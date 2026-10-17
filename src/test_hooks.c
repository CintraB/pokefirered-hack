#include "global.h"
#include "test_hooks.h"

// Compiles to nothing in the playable ROM: only make firered_switch TESTBUILD=1 defines it.
#if TESTBUILD

#include "event_data.h"
#include "item.h"
#include "pokedex.h"
#include "pokemon.h"
#include "constants/items.h"
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
    default:
        result = 0xFFFFFFFF;
        break;
    }
    gTestMailbox.result = result;
    gTestMailbox.cmd = TEST_CMD_NONE;
    gTestMailbox.done = TRUE;
}

#endif // TESTBUILD
