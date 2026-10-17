"""Modo completo: Floresta de Viridian, Brock e o tênis de corrida (Pallet/Viridian -> Pewter).

Só aperta botões e lê memória. Começa do checkpoint `telas` (em Pallet, depois do tour de
telas) e termina em Pewter, com o checkpoint `brock`.

1. Centro de Viridian cura; a saída norte de Viridian passa pelo tutorial de captura do velho
   (dá a TEACHY TV) e a Rota 2 leva à Floresta;
2. treino na grama da Rota 2 (sul) até FOREST_LEVEL, curando no Centro de Viridian;
3. atravessa a Floresta: o caminho mais curto passa na frente do Bug Catcher SAMMY (o único
   inevitável). Toda batalha de treinador confere o dinheiro: sobe exatamente o prêmio de
   Cmd_getmoneyreward (4 x nível do último Pokémon x gTrainerMoneyTable[classe] x
   moneyMultiplier), lido da memória na batalha (travel.trainer_reward);
4. em Pewter: Centro (ponto de retorno) e treino na grama da Rota 2 (norte) até o nível de
   BROCK_LEVEL do inicial (medido com o Charmander, de savestates com o RNG variado:
   Charmeleon nv16 venceu 6 de 8, nv17 15 de 20, nv18 11 de 12);
5. Brock: até BROCK_ATTEMPTS tentativas, cada uma comprando antes as Potions que o dinheiro
   pagar (Pewter Mart). O caminho até ele passa pelo Camper LIAM; depois dessa luta o roteiro
   compra Potions com o prêmio, cura e volta. Perdendo,
   o jogo leva ao Centro de Pewter e o roteiro treina mais RETRAIN_LEVELS níveis antes de
   tentar de novo. Na batalha o driver escolhe o golpe de maior dano esperado
   (BattleDriver.move_policy "best") e usa Potion abaixo de BROCK_HEAL_BELOW do HP; vencer
   liga FLAG_BADGE01_GET (os prêmios do LIAM e do Brock também são conferidos);
6. vencido o Brock, o assistente do Oak entrega o tênis de corrida na saída leste de Pewter
   (data/maps/PewterCity/scripts.inc, FLAG_SYS_B_DASH) e o cronômetro mede a corrida por
   input: RUN_FRAMES_PER_TILE (5) quadros/tile (Ruling 10: medida só depois do tênis ganho
   jogando).

Teto da Potion (cura min(20, max_hp - hp)): no treino, na 1ª vez em que faltar menos de 20 de
HP ao inicial e houver Potion na bolsa, usa uma pelo menu START e confere que o HP para no
máximo (o modo rápido só exercita a cura de 20 inteiros).
"""

import math
import time

from ..emu import KEY_A, KEY_LEFT, KEY_UP
from ..result import Result
from . import ScenarioContext
from .base import Abort
from .pace import RUN_FRAMES_PER_TILE, measure_run_frames_per_tile
from .quick_catch_save import (BUY_MENU_TASK, MART_CLERK_FRONT, POTION_HEAL, SHOP_MENU_TASK,
                               SHOP_TIMEOUT, CatchSaveScenario)
from .travel import ROUTE2_NORTH, Relocated, TravelMixin

VIRIDIAN_CENTER = "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F"
PEWTER_CENTER = "MAP_PEWTER_CITY_POKEMON_CENTER_1F"

# Níveis do inicial (Medium Slow) antes da Floresta e antes do Brock (Geodude 12, Onix 14).
# Charmander precisa de Metal Claw (nv13) e de folga contra o Rock Tomb (2x no fogo).
FOREST_LEVEL = 11
BROCK_LEVEL = {"BULBASAUR": 13, "CHARMANDER": 18, "SQUIRTLE": 13}
RETRAIN_LEVELS = 3
BROCK_ATTEMPTS = 3
BROCK_HEAL_BELOW = 0.4
# Limite de batalhas de um treino, proporcional à EXP pedida: os 3 iniciais são Medium Slow
# (src/data/pokemon/species_info.h, GROWTH_MEDIUM_SLOW) e o selvagem da Rota 2 (nv2..5) dá a
# mesma EXP qualquer que seja o nível do inicial — medido ~25 por batalha (Charmander nv11->18:
# 3056 EXP em 121 batalhas; Bulbasaur nv5->11: 607 em 24). Conta 20 por batalha e 1,5x de folga.
TRAIN_EXP_PER_BATTLE = 20
TRAIN_SAFETY = 1.5
MIN_TRAIN_BATTLES = 30
TRAIN_HEAL_BELOW = 0.5              # volta ao Centro abaixo disto (inicial)
MAX_POTIONS = 5                     # o dinheiro todo pode virar Potion antes do Brock

# grama alta (data/layouts): Rota 2 sul x 6..12, y 56..60; Rota 2 norte x 2..8, y 2..8
SOUTH_GRASS = ((9, 56), (9, 60))
NORTH_GRASS = ((5, 3), (5, 8))
BROCK_FRONT = (6, 6)                # Brock em (6, 5), olhando para baixo
AIDE_APPROACH = (45, 22)            # gatilho do assistente em (46, 21..23)
RUN_START = (40, 21)                # linha 21 de Pewter livre de x=6 a x=41


def medium_slow_exp(level: int) -> int:
    """EXP total do nível (gExperienceTables, GROWTH_MEDIUM_SLOW: 6/5 n³ - 15 n² + 100 n - 140;
    o nível 1 não importa aqui)."""
    if level <= 1:
        return 0
    return 6 * level ** 3 // 5 - 15 * level ** 2 + 100 * level - 140


def train_battle_cap(from_level: int, to_level: int) -> int:
    """Teto de batalhas para subir de `from_level` a `to_level` (EXP do início do nível atual,
    então nunca subestima)."""
    need = max(0, medium_slow_exp(to_level) - medium_slow_exp(from_level))
    return max(MIN_TRAIN_BATTLES, math.ceil(need / TRAIN_EXP_PER_BATTLE * TRAIN_SAFETY))


class ForestBrockScenario(TravelMixin, CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.starter_name = ctx.starter
        self.potion = self.consts.item("ITEM_POTION")
        self.measures.update(trainers=[], wild_fights=0, whiteouts=0, train_log=[])

    # --- treino --------------------------------------------------------------------
    def _starter(self):
        return self.game.party()[0]

    def _needs_heal(self) -> bool:
        party = self.game.party()
        return (party[0].hp < party[0].max_hp * TRAIN_HEAL_BELOW
                or any(m.hp == 0 for m in party))

    def _try_potion_cap(self) -> None:
        """Faltando menos de POTION_HEAL de HP e com Potion na bolsa: usa e confere o teto."""
        if "potion_cap" in self.measures or self.game.bag_quantity(self.potion) == 0:
            return
        mon = self._starter()
        missing = mon.max_hp - mon.hp
        if not 0 < missing < POTION_HEAL or mon.hp == 0:
            return
        count = self.game.bag_quantity(self.potion)
        after = self.menu.use_item_on_mon(self.potion, 0)
        left = self.game.bag_quantity(self.potion)
        self.measures["potion_cap"] = (mon.hp, mon.max_hp, after, count, left)

    def _check_potion_cap(self) -> Result | None:
        if "potion_cap" not in self.measures:
            return None
        hp, max_hp, after, count, left = self.measures["potion_cap"]
        name = f"potion: faltando menos de {POTION_HEAL}, a cura para no HP máximo"
        detail = (f"HP {hp}/{max_hp} (faltavam {max_hp - hp}) -> {after}; "
                  f"Potions {count} -> {left}")
        ok = after == max_hp and left == count - 1
        return Result(name, "ok" if ok else "falha", detail if ok else f"esperava {max_hp}: {detail}")

    def _train(self, area: str, grass, center: str, level: int) -> str:
        start_level, start_fights = self._starter().level, self.measures["wild_fights"]
        cap = train_battle_cap(start_level, level)
        start = time.monotonic()
        self.fight_wild = True
        try:
            while self._starter().level < level:
                if self.measures["wild_fights"] - start_fights >= cap:
                    raise AssertionError(f"nv{self._starter().level} depois de {cap} batalhas "
                                         f"(limite), esperava nv{level}")
                if self._needs_heal():
                    self._heal_at_nearest_center(center)
                self._go(area)
                if self.game.player_xy() not in grass:
                    self._walk(*grass[1])
                self._find_wild_battle(grass)
                self._battle_on_the_way()
                self._try_potion_cap()
        finally:
            self.fight_wild = False
        fights = self.measures["wild_fights"] - start_fights
        detail = (f"nv{start_level} -> nv{self._starter().level} em {fights} batalha(s) "
                  f"(limite {cap}, {time.monotonic() - start:.0f} s)")
        self.measures["train_log"].append(detail)
        return detail

    # --- Floresta ------------------------------------------------------------------
    def _old_man(self) -> str:
        self._go("MAP_ROUTE2")
        teachy = self.game.bag_quantity(self.consts.item("ITEM_TEACHY_TV"))
        assert teachy == 1, f"TEACHY TV na bolsa = {teachy}, esperava 1 (tutorial do velho)"
        return f"tutorial do velho feito, TEACHY TV x{teachy}; Rota 2 em {self.game.player_xy()}"

    def _cross_forest(self) -> str:
        if self._needs_heal():
            self._heal_at_nearest_center(VIRIDIAN_CENTER)
        before = len(self.measures["trainers"])
        self._go(ROUTE2_NORTH)
        fought = self.measures["trainers"][before:]
        names = [f"{t['name']} ({t['outcome']})" for t in fought]
        return (f"Rota 2 norte em {self.game.player_xy()}; treinadores: {names or 'nenhum'}; "
                f"desmaios do time até aqui: {self.measures['whiteouts']}")

    def _check_trainer_money(self, trainers: list[dict], what: str) -> str:
        won = [t for t in trainers if t["outcome"] in ("win", "fainted")]
        assert won, f"nenhum treinador vencido {what} ({len(trainers)} batalha(s))"
        wrong = [t for t in won if t["money_after"] - t["money_before"] != t["expected"]]
        lines = [f"{t['name']}: {t['money_before']} -> {t['money_after']} "
                 f"(+{t['money_after'] - t['money_before']}, esperado {t['expected']} = 4 x "
                 f"nv{t['last_level']} x {t['class_value']} x {t['multiplier']}"
                 f"{' x 2' if t['double'] else ''})" for t in won]
        assert not wrong, "dinheiro diferente do prêmio: " + "; ".join(lines)
        return "; ".join(lines)

    # --- Pewter e Brock ------------------------------------------------------------
    def _buy_potions(self) -> str:
        price = self.game.item_price(self.potion)
        have = self.game.bag_quantity(self.potion)
        qty = min(MAX_POTIONS - have, self.game.money() // price)
        if qty <= 0:
            return f"sem compra: {have} Potion(s), dinheiro {self.game.money()}"
        self._go("MAP_PEWTER_CITY_MART")
        money0 = self.game.money()
        self._walk(*MART_CLERK_FRONT)
        self.emu.hold(KEY_LEFT, 4)           # balconista em (2, 3), balcão em (3, 3)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do balconista")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: SHOP_MENU_TASK in self._tasks(), SHOP_TIMEOUT,
                            "menu COMPRAR/VENDER/SAIR")
        self.ctl.press_until(KEY_A, lambda: BUY_MENU_TASK in self._tasks(), "lista de compras",
                             tries=5, wait=120)
        self._buy(self.potion, qty)
        self._leave_shop()
        now = self.game.bag_quantity(self.potion)
        assert now == have + qty, f"Potions {have} -> {now}, esperava +{qty}"
        assert self.game.money() == money0 - qty * price, (
            f"dinheiro {money0} -> {self.game.money()}, esperava -{qty * price}")
        return f"Potions {have} -> {now}, dinheiro {money0} -> {self.game.money()}"

    def _reach_brock(self) -> bool:
        """Anda até a frente do Brock; True se um treinador do ginásio (LIAM) lutou no
        caminho."""
        before = len(self.measures["trainers"])
        self._go("MAP_PEWTER_CITY_GYM")
        self._walk(*BROCK_FRONT)
        return len(self.measures["trainers"]) > before

    def _challenge_brock(self, log: list[str]) -> str:
        if self._reach_brock():          # luta no caminho: Potions com o prêmio, cura e volta
            if self.game.money() >= self.game.item_price(self.potion):
                log.append(self._buy_potions())
            self._heal_at_nearest_center(PEWTER_CENTER)
            self._reach_brock()
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do Brock")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "início da conversa com o Brock")
        self.driver.heal = (self.potion, BROCK_HEAL_BELOW)
        self.driver.healed = []
        try:
            self._resolve_interruption()
        finally:
            self.driver.heal = None
        brock = [t for t in self.measures["trainers"] if t["name"] == "BROCK"]
        return brock[-1]["outcome"] if brock else "sem batalha"

    def _brock(self) -> str:
        badge = self.consts.flag("FLAG_BADGE01_GET")
        log: list[str] = []
        for attempt in range(1, BROCK_ATTEMPTS + 1):
            if attempt > 1:
                target = self._starter().level + RETRAIN_LEVELS
                log.append("treino: " + self._train(ROUTE2_NORTH, NORTH_GRASS, PEWTER_CENTER,
                                                    target))
            if self.game.money() >= self.game.item_price(self.potion):
                log.append(self._buy_potions())
            self._heal_at_nearest_center(PEWTER_CENTER)
            level = self._starter().level
            try:
                outcome = self._challenge_brock(log)
            except Relocated:            # o time desmaiou no caminho (LIAM): volta ao Centro
                outcome = "derrota antes do Brock"
            log.append(f"tentativa {attempt} com nv{level}: {outcome}, "
                       f"Potions usadas {len(self.driver.healed)}")
            if self.game.flag(badge):
                self.measures["brock_attempts"] = attempt
                return "FLAG_BADGE01_GET ligada; " + "; ".join(log)
        raise AssertionError(f"sem a insígnia em {BROCK_ATTEMPTS} tentativas: " + "; ".join(log))

    # --- tênis de corrida ----------------------------------------------------------
    def _running_shoes(self) -> str:
        dash = self.consts.flag("FLAG_SYS_B_DASH")
        assert not self.game.flag(dash), "FLAG_SYS_B_DASH já ligada antes do assistente"
        self._go("MAP_PEWTER_CITY")
        self._walk(*AIDE_APPROACH)
        self.nav.step("right", 1)
        self.ctl.wait_until(self.ctl.script_active, 120, "assistente do Oak")
        self._resolve_interruption()
        assert self.game.flag(dash), "FLAG_SYS_B_DASH desligada depois do assistente do Oak"
        return f"tênis de corrida recebido em {self.game.player_xy()} (FLAG_SYS_B_DASH)"

    def _run_pace(self) -> str:
        self._walk(*RUN_START)
        steps = measure_run_frames_per_tile(self.ctx, "left")
        assert steps and all(d == RUN_FRAMES_PER_TILE for d in steps), (
            f"correndo: {steps} quadros/tile, esperava {RUN_FRAMES_PER_TILE}")
        return f"{len(steps)} passos correndo (B segurado): {steps} quadros/tile"

    # --- roteiro -------------------------------------------------------------------
    def run(self) -> None:
        suite = self.suite
        level = BROCK_LEVEL[self.starter_name]
        try:
            self._flow("floresta: Centro de Viridian cura o time",
                       lambda: self._heal_at_nearest_center(VIRIDIAN_CENTER))
            self._flow("floresta: tutorial do velho de Viridian libera a Rota 2", self._old_man)
            self._flow(f"floresta: treino na Rota 2 até nv{FOREST_LEVEL}",
                       lambda: self._train("MAP_ROUTE2", SOUTH_GRASS, VIRIDIAN_CENTER,
                                           FOREST_LEVEL))
            self._flow("floresta: atravessa a Floresta de Viridian", self._cross_forest)
            suite.run("floresta: vence treinador e o dinheiro sobe exatamente o prêmio "
                      "(gTrainerMoneyTable x nível do último Pokémon)",
                      lambda: self._check_trainer_money(list(self.measures["trainers"]),
                                                        "na Floresta"))
            forest_trainers = len(self.measures["trainers"])
            self._flow("brock: Centro de Pewter (ponto de retorno)",
                       lambda: self._heal_at_nearest_center(PEWTER_CENTER))
            self._flow(f"brock: treino na Rota 2 norte até nv{level}",
                       lambda: self._train(ROUTE2_NORTH, NORTH_GRASS, PEWTER_CENTER, level))
            self._flow(f"brock: vence o Brock (até {BROCK_ATTEMPTS} tentativas)", self._brock)
            suite.run("brock: prêmio do ginásio é exatamente o de gTrainerMoneyTable",
                      lambda: self._check_trainer_money(
                          self.measures["trainers"][forest_trainers:], "no ginásio"))
            cap = self._check_potion_cap()
            if cap is not None:
                suite.add(cap)
            self._flow("corrida: assistente do Oak entrega o tênis de corrida",
                       self._running_shoes)
            suite.run(f"corrida: correr por input a {RUN_FRAMES_PER_TILE} quadros/tile",
                      self._run_pace)
            self.ctl.checkpoint("brock")
        except Abort:
            pass


def run_full_forest_brock(ctx: ScenarioContext) -> None:
    """Roda a partir do checkpoint `telas` já carregado no emulador."""
    ForestBrockScenario(ctx).run()
