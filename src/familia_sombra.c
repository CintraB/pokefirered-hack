#include "global.h"
#include "day_night.h"
#include "event_data.h"
#include "familia_sombra.h"
#include "constants/flags.h"
#include "constants/maps.h"
#include "constants/vars.h"

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

// Limpa o que volta a cada ocupação: itens e maletas do chão e os gêmeos.
// As flags dos 12 treinadores-slot entram na Task 3.
void FamiliaSombra_Repovoar(void)
{
    u16 flag;

    FlagClear(FLAG_FAMILIA_GEMEOS_VENCIDOS);
    for (flag = FLAG_FAMILIA_ITENS_PRIMEIRA; flag <= FLAG_FAMILIA_ITENS_ULTIMA; flag++)
        FlagClear(flag);
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
