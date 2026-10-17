"""CLI da esteira sem emulador: rodízio, ROM ausente, aprovação."""

import json

from PIL import Image

from esteira.__main__ import main


def test_rom_ausente_gera_relatorio_nao_testada_e_sai_1(tmp_path, capsys):
    out = tmp_path / "out"
    code = main(["rapido", "--rom", str(tmp_path / "nao-existe.gba"),
                 "--elf", str(tmp_path / "nao-existe.elf"), "--out", str(out),
                 "--starter", "SQUIRTLE", "--state", str(tmp_path / "estado.json")])
    assert code == 1
    html = (out / "relatorio.html").read_text(encoding="utf-8")
    assert "NÃO TESTADA" in html and "SQUIRTLE" in html
    text = capsys.readouterr().out
    assert "NÃO TESTADA" in text and "sem --log" in text
    assert not (tmp_path / "estado.json").exists()   # --starter explícito não gasta o rodízio


def test_rodizio_avanca_o_estado(tmp_path):
    state = tmp_path / "estado.json"
    main(["rapido", "--rom", "x", "--elf", "y", "--out", str(tmp_path / "o1"), "--state", str(state)])
    assert json.loads(state.read_text())["inicial"] == "BULBASAUR"
    main(["rapido", "--rom", "x", "--elf", "y", "--out", str(tmp_path / "o2"), "--state", str(state)])
    assert json.loads(state.read_text())["inicial"] == "CHARMANDER"
    meta = json.loads((tmp_path / "o2" / "meta.json").read_text())
    assert meta["inicial"] == "CHARMANDER"


def test_aprovar_usa_o_inicial_do_meta(tmp_path, monkeypatch):
    run = tmp_path / "run"
    (run / "telas").mkdir(parents=True)
    Image.new("RGB", (4, 4)).save(run / "telas" / "nome.png")
    (run / "meta.json").write_text('{"inicial": "BULBASAUR"}', encoding="utf-8")
    refs = tmp_path / "refs"
    monkeypatch.setattr("esteira.__main__.REFS_DIR", str(refs))
    assert main(["aprovar", str(run)]) == 0
    assert (refs / "BULBASAUR" / "nome.png").is_file()


def test_only_desconhecido_e_erro_de_uso(tmp_path):
    try:
        main(["rapido", "--rom", "x", "--elf", "y", "--out", str(tmp_path), "--only", "inexistente"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("--only inválido deveria sair com erro de uso")
