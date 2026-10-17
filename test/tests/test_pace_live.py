"""Cronômetro de passos ao vivo: andar a 11 e correr a 5 quadros/tile.

Como é teste unitário e não cenário da esteira, liga FLAG_SYS_B_DASH escrevendo na RAM
(o roteiro de verdade só ganha o tênis em Pewter; o Task 11 usa o mesmo helper lá).
"""

from pathlib import Path

import pytest

from esteira.game import SB1_FLAGS
from esteira.scenarios import open_context
from esteira.scenarios.pace import (RUN_FRAMES_PER_TILE, WALK_FRAMES_PER_TILE,
                                    measure_frames_per_tile, measure_run_frames_per_tile)
from esteira.scenarios.quick_opening import run_opening

REPO_ROOT = Path(__file__).resolve().parents[2]
ELF = REPO_ROOT / "pokefirered_switch.elf"


def _set_flag(game, flag_id: int) -> None:
    emu = game.emu
    addr = emu.read_u32(game.syms.addr("gSaveBlock1Ptr")) + SB1_FLAGS + flag_id // 8
    emu.write(addr, bytes([emu.read_u8(addr) | (1 << (flag_id % 8))]))


@pytest.fixture(scope="module")
def pallet(tmp_path_factory):
    rom = REPO_ROOT / "pokefirered_switch.gba"
    if not rom.is_file() or not ELF.is_file():
        pytest.skip("ROM/ELF da Switch não compilados")
    out = tmp_path_factory.mktemp("passos")
    with open_context(str(rom), str(ELF), str(out), "CHARMANDER") as ctx:
        run_opening(ctx)
        assert not ctx.suite.failed(), [r for r in ctx.suite.results if r.status == "falha"]
        assert ctx.nav.walk_to(6, 11)
        assert ctx.nav.go_through_warp("down") == ctx.consts.map("MAP_PALLET_TOWN")
        assert ctx.nav.walk_to(15, 9)       # linha 9 de Pallet: livre de x=2 a x=21
        yield ctx


def test_walk_and_run_frames_per_tile(pallet):
    ctx = pallet
    flag = ctx.consts.flag("FLAG_SYS_B_DASH")
    assert not ctx.game.flag(flag)
    with pytest.raises(AssertionError, match="FLAG_SYS_B_DASH"):
        measure_run_frames_per_tile(ctx, "left")

    walk = measure_frames_per_tile(ctx, "left")
    assert walk == [WALK_FRAMES_PER_TILE] * 5

    _set_flag(ctx.game, flag)
    assert ctx.game.flag(flag)
    run = measure_run_frames_per_tile(ctx, "right")
    assert run == [RUN_FRAMES_PER_TILE] * 5
    assert ctx.game.player_xy() == (15, 9)   # 6 tiles para a esquerda e 6 de volta
