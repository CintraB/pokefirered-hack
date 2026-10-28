#ifndef GUARD_NOVIDADES_H
#define GUARD_NOVIDADES_H

#include "global.h"

struct SpriteTemplate;

// Tela de novidades do Prof. Carvalho (docs/superpowers/specs/2026-10-17-novidades-professor-design.md).
//
// Os textos e a estrutura (tópicos -> cartões) moram em src/data/novidades/cartoes.json; o make
// gera src/data/novidades_cartoes.h com tools/novidades/gen_cartoes.py (só `const`, sem EWRAM).
// Esta é a única definição dos tipos e das medidas das janelas: a tela (src/novidades.c) desenha as
// janelas com as constantes abaixo e a checagem de texto da esteira (test/esteira/check_text.py)
// mede cada texto do JSON nelas. Mudou uma constante? Rode test/tests/test_novidades_cartoes.py.

// Quantos tópicos há em gNovidadesTopics (o header gerado confere em tempo de compilação).
#define NOVIDADES_TOPIC_COUNT 12

// Layout do cartão (tela de 240x160, layout B do mockup): barra de título 16 px, imagem 64 px
// (sprite frontal de 64x64; duas espécies lado a lado), uma linha ANTES/AGORA, 1 px de creme, a borda
// da caixa (1 px) e o corpo:
//   16 + 64 + 13 + 2 + 5 * 13 = 160 px.
//
// Nome do tópico (FONT_NORMAL, 1 linha): mostrado na grade, sob o tópico selecionado.
#define NOVIDADES_TOPIC_NAME_WIDTH_PX 160
// Título do cartão (FONT_NORMAL, 1 linha): na barra de cima; o resto da barra fica com "3/7" e as setas.
#define NOVIDADES_TITLE_WIDTH_PX 160
// "ANTES: ..." e "AGORA: ..." (FONT_SMALL, 1 linha cada), lado a lado: dois rótulos de 112 px (o
// retângulo azul tem essa largura) com 2 px de vão.
// O texto guardado já traz o rótulo ("ANTES: troca"); a tela o imprime como está.
#define NOVIDADES_BEFORE_AFTER_WIDTH_PX 112
// Corpo do cartão (FONT_SMALL): janela da largura da tela (30 tiles), texto centrado em
// x = (240 - 222) / 2 = 9; `\n` desce uma linha, sem `\l`/`\p`.
// A altura de cada linha é maxLetterHeight (13) + lineSpacing (0) de FONT_SMALL (src/new_menu_helpers.c).
#define NOVIDADES_BODY_WIDTH_PX 222
#define NOVIDADES_BODY_LINES 5
#define NOVIDADES_BODY_LINE_HEIGHT_PX 13

// Imagem do cartão: speciesBefore e speciesAfter (antes -> depois, sprites lado a lado); só speciesBefore
// (uma espécie); só itemId (ícone de item); nada (usa o ícone do tópico). Campos vazios: NULL/0.
struct NovidadesCard
{
    const u8 *title;
    const u8 *before;   // "ANTES: ..." (NULL quando não há linha ANTES/AGORA)
    const u8 *after;    // "AGORA: ..."
    const u8 *body;
    u16 speciesBefore;
    u16 speciesAfter;
    u16 itemId;
};

// Ícone do tópico: iconItemId é o ícone de item do jogo. iconCustom != 0 indexa um dos ícones novos
// (graphics/novidades/icon_*.png: 1 relógio, 2 clima, 3 cartucho, 4 ficha) e prevalece sobre iconItemId.
struct NovidadesTopic
{
    const u8 *name;
    u16 iconItemId;
    u8 iconCustom;
    const struct NovidadesCard *cards;
    u8 cardCount;
};

extern const struct NovidadesTopic gNovidadesTopics[];

// Cria o sprite do ícone do tópico (src/novidades_icones.c): o ícone novo (iconCustom) ou o ícone de item
// (iconItemId), os dois no tamanho e no formato de AddItemIconObject. MAX_SPRITES se não coube.
u8 Novidades_AddTopicIcon(u16 tilesTag, u16 paletteTag, u8 topicId);
// O mesmo, com outro template (só tileTag/paletteTag são trocados): o cartão sem imagem usa em dobro.
u8 Novidades_AddTopicIconWithTemplate(const struct SpriteTemplate *template, u16 tilesTag, u16 paletteTag, u8 topicId);

// Special (data/specials.inc): abre a tela de tópicos (src/novidades.c); ao sair (B), volta ao campo e o
// script continua (CB2_ReturnToFieldContinueScript). No script: `special OpenNovidadesScreen` + `waitstate`.
void OpenNovidadesScreen(void);

#if TESTBUILD
// TEST_CMD_NOVIDADES_STATE: 0xFFFFFFFF = tela fechada; senão cursor | pronta para input << 8 | ícones vivos << 16
// | (cartão aberto + 1, 0 na grade) << 24.
u32 Novidades_TestGetState(void);
// TEST_CMD_NOVIDADES_CARD: 0xFFFFFFFF = fora do cartão; senão tópico | cartão << 8 | imagem << 16 (0 ícone do
// tópico, 1 item, 2 uma espécie, 3 duas) | sprites vivos da imagem << 24.
u32 Novidades_TestGetCard(void);
#endif

#endif // GUARD_NOVIDADES_H
