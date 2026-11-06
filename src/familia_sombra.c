#include "global.h"
#include "battle.h"
#include "battle_message.h"
#include "battle_setup.h"
#include "day_night.h"
#include "event_data.h"
#include "field_specials.h"
#include "familia_sombra.h"
#include "pokemon.h"
#include "random.h"
#include "constants/event_objects.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/maps.h"
#include "constants/moves.h"
#include "constants/opponents.h"
#include "constants/rgb.h"
#include "constants/species.h"
#include "constants/trainers.h"
#include "constants/vars.h"
#include "data/familia_sombra_times.h"
#include "data/familia_sombra_noir.h"

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

    if (!FamiliaSombra_ChefeAtivo())   // chamada repetida não regrava a queda
        return;
    VarSet(VAR_FAMILIA_QUEDA, FamiliaSombra_MeiosDiasAgora());
    VarSet(VAR_FAMILIA_ESTADO, FAMILIA_ESTADO_SEM_CHEFE);
    if (ocupacao >= 1 && ocupacao <= FAMILIA_OCUPACOES_TOTAL)
        FlagSet(sRosas[ocupacao - 1]);
}

// Os 6 andares do prédio (o térreo é o antigo Route23_UnusedHouse).
static const u16 sAndares[] =
{
    MAP_ROUTE23_UNUSED_HOUSE,
    MAP_ROUTE23_FAMILIA_SOMBRA_2F,
    MAP_ROUTE23_FAMILIA_SOMBRA_3F,
    MAP_ROUTE23_FAMILIA_SOMBRA_4F,
    MAP_ROUTE23_FAMILIA_SOMBRA_5F,
    MAP_ROUTE23_FAMILIA_SOMBRA_6F,
};

static u16 MapaAtual(void)
{
    return (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
}

bool8 FamiliaSombra_NoPredio(void)
{
    u16 mapa = MapaAtual();
    s32 i;

    for (i = 0; i < (s32)ARRAY_COUNT(sAndares); i++)
    {
        if (sAndares[i] == mapa)
            return TRUE;
    }
    return FALSE;
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

// Batalha contra um capanga da Família: treinador da classe FAMILIA_SOMBRA (andares 1-3, gêmeos, pedágio) ou o
// encontro dos andares 4-5 (BATTLE_TYPE_FAMILIA). O chefe não entra (BATTLE_TYPE_FAMILIA_CHEFE): ele pode ser
// capturado e luta com as cores shiny, sem o filme.
bool8 FamiliaSombra_EhBatalhaDaFamilia(void)
{
    if (gBattleTypeFlags & (BATTLE_TYPE_LINK | BATTLE_TYPE_BATTLE_TOWER | BATTLE_TYPE_TRAINER_TOWER | BATTLE_TYPE_EREADER_TRAINER))
        return FALSE;
    if (gBattleTypeFlags & BATTLE_TYPE_FAMILIA)
        return TRUE;
    if (!(gBattleTypeFlags & BATTLE_TYPE_TRAINER) || gTrainerBattleOpponent_A >= NUM_TRAINERS)
        return FALSE;
    return gTrainers[gTrainerBattleOpponent_A].trainerClass == TRAINER_CLASS_FAMILIA_SOMBRA;
}

// A batalha contra o chefe da ocupação (FamiliaSombra_IniciarChefe). O diário (Task 7) usa para marcar a luta.
bool8 FamiliaSombra_EhChefe(void)
{
    return (gBattleTypeFlags & BATTLE_TYPE_FAMILIA_CHEFE) && !(gBattleTypeFlags & BATTLE_TYPE_LINK);
}

// O item que fortalece o membro da Família não vai para o jogador (Ladrão, Cobiça e Truque falham): capangas,
// encontros dos andares 4-5 e o chefe (o item fixo dele faz parte do chefe; capturado, ele vem junto).
bool8 FamiliaSombra_ItemProtegido(void)
{
    return FamiliaSombra_EhBatalhaDaFamilia() || FamiliaSombra_EhChefe();
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

// Special: as 2 lutas do pedágio foram vencidas, a passagem vale até sair do mapa da Rota 23.
void FamiliaSombra_PedagioVencido(void)
{
    FlagSet(FLAG_FAMILIA_PEDAGIO_PAGO);
}

// ---- Andares 4-5, efeito de filme e o chefe (Task 4) ----------------------------------------------------------

// Os andares escuros (4º e 5º), onde andar dá encontro com a Família; a lista acaba em FAMILIA_SEM_MAPA.
#define FAMILIA_SEM_MAPA 0xFFFF
static const u16 sAndaresEscuros[] =
{
    MAP_ROUTE23_FAMILIA_SOMBRA_4F,
    MAP_ROUTE23_FAMILIA_SOMBRA_5F,
    FAMILIA_SEM_MAPA,
};

#if TESTBUILD
EWRAM_DATA bool8 gTestFamiliaAndarEscuro = FALSE; // atalho TEST_CMD_FAMILIA_PASSOS: o mapa atual vale como andar escuro
#endif

bool8 FamiliaSombra_EhAndarEscuro(void)
{
    u16 mapa = MapaAtual();
    s32 i;

#if TESTBUILD
    if (gTestFamiliaAndarEscuro)
        return TRUE;
#endif
    for (i = 0; sAndaresEscuros[i] != FAMILIA_SEM_MAPA; i++)
    {
        if (sAndaresEscuros[i] == mapa)
            return TRUE;
    }
    return FALSE;
}

// Nível do próximo encontro dos andares 4-5: 54-58 na ocupação 1, +6 por ocupação.
u8 FamiliaSombra_NivelSelvagem(void)
{
    return FAMILIA_NIVEL_ANDAR_MIN + Random() % (FAMILIA_NIVEL_ANDAR_MAX - FAMILIA_NIVEL_ANDAR_MIN + 1)
         + (OcupacaoDasLutas() - 1) * FAMILIA_NIVEL_PASSO;
}

// O encontro dos andares 4-5 em gEnemyParty[0]: um membro do plantel da ocupação, com o item e os golpes dele.
void FamiliaSombra_CriarSelvagem(u8 level)
{
    u8 ocupacao = OcupacaoDasLutas();

    ZeroEnemyPartyMons();
    CriarMembro(&gEnemyParty[0], &sFamiliaPlantel[ocupacao - 1][Random() % FAMILIA_PLANTEL], level);
}

// Efeito de filme antigo (a função noir() da prévia aprovada, tabelada em src/data/familia_sombra_noir.h pela soma
// que dá a luminância). O índice 0 da paleta (transparente) fica como está.
void FamiliaSombra_PaletaNoir(u16 *pal, u16 count)
{
    u16 i, cor;

    for (i = 1; i < count; i++)
    {
        cor = pal[i];
        pal[i] = sFamiliaNoir[30 * GET_R(cor) + 59 * GET_G(cor) + 11 * GET_B(cor)];
    }
}

// A abertura da batalha do chefe: "GENGAR, O DOM, quer acertar as contas!" (o título da ocupação em destaque).
const u8 *FamiliaSombra_TextoDoChefe(void)
{
    return gText_FamiliaChefeQuerAcertar[OcupacaoDasLutas() - 1];
}

// Special: o chefe da ocupação em gEnemyParty[0] e a batalha contra ele (lendária, MUS_VS_LEGEND). Sempre shiny pela
// receita do SetLeadShiny (test_hooks.c): o jogador é o OT e a metade alta da personalidade anula o valor shiny;
// a metade baixa sai ao acaso (natureza e gênero). IVs no máximo, golpes e item fixos de sFamiliaChefes.
void FamiliaSombra_IniciarChefe(void)
{
    const struct FamiliaMembro *chefe = &sFamiliaChefes[OcupacaoDasLutas() - 1];
    struct Pokemon *mon = &gEnemyParty[0];
    u32 otId = GetPlayerTrainerId();
    u16 baixa = Random();
    u32 personality;
    s32 i;

    personality = (((otId >> 16) ^ (otId & 0xFFFF) ^ baixa) & 0xFFFF) << 16 | baixa;
    ZeroEnemyPartyMons();
    CreateMon(mon, chefe->species, chefe->level, MAX_PER_STAT_IVS, TRUE, personality, OT_ID_PLAYER_ID, 0);
    for (i = 0; i < MAX_MON_MOVES; i++)
        SetMonMoveSlot(mon, chefe->moves[i], i);
    SetMonData(mon, MON_DATA_HELD_ITEM, &chefe->heldItem);
    StartFamiliaChefeBattle();
}

// ---- O prédio (Task 5) ----------------------------------------------------------------------------------------

// O gráfico de chapéu de cada espécie que aparece no mapa (capangas dos andares 1-3, gêmeos e chefes).
static const u16 sGfxDaEspecie[][2] =
{
    {SPECIES_HAUNTER,    OBJ_EVENT_GFX_FAMILIA_HAUNTER},
    {SPECIES_MISDREAVUS, OBJ_EVENT_GFX_FAMILIA_MISDREAVUS},
    {SPECIES_SABLEYE,    OBJ_EVENT_GFX_FAMILIA_SABLEYE},
    {SPECIES_BANETTE,    OBJ_EVENT_GFX_FAMILIA_BANETTE},
    {SPECIES_HOUNDOUR,   OBJ_EVENT_GFX_FAMILIA_HOUNDOUR},
    {SPECIES_HOUNDOOM,   OBJ_EVENT_GFX_FAMILIA_HOUNDOOM},
    {SPECIES_MURKROW,    OBJ_EVENT_GFX_FAMILIA_MURKROW},
    {SPECIES_SNEASEL,    OBJ_EVENT_GFX_FAMILIA_SNEASEL},
    {SPECIES_CROBAT,     OBJ_EVENT_GFX_FAMILIA_CROBAT},
    {SPECIES_MUK,        OBJ_EVENT_GFX_FAMILIA_MUK},
    {SPECIES_WEEZING,    OBJ_EVENT_GFX_FAMILIA_WEEZING},
    {SPECIES_ARBOK,      OBJ_EVENT_GFX_FAMILIA_ARBOK},
    {SPECIES_MIGHTYENA,  OBJ_EVENT_GFX_FAMILIA_MIGHTYENA},
    {SPECIES_ABSOL,      OBJ_EVENT_GFX_FAMILIA_ABSOL},
    {SPECIES_CACTURNE,   OBJ_EVENT_GFX_FAMILIA_CACTURNE},
    {SPECIES_SHIFTRY,    OBJ_EVENT_GFX_FAMILIA_SHIFTRY},
    {SPECIES_CRAWDAUNT,  OBJ_EVENT_GFX_FAMILIA_CRAWDAUNT},
    {SPECIES_GOLEM,      OBJ_EVENT_GFX_FAMILIA_GOLEM},
    {SPECIES_MACHAMP,    OBJ_EVENT_GFX_FAMILIA_MACHAMP},
    {SPECIES_RHYDON,     OBJ_EVENT_GFX_FAMILIA_RHYDON},
    {SPECIES_GENGAR,     OBJ_EVENT_GFX_FAMILIA_GENGAR_SHINY},
    {SPECIES_TYRANITAR,  OBJ_EVENT_GFX_FAMILIA_TYRANITAR_SHINY},
};

// Espécie sem gráfico de chapéu (só a parte 2: Garchomp, Gligar, Darkrai, Dusclops) cai no Gengar / Machamp.
static u16 GfxDaEspecie(u16 species, u16 reserva)
{
    s32 i;

    for (i = 0; i < (s32)ARRAY_COUNT(sGfxDaEspecie); i++)
    {
        if (sGfxDaEspecie[i][0] == species)
            return sGfxDaEspecie[i][1];
    }
    return reserva;
}

// Special, no on_transition de cada andar (VAR_0x8004 = andar, 1 a 6). Os gráficos da ocupação vão para
// VAR_OBJ_GFX_ID_0..2: nos andares 1-3, os 3 capangas do andar (slots 3n-2..3n, paletas PALSLOT_NPC_1..3); no 6º, o
// chefe (0) e os gêmeos (1). Sem chefe ativo o prédio fica vazio, só com os bilhetes: capangas, gêmeos e itens do
// chão ficam marcados como vencidos/pegos (FamiliaSombra_Repovoar desmarca tudo na próxima ocupação).
void FamiliaSombra_PrepararAndar(void)
{
    u8 andar = gSpecialVar_0x8004;
    u8 ocupacao = OcupacaoDasLutas();
    u16 flag;
    s32 i;

    if (andar >= 1 && andar <= 3)
    {
        for (i = 0; i < 3; i++)
            VarSet(VAR_OBJ_GFX_ID_0 + i,
                   GfxDaEspecie(sFamiliaCapangas[ocupacao - 1][(andar - 1) * 3 + i].species, OBJ_EVENT_GFX_FAMILIA_MUK));
    }
    else if (andar == 6)
    {
        VarSet(VAR_OBJ_GFX_ID_0, GfxDaEspecie(sFamiliaChefes[ocupacao - 1].species, OBJ_EVENT_GFX_FAMILIA_GENGAR_SHINY));
        VarSet(VAR_OBJ_GFX_ID_1, GfxDaEspecie(sFamiliaGemeos[ocupacao - 1][0].species, OBJ_EVENT_GFX_FAMILIA_MACHAMP));
    }
    if (FamiliaSombra_ChefeAtivo())
        return;
    FlagSet(FLAG_FAMILIA_GEMEOS_VENCIDOS);
    for (flag = FLAG_FAMILIA_ITENS_PRIMEIRA; flag <= FLAG_FAMILIA_ITENS_ULTIMA; flag++)
        FlagSet(flag);
    for (flag = TRAINER_FAMILIA_CAPANGA_1; flag <= TRAINER_FAMILIA_GEMEOS; flag++)
        FlagSet(TRAINER_FLAGS_START + flag);
}
