"""Revanches por degrau (POK-42), Task 2: a tabela gerada e o degrau nas revanches do Vs. Seeker.

`tools/revanches/gerar.py` grava `src/data/rematch_tiers.h` (commitado); `src/rematch_tier.c` troca o time dentro
de `CreateNPCTrainerParty` quando a batalha é uma revanche do Vs. Seeker e o degrau salvo é 1–5. Aqui se confere,
lendo o C como texto, que a tabela está em dia com o gerador e que os ganchos estão no lugar certo (o primeiro
combate não muda, a dupla continua dupla, var com lixo vale 0, o prêmio usa o nível do time do degrau). O
comportamento no jogo fica no cenário `revanches` (Task 6).
"""

import importlib.util
import re
import subprocess
import sys
from collections import Counter

import pytest

from esteira.scenarios import REPO_ROOT

GERAR = REPO_ROOT / "tools" / "revanches" / "gerar.py"
HEADER = REPO_ROOT / "src" / "data" / "rematch_tiers.h"
SRC = REPO_ROOT / "src"
BASE_SHA = "4be5f6b56"  # hack-switch antes do POK-42 (o POK-44 não mexeu nos arquivos comparados)


@pytest.fixture(scope="module")
def g():
    spec = importlib.util.spec_from_file_location("revanches_gerar_t2", GERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def test_tabela_gerada_em_dia():
    r = subprocess.run([sys.executable, "-I", str(GERAR), "--conferir"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_tabela_completa(g):
    texto = _ler(HEADER)
    assert texto.startswith("// GERADO por tools/revanches/gerar.py; não editar")
    assert re.search(r"^#define REMATCH_TIER_ROWS 221$", texto, re.M)
    assert ("static const struct RematchTierMon "
            "sRematchTierParties[REMATCH_TIER_ROWS][REMATCH_TIER_COUNT][PARTY_SIZE] =") in texto
    linhas = g.ler_revanches()
    assert len(linhas) == 221
    entradas = re.findall(r"\{(SPECIES_\w+), (ITEM_\w+), (\d+), (\d+)\}", texto)
    assert len(entradas) == 221 * 5 * 6
    esperado = [(e, it, str(n), str(v)) for i in range(len(linhas)) for d in range(1, 6)
                for e, n, it, v in g.time_vs(i, d)]
    assert entradas == esperado
    # um comentário com o 1º treinador antes de cada linha, na ordem de sRematches (a Liga vem depois, Task 3)
    vs = texto[:texto.index("sLeagueTierParties")] if "sLeagueTierParties" in texto else texto
    assert re.findall(r"^    // (TRAINER_\w+)$", vs, re.M) == [linha[0] for linha in linhas]


def test_linha_unica_por_treinador(g):
    """Cada id está numa linha só de sRematches (repetido na mesma linha, como o Calvin, pode)."""
    contagem = Counter(t for linha in g.ler_revanches() for t in set(linha))
    assert [t for t, n in contagem.items() if n > 1] == []


def test_trainers_intocados():
    # só o conteúdo: no /mnt/c (drvfs) o WSL vê todo arquivo como rwxrwxrwx e, com core.fileMode=true,
    # o git acusaria "mode change 100644 => 100755" conforme quem mexeu por último no índice (POK-30)
    r = subprocess.run(["git", "-c", "core.fileMode=false", "diff", "--quiet", BASE_SHA, "--", "src/data/trainer_parties.h",
                        "src/data/trainers.h"], cwd=REPO_ROOT)
    assert r.returncode == 0


def test_primeiro_combate_nao_muda():
    """A revanche é marcada pelo modo da batalha (TRAINER_BATTLE_REMATCH*), não pelo id do treinador."""
    corpo = _corpo(_ler(SRC / "battle_setup.c"), "BattleSetup_ConfigureTrainerBattle")
    falso = corpo.find("RematchTier_SetVsSeekerBattle(FALSE);")
    assert 0 <= falso < corpo.index("switch (sTrainerBattleMode)")
    assert corpo.count("RematchTier_SetVsSeekerBattle(FALSE);") == 1
    rotulos = list(re.finditer(r"^    (?:case (\w+)|default):", corpo, re.M))
    com_true = set()
    for k, m in enumerate(rotulos):
        fim = rotulos[k + 1].start() if k + 1 < len(rotulos) else len(corpo)
        if "RematchTier_SetVsSeekerBattle(TRUE);" in corpo[m.end():fim]:
            com_true.add(m.group(1))
    assert com_true == {"TRAINER_BATTLE_REMATCH_DOUBLE", "TRAINER_BATTLE_REMATCH"}
    assert corpo.count("RematchTier_SetVsSeekerBattle(TRUE);") == 2


def test_dupla_continua_dupla():
    corpo = _corpo(_ler(SRC / "battle_main.c"), "CreateNPCTrainerParty")
    se = corpo.index("if (gBattleTypeFlags & BATTLE_TYPE_TRAINER")
    chamada = corpo.index("RematchTier_CreateParty(party, trainerNum)")
    laco = corpo.index("for (i = 0; i < gTrainers[trainerNum].partySize; i++)")
    assert se < chamada < laco
    ramo = corpo[chamada:corpo.index("return", chamada)]
    assert "gBattleTypeFlags |= gTrainers[trainerNum].doubleBattle;" in ramo


def test_degrau_invalido_vira_zero():
    corpo = _corpo(_ler(SRC / "rematch_tier.c"), "GetRematchTier")
    assert re.search(r"u16 tier = VarGet\(VAR_REMATCH_TIER\);", corpo)
    assert re.search(r"if \(!FlagGet\(FLAG_SYS_GAME_CLEAR\) \|\| tier > REMATCH_TIER_MAX\)\s*return 0;\s*return tier;",
                     corpo)


def test_dinheiro_do_degrau():
    corpo = _corpo(_ler(SRC / "battle_script_commands.c"), "Cmd_getmoneyreward")
    assert re.search(r"if \(GetCurrentBattleRematchTier\(\) != 0\)\s*"
                     r"lastMonLevel = GetMonData\(&gEnemyParty\[PARTY_SIZE - 1\], MON_DATA_LEVEL\);", corpo)
    # depois do switch dos times originais, para valer sobre ele, e antes da conta do prêmio
    assert corpo.index("GetCurrentBattleRematchTier()") > corpo.index("switch (gTrainers[gTrainerBattleOpponent_A]")
    assert corpo.index("GetCurrentBattleRematchTier()") < corpo.index("moneyReward = 4 *")


def test_linhas_iguais_a_srematches():
    """A tabela gerada e sRematches têm o mesmo número de linhas, garantido na compilação."""
    vs = _ler(SRC / "vs_seeker.c")
    assert re.search(r"^STATIC_ASSERT\(NELEMS\(sRematches\) == VS_SEEKER_REMATCH_ROWS, \w+\);", vs, re.M)
    assert re.search(r"^#define VS_SEEKER_REMATCH_ROWS 221\b", _ler(REPO_ROOT / "include" / "vs_seeker.h"), re.M)
    assert re.search(r"^STATIC_ASSERT\(REMATCH_TIER_ROWS == VS_SEEKER_REMATCH_ROWS, \w+\);",
                     _ler(SRC / "rematch_tier.c"), re.M)


def test_atalho_nao_deixa_estado():
    """O atalho de teste BuildTrainerParty desliga o bit do Vs. Seeker depois de montar o resultado."""
    corpo = _corpo(_ler(SRC / "test_hooks.c"), "BuildTrainerParty")
    montar = corpo.index("result |= GetCurrentBattleRematchTier()")
    limpar = corpo.index("RematchTier_SetVsSeekerBattle(FALSE);")
    assert montar < limpar < corpo.index("return result;")


def test_interface():
    h = _ler(REPO_ROOT / "include" / "rematch_tier.h")
    for linha in ("#define REMATCH_TIER_MAX 5", "#define REMATCH_TIER_COUNT 5",
                  "u8 GetRematchTier(void);", "void RematchTier_SetVsSeekerBattle(bool8 isRematch);",
                  "u8 RematchTier_CreateParty(struct Pokemon *party, u16 trainerNum);",
                  "u8 GetCurrentBattleRematchTier(void);"):
        assert linha in h, linha
    assert re.search(r"struct RematchTierMon\s*\{\s*u16 species;\s*u16 heldItem;\s*u8 lvl;\s*u8 iv;[^\n]*\s*\};", h)
    assert "s32 GetVsSeekerRematchRow(u16 trainerId);" in _ler(REPO_ROOT / "include" / "vs_seeker.h")
    assert re.search(r"^#define VAR_REMATCH_TIER\s+0x40BD\b", _ler(REPO_ROOT / "include" / "constants" / "vars.h"),
                     re.M)


# --- Task 5: a IA dos chefes no degrau 3+ e os ganchos das conquistas (POK-44) ---

CHEFES = ("AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_TRY_TO_FAINT | AI_SCRIPT_CHECK_VIABILITY | AI_SCRIPT_SETUP_FIRST_TURN"
          " | AI_SCRIPT_HP_AWARE")


def test_ia_do_degrau():
    """Revanche do Vs. Seeker com o degrau aplicado >= 3: a IA dos chefes do POK-32 soma-se à do treinador."""
    ai = _ler(SRC / "battle_ai_script_commands.c")
    assert '#include "rematch_tier.h"' in ai
    corpo = _corpo(ai, "BattleAI_SetupAIData")
    assert corpo.rstrip().endswith("AI_THINKING_STRUCT->aiFlags = gTrainers[gTrainerBattleOpponent_A].aiFlags"
                                   " | RematchTier_GetAiFlags();")
    assert ai.count("RematchTier_GetAiFlags()") == 1
    fonte = _ler(SRC / "rematch_tier.c")
    ia = _corpo(fonte, "RematchTier_GetAiFlags")
    assert re.search(r"if \(\(sRematchTierState & STATE_VS_SEEKER\) && GetCurrentBattleRematchTier\(\) >= 3\)\s*"
                     rf"return {re.escape(CHEFES)};\s*return 0;", ia), ia
    # o mesmo conjunto dos chefes em trainers.h (líderes, Elite 4, Campeão)
    assert CHEFES in _ler(SRC / "data" / "trainers.h")


def test_ganchos_conquistas():
    setup = _corpo(_ler(SRC / "battle_setup.c"), "CB2_EndRematchBattle")
    ganho = "RematchTier_OnRematchWon(GetCurrentBattleRematchTier());"
    assert setup.count(ganho) == 1
    # só no ramo da vitória (o último else), depois de marcar o treinador
    assert setup.index("IsPlayerDefeated(gBattleOutcome)") < setup.index("SetBattledTrainerFlag();") \
        < setup.index(ganho)
    assert "else\n    {" in setup[setup.index("CB2_WhiteOut"):setup.index(ganho)]

    hof = _corpo(_ler(SRC / "post_battle_event_funcs.c"), "EnterHallOfFame")
    liga = "RematchTier_OnLeagueCleared(GetCurrentBattleRematchTier());"
    assert hof.count(liga) == 1
    # antes da tela do Hall da Fama, que grava o save (a conquista feita sobrevive aos créditos e ao reset)
    assert hof.index(liga) < hof.index("SetMainCallback2(CB2_DoHallOfFameScreen);")
    assert '#include "rematch_tier.h"' in _ler(SRC / "post_battle_event_funcs.c")

    fonte = _ler(SRC / "rematch_tier.c")
    assert '#include "conquistas.h"' in fonte
    assert re.search(r"if \(tier == REMATCH_TIER_MAX\)\s*Conquistas_Evento\(CONQ_EVT_REVANCHE_MAX\);",
                     _corpo(fonte, "RematchTier_OnRematchWon"))
    assert re.search(r"if \(tier == REMATCH_TIER_MAX\)\s*Conquistas_Evento\(CONQ_EVT_E4_DEGRAU100\);",
                     _corpo(fonte, "RematchTier_OnLeagueCleared"))
    assert fonte.count("Conquistas_Evento(") == 2

    h = _ler(REPO_ROOT / "include" / "rematch_tier.h")
    for linha in ("u32 RematchTier_GetAiFlags(void);", "void RematchTier_OnRematchWon(u8 tier);",
                  "void RematchTier_OnLeagueCleared(u8 tier);"):
        assert linha in h, linha


def test_ganchos_respeitam_o_marcador():
    """Os ganchos de rematch_tier.c chamam Conquistas_Evento direto: a regra do POK-44 (save sem marcador = gatilho
    não faz nada; a varredura do save antigo decide) fica na própria entrada pública, não em quem chama."""
    fonte = _ler(SRC / "conquistas.c")
    for nome, perder in (("Conquistas_Evento", "FALSE"), ("Conquistas_PerderEvento", "TRUE")):
        corpo = _corpo(fonte, nome)
        assert re.search(rf"if \(ComMarcador\(\)\)\s*AplicarEvento\(evento, {perder}\);", corpo), (nome, corpo)
    # ComMarcador definida antes das entradas (sem protótipo solto)
    assert fonte.index("static bool8 ComMarcador(void)\n{") < fonte.index("void Conquistas_Evento(u8 evento)\n{")


def test_conquistas_do_degrau_ativas():
    """As duas conquistas do POK-44 que esperavam o POK-42 ficam ativas (o JSON é a fonte única)."""
    import json

    dados = json.loads(_ler(SRC / "data" / "conquistas" / "conquistas.json"))
    c = {x["id"]: x for x in dados["conquistas"]}
    for cid, evt in (("revanche_max", "CONQ_EVT_REVANCHE_MAX"), ("e4_degrau100", "CONQ_EVT_E4_DEGRAU100")):
        assert c[cid]["ativa"] is True and c[cid]["param"] == evt, cid
        assert "inativa" not in c[cid]["condicao"], cid
    assert sum(1 for x in dados["conquistas"] if x.get("ativa", True)) == 41
