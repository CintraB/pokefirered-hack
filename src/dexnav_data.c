#include "global.h"
#include "dexnav.h"
#include "day_night.h"
#include "event_data.h"
#include "constants/day_night.h"
#include "constants/flags.h"
#include "constants/maps.h"

// DexNav (POK-47): a tabela dos mapas com encontro, os mapas visitados no save e o período do dia.
// As entradas de cada mapa (espécies, chances e níveis) saem de DexNav_GetMapEntries, em src/wild_encounter.c.

#include "data/dexnav_mapas.h"

// O resto do SaveBlock1 fica onde estava: os saves existentes continuam válidos.
STATIC_ASSERT(sizeof(struct DexNavSave) == 64, DexNavSaveCabeEmUnused3A94);
STATIC_ASSERT(offsetof(struct SaveBlock1, dexNav) == 0x3A94, DexNavNoOffsetDoUnused3A94);
STATIC_ASSERT(offsetof(struct SaveBlock1, registeredTexts) == 0x3AD4, RegisteredTextsNaoMudou);
STATIC_ASSERT(sizeof(struct SaveBlock1) == 0x3D68, SaveBlock1NaoMudouDeTamanho);
STATIC_ASSERT(DEXNAV_MAP_COUNT <= sizeof(((struct DexNavSave *)0)->visitedMaps) * 8, UmBitPorMapa);
STATIC_ASSERT(DEXNAV_MAPAS_GERADOS == DEXNAV_MAP_COUNT, TabelaGeradaComOsMapasDoHeader);
STATIC_ASSERT(offsetof(struct DexNavSave, lastMapIndex) == 0x14, LastMapIndexNoPrimeiroByteLivre);
STATIC_ASSERT(DEXNAV_MAP_COUNT < DEXNAV_LAST_MAP_NONE, LastMapIndexCabeNumByte);

// A tarde-noite (TIME_EVENING) sorteia 50/50 a tabela da tarde ou a da noite (GetTimeOfDayLandSpecies)
u8 DexNav_CurrentPeriodBit(void)
{
    switch (DayNight_GetPeriod())
    {
    case TIME_MORNING:
        return DEXNAV_PERIOD_MORNING;
    case TIME_AFTERNOON:
        return DEXNAV_PERIOD_DAY;
    case TIME_EVENING:
        return DEXNAV_PERIOD_DAY | DEXNAV_PERIOD_NIGHT;
    default:
        return DEXNAV_PERIOD_NIGHT;
    }
}

// Chance (x 10) da entrada quando os períodos de `periods` valem por igual: um período é a coluna dele; a
// tarde-noite (DAY | NIGHT) é a média das duas, arredondada
u16 DexNav_RateForPeriods(const struct DexNavEntry *entry, u8 periods)
{
    u32 sum = 0, count = 0, i;

    for (i = 0; i < DEXNAV_PERIOD_COUNT; i++)
    {
        if (periods & (1 << i))
        {
            sum += entry->rateX10[i];
            count++;
        }
    }
    if (count == 0)
        return 0;
    return (sum + count / 2) / count;
}

// Índice do mapa em gDexNavMaps, ou -1 se o mapa não tem encontro
s16 DexNav_MapIndexOf(u8 mapGroup, u8 mapNum)
{
    s32 i;

    for (i = 0; i < DEXNAV_MAP_COUNT; i++)
    {
        if (gDexNavMaps[i].mapGroup == mapGroup && gDexNavMaps[i].mapNum == mapNum)
            return i;
    }
    return -1;
}

// Chamada a cada mapa carregado (InitMapLayoutData, src/fieldmap.c); mapa sem encontro não tem bit. O último mapa com
// encontro fica guardado: o DexNav aberto numa cidade ou interior abre a lista de mapas nele.
void DexNav_MarkVisited(u8 mapGroup, u8 mapNum)
{
    s16 index = DexNav_MapIndexOf(mapGroup, mapNum);

    if (index >= 0)
    {
        gSaveBlock1Ptr->dexNav.visitedMaps[index / 8] |= 1 << (index % 8);
        gSaveBlock1Ptr->dexNav.lastMapIndex = index;
    }
}

bool8 DexNav_IsVisited(u8 mapIndex)
{
    if (mapIndex >= DEXNAV_MAP_COUNT)
        return FALSE;
    return (gSaveBlock1Ptr->dexNav.visitedMaps[mapIndex / 8] >> (mapIndex % 8)) & 1;
}

// Jogo novo (NewGameInitData, depois de ClearSav1): nenhum mapa visitado, com o marcador
void DexNav_InitSave(void)
{
    memset(&gSaveBlock1Ptr->dexNav, 0, sizeof(gSaveBlock1Ptr->dexNav));
    gSaveBlock1Ptr->dexNav.magic = DEXNAV_MAGIC;
    gSaveBlock1Ptr->dexNav.lastMapIndex = DEXNAV_LAST_MAP_NONE;
}

// CONTINUAR (junto de GivePortablePcIfMissing, src/overworld.c). Save de antes do DexNav (sem marcador): zera a
// área, grava o marcador e, se o jogo já foi zerado, conta todos os mapas como visitados; senão, só daqui em
// diante (o mapa atual é marcado logo depois, ao carregar o mapa do save).
void DexNav_UpgradeOldSave(void)
{
    u32 i;

    if (gSaveBlock1Ptr->dexNav.magic == DEXNAV_MAGIC)
        return;
    memset(&gSaveBlock1Ptr->dexNav, 0, sizeof(gSaveBlock1Ptr->dexNav));
    gSaveBlock1Ptr->dexNav.magic = DEXNAV_MAGIC;
    gSaveBlock1Ptr->dexNav.lastMapIndex = DEXNAV_LAST_MAP_NONE;
    if (FlagGet(FLAG_SYS_GAME_CLEAR))
    {
        for (i = 0; i < DEXNAV_MAP_COUNT; i++)
            gSaveBlock1Ptr->dexNav.visitedMaps[i / 8] |= 1 << (i % 8);
    }
}
