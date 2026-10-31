"""Viagem entre mapas de Pallet a Pewter, resistente a encontros, treinadores e desmaios.

Mixin para cenários derivados de Route1Scenario (usa _walk de lá como base, _cross, _warp,
_talk, driver...). O mapa é um grafo de "nós" (mapas; a Rota 2 tem duas partes sem ligação a
pé: "MAP_ROUTE2" ao sul da Floresta e "MAP_ROUTE2#N" ao norte) com as arestas abaixo,
coordenadas de data/maps/*/map.json e dos layouts (grades conferidas com nav.py):
`_go(destino)` acha o caminho e anda aresta por aresta. Se no meio do caminho o jogador mudar
de mapa sem querer (desmaio do time = volta ao último Centro), `Relocated` faz `_go`
recalcular a partir de onde ele está.

Interrupções no caminho (`_resolve_interruption`): falas são avançadas com A; batalha
selvagem é fugida (ou lutada, com `self.fight_wild`); batalha de treinador é lutada até o fim
e registrada em measures["trainers"] com o prêmio esperado (`trainer_reward`); a batalha
tutorial do velho de Viridian só avança texto.
"""

import struct
from collections import deque

from ..battle import BATTLE_TYPE_TRAINER, OUTCOME_NAMES
from ..emu import KEY_A, KEY_UP
from .base import TEXT_PERIOD, dispensar_avisos

BATTLE_TYPE_DOUBLE = 1 << 0
BATTLE_TYPE_OLD_MAN_TUTORIAL = 1 << 9          # include/constants/battle.h

# struct Trainer (include/battle.h), tabela gTrainers no ROM
TRAINER_SIZE = 0x28
TRAINER_PARTY_FLAGS, TRAINER_CLASS, TRAINER_NAME = 0x00, 0x01, 0x04
TRAINER_PARTY_SIZE, TRAINER_PARTY = 0x20, 0x24
TRAINER_NAME_LENGTH = 12
# tamanho de cada struct TrainerMon* por partyFlags (F_TRAINER_PARTY_CUSTOM_MOVESET = 1,
# F_TRAINER_PARTY_HELD_ITEM = 2), como o agbcc as alinha (a 4 bytes: conferido no ROM, ex.
# sParty_CamperLiam com 16 bytes por Pokémon); o nível (u8 lvl) fica no byte 2 de todas
TRAINER_MON_SIZE = {0: 8, 1: 16, 2: 8, 3: 16}
TRAINER_MON_LEVEL = 2
MONEY_TABLE_END = 0xFF                         # gTrainerMoneyTable termina em classId 0xFF
BATTLE_STRUCT_MONEY_MULTIPLIER = 0x4A          # struct BattleStruct.moneyMultiplier (u8)

CENTER_NURSE_FRONT = (7, 4)    # Centros de Viridian e Pewter: enfermeira em (7, 2)
SCRIPT_TIMEOUT = 12000         # fala longa (tutorial do velho, Brock, tênis de corrida)
MAX_LEGS = 40


class Relocated(Exception):
    """O jogador foi parar em outro mapa no meio de uma aresta (desmaio, warp inesperado)."""


def _walk_to(x, y):
    return ("walk", x, y)


def _cross(direction):
    return ("cross", direction)


def _warp(direction=None):
    return ("warp", direction)


# (de, para) -> passos. "walk" anda até o tile; "cross" atravessa a conexão de mapa à frente;
# "warp" entra na porta/escada ao lado (direção None = o único warp vizinho); "call" chama o
# método do cenário.
EDGES: dict[tuple[str, str], list[tuple]] = {
    ("MAP_PALLET_TOWN_RIVALS_HOUSE", "MAP_PALLET_TOWN"): [_walk_to(4, 7), _warp("down")],
    ("MAP_PALLET_TOWN", "MAP_PALLET_TOWN_RIVALS_HOUSE"): [_walk_to(15, 8), _warp()],
    ("MAP_PALLET_TOWN", "MAP_ROUTE1"): [_walk_to(13, 3), _walk_to(13, 0), _cross("up")],
    ("MAP_ROUTE1", "MAP_PALLET_TOWN"): [_walk_to(13, 39), _cross("down")],
    ("MAP_ROUTE1", "MAP_VIRIDIAN_CITY"): [_walk_to(13, 0), _cross("up")],
    ("MAP_VIRIDIAN_CITY", "MAP_ROUTE1"): [_walk_to(25, 39), _cross("down")],
    ("MAP_VIRIDIAN_CITY", "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F"): [_walk_to(26, 27), _warp()],
    ("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", "MAP_VIRIDIAN_CITY"): [_walk_to(7, 7), _warp("down")],
    ("MAP_VIRIDIAN_CITY", "MAP_VIRIDIAN_CITY_MART"): [_walk_to(36, 20), _warp()],
    ("MAP_VIRIDIAN_CITY_MART", "MAP_VIRIDIAN_CITY"): [_walk_to(4, 6), _warp("down")],
    ("MAP_VIRIDIAN_CITY", "MAP_ROUTE2"): [("call", "_viridian_north")],
    ("MAP_ROUTE2", "MAP_VIRIDIAN_CITY"): [_walk_to(10, 79), _cross("down")],
    ("MAP_ROUTE2", "MAP_ROUTE2_VIRIDIAN_FOREST_SOUTH_ENTRANCE"): [_walk_to(5, 52), _warp("up")],
    ("MAP_ROUTE2_VIRIDIAN_FOREST_SOUTH_ENTRANCE", "MAP_ROUTE2"): [_walk_to(7, 9), _warp("down")],
    ("MAP_ROUTE2_VIRIDIAN_FOREST_SOUTH_ENTRANCE", "MAP_VIRIDIAN_FOREST"):
        [_walk_to(7, 2), _warp("up")],
    ("MAP_VIRIDIAN_FOREST", "MAP_ROUTE2_VIRIDIAN_FOREST_SOUTH_ENTRANCE"):
        [_walk_to(29, 61), _warp("down")],
    ("MAP_VIRIDIAN_FOREST", "MAP_ROUTE2_VIRIDIAN_FOREST_NORTH_ENTRANCE"):
        [_walk_to(5, 10), _warp("up")],
    ("MAP_ROUTE2_VIRIDIAN_FOREST_NORTH_ENTRANCE", "MAP_VIRIDIAN_FOREST"):
        [_walk_to(7, 9), _warp("down")],
    ("MAP_ROUTE2_VIRIDIAN_FOREST_NORTH_ENTRANCE", "MAP_ROUTE2#N"): [_walk_to(7, 2), _warp("up")],
    ("MAP_ROUTE2#N", "MAP_ROUTE2_VIRIDIAN_FOREST_NORTH_ENTRANCE"): [_walk_to(5, 12), _warp("down")],
    ("MAP_ROUTE2#N", "MAP_PEWTER_CITY"): [_walk_to(9, 0), _cross("up")],
    ("MAP_PEWTER_CITY", "MAP_ROUTE2#N"): [_walk_to(21, 39), _cross("down")],
    ("MAP_PEWTER_CITY", "MAP_PEWTER_CITY_POKEMON_CENTER_1F"): [_walk_to(17, 26), _warp()],
    ("MAP_PEWTER_CITY_POKEMON_CENTER_1F", "MAP_PEWTER_CITY"): [_walk_to(7, 7), _warp("down")],
    ("MAP_PEWTER_CITY", "MAP_PEWTER_CITY_GYM"): [_walk_to(15, 17), _warp()],
    ("MAP_PEWTER_CITY_GYM", "MAP_PEWTER_CITY"): [_walk_to(6, 13), _warp("down")],
    ("MAP_PEWTER_CITY", "MAP_PEWTER_CITY_MART"): [_walk_to(28, 19), _warp()],
    ("MAP_PEWTER_CITY_MART", "MAP_PEWTER_CITY"): [_walk_to(4, 6), _warp("down")],
}
ROUTE2_NORTH = "MAP_ROUTE2#N"
ROUTE2_NORTH_PART = (11, 13)        # tiles com x <= 11 e y <= 13 são a parte norte da Rota 2
CENTERS = ("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", "MAP_PEWTER_CITY_POKEMON_CENTER_1F")

# Viridian, saída norte: com VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN = 1 (depois da Pokédex) o
# velho fica em (21, 8) e as únicas passagens, (20, 8) e (22, 8), disparam o tutorial de
# captura (data/maps/ViridianCity/scripts.inc), que termina dando a TEACHY TV.
OLD_MAN_APPROACH = (22, 9)
VIRIDIAN_NORTH_EDGE = (22, 0)       # conexão "up" para a Rota 2 (offset 12 -> x = 10)


def find_path(start: str, dest: str) -> list[str] | None:
    """Nós de `start` a `dest` (inclusive) pelo grafo EDGES; None se não há caminho."""
    prev: dict[str, str] = {start: start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == dest:
            path = [cur]
            while path[-1] != start:
                path.append(prev[path[-1]])
            return path[::-1]
        for a, b in EDGES:
            if a == cur and b not in prev:
                prev[b] = cur
                queue.append(b)
    return None


def trainer_reward(last_level: int, class_value: int, multiplier: int, double: bool) -> int:
    """Prêmio de src/battle_script_commands.c (Cmd_getmoneyreward):
    4 * nível do último Pokémon * moneyMultiplier * (2 se dupla) * gTrainerMoneyTable[classe]."""
    return 4 * last_level * multiplier * (2 if double else 1) * class_value


def read_trainer(read, trainers: int, money_table: int, trainer_id: int) -> dict:
    """gTrainers[trainer_id] e gTrainerMoneyTable pelo leitor `read(endereço, n)`: classe,
    nível do último Pokémon do time e o valor da classe (sem a classe na tabela, o jogo usa o
    da entrada final 0xFF, como o laço de Cmd_getmoneyreward)."""
    raw = read(trainers + trainer_id * TRAINER_SIZE, TRAINER_SIZE)
    flags, klass, size = raw[TRAINER_PARTY_FLAGS], raw[TRAINER_CLASS], raw[TRAINER_PARTY_SIZE]
    party = struct.unpack_from("<I", raw, TRAINER_PARTY)[0]
    last = read(party + (size - 1) * TRAINER_MON_SIZE[flags] + TRAINER_MON_LEVEL, 1)[0]
    value = None
    for i in range(256):
        cls_id, val = read(money_table + 2 * i, 2)
        if cls_id in (klass, MONEY_TABLE_END):
            value = val
            break
    return {"id": trainer_id, "class": klass, "last_level": last, "class_value": value,
            "raw_name": raw[TRAINER_NAME:TRAINER_NAME + TRAINER_NAME_LENGTH]}


class TravelMixin:
    fight_wild = False          # True: encontros selvagens no caminho são lutados (treino)

    # --- onde estou ----------------------------------------------------------------
    def _node_names(self) -> dict[tuple[int, int], str]:
        names = getattr(self, "_nodes_by_loc", None)
        if names is None:
            names = {}
            for a, b in EDGES:
                for name in (a, b):
                    base = name.split("#")[0]
                    names[self.consts.map(base)] = base
            self._nodes_by_loc = names
        return names

    def _node(self) -> str:
        loc = self.game.location()
        name = self._node_names().get(loc)
        if name is None:
            raise AssertionError(f"mapa {loc} fora do roteiro de viagem")
        if name == "MAP_ROUTE2":
            x, y = self.game.player_xy()
            if x <= ROUTE2_NORTH_PART[0] and y <= ROUTE2_NORTH_PART[1]:
                return ROUTE2_NORTH
        return name

    # --- viagem --------------------------------------------------------------------
    def _go(self, dest: str) -> None:
        """Vai até o nó `dest` (nome do mapa, ou MAP_ROUTE2#N)."""
        for _ in range(MAX_LEGS):
            node = self._node()
            if node == dest:
                return
            path = find_path(node, dest)
            if path is None:
                raise AssertionError(f"sem caminho de {node} até {dest}")
            try:
                self._run_edge(node, path[1])
            except Relocated:
                self.measures["relocated"] = self.measures.get("relocated", 0) + 1
        raise self.ctl.timeout_error(f"viagem até {dest} passou de {MAX_LEGS} trechos")

    def _run_edge(self, node: str, nxt: str) -> None:
        for step in EDGES[(node, nxt)]:
            if self._node() != node:
                raise Relocated()
            kind = step[0]
            if kind == "walk":
                self._walk(step[1], step[2])
            elif kind == "cross":
                self._cross(step[1], nxt.split("#")[0])
            elif kind == "warp":
                self._warp(step[1], nxt.split("#")[0])
            else:
                getattr(self, step[1])()

    def _walk(self, x: int, y: int) -> None:
        """walk_to no mapa atual; interrupções resolvidas; Relocated se mudou de mapa."""
        start = self._node()
        for _ in range(20):
            if self.nav.walk_to(x, y):
                return
            self._resolve_interruption()
            if self._node() != start:
                raise Relocated()
        raise self.ctl.timeout_error(f"caminho até {(x, y)} em {start} interrompido demais")

    def _viridian_north(self) -> None:
        teachy = self.consts.item("ITEM_TEACHY_TV")
        if self.game.bag_quantity(teachy) == 0:
            self._walk(*OLD_MAN_APPROACH)
            self.nav.step("up", 1)
            self.ctl.wait_until(self.ctl.script_active, 120,   # o gatilho roda ao parar no tile
                                f"tutorial do velho em {self.game.player_xy()}")
            self._resolve_interruption()
            qty = self.game.bag_quantity(teachy)
            assert qty == 1, f"tutorial do velho de Viridian sem a TEACHY TV (x{qty})"
            self.measures["old_man_tutorial"] = True
        self._walk(*VIRIDIAN_NORTH_EDGE)
        self._cross("up", "MAP_ROUTE2")

    # --- Centro --------------------------------------------------------------------
    def _heal_at_nearest_center(self, center: str) -> None:
        self._go(center)
        self._walk(*CENTER_NURSE_FRONT)
        self._talk(KEY_UP, "enfermeira cura o time")
        party = self.game.party()
        assert all(m.hp == m.max_hp for m in party), (
            f"time não curado: {[(m.hp, m.max_hp) for m in party]}")
        self.measures["center_visits"] = self.measures.get("center_visits", 0) + 1

    # --- interrupções --------------------------------------------------------------
    def _resolve_interruption(self) -> None:
        """Avança falas (A), luta/foge das batalhas, até o overworld ficar livre."""
        self._wait_battle_or_text()
        spent = 0
        while not self._settled_idle():
            if self.game.in_battle():
                self._battle_on_the_way()
                spent = 0
                continue
            if spent >= SCRIPT_TIMEOUT:
                raise self.ctl.timeout_error("fala ou cena no caminho")
            self._press(KEY_A)
            spent += TEXT_PERIOD

    def _battle_on_the_way(self) -> None:
        self.driver.wait_battle_start()
        flags = self.driver.battle_type_flags()
        if flags & BATTLE_TYPE_OLD_MAN_TUTORIAL:
            self.ctl.advance_text(lambda: not self.game.in_battle(), SCRIPT_TIMEOUT,
                                  "batalha tutorial do velho")
        elif flags & BATTLE_TYPE_TRAINER:
            self._trainer_battle()
        elif self.fight_wild:
            self._wild_fight()
        else:
            self._escape_battle()

    def _after_battle(self, what: str) -> None:
        """Depois de qualquer batalha: desmaio do time vira contagem (o jogo leva ao Centro);
        falas, evolução e o desmaio são avançados com A (B cancelaria a evolução)."""
        if OUTCOME_NAMES.get(self.driver.outcome()) == "lose":
            self.measures["whiteouts"] = self.measures.get("whiteouts", 0) + 1
        spent = 0
        while self.game.in_battle() or not self._settled_idle():
            if spent >= SCRIPT_TIMEOUT:
                raise self.ctl.timeout_error(f"volta ao overworld depois de: {what}")
            self._press(KEY_A)
            spent += TEXT_PERIOD
        dispensar_avisos(self.ctx)   # conquista da batalha (vitórias, sem desmaio, x4...)

    def _wild_fight(self) -> str:
        self.driver.move_policy = "best"
        species, level = self.driver.battler_species_level(1)
        outcome = self.driver.fight_to_end()
        self._after_battle("batalha selvagem de treino")
        self.measures["wild_fights"] = self.measures.get("wild_fights", 0) + 1
        return f"{self._species(species)} nv{level}: {outcome}"

    # --- treinadores ---------------------------------------------------------------
    def _trainer_info(self) -> dict:
        """Lido na batalha: treinador, classe, nível do último Pokémon e o prêmio esperado."""
        emu, syms = self.emu, self.game.syms
        trainer_id = emu.read_u16(syms.addr("gTrainerBattleOpponent_A"))
        info = read_trainer(emu.read, syms.addr("gTrainers"), syms.addr("gTrainerMoneyTable"),
                            trainer_id)
        battle_struct = emu.read_u32(syms.addr("gBattleStruct"))
        multiplier = emu.read_u8(battle_struct + BATTLE_STRUCT_MONEY_MULTIPLIER)
        double = bool(self.driver.battle_type_flags() & BATTLE_TYPE_DOUBLE)
        info.update(name=self.game.charmap.decode(info.pop("raw_name")), multiplier=multiplier,
                    double=double, expected=trainer_reward(info["last_level"],
                                                           info["class_value"], multiplier,
                                                           double))
        return info

    def _trainer_battle(self) -> None:
        # gBattleStruct (moneyMultiplier) só fica pronto no início da batalha de fato: lê no
        # 1º menu de ação, antes de qualquer golpe
        self.driver.wait_action_menu()
        info = self._trainer_info()
        info["money_before"] = self.game.money()
        self.driver.move_policy = "best"
        info["outcome"] = self.driver.fight_to_end()
        info["money_after"] = self.game.money()
        info["level_after"] = self.game.party()[0].level
        self.measures.setdefault("trainers", []).append(info)
        self._after_battle(f"batalha contra {info['name']}")
