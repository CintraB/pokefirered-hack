"""Tela de novidades do Prof. Carvalho, Task 2: a tela de tópicos (grade com os 11 ícones), sem emulador.

O special `OpenNovidadesScreen` abre uma tela cheia (`src/novidades.c`) no molde de `src/diploma.c` e
`src/teachy_tv.c`: recursos num bloco `AllocZeroed` apontado por um único ponteiro em EWRAM (a EWRAM está
em ~99,58%), liberados na saída, que volta ao campo continuando o script (`CB2_ReturnToFieldContinueScript`).
Na grade, A chama `Novidades_OpenTopic(topicId)` (a Task 3 abre os cartões) e B sai. Na build de teste,
`TEST_CMD_OPEN_NOVIDADES` roda um script de campo com `special OpenNovidadesScreen` e
`TEST_CMD_NOVIDADES_STATE` lê o cursor (a Task 5 liga o Carvalho; a Task 6 faz o cenário da esteira).
"""

import re

from esteira import hooks
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src" / "novidades.c"
HEADER = REPO_ROOT / "include" / "novidades.h"
SPECIALS = REPO_ROOT / "data" / "specials.inc"
TEST_HOOKS_H = REPO_ROOT / "include" / "test_hooks.h"
TEST_HOOKS_C = REPO_ROOT / "src" / "test_hooks.c"
GFX_DIR = REPO_ROOT / "graphics" / "novidades"


def _src() -> str:
    return SRC.read_text(encoding="utf-8")


def _sem_comentarios(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"//[^\n]*", "", code)


def _funcao(code: str, nome: str) -> str:
    """Corpo da função `nome` (do `{` que segue a assinatura até o `}` que o fecha)."""
    m = re.search(rf"^[\w \*]*\b{nome}\s*\([^;{{]*\)\s*\{{", code, re.M)
    assert m, f"função {nome} não encontrada em src/novidades.c"
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(code[i], 0)
        i += 1
    return code[m.end():i - 1]


def test_special_registrado_no_fim_da_tabela():
    linhas = [l.strip() for l in SPECIALS.read_text(encoding="utf-8").splitlines()]
    assert "def_special OpenNovidadesScreen" in linhas
    fim = linhas.index("gSpecialsEnd::")
    defs = [l for l in linhas[:fim] if l.startswith("def_special")]
    # no fim: os números dos specials anteriores (usados pelos scripts já montados) não mudam
    assert defs[-1] == "def_special OpenNovidadesScreen"


def test_special_declarado_e_definido():
    assert re.search(r"^void OpenNovidadesScreen\(void\);", HEADER.read_text(encoding="utf-8"), re.M)
    code = _sem_comentarios(_src())
    corpo = _funcao(code, "OpenNovidadesScreen")
    for chamada in ("QuestLog_CutRecording()", "LockPlayerFieldControls()", "SetMainCallback2("):
        assert chamada in corpo, chamada


def test_um_unico_ewram_data_e_ele_e_um_ponteiro():
    code = _sem_comentarios(_src())
    ewram = re.findall(r"EWRAM_DATA[^;]*;", code)
    assert len(ewram) == 1, ewram
    assert re.fullmatch(r"EWRAM_DATA\s+(?:static\s+)?struct\s+\w+\s*\*\s*\w+\s*=\s*NULL\s*;", ewram[0]) or \
        re.fullmatch(r"static\s+EWRAM_DATA\s+struct\s+\w+\s*\*\s*\w+\s*=\s*NULL\s*;", ewram[0]), ewram[0]
    dados = (REPO_ROOT / "src" / "novidades_data.c")
    if dados.exists():
        assert "EWRAM_DATA" not in _sem_comentarios(dados.read_text(encoding="utf-8"))


def test_static_ewram_data_vira_um_so_ponteiro():
    # `static EWRAM_DATA struct X *sY = NULL;` também conta: nada de buffer/array em EWRAM
    code = _sem_comentarios(_src())
    assert len(re.findall(r"\bEWRAM_DATA\b", code)) == 1


def test_recursos_alocados_e_liberados_na_saida():
    code = _sem_comentarios(_src())
    ponteiro = re.search(r"EWRAM_DATA\s+struct\s+\w+\s*\*\s*(\w+)", code).group(1)
    assert re.search(rf"{ponteiro}\s*=\s*AllocZeroed\(sizeof\(\*{ponteiro}\)\)", code)
    saida = _funcao(code, "Task_Novidades_Exit")
    for chamada in ("FreeAllWindowBuffers()", f"FREE_AND_SET_NULL({ponteiro})",
                    "SetMainCallback2(CB2_ReturnToFieldContinueScript)", "DestroyTask("):
        assert chamada in saida, chamada
    # sprites e paletas dos ícones: soltos antes de liberar o bloco
    assert "Novidades_DestroyIcons()" in saida
    assert saida.index("Novidades_DestroyIcons()") < saida.index(f"FREE_AND_SET_NULL({ponteiro})")
    # o AddItemIconObject monta o template numa variável local: DestroySpriteAndFreeResources leria um
    # ponteiro velho (revisão da Task 2). Libera por tag, como a bolsa, e só então destrói o sprite.
    icones = _funcao(code, "Novidades_DestroyIcons")
    assert "DestroySpriteAndFreeResources(" not in icones
    assert "FreeSpriteTilesByTag(TAG_NOVIDADES_ICON + i)" in icones
    assert "FreeSpritePaletteByTag(TAG_NOVIDADES_ICON + i)" in icones
    assert icones.index("FreeSpritePaletteByTag(") < icones.index("DestroySprite(")
    assert "DestroySpriteAndFreeResources(" not in code


def test_abertura_zera_hblank_e_copias_de_bg_agendadas():
    abrir = _funcao(_sem_comentarios(_src()), "CB2_OpenNovidades")
    assert "SetVBlankHBlankCallbacksToNull()" in abrir and "ClearScheduledBgCopiesToVram()" in abrir


def test_icones_da_grade_vem_dos_topicos():
    code = _sem_comentarios(_src())
    criar = _funcao(code, "Novidades_CreateIcons")
    assert "NOVIDADES_TOPIC_COUNT" in criar
    assert "AddItemIconObject(" in criar
    assert "gNovidadesTopics[" in code
    # iconCustom != 0: ícone novo da Task 4; até lá vale o iconItemId provisório, marcado no código
    assert "Novidades_GetIconItemId" in criar
    assert "iconItemId" in _funcao(code, "Novidades_GetIconItemId")
    assert "PROVISÓRIO" in _src() and "Task 4" in _src()


def test_janela_do_nome_tem_a_largura_da_constante():
    code = _sem_comentarios(_src())
    assert re.search(r"\.width\s*=\s*NOVIDADES_TOPIC_NAME_WIDTH_PX\s*/\s*8", code)
    assert "NOVIDADES_TOPIC_NAME_WIDTH_PX" in _funcao(code, "Novidades_PrintTopicName")


def test_a_abre_o_topico_e_b_sai():
    code = _sem_comentarios(_src())
    entrada = _funcao(code, "Task_Novidades_HandleInput")
    a = entrada.index("A_BUTTON")
    b = entrada.index("B_BUTTON")
    assert "Novidades_OpenTopic(" in entrada[a:]
    assert "BeginNormalPaletteFade(" in entrada[b:]
    assert re.search(r"static void Novidades_OpenTopic\(u8 topicId\)", code)


def test_cursor_na_grade():
    code = _sem_comentarios(_src())
    mover = _funcao(code, "Novidades_MoveCursor")
    for tecla in ("DPAD_LEFT", "DPAD_RIGHT", "DPAD_UP", "DPAD_DOWN"):
        assert tecla in _funcao(code, "Task_Novidades_HandleInput") or tecla in mover, tecla
    assert "NOVIDADES_GRID_COLUMNS" in mover and "NOVIDADES_TOPIC_COUNT" in mover


def test_fundo_em_graphics_novidades():
    assert (GFX_DIR / "fundo.png").is_file()
    assert (GFX_DIR / "fundo.pal").is_file()
    code = _src()
    assert 'INCBIN_U32("graphics/novidades/fundo.4bpp' in code
    assert 'INCBIN_U16("graphics/novidades/fundo.gbapal")' in code
    pal = (GFX_DIR / "fundo.pal").read_text(encoding="ascii").split()
    assert pal[:2] == ["JASC-PAL", "0100"] and int(pal[2]) == 16


def test_atalhos_de_teste_da_tela():
    h = TEST_HOOKS_H.read_text(encoding="utf-8")
    assert "TEST_CMD_OPEN_NOVIDADES = 0x90" in h
    assert "TEST_CMD_NOVIDADES_STATE" in h
    assert hooks.CMD_OPEN_NOVIDADES == 0x90 and hooks.CMD_NOVIDADES_STATE == 0x91
    c = TEST_HOOKS_C.read_text(encoding="utf-8")
    assert "case TEST_CMD_OPEN_NOVIDADES:" in c and "case TEST_CMD_NOVIDADES_STATE:" in c
    # o hook abre pelo special de verdade (o mesmo `special` que o Carvalho vai usar)
    assert "OpenNovidadesScreen" in c and "gSpecials" in c
    code = _src()
    estado = code[code.index("#if TESTBUILD"):]
    assert "Novidades_TestGetState" in estado


# --- Task 3: cartões (imagem, ANTES/AGORA, corpo, ◀▶) ---------------------------------------------------

def _define(code: str, nome: str) -> int:
    m = re.search(rf"^#define\s+{nome}\s+(0x[0-9A-Fa-f]+|\d+)", code, re.M)
    assert m, f"#define {nome} não encontrado"
    return int(m.group(1), 0)


def test_a_na_grade_abre_o_cartao_do_topico():
    code = _sem_comentarios(_src())
    abrir = _funcao(code, "Novidades_OpenTopic")
    # começa no primeiro cartão do tópico e troca para a visão de cartão (o stub da Task 2 só tocava som)
    assert re.search(r"->card\s*=\s*0\s*;", abrir), abrir
    assert "Novidades_ShowCardView()" in abrir


def test_janelas_do_cartao_usam_as_constantes_do_header():
    code = _sem_comentarios(_src())
    # título na barra: a janela tem a largura da constante (mais o recuo de CARD_TITLE_X px)
    assert re.search(r"\[WIN_CARD_TITLE\][^}]*\.width\s*=\s*\(CARD_TITLE_X\s*\+\s*NOVIDADES_TITLE_WIDTH_PX\s*\+\s*7\)\s*/\s*8",
                     code, re.S)
    texto = _funcao(code, "Novidades_PrintCardText")
    for const in ("NOVIDADES_BEFORE_AFTER_WIDTH_PX", "FONT_SMALL", "CARD_BODY_X", "CARD_BODY_Y"):
        assert const in texto, const
    # as medidas cabem na janela e na tela: conferido em tempo de compilação
    for conta in (r"CARD_CHIPS_X\s*\+\s*2\s*\*\s*NOVIDADES_BEFORE_AFTER_WIDTH_PX\s*<=\s*DISPLAY_WIDTH",
                  r"CARD_BODY_X\s*\+\s*NOVIDADES_BODY_WIDTH_PX\s*<=\s*DISPLAY_WIDTH",
                  r"CARD_BODY_Y\s*\+\s*NOVIDADES_BODY_LINES\s*\*\s*NOVIDADES_BODY_LINE_HEIGHT_PX\s*<=\s*CARD_TEXT_HEIGHT\s*\*\s*8",
                  r"CARD_TEXT_TOP\s*\+\s*CARD_TEXT_HEIGHT\s*<=\s*DISPLAY_TILE_HEIGHT"):
        assert re.search(rf"STATIC_ASSERT\(\s*{conta}", code), conta
    titulo = _funcao(code, "Novidades_PrintCardTitle")
    assert "FONT_NORMAL" in titulo and "CARD_TITLE_X" in titulo


def test_antes_agora_so_quando_o_cartao_tem():
    code = _sem_comentarios(_src())
    texto = _funcao(code, "Novidades_PrintCardText")
    assert re.search(r"if\s*\(\s*card->before\s*!=\s*NULL\s*\)", texto), texto
    assert "card->after" in texto and "card->body" in texto


def test_regra_do_limite_para_no_primeiro_e_no_ultimo_sem_dar_a_volta():
    """Review Focus 5: ◀ no primeiro cartão e ▶ no último não fazem nada (nem som), igual à grade;
    tópico de um cartão só fica parado. A regra está escrita no código e aqui."""
    src = _src()
    regra = re.search(r"// Regra do limite[^\n]*\n(?://[^\n]*\n)*static bool8 Novidades_MoveCard\(void\)", src)
    assert regra and "sem dar a volta" in regra.group(0)
    code = _sem_comentarios(src)
    mover = _funcao(code, "Novidades_MoveCard")
    esq = mover[mover.index("DPAD_LEFT"):]
    dir_ = mover[mover.index("DPAD_RIGHT"):]
    assert re.search(r"if\s*\(\s*card\s*>\s*0\s*\)\s*card--", esq), mover
    assert re.search(r"if\s*\(\s*card\s*\+\s*1\s*<\s*\w+->cardCount\s*\)\s*card\+\+", dir_), mover
    # nada de módulo / volta ao começo
    assert "%" not in mover and "cardCount - 1;" not in mover
    entrada = _funcao(code, "Task_Novidades_CardInput")
    assert "JOY_REPT(DPAD_LEFT | DPAD_RIGHT)" in entrada
    # o som só toca quando o cartão muda
    assert re.search(r"if\s*\(\s*Novidades_MoveCard\(\)\s*\)\s*\{[^}]*PlaySE\(SE_SELECT\)", entrada, re.S)


def test_indicador_de_posicao_e_setas_nos_limites():
    code = _sem_comentarios(_src())
    pos = _funcao(code, "Novidades_PrintCardPosition")
    assert "ConvertIntToDecimalStringN(" in pos and "CHAR_SLASH" in pos and "cardCount" in pos
    # as setas da barra somem no limite (◀ no primeiro, ▶ no último)
    barra = _funcao(code, "Novidades_DrawCardBar")
    assert "TILE_BAR_ARROW_LEFT" in barra and "TILE_BAR_ARROW_RIGHT" in barra
    assert re.search(r"card\s*>\s*0", barra) and re.search(r"card\s*\+\s*1\s*<", barra)


def test_b_no_cartao_volta_a_grade_no_mesmo_topico():
    code = _sem_comentarios(_src())
    entrada = _funcao(code, "Task_Novidades_CardInput")
    b = entrada[entrada.index("B_BUTTON"):]
    assert "Novidades_ShowGridView()" in b
    # o cursor da grade não muda: quem volta não mexe em ->cursor
    grade = _funcao(code, "Novidades_ShowGridView")
    assert "->cursor =" not in grade and "->cursor =" not in entrada
    for chamada in ("Novidades_DestroyCardImage()", "Novidades_DrawBackground()", "Novidades_PrintTitle()",
                    "Novidades_PrintTopicName()"):
        assert chamada in grade, chamada
    assert "gTasks[taskId].func = Task_Novidades_HandleInput" in b


def test_imagem_do_cartao_quatro_tipos():
    code = _sem_comentarios(_src())
    criar = _funcao(code, "Novidades_CreateCardImage")
    # duas espécies (antes ➜ depois), uma espécie, item, ou o ícone do tópico
    assert "Novidades_CreateMonPic(" in criar and "speciesAfter" in criar and "speciesBefore" in criar
    assert "CreateMonPicSprite(" in _funcao(code, "Novidades_CreateMonPic")
    assert "card->itemId" in criar and "Novidades_GetIconItemId(" in criar
    assert "AddItemIconObjectWithCustomObjectTemplate(" in criar
    # espécie normal (sem brilho): personalidade fixa que não é shiny
    assert "NOVIDADES_PIC_PERSONALITY" in _funcao(code, "Novidades_CreateMonPic")
    assert _define(code, "NOVIDADES_PIC_PERSONALITY") & 0xFFFF != 0
    # a seta entre as duas espécies vem do fundo
    assert "TILE_BIG_ARROW" in code


def test_troca_de_cartao_libera_sprites_e_paletas():
    code = _sem_comentarios(_src())
    mostrar = _funcao(code, "Novidades_ShowCard")
    assert "Novidades_DestroyCardImage()" in mostrar and "Novidades_CreateCardImage()" in mostrar
    assert mostrar.index("Novidades_DestroyCardImage()") < mostrar.index("Novidades_CreateCardImage()")
    soltar = _funcao(code, "Novidades_DestroyCardImage")
    assert "FreeAndDestroyMonPicSprite(" in soltar
    assert "FreeSpritePaletteByTag(TAG_NOVIDADES_PIC" in soltar
    # ícone do cartão: por tag (template local do AddItemIcon*), mais a matriz afim do sprite em dobro
    for chamada in ("FreeSpriteTilesByTag(TAG_NOVIDADES_CARD_ICON)", "FreeSpritePaletteByTag(TAG_NOVIDADES_CARD_ICON)",
                    "FreeSpriteOamMatrix(", "DestroySprite("):
        assert chamada in soltar, chamada
    # na visão de cartão, os ícones da grade saem (folga de paletas de OBJ) e voltam na grade
    assert "Novidades_DestroyIcons()" in _funcao(code, "Novidades_ShowCardView")
    assert "Novidades_CreateIcons()" in _funcao(code, "Novidades_ShowGridView")
    # saída da tela também solta a imagem do cartão, antes de liberar o bloco
    saida = _funcao(code, "Task_Novidades_Exit")
    assert "Novidades_DestroyCardImage()" in saida
    assert saida.index("Novidades_DestroyCardImage()") < saida.index("FREE_AND_SET_NULL(")


def test_tags_do_cartao_nao_colidem_com_os_icones_da_grade():
    code = _sem_comentarios(_src())
    icone = _define(code, "TAG_NOVIDADES_ICON")
    cartao = _define(code, "TAG_NOVIDADES_CARD_ICON")
    pic = _define(code, "TAG_NOVIDADES_PIC")
    grade = set(range(icone, icone + 11))
    assert cartao not in grade and pic not in grade and pic + 1 not in grade
    assert len({cartao, pic, pic + 1}) == 3
    # as pics usam slot de paleta reservado pelo alocador (tag), não um número solto
    pic_fn = _funcao(code, "Novidades_CreateMonPic")
    assert "AllocSpritePalette(" in pic_fn and "TAG_NONE" in pic_fn
    assert re.search(r"STATIC_ASSERT\(\s*TAG_NOVIDADES_ICON\s*\+\s*NOVIDADES_TOPIC_COUNT\s*<=\s*TAG_NOVIDADES_CARD_ICON", code)


def test_cartao_sem_ewram_novo_e_dentro_do_bloco():
    code = _sem_comentarios(_src())
    assert len(re.findall(r"\bEWRAM_DATA\b", code)) == 1
    struct = re.search(r"struct Novidades\s*\{(.*?)\};", code, re.S).group(1)
    for campo in ("view", "card", "cardSpriteIds"):
        assert re.search(rf"\b{campo}\b", struct), campo


def test_atalho_de_teste_do_cartao():
    h = TEST_HOOKS_H.read_text(encoding="utf-8")
    assert re.search(r"TEST_CMD_NOVIDADES_CARD,", h)
    assert hooks.CMD_NOVIDADES_CARD == 0x92
    c = TEST_HOOKS_C.read_text(encoding="utf-8")
    assert "case TEST_CMD_NOVIDADES_CARD:" in c and "Novidades_TestGetCard()" in c
    assert re.search(r"^u32 Novidades_TestGetCard\(void\);", HEADER.read_text(encoding="utf-8"), re.M)
    estado = _src()[_src().index("#if TESTBUILD"):]
    assert "Novidades_TestGetCard" in estado
