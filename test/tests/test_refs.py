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


def test_referencia_corrompida_vira_aviso(tmp_path):
    """PNG quebrado (disco, cópia interrompida) não pode derrubar a esteira: é aviso."""
    refs = tmp_path / "refs"
    shot = make_png(tmp_path / "run" / "nome.png")
    bad = refs / "SQUIRTLE" / "nome.png"
    bad.parent.mkdir(parents=True)
    for content in (b"isto nao e um png", b"\x89PNG\r\n\x1a\n" + b"\0" * 40):
        bad.write_bytes(content)
        result = compare_ref("nome", "SQUIRTLE", shot, str(refs))
        assert result.status == "aviso", content
        assert "referência ilegível" in result.detail
        assert shot in result.images


def test_png_truncado_vira_aviso(tmp_path):
    refs = tmp_path / "refs"
    good = Path(make_png(refs / "SQUIRTLE" / "nome.png"))
    data = good.read_bytes()
    good.write_bytes(data[:len(data) // 2])                  # cabeçalho bom, dados cortados
    shot = make_png(tmp_path / "run" / "nome.png")
    result = compare_ref("nome", "SQUIRTLE", shot, str(refs))
    assert result.status == "aviso" and "referência ilegível" in result.detail


def test_tela_corrompida_vira_aviso(tmp_path):
    refs = tmp_path / "refs"
    make_png(refs / "SQUIRTLE" / "nome.png")
    shot = tmp_path / "run" / "nome.png"
    shot.parent.mkdir(parents=True)
    shot.write_bytes(b"lixo")
    result = compare_ref("nome", "SQUIRTLE", str(shot), str(refs))
    assert result.status == "aviso" and "ilegível" in result.detail


def test_approve_refs_poe_as_telas_comuns_em_COMUM(tmp_path):
    from esteira.refs import SHARED_POINTS, SHARED_REFS
    run = tmp_path / "run"
    make_png(run / "telas" / "nome.png")
    make_png(run / "telas" / f"{SHARED_POINTS[0]}.png")
    (run / "meta.json").write_text('{"inicial": "BULBASAUR"}', encoding="utf-8")
    refs = tmp_path / "refs"
    copied = approve_refs(str(run), refs_dir=str(refs))
    assert sorted(Path(p).relative_to(refs).as_posix() for p in copied) == sorted(
        ["BULBASAUR/nome.png", f"{SHARED_REFS}/{SHARED_POINTS[0]}.png"])
    assert not (refs / "BULBASAUR" / f"{SHARED_POINTS[0]}.png").exists()
