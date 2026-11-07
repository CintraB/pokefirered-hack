#include "global.h"
#include "conquistas.h"
#include "data/conquistas_ids.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/game_stat.h"
#include "event_data.h"
#include "overworld.h"
#include "rematch_tier.h"
#include "sala_trofeus.h"
#include "script.h"
#include "string_util.h"

// 0 nada / 1 bronze / 2 prata / 3 ouro. Ouro só com todas as válidas feitas (e pelo menos uma válida).
u8 SalaTrofeus_NivelDaTaca(u8 feitas, u8 validas)
{
    if (validas == 0)
        return TACA_NENHUMA;
    if (feitas >= validas)
        return TACA_OURO;
    if (feitas * 100 >= TACA_PRATA_PCT * validas)
        return TACA_PRATA;
    if (feitas * 100 >= TACA_BRONZE_PCT * validas)
        return TACA_BRONZE;
    return TACA_NENHUMA;
}

// specialvar: VAR_0x8004 = aba (CONQ_ABA_*) -> VAR_RESULT = TACA_*; STR_VAR_1 = nome da aba, 2 = feitas, 3 = válidas.
u16 SalaTrofeus_Taca(void)
{
    u8 feitas, validas;

    if (gSpecialVar_0x8004 >= CONQ_ABAS_COUNT)
        return TACA_NENHUMA;
    Conquistas_ContarAba(gSpecialVar_0x8004, &feitas, &validas);
    StringCopy(gStringVar1, gConquistasAbaNomes[gSpecialVar_0x8004]);
    ConvertIntToDecimalStringN(gStringVar2, feitas, STR_CONV_MODE_LEFT_ALIGN, 3);
    ConvertIntToDecimalStringN(gStringVar3, validas, STR_CONV_MODE_LEFT_ALIGN, 3);
    return SalaTrofeus_NivelDaTaca(feitas, validas);
}

// special: STR_VAR_1 = conquistas feitas, STR_VAR_2 = total válido (as ativas, todas as abas), STR_VAR_3 = batalhas
// marcantes no diário.
void SalaTrofeus_Placa(void)
{
    u8 aba, feitas, validas, totalFeitas = 0, totalValidas = 0;
    u8 evts[DIARIO_MAX];

    for (aba = 0; aba < CONQ_ABAS_COUNT; aba++)
    {
        Conquistas_ContarAba(aba, &feitas, &validas);
        totalFeitas += feitas;
        totalValidas += validas;
    }
    ConvertIntToDecimalStringN(gStringVar1, totalFeitas, STR_CONV_MODE_LEFT_ALIGN, 3);
    ConvertIntToDecimalStringN(gStringVar2, totalValidas, STR_CONV_MODE_LEFT_ALIGN, 3);
    ConvertIntToDecimalStringN(gStringVar3, Diario_ListarEmOrdem(evts), STR_CONV_MODE_LEFT_ALIGN, 3);
}

// specialvar: o maior degrau de revanche vencido (0 = nenhum; 1-5 = Nível 60-100) em VAR_RESULT e o rótulo em
// STR_VAR_1. Save antigo: sem o registro, mas com a conquista do degrau máximo feita, vale o degrau máximo.
u16 SalaTrofeus_PlacaRevanche(void)
{
    u8 degrau = VarGet(VAR_REVANCHE_MAIOR_DEGRAU);

    if (degrau > REMATCH_TIER_MAX)
        degrau = 0;
    if (degrau == 0 && Conquistas_GetEstado(CONQ_REVANCHE_MAX) == CONQ_FEITA)
        degrau = REMATCH_TIER_MAX;
    StringCopy(gStringVar1, GetRematchTierName(degrau));
    return degrau;
}

// special: STR_VAR_1 = vezes no Hall da Fama.
void SalaTrofeus_PlacaHall(void)
{
    ConvertIntToDecimalStringN(gStringVar1, GetGameStat(GAME_STAT_ENTERED_HOF), STR_CONV_MODE_LEFT_ALIGN, 5);
}

// specialvar: o curador. VAR_0x8005 = taças que ainda não são de ouro (0 a 5); devolve quantas rosas já estão nas redomas.
u16 SalaTrofeus_Curador(void)
{
    u8 aba, feitas, validas, faltam = 0, rosas = 0;

    for (aba = 0; aba < CONQ_ABAS_COUNT; aba++)
    {
        Conquistas_ContarAba(aba, &feitas, &validas);
        if (SalaTrofeus_NivelDaTaca(feitas, validas) != TACA_OURO)
            faltam++;
    }
    gSpecialVar_0x8005 = faltam;
    if (FlagGet(FLAG_FAMILIA_ROSA_1)) rosas++;
    if (FlagGet(FLAG_FAMILIA_ROSA_2)) rosas++;
    if (FlagGet(FLAG_FAMILIA_ROSA_3)) rosas++;
    if (FlagGet(FLAG_FAMILIA_ROSA_4)) rosas++;
    return rosas;
}
