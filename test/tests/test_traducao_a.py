"""Frente A da tradução: diálogos dos mapas (`data/maps/*/text.inc`), grupo a grupo.

Para os arquivos de cada grupo já traduzido: nenhum inglês sobrando (função de relatório de inglês
da checagem de texto), nenhum achado das regras de texto da esteira (`controle`, `glossario`,
largura, linhas, letras, charmap) e os rótulos iguais aos da base inglesa. Task seguinte da frente:
acrescentar o grupo em `GRUPOS`.
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

# grupo -> pastas de mapa (text.inc) traduzidas
GRUPOS = {
    "A1": [
        "CeladonCity", "CeladonCity_Condominiums_1F", "CeladonCity_Condominiums_2F",
        "CeladonCity_Condominiums_3F", "CeladonCity_Condominiums_Roof", "CeladonCity_Condominiums_RoofRoom",
        "CeladonCity_DepartmentStore_1F", "CeladonCity_DepartmentStore_2F", "CeladonCity_DepartmentStore_3F",
        "CeladonCity_DepartmentStore_4F", "CeladonCity_DepartmentStore_5F", "CeladonCity_DepartmentStore_Roof",
        "CeladonCity_GameCorner", "CeladonCity_GameCorner_PrizeRoom", "CeladonCity_Gym", "CeladonCity_Hotel",
        "CeladonCity_House1", "CeladonCity_PokemonCenter_1F", "CeladonCity_Restaurant", "CeruleanCave_B1F",
        "CeruleanCity", "CeruleanCity_BikeShop", "CeruleanCity_Gym", "CeruleanCity_House1", "CeruleanCity_House2",
        "CeruleanCity_House3", "CeruleanCity_House4", "CeruleanCity_House5", "CeruleanCity_Mart",
        "CeruleanCity_PokemonCenter_1F", "CinnabarIsland", "CinnabarIsland_Gym",
    ],
}
FILES = [f"data/maps/{m}/text.inc" for maps in GRUPOS.values() for m in maps]

# Inglês que a checagem conta mas é legítimo: (arquivo, palavras, textos) -> motivo
ENGLISH_EXCEPTIONS = {
    # "TO" = Treinador Original (glossário: OT -> TO); "to" está na lista de palavras inglesas
    "data/maps/CeladonCity_DepartmentStore_3F/text.inc": (2, 1),
}


@pytest.fixture(scope="module")
def results():
    if shutil.which("git") is None:
        pytest.skip("sem git")
    return ct.check_text(str(REPO_ROOT), {"text": []}, english="desligado")


def test_base_inglesa_disponivel(results):
    """Sem a base, `controle` e `glossario` não rodam (o aviso não cita arquivo): não pode ficar verde calado."""
    assert [r.detail for r in results if "base inglesa indisponível" in r.detail] == []


def _mine(results, rule=None):
    # achado conhecido de regra nova (check_text.KNOWN_FINDINGS, T4) é aviso que a frente corrige depois
    return [r for r in results if r.status != "ok" and any(f in r.detail for f in FILES)
            and not (r.status == "aviso" and "(conhecido:" in r.detail)
            and (rule is None or r.name == f"texto/{rule}")]


@pytest.mark.parametrize("rule", ["largura", "linhas", "letras", "charmap", "terminador", "controle", "glossario"])
def test_nenhum_achado_das_regras_nos_arquivos_da_frente(results, rule):
    assert [f"{r.detail}" for r in _mine(results, rule)] == []


def test_nenhum_achado_de_texto_nos_arquivos_da_frente(results):
    # qualquer outra regra de texto, com os arquivos da frente no detalhe
    assert [f"{r.name}: {r.detail}" for r in _mine(results)] == []


def test_nenhum_ingles_sobrando():
    report = ct.english_report(str(REPO_ROOT))
    left = {}
    for f in FILES:
        c = report.get(f)
        if c is None:
            continue
        if (c.words, c.texts) == ENGLISH_EXCEPTIONS.get(f):
            continue
        left[f] = (c.words, c.texts, c.examples)
    assert left == {}


def test_excecao_do_to_continua_sendo_so_a_sigla():
    """A única exceção do relatório de inglês é a sigla TO (Treinador Original)."""
    text = (REPO_ROOT / "data/maps/CeladonCity_DepartmentStore_3F/text.inc").read_text(encoding="utf-8")
    block = text[text.index("OTStandsForOriginalTrainer::"):]
    block = block[:block.index("$")]
    words = ct._plain_words(block.replace(".string", " "))
    assert [w for w in words if w.lower() in ct.ENGLISH_WORDS] == ["TO", "TO"]


@lru_cache(maxsize=None)
def _base_labels(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        return None
    return re.findall(r"^(\w+)::", out.stdout.decode("utf-8"), re.M)


@pytest.mark.parametrize("rel", FILES)
def test_rotulos_iguais_aos_da_base(rel):
    if shutil.which("git") is None:
        pytest.skip("sem git")
    base = _base_labels(rel)
    if base is None:
        pytest.skip("sem o commit base da tradução")
    now = re.findall(r"^(\w+)::", (REPO_ROOT / rel).read_text(encoding="utf-8"), re.M)
    assert now == base


@pytest.mark.parametrize("rel", FILES)
def test_sem_termos_ingleses_em_caixa_alta(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    # nomes de golpe/item do jogo inglês que não podem sobrar em caixa alta no diálogo
    text = re.sub(r"{[^}]*}", "", text)
    for old in ("POKéMON", "TRAINER", "GYM", "BADGE", "TEAM ROCKET", "POKé BALL", "BERRY", "STORE", "LEADER"):
        assert old not in re.sub(r"@.*", "", text), (rel, old)


# Regras de 20/10: jogador sem gênero marcado; termos do glossário exatos; nomes não partidos na quebra
PLAYER_GENDERED = ("Fique quieto", "muito bruto", "parceiro,", "ocupado demais", "perdedor", "Aspirante a campeão",
                   "Seja bem-vindo", "Bem-vindo",
                   # padrões que escaparam na C1 + o Treinador referido ao jogador
                   "você é bom", "ganancioso", "campeão em formação", "tão bruto", "ser discreto",
                   "habilidade como", "ser um Treinador")
WRONG_FORMS = ("Esconderijo da Equipe Rocket", "Porto de Vermilion",
               # decisões do Cintra de 20/10: forma cheia em fala; títulos de jogo no original
               "Superrepel.", "Cura Queimad.", "Vale Bicicl.", "Guarda Esp.", "Expl. Sônica", "Rajada Fogo",
               "Esmaga Pedra", "Atq. Esp.", "Def. Esp.", "Vermelho e Verde")
NAMES_NOT_SPLIT = ("Equipe Rocket", "GAME FREAK", "Loja de Celadon", "Pó de Fruta", "Canto Direto",
                   "Sistema de Armazenamento de Pokémon", "Centro Pokémon", "Loja de Bicicletas",
                   "Cura Queimadura", "Vale Bicicleta", "Guarda Especial", "Explosão Sônica", "Rajada de Fogo",
                   "Esmagamento de Pedras", "Ataque Especial", "Defesa Especial", "Red e Green")


def _flat(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    body = "".join(re.findall(r'\.string "(.*)"', text))
    return body


@pytest.mark.parametrize("rel", FILES)
def test_jogador_sem_genero_e_termos_exatos(rel):
    body = _flat(rel)
    for bad in PLAYER_GENDERED + WRONG_FORMS:
        assert bad not in body, (rel, bad)


def _multiword_terms():
    """Todo termo PT de duas ou mais palavras do glossário de máquina, mais os nomes acima."""
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    names = {t["pt"] for t in data["termos"] if " " in t["pt"]} | set(NAMES_NOT_SPLIT)
    # "Centros Pokémon", "Insígnias Rocha": plural simples com "s" na última palavra de cada trecho
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
                for br in ("\\n", "\\l"):
                    if name[:i] + br + name[i + 1:] in body:
                        found.append(name)
    assert found == [], rel


@pytest.mark.parametrize("rel", FILES)
def test_fim_de_arquivo_igual_ao_da_base(rel):
    """O fim do arquivo (linha em branco final) é o da versão inglesa."""
    if shutil.which("git") is None:
        pytest.skip("sem git")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    base = out.stdout.decode("utf-8")
    now = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert len(now) - len(now.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


# Regra de 20/10: a esteira mede {STR_VAR_n}/{B_BUFF*}/{B_COPY_VAR_*} como 0 px; aqui eles valem 10 "M" (largos)
VARIABLE_PLACEHOLDER = re.compile(r"\{(?:STR_VAR_\d|B_BUFF\d|B_COPY_VAR_\d)\}")
DIALOG_PX = 208


@pytest.fixture(scope="module")
def env():
    return ct._load_env(REPO_ROOT)


@pytest.mark.parametrize("rel", FILES)
def test_linhas_com_placeholder_variavel_cabem_com_10_letras_largas(rel, env):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    too_wide = []
    for m in re.finditer(r'^(\w+)::\n((?:[ \t]+\.string ".*"\n?)+)', text, re.M):
        raw = "".join(re.findall(r'\.string "(.*)"', m.group(2)))
        if not VARIABLE_PLACEHOLDER.search(raw):
            continue
        measured = ct.measure(VARIABLE_PLACEHOLDER.sub("MMMMMMMMMM", raw), env, "normal")
        if measured.widest > DIALOG_PX:
            too_wide.append(f"{m.group(1)}: {measured.widest} px")
    assert too_wide == []


def test_ha_texto_com_placeholder_variavel_no_grupo():
    """Garante que a checagem acima tem o que medir (se um dia não houver, o teste avisa)."""
    n = sum(bool(VARIABLE_PLACEHOLDER.search((REPO_ROOT / rel).read_text(encoding="utf-8"))) for rel in FILES)
    assert n >= 1
