"""Relatório HTML autocontido."""

from pathlib import Path

from PIL import Image

from esteira.report import write_report
from esteira.result import Result, Suite

META = {"inicial": "BULBASAUR", "data": "2026-10-17 10:00", "commit": "abc1234",
        "tempo_total": 123.4, "nao_testada": False}


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_falha_aparece_com_nome_e_detalhe(tmp_path):
    suite = Suite()
    suite.add(Result("rota1: andar", "ok", "11 quadros/tile"))
    suite.add(Result("captura: bola", "falha", "tempo esgotado <esperando> a bola"))
    out = tmp_path / "out"
    path = write_report(suite, str(out), dict(META))
    html = read(path)
    assert Path(path) == out / "relatorio.html"
    assert "captura: bola" in html
    assert "tempo esgotado &lt;esperando&gt; a bola" in html   # escapado
    assert "BULBASAUR" in html and "abc1234" in html
    assert "NÃO TESTADA" not in html


def test_nao_testada_mostra_faixa(tmp_path):
    meta = dict(META, nao_testada=True)
    html = read(write_report(Suite(), str(tmp_path), meta))
    assert "NÃO TESTADA" in html
    assert html.index("NÃO TESTADA") < html.index("BULBASAUR")


def test_imagens_sao_copiadas_para_img(tmp_path):
    shot = tmp_path / "run" / "a.png"
    shot.parent.mkdir()
    Image.new("RGB", (4, 4), (1, 2, 3)).save(shot)
    other = tmp_path / "run2" / "a.png"      # mesmo nome em outra pasta
    other.parent.mkdir()
    Image.new("RGB", (4, 4), (9, 9, 9)).save(other)
    suite = Suite()
    suite.add(Result("um", "aviso", "x", [str(shot)]))
    suite.add(Result("dois", "ok", "y", [str(other)]))
    out = tmp_path / "out"
    html = read(write_report(suite, str(out), dict(META)))
    copies = sorted((out / "img").iterdir())
    assert len(copies) == 2
    for c in copies:
        assert f"img/{c.name}" in html
    assert str(shot) not in html


def test_estado_salvo_e_tempos_aparecem(tmp_path):
    suite = Suite()
    suite.add(Result("x", "falha", "d", state="/tmp/estados/x.ss"))
    meta = dict(META, tempos={"abertura": 61.0, "rota1": 20.5})
    html = read(write_report(suite, str(tmp_path), meta))
    assert "/tmp/estados/x.ss" in html
    assert "abertura" in html and "61.0" in html


def test_falhas_vem_antes_de_ok(tmp_path):
    suite = Suite()
    suite.add(Result("tudo-certo", "ok", ""))
    suite.add(Result("deu-ruim", "falha", "motivo"))
    html = read(write_report(suite, str(tmp_path), dict(META)))
    assert html.index("deu-ruim") < html.index("tudo-certo")


def test_relatorio_novo_limpa_imagens_antigas(tmp_path):
    old = tmp_path / "img" / "velha.png"
    old.parent.mkdir()
    old.write_bytes(b"x")
    write_report(Suite(), str(tmp_path), dict(META))
    assert not old.exists()
