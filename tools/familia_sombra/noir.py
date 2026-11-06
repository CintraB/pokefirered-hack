"""Efeito de filme antigo da Família Sombra (POK-51): a tabela que o C usa em FamiliaSombra_PaletaNoir.

    python3 -I tools/familia_sombra/noir.py              # grava src/data/familia_sombra_noir.h
    python3 -I tools/familia_sombra/noir.py --conferir   # compara com o arquivo gravado (sai 1 se divergir)

`noir()` é a função da prévia aprovada (`.superpowers/brainstorm/familia-sombra/previa.py`), copiada sem mudança:
luminância ^ 1.25 * 0.92, matiz 0.61 (azul-acinzentado), saturação 0.18, cada canal com & 0xF8.

No jogo a cor é de 5 bits por canal; a entrada da função é o canal x 8 (o valor que o GBA mostra). A cor de saída
só depende da luminância, e a luminância só da soma S = 30*r + 59*g + 11*b (canais de 5 bits, 0..3100): a tabela
tem uma cor por S, e o C só faz a soma e lê a tabela (sem ponto flutuante na ROM).
"""

import colorsys
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "src" / "data" / "familia_sombra_noir.h"
PESOS = (30, 59, 11)
S_MAX = 31 * sum(PESOS)


def noir(pal):
    out = []
    for r, g, b in pal:
        lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        lum = lum ** 1.25 * 0.92
        r2, g2, b2 = colorsys.hls_to_rgb(0.61, lum, 0.18)
        out.append((int(r2 * 255) & 0xF8, int(g2 * 255) & 0xF8, int(b2 * 255) & 0xF8))
    return out


def gba(r8: int, g8: int, b8: int) -> int:
    return (r8 >> 3) | (g8 >> 3) << 5 | (b8 >> 3) << 10


def noir_gba(cor: int) -> int:
    """A cor GBA (15 bits) depois do filme, pela função da prévia."""
    r, g, b = cor & 31, cor >> 5 & 31, cor >> 10 & 31
    return gba(*noir([(r << 3, g << 3, b << 3)])[0])


def soma(cor: int) -> int:
    return PESOS[0] * (cor & 31) + PESOS[1] * (cor >> 5 & 31) + PESOS[2] * (cor >> 10 & 31)


def tabela() -> list[int]:
    """Uma cor por soma S. Toda cor de 5 bits com a mesma S dá a mesma saída (conferido aqui)."""
    out: list[int | None] = [None] * (S_MAX + 1)
    for cor in range(0x8000):
        s, n = soma(cor), noir_gba(cor)
        assert out[s] in (None, n), f"S = {s}: duas saídas"
        out[s] = n
    # S sem nenhuma cor de 5 bits (não acontece no jogo): a cor da S anterior
    for s in range(1, S_MAX + 1):
        if out[s] is None:
            out[s] = out[s - 1]
    return out  # type: ignore[return-value]


def cabecalho() -> str:
    valores = tabela()
    linhas = []
    for i in range(0, len(valores), 12):
        linhas.append("    " + ", ".join(f"0x{v:04X}" for v in valores[i:i + 12]) + ",")
    return (
        "// POK-51: efeito de filme antigo da Família Sombra. GERADO por tools/familia_sombra/noir.py; não editar.\n"
        "// sFamiliaNoir[30*r + 59*g + 11*b] = a cor (r, g, b de 5 bits) pela função noir() da prévia aprovada.\n"
        "// Incluído só por src/familia_sombra.c.\n\n"
        f"#define FAMILIA_NOIR_TAMANHO {len(valores)}\n\n"
        "static const u16 sFamiliaNoir[FAMILIA_NOIR_TAMANHO] =\n{\n" + "\n".join(linhas) + "\n};\n"
    )


def main(argv: list[str]) -> int:
    texto = cabecalho()
    if "--conferir" in argv:
        if SAIDA.read_text(encoding="utf-8") != texto:
            print(f"{SAIDA} diverge de tools/familia_sombra/noir.py", file=sys.stderr)
            return 1
        return 0
    SAIDA.write_text(texto, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
