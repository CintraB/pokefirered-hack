#include "global.h"
#include "gflib.h"
#include "day_night.h"
#include "characters.h"
#include "map_name_popup.h"
#include "quest_log.h"
#include "script.h"
#include "strings.h"

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

void DayNight_FieldUpdate(void)
{
    u8 period;

    if (QL_IS_PLAYBACK_STATE)
        return;
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
