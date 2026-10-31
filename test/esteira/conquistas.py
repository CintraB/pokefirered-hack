"""Conquistas e diário de batalhas (POK-44): o lado Python da tabela e do formato no save.

Lê a tabela-fonte `src/data/conquistas/conquistas.json` (a mesma que o make converte em
`src/data/conquistas_ids.h`) e decodifica uma `struct DiarioEntrada` (include/global.h) lida da RAM.
"""

import json
import re
import struct
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

JSON_PATH = REPO_ROOT / "src" / "data" / "conquistas" / "conquistas.json"

CONQ_MAGIC = 0x31445143   # "CQD1"
CONQ_PENDENTE, CONQ_FEITA, CONQ_PERDIDA = 0, 1, 2
CONQ_ORIGEM_JOGO_NOVO, CONQ_ORIGEM_SAVE_ANTIGO = 0, 1
DIARIO_VENCEU, DIARIO_CAPTURADO, DIARIO_DERROTOU = 1, 2, 3

# struct DiarioEntrada: minutos u16, turnos, resultado, ordem, mvp, mvpNocautes, tamanhoTime, time[6] u16
DIARIO_ENTRADA_FORMAT = "<HBBBBBB6H"
DIARIO_ENTRADA_SIZE = struct.calcsize(DIARIO_ENTRADA_FORMAT)


@lru_cache(maxsize=1)
def dados() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def num(cid: str) -> int:
    """CONQ_<ID> (campo `num`) da conquista `cid`; KeyError se não existe."""
    for c in dados()["conquistas"]:
        if c["id"] == cid:
            return c["num"]
    raise KeyError(cid)


def evento(eid: str) -> int:
    """DIARIO_EVT_<ID> (posição em `diario`) do evento `eid`; KeyError se não existe."""
    for i, e in enumerate(dados()["diario"]):
        if e["id"] == eid:
            return i
    raise KeyError(eid)


def ativas() -> list[int]:
    """`num` das conquistas ativas, em ordem."""
    return sorted(c["num"] for c in dados()["conquistas"] if c.get("ativa", True))


GYM_TRAINERS_INC = REPO_ROOT / "data" / "scripts" / "set_gym_trainers.inc"


@lru_cache(maxsize=1)
def treinadores_do_ginasio() -> list[list[str]]:
    """Os TRAINER_* que o `set_gym_trainers N` liga (data/scripts/set_gym_trainers.inc), na ordem das
    insígnias: o item i é o Ginásio da FLAG_BADGE0{i+1}_GET (o `case N` do switch, N = i + 1)."""
    texto = GYM_TRAINERS_INC.read_text(encoding="utf-8")
    casos = dict((int(n), rotulo) for n, rotulo in re.findall(r"case (\d+), (\w+)", texto))
    assert sorted(casos) == list(range(1, 9)), casos
    ginasios = []
    for n in range(1, 9):
        corpo = re.search(rf"^{casos[n]}::\n(.*?)^\treturn", texto, re.S | re.M).group(1)
        ginasios.append(re.findall(r"settrainerflag (TRAINER_\w+)", corpo))
    return ginasios


def parse_entrada(raw: bytes) -> dict:
    """Decodifica uma struct DiarioEntrada (20 bytes). `time` traz (espécie, nível) dos
    `tamanhoTime` primeiros (espécie nos 9 bits de baixo, nível nos 7 de cima)."""
    minutos, turnos, resultado, ordem, mvp, nocautes, tamanho, *time = struct.unpack(
        DIARIO_ENTRADA_FORMAT, bytes(raw[:DIARIO_ENTRADA_SIZE]))
    return {"minutos": minutos, "turnos": turnos, "resultado": resultado, "ordem": ordem, "mvp": mvp,
            "mvpNocautes": nocautes, "tamanhoTime": tamanho,
            "time": [(t & 0x1FF, t >> 9) for t in time[:tamanho]]}
