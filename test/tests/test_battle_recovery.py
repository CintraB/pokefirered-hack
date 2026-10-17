"""Recuperação do BattleDriver: Poké Ball que falha, desmaio do próprio Pokémon, sim/não.

Os testes ao vivo partem de um savestate preparado (`test/fixtures/battle_ball_fails.ss.gz`):
batalha selvagem na Rota 1, no menu de ação, com 2 Pokémon no time e 5 Poké Balls, num
quadro em que a próxima bola lançada falha. Ele foi gerado uma vez por
`make_ball_fails_state()` (abertura real + escrita na RAM para preparar o caso, como em
test_battle_live.py) para a ROM cujo SHA-1 está em `battle_ball_fails.json`. Com outra ROM o
savestate não vale (RAM com ponteiros da ROM antiga): o teste gera um novo em
test/out/fixtures/<sha>/ e usa esse. A falha da bola depende do quadro em que o jogo sorteia
a captura, ou seja, também do ritmo de botões do driver: se uma mudança em battle.py/bag.py
fizer a 1ª bola capturar, gere de novo. Para atualizar o versionado:
    ESTEIRA_REFRESH_FIXTURES=1 python3 -m pytest test/tests/test_battle_recovery.py
"""

import gzip
import hashlib
import json
import os
import shutil
import struct
from pathlib import Path

import pytest

from esteira.battle import (B_OUTCOME_CAUGHT, B_OUTCOME_LOST, B_OUTCOME_RAN, B_OUTCOME_WON,
                            BATTLE_TYPE_TRAINER, BattleDriver, yesno_key)
from esteira.emu import KEY_A, KEY_B
from esteira.scenarios import open_context
from esteira.scenarios.quick_opening import run_opening
from test_battle_live import SB1_POCKET_BALLS, _give_item, _wild_battle

REPO_ROOT = Path(__file__).resolve().parents[2]
ROM = REPO_ROOT / "pokefirered_switch.gba"
ELF = REPO_ROOT / "pokefirered_switch.elf"
FIXTURES = REPO_ROOT / "test" / "fixtures"
STATE_NAME = "battle_ball_fails.ss.gz"
META_NAME = "battle_ball_fails.json"
STARTER = "CHARMANDER"
BALLS = 5
MAX_SEARCH = 40              # tentativas (quadros de espera diferentes) até achar uma bola que falha
POKEMON_SIZE = 100
MON_HP = 0x56                # struct Pokemon.hp
BATTLE_MON_HP = 0x28         # struct BattlePokemon.hp
BATTLE_MON_PP = 0x24         # struct BattlePokemon.pp[4]


def _rom_sha1() -> str:
    return hashlib.sha1(ROM.read_bytes()).hexdigest()


def _reach_route1(ctx) -> None:
    """Do laboratório até a grama da entrada da Rota 1 (mesmo caminho de test_battle_live)."""
    nav, consts = ctx.nav, ctx.consts
    assert nav.walk_to(6, 11)
    assert nav.go_through_warp("down") == consts.map("MAP_PALLET_TOWN")
    assert nav.walk_to(13, 3, run=True)
    moved = nav.step("up", 4)
    if nav.interrupted == "script":
        ctx.controller.advance_text(ctx.controller.overworld_idle, 3000, "moça da placa")
        moved += nav.step("up", 4 - moved)
    assert moved == 4 and ctx.game.location() == consts.map("MAP_ROUTE1")


def make_ball_fails_state(dest: Path, work: Path) -> None:
    """Gera o savestate: abertura real, time de 2 (cópia do inicial), 5 bolas, batalha
    selvagem no menu de ação e um quadro em que a bola lançada falha."""
    with open_context(str(ROM), str(ELF), str(work), STARTER) as ctx:
        run_opening(ctx)
        assert not ctx.suite.failed(), [r for r in ctx.suite.results if r.status == "falha"]
        game, emu, syms = ctx.game, ctx.emu, ctx.game.syms
        party = syms.addr("gPlayerParty")
        emu.write(party + POKEMON_SIZE, emu.read(party, POKEMON_SIZE))
        emu.write(syms.addr("gPlayerPartyCount"), bytes([2]))
        ball = ctx.consts.item("ITEM_POKE_BALL")
        _give_item(game, SB1_POCKET_BALLS, ball, BALLS)
        _reach_route1(ctx)
        _wild_battle(ctx)
        driver = BattleDriver(ctx.controller)
        driver.wait_action_menu()
        menu = work / "menu.ss"
        candidate = work / "candidate.ss"
        emu.save_state(str(menu))
        for wait in range(MAX_SEARCH):
            emu.load_state(str(menu))
            emu.frames(1 + wait)            # o RNG anda a cada quadro (VBlankIntr)
            emu.save_state(str(candidate))
            if not driver.throw_ball(ball) and game.in_battle():
                break
        else:
            raise AssertionError(f"nenhuma bola falhou em {MAX_SEARCH} tentativas")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(candidate, "rb") as src, gzip.open(dest, "wb") as out:
        shutil.copyfileobj(src, out)


@pytest.fixture(scope="module")
def ball_fails_state(tmp_path_factory) -> Path:
    """Savestate descompactado (versionado se for da ROM atual; senão gerado e guardado em
    test/out/fixtures/<sha>/)."""
    if not ROM.is_file() or not ELF.is_file():
        pytest.skip("ROM/ELF da Switch não compilados")
    sha = _rom_sha1()
    meta_path = FIXTURES / META_NAME
    meta = json.loads(meta_path.read_text("utf-8")) if meta_path.is_file() else {}
    if meta.get("rom_sha1") == sha and (FIXTURES / STATE_NAME).is_file():
        packed = FIXTURES / STATE_NAME
    else:
        refresh = os.environ.get("ESTEIRA_REFRESH_FIXTURES") == "1"
        base = FIXTURES if refresh else REPO_ROOT / "test" / "out" / "fixtures" / sha[:12]
        packed = base / STATE_NAME
        if refresh or not packed.is_file():
            make_ball_fails_state(packed, tmp_path_factory.mktemp("gera_fixture"))
            if refresh:
                meta_path.write_text(json.dumps({"rom_sha1": sha, "starter": STARTER,
                                                 "balls": BALLS}, indent=2) + "\n", "utf-8")
    state = tmp_path_factory.mktemp("estado") / "battle_ball_fails.ss"
    with gzip.open(packed, "rb") as src, open(state, "wb") as out:
        shutil.copyfileobj(src, out)
    return state


@pytest.fixture
def battle(ball_fails_state, tmp_path):
    with open_context(str(ROM), str(ELF), str(tmp_path / "out"), STARTER) as ctx:
        ctx.emu.load_state(str(ball_fails_state))
        ctx.emu.keys(0)
        assert ctx.game.in_battle()
        yield ctx, BattleDriver(ctx.controller)


def _force_faint_next_hit(ctx, backup_alive: bool) -> None:
    """Inicial com 1 de HP (no time e na batalha) e sem PP no 1º golpe, para o driver usar o
    2º (Growl, que não causa dano) e o selvagem derrubá-lo; o 2º do time vivo ou desmaiado."""
    emu, syms = ctx.emu, ctx.game.syms
    party = syms.addr("gPlayerParty")
    mons = syms.addr("gBattleMons")
    emu.write(party + MON_HP, struct.pack("<H", 1))
    emu.write(mons + BATTLE_MON_HP, struct.pack("<H", 1))
    emu.write(mons + BATTLE_MON_PP, bytes([0]))
    if not backup_alive:
        emu.write(party + POKEMON_SIZE + MON_HP, struct.pack("<H", 0))


def test_failed_ball_returns_false_and_driver_keeps_going(battle):
    ctx, driver = battle
    game = ctx.game
    ball = ctx.consts.item("ITEM_POKE_BALL")
    assert game.bag_quantity(ball) == BALLS
    assert driver.throw_ball(ball) is False
    assert game.in_battle(), "a bola falhou e a batalha deveria seguir"
    assert game.bag_quantity(ball) == BALLS - 1
    caught = False
    while game.in_battle() and game.bag_quantity(ball) > 0:
        if driver.throw_ball(ball):
            caught = True
            break
    if caught:
        ctx.emu.press(KEY_B, hold=2, release=8)            # apelido: NÃO
        ctx.controller.advance_text(lambda: not game.in_battle(), 3000, "fim da captura")
        assert driver.outcome() == B_OUTCOME_CAUGHT
        assert len(game.party()) == 3
    else:
        assert game.bag_quantity(ball) == 0 or not game.in_battle()


def test_wild_faint_with_backup_sends_next_and_reports_fainted(battle):
    ctx, driver = battle
    _force_faint_next_hit(ctx, backup_alive=True)
    outcome = driver.fight_to_end()
    party = ctx.game.party()
    assert outcome == "fainted"
    assert driver.outcome() == B_OUTCOME_WON, "devia trocar de Pokémon (SIM) e vencer, não fugir"
    assert driver.outcome() != B_OUTCOME_RAN
    assert party[0].hp == 0 and party[1].hp > 0


def test_wild_faint_without_backup_loses(battle):
    ctx, driver = battle
    _force_faint_next_hit(ctx, backup_alive=False)
    assert driver.fight_to_end() == "lose"
    assert driver.outcome() == B_OUTCOME_LOST


def test_yesno_answer_depends_on_battle_type():
    # selvagem: "Usar o próximo Pokémon?" -> SIM; treinador: "trocar antes do oponente?" -> NÃO
    assert yesno_key("Cmd_yesnobox", 0) == KEY_A
    assert yesno_key("Cmd_yesnobox", BATTLE_TYPE_TRAINER) == KEY_B
    assert yesno_key("Cmd_yesnoboxlearnmove", 0) == KEY_B
    assert yesno_key("Cmd_yesnoboxstoplearningmove", BATTLE_TYPE_TRAINER) == KEY_A
