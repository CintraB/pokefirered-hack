"""POK-54 (Task 10): o fechamento da Família Sombra: a polícia na porta da Rota 23, a Oficial Jenny e a entrega dos
chefes apreendidos (src/familia_sombra.c, data/maps/Route23, tools/familia_sombra/gerar.py e predio.py).

Leitura estática de C, scripts, JSON e gráficos. O jogo de verdade (a cena, as entregas com o time cheio, a porta que não
abre) fica no cenário `familia` (casos `familia/cena_jenny`, `jenny_de_novo`, `entrega_*`, `porta_lacrada` e
`policia_ambiente`).
"""

import json
import os
import re
import struct
import subprocess
import sys

from PIL import Image

from esteira.scenarios import REPO_ROOT

MAPS = REPO_ROOT / "data" / "maps"
ROTA23 = MAPS / "Route23"
FAMILIA_C = (REPO_ROOT / "src" / "familia_sombra.c").read_text(encoding="utf-8")
EVENT_OBJECTS_H = (REPO_ROOT / "include/constants/event_objects.h").read_text(encoding="utf-8")
FLAGS_H = (REPO_ROOT / "include/constants/flags.h").read_text(encoding="utf-8")
SLOTS_JSON = json.loads((REPO_ROOT / "tools/familia_sombra/slots.json").read_text(encoding="utf-8"))
PREDIO = json.loads((REPO_ROOT / "tools/familia_sombra/predio.json").read_text(encoding="utf-8"))
INDIGO = REPO_ROOT / "data/tilesets/secondary/indigo_plateau"
SCRIPTS = (ROTA23 / "scripts.inc").read_text(encoding="utf-8")
TEXTOS = (ROTA23 / "text.inc").read_text(encoding="utf-8")
GFX_C = (REPO_ROOT / "src/data/object_events/familia_gfx.h").read_text(encoding="utf-8")
SEIS_ANDARES = MAPS / "Route23_FamiliaSombra_6F"
# os 8 primeiros objetos da Rota 23 (7 guardas de insígnia e o cobrador): o índice no array vira o LOCALID, então a
# polícia da porta só pode entrar depois deles
ANTIGOS = ["LOCALID_CASCADE_BADGE_GUARD", "LOCALID_THUNDER_BADGE_GUARD", "LOCALID_RAINBOW_BADGE_GUARD",
           "LOCALID_SOUL_BADGE_GUARD", "LOCALID_MARSH_BADGE_GUARD", "LOCALID_VOLCANO_BADGE_GUARD",
           "LOCALID_EARTH_BADGE_GUARD", "LOCALID_FAMILIA_PEDAGIO_COBRADOR"]
POLICIA = ["OBJ_EVENT_GFX_OFICIAL_JENNY", "OBJ_EVENT_GFX_POLICEMAN", "OBJ_EVENT_GFX_POLICEMAN",
           "OBJ_EVENT_GFX_POLICIA_GROWLITHE", "OBJ_EVENT_GFX_POLICIA_ARCANINE"]


def _defines(texto: str) -> dict[str, int]:
    return {n: int(v, 0) for n, v in re.findall(r"^#define (\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", texto, re.M)}


def _corpo(fonte: str, nome: str) -> str:
    return re.search(rf"\n(?:static )?\w[\w ]*\b{nome}\([^)]*\)\n\{{\n(.*?)\n\}}\n", fonte, re.S).group(1)


def _script(rotulo: str, fonte: str = SCRIPTS) -> str:
    """Do rótulo até o próximo rótulo `::` (inclusive os rótulos locais com `:`)."""
    m = re.search(rf"^{rotulo}::\n(.*?)(?=^\w+::|\Z)", fonte, re.S | re.M)
    assert m, rotulo
    return m.group(1)


def _objetos() -> list[dict]:
    return json.loads((ROTA23 / "map.json").read_text(encoding="utf-8"))["object_events"]


def _jasc(caminho) -> list[tuple[int, int, int]]:
    ls = caminho.read_bytes().decode("ascii").split("\r\n")
    assert ls[:3] == ["JASC-PAL", "0100", "16"], caminho
    cores = [tuple(int(c) for c in l.split()) for l in ls[3:19]]
    assert len(cores) == 16 and ls[19:] == [""], caminho
    return cores


# --- os gráficos novos -------------------------------------------------------------------------------------------


def test_gfx_policia_no_fim():
    """Os 3 gráficos ficam no fim (190 a 192), os ids antigos (até 189) não se mexem: o id vai para o save."""
    d = _defines(EVENT_OBJECTS_H)
    assert (d["OBJ_EVENT_GFX_POLICIA_GROWLITHE"], d["OBJ_EVENT_GFX_POLICIA_ARCANINE"],
            d["OBJ_EVENT_GFX_OFICIAL_JENNY"]) == (190, 191, 192)
    assert d["OBJ_EVENT_GFX_FAMILIA_DARKRAI_SHINY"] == 189
    assert d["NUM_OBJ_EVENT_GFX"] == 193
    # nenhum id estático novo antes do 190 (os de 240 em diante são os dinâmicos, OBJ_EVENT_GFX_VAR_*)
    assert max(v for k, v in d.items() if k.startswith("OBJ_EVENT_GFX_") and v < 240) == 192
    ponteiros = (REPO_ROOT / "src/data/object_events/familia_gfx_ponteiros.h").read_text(encoding="utf-8").splitlines()
    assert [l.split("]")[0].split("[")[1] for l in ponteiros[-3:]] == [
        "OBJ_EVENT_GFX_POLICIA_GROWLITHE", "OBJ_EVENT_GFX_POLICIA_ARCANINE", "OBJ_EVENT_GFX_OFICIAL_JENNY"]


def test_tamanhos_dos_graficos():
    pics = REPO_ROOT / "graphics/object_events/pics/familia"
    assert Image.open(pics / "policia_growlithe.png").size == (32, 32)
    assert Image.open(pics / "policia_arcanine.png").size == (32, 32)
    jenny = Image.open(pics / "oficial_jenny.png")
    assert jenny.size == (160, 32) and jenny.mode == "P"      # 10 quadros 16x32, como a Picnicker
    regras = (REPO_ROOT / "spritesheet_rules.mk").read_text(encoding="utf-8")
    assert re.search(r"familia/policia_%\.4bpp: .*\n\t\$\(GFX\) \$< \$@ -mwidth 4 -mheight 4", regras)
    assert re.search(r"familia/oficial_jenny\.4bpp: %\.4bpp: %\.png\n\t\$\(GFX\) \$< \$@ -mwidth 2 -mheight 4", regras)
    # a Jenny tem os 10 quadros de verdade (a Picnicker também); a polícia-Pokémon, 1 quadro repetido
    assert len(re.findall(r"overworld_frame\(sFamiliaPic_OficialJenny, 2, 4, (\d)\)", GFX_C)) == 10
    assert sorted(set(re.findall(r"overworld_frame\(sFamiliaPic_OficialJenny, 2, 4, (\d)\)", GFX_C))) == list("0123456789")
    assert set(re.findall(r"overworld_frame\(sFamiliaPic_PoliciaGrowlithe, 4, 4, (\d)\)", GFX_C)) == {"0"}


def test_jenny_paleta_propria():
    """O cabelo azul-petróleo não existe na paleta azul de NPC: a Jenny tem a paleta dela, com a tag dela."""
    jenny = _jasc(REPO_ROOT / "graphics/object_events/palettes/familia/oficial_jenny.pal")
    azul = _jasc(REPO_ROOT / "graphics/object_events/palettes/npc_blue.pal")
    assert jenny != azul
    teal = {(136, 224, 208), (64, 176, 176), (24, 104, 112)}
    assert teal <= set(jenny) and not teal & set(azul)
    info = re.search(r"gObjectEventGraphicsInfo_Familia_OficialJenny = \{(.*?)\n\};", GFX_C, re.S).group(1)
    assert "OBJ_EVENT_PAL_TAG_FAMILIA_OFICIAL_JENNY" in info and "OBJ_EVENT_PAL_TAG_NPC" not in info
    assert "gObjectEventPal_Familia_oficial_jenny" in GFX_C
    # a Jenny é a Picnicker: 10 quadros 16x32 (o desenho muda, as formas não); o quepe tem o distintivo dourado (5 e 6)
    im = Image.open(REPO_ROOT / "graphics/object_events/pics/familia/oficial_jenny.png")
    pic = Image.open(REPO_ROOT / "graphics/object_events/pics/people/picnicker.png")
    assert im.size == pic.size
    transparentes = lambda i: [v == 0 for v in i.tobytes()]
    assert transparentes(im) == transparentes(pic), "a silhueta mudou"
    usados = set(im.tobytes())
    assert {5, 6} <= usados and {12, 13} <= usados


def test_policia_pokemon_so_quadro_zero():
    """Growlithe e Arcanine são o quadro 0 do seguidor (parado, de frente), na paleta normal dele, sem chapéu."""
    seg = REPO_ROOT / "graphics/object_events"
    for nome in ("growlithe", "arcanine"):
        im = Image.open(seg / f"pics/familia/policia_{nome}.png")
        folha = Image.open(seg / f"pics/seguidores/{nome}.png")
        assert im.tobytes() == folha.crop((0, 0, 32, 32)).tobytes()
        pal = _jasc(seg / f"palettes/familia/policia_{nome}.pal")
        original = _jasc(seg / f"palettes/seguidores/{nome}.pal")
        assert [tuple(c & 0xF8 for c in p) for p in original[1:]] == pal[1:]


def test_slots_porta_policia():
    """Jenny, Growlithe e Arcanine ficam em 3 slots diferentes e nenhum é o 1 (a paleta azul do policial existente)."""
    ids = ["OBJ_EVENT_GFX_OFICIAL_JENNY", "OBJ_EVENT_GFX_POLICIA_GROWLITHE", "OBJ_EVENT_GFX_POLICIA_ARCANINE"]
    assert sorted(SLOTS_JSON["grupos"]["porta_policia"]) == sorted(ids)
    slots = [SLOTS_JSON["slots"][i] for i in ids]
    assert len(set(slots)) == 3 and "PALSLOT_NPC_1" not in slots, slots
    policial = re.search(r"gObjectEventGraphicsInfo_Policeman = \{(.*?)\n\};",
                         (REPO_ROOT / "src/data/object_events/object_event_graphics_info.h").read_text("utf-8"), re.S)
    assert ".paletteSlot = PALSLOT_NPC_1" in policial.group(1) and "OBJ_EVENT_PAL_TAG_NPC_BLUE" in policial.group(1)
    for gid, slot in zip(ids, slots):
        nome = {"OBJ_EVENT_GFX_OFICIAL_JENNY": "OficialJenny", "OBJ_EVENT_GFX_POLICIA_GROWLITHE": "PoliciaGrowlithe",
                "OBJ_EVENT_GFX_POLICIA_ARCANINE": "PoliciaArcanine"}[gid]
        info = re.search(rf"gObjectEventGraphicsInfo_Familia_{nome} = \{{(.*?)\n\}};", GFX_C, re.S).group(1)
        assert f".paletteSlot = {slot}" in info, nome


def test_slots_antigos_nao_mudaram():
    """Os slots dos gráficos da parte 1 e dos chefes da parte 2 (saída já versionada) ficam como estavam."""
    assert SLOTS_JSON["slots"]["OBJ_EVENT_GFX_FAMILIA_HAUNTER"] == "PALSLOT_NPC_4"
    assert SLOTS_JSON["slots"]["OBJ_EVENT_GFX_FAMILIA_PERSIAN"] == "PALSLOT_NPC_2"
    assert SLOTS_JSON["slots"]["OBJ_EVENT_GFX_FAMILIA_DARKRAI_SHINY"] == "PALSLOT_NPC_2"


def test_geradores_conferem():
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    for nome in ("gerar", "predio"):
        r = subprocess.run([sys.executable, "-I", str(REPO_ROOT / f"tools/familia_sombra/{nome}.py"), "--conferir"],
                           capture_output=True, text=True, env=env, cwd=REPO_ROOT)
        assert r.returncode == 0, nome + "\n" + r.stdout + r.stderr


# --- a porta lacrada -----------------------------------------------------------------------------------------------


def test_porta_lacrada_sem_warp():
    """O metatile da porta lacrada é o 841 (depois da porta trancada), sem comportamento de porta, com a paleta 8 (a
    das faixas amarelas) e ladrilhos novos: a porta aberta (General_Door, 0x69) é a única que o jogo anda para dentro."""
    indigo = PREDIO["indigo_plateau"]
    assert indigo["porta_lacrada"] == indigo["porta_trancada"] + 1
    labels = (REPO_ROOT / "include/constants/metatile_labels.h").read_text(encoding="utf-8")
    assert re.search(rf"#define METATILE_IndigoPlateau_FamiliaPortaLacrada\s+{indigo['porta_lacrada']:#x}\b", labels)
    indice = indigo["porta_lacrada"] - 640
    attrs = (INDIGO / "metatile_attributes.bin").read_bytes()
    atributo = struct.unpack("<I", attrs[indice * 4:indice * 4 + 4])[0]
    assert atributo & 0x1FF == 0, f"comportamento {atributo & 0x1FF:#x}: devia ser MB_NORMAL"
    metatiles = struct.unpack(f"<{len(attrs) // 4 * 8}H", (INDIGO / "metatiles.bin").read_bytes())
    entradas = metatiles[indice * 8:indice * 8 + 8]
    assert all(e >> 12 == 8 for e in entradas[:4]), "a camada de baixo usa a paleta 8"
    assert all(e & 0x3FF >= 640 + 247 for e in entradas[:4]), "ladrilhos novos, não os do Platô Índigo original"
    assert len(attrs) // 4 == 176 + 24 + 2
    # a paleta 8 tem o amarelo e o preto da fita
    pal = _jasc(INDIGO / "palettes/08.pal")
    assert (248, 216, 32) in pal and (24, 24, 24) in pal
    # a imagem do metatile tem as faixas: pixels amarelos em quantidade, nos 4 ladrilhos
    tiles = Image.open(INDIGO / "tiles.png")
    amarelo = pal.index((248, 216, 32))
    for e in entradas[:4]:
        n = e & 0x3FF
        x0, y0 = ((n - 640) % 16) * 8, ((n - 640) // 16) * 8
        recorte = tiles.crop((x0, y0, x0 + 8, y0 + 8)).tobytes()
        assert recorte.count(amarelo) >= 5, f"ladrilho {n} sem fita"
    regras = (REPO_ROOT / "tileset_rules.mk").read_text(encoding="utf-8")
    assert f"-num_tiles {indigo['ladrilhos']} " in regras and indigo["ladrilhos"] <= 384


def test_porta_lacrada_no_script():
    assert "setmetatile 4, 149, METATILE_IndigoPlateau_FamiliaPortaLacrada, TRUE" in SCRIPTS      # TRUE = colisão
    onload = _script("Route23_OnLoad")
    assert re.search(r"call_if_eq VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_LacrarPortaFamilia", onload)
    placa = _script("Route23_EventScript_PortaFamilia")
    assert placa.index("FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_PortaFamiliaLacrada") < placa.index(
        "FAMILIA_ESTADO_FECHADO")
    assert '"A porta está lacrada pela polícia.$"' in TEXTOS
    # o warp do mapa continua o mesmo (4, 149): quem fecha é o metatile impassível
    warps = json.loads((ROTA23 / "map.json").read_text(encoding="utf-8"))["warp_events"]
    assert any((w["x"], w["y"]) == (4, 149) and w["dest_map"] == "MAP_ROUTE23_UNUSED_HOUSE" for w in warps)


# --- os objetos e a cena --------------------------------------------------------------------------------------------


def test_objetos_no_fim_da_rota23():
    """Os 5 objetos novos entram depois dos 8 antigos (o índice no array vira o LOCALID), todos com FLAG_TEMP_2."""
    objetos = _objetos()
    assert [o["local_id"] for o in objetos[:8]] == ANTIGOS
    novos = objetos[8:]
    assert [o["graphics_id"] for o in novos] == POLICIA
    assert all(o["flag"] == "FLAG_TEMP_2" for o in novos)
    assert all(o["trainer_type"] == "TRAINER_TYPE_NONE" for o in novos)
    assert len({(o["x"], o["y"]) for o in novos}) == 5
    jenny = novos[0]
    assert jenny["script"] == "Route23_EventScript_PoliciaJenny" and jenny["local_id"] == "LOCALID_FAMILIA_POLICIA_JENNY"
    # perto da porta (4, 149): a calçada (x 2-6, y 150-151) e a trilha ao lado; o caminho da porta até a trilha, pelo
    # tile à frente dela e a linha 151 ((4, 150), (4, 151), (5, 151), (6, 151)), fica livre: senão o jogador ficaria preso
    for o in novos:
        assert 2 <= o["x"] <= 7 and 150 <= o["y"] <= 151, o
    ocupados = {(o["x"], o["y"]) for o in novos}
    assert not ocupados & {(4, 150), (4, 151), (5, 151), (6, 151)}, "a polícia fecharia o jogador na porta"
    # os LOCALID_* são o índice no array + 1 (o Python do cenário usa os números)
    assert [(o["local_id"], i + 1) for i, o in enumerate(objetos)][8:] == [
        ("LOCALID_FAMILIA_POLICIA_JENNY", 9), ("LOCALID_FAMILIA_POLICIA_POLICIAL_1", 10),
        ("LOCALID_FAMILIA_POLICIA_POLICIAL_2", 11), ("LOCALID_FAMILIA_POLICIA_GROWLITHE", 12),
        ("LOCALID_FAMILIA_POLICIA_ARCANINE", 13)]
    # cada objeto tem script (e todos eles existem)
    for o in novos:
        assert re.search(rf"^{o['script']}::", SCRIPTS, re.M), o["script"]


def test_policia_escondida_fora_do_fim():
    transicao = _script("Route23_OnTransition")
    assert "call_if_ne VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_EsconderPolicia" in transicao
    assert "call_if_eq VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_ChecarCenaPolicia" in transicao
    assert "setflag FLAG_TEMP_2" in _script("Route23_EventScript_EsconderPolicia")
    checar = _script("Route23_EventScript_ChecarCenaPolicia")
    assert checar.index("FLAG_FAMILIA_POLICIA_CENA") < checar.index("setvar VAR_TEMP_4, 1")
    assert "getplayerxy" in checar and "149" in checar and "150" in checar


def test_cena_com_questlog():
    assert "map_script MAP_SCRIPT_ON_FRAME_TABLE, Route23_OnFrame" in SCRIPTS
    assert re.search(r"Route23_OnFrame::\n\tmap_script_2 VAR_TEMP_4, 1, Route23_EventScript_CenaPolicia\n\t\.2byte 0", SCRIPTS)
    cena = _script("Route23_EventScript_CenaPolicia")
    assert cena.index("goto_if_questlog EventScript_ReleaseEnd") < cena.index("lockall")
    assert "setvar VAR_TEMP_4, 0" in cena                                  # o gatilho não repete (nem no Quest Log)
    assert cena.index("setvar VAR_TEMP_4, 0") < cena.index("goto_if_questlog")
    for chamada in ("Route23_EventScript_JennyVemDaPorta", "call Route23_EventScript_JennyEntregas",
                    "call Route23_EventScript_JennyOferece"):
        assert chamada in cena, chamada
    # a flag da cena liga antes de soltar o jogador, e a Jenny volta ao posto antes (libera o caminho da porta)
    assert cena.index("setflag FLAG_FAMILIA_POLICIA_CENA") < cena.index("releaseall")
    assert cena.index("Route23_EventScript_JennyVoltaDaPorta") < cena.index("releaseall")
    assert "applymovement LOCALID_FAMILIA_POLICIA_JENNY, Route23_Movement_JennyVolta\n" in SCRIPTS
    for rotulo in ("Route23_EventScript_PoliciaJenny", "Route23_EventScript_PoliciaGrowlithe",
                   "Route23_EventScript_PoliciaArcanine"):
        s = _script(rotulo)
        assert "goto_if_questlog EventScript_ReleaseEnd" in s, rotulo
    assert "special Dossie_Abrir" in _script("Route23_EventScript_JennyOferece")
    assert "waitstate" in _script("Route23_EventScript_JennyOferece")
    de_novo = _script("Route23_EventScript_PoliciaJenny")
    assert de_novo.index("JennyEntregas") < de_novo.index("JennyOferece")      # a entrega pendente, depois a pergunta
    arcanine = _script("Route23_EventScript_PoliciaArcanine")
    assert "playmoncry SPECIES_ARCANINE" in arcanine and "Route23_Text_Arcanine" in arcanine
    assert '"Arcanine: Au! Au!$"' in TEXTOS


def test_jenny_volta_ao_posto():
    """A Jenny sai de (6, 150), chega ao tile à frente do jogador que sai da porta e volta ao posto: se ficasse à frente
    da porta, o jogador (em 4, 149) ficaria preso entre o prédio e os policiais."""
    jenny = _objetos()[8]
    posto = (jenny["x"], jenny["y"])
    assert posto == (6, 150)
    ida = re.search(r"Route23_Movement_JennyAteOJogador:\n(.*?)step_end", SCRIPTS, re.S).group(1).split()
    volta = re.search(r"Route23_Movement_JennyVolta:\n(.*?)step_end", SCRIPTS, re.S).group(1).split()
    passos = {"walk_right": (1, 0), "walk_left": (-1, 0), "walk_up": (0, -1), "walk_down": (0, 1)}
    outros = {(o["x"], o["y"]) for o in _objetos()[9:]}
    pos, trilha = posto, []
    for p in ida:
        if p in passos:
            pos = (pos[0] + passos[p][0], pos[1] + passos[p][1])
            trilha.append(pos)
    assert pos == (4, 150), pos                # a frente do jogador que sai da porta
    assert not set(trilha) & outros, f"a Jenny esbarra em {set(trilha) & outros}"
    for p in volta:
        if p in passos:
            pos = (pos[0] + passos[p][0], pos[1] + passos[p][1])
            assert pos not in outros, pos
    assert pos == posto, pos
    assert volta[-1] == "face_down"


# --- a entrega ------------------------------------------------------------------------------------------------------


def test_flags_da_policia():
    d = _defines(FLAGS_H)
    antigas = {int(v) for k, v in d.items() if k not in ("FLAG_FAMILIA_POLICIA_CENA", "FLAG_FAMILIA_ENTREGUE_3",
                                                         "FLAG_FAMILIA_ENTREGUE_4")}
    for nome in ("FLAG_FAMILIA_POLICIA_CENA", "FLAG_FAMILIA_ENTREGUE_3", "FLAG_FAMILIA_ENTREGUE_4"):
        assert nome in d and d[nome] not in antigas, nome
        assert re.search(rf"^#define\s+{nome}\s.*// POK-54", FLAGS_H, re.M), nome
    for velho in ("FLAG_0x4D6", "FLAG_0x4D7", "FLAG_0x4D8"):
        assert velho not in d              # o id virou nome próprio
    assert [d["FLAG_FAMILIA_POLICIA_CENA"], d["FLAG_FAMILIA_ENTREGUE_3"], d["FLAG_FAMILIA_ENTREGUE_4"]] == [
        0x4D6, 0x4D7, 0x4D8]
    for nome in ("FLAG_FAMILIA_POLICIA_CENA", "FLAG_FAMILIA_ENTREGUE_3", "FLAG_FAMILIA_ENTREGUE_4"):
        assert f"FlagClear({nome}" not in FAMILIA_C and nome not in _corpo(FAMILIA_C, "FamiliaSombra_Repovoar")


def test_entrega_sem_item():
    entrega = _corpo(FAMILIA_C, "FamiliaSombra_EntregarApreendido")
    assert "FamiliaSombra_CriarChefe(&mon, ocupacao, FALSE)" in entrega           # sem o item fixo do chefe
    assert "gSpecialVar_0x8004" in entrega and "GiveMonToPlayer(&mon)" in entrega
    # só liga a flag (e a Dex) quando o Pokémon chegou ao time ou ao PC; com MON_CANT_GIVE nada acontece
    assert re.search(r"if \(gSpecialVar_Result == MON_GIVEN_TO_PARTY \|\| gSpecialVar_Result == MON_GIVEN_TO_PC\)\s*\{"
                     r"(.*?)\n    \}", entrega, re.S)
    ramo = re.search(r"if \(gSpecialVar_Result == MON_GIVEN_TO_PARTY \|\| gSpecialVar_Result == MON_GIVEN_TO_PC\)\s*\{"
                     r"(.*?)\n    \}", entrega, re.S).group(1)
    assert "FLAG_SET_SEEN" in ramo and "FLAG_SET_CAUGHT" in ramo and "FlagSet(sEntregues[" in ramo
    assert entrega.count("FlagSet(") == 1
    assert "sCapturados" not in entrega and "CAPTURADO" not in entrega     # entregar não é capturar: o carimbo segue DERROTADO
    assert "MON_CANT_GIVE" in entrega
    pendente = _corpo(FAMILIA_C, "FamiliaSombra_ApreendidoPendente")
    assert pendente.index("ApreendidoPendente(3)") < pendente.index("ApreendidoPendente(4)")
    assert "FamiliaSombra_ChefeCapturado(ocupacao)" in _corpo(FAMILIA_C, "ApreendidoPendente")
    assert "sEntregues[ocupacao - FAMILIA_PRIMEIRO_APREENDIDO]" in _corpo(FAMILIA_C, "ApreendidoPendente")
    assert re.search(r"sEntregues\[\] =\s*\{\s*FLAG_FAMILIA_ENTREGUE_3,\s*FLAG_FAMILIA_ENTREGUE_4,\s*\};", FAMILIA_C)


def test_entrega_no_script():
    s = _script("Route23_EventScript_JennyEntregas")
    assert s.index("special FamiliaSombra_ApreendidoPendente") < s.index("special FamiliaSombra_EntregarApreendido")
    # o laço roda enquanto houver pendente; sem espaço a Jenny avisa e o laço para (return, nada de flag)
    assert "goto_if_eq VAR_RESULT, 0, Route23_EventScript_JennyEntregasFim" in s
    assert "goto_if_eq VAR_RESULT, MON_CANT_GIVE, Route23_EventScript_JennyEntregaSemEspaco" in s
    assert "goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC, Route23_EventScript_JennyEntregouAoPC" in s
    # o nome da espécie só entra no ramo do time: no do PC STR_VAR_1 é o nome da caixa (preenchido pelo C)
    assert s.index("bufferspeciesname STR_VAR_1") > s.index("goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC")
    # M1: a fanfarra de Pokémon recebido, a do FireRed (a de item é de item)
    assert "MUS_OBTAIN_ITEM" not in SCRIPTS[SCRIPTS.index("Route23_EventScript_JennyEntregas::"):]
    assert s.count("playfanfare MUS_LEVEL_UP") == 1 and "playfanfare MUS_LEVEL_UP" in _script(
        "Route23_EventScript_JennyEntregouAoPC")
    assert s.rstrip().endswith("goto Route23_EventScript_JennyEntregas")           # volta ao topo: o próximo da fila
    assert _script("Route23_EventScript_JennyEntregasFim").strip() == "return"
    assert "return" in _script("Route23_EventScript_JennyEntregaSemEspaco")
    assert "goto Route23_EventScript_JennyEntregas" in _script("Route23_EventScript_JennyEntregouAoPC")
    assert "FLAG_FAMILIA_ENTREGUE" not in s            # a flag é do C, só depois de dar certo


def test_especiais_no_fim():
    specials = re.findall(r"^\s*def_special (\w+)", (REPO_ROOT / "data/specials.inc").read_text("utf-8"), re.M)
    assert specials[-2:] == ["FamiliaSombra_ApreendidoPendente", "FamiliaSombra_EntregarApreendido"], specials[-4:]
    assert specials[-3] == "Dossie_Abrir"
    header = (REPO_ROOT / "include/familia_sombra.h").read_text(encoding="utf-8")
    assert "void FamiliaSombra_ApreendidoPendente(void);" in header
    assert "void FamiliaSombra_EntregarApreendido(void);" in header


# --- o que as revisões deixaram para esta task ----------------------------------------------------------------------


def test_criar_chefe_limita_a_ocupacao():
    corpo = _corpo(FAMILIA_C, "FamiliaSombra_CriarChefe")
    assert re.search(r"if \(ocupacao < 1 \|\| ocupacao > FAMILIA_OCUPACOES_TOTAL\)[^\n]*\n\s*ocupacao = 1;", corpo)
    assert corpo.index("ocupacao = 1;") < corpo.index("sFamiliaChefes[ocupacao - 1]")


def test_queda_do_ultimo_chefe_fica_gravada():
    """ENCERRADA também grava VAR_FAMILIA_QUEDA (antes guardava a do chefe 3)."""
    caiu = _corpo(FAMILIA_C, "FamiliaSombra_ChefeCaiu")
    assert caiu.index("VarSet(VAR_FAMILIA_QUEDA") < caiu.index("if (ocupacao >= FAMILIA_OCUPACOES_ATIVAS)")
    assert caiu.count("VAR_FAMILIA_QUEDA") == 1
    assert caiu.index("if (!FamiliaSombra_ChefeAtivo())") < caiu.index("VarSet(VAR_FAMILIA_QUEDA")


def test_bilhete_do_6o_andar_na_familia_encerrada():
    scripts = (SEIS_ANDARES / "scripts.inc").read_text(encoding="utf-8")
    textos = (SEIS_ANDARES / "text.inc").read_text(encoding="utf-8")
    sem_chefe = _script("Route23_FamiliaSombra_6F_EventScript_BilheteSemChefe", scripts)
    assert sem_chefe.index("FAMILIA_ESTADO_ENCERRADA, Route23_FamiliaSombra_6F_EventScript_BilheteEncerrada") < sem_chefe.index(
        "FamiliaSombra_GetOcupacao")
    texto = re.search(r"Route23_FamiliaSombra_6F_Text_BilheteEncerrada::\n(.*?)\$\"", textos, re.S).group(1)
    assert "fora" not in texto and "polícia" in texto


def test_textos_novos_sem_travessao():
    novos = TEXTOS[TEXTOS.index("Route23_Text_PortaFamiliaLacrada"):]
    assert "—" not in novos and "–" not in novos
    for rotulo in ("JennyCaso", "JennyApreendido3", "JennyApreendido4", "JennyRecebeu",
                   "JennySemEspaco", "JennyQuerOuvir", "JennyObrigada", "JennyDeNovo", "Policial1", "Policial2",
                   "Growlithe", "Arcanine"):
        assert f"Route23_Text_{rotulo}::" in novos, rotulo
    # a Jenny nomeia os dois chefes apreendidos
    assert "GARCHOMP" in novos and "DARKRAI" in novos


# --- rodada de correção 1 da revisão ------------------------------------------------------------------------------


def test_policia_escondida_tambem_no_on_load():
    """I1: o CONTINUAR de um save em pé na rota só roda o ON_LOAD: ele também esconde a polícia fora de ENCERRADA."""
    onload = _script("Route23_OnLoad")
    assert "call_if_ne VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_EsconderPolicia" in onload
    assert onload.index("special FamiliaSombra_GetEstado") < onload.index("Route23_EventScript_EsconderPolicia")


def test_apreendido_so_em_encerrada():
    """I1: sem a Família encerrada ninguém tem o que entregar nem pode receber (as 2 specials conferem o estado)."""
    pendente = _corpo(FAMILIA_C, "FamiliaSombra_ApreendidoPendente")
    assert re.search(r"if \(FamiliaSombra_Estado\(\) != FAMILIA_ESTADO_ENCERRADA\)\s*gSpecialVar_Result = 0;", pendente)
    entrega = _corpo(FAMILIA_C, "FamiliaSombra_EntregarApreendido")
    assert "FamiliaSombra_Estado() != FAMILIA_ESTADO_ENCERRADA" in entrega.split("FamiliaSombra_CriarChefe")[0]


def test_vaga_conferida_antes_de_criar_o_pokemon():
    """I2: GiveMonToPlayer conta o shiny nas conquistas antes de procurar vaga: sem vaga nem se cria nem se dá."""
    entrega = _corpo(FAMILIA_C, "FamiliaSombra_EntregarApreendido")
    antes = entrega.split("FamiliaSombra_CriarChefe")[0]
    assert "!HaVagaParaReceber()" in antes and "MON_CANT_GIVE" in antes
    assert entrega.index("!HaVagaParaReceber()") < entrega.index("GiveMonToPlayer")
    vaga = _corpo(FAMILIA_C, "HaVagaParaReceber")
    assert "CalculatePlayerPartyCount() < PARTY_SIZE" in vaga and "TOTAL_BOXES_COUNT" in vaga and "IN_BOX_COUNT" in vaga
    assert "SPECIES_NONE" in vaga and "GiveMonToPlayer" not in vaga


def test_aviso_do_pc_no_padrao_do_jogo():
    """M3: o PC usa os 4 textos do jogo (caixa em que ficou, caixa que estava cheia, PC de alguém ou do Bill)."""
    s = _script("Route23_EventScript_JennyEntregouAoPC")
    for texto in ("Text_MonSentToBoxInSomeonesPC", "Text_MonSentToBoxInBillsPC", "Text_MonSentToBoxSomeonesBoxFull",
                  "Text_MonSentToBoxBillsBoxFull"):
        assert texto in SCRIPTS, texto
    entrega = _corpo(FAMILIA_C, "FamiliaSombra_EntregarApreendido")
    assert "GetBoxNamePtr(VarGet(VAR_PC_BOX_TO_SEND_MON))" in entrega and "ShouldShowBoxWasFullMessage()" in entrega
    assert "GetBoxNamePtr(GetPCBoxToSendMon())" in entrega and "FLAG_SYS_NOT_SOMEONES_PC" in entrega
    assert "gSpecialVar_0x8006" in entrega and "VAR_0x8006" in s


def test_cada_movimento_da_jenny_tem_o_waitmovement_dela():
    """I4: `waitmovement 0` espera só o último applymovement: a Jenny tem o waitmovement dela, e o jogador, o dele."""
    cena = _script("Route23_EventScript_CenaPolicia")
    assert cena.index("applymovement LOCALID_PLAYER") < cena.index("waitmovement 0") < cena.index("call_if_ne VAR_TEMP_5")
    for rotulo in ("JennyVemDaPorta", "JennyVemDeFora", "JennyVoltaDaPorta", "JennyVoltaDeFora"):
        s = _script(f"Route23_EventScript_{rotulo}")
        assert re.search(r"applymovement LOCALID_FAMILIA_POLICIA_JENNY, \w+\n\twaitmovement LOCALID_FAMILIA_POLICIA_JENNY",
                         s), rotulo


def _caminho(movimento: str, inicio: tuple[int, int]) -> list[tuple[int, int]]:
    passos = {"walk_right": (1, 0), "walk_left": (-1, 0), "walk_up": (0, -1), "walk_down": (0, 1)}
    corpo = re.search(rf"{movimento}:\n(.*?)step_end", SCRIPTS, re.S).group(1).split()
    pos, caminho = inicio, []
    for p in corpo:
        if p in passos:
            pos = (pos[0] + passos[p][0], pos[1] + passos[p][1])
            caminho.append(pos)
    return caminho


def test_jenny_nunca_pisa_no_jogador():
    """I3: o jogador chega em (4, 149) (saiu pela porta) ou (4, 150) (escape warp): a Jenny para no tile à frente dele e
    volta ao posto; o y dele (VAR_TEMP_5) escolhe o roteiro."""
    posto = (6, 150)
    outros = {(o["x"], o["y"]) for o in _objetos()[9:]}
    for y_jogador, ida, volta, parada in ((149, "Route23_Movement_JennyAteOJogador", "Route23_Movement_JennyVolta", (4, 150)),
                                          (150, "Route23_Movement_JennyAteOJogadorDeFora",
                                           "Route23_Movement_JennyVoltaDeFora", (4, 151))):
        ate = _caminho(ida, posto)
        assert ate[-1] == parada and (4, y_jogador) not in ate, (y_jogador, ate)
        assert not set(ate) & outros
        de_volta = _caminho(volta, parada)
        assert de_volta[-1] == posto and not set(de_volta) & outros, (y_jogador, de_volta)
    cena = _script("Route23_EventScript_CenaPolicia")
    assert "getplayerxy VAR_0x8004, VAR_TEMP_5" in cena
    assert "call_if_ne VAR_TEMP_5, 150, Route23_EventScript_JennyVemDaPorta" in cena
    assert "call_if_eq VAR_TEMP_5, 150, Route23_EventScript_JennyVemDeFora" in cena
    assert "call_if_ne VAR_TEMP_5, 150, Route23_EventScript_JennyVoltaDaPorta" in cena
    assert "call_if_eq VAR_TEMP_5, 150, Route23_EventScript_JennyVoltaDeFora" in cena


def test_atalho_escape_warp_no_cabecalho():
    h = (REPO_ROOT / "include/test_hooks.h").read_text(encoding="utf-8")
    assert re.search(r"TEST_CMD_ESCAPE_WARP,\s*// = 0x146:", h)
    c = (REPO_ROOT / "src/test_hooks.c").read_text(encoding="utf-8")
    assert "case TEST_CMD_ESCAPE_WARP:" in c and "gSaveBlock1Ptr->escapeWarp.y = xy >> 16;" in c
