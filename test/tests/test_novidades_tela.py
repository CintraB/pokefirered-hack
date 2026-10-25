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
