"""CLI da esteira de testes.

A partir de test/ (no WSL):
    python3 -m esteira rapido   --rom R --elf E [--log L] --out DIR [--only NOME] [--starter X]
    python3 -m esteira completo --rom R --elf E [--log L] --out DIR [--only NOME] [--starter X]
    python3 -m esteira aprovar DIR

`rapido` roda a checagem do log de build, a checagem dos textos e os 3 roteiros rápidos numa
sessão de emulador só. `completo` roda tudo isso e mais os cenários de FULL_SCENARIOS.
Sai com 0 se nenhum resultado for `falha` (avisos não reprovam) e 1 caso contrário.
"""

import argparse
import json
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from esteira.check_build import check_build
from esteira.check_text import check_text
from esteira.refs import DEFAULT_REFS_DIR, KEY_POINTS, approve_refs, compare_ref
from esteira.report import write_report
from esteira.result import Result, Suite
from esteira.rotation import STARTERS, next_starter
from esteira.scenarios import REPO_ROOT, ScenarioContext, open_context
from esteira.scenarios.quick_catch_save import run_catch_save
from esteira.scenarios.quick_opening import run_opening
from esteira.scenarios.quick_route1 import run_route1

REFS_DIR = DEFAULT_REFS_DIR
STATE_PATH = str(REPO_ROOT / "roms" / "estado-esteira.json")   # produção; testes passam --state
EXCEPTIONS_PATH = REPO_ROOT / "test" / "excecoes.json"
STATIC_CHECKS = ("build", "texto")


@dataclass
class ScenarioSpec:
    """Um cenário na cadeia de uma sessão de emulador.

    `run(ctx)` continua do estado que o cenário anterior deixou no emulador. `needs` é o
    checkpoint (OUT/estados/<needs>.ss) de onde ele pode recomeçar (None = começa do boot) e
    `produces` o checkpoint que ele grava ao terminar.
    """
    name: str
    run: Callable[[ScenarioContext], None]
    needs: str | None
    produces: str | None


QUICK_SCENARIOS = [
    ScenarioSpec("abertura", run_opening, None, "rival"),
    ScenarioSpec("rota1", run_route1, "rival", "encomenda"),
    ScenarioSpec("captura", run_catch_save, "encomenda", "save"),
]

# Ponto de registro do modo completo: um cenário novo (full_shiny, Task 11...) entra aqui com
# uma linha, ex.: ScenarioSpec("shiny", run_shiny, needs="save", produces=None).
FULL_SCENARIOS: list[ScenarioSpec] = []


def scenarios_for(mode: str) -> list[ScenarioSpec]:
    return QUICK_SCENARIOS if mode == "rapido" else QUICK_SCENARIOS + FULL_SCENARIOS


# --- execução -----------------------------------------------------------------------------

def _git_commit() -> str:
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True,
                              text=True, timeout=30, check=True).stdout.strip()
    try:
        # sem `git status`: em /mnt/c (WSL) ele leva ~45 s
        return git("rev-parse", "--short", "HEAD")
    except (OSError, subprocess.SubprocessError):
        return "desconhecido"


def _build_unusable(results: list[Result]) -> bool:
    """O log mostra que a ROM não foi gerada (erro de build, log ilegível ou memória esgotada)."""
    return any(r.status == "falha" and (r.name in ("build/erro", "build/log")
                                        or r.detail.endswith("memória esgotada"))
               for r in results)


def _static_checks(args: argparse.Namespace, suite: Suite) -> bool:
    """Roda build/texto; devolve True se o log mostra que não há ROM utilizável."""
    exceptions = json.loads(EXCEPTIONS_PATH.read_text(encoding="utf-8"))
    unusable = False
    if args.only in (None, "build"):
        if args.log:
            results = check_build(args.log, exceptions)
            unusable = _build_unusable(results)
            for r in results:
                suite.add(r)
        else:
            suite.add(Result("build/log", "aviso",
                             "sem --log: log de build não analisado (só a checagem de texto rodou)"))
    if args.only in (None, "texto"):
        results = check_text(str(REPO_ROOT), exceptions)
        for r in results:
            suite.add(r)
        if not results:
            suite.add(Result("texto/estático", "ok", "nenhum problema nos textos do jogo"))
    return unusable


def _chain(specs: list[ScenarioSpec], only: str | None, ctx: ScenarioContext) -> list[ScenarioSpec]:
    """Cenários a rodar. Com `only`, só até ele, recomeçando do checkpoint se ele existir em OUT
    (de outra execução, com o mesmo inicial) em vez de repetir o que veio antes."""
    if only is None:
        return specs
    index = next(i for i, s in enumerate(specs) if s.name == only)
    spec = specs[index]
    ctl = ctx.controller
    if spec.needs and ctl.checkpoint_path(spec.needs).is_file():
        ctl.restore(spec.needs)
        party = ctx.game.party()
        if party and party[0].species == ctx.consts.species(ctx.starter):
            return [spec]
        ctx.emu.reset()   # checkpoint de outro inicial: descarta e roda a cadeia inteira
    return specs[:index + 1]


def _run_scenarios(specs: list[ScenarioSpec], ctx: ScenarioContext, only: str | None,
                   tempos: dict[str, float]) -> None:
    chain = _chain(specs, only, ctx)
    for pos, spec in enumerate(chain):
        if ctx.suite.failed():
            for rest in chain[pos:]:
                ctx.suite.add(Result(f"cenario/{rest.name}", "aviso",
                                     "não rodou: um cenário anterior falhou"))
            return
        print(f"[rodando] {spec.name}...", flush=True)
        start = time.monotonic()
        try:
            spec.run(ctx)
        except Exception as exc:  # noqa: BLE001 - qualquer erro vira falha no relatório
            tail = "".join(traceback.format_exception(exc)[-3:]).strip()
            ctx.suite.add(Result(f"cenario/{spec.name}", "falha",
                                 f"erro inesperado: {type(exc).__name__}: {exc}\n{tail}"))
        tempos[spec.name] = time.monotonic() - start


def _compare_screens(suite: Suite, out: Path, starter: str, since: float) -> None:
    for point in KEY_POINTS:
        shot = out / "telas" / f"{point}.png"
        if shot.is_file() and shot.stat().st_mtime >= since:
            suite.add(compare_ref(point, starter, str(shot), REFS_DIR))


def _print_summary(suite: Suite, meta: dict, report: str) -> None:
    counts = {s: sum(1 for r in suite.results if r.status == s) for s in ("falha", "aviso", "ok")}
    print()
    if meta["nao_testada"]:
        print("*** ROM NÃO TESTADA: o emulador não rodou ***")
    for r in suite.results:
        if r.status != "ok":
            print(f"[{r.status}] {r.name}: {r.detail.splitlines()[0] if r.detail else ''}")
    print(f"inicial {meta['inicial']}: {counts['falha']} falha(s), {counts['aviso']} aviso(s), "
          f"{counts['ok']} ok em {meta['tempo_total']:.1f} s")
    for name, seconds in meta["tempos"].items():
        print(f"  {name}: {seconds:.1f} s")
    print(f"relatório: {report}")


def run_mode(args: argparse.Namespace) -> int:
    specs = scenarios_for(args.modo)
    starter = args.starter or next_starter(args.state)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    suite = Suite()
    tempos: dict[str, float] = {}
    started_wall = time.time()
    start = time.monotonic()
    nao_testada = False

    unusable = _static_checks(args, suite)
    if args.only in (None, *[s.name for s in specs]):
        missing = [p for p in (args.rom, args.elf) if not Path(p).is_file()]
        if unusable or missing:
            nao_testada = True
            why = ("o log de build mostra que a ROM não foi gerada" if unusable
                   else "arquivo não encontrado: " + ", ".join(missing))
            suite.add(Result("emulador/rom", "falha", f"ROM não testada: {why}"))
        else:
            with open_context(args.rom, args.elf, str(out), starter, suite) as ctx:
                _run_scenarios(specs, ctx, args.only, tempos)
            _compare_screens(suite, out, starter, started_wall)

    meta = {"inicial": starter, "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit": _git_commit(), "modo": args.modo, "tempos": tempos,
            "tempo_total": time.monotonic() - start, "nao_testada": nao_testada}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
    report = write_report(suite, str(out), meta)
    _print_summary(suite, meta, report)
    return 1 if suite.failed() else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="esteira", description="Esteira de testes da ROM hack")
    sub = parser.add_subparsers(dest="modo", required=True)
    for modo, text in (("rapido", "checagens estáticas + 3 roteiros rápidos"),
                       ("completo", "modo rápido + cenários completos registrados")):
        p = sub.add_parser(modo, help=text)
        p.add_argument("--rom", required=True)
        p.add_argument("--elf", required=True)
        p.add_argument("--log", help="log do build (make); sem ele só a checagem de texto roda")
        p.add_argument("--out", required=True, help="pasta da execução (relatório, telas, estados)")
        p.add_argument("--only", help="só um item: " + ", ".join(
            STATIC_CHECKS + tuple(s.name for s in scenarios_for(modo))))
        p.add_argument("--starter", choices=STARTERS,
                       help="força o inicial (não gasta o rodízio); padrão: o da vez")
        p.add_argument("--state", default=STATE_PATH, help=argparse.SUPPRESS)
    approve = sub.add_parser("aprovar", help="promove as telas de uma execução a referência")
    approve.add_argument("dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.modo == "aprovar":
        try:
            copied = approve_refs(args.dir, refs_dir=REFS_DIR)
        except ValueError as exc:
            parser.error(str(exc))
        if not copied:
            print(f"nenhuma tela de ponto-chave encontrada em {args.dir}/telas", file=sys.stderr)
            return 1
        for path in copied:
            print(f"referência atualizada: {path}")
        return 0
    valid = STATIC_CHECKS + tuple(s.name for s in scenarios_for(args.modo))
    if args.only is not None and args.only not in valid:
        parser.error(f"--only {args.only!r} desconhecido; opções: {', '.join(valid)}")
    return run_mode(args)


if __name__ == "__main__":
    sys.exit(main())
