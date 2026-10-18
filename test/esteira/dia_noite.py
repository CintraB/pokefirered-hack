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


# --- Hack 7 frente A: tom de cor por período (src/day_night.c, Task 3) ------------------------
# Multiplicador por canal (r, g, b) em 1/256, como sPeriodTints (struct DayNightTint).
PERIOD_TINTS = {
    MORNING: (256, 240, 224),
    AFTERNOON: (256, 256, 256),
    EVENING: (256, 200, 168),
    NIGHT: (144, 152, 224),
}


def tint_at(minute: int) -> tuple[int, int, int]:
    """Tom do minuto do dia, como DayNight_GetTintAt: o do período, mas na última hora antes de
    cada limite (03h, 09h, 16h, 19h) interpola por minuto até o do período seguinte (a conta
    só usa valores positivos, então a divisão inteira é igual à do C)."""
    minute %= MINUTES_PER_DAY
    period = period_at(minute)
    following = period_at((minute // 60 + 1) * 60)
    cur = PERIOD_TINTS[period]
    if following == period:
        return cur
    k = minute % 60
    return tuple((c * (60 - k) + n * k) // 60 for c, n in zip(cur, PERIOD_TINTS[following]))


def tint_color(color: int, tint: tuple[int, int, int]) -> int:
    """Uma cor BGR555 com o tom aplicado uma vez (DayNight_TintPaletteBuffer): canal × coef >> 8,
    limitado a 31; o bit 15 fica como estava."""
    channels = (color & 31, (color >> 5) & 31, (color >> 10) & 31)
    r, g, b = (min(31, v * t >> 8) for v, t in zip(channels, tint))
    return (color & 0x8000) | b << 10 | g << 5 | r
