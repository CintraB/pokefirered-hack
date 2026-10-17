"""Constantes do jogo (espécies, itens, flags, mapas) lidas dos headers do repo."""

import re
from pathlib import Path

# opponents.h entra porque flags.h usa MAX_TRAINERS_COUNT (em TRAINER_FLAGS_END).
_HEADERS = ["species.h", "items.h", "opponents.h", "flags.h", "map_groups.h"]
_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)(?!\()\s+(.+?)\s*$")
_SAFE = re.compile(r"^[\w\s+\-|&<>()*~]+$")


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


class Constants:
    def __init__(self, defines: dict[str, str]):
        self._defines = defines
        self._cache: dict[str, int] = {}
        self._species_names: dict[int, str] | None = None

    @classmethod
    def load(cls, repo: str) -> "Constants":
        defines: dict[str, str] = {}
        base = Path(repo) / "include" / "constants"
        for header in _HEADERS:
            path = base / header
            if not path.is_file():
                raise FileNotFoundError(f"{path} não existe (map_groups.h é gerado pelo build)")
            for line in _strip_comments(path.read_text(encoding="utf-8")).splitlines():
                m = _DEFINE.match(line)
                if m:
                    defines.setdefault(m.group(1), m.group(2))
        return cls(defines)

    def _eval(self, name: str, stack: tuple[str, ...] = ()) -> int:
        if name in self._cache:
            return self._cache[name]
        if name in stack:
            raise ValueError(f"definição circular: {name}")
        expr = self._defines[name]
        if not _SAFE.match(expr):
            raise ValueError(f"expressão não suportada em {name}: {expr!r}")
        py = re.sub(r"\b(\d+)[uUlL]+\b", r"\1", expr)
        py = re.sub(r"\(\s*(?:u8|u16|u32|s8|s16|s32|int)\s*\)", "", py)

        def sub(m: re.Match) -> str:
            tok = m.group(0)
            if tok[0].isdigit():
                return tok
            return str(self._eval(tok, stack + (name,)))

        value = int(eval(re.sub(r"\b[A-Za-z_0-9]+\b", sub, py), {"__builtins__": {}}))
        self._cache[name] = value
        return value

    def _lookup(self, prefix: str, name: str) -> int:
        if not name.startswith(prefix):
            name = prefix + name
        if name not in self._defines:
            raise KeyError(name)
        return self._eval(name)

    def species(self, name: str) -> int:
        return self._lookup("SPECIES_", name)

    def species_name(self, species_id: int) -> str:
        """Nome da constante (ex.: 'SPECIES_BULBASAUR'); a primeira definida para o id."""
        if self._species_names is None:
            names: dict[int, str] = {}
            for n in self._defines:
                if n.startswith("SPECIES_"):
                    try:
                        names.setdefault(self._eval(n), n)
                    except (ValueError, KeyError, SyntaxError, NameError):
                        pass
            self._species_names = names
        return self._species_names[species_id]

    def item(self, name: str) -> int:
        return self._lookup("ITEM_", name)

    def flag(self, name: str) -> int:
        return self._lookup("FLAG_", name)

    def map(self, name: str) -> tuple[int, int]:
        """(mapGroup, mapNum): em map_groups.h, MAP_X é (num | (group << 8))."""
        value = self._lookup("MAP_", name)
        return value >> 8, value & 0xFF
