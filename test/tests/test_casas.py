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
    assert nomes[-7:-5] == ["GetKrabbySizeRecordInfo", "CompareKrabbySize"], nomes[-8:]  # a Task 10 vem depois
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


# ---------- Task 10: a sala de troféus da Ilha Sete ----------
TROFEUS_C = (REPO_ROOT / "src" / "sala_trofeus.c").read_text(encoding="utf-8")
TROFEUS_H = (REPO_ROOT / "include" / "sala_trofeus.h").read_text(encoding="utf-8")
TROFEUS_K = (REPO_ROOT / "include" / "constants" / "sala_trofeus.h").read_text(encoding="utf-8")
TROFEUS_S = (REPO_ROOT / "data" / "maps" / "SevenIsland_UnusedHouse" / "scripts.inc").read_text(encoding="utf-8")
TROFEUS_T = (REPO_ROOT / "data" / "maps" / "SevenIsland_UnusedHouse" / "text.inc").read_text(encoding="utf-8")
GFX_INFO = (REPO_ROOT / "src" / "data" / "object_events" / "object_event_graphics_info.h").read_text(encoding="utf-8")
ROSAS = [("VERMELHA", "FLAG_FAMILIA_ROSA_1"), ("DOURADA", "FLAG_FAMILIA_ROSA_2"),
         ("AZUL", "FLAG_FAMILIA_ROSA_3"), ("NEGRA", "FLAG_FAMILIA_ROSA_4")]


def test_redomas_por_flag():
    """4 redomas (objetos de gráfico variável): a entrada no mapa troca a vazia pela redoma da cor quando a flag da
    rosa do chefe está ligada; a mesma flag decide o texto (vazia: "Uma redoma vazia…"; cheia: título + parágrafo)."""
    casa = _map("SevenIsland_UnusedHouse")
    domes = [o for o in casa["object_events"] if o["script"].startswith("SevenIsland_UnusedHouse_EventScript_Redoma")]
    assert [(o["x"], o["y"]) for o in domes] == [(2, 3), (4, 3), (6, 3), (8, 3)]
    transicao = TROFEUS_S[TROFEUS_S.index("OnTransition:"):TROFEUS_S.index("Taca_Escolher:")]
    for i, (cor, flag) in enumerate(ROSAS):
        assert domes[i]["graphics_id"] == f"OBJ_EVENT_GFX_VAR_{i}" and domes[i]["flag"] == "0"
        bloco = (f"\tsetvar VAR_OBJ_GFX_ID_{i}, OBJ_EVENT_GFX_REDOMA_VAZIA\n"
                 f"\tgoto_if_unset {flag}, SevenIsland_UnusedHouse_OnTransition_Redoma{i + 1}Pronta\n"
                 f"\tsetvar VAR_OBJ_GFX_ID_{i}, OBJ_EVENT_GFX_REDOMA_{cor}\n")
        assert bloco in transicao, cor
        exame = TROFEUS_S[TROFEUS_S.index(f"EventScript_Redoma{i + 1}::"):]
        assert f"goto_if_set {flag}, SevenIsland_UnusedHouse_EventScript_Redoma{i + 1}Cheia" in exame.split("\n\n")[0]
        assert f"msgbox SevenIsland_UnusedHouse_Text_Redoma{i + 1}, MSGBOX_SIGN" in exame
    assert "Uma redoma vazia…" in TROFEUS_T
    titulos = ["GENGAR, O DOM", "TYRANITAR, O COBRADOR", "GARCHOMP, O MERCENÁRIO", "DARKRAI, O PESADELO"]
    for i, t in enumerate(titulos):
        corpo = TROFEUS_T[TROFEUS_T.index(f"Text_Redoma{i + 1}::"):].split("$")[0]
        assert corpo.split("\n")[1].strip() == f'.string "{t}\\p"', t
        assert corpo.count("\\p") >= 2
    assert "dourada" in TROFEUS_T and "rosa azul" in TROFEUS_T and "rosa negra" in TROFEUS_T


def _nivel_taca(feitas: int, validas: int) -> int:
    """Espelho de SalaTrofeus_NivelDaTaca com os limites lidos do .h."""
    bronze = int(re.search(r"TACA_BRONZE_PCT\s+(\d+)", TROFEUS_H).group(1))
    prata = int(re.search(r"TACA_PRATA_PCT\s+(\d+)", TROFEUS_H).group(1))
    if validas == 0:
        return 0
    if feitas >= validas:
        return 3
    if feitas * 100 >= prata * validas:
        return 2
    if feitas * 100 >= bronze * validas:
        return 1
    return 0


def test_taca_limites():
    """Taça por % da aba: < 34 nada, >= 34 bronze, >= 67 prata, 100 ouro; o C tem a mesma regra do espelho."""
    assert re.search(r"TACA_BRONZE_PCT\s+34\b", TROFEUS_H) and re.search(r"TACA_PRATA_PCT\s+67\b", TROFEUS_H)
    for nome, v in (("NENHUMA", 0), ("BRONZE", 1), ("PRATA", 2), ("OURO", 3)):
        assert re.search(rf"#define TACA_{nome}\s+{v}\b", TROFEUS_K)
    fn = TROFEUS_C[TROFEUS_C.index("u8 SalaTrofeus_NivelDaTaca"):TROFEUS_C.index("// specialvar: VAR_0x8004")]
    assert "validas == 0" in fn and "feitas >= validas" in fn
    assert "feitas * 100 >= TACA_PRATA_PCT * validas" in fn and "feitas * 100 >= TACA_BRONZE_PCT * validas" in fn
    assert [_nivel_taca(f, 100) for f in (0, 33, 34, 66, 67, 99, 100)] == [0, 0, 1, 1, 2, 2, 3]
    assert [_nivel_taca(f, 9) for f in range(10)] == [0, 0, 0, 0, 1, 1, 1, 2, 2, 3]
    assert _nivel_taca(0, 0) == 0
    # só as ativas contam: o special usa Conquistas_ContarAba (válidas = ativas e não perdidas), sem número fixo
    assert "Conquistas_ContarAba" in TROFEUS_C and "44" not in TROFEUS_C and "46" not in TROFEUS_C
    nomes = re.findall(r"def_special (\w+)", SPECIALS.split("gSpecialsEnd::")[0])
    assert nomes[-5:] == ["SalaTrofeus_Taca", "SalaTrofeus_Placa", "SalaTrofeus_PlacaRevanche", "SalaTrofeus_PlacaHall",
                          "SalaTrofeus_Curador"]
    # as 5 taças: cada uma lê a sua aba (0-4 = História, Batalha, Captura, Treino, Exploração)
    for i in range(5):
        assert f"EventScript_Taca{i + 1}::\n\tgoto_if_questlog EventScript_ReleaseEnd\n\tsetvar VAR_0x8004, {i}\n" in TROFEUS_S
        assert (f"\tsetvar VAR_0x8004, {i}\n\tspecialvar VAR_RESULT, SalaTrofeus_Taca\n"
                f"\tcall SevenIsland_UnusedHouse_Taca_Escolher\n\tcopyvar VAR_OBJ_GFX_ID_{4 + i}, VAR_0x8005\n") in TROFEUS_S
        assert f"setflag FLAG_TEMP_{i + 1}\n" in TROFEUS_S
    # a placa mostra o total ativo pela mesma API, o diário e o Hall
    assert "Diario_ListarEmOrdem" in TROFEUS_C and "GAME_STAT_ENTERED_HOF" in TROFEUS_C
    assert "CONQ_REVANCHE_MAX" in TROFEUS_C


def test_casa_ilha7_ligada():
    """A casa nova da Ilha Sete: porta ligada nos dois sentidos, bloco de metatiles copiado da casa que já existe,
    frente da porta livre, nada coberto, mapa e ligações intactos, e o jogador nunca fica preso (degraus como
    arestas de mão única)."""
    ilha = _map("SevenIsland")
    casa = _map("SevenIsland_UnusedHouse")
    idas = [(i, w) for i, w in enumerate(ilha["warp_events"]) if w["dest_map"] == "MAP_SEVEN_ISLAND_UNUSED_HOUSE"]
    assert len(idas) == 1
    id_ida, ida = idas[0]
    assert (ida["x"], ida["y"]) == (17, 3) and ida["dest_warp_id"] == "0"
    voltas = casa["warp_events"]
    assert voltas and all(w["dest_map"] == "MAP_SEVEN_ISLAND" and int(w["dest_warp_id"]) == id_ida for w in voltas)
    # o resto da ilha ficou como estava: os 4 warps antigos, as ligações (Torre e baixo) e o tamanho
    assert [(w["x"], w["y"], w["dest_map"]) for w in ilha["warp_events"][:4]] == [
        (11, 9, "MAP_SEVEN_ISLAND_HOUSE_ROOM1"), (5, 9, "MAP_SEVEN_ISLAND_MART"),
        (12, 3, "MAP_SEVEN_ISLAND_POKEMON_CENTER_1F"), (16, 13, "MAP_SEVEN_ISLAND_HARBOR")]
    assert ilha["connections"] == [{"map": "MAP_SEVEN_ISLAND_TRAINER_TOWER", "offset": -48, "direction": "up"},
                                   {"map": "MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE", "offset": 0, "direction": "down"}]
    largura, celulas, attr = _grid("SevenIsland")
    assert largura == 24 and len(celulas) == 24 * 20
    assert "DOOR" in _behavior_at("SevenIsland", 17, 3), _behavior_at("SevenIsland", 17, 3)
    # o bloco 5x4 (x 16-20, y 0-3) é a cópia crua da casa roxa (x 10-14, y 6-9): nenhum metatile novo
    for j in range(4):
        for i in range(5):
            assert celulas[j * largura + 16 + i] == celulas[(6 + j) * largura + 10 + i], (16 + i, j)
    casa_xy = {(x, y) for y in range(4) for x in range(16, 21)}
    for x, y in casa_xy:
        assert not [o for o in ilha["object_events"] if (o["x"], o["y"]) == (x, y)], (x, y)
        assert not [b for b in ilha["bg_events"] if (b["x"], b["y"]) == (x, y)], (x, y)
        assert not [w for w in ilha["warp_events"] if (w["x"], w["y"]) == (x, y)] or (x, y) == (17, 3)
    assert celulas[4 * largura + 17][1] == 0, "frente da porta bloqueada"
    # grafo dirigido: tiles livres (colisão 0, sem água), degraus MB_JUMP_* de mão única; o pouso tem de ser livre
    comp = lambda x, y: BEHAVIORS.get(attr(celulas[y * largura + x][0]) & 0x1FF) or ""
    alt = 20
    livre = lambda x, y: 0 <= x < largura and 0 <= y < alt and celulas[y * largura + x][1] == 0 \
        and "WATER" not in comp(x, y) and "OCEAN" not in comp(x, y)
    saltos = {"MB_JUMP_EAST": (1, 0), "MB_JUMP_WEST": (-1, 0), "MB_JUMP_NORTH": (0, -1), "MB_JUMP_SOUTH": (0, 1)}
    nos = {(x, y) for y in range(alt) for x in range(largura) if livre(x, y)}
    arestas: dict[tuple[int, int], set[tuple[int, int]]] = {n: set() for n in nos}
    for (x, y) in nos:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p in nos:
                arestas[(x, y)].add(p)
            elif 0 <= p[0] < largura and 0 <= p[1] < alt and saltos.get(comp(*p)) == (dx, dy):
                pouso = (x + 2 * dx, y + 2 * dy)
                assert pouso in nos, f"o degrau em {p} pousa em {pouso}, que está bloqueado (ficaria preso)"
                arestas[(x, y)].add(pouso)

    def alcanca(origens, grafo):
        fila, visto = list(origens), set(origens)
        while fila:
            for q in grafo.get(fila.pop(), ()):
                if q not in visto:
                    visto.add(q)
                    fila.append(q)
        return visto

    inicio = (12, 4)   # a frente do Centro Pokémon
    assert inicio in nos
    visto = alcanca([inicio], arestas)
    assert (17, 4) in visto and (16, 4) in visto, "a frente da casa nova tem de ser alcançável a pé"
    inverso: dict[tuple[int, int], set[tuple[int, int]]] = {n: set() for n in arestas}
    for n, vizinhos in arestas.items():
        for q in vizinhos:
            inverso[q].add(n)
    volta = alcanca([inicio], inverso)
    assert visto <= volta, f"becos sem saída: {sorted(visto - volta)}"
    for w in ilha["warp_events"]:
        assert (w["x"], w["y"] + 1) in visto or (w["x"], w["y"]) in visto, (w["x"], w["y"])
    # dentro: curador e placa por último, layout próprio (a HOUSE4 é compartilhada), texto incluído no build
    scripts = [o["script"] for o in casa["object_events"]]
    assert scripts[-2:] == ["SevenIsland_UnusedHouse_EventScript_Curador", "SevenIsland_UnusedHouse_EventScript_Placa"]
    assert casa["layout"] == "LAYOUT_SEVEN_ISLAND_TROPHY_ROOM"
    assert 'data/maps/SevenIsland_UnusedHouse/text.inc' in (REPO_ROOT / "data/event_scripts.s").read_text("utf-8")
    # paletas na sala: redomas nos slots 1-2, taças no 3; curador e placa são NPCs comuns do slot 4 (sem choque)
    slots = json.loads((REPO_ROOT / "tools/familia_sombra/slots.json").read_text(encoding="utf-8"))["slots"]
    assert {slots[f"OBJ_EVENT_GFX_REDOMA_{n}"] for n in ("VAZIA", "VERMELHA", "DOURADA")} == {"PALSLOT_NPC_1"}
    assert {slots["OBJ_EVENT_GFX_REDOMA_AZUL"], slots["OBJ_EVENT_GFX_REDOMA_NEGRA"]} == {"PALSLOT_NPC_2"}
    assert {slots[f"OBJ_EVENT_GFX_TACA_{n}"] for n in ("BRONZE", "PRATA", "OURO")} == {"PALSLOT_NPC_3"}
    for g in ("Gentleman", "Sign"):
        corpo = GFX_INFO[GFX_INFO.index(f"gObjectEventGraphicsInfo_{g} ="):].split("};")[0]
        assert "PALSLOT_NPC_4" in corpo, g


def test_placa_maior_revanche():
    """A placa mostra o MAIOR degrau de revanche vencido: var própria e livre, gravada só quando o degrau novo é maior
    (pelos dois ganchos: revanche do Vs. Seeker e Liga), rótulo do degrau; 0 = nenhuma ainda; save antigo com a
    conquista do Nível 100 feita vale o degrau máximo."""
    m = re.search(r"#define VAR_REVANCHE_MAIOR_DEGRAU\s+(0x40[0-9A-Fa-f]{2})\s+// POK-51", VARS_H)
    assert m and 0x4020 <= int(m.group(1), 16) <= 0x40FF
    valores = re.findall(r"#define VAR_\w+\s+(0x40[0-9A-Fa-f]{2})\b", VARS_H)
    assert valores.count(m.group(1)) == 1 and "VAR_0x40F2" not in VARS_H
    rematch = (REPO_ROOT / "src" / "rematch_tier.c").read_text(encoding="utf-8")
    reg = rematch[rematch.index("static void RegistrarDegrauVencido"):rematch.index("void RematchTier_OnRematchWon")]
    assert "tier > VarGet(VAR_REVANCHE_MAIOR_DEGRAU)" in reg and "VarSet(VAR_REVANCHE_MAIOR_DEGRAU, tier)" in reg
    assert "tier >= 1 && tier <= REMATCH_TIER_MAX" in reg
    for nome in ("OnRematchWon", "OnLeagueCleared"):
        gancho = f"void RematchTier_{nome}(u8 tier)\n{{\n    RegistrarDegrauVencido(tier);"
        assert gancho in rematch, gancho
    assert "RematchTier_OnRematchWon(GetCurrentBattleRematchTier())" in (REPO_ROOT / "src/battle_setup.c").read_text("utf-8")
    assert "RematchTier_OnLeagueCleared(GetCurrentBattleRematchTier())" in         (REPO_ROOT / "src/post_battle_event_funcs.c").read_text("utf-8")
    fn = TROFEUS_C[TROFEUS_C.index("u16 SalaTrofeus_PlacaRevanche"):]
    fn = fn[:fn.index("// special: STR_VAR_1 = vezes no Hall")]
    assert "VarGet(VAR_REVANCHE_MAIOR_DEGRAU)" in fn and "degrau == 0 && Conquistas_GetEstado(CONQ_REVANCHE_MAX) == CONQ_FEITA" in fn
    assert "GetRematchTierName(degrau)" in fn
    assert "const u8 *GetRematchTierName(u8 tier);" in (REPO_ROOT / "include/rematch_tier.h").read_text("utf-8")
    assert "specialvar VAR_RESULT, SalaTrofeus_PlacaRevanche" in TROFEUS_S
    assert "Text_PlacaRevanche::" in TROFEUS_T and "{STR_VAR_1}." in TROFEUS_T and "nenhuma ainda." in TROFEUS_T
    assert "nenhuma até o Nível 100" not in TROFEUS_T


def test_curador_singular():
    """"Falta 1 taça de ouro" no singular; plural nos demais."""
    assert "goto_if_eq VAR_0x8005, 1, SevenIsland_UnusedHouse_EventScript_CuradorUmaTaca" in TROFEUS_S
    assert "Falta {STR_VAR_1} taça de ouro" in TROFEUS_T and "Faltam {STR_VAR_1} taças de ouro" in TROFEUS_T


def test_telas_da_familia_e_das_casas_no_fim_de_shared_points():
    """POK-51, Task 11: as telas dos cenários `familia` e `casas` entram no fim de SHARED_POINTS (referências em
    COMUM/), e os dois cenários podem ser vistos no `test-watch`."""
    from esteira import refs
    from esteira.__main__ import WATCH_FULL_SCENARIOS
    from esteira.scenarios import full_casas, full_familia
    assert refs.FAMILIA_POINTS == full_familia.SCREEN_POINTS and refs.CASAS_POINTS == full_casas.SCREEN_POINTS
    fim = refs.SHARED_POINTS[-len(refs.FAMILIA_POINTS) - len(refs.CASAS_POINTS):]
    assert fim == refs.FAMILIA_POINTS + refs.CASAS_POINTS
    assert len(set(refs.SHARED_POINTS)) == len(refs.SHARED_POINTS)
    for pontos, arquivo in ((refs.FAMILIA_POINTS, "full_familia.py"), (refs.CASAS_POINTS, "full_casas.py")):
        texto = (REPO_ROOT / "test" / "esteira" / "scenarios" / arquivo).read_text(encoding="utf-8")
        for ponto in pontos:   # além da própria tupla, o cenário grava a tela com esse nome
            assert texto.count(f'"{ponto}"') >= 2, ponto
    assert {"familia", "casas"} <= set(WATCH_FULL_SCENARIOS)
