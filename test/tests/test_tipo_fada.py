"""POK-45 sem emulador: o tipo Fada no motor e nos dados, como na Gen 6.

Lê o C como texto e o snapshot tools/gen6/gen6.json (PokéAPI). O que não é Fada tem que ficar
igual ao da branch hack-switch (a base deste pacote), lida pelo `git show`.
"""

import json
import re
import shutil
import subprocess

import pytest

from esteira import battle, hooks, ivev_page
from esteira.scenarios import REPO_ROOT

GEN6 = json.loads((REPO_ROOT / "tools" / "gen6" / "gen6.json").read_text(encoding="utf-8"))
SRC = REPO_ROOT / "src"
POKEMON_CONST_H = (REPO_ROOT / "include" / "constants" / "pokemon.h").read_text(encoding="utf-8")
BATTLE_MAIN_C = (SRC / "battle_main.c").read_text(encoding="utf-8")
BATTLE_MAIN_H = (REPO_ROOT / "include" / "battle_main.h").read_text(encoding="utf-8")
BATTLE_MESSAGE_C = (SRC / "battle_message.c").read_text(encoding="utf-8")
SCRIPT_CMDS = (SRC / "battle_script_commands.c").read_text(encoding="utf-8")
AI_SCRIPTS = (REPO_ROOT / "data" / "battle_ai_scripts.s").read_text(encoding="utf-8")
SPECIES_INFO = (SRC / "data" / "pokemon" / "species_info.h").read_text(encoding="utf-8")
BATTLE_MOVES = (SRC / "data" / "battle_moves.h").read_text(encoding="utf-8")
UNION_ROOM_H = (SRC / "data" / "union_room.h").read_text(encoding="utf-8")
TEST_HOOKS_C = (SRC / "test_hooks.c").read_text(encoding="utf-8")

BASE = "hack-switch"
TYPE_FAIRY = 18
TYPE_MYSTERY = 9

# Triplas da Fada na Gen 6 (atacante, defensor, multiplicador)
TRIPLAS_FADA = {
    ("TYPE_FAIRY", "TYPE_FIGHTING", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_DARK", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_FIRE", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_POISON", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_FAIRY", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_POISON", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_STEEL", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
    ("TYPE_FIGHTING", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_BUG", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_DARK", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_MUL_NO_EFFECT"),
}
# A Gen 6 tira do Aço a resistência a Fantasma e Sombrio
TRIPLAS_REMOVIDAS = [
    ("TYPE_GHOST", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
    ("TYPE_DARK", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
]


def _git_show(caminho: str) -> str:
    if shutil.which("git") is None:
        pytest.skip("precisa do git")
    return subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{BASE}:{caminho}"], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def _triplas(texto: str) -> list[tuple[str, str, str]]:
    corpo = re.search(r"const u8 gTypeEffectiveness\[\d+\] =\s*\{(.*?)\};", texto, re.S).group(1)
    corpo = re.sub(r"//[^\n]*", "", corpo)
    itens = [x.strip() for x in corpo.split(",") if x.strip()]
    assert len(itens) % 3 == 0
    return [tuple(itens[i:i + 3]) for i in range(0, len(itens), 3)]


def _tipos_das_especies(texto: str) -> dict[str, tuple[str, str]]:
    """SPECIES_X -> (tipo1, tipo2), pela primeira `.types` depois de `[SPECIES_X] =`."""
    tipos, atual = {}, None
    for linha in texto.splitlines():
        m = re.match(r"\s*\[(SPECIES_\w+)\]\s*=", linha)
        if m:
            atual = m.group(1)
            continue
        m = re.match(r"\s*\.types = \{(TYPE_\w+), (TYPE_\w+)\},", linha)
        if m and atual and atual not in tipos:
            tipos[atual] = (m.group(1), m.group(2))
    return tipos


def _tipos_dos_golpes(texto: str) -> dict[str, str]:
    return {m.group(1): re.search(r"\.type = (TYPE_\w+),", m.group(2)).group(1)
            for m in re.finditer(r"^    \[(MOVE_\w+)\] =\s*\{(.*?)^    \},", texto, re.M | re.S)}


def _funcao(texto: str, assinatura: str) -> str:
    inicio = re.search(re.escape(assinatura) + r"[^;{]*\n\{", texto).start()
    return texto[inicio:texto.index("\n}\n", inicio)]


def test_tipo_fada_constante():
    assert re.search(r"^#define TYPE_FAIRY\s+18$", POKEMON_CONST_H, re.M)
    assert re.search(r"^#define NUMBER_OF_MON_TYPES 19$", POKEMON_CONST_H, re.M)
    assert re.search(r'^\s*\[TYPE_FAIRY\] = _\("Fada"\),$', BATTLE_MAIN_C, re.M)
    assert ivev_page.load_type_names(REPO_ROOT)[TYPE_FAIRY] == "Fada"


def test_tabela_gen6():
    novas, antigas = _triplas(BATTLE_MAIN_C), _triplas(_git_show("src/battle_main.c"))
    foresight = ("TYPE_FORESIGHT", "TYPE_FORESIGHT", "TYPE_MUL_NO_EFFECT")
    antes_novo, depois_novo = novas[:novas.index(foresight)], novas[novas.index(foresight):]
    antes_velho, depois_velho = antigas[:antigas.index(foresight)], antigas[antigas.index(foresight):]
    # a parte da Foresight (imunidades do Fantasma) e o fim ficam iguais
    assert depois_novo == depois_velho
    for removida in TRIPLAS_REMOVIDAS:
        assert removida in antes_velho and removida not in antes_novo
    mantidas = [t for t in antes_velho if t not in TRIPLAS_REMOVIDAS]
    assert antes_novo[:len(mantidas)] == mantidas
    assert set(antes_novo[len(mantidas):]) == TRIPLAS_FADA
    assert len(antes_novo[len(mantidas):]) == len(TRIPLAS_FADA)
    assert [t for t in novas if "TYPE_FAIRY" in t[:2]] == antes_novo[len(mantidas):]
    # tamanho do vetor nos dois lados do C e no espelho da esteira
    tamanho = 3 * len(novas)
    assert f"const u8 gTypeEffectiveness[{tamanho}] =" in BATTLE_MAIN_C
    assert f"extern const u8 gTypeEffectiveness[{tamanho}];" in BATTLE_MAIN_H
    assert battle.TYPE_TABLE_SIZE == tamanho
    assert tamanho // 3 < 128   # Conversion 2 sorteia Random() % 128 entradas


def test_especies_gen6():
    novas, antigas = _tipos_das_especies(SPECIES_INFO), _tipos_das_especies(_git_show(
        "src/data/pokemon/species_info.h"))
    esperado = {k: tuple(v) for k, v in GEN6["species_types"].items()}
    assert len(esperado) == 18
    assert {k: novas[k] for k in esperado} == esperado
    assert set(novas) == set(antigas)
    mudaram = {k for k in novas if novas[k] != antigas[k]}
    assert mudaram == set(esperado)
    assert [k for k, v in novas.items() if "TYPE_FAIRY" in v and k not in esperado] == []


def test_golpes_viram_fada():
    novos, antigos = _tipos_dos_golpes(BATTLE_MOVES), _tipos_dos_golpes(_git_show("src/data/battle_moves.h"))
    viram = {"MOVE_CHARM", "MOVE_SWEET_KISS", "MOVE_MOONLIGHT"}
    assert {k: novos[k] for k in viram} == dict.fromkeys(viram, "TYPE_FAIRY")
    assert novos["MOVE_CURSE"] == "TYPE_MYSTERY"   # decisão: Curse fica ??? (só esses 3 viram Fada)
    mudaram = {k for k in antigos if novos.get(k) != antigos[k]}
    assert mudaram == viram


def _hp_tipo_velho(type_bits: int) -> int:
    """Fórmula da hack-switch: ((NUMBER_OF_MON_TYPES - 3) * typeBits) / 63 + 1, com 18 tipos."""
    t = (18 - 3) * type_bits // 63 + 1
    return t + 1 if t >= TYPE_MYSTERY else t


def _hp_tipo_novo(type_bits: int) -> int:
    t = 15 * type_bits // 63 + 1
    return t + 1 if t >= TYPE_MYSTERY else t


def test_hidden_power_inalterado():
    calc = _funcao(SCRIPT_CMDS, "void CalcHiddenPower(")
    assert "*type = (15 * typeBits) / 63 + 1;" in calc
    assert "NUMBER_OF_MON_TYPES" not in re.sub(r"//[^\n]*", "", calc)
    assert "if (*type >= TYPE_MYSTERY)\n        (*type)++;" in calc
    tipos = [_hp_tipo_novo(b) for b in range(64)]
    assert tipos == [_hp_tipo_velho(b) for b in range(64)]
    assert TYPE_FAIRY not in tipos and TYPE_MYSTERY not in tipos and 0 not in tipos
    assert len(set(tipos)) == 16
    # o espelho da página de IVs dá o mesmo tipo
    for b in range(64):
        ivs = tuple((b >> i) & 1 for i in (0, 1, 2, 4, 5, 3))  # ordem da página: HP Atk Def SpA SpD Spe
        assert ivev_page.hidden_power(ivs)[0] == _hp_tipo_novo(b)


def test_vetores_por_tipo_completos():
    assert 'const u8 gText_AFairyMove[] = _("golpe Fada");' in BATTLE_MESSAGE_C
    tabela = re.search(r"sATypeMove_Table\[NUMBER_OF_MON_TYPES\] =\s*\{(.*?)\};", BATTLE_MESSAGE_C, re.S).group(1)
    assert re.search(r"\[TYPE_FAIRY\]\s*= gText_AFairyMove", tabela)
    for lista in ("AI_CV_SpAtkDown_SpecialTypeList", "AI_CV_LightScreen_SpecialTypeList",
                  "AI_CV_MirrorCoat_SpecialTypeList"):
        corpo = re.search(rf"^{lista}::\n(.*?)\t\.byte -1\n", AI_SCRIPTS, re.M | re.S).group(1)
        assert "\t.byte TYPE_FAIRY\n" in corpo, lista
    for lista in ("AI_CV_AttackDown_PhysicalTypeList", "AI_CV_Reflect_PhysicalTypeList",
                  "AI_CV_Counter_PhysicalTypeList"):
        corpo = re.search(rf"^{lista}::\n(.*?)\t\.byte -1\n", AI_SCRIPTS, re.M | re.S).group(1)
        assert "TYPE_FAIRY" not in corpo, lista
    # Union Room: a lista tem NUMBER_OF_MON_TYPES itens (17 tipos sem ???, + Fada, + Sair)
    lista = re.search(r"sListMenuItems_TypeNames\[NUMBER_OF_MON_TYPES\] = \{(.*?)\};", UNION_ROOM_H, re.S).group(1)
    assert len(re.findall(r"\{ [^}]+\}", lista)) == 19
    assert "gTypeNames[TYPE_FAIRY]" in lista


def test_atalho_type_effectiveness():
    assert hooks.CMD_TYPE_EFFECTIVENESS == 0xA1
    assert callable(getattr(hooks.Mailbox, "type_effectiveness", None))
    assert "case TEST_CMD_TYPE_EFFECTIVENESS:" in TEST_HOOKS_C
