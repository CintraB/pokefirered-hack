"""Workflow de publicação da Página do Professor no GitHub Pages."""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO = RAIZ / ".github" / "workflows" / "pagina.yml"


def _carrega():
    texto = CAMINHO.read_text(encoding="utf-8")
    dados = yaml.safe_load(texto)
    # PyYAML lê a chave "on" como True
    gatilhos = dados.get("on", dados.get(True))
    return texto, dados, gatilhos


def test_workflow_dispara_na_hack_switch():
    _, _, gatilhos = _carrega()
    assert gatilhos["push"]["branches"] == ["hack-switch"]
    assert "workflow_dispatch" in gatilhos


def test_workflow_usa_pages():
    texto, dados, _ = _carrega()
    assert dados["permissions"]["pages"] == "write"
    assert dados["permissions"]["id-token"] == "write"
    assert dados["concurrency"]["group"] == "pages"
    assert dados["concurrency"]["cancel-in-progress"] is False
    for uso in ("actions/checkout@v4", "actions/setup-python@v5",
                "actions/configure-pages@v5",
                "actions/upload-pages-artifact@v3", "actions/deploy-pages@v4"):
        assert f"uses: {uso}" in texto
    deploy = dados["jobs"]["deploy"]
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["environment"]["url"] == "${{ steps.deployment.outputs.page_url }}"
    assert "tools/site/gerar.py --saida _site" in texto


def test_workflow_nao_compila_rom():
    texto, _, _ = _carrega()
    assert "make" not in texto
    assert "agbcc" not in texto


def test_workflow_da_pret_intacto():
    assert (RAIZ / ".github" / "workflows" / "build.yml").exists()
