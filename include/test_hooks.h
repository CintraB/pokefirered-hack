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
};

extern struct TestMailbox gTestMailbox;

void TestHooks_Run(void);

#endif // TESTBUILD

#endif // GUARD_TEST_HOOKS_H
