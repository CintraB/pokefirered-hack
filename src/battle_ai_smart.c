#include "global.h"
#include "battle.h"
#include "battle_ai_smart.h"
#include "battle_anim.h"
#include "battle_main.h"
#include "battle_script_commands.h"
#include "pokemon.h"
#include "random.h"
#include "rematch_tier.h"
#include "util.h"
#include "constants/abilities.h"
#include "constants/battle_ai.h"
#include "constants/battle_move_effects.h"
#include "constants/items.h"
#include "constants/moves.h"
#include "constants/opponents.h"
#include "constants/trainers.h"

// IA dos chefes (POK-46): estado por batalha e decisões de troca. Ver include/battle_ai_smart.h.

// Ameaças de um Pokémon do jogador: até 4 golpes mostrados + os 2 tipos dele.
#define MAX_THREATS (MAX_MON_MOVES + 2)

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
    // Só golpe que o Pokémon sabe de verdade (os do time, não os de gBattleMons): o golpe sorteado por Metronome,
    // Assist, Mirror Move ou Nature Power não conta (o próprio Metronome etc. já foi gravado no 1º "usou"), nem os
    // copiados por Transform/Mimic. O golpe chamado por Sleep Talk é um que ele sabe, então conta.
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (GetMonData(&gPlayerParty[gBattlerPartyIndexes[battler]], MON_DATA_MOVE1 + i) == move)
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
    // da escolha: SmartAI_SwitchedLastTurn.
    gBattleStruct->aiVoluntarySwitchTurn[GetBattlerPosition(battler) >> 1] = gBattleResults.battleTurnCounter;
}

bool8 SmartAI_SwitchedLastTurn(u8 battler)
{
    u8 counter = gBattleResults.battleTurnCounter;

    // Turno 0: ninguém trocou antes. 0xFF: o contador parou e o "turno anterior" não se distingue mais.
    if (counter != 0 && counter != 0xFF
     && gBattleStruct->aiVoluntarySwitchTurn[GetBattlerPosition(battler) >> 1] == counter - 1)
        return TRUE;
    return FALSE;
}

// --- Tipos ----------------------------------------------------------------------------------------------------------

// Multiplicador x10 de um tipo de ataque contra dois tipos e uma habilidade (0, 2, 5, 10, 20, 40). Imunidade por
// habilidade (Levitate, Flash Fire, Water/Volt Absorb) = 0; Wonder Guard deixa passar só o super efetivo.
static u8 TypeMultX10(u8 atkType, u8 defType1, u8 defType2, u8 defAbility)
{
    s32 i = 0;
    u8 mult = TYPE_MUL_NORMAL;

    if ((defAbility == ABILITY_LEVITATE && atkType == TYPE_GROUND)
     || (defAbility == ABILITY_FLASH_FIRE && atkType == TYPE_FIRE)
     || (defAbility == ABILITY_WATER_ABSORB && atkType == TYPE_WATER)
     || (defAbility == ABILITY_VOLT_ABSORB && atkType == TYPE_ELECTRIC))
        return 0;
    // A linha TYPE_FORESIGHT é só um marcador (nenhum golpe tem esse tipo); as imunidades do Fantasma depois dela valem,
    // como em AI_TypeCalc.
    while (TYPE_EFFECT_ATK_TYPE(i) != TYPE_ENDTABLE)
    {
        if (TYPE_EFFECT_ATK_TYPE(i) == atkType)
        {
            if (TYPE_EFFECT_DEF_TYPE(i) == defType1)
                mult = mult * TYPE_EFFECT_MULTIPLIER(i) / 10;
            if (TYPE_EFFECT_DEF_TYPE(i) == defType2 && defType1 != defType2)
                mult = mult * TYPE_EFFECT_MULTIPLIER(i) / 10;
        }
        i += 3;
    }
    if (defAbility == ABILITY_WONDER_GUARD && mult < TYPE_MUL_SUPER_EFFECTIVE)
        return 0;
    return mult;
}

// O maior multiplicador x10 entre as ameaças (0 = nenhuma ameaça conhecida ou todas sem efeito).
static u8 WorstThreatMult(const u8 *threats, u8 count, u8 defType1, u8 defType2, u8 defAbility)
{
    u8 worst = 0, mult;
    s32 i;

    for (i = 0; i < count; i++)
    {
        mult = TypeMultX10(threats[i], defType1, defType2, defAbility);
        if (mult > worst)
            worst = mult;
    }
    return worst;
}

// Habilidade de um Pokémon fora de campo (como FindMonWithFlagsAndSuperEffective).
static u8 BenchAbility(struct Pokemon *mon, u16 species)
{
    if (GetMonData(mon, MON_DATA_ABILITY_NUM) != 0 && gSpeciesInfo[species].abilities[1] != ABILITY_NONE)
        return gSpeciesInfo[species].abilities[1];
    return gSpeciesInfo[species].abilities[0];
}

static u8 AddThreat(u8 *types, u8 count, u8 max, u8 type)
{
    s32 i;

    for (i = 0; i < count; i++)
    {
        if (types[i] == type)
            return count;
    }
    if (count < max)
        types[count++] = type;
    return count;
}

u8 SmartAI_ThreatTypes(u8 opponentBattler, u8 *types, u8 max)
{
    const u16 *revealed;
    u8 count = 0;
    s32 i;

    if (gAbsentBattlerFlags & gBitTable[opponentBattler])
        return 0;
    // Os golpes que ele já mostrou nesta batalha (a IA não adivinha golpe escondido) e os tipos dele (o palpite óbvio).
    revealed = gBattleStruct->aiRevealedMoves[gBattlerPartyIndexes[opponentBattler]];
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        if (revealed[i] != MOVE_NONE && gBattleMoves[revealed[i]].power > 0)
            count = AddThreat(types, count, max, gBattleMoves[revealed[i]].type);
    }
    count = AddThreat(types, count, max, gBattleMons[opponentBattler].type1);
    count = AddThreat(types, count, max, gBattleMons[opponentBattler].type2);
    return count;
}

// --- Derruba neste turno sendo mais rápido -------------------------------------------------------------------------

// Golpes que não derrubam neste turno: carregam um turno, dependem de estado ou vão por último.
static const u16 sNoKoThisTurnEffects[] =
{
    EFFECT_DREAM_EATER,
    EFFECT_RAZOR_WIND,
    EFFECT_SKY_ATTACK,
    EFFECT_SKULL_BASH,
    EFFECT_SOLAR_BEAM,
    EFFECT_SPIT_UP,
    EFFECT_FOCUS_PUNCH,
    0xFFFF
};

static bool8 CantKoThisTurn(u8 battler, s32 moveIndex)
{
    u16 move = gBattleMons[battler].moves[moveIndex];
    u16 choiced = gBattleStruct->choicedMove[battler];
    s32 i;

    if (move == MOVE_NONE || gBattleMoves[move].power < 2 || gBattleMons[battler].pp[moveIndex] == 0
     || gBattleMoves[move].priority < 0 || move == gDisableStructs[battler].disabledMove)
        return TRUE;
    if (choiced != MOVE_NONE && choiced != 0xFFFF && choiced != move)
        return TRUE;
    if (gDisableStructs[battler].encoreTimer != 0 && gDisableStructs[battler].encoredMove != move)
        return TRUE;
    for (i = 0; sNoKoThisTurnEffects[i] != 0xFFFF; i++)
    {
        if (gBattleMoves[move].effect == sNoKoThisTurnEffects[i])
            return TRUE;
    }
    return FALSE;
}

bool8 SmartAI_CanKoFirst(u8 battler, u8 target)
{
    s32 savedDamage = gBattleMoveDamage;
    u8 savedResultFlags = gMoveResultFlags;
    u16 savedBasePower = gDynamicBasePower;
    u8 savedCritMultiplier = gCritMultiplier;
    u8 savedDmgMultiplier = gBattleScripting.dmgMultiplier;
    u8 savedMoveType = gBattleStruct->dynamicMoveType;
    u16 savedMove = gCurrentMove;
    u16 savedMovePower = gBattleMovePower;
    u8 savedLastUsedAbility = gLastUsedAbility; // CalculateBaseDamage grava nele (Mud/Water Sport)
    bool8 ko = FALSE;
    s8 first = -1;
    s32 i, damage;
    u16 move;

    if ((gBattleMons[battler].status1 & (STATUS1_SLEEP | STATUS1_FREEZE))
     || (gBattleMons[battler].status2 & STATUS2_RECHARGE))
        return FALSE;
    for (i = 0; i < MAX_MON_MOVES && !ko; i++)
    {
        if (CantKoThisTurn(battler, i))
            continue;
        move = gBattleMons[battler].moves[i];
        // Como Cmd_if_can_faint: sem dano dinâmico, sem crítico; o dano é o menor do sorteio (85%).
        gDynamicBasePower = 0;
        gBattleStruct->dynamicMoveType = 0;
        gBattleScripting.dmgMultiplier = 1;
        gMoveResultFlags = 0;
        gCritMultiplier = 1;
        gCurrentMove = move;
        AI_CalcDmg(battler, target);
        if (TypeCalc(move, battler, target) & (MOVE_RESULT_MISSED | MOVE_RESULT_DOESNT_AFFECT_FOE))
            continue;
        damage = gBattleMoveDamage * 85 / 100;
        if (damage == 0)
            damage = 1;
        if (damage < gBattleMons[target].hp)
            continue;
        // Age antes: golpe com prioridade (o golpe do jogador é desconhecido; supõe prioridade 0), ou mais rápido pela
        // velocidade efetiva de GetWhoStrikesFirst (ignorando os golpes escolhidos; empate = sorteio dele).
        if (gBattleMoves[move].priority > 0)
            ko = TRUE;
        else
        {
            if (first < 0)
                first = (GetWhoStrikesFirst(battler, target, TRUE) == 0);
            ko = first;
        }
    }
    gBattleMoveDamage = savedDamage;
    gMoveResultFlags = savedResultFlags;
    gDynamicBasePower = savedBasePower;
    gCritMultiplier = savedCritMultiplier;
    gBattleScripting.dmgMultiplier = savedDmgMultiplier;
    gBattleStruct->dynamicMoveType = savedMoveType;
    gCurrentMove = savedMove;
    gBattleMovePower = savedMovePower;
    gLastUsedAbility = savedLastUsedAbility;
    return ko;
}

// --- Quem entra ------------------------------------------------------------------------------------------------------

u8 SmartAI_ScoreBench(u8 partySlot, u8 opponentBattler)
{
    struct Pokemon *mon = &gEnemyParty[partySlot];
    u16 species = GetMonData(mon, MON_DATA_SPECIES);
    u16 move, hp, maxHP;
    u8 threats[MAX_THREATS];
    u8 count, worst, flags, defense, attack = 0;
    s32 i;

    // Defesa (0-40): o pior multiplicador das ameaças conhecidas do Pokémon do jogador.
    count = SmartAI_ThreatTypes(opponentBattler, threats, MAX_THREATS);
    worst = count ? WorstThreatMult(threats, count, gSpeciesInfo[species].types[0], gSpeciesInfo[species].types[1],
                                    BenchAbility(mon, species))
                  : TYPE_MUL_NORMAL;
    if (worst == 0)
        defense = 40;
    else if (worst <= 2)   // 0,25x
        defense = 35;
    else if (worst <= 5)   // 0,5x
        defense = 30;
    else if (worst <= 10)  // 1x
        defense = 15;
    else if (worst <= 20)  // 2x
        defense = 5;
    else                   // 4x
        defense = 0;

    // Ataque (0-30): o melhor golpe com poder no Pokémon do jogador (pela espécie e habilidade, como o original).
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        move = GetMonData(mon, MON_DATA_MOVE1 + i);
        if (move == MOVE_NONE || gBattleMoves[move].power == 0)
            continue;
        flags = AI_TypeCalc(move, gBattleMons[opponentBattler].species, gBattleMons[opponentBattler].ability);
        if (flags & (MOVE_RESULT_MISSED | MOVE_RESULT_DOESNT_AFFECT_FOE))
            continue;
        if (flags & MOVE_RESULT_SUPER_EFFECTIVE)
        {
            attack = 30;
            break;
        }
        if (flags & MOVE_RESULT_NOT_VERY_EFFECTIVE)
        {
            if (attack < 5)
                attack = 5;
        }
        else if (attack < 10)
        {
            attack = 10;
        }
    }

    // PS atual (0-30).
    hp = GetMonData(mon, MON_DATA_HP);
    maxHP = GetMonData(mon, MON_DATA_MAX_HP);
    return defense + attack + (maxHP != 0 ? hp * 30 / maxHP : 0);
}

// Preso pelas mesmas regras de ShouldSwitch (lidas direto, sem mexer em gLastUsedAbility): para o atalho de teste ver
// a mesma decisão que o jogo tomaria.
static bool8 IsTrapped(u8 battler)
{
    s32 i;

    if ((gBattleMons[battler].status2 & (STATUS2_WRAPPED | STATUS2_ESCAPE_PREVENTION))
     || (gStatuses3[battler] & STATUS3_ROOTED))
        return TRUE;
    for (i = 0; i < gBattlersCount; i++)
    {
        if (GetBattlerSide(i) != GetBattlerSide(battler)
         && (gBattleMons[i].ability == ABILITY_SHADOW_TAG || gBattleMons[i].ability == ABILITY_ARENA_TRAP))
            return TRUE;
        if (gBattleMons[i].ability == ABILITY_MAGNET_PULL && IS_BATTLER_OF_TYPE(battler, TYPE_STEEL))
            return TRUE;
    }
    return FALSE;
}

static bool8 PredictiveSwitch(u8 battler, struct SmartAiDecision *out, bool8 stayRoll)
{
    u8 threats[MAX_THREATS];
    u8 count, opponent, best, bestScore, score;
    s32 i, boosts;
    struct Pokemon *mon;
    u16 species;

    // Só batalha simples: em dupla a leitura da ameaça fica ambígua.
    if (gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
        return FALSE;
    opponent = GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);
    if ((gAbsentBattlerFlags & gBitTable[opponent]) || gBattleMons[battler].hp == 0 || IsTrapped(battler))
        return FALSE;
    // Sem pingue-pongue: quem acabou de entrar por troca voluntária fica.
    if (SmartAI_SwitchedLastTurn(battler))
        return FALSE;
    // Atributos aumentados (soma dos estágios positivos >= 2): jogar o aumento fora é pior.
    boosts = 0;
    for (i = 0; i < NUM_BATTLE_STATS; i++)
    {
        if (gBattleMons[battler].statStages[i] > DEFAULT_STAT_STAGE)
            boosts += gBattleMons[battler].statStages[i] - DEFAULT_STAT_STAGE;
    }
    if (boosts >= 2)
        return FALSE;

    // 1. Alguma ameaça conhecida pega >= 2x no Pokémon em campo.
    count = SmartAI_ThreatTypes(opponent, threats, MAX_THREATS);
    for (i = 0; i < count; i++)
    {
        if (TypeMultX10(threats[i], gBattleMons[battler].type1, gBattleMons[battler].type2,
                        gBattleMons[battler].ability) >= 20)
            break;
    }
    if (i == count)
        return FALSE;
    // 2. Se ele derruba o do jogador neste turno sendo mais rápido, atacar é melhor.
    if (SmartAI_CanKoFirst(battler, opponent))
        return FALSE;
    // 3. Quem entra: PS >= 50% e <= 0,5x de todas as ameaças; entre esses, a melhor pontuação (golpe super efetivo,
    //    depois PS).
    best = PARTY_SIZE;
    bestScore = 0;
    for (i = 0; i < PARTY_SIZE; i++)
    {
        mon = &gEnemyParty[i];
        species = GetMonData(mon, MON_DATA_SPECIES_OR_EGG);
        if (species == SPECIES_NONE || species == SPECIES_EGG || GetMonData(mon, MON_DATA_HP) == 0
         || i == gBattlerPartyIndexes[battler])
            continue;
        if (GetMonData(mon, MON_DATA_HP) * 2 < GetMonData(mon, MON_DATA_MAX_HP))
            continue;
        if (WorstThreatMult(threats, count, gSpeciesInfo[species].types[0], gSpeciesInfo[species].types[1],
                            BenchAbility(mon, species)) > 5)
            continue;
        score = SmartAI_ScoreBench(i, opponent);
        if (best == PARTY_SIZE || score > bestScore)
        {
            best = i;
            bestScore = score;
        }
    }
    if (best == PARTY_SIZE)
        return FALSE;
    // Para não ficar previsível demais: 1 em 5 fica e ataca mesmo assim.
    if (stayRoll && Random() % 5 == 0)
        return FALSE;
    out->action = SMART_AI_SWITCH;
    out->partySlot = best;
    out->item = ITEM_NONE;
    return TRUE;
}

bool8 SmartAI_ChoosePredictiveSwitch(u8 battler, struct SmartAiDecision *out)
{
    return PredictiveSwitch(battler, out, TRUE);
}

u8 SmartAI_ChooseReplacement(u8 battler)
{
    u8 battlerIn1 = battler, battlerIn2 = battler;
    u8 opponents[2], nOpponents = 0;
    u8 threats[MAX_THREATS], count;
    u8 best = PARTY_SIZE, bestWeak = PARTY_SIZE;
    s32 bestScore = -1, bestWeakScore = -1, score;
    bool8 weak;
    s32 i, j;
    struct Pokemon *mon;
    u16 species;
    u8 ability, opponent;

    // Os mesmos excluídos de GetMostSuitableMonToSwitchInto (em campo e já escolhidos, inclusive o do parceiro).
    if (gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
    {
        opponent = GetBattlerAtPosition(GetBattlerPosition(battler) ^ BIT_FLANK);
        if (!(gAbsentBattlerFlags & gBitTable[opponent]))
            battlerIn2 = opponent;
        // Em dupla, soma contra os dois Pokémon do jogador em campo.
        for (i = B_POSITION_PLAYER_LEFT; i <= B_POSITION_PLAYER_RIGHT; i += 2)
        {
            opponent = GetBattlerAtPosition(i);
            if (!(gAbsentBattlerFlags & gBitTable[opponent]))
                opponents[nOpponents++] = opponent;
        }
    }
    if (nOpponents == 0)
        opponents[nOpponents++] = GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);

    for (i = 0; i < PARTY_SIZE; i++)
    {
        mon = &gEnemyParty[i];
        species = GetMonData(mon, MON_DATA_SPECIES_OR_EGG);
        if (species == SPECIES_NONE || species == SPECIES_EGG || GetMonData(mon, MON_DATA_HP) == 0
         || i == gBattlerPartyIndexes[battlerIn1] || i == gBattlerPartyIndexes[battlerIn2]
         || i == gBattleStruct->monToSwitchIntoId[battlerIn1] || i == gBattleStruct->monToSwitchIntoId[battlerIn2])
            continue;
        ability = BenchAbility(mon, species);
        score = 0;
        weak = FALSE;
        for (j = 0; j < nOpponents; j++)
        {
            score += SmartAI_ScoreBench(i, opponents[j]);
            count = SmartAI_ThreatTypes(opponents[j], threats, MAX_THREATS);
            if (WorstThreatMult(threats, count, gSpeciesInfo[species].types[0], gSpeciesInfo[species].types[1],
                                ability) >= 20)
                weak = TRUE;
        }
        // Quem leva >= 2x de alguma ameaça conhecida só entra se não houver outro.
        if (!weak && score > bestScore)
        {
            best = i;
            bestScore = score;
        }
        else if (weak && score > bestWeakScore)
        {
            bestWeak = i;
            bestWeakScore = score;
        }
    }
    return best != PARTY_SIZE ? best : bestWeak;
}

// --- Decisão completa (atalho de teste) ------------------------------------------------------------------------------

void SmartAI_Decide(u8 battler, bool8 noStayRoll, struct SmartAiDecision *out)
{
    if (PredictiveSwitch(battler, out, !noStayRoll))
        return;
    out->action = SMART_AI_ATTACK;
    out->partySlot = PARTY_SIZE;
    out->item = ITEM_NONE;
}
