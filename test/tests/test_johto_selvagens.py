"""POK-28, Task 2: Chinchou, Lanturn, Corsola, Miltank, Girafarig e Gligar na natureza (sem emulador).

Decisões (cada slot trocado só toma o lugar de uma espécie que continua com outra fonte; FR e LG recebem
a MESMA espécie e os MESMOS níveis, para o slot não virar troca LG 50/50 do gen_swaps):

| Pokémon  | Onde                                              | Slot            | Antes (FR / LG)                  |
|----------|---------------------------------------------------|-----------------|----------------------------------|
| Chinchou | Super Vara das Rotas 19, 20, 21N e 21S, nv 25-35  | pesca 7 (15%)   | Gyarados 15-25                   |
| Lanturn  | idem, nv 35-40                                    | pesca 8 (4%)    | Seadra 25-35 / Kingler 25-35     |
| Corsola  | surf do Resort Gorgeous, nv 30-35                 | água 1 (30%)    | Hoppip 5-15                      |
| Miltank  | grama do Prado (Ilha Cinco), manhã e tarde        | grama 5 (10%)   | Meowth 41 (nível passa a 30-35)  |
| Girafarig| Safari Oeste (grama), nv 25-30                    | grama 8 (4%)    | Venonat 23                       |
| Gligar   | grama do Cânion Sevault à noite, nv 35-40         | grama 5 (10%)   | Meowth 43 (nível passa a 35-40)  |

Miltank e Gligar entram pela tabela por horário (Hack 7), que só troca a espécie: o nível é o do slot do
FireRed, por isso o slot do Meowth muda de nível no JSON (nas duas versões) e o Meowth continua nos outros
períodos.
"""

import importlib.util
import json

import pytest

from esteira.dex_fontes import fontes_selvagens
from esteira.scenarios import REPO_ROOT, full_johto as johto

WILD_JSON = REPO_ROOT / "src" / "data" / "wild_encounters.json"
TIME_JSON = REPO_ROOT / "src" / "data" / "wild_encounters_time.json"
GEN_SCRIPT = REPO_ROOT / "tools" / "wild_leafgreen" / "gen_swaps.py"
GERAR = REPO_ROOT / "tools" / "dexnav" / "gerar.py"
DEXNAV_MAPAS = REPO_ROOT / "src" / "data" / "dexnav_mapas.h"

VERSOES = ("FireRed", "LeafGreen")
ROTAS_PESCA = ("Route19", "Route20", "Route21North", "Route21South")
MAPAS_NOVOS_NA_TABELA = ("MAP_FIVE_ISLAND_MEADOW", "MAP_SEVEN_ISLAND_SEVAULT_CANYON")

# o que cada slot tinha antes (base 649fb6f61): (tabela, tipo, slot, {versão: (espécie, mín, máx)})
ANTES = {
    "Route19": [("fishing_mons", 7, {"FireRed": ("GYARADOS", 15, 25), "LeafGreen": ("GYARADOS", 15, 25)}),
                ("fishing_mons", 8, {"FireRed": ("SEADRA", 25, 35), "LeafGreen": ("KINGLER", 25, 35)})],
    "FiveIslandResortGorgeous": [("water_mons", 1, {v: ("HOPPIP", 5, 15) for v in VERSOES})],
    "FiveIslandMeadow": [("land_mons", 5, {v: ("MEOWTH", 41, 41) for v in VERSOES})],
    "SevenIslandSevaultCanyon": [("land_mons", 5, {v: ("MEOWTH", 43, 43) for v in VERSOES})],
    "SafariZoneWest": [("land_mons", 8, {v: ("VENONAT", 23, 23) for v in VERSOES})],
}
# espécies que saíram de algum slot (o teste confere que todas continuam com fonte no jogo)
REMOVIDAS = ("GYARADOS", "SEADRA", "KINGLER", "HOPPIP", "VENONAT")


def _data():
    return json.loads(WILD_JSON.read_text(encoding="utf-8"))


def _tabela(mapa, versao):
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            if e["base_label"] == f"s{mapa}_{versao}":
                return e
    raise AssertionError(f"tabela s{mapa}_{versao} não existe")


def _slot(mapa, versao, kind, slot):
    m = _tabela(mapa, versao)[kind]["mons"][slot]
    return m["species"].removeprefix("SPECIES_"), m["min_level"], m["max_level"]


def _chance(kind, slot):
    return {f["type"]: f["encounter_rates"] for f in _data()["wild_encounter_groups"][0]["fields"]}[kind][slot]


def _horario():
    return {t["map"]: t for t in json.loads(TIME_JSON.read_text(encoding="utf-8"))["tables"]}


def _modulo(caminho, nome):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def gerar():
    return _modulo(GERAR, "dexnav_gerar_johto")


def _especies(mapa, versao, kind):
    return [m["species"].removeprefix("SPECIES_") for m in _tabela(mapa, versao)[kind]["mons"]]


# --- Chinchou e Lanturn ---------------------------------------------------------------------------------------------

def test_chinchou_super_vara():
    for rota in ROTAS_PESCA:
        for versao in VERSOES:
            assert _slot(rota, versao, "fishing_mons", 7) == ("CHINCHOU", 25, 35), (rota, versao)
    # slot 7 é da Super Vara (slots 5 a 9) e vale 15%
    campos = _data()["wild_encounter_groups"][0]["fields"]
    pesca = next(f for f in campos if f["type"] == "fishing_mons")
    assert 7 in pesca["groups"]["super_rod"]
    assert 7 not in pesca["groups"]["old_rod"] + pesca["groups"]["good_rod"]
    assert _chance("fishing_mons", 7) == 15


def test_lanturn_raro():
    for rota in ROTAS_PESCA:
        for versao in VERSOES:
            assert _slot(rota, versao, "fishing_mons", 8) == ("LANTURN", 35, 40), (rota, versao)
    assert _chance("fishing_mons", 8) == 4


def test_chinchou_e_lanturn_so_nas_quatro_rotas():
    mapas = {"MAP_ROUTE19", "MAP_ROUTE20", "MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH"}
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                if kind not in e or (kind == "fishing_mons" and e["map"] in mapas):
                    continue
                especies = {m["species"] for m in e[kind]["mons"]}
                assert not especies & {"SPECIES_CHINCHOU", "SPECIES_LANTURN"}, (e["base_label"], kind)


# --- Corsola --------------------------------------------------------------------------------------------------------

def test_corsola_surf_gorgeous():
    for versao in VERSOES:
        assert _slot("FiveIslandResortGorgeous", versao, "water_mons", 1) == ("CORSOLA", 30, 35), versao
        assert "CORSOLA" not in _especies("FiveIslandResortGorgeous", versao, "fishing_mons")
        assert "land_mons" not in _tabela("FiveIslandResortGorgeous", versao)
    assert _chance("water_mons", 1) == 30
    # só no Resort Gorgeous: nenhuma outra tabela do jogo tem Corsola
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                if kind in e and "SPECIES_CORSOLA" in {m["species"] for m in e[kind]["mons"]}:
                    assert e["map"] == "MAP_FIVE_ISLAND_RESORT_GORGEOUS" and kind == "water_mons", e["base_label"]


# --- Miltank --------------------------------------------------------------------------------------------------------

def test_miltank_so_de_dia():
    t = _horario()["MAP_FIVE_ISLAND_MEADOW"]
    assert t["morning"][5] == t["day"][5] == "SPECIES_MILTANK"
    assert "SPECIES_MILTANK" not in t["night"]
    assert t["night"][5] == "SPECIES_MEOWTH"
    # nível do slot (a tabela por horário só troca a espécie): 30-35 nas duas versões, 10%
    for versao in VERSOES:
        assert _slot("FiveIslandMeadow", versao, "land_mons", 5) == ("MEOWTH", 30, 35), versao
    assert _chance("land_mons", 5) == 10
    # Miltank não está em nenhuma tabela base (só pelo horário) e só no Prado
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                if kind in e:
                    assert "SPECIES_MILTANK" not in {m["species"] for m in e[kind]["mons"]}, e["base_label"]
    outras = [m for m, x in _horario().items() if m != "MAP_FIVE_ISLAND_MEADOW"
              and "SPECIES_MILTANK" in x["morning"] + x["day"] + x["night"]]
    assert not outras


def test_prado_so_muda_o_miltank():
    """As tabelas novas copiam a grama do FireRed; só o slot do Miltank (manhã/tarde) e do Gligar (noite) mudam."""
    for mapa, rotulo, slot, periodos in (("MAP_FIVE_ISLAND_MEADOW", "FiveIslandMeadow", 5, ("morning", "day")),
                                         ("MAP_SEVEN_ISLAND_SEVAULT_CANYON", "SevenIslandSevaultCanyon", 5, ("night",))):
        t = _horario()[mapa]
        base = [f"SPECIES_{s}" for s in _especies(rotulo, "FireRed", "land_mons")]
        for p in ("morning", "day", "night"):
            esperado = list(base)
            if p in periodos:
                esperado[slot] = "SPECIES_MILTANK" if "MEADOW" in mapa else "SPECIES_GLIGAR"
            assert t[p] == esperado, (mapa, p)


# --- Gligar ---------------------------------------------------------------------------------------------------------

def test_gligar_so_de_noite():
    t = _horario()["MAP_SEVEN_ISLAND_SEVAULT_CANYON"]
    assert t["night"][5] == "SPECIES_GLIGAR"
    assert "SPECIES_GLIGAR" not in t["morning"] + t["day"]
    assert t["day"][5] == t["morning"][5] == "SPECIES_MEOWTH"
    for versao in VERSOES:
        assert _slot("SevenIslandSevaultCanyon", versao, "land_mons", 5) == ("MEOWTH", 35, 40), versao
        assert "land_mons" in _tabela("SevenIslandSevaultCanyon", versao)
    assert _chance("land_mons", 5) == 10
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                if kind in e:
                    assert "SPECIES_GLIGAR" not in {m["species"] for m in e[kind]["mons"]}, e["base_label"]
    outras = [m for m, x in _horario().items() if m != "MAP_SEVEN_ISLAND_SEVAULT_CANYON"
              and "SPECIES_GLIGAR" in x["morning"] + x["day"] + x["night"]]
    assert not outras


def test_mapas_novos_na_tabela_por_horario():
    horario = _horario()
    for mapa in MAPAS_NOVOS_NA_TABELA:
        t = horario[mapa]
        for p in ("morning", "day", "night"):
            assert len(t[p]) == 12, (mapa, p)
        assert t["source"].startswith("POK-28"), mapa
    # a ordem do arquivo segue a do wild_encounters.json (o teste de Hack 7 confere o resto)
    ordem = [e["map"] for g in _data()["wild_encounter_groups"] for e in g["encounters"]
             if "FireRed" in e["base_label"] and e["map"] in horario]
    assert list(horario) == list(dict.fromkeys(ordem))


# --- Girafarig ------------------------------------------------------------------------------------------------------

def test_girafarig_safari():
    for versao in VERSOES:
        assert _slot("SafariZoneWest", versao, "land_mons", 8) == ("GIRAFARIG", 25, 30), versao
    assert _chance("land_mons", 8) == 4
    # a Zona Safári não tem tabela por horário e o Venonat continua na própria grama
    assert not [m for m in _horario() if "SAFARI" in m]
    for versao in VERSOES:
        assert _especies("SafariZoneWest", versao, "land_mons").count("VENONAT") == 2
    # Girafarig só no Safari Oeste
    for g in _data()["wild_encounter_groups"]:
        for e in g["encounters"]:
            for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
                if kind in e and "SPECIES_GIRAFARIG" in {m["species"] for m in e[kind]["mons"]}:
                    assert e["map"] == "MAP_SAFARI_ZONE_WEST" and kind == "land_mons", e["base_label"]


# --- sem troca LG nos slots novos e nada se perde ----------------------------------------------------------------------

def test_slots_novos_fora_do_header_de_troca_50_50():
    texto = _modulo(GEN_SCRIPT, "gen_swaps_johto").render(WILD_JSON)
    for especie in ("CHINCHOU", "LANTURN", "CORSOLA", "GIRAFARIG", "MILTANK", "GLIGAR"):
        assert f"SPECIES_{especie}" not in texto, especie
    # nenhum slot trocado vira troca: FR e LG são iguais em todos eles
    for mapa, trocas in ANTES.items():
        rotulos = ROTAS_PESCA if mapa == "Route19" else (mapa,)
        for rotulo in rotulos:
            for kind, slot, _ in trocas:
                assert _slot(rotulo, "FireRed", kind, slot) == _slot(rotulo, "LeafGreen", kind, slot), (rotulo, kind, slot)


def test_nenhuma_especie_perdida():
    """Toda espécie que saiu de um slot continua obtível por outra fonte selvagem (tabelas FireRed, metade LeafGreen
    dos slots trocados, grama por horário e evoluções): `esteira.dex_fontes`, a parte "natureza" do levantamento
    `contar_dex_atual.py`. E as 6 espécies novas passaram a ter fonte."""
    fontes = fontes_selvagens(REPO_ROOT)
    for especie in REMOVIDAS:
        assert f"SPECIES_{especie}" in fontes, f"{especie} saiu de um slot e não tem mais nenhuma fonte"
    for especie in ("CHINCHOU", "LANTURN", "CORSOLA", "MILTANK", "GIRAFARIG", "GLIGAR"):
        assert f"SPECIES_{especie}" in fontes, especie


def test_removidas_seguem_em_alguma_tabela_selvagem():
    """Mais estrito que o anterior: as removidas ainda estão numa tabela (FR ou LG que vira troca), não só por evolução."""
    fontes = fontes_selvagens(REPO_ROOT)
    for especie in REMOVIDAS:
        motivos = fontes[f"SPECIES_{especie}"]
        assert any(m.startswith(("selvagem", "grama por horário", "metade LeafGreen")) for m in motivos), (especie, motivos)


# --- cenário `johto`: sem vermelho estatístico ----------------------------------------------------------------------

def test_cenario_johto_falso_vermelho_abaixo_de_1e_6():
    """Cada conferência por sorteio do cenário (`AMOSTRAS`) tem chance de falso vermelho < 1e-6: nenhum acerto em n
    sorteios (ou menos que o mínimo) e as faixas de porcentagem de Chinchou e Corsola."""
    for chave, (p, n, minimo) in johto.AMOSTRAS.items():
        assert johto.p_menos_de(minimo, p, n) < johto.FALSO_VERMELHO_MAX, (chave, johto.p_menos_de(minimo, p, n))
        if minimo == 1:
            assert johto.p_nenhum(p, n) == pytest.approx(johto.p_menos_de(1, p, n))
    assert johto.p_fora_da_faixa() < johto.FALSO_VERMELHO_MAX
    # a faixa ainda distingue a chance certa de uma errada: Chinchou 15% não passa por 4% nem por 40%
    for chave in ("chinchou", "corsola"):
        p, n, _ = johto.AMOSTRAS[chave]
        tol = johto.tolerancia_pp(p, n)
        assert tol < 100 * p / 1.5, (chave, tol)
    # o entardecer é meio a meio (5%), não os 10% do resto do dia
    assert johto.AMOSTRAS["miltank_entardecer"][0] == johto.AMOSTRAS["miltank_dia"][0] / 2
    assert johto.AMOSTRAS["gligar_entardecer"][0] == johto.AMOSTRAS["gligar_noite"][0] / 2


def test_amostras_batem_com_as_chances_do_json():
    """As chances das `AMOSTRAS` são as dos slots (campos do JSON), não números soltos."""
    campos = {f["type"]: f["encounter_rates"] for f in _data()["wild_encounter_groups"][0]["fields"]}
    esperado = {"miltank_dia": campos["land_mons"][5], "gligar_noite": campos["land_mons"][5],
                "chinchou": campos["fishing_mons"][7], "lanturn": campos["fishing_mons"][8],
                "corsola": campos["water_mons"][1], "girafarig": campos["land_mons"][8]}
    for chave, pct in esperado.items():
        assert johto.AMOSTRAS[chave][0] == pytest.approx(pct / 100), chave


# --- DexNav ---------------------------------------------------------------------------------------------------------

def test_dexnav_mostra(gerar):
    texto = DEXNAV_MAPAS.read_text(encoding="utf-8")
    for mapa in ("MAP_ROUTE19", "MAP_ROUTE20", "MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH",
                 "MAP_FIVE_ISLAND_RESORT_GORGEOUS", "MAP_FIVE_ISLAND_MEADOW",
                 "MAP_SEVEN_ISLAND_SEVAULT_CANYON", "MAP_SAFARI_ZONE_WEST"):
        assert f"MAP_GROUP({mapa}), MAP_NUM({mapa})" in texto, mapa

    def por(mapa, metodo):
        return {e["especie"]: e for e in gerar.enumerar(mapa) if e["metodo"] == metodo}

    for mapa in ("MAP_ROUTE19", "MAP_ROUTE20", "MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH"):
        super_vara = por(mapa, gerar.SUPER_ROD)
        assert super_vara["SPECIES_CHINCHOU"]["chances"] == [150, 150, 150], mapa
        assert (super_vara["SPECIES_CHINCHOU"]["min"], super_vara["SPECIES_CHINCHOU"]["max"]) == (25, 35)
        assert super_vara["SPECIES_LANTURN"]["chances"] == [40, 40, 40], mapa
        assert "SPECIES_CHINCHOU" not in por(mapa, gerar.OLD_ROD) and "SPECIES_CHINCHOU" not in por(mapa, gerar.GOOD_ROD)
    agua = por("MAP_FIVE_ISLAND_RESORT_GORGEOUS", gerar.WATER)
    assert agua["SPECIES_CORSOLA"]["chances"] == [300, 300, 300]
    prado = por("MAP_FIVE_ISLAND_MEADOW", gerar.LAND)
    assert prado["SPECIES_MILTANK"]["chances"][0] == prado["SPECIES_MILTANK"]["chances"][1] == 100
    assert prado["SPECIES_MILTANK"]["chances"][2] == 0
    assert (prado["SPECIES_MILTANK"]["min"], prado["SPECIES_MILTANK"]["max"]) == (30, 35)
    canion = por("MAP_SEVEN_ISLAND_SEVAULT_CANYON", gerar.LAND)
    assert canion["SPECIES_GLIGAR"]["chances"] == [0, 0, 100]
    assert (canion["SPECIES_GLIGAR"]["min"], canion["SPECIES_GLIGAR"]["max"]) == (35, 40)
    safari = por("MAP_SAFARI_ZONE_WEST", gerar.LAND)
    assert safari["SPECIES_GIRAFARIG"]["chances"] == [40, 40, 40]
    assert (safari["SPECIES_GIRAFARIG"]["min"], safari["SPECIES_GIRAFARIG"]["max"]) == (25, 30)
