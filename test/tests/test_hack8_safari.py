"""Hack 8: os 3 iniciais de Kanto como selvagens raros na Zona Safári (sem emulador).

Decisão do dono (24/10): Bulbasaur no mato do Leste, Charmander no mato do Norte, Squirtle
surfando no Oeste. Cada um ocupa um slot raro (1% a 5%) com os níveis do slot, no MESMO slot das
tabelas `_FireRed` e `_LeafGreen` (senão a divisão 50% FR x LG do gen_swaps trocaria o inicial por
uma espécie exclusiva do LG metade das vezes). O Safári não tem tabela por horário (Hack 7).
"""

import importlib.util
import json
import re

from esteira.scenarios import REPO_ROOT

WILD_JSON = REPO_ROOT / "src" / "data" / "wild_encounters.json"
TIME_JSON = REPO_ROOT / "src" / "data" / "wild_encounters_time.json"
GEN_SCRIPT = REPO_ROOT / "tools" / "wild_leafgreen" / "gen_swaps.py"

# (mapa, tipo de tabela, slot, espécie, nível mín, nível máx, espécie que o slot tinha antes)
INICIAIS = {
    "BULBASAUR": ("SafariZoneEast", "land_mons", 8, "SPECIES_BULBASAUR", 22, 22, "SPECIES_PARAS"),
    "CHARMANDER": ("SafariZoneNorth", "land_mons", 8, "SPECIES_CHARMANDER", 23, 23, "SPECIES_PARAS"),
    "SQUIRTLE": ("SafariZoneWest", "water_mons", 3, "SPECIES_SQUIRTLE", 30, 35, "SPECIES_PSYDUCK"),
}
VERSOES = ("FireRed", "LeafGreen")
AREAS = ("SafariZoneCenter", "SafariZoneEast", "SafariZoneNorth", "SafariZoneWest")

# Espécies de cada tabela do Safári na base (3ec4cf8c5), por (mapa, tipo): todas têm de continuar.
ANTES = {
    ("SafariZoneEast", "land_mons", "FireRed"): {"NIDORAN_M", "DODUO", "EXEGGCUTE", "PARAS", "NIDORINO",
                                                "NIDORAN_F", "PARASECT", "KANGASKHAN", "SCYTHER"},
    ("SafariZoneEast", "land_mons", "LeafGreen"): {"NIDORAN_F", "DODUO", "EXEGGCUTE", "PARAS", "NIDORINA",
                                                  "NIDORAN_M", "PARASECT", "KANGASKHAN", "PINSIR"},
    ("SafariZoneNorth", "land_mons", "FireRed"): {"RHYHORN", "NIDORAN_M", "EXEGGCUTE", "PARAS", "NIDORINO",
                                                 "NIDORINA", "VENOMOTH", "CHANSEY", "TAUROS"},
    ("SafariZoneNorth", "land_mons", "LeafGreen"): {"RHYHORN", "NIDORAN_F", "EXEGGCUTE", "PARAS", "NIDORINA",
                                                   "NIDORINO", "VENOMOTH", "CHANSEY", "TAUROS"},
    ("SafariZoneWest", "water_mons", "FireRed"): {"PSYDUCK"},
    ("SafariZoneWest", "water_mons", "LeafGreen"): {"SLOWPOKE"},
}


def _data():
    return json.loads(WILD_JSON.read_text(encoding="utf-8"))


def _tabela(mapa, versao):
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            if e["base_label"] == f"s{mapa}_{versao}":
                return e
    raise AssertionError(f"tabela s{mapa}_{versao} não existe")


def _chance(kind, slot):
    return {f["type"]: f["encounter_rates"] for f in _data()["wild_encounter_groups"][0]["fields"]}[kind][slot]


def _gerado():
    spec = importlib.util.spec_from_file_location("gen_swaps", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(WILD_JSON)


def test_cada_inicial_no_slot_raro_das_duas_versoes():
    for nome, (mapa, kind, slot, especie, lo, hi, _) in INICIAIS.items():
        for versao in VERSOES:
            mon = _tabela(mapa, versao)[kind]["mons"][slot]
            assert mon["species"] == especie, (nome, versao)
            assert (mon["min_level"], mon["max_level"]) == (lo, hi), (nome, versao)
        assert 1 <= _chance(kind, slot) <= 5, nome


def test_inicial_so_na_area_certa():
    donos = {nome: (v[0], v[1]) for nome, v in INICIAIS.items()}
    for mapa in AREAS:
        for versao in VERSOES:
            tabela = _tabela(mapa, versao)
            for kind in ("land_mons", "water_mons"):
                especies = [m["species"] for m in tabela[kind]["mons"]]
                for nome, (v, k) in donos.items():
                    esperado = 1 if (mapa, kind) == (v, k) else 0
                    assert especies.count(f"SPECIES_{nome}") == esperado, (mapa, versao, kind, nome)


def test_inicial_fora_do_header_de_troca_50_50():
    texto = _gerado()
    for nome, (mapa, kind, slot, *_) in INICIAIS.items():
        assert f"SPECIES_{nome}" not in texto, nome
        simbolo = f"s{mapa}_FireRed_{'LandMonsInfo' if kind == 'land_mons' else 'WaterMonsInfo'}"
        assert not re.search(rf"&{simbolo},\s*{slot},", texto), (nome, "slot do inicial virou slot de troca")


def test_safari_sem_tabela_por_horario():
    time = json.loads(TIME_JSON.read_text(encoding="utf-8"))
    assert not [t["map"] for t in time["tables"] if "SAFARI" in t["map"]]


def test_nenhuma_especie_do_safari_perdida():
    for (mapa, kind, versao), antes in ANTES.items():
        depois = {m["species"].removeprefix("SPECIES_") for m in _tabela(mapa, versao)[kind]["mons"]}
        assert antes <= depois, (mapa, kind, versao, antes - depois)


