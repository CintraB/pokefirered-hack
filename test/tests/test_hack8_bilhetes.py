"""Hack 8: o Prof. Carvalho entrega os bilhetes Aurora e Místico, com fala, no Hall da Fama.

Antes eles chegavam calados na bolsa (`EnterHallOfFame`, `#if REVISION >= 0xA`). Agora o script da sala
(`PokemonLeague_HallOfFame_EventScript_EnterRoom`) fala, dá os dois bilhetes com a mensagem padrão de
item recebido e liga as 4 flags, só se `FLAG_RECEIVED_AURORA_TICKET` estiver desligada. O bloco em C
continua (só age se faltar o Bilhete Aurora na bolsa, então não duplica).
"""

import re

from esteira import check_text as ct
from esteira.scenarios import REPO_ROOT

HALL = "data/maps/PokemonLeague_HallOfFame"
LABEL_FALA = "PokemonLeague_HallOfFame_Text_OakTickets"
LABEL_ENTREGA = "PokemonLeague_HallOfFame_EventScript_OakGivesTickets"
FLAGS = ("FLAG_ENABLE_SHIP_BIRTH_ISLAND", "FLAG_ENABLE_SHIP_NAVEL_ROCK",
         "FLAG_RECEIVED_AURORA_TICKET", "FLAG_RECEIVED_MYSTIC_TICKET")


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _block(src: str, label: str) -> str:
    """Corpo do rótulo `label::` até o próximo rótulo global."""
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    return src[start:start + len(label) + 2 + (m.start() if m else len(src))]


def _enter_room() -> str:
    return _block(_read(f"{HALL}/scripts.inc"), "PokemonLeague_HallOfFame_EventScript_EnterRoom")


def _entrega() -> str:
    return _block(_read(f"{HALL}/scripts.inc"), LABEL_ENTREGA)


def _fala() -> str:
    """Texto do rótulo como a esteira o lê (linhas `.string` juntas, com as quebras do fonte)."""
    return _entrada().texts[0]


def _entrada():
    achadas = [e for e in ct._sources(REPO_ROOT)
               if getattr(e, "file", None) == f"{HALL}/text.inc" and e.label == LABEL_FALA]
    assert len(achadas) == 1
    return achadas[0]


def test_enter_room_chama_a_entrega_entre_a_fala_e_o_registro():
    s = _enter_room()
    assert s.index("msgbox PokemonLeague_HallOfFame_Text_OakCongratulations") \
        < s.index(f"call {LABEL_ENTREGA}") < s.index("dofieldeffect FLDEFF_HALL_OF_FAME_RECORD")


def test_entrega_so_com_a_flag_do_aurora_desligada():
    s = _entrega()
    guarda = s.index("goto_if_set FLAG_RECEIVED_AURORA_TICKET")   # salta tudo se já recebeu
    assert guarda < s.index("msgbox") < s.index("giveitem")
    # o desvio cai direto no `return` (volta ao EnterRoom sem dar nada)
    alvo = re.search(r"goto_if_set FLAG_RECEIVED_AURORA_TICKET, (\w+)", s).group(1)
    fim = _block(_read(f"{HALL}/scripts.inc"), alvo)
    assert fim.split("::", 1)[1].strip() == "return"
    assert f"{alvo}::" in _read(f"{HALL}/scripts.inc")


def test_entrega_da_os_dois_bilhetes_e_liga_as_quatro_flags():
    s = _entrega()
    assert "giveitem ITEM_AURORA_TICKET" in s and "giveitem ITEM_MYSTIC_TICKET" in s
    assert f"msgbox {LABEL_FALA}" in s
    for flag in FLAGS:
        assert f"setflag {flag}" in s, flag
    # as flags só depois dos dois itens
    assert max(s.index("giveitem ITEM_AURORA_TICKET"), s.index("giveitem ITEM_MYSTIC_TICKET")) \
        < min(s.index(f"setflag {f}") for f in FLAGS)
    # fala antes da entrega
    assert s.index(f"msgbox {LABEL_FALA}") < s.index("giveitem ITEM_AURORA_TICKET")


def test_bloco_em_c_continua_e_nao_duplica():
    c = _read("src/post_battle_event_funcs.c")
    assert "if (!CheckBagHasItem(ITEM_AURORA_TICKET, 1))" in c
    for item in ("ITEM_AURORA_TICKET", "ITEM_MYSTIC_TICKET"):
        assert f"AddBagItem({item}, 1);" in c
    for flag in FLAGS:
        assert f"FlagSet({flag});" in c, flag


def test_texto_existe_e_traz_os_termos_inteiros():
    t = _fala()
    for frag in ("Ah, quase esqueci!", "Chegaram estes bilhetes para você.",
                 "Passe 7 Cores", "Ilhas Sevii", "Cidade de Vermilion", "marinheiro do porto"):
        assert frag in re.sub(r"\\[nlp]", " ", t), frag
    # termos compostos não podem ser partidos por quebra
    for termo in ("Passe 7 Cores", "Ilhas Sevii", "Cidade de Vermilion"):
        assert termo in t, f"{termo!r} partido pela quebra"
    assert _read(f"{HALL}/text.inc").endswith('$"\n\n')   # fim de arquivo preservado


def test_texto_sem_marca_de_genero_para_o_jogador():
    flat = re.sub(r"\\[nlp]", " ", _fala())
    assert not re.search(r"\b(cansad|pronto|preparad|obrigad|sozinh|bem-vind)[oa]s?\b", flat, re.I)


def test_texto_respeita_as_regras_da_esteira():
    assert ct.box_lines(_fala()) <= 2
    import json
    exc = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    res = ct.check_text(str(REPO_ROOT), exc, english="desligado")
    assert [r for r in res if r.status == "aviso" and "base inglesa indisponível" in r.detail] == []
    achados = [r for r in res if r.status == "falha" and LABEL_FALA in r.detail]
    assert achados == [], [r.detail for r in achados]
