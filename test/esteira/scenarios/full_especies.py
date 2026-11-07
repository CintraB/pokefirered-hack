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
- `especies/batalha`: SET_LEAD_LOOK Garchomp shiny e START_WILD_BATTLE Darkrai nv 50. No menu de ação, as
  espécies de gBattleMons são as duas → `especie_batalha_darkrai` (frente do Darkrai e costas shiny do Garchomp).

Golpes e habilidade da Task 5 (cada caso volta ao savestate `golpes_base`, tirado depois do resto, com o aviso das
conquistas em silêncio). As duplas são contra as Gêmeas Eli & Anne (START_TRAINER_BATTLE), com aiSmart forçado a 1
na RAM e sem itens (como `ia/dupla`); o 2º Pokémon do jogador é um Squirtle nv 35 só com Growl:

- `golpes/dark_void_dupla`: Darkrai nv 80 com Dark Void (SET_PARTY_MOVE). Do savestate do menu do 1º turno, até 5
  tentativas com sementes diferentes em gRngValue (precisão 80%: as 5 falham com ~0,6%); passa na 1ª em que os dois
  adversários ficam com STATUS1_SLEEP em gBattleMons → `golpe_dark_void` e savestate `golpes_dormindo`;
- `golpes/bad_dreams_dupla`: de `golpes_dormindo`, os 2 adversários dormindo (sono 5 na RAM): o fim do turno tira
  exatamente max(1, PS máximo / 8) de cada um, com 2 mensagens "… é atormentado pelo pesadelo!";
- `golpes/bad_dreams_aliado`: o Squirtle dormindo (status na RAM) não perde PS; os adversários perdem;
- `golpes/bad_dreams_acordado`: o adversário da direita acordado não perde PS; o da esquerda, dormindo, perde;
- `golpes/bad_dreams_desmaiado`: Darkrai com 1 PS e tempestade de areia permanente (RAM): a areia o derruba no fim do
  turno, antes das habilidades; os adversários dormindo perdem só o 1/16 da areia, sem o Bad Dreams;
- `golpes/dark_void_so_darkrai`: Mewtwo com Dark Void → "Mas falhou!" exatamente 1 vez (o script não roda de novo no
  parceiro; mensagens repetidas não se fundem), ninguém dorme e o PP cai de 10 para 9;
- `golpes/dark_void_usuario_dormindo`: o mesmo Mewtwo com sono 3 (RAM): sem "Mas falhou!", o sono anda para 2 e o
  PP fica 10 (a checagem do usuário roda antes da falha);
- `golpes/dragon_rush`: Garchomp nv 60 com Dragon Rush, Dragon Claw, Earthquake e Crunch (sem repetição) contra um Snorlax selvagem nv 50: o menu de golpes mostra
  "Inv. Dragão" (gMoveNames e tela `golpe_menu_garchomp`) e o golpe sai sem travar (gLastMoves).

Telas em OUT/telas/<ponto>.png, comparadas com test/referencias/COMUM/ (diferença é só aviso).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only especies
Numa janela, em tempo real: `make test-watch CENARIO=especies`.
"""

import struct
import sys

from ..battle import (ACTION_FIGHT, ACTION_FUNC, BATTLE_MON_HP, BATTLE_MON_MOVES, BATTLE_MON_PP, BATTLE_MON_SIZE,
                      MENU_TIMEOUT, MOVE_FUNC_SUFFIX, BattleDriver)
from ..breeding import header_defines
from ..breeding import BATCH, PARENT_FORMAT, PROBES_FORMAT, RECORD_SIZE, Parent, unpack_records
from ..emu import KEY_A, KEY_B, KEY_RIGHT
from ..game import POKEMON_SIZE
from ..field_menu import STARTMENU_POKEMON
from ..hooks import (CMD_BREED_EGGS, CMD_BREED_SETUP, CMD_START_WILD_BATTLE, EVO_MODE_NORMAL, NO_RESULT,
                     PSS_PAGE_EVOLUTION, PSS_PAGE_INFO, PSS_PAGE_IVS, PSS_PAGE_MOVES, PSS_PAGE_SKILLS, Mailbox)
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_breeding import FRAMES_PER_EGG_LIMIT, GENDER_CODE
from .full_ia_chefes import BS_AI_SMART, MON_MAX_HP, MON_STATUS1, PARTY_HP, TWINS
from .full_summary_evolution import PARTY_CHOOSE_TASK, SETTLE, SummaryEvolutionScenario

SCREEN_POINTS = ("especie_resumo_garchomp", "especie_resumo_darkrai", "especie_icones_equipe",
                 "especie_batalha_darkrai", "golpe_dark_void", "golpe_menu_garchomp")
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

# --- golpes e habilidade (Task 5) ---
DARKRAI_LEVEL, PARTNER, PARTNER_LEVEL = 80, "SPECIES_SQUIRTLE", 35
SEEDS = (0x5EED0001, 0x13579BDF, 0x2468ACE0, 0x0BADF00D, 0x7F4A7C15)   # 5 tentativas do Dark Void (80% em cada alvo)
STATUS1_SLEEP_MASK, SLEEP5 = 0x07, 5
B_WEATHER_SANDSTORM = (1 << 3) | (1 << 4)   # TEMPORARY | PERMANENT: sem duração
DRAGON_RUSH_LEVEL, DRAGON_RUSH_WILD = 60, ("SPECIES_SNORLAX", 50)
DRAGON_RUSH_MOVES = ("MOVE_DRAGON_RUSH", "MOVE_DRAGON_CLAW", "MOVE_EARTHQUAKE", "MOVE_CRUNCH")
MOVE_NAME_BYTES = 13                 # MOVE_NAME_LENGTH + 1
BATTLE_STRING_BYTES = 300            # gDisplayedStringBattle[300]
BAD_DREAMS_TEXT = "atormentado pelo pesadelo"
TURN_TIMEOUT = 6000
FOES = (1, 3)                        # posições dos adversários em dupla


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

    # --- batalha (golpes da Task 5) -------------------------------------------------
    def _sym(self, name: str) -> int:
        return self.game.syms.addr(name)

    def _mon(self, battler: int) -> int:
        return self._sym("gBattleMons") + battler * BATTLE_MON_SIZE

    def _hp(self, battler: int) -> int:
        return self.emu.read_u16(self._mon(battler) + BATTLE_MON_HP)

    def _max_hp(self, battler: int) -> int:
        return self.emu.read_u16(self._mon(battler) + MON_MAX_HP)

    def _status1(self, battler: int) -> int:
        return self.emu.read_u32(self._mon(battler) + MON_STATUS1)

    def _set_status1(self, battler: int, status1: int) -> None:
        self.emu.write(self._mon(battler) + MON_STATUS1, struct.pack("<I", status1))

    def _set_hp(self, battler: int, hp: int) -> None:
        """PS em gBattleMons e no time do jogador (batalhador do jogador: 0 ou 2)."""
        self.emu.write(self._mon(battler) + BATTLE_MON_HP, struct.pack("<H", hp))
        slot = self.emu.read_u16(self._sym("gBattlerPartyIndexes") + 2 * battler)
        self.emu.write(self._sym("gPlayerParty") + slot * POKEMON_SIZE + PARTY_HP, struct.pack("<H", hp))

    def _func(self, battler: int) -> str:
        ptr = self.emu.read_u32(self._sym("gBattlerControllerFuncs") + 4 * battler)
        return self.game.syms.name_at(ptr & ~1) or ""

    def _battle_text(self) -> str:
        raw = self.emu.read(self._sym("gDisplayedStringBattle"), BATTLE_STRING_BYTES)
        return self.game.charmap.decode(raw.split(b"\xff")[0])

    def _double_turn(self) -> list[str]:
        """Um turno de dupla: os dois Pokémon do jogador escolhem LUTAR e o golpe 0 (Dark Void e Growl miram os dois
        adversários, sem tela de alvo). Devolve as mensagens de batalha vistas (sem repetição seguida)."""
        for battler in (0, 2):
            self.ctl.wait_until(lambda: self._func(battler) == ACTION_FUNC, TURN_TIMEOUT,
                                f"menu de ação do Pokémon {battler}")
            self.emu.frames(4)
            cursor = self.emu.read_u8(self._sym("gActionSelectionCursor") + battler)
            assert cursor == ACTION_FIGHT, f"cursor de ação do Pokémon {battler} em {cursor}"
            self._press(KEY_A)
            self.ctl.wait_until(lambda: self._func(battler) != ACTION_FUNC, MENU_TIMEOUT,
                                f"saída do menu de ação do Pokémon {battler}")
            self.emu.frames(4)
            if not self._func(battler).endswith(MOVE_FUNC_SUFFIX):
                continue
            cursor = self.emu.read_u8(self._sym("gMoveSelectionCursor") + battler)
            assert cursor == 0, f"cursor de golpe do Pokémon {battler} em {cursor}"
            self._press(KEY_A)
            self.ctl.wait_until(lambda: not self._func(battler).endswith(MOVE_FUNC_SUFFIX), 60,
                                f"saída do menu de golpes do Pokémon {battler}")
        # cada mensagem impressa entra uma vez; a mesma mensagem de novo depois da caixa vazia (FlushMessageBox, a
        # pausa de B_WAIT_TIME_SHORT do "Mas falhou!") conta outra vez: nada de fundir repetições
        seen: list[str] = []
        last = [None]

        def watch() -> None:
            text = self._battle_text()
            if text and text != last[0]:
                seen.append(text)
            last[0] = text
        # sem substituto para um desmaiado, só o outro Pokémon do jogador volta ao menu de ação
        result = self.driver._advance_until_menu_or_end(
            "fim do turno duplo", TURN_TIMEOUT, on_step=watch, stop=lambda: self._func(2) == ACTION_FUNC)
        assert result in ("menu", "stop"), f"a batalha acabou no turno ({result}); mensagens {seen}"
        self.emu.frames(10)
        return seen

    def _double_battle(self, lead: str) -> None:
        """Do savestate `golpes_base`: `lead` nv 80 com Dark Void + Squirtle nv 35 com Growl contra as Gêmeas."""
        self.ctl.restore("golpes_base")
        self.emu.frames(12)
        self.box.set_party_mon(0, self._sp(lead), DARKRAI_LEVEL)
        self.box.set_party_move(0, 0, self.moves["MOVE_DARK_VOID"])
        self.box.set_party_mon(1, self._sp(PARTNER), PARTNER_LEVEL)
        self.box.set_party_move(1, 0, self.moves["MOVE_GROWL"])
        assert self.box.party_size(2) == 2
        self.box.start_trainer_battle(self.consts._eval(TWINS))
        self.driver = BattleDriver(self.ctl)
        self.driver.wait_action_menu(TURN_TIMEOUT)
        self.emu.frames(10)
        assert self.driver.battle_type_flags() & 1, "a batalha das Gêmeas não é dupla"
        self.emu.write(self.emu.read_u32(self._sym("gBattleStruct")) + BS_AI_SMART, b"\x01")   # como em ia/dupla
        assert self.box.ai_smart_state()[0]
        self.box.set_trainer_items()
        assert self.driver.battler_species_level(0) == (self._sp(lead), DARKRAI_LEVEL)

    def _bad_dreams_count(self, seen: list[str]) -> int:
        return sum(BAD_DREAMS_TEXT in t.replace("\n", " ") for t in seen)

    def _dark_void_double(self) -> str:
        self._double_battle("SPECIES_DARKRAI")
        self.ctl.checkpoint("golpes_dark_void_menu")
        tries = []
        for i, seed in enumerate(SEEDS):
            if i:
                self.ctl.restore("golpes_dark_void_menu")
                self.emu.frames(4)
            self.emu.write(self._sym("gRngValue"), struct.pack("<I", seed))
            self._double_turn()
            asleep = [bool(self._status1(b) & STATUS1_SLEEP_MASK) for b in FOES]
            tries.append(asleep)
            if all(asleep):
                path = self._shot("golpe_dark_void")
                self._pause_to_read()
                self.ctl.checkpoint("golpes_dormindo")
                return f"tentativa {i + 1}: os dois adversários dormem (tentativas {tries}; tela {path})"
        raise AssertionError(f"em {len(SEEDS)} tentativas os dois nunca dormiram juntos: {tries}")

    def _from_asleep(self) -> None:
        """Menu do 2º turno com os dois adversários dormindo (sono 5: não acordam neste turno)."""
        self.ctl.restore("golpes_dormindo")
        self.emu.frames(4)
        for b in FOES:
            self._set_status1(b, SLEEP5)

    @staticmethod
    def _eighth(max_hp: int) -> int:
        return max(1, max_hp // 8)

    def _bad_dreams_double(self) -> str:
        self._from_asleep()
        before = {b: (self._hp(b), self._max_hp(b)) for b in FOES}
        seen = self._double_turn()
        got = {b: before[b][0] - self._hp(b) for b in FOES}
        want = {b: self._eighth(before[b][1]) for b in FOES}
        assert got == want, f"PS perdido {got}, esperado {want} (antes {before}); mensagens {seen}"
        assert self._bad_dreams_count(seen) == 2, f"mensagens do Bad Dreams: {seen}"
        return f"cada adversário perdeu max(1, PS/8): {got} (PS máximo {[before[b][1] for b in FOES]})"

    def _bad_dreams_ally(self) -> str:
        self._from_asleep()
        self._set_status1(2, SLEEP5)
        ally = self._hp(2)
        before = {b: self._hp(b) for b in FOES}
        seen = self._double_turn()
        assert self._status1(2) & STATUS1_SLEEP_MASK, "o Squirtle acordou (o teste não vale)"
        assert self._hp(2) == ally, f"o aliado dormindo perdeu PS: {ally} → {self._hp(2)}; mensagens {seen}"
        lost = {b: before[b] - self._hp(b) for b in FOES}
        assert all(v > 0 for v in lost.values()), f"contraprova: os adversários não perderam PS {lost}"
        assert self._bad_dreams_count(seen) == 2, f"mensagens do Bad Dreams: {seen}"
        return f"Squirtle dormindo ficou com {ally} PS; adversários perderam {lost}"

    def _bad_dreams_awake(self) -> str:
        self._from_asleep()
        self._set_status1(3, 0)
        # o Dark Void do turno poria o acordado para dormir de novo: o Darkrai fica sem agir (congelado, sem degelo
        # no turno: o sorteio de 20% é refeito com a semente fixa e conferido abaixo)
        self.emu.write(self._sym("gRngValue"), struct.pack("<I", SEEDS[0]))
        self._set_status1(0, 1 << 5)
        before = {b: self._hp(b) for b in FOES}
        seen = self._double_turn()
        assert self._status1(0) & (1 << 5), f"o Darkrai descongelou e agiu (o teste não vale): {seen}"
        assert not self._status1(3) & STATUS1_SLEEP_MASK, f"o adversário da direita dormiu: {seen}"
        assert self._hp(3) == before[3], f"adversário acordado perdeu PS: {before[3]} → {self._hp(3)}; {seen}"
        assert before[1] - self._hp(1) == self._eighth(self._max_hp(1)), "contraprova: o que dorme não perdeu 1/8"
        assert self._bad_dreams_count(seen) == 1, f"mensagens do Bad Dreams: {seen}"
        return f"acordado: {before[3]} → {self._hp(3)} PS; dormindo: {before[1]} → {self._hp(1)}"

    def _bad_dreams_fainted(self) -> str:
        self._from_asleep()
        self._set_hp(0, 1)
        self.emu.write(self._sym("gBattleWeather"), struct.pack("<H", B_WEATHER_SANDSTORM))
        before = {b: (self._hp(b), self._max_hp(b)) for b in FOES}
        seen = self._double_turn()
        assert self._hp(0) == 0, f"o Darkrai não desmaiou: {self._hp(0)} PS; {seen}"
        got = {b: before[b][0] - self._hp(b) for b in FOES}
        want = {b: max(1, before[b][1] // 16) for b in FOES}
        assert got == want, f"PS perdido {got}, esperado só a areia {want}; {seen}"
        assert self._bad_dreams_count(seen) == 0, f"Bad Dreams depois do desmaio: {seen}"
        return f"Darkrai caiu na areia; adversários perderam só a areia {got}"

    def _dark_void_only_darkrai(self) -> str:
        self._double_battle("SPECIES_MEWTWO")
        pp = lambda: self.emu.read_u8(self._mon(0) + BATTLE_MON_PP)
        assert pp() == 10, f"PP do Dark Void no Mewtwo: {pp()}"
        seen = self._double_turn()
        assert seen.count("Mas falhou!") == 1, f"'Mas falhou!' deve sair exatamente 1 vez: {seen}"
        asleep = [self._status1(b) & STATUS1_SLEEP_MASK for b in FOES]
        assert asleep == [0, 0], f"adversários dormindo: {asleep}"
        assert pp() == 9, f"PP do Dark Void no Mewtwo depois: {pp()}"
        return f"Mewtwo: 'Mas falhou!', ninguém dorme, PP 10 → 9 (mensagens {seen})"

    def _dark_void_user_asleep(self) -> str:
        """O attackcanceler roda antes da falha: o Mewtwo dormindo só dorme (o sono anda, o PP fica)."""
        self._double_battle("SPECIES_MEWTWO")
        self._set_status1(0, 3)
        seen = self._double_turn()
        pp = self.emu.read_u8(self._mon(0) + BATTLE_MON_PP)
        assert "Mas falhou!" not in seen, f"o Mewtwo dormindo agiu: {seen}"
        assert self._status1(0) & STATUS1_SLEEP_MASK == 2, f"o sono não andou: status1 {self._status1(0):#x}"
        assert pp == 10, f"PP do Dark Void caiu dormindo: {pp}"
        return f"Mewtwo dormindo: sono 3 → 2, PP 10, sem 'Mas falhou!' (mensagens {seen})"

    def _dragon_rush(self) -> str:
        self.ctl.restore("golpes_base")
        self.emu.frames(12)
        garchomp, (wild, wild_level) = self._sp("SPECIES_GARCHOMP"), DRAGON_RUSH_WILD
        self.box.set_party_mon(0, garchomp, DRAGON_RUSH_LEVEL)
        # os 4 golpes escritos: no nv 60 o Garchomp já aprendeu o Dragon Rush (nv 55), que sairia repetido no menu
        for i, move in enumerate(DRAGON_RUSH_MOVES):
            self.box.set_party_move(0, i, self.moves[move])
        assert self.box.party_size(1) == 1
        raw = self.emu.read(self._sym("gMoveNames") + self.moves["MOVE_DRAGON_RUSH"] * MOVE_NAME_BYTES,
                            MOVE_NAME_BYTES)
        name = self.game.charmap.decode(raw.split(b"\xff")[0])
        assert name == "Inv. Dragão", f"nome do golpe na ROM: {name!r}"
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp(wild), wild_level) == 1, "START_WILD_BATTLE"
        d = self.driver = BattleDriver(self.ctl)
        d.wait_action_menu(TURN_TIMEOUT)
        assert d.battler_species_level(0) == (garchomp, DRAGON_RUSH_LEVEL)
        moves = list(struct.unpack("<4H", self.emu.read(self._mon(0) + BATTLE_MON_MOVES, 8)))
        assert moves == [self.moves[m] for m in DRAGON_RUSH_MOVES], f"golpes do Garchomp na batalha: {moves}"
        d._choose_action(ACTION_FIGHT)
        in_moves = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        self.emu.frames(SETTLE * 2)
        path = self._shot("golpe_menu_garchomp")
        self._pause_to_read()
        d._select_grid("gMoveSelectionCursor", 0, "golpe")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: not in_moves(), 60, "saída do menu de golpes")
        result = d._advance_until_menu_or_end("fim do turno do Dragon Rush", TURN_TIMEOUT)
        last = self.emu.read_u16(self._sym("gLastMoves"))
        assert last == self.moves["MOVE_DRAGON_RUSH"], f"último golpe do Garchomp: {last}"
        return f"menu com '{name}' (tela {path}); Dragon Rush usado, o turno terminou em '{result}'"

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self.moves = header_defines(REPO_ROOT, "moves.h")
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
        self.box.conq_silencio(True)          # R6: o aviso das conquistas pausaria o campo nos casos golpes/*
        self.ctl.checkpoint("golpes_base")    # campo, antes da batalha: ponto de partida dos casos golpes/*
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
            self.suite.run("especies/batalha: Darkrai selvagem contra o Garchomp shiny", self._battle)
            if self.suite.run("golpes/dark_void_dupla: o Darkrai põe os dois adversários para dormir",
                              self._dark_void_double).status != "falha":
                self.suite.run("golpes/bad_dreams_dupla: o fim do turno tira 1/8 de cada adversário dormindo",
                               self._bad_dreams_double)
                self.suite.run("golpes/bad_dreams_aliado: aliado dormindo não perde PS", self._bad_dreams_ally)
                self.suite.run("golpes/bad_dreams_acordado: adversário acordado não perde PS",
                               self._bad_dreams_awake)
                self.suite.run("golpes/bad_dreams_desmaiado: Darkrai desmaiado no turno não fere ninguém",
                               self._bad_dreams_fainted)
            self.suite.run("golpes/dark_void_so_darkrai: na mão do Mewtwo o Dark Void falha",
                           self._dark_void_only_darkrai)
            self.suite.run("golpes/dark_void_usuario_dormindo: quem não é Darkrai e dorme só dorme",
                           self._dark_void_user_asleep)
            self.suite.run("golpes/dragon_rush: Garchomp com Inv. Dragão no menu, o golpe sai", self._dragon_rush)
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
