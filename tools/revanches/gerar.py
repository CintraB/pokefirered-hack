"""Times das revanches do Vs. Seeker por degrau de dificuldade (POK-42).

    python3 -I tools/revanches/gerar.py             # grava src/data/rematch_tiers.h
    python3 -I tools/revanches/gerar.py --conferir  # sai com 1 se o header commitado divergir
    python3 -I tools/revanches/gerar.py --amostra   # imprime a amostra (times, temas e itens) em Markdown
    python3 -I tools/revanches/gerar.py --amostra-liga  # imprime os times da Elite 4 e do Campeão em Markdown

Lê o C como texto (sRematches, times atuais, classes, evoluções, tipos e atributos base) e junta com
regras.json e temas.json, nesta pasta. Determinístico: o sorteio usa sementes fixas por linha e degrau.
A Elite 4 e o Campeão vêm de liga.json (times à mão) e vão para sLeagueTierParties, no mesmo header; os golpes
são conferidos contra os learnsets (golpe_aprendivel / problemas_liga).
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
from typing import NoReturn

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
           "TRAINER_PSYCHIC_JACLYN", "TRAINER_TWINS_ELI_ANNE", "TRAINER_BIKER_JAXON",
           "TRAINER_COOLTRAINER_LEROY")
DEGRAUS_AMOSTRA = (1, 3, 5)
# Nomes dos tipos por extenso, só para a amostra (o jogo abrevia em 6 letras).
NOMES_TIPO = {"TYPE_NORMAL": "Normal", "TYPE_FIGHTING": "Lutador", "TYPE_FLYING": "Voador",
              "TYPE_POISON": "Venenoso", "TYPE_GROUND": "Terra", "TYPE_ROCK": "Pedra", "TYPE_BUG": "Inseto",
              "TYPE_GHOST": "Fantasma", "TYPE_STEEL": "Aço", "TYPE_FIRE": "Fogo", "TYPE_WATER": "Água",
              "TYPE_GRASS": "Planta", "TYPE_ELECTRIC": "Elétrico", "TYPE_PSYCHIC": "Psíquico", "TYPE_ICE": "Gelo",
              "TYPE_DRAGON": "Dragão", "TYPE_DARK": "Sombrio"}


def falha(msg: str) -> NoReturn:
    sys.exit(f"gerar.py: {msg}")


def _ler(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _bloco(texto: str, inicio: str, arquivo: str) -> str:
    """O trecho de `inicio` até o `};` que fecha a tabela."""
    if inicio not in texto:
        falha(f"{arquivo}: não achei {inicio!r}")
    corpo = texto[texto.index(inicio):]
    if "\n};" not in corpo:
        falha(f"{arquivo}: {inicio!r} sem o '}};' que fecha a tabela")
    return corpo[:corpo.index("\n};")]


# ---------------------------------------------------------------- dados do C

@functools.cache
def regras() -> dict:
    return json.loads((PASTA / "regras.json").read_text(encoding="utf-8"))


@functools.cache
def _temas_json() -> dict:
    return json.loads((PASTA / "temas.json").read_text(encoding="utf-8"))


@functools.cache
def temas() -> dict[str, list[str]]:
    """TRAINER_CLASS_* -> lista de espécies. Um valor texto é apelido: usa a lista de outra classe (um nível só)."""
    bruto = {c: v for c, v in _temas_json().items() if not c.startswith("_")}
    out = {}
    for c, v in bruto.items():
        if isinstance(v, str):
            alvo = bruto.get(v)
            if not isinstance(alvo, list):
                falha(f"temas.json: {c} aponta para {v}, que não é uma lista")
            v = alvo
        out[c] = v
    return out


def nomes_das_classes() -> dict[str, list[str]]:
    """TRAINER_CLASS_* -> [nome no jogo, rótulo do tema], só para a amostra (temas.json, chave "_nomes")."""
    nomes = _temas_json().get("_nomes")
    if not isinstance(nomes, dict):
        falha('temas.json: falta a chave "_nomes"')
    return nomes


def nome_da_classe(classe_: str) -> tuple[str, str]:
    """(nome no jogo, rótulo do tema) da classe, de temas.json["_nomes"]."""
    nome = nomes_das_classes().get(classe_)
    if not nome or len(nome) != 2:
        falha(f'temas.json: {classe_} sem [nome, tema] em "_nomes"')
    return nome[0], nome[1]


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
    if treinador not in _treinadores():
        falha(f"trainers.h: {treinador} sem .trainerClass/.party")
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
            falha(f"species_info.h: {m.group(1)} sem .types ou atributo base")
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


def item(especie: str, degrau: int, posicao: int, deslocamento: int) -> str:
    """Item segurado da espécie na posição (0–5; a 5 é o ás) no degrau.

    `deslocamento` (o id do 1º treinador da linha) gira o ciclo do time nos degraus com "deslocar_por_linha",
    para que todas as frutas do rodízio apareçam entre os treinadores. É obrigatório: sem ele o rodízio se
    perderia calado (quem monta o time é `time_vs`, que passa o id)."""
    r = regras()["itens"]
    d = r["por_degrau"][str(degrau)]
    giro = deslocamento if d.get("deslocar_por_linha") else 0
    escolha = d["as"] if posicao == TAMANHO_TIME - 1 else d["time"][(posicao + giro) % len(d["time"])]
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

    # Assinatura: espécies distintas do time mais forte, evoluídas, no máximo regras["assinatura_max"]:
    # o ás (maior nível, o último no empate) no fim e, antes dele, as outras mais fortes (maior nível;
    # empate pela ordem original), na ordem original.
    original = time_original(ultimo)
    maior = max(n for n, _ in original)
    asso = evoluir([e for n, e in original if n == maior][-1], nivs[0])
    outras: dict[str, tuple[int, int]] = {}  # espécie evoluída -> (maior nível original, 1ª posição)
    for k, (n, e) in enumerate(original):
        ev = evoluir(e, nivs[0])
        if ev != asso:
            nivel_ant, pos_ant = outras.get(ev, (0, k))
            outras[ev] = (max(n, nivel_ant), pos_ant)
    vagas = regras()["assinatura_max"] - 1
    escolhidas = sorted(outras, key=lambda ev: (-outras[ev][0], outras[ev][1]))[:vagas]
    assinatura = sorted(escolhidas, key=lambda ev: outras[ev][1]) + [asso]

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
        time.append((ev, nivs[pos], item(ev, degrau, pos, _id_treinador()[primeiro]), iv(degrau)))
    if len({e for e, _, _, _ in time}) != TAMANHO_TIME:
        falha(f"{primeiro}: espécie repetida no degrau {degrau}: {time}")
    return time


# ---------------------------------------------------------------- Liga (Elite 4 e Campeão, times à mão)

MEMBROS_LIGA = ("LORELEI", "BRUNO", "AGATHA", "LANCE")
VARIANTES_CAMPEAO = ("SQUIRTLE", "BULBASAUR", "CHARMANDER")  # a inicial do rival, como nos _2
TAMANHO_BASE_CAMPEAO = 4
# O id de revanche de cada um (ordem de sLeagueTierParties = ids 735–741); o do Campeão gira as frutas da base.
ID_LIGA = {**{m: f"TRAINER_ELITE_FOUR_{m}_2" for m in MEMBROS_LIGA}, "CAMPEAO": "TRAINER_CHAMPION_REMATCH_SQUIRTLE"}
IV_LIGA = 255  # IV 31 na escala 0–255 de TrainerMonItemCustomMoves (fixedIV = iv * 31 / 255)


def item_fruta_liga(membro: str, degrau: int, posicao: int) -> str:
    """Nos degraus 1–2, a fruta de quem não é o ás: a mesma regra do Vs. Seeker (regras.json), com o ciclo
    girado pelo id de revanche do membro (o do Campeão vale para a base e o parceiro das 3 variantes)."""
    if degrau not in (1, 2) or not 0 <= posicao < TAMANHO_TIME - 1:
        raise ValueError(f"fruta da Liga só nos degraus 1–2 e posições 0–4 (degrau {degrau}, posição {posicao})")
    # A espécie só importa nas escolhas TIPO/FISICO_OU_ESPECIAL, que os degraus 1–2 não usam (conferido abaixo).
    escolha = item("SPECIES_BULBASAUR", degrau, posicao, _id_treinador()[ID_LIGA[membro]])
    if not escolha.endswith("_BERRY"):
        falha(f"regras.json: o degrau {degrau} não é só de frutas ({escolha})")
    return escolha


@functools.cache
def liga() -> dict:
    """tools/revanches/liga.json: os times à mão da Elite 4 e do Campeão por degrau."""
    return json.loads((PASTA / "liga.json").read_text(encoding="utf-8"))


def time_liga(membro: str, degrau: int, variante: str | None = None) -> list[tuple[str, int, str, list[str]]]:
    """(espécie, nível, item, golpes) das 6 posições do membro (ou do Campeão na variante) no degrau.

    O Campeão é a base (4) + as 2 vagas da variante; o nível vem de niveis() com o perfil do membro."""
    if membro == "CAMPEAO":
        bloco = liga()["CAMPEAO"][str(degrau)]
        mons = bloco["base"] + bloco[variante]
        perfil = "campeao"
    else:
        mons = liga()[membro][str(degrau)]
        perfil = "elite"
    if len(mons) != TAMANHO_TIME:
        falha(f"liga.json: {membro} {variante or ''} degrau {degrau} com {len(mons)} Pokémon")
    return [(m["species"], n, m["item"], list(m["moves"])) for m, n in zip(mons, niveis(degrau, perfil))]


def times_liga():
    """Todos os times da Liga: ((rótulo, membro, degrau, variante), time) em ordem fixa."""
    for membro in MEMBROS_LIGA:
        for d in DEGRAUS:
            yield (membro, membro, d, None), time_liga(membro, d)
    for v in VARIANTES_CAMPEAO:
        for d in DEGRAUS:
            yield (f"CAMPEAO_{v}", "CAMPEAO", d, v), time_liga("CAMPEAO", d, v)


@functools.cache
def golpes_do_jogo() -> dict[str, int]:
    """MOVE_* -> id dos golpes de include/constants/moves.h (de MOVE_NONE ao último).

    Só os #define com prefixo MOVE_ e valor decimal: o total e o marcador de golpe indisponível (em hexadecimal)
    ficam de fora pelo próprio padrão."""
    texto = _ler("include/constants/moves.h")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define (MOVE_\w+)\s+(\d+)\b", texto, re.M)}


@functools.cache
def _golpes_por_nivel() -> dict[str, tuple[tuple[int, str], ...]]:
    """SPECIES_* -> ((nível, MOVE_*), ...), de level_up_learnsets.h + level_up_learnset_pointers.h."""
    texto = _ler("src/data/pokemon/level_up_learnsets.h")
    tabelas = {}
    for m in re.finditer(r"static const u16 (s\w+LevelUpLearnset)\[\] = \{(.*?)\};", texto, re.S):
        tabelas[m.group(1)] = tuple((int(n), g) for n, g in
                                    re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", m.group(2)))
    ponteiros = _ler("src/data/pokemon/level_up_learnset_pointers.h")
    out = {}
    for esp, nome in re.findall(r"\[(SPECIES_\w+)\] = (s\w+LevelUpLearnset)", ponteiros):
        if nome not in tabelas:
            falha(f"level_up_learnset_pointers.h: {esp} aponta para {nome}, que não existe")
        out[esp] = tabelas[nome]
    return out


@functools.cache
def _golpes_mt() -> dict[str, frozenset[str]]:
    """SPECIES_* -> golpes de MT/MO, de tmhm_learnsets.h; a ordem das máquinas é sTMHMMoves (party_menu.h)."""
    ordem = re.findall(r"MOVE_\w+", _bloco(_ler("src/data/party_menu.h"), "sTMHMMoves[] =", "party_menu.h"))
    texto = _ler("src/data/pokemon/tmhm_learnsets.h")
    out = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*TMHM_LEARNSET\((.*?)\),\n", texto, re.S):
        golpes = set()
        for tipo, num in re.findall(r"TMHM\((TM|HM)(\d+)_\w+\)", m.group(2)):
            golpes.add(ordem[int(num) - 1 + (50 if tipo == "HM" else 0)])
        out[m.group(1)] = frozenset(golpes)
    return out


@functools.cache
def _golpes_ovo() -> dict[str, frozenset[str]]:
    """SPECIES_* (a forma que choca) -> golpes de ovo, de egg_moves.h."""
    texto = _ler("src/data/pokemon/egg_moves.h")
    return {"SPECIES_" + m.group(1): frozenset(re.findall(r"MOVE_\w+", m.group(2)))
            for m in re.finditer(r"egg_moves\((\w+),(.*?)\)", texto, re.S)}


@functools.cache
def _golpes_tutor() -> dict[str, frozenset[str]]:
    """SPECIES_* -> golpes de tutor: sTutorLearnsets (tutor_learnsets.h) e os golpes finais das iniciais
    (CanLearnTutorMove/GetTutorMove em src/party_menu.c)."""
    texto = _ler("src/data/pokemon/tutor_learnsets.h")
    out: dict[str, set[str]] = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\] = (.*?),\n", _bloco(texto, "sTutorLearnsets[] =", "tutor_learnsets.h"),
                         re.S):
        out[m.group(1)] = set(re.findall(r"TUTOR\((MOVE_\w+)\)", m.group(2)))
    pm = _ler("src/party_menu.c")
    golpe = dict(re.findall(r"case (TUTOR_MOVE_\w+):\s*return (MOVE_\w+);", pm))
    for tutor, esp in re.findall(r"case (TUTOR_MOVE_\w+):\s*if \(species == (SPECIES_\w+)\)", pm):
        if tutor not in golpe:
            falha(f"party_menu.c: {tutor} sem golpe em GetTutorMove")
        out.setdefault(esp, set()).add(golpe[tutor])
    return {e: frozenset(g) for e, g in out.items()}


@functools.cache
def _pre_evolucao() -> dict[str, str]:
    """SPECIES_* -> a espécie da qual ela evolui (gEvolutionTable invertida)."""
    out = {}
    for origem, entradas in evolucoes().items():
        for _, _, alvo in entradas:
            out.setdefault(alvo, origem)
    return out


def linhagem(especie: str) -> list[str]:
    """A espécie e as pré-evoluções dela, da própria até a forma que choca."""
    cadeia = [especie]
    while cadeia[-1] in _pre_evolucao() and _pre_evolucao()[cadeia[-1]] not in cadeia:
        cadeia.append(_pre_evolucao()[cadeia[-1]])
    return cadeia


def golpe_aprendivel(especie: str, golpe: str, nivel: int) -> bool:
    """Se a espécie (ou uma pré-evolução dela) aprende o golpe por nível ≤ `nivel`, MT/MO, ovo ou tutor."""
    for e in linhagem(especie):
        if any(n <= nivel and g == golpe for n, g in _golpes_por_nivel().get(e, ())):
            return True
        if golpe in _golpes_mt().get(e, ()) or golpe in _golpes_tutor().get(e, ()) or golpe in _golpes_ovo().get(e, ()):
            return True
    return False


def problemas_liga() -> list[str]:
    """Tudo o que está fora da regra nos times da Liga (golpes, itens, espécies); vazio = limpo."""
    out = []
    for (rotulo, _, d, _), time in times_liga():
        for pos, (esp, nivel, it, golpes) in enumerate(time, 1):
            onde = f"{rotulo} degrau {d} pos. {pos} ({_sem('SPECIES_', esp)} nv {nivel})"
            if esp not in especies():
                out.append(f"{onde}: espécie desconhecida")
                continue
            if it not in itens_do_jogo():
                out.append(f"{onde}: item {it} não existe")
            if it == "ITEM_NONE":
                out.append(f"{onde}: sem item")
            elif d <= 2 and pos < TAMANHO_TIME and it != item_fruta_liga("CAMPEAO" if rotulo.startswith("CAMPEAO")
                                                                         else rotulo, d, pos - 1):
                out.append(f"{onde}: nos degraus 1–2 leva a fruta do Vs. Seeker, não {it}")
            if len(golpes) != 4 or len(set(golpes)) != 4 or "MOVE_NONE" in golpes:
                out.append(f"{onde}: precisa de 4 golpes distintos sem MOVE_NONE: {golpes}")
            for g in golpes:
                if g not in golpes_do_jogo():
                    out.append(f"{onde}: {g} não existe")
                elif not golpe_aprendivel(esp, g, nivel):
                    out.append(f"{onde}: não aprende {g}")
    return out


# ---------------------------------------------------------------- amostra

def _sem(prefixo: str, nome: str) -> str:
    return nome[len(prefixo):] if nome.startswith(prefixo) else nome


def _nome_item(it: str) -> str:
    return itens_do_jogo().get(it, _sem("ITEM_", it))


def amostra() -> str:
    """A amostra para o Cintra aprovar: times de 6 linhas, temas por classe e itens por degrau (Markdown)."""
    linhas = ler_revanches()
    out = ["# Revanches por degrau — amostra (POK-42)", "",
           "## Times de exemplo", "",
           "Níveis do Vs. Seeker: alvo 60/70/80/90/100 com variação pequena; o ás (posição 6) um pouco acima. "
           "As posições 1 a 6 vêm na ordem do time: primeiro o complemento sorteado do tema, "
           "depois a assinatura do treinador (até 3 espécies do time mais forte dele, evoluídas: "
           "o ás e as 2 de maior nível) com o ás no fim.", ""]
    for primeiro in AMOSTRA:
        i = next(k for k, linha in enumerate(linhas) if linha[0] == primeiro)
        cl = classe(primeiro)
        orig = ", ".join(f"{_sem('SPECIES_', e)} {n}" for n, e in time_original(linhas[i][-1]))
        nome, tema = nome_da_classe(cl)
        out += [f"### {_sem('TRAINER_', primeiro)} ({nome}, tema {tema})", "",
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
                    key=lambda c: unicodedata.normalize("NFD", nome_da_classe(c)[0]).encode("ascii", "ignore"))
    for cl in usadas:
        cols = [", ".join(_sem("SPECIES_", e) for e in f) for f in faixas(cl)]
        nome, tema = nome_da_classe(cl)
        out.append(f"| {nome} | {tema} | " + " | ".join(cols) + " |")

    r = regras()["itens"]
    out += ["", "## Itens por degrau", "",
            "Posições 1 a 5 seguem o ciclo da coluna \"Time\"; a posição 6 é o ás. "
            "No degrau 1 o rodízio começa num ponto diferente para cada treinador, então as 6 frutas aparecem. "
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
    out += ["", f"Item de cada tipo: {tipos}", ""]
    return "\n".join(out)


@functools.cache
def _nomes_golpes() -> dict[str, str]:
    """MOVE_* -> nome no jogo (src/data/text/move_names.h, já em PT-BR)."""
    return dict(re.findall(r"\[(MOVE_\w+)\]\s*=\s*_\(\"(.*?)\"\)", _ler("src/data/text/move_names.h")))


@functools.cache
def _nomes_especies() -> dict[str, str]:
    """SPECIES_* -> nome no jogo, só com a inicial maiúscula (src/data/text/species_names.h)."""
    return {e: n.title() for e, n in re.findall(r"\[(SPECIES_\w+)\]\s*=\s*_\(\"(.*?)\"\)",
                                                 _ler("src/data/text/species_names.h"))}


NOMES_MEMBROS = {"LORELEI": "Lorelei (Gelo/Água)", "BRUNO": "Bruno (Lutador/Pedra/Terra)",
                 "AGATHA": "Agatha (Fantasma/Veneno)", "LANCE": "Lance (Dragão/Voador)"}


def _linha_mon(pos: int, esp: str, nivel: int, it: str, golpes: list[str]) -> str:
    nome_it = "—" if it == "ITEM_NONE" else _nome_item(it)
    gs = ", ".join(_nomes_golpes().get(g, _sem("MOVE_", g)) for g in golpes)
    return f"| {pos} | {_nomes_especies().get(esp, _sem('SPECIES_', esp))} | {nivel} | {nome_it} | {gs} |"


def amostra_liga() -> str:
    """A tabela dos times à mão da Liga por degrau, para o Cintra aprovar (Markdown)."""
    cab = ["| Pos. | Espécie | Nível | Item | Golpes |", "|---|---|---|---|---|"]
    out = ["# Elite 4 e Campeão por degrau (POK-42, Task 3)", "",
           "- **Nível:** alvo L = 50 + 10 × degrau (60/70/80/90/100). Elite 4: L−2, L−2, L−1, L−1, L e o ás "
           "(posição 6) L+2; Campeão: L−1, L−1, L, L, L+1 e o ás L+3; teto 100 em todas. IV 31 em todos.",
           "- **Espécies melhores por degrau:** a assinatura de cada um fica (Lapras, Cloyster e Jynx; Machamp, "
           "Steelix e Hitmonlee; Gengar, Crobat e Dusclops; Dragonite, Gyarados, Kingdra e Aerodactyl; Alakazam, "
           "Heracross e a inicial do rival); as outras vagas trocam por espécies mais fortes do tema conforme o "
           "degrau sobe, com finais fortes e pseudolendários (Salamence, Metagross, Tyranitar) nos degraus 4–5. "
           "O degrau 5 tem uma troca a mais que o 4 em cada um, sempre fora o ás: Kingdra no lugar da Jynx, "
           "Tyranitar no do Hitmonlee, Sableye no do Tentacruel, Charizard no do Aerodactyl e Salamence no do "
           "Heracross.",
           "- **Itens:** todos têm item em todos os degraus. O ás: Fruta Sitrus no 1, item do tipo/Sobras do 2 em "
           "diante. Os outros: nos degraus 1–2 as frutas do Vs. Seeker (1: rodízio das frutas de status; "
           "2: Sitrus/Lum), girando pelo id do treinador; do 3 em diante, item escolhido por papel. Golpes: 4 por "
           "Pokémon, todos aprendíveis (nível ≤ o do time, MT/MO, ovo ou tutor), conferidos por `gerar.py`.", ""]
    for membro in MEMBROS_LIGA:
        out += [f"## {NOMES_MEMBROS[membro]}", ""]
        for d in DEGRAUS:
            out += [f"**Degrau {d}**", ""] + cab
            out += [_linha_mon(p, *mon) for p, mon in enumerate(time_liga(membro, d), 1)]
            out.append("")
    out += ["## Campeão (rival)", "",
            "Time = base (posições 1–4, igual nas 3 variantes) + 2 vagas da inicial do rival (posições 5–6): "
            "o parceiro do triângulo que cobre a fraqueza da inicial e a inicial final como ás. "
            "Variante = a inicial **do rival**, como nos times `_2` de hoje (o rival pega a inicial que vence a "
            "do jogador).", "",
            "| Variante (inicial do rival) | Posição 5 | Posição 6 (ás) |", "|---|---|---|"]
    for v in VARIANTES_CAMPEAO:
        par = [_nomes_especies()[m["species"]] for m in liga()["CAMPEAO"]["1"][v]]
        out.append(f"| {v.title()} | {par[0]} | {par[1]} |")
    out.append("")
    for d in DEGRAUS:
        out += [f"**Degrau {d}**", ""] + cab
        nivs = niveis(d, "campeao")
        bloco = liga()["CAMPEAO"][str(d)]
        for p, m in enumerate(bloco["base"], 1):
            out.append(_linha_mon(p, m["species"], nivs[p - 1], m["item"], m["moves"]))
        for v in VARIANTES_CAMPEAO:
            for k, m in enumerate(bloco[v]):
                p = TAMANHO_BASE_CAMPEAO + k + 1
                out.append(_linha_mon(p, m["species"], nivs[p - 1], m["item"], m["moves"])
                           .replace(f"| {p} |", f"| {p} ({v.title()}) |", 1))
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------- header C

HEADER = REPO / "src" / "data" / "rematch_tiers.h"


def header() -> str:
    """O texto de src/data/rematch_tiers.h: sRematchTierParties[linha de sRematches][degrau - 1][posição].

    Para (falha) se liga.json estiver fora da regra (problemas_liga): um header com golpe ilegal ou item errado
    nunca é gravado nem aceito pelo --conferir."""
    problemas = problemas_liga()
    if problemas:
        falha("liga.json fora da regra:\n  " + "\n  ".join(problemas))
    linhas = ler_revanches()
    out = ["// GERADO por tools/revanches/gerar.py; não editar (regenere com python3 -I tools/revanches/gerar.py).",
           "// Times das revanches do Vs. Seeker por degrau (POK-42), lidos por src/rematch_tier.c:",
           "// [linha de sRematches][degrau - 1][posição] = {espécie, item segurado, nível, IV (0-31)}.",
           "// A posição 6 é o ás; os golpes são os padrão do nível.",
           "",
           f"#define REMATCH_TIER_ROWS {len(linhas)}",
           "",
           "static const struct RematchTierMon sRematchTierParties[REMATCH_TIER_ROWS][REMATCH_TIER_COUNT][PARTY_SIZE] =",
           "{"]
    for i, linha in enumerate(linhas):
        out += [f"    // {linha[0]}", "    {"]
        for d in DEGRAUS:
            mons = ", ".join(f"{{{e}, {it}, {n}, {v}}}" for e, n, it, v in time_vs(i, d))
            out.append(f"        {{{mons}}},")
        out.append("    },")
    out += ["};", ""]
    out += header_liga()
    return "\n".join(out)


def header_liga() -> list[str]:
    """As linhas de sLeagueTierParties (tools/revanches/liga.json), no fim de src/data/rematch_tiers.h."""
    out = ["// Elite 4 e Campeão por degrau (tools/revanches/liga.json, times à mão), lidos por src/rematch_tier.c:",
           "// [trainerNum - TRAINER_ELITE_FOUR_LORELEI_2][degrau - 1][posição]; ids 735-741 = Lorelei, Bruno, Agatha,",
           "// Lance _2 e TRAINER_CHAMPION_REMATCH_SQUIRTLE/BULBASAUR/CHARMANDER (a inicial do rival). IV 31 = 255.",
           "",
           "static const struct TrainerMonItemCustomMoves sLeagueTierParties[7][REMATCH_TIER_COUNT][PARTY_SIZE] =",
           "{"]
    por_id: dict[str, list] = {}
    for (rotulo, membro, d, v), time in times_liga():
        trainer = f"TRAINER_CHAMPION_REMATCH_{v}" if membro == "CAMPEAO" else ID_LIGA[membro]
        por_id.setdefault(trainer, []).append((d, time))
    ordem = [ID_LIGA[m] for m in MEMBROS_LIGA] + [f"TRAINER_CHAMPION_REMATCH_{v}" for v in VARIANTES_CAMPEAO]
    ids = [_id_treinador()[t] for t in ordem]
    if ids != list(range(ids[0], ids[0] + len(ids))):
        falha(f"opponents.h: os ids da Liga não são seguidos na ordem {ordem}: {ids}")
    for trainer in ordem:
        out += [f"    // {trainer}", "    {"]
        for d, time in por_id[trainer]:
            out += [f"        // degrau {d}", "        {"]
            for e, n, it, golpes in time:
                out.append(f"            {{.iv = {IV_LIGA}, .lvl = {n}, .species = {e}, .heldItem = {it}, "
                           f".moves = {{{', '.join(golpes)}}}}},")
            out.append("        },")
        out.append("    },")
    out += ["};", ""]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--conferir", action="store_true", help="sai com 1 se o header commitado divergir")
    ap.add_argument("--amostra", action="store_true", help="imprime a amostra em Markdown")
    ap.add_argument("--amostra-liga", action="store_true", help="imprime os times da Liga por degrau em Markdown")
    args = ap.parse_args()
    if args.amostra_liga:
        sys.stdout.write(amostra_liga())
        return
    if args.amostra:
        sys.stdout.write(amostra())
        return
    novo = header()
    if args.conferir:
        atual = HEADER.read_text(encoding="utf-8", newline="") if HEADER.exists() else None
        if atual != novo:
            print(f"gerar.py: {HEADER.relative_to(REPO)} está fora de dia; rode python3 -I tools/revanches/gerar.py",
                  file=sys.stderr)
            sys.exit(1)
        return
    HEADER.write_text(novo, encoding="utf-8", newline="\n")
    print(f"gravado {HEADER.relative_to(REPO)} ({len(ler_revanches())} linhas x {len(DEGRAUS)} degraus)")


if __name__ == "__main__":
    main()
