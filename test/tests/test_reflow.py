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


def test_old_breaks_are_redone():
    text = "Quer que eu cure\\nos seus Pokémon para\\lque fiquem em plena forma?$"
    assert reflow(text, 208) == "Quer que eu cure os seus Pokémon\\npara que fiquem em plena forma?$"


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
    new, done = reflow_inc(source, None, None, None, "dialogo", None, "data/maps/X/text.inc")
    assert done == ["X_Text_A"]
    assert '"Quer que eu cure os seus Pokémon\\n"' in new
    # a ajuda mede o espaço com 4 px (regra de data/text/help_system.inc)
    help_src = 'Help_Text_A::\n\t.string "' + "AAAAAAA " * 4 + 'AAAA$"\n'
    new, _ = reflow_inc(help_src, None, None, None, "linhas", None, "data/text/help_system.inc")
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
        'Text_A::\n\t.string "Quer que eu cure os seus Pokémon\\n"\n\t.string "para que fiquem em plena forma?$"\n\n'
        'Text_B::\n\t.string "Fica\\nigual.$"\n')


def test_cli_without_write_only_prints(tmp_path):
    inc = tmp_path / "text.inc"
    original = 'Text_A::\n\t.string "Quer que eu cure\\n"\n\t.string "os seus Pokémon.$"\n'
    inc.write_text(original, encoding="utf-8")
    done = run_cli("--largura", "208", str(inc))
    assert done.returncode == 0, done.stderr
    assert "Quer que eu cure os seus Pokémon.$" in done.stdout
    assert inc.read_text(encoding="utf-8") == original


def test_cli_rejects_unknown_label(tmp_path):
    inc = tmp_path / "text.inc"
    inc.write_text('Text_A::\n\t.string "Oi.$"\n', encoding="utf-8")
    done = run_cli("--largura", "208", str(inc), "--rotulo", "Text_X")
    assert done.returncode != 0 and "Text_X" in done.stderr
