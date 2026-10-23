"""Estouro de buffer de string (Task T4 da tradução): texto traduzível copiado em tempo de execução
para um array de tamanho fixo. O jogo não confere o tamanho (`StringCopy` copia até o EOS): um texto
traduzido mais comprido que o buffer escreve por cima do que vem depois e trava o jogo. Casos reais
da rodada 1: "Bolso de itens-chave" (20 letras + EOS) no `gStringVar3[20]` pelo `bufferstdstring` da
mensagem de item obtido, e "Loja de Celadon Cobertura" (25 + EOS) no `mapName[25]` do aviso de mapa.

Caminhos medidos (`buffer_paths`), cada um com o arquivo:linha de onde a cópia acontece:

  script   comandos de script que copiam texto para `gStringVar1/2/3` (`sScriptStringVars`,
           src/scrcmd.c): `bufferstdstring` (tabela `gStdStringPtrs`), `bufferstring`/`vbufferstring`,
           `bufferitemname`, `bufferitemnameplural` (nome + sufixo de plural) e `buffermovename`;
  C auto   `StringCopy`/`StringCopyN`/`StringCopyPadded`/`StringExpandPlaceholders`/
           `DynamicPlaceholderTextUtil_ExpandPlaceholders`/`CopyItemName`/`GetMapName*` com destino
           num array de tamanho conhecido (global, local da função ou campo de struct com tamanho
           único) e origem traduzível (rótulo de texto, tabela de textos, nome de item/golpe/lugar);
  declarado `DECLARED`: concatenação (texto + texto, texto + número), destino que é ponteiro, e os
           caminhos que não são medidos, cada um com o motivo;
  aviso    o aviso de nome de mapa (`mapName[25]`, src/map_name_popup.c), montado para cada mapa com
           andar: nome do lugar + " " + andar ("B1F"/"5F") ou o terraço (`gText_Rooftop2`).

Medida: bytes do texto (letra acentuada = 1 byte; placeholder = os bytes do charmap) + o EOS, contra
o tamanho do buffer lido do código-fonte (`u8 gStringVar3[20]`, `u8 mapName[25]`...; expressões
como `POKEMON_NAME_LENGTH + 1` são resolvidas pelos `#define` do include/). Quando a função expande
os placeholders (`StringExpandPlaceholders`, `DynamicPlaceholderTextUtil_ExpandPlaceholders`), cada
um que ela expande mede o pior caso da T3: `{PLAYER}`/`{RIVAL}` 7 letras, `{STR_VAR_n}`/`{DYNAMIC n}`
10 letras (ou o declarado em janelas_uso.VAR_CONTENTS). Um caminho de várias partes (concatenação)
soma a maior alternativa de cada parte.

Critério "sem achado novo em relação à base inglesa" (igual ao da T3): cada alternativa (um rótulo
de texto) é medida com o texto atual e com o da base (`check_text.TRANSLATION_BASE`). Reprova se o
total passa do buffer **e** passa do total da mesma alternativa na base; rótulo novo (sem inglês)
não pode passar do buffer. O inglês que já estoura fica documentado e a tradução pode ir até ele.

A checagem roda dentro da checagem de texto (`check_text.check_text`, regra `buffer`), em
`make firered_switch`/`make test-quick`. Só ela, nos arquivos de uma frente:
`python3 -m esteira.buffers [arquivos...]` (em test/, no WSL).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable, NamedTuple

from esteira import check_text as ct
from esteira.result import Result

RULE_BUFFER = "buffer"

# Buffers dos comandos de script (sScriptStringVars, src/scrcmd.c): STR_VAR_n -> gStringVarN
SCRIPT_STRING_VARS = ("gStringVar1", "gStringVar2", "gStringVar3")


# ---- constantes e tamanhos lidos do C -------------------------------------------------------

_DEFINE = re.compile(r"^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)[ \t]+([^\n]*?)[ \t]*(?://[^\n]*|/\*.*?\*/)?$", re.M)


@lru_cache(maxsize=8)
def _defines(repo: Path) -> dict[str, str]:
    """`#define NOME valor` de include/** e dos .c/.h de src/ (a primeira definição vale)."""
    out: dict[str, str] = {}
    paths = sorted((repo / "include").rglob("*.h")) + sorted((repo / "src").rglob("*.[ch]"))
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, value in _DEFINE.findall(text):
            out.setdefault(name, value)
    return out


_SIZE_TOKEN = re.compile(r"0[xX][0-9A-Fa-f]+|\d+|[A-Za-z_]\w*|[-+*/()]|\s+")


def eval_size(expr: str, defines: dict[str, str], depth: int = 0) -> int | None:
    """Valor de uma expressão de tamanho do C (`20`, `0x900`, `POKEMON_NAME_LENGTH + 1`); None se
    não der para resolver (sizeof, macro com argumentos...)."""
    if depth > 10:
        return None
    out = []
    pos = 0
    expr = expr.strip()
    while pos < len(expr):
        m = _SIZE_TOKEN.match(expr, pos)
        if not m:
            return None
        tok = m.group()
        pos = m.end()
        if tok.isspace():
            continue
        if re.fullmatch(r"[A-Za-z_]\w*", tok):
            if tok not in defines:
                return None
            value = eval_size(defines[tok], defines, depth + 1)
            if value is None:
                return None
            out.append(str(value))
        elif tok.lower().startswith("0x"):
            out.append(str(int(tok, 16)))
        elif tok == "/":
            out.append("//")
        else:
            out.append(tok)
    try:
        value = eval(" ".join(out), {"__builtins__": {}}, {})  # só números e + - * // ( )
    except Exception:  # noqa: BLE001 - expressão que não é aritmética simples
        return None
    return value if isinstance(value, int) else None


class Buffer(NamedTuple):
    name: str          # como aparece no relatório: "gStringVar3", "mapName"
    size: int          # bytes, com o EOS
    site: str          # arquivo:linha da declaração


# ---- leitura do C ---------------------------------------------------------------------------

def _blank_comments(source: str) -> str:
    """Comentários trocados por espaços (as posições e as quebras de linha ficam)."""
    def repl(m: re.Match) -> str:
        s = m.group()
        if s.startswith(("//", "/*")):
            return re.sub(r"[^\n]", " ", s)
        return s
    return re.sub(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', repl, source, flags=re.S)


def _match_close(source: str, i: int, open_ch: str = "(", close_ch: str = ")") -> int:
    """Posição logo depois do fechamento do `open_ch` em `i` (strings puladas); len se não fechar."""
    depth = 0
    n = len(source)
    while i < n:
        c = source[i]
        if c == '"' or c == "'":
            m = re.compile(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'').match(source, i)
            i = m.end() if m else i + 1
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _split_args(text: str) -> list[str]:
    """Argumentos de uma chamada (o texto entre os parênteses), separados nas vírgulas de nível 0."""
    args, depth, cur = [], 0, []
    i = 0
    while i < len(text):
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == '"':
            m = re.compile(r'"(?:[^"\\\n]|\\.)*"').match(text, i)
            if m:
                cur.append(m.group())
                i = m.end()
                continue
        if c == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if cur or args:
        args.append("".join(cur).strip())
    return args


_FUNC_HEADER = re.compile(r"^[A-Za-z_][\w \t*]*?\b([A-Za-z_]\w*)\s*\([^;{}()]*(?:\([^()]*\)[^;{}()]*)*\)\s*\{", re.M)


def _functions(source: str) -> list[tuple[str, int, int, int]]:
    """(nome, início do corpo, fim, início do cabeçalho) de cada função do arquivo (fonte sem
    comentários)."""
    out = []
    for m in _FUNC_HEADER.finditer(source):
        name = m.group(1)
        if name in ("if", "while", "for", "switch", "return", "sizeof"):
            continue
        start = m.end() - 1
        out.append((name, start, _match_close(source, start, "{", "}"), m.start()))
    return out


_ARRAY_DECL = re.compile(r"(?<![\w.*])(?:const\s+)?u8\s+(?:ALIGNED\(\d+\)\s+)?([A-Za-z_]\w*)\s*\[([^\]\n]*)\](?:\s*\[([^\]\n]*)\])?\s*(?=[;=,)])")
_TOP_ARRAY = re.compile(r"^((?:(?:static|EWRAM_DATA|IWRAM_DATA|COMMON_DATA|ALIGNED\(\d+\))\s+)*)u8\s+([A-Za-z_]\w*)"
                        r"\s*\[([^\]\n]+)\](?:\s*\[([^\]\n]+)\])?\s*(?:=|;)", re.M)
_STRUCT = re.compile(r"\bstruct\s*\w*\s*\{")
# ponteiro para linhas de tamanho fixo: static EWRAM_DATA u8 (*sListMenuItemStrings)[19]
_TOP_ROWS = re.compile(r"^((?:(?:static|EWRAM_DATA|IWRAM_DATA|COMMON_DATA)\s+)*)u8\s*\(\s*\*\s*([A-Za-z_]\w*)\s*\)"
                       r"\s*\[([^\]\n]+)\]\s*(?:=[^;]*)?;", re.M)


@dataclass
class _CFile:
    rel: str
    source: str                         # com os comentários em branco
    functions: list[tuple[str, int, int, int]]

    def line(self, pos: int) -> int:
        return self.source.count("\n", 0, pos) + 1

    def function_at(self, pos: int) -> tuple[str, int, int, int] | None:
        for f in self.functions:
            if f[1] <= pos < f[2]:
                return f
        return None


@dataclass
class _Arrays:
    """Arrays u8 de tamanho fixo: globais (não static), static por arquivo e campos de struct."""
    # nome -> [(arquivo, expressão do tamanho de um elemento, linha, 2D?)]
    globals: dict[str, list[tuple[str, str, int, bool]]] = field(default_factory=lambda: defaultdict(list))
    statics: dict[tuple[str, str], tuple[str, int, bool]] = field(default_factory=dict)
    fields: dict[str, list[tuple[str, str, int, bool]]] = field(default_factory=lambda: defaultdict(list))


def _scan_arrays(files: dict[str, _CFile], headers: dict[str, str]) -> _Arrays:
    arrays = _Arrays()
    for rel, cf in files.items():
        inside = [(s, e) for _n, s, e, _h in cf.functions]
        for m in _TOP_ARRAY.finditer(cf.source):
            if any(s <= m.start() < e for s, e in inside):
                continue
            size = m.group(4) or m.group(3)      # u8 x[A][B]: cada elemento tem B bytes
            two = m.group(4) is not None
            if "static" in m.group(1):
                arrays.statics[(rel, m.group(2))] = (size, cf.line(m.start()), two)
            else:
                arrays.globals[m.group(2)].append((rel, size, cf.line(m.start()), two))
        for m in _TOP_ROWS.finditer(cf.source):
            if any(s <= m.start() < e for s, e in inside):
                continue
            if "static" in m.group(1):
                arrays.statics[(rel, m.group(2))] = (m.group(3), cf.line(m.start()), True)
            else:
                arrays.globals[m.group(2)].append((rel, m.group(3), cf.line(m.start()), True))
    for rel, text in list(headers.items()) + [(r, cf.source) for r, cf in files.items()]:
        for sm in _STRUCT.finditer(text):
            end = _match_close(text, sm.end() - 1, "{", "}")
            body = text[sm.end():end]
            for m in _ARRAY_DECL.finditer(body):
                size = m.group(3) or m.group(2)
                if size.strip():
                    arrays.fields[m.group(1)].append((rel, size, text.count("\n", 0, sm.end() + m.start()) + 1,
                                                      m.group(3) is not None))
    return arrays


# ---- textos: índice por nome, tabelas, base -------------------------------------------------

class Alt(NamedTuple):
    """Uma alternativa de conteúdo de uma parte: um rótulo de texto (`key`) ou um valor fixo."""
    name: str                  # como aparece no relatório ("src/strings.c: gText_KeyItemsPocket")
    cur: int                   # bytes sem o EOS, texto atual
    base: int | None           # bytes na base inglesa (None = rótulo novo, sem inglês)
    key: tuple[str, str] | None = None


@dataclass
class _Ctx:
    repo: Path
    env: ct._Env
    entries: list[ct._Entry]
    base: ct._Base | None
    by_name: dict[str, list[ct._Entry]]
    tables: dict[str, list[tuple[str, list[tuple[str, str]]]]]   # tabela -> [(arquivo, [(arq, rótulo)])]
    c_files: dict[str, _CFile]
    arrays: _Arrays
    defines: dict[str, str]
    by_key: dict[tuple[str, str], ct._Entry] = field(default_factory=dict)
    alts_cache: dict[tuple, list] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)      # scripts e map.json lidos (compartilhado)
    prefix_bytes: int = 0
    designated: dict[str, dict[str, str]] = field(default_factory=dict)   # tabela -> {[CONST] = rótulo}      # o maior prefixo de nome de batalha (sText_*Prefix*, src/battle_message.c)

    def read(self, rel: str) -> str:
        if rel not in self.files:
            self.files[rel] = (self.repo / rel).read_text(encoding="utf-8", errors="replace")
        return self.files[rel]

    def listing(self, pattern: str) -> list[str]:
        """Arquivos do repo que casam com o glob (relativos), lidos do disco uma vez só."""
        key = "glob:" + pattern
        if key not in self.files:
            self.files[key] = "\n".join(p.relative_to(self.repo).as_posix() for p in sorted(self.repo.glob(pattern)))
        return [x for x in self.files[key].split("\n") if x]

    def base_texts(self, entry: ct._Entry) -> tuple[str, ...] | None:
        """Texto da base inglesa do rótulo; None = rótulo novo (ou sem base: modo estrito)."""
        if self.base is None:
            return None
        if entry.file not in self.base.present:
            return None
        if entry.file not in self.base.changed:
            return entry.texts
        return self.base.texts.get((entry.file, entry.label))

    def find(self, name: str, file: str | None = None) -> list[ct._Entry]:
        found = self.by_name.get(name, [])
        if file is not None:
            same = [e for e in found if e.file == file]
            if same:
                return same
        if name.startswith("s") and file is not None and file.endswith(".c"):
            return []        # static de outro arquivo não é este
        return found


def _base_name(label: str) -> str:
    return label.split("#")[0]


_TABLE_START = re.compile(r"(?<![\w.])([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)+=\s*\{")
_IDENT = re.compile(r"(?<![\w.])([A-Za-z_]\w*)\b")


def _scan_tables(c_files: dict[str, _CFile], raw: dict[str, str], by_name: dict[str, list[ct._Entry]],
                 labels_by_pos: dict[str, list[tuple[int, str]]]) -> dict[str, list[tuple[str, list[tuple[str, str]]]]]:
    """Tabelas de texto: `NOME[...] = { ... }` com rótulos de texto (`gText_X`) ou literais `_("...")`
    dentro. Cada tabela guarda (arquivo, membros (arquivo do texto, rótulo))."""
    tables: dict[str, list[tuple[str, list[tuple[str, str]]]]] = defaultdict(list)
    for rel, cf in c_files.items():
        src = cf.source
        for m in _TABLE_START.finditer(src):
            start = m.end() - 1
            end = _match_close(src, start, "{", "}")
            members: list[tuple[str, str]] = []
            for pos, label in labels_by_pos.get(rel, ()):
                if start <= pos < end:
                    members.append((rel, label))
            body = src[start:end]
            body_no_str = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', body)
            for im in _IDENT.finditer(body_no_str):
                name = im.group(1)
                if name in by_name:
                    for e in by_name[name]:
                        if not (name.startswith("s") and e.file.endswith(".c") and e.file != rel
                                and any(x.file == rel for x in by_name[name])):
                            members.append((e.file, e.label))
            if members:
                tables[m.group(1)].append((rel, list(dict.fromkeys(members))))
    return tables


def _lookup(by_name: dict[str, list[ct._Entry]], name: str, file: str | None) -> list[ct._Entry]:
    """Textos com este nome vistos de `file`: o static (`sText_X`) do próprio arquivo vence; um static
    de outro .c não é visível."""
    found = by_name.get(name, [])
    if file is not None:
        same = [e for e in found if e.file == file]
        if same:
            return same
        if name.startswith("s") and file.endswith(".c"):
            return [e for e in found if not e.file.endswith(".c")]
    return found


# ---- partes do conteúdo copiado ------------------------------------------------------------

class Part(NamedTuple):
    """Um pedaço do que vai para o buffer.

    kind "text": um dos rótulos/tabelas de `names` (vistos de `file`); `field` filtra os membros
      `X.campo` de uma tabela de structs; `offset` desconta bytes pulados (`gX + 2`);
    kind "items": nome de item como CopyItemName o monta (src/item.c:73-84); `names` = padrões fnmatch
      dos rótulos do items.json ("ITEM_POTION.name", "ITEM_*_BERRY.name"; vazio = todos);
    kind "mapsec": nome de lugar (GetMapName, src/region_map.c:3801-3826): `names` = ids
      MAPSEC_* (vazio = todos);
    kind "files": todo texto dos arquivos `names` (fnmatch), ex.: as palavras do Easy Chat;
    kind "fixed": `nbytes` bytes que não se traduzem (número, letra posta pelo C), `desc` explica;
      `nbytes` pode ser uma expressão do C ("BERRY_NAME_LENGTH").
    `times`: a parte se repete (lista de nomes com separador)."""
    kind: str
    names: tuple[str, ...] = ()
    file: str | None = None
    field: str | None = None
    offset: int = 0
    nbytes: int | str = 0
    desc: str = ""
    times: int = 1


def Text(*names: str, file: str | None = None, field: str | None = None, offset: int = 0, times: int = 1) -> Part:
    return Part("text", tuple(names), file, field, offset, times=times)


def Fixed(nbytes: int | str, desc: str, times: int = 1) -> Part:
    return Part("fixed", nbytes=nbytes, desc=desc, times=times)


def Files(*patterns: str) -> Part:
    return Part("files", tuple(patterns))


ITEMS = Part("items", desc="nome de item (CopyItemName)")
BERRIES = Part("items", ("ITEM_*_BERRY.name",), desc="nome de fruta (CopyItemName)")
EC_WORDS = Part("files", ("src/data/easy_chat/easy_chat_group_*.h",), desc="palavra do Easy Chat")


def Mapsec(*ids: str) -> Part:
    return Part("mapsec", tuple(ids))


class BufRef(NamedTuple):
    """Onde o buffer é declarado: o array `name` local da função `func` de `file`, static de `file`,
    global ou campo de struct (nessa ordem). Com `size` (expressão do C), um limite que não é um
    array (o `n` de um StringAppendN, o apelido de POKEMON_NAME_LENGTH + 1), citado em `site`."""
    name: str
    file: str | None = None
    func: str | None = None
    size: str | None = None
    site: str = ""


# Funções que copiam texto para um buffer: nome -> (tipo, índice do destino, índice da origem)
_COPY_CALLS = {
    "StringCopy": ("copy", 0, 1),
    "StringCopyN": ("copy", 0, 1),
    "StringCopyPadded": ("padded", 0, 1),
    "StringAppend": ("append", 0, 1),
    "StringAppendN": ("append", 0, 1),
    "StringExpandPlaceholders": ("string", 0, 1),
    "DynamicPlaceholderTextUtil_ExpandPlaceholders": ("dynamic", 0, 1),
    "CopyItemName": ("item", 1, None),
    "GetMapName": ("mapsec", 0, None),
    "GetMapNameGeneric": ("mapsec", 0, None),
    "GetMapNameGeneric_": ("mapsec", 0, None),
    # palavra do Easy Chat ou "???" (src/easy_chat.c:166-185)
    "CopyEasyChatWord": ("ecword", 0, None),
    # frase do Easy Chat: colunas x linhas de palavras com espaço/quebra (src/easy_chat.c:188-213);
    # nunca automática: o número de palavras vem dos argumentos, então a frase é declarada
    "ConvertEasyChatWordsToString": ("ecphrase", 0, None),
    # texto de batalha com os {B_*} expandidos (src/battle_message.c:1779-1782): o ...ToDisplayedString
    # escreve sempre em gDisplayedStringBattle[300] (src/battle_main.c:123)
    "BattleStringExpandPlaceholdersToDisplayedString": ("battle", None, 0),
    "BattleStringExpandPlaceholders": ("battle", 1, 0),
    # guarda o ponteiro e o aviso de mapa copia depois para mapName[25] (src/map_name_popup.c:241-247, :198-200)
    "ShowFieldMessagePopup": ("pointer", None, 0),
}
_CALL_RE = re.compile(r"(?<![\w.>])(" + "|".join(sorted(_COPY_CALLS, key=len, reverse=True)) + r")\s*\(")
# Placeholders que cada função expande: StringExpandPlaceholders (GetExpandedPlaceholder,
# src/string_util.c) e DynamicPlaceholderTextUtil_ExpandPlaceholders (só o F7 n,
# src/dynamic_placeholder_text_util.c:97-110); os outros códigos são copiados como estão.
EXPANDS = {
    "string": frozenset({"PLAYER", "RIVAL", "STR_VAR_1", "STR_VAR_2", "STR_VAR_3", "UNKNOWN_STR", "KUN",
                         "VERSION", "EVIL_TEAM", "GOOD_TEAM", "EVIL_LEADER", "GOOD_LEADER", "EVIL_LEGENDARY",
                         "GOOD_LEGENDARY"}),
    "dynamic": frozenset({"DYNAMIC"}),
    # BattleStringExpandPlaceholders (src/battle_message.c:1829-2204): os nomes e buffers de batalha
    "battle": frozenset({*ct.DYNAMIC_LETTERS, *ct._PREFIXED, *ct._PREFIX_ONLY, "B_BUFF1", "B_BUFF2", "B_BUFF3",
                         "B_COPY_VAR_1", "B_COPY_VAR_2", "B_COPY_VAR_3", "B_26"}),
}
# chamadas que entram no inventário mesmo com a origem não resolvida (a declaração diz o texto)
_ALWAYS_LISTED = ("battle", "pointer")


class Call(NamedTuple):
    file: str
    line: int
    func: str | None
    fname: str              # função chamada (StringCopy...)
    kind: str
    dest: str               # argumento de destino ("" quando não há)
    src: str                # argumento de origem ("" quando não há)
    chained: bool           # o retorno é usado (ptr = StringCopy(...), return, argumento): concatenação

    @property
    def site(self) -> str:
        return f"{self.file}:{self.line}"

    @property
    def text(self) -> str:
        args = ", ".join(a for a in (self.dest, self.src) if a)
        return f"{self.fname}({args})"


def _calls(cf: _CFile) -> list[Call]:
    out = []
    src = cf.source
    for m in _CALL_RE.finditer(src):
        name = m.group(1)
        kind, di, si = _COPY_CALLS[name]
        open_paren = m.end() - 1
        close = _match_close(src, open_paren)
        args = _split_args(src[open_paren + 1:close - 1])
        before = src[max(0, m.start() - 40):m.start()].rstrip()
        # a definição/declaração da própria função (u8 *StringCopy(u8 *dest, ...)) não é chamada
        if re.search(r"(?:\bu8|\bvoid|\bconst|\bbool8|\bbool32|\bu16|\bu32|\bs32)\s*\**\s*$", before):
            continue
        chained = bool(re.search(r"(?<![=!<>])=$|\breturn$|[(,]$", before))
        f = cf.function_at(m.start())
        if name == "BattleStringExpandPlaceholdersToDisplayedString":
            args, di = args + ["gDisplayedStringBattle"], len(args)
        out.append(Call(cf.rel, cf.line(m.start()), f[0] if f else None, name, kind,
                        args[di] if di is not None and di < len(args) else "",
                        args[si] if si is not None and si < len(args) else "", chained))
    return out


_CAST = re.compile(r"^\(\s*(?:const\s+)?u8\s*\*\s*\)\s*")


def _clean(expr: str) -> str:
    e = _CAST.sub("", expr.strip())
    e = e.lstrip("&").strip()
    if e.startswith("(") and e.endswith(")") and _match_close(e, 0) == len(e):
        e = e[1:-1].strip()
    return e


def _indexed(e: str) -> tuple[str, str | None] | None:
    """`TABELA[i]...[j](.campo)?` -> (TABELA, campo), com índices aninhados
    (`gStatNamesTable[sStatsToRaise[statIdx]]`); None se não for isso."""
    m = re.match(r"([A-Za-z_]\w*)\s*", e)
    if not m or m.end() >= len(e) or e[m.end()] != "[":
        return None
    i = m.end()
    while i < len(e) and e[i] == "[":
        i = _match_close(e, i, "[", "]")
        while i < len(e) and e[i].isspace():
            i += 1
    rest = e[i:]
    if not rest:
        return m.group(1), None
    f = re.fullmatch(r"\.\s*([A-Za-z_]\w*)", rest)
    return (m.group(1), f.group(1)) if f else None


_LOCAL_TYPES = r"\b(?:u8|s8|u16|s16|u32|s32|bool8|bool32|char|int)\b"


def _is_local(name: str, file: str, func: str | None, ctx: _Ctx) -> bool:
    """`name` é variável local ou parâmetro da função (`u8 *text`, `const u8 *name`)?"""
    cf = ctx.c_files.get(file)
    f = next((f for f in cf.functions if f[0] == func), None) if cf and func else None
    if f is None:
        return False
    region = cf.source[f[3]:f[2]]
    return re.search(_LOCAL_TYPES + r"[\s\w*]*?\b" + re.escape(name) + r"\s*[\[;=,)]", region) is not None


def _source_part(expr: str, file: str, ctx: _Ctx, func: str | None = None) -> Part | None:
    """A parte de texto traduzível que a expressão de origem copia, ou None (nome do jogador, save,
    outro buffer...)."""
    e = _clean(expr)
    m = re.fullmatch(r"([A-Za-z_]\w*)\s*(?:\+\s*(\d+))?", e)
    if m:
        name, off = m.group(1), int(m.group(2) or 0)
        if _lookup(ctx.by_name, name, file) and not _is_local(name, file, func, ctx):
            return Text(name, file=file, offset=off)
        return None
    # entrada com índice constante de tabela com designadores: gBattleStringsTable[STRINGID_X - BASE]
    m = re.fullmatch(r"([A-Za-z_]\w*)\s*\[\s*([A-Z_][A-Z0-9_]*)\s*(?:-\s*\w+\s*)?\]", e)
    if m and m.group(2) in ctx.designated.get(m.group(1), {}):
        defs = ctx.tables.get(m.group(1))
        return Text(ctx.designated[m.group(1)][m.group(2)], file=defs[0][0] if defs else file)
    indexed = _indexed(e)
    if indexed and indexed[0] in ctx.tables:
        part = Text(indexed[0], file=file, field=indexed[1])
        return part if _alts(part, ctx, "") else None
    if re.fullmatch(r"ItemId_GetName\s*\(.*\)", e):
        return ITEMS
    return None


# ---- alternativas e bytes ------------------------------------------------------------------

def text_bytes(text: str, env: ct._Env, expand: frozenset[str] = frozenset(),
               sizes: dict[str, ct.VarSize] | None = None, prefix_bytes: int = 0) -> int:
    """Bytes que o texto ocupa no buffer, sem o EOS. Acentuada = 1 byte; placeholder = os bytes do
    charmap, menos os que a função de cópia expande (`expand`), que medem o pior caso: {PLAYER}/
    {RIVAL} 7 letras, os de VAR_SIZES (`sizes`) o tamanho declarado."""
    sizes = sizes if sizes is not None else ct.VAR_SIZES
    n = 0
    for kind, value in ct._tokenize(text):
        if kind == "break":
            n += 1
        elif kind == "char":
            if value == "$":
                break           # EOS: o resto não é copiado
            n += env.char_bytes.get(value, 1)
        elif kind == "ph":
            words = value.split()
            if words and words[0] in expand:
                if words[0] in ct._PREFIXED:          # "Wild "/"Foe " + apelido
                    n += prefix_bytes + ct._MON
                elif words[0] in ct._PREFIX_ONLY:
                    n += prefix_bytes
                elif words[0] in ct.DYNAMIC_LETTERS:
                    n += ct.DYNAMIC_LETTERS[words[0]]
                elif words[0] in sizes:
                    n += sizes[words[0]].chars
                continue
            for word in words:
                if word in env.name_bytes:
                    n += env.name_bytes[word]
                elif ct._NUMBER.match(word):
                    n += 1
        else:
            n += 1
    return n


def _entry_bytes(entry: ct._Entry, texts: tuple[str, ...], ctx: _Ctx, expand: str, offset: int) -> int:
    words = EXPANDS.get(expand, frozenset())
    sizes = ct.var_sizes(entry.file, entry.label) if words else None
    return max(text_bytes(t, ctx.env, words, sizes, ctx.prefix_bytes) for t in texts) - offset


def _alt_of(entry: ct._Entry, ctx: _Ctx, expand: str, offset: int = 0) -> Alt:
    base = ctx.base_texts(entry)
    return Alt(f"{entry.file}: {entry.label}", _entry_bytes(entry, entry.texts, ctx, expand, offset),
               _entry_bytes(entry, base, ctx, expand, offset) if base else None, (entry.file, entry.label))


def _table_members(name: str, file: str | None, ctx: _Ctx) -> list[tuple[str, str]] | None:
    defs = ctx.tables.get(name)
    if not defs:
        return None
    same = [m for f, m in defs if f == file]
    if same:
        return same[0]
    # static de um .h incluído (src/data/party_menu.h em src/party_menu.c): vale se for o único
    if name.startswith("s") and len(defs) > 1:
        return None
    return defs[0][1]


def _alts(part: Part, ctx: _Ctx, expand: str) -> list[Alt]:
    key = (part, expand)
    if key not in ctx.alts_cache:
        ctx.alts_cache[key] = _compute_alts(part, ctx, expand)
    return ctx.alts_cache[key]


def _compute_alts(part: Part, ctx: _Ctx, expand: str) -> list[Alt]:
    if part.kind == "fixed":
        n = part.nbytes if isinstance(part.nbytes, int) else (eval_size(part.nbytes, ctx.defines) or 0)
        return [Alt(part.desc, n, n)]
    if part.kind == "files":
        return [_alt_of(e, ctx, expand) for e in ctx.entries
                if any(fnmatch.fnmatchcase(e.file, pat) for pat in part.names)]
    if part.kind == "items":
        def wanted(label: str) -> bool:
            return not part.names or any(fnmatch.fnmatchcase(label, pat) for pat in part.names)

        alts = [_alt_of(e, ctx, expand) for e in ctx.entries
                if e.file == ct._ITEMS and e.label.endswith(".name") and not e.label.startswith("ITEM_ENIGMA_BERRY.")
                and wanted(e.label)]
        letters = eval_size("BERRY_NAME_LENGTH", ctx.defines) or 0
        for e in (_lookup(ctx.by_name, "gText_Berry", "src/item.c") if wanted("ITEM_ENIGMA_BERRY.name") else ()):
            # Fruta Enigma: gText_Berry + o nome da fruta do e-Reader (src/item.c:75-79)
            a = _alt_of(e, ctx, expand)
            alts.append(Alt(f"{a.name} + nome da fruta Enigma ({letters} letras, BERRY_NAME_LENGTH)",
                            a.cur + letters, None if a.base is None else a.base + letters, a.key))
        return alts
    if part.kind == "mapsec":
        wanted = set(part.names)
        return [_alt_of(e, ctx, expand) for e in ctx.entries
                if e.file == ct._REGION_MAP and (not wanted or e.label in wanted)]
    alts: list[Alt] = []
    for name in part.names:
        members = _table_members(name, part.file, ctx)
        if members is not None:
            entries = [ctx.by_key[k] for k in members if k in ctx.by_key]
            if part.field:
                entries = [e for e in entries if _base_name(e.label).endswith("." + part.field)]
        else:
            entries = _lookup(ctx.by_name, name, part.file)
        alts += [_alt_of(e, ctx, expand, part.offset) for e in entries]
    return list({a.key or a.name: a for a in alts}.values())


# ---- caminhos ---------------------------------------------------------------------------------

class BufferPath(NamedTuple):
    site: str                  # arquivo:linha de onde a cópia acontece
    what: str                  # a chamada ou o comando de script
    buffer: Buffer
    parts: tuple[Part, ...]
    expand: str = ""           # "" (cópia crua), "string" ou "dynamic" (placeholders expandidos)
    origin: str = "auto"       # "script", "auto", "declarado", "aviso"
    why: str = ""


class Declared(NamedTuple):
    """Caminho do C que a varredura automática não mede sozinha (concatenação, destino ponteiro) ou
    que fica sem medida. Casa com as chamadas de `file` (fnmatch) e da função `func` (regex inteira)
    cuja origem e destino (sem espaços nem cast) casam com `src`/`dest` (regex inteira).
    `buffer` None = não medido, com o motivo em `why`. Com `parts`, um caminho composto (a soma das
    partes); sem `parts`, cada chamada casada é medida com o próprio texto no `buffer` declarado
    (o destino é um ponteiro que o código prova ser aquele buffer)."""
    file: str
    func: str
    src: str
    buffer: BufRef | None
    parts: tuple[Part, ...] = ()
    why: str = ""
    expand: str = ""
    dest: str = r".*"


def _resolve_buffer(ref: BufRef, ctx: _Ctx, indexed: bool = False) -> Buffer | None:
    """`indexed`: o destino é `x[i]`, que só é um buffer inteiro se `x` for `u8 x[N][M]` (num array
    de uma dimensão, `x[i]` é um ponteiro para o meio dele)."""
    name = ref.name
    if ref.size is not None:
        size = eval_size(ref.size, ctx.defines)
        return Buffer(name, size, ref.site) if size else None

    def ok(expr: str, two: bool) -> int | None:
        return eval_size(expr, ctx.defines) if two or not indexed else None

    if ref.file and ref.func:
        cf = ctx.c_files.get(ref.file)
        if cf:
            for fname, start, end, _h in cf.functions:
                if fname != ref.func:
                    continue
                for m in _ARRAY_DECL.finditer(cf.source, start, end):
                    if m.group(1) == name:
                        size = ok(m.group(3) or m.group(2), m.group(3) is not None)
                        if size:
                            return Buffer(name, size, f"{ref.file}:{cf.line(m.start())}")
    if ref.file and (ref.file, name) in ctx.arrays.statics:
        expr, line, two = ctx.arrays.statics[(ref.file, name)]
        size = ok(expr, two)
        if size:
            return Buffer(name, size, f"{ref.file}:{line}")
    if name in ctx.arrays.globals:
        found = [(ok(e, two), f, line) for f, e, line, two in ctx.arrays.globals[name]]
        found = [x for x in found if x[0]]
        if found:
            size, f, line = min(found)        # #if com dois tamanhos: vale o menor
            return Buffer(name, size, f"{f}:{line}")
    if name in ctx.arrays.fields:
        fields = [x for x in ctx.arrays.fields[name] if not ref.file or ref.func or x[0] == ref.file]
        found = sorted({(ok(e, two), f, line) for f, e, line, two in fields},
                       key=lambda x: (x[0] is None, x[0] or 0, x[1], x[2]))
        sizes = {s for s, _f, _l in found}
        if len(sizes) == 1 and None not in sizes:
            size, f, line = found[0]
            return Buffer(name, size, f"{f}:{line}")
    return None


def _dest_buffer(call: Call, ctx: _Ctx) -> Buffer | None:
    """O array de tamanho fixo que a chamada escreve, se o destino for um nome de array (local,
    static, global) ou um campo de struct com tamanho único; None para ponteiro."""
    e = _clean(call.dest)
    m = re.fullmatch(r"([A-Za-z_]\w*)(\s*\[\s*0\s*\])?", e)
    if m:
        return _resolve_buffer(BufRef(m.group(1), call.file, call.func), ctx)
    m = re.fullmatch(r"([A-Za-z_]\w*)\s*\[[^\]]*\]", e)
    if m:
        return _resolve_buffer(BufRef(m.group(1), call.file, call.func), ctx, indexed=True)
    m = re.fullmatch(r".*(?:\.|->)\s*([A-Za-z_]\w*)\s*(\[[^\]]*\])?", e)
    if m:
        return _resolve_buffer(BufRef(m.group(1)), ctx, indexed=bool(m.group(2)) and m.group(2).replace(" ", "") != "[0]")
    return None


def _norm(expr: str) -> str:
    return re.sub(r"\s+", "", _clean(expr))


# ---- contexto ---------------------------------------------------------------------------------

def _c_file(rel: str, raw: str, labels_by_pos: dict[str, list[tuple[int, str]]]) -> _CFile:
    blank = _blank_comments(raw)
    if "_(" in raw:
        labels_by_pos[rel] = [(pos, e.label) for (pos, _t, _b), e in
                              zip(ct._scan_c_strings(raw), ct._extract_c_text(rel, raw))]
    return _CFile(rel, blank, _functions(blank))


def build_context(repo: Path, entries: list[ct._Entry] | None = None, base: ct._Base | None = None,
                  env: ct._Env | None = None) -> _Ctx:
    """Tudo o que a medida precisa: textos atuais (`entries`), base inglesa (`base`; None = estrito),
    fontes C sem comentários, tabelas de texto e arrays."""
    repo = Path(repo)
    env = env or ct._load_env(repo)
    if entries is None:
        entries = [e for e in ct._sources(repo) if isinstance(e, ct._Entry)]
    by_name: dict[str, list[ct._Entry]] = defaultdict(list)
    by_key: dict[tuple[str, str], ct._Entry] = {}
    for e in entries:
        by_key[(e.file, e.label)] = e
        if "#" not in e.label:
            by_name[e.label].append(e)
    c_files: dict[str, _CFile] = {}
    labels_by_pos: dict[str, list[tuple[int, str]]] = {}
    for path in sorted((repo / "src").rglob("*")):
        rel = path.relative_to(repo).as_posix()
        if path.suffix not in (".c", ".h") or rel in ct._C_EXCLUDED or not path.is_file():
            continue
        c_files[rel] = _c_file(rel, path.read_text(encoding="utf-8", errors="replace"), labels_by_pos)
    headers = {p.relative_to(repo).as_posix(): _blank_comments(p.read_text(encoding="utf-8", errors="replace"))
               for p in sorted((repo / "include").rglob("*.h"))}
    tables = _scan_tables(c_files, {}, by_name, labels_by_pos)
    arrays = _scan_arrays({r: cf for r, cf in c_files.items() if r.endswith(".c")}, headers)
    prefix = max((text_bytes(e.texts[0], env) for e in entries
                  if e.file == "src/battle_message.c" and ct._PREFIX_LABEL.match(e.label)), default=0)
    designated: dict[str, dict[str, str]] = {}
    for cf in c_files.values():
        for m in _TABLE_START.finditer(cf.source):
            body = cf.source[m.end():_match_close(cf.source, m.end() - 1, "{", "}")]
            pairs = re.findall(r"\[\s*([A-Z_][A-Z0-9_]*)[^\]\n]*\]\s*=\s*([A-Za-z_]\w*)\s*[,}]", body)
            if pairs:
                designated.setdefault(m.group(1), {}).update({k: v for k, v in pairs if v in by_name})
    return _Ctx(repo, env, entries, base, by_name, tables, c_files, arrays, _defines(repo), by_key, {}, {}, prefix,
                designated)


@lru_cache(maxsize=2)
def repo_context(repo: str) -> _Ctx | None:
    """Contexto do repo com a base inglesa (TRANSLATION_BASE), lido uma vez por processo (os testes de
    várias frentes o dividem); None se a base não estiver disponível."""
    scan = ct._scan(Path(repo), ct.TRANSLATION_BASE)
    return build_context(Path(repo), scan.raw, scan.base, scan.env) if scan.base is not None else None


def with_texts(ctx: _Ctx, changes: dict[tuple[str, str], str], base: ct._Base | None | str = "mesma") -> _Ctx:
    """O mesmo contexto com alguns textos trocados ({(arquivo, rótulo): texto}) e, se dada, outra base:
    para testar uma tradução sem reler o C."""
    entries = [ct._Entry(e.file, e.label, (changes[(e.file, e.label)],), e.needs_terminator, e.braille)
               if (e.file, e.label) in changes else e for e in ctx.entries]
    by_name: dict[str, list[ct._Entry]] = defaultdict(list)
    for e in entries:
        if "#" not in e.label:
            by_name[e.label].append(e)
    same_base = isinstance(base, str)
    if same_base and ctx.base is not None:
        # arquivo que era igual à base passa a ser "mudado": o texto de antes é a base dele
        newly = {f for f, _l in changes if f not in ctx.base.changed and f in ctx.base.present}
        if newly:
            texts = dict(ctx.base.texts)
            texts.update({(e.file, e.label): e.texts for e in ctx.entries if e.file in newly})
            base, same_base = ct._Base(texts, ctx.base.changed | newly, ctx.base.present), False
    # as alternativas já medidas que não usam nenhum texto trocado continuam valendo (com a mesma base)
    cache = ({k: v for k, v in ctx.alts_cache.items() if not any(a.key in changes for a in v)}
             if same_base else {})
    return _Ctx(ctx.repo, ctx.env, entries, ctx.base if same_base else base, by_name, ctx.tables,
                ctx.c_files, ctx.arrays, ctx.defines, {(e.file, e.label): e for e in entries}, cache, ctx.files,
                ctx.prefix_bytes, ctx.designated)


# ---- caminhos dos scripts ----------------------------------------------------------------------

_SCRIPT_CMD = re.compile(r"^[ \t]*(bufferstdstring|bufferstring|vbufferstring|bufferitemname|bufferitemnameplural|"
                         r"buffermovename)[ \t]+([A-Za-z_0-9]+)[ \t]*,[ \t]*([A-Za-z_0-9]+)", re.M)


def _script_files(ctx: _Ctx) -> list[str]:
    return (ctx.listing("data/maps/*/scripts.inc") + ctx.listing("data/scripts/*.inc")
            + ctx.listing("data/event_scripts.s"))


def _string_var(arg: str) -> str | None:
    m = re.fullmatch(r"STR_VAR_([123])|([012])", arg)
    if not m:
        return None
    return SCRIPT_STRING_VARS[int(m.group(1)) - 1 if m.group(1) else int(m.group(2))]


def _std_string_labels(ctx: _Ctx) -> dict[str, str]:
    """STDSTRING_X -> rótulo, pelos designadores de gStdStringPtrs (src/script_menu.c)."""
    cf = ctx.c_files.get("src/script_menu.c")
    if not cf:
        return {}
    m = re.search(r"gStdStringPtrs\[\]\s*=\s*\{", cf.source)
    if not m:
        return {}
    body = cf.source[m.end():_match_close(cf.source, m.end() - 1, "{", "}")]
    return dict(re.findall(r"\[\s*(STDSTRING_\w+)\s*\]\s*=\s*(\w+)", body))


def script_paths(ctx: _Ctx) -> list[BufferPath]:
    """Um caminho por comando de script que copia texto traduzível para STR_VAR_n."""
    std = _std_string_labels(ctx)
    out = []
    for rel in _script_files(ctx):
        text = ctx.read(rel)
        for m in _SCRIPT_CMD.finditer(text):
            cmd, var, arg = m.groups()
            var_name = _string_var(var)
            buf = _resolve_buffer(BufRef(var_name), ctx) if var_name else None
            if buf is None:
                continue
            if cmd == "bufferstdstring":
                parts: tuple[Part, ...] = (Text(std.get(arg, "gStdStringPtrs"), file="src/script_menu.c"),)
                why = "ScrCmd_bufferstdstring: StringCopy(sScriptStringVars[i], gStdStringPtrs[index]) (src/scrcmd.c)"
            elif cmd in ("bufferstring", "vbufferstring"):
                parts = (Text(arg, file=rel),)
                why = f"ScrCmd_{cmd}: StringCopy(sScriptStringVars[i], texto) (src/scrcmd.c)"
            elif cmd in ("bufferitemname", "bufferitemnameplural"):
                parts = (Part("items", (f"{arg}.name",)) if arg.startswith("ITEM_") else ITEMS,)
                why = "ScrCmd_bufferitemname: CopyItemName (src/scrcmd.c, src/item.c:73-84)"
                if cmd == "bufferitemnameplural":
                    # Poké Bola + "S" ou fruta com a última letra trocada por "IES"
                    # (ScrCmd_bufferitemnameplural, src/scrcmd.c): pior caso = nome + o sufixo mais comprido
                    parts += (Text("sText_S", "sText_IES", file="src/scrcmd.c"),)
                    why = ("ScrCmd_bufferitemnameplural: CopyItemName + sText_S/sText_IES (src/scrcmd.c); "
                           "pior caso = nome + o sufixo mais comprido")
            else:  # buffermovename
                parts = (Text(arg if arg.startswith("MOVE_") else "gMoveNames", file="src/data/text/move_names.h"),)
                why = "ScrCmd_buffermovename: StringCopy(sScriptStringVars[i], gMoveNames[move]) (src/scrcmd.c)"
            line = text.count("\n", 0, m.start()) + 1
            out.append(BufferPath(f"{rel}:{line}", f"{cmd} {var}, {arg}", buf, parts, "", "script", why))
    # a tabela inteira contra o menor STR_VAR: o índice do bufferstdstring pode vir de uma var e um script
    # novo pode usar qualquer entrada (era o que test_traducao_e.py media antes da T4)
    cf = ctx.c_files.get("src/script_menu.c")
    m = re.search(r"gStdStringPtrs\[\]\s*=", cf.source) if cf else None
    small = [b for b in (_resolve_buffer(BufRef(v), ctx) for v in SCRIPT_STRING_VARS) if b]
    if m and small:
        out.append(BufferPath(f"src/script_menu.c:{cf.line(m.start())}", "bufferstdstring STR_VAR_n, qualquer STDSTRING_*",
                              min(small, key=lambda b: b.size), (Text("gStdStringPtrs", file="src/script_menu.c"),),
                              "", "script", "toda entrada de gStdStringPtrs cabe no menor gStringVarN"))
    return out


# ---- aviso de nome de mapa (src/map_name_popup.c) --------------------------------------------

FLOOR_ROOFTOP = 127


def _celadon_store_maps(ctx: _Ctx) -> set[str]:
    """Mapas onde GetMapName usa o nome especial da loja (IsCeladonDeptStoreMapsec, src/region_map.c)."""
    cf = ctx.c_files.get("src/region_map.c")
    m = re.search(r"IsCeladonDeptStoreMapsec\s*\([^)]*\)\s*\{", cf.source) if cf else None
    if not m:
        return set()
    body = cf.source[m.end():_match_close(cf.source, m.end() - 1, "{", "}")]
    return set(re.findall(r"MAP_NUM\((MAP_\w+)\)", body))


def popup_paths(ctx: _Ctx) -> list[BufferPath]:
    """MapNamePopupPrintMapNameOnWindow: u8 mapName[25] = GetMapName + MapNamePopupAppendFloorNum
    (" " + "B"? + até 2 algarismos + "F", ou " " + gText_Rooftop2), sem limite de cópia. Um caminho
    por mapa com andar e aviso (`show_map_name`)."""
    buf = _resolve_buffer(BufRef("mapName", "src/map_name_popup.c", "MapNamePopupPrintMapNameOnWindow"), ctx)
    if buf is None:
        return []
    store = _celadon_store_maps(ctx)
    out = []
    for rel in ctx.listing("data/maps/*/map.json"):
        data = json.loads(ctx.read(rel))
        floor = data.get("floor_number", 0)
        if not floor or not data.get("show_map_name", True):
            continue
        mapsec = data.get("region_map_section", "")
        if mapsec == "MAPSEC_CELADON_CITY" and data.get("id") in store:
            mapsec = "MAPSEC_SPECIAL_AREA"      # GetMapName usa sMapsecName_MAPSEC_SPECIAL_AREA
        if floor == FLOOR_ROOFTOP:
            suffix = Text("gText_Rooftop2", file="src/map_name_popup.c")
        else:
            floor_text = ("B" if floor < 0 else "") + f"{abs(floor)}F"
            suffix = Fixed(len(floor_text), f"andar \"{floor_text}\"")
        out.append(BufferPath(rel, f"aviso de mapa de {data.get('name')} (andar {floor})", buf,
                              (Mapsec(mapsec), Fixed(1, "espaço"), suffix), "", "aviso",
                              "MapNamePopupPrintMapNameOnWindow/MapNamePopupAppendFloorNum (src/map_name_popup.c)"))
    return out


# ---- caminhos do C ------------------------------------------------------------------------------

class Classified(NamedTuple):
    call: Call
    status: str                 # "auto", "declarado", "isento" ou "pendente" (falta declaração)
    buffer: Buffer | None       # o destino, quando é um array de tamanho conhecido
    part: Part | None           # o texto traduzível copiado (None: só concatena num destino traduzível)
    declared: tuple[Declared, ...] = ()


def _content_part(call: Call, ctx: _Ctx) -> Part | None:
    if call.kind == "item":
        return ITEMS
    if call.kind == "mapsec":
        return Mapsec()
    if call.kind in ("ecword", "ecphrase"):
        return EC_WORDS
    return _source_part(call.src, call.file, ctx, call.func)


def declared_matches(d: Declared, call: Call) -> bool:
    return (fnmatch.fnmatchcase(call.file, d.file) and re.fullmatch(d.func, call.func or "") is not None
            and re.fullmatch(d.src, _norm(call.src)) is not None
            and re.fullmatch(d.dest, _norm(call.dest)) is not None)


def classify_calls(ctx: _Ctx, declared: list[Declared] | None = None) -> list[Classified]:
    """Toda chamada de cópia do C que leva texto traduzível para um buffer, com a sua situação:
    `auto` (medida sozinha: cópia única num array de tamanho conhecido), `declarado`/`isento` (casou
    com DECLARED) ou `pendente` (precisa de declaração: concatenação, destino ponteiro). Entra também
    a concatenação (StringAppend) num destino que, na mesma função, recebe texto traduzível. As cópias
    sem texto traduzível (nome do jogador, save, número) não entram."""
    declared = DECLARED if declared is None else declared
    out: list[Classified] = []
    for _rel, cf in sorted(ctx.c_files.items()):
        calls = _calls(cf)
        parts = {c: _content_part(c, ctx) for c in calls}
        appended = {(c.func, _norm(c.dest)) for c in calls if c.kind == "append"}
        translatable = {(c.func, _norm(c.dest)) for c in calls if parts[c] is not None}
        for c in calls:
            part = parts[c]
            key = (c.func, _norm(c.dest))
            if part is None and not (c.kind == "append" and key in translatable) and c.kind not in _ALWAYS_LISTED:
                continue
            decs = tuple(d for d in declared if declared_matches(d, c))
            buf = _dest_buffer(c, ctx) if c.dest else None
            if decs:
                status = "declarado" if any(d.buffer for d in decs) else "isento"
            elif (part is not None and buf is not None and c.kind not in ("append", "ecphrase") and not c.chained
                  and key not in appended):
                status = "auto"
            else:
                status = "pendente"
            out.append(Classified(c, status, buf, part, decs))
    return out


def c_paths(ctx: _Ctx, classified: list[Classified] | None = None,
            declared: list[Declared] | None = None) -> list[BufferPath]:
    """Os automáticos, um por chamada, e os declarados: com `parts`, um caminho composto por entrada;
    sem `parts`, um por chamada casada, com o texto da própria chamada no buffer declarado."""
    declared = DECLARED if declared is None else declared
    classified = classify_calls(ctx, declared) if classified is None else classified
    out = []
    for cl in classified:
        if cl.status == "auto":
            expand = cl.call.kind if cl.call.kind in EXPANDS else ""
            out.append(BufferPath(cl.call.site, cl.call.text, cl.buffer, (cl.part,), expand, "auto"))
    # (com origem não resolvida, a chamada de _ALWAYS_LISTED fica pendente até ser declarada)
    for d in declared:
        if d.buffer is None:
            continue
        matched = [cl for cl in classified if d in cl.declared]
        buf = _resolve_buffer(d.buffer, ctx)
        if not matched or buf is None:
            continue
        if d.parts:
            first = matched[0].call
            out.append(BufferPath(first.site, first.text, buf, d.parts, d.expand, "declarado", d.why))
            continue
        for cl in matched:
            if cl.part is None:
                continue
            expand = d.expand or (cl.call.kind if cl.call.kind in EXPANDS else "")
            out.append(BufferPath(cl.call.site, cl.call.text, buf, (cl.part,), expand, "declarado", d.why))
    return out


def buffer_paths(ctx: _Ctx) -> list[BufferPath]:
    """Todos os caminhos medidos: scripts, C (automáticos e declarados) e o aviso de mapa."""
    return script_paths(ctx) + c_paths(ctx) + popup_paths(ctx)


# ---- medida e critério da base --------------------------------------------------------------------

class Measure(NamedTuple):
    alt: Alt                    # a alternativa que define o total
    total: int                  # bytes com o EOS, esta alternativa + o maior das outras partes
    base_total: int | None      # pior caso do caminho na base inglesa (None = rótulo novo ou sem base)
    content: str                # a composição, para o relatório


def measure_path(path: BufferPath, ctx: _Ctx) -> list[Measure] | None:
    """Total no pior caso de cada alternativa de cada parte; None se alguma parte não resolveu.
    Base: num caminho de um texto só, o mesmo rótulo em inglês; num caminho composto (texto + texto,
    palavra x3), o pior caso do caminho com os textos ingleses. Rótulo novo (sem inglês) não tem base."""
    parts = [(p, _alts(p, ctx, path.expand)) for p in path.parts]
    if any(not alts for _p, alts in parts):
        return None
    cur_max = [max(a.cur for a in alts) * p.times for p, alts in parts]
    has_base = all(any(a.base is not None for a in alts) for _p, alts in parts)
    path_base = (sum(max(a.base for a in alts if a.base is not None) * p.times for p, alts in parts) + 1
                 if has_base else None)
    widest = [max(alts, key=lambda a: a.cur).name for _p, alts in parts]
    out = []
    for i, (p, alts) in enumerate(parts):
        others_cur = sum(cur_max) - cur_max[i]
        for a in alts:
            total = a.cur * p.times + others_cur + 1
            # caminho de um texto só: a base é o próprio rótulo em inglês; composto: o pior caso do caminho
            single = len(parts) == 1 and p.times == 1
            base_total = None if a.base is None else (a.base + 1 if single else path_base)
            names = [a.name if j == i else widest[j] for j in range(len(parts))]
            names = [f"{n} (x{q.times})" if q.times > 1 else n for n, (q, _a) in zip(names, parts)]
            out.append(Measure(a, total, base_total, " + ".join(names)))
    return out


def overflows(path: BufferPath, ctx: _Ctx) -> list[Measure]:
    """Alternativas que estouram o buffer e passam da base inglesa (measure_path: o próprio rótulo, ou
    o pior caso do caminho composto); o inglês que já estoura não reprova a tradução que estoura igual
    ou menos; rótulo novo não pode estourar."""
    found = []
    for m in measure_path(path, ctx) or ():
        if m.total > path.buffer.size and (m.base_total is None or m.total > m.base_total):
            found.append(m)
    return found


def _content_files(path: BufferPath, ctx: _Ctx) -> set[str]:
    files = set()
    for p in path.parts:
        for a in _alts(p, ctx, path.expand):
            if a.key:
                files.add(a.key[0])
    return files


class Known(NamedTuple):
    """Estouro que já está na hack-switch e tem dono: vira `aviso` (não reprova) enquanto o total
    for exatamente este. Corrigido o texto, a entrada vira aviso de obsoleta e sai da lista."""
    file: str
    label: str
    buffer: str
    total: int
    fingerprint: str           # check_text.fingerprint do texto do rótulo quando foi registrado
    why: str


# Achados da T4 já resolvidos: nenhum estouro conhecido (a "Fruta Ocipêra" virou "Fruta Ocipêr", 22/10)
KNOWN_OVERFLOWS: list[Known] = []


def _known(m: Measure, buf: Buffer, known: list[Known], ctx: _Ctx) -> Known | None:
    """O estouro é um conhecido? Mesmo rótulo, buffer e total, e o texto do rótulo igual ao registrado."""
    for k in known:
        entry = ctx.by_key.get((k.file, k.label))
        if (k.buffer == buf.name and k.total == m.total and f"{k.file}: {k.label}" in m.content
                and entry is not None and ct.fingerprint(entry.texts) == k.fingerprint):
            return k
    return None


_CONTEXTS: dict[tuple, _Ctx] = {}


def cached_context(repo: Path, entries: list[ct._Entry], base: ct._Base | None, env: ct._Env | None) -> _Ctx:
    """build_context com cache por processo: a mesma árvore (mesmos textos e a mesma base) reaproveita o C
    já lido. O pytest chama check_text sobre o repo real em vários módulos; sem isso cada chamada relia o C.
    A chave são os textos (o código C sem texto não muda durante um processo)."""
    key = (str(Path(repo).resolve()), hash(tuple((e.file, e.label, e.texts) for e in entries)),
           None if base is None else (frozenset(base.changed), hash(tuple(sorted(base.texts.items())))))
    if key not in _CONTEXTS:
        if len(_CONTEXTS) >= 4:
            _CONTEXTS.pop(next(iter(_CONTEXTS)))
        _CONTEXTS[key] = build_context(Path(repo), entries, base, env)
    return _CONTEXTS[key]


def check_buffers(repo: Path, entries: list[ct._Entry] | None = None, base: ct._Base | None = None,
                  env: ct._Env | None = None, ctx: _Ctx | None = None,
                  known: list[Known] | None = None) -> list[Result]:
    """Regra `buffer`: um Result `falha` por texto que estoura um buffer (agrupando os lugares onde a
    mesma cópia acontece); `aviso` para os de KNOWN_OVERFLOWS. `base` None = estrito (sem a folga da
    base inglesa)."""
    if ctx is None:
        ctx = (cached_context(Path(repo), entries, base, env) if entries is not None
               else build_context(Path(repo), entries, base, env))
    known = KNOWN_OVERFLOWS if known is None else known
    groups: dict[tuple, list[BufferPath]] = defaultdict(list)
    for path in buffer_paths(ctx):
        for m in overflows(path, ctx):
            groups[(path.buffer, m.content, m.total, m.base_total, _known(m, path.buffer, known, ctx))].append(path)
    results = []
    used: set[Known] = set()
    for (buf, content, total, base_total, k), paths in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        sites = list(dict.fromkeys(f"{p.site} ({p.what})" for p in paths))
        shown = ", ".join(sites[:3]) + (f" e mais {len(sites) - 3}" if len(sites) > 3 else "")
        base_note = (f"; a base inglesa já ia a {base_total} bytes" if base_total is not None and base_total > buf.size
                     else "" if base_total is None else f"; a base inglesa ocupava {base_total}")
        detail = (f"estouro de buffer: {content} = {total} bytes com o EOS, mas {buf.name}[{buf.size}] "
                  f"({buf.site}) só tem {buf.size}{base_note}; copiado em {shown}")
        if k is not None:
            used.add(k)
            results.append(Result(f"texto/{RULE_BUFFER}", "aviso", f"{detail} (conhecido: {k.why})"))
        else:
            results.append(Result(f"texto/{RULE_BUFFER}", "falha", detail))
    for k in known:
        if k not in used and (k.file, k.label) in ctx.by_key:   # num repo sem o texto (fixture) não se aplica
            results.append(Result(f"texto/{RULE_BUFFER}", "aviso",
                                  f"estouro conhecido não ocorre mais: {k.file}: {k.label} em {k.buffer} "
                                  f"({k.total} bytes); remova-o de KNOWN_OVERFLOWS (esteira/buffers.py)"))
    return results


def report(ctx: _Ctx, files: Iterable[str] = ()) -> list[str]:
    """Uma linha por caminho medido (os que copiam texto de `files`, ou todos): bytes no pior caso
    contra o tamanho do buffer."""
    wanted = set(files)
    rows = []
    for path in buffer_paths(ctx):
        if wanted and not (_content_files(path, ctx) & wanted):
            continue
        ms = measure_path(path, ctx)
        if not ms:
            rows.append(f"  ???  {path.buffer.name}[{path.buffer.size}]  {path.site}  {path.what}: parte sem texto")
            continue
        worst = max(ms, key=lambda m: m.total)
        bad = overflows(path, ctx)
        flag = "ESTOURA" if bad else ("estoura igual à base" if worst.total > path.buffer.size else "ok")
        rows.append(f"{worst.total:4d}/{path.buffer.size:<4d} {flag:<20} {path.buffer.name}  {path.site}  "
                    f"{path.what}  [{worst.content}]")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m esteira.buffers",
        description="Estouro de buffer de string: mede cada cópia de texto traduzível para um buffer fixo.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--todos", action="store_true", help="lista todos os caminhos medidos, não só os problemas")
    parser.add_argument("arquivos", nargs="*", help="só os caminhos que copiam texto destes arquivos (relativos ao repo)")
    args = parser.parse_args(argv)
    repo = Path(args.repo)

    def relative(arg: str) -> str:
        path = Path(arg)
        try:
            return path.resolve().relative_to(repo.resolve()).as_posix() if path.exists() else arg
        except ValueError:
            return arg

    args.arquivos = [relative(a) for a in args.arquivos]
    scan = ct._scan(repo, ct.TRANSLATION_BASE)
    if scan.base is None:
        print(f"aviso: base inglesa indisponível ({scan.base_note or 'sem .git'}): medida estrita, sem a folga da base")
    ctx = build_context(repo, scan.raw, scan.base, scan.env)
    if args.todos:
        for row in report(ctx, args.arquivos):
            print(row)
    results = check_buffers(repo, ctx=ctx)
    wanted = set(args.arquivos)
    shown = [r for r in results if not wanted or any(f"{f}:" in r.detail for f in wanted)]
    for r in shown:
        print(f"{r.status.upper()} {r.detail}")
    failed = [r for r in shown if r.status == "falha"]
    print(f"{len(failed)} estouro(s) de buffer novo(s)" + (f", {len(shown) - len(failed)} aviso(s)" if len(shown) > len(failed) else "")
          + (f" nos textos de {', '.join(sorted(wanted))}" if wanted else ""))
    return 1 if failed else 0


# ---- inventário dos caminhos do C que a varredura não mede sozinha --------------------------------

_BM = "src/battle_message.c"
_BI = "src/battle_interface.c"
_PSS = "src/pokemon_summary_screen.c"
_UR = "src/union_room.c"
_NICK = Fixed("POKEMON_NAME_LENGTH", "apelido (POKEMON_NAME_LENGTH)")
_PLAYER = Fixed("PLAYER_NAME_LENGTH", "nome do jogador (PLAYER_NAME_LENGTH)")
# MO: sText_ClearTo18 + gText_NumberClear01 + 1 algarismo; MT: gText_NumberClear01 + 2 algarismos
# (src/tm_case.c:680-692): o pior caso é o da MO
_TM_LIST = (Text("gText_FontSmall"), Text("sText_ClearTo18", file="src/tm_case.c"), Text("gText_NumberClear01"),
            Fixed(1, "nº da MO (a MT tem 2 algarismos e não tem o salto)"), Text("sText_SingleSpace", file="src/tm_case.c"),
            Text("gText_FontNormal"), Text("gMoveNames"))
_EVO_LINES = ("gText_PokeSum_EvoLevel", "gText_PokeSum_EvoItem", "gText_PokeSum_EvoLevelHoldItem",
              "gText_PokeSum_EvoFriendship", "gText_PokeSum_EvoFriendshipDay", "gText_PokeSum_EvoFriendshipNight",
              "gText_PokeSum_EvoLevelUpHoldItem", "gText_PokeSum_EvoBeauty", "gText_PokeSum_EvoAtkGtDef",
              "gText_PokeSum_EvoAtkEqDef", "gText_PokeSum_EvoAtkLtDef", "gText_PokeSum_EvoLevelRandom",
              "gText_PokeSum_EvoLevelFreeSlot", "gText_PokeSum_EvoTrade", "gText_PokeSum_EvoTradeItem")
# as strings de mudança de atributo que vão sozinhas para gBattleTextBuff2 (src/battle_message.c:715-718)
STAT_CHANGE_STRINGS = ("sText_StatSharply", "gBattleText_Rose", "sText_StatHarshly", "sText_StatFell")
_UR_DST = ("GetAwaitingCommunicationText|Leader_GetAcceptNewMemberPrompt|GetYouDeclinedTheOfferMessage|"
           "GetYouAskedToJoinGroupPleaseWaitMessage|GetGroupLeaderSentAnOKMessage|GetURoomActivityRejectMsg|"
           "GetURoomActivityStartMsg|GetChatLeaderActionRequestMessage")

DECLARED: list[Declared] = [
    # ---- implementações das funções de cópia: medidas em quem chama -----------------------------
    Declared("src/item.c", "CopyItemName", r".*", None,
             why="implementação de CopyItemName (src/item.c:73-84): cada chamada mede o nome de item (com a "
                 "Fruta Enigma = gText_Berry + nome) no buffer de quem chama"),
    Declared("src/region_map.c", r"GetMapNameGeneric_?", r".*", None,
             why="GetMapNameGeneric(_) só repassam para GetMapName (src/region_map.c:3828-3837): medido em quem chama"),
    Declared("src/scrcmd.c", r"ScrCmd_\w*buffer\w*", r".*", None,
             why="comandos de script (sScriptStringVars, src/scrcmd.c): medidos em cada uso nos scripts "
                 "(script_paths), com o texto e o STR_VAR do comando"),
    Declared("src/map_name_popup.c", r"MapNamePopup\w+", r".*", None,
             why="aviso de nome de mapa: medido por mapa em popup_paths (lugar + andar ou gText_Rooftop2 em mapName[25])"),
    Declared("src/easy_chat.c", "CopyEasyChatWord", r".*", None,
             why="implementação de CopyEasyChatWord (src/easy_chat.c:166-185): medida em quem chama"),
    # ---- sem uso ou só depuração ----------------------------------------------------------------------
    Declared("src/battle_tower.c", r"AppendBattleTowerBannedSpeciesName|CheckPartyBattleTowerBanlist", r".*", None,
             why="lista de espécies proibidas da Battle Tower: CheckPartyBattleTowerBanlist é special sem uso nos "
                 "scripts do FRLG (só o def_special em data/specials.inc:244)"),
    Declared("src/daycare.c", r"GetDaycareLevelMenu(Level)?Text", r".*", None,
             why="funções static sem chamador no FRLG (src/daycare.c:1428-1462)"),
    Declared("src/easy_chat.c", "BufferEasyChatWordGroupName", r".*", None,
             why="função static sem chamador no FRLG (src/easy_chat.c:536)"),
    Declared("src/dodrio_berry_picking.c", "Debug_SetPlayerNamesAndResults", r".*", None,
             why="só na depuração do Dodrio Berry Picking (nomes de jogador de teste)"),
    # ---- batalha ---------------------------------------------------------------------------------------
    Declared("src/battle_controller_player.c", "MoveSelectionDisplayMoveNames",
             r"gText_MoveInterfaceDynamicColors|gMoveNames\[.*\]", BufRef("gDisplayedStringBattle"),
             (Text("gText_MoveInterfaceDynamicColors"), Text("gMoveNames")),
             why="janela de golpes: cores + nome do golpe (src/battle_controller_player.c:1379-1380)"),
    Declared("src/battle_controller_player.c", "MoveSelectionDisplayMoveType",
             r"gText_MoveInterface(Type|DynamicColors)|gTypeNames\[.*\]", BufRef("gDisplayedStringBattle"),
             (Text("gText_MoveInterfaceType"), Fixed(3, "troca de fonte (FC 06 01)"),
              Text("gText_MoveInterfaceDynamicColors"), Text("gTypeNames")),
             why="tipo do golpe: gText_MoveInterfaceType + fonte + cores + nome do tipo "
                 "(src/battle_controller_player.c:1413-1418)"),
    Declared(_BI, "UpdateHpTextInHealthboxInDoubles", r"sText_Slash",
             BufRef("text", _BI, "UpdateHpTextInHealthboxInDoubles"),
             (Fixed(6, "{COLOR 01}{HIGHLIGHT 00}"), Fixed(3, "HP, 3 algarismos"), Text("sText_Slash", file=_BI)),
             why="HP na caixa de vida das duplas: text[20] = cores + HP + sText_Slash (src/battle_interface.c:871-887)"),
    Declared(_BI, "PrintSafariMonInfo", r"gNatureNamePointers\[.*\]", BufRef("text", _BI, "PrintSafariMonInfo"),
             (Fixed(6, "{COLOR 01}{HIGHLIGHT 02}"), Text("gNatureNamePointers")),
             why="natureza na Safári: text[20] com as cores nos 6 primeiros bytes e o nome da natureza em text + 6 "
                 "(src/battle_interface.c:931-939)"),
    Declared(_BI, "UpdateNickInHealthbox", r"sText_HealthboxNickname", BufRef("gDisplayedStringBattle"),
             (Text("sText_HealthboxNickname", file=_BI), _NICK, Fixed(4, "cor + símbolo de gênero")),
             why="apelido na caixa de vida: sText_HealthboxNickname + apelido + cor + gênero "
                 "(src/battle_interface.c:1493-1527)"),
    Declared(_BI, "UpdateLeftNoOfBallsTextOnHealthbox", r"gText_HighlightRed_Left",
             BufRef("text", _BI, "UpdateLeftNoOfBallsTextOnHealthbox"),
             (Text("gText_HighlightRed_Left"), Fixed(2, "Safari Balls, 2 algarismos")),
             why="Safari Balls restantes: text[16] = gText_HighlightRed_Left + número (src/battle_interface.c:1757-1763)"),
    Declared(_BM, "BattleStringExpandPlaceholders", r"sText_BerryPrefix|gEnigmaBerries\[.*\]\.name",
             BufRef("text", _BM, "BattleStringExpandPlaceholders"),
             (Text("sText_BerryPrefix", file=_BM), Fixed("BERRY_NAME_LENGTH", "nome da fruta Enigma (BERRY_NAME_LENGTH)")),
             why="item do último efeito: text[30] = sText_BerryPrefix + nome da fruta Enigma "
                 "(src/battle_message.c:1988-1989, :2001-2002)"),
    Declared(_BM, r"", r"sText_(Foe|Wild)PkmnPrefix", BufRef("text", _BM, "BattleStringExpandPlaceholders"),
             (_NICK, Text("sText_FoePkmnPrefix", "sText_WildPkmnPrefix", file=_BM)),
             why="HANDLE_NICKNAME_STRING_CASE (macro, src/battle_message.c:1807-1820): text[30] = apelido + "
                 "\" selvagem\"/\" inimigo\" depois do nome"),
    Declared(_BM, "BattleStringExpandPlaceholders", r"", BufRef("text", _BM, "BattleStringExpandPlaceholders"),
             why="item do último efeito: CopyItemName(gLastUsedItem, text) em text[30] (src/battle_message.c:2011, :2017)",
             dest=r"text"),
    # gBattleTextBuffN -> gStringVarN (src/battle_message.c:1849-1871): o menor deles, gStringVar2/3 (20)
    Declared(_BM, "ExpandBattleTextBuffPlaceholders", r"gBattleStringsTable\[.*\]", BufRef("gStringVar2"),
             (Text(*STAT_CHANGE_STRINGS, "sText_ABoosted", file=_BM),),
             why="gBattleTextBuff2 com UMA string da tabela, expandida em gStringVar2 (src/battle_message.c:1862): "
                 "a mudança de atributo (\"Aumentou muito\" ou \"Aumentou\"..., um OU outro desde a G2: "
                 "src/battle_script_commands.c:6762-6798, src/battle_util.c:2716-2720; test_buffers confere no C) "
                 "e o \"a boosted\" da EXP (src/battle_script_commands.c:3267); as outras strings não vão para buffer"),
    Declared(_BM, "ExpandBattleTextBuffPlaceholders",
             r"gMoveNames\[.*\]|gTypeNames\[.*\]|gStatNamesTable\[.*\]|gPokeblockWasTooXStringTable\[.*\]|"
             r"gAbilityNames\[.*\]|sText_EnigmaBerry|", BufRef("gStringVar2"),
             why="gBattleTextBuffN expandido em gStringVarN (src/battle_message.c:1849-1871): golpe, tipo, atributo, "
                 "sabor, habilidade, Fruta Enigma ou item (src/battle_message.c:2221-2313)"),
    Declared(_BM, "ExpandBattleTextBuffPlaceholders", r".*sText_(Foe|Wild)PkmnPrefix.*|text", BufRef("gStringVar2"),
             (_NICK, Text("sText_FoePkmnPrefix", "sText_WildPkmnPrefix", file=_BM)),
             why="B_BUFF_MON_NICK_WITH_PREFIX: apelido + \" selvagem\"/\" inimigo\" (src/battle_message.c:2250-2263)"),
    Declared(_BM, "ExpandBattleTextBuffPlaceholders", r"sText_BerryPrefix|gEnigmaBerries\[.*\]\.name", BufRef("gStringVar2"),
             (Text("sText_BerryPrefix", file=_BM), Fixed("BERRY_NAME_LENGTH", "nome da fruta Enigma (BERRY_NAME_LENGTH)")),
             why="B_BUFF_ITEM da Fruta Enigma em batalha de link: sText_BerryPrefix + nome (src/battle_message.c:2298-2299)"),
    Declared(_BM, "BattleStringExpandPlaceholdersToDisplayedString", r".*", None,
             why="implementação (src/battle_message.c:1779-1782): medida em quem chama"),
    Declared(_BM, "BufferStringBattle", r"stringPtr", BufRef("gDisplayedStringBattle"),
             (Files(_BM),), expand="battle",
             why="mensagem de batalha: stringPtr é qualquer texto de batalha (gBattleStringsTable e os sText_* "
                 "escolhidos em BufferStringBattle, src/battle_message.c:1545-1776), expandido em "
                 "gDisplayedStringBattle[300]; mede todo texto de src/battle_message.c"),
    Declared("src/battle_controller_pokedude.c", r"\w+", r"GetPokedudeText\(\)", BufRef("gDisplayedStringBattle"),
             (Text("sPokedudeTexts_Battle", "sPokedudeTexts_Status", "sPokedudeTexts_TypeMatchup",
                   "sPokedudeTexts_Catching", file="src/battle_controller_pokedude.c"),), expand="battle",
             why="Pokédude (data/text/pokedude.inc): GetPokedudeText (src/battle_controller_pokedude.c:2659-2672) "
                 "expandido em gDisplayedStringBattle[300] (:2558, :2619)"),
    Declared("src/battle_controller_oak_old_man.c", r"\w+", r"text", BufRef("gDisplayedStringBattle"),
             (Text("gText_InflictingDamageIsKey", "gText_LoweringStats", "gText_OakNoRunningFromATrainer",
                   "gText_WinEarnsPrizeMoney", "gText_HowDissapointing"),), expand="battle",
             why="tutorial do Carvalho: PrintOakTextWithMainBgDarkened(text) (src/battle_controller_oak_old_man.c:"
                 "721-741) expande em gDisplayedStringBattle[300] (:775)"),
    Declared(_BM, "ChooseMoveUsedParticle", r".*", BufRef("gBattleTextBuff1"),
             why="partícula do golpe usado em gBattleTextBuff1 (src/battle_message.c:1685, :2341-2343)"),
    Declared(_BM, "ChooseTypeOfMoveUsedString", r".*", BufRef("gBattleTextBuff2"),
             (Text("gMoveNames", "sATypeMove_Table", file=_BM),
              Text(*[f"sText_ExclamationMark{n}" for n in ("", "2", "3", "4", "5")], file=_BM)),
             why="golpe usado: gBattleTextBuff2 = nome do golpe (src/battle_message.c:1687-1690) + a exclamação "
                 "acrescentada no fim (src/battle_message.c:2370-2396)"),
    # ---- campo, menus e telas ---------------------------------------------------------------------------
    Declared("src/berry_crush.c", "Task_ShowBerryCrushRankings", r"gText_XDotY3|gText_TimesPerSec", BufRef("gStringVar4"),
             (Text("gText_XDotY3"), Fixed(1, "espaço"), Text("gText_TimesPerSec")), expand="string",
             why="ranking do Berry Crush: gText_XDotY3 expandido + espaço + gText_TimesPerSec (src/berry_crush.c:3151-3155)"),
    Declared("src/berry_pouch.c", "GetBerryNameAndIndexForMenu",
             r"gText_FontSmall|gText_NumberClear01|gStringVar1|sText_Space|gText_FontNormal",
             BufRef("sListMenuStrbuf", size="27", site="src/berry_pouch.c:645 (Alloc(listMenuNumItems * 27))"),
             (Text("gText_FontSmall"), Text("gText_NumberClear01"), Fixed(2, "número da fruta"),
              Text("sText_Space", file="src/berry_pouch.c"), Text("gText_FontNormal"), BERRIES),
             why="lista da bolsa de frutas: montada em gStringVar4 e copiada para &sListMenuStrbuf[i * 27] "
                 "(src/berry_pouch.c:657, :686-696)"),
    Declared("src/day_night.c", "DayNight_FormatClock", r".*",
             BufRef("clockText", "src/start_menu.c", "DrawStartMenuClockWindow"),
             (Fixed(5, "HH:MM"), Fixed(1, "espaço"), Text("gText_DayNight_PeriodName")),
             why="relógio do menu Start: clockText[DAY_NIGHT_CLOCK_TEXT_SIZE] = hora + espaço + período "
                 "(src/day_night.c:96-104, src/start_menu.c:297-307)"),
    Declared("src/day_night.c", "DayNight_FieldUpdate", r".*",
             BufRef("mapName", "src/map_name_popup.c", "MapNamePopupPrintMapNameOnWindow"),
             why="aviso de período (Hack 7): ShowFieldMessagePopup guarda o ponteiro (src/map_name_popup.c:241-247) e o "
                 "aviso o copia para mapName[25] (src/map_name_popup.c:198-200)"),
    Declared("src/daycare.c", "AppendGenderSymbol", r".*",
             BufRef("nickname", "src/daycare.c", "DaycarePrintMonNickname"),
             (_NICK, Text("gText_MaleSymbol4", "gText_FemaleSymbol4", "gText_GenderlessSymbol")),
             why="nome na creche: nickname[POKEMON_NAME_LENGTH * 2] = apelido + símbolo de gênero (src/daycare.c:1407-1491)"),
    Declared("src/daycare.c", "DaycarePrintMonLvl", r"gText_Lv|intText", BufRef("lvlText", "src/daycare.c", "DaycarePrintMonLvl"),
             (Text("gText_Lv"), Fixed(3, "nível, 3 algarismos")),
             why="nível na creche: lvlText[12] = gText_Lv + nível (src/daycare.c:1499-1509)"),
    Declared("src/easy_chat.c", r"ConvertEasyChatWordsToString|ConvertEasyChatWordsToStringWithLineBreaks\w*|"
             r"CopyEasyChatWordPadded", r".*", None,
             why="frases do Easy Chat (palavra + espaço, várias por linha) nos buffers de quem chama, dimensionados "
                 "para a frase em japonês/inglês; a palavra traduzida é medida na largura da coluna (janelas_uso)"),
    Declared("src/easy_chat_3.c", r"PrintECFields|ECInterfaceCmd_02", r".*", None,
             why="tela do Easy Chat: ecPrintBuffer[0xC1] com as palavras de uma linha da frase (2 ou 3, com "
                 "{CLEAR 17}); a palavra é medida na largura da coluna (janelas_uso, 79 px)"),
    Declared("src/*", "BufferBattleTowerTrainerMessage|ShowEasyChatMessage|TT_ConvertEasyChatMessageToString", r"",
             BufRef("gStringVar4"),
             (Part("files", EC_WORDS.names, desc="palavra do Easy Chat", times=6), Fixed(1, "espaço ou quebra", times=5)),
             why="frase de 6 palavras do Easy Chat (3x2 ou 2x3) em gStringVar4 (src/battle_tower.c:835-845, "
                 "src/easy_chat.c:314; Trainer Tower: dest = gStringVar4, src/battle_message.c:2108-2132)"),
    Declared("src/mail.c", "BufferMailMessage", r"", BufRef("messageLinesBuffer", "src/mail.c"),
             (Part("files", EC_WORDS.names, desc="palavra do Easy Chat", times=3), Fixed(1, "espaço", times=2)),
             why="linha da carta: messageLinesBuffer[i] ([26]) = até 3 palavras do Easy Chat com espaço "
                 "(sLayout_3x3, src/mail.c:228-231, :642)"),
    Declared("src/hall_of_fame.c", "HallOfFame_PrintMonInfo", r"gText_Number|text",
             BufRef("text2", "src/hall_of_fame.c", "HallOfFame_PrintMonInfo"),
             (Text("gText_Number"), Fixed(3, "nº da Pokédex")),
             why="Hall da Fama: text2[24] = gText_Number + 3 algarismos (src/hall_of_fame.c:1010-1023)"),
    Declared("src/hall_of_fame.c", "HallOfFame_PrintMonInfo", r"gSpeciesNames\[.*\]",
             BufRef("text", "src/hall_of_fame.c", "HallOfFame_PrintMonInfo"),
             (Fixed(1, "/"), Text("gSpeciesNames"), Fixed(1, "gênero ou espaço")),
             why="Hall da Fama: text[16] = \"/\" + espécie + gênero (src/hall_of_fame.c:1045-1064)"),
    Declared("src/hall_of_fame.c", "HallOfFame_PrintMonInfo", r"gText_Level",
             BufRef("text", "src/hall_of_fame.c", "HallOfFame_PrintMonInfo"),
             (Text("gText_Level"), Fixed(3, "nível")),
             why="Hall da Fama: text[16] = gText_Level + nível (src/hall_of_fame.c:1068-1069)"),
    Declared("src/hall_of_fame.c", "HallOfFame_PrintMonInfo", r"gText_IDNumber",
             BufRef("text", "src/hall_of_fame.c", "HallOfFame_PrintMonInfo"),
             (Text("gText_IDNumber"), Fixed(5, "nº de ID")),
             why="Hall da Fama: text[16] = gText_IDNumber + 5 algarismos (src/hall_of_fame.c:1072-1073)"),
    Declared("src/item_menu.c", "Bag_BuildListMenuTemplate", r".*", BufRef("sListMenuItemStrings", "src/item_menu.c"),
             (Text("sListItemTextColor_RegularItem", file="src/item_menu.c"), Text("gFameCheckerText_Cancel")),
             why="item \"Cancelar\" da bolsa: sListMenuItemStrings[i] ([19]) = cor + gFameCheckerText_Cancel "
                 "(src/item_menu.c:644-645)"),
    Declared("src/item_menu.c", "BagListMenuGetItemNameColored", r".*", BufRef("sListMenuItemStrings", "src/item_menu.c"),
             (Text("sListItemTextColor_RegularItem", "sListItemTextColor_TmCase_BerryPouch", file="src/item_menu.c"),
              ITEMS),
             why="item da bolsa: sListMenuItemStrings[i] ([19]) = cor + nome do item (src/item_menu.c:640, :668-674)"),
    Declared("src/mail.c", "BufferMailMessage", r"gText_From", BufRef("authorNameBuffer", "src/mail.c"),
             (_PLAYER, Text("gText_From")),
             why="assinatura da carta: authorNameBuffer[12] = nome do jogador + gText_From (src/mail.c:647)"),
    Declared("src/main_menu.c", "PrintDexCount", r".*", BufRef("strbuf", "src/main_menu.c", "PrintDexCount"),
             (Fixed(3, "total da Pokédex"), Text("gTextJPDummy_Hiki")),
             why="menu inicial: strbuf[30] = número + gTextJPDummy_Hiki (src/main_menu.c:655-656)"),
    Declared("src/main_menu.c", "PrintBadgeCount", r".*", BufRef("strbuf", "src/main_menu.c", "PrintBadgeCount"),
             (Fixed(1, "insígnias"), Text("gTextJPDummy_Ko")),
             why="menu inicial: strbuf[30] = número + gTextJPDummy_Ko (src/main_menu.c:673-674)"),
    Declared("src/money.c", r"PrintMoneyAmount(InMoneyBox)?", r".*", BufRef("gStringVar4"),
             (Fixed(5, "preenchimento"), Text("gText_PokedollarVar1")), expand="string",
             why="dinheiro: gStringVar4 = espaços + gText_PokedollarVar1 expandido (src/money.c:78-86, :95-103)"),
    Declared("src/naming_screen.c", "DrawMonTextEntryBox", r".*",
             BufRef("StringAppendN(buffer, title, 15)", size="15",
                    site="src/naming_screen.c:1719 (copia 15 bytes: título com mais de 14 letras fica sem EOS)"),
             (Text("gText_PkmnsNickname"),),
             why="título da tela de apelido (sMonNamingScreenTemplate.title, src/naming_screen.c:2110) depois da "
                 "espécie em buffer[32]: o StringAppendN(..., 15) copia 15 bytes (src/naming_screen.c:1716-1719)"),
    Declared("src/option_menu.c", "BufferOptionMenuString", r".*",
             BufRef("str", "src/option_menu.c", "BufferOptionMenuString"),
             (Text("gText_FrameType"), Fixed(2, "nº da moldura (o StringAppendN 3 leva o EOS)")),
             why="opções: str[20] = gText_FrameType + número (src/option_menu.c:496-498)"),
    Declared("src/party_menu.c", "DisplayPartyPokemonLevel", r"gText_Lv|gStringVar2", BufRef("gStringVar1"),
             (Text("gText_Lv"), Fixed(3, "nível, 3 algarismos")),
             why="nível na tela da equipe: gStringVar1 = gText_Lv + nível (src/party_menu.c:2333-2335)"),
    Declared("src/party_menu.c", "DisplayPartyPokemonMaxHP", r"gText_Slash|gStringVar2", BufRef("gStringVar1"),
             (Text("gText_Slash"), Fixed(3, "HP máximo, 3 algarismos")),
             why="HP máximo na tela da equipe: gStringVar1 = gText_Slash + HP (src/party_menu.c:2405-2407)"),
    Declared("src/party_menu.c", "CursorCB_Register", r".*", BufRef("gStringVar4"),
             (Text("gText_PkmnCantBeTradedNow", "gText_EggCantBeTradedNow"), Text("gText_PauseUntilPress")),
             expand="string",
             why="troca recusada: gStringVar4 = mensagem expandida + gText_PauseUntilPress (src/party_menu.c:3856-3869)"),
    Declared("src/party_menu.c", "CursorCB_Trade1", r".*", BufRef("gStringVar4"),
             (Text("sUnionRoomTradeMessages", file="src/party_menu.c"), Text("gText_PauseUntilPress")),
             expand="string",
             why="troca recusada (Union Room): mensagem expandida + gText_PauseUntilPress (src/party_menu.c:3883-3887)"),
    Declared("src/pokedex_screen.c", "DexScreen_PrintCategoryPageNumbers", r".*",
             BufRef("buffer", "src/pokedex_screen.c", "DexScreen_PrintCategoryPageNumbers"),
             (Text("gText_Page"), Fixed(5, "NN/NN")),
             why="página da Pokédex: buffer[30] = gText_Page + página/total (src/pokedex_screen.c:2359-2363)"),
    Declared("src/pokemon.c", "GetBoxMonData3", r"gText_EggNickname",
             BufRef("apelido", size="POKEMON_NAME_LENGTH + 1",
                    site="include/constants/global.h:63 (buffer de apelido de quem pede MON_DATA_NICKNAME)"),
             why="apelido do ovo: GetMonData(MON_DATA_NICKNAME) copia gText_EggNickname no buffer de apelido de "
                 "quem chama (src/pokemon.c:3083)"),
    Declared("src/pokemon_jump.c", r"Print\w*Prize\w*Message", r".*", BufRef("itemName", "src/pokemon_jump.c"),
             (ITEMS, Text("sPluralTxt", file="src/pokemon_jump.c")),
             why="prêmio do Pokémon Jump: itemName[64] = nome do item + plural (src/pokemon_jump.c:3339-3382)"),
    Declared("src/pokemon_size_record.c", "FormatMonSizeRecord", r".*", BufRef("gStringVar2"),
             (Fixed(8, "parte inteira, até 8 algarismos"), Text("gText_DecimalPoint"), Fixed(1, "décimo")),
             why="recorde de tamanho em gStringVar2/3 (src/pokemon_size_record.c:91-101, :127-151)"),
    Declared("src/pokemon_special_anim_scene.c", "PSA_PrintMessage", r".*", BufRef("textBuf", "include/pokemon_special_anim_internal.h"),
             why="mensagens da animação de item: cada texto em textBuf[0x900] (src/pokemon_special_anim_scene.c:399-442)"),
    Declared("src/pokemon_special_anim_scene.c", "PSA_PrintMessage", r"ItemId_GetName\(.*\)",
             BufRef("textBuf", "include/pokemon_special_anim_internal.h"),
             (ITEMS, Text("gText_WasUsedOn"), _NICK, Text("gText_Period")),
             why="\"<item> fez efeito em <apelido>.\" (src/pokemon_special_anim_scene.c:399-402)"),
    Declared("src/pokemon_storage_system_data.c", "SetDisplayMonData", r".*",
             BufRef("displayMonTexts", "include/pokemon_storage_system_internal.h"),
             why="PC de Pokémon: apelido do ovo, espécie e item em displayMonTexts[4][36] "
                 "(src/pokemon_storage_system_data.c:1016-1019, :1096-1156)"),
    Declared("src/pokemon_storage_system_menu.c", "ResetPokemonStorageSystem", r".*",
             BufRef("nome da caixa", size="BOX_NAME_LENGTH + 1", site="include/pokemon_storage_system.h:11"),
             (Text("gText_Box"), Fixed(2, "número da caixa")),
             why="nome padrão da caixa: gText_Box + número no nome da caixa [BOX_NAME_LENGTH + 1] "
                 "(src/pokemon_storage_system_menu.c:415-416)"),
    Declared(_PSS, "BufferMonInfo", r"gText_Lv|tempStr", BufRef("levelStrBuf", _PSS),
             (Text("gText_Lv"), Fixed(3, "nível (o StringAppendN 4 leva o EOS)")),
             why="nível no resumo: levelStrBuf[7] = gText_Lv + nível (src/pokemon_summary_screen.c:2286-2288)"),
    Declared(_PSS, "BufferMonInfo", r"gText_PokeSum_Item_None|", BufRef("itemNameStrBuf", _PSS),
             why="item no resumo: itemNameStrBuf[ITEM_NAME_LENGTH + 1] (src/pokemon_summary_screen.c:2293-2295)",
             dest=r".*itemNameStrBuf"),
    Declared(_PSS, "BufferMonSkills", r"gText_Slash|tempStr", BufRef("curHpStrBuf", _PSS),
             (Fixed(3, "HP"), Text("gText_Slash"), Fixed(3, "HP máximo")),
             why="HP no resumo: curHpStrBuf[9] = HP + gText_Slash + HP máximo (src/pokemon_summary_screen.c:2313-2318)"),
    Declared(_PSS, "GetEvolutionPageText", r".*", BufRef("pageText", _PSS),
             (Text(*_EVO_LINES, times=5), Fixed(3, "item tem 13 letras, 3 além das 10 do pior caso", times=5),
              Fixed(1, "quebra de linha", times=4), Text("gText_PokeSum_EvoTradedOnly")), expand="string",
             why="página EVOLUTION (Hack 4): até EVOS_PER_MON = 5 linhas expandidas em pageText[SUMMARY_PAGE_TEXT_SIZE] "
                 "(src/pokemon_summary_screen.c:2632-2722)"),
    Declared(_PSS, "GetFriendshipLineText", r".*", BufRef("friendshipText", _PSS, "PrintEvolutionPage"),
             (Fixed(12, "6 corações (2 bytes cada)"), Fixed(1, "espaço"), Text("gText_PokeSum_FriendCount"),
              Fixed(1, "espaço"), Text("gText_PokeSum_FriendBand"), Text("gText_PokeSum_FriendMark")), expand="string",
             why="amizade (Hack 7): friendshipText[FRIENDSHIP_LINE_SIZE] = corações + contagem + faixa + marca "
                 "(src/pokemon_summary_screen.c:2730-2750)"),
    Declared(_PSS, "GetIvEvPageText", r".*", BufRef("pageText", _PSS),
             (Text("gText_PokeSum_IvTotal"), Fixed(18, "números, % e saltos da 1ª linha"),
              Text("gText_PokeSum_IvTotalPerfect", "gText_PokeSum_IvTotalOutstanding", "gText_PokeSum_IvTotalAboveAverage",
                   "gText_PokeSum_IvTotalAverage", "gText_PokeSum_IvTotalBelowAverage"),
              Fixed(21, "quebra, saltos e números de cada atributo", times=6), Text("sIvEvStatNames", file=_PSS, times=6),
              Text("gText_PokeSum_IvPerfect", "gText_PokeSum_IvExcellent", "gText_PokeSum_IvVeryGood",
                   "gText_PokeSum_IvGood", "gText_PokeSum_IvPoor", times=6),
              Text("gText_PokeSum_Ev", times=7), Text("gText_PokeSum_HiddenPower"), Text("gTypeNames"),
              Fixed(20, "números, saltos e espaços da última linha")),
             why="página IVs/EVs (Hack 5) em pageText[SUMMARY_PAGE_TEXT_SIZE] (src/pokemon_summary_screen.c:2820-2896)"),
    Declared("src/quest_log.c", "DrawPreviouslyOnQuestHeader", r".*", BufRef("gStringVar4"),
             (Text("gText_QuestLog_PreviouslyOnYourQuest"), Fixed(1, "nº da cena")), expand="string",
             why="cabeçalho do Quest Log: gStringVar4 = texto expandido + número (src/quest_log.c:522-528)"),
    Declared("src/quest_log_events.c", "QuestLog_GetSpeciesName", r".*", BufRef("gStringVar2"),
             why="\"Ovo\" no Quest Log em gStringVar1/2 (src/quest_log_events.c:1014-1021, :1046-1157)"),
    Declared("src/save_menu_util.c", "SaveStatToString", r".*", BufRef("gStringVar4"),
             (Fixed(6, "cores"), Mapsec()),
             why="lugar na janela de salvar: gStringVar4 = cores + nome do lugar (src/save_menu_util.c:14-42, "
                 "src/start_menu.c:1032)"),
    Declared("src/shop.c", r"BuyMenuBuildListMenuTemplate|PokeMartWriteNameAndIdAt", r".*",
             BufRef("sShopMenuItemStrings", "src/shop.c"),
             why="lista da loja: sShopMenuItemStrings[i] ([ITEM_NAME_LENGTH]) com o nome do item ou "
                 "gFameCheckerText_Cancel (src/shop.c:521-562)"),
    Declared("src/shop.c", "BuyMenuPrintPriceInList", r".*", BufRef("gStringVar4"),
             (Fixed(4, "preenchimento"), Text("gText_PokedollarVar1")), expand="string",
             why="preço na lista da loja: gStringVar4 = espaços + preço expandido (src/shop.c:613-624)"),
    Declared("src/shop.c", "LoadTmHmNameInMart", r"gText_NumberClear01|gStringVar1", BufRef("gStringVar4"),
             (Text("gText_NumberClear01"), Fixed(2, "nº da MT")),
             why="loja de MT: gStringVar4 = gText_NumberClear01 + número (src/shop.c:633-635)"),
    Declared("src/shop.c", "LoadTmHmNameInMart", r"gMoveNames\[.*\]", BufRef("gStringVar4"),
             why="loja de MT: nome do golpe em gStringVar4 (src/shop.c:637)"),
    Declared("src/tm_case.c", "GetTMNumberAndMoveString", r".*", BufRef("sListMenuStringsBuffer", "src/tm_case.c"),
             _TM_LIST,
             why="lista do estojo de MT: montada em gStringVar4 e copiada para sListMenuStringsBuffer[i] ([29]) "
                 "(src/tm_case.c:651, :678-697)"),
    Declared("src/tm_case.c", "Task_SelectedTMHM_Field", r".*",
             BufRef("strbuf", size="256", site="src/tm_case.c:979 (Alloc(256))"),
             _TM_LIST + (Text("gText_Var1IsSelected", offset=2),),
             why="MT selecionada: strbuf = GetTMNumberAndMoveString + gText_Var1IsSelected sem o {STR_VAR_1} "
                 "(src/tm_case.c:979-981)"),
    Declared("src/trade.c", "BufferMovesString", r".*", BufRef("movesString", "src/trade.c", "DrawSelectedMonScreen"),
             (Text("sText_Dummy", file="src/trade.c"), Text("gMoveNames", times=4),
              Text("sText_Newline", file="src/trade.c", times=4)),
             why="golpes na tela de troca: movesString[56] = 4 x (golpe + quebra) (src/trade.c:2339-2368)"),
    Declared("src/trainer_card.c", "PrintNameOnCardFront", r".*", BufRef("buffer", "src/trainer_card.c", "PrintNameOnCardFront"),
             (Text("gText_TrainerCardName"), Fixed("PLAYER_NAME_LENGTH", "nome do jogador, duas vezes", times=2)),
             why="cartão: buffer[0] = gText_TrainerCardName + nome, e o StringAppend repete o nome "
                 "(src/trainer_card.c:1127-1131)"),
    Declared("src/trainer_card.c", "PrintIdOnCard", r".*", BufRef("buffer", "src/trainer_card.c", "PrintIdOnCard"),
             (Text("gText_TrainerCardIDNo"), Fixed(5, "nº de ID")),
             why="cartão: buffer[32] = gText_TrainerCardIDNo + 5 algarismos (src/trainer_card.c:1140-1141)"),
    Declared("src/trainer_card.c", "PrintMoneyOnCard", r".*", BufRef("buffer", "src/trainer_card.c", "PrintMoneyOnCard"),
             (Text("gText_TrainerCardYen"), Fixed(6, "dinheiro, 6 algarismos")),
             why="cartão: buffer[10] = gText_TrainerCardYen + 6 algarismos (src/trainer_card.c:1151-1152)"),
    Declared("src/trainer_card.c", "BufferNameForCardBack", r".*", BufRef("strings", "src/trainer_card.c"),
             (_PLAYER, Text("gText_Var1sTrainerCard")),
             why="verso do cartão: strings[TRAINER_CARD_STRING_NAME] = nome + gText_Var1sTrainerCard "
                 "(src/trainer_card.c:1256-1260)"),
    Declared("src/trainer_card.c", "BufferHofDebutTime", r".*",
             BufRef("StringAppendN(..., gText_Colon2, 2)", size="2",
                    site="src/trainer_card.c:1291 (copia 2 bytes: mais de 1 letra fica sem EOS)"),
             (Text("gText_Colon2"),),
             why="tempo do Hall da Fama no cartão: StringAppendN(..., gText_Colon2, 2) (src/trainer_card.c:1291-1294)"),
    Declared(_UR, "PrintPlayerNameAndIdOnWindow", r".*", BufRef("text2", _UR, "PrintPlayerNameAndIdOnWindow"),
             (Text("gText_UR_ID"), Fixed(5, "nº de ID")),
             why="Union Room: text2[12] = gText_UR_ID + 5 algarismos (src/union_room.c:349-354)"),
    Declared(_UR, _UR_DST, r".*", BufRef("gStringVar4"),
             why="mensagens do Union Room montadas em dst = gStringVar4 (src/union_room.c:460, :962, :1248, :1300, "
                 ":2989, :3164, :3231, :3493)"),
    Declared(_UR, "PrintGroupMemberOnWindow", r"gText_UR_Colon", BufRef("gStringVar4"),
             (Fixed(2, "nº"), Text("gText_UR_Colon")),
             why="Union Room: gStringVar4 = número + gText_UR_Colon (src/union_room.c:4221-4222)"),
    Declared(_UR, r"PrintGroup(Member|Candidate)OnWindow", r"gText_UR_ID|trainerId|id_str", BufRef("gStringVar4"),
             (Text("gText_UR_ID"), Fixed(5, "nº de ID")),
             why="Union Room: gStringVar4 = gText_UR_ID + 5 algarismos (src/union_room.c:4231-4232, :4248-4249)"),
    Declared("src/union_room_chat.c", "ProcessReceivedChatMessage", r".*", BufRef("receivedMessage", "src/union_room_chat.c"),
             why="chat do Union Room: entrou/saiu expandido em sWork->receivedMessage[0x40] (src/union_room_chat.c:1296-1318)"),
    Declared("src/union_room_chat_display.c", "PrintCurrentKeyboardPage", r".*",
             BufRef("str", "src/union_room_chat_display.c", "PrintCurrentKeyboardPage"),
             (Fixed(3, "espaçamento (FC 11 08)"), Text("gUnionRoomKeyboardText")),
             why="teclado do chat: str[45] = código de espaçamento + linha do teclado (src/union_room_chat_display.c:1113-1126)"),
]


if __name__ == "__main__":
    sys.exit(main())

