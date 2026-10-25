#!/usr/bin/env python3
"""Desenha os 4 ícones novos da tela de novidades (24x24, 4bpp, 16 cores, índice 0 transparente).

Uso: gen_icones.py <pasta de saída> (padrão: graphics/novidades)
Gera icon_relogio/clima/cartucho/ficha .png (indexados) e .pal (JASC, CRLF).
O desenho é feito pixel a pixel a partir de formas e do contorno automático (índice 1),
no estilo dos ícones de item: contorno escuro, luz vindo de cima à esquerda, 3-4 tons por material.
"""
import math
import os
import sys

from PIL import Image

W = H = 24
OUT = 1  # contorno escuro, igual ao dos ícones de item (49,49,49)


class Canvas:
    def __init__(self, palette):
        self.pal = palette  # lista de (r,g,b); índice 0 = transparente
        self.px = [[0] * W for _ in range(H)]

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < W and 0 <= y < H else 0

    def shape(self, mask, painter, outline=True):
        """Desenha uma forma: o contorno (4-vizinhança) cai sobre o que já existe, depois o preenchimento."""
        m = set(mask)
        if outline:
            for (x, y) in list(m):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (x + dx, y + dy)
                    if n not in m:
                        self.set(n[0], n[1], OUT)
        for (x, y) in m:
            self.set(x, y, painter(x, y))

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def save(self, base):
        img = Image.new("P", (W, H), 0)
        flat = [c for row in self.px for c in row]
        img.putdata(flat)
        pal = []
        for rgb in (self.pal + [(0, 0, 0)] * 16)[:16]:
            pal.extend(rgb)
        img.putpalette(pal + [0] * (768 - len(pal)))
        img.save(base + ".png", bits=4)
        with open(base + ".pal", "w", newline="") as f:
            f.write("JASC-PAL\r\n0100\r\n16\r\n")
            for rgb in (self.pal + [(0, 0, 0)] * 16)[:16]:
                f.write("%d %d %d\r\n" % rgb)


def circle(cx, cy, r):
    return [(x, y) for y in range(H) for x in range(W) if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r]


def rect(x0, y0, x1, y1):  # inclusivo
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


def ellipse(cx, cy, rx, ry):
    return [(x, y) for y in range(H) for x in range(W)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1]


# ---------------------------------------------------------------- relógio
def relogio():
    pal = [(164, 222, 106),            # 0 transparente
           (49, 49, 49),               # 1 contorno
           (140, 90, 24),              # 2 ouro escuro
           (212, 156, 36),             # 3 ouro
           (248, 214, 74),             # 4 ouro claro
           (255, 255, 255),            # 5 branco
           (222, 230, 238),            # 6 face
           (172, 186, 206),            # 7 face sombra
           (214, 56, 48),              # 8 vermelho
           (255, 248, 190),            # 9 brilho
           (90, 82, 74),               # 10 ponteiro
           (96, 132, 190)]             # 11 azul noite
    c = Canvas(pal)
    cx, cy, R = 12.0, 14.0, 9.0

    # coroa e argola no topo
    c.shape(rect(10, 1, 13, 4), lambda x, y: 3 if x > 10 else 4)
    c.shape(rect(9, 4, 14, 5), lambda x, y: 2 if y == 5 else 3)

    def case_paint(x, y):
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        lit = (x + 0.5 - cx) + (y + 0.5 - cy)  # < 0: canto de luz (cima/esquerda)
        if d > R - 1.5:                         # aro de ouro
            if lit < -4:
                return 4
            if lit > 5:
                return 2
            return 3
        return 6                                # face

    mask = circle(cx, cy, R + 0.4)
    c.shape(mask, case_paint)

    # face: sombra interna no canto de baixo/direita e brilho no de cima/esquerda
    for (x, y) in circle(cx, cy, R - 1.5):
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        lit = (x + 0.5 - cx) + (y + 0.5 - cy)
        if d > R - 3.0 and lit > 3:
            c.set(x, y, 7)
        elif d < R - 2.5 and lit < -5:
            c.set(x, y, 5)
        else:
            c.set(x, y, 6)
    # metade de baixo da face azul-noite? (dia e noite): só um quarto, discreto
    for (x, y) in circle(cx, cy, R - 2.2):
        if x + 0.5 > cx and y + 0.5 > cy + 0.5 and (x + 0.5 - cx) + (y + 0.5 - cy) > 5.2:
            pass
    # marcas das horas (12, 3, 6, 9)
    for (x, y) in ((11, 8), (12, 8), (11, 20), (12, 20), (6, 13), (6, 14), (17, 13), (17, 14)):
        c.set(x, y, 10)
    # ponteiros: minuto para cima (até a marca das 12), hora para a direita/baixo (cerca de 4h)
    c.line(12, 13, 12, 9, OUT)
    c.line(11, 13, 11, 10, OUT)
    c.line(12, 14, 15, 16, OUT)
    c.line(11, 14, 11, 14, OUT)
    c.set(11, 13, OUT)
    c.set(11, 14, OUT)
    c.set(12, 14, OUT)
    c.set(12, 13, 8)  # pino vermelho no centro
    return c


# ---------------------------------------------------------------- clima
def clima():
    pal = [(164, 222, 106),
           (49, 49, 49),               # 1 contorno
           (222, 120, 24),             # 2 laranja sol
           (250, 190, 40),             # 3 amarelo
           (255, 238, 120),            # 4 amarelo claro
           (255, 255, 255),            # 5 nuvem branca
           (214, 226, 240),            # 6 nuvem clara
           (160, 180, 210),            # 7 nuvem sombra
           (110, 134, 176),            # 8 nuvem sombra funda
           (40, 120, 214),             # 9 gota
           (96, 176, 250),             # 10 gota clara
           (24, 76, 160)]              # 11 gota escura
    c = Canvas(pal)

    # sol atrás, em cima à esquerda
    scx, scy = 8.5, 8.5
    sun = circle(scx, scy, 4.7)

    def sun_paint(x, y):
        d = math.hypot(x + 0.5 - scx, y + 0.5 - scy)
        lit = (x + 0.5 - scx) + (y + 0.5 - scy)
        if lit < -3.5:
            return 4
        if lit > 3.0 or d > 4.2:
            return 2
        return 3
    c.shape(sun, sun_paint)
    # raios: barras de 2 px separadas do contorno por 1 px
    for (x, y) in ((8, 0), (8, 1), (0, 8), (1, 8), (2, 2), (3, 3), (14, 2), (13, 3), (2, 14), (3, 13)):
        c.set(x, y, 3)

    # nuvem à frente
    cloud = set(circle(14.0, 12.5, 4.6)) | set(circle(9.2, 15.0, 3.9)) | set(circle(19.0, 15.2, 3.6)) \
        | set(rect(9, 15, 19, 18))

    def cloud_paint(x, y):
        # topo claro, barriga em sombra
        if y >= 17:
            return 8 if y >= 18 else 7
        if y == 16:
            return 7
        lit = (x + 0.5 - 12.0) * 0.5 + (y + 0.5 - 13.0)
        if lit < -2.2:
            return 5
        if lit < 1.5:
            return 6
        return 7
    c.shape(cloud, cloud_paint)

    # chuva embaixo: riscos de 3 px na diagonal (ponta clara em cima, ponta escura embaixo)
    for gx in (7, 12, 17):
        c.set(gx + 1, 21, 10)
        c.set(gx, 22, 9)
        c.set(gx - 1, 23, 11)
    return c


# ---------------------------------------------------------------- cartucho
def cartucho():
    pal = [(164, 222, 106),
           (49, 49, 49),               # 1 contorno
           (226, 228, 238),            # 2 cinza claro
           (178, 182, 198),            # 3 cinza
           (122, 126, 146),            # 4 cinza escuro
           (86, 90, 110),              # 5 cinza mais escuro
           (232, 72, 56),              # 6 vermelho
           (255, 136, 100),            # 7 vermelho claro
           (160, 32, 40),              # 8 vermelho escuro
           (255, 248, 232),            # 9 branco rótulo
           (250, 200, 60),             # 10 ouro pinos
           (255, 255, 255)]            # 11 brilho
    c = Canvas(pal)
    # conector (parte de baixo, mais estreita) e casco (parte de cima, com o canto de cima-direita chanfrado)
    conn = rect(6, 18, 17, 22)
    c.shape(conn, lambda x, y: 4 if x < 16 else 5)
    shell = [(x, y) for (x, y) in rect(3, 1, 20, 18) if not (x >= 19 and y <= 2) and not (x == 20 and y == 3)]

    def shell_paint(x, y):
        if y == 1:
            return 11 if x < 18 else 3
        if x == 3:
            return 2
        if x >= 19:
            return 4
        if y >= 17:
            return 4
        return 3
    c.shape(shell, shell_paint)
    # ranhuras de pegada no topo
    for y in (3, 5):
        for x in range(5, 18):
            c.set(x, y, 4)
            c.set(x, y + 1, 2)
    # vale do rótulo e rótulo vermelho (sem texto): faixa branca de "título" e uma "pedra" amarela
    for (x, y) in rect(5, 8, 18, 16):
        c.set(x, y, 5 if (y == 8 or x == 5) else 2)
    for (x, y) in rect(6, 9, 17, 15):
        if y == 9:
            c.set(x, y, 7)
        elif y >= 14:
            c.set(x, y, 8)
        else:
            c.set(x, y, 6)
    for x in range(8, 16):
        c.set(x, 11, 9)
    for x in range(8, 13):
        c.set(x, 13, 9)
    c.set(14, 13, 10)
    c.set(15, 13, 10)
    # pinos dourados
    for x in range(7, 17, 2):
        c.set(x, 20, 10)
        c.set(x, 21, 10)
    return c


# ---------------------------------------------------------------- ficha
def ficha():
    pal = [(164, 222, 106),
           (49, 49, 49),               # 1 contorno
           (176, 116, 52),             # 2 madeira
           (214, 156, 80),             # 3 madeira clara
           (122, 78, 36),              # 4 madeira escura
           (255, 255, 255),            # 5 papel
           (226, 232, 240),            # 6 papel sombra
           (96, 120, 170),             # 7 linhas
           (190, 196, 210),            # 8 clipe
           (130, 136, 156),            # 9 clipe escuro
           (216, 60, 52),              # 10 vermelho
           (255, 120, 100)]            # 11 vermelho claro
    c = Canvas(pal)
    board = rect(3, 3, 20, 22)

    def board_paint(x, y):
        if x == 3 or y == 3:
            return 3
        if x >= 19 or y >= 21:
            return 4
        return 2
    c.shape(board, board_paint)
    paper = rect(5, 6, 18, 20)
    c.shape(paper, lambda x, y: 6 if (x >= 17 or y >= 19) else 5)
    clip = rect(8, 1, 15, 5)

    def clip_paint(x, y):
        if y == 1:
            return 8
        if x >= 14:
            return 9
        return 8 if y < 4 else 9
    c.shape(clip, clip_paint)
    for x in range(10, 14):
        c.set(x, 3, OUT)
    # mini Poké Bola (resumo do Pokémon) e linhas de dados
    ball = circle(9.5, 11.0, 2.7)

    def ball_paint(x, y):
        if y == 11:
            return OUT
        if y < 11:
            return 11 if (y == 9 and x < 9) else 10
        return 6 if (x >= 10 or y == 13) else 5
    c.shape(ball, ball_paint)
    c.set(9, 11, 5)
    c.set(10, 11, 5)
    for x in range(14, 18):
        c.set(x, 9, 7)
    for x in range(14, 17):
        c.set(x, 11, 7)
    for x in range(6, 18):
        c.set(x, 15, 7)
    for x in range(6, 18):
        c.set(x, 17, 7)
    for x in range(6, 13):
        c.set(x, 19, 7)
    return c


ICONES = {"icon_relogio": relogio, "icon_clima": clima, "icon_cartucho": cartucho, "icon_ficha": ficha}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "graphics/novidades"
    os.makedirs(out, exist_ok=True)
    for nome, fn in ICONES.items():
        fn().save(os.path.join(out, nome))


if __name__ == "__main__":
    main()
