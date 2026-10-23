"""Hack 7, cena pós-Liga nova do Oak (ovo raro, ¥45.000, objetivo do Amuleto Brilhante), sem
emulador.

A condição da cena (60 capturados de Kanto, FLAG_WORLD_MAP_ONE_ISLAND) não muda; a troca é só o
presente: os textos do "upgrade da Pokédex" dão lugar ao ovo raro e ao dinheiro.
"""

import re

from esteira.scenarios import REPO_ROOT

OAK = "data/maps/PalletTown_ProfessorOaksLab"
OLD_LABELS = ("PalletTown_ProfessorOaksLab_Text_OakTookBothPokedexUnits",
              "PalletTown_ProfessorOaksLab_Text_OakNowTheseUnitsCanRecordMoreData",
              "PalletTown_ProfessorOaksLab_Text_PlayersPokedexWasUpgraded")


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _scene() -> str:
    s = _read(f"{OAK}/scripts.inc")
    start = s.index("PalletTown_ProfessorOaksLab_EventScript_NationalDexScene::")
    return s[start:s.index("PalletTown_ProfessorOaksLab_EventScript_NationalDexSceneRivalEnterNorth::")]


def test_ovo_tres_especies():
    c = _read("src/field_specials.c")
    body = c[c.index("u16 GetRandomRareEggSpecies(void)"):]
    body = body[:body.index("\n}")]
    for sp in ("SPECIES_LARVITAR", "SPECIES_BAGON", "SPECIES_BELDUM"):
        assert sp in body
    assert "Random() % NELEMS(sRareEggSpecies)" in body and body.count("SPECIES_") == 3
    assert "def_special GetRandomRareEggSpecies" in _read("data/specials.inc")
    scripts = _read(f"{OAK}/scripts.inc")
    assert "specialvar VAR_0x8004, GetRandomRareEggSpecies" in scripts
    assert "giveegg VAR_0x8004" in scripts


def test_cena_sem_textos_de_upgrade():
    scene, text = _scene(), _read(f"{OAK}/text.inc")
    scripts = _read(f"{OAK}/scripts.inc")
    for label in OLD_LABELS:
        assert label not in scripts, label
        assert f"{label}::" not in text, label
    for label in ("Text_OakThanksRareEgg", "Text_OakAndThisForTravels", "Text_OakShinyCharmGoal"):
        assert f"PalletTown_ProfessorOaksLab_{label}" in scene, label
        assert f"PalletTown_ProfessorOaksLab_{label}::" in text, label
    assert "EventScript_TryGiveRareEgg" in scene
    assert scene.index("Text_OakThanksRareEgg") < scene.index("EventScript_TryGiveRareEgg") \
        < scene.index("Text_OakAndThisForTravels") < scene.index("addmoney 45000") \
        < scene.index("Text_OakShinyCharmGoal") < scene.index("special EnableNationalPokedex") \
        < scene.index("VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 8")


def test_condicao_da_cena_intacta():
    s = _read("data/maps/PalletTown/scripts.inc")
    assert "goto_if_lt VAR_0x8009, 60" in s
    assert "FLAG_WORLD_MAP_ONE_ISLAND" in s
    assert "special EnableNationalPokedex" in _scene()


def test_addmoney_45000():
    assert len(re.findall(r"addmoney 45000\b", _read(f"{OAK}/scripts.inc"))) == 1
    text = _read(f"{OAK}/text.inc")
    assert "recebeu ¥45.000!" in text


def test_flag_nova():
    h = _read("include/constants/flags.h")
    assert re.search(r"#define FLAG_GOT_RARE_EGG\s+0x4A8\b", h)
    assert "FLAG_UNUSED_0x4A8" not in h
    scripts = _read(f"{OAK}/scripts.inc")
    assert scripts.count("setflag FLAG_GOT_RARE_EGG") == 2   # equipe e PC


def test_resultado_do_ovo_trata_os_tres_casos():
    s = _read(f"{OAK}/scripts.inc")
    sub = s[s.index("PalletTown_ProfessorOaksLab_EventScript_TryGiveRareEgg::"):]
    sub = sub[:sub.index("\n\n")]
    assert "goto_if_eq VAR_RESULT, MON_CANT_GIVE" in sub
    assert "goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC" in sub
    assert "Text_OakNoRoomForEgg" in s


def test_oak_entrega_pendente_ao_falar():
    s = _read(f"{OAK}/scripts.inc")
    oak = s[s.index("PalletTown_ProfessorOaksLab_EventScript_ProfOak::"):]
    oak = oak[:oak.index("PalletTown_ProfessorOaksLab_EventScript_OakJustShownCompleteDex::")]
    ge8 = oak.index("goto_if_ge VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 8, "
                    "PalletTown_ProfessorOaksLab_EventScript_OakCheckRareEgg")
    assert ge8 < oak.index("VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 9")
    assert ge8 < oak.index("VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 8, PalletTown_ProfessorOaksLab_EventScript_MonsAround")
    check = s[s.index("PalletTown_ProfessorOaksLab_EventScript_OakCheckRareEgg::"):]
    check = check[:check.index("\n\n")]
    assert "goto_if_set FLAG_GOT_RARE_EGG, PalletTown_ProfessorOaksLab_EventScript_ProfOakStoryStage" in check
    assert "OakGivePendingRareEgg" in check
    pending = s[s.index("PalletTown_ProfessorOaksLab_EventScript_OakGivePendingRareEgg::"):]
    assert "call PalletTown_ProfessorOaksLab_EventScript_TryGiveRareEgg" in pending[:pending.index("\n\n")]


def test_fala_extra_depois_da_explicacao():
    s = _read(f"{OAK}/scripts.inc")
    label = "msgbox PalletTown_ProfessorOaksLab_Text_OakDexRecordsOtherRegions"
    assert s.count(label) == 1
    assert s.index("msgbox PalletTown_ProfessorOaksLab_Text_OakCompleteMonGuideWasMyDream") \
        < s.index(label) < s.index("msgbox PalletTown_ProfessorOaksLab_Text_RivalLeaveItToMeGramps")


def test_textos_do_brief():
    t = _read(f"{OAK}/text.inc")
    for frag in ("CARVALHO: Vocês dois ajudaram", "É um Ovo de Pokémon muito raro!",
                 "{PLAYER} recebeu o Ovo!", "O Ovo foi enviado para o PC.",
                 "Venha falar comigo quando tiver", "E isto é para as suas viagens!",
                 "Amuleto Brilhante"):
        assert frag in t, frag


# --- revisão final da branch ---------------------------------------------------------------------

def _text_body(label: str) -> str:
    """O texto de um rótulo do text.inc, com as linhas .string juntadas."""
    t = _read(f"{OAK}/text.inc")
    bloco = t[t.index(f"{label}::"):]
    bloco = bloco[:bloco.index("$\"") + 2]
    return "".join(re.findall(r'\.string "(.*?)"', bloco))


def test_oak_nao_pede_mais_as_pokedex():
    """O Oak não leva mais as Pokédex (o upgrade virou o ovo raro): a fala que pedia as duas acaba
    no "preciso da sua ajuda também"."""
    body = _text_body("PalletTown_ProfessorOaksLab_Text_OakNeedYourHelpToo")
    # traduzida na A3 (as quebras de linha são do reflow, por isso se compara o texto achatado)
    flat = re.sub(r"\\[nlp]", " ", body)
    assert flat == "CARVALHO: Eu sei, eu sei. É claro que também preciso da sua ajuda.$", body
    scene = _scene()
    assert scene.index("Text_OakNeedYourHelpToo") < scene.index("Text_OakThanksRareEgg")


def test_fanfarra_do_ovo_no_padrao():
    """message / waitmessage / waitfanfare, como o resto do repo (dinheiro do Oak, obtain_item)."""
    s = _read(f"{OAK}/scripts.inc")
    padrao = ("message PalletTown_ProfessorOaksLab_Text_ReceivedRareEgg\n"
              "\twaitmessage\n"
              "\twaitfanfare\n")
    assert s.count(padrao) == 2, "equipe e PC"
    assert "message PalletTown_ProfessorOaksLab_Text_ReceivedRareEgg\n\twaitfanfare" not in s


def test_telas_da_cena_na_pagina_do_trecho():
    r"""Cada tela da cena é tirada na espera (\p ou \l) em que o trecho já está na caixa: o
    `pos_liga_objetivo` tem de mostrar "Amuleto Brilhante", que só aparece depois da rolagem."""
    from esteira.scenarios.full_post_league import SHOTS, TEXT_DINHEIRO, TEXT_OBJETIVO, TEXT_OVO
    labels = {TEXT_OVO: "PalletTown_ProfessorOaksLab_Text_ReceivedRareEgg",
              TEXT_DINHEIRO: "PalletTown_ProfessorOaksLab_Text_ReceivedMoneyFromOak",
              TEXT_OBJETIVO: "PalletTown_ProfessorOaksLab_Text_OakShinyCharmGoal"}
    assert set(labels) == set(SHOTS)
    for needle, label in labels.items():
        body = _text_body(label)
        assert needle in body, (needle, label)
        antes = body[:body.index(needle)]
        esperas = antes.count(r"\p") + antes.count(r"\l")
        assert SHOTS[needle][1] == esperas, (needle, SHOTS[needle], esperas)
