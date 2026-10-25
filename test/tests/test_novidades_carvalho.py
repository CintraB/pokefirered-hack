"""Tela de novidades, Task 5: o Prof. Carvalho oferece e abre a tela, sem emulador.

Logo depois de o jogador escolher o inicial (e de o rival pegar o dele), o Carvalho pergunta se quer
ver as novidades (Sim abre `special OpenNovidadesScreen` + `waitstate`; Não segue a história). Depois,
qualquer conversa com ele no laboratório termina oferecendo de novo, menos as cenas obrigatórias (chegada,
batalha do rival, entrega da Pokédex, cena da Dex Nacional) e as conversas de presente (Poké Balls, ovo
raro, Dex completa, Amuleto Brilhante recém-entregue). A avaliação da Pokédex roda inteira antes da oferta.
O roteiro rápido da esteira responde Não à pergunta depois do inicial (quick_opening.py).
"""

import re

import pytest

from esteira import check_text as ct
from esteira.scenarios import REPO_ROOT

LAB = REPO_ROOT / "data" / "maps" / "PalletTown_ProfessorOaksLab"
P = "PalletTown_ProfessorOaksLab_"
OFFER = f"{P}EventScript_OfferNovidades"
OFFER_FIRST = f"{P}EventScript_OfferNovidadesFirst"
OFFER_AFTER_RATING = f"{P}EventScript_OfferNovidadesAfterRating"
OPEN = f"{P}EventScript_OpenNovidades"
TEXTS = (f"{P}Text_OakOfferNovidadesFirst", f"{P}Text_OakNovidadesAnytime", f"{P}Text_OakOfferNovidades")


def _scripts() -> str:
    return re.sub(r"@[^\n]*", "", (LAB / "scripts.inc").read_text(encoding="utf-8"))


def _bloco(nome: str) -> str:
    """Comandos do rótulo `nome::` até o próximo rótulo (o que roda ao entrar nele, sem a queda)."""
    code = _scripts()
    m = re.search(rf"^{nome}::\s*$", code, re.M)
    assert m, f"rótulo {nome} não encontrado"
    fim = re.search(r"^\w+::", code[m.end():], re.M)
    return code[m.end():m.end() + fim.start()] if fim else code[m.end():]


def _comandos(nome: str) -> list[str]:
    return [l.strip() for l in _bloco(nome).splitlines() if l.strip()]


def test_special_so_dentro_da_abertura_com_waitstate():
    code = _scripts()
    assert code.count("special OpenNovidadesScreen") == 1
    cmds = _comandos(OPEN)
    i = cmds.index("special OpenNovidadesScreen")
    assert cmds[i + 1] == "waitstate"
    assert "fadescreen FADE_TO_BLACK" in cmds[:i]


@pytest.mark.parametrize("oferta", [OFFER_FIRST, OFFER])
def test_as_duas_ofertas_perguntam_e_abrem_a_tela(oferta):
    cmds = _comandos(oferta)
    # quest log (reprodução) sai antes de perguntar e de chegar ao special, como o diploma
    assert cmds[0] == "goto_if_questlog EventScript_ReleaseEnd", cmds
    pergunta = next(i for i, c in enumerate(cmds) if c.startswith("msgbox") and c.endswith("MSGBOX_YESNO"))
    assert f"goto_if_eq VAR_RESULT, YES, {OPEN}" in cmds[pergunta + 1:]
    assert "textcolor NPC_TEXT_COLOR_MALE" in cmds[:pergunta]


def test_textos_das_ofertas():
    assert f"msgbox {P}Text_OakOfferNovidadesFirst, MSGBOX_YESNO" in _comandos(OFFER_FIRST)
    # Não na 1ª vez: o Carvalho avisa que dá para ver depois; nas outras, só segue
    assert f"msgbox {P}Text_OakNovidadesAnytime" in _comandos(OFFER_FIRST)
    assert f"msgbox {P}Text_OakOfferNovidades, MSGBOX_YESNO" in _comandos(OFFER)
    texto = (LAB / "text.inc").read_text(encoding="utf-8")
    for label in TEXTS:
        assert re.search(rf"^{label}::", texto, re.M), label
    assert "novidades" in texto[texto.index(f"{P}Text_OakOfferNovidadesFirst::"):].split("$", 1)[0]


def test_oferta_logo_depois_do_inicial_e_do_rival():
    cmds = _comandos(f"{P}EventScript_RivalTakesStarter")
    cena = cmds.index("setvar VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 3")
    placa = next(i for i, c in enumerate(cmds) if "ReadyEndSignLadyScene" in c)
    assert cena < placa < cmds.index(f"goto {OFFER_FIRST}")
    assert "release" not in cmds[cena:], "a cena termina na oferta (que solta o jogador)"


# conversas comuns com o Carvalho: a fala de sempre e, no fim, a oferta
CONVERSAS = ("OakCanReachNextTownWithMon", "OakBattleMonForItToGrow", "MonsAroundWorldWait",
             "PlayerAlreadyGotBalls", "OakJustShownCompleteDex")


@pytest.mark.parametrize("nome", CONVERSAS)
def test_conversas_comuns_terminam_oferecendo(nome):
    cmds = _comandos(f"{P}EventScript_{nome}")
    assert cmds[0].startswith("msgbox "), cmds
    assert cmds[-2:] == [f"goto {OFFER}", "end"], cmds


def test_avaliacao_roda_inteira_antes_da_oferta():
    # a avaliação da Pokédex (em pessoa) acaba e só então vem a oferta
    for nome in ("RatePokedex", "TryStartNationalDexScene"):
        cmds = _comandos(f"{P}EventScript_{nome}")
        nota = cmds.index(f"call {P}EventScript_NoteShinyCharmBeforeRating")
        assert nota < cmds.index("call PokedexRating_EventScript_RateInPerson"), nome
    rate = _comandos(f"{P}EventScript_RatePokedex")
    assert rate.index(f"goto_if_set FLAG_OAK_SAW_DEX_COMPLETION, {P}EventScript_DexCompleted") \
        < rate.index(f"goto {OFFER_AFTER_RATING}")
    assert _comandos(f"{P}EventScript_DontStartNationalDexScene")[-2:] == [f"goto {OFFER_AFTER_RATING}", "end"]


def test_amuleto_recem_entregue_fica_sem_oferta():
    # a avaliação pode entregar o Amuleto Brilhante: nessa conversa fica só o presente
    nota = _comandos(f"{P}EventScript_NoteShinyCharmBeforeRating")
    assert "clearflag HAD_SHINY_CHARM_BEFORE_RATING" in nota
    assert any(c.startswith("call_if_set FLAG_GOT_SHINY_CHARM,") for c in nota)
    depois = _comandos(OFFER_AFTER_RATING)
    assert depois[:3] == [f"goto_if_unset FLAG_GOT_SHINY_CHARM, {OFFER}",
                          f"goto_if_set HAD_SHINY_CHARM_BEFORE_RATING, {OFFER}",
                          "release"], depois
    assert re.search(r"^\.equ HAD_SHINY_CHARM_BEFORE_RATING,\s*FLAG_TEMP_3$", _scripts(), re.M)


# cenas obrigatórias e conversas de presente: nenhuma passa pela oferta
SEM_OFERTA = ("LeaveStarterSceneTrigger", "RivalBattle", "EndRivalBattle",
              "ConfirmStarterChoice", "ChoseStarter", "RivalPicksStarter",
              "ReceiveDexScene", "EnterForNationalDexScene", "NationalDexScene",
              "GivePlayerMoreBalls", "OakGivePendingRareEgg", "TryGiveRareEgg", "DexCompleted",
              "ProfOakStoryStage", "ProfOak", "OakCheckRareEgg", "CheckIfPlayerNeedsBalls")


@pytest.mark.parametrize("nome", SEM_OFERTA)
def test_cenas_e_presentes_sem_oferta(nome):
    assert "Novidades" not in _bloco(f"{P}EventScript_{nome}"), nome


def test_antes_do_inicial_sem_oferta():
    # var de cena < 3 (ainda escolhendo): "Qual você vai escolher?" e solta, sem oferta
    cmds = _comandos(f"{P}EventScript_ProfOakStoryStage")
    assert cmds[-3:] == [f"msgbox {P}Text_OakWhichOneWillYouChoose", "release", "end"]


@pytest.fixture(scope="module")
def resultados():
    return ct.check_text(str(REPO_ROOT), {"text": []}, english="bloqueante")


def test_textos_novos_passam_na_checagem(resultados):
    achados = [f"{r.name}: {r.detail}" for r in resultados
               if r.status != "ok" and any(label in r.detail for label in TEXTS)]
    assert achados == []


def test_cena_de_chegada_sem_oferta():
    assert "Novidades" not in _bloco(f"{P}ChooseStarterScene")


def test_roteiro_rapido_responde_nao_e_confere_a_pergunta():
    from esteira.scenarios import base

    opening = (REPO_ROOT / "test" / "esteira" / "scenarios" / "quick_opening.py").read_text(encoding="utf-8")
    assert "self._novidades_offer()" in opening and 'return KEY_B                         # "Quer ver as novidades' in opening
    assert 'assert offers == 1' in opening
    # o texto que o roteiro procura é o das duas perguntas do Carvalho
    texto = (LAB / "text.inc").read_text(encoding="utf-8")
    for label in (f"{P}Text_OakOfferNovidadesFirst", f"{P}Text_OakOfferNovidades"):
        bloco = texto[texto.index(f"{label}::"):].split("$", 1)[0]
        corrido = re.sub(r'"\s*\n\s*\.string "', "", bloco)
        assert base.NOVIDADES_OFFER in corrido, label
