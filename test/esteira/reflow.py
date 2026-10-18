"""Refaz as quebras de linha (`\\n`, `\\l`) de um texto do jogo para caber numa janela.

Mede cada palavra com as mesmas larguras da checagem de texto (esteira/check_text.py: tabelas
`s*LatinGlyphWidths` de src/text.c pelo charmap.txt, {PLAYER}/{RIVAL} = 7 letras, nomes de
batalha pelo maior nome) e quebra de forma gulosa: cada linha leva o máximo de palavras que
cabem. `\\p` (caixa nova) é mantido; dentro de cada caixa a primeira quebra é `\\n` e as
seguintes `\\l` (rolagem), como no FRLG (`estilo="dialogo"`); `estilo="linhas"` usa só `\\n`
(Pokédex, ajuda, descrições). Códigos de controle ficam grudados na palavra em que estavam.

Formatação intencional é preservada:
  - só a caixa que tem linha estourada é refeita (`forcar=True` refaz todas): placa com
    "ROUTE 1\\nPALLET TOWN - VIRIDIAN CITY" que cabe fica como está;
  - linha que começa com glifo de lista ({CIRCLE_1}..{CIRCLE_9}, {CIRCLE_DOT}, {TRIANGLE},
    {BIG_MULT_X}) abre item novo; as linhas recuadas logo depois são a continuação do item e
    mantêm o recuo, a não ser que o item termine em ":" (sublista: cada entrada fica na linha);
  - linha recuada fora de lista ("  Usar a BOLSA") é fixa: começa linha e mantém o recuo;
  - espaços duplos entre palavras ficam.

CLI (de test/):
  python3 -m esteira.reflow --largura 208 --texto "Olá! ...$"
  python3 -m esteira.reflow data/maps/X/text.inc [--rotulo X_Text_Y] [--escrever] [--forcar]
      sem --largura usa a janela da regra do arquivo (check_text.WIDTH_RULES); sem --escrever
      só mostra o resultado; sem --forcar só os rótulos com linha estourada mudam. Blocos com
      #if/.if ficam como estão.
"""

import argparse
import re
import sys
from functools import lru_cache
from pathlib import Path

from esteira.check_text import _LABEL_LINE, _STRING_LINE, _load_env, measure, rule_for

REPO_ROOT = Path(__file__).resolve().parents[2]
_BREAK = re.compile(r"\\[nlp]")
_LIST_GLYPH = re.compile(r"^\{(?:CIRCLE_\d|CIRCLE_DOT|TRIANGLE|BIG_MULT_X)\}")   # glifos F9 de lista
_INDENT = re.compile(r"^( +)")


def _opens_sublist(text: str) -> bool:
    """Item que termina em ":" abre sublista: as linhas recuadas seguintes são entradas fixas,
    não continuação (Help_Text_HowToUseSummary, data/text/help_system.inc)."""
    return text.rstrip().endswith(":")


@lru_cache(maxsize=2)
def _env(repo: str):
    return _load_env(Path(repo))


def _width(text: str, fonte: str, espaco: int | None, repo: Path) -> int:
    return measure(text, _env(str(repo)), fonte, espaco).widest


def line_widths(texto: str, fonte: str = "normal", espaco: int | None = None, repo: Path = REPO_ROOT) -> list[int]:
    """Largura em px de cada linha do texto (quebras \\n, \\l, \\p)."""
    return [_width(line, fonte, espaco, repo) for line in _BREAK.split(texto.rstrip("$"))]


def _words(text: str) -> list[tuple[str, str]]:
    """(palavra, espaços depois dela), sem partir `{CÓDIGO COM ESPAÇO}`."""
    out: list[tuple[str, str]] = []
    word, gap, depth = [], [], 0
    for ch in text:
        if ch == " " and depth == 0:
            gap.append(ch)
            continue
        if gap:
            out.append(("".join(word), "".join(gap)))
            word, gap = [], []
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        word.append(ch)
    if word or gap:
        out.append(("".join(word), "".join(gap)))
    return out


def _segments(box: str) -> list[list[str]]:
    """[recuo da 1ª linha, recuo das seguintes, texto, tipo] de cada trecho que corre junto."""
    segs: list[list[str]] = []
    for line in _BREAK.split(box):
        indent = _INDENT.match(line)
        if _LIST_GLYPH.match(line):
            segs.append(["", "", line, "item"])
        elif indent and segs and segs[-1][3] == "item" and not _opens_sublist(segs[-1][2]):
            if not segs[-1][1]:
                segs[-1][1] = indent.group(1)
            segs[-1][2] += " " + line[len(indent.group(1)):]
        elif indent:
            segs.append([indent.group(1), indent.group(1), line[len(indent.group(1)):], "fixo"])
        elif segs and segs[-1][3] == "corrido":
            segs[-1][2] += " " + line
        else:
            segs.append(["", "", line, "corrido"])
    return segs


def _wrap(seg: list[str], largura_px: int, fonte: str, espaco: int | None, space: int, repo: Path) -> list[str]:
    first, cont, text, _kind = seg
    budgets = (largura_px - _width(first, fonte, espaco, repo), largura_px - _width(cont, fonte, espaco, repo))
    lines: list[str] = []
    cur, width, gap = "", 0, ""
    for word, after in _words(text):
        w = _width(word, fonte, espaco, repo)
        if not cur:
            cur, width = word, w
        elif width + len(gap) * space + w <= budgets[1 if lines else 0]:
            cur += gap + word
            width += len(gap) * space + w
        else:
            lines.append(cur)
            cur, width = word, w
        gap = after
    lines.append(cur)
    return [(first if i == 0 else cont) + line for i, line in enumerate(lines)]


def _kinds(lines: list[str]) -> list[tuple[str, str]]:
    """(tipo, recuo) de cada linha: item (glifo de lista), cont (recuada depois de item),
    fixo (recuada fora de lista) ou corrido."""
    out: list[tuple[str, str]] = []
    in_item = False
    for n, line in enumerate(lines):
        indent = _INDENT.match(line)
        if _LIST_GLYPH.match(line):
            out.append(("item", ""))
            in_item = True
        elif indent and in_item and not _opens_sublist(lines[n - 1]):
            out.append(("cont", indent.group(1)))
        elif indent:
            out.append(("fixo", indent.group(1)))
            in_item = False
        else:
            out.append(("corrido", ""))
            in_item = False
    return out


def _spill(box: str, largura_px: int, fonte: str, espaco: int | None, space: int, repo: Path) -> list[str]:
    """Só a linha estourada muda: as palavras do fim descem para o começo da linha seguinte
    (se ela continua o mesmo trecho) ou para uma linha nova, em cascata."""
    lines = _BREAK.split(box)
    kinds = _kinds(lines)
    out: list[str] = []
    carry = ""            # palavras que desceram da linha de cima
    carry_indent = ""
    i = 0
    while i < len(lines) or carry:
        if i < len(lines):
            kind, indent = kinds[i]
            if carry and kind in ("corrido", "cont"):
                line = indent + carry + " " + lines[i][len(indent):]
                i += 1
            elif carry:
                line = carry_indent + carry           # o que desceu vira linha própria antes do item
            else:
                line = lines[i]
                i += 1
        else:
            line = carry_indent + carry
        carry = ""
        if _width(line, fonte, espaco, repo) <= largura_px:
            out.append(line)
            continue
        indent = _INDENT.match(line).group(1) if _INDENT.match(line) else ""
        kind_here = "item" if _LIST_GLYPH.match(line) else ("cont" if indent else "corrido")
        words = _words(line[len(indent):])
        cur, width, gap, cut = "", _width(indent, fonte, espaco, repo), "", len(words)
        for n, (word, after) in enumerate(words):
            w = _width(word, fonte, espaco, repo)
            if cur and width + len(gap) * space + w > largura_px:
                cut = n
                break
            cur, width, gap = (cur + gap + word if cur else word), width + (len(gap) * space if cur else 0) + w, after
        if cut == 0:      # nem a primeira palavra cabe: ela fica sozinha na linha
            cut = 1
            cur = words[0][0]
        out.append(indent + cur)
        carry = "".join(word + after for word, after in words[cut:]).rstrip(" ")
        # a continuação de um item de lista mantém o recuo pendurado (o das linhas recuadas dele)
        carry_indent = next((ind for k, ind in kinds[i:] if k == "cont"), "   ") if kind_here in ("item", "cont") else ""
        if kind_here == "cont":
            carry_indent = indent
    return out


def reflow(texto: str, largura_px: int, fonte: str = "normal", estilo: str = "dialogo",
           espaco: int | None = None, repo: Path = REPO_ROOT, forcar: bool = False) -> str:
    """O texto com as quebras refeitas para `largura_px`. Sem `forcar`, só as caixas com linha
    estourada mudam, e nelas só a linha que estoura (o excesso desce para a seguinte); com
    `forcar`, cada caixa é refeita do zero (gulosa), mantendo itens de lista e recuos."""
    if estilo not in ("dialogo", "linhas"):
        raise ValueError(f"estilo desconhecido: {estilo}")
    end = "$" if texto.endswith("$") else ""
    body = texto[:-1] if end else texto
    space = espaco if espaco is not None else _width(" ", fonte, None, repo)
    out_boxes = []
    for box in body.split("\\p"):
        if not forcar and max(line_widths(box, fonte, espaco, repo), default=0) <= largura_px:
            out_boxes.append(box)          # cabe: as quebras (placas, listas) ficam como estão
            continue
        if forcar:
            lines = [line for seg in _segments(box) for line in _wrap(seg, largura_px, fonte, espaco, space, repo)]
        else:
            lines = _spill(box, largura_px, fonte, espaco, space, repo)
        breaks = ["\\n"] + ["\\l" if estilo == "dialogo" else "\\n"] * max(0, len(lines) - 2)
        text = lines[0] if lines else ""
        for brk, line in zip(breaks, lines[1:]):
            text += brk + line
        out_boxes.append(text)
    return "\\p".join(out_boxes) + end


# ---- .inc ----------------------------------------------------------------------------------

def _split_lines(text: str) -> list[str]:
    """Pedaços para um `.string` por linha: cada um termina na sua quebra (ou no fim)."""
    pieces, start = [], 0
    for m in _BREAK.finditer(text):
        pieces.append(text[start:m.end()])
        start = m.end()
    if start < len(text):
        pieces.append(text[start:])
    return pieces


_CUT = re.compile(r"^\s*(?:[#.]\s*(?:if|else|elif|endif)\b|@)")


def reflow_inc(source: str, rotulo: str | None, largura: int | None, fonte: str | None, estilo: str | None,
               espaco: int | None, arquivo: str, forcar: bool = False) -> tuple[str, list[str], list[str]]:
    """(arquivo reescrito, rótulos refeitos, rótulos vistos). Rótulo cujas caixas cabem fica
    intacto (a não ser com `forcar`); bloco cortado por #if/.if ou por comentário também."""
    lines = source.split("\n")
    out: list[str] = []
    done: list[str] = []
    seen: list[str] = []
    label = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _LABEL_LINE.match(line)
        if m:
            label = m.group(1)
        sm = _STRING_LINE.match(line)
        if not sm or sm.group(1) != "string" or (rotulo is not None and label != rotulo) or label in seen:
            out.append(line)
            i += 1
            continue
        seen.append(label or f"linha {i + 1}")
        block, j = [], i
        while j < len(lines) and _STRING_LINE.match(lines[j]) and _STRING_LINE.match(lines[j]).group(1) == "string":
            block.append(_STRING_LINE.match(lines[j]).group(2))
            j += 1
        if j < len(lines) and _CUT.match(lines[j]):
            out.extend(lines[i:j])     # bloco cortado por ramo ou comentário: fica como está
            i = j
            continue
        rule = rule_for(arquivo, label or "")
        px = largura if largura is not None else (rule.px if rule else None)
        if px is None:
            raise ValueError(f"{arquivo}: {label}: sem largura (passe --largura)")
        font = fonte or (rule.font if rule else "normal")
        space = espaco if espaco is not None else (rule.space if rule else None)
        style = estilo or ("linhas" if rule is not None and rule.lines is not None else "dialogo")
        indent = re.match(r"^(\s*)", line).group(1)
        old = "".join(block)
        new = reflow(old, px, font, style, space, forcar=forcar)
        if new == old:
            out.extend(lines[i:j])     # cabe: o bloco fica exatamente como estava
        else:
            out.extend(f'{indent}.string "{piece}"' for piece in _split_lines(new))
            done.append(label or f"linha {i + 1}")
        i = j
    return "\n".join(out), done, seen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m esteira.reflow", description=__doc__.split("\n\n")[0])
    parser.add_argument("arquivo", nargs="?", help=".inc a refazer (caminho; relativo ao repo para achar a regra)")
    parser.add_argument("--texto", help="texto cru (como no fonte, com \\n e $)")
    parser.add_argument("--largura", type=int, help="largura útil em px (padrão: a da regra do arquivo)")
    parser.add_argument("--fonte", choices=("normal", "small"))
    parser.add_argument("--estilo", choices=("dialogo", "linhas"),
                        help="padrão: linhas se a janela tem limite de linhas (ajuda, Pokédex), senão diálogo")
    parser.add_argument("--espaco", type=int, help="largura do espaço em px (a ajuda usa 4)")
    parser.add_argument("--rotulo", help="só este rótulo")
    parser.add_argument("--escrever", action="store_true", help="grava o arquivo (sem isto só mostra)")
    parser.add_argument("--forcar", action="store_true", help="refaz também as caixas que já cabem")
    args = parser.parse_args(argv)
    if args.texto is not None:
        if args.largura is None:
            parser.error("--texto precisa de --largura")
        print(reflow(args.texto, args.largura, args.fonte or "normal", args.estilo or "dialogo", args.espaco,
                     forcar=args.forcar))
        return 0
    if not args.arquivo:
        parser.error("passe --texto ou um arquivo .inc")
    path = Path(args.arquivo).resolve()
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = path.name
    source = path.read_text(encoding="utf-8")
    try:
        new, done, seen = reflow_inc(source, args.rotulo, args.largura, args.fonte, args.estilo, args.espaco,
                                     rel, args.forcar)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.rotulo and not seen:
        print(f"rótulo não encontrado (ou sem .string): {args.rotulo}", file=sys.stderr)
        return 2
    if args.escrever:
        path.write_text(new, encoding="utf-8")
        print(f"{len(done)} rótulo(s) refeito(s) em {args.arquivo}" + (f": {', '.join(done)}" if done else ""))
    else:
        print(new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
