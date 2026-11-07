"""POK-54 sem emulador: Dragon Rush, Dark Void (só do Darkrai) e a habilidade Bad Dreams.

Dados de batalha da Gen 4 (spec §7b.4), nomes PT-BR (R1: "Inv. Dragão" e "Vazio Negro"), descrições com o nome
cheio, animações no fim de gBattleAnims_Moves, a trava do Dark Void (`jumpifdarkvoidfails`, 1º comando de
BattleScript_EffectSleep) e o Bad Dreams no fim do turno (1/8 do PS máximo, mínimo 1, só no lado adversário).
O comportamento de verdade fica no cenário `especies` (casos `golpes/*`).
"""

import re

from esteira import check_text as ct
from esteira.reflow import line_widths
from esteira.scenarios import REPO_ROOT

NOVOS = ["MOVE_DRAGON_RUSH", "MOVE_DARK_VOID"]
P, M, C, MC = "FLAG_PROTECT_AFFECTED", "FLAG_MIRROR_MOVE_AFFECTED", "FLAG_MAKES_CONTACT", "FLAG_MAGIC_COAT_AFFECTED"
# golpe: (efeito, poder, tipo, precisão, PP, chance, alvo, flags, categoria)
ESPERADO = {
    "MOVE_DRAGON_RUSH": ("EFFECT_FLINCH_HIT", 100, "TYPE_DRAGON", 75, 10, 20, "MOVE_TARGET_SELECTED", {C, P, M},
                         "MOVE_CATEGORY_PHYSICAL"),
    "MOVE_DARK_VOID": ("EFFECT_SLEEP", 0, "TYPE_DARK", 80, 10, 0, "MOVE_TARGET_BOTH", {P, MC, M},
                       "MOVE_CATEGORY_STATUS"),
}
NOMES = {"MOVE_DRAGON_RUSH": "Inv. Dragão", "MOVE_DARK_VOID": "Vazio Negro"}
NOMES_CHEIOS = {"MOVE_DRAGON_RUSH": "Investida Dragão", "MOVE_DARK_VOID": "Vazio Sombrio"}


def _ler(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _defines(rel: str) -> dict[str, int]:
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (\w+)\s+(\d+)\b", _ler(rel), re.M)}


def _entradas() -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r"^    \[(MOVE_\w+)\] =\s*\{(.*?)^    \},",
                                                        _ler("src/data/battle_moves.h"), re.M | re.S)}


def _campo(corpo: str, nome: str) -> str:
    return re.search(rf"\.{nome} = ([^,]+),", corpo).group(1).strip()


def _dados(nome: str) -> tuple:
    corpo = _entradas()[nome]
    assert _campo(corpo, "priority") == "0", nome
    return (_campo(corpo, "effect"), int(_campo(corpo, "power")), _campo(corpo, "type"), int(_campo(corpo, "accuracy")),
            int(_campo(corpo, "pp")), int(_campo(corpo, "secondaryEffectChance")), _campo(corpo, "target"),
            {f.strip() for f in _campo(corpo, "flags").split("|")}, _campo(corpo, "category"))


def test_constantes():
    k = _defines("include/constants/moves.h")
    assert (k["MOVE_DRAGON_RUSH"], k["MOVE_DARK_VOID"], k["MOVES_COUNT"]) == (361, 362, 363)


def test_dados_dragon_rush():
    assert _dados("MOVE_DRAGON_RUSH") == ESPERADO["MOVE_DRAGON_RUSH"]


def test_dados_dark_void():
    assert _dados("MOVE_DARK_VOID") == ESPERADO["MOVE_DARK_VOID"]


def test_nomes_cabem():
    nomes = dict(re.findall(r"\[(MOVE_\w+)\]\s*=\s*_\(\"([^\"]*)\"\)", _ler("src/data/text/move_names.h")))
    assert {n: nomes.get(n) for n in NOVOS} == NOMES
    assert all(len(v) <= 12 for v in NOMES.values())                        # MOVE_NAME_LENGTH


def test_descricoes_com_o_nome_cheio():
    texto = _ler("src/move_descriptions.c")
    ponteiros = dict(re.findall(r"\[(MOVE_\w+)\s*-\s*1\]\s*=\s*(gMoveDescription_\w+)", texto))
    descricoes = {m.group(1): m.group(2) for m in re.finditer(
        r"const u8 (gMoveDescription_\w+)\[\] = _\(\"((?:[^\"\\]|\\.)*)\"\);", texto)}
    rotulos = set()
    for nome in NOVOS:
        desc = descricoes[ponteiros[nome]]
        assert len(desc.split("\\n")) == 3 and max(line_widths(desc)) <= 15 * 8 - 7, (nome, desc)
        assert NOMES_CHEIOS[nome] in desc.replace("\\n", " "), (nome, desc)
        rotulos |= {nome, ponteiros[nome]}
    entradas = [e for e in ct._sources(REPO_ROOT) if isinstance(e, ct._Entry) and e.label in rotulos]
    assert len(entradas) == 4
    assert ct.english_report(str(REPO_ROOT), entradas) == {}


def test_animacoes_no_fim():
    texto = _ler("data/battle_anim_scripts.s")
    tabela = re.search(r"gBattleAnims_Moves::\n(.*?)\n\n", texto, re.S).group(1)
    alvos = re.findall(r"^\t\.4byte (\w+)", tabela, re.M)
    assert len(alvos) == _defines("include/constants/moves.h")["MOVES_COUNT"]
    assert alvos[-2:] == ["Move_DRAGON_RUSH", "Move_DARK_VOID"]
    for rotulo in alvos[-2:]:
        corpo = re.search(rf"^{rotulo}:\n(.*?)^\tend$", texto, re.M | re.S)
        assert corpo, rotulo


def _funcao(texto: str, assinatura: str) -> str:
    return re.search(rf"{re.escape(assinatura)}\n\{{(.*?)\n\}}", texto, re.S).group(1)


def _case(corpo: str, rotulo: str) -> str:
    return re.search(rf"case {rotulo}:(.*?)(?=\n\s*case |\n\s*default:|\n    \}}\n)", corpo, re.S).group(1)


def _script(rotulo: str) -> list[str]:
    texto = _ler("data/battle_scripts_1.s")
    corpo = re.search(rf"^{rotulo}::\n(.*?)\n\n", texto, re.M | re.S).group(1)
    linhas = [linha.split("@")[0].strip() for linha in corpo.splitlines()]      # sem os comentários
    return [linha for linha in linhas if linha]


def test_dark_void_so_darkrai():
    assert _defines("include/constants/battle_script_commands.h")["VARIOUS_DARK_VOID_CHECK"] == 13
    macro = re.search(r"\.macro jumpifdarkvoidfails (\w+):req\n(.*?)\.endm", _ler("asm/macros/battle_script.inc"),
                      re.S)
    assert macro, "macro jumpifdarkvoidfails"
    assert [x.strip() for x in macro.group(2).strip().splitlines()] == [
        "various BS_ATTACKER, VARIOUS_DARK_VOID_CHECK", f".4byte \\{macro.group(1)}"]
    case = _case(_funcao(_ler("src/battle_script_commands.c"), "static void Cmd_various(void)"),
                 "VARIOUS_DARK_VOID_CHECK")
    assert "gCurrentMove == MOVE_DARK_VOID" in case
    assert "species != SPECIES_DARKRAI" in case
    assert "T1_READ_PTR(gBattlescriptCurrInstr + 3)" in case and "gBattlescriptCurrInstr += 7" in case
    assert _script("BattleScript_EffectSleep")[0] == "jumpifdarkvoidfails BattleScript_ButItFailedAtkStringPpReduce"


def test_bad_dreams_um_oitavo():
    util = _ler("src/battle_util.c")
    case = _case(_funcao(util, "u8 AbilityBattleEffects(u8 caseID, u8 battler, u8 ability, u8 special, u16 moveArg)"),
                 "ABILITY_BAD_DREAMS")
    assert "TrySetBadDreamsTarget(battler, 0)" in case
    assert "BattleScriptPushCursorAndCallback(BattleScript_BadDreamsActivates)" in case
    alvo = _funcao(util, "bool8 TrySetBadDreamsTarget(u8 user, u8 from)")
    assert "GetBattlerSide(i) != GetBattlerSide(user)" in alvo          # só o lado adversário
    assert "gBattleMons[i].status1 & STATUS1_SLEEP" in alvo and "gBattleMons[i].hp != 0" in alvo
    assert "gAbsentBattlerFlags & gBitTable[i]" in alvo
    assert "gBattleMons[i].maxHP / 8" in alvo
    assert re.search(r"if \(gBattleMoveDamage == 0\)\s*gBattleMoveDamage = 1;", alvo)    # mínimo 1
    # o script passa pelos dois adversários: o `various` chama o mesmo filtro a partir do alvo seguinte
    case_v = _case(_funcao(_ler("src/battle_script_commands.c"), "static void Cmd_various(void)"),
                   "VARIOUS_BAD_DREAMS_NEXT_TARGET")
    assert "TrySetBadDreamsTarget(gActiveBattler, gBattlerTarget + 1)" in case_v
    script = _script("BattleScript_BadDreamsActivates")
    assert script[:2] == ["printstring STRINGID_BADDREAMS", "waitmessage B_WAIT_TIME_LONG"]
    assert "healthbarupdate BS_TARGET" in script and "datahpupdate BS_TARGET" in script
    assert "tryfaintmon BS_TARGET" in script
    assert "jumpifbaddreamsnexttarget BattleScript_BadDreamsActivates" in script
    assert script[-1] == "end3"
    assert "extern const u8 BattleScript_BadDreamsActivates[];" in _ler("include/battle_scripts.h")


def test_mensagem_bad_dreams():
    ids = _defines("include/constants/battle_string_ids.h")
    assert ids["STRINGID_BADDREAMS"] == ids["STRINGID_FAMILIADESVIABOLA"] + 1
    assert ids["BATTLESTRINGS_COUNT"] == ids["STRINGID_BADDREAMS"] + 1
    msg = _ler("src/battle_message.c")
    # o artigo "O" vem no texto (o placeholder dá "Rattata inimigo"; test_traducao_g exige o artigo)
    assert 'static const u8 sText_BadDreams[] = _("O {B_DEF_NAME_WITH_PREFIX} é\\natormentado pelo pesadelo!");' in msg
    assert "[STRINGID_BADDREAMS - BATTLESTRINGS_TABLE_START]" in msg


def test_habilidade_nome():
    texto = _ler("src/data/text/abilities.h")
    assert re.search(r'\[ABILITY_BAD_DREAMS\] = _\("Sonhos Ruins"\),', texto)
    assert re.search(r'static const u8 sBadDreamsDescription\[\] = _\("Fere quem dorme a cada turno\."\);', texto)


def test_glossario():
    import json
    termos = json.loads(_ler("test/esteira/glossario.json"))["termos"]
    achados = {(t["en"], t["categoria"]): t["pt"] for t in termos if t.get("frente") == "POK-54"}
    assert achados == {("DRAGON RUSH", "golpe"): "Inv. Dragão", ("DARK VOID", "golpe"): "Vazio Negro",
                       ("BAD DREAMS", "habilidade"): "Sonhos Ruins"}


def test_cenario_especies_tem_os_casos_dos_golpes():
    from esteira import refs
    from esteira.scenarios import full_especies as cen
    texto = _ler("test/esteira/scenarios/full_especies.py")
    for caso in ("dark_void_dupla", "dark_void_so_darkrai", "bad_dreams_dupla", "bad_dreams_aliado",
                 "bad_dreams_acordado", "bad_dreams_desmaiado", "dragon_rush"):
        assert f'"golpes/{caso}:' in texto, caso
    assert cen.SCREEN_POINTS[-2:] == ("golpe_dark_void", "golpe_menu_garchomp")
    assert refs.SHARED_POINTS[-2:] == cen.SCREEN_POINTS[-2:]
    assert len(cen.SEEDS) == 5                                  # Dark Void: até 5 tentativas
