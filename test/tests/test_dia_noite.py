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
    for assinatura in ("void LoadCustomWeatherSpritePalette(const u16 *palette)",
                       "void RestoreDefaultWeatherSpritePalette(void)"):   # a padrão, da frente E
        corpo = _corpo_c("field_weather.c", assinatura)
        assert corpo.index("LoadPalette(") < corpo.index("ApplyGlobalFieldPaletteTint(") < corpo.index(
            "UpdateSpritePaletteWithWeather("), assinatura
    # o retinge volta a paleta padrão pela função da frente E, sem duplicá-la
    retint = _corpo_c("day_night.c", "static void TryRetintField(void)")
    assert "RestoreDefaultWeatherSpritePalette();" in retint
    assert "gDefaultWeatherSpritePalette" not in retint


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


# ---- Hack 7 frente A: clima dinâmico por região (Task 4) ----------------------------------------

WEATHER_TABLE_H = REPO_ROOT / "src" / "data" / "day_night_weather.h"


def test_pesos_somam_100():
    assert sorted(dn.REGION_WEIGHTS) == list(range(1, dn.REGION_COUNT))   # todas menos NONE
    for region, periods in dn.REGION_WEIGHTS.items():
        assert sorted(periods) == [dn.MORNING, dn.AFTERNOON, dn.EVENING, dn.NIGHT], region
        for period, weights in periods.items():
            assert sum(w for _, w in weights) == 100, (dn.REGION_NAMES[region], period, weights)
            assert all(w > 0 for _, w in weights)
            assert len({c for c, _ in weights}) == len(weights), (region, period)


def test_drought_nunca():
    """WEATHER_DROUGHT trava o jogo no FRLG (pkfr-mundo): nunca sorteado."""
    for periods in dn.REGION_WEIGHTS.values():
        for weights in periods.values():
            assert dn.WEATHER_DROUGHT not in [c for c, _ in weights]
    assert "WEATHER_DROUGHT" not in WEATHER_TABLE_H.read_text(encoding="utf-8")


def test_hash_conhecido():
    """Valores calculados à parte com o lowbias32 do brief (seed = dia * 4 + período)."""
    assert dn.weather_hash(0 * 4 + dn.MORNING, dn.REGION_INLAND) == 0x01FCE552
    assert dn.weather_hash(7 * 4 + dn.MORNING, dn.REGION_SNOW) == 0xBB807911
    assert dn.weather_hash(123 * 4 + dn.AFTERNOON, dn.REGION_SAND) == 0xD9BE7714
    # 0x01FCE552 % 100 = 94 → INLAND manhã: NONE 0–69, FOG_H 70–84, RAIN 85–99 (só o hash: o dia 0
    # é sempre sem clima, test_dia_zero_sem_clima)
    assert dn.roll_from_hash(dn.REGION_INLAND, dn.MORNING, 0x01FCE552) == dn.WEATHER_RAIN
    # 93 → SNOW 0–59, NONE 60–89, FOG_H 90–99
    assert dn.roll_weather(dn.REGION_SNOW, 7, dn.MORNING) == dn.WEATHER_FOG_HORIZONTAL
    # 96 → SAND tarde: NONE 0–49, SANDSTORM 50–99
    assert dn.roll_weather(dn.REGION_SAND, 123, dn.AFTERNOON) == dn.WEATHER_SANDSTORM
    # 0xD2391570 % 100 = 0 → primeiro da tabela
    assert dn.roll_weather(dn.REGION_COAST, 1000, dn.NIGHT) == dn.WEATHER_NONE
    assert dn.roll_weather(dn.REGION_NONE, 5, dn.MORNING) == dn.WEATHER_NONE


def test_dia_zero_sem_clima():
    """Regra 15: o dia 0 do clima (08:00 do jogo novo até 04:00 do dia 1) nunca sorteia clima, em
    nenhuma região nem período — senão todo jogo novo começaria com chuva em Pallet/Rota 1."""
    for region in range(dn.REGION_COUNT):
        for period in range(4):
            assert dn.roll_weather(region, 0, period) == dn.WEATHER_NONE, (region, period)
    for minute in (dn.START_MINUTE, 12 * 60, 22 * 60):
        assert dn.map_weather(dn.WEATHER_SUNNY, dn.REGION_INLAND, True, 0, minute) == dn.WEATHER_SUNNY
    assert dn.weather_day(1, 3 * 60) == 0          # 03:00 do dia 1 ainda é o dia 0 do clima
    assert dn.roll_weather(dn.REGION_INLAND, 1, dn.MORNING) == dn.roll_from_hash(
        dn.REGION_INLAND, dn.MORNING, dn.weather_hash(1 * 4 + dn.MORNING, dn.REGION_INLAND))
    corpo = _corpo_c("day_night.c", "u8 DayNight_RollWeather(u8 region, u32 day, u8 period)")
    assert re.search(r"day == 0\)\s*\n?\s*return WEATHER_NONE;", corpo) or "|| day == 0)" in corpo, corpo


def test_distribuicao_do_sorteio():
    """40 000 dias (a partir do 1; o 0 é sempre sem clima) por região × período: cada clima a ±4σ
    do peso, e nenhum fora da tabela."""
    n = 40000
    for region, periods in dn.REGION_WEIGHTS.items():
        for period, weights in periods.items():
            counts: dict[int, int] = {}
            for day in range(1, n + 1):
                w = dn.roll_weather(region, day, period)
                counts[w] = counts.get(w, 0) + 1
            assert set(counts) <= {c for c, _ in weights}, (region, period, counts)
            for weather, weight in weights:
                p = weight / 100
                sigma = (n * p * (1 - p)) ** 0.5
                got = counts.get(weather, 0)
                assert abs(got - n * p) <= 4 * sigma, (
                    f"{dn.REGION_NAMES[region]} {dn.PERIOD_NAMES[period]} "
                    f"{dn.WEATHER_BY_ID[weather]}: {got} de {n}, esperava {n * p:.0f} ± {4 * sigma:.0f}")


def test_dia_do_clima_comeca_as_4():
    """A noite inteira (20h–04h) é um sorteio só: o dia do clima vira às 04:00, não à meia-noite."""
    assert dn.weather_day(5, 3 * 60 + 59) == 4
    assert dn.weather_day(5, 4 * 60) == 5
    assert dn.weather_day(4, 23 * 60) == dn.weather_day(5, 1 * 60) == 4
    assert dn.weather_day(0, dn.START_MINUTE) == 0


def test_clima_do_mapa():
    sunny, shade = dn.WEATHER_SUNNY, dn.WEATHER_SHADE
    dia = next(d for d in range(1000) if dn.roll_weather(dn.REGION_SNOW, d, dn.MORNING) == dn.WEATHER_SNOW)
    assert dn.map_weather(sunny, dn.REGION_SNOW, True, dia, 6 * 60) == dn.WEATHER_SNOW
    assert dn.map_weather(dn.WEATHER_NONE, dn.REGION_SNOW, False, dia, 6 * 60) == dn.WEATHER_NONE  # interior
    assert dn.map_weather(shade, dn.REGION_SNOW, True, dia, 6 * 60) == shade                     # header fixo
    assert dn.map_weather(sunny, dn.REGION_NONE, True, dia, 6 * 60) == sunny
    calmo = next(d for d in range(1000) if dn.roll_weather(dn.REGION_SNOW, d, dn.MORNING) == dn.WEATHER_NONE)
    assert dn.map_weather(sunny, dn.REGION_SNOW, True, calmo, 6 * 60) == sunny                   # sorteio NONE


def _c_weather_table() -> dict:
    texto = WEATHER_TABLE_H.read_text(encoding="utf-8")
    tabela = {}
    for nome, corpo in re.findall(r"\[WEATHER_REGION_(\w+)\]\s*=\s*\{(.*?)\n    \},", texto, re.S):
        periodos = {}
        for periodo, pares in re.findall(r"\[TIME_(\w+)\]\s*=\s*\{(.*?)\},(?:\n|$)", corpo, re.S):
            periodos[getattr(dn, periodo)] = tuple(
                (dn.WEATHER_IDS[c], int(p)) for c, p in re.findall(r"\{(WEATHER_\w+),\s*(\d+)\}", pares))
        tabela[dn.REGION_NAMES.index(nome)] = periodos
    return tabela


def test_tabela_c_igual_python():
    assert _c_weather_table() == dn.REGION_WEIGHTS


def test_regioes_do_c():
    """DayNight_GetWeatherRegion: os MAPSEC de cada `return WEATHER_REGION_X;` e a regra de
    Kanto (INLAND) e das Sevii (SEVII) depois do switch."""
    corpo = _corpo_c("day_night.c", "u8 DayNight_GetWeatherRegion(u8 mapsec)")
    achados = {}
    for casos, regiao in re.findall(r"((?:\s*case MAPSEC_\w+:)+)\s*return WEATHER_REGION_(\w+);", corpo):
        achados[dn.REGION_NAMES.index(regiao)] = tuple(re.findall(r"MAPSEC_\w+", casos))
    assert {r: sorted(m) for r, m in achados.items()} == {r: sorted(m) for r, m in dn.REGION_MAPSECS.items()}
    resto = corpo[corpo.rindex("}"):]
    assert "SEVII_MAPSEC_START" in resto and "WEATHER_REGION_SEVII" in resto
    assert "KANTO_MAPSEC_START" in resto and "WEATHER_REGION_INLAND" in resto
    constantes = (REPO_ROOT / "include" / "constants" / "day_night.h").read_text(encoding="utf-8")
    for valor, nome in enumerate(dn.REGION_NAMES):
        assert re.search(rf"#define WEATHER_REGION_{nome}\s+{valor}\b", constantes), nome
    secoes = (REPO_ROOT / "include" / "constants" / "region_map_sections.h").read_text(encoding="utf-8")
    for mapsecs in dn.REGION_MAPSECS.values():
        for m in mapsecs:
            assert re.search(rf"\b{m},", secoes), m


def test_clima_salvo_pelo_sorteio():
    corpo = _corpo_c("field_weather_util.c", "void SetSavedWeatherFromCurrMapHeader(void)")
    assert "TranslateWeatherNum(DayNight_GetMapWeather(gMapHeader.weather))" in corpo
    troca = _corpo_c("day_night.c", "void DayNight_OnPeriodChange(void)")
    assert "SetWeather(" in troca and "DayNight_GetMapWeather(gMapHeader.weather)" in troca
    assert "GetRolledWeatherRegion(gMapHeader.weather) == WEATHER_REGION_NONE" in troca
    mapa = _corpo_c("day_night.c", "u8 DayNight_GetMapWeather(u8 headerWeather)")
    assert "GetRolledWeatherRegion(headerWeather)" in mapa and "WEATHER_REGION_NONE" in mapa
    rola = _corpo_c("day_night.c", "static u8 GetRolledWeatherRegion(u8 headerWeather)")
    assert "IsMapTypeOutdoors(gMapHeader.mapType)" in rola
    for w in ("WEATHER_NONE", "WEATHER_SUNNY", "WEATHER_SUNNY_CLOUDS",
              "DayNight_GetWeatherRegion(gMapHeader.regionMapSectionId)"):
        assert w in rola, w


def test_clima_atualizado_na_volta_ao_campo():
    """Na volta de batalha/bolsa (ResumeMap usa o clima salvo e o período visto é esquecido), o
    clima é conferido uma vez quando o jogador fica livre."""
    esquece = _corpo_c("day_night.c", "void DayNight_ForgetSeenPeriod(void)")
    assert "sMapWeatherChecked = FALSE;" in esquece
    volta = _corpo_c("day_night.c", "static void TryUpdateWeatherAfterEntry(void)")
    for item in ("ArePlayerFieldControlsLocked()", "ScriptContext_IsEnabled()", "gPaletteFade.active",
                 "sMapWeatherChecked = TRUE;", "DayNight_OnPeriodChange();"):
        assert item in volta, item
    update = _corpo_c("day_night.c", "void DayNight_FieldUpdate(void)")
    assert update.index("TryUpdateWeatherAfterEntry();") < update.index("if (sSeenPeriod == PERIOD_NONE)")


def test_cenario_clima_registrado():
    from esteira import __main__ as cli
    spec = {s.name: s for s in cli.FULL_SCENARIOS}["clima"]
    assert (spec.rom, spec.save_from) == (cli.TEST, "captura")
    assert "clima" in cli.WATCH_FULL_SCENARIOS


# --- Task 5: neve do mapa vira granizo na batalha ----------------------------------------------

def _src(caminho: str) -> str:
    return (REPO_ROOT / caminho).read_text(encoding="utf-8")


def test_granizo_permanente():
    battle_h = _src("include/constants/battle.h")
    assert re.search(r"#define B_WEATHER_HAIL_PERMANENT\s+\(1 << 8\)", battle_h)
    assert re.search(r"#define B_WEATHER_HAIL\s+\(B_WEATHER_HAIL_TEMPORARY \| B_WEATHER_HAIL_PERMANENT\)",
                     battle_h)
    # o bit 8 cabe: gBattleWeather e gWeatherMoveAnim são u16 e o controlador manda os 2 bytes
    assert "EWRAM_DATA u16 gBattleWeather = 0;" in _src("src/battle_main.c")
    assert "EWRAM_DATA u16 gWeatherMoveAnim = 0;" in _src("src/battle_anim.c")
    assert "sBattleBuffersTransferData[13] = (gBattleWeather & 0xFF00) >> 8;" in _src("src/battle_controllers.c")

    util = _src("src/battle_util.c")
    entrada = util[util.index("case ABILITYEFFECT_SWITCH_IN_WEATHER:"):]
    entrada = entrada[:entrada.index("if (effect != 0)")]
    neve = re.search(r"case WEATHER_SNOW:(?: *//[^\n]*)?\s*if \(!\(gBattleWeather & B_WEATHER_HAIL\)\)\s*\{(.*?)\}",
                     entrada, re.S)
    assert neve, "case WEATHER_SNOW no clima de entrada"
    for item in ("gBattleWeather = B_WEATHER_HAIL;", "gBattleScripting.animArg1 = B_ANIM_HAIL_CONTINUES;",
                 "gBattleScripting.battler = battler;", "effect++;"):
        assert item in neve.group(1), item

    fim = util[util.index("case ENDTURN_HAIL:"):util.index("case ENDTURN_FIELD_COUNT:")]
    assert ("if (!(gBattleWeather & B_WEATHER_HAIL_PERMANENT) && --gWishFutureKnock.weatherDuration == 0)"
            in fim)

    assert re.search(r"\[WEATHER_SNOW\]\s*=\s*STRINGID_STARTEDHAIL,", _src("src/battle_message.c"))

    # B_WEATHER_HAIL_TEMPORARY só nas gravações (golpe Hail e o fim do granizo temporário); os
    # testes de "há granizo" usam B_WEATHER_HAIL
    permitidos = {"gBattleWeather = B_WEATHER_HAIL_TEMPORARY;", "gBattleWeather &= ~B_WEATHER_HAIL_TEMPORARY;"}
    usos = []
    for arquivo in sorted((REPO_ROOT / "src").glob("*.c")):
        for n, linha in enumerate(arquivo.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "B_WEATHER_HAIL_TEMPORARY" in linha and linha.strip() not in permitidos:
                usos.append(f"{arquivo.name}:{n}: {linha.strip()}")
    assert not usos, usos
    assert re.search(r"if \(gBattleWeather & B_WEATHER_HAIL\)[^\n]*\n\s*AI_THINKING_STRUCT->funcResult = WEATHER_TYPE_HAIL;",
                     _src("src/battle_ai_script_commands.c"))
    assert "(B_WEATHER_RAIN | B_WEATHER_SANDSTORM | B_WEATHER_HAIL)) && gCurrentMove == MOVE_SOLAR_BEAM" in \
        _src("src/pokemon.c")


def test_atalho_batalha_selvagem():
    """TEST_CMD_START_WILD_BATTLE: cria o selvagem e roda um script de campo com dowildbattle (o
    caminho normal de setwildbattle/dowildbattle); os bytes do script batem com a tabela de comandos."""
    hooks_c = _src("src/test_hooks.c")
    caso = re.search(r"case TEST_CMD_START_WILD_BATTLE:(.*?)break;", hooks_c, re.S)
    assert caso, "case TEST_CMD_START_WILD_BATTLE"
    a_bloco = hooks_c[hooks_c.index("// Hack 7 front A: start"):hooks_c.index("// Hack 7 front A: end")]
    assert "case TEST_CMD_START_WILD_BATTLE:" in a_bloco
    for item in ("CreateScriptedWildMon(gTestMailbox.arg0, gTestMailbox.arg1, ITEM_NONE);",
                 "ScriptContext_SetupScript(sWildBattleScript);"):
        assert item in caso.group(1), item
    tabela = _src("data/script_cmd_table.inc")
    opcodes = {nome: int(valor, 16) for nome, valor in re.findall(r"\.4byte ScrCmd_(\w+)\s*@ 0x([0-9a-f]+)", tabela)}
    script = re.search(r"static const u8 sWildBattleScript\[\] =\s*\{(.*?)\};", hooks_c, re.S)
    assert script, "sWildBattleScript"
    pares = re.findall(r"(0x[0-9A-Fa-f]+),\s*// (\w+)", script.group(1))
    assert [nome for _, nome in pares] == ["lockall", "dowildbattle", "releaseall", "end"], pares
    for valor, nome in pares:
        assert int(valor, 16) == opcodes[nome], (nome, valor, opcodes[nome])
    assert re.search(r"TEST_CMD_START_WILD_BATTLE,\s*// arg0 = species, arg1 = level", _src("include/test_hooks.h"))


# --- revisão final da branch ---------------------------------------------------------------------

def test_clima_do_campo_fora_das_batalhas_roteirizadas():
    """Pokédude (Teachy TV) e o tutorial de captura do velho seguem um roteiro de comandos
    (sPokedudeTextScripts_*): o clima do campo (chuva, areia, granizo do Hack 7) não entra nelas."""
    main = _src("src/battle_main.c")
    assert re.search(r"if \(!gBattleStruct->overworldWeatherDone\s*"
                     r"&& !\(gBattleTypeFlags & \(BATTLE_TYPE_POKEDUDE \| BATTLE_TYPE_OLD_MAN_TUTORIAL\)\)\s*"
                     r"&& AbilityBattleEffects\(0, 0, 0, ABILITYEFFECT_SWITCH_IN_WEATHER, 0\) != 0\)", main)
    assert main.count("ABILITYEFFECT_SWITCH_IN_WEATHER") == 1



def test_creditos_com_o_clima_do_mapa():
    """Os créditos passeiam pelos mapas com LoadMapFromWarp, que sorteia o clima: logo depois,
    o carregador dos créditos volta ao clima do cabeçalho (nenhum mapa dos créditos troca o clima
    por script, então nada se perde)."""
    ow = _src("src/overworld.c")
    loader = re.search(r"static bool8 MapLdr_Credits\(void\)\n\{\n(.*?)\n\}", ow, re.S).group(1)
    assert re.search(r"LoadMapFromWarp\(FALSE\);\n\s*SetSavedWeather\(gMapHeader\.weather\);", loader)
    assert loader.index("SetSavedWeather(gMapHeader.weather);") < loader.index("StartWeather();")
    credits = _src("src/credits.c")
    mapas = re.findall(r"CREDITSOVWLDLOADMAP\(MAP_(\w+),", credits)
    assert len(mapas) == 13, mapas
    for mapa in mapas:
        pasta = "".join(p.capitalize() if not p.isdigit() else p for p in mapa.split("_"))
        pasta = pasta.replace("North", "_North")
        scripts = REPO_ROOT / "data" / "maps" / pasta / "scripts.inc"
        assert scripts.exists(), scripts
        assert "setweather" not in scripts.read_text(encoding="utf-8"), mapa
