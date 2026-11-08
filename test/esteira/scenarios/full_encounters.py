"""Modo completo: encontros de grama e caverna por horário (Hack 7, HeartGold), build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`):

1. `encontros/hook`: para os 37 mapas x manhã/tarde/noite x 12 slots, o atalho LAND_SPECIES
   (0x74) devolve a espécie de src/data/wild_encounters_time.json;
2. `encontros/entardecer`: num slot da Rota 1 em que tarde e noite diferem, 4000 chamadas no
   ENTARDECER dão só essas duas espécies, na proporção de 0,5 (a ±4 desvios-padrão);
3. `encontros/rota1_noite`: relógio às 22:00, na grama da Rota 1 foge de selvagens até sair um
   Hoothoot (só a tabela da noite tem; no máximo 16), todos da noite da Rota 1 e nenhum Pidgey
   (só o FRLG/dia tem); relógio às 07:00, um selvagem: da manhã e não Hoothoot;
4. `encontros/sem_tabela`: na Rota 12 (sem tabela) o atalho devolve a espécie FRLG do slot nos
   4 períodos;
5. `encontros/area_pokedex`: SPECIES_ON_MAP (0x7B): Hoothoot na Rota 1 com o relógio de dia =
   TRUE (a tabela da noite conta para a área da Pokédex), Pidgey continua TRUE, um Pokémon que
   não está lá = FALSE.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only encontros
"""

import math
import sys

from .. import dia_noite as dn
from .. import encontros as en
from ..hooks import CMD_LAND_SPECIES, CMD_SPECIES_ON_MAP, CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CATCH_GRASS, CatchSaveScenario

EVENING_SAMPLES = 4000
DAY = 1                      # dia do jogo dos relógios acertados (qualquer um serve)
NIGHT_MINUTE, MORNING_MINUTE, NOON_MINUTE = 22 * 60, 7 * 60, 12 * 60
HOOK_PERIODS = ((dn.MORNING, "morning"), (dn.AFTERNOON, "day"), (dn.NIGHT, "night"))
WARP_TIMEOUT = 600
# encontros/rota1_noite: só a tabela da noite tem Hoothoot (45% dos encontros: slots 0, 2, 6, 7,
# 9 e 11) e só o FRLG/dia tem Pidgey. Sem a tabela da noite nunca sai Hoothoot (falha sempre);
# com ela, 16 selvagens sem nenhum têm chance 0,55^16 ≈ 0,007%.
NIGHT_ONLY, DAY_ONLY = "SPECIES_HOOTHOOT", "SPECIES_PIDGEY"
NIGHT_ONLY_CHANCE = 45
NIGHT_MAX_WILD = 16


class EncountersScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.tables = en.load_time_tables(REPO_ROOT)
        self.frlg = en.load_frlg_land(REPO_ROOT)
        self.route1 = next(t for t in self.tables if t["map"] == "MAP_ROUTE1")

    # --- utilidades ----------------------------------------------------------------
    def _land_species(self, map_name: str, slot: int, period: int) -> int:
        group, num = self.consts.map(map_name)
        return self.box.call(CMD_LAND_SPECIES, group << 8 | num, slot | period << 8)

    def _name(self, species_id: int) -> str:
        if species_id >= 0xFFFF:
            return f"0x{species_id:X}"
        return self.consts.species_name(species_id)

    def _warp_to_grass(self) -> None:
        group, num = self.consts.map("MAP_ROUTE1")
        x, y = CATCH_GRASS[0]
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), WARP_TIMEOUT,
                            "warp para a grama da Rota 1")
        self.ctl.wait_overworld_idle(WARP_TIMEOUT)
        self._expect_map("MAP_ROUTE1")

    def _wild_species_at(self, minute: int) -> tuple[int, int]:
        """Relógio em `minute`, vai à grama da Rota 1, espera um selvagem, lê a espécie e foge."""
        self.box.set_clock(DAY, minute)
        self._warp_to_grass()
        self._find_wild_battle(CATCH_GRASS)
        self.driver.wait_action_menu()
        species, level = self.driver.battler_species_level(1)
        self._end_battle("fuga do selvagem da Rota 1")
        return species, level

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="encontros_continue")
        minute, period = self.box.clock_info()
        return f"CONTINUAR com o save do modo rápido: relógio em {minute // 60:02d}:{minute % 60:02d}"

    def _hook(self) -> str:
        checked = 0
        for table in self.tables:
            for period, key in HOOK_PERIODS:
                for slot, name in enumerate(table[key]):
                    want = self.consts.species(name)
                    got = self._land_species(table["map"], slot, period)
                    assert got == want, (f"{table['map']} {key} slot {slot}: o jogo devolveu "
                                         f"{self._name(got)}, o JSON diz {name}")
                    checked += 1
        assert checked == len(self.tables) * 3 * en.LAND_SLOTS
        return f"{len(self.tables)} mapas x 3 períodos x {en.LAND_SLOTS} slots = {checked} espécies conferidas"

    def _entardecer(self) -> str:
        slot = next((i for i in range(en.LAND_SLOTS)
                     if self.route1["day"][i] != self.route1["night"][i]), None)
        assert slot is not None, "Rota 1: tarde e noite iguais em todos os slots"
        day, night = self.route1["day"][slot], self.route1["night"][slot]
        ids = {self.consts.species(day): day, self.consts.species(night): night}
        counts = {day: 0, night: 0}
        for _ in range(EVENING_SAMPLES):
            got = ids.get(self._land_species("MAP_ROUTE1", slot, dn.EVENING))
            assert got in counts, f"espécie fora de {{{day}, {night}}} no entardecer"
            counts[got] += 1
        sigma = math.sqrt(EVENING_SAMPLES * 0.25)
        diff = abs(counts[night] - EVENING_SAMPLES / 2)
        assert diff <= 4 * sigma, (f"{night}: {counts[night]}/{EVENING_SAMPLES}, "
                                   f"desvio {diff:.0f} > 4σ = {4 * sigma:.0f}")
        return (f"slot {slot}: {day} {counts[day]} x {night} {counts[night]} em {EVENING_SAMPLES} "
                f"(desvio {diff:.0f}, 4σ = {4 * sigma:.0f})")

    def _rota1_noite(self) -> str:
        night = set(self.route1["night"])
        frlg = {mon["species"] for mon in self.frlg["MAP_ROUTE1"]}
        assert NIGHT_ONLY in night - frlg and DAY_ONLY in frlg - night, (night, frlg)
        self.box.set_clock(DAY, NIGHT_MINUTE)
        self._warp_to_grass()
        seen = []
        while NIGHT_ONLY not in seen:
            assert len(seen) < NIGHT_MAX_WILD, (
                f"22:00: nenhum {NIGHT_ONLY} em {len(seen)} selvagens ({', '.join(seen)}); a noite "
                f"da Rota 1 dá {NIGHT_ONLY} em {NIGHT_ONLY_CHANCE}% dos encontros")
            self._find_wild_battle(CATCH_GRASS)
            self.driver.wait_action_menu()
            species, level = self.driver.battler_species_level(1)
            name = self._name(species)
            self._end_battle("fuga do selvagem da Rota 1 à noite")
            seen.append(name)
            assert name in night and name != DAY_ONLY, (
                f"22:00, selvagem {len(seen)}: {name} nv{level}, esperava um de {sorted(night)}")
        morning_id, morning_level = self._wild_species_at(MORNING_MINUTE)
        morning_name = self._name(morning_id)
        assert morning_name in self.route1["morning"] and morning_name != NIGHT_ONLY, (
            f"07:00: {morning_name}, esperava um de {sorted(set(self.route1['morning']))}")
        return (f"22:00: {', '.join(seen)} (o {len(seen)}º foi o 1º {NIGHT_ONLY}, nenhum "
                f"{DAY_ONLY}); 07:00 {morning_name} nv{morning_level} (manhã)")

    def _sem_tabela(self) -> str:
        slots = self.frlg[en.NO_TABLE_MAP]
        for period in range(dn.NIGHT + 1):
            for slot, mon in enumerate(slots):
                want = self.consts.species(mon["species"])
                got = self._land_species(en.NO_TABLE_MAP, slot, period)
                assert got == want, (f"{en.NO_TABLE_MAP} {dn.PERIOD_NAMES[period]} slot {slot}: "
                                     f"{self._name(got)}, esperava {mon['species']} (FRLG)")
        return f"{en.NO_TABLE_MAP}: {en.LAND_SLOTS} slots x 4 períodos = espécie do FRLG"

    def _area_pokedex(self) -> str:
        self.box.set_clock(DAY, NOON_MINUTE)
        group, num = self.consts.map("MAP_ROUTE1")

        def on_map(name: str) -> int:
            return self.box.call(CMD_SPECIES_ON_MAP, group << 8 | num, self.consts.species(name))

        hoothoot, pidgey, mew = (on_map(n) for n in ("SPECIES_HOOTHOOT", "SPECIES_PIDGEY",
                                                      "SPECIES_MEW"))
        assert hoothoot == 1, f"Hoothoot na Rota 1 ao meio-dia: {hoothoot}, esperava 1"
        assert pidgey == 1, f"Pidgey na Rota 1: {pidgey}, esperava 1"
        assert mew == 0, f"Mew na Rota 1: {mew}, esperava 0"
        return "Rota 1 ao meio-dia: Hoothoot e Pidgey na área, Mew não"

    def run(self) -> None:
        try:
            self._flow("encontros: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("encontros/hook: o jogo devolve as espécies do JSON", self._hook)
            self.suite.run("encontros/entardecer: tarde ou noite meio a meio", self._entardecer)
            self.suite.run("encontros/rota1_noite: selvagem da Rota 1 muda com o horário",
                           self._rota1_noite)
            self.suite.run("encontros/sem_tabela: Rota 12 segue a tabela do FRLG",
                           self._sem_tabela)
            self.suite.run("encontros/area_pokedex: a tabela da noite conta na área",
                           self._area_pokedex)
        except Abort:
            pass


def run_full_encounters(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    EncountersScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only encontros ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "encontros", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
