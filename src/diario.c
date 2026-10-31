#include "global.h"
#include "conquistas.h"
#include "battle.h"
#include "pokemon.h"
#include "constants/battle.h"
#include "data/conquistas_ids.h"

// Diário de batalhas marcantes (POK-44): a primeira vitória/captura de cada evento de gDiarioEventos, em
// gSaveBlock2Ptr->diario (struct DiarioSave, índice = DIARIO_EVT_*). Revanche nunca entra: um slot preenchido
// não muda, salvo o lendário capturado depois de um DERROTOU (troca a entrada, com ordem nova).

#define sDiario (&gSaveBlock2Ptr->diario)
#define NENHUM_EVENTO 0xFF

static u8 EventoDoTreinador(u16 treinador)
{
    u8 evt;
    const u16 *t;

    for (evt = 0; evt < DIARIO_EVT_COUNT; evt++)
    {
        if (gDiarioEventos[evt].tipo != DIARIO_TIPO_TREINADOR || gDiarioEventos[evt].treinadores == NULL)
            continue;
        for (t = gDiarioEventos[evt].treinadores; *t != 0xFFFF; t++)
        {
            if (*t == treinador)
                return evt;
        }
    }
    return NENHUM_EVENTO;
}

static u8 EventoDoLendario(u16 especie)
{
    u8 evt;

    for (evt = 0; evt < DIARIO_EVT_COUNT; evt++)
    {
        if (gDiarioEventos[evt].tipo == DIARIO_TIPO_LENDARIO && gDiarioEventos[evt].especie == especie)
            return evt;
    }
    return NENHUM_EVENTO;
}

// Grava (ou regrava) a entrada `evt` com o estado do fim desta batalha. gBattleStruct ainda existe aqui
// (HandleEndTurn_FinishBattle; ele só é liberado na volta ao campo).
static void Registrar(u8 evt, u8 resultado)
{
    struct DiarioEntrada *e = &sDiario->entradas[evt];
    u32 minutos = gSaveBlock2Ptr->playTimeHours * 60 + gSaveBlock2Ptr->playTimeMinutes;
    u32 personalidade, capturado = 0;
    bool8 houveCaptura = (resultado == DIARIO_CAPTURADO);
    u16 especie;
    u8 i, j, n = 0, maisNocautes = 0;

    memset(e, 0, sizeof(*e));
    e->minutos = minutos < 0xFFFF ? minutos : 0xFFFF;
    // o motor só soma o turno quando a batalha continua: o turno que a encerra fica de fora
    e->turnos = gBattleResults.battleTurnCounter < 0xFF ? gBattleResults.battleTurnCounter + 1 : 0xFF;
    e->resultado = resultado;
    e->mvp = 0xFF;
    // o capturado já entrou no time (Cmd_givecaughtmon vem antes do fim da batalha), mas não lutou
    if (houveCaptura)
        capturado = GetMonData(&gEnemyParty[0], MON_DATA_PERSONALITY);
    // o time na ordem do time, sem os ovos nem o capturado; o MVP (o que mais nocauteou, o primeiro no empate; índice
    // em time[]) é achado pela personalidade, que não muda com as trocas da batalha
    for (i = 0; i < PARTY_SIZE; i++)
    {
        especie = GetMonData(&gPlayerParty[i], MON_DATA_SPECIES);
        if (especie == SPECIES_NONE || GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
            continue;
        personalidade = GetMonData(&gPlayerParty[i], MON_DATA_PERSONALITY);
        if (houveCaptura && personalidade == capturado && especie == GetMonData(&gEnemyParty[0], MON_DATA_SPECIES))
            continue;
        e->time[n] = especie | GetMonData(&gPlayerParty[i], MON_DATA_LEVEL) << 9;
        for (j = 0; j < PARTY_SIZE; j++)
        {
            if (gBattleStruct->conqNocautes[j] > maisNocautes && gBattleStruct->conqPersonalidade[j] == personalidade)
            {
                maisNocautes = gBattleStruct->conqNocautes[j];
                e->mvp = n;
            }
        }
        n++;
    }
    e->tamanhoTime = n;
    e->mvpNocautes = maisNocautes;
    // ordem 0 = slot vazio: o proximaOrdem 0 de um diário recém-zerado (jogo novo ou varredura) conta como 1.
    // 33 eventos + no máximo 14 trocas de lendário: o teto de 255 nunca chega (fica nele para não voltar a 0).
    if (sDiario->proximaOrdem == 0)
        sDiario->proximaOrdem = 1;
    e->ordem = sDiario->proximaOrdem;
    if (sDiario->proximaOrdem < 0xFF)
        sDiario->proximaOrdem++;
}

// Chamado por Conquistas_OnFimDeBatalha, que já deixou de fora link, Pokédude, tutorial do velho, Trainer Tower,
// e-Reader e Battle Tower. Num save sem marcador não faz nada (a varredura zera o diário ao gravar o marcador).
void Diario_OnFimDeBatalha(void)
{
    struct DiarioEntrada *e;
    u8 evt;

    if (gSaveBlock1Ptr->conquistas.magic != CONQ_MAGIC)
        return;
    if (gBattleTypeFlags & BATTLE_TYPE_TRAINER)
    {
        // derrota não registra nada; vitória só no slot vazio
        if (gBattleOutcome != B_OUTCOME_WON)
            return;
        evt = EventoDoTreinador(gTrainerBattleOpponent_A);
        if (evt != NENHUM_EVENTO && sDiario->entradas[evt].ordem == 0)
            Registrar(evt, DIARIO_VENCEU);
        return;
    }
    evt = EventoDoLendario(GetMonData(&gEnemyParty[0], MON_DATA_SPECIES));
    if (evt == NENHUM_EVENTO)
        return;
    e = &sDiario->entradas[evt];
    if (gBattleOutcome == B_OUTCOME_CAUGHT && (e->ordem == 0 || e->resultado == DIARIO_DERROTOU))
        Registrar(evt, DIARIO_CAPTURADO);
    else if (gBattleOutcome == B_OUTCOME_WON && e->ordem == 0)
        Registrar(evt, DIARIO_DERROTOU);
}

const struct DiarioEntrada *Diario_GetEntrada(u8 evt)
{
    if (evt >= DIARIO_EVT_COUNT || sDiario->entradas[evt].ordem == 0)
        return NULL;
    return &sDiario->entradas[evt];
}

// `evts` precisa de DIARIO_EVT_COUNT posições.
u8 Diario_ListarEmOrdem(u8 *evts)
{
    u8 evt, n = 0, i;

    for (evt = 0; evt < DIARIO_EVT_COUNT; evt++)
    {
        if (sDiario->entradas[evt].ordem == 0)
            continue;
        // inserção: desloca para a direita os de ordem maior
        for (i = n; i > 0 && sDiario->entradas[evts[i - 1]].ordem > sDiario->entradas[evt].ordem; i--)
            evts[i] = evts[i - 1];
        evts[i] = evt;
        n++;
    }
    return n;
}
