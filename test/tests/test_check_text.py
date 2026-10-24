"""Checagem estática de textos: fontes, charmap, terminador, janelas (largura, linhas, letras) e
inglês residual. As regras que comparam com a base inglesa estão em test_check_text_traducao.py."""

import json
import re
import shutil
from pathlib import Path

import pytest

from esteira.check_text import (ENGLISH_MODE, ITEM_NAME_MAX_CHARS, WIDTH_RULES, _sources, check_text,
                                compute_baseline, english_report, fingerprint, rule_for)
from esteira.result import Result

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
    inc(repo, 'Text_Fixture::\n\t.string "Ažžo aqui$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1
    assert "caractere fora do charmap" in failed[0].detail
    assert "ž" in failed[0].detail and "Text_Fixture" in failed[0].detail


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
    inc(repo, 'Text_Fixture::\n#ifdef BUGFIX @ comentário\n\t.string "Ažžo\\n"\n#else\n'
              '\t.string "{FONT_NORMAL}ok\\n"\n#endif\n\t.string "fim$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1  # um bloco só (terminador ok), e só o ramo BUGFIX tem 'ã'
    assert "'ž'" in failed[0].detail


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
    # sem base inglesa (pasta sem .git) o {STR_VAR_1} mede 0: o pior caso só vale para texto mudado
    # em relação à base (test_check_text_traducao.py)
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
    inc(repo, 'Text_Fixture::\n\t.string "Ažžo$"\n\nText_Other::\n\t.string "Ažžo$"\n')
    failed = failures(run(repo, frozen(repo, "Text_Fixture", "charmap")))
    assert len(failed) == 1 and "Text_Other" in failed[0].detail


def test_exception_is_per_rule(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ažžo"\n')  # charmap + terminador
    failed = failures(run(repo, frozen(repo, rule="charmap")))
    assert len(failed) == 1 and "terminador" in failed[0].detail


def test_exception_silences_everything_for_all_three_rules(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ažžo' + "W" * 60 + '"\n')
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
    inc(repo, 'Text_A::\n\t.string "Ažžo' + "W" * 60 + '"\n\nText_B::\n\t.string "ok$"\n')
    put(repo, "src/data/text/quest_log.h", 'const u8 gText_Q[] = _("' + "W" * 60 + '");\n')
    baseline = {"text": compute_baseline(str(repo))}
    assert len(baseline["text"]) == 4
    assert run(repo, baseline) == []


def test_exceptions_dict_without_text_key_is_accepted(repo):
    inc(repo, 'Text_Fixture::\n\t.string "ABC$"\n')
    assert run(repo, {}) == []


# ---- largura por fonte ---------------------------------------------------------------------

def test_source_without_known_window_is_not_width_checked(repo):
    inc(repo, 'Text_Fixture::\n\t.braille "' + "W" * 60 + '$"\n', rel="data/text/braille.inc")
    put(repo, "src/strings.c", 'const u8 gText_Menu[] = _("' + "W" * 60 + '");\n')
    put(repo, "src/trade.c", 'static const u8 sText_X[] = _("' + "W" * 60 + '");\n')
    assert failures(run(repo)) == []


def test_skipped_source_still_gets_charmap_and_terminator_checks(repo):
    inc(repo, 'Text_Fixture::\n\t.string "Ažžo"\n', rel="data/text/new_game_intro.inc")
    put(repo, "src/trade.c", 'static const u8 sText_X[] = _("Ažžo");\n')
    assert len(failures(run(repo))) == 3


def test_item_description_limit_is_198(repo):
    # a mochila tem 200 px (x = 0), mas o item no PC de Pokémon sai em x = 2 na janela de 25 tiles
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_OK", "description_english": "A" * 33},       # 198 px
        {"itemId": "ITEM_BAD", "description_english": "A" * 33 + "i"},  # 202 px
    ]}))
    (failed,) = failures(run(repo))
    assert "ITEM_BAD" in failed.detail and "limite 198" in failed.detail


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
    put(repo, "data/maps/Foo/text.inc", 'Foo_Text_A::\n    .string "Ažžo$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and failed[0].detail.startswith("data/maps/Foo/text.inc")


def test_c_string_with_concatenated_literals_and_escapes(repo):
    put(repo, "src/data/text/fixture.h",
        'const u8 gText_Multi[] = _(\n'
        '    "Primeira linha\\n"\n'
        '    "segunda linha\\p"\n'
        '    "terceira$");\n'
        'const u8 gText_Bad[] = _("Ažžo");\n')
    failed = failures(run(repo))
    assert len(failed) == 1
    assert "gText_Bad" in failed[0].detail and failed[0].detail.startswith("src/data/text/fixture.h")


def test_c_string_array_entry_uses_index_as_label(repo):
    put(repo, "src/data/text/fixture.h",
        'const u8 gNames[3][8] = {\n    [MOVE_A] = _("OK"),\n    [MOVE_B] = _("Ažžo"),\n};\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "MOVE_B" in failed[0].detail


def test_c_comments_are_ignored(repo):
    put(repo, "src/strings.c", '// _("Ažžo")\n/* _("Ažžo") */\nconst u8 gText_A[] = _("ok"); // _("Ažžo")\n')
    assert run(repo) == []


def test_c_long_line_in_strings_c(repo):
    put(repo, "src/data/text/quest_log.h", 'const u8 gText_Wide[] = _("' + "W" * 60 + '");\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "largura" in failed[0].detail


def test_items_json_description(repo):
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_A", "description_english": "linha um\\nlinha dois"},
        {"itemId": "ITEM_B", "description_english": "Ažžo\\n" + "W" * 60},
    ]}, ensure_ascii=False))
    failed = failures(run(repo))
    assert {("charmap" in r.detail, "largura" in r.detail) for r in failed} == {(True, False), (False, True)}
    assert all("ITEM_B" in r.detail for r in failed)


def test_missing_sources_are_not_an_error(repo):
    assert run(repo) == []


# ---- inglês residual -----------------------------------------------------------------------

def english(results):
    return [r for r in results if r.name == "texto/ingles"]


def test_english_progress_is_one_aviso_with_the_total(repo):
    inc(repo, 'Text_A::\n\t.string "You are the best$"\n\nText_B::\n\t.string "Where is your bike?$"\n')
    results = run(repo, english="progresso")
    assert failures(results) == []
    (aviso,) = english(results)
    assert aviso.status == "aviso"
    assert aviso.detail.startswith("modo progresso:")
    assert "2 textos" in aviso.detail and "data/text/pc.inc" in aviso.detail


def test_english_progress_counts_words_per_file(repo):
    inc(repo, 'Text_A::\n\t.string "You are the {PLAYER}$"\n')
    put(repo, "data/maps/Foo/text.inc", 'Foo_Text::\n\t.string "Oi, você!$"\n')
    counts = english_report(str(repo))
    assert counts["data/text/pc.inc"].words == 3        # you, are, the
    assert counts["data/text/pc.inc"].texts == 1
    assert "data/maps/Foo/text.inc" not in counts


def test_portuguese_is_not_english(repo):
    inc(repo, 'Text_A::\n\t.string "Oi, eu sou o Prof. Carvalho!$"\n\n'
              'Text_B::\n\t.string "Você é o melhor Treinador de Pallet.\\nMe dê a Poké Bola.$"\n\n'
              'Text_C::\n\t.string "Come o seu lanche, que ainda há\\nmais dados no PC.$"\n')
    assert run(repo) == []


def test_to_acronym_of_original_trainer_is_not_english(repo):
    """"TO" (Treinador Original, CeladonCity_DepartmentStore_3F) não é o "to" inglês; "to" minúsculo continua sendo."""
    inc(repo, 'Text_A::\n\t.string "Nº ID e o TO.\\pTO quer dizer Treinador Original.$"\n\n'
              'Text_B::\n\t.string "Go to the shop$"\n')
    counts = english_report(str(repo))
    assert counts["data/text/pc.inc"].words == 3        # go, to, the (só o texto B)
    assert counts["data/text/pc.inc"].texts == 1


def test_to_in_all_caps_english_still_counts(repo):
    """A exceção do TO vale só em frase com letra minúscula (PT-BR) e no título Help_Text_OT: o inglês todo em
    maiúsculas ("BELONGS TO", "A WINDOW TO", "TO ME", "TO") continua sendo inglês."""
    inc(repo, 'Text_A::\n\t.string "BELONGS TO$"\n\nText_B::\n\t.string "A WINDOW TO$"\n\n'
              'Text_C::\n\t.string "TO ME$"\n\nText_D::\n\t.string "TO$"\n\n'
              'Text_E::\n\t.string "Nº ID e o TO.$"\n\nHelp_Text_OT::\n\t.string "TO$"\n')
    counts = english_report(str(repo))
    assert counts["data/text/pc.inc"].words == 4        # um "to" em cada A, B, C e D
    assert counts["data/text/pc.inc"].texts == 4        # E (frase PT) e Help_Text_OT (título) ficam de fora


def test_english_allowlist(repo):
    put(repo, "src/data/text/species_names.h", 'const u8 gSpeciesNames[][11] = {\n'
        '    [SPECIES_X] = _("WHAT"),\n};\n')
    put(repo, "src/data/trainers.h", 'const struct Trainer gTrainers[] = {\n'
        '    [TRAINER_A] = {\n        .trainerName = _("WILL"),\n    },\n};\n')
    put(repo, "src/strings.c", 'const u8 gCreditsString_Director[] = _("The director and the team");\n'
        'const u8 gJPText_X[] = _("あいう");\n')
    put(repo, "src/keyboard_text.c", 'const u8 gText_Keys[] = _("what the you");\n')
    inc(repo, 'Text_A::\n\t.string "WILL é o mais forte. WHAT apareceu!$"\n')
    assert english(run(repo)) == []


def test_english_blocking_mode_fails_per_text_and_respects_exceptions(repo):
    inc(repo, 'Text_A::\n\t.string "You are the best$"\n\nText_B::\n\t.string "Is that you?$"\n')
    failed = failures(run(repo, english="bloqueante"))
    assert sorted(r.detail.split(": ")[1] for r in failed) == ["Text_A", "Text_B"]
    assert all(r.name == "texto/ingles" for r in failed)
    exceptions = {"text": [{"file": "data/text/pc.inc", "label": "Text_A", "rule": "ingles",
                            "fingerprint": fingerprint(("You are the best$",))}]}
    failed = failures(run(repo, exceptions, english="bloqueante"))
    assert len(failed) == 1 and "Text_B" in failed[0].detail


def test_english_check_can_be_turned_off(repo):
    inc(repo, 'Text_A::\n\t.string "You are the best$"\n')
    assert run(repo, english="desligado") == []


def test_english_mode_of_the_pipeline_is_blocking():
    """Task 11 da tradução: o pipeline (`esteira/__main__._text_checks`, que chama check_text sem `english`)
    reprova texto com inglês."""
    assert ENGLISH_MODE == "bloqueante"
    import inspect
    from esteira import __main__ as cli
    assert "check_text(str(REPO_ROOT), exceptions)" in inspect.getsource(cli._text_checks)


def test_new_english_in_a_translated_text_fails_the_build(repo):
    """Inglês que volta (ou sobra) num texto já traduzido é falha no modo padrão do pipeline, e só nesse texto."""
    inc(repo, 'Text_A::\n\t.string "Você ganhou a Insígnia!$"\n\n'
              'Text_B::\n\t.string "Você ganhou the badge!$"\n')
    results = run(repo)
    (failed,) = failures(results)
    assert failed.name == "texto/ingles" and failed.detail.startswith("data/text/pc.inc: Text_B: ")
    assert "the" in failed.detail
    assert [r for r in results if r.status != "falha"] == []      # nada de aviso de progresso


# exceções congeladas do inglês no repo real: as mensagens de depuração (test_traducao_e.E3_DEBUG_ENGLISH)
DEBUG_ENGLISH = {("src/sprite.c", "sDmaOverErrorMsg"), ("src/battle_anim_status_effects.c", "sText_TaskOver")}


def _real_english_exceptions():
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    return [e for e in exceptions["text"] if e["rule"] == "ingles"]


def test_english_exceptions_are_only_the_debug_messages():
    frozen = _real_english_exceptions()
    assert {(e["file"], e["label"]) for e in frozen} == DEBUG_ENGLISH
    assert all(len(e["fingerprint"]) == 16 and "valor" not in e and e.get("obs") for e in frozen)


@pytest.fixture
def debug_repo(repo):
    """Fixture com os dois .c reais das mensagens de depuração (o fingerprint congelado bate)."""
    for rel, _label in DEBUG_ENGLISH:
        put(repo, rel, (REPO_ROOT / rel).read_text(encoding="utf-8"))
    return repo


def test_debug_english_exceptions_silence_only_those_labels(debug_repo):
    exceptions = {"text": _real_english_exceptions()}
    assert {(r.detail.split(": ")[0], r.detail.split(": ")[1]) for r in failures(run(debug_repo))} == DEBUG_ENGLISH
    assert run(debug_repo, exceptions) == []
    # outro texto em inglês no mesmo arquivo (ou em outro) continua reprovando
    with open(debug_repo / "src" / "sprite.c", "a", encoding="utf-8") as f:
        f.write('\nstatic const u8 sNewMsg[] = _("Press the button");\n')
    inc(debug_repo, 'Text_A::\n\t.string "Where is your bike?$"\n')
    failed = failures(run(debug_repo, exceptions))
    assert sorted(r.detail.split(": ")[1] for r in failed) == ["Text_A", "sNewMsg"]
    assert all(r.name == "texto/ingles" for r in failed)


def test_debug_english_exception_goes_obsolete_when_the_text_changes(debug_repo):
    rel = debug_repo / "src" / "battle_anim_status_effects.c"
    source = rel.read_text(encoding="utf-8")
    assert '_("TASK OVER\\n' in source
    rel.write_text(source.replace('_("TASK OVER\\n', '_("TASK IS OVER\\n'), encoding="utf-8")
    results = run(debug_repo, {"text": _real_english_exceptions()})
    (failed,) = failures(results)
    assert failed.name == "texto/ingles" and "sText_TaskOver" in failed.detail
    (obsolete,) = [r for r in results if r.name == "texto/obsoleta"]
    assert obsolete.status == "aviso" and "sText_TaskOver" in obsolete.detail and "o texto mudou" in obsolete.detail


def test_compute_baseline_freezes_english_only_in_blocking_mode(repo):
    inc(repo, 'Text_A::\n\t.string "You are the best$"\n')
    (exc,) = compute_baseline(str(repo))
    assert exc["rule"] == "ingles" and exc["label"] == "Text_A"
    assert run(repo, {"text": [exc]}) == []
    assert compute_baseline(str(repo), english="progresso") == []
    with pytest.raises(ValueError):
        compute_baseline(str(repo), english="talvez")


# ---- fontes novas --------------------------------------------------------------------------

@pytest.mark.parametrize("rel", ["data/scripts/fixture.inc", "data/event_scripts.s", "data/mystery_event_msg.s"])
def test_script_sources_are_scanned(repo, rel):
    put(repo, rel, 'Text_Fixture::\n\t.string "Ažžo$"\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and failed[0].detail.startswith(rel + ": Text_Fixture")


@pytest.mark.parametrize("rel", ["src/battle_message.c", "src/move_descriptions.c", "src/union_room_message.c",
                                 "src/data/pokemon/pokedex_text_fr.h", "src/data/ingame_trades.h",
                                 "src/data/easy_chat/easy_chat_group_actions.h", "src/trainer_tower_sets.c",
                                 "src/data/decoration/description.h", "src/berry.c", "src/trade.c"])
def test_c_sources_everywhere_in_src_are_scanned(repo, rel):
    put(repo, rel, 'static const u8 sText_Fixture[] = _("Ažžo");\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and failed[0].detail.startswith(rel + ": sText_Fixture")


def test_leafgreen_dex_text_is_not_scanned(repo):
    put(repo, "src/data/pokemon/pokedex_text_lg.h", 'const u8 gX[] = _("Ažžo");\n')
    assert run(repo) == []


@pytest.mark.parametrize("rel", ["src/data/items.h", "src/data/region_map/region_map_entry_strings.h"])
def test_headers_generated_from_json_are_not_scanned(repo, rel):
    # o build gera estes .h a partir do items.json/region_map_sections.json (.gitignore)
    put(repo, rel, 'static const u8 sX[] = _("Ažžo");\n')
    assert run(repo) == []


def test_double_underscore_macro_is_not_game_text(repo):
    put(repo, "src/naming_screen.c", 'static const u8 sKeys[][8] = {\n    __("abcdžž"),\n};\n')
    assert run(repo) == []


def test_item_name_is_scanned_with_its_own_label(repo):
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_A", "english": "Ažžo", "description_english": "ok"},
    ]}, ensure_ascii=False))
    failed = failures(run(repo))
    assert len(failed) == 1 and "ITEM_A.name" in failed[0].detail


def test_region_map_names_are_scanned(repo):
    put(repo, "src/data/region_map/region_map_sections.json", json.dumps({"map_sections": [
        {"id": "MAPSEC_A", "name": "Ažžo"}, {"id": "MAPSEC_B"},
    ]}, ensure_ascii=False))
    failed = failures(run(repo))
    assert len(failed) == 1 and failed[0].detail.startswith(
        "src/data/region_map/region_map_sections.json: MAPSEC_A")


def test_braille_accepts_only_braille_characters(repo):
    inc(repo, 'Braille_Text_A::\n\t.braille "FOI ALI, PERTO$"\n\n'
              'Braille_Text_B::\n\t.braille "AVIÃO$"\n\nBraille_Text_C::\n\t.braille "SEM FIM"\n',
        rel="data/text/braille.inc")
    failed = failures(run(repo))
    details = sorted(r.detail for r in failed)
    assert len(details) == 2
    assert "Braille_Text_B" in details[0] and "braille" in details[0] and "'Ã'" in details[0]
    assert "Braille_Text_C" in details[1] and "terminador" in details[1]


def test_struct_field_label_uses_the_enclosing_index(repo):
    put(repo, "src/data/trainers.h", 'const struct Trainer gTrainers[] = {\n'
        '    [TRAINER_A] = {\n        .trainerClass = 1,\n        .trainerName = _("Ažžo"),\n    },\n};\n')
    put(repo, "src/data/pokemon/pokedex_entries.h", 'const struct PokedexEntry gPokedexEntries[] = {\n'
        '    [NATIONAL_DEX_X] =\n    {\n        .categoryName = _("Ažžo"),\n        .height = 7,\n    },\n};\n')
    put(repo, "src/berry.c", 'const struct Berry gBerries[] = {\n'
        '    [ITEM_CHERI_BERRY - FIRST_BERRY_INDEX] =\n        {\n            .name = _("Ažžo"),\n        },\n};\n')
    labels = sorted(r.detail.split(": ")[1] for r in failures(run(repo)))
    assert labels == ["ITEM_CHERI_BERRY.name", "NATIONAL_DEX_X.categoryName", "TRAINER_A.trainerName"]


def test_positional_struct_entries_use_variable_and_counter(repo):
    put(repo, "src/data/decoration/header.h", 'const struct Decoration gDecorations[] = {\n'
        '    {\n        DECOR_NONE,\n        _("OK"),\n    }, {\n        DECOR_A,\n        _("Ažžo"),\n    },\n};\n')
    (failed,) = failures(run(repo))
    assert failed.detail.startswith("src/data/decoration/header.h: gDecorations#2:")


# ---- larguras e limites das janelas novas --------------------------------------------------

def test_battle_message_window_is_222_px(repo):
    # 'A' = 6 px: 37 = 222 cabe; 'A' * 37 + 'i' = 226 não (janela B_WIN_MSG de 28 tiles, x = 2)
    put(repo, "src/battle_message.c", 'static const u8 sText_Ok[] = _("' + "A" * 37 + '");\n'
        'static const u8 sText_Bad[] = _("' + "A" * 37 + 'i");\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "sText_Bad" in failed[0].detail and "limite 222" in failed[0].detail


def test_battle_line_of_209_px_fails_in_the_oak_tutorial_window(repo):
    # a janela do Carvalho/velho (B_WIN_OAK_OLD_MAN) tem 26 tiles e x = 0: 208 px
    line = "A" * 34 + "f"            # 204 + 5 = 209 px
    put(repo, "src/battle_message.c", f'const u8 gText_ForPetesSake[] = _("{line}");\n'
        f'static const u8 sText_Normal[] = _("{line}");\n')
    failed = failures(run(repo))
    assert len(failed) == 1 and "gText_ForPetesSake" in failed[0].detail and "209 px" in failed[0].detail


def test_battle_name_placeholders_have_the_width_of_the_longest_name(repo):
    # {B_OPPONENT_MON1_NAME} = 10 letras de 6 px = 60; "Wild " = 27 px (prefixo mais largo)
    put(repo, "src/battle_message.c", 'static const u8 sText_WildPkmnPrefix[] = _("Wild ");\n'
        'static const u8 sText_A[] = _("{B_OPPONENT_MON1_NAME}' + "A" * 27 + '");\n'          # 222
        'static const u8 sText_B[] = _("{B_OPPONENT_MON1_NAME}' + "A" * 28 + '");\n'          # 228
        'static const u8 sText_C[] = _("{B_DEF_NAME_WITH_PREFIX}' + "A" * 22 + '");\n'        # 219
        'static const u8 sText_D[] = _("{B_DEF_NAME_WITH_PREFIX}' + "A" * 23 + '");\n')       # 225
    labels = sorted(r.detail.split(": ")[1] for r in failures(run(repo)))
    assert labels == ["sText_B", "sText_D"]


def test_help_system_uses_four_pixel_spaces_and_26_tiles(repo):
    # o HelpSystemRenderText avança 4 px no espaço (src/help_system_util.c): 4 espaços = 16 px
    words = "AAAAAAA " * 4                # 4 * (42 + 4) = 184 px (seria 192 com espaço de 6)
    inc(repo, f'Help_Text_Ok::\n\t.string "{words}AAAA$"\n\nHelp_Text_Bad::\n\t.string "{words}AAAAi$"\n',
        rel="data/text/help_system.inc")
    labels = [r.detail.split(": ")[1] for r in failures(run(repo))]
    assert labels == ["Help_Text_Bad"]          # 184 + 24 = 208 cabe; + 'i' = 212 não


def test_help_system_mouseover_descriptions_are_206_px(repo):
    line = "A" * 34 + "i"     # 208 px
    inc(repo, f'Help_Text_DescExit::\n\t.string "{line}$"\n\nHelp_Text_DefineHP::\n\t.string "{line}$"\n',
        rel="data/text/help_system.inc")
    labels = [r.detail.split(": ")[1] for r in failures(run(repo))]
    assert labels == ["Help_Text_DescExit"]


def test_help_list_items_and_titles_are_one_line_of_200_px(repo):
    # perguntas, tópicos e termos: uma linha da lista em x = 8 e o título da resposta (24 px de altura)
    inc(repo, 'Help_Text_PlayingForFirstTime::\n\t.string "' + "A" * 33 + '$"\n\n'           # 198 px
              'Help_Text_WhatShouldIBeDoing::\n\t.string "' + "A" * 33 + 'i$"\n\n'           # 202 px
              'Help_Text_HP::\n\t.string "Pontos\\nde Saúde$"\n\n'                          # 2 linhas
              'Help_Text_Cancel::\n\t.string "Cancelar$"\n\n'
              'Help_Text_DefineHP::\n\t.string "' + "A" * 34 + 'i\\n2\\n3$"\n',              # resposta: 208 px
        rel="data/text/help_system.inc")
    failed = failures(run(repo))
    assert sorted(r.detail.split(": ")[1] for r in failed) == ["Help_Text_HP", "Help_Text_WhatShouldIBeDoing"]
    assert any("202 px, limite 200" in r.detail for r in failed)
    assert any("2 linhas, limite 1" in r.detail for r in failed)


def test_help_list_labels_come_from_the_help_system_tables():
    from esteira.check_text import _HELP_LIST_LABELS
    for label in ("Help_Text_WhatShouldIDo", "Help_Text_PlayingForFirstTime", "Help_Text_UsingPokedex",
                  "Help_Text_HP", "Help_Text_TheHelpSystem", "Help_Text_UsingTypeMatchupList", "Help_Text_Cancel"):
        assert label in _HELP_LIST_LABELS, label
    for label in ("Help_Text_HowToUsePokedex", "Help_Text_DefineHP", "Help_Text_DescWhatShouldIDo"):
        assert label not in _HELP_LIST_LABELS, label
        assert rule_for("data/text/help_system.inc", label).lines != 1
    assert len(_HELP_LIST_LABELS) > 100


def test_help_system_answers_have_at_most_seven_lines(repo):
    # 13 tiles de altura, linhas de 15 px e glifo de 14: 6 * 15 + 14 = 104 px
    inc(repo, 'Help_Text_A::\n\t.string "1\\n2\\n3\\n4\\n5\\n6\\n7$"\n\n'
              'Help_Text_B::\n\t.string "1\\n2\\n3\\n4\\n5\\n6\\n7\\n8$"\n', rel="data/text/help_system.inc")
    (failed,) = failures(run(repo))
    assert "Help_Text_B" in failed.detail and "8 linhas" in failed.detail and "limite 7" in failed.detail


def test_a_final_break_before_the_terminator_is_not_a_line():
    from esteira.check_text import _load_env, measure
    env = _load_env(REPO_ROOT)
    assert measure("1\\n2\\p$", env).lines == 2
    assert measure("1\\n2\\n", env).lines == 2
    assert measure("1\\n2\\n3$", env).lines == 3
    assert measure("", env).lines == 1


def test_action_prompt_names_the_players_mon_without_prefix(repo):
    # "What will\n{B_ACTIVE_NAME_WITH_PREFIX} do?": o ativo é o do jogador, sem "Wild "/"Foe "
    put(repo, "src/battle_message.c", 'static const u8 sText_WildPkmnPrefix[] = _("Wild ");\n'
        'const u8 gText_WhatWillPkmnDo[] = _("What will\\n{B_ACTIVE_NAME_WITH_PREFIX} AAAAAAA");\n'   # 60 + 48
        'const u8 gText_WhatWillBad[] = _("What will\\n{B_ACTIVE_NAME_WITH_PREFIX} AAAAAAAi");\n')    # 112
    (failed,) = failures(run(repo, english="desligado"))    # o texto de largura é o inglês original
    assert "gText_WhatWillBad" in failed.detail and "limite 110" in failed.detail


def test_fame_checker_windows(repo):
    inc(repo, 'gFameCheckerPersonName_A::\n\t.string "' + "A" * 34 + 'i$"\n\n'      # 208: sai na caixa de 208 px
              'gFameCheckerPersonName_B::\n\t.string "' + "A" * 35 + '$"\n\n'        # 210 > 208
              'gFameCheckerFlavorTextOriginLocation_A::\n\t.string "' + "A" * 16 + 'i$"\n\n'   # small: 80+4
              'gFameCheckerFlavorTextOriginObjectName_A::\n\t.string "' + "A" * 17 + '$"\n\n'  # 85 > 84
              'gFameCheckerFlavorText_A::\n\t.string "' + "A" * 34 + 'i$"\n',                # 208
        rel="data/text/fame_checker.inc")
    labels = sorted(r.detail.split(": ")[1] for r in failures(run(repo)))
    assert labels == ["gFameCheckerFlavorTextOriginObjectName_A", "gFameCheckerPersonName_B"]


def test_move_description_is_113_px_and_four_lines(repo):
    put(repo, "src/move_descriptions.c",
        'const u8 gMoveDescription_Ok[] = _("' + "A" * 18 + 'f\\n2\\n3\\n4");\n'          # 113 px, 4 linhas
        'const u8 gMoveDescription_Wide[] = _("' + "A" * 19 + '");\n'                     # 114 px
        'const u8 gMoveDescription_Tall[] = _("1\\n2\\n3\\n4\\n5");\n')
    failed = failures(run(repo))
    assert sorted(r.detail.split(": ")[1] for r in failed) == ["gMoveDescription_Tall", "gMoveDescription_Wide"]
    assert any("5 linhas, limite 4" in r.detail for r in failed)


def test_pokedex_entry_is_240_px_and_three_lines(repo):
    put(repo, "src/data/pokemon/pokedex_text_fr.h",
        'const u8 gAPokedexText[] = _("' + "A" * 40 + '\\n2\\n3");\n'                      # 240, 3 linhas
        'const u8 gBPokedexText[] = _("' + "A" * 40 + 'i");\n'
        'const u8 gCPokedexText[] = _("1\\n2\\n3\\n4");\n')
    labels = sorted(r.detail.split(": ")[1] for r in failures(run(repo)))
    assert labels == ["gBPokedexText", "gCPokedexText"]


def test_item_name_has_at_most_13_letters(repo):
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_13", "english": "Bola Presente", "description_english": "ok"},
        {"itemId": "ITEM_14", "english": "Bola Presentes", "description_english": "ok"},
    ]}, ensure_ascii=False))
    (failed,) = failures(run(repo))
    assert "ITEM_14.name" in failed.detail and "14 letras, limite 13" in failed.detail
    assert ITEM_NAME_MAX_CHARS == 13


def test_item_name_fits_the_bag_list(repo):
    # nome em x = 9 e quantidade em x = 110 na lista da bolsa: 101 px; 'A' * 13 = 78 px cabe
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_A", "english": "A" * 13, "description_english": "ok"},
    ]}))
    assert failures(run(repo)) == []


def test_item_description_has_at_most_three_lines(repo):
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_A", "english": "A", "description_english": "1\\n2\\n3\\n4"},
    ]}))
    (failed,) = failures(run(repo))
    assert "ITEM_A" in failed.detail and "4 linhas, limite 3" in failed.detail


def test_berry_description_has_at_most_two_lines(repo):
    # bolsa de frutas: janela de 4 tiles de altura com o texto em y = 2 (src/berry_pouch.c:226-233, :764)
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_CHERI_BERRY", "english": "A", "description_english": "um\\ndois"},
        {"itemId": "ITEM_PECHA_BERRY", "english": "A", "description_english": "um\\ndois\\ntrês"},
        {"itemId": "ITEM_POTION", "english": "A", "description_english": "um\\ndois\\ntrês"},
    ]}, ensure_ascii=False))
    (failed,) = failures(run(repo))
    assert "ITEM_PECHA_BERRY" in failed.detail and "3 linhas, limite 2" in failed.detail


def test_tm_description_in_items_json_is_not_shown_and_not_measured(repo):
    # o jogo mostra a descrição do golpe (gMoveDescription_*, src/data/items.json.txt:17-18)
    put(repo, "src/data/items.json", json.dumps({"items": [
        {"itemId": "ITEM_TM01", "english": "TM01", "description_english": "W" * 60 + "\\n2\\n3\\n4"},
        {"itemId": "ITEM_HM08", "english": "HM08", "description_english": "W" * 60},
        {"itemId": "ITEM_TM_CASE", "english": "A", "description_english": "W" * 60},
    ]}))
    (failed,) = failures(run(repo))
    assert "ITEM_TM_CASE" in failed.detail
    rule = rule_for("src/data/items.json", "ITEM_TM01")
    assert rule.px is None and rule.lines is None and "gMoveDescription" in rule.source
    move = rule_for("src/move_descriptions.c", "gMoveDescription_Pound")
    assert "src/tm_case.c" in move.source and move.px <= 142


@pytest.mark.parametrize("rel, decl, limit", [
    ("src/data/text/move_names.h", "[MOVE_X] = _", 12),
    ("src/data/text/abilities.h", "[ABILITY_X] = _", 12),
    ("src/data/text/trainer_class_names.h", "[TRAINER_CLASS_X] = _", 12),
    ("src/data/text/species_names.h", "[SPECIES_X] = _", 10),
])
def test_name_tables_have_letter_limits(repo, rel, decl, limit):
    put(repo, rel, 'const u8 gX[][20] = {\n'
        f'    {decl}("{"i" * limit}"),\n    {decl.replace("_X", "_Y")}("{"i" * (limit + 1)}"),\n}};\n')
    (failed,) = failures(run(repo))
    assert "_Y" in failed.detail and f"limite {limit}" in failed.detail


def test_move_names_fit_the_battle_move_window_in_small_font(repo):
    # FONT_SMALL: 'A' = 5 px; janela B_WIN_MOVE_NAME de 8 tiles, x = 0: 64 px
    put(repo, "src/data/text/move_names.h", 'const u8 gMoveNames[][13] = {\n'
        '    [MOVE_A] = _("AAAAAAAAAAAA"),\n};\n')        # 60 px
    assert failures(run(repo)) == []


@pytest.fixture
def no_ivev_page(monkeypatch):
    """A página IVs/EVs (Hack 5) lê o gTypeNames inteiro do battle_main.c: fora do repo real não."""
    monkeypatch.setattr("esteira.check_text._ivev_page_results", lambda root: [])


def test_type_names_have_six_letters(repo, no_ivev_page):
    put(repo, "src/battle_main.c", 'const u8 gTypeNames[][7] = {\n'
        '    [TYPE_A] = _("Planta"),\n    [TYPE_B] = _("Elétrico"),\n};\n')
    (failed,) = failures(run(repo))
    assert "TYPE_B" in failed.detail and "8 letras, limite 6" in failed.detail


def test_berry_name_has_six_letters(repo):
    put(repo, "src/berry.c", 'const struct Berry gBerries[] = {\n'
        '    [ITEM_A - FIRST_BERRY_INDEX] = { .name = _("CHERI"), },\n'
        '    [ITEM_B - FIRST_BERRY_INDEX] = { .name = _("CHERRYS"), },\n};\n')
    (failed,) = failures(run(repo))
    assert "ITEM_B.name" in failed.detail and "limite 6" in failed.detail


def test_ability_description_fits_the_summary_buffer(repo):
    put(repo, "src/data/text/abilities.h",
        'static const u8 sOkDescription[] = _("' + "a" * 37 + '");\n'          # 222 px, 37 letras
        'static const u8 sLongDescription[] = _("' + "i" * 52 + '");\n')       # 208 px, 52 letras
    (failed,) = failures(run(repo))
    assert "sLongDescription" in failed.detail and "52 letras, limite 51" in failed.detail


def test_map_name_fits_the_region_map_buffer_and_window(repo):
    # mapName[19]/dungeonName[19] do mapa da região: 18 letras; janela de calabouço: 108 px
    put(repo, "src/data/region_map/region_map_sections.json", json.dumps({"map_sections": [
        {"id": "MAPSEC_OK", "name": "Caverna Cerulean"},              # 16 letras
        {"id": "MAPSEC_18", "name": "i" * 18},
        {"id": "MAPSEC_FOREST", "name": "Floresta de Viridian"},      # 20 letras (108 px)
        {"id": "MAPSEC_WIDE", "name": "{PKMN}" * 7},                  # 14 bytes, 112 px
    ]}, ensure_ascii=False))
    failed = failures(run(repo))
    assert sorted(r.detail.split(": ")[1] for r in failed) == ["MAPSEC_FOREST", "MAPSEC_WIDE"]
    assert any("20 letras, limite 18" in r.detail for r in failed)
    assert any("112 px, limite 108" in r.detail for r in failed)


def test_name_choices_have_seven_letters(repo):
    inc(repo, 'gNameChoice_A::\n\t.string "GARYZZZ$"\n\ngNameChoice_B::\n\t.string "GARYZZZZ$"\n',
        rel="data/text/new_game_intro.inc")
    (failed,) = failures(run(repo))
    assert "gNameChoice_B" in failed.detail and "limite 7" in failed.detail


def test_letter_limit_counts_bytes_of_the_charmap(repo, no_ivev_page):
    # {PKMN} são 2 bytes; 4 letras + {PKMN} = 6 cabe; 5 + {PKMN} = 7 > 6
    put(repo, "src/battle_main.c", 'const u8 gTypeNames[][7] = {\n    [TYPE_A] = _("AAAA{PKMN}"),\n'
        '    [TYPE_B] = _("AAAAA{PKMN}"),\n};\n')
    (failed,) = failures(run(repo))
    assert "TYPE_B" in failed.detail


def test_clear_to_skip_and_clear_move_the_pen(repo):
    # {CLEAR_TO n} e {SKIP n} levam a caneta a n px; {CLEAR n} avança n px (src/text.c)
    inc(repo, 'Text_Ok::\n\t.string "A{CLEAR_TO 196}AA$"\n\nText_Bad::\n\t.string "A{CLEAR_TO 200}AA$"\n\n'
              'Text_Skip::\n\t.string "' + "A" * 30 + '{SKIP 0}AAAA$"\n\n'
              'Text_Clear::\n\t.string "A{CLEAR 200}AA$"\n')
    labels = sorted(r.detail.split(": ")[1] for r in failures(run(repo)))
    assert labels == ["Text_Bad", "Text_Clear"]


def test_teachy_tv_menu_and_script_windows(repo):
    put(repo, "src/data/text/teachy_tv.h",
        'const u8 gTeachyTvString_Ok[] = _("' + "A" * 28 + '");\n'                # 168 px
        'const u8 gTeachyTvString_Bad[] = _("' + "A" * 29 + '");\n'
        'const u8 gTeachyTvText_Ok[] = _("' + "A" * 34 + 'i");\n')                # 208 px
    (failed,) = failures(run(repo))
    assert "gTeachyTvString_Bad" in failed.detail


# ---- regras de largura: cobertura e citações -----------------------------------------------

def _cited_lines(source):
    return re.findall(r"((?:src|data|include)/[\w./-]+\.(?:c|h|inc|s)):(\d+)(?:-(\d+))?", source)


def test_every_measured_rule_cites_existing_lines_of_the_window():
    for rule in WIDTH_RULES:
        if rule.px is None and rule.lines is None and rule.chars is None:
            assert rule.source.strip(), rule      # sem janela: o motivo fica documentado
            continue
        cited = _cited_lines(rule.source)
        assert cited, f"regra sem citação arquivo:linha: {rule}"
        for path, first, last in cited:
            lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
            assert int(last or first) <= len(lines), (rule.pattern, path, first)


def test_window_citations_point_at_the_templates():
    def cited_text(rule):
        out = []
        for path, first, last in _cited_lines(rule.source):
            lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
            out += lines[int(first) - 1:int(last or first)]
        return "\n".join(out)
    battle = rule_for("src/battle_message.c", "sText_Anything")
    assert battle.px == 222 and ".width = 28" in cited_text(battle) and ".x = 2" in cited_text(battle)
    oak = rule_for("src/battle_message.c", "gText_ForPetesSake")
    assert oak.px == 208 and ".width = 26" in cited_text(oak)
    dex = rule_for("src/data/pokemon/pokedex_text_fr.h", "gBulbasaurPokedexText")
    assert dex.px == 240 and dex.lines == 3 and ".width = 30" in cited_text(dex)
    popup = rule_for("src/data/region_map/region_map_sections.json", "MAPSEC_PALLET_TOWN")
    assert popup.px == 108 and popup.chars == 18
    assert "u8 mapName[19];" in cited_text(popup) and ".width = 15" in cited_text(popup)
    assert "12, 2" in cited_text(popup)               # x = 12 do nome de calabouço
    item = rule_for("src/data/items.json", "ITEM_POTION.name")
    assert item.chars == ITEM_NAME_MAX_CHARS and "ITEM_NAME_LENGTH 14" in cited_text(item)
    assert "[19]" in cited_text(item) and "item_X = 9" in cited_text(item) and "0x6e" in cited_text(item)
    desc = rule_for("src/data/items.json", "ITEM_POTION")
    assert desc.px == 198 and desc.lines == 3
    assert ".width = 25" in cited_text(desc) and ".height = 6" in cited_text(desc)
    assert "description, 2, 0" in cited_text(desc)          # PC de Pokémon: x = 2
    berry = rule_for("src/data/items.json", "ITEM_CHERI_BERRY")
    assert berry.px == 198 and berry.lines == 2
    assert ".height = 4" in cited_text(berry) and "str, 0, 2" in cited_text(berry)
    move = rule_for("src/move_descriptions.c", "gMoveDescription_Pound")
    assert move.px == 113 and move.lines == 4 and ".width = 15" in cited_text(move) and "7, 42" in cited_text(move)
    help_ = rule_for("data/text/help_system.inc", "Help_Text_DefineHP")
    assert help_.px == 208 and help_.space == 4 and "x += 4" in cited_text(help_)


def test_every_text_of_the_real_repo_has_a_rule():
    """Nenhuma fonte cai fora das regras: sem janela determinável é regra explícita com o motivo."""
    orphans = sorted({(e.file, e.label) for e in _sources(REPO_ROOT)
                      if not isinstance(e, Result) and rule_for(e.file, e.label) is None})
    assert orphans == [], orphans[:10]


def test_real_berry_and_tm_rules_match_exactly_their_pockets():
    """A regra de fruta (2 linhas) pega toda fruta da bolsa de frutas, e a de MT/MO (sem tela)
    pega só os itens do estojo de MT."""
    items = json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]
    for item in items:
        rule = rule_for("src/data/items.json", item["itemId"])
        assert (rule.lines == 2) == (item["pocket"] == "POCKET_BERRY_POUCH"), item["itemId"]
        assert (rule.px is None) == (item["pocket"] == "POCKET_TM_CASE"), item["itemId"]


def test_real_repo_scans_all_sources():
    files = {e.file for e in _sources(REPO_ROOT) if not isinstance(e, Result)}
    for rel in ("data/event_scripts.s", "data/mystery_event_msg.s", "data/scripts/cable_club.inc",
                "src/battle_message.c", "src/battle_main.c", "src/move_descriptions.c",
                "src/data/pokemon/pokedex_text_fr.h", "src/data/pokemon/pokedex_entries.h", "src/berry.c",
                "src/data/decoration/header.h", "src/union_room_message.c", "src/data/text/teachy_tv.h",
                "src/data/region_map/region_map_sections.json", "src/data/easy_chat/easy_chat_group_actions.h",
                "src/trainer_tower_sets.c", "src/data/ingame_trades.h", "src/data/trainers.h",
                "data/text/braille.inc", "src/data/items.json"):
        assert rel in files, rel
    assert "src/data/pokemon/pokedex_text_lg.h" not in files


def test_cli_reports(repo, capsys):
    from esteira.check_text import main
    inc(repo, 'Text_A::\n\t.string "You are the {PLAYER}$"\n')
    assert main(["--ingles", "--repo", str(repo)]) == 0
    out = capsys.readouterr().out
    assert "data/text/pc.inc" in out and "total: 3 palavras em 1 textos" in out
    assert main(["--regras", "--repo", str(repo)]) == 0
    out = capsys.readouterr().out
    assert "data/text/pc.inc" in out and "px 208" in out and "textos: largura 1" in out


# ---- repo real -----------------------------------------------------------------------------

def test_real_repo_has_no_unfrozen_failures():
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    # os achados conhecidos (esteira/buffers.KNOWN_OVERFLOWS, check_text.KNOWN_FINDINGS) são aviso de
    # propósito, como uma exceção congelada que ainda vale; o obsoleto ("não ocorre mais") continua contando
    # o inglês entra (modo bloqueante): as mensagens de depuração congeladas calam, nada mais sobra
    results = [r for r in check_text(str(REPO_ROOT), exceptions)
               if not (r.status == "aviso" and "(conhecido:" in r.detail)]
    assert results == [], [r.detail for r in results[:5]]  # nem falha nova, nem exceção obsoleta


def test_real_repo_english_without_exceptions_is_only_the_debug_messages():
    """Sem as exceções, a regra `ingles` acusa só as duas mensagens de depuração (e é falha, não aviso)."""
    english_results = [r for r in check_text(str(REPO_ROOT), {"text": []}) if r.name == "texto/ingles"]
    assert all(r.status == "falha" for r in english_results)
    assert {tuple(r.detail.split(": ")[:2]) for r in english_results} == DEBUG_ENGLISH
