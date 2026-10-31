"""CLI da esteira de testes.

A partir de test/ (no WSL):
    python3 -m esteira rapido   --rom R --elf E [--log L] --out DIR [--only NOME] [--starter X]
    python3 -m esteira completo --rom R --elf E [--rom-test RT --elf-test ET] [--log L] --out DIR ...
    python3 -m esteira aprovar DIR
    python3 -m esteira nao-testada --out DIR     # SKIP_TESTS=1: só o relatório "NÃO TESTADA"
    python3 -m esteira assistir [--starter X] [--from CHECKPOINT | --cenario evolucoes|resumo_evolucao|resumo_ivs|ovo] [--rom R --elf E]

`rapido` roda a checagem do log de build, a checagem dos textos e os 3 roteiros rápidos numa
sessão de emulador só. `completo` roda tudo isso e mais os cenários de FULL_SCENARIOS: PC,
tour de telas e Floresta/Brock continuam a sessão jogável; o `master` compila o master sem
emulador; o `shiny`, o `evolucoes`, o `resumo_evolucao`, o `resumo_ivs`, o `creche` e o `ovo` usam a
ROM de teste (`make firered_switch TESTBUILD=1`), cada um numa sessão própria que parte do save do
`captura`.
Toda execução com emulador grava OUT/video.webp: a execução inteira (todas as sessões, jogável e
teste) em WebP animado acelerado (um quadro a cada 8 emulados, 30 fps), embutido no relatório;
`--sem-video` desliga (ver esteira/video.py).
`assistir` é à parte do pipeline: roda os roteiros rápidos numa janela, em tempo real e com som,
com um save temporário; não gera versão, não mexe em roms/ nem no rodízio de iniciais. Com
`--cenario evolucoes` (ou `resumo_evolucao`, `resumo_ivs`, `ovo`), mostra esse cenário do modo completo na ROM de
teste (partindo de uma cópia do captura.sav mais recente de test/out/*/).
Paralelismo (esteira/paralelo.py): até ESTEIRA_JOBS (padrão 10) processos ao mesmo tempo. No
`completo` sem --only, cada sessão roda num processo próprio (o grupo jogável, o master e, assim
que a ponte captura.sav fica pronta, as sessões da ROM de teste; shiny e creche divididos em
partes) e tudo é juntado na ordem do sequencial. No `rapido`, a checagem de textos roda ao lado
do emulador. ESTEIRA_JOBS=1 (ou --only) é o modo sequencial de sempre.
Sai com 0 se nenhum resultado for `falha` (avisos não reprovam) e 1 caso contrário. Sem
`--starter`, o inicial é o da vez no rodízio (esteira/rotation.py), que só avança quando a
execução termina verde: um vermelho repete o mesmo inicial na próxima.
"""

import argparse
import json
import multiprocessing
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from esteira.check_build import check_build
from esteira.check_text import check_text
from esteira.emu import EmulatorError, WindowClosed
from esteira.refs import (DEFAULT_REFS_DIR, KEY_POINTS, SHARED_POINTS, SHARED_REFS, approve_refs,
                          compare_ref)
from esteira.report import VIDEO_NAME, write_report
from esteira.result import Result, StepTimeout, Suite
from esteira.rotation import STARTERS, peek_next_starter, record_starter
from esteira.scenarios import REPO_ROOT, ScenarioContext, open_context
from esteira.scenarios.full_evolutions import run_full_evolutions
from esteira import paralelo
from esteira.scenarios.full_breeding import (BREEDING_PARTS, merge_breeding,   # Hack 6
                                             run_full_breeding)
from esteira.scenarios.full_egg import run_full_egg              # Hack 6
from esteira.scenarios.full_clock import run_full_clock          # Hack 7
# Hack 7 — frente E
from esteira.scenarios.full_weather_gfx import run_full_weather_gfx
from esteira.scenarios.full_encounters import run_full_encounters  # Hack 7 — frente B
from esteira.scenarios.full_post_league import run_full_post_league  # Hack 7 — frente C
from esteira.scenarios.full_national_dex import run_full_national_dex   # Hack 7 — frente C
from esteira.scenarios.full_day_night_evo import run_full_day_night_evo  # Hack 7 - frente D
from esteira.scenarios.full_summary_friendship import run_full_summary_friendship  # Hack 7 - frente D
from esteira.scenarios.full_weather import run_full_weather      # Hack 7 frente A (clima)
from esteira.scenarios.full_novidades import (run_full_novidades,   # tela de novidades
                                             run_full_novidades_first_offer)
from esteira.scenarios.full_ritmo import run_full_pace             # Hack 2 (ritmo do jogo)
from esteira.scenarios.full_battle_weather_visual import run_full_battle_weather_visual  # POK-15
from esteira.scenarios.full_fisico_fada import run_full_fisico_fada  # POK-43, 45
from esteira.scenarios.full_conquistas import run_full_conquistas  # POK-44
from esteira.scenarios.full_revanches import run_full_revanches  # POK-42
from esteira.scenarios.full_forest_brock import run_full_forest_brock
from esteira.scenarios.full_master import run_full_master
from esteira.scenarios.full_pc import run_full_pc
from esteira.scenarios.full_screen_tour import run_full_screen_tour
from esteira.scenarios.full_shiny import SHINY_PARTS, merge_shiny, run_full_shiny
from esteira.scenarios.full_summary_evolution import run_full_summary_evolution
from esteira.scenarios.full_summary_ivs import run_full_summary_ivs
from esteira.scenarios.quick_catch_save import run_catch_save
from esteira.scenarios.quick_opening import run_opening
from esteira.scenarios.quick_route1 import run_route1
from esteira.video import VideoRecorder

REFS_DIR = DEFAULT_REFS_DIR
STATE_PATH = str(REPO_ROOT / "roms" / "estado-esteira.json")   # produção; testes sobrescrevem
EXCEPTIONS_PATH = REPO_ROOT / "test" / "excecoes.json"
STATIC_CHECKS = ("build", "texto")
PLAYABLE, TEST, HOST = "playable", "test", "host"   # ROM do cenário (HOST: sem emulador)
DEFAULT_ROM_TEST = str(REPO_ROOT / "pokefirered_switch_test.gba")
DEFAULT_ELF_TEST = str(REPO_ROOT / "pokefirered_switch_test.elf")
DEFAULT_ROM = str(REPO_ROOT / "pokefirered_switch.gba")
DEFAULT_ELF = str(REPO_ROOT / "pokefirered_switch.elf")
WATCH_CHECKPOINT_ROOT = REPO_ROOT / "test" / "out"   # onde as execuções deixam estados/<ponto>.ss


@dataclass
class ScenarioSpec:
    """Um cenário na cadeia de uma sessão de emulador.

    Cenários da mesma ROM (`rom`: PLAYABLE ou TEST) rodam em sequência numa única sessão: o
    primeiro do grupo começa do boot e `run(ctx)` de cada um continua do estado que o anterior
    deixou. Exceção: um cenário com `save_from` abre uma sessão nova da ROM dele (um grupo
    próprio, com os que vierem depois sem `save_from`). `needs` é o checkpoint
    (OUT/estados/<needs>.ss, gravado pelo cenário anterior do mesmo grupo) de onde o cenário
    pode recomeçar com `--only`; None = só começa do boot.
    Checkpoints nunca valem entre ROMs diferentes. `rom=HOST`: roda fora do emulador (ctx só
    com `suite`, `out_dir` e `starter`; `emu`, `game` etc. são None), sem ROM nem checkpoint.

    `save_from` (só na ROM de teste; abre um grupo/sessão nova): nome do cenário da ROM jogável
    cujo save do jogo (.sav) a sessão de teste carrega ao ligar — savestates não valem entre
    builds, o .sav vale. Logo que esse cenário termina sem falha, o save do jogo da memória é
    gravado (emu.flush_save) e copiado para OUT/<save_from>.sav (+ OUT/<save_from>.sav.json com
    o inicial), antes dos cenários jogáveis seguintes (que podem salvar o jogo ou mudar de
    mapa); se a cópia falhar, o cenário vira `falha`. O grupo jogável roda antes (ordem de
    FULL_SCENARIOS). Se o cenário estava na execução e não deixou o .sav, o grupo de teste vira
    `aviso` "não rodou". Com `--only` de um
    cenário da ROM de teste, usa o OUT/<save_from>.sav de uma execução anterior na mesma pasta
    (`rapido` também o deixa); sem ele, `falha` explicando o que rodar.

    `parts`/`merge` (só num cenário que é o grupo inteiro, com `save_from`): no modo paralelo
    (ESTEIRA_JOBS > 1, esteira/paralelo.py) o cenário roda em `parts` sessões ao mesmo tempo
    (ctx.part = 0..parts-1, cada uma com a sua fatia do N) e `merge(resultados de cada parte)`
    devolve os resultados na ordem do sequencial, com as faixas aplicadas ao total. No modo
    sequencial (ESTEIRA_JOBS=1) e com `--only`, roda inteiro numa sessão só.
    """
    name: str
    run: Callable[[ScenarioContext], None]
    needs: str | None = None
    rom: str = PLAYABLE
    save_from: str | None = None
    parts: int = 1
    merge: Callable[[list[list[Result]]], list[Result]] | None = None


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
# (test_cli.py::test_registro_dos_cenarios_completos confere a ordem). O `evolucoes`, o
# `resumo_evolucao` e o `resumo_ivs` também partem desse .sav, cada um numa sessão própria da ROM de teste
# (save_from abre sessão nova): rodam sozinhos com `--only <nome>` e não herdam o que o
# shiny (ou o outro) fez (Dex Nacional, Shiny Charm, time de teste). No modo paralelo cada
# sessão de teste é um processo; o shiny e o creche, `parts` processos cada (ver ScenarioSpec).
FULL_SCENARIOS: list[ScenarioSpec] = [
    ScenarioSpec("pc", run_full_pc, needs="save"),
    ScenarioSpec("telas", run_full_screen_tour, needs="pc"),
    ScenarioSpec("floresta_brock", run_full_forest_brock, needs="telas"),
    ScenarioSpec("master", run_full_master, rom=HOST),
    ScenarioSpec("shiny", run_full_shiny, rom=TEST, save_from="captura",
                 parts=SHINY_PARTS, merge=merge_shiny),
    ScenarioSpec("evolucoes", run_full_evolutions, rom=TEST, save_from="captura"),
    ScenarioSpec("resumo_evolucao", run_full_summary_evolution, rom=TEST, save_from="captura"),
    ScenarioSpec("resumo_ivs", run_full_summary_ivs, rom=TEST, save_from="captura"),
    ScenarioSpec("creche", run_full_breeding, rom=TEST, save_from="captura",    # Hack 6
                 parts=BREEDING_PARTS, merge=merge_breeding),
    ScenarioSpec("ovo", run_full_egg, rom=TEST, save_from="captura"),          # Hack 6
    ScenarioSpec("relogio", run_full_clock, rom=TEST, save_from="captura"),    # Hack 7
    # Hack 7 — frente E
    ScenarioSpec("clima_visual", run_full_weather_gfx, rom=TEST, save_from="captura"),
    ScenarioSpec("encontros", run_full_encounters, rom=TEST, save_from="captura"),  # Hack 7 — frente B
    ScenarioSpec("dex_nacional", run_full_national_dex, rom=TEST, save_from="captura"),  # Hack 7 — frente C
    ScenarioSpec("pos_liga", run_full_post_league, rom=TEST, save_from="captura"),  # Hack 7 — frente C
    # Hack 7 - frente D
    ScenarioSpec("evo_dia_noite", run_full_day_night_evo, rom=TEST, save_from="captura"),
    ScenarioSpec("resumo_amizade", run_full_summary_friendship, rom=TEST, save_from="captura"),
    ScenarioSpec("clima", run_full_weather, rom=TEST, save_from="captura"),    # Hack 7 frente A
    # tela de novidades do Carvalho: o percurso na ROM de teste e o SIM logo depois do inicial na
    # jogável (do checkpoint `abertura`; último do grupo jogável, não muda os checkpoints dos outros)
    ScenarioSpec("novidades", run_full_novidades, rom=TEST, save_from="captura"),
    ScenarioSpec("ritmo", run_full_pace, rom=TEST, save_from="captura"),       # Hack 2: andar e correr por input
    ScenarioSpec("clima_batalha", run_full_battle_weather_visual, rom=TEST, save_from="captura"),  # POK-15
    ScenarioSpec("fisico_fada", run_full_fisico_fada, rom=TEST, save_from="captura"),  # POK-43, 45
    ScenarioSpec("conquistas", run_full_conquistas, rom=TEST, save_from="captura"),  # POK-44
    ScenarioSpec("revanches", run_full_revanches, rom=TEST, save_from="captura"),  # POK-42
    ScenarioSpec("novidades_inicial", run_full_novidades_first_offer, needs="abertura"),
]
# Cenários do modo completo que o `assistir --cenario` mostra numa janela (ROM de teste, a
# partir do .sav da ponte). O shiny e o creche ficam de fora: centenas de milhares de sorteios
# em tempo real levariam horas.
WATCH_FULL_SCENARIOS = ("evolucoes", "resumo_evolucao", "resumo_ivs", "ovo",
                        "relogio",  # Hack 7
                        "encontros",  # Hack 7 — frente B
                        "dex_nacional", "pos_liga",  # Hack 7 — frente C
                        "evo_dia_noite", "resumo_amizade",  # Hack 7 - frente D
                        "clima",  # Hack 7 — frente A
                        "novidades",  # tela de novidades
                        "ritmo",  # Hack 2
                        "clima_batalha",  # POK-15
                        "fisico_fada",  # POK-43, 45
                        "conquistas",  # POK-44
                        "revanches")  # POK-42


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
    unusable = _build_checks(args, suite, exceptions)
    if args.only in (None, "texto"):
        for r in _text_checks(exceptions):
            suite.add(r)
    return unusable


def _build_checks(args: argparse.Namespace, suite: Suite, exceptions: dict) -> bool:
    """A checagem do log de build; True se ele mostra que não há ROM jogável utilizável."""
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
    return unusable


def _text_checks(exceptions: dict) -> list[Result]:
    results = check_text(str(REPO_ROOT), exceptions)
    return results or [Result("texto/estático", "ok", "nenhum problema nos textos do jogo")]


def _static_failure(exc: BaseException) -> Result:
    """Bug numa checagem estática: reprova com diagnóstico no relatório (um traceback solto
    viraria "falha de infraestrutura" a cada build)."""
    return Result("esteira/checagens-estáticas", "falha",
                  f"erro inesperado: {type(exc).__name__}: {exc}\n"
                  f"{''.join(traceback.format_exception(exc)).strip()}")


def _text_task(exceptions: dict) -> list[Result]:
    """A checagem de textos num processo à parte (modo paralelo), ao lado do emulador."""
    try:
        return _text_checks(exceptions)
    except Exception as exc:  # noqa: BLE001 - igual ao modo sequencial
        return [_static_failure(exc)]


def _groups(specs: list[ScenarioSpec], only: str | None) -> list[tuple[str, list[ScenarioSpec]]]:
    """Agrupa os cenários em sessões de emulador: por ROM, na ordem da primeira aparição; um
    cenário com `save_from` abre uma sessão nova da ROM dele. Com `only`, só o grupo dele,
    cortado nele (o que vem antes no grupo é pré-requisito)."""
    groups: list[tuple[str, list[ScenarioSpec]]] = []
    current: dict[str, list[ScenarioSpec]] = {}
    for s in specs:
        if s.save_from is not None or s.rom not in current:
            current[s.rom] = []
            groups.append((s.rom, current[s.rom]))
        current[s.rom].append(s)
    if only is not None:
        for rom, group in groups:
            names = [s.name for s in group]
            if only in names:
                return [(rom, group[:names.index(only) + 1])]
    return groups


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
                   tempos: dict[str, float], bridges: set[str] = frozenset(),
                   on_bridge: Callable[[str], None] | None = None) -> None:
    """Roda a cadeia de um grupo; depois de um cenário com falha, os seguintes viram `aviso`.
    Só falhas surgidas durante a cadeia contam (as checagens estáticas não interrompem nada).
    Um cenário de `bridges` que termina sem falha deixa o .sav da ponte (_write_bridge); se a
    ponte não puder ser gravada, ele vira `falha`. `on_bridge(nome)`: chamado logo que a ponte
    fica pronta (modo paralelo: libera as sessões da ROM de teste)."""
    chain = _chain(group, only, ctx)
    # POK-44: sessão da ROM de teste = aviso das conquistas em silêncio (scenarios/base.silenciar_avisos)
    ctx.conq_silencio = any(spec.rom == TEST for spec in group)
    suite = ctx.suite
    out = Path(ctx.out_dir)
    for spec in chain:   # produtor na cadeia que vai rodar: o .sav antigo não vale mais,
        if spec.name in bridges:   # mesmo que a cadeia pare antes dele
            for path in _bridge_paths(out, spec.name):
                path.unlink(missing_ok=True)
    for pos, spec in enumerate(chain):
        before = sum(1 for r in suite.results if r.status == "falha")
        print(f"[rodando] {spec.name}...", flush=True)
        start = time.monotonic()
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
            else:
                if on_bridge is not None:
                    on_bridge(spec.name)
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
    """Telas desta execução contra as referências do inicial (e as COMUM, que valem para os
    três: refs.SHARED_POINTS)."""
    for points, folder in ((KEY_POINTS, starter), (SHARED_POINTS, SHARED_REFS)):
        for point in points:
            shot = out / "telas" / f"{point}.png"
            if shot.is_file() and shot.stat().st_mtime >= since:
                suite.add(compare_ref(point, folder, str(shot), REFS_DIR))


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
    if "semente" in meta:
        print(f"sementes das partes do shiny/creche: ESTEIRA_SEED={meta['semente']} "
              "(repita com ela para reproduzir as contagens)")
    print(f"relatório: {report}")


def _save_video(recorder: VideoRecorder, path: Path, suite: Suite,
                tempos: dict[str, float]) -> None:
    """Codifica o vídeo da execução; problema aqui é aviso (o vídeo é conveniência, não teste)."""
    start = time.monotonic()
    try:
        recorder.save(str(path))
    except Exception as exc:  # noqa: BLE001
        path.unlink(missing_ok=True)
        suite.add(Result("video/gravacao", "aviso", f"vídeo não gravado: {type(exc).__name__}: {exc}"))
        return
    tempos["vídeo (codificação)"] = time.monotonic() - start


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
    # Um vídeo só por execução, com todas as sessões de emulador em sequência (jogável e teste);
    # o de uma execução anterior na mesma pasta não vale.
    video_path = out / VIDEO_NAME
    video_path.unlink(missing_ok=True)
    jobs = paralelo.jobs()
    parallel = jobs > 1 and args.only is None
    salt = None
    if parallel and args.modo == "completo":
        salt = paralelo.run_salt()
        starter, rotated, nao_testada, recorder = _run_parallel(args, specs, out, suite, tempos,
                                                                jobs, started_wall, salt)
    else:
        recorder = None if args.sem_video else VideoRecorder()
        starter, rotated, nao_testada = _run_sequential(args, specs, out, suite, tempos,
                                                        recorder, jobs if parallel else 1,
                                                        started_wall)

    if recorder is not None and recorder.has_activity():
        _save_video(recorder, video_path, suite, tempos)

    meta = {"inicial": starter or "-", "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit": _git_commit(), "modo": args.modo, "tempos": tempos,
            "tempo_total": time.monotonic() - start, "nao_testada": nao_testada,
            "processos": jobs}
    if salt is not None:   # sementes das partes do shiny/creche: ESTEIRA_SEED reproduz
        meta["semente"] = f"0x{salt:08x}"
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
    report = write_report(suite, str(out), meta)
    _print_summary(suite, meta, report)
    if suite.failed():
        return 1
    if rotated:   # verde: o próximo é o seguinte do rodízio (vermelho repete este inicial)
        try:
            record_starter(args.state, starter)
        except OSError as exc:
            print(f"aviso: rodízio de iniciais não gravado em {args.state}: {exc}", file=sys.stderr)
    return 0


def _run_sequential(args: argparse.Namespace, specs: list[ScenarioSpec], out: Path, suite: Suite,
                    tempos: dict[str, float], recorder: VideoRecorder | None, jobs: int,
                    started_wall: float) -> tuple[str | None, bool, bool]:
    """Os grupos um depois do outro, neste processo (o modo de sempre; também o `rapido` e o
    `--only`). Com `jobs` > 1 só a checagem de textos vai para um processo à parte, ao lado do
    emulador (o resultado entra no mesmo lugar do relatório). Devolve (inicial, se veio do
    rodízio, se a ROM jogável ficou sem teste)."""
    nao_testada = False
    starter: str | None = args.starter   # sem --starter, só sai do rodízio quando o emulador roda
    text_pool: paralelo.Pool | None = None
    text_at = 0
    try:
        try:
            if jobs > 1:
                exceptions = json.loads(EXCEPTIONS_PATH.read_text(encoding="utf-8"))
                unusable = _build_checks(args, suite, exceptions)
                if args.only in (None, "texto"):
                    text_pool = paralelo.Pool(jobs)   # fork antes do emulador (sem threads ainda)
                    text_pool.submit("texto", lambda: _text_task(exceptions))
                    text_pool.step(timeout=0)
                    text_at = len(suite.results)
            else:
                unusable = _static_checks(args, suite)
        except Exception as exc:  # noqa: BLE001 - bug numa checagem reprova com diagnóstico no relatório
            unusable = False      # (um traceback solto viraria "falha de infraestrutura" a cada build)
            suite.add(Result("esteira/checagens-estáticas", "falha",
                             f"erro inesperado: {type(exc).__name__}: {exc}\n"
                             f"{traceback.format_exc().strip()}"))
        starter, rotated, nao_testada = _run_groups_inline(args, specs, out, suite, tempos,
                                                           recorder, unusable, started_wall)
        if text_pool is not None:
            suite.results[text_at:text_at] = _wait_text(text_pool)
    finally:
        if text_pool is not None:
            text_pool.close()
    return starter, rotated, nao_testada


def _wait_text(pool: paralelo.Pool) -> list[Result]:
    while pool.busy():
        for done in pool.step():
            if done.error is not None:
                raise RuntimeError(f"checagem de textos: {done.error}")
            return done.value
    raise RuntimeError("checagem de textos não devolveu resultado")


def _run_groups_inline(args: argparse.Namespace, specs: list[ScenarioSpec], out: Path,
                       suite: Suite, tempos: dict[str, float], recorder: VideoRecorder | None,
                       unusable: bool, started_wall: float) -> tuple[str | None, bool, bool]:
    nao_testada = False
    starter: str | None = args.starter
    rotated = False   # o inicial veio do rodízio: só é gravado se a execução terminar verde
    if args.only in (None, *[s.name for s in specs]):
        roms = {PLAYABLE: (args.rom, args.elf, "ROM jogável"),
                TEST: (args.rom_test, args.elf_test, "ROM de teste")}
        groups = _groups(specs, args.only)
        scheduled = {s.name for _, group in groups for s in group}
        producers = _save_producers()
        # Execução inteira: o .sav de outra execução não vale se o produtor está nesta, mesmo
        # que ele nem chegue a rodar (falha antes, ROM ausente) — o grupo de teste não pode
        # partir do .sav velho. Com --only o grupo jogável pode recomeçar de um checkpoint
        # depois do produtor: aí quem apaga é _run_scenarios, pela cadeia que vai rodar mesmo.
        if args.only is None:
            for producer in producers & scheduled:
                for path in _bridge_paths(out, producer):
                    path.unlink(missing_ok=True)
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
                starter = peek_next_starter(args.state)
                rotated = True
            bridges = producers if kind == PLAYABLE else set()
            with open_context(rom, elf, str(out), starter, suite, save_from=save_from,
                              recorder=recorder) as ctx:
                _run_scenarios(group, ctx, args.only, tempos, bridges)
        if starter is not None:
            _compare_screens(suite, out, starter, started_wall)
    return starter, rotated, nao_testada


# --- modo completo em paralelo (ESTEIRA_JOBS > 1; ver esteira/paralelo.py) --------------------
#
# Cada grupo (sessão) vira uma tarefa num processo próprio, com o seu emulador e a sua pasta
# (OUT/sessoes/<nome>/: .sav, estados, telas); o grupo jogável usa o próprio OUT, como no
# sequencial. Ordem de partida: textos, grupo jogável e master logo de cara (o master com as
# vagas que sobram, `make -j`); as sessões da ROM de teste esperam a ponte (captura.sav), que o
# grupo jogável grava logo depois do `captura` e avisa (on_bridge). Um cenário com `parts`
# vira `parts` tarefas. No fim tudo é juntado na ordem do sequencial: resultados, tempos e o
# vídeo (quadros de cada sessão, na ordem dos grupos). Nunca mais de `jobs` vagas ocupadas.

SESSIONS_DIR = "sessoes"
# Duração típica (s) de cada cenário: as tarefas mais longas saem primeiro quando há vagas.
_EXPECTED_SECONDS = {"shiny": 500, "creche": 220, "floresta_brock": 90, "evolucoes": 30,
                     "master": 25}


def _session_task(group: list[ScenarioSpec], rom: str, elf: str, out_dir: str, starter: str,
                  save_from: str | None, video: bool, bridges: set[str], part: int, parts: int,
                  bridge_event=None, salt: int = 0) -> dict:
    """Roda no processo filho: uma sessão de emulador com a cadeia do grupo."""
    suite = Suite()
    tempos: dict[str, float] = {}
    recorder = VideoRecorder(stream=False) if video else None
    on_bridge = (lambda name: bridge_event.set()) if bridge_event is not None else None
    with open_context(rom, elf, out_dir, starter, suite, save_from=save_from,
                      recorder=recorder) as ctx:
        ctx.part, ctx.parts, ctx.seed = part, parts, salt
        _run_scenarios(group, ctx, None, tempos, bridges, on_bridge)
    return {"results": suite.results, "tempos": tempos,
            "video": recorder.export() if recorder is not None else None}


def _host_task(group: list[ScenarioSpec], out_dir: str, starter: str) -> dict:
    suite = Suite()
    tempos: dict[str, float] = {}
    host = ScenarioContext(emu=None, game=None, controller=None, nav=None, suite=suite,
                           consts=None, out_dir=out_dir, starter=starter)
    _run_scenarios(group, host, None, tempos)
    return {"results": suite.results, "tempos": tempos, "video": None}


def _adopt_files(sub: Path, out: Path, results: list[Result]) -> None:
    """Traz as telas e os estados de uma sessão (OUT/sessoes/<nome>/) para OUT/telas e
    OUT/estados, onde o sequencial os deixa (comparação com as referências, `aprovar`), e
    corrige os caminhos nos resultados. O resto (evidências de tempo esgotado) fica onde está."""
    moved: dict[str, str] = {}
    for folder in ("telas", "estados"):
        src = sub / folder
        if not src.is_dir():
            continue
        (out / folder).mkdir(parents=True, exist_ok=True)
        for path in src.iterdir():
            dest = out / folder / path.name
            os.replace(path, dest)
            moved[str(path)] = str(dest)
        try:
            src.rmdir()
        except OSError:
            pass
    for r in results:
        r.images = [moved.get(p, p) for p in r.images]
        if r.state is not None:
            r.state = moved.get(r.state, r.state)
        for folder in ("telas", "estados"):   # caminhos citados no texto do detalhe
            r.detail = r.detail.replace(f"{sub / folder}/", f"{out / folder}/")


def _drop_session_dir(sub: Path, helper: bool) -> None:
    """O .sav da sessão não serve para nada depois; pasta vazia some (evidências de tempo
    esgotado ficam). As telas e os estados das partes > 0 (repetem os da parte 0) saem."""
    (sub / "esteira.sav").unlink(missing_ok=True)
    if helper:
        for folder in ("telas", "estados"):
            shutil.rmtree(sub / folder, ignore_errors=True)
    for path in (sub, sub.parent):
        try:
            path.rmdir()
        except OSError:
            break


def _run_parallel(args: argparse.Namespace, specs: list[ScenarioSpec], out: Path, suite: Suite,
                  tempos: dict[str, float], jobs: int, started_wall: float, salt: int = 0
                  ) -> tuple[str | None, bool, bool, VideoRecorder | None]:
    nao_testada = False
    starter: str | None = args.starter
    rotated = False
    video = not args.sem_video
    roms = {PLAYABLE: (args.rom, args.elf, "ROM jogável"),
            TEST: (args.rom_test, args.elf_test, "ROM de teste")}
    groups = _groups(specs, None)
    scheduled = {s.name for _, group in groups for s in group}
    producers = _save_producers()
    for producer in producers & scheduled:   # o .sav de outra execução não vale (ver sequencial)
        for path in _bridge_paths(out, producer):
            path.unlink(missing_ok=True)

    static: list[Result] = []           # build (aqui) + textos (tarefa)
    texts: list[Result] = []
    slots_out: list[list[Result]] = [[] for _ in groups]          # resultados de cada grupo
    parts_out: dict[int, list[list[Result] | None]] = {}          # grupo dividido: por parte
    group_tempos: list[dict[str, list[float]]] = [{} for _ in groups]
    videos: dict[tuple[int, int], dict] = {}                      # (grupo, parte) -> quadros
    tasks: dict[str, tuple[int, int, Path | None]] = {}           # chave -> (grupo, parte, pasta)
    waiting: list[int] = []                                       # grupos esperando a ponte
    bridge_event = multiprocessing.get_context("fork").Event()
    playable_running = False

    static_suite = Suite()
    exceptions = None
    try:
        exceptions = json.loads(EXCEPTIONS_PATH.read_text(encoding="utf-8"))
        unusable = _build_checks(args, static_suite, exceptions)
    except Exception as exc:  # noqa: BLE001 - como no sequencial
        unusable = False
        static_suite.add(_static_failure(exc))
    static = static_suite.results

    print(f"[paralelo] até {jobs} processos ao mesmo tempo (ESTEIRA_JOBS); sementes das partes: "
          f"{paralelo.seed_label(salt)}", flush=True)
    with paralelo.Pool(jobs) as pool:
        if exceptions is not None:
            pool.submit("texto", lambda: _text_task(exceptions), priority=1000)

        def submit_session(index: int, kind: str, group: list[ScenarioSpec],
                           save_from: str | None) -> None:
            rom, elf, _ = roms[kind]
            spec = group[0]
            parts = spec.parts if (len(group) == 1 and spec.parts > 1 and spec.merge) else 1
            if parts > 1:
                parts_out[index] = [None] * parts
            for part in range(parts):
                if kind == PLAYABLE:
                    sub, key = None, "jogavel"
                else:
                    name = spec.name if parts == 1 else f"{spec.name}-parte{part + 1}"
                    sub, key = out / SESSIONS_DIR / name, name
                bridges = producers if kind == PLAYABLE else set()
                event = bridge_event if kind == PLAYABLE else None
                expected = max(_EXPECTED_SECONDS.get(s.name, 10) for s in group) / parts
                if kind == PLAYABLE:
                    expected = 10_000    # caminho crítico: sai antes de tudo
                pool.submit(key, (lambda g=group, r=rom, e=elf, d=str(sub or out), sf=save_from,
                                  b=bridges, p=part, n=parts, ev=event:
                                  _session_task(g, r, e, d, starter, sf, video and p == 0, b, p, n,
                                                ev, salt)),
                            priority=expected)
                tasks[key] = (index, part, sub)

        def release(bridge_ok: bool) -> None:
            for index in waiting:
                kind, group = groups[index]
                producer = group[0].save_from
                save, _ = _bridge_paths(out, producer)
                if bridge_ok and save.is_file():
                    submit_session(index, kind, group, str(save))
                else:
                    status, why = _missing_save(producer, producer in scheduled, save, out)
                    slots_out[index].append(Result(f"cenario/{group[0].name}", status, why))
                    _not_run(_Collector(slots_out[index]), group[1:])
            waiting.clear()

        for index, (kind, group) in enumerate(groups):
            if kind == HOST:
                slots = max(1, jobs - 2)   # o que sobra ao lado dos textos e do grupo jogável
                key = f"host-{group[0].name}"
                pool.submit(key, lambda g=group, s=starter or "-": _host_task(g, str(out), s),
                            slots=slots, priority=_EXPECTED_SECONDS.get(group[0].name, 10),
                            env={paralelo.MAKE_JOBS_ENV: str(min(slots, jobs))})
                tasks[key] = (index, 0, None)
                continue
            rom, elf, label = roms[kind]
            missing = [p for p in (rom, elf) if not Path(p).is_file()]
            bad_build = unusable and kind == PLAYABLE
            if bad_build or missing:
                if kind == PLAYABLE:
                    nao_testada = True
                why = ("o log de build mostra que a ROM não foi gerada" if bad_build
                       else "arquivo não encontrado: " + ", ".join(missing))
                slots_out[index].append(Result(f"emulador/rom-{kind}", "falha",
                                               f"{label} não testada: {why}"))
                continue
            if group[0].save_from is not None:
                waiting.append(index)
                continue
            if starter is None:
                starter = peek_next_starter(args.state)
                rotated = True
            submit_session(index, kind, group, None)
            if kind == PLAYABLE:
                playable_running = True
        if waiting and not playable_running:
            release(False)

        while pool.busy() or waiting:
            for done in pool.step():
                if done.error is not None:
                    raise RuntimeError(f"tarefa '{done.key}' do modo paralelo: {done.error}")
                if done.key == "texto":
                    texts = done.value
                    continue
                index, part, sub = tasks[done.key]
                value = done.value
                results: list[Result] = value["results"]
                if sub is not None:
                    if part == 0:
                        _adopt_files(sub, out, results)
                    _drop_session_dir(sub, helper=part > 0)
                for name, seconds in value["tempos"].items():
                    group_tempos[index].setdefault(name, []).append(seconds)
                if value["video"] is not None:
                    videos[(index, part)] = value["video"]
                if index in parts_out:
                    parts_out[index][part] = results
                else:
                    slots_out[index].extend(results)
                if done.key == "jogavel" and waiting:
                    release(bridge_event.is_set())
            if waiting and bridge_event.is_set():
                release(True)
            if waiting and not pool.busy():   # nada mais vai gravar a ponte
                release(False)
        peak = pool.peak

    for index, parts in parts_out.items():
        spec = groups[index][1][0]
        slots_out[index].extend(spec.merge(parts))
    suite.results.extend(static)
    suite.results.extend(texts)
    for index in range(len(groups)):
        suite.results.extend(slots_out[index])
        for name, values in group_tempos[index].items():
            tempos[name] = max(values)
    print(f"[paralelo] pico de {peak} vaga(s) ocupada(s) de {jobs}", flush=True)
    if starter is not None:
        _compare_screens(suite, out, starter, started_wall)
    recorder = None
    if video and videos:
        recorder = _merge_videos([videos[k] for k in sorted(videos)])
    return starter, rotated, nao_testada, recorder


class _Collector:
    """Uma lista de resultados com a cara de Suite (para _not_run)."""

    def __init__(self, results: list[Result]):
        self.results = results

    def add(self, result: Result) -> None:
        self.results.append(result)


def _merge_videos(exports: list[dict]) -> VideoRecorder:
    """Um gravador com os quadros de todas as sessões, na ordem dada (a dos grupos), no mesmo
    espaçamento para todas (o maior entre elas): o vídeo fica como o do sequencial."""
    every = max((e["every"] for e in exports if e["frames"]), default=8)
    recorder = VideoRecorder(every=every)
    for export in exports:
        if export["failure"] is not None:
            recorder.fail(RuntimeError(export["failure"]))
        for pos, packed in export["frames"]:
            recorder.add_packed(pos, packed)
    return recorder


# --- assistir: os roteiros rápidos numa janela, em tempo real -------------------------------------

def _has_display() -> bool:
    """Há onde abrir a janela: WSLg define DISPLAY/WAYLAND_DISPLAY. SDL_VIDEODRIVER só vale
    como `dummy` (testes, sem tela); qualquer outro driver precisa de um display de verdade."""
    return (any(os.environ.get(v) for v in ("DISPLAY", "WAYLAND_DISPLAY"))
            or os.environ.get("SDL_VIDEODRIVER") == "dummy")


def _load_watch_checkpoint(ctx: ScenarioContext, name: str, rom: str,
                           wanted: str | None) -> str | None:
    """Carrega no emulador o checkpoint `name` mais recente deixado por uma execução em
    test/out/*/estados/ (ignora os mais velhos que a ROM: savestate vale só para o mesmo build)
    cujo inicial seja `wanted` (qualquer um, se None). Devolve o inicial, ou None."""
    rom_time = Path(rom).stat().st_mtime
    found = [p for p in Path(WATCH_CHECKPOINT_ROOT).glob(f"*/estados/{name}.ss")
             if p.stat().st_mtime >= rom_time]
    for path in sorted(found, key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            ctx.emu.load_state(str(path))
        except WindowClosed:
            raise
        except EmulatorError:   # estado corrompido ou incompatível: tenta o próximo
            continue
        ctx.emu.keys(0)
        party = ctx.game.party()
        for starter in STARTERS:
            if party and party[0].species == ctx.consts.species(starter) and wanted in (None, starter):
                return starter
    return None


def _find_watch_save(producer: str, wanted: str | None) -> tuple[str, str] | None:
    """O save do jogo da ponte (`<producer>.sav` + `.sav.json`) mais recente deixado por uma
    execução em test/out/*/ (o `make test-quick` e todo `make firered_switch` deixam um), do
    inicial `wanted` (qualquer um, se None). Devolve (caminho, inicial) ou None. O .sav vale
    entre builds (ao contrário dos savestates): não precisa ser mais novo que a ROM."""
    found = sorted(Path(WATCH_CHECKPOINT_ROOT).glob(f"*/{producer}.sav"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    for save in found:
        starter = _bridge_starter(save.with_name(save.name + ".json"))
        if starter is not None and wanted in (None, starter):
            return str(save), starter
    return None


def _watch_chain(args: argparse.Namespace) -> list[ScenarioSpec]:
    """O que assistir: o cenário do modo completo de `--cenario`, ou os roteiros rápidos
    (todos, ou só os que vêm depois de `--from`)."""
    if args.cenario is not None:
        return [next(s for s in FULL_SCENARIOS if s.name == args.cenario)]
    if args.checkpoint is None:
        return list(QUICK_SCENARIOS)
    first = next(i for i, s in enumerate(QUICK_SCENARIOS) if s.needs == args.checkpoint)
    return QUICK_SCENARIOS[first:]


def run_watch(args: argparse.Namespace) -> int:
    """`assistir`: roda o modo rápido com janela. Save temporário (apagado no fim), nada em
    roms/ e o rodízio de iniciais só é lido, nunca gasto. Com `--cenario`, roda esse cenário
    do modo completo na ROM de teste, a partir de uma cópia do save da ponte (o
    `<save_from>.sav` mais recente de test/out/*/). Sai com 0 (terminou ou a janela foi
    fechada), 1 (um roteiro falhou) ou 2 (sem janela/ROM/checkpoint/save)."""
    if not _has_display():
        print("assistir precisa de uma janela, mas DISPLAY/WAYLAND_DISPLAY não existem. No WSL o "
              "WSLg fornece isso (Windows 11): rode `wsl --update`, feche o WSL com "
              "`wsl --shutdown` e abra de novo.", file=sys.stderr)
        return 2
    chain = _watch_chain(args)
    if args.cenario is not None:
        rom, elf, build = args.rom_test, args.elf_test, "make firered_switch TESTBUILD=1"
    else:
        rom, elf, build = args.rom, args.elf, "make firered_switch"
    missing = [p for p in (rom, elf) if not Path(p).is_file()]
    if missing:
        print("arquivo não encontrado: " + ", ".join(missing) + f" (rode `{build}`)",
              file=sys.stderr)
        return 2
    starter = args.starter or peek_next_starter(args.state)
    save_from = None
    if args.cenario is not None:
        producer = chain[0].save_from
        found = _find_watch_save(producer, args.starter)
        if found is None:
            wanted = f" do inicial {args.starter}" if args.starter else ""
            print(f"nenhum save do jogo '{producer}.sav'{wanted} em {WATCH_CHECKPOINT_ROOT}/*/: "
                  f"o cenário '{args.cenario}' parte do save do fim do modo rápido; rode "
                  "`make test-quick` antes.", file=sys.stderr)
            return 2
        save_from, starter = found
    out = Path(tempfile.mkdtemp(prefix="esteira-assistir-"))
    suite = Suite()
    code = 0
    what = f"cenário {args.cenario}" if args.cenario else "roteiro rápido"
    try:
        with open_context(rom, elf, str(out), starter, suite, save_from=save_from,
                          window=True) as ctx:
            if args.checkpoint is not None:
                try:
                    found = _load_watch_checkpoint(ctx, args.checkpoint, args.rom, args.starter)
                except WindowClosed:
                    print("janela fechada: assistir encerrado.")
                    return 0
                if found is None:
                    wanted = f" do inicial {args.starter}" if args.starter else ""
                    print(f"nenhum estado '{args.checkpoint}'{wanted} utilizável em "
                          f"{WATCH_CHECKPOINT_ROOT}/*/estados/ (de uma execução depois do último "
                          "build da ROM): rode `make test-quick` antes, ou assista sem --from.",
                          file=sys.stderr)
                    return 2
                ctx.starter = found
            print(f"[assistindo] inicial {ctx.starter}; feche a janela (ou Esc) para encerrar",
                  flush=True)
            ctx.conq_silencio = any(spec.rom == TEST for spec in chain)   # POK-44, como em _run_scenarios
            for spec in chain:
                print(f"[assistindo] {spec.name}...", flush=True)
                try:
                    spec.run(ctx)
                except WindowClosed:
                    print("janela fechada: assistir encerrado.")
                    return 0
                except EmulatorError as exc:
                    if exc.returncode == -signal.SIGINT:   # Ctrl-C matou o runner antes do Python
                        raise KeyboardInterrupt from exc
                    print(f"o emulador terminou: {exc}", file=sys.stderr)
                    code = 1
                    break
                except Exception as exc:  # noqa: BLE001 - qualquer erro vira falha no resumo
                    suite.add(_fail_result(spec, exc))
                if suite.failed():
                    break
    except KeyboardInterrupt:
        print("interrompido (Ctrl-C).")
        return 130
    finally:
        keep = code != 0 or suite.failed()
        if not keep:
            shutil.rmtree(out, ignore_errors=True)
    for r in suite.results:
        if r.status != "ok":
            print(f"[{r.status}] {r.name}: {r.detail.splitlines()[0] if r.detail else ''}")
    if keep:
        print(f"assistir terminou com falha; evidências (telas, estados) em {out}")
        return 1
    oks = sum(1 for r in suite.results if r.status == "ok")
    print(f"assistir terminou: {what} concluído sem falhas ({oks} ok).")
    return 0


def write_untested_report(out_dir: str) -> str:
    """Relatório só com a faixa NÃO TESTADA (SKIP_TESTS=1): sem emulador e sem checagens."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / VIDEO_NAME).unlink(missing_ok=True)   # vídeo de outra execução não vale
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
                       help="força o inicial (não mexe no rodízio); padrão: o da vez, que "
                            "só avança se a execução passar")
        p.add_argument("--sem-video", action="store_true",
                       help=f"não grava {VIDEO_NAME} (a execução inteira em vídeo acelerado)")
        p.add_argument("--state", default=STATE_PATH, help=argparse.SUPPRESS)
    untested = sub.add_parser("nao-testada", help="só o relatório NÃO TESTADA (SKIP_TESTS=1)")
    untested.add_argument("--out", required=True)
    approve = sub.add_parser("aprovar", help="promove as telas de uma execução a referência")
    approve.add_argument("dir")
    watch = sub.add_parser(
        "assistir", help="roda o roteiro rápido numa janela, em velocidade normal, com som",
        description="Roda os roteiros rápidos (abertura, Rota 1, captura) numa janela do Windows "
                    "(WSLg), em velocidade normal e com som, para você assistir. Fora do "
                    "pipeline: usa um save temporário, não gera versão, não mexe em roms/ nem no "
                    "rodízio de iniciais. Feche a janela (ou Esc) para encerrar. Com --cenario, "
                    "mostra um cenário do modo completo na ROM de teste.")
    watch.add_argument("--starter", choices=STARTERS,
                       help="inicial a usar; padrão: o da vez no rodízio (sem gastá-lo)")
    start = watch.add_mutually_exclusive_group()
    start.add_argument("--from", dest="checkpoint",
                       choices=sorted({s.needs for s in QUICK_SCENARIOS if s.needs}),
                       help="começa deste ponto do roteiro rápido, usando o estado mais recente "
                            "deixado por `make test-quick` em test/out/*/estados/ (senão, do boot)")
    start.add_argument("--cenario", choices=WATCH_FULL_SCENARIOS,
                       help="em vez do roteiro rápido, este cenário do modo completo na ROM de "
                            "teste (--rom-test), a partir do save do fim do modo rápido mais "
                            "recente em test/out/*/ (o inicial é o desse save)")
    watch.add_argument("--rom", default=DEFAULT_ROM, help="ROM jogável (padrão: a da raiz do repo)")
    watch.add_argument("--elf", default=DEFAULT_ELF, help="ELF da ROM jogável (padrão: o da raiz)")
    watch.add_argument("--rom-test", default=DEFAULT_ROM_TEST,
                       help="ROM de teste, só com --cenario (padrão: pokefirered_switch_test.gba)")
    watch.add_argument("--elf-test", default=DEFAULT_ELF_TEST)
    watch.add_argument("--state", default=STATE_PATH, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.modo == "nao-testada":
        print(f"ROM NÃO TESTADA (sem emulador); relatório: {write_untested_report(args.out)}")
        return 0
    if args.modo == "assistir":
        return run_watch(args)
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
