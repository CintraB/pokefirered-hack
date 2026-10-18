"""Janela pelo uso: textos do src/strings.c (e dos outros .c) medidos na janela onde o rótulo é
usado (esteira/janelas_uso.py + check_text)."""

import re
import shutil
from collections import Counter
from pathlib import Path

import pytest

from esteira.check_text import check_text, coverage_kind, effective_rules
from esteira.janelas_uso import MENU_CALL, USAGE_RULES, c_contexts, match, repo_uses

REPO_ROOT = Path(__file__).resolve().parents[2]
W60 = "W" * 60


def put(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    shutil.copy(REPO_ROOT / "charmap.txt", tmp_path / "charmap.txt")
    (tmp_path / "src").mkdir()
    shutil.copy(REPO_ROOT / "src" / "text.c", tmp_path / "src" / "text.c")
    return tmp_path


def failures(results):
    return [r for r in results if r.status == "falha"]


def run(repo):
    return check_text(str(repo), {"text": []}, english="desligado")


# ---- contexto do uso -----------------------------------------------------------------------

def test_contexts_of_calls_tables_and_code():
    src = ('static const struct MenuAction sStartMenuActionTable[] = {\n'
           '    [STARTMENU_BAG] = { gText_MenuBag, {.u8_void = Cb} },\n};\n'
           'static const struct X sInfo[] = {\n    {\n        .id = 1,\n        .desc = gText_Desc\n    },\n};\n'
           'void F(void)\n{\n    DisplayPartyMenuMessage(gText_Msg, TRUE);\n    str = gText_Code;\n'
           '    // gText_Comment\n    Foo("gText_Literal");\n}\n'
           'extern const u8 gText_Declared[];\n')
    ctx = c_contexts(src, {"gText_MenuBag", "gText_Desc", "gText_Msg", "gText_Code", "gText_Comment",
                           "gText_Literal", "gText_Declared"})
    assert ctx == {"gText_MenuBag": {"table:sStartMenuActionTable"}, "gText_Desc": {"table:sInfo.desc"},
                   "gText_Msg": {"call:DisplayPartyMenuMessage"}, "gText_Code": {"code"}}


def test_first_matching_usage_rule_wins():
    assert match("src/start_menu.c", "table:sStartMenuActionTable").px == 48
    assert match("src/data/party_menu.h", "table:sCursorOptions").px == 72
    assert match("src/data/party_menu.h", "table:sActionStringTable", "gText_DoWhatWithPokemon").px == 128
    assert match("src/data/party_menu.h", "table:sActionStringTable", "gText_ChoosePokemon").px == 168
    assert match("src/easy_chat_2.c", "table:sEasyChatScreenTemplates.titleText").px == 128     # campo próprio
    assert match("src/easy_chat_2.c", "table:sEasyChatScreenTemplates.confirmText1").px == 176  # a tabela
    assert match("src/nada_aqui.c", "code") is None


# ---- checagem ------------------------------------------------------------------------------

def strings_c(repo, *labels_texts):
    put(repo, "src/strings.c", "".join(f'const u8 {label}[] = _("{text}");\n' for label, text in labels_texts))


def test_strings_c_label_is_measured_in_the_window_where_it_is_used(repo):
    strings_c(repo, ("gText_MenuBag", "Bolsa"), ("gText_MenuWide", "MOCHILAS!"), ("gText_Summary", "Resumo"),
              ("gText_SummaryWide", "Resumo e mais"))
    put(repo, "src/start_menu.c", 'static const struct MenuAction sStartMenuActionTable[] = {\n'
        '    [A] = { gText_MenuBag, {.u8_void = Cb} },\n    [B] = { gText_MenuWide, {.u8_void = Cb} },\n};\n')
    put(repo, "src/data/party_menu.h", 'static const struct X sCursorOptions[] = {\n'
        '    [A] = {gText_Summary, Cb},\n    [B] = {gText_SummaryWide, Cb},\n};\n')
    failed = failures(run(repo))
    assert sorted(r.detail.split(": ")[1] for r in failed) == ["gText_MenuWide", "gText_SummaryWide"]
    wide = next(r for r in failed if "gText_MenuWide" in r.detail)
    assert "limite 48 px" in wide.detail and "janela de src/start_menu.c, table:sStartMenuActionTable" in wide.detail


def test_label_used_in_two_windows_must_fit_both(repo):
    strings_c(repo, ("gText_Cancel", "Cancelar tudo"))          # 76 px: cabe no grupo, não no menu Start
    put(repo, "src/start_menu.c", 'static const struct MenuAction sStartMenuActionTable[] = {\n'
        '    [A] = { gText_Cancel, {.u8_void = Cb} },\n};\n')
    put(repo, "src/party_menu.c", 'void F(void)\n{\n    DisplayPartyMenuMessage(gText_Cancel, TRUE);\n}\n')
    (failed,) = failures(run(repo))
    assert "limite 48 px" in failed.detail
    rules = effective_rules(str(repo))[("src/strings.c", "gText_Cancel")]
    assert sorted(r.px for r in rules) == [48, 224]


def test_unused_label_is_dead_text_without_width(repo):
    strings_c(repo, ("gText_Dead", W60))
    put(repo, "src/x.c", 'extern const u8 gText_Dead[];\n')
    assert failures(run(repo)) == []
    (rule,) = effective_rules(str(repo))[("src/strings.c", "gText_Dead")]
    assert rule.px is None and "texto morto" in rule.source


def test_assignment_is_a_use(repo):
    strings_c(repo, ("gText_Assigned", W60))
    put(repo, "src/start_menu.c", 'void F(void)\n{\n    str = gText_Assigned;\n}\n')
    (failed,) = failures(run(repo))
    assert "limite 208 px" in failed.detail                     # padrão do menu Start: o diálogo


def test_residue_struct_field_and_repeated_labels_use_the_owner(repo):
    put(repo, "src/trade.c", 'static const struct T sTpl = {\n    .playerName = _("' + W60 + '"),\n};\n'
        'static const u8 *const sNames[] = {\n    _("ok"),\n    _("' + W60 + '"),\n};\n'
        'void F(void)\n{\n    Use(&sTpl);\n    Use(sNames[i]);\n}\n')
    labels = sorted(r.detail.split(": ")[1] for r in failures(run(repo)))
    assert labels == ["sNames#2", "sTpl.playerName"]


def test_easy_chat_words_fit_the_word_column(repo):
    put(repo, "src/data/easy_chat/easy_chat_group_actions.h",
        'static const u8 sEasyChatWord_Ok[] = _("ENCONTRA");\nstatic const u8 sEasyChatWord_Bad[] = _("' + "W" * 18
        + '");\nconst struct EasyChatWordInfo gEasyChatGroup_Actions[] = {\n'
        '    { .text = sEasyChatWord_Ok, },\n    { .text = sEasyChatWord_Bad, },\n};\n')
    (failed,) = failures(run(repo))
    assert "sEasyChatWord_Bad" in failed.detail and "limite 96 px" in failed.detail


# ---- repo real -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_rules():
    return effective_rules(str(REPO_ROOT))


def px(rules, file, label):
    return min(r.px for r in rules[(file, label)] if r.px is not None)


def test_real_families_have_their_windows(real_rules):
    assert px(real_rules, "src/strings.c", "gText_MenuBag") == 48               # menu Start
    assert px(real_rules, "src/strings.c", "gText_TextSpeed") == 122            # nome da opção
    assert px(real_rules, "src/strings.c", "gText_TextSpeedSlow") == 70         # valor da opção
    assert px(real_rules, "src/strings.c", "gText_DoWhatWithPokemon") == 128    # grupo
    assert px(real_rules, "src/strings.c", "gText_PokeSum_Controls_Page") == 84    # resumo
    assert px(real_rules, "src/strings.c", "gText_RegionMap_AreaDesc_ViridianForest") == 198
    assert px(real_rules, "src/data/easy_chat/easy_chat_group_actions.h", "sEasyChatWord_Meets") == 96
    assert px(real_rules, "src/battle_message.c", "gText_MoveInterfacePP") == 24


@pytest.mark.parametrize("label, expected", [
    ("gText_1BigMushroom", 214),                    # multiescolha: (largura + 9) / 8 + 1 <= 28
    ("gText_Kanto", 44), ("gText_Seen", 72), ("gText_AreaUnknown", 88), ("gText_Cry", 228),
    ("gText_PokedexPokemon", 49), ("gText_Page", 200),                          # Pokédex
    ("gText_F700JoinedChat", 168), ("gText_Exit", 48), ("gText_Register", 80),  # Union Room
    ("gFameCheckerOakName", 56), ("gFameCheckerText_MainScreenUI", 188),        # Fame Checker
    ("gText_Profile", 128), ("gText_QuitEditing", 176),                         # Easy Chat
    ("gText_WirelessCommunicationStatus", 192), ("gText_PeopleTrading", 176),
])
def test_real_screens_reviewed_in_round_2(real_rules, label, expected):
    assert expected in {r.px for r in real_rules[("src/strings.c", label)]}       # a janela revista entra na conta


def test_real_union_room_chat_default_phrase_fits_the_save_buffer(real_rules):
    (rule,) = [r for r in real_rules[("src/strings.c", "gText_Hello")] if r.chars is not None]
    assert rule.chars == 20                     # registeredTexts[][21] (include/global.h)


def test_real_strings_c_is_measured(real_rules):
    kinds = Counter(coverage_kind(rules) for (file, _label), rules in real_rules.items() if file == "src/strings.c")
    assert kinds["largura"] >= 1150, kinds
    dead = [label for (file, label), rules in real_rules.items() if file == "src/strings.c"
            and coverage_kind(rules) == "sem medida" and "texto morto" not in rules[0].source]
    assert dead == [], dead[:10]


def test_table_and_menu_uses_never_fall_into_a_generic_rule():
    """Texto de tabela ou de chamada de menu/lista não pode ganhar a janela de uma regra-pega-tudo
    do arquivo: cada um desses usos tem regra própria (ou a tela tem janela única)."""
    loose = []
    for label, uses in repo_uses(REPO_ROOT).items():
        for file, ctx in uses:
            rule = match(file, ctx, label)
            assert rule is not None, (file, ctx, label)
            if (ctx.startswith("table:") or MENU_CALL.match(ctx)) and rule.generic:
                loose.append((file, ctx, label, rule.px))
    assert loose == [], loose[:10]


def test_generic_rule_flag():
    assert match("src/credits.c", "code", "x").generic is False             # tela de janela única
    assert match("src/script_menu.c", "table:sMultichoiceLists", "x").generic is False
    assert match("src/daycare.c", "code", "x").generic is True
    assert MENU_CALL.match("call:StringCopy") is None and MENU_CALL.match("call:DisplayPartyMenuMessage")
    assert bool(MENU_CALL.match("call:AddTextPrinterForListMenu")) and bool(MENU_CALL.match("call:PrintTextArray"))


_CHECKED_FILES = ("src/pokedex_screen.c", "src/union_room", "src/data/union_room.h", "src/fame_checker.c",
                  "src/easy_chat", "src/data/easy_chat/", "src/script_menu.c")
_TILES = re.compile(r"(\d+) tiles(?: cada)? \(((?:src|include)/[\w./-]+\.[ch]):(\d+)(?:-(\d+))?")
_CITE = re.compile(r"((?:src|include|data)/[\w./-]+\.(?:c|h|inc|s)):(\d+)(?:-(\d+))?((?:, :\d+(?:-\d+)?)*)")


def _cited_ranges(source):
    for path, first, last, more in _CITE.findall(source):
        yield path, int(first), int(last or first)
        for a, b in re.findall(r":(\d+)(?:-(\d+))?", more):
            yield path, int(a), int(b or a)


def _cited_text(path, first, last):
    lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[first - 1:last])


@pytest.mark.parametrize("rule", [r for r in USAGE_RULES if r.file.startswith(_CHECKED_FILES)],
                         ids=lambda r: f"{r.file}|{r.context}|{r.label}")
def test_cited_window_is_the_one_that_receives_the_text(rule):
    """Nas telas revistas, a janela citada tem a largura dita e o trecho de uso citado mostra o
    texto (a chamada, a tabela ou o rótulo) indo para ela."""
    for tiles, path, first, last in _TILES.findall(rule.source):
        text = _cited_text(path, int(first), int(last or first))
        assert re.search(rf"\bwidth\s*=\s*{tiles}\b|\b{tiles}\s*,", text), (rule.source, path, first)
    if rule.px is None and rule.chars is None:
        return
    names = {rule.label} if rule.label != "*" and not any(c in rule.label for c in "*?[") else set()
    if ":" in rule.context and "*" not in rule.context:
        names.add(rule.context.split(":", 1)[1].split(".")[0])
    if not names:
        return
    texts = [_cited_text(p, a, b) for p, a, b in _cited_ranges(rule.source)]
    assert any(n in t for n in names for t in texts), (rule.file, rule.context, rule.label, sorted(names))


def test_every_measuring_usage_rule_cites_existing_lines():
    for rule in USAGE_RULES:
        if rule.px is None and rule.chars is None:
            continue
        cited = re.findall(r"((?:src|data|include)/[\w./-]+\.(?:c|h|inc|s)):(\d+)(?:-(\d+))?", rule.source)
        assert cited, f"regra de uso sem arquivo:linha: {rule.file} {rule.context}"
        for path, first, last in cited:
            lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
            assert int(last or first) <= len(lines), (rule.file, path, first)
