"""Frente D da tradução (textos longos): os rótulos já traduzidos não têm inglês nem achado das
regras de texto da esteira (`controle`, `glossario`, largura, linhas, charmap, terminador).

Cada task da frente acrescenta a sua faixa em `TRANSLATED`: arquivo -> (primeiro rótulo, primeiro
rótulo que NÃO é da faixa ou None para ir até o fim do arquivo). O arquivo da ajuda é dividido
entre a D1 (do início até `Help_Text_HowToUseFight`) e a D2 (o resto).
"""

import re
import shutil
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git")

# arquivo -> [(primeiro rótulo, primeiro rótulo fora da faixa | None)]
TRANSLATED: dict[str, list[tuple[str, str | None]]] = {
    # D1: ajuda do jogo, parte 1
    "data/text/help_system.inc": [("Help_Text_WhatShouldIDo", "Help_Text_HowToUseFight")],
}

# Japonês deixado como está no original (a ajuda tem uma linha de "faça por conta própria")
JAPANESE_LABELS = {"data/text/help_system.inc": {"Help_Text_TryDoingItOnYourOwn"}}

_LABEL = re.compile(r"^(\w+)::", re.M)


def _labels(rel: str) -> set[str]:
    source = (REPO_ROOT / rel).read_text(encoding="utf-8")
    names = _LABEL.findall(source)
    wanted: set[str] = set()
    for first, stop in TRANSLATED[rel]:
        start = names.index(first)
        end = names.index(stop) if stop is not None else len(names)
        wanted.update(names[start:end])
    return wanted


@lru_cache(maxsize=1)
def _failures() -> tuple:
    """Todas as falhas da checagem de texto com o inglês bloqueante (sem exceções congeladas)."""
    results = ct.check_text(str(REPO_ROOT), {"text": []}, english="bloqueante")
    # sem a base inglesa as regras controle/glossario não rodam: o teste não pode passar calado
    assert not [r.detail for r in results if "base inglesa indisponível" in r.detail], \
        "base inglesa indisponível: controle/glossario não rodaram"
    return tuple(r for r in results if r.status == "falha")


def _own(rel: str) -> list:
    labels = _labels(rel) - JAPANESE_LABELS.get(rel, set())
    own = []
    for result in _failures():
        m = re.match(rf"{re.escape(rel)}: (\w+): ", result.detail)
        if m and m.group(1) in labels:
            own.append(result)
    return own


@pytest.mark.parametrize("rel", sorted(TRANSLATED))
def test_faixa_traduzida_sem_achados(rel):
    """Nenhum achado (largura, linhas, charmap, terminador, controle, glossário) nem inglês."""
    assert [f"{r.name}: {r.detail}" for r in _own(rel)] == []


@pytest.mark.parametrize("rel", sorted(TRANSLATED))
def test_faixa_nao_tem_mais_inglês(rel):
    entries = [e for e in ct._sources(REPO_ROOT) if isinstance(e, ct._Entry) and e.file == rel]
    allowed = ct._english_allowed_names([e for e in ct._sources(REPO_ROOT) if isinstance(e, ct._Entry)])
    labels = _labels(rel) - JAPANESE_LABELS.get(rel, set())
    left = {e.label: ct._english_words(e, allowed) for e in entries if e.label in labels}
    assert {label: words for label, words in left.items() if words} == {}


def test_ajuda_d1_mantem_a_faixa_toda():
    """A D1 traduziu todos os rótulos da faixa (cada um mudou em relação à base inglesa), menos o japonês."""
    rel = "data/text/help_system.inc"
    base = ct._load_base(REPO_ROOT, ct.TRANSLATION_BASE, {})
    assert not isinstance(base, str), base
    labels = _labels(rel) - JAPANESE_LABELS[rel]
    unchanged = []
    for label in sorted(labels):
        old = base.texts.get((rel, label)) if base is not None else None
        entry = next((e for e in ct._sources(REPO_ROOT) if isinstance(e, ct._Entry)
                      and e.file == rel and e.label == label), None)
        assert entry is not None, label
        if old == entry.texts:
            unchanged.append(label)
    # "PC", "Sair"... mudam sempre: nenhum rótulo da faixa pode ficar idêntico ao inglês
    assert unchanged == []
