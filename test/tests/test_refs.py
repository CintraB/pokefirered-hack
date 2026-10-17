"""Screenshots de referência: comparação pixel a pixel e aprovação dos pontos-chave."""

from pathlib import Path

from PIL import Image

from esteira.refs import KEY_POINTS, approve_refs, compare_ref

SIZE = (240, 160)


def make_png(path: Path, color=(10, 20, 30), pixel=None) -> str:
    img = Image.new("RGB", SIZE, color)
    if pixel is not None:
        img.putpixel(pixel, (200, 200, 200))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return str(path)


def test_sem_referencia_vira_aviso(tmp_path):
    shot = make_png(tmp_path / "run" / "inicial.png")
    result = compare_ref("inicial", "BULBASAUR", shot, str(tmp_path / "refs"))
    assert result.status == "aviso"
    assert "sem referência" in result.detail
    assert shot in result.images


def test_imagem_identica_vira_ok(tmp_path):
    refs = tmp_path / "refs"
    make_png(refs / "BULBASAUR" / "inicial.png")
    shot = make_png(tmp_path / "run" / "inicial.png")
    result = compare_ref("inicial", "BULBASAUR", shot, str(refs))
    assert result.status == "ok"


def test_um_pixel_diferente_vira_aviso_com_diff(tmp_path):
    refs = tmp_path / "refs"
    make_png(refs / "CHARMANDER" / "nome.png")
    shot = make_png(tmp_path / "run" / "nome.png", pixel=(7, 9))
    result = compare_ref("nome", "CHARMANDER", shot, str(refs))
    assert result.status == "aviso"
    assert "1 pixel" in result.detail
    diffs = [p for p in result.images if "diff" in Path(p).name]
    assert len(diffs) == 1 and Path(diffs[0]).is_file()
    diff = Image.open(diffs[0]).convert("RGB")
    assert diff.getpixel((7, 9)) == (255, 0, 0)
    assert diff.getpixel((0, 0)) != (255, 0, 0)


def test_tamanho_diferente_vira_aviso_sem_diff(tmp_path):
    refs = tmp_path / "refs"
    make_png(refs / "SQUIRTLE" / "captura.png")
    small = tmp_path / "run" / "captura.png"
    small.parent.mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(small)
    result = compare_ref("captura", "SQUIRTLE", str(small), str(refs))
    assert result.status == "aviso" and "tamanho" in result.detail


def test_approve_refs_copia_so_pontos_chave(tmp_path):
    run = tmp_path / "run"
    for name in (*KEY_POINTS, "fala_oak", "rota1_golpe"):
        make_png(run / "telas" / f"{name}.png")
    (run / "meta.json").write_text('{"inicial": "SQUIRTLE"}', encoding="utf-8")
    refs = tmp_path / "refs"
    copied = approve_refs(str(run), refs_dir=str(refs))
    assert sorted(Path(p).name for p in copied) == sorted(f"{k}.png" for k in KEY_POINTS)
    assert sorted(p.name for p in (refs / "SQUIRTLE").iterdir()) == sorted(f"{k}.png" for k in KEY_POINTS)


def test_approve_refs_sem_inicial_conhecido_falha(tmp_path):
    run = tmp_path / "run"
    make_png(run / "telas" / "nome.png")
    try:
        approve_refs(str(run), refs_dir=str(tmp_path / "refs"))
    except ValueError as exc:
        assert "inicial" in str(exc)
    else:
        raise AssertionError("deveria exigir o inicial")
