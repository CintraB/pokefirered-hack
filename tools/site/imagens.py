"""Telas e sprites dos cartões da Página do Professor.

Sprites: espécie (graphics/pokemon/<pasta>/front.png + normal.pal) e item (o par ícone/paleta que a
src/data/item_icon_table.h liga, resolvido pelo src/data/graphics/items.h). O PNG do jogo é indexado e o
índice 0 é o fundo: sai RGBA com ele transparente.
Telas: só as aprovadas, de docs/readme e de test/referencias, copiadas sem perda para telas/.
"""
import functools
import re
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
# Origem aprovada -> prefixo do nome publicado (as de test/referencias não colidem com as de docs/readme).
ORIGENS_TELA = {"docs/readme": (), "test/referencias": ("ref",)}


def nome_da_tela(tela: str, repo: Path = RAIZ) -> str:
    """Caminho publicado da tela: telas/<nome>.png. As de test/referencias levam o prefixo ref_<pasta>_.

    O caminho é resolvido de verdade (Path.resolve, que desfaz ".." e links): o que sair de docs/readme
    ou de test/referencias é recusado.
    """
    real = (Path(repo) / tela).resolve()
    for origem, prefixo in ORIGENS_TELA.items():
        try:
            resto = real.relative_to((Path(repo) / origem).resolve()).parts
        except ValueError:
            continue
        if resto:
            return "telas/" + "_".join(prefixo + resto).lower()
    raise ValueError(f"tela fora de docs/readme e test/referencias (as únicas aprovadas): {tela}")


def publicar_tela(repo: Path, tela: str, saida: Path) -> str:
    """Copia a tela sem perda, otimizada, para <saida>/telas/ e devolve o caminho publicado."""
    destino = nome_da_tela(tela, repo)
    origem = Path(repo) / tela
    if not origem.is_file():
        raise FileNotFoundError(f"tela não encontrada: {origem}")
    alvo = Path(saida) / destino
    alvo.parent.mkdir(parents=True, exist_ok=True)
    imagem = Image.open(origem)
    imagem.load()
    imagem.save(alvo, optimize=True)
    if alvo.stat().st_size > origem.stat().st_size:  # o PNG original já estava mais enxuto
        alvo.write_bytes(origem.read_bytes())
    return destino


# ---------- sprites ----------

def _paleta(caminho: Path) -> list:
    """Lê uma paleta JASC-PAL: lista de (r, g, b)."""
    linhas = caminho.read_text().split()
    if linhas[:1] != ["JASC-PAL"]:
        raise ValueError(f"{caminho}: não é JASC-PAL")
    n = int(linhas[2])
    nums = list(map(int, linhas[3:3 + 3 * n]))
    return [tuple(nums[i:i + 3]) for i in range(0, 3 * n, 3)]


def _rgba(png: Path, paleta_pal: Path) -> Image.Image:
    """PNG indexado do jogo + paleta JASC -> RGBA, com o índice 0 transparente."""
    fonte = Image.open(png)
    if fonte.mode != "P":
        raise ValueError(f"{png}: esperado PNG indexado, veio {fonte.mode}")
    cores = _paleta(paleta_pal)
    indices = np.array(fonte)
    if indices.max() >= len(cores):
        raise ValueError(f"{png}: índice fora da paleta {paleta_pal}")
    tabela = np.array([c + (255,) for c in cores], dtype=np.uint8)
    rgba = tabela[indices]
    rgba[indices == 0] = (0, 0, 0, 0)
    return Image.fromarray(rgba, "RGBA")


def pasta_especie(especie: str) -> str:
    """SPECIES_HAUNTER -> haunter. A pasta é o nome em minúsculas; vale também para NIDORAN_F, MR_MIME, PORYGON2."""
    return especie.removeprefix("SPECIES_").lower()


# As únicas espécies sem graphics/pokemon/<nome>/front.png + normal.pal: (pasta do front.png, pasta do normal.pal).
EXCECOES_DE_PASTA = {
    "SPECIES_CASTFORM": ("castform/normal", "castform/normal"),  # uma pasta por clima
    "SPECIES_UNOWN": ("unown/a", "unown"),                       # uma pasta por letra; a paleta fica na raiz
}


def sprite_especie(repo: Path, especie: str) -> Image.Image:
    base = Path(repo) / "graphics/pokemon"
    pasta_front, pasta_pal = EXCECOES_DE_PASTA.get(especie, (pasta_especie(especie),) * 2)
    front, pal = base / pasta_front / "front.png", base / pasta_pal / "normal.pal"
    if not front.is_file() or not pal.is_file():
        raise FileNotFoundError(f"{especie}: sem {front} e {pal}")
    imagem = _rgba(front, pal)
    if imagem.height > imagem.width:  # quadros empilhados: fica só o primeiro
        imagem = imagem.crop((0, 0, imagem.width, imagem.width))
    return imagem


@functools.lru_cache(maxsize=4)
def _simbolos_de_item(repo: str):
    """({ITEM: símbolo do ícone}, {ITEM: símbolo da paleta}, {símbolo: arquivo do INCBIN})."""
    tabela = (Path(repo) / "src/data/item_icon_table.h").read_text()
    pares = re.findall(r"\[(ITEM_\w+)\]\s*=\s*\{(\w+),\s*(\w+)\}", tabela)
    arquivos = dict(re.findall(r'const u32 (gItemIcon\w+)\[\]\s*=\s*INCBIN_U32\("([^"]+)"\)',
                               (Path(repo) / "src/data/graphics/items.h").read_text()))
    return {i: ic for i, ic, _ in pares}, {i: pa for i, _, pa in pares}, arquivos


def nome_do_sprite_de_item(item: str) -> str:
    return "sprites/" + item.lower() + ".png"


def sprite_item(repo: Path, item: str) -> Image.Image:
    icones, paletas, arquivos = _simbolos_de_item(str(repo))
    if item not in icones:
        raise KeyError(f"{item}: sem par ícone/paleta na item_icon_table.h")
    png = Path(repo) / re.sub(r"\.4bpp(\.lz)?$", ".png", arquivos[icones[item]])
    pal = Path(repo) / re.sub(r"\.gbapal(\.lz)?$", ".pal", arquivos[paletas[item]])
    return _rgba(png, pal)


def nome_do_sprite_de_especie(especie: str) -> str:
    return f"sprites/{pasta_especie(especie)}.png"


def sprites_do_cartao(repo: Path, cartao: dict) -> list:
    """[{src, largura, altura, imagem}] do cartão: espécie antes e depois, depois o item."""
    saida = []
    for especie in (cartao.get("especie"), cartao.get("especie_depois")):
        if especie:
            imagem = sprite_especie(repo, especie)
            saida.append({"src": nome_do_sprite_de_especie(especie), "imagem": imagem})
    if cartao.get("item"):
        saida.append({"src": nome_do_sprite_de_item(cartao["item"]), "imagem": sprite_item(repo, cartao["item"])})
    for s in saida:
        s["largura"], s["altura"] = s["imagem"].size
    return saida


def gravar_sprite(sprite: dict, saida: Path) -> None:
    alvo = Path(saida) / sprite["src"]
    alvo.parent.mkdir(parents=True, exist_ok=True)
    sprite["imagem"].save(alvo, optimize=True)
