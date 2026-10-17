"""Expectativas da taxa de shiny (puro Python, sem emulador).

Cada Pokémon criado com o jogador como treinador original sorteia a personalidade
1 + SHINY_BASE_REROLLS vezes (2) sem o Shiny Charm e 1 + SHINY_CHARM_REROLLS vezes (4) com
ele; cada sorteio é shiny com chance SHINY_ODDS/65536 = 1/8192.
"""

import math
import re

import pytest

from esteira.scenarios import REPO_ROOT
from esteira.scenarios.full_shiny import (ATTEMPTS_NO_CHARM, ATTEMPTS_WITH_CHARM,
                                          COLOR_PAIRS, SHINY_SAMPLES, expected_shinies,
                                          is_shiny_original, shiny_interval)


def test_sample_size_and_attempts():
    assert SHINY_SAMPLES == 200_000
    assert ATTEMPTS_NO_CHARM == 2
    assert ATTEMPTS_WITH_CHARM == 4


def test_expected_without_charm():
    n = 200_000
    mean = n * (1 - (1 - 1 / 8192) ** 2)
    assert expected_shinies(n, 2) == pytest.approx(mean)
    assert expected_shinies(n, 2) == pytest.approx(48.8, abs=0.05)
    sigma = math.sqrt(n * (mean / n) * (1 - mean / n))
    lo, hi = shiny_interval(n, 2)
    assert lo == pytest.approx(mean - 3 * sigma)
    assert hi == pytest.approx(mean + 3 * sigma)
    assert lo == pytest.approx(27.9, abs=0.1)
    assert hi == pytest.approx(69.8, abs=0.1)


def test_expected_with_charm():
    n = 200_000
    mean = n * (1 - (1 - 1 / 8192) ** 4)
    assert expected_shinies(n, 4) == pytest.approx(mean)
    assert expected_shinies(n, 4) == pytest.approx(97.6, abs=0.05)
    sigma = math.sqrt(n * (mean / n) * (1 - mean / n))
    lo, hi = shiny_interval(n, 4)
    assert lo == pytest.approx(mean - 3 * sigma)
    assert hi == pytest.approx(mean + 3 * sigma)
    assert lo == pytest.approx(68.0, abs=0.1)
    assert hi == pytest.approx(127.2, abs=0.1)


def test_charm_interval_is_above_no_charm_mean():
    lo_charm, _ = shiny_interval(SHINY_SAMPLES, ATTEMPTS_WITH_CHARM)
    assert lo_charm > expected_shinies(SHINY_SAMPLES, ATTEMPTS_NO_CHARM)


def test_original_shiny_formula_threshold_is_8():
    assert is_shiny_original(0x00000000, 0x00000007)
    assert not is_shiny_original(0x00000000, 0x00000008)
    # hi(ot) ^ lo(ot) ^ hi(pid) ^ lo(pid) = 0x1234 ^ 0x1234 ^ 0xABCD ^ 0xABCA = 7
    assert is_shiny_original(0xABCDABCA, 0x12341234)
    assert not is_shiny_original(0xABCDABC5, 0x12341234)  # = 8


def test_color_pairs_are_fixed_and_cover_both_colors():
    assert len(COLOR_PAIRS) == 1000
    assert len(set(COLOR_PAIRS)) == 1000
    assert all(0 <= pid < 2 ** 32 and 0 <= ot < 2 ** 32 for pid, ot in COLOR_PAIRS)
    shiny = sum(is_shiny_original(pid, ot) for pid, ot in COLOR_PAIRS)
    assert 100 <= shiny <= 900, f"{shiny} pares shiny: os dois lados do limite precisam aparecer"
    values = {(ot >> 16) ^ (ot & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF) for pid, ot in COLOR_PAIRS}
    assert {7, 8} <= values, "a fronteira do limite (7 shiny, 8 não) tem que estar coberta"


def test_header_matches_the_fixed_values():
    text = (REPO_ROOT / "include" / "constants" / "pokemon.h").read_text(encoding="utf-8")

    def define(name: str) -> int:
        m = re.search(rf"^#define {name}\s+(\d+)", text, re.M)
        assert m, f"{name} não encontrado em include/constants/pokemon.h"
        return int(m.group(1))

    assert define("SHINY_ODDS") == 8
    assert 1 + define("SHINY_BASE_REROLLS") == ATTEMPTS_NO_CHARM
    assert 1 + define("SHINY_CHARM_REROLLS") == ATTEMPTS_WITH_CHARM
