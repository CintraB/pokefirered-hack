#include "global.h"
#include "gflib.h"
#include "battle.h"
#include "battle_anim.h"
#include "battle_weather_visual.h"
#include "decompress.h"
#include "random.h"
#include "constants/abilities.h"
#include "constants/battle_anim.h"

// POK-15: the battle weather stays on screen while it lasts, as in the newer games. Particles
// (rain, hail, sand) or a warm tint (sun) are created once the weather is active and no battle
// animation is running; LaunchBattleAnimation suspends them, so every move keeps the sprites,
// palettes and blend registers it expects, and they come back right after.

#define BWV_RAIN_COUNT 10
#define BWV_SUBPRIORITY 2   // OAM priority 1 like the healthboxes (subpriority 0-1): drawn behind them

// sprite->data
#define sSpeedX data[0]
#define sSpeedY data[1]

EWRAM_DATA struct BattleWeatherVisual gBattleWeatherVisual = {0};

static void SpriteCB_RainDrop(struct Sprite *sprite);

static const union AnimCmd sAnim_RainDropFall[] =
{
    ANIMCMD_FRAME(16, 1), // the longest streak of rain_drops.png
    ANIMCMD_END,
};

static const union AnimCmd *const sAnims_RainDropFall[] =
{
    sAnim_RainDropFall,
};

static const struct SpriteTemplate sRainDropSpriteTemplate =
{
    .tileTag = ANIM_TAG_RAIN_DROPS,
    .paletteTag = ANIM_TAG_RAIN_DROPS,
    .oam = &gOamData_AffineOff_ObjNormal_16x32,
    .anims = sAnims_RainDropFall,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCB_RainDrop,
};

void BattleWeatherVisual_Reset(void)
{
    // the sprites and palettes are already gone (new battle, or back from the bag/party screen)
    memset(&gBattleWeatherVisual, 0, sizeof(gBattleWeatherVisual));
}

void BattleWeatherVisual_Suspend(void)
{
    u8 i;

    for (i = 0; i < gBattleWeatherVisual.count; i++)
        DestroySprite(&gSprites[gBattleWeatherVisual.spriteIds[i]]);
    gBattleWeatherVisual.count = 0;
    if (gBattleWeatherVisual.loadedTag != 0)
    {
        FreeSpriteTilesByTag(gBattleWeatherVisual.loadedTag);
        FreeSpritePaletteByTag(gBattleWeatherVisual.loadedTag);
        gBattleWeatherVisual.loadedTag = 0;
    }
    gBattleWeatherVisual.shown = BWV_NONE;
}

static bool8 IsWeatherNegatedOnField(void)
{
    u8 i;

    for (i = 0; i < gBattlersCount; i++)
    {
        if (gBattleMons[i].hp != 0
         && (gBattleMons[i].ability == ABILITY_CLOUD_NINE || gBattleMons[i].ability == ABILITY_AIR_LOCK))
            return TRUE;
    }
    return FALSE;
}

static bool8 IsBattleAnimRunning(void)
{
    u8 i;

    if (gAnimScriptActive)
        return TRUE;
    if (gBattleSpritesDataPtr == NULL)
        return TRUE;
    for (i = 0; i < gBattlersCount; i++)
    {
        if (gBattleSpritesDataPtr->healthBoxesData[i].animFromTableActive
         || gBattleSpritesDataPtr->healthBoxesData[i].specialAnimActive
         || gBattleSpritesDataPtr->healthBoxesData[i].statusAnimActive)
            return TRUE;
    }
    return FALSE;
}

// Pure: what should be on screen now. No AbilityBattleEffects/WEATHER_HAS_EFFECT here, both write
// gLastUsedAbility and this runs every frame, in the middle of battle scripts.
u8 BattleWeatherVisual_GetWanted(void)
{
    if (gSaveBlock2Ptr->optionsBattleSceneOff || gBattleOutcome != 0 || gPaletteFade.active)
        return BWV_NONE;
    if (IsBattleAnimRunning())
        return BWV_NONE;
    if (IsWeatherNegatedOnField())
        return BWV_NONE;
    if (gBattleWeather & B_WEATHER_RAIN)
        return BWV_RAIN;
    return BWV_NONE;
}

static void LoadParticleGfx(u16 tag)
{
    if (GetSpriteTileStartByTag(tag) != TAG_NONE)
        return; // a battle animation loaded it and will free it
    LoadCompressedSpriteSheetUsingHeap(&gBattleAnimPicTable[GET_TRUE_SPRITE_INDEX(tag)]);
    LoadCompressedSpritePaletteUsingHeap(&gBattleAnimPaletteTable[GET_TRUE_SPRITE_INDEX(tag)]);
    gBattleWeatherVisual.loadedTag = tag;
}

static void CreateParticles(const struct SpriteTemplate *template, u8 count, s16 speedX, s16 speedY)
{
    u8 i, spriteId;

    LoadParticleGfx(template->tileTag);
    for (i = 0; i < count; i++)
    {
        // spread over the whole scene, so the weather is already falling when it appears
        spriteId = CreateSprite(template, Random() % DISPLAY_WIDTH, Random() % DISPLAY_HEIGHT, BWV_SUBPRIORITY);
        if (spriteId == MAX_SPRITES)
            break;
        gSprites[spriteId].oam.priority = 1;
        gSprites[spriteId].sSpeedX = speedX;
        gSprites[spriteId].sSpeedY = speedY;
        gBattleWeatherVisual.spriteIds[gBattleWeatherVisual.count++] = spriteId;
    }
}

void BattleWeatherVisual_Update(void)
{
    u8 wanted = BattleWeatherVisual_GetWanted();

    if (wanted == gBattleWeatherVisual.shown)
        return;
    BattleWeatherVisual_Suspend();
    switch (wanted)
    {
    case BWV_RAIN:
        // diagonal down to the right, along the streak drawn in rain_drops.png
        CreateParticles(&sRainDropSpriteTemplate, BWV_RAIN_COUNT, 2, 6);
        break;
    }
    gBattleWeatherVisual.shown = wanted;
}

// Falls and wraps around: back to the top at a random column once it leaves the scene
static void SpriteCB_RainDrop(struct Sprite *sprite)
{
    sprite->x += sprite->sSpeedX;
    sprite->y += sprite->sSpeedY;
    if (sprite->y > DISPLAY_HEIGHT + 16 || sprite->x < -16 || sprite->x > DISPLAY_WIDTH + 16)
    {
        sprite->x = Random() % (DISPLAY_WIDTH + 32);
        sprite->y = -16;
    }
}
