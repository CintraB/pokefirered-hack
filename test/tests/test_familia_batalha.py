"""POK-51 (Task 3): capangas da Família Sombra como treinadores. Leitura estática do C, dos dados e dos scripts.

Os 12 treinadores-slot (9 capangas visíveis, os gêmeos em dupla e as 2 lutas do pedágio) são da classe
TRAINER_CLASS_FAMILIA_SOMBRA: IA dos chefes, sem prêmio, sem humano na batalha (o Pokémon aparece direto) e sem
captura (a bola é desviada e não é gasta). O time de cada um sai de src/data/familia_sombra_times.h pela ocupação.
O comportamento no jogo fica no cenário `familia` da esteira (test/esteira/scenarios/full_familia.py).
"""

import importlib.util
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
    assert int(d["NUM_TRAINERS"]) == 755 and int(d["MAX_TRAINERS_COUNT"]) == 768
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


def test_ladrao_cobica_e_truque_nao_tiram_o_item():
    """§6.3: o item que fortalece o capanga não vai para o jogador. Um ponto só (capangas, andares 4-5, chefe)."""
    protegido = _block(FAMILIA_C, "bool8 FamiliaSombra_ItemProtegido(void)")
    assert "return FamiliaSombra_EhBatalhaDaFamilia() || FamiliaSombra_EhChefe();" in protegido
    cmds = _read("src/battle_script_commands.c")
    # Ladrão/Cobiça (MOVE_EFFECT_STEAL_ITEM): falha antes de qualquer cópia do item
    roubo = cmds[cmds.index("case MOVE_EFFECT_STEAL_ITEM:"):]
    roubo = roubo[:roubo.index("BattleScript_ItemSteal;")]
    trecho = roubo[roubo.index("else if (FamiliaSombra_ItemProtegido())"):]
    assert trecho.index("gBattlescriptCurrInstr++;") < trecho.index("changedItems")
    # Truque: a 1ª condição do Cmd_tryswapitems já pula para o "falhou"
    troca = _block(cmds, "static void Cmd_tryswapitems(void)")
    assert re.search(r"if \(FamiliaSombra_ItemProtegido\(\)\n\s*\|\| gBattleTypeFlags & BATTLE_TYPE_TRAINER_TOWER", troca)
    assert cmds.count("FamiliaSombra_ItemProtegido()") == 2


# ---- Task 4: andares 4-5 (encontros), efeito de filme e o chefe ------------------------------------------------

BATTLE_H = _read("include/constants/battle.h")
BATTLE_SETUP_C = _read("src/battle_setup.c")
GFX_UTIL_C = _read("src/battle_gfx_sfx_util.c")
WILD_C = _read("src/wild_encounter.c")
POKEMON_C = _read("src/pokemon.c")
NOIR_H = REPO_ROOT / "src" / "data" / "familia_sombra_noir.h"


def _noir_tool():
    spec = importlib.util.spec_from_file_location("familia_noir", REPO_ROOT / "tools" / "familia_sombra" / "noir.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bit_familia_livre():
    """Os 2 bits novos de gBattleTypeFlags ficam na faixa livre (20-31) e não repetem nenhum outro BATTLE_TYPE_*."""
    bits = {n: int(v) for n, v in re.findall(r"#define (BATTLE_TYPE_\w+)\s+\(1 << (\d+)\)", BATTLE_H)}
    for nome in ("BATTLE_TYPE_FAMILIA", "BATTLE_TYPE_FAMILIA_CHEFE"):
        assert 20 <= bits[nome] <= 31, nome
        outros = [n for n, b in bits.items() if b == bits[nome] and n != nome]
        assert not outros, (nome, outros)


def test_noir_preserva_transparencia():
    """FamiliaSombra_PaletaNoir: o índice 0 (transparente) fica como está; as outras cores saem da tabela gerada pela
    função noir() da prévia, indexada pela soma 30r + 59g + 11b (a mesma conta do C)."""
    noir = _block(FAMILIA_C, "void FamiliaSombra_PaletaNoir(u16 *pal, u16 count)")
    assert re.search(r"for \(i = 1; i < count; i\+\+\)", noir)
    assert "sFamiliaNoir[30 * GET_R(cor) + 59 * GET_G(cor) + 11 * GET_B(cor)]" in noir
    tool = _noir_tool()
    assert tool.cabecalho() == NOIR_H.read_text(encoding="utf-8"), "rode tools/familia_sombra/noir.py"
    tabela = tool.tabela()
    # toda cor de 5 bits: a tabela pela soma = noir() da prévia aplicado à cor
    for cor in range(0x8000):
        assert tabela[tool.soma(cor)] == tool.noir_gba(cor), hex(cor)
    # preto continua preto; branco vira um cinza-azulado claro (azul >= verde >= vermelho, pouca saturação)
    assert tabela[0] == 0
    branco = tabela[tool.S_MAX]
    r, g, b = branco & 31, branco >> 5 & 31, branco >> 10 & 31
    assert b >= g >= r and b - r <= 6 and r >= 20, (r, g, b)


def test_filme_na_paleta_do_oponente():
    """A paleta do Pokémon do oponente passa pelo filme antes das 2 cópias (OBJ e BG): LoadPalette grava Unfaded e
    Faded (o clima do POK-15 reaplica a partir do Unfaded). Reshow e substituto chamam a mesma função."""
    carga = _block(GFX_UTIL_C, "void BattleLoadOpponentMonSpriteGfx(struct Pokemon *mon, u8 battlerId)")
    filme = carga.index("FamiliaSombra_PaletaNoir(buffer, 16)")
    descompacta = carga.index("LZDecompressWram(lzPaletteData, buffer)")
    assert descompacta < filme < carga.index("LoadPalette(buffer, paletteOffset")
    assert "if (FamiliaSombra_EhBatalhaDaFamilia())" in carga[:filme]
    assert "BattleLoadOpponentMonSpriteGfx(&gEnemyParty" in _read("src/reshow_battle_screen.c")
    assert "BattleLoadOpponentMonSpriteGfx(&gEnemyParty" in GFX_UTIL_C


def test_chefe_sem_filme():
    """O chefe entra com as cores shiny: a batalha dele liga só BATTLE_TYPE_FAMILIA_CHEFE, e o ramo do filme (e da
    bola desviada) é o de FamiliaSombra_EhBatalhaDaFamilia, que não olha esse bit."""
    eh = _block(FAMILIA_C, "bool8 FamiliaSombra_EhBatalhaDaFamilia(void)")
    assert "BATTLE_TYPE_FAMILIA_CHEFE" not in eh and re.search(r"BATTLE_TYPE_FAMILIA\b", eh)
    chefe = _block(BATTLE_SETUP_C, "void StartFamiliaChefeBattle(void)")
    flags = re.search(r"gBattleTypeFlags = ([^;]+);", chefe).group(1)
    assert "BATTLE_TYPE_FAMILIA_CHEFE" in flags and not re.search(r"BATTLE_TYPE_FAMILIA\b", flags)
    assert "BATTLE_TYPE_LEGENDARY" in flags
    assert "CreateBattleStartTask(B_TRANSITION_BLUR, MUS_VS_LEGEND);" in chefe
    assert "gTrainerBattleOpponent_A = 0;" in chefe          # nada de treinador velho na IA do chefe
    # o chefe é capturável (a bola segue o caminho normal e é gasta), mas o item fixo dele não sai (Ladrão/Truque)
    protegido = _block(FAMILIA_C, "bool8 FamiliaSombra_ItemProtegido(void)")
    assert "FamiliaSombra_EhBatalhaDaFamilia()" in protegido and "FamiliaSombra_EhChefe()" in protegido
    assert "BATTLE_TYPE_FAMILIA_CHEFE" in _block(FAMILIA_C, "bool8 FamiliaSombra_EhChefe(void)")


def _chefes() -> list[tuple[str, int, str, list[str]]]:
    return [(sp, int(lv), item, [x.strip() for x in mv.split(",")]) for sp, lv, item, mv in re.findall(
        r"MEMBRO\((\w+),\s*(\d+),\s*(\w+),\s*([\w ,]+)\)", _block(TIMES_H, "sFamiliaChefes["))]


def test_chefe_shiny_receita():
    """§6.5: o chefe é sempre shiny. A receita do SetLeadShiny (test_hooks.c): o jogador como OT e a metade alta da
    personalidade = OT alto ^ OT baixo ^ metade baixa (valor shiny 0); a metade baixa ao acaso (natureza e gênero)."""
    iniciar = _block(FAMILIA_C, "void FamiliaSombra_IniciarChefe(void)")
    assert "GetPlayerTrainerId()" in iniciar
    assert ("CreateMon(mon, chefe->species, chefe->level, MAX_PER_STAT_IVS, TRUE, personality, OT_ID_PLAYER_ID, 0);"
            in iniciar)
    assert "personality = (((otId >> 16) ^ (otId & 0xFFFF) ^ baixa) & 0xFFFF) << 16 | baixa;" in iniciar
    assert "SetMonMoveSlot(mon, chefe->moves[i], i);" in iniciar
    assert "MON_DATA_HELD_ITEM" in iniciar and "StartFamiliaChefeBattle();" in iniciar
    assert re.search(r"^\tdef_special FamiliaSombra_IniciarChefe$", _read("data/specials.inc"), re.M)
    # a conta dá shiny para qualquer OT e qualquer metade baixa
    for ot in (0, 0x12345678, 0xFFFFFFFF, 0xBEEF0042):
        for baixa in (0, 1, 0x7FFF, 0xFFFF):
            pid = (((ot >> 16) ^ (ot & 0xFFFF) ^ baixa) & 0xFFFF) << 16 | baixa
            assert ((ot >> 16) ^ (ot & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF)) < 8


def test_chefes_da_tabela():
    """Gengar nv 62 (o Dom) e Tyranitar nv 68 (o Cobrador), +6 por ocupação; 4 golpes e item fixos, com o porquê."""
    chefes = _chefes()
    assert [c[0] for c in chefes[:2]] == ["GENGAR", "TYRANITAR"]
    assert [c[1] for c in chefes] == [62, 68, 74, 80]
    for sp, _lv, item, moves in chefes:
        assert item != "NONE" and len(set(moves)) == 4 and "NONE" not in moves, sp
    assert chefes[0][3] == ["SHADOW_BALL", "HYPNOSIS", "DREAM_EATER", "THUNDERBOLT"]
    assert chefes[0][2] == "SPELL_TAG"
    tabela = _block(TIMES_H, "sFamiliaChefes[")
    assert tabela.count("// parte 2 troca") == 2
    assert len(re.findall(r"//[^\n]{30,}", tabela)) >= 4        # o porquê de cada escolha


def test_niveis_andares_4_5():
    """§6.3: andares 4-5 = 54-58 na ocupação 1, +6 por ocupação; espécie, item e golpes do plantel."""
    d = _defines(TIMES_H)
    assert (int(d["FAMILIA_NIVEL_ANDAR_MIN"]), int(d["FAMILIA_NIVEL_ANDAR_MAX"])) == (54, 58)
    criar = _block(FAMILIA_C, "u8 FamiliaSombra_NivelSelvagem(void)")
    assert "FAMILIA_NIVEL_ANDAR_MIN + Random() % (FAMILIA_NIVEL_ANDAR_MAX - FAMILIA_NIVEL_ANDAR_MIN + 1)" in criar
    assert "(OcupacaoDasLutas() - 1) * FAMILIA_NIVEL_PASSO" in criar
    criar = _block(FAMILIA_C, "void FamiliaSombra_CriarSelvagem(u8 level)")
    assert "CriarMembro(&gEnemyParty[0], &sFamiliaPlantel[ocupacao - 1][Random() % FAMILIA_PLANTEL], level);" in criar
    # o item do plantel não é trocado pelo item comum da espécie
    assert re.search(r"BATTLE_TYPE_FAMILIA\b", _block(POKEMON_C, "void SetWildMonHeldItem(void)"))


def test_encontro_so_com_chefe_nos_andares_escuros():
    """Os andares 4-5 (lista de FamiliaSombra_EhAndarEscuro, a Task 5 preenche) só têm encontro com chefe ativo, sem
    andarilho, e o encontro é da Família: bit próprio, música de treinador e o texto do capanga."""
    # o caminho comum (StandardWildEncounter, TryGenerateWildMon) fica como o da pret: o desvio é antes dele
    tentar = _block(WILD_C, "bool8 TryStandardWildEncounter(u32 currMetatileAttrs)")
    desvio = tentar.index("FamiliaSombra_EhAndarEscuro()")
    assert desvio < tentar.index("FamiliaWildEncounter(") < tentar.index("StandardWildEncounter(currMetatileAttrs")
    assert "FamiliaSombra_EhAndarEscuro()" not in _block(WILD_C, "bool8 StandardWildEncounter(")
    andar = _block(WILD_C, "static bool8 FamiliaWildEncounter(")
    assert "!FamiliaSombra_ChefeAtivo()" in andar and "TryStartRoamerEncounter" not in andar
    assert "DoWildEncounterRateTest(rate, FALSE)" in andar and "TryStartFamiliaEncounter(TRUE)" in andar
    criar = _block(WILD_C, "static bool8 TryStartFamiliaEncounter(bool8 checkRepel)")
    assert criar.index("FamiliaSombra_ChefeAtivo()") < criar.index("FamiliaSombra_CriarSelvagem(level);")
    assert criar.index("IsWildLevelAllowedByRepel(level)") < criar.index("FamiliaSombra_CriarSelvagem(level);")
    assert "StartWildBattle();" in criar
    aroma = _block(WILD_C, "bool8 SweetScentWildEncounter(void)")
    assert aroma.index("FamiliaSombra_EhAndarEscuro()") < aroma.index("TryStartRoamerEncounter")
    inicio = _block(BATTLE_SETUP_C, "void StartWildBattle(void)")
    assert inicio.index("FamiliaSombra_EhAndarEscuro()") < inicio.index("DoStandardWildBattle();")
    selvagem = _block(BATTLE_SETUP_C, "void StartFamiliaWildBattle(void)")
    assert "gBattleTypeFlags = BATTLE_TYPE_FAMILIA;" in selvagem
    assert "CreateBattleStartTask(GetWildBattleTransition(), MUS_VS_TRAINER);" in selvagem
    assert "sAndaresEscuros" in _block(FAMILIA_C, "bool8 FamiliaSombra_EhAndarEscuro(void)")
    intro = BATTLE_MESSAGE_C[BATTLE_MESSAGE_C.index("case STRINGID_INTROMSG:"):]
    intro = intro[:intro.index("case STRINGID_INTROSENDOUT:")]
    selv = intro[intro.index("if (gBattleTypeFlags & BATTLE_TYPE_FAMILIA)"):]
    assert selv.index("stringPtr = gText_FamiliaCapangaQuerLutar;") < selv.index("BATTLE_TYPE_GHOST")
    # o selvagem da Família é da Família: bola desviada, filme, item protegido
    eh = _block(FAMILIA_C, "bool8 FamiliaSombra_EhBatalhaDaFamilia(void)")
    assert eh.index("BATTLE_TYPE_LINK") < eh.index("BATTLE_TYPE_FAMILIA)") < eh.index("BATTLE_TYPE_TRAINER)")


def test_ia_do_chefe():
    """§6.3: o chefe, mesmo capturável, escolhe golpes com a IA dos chefes (as 5 flags), não ao acaso."""
    ai = _block(_read("src/battle_ai_script_commands.c"), "void BattleAI_SetupAIData(void)")
    chefe = ai.index("if (FamiliaSombra_EhChefe())")
    assert chefe < ai.index("BATTLE_TYPE_SAFARI") and "FAMILIA_AI_CHEFE" in ai[chefe:ai.index("BATTLE_TYPE_SAFARI")]
    constantes = _read("include/constants/familia_sombra.h").replace("\\\n", " ")
    flags = re.search(r"#define FAMILIA_AI_CHEFE\s+\(([^)]*)\)", constantes).group(1)
    assert {f.strip() for f in flags.split("|")} == AI_CHEFE
    escolha = _block(_read("src/battle_controller_opponent.c"), "static void OpponentHandleChooseMove(void)")
    assert re.search(r"BATTLE_TYPE_ROAMER\)\s*\|\| FamiliaSombra_EhChefe\(\)\)", escolha)
