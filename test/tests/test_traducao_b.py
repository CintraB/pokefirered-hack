"""Frente B da tradução: diálogos dos mapas (`data/maps/*/text.inc`), por grupo.

Para cada arquivo já traduzido: nenhuma palavra inglesa sobrando (`esteira.check_text.english_report`),
nenhum achado das regras `controle`, `glossario`, `largura`, `linhas` e `letras`, e os rótulos
continuam os da base inglesa (traduzir não renomeia nem apaga texto). Cada task da frente
acrescenta o seu grupo em `GROUPS`.
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]

GROUPS = {
    "B1": [f"data/maps/{m}/text.inc" for m in (
        "PalletTown_RivalsHouse", "PewterCity", "PewterCity_Gym", "PewterCity_House1", "PewterCity_House2",
        "PewterCity_Mart", "PewterCity_Museum_1F", "PewterCity_Museum_2F", "PewterCity_PokemonCenter_1F",
        "PokemonLeague_AgathasRoom", "PokemonLeague_BrunosRoom", "PokemonLeague_ChampionsRoom",
        "PokemonLeague_HallOfFame", "PokemonLeague_LancesRoom", "PokemonLeague_LoreleisRoom",
        "PokemonMansion_1F", "PokemonMansion_2F", "PokemonMansion_3F", "PokemonMansion_B1F",
        "PokemonTower_1F", "PokemonTower_2F", "PokemonTower_3F", "PokemonTower_4F", "PokemonTower_5F",
        "PokemonTower_6F", "PokemonTower_7F", "RockTunnel_1F", "RockTunnel_B1F", "RocketHideout_B1F",
        "RocketHideout_B2F", "RocketHideout_B3F", "RocketHideout_B4F", "RocketHideout_Elevator",
        "Route1", "Route10")],
    "B2": [f"data/maps/{m}/text.inc" for m in (
        "Route10_PokemonCenter_1F", "Route11", "Route11_EastEntrance_1F", "Route11_EastEntrance_2F", "Route12",
        "Route12_FishingHouse", "Route12_NorthEntrance_1F", "Route12_NorthEntrance_2F", "Route13", "Route14",
        "Route15", "Route15_WestEntrance_1F", "Route15_WestEntrance_2F", "Route16", "Route16_House",
        "Route16_NorthEntrance_1F", "Route16_NorthEntrance_2F", "Route17", "Route18", "Route18_EastEntrance_1F",
        "Route18_EastEntrance_2F", "Route19", "Route2", "Route20", "Route21_North", "Route21_South")],
}
FILES = sorted(f for files in GROUPS.values() for f in files)
RULES = ("controle", "glossario", "largura", "linhas", "letras")

_LABEL = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)::", re.M)


@lru_cache(maxsize=None)
def _results():
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    return ct.check_text(str(REPO_ROOT), exceptions, english="desligado")


@lru_cache(maxsize=None)
def _english():
    return ct.english_report(str(REPO_ROOT))


@pytest.mark.parametrize("rel", FILES)
def test_nenhum_ingles_sobrando(rel):
    assert rel not in _english(), _english().get(rel)


@pytest.mark.parametrize("rel", FILES)
def test_sem_achados_das_regras(rel):
    found = [r.detail for r in _results()
             if r.status == "falha" and r.name in {f"texto/{rule}" for rule in RULES}
             and r.detail.startswith(f"{rel}:")]
    assert found == []


@pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git")
@pytest.mark.parametrize("rel", FILES)
def test_rotulos_iguais_aos_da_base(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    base = _LABEL.findall(out.stdout.decode("utf-8"))
    current = _LABEL.findall((REPO_ROOT / rel).read_text(encoding="utf-8"))
    assert current == base


def test_termos_criados_pela_frente_b_no_glossario():
    terms = {t["en"]: t for t in json.loads(
        (REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))["termos"]
             if t.get("frente") == "B"}
    assert terms["RUNNING SHOES"]["completo"] == "Tênis de Corrida"
    assert all(t["fonte"] == "criado" for t in terms.values())


def test_base_inglesa_disponivel():
    """Sem a base inglesa as regras `controle` e `glossario` não rodam: o teste não pode passar calado."""
    missing = [r.detail for r in _results() if "base inglesa indispon" in r.detail]
    assert missing == []


_VARIABLE = re.compile(r"\{(?:STR_VAR_\d|B_BUFF\d|B_COPY_VAR_\d)\}")


@pytest.mark.parametrize("rel", FILES)
def test_linhas_com_placeholder_cabem_com_10_letras_largas(rel):
    """A esteira mede {STR_VAR_n} como 0 px: aqui o placeholder vira 10 'M' (nome de espécie no pior caso)."""
    env = ct._load_env(REPO_ROOT)
    too_wide = []
    for entry in ct._extract(rel, "inc", (REPO_ROOT / rel).read_text(encoding="utf-8")):
        if not isinstance(entry, ct._Entry):
            continue
        rule = ct.rule_for(entry.file, entry.label)
        for variant in entry.texts:                     # todas as variantes de #ifdef
            if not _VARIABLE.search(variant):
                continue
            measured = ct.measure(_VARIABLE.sub("MMMMMMMMMM", variant), env, rule.font)
            if rule.px is not None and measured.widest > rule.px:
                too_wide.append(f"{entry.label}: {measured.widest} px > {rule.px}")
    assert too_wide == []


# Regra de 20/10: nomes e termos do glossário não são partidos na quebra de linha (\n, \l, \p)
EXTRA_NAMES = ("Equipe Rocket", "Liga Pokémon", "Campeão da Liga Pokémon", "Hall da Fama Pokémon", "Ginásios Pokémon",
               "Tênis de Corrida", "Mapa da Cidade", "Arremesso Sísmico", "Tumba de Rochas", "Devorador de Sonhos",
               "Chave do Elevador", "Pedra Lunar", "Casa Pokémon", "Laboratório Pokémon", "Âmbar Antigo",
               "Visor Silph", "Monte Lua", "Torre Pokémon", "Túnel de Pedra", "Usina Elétrica", "Elite Quatro",
               # B2
               "Mestre da Pesca", "Ponte do Silêncio", "Área de Pesca Esportiva", "Compartilhador de Exp.",
               "Detector de Itens", "Moeda Amuleto", "Poké Flauta", "Cidade Vermilion", "Ilhas Seafoam", "Ilha Cinnabar",
               "Mansão Pokémon", "Loja de Celadon", "Líderes de Ginásio", "Pokémon-pássaro", "Caverna do Diglett",
               "Pedra Eterna", "Prof. Carvalho", "Dicas de Treinador", "Poké Bolas")


def _flat(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    return "".join(re.findall(r'\.string "(.*)"', text))


def _multiword_terms():
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    names = {t["pt"] for t in data["termos"] if " " in t["pt"]} | set(EXTRA_NAMES)
    plurals = set()
    for name in names:
        words = name.split(" ")
        for j, w in enumerate(words):
            if w[-1:].isalpha() and not w.endswith("s"):
                plurals.add(" ".join(words[:j] + [w + "s"] + words[j + 1:]))
    return sorted(names | plurals)


TERMS = _multiword_terms()


@pytest.mark.parametrize("rel", FILES)
def test_nomes_nao_sao_partidos_na_quebra(rel):
    body = _flat(rel)
    found = []
    for name in TERMS:
        for i, ch in enumerate(name):
            if ch == " ":
                for br in (chr(92) + c for c in "nlp"):
                    if name[:i] + br + name[i + 1:] in body:
                        found.append(name)
    assert found == [], rel


@pytest.mark.parametrize("rel", FILES)
def test_fim_de_arquivo_igual_ao_da_base(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    base = out.stdout.decode("utf-8")
    now = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert len(now) - len(now.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


# ---- B2: gênero do jogador, unidades, termos exatos --------------------------------------------
B2_FILES = GROUPS["B2"]
PLAYER_GENDERED = ("Fique quieto", "muito bruto", "parceiro,", "ocupado demais", "Aspirante a campeão",
                   "Seja bem-vindo", "Bem-vindo", "você é bom", "ganancioso", "Esteja pronto", "Fique pronto",
                   "jovem amigo", "meu amigo", "Satisfeito?", "querido.", "Você é perfeito", "Você é fofo")
WRONG_FORMS = ("inches", "polegadas", "Equipe Rocket Manda", "Detector Item", "Rota Marítima", "Gym", "GYM",
               "Guru da Pesca", "Pokemon", "POKéMON")


@pytest.mark.parametrize("rel", B2_FILES)
def test_b2_jogador_sem_genero_e_formas_erradas(rel):
    body = _flat(rel)
    for bad in PLAYER_GENDERED + WRONG_FORMS:
        assert bad not in body, (rel, bad)


def test_b2_tamanho_do_magikarp_em_centimetros():
    """O tamanho vem de FormatMonSizeRecord (cm com vírgula decimal; "inches" só no ramo UNITS_IMPERIAL):
    o texto traduzido nunca fala de polegadas."""
    body = _flat("data/maps/Route12_FishingHouse/text.inc")
    assert "{STR_VAR_2} cm" in body and "{STR_VAR_3} cm" in body
    assert "inch" not in body


def test_b2_termos_criados_no_glossario():
    terms = {t["en"]: t["pt"] for t in json.loads(
        (REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))["termos"]
             if t.get("frente") == "B"}
    assert terms["FISHING GURU"] == "Mestre da Pesca"
    assert terms["SILENCE BRIDGE"] == "Ponte do Silêncio"
    assert terms["EXP. SHARE (forma cheia)"] == "Compartilhador de Exp."
    body = _flat("data/maps/Route12_FishingHouse/text.inc") + _flat("data/maps/Route12/text.inc")         + _flat("data/maps/Route13/text.inc") + _flat("data/maps/Route15_WestEntrance_2F/text.inc")
    for pt in ("Mestre da Pesca", "Ponte do Silêncio", "Área de Pesca Esportiva", "Compartilhador de Exp."):
        assert pt in body, pt


def test_b2_assistentes_do_carvalho_falam_igual():
    """As 4 falas de recompensa dos assistentes usam a mesma redação (e só a primeira de cada par muda o item)."""
    for rel in ("data/maps/Route10_PokemonCenter_1F/text.inc", "data/maps/Route11_EastEntrance_2F/text.inc",
                "data/maps/Route15_WestEntrance_2F/text.inc", "data/maps/Route16_NorthEntrance_2F/text.inc"):
        body = _flat(rel)
        assert "assistentes do Prof. Carvalho" in body or "Sou um dos assistentes" in body, rel
        assert "me diga uma coisa" in body and "Aqui está!" in body, rel
        assert "do assistente." in body, rel
