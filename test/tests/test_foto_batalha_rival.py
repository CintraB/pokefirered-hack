"""Foto `batalha_rival`: tirada no quadro em que o menu de ação já aparece na tela.

O jogo troca o controller para `HandleInputChooseAction` e grava `gBattle_BG0_Y = 160` na RAM
no mesmo quadro (`HandleChooseActionAfterDma3`, src/battle_controller_player.c); o registrador
de rolagem só recebe o valor no VBlank seguinte. Se a esteira percebe o menu exatamente no
quadro da troca (o `advance_text` confere a cada 10 quadros), a tela do emulador ainda é a do
quadro anterior: caixa de mensagem vazia, sem "O que o X fará?" nem o menu. Qual quadro do
ritmo de 10 cai na troca depende das falas antes do menu (com BULBASAUR e CHARMANDER caía
justo no quadro da conferência; com SQUIRTLE, um antes). O teste cobre as 10 fases do ritmo
com um emulador falso cuja tela atrasa um quadro em relação à RAM, e exige também que a foto
não mude o ritmo do resto do roteiro (o RNG avança a cada VBlank)."""

from pathlib import Path

import pytest

from esteira.control import TEXT_PRESS_PERIOD, Controller
from esteira.result import Suite
from esteira.scenarios import ScenarioContext
from esteira.scenarios import quick_opening
from esteira.scenarios.quick_opening import OpeningScenario

MENU = "HandleInputChooseAction"


class FakeEmu:
    """Quadros, savestate e uma tela que mostra a RAM do quadro anterior (cópia no VBlank)."""

    recorder = None

    def __init__(self, menu_at: int):
        self.frame = 0
        self.menu_at = menu_at          # 1º quadro em que a RAM já está no menu de ação

    def ram_menu(self, frame: int) -> bool:
        return frame >= self.menu_at

    def frames(self, n: int) -> int:
        self.frame += max(n, 0)
        return self.frame

    def keys(self, mask: int) -> None:
        pass

    def hold(self, mask: int, n: int) -> None:
        self.frames(n)

    def press(self, mask: int, hold: int = 2, release: int = 2) -> None:
        self.frames(hold + release)

    def screenshot(self, path: str) -> None:
        shown = "menu" if self.ram_menu(self.frame - 1) else "caixa vazia"
        Path(path).write_text(shown, encoding="utf-8")

    def save_state(self, path: str) -> None:
        Path(path).write_text(str(self.frame), encoding="utf-8")

    def load_state(self, path: str) -> None:
        self.frame = int(Path(path).read_text(encoding="utf-8"))


class FakeGame:
    def in_battle(self) -> bool:
        return True


class FakeNav:
    def walk_to(self, x: int, y: int) -> bool:
        return True


class FakeDriver:
    fight_frame: int | None = None

    def __init__(self, ctl):
        self.emu = ctl.emu

    def wait_battle_start(self) -> None:
        pass

    def controller_func(self) -> str:
        return MENU if self.emu.ram_menu(self.emu.frame) else "HandleChooseActionAfterDma3"

    def fight_to_end(self) -> str:
        FakeDriver.fight_frame = self.emu.frame
        return "win"


@pytest.mark.parametrize("phase", range(TEXT_PRESS_PERIOD))
def test_foto_do_rival_mostra_o_menu_em_qualquer_fase(tmp_path, monkeypatch, phase):
    menu_at = 600 + phase
    emu = FakeEmu(menu_at)
    ctl = Controller(emu, FakeGame(), str(tmp_path))
    monkeypatch.setattr(ctl, "script_active", lambda: True)   # desafio do rival em curso
    ctx = ScenarioContext(emu=emu, game=FakeGame(), controller=ctl, nav=FakeNav(),
                          suite=Suite(), consts=None, out_dir=str(tmp_path),
                          starter="BULBASAUR")
    monkeypatch.setattr(quick_opening, "BattleDriver", FakeDriver)
    scenario = OpeningScenario(ctx)
    monkeypatch.setattr(scenario, "_finish_script", lambda *a, **k: None)

    assert scenario._rival_battle() == "win"

    shot = Path(scenario.measures["battle_shot"])
    assert shot.read_text(encoding="utf-8") == "menu", (
        f"menu na RAM no quadro {menu_at}: a foto saiu com a caixa vazia")
    # a foto não pode atrasar o resto do roteiro: a luta começa no quadro em que o menu foi
    # percebido (1ª conferência do advance_text depois da troca), como sem a foto
    checks = range(0, 10 * TEXT_PRESS_PERIOD * 100, TEXT_PRESS_PERIOD)
    seen = next(f for f in checks if f >= menu_at)
    assert FakeDriver.fight_frame == seen
    assert not list(tmp_path.rglob("*.ss")), "savestate temporário da foto ficou para trás"
