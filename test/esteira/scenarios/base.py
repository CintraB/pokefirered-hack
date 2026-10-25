"""Utilidades comuns dos roteiros: botões em ritmo fixo, falas, passos de fluxo e telas."""

from pathlib import Path

from ..emu import KEY_A, KEY_B
from ..result import Suite
from . import ScenarioContext

TEXT_PERIOD = 10            # A segurado 2 quadros + 8 soltos
SETTLE_FRAMES = 30          # overworld tem que ficar livre por tanto tempo seguido
SCENE_TIMEOUT = 6000
YESNO_TASK = "Task_YesNoMenu_HandleInput"
# Pergunta da tela de novidades do Carvalho (data/maps/PalletTown_ProfessorOaksLab/text.inc:
# Text_OakOfferNovidadesFirst e Text_OakOfferNovidades). Os roteiros respondem NÃO.
NOVIDADES_OFFER = "Quer ver as novidades"
FIELD_MESSAGE_BYTES = 400   # a fala expandida fica em gStringVar4 (src/field_message_box.c)


def print_summary(suite: Suite, seconds: float, frames: int) -> int:
    """Resumo dos stubs de linha de comando; devolve o código de saída (1 se houver falha)."""
    for r in suite.results:
        print(f"[{r.status}] {r.name}: {r.detail}")
    print(f"tempo: {seconds:.1f} s, {frames} quadros")
    return 1 if suite.failed() else 0


class Abort(Exception):
    """Um passo de fluxo falhou (já registrado na Suite): o resto do roteiro não roda."""


class Scenario:
    def __init__(self, ctx: ScenarioContext):
        self.ctx = ctx
        self.emu = ctx.emu
        self.game = ctx.game
        self.ctl = ctx.controller
        self.nav = ctx.nav
        self.suite = ctx.suite
        self.consts = ctx.consts
        self.shots = Path(ctx.out_dir) / "telas"
        self.measures: dict[str, object] = {}

    def _press(self, key: int) -> None:
        self.emu.press(key, hold=2, release=TEXT_PERIOD - 2)

    def _tasks(self) -> set[str]:
        return self.game.active_tasks()

    def _shot(self, name: str) -> str:
        self.shots.mkdir(parents=True, exist_ok=True)
        path = str(self.shots / f"{name}.png")
        self.emu.screenshot(path)
        return path

    def _shot_next_frame(self, name: str) -> str:
        """Foto do estado que acabou de ser lido na RAM, sem mudar o ritmo do roteiro.

        O jogo grava rolagem e janelas na RAM durante o quadro e só as copia para os
        registradores no VBlank: se a condição ficou verdadeira justo no último quadro
        emulado, a tela atual ainda é a do quadro anterior (ex.: `gBattle_BG0_Y = 160` do
        menu de ação da batalha). Avança um quadro, fotografa e volta ao savestate, para que
        o resto do roteiro (e o RNG, que avança a cada VBlank) siga igual a sem a foto."""
        self.shots.mkdir(parents=True, exist_ok=True)
        state = str(self.shots / f".{name}.foto.ss")
        self.emu.save_state(state)
        try:
            self.emu.frames(1)
            return self._shot(name)
        finally:
            self.emu.load_state(state)
            Path(state).unlink(missing_ok=True)

    def _flow(self, name: str, fn) -> None:
        """Passo de fluxo: falha (tempo esgotado/asserção) vira Result e interrompe o roteiro."""
        if self.suite.run(name, fn).status == "falha":
            raise Abort(name)

    def _settled_idle(self) -> bool:
        """Overworld livre agora e pelos próximos SETTLE_FRAMES quadros."""
        if not self.ctl.overworld_idle():
            return False
        for _ in range(SETTLE_FRAMES // 2):
            self.emu.frames(2)
            if not self.ctl.overworld_idle():
                return False
        return True

    def _field_message(self) -> str:
        """Fala do campo que está na caixa (o script expande o texto em gStringVar4)."""
        raw = self.emu.read(self.game.syms.addr("gStringVar4"), FIELD_MESSAGE_BYTES)
        return self.game.charmap.decode(raw)

    def _novidades_offer(self) -> bool:
        """O Carvalho está perguntando se o jogador quer ver a tela de novidades."""
        return NOVIDADES_OFFER in self._field_message()

    def _finish_script(self, what: str, timeout: int = SCENE_TIMEOUT, yesno=None) -> None:
        """Avança falas com A até o overworld ficar livre; `yesno()` escolhe a tecla de cada
        pergunta sim/não do script (padrão: A = SIM, menos a oferta das novidades do Carvalho,
        que recebe NÃO e fica contada em measures["novidades_offers"])."""
        spent = 0
        while not self._settled_idle():
            if spent >= timeout:
                raise self.ctl.timeout_error(what)
            if YESNO_TASK in self._tasks():
                if yesno:
                    self._press(yesno())
                elif self._novidades_offer():
                    self.measures["novidades_offers"] = int(self.measures.get("novidades_offers", 0)) + 1
                    self._press(KEY_B)
                else:
                    self._press(KEY_A)
            else:
                self._press(KEY_A)
            spent += TEXT_PERIOD

    def _assert_location(self, map_name: str) -> str:
        loc = self.game.location()
        assert loc == self.consts.map(map_name), f"estou em {loc}, esperava {map_name}"
        return f"{map_name} em {self.game.player_xy()}"
