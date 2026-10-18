#ifndef GUARD_DAY_NIGHT_H
#define GUARD_DAY_NIGHT_H

#include "constants/day_night.h"

u32 DayNight_GetTotalMinutes(void);
u32 DayNight_GetDay(void);
u32 DayNight_GetMinuteOfDay(void);
u8 DayNight_GetPeriodAt(u32 minuteOfDay);
u8 DayNight_GetPeriod(void);
bool8 DayNight_IsDayPeriod(u8 period);
void DayNight_SetClock(u32 day, u32 minuteOfDay);
void DayNight_Reset(void);
void DayNight_Tick(void);

#endif // GUARD_DAY_NIGHT_H
