"""reflow: refaz as quebras \\n/\\l/\\p de um texto medindo com as larguras do jogo."""

import subprocess
import sys
from pathlib import Path

import pytest

from esteira.reflow import line_widths, reflow

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_known_sentence_breaks_where_the_line_is_full():
    # "Quer que eu cure os seus Pokémon" mede 185 px; com " para" passaria de 208
    text = "Boas-vindas ao Centro Pokémon!\\pQuer que eu cure os seus Pokémon para que fiquem em plena forma?$"
    assert reflow(text, 208) == ("Boas-vindas ao Centro Pokémon!\\p"
                                 "Quer que eu cure os seus Pokémon\\npara que fiquem em plena forma?$")


def test_old_breaks_are_redone_when_forced():
    text = "Quer que eu cure\\nos seus Pokémon para\\lque fiquem em plena forma?$"
    assert reflow(text, 208, forcar=True) == "Quer que eu cure os seus Pokémon\\npara que fiquem em plena forma?$"


def test_box_that_fits_is_left_alone():
    text = "Quer que eu cure\\nos seus Pokémon para\\lque fiquem em plena forma?$"
    assert reflow(text, 208) == text


def test_route_sign_keeps_its_lines():
    sign = "ROUTE 1\\nPALLET TOWN - VIRIDIAN CITY$"
    assert reflow(sign, 208) == sign
    pt = "ROTA 1\\nCIDADE DE PALLET - CIDADE DE VIRIDIAN ADIANTE$"      # a 2ª linha estoura
    out = reflow(pt, 208)
    assert out.startswith("ROTA 1\\nCIDADE DE PALLET")       # a linha que cabe fica
    assert max(line_widths(out)) <= 208


def test_help_list_keeps_items_and_hanging_indent():
    text = ("{CIRCLE_1} Escolha “POKéDEX” no MENU.\\n"
            "{CIRCLE_2} Escolha Pokémon usando os comandos como\\n"
            "   “LISTA DE POKéMON”, “HABITATS DE POKéMON” e “BUSCA” no topo.\\n"
            "{CIRCLE_3} Escolha um Pokémon.$")
    out = reflow(text, 208, estilo="linhas", espaco=4)
    lines = out.rstrip("$").split("\\n")
    assert [line[:10] for line in lines if line.startswith("{")] == ["{CIRCLE_1}", "{CIRCLE_2}", "{CIRCLE_3}"]
    start, end = 1, next(i for i, line in enumerate(lines) if line.startswith("{CIRCLE_3}"))
    item2 = lines[start:end]
    assert len(item2) >= 3
    assert all(line.startswith("   ") and not line.startswith("    ") for line in item2[1:])
    assert max(line_widths(out, espaco=4)) <= 208


def test_forced_reflow_of_a_real_help_answer_keeps_the_list():
    text = ("{CIRCLE_1} Select “POKéDEX” on the MENU.\\n"
            "{CIRCLE_2} Choose POKéMON using commands such\\n"
            "   as “POKéMON LIST,”\\n"
            "   “HABITATS OF POKéMON,” and\\n"
            "   “SEARCH.”\\n"
            "{CIRCLE_3} Select a POKéMON to obtain detailed\\n"
            "   information.$")                 # Help_Text_HowToUsePokedex
    assert reflow(text, 208, estilo="linhas", espaco=4) == text      # cabe: intacto
    out = reflow(text, 208, estilo="linhas", espaco=4, forcar=True)
    lines = out.rstrip("$").split("\\n")
    assert [line[:10] for line in lines if line.startswith("{")] == ["{CIRCLE_1}", "{CIRCLE_2}", "{CIRCLE_3}"]
    assert all(line.startswith(("{", "   ")) for line in lines)
    assert out.replace("\\n", " ").split() == text.replace("\\n", " ").split()


def test_indented_line_outside_a_list_stays_a_line():
    text = "Ajuda:\\n  Usar a BOLSA para guardar itens e outras coisas mais que não cabem$"
    out = reflow(text, 208)
    assert out.split("\\n")[1].startswith("  Usar a BOLSA")


def test_double_spaces_are_kept():
    text = "Os tipos de  Pokémon e golpes estão listados aqui em ordem alfabética e numérica$"
    assert "de  Pokémon" in reflow(text, 208)


def test_third_line_of_a_box_scrolls_with_l():
    words = " ".join(["AAAA"] * 30)            # 7 palavras (204 px) por linha: 5 linhas
    out = reflow(words + "$", 208)
    assert out.count("\\n") == 1 and out.count("\\l") == 3 and "\\p" not in out
    assert out.index("\\n") < out.index("\\l")


def test_every_line_fits_and_no_word_is_lost():
    text = ("Eu subestimei você e, por isso, perdi. Como prova da sua vitória, eu lhe concedo… "
            "a Insígnia Rocha oficial da Liga Pokémon.\\p$")
    out = reflow(text, 208)
    assert max(line_widths(out)) <= 208
    flat = out.replace("\\n", " ").replace("\\l", " ")
    assert flat.split() == text.split()


def test_greedy_lines_cannot_take_the_next_word():
    out = reflow("um dois três quatro cinco seis sete oito nove dez onze doze treze catorze$", 100)
    lines = out.replace("\\l", "\\n").rstrip("$").split("\\n")
    for line, nxt in zip(lines, lines[1:]):
        assert line_widths(line + " " + nxt.split()[0])[0] > 100


def test_player_counts_as_seven_wide_letters():
    # {PLAYER} = 42 px; cada " AAAA" = 30: 42 + 5 * 30 = 192 cabe; a sexta (222) não
    out = reflow("{PLAYER} " + "AAAA " * 5 + "AAAA$", 208)
    assert out == "{PLAYER} AAAA AAAA AAAA AAAA AAAA\\nAAAA$"


def test_control_codes_stay_attached_and_in_place():
    text = "Você recebeu {COLOR RED}{STR_VAR_1}{COLOR DARK_GRAY} de {PLAYER}!{PAUSE 0x20}\\p$"
    assert reflow(text, 208) == text
    narrow = reflow(text, 100)
    assert narrow.replace("\\n", " ").replace("\\l", " ") == text


def test_paragraphs_are_kept():
    assert reflow("Um.\\pDois.\\pTrês.$", 208) == "Um.\\pDois.\\pTrês.$"


def test_word_wider_than_the_window_gets_its_own_line():
    out = reflow("a " + "W" * 50 + " b$", 100)
    assert out == "a\\n" + "W" * 50 + "\\lb$"


def test_lines_style_uses_only_newlines():
    out = reflow(" ".join(["AAAA"] * 24), 208, estilo="linhas")
    assert "\\l" not in out and out.count("\\n") == 3


def test_small_font_is_narrower():
    text = " ".join(["AAAA"] * 10)
    assert len(line_widths(reflow(text, 100, fonte="small"))) < len(line_widths(reflow(text, 100)))


def test_line_widths_measures_like_the_game():
    assert line_widths("AAAA\\nAA i$") == [24, 22]
    assert line_widths("{PLAYER}") == [42]


def test_inc_without_width_uses_the_window_of_the_rule():
    from esteira.reflow import reflow_inc
    source = 'X_Text_A::\n\t.string "Quer que eu cure\\n"\n\t.string "os seus Pokémon para que fiquem em plena forma?$"\n'
    new, done, _ = reflow_inc(source, None, None, None, "dialogo", None, "data/maps/X/text.inc")
    assert done == ["X_Text_A"]
    # a 1ª linha cabe e fica; da 2ª, só o excesso desce
    assert '"Quer que eu cure\\n"' in new and '"os seus Pokémon para que fiquem em\\l"' in new
    # a ajuda mede o espaço com 4 px (regra de data/text/help_system.inc)
    help_src = 'Help_Text_A::\n\t.string "' + "AAAAAAA " * 4 + 'AAAA$"\n'
    new, _, _ = reflow_inc(help_src, None, None, None, "linhas", None, "data/text/help_system.inc")
    assert "\\n" not in new              # 208 px com espaços de 4 cabe numa linha só


# ---- CLI -----------------------------------------------------------------------------------

def run_cli(*args, cwd=REPO_ROOT / "test"):
    return subprocess.run([sys.executable, "-m", "esteira.reflow", *args], cwd=cwd,
                          capture_output=True, text=True, timeout=60)


def test_cli_reflows_a_text_argument():
    done = run_cli("--largura", "208", "--texto", "Quer que eu cure os seus Pokémon para que fiquem em plena forma?$")
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "Quer que eu cure os seus Pokémon\\npara que fiquem em plena forma?$"


def test_cli_rewrites_one_label_of_an_inc_file(tmp_path):
    inc = tmp_path / "text.inc"
    inc.write_text('Text_A::\n\t.string "Quer que eu cure\\n"\n\t.string "os seus Pokémon para que fiquem em plena forma?$"\n\n'
                   'Text_B::\n\t.string "Fica\\nigual.$"\n', encoding="utf-8")
    done = run_cli("--largura", "208", str(inc), "--rotulo", "Text_A", "--escrever")
    assert done.returncode == 0, done.stderr
    assert inc.read_text(encoding="utf-8") == (
        'Text_A::\n\t.string "Quer que eu cure\\n"\n\t.string "os seus Pokémon para que fiquem em\\l"\n'
        '\t.string "plena forma?$"\n\n'
        'Text_B::\n\t.string "Fica\\nigual.$"\n')
    done = run_cli("--largura", "208", str(inc), "--rotulo", "Text_A", "--escrever", "--forcar")
    assert done.returncode == 0, done.stderr
    assert inc.read_text(encoding="utf-8").startswith(
        'Text_A::\n\t.string "Quer que eu cure os seus Pokémon\\n"\n\t.string "para que fiquem em plena forma?$"\n')


def test_cli_leaves_labels_that_fit_untouched(tmp_path):
    inc = tmp_path / "text.inc"
    sign = 'Sign_Text::\n    .string "ROUTE 1\\n"\n    .string "PALLET TOWN - VIRIDIAN CITY$"\n'
    inc.write_text(sign + '\nText_Long::\n    .string "Quer que eu cure os seus Pokémon para que fiquem '
                   'em plena forma?$"\n', encoding="utf-8")
    done = run_cli("--largura", "208", str(inc), "--escrever")
    assert done.returncode == 0, done.stderr
    assert "Text_Long" in done.stdout and "Sign_Text" not in done.stdout
    new = inc.read_text(encoding="utf-8")
    assert new.startswith(sign)
    assert '    .string "Quer que eu cure os seus Pokémon\\n"' in new


def test_cli_without_write_only_prints(tmp_path):
    inc = tmp_path / "text.inc"
    original = 'Text_A::\n\t.string "Quer que eu cure\\n"\n\t.string "os seus Pokémon.$"\n'
    inc.write_text(original, encoding="utf-8")
    done = run_cli("--largura", "208", str(inc), "--forcar")
    assert done.returncode == 0, done.stderr
    assert "Quer que eu cure os seus Pokémon.$" in done.stdout
    assert inc.read_text(encoding="utf-8") == original


def test_cli_rejects_unknown_label(tmp_path):
    inc = tmp_path / "text.inc"
    inc.write_text('Text_A::\n\t.string "Oi.$"\n', encoding="utf-8")
    done = run_cli("--largura", "208", str(inc), "--rotulo", "Text_X")
    assert done.returncode != 0 and "Text_X" in done.stderr
