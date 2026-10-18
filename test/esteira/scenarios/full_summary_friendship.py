"""Modo completo: amizade com corações na página EVOLUTION do resumo (Hack 7, frente D).

Na build de teste, a partir do .sav do modo rápido (a condução do menu é a do `resumo_evolucao`).
A 6ª linha da página sempre mostra a amizade do Pokémon: "<corações> <n>/255 <frase>", com a marca
" (220+)" a partir de 220 (esteira/evolution_page.py: `friendship_line`).

- amizade/textos: GetFriendshipLineText para 0..255 (atalho FRIENDSHIP_TEXT, arg1 = 0) é igual,
  byte a byte, ao texto gerado em Python;
- amizade/pagina: Eevee com amizade 230 -> START > POKéMON > SUMMARY > → → → na página EVOLUTION: a
  linha impressa é `friendship_line(230)` e o texto das evoluções não mudou; ↓ para o Onix, com
  amizade 0: linha sem corações. Tela do Eevee: telas/resumo_amizade_eevee.png.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only resumo_amizade
"""

import sys

from ..emu import KEY_B, KEY_DOWN, KEY_RIGHT
from ..evolution_page import (FRIENDSHIP_SCREEN_POINTS, SHOWCASE, friendship_hearts,
                              friendship_line)
from ..field_menu import STARTMENU_POKEMON
from ..hooks import PSS_PAGE_EVOLUTION, PSS_PAGE_INFO, PSS_PAGE_MOVES
from . import ScenarioContext
from .base import Abort
from .full_summary_evolution import SHOWCASE_LEVEL, SummaryEvolutionScenario

EEVEE_FRIENDSHIP = 230


class SummaryFriendshipScenario(SummaryEvolutionScenario):
    def _expected_line(self, friendship: int) -> bytes:
        return self.page.encode(friendship_line(friendship))

    def _team(self) -> str:
        detail = self._start()
        self.box.set_party_mon(0, self._sp(SHOWCASE[0]), SHOWCASE_LEVEL, friendship=EEVEE_FRIENDSHIP)
        self.box.set_party_mon(1, self._sp(SHOWCASE[1]), SHOWCASE_LEVEL)
        self.box.zero_friendship(1)
        return detail + f"; Eevee com amizade {EEVEE_FRIENDSHIP} e Onix com amizade 0"

    def _texts(self) -> str:
        wrong = []
        for friendship in range(256):
            got, want = self.box.friendship_text(friendship), self._expected_line(friendship)
            if got != want:
                wrong.append(f"{friendship}: jogo '{self._read(got)}', esperado '{self._read(want)}'")
        assert not wrong, f"{len(wrong)} amizade(s) com texto diferente: " + "; ".join(wrong[:6])
        return ("GetFriendshipLineText igual ao texto gerado em Python para 0..255; "
                f"230: '{self._read(self.box.friendship_text(230))}'")

    def _check_line(self, friendship: int, species: str) -> str:
        got = self.box.friendship_text(from_open_summary=True)
        want = self._expected_line(friendship)
        assert got == want, f"linha de amizade: '{self._read(got)}', esperado '{self._read(want)}'"
        evo, want_evo = self.box.evolution_text(from_open_summary=True), self._expected(species)
        assert evo == want_evo, f"texto das evoluções mudou: '{self._read(evo)}'"
        return f"{species.removeprefix('SPECIES_')}: '{self._read(got)}' ({friendship_hearts(friendship)} corações)"

    def _page(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self._open_summary(0)
        assert self._state()[0] == PSS_PAGE_INFO, "o resumo não abriu na página INFO"
        self._flip(KEY_RIGHT, 1, "página SKILLS")
        self._flip(KEY_RIGHT, PSS_PAGE_MOVES, "página KNOWN MOVES")
        self._flip(KEY_RIGHT, PSS_PAGE_EVOLUTION, "página EVOLUTION")
        eevee = self._check_line(EEVEE_FRIENDSHIP, SHOWCASE[0])
        self.emu.frames(10)
        shot = self._shot(FRIENDSHIP_SCREEN_POINTS[0])
        self._pause_to_read()
        self.ctl.press_until(KEY_DOWN, lambda: self._viewed_slot() == 1, "troca para o slot 1",
                             tries=3, wait=40)
        self._wait_summary("troca de Pokémon terminada")
        assert self._state()[0] == PSS_PAGE_EVOLUTION, "↓ saiu da página EVOLUTION"
        onix = self._check_line(0, SHOWCASE[1])
        assert "{EMOJI_HEART}" not in self._read(self.box.friendship_text(from_open_summary=True))
        self._pause_to_read()
        self._close_summary("amizade")
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             "volta ao menu START", tries=6, wait=120)
        self.menu.close_start_menu()
        return f"{eevee} (tela em {shot}); ↓ {onix}"

    def run(self) -> None:
        try:
            self._flow("resumo_amizade: CONTINUAR com o save do modo rápido e time de teste",
                       self._team)
            self.suite.run("amizade/textos: GetFriendshipLineText de 0 a 255", self._texts)
            self._flow("amizade/pagina: linha de amizade na 6ª linha da página EVOLUTION",
                       self._page)
        except Abort:
            pass


def run_full_summary_friendship(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    SummaryFriendshipScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only resumo_amizade ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "resumo_amizade",
                     *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
