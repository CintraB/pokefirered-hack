"""Inicial em rodízio entre execuções: Bulbasaur -> Charmander -> Squirtle -> Bulbasaur...

O estado fica num JSON fora do Git (em produção, roms/estado-esteira.json; testes usam
um caminho temporário) com o último inicial de uma execução VERDE. A execução espia o da vez
(peek_next_starter) e só o grava (record_starter) se terminar verde: um vermelho repete o mesmo
inicial na próxima, para que um bug de um inicial só não "passe" trocando de inicial.
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


def peek_next_starter(state_path: str) -> str:
    """O inicial da vez, SEM gravar nada.

    Arquivo ausente, ilegível ou com valor desconhecido recomeça em Bulbasaur.
    """
    last = _last_starter(Path(state_path))
    return STARTERS[0] if last is None else STARTERS[(STARTERS.index(last) + 1) % len(STARTERS)]


def record_starter(state_path: str, starter: str) -> None:
    """Grava `starter` como o último usado (o próximo peek devolve o seguinte)."""
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({STATE_KEY: starter}, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
