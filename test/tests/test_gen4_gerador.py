"""POK-54 (Task 1): fontes da Gen 4 e conversão reproduzível de Gible, Gabite, Garchomp e Darkrai.

`tools/gen4/gerar.py` baixa as fontes para `.superpowers/gen4-fontes/` (fora do Git) e grava sprites, paletas, ícones,
pegadas, gritos, `gen4.json` e `coordenadas.json`. Estes testes leem o que está versionado; os que precisam das fontes
(shiny contra a fonte, escolha da paleta do ícone, `--conferir`) pulam sem o cache.
"""

import importlib.util
import json
import re
import subprocess
import sys
import wave

import pytest
from PIL import Image

from esteira.scenarios import REPO_ROOT

GERADOR = REPO_ROOT / "tools" / "gen4" / "gerar.py"
GEN4_JSON = REPO_ROOT / "tools" / "gen4" / "gen4.json"
COORD_JSON = REPO_ROOT / "tools" / "gen4" / "coordenadas.json"
MON = REPO_ROOT / "graphics" / "pokemon"
CRIES = REPO_ROOT / "sound" / "direct_sound_samples" / "cries"
MOVES_H = REPO_ROOT / "include" / "constants" / "moves.h"
FRONT_COORDS = REPO_ROOT / "src" / "data" / "pokemon_graphics" / "front_pic_coordinates.h"
CACHE = REPO_ROOT / ".superpowers" / "gen4-fontes"

NOMES = ["gible", "gabite", "garchomp", "darkrai"]
DRAGAO_TERRA = ["TYPE_DRAGON", "TYPE_GROUND"]
MONSTRO_DRAGAO = ["EGG_GROUP_MONSTER", "EGG_GROUP_DRAGON"]
SAND_VEIL = ["ABILITY_SAND_VEIL", "ABILITY_SAND_VEIL"]
ESPERADO = {
    "gible": dict(dex=443, stats=[58, 70, 45, 42, 40, 45], tipos=DRAGAO_TERRA, captura=45, exp=67,
                  evs=[0, 1, 0, 0, 0, 0], sexo="PERCENT_FEMALE(50)", ciclos=40, amizade=70, ovos=MONSTRO_DRAGAO,
                  habilidades=SAND_VEIL, cor="BODY_COLOR_BLUE", altura=7, peso=205),
    "gabite": dict(dex=444, stats=[68, 90, 65, 82, 50, 55], tipos=DRAGAO_TERRA, captura=45, exp=144,
                   evs=[0, 2, 0, 0, 0, 0], sexo="PERCENT_FEMALE(50)", ciclos=40, amizade=70, ovos=MONSTRO_DRAGAO,
                   habilidades=SAND_VEIL, cor="BODY_COLOR_BLUE", altura=14, peso=560),
    "garchomp": dict(dex=445, stats=[108, 130, 95, 102, 80, 85], tipos=DRAGAO_TERRA, captura=45, exp=218,
                     evs=[0, 3, 0, 0, 0, 0], sexo="PERCENT_FEMALE(50)", ciclos=40, amizade=70, ovos=MONSTRO_DRAGAO,
                     habilidades=SAND_VEIL, cor="BODY_COLOR_BLUE", altura=19, peso=950),
    "darkrai": dict(dex=491, stats=[70, 90, 90, 125, 135, 90], tipos=["TYPE_DARK", "TYPE_DARK"], captura=3, exp=210,
                    evs=[0, 0, 0, 1, 2, 0], sexo="MON_GENDERLESS", ciclos=120, amizade=0,
                    ovos=["EGG_GROUP_UNDISCOVERED", "EGG_GROUP_UNDISCOVERED"],
                    habilidades=["ABILITY_BAD_DREAMS", "ABILITY_BAD_DREAMS"], cor="BODY_COLOR_BLACK", altura=15,
                    peso=505),
}


def _gerador():
    spec = importlib.util.spec_from_file_location("gen4_gerar", GERADOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gen4():
    return json.loads(GEN4_JSON.read_text(encoding="utf-8"))


def _coords():
    return json.loads(COORD_JSON.read_text(encoding="utf-8"))


def _jasc(caminho):
    texto = caminho.read_text()
    v = texto.split()
    assert v[:3] == ["JASC-PAL", "0100", "16"], f"{caminho}: cabeçalho JASC de 16 cores"
    nums = list(map(int, v[3:]))
    assert len(nums) == 48, f"{caminho}: 16 cores"
    return [tuple(nums[i:i + 3]) for i in range(0, 48, 3)]


def _com_cache():
    if not (CACHE / "csv").is_dir() or not (CACHE / "batalha").is_dir():
        pytest.skip("sem o cache das fontes (python3 -I tools/gen4/gerar.py --baixar)")


def test_valores_gen4():
    especies = _gen4()["especies"]
    assert sorted(especies) == sorted(NOMES)
    for nome, campos in ESPERADO.items():
        e = especies[nome]
        for campo, valor in campos.items():
            assert e[campo] == valor, f"{nome}.{campo}: {e[campo]!r} != {valor!r}"
        assert e["crescimento"] == "GROWTH_SLOW", nome
        for chave in ("nivel", "mt", "tutor", "ovo"):
            assert isinstance(e[chave], list), f"{nome}.{chave}"
        assert e["nivel"], f"{nome}: sem golpes por nível"


@pytest.mark.parametrize("nome", NOMES)
def test_sprites_de_batalha(nome):
    pasta = MON / nome
    normal, shiny = _jasc(pasta / "normal.pal"), _jasc(pasta / "shiny.pal")
    assert len(normal) == len(shiny) == 16
    paletas = []
    for lado in ("front", "back"):
        im = Image.open(pasta / f"{lado}.png")
        assert im.size == (64, 64), f"{nome} {lado}"
        assert im.mode == "P", f"{nome} {lado}"
        usados = set(im.tobytes())
        assert max(usados) <= 15, f"{nome} {lado}: índice acima de 15"
        assert 0 in usados, f"{nome} {lado}: sem transparência"
        assert im.info.get("transparency") == 0, f"{nome} {lado}: índice 0 tem de ser o transparente"
        paletas.append(im.getpalette()[:48])
    assert paletas[0] == paletas[1], f"{nome}: frente e costas com paletas diferentes"
    assert [tuple(paletas[0][i:i + 3]) for i in range(0, 48, 3)] == normal, f"{nome}: PNG fora da normal.pal"


@pytest.mark.parametrize("nome", NOMES)
def test_shiny_mesmos_indices(nome):
    _com_cache()
    g = _gerador()
    conv = g.converter_batalha(nome, CACHE)
    pasta = MON / nome
    shiny = _jasc(pasta / "shiny.pal")
    for lado in ("front", "back"):
        no_repo = g.recolorir(pasta / f"{lado}.png", shiny)
        da_fonte = g.renderizar(conv[lado], 64, 64, conv["shiny"])
        assert no_repo.tobytes() == da_fonte.tobytes(), f"{nome} {lado}: shiny fora dos mesmos índices"
    # sem escala (Gible), o shiny recolorido é o próprio sprite shiny da fonte, pixel a pixel
    if all(s >= 1.0 for s in conv["escala"].values()):
        dex = g.ESPECIES[nome]
        fonte = g.opacos(Image.open(CACHE / "batalha" / f"shiny_{dex}.png"))
        no_repo = g.recolorir(pasta / "front.png", shiny).load()
        x0 = min(p[0] for p in fonte)
        y0 = min(p[1] for p in fonte)
        pts = [(x, y) for y in range(64) for x in range(64) if no_repo[x, y][3]]
        dx = min(p[0] for p in pts) - x0
        dy = min(p[1] for p in pts) - y0
        assert len(pts) == len(fonte)
        for (x, y), c in fonte.items():
            assert no_repo[x + dx, y + dy][:3] == c, f"{nome}: shiny difere da fonte em ({x}, {y})"


def test_coordenadas_reproduzem_existentes():
    g = _gerador()
    texto = FRONT_COORDS.read_text()
    for especie, esperado in (("salamence", 4), ("bagon", 11), ("gengar", 9), ("dusclops", 5)):
        assert g.y_offset(MON / especie / "front.png") == esperado, especie
        bloco = re.search(rf"\[SPECIES_{especie.upper()}\]\s*=\s*\{{[^}}]*\.y_offset = (\d+)", texto)
        assert int(bloco.group(1)) == esperado, especie
    coords = _coords()
    assert sorted(coords) == sorted(NOMES)
    for nome in NOMES:
        for lado in ("front", "back"):
            larg, alt, yoff = coords[nome][lado]
            assert yoff == g.y_offset(MON / nome / f"{lado}.png"), f"{nome} {lado}"
            assert larg % 8 == 0 and alt % 8 == 0 and 8 <= larg <= 64 and 8 <= alt <= 64, f"{nome} {lado}"
        assert coords[nome]["front"][2] == 63 - 59, f"{nome}: frente com a base na linha 59"
        assert coords[nome]["back"][2] == 63 - 57, f"{nome}: costas com a base na linha 57"


@pytest.mark.parametrize("nome", NOMES)
def test_icone(nome):
    g = _gerador()
    n = _coords()[nome]["icone_paleta"]
    assert n in (0, 1, 2)
    im = Image.open(MON / nome / "icon.png")
    assert im.size == (32, 64) and im.mode == "P", nome
    assert im.info.get("transparency") == 0, nome
    pal = _jasc(REPO_ROOT / "graphics" / "pokemon" / "icon_palettes" / f"icon_palette_{n}.pal")
    rgba = g.recolorir(MON / nome / "icon.png", pal)
    b = rgba.tobytes()
    cores = {tuple(b[i:i + 3]) for i in range(0, len(b), 4) if b[i + 3]}
    assert cores <= set(pal[1:]), f"{nome}: cor fora da paleta de ícone {n}"
    assert max(im.tobytes()) <= 15
    if (CACHE / "icones").is_dir():
        # a escolha é a de menor erro entre as 3 paletas (o Garchomp fica roxo na paleta errada)
        fonte = g.opacos(Image.open(CACHE / "icones" / f"{g.ESPECIES[nome]}.png"))
        erros = g.erros_paleta_icone(list(fonte.values()), g.paletas_icone())
        assert erros[n] == min(erros), f"{nome}: paleta {n} com erro {erros[n]}, mínimo {min(erros)}"


@pytest.mark.parametrize("nome", NOMES)
def test_icone_segundo_quadro_proprio(nome):
    im = Image.open(MON / nome / "icon.png")
    dados = list(im.tobytes())
    q1 = [dados[y * 32:(y + 1) * 32] for y in range(32)]
    q2 = [dados[(32 + y) * 32:(33 + y) * 32] for y in range(32)]
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            deslocado = [[q1[y - dy][x - dx] if 0 <= y - dy < 32 and 0 <= x - dx < 32 else 0 for x in range(32)]
                         for y in range(32)]
            assert deslocado != q2, f"{nome}: quadro 2 é o quadro 1 deslocado ({dx}, {dy})"


@pytest.mark.parametrize("nome", NOMES)
def test_pegada(nome):
    im = Image.open(MON / nome / "footprint.png")
    assert im.size == (16, 16)
    assert im.mode == "1", f"{nome}: pegada tem de ser 1 bit"
    assert 0 < sum(1 for v in im.convert("L").tobytes() if v) < 256, f"{nome}: pegada vazia ou cheia"


def test_gritos():
    gritos = _gen4()["_gritos"]
    assert sorted(gritos) == sorted(NOMES)
    for nome in NOMES:
        assert gritos[nome] == "real" or gritos[nome].startswith("reserva:"), nome
        with wave.open(str(CRIES / f"{nome}.wav"), "rb") as w:
            assert w.getnchannels() == 1, nome
            assert w.getsampwidth() == 1, nome
            assert w.getframerate() == 10512, nome
            assert w.getnframes() / w.getframerate() <= 1.5, nome
            assert w.getnframes() > 0, nome


def test_trocas_documentadas():
    dados = _gen4()
    existentes = set(re.findall(r"^#define (MOVE_\w+) \d+", MOVES_H.read_text(), re.M))
    novos = {"MOVE_DRAGON_RUSH", "MOVE_DARK_VOID"}
    trocas = dados["_trocas"]
    for nome in NOMES:
        for nivel, golpe in dados["especies"][nome]["nivel"]:
            assert golpe in existentes or golpe in novos, f"{nome}: {golpe} (nv {nivel}) não existe no jogo"
        for chave in ("ovo", "tutor"):
            for golpe in dados["especies"][nome][chave]:
                assert golpe in existentes, f"{nome}.{chave}: {golpe}"
    for gen4, jogo in trocas.items():
        assert "MOVE_" + gen4.upper().replace("-", "_") not in existentes, f"troca de {gen4}, que já existe"
        assert jogo in existentes or jogo in novos, f"troca {gen4} -> {jogo}"
    if not (CACHE / "csv").is_dir():
        return
    g = _gerador()
    moves = {r["identifier"]: r for r in g.ler_csv(CACHE, "moves")}
    for nome in NOMES:
        for _, ident in g.golpe_platinum_por_nivel(nome, CACHE):
            m = moves[ident]
            if int(m["generation_id"]) > 3 and "MOVE_" + ident.upper().replace("-", "_") not in existentes:
                assert ident in trocas, f"{nome}: {ident} da Platinum não existe no jogo e falta em _trocas"


def test_gerador_confere():
    _com_cache()
    r = subprocess.run([sys.executable, "-I", str(GERADOR), "--conferir"], capture_output=True, text=True,
                       cwd=REPO_ROOT, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
