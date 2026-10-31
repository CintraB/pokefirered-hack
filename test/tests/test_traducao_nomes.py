"""Task 2 da tradução: nomes curtos (golpes, habilidades, naturezas, tipos, classes de Treinador,
itens, frutas, lugares e sugestões de nome).

Cada nome é comparado com o texto inglês da base (`TRANSLATION_BASE`, pelo git) e com o glossário
de máquina (`test/esteira/glossario.json`): o nome traduzido é exatamente o termo do glossário
para aquele inglês. Os limites vêm da checagem de texto (`esteira.check_text.WIDTH_RULES`).
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))

# Textos que não são nomes a traduzir (marcadores vazios do jogo) ou já eram PT-BR na base
UNCHANGED = {"-$$$$$$", "-------", "???", "????????", "Escama Prisma"}
# Classe TEAM ROCKET: glossário §2.9 (TEAM ROCKET GRUNT = classe "Recruta" + nome "Rocket")
CLASS_OVERRIDES = {"TEAM ROCKET": "Recruta"}
# Chaves acrescentadas por nós (não existem na base inglesa): arquivo -> {chave: nome}
# D3 / decisão D4 do Cintra: os 2 ADMIN da Equipe Rocket viram "Executivo" (pic masculina) e "Executiva" (feminina)
NEW_KEYS = {"src/data/text/trainer_class_names.h": {"TRAINER_CLASS_ROCKET_ADMIN": "Executivo",
                                                  "TRAINER_CLASS_ROCKET_ADMIN_F": "Executiva"},
            # itens novos em slots que eram "????????" na base (POK-36, POK-37)
            "src/data/items.json": {"ITEM_PORTABLE_PC": "PC Portátil", "ITEM_INCUBATOR": "Incubadora"},
            # tipo novo (POK-45)
            "src/battle_main.c": {"TYPE_FAIRY": "Fada"}}
BERRY_NAME_LENGTH = 6          # include/global.berry.h
POPUP_PX = 112                 # aviso de nome do mapa: maxWidth (src/map_name_popup.c:195)


def _c_table(source: str, start: str) -> dict[str, str]:
    """[CHAVE] = _("texto") de uma tabela C que começa em `start`."""
    i = source.index(start)
    body = source[i:source.index("};", i)]
    return dict(re.findall(r'\[(\w+)\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', body))


def _natures(source: str) -> dict[str, str]:
    return dict(re.findall(r'(s\w+NatureName)\[\] = _\("([^"]*)"\)', source))


def _items(source: str) -> dict[str, str]:
    return {it["itemId"]: it["english"] for it in json.loads(source)["items"]}


def _berries(source: str) -> dict[str, str]:
    return {f"berry{i}": name for i, name in enumerate(re.findall(r'\.name = _\("([^"]*)"\)', source))}


def _places(source: str) -> dict[str, str]:
    return {s["id"]: s["name"] for s in json.loads(source)["map_sections"] if "name" in s}


def _name_choices(source: str) -> dict[str, str]:
    return dict(re.findall(r'(gNameChoice_\w+)::\s*\.string "([^"$]*)\$"', source))


# arquivo -> (extrator, categoria do glossário)
SOURCES = {
    "src/data/text/move_names.h": (lambda s: _c_table(s, "gMoveNames["), "golpe"),
    "src/data/text/abilities.h": (lambda s: _c_table(s, "gAbilityNames["), "habilidade"),
    "src/data/text/nature_names.h": (_natures, "natureza"),
    "src/battle_main.c": (lambda s: _c_table(s, "gTypeNames["), "tipo"),
    "src/data/text/trainer_class_names.h": (lambda s: _c_table(s, "gTrainerClassNames["), "personagem"),
    "src/data/items.json": (_items, "item"),
    "src/berry.c": (_berries, "item"),
    "src/data/region_map/region_map_sections.json": (_places, "lugar"),
    "data/text/new_game_intro.inc": (_name_choices, None),
}


def _glossary(categoria: str) -> dict[str, str]:
    return {t["en"]: t["pt"] for t in GLOSSARY["termos"] if t["categoria"] == categoria}


@lru_cache(maxsize=None)
def _base(rel: str) -> dict[str, str] | None:
    if shutil.which("git") is None:
        return None
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        return None
    return SOURCES[rel][0](out.stdout.decode("utf-8"))


def _current(rel: str) -> dict[str, str]:
    return SOURCES[rel][0]((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _expected(rel: str, en: str) -> str:
    """O nome que o glossário manda para o texto inglês `en` deste arquivo."""
    if en in UNCHANGED:
        return en
    categoria = SOURCES[rel][1]
    if rel == "data/text/new_game_intro.inc":
        return en.title()                                   # nome próprio, caixa mista (§6.3)
    if rel == "src/berry.c":                                # "Fruta Cheri" -> "Cheri", até 6 letras
        return _glossary("item")[f"{en} BERRY"][len("Fruta "):][:BERRY_NAME_LENGTH]
    if rel == "src/data/text/trainer_class_names.h" and en in CLASS_OVERRIDES:
        return CLASS_OVERRIDES[en]
    return _glossary(categoria)[en]


def _pairs(rel: str):
    base = _base(rel)
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    current = _current(rel)
    assert set(current) >= set(base), f"{rel}: faltam chaves da base"
    # chaves que não existem na base inglesa (classe nova da D3): só as combinadas, com o nome esperado
    assert {k: current[k] for k in set(current) - set(base)} == NEW_KEYS.get(rel, {}), \
        f"{rel}: chaves diferentes da base"
    return [(key, base[key], current[key]) for key in sorted(base)]


@pytest.mark.parametrize("rel", sorted(SOURCES))
def test_nomes_batem_com_o_glossario(rel):
    wrong = [f"{key}: {en!r} -> {cur!r} (glossário: {_expected(rel, en)!r})"
             for key, en, cur in _pairs(rel) if cur != _expected(rel, en)]
    assert wrong == []


@pytest.mark.parametrize("rel", sorted(SOURCES))
def test_nenhum_nome_em_ingles_sobrando(rel):
    left = [f"{key}: {cur!r}" for key, en, cur in _pairs(rel) if en not in UNCHANGED and cur == en]
    # palavra em CAIXA ALTA de 3+ letras = grafia do jogo inglês (os nomes vão em caixa mista)
    caps = [f"{key}: {cur!r}" for key, _en, cur in _pairs(rel)
            if cur not in UNCHANGED and re.search(r"(?<![\w{])[A-Z]{3,}(?![\w}])", re.sub(r"\{[^}]*\}", "", cur))]
    assert left == [] and caps == []


@pytest.fixture(scope="module")
def env():
    return ct._load_env(REPO_ROOT)


@pytest.mark.parametrize("rel", sorted(r for r in SOURCES if r != "data/text/new_game_intro.inc"))
def test_nomes_cabem_nos_limites_da_esteira(rel, env):
    kind = {"src/data/items.json": "items", "src/data/region_map/region_map_sections.json": "region_map"}.get(rel, "c")
    names = set(_current(rel).values())
    problems = []
    for entry in ct._extract(rel, kind, (REPO_ROOT / rel).read_text(encoding="utf-8")):
        if not isinstance(entry, ct._Entry) or entry.texts[0] not in names:
            continue
        if kind == "items" and not entry.label.endswith(".name"):
            continue                                            # descrições: outra frente
        rule = ct.rule_for(entry.file, entry.label)
        # natureza: sem buffer fixo, a frase "Natureza X." é medida pela frente E (só o charmap aqui)
        assert rule is not None and (rule.px or rule.chars or rel.endswith("nature_names.h")), (rel, entry.label)
        m = ct.measure(entry.texts[0], env, rule.font)
        if m.bad or m.bad_words:
            problems.append(f"{entry.label}: fora do charmap {m.bad + m.bad_words}")
        if rule.px is not None and m.widest > rule.px:
            problems.append(f"{entry.label}: {m.widest} px > {rule.px}")
        if rule.chars is not None and m.nbytes > rule.chars:
            problems.append(f"{entry.label}: {m.nbytes} letras > {rule.chars}")
        if kind == "region_map" and m.widest > POPUP_PX:
            problems.append(f"{entry.label}: aviso de mapa {m.widest} px > {POPUP_PX}")
    assert problems == []


def test_limites_usados_sao_os_da_esteira():
    assert ct.rule_for("src/data/text/move_names.h", "MOVE_POUND").chars == 12
    assert ct.rule_for("src/data/text/abilities.h", "ABILITY_STENCH").chars == 12
    assert ct.rule_for("src/battle_main.c", "TYPE_NORMAL").chars == 6
    assert ct.rule_for("src/data/text/trainer_class_names.h", "TRAINER_CLASS_HIKER").chars == 12
    assert ct.rule_for("src/data/items.json", "ITEM_POTION.name").chars == ct.ITEM_NAME_MAX_CHARS == 13
    place = ct.rule_for("src/data/region_map/region_map_sections.json", "MAPSEC_PALLET_TOWN")
    assert (place.chars, place.px) == (18, 108)


def test_glossario_cobre_todos_os_golpes_do_jogo():
    moves = {en for en in _current_or_base_moves() if en not in UNCHANGED}
    assert moves <= set(_glossary("golpe"))
    for t in GLOSSARY["termos"]:
        if t.get("frente") == "Task 2":
            assert t["fonte"] in ("GO", "GO+TCG", "TCG", "TCG antigo", "criado"), t


def _current_or_base_moves():
    base = _base("src/data/text/move_names.h")
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    return base.values()


def test_sete_lugares_encurtados_pela_regra_1():
    """Decisão 5 do controlador: os nomes de 19-20 letras do glossário viraram estes."""
    places = _glossary("lugar")
    assert {en: places[en] for en in ("VERMILION CITY", "VIRIDIAN FOREST", "CERULEAN CAVE", "UNDERGROUND PATH",
                                      "THREE ISLE PATH", "BERRY FOREST", "FIVE ISLE MEADOW")} == {
        "VERMILION CITY": "Cidade Vermilion", "VIRIDIAN FOREST": "Floresta Viridian",
        "CERULEAN CAVE": "Caverna Cerulean", "UNDERGROUND PATH": "Via Subterrânea",
        "THREE ISLE PATH": "Trilha Ilha Três", "BERRY FOREST": "Bosque das Frutas",
        "FIVE ISLE MEADOW": "Prado Ilha Cinco"}
    # "POKéMON NET CENTER".isupper() é falso por causa do "é": troca antes de testar. Placas e nomes só citados em
    # fala (obs com "placa" ou "não é nome de mapa") não passam pelo aviso de mapa e ficam de fora do limite.
    assert all(len(pt) <= 18 for t in GLOSSARY["termos"] if t["categoria"] == "lugar" for pt in [t["pt"]]
               if t["en"].replace("é", "E").isupper()
               and "placa" not in t.get("obs", "") and "não é nome de mapa" not in t.get("obs", ""))


def test_gary_e_a_primeira_sugestao_do_rival():
    source = (REPO_ROOT / "src" / "oak_speech.c").read_text(encoding="utf-8")
    block = source[source.index("sRivalNameChoices[]"):]
    firered = block[block.index("#if defined(FIRERED)"):block.index("#elif")]
    assert re.findall(r"gNameChoice_\w+", firered) == ["gNameChoice_Gary", "gNameChoice_Green",
                                                       "gNameChoice_Kaz", "gNameChoice_Toru"]


def test_simbolos_dos_lugares_nao_dependem_do_nome():
    """sMapsecName_* sai do id da seção (getVar), não do nome: o nome traduzido ("Liga Pokémon")
    não pode mudar os símbolos que src/region_map.c usa (sDungeonInfo, GetMapName)."""
    folder = REPO_ROOT / "src" / "data" / "region_map"
    for name in ("region_map_sections.strings.json.txt", "region_map_sections.entries.json.txt"):
        template = (folder / name).read_text(encoding="utf-8")
        assert "sMapsecName_{{ getVar(map_section.name) }}" in template and "cleanString" not in template
    ids = {s["id"] for s in json.loads((folder / "region_map_sections.json").read_text(encoding="utf-8"))["map_sections"]}
    used = set(re.findall(r"sMapsecName_(\w+)", (REPO_ROOT / "src" / "region_map.c").read_text(encoding="utf-8")))
    assert used and used <= ids


def test_fruta_enigma_tem_o_prefixo_na_frente():
    """PT-BR inverte a ordem: "Fruta Enigma" (glossário §2.7, detalhe técnico)."""
    strings = (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")
    assert re.search(r'gText_Berry\[\] = _\("Fruta "\);', strings)
    item_c = (REPO_ROOT / "src" / "item.c").read_text(encoding="utf-8")
    body = item_c[item_c.index("void CopyItemName("):]
    body = body[:body.index("\n}\n")]
    assert body.index("StringCopy(dest, gText_Berry);") < body.index("StringAppend(dest, GetBerryInfo(")
