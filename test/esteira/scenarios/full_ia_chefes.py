"""Modo completo: IA dos chefes com troca preditiva e itens (POK-46), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). O aviso das conquistas fica em
silêncio a sessão toda (R6: ele pausa o campo). As batalhas começam pelo atalho START_TRAINER_BATTLE e o estado é
montado por atalho (SET_PARTY_MON, SET_PARTY_MOVE, PARTY_SIZE, SET_ENEMY_MON, SET_TRAINER_ITEMS) e pela RAM; a
decisão do chefe é lida pelo atalho AI_SMART_DECIDE (só a decisão nova: troca preditiva → item → ataque, sem efeito).
A IA do oponente escolhe a ação do turno assim que o menu de ação do jogador abre: o que se monta com o menu aberto
vale para a escolha do turno seguinte.

Brock (chefe): Squirtle nv 35 do jogador com Water Gun (mostrado no turno 0, derrubando o Geodude) e Growl; o Onix
entra e vira o savestate `ia_brock`. "Ameaça" = Onix nv 45 (Pedra/Terra: Água 4x, não derruba o Squirtle antes) e,
quando há candidato, um Bulbasaur nv 60 com PS cheio no slot 2 (resiste Água).

- `ia/troca_preditiva`: ameaça + Bulbasaur → SWITCH para o slot 2; no jogo (só Growl, o turno anda) o chefe troca de
  verdade: o Bulbasaur entra e o Onix fica vivo no banco;
- `ia/fica_e_ataca`: a mesma montagem com o sorteio (arg0 0), 60 vezes: ao menos uma decisão sem a troca preditiva
  (o "1 em 5 fica", que segue a regra original) e ao menos um SWITCH;
- `ia/sem_pingue_pongue`: a troca voluntária de verdade, com o slot 2 refeito como Onix nv 45 antes de o turno rodar
  (quem entra continua ameaçado) e um Bulbasaur seguro no slot 0: no turno seguinte a decisão não é SWITCH e o
  chefe fica em campo; um turno depois a troca volta a valer (contraprova);
- `ia/aumento_segura`: ameaça + Bulbasaur com +2 de Ataque no Onix (estágio na RAM) → não troca; com +1 troca;
- `ia/derruba_primeiro`: Onix nv 100 (mais rápido, derruba o Squirtle) → ATTACK;
- `ia/sem_candidato`: só o Onix de pé, Bulbasaur com 40% de PS, Charmander (fraco a Água) ou Bulbasaur desmaiado →
  não troca;
- `ia/substituto`: Charmander nv 30 (fraco a Água) no slot 0, Rattata nv 30 no 2 e Bulbasaur nv 30 no 3; o Onix com
  1 PS cai com o Water Gun de verdade e entra o Bulbasaur (resiste a ameaça), não o 1º vivo.

Erika (chefe): Magneton nv 55 do jogador com Growl e Night Shade (dano fixo 55); savestate `ia_erika` no menu do
turno 0, Victreebel nv 29 no slot 0 em campo.

- `ia/item_30`: Hiperpoção com PS 30% → ITEM; Poção (cura < 25% do PS máximo) → ATTACK;
- `ia/item_60`: Hiperpoção com PS 60% e 35% → ATTACK;
- `ia/cura_desfeita`: com 2 Superpoções e PS 30%, a Erika usa a 1ª de verdade; o Night Shade desfaz a cura no mesmo
  turno, a marca fica gravada e a decisão seguinte não é ITEM (a 2ª Superpoção fica na lista);
- `ia/cura_total_sono`: Victreebel dormindo com Cura Total → ITEM; no jogo ela é usada e o Victreebel acorda.

- `ia/comum_igual`: Ben (treinador comum, sem AI_SCRIPT_HP_AWARE) na montagem de `troca_preditiva`: aiSmart 0, golpe
  não gravado, AI_SMART_DECIDE = "não é chefe", e o Onix nv 45 fica em campo 3 turnos com o Bulbasaur seguro no banco
  (o caminho original não troca: o último golpe que o atingiu, Growl, não tem poder);
- `ia/dupla`: Gêmeas Eli & Anne (dupla) com aiSmart forçado a 1 na RAM (nenhum chefe luta em dupla): a ameaça com o
  Bulbasaur seguro não dá SWITCH (com a mesma montagem e o tipo de batalha simples por um instante, dá); a
  Hiperpoção com PS 30% é escolhida e usada de verdade no turno seguinte, que termina normalmente.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only ia_chefes
Numa janela, em tempo real: `make test-watch CENARIO=ia_chefes`.
"""

import struct
import sys

from ..battle import (ACTION_FIGHT, ACTION_FUNC, BATTLE_MON_HP, BATTLE_MON_PP, BATTLE_MON_SIZE, MENU_TIMEOUT,
                      MOVE_FUNC_SUFFIX, BattleDriver)
from ..breeding import header_defines
from ..emu import KEY_A
from ..game import POKEMON_SIZE
from ..hooks import SMART_AI_ATTACK, SMART_AI_ITEM, SMART_AI_SWITCH, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

ACTION_NAMES = {SMART_AI_ATTACK: "ATTACK", SMART_AI_SWITCH: "SWITCH", SMART_AI_ITEM: "ITEM"}
NO_SLOT = 6                          # PARTY_SIZE: "nenhum" na decisão

# struct BattleStruct (include/battle.h): aiSmart u8, aiRevealedMoves[6][4] u16, aiVoluntarySwitchTurn[2] u16,
# aiHealTurn[2] u16, aiHealHp[2] u16 (posição do oponente: 0 = esquerda)
BS_AI_SMART, BS_SWITCH_TURN, BS_HEAL_TURN, BS_HEAL_HP = 0x21F, 0x250, 0x254, 0x258
SMART_AI_NEVER = 0xFFFF
HEAL_UNDONE_BIT = 1 << 10            # aiHealHp: marca "cura desfeita" (bit 10); PS antes nos bits 0-9
RESULTS_TURN = 0x13                  # gBattleResults.battleTurnCounter (u8)
# struct BattleResources: battleHistory (7º ponteiro); struct BattleHistory: trainerItems[4] u16, itemsNo u8
RESOURCES_HISTORY, HISTORY_ITEMS, HISTORY_ITEMS_NO = 0x18, 0x24, 0x2C
# struct BattlePokemon: speed, statStages[8] (s8, 6 = neutro), maxHP, status1, status2
MON_SPEED, MON_STAT_STAGES, MON_MAX_HP, MON_STATUS1, MON_STATUS2 = 0x06, 0x18, 0x2C, 0x4C, 0x50
STAT_ATK, DEFAULT_STAGE = 1, 6
PARTY_HP = 0x56                      # struct Pokemon.hp (u16)
BATTLE_TYPE_DOUBLE = 1 << 0
STATUS1_SLEEP = 0x07
SLEEP5 = 5

BROCK, ERIKA, BEN, TWINS = ("TRAINER_LEADER_BROCK", "TRAINER_LEADER_ERIKA", "TRAINER_YOUNGSTER_BEN",
                            "TRAINER_TWINS_ELI_ANNE")
PLAYER_LEVEL = 35
ERIKA_PLAYER_LEVEL = 55              # Night Shade tira 55: desfaz a Superpoção (50) do Victreebel com 30%
THREAT_LEVEL = 45                    # Onix nv 45: Água 4x, não derruba o Squirtle nv 35 antes e sem Harden nem Rage
                                     # (um aumento de atributo nos turnos de espera seguraria a troca)
SAFE_LEVEL = 60                      # Bulbasaur nv 60: resiste Água, golpe de Planta super efetivo
TURN_TIMEOUT = 6000
SWITCH_TRIES = 6                     # turnos até a troca preditiva sair (cada um 4 em 5)
STAY_SAMPLES = 60                    # decisões com o sorteio "1 em 5 fica"
COMMON_TURNS = 3


class IaChefesScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.driver: BattleDriver | None = None
        self.moves = header_defines(REPO_ROOT, "moves.h")
        self.onix_slot = 1

    # --- leitura --------------------------------------------------------------------
    def _sp(self, name: str) -> int:
        return self.consts.species(f"SPECIES_{name}")

    def _item(self, name: str) -> int:
        return self.consts.item(f"ITEM_{name}")

    def _sym(self, name: str) -> int:
        return self.game.syms.addr(name)

    def _bs(self) -> int:
        return self.emu.read_u32(self._sym("gBattleStruct"))

    def _mon(self, battler: int) -> int:
        return self._sym("gBattleMons") + battler * BATTLE_MON_SIZE

    def _enemy_slot(self, battler: int = 1) -> int:
        return self.emu.read_u16(self._sym("gBattlerPartyIndexes") + 2 * battler)

    def _enemy_hp(self, slot: int) -> int:
        return self.emu.read_u16(self._sym("gEnemyParty") + slot * POKEMON_SIZE + PARTY_HP)

    def _species(self, battler: int = 1) -> str:
        return self.consts.species_name(self.driver.battler_species_level(battler)[0]).removeprefix("SPECIES_")

    def _turn_counter(self) -> int:
        return self.emu.read_u8(self._sym("gBattleResults") + RESULTS_TURN)

    def _switch_turn(self, position: int = 0) -> int:
        return self.emu.read_u16(self._bs() + BS_SWITCH_TURN + 2 * position)

    def _heal_mark(self) -> tuple[int, int]:
        """(aiHealTurn[0], aiHealHp[0])."""
        return self.emu.read_u16(self._bs() + BS_HEAL_TURN), self.emu.read_u16(self._bs() + BS_HEAL_HP)

    def _items(self) -> tuple[list[int], int]:
        """(trainerItems[4], itemsNo) da batalha."""
        history = self.emu.read_u32(self.emu.read_u32(self._sym("gBattleResources")) + RESOURCES_HISTORY)
        return ([self.emu.read_u16(history + HISTORY_ITEMS + 2 * i) for i in range(4)],
                self.emu.read_u8(history + HISTORY_ITEMS_NO))

    def _max_hp(self, battler: int = 1) -> int:
        return self.emu.read_u16(self._mon(battler) + MON_MAX_HP)

    def _status1(self, battler: int = 1) -> int:
        return self.emu.read_u32(self._mon(battler) + MON_STATUS1)

    def _decide(self, sem_sorteio: bool = True) -> tuple[str, int, int] | None:
        got = self.box.ai_smart_decide(sem_sorteio)
        return None if got is None else (ACTION_NAMES[got[0]], got[1], got[2])

    # --- escrita na RAM (só na ROM de teste) ----------------------------------------
    def _set_enemy_hp(self, hp: int, slot: int, battler: int = 1) -> None:
        self.emu.write(self._mon(battler) + BATTLE_MON_HP, struct.pack("<H", hp))
        self.emu.write(self._sym("gEnemyParty") + slot * POKEMON_SIZE + PARTY_HP, struct.pack("<H", hp))

    def _heal_player(self) -> None:
        """PS cheio no Pokémon do jogador em campo (os turnos de espera não o derrubam)."""
        hp = self.emu.read_u16(self._mon(0) + MON_MAX_HP)
        self.emu.write(self._mon(0) + BATTLE_MON_HP, struct.pack("<H", hp))
        slot = self.driver.active_slot()
        self.emu.write(self._sym("gPlayerParty") + slot * POKEMON_SIZE + PARTY_HP, struct.pack("<H", hp))

    def _no_pp(self, move_index: int, battler: int = 0) -> None:
        """Golpe sem PP em gBattleMons: o BattleDriver passa a escolher o próximo (o 1º com PP)."""
        self.emu.write(self._mon(battler) + BATTLE_MON_PP + move_index, bytes([0]))

    def _set_stage(self, stat: int, stage: int, battler: int = 1) -> None:
        self.emu.write(self._mon(battler) + MON_STAT_STAGES + stat, bytes([stage]))

    # --- batalha --------------------------------------------------------------------
    def _turn(self, watch=None) -> str:
        """Um turno de LUTAR com o 1º golpe com PP (como BattleDriver.fight_turn), com observador."""
        d = self.driver
        d.wait_action_menu(TURN_TIMEOUT)
        d._choose_action(ACTION_FIGHT)
        in_moves = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        try:
            self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        except Exception:      # o A do LUTAR às vezes cai antes do menu aceitar: de novo
            d.wait_action_menu(TURN_TIMEOUT)
            d._choose_action(ACTION_FIGHT)
            self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes (2ª vez)")
        d._choose_first_move_with_pp()
        self.ctl.wait_until(lambda: not in_moves(), 60, "saída do menu de golpes")
        result = d._advance_until_menu_or_end("fim do turno", TURN_TIMEOUT, on_step=watch)
        self.emu.frames(10)    # a IA do oponente escolhe junto com o menu de ação do jogador
        return result

    def _func(self, battler: int) -> str:
        ptr = self.emu.read_u32(self._sym("gBattlerControllerFuncs") + 4 * battler)
        return self.game.syms.name_at(ptr & ~1) or ""

    def _double_turn(self, watch=None) -> str:
        """Um turno de dupla: os dois Pokémon do jogador (PS refeito) escolhem LUTAR e o golpe 0 (Growl: mira os dois
        oponentes, sem tela de alvo). Os cursores começam em LUTAR e no golpe 0 em toda batalha. Sem menu de golpes
        (Encore, golpe desabilitado → Struggle), o LUTAR já basta."""
        for battler in (0, 2):
            hp = self.emu.read_u16(self._mon(battler) + MON_MAX_HP)
            self.emu.write(self._mon(battler) + BATTLE_MON_HP, struct.pack("<H", hp))
            party_slot = self.emu.read_u16(self._sym("gBattlerPartyIndexes") + 2 * battler)
            self.emu.write(self._sym("gPlayerParty") + party_slot * POKEMON_SIZE + PARTY_HP, struct.pack("<H", hp))
        for battler in (0, 2):
            self.ctl.wait_until(lambda: self._func(battler) == ACTION_FUNC, TURN_TIMEOUT,
                                f"menu de ação do Pokémon {battler}")
            self.emu.frames(4)
            cursor = self.emu.read_u8(self._sym("gActionSelectionCursor") + battler)
            assert cursor == ACTION_FIGHT, f"cursor de ação do Pokémon {battler} em {cursor}"
            self._press(KEY_A)
            self.ctl.wait_until(lambda: self._func(battler) != ACTION_FUNC, MENU_TIMEOUT,
                                f"saída do menu de ação do Pokémon {battler}")
            self.emu.frames(4)
            if not self._func(battler).endswith(MOVE_FUNC_SUFFIX):
                continue
            cursor = self.emu.read_u8(self._sym("gMoveSelectionCursor") + battler)
            assert cursor == 0, f"cursor de golpe do Pokémon {battler} em {cursor}"
            self._press(KEY_A)
            self.ctl.wait_until(lambda: not self._func(battler).endswith(MOVE_FUNC_SUFFIX), 60,
                                f"saída do menu de golpes do Pokémon {battler}")
        result = self.driver._advance_until_menu_or_end("fim do turno duplo", TURN_TIMEOUT, on_step=watch)
        self.emu.frames(10)
        return result

    def _start_battle(self, trainer: str, party: list[tuple[str, list[str]]], level: int = PLAYER_LEVEL) -> None:
        """Time do jogador (espécie no `level`, golpes nos índices 0..) e a batalha contra `trainer`, até o 1º menu."""
        for slot, (species, moves) in enumerate(party):
            self.box.set_party_mon(slot, self._sp(species), level)
            for i, move in enumerate(moves):
                self.box.set_party_move(slot, i, self.moves[f"MOVE_{move}"])
        self.box.party_size(len(party))
        self.box.start_trainer_battle(self.consts._eval(trainer))
        self.driver.wait_action_menu(TURN_TIMEOUT)
        self.emu.frames(10)

    def _restore(self, name: str) -> None:
        self.ctl.restore(name)
        self.emu.frames(12)

    # --- preparo --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self.driver = BattleDriver(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="ia_chefes_continue")
        self.box.conq_silencio(True)      # R6: o aviso pausaria o campo
        self.ctl.checkpoint("ia_base")
        return "CONTINUAR; avisos das conquistas em silêncio; savestate ia_base"

    def _prepare_brock(self) -> str:
        self._restore("ia_base")
        self._start_battle(BROCK, [("SQUIRTLE", ["WATER_GUN", "GROWL"])])
        assert self.box.ai_smart_state()[0], "Brock deveria ser chefe (AI_SCRIPT_HP_AWARE)"
        for _ in range(2):            # Water Gun no Geodude; o Onix entra
            assert self._turn() == "menu", "a batalha acabou antes do Onix"
            if self._species() == "ONIX":
                break
        assert self._species() == "ONIX", f"oponente {self._species()}, esperava o Onix"
        smart, revealed = self.box.ai_smart_state()
        assert smart and revealed >= 1, f"golpe mostrado não gravado: {(smart, revealed)}"
        self.onix_slot = self._enemy_slot()
        self.ctl.checkpoint("ia_brock")
        return f"Brock (chefe): Water Gun mostrado ({revealed}), Onix no slot {self.onix_slot}; savestate ia_brock"

    def _threat(self, onix_level: int = THREAT_LEVEL, safe: tuple[str, int, int] | None = ("BULBASAUR", SAFE_LEVEL, 100),
                slot: int | None = None):
        """Onix em campo (slot `slot`, padrão o do Brock) refeito com os estágios zerados e, se `safe`, o candidato no
        slot 2; sem itens."""
        self.box.set_trainer_items()
        self.box.set_enemy_mon(self.onix_slot if slot is None else slot, self._sp("ONIX"), onix_level, 100)
        if safe is not None:
            species, level, hp = safe
            self.box.set_enemy_mon(2, self._sp(species), level, hp)

    def _until_switch_chosen(self) -> tuple[int, int]:
        """Turnos com Growl (PS do jogador refeito a cada um) até a IA escolher a troca no menu; devolve
        (turnos jogados, contador do turno da troca)."""
        for n in range(1, SWITCH_TRIES + 1):
            self._heal_player()
            assert self._turn() == "menu", "a batalha acabou antes da troca"
            counter = self._turn_counter()
            if self._switch_turn() == counter:
                return n, counter
        raise AssertionError(f"o chefe não escolheu trocar em {SWITCH_TRIES} turnos")

    # --- casos: troca --------------------------------------------------------------
    def _predictive(self) -> str:
        self._restore("ia_brock")
        self._threat()
        got = self._decide()
        assert got == ("SWITCH", 2, 0), f"ameaça 4x + Bulbasaur seguro: {got}, esperava SWITCH para o slot 2"
        self._no_pp(0)                 # só Growl daqui em diante: o turno anda sem derrubar ninguém
        turns, counter = self._until_switch_chosen()
        self._heal_player()
        assert self._turn() == "menu"
        slot, onix_hp = self._enemy_slot(), self._enemy_hp(self.onix_slot)
        assert (slot, self._species()) == (2, "BULBASAUR") and onix_hp > 0, \
            f"depois da troca: slot {slot} ({self._species()}), Onix no banco com PS {onix_hp}"
        return (f"AI_SMART_DECIDE = SWITCH slot 2; no jogo a troca saiu na escolha do turno {counter} "
                f"({turns} turno(s) de Growl): entrou o Bulbasaur, Onix vivo no banco (PS {onix_hp})")

    def _stay(self) -> str:
        self._restore("ia_brock")
        self._threat()
        count = {"ATTACK": 0, "SWITCH": 0, "ITEM": 0}
        for _ in range(STAY_SAMPLES):
            count[self._decide(sem_sorteio=False)[0]] += 1
        assert count["ATTACK"] >= 1 and count["SWITCH"] >= 1, f"{STAY_SAMPLES} sorteios: {count}"
        return f"{STAY_SAMPLES} decisões com o sorteio: {count} (fica e segue a regra original ~1 em 5)"

    def _no_ping_pong(self) -> str:
        self._restore("ia_brock")
        self._threat()
        self._no_pp(0)
        _turns, counter = self._until_switch_chosen()
        # A troca para o slot 2 já foi escolhida: antes de o turno rodar, quem vai entrar vira um Onix nv 45 (continua
        # ameaçado e não derruba antes) e o slot 0 (Geodude caído) um Bulbasaur nv 60 seguro.
        self.box.set_enemy_mon(2, self._sp("ONIX"), THREAT_LEVEL, 100)
        self.box.set_enemy_mon(0, self._sp("BULBASAUR"), SAFE_LEVEL, 100)
        self._heal_player()
        assert self._turn() == "menu"
        assert self._enemy_slot() == 2 and self._enemy_hp(self.onix_slot) > 0, \
            f"a troca voluntária não aconteceu: slot {self._enemy_slot()}"
        after = self._decide()
        assert after is not None and after[0] != "SWITCH", f"logo depois da troca voluntária: {after}"
        chosen = self._switch_turn()
        assert chosen == counter, f"o chefe escolheu outra troca no turno seguinte (turno {chosen}, a 1ª foi {counter})"
        self._heal_player()
        assert self._turn() == "menu"
        assert (self._enemy_slot(), self._species()) == (2, "ONIX"), \
            f"o chefe saiu de campo: slot {self._enemy_slot()} ({self._species()})"
        later = self._decide()
        assert later == ("SWITCH", 0, 0), f"contraprova um turno depois: {later}, esperava SWITCH para o slot 0"
        return (f"troca voluntária no turno {counter}; no seguinte, com o Onix nv 45 ameaçado e o Bulbasaur seguro: "
                f"{after} e ficou em campo; um turno depois: {later}")

    def _boost(self) -> str:
        self._restore("ia_brock")
        self._threat()
        self._set_stage(STAT_ATK, DEFAULT_STAGE + 2)
        plus2 = self._decide()
        self._set_stage(STAT_ATK, DEFAULT_STAGE + 1)
        plus1 = self._decide()
        assert plus2 == ("ATTACK", NO_SLOT, 0), f"+2 de Ataque: {plus2}, esperava ATTACK"
        assert plus1 == ("SWITCH", 2, 0), f"+1 de Ataque: {plus1}, esperava SWITCH para o slot 2"
        return f"+2 de Ataque → {plus2}; +1 → {plus1}"

    def _ko_first(self) -> str:
        self._restore("ia_brock")
        self._threat(onix_level=100)
        got = self._decide()
        speeds = (self.emu.read_u16(self._mon(1) + MON_SPEED), self.emu.read_u16(self._mon(0) + MON_SPEED))
        assert got == ("ATTACK", NO_SLOT, 0), f"Onix nv 100 com o Bulbasaur seguro: {got}, esperava ATTACK"
        return f"Onix nv 100 (velocidade {speeds[0]} contra {speeds[1]} do Squirtle) → {got}"

    def _no_candidate(self) -> str:
        self._restore("ia_brock")
        cases = (("só o Onix de pé", None),
                 ("Bulbasaur com 40% de PS", ("BULBASAUR", SAFE_LEVEL, 40)),
                 ("Charmander (Água 2x)", ("CHARMANDER", SAFE_LEVEL, 100)),
                 ("Bulbasaur desmaiado", ("BULBASAUR", SAFE_LEVEL, 0)))
        seen = []
        for what, safe in cases:
            self._threat(safe=safe)
            got = self._decide()
            assert got == ("ATTACK", NO_SLOT, 0), f"{what}: {got}, esperava ATTACK"
            seen.append(f"{what} → {got[0]}")
        return "; ".join(seen)

    def _replacement(self) -> str:
        self._restore("ia_brock")
        self.box.set_enemy_mon(0, self._sp("CHARMANDER"), 30, 100)
        self.box.set_enemy_mon(2, self._sp("RATTATA"), 30, 100)
        self.box.set_enemy_mon(3, self._sp("BULBASAUR"), 30, 100)
        self._set_enemy_hp(1, self.onix_slot)
        self._heal_player()
        assert self._turn() == "menu", "a batalha acabou (o Brock tinha mais 3 Pokémon)"
        assert self._enemy_hp(self.onix_slot) == 0, f"o Onix não caiu (PS {self._enemy_hp(self.onix_slot)})"
        slot = self._enemy_slot()
        assert (slot, self._species()) == (3, "BULBASAUR"), \
            f"entrou o slot {slot} ({self._species()}), esperava o Bulbasaur do slot 3"
        return "Onix caiu com o Water Gun; no banco Charmander (fraco), Rattata e Bulbasaur: entrou o Bulbasaur (slot 3)"

    # --- casos: itens --------------------------------------------------------------
    def _prepare_erika(self) -> str:
        self._restore("ia_base")
        self._start_battle(ERIKA, [("MAGNETON", ["GROWL", "NIGHT_SHADE"])], level=ERIKA_PLAYER_LEVEL)
        assert self.box.ai_smart_state()[0], "Erika deveria ser chefe"
        assert self._species() == "VICTREEBEL" and self._enemy_slot() == 0, \
            f"oponente {self._species()} no slot {self._enemy_slot()}, esperava o Victreebel no 0"
        self.ctl.checkpoint("ia_erika")
        return "Erika (chefe) contra Magneton nv 55 (Growl, Night Shade); savestate ia_erika"

    def _item_case(self, pct: int, items: tuple[str, ...], status: int = 0) -> tuple[tuple, str]:
        self.box.set_trainer_items(*(self._item(i) for i in items))
        self.box.set_enemy_mon(0, self._sp("VICTREEBEL"), 29, pct, status)
        got = self._decide()
        return got, f"PS {self.driver.battler_hp(1)}/{self._max_hp()}"

    def _item_30(self) -> str:
        self._restore("ia_erika")
        hyper, hp = self._item_case(30, ("HYPER_POTION",))
        assert hyper == ("ITEM", NO_SLOT, self._item("HYPER_POTION")), f"Hiperpoção com {hp}: {hyper}"
        potion, _ = self._item_case(30, ("POTION",))
        assert potion == ("ATTACK", NO_SLOT, 0), f"Poção (20 PS) com {hp}: {potion}, esperava ATTACK"
        return f"{hp}: Hiperpoção → {hyper}; Poção (cura < 25%) → {potion[0]}"

    def _item_60(self) -> str:
        self._restore("ia_erika")
        seen = []
        for pct in (60, 35):
            got, hp = self._item_case(pct, ("HYPER_POTION",))
            assert got == ("ATTACK", NO_SLOT, 0), f"Hiperpoção com {hp}: {got}, esperava ATTACK"
            seen.append(f"{hp} → {got[0]}")
        return "Hiperpoção: " + "; ".join(seen)

    def _heal_undone(self) -> str:
        self._restore("ia_erika")
        self.box.set_enemy_mon(0, self._sp("VICTREEBEL"), 29, 30)
        self.box.set_enemy_mon(2, self._sp("VILEPLUME"), 29, 0)     # 2 de pé: o 2º item vale (regra original)
        superp = self._item("SUPER_POTION")
        self.box.set_trainer_items(superp, superp)
        hp0 = self.driver.battler_hp(1)
        assert self._turn() == "menu"   # Growl; na escolha do turno 1 a Erika escolhe a Superpoção
        items, _ = self._items()
        turn, mark = self._heal_mark()
        assert items[0] == 0 and items[1] == superp and turn == 1 and mark & 0x3FF == hp0, \
            f"Superpoção não escolhida no turno 1: itens {items}, cura ({turn:#x}, {mark:#x}), PS {hp0}"
        self._no_pp(0)                  # Growl sem PP: Night Shade (55 = nível) desfaz a cura no mesmo turno
        peak = [0]
        assert self._turn(lambda: peak.__setitem__(0, max(peak[0], self.driver.battler_hp(1)))) == "menu"
        hp1 = self.driver.battler_hp(1)
        assert peak[0] >= hp0 + 40 and hp1 <= hp0, f"PS {hp0} → maior {peak[0]} → {hp1}: a cura não foi desfeita"
        mark = self._heal_mark()[1]
        assert mark & HEAL_UNDONE_BIT and self._items()[0][1] == superp, \
            f"marca de cura desfeita {mark:#x}, itens {self._items()}"
        got = self._decide()
        assert got is not None and got[0] != "ITEM", f"PS {hp1}/{self._max_hp()} com Superpoção na mão: {got}"
        return (f"Superpoção usada (PS {hp0} → {peak[0]}) e desfeita pelo Night Shade ({hp1}); marca {mark:#x}; "
                f"decisão seguinte {got}, a 2ª Superpoção ficou na lista")

    def _full_heal_sleep(self) -> str:
        self._restore("ia_erika")
        full_heal = self._item("FULL_HEAL")
        got, hp = self._item_case(100, ("FULL_HEAL",), SLEEP5)
        assert got == ("ITEM", NO_SLOT, full_heal), f"Victreebel dormindo ({hp}) com Cura Total: {got}"
        assert self._turn() == "menu"   # na escolha do turno 1 a Erika escolhe a Cura Total
        items, _ = self._items()
        assert items[0] == 0 and self._status1() & STATUS1_SLEEP, \
            f"Cura Total não escolhida: itens {items}, status1 {self._status1():#x}"
        assert self._turn() == "menu"
        assert self._status1() & STATUS1_SLEEP == 0, f"o Victreebel não acordou: status1 {self._status1():#x}"
        return f"dormindo → {got}; no jogo a Cura Total saiu da lista e o Victreebel acordou"

    # --- casos: comum e dupla ----------------------------------------------------------
    def _common(self) -> str:
        self._restore("ia_base")
        self._start_battle(BEN, [("SQUIRTLE", ["WATER_GUN", "GROWL"])])
        assert self.box.ai_smart_state() == (False, 0), f"Ben: {self.box.ai_smart_state()}"
        assert self._decide() is None, "AI_SMART_DECIDE deveria dizer 'não é chefe'"
        for _ in range(2):            # Water Gun no Rattata; o Ekans entra
            assert self._turn() == "menu", "a batalha acabou antes do 2º Pokémon"
            if self._species() != "RATTATA":
                break
        state = self.box.ai_smart_state()
        assert state == (False, 0), f"golpe gravado num treinador comum: {state}"
        slot = self._enemy_slot()
        self._threat(slot=slot)
        self._no_pp(0)
        for n in range(COMMON_TURNS):
            self._heal_player()
            assert self._turn() == "menu"
            assert (self._enemy_slot(), self._species()) == (slot, "ONIX"), \
                f"turno {n + 1}: o Ben trocou para o slot {self._enemy_slot()} ({self._species()})"
        assert self._decide() is None and self.emu.read_u8(self._bs() + BS_AI_SMART) == 0
        return (f"Ben: aiSmart 0, golpe não gravado, DECIDE = não é chefe; Onix nv {THREAT_LEVEL} (Água 4x) com "
                f"Bulbasaur seguro no banco ficou {COMMON_TURNS} turnos (o chefe troca: ia/troca_preditiva)")

    def _double(self) -> str:
        self._restore("ia_base")
        self._start_battle(TWINS, [("SQUIRTLE", ["GROWL"]), ("SQUIRTLE", ["GROWL"])])
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_DOUBLE, f"batalha não é dupla: {flags:#x}"
        assert not self.box.ai_smart_state()[0], "as Gêmeas não são chefe"
        self.emu.write(self._bs() + BS_AI_SMART, b"\x01")   # nenhum chefe luta em dupla: força
        assert self.box.ai_smart_state()[0]
        left, right = self._enemy_slot(1), self._enemy_slot(3)
        self.box.set_trainer_items()
        self.box.set_enemy_mon(left, self._sp("ONIX"), THREAT_LEVEL, 100)
        # o da direita também vira Onix: sem Sing, Disable nem Encore da Jigglypuff/Clefairy nos turnos jogados
        self.box.set_enemy_mon(right, self._sp("ONIX"), THREAT_LEVEL, 100)
        self.box.set_enemy_mon(2, self._sp("BULBASAUR"), SAFE_LEVEL, 100)
        double = self._decide()
        types = self._sym("gBattleTypeFlags")
        self.emu.write(types, struct.pack("<I", flags & ~BATTLE_TYPE_DOUBLE))   # só para o atalho, e volta
        single = self._decide()
        self.emu.write(types, struct.pack("<I", flags))
        assert double is not None and double[0] != "SWITCH", f"dupla: {double}"
        assert single == ("SWITCH", 2, 0), f"contraprova (mesma montagem como simples): {single}"
        # item: Onix com 30% e uma Hiperpoção
        hyper = self._item("HYPER_POTION")
        self.box.set_enemy_mon(left, self._sp("ONIX"), THREAT_LEVEL, 30)
        self.box.set_trainer_items(hyper)
        got = self._decide()
        assert got == ("ITEM", NO_SLOT, hyper), f"dupla, PS 30% com Hiperpoção: {got}"
        hp0 = self.driver.battler_hp(1)
        assert self._double_turn() == "menu"   # na escolha do turno 1 a Hiperpoção é escolhida
        items, _ = self._items()
        assert items[0] == 0, f"Hiperpoção não escolhida: itens {items}"
        peak = [0]
        assert self._double_turn(lambda: peak.__setitem__(0, max(peak[0], self.driver.battler_hp(1)))) == "menu"
        assert peak[0] >= hp0 + 50, f"PS do Onix {hp0} → maior {peak[0]}: a Hiperpoção não curou"
        assert (self._enemy_slot(1), self._species(1)) == (left, "ONIX")
        assert self._switch_turn(0) == SMART_AI_NEVER and self._switch_turn(1) == SMART_AI_NEVER, \
            f"troca voluntária em dupla: {self._switch_turn(0):#x}, {self._switch_turn(1):#x}"
        return (f"dupla (aiSmart forçado): ameaça + Bulbasaur → {double} (simples: {single}); Hiperpoção com "
                f"PS {hp0}/{self._max_hp()} → {got} e usada (PS até {peak[0]}); o turno terminou e ninguém trocou")

    def run(self) -> None:
        try:
            self._flow("ia: CONTINUAR e preparo", self._start)
            if self.suite.run("ia/preparo_brock: batalha do Brock com o Water Gun mostrado",
                              self._prepare_brock).status != "falha":
                self.suite.run("ia/troca_preditiva: ameaça 2x+ e candidato seguro → troca antes do golpe",
                               self._predictive)
                self.suite.run("ia/fica_e_ataca: o sorteio às vezes fica e às vezes troca", self._stay)
                self.suite.run("ia/sem_pingue_pongue: quem acabou de entrar por troca voluntária fica",
                               self._no_ping_pong)
                self.suite.run("ia/aumento_segura: +2 de atributo segura o Pokémon em campo", self._boost)
                self.suite.run("ia/derruba_primeiro: quem derruba antes ataca", self._ko_first)
                self.suite.run("ia/sem_candidato: sem candidato seguro não troca", self._no_candidate)
                self.suite.run("ia/substituto: depois do desmaio entra quem resiste à ameaça", self._replacement)
            if self.suite.run("ia/preparo_erika: batalha da Erika", self._prepare_erika).status != "falha":
                self.suite.run("ia/item_30: cura com PS <= 33%", self._item_30)
                self.suite.run("ia/item_60: sem cura com PS acima de 33%", self._item_60)
                self.suite.run("ia/cura_desfeita: cura desfeita não se repete", self._heal_undone)
                self.suite.run("ia/cura_total_sono: Cura Total acorda", self._full_heal_sleep)
            self.suite.run("ia/comum_igual: treinador comum não usa a IA nova", self._common)
            self.suite.run("ia/dupla: em dupla não há troca preditiva e o item funciona", self._double)
        except Abort:
            pass


def run_full_ia_chefes(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    IaChefesScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only ia_chefes ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "ia_chefes", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
