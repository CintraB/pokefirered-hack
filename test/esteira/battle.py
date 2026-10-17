"""Condução de batalhas só com botões, decidindo pelo estado lido da memória.

- Menus de ação e de golpes: posição do cursor em gActionSelectionCursor[0] /
  gMoveSelectionCursor[0], grade 2x2 (bit 0 = coluna, bit 1 = linha), como em
  src/battle_controller_player.c (HandleInputChooseAction/HandleInputChooseMove).
- Perguntas sim/não da batalha: identificadas pelo comando apontado por
  gBattlescriptCurrInstr (opcodes tirados de gBattleScriptingCommandsTable no ROM).
- Desmaio do próprio Pokémon (data/battle_scripts_1.s, BattleScript_HandleFaintedMon):
  na selvagem o `yesnobox` pergunta "Usar o próximo Pokémon?" (NÃO = tentar fugir), na de
  treinador o mesmo comando pergunta se troca antes do oponente (NÃO = seguir). Depois vem
  a tela de Pokémon (src/party_menu.c): escolhe o 1º vivo e ENVIAR/TROCAR (1ª opção).
- Bolsa e menu de Pokémon do item: esteira/bag.py.
"""

import struct
from typing import Callable

from .bag import PARTY_MENU_SLOT_ID, Bag
from .control import Controller
from .emu import KEY_A, KEY_B, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP

# include/constants/battle.h
B_OUTCOME_WON = 1
B_OUTCOME_LOST = 2
B_OUTCOME_DREW = 3
B_OUTCOME_RAN = 4
B_OUTCOME_PLAYER_TELEPORTED = 5
B_OUTCOME_MON_FLED = 6
B_OUTCOME_CAUGHT = 7
OUTCOME_NAMES = {
    B_OUTCOME_WON: "win",
    B_OUTCOME_LOST: "lose",
    B_OUTCOME_DREW: "lose",
    B_OUTCOME_RAN: "fled",
    B_OUTCOME_PLAYER_TELEPORTED: "fled",
    B_OUTCOME_MON_FLED: "fled",
}
BATTLE_TYPE_TRAINER = 1 << 3

ACTION_FIGHT, ACTION_BAG, ACTION_RUN = 0, 1, 3
MAX_MON_MOVES = 4
BATTLE_MON_MOVES = 0x0C        # struct BattlePokemon.moves[4] (u16)
BATTLE_MON_PP = 0x24           # struct BattlePokemon.pp[4] (u8)
BATTLE_MON_SPECIES = 0x00      # struct BattlePokemon.species (u16)
BATTLE_MON_HP = 0x28           # struct BattlePokemon.hp (u16)
BATTLE_MON_LEVEL = 0x2A        # struct BattlePokemon.level (u8)
BATTLE_MON_SIZE = 0x58         # sizeof(struct BattlePokemon) (nm: gBattleMons = 0x160 = 4 * 0x58)

PARTY_MENU_ACTION = 0x0B       # gPartyMenu.action (u8), include/party_menu.h
PARTY_ACTION_USE_ITEM = 3      # include/constants/party_menu.h
PARTY_CHOOSE_TASK = "Task_HandleChooseMonInput"
PARTY_SELECTION_TASK = "Task_HandleSelectionMenuInput"   # ENVIAR/TROCAR, RESUMO, CANCELAR
BAG_INPUT_TASK = "Task_BagMenu_HandleInput"
# Nomes das funções do controlador do jogador (gBattlerControllerFuncs[0]). Na 1ª batalha
# do rival o controlador é o tutorial (battle_controller_oak_old_man.c): o menu de ação tem
# o mesmo nome (static) e o de golpes é OakOldManHandleInputChooseMove, que chama
# HandleInputChooseMove; por isso o menu de golpes é reconhecido pelo sufixo.
ACTION_FUNC = "HandleInputChooseAction"
MOVE_FUNC_SUFFIX = "HandleInputChooseMove"

# sim/não da batalha -> tecla: recusa aprender golpe (B = NÃO), confirma "parar de aprender"
# (A com o cursor em SIM). O `yesnobox` depende do tipo de batalha (yesno_key).
YESNO_COMMANDS = {
    "Cmd_yesnoboxlearnmove": KEY_B,
    "Cmd_yesnoboxstoplearningmove": KEY_A,
    "Cmd_yesnobox": KEY_B,
}
NICKNAME_COMMAND = "Cmd_trygivecaughtmonnick"
NUM_BATTLE_COMMANDS = 256

TEXT_PERIOD = 10               # A segurado 2 quadros + 8 soltos
MENU_TIMEOUT = 600

# Escolha do golpe pelo dano esperado (move_policy="best")
BATTLE_MON_TYPES = 0x21        # struct BattlePokemon.type1, type2 (u8)
BATTLE_MOVE_SIZE = 12          # struct BattleMove (include/pokemon.h), tabela gBattleMoves
BATTLE_MOVE_POWER, BATTLE_MOVE_TYPE, BATTLE_MOVE_ACCURACY = 1, 2, 3
TYPE_FORESIGHT, TYPE_ENDTABLE = 0xFE, 0xFF     # include/battle_main.h
TYPE_TABLE_SIZE = 336                          # gTypeEffectiveness[336]
STAB = 1.5


def parse_type_table(raw: bytes) -> dict[tuple[int, int], float]:
    """gTypeEffectiveness (triplas atacante, defensor, multiplicador x10) até TYPE_ENDTABLE.
    O marcador TYPE_FORESIGHT só separa as imunidades que a Foresight anula."""
    table: dict[tuple[int, int], float] = {}
    for i in range(0, len(raw) - 2, 3):
        atk, dfn, mul = raw[i], raw[i + 1], raw[i + 2]
        if atk == TYPE_ENDTABLE:
            break
        if atk != TYPE_FORESIGHT:
            table[(atk, dfn)] = mul / 10
    return table


def move_score(power: int, move_type: int, accuracy: int, attacker: tuple[int, int],
               defender: tuple[int, int], table: dict[tuple[int, int], float]) -> float:
    """Dano esperado relativo: poder x STAB x efetividade (tipo repetido conta uma vez) x
    precisão (0 = nunca erra). Golpe de status (poder 0) dá 0."""
    if power == 0:
        return 0
    score = power * (STAB if move_type in attacker else 1)
    for dfn in dict.fromkeys(defender):
        score *= table.get((move_type, dfn), 1.0)
    return score * (accuracy / 100 if accuracy else 1)


def yesno_key(command: str, battle_type_flags: int) -> int:
    """Tecla que responde o sim/não `command` da batalha.

    `yesnobox` só aparece em BattleScript_HandleFaintedMon: na selvagem é "Usar o próximo
    Pokémon?" (SIM = A; NÃO tentaria fugir), na de treinador é "trocar antes do oponente?"
    (NÃO = B, segue com o Pokémon da vez).
    """
    if command == "Cmd_yesnobox":
        return KEY_B if battle_type_flags & BATTLE_TYPE_TRAINER else KEY_A
    return YESNO_COMMANDS[command]


class BattleDriver:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.game = controller.game
        self.emu = controller.emu
        self.syms = controller.game.syms
        self.bag = Bag(controller)
        self._opcodes: dict[int, str] | None = None
        self._types: dict[tuple[int, int], float] | None = None
        # "first": sempre o 1º golpe com PP (ritmo de botões do modo rápido e das fixtures);
        # "best": o de maior dano esperado contra o oponente (move_scores).
        self.move_policy = "first"
        # (item, fração): em fight_to_end, usa o item no Pokémon em campo abaixo da fração
        self.heal: tuple[int, float] | None = None
        self.healed: list[tuple[int, int, int | None]] = []   # (slot, HP antes, HP depois)

    # --- leitura do estado ---------------------------------------------------------
    def _opcode_names(self) -> dict[int, str]:
        if self._opcodes is None:
            names = list(YESNO_COMMANDS) + [NICKNAME_COMMAND]
            wanted = {}
            for name in names:
                try:
                    wanted[self.syms.addr(name)] = name
                except KeyError:
                    pass
            table = self.emu.read(self.syms.addr("gBattleScriptingCommandsTable"),
                                  NUM_BATTLE_COMMANDS * 4)
            self._opcodes = {}
            for i in range(NUM_BATTLE_COMMANDS):
                func = struct.unpack_from("<I", table, i * 4)[0] & ~1
                if func in wanted:
                    self._opcodes[i] = wanted[func]
        return self._opcodes

    def _script_command(self) -> str | None:
        """Nome do comando de batalha em execução, se for um dos que nos interessam."""
        ptr = self.emu.read_u32(self.syms.addr("gBattlescriptCurrInstr"))
        if not 0x08000000 <= ptr < 0x0A000000:
            return None
        return self._opcode_names().get(self.emu.read_u8(ptr))

    def controller_func(self) -> str:
        return self.ctl._battle_func()

    def outcome(self) -> int:
        return self.emu.read_u8(self.syms.addr("gBattleOutcome"))

    def battle_type_flags(self) -> int:
        return self.emu.read_u32(self.syms.addr("gBattleTypeFlags"))

    def _battle_over(self) -> bool:
        return not self.game.in_battle() and self.outcome() != 0

    def _battler_addr(self, battler: int) -> int:
        return self.syms.addr("gBattleMons") + battler * BATTLE_MON_SIZE

    def battler_hp(self, battler: int) -> int:
        """gBattleMons[battler].hp (0 = jogador, 1 = oponente em batalha simples)."""
        return self.emu.read_u16(self._battler_addr(battler) + BATTLE_MON_HP)

    def battler_species_level(self, battler: int) -> tuple[int, int]:
        """(espécie, nível) de gBattleMons[battler]."""
        base = self._battler_addr(battler)
        return (self.emu.read_u16(base + BATTLE_MON_SPECIES),
                self.emu.read_u8(base + BATTLE_MON_LEVEL))

    def _battle_mon(self) -> tuple[list[int], list[int]]:
        raw = self.emu.read(self.syms.addr("gBattleMons"), 0x28)
        moves = list(struct.unpack_from("<4H", raw, BATTLE_MON_MOVES))
        pp = list(struct.unpack_from("<4B", raw, BATTLE_MON_PP))
        return moves, pp

    # --- primitivas ----------------------------------------------------------------
    def _press(self, key: int) -> None:
        self.emu.press(key, hold=2, release=TEXT_PERIOD - 2)

    def wait_battle_start(self, timeout: int = MENU_TIMEOUT) -> None:
        """Espera a batalha começar (gBattleOutcome só vale depois de uma batalha nova)."""
        def started() -> bool:
            if self.game.in_battle():
                return True
            if self.ctl.script_active() or self.game.text_printer_active():
                self._press(KEY_A)      # fala do treinador antes da batalha
            return False
        self.ctl.wait_until(started, timeout, "início da batalha")

    def _select_grid(self, cursor_sym: str, target: int, what: str) -> None:
        """Move o cursor 2x2 (bit 0 coluna, bit 1 linha) até `target`, conferindo na memória."""
        addr = self.syms.addr(cursor_sym)
        for _ in range(4):
            cur = self.emu.read_u8(addr)
            if cur == target:
                return
            if (cur ^ target) & 1:
                self.emu.press(KEY_RIGHT if target & 1 else KEY_LEFT, hold=2, release=4)
            else:
                self.emu.press(KEY_DOWN if target & 2 else KEY_UP, hold=2, release=4)
        if self.emu.read_u8(addr) != target:
            raise self.ctl.timeout_error(f"cursor de {what} em {self.emu.read_u8(addr)}, "
                                         f"esperava {target}")

    def _choose_action(self, action: int) -> None:
        self._select_grid("gActionSelectionCursor", action, "ação")
        self._press(KEY_A)

    def _choose_first_move_with_pp(self) -> None:
        """O 1º golpe com PP (move_policy "first") ou o de maior dano esperado ("best")."""
        moves, pp = self._battle_mon()
        usable = [i for i in range(MAX_MON_MOVES) if moves[i] and pp[i] > 0]
        if not usable:
            raise self.ctl.timeout_error(f"nenhum golpe com PP (golpes={moves}, pp={pp})")
        target = usable[0]
        if self.move_policy == "best":
            scores = self.move_scores()
            target = max(usable, key=lambda i: (scores[i], -i))
        self._select_grid("gMoveSelectionCursor", target, "golpe")
        self._press(KEY_A)

    def _type_table(self) -> dict[tuple[int, int], float]:
        if self._types is None:
            self._types = parse_type_table(self.emu.read(self.syms.addr("gTypeEffectiveness"),
                                                         TYPE_TABLE_SIZE))
        return self._types

    def move_scores(self) -> list[float]:
        """move_score() de cada golpe do nosso Pokémon em campo contra o oponente (batalha
        simples: gBattleMons[0] contra gBattleMons[1])."""
        ours = self.emu.read(self._battler_addr(0), BATTLE_MON_SIZE)
        theirs = self.emu.read(self._battler_addr(1), BATTLE_MON_SIZE)
        moves = struct.unpack_from("<4H", ours, BATTLE_MON_MOVES)
        attacker = tuple(ours[BATTLE_MON_TYPES:BATTLE_MON_TYPES + 2])
        defender = tuple(theirs[BATTLE_MON_TYPES:BATTLE_MON_TYPES + 2])
        table = self._type_table()
        moves_table = self.syms.addr("gBattleMoves")
        scores = []
        for move in moves:
            data = self.emu.read(moves_table + move * BATTLE_MOVE_SIZE, BATTLE_MOVE_SIZE)
            scores.append(move_score(data[BATTLE_MOVE_POWER], data[BATTLE_MOVE_TYPE],
                                     data[BATTLE_MOVE_ACCURACY], attacker, defender, table)
                          if move else 0)
        return scores

    def active_slot(self) -> int:
        """Posição no time do nosso Pokémon em campo (gBattlerPartyIndexes[0])."""
        return self.emu.read_u16(self.syms.addr("gBattlerPartyIndexes"))

    def _should_heal(self) -> bool:
        """`heal` = (item, fração): o Pokémon em campo está abaixo da fração do HP máximo e
        ainda há o item na bolsa."""
        if self.heal is None:
            return False
        item, fraction = self.heal
        slot = self.active_slot()
        party = self.game.party()
        if slot >= len(party) or self.game.bag_quantity(item) == 0:
            return False
        mon = party[slot]
        return 0 < mon.hp < mon.max_hp * fraction

    def _send_out_replacement(self) -> None:
        """Tela de Pokémon depois de um desmaio: cursor no 1º vivo e A (abre ENVIAR/TROCAR)."""
        alive = [i for i, mon in enumerate(self.game.party()) if mon.hp > 0]
        if not alive:
            raise self.ctl.timeout_error("tela de Pokémon sem nenhum Pokémon vivo")
        target = alive[0]
        slot = self.syms.addr("gPartyMenu") + PARTY_MENU_SLOT_ID
        for _ in range(8):
            cur = self.emu.read_u8(slot)
            if cur == target:
                break
            self.ctl.press_until(KEY_DOWN, lambda: self.emu.read_u8(slot) != cur,
                                 f"cursor da tela de Pokémon no slot {target}")
        if self.emu.read_u8(slot) != target:
            raise self.ctl.timeout_error(f"cursor da tela de Pokémon no slot {target}")
        self.ctl.press_until(KEY_A, lambda: PARTY_CHOOSE_TASK not in self.game.active_tasks(),
                             f"escolha do Pokémon do slot {target}")

    def _handle_event(self) -> None:
        """Um passo fora dos menus de escolha: tela de Pokémon depois de um desmaio,
        sim/não, ou avança texto com A."""
        if not self.game.in_battle():
            self._press(KEY_A)
            return
        tasks = self.game.active_tasks()
        action = self.emu.read_u8(self.syms.addr("gPartyMenu") + PARTY_MENU_ACTION)
        if PARTY_CHOOSE_TASK in tasks and action != PARTY_ACTION_USE_ITEM:
            self._send_out_replacement()
        elif PARTY_SELECTION_TASK in tasks:
            self._press(KEY_A)          # ENVIAR/TROCAR é a 1ª opção
        else:
            command = self._script_command()
            if command in YESNO_COMMANDS:
                self._press(yesno_key(command, self.battle_type_flags()))
            else:
                self._press(KEY_A)

    # --- API -----------------------------------------------------------------------
    def fight_to_end(self, timeout: int = 20000,
                     on_step: Callable[[], None] | None = None) -> str:
        """Luta até a batalha acabar com o golpe de `move_policy` (padrão: o 1º com PP); com
        `heal`, usa o item no Pokémon em campo quando o HP cai da fração (registra em
        `healed`).

        Devolve 'win'|'lose'|'fled' (gBattleOutcome), ou 'fainted' quando um Pokémon nosso
        que começou vivo desmaiou, outro entrou no lugar e a batalha não terminou em
        derrota (o resultado bruto continua em outcome()). 'lose' = time todo desmaiado.

        `on_step()` roda a cada iteração do laço (entre duas, no máximo um passo de texto ou
        a escolha de um menu), para quem quer observar a batalha enquanto ela anda.
        """
        self.wait_battle_start()
        alive = [i for i, mon in enumerate(self.game.party()) if mon.hp > 0]
        spent = 0
        while not self._battle_over():
            if spent >= timeout:
                raise self.ctl.timeout_error("fim da batalha")
            if on_step is not None:
                on_step()
            func = self.controller_func()
            if func == ACTION_FUNC and self._should_heal():
                slot = self.active_slot()
                before = self.game.party()[slot].hp
                after = self.use_item_in_battle(self.heal[0], slot)
                self.healed.append((slot, before, after))
            elif func == ACTION_FUNC:
                self._choose_action(ACTION_FIGHT)
            elif func.endswith(MOVE_FUNC_SUFFIX):
                self._choose_first_move_with_pp()
            elif self._script_command() == NICKNAME_COMMAND:
                self._press(KEY_B)       # não dá apelido a um capturado por acaso
            else:
                self._handle_event()
            spent += TEXT_PERIOD
        outcome = self.outcome()
        if outcome not in OUTCOME_NAMES:
            raise AssertionError(f"batalha terminou com gBattleOutcome={outcome} inesperado")
        name = OUTCOME_NAMES[outcome]
        party = self.game.party()
        if name != "lose" and any(i < len(party) and party[i].hp == 0 for i in alive):
            return "fainted"
        return name

    def _advance_until_menu_or_end(self, what: str, timeout: int, stop=None,
                                   on_step: Callable[[], None] | None = None) -> str:
        """Avança mensagens até: 'menu' (menu de ação), 'end' (fim da batalha) ou 'stop'."""
        spent = 0
        while True:
            if on_step is not None:
                on_step()
            if self._battle_over():
                return "end"
            if stop is not None and stop():
                return "stop"
            if self.controller_func() == ACTION_FUNC:
                return "menu"
            if spent >= timeout:
                raise self.ctl.timeout_error(what)
            self._handle_event()
            spent += TEXT_PERIOD

    def wait_action_menu(self, timeout: int = 3000) -> None:
        """Avança as mensagens (ex.: "Um RATTATA selvagem apareceu!") até o menu de ação."""
        self.wait_battle_start()
        if self._advance_until_menu_or_end("menu de ação da batalha", timeout) == "end":
            raise AssertionError("a batalha acabou antes do menu de ação")

    def fight_turn(self, timeout: int = 3000) -> str:
        """Um turno de LUTAR com o 1º golpe com PP: 'menu' (próximo turno) ou 'end'."""
        self.wait_action_menu()
        self._choose_action(ACTION_FIGHT)
        in_moves = lambda: self.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        self._choose_first_move_with_pp()
        self.ctl.wait_until(lambda: not in_moves(), 60, "saída do menu de golpes")
        return self._advance_until_menu_or_end("fim do turno", timeout)

    def run_away(self, timeout: int = 3000) -> bool:
        """Escolhe FUGIR; True se a batalha terminou em fuga, False se voltou ao menu."""
        self.wait_action_menu()
        self._choose_action(ACTION_RUN)
        self.ctl.wait_until(lambda: self.controller_func() != ACTION_FUNC, 60, "saída do menu")
        if self._advance_until_menu_or_end("resultado da fuga", timeout) == "menu":
            return False
        return self.outcome() == B_OUTCOME_RAN

    def _open_bag_on_item(self, item_id: int) -> None:
        """Abre a BOLSA pelo menu de ação e põe o cursor sobre `item_id` (sem confirmar)."""
        self.bag.find(item_id)          # falha cedo se o item não está na bolsa
        self.wait_action_menu()
        self._choose_action(ACTION_BAG)
        self.bag.wait_ready()
        self.bag.select(item_id)

    def use_item_in_battle(self, item_id: int, slot: int = 0,
                           timeout: int = 3000) -> int | None:
        """Usa `item_id` da bolsa no Pokémon `slot` do time e avança até o próximo menu de
        ação (ou o fim da batalha).

        Devolve o HP do Pokémon logo depois do item, antes do golpe do oponente no mesmo
        turno: o maior valor visto em party()[slot].hp (o menu de Pokémon sobe o HP de 1 em 1
        na animação, e o golpe só vem depois), ou None se o HP não subiu.
        """
        self._open_bag_on_item(item_id)
        self.bag.use_selected()
        before = self.game.party()[slot].hp
        highest = [before]

        def watch() -> None:
            highest[0] = max(highest[0], self.game.party()[slot].hp)

        self.bag.choose_party_slot(slot)
        self._advance_until_menu_or_end("volta ao menu depois do item", timeout, on_step=watch)
        return highest[0] if highest[0] > before else None

    def throw_ball(self, item_id: int, timeout: int = 3000) -> bool:
        """Lança a bola `item_id`; True se capturou (para na pergunta do apelido, ou no fim
        da batalha), False se o selvagem escapou da bola e a batalha seguiu (ou acabou de
        outro jeito, ex.: o nosso time todo desmaiou)."""
        self._open_bag_on_item(item_id)
        self.bag.use_selected()
        self.ctl.wait_until(lambda: self.game.in_battle()
                            and BAG_INPUT_TASK not in self.game.active_tasks()
                            and self.controller_func() != ACTION_FUNC,
                            MENU_TIMEOUT, "lançamento da bola")
        result = self._advance_until_menu_or_end(
            "resultado da bola", timeout,
            stop=lambda: self._script_command() == NICKNAME_COMMAND)
        if result == "stop":
            return True
        if result == "end":
            return self.outcome() == B_OUTCOME_CAUGHT
        return False
