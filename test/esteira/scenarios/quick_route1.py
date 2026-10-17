"""Roteiro rápido B: cronômetro de passos, Rota 1 (vitória e fuga) e a encomenda do Oak.

Só aperta botões e lê memória. Começa do checkpoint `rival` (Task 5: no laboratório, depois
da batalha do rival). Checkpoints: `rota1` (na grama da Rota 1, depois da vitória e da fuga)
e `encomenda` (no laboratório, com a Pokédex e as Poké Balls). O Task 7 continua de
`encomenda`.

Encontros selvagens fora dos testes de batalha são fugidos; se o HP do inicial cair da
metade, a Mamãe cura em casa (o roteiro nunca luta com o inicial fraco).

Uso avulso (até o CLI do Task 8 existir), a partir de test/:
    python3 -m esteira.scenarios.quick_route1 --starter BULBASAUR --out out/rota1
Se OUT/estados/rival.ss existir (gerado por quick_opening na mesma pasta), começa dele;
senão roda a abertura antes.
"""

import argparse
import sys
import time

from ..battle import OUTCOME_NAMES, BattleDriver
from ..emu import KEY_A, KEY_UP
from ..healthbox import HealthboxReader
from ..result import Result
from ..rotation import STARTERS
from . import REPO_ROOT, ScenarioContext, open_context
from .base import Abort, Scenario, print_summary
from .pace import WALK_FRAMES_PER_TILE, measure_frames_per_tile
from .quick_opening import run_opening

# Coordenadas tiradas de data/maps/*/map.json e dos layouts (grades conferidas com nav.py).
LAB_EXIT = (6, 11)                  # laboratório: warps em (5..7, 12), sai com "down"
PACE_START = (15, 9)                # Pallet: linha 9 livre de x=2 a x=21
PALLET_NORTH_APPROACH = (13, 3)     # coluna 13: a moça da placa fica parada em (12, 2)
PALLET_NORTH_EDGE = (13, 0)         # conexão "up" para a Rota 1 (offset 0)
PALLET_HOUSE_FRONT = (6, 8)         # porta de casa em (6, 7)
PALLET_LAB_FRONT = (16, 14)         # porta do laboratório em (16, 13)
HOUSE_MOM_FRONT = (8, 5)            # Mamãe em (8, 4)
HOUSE_EXIT = (4, 8)                 # tapete da saída (como no Task 5)
ROUTE1_SOUTH_EDGE = (13, 39)        # conexão "down" para Pallet
ROUTE1_NORTH_EDGE = (13, 0)         # conexão "up" para Viridian (offset -12 -> x=25)
ROUTE1_GRASS = ((13, 36), (13, 38))  # grama alta da entrada: vai e volta entre as duas
VIRIDIAN_SOUTH_EDGE = (25, 39)
VIRIDIAN_MART_FRONT = (36, 20)      # porta do Mart em (36, 19)
MART_EXIT = (4, 6)                  # warps em (3..5, 7), sai com "down"
OAK_FRONT = (6, 4)                  # Oak em (6, 3), olhando para baixo

MAX_INTERRUPTIONS = 20      # encontros/falas tolerados num mesmo trajeto
MAX_ENCOUNTER_WALKS = 200   # idas e voltas na grama procurando um selvagem
MAX_WIN_BATTLES = 8         # batalhas até receber ao menos um golpe (nenhum nas 8: falha)
MAX_FLEE_BATTLES = 3
MAX_RUN_TRIES = 5
HEAL_BELOW = 0.5            # fração do HP máximo abaixo da qual a Mamãe cura
INTERRUPTION_TIMEOUT = 900
POST_BATTLE_TIMEOUT = 900
WARP_TIMEOUT = 600
DEX_SCENE_TIMEOUT = 20000


class _HpWatch:
    """Confere o HP mostrado no healthbox toda vez que o HP do inicial cai (golpe recebido).

    O HP do time só muda no `datahpupdate`, que roda depois que a barra terminou de andar:
    nessa hora o número na tela tem que ser o valor final.
    """

    def __init__(self, scenario: "Route1Scenario"):
        self.sc = scenario
        self.last = scenario.game.party()[0].hp
        self.hits: list[tuple[int, int, int | None]] = []   # (antes, depois, mostrado)

    def __call__(self) -> None:
        hp = self.sc.game.party()[0].hp
        if hp < self.last:
            self.hits.append((self.last, hp, self.sc.reader.player_hp()))
            if "hit_shot" not in self.sc.measures:
                self.sc.measures["hit_shot"] = self.sc._shot("rota1_golpe")
        self.last = hp


class Route1Scenario(Scenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.driver = BattleDriver(self.ctl)
        self.reader = HealthboxReader(self.emu, self.game.syms)
        self.measures.update(encounters_on_the_way=0, heals=0, hp_starts=[], hits=[])

    # --- utilidades ----------------------------------------------------------------
    def _map(self, name: str) -> tuple[int, int]:
        return self.consts.map(name)

    def _expect_map(self, name: str) -> None:
        loc = self.game.location()
        if loc != self._map(name):
            raise AssertionError(f"estou em {loc} {self.game.player_xy()}, esperava {name}")

    def _warp(self, direction: str | None, dest: str) -> None:
        self.nav.go_through_warp(direction)
        self._expect_map(dest)

    def _species(self, species_id: int) -> str:
        return self.consts.species_name(species_id).removeprefix("SPECIES_")

    def _talk(self, face_key: int, what: str, timeout: int = 6000) -> None:
        """Vira para o NPC da frente, aperta A e avança as falas até o overworld ficar livre."""
        self.emu.hold(face_key, 4)
        self.ctl.wait_until(self.nav._player_still, 60, f"jogador parado antes de: {what}")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, f"início de: {what}")
        self._finish_script(what, timeout)

    # --- trajetos resistentes a encontros ------------------------------------------
    def _walk(self, x: int, y: int) -> None:
        """walk_to no mapa atual; encontro no caminho é fugido e fala é avançada."""
        for _ in range(MAX_INTERRUPTIONS):
            if self.nav.walk_to(x, y):
                return
            self._resolve_interruption()
        raise self.ctl.timeout_error(f"caminho até {(x, y)} em {self.game.location()} "
                                     f"interrompido {MAX_INTERRUPTIONS} vezes")

    def _cross(self, direction: str, dest: str) -> None:
        """Atravessa a conexão de mapa logo à frente (o jogador já está na borda)."""
        start = self.game.location()
        for _ in range(MAX_INTERRUPTIONS):
            self.nav.step(direction, 1)
            crossed = self.game.location() != start
            if self.nav.interrupted is not None:
                self._resolve_interruption()
            if crossed:
                self._expect_map(dest)
                return
        raise self.ctl.timeout_error(f"travessia {direction} a partir de {start}")

    def _wait_battle_or_text(self) -> None:
        """Depois de um passo interrompido: espera a batalha começar ou a fala aparecer."""
        self.ctl.wait_until(lambda: self.game.in_battle() or self.game.text_printer_active()
                            or self.ctl.overworld_idle(),
                            INTERRUPTION_TIMEOUT, "batalha ou fala depois do passo interrompido")

    def _resolve_interruption(self) -> None:
        self._wait_battle_or_text()
        if self.game.in_battle():
            self._escape_battle()
        elif not self.ctl.overworld_idle():
            self._finish_script("fala no caminho")

    def _after_battle(self, what: str) -> None:
        """Confere que o inicial não desmaiou e espera o overworld voltar."""
        if OUTCOME_NAMES.get(self.driver.outcome()) == "lose":
            shot = self._shot("desmaio")
            raise AssertionError(f"{what}: o inicial desmaiou (tela: {shot})")
        self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)

    def _escape_battle(self) -> None:
        """Encontro no caminho: foge; não conseguindo em MAX_RUN_TRIES, luta até o fim."""
        fled = False
        for _ in range(MAX_RUN_TRIES):
            fled = self.driver.run_away()
            if fled or not self.game.in_battle():
                break
        if not fled and self.game.in_battle():
            self.driver.fight_to_end()
        self._after_battle("encontro no caminho")
        self.measures["encounters_on_the_way"] += 1

    # --- cura e idas e vindas ------------------------------------------------------
    def _heal_at_mom(self) -> None:
        if self.game.location() == self._map("MAP_ROUTE1"):
            self._walk(*ROUTE1_SOUTH_EDGE)
            self._cross("down", "MAP_PALLET_TOWN")
        self._expect_map("MAP_PALLET_TOWN")
        self._walk(*PALLET_HOUSE_FRONT)
        self._warp(None, "MAP_PALLET_TOWN_PLAYERS_HOUSE_1F")
        self._walk(*HOUSE_MOM_FRONT)
        self._talk(KEY_UP, "Mamãe cura o time")
        mon = self.game.party()[0]
        assert mon.hp == mon.max_hp, f"Mamãe não curou: HP {mon.hp}/{mon.max_hp}"
        self._walk(*HOUSE_EXIT)
        self._warp(None, "MAP_PALLET_TOWN")
        self.measures["heals"] += 1

    def _heal_if_below(self, fraction: float) -> None:
        mon = self.game.party()[0]
        if mon.hp < mon.max_hp * fraction:
            self._heal_at_mom()

    def _go_to_route1(self) -> None:
        if self.game.location() == self._map("MAP_PALLET_TOWN"):
            self._walk(*PALLET_NORTH_APPROACH)
            self._walk(*PALLET_NORTH_EDGE)
            self._cross("up", "MAP_ROUTE1")
        self._expect_map("MAP_ROUTE1")

    def _go_to_grass(self) -> None:
        self._go_to_route1()
        if self.game.player_xy() not in ROUTE1_GRASS:
            self._walk(*ROUTE1_GRASS[1])

    def _find_wild_battle(self, grass=ROUTE1_GRASS) -> None:
        """Vai e volta entre os dois tiles de grama `grass` (mesma coluna, o de cima primeiro;
        padrão: entrada da Rota 1) até um selvagem aparecer."""
        top, bottom = grass
        for _ in range(MAX_ENCOUNTER_WALKS):
            target = top if self.game.player_xy()[1] > top[1] else bottom
            if self.nav.walk_to(*target):
                continue
            self._wait_battle_or_text()
            if self.game.in_battle():
                return
            if not self.ctl.overworld_idle():
                self._finish_script("fala na grama")
        raise AssertionError(f"nenhum selvagem em {MAX_ENCOUNTER_WALKS} idas e voltas na grama")

    # --- cronômetro de passos ------------------------------------------------------
    def _leave_lab(self) -> None:
        self._walk(*LAB_EXIT)
        self._warp("down", "MAP_PALLET_TOWN")
        self._walk(*PACE_START)

    def phase_pace(self) -> None:
        """Andar por input a 11 quadros/tile. Correr (5) não é medido aqui: o tênis só vem
        em Pewter e o modo completo (Task 11) mede com measure_run_frames_per_tile()."""
        self._flow("rota1: saída do laboratório", self._leave_lab)

        def check_walk() -> str:
            steps = measure_frames_per_tile(self.ctx, "left")
            assert steps and all(d == WALK_FRAMES_PER_TILE for d in steps), (
                f"andando: {steps} quadros/tile, esperava {WALK_FRAMES_PER_TILE}")
            return f"{len(steps)} passos andando: {steps} quadros/tile"

        self.suite.run(f"rota1: andar por input a {WALK_FRAMES_PER_TILE} quadros/tile",
                       check_walk)
        if self.game.flag(self.consts.flag("FLAG_SYS_B_DASH")):
            return

        def check_b_without_shoes() -> str:
            steps = measure_frames_per_tile(self.ctx, "right", run=True)
            assert steps and all(d == WALK_FRAMES_PER_TILE for d in steps), (
                f"sem o tênis, B segurado: {steps} quadros/tile, esperava {WALK_FRAMES_PER_TILE}")
            return f"{len(steps)} passos com B segurado: {steps} quadros/tile"

        self.suite.run("rota1: sem o tênis de corrida, B segurado anda a "
                       f"{WALK_FRAMES_PER_TILE} quadros/tile", check_b_without_shoes)

    # --- Rota 1: vitória com HP conferido e fuga -----------------------------------
    def _fight_watching_hp(self) -> str:
        self.driver.wait_action_menu()
        species, level = self.driver.battler_species_level(1)
        party_hp = self.game.party()[0].hp
        self.measures["hp_starts"].append((party_hp, self.reader.player_hp()))
        watch = _HpWatch(self)
        outcome = self.driver.fight_to_end(on_step=watch)
        wild_hp = self.driver.battler_hp(1)
        self.measures["hits"].extend(watch.hits)
        self._after_battle("batalha selvagem")
        wild = f"{self._species(species)} nv{level}"
        assert outcome == "win", f"batalha contra {wild} terminou em {outcome!r}"
        assert wild_hp == 0, f"{wild} venceu-se com HP {wild_hp} na memória, esperava 0"
        return f"{wild} (HP final 0, {len(watch.hits)} golpe(s) recebido(s))"

    def _win_battles(self) -> str:
        battles = []
        for _ in range(MAX_WIN_BATTLES):
            self._heal_if_below(HEAL_BELOW)
            self._go_to_grass()
            self._find_wild_battle()
            battles.append(self._fight_watching_hp())
            if self.measures["hits"]:
                break
        return "; ".join(battles)

    def _check_displayed_hp(self) -> Result:
        name = "rota1: HP exibido termina no valor final a cada golpe recebido"
        starts, hits = self.measures["hp_starts"], self.measures["hits"]
        images = [self.measures["hit_shot"]] if "hit_shot" in self.measures else []
        wrong_start = [(hp, shown) for hp, shown in starts if hp != shown]
        wrong_hits = [(a, b, shown) for a, b, shown in hits if b != shown]
        detail = (f"início das batalhas (HP, mostrado): {starts}; golpes "
                  f"(antes, depois, mostrado): {hits}")
        if wrong_start or wrong_hits:
            return Result(name, "falha", f"healthbox diverge do HP do time — {detail}", images)
        if not hits:   # sem golpe recebido a barra não foi conferida: não pode passar como ok
            return Result(name, "falha", f"nenhum golpe recebido em {len(starts)} batalha(s); "
                                         f"a barra não pôde ser conferida — {detail}", images)
        return Result(name, "ok", detail, images)

    def _flee(self) -> str:
        for _ in range(MAX_FLEE_BATTLES):
            self._heal_if_below(HEAL_BELOW)
            self._go_to_grass()
            self._find_wild_battle()
            where = (self.game.location(), self.game.player_xy())
            species, level = self.driver.battler_species_level(1)
            for attempt in range(1, MAX_RUN_TRIES + 1):
                if self.driver.run_away():
                    self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)
                    now = (self.game.location(), self.game.player_xy())
                    assert not self.game.in_battle()
                    assert now == where, f"fugiu e voltou em {now}, esperava {where}"
                    return (f"fugiu de {self._species(species)} nv{level} na {attempt}ª "
                            f"tentativa; overworld em {now[1]} (mapa {now[0]})")
                if not self.game.in_battle():
                    break
            if self.game.in_battle():       # não deu para fugir: encerra lutando e tenta outro
                self.driver.fight_to_end()
            self._after_battle("batalha em que a fuga falhou")
        raise AssertionError(f"não conseguiu fugir em {MAX_FLEE_BATTLES} encontros")

    def phase_route1(self) -> None:
        self._flow("rota1: caminho até a grama da Rota 1", self._go_to_grass)
        self._flow("rota1: batalha selvagem até vencer (HP do selvagem termina em 0)",
                   self._win_battles)
        self.suite.add(self._check_displayed_hp())
        self._flow("rota1: fuga volta ao overworld no mesmo tile", self._flee)
        self.ctl.checkpoint("rota1")

    # --- encomenda do Oak ----------------------------------------------------------
    def _go_to_mart(self) -> None:
        self._heal_if_below(1.0)        # viagem longa: sai com o HP cheio (Mamãe é perto)
        self._go_to_route1()
        self._walk(*ROUTE1_NORTH_EDGE)
        self._cross("up", "MAP_VIRIDIAN_CITY")
        self._walk(*VIRIDIAN_MART_FRONT)

    def _get_parcel(self) -> str:
        """Entra no Mart: a cena do balconista (ON_FRAME) começa sozinha e entrega a encomenda."""
        start = self.game.location()
        self.ctl.wait_overworld_idle()
        self.emu.keys(KEY_UP)
        try:
            self.ctl.wait_until(lambda: self.game.location() != start, WARP_TIMEOUT,
                                "entrada no Viridian Mart")
        finally:
            self.emu.keys(0)
        self._expect_map("MAP_VIRIDIAN_CITY_MART")
        self.ctl.wait_until(self.ctl.script_active, WARP_TIMEOUT, "cena do balconista")
        self._finish_script("cena da encomenda no Mart")
        qty = self.game.bag_quantity(self.consts.item("ITEM_OAKS_PARCEL"))
        assert qty == 1, f"ITEM_OAKS_PARCEL na bolsa = {qty}, esperava 1"
        return f"ITEM_OAKS_PARCEL x{qty} na bolsa; jogador em {self.game.player_xy()}"

    def _back_to_lab(self) -> None:
        self._walk(*MART_EXIT)
        self._warp("down", "MAP_VIRIDIAN_CITY")
        self._walk(*VIRIDIAN_SOUTH_EDGE)
        self._cross("down", "MAP_ROUTE1")
        self._walk(*ROUTE1_SOUTH_EDGE)
        self._cross("down", "MAP_PALLET_TOWN")
        self._walk(*PALLET_LAB_FRONT)
        self._warp(None, "MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB")

    def _deliver_parcel(self) -> str:
        consts, game = self.consts, self.game
        ball = consts.item("ITEM_POKE_BALL")
        assert not game.flag(consts.flag("FLAG_SYS_POKEDEX_GET")), "Pokédex já recebida antes"
        assert game.bag_quantity(ball) == 0, "já havia Poké Balls antes da entrega"
        self._walk(*OAK_FRONT)
        self._talk(KEY_UP, "cena da Pokédex", DEX_SCENE_TIMEOUT)
        dex = game.flag(consts.flag("FLAG_SYS_POKEDEX_GET"))
        balls = game.bag_quantity(ball)
        parcel = game.bag_quantity(consts.item("ITEM_OAKS_PARCEL"))
        assert dex, "FLAG_SYS_POKEDEX_GET desligada depois de falar com o Oak"
        assert parcel == 0, f"a encomenda continua na bolsa (x{parcel})"
        assert balls >= 1, f"bag_quantity(ITEM_POKE_BALL) = {balls}, esperava >= 1"
        return (f"Pokédex recebida (FLAG_SYS_POKEDEX_GET), {balls} Poké Balls, encomenda "
                f"entregue; no roteiro: {self.measures['encounters_on_the_way']} encontro(s) no "
                f"caminho, {self.measures['heals']} cura(s) com a Mamãe")

    def phase_parcel(self) -> None:
        self._flow("encomenda: caminho até o Viridian Mart", self._go_to_mart)
        self._flow("encomenda: Viridian Mart entrega a encomenda do Oak", self._get_parcel)
        self._flow("encomenda: volta ao laboratório", self._back_to_lab)
        self._flow("encomenda: Oak entrega a Pokédex e Poké Balls", self._deliver_parcel)
        self.ctl.checkpoint("encomenda")

    def run(self) -> None:
        try:
            self.phase_pace()
            self.phase_route1()
            self.phase_parcel()
        except Abort:
            pass


def run_route1(ctx: ScenarioContext) -> None:
    """Roda o roteiro B a partir do checkpoint `rival` já carregado no emulador."""
    Route1Scenario(ctx).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roteiro rápido B (passos, Rota 1, encomenda)")
    parser.add_argument("--starter", required=True, choices=STARTERS)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rom", default=str(REPO_ROOT / "pokefirered_switch.gba"))
    parser.add_argument("--elf", default=str(REPO_ROOT / "pokefirered_switch.elf"))
    args = parser.parse_args(argv)
    start = time.monotonic()
    with open_context(args.rom, args.elf, args.out, args.starter) as ctx:
        if ctx.controller.checkpoint_path("rival").is_file():
            ctx.controller.restore("rival")
            species = ctx.game.party()[0].species
            if species != ctx.consts.species(args.starter):
                parser.error(f"o checkpoint rival de {args.out} é de "
                             f"{ctx.consts.species_name(species)}, não de {args.starter}")
        else:
            run_opening(ctx)
        if not ctx.suite.failed():
            run_route1(ctx)
        frames = ctx.emu.frames(0)
    return print_summary(ctx.suite, time.monotonic() - start, frames)


if __name__ == "__main__":
    sys.exit(main())
