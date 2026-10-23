"""Frente F da tradução (dados de Pokémon): textos da Pokédex.

Tasks F1 e F2: `src/data/pokemon/pokedex_text_fr.h` inteiro (`gDummyPokedexText` até `gDeoxysPokedexText`).
Os testes valem para as entradas já traduzidas (acrescentar o último rótulo de cada task nova em
`DEX_RANGES`): nenhum inglês, nenhum achado de `controle`/`glossario`/janela e nenhuma unidade
imperial. Modelo: `test_traducao_nomes.py`.
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct
from esteira.reflow import line_widths

REPO_ROOT = Path(__file__).resolve().parents[2]
DEX = "src/data/pokemon/pokedex_text_fr.h"

# (primeiro rótulo, último rótulo) de cada task, na ordem do arquivo
DEX_RANGES = [
    ("gDummyPokedexText", "gSunkernPokedexText"),     # F1
    ("gSunfloraPokedexText", "gDeoxysPokedexText"),   # F2
]

BS_N = chr(92) + "n"                                  # a quebra `\n` como aparece no fonte
DEX_WIDTH_PX = 30 * 8
DEX_LINES = 3
IMPERIAL = re.compile(r"\b(?:\d[\d.,]*\s*(?:p[ée]s|polegadas?|libras?|onças?|milhas?|jardas?|n[óo]s|knots?|yd|ft|lbs?|mph)|fahrenheit)\b", re.I)
# Entrada com #if/#else que a extração da checagem não lê: medida aqui (variantes inclusive)
SPECIAL = {"gChikoritaPokedexText", "gTyranitarPokedexText"}


def _source() -> str:
    return (REPO_ROOT / DEX).read_text(encoding="utf-8")


def _labels() -> list[str]:
    """Rótulos de texto (sem o `...Unused`) cobertos por `DEX_RANGES`, na ordem do arquivo."""
    all_labels = re.findall(r"^const u8 (g\w+PokedexText)\[\]", _source(), re.M)
    out: list[str] = []
    for first, last in DEX_RANGES:
        out += all_labels[all_labels.index(first):all_labels.index(last) + 1]
    return out


def _body(label: str) -> str:
    src = _source()
    start = src.index(f"const u8 {label}[]")
    return src[start:src.index(");", start)]


@pytest.fixture(scope="module")
def entries():
    wanted = set(_labels())
    return [e for e in ct._sources(REPO_ROOT)
            if isinstance(e, ct._Entry) and e.file == DEX and e.label in wanted]


def test_arquivo_inteiro_foi_extraido(entries):
    labels = _labels()
    assert len(labels) == 192 + 195                              # F1: Dummy + 191 espécies; F2: Sunflora..Deoxys
    assert labels == re.findall(r"^const u8 (g\w+PokedexText)\[\]", _source(), re.M)   # as faixas cobrem o arquivo todo
    assert {e.label for e in entries} == set(labels) - SPECIAL


def test_nenhum_ingles_sobrando_nas_entradas_traduzidas(entries):
    assert ct.english_report(str(REPO_ROOT), entries) == {}


def test_nenhuma_unidade_imperial_nas_entradas_traduzidas():
    found = [f"{label}: {m.group(0)}" for label in _labels()
             for m in [IMPERIAL.search(_body(label))] if m]
    assert found == []


def test_nada_de_caixa_alta_do_jogo_ingles(entries):
    caps = [e.label for e in entries
            if any(re.search(r"(?<![\w{])[A-Z]{3,}(?![\w}])", re.sub(r"\{[^}]*\}", "", t)) for t in e.texts)]
    assert caps == []


@lru_cache(maxsize=1)
def _results():
    if shutil.which("git") is None:
        pytest.fail("precisa do git: sem a base inglesa as regras controle/glossario não rodam")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{ct.TRANSLATION_BASE}^{{commit}}"],
                         capture_output=True)
    if out.returncode != 0:
        pytest.fail("sem o commit base da tradução: as regras controle/glossario não rodam")
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    return ct.check_text(str(REPO_ROOT), exceptions, english="desligado")


def test_base_inglesa_disponivel_nunca_passa_calado():
    unavailable = [r.detail for r in _results() if "base inglesa indisponível" in r.detail]
    assert unavailable == []


def test_sem_achado_de_regra_nas_entradas_traduzidas():
    labels = set(_labels())
    bad = []
    for r in _results():
        if r.status != "falha" or not r.name.startswith("texto/"):
            continue
        m = re.match(rf"{re.escape(DEX)}: (\w+):", r.detail)
        if m and m.group(1) in labels:
            bad.append(f"{r.name}: {r.detail}")
    assert bad == []


# Nomes de golpe, apelidos e termos de mais de uma palavra que não podem ser partidos pela quebra de linha
PROTECTED_TERMS = ["Ataque Espelhado", "Onda de Trovão", "Soco de Cometa", "Floresta Tropical Ambulante",
                   "Mach 2", "Oddium Wanderus", "Poké Bola", "Centro Pokémon", "Prof. Carvalho"]


def test_termos_compostos_nao_sao_partidos_na_quebra():
    split = []
    for label in _labels():
        text = "".join(re.findall(r'"([^"]*)"', _body(label)))     # as quebras ficam como `\n` literal
        for term in PROTECTED_TERMS:
            words = term.split(" ")
            for i in range(1, len(words)):
                if " ".join(words[:i]) + "\\n" + " ".join(words[i:]) in text:
                    split.append(f"{label}: {term}")
    assert split == []


# Valor + quebra + unidade ("cerca de 1\nkm"): a unidade sozinha no começo da linha lê mal
NUMBER_BREAK_UNIT = re.compile(
    r"(?:\d[.,]?|\b(?:um|uma|dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|cem|mil))\\n"
    r"(?:km/h|km|cm|mm|m|kg|g|°C|graus|volts|horas|anos|segundos|minutos|dias|semanas|tentáculos|toneladas"
    r"|milhões|metros|quilos)\b")


def test_valor_e_unidade_nao_sao_partidos_na_quebra():
    found = []
    for label in _labels():
        text = "".join(re.findall(r'"([^"]*)"', _body(label)))
        for m in NUMBER_BREAK_UNIT.finditer(text):
            found.append(f"{label}: ...{text[max(0, m.start() - 12):m.end() + 8]}")
    assert found == []


def test_regex_de_valor_partido_reconhece_os_casos_da_revisao():
    assert NUMBER_BREAK_UNIT.search(r"a cerca de 1\nkm de distância")
    assert NUMBER_BREAK_UNIT.search(r"mais de 95\nkm/h.")
    assert NUMBER_BREAK_UNIT.search(r"há cerca de 100\nmilhões de anos")
    assert NUMBER_BREAK_UNIT.search(r"com seus oito\ntentáculos")
    assert not NUMBER_BREAK_UNIT.search(r"a cerca de 1 km\nde distância")


def test_chikorita_cabe_nas_duas_revisoes():
    body = _body("gChikoritaPokedexText")
    lines = re.findall(r'"([^"]*)"', body)
    first = [ln for ln in lines if ln.startswith(("Suas", "Sua"))]
    assert len(first) == 2                                        # ramo REVISION == 0 e ramo #else
    common = [ln for ln in lines if ln not in first]
    for variant in first:
        texts = (variant + "".join(common)).split("\\n")
        assert len(texts) <= DEX_LINES
        assert max(line_widths(variant + "".join(common))) <= DEX_WIDTH_PX
    assert not IMPERIAL.search(body)


def test_tyranitar_cabe_nas_duas_revisoes():
    body = _body("gTyranitarPokedexText")
    branches = re.split(r"#else|#endif", body.split("#if REVISION == 0")[1])[:2]
    assert len(branches) == 2                                     # ramo REVISION == 0 e ramo #else
    for branch in branches:
        text = "".join(re.findall(r'"([^"]*)"', branch))
        assert 1 <= len(text.split(BS_N)) <= DEX_LINES
        assert max(line_widths(text)) <= DEX_WIDTH_PX
        assert not IMPERIAL.search(text)
        assert not re.search(r"\b(?:the|and|its|it)\b", text)


def test_regra_da_pokedex_continua_240px_3_linhas():
    rule = ct.rule_for(DEX, "gBulbasaurPokedexText")
    assert (rule.px, rule.lines) == (DEX_WIDTH_PX, DEX_LINES)


# Fala dirigida ao leitor (o jogador pode ser menino ou menina): frase com "você"/"te"/"lhe" sem
# particípio ou adjetivo que marque gênero ("sendo observado", "cansado").
READER = re.compile(r"\b(?:você|vocês|te|lhe)\b", re.I)
GENDERED = re.compile(r"\b\w{3,}[ai]d[oa]s?\b", re.I)


def _gendered_reader_sentences(text: str) -> list[str]:
    flat = text.replace(BS_N, " ")
    return [sent for sent in re.split(r"(?<=[.!?])\s+", flat) if READER.search(sent) and GENDERED.search(sent)]


def test_leitor_sem_genero_marcado_no_arquivo_inteiro():
    found = []
    for label in _labels():
        text = "".join(re.findall(r'"([^"]*)"', _body(label)))
        found += [f"{label}: {sent}" for sent in _gendered_reader_sentences(text)]
    assert found == []


def test_regex_do_leitor_reconhece_o_caso_da_revisao():
    assert _gendered_reader_sentences("Se você sente que está sendo observado no escuro.")
    assert not _gendered_reader_sentences("Se você sentir olhos te vigiando no escuro, é o Haunter.")
    assert not _gendered_reader_sentences("Dizem que o Pokémon, ao ser perseguido, atrai o agressor.")


# ---- Task F3: descrições de golpes e habilidades + minors da Pokédex -------------------------

MOVES_C = "src/move_descriptions.c"
ABILITIES_H = "src/data/text/abilities.h"
MOVE_DESC_PX = 15 * 8 - 7          # janela mais estreita da descrição de golpe (resumo): 113 px
MOVE_DESC_LINES = 4
ABILITY_DESC_PX = 29 * 8 - 2       # janela da habilidade no resumo: 230 px
ABILITY_DESC_CHARS = 51            # abilityDescStrBuf[52]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _move_descriptions() -> dict[str, str]:
    """rótulo -> texto cru (com as quebras `\n` literais) de cada gMoveDescription_*."""
    out = {}
    for m in re.finditer(r"const u8 (gMoveDescription_\w+)\[\] = _\((.*?)\);", _read(MOVES_C), re.S):
        out[m.group(1)] = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2)))
    return out


def _ability_descriptions() -> dict[str, str]:
    return {m.group(1): m.group(2)
            for m in re.finditer(r'static const u8 (s\w+Description)\[\] = _\("((?:[^"\\]|\\.)*)"\);', _read(ABILITIES_H))}


def _flat(text: str) -> str:
    return text.replace(BS_N, " ")


def test_golpes_e_habilidades_cobertos_por_inteiro():
    moves, abilities = _move_descriptions(), _ability_descriptions()
    assert len(moves) == 354
    assert len(abilities) == 78                       # 77 habilidades + "sem habilidade"
    pointers = re.findall(r"\[MOVE_\w+\s*-\s*1\]\s*=\s*(gMoveDescription_\w+)", _read(MOVES_C))
    assert sorted(pointers) == sorted(moves)          # nenhum golpe sem descrição


@pytest.fixture(scope="module")
def f3_entries():
    return [e for e in ct._sources(REPO_ROOT)
            if isinstance(e, ct._Entry) and e.file in (MOVES_C, ABILITIES_H)
            and (e.label.startswith("gMoveDescription_") or e.label.endswith("Description"))]


def test_f3_entradas_foram_extraidas(f3_entries):
    assert len(f3_entries) == 354 + 78


def test_f3_nenhum_ingles_sobrando(f3_entries):
    assert ct.english_report(str(REPO_ROOT), f3_entries) == {}


def test_f3_sem_achado_de_regra_nos_golpes_e_habilidades():
    bad = []
    for r in _results():
        if r.status == "falha" and r.name.startswith("texto/") and (MOVES_C in r.detail or ABILITIES_H in r.detail):
            if re.search(r"gMoveDescription_|Description", r.detail):
                bad.append(f"{r.name}: {r.detail}")
    assert bad == []


def test_descricao_de_golpe_cabe_em_4_linhas_de_113_px():
    wide, tall = [], []
    for label, text in _move_descriptions().items():
        if len(text.split(BS_N)) > MOVE_DESC_LINES:
            tall.append(label)
        if max(line_widths(text)) > MOVE_DESC_PX:
            wide.append(label)
    assert (wide, tall) == ([], [])


def test_descricao_de_habilidade_cabe_numa_linha_de_230_px_e_51_letras():
    bad = []
    for label, text in _ability_descriptions().items():
        if BS_N in text or max(line_widths(text)) > ABILITY_DESC_PX or len(text) > ABILITY_DESC_CHARS:
            bad.append(label)
    assert bad == []


def test_f3_sem_unidade_imperial_nem_caixa_alta_do_jogo_ingles():
    texts = {**_move_descriptions(), **_ability_descriptions()}
    imperial = [k for k, t in texts.items() if IMPERIAL.search(t)]
    caps = [k for k, t in texts.items() if re.search(r"(?<![\w{])[A-Z]{3,}(?![\w}])", t)]
    assert (imperial, caps) == ([], [])


# Termos que a quebra de linha não pode partir (atributos abreviados, valor + unidade, nomes de golpe citados)
F3_PROTECTED = [r"(?:Atq\.|Def\.) Esp\.", r"\d+º? (?:PS|PP|turnos?|vezes)\b", r"Centro Pokémon", r"Tela de Luz",
                r"tipos? (?:Normal|Lutador|Voador|Venenoso|Terrestre|Pedra|Inseto|Fantasma|Aço|Fogo|Água|Planta"
                r"|Elétrico|Psíquico|Gelo|Dragão|Sombrio)\b"]


def test_f3_termos_compostos_nao_sao_partidos_na_quebra():
    split = []
    for label, text in _move_descriptions().items():
        flat_break = text.replace(BS_N, "\n")
        for pattern in F3_PROTECTED:
            for m in re.finditer(pattern.replace(" ", r"[ \n]"), flat_break):
                if "\n" in m.group(0):
                    split.append(f"{label}: {m.group(0)!r}")
    assert split == []


def test_f3_nao_dirige_fala_ao_jogador():
    # descrições falam do usuário/alvo, nunca "você": sem gênero do jogador por construção
    texts = {**_move_descriptions(), **_ability_descriptions()}
    assert [k for k, t in texts.items() if re.search(r"\b(?:você|vocês|te|lhe|{PLAYER})\b", t, re.I)] == []


def test_f3_atributos_e_status_no_vocabulario_do_glossario():
    texts = {**_move_descriptions(), **_ability_descriptions()}
    old = re.compile(r"\b(?:alvo selvagem|HP|ATK|ATAQUE|DEFESA|VELOCIDADE|Ataque Esp\.|Defesa Esp\.|Atq Esp|Def Esp"
                     r"|foe|inimigo)\b")
    found = [f"{k}: {m.group(0)}" for k, t in texts.items() for m in [old.search(_flat(t))] if m]
    assert found == []


def test_golpes_citados_na_descricao_usam_o_nome_do_golpe():
    names = set(re.findall(r'_\("([^"]+)"\)', _read("src/data/text/move_names.h")))
    moves = _move_descriptions()
    cited = {"RapidSpin": ["Ligação", "Embrulho", "Sanguessuga", "Espinhos"], "BrickBreak": ["Tela de Luz", "Refletir"],
             "SpitUp": ["Acumular"], "Swallow": ["Acumular"], "MagicCoat": ["Sanguessuga"]}
    for key, wanted in cited.items():
        text = _flat(moves[f"gMoveDescription_{key}"])
        for name in wanted:
            assert name in names, name
            assert name in text, (key, name)


def test_minors_da_pokedex_herdados_da_f2():
    ho_oh = "".join(re.findall(r'"([^"]*)"', _body("gHoOhPokedexText")))
    clamperl = "".join(re.findall(r'"([^"]*)"', _body("gClamperlPokedexText")))
    camerupt = _flat("".join(re.findall(r'"([^"]*)"', _body("gCameruptPokedexText"))))
    salamence = _flat("".join(re.findall(r'"([^"]*)"', _body("gSalamencePokedexText"))))
    assert "sete" + BS_N + "cores" not in ho_oh and "sete cores" in _flat(ho_oh)
    assert "Uma" + BS_N + "vez" not in clamperl and "Uma vez na vida" in _flat(clamperl)
    assert "Se irritado" not in camerupt and "Quando irritado" in camerupt
    assert "garras que despedaçam e fogo" not in salamence
    for label in ("gHoOhPokedexText", "gClamperlPokedexText", "gCameruptPokedexText", "gSalamencePokedexText"):
        text = "".join(re.findall(r'"([^"]*)"', _body(label)))
        assert len(text.split(BS_N)) <= DEX_LINES and max(line_widths(text)) <= DEX_WIDTH_PX, label


# ---- Task F4: categorias da Pokédex, ordem "Pokémon Semente" e m/kg na tela ------------------

ENTRIES_H = "src/data/pokemon/pokedex_entries.h"
SCREEN_C = "src/pokedex_screen.c"
CATEGORY_CHARS = 11                 # categoryStr[12] e o laço `index < 11` (src/pokedex_screen.c)
STATS_WINDOW_PX = 13 * 8            # sWindowTemplate_DexEntry_SpeciesStats
FOOTPRINT_X = 88                    # pegada na mesma janela, à direita de altura/peso


def _dex_entries() -> dict[str, dict]:
    """NATIONAL_DEX_X -> {category, height, weight} de `gPokedexEntries`."""
    out = {}
    for m in re.finditer(r"\[(NATIONAL_DEX_\w+)\]\s*=\s*\{(.*?)\n    \}", _read(ENTRIES_H), re.S):
        body = m.group(2)
        out[m.group(1)] = {"category": re.search(r'\.categoryName = _\("([^"]*)"\)', body).group(1),
                           "height": int(re.search(r"\.height = (\d+)", body).group(1)),
                           "weight": int(re.search(r"\.weight = (\d+)", body).group(1))}
    return out


@pytest.fixture(scope="module")
def f4_entries():
    return [e for e in ct._sources(REPO_ROOT)
            if isinstance(e, ct._Entry) and e.file == ENTRIES_H and e.label.endswith(".categoryName")]


def test_f4_todas_as_categorias_extraidas(f4_entries):
    entries = _dex_entries()
    assert len(entries) == 387                                     # NONE + 386 espécies
    assert len(f4_entries) == len(entries)


def test_f4_categoria_cabe_em_11_letras():
    long_ = [f"{k}: {v['category']}" for k, v in _dex_entries().items() if len(v["category"]) > CATEGORY_CHARS]
    assert long_ == []


def test_f4_nenhuma_categoria_em_ingles(f4_entries):
    assert ct.english_report(str(REPO_ROOT), f4_entries) == {}
    caps = [k for k, v in _dex_entries().items() if v["category"].isupper() and v["category"] != "DNA"]
    assert caps == []                                              # caixa alta do jogo inglês ("SEED")


def test_f4_categorias_conhecidas():
    entries = _dex_entries()
    assert entries["NATIONAL_DEX_BULBASAUR"]["category"] == "Semente"
    assert entries["NATIONAL_DEX_PIKACHU"]["category"] == "Rato"
    assert entries["NATIONAL_DEX_MEW"]["category"] == "Inédito"
    assert entries["NATIONAL_DEX_TOTODILE"]["category"] == entries["NATIONAL_DEX_CROCONAW"]["category"] == "Bocarra"


def test_f4_sem_achado_de_regra_nas_categorias():
    bad = [f"{r.name}: {r.detail}" for r in _results()
           if r.status == "falha" and r.name.startswith("texto/") and ENTRIES_H in r.detail]
    assert bad == []


def test_f4_ordem_pokemon_semente_e_cabe_na_janela():
    src = _read(SCREEN_C)
    body = src[src.index("void DexScreen_PrintMonCategory"):src.index("static void DexScreen_PrintMonMeasure")]
    assert "gText_PokedexPokemon," not in body
    assert body.index("gText_PokedexPokemonPrefix") < body.index("FONT_SMALL, categoryStr")
    strings = _read("src/strings.c")
    prefix = re.search(r'gText_PokedexPokemonPrefix\[\] = _\("([^"]*)"\)', strings).group(1)
    assert prefix == "Pokémon "
    widest = max(line_widths(v["category"], "small")[0] for v in _dex_entries().values())
    unknown = line_widths("?" * CATEGORY_CHARS, "small")[0]
    assert line_widths(prefix, "small")[0] + max(widest, unknown) <= STATS_WINDOW_PX


def _dex_measure(tenths: int, unit: str) -> str:
    """Porte de DexScreen_PrintMonMeasure (src/pokedex_screen.c): 3 casas inteiras com espaço à
    esquerda, vírgula decimal, espaço e a unidade."""
    tenths = min(tenths, 9999)
    digits, output = "", False
    for divisor in (1000, 100, 10):
        digit = tenths // divisor % 10
        if digit == 0 and not output and divisor != 10:
            digits += " "
        else:
            output = True
            digits += str(digit)
    return f"{digits},{tenths % 10} {unit}"


def test_f4_conversao_metrica_casos_conhecidos():
    e = _dex_entries()
    pikachu, onix, snorlax = e["NATIONAL_DEX_PIKACHU"], e["NATIONAL_DEX_ONIX"], e["NATIONAL_DEX_SNORLAX"]
    assert _dex_measure(pikachu["height"], "m") == "  0,4 m"
    assert _dex_measure(pikachu["weight"], "kg") == "  6,0 kg"
    assert _dex_measure(onix["height"], "m") == "  8,8 m"
    assert _dex_measure(onix["weight"], "kg") == "210,0 kg"
    assert _dex_measure(snorlax["weight"], "kg") == "460,0 kg"
    assert _dex_measure(e["NATIONAL_DEX_GASTLY"]["weight"], "kg") == "  0,1 kg"
    assert _dex_measure(e["NATIONAL_DEX_WAILORD"]["height"], "m") == " 14,5 m"
    assert _dex_measure(e["NATIONAL_DEX_GROUDON"]["weight"], "kg") == "950,0 kg"
    # nenhum valor da tabela passa de 999,9: as 3 casas inteiras bastam
    assert max(max(v["height"], v["weight"]) for v in e.values()) <= 9999


def test_f4_tela_usa_metro_e_quilo_sem_conversao_imperial():
    src = _read(SCREEN_C)
    body = src[src.index("static void DexScreen_PrintMonMeasure"):src.index("void DexScreen_PrintMonFlavorText")]
    assert "gText_Meters" in body and "gText_Kg" in body and "CHAR_COMMA" in body
    for imperial in ("gText_Lbs", "4536", "254", "inches", "feet", "lbs", "CHAR_SGL_QUOTE_RIGHT", "CHAR_PERIOD"):
        assert imperial not in body, imperial
    assert "gText_Lbs" not in src
    # o valor começa em x + 30; "999,9 " são 6 casas de 5 px; a unidade termina antes da pegada
    assert "x += 30;" in body
    for unit in ("m", "kg"):
        assert 30 + 6 * 5 + line_widths(unit, "small")[0] <= FOOTPRINT_X
