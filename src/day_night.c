#include "global.h"
#include "day_night.h"

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
