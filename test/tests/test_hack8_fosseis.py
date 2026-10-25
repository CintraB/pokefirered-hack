"""Hack 8: os dois fósseis do Monte Lua (Domo e Hélice) no mesmo save.

- O jogador pega um fóssil; o outro continua no chão e pode ser pego em seguida (cada um com a sua
  flag de objeto `FLAG_HIDE_*` e a sua flag de posse `FLAG_GOT_*`). O Super Nerd (Miguel) só comenta:
  não anda até o outro fóssil nem o tira do mapa.
- Save antigo (o Miguel levou o outro): o fóssil reaparece na próxima visita, porque a regra de
  aparecer passou a ser "esta flag de posse está desligada" (sem flag nova no save); o Miguel volta
  para o lugar de origem (13, 11), senão ficaria em cima do fóssil que reapareceu.
- Laboratório de Cinnabar: com os dois fósseis, "já reviveu tudo" só vale depois de reviver os dois.
- Cartão "Os dois fósseis" no tópico "Pokédex e captura" da tela de novidades.
"""

import json
import re

from esteira.scenarios import REPO_ROOT

MOON = "data/maps/MtMoon_B2F"
LAB = "data/maps/CinnabarIsland_PokemonLab_ExperimentRoom"
LAB_PREFIXO = "CinnabarIsland_PokemonLab_ExperimentRoom"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _block(src: str, label: str) -> str:
    """Corpo de um rótulo de script, até o próximo rótulo global."""
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    return src[start:start + len(label) + 2 + (m.start() if m else len(src))]


def _text(label: str) -> str:
    t = _read(f"{MOON}/text.inc")
    bloco = t[t.index(f"{label}::"):]
    bloco = bloco[:bloco.index('$"') + 2]
    return "".join(re.findall(r'\.string "(.*?)"', bloco))


def _flat(text: str) -> str:
    return re.sub(r"\\[nlp]", " ", text)


def _scripts() -> str:
    return _read(f"{MOON}/scripts.inc")


# --- pegar um fóssil não leva o outro ----------------------------------------------------------

def test_pegar_o_domo_nao_move_o_miguel_nem_tira_a_helice():
    bloco = _block(_scripts(), "MtMoon_B2F_EventScript_DomeFossil")
    assert "removeobject LOCALID_DOME_FOSSIL" in bloco
    assert "removeobject LOCALID_HELIX_FOSSIL" not in bloco
    assert "applymovement LOCALID_MIGUEL" not in bloco and "copyobjectxytoperm" not in bloco
    assert "setflag FLAG_GOT_DOME_FOSSIL" in bloco and "setflag FLAG_GOT_HELIX_FOSSIL" not in bloco


def test_pegar_a_helice_nao_move_o_miguel_nem_tira_o_domo():
    bloco = _block(_scripts(), "MtMoon_B2F_EventScript_HelixFossil")
    assert "removeobject LOCALID_HELIX_FOSSIL" in bloco
    assert "removeobject LOCALID_DOME_FOSSIL" not in bloco
    assert "applymovement LOCALID_MIGUEL" not in bloco and "copyobjectxytoperm" not in bloco
    assert "setflag FLAG_GOT_HELIX_FOSSIL" in bloco and "setflag FLAG_GOT_DOME_FOSSIL" not in bloco


def test_os_dois_marcam_o_fossil_do_monte_moon_e_o_miguel_comenta_so_no_primeiro():
    for rotulo, outro in (("DomeFossil", "FLAG_GOT_HELIX_FOSSIL"), ("HelixFossil", "FLAG_GOT_DOME_FOSSIL")):
        bloco = _block(_scripts(), f"MtMoon_B2F_EventScript_{rotulo}")
        assert "setflag FLAG_GOT_FOSSIL_FROM_MT_MOON" in bloco
        assert f"goto_if_unset {outro}, MtMoon_B2F_EventScript_MiguelLetsYouTakeTheOther" in bloco
    comentario = _block(_scripts(), "MtMoon_B2F_EventScript_MiguelLetsYouTakeTheOther")
    assert "MtMoon_B2F_Text_TakeTheOtherFossilToo" in comentario and "release" in comentario


def test_o_miguel_nunca_mais_toma_um_fossil():
    assert "ThenThisFossilIsMine" not in _scripts() and "ThenThisFossilIsMine" not in _read(f"{MOON}/text.inc")
    assert "MiguelToHelixFossil" not in _scripts() and "MiguelToDomeFossil" not in _scripts()


# --- o fóssil que sobrou reaparece (inclusive em save antigo) ---------------------------------

def test_cada_fossil_aparece_enquanto_a_flag_de_posse_dele_esta_desligada():
    src = _scripts()
    trans = _block(src, "MtMoon_B2F_OnTransition")
    assert "call_if_unset FLAG_GOT_FOSSIL_FROM_MT_MOON" not in trans, "a regra não pode mais ser 'pegou algum'"
    assert "MtMoon_B2F_EventScript_ShowFossils" in trans
    mostrar = _block(src, "MtMoon_B2F_EventScript_ShowFossils")
    assert re.search(r"call_if_unset FLAG_GOT_DOME_FOSSIL, \w+", mostrar)
    assert re.search(r"call_if_unset FLAG_GOT_HELIX_FOSSIL, \w+", mostrar)
    assert "clearflag FLAG_HIDE_DOME_FOSSIL" in src and "clearflag FLAG_HIDE_HELIX_FOSSIL" in src


def test_save_antigo_miguel_volta_ao_lugar_de_origem():
    """Miguel nasce em (13, 11); o script antigo o deixava embaixo do fóssil que ele levou."""
    mapa = json.loads(_read(f"{MOON}/map.json"))
    miguel = next(o for o in mapa["object_events"] if o.get("local_id") == "LOCALID_MIGUEL")
    assert (miguel["x"], miguel["y"]) == (13, 11)
    trans = _block(_scripts(), "MtMoon_B2F_OnTransition")
    assert "MtMoon_B2F_EventScript_PutMiguelBack" in trans
    volta = _block(_scripts(), "MtMoon_B2F_EventScript_PutMiguelBack")
    assert "setobjectxyperm LOCALID_MIGUEL, 13, 11" in volta


def test_os_fosseis_continuam_com_as_flags_de_objeto_e_nenhuma_flag_nova():
    mapa = json.loads(_read(f"{MOON}/map.json"))
    flags = {o["local_id"]: o["flag"] for o in mapa["object_events"] if o.get("local_id") in
             ("LOCALID_DOME_FOSSIL", "LOCALID_HELIX_FOSSIL")}
    assert flags == {"LOCALID_DOME_FOSSIL": "FLAG_HIDE_DOME_FOSSIL", "LOCALID_HELIX_FOSSIL": "FLAG_HIDE_HELIX_FOSSIL"}
    usadas = set(re.findall(r"\bFLAG_\w+", _scripts()))
    assert usadas <= {"FLAG_GOT_FOSSIL_FROM_MT_MOON", "FLAG_HIDE_DOME_FOSSIL", "FLAG_HIDE_HELIX_FOSSIL",
                      "FLAG_GOT_DOME_FOSSIL", "FLAG_GOT_HELIX_FOSSIL"}, usadas


# --- falas ------------------------------------------------------------------------------------

def test_miguel_conversa_certo_conforme_quantos_fosseis_o_jogador_tem():
    bloco = _block(_scripts(), "MtMoon_B2F_EventScript_MiguelFossilPicked")
    assert "goto_if_unset FLAG_GOT_DOME_FOSSIL, MtMoon_B2F_EventScript_MiguelLetsYouTakeTheOther" in bloco
    assert "goto_if_unset FLAG_GOT_HELIX_FOSSIL, MtMoon_B2F_EventScript_MiguelLetsYouTakeTheOther" in bloco
    assert "msgbox MtMoon_B2F_Text_LabOnCinnabarRegeneratesFossils" in bloco


def test_falas_do_miguel_nao_dizem_mais_que_cada_um_leva_um():
    for rotulo in ("MtMoon_B2F_Text_MiguelDefeat", "MtMoon_B2F_Text_WellEachTakeAFossil",
                   "MtMoon_B2F_Text_TakeTheOtherFossilToo"):
        txt = _flat(_text(rotulo))
        assert "Cada um" not in txt and "dividir" not in txt and "é meu" not in txt, rotulo
    assert "os dois" in _flat(_text("MtMoon_B2F_Text_WellEachTakeAFossil"))
    assert "Eu não sou ganancioso" in _flat(_text("MtMoon_B2F_Text_WellEachTakeAFossil"))  # a ganância é dele, não bronca no jogador
    assert "outro" in _flat(_text("MtMoon_B2F_Text_TakeTheOtherFossilToo"))


def test_batalha_com_o_miguel_continua_igual():
    bloco = _block(_scripts(), "MtMoon_B2F_EventScript_BattleMiguel")
    assert "trainerbattle_no_intro TRAINER_SUPER_NERD_MIGUEL, MtMoon_B2F_Text_MiguelDefeat" in bloco
    assert "setvar VAR_MAP_SCENE_MT_MOON_B2F, 1" in bloco
    assert "MtMoon_B2F_Text_MiguelIntro" in bloco


# --- laboratório de Cinnabar ------------------------------------------------------------------

def test_lab_so_diz_que_reviveu_tudo_depois_dos_dois_fosseis_do_monte_moon():
    src = _read(f"{LAB}/scripts.inc")
    bloco = _block(src, f"{LAB_PREFIXO}_EventScript_CheckRevivedMtMoonFossil")
    # fóssil pendente (flag de posse ligada e a de reviver desligada) barra o "já reviveu tudo",
    # tanto o Hélice quanto o Domo
    assert "CheckAddHelixFossilToList" in bloco and "CheckAddDomeFossilToList" in bloco
    assert "FLAG_GOT_HELIX_FOSSIL" in bloco and "FLAG_GOT_DOME_FOSSIL" in bloco


def test_lab_oferece_um_fossil_de_cada_vez():
    src = _read(f"{LAB}/scripts.inc")
    cientista = _block(src, f"{LAB_PREFIXO}_EventScript_FossilScientist")
    # Hélice vem antes do Domo na fila; cada revivido liga a própria flag de "revivido"
    assert cientista.index("CheckAddHelixFossilToList") < cientista.index("CheckAddDomeFossilToList")
    assert "setflag FLAG_REVIVED_HELIX" in src and "setflag FLAG_REVIVED_DOME" in src


# --- cartão da tela de novidades ---------------------------------------------------------------

def test_cartao_os_dois_fosseis_no_topico_da_pokedex_e_captura():
    dados = json.loads(_read("src/data/novidades/cartoes.json"))
    topico = next(t for t in dados["topics"] if t["name"] == "Pokédex e captura")
    cartao = next(c for c in topico["cards"] if c["title"] == "Os dois fósseis")
    corpo = re.sub(r"\s+", " ", cartao["body"])
    assert all(e in corpo for e in ("Monte Lua", "Fóssil Domo", "Fóssil Hélice", "laboratório da Ilha Cinnabar"))
    assert "Monte Moon" not in corpo
    assert cartao["itemId"] == "ITEM_DOME_FOSSIL"
    assert "speciesBefore" not in cartao
