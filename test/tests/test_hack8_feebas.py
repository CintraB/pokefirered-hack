"""Hack 8: Feebas pescável com a Super Vara na Ilha Quatro (sem emulador).

Decisão: o Milotic passa a ser obtível (Feebas segurando a Escama Prisma evolui ao subir de nível, Hack 7;
a Escama custa ¥7.000 na loja de Four Island). O Feebas ocupa um slot raro (<= 5%) da pesca de Super
Vara de `MAP_FOUR_ISLAND` (o mapa externo da ilha; as cavernas de gelo ficam de fora), com os níveis do
slot, no MESMO slot das tabelas `_FireRed` e `_LeafGreen` (senão a divisão 50% FR x LG do gen_swaps
trocaria o Feebas por um Slowpoke metade das vezes). A pesca não tem tabela por horário (Hack 7 só trocou
a grama).
"""

import importlib.util
import json
import re

from esteira.evolution_page import ARROW, SUFFIXES, evolution_line, load_item_names, load_species_names
from esteira.evolutions import load_evolution_table
from esteira.scenarios import REPO_ROOT

WILD_JSON = REPO_ROOT / "src" / "data" / "wild_encounters.json"
TIME_JSON = REPO_ROOT / "src" / "data" / "wild_encounters_time.json"
GEN_SCRIPT = REPO_ROOT / "tools" / "wild_leafgreen" / "gen_swaps.py"

MAPA = "FourIsland"
SLOT = 8                       # Super Vara = slots 5 a 9 (40/40/15/4/1)
NIVEL = (15, 25)
VERSOES = ("FireRed", "LeafGreen")

# Espécies da pesca de cada versão na base (8c031d48b): todas têm de continuar na tabela ou no mapa.
ANTES = {
    "FireRed": {"MAGIKARP", "POLIWAG", "GOLDEEN", "POLIWHIRL", "GYARADOS", "PSYDUCK"},
    "LeafGreen": {"MAGIKARP", "POLIWAG", "GOLDEEN", "POLIWHIRL", "GYARADOS", "SLOWPOKE"},
}


def _data():
    return json.loads(WILD_JSON.read_text(encoding="utf-8"))


def _tabela(mapa, versao):
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            if e["base_label"] == f"s{mapa}_{versao}":
                return e
    raise AssertionError(f"tabela s{mapa}_{versao} não existe")


def _chances(kind):
    return {f["type"]: f["encounter_rates"] for f in _data()["wild_encounter_groups"][0]["fields"]}[kind]


def _gerado():
    spec = importlib.util.spec_from_file_location("gen_swaps", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(WILD_JSON)


def test_feebas_no_slot_raro_da_super_vara_das_duas_versoes():
    for versao in VERSOES:
        mons = _tabela(MAPA, versao)["fishing_mons"]["mons"]
        assert mons[SLOT]["species"] == "SPECIES_FEEBAS", versao
        assert (mons[SLOT]["min_level"], mons[SLOT]["max_level"]) == NIVEL, versao
    assert SLOT >= 5, "Super Vara são os slots 5 a 9"
    assert 1 <= _chances("fishing_mons")[SLOT] <= 5


def test_feebas_so_uma_vez_e_so_no_mapa_externo_da_ilha_quatro():
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            achados = [(kind, i) for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons")
                       if kind in e for i, m in enumerate(e[kind]["mons"]) if m["species"] == "SPECIES_FEEBAS"]
            esperado = [("fishing_mons", SLOT)] if e["base_label"] in (f"s{MAPA}_FireRed", f"s{MAPA}_LeafGreen") else []
            assert achados == esperado, e["base_label"]


def test_feebas_fora_do_header_de_troca_50_50():
    texto = _gerado()
    assert "SPECIES_FEEBAS" not in texto
    assert not re.search(rf"&s{MAPA}_FireRed_FishingMonsInfo,\s*{SLOT},", texto), "slot do Feebas virou slot de troca"


def test_pesca_sem_tabela_por_horario():
    time = json.loads(TIME_JSON.read_text(encoding="utf-8"))
    assert not [t["map"] for t in time["tables"] if t["map"] == "MAP_FOUR_ISLAND"]


def test_nenhuma_especie_do_mapa_perdida():
    for versao, antes in ANTES.items():
        t = _tabela(MAPA, versao)
        depois = {m["species"].removeprefix("SPECIES_") for k in ("water_mons", "fishing_mons") for m in t[k]["mons"]}
        assert antes <= depois, (versao, antes - depois)


def test_milotic_pela_escama_prisma():
    tabela = load_evolution_table(REPO_ROOT)
    assert tabela["SPECIES_FEEBAS"] == [("EVO_LEVEL_UP_HOLD_ITEM", "ITEM_PRISM_SCALE", "SPECIES_MILOTIC")]
    pokemon_c = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")
    normal = pokemon_c[pokemon_c.index("case EVO_MODE_NORMAL:"):pokemon_c.index("case EVO_MODE_TRADE:")]
    caso = normal[normal.index("case EVO_LEVEL_UP_HOLD_ITEM:"):]
    caso = caso[:caso.index("break;")]
    assert "param == heldItem" in caso and "SetMonData" not in caso   # qualquer nível; a Escama fica
    # a Escama está à venda na Ilha Quatro por ¥7.000
    mart = (REPO_ROOT / "data/maps/FourIsland_Mart/scripts.inc").read_text(encoding="utf-8")
    assert "ITEM_PRISM_SCALE" in mart
    itens = json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]
    escama = next(i for i in itens if i.get("english") == "Escama Prisma")
    assert escama["price"] == 7000


def test_pagina_evolucao_do_feebas_descreve_a_evolucao_real():
    nomes, itens = load_species_names(REPO_ROOT), load_item_names(REPO_ROOT)
    ((metodo, param, alvo),) = load_evolution_table(REPO_ROOT)["SPECIES_FEEBAS"]
    linha = evolution_line(metodo, param, alvo, nomes, itens)
    assert linha == f"Subir nível + Escama Prisma {ARROW} MILOTIC"
    assert metodo not in SUFFIXES                      # sem "(só R/S/E)" nem "(impossível)"
    strings_c = (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")
    assert 'gText_PokeSum_EvoLevelUpHoldItem[] = _("Subir nível + {STR_VAR_2} {RIGHT_ARROW_2} {STR_VAR_3}")' in strings_c
