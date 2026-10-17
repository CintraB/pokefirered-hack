"""Checagem do log de build: erros, avisos novos e uso de EWRAM/IWRAM."""

from esteira.check_build import check_build

OK_LOG = """\
arm-none-eabi-gcc ... -o pokefirered_switch.elf
Memory region         Used Size  Region Size  %age Used
            ROM:    16777216 B        32 MB     50.00%
           EWRAM:      261036 B       256 KB     99.58%
           IWRAM:       30096 B        32 KB     91.85%
"""


def write_log(tmp_path, text):
    path = tmp_path / "build.log"
    path.write_text(text, encoding="utf-8")
    return str(path)


def by_status(results, status):
    return [r for r in results if r.status == status]


def test_clean_log_has_no_failures(tmp_path):
    results = check_build(write_log(tmp_path, OK_LOG), {"build_warnings": []})
    assert by_status(results, "falha") == []
    assert by_status(results, "aviso") == []
    details = " ".join(r.detail for r in results)
    assert "EWRAM" in details and "IWRAM" in details  # uso reportado mesmo quando ok


def test_ewram_at_100_percent_fails(tmp_path):
    log = OK_LOG.replace("261036 B       256 KB     99.58%", "262144 B       256 KB    100.00%")
    results = check_build(write_log(tmp_path, log), {})
    failed = by_status(results, "falha")
    assert len(failed) == 1
    assert "EWRAM" in failed[0].detail and "100.00%" in failed[0].detail


def test_iwram_over_100_percent_fails(tmp_path):
    log = OK_LOG.replace("30096 B        32 KB     91.85%", "33000 B        32 KB    100.71%")
    failed = by_status(check_build(write_log(tmp_path, log), {}), "falha")
    assert len(failed) == 1 and "IWRAM" in failed[0].detail


def test_missing_memory_report_fails(tmp_path):
    failed = by_status(check_build(write_log(tmp_path, "nada de memória aqui\n"), {}), "falha")
    assert any("EWRAM" in r.detail for r in failed)
    assert any("IWRAM" in r.detail for r in failed)


def test_new_warning_fails(tmp_path):
    warn = "src/foo.c:10: warning: unused variable 'x' [-Wunused-variable]\n"
    failed = by_status(check_build(write_log(tmp_path, warn + OK_LOG), {"build_warnings": []}), "falha")
    assert len(failed) == 1
    assert "unused variable" in failed[0].detail


def test_listed_warning_is_ignored(tmp_path):
    warn = "src/foo.c:10: warning: unused variable 'x' [-Wunused-variable]\n"
    exceptions = {"build_warnings": ["src/foo.c:10: warning: unused variable 'x' [-Wunused-variable]"]}
    results = check_build(write_log(tmp_path, warn + OK_LOG), exceptions)
    assert by_status(results, "falha") == []


def test_compiler_error_fails_even_if_text_is_listed_as_warning(tmp_path):
    err = "src/foo.c:3: error: 'y' undeclared (first use in this function)\n"
    failed = by_status(check_build(write_log(tmp_path, err + OK_LOG), {"build_warnings": [err.strip()]}), "falha")
    assert len(failed) == 1 and "undeclared" in failed[0].detail


def test_linker_overflow_and_make_error_fail(tmp_path):
    log = ("ld: region `EWRAM' overflowed by 4 bytes\n"
           "make: *** [Makefile:123: pokefirered_switch.elf] Error 1\n")
    failed = by_status(check_build(write_log(tmp_path, log + OK_LOG), {}), "falha")
    assert len(failed) == 2


def test_make_stop_without_rule_fails(tmp_path):
    log = "make: *** No rule to make target 'foo.c', needed by 'foo.o'.  Stop.\n"
    assert len(by_status(check_build(write_log(tmp_path, log + OK_LOG), {}), "falha")) == 1


def test_words_in_file_names_are_not_warnings(tmp_path):
    log = "CC src/error_message.c\nCC src/warning_screen.c\n" + OK_LOG
    assert by_status(check_build(write_log(tmp_path, log), {}), "falha") == []


def test_missing_log_file_fails(tmp_path):
    failed = by_status(check_build(str(tmp_path / "nao_existe.log"), {}), "falha")
    assert len(failed) == 1 and "log" in failed[0].detail
