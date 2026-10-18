"""Hack 7 sem emulador: o relógio do jogo (períodos, constantes do C, campo no save, tick).

O espelho Python (esteira/dia_noite.py) tem de seguir as regras do design: manhã 04–10,
tarde 10–17, entardecer 17–20, noite 20–04; 150 quadros por minuto do jogo; começo 08:00.
"""

import re

from esteira import breeding as br
from esteira import dia_noite as dn
from esteira.scenarios import REPO_ROOT

GLOBAL_H = (REPO_ROOT / "include" / "global.h").read_text(encoding="utf-8")
PLAY_TIME_C = (REPO_ROOT / "src" / "play_time.c").read_text(encoding="utf-8")


def test_periodos_nos_limites():
    casos = {
        239: dn.NIGHT, 240: dn.MORNING, 599: dn.MORNING, 600: dn.AFTERNOON,
        1019: dn.AFTERNOON, 1020: dn.EVENING, 1199: dn.EVENING, 1200: dn.NIGHT, 1439: dn.NIGHT,
    }
    for minuto, periodo in casos.items():
        assert dn.period_at(minuto) == periodo, (minuto, dn.PERIOD_NAMES[dn.period_at(minuto)])


def test_constantes_do_c_batem():
    defines = br.header_defines(REPO_ROOT, "day_night.h")
    assert defines["GAME_CLOCK_FRAMES_PER_MINUTE"] == dn.FRAMES_PER_MINUTE == 150
    assert defines["MINUTES_PER_DAY"] == 1440
    assert (defines["MORNING_START_HOUR"], defines["AFTERNOON_START_HOUR"],
            defines["EVENING_START_HOUR"], defines["NIGHT_START_HOUR"]) == (4, 10, 17, 20)
    assert (defines["TIME_MORNING"], defines["TIME_AFTERNOON"], defines["TIME_EVENING"],
            defines["TIME_NIGHT"], defines["TIME_PERIOD_COUNT"]) == (
        dn.MORNING, dn.AFTERNOON, dn.EVENING, dn.NIGHT, 4)
    text = (REPO_ROOT / "include" / "constants" / "day_night.h").read_text(encoding="utf-8")
    m = re.search(r"^#define\s+GAME_CLOCK_START_MINUTE\s+\((\d+)\s*\*\s*(\d+)\)", text, re.M)
    assert m, "GAME_CLOCK_START_MINUTE não está no formato (H * 60)"
    assert int(m.group(1)) * int(m.group(2)) == dn.START_MINUTE == 480


def test_save_campo_no_filler():
    assert re.search(r"/\*0x090\*/\s*u32 gameClockFrames;", GLOBAL_H)
    assert re.search(r"/\*0x094\*/\s*u8 filler_94\[0x4\];", GLOBAL_H)
    assert re.search(r"/\*0x098\*/\s*struct Time localTimeOffset;", GLOBAL_H)
    assert "filler_90" not in GLOBAL_H


def test_tick_no_play_time():
    """O relógio anda com o contador de tempo de jogo ligado (RUNNING) e também depois que ele
    trava em 999:59 (MAXED_OUT): só para em STOPPED."""
    corpo = re.search(r"void PlayTimeCounter_Update\(void\)\n\{(.*?)\n\}", PLAY_TIME_C, re.S)
    assert corpo, "PlayTimeCounter_Update não encontrado"
    texto = corpo.group(1)
    assert texto.count("DayNight_Tick();") == 1
    assert re.search(r"if \(sPlayTimeCounterState != STOPPED\)\s*\{?\s*DayNight_Tick\(\);", texto), (
        "DayNight_Tick() tem de estar sob `if (sPlayTimeCounterState != STOPPED)`")
    ramo = re.search(r"if \(sPlayTimeCounterState == RUNNING\)\s*\{(.*)\}", texto, re.S)
    assert ramo, "ramo RUNNING não encontrado"
    assert "DayNight_Tick();" not in ramo.group(1)


def test_jogo_novo_zera_o_relogio():
    """Jogo novo por cima de um save existente não herda o relógio: NewGameInitData zera junto
    com o tempo de jogo, e DayNight_Reset volta a 08:00 do dia 0 (gameClockFrames = 0)."""
    new_game = (REPO_ROOT / "src" / "new_game.c").read_text(encoding="utf-8")
    corpo = re.search(r"void NewGameInitData\(void\)\n\{(.*?)\n\}", new_game, re.S)
    assert corpo, "NewGameInitData não encontrado"
    assert "PlayTimeCounter_Reset();" in corpo.group(1)
    assert "DayNight_Reset();" in corpo.group(1)
    day_night = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
    reset = re.search(r"void DayNight_Reset\(void\)\n\{(.*?)\n\}", day_night, re.S)
    assert reset, "DayNight_Reset não encontrado"
    assert re.fullmatch(r"\s*gSaveBlock2Ptr->gameClockFrames = 0;\s*", reset.group(1))


def test_cenario_relogio_registrado():
    from esteira import __main__ as cli
    spec = next(s for s in cli.FULL_SCENARIOS if s.name == "relogio")
    assert (spec.rom, spec.save_from) == (cli.TEST, "captura")
    assert spec.run.__name__ == "run_full_clock"
    assert "relogio" in cli.WATCH_FULL_SCENARIOS
