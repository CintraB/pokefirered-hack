"""Hack 7 sem emulador: o relógio do jogo (períodos, constantes do C, campo no save, tick).

O espelho Python (esteira/dia_noite.py) tem de seguir as regras do design: manhã 04–10,
tarde 10–17, entardecer 17–20, noite 20–04; 150 quadros por minuto do jogo; começo 08:00.
"""

import re

from esteira import breeding as br
from esteira import dia_noite as dn
from esteira.scenarios import REPO_ROOT

GLOBAL_H = (REPO_ROOT / "include" / "global.h").read_text(encoding="utf-8")
PLAY_TIME_C = (REPO_ROOT / "src" / "play_time.c").read_text(encoding="utf-8")


def test_periodos_nos_limites():
    casos = {
        239: dn.NIGHT, 240: dn.MORNING, 599: dn.MORNING, 600: dn.AFTERNOON,
        1019: dn.AFTERNOON, 1020: dn.EVENING, 1199: dn.EVENING, 1200: dn.NIGHT, 1439: dn.NIGHT,
    }
    for minuto, periodo in casos.items():
        assert dn.period_at(minuto) == periodo, (minuto, dn.PERIOD_NAMES[dn.period_at(minuto)])


def test_constantes_do_c_batem():
    defines = br.header_defines(REPO_ROOT, "day_night.h")
    assert defines["GAME_CLOCK_FRAMES_PER_MINUTE"] == dn.FRAMES_PER_MINUTE == 150
    assert defines["MINUTES_PER_DAY"] == 1440
    assert (defines["MORNING_START_HOUR"], defines["AFTERNOON_START_HOUR"],
            defines["EVENING_START_HOUR"], defines["NIGHT_START_HOUR"]) == (4, 10, 17, 20)
    assert (defines["TIME_MORNING"], defines["TIME_AFTERNOON"], defines["TIME_EVENING"],
            defines["TIME_NIGHT"], defines["TIME_PERIOD_COUNT"]) == (
        dn.MORNING, dn.AFTERNOON, dn.EVENING, dn.NIGHT, 4)
    text = (REPO_ROOT / "include" / "constants" / "day_night.h").read_text(encoding="utf-8")
    m = re.search(r"^#define\s+GAME_CLOCK_START_MINUTE\s+\((\d+)\s*\*\s*(\d+)\)", text, re.M)
    assert m, "GAME_CLOCK_START_MINUTE não está no formato (H * 60)"
    assert int(m.group(1)) * int(m.group(2)) == dn.START_MINUTE == 480


def test_save_campo_no_filler():
    assert re.search(r"/\*0x090\*/\s*u32 gameClockFrames;", GLOBAL_H)
    assert re.search(r"/\*0x094\*/\s*u8 filler_94\[0x4\];", GLOBAL_H)
    assert re.search(r"/\*0x098\*/\s*struct Time localTimeOffset;", GLOBAL_H)
    assert "filler_90" not in GLOBAL_H


def test_tick_no_play_time():
    """O relógio anda com o contador de tempo de jogo ligado (RUNNING) e também depois que ele
    trava em 999:59 (MAXED_OUT): só para em STOPPED."""
    corpo = re.search(r"void PlayTimeCounter_Update\(void\)\n\{(.*?)\n\}", PLAY_TIME_C, re.S)
    assert corpo, "PlayTimeCounter_Update não encontrado"
    texto = corpo.group(1)
    assert texto.count("DayNight_Tick();") == 1
    assert re.search(r"if \(sPlayTimeCounterState != STOPPED\)\s*\{?\s*DayNight_Tick\(\);", texto), (
        "DayNight_Tick() tem de estar sob `if (sPlayTimeCounterState != STOPPED)`")
    ramo = re.search(r"if \(sPlayTimeCounterState == RUNNING\)\s*\{(.*)\}", texto, re.S)
    assert ramo, "ramo RUNNING não encontrado"
    assert "DayNight_Tick();" not in ramo.group(1)


def test_jogo_novo_zera_o_relogio():
    """Jogo novo por cima de um save existente não herda o relógio: NewGameInitData zera junto
    com o tempo de jogo, e DayNight_Reset volta a 08:00 do dia 0 (gameClockFrames = 0)."""
    new_game = (REPO_ROOT / "src" / "new_game.c").read_text(encoding="utf-8")
    corpo = re.search(r"void NewGameInitData\(void\)\n\{(.*?)\n\}", new_game, re.S)
    assert corpo, "NewGameInitData não encontrado"
    assert "PlayTimeCounter_Reset();" in corpo.group(1)
    assert "DayNight_Reset();" in corpo.group(1)
    day_night = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
    reset = re.search(r"void DayNight_Reset\(void\)\n\{(.*?)\n\}", day_night, re.S)
    assert reset, "DayNight_Reset não encontrado"
    assert re.fullmatch(r"\s*gSaveBlock2Ptr->gameClockFrames = 0;\s*", reset.group(1))


def test_cenario_relogio_registrado():
    from esteira import __main__ as cli
    spec = next(s for s in cli.FULL_SCENARIOS if s.name == "relogio")
    assert (spec.rom, spec.save_from) == (cli.TEST, "captura")
    assert spec.run.__name__ == "run_full_clock"
    assert "relogio" in cli.WATCH_FULL_SCENARIOS


# ---- Hack 7 frente A: hora no menu Start e aviso de troca de período -------------------------

def _strings_c() -> str:
    return (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")


def _textos(nome: str) -> list[str]:
    tabela = re.search(re.escape(nome) + r"\[TIME_PERIOD_COUNT\]\s*=\s*\{", _strings_c())
    assert tabela, f"{nome} não encontrado em src/strings.c"
    prefixo = "sPeriodName" if nome.endswith("Name") else "sPeriodStart"
    textos = re.findall(prefixo + r'_\w+\[\]\s*=\s*_\("([^"]*)"\)', _strings_c())
    assert len(textos) == 4, textos
    return textos


def _largura(texto: str) -> int:
    from esteira.charmap import Charmap
    from esteira.font_render import glyph_widths
    larguras = glyph_widths(REPO_ROOT, "sFontNormalLatinGlyphWidths")
    return sum(larguras[c] for c in Charmap.load(str(REPO_ROOT)).encode(texto))


def test_textos_dia_noite_cabem():
    assert _textos("gText_DayNight_PeriodName") == ["Manhã", "Tarde", "Entardecer", "Noite"]
    assert _textos("gText_DayNight_PeriodStart") == [
        "Amanheceu.", "O sol está alto.", "O sol se põe.", "Anoiteceu."]
    for texto in _textos("gText_DayNight_PeriodStart"):
        assert _largura(texto) <= 112, (texto, _largura(texto))
    for nome in _textos("gText_DayNight_PeriodName"):
        assert _largura("23:59 " + nome) <= 13 * 8 - 8, (nome, _largura("23:59 " + nome))


def test_relogio_destruido_com_safari():
    texto = (REPO_ROOT / "src" / "start_menu.c").read_text(encoding="utf-8")
    chamadas = [m.start() for m in re.finditer(r"^\s+DestroySafariZoneStatsWindow\(\);", texto, re.M)]
    assert chamadas, "nenhuma chamada de DestroySafariZoneStatsWindow"
    for pos in chamadas:
        resto = texto[pos:].split("\n")
        seguinte = resto[1].strip()
        assert seguinte == "DestroyStartMenuClockWindow();", (
            f"chamada em {texto[:pos].count(chr(10)) + 2}: falta DestroyStartMenuClockWindow() logo depois")
    # mais duas: ao entrar no fluxo de salvar (a Safari não tem SALVAR) e no callback do menu de link; sem elas a janela
    # vaza no SAVE confirmado e é recriada por cima no cancelado
    assert texto.count("DestroyStartMenuClockWindow();") == len(chamadas) + 2
    save1 = re.search(r"static bool8 StartCB_Save1\(void\)\n\{\n(.*?)\n\}", texto, re.S)
    assert save1, "StartCB_Save1 não encontrado"
    corpo = save1.group(1)
    assert corpo.index("DestroyStartMenuClockWindow();") < corpo.index("StartMenu_PrepareForSave();")
    draw = re.search(r"static void DrawStartMenuClockWindow\(void\)\n\{\n(.*?)\n\}", texto, re.S).group(1)
    assert draw.index("if (sClockWindowOpen)") < draw.index("AddWindow(")
    assert re.search(r"\.tilemapTop = 1,\s*\.width = 13,\s*\.height = 2,\s*\.paletteNum = 15,\s*"
                     r"\.baseBlock = 0x030", texto)


def test_aviso_so_com_jogador_livre():
    c = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
    corpo = re.search(r"void DayNight_FieldUpdate\(void\)\n\{(.*?)\n\}", c, re.S)
    assert corpo, "DayNight_FieldUpdate não encontrado"
    for item in ("ArePlayerFieldControlsLocked", "ScriptContext_IsEnabled", "gPaletteFade.active",
                 "ShowFieldMessagePopup", "DayNight_OnPeriodChange"):
        assert item in corpo.group(1), item
    ow = (REPO_ROOT / "src" / "overworld.c").read_text(encoding="utf-8")
    basic = re.search(r"static void OverworldBasic\(void\)\n\{(.*?)\n\}", ow, re.S).group(1)
    assert "DayNight_FieldUpdate();" in basic


def test_relogio_destruido_antes_de_limpar_as_janelas():
    """CleanupOverworldWindowsAndTilemaps apaga a tabela de janelas: toda chamada em start_menu.c
    tem de ser precedida (nas 6 linhas anteriores) da destruição da janela da hora, senão
    sClockWindowOpen fica verdadeiro com o id velho."""
    linhas = (REPO_ROOT / "src" / "start_menu.c").read_text(encoding="utf-8").split("\n")
    chamadas = [i for i, l in enumerate(linhas) if l.strip() == "CleanupOverworldWindowsAndTilemaps();"]
    assert len(chamadas) >= 6, chamadas
    for i in chamadas:
        antes = "\n".join(linhas[max(0, i - 6):i])
        assert "DestroyStartMenuClockWindow();" in antes, (
            f"start_menu.c:{i + 1}: CleanupOverworldWindowsAndTilemaps sem DestroyStartMenuClockWindow antes")


# ---- Hack 7 frente A: tom de cor por período (Task 3) ----------------------------------------

def _corpo_c(arquivo: str, assinatura: str) -> str:
    texto = (REPO_ROOT / "src" / arquivo).read_text(encoding="utf-8")
    corpo = re.search(re.escape(assinatura) + r"\n\{\n(.*?)\n\}", texto, re.S)
    assert corpo, f"{assinatura} não encontrado em src/{arquivo}"
    return corpo.group(1)


def test_tom_nos_periodos():
    assert dn.tint_at(12 * 60) == (256, 256, 256)
    assert dn.tint_at(22 * 60) == (144, 152, 224)
    assert dn.tint_at(5 * 60) == (256, 240, 224)
    assert dn.tint_at(18 * 60) == (256, 200, 168)


def test_tom_interpola():
    tarde, entardecer = dn.PERIOD_TINTS[dn.AFTERNOON], dn.PERIOD_TINTS[dn.EVENING]
    assert dn.tint_at(16 * 60) == tarde          # a transição parte do tom do período
    meio = dn.tint_at(16 * 60 + 30)
    for t, m, e in zip(tarde, meio, entardecer):
        assert min(t, e) <= m <= max(t, e), (tarde, meio, entardecer)
        if t != e:
            assert m not in (t, e), (tarde, meio, entardecer)
    fim = dn.tint_at(16 * 60 + 59)
    assert fim != entardecer
    for t, f, e in zip(tarde, fim, entardecer):
        passo = -(-abs(t - e) // 60)              # um minuto de interpolação, arredondado para cima
        assert abs(f - e) <= passo, (fim, entardecer)
    assert dn.tint_at(17 * 60) == entardecer


def test_tom_contínuo_nos_quatro_limites():
    """Nenhum salto maior que um minuto de interpolação em volta do dia inteiro."""
    for minuto in range(dn.MINUTES_PER_DAY):
        a, b = dn.tint_at(minuto), dn.tint_at(minuto + 1)
        for x, y in zip(a, b):
            assert abs(x - y) <= 2, (minuto, a, b)
    for hora in (3, 9, 16, 19):
        assert dn.tint_at(hora * 60) == dn.PERIOD_TINTS[dn.period_at(hora * 60)]
        assert dn.tint_at(hora * 60 + 60) == dn.PERIOD_TINTS[dn.period_at(hora * 60 + 60)]


def test_tom_da_cor():
    branco = 0x7FFF
    assert dn.tint_color(branco, (256, 256, 256)) == branco
    assert dn.tint_color(branco, (144, 152, 224)) == (27 << 10 | 18 << 5 | 17)
    assert dn.tint_color(0x8000 | branco, (256, 256, 256)) == 0x8000 | branco


def test_coeficientes_do_c_batem():
    texto = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
    tabela = re.search(r"sPeriodTints\[TIME_PERIOD_COUNT\]\s*=\s*\{(.*?)\};", texto, re.S)
    assert tabela, "sPeriodTints não encontrado em src/day_night.c"
    achados = dict(re.findall(r"\[(TIME_\w+)\]\s*=\s*\{\s*(\d+,\s*\d+,\s*\d+)\s*\}", tabela.group(1)))
    nomes = {"TIME_MORNING": dn.MORNING, "TIME_AFTERNOON": dn.AFTERNOON,
             "TIME_EVENING": dn.EVENING, "TIME_NIGHT": dn.NIGHT}
    assert {nomes[k]: tuple(int(x) for x in v.split(",")) for k, v in achados.items()} == dn.PERIOD_TINTS


TINT_POINTS = (
    ("fieldmap.c", "static void ApplyGlobalTintToPaletteEntries(u16 offset, u16 size)"),
    ("fieldmap.c", "void ApplyGlobalTintToPaletteSlot(u8 slot, u8 count)"),
    ("field_effect.c", "void ApplyGlobalFieldPaletteTint(u8 paletteIdx)"),
)


def test_tint_antes_do_quest_log():
    """Nos três pontos de tint, o tom do dia/noite vai no Unfaded antes do switch do Quest Log
    (compõe com cinza/sépia e com o backup) e a cópia para o Faded acontece mesmo sem tint do
    Quest Log."""
    for arquivo, assinatura in TINT_POINTS:
        corpo = _corpo_c(arquivo, assinatura)
        pos = corpo.find("switch (gGlobalFieldTintMode)")
        assert pos > 0, f"{assinatura}: switch (gGlobalFieldTintMode) não encontrado"
        antes = corpo[:pos]
        assert "DayNight_ShouldTintCurrentMap()" in antes, assinatura
        assert "DayNight_TintPaletteBuffer(&gPlttBufferUnfaded[" in antes, assinatura
        assert not re.search(r"case (QL_TINT_NONE|0):\s*return;", corpo), (
            f"{assinatura}: sem tint do Quest Log ainda tem de copiar o tom para o Faded")


def test_tom_so_nos_pontos_de_tint():
    """Só os três pontos de tint (que rodam logo depois de carregar a paleta do ROM) tingem: um
    buffer já tingido nunca é tingido de novo."""
    chamadas = []
    for arquivo in sorted((REPO_ROOT / "src").glob("*.c")):
        texto = arquivo.read_text(encoding="utf-8", errors="replace")
        chamadas += [arquivo.name for _ in re.finditer(r"DayNight_TintPaletteBuffer\(&", texto)]
    assert sorted(chamadas) == ["field_effect.c", "fieldmap.c", "fieldmap.c"], chamadas


def test_loadpal_tinge_so_paleta_nova():
    """FieldEffectScript_LoadPal (Poké Bola da transição de batalha) tingia a paleta que JÁ
    existia: 5 bolas = tom aplicado 4 vezes. Agora tinge só a recém-carregada, como LoadFadedPal."""
    corpo = _corpo_c("field_effect.c", "static void FieldEffectScript_LoadPal(const u8 **script)")
    assert "if (idx == 0xFF)" in corpo and "if (idx != 0xFF)" not in corpo


def test_retinge_recarregando_do_rom():
    retint = _corpo_c("day_night.c", "static void TryRetintField(void)")
    for item in ("gPaletteFade.active", "WEATHER_PAL_STATE_IDLE", "ArePlayerFieldControlsLocked()",
                 "DayNight_ShouldTintCurrentMap()", "gGlobalFieldTintMode != QL_TINT_NONE",
                 "LoadMapTilesetPalettes(gMapHeader.mapLayout);", "ApplyWeatherGammaShiftToPal(",
                 "ReloadObjectEventPalettes();", "UpdateSpritePaletteWithWeather(",
                 "LoadCustomWeatherSpritePalette("):
        assert item in retint, item
    assert "DayNight_TintPaletteBuffer" not in retint
    update = _corpo_c("day_night.c", "void DayNight_FieldUpdate(void)")
    assert update.index("TryRetintField();") < update.index("ShowFieldMessagePopup")
    reload = _corpo_c("event_object_movement.c", "void ReloadObjectEventPalettes(void)")
    assert "PatchObjectPaletteRange(" in reload and "LoadSpecialObjectReflectionPalette(" in reload
    assert "FreeAndReserveObjectSpritePalettes" not in reload   # não solta paletas em uso


def test_paleta_do_clima_customizada_tingida():
    corpo = _corpo_c("field_weather.c", "void LoadCustomWeatherSpritePalette(const u16 *palette)")
    assert corpo.index("LoadPalette(") < corpo.index("ApplyGlobalFieldPaletteTint(") < corpo.index(
        "UpdateSpritePaletteWithWeather(")


def test_fame_checker_sem_tom():
    """O Fame Checker monta os retratos com InitObjectEventPalettes fora do campo: sem tom."""
    corpo = _corpo_c("fame_checker.c", "static void FCSetup_ResetTasksAndSpriteResources(void)")
    linhas = [l.strip() for l in corpo.split("\n")]
    i = linhas.index("InitObjectEventPalettes(0);")
    assert linhas[i - 1].startswith("DayNight_SuspendTint(TRUE);")
    assert linhas[i + 1].startswith("DayNight_SuspendTint(FALSE);")


def test_tom_de_referencia_so_na_carga_completa():
    """sAppliedTint (o tom que o TryRetintField compara) só muda numa carga completa do campo
    (paletas do tileset primário) ou no próprio retinge. Se toda paleta tingida o atualizasse, uma
    paleta nova tingida com o retinge bloqueado (árvore cortada, NPC com paleta especial) deixaria
    o BG e os OBJ 0–9 presos no tom antigo."""
    tint = _corpo_c("day_night.c", "void DayNight_TintPaletteBuffer(u16 *pal, u16 count)")
    assert "sAppliedTint" not in tint
    record = _corpo_c("day_night.c", "void DayNight_RecordFieldTint(void)")
    assert "sAppliedTint" in record
    texto = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
    # gravado só em DayNight_RecordFieldTint (pelo ponteiro); fora dele, só a declaração e leituras
    assert len(re.findall(r"sAppliedTint\s*=[^=]", texto)) == 1, "sAppliedTint só na declaração"
    assert texto.count("&sAppliedTint") == record.count("&sAppliedTint") == 1
    chamadas = []
    for arquivo in sorted((REPO_ROOT / "src").glob("*.c")):
        corpo = arquivo.read_text(encoding="utf-8", errors="replace")
        chamadas += [arquivo.name for _ in re.finditer(r"DayNight_RecordFieldTint\(\);", corpo)]
    assert sorted(chamadas) == ["day_night.c", "fieldmap.c"], chamadas
    assert "DayNight_RecordFieldTint();" in _corpo_c("day_night.c", "static void TryRetintField(void)")
    entries = _corpo_c("fieldmap.c", "static void ApplyGlobalTintToPaletteEntries(u16 offset, u16 size)")
    assert re.search(r"if \(offset < BG_PLTT_ID\(NUM_PALS_IN_PRIMARY\)\)\s*DayNight_RecordFieldTint\(\);", entries), (
        "o tom de referência tem de ser gravado só na carga do tileset primário")


def test_tint_de_objeto_sem_slot_nao_escreve_fora():
    """ApplyGlobalFieldPaletteTint com paletteIdx 0xFF (tabela de paletas cheia) não pode mexer no
    buffer — nem o tom nem o switch do Quest Log."""
    corpo = _corpo_c("field_effect.c", "void ApplyGlobalFieldPaletteTint(u8 paletteIdx)")
    guarda = re.search(r"if \(paletteIdx >= 16\)\s*return;", corpo)
    assert guarda and guarda.start() < corpo.index("DayNight_ShouldTintCurrentMap()")
    assert corpo.index("DayNight_ShouldTintCurrentMap()") < corpo.index("switch (gGlobalFieldTintMode)")
