"""Primitivas de controle: tempo-limite com evidência, Suite/Result e símbolos usados."""

from pathlib import Path

import pytest

from esteira.charmap import Charmap
from esteira.constants import Constants
from esteira.control import Controller
from esteira.emu import Emulator
from esteira.game import Game
from esteira.result import Result, Suite
from esteira.symbols import Symbols
from esteira.control import StepTimeout

REPO_ROOT = Path(__file__).resolve().parents[2]
ELF = REPO_ROOT / "pokefirered_switch.elf"


@pytest.fixture(scope="module")
def syms():
    if not ELF.is_file():
        pytest.skip(f"ELF não encontrado: {ELF}")
    return Symbols.from_elf(str(ELF))


@pytest.fixture
def live(rom_path, tmp_save, tmp_path, syms):
    consts = Constants.load(str(REPO_ROOT))
    charmap = Charmap.load(str(REPO_ROOT))
    with Emulator(rom_path, tmp_save) as emu:
        game = Game(emu, syms, consts, charmap)
        yield Controller(emu, game, str(tmp_path / "out")), game, emu


def test_wait_until_timeout_saves_evidence(live):
    ctl, _game, _emu = live
    with pytest.raises(StepTimeout) as info:
        ctl.wait_until(lambda: False, timeout=30, what="nunca acontece")
    exc = info.value
    assert exc.what == "nunca acontece"
    assert Path(exc.screenshot_path).is_file()
    assert Path(exc.state_path).is_file()
    assert "nunca acontece" in str(exc)


def test_wait_until_returns_frames_spent(live):
    ctl, game, _emu = live
    spent = ctl.wait_until(lambda: "TitleScreen" in game.callback2(), timeout=6000,
                           what="tela de título")
    assert 0 < spent <= 6000


def test_checkpoint_writes_state(live):
    ctl, _game, _emu = live
    path = ctl.checkpoint("inicio")
    assert Path(path).is_file()
    assert Path(path).parent.name == "estados" and Path(path).suffix == ".ss"


def test_restore_returns_to_checkpoint(live):
    ctl, _game, emu = live
    ctl.checkpoint("volta")
    at_checkpoint = emu.frames(0)
    emu.frames(50)
    ctl.restore("volta")
    assert emu.frames(0) == at_checkpoint
    with pytest.raises(FileNotFoundError):
        ctl.restore("nao-existe")


def test_advance_text_times_out_with_evidence(live):
    ctl, _game, _emu = live
    with pytest.raises(StepTimeout):
        ctl.advance_text(lambda: False, timeout=40)


def test_suite_marks_timeout_as_falha():
    suite = Suite()

    def boom():
        raise StepTimeout(what="algo", screenshot_path="a.png", state_path="a.ss")

    suite.run("cenario", boom)
    assert suite.failed()
    (res,) = suite.results
    assert res.name == "cenario" and res.status == "falha"
    assert "algo" in res.detail and "a.ss" in res.detail
    assert res.images == ["a.png"]


def test_suite_marks_assertion_as_falha_and_ok_passes():
    suite = Suite()
    suite.run("bom", lambda: None)
    assert not suite.failed()

    def bad():
        assert 1 == 2, "um não é dois"

    suite.run("ruim", bad)
    assert suite.failed()
    assert [r.status for r in suite.results] == ["ok", "falha"]
    assert "um não é dois" in suite.results[1].detail


def test_suite_aviso_does_not_fail():
    suite = Suite()
    suite.add(Result("x", "aviso", "cuidado"))
    assert not suite.failed()
    assert Result("y", "ok", "").images == []


def test_symbols_used_by_controller_exist(syms):
    for name in ("sGlobalScriptContextStatus", "sLockFieldControls", "gPlayerAvatar",
                 "gBattlerControllerFuncs", "gMain"):
        assert syms.addr(name)
    # funções estáticas com o mesmo nome em vários controladores: comparação é por nome
    assert syms.name_at(syms.addr("HandleInputChooseMove")) == "HandleInputChooseMove"
    assert syms.addr("CB2_Overworld")
