#include "global.h"
#include "gflib.h"
#include "item_menu_icons.h"
#include "menu.h"
#include "menu_helpers.h"
#include "new_menu_helpers.h"
#include "novidades.h"
#include "overworld.h"
#include "quest_log.h"
#include "scanline_effect.h"
#include "script.h"
#include "task.h"
#include "trainer_pokemon_sprites.h"
#include "constants/items.h"
#include "constants/songs.h"

// Tela de novidades do Prof. Carvalho (docs/superpowers/specs/2026-10-17-novidades-professor-design.md).
// Tela de tópicos (layout C do mockup): barra vermelha em cima, grade com os 11 tópicos em quadros com o
// ícone de cada um e, embaixo, o nome do tópico sob o cursor. A abre o tópico, B volta ao campo
// continuando o script que chamou `special OpenNovidadesScreen`.
// Cartão (layout B): barra com o título, a posição ("3/15") e as setas; imagem (duas espécies com a seta,
// uma espécie, um item ou o ícone do tópico); a linha "ANTES ... AGORA ..." quando houver; o corpo.
// ◀▶ passa de cartão, B volta à grade com o cursor no mesmo tópico.
//
// Memória: tudo num bloco AllocZeroed apontado por sNovidades (o único EWRAM_DATA; a EWRAM está em
// ~99,58%), liberado na saída junto com os sprites e as paletas.

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

// Tags de sprite. Os ícones de item são liberados sempre por tag: o AddItemIconObject cria o template
// numa variável local, então o sprite->template não serve para soltar tiles e paleta.
#define TAG_NOVIDADES_ICON      0x5A00  // + topicId: tiles e paleta de cada ícone da grade
#define TAG_NOVIDADES_CARD_ICON 0x5A20  // ícone do cartão (item ou ícone do tópico): tiles e paleta
#define TAG_NOVIDADES_PIC       0x5A21  // + 0/1: paleta reservada de cada Pokémon do cartão (tiles dinâmicos)
STATIC_ASSERT(TAG_NOVIDADES_ICON + NOVIDADES_TOPIC_COUNT <= TAG_NOVIDADES_CARD_ICON, NovidadesIconTagsCollide);

// Pokémon do cartão: cores normais. Brilho = (otId alto ^ otId baixo ^ pers. alto ^ pers. baixo) < SHINY_ODDS;
// com otId 0, a personalidade 0x0000FFFF dá 0xFFFF, nunca shiny.
#define NOVIDADES_PIC_OTID        0
#define NOVIDADES_PIC_PERSONALITY 0x0000FFFF

#define DISPLAY_TILE_WIDTH  (DISPLAY_WIDTH / 8)
#define DISPLAY_TILE_HEIGHT (DISPLAY_HEIGHT / 8)

// Cartão, de cima para baixo (include/novidades.h: 16 + 64 + 13 + 5 * 13 = 158 px):
//   linhas 0-1  barra: título (FONT_NORMAL, x = CARD_TITLE_X), ◀ "3/15" ▶ à direita
//   linhas 2-9  imagem (64 px): sprites de 64 x 64 centrados em y = CARD_IMAGE_Y
//   linhas 10-19 WIN_CARD_TEXT: "ANTES" e "AGORA" (FONT_SMALL, 13 px) e a caixa branca do corpo
#define CARD_TITLE_X        4
#define CARD_ARROW_LEFT_X   22   // coluna do ◀ na barra
#define CARD_POS_LEFT       23   // janela da posição: colunas 23-27
#define CARD_POS_WIDTH      5
#define CARD_ARROW_RIGHT_X  28   // coluna do ▶
#define CARD_IMAGE_Y        48   // centro da área da imagem (linhas 2-9 = y 16..79)
#define CARD_MON_LEFT_X     72   // duas espécies: centros em 72 e 168, a seta grande no meio (x 112..127)
#define CARD_MON_RIGHT_X    168
#define CARD_BIG_ARROW_X    14   // seta grande: tiles 14-15, linhas 5-6 (y 40..55)
#define CARD_BIG_ARROW_Y    5
#define CARD_TEXT_TOP       10
#define CARD_TEXT_HEIGHT    10
#define CARD_CHIPS_X        8    // ANTES em x = 8, AGORA em x = 8 + 112 (dentro da janela, que começa em 0)
#define CARD_CHIP_HEIGHT    NOVIDADES_BODY_LINE_HEIGHT_PX
#define CARD_BOX_TOP        (CARD_CHIP_HEIGHT + 1)   // linha da borda da caixa branca (1 px de creme antes)
#define CARD_BODY_X         ((DISPLAY_WIDTH - NOVIDADES_BODY_WIDTH_PX) / 2)
#define CARD_BODY_Y         (CARD_BOX_TOP + 1)

STATIC_ASSERT(CARD_CHIPS_X + 2 * NOVIDADES_BEFORE_AFTER_WIDTH_PX <= DISPLAY_WIDTH, NovidadesChipsFit);
STATIC_ASSERT(CARD_BODY_X + NOVIDADES_BODY_WIDTH_PX <= DISPLAY_WIDTH, NovidadesBodyFitsWidth);
STATIC_ASSERT(CARD_BODY_Y + NOVIDADES_BODY_LINES * NOVIDADES_BODY_LINE_HEIGHT_PX <= CARD_TEXT_HEIGHT * 8, NovidadesBodyFitsHeight);
STATIC_ASSERT(CARD_TEXT_TOP + CARD_TEXT_HEIGHT <= DISPLAY_TILE_HEIGHT, NovidadesCardTextFitsScreen);
STATIC_ASSERT(CARD_TITLE_X + NOVIDADES_TITLE_WIDTH_PX <= CARD_ARROW_LEFT_X * 8, NovidadesTitleBeforeArrows);

enum {
    BG_TEXT,
    BG_FUNDO,
};

enum {
    WIN_TITLE,
    WIN_TOPIC_NAME,
    WIN_CARD_TITLE,
    WIN_CARD_POS,
    WIN_CARD_TEXT,
    WIN_COUNT
};

enum {
    VIEW_GRID,
    VIEW_CARD,
};

// Imagem do cartão (Novidades_TestGetCard devolve este número)
enum {
    CARD_IMAGE_TOPIC_ICON,
    CARD_IMAGE_ITEM,
    CARD_IMAGE_ONE_MON,
    CARD_IMAGE_TWO_MONS,
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
    TILE_BAR_ARROW_LEFT,      // + 1: metade de baixo (sobre a faixa escura da barra)
    TILE_BAR_ARROW_LEFT_BOTTOM,
    TILE_BAR_ARROW_RIGHT,
    TILE_BAR_ARROW_RIGHT_BOTTOM,
    TILE_BIG_ARROW,           // 2 x 2: TL, TR, BL, BR
};

// Paletas do BG: 0 = fundo.pal; 1 = a mesma com a borda (cor 6) em vermelho, para o quadro selecionado
#define PAL_NORMAL   0
#define PAL_SELECTED 1
#define COLOR_WHITE  1
#define COLOR_BORDER 6
#define COLOR_NAVY   7
#define COLOR_RED    4

struct Novidades
{
    u8 initState;
    u8 inputReady;
    u8 cursor;
    u8 view;                // VIEW_GRID / VIEW_CARD
    u8 card;                // cartão aberto do tópico sob o cursor
    u8 cardImage;           // CARD_IMAGE_*
    u8 iconSpriteIds[NOVIDADES_TOPIC_COUNT];
    u8 cardSpriteIds[2];    // Pokémon (antes, depois) ou o ícone em [0]; MAX_SPRITES = vazio
    u16 tilemapBuffer[0x400];
};

static EWRAM_DATA struct Novidades *sNovidades = NULL;

static void CB2_OpenNovidades(void);
static void CB2_Novidades(void);
static void VBlankCB_Novidades(void);
static void Task_Novidades_Init(u8 taskId);
static void Task_Novidades_HandleInput(u8 taskId);
static void Task_Novidades_CardInput(u8 taskId);
static void Task_Novidades_Exit(u8 taskId);
static void Novidades_InitScreen(void);
static void Novidades_DrawBackground(void);
static void Novidades_DrawPanel(u8 topicId, u8 palette);
static void Novidades_CreateIcons(void);
static void Novidades_DestroyIcons(void);
static void Novidades_PrintTitle(void);
static void Novidades_PrintTopicName(void);
static bool8 Novidades_MoveCursor(void);
static void Novidades_OpenTopic(u8 topicId);
static void Novidades_ShowCardView(void);
static void Novidades_ShowGridView(void);
static void Novidades_ShowCard(void);
static bool8 Novidades_MoveCard(void);
static void Novidades_DrawCardBar(void);
static void Novidades_PrintCardTitle(void);
static void Novidades_PrintCardPosition(void);
static void Novidades_PrintCardText(void);
static void Novidades_CreateCardImage(void);
static u8 Novidades_CreateMonPic(u16 species, u8 index, s16 x);
static void Novidades_DestroyCardImage(void);

static const u32 sFundo_Gfx[] = INCBIN_U32("graphics/novidades/fundo.4bpp");
static const u16 sFundo_Pal[] = INCBIN_U16("graphics/novidades/fundo.gbapal");

static const u8 sText_Title[] = _("NOVIDADES DE KANTO");
static const u8 sText_Controls[] = _("{A_BUTTON}VER  {B_BUTTON}SAIR");

// {fundo, letra, sombra}; fundo 0 = transparente (aparece o BG de baixo)
static const u8 sTextColors_Bar[3] = {0, 1, 5};
static const u8 sTextColors_NameBox[3] = {0, 2, 3};
static const u8 sTextColors_Chip[3] = {COLOR_NAVY, COLOR_WHITE, COLOR_NAVY};
static const u8 sTextColors_Body[3] = {COLOR_WHITE, 2, 3};

// Ícone do cartão em dobro (24 x 24 vira 48 x 48): sprite de 32 x 32 afim, área dupla
static const struct OamData sOamData_CardIcon = {
    .affineMode = ST_OAM_AFFINE_DOUBLE,
    .shape = SPRITE_SHAPE(32x32),
    .size = SPRITE_SIZE(32x32),
    .priority = 1,
};

static const union AffineAnimCmd sAffineAnim_CardIcon[] = {
    AFFINEANIMCMD_FRAME(0x200, 0x200, 0, 0),
    AFFINEANIMCMD_END
};

static const union AffineAnimCmd *const sAffineAnims_CardIcon[] = {
    sAffineAnim_CardIcon
};

static const struct SpriteTemplate sSpriteTemplate_CardIcon = {
    .tileTag = TAG_NOVIDADES_CARD_ICON,
    .paletteTag = TAG_NOVIDADES_CARD_ICON,
    .oam = &sOamData_CardIcon,
    .anims = gDummySpriteAnimTable,
    .images = NULL,
    .affineAnims = sAffineAnims_CardIcon,
    .callback = SpriteCallbackDummy
};

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

// As janelas da grade e as do cartão dividem linhas da tela; só as da visão atual ficam no tilemap.
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
    // Título do cartão na barra: NOVIDADES_TITLE_WIDTH_PX a partir de x = CARD_TITLE_X
    [WIN_CARD_TITLE] = {
        .bg = BG_TEXT,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = (CARD_TITLE_X + NOVIDADES_TITLE_WIDTH_PX + 7) / 8,
        .height = 2,
        .paletteNum = PAL_NORMAL,
        .baseBlock = 0x001 + 30 * 2 + (NOVIDADES_TOPIC_NAME_WIDTH_PX / 8) * 2,
    },
    // "3/15", entre as setas da barra
    [WIN_CARD_POS] = {
        .bg = BG_TEXT,
        .tilemapLeft = CARD_POS_LEFT,
        .tilemapTop = 0,
        .width = CARD_POS_WIDTH,
        .height = 2,
        .paletteNum = PAL_NORMAL,
        .baseBlock = 0x001 + 30 * 2 + (NOVIDADES_TOPIC_NAME_WIDTH_PX / 8) * 2
                   + (CARD_TITLE_X + NOVIDADES_TITLE_WIDTH_PX + 7) / 8 * 2,
    },
    // ANTES/AGORA e o corpo (a caixa branca é desenhada em pixels, na mesma janela)
    [WIN_CARD_TEXT] = {
        .bg = BG_TEXT,
        .tilemapLeft = 0,
        .tilemapTop = CARD_TEXT_TOP,
        .width = DISPLAY_TILE_WIDTH,
        .height = CARD_TEXT_HEIGHT,
        .paletteNum = PAL_NORMAL,
        .baseBlock = 0x001 + 30 * 2 + (NOVIDADES_TOPIC_NAME_WIDTH_PX / 8) * 2
                   + (CARD_TITLE_X + NOVIDADES_TITLE_WIDTH_PX + 7) / 8 * 2 + CARD_POS_WIDTH * 2,
    },
    [WIN_COUNT] = DUMMY_WIN_TEMPLATE
};

// Os tiles das janelas cabem no bloco de caracteres 0 do BG0 (512 tiles; o fundo usa o bloco 1)
STATIC_ASSERT(0x001 + 30 * 2 + (NOVIDADES_TOPIC_NAME_WIDTH_PX / 8) * 2 + (CARD_TITLE_X + NOVIDADES_TITLE_WIDTH_PX + 7) / 8 * 2
              + CARD_POS_WIDTH * 2 + DISPLAY_TILE_WIDTH * CARD_TEXT_HEIGHT <= 512, NovidadesWindowsFitCharBlock);

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
    SetVBlankHBlankCallbacksToNull();
    ClearScheduledBgCopiesToVram();
    sNovidades = AllocZeroed(sizeof(*sNovidades));
    memset(sNovidades->iconSpriteIds, MAX_SPRITES, sizeof(sNovidades->iconSpriteIds));
    memset(sNovidades->cardSpriteIds, MAX_SPRITES, sizeof(sNovidades->cardSpriteIds));
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
        PlaySE(SE_SELECT);
        Novidades_OpenTopic(sNovidades->cursor);
        gTasks[taskId].func = Task_Novidades_CardInput;
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

static void Task_Novidades_CardInput(u8 taskId)
{
    if (JOY_NEW(B_BUTTON))
    {
        PlaySE(SE_SELECT);
        Novidades_ShowGridView();
        gTasks[taskId].func = Task_Novidades_HandleInput;
    }
    else if (JOY_REPT(DPAD_LEFT | DPAD_RIGHT))
    {
        if (Novidades_MoveCard())
        {
            PlaySE(SE_SELECT);
            Novidades_ShowCard();
        }
    }
}

static void Task_Novidades_Exit(u8 taskId)
{
    if (gPaletteFade.active)
        return;
    Novidades_DestroyCardImage();
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

// A na grade: abre o tópico no primeiro cartão.
static void Novidades_OpenTopic(u8 topicId)
{
    sNovidades->cursor = topicId;
    sNovidades->card = 0;
    Novidades_ShowCardView();
}

// Regra do limite (Review Focus 5): ◀ no primeiro cartão e ▶ no último não fazem nada, sem dar a volta,
// igual ao cursor da grade; num tópico de um cartão só, ◀▶ ficam parados. Devolve se o cartão mudou.
static bool8 Novidades_MoveCard(void)
{
    const struct NovidadesTopic *topic = &gNovidadesTopics[sNovidades->cursor];
    u8 card = sNovidades->card;

    if (JOY_REPT(DPAD_LEFT))
    {
        if (card > 0)
            card--;
    }
    else if (JOY_REPT(DPAD_RIGHT))
    {
        if (card + 1 < topic->cardCount)
            card++;
    }
    if (card == sNovidades->card)
        return FALSE;
    sNovidades->card = card;
    return TRUE;
}

// Grade -> cartão. Os ícones da grade saem enquanto o cartão está aberto (sobram paletas de OBJ: o
// cartão usa no máximo 2, as duas espécies, ou 1, o ícone) e voltam na volta à grade.
static void Novidades_ShowCardView(void)
{
    sNovidades->view = VIEW_CARD;
    Novidades_DestroyIcons();
    ClearWindowTilemap(WIN_TITLE);
    ClearWindowTilemap(WIN_TOPIC_NAME);
    Novidades_ShowCard();
}

// Cartão -> grade, com o cursor no tópico que estava aberto.
static void Novidades_ShowGridView(void)
{
    sNovidades->view = VIEW_GRID;
    Novidades_DestroyCardImage();
    ClearWindowTilemap(WIN_CARD_TITLE);
    ClearWindowTilemap(WIN_CARD_POS);
    ClearWindowTilemap(WIN_CARD_TEXT);
    Novidades_DrawBackground();
    Novidades_PrintTitle();
    Novidades_PrintTopicName();
    Novidades_CreateIcons();
    CopyBgTilemapBufferToVram(BG_TEXT);
    CopyBgTilemapBufferToVram(BG_FUNDO);
}

// Desenha o cartão sNovidades->card do tópico sob o cursor, soltando antes a imagem do anterior.
static void Novidades_ShowCard(void)
{
    Novidades_DestroyCardImage();
    Novidades_DrawCardBar();
    Novidades_PrintCardTitle();
    Novidades_PrintCardPosition();
    Novidades_PrintCardText();
    Novidades_CreateCardImage();
    CopyBgTilemapBufferToVram(BG_TEXT);
    CopyBgTilemapBufferToVram(BG_FUNDO);
}

// Fundo do cartão: creme, barra vermelha com ◀ e ▶ (somem no primeiro e no último cartão) e, quando a
// imagem é "antes ➜ depois", a seta grande entre as duas espécies.
static void Novidades_DrawCardBar(void)
{
    const struct NovidadesTopic *topic = &gNovidadesTopics[sNovidades->cursor];
    const struct NovidadesCard *card = &topic->cards[sNovidades->card];

    FillBgTilemapBufferRect(BG_FUNDO, TILE_EMPTY, 0, 0, 32, 32, PAL_NORMAL);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR, 0, 0, 30, 1, PAL_NORMAL);
    FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR_BOTTOM, 0, 1, 30, 1, PAL_NORMAL);
    if (sNovidades->card > 0)
    {
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR_ARROW_LEFT, CARD_ARROW_LEFT_X, 0, 1, 1, PAL_NORMAL);
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR_ARROW_LEFT_BOTTOM, CARD_ARROW_LEFT_X, 1, 1, 1, PAL_NORMAL);
    }
    if (sNovidades->card + 1 < topic->cardCount)
    {
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR_ARROW_RIGHT, CARD_ARROW_RIGHT_X, 0, 1, 1, PAL_NORMAL);
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BAR_ARROW_RIGHT_BOTTOM, CARD_ARROW_RIGHT_X, 1, 1, 1, PAL_NORMAL);
    }
    if (card->speciesBefore != SPECIES_NONE && card->speciesAfter != SPECIES_NONE)
    {
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BIG_ARROW + 0, CARD_BIG_ARROW_X, CARD_BIG_ARROW_Y, 1, 1, PAL_NORMAL);
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BIG_ARROW + 1, CARD_BIG_ARROW_X + 1, CARD_BIG_ARROW_Y, 1, 1, PAL_NORMAL);
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BIG_ARROW + 2, CARD_BIG_ARROW_X, CARD_BIG_ARROW_Y + 1, 1, 1, PAL_NORMAL);
        FillBgTilemapBufferRect(BG_FUNDO, TILE_BIG_ARROW + 3, CARD_BIG_ARROW_X + 1, CARD_BIG_ARROW_Y + 1, 1, 1, PAL_NORMAL);
    }
}

static void Novidades_PrintCardTitle(void)
{
    const struct NovidadesCard *card = &gNovidadesTopics[sNovidades->cursor].cards[sNovidades->card];

    FillWindowPixelBuffer(WIN_CARD_TITLE, PIXEL_FILL(0));
    AddTextPrinterParameterized4(WIN_CARD_TITLE, FONT_NORMAL, CARD_TITLE_X, 1, 0, 0, sTextColors_Bar,
                                 TEXT_SKIP_DRAW, card->title);
    PutWindowTilemap(WIN_CARD_TITLE);
    CopyWindowToVram(WIN_CARD_TITLE, COPYWIN_GFX);
}

// "3/15": cartão aberto / cartões do tópico, centrado entre as setas
static void Novidades_PrintCardPosition(void)
{
    u8 text[8];
    u8 *end;
    s32 x;

    end = ConvertIntToDecimalStringN(text, sNovidades->card + 1, STR_CONV_MODE_LEFT_ALIGN, 2);
    *end++ = CHAR_SLASH;
    ConvertIntToDecimalStringN(end, gNovidadesTopics[sNovidades->cursor].cardCount, STR_CONV_MODE_LEFT_ALIGN, 2);
    x = (CARD_POS_WIDTH * 8 - GetStringWidth(FONT_NORMAL, text, 0)) / 2;
    if (x < 0)
        x = 0;
    FillWindowPixelBuffer(WIN_CARD_POS, PIXEL_FILL(0));
    AddTextPrinterParameterized4(WIN_CARD_POS, FONT_NORMAL, x, 1, 0, 0, sTextColors_Bar, TEXT_SKIP_DRAW, text);
    PutWindowTilemap(WIN_CARD_POS);
    CopyWindowToVram(WIN_CARD_POS, COPYWIN_GFX);
}

// ANTES e AGORA (só quando o cartão tem): dois rótulos azul-marinho de NOVIDADES_BEFORE_AFTER_WIDTH_PX
// lado a lado, texto centrado. Embaixo, a caixa branca com borda em cima e o corpo (FONT_SMALL, até
// NOVIDADES_BODY_LINES linhas de NOVIDADES_BODY_LINE_HEIGHT_PX, `\n` desce uma linha).
static void Novidades_PrintCardText(void)
{
    const struct NovidadesCard *card = &gNovidadesTopics[sNovidades->cursor].cards[sNovidades->card];

    FillWindowPixelBuffer(WIN_CARD_TEXT, PIXEL_FILL(0));
    if (card->before != NULL)
    {
        const u8 *chips[2];
        u8 i;

        chips[0] = card->before;
        chips[1] = card->after;
        for (i = 0; i < 2; i++)
        {
            u16 chipX = CARD_CHIPS_X + i * NOVIDADES_BEFORE_AFTER_WIDTH_PX;
            s32 x = chipX + (NOVIDADES_BEFORE_AFTER_WIDTH_PX - GetStringWidth(FONT_SMALL, chips[i], 0)) / 2;

            if (x < chipX)
                x = chipX;
            FillWindowPixelRect(WIN_CARD_TEXT, PIXEL_FILL(COLOR_NAVY), chipX + 1, 0,
                                NOVIDADES_BEFORE_AFTER_WIDTH_PX - 2, CARD_CHIP_HEIGHT);
            AddTextPrinterParameterized4(WIN_CARD_TEXT, FONT_SMALL, x, 0, 0, 0, sTextColors_Chip,
                                         TEXT_SKIP_DRAW, chips[i]);
        }
        // a letra pode pintar o fundo abaixo do rótulo: a faixa de creme entre ele e a caixa é refeita
        FillWindowPixelRect(WIN_CARD_TEXT, PIXEL_FILL(0), 0, CARD_CHIP_HEIGHT, DISPLAY_WIDTH, CARD_BOX_TOP - CARD_CHIP_HEIGHT);
    }
    FillWindowPixelRect(WIN_CARD_TEXT, PIXEL_FILL(COLOR_BORDER), 0, CARD_BOX_TOP, DISPLAY_WIDTH, 1);
    FillWindowPixelRect(WIN_CARD_TEXT, PIXEL_FILL(COLOR_WHITE), 0, CARD_BODY_Y, DISPLAY_WIDTH,
                        CARD_TEXT_HEIGHT * 8 - CARD_BODY_Y);
    AddTextPrinterParameterized4(WIN_CARD_TEXT, FONT_SMALL, CARD_BODY_X, CARD_BODY_Y, 0, 0, sTextColors_Body,
                                 TEXT_SKIP_DRAW, card->body);
    PutWindowTilemap(WIN_CARD_TEXT);
    CopyWindowToVram(WIN_CARD_TEXT, COPYWIN_GFX);
}

// Imagem do cartão: duas espécies (antes ➜ depois), uma espécie, o ícone do item, ou o ícone do tópico.
static void Novidades_CreateCardImage(void)
{
    const struct NovidadesCard *card = &gNovidadesTopics[sNovidades->cursor].cards[sNovidades->card];
    u8 spriteId;

    if (card->speciesBefore != SPECIES_NONE && card->speciesAfter != SPECIES_NONE)
    {
        sNovidades->cardImage = CARD_IMAGE_TWO_MONS;
        sNovidades->cardSpriteIds[0] = Novidades_CreateMonPic(card->speciesBefore, 0, CARD_MON_LEFT_X);
        sNovidades->cardSpriteIds[1] = Novidades_CreateMonPic(card->speciesAfter, 1, CARD_MON_RIGHT_X);
        return;
    }
    if (card->speciesBefore != SPECIES_NONE)
    {
        sNovidades->cardImage = CARD_IMAGE_ONE_MON;
        sNovidades->cardSpriteIds[0] = Novidades_CreateMonPic(card->speciesBefore, 0, DISPLAY_WIDTH / 2);
        return;
    }
    if (card->itemId != ITEM_NONE)
    {
        sNovidades->cardImage = CARD_IMAGE_ITEM;
        spriteId = AddItemIconObjectWithCustomObjectTemplate(&sSpriteTemplate_CardIcon, TAG_NOVIDADES_CARD_ICON,
                                                             TAG_NOVIDADES_CARD_ICON, card->itemId);
    }
    else
    {
        // ícone do tópico: o novo (relógio, clima, cartucho, ficha) ou o de item, em dobro como o item
        sNovidades->cardImage = CARD_IMAGE_TOPIC_ICON;
        spriteId = Novidades_AddTopicIconWithTemplate(&sSpriteTemplate_CardIcon, TAG_NOVIDADES_CARD_ICON,
                                                      TAG_NOVIDADES_CARD_ICON, sNovidades->cursor);
    }
    sNovidades->cardSpriteIds[0] = spriteId;
    if (spriteId == MAX_SPRITES)
        return;
    // O ícone (24 x 24) fica no canto do sprite de 32 x 32; em dobro, o centro dele fica 8 px acima e à
    // esquerda do centro do sprite.
    gSprites[spriteId].x = DISPLAY_WIDTH / 2 + 8;
    gSprites[spriteId].y = CARD_IMAGE_Y + 8;
}

// Sprite frontal de 64 x 64 centrado em (x, CARD_IMAGE_Y). A paleta vai num slot reservado pelo alocador
// com a tag TAG_NOVIDADES_PIC + index (assim não colide com os ícones), carregada por slot (TAG_NONE).
static u8 Novidades_CreateMonPic(u16 species, u8 index, s16 x)
{
    u8 slot = AllocSpritePalette(TAG_NOVIDADES_PIC + index);
    u16 spriteId;

    if (slot == 0xFF)
        return MAX_SPRITES;
    spriteId = CreateMonPicSprite(species, NOVIDADES_PIC_OTID, NOVIDADES_PIC_PERSONALITY, TRUE, x, CARD_IMAGE_Y,
                                  slot, TAG_NONE, TRUE);
    if (spriteId == 0xFFFF || spriteId >= MAX_SPRITES)
    {
        FreeSpritePaletteByTag(TAG_NOVIDADES_PIC + index);
        return MAX_SPRITES;
    }
    gSprites[spriteId].oam.priority = 1;
    return spriteId;
}

// Solta os sprites, os tiles e as paletas da imagem do cartão aberto (a cada troca e na saída).
static void Novidades_DestroyCardImage(void)
{
    u8 i;

    if (sNovidades->cardImage == CARD_IMAGE_ONE_MON || sNovidades->cardImage == CARD_IMAGE_TWO_MONS)
    {
        for (i = 0; i < ARRAY_COUNT(sNovidades->cardSpriteIds); i++)
        {
            if (sNovidades->cardSpriteIds[i] != MAX_SPRITES)
                FreeAndDestroyMonPicSprite(sNovidades->cardSpriteIds[i]);
            FreeSpritePaletteByTag(TAG_NOVIDADES_PIC + i);
            sNovidades->cardSpriteIds[i] = MAX_SPRITES;
        }
    }
    else if (sNovidades->cardSpriteIds[0] != MAX_SPRITES)
    {
        // ícone: liberado por tag (o template do AddItemIcon* era local), a matriz afim pelo sprite
        FreeSpriteTilesByTag(TAG_NOVIDADES_CARD_ICON);
        FreeSpritePaletteByTag(TAG_NOVIDADES_CARD_ICON);
        FreeSpriteOamMatrix(&gSprites[sNovidades->cardSpriteIds[0]]);
        DestroySprite(&gSprites[sNovidades->cardSpriteIds[0]]);
        sNovidades->cardSpriteIds[0] = MAX_SPRITES;
    }
    sNovidades->cardImage = CARD_IMAGE_TOPIC_ICON;
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

static void Novidades_CreateIcons(void)
{
    u8 i;

    for (i = 0; i < NOVIDADES_TOPIC_COUNT; i++)
    {
        u8 spriteId = Novidades_AddTopicIcon(TAG_NOVIDADES_ICON + i, TAG_NOVIDADES_ICON + i, i);
        sNovidades->iconSpriteIds[i] = spriteId;
        if (spriteId == MAX_SPRITES)
            continue;
        // O ícone (24 x 24) fica no canto do sprite de 32 x 32 centrado em x/y: +4 põe o ícone no meio do quadro
        gSprites[spriteId].x = (PANEL_LEFT + (i % NOVIDADES_GRID_COLUMNS) * PANEL_STEP_X) * 8 + PANEL_WIDTH * 4 + 4;
        gSprites[spriteId].y = (PANEL_TOP + (i / NOVIDADES_GRID_COLUMNS) * PANEL_STEP_Y) * 8 + PANEL_HEIGHT * 4 + 4;
    }
}

// Liberação por tag, como a bolsa (item_menu_icons.c, CreateItemMenuIcon): o AddItemIconObject monta o
// template numa variável local, então o DestroySpriteAndFreeResources leria um ponteiro velho.
static void Novidades_DestroyIcons(void)
{
    u8 i;

    for (i = 0; i < NOVIDADES_TOPIC_COUNT; i++)
    {
        if (sNovidades->iconSpriteIds[i] != MAX_SPRITES)
        {
            FreeSpriteTilesByTag(TAG_NOVIDADES_ICON + i);
            FreeSpritePaletteByTag(TAG_NOVIDADES_ICON + i);
            DestroySprite(&gSprites[sNovidades->iconSpriteIds[i]]);
        }
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
// cursor | pronta para input << 8 | ícones vivos << 16 | (cartão aberto + 1, 0 na grade) << 24.
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
    return sNovidades->cursor | sNovidades->inputReady << 8 | icons << 16
         | (sNovidades->view == VIEW_CARD ? sNovidades->card + 1 : 0) << 24;
}

// Atalho da esteira (TEST_CMD_NOVIDADES_CARD): 0xFFFFFFFF = fora do cartão; senão
// tópico | cartão << 8 | imagem (CARD_IMAGE_*: 0 ícone do tópico, 1 item, 2 uma espécie, 3 duas) << 16
// | sprites vivos da imagem << 24.
u32 Novidades_TestGetCard(void)
{
    u8 i, live = 0;

    if (sNovidades == NULL || sNovidades->view != VIEW_CARD)
        return 0xFFFFFFFF;
    for (i = 0; i < ARRAY_COUNT(sNovidades->cardSpriteIds); i++)
    {
        if (sNovidades->cardSpriteIds[i] != MAX_SPRITES && gSprites[sNovidades->cardSpriteIds[i]].inUse)
            live++;
    }
    return sNovidades->cursor | sNovidades->card << 8 | sNovidades->cardImage << 16 | live << 24;
}
#endif // TESTBUILD
