#include "global.h"
#include "gflib.h"
#include "data.h"
#include "day_night.h"
#include "dexnav.h"
#include "help_system.h"
#include "menu.h"
#include "menu_helpers.h"
#include "new_menu_helpers.h"
#include "overworld.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_icon.h"
#include "quest_log.h"
#include "scanline_effect.h"
#include "script.h"
#include "strings.h"
#include "task.h"
#include "constants/songs.h"

// DexNav (POK-47), a tela (Task 2: o modo mapa, layout A aprovado pelo Cintra; a Task 3 acrescenta a lista de mapas e
// a busca como outros modos deste mesmo arquivo). Desenho em docs/superpowers/specs/2026-10-31-dexnav-design.md.
//
// Topo: nome do mapa, período do dia (o nome do relógio: Manhã, Tarde, Entardecer, Noite) e "capturados/total" do mapa
// (todas as espécies, em qualquer horário), que vira "100%" com a coroa no mapa completo. Abas por jeito de encontrar
// (GRAMA, SURFAR, VARAS, PEDRA; só as que o mapa tem; L/R dão a volta), com a coroa na aba completa. Lista da aba: os
// Pokémon do período de agora, por chance (maior primeiro), cada linha com o ícone (silhueta se nunca visto), a marca
// (capturado, visto, nunca visto), o nome ("??????" se nunca visto), a chance e a faixa de nível, em colunas fixas
// (COL_*: o mesmo x em todas as linhas; números alinhados à direita pela largura medida). VARAS tem uma seção por vara.
// No fim da aba, "+N à noite" (ou de dia, de manhã...) quando outro período tem espécies que não aparecem agora.
// ▲▼ movem a seleção (a lista rola), B sai.
//
// A tarde-noite (TIME_EVENING) vale como tarde e noite ao mesmo tempo (DexNav_CurrentPeriodBit devolve os 2 bits): a
// lista mostra as espécies das duas tabelas e a chance é a média (DexNav_RateForPeriods), como o encontro real.
//
// Memória: o estado num bloco AllocZeroed (sDexNav é o único EWRAM novo: EWRAM ~99,6%), liberado na saída. A ajuda do
// jogo (que também escuta L/R) fica desligada enquanto a tela está aberta.

// Janelas, todas no BG0 (bloco de caracteres 0, tilemap no bloco 31), uma faixa de tiles depois da outra:
//   linhas 0-1    WIN_TOPO    nome do mapa, período e contador (ou "100%") com a coroa
//   linhas 2-3    WIN_ABAS    as abas do mapa
//   linhas 4-17   WIN_LISTA   LISTA_ALTURA px de linhas
//   linhas 18-19  WIN_RODAPE  os botões
#define TELA_TILES_X        (DISPLAY_WIDTH / 8)
#define TOPO_TILES          2
#define ABAS_TILES          2
#define RODAPE_TILES        2
#define LISTA_TOPO_TILES    (TOPO_TILES + ABAS_TILES)
#define LISTA_ALTURA        112
#define RODAPE_TOPO_TILES   (LISTA_TOPO_TILES + LISTA_ALTURA / 8)
STATIC_ASSERT(RODAPE_TOPO_TILES + RODAPE_TILES == DISPLAY_HEIGHT / 8, DexNavOcupaATela);

// Linhas da lista: Pokémon (com o ícone de 32x32, centrado na linha), título de seção (VARAS) e a linha extra ("+N").
// A lista rola quando passa de ICONES_MAX Pokémon: cada linha visível tem o seu sprite.
#define LINHA_MON_ALTURA    24
#define LINHA_SECAO_ALTURA  16
#define LINHA_EXTRA_ALTURA  16
#define ICONES_MAX          4
STATIC_ASSERT(ICONES_MAX * LINHA_MON_ALTURA <= LISTA_ALTURA && (ICONES_MAX + 1) * LINHA_MON_ALTURA > LISTA_ALTURA,
              DexNavIconesVisiveis);

// Colunas da linha de Pokémon, em px na janela da lista (240 px), as mesmas em todas as linhas (pedido do Cintra):
//   ícone (sprite 32x32 de COL_ICONE_X a +32), marca (8x8), nome (até COL_NOME_LARGURA: a espécie mais larga mede 60),
//   chance alinhada à direita até COL_CHANCE_FIM (até COL_CHANCE_LARGURA: "99,5%" mede 31), "Nv." em COL_NIVEL_X, o
//   nível mínimo alinhado à direita até COL_NIVEL_MIN_FIM, o traço em COL_NIVEL_TRACO_X e o máximo alinhado à esquerda
//   em COL_NIVEL_MAX_X: "3 - 4" e "25 - 35" com o traço na mesma coluna e o mesmo respiro dos dois lados (nível único:
//   só o mínimo, na coluna dele). As setas de rolagem ficam em COL_SETA_X.
// test/tests/test_dexnav_tela.py::test_colunas_fixas confere que nenhuma coluna encosta na outra no pior caso.
#define COL_ICONE_X         0
#define COL_MARCA_X         32
#define COL_NOME_X          44
#define COL_NOME_LARGURA    64
#define COL_CHANCE_FIM      150
#define COL_CHANCE_LARGURA  32
#define COL_NIVEL_X         160
#define COL_NIVEL_MIN_FIM   196
#define COL_NIVEL_TRACO_X   199
#define COL_NIVEL_MAX_X     208
#define COL_NIVEL_MAX_LARGURA 18  // "100"
#define COL_SETA_X          228
STATIC_ASSERT(COL_NOME_X + COL_NOME_LARGURA + 4 <= COL_CHANCE_FIM - COL_CHANCE_LARGURA, DexNavNomeAntesDaChance);
STATIC_ASSERT(COL_NIVEL_MAX_X + COL_NIVEL_MAX_LARGURA <= COL_SETA_X, DexNavNivelAntesDasSetas);

// Posições verticais dentro de cada linha (o texto FONT_NORMAL ocupa ~14 px)
#define LINHA_TEXTO_DY      5   // texto da linha de Pokémon (24 px)
#define LINHA_MARCA_DY      8   // marca 8x8 no meio da linha de Pokémon
#define LINHA_ICONE_DY      10  // centro do ícone (o desenho do Pokémon fica na parte de baixo dos 32x32)
#define LINHA_CURTA_TEXTO_DY 1  // texto das linhas de 16 px (seção e extra)
#define SECAO_X             4   // título da seção (VARAS), com um fio até SELECAO_FIM
#define SELECAO_X           0   // fundo amarelo da linha selecionada
#define SELECAO_FIM         228

// Topo (barra azul): nome do mapa em TOPO_NOME_X (até DEXNAV_NAME_WIDTH), período em TOPO_PERIODO_X (até
// TOPO_PERIODO_LARGURA: "Entardecer" mede 56), contador alinhado à direita até TOPO_CONTADOR_FIM e a coroa em TOPO_COROA_X.
#define TOPO_TEXTO_Y            1
#define TOPO_NOME_X             4
#define TOPO_PERIODO_X          130
#define TOPO_PERIODO_LARGURA    56
#define TOPO_CONTADOR_FIM       222
#define TOPO_COROA_X            226
#define TOPO_COROA_Y            4
STATIC_ASSERT(TOPO_NOME_X + DEXNAV_NAME_WIDTH + 4 <= TOPO_PERIODO_X, DexNavNomeDoMapaAntesDoPeriodo);

// Abas: vagas fixas de ABA_LARGURA px a cada ABA_PASSO, a partir de ABA_X0 (as que o mapa tem, na ordem GRAMA, SURFAR,
// VARAS, PEDRA); o rótulo em +ABA_TEXTO_DX e a coroa da aba completa em +ABA_COROA_DX.
#define ABA_X0              4
#define ABA_PASSO           58
#define ABA_LARGURA         54
#define ABA_TEXTO_DX        4
#define ABA_COROA_DX        44
#define ABA_TEXTO_Y         1
#define ABA_COROA_Y         4
STATIC_ASSERT(ABA_X0 + (DEXNAV_TAB_COUNT - 1) * ABA_PASSO + ABA_LARGURA <= DISPLAY_WIDTH, DexNavAbasCabem);

#define RODAPE_X            4
#define RODAPE_Y            1

enum {
    WIN_TOPO,
    WIN_ABAS,
    WIN_LISTA,
    WIN_RODAPE,
    WIN_COUNT
};

#define WIN_TOPO_BASE    1
#define WIN_ABAS_BASE    (WIN_TOPO_BASE + TELA_TILES_X * TOPO_TILES)
#define WIN_LISTA_BASE   (WIN_ABAS_BASE + TELA_TILES_X * ABAS_TILES)
#define WIN_RODAPE_BASE  (WIN_LISTA_BASE + TELA_TILES_X * LISTA_ALTURA / 8)
#define WINS_FIM         (WIN_RODAPE_BASE + TELA_TILES_X * RODAPE_TILES)
STATIC_ASSERT(WINS_FIM * TILE_SIZE_4BPP <= 31 * BG_SCREEN_SIZE, DexNavJanelasAntesDoTilemap);

// Ícones de graphics/dexnav/icones.png (8x8 cada, lado a lado); a paleta é a da tela inteira (icones.pal).
enum {
    ICONE_CAPTURADO,
    ICONE_VISTO,
    ICONE_NUNCA_VISTO,
    ICONE_COROA,
    ICONE_COUNT
};

// Cores de graphics/dexnav/icones.pal
#define COR_FUNDO        0
#define COR_BRANCO       1
#define COR_TEXTO        2
#define COR_SOMBRA       3
#define COR_BARRA        7
#define COR_SOMBRA_BARRA 8
#define COR_SELECAO      9
#define COR_FAIXA_ABAS   10
#define COR_ABA          11
#define COR_DIVISOR      12
#define COR_CINZA        13
#define COR_SECAO        14
#define COR_SOMBRA_ABA   15

// Ícone de Pokémon nunca visto: a paleta toda escura (a cor 0 continua transparente)
#define TAG_SILHUETA     0x4E44
#define COR_SILHUETA     RGB(5, 5, 7)
#define ICONE_NENHUM     SPRITE_NONE

enum {
    LINHA_MON,      // idx = índice em entries
    LINHA_SECAO,    // idx = DEXNAV_METHOD_* (uma vara)
    LINHA_EXTRA,    // "+N à noite"
    LINHA_VAZIA,    // "Nenhum agora": a aba não tem Pokémon no período de agora (vem antes da linha extra)
};

#define LINHAS_MAX (DEXNAV_MAX_ENTRIES + 3 + 1)   // Pokémon, os títulos das 3 varas e a linha extra (ou vazia + extra)
#define LINHA_NENHUMA 0xFF

enum {
    FASE_ESPERA,    // criada no DexNav_Open, até o CB2 montar a tela
    FASE_MONTAR,
    FASE_INPUT,
    FASE_SAIR,
};

struct DexNavLinha
{
    u8 tipo;        // LINHA_*
    u8 idx;
};

struct DexNavTela
{
    MainCallback voltar;
    u8 modo;            // DEXNAV_MODE_*
    u8 fase;
    u8 passo;           // passo da montagem
    u8 inputReady;
    u8 ajudaAntes;      // gHelpSystemEnabled de antes da tela (volta a ele na saída)
    u8 mapIndex;        // em gDexNavMaps
    u8 periods;         // DexNav_CurrentPeriodBit() ao abrir (a tarde-noite tem 2 bits)
    u8 period;          // DayNight_GetPeriod() ao abrir (o nome no topo)
    u8 nEntries;
    u8 abasMask;        // bit por DEXNAV_TAB_* que o mapa tem
    u8 nAbas;
    u8 abas[DEXNAV_TAB_COUNT];  // as abas do mapa, em ordem
    u8 abaPos;          // a aba atual (posição em abas)
    u8 nLinhas;
    u8 nMons;           // linhas de Pokémon da aba
    u8 cursor;          // linha (em linhas) do Pokémon selecionado
    u8 topo;            // primeira linha visível
    u8 extraN;          // espécies da aba que não aparecem agora (a linha "+N")
    u8 extraPeriods;    // períodos em que elas aparecem
    u8 capturadosMapa;
    u8 totalMapa;
    u8 capturadosAba;
    u8 totalAba;
    u8 icones[ICONES_MAX];  // sprites dos ícones visíveis (ICONE_NENHUM = vago)
    struct DexNavLinha linhas[LINHAS_MAX];
    struct DexNavEntry entries[DEXNAV_MAX_ENTRIES];
};

static EWRAM_DATA struct DexNavTela *sDexNav = NULL;

static void AbrirTela(MainCallback voltar, u8 modo, u8 mapIndex);
static void CB2_DexNav_Montar(void);
static void VBlankCB_DexNav(void);
static void Task_DexNav(u8 taskId);
static void Task_DexNav_Montar(u8 taskId);
static void Task_DexNav_Input(u8 taskId);
static void Task_DexNav_Sair(u8 taskId);
static void IniciarVideo(void);
static void MontarMapa(struct DexNavTela *t);
static void MontarAba(struct DexNavTela *t);
static void ContarEspecies(struct DexNavTela *t, u8 aba, u8 *capturados, u8 *total);
static void TrocarAba(struct DexNavTela *t, s8 passo);
static void MoverCursor(struct DexNavTela *t, s8 passo);
static void DesenharTudo(struct DexNavTela *t);
static void DesenharTopo(struct DexNavTela *t);
static void DesenharAbas(struct DexNavTela *t);
static void DesenharLista(struct DexNavTela *t);
static void DesenharRodape(struct DexNavTela *t);
static void DestruirIcones(struct DexNavTela *t);

static const u8 sIcones_Gfx[] = INCBIN_U8("graphics/dexnav/icones.4bpp");
static const u16 sIcones_Pal[] = INCBIN_U16("graphics/dexnav/icones.gbapal");

static const u16 sSilhueta_Pal[16] = {
    0, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA,
    COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA,
};

static const struct SpritePalette sSilhueta_SpritePal = {sSilhueta_Pal, TAG_SILHUETA};

// {fundo, letra, sombra}
static const u8 sCor_Barra[3] = {COR_BARRA, COR_BRANCO, COR_SOMBRA_BARRA};
static const u8 sCor_BarraClara[3] = {COR_BARRA, COR_FAIXA_ABAS, COR_SOMBRA_BARRA};
static const u8 sCor_Aba[3] = {COR_ABA, COR_TEXTO, COR_SOMBRA_ABA};
static const u8 sCor_AbaAtual[3] = {COR_BARRA, COR_BRANCO, COR_SOMBRA_BARRA};
static const u8 sCor_Secao[3] = {COR_FUNDO, COR_SECAO, COR_SOMBRA};
static const u8 sCor_Extra[3] = {COR_FUNDO, COR_CINZA, COR_SOMBRA};
static const u8 sCor_Seta[3] = {COR_FUNDO, COR_DIVISOR, COR_SOMBRA};
static const u8 sCor_Rodape[3] = {COR_SOMBRA_BARRA, COR_BRANCO, COR_BARRA};

static const u8 sText_SetaCima[] = _("{UP_ARROW}");
static const u8 sText_SetaBaixo[] = _("{DOWN_ARROW}");
static const u8 sText_Traco[] = {CHAR_HYPHEN, EOS};

// A aba de cada jeito de encontrar
static const u8 sAbaDoMetodo[DEXNAV_METHOD_COUNT] = {
    [DEXNAV_METHOD_LAND]      = DEXNAV_TAB_LAND,
    [DEXNAV_METHOD_WATER]     = DEXNAV_TAB_WATER,
    [DEXNAV_METHOD_OLD_ROD]   = DEXNAV_TAB_RODS,
    [DEXNAV_METHOD_GOOD_ROD]  = DEXNAV_TAB_RODS,
    [DEXNAV_METHOD_SUPER_ROD] = DEXNAV_TAB_RODS,
    [DEXNAV_METHOD_ROCK]      = DEXNAV_TAB_ROCK,
};

static const u8 *const sNomeDaAba[DEXNAV_TAB_COUNT] = {
    [DEXNAV_TAB_LAND]  = gText_DexNav_AbaGrama,
    [DEXNAV_TAB_WATER] = gText_DexNav_AbaSurf,
    [DEXNAV_TAB_RODS]  = gText_DexNav_AbaVaras,
    [DEXNAV_TAB_ROCK]  = gText_DexNav_AbaPedra,
};

// Título da seção de cada vara (DEXNAV_METHOD_OLD_ROD em diante)
static const u8 *const sNomeDaVara[] = {
    gText_DexNav_VaraVelha,
    gText_DexNav_VaraBoa,
    gText_DexNav_Supervara,
};
STATIC_ASSERT(DEXNAV_METHOD_GOOD_ROD == DEXNAV_METHOD_OLD_ROD + 1 && DEXNAV_METHOD_SUPER_ROD == DEXNAV_METHOD_OLD_ROD + 2,
              DexNavVarasEmSequencia);

static const struct BgTemplate sBgTemplates[] = {
    {
        .bg = 0,
        .charBaseIndex = 0,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0,
    },
};

static const struct WindowTemplate sWindowTemplates[WIN_COUNT + 1] = {
    [WIN_TOPO] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = TELA_TILES_X,
        .height = TOPO_TILES,
        .paletteNum = 0,
        .baseBlock = WIN_TOPO_BASE,
    },
    [WIN_ABAS] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = TOPO_TILES,
        .width = TELA_TILES_X,
        .height = ABAS_TILES,
        .paletteNum = 0,
        .baseBlock = WIN_ABAS_BASE,
    },
    [WIN_LISTA] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = LISTA_TOPO_TILES,
        .width = TELA_TILES_X,
        .height = LISTA_ALTURA / 8,
        .paletteNum = 0,
        .baseBlock = WIN_LISTA_BASE,
    },
    [WIN_RODAPE] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = RODAPE_TOPO_TILES,
        .width = TELA_TILES_X,
        .height = RODAPE_TILES,
        .paletteNum = 0,
        .baseBlock = WIN_RODAPE_BASE,
    },
    [WIN_COUNT] = DUMMY_WIN_TEMPLATE
};

// --- entrada e saída ------------------------------------------------------------------------------------------------

void DexNav_Open(MainCallback returnTo)
{
    s16 mapIndex = DexNav_MapIndexOf(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum);

    // mapa sem encontro (cidade, interior): por enquanto volta direto; a Task 3 abre a lista de mapas
    if (mapIndex < 0)
    {
        SetMainCallback2(returnTo);
        return;
    }
    AbrirTela(returnTo, DEXNAV_MODE_MAP, mapIndex);
}

// Script de campo (`callnative`, depois de `fadescreen`; a volta continua o script, que espera com `waitstate`)
void DexNav_OpenFromScript(void)
{
    QuestLog_CutRecording();
    DexNav_Open(CB2_ReturnToFieldContinueScriptPlayMapMusic);
    LockPlayerFieldControls();
}

// Aloca o bloco, guarda o retorno e troca o CB2: a tela monta no próximo CB2, fora de quem chamou. Sem memória, volta.
static void AbrirTela(MainCallback voltar, u8 modo, u8 mapIndex)
{
    struct DexNavTela *t;
    u8 i;

    sDexNav = AllocZeroed(sizeof(*sDexNav));
    if (sDexNav == NULL)
    {
        SetMainCallback2(voltar);
        return;
    }
    t = sDexNav;
    t->voltar = voltar;
    t->modo = modo;
    t->mapIndex = mapIndex;
    t->fase = FASE_ESPERA;
    for (i = 0; i < ICONES_MAX; i++)
        t->icones[i] = ICONE_NENHUM;
    t->ajudaAntes = gHelpSystemEnabled;
    gHelpSystemEnabled = FALSE;
    SetMainCallback2(CB2_DexNav_Montar);
}

static void CB2_DexNav_Montar(void)
{
    SetVBlankHBlankCallbacksToNull();
    ClearScheduledBgCopiesToVram();
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();
    ResetTasks();
    ScanlineEffect_Stop();
    CreateTask(Task_DexNav, 0);   // com as tasks zeradas, sempre há uma livre
    sDexNav->fase = FASE_MONTAR;
    SetMainCallback2(CB2_DexNav);
}

void CB2_DexNav(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void VBlankCB_DexNav(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void Task_DexNav(u8 taskId)
{
    switch (sDexNav->fase)
    {
    case FASE_MONTAR:
        Task_DexNav_Montar(taskId);
        break;
    case FASE_INPUT:
        Task_DexNav_Input(taskId);
        break;
    case FASE_SAIR:
        Task_DexNav_Sair(taskId);
        break;
    }
}

static void Task_DexNav_Montar(u8 taskId)
{
    struct DexNavTela *t = sDexNav;

    switch (t->passo)
    {
    case 0:
        SetVBlankCallback(NULL);
        IniciarVideo();
        break;
    case 1:
        LoadPalette(sIcones_Pal, BG_PLTT_ID(0), PLTT_SIZE_4BPP);
        LoadMonIconPalettes();
        LoadSpritePalette(&sSilhueta_SpritePal);
        MontarMapa(t);
        DesenharTudo(t);
        break;
    case 2:
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        SetVBlankCallback(VBlankCB_DexNav);
        break;
    default:
        if (gPaletteFade.active)
            return;
        t->inputReady = TRUE;
        t->fase = FASE_INPUT;
        return;
    }
    t->passo++;
}

static void Task_DexNav_Input(u8 taskId)
{
    struct DexNavTela *t = sDexNav;

    if (JOY_NEW(B_BUTTON))
    {
        PlaySE(SE_SELECT);
        t->inputReady = FALSE;
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        t->fase = FASE_SAIR;
    }
    else if (JOY_NEW(L_BUTTON))
    {
        TrocarAba(t, -1);
    }
    else if (JOY_NEW(R_BUTTON))
    {
        TrocarAba(t, 1);
    }
    else if (JOY_REPT(DPAD_UP))
    {
        MoverCursor(t, -1);
    }
    else if (JOY_REPT(DPAD_DOWN))
    {
        MoverCursor(t, 1);
    }
}

static void Task_DexNav_Sair(u8 taskId)
{
    MainCallback voltar = sDexNav->voltar;
    u8 ajudaAntes = sDexNav->ajudaAntes;

    if (gPaletteFade.active)
        return;
    DestruirIcones(sDexNav);
    FreeAllWindowBuffers();
    DestroyTask(taskId);
    Free(sDexNav);
    sDexNav = NULL;
    if (ajudaAntes)
        HelpSystem_Enable();
    SetMainCallback2(voltar);
}

static void IniciarVideo(void)
{
    DmaClearLarge16(3, (void *)VRAM, VRAM_SIZE, 0x1000);
    DmaClear32(3, (void *)OAM, OAM_SIZE);
    DmaClear16(3, (void *)PLTT, PLTT_SIZE);
    SetGpuReg(REG_OFFSET_DISPCNT, 0);
    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sBgTemplates, ARRAY_COUNT(sBgTemplates));
    ChangeBgX(0, 0, BG_COORD_SET);
    ChangeBgY(0, 0, BG_COORD_SET);
    InitWindows(sWindowTemplates);
    DeactivateAllTextPrinters();
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_1D_MAP | DISPCNT_OBJ_ON);
    // quem abre pode chegar com escurecimento (BLDCNT/BLDY) e janelas ligados: a tela começa limpa
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    SetGpuReg(REG_OFFSET_BLDY, 0);
    SetGpuReg(REG_OFFSET_WININ, 0);
    SetGpuReg(REG_OFFSET_WINOUT, 0);
    ShowBg(0);
}

// --- dados ----------------------------------------------------------------------------------------------------------

// As entradas do mapa (todas, de todos os períodos), as abas que ele tem e o contador do mapa; abre na primeira aba.
static void MontarMapa(struct DexNavTela *t)
{
    u8 i;

    t->periods = DexNav_CurrentPeriodBit();
    t->period = DayNight_GetPeriod();
    t->nEntries = DexNav_GetMapEntries(t->mapIndex, t->entries, DEXNAV_MAX_ENTRIES);
    t->abasMask = 0;
    for (i = 0; i < t->nEntries; i++)
        t->abasMask |= 1 << sAbaDoMetodo[t->entries[i].method];
    t->nAbas = 0;
    for (i = 0; i < DEXNAV_TAB_COUNT; i++)
    {
        if (t->abasMask & (1 << i))
            t->abas[t->nAbas++] = i;
    }
    t->abaPos = 0;
    ContarEspecies(t, DEXNAV_TAB_COUNT, &t->capturadosMapa, &t->totalMapa);
    MontarAba(t);
}

static bool8 NaAba(const struct DexNavEntry *e, u8 aba)
{
    return aba == DEXNAV_TAB_COUNT || sAbaDoMetodo[e->method] == aba;
}

// Espécies distintas da aba (DEXNAV_TAB_COUNT = o mapa todo), em qualquer horário (o progresso não muda com o
// relógio), e quantas delas estão capturadas na Pokédex.
static void ContarEspecies(struct DexNavTela *t, u8 aba, u8 *capturados, u8 *total)
{
    u8 i, j;

    *capturados = 0;
    *total = 0;
    for (i = 0; i < t->nEntries; i++)
    {
        if (!NaAba(&t->entries[i], aba))
            continue;
        for (j = 0; j < i; j++)
        {
            if (t->entries[j].species == t->entries[i].species && NaAba(&t->entries[j], aba))
                break;
        }
        if (j < i)
            continue;
        (*total)++;
        if (GetSetPokedexFlag(SpeciesToNationalPokedexNum(t->entries[i].species), FLAG_GET_CAUGHT))
            (*capturados)++;
    }
}

static void AdicionarLinha(struct DexNavTela *t, u8 tipo, u8 idx)
{
    if (t->nLinhas >= LINHAS_MAX)
        return;
    t->linhas[t->nLinhas].tipo = tipo;
    t->linhas[t->nLinhas].idx = idx;
    t->nLinhas++;
}

// A espécie aparece agora em alguma entrada da aba?
static bool8 AparecemAgora(struct DexNavTela *t, u8 aba, u16 species)
{
    u8 i;

    for (i = 0; i < t->nEntries; i++)
    {
        if (t->entries[i].species == species && NaAba(&t->entries[i], aba) && (t->entries[i].periods & t->periods))
            return TRUE;
    }
    return FALSE;
}

// As linhas da aba atual: por jeito de encontrar (VARAS: uma seção por vara, com título, só se tiver Pokémon agora),
// os Pokémon do período de agora por chance (maior primeiro; empate: a ordem de DexNav_GetMapEntries) e, no fim, a
// linha extra com as espécies da aba que só aparecem em outro período. A seleção vai para o primeiro Pokémon.
static void MontarAba(struct DexNavTela *t)
{
    u8 aba, m, i, j, secao, primeira;
    u16 rate;
    const struct DexNavEntry *e;

    t->nLinhas = 0;
    t->nMons = 0;
    t->extraN = 0;
    t->extraPeriods = 0;
    t->topo = 0;
    t->cursor = 0;
    t->capturadosAba = 0;
    t->totalAba = 0;
    if (t->nAbas == 0)
        return;
    aba = t->abas[t->abaPos];
    ContarEspecies(t, aba, &t->capturadosAba, &t->totalAba);
    for (m = 0; m < DEXNAV_METHOD_COUNT; m++)
    {
        if (sAbaDoMetodo[m] != aba)
            continue;
        secao = t->nLinhas;
        if (aba == DEXNAV_TAB_RODS)
            AdicionarLinha(t, LINHA_SECAO, m);
        primeira = t->nLinhas;
        for (i = 0; i < t->nEntries; i++)
        {
            e = &t->entries[i];
            if (e->method != m || !(e->periods & t->periods) || t->nLinhas >= LINHAS_MAX)
                continue;
            rate = DexNav_RateForPeriods(e, t->periods);
            for (j = t->nLinhas; j > primeira && DexNav_RateForPeriods(&t->entries[t->linhas[j - 1].idx], t->periods) < rate; j--)
                t->linhas[j] = t->linhas[j - 1];
            t->linhas[j].tipo = LINHA_MON;
            t->linhas[j].idx = i;
            t->nLinhas++;
            t->nMons++;
        }
        if (t->nLinhas == primeira)
            t->nLinhas = secao;   // a vara não tem nada agora: sem título
    }

    // espécies da aba que não aparecem agora (cada uma uma vez) e os períodos delas
    for (i = 0; i < t->nEntries; i++)
    {
        e = &t->entries[i];
        if (!NaAba(e, aba) || AparecemAgora(t, aba, e->species))
            continue;
        t->extraPeriods |= e->periods;
        for (j = 0; j < i; j++)
        {
            if (t->entries[j].species == e->species && NaAba(&t->entries[j], aba))
                break;
        }
        if (j == i)
            t->extraN++;
    }
    // sem Pokémon agora (a aba existe, então todas as espécies dela são de outro período): a tela se explica
    if (t->nMons == 0)
        AdicionarLinha(t, LINHA_VAZIA, 0);
    if (t->extraN != 0)
        AdicionarLinha(t, LINHA_EXTRA, 0);

    for (i = 0; i < t->nLinhas; i++)
    {
        if (t->linhas[i].tipo == LINHA_MON)
        {
            t->cursor = i;
            break;
        }
    }
}

// --- controles ------------------------------------------------------------------------------------------------------

// L/R: aba anterior/seguinte entre as que o mapa tem, dando a volta; a lista volta ao topo.
static void TrocarAba(struct DexNavTela *t, s8 passo)
{
    if (t->nAbas <= 1)
        return;
    PlaySE(SE_SELECT);
    t->abaPos = (t->abaPos + t->nAbas + passo) % t->nAbas;
    MontarAba(t);
    DesenharAbas(t);
    DesenharLista(t);
}

static u8 AlturaDaLinha(u8 tipo)
{
    switch (tipo)
    {
    case LINHA_MON:
        return LINHA_MON_ALTURA;
    case LINHA_SECAO:
        return LINHA_SECAO_ALTURA;
    default:
        return LINHA_EXTRA_ALTURA;
    }
}

// Altura das linhas de `de` a `ate` (inclusive)
static u16 AlturaDasLinhas(struct DexNavTela *t, u8 de, u8 ate)
{
    u16 altura = 0;

    for (; de <= ate && de < t->nLinhas; de++)
        altura += AlturaDaLinha(t->linhas[de].tipo);
    return altura;
}

// O título da seção (VARAS) a que a linha pertence: a última LINHA_SECAO antes dela (LINHA_NENHUMA = sem seção)
static u8 SecaoDaLinha(struct DexNavTela *t, u8 linha)
{
    while (linha > 0)
    {
        linha--;
        if (t->linhas[linha].tipo == LINHA_SECAO)
            return linha;
    }
    return LINHA_NENHUMA;
}

// Título fixo no alto da lista: quando a primeira linha visível é de uma seção cujo título já rolou para cima, o título
// fica preso no alto (LINHA_SECAO_ALTURA px), e as linhas começam embaixo dele. Assim a vara da linha de cima nunca
// some ao rolar (o título só "volta para o lugar" quando a lista sobe até ele).
static u8 SecaoFixa(struct DexNavTela *t)
{
    if (t->topo >= t->nLinhas || t->linhas[t->topo].tipo == LINHA_SECAO)
        return LINHA_NENHUMA;
    return SecaoDaLinha(t, t->topo);
}

// Altura usada a partir de `topo` até `ate`, contando o título fixo
static u16 AlturaVisivel(struct DexNavTela *t, u8 ate)
{
    return AlturaDasLinhas(t, t->topo, ate) + (SecaoFixa(t) != LINHA_NENHUMA ? LINHA_SECAO_ALTURA : 0);
}

// Rola para mostrar a linha selecionada e, no último Pokémon, o que vier depois dele (a linha extra). Subindo, o topo
// vai até o título da seção da linha selecionada (se ela tiver); descendo, o título que sair de vista fica fixo no alto
// (SecaoFixa): a seção da linha selecionada está sempre à vista.
static void AjustarTopo(struct DexNavTela *t)
{
    u8 primeira = t->cursor, ultima = t->cursor, secao, i;

    secao = SecaoDaLinha(t, t->cursor);
    if (secao != LINHA_NENHUMA)
        primeira = secao;
    for (i = t->cursor + 1; i < t->nLinhas && t->linhas[i].tipo != LINHA_MON; i++)
        ;
    if (i >= t->nLinhas)
        ultima = t->nLinhas - 1;
    if (t->topo > t->cursor)
        t->topo = primeira;
    while (t->topo < t->cursor && AlturaVisivel(t, ultima) > LISTA_ALTURA)
        t->topo++;
}

// ▲▼: o Pokémon anterior/seguinte (sem dar a volta; os títulos e a linha extra são pulados)
static void MoverCursor(struct DexNavTela *t, s8 passo)
{
    s16 i = t->cursor;

    do
    {
        i += passo;
    } while (i >= 0 && i < t->nLinhas && t->linhas[i].tipo != LINHA_MON);
    if (i < 0 || i >= t->nLinhas)
        return;
    PlaySE(SE_SELECT);
    t->cursor = i;
    AjustarTopo(t);
    DesenharLista(t);
}

// --- desenho --------------------------------------------------------------------------------------------------------

static void BlitIcone(u8 windowId, u8 icone, u16 x, u16 y)
{
    BlitBitmapRectToWindow(windowId, sIcones_Gfx, icone * 8, 0, ICONE_COUNT * 8, 8, x, y, 8, 8);
}

static void DesenharTudo(struct DexNavTela *t)
{
    DesenharTopo(t);
    DesenharAbas(t);
    DesenharLista(t);
    DesenharRodape(t);
}

// Nome do mapa, período e "capturados/total" do mapa (ou "100%" e a coroa, com tudo capturado)
static void DesenharTopo(struct DexNavTela *t)
{
    u8 contador[12];
    u8 *fim;
    bool8 completo = t->totalMapa != 0 && t->capturadosMapa == t->totalMapa;

    FillWindowPixelBuffer(WIN_TOPO, PIXEL_FILL(COR_BARRA));
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_NOME_X, TOPO_TEXTO_Y, 0, 0, sCor_Barra, TEXT_SKIP_DRAW,
                                 gDexNavMaps[t->mapIndex].name);
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_PERIODO_X, TOPO_TEXTO_Y, 0, 0, sCor_BarraClara,
                                 TEXT_SKIP_DRAW, gText_DayNight_PeriodName[t->period]);
    if (completo)
    {
        StringCopy(contador, gText_DexNav_Completo);
        BlitIcone(WIN_TOPO, ICONE_COROA, TOPO_COROA_X, TOPO_COROA_Y);
    }
    else
    {
        fim = ConvertIntToDecimalStringN(contador, t->capturadosMapa, STR_CONV_MODE_LEFT_ALIGN, 2);
        *fim++ = CHAR_SLASH;
        ConvertIntToDecimalStringN(fim, t->totalMapa, STR_CONV_MODE_LEFT_ALIGN, 2);
    }
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_CONTADOR_FIM - GetStringWidth(FONT_NORMAL, contador, 0),
                                 TOPO_TEXTO_Y, 0, 0, sCor_Barra, TEXT_SKIP_DRAW, contador);
    PutWindowTilemap(WIN_TOPO);
    CopyWindowToVram(WIN_TOPO, COPYWIN_FULL);
}

// As abas do mapa, cada uma na sua vaga fixa; a atual em azul; coroa na aba com tudo capturado
static void DesenharAbas(struct DexNavTela *t)
{
    u8 p, capturados, total;
    u16 x;

    FillWindowPixelBuffer(WIN_ABAS, PIXEL_FILL(COR_FAIXA_ABAS));
    for (p = 0; p < t->nAbas; p++)
    {
        x = ABA_X0 + p * ABA_PASSO;
        FillWindowPixelRect(WIN_ABAS, PIXEL_FILL(p == t->abaPos ? COR_BARRA : COR_ABA), x, 1, ABA_LARGURA, 14);
        AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL, x + ABA_TEXTO_DX, ABA_TEXTO_Y, 0, 0,
                                     p == t->abaPos ? sCor_AbaAtual : sCor_Aba, TEXT_SKIP_DRAW, sNomeDaAba[t->abas[p]]);
        ContarEspecies(t, t->abas[p], &capturados, &total);
        if (total != 0 && capturados == total)
            BlitIcone(WIN_ABAS, ICONE_COROA, x + ABA_COROA_DX, ABA_COROA_Y);
    }
    PutWindowTilemap(WIN_ABAS);
    CopyWindowToVram(WIN_ABAS, COPYWIN_FULL);
}

// Chance x 10 em "%": "50%", "2,5%"
static void FormatarChance(u8 *dest, u16 rateX10)
{
    dest = ConvertIntToDecimalStringN(dest, rateX10 / 10, STR_CONV_MODE_LEFT_ALIGN, 3);
    if (rateX10 % 10 != 0)
    {
        *dest++ = CHAR_COMMA;
        dest = ConvertIntToDecimalStringN(dest, rateX10 % 10, STR_CONV_MODE_LEFT_ALIGN, 1);
    }
    *dest++ = CHAR_PERCENT;
    *dest = EOS;
}

static bool8 FoiVisto(u16 species)
{
    u16 dex = SpeciesToNationalPokedexNum(species);

    return GetSetPokedexFlag(dex, FLAG_GET_CAUGHT) || GetSetPokedexFlag(dex, FLAG_GET_SEEN);
}

// O ícone do Pokémon da linha (em silhueta se nunca visto; o selecionado se mexe), na frente do fundo da linha
static void CriarIcone(struct DexNavTela *t, u8 slot, u8 linha, u16 y)
{
    const struct DexNavEntry *e = &t->entries[t->linhas[linha].idx];
    u8 spriteId;

    spriteId = CreateMonIcon(e->species, linha == t->cursor ? SpriteCB_MonIcon : SpriteCallbackDummy,
                             COL_ICONE_X + 16, LISTA_TOPO_TILES * 8 + y + LINHA_ICONE_DY, 0, 0, FALSE);
    if (spriteId >= MAX_SPRITES)
        return;
    gSprites[spriteId].oam.priority = 0;
    if (!FoiVisto(e->species))
        gSprites[spriteId].oam.paletteNum = IndexOfSpritePaletteTag(TAG_SILHUETA);
    t->icones[slot] = spriteId;
}

static void DestruirIcones(struct DexNavTela *t)
{
    u8 i;

    for (i = 0; i < ICONES_MAX; i++)
    {
        if (t->icones[i] != ICONE_NENHUM)
            DestroyMonIcon(&gSprites[t->icones[i]]);
        t->icones[i] = ICONE_NENHUM;
    }
}

// Uma linha de Pokémon, coluna por coluna (COL_*): marca, nome, chance (à direita), "Nv." e os níveis (à direita)
static void DesenharLinhaMon(struct DexNavTela *t, u8 linha, u16 y)
{
    const struct DexNavEntry *e = &t->entries[t->linhas[linha].idx];
    u16 dex = SpeciesToNationalPokedexNum(e->species);
    bool8 capturado = GetSetPokedexFlag(dex, FLAG_GET_CAUGHT);
    bool8 visto = capturado || GetSetPokedexFlag(dex, FLAG_GET_SEEN);
    bool8 selecionada = linha == t->cursor;
    u8 cor[3], corNome[3], texto[12];

    cor[0] = corNome[0] = selecionada ? COR_SELECAO : COR_FUNDO;
    cor[1] = COR_TEXTO;
    cor[2] = corNome[2] = COR_SOMBRA;
    corNome[1] = visto ? COR_TEXTO : COR_CINZA;
    if (selecionada)
        FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(COR_SELECAO), SELECAO_X, y, SELECAO_FIM - SELECAO_X, LINHA_MON_ALTURA);

    BlitIcone(WIN_LISTA, capturado ? ICONE_CAPTURADO : (visto ? ICONE_VISTO : ICONE_NUNCA_VISTO), COL_MARCA_X,
              y + LINHA_MARCA_DY);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NOME_X, y + LINHA_TEXTO_DY, 0, 0, corNome, TEXT_SKIP_DRAW,
                                 visto ? gSpeciesNames[e->species] : gText_DexNav_Desconhecido);

    FormatarChance(texto, DexNav_RateForPeriods(e, t->periods));
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_CHANCE_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);

    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_X, y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW,
                                 gText_DexNav_Nivel);
    ConvertIntToDecimalStringN(texto, e->minLevel, STR_CONV_MODE_LEFT_ALIGN, 3);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_MIN_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);
    if (e->maxLevel != e->minLevel)
    {
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_TRACO_X, y + LINHA_TEXTO_DY, 0, 0, cor,
                                     TEXT_SKIP_DRAW, sText_Traco);
        ConvertIntToDecimalStringN(texto, e->maxLevel, STR_CONV_MODE_LEFT_ALIGN, 3);
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_MAX_X, y + LINHA_TEXTO_DY, 0, 0, cor,
                                     TEXT_SKIP_DRAW, texto);
    }
}

// Título da seção de uma vara (VARAS), com um fio até o fim da linha
static void DesenharLinhaSecao(struct DexNavTela *t, u8 linha, u16 y)
{
    const u8 *nome = sNomeDaVara[t->linhas[linha].idx - DEXNAV_METHOD_OLD_ROD];
    u16 fimTexto = SECAO_X + GetStringWidth(FONT_NORMAL, nome, 0) + 4;

    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, SECAO_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, sCor_Secao,
                                 TEXT_SKIP_DRAW, nome);
    if (fimTexto < SELECAO_FIM)
        FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(COR_DIVISOR), fimTexto, y + LINHA_SECAO_ALTURA / 2, SELECAO_FIM - fimTexto, 1);
}

// "+N à noite" (de dia, de manhã, à tarde ou em outros horários), na coluna do nome
static void DesenharLinhaExtra(struct DexNavTela *t, u16 y)
{
    const u8 *texto;

    switch (t->extraPeriods)
    {
    case DEXNAV_PERIOD_NIGHT:
        texto = gText_DexNav_MaisNoite;
        break;
    case DEXNAV_PERIOD_MORNING | DEXNAV_PERIOD_DAY:
        texto = gText_DexNav_MaisDia;
        break;
    case DEXNAV_PERIOD_MORNING:
        texto = gText_DexNav_MaisManha;
        break;
    case DEXNAV_PERIOD_DAY:
        texto = gText_DexNav_MaisTarde;
        break;
    default:
        texto = gText_DexNav_MaisOutros;
        break;
    }
    ConvertIntToDecimalStringN(gStringVar1, t->extraN, STR_CONV_MODE_LEFT_ALIGN, 2);
    StringExpandPlaceholders(gStringVar4, texto);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NOME_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, sCor_Extra,
                                 TEXT_SKIP_DRAW, gStringVar4);
}

// "Nenhum agora": a aba só tem espécies de outro período (a linha extra, logo abaixo, diz quantas e quando)
static void DesenharLinhaVazia(u16 y)
{
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NOME_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, sCor_Extra,
                                 TEXT_SKIP_DRAW, gText_DexNav_NenhumAgora);
}

// As linhas visíveis a partir de `topo` (até LISTA_ALTURA), os ícones delas e as setas de rolagem; o título da seção
// que rolou para cima fica fixo no alto (SecaoFixa)
static void DesenharLista(struct DexNavTela *t)
{
    u8 i, slot = 0, fixa = SecaoFixa(t);
    u16 y = 0, altura;

    DestruirIcones(t);
    FillWindowPixelBuffer(WIN_LISTA, PIXEL_FILL(COR_FUNDO));
    if (t->nLinhas == 0)
    {
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL,
                                     (DISPLAY_WIDTH - GetStringWidth(FONT_NORMAL, gText_DexNav_Nenhum, 0)) / 2,
                                     (LISTA_ALTURA - 16) / 2, 0, 0, sCor_Extra, TEXT_SKIP_DRAW, gText_DexNav_Nenhum);
    }
    if (fixa != LINHA_NENHUMA)
    {
        DesenharLinhaSecao(t, fixa, 0);
        y = LINHA_SECAO_ALTURA;
    }
    for (i = t->topo; i < t->nLinhas; i++)
    {
        altura = AlturaDaLinha(t->linhas[i].tipo);
        if (y + altura > LISTA_ALTURA)
            break;
        switch (t->linhas[i].tipo)
        {
        case LINHA_MON:
            DesenharLinhaMon(t, i, y);
            if (slot < ICONES_MAX)
                CriarIcone(t, slot++, i, y);
            break;
        case LINHA_SECAO:
            DesenharLinhaSecao(t, i, y);
            break;
        case LINHA_VAZIA:
            DesenharLinhaVazia(y);
            break;
        default:
            DesenharLinhaExtra(t, y);
            break;
        }
        y += altura;
    }
    if (t->topo > 0)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_SETA_X, 0, 0, 0, sCor_Seta, TEXT_SKIP_DRAW,
                                     sText_SetaCima);
    if (i < t->nLinhas)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_SETA_X, LISTA_ALTURA - 16, 0, 0, sCor_Seta,
                                     TEXT_SKIP_DRAW, sText_SetaBaixo);
    PutWindowTilemap(WIN_LISTA);
    CopyWindowToVram(WIN_LISTA, COPYWIN_FULL);
}

// Os botões: "L/R: aba" só quando o mapa tem mais de uma aba
static void DesenharRodape(struct DexNavTela *t)
{
    FillWindowPixelBuffer(WIN_RODAPE, PIXEL_FILL(COR_SOMBRA_BARRA));
    AddTextPrinterParameterized4(WIN_RODAPE, FONT_NORMAL, RODAPE_X, RODAPE_Y, 0, 0, sCor_Rodape, TEXT_SKIP_DRAW,
                                 t->nAbas >= 2 ? gText_DexNav_Rodape : gText_DexNav_RodapeSair);
    PutWindowTilemap(WIN_RODAPE);
    CopyWindowToVram(WIN_RODAPE, COPYWIN_FULL);
}

// --- esteira --------------------------------------------------------------------------------------------------------

// TEST_CMD_DEXNAV_STATE (o formato de cada `what` está em include/dexnav.h)
u32 DexNav_TestGetState(u8 what)
{
    struct DexNavTela *t = sDexNav;
    u8 aba, cursor = 0, i;

    if (t == NULL)
        return 0xFFFFFFFF;
    aba = t->nAbas != 0 ? t->abas[t->abaPos] : 0xFF;
    for (i = 0; i < t->cursor && i < t->nLinhas; i++)
    {
        if (t->linhas[i].tipo == LINHA_MON)
            cursor++;
    }
    switch (what)
    {
    case 0:
        return t->modo | aba << 8 | cursor << 16 | t->mapIndex << 24;
    case 1:
        return t->inputReady | t->abasMask << 8 | t->nMons << 16 | t->topo << 24;
    case 2:
        return t->capturadosMapa | t->totalMapa << 8 | t->capturadosAba << 16 | t->totalAba << 24;
    case 3:
        return t->extraN | t->extraPeriods << 8 | t->periods << 16;
    }
    return 0xFFFFFFFF;
}
