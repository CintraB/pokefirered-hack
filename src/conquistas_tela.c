#include "global.h"
#include "gflib.h"
#include "conquistas.h"
#include "event_data.h"
#include "help_system.h"
#include "menu.h"
#include "menu_helpers.h"
#include "new_menu_helpers.h"
#include "money.h"
#include "overworld.h"
#include "quest_log.h"
#include "scanline_effect.h"
#include "script.h"
#include "strings.h"
#include "task.h"
#include "trainer_card.h"
#include "constants/conquistas.h"
#include "constants/songs.h"
#include "data/conquistas_ids.h"

// Tela de conquistas (POK-44, Task 7; desenho em docs/superpowers/specs/2026-10-31-conquistas-e-diario-design.md).
// Modelo aprovado pelo Cintra: abas no alto (L/R, dando a volta), a lista da aba com ✓ (feita), ☐ (pendente, com o
// progresso "87/100" à direita quando houver) ou o nome riscado em cinza (perdida, fora do total), e o rodapé com
// "<Aba>: F de V" e uma barra. Conquista inativa (POK-42) não aparece.
//
// Memória: um bloco AllocZeroed com tudo, apontado só pela task da tela (nenhuma EWRAM nova), liberado na saída. A
// tela sai para o CB2 `voltar` que quem abriu passou (o cartão de treinador ou o campo continuando o script).
// A ajuda do jogo (que também escuta L/R) fica desligada enquanto a tela está aberta.

// Janelas, todas no BG0 (bloco de caracteres 0, tilemap no bloco 31), uma linha de tiles depois da outra:
//   linhas 0-1    WIN_ABAS     barra das abas
//   linhas 2-17   WIN_LISTA    LISTA_LINHAS linhas de LINHA_ALTURA px
//   linhas 18-19  WIN_RODAPE   "<Aba>: F de V" e a barra
#define LISTA_LINHAS    8
#define LINHA_ALTURA    16
#define LISTA_TOPO      2
#define RODAPE_TOPO     (LISTA_TOPO + LISTA_LINHAS * LINHA_ALTURA / 8)
#define TELA_TILES_X    (DISPLAY_WIDTH / 8)
STATIC_ASSERT(RODAPE_TOPO + 2 == DISPLAY_HEIGHT / 8, ConqTelaOcupaATela);

// Cada linha da lista: ícone, nome (até CONQ_NOME_LARGURA) e o progresso alinhado à direita até PROGRESSO_FIM; a
// coluna das setas de rolagem fica depois. O progresso nunca encosta no nome (pelo menos NOME_FOLGA px depois dele).
#define ICONE_X         4
#define NOME_X          16
#define NOME_FOLGA      8
#define PROGRESSO_FIM   222
#define SETA_ROLAGEM_X  228
STATIC_ASSERT(NOME_X + CONQ_NOME_LARGURA <= PROGRESSO_FIM, ConqNomeCabe);

// Abas: todas em FONT_SMALL entre as setas (ABAS_INICIO..ABAS_FIM, 216 px; a seta ◄ em x = 1 e a ► em x = 231),
// com ABA_PAD px de cada lado; se não couberem, só a atual, no meio. test_abas_cabem_em_font_small mede as 5.
#define ABA_PAD         3
#define ABAS_INICIO     12
#define ABAS_FIM        228
#define SETA_ESQ_X      1
#define SETA_DIR_X      231

// Rodapé: texto em x = RODAPE_TEXTO_X até a barra (RODAPE_TEXTO_LARGURA px, a regra do check_text) e a barra.
#define RODAPE_TEXTO_X        6
#define RODAPE_TEXTO_LARGURA  128
#define BARRA_X               136
#define BARRA_Y               5
#define BARRA_LARGURA         96
#define BARRA_ALTURA          6
STATIC_ASSERT(RODAPE_TEXTO_X + RODAPE_TEXTO_LARGURA <= BARRA_X, ConqRodapeAntesDaBarra);
STATIC_ASSERT(BARRA_X + BARRA_LARGURA <= DISPLAY_WIDTH - 4, ConqBarraCabe);

enum {
    WIN_ABAS,
    WIN_LISTA,
    WIN_RODAPE,
    WIN_COUNT
};

#define WIN_ABAS_BASE    1
#define WIN_LISTA_BASE   (WIN_ABAS_BASE + TELA_TILES_X * 2)
#define WIN_RODAPE_BASE  (WIN_LISTA_BASE + TELA_TILES_X * LISTA_LINHAS * 2)
#define WINS_FIM         (WIN_RODAPE_BASE + TELA_TILES_X * 2)
STATIC_ASSERT(WINS_FIM * TILE_SIZE_4BPP <= 31 * BG_SCREEN_SIZE, ConqJanelasAntesDoTilemap);

// Ícones de graphics/conquistas/icones.png (8 x 8 cada, lado a lado); a paleta é a da tela inteira.
enum {
    ICONE_FEITA,
    ICONE_PENDENTE,
    ICONE_SETA_ESQ,
    ICONE_SETA_DIR,
    ICONE_COUNT
};

// Cores de graphics/conquistas/icones.pal
#define COR_FUNDO        0
#define COR_BRANCO       1
#define COR_TEXTO        2
#define COR_SOMBRA       3
#define COR_PERDIDA      6
#define COR_BARRA_ABAS   7
#define COR_SOMBRA_ABAS  8
#define COR_ABA_ATUAL    9
#define COR_BARRA_CHEIA  10
#define COR_BARRA_VAZIA  11
#define COR_LINHA        12
#define COR_PROGRESSO    14

enum {
    FASE_ESPERA,     // criada no Conquistas_AbrirTela, até o CB2 montar a tela
    FASE_MONTAR,
    FASE_INPUT,
    FASE_SAIR,
};

struct ConquistasTela
{
    void (*voltar)(void);
    u8 modo;          // 0 conquistas, 1 diário (Task 8)
    u8 aba;
    u8 topo;          // primeira linha visível da lista
    u8 n;             // conquistas da aba
    u8 fase;
    u8 passo;         // passo da montagem
    u8 inputReady;
    u8 itens[CONQ_COUNT];
};

#define tPtr 0   // data[0..1]: o bloco da tela

static void CB2_ConquistasTela_Montar(void);
static void CB2_ConquistasTela(void);
static void VBlankCB_ConquistasTela(void);
static void Task_ConquistasTela(u8 taskId);
static void Task_ConquistasTela_Montar(u8 taskId, struct ConquistasTela *t);
static void Task_ConquistasTela_Input(u8 taskId, struct ConquistasTela *t);
static void Task_ConquistasTela_Sair(u8 taskId, struct ConquistasTela *t);
static void CB2_VoltarAoCartao(void);
static void IniciarVideo(struct ConquistasTela *t);
static void TrocarAba(struct ConquistasTela *t, s8 passo);
static void MontarLista(struct ConquistasTela *t);
static void DesenharTudo(struct ConquistasTela *t);
static void DesenharAbas(struct ConquistasTela *t);
static void DesenharLista(struct ConquistasTela *t);
static void DesenharLinha(struct ConquistasTela *t, u8 linha, u8 num);
static void DesenharRodape(struct ConquistasTela *t);

static const u8 sIcones_Gfx[] = INCBIN_U8("graphics/conquistas/icones.4bpp");
static const u16 sIcones_Pal[] = INCBIN_U16("graphics/conquistas/icones.gbapal");

// {fundo, letra, sombra}
static const u8 sCor_Aba[3] = {COR_BARRA_ABAS, COR_BRANCO, COR_SOMBRA_ABAS};
static const u8 sCor_AbaAtual[3] = {COR_ABA_ATUAL, COR_TEXTO, COR_SOMBRA};
static const u8 sCor_Texto[3] = {COR_FUNDO, COR_TEXTO, COR_SOMBRA};
static const u8 sCor_Perdida[3] = {COR_FUNDO, COR_PERDIDA, COR_BARRA_VAZIA};
static const u8 sCor_Progresso[3] = {COR_FUNDO, COR_PROGRESSO, COR_SOMBRA};
static const u8 sCor_Seta[3] = {COR_FUNDO, COR_LINHA, COR_SOMBRA};

static const u8 sText_SetaCima[] = _("{UP_ARROW}");
static const u8 sText_SetaBaixo[] = _("{DOWN_ARROW}");

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
    [WIN_ABAS] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = TELA_TILES_X,
        .height = 2,
        .paletteNum = 0,
        .baseBlock = WIN_ABAS_BASE,
    },
    [WIN_LISTA] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = LISTA_TOPO,
        .width = TELA_TILES_X,
        .height = LISTA_LINHAS * LINHA_ALTURA / 8,
        .paletteNum = 0,
        .baseBlock = WIN_LISTA_BASE,
    },
    [WIN_RODAPE] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = RODAPE_TOPO,
        .width = TELA_TILES_X,
        .height = 2,
        .paletteNum = 0,
        .baseBlock = WIN_RODAPE_BASE,
    },
    [WIN_COUNT] = DUMMY_WIN_TEMPLATE
};

static struct ConquistasTela *GetTela(u8 *taskId)
{
    u8 id = FindTaskIdByFunc(Task_ConquistasTela);

    if (taskId != NULL)
        *taskId = id;
    if (id == TASK_NONE)
        return NULL;
    return (struct ConquistasTela *)GetWordTaskArg(id, tPtr);
}

// Entrada única: aloca o bloco, guarda o retorno e troca o CB2; a tela monta no próximo CB2, fora de quem chamou
// (o script do campo ou o cartão de treinador). Sem memória ou sem task, volta direto.
void Conquistas_AbrirTela(void (*voltar)(void), u8 modo)
{
    struct ConquistasTela *t = AllocZeroed(sizeof(*t));
    u8 taskId;

    if (t == NULL)
    {
        SetMainCallback2(voltar);
        return;
    }
    taskId = CreateTask(Task_ConquistasTela, 0);
    if (taskId == TASK_NONE)
    {
        Free(t);
        SetMainCallback2(voltar);
        return;
    }
    gHelpSystemEnabled = FALSE;
    t->voltar = voltar;
    t->modo = modo;
    t->fase = FASE_ESPERA;
    SetWordTaskArg(taskId, tPtr, (u32)t);
    SetMainCallback2(CB2_ConquistasTela_Montar);
}

// SELECT na frente do cartão (src/trainer_card.c): o cartão já foi liberado; o VBlank dele não roda mais.
void CB2_AbrirConquistasDoCartao(void)
{
    SetVBlankHBlankCallbacksToNull();
    Conquistas_AbrirTela(CB2_VoltarAoCartao, 0);
}

// O cartão do jogador só abre pelo menu Start (src/start_menu.c, StartMenuPlayerCallback), com este retorno.
static void CB2_VoltarAoCartao(void)
{
    ShowPlayerTrainerCard(CB2_ReturnToFieldWithOpenMenu);
}

// Special (data/specials.inc): o script escurece antes (`fadescreen`), põe o modo em VAR_0x8004 e espera a volta
// com `waitstate`.
void Conquistas_AbrirTelaDoScript(void)
{
    QuestLog_CutRecording();
    Conquistas_AbrirTela(CB2_ReturnToFieldContinueScriptPlayMapMusic, gSpecialVar_0x8004 != 0);
    LockPlayerFieldControls();
}

static void CB2_ConquistasTela_Montar(void)
{
    u8 taskId;
    struct ConquistasTela *t = GetTela(NULL);

    SetVBlankHBlankCallbacksToNull();
    ClearScheduledBgCopiesToVram();
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();
    ResetTasks();
    ScanlineEffect_Stop();
    taskId = CreateTask(Task_ConquistasTela, 0);   // com as tasks zeradas, sempre há uma livre
    t->fase = FASE_MONTAR;
    SetWordTaskArg(taskId, tPtr, (u32)t);
    SetMainCallback2(CB2_ConquistasTela);
}

static void CB2_ConquistasTela(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void VBlankCB_ConquistasTela(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void Task_ConquistasTela(u8 taskId)
{
    struct ConquistasTela *t = (struct ConquistasTela *)GetWordTaskArg(taskId, tPtr);

    switch (t->fase)
    {
    case FASE_MONTAR:
        Task_ConquistasTela_Montar(taskId, t);
        break;
    case FASE_INPUT:
        Task_ConquistasTela_Input(taskId, t);
        break;
    case FASE_SAIR:
        Task_ConquistasTela_Sair(taskId, t);
        break;
    }
}

static void Task_ConquistasTela_Montar(u8 taskId, struct ConquistasTela *t)
{
    switch (t->passo)
    {
    case 0:
        SetVBlankCallback(NULL);
        IniciarVideo(t);
        break;
    case 1:
        LoadPalette(sIcones_Pal, BG_PLTT_ID(0), PLTT_SIZE_4BPP);
        MontarLista(t);
        DesenharTudo(t);
        break;
    case 2:
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        SetVBlankCallback(VBlankCB_ConquistasTela);
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

static void Task_ConquistasTela_Input(u8 taskId, struct ConquistasTela *t)
{
    if (JOY_NEW(B_BUTTON))
    {
        PlaySE(SE_SELECT);
        t->inputReady = FALSE;
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        t->fase = FASE_SAIR;
    }
    else if (JOY_NEW(L_BUTTON))
    {
        PlaySE(SE_SELECT);
        TrocarAba(t, -1);
    }
    else if (JOY_NEW(R_BUTTON))
    {
        PlaySE(SE_SELECT);
        TrocarAba(t, 1);
    }
    else if (JOY_NEW(SELECT_BUTTON))
    {
        // o diário (Task 8) entra aqui; até lá, nada
    }
    else if (JOY_REPT(DPAD_UP))
    {
        if (t->topo > 0)
        {
            t->topo--;
            DesenharLista(t);
        }
    }
    else if (JOY_REPT(DPAD_DOWN))
    {
        if (t->topo + LISTA_LINHAS < t->n)
        {
            t->topo++;
            DesenharLista(t);
        }
    }
}

static void Task_ConquistasTela_Sair(u8 taskId, struct ConquistasTela *t)
{
    void (*voltar)(void) = t->voltar;

    if (gPaletteFade.active)
        return;
    FreeAllWindowBuffers();
    DestroyTask(taskId);
    Free(t);
    HelpSystem_Enable();
    SetMainCallback2(voltar);
}

static void IniciarVideo(struct ConquistasTela *t)
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
    ShowBg(0);
}

// L/R: aba anterior/seguinte, dando a volta (da primeira para a última e vice-versa); a lista volta ao topo.
static void TrocarAba(struct ConquistasTela *t, s8 passo)
{
    t->aba = (t->aba + CONQ_ABAS_COUNT + passo) % CONQ_ABAS_COUNT;
    t->topo = 0;
    MontarLista(t);
    DesenharTudo(t);
}

// As conquistas ativas da aba atual, na ordem da tabela.
static void MontarLista(struct ConquistasTela *t)
{
    u8 num;

    t->n = 0;
    for (num = 0; num < CONQ_COUNT; num++)
    {
        if (gConquistas[num].ativa && gConquistas[num].aba == t->aba)
            t->itens[t->n++] = num;
    }
}

static void DesenharTudo(struct ConquistasTela *t)
{
    DesenharAbas(t);
    DesenharLista(t);
    DesenharRodape(t);
}

static void BlitIcone(u8 windowId, u8 icone, u16 x, u16 y)
{
    BlitBitmapRectToWindow(windowId, sIcones_Gfx, icone * 8, 0, ICONE_COUNT * 8, 8, x, y, 8, 8);
}

static void DesenharAbas(struct ConquistasTela *t)
{
    u8 i;
    s32 x, largura, total = 0;

    FillWindowPixelBuffer(WIN_ABAS, PIXEL_FILL(COR_BARRA_ABAS));
    BlitIcone(WIN_ABAS, ICONE_SETA_ESQ, SETA_ESQ_X, 4);
    BlitIcone(WIN_ABAS, ICONE_SETA_DIR, SETA_DIR_X, 4);
    for (i = 0; i < CONQ_ABAS_COUNT; i++)
        total += GetStringWidth(FONT_SMALL, gConquistasAbaNomes[i], 0) + 2 * ABA_PAD;
    if (total <= ABAS_FIM - ABAS_INICIO)
    {
        x = ABAS_INICIO + (ABAS_FIM - ABAS_INICIO - total) / 2;
        for (i = 0; i < CONQ_ABAS_COUNT; i++)
        {
            largura = GetStringWidth(FONT_SMALL, gConquistasAbaNomes[i], 0) + 2 * ABA_PAD;
            if (i == t->aba)
                FillWindowPixelRect(WIN_ABAS, PIXEL_FILL(COR_ABA_ATUAL), x, 1, largura, 14);
            AddTextPrinterParameterized4(WIN_ABAS, FONT_SMALL, x + ABA_PAD, 2, 0, 0,
                                         i == t->aba ? sCor_AbaAtual : sCor_Aba, TEXT_SKIP_DRAW, gConquistasAbaNomes[i]);
            x += largura;
        }
    }
    else
    {
        largura = GetStringWidth(FONT_SMALL, gConquistasAbaNomes[t->aba], 0) + 2 * ABA_PAD;
        x = (DISPLAY_WIDTH - largura) / 2;
        FillWindowPixelRect(WIN_ABAS, PIXEL_FILL(COR_ABA_ATUAL), x, 1, largura, 14);
        AddTextPrinterParameterized4(WIN_ABAS, FONT_SMALL, x + ABA_PAD, 2, 0, 0, sCor_AbaAtual, TEXT_SKIP_DRAW,
                                     gConquistasAbaNomes[t->aba]);
    }
    PutWindowTilemap(WIN_ABAS);
    CopyWindowToVram(WIN_ABAS, COPYWIN_FULL);
}

static void DesenharLista(struct ConquistasTela *t)
{
    u8 i;

    FillWindowPixelBuffer(WIN_LISTA, PIXEL_FILL(COR_FUNDO));
    for (i = 0; i < LISTA_LINHAS && t->topo + i < t->n; i++)
        DesenharLinha(t, i, t->itens[t->topo + i]);
    if (t->topo > 0)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, SETA_ROLAGEM_X, 1, 0, 0, sCor_Seta, TEXT_SKIP_DRAW,
                                     sText_SetaCima);
    if (t->topo + LISTA_LINHAS < t->n)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, SETA_ROLAGEM_X, (LISTA_LINHAS - 1) * LINHA_ALTURA + 1, 0,
                                     0, sCor_Seta, TEXT_SKIP_DRAW, sText_SetaBaixo);
    PutWindowTilemap(WIN_LISTA);
    CopyWindowToVram(WIN_LISTA, COPYWIN_FULL);
}

// Número com ponto de milhar ("10.000"); devolve o fim (EOS).
static u8 *AnexarNumero(u8 *s, u32 n)
{
    if (n >= 1000)
    {
        s = AnexarNumero(s, n / 1000);
        *s++ = CHAR_PERIOD;
        return ConvertIntToDecimalStringN(s, n % 1000, STR_CONV_MODE_LEADING_ZEROS, 3);
    }
    return ConvertIntToDecimalStringN(s, n, STR_CONV_MODE_LEFT_ALIGN, 3);
}

// Uma linha: ícone (✓ feita, ☐ pendente; a perdida fica sem ícone, em cinza e riscada), o nome (o {N} dos degraus vira
// o degrau da vez: o próximo, ou o último depois de todos) e, na pendente com progresso, "atual/meta" à direita.
static void DesenharLinha(struct ConquistasTela *t, u8 linha, u8 num)
{
    const struct Conquista *c = &gConquistas[num];
    u8 estado = Conquistas_GetEstado(num);
    u8 progresso[24];
    u8 *fim;
    u32 atual, meta;
    bool8 temProgresso = Conquistas_Progresso(num, &atual, &meta);
    u16 y = linha * LINHA_ALTURA;
    s32 largNome, largProg;

    if (c->numDegraus > 0)
        ConvertIntToDecimalStringN(gStringVar1, meta, STR_CONV_MODE_LEFT_ALIGN, 3);
    StringExpandPlaceholders(gStringVar4, c->nome);
    largNome = GetStringWidth(FONT_NORMAL, gStringVar4, 0);

    if (estado == CONQ_PERDIDA)
    {
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, NOME_X, y + 1, 0, 0, sCor_Perdida, TEXT_SKIP_DRAW,
                                     gStringVar4);
        FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(COR_PERDIDA), NOME_X - 1, y + 7, largNome + 2, 1);
        return;
    }
    BlitIcone(WIN_LISTA, estado == CONQ_FEITA ? ICONE_FEITA : ICONE_PENDENTE, ICONE_X, y + 4);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, NOME_X, y + 1, 0, 0, sCor_Texto, TEXT_SKIP_DRAW, gStringVar4);
    if (estado == CONQ_FEITA || !temProgresso)
        return;

    fim = progresso;
    if (c->tipo == CONQ_TIPO_DINHEIRO)
        *fim++ = CHAR_CURRENCY;
    fim = AnexarNumero(fim, atual > meta ? meta : atual);
    *fim++ = CHAR_SLASH;
    AnexarNumero(fim, meta);
    largProg = GetStringWidth(FONT_NORMAL, progresso, 0);
    if (PROGRESSO_FIM - largProg >= NOME_X + largNome + NOME_FOLGA)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, PROGRESSO_FIM - largProg, y + 1, 0, 0, sCor_Progresso,
                                     TEXT_SKIP_DRAW, progresso);
}

// "HISTÓRIA" -> "História": a primeira letra fica, as outras viram minúsculas (A-Z e as acentuadas do charmap).
static const u8 sMinusculas[][2] = {
    {CHAR_A_GRAVE, CHAR_a_GRAVE}, {CHAR_A_ACUTE, CHAR_a_ACUTE}, {CHAR_A_CIRCUMFLEX, CHAR_a_CIRCUMFLEX},
    {CHAR_C_CEDILLA, CHAR_c_CEDILLA}, {CHAR_E_ACUTE, CHAR_e_ACUTE}, {CHAR_E_CIRCUMFLEX, CHAR_e_CIRCUMFLEX},
    {CHAR_I_ACUTE, CHAR_i_ACUTE}, {CHAR_O_ACUTE, CHAR_o_ACUTE}, {CHAR_O_CIRCUMFLEX, CHAR_o_CIRCUMFLEX},
    {CHAR_U_ACUTE, CHAR_u_ACUTE},
    {0x42, 0x40}, {0x43, 0x41},   // Ã -> ã, Õ -> õ (charmap.txt, glifos do Hack 7, sem CHAR_* em characters.h)
};

static void NomeDaAbaNoRodape(u8 *dest, u8 aba)
{
    const u8 *src = gConquistasAbaNomes[aba];
    u8 i, ch;

    *dest++ = *src++;
    while ((ch = *src++) != EOS)
    {
        if (ch >= CHAR_A && ch <= CHAR_Z)
            ch += CHAR_a - CHAR_A;
        for (i = 0; i < ARRAY_COUNT(sMinusculas); i++)
        {
            if (ch == sMinusculas[i][0])
            {
                ch = sMinusculas[i][1];
                break;
            }
        }
        *dest++ = ch;
    }
    *dest = EOS;
}

// "<Aba>: F de V" (V = ativas não perdidas da aba) e a barra com F/V preenchido.
static void DesenharRodape(struct ConquistasTela *t)
{
    u8 feitas, validas;
    u16 cheia;

    Conquistas_ContarAba(t->aba, &feitas, &validas);
    NomeDaAbaNoRodape(gStringVar1, t->aba);
    ConvertIntToDecimalStringN(gStringVar2, feitas, STR_CONV_MODE_LEFT_ALIGN, 2);
    ConvertIntToDecimalStringN(gStringVar3, validas, STR_CONV_MODE_LEFT_ALIGN, 2);
    StringExpandPlaceholders(gStringVar4, gText_ConqTela_Rodape);

    FillWindowPixelBuffer(WIN_RODAPE, PIXEL_FILL(COR_FUNDO));
    FillWindowPixelRect(WIN_RODAPE, PIXEL_FILL(COR_LINHA), 0, 0, DISPLAY_WIDTH, 1);
    AddTextPrinterParameterized4(WIN_RODAPE, FONT_NORMAL, RODAPE_TEXTO_X, 2, 0, 0, sCor_Texto, TEXT_SKIP_DRAW,
                                 gStringVar4);
    FillWindowPixelRect(WIN_RODAPE, PIXEL_FILL(COR_LINHA), BARRA_X, BARRA_Y, BARRA_LARGURA, BARRA_ALTURA);
    FillWindowPixelRect(WIN_RODAPE, PIXEL_FILL(COR_BARRA_VAZIA), BARRA_X + 1, BARRA_Y + 1, BARRA_LARGURA - 2,
                        BARRA_ALTURA - 2);
    cheia = validas == 0 ? 0 : (BARRA_LARGURA - 2) * feitas / validas;
    if (cheia > 0)
        FillWindowPixelRect(WIN_RODAPE, PIXEL_FILL(COR_BARRA_CHEIA), BARRA_X + 1, BARRA_Y + 1, cheia, BARRA_ALTURA - 2);
    PutWindowTilemap(WIN_RODAPE);
    CopyWindowToVram(WIN_RODAPE, COPYWIN_FULL);
}

// Atalho da esteira (TEST_CMD_CONQ_TELA).
u32 Conquistas_TestGetState(void)
{
    struct ConquistasTela *t = GetTela(NULL);

    if (t == NULL)
        return 0xFFFFFFFF;
    return t->modo | t->aba << 8 | t->topo << 16 | t->inputReady << 24;
}
