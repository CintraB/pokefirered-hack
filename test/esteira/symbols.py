"""Tabela de símbolos do ELF (via `arm-none-eabi-nm -n`, estáticos inclusos)."""

import shutil
import subprocess
import sys


def _nm_command(elf: str) -> list[str]:
    cmd = ["arm-none-eabi-nm", "-n", elf]
    if shutil.which("arm-none-eabi-nm") is None and sys.platform == "win32":
        cmd = ["wsl.exe", "-d", "Ubuntu", "--", *cmd]
    return cmd


class Symbols:
    def __init__(self, entries: list[tuple[int, str]]):
        self._by_name: dict[str, list[int]] = {}
        self._by_addr: dict[int, str] = {}
        for addr, name in entries:
            self._by_name.setdefault(name, []).append(addr)
            self._by_addr.setdefault(addr, name)

    @classmethod
    def from_elf(cls, elf: str) -> "Symbols":
        out = subprocess.run(_nm_command(elf), check=True, capture_output=True, text=True).stdout
        entries = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) != 3:
                continue
            addr, kind, name = parts
            # 'a'/'A' são constantes absolutas (valor 0), 'U' indefinido; '$' são marcadores ARM
            if kind in "aAUu" or name.startswith("$"):
                continue
            entries.append((int(addr, 16), name))
        return cls(entries)

    def addr(self, name: str) -> int:
        """Endereço do símbolo; KeyError se não existe, ValueError se há mais de um com o nome."""
        addrs = self._by_name[name]
        if len(set(addrs)) > 1:
            raise ValueError(f"símbolo ambíguo {name!r}: {[hex(a) for a in addrs]}")
        return addrs[0]

    def addrs(self, name: str) -> list[int]:
        """Todos os endereços com esse nome (estáticos homônimos de arquivos diferentes)."""
        return sorted(set(self._by_name.get(name, [])))

    def name_at(self, addr: int) -> str | None:
        """Símbolo que começa exatamente em `addr` (None se não houver)."""
        return self._by_addr.get(addr)
