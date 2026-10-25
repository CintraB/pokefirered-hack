"""Hack 8: o Amuleto Brilhante passa a exigir os 151 Pokémon de Kanto capturados (Nº 1 a 151, Mew incluído).

- `HasAllMons` (diploma, cartão de treinador, avaliação da Dex Nacional) NÃO muda de sentido: 380
  espécies, sem Mew nem os outros míticos.
- Checagem nova, separada: `HasAllKantoMonsWithMew` (special), capturados 1..151.
- O Carvalho entrega o Amuleto ao avaliar a Pokédex pessoalmente (nunca pelo PC), logo depois da
  avaliação de Kanto e sem precisar da Dex Nacional; a fala "Dex completa" da Nacional continua.
- Os textos que citam a condição falam dos 151 Pokémon de Kanto.
"""

import re

from esteira.scenarios import REPO_ROOT

OAK = "data/maps/PalletTown_ProfessorOaksLab"
RATING = "data/scripts/pokedex_rating.inc"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _c_function(name: str) -> str:
    src = _read("src/pokedex.c")
    m = re.search(rf"^bool16 {name}\(void\)\n\{{\n(.*?)^\}}", src, re.S | re.M)
    assert m, f"{name} não existe em src/pokedex.c"
    return m.group(1)


def _script_block(src: str, label: str) -> str:
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    return src[start:start + len(label) + 2 + (m.start() if m else len(src))]


def _text(rel: str, label: str) -> str:
    """Texto de um rótulo, quebras trocadas por espaço (e as linhas, por linhas separadas)."""
    t = _read(rel)
    bloco = t[t.index(f"{label}::"):]
    bloco = bloco[:bloco.index('$"') + 2]
    return "".join(re.findall(r'\.string "(.*?)"', bloco))


def _flat(text: str) -> str:
    return re.sub(r"\\[nlp]", " ", text)


# --- a condição ----------------------------------------------------------------------------

def test_checagem_dos_151_de_kanto_inclui_o_mew():
    body = _c_function("HasAllKantoMonsWithMew")
    assert re.search(r"i < KANTO_DEX_COUNT;", body), "o laço tem de ir até o Nº 151 (Mew incluído)"
    assert "KANTO_DEX_COUNT - 1" not in body, "não pode excluir o Mew"
    assert "GetSetPokedexFlag(i + 1, FLAG_GET_CAUGHT)" in body, "tem de ser capturado, não visto"
    assert "return FALSE" in body and "return TRUE" in body


def test_checagem_nova_e_um_special_declarado():
    assert re.search(r"^\tdef_special HasAllKantoMonsWithMew$", _read("data/specials.inc"), re.M)
    assert "bool16 HasAllKantoMonsWithMew(void);" in _read("include/pokedex.h")


def test_hasallmons_continua_sem_mew_e_com_380_especies():
    """Diploma, cartão de treinador e avaliação da Dex Nacional dependem dele: sentido intacto."""
    body = _c_function("HasAllMons")
    assert "// -1 excludes Mew" in body
    assert "KANTO_DEX_COUNT - 1" in body
    assert "JOHTO_DEX_COUNT - 3" in body       # sem Lugia, Ho-Oh e Celebi
    assert "NATIONAL_DEX_COUNT - 2" in body    # sem Jirachi e Deoxys
    assert _read("src/diploma.c").count("HasAllMons()") == 2
    assert "HasAllMons()" in _read("src/trainer_card.c")


# --- a entrega -----------------------------------------------------------------------------

def test_amuleto_vem_da_checagem_de_kanto_e_nao_da_dex_completa():
    src = _read(RATING)
    assert "HasAllKantoMonsWithMew" in _script_block(src, "PokedexRating_EventScript_TryGiveShinyCharm")
    assert "TryGiveShinyCharm" not in _script_block(src, "PokedexRating_EventScript_DexComplete"), \
        "a Dex Nacional completa não é mais a condição do Amuleto"
    # a avaliação da Nacional continua usando HasAllMons e a fala da Dex completa
    rate = _script_block(src, "PokedexRating_EventScript_Rate")
    assert "specialvar VAR_RESULT, HasAllMons" in rate
    assert "PokedexRating_EventScript_DexComplete" in rate


def test_amuleto_so_pessoalmente_e_antes_da_dex_nacional():
    rate = _script_block(_read(RATING), "PokedexRating_EventScript_Rate")
    chamada = "call_if_unset FLAG_OAKS_RATING_IS_VIA_PC, PokedexRating_EventScript_TryGiveShinyCharm"
    assert rate.count(chamada) == 1, "só em pessoa (nunca pelo PC)"
    assert "TryGiveShinyCharm" not in rate.replace(chamada, "")
    # depois da avaliação de Kanto e antes de a rotina decidir se a Nacional existe
    assert rate.index("call PokedexRating_EventScript_ShowRatingMsg") < rate.index(chamada) \
        < rate.index("goto_if_eq VAR_0x800A, FALSE, PokedexRating_EventScript_EndRating")


def test_amuleto_uma_vez_so_e_flag_depois_do_item():
    bloco = _script_block(_read(RATING), "PokedexRating_EventScript_TryGiveShinyCharm")
    assert bloco.index("goto_if_set FLAG_GOT_SHINY_CHARM") < bloco.index("HasAllKantoMonsWithMew") \
        < bloco.index("giveitem ITEM_SHINY_CHARM") < bloco.index("setflag FLAG_GOT_SHINY_CHARM")
    # sem a checagem verdadeira, nada de mensagem nem de item
    assert re.search(r"goto_if_eq VAR_RESULT, FALSE, PokedexRating_EventScript_ShinyCharmDone",
                     bloco[:bloco.index("msgbox")])


# --- textos --------------------------------------------------------------------------------

def test_objetivo_do_carvalho_fala_dos_151_de_kanto():
    flat = _flat(_text(f"{OAK}/text.inc", "PalletTown_ProfessorOaksLab_Text_OakShinyCharmGoal"))
    assert "151 Pokémon de Kanto" in flat, flat
    assert "Amuleto Brilhante" in flat
    assert "Nacional" not in flat, "a condição não é mais a Pokédex Nacional"


def test_entrega_fala_dos_151_de_kanto():
    flat = _flat(_text("data/text/pokedex_rating.inc", "PokedexRating_Text_TakeShinyCharm"))
    assert "151 Pokémon de Kanto" in flat, flat
    assert "Nacional" not in flat


def test_nenhum_texto_do_amuleto_cita_a_dex_nacional_como_condicao():
    for rel, label in ((f"{OAK}/text.inc", "PalletTown_ProfessorOaksLab_Text_OakShinyCharmGoal"),
                       ("data/text/pokedex_rating.inc", "PokedexRating_Text_TakeShinyCharm"),
                       ("data/text/pokedex_rating.inc", "PokedexRating_Text_ShinyCharmExplanation")):
        assert "Nacional" not in _text(rel, label), label


def test_objetivo_mantem_o_termo_inteiro_e_a_estrutura_da_tela():
    r"""O cenário `pos_liga` fotografa 'Amuleto Brilhante' depois de 2 esperas (\p e \l) e o termo
    não pode ser partido na quebra de linha."""
    body = _text(f"{OAK}/text.inc", "PalletTown_ProfessorOaksLab_Text_OakShinyCharmGoal")
    antes = body[:body.index("Amuleto Brilhante")]
    assert antes.count(r"\p") + antes.count(r"\l") == 2
    assert r"Amuleto\n" not in body and r"Amuleto\l" not in body
    # jogador sem gênero e no máximo 2 linhas visíveis por caixa
    for caixa in body.split("\\p"):
        assert len(re.split(r"\\[nl]", caixa)) <= 3, caixa  # 3ª linha só chega por rolagem (\l)
