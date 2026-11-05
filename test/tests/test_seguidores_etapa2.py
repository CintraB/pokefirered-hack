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
# os que leem o pacote inteiro levam minutos sobre /mnt/c: marcador slow (conftest.py), como em test_pipeline.py
pula_lento = pytest.mark.skipif(os.environ.get("ESTEIRA_SKIP_SLOW") == "1", reason="ESTEIRA_SKIP_SLOW=1")


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
    assert "->large" not in corpo  # Task 3: os grandes seguem (graphicsId OBJ_EVENT_GFX_FOLLOWER_LARGE)


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


@pytest.mark.slow
@pula_lento
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


@pytest.mark.slow
@pula_lento
@tem_veekun
def test_converter_conferir_bate():
    r = subprocess.run([sys.executable, str(CONVERSOR), "--especies", "todas", "--conferir", "--origem", str(VEEKUN)],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


# --- caminhos de erro do conversor (pacote falso com uma espécie só) ------------------------------------------------

def _origem_falsa(tmp_path, dex, alterar=None, escala=1):
    """Cópia do pacote só com a espécie `dex` (sem fêmea); `escala` amplia os quadros; `alterar(normal, shiny)` mexe
    nas imagens RGBA do quadro down/1."""
    for sub in ("", "shiny"):
        for d in DIRECOES:
            for f in ("", "frame2"):
                pasta = tmp_path / "pacote" / sub / d / f
                pasta.mkdir(parents=True, exist_ok=True)
                im = Image.open(VEEKUN / sub / d / f / f"{dex}.png").convert("RGBA")
                if escala != 1:
                    im = im.resize((im.size[0] * escala, im.size[1] * escala), Image.NEAREST)
                im.save(pasta / f"{dex}.png")
    if alterar:
        pn, ps = tmp_path / "pacote" / "down" / f"{dex}.png", tmp_path / "pacote" / "shiny" / "down" / f"{dex}.png"
        n, s = Image.open(pn).convert("RGBA"), Image.open(ps).convert("RGBA")
        alterar(n, s)
        n.save(pn)
        s.save(ps)
    return tmp_path / "pacote"


def _rodar(tmp_path, origem, dex):
    return subprocess.run(
        [sys.executable, str(CONVERSOR), "--origem", str(origem), "--especies", str(dex), "--saida", str(tmp_path / "saida")],
        capture_output=True, text=True, cwd=REPO_ROOT)


def _transparente_nos_dois(n, s):
    return next((x, y) for y in range(32) for x in range(32)
                if n.getpixel((x, y))[3] == 0 and s.getpixel((x, y))[3] == 0)


@tem_veekun
def test_falha_pixel_so_no_shiny_fora_da_lista(tmp_path):
    def alterar(n, s):
        s.putpixel(_transparente_nos_dois(n, s), (152, 152, 152, 255))
    r = _rodar(tmp_path, _origem_falsa(tmp_path, 1, alterar), 1)
    assert r.returncode != 0
    assert "transparência" in r.stderr, r.stderr


@tem_veekun
def test_falha_so_no_shiny_com_outra_cor(tmp_path):
    def alterar(n, s):  # Kingler: só (200, 200, 208) é tolerada
        s.putpixel(_transparente_nos_dois(n, s), (1, 2, 3, 255))
    r = _rodar(tmp_path, _origem_falsa(tmp_path, 99, alterar), 99)
    assert r.returncode != 0
    assert "transparência" in r.stderr, r.stderr


@tem_veekun
def test_kingler_original_converte(tmp_path):
    r = _rodar(tmp_path, _origem_falsa(tmp_path, 99), 99)
    assert r.returncode == 0, r.stderr


@tem_veekun
def test_pares_so_para_a_lista(tmp_path):
    # Weedle (13) está em PARES_NORMAL_SHINY e converte; a mesma folha com outro número (fora da lista) falha
    origem = _origem_falsa(tmp_path, 13)
    assert _rodar(tmp_path, origem, 13).returncode == 0
    for p in origem.rglob("13.png"):
        p.rename(p.with_name("10.png"))
    r = _rodar(tmp_path, origem, 10)
    assert r.returncode != 0
    assert "duas cores no shiny" in r.stderr, r.stderr


@tem_veekun
def test_falha_grande_fora_da_lista(tmp_path):
    r = _rodar(tmp_path, _origem_falsa(tmp_path, 1, escala=2), 1)
    assert r.returncode != 0
    assert "grandes" in r.stderr and "[1]" in r.stderr, r.stderr


@tem_veekun
def test_falha_femea_que_falta(tmp_path):
    # Pikachu está em FEMEAS: o pacote falso não tem a pasta female/
    r = _rodar(tmp_path, _origem_falsa(tmp_path, 25), 25)
    assert r.returncode != 0
    assert "fêmeas" in r.stderr and "faltam [25]" in r.stderr, r.stderr


@tem_veekun
def test_falha_grande_que_ficou_pequeno(tmp_path):
    # Wailord (321) reduzido para 32x32: sai da lista de grandes
    origem = _origem_falsa(tmp_path, 321)
    for p in origem.rglob("321.png"):
        Image.open(p).resize((32, 32), Image.NEAREST).save(p)
    r = _rodar(tmp_path, origem, 321)
    assert r.returncode != 0
    assert "faltam [321]" in r.stderr, r.stderr


@tem_veekun
def test_falha_femea_a_mais(tmp_path):
    # Bulbasaur (1) não está em FEMEAS: uma pasta female/ com ele faz o conversor falhar
    origem = _origem_falsa(tmp_path, 1)
    for p in list(origem.rglob("1.png")):
        rel = p.relative_to(origem)
        destino = origem / ("shiny/female" if rel.parts[0] == "shiny" else "female") / (
            Path(*rel.parts[1:]) if rel.parts[0] == "shiny" else rel)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(p.read_bytes())
    r = _rodar(tmp_path, origem, 1)
    assert r.returncode != 0
    assert "fêmeas" in r.stderr and "sobram [1]" in r.stderr, r.stderr


@tem_veekun
def test_falha_quadro_de_tamanho_errado(tmp_path):
    # Wailord (321) com quadros 48x48: nem 32 nem 64
    origem = _origem_falsa(tmp_path, 321)
    for p in origem.rglob("321.png"):
        Image.open(p).resize((48, 48), Image.NEAREST).save(p)
    r = _rodar(tmp_path, origem, 321)
    assert r.returncode != 0
    assert "48x48" in r.stderr, r.stderr


# --- conferir_listas direto, com espécies sintéticas (não precisa do pacote) -----------------------------------------

def _conversor():
    import importlib.util
    spec = importlib.util.spec_from_file_location("conversor_seguidores", CONVERSOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _especie(dex, grande=False, femea=None):
    from types import SimpleNamespace
    folha = SimpleNamespace(grande=grande)
    f = SimpleNamespace(grande=grande if femea == "igual" else not grande) if femea else None
    return SimpleNamespace(dex=dex, base=folha, femea=f, formas=None)


def _especies_certas():
    return [_especie(d, grande=d in GRANDES, femea="igual" if d in FEMEAS else None) for d in range(1, 387)]


def test_conferir_listas_aceita_as_listas_certas():
    _conversor().conferir_listas(_especies_certas(), range(1, 387))


@pytest.mark.parametrize("mexer, trecho", [
    (lambda es: es.__setitem__(0, _especie(1, grande=True)), "grandes (64x64) divergem da lista: sobram [1]"),
    (lambda es: es.__setitem__(320, _especie(321)), "grandes (64x64) divergem da lista: sobram [], faltam [321]"),
    (lambda es: es.__setitem__(0, _especie(1, femea="igual")), "fêmeas divergem da lista: sobram [1]"),
    (lambda es: es.__setitem__(24, _especie(25)), "fêmeas divergem da lista: sobram [], faltam [25]"),
    (lambda es: es.__setitem__(207, _especie(208, grande=True, femea="outra")), "#208: a fêmea e a forma padrão"),
])
def test_conferir_listas_falha_quando_diverge(mexer, trecho):
    conv = _conversor()
    especies = _especies_certas()
    mexer(especies)
    with pytest.raises(conv.ErroConversao) as e:
        conv.conferir_listas(especies, range(1, 387))
    assert trecho in str(e.value), str(e.value)


def test_conferir_listas_parcial_so_ve_as_pedidas():
    conv = _conversor()
    conv.conferir_listas([_especie(d) for d in range(10, 25)], range(10, 25))   # sem grande nem fêmea pedida
    with pytest.raises(conv.ErroConversao, match=r"faltam \[3\]"):   # Venusaur (3) pedido e sem fêmea
        conv.conferir_listas([_especie(3), _especie(4)], [3, 4])


# --- Task 3: grandes 64x64 e variantes (fêmea, letra do Unown) em tempo de execução --------------------------------

EVENT_OBJECTS_H = REPO_ROOT / "include" / "constants" / "event_objects.h"
GFX_INFO_H = REPO_ROOT / "src" / "data" / "object_events" / "object_event_graphics_info.h"
GFX_POINTERS_H = REPO_ROOT / "src" / "data" / "object_events" / "object_event_graphics_info_pointers.h"
TEST_HOOKS_H = REPO_ROOT / "include" / "test_hooks.h"
TEST_HOOKS_C = REPO_ROOT / "src" / "test_hooks.c"


def _sem_comentarios(texto):
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", texto, flags=re.S)


def _funcao(texto, nome):
    """Corpo de `nome(...)` { ... } (chaves balanceadas)."""
    m = re.search(rf"^\w[\w\s\*]*\b{nome}\s*\([^;{{]*\)\s*\{{", texto, re.M)
    assert m, f"função {nome} não encontrada"
    nivel, i = 1, m.end()
    while nivel:
        nivel += {"{": 1, "}": -1}.get(texto[i], 0)
        i += 1
    return texto[m.end():i - 1]


def _bloco_gfx(nome):
    m = re.search(rf"gObjectEventGraphicsInfo_{nome} = \{{(.*?)\n\}};", GFX_INFO_H.read_text(encoding="utf-8"), re.S)
    assert m, nome
    return campos(m.group(1))


def test_graphics_info_large_e_64x64():
    consts = EVENT_OBJECTS_H.read_text(encoding="utf-8")
    assert re.search(r"#define OBJ_EVENT_GFX_FOLLOWER\s+153\b", consts)
    assert re.search(r"#define OBJ_EVENT_GFX_FOLLOWER_LARGE\s+154\b", consts)
    assert re.search(r"#define NUM_OBJ_EVENT_GFX\s+155\b", consts)
    pequeno, grande = _bloco_gfx("Follower"), _bloco_gfx("FollowerLarge")
    assert (grande["width"], grande["height"], grande["size"]) == ("64", "64", "2048")
    assert grande["oam"] == "&gObjectEventBaseOam_64x64"
    assert grande["subspriteTables"] == "gObjectEventSpriteOamTables_64x64"
    assert grande["shadowSize"] == "SHADOW_SIZE_L"
    # o resto igual ao 32x32: mesmas animações, slot de paleta, rastros
    for campo in ("anims", "paletteSlot", "paletteTag", "tileTag", "tracks", "inanimate", "affineAnims"):
        assert grande[campo] == pequeno[campo], campo
    # imagens padrão do tamanho certo (FreeSpriteTilesIfNotUsingSheet libera images->size)
    assert grande["images"] == "FOLLOWER_DEFAULT_LARGE_IMAGES"
    m = re.search(r"#define FOLLOWER_DEFAULT_LARGE_IMAGES sFollowerPicTable_(\w+)", tabela())
    assert m and Image.open(arquivo_da_folha(f"sFollowerPicTable_{m.group(1)}")).size == (512, 64)
    ponteiros = GFX_POINTERS_H.read_text(encoding="utf-8")
    assert re.search(r"\[OBJ_EVENT_GFX_FOLLOWER_LARGE\]\s*=\s*&gObjectEventGraphicsInfo_FollowerLarge,", ponteiros)
    assert "const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_FollowerLarge;" in ponteiros


def test_follower_state_cabe_em_16():
    c = FOLLOWER_C.read_text(encoding="utf-8")
    corpo = _sem_comentarios(re.search(r"struct FollowerState\n\{(.*?)\};", c, re.S).group(1))
    tamanhos = {"u8": 1, "u16": 2, "u32": 4, "bool8": 1}
    total, bits = 0, 0
    for tipo, _nome, largura in re.findall(r"(\w+)\s+(\w+)(?::(\d+))?;", corpo):
        if largura:
            bits += int(largura)
            continue
        total += tamanhos[tipo]
    assert re.search(r"\bu8\s+variant;", corpo), corpo
    assert total + (bits + 7) // 8 <= 16
    assert "STATIC_ASSERT(sizeof(struct FollowerState) <= 16" in c


def test_todo_teste_de_seguidor_aceita_os_dois_ids():
    """Nenhum `== OBJ_EVENT_GFX_FOLLOWER` isolado: quem pergunta "é o seguidor?" passa por Follower_IsFollowerObject /
    Follower_IsFollowerGraphicsId (que aceitam os dois graphicsIds); a criação escolhe o id por `large`."""
    for caminho in list((REPO_ROOT / "src").rglob("*.c")) + list((REPO_ROOT / "include").rglob("*.h")):
        texto = _sem_comentarios(caminho.read_text(encoding="utf-8", errors="replace"))
        if caminho == FOLLOWER_C:
            texto = texto.replace(_funcao(texto, "Follower_IsFollowerGraphicsId"), "")
        # (comparar só com _LARGE é perguntar "é o 64x64?", não "é o seguidor?")
        assert not re.search(r"[!=]=\s*OBJ_EVENT_GFX_FOLLOWER\b|\bOBJ_EVENT_GFX_FOLLOWER\s*[!=]=", texto), caminho
    c = _sem_comentarios(FOLLOWER_C.read_text(encoding="utf-8"))
    ids = _funcao(c, "Follower_IsFollowerGraphicsId")
    assert "OBJ_EVENT_GFX_FOLLOWER" in ids and "OBJ_EVENT_GFX_FOLLOWER_LARGE" in ids
    assert "Follower_IsFollowerGraphicsId(objectEvent->graphicsId)" in _funcao(c, "Follower_IsFollowerObject")
    criar = _funcao(c, "CreateFollowerAt")
    assert re.search(r"->large \? OBJ_EVENT_GFX_FOLLOWER_LARGE : OBJ_EVENT_GFX_FOLLOWER", criar), criar
    ql = _sem_comentarios((REPO_ROOT / "src" / "quest_log_objects.c").read_text(encoding="utf-8"))
    assert "Follower_IsFollowerGraphicsId(questLogObjectEvents[i].graphicsId)" in _funcao(ql, "QL_LoadObjects")


def test_variante_por_genero_e_letra():
    c = _sem_comentarios(FOLLOWER_C.read_text(encoding="utf-8"))
    h = FOLLOWER_H.read_text(encoding="utf-8")
    assert "u8 Follower_GetMonVariant(struct Pokemon *mon);" in h
    assert ("const struct FollowerSpecies *Follower_GetVariantInfo(const struct FollowerSpecies *base, u8 variant);"
            in h)
    assert re.search(r"#define FOLLOWER_VARIANT_DEFAULT\s+0\b", h)
    assert re.search(r"#define FOLLOWER_VARIANT_FEMALE\s+1\b", h)
    assert re.search(r"#define FOLLOWER_VARIANT_FORM\s+2\b", h)
    variante = _funcao(c, "Follower_GetMonVariant")
    assert "GetMonGender(mon) == MON_FEMALE" in variante and "->female" in variante
    assert "GetUnownLetterByPersonality(" in variante and "->formCount" in variante
    info = _funcao(c, "Follower_GetVariantInfo")
    assert "base->female" in info and "&base->forms[" in info and "base->formCount" in info
    # recria se espécie, shiny ou variante mudou
    refresh = _funcao(c, "Follower_Refresh")
    for campo in ("sFollowerState.species", "sFollowerState.shiny", "sFollowerState.variant"):
        assert campo in refresh, campo
    # imagens, paleta (normal/shiny) e criação usam a variante
    assert "Follower_GetVariantInfo(" in _funcao(c, "GetFollowerStateInfo")
    for nome in ("Follower_OnSpriteCreated", "LoadFollowerPalette"):
        assert "GetFollowerStateInfo(" in _funcao(c, nome), nome


def test_estado_0_tem_variante_e_grande():
    c = _sem_comentarios(FOLLOWER_C.read_text(encoding="utf-8"))
    estado = _funcao(c, "Follower_TestGetState")
    assert "sFollowerState.variant << 26" in estado and "<< 31" in estado
    # 5 bits (26..30): a maior variante é 2 + 27 = 29 (o bit 31 é o `large`)
    h = FOLLOWER_H.read_text(encoding="utf-8")
    assert re.search(r"#define FOLLOWER_VARIANT_COUNT\s+\(FOLLOWER_VARIANT_FORM \+ 28\)", h)
    assert "FOLLOWER_VARIANT_COUNT <= 32" in c
    header = TEST_HOOKS_H.read_text(encoding="utf-8")
    linha = next(l for l in header.splitlines() if "TEST_CMD_FOLLOWER_STATE = 0xF0" in l)
    assert "variant << 26" in linha and "large << 31" in linha


def test_grama_alta_ignora_o_seguidor_grande():
    """O 64x64 é empurrado para trás do jogador (UpdateLargeSubpriority); a regra da grama alta que manda a grama para
    trás de quem a cruza não pode valer para ele, ou a grama do tile do jogador vai para trás do jogador (rodada 1)."""
    c = _sem_comentarios((REPO_ROOT / "src" / "field_effect_helpers.c").read_text(encoding="utf-8"))
    assert '#include "follower.h"' in c
    corpo = _funcao(c, "UpdateGrassFieldEffectSubpriority")
    laco = corpo[corpo.index("for (i = 0; i < OBJECT_EVENTS_COUNT; i++)"):]
    pula = re.search(r"if \(Follower_IsFollowerObject\(objectEvent\) && objectEvent->graphicsId == "
                     r"OBJ_EVENT_GFX_FOLLOWER_LARGE\)\s*continue;", laco)
    assert pula, laco
    # antes de qualquer conta de subprioridade com o objeto
    assert pula.start() < laco.index("linkedSprite->subpriority")
    # só o grande: o 32x32 continua na regra (como na etapa 1)
    assert "Follower_IsFollowerObject(objectEvent))" not in laco.replace(pula.group(0), "")


class _CaixaFalsa:
    """Mailbox sem emulador: `call` devolve o que a tabela manda e anota os argumentos."""

    def __init__(self, respostas):
        self.respostas, self.chamadas = respostas, []

    def call(self, cmd, arg0=0, arg1=0, **_):
        self.chamadas.append((cmd, arg0, arg1))
        return self.respostas[(cmd, arg0)] if (cmd, arg0) in self.respostas else self.respostas[cmd]


def _caixa(respostas):
    from esteira import hooks

    caixa = object.__new__(hooks.Mailbox)
    falsa = _CaixaFalsa(respostas)
    caixa.call = falsa.call
    return caixa, falsa


def test_follower_state_decodifica_variante_e_grande():
    from esteira import hooks

    raw = 1 | 208 << 8 | 1 << 24 | 1 << 26 | 1 << 31   # Steelix fêmea shiny, grande
    caixa, _ = _caixa({(hooks.CMD_FOLLOWER_STATE, 0): raw, (hooks.CMD_FOLLOWER_STATE, 1): 5 | 7 << 16,
                       (hooks.CMD_FOLLOWER_STATE, 2): 1})
    d = caixa.follower_state()
    assert (d["especie"], d["shiny"], d["escondido"], d["variante"], d["grande"]) == (208, True, False, 1, True)
    raw = 1 | 201 << 8 | 29 << 26   # Unown ?, 32x32
    caixa, _ = _caixa({(hooks.CMD_FOLLOWER_STATE, 0): raw, (hooks.CMD_FOLLOWER_STATE, 1): 0,
                       (hooks.CMD_FOLLOWER_STATE, 2): 0})
    d = caixa.follower_state()
    assert (d["especie"], d["variante"], d["grande"], d["shiny"]) == (201, 29, False, False)


def test_set_lead_look_empacota_e_decodifica():
    from esteira import hooks

    assert hooks.CMD_SET_LEAD_LOOK == hooks.CMD_START_FLY + 1
    caixa, falsa = _caixa({hooks.CMD_SET_LEAD_LOOK: 25 | 1 << 16 | 1 << 24})
    assert caixa.set_lead_look(25, 30, shiny=True, female=True) == {"especie": 25, "variante": 1, "shiny": True}
    assert falsa.chamadas == [(hooks.CMD_SET_LEAD_LOOK, 25 | 30 << 16, 1 | 2)]
    caixa, falsa = _caixa({hooks.CMD_SET_LEAD_LOOK: 201 | 29 << 16})
    assert caixa.set_lead_look(201, 5, letter=27)["variante"] == 29
    assert falsa.chamadas[0][2] == 27 << 8
    caixa, _ = _caixa({hooks.CMD_SET_LEAD_LOOK: hooks.NO_RESULT})
    with pytest.raises(AssertionError, match="SET_LEAD_LOOK"):
        caixa.set_lead_look(81, 5, female=True)   # Magnemite: sem gênero
    with pytest.raises(ValueError):
        caixa.set_lead_look(201, 5, letter=28)


def test_set_lead_look_no_c():
    header = TEST_HOOKS_H.read_text(encoding="utf-8")
    enum = header[header.index("TEST_CMD_FOLLOWER_STATE = 0xF0"):]
    enum = enum[:enum.index("};")]
    nomes = re.findall(r"^\s*(TEST_CMD_\w+)", enum, re.M)
    assert nomes[nomes.index("TEST_CMD_START_FLY") + 1] == "TEST_CMD_SET_LEAD_LOOK"
    c = _sem_comentarios(TEST_HOOKS_C.read_text(encoding="utf-8"))
    assert "case TEST_CMD_SET_LEAD_LOOK:" in c
    corpo = _funcao(c, "SetLeadLook")
    for trecho in ("GetGenderFromSpeciesAndPersonality(", "GetUnownLetterByPersonality(", "OT_ID_PLAYER_ID",
                   "Follower_GetMonVariant(", "IsMonShiny("):
        assert trecho in corpo, trecho
