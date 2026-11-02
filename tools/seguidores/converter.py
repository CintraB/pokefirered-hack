"""Seguidores (POK-48): converte os sprites de overworld do Veekun (HGSS) em folhas indexadas 4bpp + paletas + tabela C.

    python3 -I tools/seguidores/converter.py                      # as 12 espécies de ESPECIES_PADRAO
    python3 -I tools/seguidores/converter.py --especies 1-9,25    # qualquer lista de números da Pokédex nacional
    python3 -I tools/seguidores/converter.py --especies todas     # 1-386 (etapa 2; só 32x32 por enquanto)
    python3 -I tools/seguidores/converter.py --conferir           # refaz num diretório temporário e compara

Lê, em `--origem` (padrão: `.superpowers/brainstorm/seguidores/todos/pokemon/overworld`, fora do Git), o layout do
pacote do Veekun: `<direção>/<dex>.png` e `<direção>/frame2/<dex>.png` para `down`, `up`, `left` e `right`, e o mesmo
sob `shiny/`. Para cada espécie grava (a partir de `--saida`, padrão a raiz do repositório):

    graphics/object_events/pics/seguidores/<nome>.png            folha 256x32, PNG 4 bits indexado
    graphics/object_events/palettes/seguidores/<nome>.pal        JASC 16 cores (índice 0 = transparente)
    graphics/object_events/palettes/seguidores/<nome>_shiny.pal  idem, shiny
    src/data/object_events/follower_species.h                    tabela `gFollowerSpecies` (ordem da Pokédex)

A folha tem 8 quadros 32x32 lado a lado: sul (2), norte (2), oeste (2), leste (2), na ordem de `DIRECOES`; o leste
tem desenho próprio (não é espelho do oeste). O índice de cada pixel vem do sprite normal (cores numeradas pela
ordem em que aparecem, varrendo os quadros da esquerda para a direita, linha a linha; índice 0 é só transparência) e
a paleta shiny sai da correspondência pixel a pixel normal -> shiny. A conversão FALHA (código 1) se um índice do
normal corresponder a duas cores no shiny, se a transparência não coincidir, se um quadro não for 32x32, se houver
pixel semitransparente ou se a espécie tiver mais de 15 cores. `--conferir` compara o que está no repositório com o
que a conversão gera agora (PNG pelos pixels e pela paleta; o resto byte a byte).

Só Pillow e a biblioteca padrão são usados.
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
ORIGEM_PADRAO = REPO / ".superpowers" / "brainstorm" / "seguidores" / "todos" / "pokemon" / "overworld"
PICS_REL = Path("graphics/object_events/pics/seguidores")
PALS_REL = Path("graphics/object_events/palettes/seguidores")
TABELA_REL = Path("src/data/object_events/follower_species.h")
FOLLOWER_H_REL = Path("include/follower.h")

ESPECIES_PADRAO = [1, 2, 3, 4, 5, 6, 7, 8, 9, 25, 26, 172]
NUM_ESPECIES_DEX = 386
# ordem dos quadros na folha (sul, norte, oeste, leste; 2 quadros cada) = pasta do Veekun
DIRECOES = ["down", "up", "left", "right"]
QUADROS_POR_DIRECAO = 2
TAMANHO_QUADRO = 32
MAX_CORES = 15  # índice 0 é a transparência
COR_INDICE_0 = (115, 197, 164)  # a mesma que as paletas de NPC usam no índice 0
RE_CONTAGEM = re.compile(r"(#define FOLLOWER_SPECIES_COUNT\s+)\d+")


class ErroConversao(Exception):
    pass


def ler_nomes_dex():
    """{dex nacional: 'NOME'} pela enum NATIONAL_DEX_* de include/constants/pokedex.h."""
    texto = (REPO / "include" / "constants" / "pokedex.h").read_text(encoding="utf-8")
    bloco = texto.split("NATIONAL_DEX_NONE,", 1)[1].split("};", 1)[0]
    nomes = re.findall(r"^\s*NATIONAL_DEX_(\w+),", bloco, re.M)
    return {i + 1: n for i, n in enumerate(nomes)}


def lista_especies(texto):
    if texto == "todas":
        return list(range(1, NUM_ESPECIES_DEX + 1))
    dexes = set()
    for parte in texto.split(","):
        a, _, b = parte.strip().partition("-")
        dexes.update(range(int(a), int(b or a) + 1))
    return sorted(dexes)


def carregar_quadros(origem, dex, shiny):
    """Os 8 quadros do Veekun em RGBA, na ordem da folha."""
    base = origem / "shiny" if shiny else origem
    quadros = []
    for d in DIRECOES:
        for sub in ("", "frame2"):
            caminho = base / d / sub / f"{dex}.png"
            if not caminho.is_file():
                raise ErroConversao(f"falta {caminho}")
            im = Image.open(caminho).convert("RGBA")
            if im.size != (TAMANHO_QUADRO, TAMANHO_QUADRO):
                raise ErroConversao(f"{caminho}: {im.size[0]}x{im.size[1]}, esperado 32x32 (64x64 ainda não é suportado)")
            quadros.append(im)
    return quadros


def pixels_da_folha(quadros):
    """Lista de (r, g, b) ou None (transparente), quadro a quadro, linha a linha, na ordem da folha."""
    saida = []
    for q in quadros:
        for y in range(TAMANHO_QUADRO):
            for x in range(TAMANHO_QUADRO):
                r, g, b, a = q.getpixel((x, y))
                if a == 0:
                    saida.append(None)
                elif a == 255:
                    saida.append((r, g, b))
                else:
                    raise ErroConversao(f"pixel semitransparente (alfa {a}) em ({x}, {y})")
    return saida


def converter_especie(origem, dex):
    """-> (indices da folha 256x32 em ordem de linha, paleta normal, paleta shiny); listas de 16 (r, g, b)."""
    normal = pixels_da_folha(carregar_quadros(origem, dex, False))
    shiny = pixels_da_folha(carregar_quadros(origem, dex, True))
    indice = {}  # cor do normal -> índice (1..15), na ordem de aparição
    for cor in normal:
        if cor is not None and cor not in indice:
            indice[cor] = len(indice) + 1
    if len(indice) > MAX_CORES:
        raise ErroConversao(f"{len(indice)} cores no normal; o máximo é {MAX_CORES} (mais o índice 0 transparente)")
    para_shiny = {}  # índice -> cor do shiny
    for pn, ps in zip(normal, shiny):
        if (pn is None) != (ps is None):
            raise ErroConversao("a transparência do shiny não coincide com a do normal")
        if pn is None:
            continue
        i = indice[pn]
        if para_shiny.setdefault(i, ps) != ps:
            raise ErroConversao(
                f"índice {i} ({pn}) vira duas cores no shiny: {para_shiny[i]} e {ps}; "
                "não dá para ter uma só folha para as duas paletas")

    def paleta(cores_por_indice):
        pal = [COR_INDICE_0] + [cores_por_indice.get(i, (0, 0, 0)) for i in range(1, 16)]
        return pal

    pal_normal = paleta({i: cor for cor, i in indice.items()})
    pal_shiny = paleta(para_shiny)
    indices = [0 if c is None else indice[c] for c in normal]
    return reorganizar_em_folha(indices), pal_normal, pal_shiny


def reorganizar_em_folha(indices):
    """Os pixels vêm quadro a quadro; a folha de 256x32 é linha a linha com os quadros lado a lado."""
    n = TAMANHO_QUADRO
    quadros = len(indices) // (n * n)
    folha = []
    for y in range(n):
        for f in range(quadros):
            ini = f * n * n + y * n
            folha.extend(indices[ini:ini + n])
    return folha


def montar_png(indices, pal):
    quadros = len(DIRECOES) * QUADROS_POR_DIRECAO
    im = Image.new("P", (TAMANHO_QUADRO * quadros, TAMANHO_QUADRO))
    im.putpalette([c for cor in pal for c in cor])
    im.putdata(indices)
    return im


def texto_pal(pal):
    linhas = ["JASC-PAL", "0100", "16"] + [f"{r} {g} {b}" for r, g, b in pal]
    return "\r\n".join(linhas) + "\r\n"


def nome_arquivo(sufixo_constante):
    return sufixo_constante.lower()


def nome_c(sufixo_constante):
    return "".join(p.capitalize() for p in sufixo_constante.split("_"))


def texto_tabela(dexes, nomes):
    especies_h = (REPO / "include" / "constants" / "species.h").read_text(encoding="utf-8")
    por_dex = []
    for dex in dexes:
        suf = nomes[dex]
        if not re.search(rf"^#define SPECIES_{suf}\s", especies_h, re.M):
            raise ErroConversao(f"SPECIES_{suf} não existe em include/constants/species.h")
        por_dex.append((dex, suf))
    l = [
        "// Gerado por tools/seguidores/converter.py a partir do pacote HGSS do Veekun; não editar à mão.",
        "// Uma entrada por espécie, em ordem da Pokédex: folha de 8 quadros 32x32 (sul, norte, oeste, leste; 2 cada),",
        "// paleta normal e paleta shiny com o mesmo mapeamento de índices.",
        "",
    ]
    for _, suf in por_dex:
        f, c = nome_arquivo(suf), nome_c(suf)
        l += [
            f'static const u16 sFollowerPic_{c}[] = INCBIN_U16("graphics/object_events/pics/seguidores/{f}.4bpp");',
            f'static const u16 sFollowerPal_{c}[] = INCBIN_U16("graphics/object_events/palettes/seguidores/{f}.gbapal");',
            f'static const u16 sFollowerPalShiny_{c}[] = INCBIN_U16("graphics/object_events/palettes/seguidores/{f}_shiny.gbapal");',
            f"static const struct SpriteFrameImage sFollowerPicTable_{c}[] = {{",
        ]
        l += [f"    overworld_frame(sFollowerPic_{c}, 4, 4, {q})," for q in range(8)]
        l += ["};", ""]
    l.append("const struct FollowerSpecies gFollowerSpecies[FOLLOWER_SPECIES_COUNT] = {")
    for _, suf in por_dex:
        c = nome_c(suf)
        l += [
            "    {",
            f"        .species = SPECIES_{suf},",
            f"        .images = sFollowerPicTable_{c},",
            f"        .palette = sFollowerPal_{c},",
            f"        .shinyPalette = sFollowerPalShiny_{c},",
            "    },",
        ]
    l += [
        "};",
        "",
        "// Imagens do gráfico dinâmico antes de a espécie ser resolvida em tempo de execução.",
        f"#define FOLLOWER_DEFAULT_IMAGES sFollowerPicTable_{nome_c(por_dex[0][1])}",
        "",
    ]
    return "\n".join(l), len(por_dex)


def gerar(origem, dexes, saida):
    """Grava tudo sob `saida`; devolve o número de espécies. Levanta ErroConversao."""
    nomes = ler_nomes_dex()
    for dex in dexes:
        if dex not in nomes:
            raise ErroConversao(f"espécie {dex} fora da Pokédex nacional")
    tabela, n = texto_tabela(dexes, nomes)
    (saida / PICS_REL).mkdir(parents=True, exist_ok=True)
    (saida / PALS_REL).mkdir(parents=True, exist_ok=True)
    for dex in dexes:
        nome = nome_arquivo(nomes[dex])
        try:
            indices, pal_n, pal_s = converter_especie(origem, dex)
        except ErroConversao as e:
            raise ErroConversao(f"{nome} (#{dex}): {e}") from e
        montar_png(indices, pal_n).save(saida / PICS_REL / f"{nome}.png", bits=4)
        for sufixo, pal in (("", pal_n), ("_shiny", pal_s)):
            (saida / PALS_REL / f"{nome}{sufixo}.pal").write_bytes(texto_pal(pal).encode("ascii"))
    (saida / TABELA_REL).parent.mkdir(parents=True, exist_ok=True)
    (saida / TABELA_REL).write_bytes(tabela.encode("utf-8"))
    cabecalho = saida / FOLLOWER_H_REL
    if cabecalho.is_file():  # mantém FOLLOWER_SPECIES_COUNT igual à tabela
        texto = cabecalho.read_text(encoding="utf-8")
        cabecalho.write_text(RE_CONTAGEM.sub(rf"\g<1>{n}", texto), encoding="utf-8", newline="\n")
    return n


def comparar(gerado, repo, dexes):
    """Lista as diferenças entre o que `gerado` tem e o que está em `repo`."""
    nomes = ler_nomes_dex()
    difs = []
    arquivos = [TABELA_REL]
    for dex in dexes:
        nome = nome_arquivo(nomes[dex])
        arquivos += [PICS_REL / f"{nome}.png", PALS_REL / f"{nome}.pal", PALS_REL / f"{nome}_shiny.pal"]
    for rel in arquivos:
        novo, velho = gerado / rel, repo / rel
        if not velho.is_file():
            difs.append(f"falta no repositório: {rel}")
        elif rel.suffix == ".png":
            a, b = Image.open(novo), Image.open(velho)
            if (a.mode, a.size, a.tobytes(), a.getpalette()[:48]) != (b.mode, b.size, b.tobytes(), b.getpalette()[:48]):
                difs.append(f"diferente: {rel}")
        elif novo.read_bytes() != velho.read_bytes():
            difs.append(f"diferente: {rel}")
    cabecalho = repo / FOLLOWER_H_REL
    if cabecalho.is_file():
        m = RE_CONTAGEM.search(cabecalho.read_text(encoding="utf-8"))
        if not m or not m.group(0).endswith(f" {len(dexes)}"):
            difs.append(f"{FOLLOWER_H_REL}: FOLLOWER_SPECIES_COUNT não é {len(dexes)}")
    # arquivos de espécie que não estão na lista
    esperados = {rel.name for rel in arquivos}
    for pasta, padrao in ((PICS_REL, "*.png"), (PALS_REL, "*.pal")):
        if (repo / pasta).is_dir():
            for p in sorted((repo / pasta).glob(padrao)):
                if p.name not in esperados:
                    difs.append(f"sobra no repositório: {pasta / p.name}")
    return difs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--origem", type=Path, default=ORIGEM_PADRAO, help="pasta pokemon/overworld do Veekun")
    ap.add_argument("--especies", default=None, help="ex.: 1-9,25,26,172 ou 'todas' (padrão: as 12 de ESPECIES_PADRAO)")
    ap.add_argument("--saida", type=Path, default=REPO, help="raiz onde gravar (padrão: o repositório)")
    ap.add_argument("--conferir", action="store_true", help="refaz num diretório temporário e compara com o repositório")
    args = ap.parse_args(argv)
    dexes = lista_especies(args.especies) if args.especies else list(ESPECIES_PADRAO)
    try:
        if args.conferir:
            with tempfile.TemporaryDirectory() as tmp:
                gerar(args.origem, dexes, Path(tmp))
                difs = comparar(Path(tmp), args.saida, dexes)
            if difs:
                print("\n".join(difs), file=sys.stderr)
                return 1
            print(f"ok: {len(dexes)} espécies iguais ao repositório")
            return 0
        n = gerar(args.origem, dexes, args.saida)
    except ErroConversao as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    print(f"{n} espécies gravadas em {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
