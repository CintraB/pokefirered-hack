"""Integração com o build: test/pipeline.sh, version_rom.sh e a regra $(ROM) do Makefile.

A esteira de verdade (emulador, ~35 s) é trocada por um script falso via ESTEIRA_CMD; as pastas
`roms/` e `test/out/` apontam para diretórios temporários (ESTEIRA_ROMS_DIR, ESTEIRA_OUT_BASE),
então nenhum teste escreve em `roms/` de verdade. Só o último teste compila algo (um erro de
sintaxe numa cópia do repositório) e é lento.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE = REPO_ROOT / "test" / "pipeline.sh"
SWITCH = "pokefirered_switch.gba"

MARKER = "[esteira] build finished"
MEMORY = """Memory region         Used Size  Region Size  %age Used
           EWRAM:      261036 B       256 KB     99.58%
           IWRAM:       30096 B        32 KB     91.85%
             ROM:    15404028 B        32 MB     45.91%
"""

# Esteira falsa: grava os argumentos recebidos, cria o relatório em --out e sai com FAKE_EXIT
# (FAKE_NO_REPORT=1: sai sem relatório, como um crash). Se o log recebido já tinha a marca de fim
# de build quando a esteira COMEÇOU, grava $FAKE_ARGS.marker.
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
if [ -n "$log" ] && grep -qF "[esteira] build finished" "$log"; then echo yes > "$FAKE_ARGS.marker"; fi
if [ "${FAKE_NO_REPORT:-0}" = 1 ]; then exit "${FAKE_EXIT:-0}"; fi
mkdir -p "$out/img"
echo "<html>relatorio</html>" > "$out/relatorio.html"
echo png > "$out/img/tela.png"
echo "estado grande" > "$out/estado.ss"
exit "${FAKE_EXIT:-0}"
"""


# Esteira "semi-real": só a checagem de build de verdade (check_build) sobre o --log recebido.
CHECKER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from esteira.check_build import check_build
args = sys.argv[2:]
log, out = args[args.index("--log") + 1], args[args.index("--out") + 1]
results = check_build(log, {})
Path(out).mkdir(parents=True, exist_ok=True)
(Path(out) / "relatorio.html").write_text("<html>" + repr(results) + "</html>", encoding="utf-8")
sys.exit(1 if any(r.status == "falha" for r in results) else 0)
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
                     "ESTEIRA_OUT_BASE": str(self.out), "FAKE_ARGS": str(self.args_file),
                     "ESTEIRA_RUNNER_MAKE": "true"})
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


def test_runner_do_emulador_e_atualizado_antes_da_esteira(env):
    """O runner (C) é refeito se o fonte mudou, antes de a esteira rodar."""
    marker = env.tmp / "runner-made"
    result = env.run(ESTEIRA_RUNNER_MAKE=f"touch {marker}")
    assert result.returncode == 0, result.stderr
    assert marker.is_file()


def test_falha_ao_compilar_o_runner_e_falha_de_infraestrutura(env):
    result = env.run(ESTEIRA_RUNNER_MAKE="false")
    assert result.returncode == 1
    assert "runner do emulador" in result.stderr
    assert env.versions() == [] and not env.rom.exists()
    assert not env.args_file.exists()        # a esteira nem rodou


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
    out = Path(args[args.index("--out") + 1])
    assert out.parent == env.out and (out / "relatorio.html").is_file()
    # a esteira lê uma cópia do log (cortada na marca) guardada junto da execução
    assert Path(args[args.index("--log") + 1]) == out / "build.log"
    assert "compilou" in (out / "build.log").read_text(encoding="utf-8")


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


def test_without_build_log_warns_and_passes_no_log_argument(env):
    result = env.run()
    assert result.returncode == 0
    assert "--log" not in env.args_file.read_text(encoding="utf-8").split()
    assert "sem log de build: checagens de compilação puladas; use make firered_switch" \
        in result.stdout


def test_without_build_log_still_checks_memory_from_the_linker_file(env):
    memory = env.tmp / "build" / "firered_switch" / "memory.txt"
    memory.parent.mkdir(parents=True)
    memory.write_text(MEMORY, encoding="utf-8")
    result = env.run()
    assert result.returncode == 0
    args = env.args_file.read_text(encoding="utf-8").split()
    assert "EWRAM:" in Path(args[args.index("--log") + 1]).read_text(encoding="utf-8")
    assert "sem log de build" in result.stdout


def test_waits_for_the_build_to_finish_writing_the_log(env):
    """O log chega pelo `tee`: a esteira só roda depois da marca de fim de build."""
    log = env.tmp / "build.log"
    log.write_text("compilando...\n", encoding="utf-8")
    writer = subprocess.Popen(["sh", "-c", f"sleep 1; echo '{MARKER}' >> {log}"])
    try:
        result = env.run(BUILD_LOG=str(log), ESTEIRA_LOG_WAIT="20")
    finally:
        writer.wait()
    assert result.returncode == 0, result.stderr
    # a marca já estava no log que a esteira recebeu quando ela COMEÇOU: o pipeline esperou
    assert (env.tmp / "args.txt.marker").read_text(encoding="utf-8").strip() == "yes"


def test_log_that_never_finishes_fails_closed(env):
    """Sem a marca de fim o log pode estar incompleto: nada de testar nem versionar."""
    log = env.tmp / "build.log"
    log.write_text("compilando...\n", encoding="utf-8")
    result = env.run(BUILD_LOG=str(log), ESTEIRA_LOG_WAIT="1")
    assert result.returncode != 0
    assert "falha de infraestrutura" in result.stderr
    assert not env.args_file.exists()                # a esteira nem rodou
    assert env.versions() == []
    assert not (env.roms / "ultima-falha").exists()
    assert not env.rom.exists()                      # o próximo make retesta


def test_red_keeps_failure_deletes_rom_and_fails(env):
    result = env.run(FAKE_EXIT="1")
    assert result.returncode != 0
    assert "REPROVADA" in result.stderr and "infraestrutura" not in result.stderr
    assert env.versions() == []
    failure = env.roms / "ultima-falha"
    assert (failure / "relatorio.html").is_file()
    assert (failure / "estado.ss").is_file()         # a falha guarda tudo para depurar
    assert not env.rom.exists()                      # sem ROM: o próximo make refaz e retesta
    assert env.elf.exists()                          # o ELF fica: a memória do ld está em memory.txt


@pytest.mark.parametrize("code, no_report", [("127", "0"), ("130", "0"), ("2", "0"), ("1", "1")])
def test_infrastructure_failure_is_not_a_test_failure(env, code, no_report):
    """python ausente (127), Ctrl-C (130), crash sem relatório: não versiona, não vira ultima-falha."""
    (env.roms / "ultima-falha").mkdir(parents=True)
    (env.roms / "ultima-falha" / "velho.txt").write_text("falha real anterior", encoding="utf-8")
    result = env.run(FAKE_EXIT=code, FAKE_NO_REPORT=no_report)
    assert result.returncode != 0
    assert "falha de infraestrutura" in result.stderr and f"código {code}" in result.stderr
    assert env.versions() == []
    assert (env.roms / "ultima-falha" / "velho.txt").exists()   # não sobrescreve a falha real
    assert not env.rom.exists()                      # sem ROM o próximo make retesta
    assert env.elf.exists()


def test_retest_after_interruption_has_memory_data(env):
    """Ctrl-C: o make apaga só a ROM, o objcopy roda sem o ld e o log sai sem EWRAM/IWRAM.

    O uso de memória vem de build/<nome>/memory.txt (gravado no link): com a esteira de verdade
    (check_build) não pode haver falha espúria."""
    checker = env.tmp / "checker.py"
    checker.write_text(CHECKER, encoding="utf-8", newline="\n")
    cmd = f"{sys.executable} {checker} {REPO_ROOT / 'test'}"
    log = env.tmp / "build.log"
    log.write_text(f"arm-none-eabi-objcopy -O binary x.elf x.gba\n{MARKER}\n", encoding="utf-8")

    # controle: sem memory.txt o log "só objcopy" reprova (era o bug)
    assert env.run(BUILD_LOG=str(log), ESTEIRA_CMD=cmd).returncode != 0
    assert env.versions() == []

    memory = env.tmp / "build" / "firered_switch" / "memory.txt"
    memory.parent.mkdir(parents=True)
    memory.write_text(MEMORY, encoding="utf-8")
    env.rom.write_bytes(b"ROM")
    result = env.run(BUILD_LOG=str(log), ESTEIRA_CMD=cmd)
    assert result.returncode == 0, result.stdout + result.stderr
    assert env.versions() == ["1.0"]


def test_memory_file_is_not_duplicated_when_the_log_already_has_it(env):
    log = env.tmp / "build.log"
    log.write_text(f"{MEMORY}{MARKER}\n", encoding="utf-8")
    memory = env.tmp / "build" / "firered_switch" / "memory.txt"
    memory.parent.mkdir(parents=True)
    memory.write_text(MEMORY.replace("99.58", "10.00"), encoding="utf-8")
    assert env.run(BUILD_LOG=str(log)).returncode == 0
    args = env.args_file.read_text(encoding="utf-8").split()
    seen = Path(args[args.index("--log") + 1]).read_text(encoding="utf-8")
    assert seen.count("EWRAM:") == 1 and "99.58" in seen


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
    # o que vem depois da marca é da própria esteira (ela cita arquivos que não são do build)
    log.write_text(f"src/foo.c:10: warning: algo\n{MARKER}\nsrc/bar.c:3: citado pela esteira\n",
                   encoding="utf-8")
    assert env.run(FAKE_EXIT="1", BUILD_LOG=str(log),
                   ESTEIRA_OBJ_DIR=str(env.tmp / "build" / "firered_switch")).returncode != 0
    assert not obj.exists()
    assert other.exists()


def test_skip_tests_versions_with_a_not_tested_report(env):
    result = env.run(SKIP_TESTS="1")
    assert result.returncode == 0
    args = env.args_file.read_text(encoding="utf-8").split()
    assert args[0] == "nao-testada" and "rapido" not in args   # sem emulador, sem checagens
    assert "--rom" not in args
    version = env.roms / "1.0"
    assert (version / SWITCH).is_file()
    assert (version / "NAO_TESTADA.txt").is_file()
    assert (version / "relatorio.html").is_file()    # o relatório "NÃO TESTADA" vai junto


def test_skip_tests_still_versions_if_the_report_cannot_be_written(env):
    result = env.run(SKIP_TESTS="1", FAKE_EXIT="127", FAKE_NO_REPORT="1")
    assert result.returncode == 0
    assert (env.roms / "1.0" / "NAO_TESTADA.txt").is_file()
    assert not (env.roms / "1.0" / "relatorio.html").exists()


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


def test_version_rom_never_versions_a_test_build(tmp_path):
    """A build de teste (TESTBUILD=1) tem os atalhos em C: nunca vira versão, nem chamada direto."""
    rom = tmp_path / "pokefirered_switch_test.gba"
    rom.write_bytes(b"T")
    environ = {**os.environ, "ESTEIRA_ROMS_DIR": str(tmp_path / "roms")}
    done = subprocess.run(["sh", str(REPO_ROOT / "version_rom.sh"), str(rom), "--untested"],
                          env=environ, capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    assert "Not versioning test build" in done.stdout
    assert not (tmp_path / "roms").exists()




def test_red_with_assembler_warning_rebuilds_everything_this_build_assembled(env):
    """`as` por pipe diz "{standard input}:N: Warning:" (sem o arquivo): o reteste tem de montar
    de novo o que este build montou e relinkar, senão o aviso some e o vermelho vira verde."""
    obj_dir = env.tmp / "build" / "firered_switch"
    data_obj = obj_dir / "data" / "event_scripts.o"
    c_obj = obj_dir / "src" / "foo.o"
    asm_obj = obj_dir / "asm" / "crt0.o"
    untouched = obj_dir / "src" / "nao_compilado.o"
    for obj in (data_obj, c_obj, asm_obj, untouched):
        obj.parent.mkdir(parents=True, exist_ok=True)
        obj.write_bytes(b"o")
    log = env.tmp / "build.log"
    log.write_text(
        "tools/preproc/preproc data/event_scripts.s charmap.txt | cpp -I include - | "
        "tools/preproc/preproc -ie data/event_scripts.s charmap.txt | arm-none-eabi-as "
        "-mcpu=arm7tdmi -o build/firered_switch/data/event_scripts.o\n"
        "tools/agbcc/bin/agbcc <flags> -o build/firered_switch/src/foo.o src/foo.c\n"
        "arm-none-eabi-as -mcpu=arm7tdmi -o build/firered_switch/asm/crt0.o asm/crt0.s\n"
        "{standard input}: Assembler messages:\n"
        "{standard input}:1234: Warning: value 0x1ff truncated to 0xff\n"
        f"{MARKER}\n", encoding="utf-8")
    assert env.run(FAKE_EXIT="1", BUILD_LOG=str(log), ESTEIRA_OBJ_DIR=str(obj_dir)).returncode != 0
    assert not data_obj.exists() and not c_obj.exists() and not asm_obj.exists()
    assert untouched.exists()
    assert not env.elf.exists()           # ld relinka (e reimprime o uso de memória)


def test_red_with_only_c_warnings_keeps_the_elf_and_other_objects(env):
    obj_dir = env.tmp / "build" / "firered_switch"
    other = obj_dir / "data" / "x.o"
    other.parent.mkdir(parents=True)
    other.write_bytes(b"o")
    log = env.tmp / "build.log"
    log.write_text("arm-none-eabi-as -o build/firered_switch/data/x.o data/x.s\n"
                   "tools/agbcc/bin/agbcc <flags> -o build/firered_switch/src/foo.o src/foo.c\n"
                   f"src/foo.c:10: warning: algo\n{MARKER}\n", encoding="utf-8")
    assert env.run(FAKE_EXIT="1", BUILD_LOG=str(log), ESTEIRA_OBJ_DIR=str(obj_dir)).returncode != 0
    assert other.exists() and env.elf.exists()


def test_red_without_warnings_deletes_no_objects(env):
    obj_dir = env.tmp / "build" / "firered_switch"
    obj = obj_dir / "data" / "x.o"
    obj.parent.mkdir(parents=True)
    obj.write_bytes(b"o")
    log = env.tmp / "build.log"
    log.write_text("arm-none-eabi-as -o build/firered_switch/data/x.o data/x.s\n"
                   f"{MARKER}\n[falha] abertura: Warning: citado pela esteira\n", encoding="utf-8")
    assert env.run(FAKE_EXIT="1", BUILD_LOG=str(log), ESTEIRA_OBJ_DIR=str(obj_dir)).returncode != 0
    assert obj.exists() and env.elf.exists()


@pytest.mark.parametrize("outcome", [{}, {"FAKE_EXIT": "1"}, {"FAKE_EXIT": "130"},
                                     {"SKIP_TESTS": "1"}])
def test_keeps_only_the_newest_15_runs(env, outcome):
    """test/out/ não cresce sem limite: só as pastas de execução (data-hora) entram na conta."""
    old = [f"202001{d:02d}-120000" for d in range(1, 21)]          # 20 execuções antigas
    for name in old:
        (env.out / name / "telas").mkdir(parents=True)
    others = ["fixtures", "stress-BULBASAUR-0", "pipeline-copia-77", "20200101-1200",
              "x20200101-120000"]
    for name in others:
        (env.out / name).mkdir(parents=True)
    (env.out / "20200102-120000.log").write_text("arquivo solto", encoding="utf-8")
    env.run(**outcome)
    runs = sorted(p.name for p in env.out.iterdir()
                  if p.is_dir() and len(p.name) == 15 and p.name[8] == "-")
    assert len(runs) == 15
    assert runs[:-1] == old[-14:]                    # as 14 mais novas das antigas + esta execução
    assert runs[-1] > old[-1]
    for name in others:
        assert (env.out / name).is_dir(), name
    assert (env.out / "20200102-120000.log").is_file()


# --- make test-quick / test-full (ESTEIRA_RUN do Makefile) ----------------------------------------

def _make_test_quick(tmp: Path, build_dir: Path, runs: Path) -> subprocess.CompletedProcess:
    """`make test-quick` de verdade, com o python3 trocado pelo CHECKER (só check_build sobre o
    --log recebido), o build em `build_dir` e as execuções em `runs` (nada no repo real)."""
    checker = tmp / "checker.py"
    checker.write_text(CHECKER, encoding="utf-8", newline="\n")
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "python3"
    fake.write_text(f'#!/bin/sh\nexec {sys.executable} {checker} {REPO_ROOT / "test"} "$@"\n',
                    encoding="utf-8", newline="\n")
    fake.chmod(0o755)
    environ = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    return subprocess.run(["make", "test-quick", f"BUILD_DIR={build_dir}", "ESTEIRA_RUNNER=true",
                           f"ESTEIRA_RUNS_DIR={runs}"], cwd=REPO_ROOT, env=environ,
                          capture_output=True, text=True, timeout=120)


def test_test_quick_after_interruption_has_memory_data_and_ignores_old_output(tmp_path):
    """Como test_retest_after_interruption_has_memory_data, no `make test-quick`: o log de um
    build que só rodou o objcopy (reteste depois de vermelho, SKIP_TESTS, Ctrl-C) não traz
    EWRAM/IWRAM, e depois da marca vem a saída da esteira daquela vez (`*** ... ***`)."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    runs = tmp_path / "runs"
    (build_dir / "firered_switch.log").write_text(
        "arm-none-eabi-objcopy -O binary x.elf x.gba\n"
        f"{MARKER}\n*** ROM NÃO TESTADA: o emulador não rodou ***\n"
        "src/velho.c:1: warning: de uma execução anterior\n", encoding="utf-8")

    # controle: sem memory.txt o log "só objcopy" reprova
    done = _make_test_quick(tmp_path, build_dir, runs)
    assert done.returncode != 0, done.stdout + done.stderr

    memory = build_dir / "firered_switch" / "memory.txt"
    memory.parent.mkdir(parents=True, exist_ok=True)
    memory.write_text(MEMORY, encoding="utf-8")
    done = _make_test_quick(tmp_path, build_dir, runs)
    assert done.returncode == 0, done.stdout + done.stderr
    newest = sorted(runs.iterdir())[-1]        # (as duas execuções podem cair no mesmo segundo)
    seen = (newest / "build.log").read_text(encoding="utf-8")
    assert "EWRAM:" in seen and "NÃO TESTADA" not in seen and "velho.c" not in seen


def test_build_log_script_without_log_uses_only_the_memory_file(tmp_path):
    memory = tmp_path / "memory.txt"
    dest = tmp_path / "build.log"
    script = REPO_ROOT / "test" / "build_log.sh"
    done = subprocess.run(["sh", str(script), str(tmp_path / "nao-existe.log"), str(memory),
                           str(dest)], capture_output=True, text=True)
    assert done.returncode == 1 and not dest.exists()
    assert "sem log de build" in done.stdout
    memory.write_text(MEMORY, encoding="utf-8")
    done = subprocess.run(["sh", str(script), "", str(memory), str(dest)], capture_output=True,
                          text=True)
    assert done.returncode == 0 and dest.read_text(encoding="utf-8") == MEMORY


# --- Makefile real -----------------------------------------------------------------------------

def _make_dry_run(*args: str) -> str:
    """`make -n` dos alvos da esteira (estão em RULES_NO_SCAN: não varrem dependências).
    MAKE=true: o $(MAKE) recursivo só é impresso (um `make -n` o executaria de verdade)."""
    done = subprocess.run(["make", "-n", *args, "MAKE=true"], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    return done.stdout


def test_build_log_name_only_gets_the_test_suffix_with_testbuild_1():
    """config.mk define TESTBUILD ?= 0: o log da build jogável não pode virar *_test.log."""
    build = REPO_ROOT / "build"
    assert (f"sh test/build_log.sh {build / 'firered_switch.log'} "
            f"{build / 'firered_switch' / 'memory.txt'} ") in _make_dry_run("test-quick")
    assert (f"sh test/build_log.sh {build / 'firered_switch_test.log'} "
            f"{build / 'firered_switch_test' / 'memory.txt'} ") in _make_dry_run("test-quick",
                                                                                "TESTBUILD=1")


def test_test_approve_defaults_to_the_newest_run_folder_only(tmp_path):
    """fixtures/ (cache dos testes) e restos em test/out/ não são execuções para aprovar."""
    run = tmp_path / "20261017-030544"
    run.mkdir()
    for other in ("fixtures", "stress-BULBASAUR-0"):
        (tmp_path / other).mkdir()
        os.utime(tmp_path / other, (run.stat().st_mtime + 60,) * 2)
    out = _make_dry_run("test-approve", f"ESTEIRA_RUNS_DIR={tmp_path}")
    assert f'aprovar "{run}/"' in out


def test_test_full_rebuilds_the_test_rom_before_running():
    lines = _make_dry_run("test-full").splitlines()
    assert lines[0] == "true firered_switch TESTBUILD=1"
    assert lines[1] == "true -s -C test/harness"   # runner em dia antes do emulador
    run = lines[2]
    assert "python3 -m esteira completo" in run
    assert f"--rom-test {REPO_ROOT / 'pokefirered_switch_test.gba'}" in run
    assert f"--elf-test {REPO_ROOT / 'pokefirered_switch_test.elf'}" in run


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


@pytest.mark.slow
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
