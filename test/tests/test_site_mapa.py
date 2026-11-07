import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("site_mapa", REPO / "tools/site/mapa.py")
mapa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mapa)


def _gerar(tmp_path, nome):
    destino = tmp_path / nome
    mapa.gerar(REPO, destino)
    return destino


def test_mapa_tamanho(tmp_path):
    assert Image.open(_gerar(tmp_path, "a.png")).size == (768, 576)


def test_mapa_deterministico(tmp_path):
    a = _gerar(tmp_path, "a.png").read_bytes()
    b = _gerar(tmp_path, "b.png").read_bytes()
    assert a == b


def test_mapa_sem_icone(tmp_path):
    img = Image.open(_gerar(tmp_path, "a.png")).convert("RGB")
    regiao = np.array(img)[456:533, 686:749].reshape(-1, 3)
    assert not (regiao == (255, 222, 49)).all(axis=1).any()
