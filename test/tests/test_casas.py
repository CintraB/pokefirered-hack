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


# ---------- Task 9: o pescador da Rota 19 ----------
SIZE_C = (REPO_ROOT / "src" / "pokemon_size_record.c").read_text(encoding="utf-8")
PESCADOR = (REPO_ROOT / "data" / "maps" / "Route19_UnusedHouse" / "scripts.inc").read_text(encoding="utf-8")
FLAGS_H = (REPO_ROOT / "include" / "constants" / "flags.h").read_text(encoding="utf-8")
VARS_H = (REPO_ROOT / "include" / "constants" / "vars.h").read_text(encoding="utf-8")


def test_krabby_recorde_funcoes():
    """Init/Get/Compare do Krabby no molde do Magikarp, com var própria (livre), iniciada no novo jogo, e os dois
    specials registrados no FIM de specials.inc."""
    for acao in ("Init", "Get", "Compare"):
        assert re.search(rf"void {acao}Krabby\w*\(void\)", SIZE_C), acao
    assert "VarSet(VAR_KRABBY_SIZE_RECORD, DEFAULT_MAX_SIZE)" in SIZE_C
    assert "GetMonSizeRecordInfo(SPECIES_KRABBY, sizeRecord)" in SIZE_C
    assert "CompareMonSize(SPECIES_KRABBY, sizeRecord)" in SIZE_C
    assert "InitKrabbySizeRecord();" in (REPO_ROOT / "src" / "new_game.c").read_text(encoding="utf-8")
    assert "void InitKrabbySizeRecord(void);" in (REPO_ROOT / "include" / "pokemon_size_record.h").read_text("utf-8")
    # a var é salva (0x4020-0x40FF), única e a antiga VAR_0x40F0 sumiu
    m = re.search(r"#define VAR_KRABBY_SIZE_RECORD\s+(0x40[0-9A-F]{2})\s+// POK-51", VARS_H)
    assert m and 0x4020 <= int(m.group(1), 16) <= 0x40FF
    valores = re.findall(r"#define VAR_\w+\s+(0x40[0-9A-Fa-f]{2})\b", VARS_H)
    assert valores.count(m.group(1)) == 1 and "VAR_0x40F0" not in VARS_H
    nomes = re.findall(r"def_special (\w+)", SPECIALS.split("gSpecialsEnd::")[0])
    assert nomes[-2:] == ["GetKrabbySizeRecordInfo", "CompareKrabbySize"], nomes[-3:]
    # o hook de teste do tamanho entrou no bloco novo (0x130)
    assert re.search(r"TEST_CMD_SET_PARTY_PID_LOW = 0x130", (REPO_ROOT / "include" / "test_hooks.h").read_text("utf-8"))


def test_premios_pescador():
    """Recorde novo → Pepita; o primeiro recorde → também Bala Rara, com a flag só depois de a Bala Rara entrar na
    mochila; mochila cheia usa giveitem + EventScript de aviso."""
    assert PESCADOR.count("giveitem ITEM_NUGGET") == 1 and PESCADOR.count("giveitem ITEM_RARE_CANDY") == 1
    assert re.search(r"#define FLAG_PESCADOR_PRIMEIRO_RECORDE\s+0x4AA // POK-51", FLAGS_H)
    assert "FLAG_UNUSED_0x4AA" not in FLAGS_H
    corpo = PESCADOR[PESCADOR.index("Route19_UnusedHouse_EventScript_NovoRecorde::"):]
    ordem = [corpo.index(s) for s in ("giveitem ITEM_NUGGET", "goto_if_unset FLAG_PESCADOR_PRIMEIRO_RECORDE",
                                      "giveitem ITEM_RARE_CANDY", "setflag FLAG_PESCADOR_PRIMEIRO_RECORDE")]
    assert ordem == sorted(ordem)
    assert PESCADOR.count("setflag FLAG_PESCADOR_PRIMEIRO_RECORDE") == 1
    assert PESCADOR.count("goto_if_eq VAR_RESULT, FALSE, Route19_UnusedHouse_EventScript_SemEspaco") == 2
    # só o resultado 3 (recorde novo) ou o empate com o recorde padrão (flag desligada) pagam
    assert "goto_if_eq VAR_RESULT, 3, Route19_UnusedHouse_EventScript_NovoRecorde" in PESCADOR
    assert re.search(r"EventScript_Empate::\n\tgoto_if_unset FLAG_PESCADOR_PRIMEIRO_RECORDE, "
                     r"Route19_UnusedHouse_EventScript_NovoRecorde", PESCADOR)
    assert "EventScript_NaoBateORecorde::\n\tmsgbox" in PESCADOR and "giveitem" not in \
        PESCADOR[PESCADOR.index("EventScript_NaoBateORecorde::"):PESCADOR.index("EventScript_Empate::")]
    assert "special CompareKrabbySize" in PESCADOR and "special GetKrabbySizeRecordInfo" in PESCADOR


def test_casa_rota19_ligada():
    """Warp de ida e volta, porta com comportamento de porta e frente livre, casa só sobre areia, sem cobrir objeto,
    sinal ou warp, e o caminho do norte até a praia segue aberto."""
    rota = _map("Route19")
    casa = _map("Route19_UnusedHouse")
    idas = [(i, w) for i, w in enumerate(rota["warp_events"]) if w["dest_map"] == "MAP_ROUTE19_UNUSED_HOUSE"]
    assert len(idas) == 1
    id_ida, ida = idas[0]
    assert ida["dest_warp_id"] == "0"
    voltas = casa["warp_events"]
    assert voltas and all(w["dest_map"] == "MAP_ROUTE19" and int(w["dest_warp_id"]) == id_ida for w in voltas)
    assert "DOOR" in _behavior_at("Route19", ida["x"], ida["y"]), _behavior_at("Route19", ida["x"], ida["y"])
    largura, celulas, attr = _grid("Route19")
    comp = lambda x, y: BEHAVIORS.get(attr(celulas[y * largura + x][0]) & 0x1FF)
    assert celulas[(ida["y"] + 1) * largura + ida["x"]][1] == 0 and comp(ida["x"], ida["y"] + 1) == "MB_SAND"
    # a casa (x 8-12, y 8-11) fica na areia do topo: nenhum objeto, sinal ou outro warp por baixo
    casa_xy = [(x, y) for y in range(8, 12) for x in range(8, 13)]
    for x, y in casa_xy:
        assert not [o for o in rota["object_events"] if (o["x"], o["y"]) == (x, y)], (x, y)
        assert not [b for b in rota["bg_events"] if (b["x"], b["y"]) == (x, y)], (x, y)
        assert not [w for w in rota["warp_events"] if (w["x"], w["y"]) == (x, y)] or (x, y) == (ida["x"], ida["y"])
        if (x, y) != (ida["x"], ida["y"]):
            assert celulas[y * largura + x][1] == 1, (x, y)
    # os treinadores continuam livres e fora da casa (o Richard saiu de (10, 9) para (13, 11))
    for o in rota["object_events"]:
        assert (o["x"], o["y"]) not in casa_xy, o["script"]
    assert [o for o in rota["object_events"] if o["script"] == "Route19_EventScript_Richard"][0]["x"] == 13
    # o caminho do norte (15, 0) até a beira da praia (13, 13): grafo dirigido por tiles livres, com os degraus
    # (MB_JUMP_*) como arestas de mão única. O pulo ignora o tile de pouso, então o pouso TEM de ser livre.
    livre = lambda x, y: 0 <= x < largura and 0 <= y < 14 and celulas[y * largura + x][1] == 0 \
        and "OCEAN" not in (comp(x, y) or "")
    ocupados = {(o["x"], o["y"]) for o in rota["object_events"]}
    saltos = {"MB_JUMP_EAST": (1, 0), "MB_JUMP_WEST": (-1, 0), "MB_JUMP_NORTH": (0, -1), "MB_JUMP_SOUTH": (0, 1)}
    arestas: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for y in range(14):
        for x in range(largura):
            if livre(x, y) and (x, y) not in ocupados:
                arestas.setdefault((x, y), set())
    for (x, y) in list(arestas):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p in arestas:
                arestas[(x, y)].add(p)
            elif 0 <= p[0] < largura and 0 <= p[1] < 14 and saltos.get(comp(*p)) == (dx, dy):
                pouso = (x + 2 * dx, y + 2 * dy)
                assert pouso in arestas, f"o degrau em {p} pousa em {pouso}, que está bloqueado (ficaria preso)"
                arestas[(x, y)].add(pouso)

    def alcanca(origens, grafo):
        fila, visto = list(origens), set(origens)
        while fila:
            for q in grafo.get(fila.pop(), ()):
                if q not in visto:
                    visto.add(q)
                    fila.append(q)
        return visto

    visto = alcanca([(15, 0)], arestas)
    assert (13, 13) in visto and (11, 13) in visto and (13, 12) not in visto, "o caminho para a praia fechou"
    inverso: dict[tuple[int, int], set[tuple[int, int]]] = {n: set() for n in arestas}
    for n, vizinhos in arestas.items():
        for q in vizinhos:
            inverso[q].add(n)
    saida = alcanca([(15, 0), (13, 13)], inverso)
    assert visto <= saida, f"becos sem saída (o jogador ficaria preso): {sorted(visto - saida)}"
    assert (9, 12) in visto, "a frente da porta tem de ser alcançável"
    # o pescador está no mapa interno com script próprio
    assert [o["script"] for o in casa["object_events"]] == ["Route19_UnusedHouse_EventScript_Pescador"]
    assert 'data/maps/Route19_UnusedHouse/text.inc' in (REPO_ROOT / "data/event_scripts.s").read_text("utf-8")
