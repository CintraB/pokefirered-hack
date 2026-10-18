#!/usr/bin/env python3
"""Converte os encontros de grama/caverna por horário do HeartGold (pret/pokeheartgold,
files/fielddata/encountdata/gs_enc_data.json) em src/data/wild_encounters_time.json.

O arquivo tem a forma {"tables": [...]} (o jsonproc exige objeto na raiz).

Uso: python3 tools/hgss_encounters/convert.py --hgss <gs_enc_data.json> --repo . \
         --out src/data/wild_encounters_time.json

Só a versão FireRed e só os 35 mapas do mapeamento abaixo. O nível e a taxa continuam os do
FRLG; só a espécie muda. Espécie que exige evolução por nível acima do nível máximo do slot no
FRLG volta para a pré-evolução (Furret no slot nível 2-4 vira Sentret).
"""

import argparse
import json
import re
import sys
from pathlib import Path

LAND_SLOTS = 12
PERIODS = (("morn", "morning"), ("day", "day"), ("nite", "night"))
LEVEL_METHODS = {"EVO_LEVEL", "EVO_LEVEL_ATK_GT_DEF", "EVO_LEVEL_ATK_EQ_DEF",
                 "EVO_LEVEL_ATK_LT_DEF", "EVO_LEVEL_SILCOON", "EVO_LEVEL_CASCOON",
                 "EVO_LEVEL_NINJASK", "EVO_LEVEL_SHEDINJA"}
# Espécies da Gen 4 (inexistentes no FRLG) -> equivalente. Hoje nenhuma aparece nos 35 mapas.
GEN4_EQUIVALENTS: dict[str, str] = {}

# código do mapa no HGSS -> mapas do FRLG
MAP_TABLE: dict[str, tuple[str, ...]] = {
    **{f"R{n:02d}": (f"MAP_ROUTE{n}",) for n in (*range(1, 12), 13, 14, 15, 17, 18, 22, 24, 25)},
    "R16R0301": ("MAP_ROUTE16",),
    "W21": ("MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH"),
    "D46R0101": ("MAP_VIRIDIAN_FOREST",),
    "D02R0101": ("MAP_MT_MOON_1F",),
    "D02R0102": ("MAP_MT_MOON_B1F", "MAP_MT_MOON_B2F"),
    "D01R0101": ("MAP_DIGLETTS_CAVE_B1F",),
    "D05R0101": ("MAP_ROCK_TUNNEL_1F",),
    "D05R0102": ("MAP_ROCK_TUNNEL_B1F",),
    "D43R0101": ("MAP_VICTORY_ROAD_1F",),
    "D43R0102": ("MAP_VICTORY_ROAD_2F",),
    "D43R0103": ("MAP_VICTORY_ROAD_3F",),
    "D03R0101": ("MAP_CERULEAN_CAVE_1F",),
    "D03R0102": ("MAP_CERULEAN_CAVE_2F",),
    "D03R0103": ("MAP_CERULEAN_CAVE_B1F",),
}
FRLG_MAPS = tuple(m for maps in MAP_TABLE.values() for m in maps)

_EVO_ENTRY = re.compile(r"\{\s*(EVO_\w+)\s*,\s*(\w+)\s*,\s*(SPECIES_\w+)\s*\}")
_EVO_ROW = re.compile(r"\[(SPECIES_\w+)\]\s*=\s*\{(.*?)\}\s*\}\s*,", re.S)


def load_species(repo: Path) -> set[str]:
    text = (repo / "include/constants/species.h").read_text(encoding="utf-8")
    values = {m.group(1): m.group(2) for m in re.finditer(r"#define (SPECIES_\w+)\s+(\w+)", text)}

    def resolve(name: str, depth: int = 0) -> int:
        v = values[name]
        return int(v, 0) if re.fullmatch(r"(0x[0-9a-fA-F]+|\d+)", v) else resolve(v, depth + 1)

    limit = resolve("SPECIES_CHIMECHO")
    return {n for n in values if n != "SPECIES_NONE" and not n.startswith("SPECIES_OLD_UNOWN")
            and n not in ("SPECIES_EGG",) and re.fullmatch(r"SPECIES_\w+", n)
            and 0 < resolve(n) <= limit}


def load_evolutions(repo: Path) -> dict[str, list[tuple[str, str, str]]]:
    text = (repo / "src/data/pokemon/evolution.h").read_text(encoding="utf-8")
    text = re.sub(r"//[^\n]*", "", text)
    table = {}
    for m in _EVO_ROW.finditer(text):
        table[m.group(1)] = _EVO_ENTRY.findall(m.group(2) + "}")
    return table


def level_pre_evolution(species: str, evolutions) -> tuple[str, int] | None:
    """(pré-evolução, nível) se `species` vem de outra por método de nível."""
    for pre, entries in evolutions.items():
        for method, param, target in entries:
            if target == species and method in LEVEL_METHODS:
                return pre, int(param)
    return None


def adjust_species(species: str, max_level: int, evolutions) -> str:
    while True:
        pre = level_pre_evolution(species, evolutions)
        if pre is None or pre[1] <= max_level:
            return species
        species = pre[0]


def frlg_land_levels(repo: Path) -> dict[str, list[int]]:
    """mapa -> max_level dos 12 slots de terra da entrada FireRed, e a ordem do JSON."""
    data = json.loads((repo / "src/data/wild_encounters.json").read_text(encoding="utf-8"))
    out = {}
    for group in data["wild_encounter_groups"]:
        for enc in group["encounters"]:
            if "FireRed" in enc.get("base_label", "") and "land_mons" in enc:
                out[enc["map"]] = [m["max_level"] for m in enc["land_mons"]["mons"]]
    return out


def hgss_species(value) -> str:
    return value["HEARTGOLD"] if isinstance(value, dict) else value


def convert(hgss_path: Path, repo: Path) -> list[dict]:
    hgss = {e["map"]: e for e in json.loads(hgss_path.read_text(encoding="utf-8"))["encounters"]}
    valid = load_species(repo)
    evolutions = load_evolutions(repo)
    levels = frlg_land_levels(repo)

    missing_maps = [c for c in MAP_TABLE if c not in hgss]
    if missing_maps:
        sys.exit(f"mapas ausentes no HGSS: {missing_maps}")

    unknown = set()
    per_code: dict[str, dict[str, list[str]]] = {}
    for code in MAP_TABLE:
        mons = hgss[code]["land"]["mons"]
        if len(mons) != LAND_SLOTS:
            sys.exit(f"{code}: {len(mons)} slots de terra (esperado {LAND_SLOTS})")
        raw = {out_key: [hgss_species(m["species"][key]) for m in mons] for key, out_key in PERIODS}
        for key, species in raw.items():
            raw[key] = [GEN4_EQUIVALENTS.get(s, s) for s in species]
            unknown.update(s for s in raw[key] if s not in valid)
        per_code[code] = raw
    if unknown:
        sys.exit("espécies que não existem no FRLG (acrescente ao GEN4_EQUIVALENTS): "
                 + ", ".join(sorted(unknown)))

    result = []
    code_of = {m: c for c, maps in MAP_TABLE.items() for m in maps}
    for frlg_map in levels:                      # ordem do wild_encounters.json
        code = code_of.get(frlg_map)
        if code is None:
            continue
        max_levels = levels[frlg_map]
        entry = {"map": frlg_map, "source": f"HGSS {code} (HeartGold)"}
        for key, species in per_code[code].items():
            entry[key] = [adjust_species(s, max_levels[i], evolutions)
                          for i, s in enumerate(species)]
        result.append(entry)
    if len(result) != len(FRLG_MAPS):
        sys.exit(f"{len(result)} mapas gerados, esperado {len(FRLG_MAPS)}")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hgss", required=True, type=Path)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = convert(args.hgss, args.repo)
    args.out.write_text(json.dumps({"tables": result}, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result)} mapas -> {args.out}")


if __name__ == "__main__":
    main()
