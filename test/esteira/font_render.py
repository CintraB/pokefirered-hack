"""Desenha texto do jogo com as fontes latinas do repo (PNG da fonte + larguras de src/text.c).

Serve para ver um texto como o jogo o imprime sem precisar de emulador: cada caractere vira o byte
do charmap.txt, a célula do glifo é recortada do PNG pelo índice e avança a largura da tabela.

Geometria (tools/gbagfx/font.c): normal/male/female = células 16x16, 16 por linha; small = células
8x16, 32 por linha. Cores 2bpp: 1 = texto, 2 = sombra; 0 e 3 = fundo.
"""

import re
from pathlib import Path

from PIL import Image

from .charmap import Charmap

# fonte -> (largura da célula, altura, células por linha, tabela de larguras de src/text.c)
GEOMETRY = {
    "normal": (16, 16, 16, "sFontNormalLatinGlyphWidths"),
    "male": (16, 16, 16, "sFontMaleLatinGlyphWidths"),
    "female": (16, 16, 16, "sFontFemaleLatinGlyphWidths"),
    "small": (8, 16, 32, "sFontSmallLatinGlyphWidths"),
}
FONTS = tuple(GEOMETRY)
LINE_HEIGHT = 16

# cor de cada índice 2bpp (gFontPalette de tools/gbagfx/font.c, com o fundo em branco)
_COLORS = {0: (255, 255, 255), 1: (0x38, 0x38, 0x38), 2: (0xD8, 0xD8, 0xD8), 3: (255, 255, 255)}


def glyph_widths(repo: Path, table: str) -> list[int]:
    """Larguras (px) de uma tabela `s*LatinGlyphWidths` de src/text.c, um valor por glifo."""
    source = (Path(repo) / "src" / "text.c").read_text(encoding="utf-8")
    m = re.search(rf"{table}\[\]\s*=\s*\{{(.*?)\}};", source, re.S)
    if not m:
        raise RuntimeError(f"{table} não encontrada em src/text.c")
    body = re.sub(r"/\*.*?\*/|//[^\n]*", "", m.group(1), flags=re.S)
    return [int(n) for n in re.findall(r"\d+", body)]


def glyph_cell(repo: Path, font: str, code: int) -> list[list[int]]:
    """Pixels (índices 0-3) da célula do glifo `code` no PNG da fonte, linha a linha."""
    cell_w, cell_h, per_row, _ = GEOMETRY[font]
    cx, cy = (code % per_row) * cell_w, (code // per_row) * cell_h
    with Image.open(Path(repo) / "graphics" / "fonts" / f"latin_{font}.png") as img:
        return [[img.getpixel((cx + x, cy + y)) for x in range(cell_w)] for y in range(cell_h)]


def render_text(repo: Path, text: str, font: str = "normal", scale: int = 1) -> Image.Image:
    """Uma linha de texto, fundo branco; largura = soma das larguras dos glifos."""
    repo = Path(repo)
    _, cell_h, _, table = GEOMETRY[font]
    widths = glyph_widths(repo, table)
    charmap = Charmap.load(str(repo))
    cells = [(glyph_cell(repo, font, code), widths[code]) for code in charmap.encode(text)]
    img = Image.new("RGB", (sum(w for _, w in cells), cell_h), _COLORS[0])
    x = 0
    for cell, width in cells:
        for y in range(cell_h):
            for dx in range(width):
                img.putpixel((x + dx, y), _COLORS[cell[y][dx]])
        x += width
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST) if scale > 1 else img


def render_lines(repo: Path, lines: list[tuple[str, str]], scale: int = 4, margin: int = 4) -> Image.Image:
    """Empilha linhas `(fonte, texto)` numa imagem só, ampliada por `scale`."""
    parts = [render_text(repo, text, font) for font, text in lines]
    width = max(p.width for p in parts) + 2 * margin
    height = len(parts) * LINE_HEIGHT + 2 * margin
    sheet = Image.new("RGB", (width, height), _COLORS[0])
    for i, part in enumerate(parts):
        sheet.paste(part, (margin, margin + i * LINE_HEIGHT))
    return sheet.resize((width * scale, height * scale), Image.NEAREST)
