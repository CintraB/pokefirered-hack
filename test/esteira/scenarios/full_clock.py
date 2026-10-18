"""Modo completo: relógio do jogo (Hack 7), na build de teste.

O relógio conta os quadros jogados em gSaveBlock2Ptr->gameClockFrames (150 quadros = 1 minuto
do jogo; 0 = 08:00 do dia 0), avançado a cada quadro em que o contador de tempo de jogo não
está parado, inclusive depois de travar em 999:59 (esteira/dia_noite.py tem as regras). Sessão própria da ROM de teste a partir do .sav do
`captura` (`save_from="captura"`):

1. `relogio/anda`: 1500 quadros parado no campo avançam 10 minutos;
2. `relogio/salva`: relógio acertado no dia 3, 18:30 (atalho SET_CLOCK), salvo pelo menu
   (START > SALVAR), reset e CONTINUAR → o relógio volta como foi salvo (entardecer, dia 3);
3. `relogio/save_antigo`: gameClockFrames = 0 (como num save de antes do relógio), salvo, reset
   e CONTINUAR → 08:00, manhã.

Tom de cor por período (frente A, Task 3; as cores lidas são as de gPlttBufferFaded, BG 0–12 e
a paleta de NPC azul do OBJ 2, comparadas com as do ROM × o tom de esteira/dia_noite.py):

- `tom/hook`: TINT_AT do jogo == `dia_noite.tint_at` nos 1440 minutos;
- `tom/periodos`: Rota 1 (atalho WARP) às 06:00, 12:00, 18:00 e 22:00 → ROM × tom, uma vez
  (telas `tom_manha`, `tom_tarde`, `tom_entardecer`, `tom_noite`);
- `tom/interior`: Centro Pokémon de Viridian às 22:00 → ROM, sem tom;
- `tom/sem_acumular`: às 22:00, Pallet → menu Start → casa (sem tom) → Pallet → batalha
  selvagem na grama da Rota 1 e fuga: continua ROM × tom uma vez;
- `tom/transicao`: 16:00 na rota, ~62 minutos do jogo parado: cada leitura == ROM × tom do
  minuto, a cor muda em degraus e termina igual à do entardecer.

O relógio não para durante o diálogo de salvar nem depois do CONTINUAR, então o valor salvo
fica entre o acertado e o lido logo depois do save, e o lido depois do CONTINUAR passa do salvo
no máximo pelos quadros jogados desde o reset: as checagens usam esses limites exatos, e o
minuto esperado ganha a folga desses quadros (o detalhe mostra quanto foi).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only relogio
"""

import json
import re
import sys
from functools import cache

from .. import dia_noite as dn
from ..control import OVERWORLD_CALLBACK
from ..emu import KEY_B
from ..hooks import CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

GAME_CLOCK_OFFSET = 0x090   # gameClockFrames em struct SaveBlock2 (include/global.h)
WALK_MINUTES = 10
SAVE_DAY, SAVE_MINUTE = 3, 18 * 60 + 30

# --- Hack 7 frente A: tom de cor por período ---------------------------------------------------
NUM_PALS_IN_PRIMARY, NUM_PALS_TOTAL = 7, 13    # include/fieldmap.h: BG 0–12 = tilesets
OBJ_NPC_BLUE_SLOT = 2                          # PALSLOT_NPC_1 = OBJ_EVENT_PAL_TAG_NPC_BLUE (sObjectPaletteTags0)
OBJ_NPC_BLUE_PAL = "gObjectEventPal_NpcBlue"
PALETTE_FADE_ACTIVE = 7                        # gPaletteFade: bit 7 do byte 7 (`active`, include/palette.h)
# Hack 7 frente A (Task 4): um dia em que Kanto (INLAND) não sorteia clima em nenhum período — o
# gamma da chuva/sombra mudaria as cores do Faded
TINT_DAY = next(d for d in range(1, 1000) if all(
    dn.roll_weather(dn.REGION_INLAND, d, p) == dn.WEATHER_NONE for p in range(4)))
ROUTE1_SPOT = (13, 30)                         # Rota 1, chão livre ao norte da grama da entrada
PALLET_HOUSE_FRONT = (6, 8)                    # porta de casa em (6, 7)
HOUSE_EXIT = (4, 8)
VIRIDIAN_CENTER_SPOT = (7, 6)                  # Centro Pokémon de Viridian, warps em (6..7, 8)
TINT_SHOTS = ((6 * 60, "manha"), (12 * 60, "tarde"), (18 * 60, "entardecer"), (22 * 60, "noite"))
TRANSITION_START = 16 * 60
TRANSITION_SAMPLE = 75                         # quadros entre leituras (meio minuto do jogo)


@cache
def _map_json(map_name: str) -> dict:
    for path in (REPO_ROOT / "data" / "maps").glob("*/map.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("id") == map_name:
            return data
    raise KeyError(map_name)


@cache
def _tileset_palette_symbols(map_name: str) -> tuple[str, str]:
    """(paletas do tileset primário, do secundário) do layout do mapa (layouts.json + headers.h)."""
    layout_id = _map_json(map_name)["layout"]
    layouts = json.loads((REPO_ROOT / "data" / "layouts" / "layouts.json").read_text(encoding="utf-8"))
    layout = next(l for l in layouts["layouts"] if l.get("id") == layout_id)
    headers = (REPO_ROOT / "src" / "data" / "tilesets" / "headers.h").read_text(encoding="utf-8")

    def palettes(tileset: str) -> str:
        m = re.search(r"const struct Tileset " + re.escape(tileset) + r"\s*=\s*\{(.*?)\};", headers, re.S)
        assert m, f"{tileset} não encontrado em headers.h"
        return re.search(r"\.palettes = (\w+),", m.group(1)).group(1)

    return palettes(layout["primary_tileset"]), palettes(layout["secondary_tileset"])


def _outdoors(map_name: str) -> bool:
    """IsMapTypeOutdoors (src/overworld.c)."""
    return _map_json(map_name)["map_type"] in (
        "MAP_TYPE_ROUTE", "MAP_TYPE_TOWN", "MAP_TYPE_CITY", "MAP_TYPE_UNDERWATER", "MAP_TYPE_OCEAN_ROUTE")


class ClockScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None

    # --- utilidades ----------------------------------------------------------------
    def _clock_addr(self) -> int:
        return self.emu.read_u32(self.game.syms.addr("gSaveBlock2Ptr")) + GAME_CLOCK_OFFSET

    def _clock_frames(self) -> int:
        return self.emu.read_u32(self._clock_addr())

    @staticmethod
    def _minutes(frames: int) -> int:
        """Minutos desde o começo do dia 0 para um valor de gameClockFrames."""
        return frames // dn.FRAMES_PER_MINUTE + dn.START_MINUTE

    @staticmethod
    def _hhmm(minute: int) -> str:
        return f"{minute // 60:02d}:{minute % 60:02d}"

    def _save_reset_continue(self, set_clock, shot: str) -> dict:
        """`set_clock()` acerta o relógio; salva pelo menu, reseta e dá CONTINUAR. Devolve os
        gameClockFrames acertado, lido logo depois do save e lido depois do CONTINUAR, e os
        quadros jogados desde o reset (o relógio só pode ter andado isso depois do load)."""
        set_clock()
        frames_set = self._clock_frames()
        self._save()
        frames_saved_max = self._clock_frames()
        self.emu.reset()
        self._title_to_continue("tela de título depois do reset", shot=shot)
        # o reset do core zera o contador de quadros: o valor agora é o jogado desde o reset
        # (se um dia não zerar, só fica maior, e o limite afrouxa em vez de dar falso vermelho)
        elapsed = self.emu.frames(1)

        frames_after = self._clock_frames()
        assert frames_set <= frames_after <= frames_saved_max + elapsed, (
            f"gameClockFrames depois do CONTINUAR = {frames_after}, fora de [{frames_set}, "
            f"{frames_saved_max} + {elapsed} quadros desde o reset]: o relógio não veio do save")
        return {"set": frames_set, "saved_max": frames_saved_max, "after": frames_after,
                "elapsed": elapsed}

    def _check_minute(self, got: int, want: int, slack_frames: int) -> int:
        """Minuto do dia lido x esperado, com ±1 e mais a folga dos quadros em que o relógio
        pode ter corrido entre acertar e ler; devolve a diferença."""
        slack = 1 + -(-slack_frames // dn.FRAMES_PER_MINUTE)
        diff = (got - want) % dn.MINUTES_PER_DAY
        assert diff <= slack or diff >= dn.MINUTES_PER_DAY - 1, (
            f"minuto {self._hhmm(got)}, esperava {self._hhmm(want)} (folga de {slack} min)")
        return diff

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="relogio_continue")
        minute, period = self.box.clock_info()
        return (f"CONTINUAR com o save do modo rápido: relógio em {self._hhmm(minute)} "
                f"({dn.PERIOD_NAMES[period]})")

    def _clock_walk(self) -> str:
        before, _ = self.box.clock_info()
        self.emu.frames(dn.FRAMES_PER_MINUTE * WALK_MINUTES)
        after, period = self.box.clock_info()
        advanced = (after - before) % dn.MINUTES_PER_DAY
        assert abs(advanced - WALK_MINUTES) <= 1, (
            f"{dn.FRAMES_PER_MINUTE * WALK_MINUTES} quadros avançaram {advanced} min "
            f"({self._hhmm(before)} → {self._hhmm(after)}), esperava {WALK_MINUTES}")
        assert period == dn.period_at(after), (period, after)
        return (f"{self._hhmm(before)} → {self._hhmm(after)} ({advanced} min em "
                f"{dn.FRAMES_PER_MINUTE * WALK_MINUTES} quadros), {dn.PERIOD_NAMES[period]}")

    def _saved_clock(self) -> str:
        def set_clock() -> None:
            got = self.box.set_clock(SAVE_DAY, SAVE_MINUTE)
            assert got == SAVE_MINUTE, f"SET_CLOCK devolveu {got}, esperava {SAVE_MINUTE}"

        f = self._save_reset_continue(set_clock, "relogio_salva_continue")
        minute, period = self.box.clock_info()
        diff = self._check_minute(minute, SAVE_MINUTE, f["saved_max"] - f["set"] + f["elapsed"])
        assert period == dn.EVENING, f"período {dn.PERIOD_NAMES[period]}, esperava entardecer"
        day = self._minutes(self._clock_frames()) // dn.MINUTES_PER_DAY
        assert day == SAVE_DAY, f"dia {day}, esperava {SAVE_DAY}"
        return (f"acertado dia {SAVE_DAY} {self._hhmm(SAVE_MINUTE)}; depois do CONTINUAR dia "
                f"{day} {self._hhmm(minute)} (+{diff} min: save e CONTINUAR levaram "
                f"{f['saved_max'] - f['set']} + {f['elapsed']} quadros), "
                f"{dn.PERIOD_NAMES[period]}")

    def _old_save(self) -> str:
        def zero_clock() -> None:
            self.emu.write(self._clock_addr(), bytes(4))   # só a ROM de teste pode escrever

        f = self._save_reset_continue(zero_clock, "relogio_save_antigo_continue")
        minute, period = self.box.clock_info()
        diff = self._check_minute(minute, dn.START_MINUTE, f["saved_max"] + f["elapsed"])
        assert period == dn.MORNING, f"período {dn.PERIOD_NAMES[period]}, esperava manhã"
        return (f"gameClockFrames = 0 salvo; depois do CONTINUAR {self._hhmm(minute)} "
                f"(+{diff} min: save e CONTINUAR levaram {f['saved_max']} + {f['elapsed']} "
                f"quadros), {dn.PERIOD_NAMES[period]}")

    # --- Hack 7 frente A: hora no menu Start e aviso de troca de período ------------------
    def _idle(self, frames: int) -> None:
        self.emu.frames(frames)

    def _popup_period(self) -> int:
        return self.emu.read_u8(self.game.syms.addr("gDayNightPopupPeriod"))

    def _clock_text(self) -> str:
        raw = self.emu.read(self.game.syms.addr("gDayNightClockText"), 20)
        return self.game.charmap.decode(bytes(raw))

    def _menu_text(self, minute: int, shot: str | None) -> str:
        """Acerta o relógio, abre o menu Start e lê o que a janela da hora imprimiu (pode ter
        andado 1 minuto entre acertar e desenhar)."""
        self.box.set_clock(1, minute)
        self.menu.open_start_menu()
        try:
            if shot:
                self._shot(shot)
            want = {f"{m // 60:02d}:{m % 60:02d} " + dn.PERIOD_NAMES[dn.period_at(m)].capitalize()
                    for m in (minute, minute + 1)}
            got = self._clock_text()
            assert got in want, f"janela da hora imprimiu {got!r}, esperava um de {sorted(want)}"
        finally:
            self.menu.close_start_menu()
        return got

    def _clock_menu(self) -> str:
        a = self._menu_text(18 * 60 + 30, "relogio_menu")
        b = self._menu_text(7 * 60, None)
        return f"{a!r} e {b!r}"

    def _notice_night(self) -> str:
        self.box.set_clock(1, 19 * 60 + 30)
        self._idle(400)   # o aviso do entardecer passa e o período fica registrado
        self.box.set_clock(1, 19 * 60 + 59)
        spent = 0
        while self._popup_period() != dn.NIGHT:
            assert spent < 700, f"sem aviso da noite: gDayNightPopupPeriod = {self._popup_period():#x}"
            self._idle(10)
            spent += 10
        self._idle(90)
        self._shot("relogio_aviso_noite")
        return f"aviso da noite {spent} quadros depois de 19:59"

    def _notice_in_menu(self) -> str:
        self.box.set_clock(1, 9 * 60)
        self._idle(400)
        assert self._popup_period() == dn.MORNING, f"período {self._popup_period():#x}"
        self.menu.open_start_menu()
        self.box.set_clock(1, 9 * 60 + 59)
        self._idle(dn.FRAMES_PER_MINUTE + 100)
        assert self._popup_period() == dn.MORNING, "aviso com o menu Start aberto"
        self.menu.close_start_menu()
        spent = 0
        while self._popup_period() != dn.AFTERNOON:
            assert spent < 300, "sem aviso da tarde depois de fechar o menu"
            self._idle(10)
            spent += 10
        return f"nenhum aviso no menu; tarde avisada {spent} quadros depois de fechar"

    def _save_cancel(self) -> str:
        """START > SALVAR > cancelar (B) várias vezes: a janela da hora é recriada a cada volta
        sem vazar janelas (o id fica estável e a janela está aberta com o menu)."""
        syms = self.game.syms
        ids = []
        self.menu.open_start_menu()
        for i in range(4):
            self.menu.choose(4)   # STARTMENU_SAVE
            self._idle(90)
            self.ctl.press_until(KEY_B, lambda: self.menu.accepting_input() and self.menu.start_menu_open(),
                                 f"menu START depois de cancelar o save ({i})", tries=10, wait=60)
            assert self.emu.read_u8(syms.addr("sClockWindowOpen")) == 1, "janela da hora fechada"
            ids.append(self.emu.read_u8(syms.addr("sClockWindowId")))
        assert len(set(ids)) == 1, f"id da janela da hora mudou entre os cancelamentos: {ids}"
        self.menu.close_start_menu()
        assert self.emu.read_u8(syms.addr("sClockWindowOpen")) == 0, "janela da hora vazou"
        return f"4 cancelamentos do save, janela da hora sempre no id {ids[0]}"

    def _no_notice_on_enter(self) -> str:
        def set_clock() -> None:
            self.box.set_clock(1, 20 * 60 + 30)

        self._save_reset_continue(set_clock, "relogio_sem_aviso_continue")
        self._idle(300)
        got = self._popup_period()
        assert got == 0xFF, f"aviso ao entrar no campo: gDayNightPopupPeriod = {got:#x}"
        return "300 quadros no campo depois do CONTINUAR às 20:30, sem aviso"

    # --- Hack 7 frente A: tom de cor por período ---------------------------------------------
    def _fade_active(self) -> bool:
        return bool(self.emu.read_u8(self.game.syms.addr("gPaletteFade") + PALETTE_FADE_ACTIVE) & 0x80)

    def _settle(self, what: str) -> None:
        """Campo livre e sem fade (o Faded só vale a cor final depois do fade-in)."""
        self.ctl.wait_overworld_idle(900)
        self.ctl.wait_until(lambda: not self._fade_active(), 300, f"fim do fade: {what}")
        self.emu.frames(4)

    def _warp_to(self, map_name: str, xy: tuple[int, int]) -> None:
        """Atalho WARP (SetWarpDestination + DoWarp: fade e carga do mapa como numa porta),
        que também serve para entrar de novo no mesmo mapa."""
        group, num = self.consts.map(map_name)
        self._settle(f"antes do warp para {map_name}")
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.callback2() != OVERWORLD_CALLBACK, 300,
                            f"começo do warp para {map_name}")
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_name}")
        self._settle(f"warp para {map_name}")
        self._expect_map(map_name)

    def _u16s(self, addr: int, count: int) -> list[int]:
        raw = self.emu.read(addr, 2 * count)
        return [int.from_bytes(raw[i:i + 2], "little") for i in range(0, len(raw), 2)]

    def _rom_colors(self, map_name: str) -> list[int]:
        """BG 0–12 como LoadMapTilesetPalettes carrega do ROM (cor 0 do BG 0 = preto) e a
        paleta de NPC azul do OBJ 2, sem tom."""
        primary, secondary = _tileset_palette_symbols(map_name)
        syms = self.game.syms
        bg = [0] + self._u16s(syms.addr(primary) + 2, NUM_PALS_IN_PRIMARY * 16 - 1)
        bg += self._u16s(syms.addr(secondary) + 2 * NUM_PALS_IN_PRIMARY * 16,
                         (NUM_PALS_TOTAL - NUM_PALS_IN_PRIMARY) * 16)
        return bg + self._u16s(syms.addr(OBJ_NPC_BLUE_PAL), 16)

    def _faded_colors(self) -> list[int]:
        """As mesmas cores em gPlttBufferFaded (o Unfaded não serve: é ele que leva o tom)."""
        faded = self.game.syms.addr("gPlttBufferFaded")
        return (self._u16s(faded, NUM_PALS_TOTAL * 16)
                + self._u16s(faded + 2 * (256 + OBJ_NPC_BLUE_SLOT * 16), 16))

    def _expected(self, map_name: str, minute: int, times: int = 1) -> list[int]:
        colors = self._rom_colors(map_name)
        if not _outdoors(map_name):
            return colors
        tint = dn.tint_at(minute)
        for _ in range(times):
            colors = [dn.tint_color(c, tint) for c in colors]
        return colors

    @staticmethod
    def _where(i: int) -> str:
        if i < NUM_PALS_TOTAL * 16:
            return f"BG {i // 16} cor {i % 16}"
        return f"OBJ {OBJ_NPC_BLUE_SLOT} cor {i - NUM_PALS_TOTAL * 16}"

    def _check_colors(self, map_name: str, what: str) -> str:
        """Faded == ROM × tom do minuto, uma vez (ou == ROM em mapa interno). O minuto pode ter
        virado durante a leitura: vale o tom de qualquer minuto entre antes − 1 e depois."""
        before, _ = self.box.clock_info()
        got = self._faded_colors()
        after, _ = self.box.clock_info()
        minutes = [(before - 1 + i) % dn.MINUTES_PER_DAY
                   for i in range((after - before) % dn.MINUTES_PER_DAY + 2)]
        for minute in reversed(minutes):
            if got == self._expected(map_name, minute):
                tint = dn.tint_at(minute) if _outdoors(map_name) else "sem tom"
                return f"{what}: {len(got)} cores = ROM × {tint} ({self._hhmm(minute)})"
        want = self._expected(map_name, after)
        bad = [i for i, (g, w) in enumerate(zip(got, want)) if g != w]
        rom = self._rom_colors(map_name)
        twice = self._expected(map_name, after, times=2)
        if got == twice and twice != want:
            verdict = "tom aplicado DUAS vezes"
        elif got == rom and rom != want:
            verdict = "sem tom"
        else:
            verdict = f"{len(bad)} cores diferentes"
        examples = ", ".join(f"{self._where(i)}: {got[i]:#06x} (esperava {want[i]:#06x}, ROM "
                             f"{rom[i]:#06x})" for i in bad[:4])
        raise AssertionError(f"{what} ({map_name}, {self._hhmm(after)}): {verdict}; {examples}")

    def _tint_hook(self) -> str:
        diffs = []
        for minute in range(dn.MINUTES_PER_DAY):
            got, want = self.box.tint_at(minute), dn.tint_at(minute)
            if got != want:
                diffs.append(f"{self._hhmm(minute)}: jogo {got}, Python {want}")
        assert not diffs, f"{len(diffs)} minutos diferentes: {'; '.join(diffs[:4])}"
        return (f"1440 minutos iguais ao espelho; 16:30 = {dn.tint_at(16 * 60 + 30)}, "
                f"22:00 = {dn.tint_at(22 * 60)}")

    def _tint_periods(self) -> str:
        details = []
        for minute, name in TINT_SHOTS:
            self.box.set_clock(TINT_DAY, minute)
            self._warp_to("MAP_ROUTE1", ROUTE1_SPOT)
            details.append(self._check_colors("MAP_ROUTE1", name))
            self._shot(f"tom_{name}")
        return "; ".join(details)

    def _tint_interior(self) -> str:
        self.box.set_clock(TINT_DAY, 22 * 60)
        self._warp_to("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", VIRIDIAN_CENTER_SPOT)
        return self._check_colors("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", "Centro Pokémon às 22:00")

    def _tint_no_accumulation(self) -> str:
        self.box.set_clock(TINT_DAY, 22 * 60)
        self._warp_to("MAP_PALLET_TOWN", PALLET_HOUSE_FRONT)
        steps = [self._check_colors("MAP_PALLET_TOWN", "chegada em Pallet")]
        self.menu.open_start_menu()
        self.menu.close_start_menu()
        self._settle("menu Start fechado")
        steps.append(self._check_colors("MAP_PALLET_TOWN", "menu Start aberto e fechado"))
        self._warp(None, "MAP_PALLET_TOWN_PLAYERS_HOUSE_1F")
        self._settle("dentro de casa")
        steps.append(self._check_colors("MAP_PALLET_TOWN_PLAYERS_HOUSE_1F", "dentro de casa"))
        self._walk(*HOUSE_EXIT)
        self._warp(None, "MAP_PALLET_TOWN")
        self._settle("saída de casa")
        steps.append(self._check_colors("MAP_PALLET_TOWN", "saída de casa"))
        self._go_to_grass()
        self._find_wild_battle()
        self._escape_battle()
        self._settle("volta da batalha")
        self._expect_map("MAP_ROUTE1")
        steps.append(self._check_colors("MAP_ROUTE1", "volta da batalha selvagem"))
        return "; ".join(steps)

    def _tint_transition(self) -> str:
        """16:00 na rota, 60 minutos do jogo parado: o tom anda em degraus até o do entardecer."""
        self._warp_to("MAP_ROUTE1", ROUTE1_SPOT)
        rom = self._rom_colors("MAP_ROUTE1")
        ref = max(range(1, NUM_PALS_TOTAL * 16), key=lambda i: ((rom[i] >> 5) & 31) + (rom[i] >> 10 & 31))
        self.box.set_clock(TINT_DAY, TRANSITION_START)
        self.emu.frames(4)   # o FieldUpdate do próximo quadro já retinge (noite → tarde)
        values, spent = [], 0
        while True:
            self._check_colors("MAP_ROUTE1", "transição")
            minute, _ = self.box.clock_info()
            values.append(self._faded_colors()[ref])
            if minute >= dn.EVENING_START_HOUR * 60 + 2:
                break
            assert spent < 60 * dn.FRAMES_PER_MINUTE + 1200, f"relógio em {self._hhmm(minute)}"
            self.emu.frames(TRANSITION_SAMPLE)
            spent += TRANSITION_SAMPLE
        steps = [v for i, v in enumerate(values) if i == 0 or v != values[i - 1]]
        for a, b in zip(steps, steps[1:]):
            assert ((b >> 5) & 31) <= ((a >> 5) & 31) and ((b >> 10) & 31) <= ((a >> 10) & 31), (
                f"{self._where(ref)} clareou no meio da transição: {a:#06x} → {b:#06x}")
        assert len(steps) >= 3, f"{self._where(ref)} mudou em só {len(steps)} degraus: {steps}"
        assert values[-1] == dn.tint_color(rom[ref], dn.PERIOD_TINTS[dn.EVENING])
        return (f"{len(values)} leituras em {spent} quadros, todas = ROM × tom do minuto; "
                f"{self._where(ref)}: {' → '.join(f'{v:#06x}' for v in steps)} (entardecer)")

    def run(self) -> None:
        try:
            self._flow("relogio: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("relogio/anda: 1500 quadros no campo = 10 minutos", self._clock_walk)
            self._flow("relogio/salva: dia 3 18:30 sobrevive a salvar, reset e CONTINUAR",
                       self._saved_clock)
            self._flow("relogio/save_antigo: gameClockFrames = 0 começa às 08:00 (manhã)",
                       self._old_save)
            self._flow("relogio/menu: hora no menu Start", self._clock_menu)
            self._flow("relogio/aviso: aviso da noite com o jogador livre", self._notice_night)
            self._flow("relogio/aviso_no_menu: sem aviso com o menu aberto", self._notice_in_menu)
            self._flow("relogio/save_cancelado: janela da hora sem vazar", self._save_cancel)
            self._flow("relogio/sem_aviso_ao_entrar: CONTINUAR às 20:30 não avisa",
                       self._no_notice_on_enter)
            self.suite.run("tom/hook: TINT_AT do jogo = espelho Python nos 1440 minutos", self._tint_hook)
            self._flow("tom/periodos: Rota 1 às 06, 12, 18 e 22 h = ROM × tom, uma vez",
                       self._tint_periods)
            self._flow("tom/interior: Centro Pokémon de Viridian às 22:00 sem tom", self._tint_interior)
            self._flow("tom/sem_acumular: menu, casa e batalha às 22:00 não acumulam o tom",
                       self._tint_no_accumulation)
            self._flow("tom/transicao: 16:00 → 17:00 na rota em degraus até o entardecer",
                       self._tint_transition)
        except Abort:
            pass


def run_full_clock(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    ClockScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only relogio ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "relogio", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
