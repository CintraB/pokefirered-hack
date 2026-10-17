"""Modo completo: página IVs/EVs do resumo do Pokémon (Hack 5), na build de teste.

A 5ª página do resumo (depois de EVOLUTION) mostra IV (número e nível) e EV de cada atributo, o
total de IVs com % e avaliação geral, o total de EVs e o Hidden Power (esteira/ivev_page.py tem
as contas e o layout; design em docs/superpowers/specs/2026-10-17-pagina-ivs-evs-design.md).

Ponto de partida: o .sav do fim do modo rápido, como o `resumo_evolucao` (sessão própria da ROM
de teste, `save_from="captura"`). Os atalhos da build de teste montam o time (ivev_page.SHOWCASE
nos slots 0-4, com IVs e EVs escolhidos, e um ovo no 5) e leem o estado do resumo e o texto da
página; o resto é pelo menu de verdade:

1. GetIvEvPageText igual, byte a byte, ao texto calculado em Python para os casos de borda
   (tudo 31, tudo 0, limites 25/26 e 15/16, EVs 510, todos os tipos de Hidden Power) e 150
   combinações sorteadas (semente fixa);
2. START > POKéMON > 1º Pokémon > SUMMARY; → quatro vezes até a página IVs/EVs (página ativa na
   memória e texto impresso); ← volta para EVOLUTION e → de novo;
3. ↓ na página troca de Pokémon (os 5 do time) sem sair dela, com o texto de cada um; ↓ no
   último não vai para o ovo;
4. o resumo do ovo não sai da página INFO com →.

Telas: OUT/telas/resumo_ivs_<espécie>.png (referência em test/referencias/COMUM/, diferença é
só aviso). No modo assistir (janela), cada página fica parada READ_PAUSE quadros.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only resumo_ivs
Numa janela, em tempo real: `make test-watch CENARIO=resumo_ivs`.
"""

import random
import sys

from ..emu import KEY_DOWN, KEY_LEFT, KEY_RIGHT
from ..field_menu import STARTMENU_POKEMON
from ..hooks import PSS_PAGE_EVOLUTION, PSS_PAGE_INFO, PSS_PAGE_IVS, PSS_PAGE_MOVES, Mailbox
from ..ivev_page import SCREEN_POINTS, SHOWCASE, IvEvPage, worst_cases
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_summary_evolution import (EGG_SLOT, EGG_SPECIES, FLIP_WAIT, SETTLE,
                                     SummaryEvolutionScenario)

SHOWCASE_LEVEL = 50
RANDOM_CASES, RANDOM_SEED = 150, 20261017


def random_cases(n: int = RANDOM_CASES, seed: int = RANDOM_SEED):
    """IVs quaisquer e EVs válidos (cada um até 255, total até 510)."""
    rnd = random.Random(seed)
    cases = []
    for _ in range(n):
        ivs = tuple(rnd.randint(0, 31) for _ in range(6))
        evs = [0] * 6
        for _ in range(rnd.randint(0, 6)):
            stat = rnd.randrange(6)
            evs[stat] = min(255, evs[stat] + rnd.randint(0, 255), evs[stat] + 510 - sum(evs))
        cases.append((ivs, tuple(evs)))
    return cases


class SummaryIvsScenario(SummaryEvolutionScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.ivpage = IvEvPage(REPO_ROOT)

    def _read_iv(self, text: bytes) -> str:
        return self.ivpage.decode(text)

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="resumo_ivs_continue")
        assert self.game.party(), "save sem Pokémon no time"
        for slot, (species, ivs, evs) in enumerate(SHOWCASE):
            self.box.set_party_mon(slot, self._sp(species), SHOWCASE_LEVEL)
            got = self.box.ivev_text(ivs, evs, slot=slot)
            assert got == self.ivpage.text(ivs, evs), f"slot {slot}: '{self._read_iv(got)}'"
        count = self.box.set_party_egg(EGG_SLOT, self._sp(EGG_SPECIES))
        assert count == 6, f"time com {count}"
        return ("CONTINUAR no Centro de Viridian; time de teste: "
                + ", ".join(f"{s.removeprefix('SPECIES_')} (IV {sum(i)})" for s, i, _ in SHOWCASE)
                + f", ovo no slot {EGG_SLOT}")

    def _all_cases_text(self) -> str:
        cases = worst_cases() + random_cases()
        wrong = []
        for ivs, evs in cases:
            got, want = self.box.ivev_text(ivs, evs), self.ivpage.text(ivs, evs)
            if got != want:
                wrong.append(f"IVs {ivs} EVs {evs}: jogo '{self._read_iv(got)}', "
                             f"esperado '{self._read_iv(want)}'")
        assert not wrong, f"{len(wrong)} caso(s) com texto diferente: " + "; ".join(wrong[:4])
        return (f"{len(cases)} combinações de IVs/EVs (bordas, todos os tipos de Hidden Power e "
                f"{RANDOM_CASES} sorteadas): GetIvEvPageText igual ao cálculo em Python")

    def _check_ivs_page(self, index: int) -> str:
        species, ivs, evs = SHOWCASE[index]
        state = self._state()
        assert state is not None, "nenhum resumo aberto"
        assert state[0] == PSS_PAGE_IVS and not state[2], \
            f"página ativa {self._page_name(state[0])}, esperava IVs/EVs"
        assert self._viewed_slot() == index, f"resumo no slot {self._viewed_slot()}"
        got, want = self.box.evolution_text(from_open_summary=True), self.ivpage.text(ivs, evs)
        assert got == want, f"texto da página: '{self._read_iv(got)}', esperado '{self._read_iv(want)}'"
        self.emu.frames(SETTLE)
        path = self._shot(SCREEN_POINTS[index])
        self._pause_to_read()
        return f"{species.removeprefix('SPECIES_')}: '{self._read_iv(got)}' (tela em {path})"

    def _first_mon(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self._open_summary(0)
        assert self._state()[0] == PSS_PAGE_INFO, "o resumo não abriu na página INFO"
        self._flip(KEY_RIGHT, 1, "página SKILLS")
        self._flip(KEY_RIGHT, PSS_PAGE_MOVES, "página KNOWN MOVES")
        self._flip(KEY_RIGHT, PSS_PAGE_EVOLUTION, "página EVOLUTION")
        self._flip(KEY_RIGHT, PSS_PAGE_IVS, "página IVs/EVs")
        return "INFO -> SKILLS -> KNOWN MOVES -> EVOLUTION -> IVs/EVs com →; " + self._check_ivs_page(0)

    def _back_and_forth(self) -> str:
        self._flip(KEY_LEFT, PSS_PAGE_EVOLUTION, "← de volta para EVOLUTION")
        species = SHOWCASE[0][0]
        got = self.box.evolution_text(from_open_summary=True)
        assert got == self._expected(species), f"página EVOLUTION com '{self._read(got)}'"
        self._flip(KEY_RIGHT, PSS_PAGE_IVS, "→ de novo para IVs/EVs")
        self._check_ivs_page(0)
        return "← volta para EVOLUTION (texto certo) e → leva de novo para IVs/EVs"

    def _next_mon(self, index: int) -> str:
        self.ctl.press_until(KEY_DOWN, lambda: self._viewed_slot() == index,
                             f"troca para o slot {index}", tries=3, wait=FLIP_WAIT)
        self._wait_summary("troca de Pokémon terminada")
        return self._check_ivs_page(index)

    def _egg_is_skipped(self) -> str:
        self._press(KEY_DOWN)
        self.emu.frames(FLIP_WAIT)
        self._wait_summary("resumo depois do ↓ no último Pokémon")
        last = len(SHOWCASE) - 1
        assert self._viewed_slot() == last, f"↓ no último Pokémon foi para o slot {self._viewed_slot()}"
        assert self._state()[0] == PSS_PAGE_IVS, "saiu da página IVs/EVs"
        self._close_summary("fim da troca de Pokémon")
        return "↓ no último Pokémon não leva ao ovo do slot 5 (continua na página IVs/EVs)"

    def run(self) -> None:
        try:
            self._flow("resumo_ivs: CONTINUAR com o save do modo rápido e time de teste", self._start)
            self.suite.run("resumo_ivs: texto da página para bordas e combinações sorteadas",
                           self._all_cases_text)
            self._flow("resumo_ivs: START > POKéMON > SUMMARY e → até a página IVs/EVs",
                       self._first_mon)
            self._flow("resumo_ivs: ← volta para EVOLUTION", self._back_and_forth)
            for index in range(1, len(SHOWCASE)):
                name = SHOWCASE[index][0].removeprefix("SPECIES_").capitalize()
                self._flow(f"resumo_ivs: ↓ troca para {name} na página IVs/EVs",
                           lambda i=index: self._next_mon(i))
            self._flow("resumo_ivs: ↓ não leva ao ovo", self._egg_is_skipped)
            self._flow("resumo_ivs: ovo não mostra a página", self._egg_has_no_pages)
        except Abort:
            pass


def run_full_summary_ivs(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    SummaryIvsScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only resumo_ivs ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "resumo_ivs", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
