"""Roteiro rápido C: compra no Viridian Mart, captura com apelido, Potion, Centro e save.

Só aperta botões e lê memória. Começa do checkpoint `encomenda` (Task 6: no laboratório,
com a Pokédex e 5 Poké Balls do Oak). Checkpoints: `captura` (capturado com apelido no time),
`centro` (time curado no Centro de Viridian) e `save` (de volta ao jogo depois de salvar,
reiniciar e escolher CONTINUAR). O modo completo (Task 11) continua de `save`.

Adaptativo (RNG livre): lança bolas até capturar; se o selvagem fugir/desmaiar ou o time
todo desmaiar (o jogo leva ao Centro), procura outro, até MAX_CATCH_ENCOUNTERS encontros.
Se só o inicial desmaiar (o capturado entra no lugar), a batalha termina e o roteiro volta ao
Centro antes de tentar de novo. O 1º passo pelo Centro de Viridian fixa ali o ponto de
retorno (setrespawn em data/maps/ViridianCity_PokemonCenter_1F/scripts.inc).

Uso avulso (até o CLI do Task 8 existir), a partir de test/:
    python3 -m esteira.scenarios.quick_catch_save --starter BULBASAUR --out out/captura
Se OUT/estados/encomenda.ss existir (gerado por quick_route1 na mesma pasta), começa dele;
senão roda a abertura e o roteiro B antes.
"""

import argparse
import struct
import sys
import time

from ..battle import NICKNAME_COMMAND, OUTCOME_NAMES
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_LEFT, KEY_START, KEY_UP
from ..field_menu import SAVE_STATUS_OK, FieldMenu
from ..naming import NamingScreen
from ..rotation import STARTERS
from . import REPO_ROOT, ScenarioContext, open_context
from .base import TEXT_PERIOD, Abort, print_summary
from .quick_opening import run_opening
from .quick_route1 import (HEAL_BELOW, LAB_EXIT, MART_EXIT, MAX_RUN_TRIES, POST_BATTLE_TIMEOUT,
                           ROUTE1_NORTH_EDGE, VIRIDIAN_SOUTH_EDGE,
                           Route1Scenario, run_route1)

NICKNAME = "ESTEIRA"
BALLS_TO_BUY = 10
POTIONS_TO_BUY = 3
POTION_HEAL = 20                    # sItemEffect_Potion (src/data/pokemon/item_effects.h)
MAX_CATCH_ENCOUNTERS = 5
MAX_POTION_ENCOUNTERS = 6
MAX_TURNS = 20                      # turnos lutando numa batalha até o inicial levar um golpe

# Coordenadas de data/maps/*/map.json e dos layouts (grades conferidas com nav.py).
MART_CLERK_FRONT = (4, 3)           # balconista em (2,3), balcão em (3,3): fala para a esquerda
VIRIDIAN_CENTER_FRONT = (26, 27)    # porta do Centro em (26,26)
CENTER_NURSE_FRONT = (7, 4)         # enfermeira em (7,2), balcão em (7,3)
CENTER_EXIT = (7, 7)                # warps em (6..8, 8), sai com "down"
CATCH_GRASS = ((17, 6), (17, 9))    # grama alta do norte da Rota 1 (x 10..21, y 6..10)

# src/shop.c: struct ShopData {callback, itemList*, itemPrice, selectedRow u16 (0x0C),
# scrollOffset u16 (0x0E), itemCount u16 (0x10), ...}; quantidade em data[1] (tItemCount).
SHOP_ITEM_LIST = 0x04
SHOP_SELECTED_ROW = 0x0C
SHOP_SCROLL_OFFSET = 0x0E
SHOP_ITEM_COUNT = 0x10
SHOP_QUANTITY_DATA = 1
SHOP_MENU_TASK = "Task_ShopMenu"
BUY_MENU_TASK = "Task_BuyMenu"
BUY_QUANTITY_TASK = "Task_BuyHowManyDialogueHandleInput"

# src/battle_script_commands.c, Cmd_trygivecaughtmonnick: gBattleCommunication[0] == 1
# enquanto o sim/não do apelido espera resposta.
NICKNAME_YESNO_STATE = 1

# Reset e CONTINUAR (src/main_menu.c, src/quest_log.c, include/save.h)
TITLE_TIMEOUT = 6000
MAIN_MENU_TASK = "Task_HandleMenuInput"
MAIN_MENU_CALLBACK = "CB2_MainMenu"
QL_PLAYBACK_BUSY = {1, 3}           # QL_PLAYBACK_STATE_RUNNING / _ACTION_END

SHOP_TIMEOUT = 3000
NICKNAME_TIMEOUT = 3000
CAPTURE_END_TIMEOUT = 3000
WHITEOUT_TIMEOUT = 6000
CONTINUE_TIMEOUT = 20000


class OwnMonFainted(AssertionError):
    """O time todo desmaiou numa batalha; o jogo já levou o jogador ao Centro."""


class CatchSaveScenario(Route1Scenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.menu = FieldMenu(self.ctl)
        self.measures.update(whiteouts=0, center_visits=0, catch_log=[], potion_log=[])

    # --- recuperação ---------------------------------------------------------------
    def _after_battle(self, what: str) -> None:
        """Time todo desmaiado: avança o desmaio/cura no Centro e levanta OwnMonFainted."""
        if OUTCOME_NAMES.get(self.driver.outcome()) == "lose":
            self.measures["whiteouts"] += 1
            shot = self._shot(f"desmaio-{self.measures['whiteouts']}")
            self._finish_script(f"{what}: time desmaiado, volta ao Centro", WHITEOUT_TIMEOUT)
            raise OwnMonFainted(f"{what}: o time todo desmaiou (tela: {shot})")
        self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)

    def _end_battle(self, what: str) -> None:
        """Encerra a batalha em curso fugindo (ou lutando, se a fuga falhar)."""
        if self.game.in_battle():
            for _ in range(MAX_RUN_TRIES):
                if self.driver.run_away() or not self.game.in_battle():
                    break
            if self.game.in_battle():
                self.driver.fight_to_end()
        self._after_battle(what)

    def _go_to_center(self) -> None:
        if self.game.location() == self._map("MAP_VIRIDIAN_CITY_MART"):
            self._walk(*MART_EXIT)
            self._warp("down", "MAP_VIRIDIAN_CITY")
        if self.game.location() == self._map("MAP_ROUTE1"):
            self._walk(*ROUTE1_NORTH_EDGE)
            self._cross("up", "MAP_VIRIDIAN_CITY")
        if self.game.location() == self._map("MAP_VIRIDIAN_CITY"):
            self._walk(*VIRIDIAN_CENTER_FRONT)
            self._warp(None, "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F")
        self._expect_map("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F")

    def _heal_at_center(self) -> None:
        self._go_to_center()
        self._walk(*CENTER_NURSE_FRONT)
        self._talk(KEY_UP, "enfermeira cura o time")
        self.measures["center_visits"] += 1

    def _needs_center(self) -> bool:
        party = self.game.party()
        return (any(mon.hp == 0 for mon in party)
                or party[0].hp < party[0].max_hp * HEAL_BELOW)

    def _go_to_catch_grass(self) -> None:
        if self._needs_center():
            self._heal_at_center()
        loc = self.game.location()
        if loc == self._map("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F"):
            self._walk(*CENTER_EXIT)
            self._warp("down", "MAP_VIRIDIAN_CITY")
        elif loc == self._map("MAP_VIRIDIAN_CITY_MART"):
            self._walk(*MART_EXIT)
            self._warp("down", "MAP_VIRIDIAN_CITY")
        if self.game.location() == self._map("MAP_VIRIDIAN_CITY"):
            self._walk(*VIRIDIAN_SOUTH_EDGE)
            self._cross("down", "MAP_ROUTE1")
        self._expect_map("MAP_ROUTE1")
        if self.game.player_xy() not in CATCH_GRASS:
            self._walk(*CATCH_GRASS[1])

    def _wild_battle(self) -> str:
        """Acha um selvagem na grama do norte da Rota 1 e para no menu de ação."""
        self._go_to_catch_grass()
        self._find_wild_battle(CATCH_GRASS)
        self.driver.wait_action_menu()
        species, level = self.driver.battler_species_level(1)
        return f"{self._species(species)} nv{level}"

    # --- Viridian Mart -------------------------------------------------------------
    def _go_to_mart_door(self) -> None:
        if self.game.location() == self._map("MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB"):
            self._walk(*LAB_EXIT)
            self._warp("down", "MAP_PALLET_TOWN")
        self._go_to_mart()
        self._warp(None, "MAP_VIRIDIAN_CITY_MART")

    def _shop_cursor(self) -> int:
        shop = self.game.syms.addr("sShopData")
        return (self.emu.read_u16(shop + SHOP_SELECTED_ROW)
                + self.emu.read_u16(shop + SHOP_SCROLL_OFFSET))

    def _shop_items(self) -> list[int]:
        shop = self.game.syms.addr("sShopData")
        count = self.emu.read_u16(shop + SHOP_ITEM_COUNT)
        return list(struct.unpack(f"<{count}H", self.emu.read(self.emu.read_u32(
            shop + SHOP_ITEM_LIST), count * 2)))

    def _buy(self, item_id: int, qty: int) -> None:
        """Na lista de compras: item, quantidade `qty`, SIM, e de volta à lista."""
        tasks = self._tasks
        items = self._shop_items()
        if item_id not in items:
            raise AssertionError(f"item {item_id} não está à venda ({items})")
        index = items.index(item_id)
        for _ in range(len(items) + 1):
            cur = self._shop_cursor()
            if cur == index:
                break
            self.ctl.press_until(KEY_DOWN if index > cur else KEY_UP,
                                 lambda: self._shop_cursor() != cur, "cursor da loja")
        if self._shop_cursor() != index:
            raise self.ctl.timeout_error(f"cursor da loja em {self._shop_cursor()}, esperava {index}")
        quantity = lambda: (self.game.task_data(BUY_QUANTITY_TASK) or [0, 0])[SHOP_QUANTITY_DATA]
        self.ctl.press_until(KEY_A, lambda: BUY_QUANTITY_TASK in tasks(), "quantidade na loja",
                             tries=5, wait=120)
        for _ in range(qty):
            cur = quantity()
            if cur == qty:
                break
            self.ctl.press_until(KEY_UP, lambda: quantity() != cur, "quantidade na loja")
        if quantity() != qty:
            raise self.ctl.timeout_error(f"quantidade {quantity()}, esperava {qty}")
        spent = 0
        self._press(KEY_A)                          # confirma; depois SIM e "Aqui está!"
        while BUY_MENU_TASK not in tasks():
            if spent >= SHOP_TIMEOUT:
                raise self.ctl.timeout_error("compra confirmada e volta à lista")
            self._press(KEY_A)
            spent += TEXT_PERIOD

    def _leave_shop(self) -> None:
        """B sai da lista; "Mais alguma coisa?" volta ao menu da loja sem esperar botão, e
        B sai dele (A ali entraria de novo na loja). Só então A avança o "Volte sempre!"."""
        self.ctl.press_until(KEY_B, lambda: BUY_MENU_TASK not in self._tasks(), "saída da lista")
        shop_menu = lambda: SHOP_MENU_TASK in self._tasks()
        self.ctl.wait_until(shop_menu, SHOP_TIMEOUT, "volta ao menu COMPRAR/VENDER/SAIR")
        self.ctl.press_until(KEY_B, lambda: not shop_menu(), "saída do menu da loja")
        self._finish_script("fim da conversa com o balconista", SHOP_TIMEOUT)

    def _shop(self) -> str:
        game, consts = self.game, self.consts
        ball, potion = consts.item("ITEM_POKE_BALL"), consts.item("ITEM_POTION")
        money0, balls0, potions0 = game.money(), game.bag_quantity(ball), game.bag_quantity(potion)
        self._walk(*MART_CLERK_FRONT)
        self.emu.hold(KEY_LEFT, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do balconista")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: SHOP_MENU_TASK in self._tasks(), SHOP_TIMEOUT,
                            "menu COMPRAR/VENDER/SAIR")
        self.ctl.press_until(KEY_A, lambda: BUY_MENU_TASK in self._tasks(), "lista de compras",
                             tries=5, wait=120)
        self._buy(ball, BALLS_TO_BUY)
        self._buy(potion, POTIONS_TO_BUY)
        self._leave_shop()
        cost = BALLS_TO_BUY * game.item_price(ball) + POTIONS_TO_BUY * game.item_price(potion)
        money, balls, potions = game.money(), game.bag_quantity(ball), game.bag_quantity(potion)
        assert balls == balls0 + BALLS_TO_BUY, f"Poké Balls {balls0} -> {balls}, esperava +{BALLS_TO_BUY}"
        assert potions == potions0 + POTIONS_TO_BUY, (
            f"Potions {potions0} -> {potions}, esperava +{POTIONS_TO_BUY}")
        assert money == money0 - cost, f"dinheiro {money0} -> {money}, esperava -{cost}"
        return (f"Poké Balls {balls0} -> {balls}, Potions {potions0} -> {potions}, "
                f"dinheiro {money0} -> {money} (-{cost})")

    # --- captura e apelido ---------------------------------------------------------
    def _give_nickname(self) -> None:
        """SIM no "Dar apelido?", digita NICKNAME e deixa a batalha terminar."""
        naming = NamingScreen(self.ctl)
        state = self.game.syms.addr("gBattleCommunication")

        def opened() -> bool:
            if naming.is_open():
                return True
            if (self.driver._script_command() == NICKNAME_COMMAND
                    and self.emu.read_u8(state) == NICKNAME_YESNO_STATE):
                self._press(KEY_A)                  # SIM (cursor começa em SIM)
            return False

        self.ctl.wait_until(opened, NICKNAME_TIMEOUT, "tela de apelido")
        self.measures["nickname_screen"] = True
        naming.type_text(NICKNAME)
        self.ctl.advance_text(lambda: not self.game.in_battle(), CAPTURE_END_TIMEOUT,
                              "fim da batalha da captura")
        self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)

    def _catch(self) -> str:
        ball = self.consts.item("ITEM_POKE_BALL")
        log = self.measures["catch_log"]
        for n in range(1, MAX_CATCH_ENCOUNTERS + 1):
            try:
                wild = self._wild_battle()
                species = self.driver.battler_species_level(1)[0]
                thrown = 0
                while self.game.in_battle():
                    if self.game.bag_quantity(ball) == 0:
                        raise AssertionError(f"acabaram as Poké Balls; tentativas: {log}")
                    thrown += 1
                    if self.driver.throw_ball(ball):
                        self.measures["catch_shot"] = self._shot("captura")
                        log.append(f"{wild}: capturado na {thrown}ª bola")
                        self.measures["caught"] = (species, wild)
                        self._give_nickname()
                        return f"{n} encontro(s): " + "; ".join(log)
                outcome = OUTCOME_NAMES.get(self.driver.outcome(), str(self.driver.outcome()))
                log.append(f"{wild}: {thrown} bola(s), batalha terminou em {outcome}")
                self._after_battle("batalha da captura")
            except OwnMonFainted as exc:
                log.append(str(exc))
        raise AssertionError(f"não capturou em {MAX_CATCH_ENCOUNTERS} encontros: {log}")

    def phase_catch(self) -> None:
        self._flow("captura: caminho até o Viridian Mart", self._go_to_mart_door)
        self._flow(f"captura: compra {BALLS_TO_BUY} Poké Balls e {POTIONS_TO_BUY} Potions "
                   "no Viridian Mart", self._shop)
        self._flow("captura: Centro de Viridian (cura e ponto de retorno)", self._heal_at_center)
        self._flow(f"captura: lança Poké Balls até capturar (máx. {MAX_CATCH_ENCOUNTERS} "
                   "encontros)", self._catch)

        def check_party() -> str:
            party = self.game.party()
            species, wild = self.measures["caught"]
            assert len(party) == 2, f"time com {len(party)} Pokémon, esperava 2"
            assert party[1].species == species, (
                f"party()[1] é da espécie {party[1].species}, esperava {wild} ({species})")
            return f"{wild} em party()[1] (nível {party[1].level}, HP {party[1].hp}/{party[1].max_hp})"

        res = self.suite.run("captura: capturado entra no time", check_party)
        if "catch_shot" in self.measures:
            res.images.append(self.measures["catch_shot"])

        def check_nickname() -> str:
            party = self.game.party()
            assert self.measures.get("nickname_screen"), "a tela de apelido não abriu"
            assert len(party) > 1 and party[1].nickname == NICKNAME, (
                f"apelido {party[1].nickname if len(party) > 1 else None!r}, esperava {NICKNAME!r}")
            return f"party()[1].nickname == {NICKNAME!r} (digitado na tela de nome)"

        self.suite.run(f"captura: apelido {NICKNAME!r} digitado", check_nickname)
        self.ctl.checkpoint("captura")

    # --- Potion --------------------------------------------------------------------
    def _potion_in_battle(self) -> str:
        potion = self.consts.item("ITEM_POTION")
        log = self.measures["potion_log"]
        for _ in range(MAX_POTION_ENCOUNTERS):
            try:
                wild = self._wild_battle()
                for _turn in range(MAX_TURNS):
                    mon = self.game.party()[0]
                    if mon.hp == 0:
                        break                       # o inicial desmaiou; o capturado entrou
                    if mon.hp < mon.max_hp:
                        count = self.game.bag_quantity(potion)
                        after = self.driver.use_item_in_battle(potion, 0)
                        left = self.game.bag_quantity(potion)
                        self._end_battle("batalha da Potion")
                        want = mon.hp + min(POTION_HEAL, mon.max_hp - mon.hp)
                        assert after == want, (f"HP {mon.hp}/{mon.max_hp} -> {after} depois da "
                                               f"Potion, esperava {want}")
                        assert left == count - 1, f"Potions {count} -> {left}, esperava -1"
                        log.append(f"{wild}: HP {mon.hp} -> {after}/{mon.max_hp}")
                        return "; ".join(log)
                    if self.driver.fight_turn() == "end":
                        break
                log.append(f"{wild}: sem golpe recebido a tempo")
                self._end_battle("batalha da Potion")
            except OwnMonFainted as exc:
                log.append(str(exc))
        raise AssertionError(f"Potion em batalha não testada em {MAX_POTION_ENCOUNTERS} "
                             f"encontros: {log}")

    def _get_hit(self) -> None:
        """Garante o inicial vivo e ferido (para a Potion ter efeito), lutando se preciso."""
        log = []
        for _ in range(MAX_POTION_ENCOUNTERS):
            mon = self.game.party()[0]
            if 0 < mon.hp < mon.max_hp:
                return
            try:
                if mon.hp == 0:
                    self._heal_at_center()
                wild = self._wild_battle()
                for _turn in range(MAX_TURNS):
                    mon = self.game.party()[0]
                    if mon.hp < mon.max_hp or self.driver.fight_turn() == "end":
                        break
                log.append(wild)
                self._end_battle("batalha antes da Potion fora da batalha")
            except OwnMonFainted as exc:
                log.append(str(exc))
        raise AssertionError(f"o inicial não ficou ferido em {MAX_POTION_ENCOUNTERS} "
                             f"encontros: {log}")

    def _potion_in_field(self) -> str:
        potion = self.consts.item("ITEM_POTION")
        self._get_hit()
        mon = self.game.party()[0]
        count = self.game.bag_quantity(potion)
        after = self.menu.use_item_on_mon(potion, 0)
        now = self.game.party()[0].hp
        left = self.game.bag_quantity(potion)
        want = mon.hp + min(POTION_HEAL, mon.max_hp - mon.hp)
        assert after == want and now == want, (
            f"HP {mon.hp}/{mon.max_hp} -> {after} (agora {now}), esperava {want}")
        assert left == count - 1, f"Potions {count} -> {left}, esperava -1"
        return f"HP {mon.hp} -> {after}/{mon.max_hp} pela BOLSA do menu START"

    def phase_potion(self) -> None:
        self._flow("potion: em batalha, HP sobe exatamente min(20, max_hp - hp)",
                   self._potion_in_battle)
        self._flow("potion: fora da batalha, HP sobe exatamente min(20, max_hp - hp)",
                   self._potion_in_field)

    # --- Centro --------------------------------------------------------------------
    def _center(self) -> str:
        self._get_hit()                 # chega com HP faltando, senão a cura de HP não é testada
        before = self.game.party()
        self._heal_at_center()
        party = self.game.party()
        wrong = []
        for i, mon in enumerate(party):
            full_pp = [self.game.move_max_pp(mon, j) for j in range(len(mon.moves))]
            if mon.hp != mon.max_hp or mon.pp != full_pp:
                wrong.append(f"[{i}] HP {mon.hp}/{mon.max_hp}, PP {mon.pp} (cheio {full_pp})")
        assert len(party) == len(before) == 2, f"time com {len(party)} Pokémon, esperava 2"
        assert not wrong, "time não ficou curado: " + "; ".join(wrong)
        changes = [f"[{i}] HP {b.hp}->{a.hp}/{a.max_hp}, PP {b.pp}->{a.pp}"
                   for i, (b, a) in enumerate(zip(before, party))]
        return "; ".join(changes)

    def phase_center(self) -> None:
        self._flow("centro: enfermeira cura HP e PP de todo o time", self._center)
        self.ctl.checkpoint("centro")

    # --- save, reset e CONTINUAR ---------------------------------------------------
    def _snapshot(self) -> dict:
        game = self.game
        items = sorted({item for pocket in range(5) for item, _qty in game.bag_pocket(pocket)})
        return {
            "party": game.party(),
            "money": game.money(),
            "bag": {item: game.bag_quantity(item) for item in items},
            "location": game.location(),
            "player_xy": game.player_xy(),
        }

    def _save(self) -> str:
        status = self.menu.save_game()
        self.measures["save_shot"] = self._shot("save")
        assert status == SAVE_STATUS_OK, (
            f"gSaveAttemptStatus = {status}, esperava SAVE_STATUS_OK ({SAVE_STATUS_OK})")
        self.measures["before_reset"] = self._snapshot()
        return f"gSaveAttemptStatus = {status} (SAVE_STATUS_OK) em {self.game.location()}"

    def _continue_after_reset(self) -> str:
        before = self.measures["before_reset"]
        game, syms = self.game, self.game.syms
        self.emu.reset()
        self.ctl.wait_until(lambda: "TitleScreen" in game.callback2(), TITLE_TIMEOUT,
                            "tela de título depois do reset")
        self.ctl.press_until(KEY_START, lambda: MAIN_MENU_TASK in self._tasks(),
                             "menu principal", tries=20, wait=60)
        status = self.emu.read_u16(syms.addr("gSaveFileStatus"))
        assert status == SAVE_STATUS_OK, (
            f"gSaveFileStatus = {status} depois do reset, esperava SAVE_STATUS_OK")
        self.measures["continue_shot"] = self._shot("continuar")
        self.ctl.press_until(KEY_A, lambda: MAIN_MENU_TASK not in self._tasks(), "CONTINUAR")
        playback = syms.addr("gQuestLogPlaybackState")
        spent = 0
        # "Na última vez..." (diário de viagem) pode tocar antes do jogo: B pula
        while not (self.emu.read_u8(playback) not in QL_PLAYBACK_BUSY and self._settled_idle()):
            if spent >= CONTINUE_TIMEOUT:
                raise self.ctl.timeout_error("jogo livre depois de CONTINUAR")
            if game.callback2() != MAIN_MENU_CALLBACK:
                self._press(KEY_B)
            else:
                self.emu.frames(TEXT_PERIOD)
            spent += TEXT_PERIOD
        after = self._snapshot()
        diffs = [f"{key}: antes {before[key]!r}, depois {after[key]!r}"
                 for key in before if before[key] != after[key]]
        assert not diffs, "estado diferente depois de reset + CONTINUAR: " + " | ".join(diffs)
        party = after["party"]
        return (f"time {[(m.nickname, m.level, m.hp) for m in party]}, dinheiro {after['money']}, "
                f"bolsa {after['bag']}, local {after['location']} {after['player_xy']}")

    def phase_save(self) -> None:
        res = self.suite.run("save: salvar pelo menu START", self._save)
        if "save_shot" in self.measures:
            res.images.append(self.measures["save_shot"])
        if res.status == "falha":
            raise Abort("save")
        res = self.suite.run("save: reset + CONTINUAR devolvem time, dinheiro, bolsa e local",
                             self._continue_after_reset)
        if "continue_shot" in self.measures:
            res.images.append(self.measures["continue_shot"])
        if res.status == "falha":
            raise Abort("continuar")
        self.ctl.checkpoint("save")

    def run(self) -> None:
        try:
            self.phase_catch()
            self.phase_potion()
            self.phase_center()
            self.phase_save()
        except Abort:
            pass


def run_catch_save(ctx: ScenarioContext) -> None:
    """Roda o roteiro C a partir do checkpoint `encomenda` já carregado no emulador."""
    CatchSaveScenario(ctx).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roteiro rápido C (captura, Potion, Centro, save)")
    parser.add_argument("--starter", required=True, choices=STARTERS)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rom", default=str(REPO_ROOT / "pokefirered_switch.gba"))
    parser.add_argument("--elf", default=str(REPO_ROOT / "pokefirered_switch.elf"))
    args = parser.parse_args(argv)
    start = time.monotonic()
    with open_context(args.rom, args.elf, args.out, args.starter) as ctx:
        if ctx.controller.checkpoint_path("encomenda").is_file():
            ctx.controller.restore("encomenda")
            species = ctx.game.party()[0].species
            if species != ctx.consts.species(args.starter):
                parser.error(f"o checkpoint encomenda de {args.out} é de "
                             f"{ctx.consts.species_name(species)}, não de {args.starter}")
        else:
            run_opening(ctx)
            if not ctx.suite.failed():
                run_route1(ctx)
        if not ctx.suite.failed():
            run_catch_save(ctx)
        frames = ctx.emu.frames(0)
    return print_summary(ctx.suite, time.monotonic() - start, frames)


if __name__ == "__main__":
    sys.exit(main())
