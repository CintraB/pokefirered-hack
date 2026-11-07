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
    defs = [l for l in linhas[:fim] if l.startswith("def_special") and "FamiliaSombra_" not in l
            and "MestreGolpes_" not in l and "KrabbySize" not in l and "SalaTrofeus_" not in l
            and "Dossie_" not in l]  # POK-51 e POK-54 vêm depois
    # no fim: os números dos specials anteriores (usados pelos scripts já montados) não mudam
    assert defs[defs.index("def_special OpenNovidadesScreen") + 1:] == [
        "def_special GetRepelToReuse", "def_special UseRepelFromField",   # POK-31, depois dele
        "def_special StartPortablePc",                                      # POK-36
        "def_special Conquistas_MostrarAviso",                              # POK-44
        "def_special Conquistas_AbrirTelaDoScript",                         # POK-44, Task 7
        "def_special ShouldUseLeagueRematchTeams",                          # POK-42, Task 3
        "def_special BufferRematchTierName",                                # POK-42, Task 4
        "def_special ShowRematchTierMenu"]                                  # POK-42, onda final


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


def test_abertura_zera_a_tabela_de_pics():
    # sSpritePics é global (trainer_pokemon_sprites.c): a tela não depende de quem a abriu tê-la zerado
    abrir = _funcao(_sem_comentarios(_src()), "CB2_OpenNovidades")
    assert "ResetAllPicSprites()" in abrir
    assert abrir.index("ResetSpriteData()") < abrir.index("ResetAllPicSprites()")


ICONES_SRC = REPO_ROOT / "src" / "novidades_icones.c"
ICONES_NOVOS = {1: "relogio", 2: "clima", 3: "cartucho", 4: "ficha"}  # iconCustom -> nome do arquivo


def _ler_png(path):
    """(largura, altura, profundidade de bits, tipo de cor, índices usados) de um PNG indexado."""
    import struct
    import zlib

    dados = path.read_bytes()
    assert dados[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} não é PNG"
    pos, idat, ihdr = 8, b"", None
    while pos < len(dados):
        n, tipo = struct.unpack(">I4s", dados[pos:pos + 8])
        corpo = dados[pos + 8:pos + 8 + n]
        if tipo == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", corpo)
        elif tipo == b"IDAT":
            idat += corpo
        pos += 12 + n
    largura, altura, bits, cor, _, _, entrelacado = ihdr
    assert entrelacado == 0
    cru = zlib.decompress(idat)
    por_linha = (largura * bits + 7) // 8
    usados = set()
    anterior = bytearray(por_linha)
    for y in range(altura):
        base = y * (por_linha + 1)
        filtro, linha = cru[base], bytearray(cru[base + 1:base + 1 + por_linha])
        assert filtro in (0, 1, 2, 3, 4)
        for i in range(por_linha):
            a_ = linha[i - 1] if i >= 1 else 0
            b_ = anterior[i]
            c_ = anterior[i - 1] if i >= 1 else 0
            if filtro == 1:
                linha[i] = (linha[i] + a_) & 255
            elif filtro == 2:
                linha[i] = (linha[i] + b_) & 255
            elif filtro == 3:
                linha[i] = (linha[i] + (a_ + b_) // 2) & 255
            elif filtro == 4:
                p = a_ + b_ - c_
                pa, pb, pc = abs(p - a_), abs(p - b_), abs(p - c_)
                pred = a_ if pa <= pb and pa <= pc else (b_ if pb <= pc else c_)
                linha[i] = (linha[i] + pred) & 255
        anterior = linha
        for x in range(largura):
            byte = linha[x * bits // 8]
            usados.add((byte >> (8 - bits - (x * bits) % 8)) & ((1 << bits) - 1))
    return largura, altura, bits, cor, usados


def test_icones_novos_existem_24x24_4bpp_e_ate_16_cores():
    for nome in ICONES_NOVOS.values():
        png = GFX_DIR / f"icon_{nome}.png"
        assert png.is_file(), f"falta {png.name}"
        largura, altura, bits, cor, usados = _ler_png(png)
        assert (largura, altura) == (24, 24), f"{png.name}: {largura}x{altura}"
        assert (bits, cor) == (4, 3), f"{png.name}: precisa ser indexado de 4 bits"
        assert len(usados) <= 16 and max(usados) < 16
        assert 0 in usados, f"{png.name}: o índice 0 (transparente) precisa existir (fundo do ícone)"
        assert 1 in usados, f"{png.name}: sem contorno escuro (índice 1), como os ícones de item"
        pal = (GFX_DIR / f"icon_{nome}.pal").read_bytes()
        assert pal.count(b"\r\n") == pal.count(b"\n"), "paleta JASC em CRLF"
        linhas = pal.decode("ascii").split("\r\n")
        assert linhas[:3] == ["JASC-PAL", "0100", "16"]
        assert len([l for l in linhas[3:] if l]) == 16, f"icon_{nome}.pal precisa de 16 cores"


def test_icones_da_grade_vem_dos_topicos():
    code = _sem_comentarios(_src())
    criar = _funcao(code, "Novidades_CreateIcons")
    assert "NOVIDADES_TOPIC_COUNT" in criar
    assert "Novidades_AddTopicIcon(" in criar
    assert "PROVISÓRIO" not in _src(), "a Task 4 trocou os ícones provisórios"
    # a escolha entre ícone de item e ícone novo mora em src/novidades_icones.c
    icones = _sem_comentarios(ICONES_SRC.read_text(encoding="utf-8"))
    topico = _funcao(icones, "Novidades_AddTopicIcon")
    assert "gNovidadesTopics[" in icones
    assert "iconCustom" in topico and "iconItemId" in topico
    assert "AddItemIconObject(" in topico and "AddItemIconObjectFromGfx(" in topico


def test_tela_referencia_os_quatro_icones_novos():
    icones = ICONES_SRC.read_text(encoding="utf-8")
    for nome in ICONES_NOVOS.values():
        assert f'INCBIN_U32("graphics/novidades/icon_{nome}.4bpp.lz")' in icones, nome
        assert f'INCBIN_U32("graphics/novidades/icon_{nome}.gbapal.lz")' in icones, nome
    # os tópicos do JSON usam exatamente os 4 ícones novos, cada um uma vez
    import json

    json_path = REPO_ROOT / "src" / "data" / "novidades" / "cartoes.json"
    usados = sorted(t["iconCustom"] for t in json.loads(json_path.read_text(encoding="utf-8"))["topics"]
                    if t["iconCustom"])
    assert usados == sorted(ICONES_NOVOS), usados


def test_icone_proprio_usa_o_mesmo_caminho_do_icone_de_item():
    # o ícone novo sai pelo mesmo sprite do ícone de item (tiles 3x3 copiados para 4x4, 0x200 bytes)
    sem = _sem_comentarios((REPO_ROOT / "src" / "item_menu_icons.c").read_text(encoding="utf-8"))
    # um corpo só (com template) serve ao ícone de item, ao ícone novo e às versões com template próprio
    base = _funcao(sem, "AddItemIconObjectFromGfxWithTemplate")
    assert "CopyItemIconPicTo4x4Buffer(" in base and "CreateSprite(" in base
    assert "AddItemIconObjectFromGfxWithTemplate(&sSpriteTemplate_ItemIcon" in _funcao(sem, "AddItemIconObjectFromGfx")
    assert "AddItemIconObjectFromGfx(" in _funcao(sem, "AddItemIconObject")
    assert "AddItemIconObjectFromGfxWithTemplate(" in _funcao(sem, "AddItemIconObjectWithCustomObjectTemplate")
    header = (REPO_ROOT / "include" / "item_menu_icons.h").read_text(encoding="utf-8")
    assert "AddItemIconObjectFromGfx(" in header and "AddItemIconObjectFromGfxWithTemplate(" in header


def test_cartao_sem_imagem_mostra_o_icone_novo_do_topico():
    # o cartão sem imagem usa o ícone do tópico em dobro (template afim do cartão, tag do cartão): o ícone
    # novo quando o tópico tem iconCustom, senão o ícone de item
    code = _sem_comentarios(_src())
    assert "Novidades_GetIconItemId" not in code
    criar = _funcao(code, "Novidades_CreateCardImage")
    assert re.search(r"Novidades_AddTopicIconWithTemplate\(&sSpriteTemplate_CardIcon,\s*TAG_NOVIDADES_CARD_ICON,"
                     r"\s*TAG_NOVIDADES_CARD_ICON,\s*sNovidades->cursor\)", criar)
    icones = _sem_comentarios(ICONES_SRC.read_text(encoding="utf-8"))
    topico = _funcao(icones, "Novidades_AddTopicIconWithTemplate")
    assert "iconCustom" in topico and "iconItemId" in topico
    assert "AddItemIconObjectFromGfxWithTemplate(" in topico
    assert "AddItemIconObjectWithCustomObjectTemplate(" in topico
    assert re.search(r"^u8 Novidades_AddTopicIconWithTemplate\(const struct SpriteTemplate \*",
                     HEADER.read_text(encoding="utf-8"), re.M)


def test_comentario_do_json_nao_chama_o_icone_de_provisorio():
    import json

    json_path = REPO_ROOT / "src" / "data" / "novidades" / "cartoes.json"
    comentario = json.loads(json_path.read_text(encoding="utf-8"))["_comentario"]
    assert "provisório" not in comentario.lower()


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
    for conta in (r"CARD_CHIPS_X\s*\+\s*2\s*\*\s*NOVIDADES_BEFORE_AFTER_WIDTH_PX\s*\+\s*CARD_CHIPS_GAP\s*<=\s*DISPLAY_WIDTH",
                  r"CARD_BODY_X\s*\+\s*NOVIDADES_BODY_WIDTH_PX\s*<=\s*DISPLAY_WIDTH",
                  r"CARD_BODY_Y\s*\+\s*NOVIDADES_BODY_LINES\s*\*\s*NOVIDADES_BODY_LINE_HEIGHT_PX\s*<=\s*CARD_TEXT_HEIGHT\s*\*\s*8",
                  r"CARD_TEXT_TOP\s*\+\s*CARD_TEXT_HEIGHT\s*<=\s*DISPLAY_TILE_HEIGHT"):
        assert re.search(rf"STATIC_ASSERT\(\s*{conta}", code), conta
    titulo = _funcao(code, "Novidades_PrintCardTitle")
    assert "FONT_NORMAL" in titulo and "CARD_TITLE_X" in titulo


def test_rotulo_antes_agora_tem_a_largura_da_medida():
    # o retângulo azul tem os mesmos NOVIDADES_BEFORE_AFTER_WIDTH_PX que a esteira mede para o texto
    code = _sem_comentarios(_src())
    texto = _funcao(code, "Novidades_PrintCardText")
    assert re.search(r"FillWindowPixelRect\(WIN_CARD_TEXT,\s*PIXEL_FILL\(COLOR_NAVY\),\s*chipX,\s*0,\s*"
                     r"NOVIDADES_BEFORE_AFTER_WIDTH_PX,", texto), texto
    assert re.search(r"chipX\s*=\s*CARD_CHIPS_X\s*\+\s*i\s*\*\s*\(NOVIDADES_BEFORE_AFTER_WIDTH_PX\s*\+\s*CARD_CHIPS_GAP\)", texto)
    assert _define(code, "CARD_CHIPS_GAP") >= 1


def test_comentarios_de_medida_batem_com_a_tela():
    header = HEADER.read_text(encoding="utf-8")
    assert "158" not in header and "158" not in _src()
    assert "16 + 64 + 13 + 2 + 5 * 13 = 160" in header
    assert "28 tiles" not in header and "x = 2;" not in header


def test_base_block_das_janelas_em_macros():
    code = _sem_comentarios(_src())
    nomes = ("WIN_TITLE_BASE_BLOCK", "WIN_TOPIC_NAME_BASE_BLOCK", "CARD_TITLE_BASE_BLOCK", "CARD_POS_BASE_BLOCK",
             "CARD_TEXT_BASE_BLOCK", "NOVIDADES_WINDOWS_END")
    for nome in nomes:
        assert re.search(rf"^#define\s+{nome}\b", code, re.M), nome
    for win, macro in (("WIN_TITLE", "WIN_TITLE_BASE_BLOCK"), ("WIN_TOPIC_NAME", "WIN_TOPIC_NAME_BASE_BLOCK"),
                       ("WIN_CARD_TITLE", "CARD_TITLE_BASE_BLOCK"), ("WIN_CARD_POS", "CARD_POS_BASE_BLOCK"),
                       ("WIN_CARD_TEXT", "CARD_TEXT_BASE_BLOCK")):
        assert re.search(rf"\[{win}\][^}}]*\.baseBlock\s*=\s*{macro},", code, re.S), win
    assert re.search(r"STATIC_ASSERT\(\s*NOVIDADES_WINDOWS_END\s*<=\s*512", code)


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
    assert "card->itemId" in criar and "Novidades_AddTopicIconWithTemplate(" in criar
    assert "AddItemIconObjectWithCustomObjectTemplate(" in criar
    # espécie normal (sem brilho): personalidade fixa que não é shiny
    assert "NOVIDADES_PIC_PERSONALITY" in _funcao(code, "Novidades_CreateMonPic")
    otid = _define(code, "NOVIDADES_PIC_OTID")
    pers = _define(code, "NOVIDADES_PIC_PERSONALITY")
    brilho = (otid >> 16) ^ (otid & 0xFFFF) ^ (pers >> 16) ^ (pers & 0xFFFF)  # GET_SHINY_VALUE
    odds = _define((REPO_ROOT / "include" / "constants" / "pokemon.h").read_text(encoding="utf-8"), "SHINY_ODDS")
    assert brilho >= odds, f"valor de brilho {brilho:#x} < SHINY_ODDS {odds}: o Pokémon do cartão sairia shiny"
    assert "NOVIDADES_PIC_OTID" in _funcao(code, "Novidades_CreateMonPic")
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
