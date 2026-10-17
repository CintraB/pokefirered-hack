"""HP mostrado no healthbox do jogador, decodificado da VRAM de sprites."""

import pytest

from esteira.healthbox import (
    HP_TEXT_DEST,
    OBJ_VRAM0,
    SPRITE_SIZE,
    TILE_ROW_STRIDE,
    HealthboxReader,
    decode_hp_pixels,
    load_hp_glyphs,
)

# Janela de texto do HP atual (24x16 px, cores 4bpp) copiada da VRAM numa batalha real na
# Rota 1 com o CHARMANDER em 21/21 HP: " 21/" em FONT_SMALL, x=4, y=5. As linhas 0-4 são
# fundo (2); texto = 1, sombra = 3.
REAL_21 = [
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222222",
    "222222222222222222222213",
    "222222222211322213222213",
    "222222222133132113222133",
    "222222222322132313222132",
    "222222222221322213221332",
    "222222222213222213221322",
    "222222222132222213213322",
    "222222222111132111313222",
]


def _grid(rows: list[str]) -> list[list[int]]:
    return [[int(ch, 16) for ch in row] for row in rows]


@pytest.fixture(scope="module")
def glyphs():
    return load_hp_glyphs()


def test_glyphs_cover_space_and_digits(glyphs):
    assert set(glyphs) == set(" 0123456789")
    assert all(width == 5 for width, _mask in glyphs.values())   # sFontSmallLatinGlyphWidths


def test_decodes_real_vram_dump(glyphs):
    assert decode_hp_pixels(_grid(REAL_21), glyphs) == 21


def test_unknown_glyph_is_none(glyphs):
    grid = _grid(REAL_21)
    grid[12][10] = 1        # um pixel de texto a mais dentro do '2'
    assert decode_hp_pixels(grid, glyphs) is None


def test_blank_window_is_none(glyphs):
    assert decode_hp_pixels([[2] * 24 for _ in range(16)], glyphs) is None


class FakeEmu:
    def __init__(self, mem: dict[int, int]):
        self.mem = mem

    def read(self, addr: int, n: int) -> bytes:
        return bytes(self.mem.get(addr + i, 0) for i in range(n))

    def read_u8(self, addr: int) -> int:
        return self.mem.get(addr, 0)

    def read_u16(self, addr: int) -> int:
        return self.read_u8(addr) | (self.read_u8(addr + 1) << 8)


class FakeSyms:
    ADDRS = {"gHealthboxSpriteIds": 0x03000000, "gSprites": 0x02000000}

    def addr(self, name: str) -> int:
        return self.ADDRS[name]


def _vram_with_window(rows: list[str], sprite_id: int, tile_num: int) -> dict[int, int]:
    """Põe a janela nos tiles do healthbox como TextIntoHealthboxObject faria."""
    grid = _grid(rows)
    mem: dict[int, int] = {FakeSyms.ADDRS["gHealthboxSpriteIds"]: sprite_id}
    oam_attr2 = FakeSyms.ADDRS["gSprites"] + sprite_id * SPRITE_SIZE + 4
    mem[oam_attr2] = tile_num & 0xFF
    mem[oam_attr2 + 1] = (tile_num >> 8) & 0x03
    base = OBJ_VRAM0 + tile_num * 32
    for col, dest in enumerate(HP_TEXT_DEST):
        for tile_row in (0, 1):
            tile = base + dest + tile_row * TILE_ROW_STRIDE
            for y in range(8):
                for x in range(0, 8, 2):
                    lo = grid[tile_row * 8 + y][col * 8 + x]
                    hi = grid[tile_row * 8 + y][col * 8 + x + 1]
                    mem[tile + y * 4 + x // 2] = lo | (hi << 4)
    return mem


def test_reader_finds_window_through_healthbox_sprite():
    mem = _vram_with_window(REAL_21, sprite_id=3, tile_num=0x123)
    reader = HealthboxReader(FakeEmu(mem), FakeSyms())
    assert reader.player_hp() == 21
