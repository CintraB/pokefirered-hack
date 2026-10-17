"""Modo `assistir`: janela SDL2 em tempo real (runner `--window`) e o subcomando da esteira."""

import json
import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

import esteira.__main__ as cli
import esteira.emu as emu_mod
from esteira.__main__ import ScenarioSpec, main
from esteira.emu import Emulator, EmulatorError, WindowClosed
from esteira.result import Result
from esteira.video import VideoRecorder

REPO_ROOT = Path(__file__).resolve().parents[2]
DISPLAY_VARS = ("DISPLAY", "WAYLAND_DISPLAY", "SDL_VIDEODRIVER")


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    """Nenhum teste toca o rodízio nem as referências reais."""
    monkeypatch.setattr(cli, "STATE_PATH", str(tmp_path / "estado-rodizio.json"))
    monkeypatch.setattr(cli, "REFS_DIR", str(tmp_path / "referencias"))


@pytest.fixture
def dummy_sdl(monkeypatch):
    """SDL sem tela nem som: o runner abre a "janela" mas nada aparece."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


def _roms_snapshot():
    roms = REPO_ROOT / "roms"
    if not roms.is_dir():
        return {}
    return {str(p.relative_to(roms)): (p.stat().st_mtime_ns, p.stat().st_size)
            for p in roms.rglob("*") if p.is_file()}


# --- runner/Emulator ---------------------------------------------------------------------------

def test_janela_limita_a_velocidade_a_tempo_real(rom_path, tmp_save, dummy_sdl):
    with Emulator(rom_path, tmp_save, window=True) as emu:
        emu.frames(2)   # aquece (abertura da janela, primeira passada)
        start = time.monotonic()
        emu.frames(120)
        elapsed = time.monotonic() - start
    assert elapsed >= 1.9, f"120 quadros em {elapsed:.2f} s: sem limite de velocidade"
    assert elapsed < 3.0, f"120 quadros em {elapsed:.2f} s: lento demais para 59,73 quadros/s"


def test_sem_janela_continua_sem_limite(rom_path, tmp_save):
    with Emulator(rom_path, tmp_save) as emu:
        emu.frames(2)
        start = time.monotonic()
        emu.frames(120)
        elapsed = time.monotonic() - start
    assert elapsed < 1.0


def test_janela_protocolo_igual_ao_headless(rom_path, tmp_save, tmp_path, dummy_sdl):
    with Emulator(rom_path, tmp_save, window=True) as emu:
        assert emu.read(0x080000A0, 12) == b"POKEMON FIRE"
        emu.frames(30)
        img = emu.screenshot(str(tmp_path / "tela.png"))
    assert img.size == (240, 160)


def test_janela_e_gravacao_de_video_nao_combinam(rom_path, tmp_save):
    with pytest.raises(ValueError, match="vídeo"):
        Emulator(rom_path, tmp_save, window=True, recorder=VideoRecorder())


def test_runner_sem_display_falha_na_abertura(rom_path, tmp_save, monkeypatch):
    for var in DISPLAY_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SDL_VIDEODRIVER", "x11")   # driver sem servidor: não pode abrir
    monkeypatch.setenv("DISPLAY", "")
    with pytest.raises(EmulatorError):
        with Emulator(rom_path, tmp_save, window=True) as emu:
            emu.frames(1)


def test_codigo_3_do_runner_vira_janela_fechada(rom_path, tmp_save):
    emu = Emulator(rom_path, tmp_save)
    emu.close()
    emu._proc = SimpleNamespace(poll=lambda: emu_mod.WINDOW_CLOSED_EXIT, returncode=emu_mod.WINDOW_CLOSED_EXIT)
    with pytest.raises(WindowClosed):
        emu.frames(1)


# --- subcomando assistir -------------------------------------------------------------------------

class FakeWatch:
    """open_context falso: registra como foi aberto e entrega um ctx mínimo."""

    def __init__(self, tmp_path: Path):
        self.tmp = tmp_path
        self.opened: list[dict] = []
        self.ran: list[str] = []
        self.loaded: list[str] = []
        self.party_species = 1
        (tmp_path / "jogavel.gba").write_bytes(b"x")
        (tmp_path / "jogavel.elf").write_bytes(b"x")

    def argv(self, *extra: str) -> list[str]:
        return ["assistir", "--rom", str(self.tmp / "jogavel.gba"),
                "--elf", str(self.tmp / "jogavel.elf"), *extra]

    def spec(self, name, needs=None, effect=None) -> ScenarioSpec:
        def run(ctx):
            self.ran.append(name)
            if effect:
                effect(ctx)
        return ScenarioSpec(name, run, needs=needs)


@pytest.fixture
def fw(tmp_path, monkeypatch):
    f = FakeWatch(tmp_path)
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")   # passa na checagem de display

    @contextmanager
    def fake_open(rom, elf, out, starter, suite=None, save_from=None, recorder=None, window=False):
        f.opened.append({"rom": rom, "out": out, "starter": starter, "window": window,
                         "recorder": recorder, "save_from": save_from})
        emu = SimpleNamespace(load_state=lambda p: f.loaded.append(str(p)), keys=lambda m: None)
        yield SimpleNamespace(
            emu=emu, suite=suite, starter=starter, out_dir=str(out),
            game=SimpleNamespace(party=lambda: [SimpleNamespace(species=f.party_species)]),
            consts=SimpleNamespace(species=lambda s: {"BULBASAUR": 1, "CHARMANDER": 2,
                                                      "SQUIRTLE": 3}[s]))

    monkeypatch.setattr(cli, "open_context", fake_open)
    monkeypatch.setattr(cli, "WATCH_CHECKPOINT_ROOT", tmp_path / "out-antigo")
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", [
        f.spec("abertura"), f.spec("rota1", needs="rival"), f.spec("captura", needs="encomenda")])
    return f


def test_assistir_nao_toca_em_roms_nem_no_rodizio(fw, tmp_path):
    before = _roms_snapshot()
    assert main(fw.argv("--starter", "SQUIRTLE")) == 0
    assert _roms_snapshot() == before                       # nada novo em roms/ (nem versão, nem estado)
    assert not Path(cli.STATE_PATH).exists()                # rodízio intocado
    (opened,) = fw.opened
    assert opened["window"] is True and opened["recorder"] is None
    assert opened["save_from"] is None
    out = Path(opened["out"]).resolve()
    assert REPO_ROOT / "roms" not in out.parents            # save temporário, nunca roms/saves/
    assert not out.exists()                                 # temporário apagado no fim
    assert fw.ran == ["abertura", "rota1", "captura"]


def test_assistir_sem_starter_usa_o_da_vez_sem_gastar_o_rodizio(fw):
    Path(cli.STATE_PATH).write_text('{"inicial": "BULBASAUR"}\n', encoding="utf-8")
    assert main(fw.argv()) == 0
    assert fw.opened[0]["starter"] == "CHARMANDER"
    assert Path(cli.STATE_PATH).read_text(encoding="utf-8") == '{"inicial": "BULBASAUR"}\n'


def test_assistir_sem_display_sai_2_com_mensagem(fw, monkeypatch, capsys):
    for var in DISPLAY_VARS:
        monkeypatch.delenv(var, raising=False)
    assert main(fw.argv()) == 2
    err = capsys.readouterr().err
    assert "DISPLAY" in err and "WSLg" in err
    assert fw.opened == []


def test_assistir_rom_ausente_sai_2(fw, capsys):
    (fw.tmp / "jogavel.gba").unlink()
    assert main(fw.argv()) == 2
    assert "make firered_switch" in capsys.readouterr().err
    assert fw.opened == []


def test_assistir_from_invalido_e_erro_de_uso(fw):
    with pytest.raises(SystemExit) as exc:
        main(fw.argv("--from", "inexistente"))
    assert exc.value.code == 2


def _fake_checkpoint(fw, run: str, name: str, age: int = 0) -> Path:
    path = fw.tmp / "out-antigo" / run / "estados" / f"{name}.ss"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"ss")
    import os
    t = time.time() + 100 + age
    os.utime(path, (t, t))   # mais novo que a ROM
    return path


def test_assistir_from_carrega_o_checkpoint_e_roda_so_o_resto(fw):
    ss = _fake_checkpoint(fw, "r1", "encomenda")
    fw.party_species = 3
    seen = []
    cli.QUICK_SCENARIOS[2] = fw.spec("captura", needs="encomenda",
                                     effect=lambda ctx: seen.append(ctx.starter))
    assert main(fw.argv("--from", "encomenda")) == 0
    assert fw.loaded == [str(ss)]
    assert fw.ran == ["captura"]
    assert seen == ["SQUIRTLE"]   # o inicial vem do checkpoint


def test_assistir_from_ignora_checkpoint_mais_velho_que_a_rom(fw):
    ss = _fake_checkpoint(fw, "r1", "rival", age=-1000)
    import os
    os.utime(ss, (1, 1))
    assert main(fw.argv("--from", "rival")) == 2
    assert fw.ran == []


def test_assistir_from_sem_checkpoint_orienta(fw, capsys):
    assert main(fw.argv("--from", "rival")) == 2
    err = capsys.readouterr().err
    assert "rival" in err and "make test-quick" in err


def test_assistir_from_respeita_starter_pedido(fw):
    _fake_checkpoint(fw, "r1", "rival")
    fw.party_species = 1   # BULBASAUR no checkpoint
    assert main(fw.argv("--from", "rival", "--starter", "CHARMANDER")) == 2
    assert fw.ran == []


def test_assistir_falha_de_cenario_sai_1_e_guarda_evidencias(fw, monkeypatch, capsys):
    def boom(ctx):
        ctx.suite.add(Result("roteiro: x", "falha", "deu errado"))
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", [fw.spec("abertura", effect=boom),
                                                 fw.spec("rota1", needs="rival")])
    assert main(fw.argv("--starter", "SQUIRTLE")) == 1
    assert fw.ran == ["abertura"]
    out = Path(fw.opened[0]["out"])
    assert str(out) in capsys.readouterr().out
    shutil.rmtree(out, ignore_errors=True)


def test_assistir_janela_fechada_encerra_sem_falha(fw, monkeypatch, capsys):
    def close(ctx):
        raise WindowClosed("runner encerrado (código 3)")
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", [fw.spec("abertura", effect=close),
                                                 fw.spec("rota1", needs="rival")])
    assert main(fw.argv("--starter", "SQUIRTLE")) == 0
    assert fw.ran == ["abertura"]
    assert "janela fechada" in capsys.readouterr().out.lower()


# --- assistir --cenario (modo completo, ROM de teste) ---------------------------------------------

def _fake_bridge(fw, run: str, starter: str, age: int = 0) -> Path:
    """Um captura.sav (+ .sav.json) como os que as execuções deixam em test/out/<run>/."""
    save = fw.tmp / "out-antigo" / run / "captura.sav"
    save.parent.mkdir(parents=True, exist_ok=True)
    save.write_text(f"sav de {run}")
    save.with_name("captura.sav.json").write_text(json.dumps({"inicial": starter}))
    t = time.time() + 100 + age
    os.utime(save, (t, t))
    return save


@pytest.fixture
def fw_full(fw, monkeypatch):
    """`assistir --cenario evolucoes` com o cenário falso e uma ROM de teste falsa."""
    (fw.tmp / "teste.gba").write_bytes(b"x")
    (fw.tmp / "teste.elf").write_bytes(b"x")
    seen = []

    def run(ctx):
        fw.ran.append("evolucoes")
        seen.append(ctx.starter)
    monkeypatch.setattr(cli, "FULL_SCENARIOS", [
        ScenarioSpec("shiny", lambda ctx: fw.ran.append("shiny"), rom=cli.TEST, save_from="captura"),
        ScenarioSpec("evolucoes", run, rom=cli.TEST, save_from="captura")])
    fw.seen_starters = seen
    fw.full_argv = lambda *extra: fw.argv("--cenario", "evolucoes",
                                          "--rom-test", str(fw.tmp / "teste.gba"),
                                          "--elf-test", str(fw.tmp / "teste.elf"), *extra)
    return fw


def test_assistir_cenario_roda_na_rom_de_teste_com_o_sav_mais_recente(fw_full):
    _fake_bridge(fw_full, "r1", "BULBASAUR", age=-50)
    newest = _fake_bridge(fw_full, "r2", "SQUIRTLE")
    before = _roms_snapshot()
    assert main(fw_full.full_argv()) == 0
    assert fw_full.ran == ["evolucoes"]                  # só o cenário pedido, sem o roteiro rápido
    (opened,) = fw_full.opened
    assert opened["rom"] == str(fw_full.tmp / "teste.gba") and opened["window"] is True
    assert opened["save_from"] == str(newest)             # cópia: o open_context copia para o temp
    assert opened["recorder"] is None
    assert fw_full.seen_starters == ["SQUIRTLE"]          # o inicial é o do save
    assert _roms_snapshot() == before and not Path(cli.STATE_PATH).exists()
    assert not Path(opened["out"]).exists()


def test_assistir_cenario_respeita_starter_pedido(fw_full):
    older = _fake_bridge(fw_full, "r1", "CHARMANDER", age=-50)
    _fake_bridge(fw_full, "r2", "SQUIRTLE")
    assert main(fw_full.full_argv("--starter", "CHARMANDER")) == 0
    assert fw_full.opened[0]["save_from"] == str(older)


def test_assistir_cenario_sem_sav_orienta_e_sai_2(fw_full, capsys):
    assert main(fw_full.full_argv()) == 2
    err = capsys.readouterr().err
    assert "captura.sav" in err and "make test-quick" in err
    assert fw_full.opened == [] and fw_full.ran == []


def test_assistir_cenario_sem_rom_de_teste_sai_2(fw_full, capsys):
    _fake_bridge(fw_full, "r1", "SQUIRTLE")
    (fw_full.tmp / "teste.gba").unlink()
    assert main(fw_full.full_argv()) == 2
    assert "TESTBUILD=1" in capsys.readouterr().err
    assert fw_full.opened == []


def test_assistir_cenario_com_from_e_erro_de_uso(fw_full):
    with pytest.raises(SystemExit) as exc:
        main(fw_full.full_argv("--from", "rival"))
    assert exc.value.code == 2


def test_assistir_cenario_desconhecido_e_erro_de_uso(fw_full):
    with pytest.raises(SystemExit) as exc:
        main(fw_full.argv("--cenario", "shiny"))   # o shiny não se assiste (horas em tempo real)
    assert exc.value.code == 2


def test_assistir_cenario_com_falha_sai_1(fw_full, monkeypatch, capsys):
    _fake_bridge(fw_full, "r1", "SQUIRTLE")

    def boom(ctx):
        ctx.suite.add(Result("evolucoes: x", "falha", "deu errado"))
    monkeypatch.setattr(cli, "FULL_SCENARIOS", [
        ScenarioSpec("evolucoes", boom, rom=cli.TEST, save_from="captura")])
    assert main(fw_full.full_argv()) == 1
    out = Path(fw_full.opened[0]["out"])
    assert str(out) in capsys.readouterr().out
    shutil.rmtree(out, ignore_errors=True)


# --- Makefile -------------------------------------------------------------------------------------

def _recipe(target: str) -> str:
    """Receita do alvo no Makefile (linhas indentadas logo depois de `alvo:`)."""
    lines = (REPO_ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    start = lines.index(f"{target}:")
    body = []
    for line in lines[start + 1:]:
        if not line.startswith("\t"):
            break
        body.append(line)
    return "\n".join(body)


@pytest.mark.parametrize("target", ["test-quick", "test-watch", "test-full"])
def test_alvos_com_emulador_recompilam_o_runner_primeiro(target):
    recipe = _recipe(target)
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "ESTEIRA_RUNNER = $(MAKE) -s -C test/harness" in makefile
    first_use = min(i for i in (recipe.find("ESTEIRA_RUN,"), recipe.find("-m esteira"))
                    if i >= 0)
    assert recipe.index("$(ESTEIRA_RUNNER)") < first_use, "runner em dia antes de rodar a esteira"


def test_alvo_test_watch_chama_assistir_e_repassa_from_e_starter():
    recipe = _recipe("test-watch")
    assert "esteira assistir" in recipe
    assert "$(FROM)" in recipe and "$(STARTER)" in recipe
    assert "test-watch" in (REPO_ROOT / "Makefile").read_text(encoding="utf-8").split(
        "RULES_NO_SCAN +=")[1].splitlines()[0]


def test_alvo_test_watch_com_cenario_recompila_a_rom_de_teste_antes():
    recipe = _recipe("test-watch")
    assert "$(if $(CENARIO),$(MAKE) firered_switch TESTBUILD=1" in recipe
    assert "--cenario $(CENARIO)" in recipe
    assert "--rom-test $(CURDIR)/pokefirered_switch_test.gba" in recipe
    assert recipe.index("TESTBUILD=1") < recipe.index("-m esteira")


# --- rodada 1: Ctrl-C, SDL opcional, display, estado inválido -------------------------------------

import os
import signal
import sys

HARNESS = REPO_ROOT / "test" / "harness"


def _runner_procs(marker: str) -> list[str]:
    """Linhas de comando dos processos vivos que citam `marker` (Linux: /proc)."""
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                cmd = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            except OSError:
                continue
            if marker in cmd and "mgba_runner" in cmd:
                found.append(cmd)
    return found


@pytest.mark.parametrize("round_", range(3))
def test_ctrl_c_em_assistir_sai_130_limpa_o_temp_e_nao_deixa_runner(rom_path, tmp_path, round_):
    if not (REPO_ROOT / "pokefirered_switch.elf").is_file():
        pytest.skip("pokefirered_switch.elf ausente")
    env = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
           "TMPDIR": str(tmp_path), "PYTHONUNBUFFERED": "1"}
    proc = subprocess.Popen([sys.executable, "-m", "esteira", "assistir", "--starter", "BULBASAUR"],
                            cwd=REPO_ROOT / "test", env=env, start_new_session=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for line in proc.stdout:   # espera o primeiro roteiro começar
            if "[assistindo] abertura" in line:
                break
        else:
            pytest.fail("assistir terminou antes de começar o roteiro")
        time.sleep(1.0 + round_ * 0.4)
        os.killpg(proc.pid, signal.SIGINT)   # como o Ctrl-C do terminal: grupo inteiro
        rest = proc.stdout.read()
        code = proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    assert code == 130, rest
    assert "Traceback" not in rest, rest
    assert list(tmp_path.glob("esteira-assistir-*")) == []
    assert _runner_procs(str(tmp_path)) == []


@pytest.fixture(scope="module")
def no_sdl_runner(tmp_path_factory):
    """Runner compilado como numa máquina sem SDL2: um `sdl2-config` que falha vem antes no PATH."""
    if shutil.which("cc") is None:
        pytest.skip("sem compilador")
    work = tmp_path_factory.mktemp("sem-sdl")
    fake = work / "bin"
    fake.mkdir()
    (fake / "sdl2-config").write_text("#!/bin/sh\nexit 127\n")
    (fake / "sdl2-config").chmod(0o755)
    harness = work / "harness"
    harness.mkdir()
    for name in ("Makefile", "mgba_runner.c"):
        shutil.copy(HARNESS / name, harness / name)
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}"}
    done = subprocess.run(["make", "-C", str(harness)], env=env, capture_output=True, text=True,
                          timeout=300)
    assert done.returncode == 0, done.stderr
    assert "-DUSE_SDL" not in done.stdout
    clean = subprocess.run(["make", "-C", str(harness), "clean"], env=env, capture_output=True,
                           text=True, timeout=60)
    assert clean.returncode == 0 and clean.stderr == ""   # sem erro de shell por falta do SDL
    subprocess.run(["make", "-C", str(harness)], env=env, capture_output=True, timeout=300,
                   check=True)
    return harness / "mgba_runner"


def test_runner_sem_sdl_recusa_window_com_codigo_2(no_sdl_runner, tmp_path):
    done = subprocess.run([str(no_sdl_runner), "x.gba", "--save", str(tmp_path / "s.sav"),
                           "--window"], capture_output=True, text=True, timeout=30)
    assert done.returncode == 2
    assert "sem SDL2" in done.stderr and "libsdl2-dev" in done.stderr


def test_emulator_window_em_runner_sem_sdl_explica(no_sdl_runner, rom_path, tmp_save, monkeypatch):
    monkeypatch.setattr(emu_mod, "RUNNER", no_sdl_runner)
    monkeypatch.setattr(emu_mod, "RUNNER_SRC", no_sdl_runner.with_suffix(".c"))
    with pytest.raises(EmulatorError, match="libsdl2-dev"):
        with Emulator(rom_path, tmp_save, window=True) as emu:
            emu.frames(1)


def test_makefile_do_runner_sem_sdl2_config_no_path_nao_liga_sdl(tmp_path):
    empty = tmp_path / "vazio"
    empty.mkdir()
    done = subprocess.run([shutil.which("make"), "-n", "-B", "-C", str(HARNESS)],
                          env={"PATH": str(empty)}, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert "-DUSE_SDL" not in done.stdout and "SDL2" not in done.stdout
    assert done.stderr == ""


def test_makefile_do_runner_com_sdl2_liga_sdl():
    if shutil.which("sdl2-config") is None:
        pytest.skip("sdl2-config ausente")
    done = subprocess.run(["make", "-n", "-B", "-C", str(HARNESS)], capture_output=True,
                          text=True, timeout=60)
    assert "-DUSE_SDL" in done.stdout and "-lSDL2" in done.stdout


def test_display_exige_display_real_ou_driver_dummy(fw, monkeypatch, capsys):
    for var in DISPLAY_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SDL_VIDEODRIVER", "x11")   # sozinho não é display
    assert main(fw.argv()) == 2
    assert "DISPLAY" in capsys.readouterr().err
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert main(fw.argv("--starter", "SQUIRTLE")) == 0


def test_assistir_from_com_estado_invalido_explica_sem_traceback(fw, monkeypatch, capsys):
    _fake_checkpoint(fw, "r1", "rival")

    def bad_load(path):
        raise EmulatorError("state_load: estado inválido em " + path)

    @contextmanager
    def open_bad(rom, elf, out, starter, suite=None, save_from=None, recorder=None, window=False):
        with fw_open(rom, elf, out, starter, suite, save_from, recorder, window) as ctx:
            ctx.emu.load_state = bad_load
            yield ctx

    fw_open = cli.open_context
    monkeypatch.setattr(cli, "open_context", open_bad)
    assert main(fw.argv("--from", "rival")) == 2
    err = capsys.readouterr().err
    assert "rival" in err and "make test-quick" in err and "Traceback" not in err
    assert fw.ran == []


class DyingProc:
    """Runner que morre (SDL_QUIT do Ctrl-C, código 3) justo quando o `quit` vai ser enviado."""

    def __init__(self, code):
        self.code = code
        self.returncode = None
        self.stdin = SimpleNamespace(write=self._broken, flush=self._broken, close=self._broken)
        self.stdout = SimpleNamespace(readline=lambda: "", close=lambda: None)

    def _broken(self, *a):
        raise BrokenPipeError

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = self.code
        return self.code


@pytest.mark.parametrize("code", [3, -2, 1])
def test_close_tolera_runner_morrendo(rom_path, tmp_save, code):
    emu = Emulator(rom_path, tmp_save)
    emu.close()
    emu._proc = DyingProc(code)
    emu.close()   # não pode lançar (substituiria o KeyboardInterrupt do Ctrl-C)
    emu.close()


def test_sigint_do_runner_com_python_no_meio_do_frames_vira_keyboard_interrupt(fw, monkeypatch):
    def killed(ctx):
        raise EmulatorError("runner encerrado (código -2) durante 'frames'", returncode=-signal.SIGINT)
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", [fw.spec("abertura", effect=killed)])
    assert main(fw.argv("--starter", "SQUIRTLE")) == 130
