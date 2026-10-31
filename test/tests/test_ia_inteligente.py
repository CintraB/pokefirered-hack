"""IA com troca preditiva e itens (POK-46), Task 1: estado por batalha, "é chefe" e golpes mostrados.

`src/battle_ai_smart.c` guarda em `gBattleStruct` (memória da batalha, `AllocZeroed` a cada batalha) se o oponente
é um chefe (`aiSmart`: as flags efetivas `gTrainers[].aiFlags | RematchTier_GetAiFlags()` contêm
`AI_SCRIPT_HP_AWARE`, com as exclusões de `BattleAI_SetupAIData`), os golpes que cada Pokémon do jogador já mostrou
nesta batalha e o turno da última troca voluntária da IA. Aqui se confere, lendo o C como texto, que os campos
existem e que os ganchos estão no lugar certo. O comportamento no jogo é conferido pelo atalho
`TEST_CMD_AI_SMART_STATE` (0xD0).
"""

import re

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
