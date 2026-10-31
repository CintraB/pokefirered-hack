"""POK-43 sem emulador: categoria (físico/especial/estado) por golpe, igual à Gen 6.

Confere o snapshot tools/gen6/gen6.json (gerado da PokéAPI por tools/gen6/gerar.py) e se cada
entrada de src/data/battle_moves.h traz a categoria do snapshot.
"""

import json
import re

from esteira.scenarios import REPO_ROOT

GEN6 = json.loads((REPO_ROOT / "tools" / "gen6" / "gen6.json").read_text(encoding="utf-8"))
BATTLE_MOVES = (REPO_ROOT / "src" / "data" / "battle_moves.h").read_text(encoding="utf-8")
POKEMON_H = (REPO_ROOT / "include" / "pokemon.h").read_text(encoding="utf-8")
CATEGORIAS = {"PHYSICAL", "SPECIAL", "STATUS"}


def _entradas() -> dict[str, str]:
    """MOVE_X -> corpo da entrada `[MOVE_X] = { ... }` de battle_moves.h."""
    return {m.group(1): m.group(2)
            for m in re.finditer(r"^    \[(MOVE_\w+)\] =\s*\{(.*?)^    \},", BATTLE_MOVES, re.M | re.S)}


def test_snapshot_completo():
    cats = GEN6["categories"]
    assert len(cats) == 360
    assert [c for c in cats.values() if c not in CATEGORIAS] == []
    esperado = {
        "MOVE_FIRE_PUNCH": "PHYSICAL", "MOVE_CRUNCH": "PHYSICAL", "MOVE_SHADOW_BALL": "SPECIAL",
        "MOVE_HIDDEN_POWER": "SPECIAL", "MOVE_WEATHER_BALL": "SPECIAL",
        "MOVE_STRUGGLE": "PHYSICAL", "MOVE_BEAT_UP": "PHYSICAL",
        "MOVE_SEISMIC_TOSS": "PHYSICAL", "MOVE_NIGHT_SHADE": "SPECIAL", "MOVE_GROWL": "STATUS",
    }
    assert {k: cats[k] for k in esperado} == esperado


def test_categoria_de_cada_golpe():
    entradas = _entradas()
    assert len(entradas) == len(GEN6["categories"]) + 1          # MOVE_NONE + 1..MOVES_COUNT-1
    errados = {}
    for nome, corpo in entradas.items():
        if nome == "MOVE_NONE":
            continue
        achado = re.findall(r"\.category = (MOVE_CATEGORY_\w+),", corpo)
        esperado = f"MOVE_CATEGORY_{GEN6['categories'][nome]}"
        if achado != [esperado]:
            errados[nome] = (achado, esperado)
    assert errados == {}


def test_struct_tem_category_no_fim():
    corpo = re.search(r"struct BattleMove\s*\{(.*?)\};", POKEMON_H, re.S).group(1)
    campos = [linha.strip() for linha in corpo.splitlines() if linha.strip()]
    assert campos[-1] == "u8 category;"


# --- Task 2: o motor de batalha usa a categoria do golpe ------------------------------------

SRC = REPO_ROOT / "src"
BATTLE_H = (REPO_ROOT / "include" / "battle.h").read_text(encoding="utf-8")
POKEMON_C = (SRC / "pokemon.c").read_text(encoding="utf-8")
SCRIPT_CMDS = (SRC / "battle_script_commands.c").read_text(encoding="utf-8")
AI_SCRIPTS = (REPO_ROOT / "data" / "battle_ai_scripts.s").read_text(encoding="utf-8")
AI_CMDS = (SRC / "battle_ai_script_commands.c").read_text(encoding="utf-8")
AI_MACROS = (REPO_ROOT / "asm" / "macros" / "battle_ai_script.inc").read_text(encoding="utf-8")
TEST_HOOKS_C = (SRC / "test_hooks.c").read_text(encoding="utf-8")


def _funcao(texto: str, assinatura: str) -> str:
    """Corpo de uma função C de nível superior (da assinatura até a `}` na coluna 0)."""
    inicio = re.search(re.escape(assinatura) + r"[^;{]*\n\{", texto).start()  # a definição, não o protótipo
    return texto[inicio:texto.index("\n}\n", inicio)]


def _bloco_ia(rotulo: str) -> str:
    """Linhas de um rótulo de script de IA até o próximo rótulo."""
    m = re.search(rf"^{rotulo}::\n(.*?)^\S", AI_SCRIPTS, re.M | re.S)
    return m.group(1)


def test_sem_is_type_physical():
    achados = []
    for pasta in ("src", "include"):
        for arq in (REPO_ROOT / pasta).rglob("*"):
            if arq.suffix in (".c", ".h") and arq.is_file():
                texto = arq.read_text(encoding="utf-8", errors="replace")
                if "IS_TYPE_PHYSICAL" in texto or "IS_TYPE_SPECIAL" in texto:
                    achados.append(str(arq.relative_to(REPO_ROOT)))
    assert achados == []
    assert "#define IS_MOVE_PHYSICAL(move) (gBattleMoves[move].category == MOVE_CATEGORY_PHYSICAL)" in BATTLE_H
    assert "#define IS_MOVE_SPECIAL(move) (gBattleMoves[move].category == MOVE_CATEGORY_SPECIAL)" in BATTLE_H


def test_dano_usa_categoria():
    corpo = _funcao(POKEMON_C, "s32 CalculateBaseDamage(")
    assert "\n    if (IS_MOVE_PHYSICAL(move))\n    {\n        if (gCritMultiplier == 2)" in corpo
    assert "\n    if (IS_MOVE_SPECIAL(move))\n    {\n        if (gCritMultiplier == 2)" in corpo
    assert "\n    if (type == TYPE_MYSTERY)\n        damage = 0;" in corpo
    # bônus do item de tipo: o atributo segue a categoria
    item = corpo[corpo.index("sHoldEffectToType[i][1]"):corpo.index("// Apply boosts from hold items")]
    assert re.search(r"if \(IS_MOVE_PHYSICAL\(move\)\)[^\n]*\n\s*attack = ", item)


def test_thick_fat_corta_o_atributo_do_golpe():
    corpo = _funcao(POKEMON_C, "s32 CalculateBaseDamage(")
    m = re.search(r"ABILITY_THICK_FAT && \(type == TYPE_FIRE \|\| type == TYPE_ICE\)\)\s*\{(.*?)\n    \}", corpo, re.S)
    assert m, "bloco do Thick Fat"
    bloco = m.group(1)
    assert re.search(r"if \(IS_MOVE_PHYSICAL\(move\)\)\s*attack /= 2;", bloco)
    assert re.search(r"if \(IS_MOVE_SPECIAL\(move\)\)\s*spAttack /= 2;", bloco)


def test_counter_mirror_coat():
    corpo = _funcao(SCRIPT_CMDS, "static void Cmd_datahpupdate(void)")
    assert "if (IS_MOVE_PHYSICAL(gCurrentMove) && !(gHitMarker & HITMARKER_PASSIVE_DAMAGE) && gCurrentMove != MOVE_PAIN_SPLIT)" in corpo
    assert "else if (IS_MOVE_SPECIAL(gCurrentMove) && !(gHitMarker & HITMARKER_PASSIVE_DAMAGE))" in corpo
    hustle = _funcao(SCRIPT_CMDS, "static void Cmd_accuracycheck(void)")
    assert "ability == ABILITY_HUSTLE && IS_MOVE_PHYSICAL(move))" in hustle


def test_ia_counter_por_categoria():
    for rotulo, cat, baixa in (("AI_CV_Counter4", "PHYSICAL", "AI_CV_Counter_ScoreDown1"),
                               ("AI_CV_MirrorCoat4", "SPECIAL", "AI_CV_MirrorCoat_ScoreDown1")):
        bloco = _bloco_ia(rotulo)
        assert "get_move_type_from_result" not in bloco, rotulo
        assert f"\tget_move_category_from_result\n\tif_not_equal MOVE_CATEGORY_{cat}, {baixa}\n" in bloco, rotulo
    # o comando novo: macro no fim do .inc e entrada no fim da tabela
    assert re.search(r"\.macro get_move_category_from_result\n\t\.byte 0x5e\n\t\.endm", AI_MACROS)
    tabela = re.search(r"sBattleAICmdTable\[\] =\s*\{(.*?)\};", AI_CMDS, re.S).group(1)
    assert tabela.strip().splitlines()[-1].strip() == "Cmd_get_move_category_from_result,     // 0x5E"
    assert "gBattleMoves[AI_THINKING_STRUCT->funcResult].category" in AI_CMDS


def test_ia_defesa_por_categoria():
    """DefenseUp/SpDefUp também adivinhavam 'físico' pela lista de tipos do golpe."""
    for rotulo, comando in (("AI_CV_DefenseUp4", "if_not_equal MOVE_CATEGORY_PHYSICAL, AI_CV_DefenseUp_ScoreDown2"),
                            ("AI_CV_SpDefUp4", "if_equal MOVE_CATEGORY_PHYSICAL, AI_CV_SpDefUp_ScoreDown2")):
        bloco = _bloco_ia(rotulo)
        assert "get_move_type_from_result" not in bloco, rotulo
        assert f"\tget_move_category_from_result\n\t{comando}\n" in bloco, rotulo
    assert "AI_CV_DefenseUp_PhysicalTypes" not in AI_SCRIPTS
    assert "AI_CV_SpDefUp_PhysicalTypes" not in AI_SCRIPTS


def test_atalho_calc_damage():
    from esteira import hooks
    assert hooks.CMD_CALC_DAMAGE == 0xA0
    assert callable(getattr(hooks.Mailbox, "calc_damage", None))
    assert "case TEST_CMD_CALC_DAMAGE:" in TEST_HOOKS_C
