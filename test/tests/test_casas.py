"""POK-51 (Task 8): o Mestre dos Golpes na Rota 6. Leitura estática do special, do script e dos mapas.

O comportamento no jogo (lista, cobrança, recusas) fica no cenário `casas` (`--only casas`).
"""

import json
import re
import struct

from esteira.scenarios import REPO_ROOT
from tests.test_familia_mapas import BEHAVIORS, _behavior_at, _grid, _map

MESTRE_C = (REPO_ROOT / "src" / "mestre_golpes.c").read_text(encoding="utf-8")
MESTRE_H = (REPO_ROOT / "include" / "mestre_golpes.h").read_text(encoding="utf-8")
TUTOR_H = (REPO_ROOT / "src" / "data" / "pokemon" / "tutor_learnsets.h").read_text(encoding="utf-8")
SCRIPTS = (REPO_ROOT / "data" / "maps" / "Route6_UnusedHouse" / "scripts.inc").read_text(encoding="utf-8")
SPECIALS = (REPO_ROOT / "data" / "specials.inc").read_text(encoding="utf-8")


def _tabela(texto: str, nome: str) -> list[tuple[str, str]]:
    corpo = texto[texto.index(nome):]
    corpo = corpo[:corpo.index("};")]
    return re.findall(r"\[(TUTOR_MOVE_\w+)\]\s*=\s*(MOVE_\w+)", corpo)


def test_mestre_quinze_golpes():
    """A lista do Mestre tem os 15 golpes de tutor, na mesma ordem e com os mesmos golpes de sTutorMoves."""
    meus = _tabela(MESTRE_C, "sMestreGolpes[")
    originais = _tabela(TUTOR_H, "sTutorMoves[")
    assert len(meus) == 15
    assert meus[0][0] == "TUTOR_MOVE_MEGA_PUNCH" and meus[-1][0] == "TUTOR_MOVE_SUBSTITUTE"
    assert meus == originais
    # o nome vem do jogo (PT-BR) e a lista rola (6 linhas para 15 golpes)
    assert "gMoveNames[sMestreGolpes[i]]" in MESTRE_C
    assert re.search(r"MESTRE_LINHAS_VISIVEIS\s+6", MESTRE_C)
    assert "AddScrollIndicatorArrowPair" in MESTRE_C
    # cancelar devolve 0xFF
    assert re.search(r"MESTRE_GOLPES_CANCELOU\s+0xFF", MESTRE_H)
    assert re.search(r"LIST_CANCEL:.*?MESTRE_GOLPES_CANCELOU", MESTRE_C, re.S)
    # o special está registrado
    assert re.search(r"^\tdef_special MestreGolpes_EscolherGolpe$", SPECIALS, re.M)


def test_mestre_preco_3000():
    """¥3.000 por golpe: confere o dinheiro antes, cobra só depois de o Pokémon aprender, e não toca nas flags dos
    tutores originais."""
    assert re.search(r"MESTRE_GOLPES_PRECO\s+3000", MESTRE_H)
    assert SCRIPTS.count("checkmoney 3000") == 1 and SCRIPTS.count("removemoney 3000") == 1
    ordem = [SCRIPTS.index(s) for s in ("special MestreGolpes_EscolherGolpe", "checkmoney 3000",
                                        "call EventScript_ChooseMoveTutorMon",
                                        "goto_if_eq VAR_RESULT, FALSE, Route6_UnusedHouse_EventScript_MestreDesistiu",
                                        "removemoney 3000")]
    assert ordem == sorted(ordem), "a cobrança tem de vir depois do ensino"
    # o tutor é o escolhido na lista
    assert "copyvar VAR_0x8005, VAR_RESULT" in SCRIPTS
    # as flags de "já ensinou" dos tutores originais ficam em paz
    assert not re.search(r"(setflag|clearflag)\s+FLAG_(TUTOR|LEARNED)", SCRIPTS)


def test_casa_rota6_ligada():
    """Warps de ida e volta, porta com comportamento de porta, frente livre e a casa fora da grama alta."""
    rota = _map("Route6")
    casa = _map("Route6_UnusedHouse")
    idas = [(i, w) for i, w in enumerate(rota["warp_events"]) if w["dest_map"] == "MAP_ROUTE6_UNUSED_HOUSE"]
    assert len(idas) == 1
    id_ida, ida = idas[0]
    assert ida["dest_warp_id"] == "0"
    voltas = casa["warp_events"]
    assert voltas and all(w["dest_map"] == "MAP_ROUTE6" and int(w["dest_warp_id"]) == id_ida for w in voltas)
    # a porta (ida) está na linha da casa e tem comportamento de porta; a frente dela é chão livre
    assert "DOOR" in _behavior_at("Route6", ida["x"], ida["y"]), _behavior_at("Route6", ida["x"], ida["y"])
    largura, celulas, attr = _grid("Route6")
    assert celulas[(ida["y"] + 1) * largura + ida["x"]][1] == 0, "frente da porta bloqueada"
    assert BEHAVIORS.get(attr(celulas[(ida["y"] + 1) * largura + ida["x"]][0]) & 0x1FF) != "MB_TALL_GRASS"
    # a casa (x 6-9, y 27-30) não tem grama alta e não cobre outro warp nem objeto
    for y in range(27, 31):
        for x in range(6, 10):
            assert BEHAVIORS.get(attr(celulas[y * largura + x][0]) & 0x1FF) != "MB_TALL_GRASS", (x, y)
            outros = [w for w in rota["warp_events"] if (w["x"], w["y"]) == (x, y)]
            assert len(outros) <= (1 if (x, y) == (ida["x"], ida["y"]) else 0), (x, y)
            assert not [o for o in rota["object_events"] if (o["x"], o["y"]) == (x, y)]
    # o Mestre está no mapa interno com script próprio e a casa não tem a flag dos tutores
    assert [o["script"] for o in casa["object_events"]] == ["Route6_UnusedHouse_EventScript_Mestre"]
    assert (REPO_ROOT / "data/maps/Route6_UnusedHouse/text.inc").is_file()
    assert 'data/maps/Route6_UnusedHouse/text.inc' in (REPO_ROOT / "data/event_scripts.s").read_text("utf-8")
