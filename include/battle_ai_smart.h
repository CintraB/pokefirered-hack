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
// TRUE = o Pokémon do battler entrou por uma troca voluntária do chefe no turno anterior (sem pingue-pongue). No turno
// 0 e com o contador parado em 0xFF é sempre FALSE.
bool8 SmartAI_SwitchedLastTurn(u8 battler);

// --- Decisões (Task 2+): funções puras, só lêem o estado da batalha; quem emite a ação é battle_ai_switch_items.c ---

#define SMART_AI_ATTACK 0
#define SMART_AI_SWITCH 1
#define SMART_AI_ITEM   2

struct SmartAiDecision
{
    u8 action;    // SMART_AI_*
    u8 partySlot; // SWITCH: quem entra (gEnemyParty); senão PARTY_SIZE
    u16 item;     // ITEM: o item; senão ITEM_NONE
};

// Tipos que o Pokémon do jogador em campo ameaça: os dos golpes que ele já mostrou nesta batalha (com poder > 0) e os
// tipos dele, sem repetição. Devolve a quantidade (até `max`).
u8 SmartAI_ThreatTypes(u8 opponentBattler, u8 *types, u8 max);
// TRUE = algum golpe do battler derruba o target neste turno (dano mínimo da IA, 85%) e o battler age antes.
// Mexe só em cópias: as variáveis globais de dano são salvas e restauradas.
bool8 SmartAI_CanKoFirst(u8 battler, u8 target);
// Pontuação (0-100) de um Pokémon do banco (gEnemyParty) contra o Pokémon do jogador: defesa (o pior multiplicador
// das ameaças conhecidas) + ataque (golpe super efetivo nele) + PS atual. Só tipos: o banco não está em gBattleMons.
u8 SmartAI_ScoreBench(u8 partySlot, u8 opponentBattler);
// Troca preditiva (só batalha simples): TRUE e `out` = SWITCH para o slot escolhido quando o Pokémon em campo leva
// >= 2x de uma ameaça, não derruba antes e há no time quem resista (PS >= 50%, <= 0,5x de todas); 1 em 5 fica.
bool8 SmartAI_ChoosePredictiveSwitch(u8 battler, struct SmartAiDecision *out);
// Quem entra (troca sem destino escolhido e substituto depois de desmaio): a melhor pontuação; quem leva >= 2x de uma
// ameaça conhecida só se não houver outro. PARTY_SIZE = nenhum.
u8 SmartAI_ChooseReplacement(u8 battler);
// A decisão completa do chefe (troca preditiva → item → ataque) sem emitir nada; noStayRoll = TRUE tira o sorteio
// "1 em 5 fica e ataca" (atalho de teste TEST_CMD_AI_SMART_DECIDE).
void SmartAI_Decide(u8 battler, bool8 noStayRoll, struct SmartAiDecision *out);

#endif // GUARD_BATTLE_AI_SMART_H
