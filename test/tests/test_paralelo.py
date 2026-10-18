"""Modo paralelo da esteira (ESTEIRA_JOBS > 1): teto de processos, partes de cenário, sementes
e o CLI juntando tudo na ordem do sequencial. Sem emulador (cenários falsos, como test_cli)."""

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import esteira.__main__ as cli
from esteira import paralelo
from esteira.__main__ import HOST, PLAYABLE, TEST, ScenarioSpec, main
from esteira.result import Result, Suite

# Os filhos são fork do processo do pytest, onde as threads de vídeo de testes anteriores (daemon,
# paradas na fila) continuam vivas; na esteira de verdade o fork acontece antes de qualquer thread.
pytestmark = pytest.mark.filterwarnings(
    "ignore:This process .* is multi-threaded:DeprecationWarning")


# --- paralelo.py ---------------------------------------------------------------------------------

@pytest.mark.parametrize("raw, want", [(None, 10), ("4", 4), ("1", 1), ("0", 10), ("x", 10),
                                       (" 12 ", 12), ("999", 64)])
def test_teto_vem_de_ESTEIRA_JOBS(monkeypatch, raw, want):
    if raw is None:
        monkeypatch.delenv("ESTEIRA_JOBS", raising=False)
    else:
        monkeypatch.setenv("ESTEIRA_JOBS", raw)
    assert paralelo.jobs() == want


def test_make_jobs_usa_as_vagas_da_tarefa_ou_o_teto(monkeypatch):
    monkeypatch.setenv("ESTEIRA_JOBS", "6")
    monkeypatch.delenv("ESTEIRA_MAKE_JOBS", raising=False)
    assert paralelo.make_jobs() == 6
    monkeypatch.setenv("ESTEIRA_MAKE_JOBS", "3")
    assert paralelo.make_jobs() == 3


@pytest.mark.parametrize("total, parts", [(200_000, 6), (4096, 3), (5, 3), (1024, 1)])
def test_fatias_somam_o_total(total, parts):
    shares = [paralelo.share(total, k, parts) for k in range(parts)]
    assert sum(shares) == total and max(shares) - min(shares) <= 1


def test_salto_do_gerador_bate_com_o_passo_a_passo():
    x = 0x1234_5678
    for _ in range(1000):
        x = (paralelo.RAND_MULT * x + paralelo.RAND_ADD) & 0xFFFFFFFF
    assert paralelo.lcg_jump(0x1234_5678, 1000) == x
    assert paralelo.lcg_jump(7, 0) == 7


def test_sementes_fixas_e_distintas():
    seeds = [paralelo.part_seed("shiny", k) for k in range(12)]
    assert len(set(seeds)) == 12
    assert seeds == [paralelo.part_seed("shiny", k) for k in range(12)]   # determinísticas
    assert paralelo.part_seed("creche", 0) != paralelo.part_seed("shiny", 0)
    # janelas disjuntas: a semente k+1 é a k depois de SEED_WINDOW passos
    assert paralelo.lcg_jump(seeds[0], paralelo.SEED_WINDOW) == seeds[1]
    with pytest.raises(ValueError):
        paralelo.part_seed("shiny", paralelo.MAX_SEED_INDEX)


def _stamp(folder: Path, name: str, seconds: float) -> str:
    start = time.time()
    time.sleep(seconds)
    (folder / f"{name}.json").write_text(json.dumps([start, time.time(), os.getpid()]))
    return name


def _overlaps(folder: Path) -> int:
    spans = [json.loads(p.read_text()) for p in folder.glob("*.json")]
    events = sorted([(s, 1) for s, _, _ in spans] + [(e, -1) for _, e, _ in spans])
    now = peak = 0
    for _, delta in events:
        now += delta
        peak = max(peak, now)
    return peak


def test_pool_nunca_passa_do_teto_e_devolve_os_valores(tmp_path):
    with paralelo.Pool(2) as pool:
        for i in range(7):
            pool.submit(f"t{i}", lambda i=i: _stamp(tmp_path, f"t{i}", 0.3))
        got = {}
        while pool.busy():
            for done in pool.step():
                assert done.error is None
                got[done.key] = done.value
        assert pool.peak <= 2
    assert got == {f"t{i}": f"t{i}" for i in range(7)}
    assert _overlaps(tmp_path) == 2                               # usou o paralelismo
    assert len({json.loads(p.read_text())[2] for p in tmp_path.glob("*.json")}) == 7   # processos


def test_pool_conta_as_vagas_de_um_make(tmp_path):
    with paralelo.Pool(2) as pool:
        pool.submit("make", lambda: _stamp(tmp_path, "make", 0.4), slots=2, priority=10)
        for i in range(3):
            pool.submit(f"t{i}", lambda i=i: _stamp(tmp_path, f"t{i}", 0.2))
        while pool.busy():
            pool.step()
        assert pool.peak <= 2


def test_pool_erro_da_tarefa_volta_como_traceback():
    def boom():
        raise KeyError("sem isso")
    with paralelo.Pool(2) as pool:
        pool.submit("x", boom)
        done = []
        while pool.busy():
            done += pool.step()
    assert done[0].error and "KeyError" in done[0].error


def test_part_data_junta_ou_explica_a_parte_que_faltou():
    ok = lambda v: Result("taxa", "ok", "", data={"n": v})   # noqa: E731
    datas, failure = paralelo.part_data([[ok(1)], [ok(2)]], "taxa")
    assert datas == [{"n": 1}, {"n": 2}] and failure is None
    datas, failure = paralelo.part_data(
        [[ok(1)], [Result("shiny: CONTINUAR", "falha", "tempo esgotado", ["x.png"])]], "taxa")
    assert datas is None and failure.status == "falha"
    assert "parte 2/2" in failure.detail and "tempo esgotado" in failure.detail
    assert failure.images == ["x.png"]


# --- junção dos cenários estatísticos ---------------------------------------------------------

def test_merge_shiny_soma_as_fatias_e_aplica_a_faixa_do_total():
    from esteira.scenarios.full_shiny import RATE_NAMES, merge_shiny
    head = Result("shiny: CONTINUAR com o save do modo rápido na build de teste", "ok", "")

    def part(shinies, extra=()):
        return [head, *extra, Result(RATE_NAMES[False], "ok", "parcial",
                                     data={"shinies": shinies, "frames": 10, "bag": 0})]
    merged = merge_shiny([part(10, [Result("shiny: outra", "ok", "")]), part(20), part(19)])
    assert [r.name for r in merged] == [head.name, "shiny: outra", RATE_NAMES[False]]
    assert merged[-1].status == "ok" and merged[-1].detail.startswith("49 shiny em 200000")
    assert "30 quadros em 3 processos" in merged[-1].detail
    bad = merge_shiny([part(1), part(1), part(1)])          # 3 << faixa de ±3σ (~28..70)
    assert bad[-1].status == "falha" and "fora da faixa" in bad[-1].detail


def test_merge_breeding_roda_as_estatisticas_sobre_os_ovos_de_todas_as_partes():
    from esteira.breeding import CONFIGS, Record
    from esteira.scenarios.full_breeding import (BreedingStats, generation_name,
                                                 merge_breeding)
    config = CONFIGS[-1]   # sem gênero (Magnemite x Ditto): as checagens mais simples
    egg = Record(ivs=(15,) * 6, ability=1, shiny=False, nature=0, gender="-", is_egg=True,
                 probes=(False,) * 4, species=81)
    gen = generation_name(config)
    parts = [[Result(gen, "ok", "", data={"records": [egg] * 5, "compat": 20, "seconds": 1.0})]
             for _ in range(2)]
    merged = merge_breeding(parts)
    assert merged[0].name == gen and "10 ovos" in merged[0].detail
    want = Suite()
    stats = BreedingStats()
    stats.records = {config.name: [egg] * 10}
    stats.stats(config, want)
    assert [(r.name, r.status) for r in merged[1:]] == [(r.name, r.status) for r in want.results]


# --- o CLI em paralelo (cenários falsos) ---------------------------------------------------------

@pytest.fixture
def env(tmp_path, monkeypatch):
    for name in ("jogavel.gba", "jogavel.elf", "teste.gba", "teste.elf"):
        (tmp_path / name).write_bytes(b"x")
    monkeypatch.setattr(cli, "STATE_PATH", str(tmp_path / "estado-rodizio.json"))
    monkeypatch.setattr(cli, "REFS_DIR", str(tmp_path / "referencias"))
    monkeypatch.setattr(cli, "check_text", lambda repo, exceptions: [])
    monkeypatch.setattr(cli, "_git_commit", lambda: "abc1234")
    monkeypatch.setenv("ESTEIRA_JOBS", "2")   # no máximo 2 filhos por worker do xdist

    @contextmanager
    def fake_open(rom, elf, out, starter, suite=None, save_from=None, recorder=None):
        Path(out).mkdir(parents=True, exist_ok=True)
        sav = Path(out) / "esteira.sav"
        sav.write_text(Path(save_from).read_text() if save_from else Path(rom).name)

        def flush_save():
            sav.write_text(f"{Path(rom).name}:{os.getpid()}")
        ctx = SimpleNamespace(suite=suite, starter=starter, out_dir=str(out), rom=Path(rom).name,
                              emu=SimpleNamespace(flush_save=flush_save), part=0, parts=1,
                              recorder=recorder)
        yield ctx
    monkeypatch.setattr(cli, "open_context", fake_open)
    return tmp_path


def argv(tmp: Path, modo="completo", *extra: str) -> list[str]:
    return [modo, "--rom", str(tmp / "jogavel.gba"), "--elf", str(tmp / "jogavel.elf"),
            "--rom-test", str(tmp / "teste.gba"), "--elf-test", str(tmp / "teste.elf"),
            "--out", str(tmp / "out"), *extra]


def step(name, status="ok", sleep=0.0, shot=None):
    def run(ctx):
        time.sleep(sleep)
        images = []
        if shot:
            telas = Path(ctx.out_dir) / "telas"
            telas.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (4, 4)).save(telas / f"{shot}.png")
            images.append(str(telas / f"{shot}.png"))
        ctx.suite.add(Result(f"{name}: passo", status,
                             f"{getattr(ctx, 'rom', '-')} parte {ctx.part}/{ctx.parts}"
                             + "".join(f" (tela em {p})" for p in images), images))
        if getattr(ctx, "recorder", None) is not None:
            for i in range(16):
                ctx.recorder.add(i * 8, bytes([i]) * (240 * 160 * 3))
    return run


def split_run(ctx):
    ctx.suite.add(Result("dividido: CONTINUAR", "ok", f"parte {ctx.part}"))
    ctx.suite.add(Result("dividido: taxa", "ok", "", data={"n": ctx.part + 1}))
    if ctx.part == 0:
        ctx.suite.add(Result("dividido: depois", "ok", ""))


def split_merge(parts):
    out = []
    for r in parts[0]:
        if r.data is None:
            out.append(r)
        else:
            out.append(Result(r.name, "ok", f"soma {sum(p[1].data['n'] for p in parts)} "
                                              f"de {len(parts)} partes"))
    return out


def scenarios(monkeypatch, cap_status="ok", host=True):
    quick = [ScenarioSpec("a", step("a")), ScenarioSpec("cap", step("cap", cap_status), needs="x")]
    full = [ScenarioSpec("pc", step("pc", shot="pc"), needs="save")]
    if host:
        full.append(ScenarioSpec("master", step("master"), rom=HOST))
    full += [ScenarioSpec("dividido", split_run, rom=TEST, save_from="cap", parts=3,
                          merge=split_merge),
             ScenarioSpec("evo", step("evo", sleep=0.2, shot="evo_x"), rom=TEST,
                          save_from="cap"),
             ScenarioSpec("depois", step("depois"), rom=TEST)]
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", quick)
    monkeypatch.setattr(cli, "FULL_SCENARIOS", full)


def names_and_status(tmp: Path) -> list[tuple[str, str]]:
    page = (tmp / "out" / "relatorio.html").read_text(encoding="utf-8")
    import re
    return re.findall(r'<div class="r (\w+)"><span class="tag">\w+</span><b>([^<]*)</b>', page)


def test_paralelo_da_os_mesmos_resultados_que_o_sequencial_na_mesma_ordem(env, monkeypatch,
                                                                           capsys):
    scenarios(monkeypatch)
    assert main(argv(env, "completo", "--starter", "BULBASAUR")) == 0
    paralelo_out = names_and_status(env)
    meta = json.loads((env / "out" / "meta.json").read_text())
    assert meta["processos"] == 2 and meta["semente"].startswith("0x")
    assert list(meta["tempos"]) == ["a", "cap", "pc", "master", "dividido", "evo", "depois",
                                    "vídeo (codificação)"]
    printed = capsys.readouterr().out
    assert "[paralelo] até 2 processos" in printed
    monkeypatch.setenv("ESTEIRA_JOBS", "1")
    assert main(argv(env, "completo", "--starter", "BULBASAUR")) == 0
    assert names_and_status(env) == paralelo_out
    page = (env / "out" / "relatorio.html").read_text(encoding="utf-8")
    assert "dividido: taxa" in page


def test_cenario_dividido_e_juntado_e_as_partes_partem_da_ponte(env, monkeypatch):
    scenarios(monkeypatch)
    assert main(argv(env, "completo", "--starter", "SQUIRTLE")) == 0
    page = (env / "out" / "relatorio.html").read_text(encoding="utf-8")
    assert "soma 6 de 3 partes" in page                     # 1 + 2 + 3
    assert "teste.gba parte 0/1" in page                    # o evo numa sessão inteira
    assert "dividido: depois" in page
    # telas das sessões voltam para OUT/telas; as pastas das sessões somem
    assert (env / "out" / "telas" / "evo_x.png").is_file()
    assert (env / "out" / "telas" / "pc.png").is_file()
    assert not (env / "out" / cli.SESSIONS_DIR).exists()
    assert f"(tela em {env / 'out' / 'telas' / 'evo_x.png'})" in page   # o texto também
    assert (env / "out" / "video.webp").is_file()


def test_produtor_com_falha_deixa_as_sessoes_de_teste_como_nao_rodou(env, monkeypatch, capsys):
    scenarios(monkeypatch, cap_status="falha")
    assert main(argv(env, "completo", "--starter", "BULBASAUR")) == 1
    out = capsys.readouterr().out
    assert "[aviso] cenario/dividido: não rodou" in out
    assert "[aviso] cenario/evo: não rodou" in out
    assert "[aviso] cenario/depois: não rodou" in out


def test_rom_jogavel_ausente_nao_testada_e_sem_ponte(env, monkeypatch, capsys):
    scenarios(monkeypatch)
    (env / "jogavel.gba").unlink()
    assert main(argv(env, "completo", "--starter", "BULBASAUR")) == 1
    out = capsys.readouterr().out
    assert "emulador/rom-playable" in out and "cenario/dividido: não rodou" in out
    assert "ROM NÃO TESTADA" in (env / "out" / "relatorio.html").read_text(encoding="utf-8")


def test_rodizio_avanca_no_verde_tambem_em_paralelo(env, monkeypatch):
    scenarios(monkeypatch, host=False)
    assert main(argv(env, "completo")) == 0
    assert json.loads(Path(cli.STATE_PATH).read_text())["inicial"] == "BULBASAUR"
    scenarios(monkeypatch, cap_status="falha", host=False)
    assert main(argv(env, "completo")) == 1
    assert json.loads(Path(cli.STATE_PATH).read_text())["inicial"] == "BULBASAUR"


def test_erro_fora_dos_cenarios_numa_sessao_derruba_a_esteira(env, monkeypatch):
    """Como no sequencial: um erro ao abrir a sessão (runner ausente...) não é resultado de
    teste, é infraestrutura (traceback, código != 0/1)."""
    scenarios(monkeypatch, host=False)

    @contextmanager
    def broken(*args, **kwargs):
        raise FileNotFoundError("mgba_runner não existe")
        yield
    monkeypatch.setattr(cli, "open_context", broken)
    with pytest.raises(RuntimeError, match="mgba_runner"):
        main(argv(env, "completo", "--starter", "BULBASAUR"))


def test_rapido_em_paralelo_poe_os_textos_no_mesmo_lugar(env, monkeypatch):
    monkeypatch.setattr(cli, "check_text",
                        lambda repo, exceptions: [Result("texto/x", "aviso", "pid %d" % os.getpid())])
    scenarios(monkeypatch)
    assert main(argv(env, "rapido", "--starter", "BULBASAUR")) == 0
    got = names_and_status(env)
    page = (env / "out" / "relatorio.html").read_text(encoding="utf-8")
    assert f"pid {os.getpid()}" not in page                  # rodou em outro processo
    monkeypatch.setenv("ESTEIRA_JOBS", "1")
    assert main(argv(env, "rapido", "--starter", "BULBASAUR")) == 0
    assert names_and_status(env) == got


def test_rapido_em_paralelo_com_bug_na_checagem_de_texto_reprova_com_diagnostico(env, monkeypatch):
    def boom(repo, exceptions):
        raise KeyError("rótulo")
    monkeypatch.setattr(cli, "check_text", boom)
    scenarios(monkeypatch)
    assert main(argv(env, "rapido", "--starter", "BULBASAUR")) == 1
    page = (env / "out" / "relatorio.html").read_text(encoding="utf-8")
    assert "esteira/checagens-estáticas" in page and "KeyError" in page


def test_only_e_teto_1_continuam_sequenciais(env, monkeypatch):
    """--only nunca divide nem abre processos: a parte única roda o cenário inteiro."""
    seen = []
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", [])
    monkeypatch.setattr(cli, "FULL_SCENARIOS", [ScenarioSpec(
        "m", lambda ctx: seen.append((os.getpid(), getattr(ctx, "parts", 1))), rom=HOST)])
    assert main(argv(env, "completo", "--only", "m")) == 0
    assert seen == [(os.getpid(), 1)]


def test_videos_das_sessoes_juntados_na_ordem_e_no_mesmo_espacamento(tmp_path):
    from esteira.video import VideoRecorder
    exports = []
    for every, color in ((8, 10), (16, 200)):
        rec = VideoRecorder(every=every, stream=False)
        for i in range(8):
            rec.add(i * every, bytes([color + 5 * i]) * (240 * 160 * 3))   # quadros distintos
        exports.append(rec.export())
    assert exports[0]["every"] == 8 and len(exports[0]["frames"]) == 8
    merged = cli._merge_videos(exports)
    assert merged.grab_every == 16                     # o maior espaçamento vale para todas
    assert merged.positions() == [0, 16, 32, 48] + [16 * i for i in range(8)]
    path = merged.save(str(tmp_path / "v.webp"))
    with Image.open(path) as video:
        assert video.is_animated   # (o WebP funde quadros parecidos: a contagem não vale)


def test_video_com_falha_numa_sessao_vira_aviso_no_merge():
    from esteira.video import VideoRecorder
    rec = VideoRecorder(stream=False)
    rec.fail(KeyError("shots"))
    merged = cli._merge_videos([rec.export()])
    with pytest.raises(RuntimeError, match="shots"):
        merged.save("/nao/importa.webp")


# --- revisão: sal por execução, encerramento, resultado ilegível -------------------------------

def test_sal_da_execucao_sorteado_ou_fixado_por_ESTEIRA_SEED(monkeypatch):
    monkeypatch.delenv("ESTEIRA_SEED", raising=False)
    salts = {paralelo.run_salt() for _ in range(8)}
    assert len(salts) > 1 and all(0 <= s < 2 ** 32 for s in salts)
    monkeypatch.setenv("ESTEIRA_SEED", "0x00c0ffee")
    assert paralelo.run_salt() == 0xC0FFEE
    monkeypatch.setenv("ESTEIRA_SEED", "12")
    assert paralelo.run_salt() == 12
    # o sal muda as sementes; as janelas continuam disjuntas para o mesmo sal
    a = [paralelo.part_seed("shiny", k, 0xC0FFEE) for k in range(3)]
    assert a != [paralelo.part_seed("shiny", k, 12) for k in range(3)]
    assert paralelo.lcg_jump(a[0], paralelo.SEED_WINDOW) == a[1]
    assert paralelo.seed_label(0xC0FFEE) == "ESTEIRA_SEED=0x00c0ffee"


def test_merge_mostra_a_semente_no_detalhe():
    from esteira.scenarios.full_shiny import RATE_NAMES, merge_shiny
    part = [Result(RATE_NAMES[True], "ok", "", data={"shinies": 49, "frames": 1, "bag": 1,
                                                      "seed": 0xABC})]
    merged = merge_shiny([part, part])
    assert merged[0].detail.endswith("ESTEIRA_SEED=0x00000abc")


def test_meta_e_resumo_trazem_a_semente_e_ESTEIRA_SEED_reproduz(env, monkeypatch, capsys):
    scenarios(monkeypatch, host=False)
    monkeypatch.setenv("ESTEIRA_SEED", "0x1234abcd")
    assert main(argv(env, "completo", "--starter", "BULBASAUR")) == 0
    assert json.loads((env / "out" / "meta.json").read_text())["semente"] == "0x1234abcd"
    assert "ESTEIRA_SEED=0x1234abcd" in capsys.readouterr().out


def _tree_with_finally(marker: Path, pidfile: Path) -> None:
    import subprocess
    try:
        proc = subprocess.Popen(["sleep", "60"])     # como o make do master
        pidfile.write_text(str(proc.pid))
        proc.wait()
    finally:
        marker.write_text("finally rodou")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    return stat.is_file() and stat.read_text().split()[2] != "Z"


def test_close_encerra_a_arvore_da_tarefa_e_os_finally_rodam(tmp_path):
    marker, pidfile = tmp_path / "finally", tmp_path / "pid"
    pool = paralelo.Pool(2)
    pool.submit("master", lambda: _tree_with_finally(marker, pidfile))
    deadline = time.time() + 10
    while not pidfile.exists() and time.time() < deadline:
        pool.step(timeout=0.05)
    grandchild = int(pidfile.read_text())
    pool.close()                                     # como num erro de outra tarefa / Ctrl-C
    assert marker.read_text() == "finally rodou"
    deadline = time.time() + 5
    while _alive(grandchild) and time.time() < deadline:
        time.sleep(0.05)
    assert not _alive(grandchild), "o processo aberto pela tarefa ficou órfão"


def test_resultado_ilegivel_vira_erro_da_tarefa(monkeypatch):
    def broken_load(fh):
        raise AttributeError("classe sumiu")
    monkeypatch.setattr(paralelo.pickle, "load", broken_load)
    with paralelo.Pool(1) as pool:
        pool.submit("x", lambda: 1)
        done = []
        while pool.busy():
            done += pool.step()
    assert "classe sumiu" in done[0].error


def test_so_a_parte_1_de_um_cenario_dividido_grava_video(env, monkeypatch):
    log = env / "video.log"
    real = cli._session_task

    def spy(group, rom, elf, out_dir, starter, save_from, video, bridges, part, parts, *rest):
        with open(log, "a") as fh:
            fh.write(f"{group[0].name} {part} {video}\n")
        return real(group, rom, elf, out_dir, starter, save_from, video, bridges, part, parts,
                    *rest)
    monkeypatch.setattr(cli, "_session_task", spy)
    scenarios(monkeypatch, host=False)
    assert main(argv(env, "completo", "--starter", "BULBASAUR")) == 0
    lines = sorted(log.read_text().splitlines())
    assert lines == ["a 0 True", "dividido 0 True", "dividido 1 False", "dividido 2 False",
                     "evo 0 True"]
