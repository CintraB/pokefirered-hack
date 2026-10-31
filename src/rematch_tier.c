#include "global.h"
#include "rematch_tier.h"
#include "battle.h"
#include "characters.h"
#include "data.h"
#include "event_data.h"
#include "pokemon.h"
#include "vs_seeker.h"
#include "constants/battle.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/pokemon.h"
#include "constants/species.h"
#include "constants/trainers.h"
#include "constants/vars.h"

// Revanches por degrau de dificuldade (POK-42): o degrau nas revanches do Vs. Seeker.

#include "data/rematch_tiers.h"

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

u8 RematchTier_CreateParty(struct Pokemon *party, u16 trainerNum)
{
    const struct RematchTierMon *mons;
    u32 nameHash = 0;
    u32 personalityValue;
    s32 row;
    u8 tier;
    s32 i, j;

    sRematchTierState &= ~STATE_TIER_MASK;
    tier = GetRematchTier();
    if (tier == 0 || !(sRematchTierState & STATE_VS_SEEKER))
        return 0;
    row = GetVsSeekerRematchRow(trainerNum);
    if (row < 0 || row >= REMATCH_TIER_ROWS)
        return 0;

    mons = sRematchTierParties[row][tier - 1];
    ZeroEnemyPartyMons();
    for (i = 0; i < PARTY_SIZE; i++)
    {
        // A mesma personalidade do laço original de CreateNPCTrainerParty (o hash acumula de um Pokémon
        // para o outro, como lá).
        if (gTrainers[trainerNum].doubleBattle == TRUE)
            personalityValue = 0x80;
        else if (gTrainers[trainerNum].encounterMusic_gender & F_TRAINER_FEMALE)
            personalityValue = 0x78;
        else
            personalityValue = 0x88;

        for (j = 0; gTrainers[trainerNum].trainerName[j] != EOS; j++)
            nameHash += gTrainers[trainerNum].trainerName[j];
        for (j = 0; gSpeciesNames[mons[i].species][j] != EOS; j++)
            nameHash += gSpeciesNames[mons[i].species][j];

        personalityValue += nameHash << 8;
        CreateMon(&party[i], mons[i].species, mons[i].lvl, mons[i].iv, TRUE, personalityValue, OT_ID_RANDOM_NO_SHINY, 0);
        SetMonData(&party[i], MON_DATA_HELD_ITEM, &mons[i].heldItem);
    }
    sRematchTierState |= tier;
    return PARTY_SIZE;
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
