"""Modo `assistir`: janela SDL2 em tempo real (runner `--window`) e o subcomando da esteira."""

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
