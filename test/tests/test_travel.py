"""Viagem e prêmio de treinador sem emulador."""

import json
from pathlib import Path

from esteira.scenarios.travel import EDGES, find_path, trainer_reward

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_caminho_do_centro_de_viridian_ao_ginasio_passa_pela_floresta():
    path = find_path("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", "MAP_PEWTER_CITY_GYM")
    assert path == ["MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", "MAP_VIRIDIAN_CITY", "MAP_ROUTE2",
                    "MAP_ROUTE2_VIRIDIAN_FOREST_SOUTH_ENTRANCE", "MAP_VIRIDIAN_FOREST",
                    "MAP_ROUTE2_VIRIDIAN_FOREST_NORTH_ENTRANCE", "MAP_ROUTE2#N",
                    "MAP_PEWTER_CITY", "MAP_PEWTER_CITY_GYM"]
    assert find_path("MAP_PALLET_TOWN_RIVALS_HOUSE", "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F")[-2:] \
        == ["MAP_VIRIDIAN_CITY", "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F"]
    assert find_path("MAP_PEWTER_CITY", "MAP_PEWTER_CITY") == ["MAP_PEWTER_CITY"]


def test_toda_aresta_tem_volta_e_os_mapas_existem():
    groups = json.loads((REPO_ROOT / "data" / "maps" / "map_groups.json").read_text("utf-8"))
    ids = {json.loads((REPO_ROOT / "data" / "maps" / m / "map.json").read_text("utf-8"))["id"]
           for g in groups["group_order"] for m in groups[g]}
    for a, b in EDGES:
        assert (b, a) in EDGES, f"sem volta de {b} para {a}"
        assert a.split("#")[0] in ids and b.split("#")[0] in ids


def test_premio_do_treinador_segue_cmd_getmoneyreward():
    # Bug Catcher (3) com último Pokémon nv9: 4 * 9 * 1 * 3
    assert trainer_reward(9, 3, 1, False) == 108
    # Brock (líder, 25), Onix nv14: 1400; Amulet Coin dobra; batalha dupla dobra
    assert trainer_reward(14, 25, 1, False) == 1400
    assert trainer_reward(14, 25, 2, True) == 5600


def test_read_trainer_le_o_nivel_do_ultimo_pokemon_no_rom():
    """Contra o ROM compilado: structs TrainerMon* alinhadas pelo agbcc (8 e 16 bytes)."""
    import pytest

    from esteira.symbols import Symbols
    from esteira.scenarios.travel import read_trainer

    rom_path, elf = REPO_ROOT / "pokefirered_switch.gba", REPO_ROOT / "pokefirered_switch.elf"
    if not rom_path.is_file() or not elf.is_file():
        pytest.skip("ROM/ELF da Switch não compilados")
    rom = rom_path.read_bytes()
    syms = Symbols.from_elf(str(elf))

    def read(addr, n):
        return rom[addr - 0x08000000:addr - 0x08000000 + n]

    def info(trainer_id):
        return read_trainer(read, syms.addr("gTrainers"), syms.addr("gTrainerMoneyTable"),
                            trainer_id)

    # include/constants/opponents.h e src/data/trainer_parties.h
    sammy, liam, brock = info(104), info(142), info(414)
    assert (sammy["last_level"], sammy["class_value"]) == (9, 3)      # Weedle nv9, Bug Catcher
    assert (liam["last_level"], liam["class_value"]) == (11, 5)       # Sandshrew nv11, Camper
    assert (brock["last_level"], brock["class_value"]) == (14, 25)    # Onix nv14, Leader
