"""Cliente Python do runner headless do mGBA (test/harness/mgba_runner).

Fala o protocolo de uma linha JSON por comando pelo stdin/stdout do runner.
"""

import json
import subprocess
from pathlib import Path

from PIL import Image

from .video import VideoRecorder

RUNNER = Path(__file__).resolve().parent.parent / "harness" / "mgba_runner"
RUNNER_SRC = RUNNER.with_suffix(".c")
RECORD_CHUNK = 256   # quadros por pedido `frames` quando gravando vídeo (limita o tamanho da resposta)

KEY_A = 1
KEY_B = 2
KEY_SELECT = 4
KEY_START = 8
KEY_RIGHT = 16
KEY_LEFT = 32
KEY_UP = 64
KEY_DOWN = 128
KEY_R = 256
KEY_L = 512


WINDOW_CLOSED_EXIT = 3   # código de saída do runner quando a janela (--window) é fechada


class EmulatorError(RuntimeError):
    """O runner respondeu {"ok": false} ou morreu."""


class WindowClosed(EmulatorError):
    """Quem assistia fechou a janela do modo --window (o runner gravou o .sav e saiu)."""


class Emulator:
    """Uma instância do mGBA rodando `rom` com o save em `save` (nunca em roms/saves/)."""

    def __init__(self, rom: str, save: str, recorder: "VideoRecorder | None" = None,
                 window: bool = False):
        """`recorder`: se dado, recebe uma tela a cada `recorder.grab_every` quadros emulados,
        em TODA chamada que avança o jogo (frames/hold/press, inclusive as feitas direto por
        helpers de cenário), sem passo extra para quem chama.

        `window`: o runner abre uma janela SDL2 e emula em tempo real (~59,73 quadros/s) com
        áudio (modo `assistir`); não combina com `recorder` (o vídeo é do modo automático)."""
        if window and recorder is not None:
            raise ValueError("janela (assistir) e gravação de vídeo não combinam: use um só")
        self.recorder = recorder
        self._emulated = 0   # quadros avançados por frames() nesta sessão (posição no vídeo)
        if not RUNNER.is_file():
            raise FileNotFoundError(f"{RUNNER} não existe; rode `make -C test/harness`")
        if RUNNER_SRC.is_file() and RUNNER_SRC.stat().st_mtime > RUNNER.stat().st_mtime + 1:
            raise FileNotFoundError(f"{RUNNER} é mais velho que {RUNNER_SRC.name}; "
                                    "rode `make -C test/harness`")
        self._proc = subprocess.Popen(
            [str(RUNNER), str(rom), "--save", str(save), *(["--window"] if window else [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def _died(self, what: str) -> EmulatorError:
        code = self._proc.returncode
        cls = WindowClosed if code == WINDOW_CLOSED_EXIT else EmulatorError
        return cls(f"runner encerrado (código {code}){what}")

    def _send(self, cmd: str, **args) -> dict:
        if self._proc.poll() is not None:
            raise self._died("")
        line = json.dumps({"cmd": cmd, **args}, ensure_ascii=False)
        try:
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
        except BrokenPipeError as exc:
            self._proc.wait()
            raise self._died("") from exc
        reply = self._proc.stdout.readline()
        if not reply:
            self._proc.wait()
            raise self._died(f" durante {cmd!r}")
        data = json.loads(reply)
        if not data.get("ok"):
            raise EmulatorError(f"{cmd}: {data.get('error')}")
        return data

    def frames(self, n: int) -> int:
        """Avança n quadros; devolve o contador de quadros do core."""
        rec = self.recorder
        if rec is None or rec.failure is not None or n <= 0:
            return self._send("frames", n=n)["frame"]
        frame = 0
        while n > 0:   # em pedaços: a resposta carrega ~154 KB por tela
            frame = self._frames_recording(rec, min(n, RECORD_CHUNK))
            n -= RECORD_CHUNK
        return frame

    def _frames_recording(self, rec: "VideoRecorder", n: int) -> int:
        """Um pedaço de `frames` com telas na grade do gravador. Problema com o vídeo (runner
        sem suporte, tela inválida) desliga a gravação (`rec.fail`), nunca a execução."""
        every, start = rec.grab_every, self._emulated
        data = self._send("frames", n=n, every=every, phase=start % every)
        self._emulated = start + n
        try:
            shots = data["shots"]
            first = start + every - start % every   # 1ª posição múltipla de `every` após start
            for i, shot in enumerate(shots):
                rec.add_base64(first + i * every, shot)
        except Exception as exc:  # noqa: BLE001
            rec.fail(exc)
        return data["frame"]

    def keys(self, mask: int) -> None:
        """Mantém `mask` pressionado até a próxima chamada de keys()."""
        self._send("keys", mask=mask)

    def hold(self, mask: int, n: int) -> None:
        """Segura `mask` por n quadros e solta."""
        self.keys(mask)
        self.frames(n)
        self.keys(0)

    def press(self, mask: int, hold: int = 2, release: int = 2) -> None:
        """Toque: segura `hold` quadros e espera `release` quadros soltos."""
        self.hold(mask, hold)
        self.frames(release)

    def read(self, addr: int, n: int) -> bytes:
        return bytes.fromhex(self._send("read", addr=addr, len=n)["hex"])

    def read_u8(self, addr: int) -> int:
        return self.read(addr, 1)[0]

    def read_u16(self, addr: int) -> int:
        return int.from_bytes(self.read(addr, 2), "little")

    def read_u32(self, addr: int) -> int:
        return int.from_bytes(self.read(addr, 4), "little")

    def write(self, addr: int, data: bytes) -> None:
        self._send("write", addr=addr, hex=bytes(data).hex())

    def screenshot(self, path: str) -> Image.Image:
        """Grava a tela atual (PNG 240x160) em `path` e devolve a imagem RGB."""
        self._send("screenshot", path=str(path))
        with Image.open(path) as img:
            return img.convert("RGB")

    def save_state(self, path: str) -> None:
        self._send("state_save", path=str(path))

    def load_state(self, path: str) -> None:
        self._send("state_load", path=str(path))

    def reset(self) -> None:
        self._send("reset")

    def flush_save(self) -> None:
        """Grava agora no .sav o save do jogo que está na memória do emulador (sem isso o mGBA
        só grava ao fechar, e um save vindo de savestate fica só na memória até lá)."""
        self._send("flush_save")

    def close(self) -> None:
        """Grava o .sav e encerra o runner. Pode ser chamado mais de uma vez."""
        if self._proc.poll() is None:
            try:
                self._send("quit")
            finally:
                self._proc.stdin.close()
                self._proc.wait(timeout=10)
        self._proc.stdout.close()

    def __enter__(self) -> "Emulator":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
