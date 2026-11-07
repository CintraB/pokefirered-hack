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

Os 4 golpes da Gen 4 que deixaram de ser trocados (Task 12), com o Garchomp nv 70 e Presa Ígnea, Vento Agouro, Trama
Vil e Pulso Negro contra um Golem selvagem nv 50 (mais lento, então o recuo vale; Rocha/Terra, que o fantasma
alcança: o Snorlax, Normal, é imune). Cada caso volta ao savestate
`golpes_novos_acao` (menu de ação do 1º turno). Os efeitos com chance usam até 32 sementes fixas em gRngValue (como o
Dark Void) e passam na 1ª em que o efeito sai:

- `golpes/menu_novos`: gMoveNames dos 4 ids e o menu de golpes com os 4 nomes → `golpe_menu_novos`;
- `golpes/nasty_plot`: o Atq. Esp. do usuário sobe 2 estágios (6 → 8) e o PP cai de 20 para 19;
- `golpes/fire_fang_queima`: o alvo fica com STATUS1_BURN → `golpe_fire_fang` (o menu de ação já com a queimadura);
- `golpes/fire_fang_recua`: "hesitou" na tela e o PP do Golem não cai (a chance de recuar é sorteada em separado da
  de queimar);
- `golpes/ominous_wind_atributos`: os 5 atributos do usuário sobem 1 estágio;
- `golpes/dark_pulse_recua`: "hesitou" e o PP do Golem não cai.

Pokédex dos extras e a regra dos 386 (Task 6; cada caso volta ao savestate `golpes_base`, campo com o time das 4):

- `dex/numeros`: DEX_INFO: Bulbasaur 1/1, Deoxys 386/386, Gible 387/443, Gabite 388/444, Garchomp 389/445, Darkrai
  390/491 (número interno / impresso nas telas) e o Ovo sem número;
- `dex/lista_nacional`: Bulbasaur, Deoxys e os 4 extras vistos e capturados (DEX_MARCAR). A tela da Pokédex mostra a
  contagem com os extras (+4; lida em `sPokedexScreenData`, tela `dex_contagem_extras`), a lista numérica nacional
  tem 390 linhas (as 4 últimas são Gible..Darkrai, vistas e capturadas) e, com o cursor no Darkrai, termina em Deoxys,
  443, 444, 445 e 491 (tela `dex_lista_extras`);
- `dex/pagina_garchomp`: a página do Garchomp (Nº445, categoria) e a página da área ("Área desconhecida"): telas
  `dex_garchomp` e `dex_garchomp_area`;
- `dex/resumo_numero`: o resumo de Gible, Gabite, Garchomp e Darkrai guarda 443, 444, 445 e 491 (dexNumStrBuf);
- `dex/386_sem_extras`: SET_DEX_COMPLETE (os 386 e o Mew) com os 4 extras limpos: HasAllMons e os 151 de Kanto com o
  Mew continuam verdadeiros (DEX_COMPLETA);
- `dex/extras_nao_contam`: com os 4 capturados, a contagem até os 386 não muda e a com extras sobe 4; sem o Pikachu e
  com os 4 extras, HasAllMons é falso; com ele, volta a verdadeiro;
- `dex/extra_antes_da_nacional`: sem a Dex Nacional (flag do pós-Liga desligada), START_WILD_BATTLE Garchomp nv 30 +
  Master Ball: a captura registra na Dex sem travar, o jogo volta ao campo, e o resumo mostra "445" (com
  NATIONAL_DEX_FROM_START = 1 a Pokédex Nacional aparece desde o começo, então não há número escondido; com 0 o resumo
  mostraria "???", como numa espécie de Johto).

Telas em OUT/telas/<ponto>.png, comparadas com test/referencias/COMUM/ (diferença é só aviso).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only especies
Numa janela, em tempo real: `make test-watch CENARIO=especies`.
"""

import re
import struct
import sys

from ..battle import (ACTION_FIGHT, ACTION_FUNC, B_OUTCOME_CAUGHT, BATTLE_MON_HP, BATTLE_MON_MOVES, BATTLE_MON_PP,
                      BATTLE_MON_SIZE, MENU_TIMEOUT, MOVE_FUNC_SUFFIX, NICKNAME_COMMAND, BattleDriver)
from ..breeding import header_defines
from ..breeding import BATCH, PARENT_FORMAT, PROBES_FORMAT, RECORD_SIZE, Parent, unpack_records
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_RIGHT
from ..game import POKEMON_SIZE
from ..field_menu import STARTMENU_POKEDEX, STARTMENU_POKEMON
from ..hooks import (CMD_BREED_EGGS, CMD_BREED_SETUP, CMD_GIVE_ITEM, CMD_SET_DEX_COMPLETE, CMD_START_WILD_BATTLE,
                     EVO_MODE_NORMAL, NO_RESULT,
                     PSS_PAGE_EVOLUTION, PSS_PAGE_INFO, PSS_PAGE_IVS, PSS_PAGE_MOVES, PSS_PAGE_SKILLS, Mailbox)
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_breeding import FRAMES_PER_EGG_LIMIT, GENDER_CODE
from .full_ia_chefes import BS_AI_SMART, MON_MAX_HP, MON_STATUS1, PARTY_HP, TWINS
from .full_national_dex import LIST_TASK, POKEDEX_CB, POKEDEX_TASK, SETTLE_FRAMES, SUMMARY_SCAN
from .quick_route1 import POST_BATTLE_TIMEOUT
from .full_summary_evolution import PARTY_CHOOSE_TASK, SCREEN_TIMEOUT, SETTLE, SummaryEvolutionScenario

SCREEN_POINTS = ("especie_resumo_garchomp", "especie_resumo_darkrai", "especie_icones_equipe",
                 "especie_batalha_darkrai", "golpe_dark_void", "golpe_menu_garchomp",
                 "golpe_menu_novos", "golpe_fire_fang", "dex_lista_extras", "dex_garchomp", "dex_garchomp_area")
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

# --- os 4 golpes da Gen 4 (Task 12) ---
NOVOS_LEVEL, NOVOS_WILD = 70, ("SPECIES_GOLEM", 50)
NOVOS_MOVES = ("MOVE_FIRE_FANG", "MOVE_OMINOUS_WIND", "MOVE_NASTY_PLOT", "MOVE_DARK_PULSE")   # slots 0..3
NOVOS_NOMES = ("Presa Ígnea", "Vento Agouro", "Trama Vil", "Pulso Negro")
SLOT_FIRE_FANG, SLOT_OMINOUS_WIND, SLOT_NASTY_PLOT, SLOT_DARK_PULSE = range(4)
BATTLE_MON_STAT_STAGES = 0x18        # struct BattlePokemon.statStages[8] (s8): PS, Atq, Def, Vel, Atq. Esp., Def. Esp.
STAGE_ATK, STAGE_SPATK, STAGE_SPDEF = 1, 4, 5
STAGE_NEUTRAL = 6
STATUS1_BURN = 0x10
FLINCH_TEXT = "hesitou"
EFFECT_SEEDS = tuple((0x9E3779B9 * (i + 1) ^ 0x5EED1000) & 0xFFFFFFFF for i in range(32))
BATTLE_STRING_BYTES = 300            # gDisplayedStringBattle[300]
BAD_DREAMS_TEXT = "atormentado pelo pesadelo"
TURN_TIMEOUT = 6000
FOES = (1, 3)                        # posições dos adversários em dupla

# --- Pokédex dos extras (Task 6) ---
# (espécie, número nacional interno, número impresso nas telas)
DEX_ROWS = (("SPECIES_BULBASAUR", 1, 1), ("SPECIES_DEOXYS", 386, 386), ("SPECIES_GIBLE", 387, 443),
            ("SPECIES_GABITE", 388, 444), ("SPECIES_GARCHOMP", 389, 445), ("SPECIES_DARKRAI", 390, 491))
EXTRAS_DEX = (387, 388, 389, 390)
# struct PokedexScreenData (src/pokedex_screen.c, ARM de 32 bits): os campos que o cenário lê. Os contadores servem de
# conferência dos deslocamentos: precisam bater com as contagens que o atalho DEX_MARCAR devolve.
PDS_STATE, PDS_ORDER_ID = 0x01, 0x42
PDS_LIST_ITEMS, PDS_ORDERED_COUNT, PDS_DEX_SPECIES, PDS_SEEN_NAT, PDS_OWNED_NAT = 0x44, 0x48, 0x5A, 0x6A, 0x6C
DEX_ORDER_NATIONAL = 5               # DEX_ORDER_NUMERICAL_NATIONAL (include/pokedex_screen.h)
LIST_TASK_NUMERICAL, PAGE_TASK = "Task_DexScreen_NumericalOrder", "Task_DexScreen_ShowMonPage"
LIST_READY_STATE, PAGE_READY_STATE, AREA_READY_STATE = 6, 5, 9
LIST_ITEM_SIZE = 8                   # struct ListMenuItem { const u8 *label; s32 index; }
DEX_LISTED_AT_END = 390              # a lista termina no último visto: o Darkrai (dex interno 390)


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

    # --- os 4 golpes da Gen 4 (Task 12) ---------------------------------------------
    def _novos_restore(self) -> None:
        self.ctl.restore("golpes_novos_acao")
        self.emu.frames(4)

    def _novos_stages(self, battler: int) -> list[int]:
        raw = self.emu.read(self._mon(battler) + BATTLE_MON_STAT_STAGES, 8)
        return [b - 256 if b > 127 else b for b in raw]

    def _novos_pp(self, battler: int, slot: int) -> int:
        return self.emu.read_u8(self._mon(battler) + BATTLE_MON_PP + slot)

    def _novos_turn(self, slot: int, seed: int) -> list[str]:
        """Do menu de ação do savestate `golpes_novos_acao`, com a semente `seed`: LUTAR e o golpe `slot`. Devolve as
        mensagens vistas até o menu do turno seguinte (sem repetição seguida)."""
        self._novos_restore()
        self.emu.write(self._sym("gRngValue"), struct.pack("<I", seed))
        d = self.driver
        d._choose_action(ACTION_FIGHT)
        in_moves = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        d._select_grid("gMoveSelectionCursor", slot, "golpe")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: not in_moves(), 60, "saída do menu de golpes")
        seen: list[str] = []

        def watch() -> None:
            text = self._battle_text()
            if text and (not seen or text != seen[-1]):
                seen.append(text)
        result = d._advance_until_menu_or_end("fim do turno do golpe novo", TURN_TIMEOUT, on_step=watch)
        assert result == "menu", f"a batalha acabou no turno ({result}); mensagens {seen}"
        self.emu.frames(10)
        return seen

    def _novos_ate_sair(self, slot: int, saiu, what: str) -> tuple[str, int]:
        """Roda o golpe `slot` com as sementes de EFFECT_SEEDS até `saiu(mensagens)` valer; devolve (resumo, tentativa)."""
        tentativas = []
        for i, seed in enumerate(EFFECT_SEEDS):
            seen = self._novos_turn(slot, seed)
            ok, detalhe = saiu(seen)
            tentativas.append(detalhe)
            if ok:
                return f"tentativa {i + 1} de {len(EFFECT_SEEDS)}: {detalhe}", i + 1
        raise AssertionError(f"{what}: em {len(EFFECT_SEEDS)} tentativas o efeito nunca saiu: {tentativas}")

    def _novos_menu(self) -> str:
        self.ctl.restore("golpes_base")
        self.emu.frames(12)
        garchomp, (wild, wild_level) = self._sp("SPECIES_GARCHOMP"), NOVOS_WILD
        self.box.set_party_mon(0, garchomp, NOVOS_LEVEL)
        for i, move in enumerate(NOVOS_MOVES):
            self.box.set_party_move(0, i, self.moves[move])
        assert self.box.party_size(1) == 1
        nomes = []
        for move in NOVOS_MOVES:
            raw = self.emu.read(self._sym("gMoveNames") + self.moves[move] * MOVE_NAME_BYTES, MOVE_NAME_BYTES)
            nomes.append(self.game.charmap.decode(raw.split(b"\xff")[0]))
        assert tuple(nomes) == NOVOS_NOMES, f"nomes dos golpes na ROM: {nomes}"
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp(wild), wild_level) == 1, "START_WILD_BATTLE"
        d = self.driver = BattleDriver(self.ctl)
        d.wait_action_menu(TURN_TIMEOUT)
        assert d.battler_species_level(0) == (garchomp, NOVOS_LEVEL)
        assert d.battler_species_level(1) == (self._sp(wild), wild_level)
        self.emu.frames(10)
        self.ctl.checkpoint("golpes_novos_acao")
        moves = list(struct.unpack("<4H", self.emu.read(self._mon(0) + BATTLE_MON_MOVES, 8)))
        assert moves == [self.moves[m] for m in NOVOS_MOVES], f"golpes do Garchomp na batalha: {moves}"
        d._choose_action(ACTION_FIGHT)
        in_moves = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        self.emu.frames(SETTLE * 2)
        path = self._shot("golpe_menu_novos")
        self._pause_to_read()
        return f"menu com {', '.join(nomes)} (tela {path})"

    def _novos_nasty_plot(self) -> str:
        self._novos_restore()
        antes = self._novos_stages(0)
        pp = self._novos_pp(0, SLOT_NASTY_PLOT)
        assert antes[STAGE_SPATK] == STAGE_NEUTRAL and pp == 20, f"estágios de partida: {antes}, PP {pp}"
        seen = self._novos_turn(SLOT_NASTY_PLOT, EFFECT_SEEDS[0])
        depois = self._novos_stages(0)
        assert depois[STAGE_SPATK] == STAGE_NEUTRAL + 2, f"Atq. Esp. depois: {depois} ({seen})"
        assert [depois[i] for i in range(8) if i != STAGE_SPATK] == [antes[i] for i in range(8) if i != STAGE_SPATK], \
            f"outro estágio mexeu: {antes} → {depois}"
        assert self._novos_pp(0, SLOT_NASTY_PLOT) == 19, f"PP: {pp} → {self._novos_pp(0, SLOT_NASTY_PLOT)}"
        return f"Atq. Esp. 6 → {depois[STAGE_SPATK]}, PP 20 → 19; mensagens {seen}"

    def _novos_fire_fang_queima(self) -> str:
        def saiu(seen):
            queimou = bool(self._status1(1) & STATUS1_BURN)
            return queimou, f"queimado={queimou}, hesitou={any(FLINCH_TEXT in t for t in seen)}"
        resumo, _ = self._novos_ate_sair(SLOT_FIRE_FANG, saiu, "Fire Fang queimando")
        assert self._hp(1) < self._max_hp(1), "o Fire Fang não tirou PS"
        path = self._shot("golpe_fire_fang")
        self._pause_to_read()
        return f"{resumo} (tela {path})"

    def _novos_recuo(self, slot: int, what: str) -> str:
        """O golpe `slot` faz o Golem (mais lento) recuar: 'hesitou' na tela e o PP dele não cai."""
        self._novos_restore()
        pp_foe = [self._novos_pp(1, i) for i in range(4)]

        def saiu(seen):
            recuou = any(FLINCH_TEXT in t for t in seen)
            return recuou, f"hesitou={recuou}"
        resumo, _ = self._novos_ate_sair(slot, saiu, what)
        assert [self._novos_pp(1, i) for i in range(4)] == pp_foe, "o Golem recuou mas gastou PP"
        return f"{resumo}; PP do Golem {pp_foe} intacto"

    def _novos_fire_fang_recua(self) -> str:
        resumo = self._novos_recuo(SLOT_FIRE_FANG, "Fire Fang fazendo recuar")
        return resumo + f"; queimado={bool(self._status1(1) & STATUS1_BURN)} (a chance de recuar é independente)"

    def _novos_dark_pulse(self) -> str:
        return self._novos_recuo(SLOT_DARK_PULSE, "Dark Pulse fazendo recuar")

    def _novos_ominous_wind(self) -> str:
        def saiu(seen):
            stages = self._novos_stages(0)
            subiu = all(stages[i] == STAGE_NEUTRAL + 1 for i in range(STAGE_ATK, STAGE_SPDEF + 1))
            return subiu, f"estágios {stages[1:6]}"
        resumo, _ = self._novos_ate_sair(SLOT_OMINOUS_WIND, saiu, "Ominous Wind subindo os atributos")
        return resumo

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

    # --- Pokédex dos extras (Task 6) ------------------------------------------------
    def _dex_restore(self) -> None:
        """Volta ao campo do savestate `golpes_base` (time das 4, sem batalha, Pokédex do save do modo rápido)."""
        self.ctl.restore("golpes_base")
        self.emu.frames(12)

    def _dex_data(self) -> int:
        return self.emu.read_u32(self._sym("sPokedexScreenData"))

    def _dex_u8(self, offset: int) -> int:
        return self.emu.read_u8(self._dex_data() + offset)

    def _dex_u16(self, offset: int) -> int:
        return self.emu.read_u16(self._dex_data() + offset)

    def _dex_u32(self, offset: int) -> int:
        return self.emu.read_u32(self._dex_data() + offset)

    def _dex_main_ready(self) -> bool:
        return (self.game.callback2() == POKEDEX_CB and POKEDEX_TASK in self._tasks()
                and self.game.task_data(LIST_TASK) is not None and not self._fade_active())

    def _dex_task_ready(self, task: str, state: int) -> bool:
        return (self.game.callback2() == POKEDEX_CB and task in self._tasks() and self._dex_u8(PDS_STATE) == state
                and not self._fade_active())

    def _dex_open(self) -> None:
        """START > POKéDEX, até o menu de modos da Pokédex Nacional."""
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEDEX)
        self.ctl.wait_until(self._dex_main_ready, SCREEN_TIMEOUT, "Pokédex pronta")
        self.emu.frames(SETTLE_FRAMES)

    def _dex_open_national_list(self) -> None:
        """Do menu de modos (o cursor começa em "Kanto"): DOWN até "Nacional" e A, até a lista numérica pronta."""
        self._press(KEY_DOWN)
        self.emu.frames(4)
        self._press(KEY_A)
        self.ctl.wait_until(lambda: self._dex_task_ready(LIST_TASK_NUMERICAL, LIST_READY_STATE), SCREEN_TIMEOUT,
                            "lista numérica pronta")
        order = self._dex_u8(PDS_ORDER_ID)
        assert order == DEX_ORDER_NATIONAL, f"a lista aberta é a ordem {order}, esperava a nacional ({DEX_ORDER_NATIONAL})"
        self.emu.frames(SETTLE_FRAMES)

    def _dex_species_on_page(self) -> int:
        return self._dex_u16(PDS_DEX_SPECIES)

    def _dex_wait_page(self, previous: int | None = None) -> None:
        self.ctl.wait_until(lambda: self._dex_task_ready(PAGE_TASK, PAGE_READY_STATE)
                            and (previous is None or self._dex_species_on_page() != previous),
                            SCREEN_TIMEOUT, "página da espécie pronta")
        self.emu.frames(SETTLE_FRAMES)

    def _dex_page_down_to(self, species: int) -> None:
        """Na página de uma espécie: DOWN (próximo visto) até a página de `species`."""
        for _ in range(30):
            if self._dex_species_on_page() == species:
                return
            before = self._dex_species_on_page()
            self._press(KEY_DOWN)
            self._dex_wait_page(before)
        raise AssertionError(f"a página nunca chegou a {self._name(species)} (parou em "
                             f"{self._name(self._dex_species_on_page())})")

    def _dex_back_to_field(self) -> None:
        self.ctl.press_until(KEY_B, lambda: self.game.callback2() == "CB2_Overworld"
                             and self.menu.start_menu_open() and self.menu.accepting_input(),
                             "volta ao menu START (Pokédex)", tries=14, wait=120)
        self.menu.close_start_menu()

    def _dex_mark_for_list(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Bulbasaur (primeiro da lista, para o A abrir uma página), Deoxys e os 4 extras vistos e capturados.
        Devolve (contagens antes de marcar os 4 extras, depois)."""
        for dex in (1, 386):
            self.box.dex_marcar(dex, 2)
        for dex in EXTRAS_DEX:
            self.box.dex_marcar(dex, 0)
        before = self.box.dex_marcar(1, 2)
        for dex in EXTRAS_DEX:
            after = self.box.dex_marcar(dex, 2)
        return before, after

    def _dex_numbers(self) -> str:
        out = []
        for name, internal, shown in DEX_ROWS:
            got = self.box.dex_info(self._sp(name))
            assert got == (internal, shown), f"{name}: DEX_INFO {got}, esperava {(internal, shown)}"
            out.append(f"{name.removeprefix('SPECIES_')} {internal}/{shown}")
        egg = self.box.dex_info(self._sp("SPECIES_EGG"))
        assert egg == (0, 0), f"o Ovo tem entrada na Dex: {egg}"
        return "; ".join(out) + "; Ovo sem número"

    def _dex_list(self) -> str:
        self._dex_restore()
        before, after = self._dex_mark_for_list()
        assert after[0] == before[0], f"os extras mudaram a contagem dos 386: {before} -> {after}"
        assert after[1] == before[1] + len(EXTRAS_DEX), f"a contagem com extras não subiu 4: {before} -> {after}"
        self._dex_open()
        owned, seen = self._dex_u16(PDS_OWNED_NAT), self._dex_u16(PDS_SEEN_NAT)
        assert owned == after[1], f"a tela mostra {owned} capturados, o jogo conta {after[1]} com os extras"
        assert seen >= owned, f"vistos {seen} < capturados {owned}"
        counts_shot = self._shot("dex_contagem_extras")
        self._dex_open_national_list()
        listed = self._dex_u16(PDS_ORDERED_COUNT)
        assert listed == DEX_LISTED_AT_END, f"a lista numérica tem {listed} linhas, esperava {DEX_LISTED_AT_END}"
        items = self._dex_u32(PDS_LIST_ITEMS)
        rows = []
        for dex in (386, *EXTRAS_DEX):
            raw = self.emu.read_u32(items + (dex - 1) * LIST_ITEM_SIZE + 4)
            species = self._sp({386: "SPECIES_DEOXYS", 387: "SPECIES_GIBLE", 388: "SPECIES_GABITE",
                                389: "SPECIES_GARCHOMP", 390: "SPECIES_DARKRAI"}[dex])
            assert raw & 0xFFFF == species, f"linha {dex}: espécie {raw & 0xFFFF}, esperava {species}"
            assert raw >> 16 == 0b11, f"linha {dex}: vista/capturada {raw >> 16:#b}"
            rows.append(f"{dex}={self._name(raw & 0xFFFF)}")
        # a página do 1º visto; DOWN até o Darkrai e B: a lista volta com o cursor no fim
        self._press(KEY_A)
        self._dex_wait_page()
        self._dex_page_down_to(self._sp("SPECIES_DARKRAI"))
        self._press(KEY_B)
        self.ctl.wait_until(lambda: self._dex_task_ready(LIST_TASK_NUMERICAL, LIST_READY_STATE), SCREEN_TIMEOUT,
                            "volta à lista numérica")
        self.emu.frames(SETTLE_FRAMES)
        path = self._shot("dex_lista_extras")
        self._pause_to_read()
        self._dex_back_to_field()
        return (f"capturados 386: {after[0]}, com extras: {after[1]} (a tela mostra {owned}/{seen} vistos; tela "
                f"{counts_shot}); a lista tem {listed} linhas ({', '.join(rows)}); fim da lista na tela {path}")

    def _dex_garchomp_page(self) -> str:
        self._dex_restore()
        self._dex_mark_for_list()
        self._dex_open()
        self._dex_open_national_list()
        self._press(KEY_A)
        self._dex_wait_page()
        self._dex_page_down_to(self._sp("SPECIES_GARCHOMP"))
        page = self._shot("dex_garchomp")
        self._press(KEY_A)       # a página da área: o Garchomp não tem área na natureza
        self.ctl.wait_until(lambda: self._dex_task_ready(PAGE_TASK, AREA_READY_STATE), SCREEN_TIMEOUT,
                            "página da área pronta")
        self.emu.frames(SETTLE_FRAMES)
        area = self._shot("dex_garchomp_area")
        self._pause_to_read()
        self._dex_back_to_field()
        return f"página do Garchomp (tela {page}) e da área (tela {area})"

    def _read_summary_number(self) -> bytes:
        """Os bytes de summary.dexNumStrBuf: procura no pedaço da struct do resumo onde ele fica."""
        base = self.emu.read_u32(self._sym("sMonSummaryScreen"))
        return self.emu.read(base + SUMMARY_SCAN[0], SUMMARY_SCAN[1] - SUMMARY_SCAN[0])

    def _expect_summary_number(self, slot: int, text: str) -> str:
        self._open_summary(slot)
        raw = self._read_summary_number()
        number = self.game.charmap.encode(text) + b"\xff"
        found = [i for i in range(0, len(raw) - 4, 4) if raw[i:i + 4] == number]
        assert found, f"o resumo do slot {slot} não guarda '{text}' (dexNumStrBuf)"
        self._close_summary(f"número {text}")
        return f"slot {slot}: '{text}'"

    def _dex_summary_number(self) -> str:
        self._dex_restore()
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        out = [self._expect_summary_number(slot, f"{shown:03d}")
               for slot, (_name, _internal, shown) in enumerate(DEX_ROWS[2:])]   # Gible, Gabite, Garchomp, Darkrai
        self._back_to_field()
        return "o resumo mostra o número real: " + "; ".join(out)

    def _all_386_with_extras_cleared(self) -> tuple[int, int]:
        """SET_DEX_COMPLETE (os 386 e o Mew) e os 4 extras limpos; devolve as contagens."""
        assert self.box.call(CMD_SET_DEX_COMPLETE) == 1, "SET_DEX_COMPLETE não completou a Dex"
        counts = (0, 0)
        for dex in EXTRAS_DEX:
            counts = self.box.dex_marcar(dex, 0)
        return counts

    def _dex_386_without_extras(self) -> str:
        self._dex_restore()
        counts = self._all_386_with_extras_cleared()
        assert counts[0] == counts[1], f"sobrou algum extra: {counts}"
        todo, kanto, *_ = self.box.dex_completa(0)
        assert todo and kanto, f"os 386 sem os extras: HasAllMons {todo}, Kanto com Mew {kanto}"
        for dex in EXTRAS_DEX:
            assert self.box.dex_completa(dex)[2:] == (False, False), f"extra {dex} ainda na Dex"
        return (f"{counts[0]} capturados (os 386 que a Dex exige: sem Lugia, Ho-Oh, Celebi, Jirachi e Deoxys), extras "
                f"limpos: HasAllMons e os 151 de Kanto verdadeiros")

    def _dex_extras_do_not_count(self) -> str:
        self._dex_restore()
        base = self._all_386_with_extras_cleared()
        after = base
        for dex in EXTRAS_DEX:
            after = self.box.dex_marcar(dex, 2)
        assert after[0] == base[0], f"os extras mudaram a contagem dos 386: {base} -> {after}"
        assert after[1] == base[1] + len(EXTRAS_DEX), f"a contagem com extras não subiu 4: {base} -> {after}"
        assert self.box.dex_completa(0)[0], "HasAllMons caiu com os extras capturados"
        pikachu = 25
        counts = self.box.dex_marcar(pikachu, 0)
        assert not self.box.dex_completa(pikachu)[0], "HasAllMons verdadeiro com os 4 extras e sem o Pikachu"
        assert counts == (after[0] - 1, after[1] - 1), f"contagens sem o Pikachu: {counts}"
        self.box.dex_marcar(pikachu, 2)
        assert self.box.dex_completa(0)[0], "HasAllMons não voltou com o Pikachu"
        return (f"386: {base[0]} -> {after[0]}; com extras: {base[1]} -> {after[1]}; sem o Pikachu e com os 4 extras "
                f"HasAllMons é falso; com ele volta a verdadeiro")

    def _dex_extra_before_national(self) -> str:
        self._dex_restore()
        assert not self.game.flag(self.consts.flag("FLAG_SYS_NATIONAL_DEX")), "a Dex Nacional já estava ligada"
        garchomp = self._sp("SPECIES_GARCHOMP")
        self.box.dex_marcar(389, 0)
        assert self.box.dex_completa(389)[2:] == (False, False), "o Garchomp já estava na Dex"
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1, "GIVE_ITEM Master Ball"
        assert self.box.call(CMD_START_WILD_BATTLE, garchomp, 30) == 1, "START_WILD_BATTLE"
        d = self.driver = BattleDriver(self.ctl)
        d.wait_action_menu()
        assert d.battler_species_level(1) == (garchomp, 30), "o selvagem não é o Garchomp nv 30"
        assert d.throw_ball(master), "a Master Ball não capturou o Garchomp"
        for _ in range(4000):                  # sem apelido (B) e o resto das mensagens (A)
            if d._battle_over():
                break
            d._press(KEY_B if d._script_command() == NICKNAME_COMMAND else KEY_A)
        assert d.outcome() == B_OUTCOME_CAUGHT, f"gBattleOutcome = {d.outcome()}"
        self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)
        caught, seen = self.box.dex_completa(389)[2:]
        assert caught and seen, f"o Garchomp não entrou na Dex: capturado {caught}, visto {seen}"
        party = self.game.party()
        assert len(party) == len(TEAM) + 1 and party[-1].species == garchomp, "o Garchomp não foi para o time"
        # sem a Dex Nacional ligada (flag do pós-Liga): com NATIONAL_DEX_FROM_START as telas já mostram o número
        # (IsNationalPokedexUiEnabled = TRUE sempre); sem ele, o resumo esconde, como numa espécie de Johto
        config = (REPO_ROOT / "include" / "config.h").read_text("utf-8")
        from_start = re.search(r"#define NATIONAL_DEX_FROM_START (\d)", config)
        assert from_start, "NATIONAL_DEX_FROM_START sumiu do config.h"
        shown = "445" if from_start.group(1) == "1" else "???"
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        number = self._expect_summary_number(len(party) - 1, shown)
        self._back_to_field()
        return (f"Garchomp capturado sem a Dex Nacional: registrado (capturado e visto), voltou ao campo, time com "
                f"{len(party)}; resumo {number} (NATIONAL_DEX_FROM_START = {from_start.group(1)})")

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
            if self.suite.run("golpes/menu_novos: Presa Ígnea, Vento Agouro, Trama Vil e Pulso Negro no menu",
                              self._novos_menu).status != "falha":
                self.suite.run("golpes/nasty_plot: Trama Vil sobe o Atq. Esp. em 2", self._novos_nasty_plot)
                self.suite.run("golpes/fire_fang_queima: Presa Ígnea queima o alvo", self._novos_fire_fang_queima)
                self.suite.run("golpes/fire_fang_recua: Presa Ígnea faz o alvo recuar", self._novos_fire_fang_recua)
                self.suite.run("golpes/ominous_wind_atributos: Vento Agouro sobe os 5 atributos",
                               self._novos_ominous_wind)
                self.suite.run("golpes/dark_pulse_recua: Pulso Negro faz o alvo recuar", self._novos_dark_pulse)
            self.suite.run("dex/numeros: o número interno e o impresso das 4 e do Ovo", self._dex_numbers)
            self.suite.run("dex/lista_nacional: a lista termina em Deoxys, 443, 444, 445 e 491 e a contagem sobe 4",
                           self._dex_list)
            self.suite.run("dex/pagina_garchomp: a página e a área do Garchomp", self._dex_garchomp_page)
            self.suite.run("dex/resumo_numero: o resumo mostra 443, 444, 445 e 491", self._dex_summary_number)
            self.suite.run("dex/386_sem_extras: os 386 sem os 4 extras completam a Dex", self._dex_386_without_extras)
            self.suite.run("dex/extras_nao_contam: os 4 extras não entram nos 386 nem salvam a Dex incompleta",
                           self._dex_extras_do_not_count)
            self.suite.run("dex/extra_antes_da_nacional: capturar o Garchomp sem a Dex Nacional registra sem travar",
                           self._dex_extra_before_national)
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
