"""Frente E da tradução: interface e sistema (`src/strings.c`) e a gramática montada em código
do resumo do Pokémon (task E1).

- `src/strings.c` sem inglês (créditos `gCreditsString_*` e `gJPText_*` ficam, pela lista de
  permissões da própria checagem) e sem achado das regras de texto (largura, linhas, letras,
  `controle`, `glossario`);
- memória do Treinador: "Natureza X." e o lugar com "na/no/nas/em" (PokeSum_BufferMetPlace,
  src/pokemon_summary_screen.c) cabendo na janela para toda natureza e todo lugar;
- nenhuma caixa de texto ganhou linha a mais que a versão inglesa (fora as listadas);
- as strings que a frente F usa na Pokédex (altura/peso em metros e quilos).
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
FILES = ("src/strings.c", "src/pokemon_summary_screen.c")
STRINGS_C = (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")
STRINGS_H = (REPO_ROOT / "include" / "strings.h").read_text(encoding="utf-8")
SUMMARY_C = (REPO_ROOT / "src" / "pokemon_summary_screen.c").read_text(encoding="utf-8")

# Memória do Treinador: [POKESUM_WIN_INFO_4] 28 tiles com o texto em x = 0 (6 tiles de altura,
# 3 linhas) e o buffer natureMetOrHatchedAtLevelStr[152] (src/pokemon_summary_screen.c)
MEMO_WIDTH_PX = 28 * 8
MEMO_LINES = 3
MEMO_BUFFER = 152
MET_PLACE_BUFFER = 32          # metPlaceStr[32]
MAP_NAME_BUFFER = 32           # mapNameStr[32]
MEMO_LABELS = ("MetInATrade", "FatefulEncounterMet", "Met", "ApparentlyMet", "Hatched",
               "FatefulEncounterHatched", "ApparentlyFatefulEncounterHatched")

# Caixas que ganharam uma linha de propósito (a janela comporta): rótulo -> motivo
MORE_LINES = {
    "gText_PokeSum_Met": "memória do Treinador: 3 linhas como as outras memórias (janela de 6 tiles)",
    "gText_PokeSum_Met_BoldGentleGrammar": "idem",
    "gText_CantDismountBike": "mensagem de item: caixa de 2 linhas (diálogo ou mensagem da bolsa)",
    "gText_EggCantBeTradedNow": "mensagem da troca: as vizinhas já usam 2 linhas na mesma janela",
    "gText_GiftSentTo": "mensagem do Presente Misterioso: as vizinhas já usam 2 linhas; o nome do jogador "
                        "não cabe na mesma linha medido como 10 letras largas",
}

# Placeholders variáveis ({STR_VAR_n}, {DYNAMIC n}) medidos como 10 letras largas (regra de 20/10, até
# a T3 medir os placeholders). Ficam de fora os que o C prova serem número (ConvertIntToDecimalStringN)
# e as linhas da EVOLUTION, medidas com os nomes reais em esteira/evolution_page.py.
NUMERIC_PLACEHOLDERS = {
    "gString_BattleRecords_TotalRecord": "vitórias/derrotas/empates (src/battle_records.c)",
    "gText_BerryCrush_GainedXUnitsOfPowder": "quantidades de pó (src/berry_crush.c)",
    "gText_Coins": "moedas, 4 algarismos em FONT_SMALL (src/coins.c)",
    "gText_MenuSafariStats": "passos e bolas da Safári (src/start_menu.c)",
    "gText_PokedollarVar1": "dinheiro (src/money.c)",
}
WIDE_PLACEHOLDER = "MMMMMMMMMM"

_DEF = re.compile(r'^(?:ALIGNED\(4\) )?(?:static )?const u8 (\w+)\[\] = _\("((?:[^"\\]|\\.)*)"\);', re.M)


def _strings(source: str) -> dict[str, str]:
    return dict(_DEF.findall(source))


S = _strings(STRINGS_C)


@lru_cache(maxsize=None)
def _base_strings() -> dict[str, str] | None:
    if shutil.which("git") is None:
        return None
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:src/strings.c"],
                         capture_output=True)
    return _strings(out.stdout.decode("utf-8")) if out.returncode == 0 else None


@pytest.fixture(scope="module")
def env():
    return ct._load_env(REPO_ROOT)


# --- inglês e regras da checagem ---------------------------------------------------------------

def test_nenhum_ingles_nos_arquivos_da_frente():
    report = ct.english_report(str(REPO_ROOT))
    left = {f: (c.words, c.examples) for f, c in report.items() if f in FILES}
    assert left == {}


def test_nenhum_achado_das_regras_de_texto_nos_arquivos_da_frente():
    results = ct.check_text(str(REPO_ROOT), {"text": []})
    # sem a base inglesa as regras controle/glossario não rodam: o teste não pode passar calado
    unavailable = [r.detail for r in results if "base inglesa indisponível" in r.detail]
    assert unavailable == [], unavailable
    found = [f"{r.name}: {r.detail}" for r in results
             if r.status == "falha" and any(f"{f}:" in r.detail for f in FILES)]
    assert found == []


def test_moedas_cabem_na_caixa_em_fonte_pequena(env):
    """PrintCoinsString (src/coins.c:66-76): "9999 moedas" em FONT_SMALL, alinhado à direita em 64 px
    (a regra de janelas_uso para gText_Coins mede na fonte pequena desde a E1)."""
    coins = (REPO_ROOT / "src" / "coins.c").read_text(encoding="utf-8")
    assert "AddTextPrinterParameterized(windowId, FONT_SMALL, gStringVar4, 64 - width" in coins
    assert ct.measure(S["gText_Coins"].replace("{STR_VAR_1}", "9999"), env, "small").widest <= 64


def test_creditos_e_japones_ficam():
    base = _base_strings()
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    kept = [lab for lab in base if lab.startswith(("gCreditsString_", "gJPText_"))]
    assert kept and all(S[lab] == base[lab] for lab in kept)


def test_nenhuma_caixa_ganhou_linha_a_mais():
    base = _base_strings()
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")

    def boxes(text: str) -> list[int]:
        text = text.replace("\\l", "\\n")
        return [box.count("\\n") + 1 for box in text.split("\\p") if box]

    grew = []
    for label, text in S.items():
        old = base.get(label)
        if old is None or old == text or label in MORE_LINES:
            continue
        new_boxes, old_boxes = boxes(text), boxes(old)
        if len(new_boxes) > len(old_boxes) or any(n > o for n, o in zip(new_boxes, old_boxes)):
            grew.append(f"{label}: {old_boxes} -> {new_boxes}")
        if ("\\l" in old) != ("\\l" in text):
            grew.append(f"{label}: \\l diferente da base")
    assert grew == []


def test_placeholders_medidos_como_10_letras_largas(env):
    rules = ct.effective_rules(str(REPO_ROOT))
    entries = {e.label: e.texts[0] for e in ct._extract_c_text("src/strings.c", STRINGS_C)}
    wide = []
    for (file, label), rs in sorted(rules.items()):
        text = entries.get(label)
        if (file != "src/strings.c" or text is None or label in NUMERIC_PLACEHOLDERS
                or label.startswith("gText_PokeSum_Evo")):
            continue
        if not re.search(r"\{(?:STR_VAR_\d|DYNAMIC [0-9x]+)\}", text):
            continue
        filled = re.sub(r"\{(?:STR_VAR_\d|DYNAMIC [0-9x]+)\}", WIDE_PLACEHOLDER, text)
        for rule in rs:
            if rule is not None and rule.px is not None and ct.measure(filled, env, rule.font).widest > rule.px:
                wide.append(f"{label}: {ct.measure(filled, env, rule.font).widest} > {rule.px} px")
                break
    assert wide == []


_COPY_TO_VAR = re.compile(r"(?:StringCopy|StringExpandPlaceholders|StringAppend)\(gStringVar([123])\w*,\s*(g\w+)\)")


def _string_var_sizes() -> dict[str, int]:
    """Tamanho de gStringVar1/2/3, lido de src/string_util.c."""
    text = (REPO_ROOT / "src" / "string_util.c").read_text(encoding="utf-8")
    return {n: int(size, 0) for n, size in re.findall(r"u8 gStringVar([123])\[(\w+)\]", text)}


STRING_VAR_SIZES = _string_var_sizes()


def _buffer_ctx():
    """Contexto da regra de buffer (esteira/buffers.py, Task T4) com a base inglesa; None sem a base."""
    from esteira import buffers as bf
    return bf.repo_context(str(REPO_ROOT))


def _measured_labels(ctx, buffer_prefix: str) -> dict[str, int]:
    """{rótulo de src/strings.c: menor buffer} sobre os caminhos que a regra de buffer mede."""
    from esteira import buffers as bf
    out: dict[str, int] = {}
    for path in bf.buffer_paths(ctx):
        if not path.buffer.name.startswith(buffer_prefix):
            continue
        for part in path.parts:
            for alt in bf._alts(part, ctx, path.expand):
                if alt.key and alt.key[0] == "src/strings.c":
                    out[alt.key[1]] = min(out.get(alt.key[1], 999), path.buffer.size)
    return out


def test_textos_copiados_para_gstringvar_cabem_no_buffer():
    """gStringVar2/3 têm 20 bytes: "Bolso de itens-chave" (20 letras + EOS) estourava o
    gStringVar3 pelo bufferstdstring da mensagem de item obtido e travava o jogo.

    Generalizado pela regra `buffer` da esteira (T4), que roda na checagem de texto e reprova o
    estouro (test_nenhum_achado_das_regras_de_texto_nos_arquivos_da_frente o pega em strings.c).
    Aqui fica a garantia de que a regra mede tudo o que este teste media antes: toda cópia direta
    StringCopy/StringExpandPlaceholders/StringAppend(gStringVarN, gX) e toda entrada de gStdStringPtrs."""
    ctx = _buffer_ctx()
    if ctx is None:
        pytest.skip("sem git ou sem o commit base da tradução: a regra de buffer não roda")
    measured = _measured_labels(ctx, "gStringVar")
    expected = set()
    for path in (REPO_ROOT / "src").rglob("*.c"):
        expected |= {label for _var, label in _COPY_TO_VAR.findall(path.read_text(encoding="utf-8", errors="replace"))
                     if label in S}
    menu = (REPO_ROOT / "src" / "script_menu.c").read_text(encoding="utf-8")
    std = menu[menu.index("gStdStringPtrs[] = {"):]
    expected |= set(re.findall(r"=\s*(gText_\w+)", std[:std.index("};")]))
    assert sorted(expected - set(measured)) == []
    assert measured["gText_KeyItemsPocket"] == 20
    from esteira import buffers as bf
    assert [r.detail for r in bf.check_buffers(REPO_ROOT, ctx=ctx)
            if r.status == "falha" and "src/strings.c:" in r.detail] == []


def test_texto_do_estojo_de_mt_comeca_com_str_var_1():
    """src/tm_case.c pula os 2 primeiros bytes ({STR_VAR_1}) de gText_Var1IsSelected."""
    assert S["gText_Var1IsSelected"].startswith("{STR_VAR_1}")
    assert "gText_Var1IsSelected + 2" in (REPO_ROOT / "src" / "tm_case.c").read_text(encoding="utf-8")


# Aviso de nome do mapa com andar (MapNamePopupPrintMapNameOnWindow/MapNamePopupAppendFloorNum,
# src/map_name_popup.c): u8 mapName[25] = nome + " " + ("B")N"F" ou gText_Rooftop2, sem limite de
# cópia; janela de 152 px com andar e 176 px no terraço (FLOOR_ROOFTOP = 127)
FLOOR_ROOFTOP = 127


def test_aviso_de_mapa_com_andar_cabe_no_buffer(env):
    """"Loja de Celadon Cobertura" (25 letras + EOS) estourava mapName[25] no terraço da loja.

    Os bytes contra o mapName (tamanho lido do C) são da regra `buffer` da esteira (T4,
    esteira/buffers.popup_paths, um caminho por mapa com andar, com o nome especial da Loja de
    Celadon); aqui ficam a largura da janela, que a regra não mede, e a garantia de que a regra
    cobre todos os mapas com andar."""
    from esteira import buffers as bf
    ctx = _buffer_ctx()
    if ctx is None:
        pytest.skip("sem git ou sem o commit base da tradução: a regra de buffer não roda")
    paths = bf.popup_paths(ctx)
    maps = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((REPO_ROOT / "data" / "maps").glob("*/map.json"))]
    maps = [d for d in maps if d.get("floor_number", 0) and d.get("show_map_name", True)]
    assert len(paths) == len(maps) > 0 and {p.buffer.size for p in paths} == {25}
    assert [r.detail for r in bf.check_buffers(REPO_ROOT, ctx=ctx) if r.status == "falha" and "mapName" in r.detail] == []
    sections = json.loads((REPO_ROOT / "src/data/region_map/region_map_sections.json").read_text(
        encoding="utf-8"))["map_sections"]
    names = {s["id"]: s["name"] for s in sections if s.get("name")}
    store = bf._celadon_store_maps(ctx)
    problems = []
    for data in maps:
        floor, mapsec = data["floor_number"], data["region_map_section"]
        if mapsec == "MAPSEC_CELADON_CITY" and data["id"] in store:
            mapsec = "MAPSEC_SPECIAL_AREA"          # GetMapName usa o nome especial dentro da loja
        if floor == FLOOR_ROOFTOP:
            suffix, width = S["gText_Rooftop2"], 176
        else:
            suffix, width = ("B" if floor < 0 else "") + f"{abs(floor)}F", 152
        text = f"{names[mapsec]} {suffix}"
        px = ct.measure(text, env).widest
        if px > width:
            problems.append(f"{data['name']}: '{text}' {px} px > {width}")
    assert problems == []


def _tmhm_moves() -> list[str]:
    """Golpes das MT/MO na ordem dos itens (sTMHMMoves, src/data/party_menu.h)."""
    text = (REPO_ROOT / "src/data/party_menu.h").read_text(encoding="utf-8")
    body = text[text.index("static const u16 sTMHMMoves[] ="):]
    moves = re.findall(r"\b(MOVE_\w+)", body[:body.index("};")])
    names = dict(re.findall(r'\[(MOVE_\w+)\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)',
                            (REPO_ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8")))
    return [names[m] for m in moves]


TM_CASE_SELECTED_PX = 15 * 8      # WIN_SELECTED_MSG .width = 15 (src/tm_case.c:263-271), x = 0


def test_mt_selecionada_cabe_no_estojo(env):
    """tm_case.c monta "{FONT_SMALL}Nº01 {FONT_NORMAL}<golpe>" (GetTMNumberAndMoveString) e anexa
    gText_Var1IsSelected sem o {STR_VAR_1}; a 1ª linha cabe na janela de 120 px para toda MT/MO."""
    tail = S["gText_Var1IsSelected"][len("{STR_VAR_1}"):]
    moves = _tmhm_moves()
    assert len(moves) == 58
    wide = []
    for i, move in enumerate(moves):
        number = f"{i + 1:02d}" if i < 50 else "{CLEAR_TO 18}" + S["gText_NumberClear01"] + str(i - 49)
        if i < 50:
            number = S["gText_NumberClear01"] + number
        text = "{FONT_SMALL}" + number + " {FONT_NORMAL}" + move + tail
        px = ct.measure(text, env).widest
        if px > TM_CASE_SELECTED_PX:
            wide.append(f"{move}: {px} px")
    assert wide == []


# --- memória do Treinador: "Natureza X." e o lugar com a preposição -----------------------------

def _word_lists() -> list[tuple[list[str], str]]:
    return [(S[f"gText_PokeSum_PlaceWords{kind}"].split("\\n"), S[f"gText_PokeSum_PlaceIn{kind}"])
            for kind in ("Fem", "Masc", "FemPlural")]


def met_place(place: str) -> str:
    """Espelho de PokeSum_BufferMetPlace: a preposição sai da 1ª palavra do lugar."""
    first = place.split(" ")[0]
    for words, preposition in _word_lists():
        if first in words:
            return preposition + place
    return S["gText_PokeSum_PlaceIn"] + place


def _kanto_sevii_places() -> list[str]:
    sections = json.loads((REPO_ROOT / "src/data/region_map/region_map_sections.json").read_text(
        encoding="utf-8"))["map_sections"]
    ids = [s["id"] for s in sections]
    start = ids.index("MAPSEC_PALLET_TOWN")
    return sorted({s["name"] for s in sections[start:] if s.get("name")})


def _natures() -> list[str]:
    text = (REPO_ROOT / "src/data/text/nature_names.h").read_text(encoding="utf-8")
    return re.findall(r's\w+NatureName\[\] = _\("([^"]*)"\)', text)


def test_preposicao_do_lugar():
    assert met_place("Rota 1") == "na Rota 1"
    assert met_place("Monte Lua") == "no Monte Lua"
    assert met_place("Ilhas Seafoam") == "nas Ilhas Seafoam"
    assert met_place("Ilha Um") == "na Ilha Um"
    assert met_place("S.S. Anne") == "no S.S. Anne"
    assert met_place("Câmaras de Tanoby") == "nas Câmaras de Tanoby"
    assert met_place(S["gText_PokeSum_ATrade"]) == "em uma troca"
    assert met_place(S["gText_Somewhere"]) == "em algum lugar"


def test_todo_lugar_de_kanto_e_sevii_tem_preposicao_propria():
    """Nenhum lugar cai no "em" genérico: a 1ª palavra de cada nome está numa das listas, e
    nenhuma palavra está em duas listas."""
    words = [w for ws, _ in _word_lists() for w in ws]
    assert len(words) == len(set(words))
    plain = [p for p in _kanto_sevii_places() if met_place(p).startswith(S["gText_PokeSum_PlaceIn"])]
    assert plain == []


def test_memoria_usa_natureza_x_e_variantes_iguais():
    for name in MEMO_LABELS:
        text = S[f"gText_PokeSum_{name}"]
        assert text.startswith("Natureza {DYNAMIC 0x00}."), name
        assert S[f"gText_PokeSum_{name}_BoldGentleGrammar"] == text, name
    assert len(_natures()) == 25


def test_memoria_cabe_na_janela_para_toda_natureza_e_lugar(env):
    places = [met_place(p) for p in _kanto_sevii_places()]
    places += [met_place(S["gText_PokeSum_ATrade"]), met_place(S["gText_Somewhere"])]
    assert all(ct.measure(p, env).nbytes < MET_PLACE_BUFFER for p in places)
    assert all(ct.measure(p, env).nbytes < MAP_NAME_BUFFER for p in _kanto_sevii_places())
    problems = []
    for name in MEMO_LABELS:
        template = S[f"gText_PokeSum_{name}"]
        for nature in _natures():
            for place in places:
                text = (template.replace("{DYNAMIC 0x00}", nature).replace("{DYNAMIC 0x01}", "100")
                        .replace("{DYNAMIC 0x02}", place))
                m = ct.measure(text, env)
                if m.widest > MEMO_WIDTH_PX or m.lines > MEMO_LINES or m.nbytes >= MEMO_BUFFER:
                    problems.append(f"{name}/{nature}/{place}: {m.widest} px, {m.lines} linhas, {m.nbytes} bytes")
    assert problems[:5] == []


def test_codigo_monta_o_lugar_com_a_preposicao():
    """As duas memórias (Treinador original ou não) passam o lugar por PokeSum_BufferMetPlace, e
    a função testa as listas na ordem do espelho."""
    assert SUMMARY_C.count("DynamicPlaceholderTextUtil_SetPlaceholderPtr(2, PokeSum_BufferMetPlace(metPlaceStr, "
                           "mapNameStr));") == 2
    body = SUMMARY_C[SUMMARY_C.index("u8 *PokeSum_BufferMetPlace(u8 *dest, const u8 *place)\n{"):]
    body = body[:body.index("\n}\n")]
    order = re.findall(r"gText_PokeSum_PlaceWords(\w+)", body)
    assert order == ["Fem", "Masc", "FemPlural"]
    assert "preposition = gText_PokeSum_PlaceIn;" in body
    assert "u8 *PokeSum_BufferMetPlace(u8 *dest, const u8 *place);" in (
        REPO_ROOT / "include" / "pokemon_summary_screen.h").read_text(encoding="utf-8")


# --- páginas EVOLUTION e IVs/EVs -------------------------------------------------------------

def test_poder_oculto_da_pagina_e_o_nome_do_golpe():
    moves = (REPO_ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8")
    assert re.search(r'\[MOVE_HIDDEN_POWER\]\s*=\s*_\("([^"]*)"\)', moves).group(1) == S["gText_PokeSum_HiddenPower"]


def test_nomes_das_paginas_do_resumo():
    assert [S[f"gText_PokeSum_PageName_{p}"] for p in ("PokemonInfo", "PokemonSkills", "KnownMoves",
                                                       "Evolution", "IvsEvs")] == [
        "Dados", "Atributos", "Golpes", "Evolução", "IVs/EVs"]


# --- strings que a frente F usa na Pokédex --------------------------------------------------------

def test_strings_de_altura_e_peso_para_a_frente_f():
    assert (S["gText_HT"], S["gText_WT"], S["gText_Meters"], S["gText_Kg"]) == ("Alt.", "Peso", "m", "kg")
    assert S["gText_PokedexPokemonPrefix"] == "Pokémon "
    for label in ("gText_HT", "gText_WT", "gText_Meters", "gText_Kg", "gText_PokedexPokemonPrefix"):
        assert f"extern const u8 {label}[];" in STRINGS_H


# =====================================================================================================
# Task E2: textos gerais (data/text) e scripts compartilhados (data/scripts, event_scripts.s,
# mystery_event_msg.s)
# =====================================================================================================

E2_TEXT = ("aide", "berries", "competitive_brothers", "day_care", "eon_ticket", "flavor_text", "ingame_trade",
           "itemfinder", "new_game_intro", "obtain_item", "pc", "pc_transfer", "poke_mart", "pokedex_rating",
           "pokedude", "route23", "safari_zone", "save", "seagallop", "sign_lady", "surf", "trainer_card",
           "white_out")
E2_FILES = ([f"data/text/{n}.inc" for n in E2_TEXT]
            + sorted(f"data/scripts/{p.name}" for p in (REPO_ROOT / "data" / "scripts").glob("*.inc"))
            + ["data/event_scripts.s", "data/mystery_event_msg.s"])
BS_N, BS_L, BS_P = "\\n", "\\l", "\\p"


def _e2_blocks(text: str) -> dict[str, str]:
    """Rótulo -> texto inteiro (as linhas .string coladas), como o jogo monta."""
    out = {}
    for m in re.finditer(r'^(\w+)::?\n((?:[ \t]+\.string ".*"\n?)+)', text, re.M):
        out[m.group(1)] = "".join(re.findall(r'\.string "(.*)"', m.group(2)))
    return out


def _e2_base(rel: str) -> str | None:
    if shutil.which("git") is None:
        return None
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    return out.stdout.decode("utf-8") if out.returncode == 0 else None


def test_e2_nenhum_ingles_nos_arquivos_da_frente():
    report = ct.english_report(str(REPO_ROOT))
    assert {f: (c.words, c.examples) for f, c in report.items() if f in E2_FILES} == {}


def test_e2_nenhum_achado_das_regras_de_texto():
    """largura, linhas, letras, charmap, terminador, controle e glossário nos arquivos da E2; sem a base
    inglesa as regras controle/glossario não rodam, então o teste não pode passar calado."""
    results = ct.check_text(str(REPO_ROOT), {"text": []}, english="desligado")
    unavailable = [r.detail for r in results if "base inglesa indisponível" in r.detail]
    assert unavailable == [], unavailable
    found = [f"{r.name}: {r.detail}" for r in results
             if r.status != "ok" and any(f"{f}:" in r.detail for f in E2_FILES)]
    assert found == []


@pytest.mark.parametrize("rel", E2_FILES)
def test_e2_rotulos_e_fim_de_arquivo_iguais_aos_da_base(rel):
    base = _e2_base(rel)
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    now = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert re.findall(r"^(\w+)::?\s*$", now, re.M) == re.findall(r"^(\w+)::?\s*$", base, re.M)
    assert len(now) - len(now.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


# Termos de duas ou mais palavras que não podem ser partidos na quebra (\n ou \l no lugar do espaço);
# o glossário de máquina entra todo, menos as frases ("Salvando… Não desligue o aparelho.").
E2_NAMES_NOT_SPLIT = (
    "Prof. Carvalho", "Hall da Fama", "Dicas de Treinador", "Dono da Creche", "Dona da Creche", "Cara Pokémon",
    "Cartão Maravilha", "Adaptador Sem Fio", "Comunicação Sem Fio", "Esmaga Frutas", "Pulo Pokémon",
    "Colheita do Dodrio", "Presente Misterioso", "Cartão de Selos", "Cartão Contador de Batalhas",
    "Cápsula do Tempo", "Centro de Trocas", "Clube Cabo Pokémon", "Clube Sem Fio Pokémon", "Sala União",
    "Porto Vermilion", "Cidade Vermilion", "Caverna Mutante", "Ilha Proscrita", "Ilhas Sevii", "Zona de Safári",
    "Jogo do Safári", "Bolas Safári", "Poké Bola", "Poké Bolas", "Poké Mart", "Moeda Amuleto", "Detector de Itens",
    "Amuleto Brilhante", "Chicote de Vinha", "Compart. Exp.", "problema de status", "Liga Pokémon", "Platô Índigo",
    "Mapa da Cidade", "Impressora Pokémon", "Adesivo do Hall da Fama", "Adesivo do Ovo", "Adesivo da Vitória",
    "Pokédex Nacional", "Professor Pokémon", "Líder do grupo", "Batalha simples", "Batalha dupla",
    "Batalha múltipla", "Cartão de Treinador", "Cartão-chave", "Centro Pokémon", "Canto Direto", "Equipe Rocket",
    "Sistema de Armazenamento de Pokémon", "Seagallop Hi-Speed", "Bolso Itens-chave", "Estojo de MT")


@lru_cache(maxsize=None)
def _e2_terms() -> tuple[str, ...]:
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    names = {t["pt"] for t in data["termos"]
             if " " in t["pt"] and t["categoria"] != "golpe" and "…" not in t["pt"]
             and not t["pt"].endswith(("!", "?")) and len(t["pt"].split(" ")) <= 5}
    names |= set(E2_NAMES_NOT_SPLIT)
    plurals = set()
    for name in names:       # "Centros Pokémon", "Insígnias Rocha": plural simples na última palavra de cada trecho
        words = name.split(" ")
        for j, w in enumerate(words):
            if w[-1:].isalpha() and not w.endswith("s"):
                plurals.add(" ".join(words[:j] + [w + "s"] + words[j + 1:]))
    return tuple(sorted(names | plurals))


@pytest.mark.parametrize("rel", E2_FILES)
def test_e2_nomes_nao_sao_partidos_na_quebra(rel):
    found = []
    for label, body in _e2_blocks((REPO_ROOT / rel).read_text(encoding="utf-8")).items():
        for name in _e2_terms():
            for i, ch in enumerate(name):
                if ch == " " and any(name[:i] + br + name[i + 1:] in body for br in (BS_N, BS_L)):
                    found.append(f"{label}: {name}")
    assert found == []


# Jogador sem gênero marcado (regra de 20/10): nada de adjetivo/vocativo marcado dirigido a ele
E2_PLAYER_GENDERED = ("Bem-vindo", "Bem-vinda", "bem-vindo", "bem-vinda", "Seja bem", "você é bom", "Você é bom",
                      "ganancioso", "Fique quieto", "desafiado", "desafiada", "protagonista é")


@pytest.mark.parametrize("rel", E2_FILES)
def test_e2_jogador_sem_genero_e_sem_formas_erradas(rel):
    body = "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / rel).read_text(encoding="utf-8")))
    for bad in E2_PLAYER_GENDERED + ("Poké BolaS", "Equipe Rocket Grunt", "Clube do Cabo", "Wireless", "Game Link cable"):
        assert bad not in body, (rel, bad)


def test_e2_termos_novos_registrados_no_glossario():
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    created = {t["en"]: t for t in data["termos"] if t.get("frente") == "E" and t["fonte"] == "criado"}
    expected = {"DAY-CARE MAN": ("Dono da Creche", "day_care"), "DAY-CARE LADY": ("Dona da Creche", "day_care"),
                "POKé DUDE": ("Cara Pokémon", "pokedude"), "STICKER": ("adesivo", "trainer_card"),
                "HALL OF FAME STICKER": ("Adesivo do Hall da Fama", "trainer_card"),
                "EGG STICKER": ("Adesivo do Ovo", "trainer_card"),
                "VICTORY STICKER": ("Adesivo da Vitória", "trainer_card"),
                "POKéMON CABLE CLUB": ("Clube Cabo Pokémon", "event_scripts"),
                "TIME CAPSULE": ("Cápsula do Tempo", "event_scripts"),
                "POKéMON PRINTER": ("Impressora Pokémon", "trainer_card"),
                "STAMP CARD": ("Cartão de Selos", "mystery_event_msg"),
                "BATTLE COUNT CARD": ("Cartão Contador de Batalhas", "mystery_event_msg")}
    for en, (pt, where) in expected.items():
        assert created[en]["pt"] == pt, en
        path = next(f for f in E2_FILES if f.endswith(f"/{where}.inc") or f.endswith(f"/{where}.s"))
        assert pt.lower() in (REPO_ROOT / path).read_text(encoding="utf-8").lower(), (en, path)


# --- buffers que os scripts enchem (trava o jogo se passar do tamanho) ---------------------------------

def _e2_item_names() -> list[str]:
    items = json.loads((REPO_ROOT / "src" / "data" / "items.json").read_text(encoding="utf-8"))["items"]
    return [i["english"] for i in items]


def test_e2_nome_de_item_com_plural_cabe_em_gstringvar():
    """bufferitemname/bufferitemnameplural (obtain_item.inc, event_scripts.s) copiam o nome do item para
    STR_VAR_1/2; com o plural ("Poké Bolas", "Frutas Cheri") continua em até 19 letras."""
    scrcmd = (REPO_ROOT / "src" / "scrcmd.c").read_text(encoding="utf-8")
    body = scrcmd[scrcmd.index("bool8 ScrCmd_bufferitemnameplural"):]
    body = body[:body.index("\n}\n")]
    assert 'sText_S[] = _("s")' in scrcmd and '_("IES")' not in scrcmd     # plural em português, não "S"/"IES"
    assert "StringAppend(sScriptStringVars[stringVarIndex], sText_S);" in body       # Poké Bolas
    assert "BufferBerryNamePlural(sScriptStringVars[stringVarIndex]);" in body       # Frutas X (src/item.c)
    names = _e2_item_names()
    assert len(names) > 300
    plural = []
    for name in names:
        assert len(name) <= 13                                              # ITEM_NAME_LENGTH 14 com o fim
        if name == "Poké Bola":
            plural.append(name + "s")
        elif name.startswith("Fruta "):
            first, _, rest = name.partition(" ")
            plural.append(first + "s " + rest)
    assert "Poké Bolas" in plural and "Frutas Cheri" in plural and len(plural) >= 40
    env = ct._load_env(REPO_ROOT)
    assert all(ct.measure(p, env).nbytes + 1 <= STRING_VAR_SIZES["2"] for p in plural + names)


def test_e2_outros_textos_que_vao_para_buffers_cabem():
    env = ct._load_env(REPO_ROOT)
    sizes = STRING_VAR_SIZES
    moves = re.findall(r'\[MOVE_\w+\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)',
                       (REPO_ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8"))
    assert moves and all(ct.measure(m, env).nbytes + 1 <= sizes["2"] for m in moves)       # buffermovename STR_VAR_2
    for label in ("gText_BronzeCard", "gText_CopperCard", "gText_SilverCard", "gText_GoldCard", "gText_Coins_2"):
        assert ct.measure(S[label], env).nbytes + 1 <= sizes["2"], label                   # cor do cartão, moedas
    storage = (REPO_ROOT / "include" / "pokemon_storage_system.h").read_text(encoding="utf-8")
    assert "#define BOX_NAME_LENGTH         8" in storage                                  # bufferboxname STR_VAR_1/3
    # nome padrão da caixa = gText_Box + 2 algarismos (src/pokemon_storage_system_menu.c:415-416), guardado em
    # boxNames[BOX_NAME_LENGTH + 1] e copiado para STR_VAR_1/3
    assert ct.measure(S["gText_Box"], env).nbytes + 2 + 1 <= 8 + 1 <= sizes["2"]


# --- caixa de diálogo padrão: 2 linhas visíveis -----------------------------------------------------

# Janela padrão = 4 tiles de altura (src/new_menu_helpers.c:36-44) = 2 linhas; a 3ª só aparece se for aberta
# com \l (rolagem). Um \n depois de \l ou 2 \n na mesma caixa cai fora da janela. Páginas de texto corrido
# (guia de controles, páginas do Pikachu) têm janela própria.
E2_OWN_WINDOW = ("gControlsGuide_Text_", "gPikachuIntro_Text_")


def test_e2_nenhuma_caixa_de_dialogo_com_mais_de_2_linhas_visiveis():
    problems = []
    for rel in E2_FILES:
        for label, body in _e2_blocks((REPO_ROOT / rel).read_text(encoding="utf-8")).items():
            if label.startswith(E2_OWN_WINDOW) or re.search(r"[　-鿿]", body):
                continue
            for box in body.rstrip("$").split(BS_P):
                if box.count(BS_N) > 1 or re.search(re.escape(BS_L) + r"[^\\]*" + re.escape(BS_N), box):
                    problems.append(f"{rel}:{label}: {box[:60]}")
    assert problems == []


# Texto de batalha (Cara Pokémon, src/battle_controller_pokedude.c) e mensagens de caixa (battle_message.c)
# vão para gDisplayedStringBattle[300] (src/battle_main.c:123)
BATTLE_STRING_BUFFER = 300


def test_e2_textos_que_vao_para_gdisplayedstringbattle_cabem(env):
    battle = (REPO_ROOT / "src" / "battle_main.c").read_text(encoding="utf-8")
    assert f"gDisplayedStringBattle[{BATTLE_STRING_BUFFER}]" in battle
    blocks = _e2_blocks((REPO_ROOT / "data/text/pokedude.inc").read_text(encoding="utf-8"))
    blocks.update({k: v for k, v in _e2_blocks((REPO_ROOT / "data/text/pc_transfer.inc").read_text(
        encoding="utf-8")).items() if k.startswith("Text_MonSentToBox")})
    assert len(blocks) > 20
    over = {k: ct.measure(v, env).nbytes + 1 for k, v in blocks.items() if ct.measure(v, env).nbytes + 1 > BATTLE_STRING_BUFFER}
    assert over == {}


# Particípio/adjetivo dirigido ao jogador (regra de 20/10): "será acompanhado", "foi convidado"...
E2_PLAYER_PARTICIPLE = re.compile(r"\bVocê (?:será|foi|está|ficou|vai ser|fica) (?:\w+(?:ado|ido|ada|ida)|bom|ótimo|esperto|forte)\b")


@pytest.mark.parametrize("rel", E2_FILES)
def test_e2_sem_participio_marcado_dirigido_ao_jogador(rel):
    body = "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / rel).read_text(encoding="utf-8")))
    body = re.sub(r"\\[nlp]", " ", body)
    assert E2_PLAYER_PARTICIPLE.findall(body) == []


# --- janelas de linhas fixas -----------------------------------------------------------------------

# Guia de controles do Carvalho (src/oak_speech.c:178-277): janelas de 4 tiles de altura = 2 linhas e de
# 6 tiles = 3 linhas (a regra de largura da esteira não limita linhas)
E2_GUIDE_LINES = {"Intro": 2, "DPad": 3, "AButton": 2, "BButton": 2, "StartButton": 2, "SelectButton": 2,
                  "LRButtons": 3}


def test_e2_guia_de_controles_cabe_nas_janelas():
    blocks = _e2_blocks((REPO_ROOT / "data/text/new_game_intro.inc").read_text(encoding="utf-8"))
    oak = (REPO_ROOT / "src" / "oak_speech.c").read_text(encoding="utf-8")
    assert oak.count(".height = 4,") >= 5 and oak.count(".height = 6,") >= 2
    for name, lines in E2_GUIDE_LINES.items():
        text = blocks[f"gControlsGuide_Text_{name}"]
        assert BS_L not in text and text.count(BS_N) + 1 <= lines, name


def test_e2_paginas_do_pikachu_tem_o_mesmo_numero_de_linhas_da_base():
    base = _e2_blocks(_e2_base("data/text/new_game_intro.inc") or "")
    if not base:
        pytest.skip("sem git ou sem o commit base da tradução")
    now = _e2_blocks((REPO_ROOT / "data/text/new_game_intro.inc").read_text(encoding="utf-8"))
    for page in (1, 2, 3):
        label = f"gPikachuIntro_Text_Page{page}"
        assert now[label].count(BS_N) <= base[label].count(BS_N), label


# --- mensagens do Presente Misterioso (mystery_event_msg.s): cada script cabe nos 995 bytes da RAM ---------

def test_e2_scripts_do_presente_misterioso_cabem_em_995_bytes(env):
    """struct RamScriptData.script[995] (include/global.h): o tamanho de cada MysteryEventScript_* (texto +
    comandos) tem de caber; aqui conta só o texto traduzido de cada bloco, com folga de 200 bytes para os
    comandos (os maiores comandos do arquivo somam menos de 120)."""
    src = (REPO_ROOT / "data/mystery_event_msg.s").read_text(encoding="utf-8")
    assert "u8 script[995];" in (REPO_ROOT / "include" / "global.h").read_text(encoding="utf-8")
    parts = re.split(r"^(MysteryEventScript_\w+)::", src, flags=re.M)
    assert len(parts) > 6
    sizes = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        total = 0
        for text in _e2_blocks(body.replace("\n\n", "\n") + "\n").values():
            total += ct.measure(text, env).nbytes + 1
        sizes[name] = total
    assert max(sizes.values()) + 200 <= 995, sizes


# =====================================================================================================
# Task E3: resíduos de interface (Union Room, Quest Log, TV Educativa, Presente/Evento Misterioso), plural
# montado em código (Pulo Pokémon), glifo {LV}/{LV_2} -> "Nv" e limpeza de strings.c
# =====================================================================================================

E3_FILES = ("src/union_room_message.c", "src/data/text/quest_log.h", "src/data/text/teachy_tv.h",
            "src/mystery_event_msg.c", "src/mystery_gift_scripts.c", "src/pokemon_jump.c")
# mensagens de depuração que ficam em inglês (nunca aparecem num jogo normal)
E3_DEBUG_ENGLISH = {"src/sprite.c": "sDmaOverErrorMsg", "src/battle_anim_status_effects.c": "sText_TaskOver"}


def _c_entries(rel: str) -> dict[str, str]:
    """Rótulo -> texto cru (como no fonte) de cada _("...") do arquivo C."""
    source = (REPO_ROOT / rel).read_text(encoding="utf-8")
    return {e.label: e.texts[0] for e in ct._extract_c_text(rel, source)}


def _c_base(rel: str) -> dict[str, str] | None:
    base = _e2_base(rel)
    return None if base is None else {e.label: e.texts[0] for e in ct._extract_c_text(rel, base)}


QL = _c_entries("src/data/text/quest_log.h")
UR = _c_entries("src/union_room_message.c")
TV = _c_entries("src/data/text/teachy_tv.h")


def test_e3_nenhum_ingles_nos_arquivos_da_frente():
    report = ct.english_report(str(REPO_ROOT))
    assert {f: (c.words, c.examples) for f, c in report.items() if f in E3_FILES} == {}


def test_e3_mensagens_de_depuracao_ficam_em_ingles():
    """Únicas exceções do --ingles da E3: texto de depuração que o jogo não mostra ao jogador."""
    report = ct.english_report(str(REPO_ROOT))
    for rel, label in E3_DEBUG_ENGLISH.items():
        assert rel in report and set(report[rel].examples) == {label}, rel
        base = _c_base(rel)
        if base is not None:
            assert _c_entries(rel)[label] == base[label]


def test_e3_nenhum_achado_das_regras_de_texto():
    """largura, linhas, letras, charmap, controle, glossário e buffer nos arquivos da E3 (e no braille, E4);
    sem a base inglesa as regras controle/glossario não rodam, então o teste não pode passar calado."""
    results = ct.check_text(str(REPO_ROOT), {"text": []}, english="desligado")
    unavailable = [r.detail for r in results if "base inglesa indisponível" in r.detail]
    assert unavailable == [], unavailable
    found = [f"{r.name}: {r.detail}" for r in results
             if r.status != "ok" and any(f"{f}:" in r.detail for f in E3_FILES + ("data/text/braille.inc",))]
    assert found == []


@pytest.mark.parametrize("rel", E3_FILES[:5])
def test_e3_rotulos_iguais_aos_da_base(rel):
    base = _c_base(rel)
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    assert list(_c_entries(rel)) == list(base)


E3_NAMES_NOT_SPLIT = ("Mural de Trocas", "Troca de Ovo", "Cartão Maravilha", "Cartões Maravilha", "Notícias Maravilha",
                      "Comunicação Sem Fio", "Cartão de Treinador", "Cartões de Treinador", "Show do Cara Pokémon",
                      "Líder de Ginásio", "Elite Quatro", "Bolso Itens", "Bolso Itens-chave", "Corda de Fuga",
                      "golpe oculto", "Estojo de MT", "Cassino Rocket", "Centro Pokémon", "Poké Mart", "Sala União",
                      "TV Educativa", "Batalha simples", "batalha simples", "batalha dupla", "batalha múltipla",
                      "Laboratório de Pesquisa Pokémon", "Prof. Carvalho", "Zona de Safári", "Esmaga Frutas",
                      "Colheita do Dodrio", "Pulo Pokémon", "Fruta Enigma")


@pytest.mark.parametrize("rel", E3_FILES[:5])
def test_e3_nomes_nao_sao_partidos_na_quebra(rel):
    found = []
    names = set(_e2_terms()) | set(E3_NAMES_NOT_SPLIT)
    for label, body in _c_entries(rel).items():
        for name in names:
            for i, ch in enumerate(name):
                if ch == " " and any(name[:i] + br + name[i + 1:] in body for br in (BS_N, BS_L)):
                    found.append(f"{label}: {name}")
    assert found == []


# Jogador sem gênero marcado (regras de 20/10 e 21/10)
E3_PLAYER_GENDERED = E2_PLAYER_GENDERED + ("Seu ", "Ora, seu", "amigo,", "Amigo,", "cara,", "Cara,", "o protagonista",
                                           "o personagem principal", "vocês todos", "Obrigado por", "Bem-vindo")
_COPULA = r"(?:é|está|estava|era|foi|ser|estar|ficar|fica|ficou|parece|estiver|for|seja)"
_INTENSIFIERS = r"(?:muito|bem|tão|mais|menos|meio|bastante|realmente|sempre)"
E3_GENDERED_ADJ = re.compile(
    rf"(?<!\w)(?:[Vv]ocê|{{PLAYER}})\s+(?:não\s+)?{_COPULA}\s+(?:{_INTENSIFIERS}\s+)?"
    rf"(?!{_INTENSIFIERS}\b)(?!\w*ndo\b)(\w{{3,}}(?:o|ado|ido|oso|udo))\b")


def _flat_c(rel: str) -> str:
    """Todos os textos do arquivo numa linha só: quebras viram espaço antes de procurar os padrões."""
    body = " ".join(_c_entries(rel).values())
    body = re.sub(r"\{[^}]*\}", lambda m: "{PLAYER}" if m.group(0) == "{PLAYER}" else " ", body)
    return re.sub(r"\\[nlp]", " ", body)


@pytest.mark.parametrize("rel", E3_FILES[:5])
def test_e3_jogador_sem_genero(rel):
    body = _flat_c(rel)
    assert [b for b in E3_PLAYER_GENDERED if b in body] == []
    assert [m.group(0) for m in E3_GENDERED_ADJ.finditer(body)] == []
    assert E2_PLAYER_PARTICIPLE.findall(body) == []


def test_e3_termos_novos_registrados_no_glossario():
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    created = {t["en"]: t["pt"] for t in data["termos"] if t.get("frente") == "E" and t["fonte"] == "criado"}
    expected = {"TRADING BOARD": ("Mural de Trocas", UR), "EGG TRADE": ("Troca de Ovo", UR),
                "GREETINGS (menu da Sala União)": ("Saudação", UR), "POKé DUDE SHOW": ("Show do Cara Pokémon", TV),
                "ROCKET GAME CORNER": ("Cassino Rocket", QL), "NAME RATER'S HOUSE": ("Casa do Avaliador", QL),
                "POKéMON LEAGUE GATE": ("Portão da Liga", QL), "OAK RESEARCH LAB": ("Lab. do Carvalho", QL),
                "PEWTER MUSEUM OF SCIENCE (Quest Log)": ("Museu de Ciências", QL),
                "VOLUNTEER HOUSE (Quest Log)": ("Casa de Voluntários", QL),
                "BILL'S HOUSE": ("Casa do Bill", QL), "POKéMON FAN CLUB": ("Fã-clube Pokémon", QL)}
    for en, (pt, texts) in expected.items():
        assert created.get(en) == pt, en
        assert any(pt in t.replace(BS_N, " ").replace(BS_L, " ") for t in texts.values()), en
    # RIBBON é termo da G3 (Easy Chat), registrado uma vez só; o Presente Misterioso usa o mesmo "Fita"
    ribbon = [t for t in data["termos"] if t["en"] == "RIBBON"]
    assert [t["pt"] for t in ribbon] == ["Fita"] and "mystery_event_msg.c" in ribbon[0]["obs"]
    assert any("Fita" in t for t in _c_entries("src/mystery_event_msg.c").values())


def test_e3_cara_pokemon_na_tv_educativa():
    body = " ".join(TV.values())
    assert "Cara Pokémon" in body and "Show do Cara Pokémon" in body
    assert not re.search(r"Pok[ée] ?Dude|POKé DUDE", body)


# --- Quest Log: medida com os nomes reais (a checagem mede todo placeholder como 10 letras, e os nomes de
# lugar chegam a 18-20 letras) -------------------------------------------------------------------------------

QL_WIDTH = 30 * 8 - 2          # DESC_WIN_WIDTH 30 tiles, texto em x = 2 (src/quest_log.c:40, :1039)
QL_LINES = 3                   # DESC_WIN_HEIGHT 6 tiles: 3 linhas (sQuestLogTextLineYCoords, src/quest_log.c)
QL_BUILDINGS = ("Home", "OakResearchLab", "Gym", "PokemonLeagueGate", "ViridianForest", "PewterMuseumOfScience",
                "MtMoon", "BikeShop", "BillsHouse", "DayCare", "UndergroundPath", "PokemonFanClub", "SSAnne",
                "DiglettsCave", "RockTunnel", "PowerPlant", "PokemonTower", "VolunteerHouse", "NameRatersHouse",
                "CeladonDeptStore", "CeladonMansion", "RocketGameCorner", "Restaurant", "RocketHideout",
                "SafariZone", "WardensHome", "FightingDojo", "SilphCo", "SeafoamIslands", "PokemonMansion",
                "PokemonResearchLab", "VictoryRoad", "PokemonLeague", "CeruleanCave")


def _names(rel: str, pattern: str) -> list[str]:
    return re.findall(pattern, (REPO_ROOT / rel).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _widest() -> dict[str, str]:
    """Pior caso real de cada tipo de conteúdo (o nome mais largo na fonte normal)."""
    env = ct._load_env(REPO_ROOT)
    sections = json.loads((REPO_ROOT / "src/data/region_map/region_map_sections.json").read_text(encoding="utf-8"))
    lists = {
        "map": [s["name"] for s in sections["map_sections"] if s.get("name")],
        "building": [QL[f"gText_QuestLog_{n}"] for n in QL_BUILDINGS],
        "mon": _names("src/data/text/species_names.h", r'\[SPECIES_\w+\] = _\("([^"]*)"\)')[1:],
        "item": _e2_item_names(),
        "move": _names("src/data/text/move_names.h", r'\[MOVE_\w+\]\s*=\s*_\("([^"]*)"\)'),
        "trainer": [n for n in _names("src/data/trainers.h", r'\.trainerName = _\("([^"]*)"\)') if n],
        "player": ["MMMMMMM"],                     # PLAYER_NAME_LENGTH 7, a letra mais larga
        "box": ["MMMMMMMM"],                       # BOX_NAME_LENGTH 8
        "outcome": [QL["gText_QuestLog_Win"], QL["gText_QuestLog_Loss"], QL["gText_QuestLog_Draw"]],
        "adverb": [QL[f"gText_QuestLog_{n}"] for n in ("Handily", "Tenaciously", "Somehow")],
        "champion_adverb": [QL[f"gText_QuestLog_{n}"] for n in ("Coolly", "Somehow", "Barely")],
        "count": [QL["gText_QuestLog_JustOne"], QL["gText_QuestLog_Num"].replace("{DYNAMIC 0x04}", "888")],
        "spot": [QL["gText_QuestLog_ADifferentSpot"], "MMMMMMMM"],
        "teleport": [QL["gText_QuestLog_Home"], S["gText_PokemonCenter"]],
        "num3": ["888"], "num6": ["888888"],
    }
    return {kind: max(values, key=lambda v: ct.measure(v, env).widest) for kind, values in lists.items()}


# rótulo -> conteúdo de cada placeholder (src/quest_log_events.c, LoadEvent_*)
QL_CONTENTS = {
    "SwitchMon1WithMon2": {"STR_VAR_1": "mon", "STR_VAR_2": "mon"},
    "SwappedHeldItemsOnMon": {"STR_VAR_1": "mon", "STR_VAR_2": "item", "STR_VAR_3": "item"},
    "TookHeldItemFromMon": {"STR_VAR_1": "mon", "STR_VAR_2": "item"},
    "UsedItemOnMonAtThisLocation": {"STR_VAR_1": "item", "STR_VAR_2": "mon"},
    "UsedTheItem": {"STR_VAR_1": "item"}, "UsedTheKeyItem": {"STR_VAR_1": "item"},
    "MonLearnedMoveFromTM": {"STR_VAR_1": "mon", "STR_VAR_2": "move"},
    "MonReplacedMoveWithTM": {"STR_VAR_1": "mon", "STR_VAR_2": "move", "STR_VAR_3": "move"},
    "MonLearnedMoveFromHM": {"STR_VAR_1": "mon", "STR_VAR_2": "move"},
    "MonReplacedMoveWithHM": {"STR_VAR_1": "mon", "STR_VAR_2": "move", "STR_VAR_3": "move"},
    "PlayerBattledChampionRival": {"0x00": "player", "0x01": "player"},
    "PlayerSentOutMon1RivalSentOutMon2": {"0x00": "player", "0x01": "mon", "0x02": "player", "0x03": "mon"},
    "WonTheMatchAsAResult": {"0x00": "champion_adverb"},
    "StoredItemInPC": {"STR_VAR_1": "item"}, "WithdrewItemFromPC": {"STR_VAR_1": "item"},
    "TradedMon1ForPersonsMon2": {"STR_VAR_1": "player", "STR_VAR_2": "mon", "STR_VAR_3": "mon"},
    "SingleBattleWithPersonResultedInOutcome": {"0x00": "player", "0x01": "outcome"},
    "DoubleBattleWithPersonResultedInOutcome": {"0x00": "player", "0x01": "outcome"},
    "MultiBattleWithPeopleResultedInOutcome": {"0x00": "player", "0x01": "player", "0x02": "player",
                                               "0x03": "player", "0x04": "outcome"},
    "DepartedPlaceInTownForNextDestination": {"STR_VAR_1": "map", "STR_VAR_2": "building"},
    "SwitchedMonsBetweenBoxes": {"0x00": "box", "0x01": "mon", "0x02": "box", "0x03": "mon"},
    "MovedMonToNewBox": {"0x00": "box", "0x01": "mon", "0x02": "box"},
    "SwitchedMonsWithinBox": {"0x00": "box", "0x01": "mon", "0x02": "mon"},
    "MovedMonWithinBox": {"0x00": "box", "0x01": "mon"},
    "SwitchedPartyMonForPCMon": {"0x00": "box", "0x01": "mon", "0x02": "mon"},
    "WithdrewMonFromPC": {"0x00": "box", "0x01": "mon"},
    "DepositedMonInPC": {"0x00": "mon", "0x01": "box"},
    "SwitchedMultipleMons": {"0x00": "box", "0x01": "spot"},
    "GaveMonHeldItemFromPC": {"STR_VAR_1": "item", "STR_VAR_2": "mon"},
    "SwappedHeldItemFromPC": {"STR_VAR_1": "item", "STR_VAR_2": "mon", "STR_VAR_3": "item"},
    "TradedMon1ForTrainersMon2": {"STR_VAR_1": "player", "STR_VAR_2": "mon", "STR_VAR_3": "mon"},
    "BattledTrainerEndedInOutcome": {"STR_VAR_1": "player", "STR_VAR_2": "outcome"},
    "BoughtItem": {"0x00": "map", "0x01": "item"},
    "BoughtItemsIncludingItem": {"0x00": "map", "0x01": "item", "0x02": "num6"},
    "SoldNumOfItem": {"0x00": "player", "0x01": "map", "0x02": "item", "0x03": "count"},
    "SoldItemsIncludingItem": {"0x00": "map", "0x01": "item", "0x02": "num6"},
    "UsedSoftboiled": {"STR_VAR_1": "mon"}, "UsedMilkDrink": {"STR_VAR_1": "mon"},
    "DefeatedWildMon": {"0x00": "map", "0x01": "mon", "0x05": "player"},
    "DefeatedWildMons": {"0x00": "map", "0x01": "mon", "0x02": "num3"},
    "CaughtWildMon": {"0x00": "map", "0x03": "mon", "0x05": "player"},
    "CaughtWildMons": {"0x00": "map", "0x03": "mon", "0x04": "num3"},
    "DefeatedWildMonAndCaughtWildMon": {"0x00": "map", "0x01": "mon", "0x03": "mon", "0x05": "player"},
    "DefeatedWildMonAndCaughtWildMons": {"0x00": "map", "0x01": "mon", "0x03": "mon", "0x04": "num3"},
    "DefeatedWildMonsAndCaughtWildMon": {"0x00": "map", "0x01": "mon", "0x02": "num3", "0x03": "mon",
                                         "0x05": "player"},
    "DefeatedWildMonsAndCaughtWildMons": {"0x00": "map", "0x01": "mon", "0x02": "num3", "0x03": "mon",
                                          "0x04": "num3"},
    "GaveMonHeldItem": {"STR_VAR_1": "mon", "STR_VAR_2": "item"},
    "GaveMonHeldItem2": {"STR_VAR_1": "mon", "STR_VAR_2": "item"},
    **{f"Used{m}": {"STR_VAR_1": "mon"} for m in ("Cut", "Surf", "Strength", "Flash", "RockSmash", "Waterfall",
                                                   "SweetScent")},
    "UsedFly": {"STR_VAR_1": "mon", "STR_VAR_2": "map"},
    "UsedDigInLocation": {"STR_VAR_1": "mon", "STR_VAR_2": "map"},
    "UsedTeleportToLocation": {"STR_VAR_1": "mon", "STR_VAR_2": "map", "STR_VAR_3": "teleport"},
    "LeftTownsLocationForNextDestination": {"STR_VAR_1": "map", "STR_VAR_2": "building"},
    "PlayedGamesAtGameCorner": {"STR_VAR_1": "map"},
    "GymWasFullOfToughTrainers": {"STR_VAR_1": "map"}, "DepartedGym": {"STR_VAR_1": "map"},
    "ManagedToGetOutOfLocation": {"STR_VAR_2": "building"},
    "TookOnGymLeadersMonWithMonAndWon": {"0x00": "map", "0x01": "trainer", "0x02": "mon", "0x03": "mon",
                                         "0x04": "adverb"},
    "TookOnEliteFoursMonWithMonAndWon": {"0x00": "trainer", "0x01": "mon", "0x02": "mon", "0x03": "adverb"},
    "TookOnTrainersMonWithMonAndWon": {"0x00": "map", "0x01": "trainer", "0x02": "mon", "0x03": "mon",
                                       "0x04": "adverb"},
    "UsedEscapeRope": {"STR_VAR_2": "map"},
    "DepartedTheLocationForNextDestination": {"STR_VAR_2": "building"},
    "DepartedFromLocationToNextDestination": {"STR_VAR_2": "building"},
    "ObtainedItemInLocation": {"STR_VAR_1": "map", "STR_VAR_2": "item"},
    "ArrivedInLocation": {"STR_VAR_1": "map"},
    "SavedGameAtLocation": {"STR_VAR_1": "map"},
}


def _fill(text: str, contents: dict[str, str], widest: dict[str, str]) -> str:
    for key, kind in contents.items():
        ph = "{" + key + "}" if key.startswith("STR_VAR") else "{DYNAMIC " + key + "}"
        assert ph in text, (key, text)
        text = text.replace(ph, widest[kind])
    assert not re.search(r"\{(?:STR_VAR_\d|DYNAMIC [0-9x]+)\}", text), text
    return text


def test_e3_quest_log_cabe_na_janela_com_os_nomes_reais(env):
    """Cada frase do Quest Log com o pior caso real de cada placeholder (nome de lugar mais largo, Pokémon,
    item, golpe, Treinador, jogador de 7 letras, caixa de 8) cabe em 3 linhas de 238 px."""
    widest = _widest()
    texts = {k[len("gText_QuestLog_"):]: v for k, v in QL.items()}
    sentences = [k for k, v in texts.items() if re.search(r"\{(?:STR_VAR_\d|DYNAMIC [0-9x]+)\}", v)
                 and k not in ("Num", "UsedDive")]
    assert sorted(sentences) == sorted(QL_CONTENTS)
    problems = []
    for name, contents in QL_CONTENTS.items():
        m = ct.measure(_fill(texts[name], contents, widest).replace("{PLAYER}", widest["player"]), env)
        if m.widest > QL_WIDTH or m.lines > QL_LINES:
            problems.append(f"{name}: {m.widest} px, {m.lines} linhas")
    assert problems == []


def test_e3_quest_log_textos_que_vao_para_gstringvar_cabem(env):
    """LoadEvent_DepartedLocation copia o lugar para gStringVar2; o Teleporte põe gText_QuestLog_Home ou
    gText_PokemonCenter em gStringVar3; a batalha da Sala União põe o resultado em gStringVar2; a venda expande
    gText_QuestLog_Num (até 3 algarismos) em gStringVar3 (src/quest_log_events.c:1458, :1973, :2066, :2140)."""
    events = (REPO_ROOT / "src" / "quest_log_events.c").read_text(encoding="utf-8")
    assert "StringCopy(gStringVar2, sLocationNameTexts[locationId]);" in events
    assert "StringCopy(gStringVar3, gText_QuestLog_Home);" in events
    assert "StringCopy(gStringVar2, sBattleOutcomeTexts[rOutcome]);" in events
    assert "DynamicPlaceholderTextUtil_ExpandPlaceholders(gStringVar3, gText_QuestLog_Num);" in events
    texts = [QL[f"gText_QuestLog_{n}"] for n in QL_BUILDINGS]
    texts += [QL["gText_QuestLog_Win"], QL["gText_QuestLog_Loss"], QL["gText_QuestLog_Draw"],
              QL["gText_QuestLog_Home"], S["gText_PokemonCenter"], QL["gText_QuestLog_JustOne"],
              QL["gText_QuestLog_Num"].replace("{DYNAMIC 0x04}", "888")]
    limit = min(STRING_VAR_SIZES["2"], STRING_VAR_SIZES["3"])
    assert [t for t in texts if ct.measure(t, env).nbytes + 1 > limit] == []


def test_e3_quest_log_tabelas_de_lugar_e_de_resultado():
    events = (REPO_ROOT / "src" / "quest_log_events.c").read_text(encoding="utf-8")
    table = events[events.index("sLocationNameTexts[] ="):]
    table = table[:table.index("};")]
    assert set(re.findall(r"gText_QuestLog_(\w+)", table)) == set(QL_BUILDINGS)
    assert (QL["gText_QuestLog_Win"], QL["gText_QuestLog_Loss"], QL["gText_QuestLog_Draw"]) == (
        "vitória", "derrota", "empate")
    assert QL["gText_QuestLog_WardensHome"] == "Casa do Diretor"


# --- Union Room: textos que vão para buffers -----------------------------------------------------------------

def test_e3_union_room_textos_que_vao_para_buffers_cabem(env):
    """Nome da atividade -> gStringVar1[32] (src/union_room.c:450, :1306, :2085); cor do cartão ->
    trainerCardColorStrBuffer[48] (src/union_room.c:4713, include/union_room.h)."""
    data = (REPO_ROOT / "src" / "data" / "union_room.h").read_text(encoding="utf-8")
    table = data[data.index("sLinkGroupActivityNameTexts[] = {"):]
    labels = set(re.findall(r"=\s*(gText_UR_\w+)", table[:table.index("};")]))
    assert {"gText_UR_SingleBattle", "gText_UR_BerryPicking", "gText_UR_WonderNews"} <= labels
    assert all(ct.measure(UR[lab], env).nbytes + 1 <= STRING_VAR_SIZES["1"] for lab in labels)
    header = (REPO_ROOT / "include" / "union_room.h").read_text(encoding="utf-8")
    assert "u8 trainerCardColorStrBuffer[48];" in header
    assert all(ct.measure(UR[f"sText_Its{c}Card"], env).nbytes + 1 <= 48
               for c in ("Normal", "Bronze", "Copper", "Silver", "Gold"))


def test_e3_union_room_rotulos_iguais_aos_menus():
    assert (UR["gText_UR_SingleBattle"], UR["gText_UR_DoubleBattle"], UR["gText_UR_MultiBattle"]) == (
        S["gText_SingleBattle"], S["gText_DoubleBattle"], S["gText_MultiBattle"])
    assert (UR["gText_UR_PokemonJump"], UR["gText_UR_BerryCrush"], UR["gText_UR_BerryPicking"]) == (
        S["gText_PokemonJump"], S["gText_BerryCrush"], S["gText_DodrioBerryPicking"])
    assert UR["gText_UR_Exit"] == S["gText_Exit"] and UR["gText_UR_Info"] == S["gText_Info"]


# --- plural montado em código (Pulo Pokémon) ----------------------------------------------------------------

def _c_body(rel: str, signature: str) -> str:
    source = (REPO_ROOT / rel).read_text(encoding="utf-8")
    body = source[source.index(signature):]
    return body[:body.index("\n}\n")]


def berry_name_plural(name: str) -> str:
    """Espelho de BufferBerryNamePlural (src/item.c): o "s" entra antes do 1º espaço (ou no fim)."""
    first, space, rest = name.partition(" ")
    return first + "s" + space + rest


def test_e3_plural_de_fruta_numa_funcao_so():
    """O plural de fruta (era "IES" no Pulo Pokémon) fica em BufferBerryNamePlural (src/item.c), chamada pelo
    prêmio do Pulo Pokémon e por bufferitemnameplural; o C confere com o espelho em Python."""
    helper = _c_body("src/item.c", "void BufferBerryNamePlural(u8 *name)")
    assert "while (*space != EOS && *space != CHAR_SPACE)" in helper
    assert "*space = EOS;" in helper and helper.index("sText_PluralS") < helper.index("StringAppend(name, tail);")
    assert 'sText_PluralS[] = _("s");' in (REPO_ROOT / "src" / "item.c").read_text(encoding="utf-8")
    assert "void BufferBerryNamePlural(u8 *name);" in (REPO_ROOT / "include" / "item.h").read_text(encoding="utf-8")
    jump = _c_body("src/pokemon_jump.c", "static void PrintPrizeMessage(u16 itemId, u16 quantity)")
    scr = _c_body("src/scrcmd.c", "bool8 ScrCmd_bufferitemnameplural")
    assert "BufferBerryNamePlural(sPokemonJumpGfx->itemName);" in jump and "tail" not in jump
    assert "BufferBerryNamePlural(sScriptStringVars[stringVarIndex]);" in scr and "tail" not in scr
    for rel in ("src/pokemon_jump.c", "src/scrcmd.c"):
        assert '_("IES")' not in (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_e3_plural_de_toda_fruta_cabe(env):
    """Toda fruta do items.json no plural: "Frutas X", até 19 letras (gStringVar) e < 64 (itemName do Pulo)."""
    assert berry_name_plural("Fruta Cheri") == "Frutas Cheri"
    assert berry_name_plural("Fruta Ocipêra") == "Frutas Ocipêra"
    assert berry_name_plural("Enigma") == "Enigmas"
    berries = [n for n in _e2_item_names() if n.startswith("Fruta ")]
    assert len(berries) >= 40
    for name in berries:
        plural = berry_name_plural(name)
        assert plural.startswith("Frutas ") and plural[len("Frutas "):] == name[len("Fruta "):]
        assert ct.measure(plural, env).nbytes + 1 <= min(STRING_VAR_SIZES["2"], 64), plural


# --- limpeza (Ruling 25) ---------------------------------------------------------------------------------------

def test_e3_gstring_bill_e_someone_removidos():
    for name in ("gString_Bill", "gString_Someone"):
        assert name not in STRINGS_C and name not in STRINGS_H
        for path in (REPO_ROOT / "src").rglob("*.c"):
            assert name not in path.read_text(encoding="utf-8", errors="replace"), path


# Glifo do nível: {LV} = 0x34 e {LV_2} = F9 05 (CHAR_EXTRA_SYMBOL, glifo 0x100 | 0x05, src/text.c) viram "Nv"
# (decisão D5); a imagem da caixa de vida (healthbox) fica para a frente H
LV_GLYPHS = (0x34, 0x105)
LV_TABLES = {"normal": ("sFontNormalLatinGlyphWidths", "sFontNormalCopy1LatinGlyphWidths"),
             "male": ("sFontMaleLatinGlyphWidths",), "female": ("sFontFemaleLatinGlyphWidths",),
             "small": ("sFontSmallLatinGlyphWidths",)}
_INK = (1, 2)


def _base_cell(font: str, code: int) -> list[list[int]] | None:
    import io
    from PIL import Image
    from esteira.font_render import GEOMETRY
    if shutil.which("git") is None:
        return None
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:graphics/fonts/latin_{font}.png"],
                         capture_output=True)
    if out.returncode != 0:
        return None
    cell_w, cell_h, per_row, _ = GEOMETRY[font]
    cx, cy = (code % per_row) * cell_w, (code // per_row) * cell_h
    with Image.open(io.BytesIO(out.stdout)) as img:
        return [[img.getpixel((cx + x, cy + y)) for x in range(cell_w)] for y in range(cell_h)]


def _ink_columns(cell: list[list[int]], rows: range) -> list[int]:
    return [x for x in range(len(cell[0])) if any(cell[y][x] == 1 for y in rows)]


@pytest.mark.parametrize("font", sorted(LV_TABLES))
def test_e3_glifo_do_nivel_e_nv_nas_quatro_fontes(font):
    """Os dois glifos de nível têm o mesmo desenho novo em cada fonte: N (duas hastes ligadas pela diagonal,
    linhas 4-10) e v (só da linha 6/7 para baixo), tudo dentro da largura da tabela e diferente do "Lv"."""
    from esteira.font_render import glyph_cell, glyph_widths
    cells = [glyph_cell(REPO_ROOT, font, code) for code in LV_GLYPHS]
    assert cells[0] == cells[1]
    cell = cells[0]
    widths = {glyph_widths(REPO_ROOT, t)[code] for t in LV_TABLES[font] for code in LV_GLYPHS}
    assert len(widths) == 1
    width = widths.pop()
    assert width <= len(cell[0])
    inked = [x for x in range(len(cell[0])) if any(cell[y][x] in _INK for y in range(len(cell)))]
    assert max(inked) < width
    # N: haste esquerda e haste direita (coluna 3) cheias nas linhas 4-10; diagonal nas colunas 1-2
    assert all(cell[y][0] == 1 and cell[y][3] == 1 for y in range(4, 11))
    assert any(cell[y][1] == 1 for y in (5, 6)) and any(cell[y][2] == 1 for y in (7, 8))
    # v: nada acima da linha 6 depois do N; dois braços que se juntam embaixo
    assert _ink_columns(cell, range(0, 6)) == [0, 3] or _ink_columns(cell, range(0, 6)) == [0, 1, 3]
    assert len(_ink_columns(cell, range(6, 8))) >= 4
    base = _base_cell(font, 0x105)
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    assert cell != base


def test_e3_largura_do_glifo_nv():
    """Mesma largura do "Lv" (normal/male/female 10 px, pequena 8 px): nenhuma linha já medida muda."""
    from esteira.font_render import glyph_widths
    for font, tables in LV_TABLES.items():
        for table in tables:
            w = glyph_widths(REPO_ROOT, table)
            assert w[0x34] == w[0x105] == (8 if font == "small" else 10), (font, table)


def test_e3_nivel_cabe_na_caixa_de_vida():
    """UpdateLvlInHealthbox (src/battle_interface.c): "{LV_2}" + nível em FONT_SMALL a partir de
    x = 5 * (3 - algarismos), copiado em 3 tiles (TextIntoHealthboxObject(..., 3)) = 24 px."""
    from esteira.font_render import glyph_widths
    bi = (REPO_ROOT / "src" / "battle_interface.c").read_text(encoding="utf-8")
    assert "xPos = 5 * (3 - (objVram - (text + 2)));" in bi and "TextIntoHealthboxObject(objVram, windowTileData, 3);" in bi
    small = glyph_widths(REPO_ROOT, "sFontSmallLatinGlyphWidths")
    from esteira.charmap import Charmap
    cm = Charmap.load(str(REPO_ROOT))
    for level in range(1, 101):
        digits = str(level)
        width = 5 * (3 - len(digits)) + small[0x105] + sum(small[cm.encode(d)[0]] for d in digits)
        assert width <= 24, level


# =====================================================================================================
# Task E4: braille (data/text/braille.inc) em PT-BR sem acento, com cada enigma conferido
# =====================================================================================================

BRAILLE_INC = "data/text/braille.inc"
BRAILLE_GLYPH_PX = 16          # GetGlyphWidth_Braille (src/braille_text.c)
BRAILLE_MAX_CELLS = 11         # maior frase original ("HAS MEANING", "WORLD WAITS"...): mesma posição do cursor


def _braille() -> dict[str, str]:
    text = (REPO_ROOT / BRAILLE_INC).read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in re.finditer(r'^(Braille_Text_\w+)::\n\t\.braille "([^"]*)\$"', text, re.M)}


def _script(map_name: str) -> str:
    return (REPO_ROOT / "data" / "maps" / map_name / "scripts.inc").read_text(encoding="utf-8")


def test_e4_braille_sem_ingles_e_sem_acento():
    report = ct.english_report(str(REPO_ROOT))
    assert BRAILLE_INC not in report
    braille = _braille()
    assert len(braille) == 39
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ ,.")
    assert {k: v for k, v in braille.items() if not set(v) <= allowed} == {}


def test_e4_braille_rotulos_iguais_aos_da_base():
    base = _e2_base(BRAILLE_INC)
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    assert re.findall(r"^(\w+)::", base, re.M) == list(_braille())


def test_e4_cada_frase_cabe_na_janela_e_o_cursor_fica_no_lugar():
    """braillemessage imprime em FONT_BRAILLE (16 px por cela) na janela de diálogo de 26 tiles (208 px);
    braillemessage_wait põe o cursor em x = largura + 27 (getbraillestringwidth + BrailleCursorToggle,
    src/scrcmd.c, src/field_specials.c). Nenhuma frase passa da maior frase original (11 celas): o cursor
    nunca passa de onde ficava no jogo inglês."""
    braille = _braille()
    over = {k: len(v) for k, v in braille.items() if len(v) * BRAILLE_GLYPH_PX > 208 or len(v) > BRAILLE_MAX_CELLS}
    assert over == {}
    assert "return 16;" in (REPO_ROOT / "src" / "braille_text.c").read_text(encoding="utf-8")


# Enigmas: o que o jogador lê -> o que precisa fazer (a ação está no mapa/código, não no texto)
DOTTED_HOLE = {          # andar: (rótulo, frase, warp certo a partir da placa em (6, 5), destino)
    "B1F": ("Braille_Text_Up", "CIMA", (6, 1), "MAP_SIX_ISLAND_DOTTED_HOLE_B2F"),
    "B2F": ("Braille_Text_Left", "ESQUERDA", (1, 5), "MAP_SIX_ISLAND_DOTTED_HOLE_B3F"),
    "B3F": ("Braille_Text_Right", "DIREITA", (11, 5), "MAP_SIX_ISLAND_DOTTED_HOLE_B4F"),
    "B4F": ("Braille_Text_Down", "BAIXO", (6, 9), "MAP_SIX_ISLAND_DOTTED_HOLE_SAPPHIRE_ROOM"),
}


@pytest.mark.parametrize("floor", sorted(DOTTED_HOLE))
def test_e4_buraco_pontilhado_a_direcao_lida_e_a_saida_certa(floor):
    """Cada andar do Buraco Pontilhado tem a placa em (6, 5) e cinco saídas; só a da direção escrita em braille
    leva ao andar seguinte (as outras voltam ao 1F)."""
    label, phrase, (x, y), dest = DOTTED_HOLE[floor]
    assert _braille()[label] == phrase
    data = json.loads((REPO_ROOT / "data/maps" / f"SixIsland_DottedHole_{floor}" / "map.json").read_text(encoding="utf-8"))
    sign = [b for b in data["bg_events"] if b.get("script", "").endswith(label.replace("Braille_Text_", "Braille"))]
    assert [(b["x"], b["y"]) for b in sign] == [(6, 5)]
    onward = [(w["x"], w["y"]) for w in data["warp_events"] if w["dest_map"] == dest]
    assert onward == [(x, y)]
    # as outras saídas devolvem ao 1F (a de (6, 7) é a escada para o andar de cima)
    others = [w for w in data["warp_events"] if (w["x"], w["y"]) not in ((x, y), (6, 7))]
    assert len(others) == 3 and {w["dest_map"] for w in others} == {"MAP_SIX_ISLAND_DOTTED_HOLE_1F"}
    dx, dy = x - 6, y - 5
    direction = {(0, -1): "CIMA", (0, 1): "BAIXO", (1, 0): "DIREITA", (-1, 0): "ESQUERDA"}[
        ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))]
    assert direction == phrase
    assert f"braillemessage {label}" in _script("SixIsland_DottedHole_1F")


def test_e4_vale_das_ruinas_pede_o_golpe_cortar():
    """A porta do Buraco Pontilhado diz CORTAR em braille; abrir = usar Cortar virado para o norte em (24, 25)
    (CutMoveRuinValleyCheck, src/field_specials.c), o mesmo golpe que o jogo chama de Cortar."""
    assert _braille()["Braille_Text_Cut"] == "CORTAR"
    moves = (REPO_ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8")
    assert re.search(r'\[MOVE_CUT\]\s*=\s*_\("([^"]*)"\)', moves).group(1).upper() == "CORTAR"
    assert "braillemessage Braille_Text_Cut" in _script("SixIsland_RuinValley")
    specials = (REPO_ROOT / "src" / "field_specials.c").read_text(encoding="utf-8")
    body = specials[specials.index("bool8 CutMoveRuinValleyCheck(void)"):]
    body = body[:body.index("\n}\n")]
    assert "pos.x == 24" in body and "pos.y == 25" in body and "DIR_NORTH" in body


def test_e4_monte_brasa_alfabeto_e_mensagem():
    """B4F: as placas são o alfabeto braille (letras e pontuação, iguais em português); B5F: mensagem lida antes
    do Rubi, sem ação (braillemessage_wait com o cursor)."""
    braille = _braille()
    for label in ("ABC", "GHI", "MNO", "TUV", "DEF", "JKL", "PQRS", "WXYZ"):
        assert braille[f"Braille_Text_{label}"] == label
    assert (braille["Braille_Text_Period"], braille["Braille_Text_Comma"]) == (".", ",")
    b5f = [braille[lab] for lab in re.findall(r"braillemessage(?:_wait)? (Braille_Text_\w+)",
                                               _script("MtEmber_RubyPath_B5F"))]
    assert " ".join(b5f) == "TUDO TEM SENTIDO EXISTIR TEM SENTIDO ESTAR VIVO TEM SENTIDO SONHE, SEJA FORTE."


def test_e4_sala_da_safira_frase_completa():
    braille = _braille()
    room = [braille[lab] for lab in re.findall(r"braillemessage(?:_wait)? (Braille_Text_\w+)",
                                                _script("SixIsland_DottedHole_SapphireRoom"))]
    assert " ".join(room) == ("QUE AS DUAS PEDRAS BRILHANTES, A VERMELHA E A AZUL, LIGUEM O PASSADO. DOIS AMIGOS "
                              "DIVIDINDO O PODER ABREM UMA JANELA A UM NOVO MUNDO. O PROXIMO MUNDO TE ESPERA.")


def test_verso_do_cartao_diz_batalhas_por_link_em_kanto_e_em_hoenn():
    """Decisão do Cintra (24/10, achado da I2): os dois versos do Cartão de Treinador (LINK BATTLES no de
    Kanto, LINK CABLE BATTLES no de Hoenn, sLinkTrainerCardRecordStrings) dizem "Batalhas por link"."""
    card = (REPO_ROOT / "src" / "trainer_card.c").read_text(encoding="utf-8")
    labels = re.search(r"sLinkTrainerCardRecordStrings\[\] = \{(\w+), (\w+)\};", card).groups()
    assert labels == ("gText_LinkBattles", "gText_LinkCableBattles")
    texts = [re.search(rf'const u8 {lab}\[\] = _\("([^"]*)"\);', STRINGS_C).group(1) for lab in labels]
    assert texts == ["Batalhas por link", "Batalhas por link"]
