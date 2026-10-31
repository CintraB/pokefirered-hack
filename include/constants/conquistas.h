#ifndef GUARD_CONSTANTS_CONQUISTAS_H
#define GUARD_CONSTANTS_CONQUISTAS_H

// Conquistas e diário de batalhas (POK-44). Valores estáveis: entram no save ou na tabela gerada
// (src/data/conquistas/conquistas.json -> tools/conquistas/gen_conquistas.py). Não renumerar.

#define CONQ_MAGIC        0x31445143   // "CQD1"
#define CONQ_VERSAO       1
#define CONQ_MAX          64           // conquistas (campo `num` do JSON: 0 a 63)
#define CONQ_MAX_DEGRAUS  8            // conquistas com degraus (cada uma usa um slot de progresso no save)
#define DIARIO_MAX        48           // entradas do diário no save

// Estado de cada conquista no save.
#define CONQ_PENDENTE 0
#define CONQ_FEITA    1
#define CONQ_PERDIDA  2

// Como a varredura retroativa foi feita (campo de origem do save).
#define CONQ_ORIGEM_JOGO_NOVO    0
#define CONQ_ORIGEM_SAVE_ANTIGO  1

// Resultado de cada entrada do diário.
#define DIARIO_VENCEU     1
#define DIARIO_CAPTURADO  2
#define DIARIO_DERROTOU   3

// Taxa de captura (catchRate) até a qual a espécie conta como "difícil" na Poké Ball comum.
#define CONQ_TAXA_DIFICIL 45

// Tipos de conquista (struct Conquista.tipo). O significado de `param`/`param2`/`lista`/`degraus`
// de cada tipo está em include/conquistas.h.
#define CONQ_TIPO_FLAG          0
#define CONQ_TIPO_FLAGS_TODAS   1
#define CONQ_TIPO_DEX_TODOS     2
#define CONQ_TIPO_DEX_KANTO     3
#define CONQ_TIPO_DEX_NACIONAL  4
#define CONQ_TIPO_NIVEL         5
#define CONQ_TIPO_AMIZADE_MAX   6
#define CONQ_TIPO_GAME_STAT     7
#define CONQ_TIPO_DINHEIRO      8
#define CONQ_TIPO_HORAS         9
#define CONQ_TIPO_VITORIAS      10
#define CONQ_TIPO_SHINIES       11
#define CONQ_TIPO_EVENTO        12

// Eventos pontuais (CONQ_TIPO_EVENTO: `param` é uma destas constantes).
#define CONQ_EVT_LIDER_UM_POKEMON   0
#define CONQ_EVT_SEM_DESMAIO        1
#define CONQ_EVT_GOLPE_X4           2
#define CONQ_EVT_RIVAL_TODAS        3
#define CONQ_EVT_POKE_BALL_DIFICIL  4
#define CONQ_EVT_OVO_SHINY          5
#define CONQ_EVT_OVO_6IVS           6
#define CONQ_EVT_ELITE4             7
#define CONQ_EVT_REVANCHE_MAX       8   // POK-42: RematchTier_OnRematchWon (src/rematch_tier.c)
#define CONQ_EVT_E4_DEGRAU100       9   // POK-42: RematchTier_OnLeagueCleared (src/rematch_tier.c)

// Tipos de evento do diário (struct DiarioEvento.tipo).
#define DIARIO_TIPO_TREINADOR  0
#define DIARIO_TIPO_LENDARIO   1

#endif // GUARD_CONSTANTS_CONQUISTAS_H
