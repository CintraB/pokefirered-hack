"""Modo completo: o `master` (pret original) ainda compila igual ao original.

Roda fora do emulador (ScenarioSpec rom=HOST): `git worktree add` temporário do `master`
num diretório novo em /tmp (ext4 do WSL, bem mais rápido que /mnt/c), copia tools/agbcc
(fora do Git, .gitignore) e roda `make compare_firered_switch`, que confere o SHA1 da ROM com
firered_switch.sha1 e imprime `pokefirered_switch.gba: OK`. A worktree é removida no fim,
também quando algo falha. A saída do make fica em OUT/master.log.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import REPO_ROOT

BRANCH = "master"
TARGET = "compare_firered_switch"
EXPECTED = "pokefirered_switch.gba: OK"
BUILD_TIMEOUT = 3600          # segundos (compilação completa do zero)
GIT_TIMEOUT = 600
TAIL_LINES = 15


def _tail(text: str) -> str:
    return "\n".join(text.strip().splitlines()[-TAIL_LINES:])


def _build_master(repo: Path, runner, tmp_root: Path, log: Path) -> str:
    tmp_root.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="esteira-master-", dir=tmp_root))
    tree = base / "pokefirered"
    git = ["git", "-C", str(repo)]
    try:
        add = runner([*git, "worktree", "add", "--detach", str(tree), BRANCH],
                     capture_output=True, text=True, timeout=GIT_TIMEOUT)
        if add.returncode != 0:
            raise AssertionError(f"git worktree add do {BRANCH} falhou: {_tail(add.stderr)}")
        shutil.copytree(repo / "tools" / "agbcc", tree / "tools" / "agbcc", symlinks=True)
        make = runner(["make", "-C", str(tree), TARGET, f"-j{os.cpu_count() or 1}"],
                      capture_output=True, text=True, timeout=BUILD_TIMEOUT)
        output = make.stdout + make.stderr
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(output, encoding="utf-8")
        if make.returncode != 0 or EXPECTED not in output.splitlines():
            raise AssertionError(f"make {TARGET} saiu com {make.returncode} sem "
                                 f"'{EXPECTED}' (log: {log}):\n{_tail(output)}")
        return f"`make {TARGET}` no {BRANCH} (worktree em {tree}): {EXPECTED}"
    finally:
        # sem `git worktree prune`: rodando no WSL ele apaga o registro das worktrees criadas
        # pelo Git do Windows (caminhos C:/... não existem para o Git do WSL)
        runner([*git, "worktree", "remove", "--force", str(tree)],
               capture_output=True, text=True, timeout=GIT_TIMEOUT)
        shutil.rmtree(base, ignore_errors=True)


def check_master(ctx, repo: Path = REPO_ROOT, runner=subprocess.run,
                 tmp_root: Path = Path("/tmp")) -> None:
    log = Path(ctx.out_dir) / "master.log"
    ctx.suite.run(f"master: `make {TARGET}` numa worktree temporária do {BRANCH}",
                  lambda: _build_master(Path(repo), runner, Path(tmp_root), log))


def run_full_master(ctx) -> None:
    """Cenário sem emulador (rom=HOST): só usa ctx.suite e ctx.out_dir."""
    check_master(ctx)
