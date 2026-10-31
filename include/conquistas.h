#ifndef GUARD_CONQUISTAS_H
#define GUARD_CONQUISTAS_H

#include "global.h"
#include "constants/conquistas.h"

// Conquistas e diário de batalhas (POK-44), desenho em docs/superpowers/specs/2026-10-31-conquistas-e-diario-design.md.
//
// A tabela mora em src/data/conquistas/conquistas.json; o make gera, com tools/conquistas/gen_conquistas.py,
// src/data/conquistas_ids.h (CONQ_<ID>, CONQ_ABA_<ID>, DIARIO_EVT_<ID> e as contagens) e
// src/data/conquistas_tabela.h (as tabelas abaixo; só `const`, sem EWRAM). Os tipos e as larguras de texto
// ficam aqui: a checagem de texto da esteira (test/esteira/check_text.py) lê as constantes *_LARGURA.

// Larguras úteis (px, FONT_NORMAL, 1 linha). O nome de conquista com degraus traz {STR_VAR_1} no lugar do
// {N} do JSON; a medida usa "300" (o maior degrau).
#define CONQ_NOME_LARGURA    152
#define DIARIO_NOME_LARGURA  80
#define DIARIO_LOCAL_LARGURA 136

struct ConquistaPremio
{
    u16 item;
    u8 qtd;
};

// param / param2 / lista / degraus, por tipo:
//   FLAG          param = flag
//   FLAGS_TODAS   param = primeira flag, param2 = quantas (flags consecutivas)
//   DEX_TODOS     lista = espécies (SPECIES_*, termina em 0xFFFF), todas capturadas
//   DEX_KANTO     param = quantas de Kanto (151) capturadas
//   DEX_NACIONAL  param = quantas capturadas (as obtíveis no jogo)
//   NIVEL         param = nível mínimo de algum Pokémon (equipe ou PC)
//   AMIZADE_MAX   param = amizade (255) de algum Pokémon
//   GAME_STAT     param = GAME_STAT_*, param2 = valor mínimo
//   DINHEIRO      param = ₽ mínimos
//   HORAS         degraus = horas de jogo
//   VITORIAS      degraus = treinadores derrotados
//   SHINIES       degraus = shinies capturados/chocados
//   EVENTO        param = CONQ_EVT_*
// Com degraus, `numDegraus` > 0 e `slotDegrau` (0 a CONQ_MAX_DEGRAUS - 1) é o slot de progresso no save;
// sem degraus `slotDegrau` é 0xFF. `premios` tem max(1, numDegraus) entradas (um prêmio por degrau).
struct Conquista
{
    const u8 *nome;
    u8 aba;
    u8 tipo;
    u8 numDegraus;
    u8 slotDegrau;
    bool8 perdivel;   // pode ser perdida num save que já passou da chance
    bool8 ativa;      // false = existe na tabela mas não aparece, não conta e não dispara (POK-42)
    u16 param2;
    u32 param;
    const u16 *lista;
    const u16 *degraus;
    const struct ConquistaPremio *premios;
};

// `treinadores` (TRAINER_*, termina em 0xFFFF) para o tipo TREINADOR; `especie` para o tipo LENDARIO.
struct DiarioEvento
{
    const u8 *nome;
    const u8 *local;
    u8 tipo;
    bool8 lider;
    bool8 rival;
    u16 especie;
    const u16 *treinadores;
};

extern const struct Conquista gConquistas[];
extern const struct DiarioEvento gDiarioEventos[];
extern const u8 *const gConquistasAbaNomes[];

#endif // GUARD_CONQUISTAS_H
