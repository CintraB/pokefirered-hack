"""Seguidores, etapa 2 (POK-53), Task 2: tabela dos 386, folhas 64x64, fêmeas, letras do Unown e Deoxys Ataque.

Estáticos sobre o que está no Git (header gerado `src/data/object_events/follower_species.h`, PNGs e .pal em
`graphics/object_events/{pics,palettes}/seguidores/`). Os que comparam com o pacote Veekun (fora do Git) pulam com
aviso se ele não estiver presente.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from esteira.scenarios import REPO_ROOT

CONVERSOR = REPO_ROOT / "tools" / "seguidores" / "converter.py"
GRAPHICS = REPO_ROOT / "graphics" / "object_events"
TABELA_H = REPO_ROOT / "src" / "data" / "object_events" / "follower_species.h"
FOLLOWER_H = REPO_ROOT / "include" / "follower.h"
FOLLOWER_C = REPO_ROOT / "src" / "follower.c"
POKEDEX_H = REPO_ROOT / "include" / "constants" / "pokedex.h"
SPRITESHEET_MK = REPO_ROOT / "spritesheet_rules.mk"

GRANDES = {208, 249, 250, 321, 382, 383, 384}
FEMEAS = {3, 25, 154, 202, 208, 214}
LETRAS_UNOWN = [chr(c) for c in range(ord("a"), ord("z") + 1)] + ["exclamation", "question"]
DIRECOES = ["down", "up", "left", "right"]
# pixels opacos só no shiny (cor ausente no normal): o conversor os deixa transparentes nos dois (SO_NO_SHINY)
SO_NO_SHINY = {99: (200, 200, 208), 141: (152, 152, 152)}

VEEKUN = Path(os.environ.get(
    "SEGUIDORES_VEEKUN",
    REPO_ROOT / ".superpowers" / "brainstorm" / "seguidores" / "todos" / "pokemon" / "overworld"))
tem_veekun = pytest.mark.skipif(not VEEKUN.is_dir(), reason=f"pacote Veekun ausente em {VEEKUN} (fora do Git)")


def nomes_dex():
    texto = POKEDEX_H.read_text(encoding="utf-8")
    bloco = texto.split("NATIONAL_DEX_NONE,", 1)[1].split("};", 1)[0]
    return {i + 1: n for i, n in enumerate(re.findall(r"^\s*NATIONAL_DEX_(\w+),", bloco, re.M))}


def tabela():
    return TABELA_H.read_text(encoding="utf-8")


def campos(corpo):
    return dict(re.findall(r"\.(\w+)\s*=\s*([^,\n]+),", corpo))


def entradas_principais():
    """[(dex, {campo: valor})] da gFollowerSpecies, na ordem em que aparecem."""
    texto = tabela()
    m = re.search(r"const struct FollowerSpecies gFollowerSpecies\[FOLLOWER_SPECIES_COUNT\] = \{\n(.*?)\n\};", texto, re.S)
    assert m, "gFollowerSpecies não encontrada"
    nomes = {n: d for d, n in nomes_dex().items()}
    saida = []
    for nome, corpo in re.findall(r"\[NATIONAL_DEX_(\w+) - 1\] = \{(.*?)\n    \},", m.group(1), re.S):
        saida.append((nomes[nome], campos(corpo)))
    return saida


def struct_estatica(nome):
    m = re.search(rf"static const struct FollowerSpecies {nome} = \{{(.*?)\n\}};", tabela(), re.S)
    assert m, nome
    return campos(m.group(1))


def formas(nome):
    m = re.search(rf"static const struct FollowerSpecies {nome}\[(\d+)\] = \{{\n(.*?)\n\}};", tabela(), re.S)
    assert m, nome
    lista = [campos(c) for c in re.findall(r"    \{(.*?)\n    \},", m.group(2), re.S)]
    assert int(m.group(1)) == len(lista)
    return lista


def arquivo_da_folha(tabela_imagens):
    """sFollowerPicTable_X -> caminho do PNG pela INCBIN de sFollowerPic_X."""
    c = tabela_imagens.removeprefix("sFollowerPicTable_")
    m = re.search(rf'sFollowerPic_{c}\[\] = INCBIN_U16\("graphics/object_events/(pics/seguidores/[\w/]+)\.4bpp"\);', tabela())
    assert m, c
    return GRAPHICS / f"{m.group(1)}.png"


def arquivo_da_paleta(sym):
    m = re.search(rf'{sym}\[\] = INCBIN_U16\("graphics/object_events/(palettes/seguidores/\w+)\.gbapal"\);', tabela())
    assert m, sym
    return GRAPHICS / f"{m.group(1)}.pal"


def ler_pal(caminho):
    linhas = caminho.read_bytes().decode("ascii").split("\r\n")
    return [tuple(int(v) for v in linhas[3 + i].split()) for i in range(int(linhas[2]))]


def decodificar(png, pal):
    """PNG indexado + paleta -> bytes RGBA (índice 0 transparente com cor zerada)."""
    im = Image.open(png)
    assert im.mode == "P"
    out = bytearray()
    for i in im.tobytes():
        out += b"\0\0\0\0" if i == 0 else bytes((*pal[i], 255))
    return im.size, bytes(out)


def veekun_folha(nome_arquivo, shiny, femea=False):
    """Os 8 quadros do Veekun lado a lado, em RGBA com transparente zerado."""
    base = VEEKUN / "shiny" if shiny else VEEKUN
    if femea:
        base = base / "female"
    quadros = [Image.open(base / d / sub / f"{nome_arquivo}.png").convert("RGBA") for d in DIRECOES for sub in ("", "frame2")]
    n = quadros[0].size[0]
    folha = Image.new("RGBA", (n * 8, n))
    for i, q in enumerate(quadros):
        folha.paste(q, (i * n, 0))
    dados = bytearray(folha.tobytes())
    for p in range(0, len(dados), 4):
        if dados[p + 3] == 0:
            dados[p:p + 4] = b"\0\0\0\0"
    return folha.size, bytes(dados)


def confere_folha(entrada, origem, femea=False, rotulo="", dex=None):
    png = arquivo_da_folha(entrada["images"])
    normal = veekun_folha(origem, False, femea)
    for shiny, sym in ((False, entrada["palette"]), (True, entrada["shinyPalette"])):
        obtido = decodificar(png, ler_pal(arquivo_da_paleta(sym)))
        esperado = veekun_folha(origem, shiny, femea)
        if shiny and dex in SO_NO_SHINY:
            cor, dados = bytes((*SO_NO_SHINY[dex], 255)), bytearray(esperado[1])
            for p in range(0, len(dados), 4):
                if normal[1][p + 3] == 0 and dados[p + 3]:
                    assert dados[p:p + 4] == cor, f"{rotulo}: pixel só do shiny com outra cor"
                    dados[p:p + 4] = b"\0\0\0\0"
            esperado = (esperado[0], bytes(dados))
        assert obtido == esperado, f"{rotulo} {'shiny' if shiny else 'normal'}: folha diferente do Veekun ({origem})"


def test_tabela_tem_386_em_ordem_da_dex():
    assert re.search(r"#define FOLLOWER_SPECIES_COUNT\s+386\b", FOLLOWER_H.read_text(encoding="utf-8"))
    nomes = nomes_dex()
    ents = entradas_principais()
    assert [d for d, _ in ents] == list(range(1, 387))
    for dex, c in ents:
        assert c["species"] == f"SPECIES_{nomes[dex]}", dex
        assert arquivo_da_folha(c["images"]).is_file(), dex


def test_struct_e_busca_o1():
    h = FOLLOWER_H.read_text(encoding="utf-8")
    struct = re.search(r"struct FollowerSpecies\n\{(.*?)\};", h, re.S).group(1)
    assert re.findall(r"^\s*(?:const )?[\w ]+?\**(\w+);", struct, re.M) == [
        "species", "large", "formCount", "images", "palette", "shinyPalette", "female", "forms"]
    c = FOLLOWER_C.read_text(encoding="utf-8")
    corpo = re.search(r"const struct FollowerSpecies \*Follower_GetSpeciesInfo\(u16 species\)\n\{(.*?)\n\}", c, re.S).group(1)
    assert "SpeciesToNationalPokedexNum" in corpo
    assert "gFollowerSpecies[dex - 1]" in corpo
    assert "for (" not in corpo
    assert "->large" in corpo  # nesta etapa os grandes ainda não seguem


def test_grandes_sao_exatamente_os_7():
    for dex, c in entradas_principais():
        grande = dex in GRANDES
        assert c["large"] == ("TRUE" if grande else "FALSE"), dex
        png = arquivo_da_folha(c["images"])
        assert Image.open(png).size == ((512, 64) if grande else (256, 32)), png
        assert (png.parent.name == "grandes") == grande, png
    mk = SPRITESHEET_MK.read_text(encoding="utf-8")
    grandes = mk.index("$(OBJEVENTGFXDIR)/seguidores/grandes/%.4bpp")
    assert "-mwidth 8 -mheight 8" in mk[grandes:mk.index("\n\n", grandes)]
    assert grandes < mk.index("$(OBJEVENTGFXDIR)/seguidores/%.4bpp")
    # as folhas 64x64 usam quadros 8x8 tiles
    for m in re.finditer(r"overworld_frame\(sFollowerPic_(\w+), (\d), (\d), \d\)", tabela()):
        png = arquivo_da_folha(f"sFollowerPicTable_{m.group(1)}")
        esperado = "8" if png.parent.name == "grandes" else "4"
        assert m.group(2) == m.group(3) == esperado, m.group(0)


def test_femeas_sao_as_6():
    for dex, c in entradas_principais():
        if dex in FEMEAS:
            assert c["female"].startswith("&sFollowerFemale_"), dex
            f = struct_estatica(c["female"][1:])
            assert f["species"] == c["species"] and f["large"] == c["large"], dex
            assert f.get("female", "NULL") == "NULL" and f.get("forms", "NULL") == "NULL"
            png = arquivo_da_folha(f["images"])
            assert png.stem.endswith("_f"), png
        else:
            assert c["female"] == "NULL", dex
    steelix = struct_estatica("sFollowerFemale_Steelix")
    assert steelix["large"] == "TRUE"
    assert Image.open(arquivo_da_folha(steelix["images"])).size == (512, 64)


def test_unown_28_formas_na_ordem_do_jogo():
    ents = dict(entradas_principais())
    for dex, c in ents.items():
        if dex == 201:
            assert c["formCount"] == "28" and c["forms"] == "sFollowerForms_Unown"
        else:
            assert c["formCount"] == "0" and c["forms"] == "NULL", dex
    lista = formas("sFollowerForms_Unown")
    assert len(lista) == 28
    for letra, f in zip(LETRAS_UNOWN, lista):
        sufixo = letra.upper() if len(letra) == 1 else letra.capitalize()
        assert f["species"] == "SPECIES_UNOWN" and f["large"] == "FALSE"
        assert f["images"] == f"sFollowerPicTable_Unown{sufixo}"
        assert arquivo_da_folha(f["images"]).name == f"unown_{letra}.png"
    # a ordem tem de ser a de GetUnownLetterByPersonality: 0..25 = A..Z, 26 = !, 27 = ?
    icon = (REPO_ROOT / "src" / "pokemon_icon.c").read_text(encoding="utf-8")
    assert re.search(r"u16 GetUnownLetterByPersonality\(u32 personality\)\n\{.*?% 0x1C;", icon, re.S)


@tem_veekun
def test_unown_letras_batem_com_o_veekun():
    for letra, f in zip(LETRAS_UNOWN, formas("sFollowerForms_Unown")):
        confere_folha(f, f"201-{letra}", rotulo=f"unown {letra}")


@tem_veekun
def test_femeas_batem_com_o_veekun():
    for dex, c in entradas_principais():
        if dex in FEMEAS:
            confere_folha(struct_estatica(c["female"][1:]), str(dex), femea=True, rotulo=f"fêmea {dex}")


@tem_veekun
def test_deoxys_usa_forma_ataque():
    deoxys = dict(entradas_principais())[386]
    assert arquivo_da_folha(deoxys["images"]).name == "deoxys.png"
    confere_folha(deoxys, "386-attack", rotulo="deoxys")


@tem_veekun
def test_todas_as_folhas_batem_com_o_veekun():
    for dex, c in entradas_principais():
        if dex in (201, 386):
            continue  # Unown base = letra A (abaixo); Deoxys = Ataque (teste próprio)
        confere_folha(c, str(dex), rotulo=f"#{dex}", dex=dex)
    unown = dict(entradas_principais())[201]
    confere_folha(unown, "201-a", rotulo="unown base")


def test_paletas_e_pngs_validos():
    pasta = GRAPHICS / "pics" / "seguidores"
    pngs = sorted(pasta.rglob("*.png"))
    assert len(pngs) == 386 - 1 + 6 + 28  # Unown base reaproveita a folha da letra A
    for png in pngs:
        dados = png.read_bytes()
        assert dados[24] == 4 and dados[25] == 3, f"{png}: não é PNG indexado de 4 bits"
        assert max(Image.open(png).tobytes()) <= 15, png
    for pal in (GRAPHICS / "palettes" / "seguidores").glob("*.pal"):
        cores = ler_pal(pal)
        assert len(cores) == 16 and cores[0] == (115, 197, 164), pal


@tem_veekun
def test_converter_conferir_bate():
    r = subprocess.run([sys.executable, str(CONVERSOR), "--especies", "todas", "--conferir", "--origem", str(VEEKUN)],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
