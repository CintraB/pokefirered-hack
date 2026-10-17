"""Roteiro rápido A: abertura, nome digitado, inicial em rodízio e batalha do rival.

Só aperta botões e lê memória. Checkpoints: `abertura` (jogador livre no quarto),
`inicial` (inicial recebido, rival já pegou o dele) e `rival` (de volta ao overworld no
laboratório depois da batalha). Os Tasks 6-7 continuam do checkpoint `rival`.

Uso avulso (até o CLI do Task 8 existir), a partir de test/:
    python3 -m esteira.scenarios.quick_opening --starter BULBASAUR --out /tmp/abertura
"""

import argparse
import re
import sys
import time
from statistics import median

from ..battle import BattleDriver
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_START, KEY_UP
from ..naming import NamingScreen
from ..rotation import STARTERS
from . import REPO_ROOT, ScenarioContext, open_context
from .base import SCENE_TIMEOUT, TEXT_PERIOD, Abort, Scenario, print_summary

PLAYER_NAME = "TESTE"
TITLE_TIMEOUT = 6000
INTRO_TIMEOUT = 30000
INSTANT_TEXT_MAX_FRAMES = 2
SCRIPTED_FRAMES_PER_TILE = 16
MIN_SCRIPTED_STEPS = 10     # passos seguidos exigidos no trecho medido da escolta do Oak
STEP_GAP = 32               # intervalo maior que isso separa trechos de caminhada

OAK_INTRO_TASKS = {"Task_OakSpeech_Init", "Task_OakSpeech_WelcomeToTheWorld"}
OAK_FIRST_TEXT_TASK = "Task_OakSpeech_ThisWorld"
GENDER_TASK = "Task_OakSpeech_HandleGenderInput"
RIVAL_NAME_TASK = "Task_OakSpeech_HandleRivalNameInput"
CONFIRM_NAME_TASK = "Task_OakSpeech_HandleConfirmNameInput"
# Estados do printer que esperam botão (include/text.h, src/text.c RenderText):
# RENDER_STATE_WAIT, RENDER_STATE_CLEAR (\p) e RENDER_STATE_SCROLL_START (\n no fim da caixa).
BUTTON_WAIT_STATES = {1, 2, 3}

# Bola de cada inicial na mesa (data/maps/PalletTown_ProfessorOaksLab/map.json:
# LOCALID_BULBASAUR_BALL (8,4), LOCALID_SQUIRTLE_BALL (9,4), LOCALID_CHARMANDER_BALL (10,4));
# o jogador fica embaixo da bola, olhando para cima.
STARTER_BALL_X = {"BULBASAUR": 8, "SQUIRTLE": 9, "CHARMANDER": 10}
BALL_ROW = 4
LAB_EXIT_TRIGGER = (6, 8)   # coord_events em y=8 (x 5..7): rival desafia na saída


def _text_speed_fast() -> int:
    """OPTIONS_TEXT_SPEED_FAST de include/constants/global.h."""
    text = (REPO_ROOT / "include" / "constants" / "global.h").read_text(encoding="utf-8")
    return int(re.search(r"#define\s+OPTIONS_TEXT_SPEED_FAST\s+(\d+)", text).group(1))


class OpeningScenario(Scenario):
    # --- abertura ------------------------------------------------------------------
    def _boot_to_oak_speech(self) -> None:
        self.ctl.wait_until(lambda: "TitleScreen" in self.game.callback2(), TITLE_TIMEOUT,
                            "tela de título")
        spent, i = 0, 0
        while not (OAK_INTRO_TASKS & self._tasks()):
            if spent >= INTRO_TIMEOUT:
                raise self.ctl.timeout_error("início da fala do Oak")
            # START na tela de título, A em NOVO JOGO e nas páginas do guia/Pikachu
            self._press(KEY_START if i % 4 == 0 else KEY_A)
            i += 1
            spent += TEXT_PERIOD

    def _measure_instant_text(self) -> None:
        """Quadros entre a caixa da 1ª fala do Oak aparecer e o texto parar de ser impresso."""
        spent = 0
        while OAK_FIRST_TEXT_TASK not in self._tasks():
            if spent >= SCENE_TIMEOUT:
                raise self.ctl.timeout_error("primeira fala do Oak")
            self.emu.frames(1)
            spent += 1
        self.measures["text_speed_intro"] = self.game.options_text_speed()
        frames = 0
        while (self.game.text_printer_active(0)
               and self.game.text_printer_state(0) not in BUTTON_WAIT_STATES):
            if frames >= 120:
                break
            self.emu.frames(1)
            frames += 1
        self.measures["instant_text_frames"] = frames
        self.emu.frames(2)   # a tela mostra a janela um quadro depois da memória (cópia no VBlank)
        self.measures["oak_first_text_shot"] = self._shot("fala_oak")

    def _intro_to_overworld(self) -> None:
        """Gênero, nome digitado, nome do rival (pré-definido) até o quarto do jogador."""
        naming = NamingScreen(self.ctl)
        spent = 0
        typed = False
        while not self._settled_idle():
            if spent >= INTRO_TIMEOUT:
                raise self.ctl.timeout_error("fim da abertura (quarto do jogador)")
            if naming.is_open():
                if typed:
                    raise self.ctl.timeout_error("tela de nome aberta de novo (nome recusado?)")
                naming.type_text(PLAYER_NAME)
                typed = True
                continue
            tasks = self._tasks()
            if RIVAL_NAME_TASK in tasks:
                self.emu.press(KEY_DOWN, hold=2, release=6)   # 1º nome pré-definido
                self._press(KEY_A)
            elif CONFIRM_NAME_TASK in tasks:
                if typed and "name_shot" not in self.measures:
                    self.measures["name_shot"] = self._shot("nome")   # "Então seu nome é TESTE?"
                self._press(KEY_A)                            # SIM
            elif GENDER_TASK in tasks:
                self._press(KEY_A)                            # MENINO
            else:
                self._press(KEY_A)
            spent += TEXT_PERIOD
        if not typed:
            raise AssertionError("a tela de nome do jogador não apareceu")

    def phase_opening(self) -> None:
        def reach_oak_speech() -> None:
            self._boot_to_oak_speech()
            self._measure_instant_text()

        self._flow("abertura: até a 1ª fala do Oak", reach_oak_speech)
        fast = _text_speed_fast()

        def check_text_speed() -> str:
            intro = self.measures["text_speed_intro"]
            assert intro == fast, f"velocidade na abertura = {intro}, esperava FAST ({fast})"
            return f"velocidade de texto na abertura = {intro} (FAST = {fast})"

        def check_instant_text() -> str:
            n = self.measures["instant_text_frames"]
            assert n <= INSTANT_TEXT_MAX_FRAMES, (
                f"texto levou {n} quadros para parar de imprimir (máx. {INSTANT_TEXT_MAX_FRAMES})")
            return f"1ª fala do Oak impressa em {n} quadro(s) após a caixa aparecer"

        self.suite.run("abertura: velocidade de texto padrão FAST", check_text_speed)
        res = self.suite.run("abertura: texto instantâneo na 1ª fala do Oak", check_instant_text)
        res.images.append(self.measures["oak_first_text_shot"])

        self._flow("abertura: gênero, nome e rival até o quarto", self._intro_to_overworld)

        def check_name() -> str:
            name = self.game.player_name()
            assert name == PLAYER_NAME, f"nome do jogador {name!r}, esperava {PLAYER_NAME!r}"
            speed = self.game.options_text_speed()
            assert speed == fast, f"velocidade de texto no jogo = {speed}, esperava {fast}"
            return f"nome {name!r} digitado no teclado e aceito"

        res = self.suite.run("abertura: nome digitado no teclado", check_name)
        if "name_shot" in self.measures:
            res.images.append(self.measures["name_shot"])
        self._flow("abertura: jogador no quarto",
                   lambda: self._assert_location("MAP_PALLET_TOWN_PLAYERS_HOUSE_2F"))
        self.ctl.checkpoint("abertura")

    # --- Oak leva ao laboratório ---------------------------------------------------
    def _walk_to_oak_trigger(self) -> None:
        nav, consts = self.nav, self.consts
        # escada (10,2) do 2F e tapete (4,8) do 1F, como no smoke test de navegação
        if not nav.walk_to(10, 2):
            raise self.ctl.timeout_error("caminho até a escada do quarto")
        assert nav.go_through_warp() == consts.map("MAP_PALLET_TOWN_PLAYERS_HOUSE_1F")
        if not nav.walk_to(4, 8):
            raise self.ctl.timeout_error("caminho até a porta de casa")
        assert nav.go_through_warp() == consts.map("MAP_PALLET_TOWN")
        if not nav.walk_to(12, 2, run=True):
            raise self.ctl.timeout_error("caminho até a saída norte de Pallet")
        moved = nav.step("up", 1)
        assert moved == 1 and nav.interrupted == "script", (
            f"gatilho do Oak em (12,1) não disparou (andou {moved}, interrupted={nav.interrupted})")

    def _escort_to_lab(self) -> None:
        """Avança as falas e registra (quadro, tile) de cada passo do jogador na escolta."""
        pallet, lab = self.consts.map("MAP_PALLET_TOWN"), self.consts.map("MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB")
        changes: list[int] = []
        last = self.game.player_xy()
        frame, held = 0, False
        try:
            while self.game.location() == pallet:
                if frame >= SCENE_TIMEOUT:
                    raise self.ctl.timeout_error("escolta do Oak até o laboratório")
                want = frame % TEXT_PERIOD < 2
                if want != held:
                    self.emu.keys(KEY_A if want else 0)
                    held = want
                self.emu.frames(1)
                frame += 1
                pos = self.game.player_xy()
                if pos != last and self.ctl.script_active():
                    changes.append(frame)
                last = pos
        finally:
            self.emu.keys(0)
        if self.game.location() != lab:
            raise AssertionError(f"escolta terminou em {self.game.location()}, não no laboratório")
        self.measures["escort_step_frames"] = changes

    def _intro_lab_scene(self) -> None:
        self._finish_script("cena de chegada ao laboratório")
        self._assert_location("MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB")

    def phase_escort(self) -> None:
        self._flow("abertura: caminho até o gatilho do Oak", self._walk_to_oak_trigger)
        self._flow("abertura: escolta do Oak até o laboratório", self._escort_to_lab)

        def check_pace() -> str:
            steps = self.measures["escort_step_frames"]
            intervals = [b - a for a, b in zip(steps, steps[1:])]
            runs, cur = [], []
            for d in intervals:
                if d > STEP_GAP:
                    runs.append(cur)
                    cur = []
                else:
                    cur.append(d)
            runs.append(cur)
            longest = max(runs, key=len)
            assert len(longest) >= MIN_SCRIPTED_STEPS, (
                f"trecho de caminhada da escolta curto demais: {longest} (intervalos {intervals})")
            assert all(d == SCRIPTED_FRAMES_PER_TILE for d in longest), (
                f"passos do script fora de {SCRIPTED_FRAMES_PER_TILE} quadros/tile: {longest}")
            return (f"{len(longest)} passos seguidos a {SCRIPTED_FRAMES_PER_TILE} quadros/tile "
                    f"(mediana geral {median(intervals) if intervals else '-'})")

        self.suite.run("abertura: Oak leva ao laboratório a 16 quadros/tile", check_pace)
        self._flow("abertura: cena do laboratório", self._intro_lab_scene)

    # --- inicial -------------------------------------------------------------------
    def _choose_starter(self) -> None:
        starter = self.ctx.starter
        x = STARTER_BALL_X[starter]
        if not self.nav.walk_to(x, BALL_ROW + 1):
            raise self.ctl.timeout_error(f"caminho até a bola de {starter}")
        self.emu.hold(KEY_UP, 4)                 # vira para a mesa (a bola bloqueia o passo)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante da bola")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "script da bola")

        def answer() -> int:
            if not self.game.party():
                self.measures.setdefault("starter_shot", self._shot("inicial"))
                return KEY_A                         # "Quer o <inicial>?" -> SIM
            return KEY_B                             # "Dar apelido?" -> NÃO
        self._finish_script(f"recebimento do {starter}", yesno=answer)

    def phase_starter(self) -> None:
        self._flow(f"inicial: escolher {self.ctx.starter}", self._choose_starter)

        def check_party() -> str:
            party = self.game.party()
            assert party, "time vazio depois de escolher o inicial"
            want = self.consts.species(self.ctx.starter)
            mon = party[0]
            assert mon.species == want, (
                f"espécie {mon.species}, esperava {self.ctx.starter} ({want})")
            assert mon.level == 5, f"nível {mon.level}, esperava 5"
            return f"{self.ctx.starter} nível {mon.level} no time"

        res = self.suite.run(f"inicial: {self.ctx.starter} nível 5", check_party)
        if "starter_shot" in self.measures:
            res.images.append(self.measures["starter_shot"])
        if res.status == "falha":
            raise Abort("inicial")
        self.ctl.checkpoint("inicial")

    # --- rival ---------------------------------------------------------------------
    def _rival_battle(self) -> str:
        self.nav.walk_to(*LAB_EXIT_TRIGGER)
        if not (self.ctl.script_active() or self.game.in_battle()):
            raise self.ctl.timeout_error("desafio do rival na saída do laboratório")
        driver = BattleDriver(self.ctl)
        driver.wait_battle_start()
        self.ctl.advance_text(lambda: driver.controller_func() == "HandleInputChooseAction",
                              SCENE_TIMEOUT, "menu de ação da batalha do rival")
        self.measures["battle_shot"] = self._shot("batalha_rival")
        outcome = driver.fight_to_end()
        self.measures["rival_outcome"] = outcome
        self._finish_script("volta ao overworld depois do rival")
        return outcome

    def phase_rival(self) -> None:
        def run() -> str:
            outcome = self._rival_battle()
            assert outcome in ("win", "lose"), f"batalha do rival terminou em {outcome!r}"
            assert not self.game.in_battle()
            self._assert_location("MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB")
            return f"rival: {outcome}; overworld livre em {self.game.player_xy()}"

        res = self.suite.run("rival: batalha termina e volta ao overworld", run)
        if "battle_shot" in self.measures:
            res.images.append(self.measures["battle_shot"])
        if res.status == "falha":
            raise Abort("rival")
        self.ctl.checkpoint("rival")

    def run(self) -> None:
        try:
            self.phase_opening()
            self.phase_escort()
            self.phase_starter()
            self.phase_rival()
        except Abort:
            pass


def run_opening(ctx: ScenarioContext) -> None:
    """Roda o roteiro A; cada asserção vira um Result em ctx.suite."""
    if ctx.starter not in STARTERS:
        raise ValueError(f"inicial desconhecido: {ctx.starter!r}")
    OpeningScenario(ctx).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roteiro rápido A (abertura até o rival)")
    parser.add_argument("--starter", required=True, choices=STARTERS)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rom", default=str(REPO_ROOT / "pokefirered_switch.gba"))
    parser.add_argument("--elf", default=str(REPO_ROOT / "pokefirered_switch.elf"))
    args = parser.parse_args(argv)
    start = time.monotonic()
    with open_context(args.rom, args.elf, args.out, args.starter) as ctx:
        run_opening(ctx)
        frames = ctx.emu.frames(0)
    return print_summary(ctx.suite, time.monotonic() - start, frames)


if __name__ == "__main__":
    sys.exit(main())
