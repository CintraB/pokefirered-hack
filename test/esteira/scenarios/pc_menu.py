"""PC do Centro Pokémon: liga o PC e escolhe no menu "Acessar qual PC?" (data/scripts/pc.inc).

Mixin para cenários (precisa de _walk, _press, _tasks, ctl, emu, game, consts, nav).
"""

from ..emu import KEY_A, KEY_DOWN, KEY_UP

CENTER_PC_FRONT = (11, 2)       # PC (MB_PC) em (11, 1) nos Centros de Viridian e Pewter
# CreatePCMenu: alguém/BILL, <jogador>, OAK, (HALL, com FLAG_SYS_GAME_CLEAR), DESLIGAR
PC_MENU_STORAGE = 0
PC_MENU_OAK = 2
MULTICHOICE_TASK = "Task_MultichoiceMenu_HandleInput"
MENU_CURSOR = 2                 # src/menu.c struct Menu {left, top, cursorPos (s8), min, max, ...}
MENU_MIN_CURSOR = 3
PC_TIMEOUT = 600


class PcMenuMixin:
    def _open_pc_menu(self) -> None:
        """Anda até o PC do Centro, liga e para no menu "Acessar qual PC?"."""
        self._walk(*CENTER_PC_FRONT)
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do PC")
        self._press(KEY_A)
        self.ctl.advance_text(lambda: MULTICHOICE_TASK in self._tasks(), PC_TIMEOUT,
                              "menu do PC")

    def _menu_cursor_addr(self) -> int:
        """Endereço do cursor do menu aberto: `sMenu.cursorPos` de src/menu.c. Há outro
        estático `sMenu` no ELF; o certo é o que tem minCursorPos 0 e maxCursorPos = itens - 1
        (CreatePCMenuWindow: 5 itens com FLAG_SYS_GAME_CLEAR, senão 4)."""
        items = 5 if self.game.flag(self.consts.flag("FLAG_SYS_GAME_CLEAR")) else 4
        found = [addr for addr in self.game.syms.addrs("sMenu")
                 if tuple(self.emu.read(addr + MENU_MIN_CURSOR, 2)) == (0, items - 1)]
        assert len(found) == 1, f"sMenu do menu do PC ambíguo/ausente: {[hex(a) for a in found]}"
        return found[0] + MENU_CURSOR

    def _choose_menu_item(self, index: int) -> None:
        """Com o menu de múltipla escolha aberto, leva o cursor até `index` e aperta A."""
        addr = self._menu_cursor_addr()
        for _ in range(index + 1):
            cur = self.emu.read_u8(addr)
            if cur == index:
                break
            self.ctl.press_until(KEY_DOWN if index > cur else KEY_UP,
                                 lambda: self.emu.read_u8(addr) != cur, "cursor do menu do PC")
        if self.emu.read_u8(addr) != index:
            raise self.ctl.timeout_error(f"cursor do menu do PC em {self.emu.read_u8(addr)}, "
                                         f"esperava {index}")
        self._press(KEY_A)
