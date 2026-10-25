"""Hack 2 (ritmo do jogo) sem emulador: as constantes do C e o espelho do cenário `ritmo`.

Medido no emulador (.superpowers/sdd/hack2-medida/relatorio.md): andar 10 tiles por input 160 -> 110
quadros, correr 80 -> 50; esperas da batalha 64/48/32 -> 43/32/21; barras de PS/PE 1 -> 1,5 passos
por quadro; texto "Rápido" instantâneo. Aqui o que está no código tem que bater com isso.
"""

import re

import pytest

from esteira.scenarios import REPO_ROOT
from esteira.scenarios import full_ritmo as fr
from esteira.scenarios.pace import RUN_FRAMES_PER_TILE, WALK_FRAMES_PER_TILE

MOVEMENT = (REPO_ROOT / "src" / "event_object_movement.c").read_text(encoding="utf-8")
BATTLE_H = (REPO_ROOT / "include" / "constants" / "battle.h").read_text(encoding="utf-8")
BATTLE_INTERFACE = (REPO_ROOT / "src" / "battle_interface.c").read_text(encoding="utf-8")
TEXT_PRINTER = (REPO_ROOT / "src" / "text_printer.c").read_text(encoding="utf-8")


def _step_funcs(name: str) -> list[int]:
    """Pixels por quadro de cada entrada de `static const SpriteStepFunc <name>[]` (StepN = N pixels)."""
    m = re.search(rf"SpriteStepFunc {name}\[\]\s*=\s*\{{([^}}]*)\}}", MOVEMENT)
    assert m, name
    return [int(s) for s in re.findall(r"Step(\d+)", m.group(1))]


def _define(nome: str) -> int:
    m = re.search(rf"^#define\s+{nome}\s+(\d+)", BATTLE_H, re.M)
    assert m, nome
    return int(m.group(1))


# --- andar e correr -------------------------------------------------------------------------

def test_andar_por_input_leva_11_quadros_por_tile():
    steps = _step_funcs("sSpeedPlayerWalkStepFuncs")
    assert len(steps) == 11 and sum(steps) == 16


def test_correr_por_input_leva_5_quadros_por_tile():
    steps = _step_funcs("sSpeedPlayerRunStepFuncs")
    assert len(steps) == 5 and sum(steps) == 16


def test_ritmo_original_dos_npcs_e_do_script_fica():
    """O movimento por script e o dos NPCs continuam 16 (andar) e 8 (correr) quadros por tile."""
    normal, fast1 = _step_funcs("sSpeedNormalStepFuncs"), _step_funcs("sSpeedFast1StepFuncs")
    assert (len(normal), sum(normal)) == (16, 16)
    assert (len(fast1), sum(fast1)) == (8, 16)


def test_so_o_jogador_por_input_usa_os_ritmos_novos():
    assert re.search(r"return objectEvent->isPlayer && !ScriptContext_IsEnabled\(\);", MOVEMENT)
    assert re.search(r"speed == MOVE_SPEED_NORMAL && IsPlayerMovingByInput\(objectEvent\)\)\s*speed = MOVE_SPEED_PLAYER_WALK;",
                     MOVEMENT)
    assert re.search(r"IsPlayerMovingByInput\(objectEvent\) \? MOVE_SPEED_PLAYER_RUN : MOVE_SPEED_FAST_1;", MOVEMENT)


def test_tabelas_de_velocidade_incluem_os_dois_ritmos():
    for speed, funcs in (("MOVE_SPEED_PLAYER_WALK", "sSpeedPlayerWalkStepFuncs"),
                         ("MOVE_SPEED_PLAYER_RUN", "sSpeedPlayerRunStepFuncs")):
        assert re.search(rf"\[{speed}\]\s*=\s*{funcs},", MOVEMENT), speed
        assert re.search(rf"\[{speed}\]\s*=\s*NELEMS\({funcs}\),", MOVEMENT), speed


# --- batalha e texto -----------------------------------------------------------------------

def test_esperas_da_batalha_sao_dois_terços_das_originais():
    assert (_define("B_WAIT_TIME_LONG"), _define("B_WAIT_TIME_MED"), _define("B_WAIT_TIME_SHORT")) == (43, 32, 21)
    for novo, original in ((43, 64), (32, 48), (21, 32)):
        assert abs(novo - original * 2 / 3) < 0.7


def test_barras_andam_dois_passos_em_um_quadro_a_cada_dois():
    assert "u8 steps = (gMain.vblankCounter2 & 1) ? 2 : 1;" in BATTLE_INTERFACE
    assert "for (step = 0; step < steps; step++)" in BATTLE_INTERFACE


def test_texto_rapido_imprime_instantaneo():
    assert re.search(r"textPrinter->textSpeed == 0\s*&& gSaveBlock2Ptr->optionsTextSpeed == OPTIONS_TEXT_SPEED_FAST",
                     TEXT_PRINTER)
    assert "IsInstantTextPrinter(&sTextPrinters[i])" in TEXT_PRINTER


# --- o cenário da esteira ------------------------------------------------------------------

def test_cenario_trava_110_e_50_quadros_em_10_tiles():
    assert fr.TILES == 10
    assert fr.WALK_FRAMES == fr.TILES * WALK_FRAMES_PER_TILE == 110
    assert fr.RUN_FRAMES == fr.TILES * RUN_FRAMES_PER_TILE == 50
    assert fr.TOLERANCE == 2
    assert (fr.ORIGINAL_WALK_FRAMES, fr.ORIGINAL_RUN_FRAMES) == (10 * 16, 10 * 8)


def test_pace_py_espelha_o_c():
    assert WALK_FRAMES_PER_TILE == len(_step_funcs("sSpeedPlayerWalkStepFuncs"))
    assert RUN_FRAMES_PER_TILE == len(_step_funcs("sSpeedPlayerRunStepFuncs"))


def test_linha_do_cenario_cabe_no_mapa():
    """10 tiles andando (11 mudanças de tile) a partir de x=6 ficam em x <= 17, dentro dos 24 de Pallet."""
    import json
    mapa = json.loads((REPO_ROOT / "data" / "maps" / "PalletTown" / "map.json").read_text(encoding="utf-8"))
    assert fr.START[0] + fr.TILES + 1 <= 24 and mapa["id"] == "MAP_PALLET_TOWN"
    for npc in mapa["object_events"]:         # ninguém passeia pela linha 9, entre x=6 e x=17
        if "WANDER" in npc["movement_type"]:
            y0 = npc["y"] - npc["movement_range_y"]
            y1 = npc["y"] + npc["movement_range_y"]
            x0 = npc["x"] - npc["movement_range_x"]
            x1 = npc["x"] + npc["movement_range_x"]
            assert not (y0 <= fr.START[1] <= y1 and x1 >= fr.START[0] and x0 <= fr.START[0] + fr.TILES + 1), npc


@pytest.mark.parametrize("nome", ["ritmo"])
def test_registro_do_cenario(nome):
    import esteira.__main__ as cli
    spec = next(s for s in cli.FULL_SCENARIOS if s.name == nome)
    assert (spec.rom, spec.save_from) == (cli.TEST, "captura")
    assert nome in cli.WATCH_FULL_SCENARIOS
