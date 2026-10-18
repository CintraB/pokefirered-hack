"""Hack 7, Dex Nacional na tela desde o início, sem emulador.

As telas usam IsNationalPokedexUiEnabled() (chave NATIONAL_DEX_FROM_START); a flag e todos os
scripts de história continuam com IsNationalPokedexEnabled() (marca de pós-Liga).
"""

import re

from esteira.scenarios import REPO_ROOT

NEW, OLD = "IsNationalPokedexUiEnabled", "IsNationalPokedexEnabled"

# (arquivo, quantidade de usos de UI)
UI_FILES = {
    "src/pokedex_screen.c": 7,
    "src/pokemon.c": 1,
    "src/trade.c": 1,
    "src/trainer_card.c": 1,
    "src/save_menu_util.c": 1,
    "src/main_menu.c": 1,
    "src/easy_chat.c": 2,
}
STORY_C = ("src/link.c", "src/link_rfu_3.c", "src/prof_pc.c")
STORY_SCRIPTS = ("data/scripts/hall_of_fame.inc",
                 "data/maps/IndigoPlateau_PokemonCenter_1F/scripts.inc",
                 "data/maps/OneIsland_PokemonCenter_1F/scripts.inc",
                 "data/maps/ThreeIsland_DunsparceTunnel/scripts.inc")
OAK = "data/maps/PalletTown_ProfessorOaksLab"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _calls(text: str, name: str) -> int:
    return len(re.findall(rf"\b{name}\s*\(", text))


def test_ui_usa_funcao_nova():
    for rel, n in UI_FILES.items():
        text = _read(rel)
        assert _calls(text, NEW) == n, f"{rel}: esperava {n} uso(s) de {NEW}"
        body = text
        if rel == "src/easy_chat.c":   # só a declaração/definição do invólucro
            body = re.sub(r"static bool8 EC_IsNationalPokedexEnabled\(void\)", "", text)
        assert _calls(body, OLD) == 0, f"{rel}: ainda chama {OLD}"


def test_funcao_nova_e_chave():
    cfg = _read("include/config.h")
    assert re.search(r"#define NATIONAL_DEX_FROM_START 1", cfg)
    assert cfg.index("SWITCH_GBA_COMPAT") < cfg.index("NATIONAL_DEX_FROM_START")
    assert f"bool32 {NEW}(void);" in _read("include/event_data.h")
    c = _read("src/event_data.c")
    body = c[c.index(f"bool32 {NEW}(void)"):]
    body = body[:body.index("\n}")]
    assert "NATIONAL_DEX_FROM_START" in body and f"{OLD}()" in body


def test_historia_intacta():
    for rel in STORY_SCRIPTS:
        assert f"specialvar VAR_RESULT, {OLD}" in _read(rel), rel
        assert NEW not in _read(rel), rel
    for rel in STORY_C:
        assert NEW not in _read(rel), rel
        assert OLD in _read(rel), rel
    assert NEW not in _read("src/test_hooks.c")
    assert f"def_special {NEW}" not in _read("data/specials.inc")


def test_fala_do_oak():
    scripts, text = _read(f"{OAK}/scripts.inc"), _read(f"{OAK}/text.inc")
    label = "PalletTown_ProfessorOaksLab_Text_OakDexRecordsOtherRegions"
    assert f"msgbox {label}" in scripts
    assert scripts.index("setflag FLAG_SYS_POKEDEX_GET") < scripts.index(f"msgbox {label}")
    assert scripts.index(f"msgbox {label}") < scripts.index(
        "msgbox PalletTown_ProfessorOaksLab_Text_OakCatchMonsForDataTakeThese")
    assert f"{label}::" in text
    assert "Pokémon de outras" in text and "regiões" in text
