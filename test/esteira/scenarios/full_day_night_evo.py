"""Modo completo: Espeon/Umbreon por horário e Milotic pela Escama Prisma (Hack 7, frente D).

Na build de teste, a partir do .sav do modo rápido. O relógio do jogo é acertado por atalho
(`Mailbox.set_clock`), o Pokémon é montado por atalho (espécie, nível, item segurado, amizade) e a
SUBIDA DE NÍVEL é a de verdade: START > BOLSA > RARE CANDY > USAR > Pokémon, com a cena de evolução
inteira (a condução é a do cenário `evolucoes`):

- evo/espeon: 12:00 (tarde), Eevee nv 20, amizade 220 -> ESPEON; evo/manha_espeon: 06:00 -> ESPEON;
- evo/umbreon: 22:00 (noite) -> UMBREON; evo/entardecer_umbreon: 18:00 (entardecer conta como
  noite) -> UMBREON;
- evo/amizade_baixa: amizade 200 (sobe só +2 no nível) continua Eevee, de dia e de noite;
- evo/milotic: Feebas nv 10 segurando a Escama Prisma -> MILOTIC, ainda segurando;
  evo/feebas_sem_item: sem item continua Feebas;
- evo/loja: a loja de Four Island lista a Escama Prisma a 7000, antes dos 8 itens de empurrão.

Telas da cena: telas/evo_<nome>_antes.png/_depois.png e da loja `evo_loja_prisma.png` (sem
referência; a lista da loja `loja_four_island` do cenário `ovo` mudou com o item novo).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only evo_dia_noite
"""

import sys

from ..breeding import PRICES, SHOP_MONEY, header_defines
from ..emu import KEY_A, KEY_B, KEY_LEFT
from ..hooks import CMD_SET_VAR, CMD_WARP
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_egg import DAYCARE_MAN_FRONT, TO_MART, EggScenario
from .full_evolutions import EvolutionsScenario
from .quick_catch_save import (BUY_MENU_TASK, MART_CLERK_FRONT, SHOP_MENU_TASK, SHOP_TIMEOUT)

EEVEE_LEVEL = 20
FEEBAS_LEVEL = 10
FRIENDSHIP_OK = 220
FRIENDSHIP_LOW = 200
PRISM_PRICE = 7000

# (nome, minuto do dia, amizade, espécie esperada, tela)
EEVEE_CASES = (
    ("evo/espeon: Eevee 20, amizade 220, 12:00 -> Espeon", 12 * 60, FRIENDSHIP_OK,
     "SPECIES_ESPEON", "evo_espeon"),
    ("evo/umbreon: Eevee 20, amizade 220, 22:00 -> Umbreon", 22 * 60, FRIENDSHIP_OK,
     "SPECIES_UMBREON", "evo_umbreon"),
    ("evo/entardecer_umbreon: 18:00 conta como noite -> Umbreon", 18 * 60, FRIENDSHIP_OK,
     "SPECIES_UMBREON", None),
    ("evo/manha_espeon: 06:00 conta como dia -> Espeon", 6 * 60, FRIENDSHIP_OK,
     "SPECIES_ESPEON", None),
    ("evo/amizade_baixa: amizade 200, 12:00 -> continua Eevee", 12 * 60, FRIENDSHIP_LOW,
     "SPECIES_EEVEE", None),
    ("evo/amizade_baixa: amizade 200, 22:00 -> continua Eevee", 22 * 60, FRIENDSHIP_LOW,
     "SPECIES_EEVEE", None),
)


class DayNightEvoScenario(EvolutionsScenario):
    _set_money = EggScenario._set_money
    _shop_cursor_to = EggScenario._shop_cursor_to

    def _item_name(self, item_id: int) -> str:
        if item_id == self.consts.item("ITEM_PRISM_SCALE"):
            return "PRISM_SCALE"
        return super()._item_name(item_id)

    def _set_clock(self, minute: int) -> None:
        got = self.box.set_clock(1, minute)
        assert got == minute, f"SET_CLOCK devolveu {got}, esperava {minute}"

    def _mart(self) -> str:
        var = header_defines(REPO_ROOT, "vars.h")["VAR_MAP_SCENE_FOUR_ISLAND"]
        assert self.box.call(CMD_SET_VAR, var, 1) == 1
        group, num = self.consts.map("MAP_FOUR_ISLAND")
        x, y = DAYCARE_MAN_FRONT
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600,
                            "warp para Four Island")
        self.ctl.wait_overworld_idle(600)
        self._set_money(SHOP_MONEY)
        for point in TO_MART:
            self._walk(*point)
        self._warp("up", "MAP_FOUR_ISLAND_MART")
        self._walk(*MART_CLERK_FRONT)
        self.emu.hold(KEY_LEFT, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do balconista")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: SHOP_MENU_TASK in self._tasks(), SHOP_TIMEOUT,
                            "menu COMPRAR/VENDER/SAIR")
        self.ctl.press_until(KEY_A, lambda: BUY_MENU_TASK in self._tasks(), "lista de compras",
                             tries=5, wait=120)
        items = self._shop_items()
        prism = self.consts.item("ITEM_PRISM_SCALE")
        assert prism in items, f"lista da loja {items}"
        breeding = [items.index(self.consts.item(n)) for n in PRICES if self.consts.item(n) in items]
        assert items.index(prism) < min(breeding), f"Escama Prisma depois dos itens do breeding: {items}"
        price = self.game.item_price(prism)
        assert price == PRISM_PRICE, f"preço no ROM {price}"
        self._shop_cursor_to(items.index(prism))
        self.emu.frames(10)
        self.measures["loja"] = [self._shot("evo_loja_prisma")]
        self.ctl.press_until(KEY_B, lambda: BUY_MENU_TASK not in self._tasks(), "sai da lista")
        self._leave_shop()
        assert self.game.money() == SHOP_MONEY, "o dinheiro mudou sem comprar nada"
        return (f"Four Island Mart vende a Escama Prisma a ₽{price} (posição {items.index(prism)} "
                f"de {len(items)}, antes dos itens do breeding)")

    def run(self) -> None:
        try:
            self._flow("evo_dia_noite: CONTINUAR com o save do modo rápido na build de teste",
                       self._start)
            for name, minute, friendship, expect, shot in EEVEE_CASES:
                self._set_clock(minute)       # poucos quadros antes de usar a Rare Candy
                self._case(name, "SPECIES_EEVEE", EEVEE_LEVEL, None, expect, shot=shot,
                           friendship=friendship)
            self._case("evo/milotic: Feebas 10 + Escama Prisma -> Milotic, ainda segurando",
                       "SPECIES_FEEBAS", FEEBAS_LEVEL, "ITEM_PRISM_SCALE", "SPECIES_MILOTIC",
                       shot="evo_milotic")
            self._case("evo/feebas_sem_item: Feebas 10 sem item -> continua Feebas",
                       "SPECIES_FEEBAS", FEEBAS_LEVEL, None, "SPECIES_FEEBAS")
            self._flow("evo_dia_noite: fecha a bolsa e volta ao jogo", self._close_bag)
            res = self.suite.run("evo/loja: Four Island Mart lista a Escama Prisma a 7000",
                                 self._mart)
            res.images += self.measures.get("loja", [])
        except Abort:
            pass


def run_full_day_night_evo(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    DayNightEvoScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only evo_dia_noite ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "evo_dia_noite",
                     *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
