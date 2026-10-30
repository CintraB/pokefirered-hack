#ifndef GUARD_BATTLE_WEATHER_VISUAL_H
#define GUARD_BATTLE_WEATHER_VISUAL_H

// POK-15: the battle weather stays on screen (particles or a warm tint) while it lasts

enum {
    BWV_NONE,
    BWV_RAIN,
    BWV_HAIL,
    BWV_SAND,
    BWV_SUN,
};

#define BWV_MAX_SPRITES 12

struct BattleWeatherVisual
{
    u8 shown;       // BWV_*
    u8 count;       // live particles in spriteIds
    u8 spriteIds[BWV_MAX_SPRITES];
    bool8 sunApplied;
    u16 loadedTag;  // particle gfx tag this module loaded (0 = none or loaded by someone else)
    u32 tintMask;   // palettes tinted by the sun (or darkened by the rain), restored from Unfaded
};

extern struct BattleWeatherVisual gBattleWeatherVisual;

void BattleWeatherVisual_Reset(void);
void BattleWeatherVisual_Suspend(void);
void BattleWeatherVisual_Update(void);
u8 BattleWeatherVisual_GetWanted(void);

#endif // GUARD_BATTLE_WEATHER_VISUAL_H
