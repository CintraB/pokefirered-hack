"""Modo completo: Shiny Charm e taxa de shiny, na build de teste (TESTBUILD=1).

Roda na ROM de teste (`pokefirered_switch_test.gba`), que tem a caixa de comandos
`gTestMailbox` (esteira/hooks.py); aqui a escrita na RAM é permitida (modo completo).

Ponto de partida: o save do jogo (.sav) feito no fim do modo rápido (passo 11, no Centro de
Viridian). Os savestates do modo rápido não servem: são da ROM jogável e o código da build
de teste fica em outros endereços (a chamada de TestHooks_Run desloca tudo depois de main.o).
O CLI (esteira/__main__.py) registra o cenário com `rom=TEST, save_from="captura"`: guarda o
.sav da sessão jogável como OUT/captura.sav e abre a ROM de teste com uma cópia dele; o
roteiro liga, CONTINUAR e:

1. 1 000 pares (personalidade, OT ID) fixos: cor (IsMonShiny do jogo e Mon.is_shiny lido do
   Pokémon criado) == fórmula original com limite 8;
2. taxa sem charm: 200 000 Pokémon por CreateMonWithNature (o caminho dos selvagens);
3. atalho marca a Dex Nacional completa (tudo que HasAllMons() exige, mais o Mew: o Amuleto
   Brilhante exige os 151 de Kanto, HasAllKantoMonsWithMew);
4. avaliação pelo PC do Oak (Centro de Viridian) com a Dex completa: não entrega o charm;
5. anda até o laboratório e fala com o Oak: entrega o charm (1 na bolsa, FLAG_GOT_SHINY_CHARM);
6. sai, volta e fala de novo: continua 1;
7. os mesmos 1 000 pares mantêm a cor depois do charm; taxa com charm (200 000 Pokémon).

Modo paralelo (ESTEIRA_JOBS > 1, esteira/paralelo.py): o cenário roda em SHINY_PARTS sessões
ao mesmo tempo. A parte 0 faz o roteiro inteiro acima; as outras só CONTINUAR e as duas taxas.
Cada parte conta a sua fatia dos 200 000 (com o RNG semeado por parte) e `merge_shiny` soma as
fatias e aplica a MESMA faixa de ±3σ dos 200 000 ao total.

Uso, a partir de test/ (a mesma pasta OUT precisa ter o .sav do modo rápido):
    python3 -m esteira rapido   --rom R --elf E --out OUT
    python3 -m esteira completo --rom R --elf E --out OUT --only shiny
`python3 -m esteira.scenarios.full_shiny ARGS` é atalho para `python3 -m esteira completo
--only shiny ARGS`.
"""

import math
import random
import sys

from ..emu import KEY_A, KEY_B, KEY_UP
from ..game import POKEMON_SIZE, decode_mon
from ..hooks import CMD_CHECK_SHINY, CMD_COUNT_SHINIES, CMD_SET_DEX_COMPLETE, Mailbox
from ..paralelo import part_data, part_label, seed_label, seed_rng, share
from ..result import Result, Suite
from . import ScenarioContext
from .base import TEXT_PERIOD, Abort
from .pc_menu import MULTICHOICE_TASK, PC_MENU_OAK, PC_TIMEOUT, PcMenuMixin
from .quick_catch_save import CENTER_EXIT, CatchSaveScenario
from .quick_route1 import (LAB_EXIT, OAK_FRONT, PALLET_LAB_FRONT, ROUTE1_SOUTH_EDGE,
                           VIRIDIAN_SOUTH_EDGE)

# --- expectativas (include/constants/pokemon.h; conferidas em test_shiny_math.py) ----
SHINY_ODDS = 8                  # shiny se hi(ot)^lo(ot)^hi(pid)^lo(pid) < 8: 1/8192 por sorteio
ATTEMPTS_NO_CHARM = 2           # 1 + SHINY_BASE_REROLLS  (~1/4096)
ATTEMPTS_WITH_CHARM = 4         # 1 + SHINY_CHARM_REROLLS (~1/2048)
SHINY_SAMPLES = 200_000
SIGMAS = 3
SHINY_PARTS = 6                 # sessões no modo paralelo (fixo: o resultado não depende do teto)
RATE_NAMES = {False: "shiny: taxa sem charm ≈ 1/4096 (200 000 Pokémon)",
              True: "shiny: taxa com charm ≈ 1/2048 (200 000 Pokémon)"}

# ~1,9 quadro por Pokémon criado (medido); o teto dá 3x de folga
FRAMES_PER_MON_LIMIT = 6
COUNT_POLL = 60

YESNO_TASK = "Task_YesNoMenu_HandleInput"
RATING_TIMEOUT = 4000
OAK_TIMEOUT = 8000


def shiny_value(pid: int, ot: int) -> int:
    return (ot >> 16) ^ (ot & 0xFFFF) ^ (pid >> 16) ^ (pid & 0xFFFF)


def is_shiny_original(pid: int, ot: int) -> bool:
    """Fórmula do jogo original (GET_SHINY_VALUE < SHINY_ODDS, limite 8)."""
    return shiny_value(pid, ot) < SHINY_ODDS


def shiny_probability(attempts: int) -> float:
    """Chance de ao menos um dos `attempts` sorteios de personalidade ser shiny."""
    return 1 - (1 - SHINY_ODDS / 65536) ** attempts


def expected_shinies(n: int, attempts: int) -> float:
    return n * shiny_probability(attempts)


def shiny_interval(n: int, attempts: int, sigmas: float = SIGMAS) -> tuple[float, float]:
    """Média ± `sigmas` desvios-padrão da binomial(n, p)."""
    p = shiny_probability(attempts)
    mean, sigma = n * p, math.sqrt(n * p * (1 - p))
    return mean - sigmas * sigma, mean + sigmas * sigma


def _color_pairs(count: int = 1000, seed: int = 0x5A1E) -> tuple[tuple[int, int], ...]:
    """Pares (pid, ot) fixos: metade sorteada livre (quase nunca shiny) e metade com o valor
    shiny forçado a 0..15, cobrindo os dois lados do limite 8."""
    rng = random.Random(seed)
    pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    while len(pairs) < count:
        pid, ot = rng.getrandbits(32), rng.getrandbits(32)
        if len(pairs) % 2 == 0:
            target = (len(pairs) // 2) % 16
            pid ^= shiny_value(pid, ot) ^ target       # mexe só na metade baixa do pid
        if (pid, ot) not in seen:
            seen.add((pid, ot))
            pairs.append((pid, ot))
    return tuple(pairs)


COLOR_PAIRS = _color_pairs()


def _fmt(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def rate_detail(shinies: int, frames: int, with_charm: bool, bag: int, parts: int = 1) -> str:
    """Detalhe da taxa de SHINY_SAMPLES Pokémon; AssertionError fora da faixa de ±SIGMAS."""
    attempts = ATTEMPTS_WITH_CHARM if with_charm else ATTEMPTS_NO_CHARM
    lo, hi = shiny_interval(SHINY_SAMPLES, attempts)
    mean = expected_shinies(SHINY_SAMPLES, attempts)
    where = f" em {parts} processos" if parts > 1 else ""
    detail = (f"{shinies} shiny em {SHINY_SAMPLES} (esperado {_fmt(mean)} = "
              f"n·(1-(1-1/8192)^{attempts}); faixa ±{SIGMAS}σ {_fmt(lo)}..{_fmt(hi)}); "
              f"{frames} quadros{where}; charm na bolsa = {bag}")
    assert lo <= shinies <= hi, f"fora da faixa: {detail}"
    return detail


def merge_shiny(parts_results: list[list[Result]]) -> list[Result]:
    """Junta as partes (modo paralelo): os resultados da parte 0 na ordem dela, com as duas taxas
    trocadas pela soma das fatias de todas as partes, conferida com a faixa dos 200 000."""
    merged: list[Result] = []
    parts = len(parts_results)
    for result in parts_results[0]:
        if result.data is None or result.name not in RATE_NAMES.values():
            merged.append(result)
            continue
        datas, failure = part_data(parts_results, result.name)
        if failure is not None:
            merged.append(failure)
            continue
        with_charm = result.name == RATE_NAMES[True]
        suite = Suite()
        suite.run(result.name, lambda: rate_detail(
            sum(d["shinies"] for d in datas), sum(d["frames"] for d in datas), with_charm,
            datas[0]["bag"], parts))
        for r in suite.results:   # a semente reproduz a contagem (README: ESTEIRA_SEED)
            r.detail += f"; {seed_label(datas[0].get('seed', 0))}"
        merged.extend(suite.results)
    return merged


class ShinyScenario(PcMenuMixin, CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.charm = self.consts.item("ITEM_SHINY_CHARM")
        self.charm_flag = self.consts.flag("FLAG_GOT_SHINY_CHARM")
        self.colors: dict[str, list[bool]] = {}

    # --- utilidades ----------------------------------------------------------------
    def _charm_state(self) -> str:
        return (f"charm na bolsa = {self.game.bag_quantity(self.charm)}, "
                f"FLAG_GOT_SHINY_CHARM = {int(self.game.flag(self.charm_flag))}")

    def _tasks_has(self, name: str) -> bool:
        return name in self._tasks()

    # --- início --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="shiny_continue")
        consts, game = self.consts, self.game
        self._expect_map("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F")
        assert game.flag(consts.flag("FLAG_SYS_POKEDEX_GET")), "save sem a Pokédex"
        assert game.bag_quantity(self.charm) == 0, "save já tem o Shiny Charm"
        assert not game.flag(self.charm_flag), "save já tem FLAG_GOT_SHINY_CHARM"
        return (f"CONTINUAR no Centro de Viridian {game.player_xy()}; gTestMailbox em "
                f"0x{self.box.addr:08x}; {self._charm_state()}")

    # --- cor de Pokémon existentes -------------------------------------------------
    def _colors(self, when: str) -> str:
        enemy = self.game.syms.addr("gEnemyParty")
        results, wrong = [], []
        for pid, ot in COLOR_PAIRS:
            game_shiny = bool(self.box.call(CMD_CHECK_SHINY, pid, ot))
            mon = decode_mon(self.emu.read(enemy, POKEMON_SIZE), self.game.charmap)
            expected = is_shiny_original(pid, ot)
            if (mon.personality, mon.ot_id) != (pid, ot):
                wrong.append(f"pid/ot lidos {mon.personality:08x}/{mon.ot_id:08x}, "
                             f"esperava {pid:08x}/{ot:08x}")
            elif game_shiny != expected or mon.is_shiny != expected:
                wrong.append(f"pid {pid:08x} ot {ot:08x}: IsMonShiny {game_shiny}, "
                             f"Mon.is_shiny {mon.is_shiny}, original {expected}")
            results.append(game_shiny)
        self.colors[when] = results
        assert not wrong, f"{len(wrong)} par(es) com cor diferente: " + "; ".join(wrong[:5])
        detail = (f"{len(COLOR_PAIRS)} pares: {sum(results)} shiny, todos iguais à fórmula "
                  f"original (limite {SHINY_ODDS}); {self._charm_state()}")
        if when != "antes" and "antes" in self.colors:
            changed = sum(a != b for a, b in zip(self.colors["antes"], results))
            assert changed == 0, f"{changed} par(es) mudaram de cor depois do charm"
            detail += "; nenhum mudou desde antes do charm"
        return detail

    # --- taxa de shiny -------------------------------------------------------------
    def _rate(self, with_charm: bool) -> str:
        part, parts = self.ctx.part, self.ctx.parts
        samples = share(SHINY_SAMPLES, part, parts)
        bag_before = self.game.bag_quantity(self.charm)
        # o atalho põe/tira o charm durante a contagem; a taxa só vale se a bolsa real já
        # estiver no estado pedido (o que o jogador teria de verdade). As partes > 0 do modo
        # paralelo não andam até o Oak: só contam a fatia delas (a parte 0 confere a bolsa).
        if part == 0:
            assert bag_before == int(with_charm), (
                f"charm na bolsa = {bag_before} antes da taxa "
                f"{'com' if with_charm else 'sem'} charm")
        if parts > 1:   # fatias com sequências do RNG disjuntas (paralelo.part_seed)
            seed_rng(self.emu, self.game.syms, "shiny", int(with_charm) * parts + part,
                     self.ctx.seed)
        start = self.emu.frames(0)
        shinies = self.box.call(CMD_COUNT_SHINIES, samples, int(with_charm),
                                timeout=samples * FRAMES_PER_MON_LIMIT, poll=COUNT_POLL)
        frames = self.emu.frames(0) - start
        bag_after = self.game.bag_quantity(self.charm)
        self.measures[f"shinies_{'charm' if with_charm else 'sem_charm'}"] = shinies
        assert bag_after == bag_before, (
            f"o atalho mexeu na bolsa: charm {bag_before} -> {bag_after}")
        if parts > 1:
            self._partial = {"shinies": shinies, "frames": frames, "bag": bag_before,
                             "seed": self.ctx.seed}
            return (f"{part_label(part, parts)}: {shinies} shiny em {samples}; {frames} quadros "
                    "(a faixa é conferida na soma das partes)")
        return rate_detail(shinies, frames, with_charm, bag_before)

    def _run_rate(self, with_charm: bool) -> None:
        self._partial = None
        result = self.suite.run(RATE_NAMES[with_charm], lambda: self._rate(with_charm))
        if result.status != "falha" and self._partial is not None:
            result.data = self._partial

    # --- Dex completa e avaliações -------------------------------------------------
    def _dex_complete(self) -> str:
        has_all = self.box.call(CMD_SET_DEX_COMPLETE)
        national = self.game.flag(self.consts.flag("FLAG_SYS_NATIONAL_DEX"))
        assert has_all == 1, f"HasAllMons() = {has_all} depois do atalho"
        assert national, "FLAG_SYS_NATIONAL_DEX desligada depois do atalho"
        return "HasAllMons() = 1, Dex Nacional ativa"

    def _pc_rating(self) -> str:
        """PC do Centro > PC do PROF. OAK > SIM: avaliação com FLAG_OAKS_RATING_IS_VIA_PC."""
        self._open_pc_menu()
        self._choose_menu_item(PC_MENU_OAK)
        # "Acessou o PC do PROF. OAK" e a pergunta: só o PC do Oak abre um sim/não aqui
        self.ctl.advance_text(lambda: self._tasks_has(YESNO_TASK), PC_TIMEOUT,
                              "pergunta do PC do Oak (avaliar a Pokédex?)")
        self.ctl.press_until(KEY_A, lambda: not self._tasks_has(YESNO_TASK), "SIM no PC do Oak")
        # B avança a avaliação: um A que caísse no quadro em que o menu do PC volta escolheria o
        # PC do BILL; um B ali só fecha o PC (dependia da fase dos quadros, Hack 6)
        spent = 0
        while not (self._tasks_has(MULTICHOICE_TASK) or self.ctl.overworld_idle()):
            if spent >= RATING_TIMEOUT:
                raise self.ctl.timeout_error("fim da avaliação pelo PC (volta ao menu do PC)")
            self._press(KEY_B)
            spent += TEXT_PERIOD
        self.ctl.press_until(KEY_B, lambda: not self._tasks_has(MULTICHOICE_TASK),
                             "PC desligado")
        self.ctl.wait_overworld_idle(PC_TIMEOUT)   # sem falas aqui: A reabriria o PC
        return self._charm_state()

    def _check_pc_gave_nothing(self) -> str:
        saw = self.game.flag(self.consts.flag("FLAG_OAK_SAW_DEX_COMPLETION"))
        qty = self.game.bag_quantity(self.charm)
        assert saw, "FLAG_OAK_SAW_DEX_COMPLETION desligada: o PC não avaliou a Dex completa"
        assert qty == 0, f"o PC entregou o Shiny Charm (x{qty})"
        assert not self.game.flag(self.charm_flag), "o PC ligou FLAG_GOT_SHINY_CHARM"
        return f"Dex completa avaliada (FLAG_OAK_SAW_DEX_COMPLETION); {self._charm_state()}"

    def _go_to_oak(self) -> None:
        self._walk(*CENTER_EXIT)
        self._warp("down", "MAP_VIRIDIAN_CITY")
        self._walk(*VIRIDIAN_SOUTH_EDGE)
        self._cross("down", "MAP_ROUTE1")
        self._walk(*ROUTE1_SOUTH_EDGE)
        self._cross("down", "MAP_PALLET_TOWN")
        self._enter_lab()

    def _enter_lab(self) -> None:
        self._walk(*PALLET_LAB_FRONT)
        self._warp(None, "MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB")
        self._walk(*OAK_FRONT)

    def _talk_to_oak(self) -> None:
        self._talk(KEY_UP, "avaliação do Oak em pessoa", OAK_TIMEOUT)

    def _check_charm_once(self) -> str:
        qty = self.game.bag_quantity(self.charm)
        flag = self.game.flag(self.charm_flag)
        assert qty == 1, f"bag_quantity(ITEM_SHINY_CHARM) = {qty}, esperava 1"
        assert flag, "FLAG_GOT_SHINY_CHARM desligada"
        return self._charm_state()

    def _oak_again(self) -> str:
        """Sai e volta (FLAG_TEMP_2 do 'acabou de ver a Dex' zera) e fala de novo: a
        avaliação roda inteira outra vez e não pode dar outro charm."""
        self._walk(*LAB_EXIT)
        self._warp("down", "MAP_PALLET_TOWN")
        self._enter_lab()
        # SHOWED_OAK_COMPLETE_DEX (FLAG_TEMP_2, data/maps/PalletTown_ProfessorOaksLab/scripts.inc):
        # desligada => o Oak avalia de novo; ligada no fim => a avaliação chegou à Dex completa
        # (a avaliação de Kanto, onde PokedexRating_EventScript_TryGiveShinyCharm roda, vem antes)
        showed = self.consts.flag("FLAG_TEMP_2")
        assert not self.game.flag(showed), "FLAG_TEMP_2 ligada ao voltar: o Oak não avaliaria"
        self._talk_to_oak()
        assert self.game.flag(showed), "a 2ª conversa não passou pela avaliação da Dex completa"
        return "2ª avaliação em pessoa com a Dex completa; " + self._check_charm_once()

    # --- roteiro -------------------------------------------------------------------
    def run(self) -> None:
        suite = self.suite
        try:
            self._flow("shiny: CONTINUAR com o save do modo rápido na build de teste",
                       self._start)
            suite.run("shiny: Pokémon já existentes mantêm a cor original (antes do charm)",
                      lambda: self._colors("antes"))
            self._run_rate(with_charm=False)
            self._flow("shiny: atalho marca a Dex Nacional completa", self._dex_complete)
            self._flow("shiny: avaliação pelo PC do Oak com a Dex completa", self._pc_rating)
            suite.run("shiny: avaliação pelo PC não entrega o Shiny Charm",
                      self._check_pc_gave_nothing)
            self._flow("shiny: caminho até o Oak no laboratório", self._go_to_oak)
            self._flow("shiny: avaliação do Oak em pessoa", self._talk_to_oak)
            self._flow("shiny: Oak em pessoa entrega o Shiny Charm uma vez",
                       self._check_charm_once)
            self.ctl.checkpoint("shiny_charm")
            suite.run("shiny: falar de novo com o Oak não entrega outro charm", self._oak_again)
            suite.run("shiny: Pokémon já existentes mantêm a cor original (depois do charm)",
                      lambda: self._colors("depois"))
            self._run_rate(with_charm=True)
        except Abort:
            pass

    def run_part(self) -> None:
        """Parte > 0 do modo paralelo: só CONTINUAR e a fatia das duas taxas."""
        try:
            self._flow("shiny: CONTINUAR com o save do modo rápido na build de teste",
                       self._start)
            self._run_rate(with_charm=False)
            self._run_rate(with_charm=True)
        except Abort:
            pass


def run_full_shiny(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    scenario = ShinyScenario(ctx_test)
    if ctx_test.part > 0:
        scenario.run_part()
    else:
        scenario.run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only shiny ARGS` (quem orquestra é o CLI)."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "shiny",
                     *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
