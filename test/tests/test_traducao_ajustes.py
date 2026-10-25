"""Ajustes de texto adiados da tradução PT-BR (minors das rodadas 1 a 3), cada um travado:

1. Pokédex do Omanyte volta ao passado ("vivia"), 3 linhas dentro dos 232 px da moldura;
2. página EVOLUÇÃO do resumo: "+ vaga" (enigmático) virou "+ vaga na equipe", e a esteira
   (evolution_page.py) gera a mesma linha que o jogo;
3. Fã-clube de Saffron: nada de "jovem ídolo" e nenhuma linha com "ser!" sozinho;
4. Vale Bicicleta: "Cidade de Cerulean" por extenso (descrição do item);
5. "Polícia de Pewter/Vermilion" e "Museu de Ciências de Pewter" registrados no glossário, uma vez só.
"""

import json
import re
from pathlib import Path

import pytest

from esteira import check_text as ct
from esteira.constants import Constants
from esteira.evolution_page import ARROW, LINE_WIDTH_PX, LV, EvolutionPage, check_page_widths

REPO_ROOT = Path(__file__).resolve().parents[2]
DEX_WIDTH_PX = 232
DEX_LINES = 3
ITEM_DESC_WIDTH_PX = 198


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _c_string(source: str, name: str) -> str:
    """O texto de `const u8 name[] = _(...)`, juntando os pedaços e com `\\n` literal."""
    m = re.search(rf"const u8 {name}\[\] = _\((.*?)\);", source, re.S)
    assert m, name
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))


def _label(source: str, label: str) -> str:
    """O texto cru de um rótulo de `.inc` (pedaços `.string` juntos, sem o `$` final)."""
    m = re.search(rf"^{re.escape(label)}::\n((?:\s+\.string .*\n)+)", source, re.M)
    assert m, label
    return "".join(re.findall(r'\.string "((?:[^"\\]|\\.)*)"', m.group(1))).removesuffix("$")


@pytest.fixture(scope="module")
def env():
    return ct._load_env(REPO_ROOT)


# --- 1. Omanyte ---------------------------------------------------------------------------------

def test_omanyte_voltou_ao_passado(env):
    text = _c_string(_read("src/data/pokemon/pokedex_text_fr.h"), "gOmanytePokedexText")
    assert "vivia" in text.replace("\\n", " ")
    m = ct.measure(text, env)
    assert m.lines <= DEX_LINES
    assert m.widest <= DEX_WIDTH_PX


def test_omanyte_nao_traz_o_presente_do_ingles():
    """O original diz "lived ... swims": o passado do verbo é "vivia", e o texto não tem mais
    "Pokémon pré-histórico do mar" (sem verbo, que era o texto perdido)."""
    text = _c_string(_read("src/data/pokemon/pokedex_text_fr.h"), "gOmanytePokedexText").replace("\\n", " ")
    assert "do mar primitivo" not in text


# --- 2. "+ vaga" -----------------------------------------------------------------------------

def test_vaga_enigmatica_saiu_da_string_do_resumo():
    line = _c_string(_read("src/strings.c"), "gText_PokeSum_EvoLevelFreeSlot")
    assert "+ vaga" not in line.replace("+ vaga na equipe", "")
    assert "+ vaga na equipe" in line
    assert line.startswith("{LV_2} {STR_VAR_1}") and line.endswith("{RIGHT_ARROW_2} {STR_VAR_3}")


def test_esteira_gera_a_mesma_linha_do_shedinja():
    from esteira.evolution_page import evolution_line
    expected = _c_string(_read("src/strings.c"), "gText_PokeSum_EvoLevelFreeSlot")
    expected = expected.replace("{STR_VAR_1}", "20").replace("{STR_VAR_3}", "SHEDINJA")
    assert evolution_line("EVO_LEVEL_SHEDINJA", "20", "SPECIES_SHEDINJA",
                          {"SPECIES_SHEDINJA": "SHEDINJA"}, {}) == expected
    assert expected == f"{LV} 20 + vaga na equipe {ARROW} SHEDINJA"


def test_linha_do_shedinja_cabe_na_pagina(env):
    consts = Constants.load(str(REPO_ROOT), ["species.h"])
    assert check_page_widths(REPO_ROOT, consts) == []
    px = ct.measure(f"{LV} 99 + vaga na equipe {ARROW} MMMMMMMMMM", env).widest
    assert px <= LINE_WIDTH_PX


def test_pagina_do_nincada_mostra_a_vaga():
    consts = Constants.load(str(REPO_ROOT), ["species.h"])
    lines = EvolutionPage(REPO_ROOT, consts).text("SPECIES_NINCADA").split("\n")
    assert lines == [f"{LV} 20 {ARROW} NINJASK", f"{LV} 20 + vaga na equipe {ARROW} SHEDINJA"]


# --- 3. Fã-clube de Saffron --------------------------------------------------------------------

FANCLUB = "data/maps/SaffronCity_PokemonTrainerFanClub/text.inc"


def test_fa_clube_sem_jovem_idolo():
    assert "jovem ídolo" not in _read(FANCLUB).replace("\\n", " ").replace("\\l", " ")


def test_fa_clube_sem_ser_sozinho_na_linha():
    """Nenhuma linha de continuação (depois de `\\n`/`\\l`) do fã-clube não é uma sobra de até 4 letras sozinha
    ("ser!"): a quebra é refeita. Pausa dramática ("Você…") fica; palavra maior na 2ª linha é a quebra normal."""
    for label, body in re.findall(r"^(\w+)::\n((?:\s+\.string .*\n)+)", _read(FANCLUB), re.M):
        text = "".join(re.findall(r'\.string "((?:[^"\\]|\\.)*)"', body)).removesuffix("$")
        for box in text.split("\\p"):
            lines = re.split(r"\\[nl]", box)
            for line in lines[1:]:
                assert " " in line.strip() or len(line) > 4 or line.endswith("…"), f"{label}: sobra de {len(line)} letras sozinha na linha: {line!r}"


def test_fa_clube_brock_fala_inteira():
    text = _label(_read(FANCLUB), "SaffronCity_PokemonTrainerFanClub_Text_BrocksLastWordOnCool")
    flat = re.sub(r"\\[nlp]", " ", text)
    assert flat.endswith("é um cara que eu quero ser!")


def test_fa_clube_promessa_sem_vocativo_antigo():
    text = _label(_read(FANCLUB), "SaffronCity_PokemonTrainerFanClub_Text_NeverSeenTrainerOfYourMagnificence")
    flat = re.sub(r"\\[nlp]", " ", text)
    assert "Faça-me essa promessa" in flat
    assert not re.search(r"\b(jovem|ídolo|campeão|menino|garoto)\b", flat.split("promessa")[-1])


# --- 4. Vale Bicicleta ------------------------------------------------------------------------

def test_vale_bicicleta_diz_cidade_de_cerulean(env):
    items = {i["itemId"]: i for i in json.loads(_read("src/data/items.json"))["items"]}
    desc = items["ITEM_BIKE_VOUCHER"]["description_english"]
    flat = desc.replace("\\n", " ")
    assert "Cidade de Cerulean" in flat
    assert re.sub("Cidade de Cerulean", "", flat).count("Cerulean") == 0
    m = ct.measure(desc, env)
    assert m.widest <= ITEM_DESC_WIDTH_PX
    assert m.lines <= 3
    # o nome da cidade não é partido na quebra
    assert not re.search(r"Cidade de\\nCerulean|Cidade\\nde Cerulean", desc)


# --- 5. Glossário ------------------------------------------------------------------------------

GLOSSARY = json.loads(_read("test/esteira/glossario.json"))
CRIADOS = {
    ("PEWTER POLICE", "personagem"): ("Polícia de Pewter", "data/maps/PewterCity/text.inc"),
    ("VERMILION POLICE", "personagem"): ("Polícia de Vermilion", "data/maps/VermilionCity/text.inc"),
    ("PEWTER MUSEUM OF SCIENCE", "lugar"): ("Museu de Ciências de Pewter", "data/maps/PewterCity/text.inc"),
}


@pytest.mark.parametrize("key", sorted(CRIADOS))
def test_termo_registrado_como_criado_uma_vez(key):
    pt, _ = CRIADOS[key]
    found = [t for t in GLOSSARY["termos"] if (t["en"], t["categoria"]) == key]
    assert len(found) == 1
    assert found[0]["pt"] == pt
    assert found[0]["fonte"] == "criado"
    assert found[0]["detectar"] is True


@pytest.mark.parametrize("key", sorted(CRIADOS))
def test_termo_criado_aparece_na_fala(key):
    pt, rel = CRIADOS[key]
    flat = re.sub(r"\\[nlp]", " ", _read(rel))
    assert pt in flat


def test_nenhum_termo_duplicado_no_glossario():
    from collections import Counter
    dup = [k for k, n in Counter((t["en"], t["categoria"]) for t in GLOSSARY["termos"]).items() if n > 1]
    assert dup == []


# --- esteira: sem achado novo nos arquivos mexidos -----------------------------------------------

TOUCHED = ("src/strings.c", "src/data/pokemon/pokedex_text_fr.h", "src/data/items.json", FANCLUB)


def test_nenhum_achado_de_texto_nos_arquivos_mexidos():
    results = ct.check_text(str(REPO_ROOT), {"text": []})
    unavailable = [r.detail for r in results if "base inglesa indisponível" in r.detail]
    assert unavailable == [], unavailable
    found = [f"{r.name}: {r.detail}" for r in results
             if r.status == "falha" and any(f"{f}:" in r.detail for f in TOUCHED)]
    assert found == []
