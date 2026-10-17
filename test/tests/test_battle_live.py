"""BattleDriver ao vivo numa batalha selvagem da Rota 1.

Parte do roteiro de abertura real (só botões) e, como é teste unitário e não cenário da
esteira, escreve na RAM para preparar o caso: Potion e Poké Balls na bolsa e HP baixo.
"""

import struct
from pathlib import Path

import pytest

from esteira.battle import BattleDriver
from esteira.emu import KEY_B
from esteira.scenarios import open_context
from esteira.scenarios.quick_opening import run_opening

REPO_ROOT = Path(__file__).resolve().parents[2]
ELF = REPO_ROOT / "pokefirered_switch.elf"
SB1_POCKET_ITEMS = 0x0310      # include/global.h (ver game.SB1_BAG_POCKETS)
SB1_POCKET_BALLS = 0x0430
SB2_ENCRYPTION_KEY = 0xF20
MON_HP = 0x56


def _give_item(game, pocket_offset: int, item: int, qty: int) -> None:
    emu, syms = game.emu, game.syms
    sb1 = emu.read_u32(syms.addr("gSaveBlock1Ptr"))
    key = emu.read_u32(emu.read_u32(syms.addr("gSaveBlock2Ptr")) + SB2_ENCRYPTION_KEY) & 0xFFFF
    emu.write(sb1 + pocket_offset, struct.pack("<HH", item, qty ^ key))


def _wild_battle(ctx) -> None:
    """Anda para cima e para baixo na grama da entrada da Rota 1 até uma batalha começar."""
    nav = ctx.nav
    for _ in range(200):
        for direction in ("up", "down"):
            nav.step(direction, 2)
            # encontro no último tile do passo trava os controles antes da transição:
            # step() informa "script" e a batalha só começa alguns quadros depois
            if nav.interrupted is not None:
                ctx.controller.wait_until(ctx.game.in_battle, 600, "início da batalha selvagem")
                return
    raise AssertionError("nenhum encontro selvagem na grama da Rota 1")


@pytest.fixture(scope="module")
def route1(tmp_path_factory):
    rom = REPO_ROOT / "pokefirered_switch.gba"
    if not rom.is_file() or not ELF.is_file():
        pytest.skip("ROM/ELF da Switch não compilados")
    out = tmp_path_factory.mktemp("batalha")
    with open_context(str(rom), str(ELF), str(out), "CHARMANDER") as ctx:
        run_opening(ctx)
        assert not ctx.suite.failed(), [r for r in ctx.suite.results if r.status == "falha"]
        nav, consts = ctx.nav, ctx.consts
        assert nav.walk_to(6, 11)
        assert nav.go_through_warp("down") == consts.map("MAP_PALLET_TOWN")
        # pela coluna x=13: depois do inicial a moça da placa fica em (12,2) e o gatilho dela
        # em (13,2) mostra a placa uma vez (PalletTown_EventScript_SignLadyTrigger)
        assert nav.walk_to(13, 3, run=True)
        moved = nav.step("up", 4)
        if nav.interrupted == "script":
            ctx.controller.advance_text(ctx.controller.overworld_idle, 3000, "moça da placa")
            moved += nav.step("up", 4 - moved)
        assert moved == 4 and ctx.game.location() == consts.map("MAP_ROUTE1")
        yield ctx


def test_potion_and_run_away(route1):
    ctx = route1
    game, emu = ctx.game, ctx.emu
    potion = ctx.consts.item("ITEM_POTION")
    _give_item(game, SB1_POCKET_ITEMS, potion, 3)
    emu.write(game.syms.addr("gPlayerParty") + MON_HP, struct.pack("<H", 5))
    assert game.party()[0].hp == 5
    _wild_battle(ctx)
    driver = BattleDriver(ctx.controller)
    driver.use_item_in_battle(potion)
    assert game.bag_quantity(potion) == 2
    assert game.party()[0].hp > 5          # +20 da Potion menos o golpe do selvagem no turno
    for _ in range(5):
        if driver.run_away():
            break
    else:
        pytest.fail("não conseguiu fugir em 5 tentativas")
    ctx.controller.wait_overworld_idle(600)
    assert not game.in_battle()
    assert game.location() == ctx.consts.map("MAP_ROUTE1")


def test_throw_ball_until_caught(route1):
    ctx = route1
    game = ctx.game
    ball = ctx.consts.item("ITEM_POKE_BALL")
    _give_item(game, SB1_POCKET_BALLS, ball, 10)
    _wild_battle(ctx)
    driver = BattleDriver(ctx.controller)
    for _ in range(10):
        if driver.throw_ball(ball):
            break
        if not game.in_battle():
            pytest.skip("o selvagem desmaiou/fugiu antes da captura")
    else:
        pytest.fail("não capturou com 10 bolas")
    # parou na pergunta do apelido: NÃO e deixa a batalha terminar
    ctx.emu.press(KEY_B, hold=2, release=8)
    ctx.controller.advance_text(lambda: not game.in_battle(), 3000, "fim da batalha da captura")
    assert driver.outcome() == 7                 # B_OUTCOME_CAUGHT
    assert len(game.party()) == 2
    assert game.bag_quantity(ball) < 10
