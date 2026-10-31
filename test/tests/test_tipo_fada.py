"""POK-45 sem emulador: o tipo Fada no motor e nos dados, como na Gen 6.

Lê o C como texto e o snapshot tools/gen6/gen6.json (PokéAPI). O que não é Fada tem que ficar
igual ao da base deste pacote (hack-switch 759447339, SHA fixo), lida pelo `git show`.
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

BASE = "759447339662d5680268db3f3b38f44f44ecd88c"   # hack-switch na criação desta branch (SHA fixo: a hack-switch vai andar)
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


# --- Task 4: ícones FADA e de categoria nas telas ----------------------------------------------

MENU_H = (REPO_ROOT / "include" / "menu.h").read_text(encoding="utf-8")
LIST_MENU_C = (SRC / "list_menu.c").read_text(encoding="utf-8")
SUMMARY_C = (SRC / "pokemon_summary_screen.c").read_text(encoding="utf-8")
TM_CASE_C = (SRC / "tm_case.c").read_text(encoding="utf-8")
POKEDEX_ORDERS = "src/data/pokemon/pokedex_orders.h"
MENU_INFO_PNG = "graphics/interface/menu_info.png"


def _constantes_dos_icones() -> dict[str, int]:
    """TYPE_*, NUMBER_OF_MON_TYPES e MENU_INFO_ICON_* resolvidos a partir dos headers."""
    env = {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (TYPE_\w+)\s+(\d+)$", POKEMON_CONST_H, re.M)}
    env["NUMBER_OF_MON_TYPES"] = int(re.search(r"^#define NUMBER_OF_MON_TYPES (\d+)$", POKEMON_CONST_H, re.M).group(1))
    for m in re.finditer(r"^#define (MENU_INFO_ICON_\w+)\s+(.+)$", MENU_H, re.M):
        env[m.group(1)] = eval(m.group(2), {}, dict(env))   # só nomes e somas dos headers
    return env


def _icones_do_menu_info() -> dict[int, tuple[int, int, int]]:
    corpo = re.search(r"sMenuInfoIcons\[\] =\s*\{(.*?)\n\};", LIST_MENU_C, re.S).group(1)
    env = _constantes_dos_icones()
    icones = {}
    for m in re.finditer(r"\[([^\]]+)\]\s*=\s*\{\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+|\d+)\s*\}", corpo):
        indice = eval(m.group(1), {}, dict(env))
        assert indice not in icones, m.group(1)
        icones[indice] = (int(m.group(2)), int(m.group(3)), int(m.group(4), 0))
    return icones


def _png_da_base(caminho: str):
    from io import BytesIO
    from PIL import Image
    if shutil.which("git") is None:
        pytest.skip("precisa do git")
    dados = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{BASE}:{caminho}"], check=True,
                           capture_output=True).stdout
    return Image.open(BytesIO(dados))


def test_icone_fada_e_categorias():
    from PIL import Image
    env = _constantes_dos_icones()
    # as 3 categorias vêm logo depois de EFFECT, na ordem de MOVE_CATEGORY_* (0, 1, 2)
    assert env["MENU_INFO_ICON_PHYSICAL"] == env["MENU_INFO_ICON_EFFECT"] + 1
    assert env["MENU_INFO_ICON_SPECIAL"] == env["MENU_INFO_ICON_EFFECT"] + 2
    assert env["MENU_INFO_ICON_STATUS"] == env["MENU_INFO_ICON_EFFECT"] + 3
    for nome, valor in (("PHYSICAL", 0), ("SPECIAL", 1), ("STATUS", 2)):
        assert re.search(rf"^#define MOVE_CATEGORY_{nome}\s+{valor}$", POKEMON_CONST_H, re.M)

    icones = _icones_do_menu_info()
    assert sorted(icones) == list(range(env["MENU_INFO_ICON_STATUS"] + 1))   # nenhum buraco {0, 0, 0}
    novos = [TYPE_FAIRY + 1] + [env[f"MENU_INFO_ICON_{c}"] for c in ("PHYSICAL", "SPECIAL", "STATUS")]
    for i in novos:
        assert icones[i][:2] == (32, 12), i                  # mesmo tamanho dos ícones de tipo
    assert len({icones[i][2] for i in icones}) == len(icones)   # offsets distintos

    img = Image.open(REPO_ROOT / MENU_INFO_PNG)
    base = _png_da_base(MENU_INFO_PNG)
    assert img.size[0] == 128 and img.mode == "P"
    assert img.getpalette() == base.getpalette()

    # retângulos de tiles: dentro da folha, sem passar da coluna 15 e sem sobrepor outro ícone
    ocupados = {}
    for i, (w, h, off) in icones.items():
        col, lin = off % 16, off // 16
        cols, lins = -(-w // 8), -(-h // 8)
        assert col + cols <= 16 and (lin + lins) * 8 <= img.size[1], i
        for c in range(col, col + cols):
            for l in range(lin, lin + lins):
                assert (c, l) not in ocupados, (i, ocupados.get((c, l)), (c, l))
                ocupados[(c, l)] = i

    # cada ícone novo está desenhado (não é área vazia) e os antigos não mudaram de desenho
    px = img.load()
    for i in novos:
        w, h, off = icones[i]
        x0, y0 = off % 16 * 8, off // 16 * 8
        assert sum(1 for x in range(x0, x0 + w) for y in range(y0, y0 + h) if px[x, y] & 15) > w * h // 2, i
    corpo_base = re.search(r"sMenuInfoIcons\[\] =\s*\{(.*?)\n\};", _git_show("src/list_menu.c"), re.S).group(1)
    bpx = base.load()
    for m in re.finditer(r"\[([^\]]+)\]\s*=\s*\{\s*(\d+),\s*(\d+),\s*(0x[0-9A-Fa-f]+|\d+)\s*\}", corpo_base):
        chave = m.group(1).replace(" ", "")
        indice = eval(chave, {}, dict(env, MENU_INFO_ICON_TYPE=env["MENU_INFO_ICON_TYPE"]))
        w, h, off = int(m.group(2)), int(m.group(3)), int(m.group(4), 0)
        if w == 0:
            continue
        _, _, novo = icones[indice]
        for y in range(h):
            for x in range(w):
                assert px[novo % 16 * 8 + x, novo // 16 * 8 + y] & 15 == \
                       bpx[off % 16 * 8 + x, off // 16 * 8 + y] & 15, (chave, x, y)

    # o resumo usa o ícone de categoria no detalhe do golpe
    detalhe = _funcao(SUMMARY_C, "static void PokeSum_PrintSelectedMoveStats(")
    assert "MENU_INFO_ICON_PHYSICAL + gBattleMoves[" in detalhe and ".category" in detalhe


def test_estojo_de_mt_sem_paleta_de_fada():
    tabela = re.search(r"sTMSpritePaletteOffsetByType\[NUMBER_OF_MON_TYPES\] = \{(.*?)\};", TM_CASE_C, re.S).group(1)
    assert re.search(r"\[TYPE_FAIRY\]\s*= 0x0d0,", tabela)        # explícito: não existe MT Fada
    assert re.search(r"^#define NUM_DISC_COLORS \(17 \* 16\)", TM_CASE_C, re.M)   # 17 paletas, como antes


def _ordem_por_tipo(texto: str) -> list[str]:
    corpo = re.search(r"const u16 gPokedexOrder_Type\[\] =\s*\{(.*?)\};", texto, re.S).group(1)
    return re.findall(r"SPECIES_\w+", corpo)


def _numero_nacional() -> dict[str, int]:
    texto = (REPO_ROOT / "include" / "constants" / "pokedex.h").read_text(encoding="utf-8")
    enum = re.search(r"enum \{(.*?)\};", texto, re.S).group(1)
    nomes = re.findall(r"NATIONAL_DEX_(\w+)", enum)
    return {"SPECIES_" + n: i for i, n in enumerate(nomes)}


def _chave_por_tipo(tipos: dict[str, tuple[str, str]], nacional: dict[str, int], valor: dict[str, int]):
    """Regra de gPokedexOrder_Type: tipo 1, depois o tipo 2 (puro primeiro), depois o nº nacional."""
    def chave(especie: str):
        t1, t2 = (valor[t] for t in tipos[especie])
        return (t1, -1 if t2 == t1 else t2, nacional[especie])
    return chave


def test_pokedex_ordem_por_tipo():
    valor = {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (TYPE_\w+)\s+(\d+)$", POKEMON_CONST_H, re.M)}
    nacional = _numero_nacional()
    base = _ordem_por_tipo(_git_show(POKEDEX_ORDERS))
    nova = _ordem_por_tipo((REPO_ROOT / POKEDEX_ORDERS).read_text(encoding="utf-8"))
    tipos_base = _tipos_das_especies(_git_show("src/data/pokemon/species_info.h"))
    tipos = _tipos_das_especies(SPECIES_INFO)
    for t in (tipos_base, tipos):   # os Unown antigos usam a macro OLD_UNOWN_SPECIES_INFO (Normal puro)
        for e in base:
            t.setdefault(e, ("TYPE_NORMAL", "TYPE_NORMAL"))
    # a regra explica a ordem da base inteira, e a nova é a mesma regra com os tipos novos
    assert base == sorted(base, key=_chave_por_tipo(tipos_base, nacional, valor))
    assert sorted(nova) == sorted(base) and len(nova) == len(set(nova)) == 411
    assert nova == sorted(base, key=_chave_por_tipo(tipos, nacional, valor))
    # as Fada puras ficam juntas, num bloco só, no fim (TYPE_FAIRY é o último tipo)
    puras = [i for i, e in enumerate(nova) if tipos[e] == ("TYPE_FAIRY", "TYPE_FAIRY")]
    assert len(puras) >= 6 and puras == list(range(puras[0], puras[0] + len(puras)))
    assert all(tipos[e][0] == "TYPE_FAIRY" for e in nova[puras[0]:])
