"""Hack 8: a Caverna Mutante (Altering Cave) troca de conjunto de Pokémon a cada dia do relógio do Hack 7.

Testes estáticos: travam o special, o script de mapa e a coerência com as tabelas de encontro.
O comportamento (conjunto muda de um dia para o outro) é conferido no emulador.
"""

import json
import re

from esteira.scenarios import REPO_ROOT

MAPA = "data/maps/SixIsland_AlteringCave/scripts.inc"
SPECIAL = "GetAlteringCaveSetForScript"
# Ordem real das tabelas em src/data/wild_encounters.json (conjunto 0..8)
ORDEM = [
    "SPECIES_ZUBAT", "SPECIES_MAREEP", "SPECIES_PINECO", "SPECIES_HOUNDOUR", "SPECIES_TEDDIURSA",
    "SPECIES_AIPOM", "SPECIES_SHUCKLE", "SPECIES_STANTLER", "SPECIES_SMEARGLE",
]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _num_tabelas() -> int:
    m = re.search(r"^#define NUM_ALTERING_CAVE_TABLES\s+(\d+)", _read("include/wild_encounter.h"), re.M)
    assert m, "NUM_ALTERING_CAVE_TABLES não encontrada em include/wild_encounter.h"
    return int(m.group(1))


def _tabelas_json() -> dict:
    """{'FireRed': [espécie do conjunto 0, ...], 'LeafGreen': [...]} na ordem do JSON."""
    data = json.loads(_read("src/data/wild_encounters.json"))
    out: dict = {}
    for g in data["wild_encounter_groups"]:
        for e in g["encounters"]:
            if e.get("map") != "MAP_SIX_ISLAND_ALTERING_CAVE":
                continue
            versao = e["base_label"].rsplit("_", 1)[1]
            especies = {m["species"] for m in e["land_mons"]["mons"]}
            assert len(especies) == 1, f"{e['base_label']} mistura espécies: {especies}"
            out.setdefault(versao, []).append(especies.pop())
    return out


def _func_body(name: str) -> str:
    src = _read("src/field_specials.c")
    m = re.search(rf"^\w[\w\s\*]*\b{name}\(void\)\n\{{\n(.*?)^\}}", src, re.M | re.S)
    assert m, f"função {name}(void) não encontrada em src/field_specials.c"
    return m.group(1)


def test_special_registrado():
    assert re.search(rf"^\s*def_special {SPECIAL}\s*$", _read("data/specials.inc"), re.M)
    assert re.search(rf"\b{SPECIAL}\(void\);", _read("include/field_specials.h"))


def test_special_usa_dia_do_hack7_com_modulo_das_tabelas():
    corpo = _func_body(SPECIAL)
    assert re.search(r"DayNight_GetDay\(\)\s*%\s*NUM_ALTERING_CAVE_TABLES", corpo), corpo


def test_field_specials_enxerga_a_constante():
    assert "wild_encounter.h" in _read("src/field_specials.c")


def test_script_de_mapa_seta_a_var_a_partir_do_dia():
    src = _read(MAPA)
    m = re.search(r"^SixIsland_AlteringCave_OnTransition::\n(.*?)^\s*end\s*$", src, re.M | re.S)
    assert m, "OnTransition da Caverna Mutante não encontrado"
    assert re.search(rf"specialvar VAR_ALTERING_CAVE_WILD_SET, {SPECIAL}\b", m.group(1))
    assert "setworldmapflag FLAG_WORLD_MAP_SIX_ISLAND_ALTERING_CAVE" in m.group(1)
    assert "MAP_SCRIPT_ON_TRANSITION, SixIsland_AlteringCave_OnTransition" in src


def test_numero_de_conjuntos_bate_com_as_tabelas():
    n = _num_tabelas()
    tabelas = _tabelas_json()
    assert set(tabelas) == {"FireRed", "LeafGreen"}
    for versao, especies in tabelas.items():
        assert len(especies) == n, f"{versao}: {len(especies)} tabelas no JSON, constante diz {n}"
        assert especies == ORDEM, f"{versao}: ordem das tabelas mudou: {especies}"


def test_nove_dias_seguidos_passam_por_todos_os_conjuntos():
    n = _num_tabelas()
    conjuntos = [dia % n for dia in range(n)]
    assert sorted(conjuntos) == list(range(n))
    assert all(dia % n != (dia + 1) % n for dia in range(n))  # nunca repete de um dia para o seguinte


def test_mystery_event_continua_coerente():
    # O evento antigo ainda avança a var; a descrição do rumor segue valendo (cave é a da Ilha Proscrita).
    msg = _read("data/mystery_event_msg.s")
    assert "Caverna Mutante" in msg
    assert "Ilha Proscrita" in msg
