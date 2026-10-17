"""open_context: o .sav da sessão (OUT/esteira.sav) e a cópia de `save_from`, sem emulador."""

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

import esteira.scenarios as scenarios


@pytest.fixture
def booted(monkeypatch):
    """Troca o emulador e as tabelas do jogo por falsos; guarda o .sav visto ao ligar."""
    seen: list[bytes | None] = []

    @contextmanager
    def fake_emulator(rom, save):
        seen.append(Path(save).read_bytes() if Path(save).exists() else None)
        yield SimpleNamespace()

    monkeypatch.setattr(scenarios, "Emulator", fake_emulator)
    monkeypatch.setattr(scenarios.Constants, "load", staticmethod(lambda root: None))
    monkeypatch.setattr(scenarios.Charmap, "load", staticmethod(lambda root: None))
    monkeypatch.setattr(scenarios.Symbols, "from_elf", staticmethod(lambda elf: None))
    monkeypatch.setattr(scenarios, "Game", lambda *a: None)
    monkeypatch.setattr(scenarios, "Controller", lambda *a: None)
    monkeypatch.setattr(scenarios, "Navigator", lambda *a: None)
    return seen


def boot(out: Path, save_from=None) -> None:
    with scenarios.open_context("r.gba", "r.elf", str(out), "BULBASAUR", save_from=save_from):
        pass


def test_sem_save_from_comeca_com_sav_novo(tmp_path, booted):
    (tmp_path / "esteira.sav").write_bytes(b"velho")
    boot(tmp_path)
    assert booted == [None]


def test_save_from_copia_o_arquivo(tmp_path, booted):
    (tmp_path / "esteira.sav").write_bytes(b"velho")
    (tmp_path / "rapido.sav").write_bytes(b"do modo rapido")
    boot(tmp_path, save_from=str(tmp_path / "rapido.sav"))
    assert booted == [b"do modo rapido"]
    assert (tmp_path / "rapido.sav").read_bytes() == b"do modo rapido"


def test_save_from_igual_ao_sav_da_pasta_nao_apaga_antes_de_copiar(tmp_path, booted):
    (tmp_path / "esteira.sav").write_bytes(b"o mesmo")
    boot(tmp_path, save_from=str(tmp_path / "." / "esteira.sav"))
    assert booted == [b"o mesmo"]


def test_save_from_ausente_falha_sem_apagar_o_sav(tmp_path, booted):
    (tmp_path / "esteira.sav").write_bytes(b"velho")
    with pytest.raises(FileNotFoundError):
        boot(tmp_path, save_from=str(tmp_path / "nao-existe.sav"))
    assert booted == [] and (tmp_path / "esteira.sav").read_bytes() == b"velho"
