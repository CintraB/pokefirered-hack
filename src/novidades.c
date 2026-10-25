#include "global.h"
#include "gflib.h"
#include "item_menu_icons.h"
#include "menu.h"
#include "novidades.h"
#include "overworld.h"
#include "quest_log.h"
#include "scanline_effect.h"
#include "script.h"
#include "task.h"
#include "constants/songs.h"

// Tela de novidades do Prof. Carvalho (docs/superpowers/specs/2026-10-17-novidades-professor-design.md).
// Tela de tópicos (layout C do mockup): barra vermelha em cima, grade com os 11 tópicos em quadros com o
// ícone de cada um e, embaixo, o nome do tópico sob o cursor. A abre o tópico (cartões: Task 3), B volta ao
// campo continuando o script que chamou `special OpenNovidadesScreen`.
//
// Memória: tudo num bloco AllocZeroed apontado por sNovidades (o único EWRAM_DATA; a EWRAM está em
// ~99,58%), liberado na saída junto com os sprites e as paletas dos ícones.

#define NOVIDADES_GRID_COLUMNS   4
#define NOVIDADES_GRID_ROWS      ((NOVIDADES_TOPIC_COUNT + NOVIDADES_GRID_COLUMNS - 1) / NOVIDADES_GRID_COLUMNS)

// Quadro de cada tópico: 5 x 4 tiles (40 x 32 px), ícone de 24 x 24 no centro.
// Colunas em x = 2, 9, 16, 23 (margens e espaços de 2 tiles); linhas em y = 3, 8, 13.
#define PANEL_WIDTH     5
#define PANEL_HEIGHT    4
#define PANEL_LEFT      2
#define PANEL_TOP       3
#define PANEL_STEP_X    7
#define PANEL_STEP_Y    5

#define TAG_NOVIDADES_ICON 0x5A00  // + topicId: tiles e paleta de cada ícone

enum {
    BG_TEXT,
    BG_FUNDO,
};

enum {
    WIN_TITLE,
    WIN_TOPIC_NAME,
    WIN_COUNT
};

// Tiles de graphics/novidades/fundo.png
enum {
    TILE_EMPTY,
    TILE_BAR,
    TILE_WHITE,
    TILE_NAME_BOX_TOP,
    TILE_BAR_BOTTOM,
    TILE_PANEL_TL,
    TILE_PANEL_TOP,
    TILE_PANEL_TR,
    TILE_PANEL_LEFT,
    TILE_PANEL_RIGHT,
    TILE_PANEL_BL,
    TILE_PANEL_BOTTOM,
    TILE_PANEL_BR,
};

// Paletas do BG: 0 = fundo.pal; 1 = a mesma com a borda (cor 6) em vermelho, para o quadro selecionado
#define PAL_NORMAL   0
#define PAL_SELECTED 1
#define COLOR_BORDER 6
#define COLOR_RED    4

struct Novidades
{
    u8 initState;
    u8 inputReady;
    u8 cursor;
    u8 iconSpriteIds[NOVIDADES_TOPIC_COUNT];
    u16 tilemapBuffer[0x400];
};

static EWRAM_DATA struct Novidades *sNovidades = NULL;

static void CB2_OpenNovidades(void);
static void CB2_Novidades(void);
static void VBlankCB_Novidades(void);
static void Task_Novidades_Init(u8 taskId);
static void Task_Novidades_HandleInput(u8 taskId);
static void Task_Novidades_Exit(u8 taskId);
static void Novidades_InitScreen(void);
static void Novidades_DrawBackground(void);
static void Novidades_DrawPanel(u8 topicId, u8 palette);
static void Novidades_CreateIcons(void);
static void Novidades_DestroyIcons(void);
static u16 Novidades_GetIconItemId(u8 topicId);
static void Novidades_PrintTitle(void);
static void Novidades_PrintTopicName(void);
static bool8 Novidades_MoveCursor(void);
static void Novidades_OpenTopic(u8 topicId);

static const u32 sFundo_Gfx[] = INCBIN_U32("graphics/novidades/fundo.4bpp");
static const u16 sFundo_Pal[] = INCBIN_U16("graphics/novidades/fundo.gbapal");

static const u8 sText_Title[] = _("NOVIDADES DE KANTO");
static const u8 sText_Controls[] = _("{A_BUTTON}VER  {B_BUTTON}SAIR");

// {fundo, letra, sombra}; fundo 0 = transparente (aparece o BG de baixo)
static const u8 sTextColors_Bar[3] = {0, 1, 5};
static const u8 sTextColors_NameBox[3] = {0, 2, 3};

static const struct BgTemplate sBgTemplates[] = {
    {
        .bg = BG_TEXT,
        .charBaseIndex = 0,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0,
    }, {
        .bg = BG_FUNDO,
        .charBaseIndex = 1,
        .mapBaseIndex = 30,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 1,
        .baseTile = 0,
    }
};

static const struct WindowTemplate sWindowTemplates[WIN_COUNT + 1] = {
    [WIN_TITLE] = {
        .bg = BG_TEXT,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = 30,
        .height = 2,
        .paletteNum = PAL_NORMAL,
        .baseBlock = 0x001,
    },
    // Nome do tópico sob o cursor, centralizado na caixa branca de baixo (linhas 17-19)
    [WIN_TOPIC_NAME] = {
        .bg = BG_TEXT,
        .tilemapLeft = (30 - NOVIDADES_TOPIC_NAME_WIDTH_PX / 8) / 2,
        .tilemapTop = 18,
        .width = NOVIDADES_TOPIC_NAME_WIDTH_PX / 8,
        .height = 2,
        .paletteNum = PAL_NORMAL,
        .baseBlock = 0x001 + 30 * 2,
    },
    [WIN_COUNT] = DUMMY_WIN_TEMPLATE
};

// Special: como o ShowDiploma, só troca o callback; a tela monta no próximo quadro, fora do script de campo.
// O script escurece antes (`fadescreen FADE_TO_BLACK`) e espera a volta com `waitstate`.
void OpenNovidadesScreen(void)
{
    QuestLog_CutRecording();
    SetMainCallback2(CB2_OpenNovidades);
    LockPlayerFieldControls();
}

static void CB2_OpenNovidades(void)
{
    sNovidades = AllocZeroed(sizeof(*sNovidades));
    memset(sNovidades->iconSpriteIds, MAX_SPRITES, sizeof(sNovidades->iconSpriteIds));
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();
    ResetTasks();
    ScanlineEffect_Stop();
    CreateTask(Task_Novidades_Init, 0);
    SetMainCallback2(CB2_Novidades);
}

static void CB2_Novidades(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void VBlankCB_Novidades(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void Task_Novidades_Init(u8 taskId)
{
    switch (sNovidades->initState)
    {
    case 0:
        SetVBlankCallback(NULL);
        Novidades_InitScreen();
        break;
    case 1:
        LoadBgTiles(BG_FUNDO, sFundo_Gfx, sizeof(sFundo_Gfx), 0);
        LoadPalette(sFundo_Pal, BG_PLTT_ID(PAL_NORMAL), PLTT_SIZE_4BPP);
        LoadPalette(sFundo_Pal, BG_PLTT_ID(PAL_SELECTED), PLTT_SIZE_4BPP);
        LoadPalette(&sFundo_Pal[COLOR_RED], BG_PLTT_ID(PAL_SELECTED) + COLOR_BORDER, PLTT_SIZEOF(1));
        break;
    case 2:
        Novidades_DrawBackground();
        Novidades_PrintTitle();
        Novidades_PrintTopicName();
        break;
    case 3:
        Novidades_CreateIcons();
        CopyBgTilemapBufferToVram(BG_TEXT);
        CopyBgTilemapBufferToVram(BG_FUNDO);
        break;
    case 4:
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        SetVBlankCallback(VBlankCB_Novidades);
        break;
    default:
        if (gPaletteFade.active)
            return;
        sNovidades->inputReady = TRUE;
        gTasks[taskId].func = Task_Novidades_HandleInput;
        return;
    }
    sNovidades->initState++;
}

static void Task_Novidades_HandleInput(u8 taskId)
{
    if (JOY_NEW(A_BUTTON))
    {
        Novidades_OpenTopic(sNovidades->cursor);
    }
    else if (JOY_NEW(B_BUTTON))
    {
        PlaySE(SE_SELECT);
        sNovidades->inputReady = FALSE;
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        gTasks[taskId].func = Task_Novidades_Exit;
    }
    else if (JOY_REPT(DPAD_ANY))
    {
        u8 prev = sNovidades->cursor;
        if (Novidades_MoveCursor())
        {
            PlaySE(SE_SELECT);
            Novidades_DrawPanel(prev, PAL_NORMAL);
            Novidades_DrawPanel(sNovidades->cursor, PAL_SELECTED);
            CopyBgTilemapBufferToVram(BG_FUNDO);
            Novidades_PrintTopicName();
        }
    }
}

static void Task_Novidades_Exit(u8 taskId)
{
    if (gPaletteFade.active)
        return;
    Novidades_DestroyIcons();
    FreeAllWindowBuffers();
    DestroyTask(taskId);
    FREE_AND_SET_NULL(sNovidades);
    SetMainCallback2(CB2_ReturnToFieldContinueScript);
}

// Grade de 4 colunas, a última linha incompleta (11 = 4 + 4 + 3). ◀▶ andam dentro da linha e ▲▼ entre
// as linhas, sem dar a volta; ▼ para um quadro vazio vai ao último tópico. Devolve se o cursor mudou.
static bool8 Novidades_MoveCursor(void)
{
    u8 cursor = sNovidades->cursor;
    u8 column = cursor % NOVIDADES_GRID_COLUMNS;
    u8 row = cursor / NOVIDADES_GRID_COLUMNS;

    if (JOY_REPT(DPAD_LEFT))
    {
        if (column > 0)
            cursor--;
    }
    else if (JOY_REPT(DPAD_RIGHT))
    {
        if (column < NOVIDADES_GRID_COLUMNS - 1 && cursor + 1 < NOVIDADES_TOPIC_COUNT)
            cursor++;
    }
    else if (JOY_REPT(DPAD_UP))
    {
        if (row > 0)
            cursor -= NOVIDADES_GRID_COLUMNS;
    }
    else if (JOY_REPT(DPAD_DOWN))
    {
        if (cursor + NOVIDADES_GRID_COLUMNS < NOVIDADES_TOPIC_COUNT)
            cursor += NOVIDADES_GRID_COLUMNS;
        else if (row < NOVIDADES_GRID_ROWS - 1)
            cursor = NOVIDADES_TOPIC_COUNT - 1;
    }
    if (cursor == sNovidades->cursor)
        return FALSE;
    sNovidades->cursor = cursor;
    return TRUE;
}

// Cartões do tópico: entram na Task 3. Por ora só confirma o botão.
static void Novidades_OpenTopic(u8 topicId)
{
    PlaySE(SE_SELECT);
}

static void Novidades_InitScreen(void)
{
    DmaClearLarge16(3, (void *)VRAM, VRAM_SIZE, 0x1000);
    DmaClear32(3, (void *)OAM, OAM_SIZE);
    DmaClear16(3, (void *)PLTT, PLTT_SIZE);
    SetGpuReg(REG_OFFSET_DISPCNT, 0);
    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sBgTemplates, ARRAY_COUNT(sBgTemplates));
    ChangeBgX(BG_TEXT, 0, BG_COORD_SET);
    ChangeBgY(BG_TEXT, 0, BG_COORD_SET);
    ChangeBgX(BG_FUNDO, 0, BG_COORD_SET);
    ChangeBgY(BG_FUNDO, 0, BG_COORD_SET);
    InitWindows(sWindowTemplates);
    DeactivateAllTextPrinters();
    SetBgTilemapBuffer(BG_FUNDO, sNovidades->tilemapBuffer);
    FillBgTilemapBufferRect_Palette0(BG_TEXT, 0, 0, 0, 32, 32);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_1D_MAP | DISPCNT_OBJ_ON);
    ShowBg(BG_TEXT);
    ShowBg(BG_FUNDO);
}

static void Novidades_DrawBackground(void)
{
    u8 i;

    FillBgTilemapBufferRect(BG_FUNDO, TILE_EMPTY, 0, 0, 32, 32, PAL_NORMAL);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR, 0, 0, 30, 1, PAL_NORMAL);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR_BOTTOM, 0, 1, 30, 1, PAL_NORMAL);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_NAME_BOX_TOP, 0, 17, 30, 1, PAL_NORMAL);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_WHITE, 0, 18, 30, 2, PAL_NORMAL);
    for (i = 0; i < NOVIDADES_TOPIC_COUNT; i++)
        Novidades_DrawPanel(i, i == sNovidades->cursor ? PAL_SELECTED : PAL_NORMAL);
}

static void Novidades_DrawPanel(u8 topicId, u8 palette)
{
    u8 x = PANEL_LEFT + (topicId % NOVIDADES_GRID_COLUMNS) * PANEL_STEP_X;
    u8 y = PANEL_TOP + (topicId / NOVIDADES_GRID_COLUMNS) * PANEL_STEP_Y;
    u8 right = x + PANEL_WIDTH - 1;
    u8 bottom = y + PANEL_HEIGHT - 1;

    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_TL, x, y, 1, 1, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_TOP, x + 1, y, PANEL_WIDTH - 2, 1, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_TR, right, y, 1, 1, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_LEFT, x, y + 1, 1, PANEL_HEIGHT - 2, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_WHITE, x + 1, y + 1, PANEL_WIDTH - 2, PANEL_HEIGHT - 2, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_RIGHT, right, y + 1, 1, PANEL_HEIGHT - 2, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_BL, x, bottom, 1, 1, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_BOTTOM, x + 1, bottom, PANEL_WIDTH - 2, 1, palette);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_PANEL_BR, right, bottom, 1, 1, palette);
}

// iconCustom != 0: ícone novo da Task 4 (1 relógio, 2 clima, 3 cartucho, 4 ficha).
// PROVISÓRIO até a Task 4: esses tópicos mostram o iconItemId (ícone de item) que o JSON traz para eles.
static u16 Novidades_GetIconItemId(u8 topicId)
{
    return gNovidadesTopics[topicId].iconItemId;
}

static void Novidades_CreateIcons(void)
{
    u8 i;

    for (i = 0; i < NOVIDADES_TOPIC_COUNT; i++)
    {
        u8 spriteId = AddItemIconObject(TAG_NOVIDADES_ICON + i, TAG_NOVIDADES_ICON + i, Novidades_GetIconItemId(i));
        sNovidades->iconSpriteIds[i] = spriteId;
        if (spriteId == MAX_SPRITES)
            continue;
        // O ícone (24 x 24) fica no canto do sprite de 32 x 32 centrado em x/y: +4 põe o ícone no meio do quadro
        gSprites[spriteId].x = (PANEL_LEFT + (i % NOVIDADES_GRID_COLUMNS) * PANEL_STEP_X) * 8 + PANEL_WIDTH * 4 + 4;
        gSprites[spriteId].y = (PANEL_TOP + (i / NOVIDADES_GRID_COLUMNS) * PANEL_STEP_Y) * 8 + PANEL_HEIGHT * 4 + 4;
    }
}

static void Novidades_DestroyIcons(void)
{
    u8 i;

    for (i = 0; i < NOVIDADES_TOPIC_COUNT; i++)
    {
        if (sNovidades->iconSpriteIds[i] != MAX_SPRITES)
            DestroySpriteAndFreeResources(&gSprites[sNovidades->iconSpriteIds[i]]);
        sNovidades->iconSpriteIds[i] = MAX_SPRITES;
    }
}

static void Novidades_PrintTitle(void)
{
    FillWindowPixelBuffer(WIN_TITLE, PIXEL_FILL(0));
    AddTextPrinterParameterized4(WIN_TITLE, FONT_NORMAL, 4, 1, 0, 0, sTextColors_Bar, TEXT_SKIP_DRAW, sText_Title);
    AddTextPrinterParameterized4(WIN_TITLE, FONT_SMALL, 30 * 8 - 4 - GetStringWidth(FONT_SMALL, sText_Controls, 0), 2,
                                 0, 0, sTextColors_Bar, TEXT_SKIP_DRAW, sText_Controls);
    PutWindowTilemap(WIN_TITLE);
    CopyWindowToVram(WIN_TITLE, COPYWIN_FULL);
}

static void Novidades_PrintTopicName(void)
{
    const u8 *name = gNovidadesTopics[sNovidades->cursor].name;
    s32 x = (NOVIDADES_TOPIC_NAME_WIDTH_PX - GetStringWidth(FONT_NORMAL, name, 0)) / 2;

    if (x < 0)
        x = 0;
    FillWindowPixelBuffer(WIN_TOPIC_NAME, PIXEL_FILL(0));
    AddTextPrinterParameterized4(WIN_TOPIC_NAME, FONT_NORMAL, x, 1, 0, 0, sTextColors_NameBox, TEXT_SKIP_DRAW, name);
    PutWindowTilemap(WIN_TOPIC_NAME);
    CopyWindowToVram(WIN_TOPIC_NAME, COPYWIN_FULL);
}

#if TESTBUILD
// Atalho da esteira (TEST_CMD_NOVIDADES_STATE): 0xFFFFFFFF = tela fechada; senão
// cursor | pronta para input << 8 | ícones vivos << 16.
u32 Novidades_TestGetState(void)
{
    u8 i, icons = 0;

    if (sNovidades == NULL)
        return 0xFFFFFFFF;
    for (i = 0; i < NOVIDADES_TOPIC_COUNT; i++)
    {
        if (sNovidades->iconSpriteIds[i] != MAX_SPRITES && gSprites[sNovidades->iconSpriteIds[i]].inUse)
            icons++;
    }
    return sNovidades->cursor | sNovidades->inputReady << 8 | icons << 16;
}
#endif // TESTBUILD
