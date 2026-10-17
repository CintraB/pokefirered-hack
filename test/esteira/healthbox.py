"""HP mostrado no healthbox do jogador (batalha simples), lido da VRAM de sprites.

É o número que está na tela, não a conta do jogo: decodifica os pixels com os glifos da
fonte do repo, sem reimplementar a animação da barra.

De onde vem cada número (nada adivinhado):
- src/battle_interface.c UpdateHpTextInHealthbox (jogador, simples, HP_CURRENT): o valor
  vira 3 caracteres alinhados à direita + '/', impresso com FONT_SMALL em x=4, y=5 numa
  janela de 8x2 tiles (sHealthboxWindowTemplate); TextIntoHealthboxObject copia a coluna 0
  da janela para tileNum*32 + 0x2E0 e as colunas 1-2 para + 0xA00 (a linha de baixo da
  janela fica 256 bytes adiante; da linha de cima só as linhas de pixel 5-7);
- cores de AddTextPrinterAndCreateWindowOnHealthbox: fundo 2, texto 1, sombra 3;
- glifos: graphics/fonts/latin_small.png (células 8x16, 32 por linha, índice 1 = texto),
  larguras em sFontSmallLatinGlyphWidths (src/text.c), códigos em charmap.txt.
"""

import re
from pathlib import Path

from PIL import Image

from .charmap import Charmap

REPO_ROOT = Path(__file__).resolve().parents[2]

OBJ_VRAM0 = 0x06010000
TILE_SIZE_4BPP = 32
SPRITE_SIZE = 0x44             # sizeof(struct Sprite) (nm: gSprites = 0x1144 = 65 * 0x44)
SPRITE_OAM_ATTR2 = 0x04        # OamData.tileNum:10 nos bits baixos do u16 em +4
HP_TEXT_DEST = (0x2E0, 0xA00, 0xA20)   # destino das colunas 0, 1 e 2 da janela
TILE_ROW_STRIDE = 256          # linha de baixo da janela/sprite (8 tiles adiante)
WINDOW_COLUMNS = len(HP_TEXT_DEST)
WINDOW_HEIGHT = 16
HP_TEXT_X, HP_TEXT_Y = 4, 5
HP_CHARS = 3                   # ConvertIntToDecimalStringN(..., STR_CONV_MODE_RIGHT_ALIGN, 3)
TEXT_COLOR = 1

FONT_CELL_W, FONT_CELL_H, FONT_CELLS_PER_ROW = 8, 16, 32
FONT_TEXT_INDEX = 1
HP_CHARSET = " 0123456789"

_WIDTHS = re.compile(r"sFontSmallLatinGlyphWidths\[\]\s*=\s*\{([^}]*)\}", re.S)


def load_hp_glyphs(repo: Path = REPO_ROOT) -> dict[str, tuple[int, tuple[tuple[int, ...], ...]]]:
    """caractere -> (largura, máscara do texto nas linhas visíveis), para espaço e dígitos."""
    repo = Path(repo)
    widths = [int(v) for v in re.findall(r"\d+", _WIDTHS.search(
        (repo / "src" / "text.c").read_text(encoding="utf-8")).group(1))]
    charmap = Charmap.load(str(repo))
    rows = WINDOW_HEIGHT - HP_TEXT_Y     # linhas do glifo que cabem na janela
    glyphs = {}
    with Image.open(repo / "graphics" / "fonts" / "latin_small.png") as img:
        for ch in HP_CHARSET:
            code = charmap.encode(ch)[0]
            width = widths[code]
            cx = (code % FONT_CELLS_PER_ROW) * FONT_CELL_W
            cy = (code // FONT_CELLS_PER_ROW) * FONT_CELL_H
            mask = tuple(tuple(int(img.getpixel((cx + x, cy + y)) == FONT_TEXT_INDEX)
                               for x in range(width)) for y in range(rows))
            glyphs[ch] = (width, mask)
    return glyphs


def decode_hp_pixels(pixels: list[list[int]],
                     glyphs: dict[str, tuple[int, tuple[tuple[int, ...], ...]]]) -> int | None:
    """Lê os 3 caracteres da janela (linhas x colunas de cores 4bpp); None se não reconhecer."""
    x, text = HP_TEXT_X, ""
    for _ in range(HP_CHARS):
        for ch, (width, mask) in glyphs.items():
            if x + width > len(pixels[0]):
                continue
            cell = tuple(tuple(int(pixels[HP_TEXT_Y + y][x + dx] == TEXT_COLOR)
                               for dx in range(width)) for y in range(len(mask)))
            if cell == mask:
                text += ch
                x += width
                break
        else:
            return None
    text = text.strip()
    return int(text) if text.isdigit() else None


class HealthboxReader:
    def __init__(self, emu, syms, repo: Path = REPO_ROOT):
        self.emu = emu
        self.syms = syms
        self.glyphs = load_hp_glyphs(repo)

    def _window_pixels(self) -> list[list[int]]:
        sprite_id = self.emu.read_u8(self.syms.addr("gHealthboxSpriteIds"))   # battler 0
        attr2 = self.emu.read_u16(self.syms.addr("gSprites") + sprite_id * SPRITE_SIZE
                                  + SPRITE_OAM_ATTR2)
        base = OBJ_VRAM0 + (attr2 & 0x3FF) * TILE_SIZE_4BPP
        pixels = [[0] * (WINDOW_COLUMNS * 8) for _ in range(WINDOW_HEIGHT)]
        for col, dest in enumerate(HP_TEXT_DEST):
            for tile_row in (0, 1):
                data = self.emu.read(base + dest + tile_row * TILE_ROW_STRIDE, TILE_SIZE_4BPP)
                for i, byte in enumerate(data):
                    y, x = tile_row * 8 + i // 4, col * 8 + (i % 4) * 2
                    pixels[y][x] = byte & 0xF
                    pixels[y][x + 1] = byte >> 4
        return pixels

    def player_hp(self) -> int | None:
        """HP atual mostrado no healthbox do jogador (None se os pixels não forem um número)."""
        return decode_hp_pixels(self._window_pixels(), self.glyphs)
