#!/usr/bin/env python3
"""Gerador da Página do Professor: lê os cartões de novidades e monta o site estático."""
import argparse
import html
import json
import re
import shutil
import sys
import tempfile
import unicodedata
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imagens  # noqa: E402  (telas e sprites; fica ao lado, o gerador também é carregado por caminho)

ORDEM = ["sobre", "ritmo", "resumo", "dex", "shiny", "creche", "evolucoes",
         "modernas", "dia_noite", "clima", "lendarios", "pos_liga", "familia"]
CARTOES = Path("src/data/novidades/cartoes.json")
SITE = Path("site")
LARGURA_MAPA = 768  # site/assets/kanto_detalhe.png
TELA = (480, 320)  # tela do GBA (240x160) em 2x
SPRITE = 3  # sprites de espécie e item em 3x
# Cartões do capítulo "A história da Família Sombra" (atrás do aviso de spoiler): "<tópico original>/<slug do título>".
# Lista explícita, não uma busca no título: um cartão novo só entra aqui por decisão.
# "Garchomp e Darkrai" entra porque revela quem são os dois últimos chefes.
FAMILIA = ("modernas/familia-sombra", "modernas/pedagio-da-rota-23",
           "modernas/familia-sombra-o-fim", "modernas/garchomp-e-darkrai")
nome_da_tela = imagens.nome_da_tela
REPOSITORIO = "https://github.com/CintraB/pokefirered-hack"
AVISO_SPOILER = ("<summary><span class=\"aviso\">Aviso de spoiler</span> "
                 "<span>Abra para ler a história. Quem prefere descobrir jogando pode seguir rolando.</span>"
                 "</summary>")


def juntar_linhas(body: str) -> str:
    """Junta as linhas do body num parágrafo: hífen no fim cola sem espaço."""
    saida = ""
    for linha in body.split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        if not saida:
            saida = linha
        elif re.search(r"[^\W\d_]-$", saida):  # só "palavra-" cola; "algo -" mantém o espaço
            saida += linha
        else:
            saida += " " + linha
    return saida


def slug(titulo: str) -> str:
    """Slug estável do título: sem acento, minúsculas, não alfanuméricos viram hífen."""
    base = unicodedata.normalize("NFKD", titulo)
    base = "".join(ch for ch in base if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def chaves_do_topico(topico: str, cartoes: list) -> list:
    """Chave de cada cartão ("<tópico>/<slug>"); título repetido no tópico ganha -2, -3..."""
    vistos, chaves = {}, []
    for c in cartoes:
        base = slug(c["title"])
        vistos[base] = vistos.get(base, 0) + 1
        chaves.append(f"{topico}/{base}" + (f"-{vistos[base]}" if vistos[base] > 1 else ""))
    return chaves


def validar_titulos_repetidos(topicos: list, textos: dict) -> None:
    """Título repetido num tópico: a chave "-2" depende da ORDEM dos cartões e quebraria em silêncio.

    Cada cartão do grupo repetido precisa de entrada no textos.json com "ancora": um trecho do body
    (linhas juntas) que o cartão daquela chave tem de conter. Se a ordem mudar, o gerador falha.
    """
    for t in topicos:
        chaves = chaves_do_topico(t["id"], t["cards"])
        bases = [slug(c["title"]) for c in t["cards"]]
        for chave, base, c in zip(chaves, bases, t["cards"]):
            if bases.count(base) < 2:
                continue
            ancora = textos.get(chave, {}).get("ancora")
            if not ancora:
                raise ValueError(f"título repetido em '{t['id']}' ({c['title']!r}): a chave {chave} precisa de "
                                 f"entrada no textos.json com \"ancora\" (trecho do body desse cartão)")
            if ancora not in juntar_linhas(c["body"]):
                raise ValueError(f"textos.json ({chave}): a âncora {ancora!r} não está no cartão dessa chave; "
                                 f"a ordem dos cartões de título repetido mudou?")


def pasta_de_saida_segura(repo: Path, saida: Path) -> None:
    """Recusa apagar uma saída que seja site/, a raiz do repo ou esteja fora do repo (exceto _site e temporárias)."""
    repo, saida = Path(repo).resolve(), Path(saida).resolve()
    if saida == repo or saida == repo / SITE or repo / SITE in saida.parents:
        raise ValueError(f"saída recusada ({saida}): é a raiz do repositório ou a pasta site/")
    if saida == repo / "_site":
        return
    if repo in saida.parents:
        raise ValueError(f"saída recusada ({saida}): dentro do repositório só _site é aceita")
    if tempfile.gettempdir() and Path(tempfile.gettempdir()).resolve() in saida.parents:
        return
    raise ValueError(f"saída recusada ({saida}): fora do repositório e fora da pasta temporária")


def _ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _cartao(chave: str, c: dict, textos: dict, spoiler: bool) -> dict:
    extra = textos.get(chave, {})
    return {
        "id": chave.replace("/", "-"),
        "titulo": c["title"],
        "texto": juntar_linhas(c["body"]),
        "longo": extra.get("longo"),
        "tela": extra.get("tela"),
        "especie": c.get("speciesBefore") or c.get("speciesAfter"),
        "especie_depois": c.get("speciesAfter") if c.get("speciesBefore") else None,
        "sprites": [],
        "item": c.get("itemId"),
        "antes": c.get("before"),
        "depois": c.get("after"),
        "spoiler": spoiler,
    }


def carregar_capitulos(repo: Path) -> list:
    repo = Path(repo)
    dados = _ler_json(repo / CARTOES)
    lugares = _ler_json(repo / SITE / "lugares.json")
    textos = _ler_json(repo / SITE / "textos.json")
    topicos = {t["id"]: t for t in dados["topics"]}
    sem_capitulo = [tid for tid in topicos if tid not in ORDEM or tid not in lugares]
    if sem_capitulo:
        raise ValueError(f"cartoes.json: tópico sem capítulo (ORDEM do gerador ou lugares.json): {sem_capitulo}")
    # Chave do textos.json: "<tópico>/<slug do título>". Os cartões da Família Sombra
    # usam o tópico ORIGINAL ("modernas/..."), mesmo aparecendo no capítulo "familia".
    cards = {tid: list(zip(chaves_do_topico(tid, t["cards"]), t["cards"]))
             for tid, t in topicos.items()}
    por_chave = {k: (k, c) for tid in cards for k, c in cards[tid]}
    ausentes = [k for k in FAMILIA if k not in por_chave]
    if ausentes:
        raise ValueError(f"FAMILIA: cartão inexistente em cartoes.json: {ausentes}")
    cards["modernas"] = [(k, c) for k, c in cards["modernas"] if k not in FAMILIA]
    cards["familia"] = [por_chave[k] for k in FAMILIA]

    titulos = {tid: t["name"] for tid, t in topicos.items()}
    titulos["familia"] = "A história da Família Sombra"
    capitulos = []
    for tid in ORDEM:
        capitulos.append({
            "id": tid,
            "titulo": titulos[tid],
            "lugar": lugares[tid],
            "cartoes": [_cartao(k, c, textos, tid == "familia") for k, c in cards[tid]],
        })
    return capitulos


def telas_do_cartao(tela) -> list:
    """Campo `tela` do textos.json: um caminho, ou [antes, depois] para o comparador arrastável."""
    if not tela:
        return []
    return [tela] if isinstance(tela, str) else list(tela)


def ligar_imagens(repo: Path, capitulos: list) -> dict:
    """Liga a cada cartão o caminho publicado da tela (telas/<nome>.png) ou, se ele não tem tela, os sprites.

    A tela já mostra o Pokémon ou o item (nas evoluções, o antes e o depois): sprite junto seria repetição.
    Devolve o que falta gravar: {"telas": [caminhos de origem], "sprites": {src: sprite}}.
    """
    telas, sprites = [], {}
    for cap in capitulos:
        for c in cap["cartoes"]:
            origem = telas_do_cartao(c["tela"])
            telas += origem
            publicadas = [nome_da_tela(t, repo) for t in origem]
            c["tela"] = None if not publicadas else publicadas[0] if len(publicadas) == 1 else publicadas
            c["sprites"] = [] if publicadas else imagens.sprites_do_cartao(repo, c)
            sprites.update({s["src"]: s for s in c["sprites"]})
    return {"telas": telas, "sprites": sprites}


def carregar_subcapitulos(repo: Path, capitulos: list) -> dict:
    """{tópico: [(id, título, cartões)]} de subcapitulos.json; cartão não listado vai para "Mais novidades"."""
    dados = _ler_json(Path(repo) / SITE / "subcapitulos.json")
    por_id = {cap["id"]: cap for cap in capitulos}
    saida = {}
    for tid, grupos in dados.items():
        cartoes = {c["id"]: c for c in por_id[tid]["cartoes"]}
        usados, lista = set(), []
        for g in grupos:
            itens = []
            for chave in g["cartoes"]:
                cid = chave.replace("/", "-")
                if cid not in cartoes or cid in usados:
                    raise ValueError(f"subcapitulos.json: chave sem cartão ou repetida em {tid}: {chave}")
                usados.add(cid)
                itens.append(cartoes[cid])
            lista.append((g["id"], g["titulo"], itens))
        resto = [c for c in por_id[tid]["cartoes"] if c["id"] not in usados]
        if resto:
            lista.append(("mais", "Mais novidades", resto))
        saida[tid] = lista
    return saida


# ---------- README: aviso legal e créditos iguais aos do repositório ----------

def bullets_do_readme(readme: str, titulo: str) -> list:
    """Itens "- ..." da seção "## <titulo>" do README (sem blocos <details>), um por item."""
    if f"## {titulo}\n" not in readme:
        raise ValueError(f"README sem a seção '## {titulo}'")
    secao = readme.split(f"## {titulo}\n", 1)[1].split("\n## ", 1)[0]
    secao = re.sub(r"<details>.*?</details>", "", secao, flags=re.S)
    itens = []
    for linha in secao.splitlines():
        if linha.startswith("- "):
            itens.append(linha[2:].strip())
        elif linha.startswith("  ") and linha.strip() and itens:
            itens[-1] += " " + linha.strip()
    return itens


def _link(m) -> str:
    rotulo, url = m.group(1), m.group(2)
    externo = "" if url.startswith("#") else ' rel="noopener"'
    return f'<a href="{url}"{externo}>{rotulo}</a>'


def md_inline(texto: str) -> str:
    """Markdown de uma linha (negrito, código e link) para HTML."""
    t = html.escape(texto, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, t)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)


# ---------- HTML ----------

def _img(src: str, largura: int, altura: int, alt: str, classe: str, extra: str = "") -> str:
    e = html.escape
    return (f'<img class="{classe}" src="{e(src)}" width="{largura}" height="{altura}" alt="{e(alt)}" '
            f'loading="lazy" decoding="async"{extra}>')


def _midia(c: dict) -> str:
    """A tela do jogo (uma, ou o par antes/depois com o comparador); sem tela, os sprites (espécie e item, 3x)."""
    saida = ""
    telas = telas_do_cartao(c["tela"])
    sprites = c.get("sprites") or []  # [{"src", "largura", "altura"}], ligados por imagens.sprites_do_cartao
    if sprites and not telas:
        saida += ('<figure class="midia sprites">' + "".join(
            _img(s["src"], s["largura"] * SPRITE, s["altura"] * SPRITE, "", "sprite", f' style="--n:{s["largura"]}"')
            for s in sprites) + "</figure>")
    if len(telas) == 1:
        saida += f'<figure class="midia">{_img(telas[0], *TELA, "Tela do jogo: " + c["titulo"], "tela")}</figure>'
    elif len(telas) == 2:
        saida += ('<figure class="midia"><div class="ba" style="--corte:50%">'
                  + _img(telas[0], *TELA, "Antes: " + c["titulo"], "tela antes")
                  + _img(telas[1], *TELA, "Depois: " + c["titulo"], "tela depois")
                  + '<span class="linha" aria-hidden="true"></span>'
                    '<span class="rot r-antes" aria-hidden="true">ANTES</span>'
                    '<span class="rot r-depois" aria-hidden="true">DEPOIS</span>'
                    '<input type="range" min="0" max="100" value="50" '
                    'aria-label="Arraste para comparar antes e depois"></div></figure>')
    return saida


def _cartao_html(c: dict, nivel: int) -> str:
    e = html.escape
    partes = [f'<article class="cartao painel" id="{c["id"]}">', f"<h{nivel}>{e(c['titulo'])}</h{nivel}>"]
    if c["antes"] or c["depois"]:
        lados = [f'<span class="{cls}">{e(t)}</span>'
                 for cls, t in (("antes", c["antes"]), ("depois", c["depois"])) if t]
        partes.append('<p class="troca">' + '<span class="para" aria-hidden="true">→</span>'.join(lados) + "</p>")
    partes.append(f"<p>{e(c['texto'])}</p>")
    if c["longo"]:
        partes.append(f'<p class="longo">{e(c["longo"])}</p>')
    partes.append(_midia(c))
    partes.append("</article>")
    return "".join(partes)


def _capitulo_html(cap: dict, n: int, total: int, subs: list) -> str:
    e = html.escape
    lugar = cap["lugar"]
    qtd = len(cap["cartoes"])
    cabeca = [f'<header class="painel cabeca"><p class="lugar">{e(lugar["nome"])}</p>',
              f'<p class="tag">Capítulo {n} de {total} · {qtd} novidade{"s" if qtd != 1 else ""}</p>',
              f"<h2>{e(cap['titulo'])}</h2>"]
    if subs:
        cabeca.append('<nav class="indice" aria-label="Nesta parte"><ol>' + "".join(
            f'<li><a href="#{cap["id"]}-{sid}">{e(titulo)} <b>{len(itens)}</b></a></li>'
            for sid, titulo, itens in subs) + "</ol></nav>")
    cabeca.append("</header>")
    if subs:
        corpo = "".join(
            f'<div class="sub" id="{cap["id"]}-{sid}"><h3 class="subtitulo">{e(titulo)}</h3>'
            + "".join(_cartao_html(c, 4) for c in itens) + "</div>"
            for sid, titulo, itens in subs)
    else:
        corpo = "".join(_cartao_html(c, 3) for c in cap["cartoes"] if not c["spoiler"])
        recolhidos = "".join(_cartao_html(c, 3) for c in cap["cartoes"] if c["spoiler"])
        if recolhidos:
            corpo += f'<details class="spoiler">{AVISO_SPOILER}{recolhidos}</details>'
    lado = "dir" if lugar["x"] < LARGURA_MAPA // 2 else "esq"  # painel do lado oposto ao lugar: o pino fica à vista
    return (f'<section class="cap lado-{lado}" id="{cap["id"]}" {_atributos_lugar(lugar)}>'
            f'<div class="coluna">{"".join(cabeca)}{corpo}</div></section>')


def _trilha(capitulos: list) -> str:
    e = html.escape
    alvos = [("abertura", "Abertura")] + [(c["id"], c["titulo"]) for c in capitulos] + [("fim", "Créditos")]
    return ('<nav id="trilha" aria-label="Capítulos"><ol>' + "".join(
        f'<li><a href="#{i}"><span>{e(t)}</span></a></li>' for i, t in alvos) + "</ol></nav>")


def _atributos_lugar(lugar: dict) -> str:
    return (f'data-x="{lugar["x"]}" data-y="{lugar["y"]}" data-zoom="{round(lugar["zoom"])}" '
            f'data-lugar="{html.escape(lugar["nome"])}"')


def renderizar(repo: Path, capitulos: list) -> str:
    """index.html: o template com capítulos, trilha, créditos e aviso legal (estes dois vêm do README)."""
    repo = Path(repo)
    subs = carregar_subcapitulos(repo, capitulos)
    readme = (repo / "README.md").read_text(encoding="utf-8")
    abertura = _atributos_lugar(_ler_json(repo / SITE / "lugares.json")["abertura"])
    total = len(capitulos)
    trocas = {
        "{{ABERTURA}}": abertura,
        "{{TRILHA}}": _trilha(capitulos),
        "{{CAPITULOS}}": "\n".join(_capitulo_html(cap, n, total, subs.get(cap["id"], []))
                                   for n, cap in enumerate(capitulos, 1)),
        "{{TOTAL_CAPITULOS}}": str(total),
        "{{TOTAL_CARTOES}}": str(sum(len(c["cartoes"]) for c in capitulos)),
        "{{CREDITOS}}": "".join(f"<li>{md_inline(i)}</li>" for i in bullets_do_readme(readme, "Créditos")),
        "{{AVISO_LEGAL}}": "".join(f"<li>{md_inline(i)}</li>" for i in bullets_do_readme(readme, "Aviso legal")),
        "{{REPOSITORIO}}": REPOSITORIO,
    }
    pagina = (repo / SITE / "template.html").read_text(encoding="utf-8")
    for marcador, valor in trocas.items():
        pagina = pagina.replace(marcador, valor)
    sobra = re.findall(r"\{\{[A-Z_]+\}\}", pagina)
    if sobra:
        raise ValueError(f"template.html: marcadores sem valor: {sobra}")
    return pagina


def gerar(repo: Path, saida: Path) -> None:
    repo, saida = Path(repo), Path(saida)
    textos = _ler_json(repo / SITE / "textos.json")
    validas = set()
    for t in _ler_json(repo / CARTOES)["topics"]:
        validas |= set(chaves_do_topico(t["id"], t["cards"]))
    for chave in textos:
        if chave not in validas:
            raise ValueError(f"textos.json: chave sem cartão correspondente: {chave}")
    for chave, extra in textos.items():
        telas = telas_do_cartao(extra.get("tela"))
        if len(telas) > 2:
            raise ValueError(f"textos.json ({chave}): 'tela' aceita um caminho ou [antes, depois]")
        for tela in telas:
            nome_da_tela(tela, repo)  # só docs/readme e test/referencias (as telas aprovadas)
            if not (repo / tela).is_file():
                raise FileNotFoundError(f"tela não encontrada ({chave}): {repo / tela}")
    validar_titulos_repetidos(_ler_json(repo / CARTOES)["topics"], textos)
    pasta_de_saida_segura(repo, saida)
    capitulos = carregar_capitulos(repo)
    sem_longo = [c["id"] for cap in capitulos for c in cap["cartoes"] if not (c["longo"] or "").strip()]
    if sem_longo:  # o cartão cai no body (spec §3): aviso, não erro
        warnings.warn(f"{len(sem_longo)} cartões sem texto longo do Professor: {sem_longo}")
    origens = ligar_imagens(repo, capitulos)
    pagina = renderizar(repo, capitulos)
    if saida.exists():
        shutil.rmtree(saida)
    shutil.copytree(repo / SITE, saida, ignore=shutil.ignore_patterns(
        "lugares.json", "textos.json", "subcapitulos.json", "template.html"))
    for tela in origens["telas"]:
        imagens.publicar_tela(repo, tela, saida)
    for sprite in origens["sprites"].values():
        imagens.gravar_sprite(sprite, saida)
    (saida / "index.html").write_text(pagina, encoding="utf-8")


def main():
    raiz = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="_site")
    args = ap.parse_args()
    gerar(raiz, Path(args.saida))


if __name__ == "__main__":
    main()
