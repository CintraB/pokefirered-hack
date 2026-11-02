#include "global.h"
#include "random.h"
#include "wild_encounter.h"
#include "event_data.h"
#include "fieldmap.h"
#include "random.h"
#include "roamer.h"
#include "field_player_avatar.h"
#include "battle_setup.h"
#include "overworld.h"
#include "metatile_behavior.h"
#include "event_scripts.h"
#include "script.h"
#include "link.h"
#include "quest_log.h"
#include "constants/maps.h"
#include "constants/abilities.h"
#include "constants/items.h"
// Hack 7 — frente B
#include "day_night.h"
// POK-47 (DexNav)
#include "dexnav.h"
#include "field_specials.h"

#define MAX_ENCOUNTER_RATE 1600

#define HEADER_NONE 0xFFFF

struct WildEncounterData
{
    u32 rngState;
    u16 prevMetatileBehavior;
    u16 encounterRateBuff;
    u8 stepsSinceLastEncounter;
    u8 abilityEffect;
    u16 leadMonHeldItem;
};

static EWRAM_DATA struct WildEncounterData sWildEncounterData = {};
static EWRAM_DATA bool8 sWildEncountersDisabled = FALSE;

static bool8 UnlockedTanobyOrAreNotInTanoby(void);
static u32 GenerateUnownPersonalityByLetter(u8 letter);
static bool8 IsWildLevelAllowedByRepel(u8 level);
static void ApplyFluteEncounterRateMod(u32 *rate);
static u8 GetFluteEncounterRateModType(void);
static void ApplyCleanseTagEncounterRateMod(u32 *rate);
static bool8 IsLeadMonHoldingCleanseTag(void);
static u16 WildEncounterRandom(void);
static void AddToWildEncounterRateBuff(u8 encouterRate);

#include "data/wild_encounters.h"
#include "data/wild_encounters_time.h"
#include "data/wild_encounters_leafgreen.h"

// Hack 8: LeafGreen exclusives where LeafGreen has them. If the slot's LeafGreen twin is a
// LeafGreen exclusive (gWildLeafGreenSwaps, generated from wild_encounters.json), the slot rolls
// 50/50 between the FireRed line and the LeafGreen line (species and levels of the LeafGreen
// slot). Other slots return their FireRed line without touching the RNG.
static const struct WildPokemon *GetLeafGreenSlotMon(const struct WildPokemonInfo *info, u8 slot)
{
#ifdef FIRERED
    u32 i;

    for (i = 0; i < gWildLeafGreenSwapsCount; i++)
    {
        if (gWildLeafGreenSwaps[i].info == info && gWildLeafGreenSwaps[i].slot == slot)
        {
            if (Random() % 2)
                return &gWildLeafGreenSwaps[i].mon;
            break;
        }
    }
#endif
    return &info->wildPokemon[slot];
}

// Hack 8: does some period keep the FireRed species of this land slot? (no time table = yes)
// Where the time table always replaces it, the LeafGreen half of the slot never shows up.
static bool8 TimeTableKeepsLandSlot(const struct WildPokemonHeader *header, u8 slot)
{
    u32 i, p;

    for (i = 0; gWildMonTimeTables[i].mapGroup != MAP_GROUP(MAP_UNDEFINED)
             || gWildMonTimeTables[i].mapNum != MAP_NUM(MAP_UNDEFINED); i++)
    {
        if (gWildMonTimeTables[i].mapGroup != header->mapGroup || gWildMonTimeTables[i].mapNum != header->mapNum)
            continue;
        for (p = 0; p < 3; p++)
            if (gWildMonTimeTables[i].species[p][slot] == header->landMonsInfo->wildPokemon[slot].species)
                return TRUE;
        return FALSE;
    }
    return TRUE;
}

// Hack 8: Pokédex AREA, the species a header gets from the LeafGreen half of a shared slot
bool8 IsLeafGreenSlotSpeciesOnMap(const struct WildPokemonHeader *header, u16 species)
{
#ifdef FIRERED
    u32 i;

    for (i = 0; i < gWildLeafGreenSwapsCount; i++)
    {
        const struct WildPokemonInfo *info = gWildLeafGreenSwaps[i].info;

        if (gWildLeafGreenSwaps[i].mon.species != species)
            continue;
        if (info == header->landMonsInfo && TimeTableKeepsLandSlot(header, gWildLeafGreenSwaps[i].slot))
            return TRUE;
        if (info == header->waterMonsInfo || info == header->rockSmashMonsInfo || info == header->fishingMonsInfo)
            return TRUE;
    }
#endif
    return FALSE;
}

// Hack 7 — frente B: land species by time of day (HeartGold tables); level and rate stay FRLG's
u16 GetTimeOfDayLandSpecies(u8 mapGroup, u8 mapNum, u8 slot, u8 period, u16 fallback)
{
    u32 i;
    u8 index;

    if (slot >= LAND_WILD_COUNT)
        return fallback;
    for (i = 0; gWildMonTimeTables[i].mapGroup != MAP_GROUP(MAP_UNDEFINED)
             || gWildMonTimeTables[i].mapNum != MAP_NUM(MAP_UNDEFINED); i++)
    {
        if (gWildMonTimeTables[i].mapGroup != mapGroup || gWildMonTimeTables[i].mapNum != mapNum)
            continue;
        switch (period)
        {
        case TIME_MORNING:
            index = 0;
            break;
        case TIME_AFTERNOON:
            index = 1;
            break;
        case TIME_EVENING:
            index = (Random() & 1) ? 1 : 2;
            break;
        default:
            index = 2;
            break;
        }
        return gWildMonTimeTables[i].species[index][slot];
    }
    return fallback;
}

static const u8 sUnownLetterSlots[][LAND_WILD_COUNT] = {
  //  A   A   A   A   A   A   A   A   A   A   A   ?
    { 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 27},
  //  C   C   C   D   D   D   H   H   H   U   U   O
    { 2,  2,  2,  3,  3,  3,  7,  7,  7, 20, 20, 14},
  //  N   N   N   N   S   S   S   S   I   I   E   E
    {13, 13, 13, 13, 18, 18, 18, 18,  8,  8,  4,  4},
  //  P   P   L   L   J   J   R   R   R   Q   Q   Q
    {15, 15, 11, 11,  9,  9, 17, 17, 17, 16, 16, 16},
  //  Y   Y   T   T   G   G   G   F   F   F   K   K
    {24, 24, 19, 19,  6,  6,  6,  5,  5,  5, 10, 10},
  //  V   V   V   W   W   W   X   X   M   M   B   B
    {21, 21, 21, 22, 22, 22, 23, 23, 12, 12,  1,  1},
  //  Z   Z   Z   Z   Z   Z   Z   Z   Z   Z   Z   !
    {25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 26},
};

void DisableWildEncounters(bool8 state)
{
    sWildEncountersDisabled = state;
}

static u8 ChooseWildMonIndex_Land(void)
{
    u8 rand = Random() % ENCOUNTER_CHANCE_LAND_MONS_TOTAL;

    if (rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_0)
        return 0;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_0 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_1)
        return 1;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_1 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_2)
        return 2;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_2 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_3)
        return 3;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_3 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_4)
        return 4;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_4 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_5)
        return 5;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_5 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_6)
        return 6;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_6 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_7)
        return 7;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_7 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_8)
        return 8;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_8 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_9)
        return 9;
    else if (rand >= ENCOUNTER_CHANCE_LAND_MONS_SLOT_9 && rand < ENCOUNTER_CHANCE_LAND_MONS_SLOT_10)
        return 10;
    else
        return 11;
}

static u8 ChooseWildMonIndex_WaterRock(void)
{
    u8 rand = Random() % ENCOUNTER_CHANCE_WATER_MONS_TOTAL;

    if (rand < ENCOUNTER_CHANCE_WATER_MONS_SLOT_0)
        return 0;
    else if (rand >= ENCOUNTER_CHANCE_WATER_MONS_SLOT_0 && rand < ENCOUNTER_CHANCE_WATER_MONS_SLOT_1)
        return 1;
    else if (rand >= ENCOUNTER_CHANCE_WATER_MONS_SLOT_1 && rand < ENCOUNTER_CHANCE_WATER_MONS_SLOT_2)
        return 2;
    else if (rand >= ENCOUNTER_CHANCE_WATER_MONS_SLOT_2 && rand < ENCOUNTER_CHANCE_WATER_MONS_SLOT_3)
        return 3;
    else
        return 4;
}

static u8 ChooseWildMonIndex_Fishing(u8 rod)
{
    u8 wildMonIndex = 0;
    u8 rand = Random() % max(max(ENCOUNTER_CHANCE_FISHING_MONS_OLD_ROD_TOTAL, ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_TOTAL),
                             ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_TOTAL);

    switch (rod)
    {
    case OLD_ROD:
        if (rand < ENCOUNTER_CHANCE_FISHING_MONS_OLD_ROD_SLOT_0)
            wildMonIndex = 0;
        else
            wildMonIndex = 1;
        break;
    case GOOD_ROD:
        if (rand < ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_2)
            wildMonIndex = 2;
        if (rand >= ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_2 && rand < ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_3)
            wildMonIndex = 3;
        if (rand >= ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_3 && rand < ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_4)
            wildMonIndex = 4;
        break;
    case SUPER_ROD:
        if (rand < ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_5)
            wildMonIndex = 5;
        if (rand >= ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_5 && rand < ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_6)
            wildMonIndex = 6;
        if (rand >= ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_6 && rand < ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_7)
            wildMonIndex = 7;
        if (rand >= ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_7 && rand < ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_8)
            wildMonIndex = 8;
        if (rand >= ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_8 && rand < ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_9)
            wildMonIndex = 9;
        break;
    }
    return wildMonIndex;
}

static u8 ChooseWildMonLevel(const struct WildPokemon * info)
{
    u8 lo;
    u8 hi;
    u8 mod;
    u8 res;
    if (info->maxLevel >= info->minLevel)
    {
        lo = info->minLevel;
        hi = info->maxLevel;
    }
    else
    {
        lo = info->maxLevel;
        hi = info->minLevel;
    }
    mod = hi - lo + 1;
    res = Random() % mod;
    return lo + res;
}

static u16 GetCurrentMapWildMonHeaderId(void)
{
    u16 i;

    for (i = 0; ; i++)
    {
        const struct WildPokemonHeader * wildHeader = &gWildMonHeaders[i];
        if (wildHeader->mapGroup == MAP_GROUP(MAP_UNDEFINED))
            break;

        if (gWildMonHeaders[i].mapGroup == gSaveBlock1Ptr->location.mapGroup &&
            gWildMonHeaders[i].mapNum == gSaveBlock1Ptr->location.mapNum)
        {
            if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_SIX_ISLAND_ALTERING_CAVE) &&
                gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SIX_ISLAND_ALTERING_CAVE))
            {
                u16 alteringCaveId = VarGet(VAR_ALTERING_CAVE_WILD_SET);
                if (alteringCaveId >= NUM_ALTERING_CAVE_TABLES)
                    alteringCaveId = 0;

                i += alteringCaveId;
            }

            if (!UnlockedTanobyOrAreNotInTanoby())
                break;
            return i;
        }
    }

    return HEADER_NONE;
}

static bool8 UnlockedTanobyOrAreNotInTanoby(void)
{
    if (FlagGet(FLAG_SYS_UNLOCKED_TANOBY_RUINS))
        return TRUE;
    if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER))
        return TRUE;
    if (!(gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER)
    ||  gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_LIPTOO_CHAMBER)
    ||  gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_WEEPTH_CHAMBER)
    ||  gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER)
    ||  gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_SCUFIB_CHAMBER)
    ||  gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_RIXY_CHAMBER)
    ||  gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_VIAPOIS_CHAMBER)
    ))
        return TRUE;
    return FALSE;
}

static void GenerateWildMon(u16 species, u8 level, u8 slot)
{
    u32 personality;
    s8 chamber;
    ZeroEnemyPartyMons();
    if (species != SPECIES_UNOWN)
    {
        CreateMonWithNature(&gEnemyParty[0], species, level, USE_RANDOM_IVS, Random() % NUM_NATURES);
    }
    else
    {
        chamber = gSaveBlock1Ptr->location.mapNum - MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER);
        personality = GenerateUnownPersonalityByLetter(sUnownLetterSlots[chamber][slot]);
        CreateMon(&gEnemyParty[0], species, level, USE_RANDOM_IVS, TRUE, personality, FALSE, 0);
    }
}

static u32 GenerateUnownPersonalityByLetter(u8 letter)
{
    u32 personality;
    do
    {
        personality = (Random() << 16) | Random();
    } while (GetUnownLetterByPersonalityLoByte(personality) != letter);
    return personality;
}

u8 GetUnownLetterByPersonalityLoByte(u32 personality)
{
    return GET_UNOWN_LETTER(personality);
}

enum
{
    WILD_AREA_LAND,
    WILD_AREA_WATER,
    WILD_AREA_ROCKS,
    WILD_AREA_FISHING,
};

#define WILD_CHECK_REPEL    0x1
#define WILD_CHECK_KEEN_EYE 0x2

static bool8 TryGenerateWildMon(const struct WildPokemonInfo * info, u8 area, u8 flags)
{
    u8 slot = 0;
    u8 level;
    u16 species;
    const struct WildPokemon *mon;
    switch (area)
    {
    case WILD_AREA_LAND:
        slot = ChooseWildMonIndex_Land();
        break;
    case WILD_AREA_WATER:
        slot = ChooseWildMonIndex_WaterRock();
        break;
    case WILD_AREA_ROCKS:
        slot = ChooseWildMonIndex_WaterRock();
        break;
    }
    mon = &info->wildPokemon[slot];
    level = ChooseWildMonLevel(mon);
    species = mon->species;
    if (area == WILD_AREA_LAND)
        species = GetTimeOfDayLandSpecies(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum, slot, DayNight_GetPeriod(), species);
    // Hack 8: time of day first; the LeafGreen half of the slot only when the time table kept
    // the FireRed species. The LeafGreen half rerolls the level on its own line, and Repel
    // checks the final level (slots without a LeafGreen twin keep the FRLG RNG order).
    if (species == mon->species)
    {
        const struct WildPokemon *lg = GetLeafGreenSlotMon(info, slot);

        if (lg != mon)
        {
            species = lg->species;
            level = ChooseWildMonLevel(lg);
        }
    }
    if (flags == WILD_CHECK_REPEL && !IsWildLevelAllowedByRepel(level))
    {
        return FALSE;
    }
    GenerateWildMon(species, level, slot);
    return TRUE;
}

static u16 GenerateFishingEncounter(const struct WildPokemonInfo * info, u8 rod)
{
    u8 slot = ChooseWildMonIndex_Fishing(rod);
    const struct WildPokemon *mon = GetLeafGreenSlotMon(info, slot); // Hack 8
    u8 level = ChooseWildMonLevel(mon);
    GenerateWildMon(mon->species, level, slot);
    return mon->species;
}

static bool8 DoWildEncounterRateDiceRoll(u16 encounterRate)
{
    if (WildEncounterRandom() % MAX_ENCOUNTER_RATE < encounterRate)
        return TRUE;
    return FALSE;
}

static bool8 DoWildEncounterRateTest(u32 encounterRate, bool8 ignoreAbility)
{
    encounterRate *= 16;
    if (TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_MACH_BIKE | PLAYER_AVATAR_FLAG_ACRO_BIKE))
        encounterRate = encounterRate * 80 / 100;
    encounterRate += sWildEncounterData.encounterRateBuff * 16 / 200;
    ApplyFluteEncounterRateMod(&encounterRate);
    ApplyCleanseTagEncounterRateMod(&encounterRate);
    if (!ignoreAbility)
    {
        switch (sWildEncounterData.abilityEffect)
        {
        case 1:
            encounterRate /= 2;
            break;
        case 2:
            encounterRate *= 2;
            break;
        }
    }
    if (encounterRate > MAX_ENCOUNTER_RATE)
        encounterRate = MAX_ENCOUNTER_RATE;
    return DoWildEncounterRateDiceRoll(encounterRate);
}

static u8 GetAbilityEncounterRateModType(void)
{
    sWildEncounterData.abilityEffect = 0;
    if (!GetMonData(&gPlayerParty[0], MON_DATA_SANITY_IS_EGG))
    {
        u8 ability = GetMonAbility(&gPlayerParty[0]);
        if (ability == ABILITY_STENCH)
            sWildEncounterData.abilityEffect = 1;
        else if (ability == ABILITY_ILLUMINATE)
            sWildEncounterData.abilityEffect = 2;
    }
    return sWildEncounterData.abilityEffect;
}

static bool8 DoGlobalWildEncounterDiceRoll(void)
{
    if ((Random() % 100) >= 60)
        return FALSE;
    return TRUE;
}

bool8 StandardWildEncounter(u32 currMetatileAttrs, u16 previousMetatileBehavior)
{
    u16 headerId;
    struct Roamer * roamer;

    if (sWildEncountersDisabled == TRUE)
        return FALSE;

    headerId = GetCurrentMapWildMonHeaderId();
    if (headerId != HEADER_NONE)
    {
        if (ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_ENCOUNTER_TYPE) == TILE_ENCOUNTER_LAND)
        {
            if (gWildMonHeaders[headerId].landMonsInfo == NULL)
                return FALSE;
            else if (previousMetatileBehavior != ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_BEHAVIOR) && !DoGlobalWildEncounterDiceRoll())
                return FALSE;
            if (DoWildEncounterRateTest(gWildMonHeaders[headerId].landMonsInfo->encounterRate, FALSE) != TRUE)
            {
                AddToWildEncounterRateBuff(gWildMonHeaders[headerId].landMonsInfo->encounterRate);
                return FALSE;
            }

            else if (TryStartRoamerEncounter() == TRUE)
            {
                roamer = &gSaveBlock1Ptr->roamer;
                if (!IsWildLevelAllowedByRepel(roamer->level))
                {
                    return FALSE;
                }

                StartRoamerBattle();
                return TRUE;
            }
            else
            {

                // try a regular wild land encounter
                if (TryGenerateWildMon(gWildMonHeaders[headerId].landMonsInfo, WILD_AREA_LAND, WILD_CHECK_REPEL) == TRUE)
                {
                    StartWildBattle();
                    return TRUE;
                }
                else
                {
                    AddToWildEncounterRateBuff(gWildMonHeaders[headerId].landMonsInfo->encounterRate);
                }
            }
        }
        else if (ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_ENCOUNTER_TYPE) == TILE_ENCOUNTER_WATER
                 || (TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING) && MetatileBehavior_IsBridge(ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_BEHAVIOR)) == TRUE))
        {
            if (gWildMonHeaders[headerId].waterMonsInfo == NULL)
                return FALSE;
            else if (previousMetatileBehavior != ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_BEHAVIOR) && !DoGlobalWildEncounterDiceRoll())
                return FALSE;
            else if (DoWildEncounterRateTest(gWildMonHeaders[headerId].waterMonsInfo->encounterRate, FALSE) != TRUE)
            {
                AddToWildEncounterRateBuff(gWildMonHeaders[headerId].waterMonsInfo->encounterRate);
                return FALSE;
            }

            if (TryStartRoamerEncounter() == TRUE)
            {
                roamer = &gSaveBlock1Ptr->roamer;
                if (!IsWildLevelAllowedByRepel(roamer->level))
                {
                    return FALSE;
                }

                StartRoamerBattle();
                return TRUE;
            }
            else // try a regular surfing encounter
            {
                if (TryGenerateWildMon(gWildMonHeaders[headerId].waterMonsInfo, WILD_AREA_WATER, WILD_CHECK_REPEL) == TRUE)
                {
                    StartWildBattle();
                    return TRUE;
                }
                else
                {
                    AddToWildEncounterRateBuff(gWildMonHeaders[headerId].waterMonsInfo->encounterRate);
                }
            }
        }
    }

    return FALSE;
}

void RockSmashWildEncounter(void)
{
    u16 headerIdx = GetCurrentMapWildMonHeaderId();
    if (headerIdx == HEADER_NONE)
        gSpecialVar_Result = FALSE;
    else if (gWildMonHeaders[headerIdx].rockSmashMonsInfo == NULL)
        gSpecialVar_Result = FALSE;
    else if (DoWildEncounterRateTest(gWildMonHeaders[headerIdx].rockSmashMonsInfo->encounterRate, TRUE) != TRUE)
        gSpecialVar_Result = FALSE;
    else if (TryGenerateWildMon(gWildMonHeaders[headerIdx].rockSmashMonsInfo, WILD_AREA_ROCKS, WILD_CHECK_REPEL) == TRUE)
    {
        StartWildBattle();
        gSpecialVar_Result = TRUE;
    }
    else
        gSpecialVar_Result = FALSE;
}

bool8 SweetScentWildEncounter(void)
{
    s16 x, y;
    u16 headerId;

    PlayerGetDestCoords(&x, &y);
    headerId = GetCurrentMapWildMonHeaderId();
    if (headerId != HEADER_NONE)
    {
        if (MapGridGetMetatileAttributeAt(x, y, METATILE_ATTRIBUTE_ENCOUNTER_TYPE) == TILE_ENCOUNTER_LAND)
        {
            if (TryStartRoamerEncounter() == TRUE)
            {
                StartRoamerBattle();
                return TRUE;
            }

            if (gWildMonHeaders[headerId].landMonsInfo == NULL)
                return FALSE;

            TryGenerateWildMon(gWildMonHeaders[headerId].landMonsInfo, WILD_AREA_LAND, 0);

            StartWildBattle();
            return TRUE;
        }
        else if (MapGridGetMetatileAttributeAt(x, y, METATILE_ATTRIBUTE_ENCOUNTER_TYPE) == TILE_ENCOUNTER_WATER)
        {
            if (TryStartRoamerEncounter() == TRUE)
            {
                StartRoamerBattle();
                return TRUE;
            }

            if (gWildMonHeaders[headerId].waterMonsInfo == NULL)
                return FALSE;

            TryGenerateWildMon(gWildMonHeaders[headerId].waterMonsInfo, WILD_AREA_WATER, 0);
            StartWildBattle();
            return TRUE;
        }
    }

    return FALSE;
}

bool8 DoesCurrentMapHaveFishingMons(void)
{
    u16 headerIdx = GetCurrentMapWildMonHeaderId();
    if (headerIdx == HEADER_NONE)
        return FALSE;
    if (gWildMonHeaders[headerIdx].fishingMonsInfo == NULL)
        return FALSE;
    return TRUE;
}

void FishingWildEncounter(u8 rod)
{
    GenerateFishingEncounter(gWildMonHeaders[GetCurrentMapWildMonHeaderId()].fishingMonsInfo, rod);
    IncrementGameStat(GAME_STAT_FISHING_CAPTURES);
    StartWildBattle();
}

static u16 GetLocalLandSpecies(const struct WildPokemonInfo * landMonsInfo)
{
    u8 slot = ChooseWildMonIndex_Land();

    return GetTimeOfDayLandSpecies(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum, slot, DayNight_GetPeriod(), landMonsInfo->wildPokemon[slot].species);
}

u16 GetLocalWildMon(bool8 *isWaterMon)
{
    u16 headerId;
    const struct WildPokemonInfo * landMonsInfo;
    const struct WildPokemonInfo * waterMonsInfo;

    *isWaterMon = FALSE;
    headerId = GetCurrentMapWildMonHeaderId();
    if (headerId == HEADER_NONE)
        return SPECIES_NONE;
    landMonsInfo = gWildMonHeaders[headerId].landMonsInfo;
    waterMonsInfo = gWildMonHeaders[headerId].waterMonsInfo;
    // Neither
    if (landMonsInfo == NULL && waterMonsInfo == NULL)
        return SPECIES_NONE;
        // Land Pokemon
    else if (landMonsInfo != NULL && waterMonsInfo == NULL)
        return GetLocalLandSpecies(landMonsInfo);
        // Water Pokemon
    else if (landMonsInfo == NULL && waterMonsInfo != NULL)
    {
        *isWaterMon = TRUE;
        return waterMonsInfo->wildPokemon[ChooseWildMonIndex_WaterRock()].species;
    }
    // Either land or water Pokemon
    if ((Random() % 100) < 80)
    {
        return GetLocalLandSpecies(landMonsInfo);
    }
    else
    {
        *isWaterMon = TRUE;
        return waterMonsInfo->wildPokemon[ChooseWildMonIndex_WaterRock()].species;
    }
}

u16 GetLocalWaterMon(void)
{
    u16 headerId = GetCurrentMapWildMonHeaderId();

    if (headerId != HEADER_NONE)
    {
        const struct WildPokemonInfo * waterMonsInfo = gWildMonHeaders[headerId].waterMonsInfo;

        if (waterMonsInfo)
            return waterMonsInfo->wildPokemon[ChooseWildMonIndex_WaterRock()].species;
    }
    return SPECIES_NONE;
}

bool8 UpdateRepelCounter(void)
{
    u16 steps;

    if (InUnionRoom() == TRUE)
        return FALSE;

    if (gQuestLogState == QL_STATE_PLAYBACK)
        return FALSE;

    steps = VarGet(VAR_REPEL_STEP_COUNT);

    if (steps != 0)
    {
        steps--;
        VarSet(VAR_REPEL_STEP_COUNT, steps);
        if (steps == 0)
        {
            ScriptContext_SetupScript(EventScript_RepelWoreOff);
            return TRUE;
        }
    }
    return FALSE;
}

static bool8 IsWildLevelAllowedByRepel(u8 wildLevel)
{
    u8 i;

    if (!VarGet(VAR_REPEL_STEP_COUNT))
        return TRUE;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_HP) && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
        {
            u8 ourLevel = GetMonData(&gPlayerParty[i], MON_DATA_LEVEL);

            if (wildLevel < ourLevel)
                return FALSE;
            else
                return TRUE;
        }
    }

    return FALSE;
}

static void ApplyFluteEncounterRateMod(u32 *encounterRate)
{
    switch (GetFluteEncounterRateModType())
    {
    case 1:
        *encounterRate += *encounterRate / 2;
        break;
    case 2:
        *encounterRate = *encounterRate / 2;
        break;
    }
}

static u8 GetFluteEncounterRateModType(void)
{
    if (FlagGet(FLAG_SYS_WHITE_FLUTE_ACTIVE) == TRUE)
        return 1;
    else if (FlagGet(FLAG_SYS_BLACK_FLUTE_ACTIVE) == TRUE)
        return 2;
    else
        return 0;
}

static void ApplyCleanseTagEncounterRateMod(u32 *encounterRate)
{
    if (IsLeadMonHoldingCleanseTag())
        *encounterRate = *encounterRate * 2 / 3;
}

static bool8 IsLeadMonHoldingCleanseTag(void)
{
    if (sWildEncounterData.leadMonHeldItem == ITEM_CLEANSE_TAG)
        return TRUE;
    else
        return FALSE;
}

void SeedWildEncounterRng(u16 seed)
{
    sWildEncounterData.rngState = seed;
    ResetEncounterRateModifiers();
}

static u16 WildEncounterRandom(void)
{
    sWildEncounterData.rngState = ISO_RANDOMIZE2(sWildEncounterData.rngState);
    return sWildEncounterData.rngState >> 16;
}

static u8 GetMapBaseEncounterCooldown(u8 encounterType)
{
    u16 headerIdx = GetCurrentMapWildMonHeaderId();
    if (headerIdx == HEADER_NONE)
        return 0xFF;
    if (encounterType == TILE_ENCOUNTER_LAND)
    {
        if (gWildMonHeaders[headerIdx].landMonsInfo == NULL)
            return 0xFF;
        if (gWildMonHeaders[headerIdx].landMonsInfo->encounterRate >= 80)
            return 0;
        if (gWildMonHeaders[headerIdx].landMonsInfo->encounterRate < 10)
            return 8;
        return 8 - (gWildMonHeaders[headerIdx].landMonsInfo->encounterRate / 10);
    }
    if (encounterType == TILE_ENCOUNTER_WATER)
    {
        if (gWildMonHeaders[headerIdx].waterMonsInfo == NULL)
            return 0xFF;
        if (gWildMonHeaders[headerIdx].waterMonsInfo->encounterRate >= 80)
            return 0;
        if (gWildMonHeaders[headerIdx].waterMonsInfo->encounterRate < 10)
            return 8;
        return 8 - (gWildMonHeaders[headerIdx].waterMonsInfo->encounterRate / 10);
    }
    return 0xFF;
}

void ResetEncounterRateModifiers(void)
{
    sWildEncounterData.encounterRateBuff = 0;
    sWildEncounterData.stepsSinceLastEncounter = 0;
}

static bool8 HandleWildEncounterCooldown(u32 currMetatileAttrs)
{
    u8 encounterType = ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_ENCOUNTER_TYPE);
    u32 minSteps;
    u32 encRate;
    if (encounterType == TILE_ENCOUNTER_NONE)
        return FALSE;
    minSteps = GetMapBaseEncounterCooldown(encounterType);
    if (minSteps == 0xFF)
        return FALSE;
    minSteps *= 256;
    encRate = 5 * 256;
    switch (GetFluteEncounterRateModType())
    {
    case 1:
        minSteps -= minSteps / 2;
        encRate += encRate / 2;
        break;
    case 2:
        minSteps *= 2;
        encRate /= 2;
        break;
    }
    sWildEncounterData.leadMonHeldItem = GetMonData(&gPlayerParty[0], MON_DATA_HELD_ITEM);
    if (IsLeadMonHoldingCleanseTag() == TRUE)
    {
        minSteps += minSteps / 3;
        encRate -= encRate / 3;
    }
    switch (GetAbilityEncounterRateModType())
    {
    case 1:
        minSteps *= 2;
        encRate /= 2;
        break;
    case 2:
        minSteps /= 2;
        encRate *= 2;
        break;
    }
    minSteps /= 256;
    encRate /= 256;
    if (sWildEncounterData.stepsSinceLastEncounter >= minSteps)
        return TRUE;
    sWildEncounterData.stepsSinceLastEncounter++;
    if ((Random() % 100) < encRate)
        return TRUE;
    return FALSE;
}

bool8 TryStandardWildEncounter(u32 currMetatileAttrs)
{
    if (!HandleWildEncounterCooldown(currMetatileAttrs))
    {
        sWildEncounterData.prevMetatileBehavior = ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_BEHAVIOR);
        return FALSE;
    }
    else if (StandardWildEncounter(currMetatileAttrs, sWildEncounterData.prevMetatileBehavior) == TRUE)
    {
        sWildEncounterData.encounterRateBuff = 0;
        sWildEncounterData.stepsSinceLastEncounter = 0;
        sWildEncounterData.prevMetatileBehavior = ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_BEHAVIOR);
        return TRUE;
    }
    else
    {
        sWildEncounterData.prevMetatileBehavior = ExtractMetatileAttribute(currMetatileAttrs, METATILE_ATTRIBUTE_BEHAVIOR);
        return FALSE;
    }
}

static void AddToWildEncounterRateBuff(u8 encounterRate)
{
    if (VarGet(VAR_REPEL_STEP_COUNT) == 0)
        sWildEncounterData.encounterRateBuff += encounterRate;
    else
        sWildEncounterData.encounterRateBuff = 0;
}

// POK-47 DexNav: todos os resultados possíveis de um mapa, para a tela, a busca e os testes. Segue as regras do
// encontro real (GetCurrentMapWildMonHeaderId, TryGenerateWildMon, GenerateFishingEncounter) com as mesmas tabelas,
// sem sortear nada e sem mexer naquelas funções (a ordem dos sorteios do jogo fica igual):
// - chance de cada slot = a faixa dele nos limites acumulados ENCOUNTER_CHANCE_* (todos somam 100: x 10 = por mil);
// - grama: a espécie do slot em cada período pela tabela por horário (Hack 7), com o nível do slot do FRLG; a
//   tarde-noite sorteia entre a tarde e a noite e não tem coluna (DexNav_RateForPeriods tira a média);
// - metade LeafGreen (Hack 8): quando a espécie do slot (já pelo horário) é a do FireRed e o slot tem gêmeo em
//   gWildLeafGreenSwaps, metade da chance vai para cada linha, cada uma com os níveis dela;
// - Caverna Mutante: a tabela do conjunto atual (VAR_ALTERING_CAVE_WILD_SET dentro dela; de fora, o conjunto do
//   dia que a var recebe ao entrar; fora da faixa vale 0);
// - câmara de Tanoby antes de FLAG_SYS_UNLOCKED_TANOBY_RUINS: nada (o jogo não tem encontro lá).
STATIC_ASSERT(ENCOUNTER_CHANCE_LAND_MONS_TOTAL == 100, DexNavChancesDaGramaSomam100);
STATIC_ASSERT(ENCOUNTER_CHANCE_WATER_MONS_TOTAL == 100, DexNavChancesDaAguaSomam100);
STATIC_ASSERT(ENCOUNTER_CHANCE_FISHING_MONS_OLD_ROD_TOTAL == 100, DexNavChancesDaVaraVelhaSomam100);
STATIC_ASSERT(ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_TOTAL == 100, DexNavChancesDaVaraBoaSomam100);
STATIC_ASSERT(ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_TOTAL == 100, DexNavChancesDaSuperVaraSomam100);

#define DEXNAV_SLOT_RATE(limit, previous) ((limit) - (previous))

// ChooseWildMonIndex_Land
static const u8 sDexNavLandRates[LAND_WILD_COUNT] = {
    ENCOUNTER_CHANCE_LAND_MONS_SLOT_0,
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_1, ENCOUNTER_CHANCE_LAND_MONS_SLOT_0),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_2, ENCOUNTER_CHANCE_LAND_MONS_SLOT_1),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_3, ENCOUNTER_CHANCE_LAND_MONS_SLOT_2),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_4, ENCOUNTER_CHANCE_LAND_MONS_SLOT_3),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_5, ENCOUNTER_CHANCE_LAND_MONS_SLOT_4),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_6, ENCOUNTER_CHANCE_LAND_MONS_SLOT_5),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_7, ENCOUNTER_CHANCE_LAND_MONS_SLOT_6),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_8, ENCOUNTER_CHANCE_LAND_MONS_SLOT_7),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_9, ENCOUNTER_CHANCE_LAND_MONS_SLOT_8),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_10, ENCOUNTER_CHANCE_LAND_MONS_SLOT_9),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_LAND_MONS_SLOT_11, ENCOUNTER_CHANCE_LAND_MONS_SLOT_10),
};

// ChooseWildMonIndex_WaterRock (surf e Quebra-Pedra usam os limites da água)
static const u8 sDexNavWaterRockRates[WATER_WILD_COUNT] = {
    ENCOUNTER_CHANCE_WATER_MONS_SLOT_0,
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_WATER_MONS_SLOT_1, ENCOUNTER_CHANCE_WATER_MONS_SLOT_0),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_WATER_MONS_SLOT_2, ENCOUNTER_CHANCE_WATER_MONS_SLOT_1),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_WATER_MONS_SLOT_3, ENCOUNTER_CHANCE_WATER_MONS_SLOT_2),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_WATER_MONS_SLOT_4, ENCOUNTER_CHANCE_WATER_MONS_SLOT_3),
};

// ChooseWildMonIndex_Fishing: slots 0-1 Vara Velha, 2-4 Vara Boa, 5-9 Super Vara
static const u8 sDexNavFishingRates[FISH_WILD_COUNT] = {
    ENCOUNTER_CHANCE_FISHING_MONS_OLD_ROD_SLOT_0,
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_OLD_ROD_SLOT_1, ENCOUNTER_CHANCE_FISHING_MONS_OLD_ROD_SLOT_0),
    ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_2,
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_3, ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_2),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_4, ENCOUNTER_CHANCE_FISHING_MONS_GOOD_ROD_SLOT_3),
    ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_5,
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_6, ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_5),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_7, ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_6),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_8, ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_7),
    DEXNAV_SLOT_RATE(ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_9, ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_8),
};

// Primeiro slot de cada vara (DEXNAV_METHOD_OLD_ROD, _GOOD_ROD, _SUPER_ROD) e o fim
static const u8 sDexNavRodFirstSlot[] = {0, 2, 5, FISH_WILD_COUNT};

// Períodos da tabela por horário: só os que não sorteiam (rateX10[0..2])
static const u8 sDexNavTimePeriods[DEXNAV_PERIOD_COUNT] = {TIME_MORNING, TIME_AFTERNOON, TIME_NIGHT};

struct DexNavList
{
    struct DexNavEntry *out;
    u8 count;
    u8 max;
};

// UnlockedTanobyOrAreNotInTanoby para um mapa qualquer
static bool8 DexNav_IsLockedTanobyChamber(u8 mapGroup, u8 mapNum)
{
    if (FlagGet(FLAG_SYS_UNLOCKED_TANOBY_RUINS))
        return FALSE;
    if (mapGroup != MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER))
        return FALSE;
    return mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER)
        || mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_LIPTOO_CHAMBER)
        || mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_WEEPTH_CHAMBER)
        || mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER)
        || mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_SCUFIB_CHAMBER)
        || mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_RIXY_CHAMBER)
        || mapNum == MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_VIAPOIS_CHAMBER);
}

// GetCurrentMapWildMonHeaderId para um mapa qualquer (NULL = sem encontro agora)
static const struct WildPokemonHeader *DexNav_GetWildHeader(u8 mapGroup, u8 mapNum)
{
    u32 i;

    for (i = 0; gWildMonHeaders[i].mapGroup != MAP_GROUP(MAP_UNDEFINED); i++)
    {
        if (gWildMonHeaders[i].mapGroup == mapGroup && gWildMonHeaders[i].mapNum == mapNum)
        {
            if (mapGroup == MAP_GROUP(MAP_SIX_ISLAND_ALTERING_CAVE) && mapNum == MAP_NUM(MAP_SIX_ISLAND_ALTERING_CAVE))
            {
                u16 alteringCaveId;

                // Dentro da caverna vale a var (o que o encontro usa); de fora, o conjunto que a var vai receber
                // ao entrar (o script de entrada roda GetAlteringCaveSetForScript: um conjunto por dia, Hack 8)
                if (gSaveBlock1Ptr->location.mapGroup == mapGroup && gSaveBlock1Ptr->location.mapNum == mapNum)
                    alteringCaveId = VarGet(VAR_ALTERING_CAVE_WILD_SET);
                else
                    alteringCaveId = GetAlteringCaveSetForScript();
                if (alteringCaveId >= NUM_ALTERING_CAVE_TABLES)
                    alteringCaveId = 0;
                i += alteringCaveId;
            }
            if (DexNav_IsLockedTanobyChamber(mapGroup, mapNum))
                return NULL;
            return &gWildMonHeaders[i];
        }
    }
    return NULL;
}

// A linha LeafGreen do slot (GetLeafGreenSlotMon sem o sorteio), ou NULL
static const struct WildPokemon *DexNav_GetLeafGreenTwin(const struct WildPokemonInfo *info, u8 slot)
{
#ifdef FIRERED
    u32 i;

    for (i = 0; i < gWildLeafGreenSwapsCount; i++)
    {
        if (gWildLeafGreenSwaps[i].info == info && gWildLeafGreenSwaps[i].slot == slot)
            return &gWildLeafGreenSwaps[i].mon;
    }
#endif
    return NULL;
}

// Soma uma linha (espécie e níveis) à entrada (espécie, método), criando-a no fim da lista se couber
static void DexNav_AddResult(struct DexNavList *list, u16 species, u8 method, const struct WildPokemon *mon, u8 periods, u16 rateX10)
{
    struct DexNavEntry *entry = NULL;
    u8 lo, hi;
    u32 i;

    for (i = 0; i < list->count; i++)
    {
        if (list->out[i].species == species && list->out[i].method == method)
        {
            entry = &list->out[i];
            break;
        }
    }
    if (entry == NULL)
    {
        if (list->count >= list->max)
            return;
        entry = &list->out[list->count++];
        memset(entry, 0, sizeof(*entry));
        entry->species = species;
        entry->method = method;
        entry->minLevel = 0xFF;
    }
    // como ChooseWildMonLevel: mínimo e máximo podem vir trocados na tabela
    lo = min(mon->minLevel, mon->maxLevel);
    hi = max(mon->minLevel, mon->maxLevel);
    if (lo < entry->minLevel)
        entry->minLevel = lo;
    if (hi > entry->maxLevel)
        entry->maxLevel = hi;
    entry->periods |= periods;
    for (i = 0; i < DEXNAV_PERIOD_COUNT; i++)
    {
        if (periods & (1 << i))
            entry->rateX10[i] += rateX10;
    }
}

// Um slot com a chance `rate` (%): `species` já é a do horário; a metade LeafGreen só quando ela é a do FireRed
static void DexNav_AddSlot(struct DexNavList *list, const struct WildPokemonInfo *info, u8 slot, u16 species, u8 method, u8 periods, u8 rate)
{
    const struct WildPokemon *mon = &info->wildPokemon[slot];
    const struct WildPokemon *lg = NULL;

    if (species == mon->species)
        lg = DexNav_GetLeafGreenTwin(info, slot);
    if (lg != NULL)
    {
        DexNav_AddResult(list, mon->species, method, mon, periods, rate * 5);
        DexNav_AddResult(list, lg->species, method, lg, periods, rate * 5);
    }
    else
    {
        DexNav_AddResult(list, species, method, mon, periods, rate * 10);
    }
}

u8 DexNav_GetMapEntries(u8 mapIndex, struct DexNavEntry *out, u8 max)
{
    const struct WildPokemonHeader *header;
    const struct WildPokemonInfo *info;
    struct DexNavList list;
    u8 mapGroup, mapNum, rod, slot, p;
    u16 species;

    if (mapIndex >= DEXNAV_MAP_COUNT)
        return 0;
    mapGroup = gDexNavMaps[mapIndex].mapGroup;
    mapNum = gDexNavMaps[mapIndex].mapNum;
    header = DexNav_GetWildHeader(mapGroup, mapNum);
    if (header == NULL)
        return 0;
    list.out = out;
    list.count = 0;
    list.max = max;

    info = header->landMonsInfo;
    if (info != NULL)
    {
        for (p = 0; p < DEXNAV_PERIOD_COUNT; p++)
        {
            for (slot = 0; slot < LAND_WILD_COUNT; slot++)
            {
                species = GetTimeOfDayLandSpecies(mapGroup, mapNum, slot, sDexNavTimePeriods[p], info->wildPokemon[slot].species);
                DexNav_AddSlot(&list, info, slot, species, DEXNAV_METHOD_LAND, 1 << p, sDexNavLandRates[slot]);
            }
        }
    }
    info = header->waterMonsInfo;
    if (info != NULL)
    {
        for (slot = 0; slot < WATER_WILD_COUNT; slot++)
            DexNav_AddSlot(&list, info, slot, info->wildPokemon[slot].species, DEXNAV_METHOD_WATER, DEXNAV_PERIOD_ALL, sDexNavWaterRockRates[slot]);
    }
    info = header->fishingMonsInfo;
    if (info != NULL)
    {
        for (rod = 0; rod < 3; rod++)
        {
            for (slot = sDexNavRodFirstSlot[rod]; slot < sDexNavRodFirstSlot[rod + 1]; slot++)
                DexNav_AddSlot(&list, info, slot, info->wildPokemon[slot].species, DEXNAV_METHOD_OLD_ROD + rod, DEXNAV_PERIOD_ALL, sDexNavFishingRates[slot]);
        }
    }
    info = header->rockSmashMonsInfo;
    if (info != NULL)
    {
        for (slot = 0; slot < ROCK_WILD_COUNT; slot++)
            DexNav_AddSlot(&list, info, slot, info->wildPokemon[slot].species, DEXNAV_METHOD_ROCK, DEXNAV_PERIOD_ALL, sDexNavWaterRockRates[slot]);
    }
    return list.count;
}
// POK-47 DexNav: fim

// Hack 7 — frente B: test hook, the species a land slot gives in a period (the FRLG species
// of the slot when the map has no time table; 0xFFFFFFFF = no land table at all)
#if TESTBUILD
u32 TestLandSpecies(u8 mapGroup, u8 mapNum, u8 slot, u8 period)
{
    u32 i;

    for (i = 0; gWildMonHeaders[i].mapGroup != MAP_GROUP(MAP_UNDEFINED)
             || gWildMonHeaders[i].mapNum != MAP_NUM(MAP_UNDEFINED); i++)
    {
        if (gWildMonHeaders[i].mapGroup == mapGroup && gWildMonHeaders[i].mapNum == mapNum
         && gWildMonHeaders[i].landMonsInfo != NULL && slot < LAND_WILD_COUNT)
            return GetTimeOfDayLandSpecies(mapGroup, mapNum, slot, period, gWildMonHeaders[i].landMonsInfo->wildPokemon[slot].species);
    }
    return 0xFFFFFFFF;
}
#endif

// Hack 8: test hook, one wild mon of the current map through the real generator (time of day
// and LeafGreen slots included), optionally starting the battle like a real encounter.
// result = species | level << 16 of gEnemyParty[0] (0xFFFFFFFF = no table of that kind here)
#if TESTBUILD
u32 TestRollWild(u8 area, u8 rod, bool8 startBattle)
{
    u16 headerId = GetCurrentMapWildMonHeaderId();
    const struct WildPokemonInfo *info;

    if (headerId == HEADER_NONE)
        return 0xFFFFFFFF;
    switch (area)
    {
    case WILD_AREA_LAND:
        info = gWildMonHeaders[headerId].landMonsInfo;
        break;
    case WILD_AREA_WATER:
        info = gWildMonHeaders[headerId].waterMonsInfo;
        break;
    case WILD_AREA_ROCKS:
        info = gWildMonHeaders[headerId].rockSmashMonsInfo;
        break;
    case WILD_AREA_FISHING:
        info = gWildMonHeaders[headerId].fishingMonsInfo;
        break;
    default:
        return 0xFFFFFFFF;
    }
    if (info == NULL || (area == WILD_AREA_FISHING && rod > SUPER_ROD))
        return 0xFFFFFFFF;
    if (area == WILD_AREA_FISHING)
        GenerateFishingEncounter(info, rod);
    else
        TryGenerateWildMon(info, area, 0);
    if (startBattle)
        StartWildBattle();
    return GetMonData(&gEnemyParty[0], MON_DATA_SPECIES) | (GetMonData(&gEnemyParty[0], MON_DATA_LEVEL) << 16);
}
#endif
