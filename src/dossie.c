#include "global.h"
#include "gflib.h"
#include "dossie.h"
#include "event_data.h"
#include "familia_sombra.h"
#include "help_system.h"
#include "menu.h"
#include "menu_helpers.h"
#include "new_menu_helpers.h"
#include "overworld.h"
#include "quest_log.h"
#include "scanline_effect.h"
#include "script.h"
#include "task.h"
#include "constants/flags.h"
#include "constants/songs.h"

// O dossiê da Família Sombra (POK-54, Task 9; spec 2026-11-07-familia-sombra-parte2 §5). A Oficial Jenny abre com
// `special Dossie_Abrir` + `waitstate`; a saída volta ao campo continuando o script.
//
// Tela: BG1 = a pasta (papel pardo, a mesa, o selo e a moldura da foto; 3 telas prontas em graphics/dossie/pasta.bin,
// geradas por tools/familia_sombra/dossie.py), BG0 = uma janela de 30x20 com todo o texto (fundo transparente, na
// mesma paleta da pasta). Sprites por cima: a foto do chefe (64x64, 3 tons de cinza), o clipe, o carimbo (CAPTURADO ou
// DERROTADO, por cima da área da foto, nunca do texto: sem mistura de cor nem afim) e a rosinha da cor da rosa.
//
// Memória: tudo num bloco AllocZeroed apontado por sDossie (o único EWRAM_DATA), liberado na saída.

// Música da tela ([call] do plano: o Cintra julga pela tela; trocável nesta linha)
#define DOSSIE_MUSICA MUS_POKE_TOWER

#define DOSSIE_PAGINAS ARRAY_COUNT(sDossiePaginas)

enum {
    BG_TEXTO,
    BG_FUNDO,
};

enum {
    WIN_TELA,
    WIN_COUNT
};

// As 3 telas de pasta.bin (32x20 entradas cada)
enum {
    FUNDO_CAPA,
    FUNDO_FICHA,
    FUNDO_TEXTO,
};
#define FUNDO_ENTRADAS (32 * 20)

// Carimbo (Dossie_TestEstado devolve este número)
enum {
    CARIMBO_NENHUM,
    CARIMBO_DERROTADO,
    CARIMBO_CAPTURADO,
};

// Cores da paleta da pasta (tools/familia_sombra/dossie.py, PASTA_PAL): 2/3/4 = DARK_GRAY/LIGHT_GRAY/RED do charmap
#define COR_TINTA        2
#define COR_TINTA_SOMBRA 3
#define COR_VERMELHO     4
#define COR_OURO_ESC     5
#define COR_MARCA_TEXTO  15

// Geometria (a mesma do gerador): texto em pixels da tela, sprites pelo centro
#define ABA_X            12
#define ABA_Y            0
#define ABA_FICHA_FIM    156   // "FOLHA 1/3" alinhado à direita aqui (a aba da ficha vai até x = 160)
#define ROTA_CAIXA_X     166   // caixa branca do "ROTA 23" na capa: x 166..226
#define ROTA_CAIXA_W     61
#define ROTA_Y           19
#define CAB_X            88    // coluna do cabeçalho da ficha, à direita da foto
#define TITULO_Y         17
#define MARCA_Y          19    // marca-texto: 13 px de altura
#define MARCA_H          13
#define GEMEOS_Y         34
#define ROSA_TEXTO_X     101
#define ROSA_TEXTO_Y     50
#define LORE_TOPO_X      89
#define LORE_TOPO_Y      69
#define LORE_X           12
#define LORE_Y           88
#define DEPOIS_TITULO_X  12
#define DEPOIS_TEXTO_Y   36
#define RODAPE_Y         142
#define RODAPE_X         12
#define RODAPE_FIM       228

#define FOTO_X           (14 + 32)   // a foto (64x64) em (14, 21); a moldura branca do fundo vai de (11, 18) a (80, 87)
#define FOTO_Y           (21 + 32)
#define CLIPE_X          (60 + 4)    // o clipe (8x32) em (60, 14), preso na borda de cima da foto (fora do texto da aba)
#define CLIPE_Y          (14 + 16)
#define CARIMBO_X        (14 + 32)   // o carimbo (64x32) na metade de baixo da foto: (14, 53)
#define CARIMBO_Y        (53 + 16)
#define ROSA_FICHA_X     (89 + 4)    // a rosa (8x16) em (89, 47), antes do "Rosa vermelha"
#define ROSA_FICHA_Y     (47 + 8)
#define ROSA_DEPOIS_Y    (14 + 8)

STATIC_ASSERT(CAB_X + 3 + DOSSIE_TITULO_PX + 3 <= RODAPE_FIM + 4, DossieTituloCabe);
STATIC_ASSERT(LORE_TOPO_X + DOSSIE_LORE_TOPO_PX <= RODAPE_FIM + 4, DossieLoreTopoCabe);
STATIC_ASSERT(LORE_X + DOSSIE_LORE_PX <= RODAPE_FIM, DossieLoreCabe);
STATIC_ASSERT(LORE_Y + (DOSSIE_LORE_LINHAS - 2) * DOSSIE_LINHA_PX + 14 <= RODAPE_Y + 1, DossieLoreAcimaDoRodape);
STATIC_ASSERT(DEPOIS_TEXTO_Y + (DOSSIE_DEPOIS_LINHAS - 1) * DOSSIE_LINHA_PX + 14 <= RODAPE_Y + 1, DossieDepoisCabe);

#define TAG_FOTO     0x5E10   // + chefe - 1: as 4 fotos ficam carregadas; a página troca o ladrilho do sprite
#define TAG_CLIPE    0x5E14
#define TAG_CARIMBO  0x5E15
#define TAG_ROSA     0x5E16
#define TAG_PAL_FOTO 0x5E10   // a foto e o clipe dividem a paleta

#define LINHA_BYTES 120       // uma linha da lore com os códigos de cor

struct Dossie
{
    u8 initState;
    u8 pronta;
    u8 pagina;
    u8 ajudaAntes;   // gHelpSystemEnabled de antes da tela (volta a ele na saída)
    u8 carimbo;      // CARIMBO_* da página aberta
    u8 fotoSprite;
    u8 clipeSprite;
    u8 carimboSprite;
    u8 rosaSprite;
    u8 linha[LINHA_BYTES];
    u16 tilemapBuffer[0x400];
};

static EWRAM_DATA struct Dossie *sDossie = NULL;

#include "data/dossie_textos.h"

static const u32 sPasta_Gfx[] = INCBIN_U32("graphics/dossie/pasta.4bpp");
static const u16 sPasta_Pal[] = INCBIN_U16("graphics/dossie/pasta.gbapal");
static const u16 sPasta_Tilemap[] = INCBIN_U16("graphics/dossie/pasta.bin");
static const u32 sFoto_Dom[] = INCBIN_U32("graphics/dossie/foto_dom.4bpp");
static const u32 sFoto_Cobrador[] = INCBIN_U32("graphics/dossie/foto_cobrador.4bpp");
static const u32 sFoto_Mercenario[] = INCBIN_U32("graphics/dossie/foto_mercenario.4bpp");
static const u32 sFoto_Pesadelo[] = INCBIN_U32("graphics/dossie/foto_pesadelo.4bpp");
static const u16 sFoto_Pal[] = INCBIN_U16("graphics/dossie/foto.gbapal");
static const u32 sClipe_Gfx[] = INCBIN_U32("graphics/dossie/clipe.4bpp");
static const u32 sCarimbo_Gfx[] = INCBIN_U32("graphics/dossie/carimbo.4bpp");
static const u16 sCarimbo_Pal[] = INCBIN_U16("graphics/dossie/carimbo.gbapal");
static const u32 sRosa_Gfx[] = INCBIN_U32("graphics/dossie/rosa.4bpp");
static const u16 sRosas_Pal[] = INCBIN_U16("graphics/dossie/rosas.gbapal");   // 4 paletas, na ordem dos chefes

STATIC_ASSERT(sizeof(sPasta_Tilemap) == 3 * FUNDO_ENTRADAS * 2, DossieTresTelas);
STATIC_ASSERT(sizeof(sRosas_Pal) == 4 * PLTT_SIZE_4BPP, DossieQuatroRosas);

static const struct SpriteSheet sSpriteSheets[] = {
    {sFoto_Dom, sizeof(sFoto_Dom), TAG_FOTO + 0},
    {sFoto_Cobrador, sizeof(sFoto_Cobrador), TAG_FOTO + 1},
    {sFoto_Mercenario, sizeof(sFoto_Mercenario), TAG_FOTO + 2},
    {sFoto_Pesadelo, sizeof(sFoto_Pesadelo), TAG_FOTO + 3},
    {sClipe_Gfx, sizeof(sClipe_Gfx), TAG_CLIPE},
    {sCarimbo_Gfx, sizeof(sCarimbo_Gfx), TAG_CARIMBO},
    {sRosa_Gfx, sizeof(sRosa_Gfx), TAG_ROSA},
    {}
};

static const struct SpritePalette sSpritePalettes[] = {
    {sFoto_Pal, TAG_PAL_FOTO},
    {sCarimbo_Pal, TAG_CARIMBO},
    {sRosas_Pal, TAG_ROSA},
    {}
};

static const struct OamData sOam_Foto = {.shape = SPRITE_SHAPE(64x64), .size = SPRITE_SIZE(64x64)};
static const struct OamData sOam_Clipe = {.shape = SPRITE_SHAPE(8x32), .size = SPRITE_SIZE(8x32)};
static const struct OamData sOam_Carimbo = {.shape = SPRITE_SHAPE(64x32), .size = SPRITE_SIZE(64x32)};
static const struct OamData sOam_Rosa = {.shape = SPRITE_SHAPE(8x16), .size = SPRITE_SIZE(8x16)};

// Os 2 quadros do carimbo (64x32 = 32 ladrilhos cada): CAPTURADO e DERROTADO
static const union AnimCmd sAnim_Capturado[] = {ANIMCMD_FRAME(0, 0), ANIMCMD_END};
static const union AnimCmd sAnim_Derrotado[] = {ANIMCMD_FRAME(32, 0), ANIMCMD_END};
static const union AnimCmd *const sAnims_Carimbo[] = {sAnim_Capturado, sAnim_Derrotado};

static const struct SpriteTemplate sTemplate_Foto = {
    .tileTag = TAG_FOTO, .paletteTag = TAG_PAL_FOTO, .oam = &sOam_Foto, .anims = gDummySpriteAnimTable,
    .images = NULL, .affineAnims = gDummySpriteAffineAnimTable, .callback = SpriteCallbackDummy,
};
static const struct SpriteTemplate sTemplate_Clipe = {
    .tileTag = TAG_CLIPE, .paletteTag = TAG_PAL_FOTO, .oam = &sOam_Clipe, .anims = gDummySpriteAnimTable,
    .images = NULL, .affineAnims = gDummySpriteAffineAnimTable, .callback = SpriteCallbackDummy,
};
static const struct SpriteTemplate sTemplate_Carimbo = {
    .tileTag = TAG_CARIMBO, .paletteTag = TAG_CARIMBO, .oam = &sOam_Carimbo, .anims = sAnims_Carimbo,
    .images = NULL, .affineAnims = gDummySpriteAffineAnimTable, .callback = SpriteCallbackDummy,
};
static const struct SpriteTemplate sTemplate_Rosa = {
    .tileTag = TAG_ROSA, .paletteTag = TAG_ROSA, .oam = &sOam_Rosa, .anims = gDummySpriteAnimTable,
    .images = NULL, .affineAnims = gDummySpriteAffineAnimTable, .callback = SpriteCallbackDummy,
};

static const struct BgTemplate sBgTemplates[] = {
    {
        .bg = BG_TEXTO,
        .charBaseIndex = 0,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0,
    }, {
        .bg = BG_FUNDO,
        .charBaseIndex = 2,   // os 600 ladrilhos da janela passam do bloco 0; a pasta fica no bloco 2
        .mapBaseIndex = 30,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 1,
        .baseTile = 0,
    }
};

static const struct WindowTemplate sWindowTemplates[] = {
    [WIN_TELA] = {
        .bg = BG_TEXTO,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = DISPLAY_WIDTH / 8,
        .height = DISPLAY_HEIGHT / 8,
        .paletteNum = 0,
        .baseBlock = 1,
    },
    [WIN_COUNT] = DUMMY_WIN_TEMPLATE
};

// {fundo, letra, sombra}; fundo 0 = transparente (aparece a pasta)
static const u8 sCores_Texto[3] = {0, COR_TINTA, COR_TINTA_SOMBRA};
static const u8 sCores_Titulo[3] = {COR_MARCA_TEXTO, COR_VERMELHO, COR_OURO_ESC};

static void CB2_Dossie_Montar(void);
static void CB2_Dossie(void);
static void VBlankCB_Dossie(void);
static void Task_Dossie_Init(u8 taskId);
static void Task_Dossie_Input(u8 taskId);
static void Task_Dossie_Sair(u8 taskId);
static void Dossie_IniciarTela(void);
static void Dossie_CriarSprites(void);
static void Dossie_MostrarPagina(void);

// Special: como OpenNovidadesScreen, só troca o callback; a tela monta no próximo quadro, fora do script de campo.
void Dossie_Abrir(void)
{
    QuestLog_CutRecording();
    SetMainCallback2(CB2_Dossie_Montar);
    LockPlayerFieldControls();
}

static void CB2_Dossie_Montar(void)
{
    SetVBlankHBlankCallbacksToNull();
    ClearScheduledBgCopiesToVram();
    sDossie = AllocZeroed(sizeof(*sDossie));
    sDossie->ajudaAntes = gHelpSystemEnabled;
    gHelpSystemEnabled = FALSE;
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();
    ResetTasks();
    ScanlineEffect_Stop();
    CreateTask(Task_Dossie_Init, 0);
    SetMainCallback2(CB2_Dossie);
}

static void CB2_Dossie(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void VBlankCB_Dossie(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void Task_Dossie_Init(u8 taskId)
{
    switch (sDossie->initState)
    {
    case 0:
        SetVBlankCallback(NULL);
        Dossie_IniciarTela();
        break;
    case 1:
        LoadBgTiles(BG_FUNDO, sPasta_Gfx, sizeof(sPasta_Gfx), 0);
        LoadPalette(sPasta_Pal, BG_PLTT_ID(0), PLTT_SIZE_4BPP);
        Dossie_CriarSprites();
        break;
    case 2:
        Dossie_MostrarPagina();
        break;
    case 3:
        PlayBGM(DOSSIE_MUSICA);
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        SetVBlankCallback(VBlankCB_Dossie);
        break;
    default:
        if (gPaletteFade.active)
            return;
        sDossie->pronta = TRUE;
        gTasks[taskId].func = Task_Dossie_Input;
        return;
    }
    sDossie->initState++;
}

static void Dossie_Fechar(u8 taskId)
{
    PlaySE(SE_SELECT);
    sDossie->pronta = FALSE;
    BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
    gTasks[taskId].func = Task_Dossie_Sair;
}

// A ou → avança (A na última página fecha), ← volta (nada na capa), B fecha.
static void Task_Dossie_Input(u8 taskId)
{
    bool8 ultima = sDossie->pagina + 1 >= DOSSIE_PAGINAS;

    if (JOY_NEW(B_BUTTON) || (JOY_NEW(A_BUTTON) && ultima))
    {
        Dossie_Fechar(taskId);
    }
    else if (JOY_NEW(A_BUTTON) || JOY_NEW(DPAD_RIGHT))
    {
        if (!ultima)
        {
            PlaySE(SE_SELECT);
            sDossie->pagina++;
            Dossie_MostrarPagina();
        }
    }
    else if (JOY_NEW(DPAD_LEFT))
    {
        if (sDossie->pagina > 0)
        {
            PlaySE(SE_SELECT);
            sDossie->pagina--;
            Dossie_MostrarPagina();
        }
    }
}

static void Task_Dossie_Sair(u8 taskId)
{
    if (gPaletteFade.active)
        return;
    gHelpSystemEnabled = sDossie->ajudaAntes;
    ResetSpriteData();
    FreeAllSpritePalettes();
    FreeAllWindowBuffers();
    DestroyTask(taskId);
    FREE_AND_SET_NULL(sDossie);
    SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}

static void Dossie_IniciarTela(void)
{
    DmaClearLarge16(3, (void *)VRAM, VRAM_SIZE, 0x1000);
    DmaClear32(3, (void *)OAM, OAM_SIZE);
    DmaClear16(3, (void *)PLTT, PLTT_SIZE);
    SetGpuReg(REG_OFFSET_DISPCNT, 0);
    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sBgTemplates, ARRAY_COUNT(sBgTemplates));
    ChangeBgX(BG_TEXTO, 0, BG_COORD_SET);
    ChangeBgY(BG_TEXTO, 0, BG_COORD_SET);
    ChangeBgX(BG_FUNDO, 0, BG_COORD_SET);
    ChangeBgY(BG_FUNDO, 0, BG_COORD_SET);
    InitWindows(sWindowTemplates);
    DeactivateAllTextPrinters();
    SetBgTilemapBuffer(BG_FUNDO, sDossie->tilemapBuffer);
    FillBgTilemapBufferRect_Palette0(BG_TEXTO, 0, 0, 0, 32, 32);
    PutWindowTilemap(WIN_TELA);
    CopyBgTilemapBufferToVram(BG_TEXTO);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_1D_MAP | DISPCNT_OBJ_ON);
    ShowBg(BG_TEXTO);
    ShowBg(BG_FUNDO);
}

// Foto e clipe (paleta da foto), carimbo e rosa. O clipe fica por cima da foto e o carimbo por cima da foto também
// (subprioridade menor = na frente).
static void Dossie_CriarSprites(void)
{
    u8 i;

    for (i = 0; sSpriteSheets[i].data != NULL; i++)
        LoadSpriteSheet(&sSpriteSheets[i]);
    LoadSpritePalettes(sSpritePalettes);
    sDossie->fotoSprite = CreateSprite(&sTemplate_Foto, FOTO_X, FOTO_Y, 3);
    sDossie->carimboSprite = CreateSprite(&sTemplate_Carimbo, CARIMBO_X, CARIMBO_Y, 1);
    sDossie->clipeSprite = CreateSprite(&sTemplate_Clipe, CLIPE_X, CLIPE_Y, 0);
    sDossie->rosaSprite = CreateSprite(&sTemplate_Rosa, ROSA_FICHA_X, ROSA_FICHA_Y, 0);
}

static void Dossie_Visivel(u8 spriteId, bool8 visivel)
{
    if (spriteId < MAX_SPRITES)
        gSprites[spriteId].invisible = !visivel;
}

// CAPTURADO se o chefe foi capturado (Task 7), DERROTADO se só a rosa dele foi ganha, nenhum se nada disso.
static u8 Dossie_CarimboDoChefe(u8 chefe)
{
    if (chefe < 1 || chefe > 4)
        return CARIMBO_NENHUM;
    if (FamiliaSombra_ChefeCapturado(chefe))
        return CARIMBO_CAPTURADO;
    if (FlagGet(FLAG_FAMILIA_ROSA_1 + chefe - 1))
        return CARIMBO_DERROTADO;
    return CARIMBO_NENHUM;
}

static void Dossie_Imprimir(const u8 *texto, u8 x, u8 y, const u8 *cores)
{
    AddTextPrinterParameterized4(WIN_TELA, FONT_NORMAL, x, y, 0, 0, cores, TEXT_SKIP_DRAW, texto);
}

static void Dossie_ImprimirADireita(const u8 *texto, u16 fim, u8 y)
{
    Dossie_Imprimir(texto, fim - GetStringWidth(FONT_NORMAL, texto, 0), y, sCores_Texto);
}

// O texto linha por linha (cada `\n` é uma linha nova): a 1ª em (x0, y0), as outras em x, a partir de y, de
// DOSSIE_LINHA_PX em DOSSIE_LINHA_PX px. Os códigos de cor de cada linha valem só nela.
static void Dossie_ImprimirLinhas(const u8 *texto, u8 x0, u8 y0, u8 x, u8 y)
{
    u8 n = 0;

    while (TRUE)
    {
        u8 len = 0;

        while (texto[len] != EOS && texto[len] != CHAR_NEWLINE && len < LINHA_BYTES - 1)
        {
            sDossie->linha[len] = texto[len];
            len++;
        }
        sDossie->linha[len] = EOS;
        if (n == 0)
            Dossie_Imprimir(sDossie->linha, x0, y0, sCores_Texto);
        else
            Dossie_Imprimir(sDossie->linha, x, y + (n - 1) * DOSSIE_LINHA_PX, sCores_Texto);
        if (texto[len] != CHAR_NEWLINE)
            break;
        texto += len + 1;
        n++;
    }
}

// Título no marca-texto amarelo, em vermelho
static void Dossie_ImprimirTitulo(const u8 *titulo, u8 x)
{
    FillWindowPixelRect(WIN_TELA, PIXEL_FILL(COR_MARCA_TEXTO), x, MARCA_Y,
                        GetStringWidth(FONT_NORMAL, titulo, 0) + 6, MARCA_H);
    Dossie_Imprimir(titulo, x + 3, TITULO_Y, sCores_Titulo);
}

// Rodapé: ◀ (fora da capa), e à direita "N/T" da pasta com ▶ (fora da última página)
static void Dossie_ImprimirRodape(void)
{
    u8 texto[16];
    u8 *fim;

    if (sDossie->pagina > 0)
    {
        texto[0] = CHAR_LEFT_ARROW;
        texto[1] = EOS;
        Dossie_Imprimir(texto, RODAPE_X, RODAPE_Y, sCores_Texto);
    }
    fim = ConvertIntToDecimalStringN(texto, sDossie->pagina + 1, STR_CONV_MODE_LEFT_ALIGN, 2);
    *fim++ = CHAR_SLASH;
    fim = ConvertIntToDecimalStringN(fim, DOSSIE_PAGINAS, STR_CONV_MODE_LEFT_ALIGN, 2);
    if (sDossie->pagina + 1 < DOSSIE_PAGINAS)
    {
        *fim++ = CHAR_SPACE;
        *fim++ = CHAR_RIGHT_ARROW;
        *fim = EOS;
    }
    Dossie_ImprimirADireita(texto, RODAPE_FIM, RODAPE_Y);
}

// "FOLHA 1/3" no fim da aba da ficha (a parte da ficha do chefe)
static void Dossie_ImprimirFolha(const struct DossiePagina *p)
{
    u8 texto[16];
    u8 *fim = StringCopy(texto, sDossieFolha_Prefixo);

    fim = ConvertIntToDecimalStringN(fim, p->parte, STR_CONV_MODE_LEFT_ALIGN, 1);
    *fim++ = CHAR_SLASH;
    ConvertIntToDecimalStringN(fim, p->partes, STR_CONV_MODE_LEFT_ALIGN, 1);
    Dossie_ImprimirADireita(texto, ABA_FICHA_FIM, ABA_Y);
}

static void Dossie_MostrarPagina(void)
{
    const struct DossiePagina *p = &sDossiePaginas[sDossie->pagina];
    u8 fundo = p->chefe == DOSSIE_CAPA ? FUNDO_CAPA : p->chefe == DOSSIE_DEPOIS ? FUNDO_TEXTO : FUNDO_FICHA;
    bool8 ficha = fundo == FUNDO_FICHA;

    CpuCopy16(&sPasta_Tilemap[fundo * FUNDO_ENTRADAS], sDossie->tilemapBuffer, FUNDO_ENTRADAS * 2);
    CopyBgTilemapBufferToVram(BG_FUNDO);
    FillWindowPixelBuffer(WIN_TELA, PIXEL_FILL(0));

    sDossie->carimbo = ficha ? Dossie_CarimboDoChefe(p->chefe) : CARIMBO_NENHUM;
    Dossie_Visivel(sDossie->fotoSprite, ficha);
    Dossie_Visivel(sDossie->clipeSprite, ficha);
    Dossie_Visivel(sDossie->carimboSprite, sDossie->carimbo != CARIMBO_NENHUM);
    Dossie_Visivel(sDossie->rosaSprite, fundo != FUNDO_CAPA);

    if (fundo == FUNDO_CAPA)
    {
        Dossie_Imprimir(sDossieAba_Policia, ABA_X, ABA_Y, sCores_Texto);
        Dossie_Imprimir(sDossieCapa_Rota, ROTA_CAIXA_X + (ROTA_CAIXA_W - GetStringWidth(FONT_NORMAL, sDossieCapa_Rota, 0)) / 2,
                        ROTA_Y, sCores_Texto);
        Dossie_Imprimir(p->texto, RODAPE_X, RODAPE_Y, sCores_Texto);
    }
    else if (ficha)
    {
        const struct DossieChefe *c = &sDossieChefes[p->chefe - 1];
        u16 tile = GetSpriteTileStartByTag(TAG_FOTO + p->chefe - 1);

        if (sDossie->fotoSprite < MAX_SPRITES && tile != 0xFFFF)
        {
            gSprites[sDossie->fotoSprite].sheetTileStart = tile;
            gSprites[sDossie->fotoSprite].oam.tileNum = tile;
        }
        if (sDossie->carimbo != CARIMBO_NENHUM && sDossie->carimboSprite < MAX_SPRITES)
            StartSpriteAnim(&gSprites[sDossie->carimboSprite], sDossie->carimbo == CARIMBO_CAPTURADO ? 0 : 1);
        if (sDossie->rosaSprite < MAX_SPRITES)
        {
            gSprites[sDossie->rosaSprite].x = ROSA_FICHA_X;
            gSprites[sDossie->rosaSprite].y = ROSA_FICHA_Y;
        }
        LoadPalette(&sRosas_Pal[(p->chefe - 1) * 16], OBJ_PLTT_ID(IndexOfSpritePaletteTag(TAG_ROSA)), PLTT_SIZE_4BPP);
        Dossie_Imprimir(c->aba, ABA_X, ABA_Y, sCores_Texto);
        Dossie_ImprimirFolha(p);
        Dossie_ImprimirTitulo(p->titulo, CAB_X);
        Dossie_Imprimir(c->gemeos, CAB_X + 1, GEMEOS_Y, sCores_Texto);
        Dossie_Imprimir(c->rosa, ROSA_TEXTO_X, ROSA_TEXTO_Y, sCores_Texto);
        Dossie_ImprimirLinhas(p->texto, LORE_TOPO_X, LORE_TOPO_Y, LORE_X, LORE_Y);
    }
    else
    {
        // "Depois": o título, a rosa vermelha que voltou para a menina de Lavender e o texto na largura toda
        u16 fimTitulo = DEPOIS_TITULO_X + GetStringWidth(FONT_NORMAL, p->titulo, 0) + 6;

        if (sDossie->rosaSprite < MAX_SPRITES)
        {
            gSprites[sDossie->rosaSprite].x = fimTitulo + 6 + 4;
            gSprites[sDossie->rosaSprite].y = ROSA_DEPOIS_Y;
        }
        LoadPalette(&sRosas_Pal[0], OBJ_PLTT_ID(IndexOfSpritePaletteTag(TAG_ROSA)), PLTT_SIZE_4BPP);
        Dossie_Imprimir(sDossieAba_Policia, ABA_X, ABA_Y, sCores_Texto);
        Dossie_ImprimirTitulo(p->titulo, DEPOIS_TITULO_X);
        Dossie_ImprimirLinhas(p->texto, LORE_X, DEPOIS_TEXTO_Y, LORE_X, DEPOIS_TEXTO_Y + DOSSIE_LINHA_PX);
    }
    Dossie_ImprimirRodape();
    CopyWindowToVram(WIN_TELA, COPYWIN_GFX);
}

#if TESTBUILD
// Atalho da esteira (TEST_CMD_DOSSIE_ESTADO): 0xFFFFFFFF = tela fechada; senão página (0-based) | total << 8
// | chefe da página (0 capa, 1-4, 5 depois) << 16 | carimbo (0 nenhum, 1 derrotado, 2 capturado) << 24
// | pronta para o input << 31.
u32 Dossie_TestEstado(void)
{
    if (sDossie == NULL)
        return 0xFFFFFFFF;
    return sDossie->pagina | (u32)DOSSIE_PAGINAS << 8 | (u32)sDossiePaginas[sDossie->pagina].chefe << 16
         | (u32)sDossie->carimbo << 24 | (u32)(sDossie->pronta != 0) << 31;
}
#endif // TESTBUILD
