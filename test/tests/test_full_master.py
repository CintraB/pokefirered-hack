"""Cenário `master` sem compilar de verdade: comandos, veredito e limpeza da worktree."""

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from esteira.result import Suite
from esteira.scenarios import full_master


class FakeRunner:
    """Registra os comandos; `make` responde com `make_out`/`make_code`."""

    def __init__(self, make_out: str, make_code: int = 0, fail_add: bool = False):
        self.calls: list[list[str]] = []
        self.make_out, self.make_code, self.fail_add = make_out, make_code, fail_add
        self.worktree: Path | None = None

    def __call__(self, cmd, **kwargs):
        self.calls.append(list(cmd))
        if cmd[:2] == ["git", "-C"] and "add" in cmd:
            if self.fail_add:
                return subprocess.CompletedProcess(cmd, 128, "", "fatal: invalid reference")
            self.worktree = Path(cmd[-2])
            (self.worktree / "tools").mkdir(parents=True)
        if cmd[0] == "make":
            self.agbcc_copied = (self.worktree / "tools" / "agbcc" / "bin" / "agbcc").is_file()
            return subprocess.CompletedProcess(cmd, self.make_code, self.make_out, "")
        return subprocess.CompletedProcess(cmd, 0, "", "")


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "tools" / "agbcc" / "bin").mkdir(parents=True)
    (root / "tools" / "agbcc" / "bin" / "agbcc").write_text("x")
    return root


def run(repo, tmp_path, runner):
    suite = Suite()
    ctx = SimpleNamespace(suite=suite, out_dir=str(tmp_path / "out"))
    full_master.check_master(ctx, repo=repo, runner=runner, tmp_root=tmp_path / "tmp")
    return suite.results


def test_master_ok_quando_o_sha1_confere_e_remove_a_worktree(repo, tmp_path):
    runner = FakeRunner("...\npokefirered_switch.gba: OK\n")
    [result] = run(repo, tmp_path, runner)
    assert result.status == "ok", result.detail
    cmds = [" ".join(c) for c in runner.calls]
    assert any("worktree add --detach" in c and c.endswith(" master") for c in cmds)
    assert any(c.startswith("make -C") and "compare_firered_switch" in c for c in cmds)
    assert any("worktree remove --force" in c for c in cmds)
    assert runner.agbcc_copied                     # tools/agbcc (fora do Git) copiado antes do make
    assert not (tmp_path / "tmp").exists() or not any((tmp_path / "tmp").iterdir())
    assert (tmp_path / "out" / "master.log").is_file()


def test_master_falha_sem_ok_e_ainda_remove_a_worktree(repo, tmp_path):
    runner = FakeRunner("pokefirered_switch.gba: FAILED\n", make_code=2)
    [result] = run(repo, tmp_path, runner)
    assert result.status == "falha"
    assert "pokefirered_switch.gba: FAILED" in result.detail
    assert any("worktree remove --force" in " ".join(c) for c in runner.calls)


def test_master_falha_se_a_worktree_nao_pode_ser_criada(repo, tmp_path):
    runner = FakeRunner("", fail_add=True)
    [result] = run(repo, tmp_path, runner)
    assert result.status == "falha" and "invalid reference" in result.detail
    assert not any(c[0] == "make" for c in runner.calls)
