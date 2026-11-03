"""Seguidores (POK-48), Task 4: a opção no menu de Opções e os estados (sem emulador: lê o C como texto; o comportamento
no jogo é o cenário `seguidor`, test/esteira/scenarios/full_seguidor.py).

- `test_item_no_menu`: `MENUITEM_FOLLOWER` logo antes de `MENUITEM_CANCEL`, 2 valores em `sOptionMenuItemCounts`, nome
  "Seguidor" e valores "Sim"/"Não" (o valor 0 é Sim: `optionsFollowerOff` = 0);
- `test_le_e_grava_a_opcao`: a tela lê e grava `optionsFollowerOff`; o jogo novo começa com Sim;
- `test_janela_cabe_8_linhas`: a janela dos itens tem altura para as 8 linhas (13 px cada) dentro da moldura, a
  moldura cabe na tela (20 linhas de tiles) e o destaque do cursor (WIN0) cai na linha impressa;
- `test_estados`: bicicleta/surf apagam o seguidor e descer/sair da água o recria; Voar, Cavar, Teleporte, Corda de
  Fuga e Doce Aroma o apagam no início e o recriam no fim da chegada (ou da falha do Doce Aroma); a cura
  (`HealPlayerParty`) faz o refresh só com o campo rodando.
"""

import re

from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
LINE_PX = 13          # GetFontAttribute(FONT_NORMAL, FONTATTR_MAX_LETTER_HEIGHT) - 1 (src/new_menu_helpers.c)
LETTER_PX = 14
SCREEN_TILES = 20


def _ler(nome: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", (SRC / nome).read_text(encoding="utf-8"), flags=re.S)


def _funcao(texto: str, nome: str) -> str:
    m = re.search(rf"^\w[\w\s\*]*\b{nome}\s*\([^;{{]*\)\s*\{{", texto, re.M)
    assert m, f"função {nome} não encontrada"
    i, prof = m.end(), 1
    while prof:
        prof += {"{": 1, "}": -1}.get(texto[i], 0)
        i += 1
    return texto[m.end():i - 1]


def _menu_items(opt: str) -> list[str]:
    corpo = re.search(r"enum\s*\{\s*(MENUITEM_TEXTSPEED.*?)\};", opt, re.S).group(1)
    return [e.split("=")[0].strip() for e in corpo.split(",") if e.strip()]


def _texto(rotulo: str) -> str:
    m = re.search(rf"const u8 {rotulo}\[\] = _\(\"([^\"]*)\"\);", (SRC / "strings.c").read_text(encoding="utf-8"))
    assert m, rotulo
    return m.group(1)


def test_item_no_menu():
    opt = _ler("option_menu.c")
    itens = _menu_items(opt)
    assert itens[-3:] == ["MENUITEM_FOLLOWER", "MENUITEM_CANCEL", "MENUITEM_COUNT"], itens
    contagens = re.search(r"sOptionMenuItemCounts\[MENUITEM_COUNT\]\s*=\s*\{([^}]*)\}", opt).group(1)
    contagens = [int(c) for c in contagens.split(",")]
    assert len(contagens) == len(itens) - 1, contagens
    assert contagens[itens.index("MENUITEM_FOLLOWER")] == 2, contagens
    nome = re.search(r"\[MENUITEM_FOLLOWER\]\s*=\s*(\w+)", opt).group(1)
    assert _texto(nome).upper() == "SEGUIDOR", _texto(nome)
    valores = re.search(r"sFollowerOptions\[\]\s*=\s*\{([^}]*)\}", opt).group(1).split(",")
    valores = [_texto(v.strip()).upper() for v in valores if v.strip()]
    assert valores == ["SIM", "NÃO"], valores
    buf = _funcao(opt, "BufferOptionMenuString")
    assert re.search(r"case MENUITEM_FOLLOWER:\s*AddTextPrinterParameterized3\([^;]*sFollowerOptions\[", buf), buf


def test_le_e_grava_a_opcao():
    opt = _ler("option_menu.c")
    assert re.search(r"option\[MENUITEM_FOLLOWER\]\s*=\s*gSaveBlock2Ptr->optionsFollowerOff;",
                     _funcao(opt, "CB2_OptionsMenuFromStartMenu"))
    assert re.search(r"gSaveBlock2Ptr->optionsFollowerOff\s*=\s*sOptionMenuPtr->option\[MENUITEM_FOLLOWER\];",
                     _funcao(opt, "CloseAndSaveOptionMenu"))
    assert re.search(r"gSaveBlock2Ptr->optionsFollowerOff\s*=\s*(FALSE|0);", _funcao(_ler("new_game.c"),
                                                                                     "SetDefaultOptions"))


def _campos(bloco: str) -> dict[str, int]:
    return {k: int(v, 0) for k, v in re.findall(r"\.(\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)", bloco)}


def test_janela_cabe_8_linhas():
    opt = _ler("option_menu.c")
    janelas = re.search(r"sOptionMenuWinTemplates\[\]\s*=\s*\{(.*?)DUMMY_WIN_TEMPLATE", opt, re.S).group(1)
    blocos = [_campos(b) for b in re.findall(r"\{([^{}]*)\}", janelas)]
    itens = next(b for b in blocos if b["bg"] == 0)
    n = len(_menu_items(opt)) - 1
    m = re.search(r"\(u8\)\(\(i \* \(GetFontAttribute\(FONT_NORMAL, FONTATTR_MAX_LETTER_HEIGHT\)\)\) \+ (\w+)\) - i",
                  _funcao(opt, "LoadOptionMenuItemNames"))
    assert m, "LoadOptionMenuItemNames: y da linha i mudou de forma"
    y0 = int(re.search(rf"#define {m.group(1)}\s+(\d+)", opt).group(1)) if not m.group(1).isdigit() \
        else int(m.group(1))
    ultima = y0 + (n - 1) * LINE_PX + LETTER_PX
    assert ultima <= itens["height"] * 8, f"{n} linhas até o px {ultima}, janela de {itens['height'] * 8} px"
    assert itens["tilemapTop"] + itens["height"] <= SCREEN_TILES - 1, "sem linha para a borda de baixo da moldura"
    # a borda de baixo da moldura (DrawOptionMenuBg) fica logo abaixo da janela, e a de cima logo acima
    bg = _funcao(opt, "DrawOptionMenuBg")
    baixo = int(re.search(r"FillBgTilemapBufferRect\(1, 0x1B1, 2, (\w+),", bg).group(1), 0)
    cima = int(re.search(r"FillBgTilemapBufferRect\(1, 0x1AB, 2, (\w+),", bg).group(1), 0)
    assert baixo == itens["tilemapTop"] + itens["height"] and cima < itens["tilemapTop"], (cima, baixo, itens)
    # o destaque do cursor (WIN0V) começa no px da linha impressa
    sel = _funcao(opt, "UpdateSettingSelectionDisplay")
    base = re.search(r"y = selection \* \(maxLetterHeight - 1\) \+ (\w+);", sel).group(1)
    assert int(base, 0) == itens["tilemapTop"] * 8 + y0, (base, itens, y0)
    # as 3 janelas e as 2 molduras dividem os tiles do charBase 1 (sOptionMenuBgTemplates): nada se sobrepõe (com a
    # janela de 14 tiles, a barra de controles em 0x16e saía com lixo)
    faixas = [(b["baseBlock"], b["baseBlock"] + b["width"] * b["height"]) for b in blocos]
    for inicio in (0x1AA, 0x1B3):        # LoadBgTiles(... 0x120, 0x1AA) e LoadStdWindowGfxOnBg(1, 0x1B3, ...): 9 tiles
        faixas.append((inicio, inicio + 0x120 // 32))
    faixas.sort()
    for (a0, a1), (b0, b1) in zip(faixas, faixas[1:]):
        assert a1 <= b0, f"tiles sobrepostos: {a0:#x}-{a1 - 1:#x} e {b0:#x}-{b1 - 1:#x}"
    valor = _funcao(opt, "BufferOptionMenuString")
    vy = re.search(r"y = \(\(GetFontAttribute\(FONT_NORMAL, FONTATTR_MAX_LETTER_HEIGHT\) - 1\) \* selection\) \+ (\w+);",
                   valor).group(1)
    assert vy == m.group(1), (vy, m.group(1))


def test_estados():
    fpa = _ler("field_player_avatar.c")
    for nome in ("PlayerAvatarTransition_Bike", "PlayerAvatarTransition_Surfing"):
        assert "Follower_Remove();" in _funcao(fpa, nome), nome
    assert "Follower_Spawn();" in _funcao(fpa, "Task_WaitStopSurfing")
    bike = _funcao(_ler("bike.c"), "GetOnOffBike")
    desce = bike[:bike.index("else")]
    assert "Follower_Spawn();" in desce, bike
    fe = _ler("field_effect.c")
    for nome in ("UseSurfEffect_1", "FieldCallback_UseFly", "FieldCallback_FlyIntoMap", "StartEscapeRopeFieldEffect",
                 "FieldCallback_EscapeRopeExit", "TeleportFieldEffectTask1", "FieldCallback_TeleportIn"):
        assert "Follower_Remove();" in _funcao(fe, nome), nome
    for nome in ("Task_FlyIntoMap", "EscapeRopeWarpInEffect_Spin", "TeleportInFieldEffectTask3"):
        corpo = _funcao(fe, nome)
        fim = corpo.index("UnlockPlayerFieldControls();")
        assert "Follower_Spawn();" in corpo[fim:], nome
    assert "Follower_Remove();" in _funcao(_ler("fldeff_dig.c"), "FldEff_UseDig")
    assert "Follower_Remove();" in _funcao(_ler("fldeff_teleport.c"), "FldEff_UseTeleport")
    doce = _ler("fldeff_sweetscent.c")
    assert "Follower_Remove();" in _funcao(doce, "FldEff_SweetScent")
    assert "Follower_Spawn();" in _funcao(doce, "FailSweetScentEncounter")
    cura = _funcao(_ler("script_pokemon_util.c"), "HealPlayerParty")
    assert re.search(r"if \(Overworld_IsRunning\(\)\)\s*Follower_Refresh\(\);", cura), cura
