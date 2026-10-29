#include "global.h"
#include "event_data.h"
#include "field_move_rules.h"
#include "item.h"
#include "party_menu.h"
#include "pokemon.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/moves.h"

// POK-38: HMs sem ensinar. Um golpe de HM vale no campo se algum Pokémon da equipe sabe o golpe
// (como no jogo original) ou, sem ninguém que saiba, com a insígnia, a HM na bolsa e um Pokémon
// da equipe que possa aprender o golpe. A ordem das insígnias segue FLAG_BADGE01_GET + FIELD_MOVE_*.
struct FieldMoveRule
{
    u16 move;
    u16 hm;
    u16 badgeFlag;
};

static const struct FieldMoveRule sFieldMoveRules[] =
{
    { MOVE_FLASH,      ITEM_HM05_FLASH,      FLAG_BADGE01_GET },
    { MOVE_CUT,        ITEM_HM01_CUT,        FLAG_BADGE02_GET },
    { MOVE_FLY,        ITEM_HM02_FLY,        FLAG_BADGE03_GET },
    { MOVE_STRENGTH,   ITEM_HM04_STRENGTH,   FLAG_BADGE04_GET },
    { MOVE_SURF,       ITEM_HM03_SURF,       FLAG_BADGE05_GET },
    { MOVE_ROCK_SMASH, ITEM_HM06_ROCK_SMASH, FLAG_BADGE06_GET },
    { MOVE_WATERFALL,  ITEM_HM07_WATERFALL,  FLAG_BADGE07_GET },
};

static const struct FieldMoveRule *GetFieldMoveRule(u16 move)
{
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sFieldMoveRules); i++)
    {
        if (sFieldMoveRules[i].move == move)
            return &sFieldMoveRules[i];
    }
    return NULL;
}

static bool8 IsUsablePartyMon(u8 slot)
{
    return GetMonData(&gPlayerParty[slot], MON_DATA_SPECIES) != SPECIES_NONE
        && !GetMonData(&gPlayerParty[slot], MON_DATA_IS_EGG);
}

u8 FindPartyMonForFieldMove(u16 move)
{
    const struct FieldMoveRule *rule = GetFieldMoveRule(move);
    u8 i;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) == SPECIES_NONE)
            break;
        if (IsUsablePartyMon(i) && MonKnowsMove(&gPlayerParty[i], move))
            return i;
    }

    if (rule == NULL || !FlagGet(rule->badgeFlag) || !CheckBagHasItem(rule->hm, 1))
        return PARTY_SIZE;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) == SPECIES_NONE)
            break;
        if (IsUsablePartyMon(i) && CanMonLearnTMHM(&gPlayerParty[i], rule->hm - ITEM_TM01))
            return i;
    }
    return PARTY_SIZE;
}

bool8 CanUseFieldMove(u16 move)
{
    const struct FieldMoveRule *rule = GetFieldMoveRule(move);

    if (rule != NULL && !FlagGet(rule->badgeFlag))
        return FALSE;
    return FindPartyMonForFieldMove(move) != PARTY_SIZE;
}
