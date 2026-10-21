"""Frente C da tradução: diálogos dos mapas (`data/maps/*/text.inc`), por grupo de mapas.

Cada grupo da frente entra em `GRUPOS` (as tasks seguintes só acrescentam o seu). Para os arquivos
de cada grupo, afirma: nenhum inglês sobrando (relatório `ingles` da checagem de texto), nenhum
achado das regras de largura/linhas/letras/charmap/terminador, `controle` (códigos de controle
iguais aos da base inglesa) e `glossario` (termo proibido ou inglês do glossário), e que nenhum
rótulo foi perdido ou criado em relação à base inglesa.
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

# Regras que um texto traduzido da frente não pode violar (a regra `ingles` é conferida à parte)
RULES = ("largura", "linhas", "letras", "charmap", "terminador", "controle", "glossario")

GRUPOS = {
    "C1": [
        "data/maps/SafariZone_North/text.inc",
        "data/maps/SafariZone_North_RestHouse/text.inc",
        "data/maps/SafariZone_SecretHouse/text.inc",
        "data/maps/SafariZone_West/text.inc",
        "data/maps/SafariZone_West_RestHouse/text.inc",
        "data/maps/SaffronCity/text.inc",
        "data/maps/SaffronCity_CopycatsHouse_1F/text.inc",
        "data/maps/SaffronCity_CopycatsHouse_2F/text.inc",
        "data/maps/SaffronCity_Dojo/text.inc",
        "data/maps/SaffronCity_Gym/text.inc",
        "data/maps/SaffronCity_House/text.inc",
        "data/maps/SaffronCity_Mart/text.inc",
        "data/maps/SaffronCity_MrPsychicsHouse/text.inc",
        "data/maps/SaffronCity_PokemonCenter_1F/text.inc",
        "data/maps/SaffronCity_PokemonTrainerFanClub/text.inc",
        "data/maps/SeafoamIslands_B4F/text.inc",
        "data/maps/SevenIsland/text.inc",
        "data/maps/SevenIsland_House_Room1/text.inc",
        "data/maps/SevenIsland_Mart/text.inc",
        "data/maps/SevenIsland_PokemonCenter_1F/text.inc",
        "data/maps/SevenIsland_SevaultCanyon/text.inc",
        "data/maps/SevenIsland_SevaultCanyon_Entrance/text.inc",
        "data/maps/SevenIsland_SevaultCanyon_House/text.inc",
        "data/maps/SevenIsland_SevaultCanyon_TanobyKey/text.inc",
        "data/maps/SevenIsland_TanobyRuins/text.inc",
        "data/maps/SevenIsland_TrainerTower/text.inc",
        "data/maps/SilphCo_10F/text.inc",
        "data/maps/SilphCo_11F/text.inc",
    ],
}

ARQUIVOS = sorted({f for files in GRUPOS.values() for f in files})


@pytest.fixture(scope="module")
def achados():
    """Achados da checagem de texto, por arquivo, só das regras da frente."""
    if shutil.which("git") is None:
        pytest.skip("sem git")
    base = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "-e", ct.TRANSLATION_BASE],
                          capture_output=True)
    if base.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    por_arquivo: dict[str, list[str]] = {}
    for res in ct.check_text(str(REPO_ROOT), exceptions, english="desligado"):
        regra = res.name.split("/", 1)[-1]
        if res.status == "aviso" and "base inglesa indisponível" in res.detail:
            pytest.fail(f"controle/glossário não rodaram: {res.detail}")
        if res.status == "falha" and regra in RULES:
            arquivo = res.detail.split(":", 1)[0]
            por_arquivo.setdefault(arquivo, []).append(res.detail)
    return por_arquivo


@pytest.fixture(scope="module")
def ingles():
    return ct.english_report(str(REPO_ROOT))


def test_grupos_sem_arquivo_repetido():
    todos = [f for files in GRUPOS.values() for f in files]
    assert len(todos) == len(set(todos))
    assert all((REPO_ROOT / f).is_file() for f in todos)


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_nenhum_ingles_sobrando(rel, ingles):
    c = ingles.get(rel)
    assert c is None, f"{rel}: {c.words} palavras inglesas em {c.texts} textos (ex.: {', '.join(c.examples)})"


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_nenhum_achado_das_regras(rel, achados):
    assert achados.get(rel, []) == []


def _labels(text: str) -> list[str]:
    return re.findall(r"^(\w+)::", text, re.M)


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_rotulos_iguais_aos_da_base(rel):
    if shutil.which("git") is None:
        pytest.skip("sem git")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    atual = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert _labels(atual) == _labels(out.stdout.decode("utf-8"))


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_dialogo_traduzido_nao_tem_caixa_alta_do_jogo_ingles(rel):
    """Palavra em CAIXA ALTA de 3+ letras = grafia do FRLG inglês (a tradução usa caixa mista),
    salvo a fala em caixa alta de propósito, registrada em `GRITOS`; texto em japonês fica de fora."""
    sobras = []
    rotulo = None
    for linha in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+)::", linha)
        if m:
            rotulo = m.group(1)
            continue
        s = re.match(r'\s*\.string "(.*)"$', linha)
        if not s or rotulo in GRITOS or re.search(r"[぀-ヿ一-鿿]", s.group(1)):
            continue
        limpo = re.sub(r"\{[^}]*\}|\\[nlp]", " ", s.group(1))
        sobras += [f"{rotulo}: {w}" for w in re.findall(r"(?<!\w)[A-ZÀ-Ý]{3,}(?!\w)", limpo)]
    assert sobras == []


# Falas em caixa alta de propósito (grito do Doduo no espelho da Imitadora)
GRITOS = {"SaffronCity_CopycatsHouse_2F_Text_Doduo"}


def _texto_por_rotulo(rel: str) -> dict[str, str]:
    """Rótulo -> texto cru (as quebras de linha ficam no texto)."""
    textos: dict[str, list[str]] = {}
    rotulo = None
    for linha in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+)::", linha)
        if m:
            rotulo = m.group(1)
            textos[rotulo] = []
            continue
        s = re.match(r'\s*\.string "(.*)"$', linha)
        if s and rotulo:
            textos[rotulo].append(s.group(1))
    return {k: "".join(v) for k, v in textos.items()}


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_nome_do_glossario_nao_e_partido_na_quebra(rel):
    """Nome de várias palavras do glossário (lugar, personagem, golpe, item) ou "Equipe Rocket"
    fica inteiro na mesma linha, nunca partido pela quebra."""
    glossario = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    nomes = {t["pt"] for t in glossario["termos"]
             if " " in t["pt"] and len(t["pt"]) > 5 and "{" not in t["pt"] and t["categoria"] != "interface"}
    nomes |= {"Equipe Rocket", "Poké Bola", "Poké Bolas", "Dojo de Luta", "Mestre de Caratê",
              "Deslize de Pedras", "Dança das Espadas", "Repelente Máximo", "Ataque Especial",
              "Defesa Especial", "Dentes de Ouro"}
    quebra = "(?: |" + chr(92) * 2 + "[nl])"
    partidos = []
    for rotulo, texto in _texto_por_rotulo(rel).items():
        for nome in nomes:
            padrao = quebra.join(re.escape(p) for p in nome.split(" "))
            for m in re.finditer(padrao, texto):
                if chr(92) in m.group(0):
                    partidos.append(f"{rotulo}: {nome!r}")
    assert partidos == []


# {STR_VAR_n}/{B_BUFF*}: a esteira mede esses placeholders como 0 px; aqui valem 10 letras largas
PLACEHOLDER = re.compile(r"\{(?:STR_VAR_\d|B_BUFF\d|B_COPY_VAR_\d)\}")


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_linha_com_placeholder_cabe_com_nome_largo(rel):
    env = ct._load_env(REPO_ROOT)
    estouros = []
    rotulo = None
    for linha in (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+)::", linha)
        if m:
            rotulo = m.group(1)
            continue
        s = re.match(r'\s*\.string "(.*)"$', linha)
        if not s or not PLACEHOLDER.search(s.group(1)) or re.search(r"[぀-ヿ]", s.group(1)):
            continue
        texto = re.sub(r"(?:\\[nlp])+$", "", PLACEHOLDER.sub("M" * 10, s.group(1)))
        largura = ct.measure(texto, env, "normal").widest
        if largura > 208:
            estouros.append(f"{rotulo}: {largura} px: {s.group(1)}")
    assert estouros == []


# Regra de 20/10: o jogador pode ser menina; a fala dirigida a ele (ou {PLAYER} em 3ª pessoa) não marca gênero
JOGADOR_COM_GENERO = ("você é bom!", "ser ganancioso", "campeão em formação", "de si mesmo", "tão bruto",
                      "ser discreto", "um Treinador incrivelmente", "cara de vencedor", "Que Treinador incrível",
                      "um Treinador com a sua", "Treinador problemático", "Bem-vindo", "Seja bem-vindo",
                      "Mestre de Caratê que", "meu único e inigualável")


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_jogador_sem_genero_marcado(rel):
    corpo = "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / rel).read_text(encoding="utf-8")))
    corpo = re.sub(r"\\[nlp]", " ", corpo)
    assert [f for f in JOGADOR_COM_GENERO if f in corpo] == []
