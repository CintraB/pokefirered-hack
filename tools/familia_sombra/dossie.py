"""O dossiê da Família Sombra (POK-54, Task 9): os gráficos da tela cheia de src/dossie.c.

    python3 -I tools/familia_sombra/dossie.py              # grava tudo no repositório
    python3 -I tools/familia_sombra/dossie.py --conferir   # refaz num diretório temporário e compara (sai 1 se divergir)
    python3 -I tools/familia_sombra/dossie.py --folha saida.png   # prévia das 3 páginas montadas (não grava o resto)

Entradas (do próprio repositório):
    graphics/fonts/latin_normal.png + src/text.c (sFontNormalLatinGlyphWidths) + charmap.txt
        a fonte do jogo, para o "FAMÍLIA SOMBRA" em dobro da capa e os carimbos
    graphics/pokemon/<espécie>/front.png + shiny.pal   o sprite de batalha de cada chefe, para a foto
    tools/familia_sombra/predio.py                      os 3 tons do retrato da sala do Dom (TONS_DO_RETRATO)

Saídas (versionadas, nada à mão), em graphics/dossie/:
    pasta.png + pasta.pal   ladrilhos únicos do fundo (papel pardo da pasta, a mesa, o selo da polícia, a moldura da
                            foto) numa paleta só; a mesma paleta serve às janelas de texto (cores de texto em
                            DARK_GRAY = 2, LIGHT_GRAY = 3, RED = 4: os {COLOR ...} do charmap batem com ela)
    pasta.bin               3 telas de 32x20 entradas (u16): capa, ficha e texto (página "Depois")
    foto_{dom,cobrador,mercenario,pesadelo}.png   64x64, só os 3 tons do retrato (foto.pal)
    clipe.png               8x32, o clipe de papel por cima da foto (foto.pal)
    foto.pal                tons do retrato + o metal do clipe
    carimbo.png + .pal      64x64 = 2 quadros de 64x32: CAPTURADO e DERROTADO, tinta vermelha
    rosa.png + rosas.pal    8x16, a rosa da ficha; rosas.pal = 4 paletas de 16 (vermelha, dourada, azul, negra)

A foto usa o sprite de BATALHA (64x64, frente, cores shiny), não o sprite do mapa com chapéu do quadro da sala: no
tamanho da foto o de batalha se lê muito melhor (o do mapa tem 32x40 e o rosto some). Os tons são os do retrato
(predio.TONS_DO_RETRATO); os limiares de luminância são próprios (em FOTOS), porque as cores do sprite de batalha
não são as do sprite do mapa e com os LIMIARES_RETRATO de lá o Gengar ficava todo no cinza médio.

Só Pillow e a biblioteca padrão.
"""
import argparse
import filecmp
import math
import random
import re
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predio import TONS_DO_RETRATO  # noqa: E402  (o mesmo preto e os 2 cinzas do quadro da sala do Dom)

REPO = Path(__file__).resolve().parents[2]
SAIDA = Path("graphics/dossie")

# ---------------------------------------------------------------------------------------------------------------
# Paleta da pasta (BG) e do texto: os índices 2, 3 e 4 são DARK_GRAY, LIGHT_GRAY e RED do charmap ({COLOR RED} no
# texto da lore pinta o título de vermelho); o 15 é o marca-texto amarelo do título.
# ---------------------------------------------------------------------------------------------------------------
MESA = (72, 40, 20)
MESA_LINHA = (84, 48, 26)
TINTA = (56, 40, 24)
TINTA_SOMBRA = (200, 168, 104)
VERMELHO = (184, 24, 32)
OURO_ESC = (176, 128, 24)
MANILA = (224, 192, 128)
MANILA_ESC = (192, 152, 88)
MANILA_CLARO = (240, 216, 160)
FIBRA = (212, 176, 112)
AZUL = (32, 56, 136)
AZUL_ESC = (16, 32, 88)
OURO = (248, 208, 64)
BRANCO = (240, 232, 224)
SOMBRA_FOTO = (144, 120, 72)
MARCA_TEXTO = (248, 224, 80)
PASTA_PAL = [MESA, MESA_LINHA, TINTA, TINTA_SOMBRA, VERMELHO, OURO_ESC, MANILA, MANILA_ESC, MANILA_CLARO, FIBRA,
             AZUL, AZUL_ESC, OURO, BRANCO, SOMBRA_FOTO, MARCA_TEXTO]

# Foto (OBJ): 0 transparente, os 3 tons do retrato e o metal do clipe
K, CINZA_MEDIO, CINZA_CLARO = TONS_DO_RETRATO
CLIPE_CLARO, CLIPE_ESC = (224, 224, 232), (96, 96, 112)
FOTO_PAL = [(0, 0, 0), K, CINZA_MEDIO, CINZA_CLARO, CLIPE_CLARO, CLIPE_ESC]
FOTO_CHAO = 44                      # da linha 44 para baixo o fundo da foto é o cinza médio (o chão), acima o claro

# chefe -> (espécie do sprite de batalha, limiares de luminância: preto abaixo de `a`, cinza médio abaixo de `b`)
FOTOS = {
    "dom": ("gengar", (90, 150)),
    "cobrador": ("tyranitar", (80, 150)),
    "mercenario": ("garchomp", (60, 110)),
    "pesadelo": ("darkrai", (40, 90)),
}

PAPEL_CARIMBO = (232, 224, 208)     # o miolo do carimbo (de moldura a moldura): a tinta fica legível sobre a foto
CARIMBO_PAL = [(0, 0, 0), VERMELHO, PAPEL_CARIMBO]
CARIMBOS = (("CAPTURADO", 5, 5), ("DERROTADO", -5, 9))   # texto, ângulo, semente da tinta falhada (quadro 0, 1)

# A rosa da ficha (8x16, o desenho nas linhas 3-12): 1-4 pétalas do escuro ao claro, g/G caule e folha
ROSA = [
    "..1111..",
    ".122221.",
    "12333221",
    "12344321",
    ".123321.",
    "..1111..",
    "...g....",
    "..gGg...",
    "...g....",
    "...g....",
]
ROSA_Y = 3
VERDES = [(24, 72, 32), (40, 120, 48)]
PETALAS = {   # na ordem dos chefes: vermelha (Dom), dourada (Cobrador), azul (Mercenário), negra (Pesadelo)
    "vermelha": [(64, 8, 16), (152, 16, 32), (216, 48, 56), (248, 128, 120)],
    "dourada": [(96, 64, 8), (176, 128, 24), (232, 184, 48), (248, 232, 144)],
    "azul": [(16, 24, 72), (32, 64, 152), (72, 120, 216), (160, 200, 248)],
    "negra": [(8, 8, 12), (32, 28, 40), (64, 56, 72), (112, 104, 120)],
}

# Geometria das 3 telas (pixels; a mesma de src/dossie.c, que posiciona os sprites e o texto por cima)
TELA_W, TELA_H = 240, 160
PASTA = (6, 14, 233, 157)           # corpo da pasta (x0, y0, x1, y1), com a borda escura
ABA_CAPA = (6, 1, 112)              # aba (x0, y0, x1): "POLÍCIA DE KANTO"
ABA_FICHA = (6, 1, 160)             # aba da ficha: "FICHA 1 DE 4" e "FOLHA 1/3"
MOLDURA_FOTO = (11, 18, 80, 87)     # papel branco em volta da foto (a foto, sprite 64x64, fica em (14, 21))
SEPARADOR = (88, 67, 228)           # fio entre o cabeçalho e a 1ª linha da lore (x0, y, x1)
SELO = (120, 42)
ROTA_CAIXA = (166, 21, 226, 33)
TITULO_CAPA_Y = 62
CASO_ENCERRADO_Y = 96


def _5bits(cor):
    return tuple(c & 0xF8 for c in cor)


def _jasc(cores):
    cores = [_5bits(c) for c in cores] + [(0, 0, 0)] * (-len(cores) % 16)
    return "JASC-PAL\r\n0100\r\n" + f"{len(cores)}\r\n" + "".join(f"{r} {g} {b}\r\n" for r, g, b in cores)


def _png(im_idx, paleta, destino):
    """Grava uma imagem de índices (modo P) em 4 bits com a paleta `paleta` (16 cores)."""
    pal = [_5bits(c) for c in paleta] + [(0, 0, 0)] * (16 - len(paleta))
    im_idx.putpalette([v for c in pal for v in c])
    destino.parent.mkdir(parents=True, exist_ok=True)
    im_idx.save(destino, bits=4)


# ---------------------------------------------------------------------------------------------------------------
# A fonte do jogo (latin_normal.png: glifos 16x16, 16 por linha; pixel 1 = letra, 2 = sombra)
# ---------------------------------------------------------------------------------------------------------------
class Fonte:
    def __init__(self, src):
        self.img = Image.open(src / "graphics/fonts/latin_normal.png")
        texto = (src / "src/text.c").read_text(encoding="utf-8")
        corpo = re.search(r"sFontNormalLatinGlyphWidths\[\] =\s*\{(.*?)\};", texto, re.S).group(1)
        self.larg = [int(v) for v in re.findall(r"\d+", re.sub(r"/\*.*?\*/|//[^\n]*", "", corpo, flags=re.S))]
        self.cod = {}
        for linha in (src / "charmap.txt").read_text(encoding="utf-8").splitlines():
            m = re.match(r"^'(\\'|.)'\s*=\s*([0-9A-F]{2})\s*$", linha)
            if m:
                self.cod.setdefault("'" if m.group(1) == "\\'" else m.group(1), int(m.group(2), 16))

    def largura(self, s):
        return sum(self.larg[self.cod[ch]] for ch in s)

    def escrever(self, px, x, y, s, cor, sombra=None, k=1, limite=(TELA_W, TELA_H)):
        """Escreve `s` em (x, y) no acesso de pixels `px` (k = escala); devolve o x do fim."""
        for ch in s:
            g = self.cod[ch]
            gx, gy = (g % 16) * 16, (g // 16) * 16
            w = self.larg[g]
            for yy in range(16):
                for xx in range(w):
                    v = self.img.getpixel((gx + xx, gy + yy))
                    c = cor if v == 1 else sombra if v == 2 else None
                    if c is None:
                        continue
                    for a in range(k):
                        for b in range(k):
                            X, Y = x + xx * k + a, y + yy * k + b
                            if 0 <= X < limite[0] and 0 <= Y < limite[1]:
                                px[X, Y] = c
            x += w * k
        return x


# ---------------------------------------------------------------------------------------------------------------
# O fundo: 3 telas desenhadas em índices da PASTA_PAL e quebradas em ladrilhos únicos
# ---------------------------------------------------------------------------------------------------------------
I = {cor: i for i, cor in enumerate(PASTA_PAL)}


def _fibras():
    """Fibras do papel num bloco de 32x32 que se repete (assim os ladrilhos do papel se repetem também)."""
    rnd = random.Random(7)
    pontos = {}
    for _ in range(14):
        pontos[(rnd.randrange(32), rnd.randrange(32))] = MANILA_CLARO if rnd.random() < 0.5 else FIBRA
    return pontos


FIBRAS = _fibras()


def fundo(aba):
    im = Image.new("P", (TELA_W, TELA_H), I[MESA])
    d = ImageDraw.Draw(im)
    for y in range(0, TELA_H, 6):
        d.line((0, y, TELA_W - 1, y), fill=I[MESA_LINHA])
    x0, y0, x1, y1 = PASTA
    ax0, ay0, ax1 = aba
    d.rectangle((x0, y0, x1, y1), fill=I[MANILA_ESC])          # borda/sombra do corpo
    d.rectangle((ax0, ay0, ax1, y0 + 1), fill=I[MANILA_ESC])   # aba
    d.rectangle((ax0 + 1, ay0 + 1, ax1 - 1, y0 + 1), fill=I[MANILA])
    d.line((ax0 + 1, ay0 + 1, ax1 - 1, ay0 + 1), fill=I[MANILA_CLARO])
    d.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=I[MANILA])
    px = im.load()
    for y in range(ay0 + 2, y1 - 1):
        for x in range(x0 + 1, x1):
            if px[x, y] == I[MANILA] and (x % 32, y % 32) in FIBRAS:
                px[x, y] = I[FIBRAS[(x % 32, y % 32)]]
    d.line((x0 + 1, y1 - 1, x1 - 1, y1 - 1), fill=I[MANILA_ESC])
    return im


def selo_policia(im, cx, cy):
    d = ImageDraw.Draw(im)
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=I[OURO_ESC])
    d.ellipse((cx - 21, cy - 21, cx + 21, cy + 21), fill=I[OURO])
    d.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), fill=I[AZUL_ESC])
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=I[AZUL])
    pts = []
    for i in range(10):
        r = 13 if i % 2 == 0 else 5.5
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=I[OURO], outline=I[OURO_ESC])
    d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=I[OURO_ESC])
    d.point((cx, cy), fill=I[OURO])
    for i in range(16):                                        # serrilhado da borda
        a = i * math.pi / 8
        d.point((round(cx + 19 * math.cos(a)), round(cy + 19 * math.sin(a))), fill=I[OURO_ESC])


def carimbo_rgba(fonte, texto, k, angulo, semente, tinta=VERMELHO):
    """Carimbo de borracha: moldura dupla e o texto, com falhas de tinta, inclinado `angulo` graus.
    k = 2: em dobro, falhas na moldura e nas letras, girado (o da capa). k = 1: tamanho normal, sem negrito (no 1x o
    negrito falso cola as letras) e com as falhas só na moldura (uma falha numa letra de 1 px some com a letra)."""
    if k == 2:
        w, h = fonte.largura(texto) * 2 + 12, 32
    else:
        w, h = fonte.largura(texto) + 10, 17   # 3 px de folga de cada lado entre a moldura de dentro e o texto
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cor = tinta + (255,)
    d.rectangle((0, 0, w - 1, h - 1), outline=cor)
    d.rectangle((2, 2, w - 3, h - 3), outline=cor)
    px = im.load()

    def falhar(chance):                                        # tinta falhada
        rnd = random.Random(semente)
        for y in range(h):
            for x in range(w):
                if px[x, y][3] and rnd.random() < chance:
                    px[x, y] = (0, 0, 0, 0)

    if k == 2:
        fonte.escrever(px, 6, 0, texto, cor, None, 2, (w, h))
        falhar(0.13)
    else:
        falhar(0.10)
        fonte.escrever(px, 5, 0, texto, cor, None, 1, (w, h))
    if k == 2:
        return im.rotate(angulo, resample=Image.NEAREST, expand=True)
    # Em 1x a rotação come os traços de 1 px das letras: a inclinação vira um cisalhamento vertical (cada coluna
    # desce ou sobe inteira), que mantém cada letra legível e dá o degrau de carimbo torto.
    inclina = math.tan(math.radians(angulo))
    desloc = [round((w - 1 - x) * inclina) if inclina > 0 else round(-x * inclina) for x in range(w)]
    saida = Image.new("RGBA", (w, h + max(desloc)), (0, 0, 0, 0))
    out = saida.load()
    for x in range(w):
        for y in range(h):
            out[x, y + desloc[x]] = px[x, y]
    return saida


def colar_rgba(im_idx, rgba, x, y, mapa):
    """Cola os pixels opacos de `rgba` em `im_idx` (modo P), convertendo pela tabela cor -> índice `mapa`."""
    px = im_idx.load()
    src = rgba.load()
    for yy in range(rgba.height):
        for xx in range(rgba.width):
            r, g, b, a = src[xx, yy]
            if a and 0 <= x + xx < im_idx.width and 0 <= y + yy < im_idx.height:
                px[x + xx, y + yy] = mapa[(r, g, b)]


def tela_capa(fonte):
    im = fundo(ABA_CAPA)
    d = ImageDraw.Draw(im)
    d.rectangle(ROTA_CAIXA, fill=I[BRANCO], outline=I[TINTA])   # "ROTA 23" vem da janela de texto
    selo_policia(im, *SELO)
    titulo = "FAMÍLIA SOMBRA"
    w = fonte.largura(titulo) * 2
    fonte.escrever(im.load(), TELA_W // 2 - w // 2, TITULO_CAPA_Y, titulo, I[TINTA], I[TINTA_SOMBRA], 2)
    c = carimbo_rgba(fonte, "CASO ENCERRADO", 2, 4, 11)
    colar_rgba(im, c, TELA_W // 2 - c.width // 2, CASO_ENCERRADO_Y, {VERMELHO: I[VERMELHO]})
    return im


def tela_ficha():
    im = fundo(ABA_FICHA)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = MOLDURA_FOTO
    d.rectangle((x0 + 2, y0 + 2, x1 + 2, y1 + 2), fill=I[SOMBRA_FOTO])
    d.rectangle((x0, y0, x1, y1), fill=I[BRANCO])
    sx0, sy, sx1 = SEPARADOR
    d.line((sx0, sy, sx1, sy), fill=I[MANILA_ESC])
    return im


def tela_texto():
    return fundo(ABA_CAPA)


def ladrilhos_e_mapas(telas):
    """Quebra as telas em ladrilhos 8x8 únicos (o 0 é a mesa lisa) e devolve (ladrilhos, mapas 32x20 de cada tela)."""
    vazio = (I[MESA],) * 64
    ladrilhos, ids, mapas = [vazio], {vazio: 0}, []
    for im in telas:
        px = im.load()
        mapa = []
        for ty in range(TELA_H // 8):
            for tx in range(32):
                if tx >= TELA_W // 8:
                    mapa.append(0)
                    continue
                t = tuple(px[tx * 8 + x, ty * 8 + y] for y in range(8) for x in range(8))
                if t not in ids:
                    ids[t] = len(ladrilhos)
                    ladrilhos.append(t)
                mapa.append(ids[t])
        mapas.append(mapa)
    return ladrilhos, mapas


def gravar_ladrilhos(destino, ladrilhos):
    linhas = (len(ladrilhos) + 15) // 16
    im = Image.new("P", (128, linhas * 8), 0)
    px = im.load()
    for i, t in enumerate(ladrilhos):
        tx, ty = i % 16, i // 16
        for k, v in enumerate(t):
            px[tx * 8 + k % 8, ty * 8 + k // 8] = v
    _png(im, PASTA_PAL, destino)


# ---------------------------------------------------------------------------------------------------------------
# Sprites: fotos, clipe, carimbo e rosa
# ---------------------------------------------------------------------------------------------------------------
def _jasc_ler(p):
    v = p.read_text().split()
    return [tuple(map(int, v[3 + i * 3:6 + i * 3])) for i in range(16)]


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def foto(src, nome):
    """O sprite de batalha do chefe (frente, cores shiny) nos 3 tons do retrato, sobre o fundo claro com o chão médio.
    Devolve a imagem de índices da FOTO_PAL (1 preto, 2 cinza médio, 3 cinza claro)."""
    especie, (a, b) = FOTOS[nome]
    spr = Image.open(src / f"graphics/pokemon/{especie}/front.png")
    pal = _jasc_ler(src / f"graphics/pokemon/{especie}/shiny.pal")
    im = Image.new("P", (64, 64), 3)
    px, sp = im.load(), spr.load()
    for y in range(64):
        for x in range(64):
            c = sp[x, y] & 15
            if c:
                lum = _lum(pal[c])
                px[x, y] = 1 if lum < a else 2 if lum < b else 3
            elif y >= FOTO_CHAO:
                px[x, y] = 2
    return im


def clipe():
    """Clipe de papel 8x21 (no alto do sprite 8x32): 3 pernas de arame e 2 curvas, sombra à direita."""
    fio = set()
    fio |= {(xx, 0) for xx in range(2, 6)} | {(1, 1), (6, 1)}
    fio |= {(1, yy) for yy in range(1, 17)}
    fio |= {(6, yy) for yy in range(1, 20)}
    fio |= {(3, yy) for yy in range(5, 20)} | {(4, 20), (5, 20)}
    im = Image.new("P", (8, 32), 0)
    px = im.load()
    for (xx, yy) in fio:
        if (xx + 1, yy) not in fio and xx + 1 < 8:
            px[xx + 1, yy] = 5
    for (xx, yy) in fio:
        px[xx, yy] = 4
    return im


def carimbos(fonte):
    """2 quadros de 64x32 (CAPTURADO em cima, DERROTADO embaixo), o carimbo centrado em cada um."""
    im = Image.new("P", (64, 64), 0)
    for q, (texto, angulo, semente) in enumerate(CARIMBOS):
        c = carimbo_rgba(fonte, texto, 1, angulo, semente)
        assert c.width <= 64 and c.height <= 32, (texto, c.size)
        colar_rgba(im, c, (64 - c.width) // 2, q * 32 + (32 - c.height) // 2, {VERMELHO: 1})
    px = im.load()
    for q in range(2):                      # papel claro por dentro da moldura (coluna a coluna, o carimbo é torto)
        for x in range(64):
            ys = [y for y in range(q * 32, q * 32 + 32) if px[x, y] == 1]
            for y in range(min(ys, default=0), max(ys, default=-1) + 1):
                if px[x, y] == 0:
                    px[x, y] = 2
    return im


def rosa():
    im = Image.new("P", (8, 16), 0)
    px = im.load()
    idx = {"1": 1, "2": 2, "3": 3, "4": 4, "g": 5, "G": 6}
    for y, linha in enumerate(ROSA):
        for x, ch in enumerate(linha):
            if ch in idx:
                px[x, ROSA_Y + y] = idx[ch]
    return im


def rosas_pal():
    cores = []
    for petalas in PETALAS.values():
        cores += [(0, 0, 0), *petalas, *VERDES] + [(0, 0, 0)] * 9
    return cores


# ---------------------------------------------------------------------------------------------------------------
SAIDAS = [SAIDA / n for n in ("pasta.png", "pasta.pal", "pasta.bin", "foto.pal", "clipe.png", "carimbo.png",
                               "carimbo.pal", "rosa.png", "rosas.pal")] + [SAIDA / f"foto_{n}.png" for n in FOTOS]


def gerar(src, dst):
    fonte = Fonte(src)
    out = dst / SAIDA
    out.mkdir(parents=True, exist_ok=True)
    ladrilhos, mapas = ladrilhos_e_mapas([tela_capa(fonte), tela_ficha(), tela_texto()])
    gravar_ladrilhos(out / "pasta.png", ladrilhos)
    (out / "pasta.pal").write_bytes(_jasc(PASTA_PAL).encode())
    (out / "pasta.bin").write_bytes(b"".join(struct.pack("<H", t) for mapa in mapas for t in mapa))
    (out / "foto.pal").write_bytes(_jasc(FOTO_PAL).encode())
    for nome in FOTOS:
        _png(foto(src, nome), FOTO_PAL, out / f"foto_{nome}.png")
    _png(clipe(), FOTO_PAL, out / "clipe.png")
    _png(carimbos(fonte), CARIMBO_PAL, out / "carimbo.png")
    (out / "carimbo.pal").write_bytes(_jasc(CARIMBO_PAL).encode())
    cores = rosas_pal()
    _png(rosa(), cores[:16], out / "rosa.png")
    (out / "rosas.pal").write_bytes(_jasc(cores).encode())
    return len(ladrilhos)


def folha(destino):
    """Prévia: as 3 telas do fundo com as fotos, o clipe, os carimbos e a rosa colados (sem o texto), em 3x."""
    with tempfile.TemporaryDirectory() as tmp:
        gerar(REPO, Path(tmp))
        out = Path(tmp) / SAIDA
        fonte = Fonte(REPO)
        telas = [tela_capa(fonte), tela_ficha(), tela_texto()]
        rgb = [_com_pal(t, PASTA_PAL).convert("RGB") for t in telas]
        ficha = rgb[1]
        ficha.paste(_rgba(out / "foto_dom.png"), (14, 21))
        c = _rgba(out / "carimbo.png")
        ficha.paste(c.crop((0, 0, 64, 32)), (14, 52), c.crop((0, 0, 64, 32)))
        cl = _rgba(out / "clipe.png")
        ficha.paste(cl, (60, 14), cl)
        r = _rgba(out / "rosa.png")
        ficha.paste(r, (89, 47), r)
        fotos = Image.new("RGB", (70 * 4, 64 + 40), (255, 255, 255))
        for i, nome in enumerate(FOTOS):
            fotos.paste(_rgba(out / f"foto_{nome}.png"), (i * 70, 0))
        car = Image.new("RGB", (64, 64), MANILA)
        car.paste(c, (0, 0), c)
        fotos.paste(car.crop((0, 0, 64, 32)), (0, 68))
        fotos.paste(car.crop((0, 32, 64, 64)), (70, 68))
        folha_im = Image.new("RGB", (TELA_W * 3 + 16, TELA_H * 2 + 8), (255, 255, 255))
        for i, t in enumerate(rgb):
            folha_im.paste(t, (i * (TELA_W + 8), 0))
        folha_im.paste(fotos, (0, TELA_H + 8))
        folha_im.resize((folha_im.width * 3, folha_im.height * 3), Image.NEAREST).save(destino)


def _com_pal(im, pal):
    im = im.copy()
    im.putpalette([v for c in pal for v in c] + [0] * (768 - 3 * len(pal)))
    return im


def _rgba(p):
    im = Image.open(p)
    rgba = im.convert("RGBA")
    px, src = rgba.load(), im.load()
    for y in range(im.height):
        for x in range(im.width):
            if src[x, y] == 0:
                px[x, y] = (0, 0, 0, 0)
    return rgba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--folha")
    args = ap.parse_args()
    if args.folha:
        folha(args.folha)
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        n = gerar(REPO, Path(tmp))
        if not args.conferir:
            for rel in SAIDAS:
                (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(tmp) / rel, REPO / rel)
            print(f"{n} ladrilhos na pasta")
            return 0
        diferentes = [str(rel) for rel in SAIDAS
                      if not (REPO / rel).exists() or not filecmp.cmp(Path(tmp) / rel, REPO / rel, shallow=False)]
    if diferentes:
        print("diferente do gerador:", *diferentes, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
