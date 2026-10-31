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
};
// --- end of POK-44 -------------------------------------------------------------------------

extern struct TestMailbox gTestMailbox;
extern u8 gTestText[TEST_TEXT_SIZE];

void TestHooks_Run(void);

#endif // TESTBUILD

#endif // GUARD_TEST_HOOKS_H
