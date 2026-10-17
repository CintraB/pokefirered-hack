"""Integração com o build: test/pipeline.sh, version_rom.sh e a regra $(ROM) do Makefile.

A esteira de verdade (emulador, ~35 s) é trocada por um script falso via ESTEIRA_CMD; as pastas
`roms/` e `test/out/` apontam para diretórios temporários (ESTEIRA_ROMS_DIR, ESTEIRA_OUT_BASE),
então nenhum teste escreve em `roms/` de verdade. Só o último teste compila algo (um erro de
sintaxe numa cópia do repositório) e é lento.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE = REPO_ROOT / "test" / "pipeline.sh"
SWITCH = "pokefirered_switch.gba"

# Esteira falsa: grava os argumentos recebidos, cria o relatório em --out e sai com FAKE_EXIT.
FAKE_ESTEIRA = r"""#!/bin/sh
echo "$@" > "$FAKE_ARGS"
out=""
log=""
while [ $# -gt 0 ]; do
    if [ "$1" = "--out" ]; then out="$2"; fi
    if [ "$1" = "--log" ]; then log="$2"; fi
    shift
done
# como a esteira de verdade: roda em outro diretório, então os caminhos têm de ser legíveis daqui
if [ -n "$log" ] && [ ! -f "$log" ]; then echo "log ilegivel: $log" >&2; exit 3; fi
mkdir -p "$out/img"
echo "<html>relatorio</html>" > "$out/relatorio.html"
echo png > "$out/img/tela.png"
echo "estado grande" > "$out/estado.ss"
exit "${FAKE_EXIT:-0}"
"""


class Env:
    """Diretório temporário com ROM falsa, esteira falsa e pastas de saída isoladas."""

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.roms = tmp / "roms"
        self.out = tmp / "out"
        self.build = tmp / "build"
        self.build.mkdir()
        self.rom = self.build / SWITCH
        self.elf = self.build / "pokefirered_switch.elf"
        self.rom.write_bytes(b"ROM")
        self.elf.write_bytes(b"ELF")
        self.fake = tmp / "fake_esteira.sh"
        self.fake.write_text(FAKE_ESTEIRA, encoding="utf-8", newline="\n")
        self.args_file = tmp / "args.txt"

    def run(self, rom: Path | None = None, **env: str) -> subprocess.CompletedProcess:
        full = {k: v for k, v in os.environ.items()
                if k not in ("COMPARE", "SKIP_TESTS", "BUILD_LOG")}
        full.update({"ESTEIRA_CMD": f"sh {self.fake}", "ESTEIRA_ROMS_DIR": str(self.roms),
                     "ESTEIRA_OUT_BASE": str(self.out), "FAKE_ARGS": str(self.args_file)})
        full.update(env)
        return subprocess.run(["sh", str(PIPELINE), str(rom or self.rom)], capture_output=True,
                              text=True, cwd=self.tmp, env=full, timeout=60)

    def versions(self) -> list[str]:
        if not self.roms.is_dir():
            return []
        return sorted(p.name for p in self.roms.iterdir() if p.name.endswith(".0"))


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def test_green_creates_version_with_report(env):
    result = env.run()
    assert result.returncode == 0, result.stderr
    assert env.versions() == ["1.0"]
    version = env.roms / "1.0"
    assert (version / SWITCH).read_bytes() == b"ROM"
    assert (version / "relatorio.html").is_file()
    assert (version / "img" / "tela.png").is_file()
    assert not (version / "NAO_TESTADA.txt").exists()
    assert not (version / "estado.ss").exists()      # estados de depuração não vão para a versão
    assert env.rom.is_file()                         # ROM do raiz continua lá


def test_green_numbers_after_existing_versions(env):
    (env.roms / "4.0").mkdir(parents=True)
    assert env.run().returncode == 0
    assert env.versions() == ["4.0", "5.0"]


def test_esteira_receives_rom_elf_log_and_out(env):
    log = env.tmp / "build.log"
    log.write_text("compilou\n[esteira] build finished\n", encoding="utf-8")
    assert env.run(BUILD_LOG=str(log)).returncode == 0
    args = env.args_file.read_text(encoding="utf-8").split()
    assert args[0] == "rapido"
    assert args[args.index("--rom") + 1] == str(env.rom)
    assert args[args.index("--elf") + 1] == str(env.elf)
    assert args[args.index("--log") + 1] == str(log)
    out = Path(args[args.index("--out") + 1])
    assert out.parent == env.out and (out / "relatorio.html").is_file()


def test_relative_paths_still_work_after_the_esteira_changes_directory(env):
    """O make passa BUILD_LOG relativo (build/...); a esteira roda em test/."""
    (env.tmp / "build.log").write_text("[esteira] build finished\n", encoding="utf-8")
    result = env.run(rom=Path("build") / SWITCH, BUILD_LOG="build.log",
                     ESTEIRA_OUT_BASE="saida-relativa")
    assert result.returncode == 0, result.stderr
    args = env.args_file.read_text(encoding="utf-8").split()
    assert Path(args[args.index("--log") + 1]).is_absolute()
    assert Path(args[args.index("--out") + 1]).is_absolute()
    assert (env.roms / "1.0" / "relatorio.html").is_file()


def test_without_build_log_no_log_argument(env):
    assert env.run().returncode == 0
    assert "--log" not in env.args_file.read_text(encoding="utf-8").split()


def test_waits_for_the_build_to_finish_writing_the_log(env):
    """O log chega pelo `tee`: a esteira só roda depois da marca de fim de build."""
    log = env.tmp / "build.log"
    log.write_text("compilando...\n", encoding="utf-8")
    writer = subprocess.Popen(
        ["sh", "-c", f"sleep 1; echo '[esteira] build finished' >> {log}"])
    try:
        result = env.run(BUILD_LOG=str(log), ESTEIRA_LOG_WAIT="20")
    finally:
        writer.wait()
    assert result.returncode == 0
    # a esteira falsa só roda depois que o log ficou completo; o pipeline não pode ter pulado a espera
    assert "build finished" in log.read_text(encoding="utf-8")
    assert env.args_file.is_file()


def test_red_keeps_failure_deletes_rom_and_fails(env):
    result = env.run(FAKE_EXIT="1")
    assert result.returncode != 0
    assert env.versions() == []
    failure = env.roms / "ultima-falha"
    assert (failure / "relatorio.html").is_file()
    assert (failure / "estado.ss").is_file()         # a falha guarda tudo para depurar
    assert not env.rom.exists()                      # sem ROM: o próximo make refaz e retesta
    assert not env.elf.exists()                      # o ld precisa rodar de novo (uso de memória no log)


def test_red_replaces_previous_failure_and_does_not_touch_versions(env):
    (env.roms / "ultima-falha").mkdir(parents=True)
    (env.roms / "ultima-falha" / "velho.txt").write_text("de outra rodada", encoding="utf-8")
    (env.roms / "2.0").mkdir()
    assert env.run(FAKE_EXIT="1").returncode != 0
    assert not (env.roms / "ultima-falha" / "velho.txt").exists()
    assert (env.roms / "ultima-falha" / "relatorio.html").is_file()
    assert env.versions() == ["2.0"]


def test_red_deletes_objects_of_files_named_in_the_log(env):
    """Sem isso o reteste não veria os avisos: o make só relinka e o log novo sai limpo."""
    obj = env.tmp / "build" / "firered_switch" / "src" / "foo.o"
    other = env.tmp / "build" / "firered_switch" / "src" / "bar.o"
    obj.parent.mkdir(parents=True)
    obj.write_bytes(b"o")
    other.write_bytes(b"o")
    log = env.tmp / "build.log"
    log.write_text("src/foo.c:10: warning: algo\n[esteira] build finished\n", encoding="utf-8")
    assert env.run(FAKE_EXIT="1", BUILD_LOG=str(log),
                   ESTEIRA_OBJ_DIR=str(env.tmp / "build" / "firered_switch")).returncode != 0
    assert not obj.exists()
    assert other.exists()


def test_skip_tests_versions_as_untested(env):
    result = env.run(SKIP_TESTS="1")
    assert result.returncode == 0
    assert not env.args_file.exists()                # a esteira nem rodou
    version = env.roms / "1.0"
    assert (version / SWITCH).is_file()
    assert (version / "NAO_TESTADA.txt").is_file()
    assert not (version / "relatorio.html").exists()


def test_compare_build_does_nothing(env):
    result = env.run(COMPARE="1")
    assert result.returncode == 0
    assert env.versions() == [] and not env.args_file.exists()
    assert env.rom.is_file()


def test_test_build_is_ignored(env):
    test_rom = env.build / "pokefirered_switch_test.gba"
    test_rom.write_bytes(b"TEST")
    result = env.run(rom=test_rom)
    assert result.returncode == 0
    assert env.versions() == [] and not env.args_file.exists()
    assert test_rom.is_file()


def test_other_builds_are_only_versioned(env):
    other = env.build / "pokefirered.gba"
    other.write_bytes(b"OUTRA")
    assert env.run(rom=other, FAKE_EXIT="1").returncode == 0   # esteira nem é chamada
    assert not env.args_file.exists()
    assert (env.roms / "1.0" / "pokefirered.gba").read_bytes() == b"OUTRA"
    assert not (env.roms / "1.0" / "NAO_TESTADA.txt").exists()


def test_version_rom_script_args(tmp_path):
    """version_rom.sh <rom> [relatorio] [--untested] em qualquer ordem."""
    rom = tmp_path / "x.gba"
    rom.write_bytes(b"R")
    report = tmp_path / "rel"
    (report / "img").mkdir(parents=True)
    (report / "relatorio.html").write_text("h", encoding="utf-8")
    environ = {**os.environ, "ESTEIRA_ROMS_DIR": str(tmp_path / "roms")}
    for args in ([str(rom)], [str(rom), str(report)], [str(rom), "--untested", str(report)]):
        done = subprocess.run(["sh", str(REPO_ROOT / "version_rom.sh"), *args], env=environ,
                              capture_output=True, text=True, cwd=tmp_path)
        assert done.returncode == 0, done.stderr
    roms = tmp_path / "roms"
    assert not (roms / "1.0" / "relatorio.html").exists()
    assert (roms / "2.0" / "relatorio.html").is_file()
    assert (roms / "3.0" / "relatorio.html").is_file() and (roms / "3.0" / "NAO_TESTADA.txt").is_file()


# --- Makefile real -----------------------------------------------------------------------------

def _link_copy(dest: Path) -> None:
    """Cópia da árvore com hardlinks (só o que o build precisa): cria rápido, não duplica 250 MB."""
    skip = {".git", "roms", "test"}
    dest.mkdir()
    for entry in REPO_ROOT.iterdir():
        if entry.name in skip:
            continue
        subprocess.run(["cp", "-al", str(entry), str(dest / entry.name)], check=True)
    # test/pipeline.sh e os scripts de que o Makefile precisa
    shutil.copytree(REPO_ROOT / "test", dest / "test", ignore=shutil.ignore_patterns(
        "out", "__pycache__", "fixtures", "tests", "harness", ".pytest_cache"))


@pytest.mark.skipif(os.environ.get("ESTEIRA_SKIP_SLOW") == "1", reason="ESTEIRA_SKIP_SLOW=1")
def test_compile_error_makes_make_fail():
    """Um erro de sintaxe no C reprova `make firered_switch` (nunca pode parecer verde)."""
    if not (REPO_ROOT / "build" / "firered_switch").is_dir() or not (REPO_ROOT / SWITCH).is_file():
        pytest.skip("precisa de um build anterior de firered_switch (make firered_switch)")
    work = REPO_ROOT / "test" / "out" / f"pipeline-copia-{os.getpid()}"
    shutil.rmtree(work, ignore_errors=True)
    try:
        _link_copy(work)
        # Quebra um arquivo sem tocar nos inodes do original (os hardlinks): remove e recria.
        source = work / "src" / "random.c"
        text = source.read_text(encoding="utf-8")
        source.unlink()
        source.write_text(text + "\nint esteira_erro_de_sintaxe( {\n", encoding="utf-8", newline="\n")
        for stale in (work / "build" / "firered_switch" / "src").glob("random.[od]"):
            stale.unlink()
        roms = work / "roms-isolado"
        env = {**os.environ, "ESTEIRA_ROMS_DIR": str(roms), "ESTEIRA_OUT_BASE": str(work / "saida"),
               "ESTEIRA_CMD": "true"}
        done = subprocess.run(["make", "firered_switch", f"-j{os.cpu_count() or 4}"], cwd=work,
                              env=env, capture_output=True, text=True, timeout=900)
        assert done.returncode != 0, "make saiu 0 apesar do erro de compilação:\n" + done.stdout[-2000:]
        assert not roms.exists(), "nada pode ser versionado quando a compilação falha"
        log = work / "build" / "firered_switch.log"
        assert log.is_file(), "o log do build falho deve ficar em build/firered_switch.log"
        assert "random.c" in log.read_text(encoding="utf-8", errors="replace")
        assert not (log.parent / "firered_switch.log.new").exists()
    finally:
        shutil.rmtree(work, ignore_errors=True)
