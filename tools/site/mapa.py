"""Mapa de Kanto detalhado em pixel art (fundo da página do Professor).

Monta o mapa 240x160 do jogo a partir do tilemap (graphics/region_map), recorta, amplia 4x e
desenha relevo, árvores, picos, espuma, ondas e contorno de rotas. Determinístico (semente 7).
Uso: python3 tools/site/mapa.py [saida.png]
"""
import random
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SEMENTE = 7
K = 4
LARGURA_TILEMAP = 30
RECORTE = (24, 16, 216, 160)
# O ícone de troca de mapa é coberto copiando mar de ORIGEM_MAR para DESTINO_MAR.
ORIGEM_MAR = (600, 456, 664, 532)
DESTINO_MAR = (686, 456)

VERDES = [(24, 131, 8), (57, 172, 8), (82, 205, 8), (115, 230, 32), (172, 246, 57)]  # do mais baixo ao mais alto
CORES_MAR = [(164, 180, 255), (156, 213, 255), (82, 148, 213), (90, 172, 230)]
CORES_ROTA = [(230, 164, 0), (238, 189, 57), (246, 213, 82), (238, 230, 115), (246, 238, 139)]
ARVORE = [".##.", "####", "####", ".#.."]
PICO = ["..#..", ".#=#.", "#===#"]


def montar_kanto(repo):
    """Monta o mapa 240x160 (RGB) a partir de region_map.png/.pal e kanto.bin."""
    pasta = Path(repo) / "graphics/region_map"
    tiles = Image.open(pasta / "region_map.png")
    assert tiles.mode == "P", tiles.mode
    tw = tiles.width // 8
    linhas = (pasta / "region_map.pal").read_text().split("\n")
    n = int(linhas[2])
    cores = [tuple(int(v) for v in lin.split()) for lin in linhas[3:3 + n]]
    dados = (pasta / "kanto.bin").read_bytes()
    ents = struct.unpack("<%dH" % (len(dados) // 2), dados)
    altura = len(ents) // LARGURA_TILEMAP
    img = Image.new("RGB", (LARGURA_TILEMAP * 8, altura * 8))
    px = tiles.load()
    for i, e in enumerate(ents):
        t, hf, vf, pal = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, e >> 12
        tx, ty = (t % tw) * 8, (t // tw) * 8
        if ty >= tiles.height:
            continue
        for y in range(8):
            for x in range(8):
                sx = 7 - x if hf else x
                sy = 7 - y if vf else y
                idx = pal * 16 + (px[tx + sx, ty + sy] & 15)
                img.putpixel(((i % LARGURA_TILEMAP) * 8 + x, (i // LARGURA_TILEMAP) * 8 + y),
                             cores[idx] if idx < len(cores) else (0, 0, 0))
    return img


def escurece(c, f):
    return tuple(max(0, int(v * f)) for v in c)


def clareia(c, f):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c)


def detalhar(kanto):
    """Recebe o mapa 240x160 (PIL RGB) e devolve o array 576x768 detalhado."""
    rnd = random.Random(SEMENTE)
    src = np.array(kanto.convert("RGB").crop(RECORTE)).astype(int)
    h, w, _ = src.shape

    def cor(c):
        return np.all(src == np.array(c), axis=2)

    mar = np.zeros((h, w), bool)
    for c in CORES_MAR:
        mar |= cor(c)
    nivel = np.full((h, w), -1)
    for i, c in enumerate(VERDES):
        nivel[cor(c)] = i
    rota = np.zeros((h, w), bool)
    for c in CORES_ROTA:
        rota |= cor(c)

    out = np.repeat(np.repeat(src, K, 0), K, 1).astype(int)
    H, W = out.shape[:2]

    def px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            out[y, x] = c

    def borda(x, y, dx, dy, c):
        for k in range(K):
            if dx == 1: px(x * K + K - 1, y * K + k, c)
            if dy == 1: px(x * K + k, y * K + K - 1, c)
            if dx == -1: px(x * K, y * K + k, c)
            if dy == -1: px(x * K + k, y * K, c)

    # 1. relevo: sombra a sul/leste, luz a norte/oeste onde um verde encontra um mais baixo
    for y in range(h):
        for x in range(w):
            n = nivel[y, x]
            if n < 0:
                continue
            base = VERDES[n]
            for dx, dy, f, luz in ((1, 0, .78, False), (0, 1, .72, False), (-1, 0, .25, True), (0, -1, .3, True)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and 0 <= nivel[yy, xx] < n:
                    borda(x, y, dx, dy, clareia(base, f) if luz else escurece(base, f))

    # 2. árvores nos verdes baixos, tufos no meio, picos no alto
    for y in range(0, H - 4, 3):
        for x in range((y // 3) % 2 * 2, W - 4, 4):
            oy, ox = y // K, x // K
            n = nivel[min(oy, h - 1), min(ox, w - 1)]
            if n < 0 or rota[min(oy, h - 1), min(ox, w - 1)]:
                continue
            bloco = nivel[oy:oy + 2, ox:ox + 2]
            if bloco.size == 0 or (bloco != n).any():
                continue
            r = rnd.random()
            base = VERDES[n]
            if n <= 1 and r < .55:
                for j, linha in enumerate(ARVORE):
                    for i, ch in enumerate(linha):
                        if ch == "#":
                            px(x + i, y + j, escurece(base, .62) if (i + j) % 3 else clareia(base, .15))
                px(x + 1, y + 3, (92, 64, 24))
            elif n == 2 and r < .3:
                px(x + 1, y + 2, clareia(base, .35)); px(x + 2, y + 1, clareia(base, .35))
                px(x + 3, y + 2, escurece(base, .8))
            elif n >= 3 and r < .22:
                for j, linha in enumerate(PICO):
                    for i, ch in enumerate(linha):
                        if ch == "#":
                            px(x + i, y + j, escurece(base, .7))
                        elif ch == "=":
                            px(x + i, y + j, clareia(base, .55))

    # 3. mar: espuma na costa e ondinhas espalhadas
    espuma = (232, 244, 255)
    for y in range(h):
        for x in range(w):
            if not mar[y, x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and nivel[yy, xx] >= 0:
                    borda(x, y, dx, dy, espuma)
    for _ in range(int(mar.sum() * .18)):
        x, y = rnd.randrange(W - 3), rnd.randrange(H)
        if mar[y // K, x // K] and mar[y // K, min(w - 1, (x + 3) // K)]:
            px(x, y, (236, 246, 255)); px(x + 1, y - 1, (236, 246, 255)); px(x + 2, y, (200, 222, 255))

    # 4. rotas: contorno mais escuro e ponto claro em xadrez
    for y in range(h):
        for x in range(w):
            if not rota[y, x]:
                continue
            c = tuple(src[y, x])
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and not rota[yy, xx] and nivel[yy, xx] >= 0:
                    borda(x, y, dx, dy, escurece(c, .72))
            if (x + y) % 2 == 0:
                px(x * K + 1, y * K + 1, clareia(c, .45))
    return out


def cobrir_icone(out):
    x0, y0, x1, y1 = ORIGEM_MAR
    dx, dy = DESTINO_MAR
    out[dy:dy + (y1 - y0), dx:dx + (x1 - x0)] = out[y0:y1, x0:x1].copy()


def gerar(repo, destino):
    out = detalhar(montar_kanto(repo))
    cobrir_icone(out)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out.astype(np.uint8)).save(destino)


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[2]
    gerar(raiz, sys.argv[1] if len(sys.argv) > 1 else raiz / "site/assets/kanto_detalhe.png")
