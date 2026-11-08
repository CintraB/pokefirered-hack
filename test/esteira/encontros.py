"""Hack 7: encontros de grama e caverna por horário (HeartGold), só leitura de fonte.

`src/data/wild_encounters_time.json` é gerado por `tools/hgss_encounters/convert.py` a partir
do `gs_enc_data.json` do pret/pokeheartgold (não versionado). Para cada um dos 35 mapas do
FRLG com tabela (mais 2 do POK-28, escritos à mão: Prado da Ilha Cinco e Cânion Sevault), dá as 12
espécies de grama da manhã, da tarde e da noite; nível e taxa continuam os do FRLG
(`wild_encounters.json`). No jogo, `GetTimeOfDayLandSpecies` (src/wild_encounter.c) escolhe a tabela pelo período; o entardecer sorteia entre tarde e noite.
"""

import json
from pathlib import Path

LAND_SLOTS = 12
TIME_TABLE = Path("src/data/wild_encounters_time.json")
WILD_JSON = Path("src/data/wild_encounters.json")
PERIOD_KEYS = ("morning", "day", "night")     # índice 0, 1, 2 de WildMonTimeTable.species

# Os 35 mapas do FRLG (FireRed) que ganham tabela por horário pelo HeartGold, mais os 2 do POK-28
# (MANUAIS: sem fonte no HGSS). Rota 12, Rota 23, Seafoam, Torre Pokémon, Mansão, Usina, Safari e as
# outras Sevii ficam sem tabela.
MANUAIS = frozenset(["MAP_FIVE_ISLAND_MEADOW", "MAP_SEVEN_ISLAND_SEVAULT_CANYON"])
EXPECTED_MAPS = frozenset(
    list(MANUAIS) + [f"MAP_ROUTE{n}" for n in (*range(1, 12), 13, 14, 15, 16, 17, 18, 22, 24, 25)]
    + ["MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH", "MAP_VIRIDIAN_FOREST", "MAP_MT_MOON_1F",
       "MAP_MT_MOON_B1F", "MAP_MT_MOON_B2F", "MAP_DIGLETTS_CAVE_B1F", "MAP_ROCK_TUNNEL_1F",
       "MAP_ROCK_TUNNEL_B1F", "MAP_VICTORY_ROAD_1F", "MAP_VICTORY_ROAD_2F",
       "MAP_VICTORY_ROAD_3F", "MAP_CERULEAN_CAVE_1F", "MAP_CERULEAN_CAVE_2F",
       "MAP_CERULEAN_CAVE_B1F"])
NO_TABLE_MAP = "MAP_ROUTE12"      # tem grama no FRLG e nenhuma tabela por horário


def load_time_tables(repo: Path) -> list[dict]:
    return json.loads((repo / TIME_TABLE).read_text(encoding="utf-8"))["tables"]


def load_frlg_land(repo: Path) -> dict[str, list[dict]]:
    """mapa -> 12 slots (`min_level`, `max_level`, `species`) de terra da entrada FireRed."""
    data = json.loads((repo / WILD_JSON).read_text(encoding="utf-8"))
    out: dict[str, list[dict]] = {}
    for group in data["wild_encounter_groups"]:
        for enc in group["encounters"]:
            if "FireRed" in enc.get("base_label", "") and "land_mons" in enc:
                out[enc["map"]] = enc["land_mons"]["mons"]
    return out
