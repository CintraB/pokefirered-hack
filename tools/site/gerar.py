#!/usr/bin/env python3
"""Gerador da Página do Professor: lê os cartões de novidades e monta o site estático."""
import argparse
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

ORDEM = ["sobre", "ritmo", "resumo", "dex", "shiny", "creche", "evolucoes",
         "modernas", "dia_noite", "clima", "lendarios", "pos_liga", "familia"]
CARTOES = Path("src/data/novidades/cartoes.json")
SITE = Path("site")


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
    # Chave do textos.json: "<tópico>/<slug do título>". Os cartões da Família Sombra
    # usam o tópico ORIGINAL ("modernas/..."), mesmo aparecendo no capítulo "familia".
    cards = {tid: list(zip(chaves_do_topico(tid, t["cards"]), t["cards"]))
             for tid, t in topicos.items()}
    sombra = [(k, c) for k, c in cards["modernas"] if "Família Sombra" in c["title"]]
    cards["modernas"] = [(k, c) for k, c in cards["modernas"] if "Família Sombra" not in c["title"]]
    cards["familia"] = sombra

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


def _renderizar(capitulos: list) -> str:
    e = html.escape
    partes = []
    for cap in capitulos:
        lugar = cap["lugar"]
        itens = []
        for c in cap["cartoes"]:
            corpo = f"<p>{e(c['texto'])}</p>"
            if c["longo"]:
                corpo += f"<p class=\"longo\">{e(c['longo'])}</p>"
            if c["tela"]:
                corpo += f"<img src=\"{e(c['tela'])}\" alt=\"\" loading=\"lazy\">"
            itens.append(f"<article id=\"{c['id']}\"><h3>{e(c['titulo'])}</h3>{corpo}</article>")
        partes.append(
            f"<section id=\"{cap['id']}\" data-x=\"{lugar['x']}\" data-y=\"{lugar['y']}\" "
            f"data-zoom=\"{lugar['zoom']}\"><h2>{e(cap['titulo'])}</h2>{''.join(itens)}</section>")
    return "\n".join(partes)


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
        tela = extra.get("tela")
        if tela and not (repo / tela).is_file():
            raise FileNotFoundError(f"tela não encontrada ({chave}): {repo / tela}")
    capitulos = carregar_capitulos(repo)
    if saida.exists():
        shutil.rmtree(saida)
    shutil.copytree(repo / SITE, saida, ignore=shutil.ignore_patterns(
        "lugares.json", "textos.json", "template.html"))
    for extra in textos.values():
        if extra.get("tela"):
            destino = saida / extra["tela"]
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / extra["tela"], destino)
    modelo = (repo / SITE / "template.html").read_text(encoding="utf-8")
    (saida / "index.html").write_text(
        modelo.replace("{{CAPITULOS}}", _renderizar(capitulos)), encoding="utf-8")


def main():
    raiz = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="_site")
    args = ap.parse_args()
    gerar(raiz, Path(args.saida))


if __name__ == "__main__":
    main()
