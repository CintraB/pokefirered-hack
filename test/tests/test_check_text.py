"""Checagem estática de textos: charmap, terminador, largura e inglês residual."""

import json
import shutil
from pathlib import Path

import pytest

from esteira.check_text import check_text, compute_baseline, fingerprint

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def repo(tmp_path):
    """Repo mínimo: charmap.txt e src/text.c reais (tabela de larguras) + textos de fixture."""
    shutil.copy(REPO_ROOT / "charmap.txt", tmp_path / "charmap.txt")
    (tmp_path / "src").mkdir()
    shutil.copy(REPO_ROOT / "src" / "text.c", tmp_path / "src" / "text.c")
    (tmp_path / "data" / "text").mkdir(parents=True)
    return tmp_path


def put(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def inc(repo, body, rel="data/text/pc.inc"):
    put(repo, rel, body)


def run(repo, exceptions=None, **kw):
    return check_text(str(repo), exceptions if exceptions is not None else {"text": []}, **kw)


def failures(results):
    return [r for r in results if r.status == "falha"]


# ---- caractere fora do charmap -------------------------------------------------------------

def test_char_outside_charmap_fails(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ação aqui$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1
    assert "caractere fora do charmap" in failed[0].detail
    assert "ã" in failed[0].detail and "Text_Fixture" in failed[0].detail


def test_accents_present_in_charmap_pass(repo):
    inc(repo, 'Text_Fixture::\n\t.string "POKéMON é ÀÉÍ à ñ ¿ ¡ …$"\n')
    assert run(repo) == []


def test_japanese_text_is_accepted_and_not_measured(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "あ" * 40 + '$"\n')
    assert run(repo) == []


def test_unknown_placeholder_fails(repo):
    inc(repo, 'Text_Fixture::\n\t.string "{NOT_A_PLACEHOLDER} oi$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "NOT_A_PLACEHOLDER" in failed[0].detail


# ---- terminador ----------------------------------------------------------------------------

def test_string_without_terminator_fails(repo):
    inc(repo, 'Text_Fixture::\n\t.string "ABC"\n')
    failed = failures(run(repo))
    assert len(failed) == 1
    assert "terminador" in failed[0].detail and "Text_Fixture" in failed[0].detail


def test_terminator_only_needed_at_end_of_block(repo):
    inc(repo, 'Text_A::\n\t.string "AB\\n"\n\t.string "CD\\p"\n\t.string "EF$"\n\n'
              'Text_B::\n\t.string "GH$"\n')
    assert run(repo) == []


def test_each_block_is_checked_separately(repo):
    inc(repo, 'Text_A::\n\t.string "AB$"\n\nText_B::\n\t.string "CD"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "Text_B" in failed[0].detail


def test_terminator_not_required_in_c_strings(repo):
    put(repo, "src/strings.c", 'const u8 gText_A[] = _("ABC");\n')
    assert run(repo) == []


def test_ifdef_branches_stay_in_one_block_and_are_checked_separately(repo):
    inc(repo, 'Text_Fixture::\n#ifdef BUGFIX @ comentário\n\t.string "Ação\\n"\n#else\n'
              '\t.string "{FONT_NORMAL}ok\\n"\n#endif\n\t.string "fim$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1  # um bloco só (terminador ok), e só o ramo BUGFIX tem 'ã'
    assert "'ã'" in failed[0].detail


def test_ifdef_does_not_mix_widths_of_the_two_branches(repo):
    # cada ramo tem 30 'A' (180 px) sem quebra antes do texto comum; somados passariam de 208
    inc(repo, 'Text_Fixture::\n#ifdef X\n\t.string "' + "A" * 30 + '"\n#else\n\t.string "' + "A" * 30 +
              '"\n#endif\n\t.string "$"\n')
    assert run(repo) == []


# ---- largura -------------------------------------------------------------------------------

def test_wide_line_fails(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1
    assert "largura" in failed[0].detail and "208" in failed[0].detail


def test_line_exactly_at_limit_passes_and_one_more_fails(repo):
    # 'A' mede 6 px: 34 * 6 = 204; + 'i' (4 px) = 208 passa; + 'A' = 214 falha
    inc(repo, 'Text_Ok::\n\t.string "' + "A" * 34 + 'i$"\n\n'
              'Text_Bad::\n\t.string "' + "A" * 35 + 'i$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "Text_Bad" in failed[0].detail


def test_width_is_measured_per_line_between_breaks(repo):
    # 3 linhas de 30 'A' (180 px) separadas por \n, \l e \p: cada uma cabe
    line = "A" * 30
    inc(repo, f'Text_Fixture::\n\t.string "{line}\\n"\n\t.string "{line}\\l"\n'
              f'\t.string "{line}\\p"\n\t.string "{line}$"\n')
    assert run(repo) == []


def test_line_continues_across_string_directives(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "A" * 20 + '"\n\t.string "' + "A" * 20 + '$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "largura" in failed[0].detail


def test_player_and_rival_count_as_seven_wide_chars(repo):
    # 42 px de {PLAYER} + 27 'A' (162 px) = 204 passa; 28 'A' = 210 falha
    inc(repo, 'Text_Ok::\n\t.string "{PLAYER}' + "A" * 27 + '$"\n\n'
              'Text_Bad::\n\t.string "{RIVAL}' + "A" * 28 + '$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "Text_Bad" in failed[0].detail


def test_control_placeholders_have_zero_width(repo):
    body = "{COLOR RED}{SHADOW LIGHT_RED}" + "A" * 34 + "i{PAUSE 0x20}{STR_VAR_1}{PLAY_BGM MUS_OBTAIN_BADGE}"
    inc(repo, f'Text_Fixture::\n\t.string "{body}$"\n')
    assert run(repo) == []


def test_glyph_placeholder_counts_its_glyph_width(repo):
    # {PKMN} = bytes 53 54 (8 + 8 px): 24 'A' = 144 + 16 = 160 passa; 33 'A' + 16 = 214 falha
    inc(repo, 'Text_Ok::\n\t.string "{PKMN}' + "A" * 24 + '$"\n\n'
              'Text_Bad::\n\t.string "{PKMN}' + "A" * 33 + '$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "Text_Bad" in failed[0].detail


# ---- exceções ------------------------------------------------------------------------------

def frozen(repo, label=None, rule=None, file="data/text/pc.inc"):
    """Exceções congeladas (com fingerprint) dos problemas atuais, filtradas por rótulo/regra."""
    return {"text": [e for e in compute_baseline(str(repo))
                     if e["file"] == file and label in (None, e["label"]) and rule in (None, e["rule"])]}


def test_listed_exception_silences_exactly_that_item(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ação$"\n\nText_Other::\n\t.string "Ação$"\n')
    failed = failures(run(repo, frozen(repo, "Text_Fixture", "charmap")))
    assert len(failed) == 1 and "Text_Other" in failed[0].detail


def test_exception_is_per_rule(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ação"\n')  # charmap + terminador
    failed = failures(run(repo, frozen(repo, rule="charmap")))
    assert len(failed) == 1 and "terminador" in failed[0].detail


def test_exception_silences_everything_for_all_three_rules(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ação' + "W" * 60 + '"\n')
    exceptions = frozen(repo)
    assert {e["rule"] for e in exceptions["text"]} == {"charmap", "terminador", "largura"}
    assert run(repo, exceptions) == []


def test_width_exception_records_measured_value_and_fingerprint(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 40 + '$"\n')
    (exc,) = frozen(repo)["text"]
    assert exc["rule"] == "largura" and exc["valor"] == 240
    assert exc["fingerprint"] == fingerprint(("W" * 40 + "$",))


def test_exception_applies_while_text_is_unchanged(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n')
    exceptions = frozen(repo)
    assert run(repo, exceptions) == []
    assert run(repo, exceptions) == []  # estável entre rodadas


def test_changed_text_that_still_overflows_fails_again(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n')
    exceptions = frozen(repo)
    inc(repo, 'Text_Fixture::\n\t.string "' + "M" * 50 + '$"\n')  # outro texto, ainda largo demais
    results = run(repo, exceptions)
    assert len(failures(results)) == 1 and "largura" in failures(results)[0].detail
    assert [r.name for r in results if r.status == "aviso"] == ["texto/obsoleta"]


def test_changed_text_that_now_fits_is_ok_and_exception_is_reported_obsolete(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n')
    exceptions = frozen(repo)
    inc(repo, 'Text_Fixture::\n\t.string "curto$"\n')
    results = run(repo, exceptions)
    assert failures(results) == []
    assert len(results) == 1 and results[0].status == "aviso" and results[0].name == "texto/obsoleta"
    assert "Text_Fixture" in results[0].detail and "mudou" in results[0].detail


def test_exception_for_missing_label_is_reported_obsolete(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n')
    exceptions = frozen(repo)
    inc(repo, 'Text_Other::\n\t.string "oi$"\n')
    results = run(repo, exceptions)
    assert len(results) == 1 and results[0].name == "texto/obsoleta" and "não existe mais" in results[0].detail


def test_exception_whose_problem_is_gone_without_text_change_is_obsolete(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n')
    exceptions = frozen(repo)
    exceptions["text"][0]["valor"] = 999  # medida congelada diferente da atual
    results = run(repo, exceptions)
    assert len(failures(results)) == 1  # o achado volta a valer
    assert any(r.name == "texto/obsoleta" for r in results)


def test_baseline_roundtrip_is_clean(repo):
    inc(repo, 'Text_A::\n\t.string "Ação' + "W" * 60 + '"\n\nText_B::\n\t.string "ok$"\n')
    put(repo, "src/data/text/quest_log.h", 'const u8 gText_Q[] = _("' + "W" * 60 + '");\n')
    baseline = {"text": compute_baseline(str(repo))}
    assert len(baseline["text"]) == 4
    assert run(repo, baseline) == []


def test_exceptions_dict_without_text_key_is_accepted(repo):
    inc(repo, 'Text_Fixture::\n\t.string "ABC$"\n')
    assert run(repo, {}) == []


# ---- largura por fonte ---------------------------------------------------------------------

def test_source_without_known_window_is_not_width_checked(repo):
    inc(repo, 'Text_Fixture::\n\t.string "' + "W" * 60 + '$"\n', rel="data/text/help_system.inc")
    put(repo, "src/strings.c", 'const u8 gText_Menu[] = _("' + "W" * 60 + '");\n')
    put(repo, "src/data/text/move_names.h", 'const u8 gX[] = _("' + "W" * 60 + '");\n')
    assert run(repo) == []


def test_skipped_source_still_gets_charmap_and_terminator_checks(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ação"\n', rel="data/text/help_system.inc")
    assert len(failures(run(repo))) == 2


def test_item_description_limit_is_200(repo):
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_OK", "description_english": "A" * 33},       # 198 px
        {"itemId": "ITEM_BAD", "description_english": "A" * 34},      # 204 px
    ]}))
    failed = failures(run(repo))
    assert len(failed) == 1 and "ITEM_BAD" in failed[0].detail and "limite 200" in failed[0].detail


def test_quest_log_limit_is_238(repo):
    put(repo, "src/data/text/quest_log.h",
        'const u8 gText_Ok[] = _("' + "A" * 39 + '");\nconst u8 gText_Bad[] = _("' + "A" * 40 + '");\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "gText_Bad" in failed[0].detail and "limite 238" in failed[0].detail


def test_start_menu_description_label_is_measured_in_strings_c(repo):
    put(repo, "src/strings.c",
        'const u8 gStartMenuDesc_Bag[] = _("' + "A" * 40 + '");\n'      # 240 > 238
        'const u8 gText_Other[] = _("' + "A" * 60 + '");\n')            # sem janela conhecida
    failed = failures(run(repo))
    assert len(failed) == 1 and "gStartMenuDesc_Bag" in failed[0].detail


def test_gas_if_else_endif_branches_stay_in_one_block(repo):
    inc(repo, 'Text_Fixture::\n\t.string "linha\\n"\n\t.if REVISION < 1\n\t.string "ramo um$"\n'
              '\t.else\n\t.string "ramo dois$"\n\t.endif\n\nText_Next::\n\t.string "ok$"\n')
    assert run(repo) == []


def test_gas_branch_without_terminator_still_fails(repo):
    inc(repo, 'Text_Fixture::\n\t.if REVISION < 1\n\t.string "ramo um$"\n\t.else\n\t.string "ramo dois"\n\t.endif\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "terminador" in failed[0].detail


# ---- outras fontes de texto ----------------------------------------------------------------

def test_map_text_inc_is_scanned(repo):
    put(repo, "data/maps/Foo/text.inc", 'Foo_Text_A::\n    .string "Ação$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and failed[0].detail.startswith("data/maps/Foo/text.inc")


def test_c_string_with_concatenated_literals_and_escapes(repo):
    put(repo, "src/data/text/fixture.h",
        'const u8 gText_Multi[] = _(\n'
        '    "Primeira linha\\n"\n'
        '    "segunda linha\\p"\n'
        '    "terceira$");\n'
        'const u8 gText_Bad[] = _("Ação");\n')
    failed = failures(run(repo))
    assert len(failed) == 1
    assert "gText_Bad" in failed[0].detail and failed[0].detail.startswith("src/data/text/fixture.h")


def test_c_string_array_entry_uses_index_as_label(repo):
    put(repo, "src/data/text/fixture.h",
        'const u8 gNames[3][8] = {\n    [MOVE_A] = _("OK"),\n    [MOVE_B] = _("Ação"),\n};\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "MOVE_B" in failed[0].detail


def test_c_comments_are_ignored(repo):
    put(repo, "src/strings.c", '// _("Ação")\n/* _("Ação") */\nconst u8 gText_A[] = _("ok"); // _("Ação")\n')
    assert run(repo) == []


def test_c_long_line_in_strings_c(repo):
    put(repo, "src/data/text/quest_log.h", 'const u8 gText_Wide[] = _("' + "W" * 60 + '");\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "largura" in failed[0].detail


def test_items_json_description(repo):
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_A", "description_english": "linha um\\nlinha dois"},
        {"itemId": "ITEM_B", "description_english": "Ação\\n" + "W" * 60},
    ]}, ensure_ascii=False))
    failed = failures(run(repo))
    assert {("charmap" in r.detail, "largura" in r.detail) for r in failed} == {(True, False), (False, True)}
    assert all("ITEM_B" in r.detail for r in failed)


def test_missing_sources_are_not_an_error(repo):
    assert run(repo) == []


# ---- inglês residual -----------------------------------------------------------------------

def test_english_check_is_off_by_default(repo):
    inc(repo, 'Text_Fixture::\n\t.string "You are the best$"\n')
    assert run(repo) == []


def test_english_check_warns_for_unaccented_english(repo):
    inc(repo, 'Text_Fixture::\n\t.string "You are the best$"\n')
    results = run(repo, english_check=True)
    assert [r.status for r in results] == ["aviso"]
    assert "inglês" in results[0].detail and "Text_Fixture" in results[0].detail


def test_english_check_ignores_accented_strings_but_not_poke_accent(repo):
    inc(repo, 'Text_Pt::\n\t.string "Você é o melhor and the$"\n\n'
              'Text_En::\n\t.string "The POKéMON you have$"\n')
    results = run(repo, english_check=True)
    assert len(results) == 1 and "Text_En" in results[0].detail


def test_english_check_accepts_portuguese_without_accents(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Oi, eu sou o PROF. CARVALHO$"\n')
    assert run(repo, english_check=True) == []


def test_english_exception_is_respected(repo):
    inc(repo, 'Text_Fixture::\n\t.string "You are the best$"\n')
    exceptions = {"text": [{"file": "data/text/pc.inc", "label": "Text_Fixture", "rule": "ingles",
                            "fingerprint": fingerprint(("You are the best$",))}]}
    assert run(repo, exceptions, english_check=True) == []


# ---- repo real -----------------------------------------------------------------------------

def test_real_repo_has_no_unfrozen_failures():
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    results = check_text(str(REPO_ROOT), exceptions)
    assert results == [], [r.detail for r in results[:5]]  # nem falha nova, nem exceção obsoleta
