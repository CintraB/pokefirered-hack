"""ESTEIRA_JOBS no Makefile: vira o -j do build da Switch, normalizado como em esteira/paralelo.py
(arquivo à parte: cada `make -n firered_switch` leva ~6 s lendo o Makefile no /mnt/c)."""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _submake_line(*args: str, env_jobs: str | None = None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "ESTEIRA_JOBS"}
    if env_jobs is not None:
        env["ESTEIRA_JOBS"] = env_jobs
    done = subprocess.run(["make", "-n", "firered_switch", "MAKE=true", *args], cwd=REPO_ROOT,
                          env=env, capture_output=True, text=True, timeout=120)
    return next(line for line in done.stdout.splitlines() if line.startswith("true "))


@pytest.mark.parametrize("value, want", [("0", "-j10"), ("abc", "-j10"), ("999", "-j64")])
def test_esteira_jobs_invalido_vira_10_e_tem_teto(value, want):
    line = _submake_line(f"ESTEIRA_JOBS={value}")
    assert re.match(rf"true {want} GAME_VERSION=FIRERED", line), line
