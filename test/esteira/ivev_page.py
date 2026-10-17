"""Hack 5: a página IVs/EVs do resumo do Pokémon (5ª página, depois de EVOLUTION).

O jogo monta o texto em `GetIvEvPageText` (src/pokemon_summary_screen.c): 8 linhas, com as
colunas postas por códigos {SKIP x} (FC 12 x: o cursor vai para x px do início do texto).
Este módulo calcula, de forma independente, os valores (nível de cada IV, total, %, avaliação
geral, Hidden Power) e o texto ESPERADO, byte a byte, para comparar com o da build de teste
(hooks.Mailbox.ivev_text). Design: docs/superpowers/specs/2026-10-17-pagina-ivs-evs-design.md.

    IV TOTAL 161/186     87%   Outstanding
    HP          31 Perfect           EV 252
    ATTACK      28 Excellent         EV   0
    ...                              (SP. ATK, SP. DEF, SPEED)
    HIDDEN POWER FIRE 70             EV 510/510

IVs e EVs aqui vão na ordem da página: HP, ATTACK, DEFENSE, SP. ATK, SP. DEF, SPEED.
"""

import re
from pathlib import Path

from .charmap import Charmap
from .check_text import _load_widths

STATS = ("HP", "ATTACK", "DEFENSE", "SP. ATK", "SP. DEF", "SPEED")
MAX_IV, MAX_TOTAL_IVS, MAX_EV, MAX_TOTAL_EVS = 31, 186, 255, 510
IV_GRADES = ((31, "Perfect"), (26, "Excellent"), (16, "Very good"), (1, "Good"), (0, "Poor"))
TOTAL_GRADES = ((186, "Perfect"), (151, "Outstanding"), (121, "Above average"), (91, "Average"),
                (0, "Below average"))

# Colunas (px desde o início do texto; IVEV_COL_* em src/pokemon_summary_screen.c)
COL_IV_END, COL_GRADE, COL_PERCENT, COL_OVERALL, COL_EV, COL_EV_END = 66, 72, 106, 136, 144, 182
# Janela: sWindowTemplates_Ivs[0] .width = 28 tiles, texto em x = IVEV_PAGE_TEXT_X = 2;
# 14 tiles de altura = 8 linhas de 14 px
WINDOW_WIDTH_PX = 28 * 8
TEXT_X = 2
LINE_WIDTH_PX = WINDOW_WIDTH_PX - TEXT_X
LINES = 8

# Ordem dos tipos de Hidden Power (TYPE_* de include/constants/pokemon.h)
NUMBER_OF_MON_TYPES, TYPE_MYSTERY = 18, 9
TYPE_NAMES_C = Path("src/battle_main.c")
SOURCE_FILES = (TYPE_NAMES_C, Path("charmap.txt"), Path("src/text.c"))

SKIP = bytes([0xFC, 0x12])
NEWLINE, EOS = 0xFE, 0xFF

# Cenário `resumo_ivs` (scenarios/full_summary_ivs.py): o time de teste (slots 0-4; o 5 é um
# ovo) com IVs e EVs escolhidos, e a tela da página de cada um em OUT/telas/resumo_ivs_<n>.png
SHOWCASE = (
    # espécie, IVs (ordem da página), EVs (ordem da página)
    ("SPECIES_MEWTWO", (31, 31, 31, 31, 31, 31), (252, 0, 0, 252, 6, 0)),       # 100% Perfect, 510
    ("SPECIES_MAGIKARP", (0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0)),             # 0% Below average
    ("SPECIES_EEVEE", (25, 26, 15, 16, 1, 30), (10, 20, 30, 40, 50, 60)),     # limites 25/26, 15/16
    ("SPECIES_CHARIZARD", (30, 31, 30, 30, 31, 31), (0, 252, 0, 6, 0, 252)),  # Hidden Power 70
    ("SPECIES_TAUROS", (20, 20, 20, 20, 20, 20), (85, 85, 85, 85, 85, 85)),   # 120 = Average
)
SCREEN_POINTS = tuple(f"resumo_ivs_{s.removeprefix('SPECIES_').lower()}" for s, _, _ in SHOWCASE)


def iv_grade(iv: int) -> str:
    return next(name for low, name in IV_GRADES if iv >= low)


def total_grade(total: int) -> str:
    return next(name for low, name in TOTAL_GRADES if total >= low)


def percent(total: int) -> int:
    """soma ÷ 186 × 100, arredondado para o inteiro mais próximo (meio para cima)."""
    return (total * 200 + MAX_TOTAL_IVS) // (MAX_TOTAL_IVS * 2)


def hidden_power(ivs: tuple[int, ...]) -> tuple[int, int]:
    """(tipo, poder) do Gen 3, como Cmd_hiddenpowercalc: bits dos IVs na ordem HP, Atk, Def,
    Spe, SpA, SpD (a da batalha, não a da página)."""
    hp, atk, df, spa, spd, spe = ivs
    order = (hp, atk, df, spe, spa, spd)
    power_bits = sum(((iv >> 1) & 1) << i for i, iv in enumerate(order))
    type_bits = sum((iv & 1) << i for i, iv in enumerate(order))
    power = 40 * power_bits // 63 + 30
    type_ = (NUMBER_OF_MON_TYPES - 3) * type_bits // 63 + 1
    if type_ >= TYPE_MYSTERY:
        type_ += 1
    return type_, power


def load_type_names(repo: Path) -> list[str]:
    text = (Path(repo) / TYPE_NAMES_C).read_text(encoding="utf-8")
    body = re.search(r"gTypeNames\[NUMBER_OF_MON_TYPES\]\[TYPE_NAME_LENGTH \+ 1\] =\s*\{(.*?)\};",
                     text, re.S).group(1)
    names = re.findall(r'_\("([^"]*)"\)', body)
    assert len(names) == NUMBER_OF_MON_TYPES, names
    return names


class IvEvPage:
    """Texto esperado da página (bytes do jogo) e medidas."""

    def __init__(self, repo: Path):
        self.repo = Path(repo)
        self.charmap = Charmap.load(str(self.repo))
        self.widths = _load_widths(self.repo)
        self.type_names = load_type_names(self.repo)

    def _enc(self, text: str) -> bytes:
        return self.charmap.encode(text)

    def width(self, text: str) -> int:
        return sum(self.widths[b] for b in self._enc(text))

    def _right(self, number: int, right_x: int) -> bytes:
        text = str(number)
        return SKIP + bytes([right_x - self.width(text)]) + self._enc(text)

    def lines(self, ivs: tuple[int, ...], evs: tuple[int, ...]) -> list[bytes]:
        total = sum(ivs)
        hp_type, hp_power = hidden_power(ivs)
        lines = [self._enc(f"IV TOTAL {total}/{MAX_TOTAL_IVS}") + SKIP + bytes([COL_PERCENT])
                 + self._enc(f"{percent(total)}%") + SKIP + bytes([COL_OVERALL])
                 + self._enc(total_grade(total))]
        for name, iv, ev in zip(STATS, ivs, evs):
            lines.append(self._enc(name) + self._right(iv, COL_IV_END) + SKIP + bytes([COL_GRADE])
                         + self._enc(iv_grade(iv)) + SKIP + bytes([COL_EV]) + self._enc("EV")
                         + self._right(ev, COL_EV_END))
        lines.append(self._enc(f"HIDDEN POWER {self.type_names[hp_type]} {hp_power}")
                     + SKIP + bytes([COL_EV]) + self._enc("EV") + self._right(sum(evs), COL_EV_END)
                     + self._enc(f"/{MAX_TOTAL_EVS}"))
        return lines

    def text(self, ivs: tuple[int, ...], evs: tuple[int, ...]) -> bytes:
        return bytes([NEWLINE]).join(self.lines(ivs, evs))

    def line_widths(self, data: bytes) -> list[int]:
        """Até onde cada linha vai (px): {SKIP x} põe o cursor em x."""
        widths, x, right, i = [], 0, 0, 0
        while i < len(data) and data[i] != EOS:
            b = data[i]
            if b == NEWLINE:
                widths.append(right)
                x = right = 0
            elif data[i:i + 2] == SKIP:
                x = data[i + 2]
                i += 2
            else:
                x += self.widths[b]
                right = max(right, x)
            i += 1
        widths.append(right)
        return widths

    def overlaps(self, data: bytes) -> list[str]:
        """Textos que um {SKIP} faria escrever por cima do anterior (coluna apertada)."""
        bad, x, line, i = [], 0, 0, 0
        while i < len(data) and data[i] != EOS:
            if data[i] == NEWLINE:
                x, line = 0, line + 1
            elif data[i:i + 2] == SKIP:
                if data[i + 2] < x:
                    bad.append(f"linha {line}: SKIP para {data[i + 2]} com o texto já em {x}")
                x = data[i + 2]
                i += 2
            else:
                x += self.widths[data[i]]
            i += 1
        return bad

    def decode(self, data: bytes) -> str:
        out, i = [], 0
        while i < len(data) and data[i] != EOS:
            if data[i:i + 2] == SKIP:
                out.append(f"{{SKIP {data[i + 2]}}}")
                i += 3
                continue
            out.append(" / " if data[i] == NEWLINE else self.charmap.decode(bytes([data[i]])))
            i += 1
        return "".join(out)


def worst_cases() -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """IVs/EVs que exercitam cada texto possível (níveis, avaliação geral, tipo do Hidden Power) e
    os números mais largos, para a checagem de largura."""
    cases = [((iv,) * 6, (255, 255, 0, 0, 0, 0)) for iv in (0, 1, 15, 16, 25, 26, 30, 31)]
    cases += [((t, 31, 31, 31, 31, 31), (252, 252, 6, 0, 0, 0)) for t in range(0, 32)]
    for bits in range(64):        # todos os tipos de Hidden Power, com poder 70 (2º bit ligado)
        cases.append((tuple(2 | ((bits >> i) & 1) | 28 for i in range(6)), (255,) * 2 + (0,) * 4))
    return cases


def check_page_widths(repo: Path) -> list[tuple[str, int]]:
    """(linha, px) de toda linha mais larga que a janela, ou com colunas encavaladas."""
    page = IvEvPage(repo)
    wide = []
    for ivs, evs in worst_cases():
        data = page.text(ivs, evs)
        for line, px in zip(data.split(bytes([NEWLINE])), page.line_widths(data)):
            if px > LINE_WIDTH_PX:
                wide.append((page.decode(line), px))
        wide += [(problem, 0) for problem in page.overlaps(data)]
    return sorted(set(wide))
