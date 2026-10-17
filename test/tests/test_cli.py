"""CLI da esteira sem emulador: cenários falsos, agrupamento por ROM, rodízio, aprovação."""

import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import esteira.__main__ as cli
from esteira.__main__ import TEST, ScenarioSpec, main
from esteira.result import Result, StepTimeout


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    """Nenhum teste pode tocar o estado de rodízio nem as referências reais."""
    monkeypatch.setattr(cli, "STATE_PATH", str(tmp_path / "estado-rodizio.json"))
    monkeypatch.setattr(cli, "REFS_DIR", str(tmp_path / "referencias"))


# --- cenários e emulador falsos --------------------------------------------------------------

class FakeEnv:
    def __init__(self, tmp_path: Path):
        self.tmp = tmp_path
        self.opened: list[tuple[str, str]] = []     # (rom, inicial) de cada open_context
        self.ran: list[str] = []                    # cenários executados, em ordem
        self.checkpoints: set[str] = set()          # checkpoints "existentes" em OUT
        self.restored: list[str] = []
        self.resets = 0
        self.party_species = 1
        for name in ("jogavel.gba", "jogavel.elf", "teste.gba", "teste.elf"):
            (tmp_path / name).write_bytes(b"x")

    def argv(self, modo="rapido", *extra: str) -> list[str]:
        t = self.tmp
        return [modo, "--rom", str(t / "jogavel.gba"), "--elf", str(t / "jogavel.elf"),
                "--rom-test", str(t / "teste.gba"), "--elf-test", str(t / "teste.elf"),
                "--out", str(t / "out"), *extra]

    def spec(self, name, rom=cli.PLAYABLE, needs=None, effect=None) -> ScenarioSpec:
        def run(ctx):
            self.ran.append(name)
            if effect:
                effect(ctx)
        return ScenarioSpec(name, run, needs=needs, rom=rom)

    def make_ctx(self, rom, starter, suite):
        env = self
        controller = SimpleNamespace(
            checkpoint_path=lambda n: SimpleNamespace(is_file=lambda: n in env.checkpoints),
            restore=lambda n: env.restored.append(n))
        return SimpleNamespace(
            suite=suite, controller=controller, starter=starter, rom=rom,
            game=SimpleNamespace(party=lambda: [SimpleNamespace(species=env.party_species)]),
            consts=SimpleNamespace(species=lambda s: 1),
            emu=SimpleNamespace(reset=lambda: setattr(env, "resets", env.resets + 1)))


@pytest.fixture
def env(tmp_path, monkeypatch):
    e = FakeEnv(tmp_path)

    @contextmanager
    def fake_open(rom, elf, out, starter, suite=None):
        e.opened.append((Path(rom).name, starter))
        yield e.make_ctx(Path(rom).name, starter, suite)

    monkeypatch.setattr(cli, "open_context", fake_open)
    monkeypatch.setattr(cli, "check_text", lambda repo, exceptions: [])
    monkeypatch.setattr(cli, "_git_commit", lambda: "abc1234")
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", [])
    monkeypatch.setattr(cli, "FULL_SCENARIOS", [])
    return e


def set_scenarios(monkeypatch, quick, full=()):
    monkeypatch.setattr(cli, "QUICK_SCENARIOS", list(quick))
    monkeypatch.setattr(cli, "FULL_SCENARIOS", list(full))


def failing(ctx):
    ctx.suite.add(Result("roteiro: algo", "falha", "deu errado"))


def html(env) -> str:
    return (env.tmp / "out" / "relatorio.html").read_text(encoding="utf-8")


# --- sem emulador ------------------------------------------------------------------------------

def test_rom_ausente_gera_relatorio_nao_testada_e_sai_1(tmp_path, capsys):
    out = tmp_path / "out"
    code = main(["rapido", "--rom", str(tmp_path / "nao-existe.gba"),
                 "--elf", str(tmp_path / "nao-existe.elf"), "--out", str(out),
                 "--starter", "SQUIRTLE"])
    assert code == 1
    page = (out / "relatorio.html").read_text(encoding="utf-8")
    assert "NÃO TESTADA" in page and "SQUIRTLE" in page
    assert "Esteira NÃO TESTADA" in page
    text = capsys.readouterr().out
    assert "NÃO TESTADA" in text and "sem --log" in text


def test_aprovar_usa_o_inicial_do_meta(tmp_path):
    run = tmp_path / "run"
    (run / "telas").mkdir(parents=True)
    Image.new("RGB", (4, 4)).save(run / "telas" / "nome.png")
    (run / "meta.json").write_text('{"inicial": "BULBASAUR"}', encoding="utf-8")
    assert main(["aprovar", str(run)]) == 0
    assert (tmp_path / "referencias" / "BULBASAUR" / "nome.png").is_file()


def test_only_desconhecido_e_erro_de_uso(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["rapido", "--rom", "x", "--elf", "y", "--out", str(tmp_path), "--only", "inexistente"])
    assert exc.value.code == 2


# --- falhas e códigos de saída -----------------------------------------------------------------

def test_excecao_no_cenario_vira_falha_e_sai_1(env, monkeypatch):
    def boom(ctx):
        raise RuntimeError("emulador caiu")
    set_scenarios(monkeypatch, [env.spec("a", effect=boom), env.spec("b")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 1
    page = html(env)
    assert "cenario/a" in page and "emulador caiu" in page
    assert env.ran == ["a"]


def test_step_timeout_guarda_evidencias(env, monkeypatch):
    shot = env.tmp / "tela.png"
    Image.new("RGB", (4, 4)).save(shot)

    def timeout(ctx):
        raise StepTimeout("a bola", str(shot), "/tmp/x.ss")
    set_scenarios(monkeypatch, [env.spec("a", effect=timeout)])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 1
    page = html(env)
    assert "/tmp/x.ss" in page
    assert (env.tmp / "out" / "img").is_dir() and any((env.tmp / "out" / "img").iterdir())


def test_so_ok_e_aviso_sai_0(env, monkeypatch):
    def warn(ctx):
        ctx.suite.add(Result("roteiro: nota", "aviso", "só um aviso"))
    set_scenarios(monkeypatch, [env.spec("a", effect=warn), env.spec("b")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 0
    assert env.ran == ["a", "b"]
    assert "Esteira aprovada" in html(env)


def test_cenario_com_falha_pula_os_seguintes_com_aviso(env, monkeypatch, capsys):
    set_scenarios(monkeypatch, [env.spec("a", effect=failing), env.spec("b"), env.spec("c")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 1
    assert env.ran == ["a"]
    out = capsys.readouterr().out
    assert "[aviso] cenario/b: não rodou" in out and "[aviso] cenario/c: não rodou" in out


def test_falha_estatica_nao_impede_os_cenarios(env, monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_text", lambda repo, exc: [Result("texto/x", "falha", "ruim")])
    set_scenarios(monkeypatch, [env.spec("a"), env.spec("b")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 1   # a falha estática reprova
    assert env.ran == ["a", "b"]
    assert "não rodou" not in capsys.readouterr().out


def test_falha_estatica_mais_falha_de_cenario_so_pula_depois_do_cenario(env, monkeypatch):
    monkeypatch.setattr(cli, "check_text", lambda repo, exc: [Result("texto/x", "falha", "ruim")])
    set_scenarios(monkeypatch, [env.spec("a"), env.spec("b", effect=failing), env.spec("c")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 1
    assert env.ran == ["a", "b"]


# --- agrupamento por ROM -----------------------------------------------------------------------

def test_cenarios_agrupados_por_rom_abrem_um_contexto_por_grupo(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a"), env.spec("c", needs="rival")],
                  [env.spec("b", rom=TEST), env.spec("d", needs="save")])
    assert main(env.argv("completo", "--starter", "CHARMANDER")) == 0
    assert env.opened == [("jogavel.gba", "CHARMANDER"), ("teste.gba", "CHARMANDER")]
    assert env.ran == ["a", "c", "d", "b"]   # grupo jogável inteiro (a, c, d), depois o de teste


def test_falha_num_grupo_nao_pula_o_outro(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a", effect=failing), env.spec("c")],
                  [env.spec("b", rom=TEST)])
    assert main(env.argv("completo", "--starter", "BULBASAUR")) == 1
    assert env.ran == ["a", "b"]   # c pulado (mesmo grupo), b roda (ROM de teste, parte do boot)


def test_rom_de_teste_ausente_e_falha_mas_o_resto_roda(env, monkeypatch):
    (env.tmp / "teste.gba").unlink()
    set_scenarios(monkeypatch, [env.spec("a")], [env.spec("b", rom=TEST)])
    assert main(env.argv("completo", "--starter", "BULBASAUR")) == 1
    assert env.ran == ["a"]
    page = html(env)
    assert "emulador/rom-test" in page and "ROM NÃO TESTADA" not in page


def test_rapido_ignora_cenarios_completos(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a")], [env.spec("b", rom=TEST)])
    assert main(env.argv("rapido", "--starter", "BULBASAUR")) == 0
    assert env.ran == ["a"] and env.opened == [("jogavel.gba", "BULBASAUR")]


# --- --only e checkpoints ----------------------------------------------------------------------

def test_only_com_checkpoint_roda_so_o_cenario(env, monkeypatch):
    env.checkpoints = {"rival"}
    set_scenarios(monkeypatch, [env.spec("a"), env.spec("b", needs="rival"), env.spec("c")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR", "--only", "b")) == 0
    assert env.ran == ["b"] and env.restored == ["rival"]


def test_only_sem_checkpoint_roda_a_cadeia_ate_ele(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a"), env.spec("b", needs="rival"), env.spec("c")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR", "--only", "b")) == 0
    assert env.ran == ["a", "b"] and env.restored == []


def test_only_com_checkpoint_de_outro_inicial_recomeca_do_boot(env, monkeypatch):
    env.checkpoints = {"rival"}
    env.party_species = 99   # o mapa falso diz que o inicial esperado é 1
    set_scenarios(monkeypatch, [env.spec("a"), env.spec("b", needs="rival")])
    assert main(env.argv("rapido", "--starter", "BULBASAUR", "--only", "b")) == 0
    assert env.ran == ["a", "b"] and env.resets == 1


def test_only_de_cenario_da_rom_de_teste_abre_so_esse_grupo(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a")], [env.spec("x", rom=TEST), env.spec("y", rom=TEST)])
    assert main(env.argv("completo", "--starter", "BULBASAUR", "--only", "y")) == 0
    assert env.opened == [("teste.gba", "BULBASAUR")]
    assert env.ran == ["x", "y"]


# --- rodízio -----------------------------------------------------------------------------------

def state_file() -> Path:
    return Path(cli.STATE_PATH)


def test_rodizio_avanca_quando_o_emulador_roda(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a")])
    main(env.argv("rapido"))
    assert json.loads(state_file().read_text())["inicial"] == "BULBASAUR"
    main(env.argv("rapido"))
    assert json.loads(state_file().read_text())["inicial"] == "CHARMANDER"
    assert [s for _, s in env.opened] == ["BULBASAUR", "CHARMANDER"]
    assert json.loads((env.tmp / "out" / "meta.json").read_text())["inicial"] == "CHARMANDER"


def test_rodizio_avanca_uma_vez_com_dois_grupos(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a")], [env.spec("b", rom=TEST)])
    main(env.argv("completo"))
    assert [s for _, s in env.opened] == ["BULBASAUR", "BULBASAUR"]
    assert json.loads(state_file().read_text())["inicial"] == "BULBASAUR"


def test_rodizio_nao_avanca_sem_emulador(env, monkeypatch):
    set_scenarios(monkeypatch, [env.spec("a")])
    (env.tmp / "jogavel.gba").unlink()
    main(env.argv("rapido"))                               # ROM ausente
    main(env.argv("rapido", "--only", "texto"))            # só checagem estática
    main(env.argv("rapido", "--starter", "SQUIRTLE"))      # inicial forçado (ROM ainda ausente)
    assert not state_file().exists()
    (env.tmp / "jogavel.gba").write_bytes(b"x")
    main(env.argv("rapido", "--starter", "SQUIRTLE"))      # roda, mas não gasta o rodízio
    assert not state_file().exists()
