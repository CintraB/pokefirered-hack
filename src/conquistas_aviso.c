#include "global.h"
#include "gflib.h"
#include "characters.h"
#include "conquistas.h"
#include "event_scripts.h"
#include "item.h"
#include "item_menu_icons.h"
#include "link.h"
#include "map_name_popup.h"
#include "menu.h"
#include "new_menu_helpers.h"
#include "overworld.h"
#include "quest_log.h"
#include "script.h"
#include "strings.h"
#include "task.h"
#include "text_window.h"
#include "constants/items.h"
#include "constants/quest_log.h"
#include "constants/songs.h"

// Conquistas (POK-44), Task 6: o aviso que pausa o jogo, "tipo conquista no Mario". O campo chama
// Conquistas_TentarAviso uma vez por quadro (ProcessPlayerFieldInput, logo depois de TryRunOnFrameMapScript); com um
// prêmio a entregar, ela põe EventScript_AvisoConquista (data/scripts/conquistas.inc) no campo: lockall, o special
// Conquistas_MostrarAviso e waitstate. O special entrega o prêmio (bolsa, senão PC de itens) e abre a janela de
// 26x4 tiles no alto da tela, na faixa do diálogo do BG0 (0x198-0x1FF), com a moldura padrão: ela desce de cima
// rolando o BG0 (BG0VOFS), quica, mostra uma estrela que pula e brilha e o ícone do item, com a fanfarra de item.
// Fecha com A/B depois de 30 quadros ou sozinha em 180; ao fechar, sobe de volta, sai do BG0 e o BG0VOFS volta a 0.
//
// Memória: só gConquistasAvisoAtivo (a esteira lê) e, na ROM de teste, o silêncio; o texto vai num bloco do heap
// (ponteiro nos dados da task). O texto montado também fica em gStringVar4 ("título nome\nlinha 2"), que a esteira lê.

EWRAM_DATA u8 gConquistasAvisoAtivo = 0;
#if TESTBUILD
EWRAM_DATA u8 gConquistasSilencio = 0;   // TEST_CMD_CONQ_SILENCIO: os cenários da ROM de teste montam o estado em paz
#endif

#define sConq (&gSaveBlock1Ptr->conquistas)

#define AVISO_MIN_QUADROS 30    // A/B só fecha depois disto
#define AVISO_MAX_QUADROS 180   // e sozinho aqui
#define AVISO_ESCONDIDO   56    // BG0VOFS com a janela (moldura nas linhas 1 a 6) toda acima da tela
#define AVISO_MOLDURA_TILE 0x214 // a moldura padrão do campo (STD_WINDOW_BASE_TILE_NUM, src/new_menu_helpers.c)
#define AVISO_MOLDURA_PAL  14
#define AVISO_TEXTO_MAX    64
#define TAG_AVISO_ESTRELA  0x5C40
#define TAG_AVISO_ICONE    0x5C41

static const struct WindowTemplate sAvisoWindowTemplate = {
    .bg = 0,
    .tilemapLeft = 2,
    .tilemapTop = 2,
    .width = 26,
    .height = 4,
    .paletteNum = 15,
    .baseBlock = 0x198,
};

static const u32 sAvisoGfx[] = INCBIN_U32("graphics/conquistas/aviso.4bpp");
static const u16 sAvisoPal[] = INCBIN_U16("graphics/conquistas/aviso.gbapal");

// BG0VOFS a cada quadro: a janela desce de cima e quica; depois sobe de volta
static const s8 sEntrada[] = {56, 46, 37, 29, 22, 16, 11, 7, 4, 2, 0, -3, -4, -3, -1, 0};
static const s8 sSaida[] = {0, 3, 8, 15, 24, 35, 47, 56};
// o pulo da estrela (e do ícone, meio ciclo depois), em px para cima, a cada ciclo de 48 quadros
static const u8 sPulo[] = {0, 3, 5, 6, 7, 7, 6, 5, 3, 1};

static const u8 sCorTitulo[] = {TEXT_COLOR_WHITE, TEXT_COLOR_RED, TEXT_COLOR_LIGHT_RED};
static const u8 sCorResumo[] = {TEXT_COLOR_WHITE, TEXT_COLOR_BLUE, TEXT_COLOR_LIGHT_BLUE};
static const u8 sCorTexto[] = {TEXT_COLOR_WHITE, TEXT_COLOR_DARK_GRAY, TEXT_COLOR_LIGHT_GRAY};

static void SpriteCB_Pulo(struct Sprite *sprite);

static const struct SpriteSheet sEstrelaSheet = {sAvisoGfx, sizeof(sAvisoGfx), TAG_AVISO_ESTRELA};
static const struct SpritePalette sEstrelaPal = {sAvisoPal, TAG_AVISO_ESTRELA};
static const struct OamData sEstrelaOam = {
    .shape = SPRITE_SHAPE(16x16),
    .size = SPRITE_SIZE(16x16),
    .priority = 0,
};
static const union AnimCmd sEstrelaAnim[] = {
    ANIMCMD_FRAME(0, 12),
    ANIMCMD_FRAME(4, 12),
    ANIMCMD_JUMP(0),
};
static const union AnimCmd *const sEstrelaAnims[] = {sEstrelaAnim};
static const struct SpriteTemplate sEstrelaTemplate = {
    .tileTag = TAG_AVISO_ESTRELA,
    .paletteTag = TAG_AVISO_ESTRELA,
    .oam = &sEstrelaOam,
    .anims = sEstrelaAnims,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCB_Pulo,
};

struct Aviso
{
    u8 linha1[AVISO_TEXTO_MAX];
    u8 linha2[AVISO_TEXTO_MAX];
    u16 item;        // ícone do prêmio entregue (ITEM_NONE: sem ícone)
    bool8 resumo;
    bool8 nada;      // não havia o que mostrar (o script só segue)
};

enum
{
    AVISO_ESPERA_POPUP,  // o popup do nome do mapa também rola o BG0: espera ele sumir
    AVISO_ENTRADA,
    AVISO_MOSTRANDO,
    AVISO_SAIDA,
    AVISO_LIMPAR,
    AVISO_FIM,
};

#define tState   data[0]
#define tTimer   data[1]
#define tWindow  data[2]
#define tEstrela data[3]
#define tIcone   data[4]
#define tPasso   data[5]
#define TASK_PTR 6         // data[6] e data[7]: struct Aviso *

static u16 MapaAtual(void)
{
    return (u8)gSaveBlock1Ptr->location.mapGroup << 8 | (u8)gSaveBlock1Ptr->location.mapNum;
}

bool8 Conquistas_TentarAviso(void)
{
    u16 mapa;
    u8 num, degrau;

    if (gQuestLogState == QL_STATE_PLAYBACK || gQuestLogState == QL_STATE_PLAYBACK_LAST || InUnionRoom()
     || gReceivedRemoteLinkPlayers || IsUpdateLinkStateCBActive()
     || gPlayerAvatar.tileTransitionState == T_TILE_TRANSITION)
        return FALSE;
#if TESTBUILD
    if (gConquistasSilencio)
        return FALSE;
#endif
    // no FRLG o vblankCounter1 é um ponteiro (só conta quando alguém o aponta): a cadência usa o vblankCounter2
    if ((gMain.vblankCounter2 & 31) == 0)
        Conquistas_ChecarEstado();
    if (Conquistas_AvisosPendentes() == 0)
        return FALSE;
    // um prêmio que não coube fica para depois: nenhum aviso até o jogador trocar de mapa
    mapa = MapaAtual();
    if (sConq->adiadoNoMapa != 0xFFFF)
    {
        if (sConq->adiadoNoMapa == mapa)
            return FALSE;
        sConq->adiadoNoMapa = 0xFFFF;
    }
    // o resumo de um save antigo em que a varredura não achou prêmio nenhum: nada a mostrar
    if (sConq->resumoPendente && !Conquistas_ProximoPendente(&num, &degrau))
    {
        sConq->resumoPendente = FALSE;
        return FALSE;
    }
    ScriptContext_SetupScript(EventScript_AvisoConquista);
    return TRUE;
}

static u8 *AnexarNumero(u8 *s, u16 n)
{
    return ConvertIntToDecimalStringN(s, n, STR_CONV_MODE_LEFT_ALIGN, n >= 100 ? 3 : (n >= 10 ? 2 : 1));
}

// A conquista `num` (degrau `degrau`): entrega o prêmio e monta as duas linhas.
static void MontarConquista(struct Aviso *a, u8 num, u8 degrau)
{
    const struct ConquistaPremio *p = Conquistas_Premio(num, degrau);
    u8 onde = Conquistas_EntregarPremio(num, degrau);
    u8 *s;

    if (gConquistas[num].numDegraus > 0)
        AnexarNumero(gStringVar1, gConquistas[num].degraus[degrau]);   // o {N} do nome
    StringExpandPlaceholders(a->linha1, gConquistas[num].nome);
    if (onde == CONQ_ENTREGA_PENDENTE)
    {
        StringCopy(a->linha2, gText_ConqAviso_Cheios);
        sConq->adiadoNoMapa = MapaAtual();
        a->item = ITEM_NONE;
    }
    else
    {
        s = StringCopy(a->linha2, gText_ConqAviso_Premio);
        s = AnexarNumero(s, p->qtd);
        *s++ = CHAR_SPACE;
        s = StringCopy(s, ItemId_GetName(p->item));
        StringCopy(s, onde == CONQ_ENTREGA_BOLSA ? gText_ConqAviso_NaBolsa : gText_ConqAviso_NoPc);
        a->item = p->item;
    }
    s = StringCopy(gStringVar4, gText_ConqAviso_Titulo);
    s = StringCopy(s, a->linha1);
    *s++ = CHAR_NEWLINE;
    StringCopy(s, a->linha2);
}

// O resumo de um save antigo: todos os prêmios de uma vez.
static void MontarResumo(struct Aviso *a)
{
    u8 naBolsa, noPc, pendentes, total;
    u8 *s;

    Conquistas_EntregarTudo(&naBolsa, &noPc, &pendentes);
    total = naBolsa + noPc + pendentes;
    s = StringCopy(a->linha1, gText_ConqAviso_ResumoAntes);
    s = AnexarNumero(s, total);
    StringCopy(s, total == 1 ? gText_ConqAviso_ResumoUma : gText_ConqAviso_ResumoVarias);
    // com prêmio pendente a linha tem três partes: sem o "Prêmios: ", para caber nos 208 px
    s = a->linha2;
    if (pendentes == 0)
        s = StringCopy(s, gText_ConqAviso_Premios);
    s = AnexarNumero(s, naBolsa);
    s = StringCopy(s, gText_ConqAviso_NaBolsa);
    if (noPc > 0)
    {
        s = StringCopy(s, gText_ConqAviso_Separador);
        s = AnexarNumero(s, noPc);
        s = StringCopy(s, gText_ConqAviso_NoPc);
    }
    if (pendentes > 0)
    {
        s = StringCopy(s, gText_ConqAviso_Separador);
        s = AnexarNumero(s, pendentes);
        StringCopy(s, gText_ConqAviso_Depois);
        sConq->adiadoNoMapa = MapaAtual();
    }
    a->resumo = TRUE;
    a->item = ITEM_NONE;
    s = StringCopy(gStringVar4, a->linha1);
    *s++ = CHAR_NEWLINE;
    StringCopy(s, a->linha2);
}

static void Task_Aviso(u8 taskId);

// Special (specialvar): FALSE = sem task para o aviso (as 16 ocupadas); o script então pula o waitstate e nada é
// entregue (o prêmio continua pendente para o próximo quadro livre).
bool8 Conquistas_MostrarAviso(void)
{
    struct Aviso *a;
    u8 taskId = CreateTask(Task_Aviso, 80);
    u8 num, degrau;

    if (taskId == TASK_NONE)
        return FALSE;
    a = AllocZeroed(sizeof(*a));
    gTasks[taskId].tWindow = WINDOW_NONE;
    gTasks[taskId].tEstrela = MAX_SPRITES;
    gTasks[taskId].tIcone = MAX_SPRITES;
    SetWordTaskArg(taskId, TASK_PTR, (u32)a);
    if (a == NULL)
        return TRUE;
    // a fila não trava no primeiro: um prêmio que não cabe deixa passar os que cabem; o "fica para depois" sai quando
    // só sobram os que não cabem (e adia até trocar de mapa)
    if (sConq->resumoPendente)
        MontarResumo(a);
    else if (Conquistas_ProximoQueCabe(&num, &degrau) || Conquistas_ProximoPendente(&num, &degrau))
        MontarConquista(a, num, degrau);
    else
        a->nada = TRUE;
    return TRUE;
}

static void SetBg0Y(s16 y)
{
    ChangeBgY(0, (u32)((s32)y << 8), BG_COORD_SET);
}

static bool8 AbrirJanela(struct Task *t, struct Aviso *a)
{
    u8 win = AddWindow(&sAvisoWindowTemplate);

    if (win == WINDOW_NONE)
        return FALSE;
    t->tWindow = win;
    SetBg0Y(AVISO_ESCONDIDO);
    Menu_LoadStdPal();
    LoadStdWindowGfx(win, AVISO_MOLDURA_TILE, BG_PLTT_ID(AVISO_MOLDURA_PAL));
    DrawStdWindowFrame(win, FALSE);
    if (a->resumo)
    {
        AddTextPrinterParameterized4(win, FONT_NORMAL, 0, 0, 0, 0, sCorResumo, TEXT_SKIP_DRAW, a->linha1);
    }
    else
    {
        AddTextPrinterParameterized4(win, FONT_NORMAL, 0, 0, 0, 0, sCorTitulo, TEXT_SKIP_DRAW, gText_ConqAviso_Titulo);
        AddTextPrinterParameterized4(win, FONT_NORMAL, GetStringWidth(FONT_NORMAL, gText_ConqAviso_Titulo, 0), 0, 0, 0,
                                     sCorTexto, TEXT_SKIP_DRAW, a->linha1);
    }
    AddTextPrinterParameterized4(win, FONT_NORMAL, 0, 16, 0, 0, a->item == ITEM_NONE && !a->resumo ? sCorTitulo : sCorTexto,
                                 TEXT_SKIP_DRAW, a->linha2);
    CopyWindowToVram(win, COPYWIN_FULL);
    return TRUE;
}

static void SpriteCB_Pulo(struct Sprite *sprite)
{
    u8 fase = sprite->data[0]++ % 48;

    sprite->y2 = fase < ARRAY_COUNT(sPulo) ? -sPulo[fase] : 0;
}

// A estrela no canto de cima à esquerda da moldura; o ícone do prêmio pendurado no canto de baixo à direita.
static void MostrarSprites(struct Task *t, struct Aviso *a)
{
    u8 id;

    if (LoadSpritePalette(&sEstrelaPal) != 0xFF)
    {
        LoadSpriteSheet(&sEstrelaSheet);
        if (GetSpriteTileStartByTag(TAG_AVISO_ESTRELA) != 0xFFFF)
        {
            id = CreateSprite(&sEstrelaTemplate, 12, 12, 0);
            t->tEstrela = id;
        }
        if (t->tEstrela == MAX_SPRITES)
        {
            FreeSpriteTilesByTag(TAG_AVISO_ESTRELA);
            FreeSpritePaletteByTag(TAG_AVISO_ESTRELA);
        }
    }
    if (a->item != ITEM_NONE)
    {
        FreeSpriteTilesByTag(TAG_AVISO_ICONE);     // nada de um aviso anterior sob a mesma tag
        FreeSpritePaletteByTag(TAG_AVISO_ICONE);
        id = AddItemIconObject(TAG_AVISO_ICONE, TAG_AVISO_ICONE, a->item);
        if (id != MAX_SPRITES)
        {
            gSprites[id].x = 226;
            gSprites[id].y = 52;
            gSprites[id].oam.priority = 0;
            gSprites[id].data[0] = 24;
            gSprites[id].callback = SpriteCB_Pulo;
            t->tIcone = id;
        }
    }
}

// Tudo solto por tag, como a bolsa e as novidades (src/novidades.c): o AddItemIconObject monta o SpriteTemplate
// numa variável local, então o sprite->template do ícone aponta para lixo e o DestroySpriteAndFreeResources não
// soltaria os tiles nem a paleta (o aviso seguinte mostraria o ícone antigo).
static void EsconderSprites(struct Task *t)
{
    if (t->tEstrela != MAX_SPRITES)
        DestroySprite(&gSprites[t->tEstrela]);
    if (t->tIcone != MAX_SPRITES)
        DestroySprite(&gSprites[t->tIcone]);
    FreeSpriteTilesByTag(TAG_AVISO_ESTRELA);
    FreeSpritePaletteByTag(TAG_AVISO_ESTRELA);
    FreeSpriteTilesByTag(TAG_AVISO_ICONE);
    FreeSpritePaletteByTag(TAG_AVISO_ICONE);
    t->tEstrela = t->tIcone = MAX_SPRITES;
}

static void Task_Aviso(u8 taskId)
{
    struct Task *t = &gTasks[taskId];
    struct Aviso *a = (struct Aviso *)GetWordTaskArg(taskId, TASK_PTR);

    switch (t->tState)
    {
    case AVISO_ESPERA_POPUP:
        if (IsMapNamePopupTaskActive())
            break;
        if (a == NULL || a->nada || !AbrirJanela(t, a))
        {
            t->tState = AVISO_FIM;
            break;
        }
        gConquistasAvisoAtivo = 1;
        PlayFanfare(MUS_OBTAIN_ITEM);
        t->tTimer = 0;
        t->tPasso = 0;
        t->tState = AVISO_ENTRADA;
        break;
    case AVISO_ENTRADA:
        t->tTimer++;
        SetBg0Y(sEntrada[t->tPasso]);
        if (++t->tPasso >= (s16)ARRAY_COUNT(sEntrada))
        {
            MostrarSprites(t, a);
            t->tState = AVISO_MOSTRANDO;
        }
        break;
    case AVISO_MOSTRANDO:
        t->tTimer++;
        if ((t->tTimer >= AVISO_MIN_QUADROS && JOY_NEW(A_BUTTON | B_BUTTON)) || t->tTimer >= AVISO_MAX_QUADROS)
        {
            EsconderSprites(t);
            t->tPasso = 0;
            t->tState = AVISO_SAIDA;
        }
        break;
    case AVISO_SAIDA:
        SetBg0Y(sSaida[t->tPasso]);
        if (++t->tPasso >= (s16)ARRAY_COUNT(sSaida))
        {
            ClearStdWindowAndFrameToTransparent(t->tWindow, TRUE);
            RemoveWindow(t->tWindow);
            t->tWindow = WINDOW_NONE;
            t->tState = AVISO_LIMPAR;
        }
        break;
    case AVISO_LIMPAR:
        // o BG0VOFS só volta a 0 depois que o tilemap limpo chegou à VRAM (senão a janela pisca no lugar)
        if (IsDma3ManagerBusyWithBgCopy())
            break;
        ChangeBgY(0, 0, BG_COORD_SET);
        t->tState = AVISO_FIM;
        break;
    case AVISO_FIM:
        EsconderSprites(t);
        if (a != NULL)
            Free(a);
        gConquistasAvisoAtivo = 0;
        DestroyTask(taskId);
        ScriptContext_Enable();
        break;
    }
}
