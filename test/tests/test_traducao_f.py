"""Frente F da tradução (dados de Pokémon): textos da Pokédex.

Task F1: `src/data/pokemon/pokedex_text_fr.h` de `gDummyPokedexText` até `gSunkernPokedexText`.
Os testes valem para as entradas já traduzidas (acrescentar o último rótulo de cada task nova em
`DEX_RANGES`): nenhum inglês, nenhum achado de `controle`/`glossario`/janela e nenhuma unidade
imperial. Modelo: `test_traducao_nomes.py`.
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct
from esteira.reflow import line_widths

REPO_ROOT = Path(__file__).resolve().parents[2]
DEX = "src/data/pokemon/pokedex_text_fr.h"

# (primeiro rótulo, último rótulo) de cada task, na ordem do arquivo
DEX_RANGES = [
    ("gDummyPokedexText", "gSunkernPokedexText"),     # F1
]

DEX_WIDTH_PX = 30 * 8
DEX_LINES = 3
IMPERIAL = re.compile(r"\b(?:\d[\d.,]*\s*(?:p[ée]s|polegadas?|libras?|onças?|milhas?|jardas?|n[óo]s|knots?|yd|ft|lbs?|mph)|fahrenheit)\b", re.I)
# Entrada com #if/#else que a extração da checagem não lê: medida aqui (variantes inclusive)
SPECIAL = {"gChikoritaPokedexText"}


def _source() -> str:
    return (REPO_ROOT / DEX).read_text(encoding="utf-8")


def _labels() -> list[str]:
    """Rótulos de texto (sem o `...Unused`) cobertos por `DEX_RANGES`, na ordem do arquivo."""
    all_labels = re.findall(r"^const u8 (g\w+PokedexText)\[\]", _source(), re.M)
    out: list[str] = []
    for first, last in DEX_RANGES:
        out += all_labels[all_labels.index(first):all_labels.index(last) + 1]
    return out


def _body(label: str) -> str:
    src = _source()
    start = src.index(f"const u8 {label}[]")
    return src[start:src.index(");", start)]


@pytest.fixture(scope="module")
def entries():
    wanted = set(_labels())
    return [e for e in ct._sources(REPO_ROOT)
            if isinstance(e, ct._Entry) and e.file == DEX and e.label in wanted]


def test_faixa_da_f1_inteira_foi_extraida(entries):
    labels = _labels()
    assert len(labels) == 192                                    # Dummy + 191 espécies
    assert {e.label for e in entries} == set(labels) - SPECIAL


def test_nenhum_ingles_sobrando_nas_entradas_traduzidas(entries):
    assert ct.english_report(str(REPO_ROOT), entries) == {}


def test_nenhuma_unidade_imperial_nas_entradas_traduzidas():
    found = [f"{label}: {m.group(0)}" for label in _labels()
             for m in [IMPERIAL.search(_body(label))] if m]
    assert found == []


def test_nada_de_caixa_alta_do_jogo_ingles(entries):
    caps = [e.label for e in entries
            if any(re.search(r"(?<![\w{])[A-Z]{3,}(?![\w}])", re.sub(r"\{[^}]*\}", "", t)) for t in e.texts)]
    assert caps == []


@lru_cache(maxsize=1)
def _results():
    if shutil.which("git") is None:
        pytest.fail("precisa do git: sem a base inglesa as regras controle/glossario não rodam")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{ct.TRANSLATION_BASE}^{{commit}}"],
                         capture_output=True)
    if out.returncode != 0:
        pytest.fail("sem o commit base da tradução: as regras controle/glossario não rodam")
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    return ct.check_text(str(REPO_ROOT), exceptions, english="desligado")


def test_base_inglesa_disponivel_nunca_passa_calado():
    unavailable = [r.detail for r in _results() if "base inglesa indisponível" in r.detail]
    assert unavailable == []


def test_sem_achado_de_regra_nas_entradas_traduzidas():
    labels = set(_labels())
    bad = []
    for r in _results():
        if r.status != "falha" or not r.name.startswith("texto/"):
            continue
        m = re.match(rf"{re.escape(DEX)}: (\w+):", r.detail)
        if m and m.group(1) in labels:
            bad.append(f"{r.name}: {r.detail}")
    assert bad == []


# Nomes de golpe, apelidos e termos de mais de uma palavra que não podem ser partidos pela quebra de linha
PROTECTED_TERMS = ["Ataque Espelhado", "Onda de Trovão", "Soco de Cometa", "Floresta Tropical Ambulante",
                   "Mach 2", "Oddium Wanderus", "Poké Bola", "Centro Pokémon", "Prof. Carvalho"]


def test_termos_compostos_nao_sao_partidos_na_quebra():
    split = []
    for label in _labels():
        text = "".join(re.findall(r'"([^"]*)"', _body(label)))     # as quebras ficam como `\n` literal
        for term in PROTECTED_TERMS:
            words = term.split(" ")
            for i in range(1, len(words)):
                if " ".join(words[:i]) + "\\n" + " ".join(words[i:]) in text:
                    split.append(f"{label}: {term}")
    assert split == []


# Valor + quebra + unidade ("cerca de 1\nkm"): a unidade sozinha no começo da linha lê mal
NUMBER_BREAK_UNIT = re.compile(
    r"\d[.,]?\\n(?:km/h|km|cm|mm|m|kg|g|°C|graus|volts|horas|anos|segundos|minutos|dias|semanas|tentáculos)\b")


def test_valor_e_unidade_nao_sao_partidos_na_quebra():
    found = []
    for label in _labels():
        text = "".join(re.findall(r'"([^"]*)"', _body(label)))
        for m in NUMBER_BREAK_UNIT.finditer(text):
            found.append(f"{label}: ...{text[max(0, m.start() - 12):m.end() + 8]}")
    assert found == []


def test_regex_de_valor_partido_reconhece_os_casos_da_revisao():
    assert NUMBER_BREAK_UNIT.search(r"a cerca de 1\nkm de distância")
    assert NUMBER_BREAK_UNIT.search(r"mais de 95\nkm/h.")
    assert not NUMBER_BREAK_UNIT.search(r"a cerca de 1 km\nde distância")


def test_chikorita_cabe_nas_duas_revisoes():
    body = _body("gChikoritaPokedexText")
    lines = re.findall(r'"([^"]*)"', body)
    first = [ln for ln in lines if ln.startswith(("Suas", "Sua"))]
    assert len(first) == 2                                        # ramo REVISION == 0 e ramo #else
    common = [ln for ln in lines if ln not in first]
    for variant in first:
        texts = (variant + "".join(common)).split("\\n")
        assert len(texts) <= DEX_LINES
        assert max(line_widths(variant + "".join(common))) <= DEX_WIDTH_PX
    assert not IMPERIAL.search(body)


def test_regra_da_pokedex_continua_240px_3_linhas():
    rule = ct.rule_for(DEX, "gBulbasaurPokedexText")
    assert (rule.px, rule.lines) == (DEX_WIDTH_PX, DEX_LINES)
