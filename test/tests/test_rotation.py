"""Rodízio do inicial entre execuções da esteira (estado num JSON fora do Git)."""

import json

from esteira.rotation import STARTERS, next_starter


def test_rotation_cycles_bulbasaur_charmander_squirtle(tmp_path):
    state = str(tmp_path / "estado-esteira.json")
    got = [next_starter(state) for _ in range(4)]
    assert got == ["BULBASAUR", "CHARMANDER", "SQUIRTLE", "BULBASAUR"]
    assert STARTERS == ("BULBASAUR", "CHARMANDER", "SQUIRTLE")


def test_rotation_persists_last_choice(tmp_path):
    state = tmp_path / "estado-esteira.json"
    assert not state.exists()
    assert next_starter(str(state)) == "BULBASAUR"      # arquivo ausente => Bulbasaur
    assert json.loads(state.read_text(encoding="utf-8"))["inicial"] == "BULBASAUR"
    assert next_starter(str(state)) == "CHARMANDER"
    assert json.loads(state.read_text(encoding="utf-8"))["inicial"] == "CHARMANDER"


def test_rotation_restarts_on_unreadable_state(tmp_path):
    state = tmp_path / "sub" / "estado-esteira.json"   # pasta ainda inexistente
    assert next_starter(str(state)) == "BULBASAUR"
    state.write_text("{lixo", encoding="utf-8")
    assert next_starter(str(state)) == "BULBASAUR"
    state.write_text(json.dumps({"inicial": "MEW"}), encoding="utf-8")
    assert next_starter(str(state)) == "BULBASAUR"
