"""POK-40 (status na batalha com L/R) e POK-41 (clima nos chefes): checagens estáticas."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _ler(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


def _funcao(texto, nome):
    m = re.search(r"^static \w+ " + nome + r"\([^;\n]*\)\n\{.*?\n\}\n", texto, re.M | re.S)
    assert m, nome
    return m.group(0)


def _rotulo(texto, nome):
    m = re.search(r"^" + nome + r"::\n(.*?)^\w+::", texto, re.M | re.S)
    assert m, nome
    return m.group(1)


def test_l_r_abrem_os_status_e_nao_a_ajuda():
    c = _ler("src/battle_controller_player.c")
    acao = _funcao(c, "HandleInputChooseAction")
    assert "gHelpSystemBattleLRBlocked = TRUE;" in acao
    # L/R vêm antes do A: no modo L=A o L continua sendo A
    assert acao.index("R_BUTTON") < acao.index("JOY_NEW(A_BUTTON)")
    assert "OPTIONS_BUTTON_MODE_L_EQUALS_A" in acao
    assert "gHelpSystemBattleLRBlocked = FALSE;" in _funcao(c, "PlayerBufferExecCompleted")
    ajuda = _ler("src/help_system_util.c")
    assert "(gMain.inBattle && gHelpSystemBattleLRBlocked)" in ajuda
    assert "extern bool8 gHelpSystemBattleLRBlocked;" in _ler("include/help_system.h")


def test_janela_dos_status_volta_ao_menu():
    c = _ler("src/battle_controller_player.c")
    janela = _funcao(c, "HandleInputShowStatStages")
    assert "gBattle_BG0_Y = 160;" in janela
    assert "gBattlerControllerFuncs[gActiveBattler] = HandleInputChooseAction;" in janela
    montar = _funcao(c, "BuildStatStagesString")
    assert "DEFAULT_STAT_STAGE" in montar and "STAT_STAGES_LINE_WIDTH" in montar
    # sete status de batalha, um rótulo para cada
    for stat in ("ATK", "DEF", "SPEED", "SPATK", "SPDEF", "ACC", "EVASION"):
        assert f"[STAT_{stat}]" in c


def test_ia_le_ceu_limpo():
    c = _ler("src/battle_ai_script_commands.c")
    clima = _funcao(c, "Cmd_get_weather")
    assert clima.index("WEATHER_TYPE_NONE") < clima.index("B_WEATHER_RAIN")
    assert "#define AI_WEATHER_NONE      4" in _ler("include/constants/battle_ai.h")
    s = _ler("data/battle_ai_scripts.s")
    sol = _rotulo(s, "AI_CV_SunnyDay")
    assert "AI_WEATHER_NONE" in sol and "ABILITY_CHLOROPHYLL" in sol and "MOVE_SOLAR_BEAM" in sol and "TYPE_FIRE" in sol
    chuva = _rotulo(s, "AI_CV_RainDance2")
    assert "AI_WEATHER_NONE" in chuva and "ABILITY_SWIFT_SWIM" in chuva and "MOVE_THUNDER" in chuva and "TYPE_WATER" in chuva


def test_times_de_clima():
    p = _ler("src/data/trainer_parties.h")
    misty = re.search(r"sParty_LeaderMisty\[\] = \{(.*?)\n\};", p, re.S).group(1)
    blaine = re.search(r"sParty_LeaderBlaine\[\] = \{(.*?)\n\};", p, re.S).group(1)
    assert "MOVE_RAIN_DANCE" in misty and "MOVE_THUNDER" in misty and "SPECIES_GOLDEEN" in misty
    assert "MOVE_SUNNY_DAY" in blaine and "MOVE_SOLAR_BEAM" in blaine and "SPECIES_EXEGGUTOR" in blaine
    # o primeiro Pokémon de cada um abre o clima
    assert "RAIN_DANCE" in re.search(r"\.moves = \{(.*?)\}", misty).group(1)
    assert "SUNNY_DAY" in re.search(r"\.moves = \{(.*?)\}", blaine).group(1)
