"""Modo completo: Pokérus de verdade (POK-50), na build de teste.

No FRLG o Pokérus nunca acontecia: as três funções que o dão, espalham e contam os dias eram
stubs (src/pokemon.c). O POK-50 trouxe o corpo do Rubi/Safira e ligou os dias ao relógio do jogo
(Hack 7: um dia do jogo = uma hora jogada; DayNight_Tick chama UpdatePartyPokerusTime(1) a cada
meia-noite). O byte MON_DATA_POKERUS é cepa << 4 | dias: dias > 0 = infectado; cepa com 0 dias
= curado (os EVs continuam em dobro para sempre).

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). Time de
teste: 5 Pokémon e um ovo no slot 5. Os atalhos POKERUS_* (include/test_hooks.h, bloco 0x100)
gravam e leem o byte e chamam as funções do jogo:

1. `pokerus/pega`: GivePartyPokerusNow (o sorteio já ganho) infecta um só Pokémon, nunca o ovo,
   com dias = cepa % 4 + 1 (1 a 4); quem já teve não pega de novo;
2. `pokerus/sorteio`: RandomlyGivePartyPokerus (depois de toda batalha fora do link) dá o
   Pokérus em ~3 de 65536 vezes;
3. `pokerus/contagio`: PartySpreadPokerus passa a mesma cepa e os mesmos dias só ao vizinho
   (não pula dois slots de uma vez); curado não espalha; quem já teve não pega de novo;
4. `pokerus/dias`: relógio acertado em 23:59 (atalho SET_CLOCK): na meia-noite do jogo o
   infectado perde um dia, uma vez só; dois dias depois, fica curado (cepa mantida);
5. `pokerus/ev`: MonGainEVs dá o dobro com o Pokérus e também depois de curado;
6. `pokerus/telas`: o resumo do infectado (PKRS no lugar do status) e o do curado (o pontinho
   ao lado da Poké Ball) — telas `pokerus_resumo_infectado` e `pokerus_resumo_curado`. O menu de
   Pokémon não mostra o PKRS, como no Rubi/Safira/Esmeralda (UpdatePartyMonAilmentGfx);
7. `pokerus/enfermeira`: no Centro de Viridian, sem Pokérus no time a enfermeira só cura; com
   um infectado ela explica o Pokérus (tela `pokerus_enfermeira`) e liga FLAG_POKERUS_EXPLAINED;
   da vez seguinte não explica de novo. A cura não tira o Pokérus.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only pokerus
"""

import sys

from ..emu import KEY_A, KEY_B, KEY_UP
from ..field_menu import STARTMENU_POKEMON
from ..hooks import (POKERUS_DAYS, POKERUS_EVS, POKERUS_GIVE_NOW, POKERUS_ROLL, POKERUS_SPREAD,
                     Mailbox)
from . import ScenarioContext
from .base import TEXT_PERIOD, Abort
from .full_summary_evolution import PARTY_CHOOSE_TASK, SummaryEvolutionScenario

TEAM = ("SPECIES_PIDGEY", "SPECIES_RATTATA", "SPECIES_CATERPIE", "SPECIES_WEEDLE", "SPECIES_SPEAROW")
TEAM_LEVEL = 20
EGG_SLOT, EGG_SPECIES = 5, "SPECIES_TOGEPI"
GIVE_TRIES = 40
ROLLS = 0x40000                 # 262144 sorteios: espera 3/65536 x 262144 = 12
ROLL_MIN, ROLL_MAX = 2, 30
SPREAD_TRIES = 60               # 1 em 3 por chamada: (2/3)^60 de não espalhar nunca
MIDNIGHT_DAY, BEFORE_MIDNIGHT = 2, 23 * 60 + 59
FRAMES_PER_MINUTE = 150
EV_SPECIES = "SPECIES_PIDGEY"   # dá 1 EV de Velocidade
NURSE_FRONT = (7, 4)            # Centro de Viridian: enfermeira em (7, 2), balcão em (7, 3)
EXPLANATION = "infectados com o Pok"   # Text_PokerusExplanation (data/event_scripts.s)
MESSAGE_SETTLE = 90             # quadros para a 1ª caixa da explicação terminar de escrever
NURSE_TIMEOUT = 6000
SCREEN_POINTS = ("pokerus_resumo_infectado", "pokerus_resumo_curado")


def _days(value: int) -> int:
    return value & 0xF


def _strain(value: int) -> int:
    return value >> 4


class PokerusScenario(SummaryEvolutionScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None

    # --- utilidades ----------------------------------------------------------------
    def _set_all(self, values) -> None:
        for slot, value in enumerate(values):
            self.box.set_pokerus(slot, value)

    def _clean(self) -> None:
        self._set_all([0] * 6)

    def _bytes(self) -> list[int]:
        return self.box.pokerus_state()[0]

    @staticmethod
    def _hex(values) -> str:
        return " ".join(f"{v:02X}" for v in values)

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="pokerus_continue")
        assert self.game.party(), "save sem Pokémon no time"
        for slot, species in enumerate(TEAM):
            self.box.set_party_mon(slot, self._sp(species), TEAM_LEVEL)
        count = self.box.set_party_egg(EGG_SLOT, self._sp(EGG_SPECIES))
        assert count == 6, f"time com {count}"
        self._clean()
        values, infected, had = self.box.pokerus_state()
        assert values == [0] * 6 and infected == had == 0, self._hex(values)
        return (f"CONTINUAR no Centro de Viridian; time: "
                f"{', '.join(s.removeprefix('SPECIES_') for s in TEAM)} (nv {TEAM_LEVEL}) e um ovo "
                f"no slot {EGG_SLOT}; ninguém com Pokérus")

    def _give(self) -> str:
        slots, strains = set(), set()
        for _ in range(GIVE_TRIES):
            self._clean()
            values = self.box.pokerus_run(POKERUS_GIVE_NOW)
            hit = [s for s, v in enumerate(values) if v]
            assert len(hit) == 1, f"pegaram {len(hit)} de uma vez: {self._hex(values)}"
            slot, value = hit[0], values[hit[0]]
            assert slot != EGG_SLOT, f"o ovo pegou o Pokérus: {self._hex(values)}"
            assert _strain(value) != 0, f"cepa 0: {value:#04x}"
            assert _days(value) == _strain(value) % 4 + 1, (
                f"{value:#04x}: {_days(value)} dias, esperava cepa % 4 + 1 = {_strain(value) % 4 + 1}")
            slots.add(slot)
            strains.add(_strain(value))
        assert len(slots) > 1, f"sempre o mesmo slot: {slots}"
        had = [0x10] * EGG_SLOT + [0]
        self._set_all(had)
        values = self.box.pokerus_run(POKERUS_GIVE_NOW)
        assert values == had, f"quem já teve pegou de novo: {self._hex(values)}"
        self._clean()
        return (f"{GIVE_TRIES} vezes: um Pokémon por vez, nunca o ovo, dias = cepa % 4 + 1; slots "
                f"{sorted(slots)}, cepas {sorted(strains)}; time que já teve não pega de novo")

    def _roll(self) -> str:
        self._clean()
        hits = self.box.pokerus_run(POKERUS_ROLL, ROLLS, timeout=6000)
        assert ROLL_MIN <= hits <= ROLL_MAX, (
            f"{hits} de {ROLLS} sorteios deram Pokérus, esperava ~{ROLLS * 3 // 65536} "
            f"({ROLL_MIN}..{ROLL_MAX})")
        assert self._bytes() == [0] * 6, "o sorteio não devolveu o time como estava"
        return f"{hits} de {ROLLS} sorteios (esperado ~{ROLLS * 3 // 65536}, 3 em 65536)"

    def _spread(self) -> str:
        self._set_all([0x12, 0, 0, 0, 0, 0])
        for tries in range(1, SPREAD_TRIES + 1):
            values = self.box.pokerus_run(POKERUS_SPREAD, 1)
            if values[1]:
                break
        else:
            raise AssertionError(f"{SPREAD_TRIES} chamadas e o vizinho não pegou: {self._hex(values)}")
        assert values[:3] == [0x12, 0x12, 0], (
            f"esperava 12 12 00 (mesma cepa e dias, só o vizinho): {self._hex(values)}")
        self._set_all([0x10, 0, 0, 0, 0, 0])
        values = self.box.pokerus_run(POKERUS_SPREAD, SPREAD_TRIES)
        assert values[1] == 0, f"o curado espalhou: {self._hex(values)}"
        self._set_all([0x13, 0x20, 0, 0, 0, 0])
        values = self.box.pokerus_run(POKERUS_SPREAD, SPREAD_TRIES)
        assert values[1] == 0x20, f"quem já teve pegou de novo: {self._hex(values)}"
        self._clean()
        return (f"o vizinho pegou na {tries}ª chamada (12 12 00); curado não espalha; "
                f"quem já teve (20) não pega de novo")

    def _days_pass(self) -> str:
        self._set_all([0x13, 0, 0, 0, 0, 0])
        got = self.box.set_clock(MIDNIGHT_DAY, BEFORE_MIDNIGHT)
        assert got == BEFORE_MIDNIGHT, f"SET_CLOCK devolveu {got}"
        self.ctl.wait_overworld_idle()
        self.emu.frames(FRAMES_PER_MINUTE // 2)
        before = self._bytes()[0]
        assert before == 0x13, f"perdeu o dia antes da meia-noite: {before:#04x}"
        self.emu.frames(FRAMES_PER_MINUTE * 2)
        after = self._bytes()[0]
        assert after == 0x12, f"depois da meia-noite: {after:#04x}, esperava 0x12"
        self.emu.frames(FRAMES_PER_MINUTE * 3)
        still = self._bytes()[0]
        assert still == 0x12, f"perdeu mais de um dia na mesma noite: {still:#04x}"
        values = self.box.pokerus_run(POKERUS_DAYS, 2)
        assert values[0] == 0x10, f"2 dias depois: {values[0]:#04x}, esperava 0x10 (curado)"
        values = self.box.pokerus_run(POKERUS_DAYS, 1)
        assert values[0] == 0x10, f"o curado mudou: {values[0]:#04x}"
        self._clean()
        return "23:59 → meia-noite: 13 → 12 (uma vez); +2 dias: 10, curado com a cepa 1"

    def _evs(self) -> str:
        species = self._sp(EV_SPECIES)
        got = {}
        for name, value in (("sem", 0), ("infectado", 0x13), ("curado", 0x10)):
            self.box.set_pokerus(0, value)
            got[name] = self.box.pokerus_run(POKERUS_EVS, species)
        assert got["sem"] > 0, got
        assert got["infectado"] == got["curado"] == 2 * got["sem"], got
        self._clean()
        return (f"vencendo {EV_SPECIES.removeprefix('SPECIES_')}: {got['sem']} EV sem, "
                f"{got['infectado']} infectado, {got['curado']} curado")

    def _back_to_field(self) -> None:
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             "volta ao menu START", tries=6, wait=120)
        self.menu.close_start_menu()

    def _screens(self) -> str:
        self._set_all([0x13, 0x10, 0, 0, 0, 0])
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self.ctl.wait_until(lambda: PARTY_CHOOSE_TASK in self._tasks() and not self._fade_active(),
                            1200, "menu de Pokémon")
        self._open_summary(0)
        shots = [self._shot("pokerus_resumo_infectado")]
        self._close_summary("infectado")
        self._open_summary(1)
        shots.append(self._shot("pokerus_resumo_curado"))
        self._close_summary("curado")
        self._back_to_field()
        return "telas: " + ", ".join(shots)

    def _nurse(self, shot: str | None) -> bool:
        """Fala com a enfermeira (SIM para curar) e avança até o campo; True se ela explicou o
        Pokérus. `shot` fotografa a 1ª caixa da explicação."""
        self.emu.write(self.game.syms.addr("gStringVar4"), b"\xff")   # nada velho na caixa
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante da enfermeira")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "início da fala da enfermeira")
        explained, spent = False, 0
        while not self._settled_idle():
            if spent >= NURSE_TIMEOUT:
                raise self.ctl.timeout_error("fala da enfermeira")
            if not explained and EXPLANATION in self._field_message():
                explained = True
                if shot:
                    self.emu.frames(MESSAGE_SETTLE)
                    self._shot(shot)
            self._press(KEY_A)
            spent += TEXT_PERIOD
        return explained

    def _nurse_explains(self) -> str:
        flag = self.consts.flag("FLAG_POKERUS_EXPLAINED")
        assert not self.game.flag(flag), "FLAG_POKERUS_EXPLAINED já ligada no save do captura"
        self._clean()
        self._walk(*NURSE_FRONT)
        assert not self._nurse(None), "explicou o Pokérus sem ninguém infectado"
        assert not self.game.flag(flag), "a flag ligou sem explicação"
        self._set_all([0, 0, 0x13, 0x10, 0, 0])
        assert self._nurse("pokerus_enfermeira"), "não explicou o Pokérus com um infectado no time"
        assert self.game.flag(flag), "FLAG_POKERUS_EXPLAINED não ligou"
        assert self._bytes()[:4] == [0, 0, 0x13, 0x10], f"a cura mexeu no Pokérus: {self._hex(self._bytes())}"
        assert not self._nurse(None), "explicou de novo"
        return ("sem Pokérus só cura; com um infectado explica (pokerus_enfermeira) e liga a flag; "
                "na vez seguinte não explica; a cura não tira o Pokérus")

    def run(self) -> None:
        try:
            self._flow("pokerus: CONTINUAR e time de teste", self._start)
            self.suite.run("pokerus/pega: um por vez, nunca o ovo, dias pela cepa", self._give)
            self.suite.run("pokerus/sorteio: ~3 em 65536 depois da batalha", self._roll)
            self.suite.run("pokerus/contagio: só o vizinho, curado não espalha", self._spread)
            self.suite.run("pokerus/dias: a meia-noite do relógio tira um dia", self._days_pass)
            self.suite.run("pokerus/ev: dobro infectado e curado", self._evs)
            res = self.suite.run("pokerus/telas: resumo do infectado e do curado", self._screens)
            if res.status == "falha":
                raise Abort("pokerus/telas")
            self.suite.run("pokerus/enfermeira: explica uma vez", self._nurse_explains)
        except Abort:
            pass


def run_full_pokerus(ctx: ScenarioContext) -> None:
    PokerusScenario(ctx).run()


if __name__ == "__main__":
    sys.exit("use: python3 -m esteira completo ... --only pokerus")
