"""IA com troca preditiva e itens (POK-46), Task 1: estado por batalha, "é chefe" e golpes mostrados.

`src/battle_ai_smart.c` guarda em `gBattleStruct` (memória da batalha, `AllocZeroed` a cada batalha) se o oponente
é um chefe (`aiSmart`: as flags efetivas `gTrainers[].aiFlags | RematchTier_GetAiFlags()` contêm
`AI_SCRIPT_HP_AWARE`, com as exclusões de `BattleAI_SetupAIData`), os golpes que cada Pokémon do jogador já mostrou
nesta batalha e o turno da última troca voluntária da IA. Aqui se confere, lendo o C como texto, que os campos
existem e que os ganchos estão no lugar certo. O comportamento no jogo é conferido pelo atalho
`TEST_CMD_AI_SMART_STATE` (0xD0).

Task 2: troca preditiva e escolha de quem entra (só chefes; o caminho original dos treinadores comuns é comparado
com a base). A decisão no jogo é lida pelo atalho `TEST_CMD_AI_SMART_DECIDE` (0xD1), com a montagem por
`TEST_CMD_SET_ENEMY_MON` (0xD2).
"""

import re
import subprocess

from esteira import hooks
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
BATTLE_H = REPO_ROOT / "include" / "battle.h"
SMART_C = SRC / "battle_ai_smart.c"
SMART_H = REPO_ROOT / "include" / "battle_ai_smart.h"
TEST_HOOKS_H = REPO_ROOT / "include" / "test_hooks.h"

CAMPOS = (
    "u8 aiSmart;",
    "u16 aiRevealedMoves[PARTY_SIZE][MAX_MON_MOVES];",
    "u16 aiVoluntarySwitchTurn[2];",
    "u16 aiHealTurn[2];",
    "u16 aiHealHp[2];",
)
EXCLUSOES = (
    "BATTLE_TYPE_SAFARI", "BATTLE_TYPE_ROAMER", "BATTLE_TYPE_WILD_SCRIPTED", "BATTLE_TYPE_LEGENDARY_FRLG",
    "BATTLE_TYPE_TRAINER_TOWER", "BATTLE_TYPE_EREADER_TRAINER", "BATTLE_TYPE_BATTLE_TOWER", "TRAINER_SECRET_BASE",
)


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _membros_battle_struct() -> list[str]:
    m = re.search(r"^struct BattleStruct\n\{\n(.*?)^\};", _ler(BATTLE_H), re.S | re.M)
    assert m
    return [l.strip() for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("//")]


def test_campos_no_battlestruct():
    membros = _membros_battle_struct()
    for campo in CAMPOS:
        assert campo in membros, campo
    # no fim, depois dos campos do POK-44: os deslocamentos lidos pela esteira (full_conquistas.py) não mudam
    assert membros[-len(CAMPOS):] == list(CAMPOS), membros[-6:]


def test_interface():
    h = _ler(SMART_H)
    for proto in ("void SmartAI_InitBattle(void);", "bool8 AI_IsSmartTrainer(void);",
                  "void SmartAI_RecordPlayerMove(u8 battler, u16 move);",
                  "void SmartAI_NoteVoluntarySwitch(u8 battler);"):
        assert proto in h, proto


def test_chefe_por_hp_aware():
    corpo = _corpo(_ler(SMART_C), "SmartAI_InitBattle")
    assert "AI_SCRIPT_HP_AWARE" in corpo
    assert "RematchTier_GetAiFlags()" in corpo
    assert "gTrainers[gTrainerBattleOpponent_A].aiFlags" in corpo
    assert "BATTLE_TYPE_TRAINER" in corpo  # sem treinador (selvagem) não é chefe
    for nome in EXCLUSOES:
        assert nome in corpo, nome
    # o resto começa zerado e as marcas de turno em 0xFFFF (= nunca), antes de qualquer saída antecipada
    primeiro_return = corpo.index("return;")
    for marca in ("aiVoluntarySwitchTurn", "aiHealTurn", "aiHealHp", "aiRevealedMoves", "aiSmart = FALSE"):
        assert marca in corpo[:primeiro_return], marca
    assert "SMART_AI_NEVER" in corpo
    assert re.search(r"#define SMART_AI_NEVER\s+0xFFFF\b", _ler(SMART_H))


def test_init_uma_vez_por_batalha():
    chamadas = []
    for arq in sorted(SRC.rglob("*.c")):
        if arq.name == "battle_ai_smart.c":
            continue
        for n, linha in enumerate(_ler(arq).splitlines(), 1):
            if "SmartAI_InitBattle(" in linha:
                chamadas.append((arq.name, n))
    assert chamadas and len(chamadas) == 1 and chamadas[0][0] == "battle_main.c", chamadas
    corpo = _corpo(_ler(SRC / "battle_main.c"), "CB2_InitBattleInternal")
    assert corpo.count("SmartAI_InitBattle();") == 1
    assert corpo.index("CreateNPCTrainerParty(&gEnemyParty[0], gTrainerBattleOpponent_A);") \
        < corpo.index("SmartAI_InitBattle();")


def test_grava_golpe_usado():
    fonte = _ler(SRC / "battle_script_commands.c")
    attackstring = _corpo(fonte, "Cmd_attackstring")
    # só quando o "X usou Y!" é de fato mostrado (golpe usado; sono/paralisia/recuo não mostram)
    assert "SmartAI_RecordPlayerMove(gBattlerAttacker, gCurrentMove);" in attackstring
    assert attackstring.index("STRINGID_USEDMOVE") < attackstring.index("SmartAI_RecordPlayerMove(")
    ia = _ler(SRC / "battle_ai_script_commands.c")
    assert "SmartAI_RecordPlayerMove" not in _corpo(ia, "RecordLastUsedMoveByTarget")
    assert "SmartAI_RecordPlayerMove" not in ia


def test_grava_golpe_filtros():
    corpo = _corpo(_ler(SMART_C), "SmartAI_RecordPlayerMove")
    for nome in ("B_SIDE_PLAYER", "MOVE_NONE", "0xFFFF", "MOVE_STRUGGLE", "gBattlerPartyIndexes[battler]",
                 "aiRevealedMoves"):
        assert nome in corpo, nome


def test_troca_voluntaria_marcada():
    corpo = _corpo(_ler(SRC / "battle_ai_switch_items.c"), "AI_TrySwitchOrUseItem")
    ramo = corpo[corpo.index("if (ShouldSwitch())"):corpo.index("else if (ShouldUseItem())")]
    assert "SmartAI_NoteVoluntarySwitch(gActiveBattler);" in ramo
    nota = _corpo(_ler(SMART_C), "SmartAI_NoteVoluntarySwitch")
    assert "gBattleResults.battleTurnCounter" in nota


def test_hook_d0():
    assert re.search(r"TEST_CMD_AI_SMART_STATE\s*=\s*0xD0\b", _ler(TEST_HOOKS_H))
    assert hooks.CMD_AI_SMART_STATE == 0xD0
    assert "case TEST_CMD_AI_SMART_STATE:" in _ler(SRC / "test_hooks.c")


# --- Task 2: troca preditiva e escolha de quem entra ------------------------------------------------------------
# Só os chefes: em ShouldSwitch/AI_TrySwitchOrUseItem/GetMostSuitableMonToSwitchInto todo uso do módulo novo fica
# atrás de `if (AI_IsSmartTrainer())`; tirando esses blocos, o C é o mesmo da base aa076d3d3.

SWITCH_C = SRC / "battle_ai_switch_items.c"
BASE_SHA = "aa076d3d3"
FUNCOES_ORIGINAIS = ("ShouldSwitch", "AI_TrySwitchOrUseItem", "GetMostSuitableMonToSwitchInto")


def _sem_blocos_do_chefe(corpo: str) -> str:
    """O corpo sem os `if (AI_IsSmartTrainer()...)` (bloco com chaves ou 1 comando) e sem comentário do POK-46."""
    linhas = corpo.splitlines()
    saida, i = [], 0
    while i < len(linhas):
        l = linhas[i].strip()
        if l.startswith("if (AI_IsSmartTrainer()"):
            if i + 1 < len(linhas) and linhas[i + 1].strip() == "{":
                nivel, i = 0, i + 1
                while True:
                    nivel += linhas[i].count("{") - linhas[i].count("}")
                    i += 1
                    if nivel == 0:
                        break
            else:
                i += 2
            continue
        if l.startswith("// POK-46"):
            i += 1
            continue
        saida.append(linhas[i].rstrip())
        i += 1
    return "\n".join(saida)


def _base(rel: str) -> str:
    return subprocess.run(["git", "show", f"{BASE_SHA}:{rel}"], cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def test_comum_nao_muda():
    novo, velho = _ler(SWITCH_C), _base("src/battle_ai_switch_items.c")
    for nome in FUNCOES_ORIGINAIS:
        corpo = _corpo(novo, nome)
        assert "if (AI_IsSmartTrainer()" in corpo, nome
        sem = _sem_blocos_do_chefe(corpo)
        assert [l for l in sem.splitlines() if "SmartAI_" in l] == [], nome  # todo SmartAI_ atrás do chefe
        assert sem == "\n".join(l.rstrip() for l in _corpo(velho, nome).splitlines()), nome
    # as outras funções do arquivo (reações originais, itens) não mudam nesta task
    for nome in ("ShouldSwitchIfPerishSong", "ShouldSwitchIfWonderGuard", "FindMonThatAbsorbsOpponentsMove",
                 "ShouldSwitchIfNaturalCure", "HasSuperEffectiveMoveAgainstOpponents", "AreStatsRaised",
                 "FindMonWithFlagsAndSuperEffective"):
        assert _corpo(novo, nome) == _corpo(velho, nome), nome


def test_interface_task2():
    h = _ler(SMART_H)
    sem_comentarios = re.sub(r"//[^\n]*", "", h)
    assert re.search(r"struct SmartAiDecision\s*\{\s*u8 action;\s*u8 partySlot;\s*u16 item;\s*\};", sem_comentarios)
    for nome, valor in (("SMART_AI_ATTACK", 0), ("SMART_AI_SWITCH", 1), ("SMART_AI_ITEM", 2)):
        assert re.search(rf"#define {nome}\s+{valor}\b", h), nome
    for proto in ("u8 SmartAI_ThreatTypes(u8 opponentBattler, u8 *types, u8 max);",
                  "bool8 SmartAI_CanKoFirst(u8 battler, u8 target);",
                  "u8 SmartAI_ScoreBench(u8 partySlot, u8 opponentBattler);",
                  "bool8 SmartAI_ChoosePredictiveSwitch(u8 battler, struct SmartAiDecision *out);",
                  "u8 SmartAI_ChooseReplacement(u8 battler);",
                  "bool8 SmartAI_SwitchedLastTurn(u8 battler);",
                  "void SmartAI_Decide(u8 battler, bool8 noStayRoll, struct SmartAiDecision *out);"):
        assert proto in h, proto


def test_so_simples():
    fonte = _ler(SMART_C)
    assert "PredictiveSwitch(battler, out, TRUE)" in _corpo(fonte, "SmartAI_ChoosePredictiveSwitch")
    corpo = _corpo(fonte, "PredictiveSwitch")
    assert "BATTLE_TYPE_DOUBLE" in corpo[:corpo.index("return FALSE;")]   # o 1º teste do corpo
    assert corpo.index("BATTLE_TYPE_DOUBLE") < corpo.index("SmartAI_ThreatTypes(")


def test_limiares_troca():
    fonte = _ler(SMART_C)
    corpo = _corpo(fonte, "PredictiveSwitch")
    assert ">= 20" in corpo                                          # ameaça >= 2x no Pokémon em campo
    assert "GetMonData(mon, MON_DATA_HP) * 2 < GetMonData(mon, MON_DATA_MAX_HP)" in corpo  # candidato PS >= 50%
    assert "> 5" in corpo                                            # candidato leva <= 0,5x de todas as ameaças
    assert "Random() % 5 == 0" in corpo                              # 1 em 5 fica e segue a regra original
    assert "DEFAULT_STAT_STAGE" in corpo and re.search(r"boosts >= 2\b", corpo)  # aumento guardado
    assert "SmartAI_SwitchedLastTurn(battler)" in corpo              # sem pingue-pongue
    assert "SmartAI_CanKoFirst(battler, opponent)" in corpo
    # o sorteio só gasta Random() quando todo o resto vale
    assert corpo.index("SmartAI_CanKoFirst(") < corpo.index("Random() % 5")
    ultimo = _corpo(fonte, "SmartAI_SwitchedLastTurn")
    assert "gBattleResults.battleTurnCounter" in ultimo and "aiVoluntarySwitchTurn" in ultimo
    assert "counter != 0" in ultimo and "counter != 0xFF" in ultimo  # turno 0 e contador parado: nunca "trocou"
    assert "(u8)(" not in ultimo


def test_reacao_original_primeiro():
    corpo = _corpo(_ler(SWITCH_C), "ShouldSwitch")
    pred = corpo.index("SmartAI_ChoosePredictiveSwitch(gActiveBattler, &decision)")
    for nome in ("STATUS2_WRAPPED", "ABILITY_SHADOW_TAG", "ABILITY_MAGNET_PULL", "if (!availableToSwitch)",
                 "ShouldSwitchIfPerishSong()", "ShouldSwitchIfWonderGuard()", "FindMonThatAbsorbsOpponentsMove()",
                 "ShouldSwitchIfNaturalCure()"):
        assert corpo.index(nome) < pred, nome
    # o chefe tenta a preditiva e, se ela não acontece, segue o resto do original (troca por golpe que não pega)
    inicio = corpo.index("if (AI_IsSmartTrainer())")
    resto = corpo.index("if (HasSuperEffectiveMoveAgainstOpponents(FALSE)")
    bloco = corpo[inicio:resto]
    assert "return FALSE;" not in bloco and "return TRUE;" in bloco
    assert "AI_monToSwitchIntoId" in bloco and "decision.partySlot" in bloco and "B_ACTION_SWITCH" in bloco
    assert (pred < resto < corpo.index("AreStatsRaised()")
            < corpo.index("FindMonWithFlagsAndSuperEffective(MOVE_RESULT_DOESNT_AFFECT_FOE, 2)")
            < corpo.index("FindMonWithFlagsAndSuperEffective(MOVE_RESULT_NOT_VERY_EFFECTIVE, 3)"))
    # nenhum return entre a preditiva e o resto: o resto é alcançável quando a preditiva não troca
    assert bloco.rstrip().endswith("}") and bloco.count("return") == 1
    # a troca voluntária é marcada uma vez só (no ramo ShouldSwitch de AI_TrySwitchOrUseItem)
    assert "SmartAI_NoteVoluntarySwitch" not in corpo
    assert _ler(SWITCH_C).count("SmartAI_NoteVoluntarySwitch(") == 1


def test_bug_bestdmg():
    corpo = _corpo(_ler(SWITCH_C), "GetMostSuitableMonToSwitchInto")
    chefe = corpo.index("return SmartAI_ChooseReplacement(gActiveBattler);")
    # depois do atalho de "já escolhido" e antes de qualquer comparação de dano em u8
    assert corpo.index("return *(gBattleStruct->monToSwitchIntoId + gActiveBattler);") < chefe
    assert chefe < corpo.index("bestDmg = 0;")
    fonte = _ler(SMART_C)
    for nome in ("SmartAI_ChooseReplacement", "SmartAI_ScoreBench"):
        c = _corpo(fonte, nome)
        assert "bestDmg" not in c and "gBattleMoveDamage" not in c, nome
    assert re.search(r"\bs32 bestScore\b", _corpo(fonte, "SmartAI_ChooseReplacement"))


def test_substituto_evita_fraco():
    corpo = _corpo(_ler(SMART_C), "SmartAI_ChooseReplacement")
    # quem leva >= 2x de alguma ameaça conhecida só entra se não houver outro
    assert ">= 20" in corpo and "bestWeak" in corpo
    assert "return best != PARTY_SIZE ? best : bestWeak;" in corpo
    # as ameaças são calculadas uma vez por Pokémon do jogador, fora do laço dos candidatos
    assert corpo.count("SmartAI_ThreatTypes(") == 1
    assert corpo.index("SmartAI_ThreatTypes(") < corpo.index("for (i = 0; i < PARTY_SIZE; i++)")


def test_ameacas():
    corpo = _corpo(_ler(SMART_C), "SmartAI_ThreatTypes")
    assert "aiRevealedMoves[gBattlerPartyIndexes[opponentBattler]]" in corpo
    assert ".power > 0" in corpo
    assert "type1" in corpo and "type2" in corpo


def test_derruba_primeiro_salva_globais():
    fonte = _ler(SMART_C)
    tabela = fonte[fonte.index("sNoKoThisTurnEffects[] ="):]
    tabela = tabela[:tabela.index("};")]
    for efeito in ("EFFECT_FUTURE_SIGHT", "EFFECT_SEMI_INVULNERABLE", "EFFECT_FALSE_SWIPE", "EFFECT_FOCUS_PUNCH",
                   "EFFECT_SOLAR_BEAM", "EFFECT_DREAM_EATER"):
        assert efeito in tabela, efeito
    corpo = _corpo(fonte, "SmartAI_CanKoFirst")
    for nome in ("AI_CalcDmg(battler, target);", "TypeCalc(move, battler, target)",
                 "GetWhoStrikesFirst(battler, target, TRUE)", "gCurrentMove = move;"):
        assert nome in corpo, nome
    for glob in ("gBattleMoveDamage", "gMoveResultFlags", "gDynamicBasePower", "gCritMultiplier",
                 "gBattleScripting.dmgMultiplier", "gBattleStruct->dynamicMoveType", "gCurrentMove",
                 "gBattleMovePower", "gLastUsedAbility"):
        assert re.search(rf"= {re.escape(glob)};", corpo), f"salva {glob}"
        assert re.search(rf"{re.escape(glob)} = saved\w*;", corpo), f"restaura {glob}"


def test_grava_golpe_do_time():
    # Transform/Mimic: compara com os golpes de verdade do Pokémon no time, não com os de gBattleMons
    corpo = _corpo(_ler(SMART_C), "SmartAI_RecordPlayerMove")
    assert "GetMonData(&gPlayerParty[gBattlerPartyIndexes[battler]], MON_DATA_MOVE1 + i)" in corpo
    assert "gBattleMons[battler].moves" not in corpo


def test_hooks_d1_d2():
    h = _ler(TEST_HOOKS_H)
    assert re.search(r"TEST_CMD_AI_SMART_DECIDE\s*=\s*0xD1\b", h)
    assert re.search(r"TEST_CMD_SET_ENEMY_MON\s*=\s*0xD2\b", h)
    assert hooks.CMD_AI_SMART_DECIDE == 0xD1 and hooks.CMD_SET_ENEMY_MON == 0xD2
    c = _ler(SRC / "test_hooks.c")
    assert "case TEST_CMD_AI_SMART_DECIDE:" in c and "case TEST_CMD_SET_ENEMY_MON:" in c
    decide = _corpo(c, "AiSmartDecide")
    assert "SmartAI_Decide(" in decide and "B_POSITION_OPPONENT_LEFT" in decide
    for proibido in ("BtlController_Emit", "monToSwitchIntoId", "SmartAI_NoteVoluntarySwitch"):
        assert proibido not in decide, proibido
    assert "<< 8" in decide and "<< 16" in decide


# --- Task 3: itens na hora certa ----------------------------------------------------------------------------------
# O chefe escolhe o item em SmartAI_ChooseItem (núcleo puro ChooseItem, o mesmo do atalho 0xD1) e ShouldUseItem emite
# como o original. "Cura desfeita": na escolha do turno seguinte à cura (contador = turno da cura + 1), o mesmo
# Pokémon (mesmo slot do time) está com PS <= o PS de antes da cura; a partir daí ele não cura PS de novo nesta
# batalha (marca por slot em aiHealHp).


def test_interface_task3():
    h = _ler(SMART_H)
    assert "bool8 SmartAI_ChooseItem(u8 battler, struct SmartAiDecision *out, u8 *listIndex);" in h
    assert "void SmartAI_NoteHealUndone(u8 battler);" in h and "const u8 *SmartAI_ItemEffects(u16 item);" in h
    # GetAI_ItemType exportada: o chefe classifica o item como o original
    assert "u8 GetAI_ItemType(u8 itemId, const u8 *itemEffect);" in _ler(REPO_ROOT / "include" / "battle_ai_switch_items.h")
    assert "static u8 GetAI_ItemType" not in _ler(SWITCH_C)


def test_limiares_item():
    fonte = _ler(SMART_C)
    corpo = _corpo(fonte, "ChooseItem")
    # a regra original de guardar itens para os últimos Pokémon
    assert "if (i && validMons > (itemsNo - i) + 1)" in corpo
    assert "gBattleResources->battleHistory->itemsNo" in corpo and "battleHistory->trainerItems[i]" in corpo
    assert "hp * 3 <= maxHP" in corpo                                 # cura de PS com PS <= 33%
    assert "hp * 5 <= maxHP * 3" in corpo                             # Restaurar Tudo com estado e PS <= 60%
    restore = corpo[corpo.index("case AI_ITEM_FULL_RESTORE:"):corpo.index("case AI_ITEM_HEAL_HP:")]
    for estado in ("STATUS1_SLEEP", "STATUS1_FREEZE", "STATUS1_PARALYSIS", "STATUS1_TOXIC_POISON"):
        assert estado in restore, estado
    assert "STATUS1_POISON " not in restore and "STATUS1_BURN" not in restore
    # poção que cura < 25% do PS máximo não serve (Poção Máx./Restaurar Tudo = ITEM6_HEAL_HP_FULL servem sempre)
    cura = _corpo(fonte, "HealsEnough")
    assert "ITEM6_HEAL_HP_FULL" in cura and "amount * 4 >= maxHP" in cura and "ITEM4_REVIVE" in cura
    # derruba antes -> ataca: o teste de nocaute vem antes de qualquer cura ser escolhida
    assert "KoFirst(battler" in corpo
    ko = _corpo(fonte, "KoFirst")
    assert "SmartAI_CanKoFirst(battler, " in ko
    # itens X e Guard Spec: só no 1º turno, como o original
    assert corpo.count("gDisableStructs[battler].isFirstTurn") == 2 and "mistTimer == 0" in corpo


def test_cura_desfeita_estatico():
    fonte = _ler(SMART_C)
    desfeita = _corpo(fonte, "HealUndoneLastTurn")
    assert "gBattleResults.battleTurnCounter" in desfeita
    assert "counter != 0" in desfeita and "counter != 0xFF" in desfeita
    assert "(turn & 0xFF) == counter - 1" in desfeita                       # cura no turno anterior
    assert "turn >> 8" in desfeita and "gBattlerPartyIndexes[battler]" in desfeita  # o mesmo Pokémon
    assert "gBattleMons[battler].hp <= (gBattleStruct->aiHealHp[pos] & HEAL_HP_MASK)" in desfeita
    bloqueio = _corpo(fonte, "HealBlocked")
    assert "HEAL_UNDONE_SHIFT" in bloqueio and "HealUndoneLastTurn(battler)" in bloqueio
    # a marca vale nas duas posições (em dupla o Pokémon pode voltar pela outra)
    assert "gBattleStruct->aiHealHp[0] | gBattleStruct->aiHealHp[1]" in bloqueio
    corpo = _corpo(fonte, "ChooseItem")
    assert "healBlocked = HealBlocked(battler);" in corpo
    assert corpo.count("!healBlocked") == 2                                  # Restaurar Tudo (PS) e poções
    # o núcleo é puro (atalho de teste): quem grava é SmartAI_ChooseItem
    assert not re.search(r"gBattleStruct->\w+(\[[^\]]*\])?\s*[|&]?=[^=]", corpo)
    grava = _corpo(fonte, "SmartAI_ChooseItem")
    assert "ChooseItem(battler, out, listIndex)" in grava
    assert "HealUndoneLastTurn" not in grava and "HEAL_UNDONE_SHIFT" not in grava  # a marca é gravada antes
    assert "gBattleStruct->aiHealTurn[pos] = gBattleResults.battleTurnCounter | slot << 8;" in grava
    assert "gBattleMons[battler].hp" in grava and "aiHealHp[pos]" in grava
    nota = _corpo(fonte, "SmartAI_NoteHealUndone")
    assert "gBattleStruct->aiSmart" in nota and "B_SIDE_OPPONENT" in nota
    assert nota.index("HealUndoneLastTurn(battler)") < nota.index("1 << (HEAL_UNDONE_SHIFT + slot)")
    assert re.search(r"#define HEAL_HP_MASK\s+0x3FF\b", fonte) and re.search(r"#define HEAL_UNDONE_SHIFT\s+10\b", fonte)


def test_cura_total_estados():
    fonte = _ler(SMART_C)
    corpo = _corpo(fonte, "CureWorthIt")
    for estado in ("STATUS1_SLEEP", "STATUS1_FREEZE", "STATUS1_TOXIC_POISON"):
        assert estado in corpo, estado
    assert re.search(r"STATUS1_PARALYSIS\)[^;]*FasterThanFoes\(battler\)", corpo)      # paralisia: só se é rápido
    assert "gSpeciesInfo[species].baseAttack > gSpeciesInfo[species].baseSpAttack" in corpo  # queimadura: físico
    assert re.search(r"STATUS1_POISON\)[^;]*hp \* 2 <= maxHP", corpo)                   # veneno comum: PS <= 50%
    assert "CONFUSION" not in corpo                                                      # nunca só confusão
    rapido = _corpo(fonte, "FasterThanFoes")
    assert "GetWhoStrikesFirst(battler, " in rapido and "STATUS1_PARALYSIS" in rapido
    assert "status1 = saved" in rapido or "status1 = status" in rapido                    # devolve o estado


def test_item_comum_nao_muda():
    novo, velho = _ler(SWITCH_C), _base("src/battle_ai_switch_items.c")
    corpo = _corpo(novo, "ShouldUseItem")
    assert "if (AI_IsSmartTrainer())" in corpo
    sem = _sem_blocos_do_chefe(corpo)
    assert [l for l in sem.splitlines() if "Smart" in l] == []
    assert sem == "\n".join(l.rstrip() for l in _corpo(velho, "ShouldUseItem").splitlines())
    assert corpo.index("if (AI_IsSmartTrainer())") < corpo.index("for (i = 0; i < PARTY_SIZE; ++i)")
    # GetAI_ItemType só perde o `static` (a linha da definição tem comentário: _corpo não a acha)
    def tipo(fonte):
        inicio = fonte.index("u8 GetAI_ItemType(u8 itemId, const u8 *itemEffect) //")
        return fonte[inicio:fonte.index("\n}\n", inicio)]
    assert tipo(novo) == tipo(velho)


def test_item_do_chefe_emitido_como_original():
    corpo = _corpo(_ler(SWITCH_C), "ShouldUseItemSmart")
    for nome in ("SmartAI_ChooseItem(gActiveBattler, &decision, &listIndex)", "B_ACTION_USE_ITEM",
                 "*(gBattleStruct->chosenItem + (gActiveBattler / 2) * 2) = decision.item;",
                 "gBattleResources->battleHistory->trainerItems[listIndex] = 0;",
                 "itemEffects = SmartAI_ItemEffects(decision.item);",
                 "*(gBattleStruct->AI_itemType + gActiveBattler / 2) = GetAI_ItemType(decision.item, itemEffects);",
                 "*(gBattleStruct->AI_itemFlags + gActiveBattler / 2)",
                 "AI_ITEM_CURE_CONDITION", "AI_ITEM_X_STAT"):
        assert nome in corpo, nome
    # as mesmas marcas do original (mensagem do script de uso)
    for bit in ("0x20", "0x10", "0x8", "0x4", "0x2", "0x1", "0x80"):
        assert bit in corpo, bit


def test_decide_com_item_e_hook_d3():
    fonte = _ler(SMART_C)
    decide = _corpo(fonte, "SmartAI_Decide")
    assert decide.index("PredictiveSwitch(") < decide.index("ChooseItem(battler, out, &listIndex)") < decide.index("SMART_AI_ATTACK")
    assert "SmartAI_ChooseItem" not in decide                  # o atalho não grava a cura
    h = _ler(TEST_HOOKS_H)
    assert re.search(r"TEST_CMD_SET_TRAINER_ITEMS\s*=\s*0xD3\b", h)
    assert hooks.CMD_SET_TRAINER_ITEMS == 0xD3
    c = _ler(SRC / "test_hooks.c")
    assert "case TEST_CMD_SET_TRAINER_ITEMS:" in c
    itens = _corpo(c, "SetTrainerItems")
    assert "trainerItems" in itens and "itemsNo" in itens and "LAST_BERRY_INDEX" in itens
    d = _corpo(c, "AiSmartDecide")
    for proibido in ("trainerItems", "aiHealTurn", "aiHealHp", "SmartAI_ChooseItem"):
        assert proibido not in d, proibido


def test_marca_cura_desfeita_antes_da_troca():
    # A marca de cura desfeita é gravada no começo da escolha do chefe, antes de ShouldSwitch: se ele trocar no turno
    # seguinte à cura, o Pokémon sai já marcado e não cura de novo quando voltar.
    corpo = _corpo(_ler(SWITCH_C), "AI_TrySwitchOrUseItem")
    nota = corpo.index("SmartAI_NoteHealUndone(gActiveBattler);")
    assert nota < corpo.index("if (ShouldSwitch())") and nota < corpo.index("ShouldUseItem()")
    linhas = corpo.splitlines()
    i = next(n for n, l in enumerate(linhas) if "SmartAI_NoteHealUndone(" in l)
    assert linhas[i - 1].strip() == "if (AI_IsSmartTrainer())"           # só chefe
    assert _ler(SWITCH_C).count("SmartAI_NoteHealUndone(") == 1
    # o atalho de teste não grava a marca (ele vê o bloqueio por HealUndoneLastTurn, sem escrever)
    assert "SmartAI_NoteHealUndone" not in _ler(SRC / "test_hooks.c")
    assert "SmartAI_NoteHealUndone" not in _corpo(_ler(SMART_C), "SmartAI_Decide")
    # item não reconhecido: pula (comentado), em vez do return FALSE do original
    escolha = _corpo(_ler(SMART_C), "ChooseItem")
    padrao = escolha[escolha.index("default:"):]
    assert "return FALSE" in padrao.splitlines()[1] and "use = FALSE;" in padrao
    assert "*listIndex = i;" in escolha
