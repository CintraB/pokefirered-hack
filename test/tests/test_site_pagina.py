"""Página do Professor: estrutura, textos legais, spoiler, movimento e assets do HTML gerado."""
import importlib.util
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("site_gerar", REPO / "tools/site/gerar.py")
gerar_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerar_mod)

VAZIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class No:
    def __init__(self, tag, attrs, pai):
        self.tag, self.attrs, self.pai, self.filhos, self.partes = tag, dict(attrs), pai, [], []

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def ancestrais(self):
        no = self.pai
        while no is not None:
            yield no
            no = no.pai

    def todos(self):
        for f in self.filhos:
            yield f
            yield from f.todos()

    def texto_total(self):
        """Texto na ordem do documento, como o navegador junta as tags em linha."""
        return "".join(p if isinstance(p, str) else p.texto_total() for p in self.partes)


class Arvore(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = No("#doc", {}, None)
        self.atual = self.raiz

    def handle_starttag(self, tag, attrs):
        no = No(tag, attrs, self.atual)
        self.atual.filhos.append(no)
        self.atual.partes.append(no)
        if tag not in VAZIAS:
            self.atual = no

    def handle_endtag(self, tag):
        no = self.atual
        while no is not None and no.tag != tag:
            no = no.pai
        if no is not None and no.pai is not None:
            self.atual = no.pai

    def handle_data(self, data):
        self.atual.partes.append(data)


def _normal(texto):
    return re.sub(r"\s+", " ", texto).strip()


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    saida = tmp_path_factory.mktemp("site") / "_site"
    gerar_mod.gerar(REPO, saida)
    return saida


@pytest.fixture(scope="module")
def pagina(site):
    return (site / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def arvore(pagina):
    p = Arvore()
    p.feed(pagina)
    return p.raiz


def _por_classe(arvore, tag, classe):
    return [n for n in arvore.todos() if n.tag == tag and classe in n.classes]


def test_titulo(pagina, arvore):
    titulo = "Pokémon FireRed — PT-BR (by Cintra)"
    assert f"<title>{titulo}</title>" in pagina
    h1 = [n for n in arvore.todos() if n.tag == "h1"]
    assert len(h1) == 1 and _normal(h1[0].texto_total()) == titulo


def test_um_capitulo_por_topico(arvore):
    caps = _por_classe(arvore, "section", "cap")
    assert [c.attrs["id"] for c in caps] == gerar_mod.ORDEM
    for c in caps:
        for chave in ("data-x", "data-y", "data-zoom"):
            assert re.fullmatch(r"\d+", c.attrs.get(chave, "")), (c.attrs["id"], chave)
    total = sum(len(c["cartoes"]) for c in gerar_mod.carregar_capitulos(REPO))
    assert len(_por_classe(arvore, "article", "cartao")) == total


def test_zoom_inteiro_nos_lugares():
    lugares = json.loads((REPO / "site/lugares.json").read_text(encoding="utf-8"))
    for tid, lugar in lugares.items():
        assert isinstance(lugar["zoom"], int) and 1 <= lugar["zoom"] <= 3, tid


def _bullets_readme(titulo):
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    secao = readme.split(f"## {titulo}\n", 1)[1].split("\n## ", 1)[0]
    secao = re.sub(r"<details>.*?</details>", "", secao, flags=re.S)
    itens = [i for i in re.split(r"\n- ", "\n" + secao) if i.strip()]
    texto = []
    for item in itens:
        item = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", item)
        texto.append(_normal(item.replace("**", "").replace("`", "")))
    return texto


def test_aviso_legal_e_creditos(arvore):
    rodape = [n for n in arvore.todos() if n.tag == "footer"]
    assert len(rodape) == 1
    texto = _normal(rodape[0].texto_total())
    aviso = _bullets_readme("Aviso legal")
    assert len(aviso) == 6
    for frase in aviso + _bullets_readme("Créditos"):
        assert frase in texto, frase
    for nome in ("pret", "PokeAPI", "Veekun"):
        assert nome in texto
    links = {n.attrs.get("href") for n in rodape[0].todos() if n.tag == "a"}
    assert "https://github.com/CintraB/pokefirered-hack" in links


def test_sem_audio_nem_rom(site, pagina):
    proibidas = (".gba", ".mp3", ".ogg", ".wav")
    arquivos = [p for p in site.rglob("*") if p.is_file()]
    assert not [p for p in arquivos if p.suffix.lower() in proibidas]
    for p in arquivos:
        if p.suffix in (".html", ".css", ".js"):
            conteudo = p.read_text(encoding="utf-8")
            assert "<audio" not in conteudo and "<video" not in conteudo and "new Audio" not in conteudo, p
            # Nenhum link, fonte ou url() aponta para ROM ou som (o aviso legal cita ".gba" só como texto).
            urls = re.findall(r"""(?:href|src)\s*=\s*["']([^"']+)["']|url\(([^)]+)\)""", conteudo)
            for url in (a or b for a, b in urls):
                assert not url.strip("'\" ").lower().endswith(proibidas), (p, url)
            assert not re.search(r"\.(mp3|ogg|wav)\b", conteudo), p


def test_familia_recolhida(arvore):
    familia = [c for c in gerar_mod.carregar_capitulos(REPO) if c["id"] == "familia"][0]
    ids = {c["id"] for c in familia["cartoes"]}
    assert ids
    artigos = [n for n in _por_classe(arvore, "article", "cartao") if n.attrs.get("id") in ids]
    assert {a.attrs["id"] for a in artigos} == ids
    for artigo in artigos:
        detalhes = [n for n in artigo.ancestrais() if n.tag == "details"]
        assert detalhes, artigo.attrs["id"]
        resumo = [n for n in detalhes[0].filhos if n.tag == "summary"]
        assert resumo and "spoiler" in resumo[0].texto_total().lower()
    # Fora do capítulo da Família, nenhum cartão fica recolhido.
    outros = [n for n in _por_classe(arvore, "article", "cartao") if n.attrs.get("id") not in ids]
    assert outros and not any(n.tag == "details" for a in outros for n in a.ancestrais())


def _bloco_media(css, consulta):
    inicio = css.index(consulta)
    abre = css.index("{", inicio)
    nivel, i = 0, abre
    while True:
        if css[i] == "{":
            nivel += 1
        elif css[i] == "}":
            nivel -= 1
            if nivel == 0:
                return css[abre:i + 1]
        i += 1


def _regras(css):
    """[(seletores, {propriedade: valor})] das regras sem chaves aninhadas (dentro ou fora de @media)."""
    regras = []
    for sel, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sel = re.sub(r"/\*.*?\*/", "", sel, flags=re.S).strip()
        decl = {}
        for item in corpo.split(";"):
            if ":" in item:
                k, v = item.split(":", 1)
                decl[k.strip()] = re.sub(r"\s+", " ", v.strip())
        regras.append(({x.strip() for x in sel.split(",")}, decl))
    return regras


def _sem_media(css):
    """O CSS sem os blocos @media (só as regras de base)."""
    saida, i = [], 0
    for m in re.finditer(r"@media[^{]*\{", css):
        if m.start() < i:
            continue
        saida.append(css[i:m.start()])
        i = m.end() - 1 + len(_bloco_media(css[m.start():], "@media"))  # depois do "}" que fecha o bloco
    return "".join(saida) + css[i:]


def test_reduced_motion(site):
    css = (site / "estilo.css").read_text(encoding="utf-8")
    regras = _regras(_bloco_media(css, "@media (prefers-reduced-motion: reduce)"))
    tudo = [d for sel, d in regras if {"*", "*::before", "*::after"} <= sel]
    assert tudo, "falta a regra para *, *::before e *::after"
    assert tudo[0].get("transition") == "none !important"
    assert tudo[0].get("animation") == "none !important"
    paineis = [d for sel, d in regras if {".js .cabeca", ".js .cartao"} <= sel]
    assert paineis and paineis[0].get("opacity") == "1" and paineis[0].get("transform") == "none"
    js = (site / "pagina.js").read_text(encoding="utf-8")
    assert 'matchMedia("(prefers-reduced-motion: reduce)")' in js
    assert re.search(r"if \(semMovimento\.matches\) \{ termina\(\); return; \}", js)  # sem máquina de escrever
    assert 'semMovimento.addEventListener("change"' in js
    # o comportamento de verdade é conferido no Chrome em test_site_navegador.py::test_pagina_sem_movimento


def test_valores_do_mapa(site):
    css = (site / "estilo.css").read_text(encoding="utf-8")
    base = _regras(_sem_media(css))
    raiz = [d for sel, d in base if ":root" in sel and "--blur" in d]
    assert raiz and raiz[0]["--blur"] in (".9px", "0.9px")
    kanto = [d for sel, d in base if "#kanto" in sel]
    assert kanto and re.search(r"blur\(var\(--blur\)\)", kanto[0].get("filter", ""))
    assert kanto[0].get("image-rendering") == "pixelated"
    veu = [d for sel, d in base if "#veu" in sel]
    assert veu and veu[0].get("opacity") in (".17", "0.17")


def test_conteudo_visivel_sem_js(site, pagina):
    """O texto só é escondido para a revelação depois que o pagina.js inicia (classe js posta por ele)."""
    assert 'classList.add("js")' not in pagina
    js = (site / "pagina.js").read_text(encoding="utf-8")
    assert 'raiz.classList.add("js")' in js
    css = (site / "estilo.css").read_text(encoding="utf-8")
    for sel, d in _regras(css):
        if d.get("opacity") == "0" and sel & {".cabeca", ".cartao", ".js .cabeca", ".js .cartao"}:
            assert all(s.startswith(".js ") for s in sel), sel


def test_professor_rgba(site):
    with Image.open(site / "assets/oak.png") as oak:
        assert oak.mode == "RGBA" and oak.size == (64, 64)
        alfas = np.array(oak)[:, :, 3]
    with Image.open(REPO / "graphics/trainers/front_pics/professor_oak_front_pic.png") as fonte:
        indices = np.array(fonte)
    assert ((alfas == 0) == (indices == 0)).all()
    assert set(np.unique(alfas)) == {0, 255}


def test_modernas_em_subcapitulos(arvore):
    cap = [n for n in _por_classe(arvore, "section", "cap") if n.attrs["id"] == "modernas"][0]
    subs = [n for n in cap.todos() if n.tag == "div" and "sub" in n.classes]
    assert len(subs) >= 2
    indice = [n for n in cap.todos() if n.tag == "nav" and "indice" in n.classes]
    assert indice
    alvos = {n.attrs.get("href") for n in indice[0].todos() if n.tag == "a"}
    assert alvos == {"#" + s.attrs["id"] for s in subs}
    cartoes = [n for n in cap.todos() if n.tag == "article"]
    assert all(any(a in subs for a in c.ancestrais()) for c in cartoes)
    modernas = [c for c in gerar_mod.carregar_capitulos(REPO) if c["id"] == "modernas"][0]
    assert len(cartoes) == len(modernas["cartoes"])


def test_imagens_do_jogo_com_fator_inteiro(tmp_path):
    """Com uma tela e um par antes/depois ligados, a página mostra 480×320 nítido e o comparador."""
    repo = tmp_path / "repo"
    (repo / "src/data/graphics").mkdir(parents=True)
    shutil.copytree(REPO / "src/data/novidades", repo / "src/data/novidades")
    shutil.copy(REPO / "src/data/item_icon_table.h", repo / "src/data")
    shutil.copy(REPO / "src/data/graphics/items.h", repo / "src/data/graphics")
    shutil.copy(REPO / "README.md", repo)
    shutil.copytree(REPO / "site", repo / "site")
    shutil.copytree(REPO / "docs/readme", repo / "docs/readme")
    (repo / "graphics").symlink_to(REPO / "graphics")
    caps = {c["id"]: c for c in gerar_mod.carregar_capitulos(REPO)}
    uma = caps["ritmo"]["cartoes"][0]["id"].replace("-", "/", 1)
    par = [c for c in caps["evolucoes"]["cartoes"] if c["titulo"].startswith("Haunter")][0]["id"].replace("-", "/", 1)
    textos = {uma: {"tela": "docs/readme/inicial.png"},
              par: {"tela": ["docs/readme/evo_gengar_antes.png", "docs/readme/evo_gengar_depois.png"]}}
    (repo / "site/textos.json").write_text(json.dumps(textos), encoding="utf-8")
    gerar_mod.gerar(repo, tmp_path / "saida")
    pagina = (tmp_path / "saida/index.html").read_text(encoding="utf-8")
    assert (tmp_path / "saida/telas/evo_gengar_depois.png").is_file()
    assert re.search(r'<img class="tela"[^>]*src="telas/inicial.png"[^>]*width="480" height="320"', pagina)
    assert re.search(r'<div class="ba"', pagina) and 'type="range"' in pagina
    assert pagina.count('loading="lazy"') >= 3
