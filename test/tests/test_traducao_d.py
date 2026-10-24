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
FAME_FILE = "data/text/fame_checker.inc"
TRAINERS_FILE = "data/text/trainers.inc"

# arquivo -> [(primeiro rótulo, primeiro rótulo fora da faixa | None)]
TRANSLATED: dict[str, list[tuple[str, str | None]]] = {
    # D1 + D2: ajuda do jogo inteira
    HELP_FILE: [("Help_Text_WhatShouldIDo", None)],
    # D3: Arquivo Fama (textos, nomes, cartas, etiquetas, Jornal Pokémon) e falas de revanche / Explorador VS
    FAME_FILE: [("gFameCheckerFlavorText_ProfOak0", None)],
    TRAINERS_FILE: [("VSSeeker_Text_BatteryNotChargedNeedXSteps", None)],
}

# Japonês deixado como está no original (a ajuda tem uma linha de "faça por conta própria"; o Careca
# da Rota 21 tem uma fala de revanche japonesa sem uso)
JAPANESE_LABELS = {HELP_FILE: {"Help_Text_TryDoingItOnYourOwn"},
                   TRAINERS_FILE: {"Route21_North_Text_CueBallRematchIntro"}}

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
    """A única exceção do relatório de inglês é a sigla TO (Treinador Original), em maiúsculas. Desde a B3 é a
    própria regra (`check_text._english_words`) que a ignora: nos 4 rótulos da ajuda a lista de palavras
    inglesas do texto só tem "TO" e o relatório não acusa nada."""
    for label in TO_LABELS:
        entry = next(e for e in _entries() if e.file == HELP_FILE and e.label == label)
        in_list = [w for w in ct._plain_words(entry.texts[0]) if w.lower() in ct.ENGLISH_WORDS]
        assert in_list and set(in_list) == {"TO"}, label
        assert ct._english_words(entry, set(_allowed())) == [], label


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


# ======== D3: Arquivo Fama, falas de revanche / Explorador VS e a classe "Executivo" =================

D3_FILES = (FAME_FILE, TRAINERS_FILE)
_BREAK_RAW = re.compile(r"\\[nlp]")


def _blocks(rel: str, source: str | None = None) -> dict[str, str]:
    """Rótulo -> texto cru (as linhas `.string` juntas, com `\\n`/`\\l`/`\\p` e os códigos de controle)."""
    source = (REPO_ROOT / rel).read_text(encoding="utf-8") if source is None else source
    out: dict[str, str] = {}
    cur = None
    for line in source.split("\n"):
        m = re.match(r"^(\w+)::", line)
        if m:
            cur = m.group(1)
            out[cur] = ""
            continue
        m = re.match(r'^\s*\.string "(.*)"\s*$', line)
        if m and cur:
            out[cur] += m.group(1)
    return out


@lru_cache(maxsize=None)
def _base_source(rel: str) -> str | None:
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    return out.stdout.decode("utf-8") if out.returncode == 0 else None


def _plain(text: str) -> str:
    """Texto sem códigos de controle e com as quebras viradas em espaço (para comparar e para os padrões)."""
    text = re.sub(r"\{[^}]*\}", "", text)
    return re.sub(r"\s+", " ", _BREAK_RAW.sub(" ", text.replace("$", ""))).strip()


def _flat_plain(rel: str) -> str:
    return " ".join(_plain(t) for t in _blocks(rel).values())


@pytest.mark.parametrize("rel", D3_FILES)
def test_d3_rotulos_e_fim_de_arquivo_iguais_aos_da_base(rel):
    base = _base_source(rel)
    if base is None:
        pytest.skip("sem o commit base da tradução")
    now = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert _LABEL.findall(now) == _LABEL.findall(base)
    assert len(now) - len(now.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


@pytest.mark.parametrize("rel", D3_FILES)
def test_d3_todo_texto_mudou_em_relacao_ao_ingles(rel):
    """Só ficam iguais ao inglês o japonês sem uso e o rótulo que é só o nome do rival ({RIVAL})."""
    base = _base_source(rel)
    if base is None:
        pytest.skip("sem o commit base da tradução")
    old, new = _blocks(rel, base), _blocks(rel)
    assert set(old) == set(new)
    same = {label for label in new if new[label] == old[label]}
    allowed = JAPANESE_LABELS.get(rel, set())
    if rel == FAME_FILE:
        allowed = allowed | {"gFameCheckerFlavorTextOriginObjectName_Bill0"}
    assert same == allowed


# Jogador sem gênero marcado (regras de 20-21/10): vocativos, insultos e plurais masculinos dirigidos a ele
D3_PLAYER_GENDERED = (r"\bbem-vind[oa]\b", r"\bamig[oa]\s*[,!?]", r"\bcara\s*[,!?.]", r"\bparceir[oa]\b", r"\bprotagonista\b",
                      r"\bpersonagem principal\b", r"\bvocês todos\b", r"\bocupad[oa] demais\b",
                      r"\bcriança Treinadora\b", r"(?:^|[.!?…] )Seu [a-zç]+[!,]", r"\bjovem amigo\b",
                      r"\bvocê (?:é|está|ficou|parece|estava|era|foi) (?:muito |tão |bem |mais )?"
                      r"(?:enxerid|bobalhon|esperto|burro|bruto|grosseir|mal-educad|malcriad|abusad|sozinh)[oa]\b")
D3_WRONG_FORMS = ("Esconderijo da Equipe Rocket", "Cidade de Vermilion", "Porto de Vermilion", "Elite dos Quatro",
                  "Professor Carvalho", "Pokébola", "Time Rocket", "Lt. Surge", "LT. SURGE", "Tenente Surge",
                  "Pokémon GYM", "Pokémon Journal")


@pytest.mark.parametrize("rel", D3_FILES)
def test_d3_jogador_sem_genero_e_formas_do_glossario(rel):
    body = _flat_plain(rel)
    found = [p for p in D3_PLAYER_GENDERED if re.search(p, body, 0 if "Seu" in p else re.I)]
    assert found == []
    assert [w for w in D3_WRONG_FORMS if w in body] == []


def _d3_terms() -> list[str]:
    extra = {"Prof. Carvalho", "Ten. Surge", "Sr. Fuji", "Elite Quatro", "Equipe Rocket", "Ponte da Pepita",
             "Sistema de Armazenamento de Pokémon", "Jornal Pokémon", "Torneio Pokémon", "Seminário Pokémon",
             "Casa Pokémon", "Cidade de Lavender", "Cidade Vermilion", "Cidade de Pallet", "Zona de Safári",
             "Floresta Viridian", "Monte Lua", "Túnel de Pedra", "Pedra Lunar", "Explorador VS", "Louco da Pesca",
             "Mestre de Caratê", "Líder de Ginásio", "Ginásio Pokémon", "Loja de Celadon", "Ilha Quatro",
             "Caverna Gélida", "Porto da Ilha Seis", "Irmãos Pássaro", "Mestre Ninja Venenoso", "Criança Pokémon",
             "Cidade de Goldenrod", "Barras Fúria", "Laboratório de Pesquisa Pokémon do Prof. Carvalho",
             "Seminário Pokémon do Prof. Carvalho", "Revista Fã de Pokémon",
             *[f"Ginásio de {city}" for city in ("Pewter", "Cerulean", "Vermilion", "Celadon", "Fuchsia", "Saffron",
                                                  "Cinnabar", "Viridian")]}
    return sorted(set(_multiword_terms()) | extra)


# Quebras permitidas (mesma exceção da A3): a placa do laboratório não cabe numa linha (278 px) e quebra
# depois de "Pesquisa"; qualquer outra quebra no meio do termo continua proibida
SPLIT_ALLOWED = {("Laboratório de Pesquisa Pokémon do Prof. Carvalho", "Laboratório de Pesquisa")}


@pytest.mark.parametrize("rel", D3_FILES)
def test_d3_nomes_nao_sao_partidos_na_quebra(rel):
    body = "".join(_blocks(rel).values())
    found = []
    for name in _d3_terms():
        for i, ch in enumerate(name):
            if ch != " " or (name, name[:i]) in SPLIT_ALLOWED:
                continue
            for br in ("\\n", "\\l"):
                if name[:i] + br + name[i + 1:] in body:
                    found.append(name)
    assert sorted(set(found)) == []


@pytest.mark.parametrize("rel", D3_FILES)
def test_d3_primeira_quebra_de_cada_caixa_e_n(rel):
    """Dentro de uma caixa (entre \\p) a primeira quebra desce uma linha (\\n); \\l só rola depois dela."""
    bad = []
    for label, text in _blocks(rel).items():
        for box in text.split("\\p"):
            first = re.search(r"\\[nl]", box)
            if first and first.group() != "\\n":
                bad.append(label)
    assert bad == []


def test_d3_explorador_vs_cabe_com_10_letras_largas_e_com_3_algarismos():
    """{STR_VAR_1} = passos que faltam para carregar: 100 - contador (src/vs_seeker.c:864), no máximo 3 algarismos."""
    env = ct._load_env(REPO_ROOT)
    raw = _blocks(TRAINERS_FILE)["VSSeeker_Text_BatteryNotChargedNeedXSteps"]
    assert "{STR_VAR_1}" in raw
    for filler in ("MMMMMMMMMM", "100"):
        for line in _BREAK_RAW.split(raw.replace("{STR_VAR_1}", filler)):
            assert ct.measure(line, env, "normal").widest <= 208, (filler, line)


def test_d3_arquivo_fama_caixas_de_no_maximo_2_linhas():
    """A caixa do Arquivo Fama tem 2 linhas (FCWINDOWID_MSGBOX, 4 tiles); a 3ª sobe com \\l, nunca com \\n."""
    too_tall = {label: ct.box_lines(text) for label, text in _blocks(FAME_FILE).items()
                if (label.startswith(("gFameCheckerFlavorText_", "gFameCheckerPersonQuote_", "PokemonJournal_"))
                    and ct.box_lines(text) > 2)}
    assert too_tall == {}


def _fame_speech(text: str) -> str:
    """A fala depois do título azul (primeiro parágrafo)."""
    return _plain("\\p".join(text.split("\\p")[1:]))


# O mesmo texto aparece no Jornal Pokémon e nas falas do Arquivo Fama (e em três falas repetidas): igual nos dois
_SHARED = {
    "PokemonJournal_Text_SpecialFeatureBrock": "gFameCheckerFlavorText_Brock5",
    "PokemonJournal_Text_SpecialFeatureMisty": "gFameCheckerFlavorText_Misty5",
    "PokemonJournal_Text_SpecialFeatureLtSurge": "gFameCheckerFlavorText_LtSurge5",
    "PokemonJournal_Text_SpecialFeatureErika": "gFameCheckerFlavorText_Erika5",
    "PokemonJournal_Text_SpecialFeatureKoga": "gFameCheckerFlavorText_Koga4",
    "PokemonJournal_Text_SpecialFeatureSabrina": "gFameCheckerFlavorText_Sabrina4",
    "PokemonJournal_Text_SpecialFeatureBlaine": "gFameCheckerFlavorText_Blaine5",
    "PokemonJournal_Text_SpecialFeatureLorelei": "gFameCheckerFlavorText_Lorelei3",
    "PokemonJournal_Text_SpecialFeatureBruno": "gFameCheckerFlavorText_Bruno2",
    "PokemonJournal_Text_SpecialFeatureAgatha": "gFameCheckerFlavorText_Agatha3",
    "PokemonJournal_Text_SpecialFeatureLance": "gFameCheckerFlavorText_Lance4",
    "PokemonJournal_Text_SpecialFeatureProfOak": "gFameCheckerFlavorText_ProfOak3",
    "PokemonJournal_Text_SpecialFeatureMrFuji": "gFameCheckerFlavorText_MrFuji5",
    "PokemonJournal_Text_SpecialFeatureDaisyOak": "gFameCheckerFlavorText_Daisy5",
}


def test_d3_jornal_pokemon_repete_o_texto_do_arquivo_fama():
    blocks = _blocks(FAME_FILE)
    for journal, flavor in _SHARED.items():
        assert _fame_speech(blocks[flavor]) in _plain(blocks[journal]), (journal, flavor)


def test_d3_falas_repetidas_do_arquivo_fama_sao_iguais():
    speech = {k: _fame_speech(v) for k, v in _blocks(FAME_FILE).items() if k.startswith("gFameCheckerFlavorText_")}
    for a, b in (("ProfOak3", "Daisy3"), ("ProfOak4", "Agatha4"), ("Blaine4", "MrFuji4")):
        assert speech[f"gFameCheckerFlavorText_{a}"] == speech[f"gFameCheckerFlavorText_{b}"], (a, b)


def test_d3_arquivo_fama_titulos_azuis_sao_so_estes_seis():
    heads = {_plain(t.split("\\p")[0]) for k, t in _blocks(FAME_FILE).items() if k.startswith("gFameCheckerFlavorText_")}
    assert heads == {"O que essa pessoa faz?", "Como é essa pessoa?", "Família e amigos?", "Pokémon preferido?",
                     "Corre um boato…", "Onde essa pessoa nasceu?"}


def _trainers_h() -> dict[str, tuple[str, str]]:
    """TRAINER_X -> (classe, nome) de src/data/trainers.h."""
    source = (REPO_ROOT / "src/data/trainers.h").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"\[(TRAINER_\w+)\] = \{(.*?)\n    \},", source, re.S):
        cls = re.search(r"\.trainerClass = (\w+)", m.group(2))
        name = re.search(r'\.trainerName = _\("([^"]*)"\)', m.group(2))
        if cls and name:
            out[m.group(1)] = (cls.group(1), name.group(1))
    return out


def test_d3_nomes_das_pessoas_do_arquivo_fama_cabem_na_lista_de_56_px():
    """A lista usa o trainerName de trainers.h para 12 pessoas (FCWINDOWID_LIST: 8 tiles, x = 8)."""
    fame_c = (REPO_ROOT / "src/fame_checker.c").read_text(encoding="utf-8")
    table = fame_c[fame_c.index("sTrainerIdxs[] = {"):]
    ids = re.findall(r"= (TRAINER_\w+)", table[:table.index("};")])
    assert len(ids) == 12, ids          # 8 Líderes, 3 da Elite Quatro com Lance e o Chefe: os que não vêm de strings.c
    env = ct._load_env(REPO_ROOT)
    trainers = _trainers_h()
    wide = {i: ct.measure(trainers[i][1], env, "normal").widest for i in ids
            if ct.measure(trainers[i][1], env, "normal").widest > 8 * 8 - 8}
    assert wide == {}
    assert trainers["TRAINER_LEADER_LT_SURGE"][1] == "LT. SURGE"   # nome próprio fica (53 px); "Ten. Surge" mede 57


# ---- as classes "Executivo" e "Executiva" (decisão D4 do Cintra; a Admin de pic feminina é "Executiva") --

ADMIN_M = "TRAINER_TEAM_ROCKET_ADMIN_2"      # pic ROCKET_GRUNT_M
ADMIN_F = "TRAINER_TEAM_ROCKET_ADMIN"        # pic ROCKET_GRUNT_F
ADMINS = {ADMIN_M, ADMIN_F}
ADMIN_CLASSES = ("TRAINER_CLASS_ROCKET_ADMIN", "TRAINER_CLASS_ROCKET_ADMIN_F")


def _class_values() -> dict[str, int]:
    header = (REPO_ROOT / "include/constants/trainers.h").read_text(encoding="utf-8")
    return {n: int(v) for n, v in re.findall(r"#define (TRAINER_CLASS_\w+)\s+(\d+)", header)}


def _trainer_pics() -> dict[str, str]:
    source = (REPO_ROOT / "src/data/trainers.h").read_text(encoding="utf-8")
    return {m.group(1): re.search(r"\.trainerPic = (\w+)", m.group(2)).group(1)
            for m in re.finditer(r"\[(TRAINER_\w+)\] = \{(.*?)\n    \},", source, re.S)
            if re.search(r"\.trainerPic = ", m.group(2))}


def test_executivo_e_executiva_sao_classes_novas_com_id_proprio():
    values = _class_values()
    assert values["TRAINER_CLASS_ROCKET_ADMIN"] == 107 and values["TRAINER_CLASS_ROCKET_ADMIN_F"] == 108
    assert max(values.values()) == 108
    assert list(values.values()).count(107) == list(values.values()).count(108) == 1   # u8 trainerClass: cabe em 0xFF


def test_a_classe_de_cada_admin_bate_com_o_sexo_da_pic():
    trainers, pics = _trainers_h(), _trainer_pics()
    assert pics[ADMIN_F].endswith("_F") and pics[ADMIN_M].endswith("_M")
    assert trainers[ADMIN_F][0] == "TRAINER_CLASS_ROCKET_ADMIN_F"          # "Executiva"
    assert trainers[ADMIN_M][0] == "TRAINER_CLASS_ROCKET_ADMIN"            # "Executivo"
    for admin in ADMINS:
        assert trainers[admin][0].endswith("_F") == pics[admin].endswith("_F"), admin
    assert {k for k, (cls, _n) in trainers.items() if cls in ADMIN_CLASSES} == ADMINS


def test_executivos_so_nos_2_admins_e_recrutas_intactos():
    trainers = _trainers_h()
    assert all(trainers[a][1] == "Rocket" for a in ADMINS)
    recrutas = {k for k, (cls, _n) in trainers.items() if cls == "TRAINER_CLASS_TEAM_ROCKET"}
    assert len(recrutas) == 51 and all(trainers[k][1] == "Rocket" for k in recrutas)
    # nenhum nome em inglês sobra no trainerName ("LT. SURGE" fica: nome próprio, 53 px)
    assert not {n for _c, n in trainers.values()} & {"GRUNT", "ADMIN"}
    base = _base_source("src/data/trainers.h")
    if base is not None:
        # na base os 53 eram classe TEAM_ROCKET: 51 "GRUNT" + 2 "ADMIN"; o total de Treinadores não mudou
        assert base.count('trainerName = _("GRUNT")') == 51 and base.count('trainerName = _("ADMIN")') == 2
        now = (REPO_ROOT / "src/data/trainers.h").read_text(encoding="utf-8")
        assert re.findall(r"\.trainerClass = (\w+)", base).count("TRAINER_CLASS_TEAM_ROCKET") == 53
        assert len(re.findall(r"\.trainerClass = ", now)) == len(re.findall(r"\.trainerClass = ", base))
        assert re.findall(r'\.trainerName = _\("([^"]*)"\)', base).count("LT. SURGE") == \
            re.findall(r'\.trainerName = _\("([^"]*)"\)', now).count("LT. SURGE") == 1


def test_executivo_e_executiva_tem_nome_e_cabem_na_classe_de_12_letras():
    table = (REPO_ROOT / "src/data/text/trainer_class_names.h").read_text(encoding="utf-8")
    names = dict(re.findall(r'\[(TRAINER_CLASS_\w+)\]\s*=\s*_\("([^"]*)"\)', table))
    assert names["TRAINER_CLASS_ROCKET_ADMIN"] == "Executivo"
    assert names["TRAINER_CLASS_ROCKET_ADMIN_F"] == "Executiva"
    assert len("Executivo") <= 12 and len("Executiva") <= 12
    assert names["TRAINER_CLASS_TEAM_ROCKET"] == "Recruta"          # os recrutas não mudam


def test_executivos_ganham_o_mesmo_premio_e_a_mesma_musica_que_o_recruta():
    battle = (REPO_ROOT / "src/battle_main.c").read_text(encoding="utf-8")
    money = dict(re.findall(r"\{(TRAINER_CLASS_\w+), (\d+)\}", battle[battle.index("gTrainerMoneyTable[]"):]))
    assert money["TRAINER_CLASS_ROCKET_ADMIN"] == money["TRAINER_CLASS_ROCKET_ADMIN_F"] \
        == money["TRAINER_CLASS_TEAM_ROCKET"] == "8"
    # toda lista (prêmio, fanfarra da vitória, música de batalha) que cita o recruta cita as duas classes novas
    for rel, n in (("src/battle_main.c", 2), ("src/pokemon.c", 1)):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert text.count("TRAINER_CLASS_TEAM_ROCKET") == n, rel
        for cls in ADMIN_CLASSES:
            assert len(re.findall(rf"\b{cls}\b", text)) == n, (rel, cls)
        assert ("case TRAINER_CLASS_TEAM_ROCKET:\n        case TRAINER_CLASS_ROCKET_ADMIN:\n"
                "        case TRAINER_CLASS_ROCKET_ADMIN_F:") in text, rel


def test_executivos_nao_sao_citados_fora_dos_lugares_esperados():
    """Quem indexa por classe: nomes, prêmio, músicas (acima) e trainers.h; nada mais usa as classes novas."""
    users = set()
    for path in list((REPO_ROOT / "src").rglob("*.[ch]")) + list((REPO_ROOT / "include").rglob("*.h")):
        if "TRAINER_CLASS_ROCKET_ADMIN" in path.read_text(encoding="utf-8", errors="replace"):
            users.add(path.relative_to(REPO_ROOT).as_posix())
    assert users == {"include/constants/trainers.h", "src/battle_main.c", "src/pokemon.c",
                     "src/data/text/trainer_class_names.h", "src/data/trainers.h"}


def test_d3_termos_criados_estao_no_glossario():
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    d3 = {t["en"]: t["pt"] for t in data["termos"] if t.get("frente") == "D3"}
    assert d3["CERULEAN CAPE"] == "Cabo Cerulean"
    # Barra Fúria é da C3 (Ruling 29) e "Ponte da Pepita" é da B3: a D3 só registra enquanto a B3 não está na base
    assert "RAGE CANDYBAR" not in d3
    rage = [t for t in data["termos"] if t["en"] == "RAGE CANDYBAR"]
    assert [(t["pt"], t["categoria"]) for t in rage] == [("Barra Fúria", "item")]
    admin = next(t for t in data["termos"] if t["en"] == "ADMIN")
    assert admin["pt"] == "Executivo"
    # as etiquetas de 84 px que fogem do glossário estão registradas
    assert d3["ROCKET HIDEOUT (etiqueta do Arquivo Fama)"] == "Base Rocket"
    assert "PROF. OAK (nome na caixa do Arquivo Fama)" not in d3          # a caixa tem 208 px: "Prof. Carvalho"


def test_d3_nomes_das_pessoas_do_arquivo_fama_saem_na_caixa_de_208_px():
    """gFameCheckerPersonName_* só é impresso na MSGBOX (fame_checker.c:965-966): nome completo."""
    blocks = _blocks(FAME_FILE)
    assert _plain(blocks["gFameCheckerPersonName_ProfOak"]) == "Prof. Carvalho"
    assert _plain(blocks["gFameCheckerPersonName_LtSurge"]) == "Ten. Surge"
    assert _plain(blocks["gFameCheckerPersonName_MrFuji"]) == "Sr. Fuji"
    assert "\\n" not in blocks["gFameCheckerPersonName_ProfOak"]


def test_d3_etiquetas_de_objeto_cabem_no_buffer_de_19_bytes():
    """A etiqueta do objeto passa por StringExpandPlaceholders(gStringVar1, ...) (fame_checker.c:1407): 20 bytes."""
    env = ct._load_env(REPO_ROOT)
    over = {}
    for label, text in _blocks(FAME_FILE).items():
        if label.startswith("gFameCheckerFlavorTextOriginObjectName_"):
            nbytes = ct.measure(text, env, "small").nbytes
            if nbytes > 19:
                over[label] = nbytes
    assert over == {}


def test_d3_etiquetas_de_cidade_e_ginasio_sao_uniformes():
    """Na mesma tela: toda cidade é "Cidade X" e todo Ginásio é "Ginásio X" (sem "de", regra 1 do glossário)."""
    texts = {_plain(t) for k, t in _blocks(FAME_FILE).items() if k.startswith("gFameCheckerFlavorTextOriginLocation_")}
    assert not [t for t in texts if t.startswith(("Cidade de ", "Ginásio de "))]
    assert {"Cidade Pallet", "Cidade Pewter", "Cidade Celadon", "Ginásio Pewter", "Ginásio Viridian"} <= texts
