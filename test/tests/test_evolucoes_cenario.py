"""Partes do cenário `evolucoes` (scenarios/full_evolutions.py) testáveis sem emulador."""

import re
from types import SimpleNamespace

import pytest

from esteira import refs
from esteira.emu import KEY_A, KEY_B
from esteira.evolutions import EVO_SHOTS, OLD_TRADE_ITEMS, RULES, SCREEN_POINTS, SPECIES
from esteira.scenarios import REPO_ROOT
from esteira.scenarios import full_evolutions as fe

EVO_SCENE_C = (REPO_ROOT / "src" / "evolution_scene.c").read_text(encoding="utf-8")
PARTY_MENU_C = (REPO_ROOT / "src" / "party_menu.c").read_text(encoding="utf-8")


def _enum_after(marker: str) -> dict[str, int]:
    """Valores de um `enum {...}` sem inicializadores que vem logo depois de `marker`."""
    body = EVO_SCENE_C[EVO_SCENE_C.index(marker):]
    body = re.search(r"enum\s*\{(.*?)\};", body, re.S).group(1)
    names = [n.strip() for n in re.sub(r"//[^\n]*", "", body).split(",") if n.strip()]
    return {name: value for value, name in enumerate(names)}


def test_estados_da_cena_batem_com_o_fonte():
    evo = _enum_after("// States for the main switch in Task_EvolutionScene")
    move = _enum_after("// States for the switch in EVOSTATE_REPLACE_MOVE")
    assert evo["EVOSTATE_START_MUSIC"] == fe.EVOSTATE_START_MUSIC
    assert evo["EVOSTATE_TRY_LEARN_MOVE"] == fe.EVOSTATE_TRY_LEARN_MOVE
    assert evo["EVOSTATE_REPLACE_MOVE"] == fe.EVOSTATE_REPLACE_MOVE
    assert move["MVSTATE_HANDLE_YES_NO"] == fe.MVSTATE_HANDLE_YES_NO
    assert move["MVSTATE_ASK_CANCEL"] == fe.MVSTATE_ASK_CANCEL
    defines = dict(re.findall(r"#define (t\w+)\s+data\[(\d+)\]", EVO_SCENE_C))
    assert int(defines["tState"]) == fe.EVO_STATE
    assert int(defines["tLearnMoveState"]) == fe.EVO_LEARN_STATE
    assert int(defines["tLearnMoveNoState"]) == fe.EVO_LEARN_NO_STATE
    # a 1ª pergunta ("apagar um golpe?") é a que manda o NÃO para MVSTATE_ASK_CANCEL
    assert "tLearnMoveNoState = MVSTATE_ASK_CANCEL" in EVO_SCENE_C
    assert f"static void {fe.EVO_TASK}(u8 taskId)" in EVO_SCENE_C


def test_perguntas_do_menu_de_pokemon_existem():
    for task in (fe.PARTY_REPLACE_MOVE_YESNO, fe.PARTY_STOP_LEARNING_YESNO):
        assert f"static void {task}(u8 taskId)" in PARTY_MENU_C


def test_telas_da_cena_sao_pontos_comuns_unicos():
    assert len(set(SCREEN_POINTS)) == len(SCREEN_POINTS) == 2 * len(EVO_SHOTS)
    assert {f"evo_{r.slug}" for r in RULES} <= set(EVO_SHOTS)
    assert refs.SHARED_POINTS[:len(SCREEN_POINTS)] == SCREEN_POINTS   # depois vêm as dos Hacks 4-6
    assert len(set(refs.SHARED_POINTS)) == len(refs.SHARED_POINTS)
    assert not set(SCREEN_POINTS) & set(refs.KEY_POINTS)


def test_regras_cobrem_os_11_e_os_itens_antigos():
    assert len(SPECIES) == 11
    assert OLD_TRADE_ITEMS["SPECIES_CLAMPERL"] == ("ITEM_DEEP_SEA_TOOTH", "ITEM_DEEP_SEA_SCALE")
    assert OLD_TRADE_ITEMS["SPECIES_KADABRA"] == ()


# --- cena de evolução com jogo falso -------------------------------------------------------------

class FakeScene:
    """Emulador/jogo falsos: a task da cena com `data` e o printer 0 no estado dado."""

    def __init__(self, data, printer_active=False, printer_state=0):
        self.data = data
        self.presses: list[int] = []
        self.frames_run = 0
        self.shots: list[str] = []
        self.game = SimpleNamespace(task_data=lambda name: self.data,
                                    text_printer_active=lambda w: printer_active,
                                    text_printer_state=lambda w: printer_state)

    def scenario(self) -> fe.EvolutionsScenario:
        sc = fe.EvolutionsScenario.__new__(fe.EvolutionsScenario)
        sc.game = self.game
        sc.emu = SimpleNamespace(press=lambda key, hold, release: self.presses.append(key),
                                 frames=lambda n: setattr(self, "frames_run", self.frames_run + n))
        sc._shot = lambda name: self.shots.append(name) or name
        return sc


def _data(state, learn=0, no_state=0):
    data = [0] * 16
    data[fe.EVO_STATE], data[fe.EVO_LEARN_STATE], data[fe.EVO_LEARN_NO_STATE] = state, learn, no_state
    return data


def test_primeira_pergunta_de_golpe_responde_nao():
    f = FakeScene(_data(fe.EVOSTATE_REPLACE_MOVE, fe.MVSTATE_HANDLE_YES_NO, fe.MVSTATE_ASK_CANCEL))
    info = {"recusas": 0}
    f.scenario()._drive_evolution_scene(info, None)
    assert f.presses == [KEY_B] and info["recusas"] == 1


def test_segunda_pergunta_de_golpe_desiste_com_sim():
    f = FakeScene(_data(fe.EVOSTATE_REPLACE_MOVE, fe.MVSTATE_HANDLE_YES_NO, no_state=5))
    info = {"recusas": 0}
    f.scenario()._drive_evolution_scene(info, None)
    assert f.presses == [KEY_A] and info["recusas"] == 0


@pytest.mark.parametrize("state", range(0, fe.EVOSTATE_TRY_LEARN_MOVE))
def test_animacao_nao_aperta_botao(state):
    """B segurado cancela a evolução; na animação o cenário só deixa os quadros correrem."""
    f = FakeScene(_data(state))
    f.scenario()._drive_evolution_scene({"recusas": 0}, None)
    assert f.presses == [] and f.frames_run > 0


def test_telas_antes_e_depois():
    info = {"recusas": 0}
    before = FakeScene(_data(fe.EVOSTATE_START_MUSIC))
    before.scenario()._drive_evolution_scene(info, "evo_x")
    after = FakeScene(_data(fe.EVOSTATE_TRY_LEARN_MOVE), printer_active=True, printer_state=2)
    after.scenario()._drive_evolution_scene(info, "evo_x")
    assert before.shots == ["evo_x_antes"] and after.shots == ["evo_x_depois"]
    assert after.presses == [KEY_A]          # depois da tela, A fecha o "Parabéns!"
    assert info["scene"] and info["antes"] == "evo_x_antes" and info["depois"] == "evo_x_depois"


# --- consulta do modo troca ------------------------------------------------------------------------

def _trade_scenario(targets):
    sc = fe.EvolutionsScenario.__new__(fe.EvolutionsScenario)
    sc.consts = SimpleNamespace(species=lambda name: hash(name) & 0xFFF or 1,
                                item=lambda name: hash(name) & 0xFF or 1,
                                species_name=lambda sid: "SPECIES_X")
    calls = []

    def evolution_target(species, mode, **kw):
        calls.append((species, mode, kw.get("held_item", 0)))
        return targets(species, kw.get("held_item", 0))
    sc.box = SimpleNamespace(evolution_target=evolution_target)
    return sc, calls


def test_troca_consulta_os_11_com_e_sem_o_item_antigo():
    sc, calls = _trade_scenario(lambda species, item: 0)
    detail = sc._trade_never_evolves()
    expected = sum(1 + len(OLD_TRADE_ITEMS[s]) for s in SPECIES)
    assert len(calls) == expected == 19 and "19 consultas" in detail
    assert {mode for _, mode, _ in calls} == {fe.EVO_MODE_TRADE}


def test_troca_que_ainda_evolui_reprova():
    sc, _ = _trade_scenario(lambda species, item: 208 if item else 0)
    with pytest.raises(AssertionError, match="troca ainda evolui"):
        sc._trade_never_evolves()


def test_continue_do_cenario_nao_sobrescreve_tela_de_referencia(monkeypatch):
    shots = []

    class Stop(Exception):
        pass

    def title_to_continue(self, what, shot):
        shots.append(shot)
        raise Stop
    monkeypatch.setattr(fe.EvolutionsScenario, "_title_to_continue", title_to_continue)
    monkeypatch.setattr(fe, "Mailbox", lambda ctl: None)
    sc = fe.EvolutionsScenario.__new__(fe.EvolutionsScenario)
    sc.ctl = None
    with pytest.raises(Stop):
        sc._start()
    assert shots and shots[0] not in refs.KEY_POINTS + refs.SHARED_POINTS
