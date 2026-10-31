"""Revanches por degrau (POK-42), Task 4: a guarda da porta da Liga pergunta o degrau.

No Centro Pokémon do Platô Indigo, depois do Hall da Fama, a guarda da porta (`LOCALID_LEAGUE_DOOR_GUARD`)
pergunta o degrau quando o jogador pisa na casa em frente à porta (4,2), uma vez por visita (`VAR_TEMP_1`, que
zera a cada mapa), e também quando ele fala com ela. A escolha vai para `VAR_REMATCH_TIER`; o rótulo do degrau
atual sai do special `BufferRematchTierName`. Aqui tudo é estático; o comportamento fica no emulador.
"""

import json
import re

from esteira.scenarios import REPO_ROOT

MAPA = REPO_ROOT / "data" / "maps" / "IndigoPlateau_PokemonCenter_1F"
P = "IndigoPlateau_PokemonCenter_1F_EventScript"
ROTULOS = ("gText_RematchTier_Normal", "gText_RematchTier_60", "gText_RematchTier_70", "gText_RematchTier_80",
           "gText_RematchTier_90", "gText_RematchTier_100")
TEXTOS = ("Normal", "Nível 60", "Nível 70", "Nível 80", "Nível 90", "Nível 100")


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _bloco(texto: str, rotulo: str) -> list[str]:
    """Os comandos do rótulo `rotulo::` até a linha em branco."""
    m = re.search(rf"^{rotulo}::\n(.*?)\n\n", texto + "\n\n", re.S | re.M)
    assert m, f"{rotulo} não encontrado"
    return [linha.strip() for linha in m.group(1).splitlines() if linha.strip()]


def _scripts() -> str:
    return _ler(MAPA / "scripts.inc")


def test_gatilho_da_porta():
    mapa = json.loads(_ler(MAPA / "map.json"))
    gatilhos = [c for c in mapa["coord_events"] if c.get("script") == f"{P}_TierTrigger"]
    assert len(gatilhos) == 1, mapa["coord_events"]
    c = gatilhos[0]
    assert (c["type"], c["x"], c["y"], c["elevation"]) == ("trigger", 4, 2, 3), c
    assert (c["var"], str(c["var_value"])) == ("VAR_TEMP_1", "0"), c


def test_script_do_degrau():
    texto = _scripts()
    gatilho = _bloco(texto, f"{P}_TierTrigger")
    assert gatilho[0].startswith("goto_if_questlog "), gatilho
    # sem o Hall da Fama: só desliga o gatilho até sair do mapa
    desligado = [c for c in gatilho if c.startswith("goto_if_unset FLAG_SYS_GAME_CLEAR, ")]
    assert len(desligado) == 1, gatilho
    assert _bloco(texto, desligado[0].split(", ")[1]) == ["setvar VAR_TEMP_1, 1", "end"]
    # com ele: a sub da pergunta (Liga aberta), entre lockall e releaseall
    chamada = f"call {P}_AskTier"
    assert chamada in gatilho, gatilho
    assert gatilho.index("lockall") < gatilho.index(chamada) < gatilho.index("releaseall")
    assert gatilho[-1] == "end"
    # as duas subs (Liga aberta e fechada) só mudam a confirmação; a escolha fica numa sub só
    for sub, confirma in ((f"{P}_AskTier", "Text_TierSet"), (f"{P}_AskTierLeagueClosed", "Text_TierSetLeagueClosed")):
        bloco = _bloco(texto, sub)
        assert bloco[0].startswith("goto_if_questlog "), bloco
        assert bloco[1] == f"call {P}_ChooseTier", bloco
        assert bloco[2] == "goto_if_eq VAR_RESULT, SCR_MENU_CANCEL, EventScript_Return", bloco
        assert bloco[3] == f"msgbox IndigoPlateau_PokemonCenter_1F_{confirma}" and bloco[4:] == ["return"], bloco
    escolha = _bloco(texto, f"{P}_ChooseTier")
    assert escolha.index("setvar VAR_TEMP_1, 1") < escolha.index("special BufferRematchTierName")
    # a lista abre com o cursor no degrau atual (special ShowRematchTierMenu) e o script espera a escolha
    lista = escolha.index("special ShowRematchTierMenu")
    assert escolha[lista + 1] == "waitstate", escolha
    assert escolha.index("waitmessage") < lista
    assert not any(c.startswith("multichoice") for c in escolha), escolha
    cancela = [c for c in escolha if c.startswith("goto_if_eq VAR_RESULT, SCR_MENU_CANCEL, ")]
    assert escolha.index(cancela[0]) == lista + 2, escolha
    assert len(cancela) == 1, escolha
    fica = _bloco(texto, cancela[0].split(", ")[2])
    # sem copyvar e sem mexer no VAR_RESULT (as subs de cima testam o SCR_MENU_CANCEL depois)
    assert fica == ["msgbox IndigoPlateau_PokemonCenter_1F_Text_KeepTier", "return"], fica
    # a escolha grava o degrau e põe o rótulo novo no gStringVar1 para a confirmação
    i = escolha.index("copyvar VAR_REMATCH_TIER, VAR_RESULT")
    assert i > escolha.index(cancela[0])
    assert escolha[i + 1:] == ["special BufferRematchTierName", "return"], escolha
    assert len(re.findall(r"^\tcopyvar VAR_REMATCH_TIER, VAR_RESULT$", texto, re.M)) == 1
    # a lista sai só do special (nenhum multichoice com o cursor fixo em Normal)
    assert "MULTICHOICE_REMATCH_TIER" not in texto
    assert len(re.findall(r"special ShowRematchTierMenu$", texto, re.M)) == 1


def test_lista_abre_no_degrau_atual():
    """A guarda abre a lista com o cursor no degrau salvo: quem aperta A sem mexer mantém o degrau (B cancela)."""
    fonte = _ler(REPO_ROOT / "src" / "rematch_tier.c")
    assert "void ShowRematchTierMenu(void);" in _ler(REPO_ROOT / "include" / "rematch_tier.h")
    m = re.search(r"^void ShowRematchTierMenu\(void\)\n\{\n(.*?)^\}", fonte, re.S | re.M)
    assert m, "ShowRematchTierMenu não encontrada"
    chamada = re.sub(r"\s+", " ", m.group(1)).strip()
    assert re.fullmatch(r"ScriptMenu_MultichoiceWithDefault\(\d+, \d+, MULTICHOICE_REMATCH_TIER, FALSE, "
                        r"GetRematchTier\(\)\);", chamada), chamada
    assert '#include "script_menu.h"' in fonte
    # a mesma posição da lista de antes (20, 0), à direita da caixa de texto
    assert "ScriptMenu_MultichoiceWithDefault(20, 0, " in chamada
    # a assinatura: (left, top, mcId, ignoreBpress, cursorPos)
    menu = _ler(REPO_ROOT / "src" / "script_menu.c")
    assert "bool8 ScriptMenu_MultichoiceWithDefault(u8 left, u8 top, u8 mcId, u8 ignoreBpress, u8 cursorPos)" in menu


def test_guarda_oferece():
    texto = _scripts()
    for rotulo in (f"{P}_DoorGuard", f"{P}_SeviiIslandComplete"):
        bloco = _bloco(texto, rotulo)
        chamada = f"call_if_set FLAG_SYS_GAME_CLEAR, {P}_AskTier"
        assert chamada in bloco, (rotulo, bloco)
        assert bloco.index(chamada) < bloco.index("msgbox IndigoPlateau_PokemonCenter_1F_Text_FaceEliteFourGoodLuck")
    # Liga fechada (Dex Nacional antes do fim das Sevii): depois do "Lorelei ausente", a lista com a confirmação
    # sem a Elite Quatro
    assert _bloco(texto, f"{P}_CheckSeviiIslandComplete") == [
        f"goto_if_set FLAG_SYS_CAN_LINK_WITH_RS, {P}_SeviiIslandComplete",
        "msgbox IndigoPlateau_PokemonCenter_1F_Text_LoreleiIsAbsentClosedForTimeBeing",
        f"call_if_set FLAG_SYS_GAME_CLEAR, {P}_AskTierLeagueClosed", "release", "end"]
    # a porta continua bloqueada
    assert _bloco(texto, f"{P}_CheckBlockDoor") == [
        "goto_if_set FLAG_SYS_CAN_LINK_WITH_RS, EventScript_Return",
        "setobjectxyperm LOCALID_LEAGUE_DOOR_GUARD, 4, 2", "return"]


def test_lista_tem_seis():
    assert re.search(r"^#define MULTICHOICE_REMATCH_TIER\s+65\b", _ler(REPO_ROOT / "include" / "constants" / "menu.h"),
                     re.M)
    menu = _ler(REPO_ROOT / "src" / "script_menu.c")
    m = re.search(r"sMultichoiceList_RematchTier\[\] = \{\n(.*?)\n\};", menu, re.S)
    assert m
    assert re.findall(r"\{ (\w+) \}", m.group(1)) == list(ROTULOS)
    assert "[MULTICHOICE_REMATCH_TIER] = MULTICHOICE(sMultichoiceList_RematchTier)," in re.sub(r" {2,}", " ", menu)
    # uma fonte só dos 6 rótulos: strings.c, usada também pelo special
    strings = _ler(REPO_ROOT / "src" / "strings.c")
    header = _ler(REPO_ROOT / "include" / "strings.h")
    for rotulo, valor in zip(ROTULOS, TEXTOS):
        assert f'const u8 {rotulo}[] = _("{valor}");' in strings, rotulo
        assert f"extern const u8 {rotulo}[];" in header, rotulo
        assert len(valor) <= 10


def test_special_do_rotulo():
    fonte = _ler(REPO_ROOT / "src" / "rematch_tier.c")
    assert "void BufferRematchTierName(void);" in _ler(REPO_ROOT / "include" / "rematch_tier.h")
    m = re.search(r"^void BufferRematchTierName\(void\)\n\{\n(.*?)^\}", fonte, re.S | re.M)
    assert m, "BufferRematchTierName não encontrada"
    corpo = m.group(1)
    assert "StringCopy(gStringVar1, " in corpo and "GetRematchTier()" in corpo
    tabela = re.search(r"sRematchTierNames\[\] = \{\n(.*?)\n\};", fonte, re.S)
    assert tabela and re.findall(r"(gText_RematchTier_\w+)", tabela.group(1)) == list(ROTULOS)
    specials = _ler(REPO_ROOT / "data" / "specials.inc")
    nomes = re.findall(r"def_special (\w+)", specials.split("gSpecialsEnd::")[0])
    assert nomes[-3:] == ["ShouldUseLeagueRematchTeams", "BufferRematchTierName", "ShowRematchTierMenu"], nomes[-4:]


def test_textos_aprovados():
    texto = _ler(MAPA / "text.inc")

    def junto(rotulo):
        m = re.search(rf"^IndigoPlateau_PokemonCenter_1F_Text_{rotulo}::\n((?:\s+\.string \".*\"\n?)+)", texto, re.M)
        assert m, rotulo
        partes = re.findall(r'\.string "(.*)"', m.group(1))
        return re.sub(r"\\[nlp]", " ", "".join(partes)).rstrip("$")

    assert junto("AskTier") == ("Que bom ver você de volta à Liga! A Liga Pokémon pode ajustar a força dos "
                                "desafiantes. Hoje está em {STR_VAR_1}. Qual nível você quer enfrentar?")
    assert junto("TierSet") == ("Combinado! A Elite Quatro e as revanches do Explorador VS vão usar "
                                "{STR_VAR_1}.")
    assert junto("KeepTier") == "Tudo bem, fica como está."
    # com a Liga fechada (Lorelei ausente), a confirmação não fala da Elite Quatro
    fechada = junto("TierSetLeagueClosed")
    assert fechada == "Combinado! As revanches do Explorador VS vão usar {STR_VAR_1}."
    assert "Elite" not in fechada
