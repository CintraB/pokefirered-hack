#include "global.h"
#include "test_hooks.h"

// Compiles to nothing in the playable ROM: only make firered_switch TESTBUILD=1 defines it.
#if TESTBUILD

#include "characters.h"
#include "daycare.h"
#include "event_data.h"
#include "field_specials.h"
#include "item.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_summary_screen.h"
#include "string_util.h"
#include "constants/items.h"
#include "constants/pokemon.h"
#include "constants/pokedex.h"
#include "constants/species.h"
// Hack 6 (breeding)
#include "battle.h"
#include "battle_main.h"
#include "field_fadetransition.h"
#include "overworld.h"
#include "random.h"
#include "constants/daycare.h"
#include "constants/maps.h"
#include "constants/moves.h"
// Hack 7 (day/night)
#include "day_night.h"
// Hack 7 — frente B
#include "wild_encounter.h"
extern u32 TestSpeciesOnMap(u8 mapGroup, u8 mapNum, u16 species);
extern u32 TestLandSpecies(u8 mapGroup, u8 mapNum, u8 slot, u8 period);

STATIC_ASSERT(TEST_TEXT_SIZE >= SUMMARY_PAGE_TEXT_SIZE, TestTextHoldsASummaryPage);

struct TestMailbox gTestMailbox;
EWRAM_DATA u8 gTestText[TEST_TEXT_SIZE] = {0};

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

// Puts the mon in gPlayerParty[slot] (a filled slot or the first free one). A nonzero
// friendship replaces the species' base friendship (friendship evolutions).
static u32 SetPartyMon(u32 arg0, u32 arg1)
{
    u16 species = arg0 & 0xFFFF;
    u8 level = (arg0 >> 16) & 0xFF;
    u16 heldItem = arg1 & 0xFFFF;
    u8 slot = (arg1 >> 16) & 0xFF;
    u8 friendship = arg1 >> 24;

    if (!IsValidTestMon(species, level) || slot >= PARTY_SIZE || slot > CalculatePlayerPartyCount())
        return 0;
    CreateTestMon(&gPlayerParty[slot], species, level, heldItem);
    if (friendship != 0)
        SetMonData(&gPlayerParty[slot], MON_DATA_FRIENDSHIP, &friendship);
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

// Hack 4: the EVOLUTION page text, either built by the same function the summary screen uses
// (source 0) or the one the open summary screen printed (source 1), copied to gTestText.
static u32 EvolutionText(u32 species, u32 source)
{
    gTestText[0] = EOS;
    if (source == 0)
    {
        if (species == SPECIES_NONE || species >= NUM_SPECIES)
            return 0xFFFFFFFF;
        GetEvolutionPageText(gTestText, species);
    }
    else if (!PokeSum_TestCopyPageText(gTestText))
    {
        return 0xFFFFFFFF;
    }
    return StringLength(gTestText);
}

// Hack 5: gives these IVs and EVs (the EVs come in gTestText) to gPlayerParty[slot - 1], or to
// a new mon in gEnemyParty[0] (slot 0), and returns its IVs/EVs page text in gTestText.
static u32 IvEvText(u32 packedIvs, u32 slot)
{
    struct Pokemon *mon = slot == 0 ? &gEnemyParty[0] : &gPlayerParty[slot - 1];
    u8 evs[NUM_STATS];
    u8 i;

    if (slot > CalculatePlayerPartyCount())
        return 0xFFFFFFFF;
    for (i = 0; i < NUM_STATS; i++)
        evs[i] = gTestText[i];
    if (slot == 0)
        CreateTestMon(mon, SPECIES_BULBASAUR, 50, ITEM_NONE);
    for (i = 0; i < NUM_STATS; i++)
    {
        u8 iv = (packedIvs >> (5 * i)) & 0x1F;

        SetMonData(mon, MON_DATA_HP_IV + i, &iv);
        SetMonData(mon, MON_DATA_HP_EV + i, &evs[i]);
    }
    CalculateMonStats(mon);
    GetIvEvPageText(gTestText, mon);
    return StringLength(gTestText);
}

static u32 SetPartyEgg(u32 species, u32 slot)
{
    if (species == SPECIES_NONE || species >= NUM_SPECIES || slot >= PARTY_SIZE || slot > CalculatePlayerPartyCount())
        return 0;
    CreateEgg(&gPlayerParty[slot], species, FALSE);
    return CalculatePlayerPartyCount();
}
// --- Hack 6: genetic breeding (test/esteira/breeding.py) ---------------------------------
// The parents go into the real daycare (gSaveBlock1Ptr->daycare) and the eggs come out of
// GiveEggFromDaycare, the same path as the daycare man's script. Results (2 words per egg, see
// PackMonRecord) go to TEST_BREED_RESULTS: gEnemyParty is unused outside battle.
struct TestBreedSetup gTestBreedSetup;
STATIC_ASSERT(sizeof(struct TestBreedParent) == 24, TestBreedParentLayoutMatchesTheRunner) // test/esteira/breeding.py PARENT_FORMAT

#define TEST_BREED_RESULTS ((u32 *)gEnemyParty)

static bool8 HadShinyCharmSet(bool32 withCharm)
{
    bool8 hadCharm = CheckBagHasItem(ITEM_SHINY_CHARM, 1);

    if (withCharm && !hadCharm)
        AddBagItem(ITEM_SHINY_CHARM, 1);
    else if (!withCharm && hadCharm)
        RemoveBagItem(ITEM_SHINY_CHARM, 1);
    return hadCharm;
}

static void RestoreShinyCharm(bool32 withCharm, bool8 hadCharm)
{
    if (withCharm && !hadCharm)
        RemoveBagItem(ITEM_SHINY_CHARM, 1);
    else if (!withCharm && hadCharm)
        AddBagItem(ITEM_SHINY_CHARM, 1);
}

static bool8 IsFixedGender(u16 species)
{
    u8 ratio = gSpeciesInfo[species].genderRatio;

    return ratio == MON_MALE || ratio == MON_FEMALE || ratio == MON_GENDERLESS;
}

static bool8 CreateTestParent(struct BoxPokemon *dest, const struct TestBreedParent *parent)
{
    struct Pokemon mon;
    u16 species = parent->species;
    bool8 twoAbilities;
    u32 personality, tries;
    u8 i;

    if (species == SPECIES_NONE || species >= NUM_SPECIES || parent->nature >= NUM_NATURES || parent->abilityNum > 1)
        return FALSE;
    twoAbilities = gSpeciesInfo[species].abilities[1] != ABILITY_NONE;
    for (tries = 0; ; tries++)
    {
        if (tries > 1000000)
            return FALSE;
        personality = Random32();
        if ((personality % NUM_NATURES) == parent->nature
         && (!twoAbilities || (personality & 1) == parent->abilityNum)
         && (IsFixedGender(species) || GetGenderFromSpeciesAndPersonality(species, personality) == parent->gender))
            break;
    }
    CreateMon(&mon, species, 20, 0, TRUE, personality, OT_ID_PLAYER_ID, 0);
    for (i = 0; i < NUM_STATS; i++)
        SetMonData(&mon, MON_DATA_HP_IV + i, &parent->ivs[i]);
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        SetMonData(&mon, MON_DATA_MOVE1 + i, &parent->moves[i]);
        SetMonData(&mon, MON_DATA_PP1 + i, &gBattleMoves[parent->moves[i]].pp);
    }
    SetMonData(&mon, MON_DATA_HELD_ITEM, &parent->heldItem);
    *dest = mon.box;
    return TRUE;
}

// Both parents into the daycare (emptied first), with an egg pending if `pending`;
// result = compatibility score (0 = no eggs)
static u32 BreedSetup(bool32 pending)
{
    struct DayCare *daycare = &gSaveBlock1Ptr->daycare;
    u8 i;

    memset(daycare, 0, sizeof(*daycare));
    FlagClear(FLAG_PENDING_DAYCARE_EGG);
    for (i = 0; i < DAYCARE_MON_COUNT; i++)
    {
        if (!CreateTestParent(&daycare->mons[i].mon, &gTestBreedSetup.parents[i]))
            return 0xFFFFFFFF;
    }
    if (pending)
        TriggerPendingDaycareEgg();
    return TestHooks_DaycareCompatibility();
}

// word0: IVs (5 bits each, HP Atk Def Spe SpA SpD) | ability slot << 30 | shiny << 31
// word1: nature | gender << 5 (0 male, 1 female, 2 genderless) | isEgg << 7
//        | knows probe move i << (8 + i) | species << 16
static void PackMonRecord(struct Pokemon *mon, u32 *record)
{
    u32 word0 = 0, word1;
    u32 personality = GetMonData(mon, MON_DATA_PERSONALITY);
    u16 species = GetMonData(mon, MON_DATA_SPECIES);
    u8 gender = GetGenderFromSpeciesAndPersonality(species, personality);
    u8 i, j;

    for (i = 0; i < NUM_STATS; i++)
        word0 |= GetMonData(mon, MON_DATA_HP_IV + i) << (5 * i);
    word0 |= (GetMonData(mon, MON_DATA_ABILITY_NUM) & 1) << 30;
    if (GET_SHINY_VALUE(GetMonData(mon, MON_DATA_OT_ID), personality) < SHINY_ODDS)
        word0 |= 1u << 31;
    word1 = (personality % NUM_NATURES);
    word1 |= (gender == MON_MALE ? 0 : gender == MON_FEMALE ? 1 : 2) << 5;
    word1 |= (GetMonData(mon, MON_DATA_IS_EGG) ? 1 : 0) << 7;
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        for (j = 0; j < MAX_MON_MOVES; j++)
        {
            if (gTestBreedSetup.probeMoves[i] != MOVE_NONE
             && GetMonData(mon, MON_DATA_MOVE1 + j) == gTestBreedSetup.probeMoves[i])
                word1 |= 1 << (8 + i);
        }
    }
    word1 |= (u32)species << 16;
    record[0] = word0;
    record[1] = word1;
}

// One egg through the real path (pending egg + GiveEggFromDaycare); returns its party slot
static u8 HandOverEgg(void)
{
    TriggerPendingDaycareEgg();
    GiveEggFromDaycare();
    FlagClear(FLAG_PENDING_DAYCARE_EGG); // as the daycare man's script does
    return CalculatePlayerPartyCount() - 1;
}

static void RemovePartyEgg(u8 slot)
{
    ZeroMonData(&gPlayerParty[slot]);
    CalculatePlayerPartyCount();
}

static u32 BreedEggs(u32 count)
{
    u32 i;
    u8 slot;

    if (count > TEST_BREED_BATCH || CalculatePlayerPartyCount() >= PARTY_SIZE)
        return 0xFFFFFFFF;
    for (i = 0; i < count; i++)
    {
        slot = HandOverEgg();
        PackMonRecord(&gPlayerParty[slot], &TEST_BREED_RESULTS[2 * i]);
        RemovePartyEgg(slot);
    }
    return count;
}

static u32 CountEggShinies(u32 count, bool32 withCharm)
{
    bool8 hadCharm = HadShinyCharmSet(withCharm);
    u32 shinies = 0;

    TestHooks_RollEggPersonalities(count, GetPlayerTrainerId(), &shinies);
    RestoreShinyCharm(withCharm, hadCharm);
    return shinies;
}

// The handed-over egg gets exactly the personality TestHooks_RollEggPersonalities rolls from
// the same RNG state (so CountEggShinies measures the real eggs); result = matching eggs.
// Interrupts are off meanwhile: the VBlank handler also draws from the RNG.
static u32 CheckEggPersonality(u32 trials)
{
    u32 i, rng, personality, shinies = 0, matches = 0;
    u16 ime = REG_IME;
    u8 slot;

    if (CalculatePlayerPartyCount() >= PARTY_SIZE)
        return 0xFFFFFFFF;
    for (i = 0; i < trials; i++)
    {
        REG_IME = 0;
        rng = gRngValue;
        TriggerPendingDaycareEgg();
        personality = TestHooks_RollEggPersonalities(1, 0, &shinies);
        gRngValue = rng;
        slot = HandOverEgg(); // triggers the pending egg again from the same RNG state
        REG_IME = ime;
        if (GetMonData(&gPlayerParty[slot], MON_DATA_PERSONALITY) == personality)
            matches++;
        RemovePartyEgg(slot);
    }
    return matches;
}

static u32 PackPartyMon(u32 slot)
{
    if (slot >= CalculatePlayerPartyCount())
        return 0;
    PackMonRecord(&gPlayerParty[slot], TEST_BREED_RESULTS);
    return 1;
}

// Every egg in the party hatches on the next egg cycle, which ends after the daycare's step
// counter reaches 255 (arg = its new value); result = eggs in the party
static u32 MakeEggsReady(u32 stepCounter)
{
    u8 i, zero = 0;
    u32 eggs = 0;

    for (i = 0; i < CalculatePlayerPartyCount(); i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
        {
            SetMonData(&gPlayerParty[i], MON_DATA_FRIENDSHIP, &zero);
            eggs++;
        }
    }
    gSaveBlock1Ptr->daycare.stepCounter = stepCounter;
    return eggs;
}

static u32 WarpTo(u32 map, u32 xy)
{
    SetWarpDestination(map & 0xFF, map >> 8, WARP_ID_NONE, xy & 0xFFFF, xy >> 16);
    DoWarp();
    ResetInitialPlayerAvatarState();
    return 1;
}

// MonGainEVs on a mon holding `item` that beat `defeated`: arg1 = EV of `stat` | EV of the
// other stats << 8 | stat << 16. The 6 EVs (bytes) go to TEST_BREED_RESULTS; result = total
static u32 GainEVs(u32 arg0, u32 arg1)
{
    struct Pokemon mon;
    u16 item = arg0 & 0xFFFF, defeated = arg0 >> 16;
    u8 stat = (arg1 >> 16) & 0xFF;
    u8 ev, i;
    u32 total = 0;

    if (stat >= NUM_STATS || defeated == SPECIES_NONE || defeated >= NUM_SPECIES)
        return 0xFFFFFFFF;
    CreateMon(&mon, SPECIES_RATTATA, 50, 0, TRUE, 0, OT_ID_PRESET, 0);
    SetMonData(&mon, MON_DATA_HELD_ITEM, &item);
    for (i = 0; i < NUM_STATS; i++)
    {
        ev = (i == stat) ? (arg1 & 0xFF) : ((arg1 >> 8) & 0xFF);
        SetMonData(&mon, MON_DATA_HP_EV + i, &ev);
    }
    MonGainEVs(&mon, defeated);
    for (i = 0; i < NUM_STATS; i++)
    {
        ev = GetMonData(&mon, MON_DATA_HP_EV + i);
        ((u8 *)TEST_BREED_RESULTS)[i] = ev;
        total += ev;
    }
    return total;
}

// GetWhoStrikesFirst(0, 1) for two opposing-side battlers (no badge boost) given speed | item << 16
// each, no abilities, weather, status or stat stages; the battle globals are restored after
static u32 SpeedOrder(u32 arg0, u32 arg1)
{
    struct BattlePokemon saved[2];
    u8 positions[2], count = gBattlersCount;
    u32 typeFlags = gBattleTypeFlags;
    u16 weather = gBattleWeather;
    u32 args[2];
    u8 i, j, result;

    args[0] = arg0;
    args[1] = arg1;
    for (i = 0; i < 2; i++)
    {
        saved[i] = gBattleMons[i];
        positions[i] = gBattlerPositions[i];
        memset(&gBattleMons[i], 0, sizeof(gBattleMons[i]));
        gBattleMons[i].species = SPECIES_RATTATA;
        gBattleMons[i].hp = 1;
        gBattleMons[i].speed = args[i] & 0xFFFF;
        gBattleMons[i].item = args[i] >> 16;
        for (j = 0; j < NUM_BATTLE_STATS; j++)
            gBattleMons[i].statStages[j] = DEFAULT_STAT_STAGE;
    }
    gBattlerPositions[0] = B_POSITION_OPPONENT_LEFT;
    gBattlerPositions[1] = B_POSITION_OPPONENT_RIGHT;
    gBattlersCount = 2;
    gBattleTypeFlags = 0;
    gBattleWeather = 0;
    result = GetWhoStrikesFirst(0, 1, TRUE);
    for (i = 0; i < 2; i++)
    {
        gBattleMons[i] = saved[i];
        gBattlerPositions[i] = positions[i];
    }
    gBattlersCount = count;
    gBattleTypeFlags = typeFlags;
    gBattleWeather = weather;
    return result;
}
// --- end of Hack 6 -------------------------------------------------------------------------

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
    case TEST_CMD_EVOLUTION_TEXT:
        result = EvolutionText(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    case TEST_CMD_SUMMARY_STATE:
        result = PokeSum_TestGetState();
        break;
    case TEST_CMD_SET_PARTY_EGG:
        result = SetPartyEgg(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    case TEST_CMD_IVEV_TEXT:
        result = IvEvText(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    // Hack 6 (breeding)
    case TEST_CMD_BREED_SETUP:      result = BreedSetup(gTestMailbox.arg0); break;
    case TEST_CMD_BREED_EGGS:       result = BreedEggs(gTestMailbox.arg0); break;
    case TEST_CMD_EGG_SHINIES:      result = CountEggShinies(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_EGG_PERSONALITY:  result = CheckEggPersonality(gTestMailbox.arg0); break;
    case TEST_CMD_PACK_PARTY_MON:   result = PackPartyMon(gTestMailbox.arg0); break;
    case TEST_CMD_EGGS_READY:       result = MakeEggsReady(gTestMailbox.arg0); break;
    case TEST_CMD_WARP:             result = WarpTo(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_SET_VAR:          VarSet(gTestMailbox.arg0, gTestMailbox.arg1); result = VarGet(gTestMailbox.arg0); break;
    case TEST_CMD_GAIN_EVS:         result = GainEVs(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_SPEED_ORDER:      result = SpeedOrder(gTestMailbox.arg0, gTestMailbox.arg1); break;
    // Hack 7 (day/night): the in-game clock
    case TEST_CMD_SET_CLOCK:
        DayNight_SetClock(gTestMailbox.arg0, gTestMailbox.arg1);
        result = DayNight_GetMinuteOfDay();
        break;
    case TEST_CMD_CLOCK_INFO:       result = DayNight_GetMinuteOfDay() | DayNight_GetPeriod() << 16; break;
    // Hack 7 front A: start

    // Hack 7 front A: end
    // Hack 7 front B: start
    case TEST_CMD_LAND_SPECIES:
        result = TestLandSpecies(gTestMailbox.arg0 >> 8, gTestMailbox.arg0 & 0xFF, gTestMailbox.arg1 & 0xFF, gTestMailbox.arg1 >> 8);
        break;
    case TEST_CMD_SPECIES_ON_MAP:
        result = TestSpeciesOnMap(gTestMailbox.arg0 >> 8, gTestMailbox.arg0 & 0xFF, gTestMailbox.arg1);
        break;

    // Hack 7 front B: end
    // Hack 7 front C: start

    // Hack 7 front C: end
    // Hack 7 front D: start

    // Hack 7 front D: end
    // Hack 7 front E: start

    // Hack 7 front E: end
    default:
        result = 0xFFFFFFFF;
        break;
    }
    gTestMailbox.result = result;
    gTestMailbox.cmd = TEST_CMD_NONE;
    gTestMailbox.done = TRUE;
}

#endif // TESTBUILD
