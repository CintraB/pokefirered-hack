import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("site_gerar", REPO / "tools/site/gerar.py")
gerar_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerar_mod)


def _caps():
    return gerar_mod.carregar_capitulos(REPO)


def test_todos_os_cartoes_viram_secao():
    dados = json.loads((REPO / "src/data/novidades/cartoes.json").read_text(encoding="utf-8"))
    total = sum(len(t["cards"]) for t in dados["topics"])
    assert sum(len(c["cartoes"]) for c in _caps()) == total


def test_body_vira_paragrafo():
    assert all("\n" not in c["texto"] for cap in _caps() for c in cap["cartoes"])


@pytest.mark.parametrize("entrada,esperado", [
    ("abc-\ndef\nghi", "abc-def ghi"),
    ("palavra-\ncontinua", "palavra-continua"),
    ("algo -\noutro", "algo - outro"),
    ("a\n\nb", "a b"),
    ("  a  \n  b  ", "a b"),
])
def test_juntar_linhas(entrada, esperado):
    assert gerar_mod.juntar_linhas(entrada) == esperado


def test_familia_sai_de_modernas():
    caps = {c["id"]: c for c in _caps()}
    fam = caps["familia"]["cartoes"]
    assert fam and all("Família Sombra" in c["titulo"] and c["spoiler"] for c in fam)
    assert not any("Família Sombra" in c["titulo"] for c in caps["modernas"]["cartoes"])


def test_lugares_para_todos_os_capitulos():
    lugares = json.loads((REPO / "site/lugares.json").read_text(encoding="utf-8"))
    assert "abertura" in lugares
    for cap in _caps():
        assert cap["id"] in lugares
        assert set(cap["lugar"]) == {"nome", "x", "y", "zoom"}


CELULAS = {  # id: (coluna, linha, MAPSEC) em region_map_layout_kanto.h
    "sobre": (4, 11, "PALLET_TOWN"), "ritmo": (4, 9, "ROUTE_1"), "resumo": (4, 8, "VIRIDIAN_CITY"),
    "dex": (4, 4, "PEWTER_CITY"), "shiny": (14, 3, "CERULEAN_CITY"), "creche": (14, 4, "ROUTE_5"),
    "evolucoes": (11, 6, "CELADON_CITY"), "modernas": (14, 6, "SAFFRON_CITY"),
    "dia_noite": (18, 6, "LAVENDER_TOWN"), "clima": (14, 9, "VERMILION_CITY"),
    "lendarios": (4, 14, "CINNABAR_ISLAND"), "pos_liga": (2, 3, "INDIGO_PLATEAU"),
    "familia": (2, 5, "ROUTE_23"),
}


def test_coordenadas_batem_com_a_formula_e_com_o_layout():
    s = (REPO / "src/data/region_map/region_map_layout_kanto.h").read_text()
    camada = s.split("[LAYER_DUNGEON]")[0]
    grade = [[x.strip() for x in r.split(",")] for r in re.findall(r"\{(MAPSEC[^}]*)\}", camada)]
    lugares = json.loads((REPO / "site/lugares.json").read_text(encoding="utf-8"))
    for tid, (c, l, sec) in CELULAS.items():
        assert grade[l][c] == "MAPSEC_" + sec, tid
        assert (lugares[tid]["x"], lugares[tid]["y"]) == ((c * 8 + 36 - 24) * 4, (l * 8 + 22 - 16) * 4), tid


def _repo_temporario(tmp_path, textos):
    repo = tmp_path / "repo"
    (repo / "src/data/novidades").mkdir(parents=True)
    shutil.copy(REPO / "src/data/novidades/cartoes.json", repo / "src/data/novidades")
    shutil.copytree(REPO / "site", repo / "site")
    (repo / "site/textos.json").write_text(json.dumps(textos), encoding="utf-8")
    return repo


def test_cartao_sem_texto_longo(tmp_path):
    chave = gerar_mod.chaves_do_topico("ritmo", _cartoes_json()["ritmo"])[0]
    repo = _repo_temporario(tmp_path, {chave: {"longo": "texto longo"}})
    cartoes = {c["id"]: c for cap in gerar_mod.carregar_capitulos(repo) for c in cap["cartoes"]}
    assert cartoes[chave.replace("/", "-")]["longo"] == "texto longo"
    assert all(c["longo"] is None for i, c in cartoes.items() if i != chave.replace("/", "-"))


def _cartoes_json():
    d = json.loads((REPO / "src/data/novidades/cartoes.json").read_text(encoding="utf-8"))
    return {t["id"]: t["cards"] for t in d["topics"]}


def test_ids_e_chaves_unicos():
    ids = [c["id"] for cap in _caps() for c in cap["cartoes"]]
    assert len(ids) == len(set(ids))


def test_slug():
    assert gerar_mod.slug("Pokédex e Captura!") == "pokedex-e-captura"


def test_chave_de_texto_sem_cartao_falha(tmp_path):
    repo = _repo_temporario(tmp_path, {"ritmo/nao-existe": {"longo": "x"}})
    with pytest.raises(ValueError, match="ritmo/nao-existe"):
        gerar_mod.gerar(repo, tmp_path / "saida")


def test_saida_nao_publica_json_de_trabalho(tmp_path):
    repo = _repo_temporario(tmp_path, {})
    gerar_mod.gerar(repo, tmp_path / "saida")
    nomes = {p.name for p in (tmp_path / "saida").iterdir()}
    assert "index.html" in nomes
    assert not nomes & {"lugares.json", "textos.json", "template.html"}


def test_tela_inexistente_falha(tmp_path):
    chave = gerar_mod.chaves_do_topico("ritmo", _cartoes_json()["ritmo"])[0]
    repo = _repo_temporario(tmp_path, {chave: {"tela": "docs/readme/nao_existe.png"}})
    with pytest.raises(FileNotFoundError, match="tela não encontrada.*nao_existe.png"):
        gerar_mod.gerar(repo, tmp_path / "saida")
