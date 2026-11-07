"""O prédio da Família Sombra (POK-51): o exterior na Rota 23, o tileset dos andares e os 6 andares.

    python3 -I tools/familia_sombra/predio.py              # grava tudo no repositório
    python3 -I tools/familia_sombra/predio.py --conferir   # refaz num diretório temporário e compara (sai 1 se divergir)

Entradas (do próprio repositório, nunca as saídas):
    data/tilesets/secondary/pokemon_mansion/*        base dos andares (só os metatiles que os andares usam)
    data/tilesets/secondary/indigo_plateau/*         os primeiros INDIGO_TILES ladrilhos e INDIGO_METATILES metatiles
    data/layouts/Route23/map.bin                     a Rota 23 (só as células do prédio e da calçada mudam)
    graphics/object_events/pics/familia/<chefe>.png (+ palettes/familia/<chefe>.pal)   o sprite com chapéu de cada
                                                     chefe (saída de gerar.py), para o retrato do quadro (QUADROS)

Saídas (versionadas, nada à mão):
    data/tilesets/secondary/familia_sombra/{tiles.png, metatiles.bin, metatile_attributes.bin, palettes/*.pal}
        cópia compacta da Mansão (paletas 7, 8 e 12) + a decoração da sala do Dom (paletas 9, 10 e 11, desenhada
        aqui a partir da prévia aprovada: parede vinho com lambri, cortinas, quadro, tapete, mesa, poltrona, vasos)
    data/tilesets/secondary/indigo_plateau/{tiles.png, metatiles.bin, metatile_attributes.bin, palettes/07.pal}
        o prédio abandonado (paleta 7, livre no Platô Índigo) e a porta trancada (METATILE_IndigoPlateau_FamiliaPorta*)
    data/layouts/Route23/map.bin                     o prédio 4x6 em (2..5, 144..149), porta em (4, 149)
    data/layouts/Route23_FamiliaSombra_<n>F/{map.bin, border.bin}   os 6 andares
    tools/familia_sombra/predio.json                 contagens e posições (lidas pelos testes e pelo C de teste)

Só Pillow e a biblioteca padrão.
"""
import argparse
import filecmp
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
MANSAO = Path("data/tilesets/secondary/pokemon_mansion")
INDIGO = Path("data/tilesets/secondary/indigo_plateau")
FAMILIA = Path("data/tilesets/secondary/familia_sombra")
ROTA23 = Path("data/layouts/Route23/map.bin")
INDIGO_TILES = 247          # ladrilhos originais do Platô Índigo (tileset_rules.mk antes do POK-51)
INDIGO_METATILES = 176      # metatiles originais do Platô Índigo
ROTA23_LARGURA = 24
PRIMARIOS = 640             # NUM_TILES_IN_PRIMARY / NUM_METATILES_IN_PRIMARY
MAX_SECUNDARIO = 384        # 1024 - 640, ladrilhos e metatiles
METATILE_PORTA_GERAL = 0x03D  # METATILE_General_Door (porta animada do tileset primário General)

# Comportamentos e atributos (include/constants/metatile_behaviors.h, src/fieldmap.c: sMetatileAttrMasks)
MB_NORMAL = 0x00
MB_DOWN_LEFT_STAIR_WARP = 0x6F
MB_COUNTER = 0x80
ENCONTRO_TERRA = 1 << 24
CAMADA_COBERTA = 1 << 29

# ---------------------------------------------------------------------------------------------------------------
# Paletas novas
# ---------------------------------------------------------------------------------------------------------------
K = (16, 16, 24)
PAL_PREDIO = [  # Platô Índigo, paleta 7: parede escura, tábuas nas janelas, telhado plano
    (0, 0, 0), K, (40, 36, 44), (56, 52, 64), (72, 68, 80), (96, 92, 104), (32, 32, 40), (64, 64, 72),
    (104, 104, 112), (72, 48, 32), (112, 80, 48), (152, 112, 72), (24, 24, 40), (48, 56, 80), (136, 128, 144),
    (128, 16, 28),
]
PAL_PAREDE = [  # andares, paleta 9: parede vinho, lambri, cortinas, janela
    (0, 0, 0), K, (56, 32, 40), (72, 40, 48), (88, 48, 56), (120, 16, 28), (176, 24, 36), (208, 32, 40),
    (136, 96, 24), (200, 160, 48), (248, 216, 64), (72, 40, 20), (84, 54, 36), (24, 24, 48), (64, 72, 112),
]
PAL_PISO = [  # paleta 10: piso de madeira escura, tapete, mesa, papéis, poltrona
    (0, 0, 0), K, (52, 32, 22), (64, 40, 28), (40, 24, 18), (72, 40, 20), (112, 64, 32), (152, 96, 48),
    (232, 232, 216), (168, 168, 152), (136, 96, 24), (200, 160, 48), (248, 216, 64), (120, 16, 28),
    (152, 24, 36), (208, 32, 40),
]
CINZA_MEDIO, CINZA_CLARO = (112, 112, 112), (200, 200, 200)
PAL_ROSAS = [  # paleta 11: vasos com rosas e o quadro do chefe (os 2 cinzas do retrato, com o K, nos índices 14-15)
    (0, 0, 0), K, (24, 72, 32), (40, 120, 48), (120, 16, 28), (208, 32, 40), (136, 96, 24), (200, 160, 48),
    (248, 216, 64), (52, 32, 22), (64, 40, 28), (84, 54, 36), (72, 40, 48), (56, 32, 40), CINZA_MEDIO,
    CINZA_CLARO,
]
TONS_DO_RETRATO = (K, CINZA_MEDIO, CINZA_CLARO)   # o retrato só usa estes (preto e branco de foto antiga)
PALETAS_DECORACAO = {9: PAL_PAREDE, 10: PAL_PISO, 11: PAL_ROSAS}
# Metatiles da decoração com comportamento próprio (o resto é MB_NORMAL): o patamar da escada da sala do Dom é o warp
# A coluna do meio da mesa (2 de fundo) é balcão: de frente para a mesa, o A alcança o chefe na poltrona atrás dela
# (src/field_control_avatar.c olha 2 tiles além quando os 2 são balcão). Por isso o livro-caixa fica na coluna da esquerda.
ATRIBUTOS_DECORACAO = {("d", "escada_2_0"): MB_DOWN_LEFT_STAIR_WARP,
                       ("d", "mesa_1_0"): MB_COUNTER, ("d", "mesa_1_1"): MB_COUNTER}


def _5bits(cor):
    return tuple(c & 0xF8 for c in cor)


def _jasc(cores):
    cores = [_5bits(c) for c in cores] + [(0, 0, 0)] * (16 - len(cores))
    return "JASC-PAL\r\n0100\r\n16\r\n" + "".join(f"{r} {g} {b}\r\n" for r, g, b in cores)


# ---------------------------------------------------------------------------------------------------------------
# Ladrilhos
# ---------------------------------------------------------------------------------------------------------------
def ler_ladrilhos(png):
    im = Image.open(png)
    w, h = im.size
    px = im.load()
    return [tuple(px[tx * 8 + x, ty * 8 + y] & 15 for y in range(8) for x in range(8))
            for ty in range(h // 8) for tx in range(w // 8)]


def gravar_ladrilhos(png, ladrilhos, paleta_png):
    linhas = (len(ladrilhos) + 15) // 16
    im = Image.new("P", (128, linhas * 8), 0)
    im.putpalette(paleta_png)
    px = im.load()
    for i, t in enumerate(ladrilhos):
        tx, ty = i % 16, i // 16
        for k, v in enumerate(t):
            px[tx * 8 + k % 8, ty * 8 + k // 8] = v
    png.parent.mkdir(parents=True, exist_ok=True)
    im.save(png, bits=4)


def quantizar(img, paletas):
    """Cada ladrilho 8x8 do RGB `img` na paleta (de `paletas`, {nº: cores}) de menor erro: [[(índices, nº)]]."""
    w, h = img.size
    px = img.load()
    saida = []
    for ty in range(h // 8):
        linha = []
        for tx in range(w // 8):
            cores = [px[tx * 8 + x, ty * 8 + y][:3] for y in range(8) for x in range(8)]
            melhor = None
            for n, pal in paletas.items():
                idx, erro = [], 0
                for c in cores:
                    d, i = min((sum((a - b) ** 2 for a, b in zip(c, p)), i) for i, p in enumerate(pal) if i)
                    idx.append(i)
                    erro += d
                if melhor is None or erro < melhor[0]:
                    melhor = (erro, tuple(idx), n)
            linha.append((melhor[1], melhor[2]))
        saida.append(linha)
    return saida


class Ladrilhos:
    """Ladrilhos secundários novos, sem repetir (o mesmo desenho em paletas diferentes vale um só)."""

    def __init__(self, base):
        self.lista = list(base)
        self.indice = {}

    def entrada(self, idx, pal):
        if idx not in self.indice:
            self.indice[idx] = len(self.lista)
            self.lista.append(idx)
        return (PRIMARIOS + self.indice[idx]) | pal << 12


def metatiles_de(img, paletas, ladrilhos):
    """A imagem (múltiplo de 16 px) em metatiles: {(mx, my): [8 entradas]} (camada de baixo; a de cima vazia)."""
    q = quantizar(img, paletas)
    out = {}
    for my in range(img.size[1] // 16):
        for mx in range(img.size[0] // 16):
            ent = []
            for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
                idx, pal = q[my * 2 + dy][mx * 2 + dx]
                ent.append(ladrilhos.entrada(idx, pal))
            out[(mx, my)] = ent + [0, 0, 0, 0]
    return out


# ---------------------------------------------------------------------------------------------------------------
# Desenho: o prédio (exterior) e a sala do Dom
# ---------------------------------------------------------------------------------------------------------------
def desenhar_predio():
    """O prédio 64x96 (4x6 metatiles): telhado plano com parapeito, 5 andares de janelas tapadas por tábuas e o
    térreo com a porta (a porta é o METATILE_General_Door, à parte) e uma placa apagada."""
    P = PAL_PREDIO
    im = Image.new("RGB", (64, 96), P[3])
    d = ImageDraw.Draw(im)
    # telhado e parapeito
    d.rectangle((0, 0, 63, 11), fill=P[7])
    d.rectangle((0, 0, 63, 2), fill=P[8])
    d.rectangle((0, 9, 63, 11), fill=P[6])
    for x in range(4, 64, 12):
        d.rectangle((x, 4, x + 5, 7), fill=P[6])          # caixas d'água / dutos velhos
    d.line((0, 12, 63, 12), fill=P[1])
    # parede: tijolo escuro
    for y in range(13, 96):
        for x in range(64):
            if y % 6 == 0 or (x + (8 if (y // 6) % 2 else 0)) % 16 == 0:
                im.putpixel((x, y), P[2])
    # colunas nas bordas
    d.rectangle((0, 13, 2, 95), fill=P[4])
    d.rectangle((61, 13, 63, 95), fill=P[2])
    # andares de cima: 4 linhas de janelas, 2 por linha (cada uma ocupa 2 metatiles, centrada)
    for linha in range(4):
        y0 = 16 + linha * 16
        for j, x0 in enumerate((6, 38)):
            d.rectangle((x0, y0, x0 + 19, y0 + 11), fill=P[1])
            d.rectangle((x0 + 1, y0 + 1, x0 + 18, y0 + 10), fill=P[12])
            d.line((x0 + 2, y0 + 2, x0 + 6, y0 + 2), fill=P[13])
            # tábuas cruzadas (abandonado)
            torta = (linha + j) % 2
            d.rectangle((x0 - 1, y0 + 3 + torta, x0 + 20, y0 + 5 + torta), fill=P[10])
            d.line((x0 - 1, y0 + 5 + torta, x0 + 20, y0 + 5 + torta), fill=P[9])
            d.rectangle((x0 - 1, y0 + 7 - torta, x0 + 20, y0 + 9 - torta), fill=P[11])
            d.line((x0 - 1, y0 + 9 - torta, x0 + 20, y0 + 9 - torta), fill=P[9])
            for px_ in (x0 + 2, x0 + 17):
                d.point((px_, y0 + 4 + torta), fill=P[1])
                d.point((px_, y0 + 8 - torta), fill=P[1])
        d.line((0, y0 + 13, 63, y0 + 13), fill=P[14])            # beiral de cada andar
    # térreo: janelas tapadas por tábuas à esquerda, a porta (metatile próprio) na coluna 2, placa à direita
    y0 = 82
    d.rectangle((0, 80, 63, 81), fill=P[5])
    d.rectangle((5, y0, 22, 93), fill=P[9])
    for y in range(y0 + 1, 93, 3):
        d.line((5, y, 22, y), fill=P[10])
    d.line((5, y0, 22, 93), fill=P[11])
    d.rectangle((52, y0 + 1, 61, y0 + 7), fill=P[9])           # placa apagada com a rosa da Família
    d.rectangle((53, y0 + 2, 60, y0 + 6), fill=P[2])
    d.point((56, y0 + 4), fill=P[15])
    d.point((57, y0 + 3), fill=P[15])
    d.point((57, y0 + 5), fill=P[15])
    d.line((0, 94, 63, 95), fill=P[1])
    d.rectangle((0, 94, 63, 95), fill=P[2])
    return im


PAREDE, PAREDE_ESC, PAREDE_CLR = PAL_PAREDE[3], PAL_PAREDE[2], PAL_PAREDE[4]
LAMBRI, MADEIRA_ESC = PAL_PAREDE[12], PAL_PAREDE[11]
OURO_ESC, OURO, OURO_CLR = PAL_PAREDE[8], PAL_PAREDE[9], PAL_PAREDE[10]
VERM_ESC, VERM, VERM_CLR = PAL_PAREDE[5], PAL_PAREDE[6], PAL_PAREDE[7]
PISO_ESC, PISO, PISO_SOMBRA = PAL_PISO[2], PAL_PISO[3], PAL_PISO[4]
MAD_ESC, MAD, MAD_CLR = PAL_PISO[5], PAL_PISO[6], PAL_PISO[7]
PAPEL, PAPEL_SOMBRA = PAL_PISO[8], PAL_PISO[9]
TAP_ESC, TAP, TAP_CLR = PAL_PISO[13], PAL_PISO[14], PAL_PISO[15]


def _parede(d, x0, x1, alto, lambri):
    """Parede vinho de x0 a x1 (alto = linha de cima; lambri = a linha de baixo, com o rodapé de madeira)."""
    y1 = 15
    d.rectangle((x0, 0, x1, y1), fill=PAREDE)
    for x in range(x0, x1 + 1):
        if x % 8 == 0:
            d.line((x, 0, x, y1), fill=PAREDE_ESC)
    if alto:
        d.rectangle((x0, 0, x1, 1), fill=PAREDE_ESC)
    if lambri:
        d.rectangle((x0, 6, x1, 6), fill=OURO_ESC)
        d.rectangle((x0, 7, x1, 15), fill=LAMBRI)
        d.rectangle((x0, 15, x1, 15), fill=MADEIRA_ESC)
        for x in range(x0, x1 + 1):
            if x % 8 == 4:
                d.line((x, 8, x, 14), fill=MADEIRA_ESC)


def desenhar_sala(src):
    """Os metatiles da sala do Dom: {nome: imagem RGB}. Desenho próprio, na linha da prévia aprovada (item 5)."""
    s = {}

    def nova(w=16, h=16):
        im = Image.new("RGB", (w, h), PISO)
        return im, ImageDraw.Draw(im)

    # parede vinho (linha de cima e linha do lambri)
    im, d = nova()
    _parede(d, 0, 15, True, False)
    s["parede_alta"] = im
    im, d = nova()
    _parede(d, 0, 15, False, True)
    s["parede_lambri"] = im

    # janela com cortinas vermelhas (2x2): linha de cima = parede alta, de baixo = lambri
    im = Image.new("RGB", (32, 32), PAREDE)
    d = ImageDraw.Draw(im)
    top, bot = Image.new("RGB", (32, 16)), Image.new("RGB", (32, 16))
    _parede(ImageDraw.Draw(top), 0, 31, True, False)
    _parede(ImageDraw.Draw(bot), 0, 31, False, True)
    im.paste(top, (0, 0))
    im.paste(bot, (0, 16))
    d.rectangle((7, 3, 24, 22), fill=K)
    d.rectangle((8, 4, 23, 21), fill=PAL_PAREDE[13])
    d.line((15, 4, 15, 21), fill=OURO_ESC)
    d.line((8, 12, 23, 12), fill=OURO_ESC)
    d.point((10, 6), fill=PAL_PAREDE[14])
    d.point((19, 15), fill=PAL_PAREDE[14])
    d.rectangle((6, 22, 25, 23), fill=OURO)                      # peitoril
    d.rectangle((2, 1, 29, 2), fill=OURO)                        # varão
    d.point((2, 1), fill=OURO_CLR)
    d.point((29, 1), fill=OURO_CLR)
    for x0, x1 in ((3, 9), (22, 28)):
        d.rectangle((x0, 3, x1, 30), fill=VERM)
        for x in range(x0 + 1, x1, 2):
            d.line((x, 4, x, 30), fill=VERM_ESC if (x - x0) % 4 == 1 else VERM_CLR)
        d.line((x0, 3, x0, 30), fill=VERM_ESC)
        d.line((x1, 3, x1, 30), fill=VERM_ESC)
    d.rectangle((3, 16, 9, 18), fill=OURO)                       # amarras douradas
    d.rectangle((22, 16, 28, 18), fill=OURO)
    s["cortina"] = im

    # o quadro do chefe (3x2): moldura dourada e, dentro dela, o retrato em preto e branco (desenhar_quadro)
    for nome, retrato in QUADROS.items():
        s[f"quadro_{nome}"] = desenhar_quadro(src, retrato)

    # piso de madeira escura e o piso com a sombra da parede
    def piso(d, sombra):
        d.rectangle((0, 0, 15, 15), fill=PISO)
        for y in (3, 7, 11, 15):
            d.line((0, y, 15, y), fill=PISO_ESC)
        for y, x in ((0, 5), (4, 12), (8, 2), (12, 9)):
            d.line((x, y, x, y + 2), fill=PISO_ESC)
        if sombra:
            d.rectangle((0, 0, 15, 3), fill=PISO_SOMBRA)
    im, d = nova()
    piso(d, False)
    s["piso"] = im
    im, d = nova()
    piso(d, True)
    s["piso_sombra"] = im

    # tapete vermelho com bordas douradas (3 colunas, corre na vertical)
    im = Image.new("RGB", (48, 16), TAP)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1, 15), fill=PISO_ESC)
    d.rectangle((46, 0, 47, 15), fill=PISO_ESC)
    d.line((2, 0, 2, 15), fill=TAP_ESC)
    d.line((45, 0, 45, 15), fill=TAP_ESC)
    d.line((4, 0, 4, 15), fill=PAL_PISO[11])
    d.line((43, 0, 43, 15), fill=PAL_PISO[11])
    d.line((5, 0, 5, 15), fill=PAL_PISO[10])
    d.line((42, 0, 42, 15), fill=PAL_PISO[10])
    for y in range(0, 16, 4):
        d.point((3, y), fill=PAL_PISO[12])
        d.point((44, y + 2), fill=PAL_PISO[12])
    for y in (2, 10):
        d.point((16, y), fill=TAP_CLR)
        d.point((31, y + 4), fill=TAP_CLR)
    s["tapete"] = im

    # a mesa escura (3x2): papéis e luminária dourada em cima, gavetas na frente
    im = Image.new("RGB", (48, 32), PISO)
    d = ImageDraw.Draw(im)
    for y in (3, 7, 11, 15, 19, 23, 27, 31):
        d.line((0, y, 47, y), fill=PISO_ESC)
    d.rectangle((1, 6, 46, 30), fill=K)
    d.rectangle((2, 7, 45, 13), fill=MAD_CLR)
    d.rectangle((2, 12, 45, 13), fill=MAD)
    d.rectangle((2, 14, 45, 29), fill=MAD_ESC)
    d.rectangle((2, 14, 45, 14), fill=K)
    for x0 in (4, 34):
        d.rectangle((x0, 16, x0 + 9, 27), fill=MAD)
        d.rectangle((x0, 16, x0 + 9, 16), fill=MAD_CLR)
        d.rectangle((x0 + 3, 21, x0 + 6, 22), fill=PAL_PISO[11])
    d.rectangle((16, 16, 31, 26), fill=MAD)
    d.rectangle((22, 20, 25, 21), fill=PAL_PISO[12])
    d.rectangle((5, 5, 14, 10), fill=PAPEL)                      # papéis
    d.rectangle((7, 4, 16, 9), fill=PAPEL)
    d.line((8, 6, 14, 6), fill=PAPEL_SOMBRA)
    d.line((8, 8, 13, 8), fill=PAPEL_SOMBRA)
    d.rectangle((18, 8, 25, 10), fill=TAP)                       # uma rosa sobre a mesa
    d.point((19, 8), fill=TAP_CLR)
    d.rectangle((36, 0, 41, 2), fill=PAL_PISO[12])               # a luminária
    d.rectangle((35, 3, 42, 5), fill=PAL_PISO[11])
    d.rectangle((38, 6, 39, 9), fill=PAL_PISO[10])
    d.rectangle((36, 10, 41, 10), fill=PAL_PISO[10])
    d.rectangle((1, 30, 46, 31), fill=PISO_SOMBRA)
    s["mesa"] = im

    # a poltrona de veludo vermelho e ouro (3x1; o chefe fica na do meio), encostada na parede: o piso tem a sombra
    im = Image.new("RGB", (48, 16), PISO)
    d = ImageDraw.Draw(im)
    for y in (3, 7, 11, 15):
        d.line((0, y, 47, y), fill=PISO_ESC)
    d.rectangle((0, 0, 47, 3), fill=PISO_SOMBRA)
    d.rectangle((10, 0, 37, 15), fill=K)
    d.rectangle((11, 0, 36, 13), fill=PAL_PISO[10])
    d.rectangle((13, 0, 34, 12), fill=TAP_ESC)
    d.rectangle((14, 0, 33, 11), fill=TAP)
    for x in (17, 23, 29):
        d.point((x, 3), fill=TAP_CLR)
        d.point((x, 8), fill=TAP_CLR)
    for x0 in (6, 36):                                           # braços
        d.rectangle((x0, 6, x0 + 5, 14), fill=K)
        d.rectangle((x0 + 1, 7, x0 + 4, 13), fill=TAP)
        d.rectangle((x0 + 1, 7, x0 + 4, 7), fill=PAL_PISO[11])
    d.rectangle((8, 15, 39, 15), fill=PISO_SOMBRA)
    s["poltrona"] = im

    # vaso dourado com um buquê de rosas (paleta 11, sobre o piso): ocupa o tile inteiro para aparecer de longe
    P = PAL_ROSAS
    im = Image.new("RGB", (16, 16), P[10])
    d = ImageDraw.Draw(im)
    for y in (3, 7, 11, 15):
        d.line((0, y, 15, y), fill=P[9])
    d.ellipse((3, 13, 12, 15), fill=P[9])                        # sombra no piso
    d.polygon([(4, 8), (11, 8), (12, 10), (10, 14), (5, 14), (3, 10)], fill=P[1])
    d.polygon([(5, 9), (10, 9), (11, 10), (9, 13), (6, 13), (4, 10)], fill=P[7])
    d.line((5, 9, 10, 9), fill=P[8])
    d.line((4, 10, 6, 10), fill=P[8])
    d.line((6, 12, 9, 12), fill=P[6])
    d.rectangle((6, 14, 9, 14), fill=P[6])
    for x0, y0, x1, y1 in ((2, 4, 1, 6), (13, 4, 14, 6), (4, 6, 3, 8), (11, 6, 12, 8)):
        d.line((x0, y0, x1, y1), fill=P[3])                      # folhas
    for x, y in ((7, 1), (3, 3), (11, 3), (5, 5), (9, 5), (7, 4), (13, 6), (2, 6)):
        d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=P[4])     # rosas
        d.point((x, y), fill=P[5])
        d.point((x - 1, y - 1), fill=P[5])
    s["vaso"] = im

    # a moldura da sala (o alto da parede visto de cima): viga de madeira escura com um filete de ouro
    faixas = [K, K, PAREDE_ESC, PAREDE_ESC, LAMBRI, MADEIRA_ESC, MADEIRA_ESC, MADEIRA_ESC, MADEIRA_ESC,
              MADEIRA_ESC, OURO_ESC, OURO, MADEIRA_ESC, MADEIRA_ESC, K, K]   # de fora (0) para dentro (15)
    for nome, faixa in (("moldura_topo", lambda x, y: y), ("moldura_esq", lambda x, y: x),
                        ("moldura_dir", lambda x, y: 15 - x), ("moldura_canto_esq", lambda x, y: min(x, y)),
                        ("moldura_canto_dir", lambda x, y: min(15 - x, y))):
        im = Image.new("RGB", (16, 16))
        for y in range(16):
            for x in range(16):
                im.putpixel((x, y), faixas[faixa(x, y)])
        s[nome] = im

    s["escada"] = desenhar_escada()
    return s


# O retrato de cada chefe: o sprite do mapa com chapéu (tools/familia_sombra/gerar.py), quadro único 32x40. A chave é o
# nome do metatile ("quadro_<nome>"); None = a tela vazia (escura), para um chefe que ainda não tem sprite. Os 4 chefes
# têm retrato: o layout traz o Dom e o ON_LOAD do 6º andar troca pelo da ocupação (QuadroDom/Cobrador/Mercenario/Pesadelo).
QUADROS = {"dom": "gengar_shiny", "cobrador": "tyranitar_shiny", "mercenario": "garchomp_shiny",
           "pesadelo": "darkrai_shiny"}
# Os limiares de luminância (preto abaixo de `a`, cinza médio abaixo de `b`, cinza claro dali em diante). O padrão serve
# ao Gengar e ao Tyranitar (os mesmos bytes de antes). Garchomp e Darkrai são azul-escuros: no padrão a pele cai toda no
# cinza médio, igual ao fundo da tela, e sobra só o contorno; aqui a pele escura vira preto e a clara vira cinza claro.
LIMIAR_PADRAO = (64, 120)
LIMIARES_RETRATO = {"garchomp_shiny": (50, 75), "darkrai_shiny": (58, 80)}
QUADRO_TELA = (7, 5, 40, 26)        # a tela do retrato dentro do quadro 48x32 (x0, y0, x1, y1, inclusive)
SPRITES_FAMILIA = Path("graphics/object_events/pics/familia")
PALETAS_SPRITES_FAMILIA = Path("graphics/object_events/palettes/familia")


def _tom(cor, sprite):
    """Cor do sprite → um dos 3 tons do retrato, pela luminância e pelos limiares do sprite (LIMIARES_RETRATO)."""
    a, b = LIMIARES_RETRATO.get(sprite, LIMIAR_PADRAO)
    lum = 0.299 * cor[0] + 0.587 * cor[1] + 0.114 * cor[2]
    return K if lum < a else CINZA_MEDIO if lum < b else CINZA_CLARO


def desenhar_quadro(src, sprite):
    """O quadro 48x32: a parede vinho atrás, a moldura dourada e a tela do retrato (QUADRO_TELA). O retrato é o busto do
    sprite em 1:1 (as linhas de cima do desenho, do chapéu para baixo, até a altura da tela), centrado na largura e
    convertido para os 3 tons de cinza. Nada passa da tela: a moldura é a mesma em todos os quadros."""
    P = PAL_ROSAS
    im = Image.new("RGB", (48, 32), P[12])
    d = ImageDraw.Draw(im)
    for x in range(0, 48, 8):
        d.line((x, 0, x, 31), fill=P[13])
    d.rectangle((0, 0, 47, 1), fill=P[13])
    d.rectangle((0, 22, 47, 22), fill=P[6])
    d.rectangle((0, 23, 47, 31), fill=P[11])
    d.rectangle((0, 31, 47, 31), fill=P[9])
    x0, y0, x1, y1 = QUADRO_TELA
    d.rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), fill=K)              # contorno
    d.rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), fill=P[7])           # ouro
    d.line((x0 - 3, y0 - 3, x1 + 3, y0 - 3), fill=P[8])
    d.line((x0 - 3, y0 - 3, x0 - 3, y1 + 3), fill=P[8])
    d.line((x0 - 2, y1 + 3, x1 + 3, y1 + 3), fill=P[6])
    d.line((x1 + 3, y0 - 2, x1 + 3, y1 + 3), fill=P[6])
    d.rectangle((x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=P[6])           # chanfro de dentro
    for cx, cy in ((x0 - 3, y0 - 3), (x1 + 3, y0 - 3), (x0 - 3, y1 + 3), (x1 + 3, y1 + 3)):
        d.point((cx, cy), fill=P[8])                                    # cantos brilhando
    if sprite is None:
        d.rectangle((x0, y0, x1, y1), fill=K)
        return im
    d.rectangle((x0, y0, x1, y1), fill=CINZA_MEDIO)
    pic = Image.open(src / SPRITES_FAMILIA / f"{sprite}.png")
    linhas = (src / PALETAS_SPRITES_FAMILIA / f"{sprite}.pal").read_text().split()
    pal = [tuple(map(int, linhas[3 + i * 3:6 + i * 3])) for i in range(16)]
    px = pic.load()
    bx0, by0, bx1, _by1 = pic.getbbox()
    dx = x0 + (x1 - x0 + 1 - (bx1 - bx0)) // 2 - bx0
    dy = y0 + 1 - by0                                                   # 1 linha de folga em cima do chapéu
    for y in range(by0, min(pic.height, by0 + y1 - y0)):
        for x in range(bx0, bx1):
            c = px[x, y] & 15
            if c:
                im.putpixel((x + dx, y + dy), _tom(pal[c], sprite))
    return im


def desenhar_escada():
    """A escada para baixo da sala do Dom (3x2 metatiles, (x..x+2, 3..4)): degraus de madeira escura que descem para
    a esquerda, passadeira vermelha com varetas de latão e o balaústre dourado embaixo. O patamar fica na coluna da
    direita (o warp); embaixo dele, o piso livre com o pilar do corrimão. Só cores da paleta 10."""
    im = Image.new("RGB", (48, 32), PISO)
    d = ImageDraw.Draw(im)
    for y in (3, 7, 11, 15, 19, 23, 27, 31):                     # o piso de tábuas em volta
        d.line((0, y, 47, y), fill=PISO_ESC)
    d.rectangle((0, 0, 47, 3), fill=PISO_SOMBRA)
    # degraus: o patamar (x 36-47, só na linha de cima) e 6 degraus de 6 px, cada um mais escuro para a esquerda
    cores = [MAD_CLR, MAD_CLR, MAD, MAD, MAD_ESC, MAD_ESC, PISO_SOMBRA]
    d.rectangle((36, 0, 47, 15), fill=MAD_CLR)
    d.line((36, 0, 47, 0), fill=MAD)
    d.rectangle((36, 1, 37, 15), fill=PAL_PISO[11])             # soleira de latão
    for i in range(6):
        x1 = 35 - i * 6
        x0 = x1 - 5
        alto = 15 if x0 >= 32 else 23
        d.rectangle((x0, 0, x1, alto), fill=cores[i + 1])
        d.line((x0, 0, x0, alto), fill=K)                        # a queda de cada degrau
        d.line((x1, 0, x1, alto), fill=cores[i])                 # o bocel claro
    # a passadeira vermelha, com uma vareta de latão em cada degrau
    d.rectangle((0, 5, 47, 12), fill=TAP)
    d.line((0, 5, 47, 5), fill=PAL_PISO[11])
    d.line((0, 12, 47, 12), fill=PAL_PISO[11])
    for i in range(6):
        x1 = 35 - i * 6
        d.line((x1 - 5, 6, x1 - 5, 11), fill=TAP_ESC)
        d.line((x1, 6, x1, 11), fill=TAP_CLR if i < 3 else TAP)
        d.line((x1 - 1, 6, x1 - 1, 11), fill=PAL_PISO[10])
    d.rectangle((38, 6, 47, 11), fill=TAP_CLR)
    d.line((38, 6, 47, 6), fill=TAP)
    # o balaústre: corrimão de madeira, colunas douradas e a base; o pilar do canto com a bola de latão
    d.rectangle((0, 24, 35, 31), fill=PISO_SOMBRA)
    d.rectangle((0, 22, 35, 23), fill=MAD_CLR)
    d.line((0, 24, 35, 24), fill=MAD_ESC)
    for x in range(1, 34, 4):
        d.rectangle((x, 25, x + 1, 29), fill=PAL_PISO[11])
        d.point((x, 25), fill=PAL_PISO[12])
    d.rectangle((0, 30, 35, 31), fill=K)
    d.rectangle((32, 16, 35, 31), fill=MAD_ESC)                  # corrimão do lado do patamar
    d.line((32, 16, 32, 31), fill=K)
    d.rectangle((32, 18, 35, 31), fill=MAD)
    d.rectangle((31, 19, 36, 31), fill=K)
    d.rectangle((32, 20, 35, 30), fill=MAD)
    d.line((33, 20, 33, 30), fill=MAD_CLR)
    d.rectangle((32, 16, 35, 19), fill=PAL_PISO[11])             # bola de latão no topo do pilar
    d.point((33, 17), fill=PAL_PISO[12])
    return im


# ---------------------------------------------------------------------------------------------------------------
# Andares
# ---------------------------------------------------------------------------------------------------------------
LARGURA, ALTURA = 15, 13            # andares 1 a 5 (paredes nas linhas 0-2, piso de 3 a 11, a 12 é o vazio)
LARGURA_6, ALTURA_6 = 13, 13


class Andar:
    """Grade de (chave, colisão). Chaves: ("m", id da Mansão), ("d", nome da decoração) ou ("p", id primário)."""

    def __init__(self, w, h, janelas=(), parede_sala=False):
        self.w, self.h = w, h
        self.g = [[None] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                self.g[y][x] = (("m", 0x284), 0)
        # teto, paredes e o vazio de baixo (como a Mansão)
        for x in range(w):
            self.g[0][x] = (("m", 0x2A2), 1)
            self.g[1][x] = (("m", 0x2AA), 1)
            self.g[2][x] = (("m", 0x2B2), 1)
            self.g[h - 1][x] = (("p", 0x008), 1)
        self.g[0][0], self.g[0][1] = (("m", 0x2A0), 1), (("m", 0x2A1), 1)
        self.g[0][w - 2], self.g[0][w - 1] = (("m", 0x2A3), 1), (("m", 0x2A4), 1)
        for y in range(1, h - 1):
            self.g[y][0] = (("m", 0x2A8), 1)
            self.g[y][w - 1] = (("m", 0x2AC), 1)
        self.g[1][1], self.g[2][1] = (("m", 0x2A9), 1), (("m", 0x2B1), 1)
        self.g[1][w - 2], self.g[2][w - 2] = (("m", 0x2AB), 1), (("m", 0x2B3), 1)
        if parede_sala:
            for x in range(1, w - 1):
                self.g[1][x] = (("d", "parede_alta"), 1)
                self.g[2][x] = (("d", "parede_lambri"), 1)
        for x in janelas:
            self.g[1][x], self.g[1][x + 1] = (("m", 0x378), 1), (("m", 0x379), 1)
            self.g[2][x], self.g[2][x + 1] = (("m", 0x380), 1), (("m", 0x381), 1)
        self.piso = ("d", "piso") if parede_sala else None

    def put(self, x, y, chave, col):
        self.g[y][x] = (chave, col)

    def escada_acima(self, x):
        """Escada para cima (3 de largura) colada na parede; o warp é (x, 3), entrando pela esquerda."""
        g = self.put
        g(x + 2, 1, ("m", 0x374), 1)
        for i, m in enumerate((0x2D5, 0x2D6, 0x2D7)):
            g(x + i, 2, ("m", m), 1)
        for i, (m, c) in enumerate(((0x2DD, 0), (0x2DE, 1), (0x2DF, 1))):
            g(x + i, 3, ("m", m), c)
        for i, (m, c) in enumerate(((0x2E5, 0), (0x2E6, 1), (0x2E7, 1))):
            g(x + i, 4, ("m", m), c)
        for i, m in enumerate((0x37A, 0x28D, 0x28D)):
            g(x + i, 5, ("m", m), 0)
        return (x, 3)

    def escada_abaixo(self, x):
        """Escada para baixo colada na parede; o warp é (x + 2, 3), entrando pela direita."""
        g = self.put
        g(x, 2, ("m", 0x2D3), 1)
        for i, (m, c) in enumerate(((0x2D0, 1), (0x2D1, 1), (0x2D2, 0))):
            g(x + i, 3, ("m", m), c)
        for i, (m, c) in enumerate(((0x2D8, 1), (0x2D9, 1), (0x2DA, 0))):
            g(x + i, 4, ("m", m), c)
        for i, m in enumerate((0x2E0, 0x2E1, 0x2E2)):
            g(x + i, 5, ("m", m), 0)
        return (x + 2, 3)

    def escada_sala(self, x):
        """A escada para baixo da sala do Dom (desenho próprio, 3x2 em (x..x+2, 3..4)); o warp é (x + 2, 3), com o
        comportamento da escada da Mansão (ATRIBUTOS_DECORACAO). Embaixo do patamar, (x + 2, 4), o piso é livre."""
        for dy, cols in enumerate(((1, 1, 0), (1, 1, 0))):
            for dx, col in enumerate(cols):
                self.put(x + dx, 3 + dy, ("d", f"escada_{dx}_{dy}"), col)
        return (x + 2, 3)

    def moldura_sala(self):
        """O alto da parede e os lados da sala do Dom na viga escura (no lugar da moldura bege da Mansão)."""
        self.put(0, 0, ("d", "moldura_canto_esq"), 1)
        self.put(self.w - 1, 0, ("d", "moldura_canto_dir"), 1)
        for x in range(1, self.w - 1):
            self.put(x, 0, ("d", "moldura_topo"), 1)
        for y in range(1, self.h - 1):
            self.put(0, y, ("d", "moldura_esq"), 1)
            self.put(self.w - 1, y, ("d", "moldura_dir"), 1)

    def saida(self, x):
        """O tapete da saída (3 de largura, embaixo); o warp é (x + 1, h - 2), pisando para baixo."""
        y = self.h - 2
        for i, m in enumerate((0x2E8, 0x2E9, 0x2EA)):
            self.put(x + i, y, ("m", m), 0)
        for i, m in enumerate((0x01A, 0x01B, 0x01C)):
            self.put(x + i, y + 1, ("p", m), 1)
        return (x + 1, y)

    def mesa(self, x, y):
        linhas = ((0x308, 0x309, 0x30A, 0), (0x310, 0x311, 0x312, 1), (0x318, 0x319, 0x31A, 1),
                  (0x320, 0x321, 0x322, 0))
        for dy, (a, b, c, col) in enumerate(linhas):
            for dx, m in enumerate((a, b, c)):
                self.put(x + dx, y + dy, ("m", m), col)

    def pilar(self, x, y):
        for dy, (m, c) in enumerate(((0x2B5, 0), (0x2BD, 1), (0x2C5, 1), (0x2CD, 1), (0x28D, 0))):
            self.put(x, y + dy, ("m", m), c)

    def planta(self, x, y):
        self.put(x, y, ("m", 0x30B), 0)
        self.put(x, y + 1, ("m", 0x313), 1)

    def entulho(self, x, y):
        """Chão de terra 3x3 com entulho no meio (o prédio largado)."""
        tiles = ((0x2B8, 0x2B9, 0x2BA), (0x2C0, 0x2CC, 0x2C2), (0x2C8, 0x2C9, 0x2CA))
        for dy, linha in enumerate(tiles):
            for dx, m in enumerate(linha):
                self.put(x + dx, y + dy, ("m", m), 1 if (dx, dy) == (1, 1) else 0)

    def grade(self, x0, x1, y):
        """A grade de ferro da Mansão (2 linhas), de x0 a x1."""
        for x in range(x0, x1 + 1):
            topo = 0x2F8 if x == x0 else 0x2FA if x == x1 else 0x2F9
            base = 0x300 if x == x0 else 0x302 if x == x1 else 0x301
            self.put(x, y, ("m", topo), 1)
            self.put(x, y + 1, ("m", base), 1)

    def sombras(self):
        """Sombra da parede no piso liso (Mansão: 0x285, cantos 0x288/0x289); na sala, o piso de madeira."""
        parede = lambda x, y: self.g[y][x][1] == 1 and y <= 2 or x in (0, self.w - 1)
        for y in range(3, self.h - 1):
            for x in range(1, self.w - 1):
                chave, col = self.g[y][x]
                if self.piso and chave == ("m", 0x284):
                    self.g[y][x] = (("d", "piso_sombra" if y == 3 else "piso"), col)
                    continue
                if chave != ("m", 0x284):
                    continue
                cima, esq, dir_ = parede(x, y - 1), parede(x - 1, y), parede(x + 1, y)
                if cima and esq:
                    m = 0x288
                elif cima and dir_:
                    m = 0x289
                elif cima or esq:
                    m = 0x285
                else:
                    continue
                self.g[y][x] = (("m", m), col)


def andares():
    """Os 6 andares: {n: (Andar, info)}; info = warps e posições que os map.json e os testes usam."""
    out = {}
    # 1º andar: a saída embaixo, a escada para cima no canto direito; mesa, pilares e entulho.
    a = Andar(LARGURA, ALTURA, janelas=(5, 8))
    sobe = a.escada_acima(11)
    sai = a.saida(6)
    a.mesa(2, 4)
    a.pilar(6, 5)
    a.pilar(9, 5)
    a.entulho(10, 8)
    a.planta(1, 9)
    a.planta(13, 9)
    a.sombras()
    out[1] = (a, {"saida": sai, "sobe": sobe, "bilhete": (3, 6)})
    # 2º andar: a grade fecha o caminho direto entre as escadas
    a = Andar(LARGURA, ALTURA, janelas=(5, 8))
    desce = a.escada_abaixo(1)
    sobe = a.escada_acima(11)
    a.grade(5, 9, 3)
    a.mesa(6, 8)
    a.pilar(3, 7)
    a.pilar(12, 7)
    a.planta(1, 10)
    a.sombras()
    out[2] = (a, {"desce": desce, "sobe": sobe, "bilhete": (7, 10)})
    # 3º andar
    a = Andar(LARGURA, ALTURA, janelas=(5, 8))
    desce = a.escada_abaixo(1)
    sobe = a.escada_acima(11)
    a.grade(5, 9, 3)
    a.mesa(1, 7)
    a.entulho(9, 7)
    a.pilar(6, 6)
    a.planta(13, 10)
    a.sombras()
    out[3] = (a, {"desce": desce, "sobe": sobe, "bilhete": (2, 9)})
    # 4º e 5º andares (escuros): duas grades, o caminho dá a volta pelo meio da sala
    a = Andar(LARGURA, ALTURA, janelas=(5, 8))
    desce = a.escada_abaixo(1)
    sobe = a.escada_acima(11)
    a.grade(5, 9, 3)
    a.grade(5, 10, 5)
    a.mesa(7, 8)
    a.entulho(1, 8)
    a.sombras()
    out[4] = (a, {"desce": desce, "sobe": sobe, "bilhete": (8, 10)})
    a = Andar(LARGURA, ALTURA, janelas=(5, 8))
    desce = a.escada_abaixo(1)
    sobe = a.escada_acima(11)
    a.grade(5, 9, 3)
    a.grade(4, 10, 6)
    a.pilar(2, 7)
    a.mesa(10, 8)
    a.entulho(5, 9)
    a.sombras()
    out[5] = (a, {"desce": desce, "sobe": sobe, "bilhete": (11, 10)})
    # 6º andar: a sala do Dom. A escada fica no canto de cima à esquerda; o escritório (quadro, poltrona encostada na
    # parede, mesa e tapete) fica no lado direito, longe da linha da escada: ninguém passa atrás do chefe, e o jogador
    # chega pela lateral (onde estão os gêmeos) ou pela frente da mesa.
    a = Andar(LARGURA_6, ALTURA_6, parede_sala=True)
    a.moldura_sala()
    desce = a.escada_sala(1)
    x0 = SALA_ESCRITORIO_X
    for dx in range(3):
        a.put(x0 + dx, 1, ("d", f"quadro_dom_{dx}_0"), 1)      # o layout traz o Dom; o ON_LOAD troca pelo chefe
        a.put(x0 + dx, 2, ("d", f"quadro_dom_{dx}_1"), 1)
        a.put(x0 + dx, 3, ("d", f"poltrona_{dx}_0"), 1)
        a.put(x0 + dx, 4, ("d", f"mesa_{dx}_0"), 1)
        a.put(x0 + dx, 5, ("d", f"mesa_{dx}_1"), 1)
        for y in range(6, ALTURA_6 - 1):
            a.put(x0 + dx, y, ("d", f"tapete_{dx}_0"), 0)
    for dx in range(2):
        a.put(4 + dx, 1, ("d", f"cortina_{dx}_0"), 1)
        a.put(4 + dx, 2, ("d", f"cortina_{dx}_1"), 1)
    vasos = [(x0 - 1, 4), (x0 + 3, 4), (1, 10), (x0 + 3, 10)]
    for x, y in vasos:
        a.put(x, y, ("d", "vaso"), 1)
    a.sombras()
    out[6] = (a, {"desce": desce, "chefe": (x0 + 1, 3), "gemeos": [(x0 - 1, 3), (x0 + 3, 3)],
                  "bilhete": (x0, 5), "gatilhos": [(3, 4), (4, 4), (5, 3)], "vasos": vasos})
    return out


SALA_ESCRITORIO_X = 7               # 6º andar: 1ª coluna do escritório (quadro, poltrona, mesa e tapete, 3 de largura)


# ---------------------------------------------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------------------------------------------
def _u16s(b):
    return list(struct.unpack(f"<{len(b) // 2}H", b))


def _u32s(b):
    return list(struct.unpack(f"<{len(b) // 4}I", b))


def montar_familia(src, dst, plantas):
    """O tileset familia_sombra: os metatiles da Mansão que os andares usam (na ordem do id original) e a
    decoração da sala. Devolve {chave: id do metatile}."""
    lad_m = ler_ladrilhos(src / MANSAO / "tiles.png")
    met_m = _u16s((src / MANSAO / "metatiles.bin").read_bytes())
    atr_m = _u32s((src / MANSAO / "metatile_attributes.bin").read_bytes())
    usados = sorted({ch[1] for a, _ in plantas.values() for linha in a.g for ch, _c in linha if ch[0] == "m"})

    novos, remap = [], {}
    metas, atrs, ids = [], [], {}
    for mid in usados:
        i = mid - PRIMARIOS
        ent = []
        for e in met_m[i * 8:i * 8 + 8]:
            t = e & 0x3FF
            if t >= PRIMARIOS:
                if t not in remap:
                    remap[t] = len(novos)
                    novos.append(lad_m[t - PRIMARIOS])
                e = (e & ~0x3FF) | (PRIMARIOS + remap[t])
            ent.append(e)
        ids[("m", mid)] = PRIMARIOS + len(metas)
        metas.append(ent)
        atrs.append(atr_m[i])

    lad = Ladrilhos(novos)
    sala = desenhar_sala(src)
    for nome, im in sorted(sala.items()):
        for (mx, my), ent in sorted(metatiles_de(im, PALETAS_DECORACAO, lad).items()):
            chave = ("d", nome) if im.size == (16, 16) else ("d", f"{nome}_{mx}_{my}")
            ids[chave] = PRIMARIOS + len(metas)
            metas.append(ent)
            atrs.append(ATRIBUTOS_DECORACAO.get(chave, MB_NORMAL))
    assert len(lad.lista) <= MAX_SECUNDARIO, f"familia_sombra: {len(lad.lista)} ladrilhos"
    assert len(metas) <= MAX_SECUNDARIO, f"familia_sombra: {len(metas)} metatiles"

    out = dst / FAMILIA
    out.mkdir(parents=True, exist_ok=True)
    paleta_png = Image.open(src / MANSAO / "tiles.png").getpalette()[:48]
    gravar_ladrilhos(out / "tiles.png", lad.lista, paleta_png)
    (out / "metatiles.bin").write_bytes(struct.pack(f"<{len(metas) * 8}H", *[e for m in metas for e in m]))
    (out / "metatile_attributes.bin").write_bytes(struct.pack(f"<{len(atrs)}I", *atrs))
    (out / "palettes").mkdir(exist_ok=True)
    for n in range(16):
        if n in PALETAS_DECORACAO:
            texto = _jasc(PALETAS_DECORACAO[n])
        else:
            texto = (src / MANSAO / "palettes" / f"{n:02d}.pal").read_bytes().decode("ascii")
            texto = texto.replace("\r\n", "\n").replace("\n", "\r\n")
        (out / "palettes" / f"{n:02d}.pal").write_bytes(texto.encode("ascii"))
    return ids, len(lad.lista), len(metas)


def montar_indigo(src, dst):
    """O prédio no Platô Índigo (paleta 7). Devolve ({(mx, my): id}, id da porta trancada, nº de ladrilhos)."""
    base_lad = ler_ladrilhos(src / INDIGO / "tiles.png")[:INDIGO_TILES]
    base_met = _u16s((src / INDIGO / "metatiles.bin").read_bytes())[:INDIGO_METATILES * 8]
    base_atr = _u32s((src / INDIGO / "metatile_attributes.bin").read_bytes())[:INDIGO_METATILES]
    lad = Ladrilhos(base_lad)
    blocos = metatiles_de(desenhar_predio(), {7: PAL_PREDIO}, lad)
    metas, atrs, ids = [], [], {}
    for (mx, my), ent in sorted(blocos.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        ids[(mx, my)] = PRIMARIOS + INDIGO_METATILES + len(metas)
        metas.append(ent)
        atrs.append(MB_NORMAL)
    # a porta trancada: o mesmo desenho do METATILE_General_Door, sem o comportamento de porta
    gen = _u16s((src / "data/tilesets/primary/general/metatiles.bin").read_bytes())
    gen_atr = _u32s((src / "data/tilesets/primary/general/metatile_attributes.bin").read_bytes())
    porta = PRIMARIOS + INDIGO_METATILES + len(metas)
    metas.append(gen[METATILE_PORTA_GERAL * 8:METATILE_PORTA_GERAL * 8 + 8])
    atrs.append(gen_atr[METATILE_PORTA_GERAL] & ~0x1FF | MB_NORMAL)
    assert len(lad.lista) <= MAX_SECUNDARIO and INDIGO_METATILES + len(metas) <= MAX_SECUNDARIO

    out = dst / INDIGO
    out.mkdir(parents=True, exist_ok=True)
    gravar_ladrilhos(out / "tiles.png", lad.lista, Image.open(src / INDIGO / "tiles.png").getpalette()[:48])
    todos = base_met + [e for m in metas for e in m]
    (out / "metatiles.bin").write_bytes(struct.pack(f"<{len(todos)}H", *todos))
    todos_a = base_atr + atrs
    (out / "metatile_attributes.bin").write_bytes(struct.pack(f"<{len(todos_a)}I", *todos_a))
    (out / "palettes").mkdir(exist_ok=True)
    (out / "palettes" / "07.pal").write_bytes(_jasc(PAL_PREDIO).encode("ascii"))
    return ids, porta, len(lad.lista)


PREDIO_X, PREDIO_Y = 2, 144     # canto do prédio na Rota 23 (4x6)
PORTA = (4, 149)
CALCADA = [(x, y) for y in (150, 151) for x in range(2, 7)]


def montar_rota23(src, dst, ids):
    mapa = _u16s((src / ROTA23).read_bytes())
    for (mx, my), mid in ids.items():
        mapa[(PREDIO_Y + my) * ROTA23_LARGURA + PREDIO_X + mx] = mid | 1 << 10           # colisão 1, elevação 0
    mapa[PORTA[1] * ROTA23_LARGURA + PORTA[0]] = METATILE_PORTA_GERAL | 1 << 10
    for x, y in CALCADA:
        mapa[y * ROTA23_LARGURA + x] = 0x001 | 3 << 12                                    # grama, elevação 3
    (dst / ROTA23).parent.mkdir(parents=True, exist_ok=True)
    (dst / ROTA23).write_bytes(struct.pack(f"<{len(mapa)}H", *mapa))


def montar_andares(dst, plantas, ids):
    for n, (a, _info) in plantas.items():
        valores = []
        for linha in a.g:
            for chave, col in linha:
                mid = chave[1] if chave[0] == "p" else ids[chave]
                valores.append(mid | col << 10 | (0 if col else 3 << 12))
        pasta = dst / "data" / "layouts" / f"Route23_FamiliaSombra_{n}F"
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "map.bin").write_bytes(struct.pack(f"<{len(valores)}H", *valores))
        (pasta / "border.bin").write_bytes(struct.pack("<4H", *[0x008 | 1 << 10] * 4))


SAIDAS = [
    FAMILIA / "tiles.png", FAMILIA / "metatiles.bin", FAMILIA / "metatile_attributes.bin",
    *[FAMILIA / "palettes" / f"{n:02d}.pal" for n in range(16)],
    INDIGO / "tiles.png", INDIGO / "metatiles.bin", INDIGO / "metatile_attributes.bin", INDIGO / "palettes" / "07.pal",
    ROTA23, *[Path(f"data/layouts/Route23_FamiliaSombra_{n}F/{f}") for n in range(1, 7) for f in ("map.bin", "border.bin")],
    Path("tools/familia_sombra/predio.json"),
]


def gerar(src, dst):
    """Gera tudo em `dst`. As entradas do Platô Índigo e da Rota 23 são também saídas: a montagem só usa a parte
    original delas (os primeiros ladrilhos/metatiles; as células do prédio são sobrescritas), então rodar de novo
    dá o mesmo resultado."""
    plantas = andares()
    ids, n_lad, n_met = montar_familia(src, dst, plantas)
    predio, porta, n_lad_indigo = montar_indigo(src, dst)
    montar_rota23(src, dst, predio)
    montar_andares(dst, plantas, ids)
    info = {
        "_comentario": "Gerado por tools/familia_sombra/predio.py. Não editar.",
        "familia_sombra": {"ladrilhos": n_lad, "metatiles": n_met},
        "indigo_plateau": {"ladrilhos": n_lad_indigo, "porta_trancada": porta, "porta_aberta": METATILE_PORTA_GERAL},
        "rota23": {"porta": list(PORTA), "predio": [PREDIO_X, PREDIO_Y, 4, 6]},
        "quadro": {"x": SALA_ESCRITORIO_X, "y": 1, "tela": list(QUADRO_TELA),
                   "metatiles": {nome: [[ids[("d", f"quadro_{nome}_{dx}_{dy}")] for dx in range(3)] for dy in range(2)]
                                 for nome in QUADROS}},
        "andares": {str(n): {"largura": a.w, "altura": a.h,
                             **{k: (list(v) if isinstance(v, tuple) else [list(p) for p in v]) for k, v in i.items()}}
                    for n, (a, i) in plantas.items()},
    }
    (dst / "tools/familia_sombra").mkdir(parents=True, exist_ok=True)
    (dst / "tools/familia_sombra/predio.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n",
                                                            encoding="utf-8")
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conferir", action="store_true")
    args = ap.parse_args()
    if not args.conferir:
        with tempfile.TemporaryDirectory() as tmp:
            gerar(REPO, Path(tmp))
            for rel in SAIDAS:
                (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(tmp) / rel, REPO / rel)
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        gerar(REPO, Path(tmp))
        diferentes = [str(rel) for rel in SAIDAS
                      if not (REPO / rel).exists() or not filecmp.cmp(Path(tmp) / rel, REPO / rel, shallow=False)]
    if diferentes:
        print("diferente do gerador:", *diferentes, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
