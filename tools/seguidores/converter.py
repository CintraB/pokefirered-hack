"""Seguidores (POK-48/POK-53): converte os sprites de overworld do Veekun (HGSS) em folhas indexadas 4bpp + paletas + tabela C.

    python3 -I tools/seguidores/converter.py                      # as 390 espécies (o mesmo que --especies todas)
    python3 -I tools/seguidores/converter.py --especies 1-9,25    # qualquer lista de números da Pokédex nacional
    python3 -I tools/seguidores/converter.py --conferir           # refaz num diretório temporário e compara
    python3 -I tools/seguidores/converter.py --previa saida.png   # grade normal/shiny de todas as entradas (não grava)

Lê, em `--origem` (padrão: `.superpowers/brainstorm/seguidores/todos/pokemon/overworld`, fora do Git), o layout do
pacote do Veekun: `<direção>/<arquivo>.png` e `<direção>/frame2/<arquivo>.png` para `down`, `up`, `left` e `right`,
o mesmo sob `shiny/`, e as fêmeas sob `female/` e `shiny/female/`. Para cada espécie grava (a partir de `--saida`,
padrão a raiz do repositório):

    graphics/object_events/pics/seguidores/<nome>.png            folha 256x32 (8 quadros 32x32), PNG 4 bits indexado
    graphics/object_events/pics/seguidores/grandes/<nome>.png    folha 512x64 (8 quadros 64x64) dos 7 grandes
    graphics/object_events/palettes/seguidores/<nome>.pal        JASC 16 cores (índice 0 = transparente)
    graphics/object_events/palettes/seguidores/<nome>_shiny.pal  idem, shiny
    src/data/object_events/follower_species.h                    `gFollowerSpecies[dex - 1]`, ordem da Pokédex

Variantes: fêmea (`<nome>_f`, se o pacote tem `female/down/<dex>.png`), as 28 letras do Unown (`unown_<letra>`, na
ordem de GetUnownLetterByPersonality: a..z, exclamation, question; a entrada base do Unown usa a letra A) e o Deoxys,
que usa `386-attack` (a forma da batalha no FireRed). Uma variante reaproveita a paleta da espécie quando todas as
cores dela (normal e shiny) já estão lá; senão ganha `.pal` própria.

A folha tem 8 quadros lado a lado: sul (2), norte (2), oeste (2), leste (2), na ordem de `DIRECOES`; o leste tem
desenho próprio. Quadros 32x32 ou 64x64 (os 8 do mesmo tamanho). O índice de cada pixel vem do sprite normal (cores
numeradas pela ordem em que aparecem, varrendo os quadros da esquerda para a direita, linha a linha; índice 0 é só
transparência) e a paleta shiny sai da correspondência pixel a pixel normal -> shiny. A conversão FALHA (código 1) se
um índice do normal corresponder a duas cores no shiny, se a transparência não coincidir, se um quadro tiver tamanho
diferente de 32x32/64x64, se houver pixel semitransparente ou se a folha tiver mais de 15 cores — salvo as exceções
conhecidas do pacote em `PARES_NORMAL_SHINY` e `SO_NO_SHINY` (abaixo). `--conferir` compara o que está no repositório
com o que a conversão gera agora (PNG pelos pixels e pela paleta; o resto byte a byte).

Só Pillow e a biblioteca padrão são usados.
"""

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
ORIGEM_PADRAO = REPO / ".superpowers" / "brainstorm" / "seguidores" / "todos" / "pokemon" / "overworld"
PICS_REL = Path("graphics/object_events/pics/seguidores")
PALS_REL = Path("graphics/object_events/palettes/seguidores")
TABELA_REL = Path("src/data/object_events/follower_species.h")
FOLLOWER_H_REL = Path("include/follower.h")

NUM_ESPECIES_DEX = 390
# Os 4 depois do Deoxys (POK-54): o número do arquivo no pacote do Veekun é o da Pokédex nacional real (Gible 443,
# Gabite 444, Garchomp 445, Darkrai 491), diferente do número interno da tabela (387..390). Todos 32x32 e sem fêmea
# (o pacote tem fêmea de 443-445, mas ficam de fora: FEMEAS e GRANDES não mudam).
EXTRAS = {387: 443, 388: 444, 389: 445, 390: 491}
# ordem dos quadros na folha (sul, norte, oeste, leste; 2 quadros cada) = pasta do Veekun
DIRECOES = ["down", "up", "left", "right"]
QUADROS_POR_DIRECAO = 2
QUADROS = len(DIRECOES) * QUADROS_POR_DIRECAO
TAMANHOS_QUADRO = (32, 64)
PASTA_GRANDES = "grandes"
MAX_CORES = 15  # índice 0 é a transparência
COR_INDICE_0 = (115, 197, 164)  # a mesma que as paletas de NPC usam no índice 0
RE_CONTAGEM = re.compile(r"(#define FOLLOWER_SPECIES_COUNT\s+)\d+")

# Os 7 grandes (quadros 64x64) e as 6 espécies com fêmea própria no pacote, até a dex 386. A conversão FALHA se o
# que o pacote tem divergir destas listas (numa conversão parcial, confere só a interseção com as pedidas).
GRANDES = {208, 249, 250, 321, 382, 383, 384}
FEMEAS = {3, 25, 154, 202, 208, 214}

DEX_UNOWN = 201
LETRAS_UNOWN = [chr(c) for c in range(ord("a"), ord("z") + 1)] + ["exclamation", "question"]
DEX_DEOXYS = 386
FORMA_DEOXYS = "386-attack"  # sDeoxysBaseStats/sprite de batalha do FireRed = Forma Ataque

# Exceções conhecidas do pacote HGSS (conferidas à mão em 03/11/2026):
# - cor do normal que vira duas cores no shiny (a paleta do DS tinha duas entradas com a mesma cor normal e cores
#   shiny diferentes). Nessas, o índice é por par (cor normal, cor shiny): a folha continua uma só e a paleta normal
#   fica com a cor repetida. Fora desta lista, isso é erro.
PARES_NORMAL_SHINY = {13, 80, 81, 82, 123, 255, 261, 284, 315, 335, 351, 357, 359}
# - pixels opacos só no shiny, de uma cor que o normal não tem (no normal a cor coincidiu com a chave de
#   transparência na extração): ficam transparentes nos dois, como no normal.
SO_NO_SHINY = {99: (200, 200, 208), 141: (152, 152, 152)}


class ErroConversao(Exception):
    pass


@dataclass
class Folha:
    """Uma folha convertida: imagens + a paleta que ela usa (própria ou da espécie base)."""
    arquivo: str        # caminho relativo a PICS_REL, sem extensão (ex.: "bulbasaur", "grandes/steelix")
    c: str              # sufixo dos símbolos C (ex.: "Bulbasaur", "Venusaur_F", "UnownA")
    quadro: int         # 32 ou 64
    indices: list
    pal_normal: list
    pal_shiny: list
    pares: dict         # (cor normal, cor shiny) -> índice, só das cores usadas
    pal_c: str          # dono da paleta (o próprio `c` ou o da folha base)
    pal_arquivo: str    # nome do .pal (sem extensão) em PALS_REL

    @property
    def grande(self):
        return self.quadro == 64

    @property
    def paleta_propria(self):
        return self.pal_c == self.c


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


def carregar_quadros(origem, arquivo, shiny, femea=False):
    """Os 8 quadros do Veekun em RGBA, na ordem da folha."""
    base = origem / "shiny" if shiny else origem
    if femea:
        base = base / "female"
    quadros = []
    for d in DIRECOES:
        for sub in ("", "frame2"):
            caminho = base / d / sub / f"{arquivo}.png"
            if not caminho.is_file():
                raise ErroConversao(f"falta {caminho}")
            im = Image.open(caminho).convert("RGBA")
            if im.size[0] != im.size[1] or im.size[0] not in TAMANHOS_QUADRO:
                raise ErroConversao(f"{caminho}: {im.size[0]}x{im.size[1]}, esperado 32x32 ou 64x64")
            if quadros and im.size != quadros[0].size:
                raise ErroConversao(f"{caminho}: {im.size[0]}x{im.size[1]}, os outros quadros são {quadros[0].size}")
            quadros.append(im)
    return quadros


def pixels_da_folha(quadros):
    """Lista de (r, g, b) ou None (transparente), quadro a quadro, linha a linha, na ordem da folha."""
    saida = []
    for q in quadros:
        n = q.size[0]
        dados = q.tobytes()
        for i in range(n * n):
            r, g, b, a = dados[i * 4:i * 4 + 4]
            if a == 0:
                saida.append(None)
            elif a == 255:
                saida.append((r, g, b))
            else:
                raise ErroConversao(f"pixel semitransparente (alfa {a}) em ({i % n}, {i // n})")
    return saida


def paleta(cores_por_indice):
    return [COR_INDICE_0] + [cores_por_indice.get(i, (0, 0, 0)) for i in range(1, 16)]


def converter_pixels(normal, shiny, dex, base=None):
    """-> (índices em ordem de quadro, pal normal, pal shiny, pares) ou None se `base` foi pedida e não serve.

    Com `base` (dict par -> índice de outra folha), só usa os índices dela; devolve None se faltar algum par."""
    so_no_shiny = SO_NO_SHINY.get(dex)
    pares = dict(base) if base is not None else {}
    indices = []
    for pn, ps in zip(normal, shiny):
        if pn is None and ps is not None and ps == so_no_shiny:
            ps = None
        if (pn is None) != (ps is None):
            raise ErroConversao("a transparência do shiny não coincide com a do normal")
        if pn is None:
            indices.append(0)
            continue
        i = pares.get((pn, ps))
        if i is None:
            if base is not None:
                return None
            i = pares[(pn, ps)] = len(pares) + 1
        indices.append(i)
    if len(pares) > MAX_CORES:
        raise ErroConversao(f"{len(pares)} cores no normal; o máximo é {MAX_CORES} (mais o índice 0 transparente)")
    if dex not in PARES_NORMAL_SHINY:
        vistos = {}
        for (pn, ps) in pares:
            if pn in vistos:
                raise ErroConversao(
                    f"índice {pares[(pn, vistos[pn])]} ({pn}) vira duas cores no shiny: {vistos[pn]} e {ps}; "
                    "não dá para ter uma só folha para as duas paletas")
            vistos[pn] = ps
    pal_n = paleta({i: pn for (pn, _), i in pares.items()})
    pal_s = paleta({i: ps for (_, ps), i in pares.items()})
    return indices, pal_n, pal_s, pares


def reorganizar_em_folha(indices, n):
    """Os pixels vêm quadro a quadro; a folha é linha a linha com os quadros lado a lado."""
    quadros = len(indices) // (n * n)
    folha = []
    for y in range(n):
        for f in range(quadros):
            ini = f * n * n + y * n
            folha.extend(indices[ini:ini + n])
    return folha


def converter_folha(origem, dex, fonte, arquivo, c, femea=False, base=None):
    """Converte uma folha; com `base` (Folha), reaproveita a paleta dela se todas as cores couberem."""
    qn = carregar_quadros(origem, fonte, False, femea)
    qs = carregar_quadros(origem, fonte, True, femea)
    if qn[0].size != qs[0].size:
        raise ErroConversao(f"normal {qn[0].size} e shiny {qs[0].size} de tamanhos diferentes")
    n = qn[0].size[0]
    normal, shiny = pixels_da_folha(qn), pixels_da_folha(qs)
    if n == 64:
        arquivo = f"{PASTA_GRANDES}/{arquivo}"
    if base is not None:
        r = converter_pixels(normal, shiny, dex, base.pares)
        if r is not None:
            indices, _, _, _ = r
            return Folha(arquivo, c, n, reorganizar_em_folha(indices, n), base.pal_normal, base.pal_shiny,
                         base.pares, base.pal_c, base.pal_arquivo)
    indices, pal_n, pal_s, pares = converter_pixels(normal, shiny, dex)
    return Folha(arquivo, c, n, reorganizar_em_folha(indices, n), pal_n, pal_s, pares, c, Path(arquivo).name)


def montar_png(folha):
    im = Image.new("P", (folha.quadro * QUADROS, folha.quadro))
    im.putpalette([c for cor in folha.pal_normal for c in cor])
    im.putdata(folha.indices)
    return im


def texto_pal(pal):
    linhas = ["JASC-PAL", "0100", "16"] + [f"{r} {g} {b}" for r, g, b in pal]
    return "\r\n".join(linhas) + "\r\n"


def nome_arquivo(sufixo_constante):
    return sufixo_constante.lower()


def nome_c(sufixo_constante):
    return "".join(p.capitalize() for p in sufixo_constante.split("_"))


@dataclass
class Especie:
    dex: int
    constante: str      # sufixo de SPECIES_/NATIONAL_DEX_
    base: Folha
    femea: Folha = None
    formas: list = None  # Unown: 28 Folhas na ordem de LETRAS_UNOWN


def converter_especie(origem, dex, nomes):
    suf = nomes[dex]
    arq, c = nome_arquivo(suf), nome_c(suf)
    if dex == DEX_UNOWN:
        formas = []
        for letra in LETRAS_UNOWN:
            rotulo = letra.upper() if len(letra) == 1 else letra.capitalize()
            formas.append(converter_folha(origem, dex, f"{dex}-{letra}", f"{arq}_{letra}", f"Unown{rotulo}",
                                          base=formas[0] if formas else None))
        return Especie(dex, suf, formas[0], formas=formas)
    fonte = FORMA_DEOXYS if dex == DEX_DEOXYS else str(EXTRAS.get(dex, dex))
    base = converter_folha(origem, dex, fonte, arq, c)
    femea = None
    if dex not in EXTRAS and (origem / "female" / DIRECOES[0] / f"{dex}.png").is_file():
        femea = converter_folha(origem, dex, str(dex), f"{arq}_f", f"{c}_F", femea=True, base=base)
    return Especie(dex, suf, base, femea=femea)


def folhas_de(especie):
    """Todas as folhas distintas da espécie (a base do Unown é a letra A, já em `formas`)."""
    if especie.formas:
        return list(especie.formas)
    return [especie.base] + ([especie.femea] if especie.femea else [])


def bool_c(v):
    return "TRUE" if v else "FALSE"


def linhas_entrada(f, species, indent, forms="NULL", form_count=0, female="NULL"):
    p = " " * indent
    return [
        f"{p}.species = SPECIES_{species},",
        f"{p}.large = {bool_c(f.grande)},",
        f"{p}.formCount = {form_count},",
        f"{p}.images = sFollowerPicTable_{f.c},",
        f"{p}.palette = sFollowerPal_{f.pal_c},",
        f"{p}.shinyPalette = sFollowerPalShiny_{f.pal_c},",
        f"{p}.female = {female},",
        f"{p}.forms = {forms},",
    ]


def texto_tabela(especies):
    especies_h = (REPO / "include" / "constants" / "species.h").read_text(encoding="utf-8")
    for e in especies:
        if not re.search(rf"^#define SPECIES_{e.constante}\s", especies_h, re.M):
            raise ErroConversao(f"SPECIES_{e.constante} não existe em include/constants/species.h")
    l = [
        "// Gerado por tools/seguidores/converter.py a partir do pacote HGSS do Veekun; não editar à mão.",
        "// Uma entrada por espécie, indexada pelo número da Pokédex nacional - 1: folha de 8 quadros (sul, norte, oeste,",
        "// leste; 2 cada) de 32x32, ou 64x64 nos grandes (`large`), paleta normal e paleta shiny com o mesmo mapeamento",
        "// de índices. Variantes: fêmea (`female`) e as 28 letras do Unown (`forms`, ordem de GetUnownLetterByPersonality).",
        "",
    ]
    for e in especies:
        for f in folhas_de(e):
            tiles = f.quadro // 8
            l.append(f'static const u16 sFollowerPic_{f.c}[] = INCBIN_U16("{PICS_REL.as_posix()}/{f.arquivo}.4bpp");')
            if f.paleta_propria:
                l += [
                    f'static const u16 sFollowerPal_{f.c}[] = INCBIN_U16("{PALS_REL.as_posix()}/{f.pal_arquivo}.gbapal");',
                    f'static const u16 sFollowerPalShiny_{f.c}[] = INCBIN_U16("{PALS_REL.as_posix()}/{f.pal_arquivo}_shiny.gbapal");',
                ]
            l.append(f"static const struct SpriteFrameImage sFollowerPicTable_{f.c}[] = {{")
            l += [f"    overworld_frame(sFollowerPic_{f.c}, {tiles}, {tiles}, {q})," for q in range(QUADROS)]
            l += ["};", ""]
        if e.femea:
            l.append(f"static const struct FollowerSpecies sFollowerFemale_{nome_c(e.constante)} = {{")
            l += linhas_entrada(e.femea, e.constante, 4)
            l += ["};", ""]
        if e.formas:
            l.append(f"static const struct FollowerSpecies sFollowerForms_{nome_c(e.constante)}[{len(e.formas)}] = {{")
            for f in e.formas:
                l.append("    {")
                l += linhas_entrada(f, e.constante, 8)
                l.append("    },")
            l += ["};", ""]
    l.append("const struct FollowerSpecies gFollowerSpecies[FOLLOWER_SPECIES_COUNT] = {")
    for e in especies:
        c = nome_c(e.constante)
        l.append(f"    [NATIONAL_DEX_{e.constante} - 1] = {{")
        l += linhas_entrada(
            e.base, e.constante, 8,
            forms=f"sFollowerForms_{c}" if e.formas else "NULL",
            form_count=len(e.formas) if e.formas else 0,
            female=f"&sFollowerFemale_{c}" if e.femea else "NULL")
        l.append("    },")
    # o gráfico 64x64 precisa de imagens padrão 64x64 (a liberação dos tiles usa images->size); sem grande na
    # conversão (parcial), a padrão pequena só para compilar
    grande = next((e for e in especies if e.base.grande), especies[0])
    l += [
        "};",
        "",
        "// Imagens dos gráficos dinâmicos (32x32 e 64x64) antes de a espécie ser resolvida em tempo de execução.",
        f"#define FOLLOWER_DEFAULT_IMAGES sFollowerPicTable_{especies[0].base.c}",
        f"#define FOLLOWER_DEFAULT_LARGE_IMAGES sFollowerPicTable_{grande.base.c}",
        "",
    ]
    return "\n".join(l)


def converter_todas(origem, dexes):
    nomes = ler_nomes_dex()
    especies = []
    for dex in dexes:
        if dex not in nomes or dex > NUM_ESPECIES_DEX:
            raise ErroConversao(f"espécie {dex} fora da Pokédex nacional (1..{NUM_ESPECIES_DEX})")
        try:
            especies.append(converter_especie(origem, dex, nomes))
        except ErroConversao as e:
            raise ErroConversao(f"{nome_arquivo(nomes[dex])} (#{dex}): {e}") from e
    conferir_listas(especies, dexes)
    return especies


def conferir_listas(especies, dexes):
    """O pacote tem de ter exatamente os grandes de GRANDES e as fêmeas de FEMEAS (entre as espécies pedidas)."""
    pedidas = set(dexes)
    for rotulo, achadas, esperadas in (
        ("grandes (64x64)", {e.dex for e in especies if e.base.grande}, GRANDES & pedidas),
        ("fêmeas", {e.dex for e in especies if e.femea}, FEMEAS & pedidas),
    ):
        if achadas != esperadas:
            raise ErroConversao(
                f"{rotulo} divergem da lista: sobram {sorted(achadas - esperadas)}, faltam {sorted(esperadas - achadas)}")
    for e in especies:
        if e.femea and e.femea.grande != e.base.grande:
            raise ErroConversao(f"#{e.dex}: a fêmea e a forma padrão têm tamanhos diferentes")
        if e.formas and any(f.grande != e.base.grande for f in e.formas):
            raise ErroConversao(f"#{e.dex}: as formas têm tamanhos diferentes")


def gerar(origem, dexes, saida):
    """Grava tudo sob `saida`; devolve (espécies, caminhos relativos gravados). Levanta ErroConversao."""
    especies = converter_todas(origem, dexes)
    tabela = texto_tabela(especies)
    gravados = [TABELA_REL]
    (saida / PICS_REL / PASTA_GRANDES).mkdir(parents=True, exist_ok=True)
    (saida / PALS_REL).mkdir(parents=True, exist_ok=True)
    for e in especies:
        for f in folhas_de(e):
            rel = PICS_REL / f"{f.arquivo}.png"
            montar_png(f).save(saida / rel, bits=4)
            gravados.append(rel)
            if f.paleta_propria:
                for sufixo, pal in (("", f.pal_normal), ("_shiny", f.pal_shiny)):
                    rel = PALS_REL / f"{f.pal_arquivo}{sufixo}.pal"
                    (saida / rel).write_bytes(texto_pal(pal).encode("ascii"))
                    gravados.append(rel)
    (saida / TABELA_REL).parent.mkdir(parents=True, exist_ok=True)
    (saida / TABELA_REL).write_bytes(tabela.encode("utf-8"))
    cabecalho = saida / FOLLOWER_H_REL
    if cabecalho.is_file():  # a tabela é indexada pela dex: sempre NUM_ESPECIES_DEX posições
        texto = cabecalho.read_text(encoding="utf-8")
        cabecalho.write_text(RE_CONTAGEM.sub(rf"\g<1>{NUM_ESPECIES_DEX}", texto), encoding="utf-8", newline="\n")
    return especies, gravados


def comparar(gerado, repo, gravados):
    """Lista as diferenças entre o que `gerado` tem e o que está em `repo`."""
    difs = []
    for rel in gravados:
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
        if not m or not m.group(0).endswith(f" {NUM_ESPECIES_DEX}"):
            difs.append(f"{FOLLOWER_H_REL}: FOLLOWER_SPECIES_COUNT não é {NUM_ESPECIES_DEX}")
    # arquivos de espécie que não estão na lista
    esperados = {rel.as_posix() for rel in gravados}
    for pasta, padrao in ((PICS_REL, "**/*.png"), (PALS_REL, "*.pal")):
        if (repo / pasta).is_dir():
            for p in sorted((repo / pasta).glob(padrao)):
                rel = p.relative_to(repo).as_posix()
                if rel not in esperados:
                    difs.append(f"sobra no repositório: {rel}")
    return difs


def desenhar_previa(especies, destino):
    """Grade 1:1 com o 1º quadro (sul) normal e shiny de cada folha: espécies, letras do Unown, fêmeas e grandes.

    Rótulos sem acento: a fonte padrão do Pillow só tem ASCII."""
    fundo, texto = (120, 184, 120, 255), (0, 0, 0, 255)

    def rgba(f, pal):
        im = Image.new("RGBA", (f.quadro * QUADROS, f.quadro), (0, 0, 0, 0))
        im.putdata([(0, 0, 0, 0) if i == 0 else (*pal[i], 255) for i in f.indices])
        return im.crop((0, 0, f.quadro, f.quadro))

    secoes = [
        ("Especies 32x32 (normal | shiny)", [(f"{e.dex}", e.base) for e in especies if not e.base.grande]),
        ("Unown: a..z, !, ?", [(l if len(l) == 1 else l[0:5], f) for e in especies if e.formas
                               for l, f in zip(LETRAS_UNOWN, e.formas)]),
        ("Femeas", [(f"{e.dex} F", e.femea) for e in especies if e.femea]),
        ("Grandes 64x64", [(f"{e.dex}", e.base) for e in especies if e.base.grande]
         + [(f"{e.dex} F", e.femea) for e in especies if e.femea and e.femea.grande]),
    ]
    colunas, pad, rot = 16, 6, 12
    largura = colunas * (128 + pad) + pad
    blocos = []
    for titulo, itens in secoes:
        if not itens:
            continue
        lado = max(f.quadro for _, f in itens)
        por_linha = max(1, largura // (2 * lado + pad))
        linhas = (len(itens) + por_linha - 1) // por_linha
        bloco = Image.new("RGBA", (largura, 16 + linhas * (lado + rot + pad)), fundo)
        d = ImageDraw.Draw(bloco)
        d.text((pad, 2), titulo, fill=texto)
        for k, (rotulo, f) in enumerate(itens):
            x = pad + (k % por_linha) * (2 * lado + pad)
            y = 16 + (k // por_linha) * (lado + rot + pad)
            d.text((x, y), rotulo, fill=texto)
            bloco.alpha_composite(rgba(f, f.pal_normal), (x, y + rot))
            bloco.alpha_composite(rgba(f, f.pal_shiny), (x + lado, y + rot))
        blocos.append(bloco)
    im = Image.new("RGBA", (largura, sum(b.size[1] for b in blocos)), fundo)
    y = 0
    for b in blocos:
        im.alpha_composite(b, (0, y))
        y += b.size[1]
    im.save(destino)
    return im.size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--origem", type=Path, default=ORIGEM_PADRAO, help="pasta pokemon/overworld do Veekun")
    ap.add_argument("--especies", default="todas", help="ex.: 1-9,25,26,172 ou 'todas' (padrão)")
    ap.add_argument("--saida", type=Path, default=REPO, help="raiz onde gravar (padrão: o repositório)")
    ap.add_argument("--conferir", action="store_true", help="refaz num diretório temporário e compara com o repositório")
    ap.add_argument("--previa", type=Path, default=None, help="só desenha a grade de prévia neste PNG (não grava nada)")
    args = ap.parse_args(argv)
    dexes = lista_especies(args.especies)
    try:
        if args.previa:
            tamanho = desenhar_previa(converter_todas(args.origem, dexes), args.previa)
            print(f"prévia {tamanho[0]}x{tamanho[1]} em {args.previa}")
            return 0
        if args.conferir:
            with tempfile.TemporaryDirectory() as tmp:
                _, gravados = gerar(args.origem, dexes, Path(tmp))
                difs = comparar(Path(tmp), args.saida, gravados)
            if difs:
                print("\n".join(difs), file=sys.stderr)
                return 1
            print(f"ok: {len(dexes)} espécies iguais ao repositório")
            return 0
        especies, gravados = gerar(args.origem, dexes, args.saida)
    except ErroConversao as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    print(f"{len(especies)} espécies ({len(gravados) - 1} arquivos) gravadas em {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
