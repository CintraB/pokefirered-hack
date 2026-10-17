"""Fixtures compartilhadas da esteira de testes."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SWITCH_ROM = REPO_ROOT / "pokefirered_switch.gba"


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
