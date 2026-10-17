"""Vídeo acelerado da execução da esteira: WebP animado (Pillow, sem ffmpeg).

Um quadro a cada `every` quadros emulados, tocado a 30 fps (o jogo roda a 60 fps; com `every` = 8
o vídeo passa a 4x a velocidade do jogo).

Custo: a compressão do quadro e a codificação WebP (~1,5 ms por quadro) rodam numa thread de
fundo durante a execução, em paralelo com o emulador (o codificador do Pillow solta o GIL), para
o vídeo custar pouco tempo a mais; `save()` só espera o que sobrou na fila. A codificação
incremental usa `PIL._webp.WebPAnimEncoder` (API interna do Pillow); se ela não existir ou mudar,
`save()` cai na API pública (`Image.save(save_all=True)`), que só é mais lenta e gasta mais memória.

Tetos (os três resolvidos aumentando `every`, ou seja, descartando metade dos quadros guardados):
- quantidade: mais de `max_frames` quadros (estimativa do que cabe em `max_bytes`);
- memória: os quadros guardados (zlib nível 1) passam de `memory_budget` bytes;
- arquivo: o WebP gravado passa de `max_bytes` (25 MB), regravado até caber.
Os quadros ficam na memória comprimidos para poder regravar o WebP depois de uma decimação.
"""

import base64
import queue
import threading
import zlib
from pathlib import Path
from typing import Iterable

from PIL import Image

try:   # codificador incremental do Pillow (API interna): opcional
    from PIL import _webp
except ImportError:   # pragma: no cover
    _webp = None

FPS = 30
FRAME_MS = round(1000 / FPS)
MAX_BYTES = 25 * 1024 * 1024
MEMORY_BUDGET = 256 * 1024 * 1024
SCREEN_SIZE = (240, 160)
QUALITY = 50          # WebP com perdas: a tela do GBA tem poucas cores, o que pesa é o volume
METHOD = 2            # 0 (rápido) .. 6 (lento)
EST_FRAME_BYTES = 4096   # tamanho típico de um quadro no WebP (medido: ~4 KB), p/ max_frames
QUEUE_DEPTH = 256        # quadros brutos esperando a thread; cheia => quem captura espera


class _Stream:
    """Codificador incremental de WebP animado (quadros de duração fixa)."""

    def __init__(self, quality: int):
        self.quality = float(quality)
        self.count = 0
        self._enc = None   # criado no 1º quadro (precisa do tamanho)

    def add(self, img: Image.Image) -> None:
        if self._enc is None:
            self._enc = _webp.WebPAnimEncoder(img.size, 0, 0, False, 3, 5, False, False)
        self._enc.add(img.getim(), self.count * FRAME_MS, False, self.quality, 100.0, METHOD)
        self.count += 1

    def finish(self) -> bytes:
        self._enc.add(None, self.count * FRAME_MS, False, self.quality, 100.0, 0)
        data = self._enc.assemble("", "", "")
        if data is None:
            raise OSError("o codificador WebP não devolveu dados")
        return data


class VideoRecorder:
    """`every`: um quadro a cada `every` quadros emulados; `scale`: ampliação inteira (vizinho
    mais próximo) só na gravação do WebP.

    Dois jeitos de entregar quadros:
    - `capture(img)`: chamado para TODO quadro emulado; o gravador fica com os de índice
      0, every, 2*every... (100 quadros com every=8 => 13 guardados);
    - `add(pos, rgb)`: quadro já amostrado por quem o pediu ao emulador (Emulator.frames), `pos`
      é o contador de quadros emulados em que ele foi tirado; só é aceito se for múltiplo do
      `grab_every` atual (o emulador consulta `grab_every` a cada chamada, então o ritmo
      acompanha os aumentos automáticos e quase nenhum quadro desperdiçado trafega).
    """

    def __init__(self, every: int = 8, scale: int = 1, max_bytes: int = MAX_BYTES,
                 memory_budget: int = MEMORY_BUDGET, quality: int = QUALITY):
        if every < 1 or scale < 1:
            raise ValueError("every e scale devem ser >= 1")
        self.every = every
        self.scale = scale
        self.max_bytes = max_bytes
        self.max_frames = max(2, max_bytes // EST_FRAME_BYTES)
        self.memory_budget = memory_budget
        self.quality = quality
        self.size = SCREEN_SIZE
        self._seen = 0                 # quadros oferecidos a capture()
        # Estado abaixo: só a thread de fundo escreve (leitura segura depois de _flush()).
        self._frames: list[tuple[int, bytes]] = []   # (posição em quadros emulados, zlib(RGB))
        self._bytes = 0
        self._stream: _Stream | None = None if _webp is None else _Stream(quality)
        self._error: Exception | None = None
        self._queue: queue.Queue = queue.Queue(maxsize=QUEUE_DEPTH)
        self._thread: threading.Thread | None = None

    # --- entrada (thread principal) --------------------------------------------------
    @property
    def grab_every(self) -> int:
        """Espaçamento atual (em quadros emulados) entre os quadros guardados."""
        return self.every

    def __len__(self) -> int:
        self._flush()
        return len(self._frames)

    def positions(self) -> list[int]:
        """Posições (quadros emulados) dos quadros guardados."""
        self._flush()
        return [pos for pos, _ in self._frames]

    def capture(self, img: Image.Image) -> None:
        pos = self._seen
        self._seen += 1
        if pos % self.every == 0:
            self._submit(pos, img.convert("RGB").tobytes(), img.size)

    def add(self, pos: int, rgb: bytes) -> None:
        if pos % self.every == 0:
            self._submit(pos, rgb, SCREEN_SIZE)

    def add_base64(self, pos: int, data: str) -> None:
        """`data`: um item de "shots" do runner (RGB 240x160 em base64)."""
        if pos % self.every == 0:
            self._submit(pos, base64.b64decode(data), SCREEN_SIZE)

    def _submit(self, pos: int, rgb: bytes, size: tuple[int, int]) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._work, name="video", daemon=True)
            self._thread.start()
        self._queue.put((pos, rgb, size))

    def _flush(self) -> None:
        self._queue.join()

    # --- thread de fundo ---------------------------------------------------------------
    def _work(self) -> None:
        while True:
            pos, rgb, size = self._queue.get()
            try:
                if self._error is None:
                    self._ingest(pos, rgb, size)
            except Exception as exc:  # noqa: BLE001 - reaparece em save()
                self._error = exc
            finally:
                self._queue.task_done()

    def _ingest(self, pos: int, rgb: bytes, size: tuple[int, int]) -> None:
        if pos % self.every:   # o espaçamento aumentou depois que o quadro foi pedido
            return
        self.size = size
        packed = zlib.compress(rgb, 1)
        self._frames.append((pos, packed))
        self._bytes += len(packed)
        if self._stream is not None:
            self._stream.add(self._image(rgb))
        while ((self._bytes > self.memory_budget or len(self._frames) > self.max_frames)
               and len(self._frames) > 1):
            self._decimate()

    def _decimate(self) -> None:
        """Dobra `every`: fica só com os quadros em posição múltipla do novo espaçamento. O
        WebP incremental já codificado deixa de valer (será refeito em save())."""
        self.every *= 2
        kept = [(p, b) for p, b in self._frames if p % self.every == 0]
        self._frames = kept or self._frames[-1:]   # nunca esvazia o vídeo
        self._bytes = sum(len(b) for _, b in self._frames)
        self._stream = None

    # --- saída -----------------------------------------------------------------------
    def _image(self, rgb: bytes) -> Image.Image:
        img = Image.frombytes("RGB", self.size, rgb)
        if self.scale > 1:
            img = img.resize((self.size[0] * self.scale, self.size[1] * self.scale),
                             Image.NEAREST)
        return img

    def _images(self) -> Iterable[Image.Image]:
        for _, packed in self._frames:
            yield self._image(zlib.decompress(packed))

    def _encode_all(self) -> bytes:
        """Codifica os quadros guardados do zero."""
        if _webp is not None:
            stream = _Stream(self.quality)
            for img in self._images():
                stream.add(img)
            return stream.finish()
        images = list(self._images())   # API pública do Pillow: precisa de todos na memória
        import io
        buf = io.BytesIO()
        images[0].save(buf, format="WEBP", save_all=True, append_images=images[1:],
                       duration=FRAME_MS, loop=0, quality=self.quality, method=METHOD)
        return buf.getvalue()

    def save(self, path: str) -> str:
        """Grava o WebP animado em `path` (30 fps) e devolve o caminho. Se passar de `max_bytes`,
        aumenta `every` (descarta metade dos quadros) e grava de novo, até caber. Sem quadros:
        ValueError."""
        self._flush()
        if self._error is not None:
            raise self._error
        if not self._frames:
            raise ValueError("nenhum quadro capturado")
        stream, self._stream = self._stream, None
        data = None
        if stream is not None and stream.count == len(self._frames):
            data = stream.finish()   # codificado durante a execução
        while True:
            if data is None:
                data = self._encode_all()
            if len(data) <= self.max_bytes or len(self._frames) < 2:
                break
            self._decimate()
            data = None
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
        return str(target)
