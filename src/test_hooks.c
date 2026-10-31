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
extern u32 TestRollWild(u8 area, u8 rod, bool8 startBattle); // Hack 8
// Hack 7 — frente C
#include "pokemon_storage_system.h"

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

// Same ranges HasAllMons() checks (everything but Lugia, Ho-Oh, Celebi, Jirachi and Deoxys) plus Mew,
// so the Shiny Charm condition (HasAllKantoMonsWithMew, the 151 of Kanto) holds as well.
static u32 SetDexComplete(void)
{
    u16 i;

    for (i = 0; i < NATIONAL_DEX_COUNT - 2; i++)
    {
        if (i >= JOHTO_DEX_COUNT - 3 && i < JOHTO_DEX_COUNT)
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

// Hack 7 front D: friendship line of the EVOLUTION page. mode 0: GetFriendshipLineText(arg0) into
// gTestText; 1: the line rebuilt from the friendship of the mon the open summary shows (0xFFFFFFFF
// with no summary open or on an egg, which has no line); 2: sets the friendship of
// gPlayerParty[arg0] to 0.
static u32 FriendshipText(u32 arg0, u32 mode)
{
    u8 zero = 0;

    gTestText[0] = EOS;
    if (mode == 2)
    {
        if (arg0 >= CalculatePlayerPartyCount())
            return 0xFFFFFFFF;
        SetMonData(&gPlayerParty[arg0], MON_DATA_FRIENDSHIP, &zero);
        return GetMonData(&gPlayerParty[arg0], MON_DATA_FRIENDSHIP);
    }
    if (mode == 0)
        GetFriendshipLineText(gTestText, arg0);
    else if (!PokeSum_TestCopyFriendshipText(gTestText))
        return 0xFFFFFFFF;
    return StringLength(gTestText);
}
// --- end of Hack 7 front D ------------------------------------------------------------------

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

// Hack 7 front C: post-League scene (rare egg)
// Marks the first n Kanto species seen and caught, without turning the National Dex on;
// result = Kanto species caught.
static u32 SetKantoOwned(u32 n)
{
    u16 i;

    if (n > KANTO_DEX_COUNT)
        n = KANTO_DEX_COUNT;
    for (i = 1; i <= n; i++)
    {
        GetSetPokedexFlag(i, FLAG_SET_SEEN);
        GetSetPokedexFlag(i, FLAG_SET_CAUGHT);
    }
    return GetKantoPokedexCount(FLAG_GET_CAUGHT);
}

// Fills every box slot with a plain mon; result = filled slots.
static u32 FillPC(void)
{
    struct Pokemon mon;
    u32 box, slot, count = 0;

    CreateMon(&mon, SPECIES_RATTATA, 5, TEST_MON_FIXED_IV, TRUE, 0, OT_ID_PLAYER_ID, 0);
    for (box = 0; box < TOTAL_BOXES_COUNT; box++)
    {
        for (slot = 0; slot < IN_BOX_COUNT; slot++)
        {
            gPokemonStoragePtr->boxes[box][slot] = mon.box;
            count++;
        }
    }
    return count;
}

static u32 SetFlagHook(u32 flag, u32 on)
{
    if (flag >= FLAGS_COUNT)
        return 0xFFFFFFFF;
    if (on)
        FlagSet(flag);
    else
        FlagClear(flag);
    return FlagGet(flag);
}
// --- end of Hack 7 front C ------------------------------------------------------------------

// Hack 7 — frente A: wild battle started by a field script, as setwildbattle + dowildbattle do
#include "script.h"
#include "script_pokemon_util.h"

static const u8 sWildBattleScript[] =
{
    0x69, // lockall
    0xB7, // dowildbattle
    0x6B, // releaseall
    0x02, // end
};
// --- end of Hack 7 front A ------------------------------------------------------------------

// Tela de novidades: opens through the real special, from a field script built in gTestText
#include "novidades.h"

extern u16 (*const gSpecials[])(void);
extern u16 (*const gSpecialsEnd[])(void);

static u32 OpenNovidades(void)
{
    u32 special;

    for (special = 0; &gSpecials[special] < gSpecialsEnd; special++)
    {
        if ((void *)gSpecials[special] == (void *)OpenNovidadesScreen)
            break;
    }
    if (&gSpecials[special] >= gSpecialsEnd)
        return 0xFFFFFFFF;
    gTestText[0] = 0x69;            // lockall
    gTestText[1] = 0x97;            // fadescreen FADE_TO_BLACK
    gTestText[2] = 1;
    gTestText[3] = 0x25;            // special OpenNovidadesScreen
    gTestText[4] = special & 0xFF;
    gTestText[5] = special >> 8;
    gTestText[6] = 0x27;            // waitstate
    gTestText[7] = 0x6B;            // releaseall
    gTestText[8] = 0x02;            // end
    ScriptContext_SetupScript(gTestText);
    return special;
}
// --- end of novidades -----------------------------------------------------------------------

// POK-43: CalculateBaseDamage between two party mons, outside any real battle state
#include "battle_util.h"

// Same fill as CopyPlayerPartyMonToBattleData (src/pokemon.c), into a local struct
static void PartyMonToBattleMon(struct Pokemon *mon, struct BattlePokemon *bmon)
{
    s32 i;
    u8 nickname[POKEMON_NAME_LENGTH * 2];

    memset(bmon, 0, sizeof(*bmon));
    bmon->species = GetMonData(mon, MON_DATA_SPECIES, NULL);
    bmon->item = GetMonData(mon, MON_DATA_HELD_ITEM, NULL);
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        bmon->moves[i] = GetMonData(mon, MON_DATA_MOVE1 + i, NULL);
        bmon->pp[i] = GetMonData(mon, MON_DATA_PP1 + i, NULL);
    }
    bmon->ppBonuses = GetMonData(mon, MON_DATA_PP_BONUSES, NULL);
    bmon->friendship = GetMonData(mon, MON_DATA_FRIENDSHIP, NULL);
    bmon->experience = GetMonData(mon, MON_DATA_EXP, NULL);
    bmon->hpIV = GetMonData(mon, MON_DATA_HP_IV, NULL);
    bmon->attackIV = GetMonData(mon, MON_DATA_ATK_IV, NULL);
    bmon->defenseIV = GetMonData(mon, MON_DATA_DEF_IV, NULL);
    bmon->speedIV = GetMonData(mon, MON_DATA_SPEED_IV, NULL);
    bmon->spAttackIV = GetMonData(mon, MON_DATA_SPATK_IV, NULL);
    bmon->spDefenseIV = GetMonData(mon, MON_DATA_SPDEF_IV, NULL);
    bmon->personality = GetMonData(mon, MON_DATA_PERSONALITY, NULL);
    bmon->status1 = GetMonData(mon, MON_DATA_STATUS, NULL);
    bmon->level = GetMonData(mon, MON_DATA_LEVEL, NULL);
    bmon->hp = GetMonData(mon, MON_DATA_HP, NULL);
    bmon->maxHP = GetMonData(mon, MON_DATA_MAX_HP, NULL);
    bmon->attack = GetMonData(mon, MON_DATA_ATK, NULL);
    bmon->defense = GetMonData(mon, MON_DATA_DEF, NULL);
    bmon->speed = GetMonData(mon, MON_DATA_SPEED, NULL);
    bmon->spAttack = GetMonData(mon, MON_DATA_SPATK, NULL);
    bmon->spDefense = GetMonData(mon, MON_DATA_SPDEF, NULL);
    bmon->isEgg = GetMonData(mon, MON_DATA_IS_EGG, NULL);
    bmon->abilityNum = GetMonData(mon, MON_DATA_ABILITY_NUM, NULL);
    bmon->otId = GetMonData(mon, MON_DATA_OT_ID, NULL);
    bmon->type1 = gSpeciesInfo[bmon->species].types[0];
    bmon->type2 = gSpeciesInfo[bmon->species].types[1];
    bmon->ability = GetAbilityBySpecies(bmon->species, bmon->abilityNum);
    GetMonData(mon, MON_DATA_NICKNAME, nickname);
    StringCopy_Nickname(bmon->nickname, nickname);
    GetMonData(mon, MON_DATA_OT_NAME, bmon->otName);
    for (i = 0; i < NUM_BATTLE_STATS; i++)
        bmon->statStages[i] = DEFAULT_STAT_STAGE;
}

// Every global CalculateBaseDamage reads (or AbilityBattleEffects writes) is saved, pinned to a
// neutral value and put back: no crit, no weather, no badge boost (link flag), no field ability
// or sport (no battlers on the field), no Flash Fire (zeroed resource flags).
static u32 CalcDamage(u16 move)
{
    struct BattlePokemon attacker, defender;
    struct ResourceFlags flags;
    struct BattleResources resources;
    struct BattleResources *savedResources = gBattleResources;
    u16 savedMove = gCurrentMove, savedPower = gBattleMovePower, savedWeather = gBattleWeather;
    u32 savedTypeFlags = gBattleTypeFlags;
    u8 savedCrit = gCritMultiplier, savedCount = gBattlersCount, savedAbility = gLastUsedAbility;
    u8 savedAttacker = gBattlerAttacker, savedTarget = gBattlerTarget;
    s32 damage;

    if (move == MOVE_NONE || move >= MOVES_COUNT)
        return 0xFFFFFFFF;
    PartyMonToBattleMon(&gPlayerParty[0], &attacker);
    PartyMonToBattleMon(&gPlayerParty[1], &defender);
    memset(&flags, 0, sizeof(flags));
    memset(&resources, 0, sizeof(resources));
    resources.flags = &flags;

    gBattleResources = &resources;
    gCurrentMove = move;
    gCritMultiplier = 1;
    gBattleWeather = 0;
    gBattleTypeFlags = BATTLE_TYPE_LINK;
    gBattlersCount = 0;
    damage = CalculateBaseDamage(&attacker, &defender, move, 0, 0, 0, 0, 1);

    gBattleResources = savedResources;
    gCurrentMove = savedMove;
    gBattleMovePower = savedPower;
    gBattleWeather = savedWeather;
    gBattleTypeFlags = savedTypeFlags;
    gCritMultiplier = savedCrit;
    gBattlersCount = savedCount;
    gLastUsedAbility = savedAbility;
    gBattlerAttacker = savedAttacker;
    gBattlerTarget = savedTarget;
    return damage;
}

// gTypeEffectiveness the way Cmd_typecalc walks it, multiplier x 100; the Foresight marker is
// skipped (not stopped at), so the Ghost immunities after it count.
static u32 TypeEffectiveness(u8 moveType, u8 type1, u8 type2)
{
    u32 multiplier = 100;
    s32 i;

    for (i = 0; TYPE_EFFECT_ATK_TYPE(i) != TYPE_ENDTABLE; i += 3)
    {
        if (TYPE_EFFECT_ATK_TYPE(i) != moveType)
            continue;
        if (TYPE_EFFECT_DEF_TYPE(i) == type1)
            multiplier = multiplier * TYPE_EFFECT_MULTIPLIER(i) / 10;
        if (TYPE_EFFECT_DEF_TYPE(i) == type2 && type1 != type2)
            multiplier = multiplier * TYPE_EFFECT_MULTIPLIER(i) / 10;
    }
    return multiplier;
}
// --- end of POK-43 --------------------------------------------------------------------------

// POK-44: achievements and battle journal state in the save
#include "conquistas.h"
#include "data/conquistas_ids.h"
extern u8 gConquistasSilencio; // src/conquistas_aviso.c (only in TESTBUILD)
#include "constants/battle_setup.h"
#include "constants/opponents.h"

static u32 ConqEstado(u8 num)
{
    if (!Conquistas_NumValido(num))
        return 0xFFFFFFFF;
    return Conquistas_GetEstado(num) | Conquistas_Entregue(num) << 8 | Conquistas_DegrauEntregue(num) << 16
         | Conquistas_DegrauAtual(num) << 24;
}

static u32 ConqContador(u32 which)
{
    const struct ConquistasSave *conq = &gSaveBlock1Ptr->conquistas;

    switch (which)
    {
    case 0: return conq->vitoriasTreinador;
    case 1: return conq->shiniesObtidos;
    case 2: return conq->origem | conq->resumoPendente << 8;
    case 3: return conq->magic;
    }
    if (which - 4 < CONQ_ABAS_COUNT)
    {
        u8 feitas, validas;

        Conquistas_ContarAba(which - 4, &feitas, &validas);
        return feitas | validas << 8;
    }
    return 0xFFFFFFFF;
}

static u32 ConqReset(u32 jogoNovo)
{
    if (jogoNovo)
    {
        Conquistas_IniciarJogoNovo();
    }
    else
    {
        // a save from before the achievements: both areas were unused and zeroed
        memset(&gSaveBlock1Ptr->conquistas, 0, sizeof(gSaveBlock1Ptr->conquistas));
        memset(&gSaveBlock2Ptr->diario, 0, sizeof(gSaveBlock2Ptr->diario));
    }
    return gSaveBlock1Ptr->conquistas.magic;
}

static u32 ConqAplicar(u32 num, u32 opDegrau)
{
    if (num >= 0x100 || !Conquistas_NumValido(num))
        return 0xFFFFFFFF;
    switch (opDegrau & 0xFF)
    {
    case 0: Conquistas_Marcar(num); break;
    case 1: Conquistas_Perder(num); break;
    case 2: Conquistas_SetEntregue(num); break;
    case 3: Conquistas_SetDegrauEntregue(num, opDegrau >> 8); break;
    default: return 0xFFFFFFFF;
    }
    return ConqEstado(num);
}

// A mon of the player (OT) in a PC slot, for the old-save scan: shiny PID and/or hatched (MET_LEVEL 0, 6 IVs 31).
static u32 ConqPcMon(u32 arg0, u32 arg1)
{
    u8 box = arg0 & 0xFF, pos = (arg0 >> 8) & 0xFF, opcoes = (arg0 >> 16) & 0xFF;
    u16 species = arg1 & 0xFFFF;
    u8 level = (arg1 >> 16) & 0xFF, metLevel = 0;
    u32 otId = GetPlayerTrainerId();
    // shiny value = hi(ot) ^ lo(ot) ^ hi(pid) ^ lo(pid): 0 (shiny) or 0x100 (far from the shiny range)
    u32 personality = (((otId >> 16) ^ (otId & 0xFFFF) ^ ((opcoes & 1) ? 0 : 0x100)) & 0xFFFF) << 16;
    struct Pokemon mon;

    if (box >= TOTAL_BOXES_COUNT || pos >= IN_BOX_COUNT)
        return 0xFFFFFFFF;
    if (species == SPECIES_NONE)
    {
        ZeroBoxMonData(GetBoxedMonPtr(box, pos));
        return GetBoxMonDataAt(box, pos, MON_DATA_SPECIES);
    }
    if (!IsValidTestMon(species, level))
        return 0xFFFFFFFF;
    CreateMon(&mon, species, level, (opcoes & 2) ? MAX_PER_STAT_IVS : TEST_MON_FIXED_IV, TRUE, personality,
              OT_ID_PLAYER_ID, 0);
    if (opcoes & 2)
        SetMonData(&mon, MON_DATA_MET_LEVEL, &metLevel);
    *GetBoxedMonPtr(box, pos) = mon.box;
    return GetBoxMonDataAt(box, pos, MON_DATA_SPECIES);
}

// trainerbattle_no_intro <trainer>, <defeat text> run from a field script in gTestText, as the wild battle hook does;
// the defeat text ("…") sits in gTestText too, after the script. sTrainerObjectEventLocalId = 0 and
// VAR_LAST_TALKED = 0: the reveal movement of EventScript_DoNoIntroTrainerBattle finds no object and is skipped.
#define TEST_TRAINER_DEFEAT_TEXT 32  // offset of the defeat text in gTestText

static u32 StartTrainerBattle(u32 trainer)
{
    u8 *s = gTestText;
    u32 texto = (u32)&gTestText[TEST_TRAINER_DEFEAT_TEXT];

    if (trainer == 0 || trainer >= NUM_TRAINERS)
        return 0xFFFFFFFF;
    gTestText[TEST_TRAINER_DEFEAT_TEXT] = CHAR_ELLIPSIS;
    gTestText[TEST_TRAINER_DEFEAT_TEXT + 1] = EOS;
    gSpecialVar_LastTalked = 0;
    *s++ = 0x69;                                // lockall
    *s++ = 0x5C;                                // trainerbattle
    *s++ = TRAINER_BATTLE_SINGLE_NO_INTRO_TEXT;
    *s++ = trainer & 0xFF;
    *s++ = trainer >> 8;
    *s++ = 0;                                   // local id
    *s++ = 0;
    *s++ = texto & 0xFF;                        // defeat text
    *s++ = (texto >> 8) & 0xFF;
    *s++ = (texto >> 16) & 0xFF;
    *s++ = texto >> 24;
    *s++ = 0x6B;                                // releaseall (the battle returns here: gotopostbattlescript)
    *s++ = 0x02;                                // end
    ScriptContext_SetupScript(gTestText);
    return 1;
}

static u32 SetPartyMove(u32 arg0, u16 move)
{
    u8 slot = arg0 & 0xFF, index = (arg0 >> 8) & 0xFF;
    u8 pp;

    if (slot >= PARTY_SIZE || index >= MAX_MON_MOVES || move == MOVE_NONE || move >= MOVES_COUNT
     || GetMonData(&gPlayerParty[slot], MON_DATA_SPECIES) == SPECIES_NONE)
        return 0xFFFFFFFF;
    pp = gBattleMoves[move].pp;
    SetMonData(&gPlayerParty[slot], MON_DATA_MOVE1 + index, &move);
    SetMonData(&gPlayerParty[slot], MON_DATA_PP1 + index, &pp);
    return GetMonData(&gPlayerParty[slot], MON_DATA_MOVE1 + index);
}

static u32 PartySize(u32 n)
{
    u8 i;

    if (n == 0 || n > PARTY_SIZE)
        return 0xFFFFFFFF;
    for (i = n; i < PARTY_SIZE; i++)
        ZeroMonData(&gPlayerParty[i]);
    gPlayerPartyCount = CalculatePlayerPartyCount();
    return gPlayerPartyCount;
}

static u32 ConqCaptura(u16 species, u16 ball)
{
    if (!IsValidTestMon(species, 30))
        return 0xFFFFFFFF;
    CreateTestMon(&gEnemyParty[0], species, 30, ITEM_NONE);
    Conquistas_OnCaptura(&gEnemyParty[0], ball);
    return 1;
}

// The raw journal slot of an event (also an empty one) into gTestText.
static u32 DiarioEntrada(u32 evt)
{
    const struct DiarioEntrada *e;

    if (evt >= DIARIO_EVT_COUNT)
        return 0xFFFFFFFF;
    e = &gSaveBlock2Ptr->diario.entradas[evt];
    memcpy(gTestText, e, sizeof(*e));
    return e->ordem;
}

// Task 6: a full bag pocket (and PC) for the prize that does not fit. The item itself first, at 999 (FRLG keeps one
// stack per item, so that alone already refuses it), then distinct items of the same pocket, 999 each.
static u32 EncherBolso(u16 item, bool8 pc)
{
    u8 pocket, i, ocupados = 0;
    u16 id, q, n;

    pocket = ItemId_GetPocket(item);
    if (item == ITEM_NONE || item >= ITEMS_COUNT || pocket == 0)
        return 0xFFFFFFFF;
    for (n = 0, id = item; n < ITEMS_COUNT; n++, id = id + 1 < ITEMS_COUNT ? id + 1 : 1)
    {
        if (ItemId_GetPocket(id) != pocket)
            continue;
        q = BagGetQuantityByItemId(id);
        if (q < 999 && !AddBagItem(id, 999 - q))
            break;
    }
    for (i = 0; i < gBagPockets[pocket - 1].capacity; i++)
    {
        if (gBagPockets[pocket - 1].itemSlots[i].itemId != ITEM_NONE)
            ocupados++;
    }
    if (!pc)
        return ocupados;
    for (n = 0, id = item; n < ITEMS_COUNT && CountItemsInPC() < PC_ITEMS_COUNT; n++, id = id + 1 < ITEMS_COUNT ? id + 1 : 1)
    {
        if (ItemId_GetPocket(id) == 0)
            continue;
        for (i = 0; i < PC_ITEMS_COUNT && gSaveBlock1Ptr->pcItems[i].itemId != id; i++)
            ;
        for (q = 0; i == PC_ITEMS_COUNT && q < PC_ITEMS_COUNT; q++)
        {
            if (gSaveBlock1Ptr->pcItems[q].itemId == ITEM_NONE)
                i = q;
        }
        gSaveBlock1Ptr->pcItems[i].itemId = id;
        gSaveBlock1Ptr->pcItems[i].quantity = 999;   // the PC quantity has no key (GetPcItemQuantity)
    }
    return ocupados + CountItemsInPC();
}

// An egg of the player (shiny PID and/or 6 IVs 31 as asked) in a party slot, hatched through the real special.
static u32 ConqChocar(u32 arg0, u16 species)
{
    u8 slot = arg0 & 0xFF, opcoes = (arg0 >> 8) & 0xFF;
    u32 otId = GetPlayerTrainerId();
    // shiny value = hi(ot) ^ lo(ot) ^ hi(pid) ^ lo(pid): 0 (shiny) or 0x100 (far from the shiny range)
    u32 personality = (((otId >> 16) ^ (otId & 0xFFFF) ^ ((opcoes & 1) ? 0 : 0x100)) & 0xFFFF) << 16;
    bool8 ovo = TRUE;
    struct Pokemon *mon;

    if (slot >= PARTY_SIZE || slot > CalculatePlayerPartyCount() || !IsValidTestMon(species, EGG_HATCH_LEVEL))
        return 0xFFFFFFFF;
    mon = &gPlayerParty[slot];
    CreateMon(mon, species, EGG_HATCH_LEVEL, (opcoes & 2) ? MAX_PER_STAT_IVS : TEST_MON_FIXED_IV, TRUE, personality,
              OT_ID_PLAYER_ID, 0);
    SetMonData(mon, MON_DATA_IS_EGG, &ovo);
    gPlayerPartyCount = CalculatePlayerPartyCount();
    gSpecialVar_0x8004 = slot;
    ScriptHatchMon();
    return GetMonData(mon, MON_DATA_SPECIES) | GetMonData(mon, MON_DATA_IS_EGG) << 16;
}

// Task 7: the achievements screen through the real special, from a field script built in gTestText
static u32 OpenConquistas(u8 modo)
{
    u32 special;

    for (special = 0; &gSpecials[special] < gSpecialsEnd; special++)
    {
        if ((void *)gSpecials[special] == (void *)Conquistas_AbrirTelaDoScript)
            break;
    }
    if (&gSpecials[special] >= gSpecialsEnd)
        return 0xFFFFFFFF;
    gTestText[0] = 0x69;            // lockall
    gTestText[1] = 0x16;            // setvar VAR_0x8004, modo
    gTestText[2] = 0x04;
    gTestText[3] = 0x80;
    gTestText[4] = modo;
    gTestText[5] = 0;
    gTestText[6] = 0x97;            // fadescreen FADE_TO_BLACK
    gTestText[7] = 1;
    gTestText[8] = 0x25;            // special Conquistas_AbrirTelaDoScript
    gTestText[9] = special & 0xFF;
    gTestText[10] = special >> 8;
    gTestText[11] = 0x27;           // waitstate
    gTestText[12] = 0x6B;           // releaseall
    gTestText[13] = 0x02;           // end
    ScriptContext_SetupScript(gTestText);
    return special;
}
// --- end of POK-44 --------------------------------------------------------------------------

// --- POK-42: rematch tiers ------------------------------------------------------------------
#include "rematch_tier.h"

// The enemy party CreateNPCTrainerParty would build for `trainer` (as a Vs. Seeker rematch or not), in gEnemyParty.
static u32 BuildTrainerParty(u32 trainer, bool8 isRematch)
{
    u32 savedFlags = gBattleTypeFlags;
    u32 result;

    if (trainer == 0 || trainer >= NUM_TRAINERS)
        return 0xFFFFFFFF;
    RematchTier_SetVsSeekerBattle(isRematch);
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    result = CreateNPCTrainerPartyForTest(trainer);
    result |= GetCurrentBattleRematchTier() << 8 | ((gBattleTypeFlags & BATTLE_TYPE_DOUBLE) ? 1 : 0) << 16;
    RematchTier_SetVsSeekerBattle(FALSE);  // não deixa o bit nem o degrau aplicado para a próxima batalha
    gBattleTypeFlags = savedFlags;
    return result;
}
// --- end of POK-42 --------------------------------------------------------------------------

// --- POK-46: smart AI for the bosses ---------------------------------------------------------
#include "battle_anim.h"

// aiSmart | moves revealed by the player mon in the left position << 8; 0xFFFFFFFF outside a battle.
static u32 AiSmartState(void)
{
    u32 count = 0;
    s32 i;
    u8 battler;

    if (!gMain.inBattle || gBattleStruct == NULL)
        return 0xFFFFFFFF;
    battler = GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (gBattleStruct->aiRevealedMoves[gBattlerPartyIndexes[battler] % PARTY_SIZE][i] != MOVE_NONE)
            count++;
    }
    return gBattleStruct->aiSmart | count << 8;
}

#include "battle_ai_smart.h"

// The boss decision for the opponent on the left (predictive switch -> item -> attack), with nothing emitted and no
// battle state changed: action | partySlot << 8 | item << 16. Only the new boss decision: the original reactive
// switches of ShouldSwitch (before it) and its original tail (after it) are not reported. 0xFFFFFFFF outside a battle, 0xFFFFFFFE when the
// opponent is not a boss (its decision is the original one, not this). forceNoStay = 1 skips the "1 in 5 stays" roll.
static u32 AiSmartDecide(u32 forceNoStay)
{
    struct SmartAiDecision decision;

    if (!gMain.inBattle || gBattleStruct == NULL)
        return 0xFFFFFFFF;
    if (!AI_IsSmartTrainer())
        return 0xFFFFFFFE;
    SmartAI_Decide(GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT), forceNoStay != 0, &decision);
    return decision.action | decision.partySlot << 8 | (u32)decision.item << 16;
}

// Rebuilds gEnemyParty[slot] (default moves for the level, IVs 0, no held item) with hp% and status1; when that slot is
// on the field, its gBattleMons entry is refreshed too (stats, types, ability, moves, hp, status1; stat stages back to
// neutral; status2 kept). arg0 = slot | species << 8, arg1 = level | hpPercent << 8 | status1 << 16.
static u32 SetEnemyMon(u32 arg0, u32 arg1)
{
    u8 slot = arg0 & 0xFF, level = arg1 & 0xFF, hpPercent = (arg1 >> 8) & 0xFF;
    u16 species = (arg0 >> 8) & 0xFFFF;
    u32 status = (arg1 >> 16) & 0xFF;
    u16 hp;
    s32 i, b;
    struct Pokemon *mon;
    struct BattlePokemon *bm;

    if (slot >= PARTY_SIZE || species == SPECIES_NONE || species >= NUM_SPECIES || level == 0 || level > MAX_LEVEL
     || hpPercent > 100)
        return 0xFFFFFFFF;
    mon = &gEnemyParty[slot];
    CreateMon(mon, species, level, 0, FALSE, 0, OT_ID_RANDOM_NO_SHINY, 0);
    hp = GetMonData(mon, MON_DATA_MAX_HP) * hpPercent / 100;
    if (hp == 0 && hpPercent != 0)
        hp = 1;
    SetMonData(mon, MON_DATA_HP, &hp);
    SetMonData(mon, MON_DATA_STATUS, &status);
    if (!gMain.inBattle || gBattleStruct == NULL)
        return species | slot << 16;
    for (b = 0; b < gBattlersCount; b++)
    {
        if (GetBattlerSide(b) != B_SIDE_OPPONENT || gBattlerPartyIndexes[b] != slot)
            continue;
        bm = &gBattleMons[b];
        bm->species = species;
        bm->item = ITEM_NONE;
        for (i = 0; i < MAX_MON_MOVES; i++)
        {
            bm->moves[i] = GetMonData(mon, MON_DATA_MOVE1 + i);
            bm->pp[i] = GetMonData(mon, MON_DATA_PP1 + i);
        }
        bm->ppBonuses = 0;
        bm->level = level;
        bm->hp = hp;
        bm->maxHP = GetMonData(mon, MON_DATA_MAX_HP);
        bm->attack = GetMonData(mon, MON_DATA_ATK);
        bm->defense = GetMonData(mon, MON_DATA_DEF);
        bm->speed = GetMonData(mon, MON_DATA_SPEED);
        bm->spAttack = GetMonData(mon, MON_DATA_SPATK);
        bm->spDefense = GetMonData(mon, MON_DATA_SPDEF);
        bm->status1 = status;
        bm->personality = GetMonData(mon, MON_DATA_PERSONALITY);
        bm->abilityNum = GetMonData(mon, MON_DATA_ABILITY_NUM);
        bm->type1 = gSpeciesInfo[species].types[0];
        bm->type2 = gSpeciesInfo[species].types[1];
        bm->ability = bm->abilityNum && gSpeciesInfo[species].abilities[1] != ABILITY_NONE
                    ? gSpeciesInfo[species].abilities[1] : gSpeciesInfo[species].abilities[0];
        for (i = 0; i < NUM_BATTLE_STATS; i++)
            bm->statStages[i] = DEFAULT_STAT_STAGE;
    }
    return species | slot << 16;
}
// --- end of POK-46 --------------------------------------------------------------------------

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
    case TEST_CMD_TINT_AT:
    {
        struct DayNightTint tint;

        DayNight_GetTintAt(gTestMailbox.arg0, &tint);
        result = tint.r | tint.g << 10 | tint.b << 20;
        break;
    }
    case TEST_CMD_ROLL_WEATHER:
        result = DayNight_RollWeather(gTestMailbox.arg0, gTestMailbox.arg1 & 0xFFFFFF, gTestMailbox.arg1 >> 24);
        break;
    case TEST_CMD_START_WILD_BATTLE:
        CreateScriptedWildMon(gTestMailbox.arg0, gTestMailbox.arg1, ITEM_NONE);
        ScriptContext_SetupScript(sWildBattleScript);
        result = 1;
        break;
    // Hack 7 front A: end
    // Hack 7 front B: start
    case TEST_CMD_LAND_SPECIES:
        result = TestLandSpecies(gTestMailbox.arg0 >> 8, gTestMailbox.arg0 & 0xFF, gTestMailbox.arg1 & 0xFF, gTestMailbox.arg1 >> 8);
        break;
    case TEST_CMD_SPECIES_ON_MAP:
        result = TestSpeciesOnMap(gTestMailbox.arg0 >> 8, gTestMailbox.arg0 & 0xFF, gTestMailbox.arg1);
        break;

    // Hack 7 front B: end
    // Hack 8: start
    case TEST_CMD_ROLL_WILD:
        result = TestRollWild(gTestMailbox.arg0 & 0xFF, (gTestMailbox.arg0 >> 8) & 0xFF, gTestMailbox.arg1 == 1);
        break;
    // Hack 8: end
    // Hack 7 front C: start
    case TEST_CMD_RARE_EGG_ROLL:    result = GetRandomRareEggSpecies(); break;
    case TEST_CMD_SET_KANTO_OWNED:  result = SetKantoOwned(gTestMailbox.arg0); break;
    case TEST_CMD_FILL_PC:          result = FillPC(); break;
    case TEST_CMD_SET_FLAG:         result = SetFlagHook(gTestMailbox.arg0, gTestMailbox.arg1); break;
    // Hack 7 front C: end
    // Hack 7 front D: start
    case TEST_CMD_FRIENDSHIP_TEXT:
        result = FriendshipText(gTestMailbox.arg0, gTestMailbox.arg1);
        break;
    // Hack 7 front D: end
    // Hack 7 front E: start

    // Hack 7 front E: end
    // novidades: start
    case TEST_CMD_OPEN_NOVIDADES:   result = OpenNovidades(); break;
    case TEST_CMD_NOVIDADES_STATE:  result = Novidades_TestGetState(); break;
    case TEST_CMD_NOVIDADES_CARD:   result = Novidades_TestGetCard(); break;
    // novidades: end
    // POK-43: start
    case TEST_CMD_CALC_DAMAGE:      result = CalcDamage(gTestMailbox.arg0); break;
    case TEST_CMD_TYPE_EFFECTIVENESS:
        result = TypeEffectiveness(gTestMailbox.arg0, gTestMailbox.arg1 & 0xFF, (gTestMailbox.arg1 >> 8) & 0xFF);
        break;
    // POK-43: end
    // POK-44: start
    case TEST_CMD_CONQ_ESTADO:      result = ConqEstado(gTestMailbox.arg0 < 0x100 ? gTestMailbox.arg0 : 0xFF); break;
    case TEST_CMD_CONQ_CONTADOR:    result = ConqContador(gTestMailbox.arg0); break;
    case TEST_CMD_CONQ_RESET:       result = ConqReset(gTestMailbox.arg0); break;
    case TEST_CMD_CONQ_CHECAR:      Conquistas_ChecarEstado(); result = Conquistas_AvisosPendentes(); break;
    case TEST_CMD_CONQ_APLICAR:     result = ConqAplicar(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_CONQ_PC_MON:      result = ConqPcMon(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_START_TRAINER_BATTLE: result = StartTrainerBattle(gTestMailbox.arg0); break;
    case TEST_CMD_SET_PARTY_MOVE:   result = SetPartyMove(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_PARTY_SIZE:       result = PartySize(gTestMailbox.arg0); break;
    case TEST_CMD_CONQ_CAPTURA:     result = ConqCaptura(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_CONQ_CHOCAR:      result = ConqChocar(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_DIARIO_ENTRADA:   result = DiarioEntrada(gTestMailbox.arg0); break;
    case TEST_CMD_CONQ_SILENCIO:    gConquistasSilencio = gTestMailbox.arg0 != 0; result = gConquistasSilencio; break;
    case TEST_CMD_ENCHER_BOLSO:     result = EncherBolso(gTestMailbox.arg0, gTestMailbox.arg1); break;
    case TEST_CMD_OPEN_CONQUISTAS:  result = OpenConquistas(gTestMailbox.arg0 != 0); break;
    case TEST_CMD_CONQ_TELA:        result = gTestMailbox.arg0 ? Conquistas_TestGetDiario() : Conquistas_TestGetState(); break;
    // POK-44: end
    case TEST_CMD_BUILD_TRAINER_PARTY: result = BuildTrainerParty(gTestMailbox.arg0, gTestMailbox.arg1 != 0); break;
    case TEST_CMD_AI_SMART_STATE:   result = AiSmartState(); break;
    case TEST_CMD_AI_SMART_DECIDE:  result = AiSmartDecide(gTestMailbox.arg0); break;
    case TEST_CMD_SET_ENEMY_MON:    result = SetEnemyMon(gTestMailbox.arg0, gTestMailbox.arg1); break;
    default:
        result = 0xFFFFFFFF;
        break;
    }
    gTestMailbox.result = result;
    gTestMailbox.cmd = TEST_CMD_NONE;
    gTestMailbox.done = TRUE;
}

#endif // TESTBUILD
