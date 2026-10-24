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


def _block(src: str, label: str) -> str:
    """Corpo do rótulo `label::` até o próximo rótulo global."""
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    return src[start:start + len(label) + 2 + (m.start() if m else len(src))]


# Task 2: Mewtwo volta pelo Hall da Fama

CERULEAN = "data/maps/CeruleanCave_B1F/scripts.inc"


def _cerulean(label: str) -> str:
    return _block(_read(CERULEAN), f"CeruleanCave_B1F_{label}")


def test_mewtwo_flag_existe_sem_colisao():
    flags = _read("include/constants/flags.h")
    defs = re.findall(r"^#define (FLAG_\w+)\s+(0x[0-9A-Fa-f]+)\s*$", flags, re.M)
    valor = {n: int(v, 16) for n, v in defs}
    assert valor["FLAG_MEWTWO_FLEW_AWAY"] == 0x300
    iguais = [n for n, v in valor.items() if v == 0x300]
    assert iguais == ["FLAG_MEWTWO_FLEW_AWAY"], iguais


def test_mewtwo_volta_pelo_hall():
    hall = _block(_read("data/scripts/hall_of_fame.inc"), "EventScript_ResetLegendaries")
    assert "clearflag FLAG_MEWTWO_FLEW_AWAY" in hall


def test_mewtwo_derrotado_ou_fuga_ligam_flew_away():
    for label in ("EventScript_DefeatedMewtwo", "EventScript_RanFromMewtwo"):
        assert "setflag FLAG_MEWTWO_FLEW_AWAY" in _cerulean(label), label
    luta = _cerulean("EventScript_Mewtwo")
    assert "B_OUTCOME_WON, CeruleanCave_B1F_EventScript_DefeatedMewtwo" in luta
    assert "B_OUTCOME_RAN, CeruleanCave_B1F_EventScript_RanFromMewtwo" in luta
    assert "B_OUTCOME_PLAYER_TELEPORTED, CeruleanCave_B1F_EventScript_RanFromMewtwo" in luta


def test_mewtwo_derrotado_ou_fuga_nao_ligam_fought():
    # FOUGHT_MEWTWO passa a significar "capturado" (some para sempre).
    for label in ("EventScript_DefeatedMewtwo", "EventScript_RanFromMewtwo"):
        assert "FLAG_FOUGHT_MEWTWO" not in _cerulean(label), label


def test_mewtwo_capturado_liga_fought_e_nao_flew_away():
    luta = _cerulean("EventScript_Mewtwo")
    depois = luta[luta.index("B_OUTCOME_PLAYER_TELEPORTED"):]
    assert "setflag FLAG_FOUGHT_MEWTWO" in depois
    assert "FLAG_MEWTWO_FLEW_AWAY" not in depois


def test_mewtwo_mapa_esconde_e_mostra_como_o_lugia():
    trans = _cerulean("OnTransition")
    assert "call_if_set FLAG_FOUGHT_MEWTWO, CeruleanCave_B1F_EventScript_HideMewtwo" in trans
    assert "call_if_unset FLAG_FOUGHT_MEWTWO, CeruleanCave_B1F_EventScript_TryShowMewtwo" in trans
    assert "setflag FLAG_HIDE_MEWTWO" in _cerulean("EventScript_HideMewtwo")
    tenta = _cerulean("EventScript_TryShowMewtwo")
    assert tenta.index("goto_if_set FLAG_MEWTWO_FLEW_AWAY") < tenta.index("clearflag FLAG_HIDE_MEWTWO")


def test_hall_migra_save_antigo_em_que_o_mewtwo_foi_so_derrotado():
    # Save antigo: FOUGHT_MEWTWO ligada sem captura -> o Hall a desliga para ele voltar.
    c = _read("src/post_battle_event_funcs.c")
    corpo = c[c.index("bool8 EnterHallOfFame"):c.index("bool8 SetCB2WhiteOut")]
    assert "FlagGet(FLAG_FOUGHT_MEWTWO)" in corpo
    assert "FlagClear(FLAG_FOUGHT_MEWTWO)" in corpo
    assert "GetSetPokedexFlag(SpeciesToNationalPokedexNum(SPECIES_MEWTWO), FLAG_GET_CAUGHT)" in corpo
