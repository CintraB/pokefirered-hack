"""Página do Professor: telas e sprites ligados a cada cartão (POK-22, Task 4)."""
import importlib.util
import json
import os
import re
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("site_gerar", REPO / "tools/site/gerar.py")
gerar_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerar_mod)

LIMITE_PRIMEIRA_CARGA = 5 * 1024 * 1024


def _carregar_imagens():
    spec = importlib.util.spec_from_file_location("site_imagens", REPO / "tools/site/imagens.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _lista_pal(caminho):
    linhas = Path(caminho).read_text().split()
    n = int(linhas[2])
    nums = list(map(int, linhas[3:3 + 3 * n]))
    return [tuple(nums[i:i + 3]) for i in range(0, len(nums), 3)]


def _confere(indices, rgba, paleta):
    """Índice 0 -> alfa 0; os outros -> a cor da paleta, opaca."""
    assert (indices == 0).any() and (indices != 0).any()
    assert (rgba[indices == 0][:, 3] == 0).all()
    esperado = np.array([paleta[i] + (255,) for i in range(len(paleta))], dtype=np.uint8)[indices]
    assert (rgba[indices != 0] == esperado[indices != 0]).all()


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    saida = tmp_path_factory.mktemp("imagens") / "_site"
    gerar_mod.gerar(REPO, saida)
    return saida


@pytest.fixture(scope="module")
def pagina(site):
    return (site / "index.html").read_text(encoding="utf-8")


def _artigo(pagina, cartao_id):
    achado = re.search(rf'<article class="cartao painel" id="{re.escape(cartao_id)}">(.*?)</article>', pagina, re.S)
    assert achado, cartao_id
    return achado.group(1)


def _cartoes():
    caps = gerar_mod.carregar_capitulos(REPO)
    return {c["id"]: c for cap in caps for c in cap["cartoes"]}


def _telas_do_textos():
    textos = json.loads((REPO / "site/textos.json").read_text(encoding="utf-8"))
    saida = {}
    for chave, extra in textos.items():
        t = extra.get("tela") or []
        if t:
            saida[chave.replace("/", "-")] = [t] if isinstance(t, str) else list(t)
    return saida


def test_todo_cartao_tem_imagem_ou_texto(pagina):
    """Cada cartão tem o texto; e todo cartão com espécie, item ou tela em textos.json também mostra a imagem."""
    com_tela = _telas_do_textos()
    assert len(com_tela) >= 20
    for cid, c in _cartoes().items():
        corpo = _artigo(pagina, cid)
        assert c["texto"], cid
        assert re.search(r"<p>[^<]+</p>", corpo), cid  # texto real, nunca texto em imagem
        if c["especie"] or c["item"]:
            assert 'class="sprite"' in corpo, (cid, "sem sprite")
        if cid in com_tela:
            assert 'class="tela' in corpo, (cid, "sem tela")
        if not (c["especie"] or c["item"] or cid in com_tela):
            assert "<img" not in corpo, (cid, "só texto: sem figura vazia")


def test_sprite_especie(site, pagina):
    """Haunter → Gengar: dois PNG RGBA 64×64, índice 0 transparente e cores do normal.pal."""
    corpo = _artigo(pagina, "evolucoes-haunter-evolui-por-nivel")
    srcs = re.findall(r'<img class="sprite"[^>]*src="([^"]+)"', corpo)
    assert srcs == ["sprites/haunter.png", "sprites/gengar.png"]
    for nome in ("haunter", "gengar"):
        png = Image.open(site / f"sprites/{nome}.png")
        assert png.mode == "RGBA" and png.size == (64, 64)
        original = Image.open(REPO / f"graphics/pokemon/{nome}/front.png")
        paleta = _lista_pal(REPO / f"graphics/pokemon/{nome}/normal.pal")
        _confere(np.array(original), np.array(png), paleta)
    assert Image.open(site / "sprites/haunter.png").getpixel((0, 0))[3] == 0  # canto: fundo transparente


def test_sprite_item(site, pagina):
    """Repelente Máximo: ícone do Repelente com a paleta do Repelente Máximo (par da item_icon_table.h)."""
    corpo = _artigo(pagina, "modernas-repelente-automatico")
    assert 'src="sprites/item_max_repel.png"' in corpo
    png = Image.open(site / "sprites/item_max_repel.png")
    assert png.mode == "RGBA" and png.size == (24, 24)
    icone = Image.open(REPO / "graphics/items/icons/repel.png")
    paleta = _lista_pal(REPO / "graphics/items/icon_palettes/max_repel.pal")
    _confere(np.array(icone), np.array(png), paleta)
    assert png.getpixel((0, 0))[3] == 0


def test_nomes_de_pasta_das_especies():
    """Toda espécie do species.h gera sprite: pela pasta com o nome em minúsculas ou pelas exceções Castform e Unown."""
    imagens = _carregar_imagens()
    texto = (REPO / "include/constants/species.h").read_text()
    nomes = {m for m in re.findall(r"#define SPECIES_([A-Z0-9_]+)\s+\d+", texto)
             if m != "NONE" and not m.startswith("OLD_UNOWN")}
    assert len(nomes) > 380
    for n in nomes:  # pela regra do nome, ou por uma das exceções declaradas, sai um sprite RGBA
        img = imagens.sprite_especie(REPO, "SPECIES_" + n)
        assert img.mode == "RGBA" and img.width == img.height, n
    assert imagens.pasta_especie("SPECIES_NIDORAN_F") == "nidoran_f"
    assert imagens.sprite_especie(REPO, "SPECIES_CASTFORM").size == (64, 64)  # exceções de pasta
    assert imagens.sprite_especie(REPO, "SPECIES_UNOWN").size == (64, 64)
    assert imagens.pasta_especie("SPECIES_MR_MIME") == "mr_mime"
    with pytest.raises(FileNotFoundError, match="SPECIES_NAO_EXISTE"):
        imagens.sprite_especie(REPO, "SPECIES_NAO_EXISTE")


def test_item_sem_par_na_tabela_falha():
    with pytest.raises(KeyError, match="ITEM_NAO_EXISTE"):
        _carregar_imagens().sprite_item(REPO, "ITEM_NAO_EXISTE")


def test_telas_so_de_origens_aprovadas():
    """Toda tela do textos.json vem de docs/readme ou test/referencias, e existe."""
    for cid, telas in _telas_do_textos().items():
        for tela in telas:
            assert tela.startswith(("docs/readme/", "test/referencias/")), (cid, tela)
            assert (REPO / tela).is_file(), (cid, tela)


def _repo_temporario(tmp_path, textos):
    repo = tmp_path / "repo"
    (repo / "src/data/graphics").mkdir(parents=True)
    shutil.copytree(REPO / "src/data/novidades", repo / "src/data/novidades")
    shutil.copy(REPO / "src/data/item_icon_table.h", repo / "src/data")
    shutil.copy(REPO / "src/data/graphics/items.h", repo / "src/data/graphics")
    shutil.copy(REPO / "README.md", repo)
    shutil.copytree(REPO / "site", repo / "site")
    for pasta in ("graphics", "docs/readme", "test/referencias"):
        (repo / pasta).parent.mkdir(parents=True, exist_ok=True)
        os.symlink(REPO / pasta, repo / pasta)
    (repo / "site/textos.json").write_text(json.dumps(textos), encoding="utf-8")
    return repo


def test_tela_de_origem_nao_aprovada_falha(tmp_path):
    repo = _repo_temporario(tmp_path, {"ritmo/texto-instantaneo": {"tela": "graphics/pokemon/haunter/front.png"}})
    with pytest.raises(ValueError, match="docs/readme.*test/referencias"):
        gerar_mod.gerar(repo, tmp_path / "saida")


def test_telas_publicadas_com_nome_unico_e_otimizadas(site, pagina):
    """Cada tela vai para telas/<nome>.png (docs/readme e test/referencias não colidem), sem perda e sem engordar."""
    originais = [t for telas in _telas_do_textos().values() for t in telas]
    assert len(originais) >= 20 and len(set(originais)) == len(originais), "tela repetida em dois cartões"
    publicadas = {p.name: p for p in (site / "telas").glob("*.png")}
    assert len(publicadas) == len(originais)
    for tela in originais:
        nome = gerar_mod.nome_da_tela(tela).split("/")[-1]
        assert nome in publicadas, tela
        assert publicadas[nome].stat().st_size <= (REPO / tela).stat().st_size, tela
        a, b = Image.open(REPO / tela).convert("RGB"), Image.open(publicadas[nome]).convert("RGB")
        assert (np.array(a) == np.array(b)).all(), tela
        assert f'src="telas/{nome}"' in pagina


def test_ligacoes_pelo_titulo(pagina):
    """Pares que o título pede: Haunter com o comparador do Gengar, Pedágio e Família Sombra com telas da Família."""
    assert 'src="telas/evo_gengar_antes.png"' in _artigo(pagina, "evolucoes-haunter-evolui-por-nivel")
    assert 'src="telas/ref_comum_familia_pedagio.png"' in _artigo(pagina, "modernas-pedagio-da-rota-23")
    assert re.search(r'src="telas/(ref_comum_)?familia_', _artigo(pagina, "modernas-familia-sombra"))


def _primeira_carga(pagina):
    """HTML, CSS, JS, mapa, Professor e as imagens da abertura e do 1º capítulo (Pallet)."""
    primeiro = re.search(r'<section class="cap[^"]*" id="sobre".*?</section>', pagina, re.S).group(0)
    abertura = re.search(r'<section class="hero".*?</section>', pagina, re.S).group(0)
    arquivos = {"index.html", "estilo.css", "pagina.js", "assets/kanto_detalhe.png", "assets/oak.png"}
    return arquivos | set(re.findall(r'src="([^"]+)"', primeiro + abertura))


def test_peso_primeira_carga(site, pagina):
    arquivos = _primeira_carga(pagina)
    assert all((site / a).is_file() for a in arquivos), arquivos
    total = sum((site / a).stat().st_size for a in arquivos)
    assert total <= LIMITE_PRIMEIRA_CARGA, total


def test_imagens_sem_lazy_so_na_abertura(pagina):
    """Só o mapa e o Professor da abertura carregam de imediato; todas as imagens dos cartões são lazy."""
    imgs = re.findall(r"<img [^>]*>", pagina)
    sem_lazy = [i for i in imgs if 'loading="lazy"' not in i]
    assert len(sem_lazy) == 2 and any('id="kanto"' in i for i in sem_lazy) and any('class="oak"' in i for i in sem_lazy)
    do_jogo = [i for i in imgs if 'class="tela' in i or 'class="sprite"' in i]
    assert len(do_jogo) > 40 and all('loading="lazy"' in i and 'alt="' in i for i in do_jogo)


def test_sprites_em_fator_inteiro_e_com_texto_alternativo(pagina):
    sprites = re.findall(r'<img class="sprite"[^>]*>', pagina)
    assert len(sprites) > 40
    for img in sprites:
        largura, altura = map(int, re.search(r'width="(\d+)" height="(\d+)"', img).groups())
        assert largura % 3 == 0 and altura % 3 == 0, img  # 3× do tamanho original
        assert 'alt=""' in img, img  # decorativo: o texto do cartão já diz o que é
