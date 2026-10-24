#ifndef GUARD_WILD_ENCOUNTER_H
#define GUARD_WILD_ENCOUNTER_H

#include "global.h"

#define LAND_WILD_COUNT     12
#define WATER_WILD_COUNT    5
#define ROCK_WILD_COUNT     5
#define FISH_WILD_COUNT     10

#define NUM_ALTERING_CAVE_TABLES 9

struct WildPokemon
{
    u8 minLevel;
    u8 maxLevel;
    u16 species;
};

struct WildPokemonInfo
{
    u8 encounterRate;
    const struct WildPokemon *wildPokemon;
};

struct WildPokemonHeader
{
    u8 mapGroup;
    u8 mapNum;
    const struct WildPokemonInfo *landMonsInfo;
    const struct WildPokemonInfo *waterMonsInfo;
    const struct WildPokemonInfo *rockSmashMonsInfo;
    const struct WildPokemonInfo *fishingMonsInfo;
};

extern const struct WildPokemonHeader gWildMonHeaders[];

// Hack 7 — frente B
struct WildMonTimeTable
{
    u8 mapGroup;
    u8 mapNum;
    u16 species[3][LAND_WILD_COUNT]; // 0 = morning, 1 = afternoon, 2 = night
};

extern const struct WildMonTimeTable gWildMonTimeTables[];
u16 GetTimeOfDayLandSpecies(u8 mapGroup, u8 mapNum, u8 slot, u8 period, u16 fallback);

// Hack 8: a FireRed slot whose LeafGreen twin is a LeafGreen exclusive (generated from
// wild_encounters.json into src/data/wild_encounters_leafgreen.h); the slot rolls 50/50
struct WildLeafGreenSwap
{
    const struct WildPokemonInfo *info; // the FireRed table
    u8 slot;
    struct WildPokemon mon;             // the LeafGreen line of the slot (species and levels)
};

bool8 IsLeafGreenSlotSpeciesOnMap(const struct WildPokemonHeader *header, u16 species);

void DisableWildEncounters(bool8 disabled);
bool8 StandardWildEncounter(u32 currMetatileAttrs, u16 previousMetaTileBehavior);
bool8 SweetScentWildEncounter(void);
bool8 DoesCurrentMapHaveFishingMons(void);
void FishingWildEncounter(u8 rod);
u16 GetLocalWildMon(bool8 *isWaterMon);
u16 GetLocalWaterMon(void);
bool8 UpdateRepelCounter(void);
void DisableWildEncounters(bool8 state);
u8 GetUnownLetterByPersonalityLoByte(u32 personality);
bool8 SweetScentWildEncounter(void);
void SeedWildEncounterRng(u16 randVal);
void ResetEncounterRateModifiers(void);
bool8 TryStandardWildEncounter(u32 currMetatileAttrs);

#endif // GUARD_WILD_ENCOUNTER_H
