"""POK-50: Pokérus de verdade. Confere no código-fonte o que o cenário `pokerus` não alcança
(a chamada depois da batalha, a meia-noite do relógio, o script da enfermeira e a flag)."""

import re

from esteira.scenarios import REPO_ROOT

POKEMON_C = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")
DAY_NIGHT_C = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
BATTLE_MAIN_C = (REPO_ROOT / "src" / "battle_main.c").read_text(encoding="utf-8")
NURSE = (REPO_ROOT / "data" / "scripts" / "pkmn_center_nurse.inc").read_text(encoding="utf-8")
EVENT_SCRIPTS = (REPO_ROOT / "data" / "event_scripts.s").read_text(encoding="utf-8")
FLAGS_H = (REPO_ROOT / "include" / "constants" / "flags.h").read_text(encoding="utf-8")


def _body(source: str, signature: str) -> str:
    start = source.index(signature)
    end = source.index("\n}\n", start)
    return source[start:end]


def test_stubs_viraram_codigo():
    assert "&foo;" not in POKEMON_C
    roll = _body(POKEMON_C, "void RandomlyGivePartyPokerus(struct Pokemon *party)")
    assert "rnd == 0x4000 || rnd == 0x8000 || rnd == 0xC000" in roll
    assert "GivePartyPokerusNow(party)" in roll
    give = _body(POKEMON_C, "void GivePartyPokerusNow(struct Pokemon *party)")
    assert "MON_DATA_IS_EGG" in give and "CheckPartyHasHadPokerus(party, 1 << slot)" in give
    spread = _body(POKEMON_C, "void PartySpreadPokerus(struct Pokemon *party)")
    assert "Random() % 3 != 0" in spread
    days = _body(POKEMON_C, "void UpdatePartyPokerusTime(u16 days)")
    assert "gPlayerParty" in days and "pokerus = 0x10" in days


def test_ev_dobrado_continua_ligado():
    gain = _body(POKEMON_C, "void MonGainEVs(struct Pokemon *mon, u16 defeatedSpecies)")
    assert "CheckPartyHasHadPokerus(mon, 0)" in gain and "multiplier = 2" in gain


def test_depois_da_batalha_fora_do_link():
    body = _body(BATTLE_MAIN_C, "static void ReturnFromBattleToOverworld(void)\n{")
    assert re.search(r"if \(!\(gBattleTypeFlags & BATTLE_TYPE_LINK\)\)\s*\{\s*"
                     r"RandomlyGivePartyPokerus\(gPlayerParty\);\s*PartySpreadPokerus\(gPlayerParty\);", body)


def test_meia_noite_do_relogio_conta_um_dia():
    tick = _body(DAY_NIGHT_C, "void DayNight_Tick(void)")
    assert "UpdatePartyPokerusTime(1)" in tick
    assert "GAME_CLOCK_MIDNIGHT_OFFSET" in tick
    assert ("#define GAME_CLOCK_MIDNIGHT_OFFSET ((MINUTES_PER_DAY - GAME_CLOCK_START_MINUTE) "
            "* GAME_CLOCK_FRAMES_PER_MINUTE)") in DAY_NIGHT_C


def test_enfermeira_explica_uma_vez():
    heal = NURSE[NURSE.index("EventScript_PkmnCenterNurse_HealPkmn::"):]
    heal = heal[:heal.index("\tend\n")]
    assert "goto_if_unset FLAG_POKERUS_EXPLAINED, EventScript_PkmnCenterNurse_CheckPokerus" in heal
    check = NURSE[NURSE.index("EventScript_PkmnCenterNurse_CheckPokerus::"):]
    check = check[:check.index("\tend\n")]
    assert "specialvar VAR_RESULT, IsPokerusInParty" in check
    assert check.index("msgbox Text_PokerusExplanation") < check.index("setflag FLAG_POKERUS_EXPLAINED")
    assert "Text_PokerusExplanation::" in EVENT_SCRIPTS


def test_flag_era_livre():
    assert re.search(r"#define FLAG_POKERUS_EXPLAINED\s+0x4A9\b", FLAGS_H)
    assert "FLAG_UNUSED_0x4A9" not in FLAGS_H
    assert len(re.findall(r"\b0x4A9\b", FLAGS_H)) == 1
