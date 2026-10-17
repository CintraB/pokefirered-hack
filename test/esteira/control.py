"""Controle do emulador com tempo-limite: toda espera tem teto e, ao estourar, salva
screenshot + savestate em `out_dir` e lança `StepTimeout`."""

import re
from pathlib import Path
from typing import Callable

from .emu import KEY_A, Emulator
from .game import Game
from .result import StepTimeout
from .video import VideoRecorder

__all__ = ["Controller", "StepTimeout"]

# enum de src/script.c: CONTEXT_RUNNING=0, CONTEXT_WAITING=1, CONTEXT_SHUTDOWN=2.
# Overworld livre = contexto global desligado e controles de campo destravados.
CONTEXT_SHUTDOWN = 2
OVERWORLD_CALLBACK = "CB2_Overworld"
POLL_FRAMES = 2          # de quantos em quantos quadros os predicados são reavaliados
TEXT_PRESS_PERIOD = 10   # advance_text: A segurado 2 quadros + 8 soltos


class Controller:
    def __init__(self, emu: Emulator, game: Game, out_dir: str,
                 recorder: VideoRecorder | None = None):
        self.emu = emu
        self.game = game
        if recorder is not None:   # a gravação mora no Emulator: cobre também quem chama emu direto
            emu.recorder = recorder
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._failures = 0

    # --- espera genérica -----------------------------------------------------------
    def timeout_error(self, what: str) -> StepTimeout:
        self._failures += 1
        slug = re.sub(r"[^A-Za-z0-9]+", "-", what).strip("-")[:40] or "passo"
        stem = self.out_dir / f"timeout-{self._failures:02d}-{slug}"
        shot, state = str(stem) + ".png", str(stem) + ".ss"
        self.emu.screenshot(shot)
        self.emu.save_state(state)
        return StepTimeout(what=what, screenshot_path=shot, state_path=state)

    def wait_until(self, pred: Callable[[], bool], timeout: int, what: str) -> int:
        """Avança quadros até `pred()`; devolve os quadros gastos. Estoura => StepTimeout."""
        spent = 0
        while not pred():
            if spent >= timeout:
                raise self.timeout_error(what)
            n = min(POLL_FRAMES, timeout - spent)
            self.emu.frames(n)
            spent += n
        return spent

    def advance_text(self, until: Callable[[], bool], timeout: int,
                     what: str = "fim do texto") -> int:
        """Aperta A em ritmo fixo até `until()`; devolve os quadros gastos."""
        spent = 0
        while not until():
            if spent >= timeout:
                raise self.timeout_error(what)
            self.emu.press(KEY_A, hold=2, release=TEXT_PRESS_PERIOD - 2)
            spent += TEXT_PRESS_PERIOD
        return spent

    def press_until(self, key: int, done: Callable[[], bool], what: str,
                    tries: int = 10, wait: int = 20) -> None:
        """Aperta `key` até `done()`; depois de cada toque espera até `wait` quadros pelo
        efeito antes de repetir (telas em transição ignoram o botão)."""
        for _ in range(tries):
            if done():
                return
            self.emu.press(key, hold=2, release=2)
            for _ in range(wait // 2):
                if done():
                    return
                self.emu.frames(2)
        if not done():
            raise self.timeout_error(what)

    # --- estados do jogo -----------------------------------------------------------
    def script_active(self) -> bool:
        """Há script rodando/pausado ou controles de campo travados (src/script.c)."""
        syms, emu = self.game.syms, self.game.emu
        status = emu.read_u8(syms.addr("sGlobalScriptContextStatus"))
        locked = emu.read_u8(syms.addr("sLockFieldControls"))
        return status != CONTEXT_SHUTDOWN or bool(locked)

    def overworld_idle(self) -> bool:
        return (self.game.callback2() == OVERWORLD_CALLBACK
                and not self.script_active()
                and not self.game.text_printer_active())

    def wait_overworld_idle(self, timeout: int = 600) -> int:
        return self.wait_until(self.overworld_idle, timeout, "overworld livre")

    def _battle_func(self) -> str:
        if not self.game.in_battle():
            return ""
        ptr = self.emu.read_u32(self.game.syms.addr("gBattlerControllerFuncs"))
        return self.game.syms.name_at(ptr & ~1) or ""

    def wait_battle_action(self, timeout: int) -> int:
        return self.wait_until(lambda: self._battle_func() == "HandleInputChooseAction",
                               timeout, "menu de ação da batalha")

    def wait_battle_move(self, timeout: int) -> int:
        return self.wait_until(lambda: self._battle_func() == "HandleInputChooseMove",
                               timeout, "menu de golpes da batalha")

    # --- savestates ----------------------------------------------------------------
    def checkpoint_path(self, name: str) -> Path:
        return self.out_dir / "estados" / f"{name}.ss"

    def checkpoint(self, name: str) -> str:
        """Grava um savestate em out_dir/estados/<name>.ss e devolve o caminho."""
        path = self.checkpoint_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.emu.save_state(str(path))
        return str(path)

    def restore(self, name: str) -> str:
        """Carrega o checkpoint `name` gravado por checkpoint() (soltando todas as teclas)."""
        path = self.checkpoint_path(name)
        if not path.is_file():
            raise FileNotFoundError(f"checkpoint {name!r} não existe: {path}")
        self.emu.load_state(str(path))
        self.emu.keys(0)
        return str(path)
