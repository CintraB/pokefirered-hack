"""ESTEIRA_JOBS no Makefile sem valor e com -j explícito (à parte de test_makefile_jobs.py para
os dois rodarem em workers diferentes: cada `make -n` leva ~6 s no /mnt/c)."""

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


def test_sem_esteira_jobs_e_10_e_um_j_explicito_vale():
    assert _submake_line().startswith("true -j10 ")
    assert _submake_line(env_jobs="3").startswith("true -j3 ")
    assert _submake_line("-j5").split()[:2] == ["true", "GAME_VERSION=FIRERED"]   # jobserver do -j5
