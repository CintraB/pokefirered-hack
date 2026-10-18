"""Hack 7 sem emulador: encontros de grama e caverna por horário (HeartGold).

Confere o JSON gerado (src/data/wild_encounters_time.json) contra o FRLG (mapas, espécies,
regra de nível), o conversor (reproduz o arquivo quando a fonte do pret está à mão) e o C
(`GetTimeOfDayLandSpecies` só no ramo LAND, `IsSpeciesOnMap` olha a tabela).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from esteira import encontros as en
from esteira.evolutions import load_evolution_table
from esteira.scenarios import REPO_ROOT

TABLES = en.load_time_tables(REPO_ROOT)
FRLG = en.load_frlg_land(REPO_ROOT)
SPECIES_H = (REPO_ROOT / "include" / "constants" / "species.h").read_text(encoding="utf-8")
WILD_C = (REPO_ROOT / "src" / "wild_encounter.c").read_text(encoding="utf-8")
AREA_C = (REPO_ROOT / "src" / "wild_pokemon_area.c").read_text(encoding="utf-8")
WILD_H = (REPO_ROOT / "include" / "wild_encounter.h").read_text(encoding="utf-8")
LEVEL_METHODS = {"EVO_LEVEL", "EVO_LEVEL_ATK_GT_DEF", "EVO_LEVEL_ATK_EQ_DEF",
                 "EVO_LEVEL_ATK_LT_DEF", "EVO_LEVEL_SILCOON", "EVO_LEVEL_CASCOON",
                 "EVO_LEVEL_NINJASK", "EVO_LEVEL_SHEDINJA"}


def _species_values() -> dict[str, int]:
    raw = {m.group(1): m.group(2) for m in re.finditer(r"#define (SPECIES_\w+)\s+(\w+)", SPECIES_H)}
    out: dict[str, int] = {}

    def value(name: str) -> int:
        if name not in out:
            v = raw[name]
            out[name] = int(v, 0) if re.fullmatch(r"0x[0-9a-fA-F]+|\d+", v) else value(v)
        return out[name]

    for name in raw:
        value(name)
    return out


def _function_body(text: str, signature: str) -> str:
    # a definição (a `{` vem logo depois do `)`), não o protótipo
    start = re.search(re.escape(signature) + r"[^;{]*\)\s*\{", text).start()
    brace = text.index("{", start)
    depth, i = 0, brace
    while True:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return text[brace:i + 1]
        i += 1


def test_35_mapas_esperados():
    maps = [t["map"] for t in TABLES]
    assert len(maps) == len(set(maps)) == 35
    assert set(maps) == en.EXPECTED_MAPS


def test_cada_mapa_tem_land_no_frlg():
    faltam = [t["map"] for t in TABLES if t["map"] not in FRLG]
    assert not faltam, f"sem land_mons FireRed em wild_encounters.json: {faltam}"
    for t in TABLES:
        assert len(FRLG[t["map"]]) == en.LAND_SLOTS, t["map"]


def test_ordem_do_json_e_a_do_wild_encounters():
    order = [m for m in FRLG if m in en.EXPECTED_MAPS]
    assert [t["map"] for t in TABLES] == order


def test_especies_validas():
    values = _species_values()
    chimecho = values["SPECIES_CHIMECHO"]
    for t in TABLES:
        for key in en.PERIOD_KEYS:
            species = t[key]
            assert len(species) == en.LAND_SLOTS, (t["map"], key)
            for s in species:
                assert s in values, (t["map"], key, s)
                assert 0 < values[s] <= chimecho, (t["map"], key, s)
                assert "OLD_UNOWN" not in s, (t["map"], key, s)


def test_regra_de_nivel():
    evo = load_evolution_table(REPO_ROOT)
    pre_of: dict[str, list[tuple[str, int]]] = {}
    for pre, entries in evo.items():
        for method, param, target in entries:
            if method in LEVEL_METHODS:
                pre_of.setdefault(target, []).append((pre, int(param)))
    for t in TABLES:
        for key in en.PERIOD_KEYS:
            for slot, s in enumerate(t[key]):
                max_level = FRLG[t["map"]][slot]["max_level"]
                for pre, level in pre_of.get(s, []):
                    assert level <= max_level, (
                        f"{t['map']} {key} slot {slot}: {s} evolui de {pre} no nível {level}, "
                        f"acima do máximo {max_level} do slot")


def test_regra_de_nivel_troca_pela_pre_evolucao():
    """O Furret do HGSS no slot baixo da Rota 1 vira Sentret."""
    route1 = next(t for t in TABLES if t["map"] == "MAP_ROUTE1")
    assert "SPECIES_FURRET" not in route1["morning"]
    assert "SPECIES_SENTRET" in route1["morning"]


def test_rota1_noite():
    route1 = next(t for t in TABLES if t["map"] == "MAP_ROUTE1")
    assert "SPECIES_HOOTHOOT" in route1["night"]
    assert "SPECIES_HOOTHOOT" not in route1["morning"]
    assert "SPECIES_HOOTHOOT" not in route1["day"]


def test_conversor_reproduz(tmp_path):
    hgss = os.environ.get("HGSS_ENC_DATA")
    if not hgss or not Path(hgss).is_file():
        pytest.skip("HGSS_ENC_DATA não aponta para o gs_enc_data.json do pret/pokeheartgold")
    out = tmp_path / "wild_encounters_time.json"
    script = REPO_ROOT / "tools" / "hgss_encounters" / "convert.py"
    subprocess.run([sys.executable, "-I", str(script), "--hgss", hgss, "--repo", str(REPO_ROOT),
                    "--out", str(out)], check=True)
    assert out.read_text(encoding="utf-8") == (REPO_ROOT / en.TIME_TABLE).read_text(encoding="utf-8")


def test_c_usa_tabela():
    assert "struct WildMonTimeTable" in WILD_H
    assert "u16 species[3][LAND_WILD_COUNT]" in WILD_H
    assert "extern const struct WildMonTimeTable gWildMonTimeTables[];" in WILD_H
    assert '#include "data/wild_encounters_time.h"' in WILD_C
    body = _function_body(WILD_C, "static bool8 TryGenerateWildMon(")
    assert body.count("GetTimeOfDayLandSpecies(") == 1
    assert "DayNight_GetPeriod()" in body
    # só no ramo de terra: água e pedras seguem direto da tabela do FRLG
    assert re.search(r"if \(area == WILD_AREA_LAND\)\s*\n?\s*\w+ = GetTimeOfDayLandSpecies\(", body)
    body = _function_body(AREA_C, "static bool32 IsSpeciesOnMap(")
    assert "IsSpeciesInTimeTables(" in body
    assert "gWildMonTimeTables" in _function_body(AREA_C, "static bool32 IsSpeciesInTimeTables(")


def test_makefile_gera_o_header():
    rules = (REPO_ROOT / "json_data_rules.mk").read_text(encoding="utf-8")
    assert "wild_encounters_time.h" in rules
    assert "wild_encounters_time.json.txt" in rules
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "src/data/wild_encounters_time.h" in gitignore
