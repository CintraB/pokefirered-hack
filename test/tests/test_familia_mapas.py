"""POK-51 (Task 5): o prédio da Família Sombra na Rota 23. Leitura estática dos mapas, layouts, tilesets e scripts.

O prédio fica na parte sul da Rota 23 (porta em (4, 149)); o Route23_UnusedHouse virou o 1º andar e os andares 2 a 6
são mapas novos (Route23_FamiliaSombra_<n>F). `tools/familia_sombra/predio.py` gera o tileset `familia_sombra`, o
prédio no tileset do Platô Índigo, a Rota 23 e os 6 layouts. O comportamento no jogo fica no cenário `familia`
(porta trancada, ciclo, subida, encontros dos andares 4-5, gêmeos, fuga e a rosa).
"""

import json
import os
import re
import struct
import subprocess
import sys

from esteira.scenarios import REPO_ROOT

MAPS = REPO_ROOT / "data" / "maps"
NOMES = {1: "Route23_UnusedHouse", **{n: f"Route23_FamiliaSombra_{n}F" for n in range(2, 7)}}
IDS = {1: "MAP_ROUTE23_UNUSED_HOUSE", **{n: f"MAP_ROUTE23_FAMILIA_SOMBRA_{n}F" for n in range(2, 7)}}
FAMILIA_C = (REPO_ROOT / "src" / "familia_sombra.c").read_text(encoding="utf-8")
TIMES_H = (REPO_ROOT / "src" / "data" / "familia_sombra_times.h").read_text(encoding="utf-8")
PREDIO = json.loads((REPO_ROOT / "tools" / "familia_sombra" / "predio.json").read_text(encoding="utf-8"))
SLOTS = json.loads((REPO_ROOT / "tools" / "familia_sombra" / "slots.json").read_text(encoding="utf-8"))["slots"]
LAYOUTS = {l["id"]: l for l in json.loads((REPO_ROOT / "data/layouts/layouts.json").read_text("utf-8"))["layouts"]
           if "id" in l}
BEHAVIORS = {int(v, 0): n for n, v in re.findall(
    r"#define (MB_\w+)\s+(0x[0-9A-Fa-f]+|\d+)", (REPO_ROOT / "include/constants/metatile_behaviors.h").read_text())}
MAX_SECUNDARIO = 384
TILE_ENCOUNTER_LAND = 1


def _map(nome: str) -> dict:
    return json.loads((MAPS / nome / "map.json").read_text(encoding="utf-8"))


def _all_maps() -> dict[str, dict]:
    out = {}
    for pasta in MAPS.iterdir():
        f = pasta / "map.json"
        if f.is_file():
            m = json.loads(f.read_text(encoding="utf-8"))
            out[m["id"]] = m
    return out


def _attrs(tileset_sym: str) -> list[int]:
    nome = tileset_sym.replace("gTileset_", "")
    texto = (REPO_ROOT / "src/data/tilesets/metatiles.h").read_text(encoding="utf-8")
    m = re.search(rf'gMetatileAttributes_{nome}\[\] = INCBIN_U32\("([^"]+)"\)', texto)
    raw = (REPO_ROOT / m.group(1)).read_bytes()
    return list(struct.unpack(f"<{len(raw) // 4}I", raw))


def _grid(nome: str):
    """(largura, células [(metatile, colisão)], atributo do metatile)."""
    layout = LAYOUTS[_map(nome)["layout"]]
    raw = (REPO_ROOT / layout["blockdata_filepath"]).read_bytes()
    vals = struct.unpack(f"<{len(raw) // 2}H", raw)
    prim, sec = _attrs(layout["primary_tileset"]), _attrs(layout["secondary_tileset"])

    def attr(mid: int) -> int:
        return prim[mid] if mid < 640 else sec[mid - 640]

    return layout["width"], [(v & 0x3FF, (v >> 10) & 3) for v in vals], attr


def _behavior_at(nome: str, x: int, y: int) -> str:
    w, cells, attr = _grid(nome)
    return BEHAVIORS.get(attr(cells[y * w + x][0]) & 0x1FF, "?")


# ---------- os andares ----------
def test_seis_andares_ligados():
    todos = _all_maps()
    grupos = json.loads((MAPS / "map_groups.json").read_text(encoding="utf-8"))
    assert grupos["gMapGroup_IndoorRoute23"] == [NOMES[n] for n in range(1, 7)]
    rota = todos["MAP_ROUTE23"]
    porta = [i for i, w in enumerate(rota["warp_events"]) if w["dest_map"] == IDS[1]]
    assert len(porta) == 1 and (rota["warp_events"][porta[0]]["x"], rota["warp_events"][porta[0]]["y"]) == (4, 149)
    # cada warp de cada andar leva a um warp que existe, e esse volta para o mesmo lugar
    for n in range(1, 7):
        m = todos[IDS[n]]
        assert m["layout"] == f"LAYOUT_ROUTE23_FAMILIA_SOMBRA_{n}F" and m["layout"] in LAYOUTS
        for i, w in enumerate(m["warp_events"]):
            dest = todos[w["dest_map"]]
            volta = dest["warp_events"][int(w["dest_warp_id"])]
            assert volta["dest_map"] == IDS[n] and int(volta["dest_warp_id"]) == i, (n, i, w, volta)
    destinos = {n: [w["dest_map"] for w in todos[IDS[n]]["warp_events"]] for n in range(1, 7)}
    assert destinos[1] == ["MAP_ROUTE23", IDS[2]]
    for n in range(2, 6):
        assert destinos[n] == [IDS[n - 1], IDS[n + 1]], n
    assert destinos[6] == [IDS[5]]
    # o tile de cada warp tem o comportamento certo (porta, tapete de saída, escadas)
    assert _behavior_at("Route23", 4, 149) == "MB_WARP_DOOR"   # METATILE_General_Door
    esperado = {1: ["MB_SOUTH_ARROW_WARP", "MB_UP_RIGHT_STAIR_WARP"], 6: ["MB_DOWN_LEFT_STAIR_WARP"]}
    for n in range(1, 7):
        comps = [_behavior_at(NOMES[n], w["x"], w["y"]) for w in todos[IDS[n]]["warp_events"]]
        assert comps == esperado.get(n, ["MB_DOWN_LEFT_STAIR_WARP", "MB_UP_RIGHT_STAIR_WARP"]), (n, comps)
    # o C conhece os 6 andares (FamiliaSombra_NoPredio, Ruling R2) e os 2 escuros
    bloco = FAMILIA_C[FAMILIA_C.index("sAndares[] ="):]
    bloco = bloco[:bloco.index("};")]
    assert re.findall(r"MAP_\w+", bloco) == [IDS[n] for n in range(1, 7)]
    escuros = FAMILIA_C[FAMILIA_C.index("sAndaresEscuros[] ="):]
    escuros = escuros[:escuros.index("};")]
    assert re.findall(r"MAP_\w+", escuros) == [IDS[4], IDS[5]]


def test_objetos_e_eventos_em_tile_livre():
    """Capangas, itens, a cena e as placas: objetos e gatilhos em tiles livres, placas olhando para um móvel."""
    for n in range(1, 7):
        w, cells, _attr = _grid(NOMES[n])
        m = _map(NOMES[n])
        livres = {(i % w, i // w) for i, (_mid, col) in enumerate(cells) if col == 0}
        for o in m["object_events"]:
            if o["local_id"] != "LOCALID_FAMILIA_6F_CHEFE":   # o chefe fica na poltrona, atrás da mesa
                assert (o["x"], o["y"]) in livres, (n, o["local_id"])
        for c in m["coord_events"]:
            assert (c["x"], c["y"]) in livres, (n, c)
        for b in m["bg_events"]:
            assert (b["x"], b["y"]) not in livres and (b["x"], b["y"] + 1) in livres, (n, b)


def test_capangas_como_treinadores():
    """3 capangas por andar nos andares 1-3 (slots 1-9 na ordem), visão 3-4, a flag do treinador esconde o objeto e
    o gráfico vem de VAR_OBJ_GFX_ID_0..2 (FamiliaSombra_PrepararAndar)."""
    slot = 0
    for n in range(1, 4):
        capangas = [o for o in _map(NOMES[n])["object_events"] if "CAPANGA" in o["local_id"]]
        assert len(capangas) == 3
        for i, o in enumerate(capangas):
            slot += 1
            assert o["trainer_type"] == "TRAINER_TYPE_NORMAL" and o["trainer_sight_or_berry_tree_id"] in ("3", "4")
            assert o["flag"] == f"TRAINER_FLAGS_START + TRAINER_FAMILIA_CAPANGA_{slot}"
            assert o["graphics_id"] == f"OBJ_EVENT_GFX_VAR_{i}"
            script = (MAPS / NOMES[n] / "scripts.inc").read_text(encoding="utf-8")
            assert re.search(rf"^{o['script']}::\n\ttrainerbattle_single TRAINER_FAMILIA_CAPANGA_{slot},", script, re.M)
    for n in (4, 5, 6):
        assert not [o for o in _map(NOMES[n])["object_events"] if "CAPANGA" in o["local_id"]]


def test_musica_e_clima_por_andar():
    esperado = {1: ("MUS_ROCKET_HIDEOUT", "WEATHER_SHADE", False), 2: ("MUS_ROCKET_HIDEOUT", "WEATHER_SHADE", False),
                3: ("MUS_ROCKET_HIDEOUT", "WEATHER_SHADE", False), 4: ("MUS_POKE_TOWER", "WEATHER_FOG_HORIZONTAL", True),
                5: ("MUS_POKE_TOWER", "WEATHER_FOG_HORIZONTAL", True), 6: ("MUS_NONE", "WEATHER_NONE", False)}
    for n, (musica, clima, escuro) in esperado.items():
        m = _map(NOMES[n])
        assert (m["music"], m["weather"], m["requires_flash"], m["map_type"]) == (musica, clima, escuro,
                                                                                 "MAP_TYPE_INDOOR"), n
    # o chefe fala em silêncio e a música da Rocket entra com a fala dele
    cena = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    cena = cena[cena.index("Route23_FamiliaSombra_6F_EventScript_Cena::"):]
    assert cena.index("playbgm MUS_ENCOUNTER_ROCKET") < cena.index("FalaDom")


def test_andares_escuros_pisam_em_terra():
    """Os encontros dos andares 4-5 só acontecem em metatile TILE_ENCOUNTER_LAND, e nenhum dos dois tem tabela."""
    for n in (4, 5):
        w, cells, attr = _grid(NOMES[n])
        warps = {(wp["x"], wp["y"]) for wp in _map(NOMES[n])["warp_events"]}
        for i, (mid, col) in enumerate(cells):
            if col == 0 and (i % w, i // w) not in warps:
                assert (attr(mid) >> 24) & 7 == TILE_ENCOUNTER_LAND, (n, i % w, i // w, hex(mid))
    encontros = (REPO_ROOT / "src/data/wild_encounters.json").read_text(encoding="utf-8")
    assert "ROUTE23_FAMILIA_SOMBRA" not in encontros and "ROUTE23_UNUSED_HOUSE" not in encontros


def test_flash_travado_4_5():
    overworld = (REPO_ROOT / "src/overworld.c").read_text(encoding="utf-8")
    corpo = re.search(r"static void SetDefaultFlashLevel\(void\)\n\{(.*?)\n\}", overworld, re.S).group(1)
    escuro = corpo.index("FamiliaSombra_EhAndarEscuro()")
    assert escuro < corpo.index("FlagGet(FLAG_SYS_FLASH_ACTIVE)") < corpo.index("CanUseFieldMove(MOVE_FLASH)")
    trecho = corpo[escuro:corpo.index("}", escuro)]
    assert "flashLevel = gMaxFlashLevel" in trecho and "FlagClear(FLAG_SYS_FLASH_ACTIVE)" in trecho
    flash = (REPO_ROOT / "src/fldeff_flash.c").read_text(encoding="utf-8")
    corpo = re.search(r"bool8 SetUpFieldMove_Flash\(void\)\n\{(.*?)\n\}", flash, re.S).group(1)
    assert corpo.index("FamiliaSombra_EhAndarEscuro()") < corpo.index("gFieldCallback2")


def _script_de(nome_mapa: str, label: str) -> str:
    texto = ((MAPS / nome_mapa / "scripts.inc").read_text(encoding="utf-8")
             + (MAPS / NOMES[1] / "scripts.inc").read_text(encoding="utf-8"))
    corpo = texto[texto.index(f"{label}::"):]
    return corpo[:corpo.index("\tend")]


def test_itens_do_chao():
    """A tabela do spec §6.4 (maleta = addmoney + "Você achou ¥X numa maleta!"), cada objeto com a flag do andar."""
    esperado = {1: ["ITEM_PEARL x1", "¥2000"], 2: ["ITEM_PEARL x2", "¥3000"], 3: ["ITEM_BIG_PEARL x1", "¥5000"],
                4: ["ITEM_BIG_PEARL x1", "ITEM_NUGGET x1"], 5: ["ITEM_NUGGET x2", "¥10000"]}
    textos = (MAPS / NOMES[1] / "text.inc").read_text(encoding="utf-8")
    for n, itens in esperado.items():
        objs = [o for o in _map(NOMES[n])["object_events"] if o["graphics_id"] == "OBJ_EVENT_GFX_ITEM_BALL"]
        achados = []
        for k, o in enumerate(objs, 1):
            assert o["flag"] == f"FLAG_FAMILIA_ITEM_{n}_{k}", (n, o)
            corpo = _script_de(NOMES[n], o["script"])
            if m := re.search(r"finditem (ITEM_\w+)(?:, (\d+))?", corpo):
                achados.append(f"{m.group(1)} x{m.group(2) or 1}")
            else:
                valor = int(re.search(r"addmoney (\d+)", corpo).group(1))
                assert "removeobject VAR_LAST_TALKED" in corpo
                texto = re.search(r"message (\w+)", corpo).group(1)
                bloco = textos[textos.index(f"{texto}::"):].split("\n")[1]
                assert bloco == f'    .string "Você achou ¥{valor:,}'.replace(",", ".") + ' numa maleta!$"', bloco
                achados.append(f"¥{valor}")
        assert achados == itens, (n, achados)
    assert not [o for o in _map(NOMES[6])["object_events"] if o["graphics_id"] == "OBJ_EVENT_GFX_ITEM_BALL"]


def _especies(tabela: str) -> list[list[str]]:
    corpo = TIMES_H[TIMES_H.index(f"{tabela}["):]
    corpo = corpo[corpo.index("{") + 1:]
    out, prof, ini = [], 0, 0
    for i, ch in enumerate(corpo):
        if ch == "{":
            prof += 1
            if prof == 1:
                ini = i
        elif ch == "}":
            prof -= 1
            if prof == 0:
                out.append(re.findall(r"MEMBRO\((\w+),", corpo[ini:i]))
            if prof < 0:
                return out
    raise AssertionError(tabela)


def _gfx_da_especie() -> dict[str, str]:
    corpo = FAMILIA_C[FAMILIA_C.index("sGfxDaEspecie[][2] ="):]
    return dict(re.findall(r"\{SPECIES_(\w+),\s*(OBJ_EVENT_GFX_FAMILIA_\w+)\}", corpo[:corpo.index("};")]))


def test_familia_paletas_por_andar():
    """Review Focus 1: em cada andar e ocupação, nenhum slot de paleta PALSLOT_NPC_* repetido entre gráficos
    diferentes e no máximo 4 espécies (a Poké Bola do chão usa o PALSLOT_NPC_4)."""
    gfx = _gfx_da_especie()
    capangas, gemeos = _especies("sFamiliaCapangas"), _especies("sFamiliaGemeos")
    corpo = TIMES_H[TIMES_H.index("sFamiliaChefes["):]
    chefes = re.findall(r"MEMBRO\((\w+),", corpo[:corpo.index("};")])
    assert len(chefes) == len(capangas) == len(gemeos) == 4
    for ocupacao in range(4):
        for n in range(1, 7):
            no_mapa = []
            for o in _map(NOMES[n])["object_events"]:
                g = o["graphics_id"]
                if g.startswith("OBJ_EVENT_GFX_VAR_"):
                    i = int(g[-1])
                    if n <= 3:
                        especie = capangas[ocupacao][(n - 1) * 3 + i]
                        g = gfx[especie]
                    else:
                        especie = chefes[ocupacao] if i == 0 else gemeos[ocupacao][0]
                        g = gfx.get(especie, "OBJ_EVENT_GFX_FAMILIA_GENGAR_SHINY" if i == 0
                                    else "OBJ_EVENT_GFX_FAMILIA_MACHAMP")
                no_mapa.append(g)
            unicos = set(no_mapa)
            slots = {}
            for g in unicos:
                slot = "PALSLOT_NPC_4" if g == "OBJ_EVENT_GFX_ITEM_BALL" else SLOTS[g]
                assert slot not in slots, f"ocupação {ocupacao + 1}, {n}º andar: {g} e {slots[slot]} no {slot}"
                slots[slot] = g
            assert len(unicos) <= 4, (ocupacao + 1, n, unicos)


def test_tileset_cabe():
    fam, indigo = PREDIO["familia_sombra"], PREDIO["indigo_plateau"]
    assert fam["ladrilhos"] <= MAX_SECUNDARIO and fam["metatiles"] <= MAX_SECUNDARIO
    assert indigo["ladrilhos"] <= MAX_SECUNDARIO
    regras = (REPO_ROOT / "tileset_rules.mk").read_text(encoding="utf-8")
    for pasta, n in (("familia_sombra", fam["ladrilhos"]), ("indigo_plateau", indigo["ladrilhos"])):
        assert re.search(rf"secondary/{pasta}/tiles\.4bpp: %\.4bpp: %\.png\n\t\$\(GFX\) \$< \$@ -num_tiles {n} ", regras)
    for nome, pasta in (("FamiliaSombra", "familia_sombra"), ("IndigoPlateau", "indigo_plateau")):
        raw = (REPO_ROOT / f"data/tilesets/secondary/{pasta}/metatiles.bin").read_bytes()
        attrs = (REPO_ROOT / f"data/tilesets/secondary/{pasta}/metatile_attributes.bin").read_bytes()
        assert len(raw) // 16 == len(attrs) // 4 <= MAX_SECUNDARIO, nome
        assert f"const struct Tileset gTileset_{nome} =" in (REPO_ROOT / "src/data/tilesets/headers.h").read_text()
    labels = (REPO_ROOT / "include/constants/metatile_labels.h").read_text(encoding="utf-8")
    assert re.search(rf"#define METATILE_IndigoPlateau_FamiliaPortaTrancada\s+{indigo['porta_trancada']:#x}\b", labels)


def test_gerador_confere():
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    r = subprocess.run([sys.executable, "-I", str(REPO_ROOT / "tools/familia_sombra/predio.py"), "--conferir"],
                       capture_output=True, text=True, env=env, cwd=REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_porta_trancada_antes_da_insignia():
    scripts = (MAPS / "Route23" / "scripts.inc").read_text(encoding="utf-8")
    assert "map_script MAP_SCRIPT_ON_LOAD, Route23_OnLoad" in scripts
    assert "setmetatile 4, 149, METATILE_IndigoPlateau_FamiliaPortaTrancada, TRUE" in scripts
    transicao = scripts[scripts.index("Route23_OnTransition::"):]
    assert transicao.split("\n")[1] == "\tspecial FamiliaSombra_Atualizar"
    andar1 = (MAPS / NOMES[1] / "scripts.inc").read_text(encoding="utf-8")
    assert "Route23_UnusedHouse_OnTransition::\n\tspecial FamiliaSombra_Atualizar" in andar1
    texto = (MAPS / "Route23" / "text.inc").read_text(encoding="utf-8")
    assert '"A porta está trancada. Há um\\n"\n    .string "cheiro de charuto…$"' in texto


def test_titulos_em_destaque():
    """Toda fala ou bilhete que cita o chefe pelo título usa as maiúsculas ("GENGAR, O DOM", "TYRANITAR, O
    COBRADOR"); nada de "Gengar, o Dom" em minúsculas."""
    for n in range(1, 7):
        texto = (MAPS / NOMES[n] / "text.inc").read_text(encoding="utf-8")
        assert not re.search(r"(?i)gengar, o dom", texto.replace("GENGAR, O DOM", "")), n
        assert not re.search(r"(?i)tyranitar, o cobrador", texto.replace("TYRANITAR, O COBRADOR", "")), n
    sala = (MAPS / NOMES[6] / "text.inc").read_text(encoding="utf-8")
    assert sala.count("GENGAR, O DOM") >= 3 and sala.count("TYRANITAR, O COBRADOR") >= 3
    assert '"Os gêmeos só lutam em dupla.$"' in sala
    assert '"buscar alguém de fora…”$"' in sala


def test_chefe_caiu_uma_vez_so():
    corpo = re.search(r"void FamiliaSombra_ChefeCaiu\(void\)\n\{(.*?)\n\}", FAMILIA_C, re.S).group(1)
    assert corpo.index("if (!FamiliaSombra_ChefeAtivo())") < corpo.index("VarSet(VAR_FAMILIA_QUEDA")


def test_cena_do_chefe():
    """Spec §6.5: fala → dupla dos gêmeos (com o id do gêmeo, continua num script) → fala → o chefe (special) →
    venceu ou capturou: ChefeCaiu e a rosa da ocupação; fugiu ou perdeu: o chefe fica."""
    s = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    assert s.count("trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE, TRAINER_FAMILIA_GEMEOS, "
                   "LOCALID_FAMILIA_6F_GEMEO_A,") == 4
    chefe = s[s.index("Route23_FamiliaSombra_6F_EventScript_Chefe::"):]
    ordem = ["special FamiliaSombra_IniciarChefe", "waitstate", "GetBattleOutcome", "B_OUTCOME_WON",
             "B_OUTCOME_CAUGHT"]
    pos = [chefe.index(p) for p in ordem]
    assert pos == sorted(pos)
    caiu = s[s.index("Route23_FamiliaSombra_6F_EventScript_ChefeCaiu::"):]
    assert caiu.index("special FamiliaSombra_ChefeCaiu") < caiu.index("giveitem ITEM_ROSA_VERMELHA")
    assert "giveitem ITEM_ROSA_DOURADA" in s
    m6 = _map(NOMES[6])
    assert {c["var"] for c in m6["coord_events"]} == {"VAR_TEMP_1"}
    assert {(o["local_id"], o["flag"]) for o in m6["object_events"]} == {
        ("LOCALID_FAMILIA_6F_CHEFE", "FLAG_TEMP_1"), ("LOCALID_FAMILIA_6F_GEMEO_A", "FLAG_FAMILIA_GEMEOS_VENCIDOS"),
        ("LOCALID_FAMILIA_6F_GEMEO_B", "FLAG_FAMILIA_GEMEOS_VENCIDOS")}


# ---------- o pedágio (Task 6) ----------
def _rota23_scripts() -> str:
    return (MAPS / "Route23" / "scripts.inc").read_text(encoding="utf-8")


def _rotulo(texto: str, nome: str) -> str:
    """Corpo de um rótulo `nome::`/`nome:` até o próximo rótulo global."""
    i = texto.index(f"\n{nome}:")
    m = re.search(r"\n\w+::", texto[i + 1:])
    return texto[i: i + 1 + m.start()] if m else texto[i:]


def test_pedagio_valor():
    """¥1.000 (constante do C, a única fonte) e o script cobra com checkmoney/removemoney dessa constante."""
    assert re.search(r"#define FAMILIA_PEDAGIO\s+1000\b",
                     (REPO_ROOT / "include/constants/familia_sombra.h").read_text(encoding="utf-8"))
    s = _rota23_scripts()
    pedagio = _rotulo(s, "Route23_EventScript_Pedagio")
    assert "checkmoney FAMILIA_PEDAGIO" in pedagio and "removemoney FAMILIA_PEDAGIO" in pedagio
    assert pedagio.index("removemoney") < pedagio.index("setflag FLAG_FAMILIA_PEDAGIO_PAGO")
    # sem dinheiro vai direto ao menu, sem a pergunta de pagar; recusar também termina no menu
    assert "Route23_EventScript_PedagioSemDinheiro" in pedagio
    assert re.search(r"Route23_EventScript_PedagioSemDinheiro::\n(?:\t.*\n)*?\tgoto Route23_EventScript_PedagioMenu", s)
    assert re.search(r"Route23_EventScript_PedagioRecusou::\n(?:\t.*\n)*?\tgoto Route23_EventScript_PedagioMenu", s)
    assert "¥1.000" in (MAPS / "Route23" / "text.inc").read_text(encoding="utf-8")


def test_pedagio_forca_e_menu():
    s = _rota23_scripts()
    menu = _rotulo(s, "Route23_EventScript_PedagioMenu")
    assert "multichoice 17, 6, MULTICHOICE_PEDAGIO, FALSE" in menu
    forca = _rotulo(s, "Route23_EventScript_PedagioForca")
    ordem = ["special FamiliaSombra_SortearPedagio", "trainerbattle_no_intro TRAINER_FAMILIA_PEDAGIO_1,",
             "trainerbattle_no_intro TRAINER_FAMILIA_PEDAGIO_2,", "special FamiliaSombra_PedagioVencido"]
    pos = [forca.index(p) for p in ordem]
    assert pos == sorted(pos)
    # R5: o fim da passagem forçada é um special que liga a flag; a conquista é da Task 7
    assert "def_special FamiliaSombra_PedagioVencido" in (REPO_ROOT / "data/specials.inc").read_text(encoding="utf-8")
    corpo = re.search(r"void FamiliaSombra_PedagioVencido\(void\)\n\{(.*?)\n\}", FAMILIA_C, re.S).group(1)
    assert "FlagSet(FLAG_FAMILIA_PEDAGIO_PAGO);" in corpo
    # menu novo: id 66 e os dois rótulos na ordem voltar (0) / força (1)
    menu_h = (REPO_ROOT / "include/constants/menu.h").read_text(encoding="utf-8")
    assert re.search(r"#define MULTICHOICE_PEDAGIO\s+66\b", menu_h)
    sm = (REPO_ROOT / "src/script_menu.c").read_text(encoding="utf-8")
    assert re.search(r"sMultichoiceList_Pedagio\[\] = \{\s*\{ gText_PedagioVoltarDepois \},\s*"
                     r"\{ gText_PedagioPassarAForca \}\s*\}", sm)
    assert "[MULTICHOICE_PEDAGIO]" in sm
    strings = (REPO_ROOT / "src/strings.c").read_text(encoding="utf-8")
    assert 'gText_PedagioVoltarDepois[] = _("Voltar depois");' in strings
    assert 'gText_PedagioPassarAForca[] = _("Passar à força");' in strings
    # voltar depois: um passo para trás, para o lado de onde o jogador veio
    assert "walk_down" in _rotulo(s, "Route23_Movement_JogadorRecuaSul")
    assert "walk_up" in _rotulo(s, "Route23_Movement_JogadorRecuaNorte")


def test_pedagio_dois_lados():
    """O corredor de 3 tiles (x 13-15, y 145-148) ao norte do prédio é passagem obrigatória: gatilhos nas 3 colunas
    nos dois lados do cobrador (y 147 sul, y 145 norte), só com chefe ativo; o cobrador no meio, com a flag
    temporária que o esconde fora do estado ATIVA."""
    rota = _map("Route23")
    w, cells, _attr = _grid("Route23")
    livres = {(i % w, i // w) for i, (_mid, col) in enumerate(cells) if col == 0}
    cob = [o for o in rota["object_events"] if o["local_id"] == "LOCALID_FAMILIA_PEDAGIO_COBRADOR"]
    assert len(cob) == 1 and cob[0]["graphics_id"] == "OBJ_EVENT_GFX_FAMILIA_PERSIAN"
    assert (cob[0]["x"], cob[0]["y"]) == (14, 146) and cob[0]["flag"] == "FLAG_TEMP_1"
    assert rota["object_events"][-1] is cob[0]   # no fim: não renumera os LOCALID_* dos guardas
    assert rota["object_events"].index(cob[0]) + 1 == 8   # o LOCALID_COBRADOR do cenário `familia`
    assert [(x, 146) in livres for x in (13, 14, 15)] == [True] * 3
    gat = {(c["x"], c["y"]): c for c in rota["coord_events"] if "Pedagio" in c["script"]}
    assert set(gat) == {(x, y) for x in (13, 14, 15) for y in (145, 147)}
    for (x, y), c in gat.items():
        assert c["var"] == "VAR_TEMP_3" and c["var_value"] == "1" and (x, y) in livres
        assert c["script"] == ("Route23_EventScript_PedagioSul" if y == 147 else "Route23_EventScript_PedagioNorte")
    # a linha inteira de cada lado é coberta (não há como contornar) e os gatilhos dos guardas seguem onde estavam
    for y in (145, 146, 147):
        assert {x for x in range(w) if (x, y) in livres} == {13, 14, 15}
    guardas = [(c["x"], c["y"]) for c in rota["coord_events"] if "BadgeGuardTrigger" in c["script"]]
    assert not set(guardas) & set(gat) and (13, 149) in guardas and len(guardas) == 42
    s = _rota23_scripts()
    assert "VAR_TEMP_2, 0" in _rotulo(s, "Route23_EventScript_PedagioSul")
    assert "VAR_TEMP_2, 1" in _rotulo(s, "Route23_EventScript_PedagioNorte")
    # o gatilho desarma antes de qualquer outra coisa (gatilho de chão que não muda a var dispara a cada quadro e prende
    # o jogador); já pagou: solta os controles; "voltar depois" arma de novo depois do passo para trás
    assert re.search(r"Route23_EventScript_Pedagio::\n\tlockall\n\tsetvar VAR_TEMP_3, 0\n", s)
    assert "releaseall" in _rotulo(s, "Route23_EventScript_PedagioNada")
    assert s.count("setvar VAR_TEMP_3, 1") == 3   # ArmarPedagio + os dois recuos
    assert "setvar VAR_TEMP_3, 1" in _rotulo(s, "Route23_EventScript_ArmarPedagio")
    assert "Route23_EventScript_ArmarPedagio" in _rotulo(s, "Route23_OnLoad")
    # cobrador e gatilhos só com chefe ativo
    trans = _rotulo(s, "Route23_OnTransition")
    assert trans.index("special FamiliaSombra_Atualizar") < trans.index("special FamiliaSombra_GetEstado") < \
        trans.index("call_if_ne VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_EsconderCobrador") < \
        trans.index("call_if_eq VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_ArmarPedagio")
    assert "setflag FLAG_TEMP_1" in _rotulo(s, "Route23_EventScript_EsconderCobrador")


def test_pedagio_limpa_ao_sair():
    """Sair da Rota 23 (portão da Rota 22 norte, Victory Road 1F/2F ou Platô Índigo) zera o "já pagou"; entrar
    no prédio não (os andares não mexem na flag)."""
    vizinhos = ("Route22_NorthEntrance", "VictoryRoad_1F", "VictoryRoad_2F", "IndigoPlateau_Exterior")
    for mapa in vizinhos:
        s = (MAPS / mapa / "scripts.inc").read_text(encoding="utf-8")
        rotulo = f"{mapa}_OnTransition"
        assert f"map_script MAP_SCRIPT_ON_TRANSITION, {rotulo}\n" in s, mapa
        assert "clearflag FLAG_FAMILIA_PEDAGIO_PAGO" in _rotulo(s, rotulo), mapa
    # a Rota 23 liga exatamente a esses mapas (e ao prédio, que não conta)
    rota = _map("Route23")
    destinos = {w["dest_map"] for w in rota["warp_events"]} | {c["map"] for c in rota["connections"]}
    assert destinos == {"MAP_VICTORY_ROAD_1F", "MAP_VICTORY_ROAD_2F", "MAP_ROUTE22_NORTH_ENTRANCE",
                        "MAP_ROUTE23_UNUSED_HOUSE", "MAP_INDIGO_PLATEAU_EXTERIOR", "MAP_ROUTE22"}
    for pasta in MAPS.iterdir():
        f = pasta / "scripts.inc"
        if f.is_file() and pasta.name not in ("Route23",) + vizinhos:
            assert "FLAG_FAMILIA_PEDAGIO_PAGO" not in f.read_text(encoding="utf-8"), pasta.name


def test_route23_onload_atualiza_estado():
    """CONTINUE roda só o ON_LOAD: ele atualiza o estado ANTES de ler o estado e trancar a porta."""
    corpo = _rotulo(_rota23_scripts(), "Route23_OnLoad")
    assert corpo.index("special FamiliaSombra_Atualizar") < corpo.index("special FamiliaSombra_GetEstado") < \
        corpo.index("Route23_EventScript_TrancarPortaFamilia")


def test_pedagio_so_arma_com_cobrador_presente():
    """O ON_LOAD roda depois do ON_TRANSITION: se o chefe voltou no meio da visita o Persian já foi escondido
    (FLAG_TEMP_1) e armar o pedágio cobraria sem ninguém no corredor."""
    arma = _rotulo(_rota23_scripts(), "Route23_EventScript_ArmarPedagio")
    assert arma.index("goto_if_set FLAG_TEMP_1") < arma.index("setvar VAR_TEMP_3, 1")


def test_sala_do_dom_recusa_dos_gemeos_e_revanche():
    """Time de 1 Pokémon: a dupla é recusada e a música de encontro volta ao normal antes disso. Gêmeos já vencidos:
    Dom e Cobrador não mandam mais "os rapazes" falar com o jogador."""
    s = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    t = (MAPS / NOMES[6] / "text.inc").read_text(encoding="utf-8")
    cena = _rotulo(s, "Route23_FamiliaSombra_6F_EventScript_Cena")
    assert cena.index("special HasEnoughMonsForDoubleBattle") < cena.index(
        "call_if_ne VAR_RESULT, PLAYER_HAS_TWO_USABLE_MONS, Route23_FamiliaSombra_6F_EventScript_RestaurarMusica") < \
        cena.index("trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE")
    assert "fadedefaultbgm" in _rotulo(s, "Route23_FamiliaSombra_6F_EventScript_RestaurarMusica")
    assert "goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_FalaDomSemGemeos" in \
        _rotulo(s, "Route23_FamiliaSombra_6F_EventScript_FalaDom")
    dom = _rotulo(t, "Route23_FamiliaSombra_6F_Text_DomSemGemeos")
    assert dom.startswith("\nRoute") and "GENGAR, O DOM" in dom and "rapazes" not in dom


def test_bilhete_do_5_andar_traz_o_titulo_completo():
    t = (MAPS / NOMES[5] / "text.inc").read_text(encoding="utf-8")
    assert "TYRANITAR, O COBRADOR" in t[t.index("Route23_FamiliaSombra_5F_Text_Bilhete2::"):]


# ---------- ajustes do Cintra (sala do Dom e a rosa com a bolsa cheia) ----------
def test_sala_do_dom_escritorio_ao_lado_da_escada():
    """O escritório fica no lado direito, longe da linha da escada: a poltrona encostada na parede (ninguém passa
    atrás do chefe), os gêmeos dos dois lados dele, o bilhete na frente da mesa e os vasos de rosas à vista de quem
    sai da escada. Posições de predio.json = map.json."""
    sala = PREDIO["andares"]["6"]
    m6 = _map(NOMES[6])
    pos = {o["local_id"]: (o["x"], o["y"]) for o in m6["object_events"]}
    cx, cy = sala["chefe"]
    assert pos["LOCALID_FAMILIA_6F_CHEFE"] == (cx, cy)
    assert [pos["LOCALID_FAMILIA_6F_GEMEO_A"], pos["LOCALID_FAMILIA_6F_GEMEO_B"]] == [tuple(g) for g in sala["gemeos"]]
    assert [(b["x"], b["y"]) for b in m6["bg_events"]] == [tuple(sala["bilhete"])]
    assert sorted((c["x"], c["y"]) for c in m6["coord_events"]) == sorted(tuple(g) for g in sala["gatilhos"])
    w, cells, attr = _grid(NOMES[6])
    livres = {(i % w, i // w) for i, (_mid, col) in enumerate(cells) if col == 0}
    # nada livre atrás (acima) do chefe nem da poltrona; os gêmeos colados nele, um de cada lado
    assert not [(x, y) for x in range(cx - 1, cx + 2) for y in range(cy) if (x, y) in livres]
    assert sorted(sala["gemeos"]) == [[cx - 2, cy], [cx + 2, cy]]
    # a escada é a do canto esquerdo, longe do chefe: ele não fica de costas para quem sobe
    dx, dy = sala["desce"]
    assert _behavior_at(NOMES[6], dx, dy) == "MB_DOWN_LEFT_STAIR_WARP"
    assert cx - dx >= 5 and cy <= dy
    # a frente da mesa é alcançável a partir da saída da escada
    saida = (dx + 1, dy)
    vistos, fila = {saida}, [saida]
    while fila:
        x, y = fila.pop()
        for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if p in livres and p not in vistos and list(p) not in sala["gemeos"]:
                vistos.add(p)
                fila.append(p)
    assert (cx, sala["bilhete"][1] + 1) in vistos
    # vasos: tile com colisão; pelo menos 2 na tela de quem sai da escada (15x10 tiles, jogador na coluna 7, linha 4)
    vaso = {cells[y * w + x][0] for x, y in sala["vasos"]}
    assert len(vaso) == 1 and not set(map(tuple, sala["vasos"])) & livres
    na_tela = [v for v in sala["vasos"] if abs(v[0] - saida[0]) <= 7 and -4 <= v[1] - saida[1] <= 5]
    assert len(na_tela) >= 2, na_tela
    # nenhum metatile da Mansão na sala (escada, moldura e paredes são do desenho vinho): os da Mansão têm o tipo de
    # encontro TERRA nos atributos, os da decoração não
    mansao = sorted({mid for mid, _c in cells if mid >= 640 and attr(mid) >> 24 & 7 == TILE_ENCOUNTER_LAND})
    assert not mansao, [hex(m) for m in mansao]


def test_rosa_com_bolsa_cheia_vai_para_a_sala_de_trofeus():
    """Bolso de itens-chave cheio: sem giveitem; a flag da rosa (ligada por FamiliaSombra_ChefeCaiu) acende a redoma e
    a fala diz que a rosa foi direto para a Sala de Troféus, com o nome certo de cada ocupação."""
    s = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    t = (MAPS / NOMES[6] / "text.inc").read_text(encoding="utf-8")
    inicio = {"Vermelha": "ChefeCaiu", "Dourada": "RosaDourada", "Azul": "RosaAzul", "Negra": "RosaNegra"}
    for cor, rotulo in inicio.items():
        item = f"ITEM_ROSA_{cor.upper()}"
        corpo = _rotulo(s, f"Route23_FamiliaSombra_6F_EventScript_{rotulo}")
        assert corpo.index(f"checkitemspace {item}") < corpo.index(
            f"goto_if_eq VAR_RESULT, FALSE, Route23_FamiliaSombra_6F_EventScript_Rosa{cor}ParaSala") < \
            corpo.index(f"giveitem {item}"), cor
        sala = _rotulo(s, f"Route23_FamiliaSombra_6F_EventScript_Rosa{cor}ParaSala")
        assert "giveitem" not in sala and "additem" not in sala and "removeitem" not in sala
        assert f"msgbox Route23_FamiliaSombra_6F_Text_BolsaCheiaRosa{cor}" in sala and "releaseall" in sala
        fala = _rotulo(t, f"Route23_FamiliaSombra_6F_Text_BolsaCheiaRosa{cor}")
        assert "itens-chave" in fala and f"A ROSA {cor.upper()} foi enviada" in fala and "Sala de Troféus" in fala
    assert "FlagSet(sRosas[ocupacao - 1]);" in FAMILIA_C
    redomas = (MAPS / "SevenIsland_UnusedHouse" / "scripts.inc").read_text(encoding="utf-8")
    assert all(f"FLAG_FAMILIA_ROSA_{n}" in redomas for n in range(1, 5))


# ---------- o quadro da sala do Dom: o retrato do chefe em preto e branco ----------
FAMILIA_TS = REPO_ROOT / "data" / "tilesets" / "secondary" / "familia_sombra"
QUADRO = PREDIO["quadro"]


def _quadro_rgb(nome: str) -> list[list[tuple[int, int, int]]]:
    """O quadro `nome` (3x2 metatiles, 48x32) desenhado a partir do tileset (tiles.png + metatiles.bin + paletas), só a
    camada de baixo (a de cima da decoração é vazia)."""
    from PIL import Image

    im = Image.open(FAMILIA_TS / "tiles.png")
    px = im.load()
    por_linha = im.width // 8
    metas = (FAMILIA_TS / "metatiles.bin").read_bytes()
    paletas = {}
    out = [[(0, 0, 0)] * 48 for _ in range(32)]
    for dy in range(2):
        for dx in range(3):
            mid = QUADRO["metatiles"][nome][dy][dx] - 640
            ents = struct.unpack_from("<8H", metas, mid * 16)
            for k in range(4):
                e = ents[k]
                t, hf, vf, pal = (e & 0x3FF) - 640, e >> 10 & 1, e >> 11 & 1, e >> 12
                assert t >= 0 and not ents[4 + k] & 0x3FF, (nome, hex(e))   # ladrilho próprio, sem camada de cima
                if pal not in paletas:
                    v = list(map(int, (FAMILIA_TS / "palettes" / f"{pal:02d}.pal").read_text().split()[3:51]))
                    paletas[pal] = [tuple(v[i * 3:i * 3 + 3]) for i in range(16)]
                for y in range(8):
                    for x in range(8):
                        sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                        c = px[(t % por_linha) * 8 + sx, (t // por_linha) * 8 + sy] & 15
                        out[dy * 16 + (k // 2) * 8 + y][dx * 16 + (k % 2) * 8 + x] = paletas[pal][c]
    return out


QUADROS_CHEFES = (("Dom", 1), ("Cobrador", 2), ("Mercenario", 3), ("Pesadelo", 4))


def test_quadro_metatiles_por_chefe():
    """Os 4 quadros (Dom, Cobrador, Mercenário e Pesadelo) com rótulos fixos; o layout traz o Dom e o ON_LOAD do 6º
    andar troca pelo chefe da ocupação (VAR_FAMILIA_OCUPACAO; sem chefe, fica o do último). Sem tela vazia: os 4
    chefes têm retrato."""
    labels = (REPO_ROOT / "include/constants/metatile_labels.h").read_text(encoding="utf-8")
    s = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    assert "map_script MAP_SCRIPT_ON_LOAD, Route23_FamiliaSombra_6F_OnLoad" in s
    carga = _rotulo(s, "Route23_FamiliaSombra_6F_OnLoad")
    assert "special FamiliaSombra_GetOcupacao" in carga
    assert "QuadroVazio" not in s and "QuadroVazio" not in labels and "vazio" not in QUADRO["metatiles"]
    for nome, ocupacao in QUADROS_CHEFES:
        regra = f"call_if_eq VAR_0x8008, {ocupacao},"
        assert f"{regra} Route23_FamiliaSombra_6F_EventScript_Quadro{nome}" in carga, nome
        corpo = _rotulo(s, f"Route23_FamiliaSombra_6F_EventScript_Quadro{nome}")
        for dy in range(2):
            for dx in range(3):
                rotulo = f"METATILE_FamiliaSombra_Quadro{nome}_{dx}_{dy}"
                mid = QUADRO["metatiles"][nome.lower()][dy][dx]
                assert re.search(rf"#define {rotulo}\s+{mid:#x}\b", labels, re.I), rotulo
                assert f"setmetatile {QUADRO['x'] + dx}, {QUADRO['y'] + dy}, {rotulo}, TRUE" in corpo, rotulo
    w, cells, _attr = _grid(NOMES[6])
    padrao = [[cells[(QUADRO["y"] + dy) * w + QUADRO["x"] + dx][0] for dx in range(3)] for dy in range(2)]
    assert padrao == QUADRO["metatiles"]["dom"]
    assert set(QUADRO["metatiles"]) == {n.lower() for n, _o in QUADROS_CHEFES}
    assert len({m for q in QUADRO["metatiles"].values() for linha in q for m in linha}) == 24


# Os retratos que já estavam no jogo (parte 1): os ids dos metatiles e o desenho (SHA-256 dos 48x32 pixels) não mudam
# quando se acrescentam retratos novos. Valores tirados do commit c027fa369, antes da Task 8.
RETRATOS_ANTIGOS = {
    "dom": ([[750, 752, 754], [751, 753, 755]], "1e4220f6dfb010ac14c1087f9bf191e46b1e062f8f8a37e77ec19e2b8b0d2d56"),
    "cobrador": ([[744, 746, 748], [745, 747, 749]], "3e55530f1bc60a4c762b6c38a7dea6b00c26b62878018c7ad3a887b3116c3eb9"),
}


def test_retratos_antigos_iguais():
    import hashlib

    for nome, (ids, sha) in RETRATOS_ANTIGOS.items():
        assert QUADRO["metatiles"][nome] == ids, nome
        assert hashlib.sha256(repr(_quadro_rgb(nome)).encode()).hexdigest() == sha, nome
    # os limiares por espécie só existem para os dois novos: Gengar e Tyranitar seguem no padrão
    predio = _predio_py()
    assert set(predio.LIMIARES_RETRATO) == {"garchomp_shiny", "darkrai_shiny"}
    assert predio.LIMIAR_PADRAO == (64, 120)
    for a, b in predio.LIMIARES_RETRATO.values():
        assert 0 < a < b < 255


def _predio_py():
    import importlib.util

    spec = importlib.util.spec_from_file_location("predio_familia", REPO_ROOT / "tools/familia_sombra/predio.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_retrato_tres_tons():
    """Garchomp e Darkrai em 3 cinzas viravam só contorno com os limiares do Gengar: cada um dos 3 tons cobre pelo
    menos 10% da tela do retrato nos 4 quadros (preto, cinza médio e cinza claro)."""
    x0, y0, x1, y1 = QUADRO["tela"]
    total = (x1 - x0 + 1) * (y1 - y0 + 1)
    for nome, _o in QUADROS_CHEFES:
        q = _quadro_rgb(nome.lower())
        contagem: dict[tuple[int, int, int], int] = {}
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                contagem[q[y][x]] = contagem.get(q[y][x], 0) + 1
        assert len(contagem) == 3, (nome, contagem)
        for cor, n in contagem.items():
            assert n >= total / 10, (nome, cor, f"{n / total:.0%}")


def test_quadro_retrato_cinza_dentro_da_moldura():
    """Dentro da tela só tons de cinza (foto antiga); fora dela os 4 quadros são idênticos (a moldura e a parede):
    nada do retrato passa da moldura. A moldura dourada fecha a tela nos 4 lados."""
    x0, y0, x1, y1 = QUADRO["tela"]
    ref = _quadro_rgb("dom")
    dentro = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
    for nome, _o in QUADROS_CHEFES:
        q = _quadro_rgb(nome.lower())
        for y in range(32):
            for x in range(48):
                if not dentro(x, y):
                    assert q[y][x] == ref[y][x], (nome, x, y)
        tons = {q[y][x] for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}
        assert all(max(c) - min(c) <= 8 for c in tons), (nome, tons)
        assert len(tons) == 3, (nome, tons)
    for x in range(x0 - 3, x1 + 4):
        assert ref[y0 - 3][x][0] > ref[y0 - 3][x][2] and ref[y1 + 3][x][0] > ref[y1 + 3][x][2]
    for y in range(y0 - 3, y1 + 4):
        assert ref[y][x0 - 3][0] > ref[y][x0 - 3][2] and ref[y][x1 + 3][0] > ref[y][x1 + 3][2]


# ---------- parte 2: as ocupações 3 e 4 no prédio (falas, bilhetes, rosas, curador) ----------
def _texto_plano(texto: str, rotulo: str) -> str:
    """O texto de um rótulo sem os códigos de quebra: as linhas viram uma só, separadas por 1 espaço."""
    corpo = _rotulo("\n" + texto, rotulo)
    pedacos = re.findall(r'\.string "(.*)"', corpo)
    return re.sub(r"\s+", " ", re.sub(r"\\[nlp]", " ", "".join(pedacos)).replace("$", " ")).strip()


def _rotulos_de_texto(texto: str) -> list[str]:
    return re.findall(r"^(\w+)::", texto, re.M)


def test_bilhetes_3_4_em_todos_os_andares():
    """Cada andar (1º ao 6º) tem os bilhetes das ocupações 3 e 4, ligados à ocupação (VAR_FAMILIA_OCUPACAO), com o
    título completo do chefe quando o citam. Os da Rota 23 dependem só da ocupação, como os da parte 1."""
    for n in range(1, 7):
        nome = NOMES[n]
        s = (MAPS / nome / "scripts.inc").read_text(encoding="utf-8")
        t = (MAPS / nome / "text.inc").read_text(encoding="utf-8")
        for k in (3, 4):
            assert f"goto_if_eq VAR_RESULT, {k}, {nome}_EventScript_Bilhete{k}" in s, (nome, k)
            corpo = _rotulo(s, f"{nome}_EventScript_Bilhete{k}")
            assert f"msgbox {nome}_Text_Bilhete{k}" in corpo and "releaseall" in corpo, (nome, k)
            plano = _texto_plano(t, f"{nome}_Text_Bilhete{k}")
            assert plano, (nome, k)
        assert "GARCHOMP, O MERCENÁRIO" in _texto_plano(t, f"{nome}_Text_Bilhete3"), nome
        assert "DARKRAI, O PESADELO" in _texto_plano(t, f"{nome}_Text_Bilhete4"), nome
    # no 6º andar o livro-caixa vale só com chefe ativo; sem chefe: depois da 2 "alguém de fora", depois da 3 a sombra
    s6 = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    t6 = (MAPS / NOMES[6] / "text.inc").read_text(encoding="utf-8")
    sem = _rotulo(s6, "Route23_FamiliaSombra_6F_EventScript_BilheteSemChefe")
    assert "goto_if_eq VAR_RESULT, 2, Route23_FamiliaSombra_6F_EventScript_BilheteDeFora" in sem
    assert "goto_if_ge VAR_RESULT, 3, Route23_FamiliaSombra_6F_EventScript_BilheteSombra" in sem
    assert "buscar alguém de fora" in _texto_plano(t6, "Route23_FamiliaSombra_6F_Text_BilheteDeFora")
    sombra = _texto_plano(t6, "Route23_FamiliaSombra_6F_Text_BilheteSombra")
    assert "sombra por trás do Dom" in sombra and "sonhos" in sombra


def test_titulos_nas_falas():
    """Todo rótulo de texto do prédio, da sala de troféus e do 1º andar que cita GARCHOMP ou DARKRAI traz o título ao
    lado ("GARCHOMP, O MERCENÁRIO", "DARKRAI, O PESADELO"), mesmo quebrado em duas linhas; e os ramos das ocupações
    3 e 4 da sala do chefe existem, cada um com o título do próprio chefe."""
    mapas = [NOMES[n] for n in range(1, 7)] + ["SevenIsland_UnusedHouse"]
    achados = 0
    for nome in mapas:
        t = (MAPS / nome / "text.inc").read_text(encoding="utf-8")
        for rotulo in _rotulos_de_texto(t):
            plano = _texto_plano(t, rotulo)
            for especie, titulo in (("GARCHOMP", "O MERCENÁRIO"), ("DARKRAI", "O PESADELO")):
                assert plano.count(especie) == plano.count(f"{especie}, {titulo}"), (nome, rotulo, plano)
                achados += plano.count(especie)
    assert achados >= 20, achados
    t6 = (MAPS / NOMES[6] / "text.inc").read_text(encoding="utf-8")
    for sufixo, especie, titulo in (("Mercenario", "GARCHOMP", "O MERCENÁRIO"), ("Pesadelo", "DARKRAI", "O PESADELO")):
        for base in ("", "SemGemeos"):
            assert f"{especie}, {titulo}:" in _texto_plano(t6, f"Route23_FamiliaSombra_6F_Text_{sufixo}{base}")
        for base in ("Desafio", "Fuga"):
            assert f"{especie}, {titulo}:" in _texto_plano(t6, f"Route23_FamiliaSombra_6F_Text_{base}{sufixo}")
        assert f"{especie}, {titulo}," in _texto_plano(t6, f"Route23_FamiliaSombra_6F_Text_Rosa{sufixo}")
    assert "RosaChefe" not in t6 and "RosaChefe" not in (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    # os gêmeos da parte 2: Gligar com o Mercenário e Dusclops com o Pesadelo
    assert "Gligar" in _texto_plano(t6, "Route23_FamiliaSombra_6F_Text_GemeosGligar")
    assert "Dusclops" in _texto_plano(t6, "Route23_FamiliaSombra_6F_Text_GemeosDusclops")


def test_sala_do_chefe_ramos_3_e_4():
    """Falas, gêmeos, desafio, fuga e rosa por ocupação: nada cai mais nas falas do Dom (antes `call_if_ne ..., 2`)."""
    s = (MAPS / NOMES[6] / "scripts.inc").read_text(encoding="utf-8")
    assert "call_if_ne VAR_0x8008, 2," not in s
    for etapa in ("Fala", "Desafio", "Fuga"):
        for nome, ocupacao in QUADROS_CHEFES:
            assert f"call_if_eq VAR_0x8008, {ocupacao}, Route23_FamiliaSombra_6F_EventScript_{etapa}{nome}" in s, (etapa, nome)
    cena = _rotulo(s, "Route23_FamiliaSombra_6F_EventScript_Cena")
    assert "goto_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_GemeosGligar" in cena
    assert "goto_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_GemeosDusclops" in cena
    for sufixo, texto in (("Gligar", "GemeosGligar"), ("Dusclops", "GemeosDusclops")):
        corpo = _rotulo(s, f"Route23_FamiliaSombra_6F_EventScript_Gemeos{sufixo}")
        assert corpo.count("trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE, TRAINER_FAMILIA_GEMEOS, "
                           "LOCALID_FAMILIA_6F_GEMEO_A,") == 1 and f"Text_{texto}," in corpo
    for nome in ("Mercenario", "Pesadelo"):
        sem = _rotulo(s, f"Route23_FamiliaSombra_6F_EventScript_Fala{nome}")
        assert f"goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_Fala{nome}SemGemeos" in sem
    assert "msgbox Route23_FamiliaSombra_6F_Text_RosaMercenario" in _rotulo(s, "Route23_FamiliaSombra_6F_EventScript_RosaAzul")
    assert "msgbox Route23_FamiliaSombra_6F_Text_RosaPesadelo" in _rotulo(s, "Route23_FamiliaSombra_6F_EventScript_RosaNegra")


def test_curador_parte2():
    """O curador da Sala de Troféus comenta a rosa que falta, na ordem das ocupações: Dom, Cobrador, Mercenário,
    Pesadelo; com as 4 só elogia a sala (e segue para as taças)."""
    s = (MAPS / "SevenIsland_UnusedHouse" / "scripts.inc").read_text(encoding="utf-8")
    t = (MAPS / "SevenIsland_UnusedHouse" / "text.inc").read_text(encoding="utf-8")
    curador = _rotulo(s, "SevenIsland_UnusedHouse_EventScript_Curador")
    ordem = [f"goto_if_unset FLAG_FAMILIA_ROSA_{n}, SevenIsland_UnusedHouse_EventScript_CuradorFalta{nome}"
             for n, nome in ((1, "Dom"), (2, "Cobrador"), (3, "Mercenario"), (4, "Pesadelo"))]
    pos = [curador.index(o) for o in ordem]
    assert pos == sorted(pos) and curador.index("msgbox SevenIsland_UnusedHouse_Text_CuradorRosas") > pos[-1]
    for nome in ("Mercenario", "Pesadelo"):
        corpo = _rotulo(s, f"SevenIsland_UnusedHouse_EventScript_CuradorFalta{nome}")
        assert f"msgbox SevenIsland_UnusedHouse_Text_CuradorFalta{nome}" in corpo
        assert "goto SevenIsland_UnusedHouse_EventScript_CuradorTacas" in corpo
    assert "GARCHOMP, O MERCENÁRIO" in _texto_plano(t, "SevenIsland_UnusedHouse_Text_CuradorFaltaMercenario")
    assert "DARKRAI, O PESADELO" in _texto_plano(t, "SevenIsland_UnusedHouse_Text_CuradorFaltaPesadelo")
    assert "quatro rosas" in _texto_plano(t, "SevenIsland_UnusedHouse_Text_CuradorRosas")
    assert "As outras redomas seguem vazias" not in t


def test_chefe_alcancavel_pelo_balcao():
    """O chefe fica na poltrona com colisão nos 4 lados: a coluna do meio da mesa (2 de fundo) é MB_COUNTER e o motor
    olha 2 tiles além quando os 2 são balcão; assim, depois de fugir, o A na frente da mesa recomeça a luta. O
    livro-caixa fica em outra coluna (senão o objeto ganharia da placa e o bilhete sumiria com o chefe presente)."""
    cx, cy = PREDIO["andares"]["6"]["chefe"]
    w, cells, _attr = _grid(NOMES[6])
    livres = {(i % w, i // w) for i, (_mid, col) in enumerate(cells) if col == 0}
    assert [_behavior_at(NOMES[6], cx, cy + d) for d in (1, 2)] == ["MB_COUNTER", "MB_COUNTER"]
    assert (cx, cy + 3) in livres and (cx, cy + 1) not in livres and (cx, cy + 2) not in livres
    assert all((x, y) not in livres for x, y in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1)))
    bilhete = PREDIO["andares"]["6"]["bilhete"]
    assert bilhete[0] != cx and _behavior_at(NOMES[6], *bilhete) == "MB_NORMAL"
    corpo = (REPO_ROOT / "src/field_control_avatar.c").read_text(encoding="utf-8")
    corpo = corpo[corpo.index("static const u8 *GetInteractedObjectEventScript(struct MapPosition *position"):]
    corpo = corpo[:corpo.index("\n}\n")]
    assert "2 * gDirectionToVectors[direction].x" in corpo and corpo.count("MetatileBehavior_IsCounter") == 2
