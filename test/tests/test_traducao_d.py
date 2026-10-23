"""Frente D da tradução (textos longos): os rótulos já traduzidos não têm inglês nem achado das
regras de texto da esteira (`controle`, `glossario`, largura, linhas, charmap, terminador).

Cada task da frente acrescenta a sua faixa em `TRANSLATED`: arquivo -> (primeiro rótulo, primeiro
rótulo que NÃO é da faixa ou None para ir até o fim do arquivo). A ajuda (`data/text/help_system.inc`)
foi traduzida pela D1 (do início até `Help_Text_HowToUseFight`) e pela D2 (o resto): agora é o arquivo
inteiro. Os rótulos de menu citados entre aspas na ajuda são conferidos contra o `src/strings.c`
(Rulings 17 e 21).
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

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="precisa do git")

HELP_FILE = "data/text/help_system.inc"

# arquivo -> [(primeiro rótulo, primeiro rótulo fora da faixa | None)]
TRANSLATED: dict[str, list[tuple[str, str | None]]] = {
    # D1 + D2: ajuda do jogo inteira
    HELP_FILE: [("Help_Text_WhatShouldIDo", None)],
}

# Japonês deixado como está no original (a ajuda tem uma linha de "faça por conta própria")
JAPANESE_LABELS = {HELP_FILE: {"Help_Text_TryDoingItOnYourOwn"}}

# Rótulos que, por serem sigla ou nome igual nas duas línguas, ficam idênticos ao inglês
SAME_AS_ENGLISH = {
    "Help_Text_PP": "sigla PP mantida (glossário)",
}

# "TO" = Treinador Original (glossário: OT -> TO) é a sigla em português, mas "to" está na lista de
# palavras inglesas da checagem. Exceção só vale se o único achado do rótulo for a sigla em maiúsculas.
TO_LABELS = {"Help_Text_OT", "Help_Text_DefineOT", "Help_Text_DefineIDNo", "Help_Text_DefineIDNo2"}

_LABEL = re.compile(r"^(\w+)::", re.M)
_BREAK = re.compile(r"\\[nlp]")
HELP_SPACE_PX = 4
HELP_ONE_LINE_PX = 200      # lista em x = 8 num bitmap de 208 px (src/help_system_util.c:722-724)


def _labels(rel: str) -> set[str]:
    source = (REPO_ROOT / rel).read_text(encoding="utf-8")
    names = _LABEL.findall(source)
    wanted: set[str] = set()
    for first, stop in TRANSLATED[rel]:
        start = names.index(first)
        end = names.index(stop) if stop is not None else len(names)
        wanted.update(names[start:end])
    return wanted


@lru_cache(maxsize=1)
def _entries() -> tuple:
    return tuple(e for e in ct._sources(REPO_ROOT) if isinstance(e, ct._Entry))


@lru_cache(maxsize=1)
def _allowed() -> frozenset:
    return frozenset(ct._english_allowed_names(list(_entries())))


def _english_left(entry) -> list[str]:
    """Palavras inglesas do rótulo, menos a sigla TO (Treinador Original) em maiúsculas."""
    words = ct._english_words(entry, set(_allowed()))
    if entry.label in TO_LABELS and words and set(words) == {"to"}:
        plain = ct._plain_words(entry.texts[0])
        if all(w == "TO" for w in plain if w.lower() == "to"):
            return []
    return words


@lru_cache(maxsize=1)
def _failures() -> tuple:
    """Todas as falhas da checagem de texto com o inglês bloqueante (sem exceções congeladas)."""
    results = ct.check_text(str(REPO_ROOT), {"text": []}, english="bloqueante")
    # sem a base inglesa as regras controle/glossario não rodam: o teste não pode passar calado
    assert not [r.detail for r in results if "base inglesa indisponível" in r.detail], \
        "base inglesa indisponível: controle/glossario não rodaram"
    return tuple(r for r in results if r.status == "falha")


def _own(rel: str) -> list:
    labels = _labels(rel) - JAPANESE_LABELS.get(rel, set())
    by_label = {e.label: e for e in _entries() if e.file == rel}
    own = []
    for result in _failures():
        m = re.match(rf"{re.escape(rel)}: (\w+): ", result.detail)
        if not m or m.group(1) not in labels:
            continue
        if result.name == "texto/ingles" and not _english_left(by_label[m.group(1)]):
            continue            # só a sigla TO
        own.append(result)
    return own


@pytest.mark.parametrize("rel", sorted(TRANSLATED))
def test_faixa_traduzida_sem_achados(rel):
    """Nenhum achado (largura, linhas, charmap, terminador, controle, glossário) nem inglês."""
    assert [f"{r.name}: {r.detail}" for r in _own(rel)] == []


@pytest.mark.parametrize("rel", sorted(TRANSLATED))
def test_faixa_nao_tem_mais_ingles(rel):
    labels = _labels(rel) - JAPANESE_LABELS.get(rel, set())
    left = {e.label: _english_left(e) for e in _entries() if e.file == rel and e.label in labels}
    assert {label: words for label, words in left.items() if words} == {}


def test_excecao_do_to_continua_sendo_so_a_sigla():
    """A única exceção do relatório de inglês é a sigla TO (Treinador Original), em maiúsculas."""
    flagged = {}
    for e in _entries():
        if e.file != HELP_FILE:
            continue
        raw = ct._english_words(e, set(_allowed()))
        if raw and not _english_left(e):
            flagged[e.label] = raw
    assert set(flagged) == TO_LABELS
    for label in TO_LABELS:
        entry = next(e for e in _entries() if e.file == HELP_FILE and e.label == label)
        assert [w for w in ct._plain_words(entry.texts[0]) if w.lower() in ct.ENGLISH_WORDS] == \
            ["TO"] * len(flagged[label])


def test_ajuda_perguntas_e_titulos_em_uma_linha_de_200_px():
    """Itens de lista e títulos da ajuda (tabelas de src/help_system.c): 1 linha só (sem \\n) e até 200 px."""
    list_labels = set(ct._HELP_LIST_LABELS) - JAPANESE_LABELS[HELP_FILE]
    assert len(list_labels) > 150, len(list_labels)          # a lista de rótulos das tabelas não encolheu
    env = ct._load_env(REPO_ROOT)
    checked, problems = 0, []
    for e in _entries():
        if e.file != HELP_FILE or e.label not in list_labels or e.label not in _labels(HELP_FILE):
            continue
        checked += 1
        text = "".join(e.texts)
        if len(e.texts) != 1 or _BREAK.search(text):
            problems.append(f"{e.label}: mais de uma linha")
            continue
        width = ct.measure(text, env, "normal", HELP_SPACE_PX).widest
        if width > HELP_ONE_LINE_PX:
            problems.append(f"{e.label}: {width} px > {HELP_ONE_LINE_PX}")
    assert checked > 150, checked
    assert problems == []


@lru_cache(maxsize=1)
def _base_text() -> str | None:
    """A ajuda na base inglesa (git show do commit base da tradução); None se a base não existe."""
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{HELP_FILE}"],
                         capture_output=True)
    return out.stdout.decode("utf-8") if out.returncode == 0 else None


@lru_cache(maxsize=1)
def _base_entries() -> dict:
    """Rótulo -> textos da ajuda na base inglesa."""
    base = _base_text()
    assert base is not None, "base inglesa indisponível: git show da ajuda falhou"
    kind = dict(ct._source_files(REPO_ROOT))[HELP_FILE]
    return {e.label: e.texts for e in ct._extract(HELP_FILE, kind, base) if isinstance(e, ct._Entry)}


def test_ajuda_inteira_nenhum_rotulo_identico_ao_ingles():
    """Todos os rótulos da ajuda mudaram em relação à base inglesa (menos o japonês e a sigla PP)."""
    base = _base_entries()
    labels = _labels(HELP_FILE) - JAPANESE_LABELS[HELP_FILE]
    by_label = {e.label: e for e in _entries() if e.file == HELP_FILE}
    assert len(labels) > 350, len(labels)       # D1 + D2: a ajuda inteira (368 rótulos, sem o japonês)
    assert sorted(labels - set(base)) == []     # todo rótulo existe na base
    unchanged = [label for label in sorted(labels)
                 if base[label] == by_label[label].texts and label not in SAME_AS_ENGLISH]
    assert unchanged == []
    # os rótulos que ficam iguais ao inglês são só os justificados em SAME_AS_ENGLISH
    assert [label for label in SAME_AS_ENGLISH if base[label] != by_label[label].texts] == []


def test_rotulos_da_ajuda_iguais_aos_da_base():
    base = _base_text()
    if base is None:
        pytest.skip("sem o commit base da tradução")
    assert _LABEL.findall((REPO_ROOT / HELP_FILE).read_text(encoding="utf-8")) == _LABEL.findall(base)


def test_fim_de_arquivo_da_ajuda_igual_ao_da_base():
    base = _base_text()
    if base is None:
        pytest.skip("sem o commit base da tradução")
    now = (REPO_ROOT / HELP_FILE).read_text(encoding="utf-8")
    assert len(now) - len(now.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


# ---- rótulos de menu citados na ajuda x src/strings.c (Rulings 17 e 21) ---------------------------

# rótulo na ajuda -> [(arquivo, símbolo, modo)]; modo "=" (o texto é o rótulo) ou "in" (o rótulo está no texto)
MENU_LABELS: dict[str, list[tuple[str, str, str]]] = {
    "Pokédex": [("src/strings.c", "gText_MenuPokedex", "=")],
    "Pokémon": [("src/strings.c", "gText_MenuPokemon", "=")],
    "Bolsa": [("src/strings.c", "gText_MenuBag", "=")],
    "{PLAYER}": [("src/strings.c", "gText_MenuPlayer", "=")],
    "Salvar": [("src/strings.c", "gText_MenuSave", "=")],
    "Opções": [("src/strings.c", "gText_MenuOption", "="), ("src/strings.c", "gText_Option", "=")],
    "Desistir": [("src/strings.c", "gText_MenuRetire", "=")],
    "Resumo": [("src/strings.c", "gText_Summary5", "="), ("src/strings.c", "gPCText_Summary", "=")],
    "Trocar": [("src/strings.c", "gText_Shift", "="), ("src/strings.c", "gText_Switch2", "="),
               ("src/strings.c", "gPCText_Shift", "=")],       # SHIFT/SWITCH do menu da equipe (Ruling 21)
    "Item": [("src/strings.c", "gText_Item", "=")],
    "Dar": [("src/strings.c", "gOtherText_Give", "=")],
    "Pegar": [("src/strings.c", "gText_Take", "=")],
    "Usar": [("src/strings.c", "gOtherText_Use", "=")],
    "Registrar": [("src/strings.c", "gOtherText_Register", "=")],
    "Abrir": [("src/strings.c", "gOtherText_Open", "=")],
    "Sim": [("src/strings.c", "gText_Yes", "=")],
    "Cancelar": [("src/strings.c", "gText_OptionMenuCancel", "=")],
    "OK": [("src/strings.c", "gText_PartyMenu_OK", "="), ("src/strings.c", "gText_OK", "=")],
    "Itens": [("src/strings.c", "gText_Items2", "=")],
    "Itens-chave": [("src/strings.c", "gText_KeyItems2", "=")],
    "Poké Bolas": [("src/strings.c", "gText_PokeBalls2", "=")],
    "Dados": [("src/strings.c", "gText_PokeSum_PageName_PokemonInfo", "=")],
    "Atributos": [("src/strings.c", "gText_PokeSum_PageName_PokemonSkills", "=")],
    "Golpes": [("src/strings.c", "gText_PokeSum_PageName_KnownMoves", "=")],
    "Lista de Pokémon": [("src/strings.c", "gText_PokemonListNoColor", "=")],
    "Habitats Pokémon": [("src/strings.c", "gText_PokemonHabitats", "=")],
    "Busca": [("src/strings.c", "gText_SearchNoColor", "="), ("src/strings.c", "gText_Search", "=")],
    "Área": [("src/strings.c", "gText_Area", "=")],
    "Mais dados": [("src/strings.c", "gText_NextDataCancel", "in")],
    "Depósito de Itens": [("src/strings.c", "gText_ItemStorage", "=")],
    "Caixa de Cartas": [("src/strings.c", "gText_Mailbox", "=")],
    "Retirar item": [("src/strings.c", "gText_WithdrawItem2", "=")],
    "Guardar item": [("src/strings.c", "gText_DepositItem2", "=")],
    "Retirar": [("src/strings.c", "gPCText_Withdraw", "="), ("src/strings.c", "gText_Withdraw", "=")],
    "Guardar": [("src/strings.c", "gPCText_Store", "="), ("src/strings.c", "gText_Store", "=")],
    "Mover": [("src/strings.c", "gPCText_Move", "=")],
    "PC de {PLAYER}": [("src/strings.c", "gText_SPc", "=")],
    "PC Prof. Carvalho": [("src/strings.c", "gText_ProfOakSPc", "=")],
    "Hall da Fama": [("src/strings.c", "gText_HallOfFame", "=")],
    "Troca": [("src/strings.c", "gText_BattleStyleShift", "=")],       # BATTLE STYLE: SHIFT
    "Ajuda": [("src/strings.c", "gText_ButtonTypeHelp", "=")],
    "LR": [("src/strings.c", "gText_ButtonTypeLR", "=")],
    "L=A": [("src/strings.c", "gText_ButtonTypeLEqualsA", "=")],
}
# "{STR_VAR_1}" é o PC do Bill / de alguém (placeholder da ajuda): ver o teste do placeholder abaixo.
PLACEHOLDER_LABELS = {"{STR_VAR_1}"}

# Rótulos do menu de batalha: battle_message.c ainda está em inglês na base (frente da batalha); até lá
# valem os termos do glossário (FIGHT = Lutar, RUN = Fugir, BALL do Safári = Bola, BAIT = Isca, ROCK = tipo Pedra).
BATTLE_LABELS = {"Lutar": ("FIGHT", "Lutar"), "Fugir": ("RUN", "Fugir"), "Bola": ("BALL (menu do Safári)", "Bola"),
                 "Isca": ("BAIT", "Isca"), "Pedra": ("ROCK", "Pedra")}

# Aspas que não são rótulo de menu: itens e termos citados, texto de placa, definição de sigla
OTHER_QUOTES = {
    "Poção": "nome de item (Poção)",
    "Bicicleta": "nome de item (Bicicleta)",
    "Mapa da Cidade": "nome de item (forma cheia, glossário)",
    "P.C": "placa do Centro Pokémon (texto do mapa)",
    "MART": "placa do Poké Mart (texto do mapa)",
    "Treinador Original": "definição da sigla TO",
    "desmaiado": "definição da sigla DES",
    "Pontos de Poder": "definição da sigla PP",
    "Pontos de Experiência": "definição da sigla PE",
    "Natureza": "termo da Natureza do Pokémon",
    "Como faço isto?": "título do tópico de ajuda (Help_Text_HowDoIDoThis)",
}

_QUOTED = re.compile(r"“([^”]*)”")
_CONTROL_PREFIX = re.compile(r"^(?:\{(?:COLOR|SHADOW|HIGHLIGHT|COLOR_HIGHLIGHT_SHADOW|PALETTE)\b[^}]*\})+")


def _help_text() -> str:
    return "".join(re.findall(r'\.string "(.*)"', (REPO_ROOT / HELP_FILE).read_text(encoding="utf-8")))


@lru_cache(maxsize=None)
def _c_string(rel: str, symbol: str) -> str:
    source = (REPO_ROOT / rel).read_text(encoding="utf-8")
    m = re.search(rf'\b{re.escape(symbol)}\[\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', source)
    assert m, f"{rel}: {symbol} não encontrado"
    return m.group(1)


def test_todo_rotulo_citado_na_ajuda_esta_classificado():
    """Cada texto entre aspas “...” da ajuda é rótulo de menu conferido, rótulo de batalha ou citação conhecida."""
    known = set(MENU_LABELS) | PLACEHOLDER_LABELS | set(BATTLE_LABELS) | set(OTHER_QUOTES)
    # a citação pode atravessar uma quebra de linha ("tópico “Como faço\nisto?”")
    quoted = {_BREAK.sub(" ", q) for q in _QUOTED.findall(_help_text())}
    assert sorted(quoted - known) == []
    # nada na lista fica sem uso (a lista de conferência não envelhece em silêncio)
    assert sorted(known - quoted) == []


@pytest.mark.parametrize("label", sorted(MENU_LABELS))
def test_rotulo_de_menu_da_ajuda_bate_com_o_strings_c(label):
    for rel, symbol, mode in MENU_LABELS[label]:
        value = _CONTROL_PREFIX.sub("", _c_string(rel, symbol))
        if mode == "=":
            assert value == label, f"{symbol}: {value!r} != {label!r}"
        else:
            assert label in value, f"{symbol}: {label!r} não está em {value!r}"


def test_o_rotulo_do_pc_do_bill_vem_do_strings_c():
    """“{STR_VAR_1}” da ajuda desenha o PC do Bill / de alguém: a ajuda usa os mesmos rótulos do menu do PC."""
    util = (REPO_ROOT / "src/help_system_util.c").read_text(encoding="utf-8")
    assert "gText_BillSPc[i]" in util and "gText_SomeoneSPc[i]" in util
    assert "gString_Bill[i]" not in util and "gString_Someone[i]" not in util
    # a esteira mede {STR_VAR_1} como 10 letras largas (60 px); "PC de alguém" mede 67 px: as linhas que
    # levam o placeholder têm de caber com cada um dos dois textos de verdade
    env = ct._load_env(REPO_ROOT)
    text = (REPO_ROOT / HELP_FILE).read_text(encoding="utf-8")
    used = 0
    for label, limit in (("Help_Text_UsingBillsPC", HELP_ONE_LINE_PX), ("Help_Text_HowToUseBillsPC", 208)):
        m = re.search(rf'^{label}::\n((?:\t\.string ".*"\n)+)', text, re.M)
        raw = "".join(re.findall(r'\.string "(.*)"', m.group(1))).rstrip("$")
        assert "{STR_VAR_1}" in raw
        for symbol in ("gText_BillSPc", "gText_SomeoneSPc"):
            real = _c_string("src/strings.c", symbol)
            assert real.startswith("PC ")
            for line in _BREAK.split(raw.replace("{STR_VAR_1}", real)):
                width = ct.measure(line, env, "normal", HELP_SPACE_PX).widest
                assert width <= limit, (label, symbol, line, width)
                used += 1
    assert used >= 8


def test_rotulos_de_batalha_da_ajuda_seguem_o_glossario():
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    terms = {(t["en"], t["pt"]) for t in data["termos"]}
    for label, (en, pt) in BATTLE_LABELS.items():
        assert label == pt
        assert (en, pt) in terms, (en, pt)


def test_rotulos_de_batalha_batem_com_battle_message_quando_traduzido():
    """Cada menu (batalha e Safári) é conferido assim que for traduzido; skip só enquanto os dois estão em inglês."""
    source = (REPO_ROOT / "src/battle_message.c").read_text(encoding="utf-8")
    menu = re.search(r'gText_BattleMenu\[\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', source).group(1)
    safari = re.search(r'gText_SafariZoneMenu\[\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', source).group(1)
    menu_pending, safari_pending = "FIGHT" in menu, "BAIT" in safari
    if menu_pending and safari_pending:
        pytest.skip("battle_message.c ainda em inglês na base (frente da batalha): rótulos do glossário")
    if not menu_pending:
        assert "Lutar" in menu and "Fugir" in menu
    if not safari_pending:
        for label in ("Bola", "Isca", "Pedra", "Fugir"):
            assert label in safari


def test_ajuda_nao_usa_rotulos_antigos():
    text = _help_text()
    for stale in ("Entrar", "Habitats dos Pokémon", "Buscar", "Retirar Item", "Guardar Item", "“Abra”",
                  "PC do Prof. Carvalho", "PC de {STR_VAR_1}"):
        assert stale not in text, stale


# ---- regras de 20/10: jogador sem gênero, nomes não partidos, placeholders a 10 letras ------------

PLAYER_GENDERED = ("Bem-vindo", "Bem-vinda", "obrigado", "obrigada", "sozinho", "sozinha", "pronto,", "avisado",
                   "ocupado", "cansado", "protagonista", "personagem principal", "Fique quieto")
WRONG_FORMS = ("Atq.Esp.", "Def.Esp.", "Entrar", "Vermelho e Verde")


def test_ajuda_sem_genero_do_jogador_e_formas_erradas():
    body = _help_text()
    for bad in PLAYER_GENDERED + WRONG_FORMS:
        assert bad not in body, bad


def _multiword_terms() -> list[str]:
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    names = {t["pt"] for t in data["termos"] if " " in t["pt"] and "{" not in t["pt"]}
    names |= {"Centro Pokémon", "Poké Mart", "Poké Bola", "Zona de Safári", "Bola Safári", "Caixa de Cartas",
              "Adaptador Sem Fio", "Hall da Fama", "Mapa da Cidade", "Liga Pokémon", "Depósito de Itens",
              "Estojo de MT", "Cartão de Treinador", "Jogo do Safári", "Prof. Carvalho", "PC Prof. Carvalho",
              "Tabela de tipos", "Habitats Pokémon", "Lista de Pokémon", "Retirar item", "Guardar item",
              "Mais dados", "Pontos de Experiência", "Pontos de Poder", "Treinador Original", "Golpe oculto"}
    plurals = set()
    for name in names:
        words = name.split(" ")
        for j, w in enumerate(words):
            if w[-1:].isalpha() and not w.endswith("s"):
                plurals.add(" ".join(words[:j] + [w + "s"] + words[j + 1:]))
    return sorted(names | plurals)


def test_nomes_nao_sao_partidos_na_quebra_da_ajuda():
    body = _help_text()
    found = []
    for name in _multiword_terms():
        for i, ch in enumerate(name):
            if ch != " ":
                continue
            for br in ("\\n", "\\l", "\\p"):
                # quebra no lugar do espaço, com ou sem o recuo de lista de 3 espaços da linha seguinte
                for indent in ("", "   "):
                    if name[:i] + br + indent + name[i + 1:] in body:
                        found.append(name)
    assert sorted(set(found)) == []


VARIABLE_PLACEHOLDER = re.compile(r"\{(?:STR_VAR_\d|B_BUFF\d|B_COPY_VAR_\d)\}")


def test_linhas_da_ajuda_com_placeholder_variavel_cabem_com_10_letras_largas():
    env = ct._load_env(REPO_ROOT)
    text = (REPO_ROOT / HELP_FILE).read_text(encoding="utf-8")
    too_wide, seen = [], 0
    for m in re.finditer(r'^(\w+)::\n((?:[ \t]+\.string ".*"\n?)+)', text, re.M):
        raw = "".join(re.findall(r'\.string "(.*)"', m.group(2)))
        if not VARIABLE_PLACEHOLDER.search(raw):
            continue
        seen += 1
        for line in _BREAK.split(VARIABLE_PLACEHOLDER.sub("MMMMMMMMMM", raw).rstrip("$")):
            width = ct.measure(line, env, "normal", HELP_SPACE_PX).widest
            if width > 208:
                too_wide.append(f"{m.group(1)}: {width} px")
    assert seen >= 2, seen          # "{STR_VAR_1}" aparece em 2 rótulos da ajuda
    assert too_wide == []
