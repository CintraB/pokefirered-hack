"""Modo completo: Pokédex Nacional na tela desde o início (Hack 7), na build de teste.

As telas usam IsNationalPokedexUiEnabled() (NATIONAL_DEX_FROM_START); a flag
FLAG_SYS_NATIONAL_DEX continua marcando o pós-Liga para os scripts (porteiro da Liga, Hall da
Fama, Celio/Ruby, túnel do Dunsparce). Sessão própria da ROM de teste a partir do .sav do
`captura` (`save_from="captura"`):

1. `dex/flag_desligada`: flag e VAR_NATIONAL_DEX desligadas no save;
2. `dex/tela_nacional`: START > POKéDEX: a lista de modos é a nacional (a tabela de itens da
   lista de menu ativa é a de `sListMenuItems_NatDexModeSelect`); tela `pokedex_nacional`;
3. `dex/numero_no_resumo`: Larvitar no time, o resumo guarda 246 (e não "???");
4. `dex/porta_da_liga`: Centro da Liga sem a Liga vencida: o porteiro continua em (5, 3).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only dex_nacional
"""

import json
import struct
import sys

from ..breeding import header_defines
from ..emu import KEY_B
from ..field_menu import STARTMENU_POKEDEX, STARTMENU_POKEMON
from ..hooks import CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_summary_evolution import SCREEN_TIMEOUT, SummaryEvolutionScenario

SB1_VARS = 0x1000                  # u16 vars[] em struct SaveBlock1 (include/global.h)
VAR_BASE = 0x4000
NATIONAL_DEX_MAGIC = 0x6258
POKEDEX_CB, POKEDEX_TASK, LIST_TASK = "CB2_PokedexScreen", "Task_PokedexScreen", "ListMenuDummyTask"
SETTLE_FRAMES = 30
OBJECT_EVENT_SIZE, OBJECT_EVENT_COUNT = 0x24, 16   # gObjectEvents (include/global.fieldmap.h)
MAP_OFFSET = 7
SUMMARY_SCAN = (0x3000, 0x3200)   # summary.dexNumStrBuf fica perto de 0x3070 (struct PokemonSummaryScreenData)
LARVITAR = "SPECIES_LARVITAR"
LARVITAR_DEX_NUMBER = 246
LEAGUE_MAP = "MAP_INDIGO_PLATEAU_POKEMON_CENTER_1F"
GUARD_NAME = "LOCALID_LEAGUE_DOOR_GUARD"
GUARD_HOME, GUARD_BLOCKING = (5, 3), (4, 2)


def guard_local_id() -> tuple[int, tuple[int, int]]:
    """(localId, (x, y) de origem) do porteiro: o mapjson numera os local_id pela posição."""
    path = REPO_ROOT / "data" / "maps" / "IndigoPlateau_PokemonCenter_1F" / "map.json"
    events = json.loads(path.read_text(encoding="utf-8"))["object_events"]
    for i, ev in enumerate(events):
        if ev.get("local_id") == GUARD_NAME:
            return i + 1, (ev["x"], ev["y"])
    raise AssertionError(f"{GUARD_NAME} não está em {path}")


class NationalDexScenario(SummaryEvolutionScenario):
    def _var(self, name: str) -> int:
        var_id = header_defines(REPO_ROOT, "vars.h")[name]
        sb1 = self.emu.read_u32(self.game.syms.addr("gSaveBlock1Ptr"))
        return self.emu.read_u16(sb1 + SB1_VARS + (var_id - VAR_BASE) * 2)

    def _dex_ready(self) -> bool:
        return (self.game.callback2() == POKEDEX_CB and POKEDEX_TASK in self._tasks()
                and self.game.task_data(LIST_TASK) is not None and not self._fade_active())

    def _mode_list_items(self) -> int:
        data = self.game.task_data(LIST_TASK)
        assert data is not None, "nenhuma lista de menu ativa"
        return (data[0] & 0xFFFF) | (data[1] & 0xFFFF) << 16

    def _back_to_field(self, what: str) -> None:
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             f"volta ao menu START ({what})", tries=8, wait=120)
        self.menu.close_start_menu()

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="dex_nacional_continue")
        return "CONTINUAR com o save do modo rápido"

    def _flag_off(self) -> str:
        flag = self.game.flag(self.consts.flag("FLAG_SYS_NATIONAL_DEX"))
        var = self._var("VAR_NATIONAL_DEX")
        assert not flag, "FLAG_SYS_NATIONAL_DEX ligada no save do modo rápido"
        assert var != NATIONAL_DEX_MAGIC, f"VAR_NATIONAL_DEX = {var:#x}"
        return f"FLAG_SYS_NATIONAL_DEX desligada, VAR_NATIONAL_DEX = {var:#x}"

    def _national_screen(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEDEX)
        self.ctl.wait_until(self._dex_ready, SCREEN_TIMEOUT, "Pokédex pronta")
        items, syms = self._mode_list_items(), self.game.syms
        nat = syms.addr("sListMenuItems_NatDexModeSelect")
        kanto = syms.addr("sListMenuItems_KantoDexModeSelect")
        self.emu.frames(SETTLE_FRAMES)
        path = self._shot("pokedex_nacional")
        self.measures.setdefault("shots_by_name", {})["pokedex_nacional"] = path
        self._back_to_field("Pokédex")
        assert items != kanto, "a Pokédex abriu com a lista de modos de Kanto"
        assert items == nat, f"lista de modos em {items:#x}, esperava a nacional ({nat:#x})"
        return f"lista de modos nacional (itens em {items:#x}); tela em {path}"

    def _summary_number(self) -> str:
        self.box.set_party_mon(0, self._sp(LARVITAR), 20)
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self._open_summary(0)
        base = self.emu.read_u32(self.game.syms.addr("sMonSummaryScreen"))
        raw = self.emu.read(base + SUMMARY_SCAN[0], SUMMARY_SCAN[1] - SUMMARY_SCAN[0])
        number = self.game.charmap.encode(f"{LARVITAR_DEX_NUMBER:03d}") + b"\xff"
        found = [i for i in range(0, len(raw) - 4, 4) if raw[i:i + 4] == number]
        assert found, "o resumo não guarda o número 246 (dexNumStrBuf)"
        self._close_summary("número no resumo")
        self._back_to_field("resumo")
        return f"Larvitar: o resumo guarda '{LARVITAR_DEX_NUMBER}' (offset {SUMMARY_SCAN[0] + found[0]:#x})"

    def _league_door(self) -> str:
        local_id, home = guard_local_id()
        assert home == GUARD_HOME, home
        group, num = self.consts.map(LEAGUE_MAP)
        self.box.call(CMD_WARP, group | num << 8, 4 | 4 << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para a Liga")
        self.ctl.wait_overworld_idle(600)
        raw = self.emu.read(self.game.syms.addr("gObjectEvents"),
                            OBJECT_EVENT_SIZE * OBJECT_EVENT_COUNT)
        for i in range(OBJECT_EVENT_COUNT):
            obj = raw[i * OBJECT_EVENT_SIZE:(i + 1) * OBJECT_EVENT_SIZE]
            if obj[0] & 1 and obj[0x08] == local_id and obj[0x09] == num and obj[0x0A] == group:
                x, y = struct.unpack_from("<hh", obj, 0x10)
                pos = (x - MAP_OFFSET, y - MAP_OFFSET)
                assert pos != GUARD_BLOCKING, f"porteiro foi para {GUARD_BLOCKING}: a Liga abriu"
                assert pos == GUARD_HOME, f"porteiro em {pos}, esperava {GUARD_HOME}"
                return f"sem a Liga vencida o porteiro continua em {pos} (não foi para {GUARD_BLOCKING})"
        raise AssertionError(f"porteiro (localId {local_id}) não está nos objetos do mapa")

    def run(self) -> None:
        try:
            self._flow("dex_nacional: CONTINUAR com o save do modo rápido", self._start)
            self._flow("dex/flag_desligada: a flag do pós-Liga continua desligada", self._flag_off)
            res = self.suite.run("dex/tela_nacional: START > POKéDEX com a lista nacional",
                                 self._national_screen)
            shot = self.measures.get("shots_by_name", {}).get("pokedex_nacional")
            if shot:
                res.images.append(shot)
            if res.status == "falha":
                raise Abort("tela_nacional")
            self._flow("dex/numero_no_resumo: Larvitar mostra 246, não ???", self._summary_number)
            self._flow("dex/porta_da_liga: o porteiro não abre sem a Liga vencida",
                       self._league_door)
        except Abort:
            pass


def run_full_national_dex(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    NationalDexScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only dex_nacional ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "dex_nacional", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
