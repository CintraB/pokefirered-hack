"""POK-53: a ROM passa a ter 32 MB para caber os sprites dos 386 seguidores."""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def test_makefile_pad_32mb():
    texto = (RAIZ / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"--pad-to 0xA000000\b", texto)


def test_rom_tem_32mb():
    rom = RAIZ / "pokefirered_switch.gba"
    if not rom.exists():
        pytest.skip("ROM não compilada")
    assert rom.stat().st_size == 32 * 1024 * 1024
