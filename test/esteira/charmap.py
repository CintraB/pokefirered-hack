"""Conversão entre bytes de texto do jogo e str, a partir do charmap.txt do repo."""

import re
from pathlib import Path

EOS = 0xFF  # '$' no charmap.txt: terminador de string

# Linhas de caractere único: 'A' = BB   /   '\'' = B4   (macros como PKMN = 53 54 são ignoradas)
_ENTRY = re.compile(r"^'(\\.|[^'\\])'\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+?)\s*(?:@.*)?$")


class Charmap:
    def __init__(self, enc: dict[str, bytes], dec: dict[int, str]):
        self._enc = enc
        self._dec = dec

    @classmethod
    def load(cls, repo: str) -> "Charmap":
        enc: dict[str, bytes] = {}
        dec: dict[int, str] = {}
        for line in (Path(repo) / "charmap.txt").read_text(encoding="utf-8").splitlines():
            m = _ENTRY.match(line.strip())
            if not m:
                continue
            ch = m.group(1)
            if ch.startswith("\\"):
                ch = {"n": "\n", "\\": "\\"}.get(ch[1], ch[1])
            value = bytes.fromhex(m.group(2).replace(" ", ""))
            enc.setdefault(ch, value)
            if len(value) == 1:
                dec.setdefault(value[0], ch)
        return cls(enc, dec)

    def decode(self, b: bytes) -> str:
        """Decodifica até o primeiro 0xFF (EOS); byte desconhecido vira <XX>."""
        out = []
        for byte in b:
            if byte == EOS:
                break
            out.append(self._dec.get(byte, f"<{byte:02X}>"))
        return "".join(out)

    def encode(self, s: str) -> bytes:
        """Codifica sem terminador; levanta KeyError para caractere fora do charmap."""
        return b"".join(self._enc[ch] for ch in s)
