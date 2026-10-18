"""Regras da tradução que comparam com a base inglesa: `controle` (códigos de controle e
placeholders) e `glossario` (variante proibida e termo inglês do glossário que sobrou).

Cada teste monta um repositório git mínimo: o commit inicial é a "base" (o texto em inglês) e a
árvore de trabalho é a tradução.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from esteira.check_text import TRANSLATION_BASE, check_text, fingerprint

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git")


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
    put(tmp_path, "data/text/pc.inc",
        'Text_Hello::\n\t.string "Hello, {PLAYER}!\\n"\n\t.string "Take this {STR_VAR_1}.\\p"\n'
        '\t.string "{COLOR RED}Bye!$"\n\n'
        'Text_Ball::\n\t.string "Here is a POKé BALL.$"\n\n'
        'Text_Two::\n\t.string "{STR_VAR_1} gave {STR_VAR_2} to you.$"\n')
    put(tmp_path, "src/battle_message.c",
        'static const u8 sText_Gained[] = _("{B_BUFF1} gained{B_BUFF2}\\n{B_BUFF3} EXP. Points!\\p");\n')
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return tmp_path


def run(repo, exceptions=None):
    return check_text(str(repo), exceptions if exceptions is not None else {"text": []},
                      base=git(repo, "rev-parse", "HEAD"), english="desligado")


def failures(results, rule=None):
    return [r for r in results if r.status == "falha" and (rule is None or r.name == f"texto/{rule}")]


def translate(repo, hello=None, ball=None, two=None, gained=None):
    hello = hello or 'Olá, {PLAYER}!\\n"\n\t.string "Pegue este {STR_VAR_1}.\\p"\n\t.string "{COLOR RED}Tchau!$'
    ball = ball or "Aqui está uma Poké Bola.$"
    two = two or "{STR_VAR_1} deu {STR_VAR_2} a você.$"
    put(repo, "data/text/pc.inc", f'Text_Hello::\n\t.string "{hello}"\n\nText_Ball::\n\t.string "{ball}"\n\n'
        f'Text_Two::\n\t.string "{two}"\n')
    if gained is not None:
        put(repo, "src/battle_message.c", f'static const u8 sText_Gained[] = _("{gained}");\n')


# ---- controle ------------------------------------------------------------------------------

def test_untouched_english_passes(repo):
    assert run(repo) == []


def test_faithful_translation_passes(repo):
    translate(repo, gained="{B_BUFF1} ganhou{B_BUFF2}\\n{B_BUFF3} PE!\\p")
    assert run(repo) == []


def test_lost_placeholder_fails(repo):
    translate(repo, hello='Olá!\\n"\n\t.string "Pegue este {STR_VAR_1}.\\p"\n\t.string "{COLOR RED}Tchau!$')
    (failed,) = failures(run(repo))
    assert failed.name == "texto/controle"
    assert failed.detail.startswith("data/text/pc.inc: Text_Hello:") and "{PLAYER}" in failed.detail


def test_extra_or_swapped_control_code_fails(repo):
    translate(repo, two="{STR_VAR_1} deu {STR_VAR_3} a você.$")
    (failed,) = failures(run(repo))
    assert "{STR_VAR_2}" in failed.detail and "{STR_VAR_3}" in failed.detail


def test_lost_battle_placeholder_in_c_fails(repo):
    translate(repo, gained="{B_BUFF1} ganhou\\n{B_BUFF3} PE!\\p")
    (failed,) = failures(run(repo))
    assert failed.detail.startswith("src/battle_message.c: sText_Gained:") and "{B_BUFF2}" in failed.detail


def test_lost_terminator_fails_controle_too(repo):
    translate(repo, ball="Aqui está uma Poké Bola.")
    assert {r.name for r in failures(run(repo))} == {"texto/controle", "texto/terminador"}


def test_line_breaks_may_change(repo):
    translate(repo, hello='Olá, {PLAYER}! Pegue\\n"\n\t.string "este {STR_VAR_1}.\\l"\n\t.string '
                          '"Mais uma linha\\p{COLOR RED}Tchau!$',
              two="{STR_VAR_1}\\ndeu {STR_VAR_2}\\pa você.$")
    assert run(repo) == []


def test_placeholders_may_change_order(repo):
    translate(repo, two="Você recebeu {STR_VAR_2} de {STR_VAR_1}.$")
    assert run(repo) == []


def test_new_label_has_nothing_to_compare(repo):
    put(repo, "data/text/pc.inc", (repo / "data/text/pc.inc").read_text(encoding="utf-8")
        + '\nText_New::\n\t.string "Texto novo.$"\n')
    assert run(repo) == []


def test_controle_exception_is_respected(repo):
    translate(repo, two="{STR_VAR_1} deu a você.$")
    exc = {"text": [{"file": "data/text/pc.inc", "label": "Text_Two", "rule": "controle",
                     "fingerprint": fingerprint(("{STR_VAR_1} deu a você.$",))}]}
    assert run(repo, exc) == []


def test_without_git_there_is_no_base_and_no_complaint(tmp_path):
    shutil.copy(REPO_ROOT / "charmap.txt", tmp_path / "charmap.txt")
    (tmp_path / "src").mkdir()
    shutil.copy(REPO_ROOT / "src" / "text.c", tmp_path / "src" / "text.c")
    put(tmp_path, "data/text/pc.inc", 'Text_A::\n\t.string "Oi.$"\n')
    assert check_text(str(tmp_path), {"text": []}, english="desligado") == []


def test_unknown_base_is_an_aviso_of_both_rules(repo):
    results = check_text(str(repo), {"text": []}, base="0123456789abcdef0123", english="desligado")
    assert [(r.name, r.status) for r in results] == [("texto/controle", "aviso"), ("texto/glossario", "aviso")]
    assert all("base" in r.detail and "não rodou" in r.detail for r in results)


def test_broken_git_is_an_aviso_not_silence(repo):
    # ex.: worktree com `gitdir:` absoluto do Windows que o git do WSL não resolve
    shutil.rmtree(repo / ".git")
    (repo / ".git").write_text("gitdir: C:/nao/existe/.git/worktrees/x\n", encoding="utf-8")
    results = check_text(str(repo), {"text": []}, english="desligado")
    assert [(r.name, r.status) for r in results] == [("texto/controle", "aviso"), ("texto/glossario", "aviso")]
    assert "git" in results[0].detail


def test_missing_base_object_counts_as_new_labels(repo):
    sha = git(repo, "rev-parse", "HEAD:data/text/pc.inc")
    (repo / ".git" / "objects" / sha[:2] / sha[2:]).unlink()
    translate(repo, ball="Aqui está uma Pokébola.$", two="{STR_VAR_1} deu a você.$")
    results = run(repo)
    # sem o original não há controle (o {STR_VAR_2} perdido passa), mas o glossário roda
    assert [r.name for r in failures(results)] == ["texto/glossario"]


def test_pipeline_base_is_the_hack_switch_commit_before_translation():
    assert TRANSLATION_BASE == "3a8d861f513f0805d586532acd56b7e2065b89ff"     # 3a8d861f5


def test_real_repo_has_the_base():
    """A worktree/checkout real tem o commit base: _load_base devolve a base (não None/motivo)."""
    from esteira.check_text import _Base, _load_base
    assert isinstance(_load_base(REPO_ROOT, TRANSLATION_BASE, {}), _Base)
    results = check_text(str(REPO_ROOT), {"text": []}, english="desligado")
    assert not [r for r in results if r.name in ("texto/controle", "texto/glossario")]


def test_glyph_macros_are_not_control_codes(repo):
    put(repo, "data/text/pc.inc", (repo / "data/text/pc.inc").read_text(encoding="utf-8")
        + '\nText_Lv::\n\t.string "{LV_2}5 {PKMN} {COLOR RED}ok$"\n')
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "lv")
    put(repo, "data/text/pc.inc", (repo / "data/text/pc.inc").read_text(encoding="utf-8")
        .replace("{LV_2}5 {PKMN} {COLOR RED}ok", "Nv.5 Pokémon {COLOR RED}ok"))
    assert failures(run(repo)) == []
    put(repo, "data/text/pc.inc", (repo / "data/text/pc.inc").read_text(encoding="utf-8")
        .replace("Nv.5 Pokémon {COLOR RED}ok", "Nv.5 Pokémon ok"))
    (failed,) = failures(run(repo))
    assert "{COLOR RED}" in failed.detail


# ---- glossário -----------------------------------------------------------------------------

def test_forbidden_variant_in_translated_text_fails(repo):
    translate(repo, ball="Aqui está uma Pokébola.$")
    (failed,) = failures(run(repo))
    assert failed.name == "texto/glossario" and "Pokébola" in failed.detail and "Poké Bola" in failed.detail


def test_leftover_english_glossary_term_in_translated_text_fails(repo):
    translate(repo, ball="Aqui está uma POKé BALL.$")
    (failed,) = failures(run(repo))
    assert failed.name == "texto/glossario" and "POKé BALL" in failed.detail and "Poké Bola" in failed.detail


def test_hp_in_translated_ui_text_fails(repo):
    translate(repo, gained="{B_BUFF1} recuperou{B_BUFF2}\\n{B_BUFF3} HP!\\p")
    (failed,) = failures(run(repo))
    assert "HP" in failed.detail and "PS" in failed.detail


def test_professor_oak_is_forbidden(repo):
    translate(repo, ball="O Professor Oak deu uma Poké Bola.$")
    (failed,) = failures(run(repo))
    assert "Professor Oak" in failed.detail and "Carvalho" in failed.detail


def test_untranslated_english_text_is_not_a_glossary_finding(repo):
    # o texto da base continua igual: o inglês dele é assunto da regra `ingles`, não do glossário
    assert failures(run(repo), "glossario") == []


def test_correct_terms_pass(repo):
    translate(repo, ball="O Prof. Carvalho deu uma Poké Bola\\ne uma Poção. Seus PS subiram!$")
    assert run(repo) == []


def test_glossary_exception_is_respected(repo):
    translate(repo, ball="Aqui está uma Pokébola.$")
    exc = {"text": [{"file": "data/text/pc.inc", "label": "Text_Ball", "rule": "glossario",
                     "fingerprint": fingerprint(("Aqui está uma Pokébola.$",))}]}
    assert run(repo, exc) == []
