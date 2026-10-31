"""Modo completo: revanches por degrau de dificuldade (POK-42), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). A preparação é por atalho
(SET_FLAG, SET_VAR, SET_PARTY_MON, WARP e a RAM): FLAG_SYS_GAME_CLEAR, o relógio no dia 0 ao meio-dia (clima do
dia 0 é sempre limpo: a Rota 3 fica sem areia nas telas) e um time de 6 Mewtwo nv 100. Cada caso parte do
savestate `revanches_base`. O aviso das conquistas fica em silêncio a sessão toda (R6: ele pausa o campo e
quebraria o warp e o `in_battle`); a conquista é lida pelo estado (CONQ_ESTADO), que é marcado mesmo em silêncio
(o silêncio só cala `Conquistas_TentarAviso`).

- `revanches/escolha`: no Centro da Liga, um passo até (4,2) dispara a guarda: pergunta (`revanche_pergunta`), a
  lista dos 6 degraus (`revanche_lista`, cursor em "Nível 90") e A → VAR_REMATCH_TIER = 4;
- `revanches/vs_seeker`: degrau 4, Ben derrotado e `trainerRematches[9]` = 1 na RAM (o warp zera a tabela, então
  a escrita vem depois dele); falar com o Ben (Rota 3, 17,4) abre a revanche com o time de
  `gerar.time_vs(linha do Ben, 4)`: níveis 87–92, IV 30 e os itens (`revanche_batalha`). A IA dos chefes do POK-32
  está em uso: depois da escolha do golpe do oponente, `aiLogicId` (struct AI_ThinkingStruct) vale o tamanho em
  bits das aiFlags usadas, 9 com AI_SCRIPT_HP_AWARE (1 << 8), que o Ben não tem;
- `revanches/primeiro_combate`: degrau 5, BUILD_TRAINER_PARTY(Calvin, combate normal) = o time de
  trainer_parties.h, degrau 0; e o 1º combate de verdade contra o Ben (atalho START_TRAINER_BATTLE) usa o time de
  hoje e as aiFlags só dele (`aiLogicId` 1: AI_SCRIPT_CHECK_BAD_MOVE);
- `revanches/dupla`: degrau 5, a 1ª linha de Gêmeas como revanche → (6, 5, dupla);
- `revanches/var_lixo`: var 9 → BUILD_TRAINER_PARTY(BEN_4, revanche) dá o time de hoje, degrau 0;
- `revanches/lorelei`: degrau 2; entrar na sala (a cena anda o jogador para dentro) e falar com a Lorelei: uma
  batalha só, contra LORELEI_2 com o time de `liga.json` no degrau 2 (espécie, nível, item, golpes, IV 31);
  vencida, a sala volta ao campo com FLAG_DEFEATED_LORELEI e nenhuma outra batalha em 300 quadros;
- `revanches/degrau_zero_liga`: sem FLAG_SYS_CAN_LINK_WITH_RS e com degrau 0, a Lorelei usa
  TRAINER_ELITE_FOUR_LORELEI com o time de hoje;
- `revanches/conquista_max`: degrau 5, a revanche do Ben vencida de verdade → `revanche_max` (POK-44) feita.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only revanches
"""

import importlib.util
import struct
import sys
from functools import cache

from .. import conquistas as cq
from ..bag import MENU_CURSOR_POS, MENU_MAX_CURSOR, MENU_MIN_CURSOR
from ..battle import ACTION_FIGHT, ACTION_FUNC, B_OUTCOME_WON, MOVE_FUNC_SUFFIX
from ..breeding import header_defines
from ..emu import KEY_A, KEY_DOWN, KEY_UP
from ..game import _SUBSTRUCT_ORDER, MON_SECURE, PARTY_SIZE, POKEMON_SIZE, SUBSTRUCT_SIZE
from ..hooks import CMD_SET_VAR, CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario
from .quick_route1 import POST_BATTLE_TIMEOUT

# Telas comparadas com a referência (test/referencias/COMUM/: o time é o do atalho, não o inicial)
SCREEN_POINTS = ("revanche_pergunta", "revanche_lista", "revanche_batalha")

GERAR = REPO_ROOT / "tools" / "revanches" / "gerar.py"
SB1_VARS = 0x1000                     # u16 vars[] em struct SaveBlock1 (include/global.h)
SB1_TRAINER_REMATCHES = 0x063A        # u8 trainerRematches[MAX_REMATCH_ENTRIES], pelo local id do NPC
VAR_BASE = 0x4000
CLOCK = (0, 12 * 60)                  # dia 0, 12:00: o clima do dia 0 é sempre limpo (dia_noite.roll_weather)

CENTER = "MAP_INDIGO_PLATEAU_POKEMON_CENTER_1F"
BELOW_TRIGGER = (4, 3)                # o gatilho da guarda fica em (4,2), na frente da porta (4,1)
ROUTE3 = "MAP_ROUTE3"
BEN_FRONT, BEN_LOCAL_ID = (17, 5), 9  # o Ben fica em (17,4), olhando para baixo
LORELEI_ROOM = "MAP_POKEMON_LEAGUE_LORELEIS_ROOM"
ROOM_ENTRY = (6, 12)                  # o warp de entrada; a cena anda 5 para cima
LORELEI_FRONT = (6, 6)                # a Lorelei fica em (6,5)

MULTICHOICE_TASK = "Task_MultichoiceMenu_HandleInput"
TIER_LABELS = ("Normal", "Nível 60", "Nível 70", "Nível 80", "Nível 90", "Nível 100")
TEXT_ASK, TEXT_SET = "Que bom ver você de volta à Liga!", "Combinado!"
BUTTON_WAIT_STATES = {1, 2, 3}        # RENDER_STATE_WAIT/CLEAR/SCROLL_START: o texto espera um botão

TEAM = "SPECIES_MEWTWO"
TEAM_MOVES = ("MOVE_PSYCHIC", "MOVE_THUNDERBOLT", "MOVE_ICE_BEAM", "MOVE_FLAMETHROWER")
LEVEL = 100

# struct BattleResources (include/battle.h): o 6º ponteiro é `ai`; struct AI_ThinkingStruct: aiFlags u32 em 0x0C,
# aiLogicId u8 em 0x11. BattleAI_ChooseMoveOrAction desloca aiFlags até 0 e soma 1 em aiLogicId a cada bit: depois
# da escolha, aiLogicId = tamanho em bits das aiFlags usadas (as aiFlags lidas já são 0).
RESOURCES_AI, AI_FLAGS, AI_LOGIC_ID = 0x14, 0x0C, 0x11
AI_CHECK_BAD_MOVE, AI_HP_AWARE = 1 << 0, 1 << 8      # include/constants/battle_ai.h
BOSS_AI_LOGIC = AI_HP_AWARE.bit_length()             # 9: RematchTier_GetAiFlags inclui AI_SCRIPT_HP_AWARE
FIRST_BATTLE_LOGIC = AI_CHECK_BAD_MOVE.bit_length()  # 1: o Ben de trainers.h só tem AI_SCRIPT_CHECK_BAD_MOVE
AI_TURNS = 3                          # turnos até o oponente escolher um golpe (troca ou item não passam pela IA)

# PokemonSubstruct3 (include/pokemon.h): os 6 IVs (5 bits cada) no u32 em +4
SUB_MISC, MISC_IVS_WORD = 3, 1
NO_BATTLE_FRAMES = 300
BATTLE_TIMEOUT = 40000


@cache
def _gerar():
    """tools/revanches/gerar.py carregado pelo caminho (como em test_revanches_*.py)."""
    spec = importlib.util.spec_from_file_location("revanches_gerar_cenario", GERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ivs(raw: bytes) -> tuple[int, ...]:
    """Os 6 IVs (HP, Atq, Def, Vel, AtqEsp, DefEsp) de uma struct Pokemon crua."""
    pid, ot = struct.unpack_from("<II", raw, 0)
    words = struct.unpack_from("<12I", raw, MON_SECURE)
    index = _SUBSTRUCT_ORDER[pid % 24][SUB_MISC] * (SUBSTRUCT_SIZE // 4) + MISC_IVS_WORD
    word = words[index] ^ pid ^ ot
    return tuple(word >> (5 * i) & 0x1F for i in range(6))


class RevanchesScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.vars = header_defines(REPO_ROOT, "vars.h")
        self.vars["VAR_TEMP_1"] = self.vars["TEMP_VARS_START"] + 1   # (TEMP_VARS_START + 0x1): header_defines só lê números
        self.g = _gerar()
        self.moves = self.g.golpes_do_jogo()

    # --- leitura e montagem --------------------------------------------------------
    def _trainer(self, name: str) -> int:
        return self.consts._eval(name)   # TRAINER_* (opponents.h) e TRAINER_FLAGS_START (flags.h)

    def _var(self, name: str) -> int:
        return self.emu.read_u16(self.game._sb1() + SB1_VARS + (self.vars[name] - VAR_BASE) * 2)

    def _set_var(self, name: str, value: int) -> None:
        got = self.box.call(CMD_SET_VAR, self.vars[name], value)
        assert got == value, f"{name} = {got}, esperava {value}"

    def _flag(self, name: str, on: bool = True) -> None:
        assert self.box.set_flag(self.consts.flag(name), on) == on, name

    def _set_tier(self, tier: int) -> None:
        self._set_var("VAR_REMATCH_TIER", tier)

    def _teleport(self, map_name: str, xy: tuple[int, int]) -> None:
        group, num = self.consts.map(map_name)
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_name}")

    def _message(self) -> str:
        return self._field_message()

    def _text_waiting(self) -> bool:
        """Página inteira na caixa, esperando um botão."""
        return (self.game.text_printer_active()
                and self.game.text_printer_state(0) in BUTTON_WAIT_STATES)

    def _enemy_raw(self) -> list[bytes]:
        raw = self.emu.read(self.game.syms.addr("gEnemyParty"), POKEMON_SIZE * PARTY_SIZE)
        return [raw[i * POKEMON_SIZE:(i + 1) * POKEMON_SIZE] for i in range(PARTY_SIZE)]

    def _opponent(self) -> int:
        return self.emu.read_u16(self.game.syms.addr("gTrainerBattleOpponent_A"))

    def _ai_logic_id(self) -> int | None:
        """aiLogicId da IA em uso (None fora da batalha ou sem a estrutura alocada)."""
        if not self.game.in_battle():
            return None
        resources = self.emu.read_u32(self.game.syms.addr("gBattleResources"))
        if not 0x02000000 <= resources < 0x02040000:
            return None
        ai = self.emu.read_u32(resources + RESOURCES_AI)
        if not 0x02000000 <= ai < 0x02040000:
            return None
        return self.emu.read_u8(ai + AI_LOGIC_ID)

    def _species_name(self, species: int) -> str:
        return self.consts.species_name(species).removeprefix("SPECIES_")

    def _team(self) -> None:
        """6 Mewtwo nv 100 com Psíquico, Trovoada, Raio de Gelo e Lança-chamas (o BattleDriver escolhe o melhor)."""
        mewtwo = self.consts.species(TEAM)
        for slot in range(PARTY_SIZE):
            self.box.set_party_mon(slot, mewtwo, LEVEL)
            for i, move in enumerate(TEAM_MOVES):
                self.box.set_party_move(slot, i, self.moves[move])
        party = self.game.party()
        assert [(m.species, m.level) for m in party] == [(mewtwo, LEVEL)] * PARTY_SIZE, \
            f"time montado errado: {[(self._species_name(m.species), m.level) for m in party]}"

    def _check_team(self, expected: list[tuple[str, int, str, int]], what: str) -> str:
        """gEnemyParty == [(espécie, nível, item, IV)] (o IV igual nos 6 atributos)."""
        mons, raws = self.game.enemy_party(), self._enemy_raw()
        got = [(self.consts.species_name(m.species), m.level, m.held_item, _ivs(raws[i]))
               for i, m in enumerate(mons)]
        want = [(sp, lvl, self.consts.item(it), (iv,) * 6) for sp, lvl, it, iv in expected]
        assert got == want, f"{what}: time {got}, esperava {want}"
        return ", ".join(f"{sp.removeprefix('SPECIES_')} {lvl}" for sp, lvl, _, _ in expected)

    def _check_original(self, trainer: str, what: str) -> str:
        """gEnemyParty == o time de hoje (trainer_parties.h: nível e espécie)."""
        want = [(sp, lvl) for lvl, sp in self.g.time_original(trainer)]
        got = [(self.consts.species_name(m.species), m.level) for m in self.game.enemy_party()]
        assert got == want, f"{what}: time {got}, esperava o de hoje {want}"
        return ", ".join(f"{sp.removeprefix('SPECIES_')} {lvl}" for sp, lvl in want)

    def _ben_row(self) -> int:
        linhas = self.g.ler_revanches()
        return next(i for i, linha in enumerate(linhas) if linha[0] == "TRAINER_YOUNGSTER_BEN")

    # --- batalhas -------------------------------------------------------------------
    def _talk_to_battle(self, face_key: int, what: str) -> None:
        """Vira para o NPC da frente, aperta A e avança as falas até a batalha começar."""
        self.emu.hold(face_key, 4)
        self.ctl.wait_until(self.nav._player_still, 60, f"jogador parado antes de: {what}")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, f"início de: {what}")
        self.driver.wait_battle_start()

    def _ben_rematch(self) -> None:
        """Na Rota 3 diante do Ben, com o Vs. Seeker já tendo marcado a revanche (na RAM), fala com ele."""
        self._flag_trainer("TRAINER_YOUNGSTER_BEN")
        self._teleport(ROUTE3, BEN_FRONT)
        self.ctl.wait_overworld_idle(600)
        sb1 = self.game._sb1()
        self.emu.write(sb1 + SB1_TRAINER_REMATCHES + BEN_LOCAL_ID, b"\x01")   # depois do warp, que zera a tabela
        self._talk_to_battle(KEY_UP, "revanche do Ben")

    def _flag_trainer(self, trainer: str, on: bool = True) -> None:
        flag = self._trainer("TRAINER_FLAGS_START") + self._trainer(trainer)
        assert self.box.set_flag(flag, on) == on, trainer

    def _ai_logic_after_choice(self) -> int:
        """Joga turnos (LUTAR, 1º golpe) até o oponente escolher um golpe pela IA; devolve o aiLogicId visto."""
        d = self.driver
        seen = [0]

        def poll() -> None:
            logic = self._ai_logic_id()
            if logic:
                seen[0] = max(seen[0], logic)

        for _ in range(AI_TURNS):
            self.ctl.wait_until(lambda: d.controller_func() == ACTION_FUNC or d._battle_over(), 3000,
                                "menu de ação da batalha")
            for _ in range(30):              # o oponente pode escolher enquanto o jogador está no menu
                poll()
                self.emu.frames(2)
            if seen[0] or d._battle_over():
                break
            d._choose_action(ACTION_FIGHT)
            self.ctl.wait_until(lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX), 300, "menu de golpes")
            d._choose_first_move_with_pp()
            self.ctl.wait_until(lambda: not d.controller_func().endswith(MOVE_FUNC_SUFFIX), 60,
                                "saída do menu de golpes")
            if d._advance_until_menu_or_end("fim do turno", 3000, on_step=poll) == "end" or seen[0]:
                break
        assert seen[0], "o oponente não escolheu golpe pela IA em nenhum turno"
        return seen[0]

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="revanches_continue")
        self.box.conq_silencio(True)      # R6: o aviso pausaria o campo (warp, in_battle)
        self.box.set_clock(*CLOCK)
        self._flag("FLAG_SYS_GAME_CLEAR")
        self._flag("FLAG_SYS_CAN_LINK_WITH_RS", False)
        self._set_tier(0)
        self._team()
        self.ctl.checkpoint("revanches_base")
        return "CONTINUAR; Hall da Fama ligado, relógio no dia 0 12:00, 6 Mewtwo nv 100; savestate revanches_base"

    def _restore(self) -> None:
        self.ctl.restore("revanches_base")
        self.emu.frames(12)

    def _choice(self) -> str:
        self._restore()
        # Liga aberta (como depois das Ilhas Sevii): a guarda fica fora da porta mesmo com a Dex Nacional
        self._flag("FLAG_SYS_CAN_LINK_WITH_RS")
        self._teleport(CENTER, BELOW_TRIGGER)
        self.ctl.wait_overworld_idle(600)
        self.nav.step("up", 1)
        assert self.nav.interrupted == "script", f"o passo até (4,2) não disparou a guarda ({self.nav.interrupted})"
        assert self.game.player_xy() == (4, 2), self.game.player_xy()
        self.ctl.wait_until(lambda: self._text_waiting() and TEXT_ASK in self._message(), 600,
                            "pergunta da guarda")
        self.emu.frames(6)
        shots = [self._shot("revanche_pergunta")]
        self.ctl.press_until(KEY_A, lambda: MULTICHOICE_TASK in self._tasks(), "lista dos degraus", tries=8, wait=40)
        assert f"Hoje está em {TIER_LABELS[0]}." in self._message(), self._message()
        cursor = self._menu_cursor(len(TIER_LABELS))
        target = TIER_LABELS.index("Nível 90")
        for _ in range(len(TIER_LABELS)):
            cur = self.emu.read_u8(cursor)
            if cur == target:
                break
            self.ctl.press_until(KEY_DOWN, lambda c=cur: self.emu.read_u8(cursor) != c, "cursor da lista",
                                 tries=3, wait=20)
        assert self.emu.read_u8(cursor) == target, f"cursor em {self.emu.read_u8(cursor)}, esperava {target}"
        self.emu.frames(8)
        shots.append(self._shot("revanche_lista"))
        self.ctl.press_until(KEY_A, lambda: MULTICHOICE_TASK not in self._tasks(), "escolha do degrau")
        self.ctl.wait_until(lambda: TEXT_SET in self._message(), 300, "confirmação da guarda")
        assert f"{TIER_LABELS[target]}." in self._message(), self._message()
        self._finish_script("confirmação do degrau")
        tier = self._var("VAR_REMATCH_TIER")
        assert tier == target == 4, f"VAR_REMATCH_TIER = {tier}, esperava 4 (Nível 90)"
        assert self._var("VAR_TEMP_1") == 1, "VAR_TEMP_1 não marcou a visita"
        self.measures["choice_shots"] = shots
        return f"passo até (4,2) → pergunta, lista, cursor em Nível 90, A → VAR_REMATCH_TIER = {tier}"

    def _menu_cursor(self, options: int) -> int:
        """&sMenu.cursorPos (src/menu.c) do menu aberto: há outro `sMenu` estático no ELF."""
        found = [a for a in self.game.syms.addrs("sMenu")
                 if self.emu.read_u8(a + MENU_MIN_CURSOR) == 0
                 and self.emu.read_u8(a + MENU_MAX_CURSOR) == options - 1]
        assert len(found) == 1, f"não achei o sMenu da lista ({len(found)} candidatos)"
        return found[0] + MENU_CURSOR_POS

    def _vs_seeker(self) -> str:
        self._restore()
        self._set_tier(4)
        self._ben_rematch()
        self.driver.wait_action_menu()
        expected = self.g.time_vs(self._ben_row(), 4)
        assert [lvl for _, lvl, _, _ in expected] == [87, 87, 88, 88, 89, 92], expected
        team = self._check_team(expected, "Ben no degrau 4")
        assert all(iv == 30 for _, _, _, iv in expected), expected
        opponent = self._trainer_name(self._opponent())
        self.measures["battle_shot"] = self._shot_next_frame("revanche_batalha")
        logic = self._ai_logic_after_choice()
        assert logic == BOSS_AI_LOGIC, (f"aiLogicId {logic}: as aiFlags em uso não têm AI_SCRIPT_HP_AWARE "
                                        f"(esperava {BOSS_AI_LOGIC}, a IA dos chefes)")
        return (f"{opponent} (revanche): {team}, IV 30, itens de time_vs; "
                f"IA em uso com aiLogicId {logic} (aiFlags até AI_SCRIPT_HP_AWARE)")

    def _trainer_name(self, trainer: int) -> str:
        names = {self._trainer(n): n for n in ("TRAINER_YOUNGSTER_BEN", "TRAINER_YOUNGSTER_BEN_2",
                                                "TRAINER_YOUNGSTER_BEN_3", "TRAINER_YOUNGSTER_BEN_4",
                                                "TRAINER_ELITE_FOUR_LORELEI", "TRAINER_ELITE_FOUR_LORELEI_2")}
        return names.get(trainer, str(trainer))

    def _first_battle(self) -> str:
        self._restore()
        self._set_tier(5)
        size, tier, double = self.box.build_trainer_party(self._trainer("TRAINER_YOUNGSTER_CALVIN"), False)
        original = self.g.time_original("TRAINER_YOUNGSTER_CALVIN")
        assert (size, tier, double) == (len(original), 0, False), (size, tier, double)
        calvin = self._check_original("TRAINER_YOUNGSTER_CALVIN", "Calvin (1º combate)")
        # o 1º combate de verdade: o time de hoje e só as aiFlags do treinador
        self.box.start_trainer_battle(self._trainer("TRAINER_YOUNGSTER_BEN"))
        self.driver.wait_action_menu()
        ben = self._check_original("TRAINER_YOUNGSTER_BEN", "Ben (1º combate)")
        logic = self._ai_logic_after_choice()
        assert logic == FIRST_BATTLE_LOGIC, (f"aiLogicId {logic} no 1º combate: a IA do degrau foi somada "
                                             f"(esperava {FIRST_BATTLE_LOGIC}, só AI_SCRIPT_CHECK_BAD_MOVE)")
        return f"degrau 5: Calvin = {calvin} (degrau 0); Ben de verdade = {ben}, aiLogicId {logic}"

    def _double(self) -> str:
        self._restore()
        self._set_tier(5)
        twins = next(linha[0] for linha in self.g.ler_revanches() if linha[0].startswith("TRAINER_TWINS_"))
        got = self.box.build_trainer_party(self._trainer(twins), True)
        assert got == (6, 5, True), f"{twins}: {got}, esperava (6, 5, True)"
        return f"{twins} (revanche, degrau 5) → {got}"

    def _junk_var(self) -> str:
        self._restore()
        self._set_tier(9)
        got = self.box.build_trainer_party(self._trainer("TRAINER_YOUNGSTER_BEN_4"), True)
        original = self.g.time_original("TRAINER_YOUNGSTER_BEN_4")
        assert got == (len(original), 0, False), f"var 9: {got}, esperava ({len(original)}, 0, False)"
        team = self._check_original("TRAINER_YOUNGSTER_BEN_4", "BEN_4 com var 9")
        return f"VAR_REMATCH_TIER = 9 → degrau 0, time de hoje: {team}"

    def _enter_lorelei_room(self) -> None:
        self._flag("FLAG_DEFEATED_LORELEI", False)
        self._set_var("VAR_MAP_SCENE_POKEMON_LEAGUE", 0)
        self._teleport(LORELEI_ROOM, ROOM_ENTRY)
        self.ctl.wait_overworld_idle(1200)          # a cena de entrada anda o jogador 5 para cima
        assert self._var("VAR_MAP_SCENE_POKEMON_LEAGUE") == 1, "a cena de entrada na sala não rodou"
        assert self.nav.walk_to(*LORELEI_FRONT), f"não cheguei à frente da Lorelei: {self.game.player_xy()}"
        self._talk_to_battle(KEY_UP, "Lorelei")

    def _lorelei(self) -> str:
        self._restore()
        self._set_tier(2)
        self._enter_lorelei_room()
        self.driver.wait_action_menu()
        opponent = self._opponent()
        assert opponent == self._trainer("TRAINER_ELITE_FOUR_LORELEI_2"), \
            f"oponente {self._trainer_name(opponent)}, esperava LORELEI_2"
        expected = self.g.time_liga("LORELEI", 2)
        mons, raws = self.game.enemy_party(), self._enemy_raw()
        got = [(self.consts.species_name(m.species), m.level, m.held_item, m.moves, _ivs(raws[i]))
               for i, m in enumerate(mons)]
        want = [(sp, lvl, self.consts.item(it), [self.moves[mv] for mv in golpes], (31,) * 6)
                for sp, lvl, it, golpes in expected]
        assert got == want, f"Lorelei no degrau 2: {got}, esperava {want}"
        self.driver.move_policy = "best"
        result = self.driver.fight_to_end(timeout=BATTLE_TIMEOUT)
        assert self.driver.outcome() == B_OUTCOME_WON, f"a batalha terminou em {result}"
        self._finish_script("fim da sala da Lorelei", POST_BATTLE_TIMEOUT * 4)
        assert self.game.flag(self.consts.flag("FLAG_DEFEATED_LORELEI")), "FLAG_DEFEATED_LORELEI desligada"
        assert self.game.location() == self.consts.map(LORELEI_ROOM), self.game.location()
        for _ in range(NO_BATTLE_FRAMES // 2):
            assert not self.game.in_battle(), "outra batalha abriu depois da vitória"
            self.emu.frames(2)
        team = ", ".join(f"{sp.removeprefix('SPECIES_')} {lvl}" for sp, lvl, _, _ in expected)
        return (f"LORELEI_2 com liga.json degrau 2 ({team}; itens, golpes, IV 31); vencida ({result}): "
                f"FLAG_DEFEATED_LORELEI ligada, sem outra batalha em {NO_BATTLE_FRAMES} quadros")

    def _tier_zero_league(self) -> str:
        self._restore()
        self._set_tier(0)
        self._flag("FLAG_SYS_CAN_LINK_WITH_RS", False)
        self._enter_lorelei_room()
        self.driver.wait_action_menu()
        opponent = self._opponent()
        assert opponent == self._trainer("TRAINER_ELITE_FOUR_LORELEI"), \
            f"oponente {self._trainer_name(opponent)}, esperava TRAINER_ELITE_FOUR_LORELEI"
        team = self._check_original("TRAINER_ELITE_FOUR_LORELEI", "Lorelei no degrau 0")
        return f"degrau 0, sem CAN_LINK_WITH_RS: TRAINER_ELITE_FOUR_LORELEI com o time de hoje ({team})"

    def _achievement(self) -> str:
        self._restore()
        num = cq.num("revanche_max")
        self.box.conq_reset(True)                   # marcador e tudo pendente
        assert self.box.conq_estado(num)[0] == cq.CONQ_PENDENTE, self.box.conq_estado(num)
        self._set_tier(5)
        self._ben_rematch()
        self.driver.move_policy = "best"
        result = self.driver.fight_to_end(timeout=BATTLE_TIMEOUT)
        assert self.driver.outcome() == B_OUTCOME_WON, f"a revanche terminou em {result}"
        self._finish_script("fim da revanche do Ben", POST_BATTLE_TIMEOUT * 4)
        estado = self.box.conq_estado(num)
        assert estado[0] == cq.CONQ_FEITA, f"revanche_max {estado}, esperava feita"
        return f"revanche do Ben no degrau 5 vencida ({result}): revanche_max (num {num}) feita {estado}"

    def run(self) -> None:
        try:
            self._flow("revanches: CONTINUAR e preparação", self._start)
            res = self.suite.run("revanches/escolha: guarda da Liga, lista e Nível 90 → degrau 4", self._choice)
            res.images.extend(self.measures.get("choice_shots", []))
            res = self.suite.run("revanches/vs_seeker: revanche do Ben no degrau 4 e a IA dos chefes", self._vs_seeker)
            if "battle_shot" in self.measures:
                res.images.append(self.measures["battle_shot"])
            self.suite.run("revanches/primeiro_combate: 1º combate não muda (time e IA)", self._first_battle)
            self.suite.run("revanches/dupla: Gêmeas no degrau 5 continuam em dupla", self._double)
            self.suite.run("revanches/var_lixo: var com lixo vale degrau 0", self._junk_var)
            self.suite.run("revanches/lorelei: Lorelei no degrau 2, uma batalha só", self._lorelei)
            self.suite.run("revanches/degrau_zero_liga: degrau 0 mantém a Lorelei de hoje", self._tier_zero_league)
            self.suite.run("revanches/conquista_max: revanche no degrau 5 marca revanche_max", self._achievement)
        except Abort:
            pass


def run_full_revanches(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    RevanchesScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only revanches ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "revanches", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
