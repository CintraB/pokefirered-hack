"""Hack 8: Mew, Celebi e Jirachi no endgame (e o Mewtwo voltando pelo Hall da Fama).

Testes estáticos: travam os specials, scripts e flags. O comportamento é conferido no emulador.
"""

import re

from esteira.scenarios import REPO_ROOT


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


# Task 1 — specials de período do dia, céu limpo e espécie capturada ---------------------------

SPECIALS_T1 = ("GetDayNightPeriodForScript", "IsSkyClear", "IsSpeciesCaught")
# Climas que não são "céu limpo": chuva, tempestade, neblina, neve, areia, granizo (e cinza vulcânica).
CLIMA_RUIM_T1 = re.compile(r"RAIN|THUNDERSTORM|DOWNPOUR|FOG|SNOW|SANDSTORM|HAIL|VOLCANIC_ASH")


def _func_body_t1(name: str) -> str:
    """Corpo da função C `name` em src/field_specials.c (da assinatura até a `}` na coluna 0)."""
    src = _read("src/field_specials.c")
    m = re.search(rf"^\w[\w\s\*]*\b{name}\(void\)\n\{{\n(.*?)^\}}", src, re.M | re.S)
    assert m, f"função {name}(void) não encontrada em src/field_specials.c"
    return m.group(1)


def test_specials_registrados():
    specials = _read("data/specials.inc")
    header = _read("include/field_specials.h")
    for name in SPECIALS_T1:
        assert re.search(rf"^\s*def_special {name}\s*$", specials, re.M), f"{name} fora de data/specials.inc"
        assert re.search(rf"\b{name}\(void\);", header), f"{name} sem protótipo em include/field_specials.h"
        _func_body_t1(name)


def test_get_day_night_period_usa_hack7():
    assert "DayNight_GetPeriod()" in _func_body_t1("GetDayNightPeriodForScript")


def test_is_sky_clear_cobre_climas_ruins():
    weathers = re.findall(r"^#define (WEATHER_\w+)\s", _read("include/constants/weather.h"), re.M)
    ruins = [w for w in weathers if CLIMA_RUIM_T1.search(w)]
    assert ruins, "regex não achou nenhum clima ruim em weather.h"
    body = _func_body_t1("IsSkyClear")
    assert "GetCurrentWeather()" in body
    faltam = [w for w in ruins if not re.search(rf"\b{w}\b", body)]
    assert not faltam, f"IsSkyClear não trata: {faltam}"
    # céu limpo de verdade não pode estar na lista
    for bom in ("WEATHER_NONE", "WEATHER_SUNNY", "WEATHER_SUNNY_CLOUDS", "WEATHER_SHADE"):
        assert not re.search(rf"\b{bom}\b", body), f"IsSkyClear trata {bom} como clima ruim"


def test_is_species_caught_usa_flag_caught():
    body = _func_body_t1("IsSpeciesCaught")
    assert "gSpecialVar_0x8004" in body
    assert "FLAG_GET_CAUGHT" in body
    assert "SpeciesToNationalPokedexNum(" in body
    assert "GetSetPokedexFlag(" in body

# fim da Task 1 ------------------------------------------------------------------------------
