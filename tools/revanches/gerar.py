"""Times das revanches do Vs. Seeker por degrau de dificuldade (POK-42).

    python3 -I tools/revanches/gerar.py             # grava src/data/rematch_tiers.h (Task 2)
    python3 -I tools/revanches/gerar.py --conferir  # sai com 1 se o header commitado divergir (Task 2)
    python3 -I tools/revanches/gerar.py --amostra   # imprime a amostra (times, temas e itens) em Markdown

Lê o C como texto (sRematches, times atuais, classes, evoluções, tipos e atributos base) e junta com
regras.json e temas.json, nesta pasta. Determinístico: o sorteio usa sementes fixas por linha e degrau.
Só a biblioteca padrão é usada.
"""

import argparse
import functools
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PASTA = Path(__file__).resolve().parent

DEGRAUS = range(1, 6)
TAMANHO_TIME = 6
NIVEL_MAX = 100

# Métodos de evolução (include/constants/pokemon.h) e o nível que cada um usa aqui.
POR_NIVEL = {"EVO_LEVEL", "EVO_LEVEL_ATK_GT_DEF", "EVO_LEVEL_ATK_EQ_DEF", "EVO_LEVEL_ATK_LT_DEF",
             "EVO_LEVEL_SILCOON", "EVO_LEVEL_CASCOON", "EVO_LEVEL_NINJASK", "EVO_LEVEL_SHEDINJA"}
POR_NIVEL_EQUIVALENTE = {"EVO_ITEM", "EVO_FRIENDSHIP", "EVO_FRIENDSHIP_DAY", "EVO_FRIENDSHIP_NIGHT",
                         "EVO_BEAUTY", "EVO_LEVEL_UP_HOLD_ITEM"}
POR_ITEM_SEGURADO = "EVO_LEVEL_HOLD_ITEM"  # nível fixo EVO_HOLD_ITEM_LEVEL (Hack 3)

# Linhas da amostra para o Cintra: o 1º treinador de cada linha de sRematches.
AMOSTRA = ("TRAINER_YOUNGSTER_BEN", "TRAINER_FISHERMAN_ELLIOT", "TRAINER_HIKER_FRANKLIN",
           "TRAINER_PSYCHIC_JACLYN", "TRAINER_TWINS_ELI_ANNE", "TRAINER_BIKER_JAXON")
DEGRAUS_AMOSTRA = (1, 3, 5)
# Nomes dos tipos por extenso, só para a amostra (o jogo abrevia em 6 letras).
NOMES_TIPO = {"TYPE_NORMAL": "Normal", "TYPE_FIGHTING": "Lutador", "TYPE_FLYING": "Voador",
              "TYPE_POISON": "Venenoso", "TYPE_GROUND": "Terra", "TYPE_ROCK": "Pedra", "TYPE_BUG": "Inseto",
              "TYPE_GHOST": "Fantasma", "TYPE_STEEL": "Aço", "TYPE_FIRE": "Fogo", "TYPE_WATER": "Água",
              "TYPE_GRASS": "Planta", "TYPE_ELECTRIC": "Elétrico", "TYPE_PSYCHIC": "Psíquico", "TYPE_ICE": "Gelo",
              "TYPE_DRAGON": "Dragão", "TYPE_DARK": "Sombrio"}


def falha(msg: str) -> None:
    sys.exit(f"gerar.py: {msg}")


def _ler(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _bloco(texto: str, inicio: str, arquivo: str) -> str:
    """O trecho de `inicio` até o `};` que fecha a tabela."""
    if inicio not in texto:
        falha(f"{arquivo}: não achei {inicio!r}")
    corpo = texto[texto.index(inicio):]
    return corpo[:corpo.index("\n};")]


# ---------------------------------------------------------------- dados do C

@functools.cache
def regras() -> dict:
    return json.loads((PASTA / "regras.json").read_text(encoding="utf-8"))


@functools.cache
def temas() -> dict[str, list[str]]:
    return json.loads((PASTA / "temas.json").read_text(encoding="utf-8"))


@functools.cache
def ler_revanches() -> list[list[str]]:
    """As linhas de sRematches em ordem, só com os ids reais (sem SKIP)."""
    corpo = _bloco(_ler("src/vs_seeker.c"), "sRematches[] = {", "vs_seeker.c")
    linhas = [[t for t in re.findall(r"\bTRAINER_\w+\b", m)]
              for m in re.findall(r"\{\s*\{([^}]*)\}", corpo)]
    if not linhas or any(not linha for linha in linhas):
        falha("vs_seeker.c: sRematches vazio ou com linha sem treinador")
    return linhas


@functools.cache
def _treinadores() -> dict[str, tuple[str, str]]:
    """TRAINER_* -> (TRAINER_CLASS_*, sParty_*), de src/data/trainers.h."""
    texto = _ler("src/data/trainers.h")
    out = {}
    for m in re.finditer(r"^    \[(TRAINER_\w+)\] = \{(.*?)^    \},", texto, re.M | re.S):
        classe = re.search(r"\.trainerClass = (TRAINER_CLASS_\w+)", m.group(2))
        party = re.search(r"\.party = \w+\((sParty_\w+)\)", m.group(2))
        if classe and party:
            out[m.group(1)] = (classe.group(1), party.group(1))
    return out


@functools.cache
def _times() -> dict[str, tuple[tuple[int, str], ...]]:
    """sParty_* -> ((nível, SPECIES_*), ...), de src/data/trainer_parties.h."""
    texto = _ler("src/data/trainer_parties.h")
    out = {}
    for m in re.finditer(r"(sParty_\w+)\[\] = \{\n(.*?)\n\};", texto, re.S):
        out[m.group(1)] = tuple((int(n), s) for n, s in
                                re.findall(r"\.lvl = (\d+),\s*\.species = (SPECIES_\w+)", m.group(2)))
    return out


def classe(treinador: str) -> str:
    if treinador not in _treinadores():
        falha(f"trainers.h: {treinador} sem .trainerClass/.party")
    return _treinadores()[treinador][0]


def time_original(treinador: str) -> tuple[tuple[int, str], ...]:
    """O time atual do treinador: ((nível, SPECIES_*), ...)."""
    party = _treinadores()[treinador][1]
    time = _times().get(party)
    if not time:
        falha(f"trainer_parties.h: {party} ({treinador}) sem Pokémon")
    return time


@functools.cache
def _id_treinador() -> dict[str, int]:
    texto = _ler("include/constants/opponents.h")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (TRAINER_\w+)\s+(\d+)\b", texto, re.M)}


@functools.cache
def evolucoes() -> dict[str, tuple[tuple[str, str, str], ...]]:
    """SPECIES_* -> ((método, parâmetro, alvo), ...), de gEvolutionTable."""
    corpo = _bloco(_ler("src/data/pokemon/evolution.h"), "gEvolutionTable", "evolution.h")
    out = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\{(.*?)\}\},", corpo, re.S):
        out[m.group(1)] = tuple(re.findall(r"\{(EVO_\w+),\s*(\w+),\s*(SPECIES_\w+)\}", m.group(2) + "}"))
    return out


@functools.cache
def _nivel_item_segurado() -> int:
    m = re.search(r"^#define EVO_HOLD_ITEM_LEVEL\s+(\d+)", _ler("include/constants/pokemon.h"), re.M)
    if not m:
        falha("pokemon.h: EVO_HOLD_ITEM_LEVEL não encontrado")
    return int(m.group(1))


@functools.cache
def especies() -> dict[str, dict]:
    """SPECIES_* -> {"tipos": (TYPE_*, TYPE_*), "atk", "spatk", "total"}, de species_info.h."""
    texto = _ler("src/data/pokemon/species_info.h")
    campos = ("baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense")
    out = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\] =\s*\{\n(.*?)\n    \},", texto, re.S):
        bloco = m.group(2)
        valores = {c: re.search(rf"\.{c} = (\d+)", bloco) for c in campos}
        tipos = re.search(r"\.types = \{(TYPE_\w+), (TYPE_\w+)\}", bloco)
        if not tipos or not all(valores.values()):
            continue
        v = {c: int(x.group(1)) for c, x in valores.items()}
        out[m.group(1)] = {"tipos": (tipos.group(1), tipos.group(2)), "atk": v["baseAttack"],
                           "spatk": v["baseSpAttack"], "total": sum(v.values())}
    return out


@functools.cache
def itens_do_jogo() -> dict[str, str]:
    """ITEM_* -> nome no jogo (items.json, campo "english", que a tradução já trocou)."""
    dados = json.loads(_ler("src/data/items.json"))
    lista = dados["items"] if isinstance(dados, dict) else dados
    return {i["itemId"]: i["english"] for i in lista}


# ---------------------------------------------------------------- regras

def evoluir(especie: str, nivel: int) -> str:
    """Aplica gEvolutionTable em cadeia até onde o nível deixa."""
    equivalente = regras()["nivel_equivalente"]
    vistos = {especie}
    while True:
        entradas = evolucoes().get(especie, ())
        if not entradas:
            return especie
        alvos = {alvo for _, _, alvo in entradas}
        if len(alvos) > 1:
            ramo = regras()["ramos"].get(especie)
            if ramo is None:
                raise ValueError(f"{especie} tem mais de um alvo {sorted(alvos)}; falta em regras.json['ramos']")
            entradas = tuple(e for e in entradas if e[2] == ramo)
            if not entradas:
                raise ValueError(f"{especie}: ramo {ramo} não está em gEvolutionTable")
        prox = None
        for metodo, param, alvo in entradas:
            if metodo in POR_NIVEL:
                minimo = int(param)
            elif metodo == POR_ITEM_SEGURADO:
                minimo = _nivel_item_segurado()
            elif metodo in POR_NIVEL_EQUIVALENTE:
                minimo = equivalente
            else:
                raise ValueError(f"{especie}: método {metodo} sem regra no gerador")
            if nivel >= minimo:
                prox = alvo
                break
        if prox is None:
            return especie
        if prox in vistos:
            raise ValueError(f"{especie}: ciclo em gEvolutionTable")
        vistos.add(prox)
        especie = prox


def niveis(degrau: int, perfil: str = "vs") -> list[int]:
    """Níveis por posição (a 6ª é o ás); teto 100 em todas (ruling R2)."""
    alvo = 50 + 10 * degrau
    desvios = {"vs": (-3, -3, -2, -2, -1, 2), "elite": (-2, -2, -1, -1, 0, 2), "campeao": (-1, -1, 0, 0, 1, 3)}
    if degrau not in DEGRAUS or perfil not in desvios:
        raise ValueError(f"degrau {degrau} / perfil {perfil!r} inválido")
    return [min(alvo + d, NIVEL_MAX) for d in desvios[perfil]]


def iv(degrau: int) -> int:
    return regras()["iv"][str(degrau)]


def item(especie: str, degrau: int, posicao: int) -> str:
    """Item segurado da espécie na posição (0–5; a 5 é o ás) no degrau."""
    r = regras()["itens"]
    d = r["por_degrau"][str(degrau)]
    escolha = d["as"] if posicao == TAMANHO_TIME - 1 else d["time"][posicao % len(d["time"])]
    dados = especies()[especie]
    if escolha == "TIPO":
        return r["item_do_tipo"].get(dados["tipos"][0], r["reserva_tipo"])
    if escolha == "FISICO_OU_ESPECIAL":
        return r["fisico"] if dados["atk"] > dados["spatk"] else r["especial"]
    return escolha


def faixas(classe_: str) -> tuple[list[str], list[str], list[str]]:
    """A lista da classe em terços pela soma dos atributos base da forma final: comum, forte, mais forte."""
    lista = sorted(temas()[classe_], key=lambda e: (especies()[evoluir(e, NIVEL_MAX)]["total"], e))
    n = len(lista)
    out: tuple[list[str], list[str], list[str]] = ([], [], [])
    for i, e in enumerate(lista):
        out[i * 3 // n].append(e)
    return out


def time_vs(linha: int, degrau: int) -> list[tuple[str, int, str, int]]:
    """(espécie, nível, item, IV) das 6 posições da linha `linha` de sRematches no degrau."""
    treinadores = ler_revanches()[linha]
    primeiro, ultimo = treinadores[0], treinadores[-1]
    nivs = niveis(degrau)

    # Assinatura: espécies distintas do time mais forte, evoluídas; o ás (maior nível, o último no empate) no fim.
    original = time_original(ultimo)
    maior = max(n for n, _ in original)
    asso = evoluir([e for n, e in original if n == maior][-1], nivs[0])
    assinatura = []
    for _, e in original:
        ev = evoluir(e, nivs[0])
        if ev != asso and ev not in assinatura:
            assinatura.append(ev)
    assinatura = (assinatura + [asso])[-TAMANHO_TIME:]

    # Complemento: sorteio por degrau na faixa do degrau; se faltar, as faixas vizinhas.
    rng = random.Random(_id_treinador()[primeiro] * 10 + degrau)
    bandas = faixas(classe(primeiro))
    preferida = regras()["faixa_por_degrau"][str(degrau)]
    ordem = sorted(range(3), key=lambda f: (abs(f - preferida), -f))
    complemento: list[str] = []
    falta = TAMANHO_TIME - len(assinatura)
    for f in ordem:
        candidatos = list(bandas[f])
        rng.shuffle(candidatos)
        for c in candidatos:
            if len(complemento) == falta:
                break
            ev = evoluir(c, nivs[0])
            if ev not in assinatura and ev not in complemento:
                complemento.append(ev)
    if len(complemento) != falta:
        falha(f"{primeiro}: a lista de {classe(primeiro)} não completa o time no degrau {degrau}")

    time = []
    for pos, e in enumerate(complemento + assinatura):
        ev = evoluir(e, nivs[pos])
        time.append((ev, nivs[pos], item(ev, degrau, pos), iv(degrau)))
    if len({e for e, _, _, _ in time}) != TAMANHO_TIME:
        falha(f"{primeiro}: espécie repetida no degrau {degrau}: {time}")
    return time


# ---------------------------------------------------------------- amostra

def _sem(prefixo: str, nome: str) -> str:
    return nome[len(prefixo):] if nome.startswith(prefixo) else nome


def _nome_item(it: str) -> str:
    return itens_do_jogo().get(it, _sem("ITEM_", it))


def amostra() -> str:
    """A amostra para o Cintra aprovar: times de 6 linhas, temas por classe e itens por degrau (Markdown)."""
    linhas = ler_revanches()
    nomes = regras()["nomes_das_classes"]
    out = ["# Revanches por degrau — amostra (POK-42)", "",
           "## Times de exemplo", "",
           "Níveis do Vs. Seeker: alvo 60/70/80/90/100 com variação pequena; o ás (posição 6) um pouco acima. "
           "As posições 1 a 6 vêm na ordem do time: primeiro o complemento sorteado do tema, "
           "depois a assinatura do treinador (o time mais forte dele, evoluído) com o ás no fim.", ""]
    for primeiro in AMOSTRA:
        i = next(k for k, linha in enumerate(linhas) if linha[0] == primeiro)
        cl = classe(primeiro)
        orig = ", ".join(f"{_sem('SPECIES_', e)} {n}" for n, e in time_original(linhas[i][-1]))
        out += [f"### {_sem('TRAINER_', primeiro)} ({nomes[cl][0]}, tema {nomes[cl][1]})", "",
                f"Time mais forte hoje ({_sem('TRAINER_', linhas[i][-1])}): {orig}.", "",
                "| Degrau | Pos. | Espécie | Nível | Item | IV |", "|---|---|---|---|---|---|"]
        for d in DEGRAUS_AMOSTRA:
            for pos, (e, n, it, v) in enumerate(time_vs(i, d)):
                out.append(f"| {d if pos == 0 else ''} | {pos + 1} | {_sem('SPECIES_', e)} | {n} | "
                           f"{_nome_item(it)} | {v} |")
        out.append("")

    out += ["## Temas por classe", "",
            "Faixas de força: a lista da classe é ordenada pela soma dos atributos base da forma final e "
            "dividida em terços — comum (degraus 1–2), forte (degrau 3) e mais forte (degraus 4–5). "
            "Se a faixa não tiver espécies novas suficientes, o sorteio completa com a faixa vizinha.", "",
            "| Classe | Tema | Comum (1–2) | Forte (3) | Mais forte (4–5) |", "|---|---|---|---|---|"]
    usadas = sorted({classe(linha[0]) for linha in linhas},
                    key=lambda c: unicodedata.normalize("NFD", nomes[c][0]).encode("ascii", "ignore"))
    for cl in usadas:
        cols = [", ".join(_sem("SPECIES_", e) for e in f) for f in faixas(cl)]
        out.append(f"| {nomes[cl][0]} | {nomes[cl][1]} | " + " | ".join(cols) + " |")

    r = regras()["itens"]
    out += ["", "## Itens por degrau", "",
            "Posições 1 a 5 seguem o ciclo da coluna \"Time\"; a posição 6 é o ás. "
            "\"Item do tipo\" = item do 1º tipo da espécie (Fada e ??? levam "
            f"{_nome_item(r['reserva_tipo'])}).", "",
            "| Degrau | IV | Time (posições 1–5) | Ás (posição 6) |", "|---|---|---|---|"]
    rotulo = {"TIPO": "item do tipo",
              "FISICO_OU_ESPECIAL": f"{_nome_item(r['fisico'])} se Ataque > Atq. Esp.; "
                                    f"senão {_nome_item(r['especial'])}"}
    for d in DEGRAUS:
        pd = r["por_degrau"][str(d)]
        time = ", ".join(rotulo.get(x, _nome_item(x)) for x in pd["time"])
        out.append(f"| {d} | {iv(d)} | {time} | {rotulo.get(pd['as'], _nome_item(pd['as']))} |")
    tipos = "; ".join(f"{NOMES_TIPO[t]} → {_nome_item(it)}" for t, it in r["item_do_tipo"].items())
    out += ["", f"Item de cada tipo: {tipos}", "",
            "Obs.: no degrau 1 só 5 posições usam o rodízio, então a 6ª fruta "
            f"({_nome_item(r['por_degrau']['1']['time'][-1])}) não aparece.", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--conferir", action="store_true", help="sai com 1 se o header commitado divergir")
    ap.add_argument("--amostra", action="store_true", help="imprime a amostra em Markdown")
    args = ap.parse_args()
    if args.amostra:
        sys.stdout.write(amostra())
        return
    falha("a gravação de src/data/rematch_tiers.h entra no Task 2")


if __name__ == "__main__":
    main()
