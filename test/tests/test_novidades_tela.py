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
    icones = _funcao(code, "Novidades_DestroyIcons")
    assert "DestroySpriteAndFreeResources(" in icones


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
    base = _funcao(sem, "AddItemIconObjectFromGfx")
    assert "CopyItemIconPicTo4x4Buffer(" in base and "sSpriteTemplate_ItemIcon" in base
    assert "AddItemIconObjectFromGfx(" in _funcao(sem, "AddItemIconObject")
    header = (REPO_ROOT / "include" / "item_menu_icons.h").read_text(encoding="utf-8")
    assert "AddItemIconObjectFromGfx" in header


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
