"""Cliente Python do runner headless do mGBA (test/harness/mgba_runner).

Fala o protocolo de uma linha JSON por comando pelo stdin/stdout do runner.
"""

import json
import subprocess
from pathlib import Path

from PIL import Image

RUNNER = Path(__file__).resolve().parent.parent / "harness" / "mgba_runner"

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


class EmulatorError(RuntimeError):
    """O runner respondeu {"ok": false} ou morreu."""


class Emulator:
    """Uma instância do mGBA rodando `rom` com o save em `save` (nunca em roms/saves/)."""

    def __init__(self, rom: str, save: str):
        if not RUNNER.is_file():
            raise FileNotFoundError(f"{RUNNER} não existe; rode `make -C test/harness`")
        self._proc = subprocess.Popen(
            [str(RUNNER), str(rom), "--save", str(save)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def _send(self, cmd: str, **args) -> dict:
        if self._proc.poll() is not None:
            raise EmulatorError(f"runner encerrado (código {self._proc.returncode})")
        line = json.dumps({"cmd": cmd, **args}, ensure_ascii=False)
        try:
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
        except BrokenPipeError as exc:
            raise EmulatorError("runner encerrado") from exc
        reply = self._proc.stdout.readline()
        if not reply:
            self._proc.wait()
            raise EmulatorError(f"runner encerrado (código {self._proc.returncode}) durante {cmd!r}")
        data = json.loads(reply)
        if not data.get("ok"):
            raise EmulatorError(f"{cmd}: {data.get('error')}")
        return data

    def frames(self, n: int) -> int:
        """Avança n quadros; devolve o contador de quadros do core."""
        return self._send("frames", n=n)["frame"]

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
