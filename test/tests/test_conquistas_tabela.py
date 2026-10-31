"""Conquistas e diário de batalhas (POK-44), Task 1: a tabela-fonte, o gerador e a medida dos textos.

As conquistas e os eventos do diário moram num JSON único (`src/data/conquistas/conquistas.json`); o make o
converte em `src/data/conquistas_ids.h` e `src/data/conquistas_tabela.h` (só `const`) com
`tools/conquistas/gen_conquistas.py`, no padrão do `tools/novidades/gen_cartoes.py`. As larguras dos nomes são
constantes de `include/conquistas.h`; a checagem de texto da esteira (`esteira.check_text`) lê essas mesmas
constantes e mede cada nome do JSON (sem emulador).
"""

import copy
import importlib.util
import json
import re
import subprocess
import sys

import pytest

from esteira import check_text as ct
from esteira.scenarios import REPO_ROOT

JSON_REL = "src/data/conquistas/conquistas.json"
JSON_PATH = REPO_ROOT / JSON_REL
GEN_SCRIPT = REPO_ROOT / "tools" / "conquistas" / "gen_conquistas.py"
HEADER_H = REPO_ROOT / "include" / "conquistas.h"
CONST_H = REPO_ROOT / "include" / "constants" / "conquistas.h"
RULES_MK = REPO_ROOT / "json_data_rules.mk"
GITIGNORE = REPO_ROOT / ".gitignore"

# Os ids da tabela do plano (Task 1, Step 3).
IDS_DO_SPEC = (
    [f"insignia_{n}" for n in ("rocha", "cascata", "trovao", "arcoiris", "alma", "pantano", "vulcao", "terra")]
    + ["vencer_elite4", "campeao", "silph", "sevii",
       "treinadores", "lider_um_pokemon", "sem_desmaio", "golpe_x4", "rival_todas", "revanche_max", "e4_degrau100",
       "primeira_captura", "shinies", "aves", "caes", "mewtwo", "lugia_hooh", "miticos", "kanto_151", "dex_obtivel",
       "poke_ball_dificil", "fosseis",
       "nivel_50", "nivel_100", "primeiro_ovo", "ovo_shiny", "ovo_6ivs", "amizade_max", "espeon_umbreon",
       "cidades", "passos", "dinheiro", "horas"])
TIPOS = ("FLAG", "FLAGS_TODAS", "DEX_TODOS", "DEX_KANTO", "DEX_NACIONAL", "NIVEL", "AMIZADE_MAX", "GAME_STAT",
         "DINHEIRO", "HORAS", "VITORIAS", "SHINIES", "EVENTO")


def _dados() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def _conquistas() -> dict[str, dict]:
    return {c["id"]: c for c in _dados()["conquistas"]}


def _gen():
    spec = importlib.util.spec_from_file_location("gen_conquistas", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _defines(*nomes_de_header: str) -> set[str]:
    out: set[str] = set()
    for nome in nomes_de_header:
        texto = (REPO_ROOT / "include" / "constants" / f"{nome}.h").read_text(encoding="utf-8")
        out.update(re.findall(r"^#define\s+([A-Z][A-Z0-9_]*)\b", texto, re.M))
    return out


def _constante_numerica(nome: str) -> int:
    m = re.search(rf"^#define {nome}\s+(\d+)\b", CONST_H.read_text(encoding="utf-8"), re.M)
    assert m, f"{nome} não está em include/constants/conquistas.h"
    return int(m.group(1))


# --- esquema -----------------------------------------------------------------------------------

def test_esquema():
    dados = _dados()
    abas = [a["id"] for a in dados["abas"]]
    assert len(abas) == len(set(abas))
    conquistas = dados["conquistas"]
    nums = [c["num"] for c in conquistas]
    assert len(nums) == len(set(nums)) and all(0 <= n < 64 for n in nums)
    ids = [c["id"] for c in conquistas]
    assert len(ids) == len(set(ids)) and all(re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids)
    consts = _defines("flags", "game_stat", "species", "items", "opponents", "conquistas")
    itens = _defines("items")
    com_degraus = 0
    for c in conquistas:
        assert c["aba"] in abas, c["id"]
        assert c["tipo"] in TIPOS, c["id"]
        if c["tipo"] in ("FLAG", "FLAGS_TODAS", "EVENTO", "GAME_STAT"):
            assert c["param"] in consts, f"{c['id']}: param {c['param']} não existe nos headers"
        for s in c.get("lista", []):
            assert s in consts, f"{c['id']}: {s}"
        for p in c["premios"]:
            assert p["item"] in itens, f"{c['id']}: {p['item']}"
            assert 1 <= p["qtd"] <= 99, c["id"]
        degraus = c.get("degraus", [])
        if degraus:
            com_degraus += 1
            assert all(a < b for a, b in zip(degraus, degraus[1:])), c["id"]
        assert len(c["premios"]) in {1, len(degraus)}, c["id"]
        assert ("{N}" in c["nome"]) == bool(degraus), c["id"]
    assert com_degraus <= 8
    assert _constante_numerica("CONQ_MAX") == 64 and _constante_numerica("CONQ_MAX_DEGRAUS") == 8


def test_constantes_do_plano_nos_headers():
    esperadas = {"CONQ_MAGIC": "0x31445143", "CONQ_VERSAO": "1", "CONQ_MAX": "64", "CONQ_MAX_DEGRAUS": "8",
                 "DIARIO_MAX": "48", "CONQ_PENDENTE": "0", "CONQ_FEITA": "1", "CONQ_PERDIDA": "2",
                 "CONQ_ORIGEM_JOGO_NOVO": "0", "CONQ_ORIGEM_SAVE_ANTIGO": "1", "DIARIO_VENCEU": "1",
                 "DIARIO_CAPTURADO": "2", "DIARIO_DERROTOU": "3", "CONQ_TAXA_DIFICIL": "45",
                 "DIARIO_TIPO_TREINADOR": "0", "DIARIO_TIPO_LENDARIO": "1"}
    tipos = ["FLAG", "FLAGS_TODAS", "DEX_TODOS", "DEX_KANTO", "DEX_NACIONAL", "NIVEL", "AMIZADE_MAX", "GAME_STAT",
             "DINHEIRO", "HORAS", "VITORIAS", "SHINIES", "EVENTO"]
    esperadas.update({f"CONQ_TIPO_{t}": str(i) for i, t in enumerate(tipos)})
    eventos = ["LIDER_UM_POKEMON", "SEM_DESMAIO", "GOLPE_X4", "RIVAL_TODAS", "POKE_BALL_DIFICIL", "OVO_SHINY",
               "OVO_6IVS", "ELITE4", "REVANCHE_MAX", "E4_DEGRAU100"]
    esperadas.update({f"CONQ_EVT_{e}": str(i) for i, e in enumerate(eventos)})
    texto = CONST_H.read_text(encoding="utf-8")
    for nome, valor in esperadas.items():
        m = re.search(rf"^#define {nome}\s+(\S+)", texto, re.M)
        assert m and m.group(1) == valor, nome
    texto_h = HEADER_H.read_text(encoding="utf-8")
    for nome, valor in (("CONQ_NOME_LARGURA", 152), ("DIARIO_NOME_LARGURA", 80), ("DIARIO_LOCAL_LARGURA", 136)):
        assert re.search(rf"^#define {nome}\s+{valor}\b", texto_h, re.M), nome
    assert "struct ConquistaPremio" in texto_h and "struct Conquista\n" in texto_h
    assert "struct DiarioEvento" in texto_h and "gConquistasAbaNomes" in texto_h


def test_pedidas_pelo_cintra():
    c = _conquistas()
    for i in range(1, 9):
        assert any(x["tipo"] == "FLAG" and x["param"] == f"FLAG_BADGE0{i}_GET" for x in c.values()), i
    for cid in ("vencer_elite4", "campeao", "treinadores", "shinies", "aves", "caes", "mewtwo", "lugia_hooh",
                "miticos", "nivel_50", "nivel_100"):
        assert cid in c, cid
    assert c["treinadores"]["degraus"] == list(range(10, 301, 10))
    assert c["shinies"]["degraus"][0] == 1
    assert c["nivel_50"]["param"] == 50 and c["nivel_100"]["param"] == 100


def test_cobre_o_spec():
    c = _conquistas()
    assert set(IDS_DO_SPEC) <= set(c)
    assert len(c) == len(IDS_DO_SPEC)
    assert {i for i, x in c.items() if x.get("ativa") is False} == {"revanche_max", "e4_degrau100"}
    assert {i for i, x in c.items() if x.get("perdivel")} == {"lider_um_pokemon", "rival_todas"}
    assert c["dex_obtivel"]["param"] == 245
    assert "contar_dex" in _dados()["_comentario"]


def test_premios_do_plano():
    c = _conquistas()
    assert [p["item"] for i, x in c.items() if i.startswith("insignia_") for p in x["premios"]] == [
        "ITEM_POKE_BALL", "ITEM_SUPER_POTION", "ITEM_GREAT_BALL", "ITEM_SUPER_REPEL", "ITEM_ULTRA_BALL",
        "ITEM_RARE_CANDY", "ITEM_PP_UP", "ITEM_MAX_REVIVE"]
    treinadores = c["treinadores"]
    for degrau, premio in zip(treinadores["degraus"], treinadores["premios"]):
        esperado = ("ITEM_RARE_CANDY", 1) if degrau % 50 == 0 else ("ITEM_GREAT_BALL", 3)
        assert (premio["item"], premio["qtd"]) == esperado, degrau
    assert [p["item"] for p in c["shinies"]["premios"]] == [
        "ITEM_ULTRA_BALL", "ITEM_RARE_CANDY", "ITEM_PP_MAX", "ITEM_MASTER_BALL", "ITEM_LUCKY_EGG", "ITEM_MASTER_BALL"]
    assert c["horas"]["degraus"] == [10, 50, 100]
    assert [p["item"] for p in c["horas"]["premios"]] == ["ITEM_RARE_CANDY", "ITEM_PP_UP", "ITEM_MASTER_BALL"]
    assert c["cidades"]["param2"] == 18 and c["cidades"]["paramFim"] == "FLAG_WORLD_MAP_SIX_ISLAND"


# --- diário ------------------------------------------------------------------------------------

def test_diario():
    d = _dados()["diario"]
    assert len(d) == 33
    assert sum(1 for e in d if e["lider"]) == 8
    assert sum(1 for e in d if e["rival"]) == 8
    assert "campeao" in {e["id"] for e in d if e["rival"]}
    rivais = [e for e in d if e["rival"]]
    for e in rivais:
        assert len(e["treinadores"]) == 3, e["id"]
        assert {t.rsplit("_", 1)[1] for t in e["treinadores"]} == {"SQUIRTLE", "BULBASAUR", "CHARMANDER"}, e["id"]
    assert [e["id"] for e in rivais if e["id"].startswith("rival_")] == [
        "rival_lab", "rival_rota22", "rival_cerulean", "rival_ss_anne", "rival_torre", "rival_silph",
        "rival_rota22_final"]
    giovanni = next(e for e in d if e["id"] == "giovanni")
    assert giovanni["lider"] and giovanni["treinadores"] == ["TRAINER_LEADER_GIOVANNI"]
    lance = next(e for e in d if e["id"] == "lance")
    assert lance["treinadores"] == ["TRAINER_ELITE_FOUR_LANCE", "TRAINER_ELITE_FOUR_LANCE_2"]
    lendarios = [e for e in d if e["tipo"] == "lendario"]
    assert len(lendarios) == 13 and all(e["especie"].startswith("SPECIES_") for e in lendarios)
    consts = _defines("species", "opponents")
    for e in d:
        for t in e.get("treinadores", []):
            assert t in consts, t
        if e["tipo"] == "lendario":
            assert e["especie"] in consts


# --- gerador -----------------------------------------------------------------------------------

def _gerar(destino, json_path=JSON_PATH):
    ids, tabela = destino / "ids.h", destino / "tabela.h"
    subprocess.run([sys.executable, str(GEN_SCRIPT), str(json_path), str(ids), str(tabela)], check=True)
    return ids.read_text(encoding="utf-8"), tabela.read_text(encoding="utf-8")


def test_gerador_deterministico(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    a, b = _gerar(tmp_path / "a"), _gerar(tmp_path / "b")
    assert a == b
    for texto in a:
        assert "EWRAM_DATA" not in texto
        assert "DO NOT MODIFY THIS FILE" in texto


def test_ids_gerados(tmp_path):
    ids, tabela = _gerar(tmp_path)
    for c in _dados()["conquistas"]:
        assert f"#define CONQ_{c['id'].upper()} {c['num']}\n" in ids
    assert "#define CONQ_COUNT 41\n" in ids
    assert "#define CONQ_ABAS_COUNT 5\n" in ids and "#define CONQ_ABA_EXPLORACAO 4\n" in ids
    assert "#define DIARIO_EVT_BROCK 0\n" in ids and "#define DIARIO_EVT_COUNT 33\n" in ids
    assert "{STR_VAR_1}" in tabela and "{N}" not in tabela      # o {N} do JSON vira o placeholder do jogo
    assert ".slotDegrau = 0xFF," in tabela and ".ativa = FALSE," in tabela and ".perdivel = TRUE," in tabela
    assert "sConqPremios_treinadores[] =" in tabela


def test_cli_tabela_markdown():
    r = subprocess.run([sys.executable, str(GEN_SCRIPT), "--tabela", str(JSON_PATH)], check=True,
                       capture_output=True, encoding="utf-8")
    md = r.stdout
    assert "## Conquistas" in md and "## Prêmios por faixa" in md and "### BATALHA" in md
    assert "Vencer {N} treinadores" in md and "Bola Mestra" in md


@pytest.mark.parametrize("mexe, erro", [
    (lambda d: d["conquistas"][0].update(param="FLAG_NAO_EXISTE"), "não existe nos headers"),
    (lambda d: d["conquistas"][0]["premios"][0].update(item="ITEM_NAO_EXISTE"), "não existe nos headers"),
    (lambda d: d["conquistas"][0]["premios"][0].update(qtd=100), "fora de 1-99"),
    (lambda d: d["conquistas"][1].update(num=d["conquistas"][0]["num"]), "repetido"),
    (lambda d: d["conquistas"][0].update(aba="nenhuma"), "não está em `abas`"),
    (lambda d: d["conquistas"][0].update(nome="Insígnia {N}"), "se e só se"),
    (lambda d: d["diario"][0]["treinadores"].append("TRAINER_NAO_EXISTE"), "não existe nos headers"),
])
def test_gerador_recusa_json_malformado(tmp_path, mexe, erro):
    dados = copy.deepcopy(_dados())
    mexe(dados)
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(GEN_SCRIPT), str(ruim), str(tmp_path / "i.h"), str(tmp_path / "t.h")],
                       capture_output=True, encoding="utf-8")
    assert r.returncode != 0 and erro in r.stderr


def test_gerador_recusa_degraus_fora_de_ordem(tmp_path):
    dados = copy.deepcopy(_dados())
    dados["conquistas"] = [c for c in dados["conquistas"]]
    shinies = next(c for c in dados["conquistas"] if c["id"] == "shinies")
    shinies["degraus"] = [5, 1, 10, 20, 30, 50]
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(GEN_SCRIPT), str(ruim), str(tmp_path / "i.h"), str(tmp_path / "t.h")],
                       capture_output=True, encoding="utf-8")
    assert r.returncode != 0 and "estritamente crescentes" in r.stderr


def test_slots_de_degrau_fixos(tmp_path):
    """O progresso dos degraus vai no save (`degrauEntregue[slot]`): o slot é explícito no JSON e não muda
    quando uma conquista nova entra (Task 2)."""
    c = {x["id"]: x for x in _dados()["conquistas"]}
    assert {i: x["slot"] for i, x in c.items() if "slot" in x} == {"treinadores": 0, "shinies": 1, "horas": 2}
    _, tabela = _gerar(tmp_path)
    for cid, slot in (("treinadores", 0), ("shinies", 1), ("horas", 2)):
        bloco = re.search(rf"\[CONQ_{cid.upper()}\] =\n    \{{(.*?)\n    \}}", tabela, re.S).group(1)
        assert f".slotDegrau = {slot}," in bloco, cid


@pytest.mark.parametrize("mexe, erro", [
    (lambda d: next(c for c in d["conquistas"] if c["id"] == "horas").pop("slot"), "slot"),
    (lambda d: next(c for c in d["conquistas"] if c["id"] == "horas").update(slot=0), "slot 0 repetido"),
    (lambda d: next(c for c in d["conquistas"] if c["id"] == "horas").update(slot=8), "fora de 0-7"),
    (lambda d: d["conquistas"][0].update(slot=3), "`slot` só existe"),
])
def test_gerador_recusa_slot_malformado(tmp_path, mexe, erro):
    dados = copy.deepcopy(_dados())
    mexe(dados)
    ruim = tmp_path / "ruim.json"
    ruim.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(GEN_SCRIPT), str(ruim), str(tmp_path / "i.h"), str(tmp_path / "t.h")],
                       capture_output=True, encoding="utf-8")
    assert r.returncode != 0 and erro in r.stderr


def test_make_gera_os_headers_e_o_git_ignora():
    mk = RULES_MK.read_text(encoding="utf-8")
    assert "tools/conquistas/gen_conquistas.py" in mk
    assert "conquistas/conquistas.json" in mk and "conquistas_ids.h" in mk and "conquistas_tabela.h" in mk
    assert re.search(r"conquistas_data\.o: c_dep \+=.*conquistas_tabela\.h", mk)
    ignorados = GITIGNORE.read_text(encoding="utf-8").splitlines()
    assert "src/data/conquistas_ids.h" in ignorados and "src/data/conquistas_tabela.h" in ignorados
    fonte = (REPO_ROOT / "src" / "conquistas_data.c").read_text(encoding="utf-8")
    assert "data/conquistas_ids.h" in fonte and "data/conquistas_tabela.h" in fonte


# --- larguras (esteira) ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def entradas():
    return {e.label: e for e in ct._sources(REPO_ROOT) if not isinstance(e, ct.Result) and e.file == JSON_REL}


def test_esteira_registra_nomes_e_locais(entradas):
    dados = _dados()
    esperados = ({f"c.{c['id']}.nome" for c in dados["conquistas"]}
                 | {f"d.{e['id']}.{campo}" for e in dados["diario"] for campo in ("nome", "local")})
    assert set(entradas) == esperados
    assert entradas["c.treinadores.nome"].texts == ("Vencer 300 treinadores",)     # {N} medido como 300
    for rel in ("src/data/conquistas_ids.h", "src/data/conquistas_tabela.h"):
        assert rel not in {f for f, _ in ct._source_files(REPO_ROOT)}


def test_janelas_da_esteira_usam_as_constantes_do_header(entradas):
    esperado = {"c.": ("CONQ_NOME_LARGURA", 152), "d.": ("DIARIO_NOME_LARGURA", 80)}
    for label in entradas:
        regra = ct.rule_for(JSON_REL, label)
        assert regra is not None, label
        if label.endswith(".local"):
            assert regra.px == 136 and "DIARIO_LOCAL_LARGURA" in regra.source, label
        else:
            const, px = esperado[label[:2]]
            assert regra.px == px and const in regra.source, label
        assert regra.lines == 1 and regra.font == "normal"


def test_larguras():
    achados = [r for r in ct.check_text(str(REPO_ROOT), {}) if JSON_REL in r.detail]
    assert not achados, "\n".join(r.detail for r in achados)


def test_medida_acusa_nome_que_nao_cabe():
    env = ct._load_env(REPO_ROOT)
    regra = ct.rule_for(JSON_REL, "c.treinadores.nome")
    assert ct.measure("Vencer 300 treinadores", env, "normal").widest <= regra.px
    assert [p[0] for p in ct._analyze("Vencer um total de 300 treinadores na jornada", False, regra, env)] == [
        ct.RULE_WIDTH]


def test_pior_nome_usa_a_janela_com_folga_pequena(entradas):
    """Os nomes mais largos chegam perto do limite: avisa se a janela ficou frouxa demais ou se estourou."""
    env = ct._load_env(REPO_ROOT)
    medidas = {rotulo: ct.measure(e.texts[0], env, "normal").widest for rotulo, e in entradas.items()}
    assert max(v for k, v in medidas.items() if k.startswith("c.")) <= 152
    assert max(v for k, v in medidas.items() if k.startswith("d.") and k.endswith(".nome")) <= 80
    assert max(v for k, v in medidas.items() if k.endswith(".local")) <= 136
