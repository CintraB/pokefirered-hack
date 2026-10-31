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
    bruto = {c: v for c, v in json.loads(TEMAS.read_text(encoding="utf-8")).items() if not c.startswith("_")}
    for c, v in bruto.items():  # apelido aponta para uma lista de verdade (um nível só)
        if isinstance(v, str):
            assert isinstance(bruto.get(v), list), (c, v)
    temas = g.temas()
    assert set(temas) == set(bruto)
    classes = {g.classe(linha[0]) for linha in g.ler_revanches()}
    assert len(classes) == 37
    assert classes <= set(temas), sorted(classes - set(temas))
    assert classes <= set(g.nomes_das_classes()), sorted(classes - set(g.nomes_das_classes()))
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
        for e in g.time_original("TRAINER_YOUNGSTER_BEN_4"):  # Ben tem 2 espécies: as duas ficam
            assert g.evoluir(e[1], nivel) in especies, (degrau, e)


def _linha(g, primeiro: str) -> int:
    return next(i for i, linha in enumerate(g.ler_revanches()) if linha[0] == primeiro)


def test_assinatura_no_maximo_3(g):
    """Leroy tem 5 espécies (Rhydon 52, Slowbro 54, Kangaskhan 52, Machamp 52, Ursaring 55): ficam o ás
    (Ursaring) e as 2 de maior nível (Slowbro; no empate em 52, o Rhydon, que vem antes), na ordem original."""
    leroy = _linha(g, "TRAINER_COOLTRAINER_LEROY")
    for degrau in range(1, 6):
        especies = [e for e, _, _, _ in g.time_vs(leroy, degrau)]
        assert especies[3:] == ["SPECIES_RHYDON", "SPECIES_SLOWBRO", "SPECIES_URSARING"], (degrau, especies)


def test_especies_melhores_por_degrau(g):
    """Ben (assinatura pequena): o complemento sai da faixa do degrau e o ás evoluído fica na posição 6."""
    ben = _linha(g, "TRAINER_YOUNGSTER_BEN")
    faixas = g.faixas(g.classe("TRAINER_YOUNGSTER_BEN"))
    for degrau in (1, 3, 5):
        time = g.time_vs(ben, degrau)
        faixa = faixas[g.regras()["faixa_por_degrau"][str(degrau)]]
        assert len(faixa) >= 4  # a faixa tem espécies novas para as 4 vagas do complemento
        assert all(e in faixa for e, _, _, _ in time[:4]), (degrau, time)
        assert time[5][0] == g.evoluir("SPECIES_ARBOK", g.niveis(degrau)[5])


def test_frutas_do_degrau_1_todas_aparecem(g):
    vistas = {it for i in range(len(g.ler_revanches())) for _, _, it, _ in g.time_vs(i, 1)[:5]}
    assert vistas == FRUTAS_DEGRAU_1 - {"ITEM_SITRUS_BERRY"}
    assert all(g.time_vs(i, 1)[5][2] == "ITEM_SITRUS_BERRY" for i in range(len(g.ler_revanches())))


def test_deterministico(g):
    assert g.amostra() == g.amostra()
