"""Refaz as quebras de linha (`\\n`, `\\l`) de um texto do jogo para caber numa janela.

Mede cada palavra com as mesmas larguras da checagem de texto (esteira/check_text.py: tabelas
`s*LatinGlyphWidths` de src/text.c pelo charmap.txt, {PLAYER}/{RIVAL} = 7 letras, nomes de
batalha pelo maior nome) e quebra de forma gulosa: cada linha leva o máximo de palavras que
cabem. `\\p` (caixa nova) é mantido; dentro de cada caixa a primeira quebra é `\\n` e as
seguintes `\\l` (rolagem), como no FRLG (`estilo="dialogo"`); `estilo="linhas"` usa só `\\n`
(Pokédex, ajuda, descrições). Códigos de controle ficam grudados na palavra em que estavam.

CLI (de test/):
  python3 -m esteira.reflow --largura 208 --texto "Olá! ...$"
  python3 -m esteira.reflow data/maps/X/text.inc [--rotulo X_Text_Y] [--escrever]
      sem --largura usa a janela da regra do arquivo (check_text.WIDTH_RULES); sem --escrever
      só mostra o resultado. Blocos com #if/.if ficam como estão.
"""

import argparse
import re
import sys
from functools import lru_cache
from pathlib import Path

from esteira.check_text import _LABEL_LINE, _STRING_LINE, _load_env, measure, rule_for

REPO_ROOT = Path(__file__).resolve().parents[2]
_BREAK = re.compile(r"\\[nlp]")


@lru_cache(maxsize=2)
def _env(repo: str):
    return _load_env(Path(repo))


def _width(text: str, fonte: str, espaco: int | None, repo: Path) -> int:
    return measure(text, _env(str(repo)), fonte, espaco).widest


def line_widths(texto: str, fonte: str = "normal", espaco: int | None = None, repo: Path = REPO_ROOT) -> list[int]:
    """Largura em px de cada linha do texto (quebras \\n, \\l, \\p)."""
    return [_width(line, fonte, espaco, repo) for line in _BREAK.split(texto.rstrip("$"))]


def _words(paragraph: str) -> list[str]:
    """Palavras separadas por espaço, sem partir `{CÓDIGO COM ESPAÇO}`."""
    words: list[str] = []
    cur = []
    depth = 0
    for ch in paragraph:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if ch == " " and depth == 0:
            if cur:
                words.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        words.append("".join(cur))
    return words


def reflow(texto: str, largura_px: int, fonte: str = "normal", estilo: str = "dialogo",
           espaco: int | None = None, repo: Path = REPO_ROOT) -> str:
    """O texto com as quebras refeitas para `largura_px`."""
    if estilo not in ("dialogo", "linhas"):
        raise ValueError(f"estilo desconhecido: {estilo}")
    end = "$" if texto.endswith("$") else ""
    body = texto[:-1] if end else texto
    space = espaco if espaco is not None else _width(" ", fonte, None, repo)
    boxes = body.split("\\p")
    out_boxes = []
    for box in boxes:
        words = _words(_BREAK.sub(" ", box))
        lines: list[list[str]] = []
        width = 0
        for word in words:
            w = _width(word, fonte, espaco, repo)
            if lines and width + space + w <= largura_px:
                lines[-1].append(word)
                width += space + w
            else:
                lines.append([word])
                width = w
        breaks = ["\\n"] + ["\\l" if estilo == "dialogo" else "\\n"] * max(0, len(lines) - 2)
        text = " ".join(lines[0]) if lines else ""
        for brk, line in zip(breaks, lines[1:]):
            text += brk + " ".join(line)
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


def reflow_inc(source: str, rotulo: str | None, largura: int | None, fonte: str | None, estilo: str,
               espaco: int | None, arquivo: str) -> tuple[str, list[str]]:
    """(arquivo reescrito, rótulos refeitos)."""
    lines = source.split("\n")
    out: list[str] = []
    done: list[str] = []
    label = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _LABEL_LINE.match(line)
        if m:
            label = m.group(1)
        sm = _STRING_LINE.match(line)
        if not sm or sm.group(1) != "string" or (rotulo is not None and label != rotulo) or label in done:
            out.append(line)
            i += 1
            continue
        block, j = [], i
        while j < len(lines) and _STRING_LINE.match(lines[j]) and _STRING_LINE.match(lines[j]).group(1) == "string":
            block.append(_STRING_LINE.match(lines[j]).group(2))
            j += 1
        if j < len(lines) and re.match(r"^\s*[#.]\s*(if|else|elif|endif)", lines[j].strip()):
            out.extend(lines[i:j])     # bloco com ramos: fica como está
            i = j
            continue
        rule = rule_for(arquivo, label or "")
        px = largura if largura is not None else (rule.px if rule else None)
        if px is None:
            raise ValueError(f"{arquivo}: {label}: sem largura (passe --largura)")
        font = fonte or (rule.font if rule else "normal")
        space = espaco if espaco is not None else (rule.space if rule else None)
        indent = re.match(r"^(\s*)", line).group(1)
        new = reflow("".join(block), px, font, estilo, space)
        out.extend(f'{indent}.string "{piece}"' for piece in _split_lines(new))
        done.append(label or f"linha {i + 1}")
        i = j
    return "\n".join(out), done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m esteira.reflow", description=__doc__.split("\n\n")[0])
    parser.add_argument("arquivo", nargs="?", help=".inc a refazer (caminho; relativo ao repo para achar a regra)")
    parser.add_argument("--texto", help="texto cru (como no fonte, com \\n e $)")
    parser.add_argument("--largura", type=int, help="largura útil em px (padrão: a da regra do arquivo)")
    parser.add_argument("--fonte", choices=("normal", "small"))
    parser.add_argument("--estilo", choices=("dialogo", "linhas"), default="dialogo")
    parser.add_argument("--espaco", type=int, help="largura do espaço em px (a ajuda usa 4)")
    parser.add_argument("--rotulo", help="só este rótulo")
    parser.add_argument("--escrever", action="store_true", help="grava o arquivo (sem isto só mostra)")
    args = parser.parse_args(argv)
    if args.texto is not None:
        if args.largura is None:
            parser.error("--texto precisa de --largura")
        print(reflow(args.texto, args.largura, args.fonte or "normal", args.estilo, args.espaco))
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
        new, done = reflow_inc(source, args.rotulo, args.largura, args.fonte, args.estilo, args.espaco, rel)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.rotulo and not done:
        print(f"rótulo não encontrado (ou sem .string): {args.rotulo}", file=sys.stderr)
        return 2
    if args.escrever:
        path.write_text(new, encoding="utf-8")
        print(f"{len(done)} rótulo(s) refeito(s) em {args.arquivo}")
    else:
        print(new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
