"""Navegação no overworld: BFS sobre o map.bin do layout atual e passos conferidos.

Dados lidos do repo (nada adivinhado):
- data/maps/map_groups.json: (mapGroup, mapNum) -> nome do mapa;
- data/maps/<Nome>/map.json: layout e warp_events; data/layouts/layouts.json: tilesets e map.bin;
- map.bin: u16 por tile, colisão = (v >> 10) & 3, metatile = v & 0x3FF
  (include/fieldmap.h: MAPGRID_*); ids >= NUM_METATILES_IN_PRIMARY (640) são do tileset
  secundário (src/fieldmap.c: GetAttributeByMetatileIdAndMapLayout);
- metatile_attributes.bin: u32 por metatile, comportamento = attr & 0x1FF
  (src/fieldmap.c: sMetatileAttrMasks[METATILE_ATTRIBUTE_BEHAVIOR]).
"""

import json
import re
import struct
from collections import deque
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .control import Controller
from .emu import KEY_B, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP
from .result import StepTimeout

REPO_ROOT = Path(__file__).resolve().parents[2]

DIRECTIONS = {  # nome -> (dx, dy, tecla); o eixo y cresce para baixo, como nas coordenadas do jogo
    "up": (0, -1, KEY_UP),
    "down": (0, 1, KEY_DOWN),
    "left": (-1, 0, KEY_LEFT),
    "right": (1, 0, KEY_RIGHT),
}

_MB_JUMP = re.compile(r"^\s*#\s*define\s+(MB_JUMP_\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", re.M)
_TILESET_ATTRS = re.compile(r"^\s*\.metatileAttributes\s*=\s*(\w+)\s*,", re.M)
_TILESET_BLOCK = re.compile(r"const struct Tileset (\w+)\s*=\s*\{(.*?)\};", re.S)
_ATTR_INCBIN = re.compile(r"const u32 (\w+)\[\]\s*=\s*INCBIN_U32\(\"([^\"]+)\"\)")

NUM_METATILES_IN_PRIMARY = int(re.search(
    r"#define NUM_METATILES_IN_PRIMARY (\d+)",
    (REPO_ROOT / "include" / "fieldmap.h").read_text(encoding="utf-8")).group(1))
LEDGE_BEHAVIORS = {
    int(value, 0) for _name, value in _MB_JUMP.findall(
        (REPO_ROOT / "include" / "constants" / "metatile_behaviors.h").read_text(encoding="utf-8"))
}

# Direção que dispara o warp estando EM CIMA do tile (src/field_control_avatar.c:
# IsArrowWarpMetatileBehavior / IsDirectionalStairWarpMetatileBehavior).
WARP_TILE_DIRECTION = {
    0x62: "right",  # MB_EAST_ARROW_WARP
    0x63: "left",   # MB_WEST_ARROW_WARP
    0x64: "up",     # MB_NORTH_ARROW_WARP
    0x65: "down",   # MB_SOUTH_ARROW_WARP
    0x6C: "right",  # MB_UP_RIGHT_STAIR_WARP
    0x6D: "left",   # MB_UP_LEFT_STAIR_WARP
    0x6E: "right",  # MB_DOWN_RIGHT_STAIR_WARP
    0x6F: "left",   # MB_DOWN_LEFT_STAIR_WARP
}

STALL_FRAMES = 48       # sem mudar de tile por tanto tempo segurando a direção => bloqueado
MAX_REPLANS = 6          # tentativas de walk_to com NPC/obstáculo no caminho


class StepBlocked(StepTimeout):
    """O jogador não saiu do lugar (NPC, parede inesperada...), com evidências salvas.

    É um StepTimeout: se escapar de `walk_to`, a Suite o registra como `falha` com screenshot e
    savestate. `walk_to` o captura para replanejar.
    """

    def __init__(self, what: str, screenshot_path: str, state_path: str,
                 moved: int, tile: tuple[int, int]):
        super().__init__(what, screenshot_path, state_path)
        self.moved = moved   # tiles já andados antes de travar
        self.tile = tile     # tile que não pôde ser ocupado


@dataclass
class MapGrid:
    width: int
    height: int
    collision: list[int]               # colisão por tile (linha a linha)
    behaviors: list[int]               # comportamento do metatile por tile
    warps: set[tuple[int, int]] = field(default_factory=set)

    def blocked(self, x: int, y: int) -> bool:
        """Terreno intransponível: fora do mapa, colisão != 0 ou ledge (MB_JUMP_*)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True
        i = y * self.width + x
        return self.collision[i] != 0 or self.behaviors[i] in LEDGE_BEHAVIORS


@lru_cache(maxsize=None)
def _tileset_attr_paths(repo: str) -> dict[str, str]:
    """gTileset_X -> caminho do metatile_attributes.bin (src/data/tilesets/{headers,metatiles}.h)."""
    base = Path(repo) / "src" / "data" / "tilesets"
    files = dict(_ATTR_INCBIN.findall((base / "metatiles.h").read_text(encoding="utf-8")))
    paths = {}
    for name, body in _TILESET_BLOCK.findall((base / "headers.h").read_text(encoding="utf-8")):
        m = _TILESET_ATTRS.search(body)
        if m and m.group(1) in files:
            paths[name] = files[m.group(1)]
    return paths


def _read_attrs(repo: str, tileset: str) -> bytes:
    return (Path(repo) / _tileset_attr_paths(repo)[tileset]).read_bytes()


def map_name(repo: str, group: int, num: int) -> str:
    groups = json.loads((Path(repo) / "data" / "maps" / "map_groups.json").read_text("utf-8"))
    return groups[groups["group_order"][group]][num]


@lru_cache(maxsize=None)
def _load_map_grid(repo: str, group: int, num: int) -> MapGrid:
    name = map_name(repo, group, num)
    map_json = json.loads((Path(repo) / "data" / "maps" / name / "map.json").read_text("utf-8"))
    layouts = json.loads((Path(repo) / "data" / "layouts" / "layouts.json").read_text("utf-8"))
    layout = next(l for l in layouts["layouts"] if l.get("id") == map_json["layout"])
    width, height = layout["width"], layout["height"]
    raw = (Path(repo) / layout["blockdata_filepath"]).read_bytes()
    if len(raw) != width * height * 2:
        raise ValueError(f"{layout['blockdata_filepath']}: {len(raw)} bytes, esperado {width * height * 2}")
    blocks = struct.unpack(f"<{width * height}H", raw)
    primary = _read_attrs(repo, layout["primary_tileset"])
    secondary = _read_attrs(repo, layout["secondary_tileset"])

    def behavior(metatile: int) -> int:
        if metatile < NUM_METATILES_IN_PRIMARY:
            data, idx = primary, metatile
        else:
            data, idx = secondary, metatile - NUM_METATILES_IN_PRIMARY
        return struct.unpack_from("<I", data, idx * 4)[0] & 0x1FF

    return MapGrid(
        width=width,
        height=height,
        collision=[(v >> 10) & 3 for v in blocks],
        behaviors=[behavior(v & 0x3FF) for v in blocks],
        warps={(w["x"], w["y"]) for w in map_json.get("warp_events", [])},
    )


def load_map_grid(repo: str, group: int, num: int) -> MapGrid:
    """Grade de colisão/comportamento do mapa (mapGroup, mapNum); resultado em cache."""
    return _load_map_grid(str(repo), group, num)


def find_route(grid: MapGrid, start: tuple[int, int], goal: tuple[int, int],
               extra_blocked: set[tuple[int, int]] | frozenset = frozenset()) -> list[str] | None:
    """BFS de `start` a `goal`; devolve a lista de direções ('up'...) ou None se inalcançável.

    Tiles de warp só entram na rota se forem o próprio destino (pisar neles teletransporta).
    """
    if start == goal:
        return []
    if grid.blocked(*goal) or goal in extra_blocked:
        return None
    prev: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for name, (dx, dy, _key) in DIRECTIONS.items():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in seen or grid.blocked(*nxt) or nxt in extra_blocked:
                continue
            if nxt in grid.warps and nxt != goal:
                continue
            seen.add(nxt)
            prev[nxt] = (cur, name)
            if nxt == goal:
                route = []
                while nxt != start:
                    nxt, step = prev[nxt]
                    route.append(step)
                return route[::-1]
            queue.append(nxt)
    return None


class Navigator:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.game = controller.game
        self.emu = controller.emu
        # Por que o último step() parou antes de andar tudo: None (andou tudo), "script"
        # (script/warp/fade assumiu os controles) ou "battle".
        self.interrupted: str | None = None

    def _fail(self, what: str, cls: type = StepTimeout, **extra) -> StepTimeout:
        """Falha de navegação com evidências (screenshot + savestate), pronta para `raise`."""
        base = self.ctl.timeout_error(what)
        return cls(what, base.screenshot_path, base.state_path, **extra)

    def _grid(self) -> MapGrid:
        loc = self.game.location()
        try:
            return load_map_grid(str(REPO_ROOT), *loc)
        except (KeyError, IndexError, StopIteration, OSError) as exc:
            raise self._fail(f"dados de navegação do mapa {loc} ({exc!r})") from exc

    def _player_still(self) -> bool:
        base = self.game.syms.addr("gPlayerAvatar")
        return self.emu.read_u8(base + 3) == 0   # PlayerAvatar.tileTransitionState == T_NOT_MOVING

    @staticmethod
    def _outside_map(loc: tuple[int, int], pos: tuple[int, int]) -> bool:
        """`pos` fora dos limites do mapa `loc` (False se o mapa não tem dados de navegação)."""
        try:
            grid = load_map_grid(str(REPO_ROOT), *loc)
        except (KeyError, IndexError, StopIteration, OSError, ValueError):
            return False
        return not (0 <= pos[0] < grid.width and 0 <= pos[1] < grid.height)

    def step(self, direction: str, n: int = 1, run: bool = False) -> int:
        """Anda `n` tiles na direção, conferindo cada mudança de tile; devolve quantos andou.

        - Cruzar uma conexão de mapas (ex.: PalletTown -> Route 1) é transparente: o tile conta
          uma vez e o passo segue no mapa novo. Normalmente `pos` e `location` mudam no mesmo
          quadro; com chuva o mapa troca um quadro antes, com `pos` ainda no tile de partida (fora
          do mapa novo), e esse quadro não conta como tile.
        - Se um script/warp/fade ou uma batalha assumir os controles, para e devolve < n com
          `self.interrupted` = "script" ou "battle" (confira `game.location()` para warps).
        - Sem sair do lugar por STALL_FRAMES (NPC/parede) ou caindo em tile inesperado,
          levanta StepBlocked / StepTimeout, ambos com evidências salvas.
        """
        dx, dy, key = DIRECTIONS[direction]
        mask = key | (KEY_B if run else 0)
        self.interrupted = None
        self.ctl.wait_overworld_idle()
        loc = self.game.location()
        x, y = self.game.player_xy()
        done, stalled = 0, 0
        self.emu.keys(mask)
        try:
            while done < n:
                self.emu.frames(1)
                if self.game.in_battle():
                    self.interrupted = "battle"
                    break
                if self.ctl.script_active():
                    self.interrupted = "script"
                    break
                pos = self.game.player_xy()
                new_loc = self.game.location()
                if pos == (x, y) and new_loc == loc:
                    stalled += 1
                    if stalled >= STALL_FRAMES:
                        raise self._fail(
                            f"passo {direction} de {(x, y)} em {loc} bloqueado (NPC/parede?)",
                            StepBlocked, moved=done, tile=(x + dx, y + dy))
                    continue
                if new_loc == loc:
                    expected = (x + dx, y + dy)
                    if pos != expected:
                        raise self._fail(f"passo {direction} de {(x, y)}: esperava tile "
                                         f"{expected}, estou em {pos}")
                elif self._outside_map(new_loc, pos):
                    # conexão com o mapa trocado um quadro antes da posição (acontece com chuva,
                    # Hack 7): pos ainda é o tile de partida, nas coordenadas do mapa novo e fora
                    # dele; não conta, o tile chega no quadro seguinte
                    loc, x, y = new_loc, pos[0], pos[1]
                    stalled = 0
                    continue
                # (conexão: mudar de mapa sem script ativo; pos já vem nas coordenadas do novo)
                loc, x, y = new_loc, pos[0], pos[1]
                done += 1
                stalled = 0
        finally:
            self.emu.keys(0)
        if self.interrupted is None:
            # um encontro selvagem no último tile trava os controles e o avatar não chega a
            # ficar parado (a transição da batalha começa no meio da animação do passo)
            self.ctl.wait_until(lambda: self._player_still() or self.ctl.script_active()
                                or self.game.in_battle(), 60, "fim do passo")
            if self.game.in_battle():
                self.interrupted = "battle"
            elif self.ctl.script_active():
                self.interrupted = "script"   # gatilho/encontro disparado no último tile
        return done

    def walk_to(self, x: int, y: int, run: bool = False) -> bool:
        """Anda até (x, y) do mapa atual; True se chegou, False se um warp/script/batalha interrompeu.

        Replaneja (esperando e contornando o tile) se um NPC bloquear; esgotadas as tentativas,
        levanta StepTimeout com evidências.
        """
        goal = (x, y)
        start_loc = self.game.location()
        grid = self._grid()
        temp_blocked: set[tuple[int, int]] = set()
        for _attempt in range(MAX_REPLANS):
            cur = self.game.player_xy()
            if cur == goal:
                return True
            route = find_route(grid, cur, goal, temp_blocked)
            if route is None and temp_blocked:
                temp_blocked.clear()
                route = find_route(grid, cur, goal)
            if route is None:
                raise self.ctl.timeout_error(f"rota de {cur} até {goal} em {start_loc}")
            i = 0
            try:
                while i < len(route):
                    j = i
                    while j < len(route) and route[j] == route[i]:
                        j += 1
                    moved = self.step(route[i], j - i, run)
                    if moved < j - i or self.interrupted is not None:
                        # interrompido por warp, script ou batalha (inclusive gatilho
                        # disparado no último tile do trecho, com o trecho completo)
                        return False
                    i = j
                return self.game.player_xy() == goal
            except StepBlocked as blocked:
                temp_blocked.add(blocked.tile)
                self.emu.frames(30)         # dá tempo ao NPC de sair da frente
        raise self.ctl.timeout_error(f"NPC bloqueando a rota até {goal} em {start_loc}")

    def go_through_warp(self, direction: str | None = None, timeout: int = 600) -> tuple[int, int]:
        """Segura `direction` até o mapa mudar e espera o overworld ficar livre no destino.

        Sem `direction`, usa o único vizinho do jogador que é warp_event (portas: ficam em
        tile com colisão, então basta andar contra elas). Se o jogador estiver em cima do
        warp, a direção vem do comportamento do tile (arrow warp/escada direcional); outros
        casos exigem `direction`. Devolve (mapGroup, mapNum) do destino.
        """
        start_loc = self.game.location()
        if direction is None:
            direction = self._warp_direction()
        key = DIRECTIONS[direction][2]
        self.ctl.wait_overworld_idle()
        self.emu.keys(key)
        try:
            self.ctl.wait_until(
                lambda: self.game.location() != start_loc or self.ctl.script_active(),
                180, f"início do warp ({direction})")
        finally:
            self.emu.keys(0)
        self.ctl.wait_until(lambda: self.game.location() != start_loc, timeout, "troca de mapa")
        self.ctl.wait_overworld_idle(timeout)
        return self.game.location()

    def _warp_direction(self) -> str:
        grid = self._grid()
        px, py = self.game.player_xy()
        if (px, py) in grid.warps:
            # sobre o warp: a direção vem do comportamento (arrow warps e escadas direcionais)
            direction = WARP_TILE_DIRECTION.get(grid.behaviors[py * grid.width + px])
            if direction is None:
                raise self._fail(f"jogador sobre o warp {(px, py)} sem direção conhecida: "
                                 "informe a direção em go_through_warp()")
            return direction
        near = [name for name, (dx, dy, _k) in DIRECTIONS.items() if (px + dx, py + dy) in grid.warps]
        if not near:
            raise self._fail(f"nenhum warp ao lado de {(px, py)} em {self.game.location()}")
        return near[0]
