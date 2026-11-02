"""Seguidores (POK-48), Task 1: sprites HGSS das 12 espécies, paletas normal/shiny e o gráfico dinâmico (sem emulador).

`tools/seguidores/converter.py` lê o pacote Veekun (fora do Git: `.superpowers/brainstorm/seguidores/todos/...`,
ou a pasta de `SEGUIDORES_VEEKUN`) e grava, por espécie, uma folha indexada 4bpp 256x32 (8 quadros 32x32: sul,
norte, oeste, leste, 2 quadros cada; o leste tem desenho próprio) com `.pal` normal e `_shiny` de mesmo mapeamento
de índices, mais a tabela C `src/data/object_events/follower_species.h`. Os testes que comparam com o Veekun pulam
(com aviso) se a pasta não existir; os estáticos sobre o que está no Git rodam sempre.
"""

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from esteira.scenarios import REPO_ROOT

CONVERSOR = REPO_ROOT / "tools" / "seguidores" / "converter.py"
PICS = REPO_ROOT / "graphics" / "object_events" / "pics" / "seguidores"
PALS = REPO_ROOT / "graphics" / "object_events" / "palettes" / "seguidores"
TABELA_H = REPO_ROOT / "src" / "data" / "object_events" / "follower_species.h"
FOLLOWER_H = REPO_ROOT / "include" / "follower.h"
EVENT_OBJECTS_H = REPO_ROOT / "include" / "constants" / "event_objects.h"
GFX_INFO_H = REPO_ROOT / "src" / "data" / "object_events" / "object_event_graphics_info.h"
GFX_POINTERS_H = REPO_ROOT / "src" / "data" / "object_events" / "object_event_graphics_info_pointers.h"
MOVEMENT_H = REPO_ROOT / "include" / "event_object_movement.h"

ESPECIES = {  # dex nacional -> nome do arquivo e da constante
    1: "bulbasaur", 2: "ivysaur", 3: "venusaur",
    4: "charmander", 5: "charmeleon", 6: "charizard",
    7: "squirtle", 8: "wartortle", 9: "blastoise",
    25: "pikachu", 26: "raichu", 172: "pichu",
}
ORDEM_DEX = sorted(ESPECIES)
DIRECOES = ["down", "up", "left", "right"]  # ordem dos quadros na folha: sul, norte, oeste, leste
COR_INDICE_0 = (115, 197, 164)

VEEKUN = Path(os.environ.get(
    "SEGUIDORES_VEEKUN",
    REPO_ROOT / ".superpowers" / "brainstorm" / "seguidores" / "todos" / "pokemon" / "overworld"))
tem_veekun = pytest.mark.skipif(not VEEKUN.is_dir(), reason=f"pacote Veekun ausente em {VEEKUN} (fora do Git)")


@pytest.fixture(scope="module")
def conv():
    spec = importlib.util.spec_from_file_location("seguidores_converter_t", CONVERSOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ler_pal(caminho):
    linhas = caminho.read_bytes().decode("ascii").split("\r\n")
    assert linhas[0] == "JASC-PAL" and linhas[1] == "0100", caminho
    n = int(linhas[2])
    cores = [tuple(int(v) for v in linhas[3 + i].split()) for i in range(n)]
    assert linhas[3 + n:] == [""], f"{caminho}: lixo depois das cores (CRLF no fim?)"
    return cores


def veekun_folha(dex, shiny):
    """Os 8 quadros do Veekun lado a lado (256x32 RGBA) na ordem da folha."""
    base = VEEKUN / "shiny" if shiny else VEEKUN
    folha = Image.new("RGBA", (256, 32))
    for i, d in enumerate(DIRECOES):
        for j, sub in enumerate(["", "frame2"]):
            quadro = Image.open(base / d / sub / f"{dex}.png").convert("RGBA")
            assert quadro.size == (32, 32)
            folha.paste(quadro, ((i * 2 + j) * 32, 0))
    return folha


def decodificar(dex_nome, pal):
    """PNG indexado + .pal -> RGBA (índice 0 transparente), como o jogo mostraria."""
    im = Image.open(PICS / f"{dex_nome}.png")
    assert im.mode == "P" and im.size == (256, 32)
    out = Image.new("RGBA", im.size)
    px = out.load()
    for y in range(32):
        for x in range(256):
            i = im.getpixel((x, y))
            px[x, y] = (0, 0, 0, 0) if i == 0 else (*pal[i], 255)
    return out


def tabela_texto():
    return TABELA_H.read_text(encoding="utf-8")


def test_12_especies():
    texto = tabela_texto()
    achadas = re.findall(r"\.species\s*=\s*SPECIES_(\w+)", texto)
    esperado = [ESPECIES[d].upper() for d in ORDEM_DEX]
    assert achadas == esperado, "a tabela tem de ter exatamente as 12 espécies, em ordem da Pokédex"
    follower_h = FOLLOWER_H.read_text(encoding="utf-8")
    assert re.search(r"#define FOLLOWER_SPECIES_COUNT\s+12\b", follower_h)
    assert "struct FollowerSpecies" in follower_h
    assert "Follower_GetSpeciesInfo" in follower_h
    # a tabela C carrega os 3 arquivos de cada espécie (folha, paleta normal e shiny), todos existentes
    for nome in ESPECIES.values():
        assert (PICS / f"{nome}.png").is_file(), nome
        assert (PALS / f"{nome}.pal").is_file(), nome
        assert (PALS / f"{nome}_shiny.pal").is_file(), nome
        assert f"pics/seguidores/{nome}.4bpp" in texto
        assert f"palettes/seguidores/{nome}.gbapal" in texto
        assert f"palettes/seguidores/{nome}_shiny.gbapal" in texto


def test_paletas_16_cores():
    for nome in ESPECIES.values():
        for sufixo in ("", "_shiny"):
            cores = ler_pal(PALS / f"{nome}{sufixo}.pal")
            assert len(cores) == 16, f"{nome}{sufixo}.pal"
            assert cores[0] == COR_INDICE_0, f"{nome}{sufixo}: índice 0 é a cor de transparência"
        # o PNG indexado carrega a paleta normal e usa o índice 0 só como transparente
        im = Image.open(PICS / f"{nome}.png")
        assert im.mode == "P" and im.size == (256, 32)
        pal_png = im.getpalette()[:48]
        normal = ler_pal(PALS / f"{nome}.pal")
        assert [tuple(pal_png[i * 3:i * 3 + 3]) for i in range(16)] == normal
        assert max(im.tobytes()) <= 15


def test_png_4bpp_de_verdade():
    """O gbagfx só aceita PNG de 4 bits para .4bpp: lê a profundidade no IHDR."""
    for nome in ESPECIES.values():
        dados = (PICS / f"{nome}.png").read_bytes()
        assert dados[:8] == b"\x89PNG\r\n\x1a\n"
        assert dados[24] == 4 and dados[25] == 3, f"{nome}: profundidade {dados[24]}, tipo de cor {dados[25]}"


@tem_veekun
def test_shiny_mesmo_mapeamento():
    for dex, nome in ESPECIES.items():
        normal = ler_pal(PALS / f"{nome}.pal")
        shiny = ler_pal(PALS / f"{nome}_shiny.pal")
        for rotulo, pal in (("normal", normal), ("shiny", shiny)):
            esperado = veekun_folha(dex, rotulo == "shiny")
            obtido = decodificar(nome, pal)
            ex, ob = esperado.load(), obtido.load()
            for y in range(32):
                for x in range(256):
                    assert (ex[x, y][3] == 0) == (ob[x, y][3] == 0), f"{nome} {rotulo}: transparência em {x},{y}"
                    if ex[x, y][3]:
                        assert ex[x, y][:3] == ob[x, y][:3], f"{nome} {rotulo}: cor em {x},{y}"


@tem_veekun
def test_conferir():
    r = subprocess.run([sys.executable, str(CONVERSOR), "--conferir", "--origem", str(VEEKUN)],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def _origem_falsa(tmp_path, dex, alterar):
    """Cópia do pacote só com a espécie `dex`; `alterar(normal, shiny)` mexe nas imagens RGBA do quadro down/1."""
    for sub in ("", "shiny"):
        for d in DIRECOES:
            for f in ("", "frame2"):
                pasta = tmp_path / sub / d / f
                pasta.mkdir(parents=True, exist_ok=True)
                origem = (VEEKUN / sub / d / f / f"{dex}.png")
                Image.open(origem).convert("RGBA").save(pasta / f"{dex}.png")
    n = Image.open(tmp_path / "down" / f"{dex}.png").convert("RGBA")
    s = Image.open(tmp_path / "shiny" / "down" / f"{dex}.png").convert("RGBA")
    alterar(n, s)
    n.save(tmp_path / "down" / f"{dex}.png")
    s.save(tmp_path / "shiny" / "down" / f"{dex}.png")


def _rodar_falso(tmp_path):
    saida = tmp_path / "saida"
    return subprocess.run(
        [sys.executable, str(CONVERSOR), "--origem", str(tmp_path), "--especies", "25", "--saida", str(saida)],
        capture_output=True, text=True, cwd=REPO_ROOT)


@tem_veekun
def test_falha_indice_com_duas_cores_no_shiny(tmp_path):
    def alterar(n, s):
        # pinta dois pixels da MESMA cor no normal com cores diferentes no shiny
        cor = n.getpixel((16, 16))
        assert cor[3] == 255
        ps = [(x, y) for y in range(32) for x in range(32) if n.getpixel((x, y)) == cor][:2]
        assert len(ps) == 2
        s.putpixel(ps[0], (1, 2, 3, 255))
        s.putpixel(ps[1], (9, 8, 7, 255))
    _origem_falsa(tmp_path, 25, alterar)
    r = _rodar_falso(tmp_path)
    assert r.returncode != 0
    assert "shiny" in (r.stdout + r.stderr).lower()


@tem_veekun
def test_falha_mais_de_15_cores(tmp_path):
    def alterar(n, s):
        for i in range(16):  # 16 cores novas e distintas no normal e no shiny
            n.putpixel((i, 0), (i * 8, 8, 8, 255))
            s.putpixel((i, 0), (i * 8, 16, 16, 255))
    _origem_falsa(tmp_path, 25, alterar)
    r = _rodar_falso(tmp_path)
    assert r.returncode != 0
    assert "15" in (r.stdout + r.stderr)


def test_um_gfx_so():
    texto = EVENT_OBJECTS_H.read_text(encoding="utf-8")
    assert re.search(r"#define NUM_OBJ_EVENT_GFX\s+154\b", texto)
    assert re.search(r"#define OBJ_EVENT_GFX_FOLLOWER\s+153\b", texto)
    ids = [(n, v) for n, v in re.findall(r"#define (OBJ_EVENT_GFX_\w+)\s+(\d+)\b", texto) if int(v) < 240]  # 240+: VAR_*
    assert max(int(v) for _, v in ids) == 153
    assert sum(1 for _, v in ids if int(v) == 153) == 1
    # ficha 32x32, no slot de paleta próprio, só um graphicsInfo novo e o ponteiro dele
    info = GFX_INFO_H.read_text(encoding="utf-8")
    bloco = re.search(r"gObjectEventGraphicsInfo_Follower = \{(.*?)\n\};", info, re.S).group(1)
    assert ".width = 32" in bloco and ".height = 32" in bloco and ".size = 512" in bloco
    assert ".paletteSlot = PALSLOT_FOLLOWER" in bloco
    assert "gObjectEventBaseOam_32x32" in bloco
    assert "[OBJ_EVENT_GFX_FOLLOWER]" in GFX_POINTERS_H.read_text(encoding="utf-8")
    assert re.search(r"#define PALSLOT_FOLLOWER\s+PALSLOT_NPC_SPECIAL_REFLECTION\b", MOVEMENT_H.read_text(encoding="utf-8"))
