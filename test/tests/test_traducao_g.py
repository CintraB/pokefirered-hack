"""Frente G da tradução (itens, batalha e listas).

Task G1: descrições de item (`items.json`), frutas (`berry.c`) e enfeites (`decoration/`).
Cada arquivo traduzido não tem inglês sobrando (função de relatório da checagem de texto) nem
achado das regras de texto (`controle`, `glossario`, largura, linhas, letras, charmap).
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

# G1: arquivos desta task (acrescentar os das próximas tasks da frente)
G1_FILES = (
    "src/data/items.json",
    "src/berry.c",
    "src/data/decoration/description.h",
    "src/data/decoration/header.h",
)
FILES = G1_FILES

# Descrição que fica como estava: marcador vazio do jogo e texto que o Hack 7 já pôs em PT-BR
ITEM_DESC_UNCHANGED = {"?????", "Uma escama misteriosa que\\nfaz certo Pokémon evoluir.\\nBrilha com as cores do arco-íris."}
DECOR_NAME_UNCHANGED = {"TV"}        # sigla igual nas duas línguas
DECOR_NAME_MAX = 15                   # name[16] (include/decoration.h:46)


@pytest.fixture(scope="module")
def report():
    return ct.english_report(str(REPO_ROOT))


@pytest.fixture(scope="module")
def results():
    exceptions = json.loads((REPO_ROOT / "test" / "excecoes.json").read_text(encoding="utf-8"))
    return ct.check_text(str(REPO_ROOT), exceptions, english="desligado")


@pytest.fixture(scope="module")
def findings(results):
    return [r for r in results if r.status == "falha" and r.name.startswith("texto/")]


def test_base_inglesa_disponivel(results):
    """Sem a base, `controle` e `glossario` não rodam: o teste não pode passar calado."""
    missing = [r.detail for r in results if r.status == "aviso" and "base inglesa indisponível" in r.detail]
    assert missing == [], missing


@pytest.mark.parametrize("rel", FILES)
def test_nenhum_ingles_sobrando(rel, report):
    count = report.get(rel)
    assert count is None, f"{rel}: {count.words} palavras inglesas (ex.: {count.examples})"


@pytest.mark.parametrize("rel", FILES)
def test_nenhum_achado_das_regras_de_texto(rel, findings):
    own = [f"{r.name}: {r.detail}" for r in findings if r.detail.startswith(f"{rel}:")]
    assert own == []


@lru_cache(maxsize=None)
def _base_text(rel: str) -> str | None:
    if shutil.which("git") is None:
        return None
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    return out.stdout.decode("utf-8") if out.returncode == 0 else None


def _item_descriptions(source: str) -> dict[str, str]:
    return {f"{i}:{it['itemId']}": it["description_english"] for i, it in enumerate(json.loads(source)["items"])}


def test_toda_descricao_de_item_foi_traduzida():
    base = _base_text("src/data/items.json")
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    before = _item_descriptions(base)
    now = _item_descriptions((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))
    assert set(now) == set(before), "os itens mudaram de lugar ou de id"
    same = [k for k in before if now[k] == before[k] and now[k] not in ITEM_DESC_UNCHANGED]
    assert same == []


def test_nomes_de_item_nao_mudaram_nesta_task():
    """O campo `english` é da Task 2: a G1 só mexe em `description_english`."""
    base = _base_text("src/data/items.json")
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    names = lambda s: [(it["itemId"], it["price"], it["pocket"]) for it in json.loads(s)["items"]]
    assert names((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8")) == names(base)


def test_descricoes_de_item_tem_ate_tres_linhas_e_sem_quebra_solta():
    texts = _item_descriptions((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))
    bad = [k for k, t in texts.items() if t.count("\\n") > 2 or re.search(r"\\n\s|\s\\n|\\n\\n", t)]
    assert bad == []


def _decor_names(source: str) -> list[str]:
    return re.findall(r'_\("([^"]*)"\)', source)


def test_nomes_de_enfeite_traduzidos_e_dentro_do_buffer():
    base = _base_text("src/data/decoration/header.h")
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    before = _decor_names(base)
    now = _decor_names((REPO_ROOT / "src/data/decoration/header.h").read_text(encoding="utf-8"))
    assert len(now) == len(before)
    untranslated = [b for b, n in zip(before, now) if b == n and b not in DECOR_NAME_UNCHANGED]
    too_long = [n for n in now if len(n) > DECOR_NAME_MAX]
    assert untranslated == [] and too_long == []


def test_descricoes_de_enfeite_traduzidas_com_os_mesmos_rotulos():
    base = _base_text("src/data/decoration/description.h")
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    label = lambda s: re.findall(r"const u8 (DecorDesc_\w+)\[\]", s)
    now = (REPO_ROOT / "src/data/decoration/description.h").read_text(encoding="utf-8")
    assert label(now) == label(base)
    # nenhuma descrição ficou igual à inglesa: o trecho entre `_(` e `);` mudou em todas
    blocks = lambda s: re.findall(r"= _\(\n(.*?)\);", s, re.S)
    assert [b for b, n in zip(blocks(base), blocks(now)) if b == n] == []


def test_frutas_tem_nome_e_descricao_de_item_em_portugues():
    """As descrições curtas de `berry.c` são japonesas e sem uso (a bolsa de frutas mostra a descrição
    do `items.json`); a que o jogador lê é a do item."""
    items = json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]
    berries = [it for it in items if it["itemId"].endswith("_BERRY")]
    assert len(berries) == 43
    assert all(it["english"].startswith("Fruta ") for it in berries)
    assert all(re.search(r"[áéíóúãõç]| a | de | o ", it["description_english"]) for it in berries)


def _glossary_terms() -> set[str]:
    g = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    terms = {t["pt"] for t in g["termos"]
             if " " in t["pt"] and t["categoria"] in ("lugar", "item", "personagem")}
    return terms | {"Atq. Esp.", "Def. Esp.", "Poké Mart"}


def _g1_texts() -> dict[str, str]:
    """rótulo -> texto com as quebras (`\n` literal) das descrições de item e de enfeite."""
    texts = {it["itemId"]: it["description_english"]
             for it in json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]}
    src = (REPO_ROOT / "src/data/decoration/description.h").read_text(encoding="utf-8")
    for m in re.finditer(r"const u8 (\w+)\[\] = _\(\n(.*?)\);", src, re.S):
        texts[m.group(1)] = "".join(re.findall(r'"([^"]*)"', m.group(2)))
    return texts


def test_quebra_de_linha_nao_parte_nome_nem_termo():
    terms = _glossary_terms()
    # quebra num espaço ("Loja de\nBicicletas") ou num ponto sem espaço ("S.\nS. Anne")
    split = [f"{label}: {term}" for label, text in _g1_texts().items()
             for term in terms
             if term not in text and (term in text.replace("\\n", " ") or term in text.replace("\\n", ""))]
    assert split == []


def test_fruta_cabe_em_duas_linhas_na_bolsa_de_frutas():
    """berry_pouch.c:229-231 e :762: janela de 4 tiles de altura, texto em y = 2, linhas de 14 px."""
    items = json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]
    berries = [it for it in items if it["pocket"] == "POCKET_BERRY_POUCH"]
    assert len(berries) == 43
    long = [it["itemId"] for it in berries if it["description_english"].count("\\n") > 1]
    assert long == []


def test_descricao_de_item_cabe_na_janela_mais_estreita(env):
    """Item no PC de Pokémon (pokemon_storage_system_misc.c:1151): 25 tiles com x = 2, 198 px."""
    items = json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]
    wide = [f"{it['itemId']}: {ct.measure(it['description_english'], env, 'normal').widest} px"
            for it in items if it["description_english"] != "?????"
            and ct.measure(it["description_english"], env, "normal").widest > 198]
    assert wide == []


@pytest.fixture(scope="module")
def env():
    return ct._load_env(REPO_ROOT)
