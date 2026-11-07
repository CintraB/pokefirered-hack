import importlib.util
import json
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
    assert gerar_mod.juntar_linhas("abc-\ndef\nghi") == "abc-def ghi"


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


def test_cartao_sem_texto_longo():
    assert all(c["longo"] is None for cap in _caps() for c in cap["cartoes"])


def test_tela_inexistente_falha(tmp_path):
    repo = tmp_path / "repo"
    (repo / "src/data/novidades").mkdir(parents=True)
    shutil.copy(REPO / "src/data/novidades/cartoes.json", repo / "src/data/novidades")
    shutil.copytree(REPO / "site", repo / "site")
    (repo / "site/textos.json").write_text(
        json.dumps({"ritmo/0": {"tela": "docs/readme/nao_existe.png"}}), encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="nao_existe.png"):
        gerar_mod.gerar(repo, tmp_path / "saida")
