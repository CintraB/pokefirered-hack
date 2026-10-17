"""Digitação na tela de nome (src/naming_screen.c) só com botões, conferindo pela memória.

Offsets de `struct NamingScreenData` e dos dados do cursor vêm de src/naming_screen.c:
textBuffer 0x1800, state 0x1E10, currentPage 0x1E22, cursorSpriteId 0x1E23; o cursor é
um sprite cujo data[0]/data[1] guardam a coluna/linha (sX/sY). struct Sprite tem 0x44
bytes com data[8] em 0x2E (include/sprite.h).
"""

from .control import Controller
from .emu import KEY_A, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_START, KEY_UP

NAMING_CALLBACK = "CB2_NamingScreen"
NS_TEXT_BUFFER = 0x1800
NS_STATE = 0x1E10
NS_CURRENT_PAGE = 0x1E22
NS_CURSOR_SPRITE_ID = 0x1E23
STATE_HANDLE_INPUT = 2          # enum de estados de Task_NamingScreen
KBPAGE_LETTERS_UPPER = 1        # enum KBPAGE_* (ordem de troca das páginas)
SPRITE_SIZE = 0x44
SPRITE_DATA = 0x2E

# Página de maiúsculas (sKeyboardChars[KEYBOARD_LETTERS_UPPER]); coluna, linha.
UPPER_ROWS = ["ABCDEF .", "GHIJKL ,", "MNOPQRS", "TUVWXYZ"]
UPPER_KEYS = {ch: (x, y) for y, row in enumerate(UPPER_ROWS) for x, ch in enumerate(row) if ch != " "}

MAX_MOVES_PER_KEY = 12


class NamingScreen:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.game = controller.game
        self.emu = controller.emu

    def _base(self) -> int:
        return self.emu.read_u32(self.game.syms.addr("sNamingScreen"))

    def is_open(self) -> bool:
        return self.game.callback2() == NAMING_CALLBACK

    def ready(self) -> bool:
        base = self._base()
        return (self.is_open() and base != 0
                and self.emu.read_u8(base + NS_STATE) == STATE_HANDLE_INPUT)

    def text(self) -> str:
        raw = self.emu.read(self._base() + NS_TEXT_BUFFER, 16)
        return self.game.charmap.decode(raw)

    def cursor(self) -> tuple[int, int]:
        sprite_id = self.emu.read_u8(self._base() + NS_CURSOR_SPRITE_ID)
        data = self.game.syms.addr("gSprites") + sprite_id * SPRITE_SIZE + SPRITE_DATA
        raw = self.emu.read(data, 4)
        return (int.from_bytes(raw[0:2], "little", signed=True),
                int.from_bytes(raw[2:4], "little", signed=True))

    def _move_to(self, target: tuple[int, int], ch: str) -> None:
        for _ in range(MAX_MOVES_PER_KEY):
            x, y = self.cursor()
            if (x, y) == target:
                return
            if x != target[0]:
                key = KEY_RIGHT if target[0] > x else KEY_LEFT
            else:
                key = KEY_DOWN if target[1] > y else KEY_UP
            self.emu.press(key, hold=2, release=4)
        raise self.ctl.timeout_error(f"cursor da tela de nome até {ch!r} {target} "
                                     f"(está em {self.cursor()})")

    def type_text(self, text: str, timeout: int = 900) -> None:
        """Digita `text` (maiúsculas) e confirma em OK; espera a tela de nome fechar."""
        self.ctl.wait_until(self.ready, timeout, "tela de nome pronta")
        if self.emu.read_u8(self._base() + NS_CURRENT_PAGE) != KBPAGE_LETTERS_UPPER:
            raise self.ctl.timeout_error("tela de nome fora da página de maiúsculas")
        if self.text():
            raise self.ctl.timeout_error(f"tela de nome não começou vazia ({self.text()!r})")
        for i, ch in enumerate(text):
            if ch not in UPPER_KEYS:
                raise ValueError(f"caractere {ch!r} fora da página de maiúsculas")
            self._move_to(UPPER_KEYS[ch], ch)
            self.emu.press(KEY_A, hold=2, release=4)
            self.ctl.wait_until(lambda: len(self.text()) == i + 1, 30, f"letra {ch!r} digitada")
            if self.text() != text[:i + 1]:
                raise self.ctl.timeout_error(f"tela de nome: esperava {text[:i + 1]!r}, "
                                             f"tenho {self.text()!r}")
        # START leva o cursor ao OK; A confirma.
        self.emu.press(KEY_START, hold=2, release=4)
        self.emu.press(KEY_A, hold=2, release=4)
        self.ctl.wait_until(lambda: not self.is_open(), timeout, "saída da tela de nome")
