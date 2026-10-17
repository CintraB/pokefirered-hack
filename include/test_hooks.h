#ifndef GUARD_TEST_HOOKS_H
#define GUARD_TEST_HOOKS_H

// Test-only shortcuts for the automated test pipeline (make firered_switch TESTBUILD=1).
// The playable ROM is built without TESTBUILD and contains none of this.
#if TESTBUILD

#include "constants/pokemon.h"

// The test runner writes arg0/arg1 (and clears result/done), then cmd. Once per frame
// TestHooks_Run executes a pending command, stores result, clears cmd and sets done = 1.
struct TestMailbox
{
    u32 cmd;
    u32 arg0;
    u32 arg1;
    u32 result;
    u32 done;
};

enum
{
    TEST_CMD_NONE,
    TEST_CMD_COUNT_SHINIES,     // arg0 = how many mons, arg1 = with Shiny Charm (0/1); result = shinies
    TEST_CMD_SET_DEX_COMPLETE,  // every mon HasAllMons() needs seen+caught, National Dex on; result = HasAllMons()
    TEST_CMD_GIVE_ITEM,         // arg0 = item, arg1 = quantity; result = AddBagItem()
    TEST_CMD_CHECK_SHINY,       // arg0 = personality, arg1 = OT ID: gEnemyParty[0] built with them; result = IsMonShiny()
    TEST_CMD_SET_PARTY_MON,     // arg0 = species | level << 16, arg1 = held item | slot << 16 | friendship << 24 (0 = base); result = party count (0 = bad args)
    TEST_CMD_ENABLE_NATIONAL_DEX, // result = IsNationalPokedexEnabled()
    TEST_CMD_EVOLUTION_TARGET,  // arg0 = species | held item << 16, arg1 = mode | level << 8 | evolution item << 16: mon in gEnemyParty[0]; result = GetEvolutionTargetSpecies()
};

// --- Hack 6: genetic breeding (numbered apart so other hacks can add commands above) -----
enum
{
    TEST_CMD_BREED_SETUP = 0x60, // gTestBreedSetup.parents -> daycare (arg0 = 1: egg pending); result = compatibility (0xFFFFFFFF = bad parent)
    TEST_CMD_BREED_EGGS,         // arg0 = count (<= TEST_BREED_BATCH) eggs handed over; 2-word records in gEnemyParty; result = count
    TEST_CMD_EGG_SHINIES,        // arg0 = count, arg1 = with Shiny Charm (0/1): egg personalities rolled; result = shinies
    TEST_CMD_EGG_PERSONALITY,    // arg0 = trials: handed-over egg's personality == the rolled one; result = matches
    TEST_CMD_PACK_PARTY_MON,     // arg0 = party slot: its record into gEnemyParty; result = 1 (0 = empty slot)
    TEST_CMD_EGGS_READY,         // arg0 = daycare step counter: party eggs hatch on the next cycle; result = eggs
    TEST_CMD_WARP,               // arg0 = map group | map num << 8, arg1 = x | y << 16; result = 1
    TEST_CMD_SET_VAR,            // arg0 = var, arg1 = value; result = VarGet()
    TEST_CMD_GAIN_EVS,           // arg0 = held item | defeated species << 16, arg1 = stat EV | other EVs << 8 | stat << 16: MonGainEVs; EVs (bytes) in gEnemyParty; result = total
    TEST_CMD_SPEED_ORDER,        // arg0/arg1 = speed | item << 16 of two battlers: result = GetWhoStrikesFirst() (0 first, 1 second, 2 tie)
};

#define TEST_BREED_BATCH 64

// A daycare parent built by TEST_CMD_BREED_SETUP (layout read by test/esteira/breeding.py)
struct TestBreedParent
{
    u16 species;
    u16 heldItem;
    u16 moves[MAX_MON_MOVES];
    u8 ivs[NUM_STATS];  // HP, Atk, Def, Spe, SpA, SpD
    u8 gender;          // MON_MALE / MON_FEMALE (ignored for single-gender species)
    u8 nature;
    u8 abilityNum;      // ignored for single-ability species
    u8 padding[3];      // agbcc rounds struct sizes up to 4 bytes: 24 in all
};

struct TestBreedSetup
{
    struct TestBreedParent parents[DAYCARE_MON_COUNT];
    u16 probeMoves[MAX_MON_MOVES];  // the egg records say which of these the egg knows
};

extern struct TestBreedSetup gTestBreedSetup;
// --- end of Hack 6 -------------------------------------------------------------------------

extern struct TestMailbox gTestMailbox;

void TestHooks_Run(void);

#endif // TESTBUILD

#endif // GUARD_TEST_HOOKS_H
