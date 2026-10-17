"""Menu START do campo (src/start_menu.c) só com botões: bolsa (usar item num Pokémon) e
salvar o jogo.

O menu guarda a ordem das entradas em sStartMenuOrder[sNumStartMenuItems] (valores do enum
STARTMENU_* de src/start_menu.c) e o cursor em sStartMenuCursorPos. O resultado do save
fica em gSaveAttemptStatus (SAVE_STATUS_* de include/save.h).
"""

from .bag import Bag
from .control import Controller
from .emu import KEY_A, KEY_B, KEY_DOWN, KEY_START, KEY_UP

STARTMENU_BAG = 2
STARTMENU_SAVE = 4
MAX_STARTMENU_ITEMS = 9
SAVE_STATUS_OK = 1

START_MENU_TASK = "Task_StartMenuHandleInput"
# menu de Pokémon e a animação "POTION foi usada em X" (src/pokemon_special_anim.c)
ITEM_USE_CALLBACKS = {"CB2_UpdatePartyMenu", "CB2_PSA"}
TEXT_PERIOD = 10
MENU_TIMEOUT = 600
ITEM_USE_TIMEOUT = 1500
SAVE_TIMEOUT = 3000


class FieldMenu:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.game = controller.game
        self.emu = controller.emu
        self.syms = controller.game.syms
        self.bag = Bag(controller)

    def _press(self, key: int) -> None:
        self.emu.press(key, hold=2, release=TEXT_PERIOD - 2)

    def start_menu_open(self) -> bool:
        return START_MENU_TASK in self.game.active_tasks()

    def open_start_menu(self) -> None:
        self.ctl.wait_overworld_idle()
        self.ctl.press_until(KEY_START, self.start_menu_open, "menu START aberto")

    def entries(self) -> list[int]:
        count = self.emu.read_u8(self.syms.addr("sNumStartMenuItems"))
        return list(self.emu.read(self.syms.addr("sStartMenuOrder"), min(count, MAX_STARTMENU_ITEMS)))

    def choose(self, entry: int) -> None:
        """Com o menu START aberto, põe o cursor na entrada `entry` e aperta A."""
        entries = self.entries()
        if entry not in entries:
            raise AssertionError(f"entrada {entry} fora do menu START {entries}")
        index = entries.index(entry)
        addr = self.syms.addr("sStartMenuCursorPos")
        for _ in range(MAX_STARTMENU_ITEMS):
            cur = self.emu.read_u8(addr)
            if cur == index:
                break
            self.ctl.press_until(KEY_DOWN if index > cur else KEY_UP,
                                 lambda: self.emu.read_u8(addr) != cur, "cursor do menu START")
        if self.emu.read_u8(addr) != index:
            raise self.ctl.timeout_error(f"cursor do menu START em {self.emu.read_u8(addr)}, "
                                         f"esperava {index}")
        self._press(KEY_A)

    def close_start_menu(self) -> None:
        self.ctl.press_until(KEY_B, lambda: not self.start_menu_open(), "menu START fechado")
        self.ctl.wait_overworld_idle()

    def use_item_on_mon(self, item_id: int, slot: int) -> int:
        """START > BOLSA > item > USAR > Pokémon `slot`; fecha bolsa e menu. Devolve o HP do
        Pokémon depois do item."""
        self.open_start_menu()
        self.choose(STARTMENU_BAG)
        self.bag.wait_ready()
        self.bag.select(item_id)
        self.bag.use_selected()
        self.bag.choose_party_slot(slot)
        # animação + "O HP de X foi restaurado..." esperam A; depois a bolsa volta
        spent = 0
        while not self.bag.ready():
            if spent >= ITEM_USE_TIMEOUT:
                raise self.ctl.timeout_error("volta à bolsa depois de usar o item")
            if self.game.callback2() in ITEM_USE_CALLBACKS:
                self._press(KEY_A)
            else:
                self.emu.frames(TEXT_PERIOD)
            spent += TEXT_PERIOD
        hp = self.game.party()[slot].hp
        self.ctl.press_until(KEY_B, lambda: not self.bag.ready(), "bolsa fechada")
        self.ctl.wait_until(self.start_menu_open, MENU_TIMEOUT, "menu START depois da bolsa")
        self.close_start_menu()
        return hp

    def save_game(self) -> int:
        """START > SALVAR > SIM (e SIM para sobrescrever, se perguntar); espera o overworld.
        Devolve gSaveAttemptStatus."""
        self.open_start_menu()
        self.choose(STARTMENU_SAVE)
        spent = 0
        while self.start_menu_open():   # a task do menu conduz o diálogo inteiro do save
            if spent >= SAVE_TIMEOUT:
                raise self.ctl.timeout_error("fim do diálogo de salvar")
            self._press(KEY_A)
            spent += TEXT_PERIOD
        self.ctl.wait_overworld_idle()
        return self.emu.read_u16(self.syms.addr("gSaveAttemptStatus"))
