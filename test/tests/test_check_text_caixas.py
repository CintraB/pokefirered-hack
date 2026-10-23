"""Linhas por caixa no diálogo padrão (escopo 9 da T4, achado da revisão da E2): a caixa de
mensagem tem 4 tiles de altura = 2 linhas (src/new_menu_helpers.c:36-44); uma 3ª linha numa caixa
(dois `\\n` antes do próximo `\\p`, ou `\\n` depois de `\\l`) é cortada sem aviso. Medido no texto
mudado em relação à base inglesa, sem piorar a base (repositório git mínimo, como em
test_check_text_traducao.py).
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from esteira.check_text import box_lines, check_text, rule_for

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git")

# Os dois casos reais da E2, em inglês como na base (4115d3050)
LETS_GO_EN = ('gOakSpeech_Text_LetsGo::\n    .string "{PLAYER}!\\p"\n    .string "Your very own POKéMON legend is\\n"\n'
              '    .string "about to unfold!\\p"\n    .string "A world of dreams and adventures\\n"\n'
              '    .string "with POKéMON awaits! Let\'s go!$"\n')
DODRIO_EN = ('Text_DodrioBerryPickingInfo::\n\t.string "“DODRIO BERRY-PICKING”\\p"\n'
             '\t.string "Command DODRIO\'s three heads to\\n"\n\t.string "catch falling BERRIES.\\p"\n'
             '\t.string "To play this game, you must have\\n"\n\t.string "a DODRIO.$"\n')


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def put(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    shutil.copy(REPO_ROOT / "charmap.txt", tmp_path / "charmap.txt")
    (tmp_path / "src").mkdir()
    shutil.copy(REPO_ROOT / "src" / "text.c", tmp_path / "src" / "text.c")
    put(tmp_path, "data/text/new_game_intro.inc", LETS_GO_EN)
    put(tmp_path, "data/scripts/cable_club.inc", DODRIO_EN)
    put(tmp_path, "data/text/pc.inc", 'Text_Three::\n\t.string "One\\nTwo\\nThree.$"\n')
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return tmp_path


def run(repo):
    return check_text(str(repo), {"text": []}, base=git(repo, "rev-parse", "HEAD"), english="desligado")


def box_failures(results):
    return [r.detail for r in results if r.status == "falha" and r.name == "texto/linhas"]


def test_box_lines_counts_like_the_dialog_box():
    assert box_lines("Uma linha.$") == 1
    assert box_lines("Uma\\nDuas.$") == 2
    assert box_lines("Uma\\nDuas\\lTrês rola.\\lQuatro rola.$") == 2
    assert box_lines("Uma\\nDuas\\nTrês.$") == 3                 # dois \n na mesma caixa
    # \l rola e mantém a linha (src/text.c:872-879): na 1ª linha não conta como 2ª
    assert box_lines("Uma\\lDuas\\nTrês.$") == 2
    assert box_lines("Uma\\nDuas\\lTrês\\nQuatro.$") == 3       # \n depois de \l na 2ª linha
    assert box_lines("Uma\\nDuas\\pTrês\\nQuatro.$") == 2        # \p abre caixa nova
    assert box_lines("Uma\\nDuas\\n$") == 2                      # quebra no fim não abre linha


def test_dialog_rules_have_two_lines_per_box():
    for file, label in (("data/maps/PalletTown/text.inc", "PalletTown_Text_X"), ("data/scripts/cable_club.inc", "X"),
                        ("data/text/new_game_intro.inc", "gOakSpeech_Text_LetsGo"), ("data/event_scripts.s", "X")):
        assert rule_for(file, label).box_lines == 2, file


def test_english_untouched_passes(repo):
    assert box_failures(run(repo)) == []


def test_lets_go_with_three_lines_in_a_box_fails(repo):
    put(repo, "data/text/new_game_intro.inc",
        'gOakSpeech_Text_LetsGo::\n    .string "{PLAYER}!\\p"\n    .string "Sua própria lenda Pokémon\\n"\n'
        '    .string "está para começar!\\p"\n    .string "Um mundo de sonhos e aventuras\\n"\n'
        '    .string "com Pokémon espera por você!\\n"\n    .string "Vamos lá!$"\n')
    found = box_failures(run(repo))
    assert len(found) == 1 and "gOakSpeech_Text_LetsGo" in found[0] and "3 linhas" in found[0]


def test_dodrio_with_newline_after_scroll_fails(repo):
    put(repo, "data/scripts/cable_club.inc",
        'Text_DodrioBerryPickingInfo::\n\t.string "“COLHEITA DE FRUTAS DO DODRIO”\\p"\n'
        '\t.string "Comande as três cabeças do\\n"\n\t.string "Dodrio para pegar as frutas\\l"\n'
        '\t.string "que caem do céu\\n"\n\t.string "sem parar.\\p"\n'
        '\t.string "Para jogar, você precisa\\n"\n\t.string "de um Dodrio.$"\n')
    found = box_failures(run(repo))
    assert len(found) == 1 and "Text_DodrioBerryPickingInfo" in found[0]


def test_scrolling_with_l_passes(repo):
    put(repo, "data/scripts/cable_club.inc",
        'Text_DodrioBerryPickingInfo::\n\t.string "“COLHEITA DE FRUTAS DO DODRIO”\\p"\n'
        '\t.string "Comande as três cabeças do\\n"\n\t.string "Dodrio para pegar as frutas\\l"\n'
        '\t.string "que caem do céu.\\p"\n\t.string "Para jogar, você precisa\\n"\n\t.string "de um Dodrio.$"\n')
    assert box_failures(run(repo)) == []


def test_english_that_already_has_three_lines_may_keep_them(repo):
    """Critério da base: o inglês de Text_Three já tem 3 linhas numa caixa; a tradução com 3 passa,
    com 4 reprova."""
    put(repo, "data/text/pc.inc", 'Text_Three::\n\t.string "Um\\nDois\\nTrês.$"\n')
    assert box_failures(run(repo)) == []
    put(repo, "data/text/pc.inc", 'Text_Three::\n\t.string "Um\\nDois\\nTrês\\nQuatro.$"\n')
    found = box_failures(run(repo))
    assert len(found) == 1 and "a base inglesa ia a 3" in found[0]


def test_new_label_is_strict(repo):
    put(repo, "data/text/pc.inc", 'Text_Three::\n\t.string "One\\nTwo\\nThree.$"\n\n'
        'Text_New::\n\t.string "Um\\nDois\\nTrês.$"\n')
    found = box_failures(run(repo))
    assert len(found) == 1 and "Text_New" in found[0]


def test_known_finding_is_an_aviso_until_fixed(repo, monkeypatch):
    """Achado já mergeado com dona (KNOWN_FINDINGS): aviso enquanto o texto for o mesmo; corrigido,
    vira aviso de obsoleto; mudado e ainda errado, volta a reprovar."""
    from esteira import check_text as ct
    put(repo, "data/text/pc.inc", 'Text_Three::\n\t.string "Um\\nDois\\nTrês\\nQuatro.$"\n')
    fp = ct.fingerprint(("Um\\nDois\\nTrês\\nQuatro.$",))
    monkeypatch.setattr(ct, "KNOWN_FINDINGS", [ct.KnownFinding("data/text/pc.inc", "Text_Three", "linhas", fp, 4,
                                                               "frente X")])
    results = run(repo)
    assert box_failures(results) == []
    assert any(r.status == "aviso" and "(conhecido: frente X)" in r.detail for r in results)
    put(repo, "data/text/pc.inc", 'Text_Three::\n\t.string "Um\\nDois\\lTrês.$"\n')
    assert any("não ocorre mais" in r.detail for r in run(repo))
    put(repo, "data/text/pc.inc", 'Text_Three::\n\t.string "Um\\nDois\\nTrês\\nQuatro!$"\n')
    assert len(box_failures(run(repo))) == 1
