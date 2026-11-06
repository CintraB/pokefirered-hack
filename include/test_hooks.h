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
    TEST_CMD_SET_DEX_COMPLETE,  // every mon HasAllMons() needs, plus Mew (Shiny Charm), seen+caught, National Dex on; result = HasAllMons()
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

// --- Hack 7: day/night, weather and time-based encounters (numbers fixed by the plan) ------
// Commands not implemented yet fall to TestHooks_Run's default (result = 0xFFFFFFFF).
enum
{
    TEST_CMD_SET_CLOCK = 0x70,   // arg0 = day, arg1 = minute of day: DayNight_SetClock; result = DayNight_GetMinuteOfDay()
    TEST_CMD_CLOCK_INFO,         // result = minute of day | period << 16
    TEST_CMD_TINT_AT,            // arg0 = minute of day; result = r | g << 10 | b << 20 (DayNight_GetTintAt, 1/256)
    TEST_CMD_ROLL_WEATHER,       // arg0 = region, arg1 = day | period << 24; result = DayNight_RollWeather
    TEST_CMD_LAND_SPECIES,       // arg0 = mapGroup << 8 | mapNum, arg1 = slot | period << 8: species of that land slot (the FRLG one without a time table; 0xFFFFFFFF = no land table)
    TEST_CMD_FRIENDSHIP_TEXT,    // arg1 = 0: GetFriendshipLineText(arg0 = friendship) / 1: the line rebuilt from the friendship of the mon the open summary shows (0xFFFFFFFF on an egg), into gTestText (result = length) / 2: friendship of party slot arg0 set to 0
    TEST_CMD_RARE_EGG_ROLL,
    TEST_CMD_SET_KANTO_OWNED,
    TEST_CMD_START_WILD_BATTLE,  // arg0 = species, arg1 = level: wild battle through a field script (dowildbattle); result = 1
    TEST_CMD_FILL_PC,
    TEST_CMD_SET_FLAG,
    TEST_CMD_SPECIES_ON_MAP,     // arg0 = mapGroup << 8 | mapNum, arg1 = species: IsSpeciesOnMap of that map header (0xFFFFFFFF = no header)
};
// --- end of Hack 7 -------------------------------------------------------------------------

// --- Hack 8: LeafGreen exclusives in the wild ---------------------------------------------
enum
{
    TEST_CMD_ROLL_WILD = 0x80,   // arg0 = area (0 land, 1 water, 2 rock smash, 3 fishing) | rod << 8, arg1 = 1: also StartWildBattle; result = species | level << 16 of the generated mon (0xFFFFFFFF = no such table here)
};
// --- end of Hack 8 -------------------------------------------------------------------------

// --- Tela de novidades do Prof. Carvalho ---------------------------------------------------
enum
{
    TEST_CMD_OPEN_NOVIDADES = 0x90, // field script: lockall, fadescreen, special OpenNovidadesScreen, waitstate, releaseall; result = special number (0xFFFFFFFF = not in gSpecials)
    TEST_CMD_NOVIDADES_STATE,       // result = Novidades_TestGetState(): cursor | input ready << 8 | live icons << 16 | (open card + 1, 0 = grid) << 24 (0xFFFFFFFF = screen closed)
    TEST_CMD_NOVIDADES_CARD,        // result = Novidades_TestGetCard(): topic | card << 8 | image kind << 16 | live image sprites << 24 (0xFFFFFFFF = not on a card)
};
// --- end of novidades ----------------------------------------------------------------------

// --- POK-43: physical/special split per move -----------------------------------------------
enum
{
    TEST_CMD_CALC_DAMAGE = 0xA0, // arg0 = move, arg1 = 0: gPlayerParty[0] hits gPlayerParty[1] as BattlePokemon built on the spot (no crit, weather, screens, badges, Flash Fire or field effects; gBattleMons untouched); result = CalculateBaseDamage
    TEST_CMD_TYPE_EFFECTIVENESS,  // arg0 = move type, arg1 = type1 | type2 << 8 of the defender; result = multiplier x 100 from gTypeEffectiveness, applied like ModulateDmgByType (each matching entry: x mul / 10; type2 only if != type1), without Foresight (the Ghost immunities count)
};
// --- end of POK-43 -------------------------------------------------------------------------

// --- POK-44: achievements and battle journal ------------------------------------------------
enum
{
    TEST_CMD_CONQ_ESTADO = 0xB0, // arg0 = num (CONQ_*); result = state | delivered << 8 | delivered tier << 16 | current tier (Conquistas_DegrauAtual) << 24 (0xFFFFFFFF = invalid num)
    TEST_CMD_CONQ_CONTADOR,      // arg0 = 0 trainer wins, 1 shinies, 2 origem | resumoPendente << 8, 3 magic, 4 + tab: done | valid << 8 of that tab (Conquistas_ContarAba); result = that value (0xFFFFFFFF = invalid arg0)
    TEST_CMD_CONQ_RESET,         // arg0 = 0: zero both save areas (an old save, no marker), 1: Conquistas_IniciarJogoNovo(); result = magic
    TEST_CMD_CONQ_CHECAR,        // Conquistas_ChecarEstado() now (an old save is scanned first); result = Conquistas_AvisosPendentes()
    TEST_CMD_CONQ_APLICAR,       // arg0 = num, arg1 = op | tier << 8: 0 Conquistas_Marcar, 1 Conquistas_Perder, 2 Conquistas_SetEntregue, 3 Conquistas_SetDegrauEntregue(num, tier); result = as TEST_CMD_CONQ_ESTADO afterwards (0xFFFFFFFF = invalid num or op)
    TEST_CMD_CONQ_PC_MON,        // arg0 = box | position << 8 | options << 16 (bit 0 shiny, bit 1 hatched by the player: MET_LEVEL 0 and 6 IVs 31), arg1 = species | level << 16 (species 0 empties the slot); the player is the OT; result = species read back from the box (0xFFFFFFFF = invalid)
    TEST_CMD_START_TRAINER_BATTLE, // arg0 = trainer (TRAINER_*): battle with no intro speech through a field script in RAM (trainerbattle_no_intro, as TEST_CMD_START_WILD_BATTLE); a loss whites out as usual; result = 1 (0xFFFFFFFF = invalid trainer)
    TEST_CMD_SET_PARTY_MOVE,     // arg0 = party slot | move index (0-3) << 8, arg1 = move (PP full, no PP Ups); result = the move read back (0xFFFFFFFF = invalid)
    TEST_CMD_PARTY_SIZE,         // arg0 = n (1-6): keeps only the first n party mons (slots n-5 zeroed); result = gPlayerPartyCount
    TEST_CMD_CONQ_CAPTURA,       // arg0 = species, arg1 = ball (ITEM_*): gEnemyParty[0] built at level 30, then Conquistas_OnCaptura(&gEnemyParty[0], ball); result = 1 (0xFFFFFFFF = invalid species)
    TEST_CMD_CONQ_CHOCAR,        // arg0 = party slot (<= party count) | options << 8 (bit 0 shiny, bit 1 6 IVs 31), arg1 = species: an egg of the player in that slot, hatched by ScriptHatchMon (AddHatchedMonToParty); result = species | isEgg << 16 read back (0xFFFFFFFF = invalid)
    TEST_CMD_DIARIO_ENTRADA,     // arg0 = journal event (DIARIO_EVT_*): its 20-byte struct DiarioEntrada copied into gTestText; result = its ordem (0 = empty slot, 0xFFFFFFFF = invalid event)
    TEST_CMD_CONQ_SILENCIO,      // arg0 = 1 silences the achievement notice (the field does not even check), 0 restores it; result = arg0 (gConquistasSilencio)
    TEST_CMD_ENCHER_BOLSO,       // arg0 = item: fills the free slots of its bag pocket with distinct items of that pocket, 999 each, starting with the item itself; arg1 = 1 also fills the 30 PC item slots the same way (the item first, then distinct items); result = slots taken (pocket + PC) (0xFFFFFFFF = invalid item)
    TEST_CMD_OPEN_CONQUISTAS,    // arg0 = modo (0 conquistas, 1 diário): field script lockall, setvar VAR_0x8004, fadescreen, special Conquistas_AbrirTelaDoScript, waitstate, releaseall; result = special number (0xFFFFFFFF = not in gSpecials)
    TEST_CMD_CONQ_TELA,          // result = Conquistas_TestGetState(): modo | tab << 8 | cursor << 16 | input ready << 24 (cursor = first visible row in the achievements mode, selected row in the journal mode; 0xFFFFFFFF = screen closed); arg0 = 1: Conquistas_TestGetDiario(): entries | selected DIARIO_EVT_* << 8 | first visible row << 16 (0xFFFFFFFF = closed or not the journal)
};
// --- end of POK-44 -------------------------------------------------------------------------

// --- POK-42: rematch tiers ----------------------------------------------------------------
enum
{
    TEST_CMD_BUILD_TRAINER_PARTY = 0xC0, // arg0 = trainer (TRAINER_*), arg1 = 1 built as a Vs. Seeker rematch, 0 as a normal battle: gBattleTypeFlags = BATTLE_TYPE_TRAINER, CreateNPCTrainerPartyForTest into gEnemyParty, flags restored; result = party size | GetCurrentBattleRematchTier() << 8 | double << 16 (read before the restore; 0xFFFFFFFF = invalid trainer)
};
// --- end of POK-42 -------------------------------------------------------------------------

// --- POK-46: smart AI for the bosses (switching and items) ---------------------------------
enum
{
    TEST_CMD_AI_SMART_STATE = 0xD0, // result = gBattleStruct->aiSmart | moves revealed so far by the player mon at B_POSITION_PLAYER_LEFT (aiRevealedMoves of its party slot) << 8 (0xFFFFFFFF = not in battle)
    TEST_CMD_AI_SMART_DECIDE = 0xD1, // arg0 = 1 skips the "1 in 5 stays and follows the original rule" roll (0 = normal roll): the boss decision (predictive switch -> item -> attack) for B_POSITION_OPPONENT_LEFT, nothing emitted; only the new boss decision is reported (not the original reactive switches of ShouldSwitch nor its original tail, which run before/after it in the game); result = action (SMART_AI_*) | partySlot << 8 | item << 16 (0xFFFFFFFF = not in battle, 0xFFFFFFFE = not a boss)
    TEST_CMD_SET_ENEMY_MON = 0xD2,  // arg0 = slot | species << 8, arg1 = level | hpPercent << 8 | status1 byte << 16: rebuilds gEnemyParty[slot] (default moves for the level) and, if on the field, its gBattleMons; result = species | slot << 16 (0xFFFFFFFF = bad args)
    TEST_CMD_SET_TRAINER_ITEMS = 0xD3, // arg0 = item1 | item2 << 16, arg1 = item3 | item4 << 16 (0 = none): zeroes and rewrites the trainer's item list of this battle (battleHistory trainerItems, packed, and itemsNo); result = itemsNo (0xFFFFFFFF = not in battle or an item outside ITEM_POTION..LAST_BERRY_INDEX)
};
// --- end of POK-46 -------------------------------------------------------------------------

// --- POK-47: DexNav -----------------------------------------------------------------------
enum
{
    TEST_CMD_DEXNAV_ENTRY = 0xE0, // arg0 = map index (gDexNavMaps), arg1 = entry index: DexNav_GetMapEntries; result = species | method << 16 | periods << 24 (0xFFFFFFFF = past the last entry or bad map)
    TEST_CMD_DEXNAV_RATE = 0xE1,  // arg0 = map index, arg1 = entry index | period << 8 (0 morning, 1 afternoon, 2 night: rateX10[period]; 3 evening: DexNav_RateForPeriods(DAY | NIGHT)); result = rate x 10 | minLevel << 16 | maxLevel << 24 (0xFFFFFFFF = bad args)
    TEST_CMD_DEXNAV_ROLL = 0xE2,  // arg0 = method (DEXNAV_METHOD_*), arg1 = N (<= 0xFFFF): the real generator of the current map (TestRollWild, no battle) N times; gTestText = struct TestDexNavTally[TEST_DEXNAV_TALLY_MAX] (species 0 = end); result = distinct species (0xFFFFFFFF = no such table here or bad method)
    TEST_CMD_DEXNAV_STATE = 0xE3, // arg0 = what: DexNav_TestGetState (include/dexnav.h); 0: mode | tab (DEXNAV_TAB_*) << 8 | cursor (selected mon, in the tab order) << 16 | map index << 24; 1: input ready | tabs of the map (bit per tab) << 8 | mons in the tab << 16 | first visible row << 24; 2: caught | total of the map << 8 | caught of the tab << 16 | total of the tab << 24; 3: species of the "+N" row | their periods << 8 | current period bits << 16; 4-7 (cursor, stack, search, selected row): see include/dexnav.h (0xFFFFFFFF = screen closed)
    TEST_CMD_OPEN_DEXNAV = 0xE4,  // field script lockall, fadescreen, callnative DexNav_OpenFromScript, waitstate, releaseall: opens the DexNav on the current map; result = its map index (0xFFFFFFFF = no encounters here: the screen opens on the map list, at the last visited map with encounters)
};

// The tally of TEST_CMD_DEXNAV_ROLL in gTestText (test/esteira/dexnav.py reads this layout)
struct TestDexNavTally
{
    u16 species;
    u16 count;
};

#define TEST_DEXNAV_TALLY_MAX (TEST_TEXT_SIZE / sizeof(struct TestDexNavTally))
// --- end of POK-47 -------------------------------------------------------------------------

// --- POK-48: Pokémon seguidor ---------------------------------------------------------------
enum
{
    TEST_CMD_FOLLOWER_STATE = 0xF0, // arg0 = what: Follower_TestGetState (include/follower.h); 0: exists | species << 8 | shiny << 24 | hidden << 25 | variant << 26 (5 bits, FOLLOWER_VARIANT_*: 0 default, 1 female, 2 + Unown letter) | large << 31 (the 64x64 graphicsId); 1: x | y << 16 of the follower (s16 each, without MAP_OFFSET; 0xFFFFFFFE = no follower); 2: facingDirection | idle anim frame << 8 | objects with the follower localId << 16 (0xFFFFFFFF = not in the field)
    TEST_CMD_SET_FOLLOWER_OPTION,   // arg0 = 0 Yes / 1 No: gSaveBlock2Ptr->optionsFollowerOff, then Follower_Refresh if the overworld is running (Overworld_IsRunning); result = the old value
    TEST_CMD_SET_LEAD_SHINY,        // arg0 = 1 shiny / 0 never shiny: rebuilds gPlayerParty[0] (same species and level, player as OT) with that personality; the follower changes on the next spawn/refresh; result = species | IsMonShiny << 16 (0xFFFFFFFF = no valid lead)
    TEST_CMD_FILL_OBJECT_EVENTS,    // arg0 = 1: invisible filler objects (the player's graphics, localId TEST_FILLER_LOCALID + i, on the player's tile) in every free gObjectEvents slot; 0: removes them; result = active objects afterwards
    TEST_CMD_START_FLY,             // arg0 = heal location (HEAL_LOCATION_*), arg1 = party slot shown: what the fly map does on A (SetWarpDestinationToHealLocation + ReturnToFieldFromFlyMapSelect), so the real fly-out/fly-in effects run; result = 1 (0xFFFFFFFF = not in the field or bad args)
    TEST_CMD_SET_LEAD_LOOK,         // arg0 = species | level << 16, arg1 = shiny (bit 0) | female (bit 1) | Unown letter << 8 (0..27, only checked for SPECIES_UNOWN): rebuilds gPlayerParty[0] (player as OT) with the first personality found that gives all three; the follower changes on the next spawn/refresh; result = species | variant (Follower_GetMonVariant) << 16 | shiny << 24 (0xFFFFFFFF = impossible: bad species/level, letter > 27, female for a species that is never female, or no personality found)
};
#define TEST_FILLER_LOCALID 0xE0
// --- end of POK-48 -------------------------------------------------------------------------

// --- POK-50: Pokérus ------------------------------------------------------------------------
enum
{
    TEST_CMD_POKERUS_SET = 0x100, // arg0 = party slot, arg1 = MON_DATA_POKERUS byte (strain << 4 | days): written as is; result = the old byte (0xFFFFFFFF = bad slot or empty)
    TEST_CMD_POKERUS_STATE,       // gTestText[0..5] = MON_DATA_POKERUS of gPlayerParty[0..5]; result = CheckPartyPokerus(party, 0x3F) | CheckPartyHasHadPokerus(party, 0x3F) << 8
    TEST_CMD_POKERUS_RUN,         // arg0 = what, arg1 = n: 0 GivePartyPokerusNow; 1 PartySpreadPokerus n times; 2 UpdatePartyPokerusTime(n); 3 n x RandomlyGivePartyPokerus, result = how many rolls were won (gTestPokerusRollHits; party bytes restored at the end); then (0-2) result = as POKERUS_STATE (gTestText filled too); 4: EVs of gPlayerParty[0] zeroed, MonGainEVs(gPlayerParty[0], species n), result = its EV total (0xFFFFFFFF = bad args)
};
extern u32 gTestPokerusRollHits; // src/pokemon.c
// --- end of POK-50 -------------------------------------------------------------------------

extern struct TestMailbox gTestMailbox;
extern u8 gTestText[TEST_TEXT_SIZE];

void TestHooks_Run(void);

#endif // TESTBUILD

#endif // GUARD_TEST_HOOKS_H
