#include "global.h"
#include "conquistas.h"
#include "data/conquistas_ids.h"

// Conquistas e diário de batalhas (POK-44): o estado no save.
// As duas áreas (SaveBlock1 0x348C e SaveBlock2 0xB20) eram espaço sem uso e têm zeros em todo save
// anterior: magic != CONQ_MAGIC é um save antigo (a varredura retroativa entra na Task 3).

// O resto dos dois blocos fica onde estava: os saves existentes continuam válidos.
STATIC_ASSERT(sizeof(struct ConquistasSave) == 400, ConquistasSaveCabeEmUnused348C);
STATIC_ASSERT(sizeof(struct DiarioEntrada) == 20, DiarioEntradaTem20Bytes);
STATIC_ASSERT(sizeof(struct DiarioSave) == 0x400, DiarioSaveCabeEmFillerB20);
STATIC_ASSERT(offsetof(struct SaveBlock1, conquistas) == 0x348C, ConquistasNoOffsetDoUnused348C);
STATIC_ASSERT(offsetof(struct SaveBlock1, ramScript) == 0x361C, RamScriptNaoMudou);
STATIC_ASSERT(sizeof(struct SaveBlock1) == 0x3D68, SaveBlock1NaoMudouDeTamanho);
STATIC_ASSERT(offsetof(struct SaveBlock2, diario) == 0xB20, DiarioNoOffsetDoFillerB20);
STATIC_ASSERT(offsetof(struct SaveBlock2, encryptionKey) == 0xF20, EncryptionKeyNaoMudou);
STATIC_ASSERT(sizeof(struct SaveBlock2) == 0xF24, SaveBlock2NaoMudouDeTamanho);
STATIC_ASSERT(CONQ_COUNT <= CONQ_MAX, ConquistasCabemNosBits);
STATIC_ASSERT(DIARIO_EVT_COUNT <= DIARIO_MAX, DiarioCabeNasEntradas);

#define sConq (&gSaveBlock1Ptr->conquistas)

// `num` de uma conquista da tabela (um buraco na numeração tem a entrada zerada, sem nome).
bool8 Conquistas_NumValido(u8 num)
{
    return num < CONQ_COUNT && gConquistas[num].nome != NULL;
}

void Conquistas_IniciarJogoNovo(void)
{
    memset(&gSaveBlock1Ptr->conquistas, 0, sizeof(gSaveBlock1Ptr->conquistas));
    memset(&gSaveBlock2Ptr->diario, 0, sizeof(gSaveBlock2Ptr->diario));
    sConq->magic = CONQ_MAGIC;
    sConq->versao = CONQ_VERSAO;
    sConq->origem = CONQ_ORIGEM_JOGO_NOVO;
    sConq->adiadoNoMapa = 0xFFFF;
    gSaveBlock2Ptr->diario.versao = CONQ_VERSAO;
}

u8 Conquistas_GetEstado(u8 num)
{
    if (!Conquistas_NumValido(num))
        return CONQ_PENDENTE;
    return (sConq->estados[num / 4] >> ((num % 4) * 2)) & 3;
}

static void SetEstado(u8 num, u8 estado)
{
    u8 shift = (num % 4) * 2;

    sConq->estados[num / 4] = (sConq->estados[num / 4] & ~(3 << shift)) | (estado << shift);
}

void Conquistas_Marcar(u8 num)
{
    if (Conquistas_NumValido(num) && Conquistas_GetEstado(num) == CONQ_PENDENTE)
        SetEstado(num, CONQ_FEITA);
}

void Conquistas_Perder(u8 num)
{
    if (Conquistas_NumValido(num) && Conquistas_GetEstado(num) == CONQ_PENDENTE)
        SetEstado(num, CONQ_PERDIDA);
}

bool8 Conquistas_Entregue(u8 num)
{
    if (!Conquistas_NumValido(num))
        return FALSE;
    return (sConq->entregues[num / 8] >> (num % 8)) & 1;
}

void Conquistas_SetEntregue(u8 num)
{
    if (Conquistas_NumValido(num))
        sConq->entregues[num / 8] |= 1 << (num % 8);
}

u8 Conquistas_DegrauEntregue(u8 num)
{
    if (!Conquistas_NumValido(num) || gConquistas[num].slotDegrau >= CONQ_MAX_DEGRAUS)
        return 0;
    return sConq->degrauEntregue[gConquistas[num].slotDegrau];
}

void Conquistas_SetDegrauEntregue(u8 num, u8 degrau)
{
    if (Conquistas_NumValido(num) && gConquistas[num].slotDegrau < CONQ_MAX_DEGRAUS)
        sConq->degrauEntregue[gConquistas[num].slotDegrau] = degrau;
}
