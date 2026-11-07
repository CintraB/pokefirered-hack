"""Sprite do Prof. Carvalho para a página: PNG indexado do jogo -> RGBA com o fundo transparente.

O índice 0 da paleta é o fundo. A imagem fica 64x64; a página a mostra em 2x (128 px), pixelada.
Uso: python3 tools/site/professor.py [saida.png]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ORIGEM = Path("graphics/trainers/front_pics/professor_oak_front_pic.png")
DESTINO = Path("site/assets/oak.png")


def converter(origem: Path) -> Image.Image:
    fonte = Image.open(origem)
    if fonte.mode != "P":
        raise ValueError(f"{origem}: esperado PNG indexado, veio {fonte.mode}")
    rgba = fonte.convert("RGB").convert("RGBA")
    alfa = Image.fromarray(np.where(np.array(fonte) == 0, 0, 255).astype(np.uint8))
    rgba.putalpha(alfa)
    return rgba


def gerar(repo: Path, destino: Path) -> None:
    converter(Path(repo) / ORIGEM).save(destino, optimize=True)


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[2]
    gerar(raiz, Path(sys.argv[1]) if len(sys.argv) > 1 else raiz / DESTINO)
