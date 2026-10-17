"""Modo completo: tour de telas (só screenshots, comparadas com as referências).

Só aperta botões e lê memória. Começa do checkpoint `pc` (Centro de Viridian, diante do PC)
e termina na casa do rival em Pallet, com o checkpoint `telas`.

Cada tela é aberta só com botões, espera ficar pronta (callback2 e a task de entrada da tela
ativos, sem fade de paleta) e mais SETTLE_FRAMES quadros, e vira OUT/telas/<nome>.png com o
nome de refs.TOUR_POINTS; o CLI compara com test/referencias/<INICIAL>/<nome>.png (diferença
é só `aviso`). Telas com dados que mudam de execução para execução (dinheiro, HP, tempo de
jogo, vistos na Pokédex) dão aviso até serem aprovadas para aquele estado.

Telas: bolsa, resumo do inicial, Pokédex, opções, cartão de treinador (menu START); menu do
PC (Centro de Viridian); lista de compras (Viridian Mart); mapa da região (TOWN MAP, que a
Daisy entrega na casa do rival em Pallet depois da Pokédex — data/maps/PalletTown_RivalsHouse).
"""

from ..emu import KEY_A, KEY_B, KEY_LEFT, KEY_UP
from ..field_menu import STARTMENU_BAG, STARTMENU_OPTION, STARTMENU_PLAYER, \
    STARTMENU_POKEDEX, STARTMENU_POKEMON
from ..refs import TOUR_POINTS
from . import ScenarioContext
from .base import Abort
from .pc_menu import MULTICHOICE_TASK, PcMenuMixin
from .quick_catch_save import (BUY_MENU_TASK, MART_CLERK_FRONT, SHOP_MENU_TASK, SHOP_TIMEOUT,
                               CatchSaveScenario)
from .travel import TravelMixin

SETTLE_FRAMES = 30
SCREEN_TIMEOUT = 1200
PALETTE_FADE_ACTIVE = 7         # gPaletteFade: bit 7 do byte 7 (`active`, include/palette.h)

# (callback2, task de entrada) de cada tela pronta (src/*.c)
BAG = ("CB2_BagMenuRun", "Task_BagMenu_HandleInput")
PARTY = ("CB2_UpdatePartyMenu", "Task_HandleChooseMonInput")
PARTY_ACTIONS = ("CB2_UpdatePartyMenu", "Task_HandleSelectionMenuInput")   # RESUMO é a 1ª
SUMMARY = ("CB2_RunPokemonSummaryScreen", "Task_InputHandler_Info")
POKEDEX = ("CB2_PokedexScreen", "Task_PokedexScreen")
OPTIONS = (None, "Task_OptionMenu")
TRAINER_CARD = ("CB2_TrainerCard", "Task_TrainerCard")
REGION_MAP = ("CB2_RegionMap", "Task_RegionMap")

DAISY_FRONT = (5, 5)            # Daisy à mesa em (5, 4) (PalletTown_RivalsHouse_OnTransition)
RIVALS_HOUSE = "MAP_PALLET_TOWN_RIVALS_HOUSE"


class ScreenTourScenario(PcMenuMixin, TravelMixin, CatchSaveScenario):
    # --- espera e foto -------------------------------------------------------------
    def _fade_active(self) -> bool:
        addr = self.game.syms.addr("gPaletteFade") + PALETTE_FADE_ACTIVE
        return bool(self.emu.read_u8(addr) & 0x80)

    def _is_screen(self, screen: tuple[str | None, str]) -> bool:
        callback, task = screen
        return ((callback is None or self.game.callback2() == callback)
                and task in self._tasks() and not self._fade_active())

    def _wait_screen(self, screen, what: str) -> None:
        self.ctl.wait_until(lambda: self._is_screen(screen), SCREEN_TIMEOUT, what)

    def _snap(self, name: str) -> str:
        assert name in TOUR_POINTS, name
        self.emu.frames(SETTLE_FRAMES)
        path = self._shot(name)
        self.measures.setdefault("shots_by_name", {})[name] = path
        return f"tela em {path}"

    def _back_to_start_menu(self, what: str) -> None:
        """B até voltar ao menu START no campo (aceitando botões)."""
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             f"volta ao menu START ({what})", tries=6, wait=120)

    # --- telas do menu START -------------------------------------------------------
    def _start_screen(self, entry: int, screen, name: str) -> str:
        self.menu.open_start_menu()
        self.menu.choose(entry)
        self._wait_screen(screen, f"tela {name}")
        shot = self._snap(name)
        self._back_to_start_menu(name)
        self.menu.close_start_menu()
        return shot

    def _summary(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self._wait_screen(PARTY, "tela de Pokémon")
        self.ctl.press_until(KEY_A, lambda: self._is_screen(PARTY_ACTIONS), "opções do Pokémon",
                             tries=3, wait=60)
        self.ctl.press_until(KEY_A, lambda: self._is_screen(SUMMARY), "resumo do Pokémon",
                             tries=3, wait=120)
        shot = self._snap("resumo")
        self._back_to_start_menu("resumo")
        self.menu.close_start_menu()
        return shot

    # --- PC e loja -----------------------------------------------------------------
    def _pc_screen(self) -> str:
        self._go("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F")
        self._open_pc_menu()
        shot = self._snap("pc")
        self.ctl.press_until(KEY_B, lambda: MULTICHOICE_TASK not in self._tasks(), "PC desligado")
        self.ctl.wait_overworld_idle()
        return shot

    def _shop_screen(self) -> str:
        self._go("MAP_VIRIDIAN_CITY_MART")
        self._walk(*MART_CLERK_FRONT)
        self.emu.hold(KEY_LEFT, 4)          # balconista em (2, 3), balcão em (3, 3)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do balconista")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: SHOP_MENU_TASK in self._tasks(), SHOP_TIMEOUT,
                            "menu COMPRAR/VENDER/SAIR")
        self.ctl.press_until(KEY_A, lambda: BUY_MENU_TASK in self._tasks(), "lista de compras",
                             tries=5, wait=120)
        self.ctl.wait_until(lambda: not self._fade_active(), SCREEN_TIMEOUT, "loja sem fade")
        shot = self._snap("loja")
        self._leave_shop()
        return shot

    # --- mapa da região ------------------------------------------------------------
    def _town_map(self) -> str:
        item = self.consts.item("ITEM_TOWN_MAP")
        if self.game.bag_quantity(item) == 0:
            self._go(RIVALS_HOUSE)
            self._walk(*DAISY_FRONT)
            self._talk(KEY_UP, "Daisy entrega o TOWN MAP")
        qty = self.game.bag_quantity(item)
        assert qty == 1, f"TOWN MAP na bolsa = {qty}, esperava 1 (Daisy)"
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_BAG)
        self.menu.bag.wait_ready()
        self.menu.bag.select(item)
        self.menu.bag.use_selected()
        self._wait_screen(REGION_MAP, "mapa da região")
        shot = self._snap("mapa")
        self._back_to_start_menu("mapa da região")
        self.menu.close_start_menu()
        return shot

    # --- roteiro -------------------------------------------------------------------
    def run(self) -> None:
        steps = [
            ("bolsa", "bolsa (menu START)", lambda: self._start_screen(STARTMENU_BAG, BAG, "bolsa")),
            ("resumo", "resumo do inicial", self._summary),
            ("pokedex", "Pokédex", lambda: self._start_screen(STARTMENU_POKEDEX, POKEDEX,
                                                              "pokedex")),
            ("opcoes", "opções", lambda: self._start_screen(STARTMENU_OPTION, OPTIONS, "opcoes")),
            ("cartao", "cartão de treinador", lambda: self._start_screen(STARTMENU_PLAYER,
                                                                         TRAINER_CARD, "cartao")),
            ("pc", "menu do PC (Centro de Viridian)", self._pc_screen),
            ("loja", "lista de compras (Viridian Mart)", self._shop_screen),
            ("mapa", "mapa da região (TOWN MAP da Daisy)", self._town_map),
        ]
        try:
            for name, label, fn in steps:
                res = self.suite.run(f"telas: {label}", fn)
                if name in self.measures.get("shots_by_name", {}):
                    res.images.append(self.measures["shots_by_name"][name])
                if res.status == "falha":
                    raise Abort(name)
            self.ctl.checkpoint("telas")
        except Abort:
            pass


def run_full_screen_tour(ctx: ScenarioContext) -> None:
    """Roda a partir do checkpoint `pc` já carregado no emulador."""
    ScreenTourScenario(ctx).run()
