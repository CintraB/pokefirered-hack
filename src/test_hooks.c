#include "global.h"
#include "test_hooks.h"

// Compiles to nothing in the playable ROM: only make firered_switch TESTBUILD=1 defines it.
#if TESTBUILD

#include "event_data.h"
#include "field_specials.h"
#include "item.h"
#include "pokedex.h"
#include "pokemon.h"
#include "constants/items.h"
#include "constants/pokemon.h"
#include "constants/pokedex.h"
#include "constants/species.h"

struct TestMailbox gTestMailbox;

// Creates `count` mons through the same path wild encounters use (CreateMonWithNature, with
// the player as OT) and counts the shiny ones. The Shiny Charm is put in / taken out of the bag
// for the duration so GetShinyRerolls() sees the requested state, then restored.
static u32 CountShinies(u32 count, bool32 withCharm)
{
    struct Pokemon mon;
    bool8 hadCharm = CheckBagHasItem(ITEM_SHINY_CHARM, 1);
    u32 i;
    u32 shinies = 0;

    if (withCharm && !hadCharm)
        AddBagItem(ITEM_SHINY_CHARM, 1);
    else if (!withCharm && hadCharm)
        RemoveBagItem(ITEM_SHINY_CHARM, 1);

    for (i = 0; i < count; i++)
    {
        CreateMonWithNature(&mon, SPECIES_RATTATA, 5, USE_RANDOM_IVS, i % NUM_NATURES);
        if (IsMonShiny(&mon))
            shinies++;
    }

    if (withCharm && !hadCharm)
        RemoveBagItem(ITEM_SHINY_CHARM, 1);
    else if (!withCharm && hadCharm)
        AddBagItem(ITEM_SHINY_CHARM, 1);
    return shinies;
}

// Same ranges HasAllMons() checks: everything but Mew, Lugia, Ho-Oh, Celebi, Jirachi and Deoxys.
static u32 SetDexComplete(void)
{
    u16 i;

    for (i = 0; i < NATIONAL_DEX_COUNT - 2; i++)
    {
        if (i == KANTO_DEX_COUNT - 1 || (i >= JOHTO_DEX_COUNT - 3 && i < JOHTO_DEX_COUNT))
            continue;
        GetSetPokedexFlag(i + 1, FLAG_SET_SEEN);
        GetSetPokedexFlag(i + 1, FLAG_SET_CAUGHT);
    }
    EnableNationalPokedex();
    return HasAllMons();
}

// A mon with a fixed personality and OT ID (no rerolls apply), left in gEnemyParty[0] so the
// runner can also read it back.
static u32 CheckShiny(u32 personality, u32 otId)
{
    CreateMon(&gEnemyParty[0], SPECIES_RATTATA, 5, 0, TRUE, personality, OT_ID_PRESET, otId);
    return IsMonShiny(&gEnemyParty[0]);
}

// Evolution tests: a mon the player could own (player as OT, fixed IVs) with a fixed
// personality that is never shiny for this player, so the evolution scene looks the same on
// every run.
#define TEST_MON_FIXED_IV 15

static void CreateTestMon(struct Pokemon *mon, u16 species, u8 level, u16 heldItem)
{
    u32 otId = GetPlayerTrainerId();
    // shiny value = hi(ot) ^ lo(ot) ^ hi(pid) ^ lo(pid) = 0x100, far from the shiny range
    u32 personality = (((otId >> 16) ^ (otId & 0xFFFF) ^ 0x100) & 0xFFFF) << 16;

    CreateMon(mon, species, level, TEST_MON_FIXED_IV, TRUE, personality, OT_ID_PLAYER_ID, 0);
    SetMonData(mon, MON_DATA_HELD_ITEM, &heldItem);
}

static bool32 IsValidTestMon(u16 species, u8 level)
{
    return species != SPECIES_NONE && species < NUM_SPECIES && level != 0 && level <= MAX_LEVEL;
}

// Puts the mon in gPlayerParty[slot] (a filled slot or the first free one).
static u32 SetPartyMon(u32 arg0, u32 arg1)
{
    u16 species = arg0 & 0xFFFF;
    u8 level = (arg0 >> 16) & 0xFF;
    u16 heldItem = arg1 & 0xFFFF;
    u8 slot = (arg1 >> 16) & 0xFF;

    if (!IsValidTestMon(species, level) || slot >= PARTY_SIZE || slot > CalculatePlayerPartyCount())
        return 0;
    CreateTestMon(&gPlayerParty[slot], species, level, heldItem);
    return CalculatePlayerPartyCount();
}

// GetEvolutionTargetSpecies() for a mon built in gEnemyParty[0], in any mode (trade included).
static u32 EvolutionTarget(u32 arg0, u32 arg1)
{
    u16 species = arg0 & 0xFFFF;
    u16 heldItem = arg0 >> 16;
    u8 mode = arg1 & 0xFF;
    u8 level = (arg1 >> 8) & 0xFF;
    u16 evolutionItem = arg1 >> 16;

    if (!IsValidTestMon(species, level))
        return 0xFFFFFFFF;
    CreateTestMon(&gEnemyParty[0], species, level, heldItem);
    return GetEvolutionTargetSpecies(&gEnemyParty[0], mode, evolutionItem);
}

void TestHooks_Run(void)
{
    u32 result = 0;

    switch (gTestMailbox.cmd)
    {
    case TEST_CMD_NONE:
        return;
    case TEST_CMD_COUNT_SHINIES:
        result = CountShinies(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    case TEST_CMD_SET_DEX_COMPLETE:
        result = SetDexComplete();
        break;
    case TEST_CMD_GIVE_ITEM:
        result = AddBagItem(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    case TEST_CMD_CHECK_SHINY:
        result = CheckShiny(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    case TEST_CMD_SET_PARTY_MON:
        result = SetPartyMon(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    case TEST_CMD_ENABLE_NATIONAL_DEX:
        EnableNationalPokedex();
        result = IsNationalPokedexEnabled();
        break;
    case TEST_CMD_EVOLUTION_TARGET:
        result = EvolutionTarget(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    default:
        result = 0xFFFFFFFF;
        break;
    }
    gTestMailbox.result = result;
    gTestMailbox.cmd = TEST_CMD_NONE;
    gTestMailbox.done = TRUE;
}

#endif // TESTBUILD
