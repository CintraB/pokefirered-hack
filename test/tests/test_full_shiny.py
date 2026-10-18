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
    sc.game = SimpleNamespace(bag_quantity=lambda item: bag, syms=syms)
    sc.charm = 0x177
    sc.measures = {}
    sc.ctx = SimpleNamespace(part=0, parts=1, seed=0)
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


def test_parte_do_modo_paralelo_semeia_o_rng_e_conta_so_a_fatia():
    """Parte 2 de 6: não confere a bolsa (não andou até o Oak), grava a semente fixa da janela
    dela no gRngValue antes de contar e conta só a fatia dos 200 000; a faixa fica para a soma."""
    from esteira import paralelo
    from esteira.scenarios.full_shiny import SHINY_SAMPLES
    sc = scenario(bag=0)
    sc.ctx = SimpleNamespace(part=1, parts=6, seed=0x1234)
    writes, calls = [], []
    sc.emu = SimpleNamespace(frames=lambda n: 0, write=lambda addr, data: writes.append((addr, data)))
    sc.box = SimpleNamespace(call=lambda *a, **k: calls.append(a) or 7)
    detail = sc._rate(with_charm=True)
    seed = paralelo.part_seed("shiny", 1 * 6 + 1, 0x1234)
    assert writes == [(0x03007590, seed.to_bytes(4, "little"))]
    assert calls[0][1:] == (paralelo.share(SHINY_SAMPLES, 1, 6), 1)
    assert sc._partial == {"shinies": 7, "frames": 0, "bag": 0, "seed": 0x1234}
    assert "parte 2/6" in detail
