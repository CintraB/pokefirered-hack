"""Decodificação de dados do jogo sem emulador (struct Pokemon, charmap, shiny)."""

import struct
from pathlib import Path

from esteira.charmap import Charmap
from esteira.game import Mon, decode_mon, max_pp

REPO_ROOT = Path(__file__).resolve().parents[2]

# Posição de cada subestrutura (0=growth, 1=attacks, 2=EVs, 3=misc) em função de
# personality % 24; cópia independente de SUBSTRUCT_CASE em src/pokemon.c.
_ORDERS = [
    (0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 3, 1, 2), (0, 2, 3, 1), (0, 3, 2, 1),
    (1, 0, 2, 3), (1, 0, 3, 2), (2, 0, 1, 3), (3, 0, 1, 2), (2, 0, 3, 1), (3, 0, 2, 1),
    (1, 2, 0, 3), (1, 3, 0, 2), (2, 1, 0, 3), (3, 1, 0, 2), (2, 3, 0, 1), (3, 2, 0, 1),
    (1, 2, 3, 0), (1, 3, 2, 0), (2, 1, 3, 0), (3, 1, 2, 0), (2, 3, 1, 0), (3, 2, 1, 0),
]


def build_mon(charmap, pid, ot, species, level, hp, max_hp, nickname, moves, pp,
              pp_bonuses=0) -> bytes:
    """Monta os 100 bytes de uma struct Pokemon, encriptando os dados com pid^ot."""
    growth = struct.pack("<HHIBBH", species, 0, 0, pp_bonuses, 70, 0)
    attacks = struct.pack("<4H4B", *moves, *pp)
    evs = bytes(12)
    misc = bytes(12)
    plain = [growth, attacks, evs, misc]
    secure = bytearray(48)
    for kind, pos in enumerate(_ORDERS[pid % 24]):
        secure[pos * 12:pos * 12 + 12] = plain[kind]
    key = pid ^ ot
    for i in range(0, 48, 4):
        word = struct.unpack_from("<I", secure, i)[0] ^ key
        struct.pack_into("<I", secure, i, word)
    name = (charmap.encode(nickname) + b"\xff").ljust(10, b"\xff")
    box = struct.pack("<II", pid, ot) + name + bytes(2) + bytes(7) + bytes(1) + bytes(2) + bytes(2)
    assert len(box) == 0x20
    tail = struct.pack("<IBBHH", 0, level, 0, hp, max_hp) + bytes(10)  # + atk, def, spe, spa, spd
    raw = box + bytes(secure) + tail
    assert len(raw) == 100
    return raw


def test_decode_bulbasaur_level_5():
    cm = Charmap.load(str(REPO_ROOT))
    raw = build_mon(cm, pid=0x12345678, ot=0xABCD1234, species=1, level=5, hp=19,
                    max_hp=20, nickname="BULBA", moves=[33, 45, 0, 0], pp=[35, 40, 0, 0])
    mon = decode_mon(raw, cm)
    assert mon.species == 1
    assert mon.level == 5
    assert (mon.hp, mon.max_hp) == (19, 20)
    assert mon.nickname == "BULBA"
    assert mon.personality == 0x12345678
    assert mon.ot_id == 0xABCD1234
    assert mon.moves == [33, 45, 0, 0]
    assert mon.pp == [35, 40, 0, 0]


def test_decode_all_substruct_orders():
    cm = Charmap.load(str(REPO_ROOT))
    for pid in range(24):
        raw = build_mon(cm, pid=pid, ot=0x00010002, species=25, level=7, hp=1, max_hp=2,
                        nickname="X", moves=[1, 2, 3, 4], pp=[5, 6, 7, 8])
        mon = decode_mon(raw, cm)
        assert (mon.species, mon.moves, mon.pp) == (25, [1, 2, 3, 4], [5, 6, 7, 8]), pid


def test_decode_pp_bonuses():
    cm = Charmap.load(str(REPO_ROOT))
    raw = build_mon(cm, pid=7, ot=9, species=4, level=6, hp=20, max_hp=21, nickname="X",
                    moves=[10, 45, 0, 0], pp=[35, 40, 0, 0], pp_bonuses=0b00001101)
    assert decode_mon(raw, cm).pp_bonuses == 0b00001101


def test_max_pp_with_pp_ups():
    # CalculatePPWithBonus (src/pokemon.c): base + base * 20 * ups / 100, 2 bits por golpe
    assert max_pp(35, 0, 0) == 35
    assert max_pp(35, 0b01, 0) == 42
    assert max_pp(40, 0b1100, 1) == 64
    assert max_pp(40, 0b1100, 0) == 40


def test_is_shiny():
    def mon(pid, ot):
        return Mon(1, 5, 1, 1, "", pid, ot, [0] * 4, [0] * 4)

    assert mon(0x00000000, 0x00000007).is_shiny
    assert not mon(0x00000000, 0x00000008).is_shiny


def test_charmap_roundtrip():
    cm = Charmap.load(str(REPO_ROOT))
    assert cm.decode(cm.encode("TESTE")) == "TESTE"
    assert cm.encode("A") == b"\xbb"
    assert cm.decode(b"\xbb\xbc\xff\xbd") == "AB"  # 0xFF encerra a string


def test_constants_from_headers():
    from esteira.constants import Constants

    c = Constants.load(str(REPO_ROOT))
    assert c.species("SPECIES_BULBASAUR") == 1
    assert c.species_name(1) == "SPECIES_BULBASAUR"
    assert c.item("ITEM_POTION") == 13
    assert c.flag("FLAG_SYS_POKEDEX_GET") >= 0x800  # SYS_FLAGS + 0x29
    assert c.map("MAP_PALLET_TOWN") == (3, 0)


def test_box_mons_reads_the_boxes_of_the_pc():
    """Game.box_mons: struct PokemonStorage {u8 currentBox; BoxPokemon boxes[14][30]} (80 bytes
    por Pokémon) atrás de gPokemonStoragePtr; slot vazio (hasSpecies = 0) vira None."""
    from types import SimpleNamespace

    from esteira.game import BOX_MON_SIZE, Game, IN_BOX_COUNT

    cm = Charmap.load(str(REPO_ROOT))
    storage = 0x02029314
    mem = bytearray(4 + 14 * IN_BOX_COUNT * BOX_MON_SIZE)
    mon = bytearray(build_mon(cm, pid=0x0BADF00D, ot=0x11112222, species=16, level=3, hp=15,
                              max_hp=15, nickname="ESTEIRA", moves=[33, 0, 0, 0], pp=[35, 0, 0, 0]))
    mon[0x13] = 0x02                                    # hasSpecies
    slot = 4 + (1 * IN_BOX_COUNT + 2) * BOX_MON_SIZE      # caixa 2 (índice 1), posição 2
    mem[slot:slot + BOX_MON_SIZE] = mon[:BOX_MON_SIZE]

    def read(addr, n):
        off = addr - storage
        return bytes(mem[off:off + n])

    ptr = 0x03005008
    emu = SimpleNamespace(read=read, read_u32=lambda a: storage if a == ptr else 0)
    syms = SimpleNamespace(addr=lambda name: {"gPokemonStoragePtr": ptr}[name])
    game = Game(emu, syms, None, cm)
    assert game.box_mons(0) == [None] * IN_BOX_COUNT
    box = game.box_mons(1)
    assert [i for i, m in enumerate(box) if m is not None] == [2]
    assert (box[2].species, box[2].personality, box[2].nickname) == (16, 0x0BADF00D, "ESTEIRA")
