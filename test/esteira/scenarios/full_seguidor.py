"""Modo completo: Pokémon seguidor (POK-48), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`), com o aviso das conquistas em
silêncio. A preparação (`_start`, savestate `seguidor_base`) põe um CHARMANDER nv 50 (nunca shiny) no 1º lugar da
equipe, o relógio no dia 0 ao meio-dia (tarde: tom neutro, clima limpo), Repel ligado (nenhum selvagem atrapalha os
passos) e o jogador em Pallet Town (12, 9), virado para o sul. A Task 2 só cria o seguidor (ele ainda não anda: a
Task 3 faz o passo); os pontos daqui não o fazem andar.

- `seguidor/aparece`: depois do warp, existe, espécie CHARMANDER, sem shiny, visível, no tile atrás do jogador (12, 8),
  virado para o sul, 1 objeto com o localId do seguidor (foto `seguidor_parado`);
- `seguidor/parado_anima`: lido a cada quadro, o quadro da animação parada alterna 0/1 em trechos de exatamente
  FOLLOWER_IDLE_FRAMES quadros (include/follower.h);
- `seguidor/warp`: Cidade de Viridian, entrar no Centro Pokémon pela porta e sair: 1 objeto do seguidor em cada mapa;
- `seguidor/borda_mapa`: Rota 1 → Pallet Town pela conexão (sem warp), 11 tiles para o sul, longe o bastante para
  `RemoveObjectEventsOutsideView` apagar um NPC; de volta à Rota 1: 1 objeto dos dois lados, no mesmo tile;
- `seguidor/save_continuar`: salvar, ver que o save não tem o seguidor, resetar e CONTINUAR: o seguidor é recriado
  da equipe, atrás do jogador, 1 objeto;
- `seguidor/noite`: às 22:00 a paleta do seguidor (slot PALSLOT_FOLLOWER) recebe o tom, como a do jogador (foto
  `seguidor_noite`);
- `seguidor/paleta_especial`: no cais do S.S. Anne, a paleta do navio (slot 10) e a do seguidor (slot 11) são as do
  ROM, ao mesmo tempo (foto `seguidor_paleta_especial`); no porto da Ilha Um (o Seagallop usa o slot 11 para o
  reflexo) o seguidor não aparece.

As telas `seguidor_*` são novas: ficam para a aprovação do Cintra (Task 5).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only seguidor
"""

import re
import sys

from ..breeding import header_defines
from ..hooks import CMD_SET_VAR, CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

CLOCK = (0, 12 * 60)          # dia 0, 12:00: tarde, tom neutro (sTints[TIME_AFTERNOON] = 256, 256, 256)
NIGHT = 22 * 60
LEAD = ("CHARMANDER", 50)
PALLET = ("MAP_PALLET_TOWN", (12, 9))       # linha 8 livre: o seguidor nasce em (12, 8)
VIRIDIAN_DOOR = ("MAP_VIRIDIAN_CITY", (26, 27))   # logo abaixo da porta do Centro Pokémon (26, 26)
CENTER = "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F"
ROUTE1_SOUTH = ("MAP_ROUTE1", (12, 35))     # x 12 livre até o fim da Rota 1 e até a linha 7 de Pallet
BORDER_STEPS = 11                           # 4 na Rota 1 + 7 em Pallet (até y 6): seguidor a 12 tiles
SS_ANNE_DOCK = ("MAP_SSANNE_EXTERIOR", (32, 12))   # o navio (30, 16) na tela
SEAGALLOP_HARBOR = ("MAP_ONE_ISLAND_HARBOR", (8, 3))
DIR_SOUTH = 1
PALSLOT_FOLLOWER, PALSLOT_NPC_SPECIAL = 11, 10
PLTT_SIZE_4BPP = 32
OBJ_EVENT_SIZE, SB1_OBJECT_EVENTS, OBJECT_EVENTS_COUNT = 0x24, 0x6A0, 16
OBJ_GRAPHICS_ID, OBJ_LOCAL_ID = 5, 8
FOLLOWER_H = REPO_ROOT / "include" / "follower.h"
SCREEN_POINTS = ("seguidor_parado", "seguidor_noite", "seguidor_paleta_especial")


def _follower_define(name: str) -> int:
    m = re.search(rf"#define {name}\s+(0x[0-9A-Fa-f]+|\d+)", FOLLOWER_H.read_text(encoding="utf-8"))
    assert m, f"{name} não está em include/follower.h"
    return int(m.group(1), 0)


class FollowerScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.vars = header_defines(REPO_ROOT, "vars.h")

    # --- utilidades -------------------------------------------------------------------------------------------------
    def _sb(self, n: int) -> int:
        return self.emu.read_u32(self.game.syms.addr(f"gSaveBlock{n}Ptr"))

    def _teleport(self, where: tuple[str, tuple[int, int]]) -> None:
        map_id, (x, y) = where
        group, num = self.consts.map(map_id)
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_id}")
        self.ctl.wait_overworld_idle(900)
        self.emu.frames(30)

    def _state(self) -> dict:
        state = self.box.follower_state()
        assert state is not None, f"estado do seguidor fora do campo ({self.game.callback2()})"
        return state

    def _expect_one(self, where: str) -> dict:
        state = self._state()
        assert state["existe"] and state["objetos"] == 1, f"{where}: {state}"
        assert state["especie"] == self.consts.species(LEAD[0]), f"{where}: espécie {state['especie']}"
        return state

    def _palette(self, slot: int) -> bytes:
        """Paleta de sprite `slot` em gPlttBufferUnfaded (antes do gamma do clima)."""
        base = self.game.syms.addr("gPlttBufferUnfaded")
        return self.emu.read(base + (16 + slot) * PLTT_SIZE_4BPP, PLTT_SIZE_4BPP)

    def _rom(self, symbol: str) -> bytes:
        return self.emu.read(self.game.syms.addr(symbol), PLTT_SIZE_4BPP)

    def _restore(self) -> None:
        self.ctl.restore("seguidor_base")
        self.emu.frames(12)

    # --- passos -----------------------------------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="seguidor_continue")
        self.box.conq_silencio(True)
        self.box.set_clock(*CLOCK)
        self.box.set_party_mon(0, self.consts.species(LEAD[0]), LEAD[1])
        self.box.call(CMD_SET_VAR, self.vars["VAR_REPEL_STEP_COUNT"], 250)
        self._teleport(PALLET)
        assert self.game.player_xy() == PALLET[1], self.game.player_xy()
        self.ctl.checkpoint("seguidor_base")
        return f"CONTINUAR; {LEAD[0]} nv {LEAD[1]} no 1º lugar, 12:00, Repel; Pallet Town {PALLET[1]}"

    def _aparece(self) -> str:
        self._restore()
        state = self._expect_one("Pallet")
        px, py = self.game.player_xy()
        assert state["xy"] == (px, py - 1), f"seguidor em {state['xy']}, jogador em {(px, py)} virado para o sul"
        assert not state["shiny"] and not state["escondido"], state
        assert state["direcao"] == DIR_SOUTH, state
        self.emu.frames(10)
        self._shot("seguidor_parado")
        return f"seguidor {state} atrás do jogador {(px, py)} (foto seguidor_parado)"

    def _parado_anima(self) -> str:
        self._restore()
        period = _follower_define("FOLLOWER_IDLE_FRAMES")
        frames = [self.box.follower_idle_frame() for _ in range(4 * period + 2)]
        assert set(frames) == {0, 1}, f"quadro parado não alterna: {frames}"
        runs, last, size = [], frames[0], 0
        for f in frames:
            if f == last:
                size += 1
            else:
                runs.append(size)
                last, size = f, 1
        inner = runs[1:]      # o 1º trecho começou antes da leitura
        assert len(inner) >= 2 and all(r == period for r in inner), (
            f"trechos {runs} (cada troca a {period} quadros esperada): {frames}")
        return f"{len(frames)} quadros lidos: troca a cada {period} ({runs})"

    def _warp(self) -> str:
        self._restore()
        self._teleport(VIRIDIAN_DOOR)
        out = self._expect_one("Viridian")
        loc = self.nav.go_through_warp("up")
        assert loc == self.consts.map(CENTER), loc
        self.emu.frames(30)
        inside = self._expect_one("Centro Pokémon")
        loc = self.nav.go_through_warp("down")
        assert loc == self.consts.map(VIRIDIAN_DOOR[0]), loc
        self.emu.frames(30)
        back = self._expect_one("Viridian de volta")
        return f"fora {out['xy']}, dentro {inside['xy']} (escondido {inside['escondido']}), fora de novo {back['xy']}"

    def _borda_mapa(self) -> str:
        self._restore()
        self._teleport(ROUTE1_SOUTH)
        route1, pallet = self.consts.map(ROUTE1_SOUTH[0]), self.consts.map(PALLET[0])
        start = self._expect_one("Rota 1")
        x, y = ROUTE1_SOUTH[1]
        assert start["xy"] == (x, y - 1), start
        moved = self.nav.step("down", BORDER_STEPS)
        assert moved == BORDER_STEPS and self.game.location() == pallet, (moved, self.game.location())
        far = self._expect_one("Pallet, longe do seguidor")
        height = 40   # a Rota 1 tem 40 de altura: em coordenadas de Pallet o seguidor fica em y - 40
        assert far["xy"] == (x, y - 1 - height), far
        moved = self.nav.step("up", BORDER_STEPS)
        assert moved == BORDER_STEPS and self.game.location() == route1, (moved, self.game.location())
        back = self._expect_one("Rota 1 de volta")
        assert back["xy"] == (x, y - 1), back
        return f"Rota 1 {start['xy']} → Pallet {far['xy']} (12 tiles) → Rota 1 {back['xy']}: 1 objeto sempre"

    def _saved_followers(self) -> list[int]:
        base = self._sb(1) + SB1_OBJECT_EVENTS
        raw = self.emu.read(base, OBJ_EVENT_SIZE * OBJECT_EVENTS_COUNT)
        local = _follower_define("OBJ_EVENT_ID_FOLLOWER")
        return [i for i in range(OBJECT_EVENTS_COUNT)
                if raw[i * OBJ_EVENT_SIZE] & 1 and raw[i * OBJ_EVENT_SIZE + OBJ_LOCAL_ID] == local]

    def _save_continuar(self) -> str:
        self._restore()
        before = self._expect_one("antes de salvar")
        status = self.menu.save_game()
        assert status == 1, f"gSaveAttemptStatus = {status}"
        saved = self._saved_followers()
        assert not saved, f"o seguidor foi para o save (slots {saved})"
        self.emu.flush_save()
        self.emu.reset()
        self._title_to_continue("tela de título depois do reset", shot="seguidor_save_continue")
        self.box.conq_silencio(True)
        self.emu.frames(30)
        after = self._expect_one("depois de CONTINUAR")
        px, py = self.game.player_xy()
        assert after["xy"] == (px, py - 1) and after["xy"] == before["xy"], (before, after, (px, py))
        return f"save sem o seguidor; CONTINUAR: {after}"

    def _noite(self) -> str:
        self._restore()
        rom = self._rom("sFollowerPal_Charmander")
        day, player_day = self._palette(PALSLOT_FOLLOWER), self._palette(0)
        assert day == rom, "ao meio-dia (tom neutro) a paleta do seguidor não é a do ROM"
        self.box.set_clock(0, NIGHT)
        self.ctl.wait_until(lambda: self._palette(PALSLOT_FOLLOWER) != day, 600, "tom da noite no seguidor")
        self.emu.frames(30)
        night = self._palette(PALSLOT_FOLLOWER)
        assert night != rom and self._palette(0) != player_day, "à noite o seguidor ou o jogador ficaram sem tom"
        self._expect_one("à noite")
        self._shot("seguidor_noite")
        return f"22:00: paleta do seguidor com tom ({rom[:4].hex()} → {night[:4].hex()}); foto seguidor_noite"

    def _paleta_especial(self) -> str:
        self._restore()
        self.box.set_flag(self.consts.flag("FLAG_HIDE_SS_ANNE"), False)
        self._teleport(SS_ANNE_DOCK)
        self._expect_one("cais do S.S. Anne")
        ship, follower = self._palette(PALSLOT_NPC_SPECIAL), self._palette(PALSLOT_FOLLOWER)
        assert ship == self._rom("gObjectEventPal_SSAnne"), "paleta do S.S. Anne (slot 10) errada"
        assert follower == self._rom("sFollowerPal_Charmander"), "paleta do seguidor (slot 11) errada no cais"
        self._shot("seguidor_paleta_especial")
        self._teleport(SEAGALLOP_HARBOR)
        state = self._state()
        assert not state["existe"] and state["objetos"] == 0, f"seguidor no porto do Seagallop: {state}"
        return "S.S. Anne no slot 10 e seguidor no 11 com as cores do ROM; no porto do Seagallop, sem seguidor"

    def run(self) -> None:
        try:
            self._flow("seguidor: CONTINUAR, CHARMANDER no 1º lugar, 12:00 e Pallet Town", self._start)
            self.suite.run("seguidor/aparece: atrás do jogador, espécie certa, 1 objeto", self._aparece)
            self.suite.run("seguidor/parado_anima: alterna os 2 quadros parado", self._parado_anima)
            self.suite.run("seguidor/warp: entra e sai do Centro Pokémon, 1 objeto", self._warp)
            self.suite.run("seguidor/borda_mapa: Rota 1 ↔ Pallet sem sumir nem duplicar", self._borda_mapa)
            self.suite.run("seguidor/save_continuar: fora do save, recriado ao CONTINUAR", self._save_continuar)
            self.suite.run("seguidor/noite: paleta do seguidor com o tom da noite", self._noite)
            self.suite.run("seguidor/paleta_especial: S.S. Anne e seguidor com as cores certas",
                           self._paleta_especial)
        except Abort:
            pass


def run_full_seguidor(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    FollowerScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only seguidor ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "seguidor", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
