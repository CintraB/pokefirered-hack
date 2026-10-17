"""Cenários da esteira e o contexto que eles compartilham.

Todo cenário recebe um `ScenarioContext` (`ctx`) e só aperta botões e lê memória.
"""

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


@contextmanager
def open_context(rom: str, elf: str, out_dir: str, starter: str,
                 suite: Suite | None = None) -> Iterator[ScenarioContext]:
    """Liga o emulador com um .sav novo dentro de `out_dir` (nunca em roms/saves/)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    save = out / "esteira.sav"
    if save.exists():
        save.unlink()
    consts = Constants.load(str(REPO_ROOT))
    with Emulator(rom, str(save)) as emu:
        game = Game(emu, Symbols.from_elf(elf), consts, Charmap.load(str(REPO_ROOT)))
        controller = Controller(emu, game, str(out))
        yield ScenarioContext(emu=emu, game=game, controller=controller,
                              nav=Navigator(controller), suite=suite or Suite(),
                              consts=consts, out_dir=str(out), starter=starter)
