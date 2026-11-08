"""POK-28: os ovos do Prof. Elm (Chikorita, Cyndaquil, Totodile), no ritmo do ovo raro do Carvalho.

- 1ª oferta: na cena da Dex Nacional, logo depois do ovo raro, ou na conversa comum depois dela (save antigo). O
  Carvalho fala do Prof. Elm e o jogador escolhe um dos três num multichoice com os nomes das espécies.
- Cada nova entrada no Hall da Fama deixa UM ovo do Elm pendente (`FLAG_ELM_EGG_PENDING`), se sobrar espécie.
- Na conversa com os dois pendentes: primeiro o ovo raro, depois o do Elm. Com 2 restantes o jogador escolhe; com 1,
  ele vem direto.
- Sem vaga na equipe nem no PC: nada se perde (nenhuma flag muda, o Carvalho oferece de novo).

O cenário `johto` (`test/esteira/scenarios/full_johto.py`, casos `johto/ovos_elm*`) roda o fluxo de verdade.
"""

import re

from esteira.scenarios import REPO_ROOT

OAK = "data/maps/PalletTown_ProfessorOaksLab"
P = "PalletTown_ProfessorOaksLab_"
FLAGS = (("FLAG_GOT_EGG_CHIKORITA", 0x4D9), ("FLAG_GOT_EGG_CYNDAQUIL", 0x4DA), ("FLAG_GOT_EGG_TOTODILE", 0x4DB),
         ("FLAG_ELM_EGG_PENDING", 0x4DC), ("FLAG_GOT_ELM_EGG", 0x4DD))
SPECIALS = ("GetElmEggChoice", "GiveElmEgg", "MarkElmEggDelivered", "QueueElmEggAfterHallOfFame")


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _block(src: str, label: str) -> str:
    """Corpo do rótulo `label::` até o próximo rótulo global, sem os comentários `@` que abrem o seguinte."""
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    corpo = src[start:start + len(label) + 2 + (m.start() if m else len(src))]
    return re.sub(r"(?:^@[^\n]*\n)+\Z", "", corpo, flags=re.M)


def _func(name: str) -> str:
    """Corpo da função C `name` em src/field_specials.c (até a `}` da coluna 0)."""
    m = re.search(rf"^\w[\w ]*\b{name}\(void\)\n\{{\n(.*?)^\}}", _read("src/field_specials.c"), re.M | re.S)
    assert m, name
    return m.group(1)


def _oak(label: str) -> str:
    return _block(_read(f"{OAK}/scripts.inc"), P + label)


# --- flags -----------------------------------------------------------------------------------------------------------

def test_flags_na_faixa_livre_em_ordem_sem_colisao():
    h = _read("include/constants/flags.h")
    for nome, valor in FLAGS:
        assert re.search(rf"^#define {nome}\s+0x{valor:03X}\b", h, re.M), nome
        assert 0x4D9 <= valor <= 0x4FF
        assert not re.search(rf"^#define FLAG_0x{valor:03X}\b", h, re.M), f"sobrou FLAG_0x{valor:03X} genérica"
    # nenhuma outra flag com o mesmo valor
    valores = re.findall(r"^#define FLAG_\w+\s+(0x[0-9A-Fa-f]+)\b", h, re.M)
    for _, valor in FLAGS:
        assert [int(v, 16) for v in valores].count(valor) == 1, hex(valor)
    # a 0x4DE (próxima depois das do Elm) não é nenhuma delas: virou FLAG_GOT_SNUBBULL na Task 4
    assert 0x4DE not in [valor for _, valor in FLAGS]


# --- C ---------------------------------------------------------------------------------------------------------------

def test_specials_registrados_no_fim_e_declarados():
    inc = _read("data/specials.inc")
    hdr = _read("include/field_specials.h")
    for f in SPECIALS:
        assert inc.count(f"def_special {f}\n") == 1, f
        assert inc.index(f"def_special {f}") > inc.index("def_special FamiliaSombra_EntregarApreendido"), f
        assert inc.index(f"def_special {f}") < inc.index("gSpecialsEnd::"), f
        assert re.search(rf"\b{f}\(void\);", hdr), f


def test_tabela_especie_flag():
    src = _read("src/field_specials.c")
    tab = re.search(r"sElmEggs\[\]\s*=\s*\{(.*?)\};", src, re.S)
    assert tab, "tabela sElmEggs"
    pares = re.findall(r"\{\s*(SPECIES_\w+)\s*,\s*(FLAG_\w+)\s*\}", tab.group(1))
    assert pares == [("SPECIES_CHIKORITA", "FLAG_GOT_EGG_CHIKORITA"),
                     ("SPECIES_CYNDAQUIL", "FLAG_GOT_EGG_CYNDAQUIL"),
                     ("SPECIES_TOTODILE", "FLAG_GOT_EGG_TOTODILE")]


def test_escolha_lista_as_que_faltam_com_o_nome_do_jogo():
    f = _func("GetElmEggChoice")
    assert "FlagGet(" in f
    assert "gSpeciesNames[" in f                       # o nome como o jogo mostra (CHIKORITA...)
    for buf in ("gStringVar1", "gStringVar2", "gStringVar3"):
        assert buf in _read("src/field_specials.c")
    assert "gSpecialVar_0x8005" in f                   # espécie de cada opção, na ordem do menu


def test_multichoice_dinamico_le_os_buffers():
    sm = _read("src/script_menu.c")
    menu = _read("include/constants/menu.h")
    assert re.search(r"^#define MULTICHOICE_ELM_EGG_3\s+67\b", menu, re.M)
    assert re.search(r"^#define MULTICHOICE_ELM_EGG_2\s+68\b", menu, re.M)
    tres = re.search(r"sMultichoiceList_ElmEgg3\[\]\s*=\s*\{(.*?)\};", sm, re.S).group(1)
    dois = re.search(r"sMultichoiceList_ElmEgg2\[\]\s*=\s*\{(.*?)\};", sm, re.S).group(1)
    assert re.findall(r"gStringVar\d", tres) == ["gStringVar1", "gStringVar2", "gStringVar3"]
    assert re.findall(r"gStringVar\d", dois) == ["gStringVar1", "gStringVar2"]
    tabela = re.sub(r" {2,}", " ", sm)
    assert "[MULTICHOICE_ELM_EGG_3] = MULTICHOICE(sMultichoiceList_ElmEgg3)," in tabela
    assert "[MULTICHOICE_ELM_EGG_2] = MULTICHOICE(sMultichoiceList_ElmEgg2)," in tabela


def test_entregar_usa_o_ovo_do_jogo():
    f = _func("GiveElmEgg")
    assert "ScriptGiveEgg(" in f and "gSpecialVar_0x8004" in f
    assert "MON_CANT_GIVE" in f                         # espécie fora da lista não vira ovo


def test_marcar_entrega():
    f = _func("MarkElmEggDelivered")
    assert "gSpecialVar_0x8004" in f
    assert "FlagSet(" in f and "FLAG_GOT_ELM_EGG" in f
    # o 1º ovo não consome o pendente de uma 2ª vitória
    assert f.index("FlagGet(FLAG_GOT_ELM_EGG)") < f.index("FlagClear(FLAG_ELM_EGG_PENDING)")


def test_hall_so_a_partir_da_segunda_vitoria_e_se_sobrar():
    f = _func("QueueElmEggAfterHallOfFame")
    assert "FLAG_SYS_GAME_CLEAR" in f
    assert "FlagSet(FLAG_ELM_EGG_PENDING)" in f
    assert "CountElmEggsLeft()" in f


def test_sem_ram_estatica_nova():
    src = _read("src/field_specials.c")
    trecho = src[src.index("// POK-28 — ovos do Prof. Elm"):]
    trecho = trecho[:trecho.index("// Repel automático")]
    assert not re.search(r"^EWRAM_DATA", trecho, re.M)
    assert not re.search(r"^static (?!const)[^(]*;", trecho, re.M)


# --- scripts ---------------------------------------------------------------------------------------------------------

def test_hall_chama_o_queue_junto_do_ovo_raro():
    corpo = _block(_read("data/scripts/hall_of_fame.inc"), "EventScript_SetDefeatedEliteFourFlagsVars")
    assert corpo.index("special QueueRareEggAfterHallOfFame") < corpo.index("special QueueElmEggAfterHallOfFame")


def test_cena_oferece_depois_do_ovo_raro_e_antes_do_dinheiro():
    s = _read(f"{OAK}/scripts.inc")
    cena = s[s.index(P + "EventScript_NationalDexScene::"):s.index(P + "EventScript_NationalDexSceneRivalEnterNorth::")]
    raro = cena.index("call " + P + "EventScript_TryGiveRareEgg")
    elm = cena.index(P + "EventScript_OakTryElmEgg")
    assert raro < elm < cena.index("addmoney 45000")
    # sem vaga para o ovo raro, a oferta do Elm fica para a conversa (não pergunta à toa)
    assert f"call_if_ne VAR_RESULT, MON_CANT_GIVE, {P}EventScript_OakTryElmEgg" in cena
    # nenhum ovo raro sobrando não bloqueia o do Elm (VAR_RESULT não fica com lixo)
    assert "setvar VAR_RESULT, MON_GIVEN_TO_PARTY" in _oak("EventScript_NoRareEggLeft")


def test_conversa_primeiro_o_raro_depois_o_do_elm():
    chk = _oak("EventScript_OakCheckRareEgg")
    for linha in (f"goto_if_unset FLAG_GOT_RARE_EGG, {P}EventScript_OakGivePendingRareEgg",
                  f"goto_if_set FLAG_RARE_EGG_PENDING, {P}EventScript_OakGivePendingRareEgg",
                  f"goto_if_unset FLAG_GOT_ELM_EGG, {P}EventScript_OakGivePendingElmEgg",
                  f"goto_if_set FLAG_ELM_EGG_PENDING, {P}EventScript_OakGivePendingElmEgg",
                  f"goto {P}EventScript_ProfOakStoryStage"):
        assert linha in chk, linha
    assert chk.index("FLAG_RARE_EGG_PENDING") < chk.index("FLAG_GOT_ELM_EGG")
    # depois do raro, o do Elm na mesma conversa (se o raro coube)
    pend = _oak("EventScript_OakGivePendingRareEgg")
    raro = pend.index("call " + P + "EventScript_TryGiveRareEgg")
    elm = pend.index(f"call_if_ne VAR_RESULT, MON_CANT_GIVE, {P}EventScript_OakTryElmEgg")
    assert raro < elm
    assert pend.rstrip().endswith("end")
    so_elm = _oak("EventScript_OakGivePendingElmEgg")
    assert f"call {P}EventScript_OakTryElmEgg" in so_elm and so_elm.rstrip().endswith("end")


def test_try_elm_egg_primeira_ou_pendente():
    t = _oak("EventScript_OakTryElmEgg")
    assert f"goto_if_unset FLAG_GOT_ELM_EGG, {P}EventScript_OakOffersElmEgg" in t
    assert f"goto_if_set FLAG_ELM_EGG_PENDING, {P}EventScript_OakOffersAnotherElmEgg" in t
    assert "Text_OakElmSentEggs" in _oak("EventScript_OakOffersElmEgg")
    assert "Text_OakAnotherElmEgg" in _oak("EventScript_OakOffersAnotherElmEgg")


def test_escolha_dois_ou_tres_e_um_direto():
    sub = _oak("EventScript_TryGiveElmEgg")
    assert "specialvar VAR_RESULT, GetElmEggChoice" in sub
    assert "goto_if_eq VAR_RESULT, 0," in sub          # nenhuma sobrou: nada
    assert "goto_if_eq VAR_RESULT, 1," in sub          # uma: vem direto, sem menu
    s = _read(f"{OAK}/scripts.inc")
    assert "multichoice 19, 6, MULTICHOICE_ELM_EGG_3, TRUE" in s
    assert "multichoice 19, 8, MULTICHOICE_ELM_EGG_2, TRUE" in s
    um = _oak("EventScript_ElmEggOnlyOne")
    assert "multichoice" not in um and "copyvar VAR_0x8004, VAR_0x8005" in um


def test_resultado_trata_os_tres_casos_e_marca_depois():
    sub = _oak("EventScript_GiveChosenElmEgg")
    assert "specialvar VAR_RESULT, GiveElmEgg" in sub
    assert "goto_if_eq VAR_RESULT, MON_CANT_GIVE" in sub and "goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC" in sub
    assert sub.index("GiveElmEgg") < sub.index("special MarkElmEggDelivered") < sub.index("message ")
    assert "special MarkElmEggDelivered" in _oak("EventScript_ElmEggSentToPC")
    sem = _oak("EventScript_NoRoomForElmEgg")
    assert "MarkElmEggDelivered" not in sem and "Text_OakNoRoomForEgg" in sem


# --- texto -----------------------------------------------------------------------------------------------------------

def _texto(label: str) -> str:
    return "".join(re.findall(r'\.string "(.*?)"', _block(_read(f"{OAK}/text.inc"), P + label)))


def test_falas_do_carvalho_em_ptbr():
    primeira = _texto("Text_OakElmSentEggs")
    assert primeira.startswith("Carvalho:") and "Prof. Elm" in primeira and "Johto" in primeira
    assert _texto("Text_OakAnotherElmEgg").startswith("Carvalho:")
    assert "Ovo" in _texto("Text_WhichElmEgg")
    assert "{STR_VAR_1}" in _texto("Text_ReceivedElmEgg")
    for label in ("Text_OakElmSentEggs", "Text_OakAnotherElmEgg", "Text_WhichElmEgg", "Text_ReceivedElmEgg"):
        corpo = _texto(label)
        assert corpo.endswith("$"), label
        # jogador sem gênero: nada de adjetivo flexionado em referência a {PLAYER}
        assert not re.search(r"\b(bem-vindo|bem-vinda|pronto|pronta|obrigado|obrigada)\b", corpo, re.I), label
