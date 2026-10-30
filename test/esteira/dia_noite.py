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


# --- Hack 7 frente A: clima dinâmico por região (src/day_night.c, src/data/day_night_weather.h,
# Task 4) ---------------------------------------------------------------------------------------
# WEATHER_* de include/constants/weather.h
WEATHER_NONE, WEATHER_SUNNY_CLOUDS, WEATHER_SUNNY, WEATHER_RAIN, WEATHER_SNOW = 0, 1, 2, 3, 4
WEATHER_RAIN_THUNDERSTORM, WEATHER_FOG_HORIZONTAL, WEATHER_VOLCANIC_ASH = 5, 6, 7
WEATHER_SANDSTORM, WEATHER_SHADE, WEATHER_DROUGHT, WEATHER_DOWNPOUR = 8, 11, 12, 13
WEATHER_IDS = {name: value for name, value in globals().items() if name.startswith("WEATHER_")}
WEATHER_BY_ID = {value: name for name, value in WEATHER_IDS.items()}
OVERRIDABLE_WEATHER = (WEATHER_NONE, WEATHER_SUNNY, WEATHER_SUNNY_CLOUDS)

# WEATHER_REGION_* de include/constants/day_night.h
REGION_NONE, REGION_INLAND, REGION_COAST, REGION_OPEN_SEA = 0, 1, 2, 3
REGION_SNOW, REGION_SAND, REGION_VOLCANO, REGION_SEVII = 4, 5, 6, 7
REGION_NAMES = ("NONE", "INLAND", "COAST", "OPEN_SEA", "SNOW", "SAND", "VOLCANO", "SEVII")
REGION_COUNT = len(REGION_NAMES)

# MAPSEC_* com região própria (DayNight_GetWeatherRegion); os outros de Kanto são INLAND e os de
# SEVII_MAPSEC_START (MAPSEC_ONE_ISLAND) em diante, SEVII
REGION_MAPSECS = {
    REGION_COAST: ("MAPSEC_VERMILION_CITY", "MAPSEC_CERULEAN_CITY", "MAPSEC_ROUTE_24", "MAPSEC_ROUTE_25"),
    REGION_OPEN_SEA: ("MAPSEC_ROUTE_19", "MAPSEC_ROUTE_20", "MAPSEC_ROUTE_21"),
    REGION_SAND: ("MAPSEC_ROUTE_3", "MAPSEC_ROUTE_10"),
    REGION_VOLCANO: ("MAPSEC_CINNABAR_ISLAND", "MAPSEC_MT_EMBER"),
    REGION_SNOW: ("MAPSEC_FOUR_ISLAND",),
    REGION_NONE: ("MAPSEC_NAVEL_ROCK", "MAPSEC_BIRTH_ISLAND"),
}

_ALL_PERIODS = (MORNING, AFTERNOON, EVENING, NIGHT)
_COAST = {
    MORNING: ((WEATHER_NONE, 50), (WEATHER_RAIN, 30), (WEATHER_FOG_HORIZONTAL, 20)),
    AFTERNOON: ((WEATHER_NONE, 55), (WEATHER_SHADE, 10), (WEATHER_RAIN, 25), (WEATHER_RAIN_THUNDERSTORM, 10)),
    EVENING: ((WEATHER_NONE, 50), (WEATHER_RAIN, 30), (WEATHER_RAIN_THUNDERSTORM, 20)),
    NIGHT: ((WEATHER_NONE, 55), (WEATHER_RAIN, 30), (WEATHER_RAIN_THUNDERSTORM, 15)),
}
# (clima, peso) na ordem do sorteio cumulativo; os pesos de cada período somam 100
REGION_WEIGHTS = {
    REGION_INLAND: {
        MORNING: ((WEATHER_NONE, 70), (WEATHER_FOG_HORIZONTAL, 15), (WEATHER_RAIN, 15)),
        AFTERNOON: ((WEATHER_NONE, 75), (WEATHER_SHADE, 10), (WEATHER_RAIN, 10), (WEATHER_RAIN_THUNDERSTORM, 5)),
        EVENING: ((WEATHER_NONE, 75), (WEATHER_RAIN, 20), (WEATHER_RAIN_THUNDERSTORM, 5)),
        NIGHT: ((WEATHER_NONE, 75), (WEATHER_RAIN, 15), (WEATHER_FOG_HORIZONTAL, 10)),
    },
    REGION_COAST: _COAST,
    REGION_OPEN_SEA: {p: ((WEATHER_NONE, 60), (WEATHER_RAIN, 25), (WEATHER_RAIN_THUNDERSTORM, 10),
                          (WEATHER_DOWNPOUR, 5)) for p in _ALL_PERIODS},
    REGION_SNOW: {p: ((WEATHER_SNOW, 60), (WEATHER_NONE, 30), (WEATHER_FOG_HORIZONTAL, 10)) for p in _ALL_PERIODS},
    REGION_SAND: {
        MORNING: ((WEATHER_NONE, 70), (WEATHER_SANDSTORM, 30)),
        AFTERNOON: ((WEATHER_NONE, 50), (WEATHER_SANDSTORM, 50)),
        EVENING: ((WEATHER_NONE, 60), (WEATHER_SANDSTORM, 40)),
        NIGHT: ((WEATHER_NONE, 80), (WEATHER_SANDSTORM, 20)),
    },
    REGION_VOLCANO: {  # POK-16: sol forte de dia, nunca à noite
        MORNING: ((WEATHER_VOLCANIC_ASH, 40), (WEATHER_DROUGHT, 20), (WEATHER_NONE, 40)),
        AFTERNOON: ((WEATHER_VOLCANIC_ASH, 30), (WEATHER_DROUGHT, 40), (WEATHER_NONE, 30)),
        EVENING: ((WEATHER_VOLCANIC_ASH, 40), (WEATHER_DROUGHT, 15), (WEATHER_NONE, 45)),
        NIGHT: ((WEATHER_VOLCANIC_ASH, 50), (WEATHER_NONE, 50)),
    },
    REGION_SEVII: _COAST,
}

_U32 = 0xFFFFFFFF


def weather_hash(seed: int, region: int) -> int:
    """WeatherHash (lowbias32) em u32, como no C."""
    x = (seed ^ (region * 0x9E3779B9)) & _U32
    x ^= x >> 16
    x = (x * 0x7FEB352D) & _U32
    x ^= x >> 15
    x = (x * 0x846CA68B) & _U32
    x ^= x >> 16
    return x


def roll_from_hash(region: int, period: int, hashed: int) -> int:
    """Clima de um valor do hash: hash % 100 contra os pesos cumulativos da região."""
    roll = hashed % 100
    for weather, weight in REGION_WEIGHTS[region][period]:
        if roll < weight:
            return weather
        roll -= weight
    return WEATHER_NONE


def roll_weather(region: int, day: int, period: int) -> int:
    """Clima sorteado (DayNight_RollWeather): roll = hash(dia * 4 + período, região) % 100 contra
    os pesos cumulativos da região; região NONE → WEATHER_NONE. O dia 0 do clima (o do jogo novo,
    até 04:00 do dia 1) é sempre WEATHER_NONE, em todas as regiões (regra 15)."""
    if region not in REGION_WEIGHTS or day == 0:
        return WEATHER_NONE
    return roll_from_hash(region, period, weather_hash((day * 4 + period) & _U32, region))


def weather_day(day: int, minute: int) -> int:
    """Dia do sorteio do clima: começa às 04:00 (início da manhã), para a noite inteira (20h–04h)
    ser um sorteio só, sem troca à meia-noite."""
    return (day * MINUTES_PER_DAY + minute - MORNING_START_HOUR * 60) // MINUTES_PER_DAY


def map_weather(header: int, region: int, outdoors: bool, day: int, minute: int) -> int:
    """DayNight_GetMapWeather num relógio (dia, minuto do dia): o sorteio só substitui o clima do
    header num mapa externo, com header NONE/SUNNY/SUNNY_CLOUDS, região ≠ NONE e sorteio ≠ NONE."""
    if not outdoors or header not in OVERRIDABLE_WEATHER or region == REGION_NONE:
        return header
    rolled = roll_weather(region, weather_day(day, minute), period_at(minute))
    return header if rolled == WEATHER_NONE else rolled
