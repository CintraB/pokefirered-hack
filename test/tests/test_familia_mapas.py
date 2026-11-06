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
                   "LOCALID_FAMILIA_6F_GEMEO_A,") == 2
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
