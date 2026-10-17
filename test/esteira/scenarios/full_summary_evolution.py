"""Modo completo: página EVOLUTION do resumo do Pokémon (Hack 4), na build de teste.

A 4ª página do resumo (depois de INFO / SKILLS / KNOWN MOVES) lista como a espécie evolui,
uma linha por entrada de gEvolutionTable (esteira/evolution_page.py tem os formatos).

Ponto de partida: o .sav do fim do modo rápido, como o `evolucoes` (sessão própria da ROM de
teste, `save_from="captura"`). Os atalhos da build de teste (esteira/hooks.py) só montam o time
(Eevee, Onix, Slowpoke, Bulbasaur e Tauros nos slots 0-4 e um ovo no 5), dão uma Rare Candy e
leem o estado do resumo (página, modo, ovo) e o texto da página; o resto é pelo menu de verdade:

1. o texto que GetEvolutionPageText monta para TODAS as espécies (1..CHIMECHO, sem as
   OLD_UNOWN) é igual, byte a byte, ao gerado em Python a partir dos fontes;
2. START > POKéMON > Eevee > SUMMARY; → → → chega na página EVOLUTION (curPageIndex), com o
   texto do Eevee; ← volta para KNOWN MOVES e → de novo vai para EVOLUTION;
3. na página EVOLUTION, ↓ troca de Pokémon (Onix, Slowpoke, Bulbasaur, Tauros): a página
   continua e o texto é o da espécie nova; ↓ no Tauros não vai para o ovo (slot 5);
4. o resumo do ovo não sai da página INFO com →;
5. Tauros 18 + Rare Candy pela bolsa quer aprender PURSUIT: SIM para esquecer um golpe abre o
   resumo no modo de escolher golpe (PSS_MODE_SELECT_MOVE), onde → não leva à página EVOLUTION;
   B cancela e SIM desiste de aprender.

Telas da página: OUT/telas/resumo_evo_<espécie>.png (referência em test/referencias/COMUM/,
diferença é só aviso). No modo assistir (janela), cada página fica parada READ_PAUSE quadros.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only resumo_evolucao
Numa janela, em tempo real: `make test-watch CENARIO=resumo_evolucao`.
"""

import sys

from ..bag import Bag
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_LEFT, KEY_RIGHT
from ..evolution_page import SCREEN_POINTS, SHOWCASE, EvolutionPage
from ..field_menu import STARTMENU_BAG, STARTMENU_POKEMON
from ..hooks import (CMD_GIVE_ITEM, PSS_MODE_SELECT_MOVE, PSS_PAGE_EVOLUTION, PSS_PAGE_INFO,
                     PSS_PAGE_MOVES, PSS_PAGE_MOVES_INFO, Mailbox)
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

SUMMARY_CB = "CB2_RunPokemonSummaryScreen"
SUMMARY_TASK = "Task_InputHandler_Info"
SELECT_MOVE_TASK = "Task_InputHandler_SelectOrForgetMove"
FLIP_TASK = "Task_PokeSum_FlipPages"
SWITCH_TASK = "Task_PokeSum_SwitchDisplayedPokemon"
PARTY_CHOOSE_TASK = "Task_HandleChooseMonInput"
PARTY_ACTIONS_TASK = "Task_HandleSelectionMenuInput"     # RESUMO é a 1ª opção
PARTY_REPLACE_MOVE_YESNO = "Task_HandleReplaceMoveYesNoInput"     # esquecer um golpe? -> SIM
PARTY_STOP_LEARNING_YESNO = "Task_HandleStopLearningMoveYesNoInput"  # desistir? -> SIM
PALETTE_FADE_ACTIVE = 7         # gPaletteFade: bit 7 do byte 7 (`active`, include/palette.h)

EGG_SLOT, EGG_SPECIES = 5, "SPECIES_TOGEPI"
LEARNER = "SPECIES_TAUROS"      # nível 18 com 4 golpes; no 19 aprende PURSUIT
LEARNER_LEVEL = 18
SHOWCASE_LEVEL = 30
SCREEN_TIMEOUT = 1200
FLIP_WAIT = 40                  # quadros para a página mudar depois do botão
SETTLE = 10
READ_PAUSE = 150                # modo assistir: ~2,5 s parado em cada página EVOLUTION
CANDY_TIMEOUT = 3000
PAGE_NAMES = {PSS_PAGE_INFO: "INFO", 1: "SKILLS", PSS_PAGE_MOVES: "KNOWN MOVES",
              PSS_PAGE_MOVES_INFO: "detalhe do golpe", PSS_PAGE_EVOLUTION: "EVOLUTION"}


class SummaryEvolutionScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.bag = Bag(self.ctl)
        self.page = EvolutionPage(REPO_ROOT, self.consts)

    # --- utilidades ----------------------------------------------------------------
    def _sp(self, name: str) -> int:
        return self.consts.species(name)

    def _fade_active(self) -> bool:
        addr = self.game.syms.addr("gPaletteFade") + PALETTE_FADE_ACTIVE
        return bool(self.emu.read_u8(addr) & 0x80)

    def _state(self) -> tuple[int, int, bool] | None:
        return self.box.summary_state()

    def _summary_ready(self, task: str = SUMMARY_TASK) -> bool:
        tasks = self._tasks()
        return (self.game.callback2() == SUMMARY_CB and task in tasks
                and FLIP_TASK not in tasks and SWITCH_TASK not in tasks and not self._fade_active())

    def _wait_summary(self, what: str, task: str = SUMMARY_TASK) -> None:
        self.ctl.wait_until(lambda: self._summary_ready(task), SCREEN_TIMEOUT, what)

    def _page_name(self, page: int) -> str:
        return PAGE_NAMES.get(page, f"página {page}")

    def _flip(self, key: int, want: int, what: str) -> None:
        """Aperta → ou ← (de novo só se o resumo ignorou o toque) e espera a página `want`
        terminar de virar. curPageIndex muda logo no toque, antes da animação."""
        self.ctl.press_until(key, lambda: (self._state() or (None,))[0] == want, what,
                             tries=3, wait=FLIP_WAIT)
        self._wait_summary(what)

    def _viewed_slot(self) -> int:
        return self.emu.read_u8(self.game.syms.addr("sLastViewedMonIndex"))

    def _expected(self, species: str) -> bytes:
        return self.page.encode(self.page.text(species))

    def _read(self, text: bytes) -> str:
        return self.page.decode(text)

    def _pause_to_read(self) -> None:
        if self.emu.window:
            self.emu.frames(READ_PAUSE)

    def _party_cursor(self, slot: int) -> None:
        """No menu de Pokémon (escolha), leva o cursor ao slot e abre as opções dele."""
        self.ctl.wait_until(lambda: PARTY_CHOOSE_TASK in self._tasks(), SCREEN_TIMEOUT,
                            "menu de Pokémon")
        addr = self.game.syms.addr("gPartyMenu") + 0x09        # gPartyMenu.slotId (esteira/bag.py)
        for _ in range(8):
            cur = self.emu.read_u8(addr)
            if cur == slot:
                break
            self.ctl.press_until(KEY_LEFT if slot == 0 else KEY_DOWN,
                                 lambda: self.emu.read_u8(addr) != cur,
                                 f"cursor do menu de Pokémon no slot {slot}")
        assert self.emu.read_u8(addr) == slot, f"cursor do menu de Pokémon fora do slot {slot}"
        self.ctl.press_until(KEY_A, lambda: PARTY_ACTIONS_TASK in self._tasks(),
                             f"opções do Pokémon do slot {slot}", tries=3, wait=60)

    def _open_summary(self, slot: int) -> None:
        self._party_cursor(slot)
        self.ctl.press_until(KEY_A, lambda: self.game.callback2() == SUMMARY_CB,
                             f"RESUMO do slot {slot}", tries=3, wait=120)
        self._wait_summary(f"resumo do slot {slot} pronto")

    def _close_summary(self, what: str) -> None:
        self.ctl.press_until(KEY_B, lambda: PARTY_CHOOSE_TASK in self._tasks()
                             and not self._fade_active(), f"volta ao menu de Pokémon ({what})",
                             tries=4, wait=120)

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="resumo_evolucao_continue")
        party = self.game.party()
        assert party, "save sem Pokémon no time"
        for slot, species in enumerate(SHOWCASE):
            self.box.set_party_mon(slot, self._sp(species), SHOWCASE_LEVEL)
        count = self.box.set_party_egg(EGG_SLOT, self._sp(EGG_SPECIES))
        got = [m.species for m in self.game.party()]
        want = [self._sp(s) for s in SHOWCASE]
        assert got[:len(SHOWCASE)] == want and count == 6, f"time montado errado: {got}"
        return (f"CONTINUAR no Centro de Viridian; time de teste: "
                f"{', '.join(s.removeprefix('SPECIES_') for s in SHOWCASE)} (nv {SHOWCASE_LEVEL}) "
                f"e um ovo de {EGG_SPECIES.removeprefix('SPECIES_')} no slot {EGG_SLOT}")

    def _all_species_text(self) -> str:
        species = self.page.valid_species()
        wrong = []
        for name in species:
            got = self.box.evolution_text(self._sp(name))
            want = self._expected(name)
            if got != want:
                wrong.append(f"{name}: jogo '{self._read(got)}', esperado '{self._read(want)}'")
        assert not wrong, f"{len(wrong)} espécie(s) com texto diferente: " + "; ".join(wrong[:8])
        return (f"{len(species)} espécies (1..CHIMECHO, sem as OLD_UNOWN): GetEvolutionPageText "
                "igual ao texto gerado dos fontes; Eevee: "
                f"'{self._read(self.box.evolution_text(self._sp('SPECIES_EEVEE')))}'")

    def _check_page(self, species: str, shot: str) -> str:
        """Na página EVOLUTION: estado, texto impresso (o da espécie) e tela."""
        state = self._state()
        assert state is not None, "nenhum resumo aberto"
        page, _mode, egg = state
        assert page == PSS_PAGE_EVOLUTION and not egg, \
            f"página ativa {self._page_name(page)} (ovo: {egg}), esperava EVOLUTION"
        mon = self.game.party()[SHOWCASE.index(species)]
        assert mon.species == self._sp(species), f"slot de {species} tem a espécie {mon.species}"
        got, want = self.box.evolution_text(from_open_summary=True), self._expected(species)
        assert got == want, f"texto da página: '{self._read(got)}', esperado '{self._read(want)}'"
        self.emu.frames(SETTLE)
        path = self._shot(shot)
        self._pause_to_read()
        return f"{species.removeprefix('SPECIES_')}: '{self._read(got)}' (tela em {path})"

    def _first_mon(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self._open_summary(0)
        assert self._state()[0] == PSS_PAGE_INFO, "o resumo não abriu na página INFO"
        self._flip(KEY_RIGHT, 1, "página SKILLS")
        self._flip(KEY_RIGHT, PSS_PAGE_MOVES, "página KNOWN MOVES")
        self._flip(KEY_RIGHT, PSS_PAGE_EVOLUTION, "página EVOLUTION")
        return "INFO -> SKILLS -> KNOWN MOVES -> EVOLUTION com →; " + \
            self._check_page(SHOWCASE[0], SCREEN_POINTS[0])

    def _back_and_forth(self) -> str:
        self._flip(KEY_LEFT, PSS_PAGE_MOVES, "← de volta para KNOWN MOVES")
        self._flip(KEY_RIGHT, PSS_PAGE_EVOLUTION, "→ de novo para EVOLUTION")
        got, want = self.box.evolution_text(from_open_summary=True), self._expected(SHOWCASE[0])
        assert got == want, f"texto depois de voltar: '{self._read(got)}'"
        return "← volta para KNOWN MOVES e → leva de novo para EVOLUTION (texto do Eevee)"

    def _next_mon(self, index: int) -> str:
        """↓ na página EVOLUTION: o Pokémon seguinte, sem sair da página."""
        self.ctl.press_until(KEY_DOWN, lambda: self._viewed_slot() == index,
                             f"troca para o slot {index}", tries=3, wait=FLIP_WAIT)
        self._wait_summary("troca de Pokémon terminada")
        return self._check_page(SHOWCASE[index], SCREEN_POINTS[index])

    def _egg_is_skipped(self) -> str:
        self._press(KEY_DOWN)
        self.emu.frames(FLIP_WAIT)
        self._wait_summary("resumo depois do ↓ no último Pokémon")
        assert self._viewed_slot() == len(SHOWCASE) - 1, \
            f"↓ no último Pokémon foi para o slot {self._viewed_slot()}"
        got, want = self.box.evolution_text(from_open_summary=True), self._expected(SHOWCASE[-1])
        assert self._state()[0] == PSS_PAGE_EVOLUTION and got == want, \
            f"depois do ↓: página {self._page_name(self._state()[0])}, texto '{self._read(got)}'"
        self._close_summary("fim da troca de Pokémon")
        return "↓ no Tauros não leva ao ovo do slot 5 (continua Tauros na página EVOLUTION)"

    def _egg_has_no_pages(self) -> str:
        self._open_summary(EGG_SLOT)
        state = self._state()
        assert state is not None and state[0] == PSS_PAGE_INFO and state[2], \
            f"resumo do ovo: {state}"
        for _ in range(3):
            self._press(KEY_RIGHT)
            self.emu.frames(FLIP_WAIT)
            page, _mode, egg = self._state()
            assert page == PSS_PAGE_INFO and egg, f"→ no ovo levou à página {self._page_name(page)}"
        self._close_summary("ovo")
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             "volta ao menu START", tries=6, wait=120)
        self.menu.close_start_menu()
        return "ovo: → três vezes e o resumo continua na página INFO"

    def _select_move_mode(self) -> str:
        """Tauros 18 + Rare Candy: SIM para esquecer um golpe abre o resumo no modo de escolher
        golpe; → não leva à página EVOLUTION; B cancela e SIM desiste de aprender."""
        slot = SHOWCASE.index(LEARNER)
        candy = self.consts.item("ITEM_RARE_CANDY")
        self.box.set_party_mon(slot, self._sp(LEARNER), LEARNER_LEVEL)
        moves_before = [m for m in self.game.party()[slot].moves if m]
        assert len(moves_before) == 4, f"{LEARNER} nv {LEARNER_LEVEL} com golpes {moves_before}"
        assert self.box.call(CMD_GIVE_ITEM, candy, 1) == 1, "AddBagItem(Rare Candy) falhou"
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_BAG)
        self.bag.wait_ready()
        self.bag.select(candy)
        self.bag.use_selected()
        self.bag.choose_party_slot(slot)
        seen: dict = {}
        spent = 0
        while not self.bag.ready():
            if spent >= CANDY_TIMEOUT:
                raise self.ctl.timeout_error("bolsa de volta depois da Rare Candy")
            before = self.emu.frames(0)
            tasks = self._tasks()
            if self.game.callback2() == SUMMARY_CB:
                if "summary" not in seen:
                    self._wait_summary("resumo de escolher golpe", SELECT_MOVE_TASK)
                    self.emu.frames(FLIP_WAIT)     # fim do fade e do grito: aceita botões
                    seen["summary"] = self._state()
                    for _ in range(3):
                        self._press(KEY_RIGHT)
                        self.emu.frames(FLIP_WAIT // 2)
                    seen["after_right"] = self._state()
                    seen["shot"] = self._shot("resumo_evo_escolher_golpe")
                    self._pause_to_read()
                if self._summary_ready(SELECT_MOVE_TASK):
                    self._press(KEY_B)         # cancela: não esquece nenhum golpe
                else:
                    self.emu.frames(2)          # saindo do resumo (fade)
            elif PARTY_REPLACE_MOVE_YESNO in tasks:
                self._press(KEY_A)             # SIM: escolher o golpe a esquecer (abre o resumo)
            elif PARTY_STOP_LEARNING_YESNO in tasks:
                self._press(KEY_A)             # SIM: desiste de aprender
            else:
                self._press(KEY_A)
            spent += max(self.emu.frames(0) - before, 1)
        assert "summary" in seen, "o resumo de escolher golpe não abriu"
        page, mode, _egg = seen["summary"]
        assert (page, mode) == (PSS_PAGE_MOVES_INFO, PSS_MODE_SELECT_MOVE), \
            f"resumo de escolher golpe na página {self._page_name(page)}, modo {mode}"
        assert seen["after_right"] == seen["summary"], \
            f"→ mudou o resumo de escolher golpe: {seen['summary']} -> {seen['after_right']}"
        mon = self.game.party()[slot]
        assert mon.level == LEARNER_LEVEL + 1, f"nível {mon.level}"
        assert [m for m in mon.moves if m] == moves_before, f"golpes mudaram: {mon.moves}"
        self.ctl.press_until(KEY_B, lambda: not self.bag.ready(), "bolsa fechada")
        self.ctl.wait_until(self.menu.start_menu_open, 600, "menu START depois da bolsa")
        self.menu.close_start_menu()
        return (f"{LEARNER.removeprefix('SPECIES_')} {LEARNER_LEVEL} + Rare Candy -> resumo de "
                "escolher golpe (detalhe do golpe, PSS_MODE_SELECT_MOVE); → três vezes não mudou "
                f"a página; B cancelou e o golpe novo foi recusado (tela em {seen['shot']})")

    # --- roteiro -------------------------------------------------------------------
    def run(self) -> None:
        try:
            self._flow("resumo_evolucao: CONTINUAR com o save do modo rápido e time de teste",
                       self._start)
            self.suite.run("resumo_evolucao: texto da página para todas as espécies",
                           self._all_species_text)
            self._flow("resumo_evolucao: START > POKéMON > SUMMARY e → até a página EVOLUTION",
                       self._first_mon)
            self._flow("resumo_evolucao: ← volta para KNOWN MOVES", self._back_and_forth)
            for index in range(1, len(SHOWCASE)):
                name = SHOWCASE[index].removeprefix("SPECIES_").capitalize()
                self._flow(f"resumo_evolucao: ↓ troca para {name} na página EVOLUTION",
                           lambda i=index: self._next_mon(i))
            self._flow("resumo_evolucao: ↓ não leva ao ovo", self._egg_is_skipped)
            self._flow("resumo_evolucao: ovo não mostra a página", self._egg_has_no_pages)
            self._flow("resumo_evolucao: modo de aprender golpe não mostra a página",
                       self._select_move_mode)
        except Abort:
            pass


def run_full_summary_evolution(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    SummaryEvolutionScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only resumo_evolucao ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "resumo_evolucao",
                     *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
