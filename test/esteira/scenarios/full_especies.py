"""Modo completo: Gible, Gabite, Garchomp e Darkrai (POK-54), na build de teste.

As 4 espécies da Gen 4 entram depois do Ovo e das letras do Unown (ids 440-443). Este cenário confere que um
Pokémon delas funciona nas telas de verdade. Sessão própria da ROM de teste a partir do .sav do `captura`
(`save_from="captura"`):

- `especies/resumo`: SET_PARTY_MON Gible nv 20, Gabite nv 30, Garchomp nv 30 e Darkrai nv 50 (abaixo dos golpes
  novos da Task 5) e PARTY_SIZE 4. Pelo menu de verdade (START > POKéMON > RESUMO), cada um passa por todas as
  páginas com → até IVs/EVs sem travar (SUMMARY_STATE), e o texto da EVOLUTION (EVOLUTION_TEXT) bate com o espelho
  `esteira/evolution_page.py`. Telas da página INFO (sprite, nome, tipos): `especie_resumo_garchomp` e
  `especie_resumo_darkrai`;
- `especies/icones`: o menu da equipe com os 4 (ícone e paleta de cada um) → `especie_icones_equipe`;
- `especies/evolucao`: EVOLUTION_TARGET no modo normal: Gible nv 23 não evolui, nv 24 vira GABITE; Gabite nv 47 não,
  nv 48 vira GARCHOMP; Garchomp e Darkrai nv 100 não evoluem;
- `especies/creche`: BREED_SETUP Garchomp + Ditto → compatível, e BREED_EGGS 8 → 8 ovos de GIBLE; Gabite +
  Charizard (Monstro) → compatível; Darkrai + Ditto → 0 (grupo Indescoberto);
- `especies/batalha` (último: a batalha fica aberta): SET_LEAD_LOOK Garchomp shiny e START_WILD_BATTLE Darkrai nv 50.
  No menu de ação, as espécies de gBattleMons são as duas → `especie_batalha_darkrai` (frente do Darkrai e costas
  shiny do Garchomp).

Telas em OUT/telas/<ponto>.png, comparadas com test/referencias/COMUM/ (diferença é só aviso).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only especies
Numa janela, em tempo real: `make test-watch CENARIO=especies`.
"""

import struct
import sys

from ..battle import BattleDriver
from ..breeding import BATCH, PARENT_FORMAT, PROBES_FORMAT, RECORD_SIZE, Parent, unpack_records
from ..emu import KEY_B, KEY_RIGHT
from ..field_menu import STARTMENU_POKEMON
from ..hooks import (CMD_BREED_EGGS, CMD_BREED_SETUP, CMD_START_WILD_BATTLE, EVO_MODE_NORMAL, NO_RESULT,
                     PSS_PAGE_EVOLUTION, PSS_PAGE_INFO, PSS_PAGE_IVS, PSS_PAGE_MOVES, PSS_PAGE_SKILLS, Mailbox)
from . import ScenarioContext
from .base import Abort
from .full_breeding import FRAMES_PER_EGG_LIMIT, GENDER_CODE
from .full_summary_evolution import PARTY_CHOOSE_TASK, SETTLE, SummaryEvolutionScenario

SCREEN_POINTS = ("especie_resumo_garchomp", "especie_resumo_darkrai", "especie_icones_equipe",
                 "especie_batalha_darkrai")
# o time do resumo e dos ícones: (espécie, nível); os níveis ficam abaixo dos golpes novos da Task 5
TEAM = (("SPECIES_GIBLE", 20), ("SPECIES_GABITE", 30), ("SPECIES_GARCHOMP", 30), ("SPECIES_DARKRAI", 50))
SUMMARY_SHOTS = {"SPECIES_GARCHOMP": "especie_resumo_garchomp", "SPECIES_DARKRAI": "especie_resumo_darkrai"}
PAGES = ((PSS_PAGE_SKILLS, "SKILLS"), (PSS_PAGE_MOVES, "KNOWN MOVES"), (PSS_PAGE_EVOLUTION, "EVOLUTION"),
         (PSS_PAGE_IVS, "IVs/EVs"))
# (espécie, nível, alvo esperado no modo normal; None = não evolui)
EVOLUTIONS = (("SPECIES_GIBLE", 23, None), ("SPECIES_GIBLE", 24, "SPECIES_GABITE"),
              ("SPECIES_GABITE", 47, None), ("SPECIES_GABITE", 48, "SPECIES_GARCHOMP"),
              ("SPECIES_GARCHOMP", 100, None), ("SPECIES_DARKRAI", 100, None))
# creche: (pai, mãe, compatível?)
DITTO = Parent("SPECIES_DITTO", "-", 0)
PAIRS = ((Parent("SPECIES_GARCHOMP", "M", 0), DITTO, True),
         (Parent("SPECIES_GABITE", "M", 0), Parent("SPECIES_CHARIZARD", "F", 0), True),
         (Parent("SPECIES_DARKRAI", "-", 0), DITTO, False))
EGGS = 8
LEAD = ("SPECIES_GARCHOMP", 30)
WILD = ("SPECIES_DARKRAI", 50)


class EspeciesScenario(SummaryEvolutionScenario):
    # --- utilidades ----------------------------------------------------------------
    def _name(self, species: int) -> str:
        return self.consts.species_name(species).removeprefix("SPECIES_") if species else "nenhuma"

    def _parent_bytes(self, p: Parent) -> bytes:
        moves = [0] * 4
        return struct.pack(PARENT_FORMAT, self._sp(p.species), 0, *moves, *p.ivs, GENDER_CODE[p.gender],
                           p.nature, p.ability)

    def _back_to_field(self) -> None:
        """Do menu da equipe para o campo: B até o menu START e fecha."""
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             "volta ao menu START", tries=6, wait=120)
        self.menu.close_start_menu()

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="especies_continue")
        assert self.game.party(), "save sem Pokémon no time"
        for slot, (species, level) in enumerate(TEAM):
            self.box.set_party_mon(slot, self._sp(species), level)
        assert self.box.party_size(len(TEAM)) == len(TEAM)
        got = [(m.species, m.level) for m in self.game.party()]
        want = [(self._sp(s), lv) for s, lv in TEAM]
        assert got == want, f"time montado errado: {got}"
        return ("CONTINUAR no Centro de Viridian; time de teste: "
                + ", ".join(f"{s.removeprefix('SPECIES_')} nv {lv}" for s, lv in TEAM))

    def _summary(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        out = []
        for slot, (species, _level) in enumerate(TEAM):
            self._open_summary(slot)
            state = self._state()
            assert state is not None and state[0] == PSS_PAGE_INFO and not state[2], \
                f"{species}: o resumo abriu em {state}"
            assert self._viewed_slot() == slot, f"resumo no slot {self._viewed_slot()}"
            shot = ""
            if species in SUMMARY_SHOTS:
                self.emu.frames(SETTLE)
                shot = f" (tela {self._shot(SUMMARY_SHOTS[species])})"
                self._pause_to_read()
            for page, name in PAGES:
                self._flip(KEY_RIGHT, page, f"{species}: página {name}")
                if page == PSS_PAGE_EVOLUTION:
                    got, want = self.box.evolution_text(from_open_summary=True), self._expected(species)
                    assert got == want, \
                        f"{species}: página EVOLUTION com '{self._read(got)}', esperado '{self._read(want)}'"
                    evo = self._read(got)
            assert self._state()[0] == PSS_PAGE_IVS, f"{species}: não chegou à página IVs/EVs"
            self._close_summary(species)
            out.append(f"{species.removeprefix('SPECIES_')}: INFO → IVs/EVs, EVOLUTION '{evo}'{shot}")
        self._back_to_field()
        return "; ".join(out)

    def _icons(self) -> str:
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self.ctl.wait_until(lambda: PARTY_CHOOSE_TASK in self._tasks() and not self._fade_active(), 600,
                            "menu da equipe")
        self.emu.frames(SETTLE * 3)
        path = self._shot("especie_icones_equipe")
        self._pause_to_read()
        self._back_to_field()
        return f"menu da equipe com {', '.join(s.removeprefix('SPECIES_') for s, _ in TEAM)} (tela {path})"

    def _evolution(self) -> str:
        wrong, seen = [], []
        for species, level, want in EVOLUTIONS:
            got = self.box.evolution_target(self._sp(species), EVO_MODE_NORMAL, level)
            label = f"{species.removeprefix('SPECIES_')} nv {level} → {self._name(got)}"
            seen.append(label)
            if got != (self._sp(want) if want else 0):
                wrong.append(f"{label}, esperava {want.removeprefix('SPECIES_') if want else 'nenhuma'}")
        assert not wrong, "; ".join(wrong)
        return "; ".join(seen)

    def _setup(self, father: Parent, mother: Parent) -> int:
        raw = (self._parent_bytes(father) + self._parent_bytes(mother) + struct.pack(PROBES_FORMAT, 0, 0, 0, 0))
        self.emu.write(self.game.syms.addr("gTestBreedSetup"), raw)
        compat = self.box.call(CMD_BREED_SETUP, 0)
        assert compat != NO_RESULT, f"o jogo recusou {father.species} ou {mother.species}"
        return compat

    def _daycare(self) -> str:
        out = []
        for father, mother, compatible in PAIRS:
            compat = self._setup(father, mother)
            label = f"{father.species.removeprefix('SPECIES_')} + {mother.species.removeprefix('SPECIES_')}"
            assert (compat > 0) == compatible, f"{label}: compatibilidade {compat}"
            out.append(f"{label}: compatibilidade {compat}")
            if father.species == "SPECIES_GARCHOMP":
                assert EGGS <= BATCH
                got = self.box.call(CMD_BREED_EGGS, EGGS, timeout=EGGS * FRAMES_PER_EGG_LIMIT)
                assert got == EGGS, f"BREED_EGGS devolveu {got:#x}"
                recs = unpack_records(self.emu.read(self.game.syms.addr("gEnemyParty"), RECORD_SIZE * EGGS), EGGS)
                species = sorted({self._name(r.species) for r in recs})
                assert all(r.species == self._sp("SPECIES_GIBLE") and r.is_egg for r in recs), \
                    f"ovos de {species} (marca de ovo: {[r.is_egg for r in recs]})"
                out[-1] += f", {EGGS} ovos de GIBLE"
        return "; ".join(out)

    def _battle(self) -> str:
        lead = self.box.set_lead_look(self._sp(LEAD[0]), LEAD[1], shiny=True)
        assert lead["especie"] == self._sp(LEAD[0]) and lead["shiny"], f"SET_LEAD_LOOK: {lead}"
        species, level = WILD
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp(species), level) == 1, "START_WILD_BATTLE"
        d = BattleDriver(self.ctl)
        d.wait_action_menu()
        mine, foe = d.battler_species_level(0), d.battler_species_level(1)
        assert mine == (self._sp(LEAD[0]), LEAD[1]), f"o jogador está com {mine}"
        assert foe == (self._sp(species), level), f"o selvagem é {foe}"
        self.emu.frames(SETTLE)
        path = self._shot("especie_batalha_darkrai")
        self._pause_to_read()
        return (f"{species.removeprefix('SPECIES_')} nv {level} contra {LEAD[0].removeprefix('SPECIES_')} shiny: "
                f"menu de ação aberto (tela {path})")

    def run(self) -> None:
        try:
            self._flow("especies: CONTINUAR com o save do modo rápido e o time das 4", self._start)
            self._flow("especies/resumo: as 4 passam por todas as páginas do resumo", self._summary)
            self._flow("especies/icones: o menu da equipe com as 4", self._icons)
            self.suite.run("especies/evolucao: Gible no 24 e Gabite no 48", self._evolution)
            self.suite.run("especies/creche: o Gible nasce do ovo; o Darkrai não cruza", self._daycare)
            self._flow("especies/batalha: Darkrai selvagem contra o Garchomp shiny", self._battle)
        except Abort:
            pass


def run_full_especies(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    EspeciesScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only especies ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "especies", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
