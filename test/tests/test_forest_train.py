"""Teto de batalhas do treino do modo completo (sem emulador)."""

import struct
from pathlib import Path

import pytest

from esteira.scenarios.full_forest_brock import (MIN_TRAIN_BATTLES, medium_slow_exp,
                                                 train_battle_cap)

REPO_ROOT = Path(__file__).resolve().parents[2]
GROWTH_MEDIUM_SLOW = 3        # include/constants/pokemon.h
TABLE_LEVELS = 101            # gExperienceTables[][MAX_LEVEL + 1]


def test_exp_medium_slow_bate_com_a_tabela_do_rom():
    from esteira.symbols import Symbols
    rom_path, elf = REPO_ROOT / "pokefirered_switch.gba", REPO_ROOT / "pokefirered_switch.elf"
    if not rom_path.is_file() or not elf.is_file():
        pytest.skip("ROM/ELF da Switch não compilados")
    rom = rom_path.read_bytes()
    base = Symbols.from_elf(str(elf)).addr("gExperienceTables") - 0x08000000
    row = base + GROWTH_MEDIUM_SLOW * TABLE_LEVELS * 4
    table = struct.unpack_from(f"<{TABLE_LEVELS}I", rom, row)
    assert [medium_slow_exp(n) for n in range(2, 40)] == list(table[2:40])   # nv1 é especial


def test_teto_cresce_com_a_exp_pedida_e_cobre_o_medido():
    # medido: Charmander nv11 -> nv18 em 121 batalhas; o teto antigo (150 fixo) não cobria a
    # 3ª tentativa do Brock (nv21 -> nv24, ~3750 EXP, ~150 batalhas a ~25 EXP cada)
    assert train_battle_cap(11, 18) >= 121 * 1.5
    assert train_battle_cap(21, 24) > train_battle_cap(18, 21) > train_battle_cap(11, 13)
    assert train_battle_cap(21, 24) >= 3750 / 25 * 1.5
    assert train_battle_cap(13, 13) == MIN_TRAIN_BATTLES          # já no nível
    assert train_battle_cap(5, 6) == MIN_TRAIN_BATTLES            # piso
