"""POK-43 sem emulador: categoria (físico/especial/estado) por golpe, igual à Gen 6.

Confere o snapshot tools/gen6/gen6.json (gerado da PokéAPI por tools/gen6/gerar.py) e se cada
entrada de src/data/battle_moves.h traz a categoria do snapshot.
"""

import json
import re

from esteira.scenarios import REPO_ROOT

GEN6 = json.loads((REPO_ROOT / "tools" / "gen6" / "gen6.json").read_text(encoding="utf-8"))
BATTLE_MOVES = (REPO_ROOT / "src" / "data" / "battle_moves.h").read_text(encoding="utf-8")
POKEMON_H = (REPO_ROOT / "include" / "pokemon.h").read_text(encoding="utf-8")
CATEGORIAS = {"PHYSICAL", "SPECIAL", "STATUS"}


def _entradas() -> dict[str, str]:
    """MOVE_X -> corpo da entrada `[MOVE_X] = { ... }` de battle_moves.h."""
    return {m.group(1): m.group(2)
            for m in re.finditer(r"^    \[(MOVE_\w+)\] =\s*\{(.*?)^    \},", BATTLE_MOVES, re.M | re.S)}


def test_snapshot_completo():
    cats = GEN6["categories"]
    assert len(cats) == 360
    assert [c for c in cats.values() if c not in CATEGORIAS] == []
    esperado = {
        "MOVE_FIRE_PUNCH": "PHYSICAL", "MOVE_CRUNCH": "PHYSICAL", "MOVE_SHADOW_BALL": "SPECIAL",
        "MOVE_HIDDEN_POWER": "SPECIAL", "MOVE_WEATHER_BALL": "SPECIAL",
        "MOVE_STRUGGLE": "PHYSICAL", "MOVE_BEAT_UP": "PHYSICAL",
        "MOVE_SEISMIC_TOSS": "PHYSICAL", "MOVE_NIGHT_SHADE": "SPECIAL", "MOVE_GROWL": "STATUS",
    }
    assert {k: cats[k] for k in esperado} == esperado


def test_categoria_de_cada_golpe():
    entradas = _entradas()
    assert len(entradas) == 355
    errados = {}
    for nome, corpo in entradas.items():
        if nome == "MOVE_NONE":
            continue
        achado = re.findall(r"\.category = (MOVE_CATEGORY_\w+),", corpo)
        esperado = f"MOVE_CATEGORY_{GEN6['categories'][nome]}"
        if achado != [esperado]:
            errados[nome] = (achado, esperado)
    assert errados == {}


def test_struct_tem_category_no_fim():
    corpo = re.search(r"struct BattleMove\s*\{(.*?)\};", POKEMON_H, re.S).group(1)
    campos = [linha.strip() for linha in corpo.splitlines() if linha.strip()]
    assert campos[-1] == "u8 category;"
