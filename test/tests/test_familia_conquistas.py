"""POK-51 (Task 7): conquistas e diário da Família Sombra. Leitura estática do JSON, do gerador e do C.

O comportamento no jogo (chefe vencido grava a conquista e a entrada do diário; Gengar selvagem comum não grava)
fica nos casos `familia/conquista_dom` e `familia/gengar_fora_nao_conta` do cenário `familia` da esteira.
"""

import json
import re

from esteira.scenarios import REPO_ROOT


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


DADOS = json.loads(_read("src/data/conquistas/conquistas.json"))
CONQ = {c["id"]: c for c in DADOS["conquistas"]}
DIARIO_C = _read("src/diario.c")
FAMILIA_C = _read("src/familia_sombra.c")
CONST_H = _read("include/constants/conquistas.h")

# num (= posição) das 41 conquistas e ordem do diário antes do POK-51: nada disso muda (viram posições no save).
ANTIGAS = ["insignia_rocha", "insignia_cascata", "insignia_trovao", "insignia_arcoiris", "insignia_alma",
           "insignia_pantano", "insignia_vulcao", "insignia_terra", "vencer_elite4", "campeao", "silph", "sevii",
           "treinadores", "lider_um_pokemon", "sem_desmaio", "golpe_x4", "rival_todas", "revanche_max",
           "e4_degrau100", "primeira_captura", "shinies", "aves", "caes", "mewtwo", "lugia_hooh", "miticos",
           "kanto_151", "dex_obtivel", "poke_ball_dificil", "fosseis", "nivel_50", "nivel_100", "primeiro_ovo",
           "ovo_shiny", "ovo_6ivs", "amizade_max", "espeon_umbreon", "cidades", "passos", "dinheiro", "horas"]
DIARIO_ANTIGO = ["brock", "misty", "surge", "erika", "koga", "sabrina", "blaine", "giovanni", "rival_lab",
                 "rival_rota22", "rival_cerulean", "rival_ss_anne", "rival_torre", "rival_silph",
                 "rival_rota22_final", "lorelei", "bruno", "agatha", "lance", "campeao", "articuno", "zapdos",
                 "moltres", "mewtwo", "raikou", "entei", "suicune", "lugia", "ho_oh", "mew", "celebi", "jirachi",
                 "deoxys"]
NOVAS = ["familia_dom", "familia_cobrador", "familia_pedagio", "familia_mercenario", "familia_toda"]


def _corpo(fonte: str, nome: str) -> str:
    m = re.search(rf"^(?:static )?\w[\w ]*\*?\s*\b{nome}\(.*?\)\n\{{\n(.*?)^\}}", fonte, re.M | re.S)
    assert m, nome
    return m.group(1)


def test_conquistas_no_fim():
    for i, cid in enumerate(ANTIGAS):
        assert CONQ[cid]["num"] == i, cid
    assert [CONQ[i]["num"] for i in NOVAS] == [41, 42, 43, 44, 45]
    assert all(CONQ[i]["aba"] == "batalha" and CONQ[i]["tipo"] == "EVENTO" for i in NOVAS)
    assert [e["id"] for e in DADOS["diario"][:len(DIARIO_ANTIGO)]] == DIARIO_ANTIGO
    assert [e["id"] for e in DADOS["diario"][len(DIARIO_ANTIGO):]] == [
        "familia_dom", "familia_cobrador", "familia_mercenario", "familia_pesadelo"]


def test_total_ativo_44():
    ativas = [c for c in DADOS["conquistas"] if c.get("ativa", True)]
    assert len(DADOS["conquistas"]) == 46 and len(ativas) == 44
    assert {c["id"] for c in DADOS["conquistas"] if not c.get("ativa", True)} == {"familia_mercenario", "familia_toda"}
    # os 3 eventos da parte 1 existem e são distintos
    evts = [CONQ[i]["param"] for i in NOVAS]
    assert len(set(evts)) == 5
    for e in evts:
        assert re.search(rf"#define {e}\s+\d+", CONST_H), e


def test_diario_so_no_predio():
    # o chefe tem tipo próprio: só entra quando a batalha é a do chefe; o selvagem comum só olha os LENDARIO
    por_id = {e["id"]: e for e in DADOS["diario"]}
    assert por_id["familia_dom"]["tipo"] == "chefe" and por_id["familia_dom"]["especie"] == "SPECIES_GENGAR"
    assert por_id["familia_cobrador"]["tipo"] == "chefe" and por_id["familia_cobrador"]["especie"] == "SPECIES_TYRANITAR"
    assert "SPECIES_GENGAR" not in [e.get("especie") for e in DADOS["diario"] if e["tipo"] == "lendario"]
    # as 2 da parte 2 ficam reservadas e nunca gravam (SPECIES_NONE)
    assert por_id["familia_mercenario"]["especie"] == por_id["familia_pesadelo"]["especie"] == "SPECIES_NONE"
    corpo = _corpo(DIARIO_C, "EventoDoLendario")
    assert "FamiliaSombra_EhChefe() ? DIARIO_TIPO_CHEFE : DIARIO_TIPO_LENDARIO" in corpo
    assert "gDiarioEventos[evt].tipo == tipo" in corpo


def test_ganchos_da_familia():
    caiu = _corpo(FAMILIA_C, "FamiliaSombra_ChefeCaiu")
    assert "CONQ_EVT_FAMILIA_DOM" in caiu and "CONQ_EVT_FAMILIA_COBRADOR" in caiu
    # o guard de estado vem antes: chamada repetida não conta de novo
    assert caiu.index("FamiliaSombra_ChefeAtivo") < caiu.index("Conquistas_Evento")
    assert "CONQ_EVT_FAMILIA_PEDAGIO_FORCA" in _corpo(FAMILIA_C, "FamiliaSombra_PedagioVencido")
