"""POK-28, Task 4: o Presidente do Fã-clube de Vermilion presenteia um Snubbull nv 20 a quem tem o 1º da equipe com
amizade alta (`GetLeadMonFriendship` >= 5, ou seja, 200 ou mais).

Escolhido o Presidente (e não a funcionária) porque o ramo `AlreadyHeardStory` só roda DEPOIS do Vale Bicicleta: a
conversa do voucher fica intacta, e a funcionária, que chama o `famechecker`, não é tocada.

O cenário `johto` (`test/esteira/scenarios/full_johto.py`, casos `johto/snubbull/*`) roda o fluxo de verdade.
"""

import re

from esteira.scenarios import REPO_ROOT

MAPA = "data/maps/VermilionCity_PokemonFanClub"
P = "VermilionCity_PokemonFanClub_"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _block(label: str) -> str:
    """Corpo do rótulo `label::` em scripts.inc, até o próximo rótulo global (sem os comentários `@` do seguinte)."""
    src = _read(f"{MAPA}/scripts.inc")
    start = src.index(f"{P}{label}::")
    m = re.search(r"^\w+::", src[start + len(P + label) + 2:], re.M)
    corpo = src[start:start + len(P + label) + 2 + (m.start() if m else len(src))]
    return re.sub(r"(?:^@[^\n]*\n)+\Z", "", corpo, flags=re.M)


def test_flag_na_faixa_livre_sem_colisao():
    h = _read("include/constants/flags.h")
    assert re.search(r"^#define FLAG_GOT_SNUBBULL\s+0x4DE\b", h, re.M)
    assert not re.search(r"^#define FLAG_0x4DE\b", h, re.M)
    valores = [int(v, 16) for v in re.findall(r"^#define FLAG_\w+\s+(0x[0-9A-Fa-f]+)\b", h, re.M)]
    assert valores.count(0x4DE) == 1
    assert re.search(r"^#define FLAG_HIDE_SUDOWOODO\s+0x4DF\b", h, re.M)   # a seguinte foi para a Task 5


def test_dica_e_oferta_na_conversa_pos_voucher():
    b = _block("EventScript_AlreadyHeardStory")
    # a fala de antes continua a primeira
    assert b.index(f"msgbox {P}Text_DidntComeToSeeAboutMonsAgain") < b.index("GetLeadMonFriendship")
    assert "goto_if_set FLAG_GOT_SNUBBULL, EventScript_ReleaseEnd" in b
    assert "goto_if_questlog EventScript_ReleaseEnd" in b
    assert "specialvar VAR_RESULT, GetLeadMonFriendship" in b
    assert f"goto_if_ge VAR_RESULT, 5, {P}EventScript_TryGiveSnubbull" in b
    # abaixo de 5: só a dica, sem flag nem Pokémon
    assert f"msgbox {P}Text_SnubbullHint" in b and "givemon" not in b and "setflag" not in b


def test_entrega_nv20_com_os_tres_desfechos():
    b = _block("EventScript_TryGiveSnubbull")
    assert "givemon SPECIES_SNUBBULL, 20" in b
    assert b.index(f"msgbox {P}Text_SnubbullOffer") < b.index("givemon")
    assert "setvar VAR_TEMP_1, SPECIES_SNUBBULL" in b           # o texto do PC lê a espécie em VAR_TEMP_1
    assert f"goto_if_eq VAR_RESULT, 0, {P}EventScript_GetSnubbullParty" in b
    assert f"goto_if_eq VAR_RESULT, 1, {P}EventScript_GetSnubbullPC" in b
    assert "goto EventScript_NoMoreRoomForPokemon" in b
    assert "setflag" not in b                                   # sem vaga, a flag não liga
    for ramo in ("GetSnubbullParty", "GetSnubbullPC"):
        r = _block(f"EventScript_{ramo}")
        assert r.count("setflag FLAG_GOT_SNUBBULL") == 1 and r.index("setflag") < r.index("message "), ramo
    assert "EventScript_TransferredToPC" in _block("EventScript_TransferSnubbullToPC")
    assert "EventScript_ChangePokemonNickname" in _block("EventScript_GetSnubbullParty")
    assert "EventScript_NameReceivedBoxMon" in _block("EventScript_GetSnubbullPC")


def test_vale_bicicleta_e_funcionaria_intactos():
    chairman = _block("EventScript_Chairman")
    assert f"goto_if_set FLAG_GOT_BIKE_VOUCHER, {P}EventScript_AlreadyHeardStory" in chairman
    assert "Snubbull" not in chairman and "Friendship" not in chairman
    story = _block("EventScript_ChairmanStory")
    assert "checkitemspace ITEM_BIKE_VOUCHER" in story and "setflag FLAG_GOT_BIKE_VOUCHER" in story
    assert "giveitem_msg" in story and "Snubbull" not in story
    worker = _block("EventScript_WorkerFGameClear")
    assert "famechecker FAMECHECKER_DAISY, 1" in worker and "Snubbull" not in _block("EventScript_WorkerF")


def test_textos():
    t = _read(f"{MAPA}/text.inc")
    for rot in ("SnubbullOffer", "ReceivedSnubbullFromChairman", "SnubbullHint"):
        assert f"{P}Text_{rot}::" in t, rot
    # PT-BR: nada em inglês nem japonês nos textos novos
    novos = t[t.index(f"{P}Text_SnubbullOffer::"):]
    assert "{PLAYER} recebeu um SNUBBULL" in novos
    assert "gostar muito de você" in novos
    assert not re.search(r"[ぁ-んァ-ン]", novos)
