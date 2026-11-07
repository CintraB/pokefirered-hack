"""Revanches por degrau (POK-42), Task 3: Elite 4 e Campeão com times à mão por degrau.

Os times ficam em `tools/revanches/liga.json` (aprovados pelo Cintra); `tools/revanches/gerar.py` os grava em
`sLeagueTierParties`, no fim de `src/data/rematch_tiers.h`. Com degrau ≥ 1, `RematchTier_CreateParty` troca o
time dos ids `_2`/REMATCH da Liga; as 5 salas escolhem a batalha pelo special `ShouldUseLeagueRematchTeams`.
Aqui tudo é estático (o C e os scripts lidos como texto); o comportamento no jogo fica no cenário (Task 6).
"""

import importlib.util
import re
import subprocess
import sys

import pytest

from esteira.scenarios import REPO_ROOT

GERAR = REPO_ROOT / "tools" / "revanches" / "gerar.py"
HEADER = REPO_ROOT / "src" / "data" / "rematch_tiers.h"
SRC = REPO_ROOT / "src"
BASE_SHA = "e5ffdd965"  # antes do Task 3 (as intros das salas não podem mudar)

MEMBROS = ("LORELEI", "BRUNO", "AGATHA", "LANCE")
VARIANTES = ("SQUIRTLE", "BULBASAUR", "CHARMANDER")
TEMA = {"LORELEI": {"TYPE_ICE", "TYPE_WATER"}, "BRUNO": {"TYPE_FIGHTING", "TYPE_ROCK", "TYPE_GROUND"},
        "AGATHA": {"TYPE_GHOST", "TYPE_POISON"}, "LANCE": {"TYPE_DRAGON", "TYPE_FLYING"}}
INICIAL_FINAL = {"SQUIRTLE": "SPECIES_BLASTOISE", "BULBASAUR": "SPECIES_VENUSAUR", "CHARMANDER": "SPECIES_CHARIZARD"}
SALAS = ("Loreleis", "Brunos", "Agathas", "Lances", "Champions")
ENTRADA = re.compile(r"\{\.iv = (\d+), \.lvl = (\d+), \.species = (SPECIES_\w+), \.heldItem = (ITEM_\w+), "
                     r"\.moves = \{(MOVE_\w+), (MOVE_\w+), (MOVE_\w+), (MOVE_\w+)\}\}")


@pytest.fixture(scope="module")
def g():
    spec = importlib.util.spec_from_file_location("revanches_gerar_t3", GERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _times(g):
    """((rótulo, perfil, degrau), time) de todos os times da Liga."""
    for (rotulo, membro, d, _), time in g.times_liga():
        yield (rotulo, "campeao" if membro == "CAMPEAO" else "elite", d), time


def test_liga_completa(g):
    bruto = g.liga()
    for m in MEMBROS:
        assert sorted(bruto[m]) == ["1", "2", "3", "4", "5"]
        assert all(len(bruto[m][d]) == 6 for d in bruto[m])
    assert sorted(bruto["CAMPEAO"]) == ["1", "2", "3", "4", "5"]
    for d, bloco in bruto["CAMPEAO"].items():
        assert sorted(bloco) == sorted(("base",) + VARIANTES)
        assert len(bloco["base"]) == 4 and all(len(bloco[v]) == 2 for v in VARIANTES)
    times = list(_times(g))
    assert len(times) == 7 * 5
    for (rotulo, perfil, d), time in times:
        assert [n for _, n, _, _ in time] == g.niveis(d, perfil), (rotulo, d)

    # o header bate com liga.json: 7 linhas (ids 735–741) × 5 degraus × 6, IV 31 (= 255 na escala do TrainerMon)
    r = subprocess.run([sys.executable, "-I", str(GERAR), "--conferir"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    texto = _ler(HEADER)
    assert ("static const struct TrainerMonItemCustomMoves "
            "sLeagueTierParties[7][REMATCH_TIER_COUNT][PARTY_SIZE] =") in texto
    liga = texto[texto.index("sLeagueTierParties"):]
    entradas = ENTRADA.findall(liga)
    esperado = [("255", str(n), e, it, *gs) for _, time in times for e, n, it, gs in time]
    assert entradas == esperado
    rotulos = re.findall(r"^    // (TRAINER_\w+)$", liga, re.M)
    assert rotulos == [f"TRAINER_ELITE_FOUR_{m}_2" for m in MEMBROS] + \
        [f"TRAINER_CHAMPION_REMATCH_{v}" for v in VARIANTES]


def test_tema_da_liga(g):
    for (rotulo, _, d), time in _times(g):
        if rotulo.startswith("CAMPEAO"):
            continue
        for esp, _, _, _ in time:
            assert set(g.especies()[esp]["tipos"]) & TEMA[rotulo], (rotulo, d, esp)


def test_inicial_do_rival(g):
    for v in VARIANTES:
        for d in g.DEGRAUS:
            time = g.time_liga("CAMPEAO", d, v)
            assert time[5][0] == INICIAL_FINAL[v], (v, d)
            assert time[:4] == g.time_liga("CAMPEAO", d, VARIANTES[0])[:4]  # a base é a mesma


def test_degrau_5_troca_uma_especie(g):
    """Decisão do Cintra: o degrau 5 tem uma troca a mais que o 4 em cada membro; o ás fica."""
    for rotulo, v in [(m, None) for m in MEMBROS] + [("CAMPEAO", "SQUIRTLE")]:
        d4 = [e for e, _, _, _ in g.time_liga(rotulo, 4, v)]
        d5 = [e for e, _, _, _ in g.time_liga(rotulo, 5, v)]
        assert len(set(d5) - set(d4)) == 1, (rotulo, d4, d5)
        assert d4[5] == d5[5]


def test_golpes_aprendiveis(g):
    # o checador não é vazio: recusa o que a espécie não aprende e respeita o nível
    assert not g.golpe_aprendivel("SPECIES_GENGAR", "MOVE_SURF", 100)
    assert not g.golpe_aprendivel("SPECIES_VENUSAUR", "MOVE_HYDRO_CANNON", 100)
    assert not g.golpe_aprendivel("SPECIES_LAPRAS", "MOVE_SHEER_COLD", 54)  # só por nível (55)
    assert g.golpe_aprendivel("SPECIES_LAPRAS", "MOVE_SHEER_COLD", 55)
    assert g.golpe_aprendivel("SPECIES_HITMONLEE", "MOVE_MACH_PUNCH", 20)  # ovo do Tyrogue (pré-evolução)
    assert g.golpe_aprendivel("SPECIES_BLASTOISE", "MOVE_HYDRO_CANNON", 50)
    for (rotulo, _, d), time in _times(g):
        for esp, nivel, _, golpes in time:
            assert len(golpes) == 4 and len(set(golpes)) == 4 and "MOVE_NONE" not in golpes, (rotulo, d, esp)
            for golpe in golpes:
                assert golpe in g.golpes_do_jogo(), (rotulo, d, esp, golpe)
                assert g.golpe_aprendivel(esp, golpe, nivel), (rotulo, d, esp, nivel, golpe)
    assert g.problemas_liga() == []


def test_golpes_do_jogo_so_golpes(g):
    """Só os golpes de verdade de moves.h: ficam de fora MOVE_UNAVAILABLE (0xFFFF) e MOVES_COUNT."""
    golpes = g.golpes_do_jogo()
    assert "MOVE_UNAVAILABLE" not in golpes and "MOVES_COUNT" not in golpes
    assert golpes["MOVE_NONE"] == 0
    total = re.search(r"^#define MOVES_COUNT\s+(\d+)", _ler(REPO_ROOT / "include" / "constants" / "moves.h"), re.M)
    assert total and max(golpes.values()) == int(total.group(1)) - 1
    assert "MOVES_COUNT" not in g.golpes_do_jogo.__doc__


def test_header_recusa_liga_quebrada(g, monkeypatch, tmp_path):
    """Com liga.json fora da regra, o gerador para antes de montar o header: nem grava nem confere um header ruim."""
    problema = "CAMPEAO_SQUIRTLE degrau 5 pos. 1 (Alakazam nv 99): não aprende MOVE_SURF"
    monkeypatch.setattr(g, "problemas_liga", lambda: [problema])
    with pytest.raises(SystemExit, match="não aprende MOVE_SURF"):
        g.header()
    destino = tmp_path / "rematch_tiers.h"
    monkeypatch.setattr(g, "HEADER", destino)
    monkeypatch.setattr(sys, "argv", ["gerar.py"])
    with pytest.raises(SystemExit, match="liga.json"):
        g.main()
    assert not destino.exists()


def test_itens_da_liga(g):
    """Todos têm item em todos os degraus; nos degraus 1–2 quem não é o ás leva a fruta do Vs. Seeker."""
    for (rotulo, _, d), time in _times(g):
        membro = "CAMPEAO" if rotulo.startswith("CAMPEAO") else rotulo
        for pos, (esp, _, it, _) in enumerate(time):
            assert it != "ITEM_NONE", (rotulo, d, pos, esp)
            assert it in g.itens_do_jogo(), (rotulo, d, pos, it)
            if d <= 2 and pos < 5:
                assert it == g.item_fruta_liga(membro, d, pos), (rotulo, d, pos, it)
    # degrau 1: o rodízio das 6 frutas de status aparece na Liga
    frutas = {it for (_, _, d), time in _times(g) if d == 1 for _, _, it, _ in time[:5]}
    assert frutas == set(g.regras()["itens"]["por_degrau"]["1"]["time"])


def test_liga_no_c():
    h = _ler(REPO_ROOT / "include" / "rematch_tier.h")
    assert "bool8 ShouldUseLeagueRematchTeams(void);" in h
    fonte = _ler(SRC / "rematch_tier.c")
    especial = _corpo(fonte, "ShouldUseLeagueRematchTeams")
    assert re.search(r"return FlagGet\(FLAG_SYS_CAN_LINK_WITH_RS\) \|\| GetRematchTier\(\) >= 1;", especial)
    criar = _corpo(fonte, "RematchTier_CreateParty")
    assert re.search(r"trainerNum >= TRAINER_ELITE_FOUR_LORELEI_2 && trainerNum <= TRAINER_CHAMPION_REMATCH_CHARMANDER",
                     criar)
    assert "sLeagueTierParties[trainerNum - TRAINER_ELITE_FOUR_LORELEI_2][tier - 1]" in criar
    assert "MON_DATA_MOVE1 + j" in criar and "MON_DATA_PP1 + j" in criar and "gBattleMoves[" in criar
    assert "MON_DATA_HELD_ITEM" in criar
    assert re.search(r"STATIC_ASSERT\(NELEMS\(sLeagueTierParties\) == "
                     r"TRAINER_CHAMPION_REMATCH_CHARMANDER - TRAINER_ELITE_FOUR_LORELEI_2 \+ 1", fonte)
    specials = _ler(REPO_ROOT / "data" / "specials.inc")
    fim = [l for l in specials[:specials.index("gSpecialsEnd::")].rstrip().splitlines()
           if "FamiliaSombra_" not in l and "MestreGolpes_" not in l and "KrabbySize" not in l and "SalaTrofeus_" not in l and "POK-51" not in l
           and "Dossie_" not in l]  # POK-51 e POK-54 vêm depois
    # os da Task 4 (BufferRematchTierName) e da onda final (ShowRematchTierMenu) vêm logo depois
    assert [l.strip() for l in fim[-3:]] == ["def_special ShouldUseLeagueRematchTeams", "def_special BufferRematchTierName",
                                           "def_special ShowRematchTierMenu"]


@pytest.mark.parametrize("sala", SALAS)
def test_sala_escolhe_uma_batalha(sala):
    rel = f"data/maps/PokemonLeague_{sala}Room/scripts.inc"
    texto = _ler(REPO_ROOT / rel)
    p = f"PokemonLeague_{sala}Room_EventScript"
    assert not re.search(rf"call_if_(?:un)?set FLAG_SYS_CAN_LINK_WITH_RS, {p}_(?:Battle|Rematch)\b", texto)
    assert len(re.findall(rf"^\tcall {p}_ChooseBattle$", texto, re.M)) == 1
    assert f"{p}_ChooseBattle::\n" \
           f"\tspecialvar VAR_RESULT, ShouldUseLeagueRematchTeams\n" \
           f"\tgoto_if_eq VAR_RESULT, TRUE, {p}_Rematch\n" \
           f"\tgoto {p}_Battle\n" in texto
    for rotulo in ("Battle", "Rematch"):
        bloco = re.search(rf"^{p}_{rotulo}::\n(.*?)\n\n", texto + "\n\n", re.S | re.M).group(1)
        assert bloco.rstrip().endswith("\treturn"), (sala, rotulo)
        if sala == "Champions":
            assert bloco.count("call_if_eq VAR_STARTER_MON") == 3
    # as intros não mudam
    antes = subprocess.run(["git", "show", f"{BASE_SHA}:{rel}"], cwd=REPO_ROOT, capture_output=True, text=True,
                           encoding="utf-8").stdout
    intro = re.compile(rf"^.*{p}_(?:Rematch)?Intro\b.*$", re.M)
    assert intro.findall(texto) == intro.findall(antes)
