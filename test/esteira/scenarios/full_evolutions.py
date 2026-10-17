"""Modo completo: fim das evoluções por troca (Hack 3), na build de teste (TESTBUILD=1).

As regras (esteira/evolutions.py): Kadabra, Haunter, Machoke e Graveler evoluem no nível 37;
Slowpoke e Poliwhirl (King's Rock), Onix e Scyther (Metal Coat), Seadra (Dragon Scale),
Porygon (Up-Grade) e Clamperl (DeepSeaTooth/DeepSeaScale) evoluem em qualquer subida de nível
a partir do 37 segurando o item, que não é consumido. Troca não evolui mais nenhum deles. E
não há mais a trava da Dex Nacional: qualquer evolução (inclusive para espécies de fora de
Kanto, como Steelix, Bellossom e Crobat) acontece em qualquer ponto do jogo.

Ponto de partida: o .sav do fim do modo rápido (Centro de Viridian, SEM a Dex Nacional), como o
`shiny`; o CLI abre uma sessão própria da ROM de teste para este cenário
(`save_from="captura"`). Os atalhos da build de teste (esteira/hooks.py) só montam o Pokémon
(espécie, nível, item segurado, amizade), dão itens à bolsa e consultam
GetEvolutionTargetSpecies no modo troca. A SUBIDA DE NÍVEL é a de verdade: START > BOLSA >
RARE CANDY > USAR > Pokémon (a pedra também: SUN STONE > USAR), e a cena de evolução roda
inteira (perguntas de golpe novo são recusadas: NÃO para esquecer um golpe, SIM para desistir).
O Metal Coat do caso "passou do 37" é dado pela bolsa (DAR). Tudo sem a Dex Nacional:

1. os 12 casos das regras evoluem (os 4 sem item; os 8 com item, que continua segurado) e o
   Slowpoke 36 sem item vira Slowbro;
2. de fora de Kanto por outros caminhos: Gloom + Sun Stone (pela bolsa) -> Bellossom e
   Golbat com amizade alta + Rare Candy -> Crobat;
3. Onix + King's Rock (item errado) e Clamperl sem item não evoluem;
4. Onix 39 sem item sobe para 40 e continua Onix; recebe o Metal Coat pela bolsa; sobe para
   41 e vira Steelix, ainda segurando o Metal Coat (o exemplo do Cintra);
5. modo troca devolve 0 para os 11, com e sem o item antigo (e conferências do atalho:
   Water Stone ainda faz Poliwrath, Everstone ainda segura);
6. no fim a Dex Nacional continua desligada.

Telas antes/depois de cada cena: OUT/telas/evo_<alvo>_antes.png/_depois.png, comparadas com
test/referencias/COMUM/ (diferença é só aviso).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only evolucoes
Numa janela, em tempo real: `make test-watch CENARIO=evolucoes`.
"""

import sys

from ..bag import Bag
from ..emu import KEY_A, KEY_B
from ..evolutions import HOLD_ITEM_LEVEL, OLD_TRADE_ITEMS, RULES, SPECIES
from ..field_menu import STARTMENU_BAG
from ..hooks import (CMD_GIVE_ITEM, EVO_MODE_ITEM_USE, EVO_MODE_NORMAL, EVO_MODE_TRADE,
                     Mailbox)
from . import ScenarioContext
from .base import TEXT_PERIOD, Abort
from .quick_catch_save import CatchSaveScenario

# Task_EvolutionScene (src/evolution_scene.c): data[0] = tState, data[6] = tLearnMoveState,
# data[8] = tLearnMoveNoState; valores dos enums EVOSTATE_* e MVSTATE_* (conferidos com o
# fonte em tests/test_evolucoes_cenario.py)
EVO_TASK = "Task_EvolutionScene"
EVO_STATE, EVO_LEARN_STATE, EVO_LEARN_NO_STATE = 0, 6, 8
EVOSTATE_START_MUSIC = 4            # "Hã? X está evoluindo!" já na tela, antes do escurecer
EVOSTATE_TRY_LEARN_MOVE = 15        # "Parabéns! ... evoluiu para Y!" (ou "……?" se cancelou)
EVOSTATE_REPLACE_MOVE = 22
MVSTATE_HANDLE_YES_NO = 4
MVSTATE_ASK_CANCEL = 10             # tLearnMoveNoState da 1ª pergunta ("esquecer um golpe?")
BUTTON_WAIT_STATES = {1, 2, 3}      # RENDER_STATE_WAIT/CLEAR/SCROLL_START: o texto espera um botão

# menu de Pokémon (src/party_menu.c) depois da Rare Candy: as duas perguntas de golpe novo
PARTY_REPLACE_MOVE_YESNO = "Task_HandleReplaceMoveYesNoInput"     # esquecer um golpe? -> NÃO
PARTY_STOP_LEARNING_YESNO = "Task_HandleStopLearningMoveYesNoInput"  # desistir? -> SIM

RARE_CANDIES = 30
CROBAT_FRIENDSHIP = 250             # EVO_FRIENDSHIP pede >= 220
CANDY_TIMEOUT = 5000                # Rare Candy + cena de evolução inteira (~1 000 quadros)
EVO_POLL = 2


class EvolutionsScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.bag = Bag(self.ctl)
        self.slot = 0
        self.candy = self.consts.item("ITEM_RARE_CANDY")

    # --- utilidades ----------------------------------------------------------------
    def _sp(self, name: str) -> int:
        return self.consts.species(name)

    def _item(self, name: str | None) -> int:
        return self.consts.item(name) if name else 0

    def _name(self, species: int) -> str:
        return self.consts.species_name(species).removeprefix("SPECIES_")

    def _item_name(self, item_id: int) -> str:
        """Nome dos itens que o cenário usa (o número, para qualquer outro)."""
        if item_id == 0:
            return "nada"
        known = {r.item for r in RULES if r.item} | {"ITEM_RARE_CANDY", "ITEM_EVERSTONE",
                                                      "ITEM_SUN_STONE"}
        names = {self.consts.item(n): n.removeprefix("ITEM_") for n in known}
        return names.get(item_id, f"item {item_id}")

    def _mon(self):
        return self.game.party()[self.slot]

    def _national_dex(self) -> bool:
        return self.game.flag(self.consts.flag("FLAG_SYS_NATIONAL_DEX"))

    # --- início --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="evolucoes_continue")
        assert not self._national_dex(), "o save já tem a Dex Nacional"
        party = self.game.party()
        assert party, "save sem Pokémon no time"
        self.slot = min(len(party), 5)      # o 1º lugar livre (ou o último, com o time cheio)
        for item, qty in (("ITEM_RARE_CANDY", RARE_CANDIES), ("ITEM_METAL_COAT", 1),
                          ("ITEM_SUN_STONE", 1)):
            assert self.box.call(CMD_GIVE_ITEM, self.consts.item(item), qty) == 1, \
                f"AddBagItem({item}, {qty}) falhou"
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_BAG)
        self.bag.wait_ready()
        return (f"CONTINUAR no Centro de Viridian; time de {len(party)}, Pokémon de teste no "
                f"slot {self.slot}; {RARE_CANDIES} Rare Candy, 1 Metal Coat e 1 Sun Stone na "
                "bolsa; Dex Nacional desligada")

    # --- Rare Candy pelo menu, com a cena de evolução ------------------------------
    def _drive_evolution_scene(self, info: dict, shot: str | None) -> None:
        data = self.game.task_data(EVO_TASK)
        if data is None:          # a task acabou de sair/entrar: só deixa o jogo andar
            self.emu.frames(EVO_POLL)
            return
        info["scene"] = True
        state = data[EVO_STATE]
        if shot and "antes" not in info and state >= EVOSTATE_START_MUSIC:
            info["antes"] = self._shot(f"{shot}_antes")
        waiting = (self.game.text_printer_active(0)
                   and self.game.text_printer_state(0) in BUTTON_WAIT_STATES)
        if state == EVOSTATE_REPLACE_MOVE and data[EVO_LEARN_STATE] == MVSTATE_HANDLE_YES_NO:
            if data[EVO_LEARN_NO_STATE] == MVSTATE_ASK_CANCEL:
                self._press(KEY_B)              # "Apagar um golpe para aprender X?" -> NÃO
                info["recusas"] += 1
            else:
                self._press(KEY_A)              # "Desistir de aprender X?" -> SIM
        elif waiting:
            if shot and state == EVOSTATE_TRY_LEARN_MOVE and "depois" not in info:
                info["depois"] = self._shot(f"{shot}_depois")
            self._press(KEY_A)
        else:
            self.emu.frames(EVO_POLL)           # nada de botão na animação (B cancela)

    def _use_item(self, item_id: int, shot: str | None = None) -> dict:
        """Usa o item (Rare Candy ou pedra) no Pokémon de teste pela bolsa (já aberta) e
        conduz o que vier (subida de nível, golpes, cena de evolução) até a bolsa voltar."""
        info: dict = {"scene": False, "recusas": 0}
        self.bag.select(item_id)
        self.bag.use_selected()
        self.bag.choose_party_slot(self.slot)
        spent = 0
        while not self.bag.ready():
            if spent >= CANDY_TIMEOUT:
                raise self.ctl.timeout_error(f"bolsa de volta depois de usar o item {item_id}")
            before = self.emu.frames(0)
            tasks = self._tasks()
            if EVO_TASK in tasks or self.game.callback2() == "CB2_EvolutionSceneUpdate":
                self._drive_evolution_scene(info, shot)
            elif PARTY_REPLACE_MOVE_YESNO in tasks:
                self._press(KEY_B)
                info["recusas"] += 1
            elif PARTY_STOP_LEARNING_YESNO in tasks:
                self._press(KEY_A)
            else:
                self._press(KEY_A)
            spent += max(self.emu.frames(0) - before, 1)
        if shot and info["scene"]:
            missing = [w for w in ("antes", "depois") if w not in info]
            assert not missing, f"tela(s) {missing} da cena de evolução não gravada(s)"
        return info

    # --- casos ---------------------------------------------------------------------
    def _case(self, name: str, species: str, level: int, item: str | None, expect: str,
              shot: str | None = None, set_mon: bool = True, use: str = "ITEM_RARE_CANDY",
              friendship: int = 0) -> None:
        """Monta o Pokémon (ou usa o que está no slot), usa uma Rare Candy (ou a pedra `use`)
        e confere espécie, nível, item segurado, o item usado gasto, se a cena abriu e que
        nenhum golpe foi esquecido."""
        info: dict = {}

        def run() -> str:
            want_item, want_species = self._item(item), self._sp(expect)
            used = self.consts.item(use)
            want_level = level + 1 if used == self.candy else level
            if set_mon:
                self.box.set_party_mon(self.slot, self._sp(species), level, want_item,
                                       friendship)
            mon = self._mon()
            assert (mon.species, mon.level, mon.held_item) == (self._sp(species), level, want_item), \
                f"Pokémon de teste {self._name(mon.species)} nv {mon.level} item {mon.held_item}"
            moves_before = {m for m in mon.moves if m}
            stock = self.game.bag_quantity(used)
            info.update(self._use_item(used, shot))
            after = self._mon()
            evolved = want_species != mon.species
            detail = (f"{self._name(mon.species)} nv {level} segurando "
                      f"{self._item_name(want_item)}, {self._item_name(used)} -> "
                      f"{self._name(after.species)} nv {after.level} segurando "
                      f"{self._item_name(after.held_item)}; cena de evolução: "
                      f"{'sim' if info['scene'] else 'não'}; perguntas de golpe recusadas: "
                      f"{info['recusas']}")
            assert self.game.bag_quantity(used) == stock - 1, \
                f"{self._item_name(used)} na bolsa: {stock} -> {self.game.bag_quantity(used)}"
            assert after.level == want_level, f"nível {after.level}, esperava {want_level}: {detail}"
            assert after.species == want_species, f"esperava {expect}: {detail}"
            assert after.held_item == want_item, f"item segurado mudou: {detail}"
            if evolved:
                assert info["scene"], f"evoluiu sem a cena: {detail}"
            forgotten = moves_before - set(after.moves)
            assert not forgotten, f"golpes esquecidos {sorted(forgotten)}: {detail}"
            return detail

        res = self.suite.run(f"evolucoes: {name}", run)
        res.images += [info[w] for w in ("antes", "depois") if w in info]
        if res.state is not None:       # tempo esgotado: a tela está num lugar desconhecido
            raise Abort(name)

    def _give_metal_coat(self) -> str:
        coat = self.consts.item("ITEM_METAL_COAT")
        qty = self.game.bag_quantity(coat)
        self.bag.select(coat)
        self.bag.give_selected()
        self.bag.choose_party_slot(self.slot)
        # "ONIX recebeu o METAL COAT para segurar." e a bolsa volta
        self.ctl.advance_text(self.bag.ready, CANDY_TIMEOUT, "bolsa de volta depois de DAR")
        mon = self._mon()
        assert mon.held_item == coat, f"{self._name(mon.species)} segura {self._item_name(mon.held_item)}"
        assert self.game.bag_quantity(coat) == qty - 1, "o Metal Coat não saiu da bolsa"
        return f"{self._name(mon.species)} nv {mon.level} agora segura o Metal Coat (pela bolsa)"

    def _still_no_national_dex(self) -> str:
        assert not self._national_dex(), "a Dex Nacional foi ligada durante o cenário"
        return ("Dex Nacional continua desligada: todas as evoluções acima aconteceram sem ela "
                "(sem a trava original de espécies de fora de Kanto)")

    def _trade_never_evolves(self) -> str:
        """GetEvolutionTargetSpecies(mon, EVO_MODE_TRADE) = 0 para os 11, sem item e com o
        item que antes os fazia evoluir na troca."""
        wrong, checked = [], 0
        for species in SPECIES:
            for item in (None, *OLD_TRADE_ITEMS[species]):
                target = self.box.evolution_target(self._sp(species), EVO_MODE_TRADE,
                                                   held_item=self._item(item))
                checked += 1
                if target != 0:
                    wrong.append(f"{species} segurando {item or 'nada'} -> {self._name(target)}")
        assert not wrong, "troca ainda evolui: " + "; ".join(wrong)
        return (f"{checked} consultas no modo troca, todas 0 ({len(SPECIES)} espécies, sem item "
                "e com o item antigo)")

    def _hook_sanity(self) -> str:
        """O atalho de consulta responde de verdade (senão o 0 da troca não valeria nada) e
        as outras regras continuam: nível, item de evolução e Everstone."""
        box, sp, it = self.box, self._sp, self.consts.item
        checks = [
            ("Kadabra nv 37, modo normal", box.evolution_target(sp("KADABRA"), EVO_MODE_NORMAL,
                                                               level=HOLD_ITEM_LEVEL),
             sp("ALAKAZAM")),
            ("Kadabra nv 36, modo normal", box.evolution_target(sp("KADABRA"), EVO_MODE_NORMAL),
             0),
            ("Kadabra nv 37 segurando Everstone", box.evolution_target(
                sp("KADABRA"), EVO_MODE_NORMAL, level=HOLD_ITEM_LEVEL,
                held_item=it("ITEM_EVERSTONE")), 0),
            ("Slowpoke nv 50 segurando King's Rock", box.evolution_target(
                sp("SLOWPOKE"), EVO_MODE_NORMAL, level=50, held_item=it("ITEM_KINGS_ROCK")),
             sp("SLOWKING")),
            ("Poliwhirl + Water Stone", box.evolution_target(
                sp("POLIWHIRL"), EVO_MODE_ITEM_USE, evolution_item=it("ITEM_WATER_STONE")),
             sp("POLIWRATH")),
        ]
        wrong = [f"{what}: {got}, esperava {want}" for what, got, want in checks if got != want]
        assert not wrong, "; ".join(wrong)
        return "; ".join(f"{what} -> {self._name(got) if got else 0}" for what, got, _ in checks)

    def _close_bag(self) -> str:
        self.ctl.press_until(KEY_B, lambda: not self.bag.ready(), "bolsa fechada")
        self.ctl.wait_until(self.menu.start_menu_open, 600, "menu START depois da bolsa")
        self.menu.close_start_menu()
        return f"de volta ao jogo em {self.game.player_xy()}"

    # --- roteiro -------------------------------------------------------------------
    def run(self) -> None:
        try:
            self._flow("evolucoes: CONTINUAR com o save do modo rápido na build de teste",
                       self._start)
            # 1. as regras, sem a Dex Nacional (como no save)
            for rule in RULES:
                kept = " (item continua segurado)" if rule.item else ""
                self._case(f"{self._label(rule)}{kept}, sem Dex Nacional", rule.species,
                           HOLD_ITEM_LEVEL - 1, rule.item, rule.target, shot=f"evo_{rule.slug}")
            self._case("Slowpoke 36 sem item -> Rare Candy -> Slowbro", "SPECIES_SLOWPOKE",
                       HOLD_ITEM_LEVEL - 1, None, "SPECIES_SLOWBRO", shot="evo_slowbro")
            # 2. fora de Kanto por pedra e por amizade, sem a Dex Nacional
            self._case("Gloom + Sun Stone (pela bolsa) -> Bellossom, sem Dex Nacional",
                       "SPECIES_GLOOM", 30, None, "SPECIES_BELLOSSOM", shot="evo_bellossom",
                       use="ITEM_SUN_STONE")
            self._case(f"Golbat 30 com amizade {CROBAT_FRIENDSHIP} -> Rare Candy -> Crobat, "
                       "sem Dex Nacional", "SPECIES_GOLBAT", 30, None, "SPECIES_CROBAT",
                       shot="evo_crobat", friendship=CROBAT_FRIENDSHIP)
            # 3. item errado / sem item
            self._case("Onix 36 + King's Rock (item errado) -> Rare Candy -> continua Onix",
                       "SPECIES_ONIX", HOLD_ITEM_LEVEL - 1, "ITEM_KINGS_ROCK", "SPECIES_ONIX")
            self._case("Clamperl 36 sem item -> Rare Candy -> continua Clamperl",
                       "SPECIES_CLAMPERL", HOLD_ITEM_LEVEL - 1, None, "SPECIES_CLAMPERL")
            # 4. passou do 37 sem item (o exemplo do Cintra: Onix 40 + Metal Coat -> 41 Steelix)
            self._case("Onix 39 sem item -> Rare Candy -> continua Onix no 40", "SPECIES_ONIX",
                       39, None, "SPECIES_ONIX")
            self._flow("evolucoes: Onix 40 recebe o Metal Coat pela bolsa (DAR)",
                       self._give_metal_coat)
            self._case("Onix 40 + Metal Coat -> Rare Candy -> Steelix no 41, ainda com o "
                       "Metal Coat", "SPECIES_ONIX", 40, "ITEM_METAL_COAT", "SPECIES_STEELIX",
                       shot="evo_steelix_nivel41", set_mon=False)
            # 5. troca
            self.suite.run("evolucoes: atalho de consulta responde (nível, Everstone, pedra)",
                           self._hook_sanity)
            self.suite.run("evolucoes: troca não evolui nenhum dos 11 (com e sem o item antigo)",
                           self._trade_never_evolves)
            # 6. tudo isso sem a Dex Nacional
            self.suite.run("evolucoes: Dex Nacional continua desligada no fim",
                           self._still_no_national_dex)
            self._flow("evolucoes: fecha a bolsa e volta ao jogo", self._close_bag)
        except Abort:
            pass

    def _label(self, rule) -> str:
        how = f"segurando {rule.item.removeprefix('ITEM_')}" if rule.item else "sem item"
        return (f"{rule.species.removeprefix('SPECIES_').capitalize()} {HOLD_ITEM_LEVEL - 1} "
                f"{how} -> Rare Candy -> {rule.target.removeprefix('SPECIES_').capitalize()}")


def run_full_evolutions(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    EvolutionsScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only evolucoes ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "evolucoes",
                     *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
