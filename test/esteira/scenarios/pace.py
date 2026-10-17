"""Cronômetro de passos do jogador movido por input (andar e correr).

Ritmos da hack em src/event_object_movement.c (só para o jogador movido por input; o
movimento por script continua a 16):
- andar: sSpeedPlayerWalkStepFuncs tem 11 entradas -> 11 quadros/tile;
- correr: sSpeedPlayerRunStepFuncs tem 5 entradas -> 5 quadros/tile.
Correr exige FLAG_SYS_B_DASH (src/field_player_avatar.c), que o jogo só liga em Pewter
(data/maps/PewterCity/scripts.inc): o modo rápido mede só o andar; a corrida fica para o
modo completo (Task 11), depois de o roteiro ganhar o tênis de verdade.
"""

from ..emu import KEY_B
from ..nav import DIRECTIONS
from . import ScenarioContext

WALK_FRAMES_PER_TILE = 11
RUN_FRAMES_PER_TILE = 5
PACE_STEPS = 5              # intervalos medidos (steps + 1 mudanças de tile seguidas)
PACE_TIMEOUT = 300


def measure_frames_per_tile(ctx: ScenarioContext, direction: str, run: bool = False,
                            steps: int = PACE_STEPS) -> list[int]:
    """Segura a direção (com B se `run`) e devolve os quadros entre mudanças de tile de
    player_xy(). Precisa de `steps + 1` tiles livres em linha reta, fora de grama alta."""
    ctl, game, emu = ctx.controller, ctx.game, ctx.emu
    ctl.wait_overworld_idle()
    mask = DIRECTIONS[direction][2] | (KEY_B if run else 0)
    last = game.player_xy()
    changes: list[int] = []
    frame = 0
    emu.keys(mask)
    try:
        while len(changes) < steps + 1:
            if frame >= PACE_TIMEOUT:
                raise ctl.timeout_error(f"passos {direction} para o cronômetro")
            emu.frames(1)
            frame += 1
            if ctl.script_active() or game.in_battle():
                raise AssertionError("script/batalha durante a medição dos passos")
            pos = game.player_xy()
            if pos != last:
                changes.append(frame)
                last = pos
    finally:
        emu.keys(0)
    ctl.wait_until(ctx.nav._player_still, 60, "fim do passo medido")
    return [b - a for a, b in zip(changes, changes[1:])]


def measure_run_frames_per_tile(ctx: ScenarioContext, direction: str,
                                steps: int = PACE_STEPS) -> list[int]:
    """Mede a corrida (B segurado); exige o tênis de corrida (FLAG_SYS_B_DASH ligada)."""
    if not ctx.game.flag(ctx.consts.flag("FLAG_SYS_B_DASH")):
        raise AssertionError("FLAG_SYS_B_DASH desligada: sem o tênis de corrida, B não corre")
    return measure_frames_per_tile(ctx, direction, run=True, steps=steps)
