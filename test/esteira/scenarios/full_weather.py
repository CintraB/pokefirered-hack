"""Modo completo: clima dinâmico por região e período (Hack 7, frente A, Task 4), na build de teste.

O clima de um mapa externo com header NONE/SUNNY/SUNNY_CLOUDS sai de um sorteio por (região,
dia do clima, período) — tabela e hash em esteira/dia_noite.py; o dia do clima vira às 04:00.
Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`):

- `clima/hook`: ROLL_WEATHER do jogo == `dia_noite.roll_weather` em 2000 (região, dia, período)
  sorteados (todas as regiões);
- `clima/neve`: um dia em que Four Island (SNOW) sorteia neve de manhã, 06:00, atalho WARP →
  clima atual e gSaveBlock1Ptr->weather == WEATHER_SNOW (tela `clima_neve`);
- `clima/interior`: Centro Pokémon de Four Island → WEATHER_NONE; sair pela porta → neve de novo;
- `clima/troca_de_periodo`: Rota 3 (SAND) num dia em que manhã e tarde sorteiam climas
  diferentes, 09:59 → ao virar a tarde (jogador livre) o clima passa ao da tarde;
- `clima/volta_da_bolsa`: outro dia assim, a tarde chega com a bolsa aberta → na volta ao campo
  (ResumeMap restaura o clima salvo) o clima passa ao da tarde quando o jogador fica livre;
- `clima/fixo`: Viridian Forest (SHADE no header) e Pokémon Tower 3F (neblina) não mudam em
  relógios cujo sorteio de INLAND não é NONE;
- `clima/caverna`: Mt. Moon (subterrâneo) → WEATHER_NONE com o mesmo tipo de sorteio.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only clima
"""

import random
import sys

from .. import dia_noite as dn
from ..emu import KEY_B
from ..field_menu import STARTMENU_BAG
from ..hooks import CMD_SET_VAR
from . import ScenarioContext
from .base import TEXT_PERIOD, Abort
from .full_clock import ClockScenario

# struct Weather (include/field_weather.h): union de sprites 0x200 + 2 tabelas de gamma 0x4C0
WEATHER_CURR = 0x6D0                # currWeather (GetCurrentWeather)
WEATHER_NEXT = 0x6D1                # nextWeather
SB1_WEATHER = 0x2E                  # gSaveBlock1Ptr->weather (include/global.h)
HOOK_SAMPLES = 2000
HOOK_SEED = 0x7A73
MAX_DAY = 1 << 20

FOUR_ISLAND_SPOT = (18, 21)         # em frente à porta do Centro Pokémon (18, 20)
VAR_MAP_SCENE_FOUR_ISLAND = 0x4086  # include/constants/vars.h: 1 = cena do rival já vista
FOUR_ISLAND_CENTER = "MAP_FOUR_ISLAND_POKEMON_CENTER_1F"
CENTER_SPOT, CENTER_EXIT = (7, 6), (7, 7)   # porta de saída em (7, 8)
ROUTE3_SPOT = (65, 13)              # leste da Rota 3, longe da visão dos treinadores
FIXED_MAPS = (("MAP_VIRIDIAN_FOREST", (29, 61), dn.WEATHER_SHADE),
              ("MAP_POKEMON_TOWER_3F", (5, 10), dn.WEATHER_FOG_HORIZONTAL))
CAVE = ("MAP_MT_MOON_1F", (18, 36))
PERIOD_FLIP_FRAMES = dn.FRAMES_PER_MINUTE + 1200


def _name(weather: int) -> str:
    return dn.WEATHER_BY_ID.get(weather, str(weather)).removeprefix("WEATHER_")


def _first_day(pred, start: int = 1) -> int:
    return next(d for d in range(start, start + 5000) if pred(d))


class WeatherScenario(ClockScenario):
    # --- utilidades ----------------------------------------------------------------
    def _weather_base(self) -> int:
        return self.emu.read_u32(self.game.syms.addr("gWeatherPtr"))

    def _current_weather(self) -> int:
        return self.emu.read_u8(self._weather_base() + WEATHER_CURR)

    def _next_weather(self) -> int:
        return self.emu.read_u8(self._weather_base() + WEATHER_NEXT)

    def _saved_weather(self) -> int:
        return self.emu.read_u8(self.emu.read_u32(self.game.syms.addr("gSaveBlock1Ptr")) + SB1_WEATHER)

    def _expect_weather(self, want: int, where: str) -> str:
        curr, saved = self._current_weather(), self._saved_weather()
        assert (curr, saved) == (want, want), (
            f"{where}: clima atual {_name(curr)}, salvo {_name(saved)}; esperava {_name(want)}")
        return f"{where}: {_name(want)}"

    def _rolled_inland_days(self, count: int) -> list[tuple[int, int, int]]:
        """(dia, minuto, clima) de manhã e de noite em que INLAND sorteia algo ≠ NONE."""
        out = []
        for period, minute in ((dn.MORNING, 6 * 60), (dn.NIGHT, 22 * 60)):
            day = 1
            while len([o for o in out if o[1] == minute]) < count:
                rolled = dn.roll_weather(dn.REGION_INLAND, day, period)
                if rolled != dn.WEATHER_NONE:
                    out.append((day, minute, rolled))
                day += 1
        return out

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        """CONTINUAR e campo livre: a última cena do diário de viagem pode deixar uma fala na
        tela (B avança)."""
        detail = super()._start()
        spent = 0
        while not self._settled_idle():
            assert spent < 3000, "campo não ficou livre depois do CONTINUAR"
            self._press(KEY_B)
            spent += TEXT_PERIOD
        return f"{detail}; campo livre depois de {spent} quadros"

    def _hook(self) -> str:
        rng = random.Random(HOOK_SEED)
        diffs, seen = [], set()
        for i in range(HOOK_SAMPLES):
            region = i % dn.REGION_COUNT
            day, period = rng.randrange(MAX_DAY), rng.randrange(4)
            got, want = self.box.roll_weather(region, day, period), dn.roll_weather(region, day, period)
            seen.add(want)
            if got != want:
                diffs.append(f"{dn.REGION_NAMES[region]} dia {day} {dn.PERIOD_NAMES[period]}: "
                             f"jogo {_name(got)}, Python {_name(want)}")
        assert not diffs, f"{len(diffs)} de {HOOK_SAMPLES} diferentes: {'; '.join(diffs[:4])}"
        return (f"{HOOK_SAMPLES} sorteios iguais ao espelho (todas as regiões); climas vistos: "
                f"{', '.join(sorted(_name(w) for w in seen))}")

    def _snow(self) -> str:
        snow_day = _first_day(
            lambda d: dn.roll_weather(dn.REGION_SNOW, d, dn.MORNING) == dn.WEATHER_SNOW)
        self.box.call(CMD_SET_VAR, VAR_MAP_SCENE_FOUR_ISLAND, 1)   # sem a cena do rival na chegada
        self.box.set_clock(snow_day, 6 * 60)
        self._warp_to("MAP_FOUR_ISLAND", FOUR_ISLAND_SPOT)
        detail = self._expect_weather(dn.WEATHER_SNOW, f"Four Island, dia {snow_day} 06:00")
        self.emu.frames(120)   # flocos na tela
        self._shot("clima_neve")
        return detail

    def _interior(self) -> str:
        self._warp_to(FOUR_ISLAND_CENTER, CENTER_SPOT)
        steps = [self._expect_weather(dn.WEATHER_NONE, "Centro Pokémon de Four Island")]
        self._walk(*CENTER_EXIT)
        self._warp("down", "MAP_FOUR_ISLAND")
        self._settle("saída do Centro Pokémon")
        minute, _ = self.box.clock_info()
        assert dn.period_at(minute) == dn.MORNING, f"relógio em {self._hhmm(minute)}"
        steps.append(self._expect_weather(dn.WEATHER_SNOW, "saída pela porta"))
        return "; ".join(steps)

    @staticmethod
    def _route3(day: int, period: int) -> int:
        """Clima que a Rota 3 (SAND, header SUNNY) mostra no período do dia."""
        minute = 6 * 60 if period == dn.MORNING else 12 * 60
        return dn.map_weather(dn.WEATHER_SUNNY, dn.REGION_SAND, True, day, minute)

    def _route3_change_day(self, start: int) -> tuple[int, int, int]:
        """(dia, clima da manhã, clima da tarde) do 1º dia ≥ start em que eles diferem."""
        day = _first_day(lambda d: self._route3(d, dn.MORNING) != self._route3(d, dn.AFTERNOON), start)
        return day, self._route3(day, dn.MORNING), self._route3(day, dn.AFTERNOON)

    def _wait_weather(self, want: int, since: str) -> int:
        """Espera clima atual e salvo == want; devolve os quadros gastos."""
        spent = 0
        while self._current_weather() != want or self._saved_weather() != want:
            assert spent < PERIOD_FLIP_FRAMES, (
                f"{spent} quadros depois de {since}: clima atual {_name(self._current_weather())}, "
                f"próximo {_name(self._next_weather())}, salvo {_name(self._saved_weather())}; "
                f"esperava {_name(want)}")
            self.emu.frames(10)
            spent += 10
        return spent

    def _period_change(self) -> str:
        day, morning, afternoon = self._route3_change_day(1)
        self.change_day = day
        self.box.set_clock(day, 9 * 60 + 50)
        self._warp_to("MAP_ROUTE3", ROUTE3_SPOT)
        before = self._expect_weather(morning, f"Rota 3, dia {day} manhã")
        self.box.set_clock(day, 9 * 60 + 59)
        spent = self._wait_weather(afternoon, "09:59")
        minute, period = self.box.clock_info()
        assert period == dn.AFTERNOON, f"clima trocou ainda de manhã ({self._hhmm(minute)})"
        self._shot("clima_troca_de_periodo")
        return f"{before} → tarde: {_name(afternoon)} ({spent} quadros depois de 09:59)"

    def _bag_return(self) -> str:
        """A tarde chega com a bolsa aberta: na volta ao campo (CB2_ReturnToField, que restaura
        o clima salvo) o clima passa ao da tarde."""
        day, morning, afternoon = self._route3_change_day(self.change_day + 1)
        self.box.set_clock(day, 9 * 60 + 50)
        self._warp_to("MAP_ROUTE3", ROUTE3_SPOT)
        before = self._expect_weather(morning, f"Rota 3, dia {day} manhã")
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_BAG)
        self.menu.bag.wait_ready()
        self.box.set_clock(day, 10 * 60 + 5)
        self.emu.frames(60)
        self.ctl.press_until(KEY_B, lambda: not self.menu.bag.ready(), "bolsa fechada")
        self.ctl.wait_until(self.menu.start_menu_open, 600, "menu START depois da bolsa")
        assert self._saved_weather() == morning, (
            f"clima salvo {_name(self._saved_weather())} já na volta da bolsa, esperava "
            f"{_name(morning)} até o jogador ficar livre")
        self.menu.close_start_menu()
        spent = self._wait_weather(afternoon, "fechar o menu")
        return f"{before}; tarde chegou na bolsa → {_name(afternoon)} {spent} quadros depois de fechar o menu"

    def _fixed(self) -> str:
        details = []
        for map_name, spot, header in FIXED_MAPS:
            for day, minute, rolled in self._rolled_inland_days(1):
                self.box.set_clock(day, minute)
                self._warp_to(map_name, spot)
                details.append(self._expect_weather(
                    header, f"{map_name} dia {day} {self._hhmm(minute)} (sorteio {_name(rolled)})"))
        return "; ".join(details)

    def _cave(self) -> str:
        map_name, spot = CAVE
        day, minute, rolled = self._rolled_inland_days(1)[0]
        self.box.set_clock(day, minute)
        self._warp_to(map_name, spot)
        return self._expect_weather(
            dn.WEATHER_NONE, f"{map_name} dia {day} {self._hhmm(minute)} (sorteio {_name(rolled)})")

    def run(self) -> None:
        try:
            self._flow("clima: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("clima/hook: ROLL_WEATHER do jogo = espelho Python em 2000 sorteios",
                           self._hook)
            self._flow("clima/neve: Four Island de manhã num dia de neve", self._snow)
            self._flow("clima/interior: Centro Pokémon sem clima, neve de novo na saída",
                       self._interior)
            self._flow("clima/troca_de_periodo: Rota 3 troca o clima ao virar a tarde",
                       self._period_change)
            self._flow("clima/volta_da_bolsa: a tarde chega com a bolsa aberta",
                       self._bag_return)
            self._flow("clima/fixo: Viridian Forest e Pokémon Tower mantêm o clima do header",
                       self._fixed)
            self._flow("clima/caverna: Mt. Moon sem clima", self._cave)
        except Abort:
            pass


def run_full_weather(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    WeatherScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only clima ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "clima", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
