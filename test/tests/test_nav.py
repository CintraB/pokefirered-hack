"""Navegação: BFS sobre o map.bin real e leitura de layouts/tilesets."""

from pathlib import Path

import pytest

from esteira.charmap import Charmap
from esteira.constants import Constants
from esteira.control import Controller
from esteira.emu import KEY_A, KEY_START, Emulator
from esteira.game import Game
from esteira.nav import LEDGE_BEHAVIORS, MapGrid, Navigator, find_route, load_map_grid
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
