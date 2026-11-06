"""Galeria de textos (POK-29): lista de rótulos, pior caso, atalho em C e índice (sem emulador)."""

import re
from pathlib import Path

import pytest

from esteira import check_text, galeria
from esteira.__main__ import build_parser
from esteira.scenarios import REPO_ROOT

TEXTS = galeria.list_texts()
HOOKS_C = (REPO_ROOT / "src" / "test_hooks.c").read_text(encoding="utf-8")


def test_lista_tem_os_textos_do_campo():
    assert len(TEXTS) >= 3500, len(TEXTS)   # 3812 em 06/11/2026
    files = {t.file for t in TEXTS}
    assert sum(f.startswith("data/maps/") for f in files) >= 280   # 290 mapas com fala
    assert "data/event_scripts.s" in files
    assert "data/text/help_system.inc" not in files      # ajuda: janela própria, não a caixa do campo
    assert "data/text/braille.inc" not in files
    labels = [t.label for t in TEXTS]
    assert len(labels) == len(set(labels))


def test_todo_rotulo_do_mapa_entra():
    source = (REPO_ROOT / "data/maps/PalletTown/text.inc").read_text(encoding="utf-8")
    want = re.findall(r"^(\w+)::", source, re.M)
    got = [t.label for t in TEXTS if t.group == "PalletTown"]
    assert got == want


def test_filtro_por_grupo_e_por_caminho():
    pallet = galeria.select(TEXTS, "PalletTown*")
    assert pallet and {t.group for t in pallet} >= {"PalletTown", "PalletTown_ProfessorOaksLab"}
    assert all(t.group.startswith("PalletTown") for t in pallet)
    both = galeria.select(TEXTS, "PalletTown, data/event_scripts.s")
    assert {t.group for t in both} == {"PalletTown", "event_scripts"}
    assert galeria.select(TEXTS, None) == TEXTS


def test_pior_glifo_e_o_mais_largo_da_fonte_normal():
    env = check_text._load_env(REPO_ROOT)
    ch = galeria.worst_glyph()
    assert ch.isascii() and ch.isalnum()
    assert env.widths["normal"][ch] == env.max_letter["normal"]


def test_tamanhos_do_pior_caso_iguais_no_c():
    assert re.search(rf"#define FIELD_TEXT_VAR_GLYPHS {galeria.VAR_LETTERS}\b", HOOKS_C)
    assert galeria.VAR_LETTERS == check_text.VAR_SIZES["STR_VAR_1"].chars   # o que a checagem de texto mede
    assert "FillGlyphs(gSaveBlock2Ptr->playerName, PLAYER_NAME_LENGTH, glyph)" in HOOKS_C
    assert "FillGlyphs(gSaveBlock1Ptr->rivalName, PLAYER_NAME_LENGTH, glyph)" in HOOKS_C
    length = re.search(r"#define PLAYER_NAME_LENGTH\s+(\d+)",
                       (REPO_ROOT / "include/constants/global.h").read_text(encoding="utf-8"))
    assert int(length.group(1)) == galeria.NAME_LETTERS


def test_script_do_atalho_usa_o_msgbox_padrao():
    macros = (REPO_ROOT / "asm/macros/event.inc").read_text(encoding="utf-8")
    msgbox_default = int(re.search(r"MSGBOX_DEFAULT = (\d+)", macros).group(1))
    assert re.search(rf"#define FIELD_TEXT_MSGBOX_DEFAULT {msgbox_default}\b", HOOKS_C)
    std = (REPO_ROOT / "data/event_scripts.s").read_text(encoding="utf-8")
    table = std.split("gStdScripts::", 1)[1].split("gStdScriptsEnd::", 1)[0]
    entries = re.findall(r"\.4byte (\w+)", table)
    assert entries[msgbox_default] == "Std_MsgboxDefault"
    # o atalho só existe na build de teste
    start = HOOKS_C.index("static u32 ShowFieldText")
    assert HOOKS_C.rindex("#if TESTBUILD", 0, start) < start < HOOKS_C.rindex("#endif // TESTBUILD")


def test_estados_de_parada_batem_com_o_text_h():
    header = (REPO_ROOT / "include/text.h").read_text(encoding="utf-8")
    body = re.search(r"enum\s*\{\s*(RENDER_STATE_HANDLE_CHAR.*?)\}", header, re.S).group(1)
    names = [n.strip() for n in body.split(",") if n.strip()]
    assert names.index("RENDER_STATE_WAIT") == galeria.RENDER_STATE_WAIT
    assert names.index("RENDER_STATE_CLEAR") == galeria.RENDER_STATE_CLEAR
    assert names.index("RENDER_STATE_SCROLL_START") == galeria.RENDER_STATE_SCROLL_START


@pytest.mark.parametrize("elf", ["pokefirered_switch_test.elf", "pokefirered_switch.elf"])
def test_todo_rotulo_tem_um_endereco_no_elf(elf):
    path = REPO_ROOT / elf
    if not path.exists():
        pytest.skip(f"{elf} não existe")
    from esteira.symbols import Symbols
    syms = Symbols.from_elf(str(path))
    missing = [t.label for t in TEXTS if len(syms.addrs(t.label)) != 1]
    assert not missing, missing[:20]


def test_indice_agrupa_por_arquivo(tmp_path: Path):
    shots = [
        {"label": "A_Text_1", "file": "data/maps/X/text.inc", "group": "X", "source": "Oi\\p{PLAYER}$",
         "pages": ["img/X/A_Text_1_1.png", "img/X/A_Text_1_2.png"], "status": "ok", "detail": "", "frames": 9},
        {"label": "B_<Text>", "file": "data/maps/Y/text.inc", "group": "Y", "source": "x$", "pages": [],
         "status": "aviso", "detail": "não terminou", "frames": 9},
    ]
    meta = {"filtro": "X*", "glifo": "W", "data": "hoje", "segundos": 1.0}
    page = galeria.write_index(tmp_path, shots, meta).read_text(encoding="utf-8")
    assert page.index("A_Text_1") < page.index("B_&lt;Text&gt;")
    assert page.count("<img ") == 2 and "1/2" in page and "2/2" in page
    assert "não terminou" in page and "<script" not in page and "http" not in page


def test_cli_e_alvo_do_make():
    args = build_parser().parse_args(["galeria", "--out", "x", "--filtro", "PalletTown*"])
    assert args.modo == "galeria" and args.filtro == "PalletTown*"
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    recipe = makefile.split("\ntest-galeria:\n", 1)[1].split("\n\n", 1)[0]
    assert recipe.index("TESTBUILD=1") < recipe.index("$(ESTEIRA_RUNNER)") < recipe.index("esteira galeria")
    assert "$(FILTRO)" in recipe
    assert "test-galeria" in makefile.split("RULES_NO_SCAN +=")[1].splitlines()[0]
