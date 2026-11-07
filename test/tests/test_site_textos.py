"""Página do Professor: o texto longo do Professor em cada cartão (POK-22, Task 5)."""
import importlib.util
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("site_gerar", REPO / "tools/site/gerar.py")
gerar_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerar_mod)

MINIMO, MAXIMO = 250, 1200
# Inglês comum que escapa na escrita (palavra inteira, sem diferenciar maiúsculas).
PROIBIDAS = ("the", "and", "trade", "level up")


def _cartoes():
    return [c for cap in gerar_mod.carregar_capitulos(REPO) for c in cap["cartoes"]]


def test_todo_cartao_tem_texto_longo():
    sem = [c["id"] for c in _cartoes() if not (c["longo"] or "").strip()]
    assert not sem, sem


def test_textos_sem_ingles_comum():
    for c in _cartoes():
        texto = (c["longo"] or "").lower()
        for palavra in PROIBIDAS:
            assert not re.search(rf"\b{palavra}\b", texto), (c["id"], palavra)


def test_tamanho():
    for c in _cartoes():
        n = len(c["longo"] or "")
        assert MINIMO <= n <= MAXIMO, (c["id"], n)


def test_longo_fora_do_spoiler_nao_revela_a_familia():
    """Chefes, desfecho e dossiê da Família Sombra só aparecem nos cartões recolhidos atrás do aviso."""
    revela = ("garchomp", "darkrai", "tyranitar", "cobrador", "mercenário", "pesadelo", "jenny", "dossiê")
    for c in _cartoes():
        if c["spoiler"]:
            continue
        texto = (c["longo"] or "").lower()
        assert not [p for p in revela if re.search(rf"\b{p}\b", texto)], c["id"]


def test_longo_e_texto_corrido():
    """Um parágrafo de texto real: sem quebra de linha nem marcação (o gerador escapa o HTML)."""
    textos = json.loads((REPO / "site/textos.json").read_text(encoding="utf-8"))
    for chave, extra in textos.items():
        longo = extra.get("longo", "")
        assert "\n" not in longo and "<" not in longo and "**" not in longo, chave
