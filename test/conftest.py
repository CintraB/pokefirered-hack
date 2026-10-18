"""Fixtures compartilhadas da esteira de testes."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SWITCH_ROM = REPO_ROOT / "pokefirered_switch.gba"


def pytest_xdist_auto_num_workers(config) -> int:
    """`-n auto` (test/pytest.ini): tantos workers quanto o teto ESTEIRA_JOBS (padrão 10), para
    o PC continuar usável; `-n 0` roda tudo num processo só."""
    from esteira.paralelo import jobs
    return jobs()


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers", "slow: compila de verdade (minutos); ESTEIRA_SKIP_SLOW=1 pula")


@pytest.fixture
def rom_path() -> str:
    """Caminho absoluto da ROM Switch; pula o teste se ela não foi compilada."""
    if not SWITCH_ROM.is_file():
        pytest.skip(f"ROM não encontrada: {SWITCH_ROM} (rode `make firered_switch`)")
    return str(SWITCH_ROM)


@pytest.fixture
def tmp_save(tmp_path: Path) -> str:
    """Caminho de um .sav descartável (ainda inexistente) dentro do tmp do teste."""
    return str(tmp_path / "esteira.sav")
