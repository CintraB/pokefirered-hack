"""POK-51 (Task 3): capangas da Família Sombra como treinadores. Leitura estática do C, dos dados e dos scripts.

Os 12 treinadores-slot (9 capangas visíveis, os gêmeos em dupla e as 2 lutas do pedágio) são da classe
TRAINER_CLASS_FAMILIA_SOMBRA: IA dos chefes, sem prêmio, sem humano na batalha (o Pokémon aparece direto) e sem
captura (a bola é desviada e não é gasta). O time de cada um sai de src/data/familia_sombra_times.h pela ocupação.
O comportamento no jogo fica no cenário `familia` da esteira (test/esteira/scenarios/full_familia.py).
"""

import json
import re

from esteira import check_text as ct
from esteira.scenarios import REPO_ROOT


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


OPPONENTS_H = _read("include/constants/opponents.h")
TRAINERS_H = _read("src/data/trainers.h")
PARTIES_H = _read("src/data/trainer_parties.h")
CLASSES_H = _read("include/constants/trainers.h")
CLASS_NAMES_H = _read("src/data/text/trainer_class_names.h")
TIMES_H = _read("src/data/familia_sombra_times.h")
FAMILIA_C = _read("src/familia_sombra.c")
BATTLE_MAIN_C = _read("src/battle_main.c")
BATTLE_MESSAGE_C = _read("src/battle_message.c")
SCRIPTS_1 = _read("data/battle_scripts_1.s")
SCRIPTS_2 = _read("data/battle_scripts_2.s")

CAPANGAS = [f"TRAINER_FAMILIA_CAPANGA_{n}" for n in range(1, 10)]
DOZE = CAPANGAS + ["TRAINER_FAMILIA_GEMEOS", "TRAINER_FAMILIA_PEDAGIO_1", "TRAINER_FAMILIA_PEDAGIO_2"]
AI_CHEFE = {"AI_SCRIPT_CHECK_BAD_MOVE", "AI_SCRIPT_TRY_TO_FAINT", "AI_SCRIPT_CHECK_VIABILITY",
            "AI_SCRIPT_SETUP_FIRST_TURN", "AI_SCRIPT_HP_AWARE"}
# R3: espécies com sprite de chapéu da Task 2 que podem ser capanga (Persian = cobrador, Machamp/Rhydon = gêmeos)
COM_CHAPEU = {"HAUNTER", "MISDREAVUS", "SABLEYE", "BANETTE", "HOUNDOUR", "HOUNDOOM", "MURKROW", "SNEASEL", "CROBAT",
              "MUK", "WEEZING", "ARBOK", "MIGHTYENA", "ABSOL", "CACTURNE", "SHIFTRY", "CRAWDAUNT", "GOLEM"}
NUNCA_CAPANGA = {"GENGAR", "TYRANITAR", "PERSIAN", "MACHAMP", "RHYDON"}
CAIXA_DE_BATALHA_PX = 222     # B_WIN_MSG: 28 tiles com x = 2 (a medição da checagem de texto da esteira)


def _defines(text: str) -> dict[str, str]:
    return dict(re.findall(r"^#define\s+(\w+)\s+(\w+)", text, re.M))


def _trainer(name: str) -> str:
    m = re.search(rf"\[{name}\] = \{{(.*?)\n    \}},", TRAINERS_H, re.S)
    assert m, name
    return m.group(1)


def _block(text: str, start: str) -> str:
    """O bloco entre a 1ª chave depois de `start` e a chave que o fecha (pula os protótipos, que acabam em ';')."""
    pos = text.index(start)
    while text.find(";", pos) < text.find("{", pos):
        pos = text.index(start, pos + 1)
    i = text.index("{", pos)
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1:j]
    raise AssertionError(start)


def _membros(table: str) -> list[list[tuple[str, int, str, list[str]]]]:
    """Uma lista por ocupação de (espécie, nível, item, golpes) da tabela `table` de familia_sombra_times.h."""
    body = _block(TIMES_H, f"{table}[")
    ocupacoes = []
    depth, start = 0, None
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
            if depth == 1:
                start = i
        elif ch == "}":
            depth -= 1
            if depth == 0:
                bloco = body[start:i]
                ocupacoes.append([(sp, int(lv), item, [m.strip() for m in moves.split(",")])
                                  for sp, lv, item, moves in re.findall(
                                      r"MEMBRO\((\w+),\s*(\d+),\s*(\w+),\s*([\w ,]+)\)", bloco)])
    return ocupacoes


def _ocupacao_blocks(table: str) -> list[str]:
    body = _block(TIMES_H, f"{table}[")
    return re.split(r"\n    // Ocupação ", body)[1:]


def test_doze_treinadores():
    d = _defines(OPPONENTS_H)
    ids = [int(d[n]) for n in DOZE]
    assert ids == list(range(743, 755)), ids          # logo depois do último da pret (742), sem buraco
    assert int(d["NUM_TRAINERS"]) == 755 <= 755 and int(d["MAX_TRAINERS_COUNT"]) == 768
    assert d["TRAINER_FAMILIA_PRIMEIRO"] == "TRAINER_FAMILIA_CAPANGA_1"
    assert d["TRAINER_FAMILIA_ULTIMO"] == "TRAINER_FAMILIA_PEDAGIO_2"
    for name in DOZE:
        assert ".trainerClass = TRAINER_CLASS_FAMILIA_SOMBRA," in _trainer(name), name
    assert TRAINERS_H.count("TRAINER_CLASS_FAMILIA_SOMBRA") == 12


def test_classe_nome_curto():
    values = {n: int(v) for n, v in re.findall(r"#define (TRAINER_CLASS_\w+)\s+(\d+)", CLASSES_H)}
    assert values["TRAINER_CLASS_FAMILIA_SOMBRA"] == 109
    assert list(values.values()).count(109) == 1 and max(values.values()) <= 0xFF
    names = dict(re.findall(r'\[(TRAINER_CLASS_\w+)\]\s*=\s*_\("([^"]*)"\)', CLASS_NAMES_H))
    assert names["TRAINER_CLASS_FAMILIA_SOMBRA"] == "Capanga"
    assert len(names["TRAINER_CLASS_FAMILIA_SOMBRA"]) <= 12
    # o nome do "treinador" completa as frases de vitória e derrota: "Você derrotou\nCapanga da Família!"
    for name in DOZE:
        assert '.trainerName = _("da Família"),' in _trainer(name)
    assert len("da Família") <= 11      # trainerName[12] com o EOS


def test_ia_de_chefe():
    for name in DOZE:
        flags = re.search(r"\.aiFlags = ([^,]+),", _trainer(name)).group(1)
        assert {f.strip() for f in flags.split("|")} == AI_CHEFE, name


def test_gemeos_dupla():
    assert ".doubleBattle = TRUE," in _trainer("TRAINER_FAMILIA_GEMEOS")
    for name in CAPANGAS + ["TRAINER_FAMILIA_PEDAGIO_1", "TRAINER_FAMILIA_PEDAGIO_2"]:
        assert ".doubleBattle = FALSE," in _trainer(name), name
    # o tamanho do time em gTrainers bate com o que FamiliaSombra_CriarTime monta (2 na dupla, 1 nos outros)
    assert "NO_ITEM_DEFAULT_MOVES(sParty_FamiliaGemeos)" in _trainer("TRAINER_FAMILIA_GEMEOS")
    assert _block(PARTIES_H, "sParty_FamiliaGemeos[]").count(".species") == 2
    for party in ("sParty_FamiliaCapanga", "sParty_FamiliaPedagio"):
        assert _block(PARTIES_H, f"{party}[]").count(".species") == 1
    criar = _block(FAMILIA_C, "u8 FamiliaSombra_CriarTime(")
    assert re.search(r"case TRAINER_FAMILIA_GEMEOS:.*?return 2;", criar, re.S)
    # os gêmeos: 2 Machamp com o Dom, 2 Rhydon com o Cobrador; nas 4 ocupações, os dois da mesma espécie
    gemeos = _membros("sFamiliaGemeos")
    assert [g[0][0] for g in gemeos[:2]] == ["MACHAMP", "RHYDON"]
    assert all(len(g) == 2 and g[0][0] == g[1][0] for g in gemeos)


def test_niveis_do_spec():
    capangas, gemeos = _membros("sFamiliaCapangas"), _membros("sFamiliaGemeos")
    assert len(capangas) == len(gemeos) == 4 and all(len(o) == 9 for o in capangas)
    niveis = [lv for _sp, lv, _i, _m in capangas[0]]
    assert min(niveis) == 50 and max(niveis) == 54 and niveis == sorted(niveis)    # andares 1-3: 50-54
    assert [lv for _sp, lv, _i, _m in gemeos[0]] == [60, 60]
    for k in range(1, 4):           # +6 em tudo a cada ocupação
        assert [m[1] for m in capangas[k]] == [lv + 6 * k for lv in niveis], k
        assert [m[1] for m in gemeos[k]] == [60 + 6 * k] * 2, k
    # pedágio: dentro dos andares 4-5 (54-58 na ocupação 1), com o mesmo passo
    d = _defines(TIMES_H)
    assert 54 <= int(d["FAMILIA_NIVEL_PEDAGIO_1"]) <= int(d["FAMILIA_NIVEL_PEDAGIO_2"]) <= 58
    assert int(d["FAMILIA_NIVEL_PASSO"]) == 6
    assert "(ocupacao - 1) * FAMILIA_NIVEL_PASSO" in FAMILIA_C


def test_capangas_visiveis_tem_chapeu_e_paleta_livre_no_andar():
    slots = json.loads(_read("tools/familia_sombra/slots.json"))["slots"]
    for k, ocupacao in enumerate(_membros("sFamiliaCapangas")):
        for i, (sp, _lv, _item, _moves) in enumerate(ocupacao):
            assert sp in COM_CHAPEU and sp not in NUNCA_CAPANGA, (k + 1, i + 1, sp)
            # posição 1/2/3 do andar = PALSLOT_NPC_1/2/3: sem slot repetido no andar e o 4 livre para a Poké Bola
            assert slots[f"OBJ_EVENT_GFX_FAMILIA_{sp}"] == f"PALSLOT_NPC_{i % 3 + 1}", (k + 1, i + 1, sp)
    for ocupacao in _membros("sFamiliaPlantel"):
        assert len(ocupacao) == 6 and not {m[0] for m in ocupacao} & NUNCA_CAPANGA
        assert all(m[1] == 0 for m in ocupacao)         # o nível vem do pedágio / dos andares 4-5


def test_parte_2_marcada():
    for table in ("sFamiliaCapangas", "sFamiliaPlantel"):
        blocos = _ocupacao_blocks(table)
        assert len(blocos) == 4, table
        assert all("// parte 2 troca" not in b for b in blocos[:2]), table
        assert all("// parte 2 troca" in b for b in blocos[2:]), table


def test_cada_membro_com_item_e_quatro_golpes():
    for table in ("sFamiliaCapangas", "sFamiliaGemeos", "sFamiliaPlantel"):
        for ocupacao in _membros(table):
            for sp, _lv, item, moves in ocupacao:
                assert item != "NONE", (table, sp)
                assert len(moves) == 4 and len(set(moves)) == 4 and "NONE" not in moves, (table, sp, moves)
    assert "OT_ID_RANDOM_NO_SHINY" in _block(FAMILIA_C, "static void CriarMembro(")


def test_textos_cabem():
    env = ct._load_env(REPO_ROOT)
    textos = dict(re.findall(r'const u8 (gText_Familia\w+)\[\] = _\("([^"]*)"\);', BATTLE_MESSAGE_C))
    assert textos == {
        "gText_FamiliaCapangaQuerLutar": r"Um capanga da Família Sombra\nquer lutar!\p",
        "gText_FamiliaGemeosQueremLutar": r"Os gêmeos guarda-costas\nquerem lutar!\p",
        "gText_FamiliaDesviaBola": r"O capanga desvia a Poké Bola!\nNinguém tira um membro da Família.",
    }
    for nome, texto in textos.items():
        medida = ct.measure(texto, env, "normal")
        assert medida.widest <= CAIXA_DE_BATALHA_PX and medida.lines == 2, (nome, medida.widest, medida.lines)
    assert "[STRINGID_FAMILIADESVIABOLA - BATTLESTRINGS_TABLE_START]" in BATTLE_MESSAGE_C


def test_sem_dinheiro():
    money = dict(re.findall(r"\{(TRAINER_CLASS_\w+), (\d+)\}",
                            BATTLE_MAIN_C[BATTLE_MAIN_C.index("gTrainerMoneyTable[]"):]))
    assert money["TRAINER_CLASS_FAMILIA_SOMBRA"] == "0"
    # e a vitória nem passa pelo getmoneyreward (nem pelo trainerslidein: não há humano)
    venceu = SCRIPTS_1[SCRIPTS_1.index("BattleScript_FamiliaBattleWon::"):]
    venceu = venceu[:venceu.index("goto BattleScript_PayDayMoneyAndPickUpItems")]
    assert "getmoneyreward" not in venceu and "trainerslidein" not in venceu
    assert re.search(r"case TRAINER_CLASS_FAMILIA_SOMBRA:\s*//[^\n]*\n\s*gBattlescriptCurrInstr = "
                     r"BattleScript_FamiliaBattleWon;", BATTLE_MAIN_C)


def test_musicas():
    pokemon_c = _read("src/pokemon.c")
    assert re.search(r"case TRAINER_CLASS_FAMILIA_SOMBRA:.*?if \(gTrainerBattleOpponent_A == TRAINER_FAMILIA_GEMEOS\)"
                     r"\s*return MUS_VS_GYM_LEADER;\s*return MUS_VS_TRAINER;", pokemon_c, re.S)
    # encontro: TRAINER_ENCOUNTER_MUSIC_AQUA cai no default de PlayTrainerEncounterMusic = MUS_ENCOUNTER_ROCKET
    for name in DOZE:
        assert ".encounterMusic_gender = TRAINER_ENCOUNTER_MUSIC_AQUA," in _trainer(name)
    setup = _block(_read("src/battle_setup.c"), "void PlayTrainerEncounterMusic(void)")
    assert "TRAINER_ENCOUNTER_MUSIC_AQUA" not in setup and "default:\n            music = MUS_ENCOUNTER_ROCKET;" in setup


def test_sem_humano_na_batalha():
    desenho = _block(BATTLE_MAIN_C, "static void BattleIntroDrawTrainersOrMonsSprites(void)")
    assert "familia = FamiliaSombra_EhBatalhaDaFamilia();" in desenho
    assert "if ((gBattleTypeFlags & BATTLE_TYPE_TRAINER) && !familia)" in desenho
    resumo = _block(BATTLE_MAIN_C, "static void BattleIntroDrawPartySummaryScreens(void)")
    assert "if ((gBattleTypeFlags & BATTLE_TYPE_TRAINER) && !FamiliaSombra_EhBatalhaDaFamilia())" in resumo
    slide = _block(_read("src/battle_controller_opponent.c"), "static void OpponentHandleTrainerSlide(void)")
    assert slide.index("FamiliaSombra_EhBatalhaDaFamilia()") < slide.index("DecompressTrainerFrontPic")
    intro = BATTLE_MESSAGE_C[BATTLE_MESSAGE_C.index("case STRINGID_INTROMSG:"):]
    intro = intro[:intro.index("case STRINGID_INTROSENDOUT:")]
    assert intro.index("FamiliaSombra_EhBatalhaDaFamilia()") < intro.index("stringPtr = sText_Trainer1WantsToBattle;\n            }\n        }")
    assert "gText_FamiliaGemeosQueremLutar" in intro and "gText_FamiliaCapangaQuerLutar" in intro


def test_captura_bloqueada_sem_gastar_a_bola():
    cmds = _read("src/battle_script_commands.c")
    bola = _block(cmds, "static void Cmd_handleballthrow(void)")
    familia = bola.index("if (FamiliaSombra_EhBatalhaDaFamilia())")
    assert familia < bola.index("BATTLE_TYPE_GHOST") < bola.index("BATTLE_TYPE_TRAINER")
    trecho = bola[familia:bola.index("BATTLE_TYPE_GHOST")]
    assert "BALL_GHOST_DODGE" in trecho and "BattleScript_FamiliaBallDodge" in trecho
    desvio = SCRIPTS_2[SCRIPTS_2.index("BattleScript_FamiliaBallDodge::"):]
    assert "printstring STRINGID_FAMILIADESVIABOLA" in desvio[:desvio.index("finishaction")]
    uso = _block(_read("src/item_use.c"), "void BattleUseFunc_PokeBallEtc(u8 taskId)")
    assert uso.index("FamiliaSombra_EhBatalhaDaFamilia()") < uso.index("RemoveBagItem")
    ramo = uso[:uso.index("else if")]
    assert "RemoveBagItem" not in ramo and "ItemMenu_StartFadeToExitCallback" in ramo
    eh = _block(FAMILIA_C, "bool8 FamiliaSombra_EhBatalhaDaFamilia(void)")
    assert "TRAINER_CLASS_FAMILIA_SOMBRA" in eh and "BATTLE_TYPE_LINK" in eh


def test_time_pela_ocupacao_no_create_party():
    party = _block(BATTLE_MAIN_C, "static u8 CreateNPCTrainerParty(")
    assert party.index("RematchTier_CreateParty(party, trainerNum)") \
        < party.index("FamiliaSombra_CriarTime(party, trainerNum)") < party.index("ZeroEnemyPartyMons();")
    criar = _block(FAMILIA_C, "u8 FamiliaSombra_CriarTime(")
    assert "TRAINER_FAMILIA_PRIMEIRO" in criar and "TRAINER_FAMILIA_ULTIMO" in criar
    assert "sFamiliaCapangas[ocupacao - 1]" in criar and "sFamiliaPlantel[ocupacao - 1]" in criar


def test_pedagio_sorteia_dois_diferentes():
    sorteio = _block(FAMILIA_C, "void FamiliaSombra_SortearPedagio(void)")
    assert "Random() % FAMILIA_PLANTEL" in sorteio
    assert "(sPedagio[0] + 1 + Random() % (FAMILIA_PLANTEL - 1)) % FAMILIA_PLANTEL" in sorteio
    assert re.search(r"^\tdef_special FamiliaSombra_SortearPedagio$", _read("data/specials.inc"), re.M)


def test_repovoar_limpa_os_doze_treinadores():
    """Ruling R1: a cada ocupação os 12 treinadores-slot voltam (flags de treinador limpas)."""
    repovoar = _block(FAMILIA_C, "void FamiliaSombra_Repovoar(void)")
    assert re.search(r"for \(flag = TRAINER_FAMILIA_PRIMEIRO; flag <= TRAINER_FAMILIA_ULTIMO; flag\+\+\)\s*"
                     r"ClearTrainerFlag\(flag\);", repovoar)
