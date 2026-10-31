#ifndef GUARD_REMATCH_TIER_H
#define GUARD_REMATCH_TIER_H

#include "global.h"

// Revanches por degrau de dificuldade (POK-42), desenho em docs/superpowers/specs/2026-10-31-revanches-por-degrau-design.md.
//
// O degrau (0 = jogo como hoje; 1-5 = nível-alvo 60, 70, 80, 90, 100) fica salvo em VAR_REMATCH_TIER. Com degrau
// >= 1, a revanche do Vs. Seeker troca o time dentro de CreateNPCTrainerParty pelo da tabela gerada
// src/data/rematch_tiers.h (tools/revanches/gerar.py). O id do treinador não muda: flags, nome, classe e prêmio
// seguem os de hoje. O primeiro combate e o degrau 0 não passam por aqui.

#define REMATCH_TIER_MAX 5
#define REMATCH_TIER_COUNT 5  // tabelas indexadas por degrau - 1

struct RematchTierMon
{
    u16 species;
    u16 heldItem;
    u8 lvl;
    u8 iv;  // 0-31, os 6 iguais (fixedIV do CreateMon)
};

// O degrau salvo; 0 se a var tiver lixo (> REMATCH_TIER_MAX) ou se o jogo ainda não foi zerado.
u8 GetRematchTier(void);
// Marca (TRUE) ou desmarca a batalha de treinador que vai começar como revanche do Vs. Seeker.
void RematchTier_SetVsSeekerBattle(bool8 isRematch);
// Chamada por CreateNPCTrainerParty: 0 = não se aplica (segue o caminho original); senão monta o time do degrau
// em `party` e devolve PARTY_SIZE. Vale para a revanche do Vs. Seeker e para a Elite 4/Campeão (ids 735-741).
u8 RematchTier_CreateParty(struct Pokemon *party, u16 trainerNum);
// O degrau aplicado na última CreateNPCTrainerParty; 0 = nenhum.
u8 GetCurrentBattleRematchTier(void);
// Special das salas da Liga: TRUE = usar os ids _2/REMATCH (depois das Sevii, ou com degrau >= 1). Com degrau
// >= 1, RematchTier_CreateParty troca o time desses ids pelo da tabela sLeagueTierParties.
bool8 ShouldUseLeagueRematchTeams(void);

#endif // GUARD_REMATCH_TIER_H
