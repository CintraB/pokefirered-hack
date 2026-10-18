"""Paralelismo da esteira: teto de processos (ESTEIRA_JOBS), divisão de cenários estatísticos
em partes e o executor de tarefas em processos separados.

Teto: `ESTEIRA_JOBS` (padrão 10) processos de trabalho ao mesmo tempo, contando tudo o que roda
em paralelo: cada sessão de emulador (o Python que a dirige e o runner do mGBA revezam, ~1
núcleo), a checagem de textos e os `make -jN` (N vagas). `ESTEIRA_JOBS=1` é o modo sequencial
de sempre (uma sessão por vez, nada dividido).

Partes: um cenário estatístico (`shiny`, `creche`) com `ScenarioSpec.parts` = P > 1 roda, no
modo paralelo, em P sessões da ROM de teste ao mesmo tempo, cada uma com a sua fatia do N
(`share`). A parte 0 faz o roteiro inteiro; as outras só as contagens. O CLI junta as fatias
(`ScenarioSpec.merge`) e aplica as MESMAS faixas estatísticas ao total. Cada parte semeia o RNG
do jogo (`gRngValue`) com `part_seed(cenário, índice)`: sementes fixas, separadas por
`SEED_WINDOW` passos do gerador do jogo, então as fatias nunca repetem a mesma sequência e o
resultado é o mesmo a cada execução com o mesmo número de partes (P não depende de
ESTEIRA_JOBS: com 4 ou com 10 processos as contas são idênticas).
"""

import multiprocessing
import os
import pickle
import struct
import tempfile
import time
import traceback
import zlib
from dataclasses import dataclass, field
from multiprocessing.connection import wait
from pathlib import Path
from typing import Any, Callable

JOBS_ENV = "ESTEIRA_JOBS"
DEFAULT_JOBS = 10
MAKE_JOBS_ENV = "ESTEIRA_MAKE_JOBS"   # vagas de um `make -j` dentro de uma tarefa (ex.: master)


def jobs() -> int:
    """Teto de processos simultâneos: ESTEIRA_JOBS (inteiro >= 1), senão DEFAULT_JOBS."""
    try:
        value = int(os.environ.get(JOBS_ENV, "").strip())
    except ValueError:
        return DEFAULT_JOBS
    return value if value >= 1 else DEFAULT_JOBS


def make_jobs() -> int:
    """`-j` de um make rodado pela esteira: as vagas dadas à tarefa, senão o teto inteiro."""
    try:
        value = int(os.environ.get(MAKE_JOBS_ENV, "").strip())
    except ValueError:
        return jobs()
    return value if value >= 1 else jobs()


def share(total: int, part: int, parts: int) -> int:
    """Fatia `part` (0..parts-1) de `total`: as primeiras levam o resto, a soma dá `total`."""
    if not 0 <= part < parts:
        raise ValueError(f"parte {part} fora de 0..{parts - 1}")
    return total // parts + (1 if part < total % parts else 0)


# --- sementes do RNG do jogo (src/random.c: gRngValue = 1103515245 * x + 24691) ---------------
RAND_MULT = 1103515245
RAND_ADD = 24691
SEED_WINDOW = 1 << 27     # passos do gerador entre duas sementes (~134 milhões: folga enorme)
MAX_SEED_INDEX = (1 << 32) // SEED_WINDOW   # 32 janelas disjuntas no ciclo de 2^32
RNG_SYMBOL = "gRngValue"


def lcg_jump(value: int, steps: int) -> int:
    """Estado do gerador do jogo depois de `steps` chamadas a Random() a partir de `value`."""
    mult, add = 1, 0                       # composição acumulada: x -> mult * x + add
    step_mult, step_add = RAND_MULT, RAND_ADD
    while steps:
        if steps & 1:
            mult, add = (mult * step_mult) & 0xFFFFFFFF, (add * step_mult + step_add) & 0xFFFFFFFF
        step_mult, step_add = ((step_mult * step_mult) & 0xFFFFFFFF,
                               (step_add * step_mult + step_add) & 0xFFFFFFFF)
        steps >>= 1
    return (mult * value + add) & 0xFFFFFFFF


def part_seed(scenario: str, index: int) -> int:
    """Semente fixa da janela `index` do cenário: a partir de uma base do nome, avança
    index * SEED_WINDOW passos (janelas disjuntas enquanto cada uma gastar menos que isso)."""
    if not 0 <= index < MAX_SEED_INDEX:
        raise ValueError(f"índice de semente {index} fora de 0..{MAX_SEED_INDEX - 1}")
    return lcg_jump(zlib.crc32(scenario.encode("utf-8")), index * SEED_WINDOW)


def seed_rng(emu, syms, scenario: str, index: int) -> int:
    """Grava a semente no gRngValue do jogo (só na ROM de teste); devolve a semente."""
    seed = part_seed(scenario, index)
    emu.write(syms.addr(RNG_SYMBOL), struct.pack("<I", seed))
    return seed


def part_label(part: int, parts: int) -> str:
    return f"parte {part + 1}/{parts}"


# --- junção das partes -------------------------------------------------------------------------

def part_data(parts_results: list, name: str):
    """Para o resultado `name`: (lista com o `data` de cada parte, None) se todas as partes o
    mediram; senão (None, Result de falha explicando qual parte faltou, com as evidências dela).
    `parts_results`: a lista de Results de cada parte, na ordem das partes."""
    from .result import Result
    datas = []
    for index, results in enumerate(parts_results):
        found = next((r for r in results if r.name == name), None)
        if found is not None and found.status != "falha" and found.data is not None:
            datas.append(found.data)
            continue
        cause = found if found is not None and found.status == "falha" else next(
            (r for r in results if r.status == "falha"), None)
        label = part_label(index, len(parts_results))
        if cause is None:
            return None, Result(name, "falha", f"{label}: sem a medição (a parte não chegou aqui)")
        return None, Result(name, "falha", f"{label}: {cause.name}: {cause.detail}",
                            list(cause.images), cause.state)
    return datas, None


# --- executor: tarefas em processos separados, no máximo `limit` vagas ocupadas ---------------

@dataclass
class Done:
    key: str
    value: Any = None
    error: str | None = None      # traceback do processo filho (exceção que escapou da tarefa)
    exitcode: int | None = 0
    start: float = 0.0
    end: float = 0.0


@dataclass
class _Task:
    key: str
    fn: Callable[[], Any]
    slots: int
    priority: float
    order: int
    proc: Any = None
    start: float = 0.0
    result_path: Path | None = None
    extra: dict = field(default_factory=dict)


def _child(fn: Callable[[], Any], result_path: str, env: dict[str, str]) -> None:
    os.environ.update(env)
    try:
        payload = {"value": fn()}
    except BaseException:  # noqa: BLE001 - o pai decide (vira erro de infraestrutura)
        payload = {"error": traceback.format_exc()}
    tmp = result_path + ".tmp"
    with open(tmp, "wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, result_path)


class Pool:
    """Roda funções em processos filhos (fork: herdam o estado do pai, inclusive o que os testes
    trocaram), ocupando no máximo `limit` vagas. Uma tarefa pede `slots` vagas (um `make -jN`
    pede N). Entre as que cabem, sai primeiro a de maior `priority` (a mais longa). O valor
    devolvido pela função vai para o pai num arquivo temporário (pickle) em /tmp."""

    def __init__(self, limit: int):
        self.limit = max(1, limit)
        self._pending: list[_Task] = []
        self._running: list[_Task] = []
        self._count = 0
        self._ctx = multiprocessing.get_context("fork")
        self._tmp = Path(tempfile.mkdtemp(prefix="esteira-tarefas-"))
        self.peak = 0          # maior número de vagas ocupadas ao mesmo tempo (conferido nos testes)

    def submit(self, key: str, fn: Callable[[], Any], slots: int = 1, priority: float = 0.0,
               env: dict[str, str] | None = None) -> None:
        task = _Task(key, fn, min(max(1, slots), self.limit), priority, self._count)
        task.extra["env"] = dict(env or {})
        self._count += 1
        self._pending.append(task)

    def busy(self) -> bool:
        return bool(self._pending or self._running)

    def used(self) -> int:
        return sum(t.slots for t in self._running)

    def _start_ready(self) -> None:
        for task in sorted(self._pending, key=lambda t: (-t.priority, t.order)):
            if task.slots > self.limit - self.used():
                continue
            self._pending.remove(task)
            task.result_path = self._tmp / f"{task.order:03d}.pickle"
            task.proc = self._ctx.Process(target=_child, name=f"esteira-{task.key}",
                                          args=(task.fn, str(task.result_path), task.extra["env"]))
            task.start = time.monotonic()
            task.proc.start()
            self._running.append(task)
            self.peak = max(self.peak, self.used())

    def step(self, timeout: float = 0.2) -> list[Done]:
        """Inicia o que cabe, espera até `timeout` s e devolve as tarefas que terminaram."""
        self._start_ready()
        if not self._running:
            return []
        wait([t.proc.sentinel for t in self._running], timeout=timeout)
        finished = []
        for task in list(self._running):
            if task.proc.is_alive():
                continue
            task.proc.join()
            self._running.remove(task)
            finished.append(self._collect(task))
        return finished

    def _collect(self, task: _Task) -> Done:
        done = Done(task.key, exitcode=task.proc.exitcode, start=task.start, end=time.monotonic())
        try:
            with open(task.result_path, "rb") as fh:
                payload = pickle.load(fh)
        except (OSError, EOFError, pickle.UnpicklingError) as exc:
            done.error = (f"o processo da tarefa '{task.key}' terminou (código "
                          f"{task.proc.exitcode}) sem devolver resultado: {exc}")
            return done
        finally:
            task.result_path.unlink(missing_ok=True)
        done.value = payload.get("value")
        done.error = payload.get("error")
        return done

    def close(self) -> None:
        """Encerra o que ainda roda (Ctrl-C, erro no pai) e apaga a pasta temporária."""
        for task in self._running:
            if task.proc.is_alive():
                task.proc.terminate()
        for task in self._running:
            task.proc.join(timeout=10)
            if task.proc.is_alive():
                task.proc.kill()
                task.proc.join()
        self._running.clear()
        self._pending.clear()
        for path in self._tmp.glob("*"):
            path.unlink(missing_ok=True)
        try:
            self._tmp.rmdir()
        except OSError:
            pass

    def __enter__(self) -> "Pool":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
