"""Checagem estática dos textos do jogo: charmap, terminador, largura da caixa e inglês residual.

Só devolve problemas (`falha`, ou `aviso` para o inglês residual e para exceções obsoletas); texto
sem problema não gera `Result`.

Exceções (`exceptions["text"]`, em `test/excecoes.json`) congelam problemas pré-existentes. Cada
uma é um objeto com:
  file, label, rule  - qual achado (arquivo relativo ao repo com `/`, rótulo, regra);
  fingerprint        - sha1 (16 primeiros hex) do texto cru do rótulo na hora do congelamento;
  valor              - medida congelada (px da linha mais larga, só para a regra `largura`).
A exceção só cala o achado enquanto o fingerprint (e o valor) batem com o texto atual: texto
alterado volta a ser checado normalmente. Exceção cujo rótulo sumiu, cujo texto mudou ou cujo
problema desapareceu vira `aviso` "exceção obsoleta", para a lista poder encolher.
`compute_baseline(repo)` gera a lista de exceções para os problemas atuais.
"""

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from esteira.result import Result

PLAYER_NAME_CHARS = 7  # {PLAYER}/{RIVAL}: nome de até 7 letras

# Largura útil (px) por fonte de texto, derivada dos templates de janela do repo. A primeira regra
# que casar (arquivo e, se houver, prefixo de rótulo) vale; `None` = largura não determinada com
# segurança, a regra de largura é pulada (nem falha nem aviso). Fonte sem regra também é pulada.
# O espaçamento entre letras (`letterSpacing`) não conta: só é somado a texto japonês (src/text.c:854).
DIALOG_WIDTH_PX = 26 * 8
_DIALOG = ("diálogo padrão: sStandardTextBox_WindowTemplates .width = 26 tiles (src/new_menu_helpers.c:40), "
           "texto em x = 0 (src/new_menu_helpers.c:411)")
_DIALOG_INC = ("aide", "berries", "competitive_brothers", "day_care", "eon_ticket", "flavor_text",
               "ingame_trade", "itemfinder", "obtain_item", "pc", "poke_mart", "route23", "safari_zone",
               "seagallop", "sign_lady", "surf", "trainer_card", "trainers", "white_out")
WIDTH_RULES: list[tuple[str, str | None, int | None, str]] = [
    # (padrão do arquivo, prefixo do rótulo, px, de onde vem)
    ("data/maps/*/text.inc", None, DIALOG_WIDTH_PX, _DIALOG),
    *[(f"data/text/{name}.inc", None, DIALOG_WIDTH_PX, _DIALOG + "; usado só via msgbox/message")
      for name in _DIALOG_INC],
    ("src/data/items.json", None, 200,
     "janela de descrição da mochila: sDefaultBagWindowsStd[1].width = 25 tiles (src/bag.c:34), texto em "
     "x = 0 (src/item_menu.c:756); as descrições originais medem no máx. 198 px. Lojas, TM case e "
     "bolsa de frutas usam outras janelas e não são modeladas"),
    ("src/data/text/quest_log.h", None, 30 * 8 - 2,
     "janela de descrição do Quest Log: DESC_WIN_WIDTH = DISPLAY_WIDTH / 8 = 30 tiles (src/quest_log.c:40,163), "
     "texto em x = 2 (src/quest_log.c:1039)"),
    ("src/strings.c", "gStartMenuDesc_", 30 * 8 - 2,
     "barra de ajuda do menu Start: sHelpMessageWindowTemplate .width = 30 tiles (src/help_message.c:14), "
     "texto em x = 2 (src/help_message.c:97)"),
    # Os {STR_VAR_*} medem 0 aqui; as linhas montadas (nível, item, espécie) de toda espécie são
    # medidas à parte em _evolution_page_results (esteira/evolution_page.py).
    ("src/strings.c", "gText_PokeSum_Evo", 28 * 8 - 2,
     "página EVOLUTION do resumo: sWindowTemplates_Evolution[0] .width = 28 tiles "
     "(src/pokemon_summary_screen.c:921), texto em x = EVOLUTION_PAGE_TEXT_X = 2 "
     "(src/pokemon_summary_screen.c:911)"),
    # Hack 5: página IVs/EVs (os pedaços de cada linha; a linha inteira, com as colunas, é
    # medida em _ivev_page_results)
    *[("src/strings.c", prefix, 28 * 8 - 2, "página IVs/EVs do resumo: sWindowTemplates_Ivs[0] .width = 28 tiles (src/pokemon_summary_screen.c:966), texto em x = IVEV_PAGE_TEXT_X = 2 (src/pokemon_summary_screen.c:957); as linhas montadas são medidas em _ivev_page_results")
      for prefix in ("gText_PokeSum_Iv", "gText_PokeSum_Stat", "gText_PokeSum_HiddenPower",
                     "gText_PokeSum_Ev")],
    # Sem largura determinada (janelas diferentes ou não localizadas): pulados de propósito.
    ("data/text/help_system.inc", None, None,
     "texto renderizado num bitmap de 26 tiles (src/help_system_util.c:588-591) cuja janela de exibição "
     "não foi determinada"),
    ("data/text/new_game_intro.inc", None, None, "janelas variadas de src/oak_speech.c"),
    ("data/text/fame_checker.inc", None, None, "janelas de src/fame_checker.c não verificadas"),
    ("data/text/pokedude.inc", None, None, "janela de batalha não verificada"),
    ("data/text/pc_transfer.inc", None, None, "usado também em batalha/naming screen; janela não verificada"),
    ("data/text/save.inc", None, None, "usado por src/start_menu.c; janela não verificada"),
    ("data/text/pokedex_rating.inc", None, None, "usado por src/prof_pc.c; janela não verificada"),
    ("data/text/braille.inc", None, None, "texto braille, janela própria"),
    ("src/strings.c", None, None, "menus e janelas diversos"),
    ("src/data/text/*.h", None, None, "nomes, descrições e textos de janelas diversas"),
]

# Regras (usadas em `excecoes.json`)
RULE_CHARMAP = "charmap"
RULE_TERMINATOR = "terminador"
RULE_WIDTH = "largura"
RULE_SYNTAX = "sintaxe"
RULE_ENGLISH = "ingles"
RULE_OBSOLETE = "obsoleta"

_NAME_PLACEHOLDERS = ("PLAYER", "RIVAL")

# Linhas de charmap: `'A' = BB`, `'\'' = B4`, `PKMN = 53 54`, `'\n' = FE @ comentário`
_CHAR_ENTRY = re.compile(r"^'(\\.|[^'\\])'\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+?)\s*(?:@.*)?$")
_NAME_ENTRY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+?)\s*(?:@.*)?$")
_JAPANESE_SECTION = "@ Hiragana"  # o que vem depois é só japonês/constantes (cores, sons...)
_NUMBER = re.compile(r"^(?:0[xX][0-9A-Fa-f]+|\d+)$")

# Quebras de linha de texto: o resto da string continua numa linha nova da caixa
_BREAKS = {"n": "\\n", "l": "\\l", "p": "\\p"}

_ENGLISH_WORDS = re.compile(
    r"\b(?:the|you|your|and|with|this|that|have|what|are|from|will|can|not|was|were|there|they)\b",
    re.IGNORECASE)
_ACCENTED = re.compile(r"[ÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜàáâãäçèéêëìíîïñòóôõöùúûü]")


@dataclass
class _Entry:
    file: str
    label: str
    texts: tuple[str, ...]  # variantes do texto cru (escapes `\n`, `\p` e `{...}` como no fonte)
    needs_terminator: bool


@dataclass
class _Env:
    chars: set[str]                 # todo caractere aceito (latino + japonês)
    latin_width: dict[str, int]     # largura em px dos caracteres da fonte latina
    names: set[str]                 # nomes de macro/placeholder definidos no charmap
    glyph_macros: dict[str, int]    # macros que imprimem glifos ({PKMN}, {LV}...) -> largura
    name_width: int                 # largura de {PLAYER}/{RIVAL}


# ---- ambiente: charmap e tabela de larguras ------------------------------------------------

def _load_widths(repo: Path) -> list[int]:
    source = (repo / "src" / "text.c").read_text(encoding="utf-8")
    m = re.search(r"sFontNormalLatinGlyphWidths\[\]\s*=\s*\{(.*?)\};", source, re.S)
    if not m:
        raise RuntimeError("sFontNormalLatinGlyphWidths não encontrada em src/text.c")
    return [int(n) for n in re.findall(r"\d+", m.group(1))]


def _load_env(repo: Path) -> _Env:
    widths = _load_widths(repo)
    chars: set[str] = set()
    latin_width: dict[str, int] = {}
    names: set[str] = set()
    glyph_macros: dict[str, int] = {}
    latin = True
    for raw in (repo / "charmap.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith(_JAPANESE_SECTION):
            latin = False
        m = _CHAR_ENTRY.match(line)
        if m:
            ch = m.group(1)
            if ch.startswith("\\"):
                if ch != "\\'":
                    continue  # '\n', '\l', '\p' são quebras de linha, tratadas à parte
                ch = "'"
            chars.add(ch)
            first = int(m.group(2).split()[0], 16)
            if latin:
                latin_width.setdefault(ch, widths[first])
            continue
        m = _NAME_ENTRY.match(line)
        if m:
            names.add(m.group(1))
            data = bytes.fromhex(m.group(2).replace(" ", ""))
            if latin and all(b < 0xF7 for b in data):
                glyph_macros[m.group(1)] = sum(widths[b] for b in data)
    name_width = PLAYER_NAME_CHARS * max(w for ch, w in latin_width.items() if ch.isalnum() and ch.isascii())
    return _Env(chars, latin_width, names, glyph_macros, name_width)


# ---- extração dos textos -------------------------------------------------------------------

_STRING_LINE = re.compile(r'^\s*\.string\s+"((?:[^"\\]|\\.)*)"\s*(?:@.*)?$')
_LABEL_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)::?\s*(?:@.*)?$")


_CONDITIONAL = re.compile(r"^[#.]\s*(if\w*|elif|elseif|else|endif)\b")  # cpp (#if) e gas (.if)


def _variants(parts: list[tuple[tuple[tuple[int, int], ...], str]]) -> tuple[str, ...]:
    """Textos possíveis de um bloco: um por combinação de ramos de `#if/#else` (em geral, um só)."""
    ids = sorted({i for conds, _ in parts for i, _branch in conds})
    combos: list[dict[int, int]] = [{}]
    for i in ids:
        branches = sorted({b for conds, _ in parts for j, b in conds if j == i})
        combos = [{**c, i: b} for c in combos for b in branches]
    texts = ["".join(t for conds, t in parts if all(c[i] == b for i, b in conds)) for c in combos]
    return tuple(dict.fromkeys(texts))


def _extract_inc(repo: Path, path: Path) -> Iterator[_Entry | Result]:
    """Blocos de `.string` consecutivos sob o mesmo rótulo viram um texto só.

    Ramos de `#ifdef/#else/#endif` dentro do bloco são analisados cada um como um texto próprio.
    """
    rel = path.relative_to(repo).as_posix()
    label = None
    parts: list[tuple[tuple[tuple[int, int], ...], str]] = []
    block_label = None
    open_conditionals: list[list[int]] = []  # [linha do #if, ramo atual]

    def flush() -> Iterator[_Entry]:
        nonlocal parts, block_label
        if parts:
            yield _Entry(rel, block_label or "?", _variants(parts), True)
        parts, block_label = [], None

    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        label_match = _LABEL_LINE.match(line)
        if label_match:
            yield from flush()
            label = label_match.group(1)
            continue
        stripped = line.strip()
        cpp = _CONDITIONAL.match(stripped)
        if cpp:
            kind = cpp.group(1)
            if kind.startswith("if"):
                open_conditionals.append([number, 0])
            elif kind == "endif":
                if open_conditionals:
                    open_conditionals.pop()
            elif open_conditionals:
                open_conditionals[-1][1] += 1
        elif stripped.startswith(".string"):
            string_match = _STRING_LINE.match(line)
            if not string_match:
                yield Result(f"texto/{RULE_SYNTAX}", "falha",
                             f"{rel}:{number}: linha .string não reconhecida: {stripped}")
                continue
            if not parts:
                block_label = label or f"linha {number}"
            parts.append((tuple((i, b) for i, b in open_conditionals), string_match.group(1)))
        elif stripped and not stripped.startswith("@"):
            yield from flush()  # outra diretiva (.align, .byte...) encerra o bloco
    yield from flush()


def _scan_c_strings(source: str) -> Iterator[tuple[int, str]]:
    """Acha cada `_( "..." "..." )` fora de comentários; devolve (posição do `_(`, texto cru)."""
    i, n = 0, len(source)
    while i < n:
        c = source[i]
        if source.startswith("//", i):
            i = source.find("\n", i)
            i = n if i < 0 else i
        elif source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = n if end < 0 else end + 2
        elif c == '"':
            i = _skip_literal(source, i)
        elif c == "_" and source.startswith("_(", i) and (i == 0 or not (source[i - 1].isalnum()
                                                                        or source[i - 1] == "_")):
            parsed = _parse_underscore_call(source, i + 2)
            if parsed is not None:
                text, end = parsed
                yield i, text
                i = end
                continue
            i += 2
        else:
            i += 1


def _skip_literal(source: str, i: int) -> int:
    i += 1
    while i < len(source) and source[i] != '"':
        i += 2 if source[i] == "\\" else 1
    return i + 1


def _parse_underscore_call(source: str, i: int) -> tuple[str, int] | None:
    """Lê os literais seguidos (concatenação de strings C) até o `)`; None se não for só literais."""
    parts: list[str] = []
    n = len(source)
    while i < n:
        c = source[i]
        if c.isspace():
            i += 1
        elif source.startswith("//", i):
            i = source.find("\n", i)
            if i < 0:
                return None
        elif source.startswith("/*", i):
            end = source.find("*/", i + 2)
            if end < 0:
                return None
            i = end + 2
        elif c == '"':
            end = _skip_literal(source, i)
            parts.append(source[i + 1:end - 1])
            i = end
        elif c == ")":
            return ("".join(parts), i + 1) if parts else None
        else:
            return None
    return None


_INDEX_LABEL = re.compile(r"(?:^|[\n,{])\s*\[\s*([A-Za-z_]\w*)\s*\]\s*(?:\[[^\]]*\]\s*)*=\s*$")
_VAR_LABEL = re.compile(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*=\s*$")


def _c_label(source: str, pos: int, fallback: str) -> str:
    """Rótulo de um `_(`: o índice (`[MOVE_X] = _(`) ou a variável (`gText_X[] = _(`)."""
    context = source[max(0, pos - 200):pos]
    m = _INDEX_LABEL.search(context) or _VAR_LABEL.search(context)
    return m.group(1) if m else fallback


def _extract_c(repo: Path, path: Path) -> Iterator[_Entry]:
    rel = path.relative_to(repo).as_posix()
    source = path.read_text(encoding="utf-8")
    counter: dict[str, int] = {}
    for pos, text in _scan_c_strings(source):
        line = source.count("\n", 0, pos) + 1
        label = _c_label(source, pos, f"linha {line}")
        counter[label] = counter.get(label, 0) + 1
        if counter[label] > 1:
            label = f"{label}#{counter[label]}"
        yield _Entry(rel, label, (text,), False)


def _extract_items(repo: Path, path: Path) -> Iterator[_Entry]:
    rel = path.relative_to(repo).as_posix()
    for item in json.loads(path.read_text(encoding="utf-8")).get("items", []):
        text = item.get("description_english")
        if text is not None:
            yield _Entry(rel, item.get("itemId", "?"), (text,), False)


def _sources(repo: Path) -> Iterator[_Entry | Result]:
    for path in sorted((repo / "data" / "text").glob("*.inc")):
        yield from _extract_inc(repo, path)
    for path in sorted((repo / "data" / "maps").glob("*/text.inc")):
        yield from _extract_inc(repo, path)
    strings_c = repo / "src" / "strings.c"
    if strings_c.is_file():
        yield from _extract_c(repo, strings_c)
    for path in sorted((repo / "src" / "data" / "text").glob("*.h")):
        yield from _extract_c(repo, path)
    items = repo / "src" / "data" / "items.json"
    if items.is_file():
        yield from _extract_items(repo, items)


# ---- análise de um texto -------------------------------------------------------------------

def _tokenize(text: str) -> Iterator[tuple[str, str]]:
    """('char', c) | ('break', '') | ('ph', conteúdo) | ('bad', descrição)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if nxt in _BREAKS:
                yield "break", ""
            elif nxt == '"':
                yield "char", '"'
            else:
                yield "bad", f"escape desconhecido \\{nxt}"
            i += 2
        elif c == "{":
            end = text.find("}", i)
            if end < 0:
                yield "bad", "'{' sem '}'"
                return
            yield "ph", text[i + 1:end]
            i = end + 1
        else:
            yield "char", c
            i += 1


def width_limit(file: str, label: str) -> int | None:
    """Largura útil em px da caixa onde o texto aparece, ou None se não foi determinada."""
    for pattern, prefix, px, _source in WIDTH_RULES:
        if fnmatch.fnmatchcase(file, pattern) and (prefix is None or label.startswith(prefix)):
            return px
    return None


def fingerprint(texts: tuple[str, ...]) -> str:
    """Impressão digital do texto cru de um rótulo (todas as variantes de #if/.if)."""
    return hashlib.sha1("\x00".join(texts).encode("utf-8")).hexdigest()[:16]


# problema: (regra, descrição, valor medido ou None)
_Problem = tuple[str, str, int | None]


def _analyze(text: str, needs_terminator: bool, limit: int | None, env: _Env) -> list[_Problem]:
    """Problemas do texto; `limit` é a largura útil em px (None = não medir)."""
    problems: list[_Problem] = []
    bad_chars: list[str] = []
    bad_words: list[str] = []
    widest = 0
    width = 0
    latin_only = True
    ends_with_terminator = False

    def close_line() -> None:
        nonlocal widest, width, latin_only
        if latin_only:
            widest = max(widest, width)
        width, latin_only = 0, True

    for kind, value in _tokenize(text):
        ends_with_terminator = False
        if kind == "break":
            close_line()
        elif kind == "bad":
            bad_chars.append(value)
        elif kind == "char":
            if value not in env.chars:
                if value not in bad_chars:
                    bad_chars.append(value)
            elif value == "$":
                ends_with_terminator = True  # terminador (FF): não ocupa largura
            elif value in env.latin_width:
                width += env.latin_width[value]
            else:
                latin_only = False  # japonês: outra fonte/tabela, não dá para medir aqui
        else:  # placeholder `{PALAVRA arg ...}`
            for word in value.split():
                if word in _NAME_PLACEHOLDERS:
                    width += env.name_width
                elif word in env.glyph_macros:
                    width += env.glyph_macros[word]
                elif word not in env.names and not _NUMBER.match(word):
                    bad_words.append(word)
    close_line()

    for ch in bad_chars:
        shown = ch if ch.startswith("escape") or ch.startswith("'{'") else f"'{ch}'"
        problems.append((RULE_CHARMAP, f"caractere fora do charmap: {shown}", None))
    for word in bad_words:
        problems.append((RULE_CHARMAP, f"placeholder fora do charmap: {{{word}}}", None))
    if needs_terminator and not ends_with_terminator:
        problems.append((RULE_TERMINATOR, "terminador ausente: bloco .string não termina em '$'", None))
    if limit is not None and widest > limit:
        problems.append((RULE_WIDTH, f"largura excedida: linha com {widest} px, limite {limit} px", widest))
    return problems


def _english_problem(text: str) -> bool:
    """Sem acento (fora o 'é' de POKéMON) e com palavra inglesa comum."""
    plain = text.replace("POKé", "POKE")
    return not _ACCENTED.search(plain) and bool(_ENGLISH_WORDS.search(plain))


# ---- ponto de entrada ----------------------------------------------------------------------

def _entry_problems(entry: _Entry, env: _Env, english_check: bool) -> list[_Problem]:
    limit = width_limit(entry.file, entry.label)
    found = dict.fromkeys(p for text in entry.texts
                          for p in _analyze(text, entry.needs_terminator, limit, env))
    problems = list(found)
    if english_check and any(_english_problem(text) for text in entry.texts):
        problems.append((RULE_ENGLISH, "possível texto em inglês sem tradução", None))
    return problems


def _scan(root: Path, english_check: bool) -> tuple[list[Result], dict[tuple[str, str], tuple[str, list[_Problem]]]]:
    """(resultados de sintaxe, {(arquivo, rótulo): (fingerprint, problemas)})."""
    env = _load_env(root)
    syntax: list[Result] = []
    entries: dict[tuple[str, str], tuple[str, list[_Problem]]] = {}
    for entry in _sources(root):
        if isinstance(entry, Result):
            syntax.append(entry)
            continue
        entries[(entry.file, entry.label)] = (fingerprint(entry.texts), _entry_problems(entry, env, english_check))
    return syntax, entries


def _evolution_page_results(root: Path) -> list[Result]:
    """Hack 4: largura de cada linha da página EVOLUTION, montada para toda espécie com os
    nomes de verdade (os rótulos gText_PokeSum_Evo* sozinhos não dizem o tamanho final). Repo
    sem os fontes da página (fixtures) não é checado."""
    from esteira.constants import Constants
    from esteira.evolution_page import (LINE_WIDTH_PX, SOURCE_FILES, SOURCE_REF,
                                        check_page_widths)
    if not all((root / path).is_file() for path in SOURCE_FILES):
        return []
    consts = Constants.load(str(root), ["species.h"])
    return [Result(f"texto/{RULE_WIDTH}", "falha",
                   f"src/strings.c: página EVOLUTION de {species}: '{line}' com {px} px, limite "
                   f"{LINE_WIDTH_PX} px ({SOURCE_REF})")
            for species, line, px in check_page_widths(root, consts)]


def _ivev_page_results(root: Path) -> list[Result]:
    """Hack 5: largura das linhas da página IVs/EVs (com as colunas {SKIP x}) para os textos e
    números mais largos possíveis, e colunas que encavalariam. Repo sem os fontes não é checado."""
    from esteira.ivev_page import LINE_WIDTH_PX, SOURCE_FILES, check_page_widths
    if not all((root / path).is_file() for path in SOURCE_FILES):
        return []
    return [Result(f"texto/{RULE_WIDTH}", "falha",
                   f"src/strings.c: página IVs/EVs: '{line}'"
                   + (f" com {px} px, limite {LINE_WIDTH_PX} px" if px else ""))
            for line, px in check_page_widths(root)]


def check_text(repo: str, exceptions: dict, english_check: bool = False) -> list[Result]:
    syntax, entries = _scan(Path(repo), english_check)
    results = list(syntax) + _evolution_page_results(Path(repo)) + _ivev_page_results(Path(repo))
    frozen = exceptions.get("text", [])
    applied: set[tuple[str, str, str]] = set()  # exceções que de fato calaram um achado

    silenced: dict[tuple[str, str, str], dict] = {}
    for exc in frozen:
        key = (exc["file"], exc["label"])
        if key not in entries or exc["rule"] == RULE_ENGLISH and not english_check:
            continue
        if exc.get("fingerprint") != entries[key][0]:
            continue
        silenced[(exc["file"], exc["label"], exc["rule"])] = exc

    for (file, label), (_fp, problems) in entries.items():
        for rule, detail, value in problems:
            exc = silenced.get((file, label, rule))
            if exc is not None and exc.get("valor") in (None, value):
                applied.add((file, label, rule))
                continue
            status = "aviso" if rule == RULE_ENGLISH else "falha"
            results.append(Result(f"texto/{rule}", status, f"{file}: {label}: {detail}"))

    for exc in frozen:
        file, label, rule = exc["file"], exc["label"], exc["rule"]
        if rule == RULE_ENGLISH and not english_check:
            continue
        if (file, label, rule) in applied:
            continue
        if (file, label) not in entries:
            why = "o rótulo não existe mais"
        elif exc.get("fingerprint") != entries[(file, label)][0]:
            why = "o texto mudou desde o congelamento"
        else:
            why = "o problema não ocorre mais (ou mudou de valor)"
        results.append(Result(f"texto/{RULE_OBSOLETE}", "aviso",
                              f"exceção obsoleta ({rule}) em {file}: {label}: {why}; remova-a de excecoes.json"))
    return results


def compute_baseline(repo: str) -> list[dict]:
    """Exceções (ordenadas) que congelam todos os problemas de texto atuais (sem o inglês residual)."""
    syntax, entries = _scan(Path(repo), english_check=False)
    if syntax:
        raise ValueError(f"linhas .string não reconhecidas: {[r.detail for r in syntax]}")
    baseline = []
    for (file, label), (fp, problems) in sorted(entries.items()):
        for rule, _detail, value in sorted(problems, key=lambda p: p[0]):
            exc = {"file": file, "label": label, "rule": rule, "fingerprint": fp}
            if value is not None:
                exc["valor"] = value
            if exc not in baseline:
                baseline.append(exc)
    return baseline
