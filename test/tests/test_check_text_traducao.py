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
    translate(repo, two="Recebeu {STR_VAR_2} de {STR_VAR_1}.$")
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


def test_unknown_base_is_an_aviso_of_the_three_rules(repo):
    results = check_text(str(repo), {"text": []}, base="0123456789abcdef0123", english="desligado")
    assert [(r.name, r.status) for r in results] == [("texto/controle", "aviso"), ("texto/glossario", "aviso"),
                                                     ("texto/largura", "aviso"), ("texto/buffer", "aviso")]
    assert all("base" in r.detail and "não rodou" in r.detail for r in results)
    assert "pior caso" in results[2].detail


def test_broken_git_is_an_aviso_not_silence(repo):
    # ex.: worktree com `gitdir:` absoluto do Windows que o git do WSL não resolve
    shutil.rmtree(repo / ".git")
    (repo / ".git").write_text("gitdir: C:/nao/existe/.git/worktrees/x\n", encoding="utf-8")
    results = check_text(str(repo), {"text": []}, english="desligado")
    assert [(r.name, r.status) for r in results] == [("texto/controle", "aviso"), ("texto/glossario", "aviso"),
                                                     ("texto/largura", "aviso"), ("texto/buffer", "aviso")]
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


# ---- largura no pior caso dos placeholders variáveis ({STR_VAR_n}, {B_BUFF*}...) -----------
# 'A' = 6 px, 'i' = 4, espaço = 6; {STR_VAR_n}/{B_BUFF*} medem 10 letras de 6 px = 60 px.

def with_base(repo, base, rel="data/text/route23.inc", label="Text_Var", extra=""):
    """Grava `label` com o texto `base` (inglês) e commita: vira a base dos testes."""
    put(repo, rel, f'{label}::\n\t.string "{base}"\n' + extra)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base var")
    return git(repo, "rev-parse", "HEAD")


def run_base(repo, base_sha, exceptions=None):
    return check_text(str(repo), exceptions if exceptions is not None else {"text": []}, base=base_sha,
                      english="desligado")


def test_str_var_line_that_fits_at_zero_but_not_with_a_ten_letter_name_fails(repo):
    sha = with_base(repo, "{STR_VAR_1} AAAA.$")
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} ' + "A" * 30 + '$"\n')   # 186 / 246
    (failed,) = failures(run_base(repo, sha))
    assert failed.name == "texto/largura" and "Text_Var" in failed.detail
    assert "pior caso" in failed.detail and "246 px" in failed.detail and "limite 208" in failed.detail
    assert "{STR_VAR_1} = 10 letras" in failed.detail


def test_translation_may_overflow_up_to_what_the_english_base_already_did(repo):
    sha = with_base(repo, "{STR_VAR_1} " + "A" * 28 + "$")                       # 174 / 234: o inglês já estoura
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} ' + "A" * 27 + 'i$"\n')  # 232
    assert failures(run_base(repo, sha)) == []
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} ' + "A" * 29 + '$"\n')   # 240
    (failed,) = failures(run_base(repo, sha))
    assert "240 px" in failed.detail and "234" in failed.detail


def test_the_base_allowance_does_not_excuse_a_line_that_overflows_without_names(repo):
    sha = with_base(repo, "{STR_VAR_1} " + "A" * 28 + "$")                       # base: 234 no pior caso
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} oi\\n' + "A" * 35 + '$"\n')  # 210 fixo
    (failed,) = failures(run_base(repo, sha))
    assert "210 px" in failed.detail and "pior caso" not in failed.detail


def test_untouched_english_that_overflows_in_the_worst_case_is_the_base(repo):
    sha = with_base(repo, "{STR_VAR_1} " + "A" * 28 + "$",
                    extra='\nText_Other::\n\t.string "Hello.$"\n')
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} ' + "A" * 28 + '$"\n'
        '\nText_Other::\n\t.string "Olá.$"\n')                                      # arquivo mudado, rótulo igual
    assert failures(run_base(repo, sha)) == []


def test_new_label_without_english_is_measured_strictly(repo):
    sha = with_base(repo, "Hello.$")
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "Olá.$"\n'
        '\nText_New::\n\t.string "{STR_VAR_2} ' + "A" * 25 + '$"\n')                 # 156 / 216
    (failed,) = failures(run_base(repo, sha))
    assert "Text_New" in failed.detail and "216 px" in failed.detail


def test_battle_buffers_are_measured_in_the_worst_case(repo):
    base_sha = git(repo, "rev-parse", "HEAD")
    translate(repo, gained="{B_BUFF1} " + "A" * 20 + "{B_BUFF2}\\n{B_BUFF3} PE!\\p")   # 126 / 246 > 222
    (failed,) = failures(run_base(repo, base_sha))
    assert failed.detail.startswith("src/battle_message.c: sText_Gained:") and "246 px" in failed.detail
    assert "limite 222" in failed.detail
    translate(repo, gained="{B_BUFF1} " + "A" * 16 + "{B_BUFF2}\\n{B_BUFF3} PE!\\p")    # 222
    assert failures(run_base(repo, base_sha)) == []


def test_context_declares_a_number_or_an_item_name(repo, monkeypatch):
    from esteira import janelas_uso
    sha = with_base(repo, "{STR_VAR_1} AAAA.$")
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} ' + "A" * 28 + '$"\n')   # 174
    assert len(failures(run_base(repo, sha))) == 1                                  # 10 letras: 234
    number = janelas_uso.VarContent("data/text/route23.inc", "Text_Var", "STR_VAR_1", 5,
                                    "número de 5 algarismos (src/x.c:1)", digits=True)
    monkeypatch.setattr(janelas_uso, "VAR_CONTENTS", [number])
    assert failures(run_base(repo, sha)) == []                                      # 5 algarismos: 204
    item = number._replace(chars=13, digits=False, source="nome de item (src/x.c:1)")
    monkeypatch.setattr(janelas_uso, "VAR_CONTENTS", [item])
    (failed,) = failures(run_base(repo, sha))
    assert "252 px" in failed.detail and "{STR_VAR_1} = 13 letras" in failed.detail
    other = number._replace(label="Text_Outro")                                    # outro rótulo: não vale
    monkeypatch.setattr(janelas_uso, "VAR_CONTENTS", [other])
    assert len(failures(run_base(repo, sha))) == 1


def test_dynamic_placeholder_is_measured_in_the_worst_case(repo):
    # {DYNAMIC n} recebe espécie, apelido, jogador ou gStringVar1 (src/quest_log_events.c:1026, :1320);
    # janela do Quest Log: 238 px
    rel = "src/data/text/quest_log.h"
    put(repo, rel, 'const u8 gText_QL_X[] = _("{DYNAMIC 0x00} ' + "A" * 33 + '");\n')    # 204 / 264
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base ql")
    sha = git(repo, "rev-parse", "HEAD")
    put(repo, rel, 'const u8 gText_QL_X[] = _("{DYNAMIC 0x00} ' + "A" * 32 + 'i");\n')   # 262: não piora
    assert failures(run_base(repo, sha)) == []
    put(repo, rel, 'const u8 gText_QL_X[] = _("{DYNAMIC 0x00} ' + "A" * 34 + '");\n')    # 210 / 270
    (failed,) = failures(run_base(repo, sha))
    assert "gText_QL_X" in failed.detail and "270 px" in failed.detail and "limite 238" in failed.detail
    assert "{DYNAMIC} = 10 letras" in failed.detail and "264" in failed.detail
    put(repo, rel, 'const u8 gText_QL_X[] = _("Olá, {DYNAMIC 0x00}!");\nconst u8 gText_QL_New[] = _("{DYNAMIC 0x01} '
        + "A" * 30 + '");\n')                                                               # novo: 246
    (failed,) = failures(run_base(repo, sha))
    assert "gText_QL_New" in failed.detail and "246 px" in failed.detail


def test_worst_case_finding_can_be_frozen_like_any_width_finding(repo):
    from esteira.check_text import compute_baseline
    sha = with_base(repo, "{STR_VAR_1} AAAA.$")
    put(repo, "data/text/route23.inc", 'Text_Var::\n\t.string "{STR_VAR_1} ' + "A" * 30 + '$"\n')
    (exc,) = compute_baseline(str(repo), base=sha)
    assert exc["rule"] == "largura" and exc["valor"] == 246
    assert failures(run_base(repo, sha, {"text": [exc]})) == []
