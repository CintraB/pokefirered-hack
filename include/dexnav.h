#ifndef GUARD_DEXNAV_H
#define GUARD_DEXNAV_H

#include "global.h"

// DexNav (POK-47): os Pokémon de cada mapa com encontro, com as chances reais da hack, e os mapas visitados.
// Dados: src/dexnav_data.c (mapas, visitados, período) e DexNav_GetMapEntries em src/wild_encounter.c.

// Mapas com encontro do FireRed (132 cabeçalhos, 124 mapas): gDexNavMaps, gerado por tools/dexnav/gerar.py em
// src/data/dexnav_mapas.h (commitado; o teste roda gerar.py --conferir). O índice é o bit de "visitado" no save.
#define DEXNAV_MAP_COUNT 124

#define DEXNAV_REGION_KANTO 0
#define DEXNAV_REGION_SEVII 1  // Ilhas Um a Sete e seus caminhos/cavernas (seção >= MAPSEC_ONE_ISLAND)

// Largura do nome do mapa na coluna da lista (FONT_NORMAL); os nomes gerados cabem nela (test_dexnav_dados.py e
// a checagem de texto da esteira). Imprimir direto de gDexNavMaps[i].name: alguns passam de 20 bytes (gStringVar).
#define DEXNAV_NAME_WIDTH 120

// Jeitos de encontrar (a ordem da enumeração)
#define DEXNAV_METHOD_LAND      0
#define DEXNAV_METHOD_WATER     1
#define DEXNAV_METHOD_OLD_ROD   2
#define DEXNAV_METHOD_GOOD_ROD  3
#define DEXNAV_METHOD_SUPER_ROD 4
#define DEXNAV_METHOD_ROCK      5  // Quebra-Pedra
#define DEXNAV_METHOD_COUNT     6

// Períodos (bits de DexNavEntry.periods; o índice de rateX10 é o número do bit). A tarde-noite do jogo
// (TIME_EVENING) sorteia 50/50 entre as tabelas da tarde e da noite: DexNav_CurrentPeriodBit devolve
// DEXNAV_PERIOD_DAY | DEXNAV_PERIOD_NIGHT e DexNav_RateForPeriods dá a média das duas colunas.
#define DEXNAV_PERIOD_MORNING   1  // TIME_MORNING
#define DEXNAV_PERIOD_DAY       2  // TIME_AFTERNOON
#define DEXNAV_PERIOD_NIGHT     4  // TIME_NIGHT
#define DEXNAV_PERIOD_COUNT     3
#define DEXNAV_PERIOD_ALL       (DEXNAV_PERIOD_MORNING | DEXNAV_PERIOD_DAY | DEXNAV_PERIOD_NIGHT)

// Entradas de um mapa no pior caso (todos os métodos e períodos; conferido pelo espelho Python em pytest)
#define DEXNAV_MAX_ENTRIES 32

// Marcador do save (gSaveBlock1Ptr->dexNav.magic): "DNV1" em little-endian
#define DEXNAV_MAGIC 0x31564E44

struct DexNavMap
{
    u8 mapGroup;
    u8 mapNum;
    u8 region; // DEXNAV_REGION_*
    const u8 *name;
};

// Um resultado possível do mapa: uma espécie num jeito de encontrar, somando os slots dela
struct DexNavEntry
{
    u16 species;
    u8 method;       // DEXNAV_METHOD_*
    u8 minLevel;
    u8 maxLevel;
    u8 periods;      // DEXNAV_PERIOD_* em que aparece
    u16 rateX10[DEXNAV_PERIOD_COUNT]; // por período: chance x 10 (por mil), 0 = não aparece
};

extern const struct DexNavMap gDexNavMaps[DEXNAV_MAP_COUNT];

// src/wild_encounter.c: todos os resultados possíveis do mapa (todos os métodos e períodos), sem sortear nada;
// devolve quantas entradas escreveu em out (no máximo max). Segue as regras do encontro real: chance por slot do
// FRLG, tabela por horário (Hack 7), metade LeafGreen (Hack 8), conjunto atual da Caverna Mutante (dentro dela, a
// var do encontro; de fora, o conjunto do dia que ela recebe ao entrar); câmara de Tanoby trancada devolve 0.
u8 DexNav_GetMapEntries(u8 mapIndex, struct DexNavEntry *out, u8 max);

// src/dexnav_data.c
u8 DexNav_CurrentPeriodBit(void);
u16 DexNav_RateForPeriods(const struct DexNavEntry *entry, u8 periods);
s16 DexNav_MapIndexOf(u8 mapGroup, u8 mapNum);
void DexNav_MarkVisited(u8 mapGroup, u8 mapNum);
bool8 DexNav_IsVisited(u8 mapIndex);
void DexNav_InitSave(void);
void DexNav_UpgradeOldSave(void);

#endif // GUARD_DEXNAV_H
