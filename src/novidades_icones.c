#include "global.h"
#include "item_menu_icons.h"
#include "novidades.h"

// Ícones dos tópicos da tela de novidades (Task 4). Os tópicos com iconCustom != 0 usam um dos 4 ícones
// novos de graphics/novidades/ (24x24, 4bpp, 16 cores, desenhados por tools/novidades/gen_icones.py no
// estilo dos ícones de item); os outros usam o ícone de item do jogo (iconItemId). Os dois saem pelo
// mesmo sprite (AddItemIconObjectFromGfx), então têm o mesmo tamanho e a mesma posição na grade.

static const u32 sIcon_Relogio[] = INCBIN_U32("graphics/novidades/icon_relogio.4bpp.lz");
static const u32 sIconPalette_Relogio[] = INCBIN_U32("graphics/novidades/icon_relogio.gbapal.lz");
static const u32 sIcon_Clima[] = INCBIN_U32("graphics/novidades/icon_clima.4bpp.lz");
static const u32 sIconPalette_Clima[] = INCBIN_U32("graphics/novidades/icon_clima.gbapal.lz");
static const u32 sIcon_Cartucho[] = INCBIN_U32("graphics/novidades/icon_cartucho.4bpp.lz");
static const u32 sIconPalette_Cartucho[] = INCBIN_U32("graphics/novidades/icon_cartucho.gbapal.lz");
static const u32 sIcon_Ficha[] = INCBIN_U32("graphics/novidades/icon_ficha.4bpp.lz");
static const u32 sIconPalette_Ficha[] = INCBIN_U32("graphics/novidades/icon_ficha.gbapal.lz");

// Indexada por iconCustom (1 relógio, 2 clima, 3 cartucho, 4 ficha); o 0 é "ícone de item".
static const u32 *const sCustomIcons[][2] =
{
    [1] = {sIcon_Relogio, sIconPalette_Relogio},
    [2] = {sIcon_Clima, sIconPalette_Clima},
    [3] = {sIcon_Cartucho, sIconPalette_Cartucho},
    [4] = {sIcon_Ficha, sIconPalette_Ficha},
};

u8 Novidades_AddTopicIcon(u16 tilesTag, u16 paletteTag, u8 topicId)
{
    u8 custom = gNovidadesTopics[topicId].iconCustom;

    if (custom != 0 && custom < ARRAY_COUNT(sCustomIcons))
        return AddItemIconObjectFromGfx(tilesTag, paletteTag, sCustomIcons[custom][0], sCustomIcons[custom][1]);
    return AddItemIconObject(tilesTag, paletteTag, gNovidadesTopics[topicId].iconItemId);
}

// O mesmo ícone com outro template (o cartão sem imagem mostra o ícone do tópico em dobro, sprite afim).
u8 Novidades_AddTopicIconWithTemplate(const struct SpriteTemplate *template, u16 tilesTag, u16 paletteTag, u8 topicId)
{
    u8 custom = gNovidadesTopics[topicId].iconCustom;

    if (custom != 0 && custom < ARRAY_COUNT(sCustomIcons))
        return AddItemIconObjectFromGfxWithTemplate(template, tilesTag, paletteTag, sCustomIcons[custom][0], sCustomIcons[custom][1]);
    return AddItemIconObjectWithCustomObjectTemplate(template, tilesTag, paletteTag, gNovidadesTopics[topicId].iconItemId);
}
