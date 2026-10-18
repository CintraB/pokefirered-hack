"""Glifos ã õ Ã Õ: charmap, larguras e desenho nas quatro fontes latinas (Hack 7, Task 0)."""

import re
from pathlib import Path

import pytest
from PIL import Image

from esteira.charmap import Charmap
from esteira.check_text import _load_env
from esteira.font_render import FONTS, glyph_cell, glyph_widths, render_text

REPO = Path(__file__).resolve().parents[2]
NOVOS = {"ã": "a", "õ": "o", "Ã": "A", "Õ": "O"}
MAIUSCULAS = {"Ã", "Õ"}
# fonte (PNG) -> tabelas de largura de src/text.c que a usam
TABELAS = {
    "normal": ("sFontNormalLatinGlyphWidths", "sFontNormalCopy1LatinGlyphWidths"),
    "male": ("sFontMaleLatinGlyphWidths",),
    "female": ("sFontFemaleLatinGlyphWidths",),
    "small": ("sFontSmallLatinGlyphWidths",),
}
CONTROLE = {0x00, 0xF7, 0xF8, 0xF9, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF}
INK = (1, 2)  # índices 4bpp de texto e sombra; 0 = fora do glifo, 3 = fundo da caixa


@pytest.fixture(scope="module")
def charmap() -> Charmap:
    return Charmap.load(str(REPO))


def _code(charmap: Charmap, ch: str) -> int:
    data = charmap.encode(ch)
    assert len(data) == 1
    return data[0]


def _latin_entries() -> list[tuple[str, int]]:
    """(nome, byte) de toda entrada de um byte só antes do bloco japonês."""
    out = []
    for line in (REPO / "charmap.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("@ Hiragana"):
            break
        m = re.match(r"^(\S+)\s*=\s*([0-9A-Fa-f]{2})\s*(?:@.*)?$", line.strip())
        if m:
            out.append((m.group(1), int(m.group(2), 16)))
    return out


def _ink_rows(cell: list[list[int]]) -> list[int]:
    return [y for y, row in enumerate(cell) if any(p in INK for p in row)]


def _diff_rows(a: list[list[int]], b: list[list[int]]) -> list[int]:
    return [y for y in range(len(a)) if a[y] != b[y]]


def test_quatro_caracteres_com_bytes_unicos_e_livres(charmap):
    codes = {ch: _code(charmap, ch) for ch in NOVOS}
    assert len(set(codes.values())) == 4
    entries = _latin_entries()
    for ch, code in codes.items():
        donos = [n for n, b in entries if b == code]
        assert donos == [f"'{ch}'"], f"byte {code:02X} tem outros donos: {donos}"
        assert code not in CONTROLE
    # o resto do charmap não reutiliza esses bytes em sequências (macros de vários bytes)
    texto = (REPO / "charmap.txt").read_text(encoding="utf-8").split("@ Hiragana")[0]
    for line in texto.splitlines():
        m = re.match(r"^\S+\s*=\s*((?:[0-9A-Fa-f]{2}\s*){2,})", line)
        if m:
            usados = {int(b, 16) for b in m.group(1).split()}
            assert not usados & set(codes.values()), line


def test_bytes_novos_nao_colidem_com_os_codigos_do_braille():
    header = (REPO / "include" / "characters.h").read_text(encoding="utf-8")
    braille = {int(v, 16) for v in re.findall(r"#define BRAILLE_CHAR_\w+\s+(0x[0-9A-Fa-f]+)", header)}
    charmap = Charmap.load(str(REPO))
    assert not {_code(charmap, ch) for ch in NOVOS} & braille


def test_encode_decode(charmap):
    data = charmap.encode("Manhã não Ã Õ õ")
    assert charmap.decode(data + b"\xFF") == "Manhã não Ã Õ õ"


@pytest.mark.parametrize("fonte", FONTS)
def test_largura_igual_a_da_letra_base(charmap, fonte):
    for tabela in TABELAS[fonte]:
        widths = glyph_widths(REPO, tabela)
        assert len(widths) >= 0x100
        for ch, base in NOVOS.items():
            assert widths[_code(charmap, ch)] == widths[_code(charmap, base)], (tabela, ch)


@pytest.mark.parametrize("fonte", FONTS)
def test_pixels_so_diferem_da_base_nas_linhas_do_til(charmap, fonte):
    for ch, base in NOVOS.items():
        glifo = glyph_cell(REPO, fonte, _code(charmap, ch))
        letra = glyph_cell(REPO, fonte, _code(charmap, base))
        diff = _diff_rows(glifo, letra)
        assert diff, f"{ch} igual a {base} em {fonte}"
        # o til fica acima de toda a tinta da letra base
        assert max(diff) < min(_ink_rows(letra)), (fonte, ch, diff)
        # e é desenhado com a cor de texto
        assert any(p == 1 for y in diff for p in glifo[y]), (fonte, ch)


@pytest.mark.parametrize("fonte", FONTS)
def test_til_ocupa_as_mesmas_linhas_do_circunflexo(charmap, fonte):
    for ch, base, circ in (("ã", "a", "â"), ("õ", "o", "ô"), ("Ã", "A", "Â"), ("Õ", "O", "Ô")):
        letra = glyph_cell(REPO, fonte, _code(charmap, base))
        til = _diff_rows(glyph_cell(REPO, fonte, _code(charmap, ch)), letra)
        # só acima da letra: o ô da fonte small tem um pixel solto na linha 8, herdado do pret
        cir = [y for y in _diff_rows(glyph_cell(REPO, fonte, _code(charmap, circ)), letra)
               if y < min(_ink_rows(letra))]
        assert til == cir, (fonte, ch, til, cir)


@pytest.mark.parametrize("fonte", FONTS)
def test_minusculas_e_maiusculas_diferem(charmap, fonte):
    for a, b in (("ã", "õ"), ("Ã", "Õ"), ("ã", "Ã"), ("õ", "Õ")):
        assert glyph_cell(REPO, fonte, _code(charmap, a)) != glyph_cell(REPO, fonte, _code(charmap, b))


def test_fontes_normal_male_female_iguais():
    base = (REPO / "graphics" / "fonts" / "latin_normal.png").read_bytes()
    assert (REPO / "graphics" / "fonts" / "latin_male.png").read_bytes() == base
    assert (REPO / "graphics" / "fonts" / "latin_female.png").read_bytes() == base


def test_check_text_mede_os_novos_como_a_letra_base():
    env = _load_env(REPO)
    for ch, base in NOVOS.items():
        assert ch in env.chars
        assert env.latin_width[ch] == env.latin_width[base]


@pytest.mark.parametrize("fonte", FONTS)
def test_render_mede_a_soma_das_larguras(charmap, fonte):
    tabela = TABELAS[fonte][0]
    widths = glyph_widths(REPO, tabela)
    texto = "Manhã não"
    img = render_text(REPO, texto, fonte)
    assert isinstance(img, Image.Image)
    assert img.width == sum(widths[b] for b in charmap.encode(texto))
