"""Inicial em rodízio entre execuções: Bulbasaur -> Charmander -> Squirtle -> Bulbasaur...

O estado fica num JSON fora do Git (em produção, roms/estado-esteira.json; testes usam
um caminho temporário).
"""

import json
import os
from pathlib import Path

STARTERS = ("BULBASAUR", "CHARMANDER", "SQUIRTLE")
STATE_KEY = "inicial"


def _last_starter(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    last = data.get(STATE_KEY) if isinstance(data, dict) else None
    return last if last in STARTERS else None


def next_starter(state_path: str) -> str:
    """Devolve o inicial da vez e o grava como último escolhido.

    Arquivo ausente, ilegível ou com valor desconhecido recomeça em Bulbasaur.
    """
    path = Path(state_path)
    last = _last_starter(path)
    starter = STARTERS[0] if last is None else STARTERS[(STARTERS.index(last) + 1) % len(STARTERS)]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({STATE_KEY: starter}, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return starter
