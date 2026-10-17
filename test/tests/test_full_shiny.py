"""Partes do cenário de shiny testáveis sem emulador."""

from types import SimpleNamespace

import pytest

from esteira.refs import KEY_POINTS
from esteira.scenarios.full_shiny import ShinyScenario


class Stop(Exception):
    pass


def scenario(bag: int = 0) -> ShinyScenario:
    sc = ShinyScenario.__new__(ShinyScenario)   # sem emulador: só os atributos usados
    syms = SimpleNamespace(addr=lambda name: 0x03007590)
    sc.ctl = SimpleNamespace(emu=None, game=SimpleNamespace(syms=syms))
    sc.game = SimpleNamespace(bag_quantity=lambda item: bag)
    sc.charm = 0x177
    sc.measures = {}
    return sc


def test_shiny_nao_sobrescreve_a_tela_do_save_continue(monkeypatch):
    shots = []

    def title_to_continue(self, what, shot):
        shots.append(shot)
        raise Stop
    monkeypatch.setattr(ShinyScenario, "_title_to_continue", title_to_continue)
    with pytest.raises(Stop):
        scenario()._start()
    assert shots and shots[0] not in KEY_POINTS     # save_continue é do modo rápido


@pytest.mark.parametrize("with_charm, bag", [(True, 0), (False, 1)])
def test_taxa_confere_o_charm_na_bolsa_antes_de_contar(with_charm, bag):
    sc = scenario(bag)
    sc.box = SimpleNamespace(call=lambda *a, **k: pytest.fail("contou sem conferir a bolsa"))
    sc.emu = SimpleNamespace(frames=lambda n: 0)
    with pytest.raises(AssertionError, match="charm na bolsa"):
        sc._rate(with_charm=with_charm)
