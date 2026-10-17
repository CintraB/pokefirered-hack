"""Recuperação do BattleDriver: Poké Ball que falha, desmaio do próprio Pokémon, sim/não.

Os testes ao vivo partem de um savestate preparado (`test/fixtures/battle_ball_fails.ss.gz`):
batalha selvagem na Rota 1, no menu de ação, com 2 Pokémon no time e 5 Poké Balls, num
quadro em que a próxima bola lançada falha. Ele foi gerado uma vez por
`make_ball_fails_state()` (abertura real + escrita na RAM para preparar o caso, como em
test_battle_live.py) para a ROM cujo SHA-1 está em `battle_ball_fails.json`. Com outra ROM o
savestate não vale (RAM com ponteiros da ROM antiga): o teste gera um novo em
test/out/fixtures/<sha>/ e usa esse. A falha da bola depende do quadro em que o jogo sorteia
a captura, ou seja, também do ritmo de botões do driver: antes dos testes, a fixture confere
que a 1ª bola ainda falha e, se não, gera de novo no mesmo lugar (uma vez). Para regravar o
versionado na mão (mesmo com a ROM igual):
    ESTEIRA_REFRESH_FIXTURES=1 python3 -m pytest test/tests/test_battle_recovery.py
"""

import gzip
import hashlib
import json
import os
import shutil
import struct
from pathlib import Path
from typing import Callable

import pytest

from esteira.battle import (B_OUTCOME_CAUGHT, B_OUTCOME_LOST, B_OUTCOME_RAN, B_OUTCOME_WON,
                            BATTLE_TYPE_TRAINER, BattleDriver, yesno_key)
from esteira.emu import KEY_A, KEY_B
from esteira.result import StepTimeout
from esteira.scenarios import open_context
from esteira.scenarios.quick_opening import run_opening
from test_battle_live import SB1_POCKET_BALLS, _give_item, _wild_battle

REPO_ROOT = Path(__file__).resolve().parents[2]
ROM = REPO_ROOT / "pokefirered_switch.gba"
ELF = REPO_ROOT / "pokefirered_switch.elf"
FIXTURES = REPO_ROOT / "test" / "fixtures"
CACHE_ROOT = REPO_ROOT / "test" / "out" / "fixtures"
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
    with open(candidate, "rb") as src, gzip.open(dest, "wb") as out:
        shutil.copyfileobj(src, out)


def _unpack(packed: Path, dest: Path) -> Path:
    with gzip.open(packed, "rb") as src, open(dest, "wb") as out:
        shutil.copyfileobj(src, out)
    return dest


def first_throw_fails(packed: Path, work: Path) -> bool:
    """O savestate ainda serve? (em batalha e a 1ª bola lançada dali falha)."""
    try:
        with open_context(str(ROM), str(ELF), str(work), STARTER) as ctx:
            ctx.emu.load_state(str(_unpack(packed, work / "check.ss")))
            ctx.emu.keys(0)
            if not ctx.game.in_battle():
                return False
            ball = ctx.consts.item("ITEM_POKE_BALL")
            return not BattleDriver(ctx.controller).throw_ball(ball) and ctx.game.in_battle()
    except (AssertionError, StepTimeout):
        return False


def _write_atomic(dest: Path, write: Callable[[Path], None]) -> None:
    """write(tmp) num nome temporário ao lado de `dest` e depois os.replace: um arquivo
    gerado pela metade nunca fica com o nome final (nem é reaproveitado depois)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    try:
        write(tmp)
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)


def _meta(sha: str) -> dict:
    return {"rom_sha1": sha, "starter": STARTER, "balls": BALLS}


def _meta_matches(meta_path: Path, sha: str) -> bool:
    try:
        meta = json.loads(meta_path.read_text("utf-8"))
    except (OSError, ValueError):
        return False
    return all(meta.get(key) == value for key, value in _meta(sha).items())


def prepare_ball_fails_state(sha: str, fixtures: Path, cache_root: Path, refresh: bool,
                             generate: Callable[[Path], None],
                             still_fails: Callable[[Path], bool],
                             log: Callable[[str], None] = print) -> Path:
    """Escolhe (e gera se preciso) o savestate compactado; devolve o caminho dele.

    - `refresh` (ESTEIRA_REFRESH_FIXTURES=1): regrava o versionado em `fixtures` para esta ROM,
      mesmo que os metadados já batam (o caso de mudança de ritmo do driver);
    - versionado com metadados desta ROM, STARTER e BALLS: usa ele;
    - senão: `cache_root/<sha12>/` (gerado se faltar ou com metadados diferentes).
    Se a 1ª bola não falha mais no escolhido (ritmo de battle.py/bag.py mudou), gera de novo no
    mesmo lugar, uma vez; se nem o recém-gerado servir, falha com a explicação.
    """
    versioned = fixtures / STATE_NAME
    if refresh or (versioned.is_file() and _meta_matches(fixtures / META_NAME, sha)):
        base = fixtures
    else:
        base = cache_root / sha[:12]
    packed, meta = base / STATE_NAME, base / META_NAME

    def regenerate(reason: str) -> None:
        log(f"savestate da bola que falha: {reason}; gerando em {packed}")
        _write_atomic(packed, generate)
        _write_atomic(meta, lambda tmp: tmp.write_text(
            json.dumps(_meta(sha), indent=2) + "\n", "utf-8"))

    if refresh:
        regenerate("ESTEIRA_REFRESH_FIXTURES=1")
    elif not packed.is_file() or not _meta_matches(meta, sha):
        regenerate("ausente ou de outra ROM/configuração")
    elif not still_fails(packed):
        regenerate("a 1ª bola não falha mais (ritmo do driver mudou?)")
    else:
        return packed
    if not still_fails(packed):
        raise AssertionError(f"{packed} acabou de ser gerado e a 1ª bola não falha ao "
                             "recarregá-lo: o replay do savestate não é determinístico")
    return packed


@pytest.fixture(scope="module")
def ball_fails_state(tmp_path_factory) -> Path:
    """Savestate descompactado (ver prepare_ball_fails_state)."""
    if not ROM.is_file() or not ELF.is_file():
        pytest.skip("ROM/ELF da Switch não compilados")
    packed = prepare_ball_fails_state(
        _rom_sha1(), FIXTURES, CACHE_ROOT, os.environ.get("ESTEIRA_REFRESH_FIXTURES") == "1",
        generate=lambda dest: make_ball_fails_state(dest, tmp_path_factory.mktemp("gera")),
        still_fails=lambda packed: first_throw_fails(packed, tmp_path_factory.mktemp("confere")))
    return _unpack(packed, tmp_path_factory.mktemp("estado") / "battle_ball_fails.ss")


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
    assert driver.throw_ball(ball) is False, (
        "a 1ª bola capturou: o savestate (test/fixtures/battle_ball_fails.ss.gz ou o cache em "
        "test/out/fixtures/) não serve ao ritmo atual do driver; regrave com "
        "ESTEIRA_REFRESH_FIXTURES=1 python3 -m pytest test/tests/test_battle_recovery.py")
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


# --- escolha/geração do savestate (sem emulador: gerador e conferência falsos) -----------
SHA = "ab" * 20


class _FakeFixture:
    """Gerador que grava "gerado-N" e conferência que responde da lista `checks`."""

    def __init__(self, checks=()):
        self.generated = 0
        self.checks = list(checks)
        self.checked = []

    def generate(self, dest: Path) -> None:
        self.generated += 1
        dest.write_text(f"gerado-{self.generated}")

    def still_fails(self, packed: Path) -> bool:
        self.checked.append(packed.read_text())
        return self.checks.pop(0) if self.checks else True

    def prepare(self, tmp_path: Path, refresh: bool = False) -> Path:
        return prepare_ball_fails_state(SHA, tmp_path / "fixtures", tmp_path / "cache", refresh,
                                        self.generate, self.still_fails, log=lambda _msg: None)


def _versioned(tmp_path: Path, content: str = "antigo", **meta) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (fixtures / STATE_NAME).write_text(content)
    (fixtures / META_NAME).write_text(json.dumps({**_meta(SHA), **meta}))


def test_fixture_matching_versioned_is_used_as_is(tmp_path):
    _versioned(tmp_path)
    fake = _FakeFixture()
    assert fake.prepare(tmp_path) == tmp_path / "fixtures" / STATE_NAME
    assert fake.generated == 0 and fake.checked == ["antigo"]


def test_fixture_refresh_regenerates_even_with_matching_rom(tmp_path):
    _versioned(tmp_path)
    fake = _FakeFixture()
    packed = fake.prepare(tmp_path, refresh=True)
    assert packed == tmp_path / "fixtures" / STATE_NAME
    assert packed.read_text() == "gerado-1" and fake.generated == 1
    assert json.loads((tmp_path / "fixtures" / META_NAME).read_text()) == _meta(SHA)


def test_fixture_stale_pacing_regenerates_once_in_place(tmp_path):
    _versioned(tmp_path)
    fake = _FakeFixture(checks=[False, True])     # a 1ª bola capturou no antigo
    packed = fake.prepare(tmp_path)
    assert packed == tmp_path / "fixtures" / STATE_NAME
    assert packed.read_text() == "gerado-1" and fake.generated == 1
    assert fake.checked == ["antigo", "gerado-1"]


def test_fixture_still_stale_after_regenerating_fails_loudly(tmp_path):
    _versioned(tmp_path)
    fake = _FakeFixture(checks=[False, False])
    with pytest.raises(AssertionError, match="não é determinístico"):
        fake.prepare(tmp_path)
    assert fake.generated == 1


@pytest.mark.parametrize("meta", [{"rom_sha1": "cd" * 20}, {"starter": "SQUIRTLE"}, {"balls": 3}])
def test_fixture_other_rom_or_config_goes_to_cache(tmp_path, meta):
    _versioned(tmp_path, **meta)
    fake = _FakeFixture()
    packed = fake.prepare(tmp_path)
    assert packed == tmp_path / "cache" / SHA[:12] / STATE_NAME
    assert packed.read_text() == "gerado-1"
    assert (tmp_path / "fixtures" / STATE_NAME).read_text() == "antigo"   # versionado intacto
    assert fake.prepare(tmp_path) == packed and fake.generated == 1       # cache reaproveitado


def test_fixture_half_written_file_never_gets_final_name(tmp_path):
    def broken(dest: Path) -> None:
        dest.write_text("pela metade")
        raise RuntimeError("geração interrompida")

    with pytest.raises(RuntimeError):
        prepare_ball_fails_state(SHA, tmp_path / "fixtures", tmp_path / "cache", False,
                                 broken, lambda _p: True, log=lambda _msg: None)
    cache = tmp_path / "cache" / SHA[:12]
    assert not (cache / STATE_NAME).exists() and not (cache / META_NAME).exists()
    assert list(cache.iterdir()) == []
