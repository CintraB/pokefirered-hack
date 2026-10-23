"""Frente G da tradução (itens, batalha e listas).

Task G1: descrições de item (`items.json`), frutas (`berry.c`) e enfeites (`decoration/`).
Task G2: mensagens de batalha (`src/battle_message.c`), com a gramática montada no código
(o lado do Pokémon vira sufixo: "o Rattata selvagem", "do Pidgey inimigo").
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
G2_FILES = ("src/battle_message.c",)
FILES = G1_FILES + G2_FILES

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
