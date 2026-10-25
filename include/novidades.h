#ifndef GUARD_NOVIDADES_H
#define GUARD_NOVIDADES_H

#include "global.h"

// Tela de novidades do Prof. Carvalho (docs/superpowers/specs/2026-10-17-novidades-professor-design.md).
//
// Os textos e a estrutura (tópicos -> cartões) moram em src/data/novidades/cartoes.json; o make
// gera src/data/novidades_cartoes.h com tools/novidades/gen_cartoes.py (só `const`, sem EWRAM).
// Esta é a única definição dos tipos e das medidas das janelas: a tela (src/novidades.c) desenha as
// janelas com as constantes abaixo e a checagem de texto da esteira (test/esteira/check_text.py)
// mede cada texto do JSON nelas. Mudou uma constante? Rode test/tests/test_novidades_cartoes.py.

// Quantos tópicos há em gNovidadesTopics (o header gerado confere em tempo de compilação).
#define NOVIDADES_TOPIC_COUNT 11

// Layout do cartão (tela de 240x160, layout B do mockup): barra de título 16 px, imagem 64 px
// (sprite frontal de 64x64; duas espécies lado a lado), uma linha ANTES/AGORA e o corpo.
//   16 + 64 + 13 + 5 * 13 = 158 px.
//
// Nome do tópico (FONT_NORMAL, 1 linha): mostrado na grade, sob o tópico selecionado.
#define NOVIDADES_TOPIC_NAME_WIDTH_PX 160
// Título do cartão (FONT_NORMAL, 1 linha): na barra de cima; o resto da barra fica com "3/7" e as setas.
#define NOVIDADES_TITLE_WIDTH_PX 160
// "ANTES: ..." e "AGORA: ..." (FONT_SMALL, 1 linha cada), lado a lado: 2 * 112 = 224 px.
// O texto guardado já traz o rótulo ("ANTES: troca"); a tela o imprime como está.
#define NOVIDADES_BEFORE_AFTER_WIDTH_PX 112
// Corpo do cartão (FONT_SMALL): janela de 28 tiles com o texto em x = 2; `\n` desce uma linha, sem `\l`/`\p`.
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
// da Task 4 (1 relógio, 2 clima, 3 cartucho, 4 ficha); enquanto ele não existe, vale iconItemId
// (provisório nos tópicos com iconCustom != 0).
struct NovidadesTopic
{
    const u8 *name;
    u16 iconItemId;
    u8 iconCustom;
    const struct NovidadesCard *cards;
    u8 cardCount;
};

extern const struct NovidadesTopic gNovidadesTopics[];

// Special (data/specials.inc): abre a tela de tópicos (src/novidades.c); ao sair (B), volta ao campo e o
// script continua (CB2_ReturnToFieldContinueScript). No script: `special OpenNovidadesScreen` + `waitstate`.
void OpenNovidadesScreen(void);

#if TESTBUILD
// TEST_CMD_NOVIDADES_STATE: 0xFFFFFFFF = tela fechada; senão cursor | pronta para input << 8 | ícones vivos << 16.
u32 Novidades_TestGetState(void);
#endif

#endif // GUARD_NOVIDADES_H
