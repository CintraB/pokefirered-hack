#include "global.h"
#include "battle.h"
#include "battle_setup.h"
#include "day_night.h"
#include "event_data.h"
#include "familia_sombra.h"
#include "pokemon.h"
#include "random.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/maps.h"
#include "constants/moves.h"
#include "constants/opponents.h"
#include "constants/species.h"
#include "constants/trainers.h"
#include "constants/vars.h"
#include "data/familia_sombra_times.h"

// POK-51: estado da Família Sombra. Ocupação (VAR_FAMILIA_OCUPACAO, 0 = nenhuma; 1..4) e estado
// (FAMILIA_ESTADO_*). A volta da máfia conta meios-dias do relógio da hack (src/day_night.c).

static const u16 sRosas[FAMILIA_OCUPACOES_TOTAL] =
{
    FLAG_FAMILIA_ROSA_1,
    FLAG_FAMILIA_ROSA_2,
    FLAG_FAMILIA_ROSA_3,
    FLAG_FAMILIA_ROSA_4,
};

u16 FamiliaSombra_MeiosDiasAgora(void)
{
    return DayNight_GetTotalMinutes() / 720; // 720 minutos do relógio = meio-dia da hack (1 dia = 1 h jogada)
}

u8 FamiliaSombra_Ocupacao(void)
{
    return VarGet(VAR_FAMILIA_OCUPACAO);
}

u8 FamiliaSombra_Estado(void)
{
    return VarGet(VAR_FAMILIA_ESTADO);
}

bool8 FamiliaSombra_ChefeAtivo(void)
{
    return FamiliaSombra_Estado() == FAMILIA_ESTADO_ATIVA;
}

// Limpa o que volta a cada ocupação: itens e maletas do chão, os gêmeos e os 12 treinadores-slot (capangas,
// gêmeos e pedágio).
void FamiliaSombra_Repovoar(void)
{
    u16 flag;

    FlagClear(FLAG_FAMILIA_GEMEOS_VENCIDOS);
    for (flag = FLAG_FAMILIA_ITENS_PRIMEIRA; flag <= FLAG_FAMILIA_ITENS_ULTIMA; flag++)
        FlagClear(flag);
    for (flag = TRAINER_FAMILIA_PRIMEIRO; flag <= TRAINER_FAMILIA_ULTIMO; flag++)
        ClearTrainerFlag(flag);
}

void FamiliaSombra_Atualizar(void)
{
    u8 ocupacao = FamiliaSombra_Ocupacao();

    switch (FamiliaSombra_Estado())
    {
    case FAMILIA_ESTADO_FECHADO:
        if (FlagGet(FLAG_BADGE08_GET))
        {
            VarSet(VAR_FAMILIA_OCUPACAO, 1);
            VarSet(VAR_FAMILIA_ESTADO, FAMILIA_ESTADO_ATIVA);
            FamiliaSombra_Repovoar();
        }
        break;
    case FAMILIA_ESTADO_SEM_CHEFE:
        if ((u32)FamiliaSombra_MeiosDiasAgora() >= (u32)VarGet(VAR_FAMILIA_QUEDA) + FAMILIA_MEIOS_DIAS_RETORNO
         && ocupacao < FAMILIA_OCUPACOES_ATIVAS)
        {
            VarSet(VAR_FAMILIA_OCUPACAO, ocupacao + 1);
            VarSet(VAR_FAMILIA_ESTADO, FAMILIA_ESTADO_ATIVA);
            FamiliaSombra_Repovoar();
        }
        break;
    }
}

void FamiliaSombra_ChefeCaiu(void)
{
    u8 ocupacao = FamiliaSombra_Ocupacao();

    VarSet(VAR_FAMILIA_QUEDA, FamiliaSombra_MeiosDiasAgora());
    VarSet(VAR_FAMILIA_ESTADO, FAMILIA_ESTADO_SEM_CHEFE);
    if (ocupacao >= 1 && ocupacao <= FAMILIA_OCUPACOES_TOTAL)
        FlagSet(sRosas[ocupacao - 1]);
}

// Só o térreo por enquanto (Task 1); os andares 2-6 entram na Task 5.
bool8 FamiliaSombra_NoPredio(void)
{
    return gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ROUTE23_UNUSED_HOUSE)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_ROUTE23_UNUSED_HOUSE);
}

void FamiliaSombra_GetEstado(void)
{
    gSpecialVar_Result = FamiliaSombra_Estado();
}

void FamiliaSombra_GetOcupacao(void)
{
    gSpecialVar_Result = FamiliaSombra_Ocupacao();
}

// ---- Batalhas (Task 3) ----------------------------------------------------------------------------------------

// As 2 lutas do pedágio: índices no plantel da ocupação, sorteados por FamiliaSombra_SortearPedagio.
static EWRAM_DATA u8 sPedagio[2] = {0};

static u8 OcupacaoDasLutas(void)
{
    u8 ocupacao = FamiliaSombra_Ocupacao();

    if (ocupacao < 1 || ocupacao > FAMILIA_OCUPACOES_TOTAL)
        ocupacao = 1;
    return ocupacao;
}

// Batalha contra a Família: treinador da classe FAMILIA_SOMBRA. Os encontros dos andares 4-5 (bit de tipo de
// batalha próprio) entram na Task 4.
bool8 FamiliaSombra_EhBatalhaDaFamilia(void)
{
    if (!(gBattleTypeFlags & BATTLE_TYPE_TRAINER)
     || gBattleTypeFlags & (BATTLE_TYPE_LINK | BATTLE_TYPE_BATTLE_TOWER | BATTLE_TYPE_TRAINER_TOWER | BATTLE_TYPE_EREADER_TRAINER)
     || gTrainerBattleOpponent_A >= NUM_TRAINERS)
        return FALSE;
    return gTrainers[gTrainerBattleOpponent_A].trainerClass == TRAINER_CLASS_FAMILIA_SOMBRA;
}

static void CriarMembro(struct Pokemon *mon, const struct FamiliaMembro *membro, u8 level)
{
    s32 i;

    // IVs no máximo e sem shiny (OT_ID_RANDOM_NO_SHINY); natureza e habilidade ao acaso.
    CreateMon(mon, membro->species, level, MAX_PER_STAT_IVS, FALSE, 0, OT_ID_RANDOM_NO_SHINY, 0);
    SetMonData(mon, MON_DATA_HELD_ITEM, &membro->heldItem);
    for (i = 0; i < MAX_MON_MOVES; i++)
    {
        SetMonData(mon, MON_DATA_MOVE1 + i, &membro->moves[i]);
        SetMonData(mon, MON_DATA_PP1 + i, &gBattleMoves[membro->moves[i]].pp);
    }
}

// Monta em `party` o time do treinador da Família na ocupação atual; devolve o tamanho (0 = não é da Família).
u8 FamiliaSombra_CriarTime(struct Pokemon *party, u16 trainerId)
{
    u8 ocupacao, nivelExtra, segundo;

    if (trainerId < TRAINER_FAMILIA_PRIMEIRO || trainerId > TRAINER_FAMILIA_ULTIMO)
        return 0;

    ocupacao = OcupacaoDasLutas();
    nivelExtra = (ocupacao - 1) * FAMILIA_NIVEL_PASSO;
    ZeroEnemyPartyMons();
    switch (trainerId)
    {
    case TRAINER_FAMILIA_GEMEOS:
        CriarMembro(&party[0], &sFamiliaGemeos[ocupacao - 1][0], sFamiliaGemeos[ocupacao - 1][0].level);
        CriarMembro(&party[1], &sFamiliaGemeos[ocupacao - 1][1], sFamiliaGemeos[ocupacao - 1][1].level);
        return 2;
    case TRAINER_FAMILIA_PEDAGIO_1:
        CriarMembro(&party[0], &sFamiliaPlantel[ocupacao - 1][sPedagio[0] % FAMILIA_PLANTEL],
                    FAMILIA_NIVEL_PEDAGIO_1 + nivelExtra);
        return 1;
    case TRAINER_FAMILIA_PEDAGIO_2:
        // Nunca a mesma espécie da 1ª luta, mesmo sem sorteio.
        segundo = sPedagio[1] % FAMILIA_PLANTEL;
        if (segundo == sPedagio[0] % FAMILIA_PLANTEL)
            segundo = (segundo + 1) % FAMILIA_PLANTEL;
        CriarMembro(&party[0], &sFamiliaPlantel[ocupacao - 1][segundo], FAMILIA_NIVEL_PEDAGIO_2 + nivelExtra);
        return 1;
    default:
        CriarMembro(&party[0], &sFamiliaCapangas[ocupacao - 1][trainerId - TRAINER_FAMILIA_CAPANGA_1],
                    sFamiliaCapangas[ocupacao - 1][trainerId - TRAINER_FAMILIA_CAPANGA_1].level);
        return 1;
    }
}

// Special: sorteia 2 membros diferentes do plantel da ocupação para as 2 lutas do pedágio (passar à força).
void FamiliaSombra_SortearPedagio(void)
{
    sPedagio[0] = Random() % FAMILIA_PLANTEL;
    sPedagio[1] = (sPedagio[0] + 1 + Random() % (FAMILIA_PLANTEL - 1)) % FAMILIA_PLANTEL;
}
