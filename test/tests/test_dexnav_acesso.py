"""DexNav (POK-47), Task 4: o acesso — linha "DEXNAV" no menu Start, item-chave registrável no SELECT, sem emulador.

Spec (docs/superpowers/specs/2026-10-31-dexnav-design.md): a linha "DEXNAV" aparece logo abaixo de "POKéDEX", junto
com ela (`FLAG_SYS_POKEDEX_GET`), e não depende do item estar na bolsa; o item-chave DEXNAV (slot livre "????????",
molde do PC Portátil do POK-36) vem no jogo novo e um save antigo o ganha ao CONTINUAR; pode ser registrado no SELECT
e usado pela bolsa. Ao sair, a tela volta exatamente de onde veio: menu Start reaberto, campo ou bolsa (mesmo bolso e
posição, como o Arquivo Fama). Com o DEXNAV, o menu Start chega a 8 linhas: a geometria tem de continuar fora da
barra de ajuda e dos tiles do diálogo. Este arquivo lê o C, o JSON e o gráfico como texto; o comportamento no emulador
fica no cenário `dexnav` (Task 5).
"""

import json
import re

from PIL import Image

from esteira import check_text, field_menu
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
START_MENU_C = SRC / "start_menu.c"
NEW_MENU_HELPERS_C = SRC / "new_menu_helpers.c"
HELP_MESSAGE_C = SRC / "help_message.c"
ITEM_USE_C = SRC / "item_use.c"
NEW_GAME_C = SRC / "new_game.c"
OVERWORLD_C = SRC / "overworld.c"
STRINGS_C = SRC / "strings.c"
ITEMS_JSON = SRC / "data" / "items.json"
ITEMS_H = REPO_ROOT / "include" / "constants" / "items.h"
ICON_TABLE = SRC / "data" / "item_icon_table.h"
ICONS_GFX_H = SRC / "data" / "graphics" / "items.h"
GRAPHICS_H = REPO_ROOT / "include" / "graphics.h"
ITEM_USE_H = REPO_ROOT / "include" / "item_use.h"
NEW_GAME_H = REPO_ROOT / "include" / "new_game.h"
PALETA = REPO_ROOT / "graphics" / "items" / "icon_palettes" / "dexnav.pal"

SLOT_DEXNAV = 72          # o primeiro "????????" livre depois do POK-36/37 (ITEM_048)
ROTULO_MENU_PX = 7 * 8 - 8   # janela de 7 tiles, texto em x = 8 (pkfr-menus-telas §2)
AJUDA_PX = 30 * 8 - 2        # barra de ajuda: 30 tiles, x = 2
DESCRICAO_ITEM_PX = 198      # descrição na bolsa (regra de items.json do check_text)


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _sem_comentarios(fonte: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", fonte, flags=re.S)


def _medir(texto: str, fonte: str = "normal") -> int:
    env = check_text._load_env(REPO_ROOT)
    return check_text.measure(texto + "$", env, font=fonte).widest


def _string(nome: str) -> str:
    m = re.search(rf'const u8 {nome}\[\]\s*=\s*_\("(.*?)"\);', _ler(STRINGS_C))
    assert m, f"{nome} não está em src/strings.c"
    return m.group(1)


def _enum_start_menu() -> list[str]:
    m = re.search(r"enum StartMenuOption\s*\{(.*?)\};", _ler(START_MENU_C), re.S)
    assert m
    return re.findall(r"\b(STARTMENU_\w+|MAX_STARTMENU_ITEMS)\b", _sem_comentarios(m.group(1)))


def _itens() -> list[dict]:
    return json.loads(_ler(ITEMS_JSON))["items"]


# --- menu Start ---------------------------------------------------------------------------------------------------

def test_menu_start():
    """Entrada nova no fim do enum (os índices que a esteira usa não mudam), na tabela e na ajuda (posicional), logo
    abaixo de POKéDEX e só com FLAG_SYS_POKEDEX_GET; o espelho da esteira acompanha."""
    enum = _enum_start_menu()
    assert enum[-2:] == ["STARTMENU_DEXNAV", "MAX_STARTMENU_ITEMS"]
    assert enum.index("STARTMENU_SAVE") == field_menu.STARTMENU_SAVE    # os de antes não andaram
    assert field_menu.STARTMENU_DEXNAV == enum.index("STARTMENU_DEXNAV")
    assert field_menu.MAX_STARTMENU_ITEMS == enum.index("MAX_STARTMENU_ITEMS")

    fonte = _sem_comentarios(_ler(START_MENU_C))
    assert re.search(r"\[STARTMENU_DEXNAV\]\s*=\s*\{\s*gText_MenuDexNav,\s*\{\.u8_void = StartMenuDexNavCallback\}",
                     fonte)
    descricoes = re.search(r"sStartMenuDescPointers\[\]\s*=\s*\{(.*?)\};", fonte, re.S).group(1)
    descricoes = re.findall(r"gStartMenuDesc_\w+", descricoes)
    assert len(descricoes) == len(enum) - 1                     # posicional: uma por entrada do enum
    assert descricoes[enum.index("STARTMENU_DEXNAV")] == "gStartMenuDesc_DexNav"

    normal = _corpo(fonte, "SetUpStartMenu_NormalField")
    assert re.search(r"if \(FlagGet\(FLAG_SYS_POKEDEX_GET\) == TRUE\)\s*\{\s*"
                     r"AppendToStartMenuItems\(STARTMENU_POKEDEX\);\s*"
                     r"AppendToStartMenuItems\(STARTMENU_DEXNAV\);\s*\}", normal), \
        "DEXNAV logo abaixo de POKéDEX, dentro da condição da Pokédex"
    safari = _corpo(fonte, "SetUpStartMenu_SafariZone")
    assert re.search(r"AppendToStartMenuItems\(STARTMENU_POKEDEX\);\s*"
                     r"if \(FlagGet\(FLAG_SYS_POKEDEX_GET\) == TRUE\)\s*AppendToStartMenuItems\(STARTMENU_DEXNAV\);",
                     safari), "na Zona Safari também, logo abaixo de POKéDEX"
    for sem in ("SetUpStartMenu_Link", "SetUpStartMenu_UnionRoom"):
        assert "STARTMENU_DEXNAV" not in _corpo(fonte, sem)


def test_menu_start_abre_e_volta_ao_menu():
    """No molde de StartMenuOptionCallback: espera o fade, fecha as janelas do menu e abre a tela; a volta reabre o
    menu Start (CB2_ReturnToFieldWithOpenMenu)."""
    fonte = _sem_comentarios(_ler(START_MENU_C))
    cb = _corpo(fonte, "StartMenuDexNavCallback")
    assert "if (!gPaletteFade.active)" in cb
    ordem = ["PlayRainStoppingSoundEffect();", "DestroySafariZoneStatsWindow();", "DestroyStartMenuClockWindow();",
             "CleanupOverworldWindowsAndTilemaps();", "DexNav_Open(CB2_ReturnToFieldWithOpenMenu);", "return TRUE;"]
    posicoes = [cb.find(passo) for passo in ordem]
    assert -1 not in posicoes and posicoes == sorted(posicoes), cb
    assert '#include "dexnav.h"' in _ler(START_MENU_C)
    # sai do campo com fade (não está nas exceções de StartMenu_FadeScreenIfLeavingOverworld)
    assert "StartMenuDexNavCallback" not in _corpo(fonte, "StartMenu_FadeScreenIfLeavingOverworld")


def test_rotulo_e_ajuda_cabem():
    assert _string("gText_MenuDexNav") == "DEXNAV"
    assert _medir(_string("gText_MenuDexNav")) <= ROTULO_MENU_PX
    ajuda = _string("gStartMenuDesc_DexNav")
    linhas = ajuda.split("\\n")
    assert len(linhas) <= 2
    assert all(_medir(linha) <= AJUDA_PX for linha in linhas), ajuda
    strings_h = _ler(REPO_ROOT / "include" / "strings.h")
    assert "extern const u8 gText_MenuDexNav[];" in strings_h
    assert "extern const u8 gStartMenuDesc_DexNav[];" in strings_h


def test_menu_start_com_oito_linhas_cabe():
    """Com 8 linhas (DEXNAV), o passo de 15 px pisaria na barra de ajuda (linha 15) e nos tiles do diálogo (0x198):
    acima de 7 linhas o passo cai para 13 px e a janela fica com a altura de 7 linhas. A fonte normal tem 14 px de
    altura e só a sombra das pernas (g, ç, ...) usa a última linha, então nada some além dela."""
    fonte = _sem_comentarios(_ler(START_MENU_C))
    passo = _corpo(fonte, "StartMenuLineHeight")
    m = re.search(r"return sNumStartMenuItems > START_MENU_FULL_PITCH_ROWS \? (\d+) : (\d+);", passo)
    assert m, passo
    curto, normal = int(m.group(1)), int(m.group(2))
    assert normal == 15
    linhas_cheias = int(re.search(r"#define START_MENU_FULL_PITCH_ROWS (\d+)", _ler(START_MENU_C)).group(1))
    assert linhas_cheias == 7

    # janela: CreateStartMenuWindow(n) faz 2n − 1 tiles a partir da linha 1, moldura embaixo, tiles desde 0x13D
    cria = re.search(r"SetWindowTemplateFields\(0, 0x16, 1, 7, height \* 2 - 1, \w+, (0x[0-9A-F]+)\)",
                     _ler(NEW_MENU_HELPERS_C))
    base = int(cria.group(1), 16)
    desenho = _corpo(fonte, "DoDrawStartMenu")
    assert "CreateStartMenuWindow(min(sNumStartMenuItems, START_MENU_FULL_PITCH_ROWS))" in desenho
    for n in (7, 8):
        altura_tiles = 2 * min(n, linhas_cheias) - 1
        passo_px = curto if n > linhas_cheias else normal
        assert (n - 1) * passo_px + 14 - 1 <= altura_tiles * 8, f"{n} linhas: a última sai da janela"
        assert 1 + altura_tiles + 1 <= 15, f"{n} linhas: a moldura pisa na barra de ajuda (linha 15)"
        assert base + 7 * altura_tiles <= 0x198, f"{n} linhas: os tiles invadem o diálogo"
    assert curto >= 13, "menos de 13 px: a linha de baixo apagaria a de cima além da sombra"
    ajuda = re.search(r"\.tilemapTop = (\d+)", _ler(HELP_MESSAGE_C))
    assert int(ajuda.group(1)) == 15

    # o passo vale para o texto, o nome do jogador e o cursor
    imprimir = _corpo(fonte, "PrintStartMenuItems")
    assert imprimir.count("i * StartMenuLineHeight()") == 2 and "i * 15" not in imprimir
    assert re.search(r"Menu_InitCursor\(GetStartMenuWindowId\(\), FONT_NORMAL, 0, 0, StartMenuLineHeight\(\),",
                     desenho)


# --- o item-chave -------------------------------------------------------------------------------------------------

def test_item_registravel():
    """Item-chave no primeiro slot livre, registrável no SELECT, com o uso no molde do Arquivo Fama."""
    assert re.search(rf"^#define ITEM_DEXNAV {SLOT_DEXNAV}$", _ler(ITEMS_H), re.M)
    item = _itens()[SLOT_DEXNAV]
    assert item["itemId"] == "ITEM_DEXNAV"
    assert item["english"] == "DEXNAV"
    assert item["price"] == 0
    assert item["holdEffect"] == "HOLD_EFFECT_NONE"
    assert item["importance"] == 1
    assert item["registrability"] == 1
    assert item["pocket"] == "POCKET_KEY_ITEMS"
    assert item["type"] == "ITEM_TYPE_BAG_MENU"
    assert item["fieldUseFunc"] == "FieldUseFunc_DexNav"
    assert item["battleUsage"] == 0 and item["battleUseFunc"] == "NULL"
    assert len(item["english"]) <= check_text.ITEM_NAME_MAX_CHARS
    assert _medir(item["english"]) <= 110 - 9          # coluna do nome na bolsa (regra *.name do check_text)
    linhas = item["description_english"].split("\\n")
    assert len(linhas) <= 3
    assert all(_medir(linha) <= DESCRICAO_ITEM_PX for linha in linhas), item["description_english"]


def test_item_usa_e_volta_de_onde_veio():
    """Da bolsa: sai com fade e a tela volta à bolsa (CB2_BagMenuFromStartMenu: mesmo bolso e posição). Do SELECT
    (data[3] = 1): fade no campo e a tela volta ao campo."""
    fonte = _sem_comentarios(_ler(ITEM_USE_C))
    uso = _corpo(fonte, "FieldUseFunc_DexNav")
    assert re.search(r"if \(gTasks\[taskId\]\.data\[3\] == 0\)\s*\{\s*ItemMenu_SetExitCallback\(OpenDexNavFromBag\);"
                     r"\s*ItemMenu_StartFadeToExitCallback\(taskId\);", uso), uso
    assert "FadeScreen(FADE_TO_BLACK, 0);" in uso
    assert "gTasks[taskId].func = Task_OpenDexNavFromField;" in uso
    assert "DexNav_Open(CB2_BagMenuFromStartMenu);" in _corpo(fonte, "OpenDexNavFromBag")
    campo = _corpo(fonte, "Task_OpenDexNavFromField")
    ordem = ["if (!gPaletteFade.active)", "CleanupOverworldWindowsAndTilemaps();", "SetFieldCallback2ForItemUse();",
             "DexNav_Open(CB2_ReturnToField);", "DestroyTask(taskId);"]
    posicoes = [campo.find(passo) for passo in ordem]
    assert -1 not in posicoes and posicoes == sorted(posicoes), campo
    assert "void FieldUseFunc_DexNav(u8 taskId);" in _ler(ITEM_USE_H)
    assert '#include "dexnav.h"' in _ler(ITEM_USE_C)


def test_icone_do_item():
    """Ícone no molde da Incubadora (POK-37): o desenho do Arquivo Fama com uma paleta nova (JASC, 16 cores, CRLF)."""
    tabela = _ler(ICON_TABLE)
    assert re.search(r"\[ITEM_DEXNAV\]\s*=\s*\{gItemIcon_FameChecker, gItemIconPalette_DexNav\}", tabela)
    assert ('const u32 gItemIconPalette_DexNav[] = INCBIN_U32("graphics/items/icon_palettes/dexnav.gbapal.lz");'
            in _ler(ICONS_GFX_H))
    assert "extern const u32 gItemIconPalette_DexNav[];" in _ler(GRAPHICS_H)
    bruto = PALETA.read_bytes()
    assert b"\r\n" in bruto and b"\n" not in bruto.replace(b"\r\n", b"")
    linhas = bruto.decode("ascii").split("\r\n")
    assert linhas[:3] == ["JASC-PAL", "0100", "16"]
    cores = [tuple(map(int, l.split())) for l in linhas[3:19]]
    assert len(cores) == 16 and all(len(c) == 3 and all(0 <= v <= 255 for v in c) for c in cores)
    assert cores[0] == (180, 180, 180)                   # índice 0 = transparente, como os outros itens
    # todo índice que o desenho do Arquivo Fama usa com cor continua com cor na paleta nova (nada vira preto)
    desenho = Image.open(REPO_ROOT / "graphics" / "items" / "icons" / "fame_checker.png")
    original = [tuple(map(int, l.split()))
                for l in _ler(REPO_ROOT / "graphics" / "items" / "icon_palettes" / "fame_checker.pal").split("\n")[3:19]]
    assert desenho.mode == "P"
    usados = set(desenho.tobytes()) - {0}
    assert usados and usados <= set(range(16))
    assert [i for i in usados if original[i] != (0, 0, 0) and cores[i] == (0, 0, 0)] == []


def test_dado_no_inicio_e_continuar():
    """Como o PC Portátil (POK-36): vem na bolsa no jogo novo e um save antigo o ganha ao CONTINUAR (inclusive pelo
    caminho do Quest Log). Bolso cheio: AddBagItem falha calado e o menu Start continua dando acesso."""
    fonte = _sem_comentarios(_ler(NEW_GAME_C))
    dar = _corpo(fonte, "GiveDexNavIfMissing")
    assert re.search(r"if \(!CheckBagHasItem\(ITEM_DEXNAV, 1\)\)\s*AddBagItem\(ITEM_DEXNAV, 1\);", dar), dar
    assert "void GiveDexNavIfMissing(void);" in _ler(NEW_GAME_H)
    novo = _corpo(fonte, "NewGameInitData")
    assert novo.index("GivePortablePcIfMissing();") < novo.index("GiveDexNavIfMissing();")
    assert novo.index("ClearBag();") < novo.index("GiveDexNavIfMissing();")
    mundo = _sem_comentarios(_ler(OVERWORLD_C))
    for funcao in ("CB2_ContinueSavedGame", "CB2_EnterFieldFromQuestLog"):
        corpo = _corpo(mundo, funcao)
        assert "GiveDexNavIfMissing();" in corpo, funcao
        assert corpo.index("GivePortablePcIfMissing();") < corpo.index("GiveDexNavIfMissing();")
