"""Conquistas e diário de batalhas (POK-44), Task 2: o formato no save, o marcador e o núcleo do estado.

O estado das conquistas mora no `SaveBlock1` em `0x348C` (era `unused_348C[400]`) e o diário no `SaveBlock2` em
`0xB20` (era `filler_B20[0x400]`). Todo o resto dos dois blocos fica nos mesmos offsets da base `4be5f6b56`, para
que os saves existentes continuem válidos (eles têm zeros nas duas áreas: magic 0 = save antigo, sem marcador).
"""

import re
import struct
import subprocess

import pytest

from esteira import conquistas as cq
from esteira.scenarios import REPO_ROOT

BASE = "4be5f6b56"
GLOBAL_H = REPO_ROOT / "include" / "global.h"
CONQ_C = REPO_ROOT / "src" / "conquistas.c"
CONQ_H = REPO_ROOT / "include" / "conquistas.h"
NEW_GAME_C = REPO_ROOT / "src" / "new_game.c"
RULES_MK = REPO_ROOT / "json_data_rules.mk"

AREAS = {"SaveBlock1": ("unused_348C", "conquistas"), "SaveBlock2": ("filler_B20", "diario")}


def _campos(texto: str, struct_nome: str) -> dict[str, int]:
    """Nome do campo -> offset do comentário `/*0x....*/` dentro de `struct <nome> { ... };`."""
    corpo = re.search(rf"struct {struct_nome}\n\{{(.*?)\n\}};", texto, re.S).group(1)
    campos = {}
    for off, decl in re.findall(r"/\*(0x[0-9A-Fa-f]+)\*/\s*([^;]+);", corpo):
        nome = re.search(r"(\w+)\s*(?:\[[^\]]*\])*\s*$", decl).group(1)
        campos[nome] = int(off, 16)
    return campos


@pytest.fixture(scope="module")
def global_base() -> str:
    return subprocess.run(["git", "show", f"{BASE}:include/global.h"], cwd=REPO_ROOT, check=True,
                          capture_output=True, encoding="utf-8").stdout


@pytest.mark.parametrize("bloco", sorted(AREAS))
def test_offsets_iguais_a_base(global_base, bloco):
    antigo, novo = AREAS[bloco]
    base = _campos(global_base, bloco)
    atual = _campos(GLOBAL_H.read_text(encoding="utf-8"), bloco)
    assert base.pop(antigo) == atual.pop(novo)
    assert atual == base


def test_offsets_das_areas_e_vizinhos():
    texto = GLOBAL_H.read_text(encoding="utf-8")
    sb1, sb2 = _campos(texto, "SaveBlock1"), _campos(texto, "SaveBlock2")
    assert (sb1["conquistas"], sb1["ramScript"]) == (0x348C, 0x361C)
    assert (sb2["diario"], sb2["encryptionKey"]) == (0xB20, 0xF20)
    assert "struct ConquistasSave conquistas;" in texto and "struct DiarioSave diario;" in texto
    assert "u8 unused_348C[" not in texto and "u8 filler_B20[" not in texto
    assert "POK-44, era unused_348C[400]" in texto and "POK-44, era filler_B20[0x400]" in texto


def test_static_asserts():
    fonte = CONQ_C.read_text(encoding="utf-8")
    for esperado in ("sizeof(struct ConquistasSave) == 400", "sizeof(struct DiarioSave) == 0x400",
                     "sizeof(struct DiarioEntrada) == 20",
                     "offsetof(struct SaveBlock1, conquistas) == 0x348C",
                     "offsetof(struct SaveBlock1, ramScript) == 0x361C",
                     "sizeof(struct SaveBlock1) == 0x3D68",
                     "offsetof(struct SaveBlock2, diario) == 0xB20",
                     "offsetof(struct SaveBlock2, encryptionKey) == 0xF20",
                     "sizeof(struct SaveBlock2) == 0xF24"):
        assert re.search(rf"STATIC_ASSERT\({re.escape(esperado)},", fonte), esperado


def test_layout_da_struct_conquistas_save():
    corpo = re.search(r"struct ConquistasSave\n\{(.*?)\n\};", GLOBAL_H.read_text(encoding="utf-8"), re.S).group(1)
    corpo = re.sub(r"//[^\n]*", "", corpo)
    nomes = [re.search(r"(\w+)\s*(?:\[[^\]]*\])?$", d.strip()).group(1) for d in corpo.split(";") if d.strip()]
    assert nomes == ["magic", "versao", "origem", "resumoPendente", "livre0", "vitoriasTreinador",
                     "shiniesObtidos", "estados", "entregues", "degrauEntregue", "adiadoNoMapa", "livre"]
    assert "livre[354]" in corpo and "estados[CONQ_MAX / 4]" in corpo and "entregues[CONQ_MAX / 8]" in corpo
    assert "degrauEntregue[CONQ_MAX_DEGRAUS]" in corpo


def test_jogo_novo_inicia():
    fonte = NEW_GAME_C.read_text(encoding="utf-8")
    corpo = re.search(r"void NewGameInitData\(void\)\n\{(.*?)\n\}", fonte, re.S).group(1)
    linhas = [l.strip() for l in corpo.splitlines() if l.strip()]
    i = linhas.index("ClearSav1();")
    assert linhas[i + 1] == "Conquistas_IniciarJogoNovo();"
    assert '#include "conquistas.h"' in fonte


def test_interface_do_nucleo():
    h = CONQ_H.read_text(encoding="utf-8")
    for proto in ("void Conquistas_IniciarJogoNovo(void);", "u8 Conquistas_GetEstado(u8 num);",
                  "void Conquistas_Marcar(u8 num);", "void Conquistas_Perder(u8 num);",
                  "bool8 Conquistas_Entregue(u8 num);", "void Conquistas_SetEntregue(u8 num);",
                  "u8 Conquistas_DegrauEntregue(u8 num);", "void Conquistas_SetDegrauEntregue(u8 num, u8 degrau);"):
        assert proto in h, proto
    fonte = CONQ_C.read_text(encoding="utf-8")
    inicio = re.search(r"void Conquistas_IniciarJogoNovo\(void\)\n\{(.*?)\n\}", fonte, re.S).group(1)
    assert "adiadoNoMapa = 0xFFFF" in inicio and "CONQ_MAGIC" in inicio and "CONQ_ORIGEM_JOGO_NOVO" in inicio
    # Marcar só PENDENTE -> FEITA, Perder só PENDENTE -> PERDIDA
    for funcao, alvo in (("Marcar", "CONQ_FEITA"), ("Perder", "CONQ_PERDIDA")):
        corpo = re.search(rf"void Conquistas_{funcao}\(u8 num\)\n\{{(.*?)\n\}}", fonte, re.S).group(1)
        assert "CONQ_PENDENTE" in corpo and alvo in corpo, funcao


def test_c_dep_dos_que_incluem_os_ids():
    """Todo .o que inclui data/conquistas_ids.h espera o header gerado (json_data_rules.mk)."""
    mk = RULES_MK.read_text(encoding="utf-8")
    for c in sorted((REPO_ROOT / "src").glob("*.c")):
        if "data/conquistas_ids.h" in c.read_text(encoding="utf-8", errors="replace"):
            assert re.search(rf"\$\(C_BUILDDIR\)/{c.stem}\.o: c_dep \+=.*conquistas_ids\.h", mk), c.name


def test_parse_entrada_do_diario():
    time = [25 | 12 << 9, 6 | 36 << 9, 0, 0, 0, 0]
    dados = struct.pack("<HBBBBBB6H", 340, 7, 1, 3, 0, 2, 2, *time)
    assert len(dados) == cq.DIARIO_ENTRADA_SIZE == 20
    e = cq.parse_entrada(dados)
    assert e == {"minutos": 340, "turnos": 7, "resultado": 1, "ordem": 3, "mvp": 0, "mvpNocautes": 2,
                 "tamanhoTime": 2, "time": [(25, 12), (6, 36)]}


def test_ids_do_json():
    assert cq.num("treinadores") == 12 and cq.num("horas") == 40
    assert cq.evento("brock") == 0
    with pytest.raises(KeyError):
        cq.num("nao_existe")


def test_cenario_registrado():
    from esteira.__main__ import FULL_SCENARIOS, TEST, WATCH_FULL_SCENARIOS
    from esteira.scenarios import full_conquistas as cen
    spec = next(s for s in FULL_SCENARIOS if s.name == "conquistas")
    assert (spec.run, spec.rom, spec.save_from) == (cen.run_full_conquistas, TEST, "captura")
    assert "conquistas" in WATCH_FULL_SCENARIOS


def test_atalhos_no_bloco_b0():
    from esteira import hooks
    assert (hooks.CMD_CONQ_ESTADO, hooks.CMD_CONQ_CONTADOR, hooks.CMD_CONQ_RESET, hooks.CMD_CONQ_CHECAR) == (
        0xB0, 0xB1, 0xB2, 0xB3)
    for nome in ("conq_estado", "conq_contador", "conq_reset", "conq_checar"):
        assert callable(getattr(hooks.Mailbox, nome)), nome
