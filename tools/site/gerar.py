#!/usr/bin/env python3
"""Gerador da Página do Professor: lê os cartões de novidades e monta o site estático."""
import argparse
import html
import json
import shutil
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
        elif saida.endswith("-"):
            saida += linha
        else:
            saida += " " + linha
    return saida


def _ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _cartao(topico: str, indice: int, c: dict, textos: dict, spoiler: bool) -> dict:
    extra = textos.get(f"{topico}/{indice}", {})
    return {
        "id": f"{topico}-{indice}",
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
    # Os índices do textos.json são os do cartoes.json (antes de tirar a Família Sombra).
    cards = {tid: list(enumerate(t["cards"])) for tid, t in topicos.items()}
    sombra = [(i, c) for i, c in cards["modernas"] if "Família Sombra" in c["title"]]
    cards["modernas"] = [(i, c) for i, c in cards["modernas"] if "Família Sombra" not in c["title"]]
    cards["familia"] = sombra

    titulos = {tid: t["name"] for tid, t in topicos.items()}
    titulos["familia"] = "A história da Família Sombra"
    capitulos = []
    for tid in ORDEM:
        origem = "modernas" if tid == "familia" else tid
        capitulos.append({
            "id": tid,
            "titulo": titulos[tid],
            "lugar": lugares[tid],
            "cartoes": [_cartao(origem, i, c, textos, tid == "familia") for i, c in cards[tid]],
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
    for chave, extra in textos.items():
        tela = extra.get("tela")
        if tela and not (repo / tela).is_file():
            raise FileNotFoundError(f"tela não encontrada ({chave}): {repo / tela}")
    capitulos = carregar_capitulos(repo)
    if saida.exists():
        shutil.rmtree(saida)
    shutil.copytree(repo / SITE, saida)
    for extra in textos.values():
        if extra.get("tela"):
            destino = saida / extra["tela"]
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / extra["tela"], destino)
    modelo = (repo / SITE / "template.html").read_text(encoding="utf-8")
    (saida / "index.html").write_text(
        modelo.replace("{{CAPITULOS}}", _renderizar(capitulos)), encoding="utf-8")
    (saida / "template.html").unlink()


def main():
    raiz = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="_site")
    args = ap.parse_args()
    gerar(raiz, Path(args.saida))


if __name__ == "__main__":
    main()
