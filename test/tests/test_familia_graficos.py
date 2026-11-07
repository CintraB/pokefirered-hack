"""POK-51 (Task 2): gráficos da Família Sombra — chapéu nos sprites, rosas, redomas e taças. Leitura estática, sem emulador.

`tools/familia_sombra/gerar.py` gera tudo (PNG, paletas, tabelas C, bloco de constantes, `slots.json`); estes testes
conferem que o gerado bate com o gerador, que cabe nas 16 cores, que os slots de paleta valem e que o C registra
cada gráfico e cada item.
"""

import json
import os
import re
import struct
import subprocess
import sys

import pytest
from PIL import Image

from esteira.scenarios import REPO_ROOT

GERADOR = REPO_ROOT / "tools" / "familia_sombra" / "gerar.py"
SLOTS_JSON = REPO_ROOT / "tools" / "familia_sombra" / "slots.json"
PICS = REPO_ROOT / "graphics" / "object_events" / "pics" / "familia"
PALS = REPO_ROOT / "graphics" / "object_events" / "palettes" / "familia"
ICONES = REPO_ROOT / "graphics" / "items" / "icons"
ICONES_PALS = REPO_ROOT / "graphics" / "items" / "icon_palettes"
EVENT_OBJECTS_H = REPO_ROOT / "include" / "constants" / "event_objects.h"
GFX_H = REPO_ROOT / "src" / "data" / "object_events" / "familia_gfx.h"
POINTERS_H = REPO_ROOT / "src" / "data" / "object_events" / "object_event_graphics_info_pointers.h"
SUBSPRITES_H = REPO_ROOT / "src" / "data" / "object_events" / "object_event_subsprites.h"
MOVEMENT_C = REPO_ROOT / "src" / "event_object_movement.c"
ITEMS_JSON = REPO_ROOT / "src" / "data" / "items.json"
ITEMS_H = REPO_ROOT / "include" / "constants" / "items.h"
ICON_TABLE = REPO_ROOT / "src" / "data" / "item_icon_table.h"
ICONS_GFX_H = REPO_ROOT / "src" / "data" / "graphics" / "items.h"
RULES_MK = REPO_ROOT / "spritesheet_rules.mk"

ESPECIES = ["haunter", "misdreavus", "sableye", "banette", "houndour", "houndoom", "murkrow", "sneasel", "crobat",
            "muk", "weezing", "arbok", "mightyena", "absol", "cacturne", "shiftry", "crawdaunt", "golem", "persian",
            "machamp", "rhydon"]
PARTE2 = ["gligar", "dusclops"]                      # POK-54: chapéus novos, ids 186 e 187
CHEFES_PARTE2 = ["garchomp_shiny", "darkrai_shiny"]  # POK-54: ids 188 e 189
SPRITES_PARTE1 = ESPECIES + ["gengar_shiny", "tyranitar_shiny"]
SPRITES = SPRITES_PARTE1 + PARTE2 + CHEFES_PARTE2
REDOMAS = ["vazia", "vermelha", "dourada", "azul", "negra"]
TACAS = ["bronze", "prata", "ouro"]
ROSAS = {"vermelha": 87, "dourada": 88, "azul": 89, "negra": 90}
# a ordem dos ids: parte 1 (sprites, redomas, taças) e, no fim, a parte 2
GFX_IDS_PARTE1 = (
    [f"OBJ_EVENT_GFX_FAMILIA_{e.upper()}" for e in SPRITES_PARTE1]
    + [f"OBJ_EVENT_GFX_REDOMA_{r.upper()}" for r in REDOMAS]
    + [f"OBJ_EVENT_GFX_TACA_{t.upper()}" for t in TACAS]
)
GFX_IDS_PARTE2 = [f"OBJ_EVENT_GFX_FAMILIA_{e.upper()}" for e in PARTE2 + CHEFES_PARTE2]
GFX_IDS = GFX_IDS_PARTE1 + GFX_IDS_PARTE2
ARQUIVO_DO_GFX = dict(zip(GFX_IDS, SPRITES_PARTE1 + [f"redoma_{r}" for r in REDOMAS] + [f"taca_{t}" for t in TACAS]
                          + PARTE2 + CHEFES_PARTE2))
SLOTS = {"PALSLOT_NPC_1", "PALSLOT_NPC_2", "PALSLOT_NPC_3", "PALSLOT_NPC_4"}
TAMANHO = {"sprite": (32, 40), "redoma": (32, 32), "taca": (16, 32)}


def _tipo(arquivo):
    return "redoma" if arquivo.startswith("redoma_") else "taca" if arquivo.startswith("taca_") else "sprite"


def _pal(caminho):
    texto = caminho.read_bytes().decode("ascii")
    assert texto.count("\r\n") == texto.count("\n"), f"{caminho.name}: o .pal tem de ser CRLF"
    linhas = texto.split("\r\n")
    assert linhas[:3] == ["JASC-PAL", "0100", "16"], caminho.name
    cores = [tuple(int(v) for v in l.split()) for l in linhas[3:19]]
    assert len(cores) == 16 and linhas[19:] == [""], f"{caminho.name}: tem de ter 16 cores"
    return cores


def _bits_do_png(caminho):
    d = caminho.read_bytes()
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    largura, altura, profundidade, tipo = struct.unpack(">IIBB", d[16:26])
    return largura, altura, profundidade, tipo


def _constantes():
    texto = EVENT_OBJECTS_H.read_text(encoding="utf-8")
    return {n: int(v) for n, v in re.findall(r"#define (OBJ_EVENT_GFX_\w+)\s+(\d+)\b", texto) if int(v) < 240}


# ---------- gerador ----------
def test_gerador_confere():
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    r = subprocess.run([sys.executable, "-I", str(GERADOR), "--conferir"], capture_output=True, text=True, env=env,
                       cwd=REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stderr == ""


def test_ajustes_so_de_especies_conhecidas():
    ajustes = json.loads((REPO_ROOT / "tools" / "familia_sombra" / "ajustes.json").read_text(encoding="utf-8"))
    conhecidas = set(ESPECIES) | {"gengar", "tyranitar"} | set(PARTE2) | {"garchomp", "darkrai"}
    assert set(ajustes) <= conhecidas
    for dx, dy in ajustes.values():
        assert -4 <= dx <= 4 and 0 <= dy <= 10


# ---------- cores e paletas ----------
@pytest.mark.parametrize("arquivo", ARQUIVO_DO_GFX.values())
def test_chapeu_cabe_na_paleta(arquivo):
    caminho = PICS / f"{arquivo}.png"
    largura, altura, profundidade, tipo = _bits_do_png(caminho)
    assert tipo == 3 and profundidade == 4, "PNG indexado de 4 bits"
    assert (largura, altura) == TAMANHO[_tipo(arquivo)]
    im = Image.open(caminho)
    usados = set(im.tobytes())
    assert max(usados) <= 15
    assert 0 in usados, "tem de sobrar fundo (índice 0 = transparente)"
    assert im.getpixel((0, 0)) == 0 and im.getpixel((largura - 1, 0)) == 0
    assert len(usados - {0}) <= 15


def test_cada_png_confere_com_a_paleta_dele():
    paletas = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))["paletas"]
    for gfx, arquivo in ARQUIVO_DO_GFX.items():
        pal = _pal(PALS / f"{paletas[gfx]}.pal")
        png = Image.open(PICS / f"{arquivo}.png")
        png_pal = png.getpalette()[:48]
        for i in range(1, 16):
            if i in set(png.tobytes()):
                assert tuple(png_pal[3 * i:3 * i + 3]) == pal[i], f"{arquivo}: índice {i}"


@pytest.mark.parametrize("pal", sorted(p.name for p in PALS.glob("*.pal")))
def test_paletas_jasc_de_16_cores_em_5_bits(pal):
    cores = _pal(PALS / pal)
    assert cores[0] == (115, 197, 164), "índice 0 = a cor de transparência das paletas de NPC"
    for cor in cores[1:]:
        assert all(0 <= v <= 255 and v % 8 == 0 for v in cor), cor


@pytest.mark.parametrize("arquivo", SPRITES)
def test_chapeu_esta_no_sprite(arquivo):
    """As cores do chapéu (fita vermelha e copa escura) estão no sprite: a fita é a cor R da prévia."""
    pal = _pal(PALS / f"{arquivo}.pal")
    png = Image.open(PICS / f"{arquivo}.png")
    usadas = {tuple(png.getpalette()[3 * i:3 * i + 3]) for i in set(png.tobytes()) if i}
    assert (208, 32, 40) in usadas, "fita vermelha do chapéu"
    assert any(sum(c) < 100 for c in usadas), "contorno escuro do chapéu"
    assert len(usadas) <= 15 and set(usadas) <= set(pal)


def test_redomas_e_tacas_dividem_paleta():
    paletas = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))["paletas"]
    assert paletas["OBJ_EVENT_GFX_REDOMA_VAZIA"] == paletas["OBJ_EVENT_GFX_REDOMA_VERMELHA"] == paletas[
        "OBJ_EVENT_GFX_REDOMA_DOURADA"]
    assert paletas["OBJ_EVENT_GFX_REDOMA_AZUL"] == paletas["OBJ_EVENT_GFX_REDOMA_NEGRA"]
    assert paletas["OBJ_EVENT_GFX_REDOMA_VAZIA"] != paletas["OBJ_EVENT_GFX_REDOMA_AZUL"]
    assert len({paletas[f"OBJ_EVENT_GFX_TACA_{t.upper()}"] for t in TACAS}) == 1


def test_redoma_vazia_nao_tem_rosa_e_as_cheias_tem_cor_propria():
    def cores(arquivo):
        im = Image.open(PICS / f"{arquivo}.png")
        return {tuple(im.getpalette()[3 * i:3 * i + 3]) for i in set(im.tobytes()) if i}

    vazia = cores("redoma_vazia")
    for r in ("vermelha", "dourada", "azul", "negra"):
        cheia = cores(f"redoma_{r}")
        assert len(cheia) > len(vazia)
        assert cheia >= vazia
    extra ={r: cores(f"redoma_{r}") - vazia for r in ("vermelha", "dourada", "azul", "negra")}
    for a in extra:
        for b in extra:
            if a != b:
                assert extra[a] != extra[b], (a, b)


def test_tacas_tem_o_metal_de_cada_uma():
    def cores(arquivo):
        im = Image.open(PICS / f"{arquivo}.png")
        return {tuple(im.getpalette()[3 * i:3 * i + 3]) for i in set(im.tobytes()) if i}

    bronze, prata, ouro = (cores(f"taca_{t}") for t in TACAS)
    assert bronze != prata != ouro and bronze != ouro
    assert (232, 160, 96) in bronze and (240, 240, 248) in prata and (248, 240, 128) in ouro  # claro de cada metal, em 5 bits


# ---------- slots de paleta ----------
def test_slots_de_paleta():
    dados = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))
    assert set(dados["slots"]) == set(GFX_IDS), "slots.json cobre todos os gráficos"
    assert set(dados["slots"].values()) <= SLOTS
    assert set(dados["paletas"]) == set(GFX_IDS)
    # quem divide paleta divide slot; paletas diferentes no mesmo slot não aparecem no mesmo grupo
    por_paleta = {}
    for gfx, p in dados["paletas"].items():
        por_paleta.setdefault(p, set()).add(dados["slots"][gfx])
    assert all(len(s) == 1 for s in por_paleta.values())
    for nome, membros in dados["grupos"].items():
        slots = [dados["slots"][g] for g in membros if g in dados["slots"]]
        paletas = {dados["paletas"][g] for g in membros}
        assert len({dados["slots"][g] for g in membros}) == len(paletas), nome
        assert len(paletas) <= 4, nome
        assert slots, nome


def test_slots_dos_grupos_do_roteiro():
    dados = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))
    s = dados["slots"]
    assert s["OBJ_EVENT_GFX_FAMILIA_GENGAR_SHINY"] != s["OBJ_EVENT_GFX_FAMILIA_MACHAMP"]       # sala do Dom
    assert s["OBJ_EVENT_GFX_FAMILIA_TYRANITAR_SHINY"] != s["OBJ_EVENT_GFX_FAMILIA_RHYDON"]     # sala do Cobrador
    # sala de troféus: 2 paletas de redoma + 1 de taças em 3 slots, sobra 1 para o curador
    slots_da_sala = {s[g] for g in s if "REDOMA" in g or "TACA" in g}
    assert len(slots_da_sala) == 3


def test_slots_equilibrados_para_o_plantel():
    """Cada andar escolhe até 4 espécies de slots diferentes: nenhum slot pode ficar sem espécies suficientes."""
    s = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))["slots"]
    contagem = {slot: 0 for slot in SLOTS}
    for e in ESPECIES:
        contagem[s[f"OBJ_EVENT_GFX_FAMILIA_{e.upper()}"]] += 1
    assert min(contagem.values()) >= 4, contagem


# ---------- registros em C ----------
def test_chapeus_parte2():
    """POK-54: Gligar, Dusclops, Garchomp e Darkrai shiny de chapéu: 32x40, até 15 cores e fundo transparente. O
    Garchomp e o Darkrai passam de 18 e 16 cores para 15 pela reduzir_cores do gerador."""
    for arquivo in PARTE2 + CHEFES_PARTE2:
        largura, altura, profundidade, tipo = _bits_do_png(PICS / f"{arquivo}.png")
        assert (largura, altura, profundidade, tipo) == (32, 40, 4, 3), arquivo
        im = Image.open(PICS / f"{arquivo}.png")
        usados = set(im.tobytes())
        assert 0 in usados and im.getpixel((0, 0)) == 0 and im.getpixel((31, 0)) == 0, arquivo
        assert 1 <= len(usados - {0}) <= 15 and max(usados) <= 15, arquivo
    for arquivo, antes in (("garchomp_shiny", 18), ("darkrai_shiny", 16)):
        sprite = Image.open(PICS / f"{arquivo}.png")
        assert len(set(sprite.tobytes()) - {0}) == 15, (arquivo, antes)
    # o ajuste do chapéu dos dois chefes (0, 4), como na prévia
    ajustes = json.loads((REPO_ROOT / "tools" / "familia_sombra" / "ajustes.json").read_text(encoding="utf-8"))
    assert ajustes["garchomp"] == [0, 4] and ajustes["darkrai"] == [0, 4]


def test_ids_gfx_no_fim():
    """O id vai para o save: a parte 1 (155..185) fica igual à base e a parte 2 entra no fim (186..189)."""
    c = _constantes()
    for i, gfx in enumerate(GFX_IDS_PARTE1):
        assert c[gfx] == 155 + i, gfx
    assert [c[g] for g in GFX_IDS_PARTE2] == [186, 187, 188, 189]
    assert c["OBJ_EVENT_GFX_FAMILIA_GLIGAR"] == 186 and c["OBJ_EVENT_GFX_FAMILIA_DUSCLOPS"] == 187
    assert c["OBJ_EVENT_GFX_FAMILIA_GARCHOMP_SHINY"] == 188 and c["OBJ_EVENT_GFX_FAMILIA_DARKRAI_SHINY"] == 189
    assert re.search(r"#define NUM_OBJ_EVENT_GFX\s+190\b", EVENT_OBJECTS_H.read_text(encoding="utf-8"))
    # a base (v70) está congelada em ids_do_save_184573748.json: nada dela mudou de número
    base = json.loads((REPO_ROOT / "test" / "tests" / "dados" / "ids_do_save_184573748.json").read_text(
        encoding="utf-8"))["familias"]["OBJ_EVENT_GFX_"]
    assert base["OBJ_EVENT_GFX_FAMILIA_MACHAMP"] == 174
    for nome, valor in base.items():
        if valor < 240:
            assert c[nome] == valor, nome


def test_slots_salas_parte2():
    """POK-54: as duas salas novas do prédio da Rota 23 não repetem slot (cada paleta de um slot só, por sala)."""
    dados = json.loads(SLOTS_JSON.read_text(encoding="utf-8"))
    salas = {"sala_do_mercenario": ["OBJ_EVENT_GFX_FAMILIA_GARCHOMP_SHINY", "OBJ_EVENT_GFX_FAMILIA_GLIGAR"],
             "sala_do_pesadelo": ["OBJ_EVENT_GFX_FAMILIA_DARKRAI_SHINY", "OBJ_EVENT_GFX_FAMILIA_DUSCLOPS"]}
    for sala, membros in salas.items():
        assert sorted(dados["grupos"][sala]) == sorted(membros), sala
        slots = [dados["slots"][g] for g in membros]
        assert len(set(slots)) == len(slots), (sala, slots)
        assert set(slots) <= SLOTS
    # a parte 1 não mudou de slot por causa da parte 2
    assert dados["slots"]["OBJ_EVENT_GFX_FAMILIA_GENGAR_SHINY"] == "PALSLOT_NPC_1"


def test_ids_dos_graficos_seguem_o_follower():
    c = _constantes()
    assert c["OBJ_EVENT_GFX_FOLLOWER_LARGE"] == 154
    for i, gfx in enumerate(GFX_IDS):
        assert c[gfx] == 155 + i, gfx
    texto = EVENT_OBJECTS_H.read_text(encoding="utf-8")
    assert re.search(rf"#define NUM_OBJ_EVENT_GFX\s+{155 + len(GFX_IDS)}\b", texto)
    assert max(c.values()) == 154 + len(GFX_IDS)
    assert len(set(c.values())) == len(c)


def test_graphics_info_e_ponteiros():
    gfx = GFX_H.read_text(encoding="utf-8")
    ponteiros = (REPO_ROOT / "src" / "data" / "object_events" / "familia_gfx_ponteiros.h").read_text(encoding="utf-8")
    tabela = POINTERS_H.read_text(encoding="utf-8")
    assert '"familia_gfx_ponteiros.h"' in tabela and '"familia_gfx_extern.h"' in tabela
    assert len(re.findall(r"\bgObjectEventGraphicsInfo_Familia_\w+ = \{", gfx)) == len(GFX_IDS)
    for g in GFX_IDS:
        assert re.search(rf"\[{g}\]\s*=\s*&gObjectEventGraphicsInfo_Familia_\w+,", ponteiros), g
    blocos = re.findall(r"gObjectEventGraphicsInfo_Familia_(\w+) = \{(.*?)\n\};", gfx, re.S)
    assert len(blocos) == len(GFX_IDS)
    for nome, corpo in blocos:
        slot = re.search(r"\.paletteSlot = (\w+),", corpo).group(1)
        assert slot in SLOTS, nome
        tag = re.search(r"\.paletteTag = (OBJ_EVENT_PAL_TAG_FAMILIA_\w+),", corpo)
        assert tag, nome
        assert "sAnimTable_Standard" in corpo and ".tracks = TRACKS_NONE" in corpo


def test_tamanhos_do_graphics_info():
    gfx = GFX_H.read_text(encoding="utf-8")
    campos = {"sprite": ("640", "32", "40", "gObjectEventBaseOam_32x32", "gObjectEventSpriteOamTables_32x40"),
              "redoma": ("512", "32", "32", "gObjectEventBaseOam_32x32", "gObjectEventSpriteOamTables_32x32"),
              "taca": ("256", "16", "32", "gObjectEventBaseOam_16x32", "gObjectEventSpriteOamTables_16x32")}
    for gfx_id, arquivo in ARQUIVO_DO_GFX.items():
        ponteiro = (REPO_ROOT / "src" / "data" / "object_events" / "familia_gfx_ponteiros.h").read_text(encoding="utf-8")
        nome = re.search(rf"\[{gfx_id}\]\s*=\s*&gObjectEventGraphicsInfo_Familia_(\w+),", ponteiro).group(1)
        corpo = re.search(rf"gObjectEventGraphicsInfo_Familia_{nome} = \{{(.*?)\n\}};", gfx, re.S).group(1)
        tam, w, h, oam, tabelas = campos[_tipo(arquivo)]
        assert f".size = {tam}," in corpo and f".width = {w}," in corpo and f".height = {h}," in corpo, arquivo
        assert f"&{oam}," in corpo and f"{tabelas}," in corpo, arquivo
        # um quadro só, repetido: 10 entradas (a sAnimTable_Standard vai até o quadro 9)
        tab = re.search(rf"sFamiliaPicTable_{nome}\[\] = \{{(.*?)\n\}};", gfx, re.S).group(1)
        assert tab.count(f"sFamiliaPic_{nome}") == 10 and tab.count(", 0)") == 10
        assert f"pics/familia/{arquivo}.4bpp" in gfx


def test_paletas_com_tag_unica_e_registradas():
    gfx = GFX_H.read_text(encoding="utf-8")
    tags = dict(re.findall(r"#define (OBJ_EVENT_PAL_TAG_FAMILIA_\w+) (0x[0-9A-F]{4})", gfx))
    primeira = int(tags.pop("OBJ_EVENT_PAL_TAG_FAMILIA_FIRST"), 16)
    valores = [int(v, 16) for v in tags.values()]
    assert len(set(valores)) == len(valores) and min(valores) == primeira
    movimento = MOVEMENT_C.read_text(encoding="utf-8")
    ultimo_conhecido = max(int(v, 16) for v in re.findall(r"#define OBJ_EVENT_PAL_TAG_\w+\s+(0x11[0-9A-F]{2})", movimento)
                           if int(v, 16) != 0x11FF)
    assert primeira > ultimo_conhecido and max(valores) < 0x11FF
    registradas = (REPO_ROOT / "src" / "data" / "object_events" / "familia_gfx_paletas.h").read_text(encoding="utf-8")
    for tag in tags:
        assert f", {tag}}}," in registradas, tag
    assert 'familia_gfx_paletas.h"' in movimento and 'familia_gfx.h"' in movimento
    # cada .pal tem o gbapal incluído
    for p in PALS.glob("*.pal"):
        assert f"palettes/familia/{p.stem}.gbapal" in gfx


def test_motor_grava_a_paleta_da_familia():
    c = MOVEMENT_C.read_text(encoding="utf-8")
    funcao = re.search(r"static void LoadFamiliaObjectPalette\([^;]*?\)\n\{.*?\n\}", c, re.S).group(0)
    assert "PALSLOT_NPC_1" in funcao and "PALSLOT_NPC_4" in funcao and "OBJ_EVENT_PAL_TAG_FAMILIA_FIRST" in funcao
    assert "PatchObjectPalette(graphicsInfo->paletteTag, graphicsInfo->paletteSlot)" in funcao
    assert c.count("LoadFamiliaObjectPalette(") >= 6   # protótipo, definição, spawn, volta ao campo, troca de gráfico, retint
    setup = re.search(r"static u8 TrySetupObjectEventSprite\(.*?\n\}", c, re.S).group(0)
    assert "LoadFamiliaObjectPalette(graphicsInfo)" in setup
    troca = re.search(r"void ObjectEventSetGraphicsId\(.*?\n\}", c, re.S).group(0)
    assert "LoadFamiliaObjectPalette(graphicsInfo)" in troca
    retint = re.search(r"void ReloadObjectEventPalettes\(.*?\n\}", c, re.S).group(0)
    assert "LoadFamiliaObjectPalette(" in retint
    volta = re.search(r"static void SpawnObjectEventOnReturnToField\(u8 objectEventId, s16 x, s16 y\)\n\{.*?\n\}", c, re.S).group(0)
    assert "LoadFamiliaObjectPalette(graphicsInfo)" in volta, "ResumeMap regrava os slots de NPC antes de recriar os objetos"


def test_tabela_de_subsprites_32x40():
    h = SUBSPRITES_H.read_text(encoding="utf-8")
    tabela = re.search(r"gObjectEventSpriteOamTables_32x40\[\] = \{(.*?)\};", h, re.S).group(1)
    assert len(re.findall(r"\{\d, ", tabela)) == 6 and "{0, NULL}" in tabela
    # cada tabela cobre os 20 tiles (4x5) uma vez: 32x32 + 32x8, ou 32x16 + 32x8 + 32x16
    tiles = {"32x32": 16, "32x16": 8, "32x8": 4}
    for i in range(5):
        corpo = re.search(rf"gObjectEventSpriteOamTable_32x40_{i}\[\] = \{{(.*?)\n\}};", h, re.S).group(1)
        formas = re.findall(r"\.shape = SPRITE_SHAPE\((\w+)\)", corpo)
        offsets = [int(v) for v in re.findall(r"\.tileOffset = (\d+)", corpo)]
        ys = [int(v) for v in re.findall(r"\.y = (-?\d+)", corpo)]
        assert sum(tiles[f] for f in formas) == 20, i
        assert offsets[0] == 0 and offsets == sorted(offsets)
        proximo = 0
        for f, o in zip(formas, offsets):
            assert o == proximo
            proximo += tiles[f]
        altura = {"32x32": 32, "32x16": 16, "32x8": 8}
        y = -20
        for f, yy in zip(formas, ys):
            assert yy == y, (i, yy, y)
            y += altura[f]
        assert y == 20


def test_regras_do_make_para_os_tamanhos():
    mk = RULES_MK.read_text(encoding="utf-8")
    assert re.search(r"familia/%\.4bpp: .*\n\t\$\(GFX\) \$< \$@ -mwidth 4 -mheight 5", mk)
    assert re.search(r"familia/redoma_%\.4bpp: .*\n\t\$\(GFX\) \$< \$@ -mwidth 4 -mheight 4", mk)
    assert re.search(r"familia/taca_%\.4bpp: .*\n\t\$\(GFX\) \$< \$@ -mwidth 2 -mheight 4", mk)


def test_persian_e_o_plantel_da_parte_1():
    c = _constantes()
    assert "OBJ_EVENT_GFX_FAMILIA_PERSIAN" in c
    assert len([k for k in c if k.startswith("OBJ_EVENT_GFX_FAMILIA_")]) == 23 + len(PARTE2 + CHEFES_PARTE2)  # POK-54: +4
    assert {k for k in c if k.startswith("OBJ_EVENT_GFX_REDOMA_")} == {f"OBJ_EVENT_GFX_REDOMA_{r.upper()}" for r in REDOMAS}
    assert {k for k in c if k.startswith("OBJ_EVENT_GFX_TACA_")} == {f"OBJ_EVENT_GFX_TACA_{t.upper()}" for t in TACAS}


# ---------- rosas: itens-chave ----------
def _itens():
    return json.loads(ITEMS_JSON.read_text(encoding="utf-8"))["items"]


def test_rosas_sao_itens_chave():
    itens = _itens()
    constantes = dict(re.findall(r"#define (ITEM_\w+) (\d+)", ITEMS_H.read_text(encoding="utf-8")))
    nomes = {"vermelha": "Rosa Vermelha", "dourada": "Rosa Dourada", "azul": "Rosa Azul", "negra": "Rosa Negra"}
    for cor, slot in ROSAS.items():
        item = itens[slot]
        assert item["itemId"] == f"ITEM_ROSA_{cor.upper()}"
        assert int(constantes[item["itemId"]]) == slot
        assert item["english"] == nomes[cor] and len(item["english"]) <= 13
        assert item["pocket"] == "POCKET_KEY_ITEMS" and item["price"] == 0
        assert item["importance"] == 1 and item["registrability"] == 0
        assert item["type"] == "ITEM_TYPE_BAG_MENU" and item["fieldUseFunc"] == "FieldUseFunc_OakStopsYou"
        assert item["holdEffect"] == "HOLD_EFFECT_NONE" and item["battleUsage"] == 0
        desc = item["description_english"]
        assert desc.count("\\n") <= 2 and not re.search(r"\\n\s|\s\\n|\\n\\n", desc)
    vistos = [i["itemId"] for i in itens]
    assert len(vistos) == len(set(v for v in vistos if v != "ITEM_NONE")) + vistos.count("ITEM_NONE")


def test_descricoes_das_rosas_contam_o_chefe():
    itens = _itens()
    texto = {cor: itens[slot]["description_english"] for cor, slot in ROSAS.items()}
    assert "Dom" in texto["vermelha"] and "Gengar" in texto["vermelha"] and "lapela" in texto["vermelha"]
    assert "Cobrador" in texto["dourada"] and "Tyranitar" in texto["dourada"]
    assert "Mercenário" in texto["azul"] and "Garchomp" in texto["azul"]
    assert "Pesadelo" in texto["negra"] and "Darkrai" in texto["negra"]


def test_rosas_tem_icone_registrado():
    tabela = ICON_TABLE.read_text(encoding="utf-8")
    gfx = ICONS_GFX_H.read_text(encoding="utf-8")
    graficos = (REPO_ROOT / "include" / "graphics.h").read_text(encoding="utf-8")
    for cor in ROSAS:
        nome = cor.capitalize()
        m = re.search(rf"\[ITEM_ROSA_{cor.upper()}\]\s*=\s*\{{gItemIcon_Rosa{nome}, gItemIconPalette_Rosa{nome}\}}", tabela)
        assert m, cor
        assert f'gItemIcon_Rosa{nome}[] = INCBIN_U32("graphics/items/icons/rosa_{cor}.4bpp.lz")' in gfx
        assert f'gItemIconPalette_Rosa{nome}[] = INCBIN_U32("graphics/items/icon_palettes/rosa_{cor}.gbapal.lz")' in gfx
        assert f"extern const u32 gItemIcon_Rosa{nome}[];" in graficos
        assert f"extern const u32 gItemIconPalette_Rosa{nome}[];" in graficos


@pytest.mark.parametrize("cor", ROSAS)
def test_icone_da_rosa_24x24_4bpp_e_pal_jasc(cor):
    png = ICONES / f"rosa_{cor}.png"
    assert _bits_do_png(png) == (24, 24, 4, 3)
    im = Image.open(png)
    usados = set(im.tobytes())
    assert 0 in usados and max(usados) <= 15
    pal = _pal(ICONES_PALS / f"rosa_{cor}.pal")
    assert pal[0] == (180, 180, 180)
    paleta_png = im.getpalette()[:48]
    for i in usados:
        assert tuple(paleta_png[3 * i:3 * i + 3]) == pal[i]
    assert len(usados - {0}) >= 6, "rosa de 4 tons e caule verde"


def test_rosas_de_cores_diferentes():
    def cores(cor):
        im = Image.open(ICONES / f"rosa_{cor}.png")
        return {tuple(im.getpalette()[3 * i:3 * i + 3]) for i in set(im.tobytes()) if i}

    verdes = cores("vermelha") & cores("dourada") & cores("azul") & cores("negra")
    assert len(verdes) == 3, "as 4 dividem o caule e as folhas"
    for a in ROSAS:
        for b in ROSAS:
            if a < b:
                assert cores(a) - verdes != cores(b) - verdes
