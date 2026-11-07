"""Workflow de publicação da Página do Professor no GitHub Pages."""
import re
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
    # Privilégio mínimo: o topo só lê; pages/id-token só no job que publica.
    assert dados["permissions"] == {"contents": "read"}
    assert dados["jobs"]["deploy"]["permissions"] == {"pages": "write", "id-token": "write"}
    # o build só lê o repositório e a configuração do Pages (o configure-pages consulta a API)
    assert dados["jobs"]["build"]["permissions"] == {"contents": "read", "pages": "read"}
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
    texto, dados, _ = _carrega()
    passos = [p for job in dados["jobs"].values() for p in job.get("steps", []) if "run" in p]
    assert passos
    for passo in passos:
        assert not re.search(r"(^|[\s;&|])make(\s|$)", passo["run"]), passo["run"]
    assert "agbcc" not in texto


def test_workflow_instala_o_requirements():
    _, dados, _ = _carrega()
    comandos = [p["run"] for p in dados["jobs"]["build"]["steps"] if "run" in p]
    assert "pip install -r tools/site/requirements.txt" in comandos


def test_workflow_da_pret_intacto():
    assert (RAIZ / ".github" / "workflows" / "build.yml").exists()
