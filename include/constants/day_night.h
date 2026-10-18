#ifndef GUARD_CONSTANTS_DAY_NIGHT_H
#define GUARD_CONSTANTS_DAY_NIGHT_H

// Time-of-day periods (test/esteira/dia_noite.py mirrors these rules)
#define TIME_MORNING      0
#define TIME_AFTERNOON    1
#define TIME_EVENING      2
#define TIME_NIGHT        3
#define TIME_PERIOD_COUNT 4

// 150 frames per in-game minute: one in-game day lasts one real hour at 60 frames per second
#define GAME_CLOCK_FRAMES_PER_MINUTE 150
#define MINUTES_PER_DAY              1440

#define MORNING_START_HOUR   4
#define AFTERNOON_START_HOUR 10
#define EVENING_START_HOUR   17
#define NIGHT_START_HOUR     20

// A new game (or a save from before the clock existed, gameClockFrames = 0) starts at 08:00 of day 0
#define GAME_CLOCK_START_MINUTE (8 * 60)

#endif // GUARD_CONSTANTS_DAY_NIGHT_H
