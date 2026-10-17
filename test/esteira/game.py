"""Leitura do estado do jogo pela memória do emulador.

Todos os offsets vêm dos comentários /*0x..*/ e das structs dos headers do repo
(include/global.h, include/pokemon.h, include/main.h, include/text.h); não adivinhar.
"""

import struct
from dataclasses import dataclass

from .charmap import Charmap
from .constants import Constants
from .emu import Emulator
from .symbols import Symbols

# --- struct BoxPokemon / Pokemon (include/pokemon.h) -------------------------------
POKEMON_SIZE = 100            # sizeof(struct Pokemon)
POKEMON_NAME_LENGTH = 10      # include/constants/global.h
MON_PERSONALITY = 0x00        # BoxPokemon.personality (u32)
MON_OT_ID = 0x04              # BoxPokemon.otId (u32)
MON_NICKNAME = 0x08           # BoxPokemon.nickname[10]
MON_SECURE = 0x20             # BoxPokemon.secure: 4 subestruturas de 12 bytes
MON_LEVEL = 0x54              # Pokemon.level (u8): box(0x50) + status(u32) = 0x54
MON_HP = 0x56                 # Pokemon.hp (u16)
MON_MAX_HP = 0x58             # Pokemon.maxHP (u16)
SUBSTRUCT_SIZE = 12           # NUM_SUBSTRUCT_BYTES
PARTY_SIZE = 6

# Posição de cada tipo de subestrutura (0=growth, 1=attacks, 2=EVs, 3=misc) dentro de
# `secure`, em função de personality % 24. Tabela SUBSTRUCT_CASE(n,v1,v2,v3,v4) de
# src/pokemon.c: o tipo t fica na posição v[t+1].
_SUBSTRUCT_ORDER = [
    (0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 3, 1, 2), (0, 2, 3, 1), (0, 3, 2, 1),
    (1, 0, 2, 3), (1, 0, 3, 2), (2, 0, 1, 3), (3, 0, 1, 2), (2, 0, 3, 1), (3, 0, 2, 1),
    (1, 2, 0, 3), (1, 3, 0, 2), (2, 1, 0, 3), (3, 1, 0, 2), (2, 3, 0, 1), (3, 2, 0, 1),
    (1, 2, 3, 0), (1, 3, 2, 0), (2, 1, 3, 0), (3, 1, 2, 0), (2, 3, 1, 0), (3, 2, 1, 0),
]

# --- struct SaveBlock2 (include/global.h) ------------------------------------------
SB2_PLAYER_NAME = 0x000       # playerName[PLAYER_NAME_LENGTH + 1]
PLAYER_NAME_LENGTH = 7
SB2_OPTIONS = 0x014           # u16: optionsTextSpeed:3 nos bits 0-2
SB2_ENCRYPTION_KEY = 0xF20    # u32 encryptionKey

# --- struct SaveBlock1 (include/global.h) ------------------------------------------
SB1_POS = 0x0000              # struct Coords16 pos {s16 x, y}
SB1_LOCATION = 0x0004         # struct WarpData location {s8 mapGroup, s8 mapNum, ...}
SB1_MONEY = 0x0290            # u32 money (XOR encryptionKey)
SB1_FLAGS = 0x0EE0            # u8 flags[NUM_FLAG_BYTES]
# (offset, nº de ItemSlot {u16 itemId, u16 quantity}) de cada bolso; contagens em
# include/constants/global.h (BAG_*_COUNT)
SB1_BAG_POCKETS = [
    (0x0310, 42),  # bagPocket_Items
    (0x03B8, 30),  # bagPocket_KeyItems
    (0x0430, 13),  # bagPocket_PokeBalls
    (0x0464, 58),  # bagPocket_TMHM
    (0x054C, 43),  # bagPocket_Berries
]

# --- struct Main (include/main.h) --------------------------------------------------
MAIN_CALLBACK2 = 0x004
MAIN_IN_BATTLE = 0x439        # bit 1 do byte (oamLoadDisabled:1, inBattle:1, ...)

# --- struct TextPrinter (include/text.h) -------------------------------------------
TEXT_PRINTER_SIZE = 0x24      # confere com sizeof(sTextPrinters)==0x480 / 32 janelas no ELF
TEXT_PRINTER_ACTIVE = 0x1B    # campo `active` (IsTextPrinterActive lê [r1, #27])
TEXT_PRINTER_STATE = 0x1C     # campo `state` (enum RENDER_STATE_* de include/text.h)

# --- struct Task (include/task.h) --------------------------------------------------
NUM_TASKS = 16
TASK_SIZE = 0x28              # func(4) + isActive, prev, next, priority + s16 data[16]
TASK_IS_ACTIVE = 0x04


@dataclass
class Mon:
    species: int
    level: int
    hp: int
    max_hp: int
    nickname: str
    personality: int
    ot_id: int
    moves: list[int]
    pp: list[int]

    @property
    def is_shiny(self) -> bool:
        ot, pid = self.ot_id, self.personality
        return ((ot >> 16) ^ (ot & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF)) < 8


def decode_mon(raw: bytes, charmap: Charmap) -> Mon:
    """Decodifica os 100 bytes de uma `struct Pokemon` (dados seguros XOR pid^otId)."""
    if len(raw) < POKEMON_SIZE:
        raise ValueError(f"struct Pokemon tem {POKEMON_SIZE} bytes, recebi {len(raw)}")
    pid, ot = struct.unpack_from("<II", raw, MON_PERSONALITY)
    key = pid ^ ot
    words = struct.unpack_from("<12I", raw, MON_SECURE)
    secure = struct.pack("<12I", *(w ^ key for w in words))
    order = _SUBSTRUCT_ORDER[pid % 24]

    def sub(kind: int) -> bytes:
        start = order[kind] * SUBSTRUCT_SIZE
        return secure[start:start + SUBSTRUCT_SIZE]

    species = struct.unpack_from("<H", sub(0), 0)[0]          # PokemonSubstruct0.species
    moves = list(struct.unpack_from("<4H", sub(1), 0))        # PokemonSubstruct1.moves
    pp = list(struct.unpack_from("<4B", sub(1), 8))           # PokemonSubstruct1.pp
    return Mon(
        species=species,
        level=raw[MON_LEVEL],
        hp=struct.unpack_from("<H", raw, MON_HP)[0],
        max_hp=struct.unpack_from("<H", raw, MON_MAX_HP)[0],
        nickname=charmap.decode(raw[MON_NICKNAME:MON_NICKNAME + POKEMON_NAME_LENGTH]),
        personality=pid,
        ot_id=ot,
        moves=moves,
        pp=pp,
    )


class Game:
    """Visão de alto nível do estado do jogo; só lê memória (nunca escreve)."""

    def __init__(self, emu: Emulator, syms: Symbols, consts: Constants, charmap: Charmap):
        self.emu = emu
        self.syms = syms
        self.consts = consts
        self.charmap = charmap

    # gSaveBlock1Ptr / gSaveBlock2Ptr são ponteiros: desreferenciar a cada leitura
    # (os blocos podem mudar de lugar entre telas).
    def _sb1(self) -> int:
        return self.emu.read_u32(self.syms.addr("gSaveBlock1Ptr"))

    def _sb2(self) -> int:
        return self.emu.read_u32(self.syms.addr("gSaveBlock2Ptr"))

    def _key(self) -> int:
        return self.emu.read_u32(self._sb2() + SB2_ENCRYPTION_KEY)

    def party(self) -> list[Mon]:
        count = min(self.emu.read_u8(self.syms.addr("gPlayerPartyCount")), PARTY_SIZE)
        base = self.syms.addr("gPlayerParty")
        raw = self.emu.read(base, POKEMON_SIZE * count) if count else b""
        return [decode_mon(raw[i * POKEMON_SIZE:(i + 1) * POKEMON_SIZE], self.charmap)
                for i in range(count)]

    def player_name(self) -> str:
        raw = self.emu.read(self._sb2() + SB2_PLAYER_NAME, PLAYER_NAME_LENGTH + 1)
        return self.charmap.decode(raw)

    def money(self) -> int:
        return self.emu.read_u32(self._sb1() + SB1_MONEY) ^ self._key()

    def bag_quantity(self, item_id: int) -> int:
        """Soma a quantidade do item em todos os bolsos (quantity XOR 16 bits baixos da chave)."""
        sb1, key = self._sb1(), self._key() & 0xFFFF
        total = 0
        for offset, count in SB1_BAG_POCKETS:
            raw = self.emu.read(sb1 + offset, count * 4)
            for i in range(count):
                slot_item, qty = struct.unpack_from("<HH", raw, i * 4)
                if slot_item == item_id:
                    total += qty ^ key
        return total

    def bag_pocket(self, pocket: int) -> list[tuple[int, int]]:
        """(item, quantidade) de cada slot ocupado do bolso `pocket` (0 = POCKET_ITEMS - 1), na
        ordem em que a bolsa os lista."""
        offset, count = SB1_BAG_POCKETS[pocket]
        sb1, key = self._sb1(), self._key() & 0xFFFF
        raw = self.emu.read(sb1 + offset, count * 4)
        slots = []
        for i in range(count):
            item, qty = struct.unpack_from("<HH", raw, i * 4)
            if item:
                slots.append((item, qty ^ key))
        return slots

    def flag(self, flag_id: int) -> bool:
        byte = self.emu.read_u8(self._sb1() + SB1_FLAGS + flag_id // 8)
        return bool(byte & (1 << (flag_id % 8)))

    def location(self) -> tuple[int, int]:
        """(mapGroup, mapNum) do mapa atual (SaveBlock1.location)."""
        group, num = struct.unpack("<bb", self.emu.read(self._sb1() + SB1_LOCATION, 2))
        return group, num

    def player_xy(self) -> tuple[int, int]:
        """Posição do jogador (SaveBlock1.pos), em metatiles, sem o MAP_OFFSET."""
        return struct.unpack("<hh", self.emu.read(self._sb1() + SB1_POS, 4))

    def in_battle(self) -> bool:
        return bool(self.emu.read_u8(self.syms.addr("gMain") + MAIN_IN_BATTLE) & 0x02)

    def callback2(self) -> str:
        """Nome do símbolo apontado por gMain.callback2 (0x... se desconhecido, '' se nulo)."""
        ptr = self.emu.read_u32(self.syms.addr("gMain") + MAIN_CALLBACK2)
        if ptr == 0:
            return ""
        # funções Thumb têm o bit 0 ligado no ponteiro
        return self.syms.name_at(ptr & ~1) or f"0x{ptr:08x}"

    def text_printer_active(self, window: int = 0) -> bool:
        base = self.syms.addr("sTextPrinters")
        return bool(self.emu.read_u8(base + window * TEXT_PRINTER_SIZE + TEXT_PRINTER_ACTIVE))

    def text_printer_state(self, window: int = 0) -> int:
        """`state` do printer da janela (1 = RENDER_STATE_WAIT: esperando botão)."""
        base = self.syms.addr("sTextPrinters")
        return self.emu.read_u8(base + window * TEXT_PRINTER_SIZE + TEXT_PRINTER_STATE)

    def active_tasks(self) -> set[str]:
        """Nomes das funções das tasks ativas em gTasks (0x... se o símbolo não existir)."""
        raw = self.emu.read(self.syms.addr("gTasks"), NUM_TASKS * TASK_SIZE)
        names = set()
        for i in range(NUM_TASKS):
            entry = raw[i * TASK_SIZE:(i + 1) * TASK_SIZE]
            if not entry[TASK_IS_ACTIVE]:
                continue
            func = struct.unpack_from("<I", entry, 0)[0] & ~1
            names.add(self.syms.name_at(func) or f"0x{func:08x}")
        return names

    def options_text_speed(self) -> int:
        return self.emu.read_u16(self._sb2() + SB2_OPTIONS) & 0x7
