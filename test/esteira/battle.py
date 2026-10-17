"""Condução de batalhas só com botões, decidindo pelo estado lido da memória.

- Menus de ação e de golpes: posição do cursor em gActionSelectionCursor[0] /
  gMoveSelectionCursor[0], grade 2x2 (bit 0 = coluna, bit 1 = linha), como em
  src/battle_controller_player.c (HandleInputChooseAction/HandleInputChooseMove).
- Perguntas sim/não da batalha: identificadas pelo comando apontado por
  gBattlescriptCurrInstr (opcodes tirados de gBattleScriptingCommandsTable no ROM).
- Bolsa (src/item_menu.c): gBagMenuState {callback, location, bagOpen, pocket u16,
  itemsAbove[3] u16, cursorPos[3] u16}; menu de Pokémon: gPartyMenu.slotId em +9.
"""

import struct
from typing import Callable

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

ACTION_FIGHT, ACTION_BAG, ACTION_RUN = 0, 1, 3
MAX_MON_MOVES = 4
BATTLE_MON_MOVES = 0x0C        # struct BattlePokemon.moves[4] (u16)
BATTLE_MON_PP = 0x24           # struct BattlePokemon.pp[4] (u8)
BATTLE_MON_SPECIES = 0x00      # struct BattlePokemon.species (u16)
BATTLE_MON_HP = 0x28           # struct BattlePokemon.hp (u16)
BATTLE_MON_LEVEL = 0x2A        # struct BattlePokemon.level (u8)
BATTLE_MON_SIZE = 0x58         # sizeof(struct BattlePokemon) (nm: gBattleMons = 0x160 = 4 * 0x58)

BAG_POCKET = 0x06              # gBagMenuState.pocket (u16)
BAG_ITEMS_ABOVE = 0x08         # gBagMenuState.itemsAbove[3] (u16)
BAG_CURSOR_POS = 0x0E          # gBagMenuState.cursorPos[3] (u16)
NUM_BAG_POCKETS_NO_CASES = 3   # Itens, Itens-chave, Poké Balls
PARTY_MENU_SLOT_ID = 0x09      # gPartyMenu.slotId (s8)

BAG_INPUT_TASK = "Task_BagMenu_HandleInput"
BAG_CONTEXT_TASK = "Task_FieldItemContextMenuHandleInput"
PARTY_CHOOSE_TASK = "Task_HandleChooseMonInput"
# Nomes das funções do controlador do jogador (gBattlerControllerFuncs[0]). Na 1ª batalha
# do rival o controlador é o tutorial (battle_controller_oak_old_man.c): o menu de ação tem
# o mesmo nome (static) e o de golpes é OakOldManHandleInputChooseMove, que chama
# HandleInputChooseMove; por isso o menu de golpes é reconhecido pelo sufixo.
ACTION_FUNC = "HandleInputChooseAction"
MOVE_FUNC_SUFFIX = "HandleInputChooseMove"

# sim/não da batalha -> tecla: recusa aprender golpe (B = NÃO), confirma "parar de aprender"
# (A com o cursor em SIM), recusa trocar de Pokémon no modo SHIFT (B = NÃO).
YESNO_COMMANDS = {
    "Cmd_yesnoboxlearnmove": KEY_B,
    "Cmd_yesnoboxstoplearningmove": KEY_A,
    "Cmd_yesnobox": KEY_B,
}
NICKNAME_COMMAND = "Cmd_trygivecaughtmonnick"
NUM_BATTLE_COMMANDS = 256

TEXT_PERIOD = 10               # A segurado 2 quadros + 8 soltos
MENU_TIMEOUT = 600


class BattleDriver:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.game = controller.game
        self.emu = controller.emu
        self.syms = controller.game.syms
        self._opcodes: dict[int, str] | None = None

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
        moves, pp = self._battle_mon()
        usable = [i for i in range(MAX_MON_MOVES) if moves[i] and pp[i] > 0]
        if not usable:
            raise self.ctl.timeout_error(f"nenhum golpe com PP (golpes={moves}, pp={pp})")
        self._select_grid("gMoveSelectionCursor", usable[0], "golpe")
        self._press(KEY_A)

    def _handle_event(self) -> None:
        """Um passo fora dos menus de escolha: responde sim/não ou avança texto com A."""
        command = self._script_command() if self.game.in_battle() else None
        if command in YESNO_COMMANDS:
            self._press(YESNO_COMMANDS[command])
        else:
            self._press(KEY_A)

    # --- API -----------------------------------------------------------------------
    def fight_to_end(self, timeout: int = 20000,
                     on_step: Callable[[], None] | None = None) -> str:
        """Luta usando sempre o 1º golpe com PP até a batalha acabar: 'win'|'lose'|'fled'.

        `on_step()` roda a cada iteração (no máximo TEXT_PERIOD quadros entre duas), para
        quem quer observar a batalha enquanto ela anda.
        """
        self.wait_battle_start()
        spent = 0
        while not self._battle_over():
            if spent >= timeout:
                raise self.ctl.timeout_error("fim da batalha")
            if on_step is not None:
                on_step()
            func = self.controller_func()
            if func == ACTION_FUNC:
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
        return OUTCOME_NAMES[outcome]

    def _advance_until_menu_or_end(self, what: str, timeout: int,
                                   stop=None) -> str:
        """Avança mensagens até: 'menu' (menu de ação), 'end' (fim da batalha) ou 'stop'."""
        spent = 0
        while True:
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
        target = None
        for pocket in range(NUM_BAG_POCKETS_NO_CASES):
            items = [item for item, _qty in self.game.bag_pocket(pocket)]
            if item_id in items:
                target = (pocket, items.index(item_id))
                break
        if target is None:
            raise AssertionError(f"item {item_id} não está na bolsa")
        pocket, index = target
        self.wait_action_menu()
        self._choose_action(ACTION_BAG)
        bag_ready = lambda: BAG_INPUT_TASK in self.game.active_tasks()
        self.ctl.wait_until(bag_ready, MENU_TIMEOUT, "bolsa aberta")
        state = self.syms.addr("gBagMenuState")
        current_pocket = lambda: self.emu.read_u16(state + BAG_POCKET)
        for _ in range(NUM_BAG_POCKETS_NO_CASES):
            cur = current_pocket()
            if cur == pocket:
                break
            self._press_until(KEY_RIGHT if pocket > cur else KEY_LEFT,
                              lambda: current_pocket() != cur and bag_ready(), "troca de bolso")
        if current_pocket() != pocket:
            raise self.ctl.timeout_error(f"bolso {pocket} da bolsa")

        def position() -> int:
            return (self.emu.read_u16(state + BAG_CURSOR_POS + pocket * 2)
                    + self.emu.read_u16(state + BAG_ITEMS_ABOVE + pocket * 2))

        for _ in range(64):
            cur = position()
            if cur == index:
                return
            self._press_until(KEY_DOWN if index > cur else KEY_UP,
                              lambda: position() != cur, "cursor da bolsa")
        raise self.ctl.timeout_error(f"cursor da bolsa no item {item_id} (posição {position()}, "
                                     f"esperava {index})")

    def _press_until(self, key: int, done, what: str, tries: int = 10, wait: int = 20) -> None:
        """Aperta `key` até `done()`; depois de cada toque espera até `wait` quadros pelo
        efeito antes de repetir (telas em transição ignoram o botão)."""
        for _ in range(tries):
            if done():
                return
            self.emu.press(key, hold=2, release=2)
            for _ in range(wait // 2):
                if done():
                    return
                self.emu.frames(2)
        if not done():
            raise self.ctl.timeout_error(what)

    def _use_selected_item(self) -> None:
        """Confirma o item sob o cursor e escolhe USAR no menu de contexto."""
        in_context = lambda: BAG_CONTEXT_TASK in self.game.active_tasks()
        self._press_until(KEY_A, in_context, "menu USAR/CANCELAR")
        self._press_until(KEY_A, lambda: not in_context(), "USAR")   # cursor começa em USAR

    def use_item_in_battle(self, item_id: int, timeout: int = 3000) -> None:
        """Usa `item_id` da bolsa no Pokémon da frente e avança até o próximo menu de ação
        (ou o fim da batalha)."""
        self._open_bag_on_item(item_id)
        self._use_selected_item()
        party_ready = lambda: PARTY_CHOOSE_TASK in self.game.active_tasks()
        self.ctl.wait_until(party_ready, MENU_TIMEOUT, "escolha do Pokémon para o item")
        slot = self.syms.addr("gPartyMenu") + PARTY_MENU_SLOT_ID
        self._press_until(KEY_LEFT, lambda: self.emu.read_u8(slot) == 0,
                          "cursor do menu de Pokémon no 1º")
        self._press_until(KEY_A, lambda: not party_ready(), "item usado no 1º Pokémon")
        self._advance_until_menu_or_end("volta ao menu depois do item", timeout)

    def throw_ball(self, item_id: int, timeout: int = 3000) -> bool:
        """Lança a bola `item_id`; True se capturou (para na pergunta do apelido, ou no fim
        da batalha), False se o selvagem escapou da bola e a batalha seguiu."""
        self._open_bag_on_item(item_id)
        self._use_selected_item()
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
