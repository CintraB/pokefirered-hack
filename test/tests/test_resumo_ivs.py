"""Hack 5: página IVs/EVs do resumo do Pokémon.

Sem emulador: as contas (nível de cada IV, total, %, avaliação geral, Hidden Power) nos casos de
borda do design, a ligação do texto esperado com src/strings.c e com o C (colunas, janela, a
fórmula do Hidden Power compartilhada com o golpe) e a largura das linhas. Com a ROM de teste
(pula se ela não existe ou está velha): GetIvEvPageText igual, byte a byte, ao texto calculado
aqui, nas bordas, em todos os tipos de Hidden Power e em combinações sorteadas.
"""

import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from esteira import hooks
from esteira.check_text import WIDTH_RULES, _ivev_page_results, width_limit
from esteira.ivev_page import (COL_EV, COL_EV_END, COL_GRADE, COL_IV_END, COL_OVERALL,
                               COL_PERCENT, LINE_WIDTH_PX, LINES, SCREEN_POINTS, SHOWCASE,
                               SOURCE_FILES, STATS, TEXT_X, WINDOW_WIDTH_PX, IvEvPage,
                               check_page_widths, hidden_power, iv_grade, load_type_names,
                               percent, total_grade, worst_cases)
from esteira.refs import SHARED_POINTS
from esteira.scenarios import REPO_ROOT, open_context
from esteira.scenarios import full_summary_ivs as fsi
from esteira.scenarios.full_summary_evolution import READ_PAUSE

PAGE = IvEvPage(REPO_ROOT)
SUMMARY_C = (REPO_ROOT / "src" / "pokemon_summary_screen.c").read_text(encoding="utf-8")
BATTLE_C = (REPO_ROOT / "src" / "battle_script_commands.c").read_text(encoding="utf-8")
STRINGS_C = (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")
SUMMARY_H = (REPO_ROOT / "include" / "pokemon_summary_screen.h").read_text(encoding="utf-8")
TEST_ROM = REPO_ROOT / "pokefirered_switch_test.gba"
TEST_ELF = REPO_ROOT / "pokefirered_switch_test.elf"
TYPES = load_type_names(REPO_ROOT)


def _function(source: str, signature: str) -> str:
    """Corpo da definição (o protótipo, que termina em `;`, é pulado)."""
    start = next(m.start() for m in re.finditer(re.escape(signature), source)
                 if not re.match(r"[^)]*\);", source[m.start():]))
    start = source.index("\n{", start)
    return source[start:source.index("\n}\n", start)]


# --- contas (design: docs/superpowers/specs/2026-10-17-pagina-ivs-evs-design.md) ---------------

@pytest.mark.parametrize("iv, grade", [(31, "Perfect"), (30, "Excellent"), (26, "Excellent"),
                                       (25, "Very good"), (16, "Very good"), (15, "Good"),
                                       (1, "Good"), (0, "Poor")])
def test_nivel_de_cada_iv(iv, grade):
    assert iv_grade(iv) == grade


@pytest.mark.parametrize("total, grade", [(186, "Perfect"), (185, "Outstanding"), (151, "Outstanding"),
                                          (150, "Above average"), (121, "Above average"),
                                          (120, "Average"), (91, "Average"), (90, "Below average"),
                                          (0, "Below average")])
def test_avaliacao_geral(total, grade):
    assert total_grade(total) == grade


@pytest.mark.parametrize("total, pct", [(186, 100), (0, 0), (161, 87), (93, 50), (1, 1), (185, 99),
                                        (120, 65)])
def test_percentual_arredondado(total, pct):
    assert percent(total) == pct
    assert pct == int(total / 186 * 100 + 0.5)


def test_hidden_power_bordas():
    assert hidden_power((31,) * 6) == (17, 70)          # Sombr. 70
    assert TYPES[17] == "Sombr."
    assert hidden_power((0,) * 6) == (1, 30)            # Lutad. 30
    assert TYPES[1] == "Lutad."
    seen = {hidden_power(tuple(2 | ((b >> i) & 1) | 28 for i in range(6))) for b in range(64)}
    assert {t for t, _ in seen} == set(range(1, 18)) - {9}      # nunca NORMAL nem ???
    assert {p for _, p in seen} == {70}


def test_hidden_power_usa_a_ordem_da_batalha():
    """A página guarda os IVs na ordem dela (… SP. ATK, SP. DEF, SPEED); a conta usa a da batalha
    (HP, Atk, Def, Spe, SpA, SpD): só o SPEED ímpar muda o 4º bit do tipo."""
    base = (0,) * 6
    speed_odd = (0, 0, 0, 0, 0, 1)
    spatk_odd = (0, 0, 0, 1, 0, 0)
    assert hidden_power(base) == (1, 30)                     # Lutad.
    assert hidden_power(speed_odd) == (15 * 8 // 63 + 1, 30) == (2, 30)      # FLYING
    assert hidden_power(spatk_odd) == (15 * 16 // 63 + 1, 30) == (4, 30)     # GROUND


def test_casos_do_design_e_do_cenario():
    mewtwo = PAGE.text(*SHOWCASE[0][1:])
    assert PAGE.decode(mewtwo).startswith("IV TOTAL 186/186{SKIP 106}100%{SKIP 136}Perfect / HP")
    assert PAGE.decode(mewtwo).endswith("HIDDEN POWER Sombr. 70{SKIP 144}EV{SKIP 164}510/510")
    magikarp = PAGE.decode(PAGE.text(*SHOWCASE[1][1:]))
    assert "IV TOTAL 0/186{SKIP 106}0%{SKIP 136}Below average" in magikarp
    eevee = PAGE.decode(PAGE.text(*SHOWCASE[2][1:]))
    for grade in ("Very good", "Excellent", "Good"):    # 25/16, 26/30, 15/1
        assert grade in eevee
    assert len(PAGE.text(*SHOWCASE[0][1:]).split(b"\xfe")) == LINES


# --- ligação com o C ---------------------------------------------------------------------------

def _strings() -> dict[str, str]:
    return dict(re.findall(r'const u8 (gText_PokeSum_\w+)\[\] = _\("((?:[^"\\]|\\.)*)"\);', STRINGS_C))


def test_textos_de_strings_c_batem_com_o_python():
    s = _strings()
    assert [s[f"gText_PokeSum_Stat{n}"] for n in ("Hp", "Attack", "Defense", "SpAtk", "SpDef", "Speed")] \
        == list(STATS)
    assert [s[f"gText_PokeSum_Iv{n}"] for n in ("Perfect", "Excellent", "VeryGood", "Good", "Poor")] \
        == [iv_grade(i) for i in (31, 30, 20, 10, 0)]
    assert [s[f"gText_PokeSum_IvTotal{n}"] for n in ("Perfect", "Outstanding", "AboveAverage",
                                                     "Average", "BelowAverage")] \
        == [total_grade(t) for t in (186, 160, 130, 100, 50)]
    assert (s["gText_PokeSum_IvTotal"], s["gText_PokeSum_Ev"], s["gText_PokeSum_HiddenPower"]) == (
        "IV TOTAL", "EV", "HIDDEN POWER")
    assert s["gText_PokeSum_PageName_IvsEvs"] == "IVs/EVs"


def test_colunas_e_janela_do_c_batem_com_o_python():
    defines = {k: int(v) for k, v in re.findall(r"#define (IVEV_\w+)\s+(\d+)\b", SUMMARY_C)}
    assert (defines["IVEV_COL_IV_END"], defines["IVEV_COL_GRADE"], defines["IVEV_COL_PERCENT"],
            defines["IVEV_COL_OVERALL"], defines["IVEV_COL_EV"], defines["IVEV_COL_EV_END"]) == (
        COL_IV_END, COL_GRADE, COL_PERCENT, COL_OVERALL, COL_EV, COL_EV_END)
    assert defines["IVEV_PAGE_TEXT_X"] == TEXT_X
    window = re.search(r"sWindowTemplates_Ivs\[\] =\s*\{\s*\[POKESUM_WIN_RIGHT_PANE - 3\] = \{(.*?)\}",
                       SUMMARY_C, re.S).group(1)
    fields = {k: int(v) for k, v in re.findall(r"\.(\w+) = (\d+)", window)}
    assert fields["width"] * 8 == WINDOW_WIDTH_PX
    assert defines["IVEV_PAGE_TEXT_Y"] + LINES * 14 <= fields["height"] * 8


def test_hidden_power_da_pagina_e_do_golpe_e_a_mesma_funcao():
    move = _function(BATTLE_C, "static void Cmd_hiddenpowercalc(void)")
    assert "CalcHiddenPower(" in move and "powerBits" not in move
    assert "CalcHiddenPower(" in _function(SUMMARY_C, "void GetIvEvPageText(u8 *dest, struct Pokemon *mon)")
    calc = _function(BATTLE_C, "void CalcHiddenPower(")
    # a fórmula do Gen 3, a mesma que o Python usa
    assert "*power = (40 * powerBits) / 63 + 30;" in calc
    assert "*type = ((NUMBER_OF_MON_TYPES - 3) * typeBits) / 63 + 1;" in calc
    assert "if (*type >= TYPE_MYSTERY)" in calc
    order = re.findall(r"\(\((\w+)IV & 1\) << (\d)\)", calc)
    assert order == [("hp", "0"), ("attack", "1"), ("defense", "2"), ("speed", "3"),
                     ("spAttack", "4"), ("spDefense", "5")]


def test_pagina_segue_as_regras_da_evolution():
    handler = _function(SUMMARY_C, "static void Task_InputHandler_Info(u8 taskId)")
    assert "PSS_PAGE_IVS" in handler and "PokeSum_CanShowExtraPages()" in handler
    seek = _function(SUMMARY_C, "static u8 PokeSum_CanSeekToMon(struct Pokemon * partyMons)")
    assert "PSS_PAGE_IVS" in seek
    pages = re.search(r"enum PokemonSummaryScreenPage\s*\{(.*?)\};", SUMMARY_H, re.S).group(1)
    names = [n.strip() for n in re.sub(r"//[^\n]*", "", pages).split(",") if n.strip()]
    assert names.index("PSS_PAGE_IVS") == hooks.PSS_PAGE_IVS


# --- largura -----------------------------------------------------------------------------------

def test_todas_as_linhas_cabem_na_janela_sem_encavalar():
    assert check_page_widths(REPO_ROOT) == []
    for ivs, evs in worst_cases():
        assert max(PAGE.line_widths(PAGE.text(ivs, evs))) <= LINE_WIDTH_PX


def test_regras_de_largura_dos_textos_novos():
    for label in ("gText_PokeSum_IvTotalAboveAverage", "gText_PokeSum_StatSpAtk",
                  "gText_PokeSum_HiddenPower", "gText_PokeSum_Ev"):
        assert width_limit("src/strings.c", label) == LINE_WIDTH_PX
    assert width_limit("src/strings.c", "gText_PokeSum_EvoLevel") == LINE_WIDTH_PX   # a da EVOLUTION
    rule = next(r for r in WIDTH_RULES if r[1] == "gText_PokeSum_Iv")
    lines = SUMMARY_C.splitlines()
    cited = [int(n) for n in re.findall(r"src/pokemon_summary_screen\.c:(\d+)", rule[3])]
    text = "\n".join(lines[n - 1] for n in cited)
    assert ".width = 28" in text and "#define IVEV_PAGE_TEXT_X" in text
    start = next(i for i, l in enumerate(lines) if "sWindowTemplates_Ivs[] =" in l)
    assert next(i for i in range(start, len(lines)) if ".width" in lines[i]) + 1 in cited


def test_checagem_de_texto_reprova_coluna_apertada(tmp_path):
    for rel in SOURCE_FILES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    assert _ivev_page_results(tmp_path) == []
    battle = tmp_path / "src" / "battle_main.c"
    battle.write_text(battle.read_text(encoding="utf-8").replace('_("Lutad.")', '_("LUTADORLUTADOR")'),
                      encoding="utf-8")
    results = _ivev_page_results(tmp_path)
    assert results and all(r.name == "texto/largura" and r.status == "falha" for r in results)
    assert _ivev_page_results(tmp_path / "vazio") == []


# --- cenário -----------------------------------------------------------------------------------

def test_cenario_tem_as_bordas_do_design():
    totals = [sum(ivs) for _, ivs, _ in SHOWCASE]
    assert 186 in totals and 0 in totals
    assert any(sum(evs) == 510 for _, _, evs in SHOWCASE)
    ivs = {iv for _, i, _ in SHOWCASE for iv in i}
    assert {25, 26, 15, 16} <= ivs
    assert set(SCREEN_POINTS) <= set(SHARED_POINTS)


def test_combinacoes_sorteadas_sao_validas_e_fixas():
    cases = fsi.random_cases()
    assert cases == fsi.random_cases() and len(cases) == fsi.RANDOM_CASES
    for ivs, evs in cases:
        assert all(0 <= iv <= 31 for iv in ivs)
        assert all(0 <= ev <= 255 for ev in evs) and sum(evs) <= 510


def test_assistir_aceita_o_cenario():
    from esteira import __main__ as cli
    assert "resumo_ivs" in cli.WATCH_FULL_SCENARIOS
    assert cli.build_parser().parse_args(["assistir", "--cenario", "resumo_ivs"]).cenario == "resumo_ivs"


@pytest.mark.parametrize("window, frames", [(True, READ_PAUSE), (False, 0)])
def test_pausa_de_leitura_so_na_janela(window, frames):
    spent = []
    sc = fsi.SummaryIvsScenario.__new__(fsi.SummaryIvsScenario)
    sc.emu = SimpleNamespace(window=window, frames=lambda n: spent.append(n))
    sc._pause_to_read()
    assert sum(spent) == frames


# --- o jogo (build de teste) --------------------------------------------------------------------

def _stale_test_rom() -> str | None:
    if not (TEST_ROM.is_file() and TEST_ELF.is_file()):
        return f"ROM de teste não encontrada ({TEST_ROM.name}): rode `make firered_switch TESTBUILD=1`"
    sources = [REPO_ROOT / p for p in (*SOURCE_FILES, "src/strings.c", "src/pokemon_summary_screen.c",
                                       "src/battle_script_commands.c", "src/test_hooks.c")]
    if TEST_ROM.stat().st_mtime < max(p.stat().st_mtime for p in sources):
        return "ROM de teste mais velha que os fontes da página: rode `make firered_switch TESTBUILD=1`"
    return None


def test_jogo_monta_o_texto_esperado(tmp_path):
    why = _stale_test_rom()
    if why:
        pytest.skip(why)
    with open_context(str(TEST_ROM), str(TEST_ELF), str(tmp_path), "BULBASAUR") as ctx:
        box = hooks.Mailbox(ctx.controller)
        ctx.emu.frames(60)
        wrong = []
        for ivs, evs in worst_cases() + fsi.random_cases():
            got, want = box.ivev_text(ivs, evs), PAGE.text(ivs, evs)
            if got != want:
                wrong.append(f"{ivs} {evs}: '{PAGE.decode(got)}' != '{PAGE.decode(want)}'")
        assert not wrong, wrong[:3]
