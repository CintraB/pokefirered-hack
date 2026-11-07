"""Gible, Gabite, Garchomp e Darkrai (POK-54): fontes da Gen 4 e conversão reproduzível para o jogo.

    python3 -I tools/gen4/gerar.py --baixar          # baixa as fontes para o cache (.superpowers/gen4-fontes/)
    python3 -I tools/gen4/gerar.py                   # converte do cache e grava no repositório
    python3 -I tools/gen4/gerar.py --conferir        # refaz num diretório temporário e compara (sai 1 se divergir)
    python3 -I tools/gen4/gerar.py --folha saida.png # folha 4x: frente, costas, shiny, ícone (2 quadros) e pegada

Fontes (dado não confiável: só lidas como imagem, CSV, tar ou áudio, nunca executadas), uma pasta nova por pacote
dentro do cache, fora do Git:

    batalha/  PokeAPI sprites, Platinum: <dex>.png, shiny_<dex>.png, back_<dex>.png, back_shiny_<dex>.png
    icones/   PokeAPI sprites, ícones da Gen 7 (mesma arte da Gen 4): <dex>.png
    pegadas/  Veekun pokemon-footprints.tar.gz, só os 4 membros pokemon/footprints/<dex>.png
    csv/      PokeAPI data/v2/csv: pokemon_stats, pokemon_species, pokemon_moves, pokemon_egg_groups, moves,
              version_groups
    gritos/   PokeAPI cries (legacy): <dex>.ogg e, se o soundfile decodificar, <dex>.wav (PCM 16 bits)

O .ogg é decodificado no --baixar por um Python filho com o pacote `soundfile` (pip --user), e o WAV decodificado fica
no cache: a conversão usa só Pillow e a biblioteca padrão. Sem WAV no cache, tenta o ffmpeg; sem ffmpeg, copia o grito
de reserva (GRITO_RESERVA) e anota "reserva:<espécie>" em `_gritos`.

Saídas (versionadas, nada à mão):

    tools/gen4/gen4.json                     dados base da Gen 4, golpes, trocas de golpe, gritos
    tools/gen4/coordenadas.json              {nome: {"front": [larg, alt, y_offset], "back": [...], "icone_paleta": n}}
    graphics/pokemon/<nome>/front.png, back.png, normal.pal, shiny.pal, icon.png, footprint.png
    sound/direct_sound_samples/cries/<nome>.wav

`retoques.json` traz os toques à mão aplicados depois da conversão: `"<nome>_front"`/`"<nome>_back"` são listas de
[x, y, índice] no quadro 64x64 (pontos finos que a redução apaga), e `"<nome>_icone_q2"` é o quadro 2 do ícone, desenhado
como [x, y, índice] sobre uma cópia do quadro 1 (outra pose; nunca um deslocamento).
"""

import argparse
import csv
import io
import json
import math
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import wave
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
CACHE = REPO / ".superpowers" / "gen4-fontes"
RETOQUES = AQUI / "retoques.json"

ESPECIES = {"gible": 443, "gabite": 444, "garchomp": 445, "darkrai": 491}

GEN4_JSON = Path("tools/gen4/gen4.json")
COORD_JSON = Path("tools/gen4/coordenadas.json")
MON_DIR = Path("graphics/pokemon")
CRY_DIR = Path("sound/direct_sound_samples/cries")
ICON_PALS = Path("graphics/pokemon/icon_palettes")

URL_SPRITES = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions"
URL_BATALHA = URL_SPRITES + "/generation-iv/platinum/{pasta}{dex}.png"
URL_ICONE = URL_SPRITES + "/generation-vii/icons/{dex}.png"
URL_PEGADAS = "https://veekun.com/static/pokedex/downloads/pokemon-footprints.tar.gz"
URL_CSV = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/{nome}.csv"
URL_GRITO = "https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/legacy/{dex}.ogg"
CSVS = ["pokemon_stats", "pokemon_species", "pokemon_moves", "pokemon_egg_groups", "moves", "version_groups"]
# arquivo no cache -> pasta da URL de batalha
LADOS_BATALHA = {"front": "", "front_s": "shiny/", "back": "back/", "back_s": "back/shiny/"}

# EXP e amizade da Gen 4 não ficam por geração na PokeAPI; tipos, habilidades, cor, altura e peso são os da Gen 4
GEN4_FIXOS = {
    "gible": {"exp": 67, "amizade": 70, "tipos": ["TYPE_DRAGON", "TYPE_GROUND"],
              "habilidades": ["ABILITY_SAND_VEIL", "ABILITY_SAND_VEIL"], "altura": 7, "peso": 205},
    "gabite": {"exp": 144, "amizade": 70, "tipos": ["TYPE_DRAGON", "TYPE_GROUND"],
               "habilidades": ["ABILITY_SAND_VEIL", "ABILITY_SAND_VEIL"], "altura": 14, "peso": 560},
    "garchomp": {"exp": 218, "amizade": 70, "tipos": ["TYPE_DRAGON", "TYPE_GROUND"],
                 "habilidades": ["ABILITY_SAND_VEIL", "ABILITY_SAND_VEIL"], "altura": 19, "peso": 950},
    "darkrai": {"exp": 210, "amizade": 0, "tipos": ["TYPE_DARK", "TYPE_DARK"],
                "habilidades": ["ABILITY_BAD_DREAMS", "ABILITY_BAD_DREAMS"], "altura": 15, "peso": 505},
}
# ids das tabelas de apoio da PokeAPI (pokemon_colors, growth_rates, egg_groups, stats, pokemon_move_methods)
CORES = {1: "BODY_COLOR_BLACK", 2: "BODY_COLOR_BLUE", 3: "BODY_COLOR_BROWN", 4: "BODY_COLOR_GRAY",
         5: "BODY_COLOR_GREEN", 6: "BODY_COLOR_PINK", 7: "BODY_COLOR_PURPLE", 8: "BODY_COLOR_RED",
         9: "BODY_COLOR_WHITE", 10: "BODY_COLOR_YELLOW"}
CRESCIMENTO = {1: "GROWTH_SLOW", 2: "GROWTH_MEDIUM_FAST", 3: "GROWTH_FAST", 4: "GROWTH_MEDIUM_SLOW",
               5: "GROWTH_ERRATIC", 6: "GROWTH_FLUCTUATING"}
GRUPOS_OVO = {1: "EGG_GROUP_MONSTER", 2: "EGG_GROUP_WATER_1", 3: "EGG_GROUP_BUG", 4: "EGG_GROUP_FLYING",
              5: "EGG_GROUP_FIELD", 6: "EGG_GROUP_FAIRY", 7: "EGG_GROUP_GRASS", 8: "EGG_GROUP_HUMAN_LIKE",
              9: "EGG_GROUP_WATER_3", 10: "EGG_GROUP_MINERAL", 11: "EGG_GROUP_AMORPHOUS", 12: "EGG_GROUP_WATER_2",
              13: "EGG_GROUP_DITTO", 14: "EGG_GROUP_DRAGON", 15: "EGG_GROUP_UNDISCOVERED"}
ORDEM_STATS = [1, 2, 3, 6, 4, 5]  # PokeAPI: 1 hp, 2 atk, 3 def, 4 spa, 5 spd, 6 spe -> HP, Atk, Def, Spe, SpA, SpD
METODO_NIVEL, METODO_OVO, METODO_TUTOR, METODO_MAQUINA = 1, 2, 3, 4
GRUPO_NIVEL = "platinum"
GRUPOS_OUTROS = ["platinum", "heartgold-soulsilver"]
GERACAO_DO_JOGO = 3  # golpes da Gen 1-3 têm o mesmo número no moves.h do jogo

TROCAS = {
    "fire-fang": "MOVE_FIRE_PUNCH",
    "ominous-wind": "MOVE_ASTONISH",
    "nasty-plot": "MOVE_CALM_MIND",
    "dark-pulse": "MOVE_CRUNCH",
    "dragon-rush": "MOVE_DRAGON_RUSH",
    "dark-void": "MOVE_DARK_VOID",
}
GOLPES_NOVOS = {"MOVE_DRAGON_RUSH", "MOVE_DARK_VOID"}  # ainda não existem no moves.h (tasks seguintes)

GRITO_RESERVA = {"gible": "bagon", "gabite": "shelgon", "garchomp": "salamence", "darkrai": "dusclops"}
GRITO_TAXA = 10512
GRITO_MAX_S = 1.5
GRITO_PICO = 0.95          # pico depois da normalização
GRITO_FADE_S = 0.03        # fade-out quando o grito é cortado em 1,5 s

COR_INDICE_0 = (152, 208, 160)  # não aparece no jogo (transparência)
MAX_CORES = 15
BASE_FRENTE, BASE_COSTAS = 59, 57  # última linha opaca no quadro 64x64
BASE_ICONE = 29
PESO_CONTORNO, PESO_VAZIO = 1.6, 0.85


# =====================================================================================================================
# Baixar (fontes = dado não confiável)
# =====================================================================================================================
def _baixar_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pokefirered-gen4/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        if r.status != 200:
            raise RuntimeError(f"{url}: HTTP {r.status}")
        return r.read()


def _pasta_nova(nome):
    pasta = CACHE / nome
    if pasta.exists():
        shutil.rmtree(pasta)
    pasta.mkdir(parents=True)
    return pasta


def _png_valido(dados, url):
    if not dados.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"{url}: não é PNG")
    return dados


# decodificador do grito: roda num Python filho (-P: sem o diretório atual no sys.path; cwd = pasta vazia), que enxerga
# o soundfile instalado com pip --user. Só lê o .ogg e grava um WAV PCM 16 bits.
DECODIFICAR_OGG = (
    "import sys, soundfile\n"
    "dados, taxa = soundfile.read(sys.argv[1], dtype='int16', always_2d=True)\n"
    "soundfile.write(sys.argv[2], dados, taxa, subtype='PCM_16', format='WAV')\n"
)


def _decodificar_ogg(ogg, wav):
    with tempfile.TemporaryDirectory() as vazio:
        r = subprocess.run([sys.executable, "-P", "-c", DECODIFICAR_OGG, str(ogg), str(wav)], cwd=vazio,
                           capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        wav.unlink(missing_ok=True)
        return r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"saída {r.returncode}"
    return None


def baixar():
    pasta = _pasta_nova("batalha")
    for dex in ESPECIES.values():
        for lado, sub in LADOS_BATALHA.items():
            url = URL_BATALHA.format(pasta=sub, dex=dex)
            prefixo = {"front": "", "front_s": "shiny_", "back": "back_", "back_s": "back_shiny_"}[lado]
            (pasta / f"{prefixo}{dex}.png").write_bytes(_png_valido(_baixar_url(url), url))
    print("batalha: ok")

    pasta = _pasta_nova("icones")
    for dex in ESPECIES.values():
        url = URL_ICONE.format(dex=dex)
        (pasta / f"{dex}.png").write_bytes(_png_valido(_baixar_url(url), url))
    print("icones: ok")

    pasta = _pasta_nova("pegadas")
    pacote = _baixar_url(URL_PEGADAS)
    with tarfile.open(fileobj=io.BytesIO(pacote), mode="r:gz") as tar:
        membros = {m.name: m for m in tar.getmembers()}
        for dex in ESPECIES.values():
            nome = f"pokemon/footprints/{dex}.png"
            m = membros.get(nome)
            if m is None or not m.isfile() or m.size > 64 * 1024:
                raise RuntimeError(f"pegadas: membro {nome} ausente ou suspeito")
            (pasta / f"{dex}.png").write_bytes(_png_valido(tar.extractfile(m).read(), nome))
    print("pegadas: ok")

    pasta = _pasta_nova("csv")
    for nome in CSVS:
        (pasta / f"{nome}.csv").write_bytes(_baixar_url(URL_CSV.format(nome=nome)))
    print("csv: ok")

    pasta = _pasta_nova("gritos")
    for nome, dex in ESPECIES.items():
        url = URL_GRITO.format(dex=dex)
        dados = _baixar_url(url)
        if not dados.startswith(b"OggS"):
            raise RuntimeError(f"{url}: não é Ogg")
        ogg = pasta / f"{dex}.ogg"
        ogg.write_bytes(dados)
        erro = _decodificar_ogg(ogg, pasta / f"{dex}.wav")
        print(f"grito {nome}: " + ("decodificado" if erro is None else f"sem decodificar ({erro})"))


# =====================================================================================================================
# Utilidades de imagem e paleta
# =====================================================================================================================
def q(c):
    return tuple(v & 0xF8 for v in c[:3])


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def ler_jasc(caminho):
    v = Path(caminho).read_text().split()
    n = int(v[2])
    nums = list(map(int, v[3:3 + n * 3]))
    return [tuple(nums[i:i + 3]) for i in range(0, n * 3, 3)]


def jasc(pal):
    return "JASC-PAL\r\n0100\r\n16\r\n" + "".join(f"{r} {g} {b}\r\n" for r, g, b in pal)


def opacos(im):
    """{(x, y): rgb de 5 bits} dos pixels opacos."""
    im = im.convert("RGBA")
    px = im.load()
    return {(x, y): q(px[x, y]) for y in range(im.height) for x in range(im.width) if px[x, y][3] >= 128}


def png_indexado(dados, largura, altura, pal):
    p = Image.new("P", (largura, altura))
    p.putpalette([c for t in pal for c in t] + [0] * (768 - 3 * len(pal)))
    p.putdata(dados)
    return p


def renderizar(dados, largura, altura, pal):
    """RGBA de um mapa de índices (índice 0 = transparente)."""
    im = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    px = im.load()
    for i, v in enumerate(dados):
        if v:
            px[i % largura, i // largura] = tuple(pal[v]) + (255,)
    return im


def recolorir(png, pal):
    """RGBA de um PNG indexado com outra paleta (índice 0 = transparente)."""
    im = Image.open(png)
    return renderizar(list(im.tobytes()), im.width, im.height, pal)  # modo P: 1 byte por pixel


def y_offset(png):
    """63 - última linha opaca (índice != 0) do quadro 64x64: o mesmo y_offset de front/back_pic_coordinates.h."""
    im = Image.open(png)
    px = im.load()
    ultima = max(y for y in range(im.height) for x in range(im.width) if px[x, y] != 0)
    return 63 - ultima


def tamanho_coord(png):
    """[largura, altura] do recorte opaco arredondados para cima em múltiplos de 8 (MON_COORDS_SIZE)."""
    im = Image.open(png)
    px = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y] != 0]
    w = max(p[0] for p in pts) - min(p[0] for p in pts) + 1
    h = max(p[1] for p in pts) - min(p[1] for p in pts) + 1
    return [min(64, 8 * math.ceil(w / 8)), min(64, 8 * math.ceil(h / 8))]


def ler_retoques():
    return json.loads(RETOQUES.read_text(encoding="utf-8"))


def aplicar_pixels(dados, largura, pixels, chave):
    altura = len(dados) // largura
    for x, y, i in pixels:
        if not (0 <= x < largura and 0 <= y < altura and 0 <= i <= MAX_CORES):
            raise ValueError(f"retoques.json {chave}: pixel fora do quadro ({x}, {y}, {i})")
        dados[y * largura + x] = i


# =====================================================================================================================
# Sprites de batalha
# =====================================================================================================================
def reduzir_pares(contagem, limite=MAX_CORES):
    """Junta os pares (normal, shiny) mais parecidos (custo = usos x distância² nas 6 coordenadas) até sobrarem `limite`."""
    troca = {c: c for c in contagem}
    uso = dict(contagem)
    while len(uso) > limite:
        melhor = None
        for a in sorted(uso):
            for b in sorted(uso):
                if a == b:
                    continue
                custo = uso[a] * dist(a[0] + a[1], b[0] + b[1])
                if melhor is None or custo < melhor[0]:
                    melhor = (custo, a, b)
        _, a, b = melhor
        uso[b] += uso.pop(a)
        for k, v in troca.items():
            if v == a:
                troca[k] = b
    return troca


def reduzir_maioria(idx, w, h, s, escuro):
    """Reduz o mapa de índices ((x, y) -> i; ausente = vazio) pela fração s, com voto por área; o contorno pesa mais."""
    ow, oh = max(1, round(w * s)), max(1, round(h * s))
    out = {}
    for oy in range(oh):
        y0, y1 = oy / s, (oy + 1) / s
        for ox in range(ow):
            x0, x1 = ox / s, (ox + 1) / s
            votos = {}
            for sy in range(int(y0), min(h, math.ceil(y1))):
                fy = min(y1, sy + 1) - max(y0, sy)
                for sx in range(int(x0), min(w, math.ceil(x1))):
                    fx = min(x1, sx + 1) - max(x0, sx)
                    i = idx.get((sx, sy), 0)
                    peso = fx * fy * (PESO_CONTORNO if i == escuro else PESO_VAZIO if i == 0 else 1.0)
                    votos[i] = votos.get(i, 0) + peso
            i = max(sorted(votos), key=lambda k: votos[k])
            if i:
                out[(ox, oy)] = i
    return out, ow, oh


def converter_batalha(nome, fontes=CACHE, retoques=None):
    """Frente e costas 64x64 com uma paleta só (normal e shiny nos mesmos índices).

    Devolve {"front": [4096 índices], "back": [...], "normal": pal16, "shiny": pal16, "escala": {lado: s},
    "recorte": {lado: (w, h)}}.
    """
    dex = ESPECIES[nome]
    pasta = Path(fontes) / "batalha"
    arqs = {"front": f"{dex}.png", "front_s": f"shiny_{dex}.png", "back": f"back_{dex}.png",
            "back_s": f"back_shiny_{dex}.png"}
    im = {k: Image.open(pasta / v) for k, v in arqs.items()}
    contagem, pares_px = {}, {}
    for lado in ("front", "back"):
        n, s = opacos(im[lado]), opacos(im[lado + "_s"])
        if set(n) != set(s):
            raise ValueError(f"{nome} {lado}: transparência diferente no shiny")
        pares_px[lado] = {p: (n[p], s[p]) for p in n}
        for par in pares_px[lado].values():
            contagem[par] = contagem.get(par, 0) + 1
    troca = reduzir_pares(contagem) if len(contagem) > MAX_CORES else {c: c for c in contagem}
    finais = sorted(set(troca.values()), key=lambda p: (lum(p[0]), p))
    indice = {p: i + 1 for i, p in enumerate(finais)}
    escuro = 1  # o mais escuro é o contorno
    resto = MAX_CORES - len(finais)
    saida = {
        "normal": [COR_INDICE_0] + [p[0] for p in finais] + [(0, 0, 0)] * resto,
        "shiny": [COR_INDICE_0] + [p[1] for p in finais] + [(0, 0, 0)] * resto,
        "escala": {}, "recorte": {},
    }
    if retoques is None:
        retoques = ler_retoques()
    for lado, base in (("front", BASE_FRENTE), ("back", BASE_COSTAS)):
        mapa = {p: indice[troca[par]] for p, par in pares_px[lado].items()}
        bx0 = min(p[0] for p in mapa)
        by0 = min(p[1] for p in mapa)
        w = max(p[0] for p in mapa) - bx0 + 1
        h = max(p[1] for p in mapa) - by0 + 1
        local = {(x - bx0, y - by0): i for (x, y), i in mapa.items()}
        s = min(1.0, 64 / w, (base + 1) / h)
        if s >= 1.0:
            red, ow, oh = local, w, h
        else:
            red, ow, oh = reduzir_maioria(local, w, h, s, escuro)
        ox, oy = (64 - ow) // 2, base + 1 - oh
        dados = [0] * 64 * 64
        for (x, y), i in red.items():
            dados[(y + oy) * 64 + x + ox] = i
        aplicar_pixels(dados, 64, retoques.get(f"{nome}_{lado}", []), f"{nome}_{lado}")
        saida[lado] = dados
        saida["escala"][lado] = s
        saida["recorte"][lado] = (w, h)
    return saida


# =====================================================================================================================
# Ícone
# =====================================================================================================================
def paletas_icone(repo=REPO):
    return [ler_jasc(repo / ICON_PALS / f"icon_palette_{i}.pal") for i in range(3)]


def lab(c):
    """RGB (0-255, sRGB) -> CIELAB (D65)."""
    def linear(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(v) for v in c[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


def distancia_de_tom(a, b):
    """Distância em LCh (CIELAB) que pesa o tom: sqrt((dL/2)² + dC² + 2·dH²).

    Escolhe a paleta do ícone. No RGB o azul do Garchomp fica mais perto do roxo da paleta 0 que do azul da paleta 2;
    no Delta E puro o azul apagado do Gible cai no cinza da paleta 2. Pesar o tom e aliviar a luz acerta os dois.
    """
    la, aa, ba = lab(a)
    lb, ab, bb = lab(b)
    dl = la - lb
    dc = math.hypot(aa, ba) - math.hypot(ab, bb)
    dh2 = max(0.0, (aa - ab) ** 2 + (ba - bb) ** 2 - dc ** 2)
    return math.sqrt((dl / 2) ** 2 + dc ** 2 + 2 * dh2)


def erros_paleta_icone(cores, paletas):
    """Soma, por pixel, da distância de tom à cor mais próxima (índices 1..15) de cada paleta de ícone."""
    return [sum(min(distancia_de_tom(c, p) for p in pal[1:]) for c in cores) for pal in paletas]


def converter_icone(nome, fontes=CACHE, retoques=None, repo=REPO):
    """Ícone 32x64 (2 quadros 32x32). Devolve (dados, n da paleta, paleta)."""
    dex = ESPECIES[nome]
    px = opacos(Image.open(Path(fontes) / "icones" / f"{dex}.png"))
    paletas = paletas_icone(repo)
    erros = erros_paleta_icone(list(px.values()), paletas)
    n = min(range(3), key=lambda i: (erros[i], i))
    pal = paletas[n]
    bx0 = min(p[0] for p in px)
    by0 = min(p[1] for p in px)
    w = max(p[0] for p in px) - bx0 + 1
    h = max(p[1] for p in px) - by0 + 1
    if w > 32 or h > 32:
        raise ValueError(f"{nome}: ícone {w}x{h} não cabe em 32x32")
    ox, oy = (32 - w) // 2, min(BASE_ICONE + 1, 32) - h
    q1 = [0] * 32 * 32
    for (x, y), c in px.items():
        # o pixel vai para a cor mais próxima no RGB, como na prévia aprovada
        q1[(y - by0 + oy) * 32 + x - bx0 + ox] = min(range(1, 16), key=lambda k: (dist(c, pal[k]), k))
    if retoques is None:
        retoques = ler_retoques()
    chave = f"{nome}_icone_q2"
    if not retoques.get(chave):
        raise ValueError(f"retoques.json: falta o quadro 2 desenhado ({chave})")
    q2 = list(q1)
    aplicar_pixels(q2, 32, retoques[chave], chave)
    return q1 + q2, n, pal


# =====================================================================================================================
# Pegada
# =====================================================================================================================
def converter_pegada(nome, fontes=CACHE):
    """16x16, 1 bit: 1 = pegada (pixel opaco e escuro da fonte)."""
    im = Image.open(Path(fontes) / "pegadas" / f"{ESPECIES[nome]}.png").convert("RGBA")
    if im.size != (16, 16):
        raise ValueError(f"{nome}: pegada {im.size}, esperado 16x16")
    px = im.load()
    out = Image.new("1", (16, 16), 0)
    for y in range(16):
        for x in range(16):
            r, g, b, a = px[x, y]
            out.putpixel((x, y), 1 if a >= 128 and lum((r, g, b)) < 128 else 0)
    return out


# =====================================================================================================================
# Dados e golpes
# =====================================================================================================================
def ler_csv(fontes, nome):
    with open(Path(fontes) / "csv" / f"{nome}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def golpes_do_jogo(repo=REPO):
    """{número: "MOVE_X"} e o conjunto de nomes do include/constants/moves.h."""
    por_num = {}
    for nome, num in re.findall(r"^#define (MOVE_\w+) (\d+)\s*$", (repo / "include/constants/moves.h").read_text(),
                                re.M):
        if nome not in ("MOVES_COUNT",):
            por_num[int(num)] = nome
    return por_num, set(por_num.values())


def maquinas_do_jogo(repo=REPO):
    """[("TM01_FOCUS_PUNCH", "MOVE_FOCUS_PUNCH"), ...] na ordem do jogo (TM01..TM50, HM01..HM08)."""
    nomes = re.findall(r"^#define ITEM_((?:TM|HM)\d\d_\w+) ITEM_(?:TM|HM)\d\d\s*$",
                       (repo / "include/constants/items.h").read_text(), re.M)
    texto = (repo / "src/data/party_menu.h").read_text()
    bloco = re.search(r"sTMHMMoves\[\]\s*=\s*\{(.*?)\};", texto, re.S).group(1)
    golpes = re.findall(r"MOVE_\w+", bloco)
    if len(nomes) != len(golpes):
        raise ValueError(f"{len(nomes)} MT/MO em items.h e {len(golpes)} em sTMHMMoves")
    return list(zip(nomes, golpes))


def tutores_do_jogo(repo=REPO):
    texto = (repo / "src/data/pokemon/tutor_learnsets.h").read_text()
    bloco = re.search(r"sTutorMoves\[TUTOR_MOVE_COUNT\]\s*=\s*\{(.*?)\};", texto, re.S).group(1)
    return re.findall(r"=\s*(MOVE_\w+)", bloco)


def golpe_platinum_por_nivel(nome, fontes=CACHE):
    """[(nível, identificador PokeAPI)] por nível (método 1) na Platinum, na ordem do jogo."""
    grupos = {r["identifier"]: r["id"] for r in ler_csv(fontes, "version_groups")}
    moves = {r["id"]: r for r in ler_csv(fontes, "moves")}
    pid = str(ESPECIES[nome])
    linhas = [r for r in ler_csv(fontes, "pokemon_moves")
              if r["pokemon_id"] == pid and r["version_group_id"] == grupos[GRUPO_NIVEL]
              and int(r["pokemon_move_method_id"]) == METODO_NIVEL]
    linhas.sort(key=lambda r: (int(r["level"]), int(r["order"] or 0), int(r["move_id"])))
    return [(int(r["level"]), moves[r["move_id"]]["identifier"]) for r in linhas]


def dados_especies(fontes=CACHE, repo=REPO):
    por_num, existentes = golpes_do_jogo(repo)
    grupos = {r["identifier"]: r["id"] for r in ler_csv(fontes, "version_groups")}
    ids_outros = {grupos[g] for g in GRUPOS_OUTROS}
    moves = {r["id"]: r for r in ler_csv(fontes, "moves")}
    stats = ler_csv(fontes, "pokemon_stats")
    especies_csv = {r["id"]: r for r in ler_csv(fontes, "pokemon_species")}
    ovos_csv = ler_csv(fontes, "pokemon_egg_groups")
    pokemon_moves = ler_csv(fontes, "pokemon_moves")
    maquinas = maquinas_do_jogo(repo)
    tutores = tutores_do_jogo(repo)

    def no_jogo(move_id):
        m = moves[move_id]
        if int(m["generation_id"]) <= GERACAO_DO_JOGO:
            return por_num[int(move_id)]
        nome = "MOVE_" + m["identifier"].upper().replace("-", "_")
        return nome if nome in existentes else None

    saida, descartados = {}, {}
    for nome, dex in ESPECIES.items():
        pid = str(dex)
        sp = especies_csv[pid]
        st = {int(r["stat_id"]): r for r in stats if r["pokemon_id"] == pid}
        genero = int(sp["gender_rate"])
        e = {
            "dex": dex,
            "stats": [int(st[i]["base_stat"]) for i in ORDEM_STATS],
            "tipos": GEN4_FIXOS[nome]["tipos"],
            "captura": int(sp["capture_rate"]),
            "exp": GEN4_FIXOS[nome]["exp"],
            "evs": [int(st[i]["effort"]) for i in ORDEM_STATS],
            "sexo": "MON_GENDERLESS" if genero < 0 else f"PERCENT_FEMALE({genero * 100 // 8})",
            "ciclos": int(sp["hatch_counter"]),
            "amizade": GEN4_FIXOS[nome]["amizade"],
            "crescimento": CRESCIMENTO[int(sp["growth_rate_id"])],
            "ovos": [],
            "habilidades": GEN4_FIXOS[nome]["habilidades"],
            "cor": CORES[int(sp["color_id"])],
            "altura": GEN4_FIXOS[nome]["altura"],
            "peso": GEN4_FIXOS[nome]["peso"],
        }
        grupos_ovo = sorted(int(r["egg_group_id"]) for r in ovos_csv if r["species_id"] == pid)
        e["ovos"] = [GRUPOS_OVO[g] for g in grupos_ovo] * (2 if len(grupos_ovo) == 1 else 1)

        nivel = []
        for lvl, ident in golpe_platinum_por_nivel(nome, fontes):
            m = next(r for r in moves.values() if r["identifier"] == ident)
            jogo = TROCAS.get(ident) or no_jogo(m["id"])
            if jogo is None:
                raise ValueError(f"{nome}: golpe por nível {ident} (nv {lvl}) não existe no jogo e não tem troca")
            nivel.append([lvl, jogo])
        e["nivel"] = nivel

        def aprende(metodo, ids_grupos):
            return {r["move_id"] for r in pokemon_moves
                    if r["pokemon_id"] == pid and r["version_group_id"] in ids_grupos
                    and int(r["pokemon_move_method_id"]) == metodo}

        por_maquina_ou_tutor = {no_jogo(i) for i in aprende(METODO_MAQUINA, ids_outros) | aprende(METODO_TUTOR, ids_outros)}
        e["mt"] = [mt for mt, golpe in maquinas if golpe in por_maquina_ou_tutor]
        e["tutor"] = [g for g in tutores if g in por_maquina_ou_tutor]
        ovo, fora = [], []
        for i in sorted(aprende(METODO_OVO, ids_outros), key=int):
            jogo = no_jogo(i)
            (ovo if jogo else fora).append(jogo or moves[i]["identifier"])
        e["ovo"] = ovo
        if fora:
            descartados[nome] = fora
        saida[nome] = e
    return saida, descartados


# =====================================================================================================================
# Gritos
# =====================================================================================================================
def _ler_wav_pcm16(caminho):
    with wave.open(str(caminho), "rb") as w:
        canais, largura, taxa, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        bruto = w.readframes(n)
    if largura != 2:
        raise ValueError(f"{caminho}: esperado PCM 16 bits")
    vals = memoryview(bruto).cast("h")
    mono = [sum(vals[i * canais + c] for c in range(canais)) / (canais * 32768.0) for i in range(n)]
    return mono, taxa


def _reamostrar(amostras, taxa):
    """Média por área (filtro caixa) da taxa de origem para GRITO_TAXA; sem dependência externa."""
    r = taxa / GRITO_TAXA
    n_out = int(len(amostras) / r)
    out = []
    for i in range(n_out):
        a, b = i * r, (i + 1) * r
        soma, peso = 0.0, 0.0
        j = int(a)
        while j < b and j < len(amostras):
            f = min(b, j + 1) - max(a, j)
            soma += amostras[j] * f
            peso += f
            j += 1
        out.append(soma / peso if peso else 0.0)
    return out


def _gravar_wav_u8(destino, amostras):
    limite = int(GRITO_TAXA * GRITO_MAX_S)
    # corta silêncio no começo e no fim (abaixo de 2% do pico)
    pico = max((abs(v) for v in amostras), default=0.0) or 1.0
    vivos = [i for i, v in enumerate(amostras) if abs(v) >= 0.02 * pico]
    amostras = amostras[vivos[0]:vivos[-1] + 1] if vivos else amostras
    cortado = len(amostras) > limite
    amostras = amostras[:limite]
    ganho = GRITO_PICO / pico
    if cortado:
        fade = int(GRITO_TAXA * GRITO_FADE_S)
        for k in range(fade):
            amostras[-fade + k] *= (fade - k) / fade
    dados = bytes(max(0, min(255, round(v * ganho * 127) + 128)) for v in amostras)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(GRITO_TAXA)
        w.writeframes(dados)


def converter_grito(nome, destino, fontes=CACHE, repo=REPO):
    """Grava o grito e devolve "real" ou "reserva:<espécie>"."""
    dex = ESPECIES[nome]
    wav = Path(fontes) / "gritos" / f"{dex}.wav"
    ogg = Path(fontes) / "gritos" / f"{dex}.ogg"
    if wav.is_file():
        amostras, taxa = _ler_wav_pcm16(wav)
        _gravar_wav_u8(destino, _reamostrar(amostras, taxa))
        return "real"
    if ogg.is_file() and shutil.which("ffmpeg"):
        destino.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(ogg), "-ac", "1",
                        "-ar", str(GRITO_TAXA), "-acodec", "pcm_u8", "-t", str(GRITO_MAX_S), str(destino)],
                       check=True, timeout=120)
        return "real"
    reserva = GRITO_RESERVA[nome]
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes((repo / CRY_DIR / f"{reserva}.wav").read_bytes())
    return f"reserva:{reserva}"


# =====================================================================================================================
# Gerar, conferir, folha
# =====================================================================================================================
def _json_compacto(obj):
    texto = json.dumps(obj, indent=2, ensure_ascii=False)
    # listas sem lista/objeto dentro ficam numa linha só
    return re.sub(r"\[\s*([^\[\]{}]*?)\s*\]", lambda m: "[" + re.sub(r",\s+", ", ", m.group(1)) + "]", texto) + "\n"


def gerar(raiz, fontes=CACHE):
    """Converte do cache e grava tudo sob `raiz`. Devolve a lista de caminhos relativos gravados."""
    raiz = Path(raiz)
    if not (Path(fontes) / "csv").is_dir():
        raise SystemExit(f"cache ausente em {fontes}: rode --baixar antes")
    retoques = ler_retoques()
    gravados = []

    def gravar(rel, conteudo=None, imagem=None, **kw):
        destino = raiz / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        if imagem is not None:
            imagem.save(destino, **kw)
        elif isinstance(conteudo, bytes):
            destino.write_bytes(conteudo)
        else:
            destino.write_bytes(conteudo.encode("utf-8"))
        gravados.append(Path(rel))

    especies, descartados = dados_especies(fontes)
    coordenadas, gritos = {}, {}
    for nome in ESPECIES:
        pasta = MON_DIR / nome
        b = converter_batalha(nome, fontes, retoques)
        for lado in ("front", "back"):
            gravar(pasta / f"{lado}.png", imagem=png_indexado(b[lado], 64, 64, b["normal"]), transparency=0)
        gravar(pasta / "normal.pal", jasc(b["normal"]))
        gravar(pasta / "shiny.pal", jasc(b["shiny"]))
        dados, n, pal = converter_icone(nome, fontes, retoques)
        gravar(pasta / "icon.png", imagem=png_indexado(dados, 32, 64, pal), transparency=0)
        gravar(pasta / "footprint.png", imagem=converter_pegada(nome, fontes))
        rel = CRY_DIR / f"{nome}.wav"
        gritos[nome] = converter_grito(nome, raiz / rel, fontes)
        gravados.append(rel)
        coordenadas[nome] = {
            "front": tamanho_coord(raiz / pasta / "front.png") + [y_offset(raiz / pasta / "front.png")],
            "back": tamanho_coord(raiz / pasta / "back.png") + [y_offset(raiz / pasta / "back.png")],
            "icone_paleta": n,
        }
    especies_json = {"especies": especies,
                     "_trocas": TROCAS,
                     "_descartados_ovo": descartados,
                     "_gritos": gritos}
    gravar(GEN4_JSON, _json_compacto(especies_json))
    gravar(COORD_JSON, _json_compacto(coordenadas))
    return gravados


def mesmo_arquivo(a, b):
    if a.suffix == ".png":
        ia, ib = Image.open(a), Image.open(b)
        if ia.mode != ib.mode or ia.size != ib.size or ia.tobytes() != ib.tobytes():
            return False
        return ia.mode != "P" or ia.getpalette()[:48] == ib.getpalette()[:48]
    if a.suffix in (".pal", ".json"):
        return a.read_text().replace("\r\n", "\n") == b.read_text().replace("\r\n", "\n")
    return a.read_bytes() == b.read_bytes()


def conferir():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        erros = []
        for rel in gerar(tmp):
            if not (REPO / rel).is_file():
                erros.append(f"falta {rel}")
            elif not mesmo_arquivo(REPO / rel, tmp / rel):
                erros.append(f"diverge {rel}")
        return erros


def folha(saida, raiz=REPO):
    """Folha 4x por espécie: frente, costas, frente shiny, costas shiny, ícone q1, ícone q2 e pegada."""
    k, margem = 4, 8
    fundo = (232, 232, 216)
    linhas = []
    for nome in ESPECIES:
        pasta = raiz / MON_DIR / nome
        normal, shiny = ler_jasc(pasta / "normal.pal"), ler_jasc(pasta / "shiny.pal")
        n = json.loads((raiz / COORD_JSON).read_text())[nome]["icone_paleta"]
        pal_ic = ler_jasc(raiz / ICON_PALS / f"icon_palette_{n}.pal")
        icone = recolorir(pasta / "icon.png", pal_ic)
        pegada = Image.open(pasta / "footprint.png").convert("L").point(lambda v: 0 if v else 255).convert("RGBA")
        linhas.append([recolorir(pasta / "front.png", normal), recolorir(pasta / "back.png", normal),
                       recolorir(pasta / "front.png", shiny), recolorir(pasta / "back.png", shiny),
                       icone.crop((0, 0, 32, 32)), icone.crop((0, 32, 32, 64)), pegada])
    larg = margem + sum(im.width * k + margem for im in linhas[0])
    alt = margem + len(linhas) * (64 * k + margem)
    out = Image.new("RGBA", (larg, alt), fundo + (255,))
    y = margem
    for linha in linhas:
        x = margem
        for im in linha:
            grande = im.resize((im.width * k, im.height * k), Image.NEAREST)
            out.alpha_composite(grande, (x, y + (64 * k - grande.height)))
            x += grande.width + margem
        y += 64 * k + margem
    out.convert("RGB").save(saida)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--baixar", action="store_true", help="baixa as fontes para o cache")
    grupo.add_argument("--conferir", action="store_true", help="refaz num diretório temporário e compara")
    grupo.add_argument("--folha", metavar="PNG", help="monta a folha de conferência 4x")
    args = ap.parse_args()
    if args.baixar:
        baixar()
        return 0
    if args.folha:
        folha(args.folha)
        print("folha", args.folha)
        return 0
    if args.conferir:
        erros = conferir()
        for e in erros:
            print(e, file=sys.stderr)
        print("gen4: " + ("tudo confere" if not erros else f"{len(erros)} divergência(s)"))
        return 1 if erros else 0
    gravados = gerar(REPO)
    print(f"gen4: {len(gravados)} arquivos gravados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
