#ifndef GUARD_BATTLE_AI_SMART_H
#define GUARD_BATTLE_AI_SMART_H

#include "global.h"

// IA com troca preditiva e itens (POK-46), desenho em docs/superpowers/specs/2026-10-31-ia-troca-e-itens-design.md.
//
// Só os chefes (flags efetivas da batalha com AI_SCRIPT_HP_AWARE: os 43 do POK-32 e as revanches do Vs. Seeker no
// degrau >= 3 do POK-42) usam a IA nova; todo código novo fica atrás de AI_IsSmartTrainer(). O estado mora em
// gBattleStruct (memória da batalha, zerada a cada batalha), não em EWRAM global nem no save.

// Marca de turno "nunca" em aiVoluntarySwitchTurn/aiHealTurn (os turnos são gBattleResults.battleTurnCounter, u8).
#define SMART_AI_NEVER 0xFFFF

// Calcula se o oponente é um chefe e zera o resto do estado; chamada uma vez por batalha, em CB2_InitBattleInternal,
// depois de CreateNPCTrainerParty (o degrau da revanche já aplicado).
void SmartAI_InitBattle(void);
// TRUE = o oponente desta batalha é um chefe.
bool8 AI_IsSmartTrainer(void);
// Chamada quando o "X usou Y!" de um golpe aparece (Cmd_attackstring): grava o golpe entre os mostrados pelo Pokémon
// do jogador nesta batalha (só num chefe, só do lado do jogador, só golpe que ele conhece; sem repetir).
void SmartAI_RecordPlayerMove(u8 battler, u16 move);
// A IA do chefe escolheu trocar por vontade própria (AI_TrySwitchOrUseItem): guarda o turno, por posição.
void SmartAI_NoteVoluntarySwitch(u8 battler);

#endif // GUARD_BATTLE_AI_SMART_H
