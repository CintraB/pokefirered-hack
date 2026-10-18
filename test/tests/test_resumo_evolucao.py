"""Hack 4: página EVOLUTION do resumo do Pokémon.

Sem emulador: o texto esperado (esteira/evolution_page.py) nos casos fixos pedidos, o tamanho e
a largura das linhas de toda espécie, a ligação com os textos de src/strings.c e com o C da
página (janela, constantes, modos). Com a ROM de teste (pula se ela não existe ou está velha):
GetEvolutionPageText de TODAS as espécies igual, byte a byte, ao texto gerado aqui.
"""

import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from esteira import hooks
from esteira.check_text import WIDTH_RULES, _evolution_page_results, check_text, width_limit
from esteira.constants import Constants
from esteira.evolution_page import (ARROW, LINE_WIDTH_PX, LV, MAX_LINES, NO_EVOLUTION,
                                    NOT_POSSIBLE, PAGE_POINTS, SCREEN_POINTS, TRADED_ONLY, SHOWCASE, SOURCE_FILES, TEXT_X,
                                    WINDOW_WIDTH_PX, EvolutionPage, check_page_widths,
                                    evolution_line, text_size)
from esteira.refs import SHARED_POINTS
from esteira.scenarios import REPO_ROOT, open_context
from esteira.scenarios import full_summary_evolution as fse

CONSTS = Constants.load(str(REPO_ROOT), ["species.h"])
PAGE = EvolutionPage(REPO_ROOT, CONSTS)
SUMMARY_C = (REPO_ROOT / "src" / "pokemon_summary_screen.c").read_text(encoding="utf-8")
SUMMARY_H = (REPO_ROOT / "include" / "pokemon_summary_screen.h").read_text(encoding="utf-8")
STRINGS_C = (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")
TEST_HOOKS_H = (REPO_ROOT / "include" / "test_hooks.h").read_text(encoding="utf-8")
TEST_ROM = REPO_ROOT / "pokefirered_switch_test.gba"
TEST_ELF = REPO_ROOT / "pokefirered_switch_test.elf"

# Casos fixos (pedido do Cintra): o texto completo, linha a linha
FIXED = {
    "SPECIES_BULBASAUR": [f"{LV} 16 {ARROW} IVYSAUR"],
    "SPECIES_EEVEE": [f"THUNDERSTONE {ARROW} JOLTEON",
                      f"WATER STONE {ARROW} VAPOREON",
                      f"FIRE STONE {ARROW} FLAREON",
                      f"Day friendship {ARROW} ESPEON",
                      f"Night friendship {ARROW} UMBREON"],
    "SPECIES_ONIX": [f"{LV} 37 + METAL COAT {ARROW} STEELIX"],
    "SPECIES_SLOWPOKE": [f"{LV} 37 {ARROW} SLOWBRO",
                         f"{LV} 37 + KING'S ROCK {ARROW} SLOWKING"],
    "SPECIES_FEEBAS": [f"Subir nível + Escama Prisma {ARROW} MILOTIC"],
    "SPECIES_TAUROS": ["Does not evolve."],
    "SPECIES_WURMPLE": [f"{LV} 7 (random) {ARROW} SILCOON",
                        f"{LV} 7 (random) {ARROW} CASCOON"],
    "SPECIES_NINCADA": [f"{LV} 20 {ARROW} NINJASK",
                        f"{LV} 20, free slot {ARROW} SHEDINJA"],
    "SPECIES_TYROGUE": [f"{LV} 20, ATK < DEF {ARROW} HITMONCHAN",
                        f"{LV} 20, ATK > DEF {ARROW} HITMONLEE",
                        f"{LV} 20, ATK = DEF {ARROW} HITMONTOP"],
}


def _function(source: str, signature: str) -> str:
    start = source.index(signature + "\n{")
    return source[start:source.index("\n}\n", start)]


# --- texto esperado ---------------------------------------------------------------------------

@pytest.mark.parametrize("species", sorted(FIXED))
def test_casos_fixos(species):
    assert PAGE.text(species).split("\n") == FIXED[species]


def test_eevee_tem_5_linhas_sem_impossible():
    lines = PAGE.text("SPECIES_EEVEE").split("\n")
    assert len(lines) == 5
    assert [line.endswith(NOT_POSSIBLE) for line in lines] == [False] * 5


def test_especies_validas_sao_as_386_sem_old_unown():
    species = PAGE.valid_species()
    assert len(species) == 386 == len(set(species))
    assert species[0] == "SPECIES_BULBASAUR" and species[-1] == "SPECIES_CHIMECHO"
    assert not [s for s in species if "OLD_UNOWN" in s]
    assert "SPECIES_UNOWN" in species


def test_toda_especie_cabe_na_janela_e_no_buffer():
    size = text_size(REPO_ROOT)
    for species in PAGE.valid_species():
        text = PAGE.text(species)
        data = PAGE.encode(text)
        assert 1 <= len(text.split("\n")) <= MAX_LINES, species
        assert len(data) + 1 <= size, f"{species}: {len(data)} bytes"
        assert max(PAGE.line_widths(data)) <= LINE_WIDTH_PX, f"{species}: {PAGE.decode(data)}"
    assert check_page_widths(REPO_ROOT, CONSTS) == []


def test_todo_metodo_da_tabela_vira_linha():
    """Nenhuma entrada da tabela some da página (método sem formato)."""
    for species, entries in PAGE.table.items():
        for method, param, target in entries:
            assert evolution_line(method, param, target, PAGE.species_names,
                                  PAGE.item_names), (species, method)
    assert PAGE.text("SPECIES_MEW") == NO_EVOLUTION


def test_codifica_os_glifos_do_jogo():
    assert PAGE.encode(f"{LV} 5 {ARROW} A") == bytes([0xF9, 0x05, 0x00, 0xA6, 0x00, 0xF9, 0x03,
                                                      0x00, 0xBB])
    assert PAGE.decode(PAGE.encode(f"{LV}1\n{ARROW}") + b"\xff\x00") == "{LV_2}1 / {RIGHT_ARROW_2}"
    # largura do Lv e da seta: tabela de larguras do jogo em 0x100 | byte
    assert PAGE.line_widths(PAGE.encode(f"{LV}{ARROW}")) == [10 + 12]
    assert PAGE.line_widths(PAGE.encode("A\nAA")) == [6, 12]


# --- ligação com o C ---------------------------------------------------------------------------

def _templates() -> dict[str, str]:
    return dict(re.findall(r'const u8 (gText_PokeSum_Evo\w+)\[\] = _\("((?:[^"\\]|\\.)*)"\);',
                           STRINGS_C))


def test_formatos_de_strings_c_batem_com_o_python():
    """Cada gText_PokeSum_Evo* expandido como o C faz dá a linha que o Python espera."""
    t = _templates()
    by_method = {
        "EVO_LEVEL": "gText_PokeSum_EvoLevel", "EVO_LEVEL_NINJASK": "gText_PokeSum_EvoLevel",
        "EVO_ITEM": "gText_PokeSum_EvoItem", "EVO_LEVEL_HOLD_ITEM": "gText_PokeSum_EvoLevelHoldItem",
        "EVO_LEVEL_UP_HOLD_ITEM": "gText_PokeSum_EvoLevelUpHoldItem",
        "EVO_FRIENDSHIP": "gText_PokeSum_EvoFriendship",
        "EVO_FRIENDSHIP_DAY": "gText_PokeSum_EvoFriendshipDay",
        "EVO_FRIENDSHIP_NIGHT": "gText_PokeSum_EvoFriendshipNight",
        "EVO_BEAUTY": "gText_PokeSum_EvoBeauty",
        "EVO_LEVEL_ATK_GT_DEF": "gText_PokeSum_EvoAtkGtDef",
        "EVO_LEVEL_ATK_EQ_DEF": "gText_PokeSum_EvoAtkEqDef",
        "EVO_LEVEL_ATK_LT_DEF": "gText_PokeSum_EvoAtkLtDef",
        "EVO_LEVEL_SILCOON": "gText_PokeSum_EvoLevelRandom",
        "EVO_LEVEL_CASCOON": "gText_PokeSum_EvoLevelRandom",
        "EVO_LEVEL_SHEDINJA": "gText_PokeSum_EvoLevelFreeSlot",
        "EVO_TRADE": "gText_PokeSum_EvoTrade", "EVO_TRADE_ITEM": "gText_PokeSum_EvoTradeItem",
    }
    suffixes = {"EVO_BEAUTY": "gText_PokeSum_EvoTradedOnly"}
    for method, label in by_method.items():
        item = method in ("EVO_ITEM", "EVO_LEVEL_HOLD_ITEM", "EVO_LEVEL_UP_HOLD_ITEM",
                          "EVO_TRADE_ITEM")
        param = "ITEM_METAL_COAT" if item else "20"
        level = "37" if method == "EVO_LEVEL_HOLD_ITEM" else param
        c_line = (t[label].replace("{STR_VAR_1}", level).replace("{STR_VAR_2}", "METAL COAT")
                  .replace("{STR_VAR_3}", "STEELIX"))
        if method in suffixes:
            c_line += t[suffixes[method]]
        assert evolution_line(method, param, "SPECIES_STEELIX", PAGE.species_names,
                              PAGE.item_names) == c_line, method
        case = re.search(rf"case {method}:(?:\s*case \w+:)*(.*?)break;",
                         _function(SUMMARY_C, "void GetEvolutionPageText(u8 *dest, u16 species)"),
                         re.S)
        assert case and label in case.group(1), f"{method} sem {label} em GetEvolutionPageText"
        suffix = re.search(r"suffix = (\w+);", case.group(1))
        assert (suffix and suffix.group(1)) == suffixes.get(method), method
    assert t["gText_PokeSum_EvoNone"] == NO_EVOLUTION
    assert t["gText_PokeSum_EvoNotPossible"] == NOT_POSSIBLE
    assert t["gText_PokeSum_EvoTradedOnly"] == TRADED_ONLY


def test_janela_e_constantes_do_c_batem_com_o_python():
    window = re.search(r"sWindowTemplates_Evolution\[\] =\s*\{\s*\[POKESUM_WIN_RIGHT_PANE - 3\] = "
                       r"\{(.*?)\}", SUMMARY_C, re.S).group(1)
    fields = dict(re.findall(r"\.(\w+) = (\w+)", window))
    assert (int(fields["tilemapLeft"]), int(fields["width"])) == (1, WINDOW_WIDTH_PX // 8)
    defines = dict(re.findall(r"#define (EVOLUTION_PAGE_\w+)\s+(\d+)", SUMMARY_C))
    assert int(defines["EVOLUTION_PAGE_TEXT_X"]) == TEXT_X
    # MAX_LINES linhas de 14 px + espaçamento cabem na altura da janela
    line = 14 + int(defines["EVOLUTION_PAGE_LINE_SPACING"])
    assert int(defines["EVOLUTION_PAGE_TEXT_Y"]) + MAX_LINES * line <= int(fields["height"]) * 8
    assert line == 16             # uma linha por pauta da moldura (page_evolution.bin)


def test_regra_de_largura_cita_a_janela_certa():
    rule = next(r for r in WIDTH_RULES if r[1] == "gText_PokeSum_Evo")
    assert rule[2] == LINE_WIDTH_PX
    lines = SUMMARY_C.splitlines()
    cited = {int(n) for n in re.findall(r"src/pokemon_summary_screen\.c:(\d+)", rule[3])}
    assert cited, rule[3]
    text = "\n".join(lines[n - 1] for n in cited)
    assert ".width = 28" in text and "#define EVOLUTION_PAGE_TEXT_X" in text
    window_start = next(i for i, l in enumerate(lines) if "sWindowTemplates_Evolution[] =" in l)
    width_line = next(i for i in range(window_start, len(lines)) if ".width" in lines[i]) + 1
    assert width_line in cited


def test_buffer_da_build_de_teste_comporta_o_texto():
    test_size = int(re.search(r"#define TEST_TEXT_SIZE (\d+)", TEST_HOOKS_H).group(1))
    assert test_size >= text_size(REPO_ROOT)


def test_paginas_e_modos_do_header_batem_com_hooks():
    pages = re.search(r"enum PokemonSummaryScreenPage\s*\{(.*?)\};", SUMMARY_H, re.S).group(1)
    names = [n.strip() for n in re.sub(r"//[^\n]*", "", pages).split(",") if n.strip()]
    index = {n: i for i, n in enumerate(names)}
    assert index["PSS_PAGE_EVOLUTION"] == hooks.PSS_PAGE_EVOLUTION
    assert (index["PSS_PAGE_INFO"], index["PSS_PAGE_MOVES"], index["PSS_PAGE_MOVES_INFO"]) == (
        hooks.PSS_PAGE_INFO, hooks.PSS_PAGE_MOVES, hooks.PSS_PAGE_MOVES_INFO)
    assert index["PSS_PAGE_MOVES_INFO"] == index["PSS_PAGE_MOVES"] + 1   # o código de virar conta com isso
    modes = re.search(r"enum PokemonSummaryScreenMode\s*\{(.*?)\};", SUMMARY_H, re.S).group(1)
    modes = [n.strip() for n in modes.split(",") if n.strip()]
    assert modes.index("PSS_MODE_SELECT_MOVE") == hooks.PSS_MODE_SELECT_MOVE


def test_pagina_nao_aparece_para_ovo_nem_nos_modos_de_golpe():
    body = _function(SUMMARY_C, "static bool32 PokeSum_CanShowExtraPages(void)")
    assert "isEgg" in body
    assert "PSS_MODE_SELECT_MOVE" in body and "PSS_MODE_FORGET_MOVE" in body
    handler = _function(SUMMARY_C, "static void Task_InputHandler_Info(u8 taskId)")
    assert "PokeSum_CanShowExtraPages()" in handler
    # o resumo de ovo não vira página nenhuma (vanilla)
    assert "if (sMonSummaryScreen->isEgg)\n        return FALSE;" in _function(
        SUMMARY_C, "bool32 IsPageFlipInput(u8 direction)")


def test_textos_novos_entram_na_checagem_de_texto():
    assert width_limit("src/strings.c", "gText_PokeSum_EvoLevelHoldItem") == LINE_WIDTH_PX
    assert width_limit("src/strings.c", "gText_PokeSum_PageName_Evolution") is None   # menu
    problems = [r for r in check_text(str(REPO_ROOT), {"text": []})
                if "gText_PokeSum_" in r.detail or "EVOLUTION" in r.detail]
    assert problems == []


def _mini_repo(tmp_path: Path) -> Path:
    for rel in SOURCE_FILES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    return tmp_path


def test_checagem_de_texto_reprova_linha_larga_demais(tmp_path):
    repo = _mini_repo(tmp_path)
    items = repo / "src" / "data" / "items.json"
    items.write_text(items.read_text(encoding="utf-8").replace('"METAL COAT"', '"METAL COAT XXXXXXXXXXXX"'),
                     encoding="utf-8")
    results = _evolution_page_results(repo)
    assert results and all(r.status == "falha" and r.name == "texto/largura" for r in results)
    assert any("SPECIES_ONIX" in r.detail for r in results)
    assert any("SPECIES_SCYTHER" in r.detail for r in results)


def test_checagem_de_texto_sem_os_fontes_nao_mede_e_com_os_reais_passa(tmp_path):
    assert _evolution_page_results(tmp_path) == []
    repo = _mini_repo(tmp_path)
    assert _evolution_page_results(repo) == []


# --- cenário e telas ---------------------------------------------------------------------------

def test_telas_da_pagina_sao_comuns_aos_iniciais():
    assert set(SCREEN_POINTS) | set(PAGE_POINTS) <= set(SHARED_POINTS)
    assert SCREEN_POINTS == tuple(f"resumo_evo_{s[8:].lower()}" for s in SHOWCASE)


def test_time_do_cenario_tem_os_pedidos():
    for species in ("SPECIES_EEVEE", "SPECIES_ONIX", "SPECIES_SLOWPOKE", "SPECIES_BULBASAUR",
                    "SPECIES_TAUROS"):
        assert species in SHOWCASE
    assert fse.EGG_SLOT == len(SHOWCASE)
    assert fse.LEARNER in SHOWCASE


def test_aprendiz_tem_4_golpes_e_aprende_um_no_nivel_seguinte():
    """Tauros 18 sai do CreateMon com 4 golpes e aprende PURSUIT no 19 (o cenário provoca o
    resumo de escolher golpe com uma Rare Candy)."""
    learnsets = (REPO_ROOT / "src" / "data" / "pokemon" / "level_up_learnsets.h").read_text(encoding="utf-8")
    body = re.search(r"sTaurosLevelUpLearnset\[\] = \{(.*?)\};", learnsets, re.S).group(1)
    moves = [(int(lv), mv) for lv, mv in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(\w+)\)", body)]
    known = [mv for lv, mv in moves if lv <= fse.LEARNER_LEVEL]
    assert len(known) >= 4
    assert [mv for lv, mv in moves if lv == fse.LEARNER_LEVEL + 1] == ["MOVE_PURSUIT"]
    evolutions = (REPO_ROOT / "src" / "data" / "pokemon" / "evolution.h").read_text(encoding="utf-8")
    assert "[SPECIES_TAUROS]" not in evolutions      # e não evolui no meio do teste


@pytest.mark.parametrize("window, frames", [(True, fse.READ_PAUSE), (False, 0)])
def test_pausa_de_leitura_so_na_janela(window, frames):
    spent = []
    sc = fse.SummaryEvolutionScenario.__new__(fse.SummaryEvolutionScenario)
    sc.emu = SimpleNamespace(window=window, frames=lambda n: spent.append(n))
    sc._pause_to_read()
    assert sum(spent) == frames


def test_assistir_aceita_o_cenario():
    from esteira import __main__ as cli
    assert "resumo_evolucao" in cli.WATCH_FULL_SCENARIOS
    args = cli.build_parser().parse_args(["assistir", "--cenario", "resumo_evolucao"])
    assert args.cenario == "resumo_evolucao"


# --- o jogo (build de teste) --------------------------------------------------------------------

def _stale_test_rom() -> str | None:
    if not (TEST_ROM.is_file() and TEST_ELF.is_file()):
        return f"ROM de teste não encontrada ({TEST_ROM.name}): rode `make firered_switch TESTBUILD=1`"
    sources = [REPO_ROOT / p for p in (*SOURCE_FILES, "src/strings.c", "src/pokemon_summary_screen.c",
                                       "src/test_hooks.c")]
    newest = max(p.stat().st_mtime for p in sources)
    if TEST_ROM.stat().st_mtime < newest:
        return "ROM de teste mais velha que os fontes da página: rode `make firered_switch TESTBUILD=1`"
    return None


def test_jogo_monta_o_texto_esperado_para_todas_as_especies(tmp_path):
    why = _stale_test_rom()
    if why:
        pytest.skip(why)
    with open_context(str(TEST_ROM), str(TEST_ELF), str(tmp_path), "BULBASAUR") as ctx:
        box = hooks.Mailbox(ctx.controller)
        ctx.emu.frames(60)
        wrong = []
        for name in PAGE.valid_species():
            got = box.evolution_text(CONSTS.species(name))
            want = PAGE.encode(PAGE.text(name))
            if got != want:
                wrong.append(f"{name}: '{PAGE.decode(got)}' != '{PAGE.decode(want)}'")
        assert not wrong, wrong[:5]
        assert box.summary_state() is None                 # nenhum resumo aberto no boot
        with pytest.raises(AssertionError, match="nenhum resumo aberto"):
            box.evolution_text(from_open_summary=True)
