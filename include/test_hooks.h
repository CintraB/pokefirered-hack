#ifndef GUARD_TEST_HOOKS_H
#define GUARD_TEST_HOOKS_H

// Test-only shortcuts for the automated test pipeline (make firered_switch TESTBUILD=1).
// The playable ROM is built without TESTBUILD and contains none of this.
#if TESTBUILD

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
    TEST_CMD_EVOLUTION_TEXT,    // arg0 = species, arg1 = 0: GetEvolutionPageText(species) / 1: the text the open summary's EVOLUTION page printed, into gTestText; result = its length (0xFFFFFFFF = bad species / no summary)
    TEST_CMD_SUMMARY_STATE,     // result = page | mode << 8 | isEgg << 16 of the open summary screen (0xFFFFFFFF = none)
    TEST_CMD_SET_PARTY_EGG,     // arg0 = species, arg1 = slot: an Egg (CreateEgg) in gPlayerParty[slot]; result = party count (0 = bad args)
    TEST_CMD_IVEV_TEXT,         // arg0 = IVs (5 bits each: HP, Atk, Def, Spe, SpA, SpD), EVs in gTestText[0-5] (same order), arg1 = party slot + 1 (0 = a new mon in gEnemyParty[0]): sets them, GetIvEvPageText into gTestText; result = its length
};

#define TEST_TEXT_SIZE 384  // SUMMARY_PAGE_TEXT_SIZE (include/pokemon_summary_screen.h)

extern struct TestMailbox gTestMailbox;
extern u8 gTestText[TEST_TEXT_SIZE];

void TestHooks_Run(void);

#endif // TESTBUILD

#endif // GUARD_TEST_HOOKS_H
