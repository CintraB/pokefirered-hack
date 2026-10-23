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
    "C3": [
        "data/maps/TwoIsland/text.inc",
        "data/maps/TwoIsland_CapeBrink_House/text.inc",
        "data/maps/TwoIsland_House/text.inc",
        "data/maps/TwoIsland_JoyfulGameCorner/text.inc",
        "data/maps/TwoIsland_PokemonCenter_1F/text.inc",
        "data/maps/UndergroundPath_EastEntrance/text.inc",
        "data/maps/UndergroundPath_SouthEntrance/text.inc",
        "data/maps/UndergroundPath_WestEntrance/text.inc",
        "data/maps/VermilionCity/text.inc",
        "data/maps/VermilionCity_Gym/text.inc",
        "data/maps/VermilionCity_House1/text.inc",
        "data/maps/VermilionCity_House2/text.inc",
        "data/maps/VermilionCity_House3/text.inc",
        "data/maps/VermilionCity_Mart/text.inc",
        "data/maps/VermilionCity_PokemonCenter_1F/text.inc",
        "data/maps/VermilionCity_PokemonFanClub/text.inc",
        "data/maps/VictoryRoad_1F/text.inc",
        "data/maps/VictoryRoad_2F/text.inc",
        "data/maps/VictoryRoad_3F/text.inc",
        "data/maps/ViridianCity/text.inc",
        "data/maps/ViridianCity_Gym/text.inc",
        "data/maps/ViridianCity_House/text.inc",
        "data/maps/ViridianCity_Mart/text.inc",
        "data/maps/ViridianCity_PokemonCenter_1F/text.inc",
        "data/maps/ViridianCity_School/text.inc",
        "data/maps/ViridianForest/text.inc",
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
              "Restaura Tudo", "Onda Trovão", "Líder de Ginásio", "Elite Quatro", "Ilhas Sevii",
              # C3: nomes de fala que o glossário só tem abreviados ou em outra forma
              "Faca de Dois Gumes", "Onda de Choque", "Ferrão Venenoso", "Cura Queimadura", "Bilhete Místico",
              "Bilhete Aurora", "Loja de Bicicletas", "Mestre da Pesca", "Maníaco dos Golpes", "Rei do Caratê",
              "Americano Relâmpago", "Cassino da Alegria", "Barras Fúria", "Dicas de Treinador", "Floresta Viridian",
              "Cidade de Viridian", "Cidade Vermilion", "Cidade de Pewter", "Cidade de Lavender", "Cidade de Celadon",
              "Cidade de Cerulean", "Cidade de Saffron", "Cidade de Pallet", "Via Subterrânea", "Porto Vermilion",
              "Estrada da Vitória", "Túnel de Pedra", "Liga Pokémon", "Sala União", "balsa Seagallop",
              "Seagallop Hi-Speed", "Explorador VS", "Passe 7 Cores", "Passe Triplo", "Fã-clube Pokémon",
              "TV Educativa", "Ginásio Pokémon", "Rocha Umbigo", "Ilha do Nascimento", "Prof. Carvalho"}
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
    # "Rumo ao título de campeão!" (Gym Guy, C3) nomeia o título, não o jogador: o "campeão" avulso segue proibido
    corpo = corpo.replace("título de campeão", "título")
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


# ---------------------------------------------------------------------------------------------
# Rodada 3 (C3: TwoIsland, Underground Path, Vermilion, Victory Road, Viridian)
# ---------------------------------------------------------------------------------------------

# Gênero do jogador, regras de 20/10 e 21/10 (A1, B2, C2, D2): palavras soltas, insulto "Seu X!"/"Ora, seu!",
# vocativo "amigo"/"cara" (o "Cara Pokémon" não conta), "o protagonista"/"o personagem principal" e o plural
# masculino que inclui o jogador ("vocês todos"). As regex rodam sobre o texto com as quebras viradas em espaço.
PLAYER_GENDERED_R3 = tuple(re.compile(p) for p in (
    r"\bavisad[oa]\b", r"\bladrão\b", r"\bderrotado\b", r"\bsozinho\b", r"\bpreparado\b", r"\b[Bb]em-vindo\b",
    r"\bocupado\b", r"\bpronto\b", r"\bcansado\b", r"\bperdedor\b", r"\bbruto\b", r"\bganancioso\b",
    r"(?:^|[!?.…] )Seu \w+!", r", seu \w+!", r"\b[Oo]ra, seu\b",
    r"\b[Aa]migo\b", r"\b[Cc]ara\b(?! Pokémon)", r"\b[Rr]apaz\b", r"\b[Gg]aroto\b", r"\b[Nn]ovato\b",
    r"\bprotagonista\b", r"\bpersonagem principal\b", r"\bcampeão em formação\b",
    r"(?i)\bvocês tod[oa]s\b", r"(?i)\btodos vocês\b",
))

# Adjetivo/particípio masculino logo depois de "você" + verbo de ligação (ou {PLAYER} em 3ª pessoa)
_COPULA_R3 = r"(?:é|está|estava|era|foi|ser|estar|ficar|fica|ficou|parece|estiver|for|seja)"
_INTENS_R3 = r"(?:muito|bem|tão|mais|menos|meio|bastante|realmente|sempre)"
GENDERED_ADJ_R3 = re.compile(
    rf"(?<!\w)(?:[Vv]ocê|{{PLAYER}})\s+(?:não\s+)?{_COPULA_R3}\s+(?:{_INTENS_R3}\s+)?"
    rf"(?!{_INTENS_R3}\b)(?!\w*ndo\b)(\w{{3,}}(?:o|ado|ido|oso|udo))\b")
# "você é/está <palavra em -o>" que não marca o gênero do jogador (palavra -> motivo)
GENDERED_ADJ_R3_OK: dict[str, str] = {}


def _c3_corpo(rel: str) -> str:
    """Todo o texto do arquivo numa linha só: quebras literais viram espaço, só {PLAYER} sobra entre chaves."""
    corpo = " ".join(_texto_por_rotulo(rel).values())
    corpo = re.sub(r"\{[^}]*\}", lambda m: "{PLAYER}" if m.group(0) == "{PLAYER}" else " ", corpo)
    return re.sub(r"\\[nlp]", " ", corpo)


GRUPO_C3 = GRUPOS["C3"]


@pytest.mark.parametrize("rel", GRUPO_C3)
def test_c3_nenhum_padrao_de_genero_do_jogador(rel):
    corpo = _c3_corpo(rel)
    achados = [m.group(0) for p in PLAYER_GENDERED_R3 for m in p.finditer(corpo)]
    achados += [m.group(0) for m in GENDERED_ADJ_R3.finditer(corpo) if m.group(1) not in GENDERED_ADJ_R3_OK]
    assert achados == []


@pytest.mark.parametrize("bruto", [
    "Valeu, amigo!", "Ei, cara, espere!", "Ora, seu!", "Seu fracote!", "Droga, seu fracote!",
    r"Ei,\ncara!", r"Ora,\nseu!", r"Tchau,\lamigo!", r"Ganhei!\pSeu fracote!",
    "Você é o protagonista.", r"Você é o\nprotagonista.", "Vocês todos são pomposos!", r"Vocês\ntodos!",
    "Você foi avisado.", r"Foi\navisado.", "Você ficou sozinho no mapa.", "Bem-vindo!",
])
def test_c3_padroes_de_genero_pegam_os_casos_conhecidos(bruto):
    flat = re.sub(r"\\[nlp]", " ", bruto)
    assert [m.group(0) for p in PLAYER_GENDERED_R3 for m in p.finditer(flat)], bruto


@pytest.mark.parametrize("bruto", [
    "Você está pronto?", r"Você ser\nrápido", r"Você está\pmuito cansado", "{PLAYER} está pronto",
    "Sim, {PLAYER} foi esperto", "Você não é preguiçoso",
])
def test_c3_padrao_de_adjetivo_masculino_pega_os_casos_conhecidos(bruto):
    flat = re.sub(r"\\[nlp]", " ", bruto)
    assert GENDERED_ADJ_R3.search(flat), bruto


@pytest.mark.parametrize("bruto", [
    "Parabéns! Seu {STR_VAR_1} evoluiu!", "O Cara Pokémon usou o item!", "Os seus Pokémon.", "Você manda bem!",
    "Você está sem tempo?", "Você é legal!", "Acho que podemos ser amigos.", "Os fãs são bem-vindos!",
    "Você é melhor do que eu!", "Você está à minha altura?", "Quem é Treinador Pokémon não passa!",
])
def test_c3_padroes_de_genero_nao_acusam_falso_positivo(bruto):
    flat = re.sub(r"\\[nlp]", " ", bruto)
    flat = re.sub(r"\{[^}]*\}", lambda m: "{PLAYER}" if m.group(0) == "{PLAYER}" else " ", flat)
    assert [m.group(0) for p in PLAYER_GENDERED_R3 for m in p.finditer(flat)] == [], bruto
    assert not GENDERED_ADJ_R3.search(flat), bruto


# Termos que a C3 criou (glossário "criado") ou que outras frentes criaram e a C3 usa: registrados e nas falas
TERMOS_C3 = {
    "POKéMON MOVE MANIAC": ("Maníaco dos Golpes", "data/maps/TwoIsland_House/text.inc"),
    "KARATE KING": ("Rei do Caratê", "data/maps/ViridianCity_Gym/text.inc"),
    "Lightning American": ("Americano Relâmpago", "data/maps/VermilionCity_Gym/text.inc"),
    "Joyful GAME CORNER": ("Cassino da Alegria", "data/maps/TwoIsland/text.inc"),
    "RAGE CANDYBAR": ("Barra Fúria", "data/maps/TwoIsland/text.inc"),
    "MYSTICTICKET (forma cheia)": ("Bilhete Místico", "data/maps/VermilionCity/text.inc"),
    "AURORATICKET (forma cheia)": ("Bilhete Aurora", "data/maps/VermilionCity/text.inc"),
    # criados por outras frentes (pendência da rodada 3): "Mestre da Pesca" na casa de Vermilion
    "FISHING GURU": ("Mestre da Pesca", "data/maps/VermilionCity_House1/text.inc"),
}


@pytest.mark.parametrize("en", sorted(TERMOS_C3))
def test_c3_termo_esta_no_glossario_e_na_fala(en):
    glossario = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    entradas = [t for t in glossario["termos"] if t["en"] == en]
    pt, arquivo = TERMOS_C3[en]
    assert len(entradas) == 1 and entradas[0]["fonte"] == "criado"
    # "Barra Fúria" aparece no plural ("Barras Fúria") na fala
    assert entradas[0]["pt"] == pt
    corpo = _c3_corpo(arquivo)
    assert pt in corpo or (pt.startswith("Barra ") and "Barras " + pt[6:] in corpo)


def test_c3_pendencia_mestre_da_pesca_na_casa_de_vermilion():
    corpo = _c3_corpo("data/maps/VermilionCity_House1/text.inc")
    assert corpo.count("Mestre da Pesca") >= 2
    assert not re.search(r"(?i)guru|pescador", corpo)


def test_c3_formas_cheias_de_item_e_golpe_em_fala():
    """Decisão de 20/10: nome de item/golpe em fala usa a forma cheia quando cabe."""
    corpo = " ".join(_c3_corpo(f) for f in GRUPO_C3)
    for cheio in ("Faca de Dois Gumes", "Onda de Choque", "Ferrão Venenoso", "Cura Queimadura", "Vale Bicicleta",
                  "Bilhete Místico", "Bilhete Aurora", "Explorador VS", "Antiparalisia", "Descongelar", "Despertar"):
        assert cheio in corpo, cheio
    for curto in ("Faca 2 Gumes", "Onda Choque", "F. Venenoso", "Cura Queimad.", "Vale Bicicl.", "Bilhete Míst.",
                  "Bilh. Aurora"):
        assert curto not in corpo, curto


def test_c3_fala_de_vermilion_e_viridian_sem_o_nome_em_ingles():
    corpo = " ".join(_c3_corpo(f) for f in GRUPO_C3)
    for ingles in ("VERMILION", "VIRIDIAN", "S.S. ANNE", "SEAGALLOP", "THUNDERBADGE", "EARTHBADGE", "Lt. Surge",
                   "LT. SURGE", "TM34", "TM26"):
        assert ingles not in corpo, ingles
    # MT34/MT26 (TM -> MT) e as insígnias do glossário
    assert "MT34" in corpo and "MT26" in corpo
    assert "Insígnia Trovão" in corpo and "Insígnia Terra" in corpo


def test_c3_gym_do_surge_chama_o_jogador_de_recruta():
    """O 'kid' do Ten. Surge virou 'recruta' (neutro e militar): nada de 'garoto'/'rapaz'/'moleque'."""
    corpo = _c3_corpo("data/maps/VermilionCity_Gym/text.inc")
    assert corpo.count("recruta") >= 6
    assert not re.search(r"\b(?:garoto|garota|rapaz|moleque|criança)\b(?!s)", corpo.replace("para crianças", ""))
