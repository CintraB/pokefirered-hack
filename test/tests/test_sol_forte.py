"""POK-16 (sol forte no mapa): checagens estáticas das tabelas, do laço e do sorteio."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TABELAS = [RAIZ / f"graphics/weather/drought/colors_{n}.bin" for n in range(6)]


def _ler(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


def _funcao(texto, nome):
    m = re.search(r"^(?:static )?\w+ " + nome + r"\([^;\n]*\)\n\{.*?\n\}\n", texto, re.M | re.S)
    assert m, nome
    return m.group(0)


def _sem_comentarios(c):
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", c, flags=re.S)


VULCAO = {  # período: (cinzas, sol forte, limpo) em %, decisão do Cintra em 29/10
    "TIME_MORNING": (40, 20, 40),
    "TIME_AFTERNOON": (30, 40, 30),
    "TIME_EVENING": (40, 15, 45),
    "TIME_NIGHT": (50, 0, 50),
}


def test_vulcao_sorteia_sol_forte():
    from esteira import dia_noite as dn
    h = _ler("src/data/day_night_weather.h")
    bloco = re.search(r"\[WEATHER_REGION_VOLCANO\] =\s*\{(.*?)\n    \},", h.replace("\r", ""), re.S).group(1)
    periodos = ("TIME_MORNING", "TIME_AFTERNOON", "TIME_EVENING", "TIME_NIGHT")
    for i, periodo in enumerate(periodos):
        linha = re.search(r"\[" + periodo + r"\]\s*=\s*\{(.*)\},", bloco).group(1)
        pares = [(w, int(c)) for w, c in re.findall(r"\{(WEATHER_\w+), (\d+)\}", linha)]
        cinzas, sol, limpo = VULCAO[periodo]
        esperado = [("WEATHER_VOLCANIC_ASH", cinzas)] + ([("WEATHER_DROUGHT", sol)] if sol else []) + [("WEATHER_NONE", limpo)]
        assert pares == esperado, periodo
        espelho = [(dn.WEATHER_BY_ID[w], c) for w, c in dn.REGION_WEIGHTS[dn.REGION_VOLCANO][i]]
        assert espelho == esperado, periodo


def test_tabelas_do_sol_forte_existem():
    for t in TABELAS:
        assert t.stat().st_size == 0x1000 * 2, t.name
    assert any(TABELAS[0].read_bytes())


def test_tabelas_incluidas():
    c = _ler("src/field_weather.c")
    for n in range(6):
        assert f'INCBIN_U16("graphics/weather/drought/colors_{n}.bin")' in c


def test_laco_do_sol_forte_termina():
    corpo = _sem_comentarios(_funcao(_ler("src/field_weather.c"), "LoadDroughtWeatherPalette"))
    assert "*gammaIndexPtr = 0x20;" in corpo


def test_gamma_negativo_usa_a_tabela():
    c = _ler("src/field_weather.c")
    gamma = _sem_comentarios(_funcao(c, "ApplyGammaShift"))
    negativo = gamma[gamma.index("gammaIndex < 0"):]
    assert "sDroughtWeatherColors[" in negativo and "DROUGHT_COLOR_INDEX(" in negativo
    assert "sDroughtWeatherColors[" in _sem_comentarios(_funcao(c, "ApplyDroughtGammaShiftWithBlend"))
