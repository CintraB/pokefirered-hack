"""Navegação: BFS sobre o map.bin real e leitura de layouts/tilesets."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from esteira.charmap import Charmap
from esteira.constants import Constants
from esteira.control import Controller
from esteira.emu import KEY_A, KEY_START, Emulator
from esteira.game import Game
from esteira.nav import (LEDGE_BEHAVIORS, MAX_REPLANS, MapGrid, Navigator, StepBlocked, find_route,
                         load_map_grid)
from esteira.result import StepTimeout, Suite
from esteira.symbols import Symbols

REPO_ROOT = Path(__file__).resolve().parents[2]
PALLET = (3, 0)  # (mapGroup, mapNum) de PalletTown: gMapGroup_TownsAndRoutes[0]
DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def walk(route, start):
    x, y = start
    tiles = []
    for d in route:
        x, y = x + DELTA[d][0], y + DELTA[d][1]
        tiles.append((x, y))
    return tiles


def test_bfs_route_pallet_town():
    grid = load_map_grid(str(REPO_ROOT), *PALLET)
    assert (grid.width, grid.height) == (24, 20)
    # início (5,8) e saída norte (12,0): ambos livres em map.bin (rua em y=8 e o
    # corredor de 2 tiles em x=12..13, y=0..1 que leva à Route 1)
    start, goal = (5, 8), (12, 0)
    assert not grid.blocked(*start) and not grid.blocked(*goal)
    route = find_route(grid, start, goal)
    assert route is not None
    tiles = walk(route, start)
    assert tiles[-1] == goal
    assert all(not grid.blocked(x, y) for x, y in tiles)
    # há caminho livre em L pela rua, então a rota mais curta é a distância de Manhattan
    assert len(route) == abs(5 - 12) + abs(8 - 0)


def test_bfs_detours_around_walls_and_refuses_walled_goal():
    grid = load_map_grid(str(REPO_ROOT), *PALLET)
    # (6,5) é parede da casa do jogador (collision != 0): destino bloqueado => sem rota
    assert grid.blocked(6, 5)
    assert find_route(grid, (5, 8), (6, 5)) is None
    # a casa ocupa x=5..9, y=4..7: de (6,8) a (6,3) é preciso contornar
    route = find_route(grid, (6, 8), (6, 3))
    assert route is not None
    tiles = walk(route, (6, 8))
    assert tiles[-1] == (6, 3) and all(not grid.blocked(x, y) for x, y in tiles)
    assert len(route) > abs(8 - 3)
    assert find_route(grid, (5, 8), (5, 8)) == []


def test_real_door_tile_is_blocked_and_listed_as_warp():
    grid = load_map_grid(str(REPO_ROOT), *PALLET)
    assert (6, 7) in grid.warps  # porta da casa do jogador (warp_events de map.json)
    assert grid.blocked(6, 7)    # portas têm collision: entra-se andando contra elas


def test_walkable_warp_only_when_goal_and_ledge_blocked():
    plain = [0, 0, 0]
    grid = MapGrid(3, 1, collision=plain, behaviors=[0, 0, 0], warps={(1, 0)})
    assert find_route(grid, (0, 0), (2, 0)) is None          # warp no meio não é atalho
    assert find_route(grid, (0, 0), (1, 0)) == ["right"]     # mas pode ser o destino
    ledge = MapGrid(3, 1, collision=plain, behaviors=[0, 0x3B, 0], warps=set())
    assert find_route(ledge, (0, 0), (2, 0)) is None         # ledge MB_JUMP_SOUTH bloqueia
    assert LEDGE_BEHAVIORS == {0x38, 0x39, 0x3A, 0x3B}
    free = MapGrid(3, 1, collision=plain, behaviors=[0, 0, 0], warps=set())
    assert find_route(free, (0, 0), (2, 0), extra_blocked={(1, 0)}) is None


def test_route1_has_ledge_tiles():
    consts = Constants.load(str(REPO_ROOT))
    grid = load_map_grid(str(REPO_ROOT), *consts.map("MAP_ROUTE1"))
    assert any(b in LEDGE_BEHAVIORS for b in grid.behaviors)


# --- smoke ao vivo: novo jogo -> quarto -> escada -> casa -> rua ---------------------

def _new_game_overworld(ctl, game, emu):
    """Aperta A/START (nomeia o jogador com o padrão) até o overworld ficar livre."""
    for i in range(1, 1500):
        if ctl.overworld_idle():
            return
        emu.press(KEY_A if i % 7 else KEY_START, hold=2, release=8)
    raise AssertionError(f"não chegou ao overworld (callback2={game.callback2()})")


def test_navigator_live_bedroom_to_town(rom_path, tmp_save, tmp_path):
    elf = REPO_ROOT / "pokefirered_switch.elf"
    if not elf.is_file():
        pytest.skip(f"ELF não encontrado: {elf}")
    consts = Constants.load(str(REPO_ROOT))
    with Emulator(rom_path, tmp_save) as emu:
        game = Game(emu, Symbols.from_elf(str(elf)), consts, Charmap.load(str(REPO_ROOT)))
        ctl = Controller(emu, game, str(tmp_path / "out"))
        nav = Navigator(ctl)
        _new_game_overworld(ctl, game, emu)
        assert game.location() == consts.map("MAP_PALLET_TOWN_PLAYERS_HOUSE_2F")
        # escada no tile (10,2) do 2F (MB_DOWN_LEFT_STAIR_WARP: dispara andando para a esquerda)
        assert nav.walk_to(10, 2)
        assert nav.go_through_warp() == consts.map("MAP_PALLET_TOWN_PLAYERS_HOUSE_1F")
        # tapete de saída (4,8) do 1F: MB_SOUTH_ARROW_WARP
        assert nav.walk_to(4, 8)
        assert nav.go_through_warp() == consts.map("MAP_PALLET_TOWN")
        assert game.player_xy() == (6, 8)
        # contornando a casa até a porta do rival e entrando nela (porta tem colisão)
        assert nav.walk_to(15, 8, run=True)
        assert nav.go_through_warp() == consts.map("MAP_PALLET_TOWN_RIVALS_HOUSE")


# --- walk_to: replanejamento quando um NPC bloqueia (Controller/Game falsos) -----------

class _FakeCtl:
    def __init__(self):
        self.game = SimpleNamespace(location=lambda: PALLET)
        self.emu = SimpleNamespace(frames=self._frames)
        self.waited = 0
        self.failures = []

    def _frames(self, n):
        self.waited += n

    def timeout_error(self, what):
        self.failures.append(what)
        return StepTimeout(what, "fake.png", "fake.ss")


def _fake_nav(step_fn):
    ctl = _FakeCtl()
    pos = [5, 8]
    ctl.game.player_xy = lambda: tuple(pos)
    nav = Navigator(ctl)
    nav.step = lambda direction, n=1, run=False: step_fn(nav, ctl, pos, direction, n)
    return nav, ctl, pos


def _advance(pos, direction, n):
    dx, dy = DELTA[direction]
    pos[0] += dx * n
    pos[1] += dy * n
    return n


def test_walk_to_replans_around_blocking_npc():
    calls = []

    def step(nav, ctl, pos, direction, n):
        calls.append((tuple(pos), direction, n))
        if len(calls) == 1:  # um NPC está em (6,8), logo à direita do início
            raise StepBlocked("npc", "fake.png", "fake.ss", moved=0, tile=(6, 8))
        return _advance(pos, direction, n)

    nav, ctl, pos = _fake_nav(step)
    assert nav.walk_to(12, 8) is True
    assert tuple(pos) == (12, 8)
    assert calls[0][1] == "right"                 # primeira rota: reta pela rua
    assert ctl.waited == 30                       # esperou o NPC sair
    first_replanned = calls[1]
    assert first_replanned[0] == (5, 8) and first_replanned[1] != "right"  # (6,8) bloqueado
    walked = [(5, 8)]
    for _start, d, n in calls[1:]:
        for _ in range(n):
            walked.append((walked[-1][0] + DELTA[d][0], walked[-1][1] + DELTA[d][1]))
    assert (6, 8) not in walked


def test_walk_to_gives_up_with_evidence_after_max_replans():
    count = []

    def step(nav, ctl, pos, direction, n):
        count.append(1)
        dx, dy = DELTA[direction]
        raise StepBlocked("npc", "fake.png", "fake.ss", moved=0, tile=(pos[0] + dx, pos[1] + dy))

    nav, ctl, pos = _fake_nav(step)
    with pytest.raises(StepTimeout) as info:
        nav.walk_to(12, 8)
    assert len(count) == MAX_REPLANS
    assert info.value.screenshot_path == "fake.png" and info.value.state_path == "fake.ss"
    assert "NPC bloqueando" in info.value.what and ctl.failures


def test_walk_to_reports_interruption_without_error():
    def step(nav, ctl, pos, direction, n):
        return _advance(pos, direction, 1)  # um tile a menos que o pedido: script assumiu

    nav, _ctl, _pos = _fake_nav(step)
    assert nav.walk_to(12, 8) is False


def test_walk_to_stops_when_trigger_fires_on_last_tile_of_segment():
    calls = []

    def step(nav, ctl, pos, direction, n):
        calls.append((direction, n))
        moved = _advance(pos, direction, n)
        nav.interrupted = "script"   # gatilho no último tile do trecho: andou tudo, script assumiu
        return moved

    nav, _ctl, _pos = _fake_nav(step)
    # (5,8) -> (12,2): dois trechos (direita e cima); o segundo não pode começar
    assert nav.walk_to(12, 2) is False
    assert len(calls) == 1


# --- step com mundo falso: encontro selvagem no último tile ----------------------------

class _StepWorld:
    """Um passo para a direita a partir de (5,8): o tile muda no quadro `arrive`; os
    controles travam no quadro `lock` (encontro selvagem) e o avatar nunca volta a ficar
    parado (tileTransitionState != T_NOT_MOVING), como na transição para a batalha."""

    def __init__(self, arrive: int = 6, lock: int = 9):
        self.frame = 0
        self.arrive, self.lock = arrive, lock
        self.game = SimpleNamespace(location=lambda: PALLET, player_xy=self._xy,
                                    in_battle=lambda: False,
                                    syms=SimpleNamespace(addr=lambda name: 0x1000))
        self.emu = SimpleNamespace(frames=self._frames, keys=lambda mask: None,
                                   read_u8=lambda addr: 0 if self.frame < 1 else 1)

    def _frames(self, n):
        self.frame += n
        return self.frame

    def _xy(self):
        return (6, 8) if self.frame >= self.arrive else (5, 8)

    def wait_overworld_idle(self, timeout=600):
        return 0

    def script_active(self):
        return self.frame >= self.lock

    def wait_until(self, pred, timeout, what):
        spent = 0
        while not pred():
            if spent >= timeout:
                raise self.timeout_error(what)
            self._frames(2)
            spent += 2
        return spent

    def timeout_error(self, what):
        return StepTimeout(what, "fake.png", "fake.ss")


def test_step_reports_lock_on_last_tile_even_if_player_never_stops():
    world = _StepWorld()
    nav = Navigator(world)
    assert nav.step("right", 1) == 1
    assert nav.interrupted == "script"


# --- step ao vivo: bloqueio com evidência e conexão de mapas -------------------------



def _dry_clock(emu, game) -> None:
    """Hack 7 frente A: o jogo novo começa às 08:00 do dia 0, quando Kanto (INLAND) sorteia chuva;
    a travessia de conexão com chuva atrasa um quadro e o mapa muda antes da posição. O relógio vai
    para 08:00 de um dia seco (gameClockFrames em SaveBlock2 0x090) antes de sair de casa."""
    from esteira import dia_noite as dn
    day = next(d for d in range(1, 100) if dn.roll_weather(dn.REGION_INLAND, d, dn.MORNING) == dn.WEATHER_NONE)
    sb2 = emu.read_u32(game.syms.addr("gSaveBlock2Ptr"))
    emu.write(sb2 + 0x090, (day * dn.MINUTES_PER_DAY * dn.FRAMES_PER_MINUTE).to_bytes(4, "little"))


@pytest.fixture
def town(rom_path, tmp_save, tmp_path):
    """Novo jogo, já em PalletTown (6,8), na rua em frente à casa."""
    elf = REPO_ROOT / "pokefirered_switch.elf"
    if not elf.is_file():
        pytest.skip(f"ELF não encontrado: {elf}")
    consts = Constants.load(str(REPO_ROOT))
    with Emulator(rom_path, tmp_save) as emu:
        game = Game(emu, Symbols.from_elf(str(elf)), consts, Charmap.load(str(REPO_ROOT)))
        ctl = Controller(emu, game, str(tmp_path / "out"))
        nav = Navigator(ctl)
        _new_game_overworld(ctl, game, emu)
        _dry_clock(emu, game)
        assert nav.walk_to(10, 2)
        nav.go_through_warp()
        assert nav.walk_to(4, 8)
        assert nav.go_through_warp() == consts.map("MAP_PALLET_TOWN")
        yield SimpleNamespace(emu=emu, game=game, ctl=ctl, nav=nav, consts=consts)


def test_blocked_direct_step_is_step_timeout_with_evidence_and_falha(town):
    nav, game = town.nav, town.game
    assert nav.walk_to(5, 8)
    # (5,7) é parede da casa: andar para cima não sai do lugar
    with pytest.raises(StepTimeout) as info:
        nav.step("up")
    exc = info.value
    assert isinstance(exc, StepBlocked) and exc.tile == (5, 7) and exc.moved == 0
    assert Path(exc.screenshot_path).is_file() and Path(exc.state_path).is_file()
    assert game.player_xy() == (5, 8)

    suite = Suite()
    suite.run("passo bloqueado", lambda: nav.step("up"))
    (res,) = suite.results
    assert res.status == "falha" and suite.failed()
    assert len(res.images) == 1 and Path(res.images[0]).is_file()
    assert "bloqueado" in res.detail


def test_step_reports_oak_trigger_as_script_interruption(town):
    nav, game = town.nav, town.game
    assert nav.walk_to(12, 2)
    # coord event do Oak em (12,1): script assume ao pisar nele (e step informa, sem erro)
    moved = nav.step("up", 3)
    assert moved == 1 and nav.interrupted == "script"
    assert game.player_xy() == (12, 1)
    assert game.location() == town.consts.map("MAP_PALLET_TOWN")
    assert town.ctl.script_active()


def test_step_crosses_map_connection_to_route1(town):
    nav, game, emu, consts = town.nav, town.game, town.emu, town.consts
    # desliga o gatilho do Oak (VAR_MAP_SCENE_PALLET_TOWN_OAK=0x4050 != 0), senão o script
    # o para em (12,1). SaveBlock1.vars começa em 0x1000 (include/global.h).
    sb1 = emu.read_u32(town.game.syms.addr("gSaveBlock1Ptr"))
    emu.write(sb1 + 0x1000 + (0x4050 - 0x4000) * 2, (1).to_bytes(2, "little"))
    assert nav.walk_to(12, 2)
    route1 = consts.map("MAP_ROUTE1")
    height = load_map_grid(str(REPO_ROOT), *route1).height
    # 12,1 -> 12,0 -> (cruza a conexão) -> Route 1 na linha de baixo
    assert nav.step("up", 3) == 3 and nav.interrupted is None
    assert game.location() == route1
    assert game.player_xy() == (12, height - 1)
    # e o passo continua normalmente no mapa novo, também com a conexão no meio de um n maior
    assert nav.step("down", 1) == 1 and game.location() == consts.map("MAP_PALLET_TOWN")
    assert game.player_xy() == (12, 0)
    assert nav.step("up", 4) == 4 and game.location() == route1
    assert game.player_xy() == (12, height - 4)   # y=-1 vira height-1; mais 3 tiles
