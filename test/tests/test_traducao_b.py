"""Frente B da tradução: diálogos dos mapas (`data/maps/*/text.inc`), por grupo.

Para cada arquivo já traduzido: nenhuma palavra inglesa sobrando (`esteira.check_text.english_report`),
nenhum achado das regras `controle`, `glossario`, `largura`, `linhas` e `letras`, e os rótulos
continuam os da base inglesa (traduzir não renomeia nem apaga texto). Cada task da frente
acrescenta o seu grupo em `GROUPS`.
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]

GROUPS = {
    "B1": [f"data/maps/{m}/text.inc" for m in (
        "PalletTown_RivalsHouse", "PewterCity", "PewterCity_Gym", "PewterCity_House1", "PewterCity_House2",
        "PewterCity_Mart", "PewterCity_Museum_1F", "PewterCity_Museum_2F", "PewterCity_PokemonCenter_1F",
        "PokemonLeague_AgathasRoom", "PokemonLeague_BrunosRoom", "PokemonLeague_ChampionsRoom",
        "PokemonLeague_HallOfFame", "PokemonLeague_LancesRoom", "PokemonLeague_LoreleisRoom",
        "PokemonMansion_1F", "PokemonMansion_2F", "PokemonMansion_3F", "PokemonMansion_B1F",
        "PokemonTower_1F", "PokemonTower_2F", "PokemonTower_3F", "PokemonTower_4F", "PokemonTower_5F",
        "PokemonTower_6F", "PokemonTower_7F", "RockTunnel_1F", "RockTunnel_B1F", "RocketHideout_B1F",
        "RocketHideout_B2F", "RocketHideout_B3F", "RocketHideout_B4F", "RocketHideout_Elevator",
        "Route1", "Route10")],
}
FILES = sorted(f for files in GROUPS.values() for f in files)
RULES = ("controle", "glossario", "largura", "linhas", "letras")

_LABEL = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)::", re.M)


@lru_cache(maxsize=None)
def _results():
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    return ct.check_text(str(REPO_ROOT), exceptions, english="desligado")


@lru_cache(maxsize=None)
def _english():
    return ct.english_report(str(REPO_ROOT))


@pytest.mark.parametrize("rel", FILES)
def test_nenhum_ingles_sobrando(rel):
    assert rel not in _english(), _english().get(rel)


@pytest.mark.parametrize("rel", FILES)
def test_sem_achados_das_regras(rel):
    found = [r.detail for r in _results()
             if r.status == "falha" and r.name in {f"texto/{rule}" for rule in RULES}
             and r.detail.startswith(f"{rel}:")]
    assert found == []


@pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git")
@pytest.mark.parametrize("rel", FILES)
def test_rotulos_iguais_aos_da_base(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    base = _LABEL.findall(out.stdout.decode("utf-8"))
    current = _LABEL.findall((REPO_ROOT / rel).read_text(encoding="utf-8"))
    assert current == base


def test_termos_criados_pela_frente_b_no_glossario():
    terms = {t["en"]: t for t in json.loads(
        (REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))["termos"]
             if t.get("frente") == "B"}
    assert terms["RUNNING SHOES"]["completo"] == "Tênis de Corrida"
    assert all(t["fonte"] == "criado" for t in terms.values())


def test_base_inglesa_disponivel():
    """Sem a base inglesa as regras `controle` e `glossario` não rodam: o teste não pode passar calado."""
    missing = [r.detail for r in _results() if "base inglesa indispon" in r.detail]
    assert missing == []
