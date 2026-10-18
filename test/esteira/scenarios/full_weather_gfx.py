"""Modo completo: neve, cinzas, areia e neblina visíveis no campo (Hack 7), na build de teste.

O FRLG herdou esses climas do RSE e nenhum mapa os usa. Sessão própria da ROM de teste a partir
do .sav do `captura` (`save_from="captura"`): CONTINUAR, relógio às 12:00 (tarde, sem tom de
dia/noite), warp para a Rota 1 e um savestate do céu limpo. Cada clima é injetado como na
prévia (gWeatherPtr->nextWeather, finishStep = 0, weatherChangeComplete = 0, o mesmo que
SetNextWeather faz) a partir desse savestate e o jogo roda 1500 quadros:

1. `clima_visual/neve`: os flocos continuam caindo (pelo menos 10 entradas do OAM na tela com o
   tile de um floco, em todas as amostras do fim) e mudam a tela (pixels cinza-claros que o
   céu limpo não tem >= 0,5% da tela);
2. `clima_visual/cinzas`: BLDCNT/BLDALPHA iguais aos que o código do Emerald deixa (BLDCNT do
   campo, BLDALPHA 16/0) e os 20 sprites de cinza na tela;
3. `clima_visual/areia`: os mesmos registradores e a paleta dos sprites = sandstorm.gbapal;
4. `clima_visual/areia_troca`: areia -> neve sem trocar de mapa: os flocos voltam a usar a paleta
   padrão do clima (default.gbapal), e não a da areia;
5. `clima_visual/neblina`: neblina horizontal num mapa externo com a intensidade nova
   (FOG_OUTDOOR_BLEND, espelho do C); na Pokémon Tower 3F (interior) a original 12/8.

Telas para o Cintra aprovar: telas/clima_<neve|cinzas|areia|neblina>.png (+ clima_limpo,
clima_neblina_torre).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only clima_visual
"""

import struct
import sys
from pathlib import Path

from PIL import Image

from ..breeding import header_defines
from ..hooks import CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

# struct Weather (include/field_weather.h): offsets iguais aos do Emerald
W_SNOW_SPRITES = 0x060     # sprites.s1.snowflakeSprites[]
W_ASH_SPRITES = 0x0F0      # sprites.s2.ashSprites[20]
W_SAND_SPRITES = 0x190     # sprites.s2.sandstormSprites1[20]
W_FINISH_STEP = 0x6CE
W_CURR = 0x6D0
W_NEXT = 0x6D1
W_GFX_LOADED = 0x6D2
W_CHANGE_COMPLETE = 0x6D3
W_SNOW_COUNT = 0x6E4
NUM_ASH_SPRITES = NUM_SANDSTORM_SPRITES = 20

GPU_BLDCNT, GPU_BLDALPHA = 0x50, 0x52          # offsets em sGpuRegBuffer
OAM_BUFFER = 0x38                              # gMain.oamBuffer (include/main.h)
SPRITE_SIZE = 0x44                             # sizeof(struct Sprite)

# BLDCNT do campo (overworld.c: TGT2_BG1|BG2|BG3|OBJ | EFFECT_BLEND), o mesmo no Emerald
FIELD_BLDCNT = 0x0200 | 0x0400 | 0x0800 | 0x1000 | 0x0040


def bldalpha(eva: int, evb: int) -> int:
    return eva | evb << 8


ASH_SAND_BLEND = bldalpha(16, 0)        # Ash_Main/Sandstorm_Main: Weather_SetTargetBlendCoeffs(16, 0, _)
FOG_INDOOR_BLEND = bldalpha(12, 8)      # FogHorizontal_Main do Emerald (interiores: Pokémon Tower)
FOG_OUTDOOR_BLEND = bldalpha(9, 11)     # Hack 7: neblina externa mais fraca (espelho do C)

ROUTE1_SPOT = (12, 20)
TOWER_SPOT = (5, 10)        # ao lado da escada para o 2F, fora da visão das médiuns
NOON = 12 * 60
FRAMES = 1500
MIN_FLAKES = 10
MIN_SNOW_PIXELS = 240 * 160 * 5 // 1000   # 0,5% da tela
SAMPLES, SAMPLE_GAP = 10, 6


def _gbapal(name: str) -> tuple[int, ...]:
    data = (Path(REPO_ROOT) / "graphics" / "weather" / f"{name}.gbapal").read_bytes()
    return struct.unpack("<16H", data[:32])


def _light_gray(p: tuple[int, int, int]) -> bool:
    return min(p) >= 160 and max(p) - min(p) <= 24   # cores do floco: 164..255, cinzas


class WeatherGfxScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.state = str(Path(ctx.out_dir) / "clima_visual_rota1.ss")
        self.clean: Image.Image | None = None
        self.weather = header_defines(Path(REPO_ROOT), "weather.h")

    # --- memória ---------------------------------------------------------------------
    def _wp(self) -> int:
        return self.emu.read_u32(self.game.syms.addr("gWeatherPtr"))

    def _gpu(self, reg: int) -> int:
        return self.emu.read_u16(self.game.syms.addr("sGpuRegBuffer") + reg)

    def _sprite_ptrs(self, offset: int, count: int) -> list[int]:
        raw = self.emu.read(self._wp() + offset, 4 * count)
        return [p for p in struct.unpack(f"<{count}I", raw) if p]

    def _sprite(self, ptr: int) -> dict:
        raw = self.emu.read(ptr, SPRITE_SIZE)
        attr2 = struct.unpack_from("<H", raw, 4)[0]
        return {"tile": attr2 & 0x3FF, "pal": attr2 >> 12, "invisible": bool(raw[0x3E] & 4)}

    def _oam_on_screen(self, tiles: set[int], size: int) -> int:
        """Entradas do gMain.oamBuffer com um desses tiles, ligadas e dentro da tela."""
        raw = self.emu.read(self.game.syms.addr("gMain") + OAM_BUFFER, 128 * 8)
        n = 0
        for i in range(128):
            a0, a1, a2 = struct.unpack_from("<HHH", raw, i * 8)
            if (a2 & 0x3FF) not in tiles or (a0 >> 8) & 3 == 2:   # 2 = escondida
                continue
            x, y = a1 & 0x1FF, a0 & 0xFF
            x = x - 512 if x >= 256 else x
            y = y - 256 if y > 160 else y
            n += x + size > 0 and x < 240 and y + size > 0 and y < 160
        return n

    def _obj_palette(self, slot: int, buffer: str = "gPlttBufferUnfaded") -> tuple[int, ...]:
        addr = self.game.syms.addr(buffer) + (16 + slot) * 32
        return struct.unpack("<16H", self.emu.read(addr, 32))

    def _set_weather(self, weather: int) -> None:
        """O que SetNextWeather faz, escrito na RAM (só a ROM de teste)."""
        wp = self._wp()
        self.emu.write(wp + W_FINISH_STEP, bytes(2))
        self.emu.write(wp + W_NEXT, bytes([weather]))
        self.emu.write(wp + W_CHANGE_COMPLETE, bytes(1))

    def _inject(self, name: str) -> int:
        self.emu.load_state(self.state)
        weather = self.weather[name]
        self._set_weather(weather)
        self.emu.frames(FRAMES)
        curr = self.emu.read_u8(self._wp() + W_CURR)
        assert curr == weather, f"clima atual {curr}, esperava {name} ({weather})"
        return weather

    def _warp(self, map_name: str, spot: tuple[int, int]) -> None:
        group, num = self.consts.map(map_name)
        self.box.call(CMD_WARP, group | num << 8, spot[0] | spot[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_name}")
        self.ctl.wait_overworld_idle(600)

    def _regs(self, what: str, blend: int) -> str:
        bldcnt, alpha = self._gpu(GPU_BLDCNT), self._gpu(GPU_BLDALPHA)
        assert bldcnt == FIELD_BLDCNT, f"{what}: BLDCNT {bldcnt:#06x}, esperava {FIELD_BLDCNT:#06x}"
        assert alpha == blend, f"{what}: BLDALPHA {alpha:#06x}, esperava {blend:#06x}"
        return f"BLDCNT {bldcnt:#06x}, BLDALPHA {alpha:#06x}"

    def _snow_flakes(self) -> tuple[list[dict], int]:
        count = self.emu.read_u8(self._wp() + W_SNOW_COUNT)
        flakes = [self._sprite(p) for p in self._sprite_ptrs(W_SNOW_SPRITES, count)]
        return flakes, self._oam_on_screen({f["tile"] for f in flakes}, 8)

    # --- passos ------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="clima_visual_continue")
        got = self.box.set_clock(0, NOON)
        assert got == NOON, f"SET_CLOCK devolveu {got}, esperava {NOON}"
        self._warp("MAP_ROUTE1", ROUTE1_SPOT)
        self.emu.frames(240)                  # some a placa com o nome do mapa
        self.emu.save_state(self.state)
        self.clean = self.emu.screenshot(self._shot("clima_limpo")).convert("RGB")
        curr = self.emu.read_u8(self._wp() + W_CURR)
        return f"Rota 1 {self.game.player_xy()}, 12:00, clima do mapa {curr}"

    def _snow(self) -> str:
        self._inject("WEATHER_SNOW")
        counts, pixels = [], []
        clean = self.clean.load()
        for i in range(SAMPLES):
            self.emu.frames(SAMPLE_GAP)
            counts.append(self._snow_flakes()[1])
            shot = self.emu.screenshot(self._shot("clima_neve")).convert("RGB").load()
            pixels.append(sum(1 for y in range(160) for x in range(240)
                              if _light_gray(shot[x, y]) and not _light_gray(clean[x, y])))
        flakes, _ = self._snow_flakes()
        hidden = sum(f["invisible"] for f in flakes)
        median = sorted(pixels)[SAMPLES // 2]
        assert min(counts) >= MIN_FLAKES, (
            f"flocos no OAM dentro da tela {counts} (mínimo {MIN_FLAKES}); {len(flakes)} sprites "
            f"de floco, {hidden} escondidos")
        assert median >= MIN_SNOW_PIXELS, (
            f"pixels de neve por amostra {pixels} (mediana {median}), esperava >= "
            f"{MIN_SNOW_PIXELS} (0,5% da tela)")
        return (f"flocos na tela por amostra {counts}; {len(flakes)} sprites ({hidden} "
                f"escondidos); pixels de neve por amostra {pixels} (mediana {median}, "
                f"{median * 100 / 38400:.1f}% da tela)")

    def _particles(self, name: str, offset: int, count: int, shot: str) -> tuple[str, list[dict]]:
        self._inject(name)
        regs = self._regs(name, ASH_SAND_BLEND)
        sprites = [self._sprite(p) for p in self._sprite_ptrs(offset, count)]
        assert len(sprites) == count, f"{len(sprites)} sprites, esperava {count}"
        assert not any(s["invisible"] for s in sprites), "sprite do clima escondido"
        on_screen = self._oam_on_screen({s["tile"] for s in sprites}, 64)
        assert on_screen >= 6, f"só {on_screen} sprites 64x64 do clima na tela"
        self._shot(shot)
        return f"{regs}; {len(sprites)} sprites, {on_screen} entradas do OAM na tela", sprites

    def _ash(self) -> str:
        return self._particles("WEATHER_VOLCANIC_ASH", W_ASH_SPRITES, NUM_ASH_SPRITES,
                               "clima_cinzas")[0]

    def _sand(self) -> str:
        detail, sprites = self._particles("WEATHER_SANDSTORM", W_SAND_SPRITES,
                                          NUM_SANDSTORM_SPRITES, "clima_areia")
        slot = sprites[0]["pal"]
        want = _gbapal("sandstorm")
        for buf in ("gPlttBufferUnfaded", "gPlttBufferFaded"):
            got = self._obj_palette(slot, buf)
            assert got == want, f"paleta OBJ {slot} ({buf}) {got}, esperava sandstorm.gbapal {want}"
        return f"{detail}; paleta OBJ {slot} = sandstorm.gbapal"

    def _sand_to_snow(self) -> str:
        self._inject("WEATHER_SANDSTORM")
        self._set_weather(self.weather["WEATHER_SNOW"])

        def flake_out() -> bool:
            wp = self._wp()
            return (self.emu.read_u8(wp + W_CURR) == self.weather["WEATHER_SNOW"]
                    and self.emu.read_u8(wp + W_SNOW_COUNT) >= 1)

        self.ctl.wait_until(flake_out, 1200, "areia -> neve: primeiro floco")
        flakes, _ = self._snow_flakes()
        slot = flakes[0]["pal"]
        got, want = self._obj_palette(slot), _gbapal("default")
        assert got == want, (f"floco depois da areia com a paleta OBJ {slot} = {got}; esperava a "
                             f"padrão do clima (default.gbapal) {want}")
        return f"areia -> neve sem trocar de mapa: floco na paleta OBJ {slot} = default.gbapal"

    def _fog(self) -> str:
        self._inject("WEATHER_FOG_HORIZONTAL")
        alpha = self._gpu(GPU_BLDALPHA)
        self._shot("clima_neblina")
        assert alpha == FOG_OUTDOOR_BLEND, (
            f"neblina na Rota 1: BLDALPHA {alpha:#06x}, esperava {FOG_OUTDOOR_BLEND:#06x} "
            f"(intensidade externa nova; a do Emerald é {FOG_INDOOR_BLEND:#06x})")
        self._warp("MAP_POKEMON_TOWER_3F", TOWER_SPOT)
        fog = self.weather["WEATHER_FOG_HORIZONTAL"]
        self.ctl.wait_until(lambda: self.emu.read_u8(self._wp() + W_CURR) == fog
                            and self.emu.read_u8(self._wp() + W_GFX_LOADED), 600,
                            "neblina da Pokémon Tower 3F")
        tower = self._gpu(GPU_BLDALPHA)
        self._shot("clima_neblina_torre")
        assert tower == FOG_INDOOR_BLEND, (
            f"Pokémon Tower 3F: BLDALPHA {tower:#06x}, esperava a original {FOG_INDOOR_BLEND:#06x}")
        return f"Rota 1 BLDALPHA {alpha:#06x}; Pokémon Tower 3F {tower:#06x}"

    def run(self) -> None:
        try:
            self._flow("clima_visual: CONTINUAR, 12:00 e Rota 1 com céu limpo", self._start)
            self.suite.run("clima_visual/neve: flocos caindo na tela depois de 1500 quadros",
                           self._snow)
            self.suite.run("clima_visual/cinzas: blend do Emerald e cinzas na tela", self._ash)
            self.suite.run("clima_visual/areia: blend do Emerald e paleta sandstorm.gbapal",
                           self._sand)
            self.suite.run("clima_visual/areia_troca: areia -> neve devolve a paleta padrão",
                           self._sand_to_snow)
            self.suite.run("clima_visual/neblina: mais fraca fora, original na Pokémon Tower",
                           self._fog)
        except Abort:
            pass


def run_full_weather_gfx(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    WeatherGfxScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only clima_visual ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "clima_visual", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
