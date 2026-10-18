#include "global.h"
#include "gflib.h"
#include "day_night.h"
#include "characters.h"
#include "event_object_movement.h"
#include "field_effect.h"
#include "field_weather.h"
#include "fieldmap.h"
#include "graphics.h"
#include "map_name_popup.h"
#include "overworld.h"
#include "quest_log.h"
#include "script.h"
#include "strings.h"
#include "constants/quest_log.h"
#include "constants/weather.h"

// The in-game clock: gSaveBlock2Ptr->gameClockFrames counts the frames played since 08:00 of
// day 0, advanced by DayNight_Tick every frame the play time counter is not stopped (it keeps
// going after play time maxes out at 999:59).

u32 DayNight_GetTotalMinutes(void)
{
    return gSaveBlock2Ptr->gameClockFrames / GAME_CLOCK_FRAMES_PER_MINUTE + GAME_CLOCK_START_MINUTE;
}

u32 DayNight_GetDay(void)
{
    return DayNight_GetTotalMinutes() / MINUTES_PER_DAY;
}

u32 DayNight_GetMinuteOfDay(void)
{
    return DayNight_GetTotalMinutes() % MINUTES_PER_DAY;
}

u8 DayNight_GetPeriodAt(u32 minuteOfDay)
{
    u32 hour = (minuteOfDay % MINUTES_PER_DAY) / 60;

    if (hour < MORNING_START_HOUR || hour >= NIGHT_START_HOUR)
        return TIME_NIGHT;
    if (hour < AFTERNOON_START_HOUR)
        return TIME_MORNING;
    if (hour < EVENING_START_HOUR)
        return TIME_AFTERNOON;
    return TIME_EVENING;
}

u8 DayNight_GetPeriod(void)
{
    return DayNight_GetPeriodAt(DayNight_GetMinuteOfDay());
}

bool8 DayNight_IsDayPeriod(u8 period)
{
    return period == TIME_MORNING || period == TIME_AFTERNOON;
}

// A time before the clock's start (08:00 of day 0) is clamped to the start
void DayNight_SetClock(u32 day, u32 minuteOfDay)
{
    u32 total = day * MINUTES_PER_DAY + minuteOfDay;

    if (total < GAME_CLOCK_START_MINUTE)
        total = GAME_CLOCK_START_MINUTE;
    gSaveBlock2Ptr->gameClockFrames = (total - GAME_CLOCK_START_MINUTE) * GAME_CLOCK_FRAMES_PER_MINUTE;
}

// 08:00 of day 0 (new game)
void DayNight_Reset(void)
{
    gSaveBlock2Ptr->gameClockFrames = 0;
}

void DayNight_Tick(void)
{
    gSaveBlock2Ptr->gameClockFrames++;
}

/* Hack 7 — frente A */
#define PERIOD_NONE 0

EWRAM_DATA u8 gDayNightClockText[20] = {0};
EWRAM_DATA u8 gDayNightPopupPeriod = 0;
static u8 sSeenPeriod; // period + 1, 0 = none yet

// "HH:MM Period"
void DayNight_FormatClock(u8 *dest)
{
    u32 minute = DayNight_GetMinuteOfDay();

    dest = ConvertIntToDecimalStringN(dest, minute / 60, STR_CONV_MODE_LEADING_ZEROS, 2);
    *dest++ = CHAR_COLON;
    dest = ConvertIntToDecimalStringN(dest, minute % 60, STR_CONV_MODE_LEADING_ZEROS, 2);
    *dest++ = CHAR_SPACE;
    StringCopy(dest, gText_DayNight_PeriodName[DayNight_GetPeriodAt(minute)]);
}

// Called when entering the field (new game, continue, door, end of battle, return from a
// screen): the next update only records the current period, with no notice; also clears the
// last-notice period for the test hooks (0xFF = none; EWRAM_DATA cannot start non-zero)
void DayNight_ForgetSeenPeriod(void)
{
    sSeenPeriod = PERIOD_NONE;
    gDayNightPopupPeriod = 0xFF;
}

// Field palette tone. The tint points (ApplyGlobalTintToPaletteEntries/Slot in fieldmap.c,
// ApplyGlobalFieldPaletteTint in field_effect.c) run right after a palette is loaded from ROM, so
// each color is tinted once; when the tone changes in the field, TryRetintField reloads the
// palettes from ROM instead of tinting them again.
static const struct DayNightTint sPeriodTints[TIME_PERIOD_COUNT] =
{
    [TIME_MORNING]   = {256, 240, 224},
    [TIME_AFTERNOON] = {256, 256, 256},
    [TIME_EVENING]   = {256, 200, 168},
    [TIME_NIGHT]     = {144, 152, 224},
};

static EWRAM_DATA struct DayNightTint sAppliedTint = {0}; // last tone given to a field palette
static EWRAM_DATA bool8 sTintSuspended = FALSE;

// The period's tone; in the last hour before a period starts it moves minute by minute to the
// next period's tone
void DayNight_GetTintAt(u32 minuteOfDay, struct DayNightTint *out)
{
    const struct DayNightTint *next;
    u8 period, nextPeriod;
    u32 k;

    minuteOfDay %= MINUTES_PER_DAY;
    period = DayNight_GetPeriodAt(minuteOfDay);
    nextPeriod = DayNight_GetPeriodAt((minuteOfDay / 60 + 1) * 60);
    *out = sPeriodTints[period];
    if (nextPeriod != period)
    {
        next = &sPeriodTints[nextPeriod];
        k = minuteOfDay % 60;
        out->r = (out->r * (60 - k) + next->r * k) / 60;
        out->g = (out->g * (60 - k) + next->g * k) / 60;
        out->b = (out->b * (60 - k) + next->b * k) / 60;
    }
}

bool8 DayNight_ShouldTintCurrentMap(void)
{
    return !sTintSuspended && IsMapTypeOutdoors(gMapHeader.mapType);
}

// For palettes loaded with the field map header but shown off the field (Fame Checker)
void DayNight_SuspendTint(bool8 suspend)
{
    sTintSuspended = suspend;
}

// Only for a buffer just loaded from ROM
void DayNight_TintPaletteBuffer(u16 *pal, u16 count)
{
    struct DayNightTint tint;
    u32 r, g, b;

    DayNight_GetTintAt(DayNight_GetMinuteOfDay(), &tint);
    sAppliedTint = tint;
    for (; count != 0; count--, pal++)
    {
        r = ((*pal & 0x1F) * tint.r) >> 8;
        g = (((*pal >> 5) & 0x1F) * tint.g) >> 8;
        b = (((*pal >> 10) & 0x1F) * tint.b) >> 8;
        if (r > 31)
            r = 31;
        if (g > 31)
            g = 31;
        if (b > 31)
            b = 31;
        *pal = (*pal & 0x8000) | (b << 10) | (g << 5) | r;
    }
}

static void ReloadFieldEffectPalette(const struct SpritePalette *palette)
{
    u8 index = IndexOfSpritePaletteTag(palette->tag);

    if (index == 0xFF)
        return;
    LoadPalette(palette->data, OBJ_PLTT_ID(index), PLTT_SIZE_4BPP);
    ApplyGlobalFieldPaletteTint(index);
    UpdateSpritePaletteWithWeather(index);
}

// The tone changed (transition minute or new period): reload the field palettes from ROM, which
// tints them with the new tone, and redo the weather's gamma, as LoadMapFromCameraTransition does
static void TryRetintField(void)
{
    struct DayNightTint tint;
    u8 i;

    if (!DayNight_ShouldTintCurrentMap() || gGlobalFieldTintMode != QL_TINT_NONE
     || gPaletteFade.active || gWeatherPtr->palProcessingState != WEATHER_PAL_STATE_IDLE
     || ArePlayerFieldControlsLocked())
        return;
    DayNight_GetTintAt(DayNight_GetMinuteOfDay(), &tint);
    if (tint.r == sAppliedTint.r && tint.g == sAppliedTint.g && tint.b == sAppliedTint.b)
        return;

    LoadMapTilesetPalettes(gMapHeader.mapLayout);
    for (i = 0; i < NUM_PALS_TOTAL; i++)
        ApplyWeatherGammaShiftToPal(i);
    ReloadObjectEventPalettes();
    for (i = 0; i < OBJ_PALSLOT_COUNT; i++)
        UpdateSpritePaletteWithWeather(i);
    ReloadFieldEffectPalette(&gSpritePalette_GeneralFieldEffect0);
    ReloadFieldEffectPalette(&gSpritePalette_GeneralFieldEffect1);
    if (gWeatherPtr->currWeather == WEATHER_SUNNY_CLOUDS)
        LoadCustomWeatherSpritePalette(gCloudsWeatherPalette);
    else if (gWeatherPtr->currWeather == WEATHER_SANDSTORM)
        LoadCustomWeatherSpritePalette(gSandstormWeatherPalette);
    else
        LoadCustomWeatherSpritePalette(gDefaultWeatherSpritePalette);
}

void DayNight_FieldUpdate(void)
{
    u8 period;

    if (QL_IS_PLAYBACK_STATE)
        return;
    TryRetintField();
    period = DayNight_GetPeriod();
    if (sSeenPeriod == PERIOD_NONE)
    {
        sSeenPeriod = period + 1;
        return;
    }
    if (period + 1 == sSeenPeriod)
        return;
    if (ArePlayerFieldControlsLocked() || ScriptContext_IsEnabled() || gPaletteFade.active)
        return;
    sSeenPeriod = period + 1;
    gDayNightPopupPeriod = period;
    ShowFieldMessagePopup(gText_DayNight_PeriodStart[period]);
    DayNight_OnPeriodChange();
}

// Weather hook, filled in by the weather task
void DayNight_OnPeriodChange(void)
{
}
