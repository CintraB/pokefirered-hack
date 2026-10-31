"""Revanches por degrau (POK-42), Task 1: o gerador de times, as regras e as listas temáticas.

`tools/revanches/gerar.py` lê `sRematches` (src/vs_seeker.c), os times atuais, a tabela de evoluções e os
atributos base, e monta os times do Vs. Seeker por degrau (1–5) com `tools/revanches/regras.json` e
`tools/revanches/temas.json`. Aqui só se testa o Python (sem emulador nem header gerado).
"""

import importlib.util
import json
import re

import pytest

from esteira.scenarios import REPO_ROOT

GERAR = REPO_ROOT / "tools" / "revanches" / "gerar.py"
TEMAS = REPO_ROOT / "tools" / "revanches" / "temas.json"
ITEMS_H = REPO_ROOT / "include" / "constants" / "items.h"
SPECIES_H = REPO_ROOT / "include" / "constants" / "species.h"

# Global Constraints do plano: lendários e míticos ficam de fora das listas.
LENDARIOS = {f"SPECIES_{n}" for n in (
    "ARTICUNO", "ZAPDOS", "MOLTRES", "MEWTWO", "MEW", "RAIKOU", "ENTEI", "SUICUNE", "LUGIA", "HO_OH", "CELEBI",
    "REGIROCK", "REGICE", "REGISTEEL", "LATIAS", "LATIOS", "KYOGRE", "GROUDON", "RAYQUAZA", "JIRACHI", "DEOXYS")}
FRUTAS_DEGRAU_1 = {f"ITEM_{n}_BERRY" for n in ("CHERI", "CHESTO", "PECHA", "RAWST", "ASPEAR", "PERSIM", "SITRUS")}


@pytest.fixture(scope="module")
def g():
    spec = importlib.util.spec_from_file_location("revanches_gerar", GERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _especies_validas() -> set[str]:
    """SPECIES_BULBASAUR..SPECIES_CELEBI e SPECIES_TREECKO..SPECIES_CHIMECHO, sem lendários."""
    texto = SPECIES_H.read_text(encoding="utf-8")
    num = {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (SPECIES_\w+) (\d+)\b", texto, re.M)}
    faixas = ((num["SPECIES_BULBASAUR"], num["SPECIES_CELEBI"]), (num["SPECIES_TREECKO"], num["SPECIES_CHIMECHO"]))
    return {s for s, n in num.items() if any(a <= n <= b for a, b in faixas)} - LENDARIOS


def _itens() -> set[str]:
    texto = ITEMS_H.read_text(encoding="utf-8")
    return set(re.findall(r"^#define (ITEM_\w+) \d+\b", texto, re.M)) - {"ITEM_NONE"}


def test_evolui_pelo_nivel(g, monkeypatch):
    assert g.evoluir("SPECIES_RATTATA", 90) == "SPECIES_RATICATE"
    assert g.evoluir("SPECIES_KADABRA", 57) == "SPECIES_ALAKAZAM"
    assert g.evoluir("SPECIES_ONIX", 57) == "SPECIES_STEELIX"
    assert g.evoluir("SPECIES_GOLBAT", 57) == "SPECIES_CROBAT"
    assert g.evoluir("SPECIES_PICHU", 57) == "SPECIES_RAICHU"
    assert g.evoluir("SPECIES_NINCADA", 57) == "SPECIES_NINJASK"
    monkeypatch.setitem(g.regras(), "ramos", {})
    with pytest.raises(ValueError, match="SPECIES_GLOOM"):
        g.evoluir("SPECIES_GLOOM", 57)


def test_niveis_do_degrau(g):
    assert g.niveis(1) == [57, 57, 58, 58, 59, 62]
    assert g.niveis(5) == [97, 97, 98, 98, 99, 100]
    assert g.niveis(5, "campeao") == [99, 99, 100, 100, 100, 100]


def test_iv_por_degrau(g):
    assert [g.iv(d) for d in range(1, 6)] == [20, 24, 27, 30, 31]


def test_item_reserva_fada(g):
    assert g.item("SPECIES_CLEFABLE", 3, 0) == "ITEM_LEFTOVERS"
    assert g.item("SPECIES_CHARIZARD", 3, 0) == "ITEM_CHARCOAL"
    itens = _itens()
    for especie in sorted(_especies_validas()):
        for pos in range(6):
            assert g.item(especie, 1, pos) in FRUTAS_DEGRAU_1, (especie, pos)
            for degrau in range(1, 6):
                it = g.item(especie, degrau, pos)
                assert it in itens, (especie, degrau, pos, it)


def test_temas_validos(g):
    temas = json.loads(TEMAS.read_text(encoding="utf-8"))
    classes = {g.classe(linha[0]) for linha in g.ler_revanches()}
    assert len(classes) == 37
    assert classes <= set(temas), sorted(classes - set(temas))
    validas = _especies_validas()
    for classe, lista in temas.items():
        assert len(lista) >= 10, classe
        assert len(set(lista)) == len(lista), classe
        assert set(lista) <= validas, (classe, sorted(set(lista) - validas))


def test_time_vs(g):
    linhas = g.ler_revanches()
    assert len(linhas) == 221
    for i in range(len(linhas)):
        for degrau in range(1, 6):
            time = g.time_vs(i, degrau)
            especies = [e for e, _, _, _ in time]
            assert len(time) == 6 and len(set(especies)) == 6, (linhas[i][0], degrau, especies)
            assert [n for _, n, _, _ in time] == g.niveis(degrau)
            assert all(v == g.iv(degrau) for _, _, _, v in time)
            assert all(g.evoluir(e, n) == e for e, n, _, _ in time), (linhas[i][0], degrau, time)
    ben = next(i for i, linha in enumerate(linhas) if linha[0] == "TRAINER_YOUNGSTER_BEN")
    assert linhas[ben][-1] == "TRAINER_YOUNGSTER_BEN_4"
    for degrau in range(1, 6):
        especies = [e for e, _, _, _ in g.time_vs(ben, degrau)]
        nivel = g.niveis(degrau)[0]
        for e in g.time_original("TRAINER_YOUNGSTER_BEN_4"):
            assert g.evoluir(e[1], nivel) in especies, (degrau, e)


def test_deterministico(g):
    assert g.amostra() == g.amostra()
