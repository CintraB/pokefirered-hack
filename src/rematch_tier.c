#include "global.h"
#include "rematch_tier.h"
#include "battle.h"
#include "characters.h"
#include "conquistas.h"
#include "data.h"
#include "event_data.h"
#include "pokemon.h"
#include "script_menu.h"
#include "string_util.h"
#include "strings.h"
#include "vs_seeker.h"
#include "constants/battle.h"
#include "constants/battle_ai.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/menu.h"
#include "constants/moves.h"
#include "constants/opponents.h"
#include "constants/pokemon.h"
#include "constants/species.h"
#include "constants/trainers.h"
#include "constants/vars.h"

// Revanches por degrau de dificuldade (POK-42): o degrau nas revanches do Vs. Seeker.

#include "data/rematch_tiers.h"

STATIC_ASSERT(REMATCH_TIER_ROWS == VS_SEEKER_REMATCH_ROWS, RematchTierRowsIgualASRematches);
STATIC_ASSERT(NELEMS(sLeagueTierParties) == TRAINER_CHAMPION_REMATCH_CHARMANDER - TRAINER_ELITE_FOUR_LORELEI_2 + 1,
              LeagueTierPartiesCobreOsIdsDaLiga);

// Um byte só (a EWRAM está quase cheia): bit 7 = a batalha de treinador atual é revanche do Vs. Seeker
// (BattleSetup_ConfigureTrainerBattle); bits 0-2 = o degrau aplicado no time (0 = nenhum).
#define STATE_VS_SEEKER 0x80
#define STATE_TIER_MASK 0x07

static EWRAM_DATA u8 sRematchTierState = 0;

u8 GetRematchTier(void)
{
    u16 tier = VarGet(VAR_REMATCH_TIER);

    // Save antigo, var com lixo ou degrau sem o Hall da Fama: o jogo de hoje.
    if (!FlagGet(FLAG_SYS_GAME_CLEAR) || tier > REMATCH_TIER_MAX)
        return 0;
    return tier;
}

void RematchTier_SetVsSeekerBattle(bool8 isRematch)
{
    // Batalha nova: também zera o degrau aplicado na anterior.
    sRematchTierState = isRematch ? STATE_VS_SEEKER : 0;
}

// A mesma personalidade do laço original de CreateNPCTrainerParty (o hash acumula de um Pokémon para o outro,
// como lá).
static u32 TrainerMonPersonality(u16 trainerNum, u16 species, u32 *nameHash)
{
    u32 personalityValue;
    s32 j;

    if (gTrainers[trainerNum].doubleBattle == TRUE)
        personalityValue = 0x80;
    else if (gTrainers[trainerNum].encounterMusic_gender & F_TRAINER_FEMALE)
        personalityValue = 0x78;
    else
        personalityValue = 0x88;

    for (j = 0; gTrainers[trainerNum].trainerName[j] != EOS; j++)
        *nameHash += gTrainers[trainerNum].trainerName[j];
    for (j = 0; gSpeciesNames[species][j] != EOS; j++)
        *nameHash += gSpeciesNames[species][j];

    return personalityValue + (*nameHash << 8);
}

u8 RematchTier_CreateParty(struct Pokemon *party, u16 trainerNum)
{
    const struct RematchTierMon *mons;
    const struct TrainerMonItemCustomMoves *league;
    u32 nameHash = 0;
    s32 row;
    u8 tier;
    s32 i, j;

    sRematchTierState &= ~STATE_TIER_MASK;
    tier = GetRematchTier();
    if (tier == 0)
        return 0;

    // Elite 4 e Campeão (_2 e REMATCH): os times à mão do degrau, sem o Vs. Seeker. A sala só chama esses ids
    // com ShouldUseLeagueRematchTeams; com degrau 0, seguem os times _2 de hoje.
    if (trainerNum >= TRAINER_ELITE_FOUR_LORELEI_2 && trainerNum <= TRAINER_CHAMPION_REMATCH_CHARMANDER)
    {
        league = sLeagueTierParties[trainerNum - TRAINER_ELITE_FOUR_LORELEI_2][tier - 1];
        ZeroEnemyPartyMons();
        for (i = 0; i < PARTY_SIZE; i++)
        {
            // Como F_TRAINER_PARTY_CUSTOM_MOVESET | F_TRAINER_PARTY_HELD_ITEM: IV na escala 0-255, golpes com PP.
            CreateMon(&party[i], league[i].species, league[i].lvl, league[i].iv * MAX_PER_STAT_IVS / 255, TRUE,
                      TrainerMonPersonality(trainerNum, league[i].species, &nameHash), OT_ID_RANDOM_NO_SHINY, 0);
            SetMonData(&party[i], MON_DATA_HELD_ITEM, &league[i].heldItem);
            for (j = 0; j < MAX_MON_MOVES; j++)
            {
                SetMonData(&party[i], MON_DATA_MOVE1 + j, &league[i].moves[j]);
                SetMonData(&party[i], MON_DATA_PP1 + j, &gBattleMoves[league[i].moves[j]].pp);
            }
        }
        sRematchTierState |= tier;
        return PARTY_SIZE;
    }

    if (!(sRematchTierState & STATE_VS_SEEKER))
        return 0;
    row = GetVsSeekerRematchRow(trainerNum);
    if (row < 0 || row >= REMATCH_TIER_ROWS)
        return 0;

    mons = sRematchTierParties[row][tier - 1];
    ZeroEnemyPartyMons();
    for (i = 0; i < PARTY_SIZE; i++)
    {
        CreateMon(&party[i], mons[i].species, mons[i].lvl, mons[i].iv, TRUE,
                  TrainerMonPersonality(trainerNum, mons[i].species, &nameHash), OT_ID_RANDOM_NO_SHINY, 0);
        SetMonData(&party[i], MON_DATA_HELD_ITEM, &mons[i].heldItem);
    }
    sRematchTierState |= tier;
    return PARTY_SIZE;
}

bool8 ShouldUseLeagueRematchTeams(void)
{
    // As salas da Liga usam os ids _2/REMATCH depois das Ilhas Sevii (como hoje) ou, com degrau >= 1, logo
    // depois do Hall da Fama.
    return FlagGet(FLAG_SYS_CAN_LINK_WITH_RS) || GetRematchTier() >= 1;
}

u8 GetCurrentBattleRematchTier(void)
{
    // Só numa batalha de treinador que passa por CreateNPCTrainerParty: numa selvagem, de link ou da Torre de
    // Treinadores depois de uma revanche, o degrau da anterior não vale.
    if ((gBattleTypeFlags & (BATTLE_TYPE_TRAINER | BATTLE_TYPE_LINK | BATTLE_TYPE_BATTLE_TOWER
                           | BATTLE_TYPE_EREADER_TRAINER | BATTLE_TYPE_TRAINER_TOWER)) != BATTLE_TYPE_TRAINER)
        return 0;
    return sRematchTierState & STATE_TIER_MASK;
}

u32 RematchTier_GetAiFlags(void)
{
    // Revanche do Vs. Seeker no degrau 80 ou mais: a IA dos chefes do POK-32 (líderes, Elite 4, Campeão). A Elite 4
    // e o Campeão já têm esse conjunto em trainers.h.
    if ((sRematchTierState & STATE_VS_SEEKER) && GetCurrentBattleRematchTier() >= 3)
        return AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_TRY_TO_FAINT | AI_SCRIPT_CHECK_VIABILITY | AI_SCRIPT_SETUP_FIRST_TURN | AI_SCRIPT_HP_AWARE;
    return 0;
}

// Ganchos das conquistas do POK-44 (a regra de marcar fica em src/conquistas.c).
void RematchTier_OnRematchWon(u8 tier)
{
    if (tier == REMATCH_TIER_MAX)
        Conquistas_Evento(CONQ_EVT_REVANCHE_MAX);
}

void RematchTier_OnLeagueCleared(u8 tier)
{
    if (tier == REMATCH_TIER_MAX)
        Conquistas_Evento(CONQ_EVT_E4_DEGRAU100);
}

// Os mesmos rótulos da lista da guarda da Liga (sMultichoiceList_RematchTier, src/script_menu.c), por degrau.
static const u8 *const sRematchTierNames[] = {
    gText_RematchTier_Normal,
    gText_RematchTier_60,
    gText_RematchTier_70,
    gText_RematchTier_80,
    gText_RematchTier_90,
    gText_RematchTier_100,
};

STATIC_ASSERT(NELEMS(sRematchTierNames) == REMATCH_TIER_MAX + 1, RematchTierNamesCobreOsDegraus);

void BufferRematchTierName(void)
{
    StringCopy(gStringVar1, sRematchTierNames[GetRematchTier()]);
}

// Special da guarda da Liga: a lista dos degraus com o cursor no degrau atual, para quem aperta A sem mexer manter
// o degrau. O script espera com waitstate; a escolha volta em VAR_RESULT (SCR_MENU_CANCEL no B).
void ShowRematchTierMenu(void)
{
    ScriptMenu_MultichoiceWithDefault(20, 0, MULTICHOICE_REMATCH_TIER, FALSE, GetRematchTier());
}
