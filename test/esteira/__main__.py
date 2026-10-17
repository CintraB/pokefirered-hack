"""CLI da esteira de testes.

A partir de test/ (no WSL):
    python3 -m esteira rapido   --rom R --elf E [--log L] --out DIR [--only NOME] [--starter X]
    python3 -m esteira completo --rom R --elf E [--rom-test RT --elf-test ET] [--log L] --out DIR ...
    python3 -m esteira aprovar DIR
    python3 -m esteira nao-testada --out DIR     # SKIP_TESTS=1: só o relatório "NÃO TESTADA"

`rapido` roda a checagem do log de build, a checagem dos textos e os 3 roteiros rápidos numa
sessão de emulador só. `completo` roda tudo isso e mais os cenários de FULL_SCENARIOS: PC,
tour de telas e Floresta/Brock continuam a sessão jogável; o `master` compila o master sem
emulador; o `shiny` usa a ROM de teste (`make firered_switch TESTBUILD=1`) e parte do save do
`captura`.
Sai com 0 se nenhum resultado for `falha` (avisos não reprovam) e 1 caso contrário.
"""

import argparse
import json
import shutil
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
from esteira.result import Result, StepTimeout, Suite
from esteira.rotation import STARTERS, next_starter
from esteira.scenarios import REPO_ROOT, ScenarioContext, open_context
from esteira.scenarios.full_forest_brock import run_full_forest_brock
from esteira.scenarios.full_master import run_full_master
from esteira.scenarios.full_pc import run_full_pc
from esteira.scenarios.full_screen_tour import run_full_screen_tour
from esteira.scenarios.full_shiny import run_full_shiny
from esteira.scenarios.quick_catch_save import run_catch_save
from esteira.scenarios.quick_opening import run_opening
from esteira.scenarios.quick_route1 import run_route1

REFS_DIR = DEFAULT_REFS_DIR
STATE_PATH = str(REPO_ROOT / "roms" / "estado-esteira.json")   # produção; testes sobrescrevem
EXCEPTIONS_PATH = REPO_ROOT / "test" / "excecoes.json"
STATIC_CHECKS = ("build", "texto")
PLAYABLE, TEST, HOST = "playable", "test", "host"   # ROM do cenário (HOST: sem emulador)
DEFAULT_ROM_TEST = str(REPO_ROOT / "pokefirered_switch_test.gba")
DEFAULT_ELF_TEST = str(REPO_ROOT / "pokefirered_switch_test.elf")


@dataclass
class ScenarioSpec:
    """Um cenário na cadeia de uma sessão de emulador.

    Cenários da mesma ROM (`rom`: PLAYABLE ou TEST) rodam em sequência numa única sessão: o
    primeiro do grupo começa do boot e `run(ctx)` de cada um continua do estado que o anterior
    deixou. `needs` é o checkpoint (OUT/estados/<needs>.ss, gravado pelo cenário anterior do
    mesmo grupo) de onde o cenário pode recomeçar com `--only`; None = só começa do boot.
    Checkpoints nunca valem entre ROMs diferentes. `rom=HOST`: roda fora do emulador (ctx só
    com `suite`, `out_dir` e `starter`; `emu`, `game` etc. são None), sem ROM nem checkpoint.

    `save_from` (só no 1º cenário de um grupo da ROM de teste): nome do cenário da ROM jogável
    cujo save do jogo (.sav) a sessão de teste carrega ao ligar — savestates não valem entre
    builds, o .sav vale. Logo que esse cenário termina sem falha, o save do jogo da memória é
    gravado (emu.flush_save) e copiado para OUT/<save_from>.sav (+ OUT/<save_from>.sav.json com
    o inicial), antes dos cenários jogáveis seguintes (que podem salvar o jogo ou mudar de
    mapa); se a cópia falhar, o cenário vira `falha`. O grupo jogável roda antes (ordem de
    FULL_SCENARIOS). Se o cenário estava na execução e não deixou o .sav, o grupo de teste vira
    `aviso` "não rodou". Com `--only` de um
    cenário da ROM de teste, usa o OUT/<save_from>.sav de uma execução anterior na mesma pasta
    (`rapido` também o deixa); sem ele, `falha` explicando o que rodar.
    """
    name: str
    run: Callable[[ScenarioContext], None]
    needs: str | None = None
    rom: str = PLAYABLE
    save_from: str | None = None


QUICK_SCENARIOS = [
    ScenarioSpec("abertura", run_opening),
    ScenarioSpec("rota1", run_route1, needs="rival"),
    ScenarioSpec("captura", run_catch_save, needs="encomenda"),
]

# Ponto de registro do modo completo. Cenário novo = 1 linha na lista (+ o import acima), p.ex.:
#     ScenarioSpec("x", run_full_x, rom=TEST),                    # ROM de teste, parte do boot
#     ScenarioSpec("completo1", run_full_y, needs="save"),        # ROM jogável, continua do `save`
# `rom=TEST` usa --rom-test/--elf-test (padrão: pokefirered_switch_test.gba/.elf na raiz).
# Os jogáveis continuam a sessão do modo rápido, cada um do checkpoint que o anterior deixa
# (`save` -> `pc` -> `telas`). O shiny parte do .sav gravado logo depois do `captura`
# (save_from), então os jogáveis seguintes não mudam o ponto de partida dele
# (test_cli.py::test_registro_dos_cenarios_completos confere a ordem).
FULL_SCENARIOS: list[ScenarioSpec] = [
    ScenarioSpec("pc", run_full_pc, needs="save"),
    ScenarioSpec("telas", run_full_screen_tour, needs="pc"),
    ScenarioSpec("floresta_brock", run_full_forest_brock, needs="telas"),
    ScenarioSpec("master", run_full_master, rom=HOST),
    ScenarioSpec("shiny", run_full_shiny, rom=TEST, save_from="captura"),
]


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
    """Roda build/texto; devolve True se o log mostra que não há ROM jogável utilizável."""
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


def _groups(specs: list[ScenarioSpec], only: str | None) -> list[tuple[str, list[ScenarioSpec]]]:
    """Agrupa os cenários por ROM (na ordem da primeira aparição). Com `only`, só o grupo dele,
    cortado nele (o que vem antes no grupo é pré-requisito)."""
    if only is not None:
        spec = next(s for s in specs if s.name == only)
        group = [s for s in specs if s.rom == spec.rom]
        return [(spec.rom, group[:group.index(spec) + 1])]
    order: dict[str, list[ScenarioSpec]] = {}
    for s in specs:
        order.setdefault(s.rom, []).append(s)
    return list(order.items())


def _chain(group: list[ScenarioSpec], only: str | None, ctx: ScenarioContext) -> list[ScenarioSpec]:
    """Cenários do grupo a rodar. Com `only`, o último do grupo é o escolhido; se o checkpoint
    de que ele precisa existir em OUT (de outra execução, mesmo inicial), recomeça dele em vez de
    repetir o que veio antes."""
    if only is None:
        return group
    spec = group[-1]
    ctl = ctx.controller
    if spec.needs and ctl.checkpoint_path(spec.needs).is_file():
        ctl.restore(spec.needs)
        party = ctx.game.party()
        if party and party[0].species == ctx.consts.species(ctx.starter):
            return [spec]
        ctx.emu.reset()   # checkpoint de outro inicial: descarta e roda a cadeia inteira
    return group


def _fail_result(spec: ScenarioSpec, exc: Exception) -> Result:
    tail = "".join(traceback.format_exception(exc)[-3:]).strip()
    result = Result(f"cenario/{spec.name}", "falha",
                    f"erro inesperado: {type(exc).__name__}: {exc}\n{tail}")
    if isinstance(exc, StepTimeout):
        result.images, result.state = [exc.screenshot_path], exc.state_path
    return result


def _not_run(suite: Suite, specs: list[ScenarioSpec],
             why: str = "não rodou: um cenário anterior falhou") -> None:
    for spec in specs:
        suite.add(Result(f"cenario/{spec.name}", "aviso", why))


def _run_scenarios(group: list[ScenarioSpec], ctx: ScenarioContext, only: str | None,
                   tempos: dict[str, float], bridges: set[str] = frozenset()) -> None:
    """Roda a cadeia de um grupo; depois de um cenário com falha, os seguintes viram `aviso`.
    Só falhas surgidas durante a cadeia contam (as checagens estáticas não interrompem nada).
    Um cenário de `bridges` que termina sem falha deixa o .sav da ponte (_write_bridge); se a
    ponte não puder ser gravada, ele vira `falha`."""
    chain = _chain(group, only, ctx)
    suite = ctx.suite
    out = Path(ctx.out_dir)
    for pos, spec in enumerate(chain):
        before = sum(1 for r in suite.results if r.status == "falha")
        print(f"[rodando] {spec.name}...", flush=True)
        start = time.monotonic()
        if spec.name in bridges:   # vai ser refeito agora: o .sav antigo não vale
            for path in _bridge_paths(out, spec.name):
                path.unlink(missing_ok=True)
        try:
            spec.run(ctx)
        except Exception as exc:  # noqa: BLE001 - qualquer erro vira falha no relatório
            suite.add(_fail_result(spec, exc))
        failed = sum(1 for r in suite.results if r.status == "falha") > before
        if spec.name in bridges and not failed:
            try:
                _write_bridge(ctx, spec.name)
            except Exception as exc:  # noqa: BLE001 - sem a ponte o produtor reprova
                suite.add(Result(f"cenario/{spec.name}", "falha",
                                 "save do jogo para a ROM de teste não gravado: "
                                 f"{type(exc).__name__}: {exc}"))
                failed = True
        tempos[spec.name] = time.monotonic() - start
        if failed:
            _not_run(suite, chain[pos + 1:])
            return


# --- save do jogo (.sav) da ROM jogável para a ROM de teste (ScenarioSpec.save_from) --------

def _save_producers() -> set[str]:
    """Cenários da ROM jogável cujo .sav algum cenário da ROM de teste usa (todos os modos:
    o `rapido` também deixa o .sav para um `completo --only` depois)."""
    return {s.save_from for s in scenarios_for("completo") if s.save_from}


def _bridge_paths(out: Path, producer: str) -> tuple[Path, Path]:
    """OUT/<cenário>.sav e o .json com o inicial (nunca o OUT/esteira.sav da sessão)."""
    return out / f"{producer}.sav", out / f"{producer}.sav.json"


def _write_bridge(ctx: ScenarioContext, producer: str) -> None:
    """Grava no OUT/esteira.sav o save do jogo da memória (o mGBA só garante isso ao fechar)
    e o copia para OUT/<producer>.sav, com o inicial ao lado."""
    out = Path(ctx.out_dir)
    ctx.emu.flush_save()
    save, info = _bridge_paths(out, producer)
    tmp = save.with_name(save.name + ".tmp")
    shutil.copyfile(out / "esteira.sav", tmp)
    tmp.replace(save)
    info.write_text(json.dumps({"inicial": ctx.starter}) + "\n", encoding="utf-8")


def _bridge_starter(info: Path) -> str | None:
    try:
        starter = json.loads(info.read_text(encoding="utf-8")).get("inicial")
    except (OSError, ValueError, AttributeError):
        return None
    return starter if starter in STARTERS else None


def _missing_save(producer: str, scheduled: bool, save: Path, out: Path) -> tuple[str, str]:
    if scheduled:
        return "aviso", (f"não rodou: o cenário '{producer}' não deixou o save do jogo nesta "
                         "execução (falhou ou não rodou)")
    return "falha", (f"sem o save do jogo de '{producer}' ({save}): a ROM de teste parte do .sav "
                     "da ROM jogável (savestates não valem entre builds); rode antes "
                     f"`python3 -m esteira rapido --out {out}` (mesma pasta) ou o `completo` "
                     "sem --only")


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
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    suite = Suite()
    tempos: dict[str, float] = {}
    started_wall = time.time()
    start = time.monotonic()
    nao_testada = False
    starter: str | None = args.starter   # sem --starter, só sai do rodízio quando o emulador roda

    unusable = _static_checks(args, suite)
    if args.only in (None, *[s.name for s in specs]):
        roms = {PLAYABLE: (args.rom, args.elf, "ROM jogável"),
                TEST: (args.rom_test, args.elf_test, "ROM de teste")}
        groups = _groups(specs, args.only)
        scheduled = {s.name for _, group in groups for s in group}
        producers = _save_producers()
        for kind, group in groups:
            if kind == HOST:
                host = ScenarioContext(emu=None, game=None, controller=None, nav=None,
                                       suite=suite, consts=None, out_dir=str(out),
                                       starter=starter or "-")
                _run_scenarios(group, host, args.only, tempos)
                continue
            rom, elf, label = roms[kind]
            missing = [p for p in (rom, elf) if not Path(p).is_file()]
            bad_build = unusable and kind == PLAYABLE
            if bad_build or missing:
                if kind == PLAYABLE:
                    nao_testada = True
                why = ("o log de build mostra que a ROM não foi gerada" if bad_build
                       else "arquivo não encontrado: " + ", ".join(missing))
                suite.add(Result(f"emulador/rom-{kind}", "falha", f"{label} não testada: {why}"))
                continue
            save_from = None
            producer = group[0].save_from
            if producer is not None:
                save, info = _bridge_paths(out, producer)
                if not save.is_file():
                    status, why = _missing_save(producer, producer in scheduled, save, out)
                    suite.add(Result(f"cenario/{group[0].name}", status, why))
                    _not_run(suite, group[1:])
                    continue
                save_from = str(save)
                if starter is None:   # o inicial é o do .sav (não gasta o rodízio)
                    starter = _bridge_starter(info)
            if starter is None:
                starter = next_starter(args.state)
            bridges = producers if kind == PLAYABLE else set()
            with open_context(rom, elf, str(out), starter, suite, save_from=save_from) as ctx:
                _run_scenarios(group, ctx, args.only, tempos, bridges)
        if starter is not None:
            _compare_screens(suite, out, starter, started_wall)

    meta = {"inicial": starter or "-", "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit": _git_commit(), "modo": args.modo, "tempos": tempos,
            "tempo_total": time.monotonic() - start, "nao_testada": nao_testada}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
    report = write_report(suite, str(out), meta)
    _print_summary(suite, meta, report)
    return 1 if suite.failed() else 0


def write_untested_report(out_dir: str) -> str:
    """Relatório só com a faixa NÃO TESTADA (SKIP_TESTS=1): sem emulador e sem checagens."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    suite = Suite()
    suite.add(Result("esteira/pulada", "aviso",
                     "testes pulados (SKIP_TESTS=1): esta ROM não foi testada"))
    meta = {"inicial": "-", "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit": _git_commit(), "modo": "nao-testada", "tempos": {}, "tempo_total": 0.0,
            "nao_testada": True}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
    return write_report(suite, str(out), meta)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="esteira", description="Esteira de testes da ROM hack")
    sub = parser.add_subparsers(dest="modo", required=True)
    for modo, text in (("rapido", "checagens estáticas + 3 roteiros rápidos"),
                       ("completo", "modo rápido + cenários completos registrados")):
        p = sub.add_parser(modo, help=text)
        p.add_argument("--rom", required=True)
        p.add_argument("--elf", required=True)
        p.add_argument("--rom-test", default=DEFAULT_ROM_TEST,
                       help="ROM de teste (com hooks em C), só para cenários com rom=TEST")
        p.add_argument("--elf-test", default=DEFAULT_ELF_TEST)
        p.add_argument("--log", help="log do build (make); sem ele só a checagem de texto roda")
        p.add_argument("--out", required=True, help="pasta da execução (relatório, telas, estados)")
        p.add_argument("--only", help="só um item: " + ", ".join(
            STATIC_CHECKS + tuple(s.name for s in scenarios_for(modo))))
        p.add_argument("--starter", choices=STARTERS,
                       help="força o inicial (não gasta o rodízio); padrão: o da vez")
        p.add_argument("--state", default=STATE_PATH, help=argparse.SUPPRESS)
    untested = sub.add_parser("nao-testada", help="só o relatório NÃO TESTADA (SKIP_TESTS=1)")
    untested.add_argument("--out", required=True)
    approve = sub.add_parser("aprovar", help="promove as telas de uma execução a referência")
    approve.add_argument("dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.modo == "nao-testada":
        print(f"ROM NÃO TESTADA (sem emulador); relatório: {write_untested_report(args.out)}")
        return 0
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
