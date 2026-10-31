"""Modo completo: categoria físico/especial por golpe (POK-43) e tipo Fada (POK-45), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). Os atalhos
CALC_DAMAGE (0xA0: CalculateBaseDamage com gPlayerParty[0] atacando gPlayerParty[1], sem crítico,
clima, tela nem insígnia; antes de STAB, eficácia e fator aleatório) e TYPE_EFFECTIVENESS (0xA1:
multiplicador x 100 de gTypeEffectiveness) medem o motor; o resto é pelo menu e por uma batalha
de verdade:

- `categoria/soco_de_fogo_fisico`: Machamp nv 50 contra Blissey nv 50 (sem Thick Fat): Soco de
  Fogo == Soco do Trovão (os dois físicos, poder 75) e os dois > Signal Beam (especial, 75): o
  Ataque do Machamp é bem maior que o AtqEsp e a Defesa da Blissey bem menor que a DefEsp;
- `categoria/thick_fat`: Snorlax nv 50 de alvo. O Pokémon do atalho tem personalidade fixa
  (abilityNum 0 = Immunity): primeiro Soco de Fogo == Soco do Trovão; com abilityNum 1 (Thick
  Fat, escrito na RAM com o checksum refeito) o Soco de Fogo cai para ~metade (o Ataque é cortado
  porque o golpe é físico; no Gen 3 o Thick Fat só cortava o AtqEsp);
- `fada/tabela`: Fada → Dragão x2, Dragão → Fada x0, Fada → Aço x0,5, Fantasma e Sombrio → Aço
  x1 (Aço perdeu as resistências), Venenoso → Fada x2;
- `fada/especie`: Gardevoir, Clefairy e Mawile no time (RAM) com os tipos de gSpeciesInfo do
  spec: Psíquico/Fada, Fada, Aço/Fada;
- telas do resumo (test/referencias/COMUM/): INFO do Gardevoir com o ícone FADA
  (`fada_resumo_tipos`), detalhe do Psychic do Gardevoir (`fada_resumo_golpe_especial`), detalhe
  do Moonlight (Fada, estado), do Meteor Mash (físico) e do Moonblast (golpe novo) do Clefairy
  (`fada_resumo_golpe_estado`, `fada_resumo_golpe_fisico`, `fada_golpe_novo`);
- `counter/fogo`: batalha selvagem (atalho START_WILD_BATTLE) com um Machamp que usa Soco de
  Fogo de verdade: o dano que o Counter devolveria fica em gProtectStructs[1].physicalDmg
  (specialDmg continua 0, o do Mirror Coat). Lido a cada passo do turno, porque
  TurnValuesCleanUp zera a estrutura no fim do turno. Último passo: a batalha fica aberta.

O clima (sol no Soco de Fogo) não é medido aqui: o atalho CALC_DAMAGE zera gBattleWeather de
propósito e uma batalha de verdade tem o fator aleatório e o crítico. Ele fica no estático
(`test_fisico_especial.py::test_clima_e_flash_fire_nos_dois_ramos`).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only fisico_fada
Numa janela, em tempo real: `make test-watch CENARIO=fisico_fada`.
"""

import re
import struct
import sys

from ..battle import (ACTION_FIGHT, BATTLE_MON_MOVES, BATTLE_MON_PP, MOVE_FUNC_SUFFIX,
                      BattleDriver)
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_RIGHT, KEY_UP
from ..field_menu import STARTMENU_POKEMON
from ..game import _SUBSTRUCT_ORDER, MON_SECURE, POKEMON_SIZE, SUBSTRUCT_SIZE
from ..hooks import (CMD_START_WILD_BATTLE, PSS_PAGE_INFO, PSS_PAGE_MOVES, PSS_PAGE_MOVES_INFO,
                     Mailbox)
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_summary_evolution import DETAIL_TASK, FLIP_WAIT, SETTLE, SummaryEvolutionScenario

# Telas comparadas com a referência (test/referencias/COMUM/, não dependem do inicial)
SCREEN_POINTS = ("fada_resumo_tipos", "fada_resumo_golpe_fisico", "fada_resumo_golpe_especial",
                 "fada_resumo_golpe_estado", "fada_golpe_novo")

LEVEL = 50
# PokemonSubstruct3 (include/pokemon.h): IVs, isEgg e abilityNum no u32 em +4; abilityNum é o bit 31
SUB_MISC, MISC_IVS_WORD, ABILITY_NUM_BIT = 3, 1, 31
MON_CHECKSUM = 0x1C               # BoxPokemon.checksum (u16): soma dos 24 u16 de `secure` decifrado
SPECIES_INFO_SIZE = 0x1C          # sizeof(struct SpeciesInfo) (agbcc arredonda para 4)
SPECIES_INFO_TYPES = 0x06         # SpeciesInfo.types[2]
# struct ProtectStruct (include/battle.h): 4 bytes de bits, physicalDmg u32, specialDmg u32,
# physicalBattlerId u8, specialBattlerId u8, fieldE u16
PROTECT_SIZE, PROTECT_PHYSICAL, PROTECT_SPECIAL, PROTECT_PHYSICAL_ID = 0x10, 0x04, 0x08, 0x0C
WILD = ("SPECIES_SNORLAX", LEVEL)  # aguenta um Soco de Fogo (até crítico) e é mais lento que o Machamp
FIRE_PUNCH_PP = 15
THICK_FAT_SLACK = 2               # truncamentos de (2L/5+2)*poder*atq/def/50 com o Ataque pela metade

# (tipo do golpe, tipo1, tipo2) -> multiplicador x 100
TYPE_CASES = (
    (("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_DRAGON"), 200),
    (("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_FAIRY"), 0),
    (("TYPE_FAIRY", "TYPE_STEEL", "TYPE_STEEL"), 50),
    (("TYPE_GHOST", "TYPE_STEEL", "TYPE_STEEL"), 100),
    (("TYPE_DARK", "TYPE_STEEL", "TYPE_STEEL"), 100),
    (("TYPE_POISON", "TYPE_FAIRY", "TYPE_FAIRY"), 200),
)
FAIRY_SPECIES = (("SPECIES_GARDEVOIR", ("TYPE_PSYCHIC", "TYPE_FAIRY")),
                 ("SPECIES_CLEFAIRY", ("TYPE_FAIRY", "TYPE_FAIRY")),
                 ("SPECIES_MAWILE", ("TYPE_STEEL", "TYPE_FAIRY")))
CONTROL_SPECIES = (("SPECIES_BULBASAUR", ("TYPE_GRASS", "TYPE_POISON")),   # confere o passo da tabela
                   ("SPECIES_MACHAMP", ("TYPE_FIGHTING", "TYPE_FIGHTING")))
# telas do detalhe do golpe: (slot no time, golpe, tela)
MOVE_SHOTS = ((0, "MOVE_PSYCHIC", "fada_resumo_golpe_especial"),
              (1, "MOVE_MOONLIGHT", "fada_resumo_golpe_estado"),
              (1, "MOVE_METEOR_MASH", "fada_resumo_golpe_fisico"),
              (1, "MOVE_MOONBLAST", "fada_golpe_novo"))


def _defines(rel: str, prefix: str) -> dict[str, int]:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2))
            for m in re.finditer(rf"^#define ({prefix}\w+)\s+(\d+)\b", text, re.M)}


class FisicoFadaScenario(SummaryEvolutionScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.moves = _defines("include/constants/moves.h", "MOVE_")
        self.types = _defines("include/constants/pokemon.h", "TYPE_")

    # --- utilidades ----------------------------------------------------------------
    def _team(self, *species: str) -> None:
        for slot, name in enumerate(species):
            self.box.set_party_mon(slot, self._sp(name), LEVEL)
        got = [m.species for m in self.game.party()[:len(species)]]
        assert got == [self._sp(s) for s in species], f"time montado errado: {got}"

    def _damage(self, move: str) -> int:
        damage = self.box.calc_damage(self.moves[move])
        assert damage > 0, f"{move}: dano {damage}"
        return damage

    def _mon_addr(self, slot: int) -> int:
        return self.game.syms.addr("gPlayerParty") + slot * POKEMON_SIZE

    def _misc_word(self, slot: int) -> tuple[bytearray, list[int], int, int]:
        """(struct crua, `secure` decifrado em u32, chave, índice do u32 dos IVs/abilityNum)."""
        raw = bytearray(self.emu.read(self._mon_addr(slot), POKEMON_SIZE))
        pid, ot = struct.unpack_from("<II", raw, 0)
        key = pid ^ ot
        plain = [w ^ key for w in struct.unpack_from("<12I", raw, MON_SECURE)]
        index = _SUBSTRUCT_ORDER[pid % 24][SUB_MISC] * (SUBSTRUCT_SIZE // 4) + MISC_IVS_WORD
        return raw, plain, key, index

    def _ability_num(self, slot: int) -> int:
        _raw, plain, _key, index = self._misc_word(slot)
        return plain[index] >> ABILITY_NUM_BIT & 1

    def _set_ability_num(self, slot: int, value: int) -> None:
        """Escreve abilityNum no Pokémon do time (só na ROM de teste) e refaz o checksum: sem ele
        o GetMonData marcaria o Pokémon como Ovo Ruim."""
        raw, plain, key, index = self._misc_word(slot)
        plain[index] = plain[index] & ~(1 << ABILITY_NUM_BIT) | value << ABILITY_NUM_BIT
        checksum = sum(struct.unpack("<24H", struct.pack("<12I", *plain))) & 0xFFFF
        struct.pack_into("<H", raw, MON_CHECKSUM, checksum)
        struct.pack_into("<12I", raw, MON_SECURE, *(w ^ key for w in plain))
        self.emu.write(self._mon_addr(slot), bytes(raw))

    def _species_types(self, species: int) -> tuple[int, int]:
        addr = self.game.syms.addr("gSpeciesInfo") + species * SPECIES_INFO_SIZE + SPECIES_INFO_TYPES
        return self.emu.read_u8(addr), self.emu.read_u8(addr + 1)

    def _type_names(self, pair: tuple[int, int]) -> str:
        names = {v: k.removeprefix("TYPE_") for k, v in self.types.items()}
        return "/".join(names.get(t, str(t)) for t in pair)

    def _move_cursor(self) -> int:
        return self.emu.read_u8(self.game.syms.addr("sMoveSelectionCursorPos"))

    def _cursor_to(self, index: int, what: str) -> None:
        """No detalhe do golpe, ↑/↓ até o cursor chegar ao golpe `index` (0-3)."""
        for _ in range(8):
            cur = self._move_cursor()
            if cur == index:
                break
            key = KEY_UP if index < cur else KEY_DOWN
            self.ctl.press_until(key, lambda c=cur: self._move_cursor() != c, f"cursor ({what})",
                                 tries=3, wait=FLIP_WAIT)
            self._wait_summary(f"cursor ({what})", DETAIL_TASK)
        assert self._move_cursor() == index, f"cursor em {self._move_cursor()}, esperava {index} ({what})"

    def _detail_shot(self, slot: int, move: str, shot: str) -> str:
        moves = self.game.party()[slot].moves
        assert self.moves[move] in moves, f"slot {slot} sem {move}: golpes {moves}"
        self._cursor_to(moves.index(self.moves[move]), move)
        self.emu.frames(SETTLE * 2)
        path = self._shot(shot)
        self._pause_to_read()
        return f"{move.removeprefix('MOVE_')} ({path})"

    def _open_detail(self) -> None:
        self.ctl.press_until(KEY_A, lambda: (self._state() or (None,))[0] == PSS_PAGE_MOVES_INFO,
                             "detalhe do golpe", tries=3, wait=FLIP_WAIT)
        self._wait_summary("detalhe do golpe", DETAIL_TASK)

    def _close_detail(self) -> None:
        self.ctl.press_until(KEY_B, lambda: (self._state() or (None,))[0] == PSS_PAGE_MOVES,
                             "volta do detalhe do golpe", tries=3, wait=FLIP_WAIT)
        self._wait_summary("KNOWN MOVES de novo")

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="fisico_fada_continue")
        assert len(self.game.party()) >= 2, "save com menos de 2 Pokémon no time"
        return "CONTINUAR no Centro de Viridian"

    def _fire_punch_physical(self) -> str:
        self._team("SPECIES_MACHAMP", "SPECIES_BLISSEY")
        fire, thunder = self._damage("MOVE_FIRE_PUNCH"), self._damage("MOVE_THUNDER_PUNCH")
        signal = self._damage("MOVE_SIGNAL_BEAM")
        assert fire == thunder, f"Soco de Fogo {fire} != Soco do Trovão {thunder} (os dois físicos, poder 75)"
        assert fire > signal, f"Soco de Fogo {fire} <= Signal Beam {signal} (especial)"
        return f"Machamp → Blissey: Soco de Fogo {fire} = Soco do Trovão {thunder} > Signal Beam {signal}"

    def _thick_fat(self) -> str:
        self._team("SPECIES_MACHAMP", "SPECIES_SNORLAX")
        assert self._ability_num(1) == 0, "Snorlax do atalho não veio com abilityNum 0 (Immunity)"
        fire0, thunder0 = self._damage("MOVE_FIRE_PUNCH"), self._damage("MOVE_THUNDER_PUNCH")
        assert fire0 == thunder0, f"com Immunity: Soco de Fogo {fire0} != Soco do Trovão {thunder0}"
        self._set_ability_num(1, 1)
        mon = self.game.party()[1]
        assert mon.species == self._sp("SPECIES_SNORLAX") and self._ability_num(1) == 1, \
            "abilityNum 1 não pegou (checksum?)"
        fire, thunder = self._damage("MOVE_FIRE_PUNCH"), self._damage("MOVE_THUNDER_PUNCH")
        assert thunder == thunder0, f"Soco do Trovão mudou com o Thick Fat: {thunder0} -> {thunder}"
        # dano = base + 2; com o Ataque pela metade a base cai pela metade (± truncamento)
        assert abs((thunder - 2) - 2 * (fire - 2)) <= THICK_FAT_SLACK, \
            f"Thick Fat: Soco de Fogo {fire}, esperava ~metade do Soco do Trovão {thunder}"
        return (f"Machamp → Snorlax: Immunity: fogo {fire0} = trovão {thunder0}; "
                f"Thick Fat: fogo {fire} ≈ metade do trovão {thunder}")

    def _type_table(self) -> str:
        wrong, seen = [], []
        for (move_type, t1, t2), want in TYPE_CASES:
            got = self.box.type_effectiveness(self.types[move_type], self.types[t1], self.types[t2])
            label = f"{move_type[5:]}→{t1[5:]}" + ("" if t1 == t2 else f"/{t2[5:]}")
            seen.append(f"{label} {got / 100:g}")
            if got != want:
                wrong.append(f"{label}: {got}, esperava {want}")
        assert not wrong, "; ".join(wrong)
        return "; ".join(seen)

    def _fairy_species(self) -> str:
        for name, want in CONTROL_SPECIES:
            got = self._species_types(self._sp(name))
            assert got == tuple(self.types[t] for t in want), \
                f"controle {name}: {self._type_names(got)} (tamanho de SpeciesInfo errado?)"
        self._team(*(name for name, _ in FAIRY_SPECIES))
        party, out = self.game.party(), []
        for slot, (name, want) in enumerate(FAIRY_SPECIES):
            got = self._species_types(party[slot].species)
            assert got == tuple(self.types[t] for t in want), \
                f"{name}: {self._type_names(got)}, esperava {'/'.join(want)}"
            out.append(f"{name.removeprefix('SPECIES_')} {self._type_names(got)}")
        return "; ".join(out)

    def _summary_shots(self) -> str:
        """Time do passo anterior: Gardevoir (0), Clefairy (1), Mawile (2), nível 50."""
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        self._open_summary(0)
        assert self._state()[0] == PSS_PAGE_INFO, "o resumo não abriu na página INFO"
        self.emu.frames(SETTLE)
        shots = [f"INFO do Gardevoir ({self._shot(SCREEN_POINTS[0])})"]
        self._pause_to_read()
        self._flip(KEY_RIGHT, 1, "página SKILLS")
        self._flip(KEY_RIGHT, PSS_PAGE_MOVES, "página KNOWN MOVES")
        slot = 0
        self._open_detail()
        for want_slot, move, shot in MOVE_SHOTS:
            if want_slot != slot:
                self._close_detail()
                self.ctl.press_until(KEY_DOWN, lambda s=want_slot: self._viewed_slot() == s,
                                     f"troca para o slot {want_slot}", tries=3, wait=FLIP_WAIT)
                self._wait_summary("troca de Pokémon terminada")
                assert self._state()[0] == PSS_PAGE_MOVES, "↓ saiu da página KNOWN MOVES"
                slot = want_slot
                self._open_detail()
            shots.append(self._detail_shot(slot, move, shot))
        self._close_detail()
        self._close_summary("fisico_fada")
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             "volta ao menu START", tries=6, wait=120)
        self.menu.close_start_menu()
        return "; ".join(shots)

    def _counter_fire(self) -> str:
        self.box.set_party_mon(0, self._sp("SPECIES_MACHAMP"), LEVEL)
        species, level = WILD
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp(species), level) == 1, "START_WILD_BATTLE"
        d = BattleDriver(self.ctl)
        d.wait_action_menu()
        mons = self.game.syms.addr("gBattleMons")
        fire = self.moves["MOVE_FIRE_PUNCH"]
        self.emu.write(mons + BATTLE_MON_MOVES, struct.pack("<H", fire))
        self.emu.write(mons + BATTLE_MON_PP, bytes([FIRE_PUNCH_PP]))
        protect = self.game.syms.addr("gProtectStructs") + 1 * PROTECT_SIZE   # o selvagem
        seen = {"physical": 0, "special": 0, "attacker": None}

        def watch() -> None:
            physical = self.emu.read_u32(protect + PROTECT_PHYSICAL)
            seen["special"] = max(seen["special"], self.emu.read_u32(protect + PROTECT_SPECIAL))
            if physical > seen["physical"]:
                seen["physical"] = physical
                seen["attacker"] = self.emu.read_u8(protect + PROTECT_PHYSICAL_ID)

        hp_before = d.battler_hp(1)
        d._choose_action(ACTION_FIGHT)
        self.ctl.wait_until(lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX), 300, "menu de golpes")
        d._select_grid("gMoveSelectionCursor", 0, "golpe")
        d._press(KEY_A)
        self.ctl.wait_until(lambda: not d.controller_func().endswith(MOVE_FUNC_SUFFIX), 60,
                            "saída do menu de golpes")
        result = d._advance_until_menu_or_end("turno do Soco de Fogo", 3000, on_step=watch)
        assert seen["physical"] > 0, (f"Soco de Fogo não guardou dano físico para o Counter "
                                      f"(specialDmg {seen['special']}, PS {hp_before} -> {d.battler_hp(1)})")
        assert seen["special"] == 0, f"Soco de Fogo guardou {seen['special']} de dano especial (Mirror Coat)"
        assert seen["attacker"] == 0, f"physicalBattlerId {seen['attacker']}, esperava 0 (o Machamp)"
        return (f"{species.removeprefix('SPECIES_')} nv {level} levou {seen['physical']} de Soco de Fogo: "
                f"gProtectStructs[1].physicalDmg = {seen['physical']}, specialDmg = 0, "
                f"physicalBattlerId = 0 (turno terminou em '{result}')")

    def run(self) -> None:
        try:
            self._flow("fisico_fada: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("categoria/soco_de_fogo_fisico: Soco de Fogo usa o Ataque",
                           self._fire_punch_physical)
            self.suite.run("categoria/thick_fat: Thick Fat corta o Ataque do golpe físico de Fogo",
                           self._thick_fat)
            self.suite.run("fada/tabela: tabela de tipos da Gen 6", self._type_table)
            self._flow("fada/especie: Gardevoir, Clefairy e Mawile com o tipo Fada", self._fairy_species)
            self._flow("fada/telas: resumo com FADA e ícones de categoria", self._summary_shots)
            self._flow("counter/fogo: Soco de Fogo guarda dano físico para o Counter", self._counter_fire)
        except Abort:
            pass


def run_full_fisico_fada(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    FisicoFadaScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only fisico_fada ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "fisico_fada",
                     *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
