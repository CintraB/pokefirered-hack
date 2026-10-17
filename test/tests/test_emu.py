"""Prova de viabilidade do runner headless do mGBA e do cliente Python."""

import os
from pathlib import Path

from esteira.emu import Emulator

REPO_ROOT = Path(__file__).resolve().parents[2]
IWRAM = 0x03000000
IWRAM_SIZE = 0x8000


def _saves_snapshot():
    saves = REPO_ROOT / "roms" / "saves"
    if not saves.is_dir():
        return {}
    return {p.name: p.stat().st_mtime_ns for p in saves.iterdir()}


def test_boot_reads_rom_title(rom_path, tmp_save):
    with Emulator(rom_path, tmp_save) as emu:
        assert emu.read(0x080000A0, 12) == b"POKEMON FIRE"


def test_reaches_title_screen_and_screenshot_not_blank(rom_path, tmp_save, tmp_path):
    with Emulator(rom_path, tmp_save) as emu:
        assert emu.frames(900) >= 900
        img = emu.screenshot(str(tmp_path / "title.png"))
    assert img.size == (240, 160)
    assert len(img.getcolors(maxcolors=240 * 160)) > 8


def test_state_roundtrip(rom_path, tmp_save, tmp_path):
    state = str(tmp_path / "roundtrip.ss")
    with Emulator(rom_path, tmp_save) as emu:
        emu.frames(600)
        emu.save_state(state)
        ram_at_save = emu.read(IWRAM, IWRAM_SIZE)

        emu.frames(60)
        assert emu.read(IWRAM, IWRAM_SIZE) != ram_at_save

        emu.load_state(state)
        assert emu.read(IWRAM, IWRAM_SIZE) == ram_at_save
        emu.frames(1)
        first = emu.screenshot(str(tmp_path / "a.png"))

        emu.load_state(state)
        emu.frames(1)
        second = emu.screenshot(str(tmp_path / "b.png"))

    assert first.tobytes() == second.tobytes()


def test_save_file_goes_to_given_path(rom_path, tmp_save):
    before = _saves_snapshot()
    emu = Emulator(rom_path, tmp_save)
    emu.frames(120)
    emu.close()
    assert os.path.isfile(tmp_save)
    assert _saves_snapshot() == before
