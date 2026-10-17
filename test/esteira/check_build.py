"""Checagem estática do log de build: erros, avisos novos e uso de EWRAM/IWRAM."""

import re
from pathlib import Path

from esteira.result import Result

# `--print-memory-usage` do ld:  "           EWRAM:      261036 B       256 KB     99.58%"
_MEMORY = re.compile(r"^\s*(EWRAM|IWRAM):\s+(\d+) B\s+(\d+ [KMG]?B)\s+([\d.]+)%\s*$")
_REGIONS = ("EWRAM", "IWRAM")

# Mensagens do compilador/linker/make; exige o ':' antes para não pegar nomes de arquivo
# como `src/error_message.c`.
_ERROR = re.compile(r"(?:^|[:\s])(?:fatal error|error):\s|overflowed by|\*\*\* ")  # `make: *** ...`
_WARNING = re.compile(r"(?:^|[:\s])warning:\s")


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
            usage[mem.group(1)] = (mem.group(2), mem.group(3), mem.group(4))
        elif _ERROR.search(line):
            results.append(Result("build/erro", "falha", text))
        elif _WARNING.search(line) and not any(a and a in text for a in allowed):
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
