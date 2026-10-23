"""Frente G da tradução (itens, batalha e listas).

Task G1: descrições de item (`items.json`), frutas (`berry.c`) e enfeites (`decoration/`).
Task G2: mensagens de batalha (`src/battle_message.c`), com a gramática montada no código
(o lado do Pokémon vira sufixo: "o Rattata selvagem", "do Pidgey inimigo").
Task G3: Easy Chat (`src/data/easy_chat/`): palavras em PT-BR, ordem alfabética PT-BR nos grupos, nos
golpes e nas listas por letra, falas da Trainer Tower e frases/senhas fixas.
Cada arquivo traduzido não tem inglês sobrando (função de relatório da checagem de texto) nem
achado das regras de texto (`controle`, `glossario`, largura, linhas, letras, charmap).
"""

import json
import re
import shutil
import subprocess
import unicodedata
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
G2_FILES = ("src/battle_message.c",)
EC_WORD_GROUPS = ("trainer", "status", "battle", "greetings", "people", "voices", "speech", "endings", "feelings",
                  "conditions", "actions", "lifestyle", "hobbies", "time", "misc", "adjectives", "events",
                  "trendy_saying")
G3_FILES = tuple(f"src/data/easy_chat/easy_chat_group_{g}.h" for g in EC_WORD_GROUPS) + (
    "src/trainer_tower_sets.c", "data/mystery_event_msg.s")
FILES = G1_FILES + G2_FILES + G3_FILES

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


# ---- G2: mensagens de batalha (src/battle_message.c) ---------------------------------------

BATTLE = "src/battle_message.c"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _battle_strings(source: str) -> dict[str, str]:
    return {e.label: e.texts[0] for e in ct._extract_c_text(BATTLE, source)}


@lru_cache(maxsize=None)
def _battle_now() -> dict[str, str]:
    return _battle_strings(_read(BATTLE))


@lru_cache(maxsize=None)
def _battle_base() -> dict[str, str] | None:
    base = _base_text(BATTLE)
    return None if base is None else _battle_strings(base)


def _need_battle_base() -> dict[str, str]:
    base = _battle_base()
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    return base


# Texto inglês que fica: sigla igual nas duas línguas
BATTLE_UNCHANGED = {"gText_MoveInterfacePP"}   # "PP " (glossário: PP)


def _letters(text: str) -> str:
    return re.sub(r"\{[^}]*\}|\\[nlp]", " ", text)


def test_toda_mensagem_de_batalha_foi_traduzida():
    """Todo texto da base com palavra latina (2+ letras) mudou; ficam só os da lista acima."""
    base, now = _need_battle_base(), _battle_now()
    renamed = {"sText_BerrySuffix": "sText_BerryPrefix"}   # "Fruta " + nome (ordem PT-BR)
    assert set(now) == {renamed.get(label, label) for label in base}, "rótulos mudaram"
    same = [label for label, text in base.items()
            if re.search(r"[A-Za-z]{2}", _letters(text)) and now[renamed.get(label, label)] == text
            and label not in BATTLE_UNCHANGED]
    assert same == []


# Gramática do lado do Pokémon: "Wild "/"Foe " viram sufixo depois do nome; o artigo fica no texto
SUFFIXES = {"sText_WildPkmnPrefix": " selvagem", "sText_FoePkmnPrefix": " inimigo"}
SIDE_WORDS = ("sText_FoePkmnPrefix2", "sText_FoePkmnPrefix3", "sText_FoePkmnPrefix4",
              "sText_AllyPkmnPrefix", "sText_AllyPkmnPrefix2", "sText_AllyPkmnPrefix3")
PREFIXED = re.compile(r"\{B_(?:ATK|DEF|EFF|ACTIVE|SCR_ACTIVE)_NAME_WITH_PREFIX(?:_MON1)?\}|\{B_26\}")
# {B_BUFF1} com apelido + sufixo (PREPARE_MON_NICK_WITH_PREFIX_BUFFER): Beat Up, Wish, Trace
# (battle_script_commands.c:8614, :8933; battle_util.c:2290) e a troca impedida (pokemon.c:6084)
NICK_WITH_SUFFIX_BUFF1 = ("sText_PkmnAttack", "sText_PkmnWishCameTrue", "sText_PkmnTraced",
                          "gText_PkmnsXPreventsSwitching")
ARTICLES = {"o", "O", "do", "no", "ao", "pelo"}


def test_lado_do_pokemon_vira_sufixo():
    now = _battle_now()
    assert {label: now[label] for label in SUFFIXES} == SUFFIXES
    assert {now[label] for label in SIDE_WORDS} == {"inimiga", "aliada"}   # "a equipe inimiga/aliada"
    src = _read(BATTLE)
    macro = src[src.index("#define HANDLE_NICKNAME_STRING_CASE"):]
    macro = macro[:macro.index("toCpy = text;")]
    # nome primeiro, sufixo depois (e nada copiado para dst antes do nome)
    assert macro.index("StringGet_Nickname(text)") < macro.index("StringAppend(text, sText_FoePkmnPrefix)")
    assert "dst[" not in macro
    buff = src[src.index("case B_BUFF_MON_NICK_WITH_PREFIX:"):]
    buff = buff[:buff.index("break;")]
    assert buff.rindex("StringAppend(dst, text)") < buff.index("sText_FoePkmnPrefix")
    # Fruta Enigma do link: "Fruta" + nome, como os nomes de item
    assert src.count("StringCopy(text, sText_BerryPrefix);") == 2
    assert "StringCopy(dst, sText_BerryPrefix);" in src


def _word_before(text: str, pos: int) -> str:
    before = re.sub(r"\\[nlp]|\{[^}]*\}", " ", text[:pos]).rstrip()
    return before.split(" ")[-1] if before else ""


def test_pokemon_com_sufixo_tem_artigo_no_texto():
    """O placeholder dá "Rattata selvagem"; o artigo (sempre masculino: "o Pokémon") vem no texto."""
    missing = []
    for label, text in _battle_now().items():
        spots = [m.start() for m in PREFIXED.finditer(text)]
        if label in NICK_WITH_SUFFIX_BUFF1:
            spots += [m.start() for m in re.finditer(r"\{B_BUFF1\}", text)]
        for pos in spots:
            if _word_before(text, pos) not in ARTICLES:
                missing.append(f"{label}: …{text[max(0, pos - 12):pos + 25]}")
    assert missing == []
    side = [f"{label}: {text}" for label, text in _battle_now().items()
            for m in re.finditer(r"\{B_(?:ATK|DEF)_PREFIX\d\}", text) if _word_before(text, m.start()) != "equipe"]
    assert side == []


# Mudança de atributo: "Aumentou o Ataque do Pidgey inimigo!" (verbo primeiro, artigo no nome)
STAT_TEMPLATES = ("sText_AttackersStatRose", "gText_DefendersStatRose", "sText_AttackersStatFell",
                  "sText_DefendersStatFell", "sText_UsingItemTheStatOfPkmnRose")
STAT_NAMES = ("sText_HP2", "sText_Attack2", "sText_Defense2", "sText_Speed", "sText_SpAtk2", "sText_SpDef2",
              "sText_Accuracy", "sText_Evasiveness")


def test_mudanca_de_atributo_com_verbo_primeiro():
    now = _battle_now()
    assert all(re.match(r"(?:o|a|os) \S", now[label]) for label in STAT_NAMES)
    assert all(now[label].startswith("{B_BUFF2} {B_BUFF1}\\n") for label in STAT_TEMPLATES)
    verbs = {label: now[label] for label in ("gBattleText_Rose", "sText_StatSharply", "sText_StatFell",
                                             "sText_StatHarshly")}
    assert verbs == {"gBattleText_Rose": "Aumentou", "sText_StatSharply": "Aumentou muito",
                     "sText_StatFell": "Diminuiu", "sText_StatHarshly": "Diminuiu muito"}
    # "muito" já tem o verbo: o código não acrescenta STATROSE/STATFELL depois dele
    cmds = _read("src/battle_script_commands.c")
    for strong in ("STRINGID_STATHARSHLY", "STRINGID_STATSHARPLY"):
        assert re.search(strong + r" >> 8;\s*index = 4;\s*\}\s*else\b", cmds), strong
    util = _read("src/battle_util.c")
    starf = util[util.index("gBattleTextBuff2[2] = STRINGID_STATSHARPLY;"):]
    assert "STRINGID_STATROSE" not in starf[:starf.index("SET_STATCHANGER")]


def _c_array_size(rel: str, name: str) -> int:
    return int(re.search(re.escape(name) + r"\[(\d+)\]", _read(rel)).group(1))


def _nbytes(text: str, env) -> int:
    return ct.measure(text, env, "normal").nbytes


def test_textos_que_vao_para_buffers_cabem(env):
    now = _battle_now()
    var2 = _c_array_size("src/string_util.c", "gStringVar2")                 # 20
    buff = int(re.search(r"TEXT_BUFF_ARRAY_COUNT\s+(\d+)", _read("include/battle_message.h")).group(1))   # 16
    problems = []
    # apelido (10) + sufixo expandido em gStringVar2/3 (B_BUFF_MON_NICK_WITH_PREFIX)
    for label in SUFFIXES:
        if 10 + _nbytes(now[label], env) + 1 > var2:
            problems.append(label)
    # "golpe X" + "!" copiados em gBattleTextBuff2 (STRINGID_USEDMOVE em BufferStringBattle)
    for label, text in now.items():
        if re.match(r"gText_An?[A-Z]\w*Move$", label) and _nbytes(text, env) + 2 > buff:
            problems.append(label)
    # nome de atributo e "Aumentou" copiados crus em gBattleTextBuff1/2 (pokemon.c, BufferStatRoseMessage)
    for label in STAT_NAMES + ("gBattleText_Rose",):
        if _nbytes(now[label], env) + 1 > buff:
            problems.append(label)
    # frases de atributo e "com bônus" expandidas em gStringVar2 (B_BUFF_STRING)
    for label in ("sText_StatSharply", "sText_StatHarshly", "sText_StatFell", "gBattleText_Rose", "sText_ABoosted"):
        if _nbytes(now[label], env) + 1 > var2:
            problems.append(label)
    # "Fruta " + nome da Fruta Enigma (BERRY_NAME_LENGTH = 6) em gStringVar2/3
    if _nbytes(now["sText_BerryPrefix"], env) + 6 + 1 > var2:
        problems.append("sText_BerryPrefix")
    # Ovo Ruim vira apelido (pokemon.c:3076): POKEMON_NAME_LENGTH
    if _nbytes(now["gText_BadEgg"], env) > 10:
        problems.append("gText_BadEgg")
    # Bolas do Safári na healthbox: u8 text[16] e texto alinhado à direita em 47 px (battle_interface.c)
    left = now["gText_HighlightRed_Left"]
    if _nbytes(left, env) + 2 + 1 > 16 or ct.measure(left, env, "small").widest + 2 * env.max_digit["small"] > 47:
        problems.append("gText_HighlightRed_Left")
    assert problems == []


def _prefix_px(strings: dict[str, str], env) -> dict[str, int]:
    labels = [label for label in strings if re.match(r"^sText_\w*Prefix\d*$", label)]
    return {font: max(ct.measure(strings[label], env, font).widest for label in labels) for font in env.widths}


def test_mensagens_cabem_com_os_buffers_no_pior_caso_real(env):
    """Além da medida da esteira (B_BUFF = 10 letras): B_BUFF com o maior conteúdo real (item, 13
    letras) e, onde é apelido + sufixo, o nome com sufixo."""
    now = _battle_now()
    env.prefix_px = _prefix_px(now, env)
    wide = []
    for label, text in now.items():
        rule = ct.rule_for(BATTLE, label)
        if rule is None or rule.px is None or "{B_BUFF" not in text:
            continue
        if label in NICK_WITH_SUFFIX_BUFF1:
            text = text.replace("{B_BUFF1}", "{B_ATK_NAME_WITH_PREFIX}")
        sizes = {name: ct.VarSize(13) for name in ("B_BUFF1", "B_BUFF2", "B_BUFF3")}
        px = ct.measure(text, env, rule.font, rule.space, False, rule.no_prefix, sizes).widest
        if px > rule.px:
            wide.append(f"{label}: {px} px > {rule.px}")
    assert wide == []


def test_cada_pagina_tem_no_maximo_duas_linhas():
    """Janela da batalha: 2 linhas por página; a 3ª entra rolando com \\l, nunca com outro \\n."""
    over = [label for label, text in _battle_now().items() for page in text.split("\\p") if page.count("\\n") > 1]
    assert over == []


# Fala dirigida ao jogador com gênero marcado (regras de 20/10 e 21/10): palavras soltas, o insulto
# "Seu X!"/"Ora, seu!" (o possessivo "Seu {STR_VAR_1}" não conta), o vocativo "amigo"/"cara" (o
# termo "Cara Pokémon" não conta), "o protagonista"/"o personagem principal" e o plural masculino
# que inclui o jogador ("vocês todos").
PLAYER_GENDERED = tuple(re.compile(p) for p in (
    r"\bavisad[oa]\b", r"\bladrão\b", r"\bderrotado\b", r"\bsozinho\b", r"\bpreparado\b", r"\bbem-vindo\b",
    r"(?:^|[!?.…] )Seu \w+!", r", seu \w+!", r"\b[Oo]ra, seu\b",
    r"\b[Aa]migo\b", r"\b[Cc]ara\b(?! Pokémon)",
    r"\bprotagonista\b", r"\bpersonagem principal\b",
    r"(?i)\bvocês tod[oa]s\b", r"(?i)\btodos vocês\b",
))


def _gendered(text: str) -> list[str]:
    flat = re.sub(r"\\[nlp]", " ", text)    # quebra literal vira espaço: o \b vale depois dela
    return [m.group(0) for p in PLAYER_GENDERED for m in p.finditer(flat)]


def test_padroes_de_genero_do_jogador_pegam_os_casos_conhecidos():
    caught = ["Ora, seu!", "Seu fracote!", "Valeu, amigo!", "Ei, cara, espere!", "Você é o protagonista.",
              "Vocês todos são pomposos!", "Você foi avisado.", "Droga, seu fracote!",
              "Foi\\navisado.", "Ei,\\ncara!", "Ora,\\nseu!", "Tchau,\\lamigo!", "Ganhei!\\pSeu fracote!",
              "Você é o\\nprotagonista.", "Vocês\\ntodos!"]
    clean = ["Parabéns! Seu {STR_VAR_1}\\nevoluiu!", "O Cara Pokémon usou\\n{B_LAST_ITEM}!", "Os seus Pokémon.",
             "O item normalizou seu status!", "O Pikachu usou\\nCara Pokémon!", "Fala com o\\pCara Pokémon."]
    assert [t for t in caught if not _gendered(t)] == []
    assert [t for t in clean if _gendered(t)] == []


def test_jogador_sem_genero_marcado():
    found = [f"{label}: {word}" for label, text in _battle_now().items() for word in _gendered(text)]
    assert found == []


# Termos de mais de uma palavra usados nas mensagens de batalha (além dos do glossário)
BATTLE_TERMS = ("Semente Sanguessuga", "Bolas Safári", "Visor Silph", "Onda de Calor", "Casaco Mágico",
                "Poder Natural", "Lodo Líquido", "Defesa Especial", "Fosso de Areia", "Ataque Espelhado",
                "Cara Pokémon", "Fruta Enigma", "Quadro de Tempos", "Atq. Esp.", "Def. Esp.")


def test_quebra_de_linha_nao_parte_termo_nas_mensagens_de_batalha():
    terms = _glossary_terms() | set(BATTLE_TERMS)
    split = [f"{label}: {term}" for label, text in _battle_now().items() for term in terms
             if term not in text and any(term in re.sub(r"\\[nlp]", sep, text) for sep in (" ", ""))]
    assert split == []


def test_texto_do_granizo_da_esteira_e_o_do_jogo():
    """test/esteira/scenarios/full_weather.py espera ler sText_StartedHail em gDisplayedStringBattle."""
    hail = re.search(r'^HAIL_TEXT = "(.*)"', _read("test/esteira/scenarios/full_weather.py"), re.M).group(1)
    assert hail == _battle_now()["sText_StartedHail"]


# ---- gDisplayedStringBattle[300]: texto expandido no pior caso ------------------------------

def _expansion_bytes(strings: dict[str, str], env) -> dict[str, int]:
    """Bytes de cada placeholder {B_*} expandido (BattleStringExpandPlaceholders), no pior caso."""
    suffix = max(_nbytes(strings[label], env) for label in SUFFIXES)
    side = max(_nbytes(strings[label], env) for label in SIDE_WORDS)
    pc = max(_nbytes(strings[label], env) for label in ("sText_Someones", "sText_Bills"))
    # B_BUFF: maior conteúdo real é apelido + sufixo, expandido em gStringVar2/3[20]
    sizes = {name: 19 for name in ("B_BUFF1", "B_BUFF2", "B_BUFF3")}
    sizes.update({"B_COPY_VAR_1": 31, "B_COPY_VAR_2": 19, "B_COPY_VAR_3": 19})   # gStringVar1[32], 2/3[20]
    sizes.update({name: 7 for name in ("B_PLAYER_NAME", "B_LINK_PLAYER_NAME", "B_LINK_PARTNER_NAME",
                                       "B_LINK_OPPONENT1_NAME", "B_LINK_OPPONENT2_NAME", "B_LINK_SCR_TRAINER_NAME")})
    sizes.update({name: 10 for name in ("B_PLAYER_MON1_NAME", "B_OPPONENT_MON1_NAME", "B_PLAYER_MON2_NAME",
                                        "B_OPPONENT_MON2_NAME", "B_LINK_PLAYER_MON1_NAME", "B_LINK_OPPONENT_MON1_NAME",
                                        "B_LINK_PLAYER_MON2_NAME", "B_LINK_OPPONENT_MON2_NAME", "B_ATK_PARTNER_NAME")})
    sizes.update({name: 10 + suffix for name in ("B_ATK_NAME_WITH_PREFIX_MON1", "B_ATK_NAME_WITH_PREFIX",
                                                 "B_DEF_NAME_WITH_PREFIX", "B_EFF_NAME_WITH_PREFIX",
                                                 "B_ACTIVE_NAME_WITH_PREFIX", "B_SCR_ACTIVE_NAME_WITH_PREFIX", "B_26")})
    sizes.update({name: side for name in ("B_ATK_PREFIX1", "B_DEF_PREFIX1", "B_ATK_PREFIX2", "B_DEF_PREFIX2",
                                          "B_ATK_PREFIX3", "B_DEF_PREFIX3")})
    sizes.update({"B_CURRENT_MOVE": 12, "B_LAST_MOVE": 12, "B_LAST_ITEM": 13, "B_TRAINER1_CLASS": 12,
                  "B_TRAINER1_NAME": 11, "B_PC_CREATOR_NAME": pc})
    sizes.update({name: 12 for name in ("B_LAST_ABILITY", "B_ATK_ABILITY", "B_DEF_ABILITY", "B_SCR_ACTIVE_ABILITY",
                                        "B_EFF_ABILITY")})
    # fala do Treinador: medida à parte (test_fala_do_treinador_cabe_...); aqui só o {PAUSE_UNTIL_PRESS}
    sizes.update({name: 2 for name in ("B_TRAINER1_LOSE_TEXT", "B_TRAINER1_WIN_TEXT", "B_TRAINER2_LOSE_TEXT",
                                       "B_TRAINER2_WIN_TEXT")})
    return sizes


def _expanded_bytes(text: str, env, sizes: dict[str, int]) -> int:
    """Bytes do texto expandido, com o terminador."""
    total = _nbytes(text, env) + 1
    for m in re.finditer(r"\{(\w+)\}", text):
        if m.group(1) in sizes:
            total += sizes[m.group(1)] - env.name_bytes[m.group(1)]
    return total


def test_mensagens_expandidas_cabem_em_gDisplayedStringBattle(env):
    """gDisplayedStringBattle[300] (battle_main.c): pior caso de cada texto <= 300 bytes. O inglês
    estourava no gText_HowDissapointing do Carvalho (340); a tradução cabe."""
    size = _c_array_size("src/battle_main.c", "gDisplayedStringBattle")
    now = _battle_now()
    sizes = _expansion_bytes(now, env)
    over = [f"{label}: {_expanded_bytes(text, env, sizes)} bytes" for label, text in now.items()
            if _expanded_bytes(text, env, sizes) > size]
    assert over == []
    assert _expanded_bytes(now["gText_HowDissapointing"], env, sizes) > 250   # a medida vê o texto longo


TRAINER_MACROS = {   # macro -> posições (nos argumentos) das falas que vão para a batalha
    "trainerbattle_single": (2,), "trainerbattle_double": (2,), "trainerbattle_rematch": (2,),
    "trainerbattle_rematch_double": (2,), "trainerbattle_no_intro": (1,), "trainerbattle_earlyrival": (2, 3),
}


def _battle_speech_labels() -> set[str]:
    labels = set()
    scripts = list((REPO_ROOT / "data" / "maps").glob("*/scripts.inc")) + list((REPO_ROOT / "data" / "scripts").glob("*.inc"))
    for path in scripts:
        for m in re.finditer(r"^\s*(trainerbattle_\w+)\s+(.*)$", path.read_text(encoding="utf-8"), re.M):
            args = [a.strip() for a in m.group(2).split("@")[0].split(",")]
            for i in TRAINER_MACROS.get(m.group(1), ()):
                if i < len(args):
                    labels.add(args[i])
    return labels


def _inc_texts(sources: dict[str, str]) -> dict[str, str]:
    out = {}
    for rel, source in sources.items():
        for e in ct._extract_inc_text(rel, source):
            if isinstance(e, ct._Entry):
                out[e.label] = e.texts[0]
    return out


def _base_texts(rels: list[str]) -> dict[str, str]:
    """Os arquivos na base inglesa, num só `git cat-file --batch` (arquivo ausente fica de fora)."""
    query = "".join(f"{ct.TRANSLATION_BASE}:{rel}\n" for rel in rels).encode()
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "--batch"], input=query,
                         capture_output=True).stdout
    texts, pos = {}, 0
    for rel in rels:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        pos = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            texts[rel] = out[pos:pos + size].decode("utf-8")
            pos += size + 1
    return texts


def _speech_bytes(text: str, env) -> int:
    """Fala do Treinador em gDisplayedStringBattle: StringExpandPlaceholders ({PLAYER}/{RIVAL} = 7
    letras), mais {PAUSE_UNTIL_PRESS} (BattleStringExpandPlaceholders) e o terminador."""
    total = _nbytes(text, env) + 2 + 1
    for m in re.finditer(r"\{(PLAYER|RIVAL)\}", text):
        total += 7 - env.name_bytes[m.group(1)]
    return total


def test_fala_do_treinador_cabe_em_gDisplayedStringBattle(env):
    """A derrota/vitória do Treinador ({B_TRAINER1_LOSE_TEXT}/{B_TRAINER1_WIN_TEXT}) é copiada inteira
    para gDisplayedStringBattle[300]. A do Brock já passava em inglês: nenhuma pode piorar."""
    if shutil.which("git") is None:
        pytest.skip("sem git")
    size = _c_array_size("src/battle_main.c", "gDisplayedStringBattle")
    labels = _battle_speech_labels()
    files = sorted({f"data/maps/{p.parent.name}/text.inc" for p in (REPO_ROOT / "data" / "maps").glob("*/text.inc")}
                   | {f"data/text/{p.name}" for p in (REPO_ROOT / "data" / "text").glob("*.inc")})
    now = _inc_texts({rel: _read(rel) for rel in files})
    base = _inc_texts(_base_texts(files))
    if not base:
        pytest.skip("sem o commit base da tradução")
    found = labels & set(now)
    assert len(found) > 300, "não achou as falas dos Treinadores"
    over = []
    for label in sorted(found):
        cur, old = _speech_bytes(now[label], env), _speech_bytes(base.get(label, ""), env)
        if cur > size and cur > old:
            over.append(f"{label}: {cur} bytes (inglês {old})")
    assert over == []


# ---- G3: Easy Chat (src/data/easy_chat/, trainer_tower_sets.c, frases fixas) -----------------

EC_DIR = "src/data/easy_chat"
_EC_STR = re.compile(r'static const u8 (sEasyChatWord_\w+)\[\] = _\("((?:[^"\\]|\\.)*)"\);')
_EC_ENT = re.compile(r"\.text = (\w+),\s*\.alphabeticalOrder = (\d+),\s*\.enabled = (\w+)")
# Igual nas duas línguas: pontuação e siglas
EC_UNCHANGED = {"!", "!!", "?!", "?", "…", "…!", "………", "-", "- - -", "PC", "RPG"}
EC_WORD_MAX_BYTES = 12        # trainer_card.c: easyChatProfile[...][13] recebe CopyEasyChatWord
EC_WORD_MAX_PX = 79           # janelas_uso: 2 palavras por linha com {CLEAR 17} na moldura de 24 tiles


def _ec_words(source: str) -> list[tuple[str, str, int, str]]:
    """(variável, texto, alphabeticalOrder, enabled) na ordem do vetor (= índice da palavra)."""
    strings = dict(_EC_STR.findall(source))
    return [(v, strings[v], int(o), e) for v, o, e in _EC_ENT.findall(source)]


def _ec_now(group: str):
    return _ec_words(_read(f"{EC_DIR}/easy_chat_group_{group}.h"))


def _ec_plain(text: str) -> str:
    text = text.replace("{PK}", "PK").replace("{POKEBLOCK}", "POKEBLOCK")
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def ec_sort_key(text: str):
    """Ordem PT-BR do brief: acento conta como a letra base, sem caixa; empate pela grafia."""
    return (_ec_plain(text).casefold(), text)


def ec_letter(text: str) -> str:
    c = _ec_plain(text)[:1].upper()
    return c if "A" <= c <= "Z" else "Others"


def _names(rel: str, prefix: str) -> dict[str, str]:
    return dict(re.findall(rf'\[{prefix}_(\w+)\]\s*=\s*_\("([^"]*)"\)', _read(rel)))


def _move_names():
    return _names("src/data/text/move_names.h", "MOVE")


def _species_names():
    return _names("src/data/text/species_names.h", "SPECIES")


def _value_list_text(source: str, prefix: str) -> list[str]:
    return re.findall(rf"\b{prefix}_(\w+),", source.split("{", 1)[1])


def _value_list(rel: str, prefix: str) -> list[str]:
    return _value_list_text(_read(rel), prefix)


def _ec_constants() -> dict[str, tuple[str, int]]:
    return {name: (grp.lower(), int(idx, 16)) for name, grp, idx in re.findall(
        r"#define (EC_WORD_\w+)\s+\(EC_GROUP_(\w+) << 9\) \| (0x[0-9a-fA-F]+)", _read("include/constants/easy_chat.h"))}


def _ec_text_of() -> dict[str, str]:
    """Constante do Easy Chat (EC_WORD_X, EC_MOVE(X), EC_MOVE2(X), EC_POKEMON(X), EC_POKEMON2(X)) -> texto."""
    words = {g: _ec_now(g) for g in EC_WORD_GROUPS}
    out = {name: words[g][i][1] for name, (g, i) in _ec_constants().items()}
    moves, species = _move_names(), _species_names()
    for m in moves:
        out[f"EC_MOVE({m})"] = out[f"EC_MOVE2({m})"] = moves[m]
    for s in species:
        out[f"EC_POKEMON({s})"] = out[f"EC_POKEMON2({s})"] = species[s]
    return out


def _need_base(rel: str) -> str:
    base = _base_text(rel)
    if base is None:
        pytest.skip("sem git ou sem o commit base da tradução")
    return base


@pytest.mark.parametrize("group", EC_WORD_GROUPS)
def test_toda_palavra_do_easy_chat_foi_traduzida(group):
    before = _ec_words(_need_base(f"{EC_DIR}/easy_chat_group_{group}.h"))
    now = _ec_now(group)
    assert [(v, e) for v, _, _, e in now] == [(v, e) for v, _, _, e in before], "a ordem dos vetores define o id"
    same = [t for (_, t, _, _), (_, old, _, _) in zip(now, before) if t == old and t not in EC_UNCHANGED]
    assert same == []


def test_palavras_do_easy_chat_cabem_na_coluna_e_no_buffer_do_cartao(env):
    assert "easyChatProfile[TRAINER_CARD_PROFILE_LENGTH][13]" in _read("src/trainer_card.c")
    bad = []
    for g in EC_WORD_GROUPS:
        for v, text, _, _ in _ec_now(g):
            m = ct.measure(text, env)
            if m.widest > EC_WORD_MAX_PX or m.nbytes > EC_WORD_MAX_BYTES or m.bad:
                bad.append(f"{g}/{v} '{text}': {m.widest} px, {m.nbytes} bytes {m.bad}")
    assert bad == []


def test_palavras_do_easy_chat_nao_se_repetem():
    """Duas palavras com a mesma grafia confundiriam a lista (acento distingue: "avô"/"avó", "e"/"é")."""
    seen: dict[str, list[str]] = {}
    for g in EC_WORD_GROUPS:
        for v, text, _, _ in _ec_now(g):
            seen.setdefault(text.casefold(), []).append(f"{g}/{v}")
    assert {t: vs for t, vs in seen.items() if len(vs) > 1} == {}


def test_ordem_alfabetica_ptbr_dos_grupos_de_palavras():
    """alphabeticalOrder da entrada i = índice da i-ésima palavra na ordem (easy_chat.c, GetUnlockedWordsInECGroup)."""
    for g in EC_WORD_GROUPS:
        words = _ec_now(g)
        order = [o for _, _, o, _ in words]
        assert sorted(order) == list(range(len(words))), f"{g}: não é permutação"
        shown = [words[o][1] for o in order]
        assert shown == sorted(shown, key=ec_sort_key), g


def test_ordem_alfabetica_ptbr_dos_golpes():
    names = _move_names()
    for n in (1, 2):
        rel = f"{EC_DIR}/easy_chat_group_move_{n}.h"
        now = _value_list(rel, "MOVE")
        assert sorted(now) == sorted(_value_list_text(_need_base(rel), "MOVE")), f"golpes do grupo {n} mudaram"
        assert now == sorted(now, key=lambda m: ec_sort_key(names[m])), n


def _letter_lists() -> dict[str, list[list[str]]]:
    """Letra -> entradas (cada entrada = lista de constantes; o par duplo "-1, 2" vira uma entrada)."""
    src = _read(f"{EC_DIR}/easy_chat_words_by_letter.h")
    lists, counts = {}, {}
    for letter, body in re.findall(r"sEasyChatWordsByLetter_(\w+)\[\] = \{(.*?)\};", src, re.S):
        toks = [t.strip() for t in re.sub(r"//[^\n]*", "", body).split(",") if t.strip()]
        counts[letter] = len(toks)
        entries, i = [], 0
        while i < len(toks):
            if toks[i] == "-1":
                n = int(toks[i + 1])
                entries.append(toks[i + 2:i + 2 + n])
                i += 2 + n
            else:
                entries.append([toks[i]])
                i += 1
        lists[letter] = entries
    declared = dict(re.findall(r"\.words = sEasyChatWordsByLetter_(\w+),\s*\.numWords = (\d+)", src))
    assert {k: int(v) for k, v in declared.items()} == counts, "numWords diferente do tamanho do vetor"
    return lists


def test_listas_por_letra_tem_cada_palavra_uma_vez_na_letra_certa_e_em_ordem():
    lists = _letter_lists()
    assert list(lists) == ["Others"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    text_of = _ec_text_of()
    mons1 = _value_list(f"{EC_DIR}/easy_chat_group_pokemon.h", "SPECIES")
    mons2 = _value_list(f"{EC_DIR}/easy_chat_group_pokemon2.h", "SPECIES")
    expected = set(_ec_constants())
    expected |= {f"EC_MOVE({m})" for m in _value_list(f"{EC_DIR}/easy_chat_group_move_1.h", "MOVE")}
    expected |= {f"EC_MOVE2({m})" for m in _value_list(f"{EC_DIR}/easy_chat_group_move_2.h", "MOVE")}
    expected |= {f"EC_POKEMON({s})" for s in mons1} | {f"EC_POKEMON2({s})" for s in mons2}
    flat = [c for entries in lists.values() for e in entries for c in e]
    assert len(flat) == len(set(flat)), "palavra duplicada nas listas por letra"
    assert set(flat) == expected, (sorted(expected - set(flat))[:10], sorted(set(flat) - expected)[:10])
    for letter, entries in lists.items():
        for e in entries:
            texts = {text_of[c] for c in e}
            assert len(texts) == 1, e                      # par duplo = a mesma espécie nos dois grupos
            if len(e) > 1:
                (sp,) = {re.search(r"\((\w+)\)", c).group(1) for c in e}
                assert e == [f"EC_POKEMON2({sp})", f"EC_POKEMON({sp})"], e
            assert ec_letter(texts.pop()) == letter, (letter, e)
        shown = [text_of[e[0]] for e in entries]
        assert shown == sorted(shown, key=ec_sort_key), letter
    doubled = {re.search(r"\((\w+)\)", e[0]).group(1) for es in lists.values() for e in es if len(e) > 1}
    assert doubled == set(mons1) & set(mons2)


def test_nenhuma_letra_passa_do_limite_da_tela():
    """alphabeticalWordsByGroup[27][N] e allWords[N] (easy_chat.c): uma letra com mais de N palavras estoura."""
    src = _read("src/easy_chat.c")
    limit = int(re.search(r"alphabeticalWordsByGroup\[27\]\[(\d+)\]", src).group(1))
    assert int(re.search(r"u16 allWords\[(\d+)\]", src).group(1)) == limit
    assert {k: len(v) for k, v in _letter_lists().items() if len(v) > limit} == {}


def test_habilidades_e_tipos_do_easy_chat_usam_os_nomes_do_jogo():
    """Grupo "Condição": habilidade = gAbilityNames (Task 2); tipo = forma cheia do glossário (cabe)."""
    abilities = _names("src/data/text/abilities.h", "ABILITY")
    types = {"NORMAL": "Normal", "FIGHTING": "Lutador", "FLYING": "Voador", "POISON": "Venenoso", "GROUND": "Terra",
             "ROCK": "Pedra", "BUG": "Inseto", "GHOST": "Fantasma", "STEEL": "Aço", "FIRE": "Fogo", "WATER": "Água",
             "GRASS": "Planta", "ELECTRIC": "Elétrico", "PSYCHIC": "Psíquico", "ICE": "Gelo", "DRAGON": "Dragão",
             "DARK": "Sombrio"}
    renamed = {"LIGHTNINGROD": "LIGHTNING_ROD", "COMPOUNDEYES": "COMPOUND_EYES"}
    before = _ec_words(_need_base(f"{EC_DIR}/easy_chat_group_status.h"))
    checked, wrong = 0, []
    for (_, en, _, _), (_, pt, _, _) in zip(before, _ec_now("status")):
        want = types.get(en) or abilities.get(renamed.get(en, en.replace(" ", "_")))
        if want is None:
            continue
        checked += 1
        if pt != want:
            wrong.append(f"{en}: '{pt}' (esperado '{want}')")
    assert wrong == []
    assert checked == len(types) + 76            # as 76 habilidades da 3ª geração estão no grupo


def _ec_phrase(tokens: list[str], text_of: dict[str, str]) -> str:
    return " ".join(text_of[t] for t in tokens if t not in ("0xFFFF", "EC_WORD_UNDEFINED"))


def _c_word_array(rel: str, name: str) -> list[str]:
    body = re.search(rf"{name}\[\] = \{{[^\n]*\n(.*?)\}};", _read(rel), re.S).group(1)
    return [t.strip() for t in body.split(",") if t.strip()]


def capitalize_phrase(text: str) -> str:
    """Espelho de CapitalizeEasyChatPhrase (easy_chat.c): maiúscula no início e depois de "!" ou "?"
    ("…" e "-" no começo da frase são pulados)."""
    out, start = [], True
    for ch in text:
        if ch in "!?":
            start = True
        elif ch not in " \n…-" and start:
            ch, start = ch.upper(), False
        out.append(ch)
    return "".join(out)


# Frases e senhas que dependem de palavras do Easy Chat (tabela do relatório da G3)
FIXED_PHRASES = {
    ("src/easy_chat.c", "sDefaultProfileWords"): "eu adoro Pokémon !",
    ("src/easy_chat.c", "sDefaultBattleStartWords"): "ei vamos lutar ! aí vou eu !",
    ("src/easy_chat_2.c", "sECPhrase_MysteryEventIsExciting"): "evento misterioso é emocionante",
    ("src/easy_chat_2.c", "sECPhrase_LinkTogetherWithAll"): "conexão com todos juntos",
}


def test_frases_e_senhas_fixas_existem_em_portugues():
    text_of = _ec_text_of()
    assert {key: _ec_phrase(_c_word_array(*key), text_of) for key in FIXED_PHRASES} == FIXED_PHRASES


def test_senha_do_presente_misterioso_da_e2_usa_palavras_reais():
    """mystery_event_msg.s (E2) cita a senha da pesquisa: “Me dá Treinador incrível” = GIVE_ME, TRAINER, AWESOME."""
    text_of = _ec_text_of()
    words = [text_of[c] for c in ("EC_WORD_GIVE_ME", "EC_WORD_TRAINER", "EC_WORD_AWESOME")]
    assert words == ["me dá", "Treinador", "incrível"]
    src = re.sub(r'"\s*\n\s*\.string\s*"', "", _read("data/mystery_event_msg.s")).replace("\\n", " ")
    assert "“" + capitalize_phrase(" ".join(words)) + "”" in src


def _tower_speeches() -> list[tuple[int, str, list[str]]]:
    return _tower_speeches_of(_read("src/trainer_tower_sets.c"))


def _tower_speeches_of(source: str) -> list[tuple[int, str, list[str]]]:
    out = []
    for n, line in enumerate(source.splitlines(), 1):
        m = re.search(r"\.speech(\w+) = \{([^}]*)\}", line)
        if m and "EC_" in m.group(2):
            out.append((n, m.group(1), [t.strip() for t in m.group(2).split(",")]))
    return out


# Fala da Trainer Tower dirigida ao jogador com gênero marcado ("você é fraco", "meu amigo", "você é um mestre")
TOWER_PLAYER_GENDERED = re.compile(r"\b[Vv]ocê (?:é|foi|está|era) (?:muito |bem |realmente |o |um )?[a-zà-ÿ]\w*o\b|"
                                   r"\b(?:[Mm]eu|[Ss]eu) amigo\b|\b[Vv]ocê é (?:o |um )?(?:mestre|Treinador|adversário)\b")


def test_padrao_de_genero_da_trainer_tower_pega_os_casos_do_ingles_literal():
    caught = ["Você é fabuloso", "Você é fraco demais", "Desculpa meu amigo", "Você é um mestre Treinador",
              "Você está pronto ?", "Você foi perfeito"]
    clean = ["Você é forte demais", "Você é legal !", "Você é só uma criança ahaha !", "Você é moleza !",
             "Eu sou Positivo você é Negativo"]   # nome de habilidade, entre o casal
    assert [t for t in caught if not TOWER_PLAYER_GENDERED.search(t)] == []
    assert [t for t in clean if TOWER_PLAYER_GENDERED.search(t)] == []


# Emendas que a tradução palavra a palavra da frase inglesa produz ("I AM SORRY" -> "eu sou desculpa",
# "YOU'RE NOT GOING" -> "você é não indo", "WE WON" -> "nós venci", "ARE YOU" -> "está você")
TOWER_LITERAL = re.compile(r"(?i)\b(?:eu sou desculpa|você é não|é não indo|nós venci|eu precisar|eu querer|"
                           r"eu ter|está você|eu sou derrotar|eram meu|sensação trêmulo|um pouco moleza)\b")


def test_falas_da_trainer_tower_em_portugues_e_sem_genero_do_jogador(env):
    text_of = _ec_text_of()
    speeches = _tower_speeches()
    assert len(speeches) == 240
    base = {n: toks for n, _, toks in _tower_speeches_of(_need_base("src/trainer_tower_sets.c"))}
    rewritten = sum(1 for n, _, toks in speeches if base.get(n) != toks)
    assert rewritten >= 200, "as falas têm de ser refeitas na ordem do português, não só trocadas palavra a palavra"
    as_english = [capitalize_phrase(_ec_phrase(toks, text_of)) for toks in base.values()]
    assert sum(1 for p in as_english if TOWER_LITERAL.search(p)) >= 10   # o padrão pega a versão literal
    bad, literal = [], []
    for n, kind, toks in speeches:
        assert len(toks) == 6, n
        words = [t for t in toks if t != "0xFFFF"]
        assert all(t in text_of for t in words), (n, [t for t in words if t not in text_of])
        phrase = capitalize_phrase(_ec_phrase(toks, text_of))
        if TOWER_PLAYER_GENDERED.search(phrase):
            bad.append(f"{n} {kind}: {phrase}")
        if TOWER_LITERAL.search(phrase):
            literal.append(f"{n}: {phrase}")
        # TT_ConvertEasyChatMessageToString: 3x2 se couber em 196 px; senão 2x3 (2 palavras por linha)
        rows3 = [" ".join(text_of[t] for t in toks[i:i + 3] if t != "0xFFFF") for i in (0, 3)]
        rows2 = [" ".join(text_of[t] for t in toks[i:i + 2] if t != "0xFFFF") for i in (0, 2, 4)]
        if max(ct.measure(r, env).widest for r in rows3) > 196:
            assert max(ct.measure(r, env).widest for r in rows2) <= 196, (n, rows2)
    assert bad == []
    assert literal == []


def test_maiuscula_das_frases_cobre_os_acentos_do_charmap():
    """A tabela de CapitalizeEasyChatPhrase leva cada minúscula acentuada à sua maiúscula (pelo charmap)
    e cobre toda letra acentuada que começa uma palavra do Easy Chat."""
    charmap = {}
    for ch, code in re.findall(r"^'(.)'\s*=\s*([0-9A-F]{2})\s*$", _read("charmap.txt"), re.M):
        charmap.setdefault(int(code, 16), ch)
    defines = {k: int(v, 16) for k, v in re.findall(r"#define (CHAR_\w+)\s+(0x[0-9A-Fa-f]+)",
                                                     _read("include/characters.h"))}
    src = _read("src/easy_chat.c")
    table = re.search(r"sLowerToUpperAccented\[\]\[2\] = \{(.*?)\n\};", src, re.S).group(1)
    pairs = [tuple(defines[x] if x in defines else int(x, 16) for x in p)
             for p in re.findall(r"\{(\w+), (\w+)\}", table)]
    got = {charmap[a]: charmap[b] for a, b in pairs}
    assert all(lo.upper() == up for lo, up in got.items()), got
    first = {t[:1] for g in EC_WORD_GROUPS for _, t, _, _ in _ec_now(g)}
    assert {c for c in first if c.islower() and not c.isascii()} <= set(got)
    assert "ShowFieldAutoScrollMessage(CapitalizeEasyChatPhrase(gStringVar4));" in src
    assert _read("src/trainer_tower.c").count("CapitalizeEasyChatPhrase(dest)") == 2


def test_termos_novos_do_easy_chat_no_glossario():
    g = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    created = {t["pt"] for t in g["termos"] if t.get("frente") == "G3"}
    assert {"T. Batalha", "Sala Batalha", "Base Secreta", "Pokébloco", "Pokérus", "Loja Depart.", "Fita",
            "KO direto!"} <= created


# Caixa das palavras que são termos do glossário (fix 1 da G3). Regra: a palavra segue a caixa que o termo tem
# no meio da frase nos textos já traduzidos ("Ovo" 22×0, "Bolsa" 25×4, "Líder" 16×2; "tipo" 0×80, "nome" 0×25).
# Termo criado pela G3 sem ocorrência no texto usa a caixa do glossário ("Fita", "Base Secreta", "Loja Depart.");
# "Torneio" é conferido à parte. Rótulos de menu (Sim, Não, Usar…) aparecem em minúscula no texto: ficam assim.
# Itens e habilidades ficam fora: são nomes próprios ("Pegar" é habilidade; "reviver" é verbo, não o item Reviver).
EC_TERM_CATEGORIES = ("interface", "batalha", "personagem", "lugar")
# BALL (Passatempos) é a bola comum; "Bola" com maiúscula no texto é a Poké Bola abreviada
EC_CASE_OTHER_MEANING = {"bola"}


def _running_text() -> str:
    files = [p for p in (REPO_ROOT / "data").rglob("*.inc")] + [REPO_ROOT / "src/strings.c", REPO_ROOT / BATTLE]
    return "\n".join(p.read_text(encoding="utf-8") for p in files)


def _mid_sentence(text: str, word: str) -> int:
    """Ocorrências depois de uma palavra minúscula e fora de nome composto ("Poké Bola", "Ultra Bola", "Bola Mestra")."""
    return len(re.findall(rf"(?<![\wà-úÀ-Ú.'-])[a-zà-ú][a-zà-ú]*,? {re.escape(word)}(?![\wà-ú])(?! [A-ZÀ-Ú])", text))


def test_capitalizacao_espelho_pula_reticencias_e_traco():
    assert capitalize_phrase("… quem é você ?") == "… Quem é você ?"
    assert capitalize_phrase("- - - ei ! ahaha") == "- - - Ei ! Ahaha"
    assert capitalize_phrase("iiih !! desculpa") == "Iiih !! Desculpa"


def test_palavra_que_e_termo_do_glossario_tem_a_caixa_do_termo():
    g = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    terms: dict[str, set[str]] = {}
    created = {t["pt"] for t in g["termos"] if t.get("frente") == "G3"}
    for t in g["termos"]:
        if t["categoria"] in EC_TERM_CATEGORIES and " " not in t["pt"].strip(". ") or t["pt"] in created:
            terms.setdefault(t["pt"].casefold(), set()).add(t["pt"])
    text = _running_text()
    wrong, checked = [], 0
    for grp in EC_WORD_GROUPS:
        if grp == "status":
            continue                                   # tipos e habilidades: test_habilidades_e_tipos_...
        for v, word, _, _ in _ec_now(grp):
            glossary = terms.get(word.casefold())
            if not glossary or word in EC_CASE_OTHER_MEANING:
                continue
            checked += 1
            up, lo = word[:1].upper() + word[1:], word[:1].lower() + word[1:]
            n_up, n_lo = _mid_sentence(text, up), _mid_sentence(text, lo)
            if n_up + n_lo:
                want = up if n_up > n_lo else lo
            elif glossary & created:
                want = sorted(glossary & created)[0]
            else:
                continue                               # sem uso no texto: qualquer caixa
            if word != want:
                wrong.append(f"{grp}/{v} '{word}': esperado '{want}' (meio da frase {n_up}×{n_lo}, glossário {glossary})")
    assert checked > 20
    assert wrong == [], wrong
    text_of = _ec_text_of()
    assert [text_of[c] for c in ("EC_WORD_EGG", "EC_WORD_BAG", "EC_WORD_MAIL", "EC_WORD_CONTEST")] == \
        ["Ovo", "Bolsa", "Carta", "Torneio"]


def test_maiuscula_tambem_na_mensagem_do_treinador_do_ereader():
    src = _read("src/battle_tower.c")
    body = re.search(r"static void BufferBattleTowerTrainerMessage\(.*?\n\}", src, re.S).group(0)
    assert "CapitalizeEasyChatPhrase(gStringVar4);" in body
