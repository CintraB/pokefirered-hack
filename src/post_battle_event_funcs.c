#include "global.h"
#include "script_pokemon_util.h"
#include "event_data.h"
#include "credits.h"
#include "overworld.h"
#include "hall_of_fame.h"
#include "load_save.h"
#include "item.h"
#include "pokedex.h"
#include "pokemon.h"
#include "rematch_tier.h"
#include "constants/heal_locations.h"
#include "constants/items.h"

bool8 EnterHallOfFame(void)
{
    bool8 ribbonState;
    bool8 *r7;
    int i;
    bool8 gaveAtLeastOneRibbon;
    HealPlayerParty();
    // FLAG_FOUGHT_MEWTWO now means "caught". Saves from before the Mewtwo started returning
    // may have it set after a mere defeat: unset it so he comes back after this Hall of Fame.
    if (FlagGet(FLAG_FOUGHT_MEWTWO) && !GetSetPokedexFlag(SpeciesToNationalPokedexNum(SPECIES_MEWTWO), FLAG_GET_CAUGHT))
        FlagClear(FLAG_FOUGHT_MEWTWO);
    if (FlagGet(FLAG_SYS_GAME_CLEAR) == TRUE)
    {
        gHasHallOfFameRecords = TRUE;
    }
    else
    {
        gHasHallOfFameRecords = FALSE;
        FlagSet(FLAG_SYS_GAME_CLEAR);
    }
    if (GetGameStat(GAME_STAT_FIRST_HOF_PLAY_TIME) == 0)
    {
        SetGameStat(GAME_STAT_FIRST_HOF_PLAY_TIME, (gSaveBlock2Ptr->playTimeHours << 16) | (gSaveBlock2Ptr->playTimeMinutes << 8) | gSaveBlock2Ptr->playTimeSeconds);
    }
    SetContinueGameWarpStatus();
    SetContinueGameWarpToHealLocation(HEAL_LOCATION_PALLET_TOWN);
    gaveAtLeastOneRibbon = FALSE;
    for (i = 0, r7 = &ribbonState; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_SANITY_HAS_SPECIES) && !GetMonData(&gPlayerParty[i], MON_DATA_SANITY_IS_EGG))
        {
            if (!GetMonData(&gPlayerParty[i], MON_DATA_CHAMPION_RIBBON))
            {
                *r7 = TRUE;
                SetMonData(&gPlayerParty[i], MON_DATA_CHAMPION_RIBBON, &ribbonState);
                gaveAtLeastOneRibbon = TRUE;
            }
        }
    }
    if (gaveAtLeastOneRibbon == TRUE)
    {
        IncrementGameStat(GAME_STAT_RECEIVED_RIBBONS);
        FlagSet(FLAG_SYS_RIBBON_GET);
#if REVISION >= 0xA
        // The player has entered the Hall of Fame for the first time.
        // (At least, this is probably what was intended, except giving at least one Champion Ribbon does not imply first Hall of Fame entry)
        // Give the event tickets, and the flags for obtaining them, if required.
        if (!CheckBagHasItem(ITEM_AURORA_TICKET, 1))
        {
             AddBagItem(ITEM_AURORA_TICKET, 1);
             FlagSet(FLAG_ENABLE_SHIP_BIRTH_ISLAND);
             FlagSet(FLAG_RECEIVED_AURORA_TICKET);
             AddBagItem(ITEM_MYSTIC_TICKET, 1);
             FlagSet(FLAG_ENABLE_SHIP_NAVEL_ROCK);
             FlagSet(FLAG_RECEIVED_MYSTIC_TICKET);
        }
#endif
    }
    // POK-42: o degrau ainda é o da batalha do Campeão. Do fim dela até aqui (falas, warp para o Hall, este special)
    // não há outra batalha nem CreateNPCTrainerParty, então gBattleTypeFlags (só BATTLE_TYPE_TRAINER) e o estado do
    // degrau continuam os dela. Antes da tela do Hall, que grava o save: a conquista feita sobrevive aos créditos e
    // ao reset, e o aviso sai no próximo momento livre no campo.
    RematchTier_OnLeagueCleared(GetCurrentBattleRematchTier());
    SetMainCallback2(CB2_DoHallOfFameScreen);
    return FALSE;
}

bool8 SetCB2WhiteOut(void)
{
    SetMainCallback2(CB2_WhiteOut);
    return FALSE;
}
