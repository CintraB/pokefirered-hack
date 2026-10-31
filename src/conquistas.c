#include "global.h"
#include "conquistas.h"
#include "battle.h"
#include "battle_anim.h"
#include "event_data.h"
#include "field_specials.h"
#include "money.h"
#include "overworld.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "constants/battle_move_effects.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/moves.h"
#include "constants/opponents.h"
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

// --- Regras de estado (Task 3) -----------------------------------------------------------------------------
// Cada tipo de estado tem uma função de avaliação, e o `switch` de CumpreEstado é o único despacho: a checagem
// cadenciada (Conquistas_ChecarEstado) e a varredura do save antigo passam por ele. EVENTO não tem regra de
// estado (só os gatilhos da Task 4 e a varredura mexem nele).

// O que o time (e, só na varredura, o PC) mostra. Ovo ainda não chocado não conta.
struct ConqLeituraMons
{
    u8 nivelMax;
    u8 amizadeMax;
    u16 shinies;     // não-ovo shiny
    bool8 ovoShiny;  // chocado pelo jogador (MET_LEVEL 0, OT = jogador) e shiny
    bool8 ovo6Ivs;   // chocado pelo jogador com os 6 IVs 31
};

static bool8 Ativa(u8 num)
{
    return Conquistas_NumValido(num) && gConquistas[num].ativa;
}

// `daEquipe`: o Pokémon do time (o nível vem do campo próprio) ou NULL no PC (o nível vem da EXP). Os filtros de
// vaga vazia, ovo e Bad Egg vêm antes de qualquer leitura que use a espécie (a de um Bad Egg é lixo).
static void LerMon(struct BoxPokemon *boxMon, struct Pokemon *daEquipe, u32 otJogador, struct ConqLeituraMons *l)
{
    u32 otId, personalidade, campo;
    u8 nivel, amizade;
    bool8 shiny, ivs31;

    if (!GetBoxMonData(boxMon, MON_DATA_SANITY_HAS_SPECIES) || GetBoxMonData(boxMon, MON_DATA_SANITY_IS_EGG)
     || GetBoxMonData(boxMon, MON_DATA_SANITY_IS_BAD_EGG))
        return;
    nivel = daEquipe != NULL ? GetMonData(daEquipe, MON_DATA_LEVEL) : GetLevelFromBoxMonExp(boxMon);
    otId = GetBoxMonData(boxMon, MON_DATA_OT_ID);
    personalidade = GetBoxMonData(boxMon, MON_DATA_PERSONALITY);
    shiny = GET_SHINY_VALUE(otId, personalidade) < SHINY_ODDS;
    amizade = GetBoxMonData(boxMon, MON_DATA_FRIENDSHIP);
    if (nivel > l->nivelMax)
        l->nivelMax = nivel;
    if (amizade > l->amizadeMax)
        l->amizadeMax = amizade;
    if (shiny && l->shinies < 0xFFFF)
        l->shinies++;
    // chocado de um ovo do próprio jogador
    if (GetBoxMonData(boxMon, MON_DATA_MET_LEVEL) != 0 || otId != otJogador)
        return;
    if (shiny)
        l->ovoShiny = TRUE;
    ivs31 = TRUE;
    for (campo = MON_DATA_HP_IV; campo <= MON_DATA_SPDEF_IV; campo++)
    {
        if (GetBoxMonData(boxMon, campo) != MAX_PER_STAT_IVS)
            ivs31 = FALSE;
    }
    if (ivs31)
        l->ovo6Ivs = TRUE;
}

static void LerTime(struct ConqLeituraMons *l, u32 otJogador)
{
    u8 i;

    for (i = 0; i < PARTY_SIZE; i++)
        LerMon(&gPlayerParty[i].box, &gPlayerParty[i], otJogador, l);
}

// Só a varredura do save antigo chama isto: o PC tem TOTAL_BOXES_COUNT * IN_BOX_COUNT Pokémon a decifrar.
static void VarrerTimeEPC(struct ConqLeituraMons *l)
{
    u32 otJogador = GetPlayerTrainerId();
    u8 caixa, pos;

    LerTime(l, otJogador);
    for (caixa = 0; caixa < TOTAL_BOXES_COUNT; caixa++)
    {
        for (pos = 0; pos < IN_BOX_COUNT; pos++)
        {
            LerMon(GetBoxedMonPtr(caixa, pos), NULL, otJogador, l);
        }
    }
}

// Os treinadores que o `set_gym_trainers N` (data/scripts/set_gym_trainers.inc) liga como derrotados ao vencer o
// líder do Ginásio N, tenha o jogador lutado com eles ou não. Ordem = insígnia (FLAG_BADGE01_GET + N - 1); 0xFFFF
// termina. test/tests/test_conquistas_regras.py confere esta tabela contra o .inc.
#define CONQ_GINASIO_MAX_TREINADORES 8
static const u16 sTreinadoresDoGinasio[NUM_BADGES][CONQ_GINASIO_MAX_TREINADORES + 1] =
{
    {TRAINER_CAMPER_LIAM, 0xFFFF},
    {TRAINER_PICNICKER_DIANA, TRAINER_SWIMMER_MALE_LUIS, 0xFFFF},
    {TRAINER_SAILOR_DWAYNE, TRAINER_ENGINEER_BAILY, TRAINER_GENTLEMAN_TUCKER, 0xFFFF},
    {TRAINER_LASS_KAY, TRAINER_LASS_LISA, TRAINER_PICNICKER_TINA, TRAINER_BEAUTY_BRIDGET, TRAINER_BEAUTY_TAMIA,
     TRAINER_BEAUTY_LORI, TRAINER_COOLTRAINER_MARY, 0xFFFF},
    {TRAINER_TAMER_PHIL, TRAINER_TAMER_EDGAR, TRAINER_JUGGLER_KIRK, TRAINER_JUGGLER_SHAWN, TRAINER_JUGGLER_KAYDEN,
     TRAINER_JUGGLER_NATE, 0xFFFF},
    {TRAINER_PSYCHIC_JOHAN, TRAINER_PSYCHIC_TYRON, TRAINER_PSYCHIC_CAMERON, TRAINER_PSYCHIC_PRESTON,
     TRAINER_CHANNELER_AMANDA, TRAINER_CHANNELER_STACY, TRAINER_CHANNELER_TASHA, 0xFFFF},
    {TRAINER_SUPER_NERD_ERIK, TRAINER_SUPER_NERD_AVERY, TRAINER_SUPER_NERD_DEREK, TRAINER_SUPER_NERD_ZAC,
     TRAINER_BURGLAR_QUINN, TRAINER_BURGLAR_RAMON, TRAINER_BURGLAR_DUSTY, 0xFFFF},
    {TRAINER_TAMER_JASON, TRAINER_TAMER_COLE, TRAINER_BLACK_BELT_ATSUSHI, TRAINER_BLACK_BELT_KIYO,
     TRAINER_BLACK_BELT_TAKASHI, TRAINER_COOLTRAINER_SAMUEL, TRAINER_COOLTRAINER_YUJI, TRAINER_COOLTRAINER_WARREN,
     0xFFFF},
};

// A flag do treinador pode ter sido ligada pelo set_gym_trainers (Ginásio com a insígnia): não prova vitória.
static bool8 LigadoPeloGinasio(u16 treinador)
{
    u8 ginasio, i;

    for (ginasio = 0; ginasio < NUM_BADGES; ginasio++)
    {
        if (!FlagGet(FLAG_BADGE01_GET + ginasio))
            continue;
        for (i = 0; sTreinadoresDoGinasio[ginasio][i] != 0xFFFF; i++)
        {
            if (sTreinadoresDoGinasio[ginasio][i] == treinador)
                return TRUE;
        }
    }
    return FALSE;
}

static bool8 TemTodasInsignias(void)
{
    u16 flag;

    for (flag = FLAG_BADGE01_GET; flag <= FLAG_BADGE08_GET; flag++)
    {
        if (!FlagGet(flag))
            return FALSE;
    }
    return TRUE;
}

// Perde (ou marca) as conquistas ativas de tipo EVENTO com aquele `param`.
static void AplicarEvento(u8 evento, bool8 perder)
{
    u8 num;

    for (num = 0; num < CONQ_COUNT; num++)
    {
        if (!Ativa(num) || gConquistas[num].tipo != CONQ_TIPO_EVENTO || gConquistas[num].param != evento)
            continue;
        if (perder)
            Conquistas_Perder(num);
        else
            Conquistas_Marcar(num);
    }
}

// Contador das conquistas com degraus.
static u32 ContadorDosDegraus(u8 num)
{
    switch (gConquistas[num].tipo)
    {
    case CONQ_TIPO_HORAS:    return gSaveBlock2Ptr->playTimeHours;
    case CONQ_TIPO_VITORIAS: return sConq->vitoriasTreinador;
    case CONQ_TIPO_SHINIES:  return sConq->shiniesObtidos;
    }
    return 0;
}

u8 Conquistas_DegrauAtual(u8 num)
{
    const struct Conquista *c;
    u32 contador;
    u8 degrau;

    if (!Conquistas_NumValido(num) || gConquistas[num].numDegraus == 0)
        return 0;
    c = &gConquistas[num];
    contador = ContadorDosDegraus(num);
    for (degrau = 0; degrau < c->numDegraus && c->degraus[degrau] <= contador; degrau++)
        ;
    return degrau;
}

static bool8 CumpreFlag(const struct Conquista *c)
{
    return FlagGet(c->param);
}

static bool8 CumpreFlagsTodas(const struct Conquista *c)
{
    u16 i;

    for (i = 0; i < c->param2; i++)
    {
        if (!FlagGet(c->param + i))
            return FALSE;
    }
    return TRUE;
}

static u16 DexTodosCapturados(const struct Conquista *c, u16 *total)
{
    u16 i, capturados = 0;

    for (i = 0; c->lista[i] != 0xFFFF; i++)
    {
        if (GetSetPokedexFlag(SpeciesToNationalPokedexNum(c->lista[i]), FLAG_GET_CAUGHT))
            capturados++;
    }
    *total = i;
    return capturados;
}

static bool8 CumpreDexTodos(const struct Conquista *c)
{
    u16 total;

    return DexTodosCapturados(c, &total) == total;
}

static bool8 CumpreDexKanto(const struct Conquista *c)
{
    return GetKantoPokedexCount(FLAG_GET_CAUGHT) >= c->param;
}

static bool8 CumpreDexNacional(const struct Conquista *c)
{
    return GetNationalPokedexCount(FLAG_GET_CAUGHT) >= c->param;
}

static bool8 CumpreNivel(const struct Conquista *c, const struct ConqLeituraMons *mons)
{
    return mons->nivelMax >= c->param;
}

static bool8 CumpreAmizade(const struct Conquista *c, const struct ConqLeituraMons *mons)
{
    return mons->amizadeMax >= c->param;
}

static bool8 CumpreGameStat(const struct Conquista *c)
{
    return GetGameStat(c->param) >= c->param2;
}

static bool8 CumpreDinheiro(const struct Conquista *c)
{
    return GetMoney(&gSaveBlock1Ptr->money) >= c->param;
}

static bool8 CumpreDegraus(u8 num)
{
    return gConquistas[num].numDegraus > 0 && Conquistas_DegrauAtual(num) == gConquistas[num].numDegraus;
}

// `mons`: o time (na checagem cadenciada) ou o time e o PC (na varredura).
static bool8 CumpreEstado(u8 num, const struct ConqLeituraMons *mons)
{
    const struct Conquista *c = &gConquistas[num];

    switch (c->tipo)
    {
    case CONQ_TIPO_FLAG:         return CumpreFlag(c);
    case CONQ_TIPO_FLAGS_TODAS:  return CumpreFlagsTodas(c);
    case CONQ_TIPO_DEX_TODOS:    return CumpreDexTodos(c);
    case CONQ_TIPO_DEX_KANTO:    return CumpreDexKanto(c);
    case CONQ_TIPO_DEX_NACIONAL: return CumpreDexNacional(c);
    case CONQ_TIPO_NIVEL:        return CumpreNivel(c, mons);
    case CONQ_TIPO_AMIZADE_MAX:  return CumpreAmizade(c, mons);
    case CONQ_TIPO_GAME_STAT:    return CumpreGameStat(c);
    case CONQ_TIPO_DINHEIRO:     return CumpreDinheiro(c);
    case CONQ_TIPO_HORAS:
    case CONQ_TIPO_VITORIAS:
    case CONQ_TIPO_SHINIES:      return CumpreDegraus(num);
    }
    return FALSE; // CONQ_TIPO_EVENTO: só por gatilho (e, num save antigo, pela varredura)
}

void Conquistas_ChecarEstado(void)
{
    struct ConqLeituraMons time = {0};
    u8 num;

    if (sConq->magic != CONQ_MAGIC)
        Conquistas_VarrerSaveAntigo();
    LerTime(&time, GetPlayerTrainerId());
    for (num = 0; num < CONQ_COUNT; num++)
    {
        if (Ativa(num) && Conquistas_GetEstado(num) == CONQ_PENDENTE && CumpreEstado(num, &time))
            Conquistas_Marcar(num);
    }
    // depois da 8ª insígnia não há mais líder de Ginásio para vencer
    if (TemTodasInsignias())
        AplicarEvento(CONQ_EVT_LIDER_UM_POKEMON, TRUE);
}

// Uma vez por save sem marcador (a checagem só chega aqui com magic != CONQ_MAGIC). Contadores que o jogo nunca
// guardou começam do que o save prova; o diário de um save antigo começa vazio. O marcador do diário
// (`diario.versao`) também é gravado: as duas áreas saem daqui no mesmo formato de um jogo novo.
void Conquistas_VarrerSaveAntigo(void)
{
    struct ConqLeituraMons mons = {0};
    u16 vitorias = 0;
    u16 i;
    u8 num;

    memset(&gSaveBlock1Ptr->conquistas, 0, sizeof(gSaveBlock1Ptr->conquistas));
    memset(&gSaveBlock2Ptr->diario, 0, sizeof(gSaveBlock2Ptr->diario));
    sConq->magic = CONQ_MAGIC;
    sConq->versao = CONQ_VERSAO;
    sConq->origem = CONQ_ORIGEM_SAVE_ANTIGO;
    sConq->resumoPendente = TRUE;
    sConq->adiadoNoMapa = 0xFFFF;
    gSaveBlock2Ptr->diario.versao = CONQ_VERSAO;

    // vitórias: os treinadores com a flag de derrotado ligada (GAME_STAT_TRAINER_BATTLES conta batalhas iniciadas),
    // menos os de cada Ginásio já vencido, que o set_gym_trainers liga mesmo sem batalha (erra para menos)
    for (i = 1; i < NUM_TRAINERS; i++)
    {
        if (FlagGet(TRAINER_FLAGS_START + i) && !LigadoPeloGinasio(i))
            vitorias++;
    }
    sConq->vitoriasTreinador = vitorias;
    VarrerTimeEPC(&mons);
    sConq->shiniesObtidos = mons.shinies;

    for (num = 0; num < CONQ_COUNT; num++)
    {
        if (!Ativa(num))
            continue;
        if (gConquistas[num].tipo != CONQ_TIPO_EVENTO)
        {
            if (CumpreEstado(num, &mons))
                Conquistas_Marcar(num);
            continue;
        }
        switch (gConquistas[num].param)
        {
        case CONQ_EVT_ELITE4:
            if (FlagGet(FLAG_SYS_GAME_CLEAR))
                Conquistas_Marcar(num);
            break;
        case CONQ_EVT_OVO_SHINY:
            if (mons.ovoShiny)
                Conquistas_Marcar(num);
            break;
        case CONQ_EVT_OVO_6IVS:
            if (mons.ovo6Ivs)
                Conquistas_Marcar(num);
            break;
        }
    }

    // perdidas: só o que o save prova que passou. Qualquer batalha do rival já travada (vencida ou não) tira a
    // prova de "o rival nunca venceu"; com as 8 insígnias não há mais líder (Conquistas_ChecarEstado repete esta).
    for (i = 0; i < DIARIO_EVT_COUNT; i++)
    {
        const u16 *t = gDiarioEventos[i].treinadores;

        if (!gDiarioEventos[i].rival || t == NULL)
            continue;
        for (; *t != 0xFFFF; t++)
        {
            if (FlagGet(TRAINER_FLAGS_START + *t))
                AplicarEvento(CONQ_EVT_RIVAL_TODAS, TRUE);
        }
    }
    if (TemTodasInsignias())
        AplicarEvento(CONQ_EVT_LIDER_UM_POKEMON, TRUE);
}

bool8 Conquistas_Progresso(u8 num, u32 *atual, u32 *meta)
{
    const struct Conquista *c;
    u16 total;
    u8 degrau;

    if (!Conquistas_NumValido(num))
        return FALSE;
    c = &gConquistas[num];
    if (c->numDegraus > 0)
    {
        degrau = Conquistas_DegrauAtual(num);
        *atual = ContadorDosDegraus(num);
        *meta = c->degraus[degrau < c->numDegraus ? degrau : c->numDegraus - 1];
        return TRUE;
    }
    switch (c->tipo)
    {
    case CONQ_TIPO_FLAGS_TODAS:
        *atual = 0;
        for (total = 0; total < c->param2; total++)
            *atual += FlagGet(c->param + total);
        *meta = c->param2;
        return TRUE;
    case CONQ_TIPO_DEX_TODOS:
        *atual = DexTodosCapturados(c, &total);
        *meta = total;
        return total > 1;
    case CONQ_TIPO_DEX_KANTO:
        *atual = GetKantoPokedexCount(FLAG_GET_CAUGHT);
        *meta = c->param;
        return TRUE;
    case CONQ_TIPO_DEX_NACIONAL:
        *atual = GetNationalPokedexCount(FLAG_GET_CAUGHT);
        *meta = c->param;
        return TRUE;
    case CONQ_TIPO_GAME_STAT:
        *atual = GetGameStat(c->param);
        *meta = c->param2;
        return c->param2 > 1;
    }
    return FALSE; // sim/não: FLAG, EVENTO, NIVEL, AMIZADE_MAX, DINHEIRO, DEX_TODOS de uma espécie, GAME_STAT de 1
}

u8 Conquistas_AvisosPendentes(void)
{
    u32 avisos = 0;
    u8 num, atual, entregue;

    if (sConq->magic != CONQ_MAGIC)
        return 0;
    if (sConq->resumoPendente)
        return 1; // um aviso só, o resumo, entrega tudo o que a varredura achou
    for (num = 0; num < CONQ_COUNT; num++)
    {
        if (!Ativa(num))
            continue;
        if (gConquistas[num].numDegraus > 0)
        {
            atual = Conquistas_DegrauAtual(num);
            entregue = Conquistas_DegrauEntregue(num);
            if (atual > entregue)
                avisos += atual - entregue;
        }
        else if (Conquistas_GetEstado(num) == CONQ_FEITA && !Conquistas_Entregue(num))
        {
            avisos++;
        }
    }
    return avisos > 0xFF ? 0xFF : avisos;
}

void Conquistas_ContarAba(u8 aba, u8 *feitas, u8 *validas)
{
    u8 num, estado;

    *feitas = 0;
    *validas = 0;
    for (num = 0; num < CONQ_COUNT; num++)
    {
        if (!Ativa(num) || gConquistas[num].aba != aba)
            continue;
        estado = Conquistas_GetEstado(num);
        if (estado == CONQ_PERDIDA)
            continue;
        (*validas)++;
        if (estado == CONQ_FEITA)
            (*feitas)++;
    }
}

// --- Gatilhos de evento (Task 4) ----------------------------------------------------------------------------
// Os ganchos de uma linha no motor (battle_main.c, battle_script_commands.c, pokemon.c, daycare.c) chegam aqui.
// Num save ainda sem marcador eles não fazem nada: a varredura do save antigo (que a checagem cadenciada roda logo
// depois de carregar) reconhece o que o save prova, e assim nada conta duas vezes nem some no memset dela.

void Conquistas_Evento(u8 evento)
{
    AplicarEvento(evento, FALSE);
}

void Conquistas_PerderEvento(u8 evento)
{
    AplicarEvento(evento, TRUE);
}

static bool8 ComMarcador(void)
{
    return sConq->magic == CONQ_MAGIC;
}

// Batalhas que não são do jogador nesta jornada (o FRLG não tem BATTLE_TYPE_RECORDED, que é do Emerald).
static bool8 BatalhaIgnorada(void)
{
    return (gBattleTypeFlags & (BATTLE_TYPE_LINK | BATTLE_TYPE_POKEDUDE | BATTLE_TYPE_OLD_MAN_TUTORIAL
                              | BATTLE_TYPE_TRAINER_TOWER | BATTLE_TYPE_EREADER_TRAINER | BATTLE_TYPE_BATTLE_TOWER)) != 0;
}

static bool8 TreinadorDoEvento(u8 evt, u16 treinador)
{
    const u16 *t = gDiarioEventos[evt].treinadores;

    if (t == NULL)
        return FALSE;
    for (; *t != 0xFFFF; t++)
    {
        if (*t == treinador)
            return TRUE;
    }
    return FALSE;
}

// O treinador é um líder (lider = TRUE) ou o rival (lider = FALSE) de algum evento do diário.
static bool8 TreinadorMarcante(u16 treinador, bool8 lider)
{
    u8 evt;

    for (evt = 0; evt < DIARIO_EVT_COUNT; evt++)
    {
        if ((lider ? gDiarioEventos[evt].lider : gDiarioEventos[evt].rival) && TreinadorDoEvento(evt, treinador))
            return TRUE;
    }
    return FALSE;
}

// Pokémon no time, sem contar ovos.
static u8 TimeSemOvos(void)
{
    u8 i, n = 0;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE
         && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
            n++;
    }
    return n;
}

void Conquistas_OnNocaute(u8 battlerAtacante)
{
    u32 personalidade;
    u8 i;

    if (GetBattlerSide(battlerAtacante) != B_SIDE_PLAYER || BatalhaIgnorada()
     // o golpe tardio acerta turnos depois: gBattlerAttacker é a posição, e o Pokémon ali pode ser outro
     || gCurrentMove == MOVE_FUTURE_SIGHT || gCurrentMove == MOVE_DOOM_DESIRE)
        return;
    personalidade = GetMonData(&gPlayerParty[gBattlerPartyIndexes[battlerAtacante]], MON_DATA_PERSONALITY);
    // vaga com nocautes = vaga usada; a primeira livre ou a do mesmo Pokémon recebe o nocaute
    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (gBattleStruct->conqNocautes[i] == 0 || gBattleStruct->conqPersonalidade[i] == personalidade)
        {
            gBattleStruct->conqPersonalidade[i] = personalidade;
            if (gBattleStruct->conqNocautes[i] < 0xFF)
                gBattleStruct->conqNocautes[i]++;
            return;
        }
    }
}

// Golpes cujo dano não depende do tipo (dano fixo, metade do HP, OHKO): passam pelo typecalc (o OHKO antes de
// acertar), mas o script descarta a eficácia. ×4 neles não é "acertar um golpe ×4".
static bool8 DanoSemTipo(u16 move)
{
    switch (gBattleMoves[move].effect)
    {
    case EFFECT_LEVEL_DAMAGE:
    case EFFECT_DRAGON_RAGE:
    case EFFECT_SONICBOOM:
    case EFFECT_SUPER_FANG:
    case EFFECT_PSYWAVE:
    case EFFECT_OHKO:
    case EFFECT_ENDEAVOR:
        return TRUE;
    }
    return FALSE;
}

void Conquistas_OnEficacia(u8 battlerAtacante, u16 multX10)
{
    if (!ComMarcador() || GetBattlerSide(battlerAtacante) != B_SIDE_PLAYER || BatalhaIgnorada()
     || DanoSemTipo(gCurrentMove))
        return;
    if (multX10 == 40 && gBattleMoves[gCurrentMove].power > 0 && !(gMoveResultFlags & MOVE_RESULT_NO_EFFECT))
        Conquistas_Evento(CONQ_EVT_GOLPE_X4);
}

// Roda no fim da batalha, antes de voltar ao campo: o script do Ginásio só liga a insígnia (setflag) depois. Por
// isso "líder com um Pokémon só" já está feita quando a 8ª insígnia faz a checagem perder a pendente.
void Conquistas_OnFimDeBatalha(void)
{
    u16 treinador = gTrainerBattleOpponent_A;

    if (BatalhaIgnorada())
        return;
    if (ComMarcador() && (gBattleTypeFlags & BATTLE_TYPE_TRAINER))
    {
        if (gBattleOutcome == B_OUTCOME_WON)
        {
            if (sConq->vitoriasTreinador < 0xFFFF)
                sConq->vitoriasTreinador++;
            if (gBattleResults.playerFaintCounter == 0)
                Conquistas_Evento(CONQ_EVT_SEM_DESMAIO);
            if (TreinadorMarcante(treinador, TRUE) && TimeSemOvos() == 1)
                Conquistas_Evento(CONQ_EVT_LIDER_UM_POKEMON);
            if (TreinadorDoEvento(DIARIO_EVT_LANCE, treinador))
                Conquistas_Evento(CONQ_EVT_ELITE4);
            if (TreinadorDoEvento(DIARIO_EVT_CAMPEAO, treinador))
                Conquistas_Evento(CONQ_EVT_RIVAL_TODAS);
        }
        else if (TreinadorMarcante(treinador, FALSE))
        {
            Conquistas_PerderEvento(CONQ_EVT_RIVAL_TODAS);
        }
    }
    Diario_OnFimDeBatalha();
}

void Conquistas_OnCaptura(struct Pokemon *mon, u16 bola)
{
    u16 especie = GetMonData(mon, MON_DATA_SPECIES);

    if (!ComMarcador() || BatalhaIgnorada())
        return;
    // o shiny capturado soma no GiveMonToPlayer (Conquistas_OnPokemonRecebido), não aqui
    if (bola == ITEM_POKE_BALL && gSpeciesInfo[especie].catchRate <= CONQ_TAXA_DIFICIL)
        Conquistas_Evento(CONQ_EVT_POKE_BALL_DIFICIL);
}

void Conquistas_OnPokemonRecebido(struct Pokemon *mon)
{
    if (!ComMarcador() || GetMonData(mon, MON_DATA_IS_EGG))
        return;
    if (IsMonShiny(mon) && sConq->shiniesObtidos < 0xFFFF)
        sConq->shiniesObtidos++;
}

void Conquistas_OnOvoChocado(struct Pokemon *mon)
{
    u32 campo;
    bool8 ivs31 = TRUE;

    if (!ComMarcador())
        return;
    if (IsMonShiny(mon))
    {
        if (sConq->shiniesObtidos < 0xFFFF)
            sConq->shiniesObtidos++;
        Conquistas_Evento(CONQ_EVT_OVO_SHINY);
    }
    for (campo = MON_DATA_HP_IV; campo <= MON_DATA_SPDEF_IV; campo++)
    {
        if (GetMonData(mon, campo) != MAX_PER_STAT_IVS)
            ivs31 = FALSE;
    }
    if (ivs31)
        Conquistas_Evento(CONQ_EVT_OVO_6IVS);
}

// Stub até a Task 5 (src/diario.c).
void Diario_OnFimDeBatalha(void)
{
}
