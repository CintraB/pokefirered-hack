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


def _string_var_sizes() -> dict[str, int]:
    """Tamanho de gStringVar1/2/3, lido de src/string_util.c."""
    text = (REPO_ROOT / "src" / "string_util.c").read_text(encoding="utf-8")
    return {n: int(size, 0) for n, size in re.findall(r"u8 gStringVar([123])\[(\w+)\]", text)}


STRING_VAR_SIZES = _string_var_sizes()
_COPY_TO_VAR = re.compile(r"(?:StringCopy|StringExpandPlaceholders|StringAppend)\(gStringVar([123])\w*,\s*(g\w+)\)")


def test_textos_copiados_para_gstringvar_cabem_no_buffer(env):
    """gStringVar2/3 têm 20 bytes: "Bolso de itens-chave" (20 letras + EOS) estourava o
    gStringVar3 pelo bufferstdstring da mensagem de item obtido e travava o jogo."""
    sizes: dict[str, int] = {}
    for path in (REPO_ROOT / "src").rglob("*.c"):
        for var, label in _COPY_TO_VAR.findall(path.read_text(encoding="utf-8", errors="replace")):
            sizes[label] = min(sizes.get(label, 999), STRING_VAR_SIZES[var])
    menu = (REPO_ROOT / "src" / "script_menu.c").read_text(encoding="utf-8")
    std = menu[menu.index("gStdStringPtrs[] = {"):]
    for label in re.findall(r"=\s*(gText_\w+)", std[:std.index("};")]):
        sizes[label] = min(sizes.get(label, 999), 20)      # bufferstdstring para qualquer STR_VAR
    over = [f"{label}: {ct.measure(S[label], env).nbytes + 1} bytes > {size}"
            for label, size in sorted(sizes.items())
            if label in S and ct.measure(S[label], env).nbytes + 1 > size]
    assert sizes.get("gText_KeyItemsPocket") == 20 and over == []


def test_texto_do_estojo_de_mt_comeca_com_str_var_1():
    """src/tm_case.c pula os 2 primeiros bytes ({STR_VAR_1}) de gText_Var1IsSelected."""
    assert S["gText_Var1IsSelected"].startswith("{STR_VAR_1}")
    assert "gText_Var1IsSelected + 2" in (REPO_ROOT / "src" / "tm_case.c").read_text(encoding="utf-8")


# Aviso de nome do mapa com andar (MapNamePopupPrintMapNameOnWindow/MapNamePopupAppendFloorNum,
# src/map_name_popup.c): u8 mapName[25] = nome + " " + ("B")N"F" ou gText_Rooftop2, sem limite de
# cópia; janela de 152 px com andar e 176 px no terraço (FLOOR_ROOFTOP = 127)
POPUP_BUFFER = 25
FLOOR_ROOFTOP = 127
# IsCeladonDeptStoreMapsec (src/region_map.c): nos mapas CeladonCity_DepartmentStore_* o nome é o
# da seção especial ("Loja de Celadon")
CELADON_DEPT_STORE_NAME = "MAPSEC_SPECIAL_AREA"


def test_aviso_de_mapa_com_andar_cabe_no_buffer(env):
    """"Loja de Celadon Cobertura" (25 letras + EOS) estourava mapName[25] no terraço da loja."""
    sections = json.loads((REPO_ROOT / "src/data/region_map/region_map_sections.json").read_text(
        encoding="utf-8"))["map_sections"]
    names = {s["id"]: s["name"] for s in sections if s.get("name")}
    popup = (REPO_ROOT / "src" / "map_name_popup.c").read_text(encoding="utf-8")
    assert "u8 mapName[25];" in popup and "StringCopy(dest, gText_Rooftop2)" in popup
    problems, seen = [], 0
    for path in sorted((REPO_ROOT / "data" / "maps").glob("*/map.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        floor = data.get("floor_number", 0)
        if not floor or not data.get("show_map_name", True):
            continue
        mapsec = data["region_map_section"]
        if mapsec == "MAPSEC_CELADON_CITY" and data["name"].startswith("CeladonCity_DepartmentStore_"):
            mapsec = CELADON_DEPT_STORE_NAME        # GetMapName usa o nome especial dentro da loja
        for mapsec in (mapsec,):
            if mapsec not in names:
                continue
            seen += 1
            if floor == FLOOR_ROOFTOP:
                suffix, width = S["gText_Rooftop2"], 176
            else:
                suffix, width = ("B" if floor < 0 else "") + f"{abs(floor)}F", 152
            text = f"{names[mapsec]} {suffix}"
            m = ct.measure(text, env)
            if m.nbytes + 1 > POPUP_BUFFER or m.widest > width:
                problems.append(f"{path.parent.name}: '{text}' {m.nbytes + 1} bytes, {m.widest} px")
    assert seen and problems == []


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
    assert "StringAppend(name, sText_S);" in body and "StringAppend(name, tail);" in body
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
    assert 8 + 1 <= sizes["2"]


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
