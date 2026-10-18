"""Espelho Python das regras do Hack 7 (dia/noite, clima e encontros por horário).

Relógio (include/constants/day_night.h, src/day_night.c): 150 quadros = 1 minuto do jogo
(1 dia do jogo = 1 h real a 60 quadros/s); o jogo novo (ou um save antigo) começa às 08:00 do
dia 0. Períodos: manhã 04–10, tarde 10–17, entardecer 17–20, noite 20–04.
"""

MORNING, AFTERNOON, EVENING, NIGHT = 0, 1, 2, 3     # TIME_* de include/constants/day_night.h
PERIOD_NAMES = ("manhã", "tarde", "entardecer", "noite")

FRAMES_PER_MINUTE = 150
MINUTES_PER_DAY = 1440
START_MINUTE = 8 * 60

MORNING_START_HOUR, AFTERNOON_START_HOUR, EVENING_START_HOUR, NIGHT_START_HOUR = 4, 10, 17, 20


def period_at(minute: int) -> int:
    """Período (MORNING..NIGHT) de um minuto do dia (0–1439), como DayNight_GetPeriodAt."""
    hour = (minute % MINUTES_PER_DAY) // 60
    if hour < MORNING_START_HOUR or hour >= NIGHT_START_HOUR:
        return NIGHT
    if hour < AFTERNOON_START_HOUR:
        return MORNING
    if hour < EVENING_START_HOUR:
        return AFTERNOON
    return EVENING
