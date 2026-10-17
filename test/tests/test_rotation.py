"""Rodízio do inicial entre execuções da esteira (estado num JSON fora do Git)."""

import json

from esteira.rotation import STARTERS, peek_next_starter, record_starter


def test_rotation_cycles_bulbasaur_charmander_squirtle(tmp_path):
    state = str(tmp_path / "estado-esteira.json")
    got = []
    for _ in range(4):
        starter = peek_next_starter(state)
        record_starter(state, starter)
        got.append(starter)
    assert got == ["BULBASAUR", "CHARMANDER", "SQUIRTLE", "BULBASAUR"]
    assert STARTERS == ("BULBASAUR", "CHARMANDER", "SQUIRTLE")


def test_peek_never_writes_so_the_turn_repeats_until_recorded(tmp_path):
    """Execução vermelha só espia: a próxima repete o mesmo inicial."""
    state = tmp_path / "estado-esteira.json"
    assert peek_next_starter(str(state)) == "BULBASAUR"      # arquivo ausente => Bulbasaur
    assert peek_next_starter(str(state)) == "BULBASAUR"
    assert not state.exists()
    record_starter(str(state), "BULBASAUR")
    assert json.loads(state.read_text(encoding="utf-8"))["inicial"] == "BULBASAUR"
    assert peek_next_starter(str(state)) == "CHARMANDER"
    assert peek_next_starter(str(state)) == "CHARMANDER"


def test_rotation_restarts_on_unreadable_state(tmp_path):
    state = tmp_path / "sub" / "estado-esteira.json"   # pasta ainda inexistente
    record_starter(str(state), "SQUIRTLE")
    assert peek_next_starter(str(state)) == "BULBASAUR"
    state.write_text("{lixo", encoding="utf-8")
    assert peek_next_starter(str(state)) == "BULBASAUR"
    state.write_text(json.dumps({"inicial": "MEW"}), encoding="utf-8")
    assert peek_next_starter(str(state)) == "BULBASAUR"
