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
    # com ele: a sub da pergunta, que também desliga o gatilho
    assert f"call {P}_AskTier" in gatilho, gatilho
    assert gatilho[-1] == "end"
    pergunta = _bloco(texto, f"{P}_AskTier")
    assert "setvar VAR_TEMP_1, 1" in pergunta
    assert pergunta.index("setvar VAR_TEMP_1, 1") < pergunta.index("special BufferRematchTierName")
    assert any(re.fullmatch(r"multichoice \d+, \d+, MULTICHOICE_REMATCH_TIER, FALSE", c) for c in pergunta), pergunta
    cancela = [c for c in pergunta if c.startswith("goto_if_eq VAR_RESULT, SCR_MENU_CANCEL, ")]
    assert len(cancela) == 1, pergunta
    fica = _bloco(texto, cancela[0].split(", ")[2])
    assert not any(c.startswith("copyvar") for c in fica), fica
    assert any("Text_KeepTier" in c for c in fica) and fica[-1] == "return", fica
    # a escolha grava o degrau e confirma com o rótulo novo
    i = pergunta.index("copyvar VAR_REMATCH_TIER, VAR_RESULT")
    assert i > pergunta.index(cancela[0])
    assert "special BufferRematchTierName" in pergunta[i:]
    assert any("Text_TierSet" in c for c in pergunta[i:]) and pergunta[-1] == "return", pergunta


def test_guarda_oferece():
    texto = _scripts()
    for rotulo in (f"{P}_DoorGuard", f"{P}_SeviiIslandComplete"):
        bloco = _bloco(texto, rotulo)
        chamada = f"call_if_set FLAG_SYS_GAME_CLEAR, {P}_AskTier"
        assert chamada in bloco, (rotulo, bloco)
        assert bloco.index(chamada) < bloco.index("msgbox IndigoPlateau_PokemonCenter_1F_Text_FaceEliteFourGoodLuck")
    # o ramo "Lorelei ausente" e a porta bloqueada seguem os de hoje
    assert _bloco(texto, f"{P}_CheckSeviiIslandComplete") == [
        f"goto_if_set FLAG_SYS_CAN_LINK_WITH_RS, {P}_SeviiIslandComplete",
        "msgbox IndigoPlateau_PokemonCenter_1F_Text_LoreleiIsAbsentClosedForTimeBeing", "release", "end"]
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
    assert nomes[-2:] == ["ShouldUseLeagueRematchTeams", "BufferRematchTierName"], nomes[-3:]


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
