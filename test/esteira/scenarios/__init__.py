"""Cenários da esteira e o contexto que eles compartilham.

Todo cenário recebe um `ScenarioContext` (`ctx`) e só aperta botões e lê memória.
"""

import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..charmap import Charmap
from ..constants import Constants
from ..control import Controller
from ..emu import Emulator
from ..game import Game
from ..nav import Navigator
from ..result import Suite
from ..symbols import Symbols
from ..video import VideoRecorder

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class ScenarioContext:
    emu: Emulator
    game: Game
    controller: Controller
    nav: Navigator
    suite: Suite
    consts: Constants
    out_dir: str
    starter: str   # "BULBASAUR" | "CHARMANDER" | "SQUIRTLE"
    # cenário dividido em partes no modo paralelo (esteira/paralelo.py): esta é a parte `part`
    # de `parts`; 0 de 1 = o cenário inteiro, como no modo sequencial
    part: int = 0
    parts: int = 1
    seed: int = 0   # sal das sementes das partes nesta execução (paralelo.run_salt)


@contextmanager
def open_context(rom: str, elf: str, out_dir: str, starter: str,
                 suite: Suite | None = None,
                 save_from: str | None = None,
                 recorder: VideoRecorder | None = None,
                 window: bool = False) -> Iterator[ScenarioContext]:
    """Liga o emulador com um .sav novo dentro de `out_dir` (nunca em roms/saves/); com
    `save_from`, o .sav começa como cópia desse arquivo (ex.: o save do modo rápido). Se
    `save_from` já é o próprio OUT/esteira.sav, ele é usado como está (nunca apagado antes da
    cópia); se não existe, FileNotFoundError sem tocar no .sav da pasta. `recorder`: grava a
    sessão inteira no vídeo (ver Emulator). `window`: janela em tempo real (modo assistir)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    save = out / "esteira.sav"
    if save_from is None:
        save.unlink(missing_ok=True)
    elif Path(save_from).resolve() != save.resolve():
        shutil.copyfile(save_from, save)   # abre a origem antes de truncar o destino
    consts = Constants.load(str(REPO_ROOT))
    with Emulator(rom, str(save), recorder=recorder, window=window) as emu:
        game = Game(emu, Symbols.from_elf(elf), consts, Charmap.load(str(REPO_ROOT)))
        controller = Controller(emu, game, str(out))
        yield ScenarioContext(emu=emu, game=game, controller=controller,
                              nav=Navigator(controller), suite=suite or Suite(),
                              consts=consts, out_dir=str(out), starter=starter)
