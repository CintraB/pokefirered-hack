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
