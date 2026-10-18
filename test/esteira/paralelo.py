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
do jogo (`gRngValue`) com `part_seed(cenário, índice, sal)`: sementes separadas por
`SEED_WINDOW` passos do gerador do jogo, então as fatias nunca repetem a mesma sequência. O sal
de 32 bits é sorteado a cada execução (`run_salt`; um falso vermelho estatístico não se repete)
e sai no meta.json, no resumo e no detalhe de cada resultado juntado; `ESTEIRA_SEED=0x...`
fixa o sal e reproduz as contagens (P não depende de ESTEIRA_JOBS: com 4 ou com 10 processos
as contas são idênticas).

Encerramento: cada tarefa roda num grupo de processos próprio, e SIGTERM nela vira SystemExit
(os `finally` rodam: o master remove a worktree); `Pool.close` manda SIGTERM ao grupo (o
make, os compiladores, o runner do mGBA), espera e só então SIGKILL.
"""

import multiprocessing
import os
import pickle
import random
import signal
import struct
import sys
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
MAX_JOBS = 64             # teto do teto (o Makefile normaliza igual)
SEED_ENV = "ESTEIRA_SEED"  # sal das sementes das partes; fixe para reproduzir uma execução
MAKE_JOBS_ENV = "ESTEIRA_MAKE_JOBS"   # vagas de um `make -j` dentro de uma tarefa (ex.: master)


def jobs() -> int:
    """Teto de processos simultâneos: ESTEIRA_JOBS (inteiro >= 1, no máximo MAX_JOBS), senão
    DEFAULT_JOBS (a mesma regra do Makefile)."""
    try:
        value = int(os.environ.get(JOBS_ENV, "").strip())
    except ValueError:
        return DEFAULT_JOBS
    return min(value, MAX_JOBS) if value >= 1 else DEFAULT_JOBS


def run_salt() -> int:
    """Sal de 32 bits das sementes das partes nesta execução: ESTEIRA_SEED (decimal ou 0x...)
    para reproduzir uma execução anterior, senão sorteado (cada execução usa outras sequências
    do RNG, então um falso vermelho estatístico não se repete)."""
    raw = os.environ.get(SEED_ENV, "").strip()
    if raw:
        try:
            return int(raw, 0) & 0xFFFFFFFF
        except ValueError:
            pass
    return random.SystemRandom().getrandbits(32)


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


def part_seed(scenario: str, index: int, salt: int = 0) -> int:
    """Semente da janela `index` do cenário: a partir de uma base (nome do cenário XOR o sal da
    execução), avança index * SEED_WINDOW passos (janelas disjuntas enquanto cada uma gastar
    menos que isso). Mesmo sal = mesmas sementes (reprodução com ESTEIRA_SEED)."""
    if not 0 <= index < MAX_SEED_INDEX:
        raise ValueError(f"índice de semente {index} fora de 0..{MAX_SEED_INDEX - 1}")
    base = zlib.crc32(scenario.encode("utf-8")) ^ (salt & 0xFFFFFFFF)
    return lcg_jump(base, index * SEED_WINDOW)


def seed_label(salt: int) -> str:
    return f"ESTEIRA_SEED=0x{salt & 0xFFFFFFFF:08x}"


def seed_rng(emu, syms, scenario: str, index: int, salt: int = 0) -> int:
    """Grava a semente no gRngValue do jogo (só na ROM de teste); devolve a semente."""
    seed = part_seed(scenario, index, salt)
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


def _terminated(signum, frame) -> None:
    raise SystemExit(128 + signum)


def _child(fn: Callable[[], Any], result_path: str, env: dict[str, str]) -> None:
    # Grupo de processos próprio (o pai encerra a árvore inteira: make, compiladores, runner do
    # mGBA) e SIGTERM vira SystemExit: os `finally` rodam (o master remove a worktree) e o
    # subprocess.run em andamento mata o filho dele.
    os.setpgid(0, 0)
    signal.signal(signal.SIGTERM, _terminated)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    os.environ.update(env)
    try:
        payload = {"value": fn()}
    except BaseException:  # noqa: BLE001 - o pai decide (vira erro de infraestrutura)
        payload = {"error": traceback.format_exc()}
    tmp = result_path + ".tmp"
    with open(tmp, "wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, result_path)


def _signal_group(proc, sig: int) -> None:
    """Sinal para o grupo de processos da tarefa (o filho e tudo o que ele abriu)."""
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        if proc.is_alive():
            os.kill(proc.pid, sig)


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
            try:
                os.setpgid(task.proc.pid, task.proc.pid)   # sem corrida com o setpgid do filho
            except OSError:
                pass
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
        except Exception as exc:  # noqa: BLE001 - arquivo ausente, truncado ou ilegível
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
                _signal_group(task.proc, signal.SIGTERM)
        for task in self._running:
            task.proc.join(timeout=30)        # o filho limpa (worktree do master...) e sai
            if task.proc.is_alive():
                _signal_group(task.proc, signal.SIGKILL)
                task.proc.join()
            else:                             # o que sobrou da árvore dele (make, compiladores)
                _signal_group(task.proc, signal.SIGKILL)
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
