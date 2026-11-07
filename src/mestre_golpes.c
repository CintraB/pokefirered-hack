#include "global.h"
#include "gflib.h"
#include "list_menu.h"
#include "menu.h"
#include "menu_indicators.h"
#include "mestre_golpes.h"
#include "new_menu_helpers.h"
#include "script.h"
#include "event_data.h"
#include "task.h"
#include "constants/moves.h"
#include "data.h"
#include "constants/party_menu.h"
#include "constants/songs.h"
#include "field_player_avatar.h"

#define MESTRE_LINHAS_VISIVEIS 6
#define MESTRE_JANELA_X        1
#define MESTRE_JANELA_Y        1
#define MESTRE_BASE_BLOCK      0x038   // a mesma faixa livre do menu de lista dos scripts (field_specials.c)

// Os golpes na ordem dos TUTOR_MOVE_* (o índice da lista é o id do tutor); test_casas.py confere com
// sTutorMoves de src/data/pokemon/tutor_learnsets.h.
static const u16 sMestreGolpes[TUTOR_MOVE_COUNT] =
{
    [TUTOR_MOVE_MEGA_PUNCH] = MOVE_MEGA_PUNCH,
    [TUTOR_MOVE_SWORDS_DANCE] = MOVE_SWORDS_DANCE,
    [TUTOR_MOVE_MEGA_KICK] = MOVE_MEGA_KICK,
    [TUTOR_MOVE_BODY_SLAM] = MOVE_BODY_SLAM,
    [TUTOR_MOVE_DOUBLE_EDGE] = MOVE_DOUBLE_EDGE,
    [TUTOR_MOVE_COUNTER] = MOVE_COUNTER,
    [TUTOR_MOVE_SEISMIC_TOSS] = MOVE_SEISMIC_TOSS,
    [TUTOR_MOVE_MIMIC] = MOVE_MIMIC,
    [TUTOR_MOVE_METRONOME] = MOVE_METRONOME,
    [TUTOR_MOVE_SOFT_BOILED] = MOVE_SOFT_BOILED,
    [TUTOR_MOVE_DREAM_EATER] = MOVE_DREAM_EATER,
    [TUTOR_MOVE_THUNDER_WAVE] = MOVE_THUNDER_WAVE,
    [TUTOR_MOVE_EXPLOSION] = MOVE_EXPLOSION,
    [TUTOR_MOVE_ROCK_SLIDE] = MOVE_ROCK_SLIDE,
    [TUTOR_MOVE_SUBSTITUTE] = MOVE_SUBSTITUTE,
};

// Dados da task
#define tJanela   data[0]
#define tLista    data[1]
#define tSetas    data[2]

static EWRAM_DATA struct ListMenuItem *sMestreItens = NULL;
static EWRAM_DATA u16 sMestreRolagem = 0;

static void Task_MestreGolpes_Entrada(u8 taskId);
static void Task_MestreGolpes_Entrada_Input(u8 taskId);
static void MestreGolpes_MoveCursor(s32 itemIndex, bool8 onInit, struct ListMenu *list);
static void MestreGolpes_Fechar(u8 taskId, u16 resultado);

void MestreGolpes_EscolherGolpe(void)
{
    CreateTask(Task_MestreGolpes_Entrada, 80);
}

static void Task_MestreGolpes_Entrada(u8 taskId)
{
    struct WindowTemplate janela;
    struct ListMenuTemplate modelo = gMultiuseListMenuTemplate;
    struct ScrollArrowsTemplate setas = {
        .firstArrowType = 2,
        .secondArrowType = 3,
        .tileTag = 2000,
        .palTag = 100,
    };
    struct Task *task = &gTasks[taskId];
    s32 largura = 0, i, tiles;

    LockPlayerFieldControls();
    sMestreRolagem = 0;
    sMestreItens = AllocZeroed(TUTOR_MOVE_COUNT * sizeof(struct ListMenuItem));
    for (i = 0; i < TUTOR_MOVE_COUNT; i++)
    {
        s32 w;
        sMestreItens[i].label = gMoveNames[sMestreGolpes[i]];
        sMestreItens[i].index = i;
        w = GetStringWidth(FONT_NORMAL, sMestreItens[i].label, 0);
        if (w > largura)
            largura = w;
    }
    tiles = (largura + 9) / 8 + 1;
    janela = SetWindowTemplateFields(0, MESTRE_JANELA_X, MESTRE_JANELA_Y, tiles, MESTRE_LINHAS_VISIVEIS * 2, 15, MESTRE_BASE_BLOCK);
    task->tJanela = AddWindow(&janela);
    SetStdWindowBorderStyle(task->tJanela, FALSE);

    modelo.items = sMestreItens;
    modelo.moveCursorFunc = MestreGolpes_MoveCursor;
    modelo.itemPrintFunc = NULL;
    modelo.totalItems = TUTOR_MOVE_COUNT;
    modelo.maxShowed = MESTRE_LINHAS_VISIVEIS;
    modelo.windowId = task->tJanela;
    modelo.header_X = 0;
    modelo.item_X = 8;
    modelo.cursor_X = 0;
    modelo.upText_Y = 0;
    modelo.cursorPal = 2;
    modelo.fillValue = 1;
    modelo.cursorShadowPal = 3;
    modelo.lettersSpacing = 1;
    modelo.itemVerticalPadding = 0;
    modelo.scrollMultiple = 0;
    modelo.fontId = FONT_NORMAL;
    modelo.cursorKind = 0;

    setas.firstX = 4 * tiles + 8 * MESTRE_JANELA_X;
    setas.firstY = 8;
    setas.secondX = setas.firstX;
    setas.secondY = 8 * (MESTRE_LINHAS_VISIVEIS * 2) + 10;
    setas.fullyUpThreshold = 0;
    setas.fullyDownThreshold = TUTOR_MOVE_COUNT - MESTRE_LINHAS_VISIVEIS;
    task->tSetas = AddScrollIndicatorArrowPair(&setas, &sMestreRolagem);

    task->tLista = ListMenuInit(&modelo, 0, 0);
    PutWindowTilemap(task->tJanela);
    CopyWindowToVram(task->tJanela, COPYWIN_FULL);
    task->func = Task_MestreGolpes_Entrada_Input;
}

static void MestreGolpes_MoveCursor(s32 itemIndex, bool8 onInit, struct ListMenu *list)
{
    u8 taskId;

    PlaySE(SE_SELECT);
    taskId = FindTaskIdByFunc(Task_MestreGolpes_Entrada_Input);
    if (taskId != TASK_NONE)
        ListMenuGetScrollAndRow(gTasks[taskId].tLista, &sMestreRolagem, NULL);
}

static void Task_MestreGolpes_Entrada_Input(u8 taskId)
{
    s32 entrada = ListMenu_ProcessInput(gTasks[taskId].tLista);

    switch (entrada)
    {
    case LIST_NOTHING_CHOSEN:
        break;
    case LIST_CANCEL:
        PlaySE(SE_SELECT);
        MestreGolpes_Fechar(taskId, MESTRE_GOLPES_CANCELOU);
        break;
    default:
        PlaySE(SE_SELECT);
        MestreGolpes_Fechar(taskId, entrada);
        break;
    }
}

static void MestreGolpes_Fechar(u8 taskId, u16 resultado)
{
    struct Task *task = &gTasks[taskId];

    gSpecialVar_Result = resultado;
    RemoveScrollIndicatorArrowPair(task->tSetas);
    DestroyListMenuTask(task->tLista, NULL, NULL);
    Free(sMestreItens);
    sMestreItens = NULL;
    ClearStdWindowAndFrameToTransparent(task->tJanela, TRUE);
    FillWindowPixelBuffer(task->tJanela, PIXEL_FILL(0));
    ClearWindowTilemap(task->tJanela);
    CopyWindowToVram(task->tJanela, COPYWIN_GFX);
    RemoveWindow(task->tJanela);
    DestroyTask(taskId);
    ScriptContext_Enable();
}
