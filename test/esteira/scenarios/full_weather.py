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
- `clima/caverna`: Mt. Moon (subterrâneo) → WEATHER_NONE com o mesmo tipo de sorteio;
- `clima/batalha_granizo` (Task 5): Four Island com neve, atalho START_WILD_BATTLE (Pikachu nível 5)
  → depois da abertura gBattleWeather tem B_WEATHER_HAIL_PERMANENT, a mensagem "Começou a cair
  granizo!" (tela `batalha_granizo`); aí gWishFutureKnock.weatherDuration = 1 na RAM (o granizo
  temporário acabaria no fim do 1º turno: sem a guarda de B_WEATHER_HAIL_PERMANENT o contador,
  que começa em 0, daria a volta para 255 e a checagem não pegaria nada) e o granizo continua
  depois de 3 turnos (Splash de um Magikarp nível 50 no lugar do 1º do time, para o Pikachu não
  cair);
- `clima/batalha_areia`, `clima/batalha_chuva`, `clima/batalha_cinzas`: Rota 3 com tempestade de
  areia → B_WEATHER_SANDSTORM; Vermilion (COAST) com chuva → B_WEATHER_RAIN; Cinnabar (VOLCANO)
  com cinzas → gBattleWeather == 0.
- `clima/sol_forte` (POK-16): Cinnabar num dia de sol forte à tarde → o jogo não trava (o tempo
  de jogo anda), a paleta do mapa clareia (Faded > Unfaded) e Unfaded não muda depois do menu
  START nem do Centro Pokémon (sem tom dobrado; tela `clima_sol_forte`); num dia de sol forte no
  fim de tarde, às 19:59, a noite chega sem travar e sem sol forte;
- `clima/batalha_sol_forte` (POK-16): Cinnabar com sol forte → B_WEATHER_SUN na batalha.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only clima
"""

import random
import sys

from .. import dia_noite as dn
from ..emu import KEY_A, KEY_B
from ..battle import BattleDriver
from ..field_menu import STARTMENU_BAG
from ..hooks import CMD_SET_VAR, CMD_START_WILD_BATTLE
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

# Task 5: clima na batalha (include/constants/battle.h)
B_WEATHER_RAIN = 0x7                # TEMPORARY | DOWNPOUR | PERMANENT
B_WEATHER_SANDSTORM = 0x18
B_WEATHER_SUN = 0x60                # TEMPORARY | PERMANENT
B_WEATHER_HAIL_TEMPORARY = 1 << 7
B_WEATHER_HAIL_PERMANENT = 1 << 8
B_WEATHER_HAIL = B_WEATHER_HAIL_TEMPORARY | B_WEATHER_HAIL_PERMANENT
WILD_SPECIES, WILD_LEVEL = "SPECIES_PIKACHU", 5
LEAD_SPECIES, LEAD_LEVEL = "SPECIES_MAGIKARP", 50   # 1º golpe Splash, mais rápido: o turno não derruba ninguém
HAIL_TURNS = 3
HAIL_DURATION = 1                   # weatherDuration escrito depois da abertura: acaba no 1º turno
WISH_WEATHER_DURATION = 0x28        # gWishFutureKnock.weatherDuration (struct WishFutureKnock, include/battle.h)
HAIL_TEXT = "Começou a cair granizo!"     # sText_StartedHail (src/battle_message.c)
BATTLE_CASES = (   # (fluxo, mapa, ponto, região, período, clima do campo, (máscara, esperado) na batalha)
    ("areia", "MAP_ROUTE3", ROUTE3_SPOT, dn.REGION_SAND, dn.AFTERNOON, dn.WEATHER_SANDSTORM,
     (B_WEATHER_SANDSTORM, B_WEATHER_SANDSTORM)),
    ("chuva", "MAP_VERMILION_CITY", (12, 18), dn.REGION_COAST, dn.MORNING, dn.WEATHER_RAIN,
     (B_WEATHER_RAIN, 0x5)),        # TEMPORARY | PERMANENT
    ("cinzas", "MAP_CINNABAR_ISLAND", (19, 12), dn.REGION_VOLCANO, dn.MORNING, dn.WEATHER_VOLCANIC_ASH,
     (0xFFFF, 0)),
    ("sol_forte", "MAP_CINNABAR_ISLAND", (19, 12), dn.REGION_VOLCANO, dn.AFTERNOON, dn.WEATHER_DROUGHT,
     (B_WEATHER_SUN, B_WEATHER_SUN)),
)
# POK-16: sol forte no mapa (Cinnabar, região vulcão)
CINNABAR_SPOT = (19, 12)            # em frente à porta da loja (19, 11)
CINNABAR_CENTER = "MAP_CINNABAR_ISLAND_POKEMON_CENTER_1F"
MAP_BG_COLORS = range(16 * 2, 16 * 13)   # paletas de BG do mapa (2-12)
SB2_PLAYTIME_SECONDS = 0x11         # playTimeSeconds, playTimeVBlanks em 0x12 (include/global.h)
PERIOD_MINUTE = {dn.MORNING: 6 * 60, dn.AFTERNOON: 12 * 60, dn.EVENING: 18 * 60, dn.NIGHT: 22 * 60}


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

    # --- POK-16: sol forte no mapa -------------------------------------------------------
    def _playtime_frames(self) -> int:
        sb2 = self.game._sb2()
        return self.emu.read_u8(sb2 + SB2_PLAYTIME_SECONDS) * 60 + self.emu.read_u8(sb2 + SB2_PLAYTIME_SECONDS + 1)

    def _map_bg(self, buffer: str) -> list[int]:
        base = self.game.syms.addr(buffer)
        return [self.emu.read_u16(base + c * 2) for c in MAP_BG_COLORS]

    def _drought(self) -> str:
        day = self._weather_day(dn.REGION_VOLCANO, dn.AFTERNOON, dn.WEATHER_DROUGHT)
        self.box.set_clock(day, PERIOD_MINUTE[dn.AFTERNOON])
        self._warp_to("MAP_CINNABAR_ISLAND", CINNABAR_SPOT)
        steps = [self._expect_weather(dn.WEATHER_DROUGHT, f"Cinnabar, dia {day} tarde")]
        before = self._playtime_frames()
        self.emu.frames(120)
        ran = (self._playtime_frames() - before) % 3600
        assert ran >= 100, f"o jogo travou com o sol forte: o tempo de jogo andou {ran} em 120 quadros"
        lum = lambda c: (c & 31) + (c >> 5 & 31) + (c >> 10 & 31)
        unfaded = self._map_bg("gPlttBufferUnfaded")
        brighter = sum(lum(f) > lum(u) for u, f in zip(unfaded, self._map_bg("gPlttBufferFaded")))
        assert brighter > len(unfaded) // 2, f"só {brighter} de {len(unfaded)} cores clarearam"
        self._shot("clima_sol_forte")
        steps.append(f"tempo de jogo andou {ran}/120; {brighter}/{len(unfaded)} cores mais claras")
        self.menu.open_start_menu()
        self.menu.close_start_menu()
        self._settle("menu START com sol forte")
        assert self._map_bg("gPlttBufferUnfaded") == unfaded, "Unfaded mudou depois do menu START (tom dobrado)"
        self._warp_to(CINNABAR_CENTER, CENTER_SPOT)
        self._walk(*CENTER_EXIT)
        self._warp("down", "MAP_CINNABAR_ISLAND")
        self._settle("saída do Centro Pokémon de Cinnabar")
        steps.append(self._expect_weather(dn.WEATHER_DROUGHT, "saída do Centro Pokémon"))
        assert self._map_bg("gPlttBufferUnfaded") == unfaded, "Unfaded mudou depois do Centro Pokémon (tom dobrado)"
        steps.append("Unfaded igual depois do menu START e do Centro Pokémon")
        return "; ".join(steps)

    def _drought_to_night(self) -> str:
        day = self._weather_day(dn.REGION_VOLCANO, dn.EVENING, dn.WEATHER_DROUGHT)
        night = dn.roll_weather(dn.REGION_VOLCANO, day, dn.NIGHT)
        self.box.set_clock(day, 19 * 60 + 50)
        self._warp_to("MAP_CINNABAR_ISLAND", CINNABAR_SPOT)
        before = self._expect_weather(dn.WEATHER_DROUGHT, f"Cinnabar, dia {day} 19:50")
        self.box.set_clock(day, 19 * 60 + 59)
        spent = self._wait_weather(night, "19:59")
        return f"{before} → noite: {_name(night)} ({spent} quadros depois de 19:59)"

    def _cave(self) -> str:
        map_name, spot = CAVE
        day, minute, rolled = self._rolled_inland_days(1)[0]
        self.box.set_clock(day, minute)
        self._warp_to(map_name, spot)
        return self._expect_weather(
            dn.WEATHER_NONE, f"{map_name} dia {day} {self._hhmm(minute)} (sorteio {_name(rolled)})")

    # --- Task 5: clima na batalha -----------------------------------------------------
    def _battle_weather(self) -> int:
        return self.emu.read_u16(self.game.syms.addr("gBattleWeather"))

    def _battle_text(self) -> str:
        raw = self.emu.read(self.game.syms.addr("gDisplayedStringBattle"), 64)
        return self.game.charmap.decode(raw.split(b"\xff")[0])

    @staticmethod
    def _weather_day(region: int, period: int, weather: int) -> int:
        return _first_day(lambda d: dn.roll_weather(region, d, period) == weather)

    def _start_wild_battle(self) -> BattleDriver:
        result = self.box.call(CMD_START_WILD_BATTLE, self.consts.species(WILD_SPECIES), WILD_LEVEL)
        assert result == 1, f"START_WILD_BATTLE devolveu {result:#x}"
        driver = BattleDriver(self.ctl)
        driver.wait_battle_start()
        return driver

    def _leave_battle(self, driver: BattleDriver, where: str) -> None:
        assert driver.run_away(), f"{where}: não conseguiu fugir"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, f"volta ao campo: {where}")
        self._settle(f"volta da batalha: {where}")

    def _battle_hail(self) -> str:
        self.box.set_party_mon(0, self.consts.species(LEAD_SPECIES), LEAD_LEVEL)
        day = self._weather_day(dn.REGION_SNOW, dn.MORNING, dn.WEATHER_SNOW)
        self.box.set_clock(day, PERIOD_MINUTE[dn.MORNING])
        self._warp_to("MAP_FOUR_ISLAND", FOUR_ISLAND_SPOT)
        steps = [self._expect_weather(dn.WEATHER_SNOW, f"Four Island, dia {day}")]
        driver = self._start_wild_battle()
        spent = 0
        while HAIL_TEXT not in self._battle_text():
            assert spent < 1200, (f"sem \"{HAIL_TEXT}\" na abertura: gBattleWeather = "
                                  f"{self._battle_weather():#x}, texto \"{self._battle_text()}\"")
            self.emu.press(KEY_A, hold=2, release=2)   # "Um Pikachu selvagem apareceu!" etc.
            spent += 4
        self.emu.frames(4)
        self._shot("batalha_granizo")
        driver.wait_action_menu()
        weather = self._battle_weather()
        assert weather & B_WEATHER_HAIL == B_WEATHER_HAIL, (
            f"depois da abertura gBattleWeather = {weather:#x}, esperava granizo permanente")
        steps.append(f"\"{HAIL_TEXT}\"; abertura: gBattleWeather = {weather:#x}")
        duration = self.game.syms.addr("gWishFutureKnock") + WISH_WEATHER_DURATION
        self.emu.write(duration, bytes([HAIL_DURATION]))
        for turn in range(1, HAIL_TURNS + 1):
            assert driver.fight_turn() == "menu", f"a batalha acabou no turno {turn}"
            weather = self._battle_weather()
            assert weather & B_WEATHER_HAIL == B_WEATHER_HAIL, (
                f"turno {turn}: gBattleWeather = {weather:#x}, o granizo acabou")
        steps.append(f"weatherDuration = {HAIL_DURATION} e {HAIL_TURNS} turnos depois: {weather:#x} "
                     f"(contador em {self.emu.read_u8(duration)})")
        self._leave_battle(driver, "granizo")
        return "; ".join(steps)

    def _battle_case(self, map_name: str, spot: tuple[int, int], region: int, period: int,
                     field_weather: int, expected: tuple[int, int]) -> str:
        mask, want = expected
        day = self._weather_day(region, period, field_weather)
        self.box.set_clock(day, PERIOD_MINUTE[period])
        self._warp_to(map_name, spot)
        field = self._expect_weather(field_weather, f"{map_name}, dia {day} {dn.PERIOD_NAMES[period]}")
        driver = self._start_wild_battle()
        driver.wait_action_menu()
        weather = self._battle_weather()
        assert weather & mask == want, f"{map_name}: gBattleWeather = {weather:#x}, esperava {want:#x}"
        self._leave_battle(driver, map_name)
        return f"{field} → gBattleWeather = {weather:#x}"

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
            self._flow("clima/sol_forte: Cinnabar com sol forte sem travar nem dobrar o tom",
                       self._drought)
            self._flow("clima/sol_forte_noite: o sol forte do fim de tarde sai na virada da noite",
                       self._drought_to_night)
            self._flow("clima/batalha_granizo: neve do mapa vira granizo permanente na batalha",
                       self._battle_hail)
            for name, *case in BATTLE_CASES:
                self._flow(f"clima/batalha_{name}: clima do mapa na batalha",
                           lambda case=case: self._battle_case(*case))
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
