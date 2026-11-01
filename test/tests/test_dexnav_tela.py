"""DexNav (POK-47), Task 2: a tela do mapa (layout A aprovado pelo Cintra), sem emulador.

A tela (src/dexnav.c) é uma tela cheia no molde de src/conquistas_tela.c: o estado num bloco `AllocZeroed` (o único
EWRAM novo é o ponteiro para ele), liberado na saída. Topo com o nome do mapa, o período do dia e "capturados/total"
(ou "100%" com a coroa); abas GRAMA, SURFAR, VARAS (seções Vara Velha / Vara Boa / Supervara) e PEDRA, só as que o mapa
tem, trocadas com L/R; cada linha com o ícone do Pokémon (silhueta quando nunca visto), a marca (capturado, visto,
nunca visto), o nome ("??????" quando nunca visto), a chance (%) e a faixa de nível, **em colunas fixas** (pedido do
Cintra: "cuidado com o alinhamento"). Este arquivo lê o C, os textos e o gráfico como texto; o comportamento no
emulador fica nas fotos da Task 2 e no cenário `dexnav` (Task 5).
"""

import re

from PIL import Image

from esteira import check_text, hooks
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
TELA_C = SRC / "dexnav.c"
DEXNAV_H = REPO_ROOT / "include" / "dexnav.h"
STRINGS_C = SRC / "strings.c"
STRINGS_H = REPO_ROOT / "include" / "strings.h"
HOOKS_H = REPO_ROOT / "include" / "test_hooks.h"
HOOKS_C = SRC / "test_hooks.c"
NOMES_ESPECIES = SRC / "data" / "text" / "species_names.h"
GFX = REPO_ROOT / "graphics" / "dexnav"
LARGURA_TELA = 240


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _sem_comentarios(fonte: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", fonte, flags=re.S)


def _defines(fonte: str) -> dict[str, int]:
    """#define NOME <número> (só os literais; expressões ficam de fora)."""
    return {m.group(1): int(m.group(2), 0)
            for m in re.finditer(r"^#define (\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", fonte, re.M)}


def _medir(texto: str, fonte: str = "normal") -> int:
    env = check_text._load_env(REPO_ROOT)
    return check_text.measure(texto + "$", env, font=fonte).widest


def _textos_dexnav() -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r'const u8 (gText_DexNav_\w+)\[\]\s*=\s*_\("(.*?)"\);',
                                                         _ler(STRINGS_C))}


def _maior_especie() -> int:
    nomes = re.findall(r'_\("([^"]*)"\)', _ler(NOMES_ESPECIES))
    assert len(nomes) > 400
    return max(_medir(n) for n in nomes)


# --- interface ---------------------------------------------------------------------------------------------------

def test_interface():
    h = _ler(DEXNAV_H)
    for proto in ("void DexNav_Open(MainCallback returnTo);", "void CB2_DexNav(void);",
                  "void DexNav_OpenFromScript(void);", "u32 DexNav_TestGetState(u8 what);"):
        assert proto in h, proto
    d = _defines(h)
    assert (d["DEXNAV_MODE_MAP"], d["DEXNAV_MODE_LIST"], d["DEXNAV_MODE_SEARCH"]) == (0, 1, 2)
    assert (d["DEXNAV_TAB_LAND"], d["DEXNAV_TAB_WATER"], d["DEXNAV_TAB_RODS"], d["DEXNAV_TAB_ROCK"],
            d["DEXNAV_TAB_COUNT"]) == (0, 1, 2, 3, 4)
    fonte = _ler(TELA_C)
    # abrir pelo script de campo: volta ao script com a música do mapa (o molde do Conquistas_AbrirTelaDoScript)
    script = _corpo(fonte, "DexNav_OpenFromScript")
    assert "DexNav_Open(CB2_ReturnToFieldContinueScriptPlayMapMusic);" in script
    assert "QuestLog_CutRecording();" in script and "LockPlayerFieldControls();" in script


def test_abre_no_mapa_atual_ou_volta():
    """Mapa atual com encontro: abre no modo mapa dele; sem encontro, por ora volta direto (a Task 3 põe a lista)."""
    corpo = _corpo(_ler(TELA_C), "DexNav_Open")
    assert "DexNav_MapIndexOf(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum)" in corpo
    assert "DEXNAV_MODE_MAP" in corpo
    assert "SetMainCallback2(returnTo);" in corpo


def test_heap():
    """O estado vai para o heap (AllocZeroed ao abrir, Free ao sair); o único EWRAM novo é o ponteiro."""
    fonte = _sem_comentarios(_ler(TELA_C))
    ewram = re.findall(r"^.*\bEWRAM_DATA\b.*$", fonte, re.M)
    assert ewram == ["static EWRAM_DATA struct DexNavTela *sDexNav = NULL;"], ewram
    assert "IWRAM_DATA" not in fonte
    globais = [g for g in re.findall(r"^static (?!const\b)[^(=;]*[;=]", fonte, re.M) if "sDexNav" not in g]
    assert globais == [], globais
    assert "sDexNav = AllocZeroed(sizeof(*sDexNav));" in fonte
    saida = _corpo(fonte, "Task_DexNav_Sair")
    assert "Free(sDexNav);" in saida and "sDexNav = NULL;" in saida and "FreeAllWindowBuffers();" in saida
    assert saida.index("sDexNav = NULL;") < saida.index("SetMainCallback2(voltar);")
    # nos arquivos do DexNav (tela e dados), no máximo esse ponteiro em EWRAM
    todos = [l for c in sorted(SRC.glob("dexnav*.c"))
             for l in re.findall(r"^.*\bEWRAM_DATA\b.*$", _sem_comentarios(_ler(c)), re.M)]
    assert todos == ["static EWRAM_DATA struct DexNavTela *sDexNav = NULL;"], todos
    # as entradas do mapa ficam no bloco (DEXNAV_MAX_ENTRIES), não na pilha de cada desenho
    assert "struct DexNavEntry entries[DEXNAV_MAX_ENTRIES];" in fonte


def test_tela_desliga_ajuda():
    fonte = _ler(TELA_C)
    assert "ajudaAntes = gHelpSystemEnabled;" in fonte and "gHelpSystemEnabled = FALSE;" in fonte
    saida = _corpo(fonte, "Task_DexNav_Sair")
    assert re.search(r"if \(ajudaAntes\)\s*HelpSystem_Enable\(\);", saida), saida


def test_iniciar_video_zera_efeitos():
    corpo = _corpo(_ler(TELA_C), "IniciarVideo")
    for reg in ("BLDCNT", "BLDALPHA", "BLDY", "WININ", "WINOUT"):
        assert f"SetGpuReg(REG_OFFSET_{reg}, 0);" in corpo, reg
    assert "DISPCNT_OBJ_ON" in corpo, "os ícones dos Pokémon são sprites"


# --- alinhamento (o pedido do Cintra) -----------------------------------------------------------------------------

COLUNAS = ("COL_ICONE_X", "COL_MARCA_X", "COL_NOME_X", "COL_NOME_LARGURA", "COL_CHANCE_FIM", "COL_CHANCE_LARGURA",
           "COL_NIVEL_X", "COL_NIVEL_MIN_FIM", "COL_NIVEL_TRACO_X", "COL_NIVEL_MAX_X", "COL_NIVEL_MAX_LARGURA", "COL_SETA_X")


def test_colunas_fixas():
    fonte = _ler(TELA_C)
    d = _defines(fonte)
    for nome in COLUNAS:
        assert nome in d, nome
    linha = _sem_comentarios(_corpo(fonte, "DesenharLinhaMon"))
    # cada coluna sai da sua constante: nada de x literal nas chamadas que desenham a linha
    assert "COL_ICONE_X" in _sem_comentarios(_corpo(fonte, "CriarIcone"))
    assert re.search(r"BlitIcone\(WIN_LISTA, [^,]+, COL_MARCA_X,", linha), linha
    assert re.search(r"AddTextPrinterParameterized4\(WIN_LISTA, FONT_NORMAL, COL_NOME_X,", linha), linha
    assert "COL_CHANCE_FIM - GetStringWidth(FONT_NORMAL, " in linha, "a chance é alinhada à direita"
    assert re.search(r"AddTextPrinterParameterized4\(WIN_LISTA, FONT_NORMAL, COL_NIVEL_X,", linha), linha
    assert "COL_NIVEL_MIN_FIM - GetStringWidth(FONT_NORMAL, " in linha, "o nível mínimo é alinhado à direita"
    # faixa "3 - 4" / "25 - 35": mínimo à direita até antes do traço, traço fixo, máximo à esquerda logo depois dele
    assert re.search(r"AddTextPrinterParameterized4\(WIN_LISTA, FONT_NORMAL, COL_NIVEL_MAX_X,", linha), linha
    assert "COL_NIVEL_MAX_X - " not in linha and "COL_NIVEL_MAX_FIM" not in fonte
    assert re.search(r"AddTextPrinterParameterized4\(WIN_LISTA, FONT_NORMAL, COL_NIVEL_TRACO_X,", linha), linha
    for chamada in re.findall(r"AddTextPrinterParameterized4\(WIN_LISTA, FONT_NORMAL, ([^,]+),", linha):
        assert not re.fullmatch(r"\s*\d+\s*", chamada), f"x literal na linha: {chamada}"

    # as colunas não se encostam no pior caso de cada uma
    especie = max(_maior_especie(), _medir("??????"))
    chance = max(_medir(t) for t in ("100%", "99,5%", "88,8%", "0,5%"))
    nivel3 = _medir("100")
    assert d["COL_ICONE_X"] + 32 <= d["COL_MARCA_X"]
    assert d["COL_MARCA_X"] + 8 + 4 <= d["COL_NOME_X"]
    assert especie <= d["COL_NOME_LARGURA"], especie
    assert chance <= d["COL_CHANCE_LARGURA"], chance
    assert d["COL_NOME_X"] + d["COL_NOME_LARGURA"] + 4 <= d["COL_CHANCE_FIM"] - d["COL_CHANCE_LARGURA"]
    assert d["COL_CHANCE_FIM"] + 8 <= d["COL_NIVEL_X"]
    assert d["COL_NIVEL_X"] + _medir("Nv.") <= d["COL_NIVEL_MIN_FIM"] - nivel3
    assert d["COL_NIVEL_MIN_FIM"] < d["COL_NIVEL_TRACO_X"], "um respiro entre o mínimo e o traço"
    assert d["COL_NIVEL_TRACO_X"] + _medir("-") < d["COL_NIVEL_MAX_X"], "um respiro entre o traço e o máximo"
    # o traço fica no meio: o respiro de cada lado difere no máximo 2 px
    antes = d["COL_NIVEL_TRACO_X"] - d["COL_NIVEL_MIN_FIM"]
    depois = d["COL_NIVEL_MAX_X"] - (d["COL_NIVEL_TRACO_X"] + _medir("-"))
    assert abs(antes - depois) <= 2, (antes, depois)
    assert nivel3 <= d["COL_NIVEL_MAX_LARGURA"]
    assert d["COL_NIVEL_MAX_X"] + d["COL_NIVEL_MAX_LARGURA"] <= d["COL_SETA_X"]
    assert d["COL_SETA_X"] + _medir("{UP_ARROW}") <= LARGURA_TELA


def test_topo_e_abas_alinhados():
    fonte = _ler(TELA_C)
    d = _defines(fonte)
    h = _defines(_ler(DEXNAV_H))
    topo = _sem_comentarios(_corpo(fonte, "DesenharTopo"))
    assert "TOPO_NOME_X" in topo and "TOPO_PERIODO_X" in topo and "TOPO_COROA_X" in topo
    assert "TOPO_CONTADOR_FIM - GetStringWidth(FONT_NORMAL, " in topo, "o contador é alinhado à direita"
    # o período sai do relógio (o mesmo nome do relógio do menu Start); a tarde-noite é "Entardecer"
    assert "gText_DayNight_PeriodName[" in topo and "DayNight_GetPeriod()" in fonte
    periodos = ("Manhã", "Tarde", "Entardecer", "Noite")
    textos = _ler(STRINGS_C)
    for p in periodos:
        assert f'_("{p}")' in textos, p
    assert d["TOPO_NOME_X"] + h["DEXNAV_NAME_WIDTH"] + 4 <= d["TOPO_PERIODO_X"]
    assert max(_medir(p) for p in periodos) <= d["TOPO_PERIODO_LARGURA"]
    contador = max(_medir("99/99"), _medir("100%"))
    assert d["TOPO_PERIODO_X"] + d["TOPO_PERIODO_LARGURA"] + 4 <= d["TOPO_CONTADOR_FIM"] - contador
    assert d["TOPO_CONTADOR_FIM"] + 2 <= d["TOPO_COROA_X"] and d["TOPO_COROA_X"] + 8 <= LARGURA_TELA

    abas = _sem_comentarios(_corpo(fonte, "DesenharAbas"))
    assert "ABA_X0 + " in abas and "ABA_PASSO" in abas, "cada aba numa vaga fixa"
    rotulos = [v for k, v in _textos_dexnav().items() if k.startswith("gText_DexNav_Aba")]
    assert len(rotulos) == 4
    assert max(_medir(r) for r in rotulos) + d["ABA_TEXTO_DX"] + 2 <= d["ABA_COROA_DX"]
    assert d["ABA_COROA_DX"] + 8 <= d["ABA_LARGURA"] <= d["ABA_PASSO"]
    assert d["ABA_X0"] + 3 * d["ABA_PASSO"] + d["ABA_LARGURA"] <= LARGURA_TELA


def test_linhas_e_rolagem():
    fonte = _ler(TELA_C)
    d = _defines(fonte)
    assert d["LINHA_MON_ALTURA"] >= 24, "o ícone de 32x32 precisa de pelo menos 24 px por linha"
    assert d["LISTA_ALTURA"] % 8 == 0
    # rola quando passa de 4 Pokémon (o ícone de cada linha visível é um sprite)
    assert d["LISTA_ALTURA"] // d["LINHA_MON_ALTURA"] == 4
    assert "STATIC_ASSERT(ICONES_MAX * LINHA_MON_ALTURA <= LISTA_ALTURA" in fonte
    lista = _corpo(fonte, "DesenharLista")
    assert "sText_SetaCima" in lista and "sText_SetaBaixo" in lista and "COL_SETA_X" in lista


def test_chance_do_periodo_atual():
    """A chance vem de DexNav_RateForPeriods com os bits do período (a tarde-noite tem 2 bits): nunca rateX10[bit]."""
    fonte = _sem_comentarios(_ler(TELA_C))
    assert "rateX10[" not in fonte
    assert "DexNav_RateForPeriods(" in fonte and "DexNav_CurrentPeriodBit()" in fonte
    assert re.search(r"->periods & \w+->periods\b|\.periods & \w+->periods\b|periods & t->periods", fonte), \
        "a lista testa o período com `periods & bits`"
    # contador e coroa contam todas as espécies em qualquer horário; a linha extra lista as que não aparecem agora
    contar = _corpo(fonte, "ContarEspecies")
    assert "periods" not in contar, "o progresso não muda com o relógio"
    assert "FLAG_GET_CAUGHT" in contar


def test_marcas_e_silhueta():
    fonte = _ler(TELA_C)
    linha = _corpo(fonte, "DesenharLinhaMon")
    assert "FLAG_GET_CAUGHT" in fonte and "FLAG_GET_SEEN" in fonte
    for icone in ("ICONE_CAPTURADO", "ICONE_VISTO", "ICONE_NUNCA_VISTO"):
        assert icone in linha, icone
    assert "gText_DexNav_Desconhecido" in linha and "gSpeciesNames[" in linha
    icone = _corpo(fonte, "CriarIcone")
    assert "CreateMonIcon(" in icone and "TAG_SILHUETA" in icone and "oam.paletteNum" in icone
    assert "oam.priority = 0" in icone, "o ícone fica na frente da faixa amarela da linha selecionada"
    # a paleta da silhueta: a cor 0 transparente e as outras escuras
    pal = re.search(r"sSilhueta_Pal\[16\] = \{(.*?)\};", fonte, re.S)
    assert pal, "paleta da silhueta"
    cores = [c.strip() for c in pal.group(1).split(",") if c.strip()]
    assert len(cores) == 16 and len(set(cores[1:])) == 1, cores


def test_icones_do_dexnav():
    png = Image.open(GFX / "icones.png")
    assert png.mode == "P" and png.size == (32, 8), (png.mode, png.size)
    assert max(png.tobytes()) < 16
    pal = (GFX / "icones.pal").read_bytes()
    assert pal.startswith(b"JASC-PAL\r\n0100\r\n16\r\n") and pal.count(b"\r\n") == 19, pal[:40]
    fonte = _ler(TELA_C)
    assert 'INCBIN_U8("graphics/dexnav/icones.4bpp")' in fonte
    assert 'INCBIN_U16("graphics/dexnav/icones.gbapal")' in fonte
    nomes = re.search(r"enum \{\s*(ICONE_CAPTURADO,.*?)ICONE_COUNT", fonte, re.S).group(1)
    assert [n.strip() for n in nomes.split(",") if n.strip()] == [
        "ICONE_CAPTURADO", "ICONE_VISTO", "ICONE_NUNCA_VISTO", "ICONE_COROA"]


def test_controles():
    fonte = _ler(TELA_C)
    entrada = _corpo(fonte, "Task_DexNav_Input")
    for trecho in ("JOY_NEW(B_BUTTON)", "JOY_NEW(L_BUTTON)", "JOY_NEW(R_BUTTON)", "JOY_REPT(DPAD_UP)",
                   "JOY_REPT(DPAD_DOWN)"):
        assert trecho in entrada, trecho
    # L/R dão a volta entre as abas que o mapa tem
    assert "t->nAbas" in _corpo(fonte, "TrocarAba")


# --- textos ------------------------------------------------------------------------------------------------------

ESPERADOS = {
    "gText_DexNav_AbaGrama": "GRAMA",
    "gText_DexNav_AbaSurf": "SURFAR",
    "gText_DexNav_AbaVaras": "VARAS",
    "gText_DexNav_AbaPedra": "PEDRA",
    "gText_DexNav_VaraVelha": "Vara Velha",
    "gText_DexNav_VaraBoa": "Vara Boa",
    "gText_DexNav_Supervara": "Supervara",
    "gText_DexNav_Desconhecido": "??????",
    "gText_DexNav_Nivel": "Nv.",
    "gText_DexNav_Completo": "100%",
    "gText_DexNav_MaisNoite": "+{STR_VAR_1} à noite",
    "gText_DexNav_MaisDia": "+{STR_VAR_1} de dia",
    "gText_DexNav_MaisManha": "+{STR_VAR_1} de manhã",
    "gText_DexNav_MaisTarde": "+{STR_VAR_1} à tarde",
    "gText_DexNav_MaisOutros": "+{STR_VAR_1} em outros horários",
    "gText_DexNav_Nenhum": "Nenhum Pokémon por aqui.",
    "gText_DexNav_Rodape": "L/R: aba   B: sair",
    "gText_DexNav_RodapeSair": "B: sair",
    "gText_DexNav_NenhumAgora": "Nenhum agora",
}


def test_textos():
    textos = _textos_dexnav()
    for nome, texto in ESPERADOS.items():
        assert textos.get(nome) == texto, (nome, textos.get(nome))
    h = _ler(STRINGS_H)
    for nome in textos:
        assert f"extern const u8 {nome}[];" in h, nome
    # a esteira de larguras tem regra (com citação) para cada um
    for nome in textos:
        regra = check_text.rule_for("src/strings.c", nome)
        assert regra is not None and regra.px is not None and regra.lines == 1 and not regra.by_usage, (nome, regra)
    d = _defines(_ler(TELA_C))
    assert check_text.rule_for("src/strings.c", "gText_DexNav_AbaGrama").px == d["ABA_COROA_DX"] - d["ABA_TEXTO_DX"] - 2
    assert check_text.rule_for("src/strings.c", "gText_DexNav_Desconhecido").px == d["COL_NOME_LARGURA"]
    # a linha extra com o pior número real (até 32 espécies por mapa) cabe entre a coluna do nome e as setas
    for nome in ("gText_DexNav_MaisNoite", "gText_DexNav_MaisDia", "gText_DexNav_MaisManha", "gText_DexNav_MaisTarde",
                 "gText_DexNav_MaisOutros"):
        assert _medir(textos[nome].replace("{STR_VAR_1}", "32")) <= d["COL_SETA_X"] - d["COL_NOME_X"], nome
    assert _medir(textos["gText_DexNav_Completo"]) <= max(_medir("99/99"), 26)


def test_textos_sem_buffer_estourado():
    """O número da linha extra vai para gStringVar1 (2 dígitos); o nome do mapa é impresso direto da tabela."""
    fonte = _ler(TELA_C)
    extra = _corpo(fonte, "DesenharLinhaExtra")
    assert "ConvertIntToDecimalStringN(gStringVar1, " in extra and "STR_CONV_MODE_LEFT_ALIGN, 2)" in extra
    topo = _corpo(fonte, "DesenharTopo")
    assert "gDexNavMaps[t->mapIndex].name" in topo


# --- atalhos da esteira ------------------------------------------------------------------------------------------

def test_atalhos():
    h = _ler(HOOKS_H)
    assert re.search(r"TEST_CMD_DEXNAV_STATE = 0xE3,", h) and re.search(r"TEST_CMD_OPEN_DEXNAV = 0xE4,", h)
    assert hooks.CMD_DEXNAV_STATE == 0xE3 and hooks.CMD_OPEN_DEXNAV == 0xE4
    assert callable(hooks.Mailbox.open_dexnav) and callable(hooks.Mailbox.dexnav_tela)
    c = _ler(HOOKS_C)
    assert "case TEST_CMD_DEXNAV_STATE:" in c and "case TEST_CMD_OPEN_DEXNAV:" in c
    abrir = _corpo(c, "OpenDexNav")
    assert "DexNav_OpenFromScript" in abrir and "0x23" in abrir, "callnative, sem special novo"
    estado = _corpo(_ler(TELA_C), "DexNav_TestGetState")
    assert "0xFFFFFFFF" in estado
    assert re.search(r"modo\s*\|\s*\w+\s*<<\s*8\s*\|\s*\w+\s*<<\s*16\s*\|\s*.*mapIndex\s*<<\s*24", estado), estado


def test_citacoes_apontam_para_o_codigo():
    """As regras de largura e a exceção do {STR_VAR_1} que citam src/dexnav.c apontam para as constantes (#define) e
    para a linha que enche gStringVar1: a citação não fica velha quando a tela cresce (Task 3)."""
    from esteira.janelas_uso import VAR_CONTENTS
    linhas = _ler(TELA_C).splitlines()

    def citadas(fonte):
        for a, b in re.findall(r"src/dexnav\.c:(\d+)(?:-(\d+))?", fonte):
            yield linhas[int(a) - 1:int(b or a)]

    vistas = 0
    for regra in check_text.WIDTH_RULES:
        if regra.prefix and regra.prefix.startswith("gText_DexNav_"):
            for trecho in citadas(regra.source):
                assert trecho and all(l.startswith("#define ") for l in trecho), (regra.prefix, trecho)
                vistas += 1
    from esteira.janelas_uso import USAGE_RULES
    for uso in USAGE_RULES:
        if uso.file == "src/dexnav.c":
            for trecho in citadas(uso.source):
                assert trecho and all(l.startswith("#define ") for l in trecho), (uso.label, trecho)
                vistas += 1
    for vc in VAR_CONTENTS:
        if vc.label.startswith("gText_DexNav_"):
            for trecho in citadas(vc.source):
                assert any("gStringVar1" in l for l in trecho), (vc.label, trecho)
                vistas += 1
    assert vistas >= 20, vistas


# --- rodada de correções 1 (revisão da Task 2) -----------------------------------------------------------------------

def test_titulo_da_secao_nao_some_ao_rolar():
    """VARAS: o título da vara da linha de cima fica à vista ao rolar (fixo no alto quando o original rolou)."""
    fonte = _ler(TELA_C)
    fixa = _corpo(fonte, "SecaoFixa")
    assert "SecaoDaLinha(t, t->topo)" in fixa and "LINHA_SECAO" in fixa
    lista = _corpo(fonte, "DesenharLista")
    assert "SecaoFixa(t)" in lista and "y = LINHA_SECAO_ALTURA;" in lista
    assert lista.index("y = LINHA_SECAO_ALTURA;") < lista.index("for (i = t->topo;")
    ajuste = _corpo(fonte, "AjustarTopo")
    # o título fixo entra na conta da altura (senão a última linha passa do fim da lista)
    assert "AlturaVisivel(t, ultima) > LISTA_ALTURA" in ajuste
    assert "SecaoFixa(t)" in _corpo(fonte, "AlturaVisivel")
    assert "SecaoDaLinha(t, t->cursor)" in ajuste


def test_rodape_so_mostra_lr_com_duas_abas():
    rodape = _corpo(_ler(TELA_C), "DesenharRodape")
    assert re.search(r"t->nAbas >= 2 \? gText_DexNav_Rodape : gText_DexNav_RodapeSair", rodape), rodape


def test_aba_sem_pokemon_agora_se_explica():
    fonte = _ler(TELA_C)
    montar = _corpo(fonte, "MontarAba")
    m = re.search(r"if \(t->nMons == 0\)\s*AdicionarLinha\(t, LINHA_VAZIA, 0\);", montar)
    assert m, montar
    assert montar.index("LINHA_VAZIA") < montar.index("LINHA_EXTRA, 0"), "a linha vazia vem antes do +N"
    assert "gText_DexNav_NenhumAgora" in _corpo(fonte, "DesenharLinhaVazia")
    assert "case LINHA_VAZIA:" in _corpo(fonte, "DesenharLista")
    # ▲▼ só param em linha de Pokémon: sem Pokémon, a seleção fica parada
    assert "t->linhas[i].tipo != LINHA_MON" in _corpo(fonte, "MoverCursor")


def test_dexnav_tela_recusa_what_invalido():
    import pytest

    caixa = object.__new__(hooks.Mailbox)
    for ruim in (-1, 4, 255):
        with pytest.raises(ValueError, match="what"):
            caixa.dexnav_tela(ruim)
