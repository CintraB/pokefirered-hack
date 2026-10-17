"""Bolsa (src/item_menu.c) já aberta, na batalha ou no campo: bolso, cursor e USAR.

gBagMenuState {callback, location, bagOpen, pocket u16, itemsAbove[3] u16,
cursorPos[3] u16}; menu de Pokémon: gPartyMenu.slotId em +9 (src/party_menu.c).
"""

from .control import Controller
from .emu import KEY_A, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP

BAG_POCKET = 0x06              # gBagMenuState.pocket (u16)
BAG_ITEMS_ABOVE = 0x08         # gBagMenuState.itemsAbove[3] (u16)
BAG_CURSOR_POS = 0x0E          # gBagMenuState.cursorPos[3] (u16)
NUM_BAG_POCKETS_NO_CASES = 3   # Itens, Itens-chave, Poké Balls
PARTY_MENU_SLOT_ID = 0x09      # gPartyMenu.slotId (s8)

BAG_INPUT_TASK = "Task_BagMenu_HandleInput"
BAG_CONTEXT_TASK = "Task_FieldItemContextMenuHandleInput"
PARTY_CHOOSE_TASK = "Task_HandleChooseMonInput"
MENU_TIMEOUT = 600


class Bag:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.game = controller.game
        self.emu = controller.emu
        self.syms = controller.game.syms

    def find(self, item_id: int) -> tuple[int, int]:
        """(bolso, posição na lista) de `item_id`; AssertionError se não estiver na bolsa."""
        for pocket in range(NUM_BAG_POCKETS_NO_CASES):
            items = [item for item, _qty in self.game.bag_pocket(pocket)]
            if item_id in items:
                return pocket, items.index(item_id)
        raise AssertionError(f"item {item_id} não está na bolsa")

    def ready(self) -> bool:
        return BAG_INPUT_TASK in self.game.active_tasks()

    def wait_ready(self) -> None:
        self.ctl.wait_until(self.ready, MENU_TIMEOUT, "bolsa aberta")

    def select(self, item_id: int) -> None:
        """Com a bolsa aberta, vai ao bolso de `item_id` e põe o cursor sobre ele."""
        pocket, index = self.find(item_id)
        state = self.syms.addr("gBagMenuState")
        current_pocket = lambda: self.emu.read_u16(state + BAG_POCKET)
        for _ in range(NUM_BAG_POCKETS_NO_CASES):
            cur = current_pocket()
            if cur == pocket:
                break
            self.ctl.press_until(KEY_RIGHT if pocket > cur else KEY_LEFT,
                                 lambda: current_pocket() != cur and self.ready(),
                                 "troca de bolso")
        if current_pocket() != pocket:
            raise self.ctl.timeout_error(f"bolso {pocket} da bolsa")

        def position() -> int:
            return (self.emu.read_u16(state + BAG_CURSOR_POS + pocket * 2)
                    + self.emu.read_u16(state + BAG_ITEMS_ABOVE + pocket * 2))

        for _ in range(64):
            cur = position()
            if cur == index:
                return
            self.ctl.press_until(KEY_DOWN if index > cur else KEY_UP,
                                 lambda: position() != cur, "cursor da bolsa")
        raise self.ctl.timeout_error(f"cursor da bolsa no item {item_id} (posição "
                                     f"{position()}, esperava {index})")

    def use_selected(self) -> None:
        """Confirma o item sob o cursor e escolhe USAR (1ª opção do menu de contexto)."""
        in_context = lambda: BAG_CONTEXT_TASK in self.game.active_tasks()
        self.ctl.press_until(KEY_A, in_context, "menu USAR/CANCELAR")
        self.ctl.press_until(KEY_A, lambda: not in_context(), "USAR")

    def choose_party_slot(self, slot: int) -> None:
        """No menu de Pokémon aberto pelo item, escolhe o Pokémon `slot` (layout simples:
        BAIXO avança um slot)."""
        party_ready = lambda: PARTY_CHOOSE_TASK in self.game.active_tasks()
        self.ctl.wait_until(party_ready, MENU_TIMEOUT, "escolha do Pokémon para o item")
        addr = self.syms.addr("gPartyMenu") + PARTY_MENU_SLOT_ID
        for _ in range(8):
            cur = self.emu.read_u8(addr)
            if cur == slot:
                break
            self.ctl.press_until(KEY_LEFT if slot == 0 else KEY_DOWN,
                                 lambda: self.emu.read_u8(addr) != cur,
                                 f"cursor do menu de Pokémon no slot {slot}")
        if self.emu.read_u8(addr) != slot:
            raise self.ctl.timeout_error(f"cursor do menu de Pokémon no slot {slot}")
        self.ctl.press_until(KEY_A, lambda: not party_ready(), f"item usado no slot {slot}")
