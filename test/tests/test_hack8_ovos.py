"""Hack 8: o ovo raro do Prof. Carvalho (Larvitar, Bagon, Beldum) vem um por vitória na Liga, até os 3.

- 1º ovo: como no Hack 7 (cena pós-Liga do laboratório), sorteado entre os 3.
- Cada nova entrada no Hall da Fama deixa UM ovo pendente (`FLAG_RARE_EGG_PENDING`); ao falar com o
  Carvalho ele entrega um ovo sorteado entre as espécies que ainda não foram dadas
  (`FLAG_GOT_EGG_LARVITAR/BAGON/BELDUM`). Com as 3 dadas, nada.
- Save antigo (`FLAG_GOT_RARE_EGG` sem flag de espécie): `QueueRareEggAfterHallOfFame` marca como dada UMA
  espécie: a do ovo ainda fechado na equipe ou no PC; senão a 1ª (Larvitar, Bagon, Beldum) capturada na
  Pokédex; senão a 1ª vista; senão Larvitar. Sempre exatamente uma.
"""

import re

from esteira.scenarios import REPO_ROOT

OAK = "data/maps/PalletTown_ProfessorOaksLab"
HALL_INC = "data/scripts/hall_of_fame.inc"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _block(src: str, label: str) -> str:
    """Corpo do rótulo `label::` até o próximo rótulo global."""
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    return src[start:start + len(label) + 2 + (m.start() if m else len(src))]


def _func(name: str) -> str:
    """Corpo da função C `name` em src/field_specials.c (até a `}` da coluna 0)."""
    src = _read("src/field_specials.c")
    m = re.search(rf"^\w[\w ]*\b{name}\(void\)\n\{{\n(.*?)^\}}", src, re.M | re.S)
    assert m, name
    return m.group(1)


def _oak(label: str) -> str:
    return _block(_read(f"{OAK}/scripts.inc"), f"PalletTown_ProfessorOaksLab_{label}")


# --- flags -----------------------------------------------------------------------------------------

def test_flags_renomeadas_sem_linha_nova():
    h = _read("include/constants/flags.h")
    for nome, valor in (("FLAG_GOT_EGG_LARVITAR", "0x307"), ("FLAG_GOT_EGG_BAGON", "0x308"),
                        ("FLAG_GOT_EGG_BELDUM", "0x309"), ("FLAG_RARE_EGG_PENDING", "0x30A")):
        assert re.search(rf"^#define {nome}\s+{valor}\b", h, re.M), nome
    for g in ("FLAG_0x307", "FLAG_0x308", "FLAG_0x309", "FLAG_0x30A"):
        assert not re.search(rf"\b{g}\b", h), f"sobrou {g} genérico"
    # as vizinhas seguem genéricas e livres
    assert re.search(r"^#define FLAG_0x30B\s+0x30B\b", h, re.M)
    assert re.search(r"^#define FLAG_JIRACHI_FLEW_AWAY\s+0x306\b", h, re.M)


def test_flag_do_primeiro_ovo_continua():
    assert re.search(r"^#define FLAG_GOT_RARE_EGG\s+0x4A8\b", _read("include/constants/flags.h"), re.M)


# --- C ----------------------------------------------------------------------------------------------

def test_specials_registrados_e_declarados():
    inc = _read("data/specials.inc")
    hdr = _read("include/field_specials.h")
    for f in ("MarkRareEggDelivered", "QueueRareEggAfterHallOfFame"):
        assert f"def_special {f}" in inc, f
        assert re.search(rf"void {f}\(void\);", hdr), f
    # novos no fim da tabela, antes de gSpecialsEnd (não renumera os anteriores)
    assert inc.index("def_special QueueRareEggAfterHallOfFame") < inc.index("gSpecialsEnd::")
    assert inc.index("def_special GetAlteringCaveSetForScript") < inc.index("def_special MarkRareEggDelivered")


def test_sorteio_ignora_as_especies_ja_dadas():
    f = _func("GetRandomRareEggSpecies")
    for fl in ("FLAG_GOT_EGG_LARVITAR", "FLAG_GOT_EGG_BAGON", "FLAG_GOT_EGG_BELDUM"):
        assert fl in _read("src/field_specials.c")
    assert "FlagGet(" in f
    assert "SPECIES_NONE" in f      # nenhuma sobrou: o script não entrega nada
    assert "Random()" in f


def test_tabela_espécie_flag_unica():
    src = _read("src/field_specials.c")
    tab = re.search(r"sRareEggs\[\]\s*=\s*\{(.*?)\};", src, re.S)
    assert tab, "tabela sRareEggs"
    pares = re.findall(r"\{\s*(SPECIES_\w+)\s*,\s*(FLAG_\w+)\s*\}", tab.group(1))
    assert pares == [("SPECIES_LARVITAR", "FLAG_GOT_EGG_LARVITAR"),
                     ("SPECIES_BAGON", "FLAG_GOT_EGG_BAGON"),
                     ("SPECIES_BELDUM", "FLAG_GOT_EGG_BELDUM")]


def test_entrega_marca_especie_e_flags():
    f = _func("MarkRareEggDelivered")
    assert "gSpecialVar_0x8004" in f                 # a espécie que o script acabou de entregar
    assert "FlagSet(" in f and "FLAG_GOT_RARE_EGG" in f
    assert "FlagClear(FLAG_RARE_EGG_PENDING)" in f   # entregou o pendente


def test_entrega_do_primeiro_ovo_nao_consome_o_pendente():
    # o 1º ovo (FLAG_GOT_RARE_EGG ainda desligada) não pode apagar o pendente de uma 2ª vitória
    f = _func("MarkRareEggDelivered")
    got = f.index("FlagGet(FLAG_GOT_RARE_EGG)")
    assert got < f.index("FlagClear(FLAG_RARE_EGG_PENDING)")


def test_sinal_do_hall_so_a_partir_da_segunda_vitoria_e_no_maximo_um_pendente():
    f = _func("QueueRareEggAfterHallOfFame")
    assert "FLAG_SYS_GAME_CLEAR" in f       # ainda desligada na 1ª vitória (EnterHallOfFame a liga depois)
    assert "FlagSet(FLAG_RARE_EGG_PENDING)" in f   # flag, não contador: no máximo 1 pendente


def test_save_antigo_usa_a_pokedex():
    src = _read("src/field_specials.c")
    assert "FLAG_GOT_RARE_EGG" in _func("MigrateLegacyRareEgg")
    f = _func("QueueRareEggAfterHallOfFame")
    assert "FLAG_GET_CAUGHT" in src and "FLAG_GET_SEEN" in src
    # a migração acontece antes de decidir se sobrou ovo
    assert re.search(r"MigrateLegacyRareEgg\(\)", f)
    mig = _func("MigrateLegacyRareEgg").replace("\n", " ")
    assert "FLAG_GET_CAUGHT" in mig and "FLAG_GET_SEEN" in mig
    assert mig.index("FLAG_GET_CAUGHT") < mig.index("FLAG_GET_SEEN")
    assert "SPECIES_LARVITAR" in mig or "sRareEggs[0]" in mig   # sem Pokédex: a 1ª da lista


def test_save_antigo_procura_o_ovo_na_equipe_e_no_pc_antes_da_pokedex():
    # o ovo ainda não chocado não consta na Pokédex: um ovo das 3 espécies na equipe ou no PC é a prova mais direta
    mig = _func("MigrateLegacyRareEgg").replace("\n", " ")
    assert "MON_DATA_IS_EGG" in mig
    assert "GetBoxMonDataAt(" in mig and "TOTAL_BOXES_COUNT" in mig and "IN_BOX_COUNT" in mig
    assert "gPlayerParty" in mig
    assert mig.index("MON_DATA_IS_EGG") < mig.index("GetSetPokedexFlag(")


def test_sem_ram_estatica_nova():
    src = _read("src/field_specials.c")
    trecho = src[src.index("// Hack 8 — ovos raros"):]
    assert not re.search(r"^EWRAM_DATA", trecho, re.M)
    assert not re.search(r"^static (?!const)[^(]*;", trecho, re.M)    # nenhuma variável estática mutável


# --- scripts ------------------------------------------------------------------------------------------

def test_hall_sinaliza_o_ovo_junto_da_entrada():
    s = _read(HALL_INC)
    corpo = _block(s, "EventScript_SetDefeatedEliteFourFlagsVars")
    assert "special QueueRareEggAfterHallOfFame" in corpo
    # roda junto do resto da entrada no Hall: a sala chama esse script antes de `special EnterHallOfFame`
    sala = _read("data/maps/PokemonLeague_HallOfFame/scripts.inc")
    assert sala.index("call EventScript_SetDefeatedEliteFourFlagsVars") < sala.index("special EnterHallOfFame")


def test_entrega_marca_a_especie_nos_dois_desfechos():
    sub = _oak("EventScript_TryGiveRareEgg")
    assert "specialvar VAR_0x8004, GetRandomRareEggSpecies" in sub
    # nenhuma espécie sobrou: não entrega "ovo 0"
    assert "goto_if_eq VAR_0x8004, SPECIES_NONE" in sub
    assert sub.index("goto_if_eq VAR_0x8004, SPECIES_NONE") < sub.index("giveegg")
    assert "MON_CANT_GIVE" in sub and "MON_GIVEN_TO_PC" in sub
    # equipe e PC: os dois chamam o special que marca; a falta de espaço não
    pc = _oak("EventScript_RareEggSentToPC")
    assert "special MarkRareEggDelivered" in pc
    assert sub.count("special MarkRareEggDelivered") == 1
    sem = _oak("EventScript_NoRoomForRareEgg")
    assert "MarkRareEggDelivered" not in sem
    # sem espaço: nada de flag no script (a flag do ovo agora é ligada no special)
    assert "setflag FLAG_GOT_RARE_EGG" not in _read(f"{OAK}/scripts.inc")


def test_marcar_vem_depois_do_giveegg_e_antes_da_fala():
    sub = _oak("EventScript_TryGiveRareEgg")
    assert sub.index("giveegg") < sub.index("special MarkRareEggDelivered") < sub.index("message ")


def test_carvalho_entrega_o_pendente_ao_falar():
    chk = _oak("EventScript_OakCheckRareEgg")
    assert "goto_if_unset FLAG_GOT_RARE_EGG, PalletTown_ProfessorOaksLab_EventScript_OakGivePendingRareEgg" in chk
    assert "goto_if_set FLAG_RARE_EGG_PENDING, PalletTown_ProfessorOaksLab_EventScript_OakGivePendingRareEgg" in chk
    assert "goto PalletTown_ProfessorOaksLab_EventScript_ProfOakStoryStage" in chk
    s = _read(f"{OAK}/scripts.inc")
    oak = _block(s, "PalletTown_ProfessorOaksLab_EventScript_ProfOak")
    assert "OakCheckRareEgg" in oak          # a entrada continua (estágio ≥ 8)


def test_fala_curta_so_nos_ovos_seguintes():
    pend = _oak("EventScript_OakGivePendingRareEgg")
    assert "goto_if_set FLAG_GOT_RARE_EGG" in pend or "call_if_set FLAG_GOT_RARE_EGG" in pend
    assert "PalletTown_ProfessorOaksLab_Text_OakAnotherRareEgg" in _oak("EventScript_OakSaysAnotherRareEgg")
    assert "call PalletTown_ProfessorOaksLab_EventScript_TryGiveRareEgg" in pend
    assert "release" in pend and pend.rstrip().endswith("end")


def test_sem_espaco_continua_pendente():
    # sem espaço: não marca nada, pendente (ou 1º ovo ainda devido) continua; o Carvalho avisa
    sem = _oak("EventScript_NoRoomForRareEgg")
    assert "Text_OakNoRoomForEgg" in sem
    f = _func("MarkRareEggDelivered")
    assert "MON_CANT_GIVE" not in f


# --- texto --------------------------------------------------------------------------------------------

def test_texto_novo_em_ptbr_sem_genero():
    t = _read(f"{OAK}/text.inc")
    corpo = _block(t, "PalletTown_ProfessorOaksLab_Text_OakAnotherRareEgg")
    assert "Carvalho:" in corpo
    linhas = re.findall(r'\.string "(.*?)"', corpo)
    assert 2 <= len(linhas) <= 4
    assert corpo.rstrip().endswith('$"')
    # jogador sem gênero (onda1-comum): nada de adjetivo flexionado em referência a {PLAYER}
    assert not re.search(r"\b(bem-vindo|bem-vinda|pronto|pronta|obrigado|obrigada)\b", corpo, re.I)
