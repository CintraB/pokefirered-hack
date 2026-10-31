#include "global.h"
#include "battle.h"
#include "battle_ai_smart.h"
#include "battle_anim.h"
#include "rematch_tier.h"
#include "constants/battle_ai.h"
#include "constants/moves.h"
#include "constants/opponents.h"
#include "constants/trainers.h"

// IA dos chefes (POK-46): estado por batalha. Ver include/battle_ai_smart.h.

void SmartAI_InitBattle(void)
{
    u32 flags;
    s32 i, j;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        for (j = 0; j < MAX_MON_MOVES; j++)
            gBattleStruct->aiRevealedMoves[i][j] = MOVE_NONE;
    }
    for (i = 0; i < 2; i++)
    {
        gBattleStruct->aiVoluntarySwitchTurn[i] = SMART_AI_NEVER;
        gBattleStruct->aiHealTurn[i] = SMART_AI_NEVER;
        gBattleStruct->aiHealHp[i] = 0;
    }
    gBattleStruct->aiSmart = FALSE;

    // Só batalha de treinador contra a IA (link: o outro lado é gente).
    if (!(gBattleTypeFlags & BATTLE_TYPE_TRAINER) || (gBattleTypeFlags & BATTLE_TYPE_LINK))
        return;
    // As mesmas exclusões de BattleAI_SetupAIData: nesses casos as flags do treinador não valem.
    if (gBattleTypeFlags & (BATTLE_TYPE_SAFARI | BATTLE_TYPE_ROAMER | BATTLE_TYPE_WILD_SCRIPTED | BATTLE_TYPE_LEGENDARY_FRLG
                          | BATTLE_TYPE_TRAINER_TOWER | BATTLE_TYPE_EREADER_TRAINER | BATTLE_TYPE_BATTLE_TOWER))
        return;
    if (gTrainerBattleOpponent_A == TRAINER_SECRET_BASE || gTrainerBattleOpponent_A >= NUM_TRAINERS)
        return;

    // As flags efetivas da batalha (BattleAI_SetupAIData): o degrau da revanche já foi aplicado por CreateNPCTrainerParty.
    flags = gTrainers[gTrainerBattleOpponent_A].aiFlags | RematchTier_GetAiFlags();
    if (flags & AI_SCRIPT_HP_AWARE)
        gBattleStruct->aiSmart = TRUE;
}

bool8 AI_IsSmartTrainer(void)
{
    return gBattleStruct->aiSmart;
}

void SmartAI_RecordPlayerMove(u8 battler, u16 move)
{
    u16 *revealed;
    s32 i;

    if (!gBattleStruct->aiSmart || GetBattlerSide(battler) != B_SIDE_PLAYER)
        return;
    if (move == MOVE_NONE || move == 0xFFFF || move == MOVE_STRUGGLE)
        return;
    // Só golpe que o Pokémon conhece: o golpe sorteado por Metronome/Assist/Sleep Talk não conta (o próprio
    // Metronome já foi gravado no 1º "usou").
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (gBattleMons[battler].moves[i] == move)
            break;
    }
    if (i == MAX_MON_MOVES)
        return;

    revealed = gBattleStruct->aiRevealedMoves[gBattlerPartyIndexes[battler]];
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (revealed[i] == move)
            return;
        if (revealed[i] == MOVE_NONE)
        {
            revealed[i] = move;
            return;
        }
    }
}

void SmartAI_NoteVoluntarySwitch(u8 battler)
{
    if (!gBattleStruct->aiSmart || GetBattlerSide(battler) != B_SIDE_OPPONENT)
        return;
    // battleTurnCounter: 0 no 1º turno, +1 em BattleTurnPassed (para em 0xFF); "trocou no turno anterior" na hora
    // da escolha = aiVoluntarySwitchTurn == battleTurnCounter - 1.
    gBattleStruct->aiVoluntarySwitchTurn[GetBattlerPosition(battler) >> 1] = gBattleResults.battleTurnCounter;
}
