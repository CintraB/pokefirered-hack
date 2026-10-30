#include "global.h"
#include "gflib.h"
#include "battle.h"
#include "battle_anim.h"
#include "battle_main.h"
#include "battle_weather_visual.h"
#include "decompress.h"
#include "random.h"
#include "trig.h"
#include "constants/abilities.h"
#include "constants/battle_anim.h"

// POK-15: the battle weather stays on screen while it lasts, as in the newer games. Particles
// (rain, hail, sand) or a warm tint (sun) are created once the weather is active and no battle
// animation is running; LaunchBattleAnimation suspends them, so every move keeps the sprites,
// palettes and blend registers it expects, and they come back right after.

#define BWV_RAIN_COUNT 10
#define BWV_HAIL_COUNT 8
#define BWV_SAND_COUNT 10
#define BWV_SUBPRIORITY 2   // OAM priority 1 like the healthboxes (subpriority 0-1): drawn behind them

// Scene tint, on the battle background and the battlers only (never the healthboxes or the text).
// The sun warms it up; the rain darkens it a little, as General_Rain does, so the drops show.
#define BWV_SUN_TINT RGB(31, 28, 16)
#define BWV_SUN_TINT_COEFF 3
#define BWV_RAIN_TINT_COEFF 3
// BG palettes 2-3 hold the terrain; palette 1 also frames the action and move menus
#define BWV_TERRAIN_PALETTES ((1 << 2) | (1 << 3))

// sprite->data
#define sSpeedX data[0]
#define sSpeedY data[1]
#define sWaveTimer data[2]

EWRAM_DATA struct BattleWeatherVisual gBattleWeatherVisual = {0};

static void SpriteCB_RainDrop(struct Sprite *sprite);
static void SpriteCB_Hail(struct Sprite *sprite);
static void SpriteCB_Sand(struct Sprite *sprite);

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

static const struct SpriteTemplate sHailSpriteTemplate =
{
    .tileTag = ANIM_TAG_HAIL,
    .paletteTag = ANIM_TAG_HAIL,
    .oam = &gOamData_AffineOff_ObjNormal_16x16,
    .anims = gDummySpriteAnimTable,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCB_Hail,
};

// flying_dirt.png holds two 32x16 frames: loose grains and a sand crescent
static const union AnimCmd sAnim_SandGrains[] =
{
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_SandCrescent[] =
{
    ANIMCMD_FRAME(8, 1),
    ANIMCMD_END,
};

static const union AnimCmd *const sAnims_Sand[] =
{
    sAnim_SandGrains,
    sAnim_SandCrescent,
};

static const struct SpriteTemplate sSandSpriteTemplate =
{
    .tileTag = ANIM_TAG_FLYING_DIRT,
    .paletteTag = ANIM_TAG_FLYING_DIRT,
    .oam = &gOamData_AffineOff_ObjNormal_32x16,
    .anims = sAnims_Sand,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCB_Sand,
};

void BattleWeatherVisual_Reset(void)
{
    // the sprites and palettes are already gone (new battle, or back from the bag/party screen)
    memset(&gBattleWeatherVisual, 0, sizeof(gBattleWeatherVisual));
}

static void RestorePalettes(u32 mask)
{
    u8 i;

    for (i = 0; i < 32; i++)
    {
        if (mask & (1u << i))
            CpuCopy16(&gPlttBufferUnfaded[PLTT_ID(i)], &gPlttBufferFaded[PLTT_ID(i)], PLTT_SIZE_4BPP);
    }
}

// Always from Unfaded, so it never stacks: safe to redo every frame. Redone every frame because a
// Pokémon sent out (LoadPalette) or the move menu's 0->0 fade rewrite the battler palettes.
static void ApplySceneTint(u8 coeff, u16 color)
{
    u32 mask = BWV_TERRAIN_PALETTES | GetBattleMonSpritePalettesMask(1, 1, 1, 1);

    if (gBattleWeatherVisual.sunApplied)
        RestorePalettes(gBattleWeatherVisual.tintMask & ~mask); // a Pokémon left the field
    BlendPalettes(mask, coeff, color);
    gBattleWeatherVisual.tintMask = mask;
    gBattleWeatherVisual.sunApplied = TRUE;
}

static void RemoveSceneTint(void)
{
    if (!gBattleWeatherVisual.sunApplied)
        return;
    RestorePalettes(gBattleWeatherVisual.tintMask);
    gBattleWeatherVisual.tintMask = 0;
    gBattleWeatherVisual.sunApplied = FALSE;
}

static void RefreshSceneTint(void)
{
    if (gBattleWeatherVisual.shown == BWV_SUN)
        ApplySceneTint(BWV_SUN_TINT_COEFF, BWV_SUN_TINT);
    else if (gBattleWeatherVisual.shown == BWV_RAIN)
        ApplySceneTint(BWV_RAIN_TINT_COEFF, RGB_BLACK);
}

// A ResetSpriteData this module never saw (the Pokédex page of a capture) leaves stale ids behind
static bool8 IsWeatherParticle(struct Sprite *sprite)
{
    return sprite->inUse
        && (sprite->callback == SpriteCB_RainDrop || sprite->callback == SpriteCB_Hail || sprite->callback == SpriteCB_Sand);
}

void BattleWeatherVisual_Suspend(void)
{
    u8 i;

    RemoveSceneTint();
    for (i = 0; i < gBattleWeatherVisual.count; i++)
    {
        if (IsWeatherParticle(&gSprites[gBattleWeatherVisual.spriteIds[i]]))
            DestroySprite(&gSprites[gBattleWeatherVisual.spriteIds[i]]);
    }
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

// A fade that changes the brightness (to/from black or white). The move menu runs 0->0 fades on
// every cursor move; those must not drop the weather.
static bool8 IsBrightnessFade(void)
{
    return gPaletteFade.active && (gPaletteFade.y != 0 || gPaletteFade.targetY != 0);
}

// Pure: what should be on screen now. No AbilityBattleEffects/WEATHER_HAS_EFFECT here, both write
// gLastUsedAbility and this runs every frame, in the middle of battle scripts.
u8 BattleWeatherVisual_GetWanted(void)
{
    if (gSaveBlock2Ptr->optionsBattleSceneOff || gBattleOutcome != 0)
        return BWV_NONE;
    // another screen inside BattleMainCB2 (the Pokédex page of a capture), a fade under way, or a
    // screen left black at the end of one (the frame before the bag or the party menu opens)
    if (gMain.vblankCallback != VBlankCB_Battle || IsBrightnessFade() || gPaletteFade.y != 0)
        return BWV_NONE;
    if (IsBattleAnimRunning())
        return BWV_NONE;
    if (IsWeatherNegatedOnField())
        return BWV_NONE;
    if (gBattleWeather & B_WEATHER_RAIN)
        return BWV_RAIN;
    if (gBattleWeather & B_WEATHER_HAIL)
        return BWV_HAIL;
    if (gBattleWeather & B_WEATHER_SANDSTORM)
        return BWV_SAND;
    if (gBattleWeather & B_WEATHER_SUN)
        return BWV_SUN;
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
        gSprites[spriteId].sWaveTimer = Random() % 64;
        if (template->anims == sAnims_Sand)
            StartSpriteAnim(&gSprites[spriteId], i % 2);
        gBattleWeatherVisual.spriteIds[gBattleWeatherVisual.count++] = spriteId;
    }
}

void BattleWeatherVisual_Update(void)
{
    u8 wanted = BattleWeatherVisual_GetWanted();

    if (wanted == gBattleWeatherVisual.shown)
    {
        RefreshSceneTint();
        return;
    }
    BattleWeatherVisual_Suspend();
    switch (wanted)
    {
    case BWV_RAIN:
        // diagonal down to the right, along the streak drawn in rain_drops.png
        CreateParticles(&sRainDropSpriteTemplate, BWV_RAIN_COUNT, 2, 6);
        ApplySceneTint(BWV_RAIN_TINT_COEFF, RGB_BLACK);
        break;
    case BWV_HAIL:
        // almost straight down, slower than the rain
        CreateParticles(&sHailSpriteTemplate, BWV_HAIL_COUNT, 1, 3);
        break;
    case BWV_SAND:
        // swept from left to right, waving up and down
        CreateParticles(&sSandSpriteTemplate, BWV_SAND_COUNT, 5, 0);
        break;
    case BWV_SUN:
        // no particles: a warm, brighter scene
        ApplySceneTint(BWV_SUN_TINT_COEFF, BWV_SUN_TINT);
        break;
    }
    gBattleWeatherVisual.shown = wanted;
}

// Falls and wraps around: back to the top once it leaves the scene, a little to the left so the
// drift to the right still covers the whole width
static void FallAndWrap(struct Sprite *sprite)
{
    sprite->x += sprite->sSpeedX;
    sprite->y += sprite->sSpeedY;
    if (sprite->y > DISPLAY_HEIGHT + 16 || sprite->x > DISPLAY_WIDTH + 16)
    {
        sprite->x = Random() % DISPLAY_WIDTH - 32;
        sprite->y = -16;
    }
}

static void SpriteCB_RainDrop(struct Sprite *sprite)
{
    FallAndWrap(sprite);
}

static void SpriteCB_Hail(struct Sprite *sprite)
{
    FallAndWrap(sprite);
}

// Blows across and wraps around: back to the left edge at a random height
static void SpriteCB_Sand(struct Sprite *sprite)
{
    sprite->x += sprite->sSpeedX;
    sprite->sWaveTimer = (sprite->sWaveTimer + 6) & 0xFF;
    sprite->y2 = Sin(sprite->sWaveTimer, 4);
    if (sprite->x > DISPLAY_WIDTH + 32)
    {
        sprite->x = -32;
        sprite->y = Random() % (DISPLAY_HEIGHT - 48);
    }
}
