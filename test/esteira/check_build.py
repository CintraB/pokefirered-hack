"""Checagem estática do log de build: erros, avisos novos e uso de EWRAM/IWRAM."""

import re
from pathlib import Path

from esteira.result import Result

# `--print-memory-usage` do ld:  "           EWRAM:      261036 B       256 KB     99.58%"
# O uso sai em KB/MB quando é múltiplo exato de 1024 ("EWRAM:  255 KB  256 KB  99.61%").
_MEMORY = re.compile(r"^\s*(EWRAM|IWRAM):\s+(\d+) ([KMG]?B)\s+(\d+ [KMG]?B)\s+([\d.]+)%\s*$")
_UNIT = {"B": 1, "KB": 1 << 10, "MB": 1 << 20, "GB": 1 << 30}
_REGIONS = ("EWRAM", "IWRAM")

# Mensagens do compilador/linker; exige o ':' antes para não pegar nomes de arquivo como
# `src/error_message.c`.
_ERROR = re.compile(r"(?:^|[:\s])(?:fatal error|error):\s|overflowed by")
_WARNING = re.compile(r"(?:^|[:\s])warning:\s")
# Com arquivo e linha, em qualquer caixa: o `as` escreve "Warning:"/"Error:", e o C e o data/*.s
# chegam a ele por pipe, então o arquivo é "{standard input}" (`{standard input}:12: Warning: ...`).
_LOCATED = re.compile(r"^\s*[^:\s][^:]*:\d+:(?:\d+:)?\s*(fatal error|error|warning)\s*:", re.I)
# Erros do make: `make[1]: *** [Makefile:9: x] Error 1`, `make: *** No rule...  Stop.`,
# `Makefile:12: *** missing separator.  Stop.`. Um `*** ` qualquer não (a própria esteira imprime
# `*** ROM NÃO TESTADA ... ***`).
_MAKE_ERROR = re.compile(r"^\s*(?:\S*make(?:\[\d+\])?|[^\s:]+:\d+): \*\*\* ")


def _kind(line: str) -> str | None:
    """Classifica uma linha do log: "erro", "aviso" ou None."""
    located = _LOCATED.match(line)
    if located:
        return "aviso" if located.group(1).lower() == "warning" else "erro"
    if _ERROR.search(line) or _MAKE_ERROR.match(line):
        return "erro"
    if _WARNING.search(line):
        return "aviso"
    return None


def check_build(log_path: str, exceptions: dict) -> list[Result]:
    """Analisa o log de um `make`. Erros e avisos fora de `exceptions["build_warnings"]` e
    EWRAM/IWRAM em 100% ou mais são `falha`; o uso de memória abaixo disso vira um `ok` informativo.
    """
    try:
        lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return [Result("build/log", "falha", f"não foi possível ler o log de build {log_path}: {exc}")]

    allowed = exceptions.get("build_warnings", [])
    results: list[Result] = []
    usage: dict[str, tuple[str, str, str]] = {}

    for line in lines:
        text = line.strip()
        mem = _MEMORY.match(line)
        if mem:
            used = int(mem.group(2)) * _UNIT[mem.group(3)]
            usage[mem.group(1)] = (str(used), mem.group(4), mem.group(5))
            continue
        kind = _kind(line)
        if kind == "erro":
            results.append(Result("build/erro", "falha", text))
        elif kind == "aviso" and not any(a and a in text for a in allowed):
            results.append(Result("build/aviso", "falha", f"aviso de build novo: {text}"))

    for region in _REGIONS:
        if region not in usage:
            results.append(Result(f"build/{region}", "falha",
                                  f"uso de {region} ausente do log (faltou --print-memory-usage?)"))
            continue
        size_b, region_size, percent = usage[region]
        detail = f"{region}: {size_b} B de {region_size} ({percent}%)"
        if float(percent) >= 100.0:
            results.append(Result(f"build/{region}", "falha", f"{detail} - memória esgotada"))
        else:
            results.append(Result(f"build/{region}", "ok", detail))
    return results
