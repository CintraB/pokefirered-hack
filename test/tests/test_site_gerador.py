import importlib.util
import json
import os
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


def test_familia_definida_por_lista_de_slugs():
    """O capítulo da Família é a lista explícita FAMILIA (Família Sombra e Pedágio da Rota 23), não uma busca no título."""
    assert gerar_mod.FAMILIA == ("modernas/familia-sombra", "modernas/pedagio-da-rota-23")
    caps = {c["id"]: c for c in _caps()}
    fam = caps["familia"]["cartoes"]
    assert [c["id"] for c in fam] == [k.replace("/", "-") for k in gerar_mod.FAMILIA]
    assert all(c["spoiler"] for c in fam)
    assert {c["titulo"] for c in fam} == {"Família Sombra", "Pedágio da Rota 23"}
    assert not {c["id"] for c in caps["modernas"]["cartoes"]} & {c["id"] for c in fam}
    assert not any(c["spoiler"] for cap in caps.values() if cap["id"] != "familia" for c in cap["cartoes"])


def test_familia_com_slug_inexistente_falha(monkeypatch):
    monkeypatch.setattr(gerar_mod, "FAMILIA", ("modernas/familia-sombra", "modernas/nao-existe"))
    with pytest.raises(ValueError, match="modernas/nao-existe"):
        _caps()


def test_titulo_com_familia_sombra_fora_da_lista_nao_vai_para_o_spoiler(tmp_path):
    """Um cartão novo com "Família Sombra" no título só entra no spoiler se for posto na lista."""
    repo = _repo_temporario(tmp_path, {})
    arq = repo / "src/data/novidades/cartoes.json"
    dados = json.loads(arq.read_text(encoding="utf-8"))
    modernas = [t for t in dados["topics"] if t["id"] == "modernas"][0]
    modernas["cards"].append({"title": "Família Sombra: bônus", "body": "Texto."})
    arq.write_text(json.dumps(dados), encoding="utf-8")
    caps = {c["id"]: c for c in gerar_mod.carregar_capitulos(repo)}
    assert "Família Sombra: bônus" in {c["titulo"] for c in caps["modernas"]["cartoes"]}
    assert "Família Sombra: bônus" not in {c["titulo"] for c in caps["familia"]["cartoes"]}


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
        assert (lugares[tid]["x"], lugares[tid]["y"]) == ((c * 8 + 36 - 24) * 4, (l * 8 + 36 - 16) * 4), tid


def _repo_temporario(tmp_path, textos):
    repo = tmp_path / "repo"
    (repo / "src/data/graphics").mkdir(parents=True)
    shutil.copytree(REPO / "src/data/novidades", repo / "src/data/novidades")
    shutil.copy(REPO / "src/data/item_icon_table.h", repo / "src/data")  # sprites de item
    shutil.copy(REPO / "src/data/graphics/items.h", repo / "src/data/graphics")
    shutil.copy(REPO / "README.md", repo)  # aviso legal e créditos da página vêm do README
    shutil.copytree(REPO / "site", repo / "site")
    for pasta in ("graphics", "docs/readme", "test/referencias"):  # sprites e telas: só leitura, por link
        (repo / pasta).parent.mkdir(parents=True, exist_ok=True)
        os.symlink(REPO / pasta, repo / pasta)
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
