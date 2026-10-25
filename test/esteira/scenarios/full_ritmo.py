"""Modo completo: ritmo do jogo (Hack 2) medido em quadros, na build de teste.

O jogador movido por input anda a 11 quadros por tile e corre a 5 (o jogo original: 16 e 8); o
movimento por script mantém o ritmo original (o roteiro `abertura` já confere os 16 quadros/tile da
escolta do Oak). Este cenário trava os números do input:

1. CONTINUAR com o .sav do `captura`, warp para a linha 9 de Pallet Town (x 6..17, livre e fora da
   área de passeio da Mulher, x 2-4) e o Tênis de Corrida ligado pelo atalho SET_FLAG (o jogo só o
   dá em Pewter);
2. andar 10 tiles por input (→, 11 mudanças de tile seguidas): soma dos 10 intervalos em 110 ± 2
   quadros (original: 160);
3. correr 10 tiles por input (← com B): soma em 50 ± 2 quadros (original: 80).

As medidas da comparação com o jogo original (batalha, barras de PS/PE, texto) estão em
.superpowers/sdd/hack2-medida/relatorio.md; aqui só o que é estável e barato de medir.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only ritmo
Numa janela, em tempo real: `make test-watch CENARIO=ritmo`.
"""

import sys

from ..hooks import CMD_WARP, Mailbox
from . import ScenarioContext
from .base import Abort
from .pace import measure_frames_per_tile
from .quick_catch_save import CatchSaveScenario

MAP = "MAP_PALLET_TOWN"
START = (6, 9)                 # x 6..17 da linha 9 livres
TILES = 10
WALK_FRAMES = 110              # 10 tiles x 11 quadros (original: 160)
RUN_FRAMES = 50                # 10 tiles x 5 quadros (original: 80)
TOLERANCE = 2
ORIGINAL_WALK_FRAMES, ORIGINAL_RUN_FRAMES = 160, 80


class PaceScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None

    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="ritmo_continue")
        group, num = self.consts.map(MAP)
        self.box.call(CMD_WARP, group | num << 8, START[0] | START[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para Pallet Town")
        self.ctl.wait_overworld_idle(600)
        self.emu.frames(30)
        assert self.game.player_xy() == START, self.game.player_xy()
        flag = self.consts.flag("FLAG_SYS_B_DASH")
        self.box.set_flag(flag, True)
        assert self.game.flag(flag), "o Tênis de Corrida não ligou"
        return f"Pallet Town em {START}, Tênis de Corrida ligado"

    def _walk(self) -> str:
        steps = measure_frames_per_tile(self.ctx, "right", steps=TILES)
        total = sum(steps)
        assert len(steps) == TILES and abs(total - WALK_FRAMES) <= TOLERANCE, (
            f"andar {TILES} tiles por input: {total} quadros {steps} (esperado {WALK_FRAMES} ± {TOLERANCE})")
        self.measures["walk"] = total
        return (f"{TILES} tiles em {total} quadros {steps} "
                f"(original {ORIGINAL_WALK_FRAMES}: {100 * (1 - total / ORIGINAL_WALK_FRAMES):.0f}% menos)")

    def _run(self) -> str:
        steps = measure_frames_per_tile(self.ctx, "left", run=True, steps=TILES)
        total = sum(steps)
        assert len(steps) == TILES and abs(total - RUN_FRAMES) <= TOLERANCE, (
            f"correr {TILES} tiles por input: {total} quadros {steps} (esperado {RUN_FRAMES} ± {TOLERANCE})")
        self.measures["run"] = total
        return (f"{TILES} tiles em {total} quadros {steps} "
                f"(original {ORIGINAL_RUN_FRAMES}: {100 * (1 - total / ORIGINAL_RUN_FRAMES):.0f}% menos)")

    def run(self) -> None:
        try:
            self._flow("ritmo: CONTINUAR, warp para Pallet Town e Tênis de Corrida", self._start)
            self.suite.run(f"ritmo/andar: {TILES} tiles por input em {WALK_FRAMES} ± {TOLERANCE} quadros", self._walk)
            self.suite.run(f"ritmo/correr: {TILES} tiles por input em {RUN_FRAMES} ± {TOLERANCE} quadros", self._run)
        except Abort:
            pass


def run_full_pace(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    PaceScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only ritmo ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "ritmo", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
