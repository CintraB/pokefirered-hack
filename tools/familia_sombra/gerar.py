"""Gráficos da Família Sombra (POK-51): chapéu nos sprites do mapa, rosas, redomas e taças.

    python3 -I tools/familia_sombra/gerar.py              # grava tudo no repositório
    python3 -I tools/familia_sombra/gerar.py --conferir   # refaz num diretório temporário e compara (sai 1 se divergir)
    python3 -I tools/familia_sombra/gerar.py --folha saida.png   # folha de conferência (todos os sprites 4x; não grava o resto)

Entradas: os sprites de seguidor (`graphics/object_events/pics/seguidores/<espécie>.png`, quadro 0 = parado olhando
para baixo) com as paletas `palettes/seguidores/<espécie>[_shiny].pal`, e `ajustes.json` (posição do chapéu por espécie:
`{"haunter": [dx, dy]}`; o que falta usa DAJUSTE_PADRAO). O desenho do chapéu, das rosas, da redoma e das taças está
neste arquivo (saiu da prévia aprovada `.superpowers/brainstorm/familia-sombra/previa.py`).

Saídas (todas versionadas, nada à mão):

    graphics/object_events/pics/familia/<nome>.png           sprite 32x40 com chapéu (1 quadro), 4 bits indexado
    graphics/object_events/pics/familia/redoma_<x>.png       redoma 32x32 (vazia, vermelha, dourada, azul, negra)
    graphics/object_events/pics/familia/taca_<x>.png         taça 16x32 (bronze, prata, ouro)
    graphics/object_events/pics/familia/policia_<x>.png      Growlithe e Arcanine da polícia, 32x32 (quadro 0 do seguidor, sem chapéu)
    graphics/object_events/pics/familia/oficial_jenny.png    a Oficial Jenny, NPC 160x32 (10 quadros 16x32), paleta própria
    graphics/object_events/palettes/familia/*.pal            JASC 16 cores (índice 0 = transparente), uma por sprite;
                                                             redomas_a/redomas_b (duas rosas por paleta) e tacas
    graphics/items/icons/rosa_<x>.png + icon_palettes/rosa_<x>.pal   ícones 24x24 das 4 rosas
    tools/familia_sombra/slots.json                          slot de paleta de cada gráfico (PALSLOT_NPC_1..4)
    src/data/object_events/familia_gfx*.h                    tabelas C (imagens, paletas, graphics info, ponteiros)
    include/constants/event_objects.h                        bloco OBJ_EVENT_GFX_FAMILIA_* (entre marcadores)

Cada gráfico do mapa tem a própria paleta (tag OBJ_EVENT_PAL_TAG_FAMILIA_*), gravada em tempo de execução no slot
`PALSLOT_NPC_n` dele (src/event_object_movement.c). Dois gráficos de paletas diferentes no mesmo slot, no mesmo mapa,
mostram as cores trocadas: por isso o slot é fixo e sai em `slots.json`, e as redomas e as taças dividem paletas.

Só Pillow e a biblioteca padrão.
"""

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
SEG_PICS = Path("graphics/object_events/pics/seguidores")
SEG_PALS = Path("graphics/object_events/palettes/seguidores")
PICS = Path("graphics/object_events/pics/familia")
PALS = Path("graphics/object_events/palettes/familia")
ICONES = Path("graphics/items/icons")
ICONES_PALS = Path("graphics/items/icon_palettes")
SLOTS_REL = Path("tools/familia_sombra/slots.json")
CONSTANTES_REL = Path("include/constants/event_objects.h")
C_DIR = Path("src/data/object_events")
C_GFX = C_DIR / "familia_gfx.h"
C_EXTERN = C_DIR / "familia_gfx_extern.h"
C_PONTEIROS = C_DIR / "familia_gfx_ponteiros.h"
C_PALETAS = C_DIR / "familia_gfx_paletas.h"
AJUSTES = AQUI / "ajustes.json"

COR_INDICE_0 = (115, 197, 164)  # a mesma que as paletas de NPC usam no índice 0
MAX_CORES = 15                  # o índice 0 é a transparência
DESLOCAMENTO_Y = 9              # o quadro 32x32 desce 9 linhas na tela 32x40 (sobra espaço para o chapéu em cima)
LARGURA, ALTURA = 32, 40
DAJUSTE_PADRAO = (0, 3)
PRIMEIRO_GFX = 155              # logo depois de OBJ_EVENT_GFX_FOLLOWER_LARGE (154)
PRIMEIRA_TAG = 0x1120           # OBJ_EVENT_PAL_TAG_* de NPC vão até 0x111C; 0x11FF é o NONE
QUADROS_NA_TABELA = 10          # sAnimTable_Standard pede até o quadro 9 (ANIM_RAISE_HAND); todos iguais

# plantel da parte 1 (ordem fixa: o id do gráfico depende dela), depois os dois chefes shiny
ESPECIES = ["haunter", "misdreavus", "sableye", "banette", "houndour", "houndoom", "murkrow", "sneasel", "crobat",
            "muk", "weezing", "arbok", "mightyena", "absol", "cacturne", "shiftry", "crawdaunt", "golem", "persian",
            "machamp", "rhydon"]
CHEFES_SHINY = ["gengar", "tyranitar"]
# parte 2 (POK-54): entram DEPOIS das taças, para os ids da parte 1 (155..185) não mudarem (o id vai para o save)
PARTE2 = ["gligar", "dusclops"]
CHEFES_SHINY_PARTE2 = ["garchomp", "darkrai"]
REDOMAS = ["vazia", "vermelha", "dourada", "azul", "negra"]
TACAS = ["bronze", "prata", "ouro"]
ROSAS = ["vermelha", "dourada", "azul", "negra"]
# redomas e taças dividem paletas (só 4 slots de NPC por mapa): a vazia usa a paleta A, sem pixel de rosa
PALETA_DA_REDOMA = {"vazia": "redomas_a", "vermelha": "redomas_a", "dourada": "redomas_a",
                    "azul": "redomas_b", "negra": "redomas_b"}
# conjuntos de gráficos que aparecem juntos num mapa: cada paleta distinta deles cai num slot diferente
GRUPOS = {
    "sala_do_dom": ["gengar_shiny", "machamp"],
    "sala_do_cobrador": ["tyranitar_shiny", "rhydon"],
    "sala_de_trofeus": ["redomas_a", "redomas_b", "tacas"],
    "sala_do_mercenario": ["garchomp_shiny", "gligar"],
    "sala_do_pesadelo": ["darkrai_shiny", "dusclops"],
    "porta_policia": ["oficial_jenny", "policia_growlithe", "policia_arcanine", "npc_policia"],
}
# parte 2, o fechamento (POK-54): a polícia na porta da Rota 23, depois do 190 (os ids do save só crescem no fim)
POLICIA = ["growlithe", "arcanine"]
JENNY = "oficial_jenny"
SLOTS = ["PALSLOT_NPC_1", "PALSLOT_NPC_2", "PALSLOT_NPC_3", "PALSLOT_NPC_4"]
GRUPOS_TARDIOS = ["porta_policia"]   # o que veio depois da parte 1: distribuído por último (os slots antigos não mudam)
# paletas que não são nossas mas dividem o mapa: o policial (OBJ_EVENT_GFX_POLICEMAN) usa a azul de NPC no slot 1
RESERVADAS = {"npc_policia": "PALSLOT_NPC_1"}

# ---------- cores ----------
C = {
    ".": None,
    "K": (16, 16, 24), "D": (44, 44, 56), "M": (78, 78, 96), "L": (120, 120, 140),
    "R": (208, 32, 40), "r": (128, 16, 28),
    "G": (40, 120, 48), "g": (24, 72, 32), "H": (96, 176, 80),
    "c": (176, 224, 240), "B": (232, 248, 255),
    "Y": (248, 216, 64), "y": (184, 144, 32),
    "w": (112, 64, 32), "v": (72, 40, 20), "V": (152, 96, 48),
}
ROSA_CORES = {  # 4 tons por rosa: contorno, corpo escuro, corpo, brilho
    "vermelha": [(64, 8, 16), (152, 16, 32), (216, 48, 56), (248, 128, 120)],
    "dourada": [(96, 64, 8), (184, 136, 24), (232, 192, 48), (255, 240, 160)],
    "azul": [(16, 24, 72), (32, 72, 168), (72, 128, 224), (168, 208, 255)],
    "negra": [(8, 8, 12), (32, 24, 40), (64, 48, 80), (128, 96, 152)],
}

CHAPEU = [
    "....KKKKKK....",
    "...KDMLLMDK...",
    "...KDMMDMDK...",
    "...KDDDDDDK...",
    "...KRRRRRRK...",
    ".KKKrrrrrrKKK.",
    "KDDDDDDDDDDDDK",
    ".KKKKKKKKKKKK.",
]

ROSA = [
    "........................",
    "........................",
    ".........1111...........",
    ".......11222211.........",
    "......1223332221........",
    ".....122344332221.......",
    ".....123444433321.......",
    ".....1234422343321......",
    ".....1233212333221......",
    "......122333332221......",
    "......11222222211.......",
    "........111111.gg.......",
    "..........gg..gHg.......",
    "..........gG..gHGg......",
    "...gg.....gG...gGg......",
    "..gHHg....gG....gg......",
    "..gHGGgg..gG............",
    "...ggGGgggG.............",
    ".....ggGgg..............",
    "..........gG............",
    "..........gG............",
    "..........gG............",
    "...........g............",
    "........................",
]

REDOMA = [
    "...........KKKKKKKKKK...........",
    ".........KKccccccccccKK.........",
    "........KccBB.........cK........",
    ".......KcBB............cK.......",
    "......KcBB..............cK......",
    "......KcB...............cK......",
    ".....KcB.................cK.....",
    ".....KcB.................cK.....",
    ".....KcB.................cK.....",
    ".....KcB.................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    ".....Kc..................cK.....",
    "...KKKKKKKKKKKKKKKKKKKKKKKKKK...",
    "...KYYYYYYYYYYYYYYYYYYYYYYYYK...",
    "...KyyyyyyyyyyyyyyyyyyyyyyyyK...",
    "....KKKKKKKKKKKKKKKKKKKKKKKK....",
    ".....KwwwwwwwwwwwwwwwwwwwwK.....",
    ".....KwwwwwwwwwwwwwwwwwwwwK.....",
    ".....KwwwwwwwwwwwwwwwwwwwwK.....",
    ".....KwwwwwwwwwwwwwwwwwwwwK.....",
    ".....KvvvvvvvvvvvvvvvvvvvvK.....",
    "....KKKKKKKKKKKKKKKKKKKKKKKK....",
    "....KYYYYYYYYYYYYYYYYYYYYYYK....",
    "....KKKKKKKKKKKKKKKKKKKKKKKK....",
]
DOMO_ROSA_X, DOMO_ROSA_Y = 4, 0

# Taça 16x32: a (escuro), b (médio), c (claro) = os três tons do metal; w/v/V = madeira do pedestal
TACA = [
    "................",
    "................",
    "................",
    "................",
    "..KKKKKKKKKKKK..",
    ".KcccbbbbbbbaaK.",
    "KKcccbbbbbbbaaKK",
    "KcKccbbbbbbbaKcK",
    "KcKccbbbbbbbaKcK",
    "KcKcbbbbbbbbaKcK",
    ".KKKcbbbbbbbaKK.",
    "...KcbbbbbbbaK..",
    "...KKcbbbbbaKK..",
    "....KKcbbbaKK...",
    ".....KKbbaKK....",
    "......KbbaK.....",
    "......KbbaK.....",
    ".....KcbbaaK....",
    "....KccbbbaaK...",
    "....KKKKKKKKK...",
    "...KKKKKKKKKK...",
    "...KVVVVVVVVK...",
    "...KwwwwwwwwK...",
    "...KKKKKKKKKK...",
    "....KwwwwwwK....",
    "....KwwbbbwK....",
    "....KwwcccwK....",
    "....KwwwwwwK....",
    "...KKKKKKKKKK...",
    "..KVVVVVVVVVVK..",
    "..KwwwwwwwwwwK..",
    "..KKKKKKKKKKKK..",
]
METAL = {  # tons (escuro, médio, claro) de cada taça
    "bronze": [(96, 52, 24), (168, 104, 48), (232, 160, 96)],
    "prata": [(96, 104, 128), (168, 176, 200), (240, 244, 252)],
    "ouro": [(160, 112, 24), (232, 184, 40), (255, 240, 128)],
}
# Paleta única das três taças: K, madeira (w, v, V), e os 3 tons de cada metal
TACAS_PALETA = [("K", C["K"]), ("w", C["w"]), ("v", C["v"]), ("V", C["V"])] + [
    (f"{m}{i}", METAL[m][i]) for m in TACAS for i in range(3)]


def q(cor):
    """Cor de 5 bits por canal (o que o GBA guarda)."""
    return tuple(v & 0xF8 for v in cor)


def jasc(caminho):
    ls = Path(caminho).read_text().split()
    n = int(ls[2])
    v = list(map(int, ls[3:3 + n * 3]))
    return [tuple(v[i:i + 3]) for i in range(0, n * 3, 3)]


def texto_pal(pal):
    assert len(pal) == 16
    return "\r\n".join(["JASC-PAL", "0100", "16"] + [f"{r} {g} {b}" for r, g, b in pal]) + "\r\n"


def pal_completa(cores, indice0=COR_INDICE_0):
    assert len(cores) <= MAX_CORES, len(cores)
    return [indice0] + list(cores) + [(0, 0, 0)] * (MAX_CORES - len(cores))


def png_indexado(tam, indices, pal):
    im = Image.new("P", tam)
    im.putpalette([c for cor in pal for c in cor])
    im.putdata(indices)
    return im


def arte(linhas, mapa):
    """Linhas de letras -> {(x, y): rgb} (letras sem cor no mapa ficam transparentes)."""
    pix = {}
    for y, l in enumerate(linhas):
        for x, ch in enumerate(l):
            cor = mapa.get(ch)
            if cor:
                pix[(x, y)] = cor
    return pix


# ---------- sprites do mapa com chapéu ----------
def carregar_ajustes():
    return {k: tuple(v) for k, v in json.loads(AJUSTES.read_text(encoding="utf-8")).items()}


def topo_cabeca(px):
    """Linha mais alta com conteúdo e o centro horizontal das 5 linhas de cima (a cabeça)."""
    ys = sorted({y for (_, y) in px})
    y0 = ys[0]
    xs = [x for (x, y) in px if y0 <= y < y0 + 5]
    return y0, (min(xs) + max(xs)) // 2


def reduzir_cores(contagem, protegidas):
    """Junta as cores mais parecidas (custo = usos x distância²) até sobrarem MAX_CORES; devolve {cor: cor nova}."""
    troca = {c: c for c in contagem}
    uso = dict(contagem)
    while len(uso) > MAX_CORES:
        melhor = None
        for a in uso:
            for b in uso:
                if a == b:
                    continue
                peso = uso[a] * (4 if a in protegidas else 1)
                custo = peso * sum((x - y) ** 2 for x, y in zip(a, b))
                if melhor is None or custo < melhor[0]:
                    melhor = (custo, a, b)
        _, a, b = melhor
        uso[b] += uso.pop(a)
        for k, v in troca.items():
            if v == a:
                troca[k] = b
    return troca


def sprite_com_chapeu(nome, shiny, ajuste):
    """(PNG indexado 32x40, paleta de 16 cores) do quadro 0 do seguidor com o chapéu na cabeça."""
    folha = Image.open(REPO / SEG_PICS / f"{nome}.png")
    pal = jasc(REPO / SEG_PALS / f"{nome}{'_shiny' if shiny else ''}.pal")
    ind = list(folha.crop((0, 0, 32, 32)).tobytes())
    corpo = {(i % 32, i // 32): q(pal[v]) for i, v in enumerate(ind) if v}
    ordem = {}  # cor -> menor índice original (mantém a ordem da paleta do seguidor)
    for i, v in enumerate(ind):
        if v:
            ordem.setdefault(q(pal[v]), v)
    y, cx = topo_cabeca(corpo)
    dx, dy = ajuste.get(nome, DAJUSTE_PADRAO)
    tela = {(x, yy + DESLOCAMENTO_Y): c for (x, yy), c in corpo.items()}
    chapeu = arte(CHAPEU, {k: q(v) for k, v in C.items() if v})
    cor_do_chapeu = set(chapeu.values())
    hx, hy = cx - 7 + dx, y + DESLOCAMENTO_Y - 8 + dy
    for (x, yy), c in chapeu.items():
        tela[(hx + x, hy + yy)] = c
    xs, ys = [p[0] for p in tela], [p[1] for p in tela]
    if min(xs) < 0 or max(xs) >= LARGURA or min(ys) < 0 or max(ys) >= ALTURA:
        raise SystemExit(f"{nome}: o chapéu sai da tela 32x40 ({min(xs)},{min(ys)})-({max(xs)},{max(ys)})")
    contagem = {}
    for c in tela.values():
        contagem[c] = contagem.get(c, 0) + 1
    troca = reduzir_cores(contagem, cor_do_chapeu)
    tela = {p: troca[c] for p, c in tela.items()}
    cores = []
    for c in sorted({c for c in tela.values() if c in ordem}, key=lambda c: ordem[c]):
        cores.append(c)
    cores += sorted({c for c in tela.values() if c not in ordem}, key=lambda c: sum(c))
    indice = {c: i + 1 for i, c in enumerate(cores)}
    dados = [indice[tela[(x, yy)]] if (x, yy) in tela else 0 for yy in range(ALTURA) for x in range(LARGURA)]
    return png_indexado((LARGURA, ALTURA), dados, pal_completa(cores)), pal_completa(cores)


# ---------- rosas ----------
def rosa_png(cor):
    t = ROSA_CORES[cor]
    mapa = dict(C)
    mapa.update({"1": t[0], "2": t[1], "3": t[2], "4": t[3]})
    pix = arte(ROSA, mapa)
    cores = [q(c) for c in t] + [q(C["g"]), q(C["G"]), q(C["H"])]
    cores = list(dict.fromkeys(cores))
    indice = {c: i + 1 for i, c in enumerate(cores)}
    dados = [indice[q(pix[(x, y)])] if (x, y) in pix else 0 for y in range(24) for x in range(24)]
    pal = [(180, 180, 180)] + cores + [(0, 0, 0)] * (15 - len(cores))
    return png_indexado((24, 24), dados, pal), pal


# ---------- redomas ----------
def rosa_do_domo():
    """A rosa da prévia sem 3 linhas do caule e com 3 tons (2 e 3 viram um só): o domo tem 32 linhas e a paleta divide
    duas rosas."""
    linhas = ROSA[:19] + ROSA[22:]
    return linhas


def domo_pixels(cor):
    """{(x, y): letra} da redoma de 32x32 (vidro, base, rosa com os tons d, m, l)."""
    pix = {}
    for y, l in enumerate(REDOMA):
        for x, ch in enumerate(l):
            if ch != ".":
                pix[(x, y)] = "w" if ch == "V" else ch
    if cor:
        mapa = {"1": f"{cor}d", "2": f"{cor}m", "3": f"{cor}m", "4": f"{cor}l", "f": "g", "g": "g", "G": "G", "H": "G"}
        for y, l in enumerate(rosa_do_domo()):
            for x, ch in enumerate(l):
                if ch in mapa:
                    pix[(x + DOMO_ROSA_X, y + DOMO_ROSA_Y)] = mapa[ch]
    return pix


def paleta_das_redomas(cores_das_rosas):
    base = [("K", C["K"]), ("c", C["c"]), ("B", C["B"]), ("Y", C["Y"]), ("y", C["y"]), ("w", C["w"]), ("v", C["v"]),
            ("g", C["g"]), ("G", C["G"])]
    for cor in cores_das_rosas:
        t = ROSA_CORES[cor]
        base += [(f"{cor}d", t[0]), (f"{cor}m", t[2]), (f"{cor}l", t[3])]
    return base


PALETAS_DAS_REDOMAS = {"redomas_a": ["vermelha", "dourada"], "redomas_b": ["azul", "negra"]}


def png_com_nomes(tam, pix, paleta_nomeada):
    nomes = [n for n, _ in paleta_nomeada]
    cores = [q(c) for _, c in paleta_nomeada]
    assert len(set(cores)) == len(cores), "duas cores iguais na mesma paleta"
    dados = [0] * (tam[0] * tam[1])
    for (x, y), n in pix.items():
        dados[y * tam[0] + x] = nomes.index(n) + 1
    pal = pal_completa(cores)
    return png_indexado(tam, dados, pal), pal


def redoma_png(cor):
    grupo = PALETA_DA_REDOMA[cor]
    pn = paleta_das_redomas(PALETAS_DAS_REDOMAS[grupo])
    return png_com_nomes((32, 32), domo_pixels(None if cor == "vazia" else cor), pn)


def taca_png(material):
    mapa = {"K": "K", "w": "w", "v": "v", "V": "V", "a": f"{material}0", "b": f"{material}1", "c": f"{material}2"}
    pix = {(x, y): mapa[ch] for y, l in enumerate(TACA) for x, ch in enumerate(l) if ch != "."}
    return png_com_nomes((16, 32), pix, TACAS_PALETA)


# ---------- a polícia da porta (parte 2) ----------
TEAL = [(136, 224, 208), (64, 176, 176), (24, 104, 112)]   # o cabelo da Jenny: claro, médio, escuro
PICNICKER = Path("graphics/object_events/pics/people/picnicker.png")
NPC_AZUL = Path("graphics/object_events/palettes/npc_blue.pal")
# índice do Picnicker -> índice da Jenny: o cabelo laranja (5-7) vai para os 3 tons de TEAL (11-13 da paleta dela) e o
# que era pele nos 11-13 da paleta original do Picnicker volta para a pele (1, 2, 4); o resto fica igual
JENNY_INDICES = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 11, 6: 12, 7: 13, 8: 8, 9: 9, 10: 10, 11: 1, 12: 2, 13: 4, 14: 14, 15: 15}
JENNY_QUADRO = 16                 # largura de cada quadro
# O quepe do Picnicker é uma boina com faixa clara; o da polícia é escuro, com o distintivo dourado (índices 5 e 6 da
# paleta azul de NPC: ouro claro e ouro médio) e a aba escura que avança. Linhas de baixo para cima, por quadro:
# de frente (0, 3 e 4: linha do emblema E; 9, com a mão levantada, tem o quepe uma linha acima) e de lado (2, 7 e 8:
# topo S do quepe). As costas (1, 5 e 6) não têm emblema e ficam como estão.
QUEPE_DE_FRENTE = {0: 16, 3: 17, 4: 17, 9: 14}
QUEPE_DE_LADO = {2: 12, 7: 13, 8: 13}
OURO_CLARO, OURO_MEDIO, ESCURO, COROA = 5, 6, 10, 9


def retoques():
    """{(quadro, x, y): índice} do quepe da Jenny (a aba que lê como quepe de polícia, o distintivo no meio)."""
    r = {}
    for quadro, e in QUEPE_DE_FRENTE.items():
        for x in range(3, 13):
            r[(quadro, x, e)] = COROA                 # sem o emblema branco da boina
            r[(quadro, x, e + 1)] = ESCURO            # faixa escura de lado a lado
        for x in range(5, 11):
            r[(quadro, x, e + 2)] = ESCURO            # a faixa clara vira aba escura
        for x in (7, 8):
            r[(quadro, x, e + 1)] = OURO_CLARO        # o distintivo, 2x2, como o do policial
            r[(quadro, x, e + 2)] = OURO_MEDIO
    for quadro, s in QUEPE_DE_LADO.items():
        r[(quadro, 3, s + 3)] = OURO_CLARO            # o emblema branco vira distintivo
        r[(quadro, 3, s + 4)] = OURO_MEDIO
        r[(quadro, 2, s + 5)] = ESCURO                # a aba que avança, escura
        r[(quadro, 3, s + 6)] = ESCURO
        r[(quadro, 4, s + 6)] = ESCURO
    return r


def jenny_png():
    """(PNG indexado 160x32, paleta de 16 cores) da Oficial Jenny: a Picnicker com a paleta azul de NPC (a do policial),
    o cabelo azul-petróleo (paleta própria, porque esse tom não existe na azul de NPC) e o quepe de polícia."""
    pic = Image.open(REPO / PICNICKER)
    pal = jasc(REPO / NPC_AZUL)
    pal[11], pal[12], pal[13] = TEAL
    pal = [pal[0]] + [q(c) for c in pal[1:]]
    dados = [JENNY_INDICES[v] for v in pic.tobytes()]
    largura = pic.width
    for (quadro, x, y), indice in retoques().items():
        dados[y * largura + quadro * JENNY_QUADRO + x] = indice
    return png_indexado(pic.size, dados, pal), pal


def policia_png(especie):
    """(PNG indexado 32x32, paleta) do quadro 0 do seguidor (parado, de frente), sem chapéu."""
    folha = Image.open(REPO / SEG_PICS / f"{especie}.png")
    pal = jasc(REPO / SEG_PALS / f"{especie}.pal")
    pal = [pal[0]] + [q(c) for c in pal[1:]]
    return png_indexado((32, 32), list(folha.crop((0, 0, 32, 32)).tobytes()), pal), pal


# ---------- lista de gráficos do mapa ----------
def lista_gfx():
    """[(nome do arquivo, id C em maiúsculas, nome C em CamelCase, paleta, largura, altura)] na ordem dos ids."""
    def camel(s):
        return "".join(p.capitalize() for p in s.split("_"))

    itens = []
    for e in ESPECIES:
        itens.append((e, e.upper(), camel(e), e, "sprite"))
    for e in CHEFES_SHINY:
        n = f"{e}_shiny"
        itens.append((n, n.upper(), camel(n), n, "sprite"))
    for r in REDOMAS:
        itens.append((f"redoma_{r}", f"REDOMA_{r.upper()}", f"Redoma{camel(r)}", PALETA_DA_REDOMA[r], "redoma"))
    for t in TACAS:
        itens.append((f"taca_{t}", f"TACA_{t.upper()}", f"Taca{camel(t)}", "tacas", "taca"))
    for e in PARTE2:
        itens.append((e, e.upper(), camel(e), e, "sprite"))
    for e in CHEFES_SHINY_PARTE2:
        n = f"{e}_shiny"
        itens.append((n, n.upper(), camel(n), n, "sprite"))
    for e in POLICIA:
        itens.append((f"policia_{e}", f"POLICIA_{e.upper()}", f"Policia{camel(e)}", f"policia_{e}", "policia"))
    itens.append((JENNY, JENNY.upper(), camel(JENNY), JENNY, "npc"))
    resultado = []
    for i, (arq, uid, cam, pal, tipo) in enumerate(itens):
        gid = f"OBJ_EVENT_GFX_{'FAMILIA_' if tipo == 'sprite' else ''}{uid}"
        resultado.append({"arquivo": arq, "id": gid, "valor": PRIMEIRO_GFX + i, "camel": cam, "paleta": pal,
                          "tipo": tipo})
    return resultado


def paletas_distintas(gfx):
    ordem = []
    for g in gfx:
        if g["paleta"] not in ordem:
            ordem.append(g["paleta"])
    return ordem


def distribuir_slots(gfx):
    """slot de cada paleta: grupos (cliques) com cores diferentes; o resto, no slot menos usado. Os grupos de
    GRUPOS_TARDIOS entram por último: os slots que já estavam em uso não mudam quando um grupo novo chega."""
    paletas = paletas_distintas(gfx)
    tardias = {p for k in GRUPOS_TARDIOS for p in GRUPOS[k]}
    slot = dict(RESERVADAS)
    uso = {s: 0 for s in SLOTS}

    def escolher(p):
        tomados = {slot[o] for m in GRUPOS.values() if p in m for o in m if o in slot}
        livre = [s for s in SLOTS if s not in tomados]
        assert livre, f"grupo com mais de {len(SLOTS)} paletas: {p}"
        slot[p] = min(livre, key=lambda s: (uso[s], SLOTS.index(s)))
        uso[slot[p]] += 1

    for nome, membros in GRUPOS.items():
        if nome in GRUPOS_TARDIOS:
            continue
        for p in membros:
            assert p in paletas or p in RESERVADAS, p
            if p not in slot:
                escolher(p)
    for p in paletas:
        if p not in slot and p not in tardias:
            slot[p] = min(SLOTS, key=lambda s: (uso[s], SLOTS.index(s)))
            uso[slot[p]] += 1
    for nome in GRUPOS_TARDIOS:
        for p in GRUPOS[nome]:
            assert p in paletas or p in RESERVADAS, p
            if p not in slot:
                escolher(p)
    return slot


def texto_slots(gfx, slot):
    dados = {
        "_comentario": "Gerado por tools/familia_sombra/gerar.py. `slots`: slot de paleta de cada gráfico do mapa. Dois "
                       "gráficos com paletas diferentes não podem dividir o slot no mesmo mapa (as cores saem trocadas). "
                       "Redomas e taças dividem paletas (`paleta`), por isso dividem o slot. `grupos`: o que aparece junto.",
        "slots": {g["id"]: slot[g["paleta"]] for g in gfx},
        "paletas": {g["id"]: g["paleta"] for g in gfx},
        "grupos": {k: [g["id"] for g in gfx if g["paleta"] in v or g["arquivo"] in v] for k, v in GRUPOS.items()},
    }
    return json.dumps(dados, indent=2, ensure_ascii=False) + "\n"


# ---------- C ----------
def tag_de(paleta, paletas):
    return PRIMEIRA_TAG + paletas.index(paleta)


def nome_tag(paleta):
    return f"OBJ_EVENT_PAL_TAG_FAMILIA_{paleta.upper()}"


def texto_c_gfx(gfx, slot):
    paletas = paletas_distintas(gfx)
    L = ["// Gerado por tools/familia_sombra/gerar.py; não editar à mão.",
         "// Gráficos do mapa da Família Sombra (POK-51): sprites com chapéu, redomas e taças. Um quadro só, repetido nas",
         "// posições que a sAnimTable_Standard pede. Cada paleta tem a própria tag e é gravada no slot PALSLOT_NPC_n do",
         "// gráfico quando o objeto aparece (event_object_movement.c: LoadFamiliaObjectPalette).",
         ""]
    L.append(f"#define OBJ_EVENT_PAL_TAG_FAMILIA_FIRST 0x{PRIMEIRA_TAG:04X}")
    for p in paletas:
        L.append(f"#define {nome_tag(p)} 0x{tag_de(p, paletas):04X}")
    L.append("")
    for p in paletas:
        L.append(f'static const u16 gObjectEventPal_Familia_{p}[] = INCBIN_U16("graphics/object_events/palettes/familia/{p}.gbapal");')
    L.append("")
    dim = {"sprite": (4, 5, 32, 40, 640, "32x40", "SHADOW_SIZE_M"),
           "redoma": (4, 4, 32, 32, 512, "32x32", "SHADOW_SIZE_S"),
           "taca": (2, 4, 16, 32, 256, "16x32", "SHADOW_SIZE_S"),
           "policia": (4, 4, 32, 32, 512, "32x32", "SHADOW_SIZE_M"),
           "npc": (2, 4, 16, 32, 256, "16x32", "SHADOW_SIZE_M")}
    for g in gfx:
        w, h, pw, ph, tam, sufixo, sombra = dim[g["tipo"]]
        c = g["camel"]
        L.append(f'static const u16 sFamiliaPic_{c}[] = INCBIN_U16("graphics/object_events/pics/familia/{g["arquivo"]}.4bpp");')
        L.append(f"static const struct SpriteFrameImage sFamiliaPicTable_{c}[] = {{")
        # o NPC tem os 10 quadros de verdade (a Jenny anda e olha para os lados); os outros, 1 quadro repetido
        quadros = range(QUADROS_NA_TABELA) if g["tipo"] == "npc" else [0] * QUADROS_NA_TABELA
        L += [f"    overworld_frame(sFamiliaPic_{c}, {w}, {h}, {i})," for i in quadros]
        L.append("};")
        oam = "32x32" if sufixo == "32x40" else sufixo
        tabelas = "gObjectEventSpriteOamTables_" + sufixo
        L += [
            f"const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Familia_{c} = {{",
            "    .tileTag = TAG_NONE,",
            f"    .paletteTag = {nome_tag(g['paleta'])},",
            "    .reflectionPaletteTag = OBJ_EVENT_PAL_TAG_NONE,",
            f"    .size = {tam},",
            f"    .width = {pw},",
            f"    .height = {ph},",
            f"    .paletteSlot = {slot[g['paleta']]},",
            f"    .shadowSize = {sombra},",
            "    .inanimate = FALSE,",
            "    .disableReflectionPaletteLoad = FALSE,",
            f"    .tracks = {'TRACKS_FOOT' if g['tipo'] == 'npc' else 'TRACKS_NONE'},",
            f"    .oam = &gObjectEventBaseOam_{oam},",
            f"    .subspriteTables = {tabelas},",
            "    .anims = sAnimTable_Standard,",
            f"    .images = sFamiliaPicTable_{c},",
            "    .affineAnims = gDummySpriteAffineAnimTable,",
            "};",
            "",
        ]
    return "\n".join(L)


def texto_c_extern(gfx):
    return "// Gerado por tools/familia_sombra/gerar.py; não editar à mão.\n" + "".join(
        f"const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Familia_{g['camel']};\n" for g in gfx)


def texto_c_ponteiros(gfx):
    return "// Gerado por tools/familia_sombra/gerar.py; não editar à mão.\n" + "".join(
        f"    [{g['id']}] = &gObjectEventGraphicsInfo_Familia_{g['camel']},\n" for g in gfx)


def texto_c_paletas(gfx):
    paletas = paletas_distintas(gfx)
    return "// Gerado por tools/familia_sombra/gerar.py; não editar à mão.\n" + "".join(
        f"    {{gObjectEventPal_Familia_{p}, {nome_tag(p)}}},\n" for p in paletas)


MARCA_INI = "// <familia-sombra gfx: gerado por tools/familia_sombra/gerar.py>"
MARCA_FIM = "// </familia-sombra gfx>"


def bloco_constantes(gfx):
    L = [MARCA_INI,
         "// POK-51/POK-54: sprites do mapa da Família Sombra (chapéu), redomas e taças da sala de troféus"]
    L += [f"#define {g['id']} {g['valor']}" for g in gfx]
    L += [MARCA_FIM]
    return "\n".join(L)


def constantes_atualizadas(texto, gfx):
    """O bloco fica entre os marcadores. O NUM_OBJ_EVENT_GFX fica fora dele, escrito à mão, porque há gráficos depois
    da família (POK-28: OBJ_EVENT_GFX_SUDOWOODO = 193). Um gráfico novo da família pegaria o id de um deles: o
    gerador recusa, e o novo vai à mão para depois do último (o id vai para o save, nenhum antigo muda)."""
    bloco = bloco_constantes(gfx)
    if MARCA_INI in texto:
        novo = re.sub(re.escape(MARCA_INI) + r".*?" + re.escape(MARCA_FIM), lambda _: bloco, texto, flags=re.S)
    else:
        novo, n = re.subn(r"#define NUM_OBJ_EVENT_GFX\s+\d+", lambda m: f"{bloco}\n\n{m.group(0)}", texto, count=1)
        if n != 1:
            raise SystemExit("NUM_OBJ_EVENT_GFX não encontrado em event_objects.h")
    ids = [int(v) for v in re.findall(r"^#define OBJ_EVENT_GFX_\w+\s+(\d+)\b", novo, re.M) if int(v) < 240]
    repetidos = sorted({v for v in ids if ids.count(v) > 1})
    if repetidos:
        raise SystemExit(f"ids de gráfico repetidos em event_objects.h: {repetidos}")
    # NUM fica fora do bloco, à mão: um id novo acima dele sairia do alcance da tabela de gráficos
    num = re.search(r"^#define NUM_OBJ_EVENT_GFX\s+(\d+)\b", novo, re.M)
    if not num or int(num.group(1)) <= max(ids):
        raise SystemExit(f"NUM_OBJ_EVENT_GFX ({num and num.group(1)}) tem de ser maior que o maior id de gráfico "
                         f"({max(ids)}) em event_objects.h")
    return novo


# ---------- geração ----------
def gerar(saida):
    """Grava tudo sob `saida`; devolve os caminhos relativos gravados."""
    gravados = []

    def gravar_bytes(rel, dados):
        (saida / rel).parent.mkdir(parents=True, exist_ok=True)
        (saida / rel).write_bytes(dados)
        gravados.append(rel)

    def gravar_png(rel, im):
        (saida / rel).parent.mkdir(parents=True, exist_ok=True)
        im.save(saida / rel, bits=4)
        gravados.append(rel)

    def gravar_pal(rel, pal):
        gravar_bytes(rel, texto_pal(pal).encode("ascii"))

    ajuste = carregar_ajustes()
    gfx = lista_gfx()
    slot = distribuir_slots(gfx)
    for g in gfx:
        a = g["arquivo"]
        if g["tipo"] == "sprite":
            base, shiny = (a[:-6], True) if a.endswith("_shiny") else (a, False)
            im, pal = sprite_com_chapeu(base, shiny, ajuste)
            gravar_png(PICS / f"{a}.png", im)
            gravar_pal(PALS / f"{a}.pal", pal)
        elif g["tipo"] == "redoma":
            im, pal = redoma_png(a[len("redoma_"):])
            gravar_png(PICS / f"{a}.png", im)
            if not any(str(p).endswith(f"{g['paleta']}.pal") for p in gravados):
                gravar_pal(PALS / f"{g['paleta']}.pal", pal)
        elif g["tipo"] == "policia":
            im, pal = policia_png(a[len("policia_"):])
            gravar_png(PICS / f"{a}.png", im)
            gravar_pal(PALS / f"{g['paleta']}.pal", pal)
        elif g["tipo"] == "npc":
            im, pal = jenny_png()
            gravar_png(PICS / f"{a}.png", im)
            gravar_pal(PALS / f"{g['paleta']}.pal", pal)
        else:
            im, pal = taca_png(a[len("taca_"):])
            gravar_png(PICS / f"{a}.png", im)
            if not any(str(p).endswith("tacas.pal") for p in gravados):
                gravar_pal(PALS / "tacas.pal", pal)
    for r in ROSAS:
        im, pal = rosa_png(r)
        gravar_png(ICONES / f"rosa_{r}.png", im)
        gravar_pal(ICONES_PALS / f"rosa_{r}.pal", pal)
    gravar_bytes(SLOTS_REL, texto_slots(gfx, slot).encode("utf-8"))
    gravar_bytes(C_GFX, texto_c_gfx(gfx, slot).encode("utf-8"))
    gravar_bytes(C_EXTERN, texto_c_extern(gfx).encode("utf-8"))
    gravar_bytes(C_PONTEIROS, texto_c_ponteiros(gfx).encode("utf-8"))
    gravar_bytes(C_PALETAS, texto_c_paletas(gfx).encode("utf-8"))
    consts = (REPO / CONSTANTES_REL).read_text(encoding="utf-8")
    gravar_bytes(CONSTANTES_REL, constantes_atualizadas(consts, gfx).encode("utf-8"))
    return gravados


def mesma_imagem(a, b):
    ia, ib = Image.open(a), Image.open(b)
    return (ia.size, ia.mode, ia.tobytes(), ia.getpalette()[:48]) == (ib.size, ib.mode, ib.tobytes(), ib.getpalette()[:48])


def conferir():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / CONSTANTES_REL).parent.mkdir(parents=True)
        (tmp / CONSTANTES_REL).write_bytes((REPO / CONSTANTES_REL).read_bytes())
        gravados = gerar(tmp)
        erros = []
        for rel in gravados:
            atual = REPO / rel
            if not atual.is_file():
                erros.append(f"falta {rel}")
            elif rel.suffix == ".png":
                if not mesma_imagem(atual, tmp / rel):
                    erros.append(f"diverge {rel}")
            elif atual.read_bytes() != (tmp / rel).read_bytes():
                erros.append(f"diverge {rel}")
    return erros


# ---------- folha de conferência ----------
def folha(destino):
    from PIL import ImageFont

    S = 4
    ajuste = carregar_ajustes()
    fundo = (112, 200, 120)
    tela = Image.new("RGB", (1500, 1700), (245, 243, 238))
    d = ImageDraw.Draw(tela)
    try:
        fonte = ImageFont.truetype("DejaVuSans.ttf", 15)
    except OSError:
        fonte = ImageFont.load_default()

    def cola(im, x, y, fd=fundo):
        im = im.convert("RGBA")
        big = im.resize((im.width * S, im.height * S), Image.NEAREST)
        bg = Image.new("RGBA", big.size, fd + (255,))
        bg.alpha_composite(big)
        tela.paste(bg.convert("RGB"), (x, y))
        return big.size

    def indexado_rgba(im, pal):
        px = list(im.tobytes())
        out = Image.new("RGBA", im.size)
        out.putdata([(0, 0, 0, 0) if v == 0 else pal[v] + (255,) for v in px])
        return out

    y = 10
    d.text((10, y), "Sprites do mapa: sem chapéu (em cima) e com chapéu (embaixo), 4x", fill=(30, 30, 30), font=fonte)
    y += 24
    nomes = ([(e, False) for e in ESPECIES] + [(e, True) for e in CHEFES_SHINY]
             + [(e, False) for e in PARTE2] + [(e, True) for e in CHEFES_SHINY_PARTE2])
    x = 10
    linha = 0
    for nome, shiny in nomes:
        im, pal = sprite_com_chapeu(nome, shiny, ajuste)
        seg = jasc(REPO / SEG_PALS / f"{nome}{'_shiny' if shiny else ''}.pal")
        q0 = Image.open(REPO / SEG_PICS / f"{nome}.png").crop((0, 0, 32, 32))
        sem = Image.new("RGBA", (32, 40), (0, 0, 0, 0))
        sem.alpha_composite(indexado_rgba(q0, seg), (0, DESLOCAMENTO_Y))
        cola(sem, x, y)
        cola(indexado_rgba(im, pal), x, y + 170)
        d.text((x, y + 335), nome + (" (shiny)" if shiny else ""), fill=(30, 30, 30), font=fonte)
        x += 140
        if x > 1500 - 140:
            x = 10
            y += 365
            linha += 1
    y += 365
    d.text((10, y), "Rosas (ícones 24x24), redomas 32x32 e taças 16x32", fill=(30, 30, 30), font=fonte)
    y += 24
    x = 10
    for r in ROSAS:
        im, pal = rosa_png(r)
        cola(indexado_rgba(im, pal), x, y, (248, 248, 248))
        d.text((x, y + 100), f"rosa {r}", fill=(30, 30, 30), font=fonte)
        x += 110
    x = 10
    y += 130
    for r in REDOMAS:
        im, pal = redoma_png(r)
        cola(indexado_rgba(im, pal), x, y, (176, 148, 112))
        d.text((x, y + 130), f"redoma {r}", fill=(30, 30, 30), font=fonte)
        x += 150
    for t in TACAS:
        im, pal = taca_png(t)
        cola(indexado_rgba(im, pal), x, y, (176, 148, 112))
        d.text((x, y + 130), f"taça {t}", fill=(30, 30, 30), font=fonte)
        x += 100
    y += 160
    tela.crop((0, 0, 1500, y)).save(destino)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--folha", metavar="PNG")
    args = ap.parse_args()
    if args.folha:
        folha(args.folha)
        print("folha", args.folha)
        return 0
    if args.conferir:
        erros = conferir()
        for e in erros:
            print(e, file=sys.stderr)
        print("familia_sombra: " + ("tudo confere" if not erros else f"{len(erros)} divergência(s)"))
        return 1 if erros else 0
    gravados = gerar(REPO)
    print(f"familia_sombra: {len(gravados)} arquivos gravados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
