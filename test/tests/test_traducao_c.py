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
    "C2": [
        "data/maps/SilphCo_1F/text.inc",
        "data/maps/SilphCo_2F/text.inc",
        "data/maps/SilphCo_3F/text.inc",
        "data/maps/SilphCo_4F/text.inc",
        "data/maps/SilphCo_5F/text.inc",
        "data/maps/SilphCo_6F/text.inc",
        "data/maps/SilphCo_7F/text.inc",
        "data/maps/SilphCo_8F/text.inc",
        "data/maps/SilphCo_9F/text.inc",
        "data/maps/SixIsland/text.inc",
        "data/maps/SixIsland_DottedHole_SapphireRoom/text.inc",
        "data/maps/SixIsland_GreenPath/text.inc",
        "data/maps/SixIsland_House/text.inc",
        "data/maps/SixIsland_Mart/text.inc",
        "data/maps/SixIsland_OutcastIsland/text.inc",
        "data/maps/SixIsland_PatternBush/text.inc",
        "data/maps/SixIsland_PokemonCenter_1F/text.inc",
        "data/maps/SixIsland_RuinValley/text.inc",
        "data/maps/SixIsland_WaterPath/text.inc",
        "data/maps/SixIsland_WaterPath_House1/text.inc",
        "data/maps/SixIsland_WaterPath_House2/text.inc",
        "data/maps/ThreeIsland/text.inc",
        "data/maps/ThreeIsland_BerryForest/text.inc",
        "data/maps/ThreeIsland_BondBridge/text.inc",
        "data/maps/ThreeIsland_DunsparceTunnel/text.inc",
        "data/maps/ThreeIsland_House1/text.inc",
        "data/maps/ThreeIsland_House2/text.inc",
        "data/maps/ThreeIsland_House3/text.inc",
        "data/maps/ThreeIsland_House4/text.inc",
        "data/maps/ThreeIsland_House5/text.inc",
        "data/maps/ThreeIsland_Mart/text.inc",
        "data/maps/ThreeIsland_PokemonCenter_1F/text.inc",
        "data/maps/ThreeIsland_Port/text.inc",
        "data/maps/TrainerTower_Lobby/text.inc",
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
              "Defesa Especial", "Dentes de Ouro",
              # C2: nomes criados em fala (alguns são "interface" no glossário e ficam fora do filtro acima)
              "Irmãos Rocket", "Relatório Pokémon", "Quadro de Tempos", "Pontos de Exp.", "Centro Pokémon",
              "Federação Motoqueira de Kanto", "Filial de Tiksi", "Porto da Ilha Seis",
              "Bosque das Frutas", "Ponte da União", "Torre do Treinador", "Cartão-chave", "Bola Mestra",
              "Restaura Tudo", "Onda Trovão", "Líder de Ginásio", "Elite Quatro", "Ilhas Sevii"}
    # plural simples ("Irmãos Rocket", "Motoqueiros ..."): "s" na última palavra de cada trecho
    for nome in list(nomes):
        palavras = nome.split(" ")
        for j, p in enumerate(palavras):
            if p[-1:].isalpha() and not p.endswith("s"):
                nomes.add(" ".join(palavras[:j] + [p + "s"] + palavras[j + 1:]))
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
        # pior caso: 10 letras largas, salvo exceção provada no C (VAR_CONTENTS: tempo da Torre = 2 algarismos)
        tamanhos = ct.var_sizes(rel, rotulo)

        def pior_caso(m, tamanhos=tamanhos):
            nome = m.group(0)[1:-1]
            t = tamanhos.get(nome)
            return ("0" if t is not None and t.digits else "M") * (t.chars if t is not None else 10)

        texto = re.sub(r"(?:\\[nlp])+$", "", PLACEHOLDER.sub(pior_caso, s.group(1)))
        largura = ct.measure(texto, env, "normal").widest
        if largura > 208:
            estouros.append(f"{rotulo}: {largura} px: {s.group(1)}")
    assert estouros == []


# Regra de 20/10: o jogador pode ser menina; a fala dirigida a ele (ou {PLAYER} em 3ª pessoa) não marca gênero
JOGADOR_COM_GENERO = ("você é bom!", "ser ganancioso", "campeão em formação", "de si mesmo", "tão bruto",
                      "ser discreto", "um Treinador incrivelmente", "cara de vencedor", "Que Treinador incrível",
                      "um Treinador com a sua", "Treinador problemático", "Bem-vindo", "Seja bem-vindo",
                      "Mestre de Caratê que", "meu único e inigualável",
                      # C2: padrões que o inglês marcaria (kid/hero/intruder/traitor/tired...)
                      "nosso herói", "Intruso", "Você parece cansado", "Você é um traidor", "Traidor!",
                      "bom Treinador", "ser um Treinador", "campeão", "rapaz,", "garoto",
                      "sozinho no", "sozinho?", "tão corajoso", "muito corajoso",
                      # fix 1 da C2: "amigo deles" dirigido ao jogador; vocativo "cara" fora (em NPC para NPC fica)
                      "amigo deles", "amiga deles", "Você é amigo", "Você é amiga", "amigo d", "amiga d",
                      "Nada a ver, cara", "nos envergonhou, cara", "do sério, cara")


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_jogador_sem_genero_marcado(rel):
    corpo = "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / rel).read_text(encoding="utf-8")))
    corpo = re.sub(r"\\[nlp]", " ", corpo)
    assert [f for f in JOGADOR_COM_GENERO if f in corpo] == []


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_fim_de_arquivo_igual_ao_da_base(rel):
    """O fim do arquivo (linha em branco final, ou não) é o da versão inglesa."""
    if shutil.which("git") is None:
        pytest.skip("sem git")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    base = out.stdout.decode("utf-8")
    atual = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert len(atual) - len(atual.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


# Unidades: o jogo passou a usar metro/quilo; nada de pés, polegadas, libras, milhas...
IMPERIAL = re.compile(r"\b(?:inch(?:es)?|polegadas?|libras?|lbs?\.?|feet|foot|milhas?|jardas?|onças?)\b"
                      r"|\d\s*(?:ft|pés?|pol\.?)(?!\w)", re.I)


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_sem_unidade_imperial(rel):
    corpo = "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / rel).read_text(encoding="utf-8")))
    corpo = re.sub(r"\{[^}]*\}|\\[nlp]", " ", corpo)
    assert IMPERIAL.findall(corpo) == []


def test_medidas_do_heracross_em_centimetros():
    """O recorde de tamanho vem de `FormatMonSizeRecord` (src/pokemon_size_record.c): com UNITS_METRIC sai
    "150,0" (cm, vírgula decimal). Os textos dizem "cm" e a altura fixa da casa vizinha (67,0 pol) virou 1,70 m."""
    casa1 = _texto_por_rotulo("data/maps/SixIsland_WaterPath_House1/text.inc")
    usos = {r: t for r, t in casa1.items() if re.search(r"\{STR_VAR_[23]\}", t)}
    assert len(usos) == 4      # as 4 falas com medida (a 5ª, "tabela em branco", não tem número)
    for rotulo, texto in usos.items():
        assert not re.search(r"\{STR_VAR_[23]\}(?! cm)", texto), rotulo
    casa2 = _texto_por_rotulo("data/maps/SixIsland_WaterPath_House2/text.inc")
    assert "1,70 m" in casa2["SixIsland_WaterPath_House2_Text_MyNeighborMeasuredMe"]


# Termos que a C2 criou (glossário "criado") têm de estar registrados e aparecer nas falas
TERMOS_C2 = {
    "ROCKET BROTHERS": ("Irmãos Rocket", "data/maps/SilphCo_6F/text.inc"),
    "TIKSI BRANCH": ("Filial de Tiksi", "data/maps/SilphCo_6F/text.inc"),
    "POKéMON REPORT": ("Relatório Pokémon", "data/maps/SilphCo_5F/text.inc"),
    "KANTO RIDER FEDERATION": ("Federação Motoqueira de Kanto", "data/maps/ThreeIsland_Port/text.inc"),
    "TIME ATTACK": ("Contra-Relógio", "data/maps/TrainerTower_Lobby/text.inc"),
    "TIME BOARD": ("Quadro de Tempos", "data/maps/TrainerTower_Lobby/text.inc"),
    "SIX ISLE PORT": ("Porto da Ilha Seis", "data/maps/SixIsland_OutcastIsland/text.inc"),
}


@pytest.mark.parametrize("en", sorted(TERMOS_C2))
def test_termo_criado_na_c2_esta_no_glossario_e_na_fala(en):
    glossario = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    entradas = [t for t in glossario["termos"] if t["en"] == en]
    pt, arquivo = TERMOS_C2[en]
    assert len(entradas) == 1 and entradas[0]["pt"] == pt and entradas[0]["fonte"] == "criado"
    corpo = re.sub(r"\\[nlp]", " ", "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / arquivo).read_text(encoding="utf-8"))))
    assert pt in corpo


def test_ha_texto_com_placeholder_variavel_nos_dois_grupos():
    """A checagem de largura com 10 letras só vale se houver o que medir em cada grupo."""
    for grupo, arquivos in GRUPOS.items():
        n = sum(bool(PLACEHOLDER.search((REPO_ROOT / rel).read_text(encoding="utf-8"))) for rel in arquivos)
        assert n >= 1, grupo
