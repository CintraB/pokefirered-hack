"""Vídeo da execução: gravador de WebP animado, gancho no Emulator e embutido no relatório."""

import base64
import os
import queue
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from esteira import emu as emu_module
from esteira.report import write_report
from esteira.result import Suite
from esteira.video import VideoRecorder

META = {"inicial": "BULBASAUR", "data": "2026-10-17 10:00", "commit": "abc1234",
        "tempo_total": 1.0, "nao_testada": False}


def synthetic(i: int) -> Image.Image:
    img = Image.new("RGB", (240, 160), (i % 256, 40, 90))
    img.putpixel((i % 240, i % 160), (255, 255, 255))
    return img


def test_100_quadros_com_every_8_viram_13_quadros_a_30_fps(tmp_path):
    rec = VideoRecorder(every=8)
    for i in range(100):
        rec.capture(synthetic(i))
    path = rec.save(str(tmp_path / "v.webp"))
    with Image.open(path) as video:
        assert video.format == "WEBP" and video.is_animated
        assert video.n_frames == 13
        durations = []
        for idx in range(video.n_frames):
            video.seek(idx)
            video.load()
            durations.append(video.info["duration"])
    assert all(d in (33, 34) for d in durations), durations


def test_scale_amplia_o_quadro(tmp_path):
    rec = VideoRecorder(every=1, scale=2)
    for i in range(3):
        rec.capture(synthetic(i))
    with Image.open(rec.save(str(tmp_path / "v.webp"))) as video:
        assert video.size == (480, 320)


def test_sem_quadros_nao_grava(tmp_path):
    with pytest.raises(ValueError):
        VideoRecorder().save(str(tmp_path / "v.webp"))


def test_teto_do_arquivo_aumenta_every(tmp_path):
    """Passou de max_bytes: descarta metade dos quadros (every dobra) até caber."""
    frames = [Image.effect_noise((240, 160), 80 + i).convert("RGB") for i in range(60)]
    free = VideoRecorder(every=1)
    for img in frames:
        free.capture(img)
    full_size = Path(free.save(str(tmp_path / "livre.webp"))).stat().st_size
    rec = VideoRecorder(every=1, max_bytes=full_size // 3)
    for img in frames:
        rec.capture(img)
    path = Path(rec.save(str(tmp_path / "v.webp")))
    assert path.stat().st_size <= full_size // 3
    assert rec.every > 1
    with Image.open(path) as video:
        assert 1 <= video.n_frames < 60


def test_teto_de_memoria_aumenta_every_sem_perder_o_primeiro_quadro():
    rec = VideoRecorder(every=1, memory_budget=3000)
    for i in range(200):
        rec.capture(Image.effect_noise((240, 160), 60 + i % 30).convert("RGB"))
    assert rec.every > 1 and len(rec) < 200
    assert rec.positions()[0] == 0
    assert all(pos % rec.every == 0 for pos in rec.positions())


def test_max_frames_aumenta_every():
    rec = VideoRecorder(every=1, max_bytes=4096 * 10)    # ~10 quadros de 4 KB
    for i in range(100):
        rec.capture(synthetic(i))
    pos = rec.positions()
    assert len(pos) <= 10 and rec.every > 1 and pos[0] == 0
    assert all(p % rec.every == 0 for p in pos)


def test_sem_codificador_incremental_usa_a_api_publica(tmp_path, monkeypatch):
    monkeypatch.setattr("esteira.video._webp", None)
    rec = VideoRecorder(every=8)
    for i in range(100):
        rec.capture(synthetic(i))
    with Image.open(rec.save(str(tmp_path / "v.webp"))) as video:
        assert video.n_frames == 13


def _valid_webp(path, frames):
    with Image.open(path) as video:
        assert video.format == "WEBP" and video.n_frames == frames


def feed(rec, n=100):
    for i in range(n):
        rec.capture(synthetic(i))


@pytest.mark.parametrize("error", [TypeError("assinatura nova"), AttributeError("sem getim")])
def test_codificador_interno_que_falha_cai_na_api_publica(tmp_path, monkeypatch, error):
    """Qualquer exceção do WebPAnimEncoder (não só ImportError) abandona o incremental."""
    def broken(*args, **kwargs):
        raise error
    monkeypatch.setattr("esteira.video._webp", SimpleNamespace(WebPAnimEncoder=broken))
    rec = VideoRecorder(every=8)
    feed(rec)
    _valid_webp(rec.save(str(tmp_path / "v.webp")), 13)


def test_stream_add_que_falha_durante_a_execucao_cai_na_api_publica(tmp_path, monkeypatch):
    def broken(self, img):
        raise AttributeError("getim sumiu")
    monkeypatch.setattr("esteira.video._Stream.add", broken)
    rec = VideoRecorder(every=8)
    feed(rec)
    # a API interna falha também na regravação: o fallback público é quem entrega o arquivo
    _valid_webp(rec.save(str(tmp_path / "v.webp")), 13)
    assert rec._incremental is False


def test_finish_que_falha_cai_na_api_publica(tmp_path, monkeypatch):
    def broken(self):
        raise TypeError("assemble mudou")
    monkeypatch.setattr("esteira.video._Stream.finish", broken)
    rec = VideoRecorder(every=8)
    feed(rec)
    _valid_webp(rec.save(str(tmp_path / "v.webp")), 13)


def test_erro_da_thread_de_fundo_reaparece_em_save(tmp_path, monkeypatch):
    rec = VideoRecorder(every=8)

    def boom(pos, rgb, size):
        raise ValueError("zlib quebrou")
    monkeypatch.setattr(rec, "_ingest", boom)
    feed(rec, 20)
    with pytest.raises(ValueError, match="zlib quebrou"):
        rec.save(str(tmp_path / "v.webp"))


def test_gravador_com_falha_recusa_quadros_e_save_explica(tmp_path):
    rec = VideoRecorder(every=8)
    feed(rec, 20)
    rec.fail(KeyError("shots"))
    feed(rec, 20)
    assert len(rec) == 3     # nada entrou depois da falha
    with pytest.raises(RuntimeError, match="interrompida"):
        rec.save(str(tmp_path / "v.webp"))


def test_thread_que_nao_inicia_nao_fica_gravada(monkeypatch):
    rec = VideoRecorder(every=1)

    def no_start(self):
        raise RuntimeError("cannot start new thread")
    monkeypatch.setattr(threading.Thread, "start", no_start)
    with pytest.raises(RuntimeError):
        rec.capture(synthetic(0))
    assert rec._thread is None


def test_fila_cheia_com_thread_morta_nao_trava():
    rec = VideoRecorder(every=1)
    rec._queue = queue.Queue(maxsize=1)
    rec._queue.put(("x", b"", (1, 1)))
    rec._thread = SimpleNamespace(is_alive=lambda: False)
    with pytest.raises(RuntimeError, match="morreu"):
        rec.capture(synthetic(0))


def test_decimar_depois_de_codificar_regrava_so_com_os_quadros_que_ficaram(tmp_path):
    rec = VideoRecorder(every=1, memory_budget=1_000_000)
    for i in range(40):
        rec.capture(synthetic(i))
    rec._queue.join()
    rec._decimate()    # como se o teto de memória estourasse no fim
    with Image.open(rec.save(str(tmp_path / "v.webp"))) as video:
        assert video.n_frames == 20


def test_add_so_aceita_posicoes_do_espacamento_atual():
    rec = VideoRecorder(every=8)
    raw = bytes(240 * 160 * 3)
    rec.add(8, raw)
    rec.add(12, raw)    # fora da grade
    rec.add(16, raw)
    assert rec.positions() == [8, 16]


# --- gancho no Emulator ----------------------------------------------------------------------

class FakeRunner:
    """Responde `frames` como o runner: uma tela (base64 RGB) a cada `every` quadros."""

    def __init__(self):
        self.frame = 0
        self.calls = []

    def send(self, cmd, **args):
        assert cmd == "frames"
        self.calls.append(args)
        n, every, phase = args["n"], args.get("every"), args.get("phase", 0)
        shots = []
        for i in range(1, n + 1):
            self.frame += 1
            if every and (phase + i) % every == 0:
                shots.append(base64.b64encode(bytes([self.frame % 256]) * (240 * 160 * 3)).decode())
        reply = {"ok": True, "frame": self.frame}
        if every:
            reply["shots"] = shots
        return reply


def make_emulator(recorder):
    emu = emu_module.Emulator.__new__(emu_module.Emulator)
    emu.recorder = recorder
    emu._emulated = 0
    runner = FakeRunner()
    emu._send = runner.send
    return emu, runner


def test_emulator_entrega_um_quadro_a_cada_every_em_frames_hold_e_press():
    rec = VideoRecorder(every=8)
    emu, runner = make_emulator(rec)
    emu.keys = lambda mask: None     # hold/press só avançam quadros neste teste
    emu.frames(5)                     # 5
    emu.hold(1, 2)                    # 7
    emu.press(1, hold=2, release=2)   # 11  -> cruza o quadro 8
    emu.frames(50)                    # 61  -> 16..56 (6 quadros)
    positions = rec.positions()
    assert positions == [8, 16, 24, 32, 40, 48, 56]
    assert runner.frame == 61


def test_emulator_sem_gravador_nao_pede_telas():
    emu, runner = make_emulator(None)
    emu.frames(10)
    assert runner.calls == [{"n": 10}]


def test_emulator_acompanha_o_every_depois_de_decimar():
    rec = VideoRecorder(every=4, memory_budget=1)   # qualquer quadro estoura => decima sempre
    emu, runner = make_emulator(rec)
    emu.frames(40)
    assert len(rec) >= 1            # espera a thread de fundo terminar
    assert rec.grab_every > 4
    assert runner.calls[-1]["every"] == 4          # a 1ª chamada ainda usou o ritmo original
    emu.frames(10)
    assert runner.calls[-1]["every"] == rec.grab_every


class NoShotsRunner(FakeRunner):
    """Runner velho: ignora every/phase e responde sem "shots"."""

    def send(self, cmd, **args):
        reply = super().send(cmd, **args)
        reply.pop("shots", None)
        return reply


def test_runner_sem_suporte_a_telas_desliga_o_video_mas_a_execucao_segue():
    rec = VideoRecorder(every=8)
    emu, _ = make_emulator(rec)
    runner = NoShotsRunner()
    emu._send = runner.send
    assert emu.frames(20) == 20          # não levanta KeyError
    assert rec.failure is not None
    assert emu.frames(5) == 25
    assert "every" not in runner.calls[-1]   # depois da falha, pedidos simples


def test_erro_do_gravador_dentro_de_frames_nao_derruba_a_execucao():
    rec = VideoRecorder(every=8)

    def boom(pos, data):
        raise OSError("disco cheio")
    rec.add_base64 = boom
    emu, runner = make_emulator(rec)
    assert emu.frames(100) == 100
    assert isinstance(rec.failure, OSError)
    assert emu.frames(10) == 110
    assert "every" not in runner.calls[-1]


def test_frames_grande_e_dividido_em_pedacos_com_as_mesmas_telas():
    big_rec = VideoRecorder(every=8)
    big, big_runner = make_emulator(big_rec)
    big.frames(1000)
    small_rec = VideoRecorder(every=8)
    small, _ = make_emulator(small_rec)
    for _ in range(100):
        small.frames(10)
    assert max(call["n"] for call in big_runner.calls) <= emu_module.RECORD_CHUNK
    assert len(big_runner.calls) == 4         # 256 + 256 + 256 + 232
    assert big_rec.positions() == small_rec.positions() == list(range(8, 1001, 8))
    assert [f for _, f in big_rec._frames] == [f for _, f in small_rec._frames]


def test_runner_mais_velho_que_o_fonte_e_recusado(tmp_path, monkeypatch):
    runner, src = tmp_path / "mgba_runner", tmp_path / "mgba_runner.c"
    runner.write_bytes(b"")
    src.write_text("// novo", encoding="utf-8")
    os.utime(runner, (1_000_000, 1_000_000))
    monkeypatch.setattr(emu_module, "RUNNER", runner)
    monkeypatch.setattr(emu_module, "RUNNER_SRC", src)
    with pytest.raises(FileNotFoundError, match="make -C test/harness"):
        emu_module.Emulator("r.gba", str(tmp_path / "s.sav"))


def test_controller_com_recorder_liga_o_gancho_no_emulator():
    from esteira.control import Controller
    rec = VideoRecorder()
    emu = SimpleNamespace(recorder=None)
    Controller(emu, SimpleNamespace(), "unused-out-dir-test", recorder=rec)
    assert emu.recorder is rec


# --- relatório -------------------------------------------------------------------------------

def test_relatorio_com_video_tem_a_tag(tmp_path):
    (tmp_path / "video.webp").write_bytes(b"RIFF")
    html = Path(write_report(Suite(), str(tmp_path), dict(META))).read_text(encoding="utf-8")
    assert '<img src="video.webp"' in html


def test_relatorio_sem_video_nao_tem_a_tag(tmp_path):
    html = Path(write_report(Suite(), str(tmp_path), dict(META))).read_text(encoding="utf-8")
    assert "video.webp" not in html


# --- versionamento ---------------------------------------------------------------------------

def test_version_rom_leva_o_video_junto(tmp_path):
    import os
    import subprocess
    rom = tmp_path / "x.gba"
    rom.write_bytes(b"R")
    report = tmp_path / "rel"
    report.mkdir()
    (report / "relatorio.html").write_text("h", encoding="utf-8")
    (report / "video.webp").write_bytes(b"V")
    environ = {**os.environ, "ESTEIRA_ROMS_DIR": str(tmp_path / "roms")}
    root = Path(__file__).resolve().parents[2]
    done = subprocess.run(["sh", str(root / "version_rom.sh"), str(rom), str(report)], env=environ,
                          capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    assert (tmp_path / "roms" / "1.0" / "video.webp").read_bytes() == b"V"


# --- runner real -----------------------------------------------------------------------------

def test_runner_real_devolve_telas_iguais_ao_screenshot(rom_path, tmp_save, tmp_path):
    """`frames` com every/phase devolve a tela no instante certo e igual ao PNG do screenshot."""
    with emu_module.Emulator(str(rom_path), str(tmp_save)) as plain:
        plain.frames(300)
        ref = plain.screenshot(str(tmp_path / "ref.png"))
    rec = VideoRecorder(every=100)
    with emu_module.Emulator(str(rom_path), str(tmp_save), recorder=rec) as emu:
        emu.frames(300)
    assert rec.positions() == [100, 200, 300]
    last = Image.frombytes("RGB", (240, 160), __import__("zlib").decompress(rec._frames[-1][1]))
    assert last.tobytes() == ref.tobytes()
