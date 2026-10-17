"""Leitura do estado do jogo no emulador, até a tela de título."""

from pathlib import Path

import pytest

from esteira.charmap import Charmap
from esteira.constants import Constants
from esteira.emu import Emulator
from esteira.game import Game
from esteira.symbols import Symbols

REPO_ROOT = Path(__file__).resolve().parents[2]
ELF = REPO_ROOT / "pokefirered_switch.elf"
EWRAM = (0x02000000, 0x0203FFFF)


@pytest.fixture(scope="module")
def syms():
    if not ELF.is_file():
        pytest.skip(f"ELF não encontrado: {ELF}")
    return Symbols.from_elf(str(ELF))


def test_symbols_player_party_in_ewram(syms):
    assert EWRAM[0] <= syms.addr("gPlayerParty") <= EWRAM[1]
    assert syms.name_at(syms.addr("gPlayerParty")) == "gPlayerParty"
    assert syms.name_at(0x12345678) is None


def test_game_at_title_screen(rom_path, tmp_save, syms):
    consts = Constants.load(str(REPO_ROOT))
    charmap = Charmap.load(str(REPO_ROOT))
    with Emulator(rom_path, tmp_save) as emu:
        game = Game(emu, syms, consts, charmap)
        total = 0
        # a tela de título aparece perto do quadro 2100; espera por condição, com teto
        while "TitleScreen" not in game.callback2() and total < 6000:
            emu.frames(60)
            total += 60
        assert "TitleScreen" in game.callback2(), f"callback2={game.callback2()!r}"
        assert game.in_battle() is False
        assert game.options_text_speed() in (0, 1, 2)
        assert isinstance(game.text_printer_active(0), bool)
        assert game.party() == [] or all(m.species >= 0 for m in game.party())
