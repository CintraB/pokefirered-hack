"""DexNav (POK-47), Task 5: as peças puras do cenário `dexnav` (sem emulador).

- `esteira.dexnav.comparar` (R4): a tolerância do `dexnav/chances_reais` é em desvios-padrão da binomial, não um
  ±3 p.p. fixo (que com 2000 sorteios e ~35 espécies dava ~20% de vermelho falso por rodada);
- `full_dexnav.taxa`: a média arredondada de `DexNav_RateForPeriods` (src/dexnav_data.c);
- as telas do cenário vão para o fim de `SHARED_POINTS` (referências em COMUM/).
"""

import math

from esteira import dexnav, refs
from esteira.scenarios import REPO_ROOT
from esteira.scenarios import full_dexnav as cen

DEXNAV_DATA_C = REPO_ROOT / "src" / "dexnav_data.c"


def test_tolerancia_em_sigma():
    n = 2000
    # p = 50%: σ = 100·√(0,25/2000) = 1,118 p.p.
    assert math.isclose(dexnav.tolerancia(50, n), dexnav.SIGMAS * 1.118034 + dexnav.ARREDONDAMENTO, rel_tol=1e-5)
    # cresce com p(1−p) e some nos extremos (só o arredondamento)
    assert dexnav.tolerancia(1, n) < dexnav.tolerancia(10, n) < dexnav.tolerancia(50, n)
    assert dexnav.tolerancia(0, n) == dexnav.tolerancia(100, n) == dexnav.ARREDONDAMENTO
    assert 4 <= dexnav.SIGMAS <= 5


def test_comparar():
    n = 2000
    esperado = {1: 500, 2: 300, 3: 200}   # ‰
    # dentro: 4 p.p. de desvio em 50% (3,6 σ)
    assert dexnav.comparar(esperado, {1: 1080, 2: 560, 3: 360}, n) == []
    # fora: 6 p.p. em 50% (5,4 σ)
    fora = dexnav.comparar(esperado, {1: 1120, 2: 520, 3: 360}, n)
    assert [f[0] for f in fora] == [1] and fora[0][1:3] == (50.0, 56.0)
    # espécie que não devia aparecer, ou chance 100% que falha uma vez
    assert {f[0] for f in dexnav.comparar({1: 1000}, {1: 1999, 9: 1}, n)} == {1, 9}
    # espécie com chance que nunca saiu (1% em 2000: esperado 20 vezes)
    assert [f[0] for f in dexnav.comparar({1: 990, 2: 10}, {1: 2000}, n)] == [2]


def test_taxa_igual_ao_c():
    fonte = DEXNAV_DATA_C.read_text(encoding="utf-8")
    assert "return (sum + count / 2) / count;" in fonte
    assert cen.taxa([450, 450, 0], cen.DIA) == 450
    assert cen.taxa([450, 450, 0], cen.TARDE_NOITE) == 225
    assert cen.taxa([0, 0, 450], cen.TARDE_NOITE) == 225
    assert cen.taxa([300, 300, 550], cen.TARDE_NOITE) == 425
    assert cen.taxa([175, 175, 0], cen.MANHA | cen.DIA) == 175
    assert cen.taxa([1, 0, 0], cen.MANHA | cen.NOITE) == 1   # (1 + 0 + 1) // 2: arredonda para cima no meio
    assert cen.taxa([500, 500, 500], 0) == 0


def test_telas_no_fim_de_shared_points():
    assert cen.SCREEN_POINTS == ("dexnav_mapa", "dexnav_lista", "dexnav_busca_resultado", "dexnav_menu_start")
    # depois deles, só os do seguidor (POK-48), do Pokérus (POK-50) e do POK-51
    fim = (len(refs.SHARED_POINTS) - len(refs.SEGUIDOR_POINTS) - len(refs.POKERUS_POINTS) - len(refs.FAMILIA_POINTS)
           - len(refs.CASAS_POINTS) - len(refs.ESPECIES_POINTS))   # e os do POK-54
    assert refs.SHARED_POINTS[fim - len(cen.SCREEN_POINTS):fim] == cen.SCREEN_POINTS
    assert len(set(refs.SHARED_POINTS)) == len(refs.SHARED_POINTS)
    texto = (REPO_ROOT / "test" / "esteira" / "scenarios" / "full_dexnav.py").read_text(encoding="utf-8")
    for ponto in cen.SCREEN_POINTS:
        assert f'self._shot("{ponto}")' in texto, ponto


def test_resultado_fora_do_horario_nos_124_mapas():
    """R14, no espelho (`full_dexnav.linha_resultado`, o mesmo do cenário) e nos 124 mapas: em qualquer horário de
    agora (manhã, tarde, tarde-noite, noite), um resultado que não aparece agora mostra a chance de UM período em que
    ele aparece, a maior delas, com o nome dos períodos que têm essa chance. A versão antiga (a média dos períodos)
    mostrava 20% para o Spinarak da Rota 2 (manhã 4%, noite 36%), uma chance que não existe em hora nenhuma."""
    g = cen._gerar()
    vistos_diferentes = 0
    for mapa in g.mapas():
        for e in g.enumerar(mapa["id"], tanoby_liberado=True):
            ch, per = e["chances"], e["periodos"]
            individuais = {i: ch[i] for i in range(3) if per >> i & 1}
            for bits in (cen.MANHA, cen.DIA, cen.TARDE_NOITE, cen.NOITE):
                agora, chance, mostrados = cen.linha_resultado(ch, per, bits)
                if agora:
                    assert (chance, mostrados) == (cen.taxa(ch, bits), per)
                    continue
                assert chance in individuais.values() and chance == max(individuais.values()), (mapa["id"], e)
                assert mostrados and mostrados & ~per == 0, (mapa["id"], e, mostrados)
                assert all(individuais[i] == chance for i in range(3) if mostrados >> i & 1)
                assert all(individuais[i] < chance for i in individuais if not mostrados >> i & 1)
                if len(set(individuais.values())) > 1:
                    vistos_diferentes += 1
                    assert chance != cen.taxa(ch, per), (mapa["id"], e)   # a média antiga mentia aqui
    assert vistos_diferentes > 0
    # o caso do relatório da revisão
    spinarak = next(e for e in g.enumerar("MAP_ROUTE2") if e["especie"] == "SPECIES_SPINARAK")
    assert spinarak["periodos"] == cen.MANHA | cen.NOITE and spinarak["chances"][0] != spinarak["chances"][2]
    assert cen.linha_resultado(spinarak["chances"], spinarak["periodos"], cen.DIA) == \
        (False, max(spinarak["chances"]), cen.NOITE)
