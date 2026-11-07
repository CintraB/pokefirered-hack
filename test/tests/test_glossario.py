"""Glossário de máquina (test/esteira/glossario.json) e a busca de termos da regra `glossario`."""

import json
from collections import Counter

import pytest

from esteira import glossario as gl

DATA = json.loads(gl.GLOSSARY_PATH.read_text(encoding="utf-8"))
TERMS = DATA["termos"]
CATEGORIES = {"tipo", "status", "natureza", "batalha", "habilidade", "golpe", "item", "lugar",
              "personagem", "interface"}


def by_en(en, categoria=None):
    found = [t for t in TERMS if t["en"] == en and categoria in (None, t["categoria"])]
    assert found, en
    return found[0]


# ---- formato -------------------------------------------------------------------------------

def test_every_term_has_the_required_fields():
    for t in TERMS:
        assert set(t) >= {"en", "pt", "fonte", "categoria", "detectar"}, t
        assert t["en"].strip() and t["pt"].strip(), t
        assert t["categoria"] in CATEGORIES, t
        assert isinstance(t["detectar"], bool)


def test_terms_are_unique_per_category():
    dup = [k for k, n in Counter((t["en"], t["categoria"]) for t in TERMS).items() if n > 1]
    assert dup == []


def test_glossary_has_every_section_of_the_approved_document():
    approved = [t for t in TERMS if "frente" not in t]     # acréscimos das frentes ficam de fora
    counts = Counter(t["categoria"] for t in approved)
    assert counts["tipo"] == 18
    assert counts["natureza"] == 25
    assert counts["habilidade"] == 77
    assert counts["golpe"] == 178
    # Task 2: os 176 golpes fora da amostra entram com fonte própria; o glossário cobre os 354,
    # e o POK-45 acrescenta os 6 golpes de Fada da Gen 6
    # e o POK-54 acrescenta Dragon Rush, Dark Void, Fire Fang, Ominous Wind, Nasty Plot e Dark Pulse
    assert sum(t["categoria"] == "golpe" for t in TERMS) == 366
    assert counts["item"] >= 163          # linhas agrupadas ("BLUE / YELLOW / RED FLUTE") viram termos
    assert counts["lugar"] >= 70
    assert len(TERMS) >= 688


def test_created_terms_are_marked():
    assert by_en("SUPER REPEL")["fonte"] == "criado"
    assert by_en("POTION")["fonte"] == "GO+TCG"


def test_decisions_of_section_6():
    assert by_en("HP", "batalha")["pt"] == "PS"
    assert by_en("POKé BALL")["pt"] == "Poké Bola"
    assert by_en("PROF. OAK")["pt"] == "Prof. Carvalho"
    assert by_en("TEAM ROCKET")["pt"] == "Equipe Rocket"
    assert by_en("PALLET TOWN")["pt"] == "Cidade de Pallet"
    assert by_en("QUICK ATTACK")["pt"] == "Atq. Rápido"     # golpe longo: abreviar com ponto
    assert by_en("ROUTE 1")["pt"] == "Rota 1" and by_en("ROUTE 25")["pt"] == "Rota 25"


def test_grouped_rows_are_expanded():
    assert by_en("YELLOW FLUTE")["pt"] == "Flauta Amar."
    assert by_en("WHITE FLUTE")["pt"] == "Flauta Branca"
    assert by_en("CHESTO BERRY")["pt"] == "Fruta Chesto"
    assert by_en("FIGY BERRY")["pt"] == "Fruta Figy"
    assert by_en("BIG PEARL")["pt"] == "Pérola Grande"
    assert by_en("SIX ISLAND")["pt"] == "Ilha Seis"


def test_names_stay_in_the_game_limits():
    for t in TERMS:
        if t["categoria"] == "golpe" or t["categoria"] == "habilidade":
            assert len(t["pt"]) <= 12, t
        elif t["categoria"] == "tipo":
            assert len(t["pt"]) <= 6, t
        elif t["categoria"] == "item" and t["en"].isupper():
            assert len(t["pt"]) <= 13, t


def test_only_game_spelled_terms_are_detected():
    # termos em minúsculas ("move", "type") colidem com português e não são procurados
    assert by_en("move")["detectar"] is False
    assert by_en("POTION")["detectar"] is True
    assert by_en("PP")["detectar"] is False            # igual em PT


def test_forbidden_variants_have_a_replacement():
    variants = {p["variante"]: p for p in DATA["proibidos"]}
    for v in ("Pokébola", "Pokebola", "Professor Oak", "Prof. Oak", "HP", "Team Rocket", "Pokemon"):
        assert v in variants and variants[v]["use"], v


# ---- busca -----------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def glossary():
    return gl.load()


def test_finds_forbidden_variant(glossary):
    (p,) = glossary.problems("Pegue esta Pokébola!")
    assert "Pokébola" in p and "Poké Bola" in p


def test_finds_leftover_english_term(glossary):
    (p,) = glossary.problems("Você ganhou uma POTION.")
    assert "POTION" in p and "Poção" in p


def test_leftover_multiword_term_in_title_case(glossary):
    (p,) = glossary.problems("Bem-vindo a Pallet Town!")
    assert "Pallet Town" in p


def test_whole_words_only(glossary):
    assert glossary.problems("CHAPA de ferro") == []           # "HP" dentro de CHAPA
    assert glossary.problems("Ele usou o Corte.") == []


def test_correct_portuguese_has_no_problem(glossary):
    assert glossary.problems("O Prof. Carvalho deu uma Poké Bola. Seus PS e PE subiram na Rota 1.") == []


def test_new_term_with_placeholder_in_the_translation():
    g = gl.Glossary({"termos": [{"en": "FOO BAR", "pt": "PC de {PLAYER}", "fonte": "criado",
                                 "categoria": "interface", "detectar": True}]})
    assert g.problems("o FOO BAR e o Foo Bar") == ["termo do glossário em inglês 'FOO BAR' (use 'PC de {PLAYER}')",
                                                   "termo do glossário em inglês 'Foo Bar' (use 'PC de {PLAYER}')"]


def test_control_codes_are_not_words(glossary):
    assert glossary.problems("{COLOR RED}{STR_VAR_1}{B_BUFF1}") == []
