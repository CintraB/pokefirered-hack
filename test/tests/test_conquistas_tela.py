"""Conquistas e diário de batalhas (POK-44), Tasks 7 e 8: a tela de conquistas, o botão no Cartão de Treinador e o
modo diário da mesma tela (SELECT alterna).

A tela (src/conquistas_tela.c) é uma tela cheia nova no molde de src/novidades.c: um bloco `AllocZeroed` (o ponteiro
fica numa task, sem EWRAM nova), liberado na saída. Abas trocadas com L/R (dando a volta), ▲▼ rolam, B volta;
o cartão de treinador abre a tela com SELECT (só fora de link) e a tela volta ao cartão. Este arquivo lê o C, os
textos e o gráfico como texto; o comportamento no emulador fica no cenário `conquistas` (grupos `tela/*`).
"""

import json
import re
import subprocess

from PIL import Image

from esteira import check_text, hooks, refs
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
TELA_C = SRC / "conquistas_tela.c"
CARTAO_C = SRC / "trainer_card.c"
CONQ_C = SRC / "conquistas.c"
CONQ_H = REPO_ROOT / "include" / "conquistas.h"
STRINGS_C = SRC / "strings.c"
SPECIALS = REPO_ROOT / "data" / "specials.inc"
JSON_PATH = SRC / "data" / "conquistas" / "conquistas.json"
GFX = REPO_ROOT / "graphics" / "conquistas"
CENARIO = REPO_ROOT / "test" / "esteira" / "scenarios" / "full_conquistas.py"
BASE = "4be5f6b56"
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


def _medir(texto: str, fonte: str = "normal") -> int:
    env = check_text._load_env(REPO_ROOT)
    return check_text.measure(texto + "$", env, font=fonte).widest


# --- o botão no cartão ------------------------------------------------------------------------------------------
def test_cartao_select_so_fora_de_link():
    fonte = _ler(CARTAO_C)
    frente = re.search(r"case STATE_HANDLE_INPUT_FRONT:(.*?)\n    case ", fonte, re.S).group(1)
    m = re.search(r"else if \(JOY_NEW\(SELECT_BUTTON\) && !sTrainerCardDataPtr->isLink && !gReceivedRemoteLinkPlayers\)"
                  r"\s*\{(.*?)\}", frente, re.S)
    assert m, "o SELECT do cartão precisa da condição !isLink && !gReceivedRemoteLinkPlayers"
    bloco = m.group(1)
    for linha in ("PlaySE(SE_SELECT);", "BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);",
                  "sTrainerCardDataPtr->callback2 = CB2_AbrirConquistasDoCartao;",
                  "sTrainerCardDataPtr->mainState = STATE_CLOSE_CARD;"):
        assert linha in bloco, linha
    assert _sem_comentarios(fonte).count("SELECT_BUTTON") == 1, "o SELECT só na frente do cartão"
    # contra a base: só linhas novas, e cada trecho novo é o botão ou a dica
    diff = subprocess.run(["git", "diff", "-U0", BASE, "--", "src/trainer_card.c"], cwd=REPO_ROOT, check=True,
                          capture_output=True, text=True).stdout
    removidas = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    assert removidas == [], removidas
    trechos = re.split(r"^@@.*$", diff, flags=re.M)[1:]
    assert trechos, "trainer_card.c sem o botão"
    for trecho in trechos:
        texto = "\n".join(l[1:] for l in trecho.splitlines() if l.startswith("+"))
        assert re.search(r"conquista|SELECT_BUTTON", texto, re.I), f"trecho fora do botão e da dica:\n{texto}"


def test_dica_na_frente_do_cartao():
    fonte = _ler(CARTAO_C)
    frente = _corpo(fonte, "PrintAllOnCardFront")
    assert "PrintConquistasHintOnCard();" in frente
    dica = _corpo(fonte, "PrintConquistasHintOnCard")
    # a mesma condição do botão: onde o SELECT não vale, a dica não aparece
    assert "if (!sTrainerCardDataPtr->isLink && !gReceivedRemoteLinkPlayers)" in dica
    assert "gText_ConqTela_DicaCartao" in dica
    assert '#include "conquistas.h"' in fonte


# --- a tela -----------------------------------------------------------------------------------------------------
def test_interface():
    h = _ler(CONQ_H)
    for proto in ("void Conquistas_AbrirTela(void (*voltar)(void), u8 modo);",
                  "void CB2_AbrirConquistasDoCartao(void);", "void Conquistas_AbrirTelaDoScript(void);",
                  "u32 Conquistas_TestGetState(void);"):
        assert proto in h, proto
    fonte = _ler(TELA_C)
    assert "static void CB2_VoltarAoCartao(void)" in fonte
    assert "ShowPlayerTrainerCard(CB2_ReturnToFieldWithOpenMenu);" in _corpo(fonte, "CB2_VoltarAoCartao")
    assert "Conquistas_AbrirTela(CB2_VoltarAoCartao, 0);" in _corpo(fonte, "CB2_AbrirConquistasDoCartao")
    script = _corpo(fonte, "Conquistas_AbrirTelaDoScript")
    assert "Conquistas_AbrirTela(CB2_ReturnToFieldContinueScriptPlayMapMusic, gSpecialVar_0x8004" in script


def test_tela_desliga_ajuda():
    fonte = _ler(TELA_C)
    entrada = _corpo(fonte, "Conquistas_AbrirTela")
    assert "t->ajudaAntes = gHelpSystemEnabled;" in entrada
    assert entrada.index("t->ajudaAntes = gHelpSystemEnabled;") < entrada.index("gHelpSystemEnabled = FALSE;")
    saida = _corpo(fonte, "Task_ConquistasTela_Sair")
    # na saída a ajuda volta ao valor de antes (guardado no bloco), não é sempre religada
    assert "ajudaAntes = t->ajudaAntes;" in saida
    assert re.search(r"if \(ajudaAntes\)\s*HelpSystem_Enable\(\);", saida), saida
    assert saida.index("HelpSystem_Enable();") < saida.index("SetMainCallback2(voltar);")
    assert "Free(t);" in saida and "FreeAllWindowBuffers();" in saida
    assert "u8 ajudaAntes;" in fonte


def test_iniciar_video_zera_efeitos():
    """A tela não herda o escurecimento (BLDCNT/BLDY) nem as janelas do cartão de treinador."""
    corpo = _corpo(_ler(TELA_C), "IniciarVideo")
    for reg in ("BLDCNT", "BLDALPHA", "BLDY", "WININ", "WINOUT"):
        assert f"SetGpuReg(REG_OFFSET_{reg}, 0);" in corpo, reg
    assert corpo.index("REG_OFFSET_BLDCNT") < corpo.index("ShowBg(0);")


def test_memoria_no_heap():
    fonte = _sem_comentarios(_ler(TELA_C))
    assert "EWRAM_DATA" not in fonte and "IWRAM_DATA" not in fonte
    # nenhuma variável global de arquivo (o ponteiro do bloco fica na task)
    globais = re.findall(r"^static (?!const\b)[^(=;]*[;=]", fonte, re.M)
    assert globais == [], globais
    assert "AllocZeroed(sizeof(*t))" in fonte
    assert "SetWordTaskArg(" in fonte and "GetWordTaskArg(" in fonte


def test_controles():
    fonte = _ler(TELA_C)
    entrada = _corpo(fonte, "Task_ConquistasTela_Input")
    for trecho in ("JOY_NEW(B_BUTTON)", "JOY_NEW(SELECT_BUTTON)", "TrocarModo(t);"):
        assert trecho in entrada, trecho
    conq = _corpo(fonte, "Input_Conquistas")
    for trecho in ("JOY_NEW(L_BUTTON)", "JOY_NEW(R_BUTTON)", "JOY_REPT(DPAD_UP)", "JOY_REPT(DPAD_DOWN)"):
        assert trecho in conq, trecho
    diario = _corpo(fonte, "Input_Diario")
    for trecho in ("JOY_REPT(DPAD_UP)", "JOY_REPT(DPAD_DOWN)"):
        assert trecho in diario, trecho
    assert "CONQ_ABAS_COUNT" in _corpo(fonte, "TrocarAba"), "L/R dão a volta"


def test_estado_da_tela():
    fonte = _ler(TELA_C)
    corpo = _corpo(fonte, "Conquistas_TestGetState")
    assert "0xFFFFFFFF" in corpo
    # o 3º byte é a primeira linha visível nas conquistas e a linha selecionada (cursor) no diário
    assert re.search(r"t->modo\s*\?\s*t->dCursor\s*:\s*t->topo", corpo), corpo
    assert re.search(r"modo\s*\|\s*.*aba\s*<<\s*8\s*\|\s*.*<<\s*16\s*\|\s*.*inputReady\s*<<\s*24", corpo,
                     re.S), corpo
    h = _ler(CONQ_H)
    assert "linha selecionada" in h and "no modo diário" in h, "o include documenta o campo no modo diário"
    extra = _corpo(fonte, "Conquistas_TestGetDiario")
    assert "0xFFFFFFFF" in extra and "t->dN" in extra and "t->dTopo" in extra
    hook = _ler(SRC / "test_hooks.c")
    assert "gTestMailbox.arg0 ? Conquistas_TestGetDiario() : Conquistas_TestGetState()" in hook


def test_lista_estados_e_riscada():
    fonte = _ler(TELA_C)
    linha = _corpo(fonte, "DesenharLinha")
    for trecho in ("Conquistas_GetEstado(", "Conquistas_Progresso(", "CONQ_PERDIDA", "CONQ_FEITA",
                   "FillWindowPixelRect("):
        assert trecho in linha, trecho
    montar = _corpo(fonte, "MontarLista")
    assert ".ativa" in montar and ".aba" in montar, "inativa não aparece; só a aba atual"
    rodape = _corpo(fonte, "DesenharRodape")
    assert "Conquistas_ContarAba(" in rodape and "gText_ConqTela_Rodape" in rodape


def test_pendente_sem_progresso_mostra_traco():
    """Conquista de sim/não pendente (não perdida) mostra "──" na coluna do progresso."""
    linha = _corpo(_ler(TELA_C), "DesenharLinha")
    m = re.search(r"if \(estado == CONQ_FEITA\)\s*return;\s*if \(!temProgresso\)\s*\{(.*?)\}", linha, re.S)
    assert m, "o ramo pendente sem progresso (estado != FEITA e !temProgresso) precisa desenhar o traço"
    assert "FillWindowPixelRect(" in m.group(1) and "COR_PROGRESSO" in m.group(1) and "TRACO_" in m.group(1), m.group(1)
    fonte = _ler(TELA_C)
    largura = int(re.search(r"#define TRACO_LARGURA\s+(\d+)", fonte).group(1))
    assert 8 <= largura <= 24
    # o traço fica na coluna do progresso (termina em PROGRESSO_FIM) e não encosta no nome mais largo
    assert "PROGRESSO_FIM - TRACO_LARGURA" in m.group(1)
    dados = json.loads(_ler(JSON_PATH))
    mais_largo = max(_medir(c["nome"].replace("{N}", "300")) for c in dados["conquistas"] if c.get("ativa", True))
    assert 16 + mais_largo + 8 <= 222 - largura, (mais_largo, largura)


def _charmap() -> dict[str, int]:
    glifos = {}
    latino = _ler(REPO_ROOT / "charmap.txt").split("@ Hiragana")[0]   # depois dele vêm os códigos do japonês
    for m in re.finditer(r"^'(\\.|[^'\\])'\s*=\s*([0-9A-Fa-f]{2})\s*(?:@.*)?$", latino, re.M):
        glifos.setdefault(m.group(1), int(m.group(2), 16))
    return glifos


def _chars_h() -> dict[str, int]:
    return {m.group(1): int(m.group(2), 16)
            for m in re.finditer(r"#define (CHAR_\w+)\s+(0x[0-9A-Fa-f]+)", _ler(REPO_ROOT / "include" / "characters.h"))}


def test_minusculas_conferem_com_o_charmap():
    """A tabela `sMinusculas` da tela (HISTÓRIA -> História) escreve à mão os bytes de Ã/Õ -> ã/õ (os glifos do
    Hack 7 não têm CHAR_*): cada par, em CHAR_* ou em hexadecimal, bate com o charmap.txt, letra a letra."""
    fonte = _ler(TELA_C)
    tabela = re.search(r"static const u8 sMinusculas\[\]\[2\] = \{(.*?)\n\};", fonte, re.S).group(1)
    tabela = re.sub(r"//[^\n]*", "", tabela)
    glifos, nomes = _charmap(), _chars_h()
    por_codigo = {v: k for k, v in glifos.items()}

    def valor(token: str) -> int:
        token = token.strip()
        return nomes[token] if token.startswith("CHAR_") else int(token, 16)
    pares = re.findall(r"\{\s*(\w+)\s*,\s*(\w+)\s*\}", tabela)
    assert len(pares) >= 12, pares
    for maiuscula, minuscula in pares:
        a, b = valor(maiuscula), valor(minuscula)
        assert a in por_codigo and b in por_codigo, (maiuscula, minuscula, hex(a), hex(b))
        assert por_codigo[a].lower() == por_codigo[b], (maiuscula, minuscula, por_codigo[a], por_codigo[b])
    # os quatro glifos do Hack 7, pelo nome do charmap
    assert (glifos["Ã"], glifos["ã"], glifos["Õ"], glifos["õ"]) == (0x42, 0x40, 0x43, 0x41)
    for nome_aba in ("EXPLORAÇÃO", "HISTÓRIA", "BATALHA", "CAPTURA", "TREINO"):
        assert all(c in glifos for c in nome_aba.lower()), nome_aba


def test_dinheiro_mostra_progresso():
    """Pendência da Task 3: o Milionário mostra "₽123.456/999.999" (cabe: o nome é curto e a tela alinha o
    progresso à direita, depois do nome)."""
    corpo = _corpo(_ler(CONQ_C), "Conquistas_Progresso")
    assert "case CONQ_TIPO_DINHEIRO:" in corpo and "GetMoney(&gSaveBlock1Ptr->money)" in corpo
    dados = json.loads(_ler(JSON_PATH))
    dinheiro = next(c for c in dados["conquistas"] if c["tipo"] == "DINHEIRO")
    nome = _medir(dinheiro["nome"])
    progresso = _medir("¥999.999/999.999")
    assert 16 + nome + 8 + progresso <= 222, (nome, progresso)


def test_cabem_os_nomes_e_o_progresso():
    """Cada linha: ícone, nome (até CONQ_NOME_LARGURA) e o progresso alinhado à direita até x = 222 (a coluna das
    setas de rolagem fica depois)."""
    dados = json.loads(_ler(JSON_PATH))
    for c in dados["conquistas"]:
        if not c.get("ativa", True):
            continue
        nome = c["nome"].replace("{N}", "300")
        if c.get("degraus"):
            meta = max(c["degraus"])
        elif c["tipo"] in ("FLAGS_TODAS", "GAME_STAT"):
            meta = c["param2"]
        elif c["tipo"] in ("DEX_KANTO", "DEX_NACIONAL", "DINHEIRO"):
            meta = c["param"]
        elif c["tipo"] == "DEX_TODOS":
            meta = len(c["lista"])
        else:
            continue   # sim/não: só ✓ ou ☐
        maior = str(meta)
        if len(maior) >= 4:
            maior = f"{int(maior):,}".replace(",", ".")
        prog = "¥" * (c["tipo"] == "DINHEIRO") + f"{maior}/{maior}"
        assert 16 + _medir(nome) + 8 + _medir(prog) <= 222, (c["id"], nome, prog)


def test_abas_cabem_em_font_small():
    """As 5 abas cabem juntas no cabeçalho (232 px entre as setas); a tela confere de novo em tempo de execução."""
    dados = json.loads(_ler(JSON_PATH))
    larguras = [_medir(a["nome"], "small") for a in dados["abas"]]
    m = re.search(r"#define ABA_PAD\s+(\d+)", _ler(TELA_C))
    assert m
    assert sum(larguras) + 2 * int(m.group(1)) * len(larguras) <= 232 - 16, larguras


def test_textos_da_tela_e_regra():
    fonte = _ler(STRINGS_C)
    textos = {m.group(1): m.group(2) for m in re.finditer(r'const u8 (gText_ConqTela_\w+)\[\]\s*=\s*_\("(.*?)"\);',
                                                           fonte)}
    assert set(textos) >= {"gText_ConqTela_DicaCartao", "gText_ConqTela_Rodape"}, textos
    h = _ler(REPO_ROOT / "include" / "strings.h")
    for nome in textos:
        assert f"extern const u8 {nome}[];" in h, nome
    regra = check_text.rule_for("src/strings.c", "gText_ConqTela_Rodape")
    assert regra is not None and regra.px is not None and regra.lines == 1, regra
    # o rodapé com o pior caso ("Exploração: 99 de 99") cabe antes da barra
    rodape = textos["gText_ConqTela_Rodape"].replace("{STR_VAR_1}", "Exploração").replace("{STR_VAR_2}", "99") \
        .replace("{STR_VAR_3}", "99")
    assert _medir(rodape) <= regra.px, rodape


def test_citacoes_dos_buffers_apontam_para_quem_enche():
    """As exceções de VAR_CONTENTS que citam a tela apontam para as linhas que enchem aquele buffer
    (STR_VAR_n → gStringVarn): a citação não fica velha quando a tela cresce."""
    from esteira.janelas_uso import VAR_CONTENTS
    linhas = _ler(TELA_C).splitlines()
    vistas = 0
    for vc in VAR_CONTENTS:
        for primeira, ultima in re.findall(r"src/conquistas_tela\.c:(\d+)(?:-(\d+))?", vc.source):
            trecho = linhas[int(primeira) - 1:int(ultima or primeira)]
            buffer = "gStringVar" + vc.var.rsplit("_", 1)[1]
            assert any(re.search(rf"\b{buffer}\b", l) for l in trecho), (vc.label, vc.var, primeira, trecho)
            vistas += 1
    assert vistas >= 6, vistas   # rodapé (2), tempo, turnos e os dois do MVP


def test_icones():
    png = Image.open(GFX / "icones.png")
    assert png.mode == "P" and png.size == (32, 8), (png.mode, png.size)
    assert max(png.tobytes()) < 16
    pal = (GFX / "icones.pal").read_bytes()
    assert pal.startswith(b"JASC-PAL\r\n0100\r\n16\r\n") and pal.count(b"\r\n") == 19, pal[:40]
    fonte = _ler(TELA_C)
    assert 'INCBIN_U8("graphics/conquistas/icones.4bpp")' in fonte
    assert 'INCBIN_U16("graphics/conquistas/icones.gbapal")' in fonte


def test_special_e_atalhos():
    specials = re.findall(r"def_special (\w+)", _ler(SPECIALS).split("gSpecialsEnd::")[0])
    # no fim (o POK-42 acrescentou o da Liga depois)
    finais = specials[specials.index("Conquistas_MostrarAviso"):]
    assert finais == ["Conquistas_MostrarAviso", "Conquistas_AbrirTelaDoScript", "ShouldUseLeagueRematchTeams",
                      "BufferRematchTierName", "ShowRematchTierMenu"], finais
    assert hooks.CMD_OPEN_CONQUISTAS == 0xBE and hooks.CMD_CONQ_TELA == 0xBF
    assert callable(hooks.Mailbox.open_conquistas) and callable(hooks.Mailbox.conq_tela)
    corpo = _ler(SRC / "test_hooks.c")
    assert "case TEST_CMD_OPEN_CONQUISTAS:" in corpo and "case TEST_CMD_CONQ_TELA:" in corpo


def test_cenario_e_telas():
    cenario = _ler(CENARIO)
    for grupo in ("tela/abre_e_abas", "tela/lr_sem_ajuda", "tela/rodape", "tela/cartao"):
        assert f'"{grupo}"' in cenario, grupo
    pontos = ("conquistas_historia", "conquistas_batalha", "cartao_dica")
    assert refs.CONQUISTAS_TELA_POINTS[:3] == pontos


# --- Task 8: o modo diário ---------------------------------------------------------------------------------------
STRINGS_DIARIO = {
    "gText_Diario_Titulo": "DIÁRIO DA JORNADA",
    "gText_Diario_Vazio": "Nenhuma batalha marcante ainda.",
    "gText_Diario_Venceu": "VENCEU",
    "gText_Diario_Capturado": "CAPTURADO",
    "gText_Diario_Derrotou": "DERROTOU",
    "gText_Diario_Separador": " - ",
    "gText_Diario_TempoTurnos": "Tempo: {STR_VAR_1}   Turnos: {STR_VAR_2}",
    "gText_Diario_Time": "Time:",
    "gText_Diario_Nivel": " nv",
    "gText_Diario_MvpUm": "MVP: {STR_VAR_1} ({STR_VAR_2} nocaute)",
    "gText_Diario_MvpVarios": "MVP: {STR_VAR_1} ({STR_VAR_2} nocautes)",
}


def _define(nome: str) -> int:
    m = re.search(rf"^#define {nome}\s+(\d+)\b", _ler(TELA_C), re.M)
    assert m, f"#define {nome} não encontrado em conquistas_tela.c"
    return int(m.group(1))


def _especies() -> list[tuple[str, str]]:
    return re.findall(r'\[SPECIES_(\w+)\] = _\("(.*?)"\)', _ler(SRC / "data" / "text" / "species_names.h"))


def test_textos_do_diario():
    fonte = _ler(STRINGS_C)
    textos = {m.group(1): m.group(2) for m in re.finditer(r'const u8 (gText_Diario_\w+)\[\]\s*=\s*_\("(.*?)"\);',
                                                           fonte)}
    assert textos == STRINGS_DIARIO, textos
    h = _ler(REPO_ROOT / "include" / "strings.h")
    for nome in textos:
        assert f"extern const u8 {nome}[];" in h, nome
    # cada texto tem regra própria na checagem (nenhum cai no "by_usage") e cita a constante da tela
    for nome in textos:
        regra = check_text.rule_for("src/strings.c", nome)
        assert regra is not None and regra.px is not None and not regra.by_usage and regra.lines == 1, (nome, regra)
        citacoes = re.findall(r"((?:src|include)/[\w./-]+):(\d+)(?:-(\d+))?", regra.source)
        assert citacoes, (nome, regra.source)
        for caminho, primeira, _ in citacoes:
            assert caminho == "src/conquistas_tela.c", (nome, regra.source)
            linha = _ler(REPO_ROOT / caminho).splitlines()[int(primeira) - 1]
            assert re.search(r"#define \w+", linha), (nome, primeira, linha)


def _quebra_time(tokens: list[str], largura: int) -> list[str]:
    """A quebra de DesenharDiarioTime: "Time:" e os tokens "ESPÉCIE nvN" (vírgula depois de todos menos o último),
    um espaço entre eles; o token que estoura a largura abre a linha seguinte."""
    linhas, atual = [], STRINGS_DIARIO["gText_Diario_Time"]
    for i, token in enumerate(tokens):
        t = token + ("," if i + 1 < len(tokens) else "")
        candidata = atual + " " + t
        if _medir(candidata, "small") > largura:
            linhas.append(atual)
            atual = t
        else:
            atual = candidata
    linhas.append(atual)
    return linhas


def test_larguras_diario():
    """O pior caso das linhas do diário cabe na janela: título, vazio, resultado, "hh:mm" até o teto do save
    ("1092:15" = 65535 minutos), cabeçalho nome + local, "Tempo: ... Turnos: 255", o MVP (nome de 10 letras, 255
    nocautes) e o time de 6 com a espécie mais larga em nv100 (quebra por largura, até DETALHE_TIME_LINHAS)."""
    largura = _define("TELA_TEXTO_LARGURA")
    assert largura <= LARGURA_TELA - 8
    assert _medir(STRINGS_DIARIO["gText_Diario_Titulo"]) <= largura
    assert _medir(STRINGS_DIARIO["gText_Diario_Vazio"]) <= largura
    for nome in ("Venceu", "Capturado", "Derrotou"):
        assert _medir(STRINGS_DIARIO[f"gText_Diario_{nome}"]) <= _define("RESULTADO_LARGURA"), nome
    # a lista: "hh:mm" | nome | resultado, sem encostar um no outro
    hora = _medir("1092:15")
    assert _define("DIARIO_HORA_X") + hora + 4 <= _define("DIARIO_NOME_X"), hora
    dados = json.loads(_ler(JSON_PATH))
    nomes = [_medir(e["nome"]) for e in dados["diario"]]
    locais = [_medir(e["local"]) for e in dados["diario"]]
    assert _define("DIARIO_NOME_X") + max(nomes) + 8 <= _define("PROGRESSO_FIM") - _define("RESULTADO_LARGURA")
    # o cabeçalho: nome + " - " + local (o pior de cada lado)
    separador = _medir(STRINGS_DIARIO["gText_Diario_Separador"])
    assert max(nomes) + separador + max(locais) <= largura, (max(nomes), separador, max(locais))
    # "Tempo: 1092:15   Turnos: 255" com o pior tempo (65535 min) e o teto de turnos
    tempo = STRINGS_DIARIO["gText_Diario_TempoTurnos"].replace("{STR_VAR_1}", "1092:15").replace("{STR_VAR_2}", "255")
    assert _medir(tempo, "small") <= largura, tempo
    assert _medir("Tempo: 999:59   Turnos: 255", "small") <= largura
    # MVP: a espécie mais larga (small), 255 nocautes
    especies = _especies()
    pior_nome = max(especies, key=lambda e: _medir(e[1], "small"))[1]
    mvp = STRINGS_DIARIO["gText_Diario_MvpVarios"].replace("{STR_VAR_1}", pior_nome).replace("{STR_VAR_2}", "255")
    assert _medir(mvp, "small") <= largura, mvp
    # o time: 6 x espécie mais larga em nv100, na quebra gulosa da tela (rótulo na 1ª linha, "," entre eles)
    token = pior_nome + STRINGS_DIARIO["gText_Diario_Nivel"] + "100"
    rotulo = STRINGS_DIARIO["gText_Diario_Time"]
    linhas = _quebra_time([token] * 6, largura)
    assert all(_medir(l, "small") <= largura for l in linhas), linhas
    maximo = _define("DETALHE_TIME_LINHAS")
    assert len(linhas) <= maximo, (len(linhas), linhas)
    # as 2 linhas do brief não cabem no pior caso real (6 x 50 px + níveis > 2 x 232 px): o time ganha a 3ª linha
    assert maximo == 3 and len(linhas) == 3, linhas
    # cabe na janela: cabeçalho (normal) + tempo + time + MVP, em passo de DETALHE_PASSO
    altura = _define("DETALHE_ALTURA")
    assert _define("DETALHE_CABECALHO_Y") + 16 + _define("DETALHE_PASSO") * (1 + maximo + 1) <= altura
    # um time médio de 6 (as fotos diario_rolado e diario_detalhe_sem_mvp): a mesma quebra palavra a palavra dá 3 linhas
    # (medir o comprimento total contra 2 x a largura engana: a quebra só acontece entre Pokémon)
    medios = ["BLASTOISE nv50", "PIDGEOT nv46", "ALAKAZAM nv48", "PIKACHU nv40", "SNORLAX nv52", "LAPRAS nv50"]
    linhas_medio = _quebra_time(medios, largura)
    assert len(linhas_medio) == 3, linhas_medio
    # 3 Pokémon de nomes médios ainda cabem em 2 linhas
    assert len(_quebra_time(["WARTORTLE nv21", "PIDGEOTTO nv19", "RATTATA nv18"], largura)) == 2
    # a simulação é a da tela: o time vai em tokens "ESPÉCIE nvN" com vírgula, o rótulo só na 1ª linha
    assert "DesenharDiarioTime" in _ler(TELA_C) and "CHAR_COMMA" in _corpo(_ler(TELA_C), "DesenharDiarioTime")


def test_modo_diario_no_c():
    fonte = _ler(TELA_C)
    sem = _sem_comentarios(fonte)
    # as duas funções do diário (Task 5) são lidas pela tela
    for chamada in ("Diario_ListarEmOrdem(", "Diario_GetEntrada(", "gDiarioEventos["):
        assert chamada in sem, chamada
    for tipo in ("DIARIO_VENCEU", "DIARIO_CAPTURADO", "DIARIO_DERROTOU"):
        assert tipo in sem, tipo
    for texto in STRINGS_DIARIO:
        assert texto in sem, texto
    # modelo: cursor de verdade, MVP só com nocaute (0xFF = nenhum)
    for token in ("u8 dCursor;", "u8 dTopo;", "u8 dN;", "u8 evts[DIARIO_EVT_COUNT];"):
        assert token in sem, token
    detalhe = _corpo(fonte, "DesenharDiarioDetalhe")
    assert "e->mvp != 0xFF && e->mvp < PARTY_SIZE && e->mvp < e->tamanhoTime" in detalhe and "gText_Diario_MvpUm" in detalhe and "gText_Diario_MvpVarios" in detalhe
    assert "gText_Diario_TempoTurnos" in detalhe and "gDiarioEventos[" in detalhe
    lista = _corpo(fonte, "DesenharDiarioLista")
    assert "sText_SetaCima" in lista and "sText_SetaBaixo" in lista, "▲▼ quando há mais linhas"
    assert "gText_Diario_Vazio" in lista
    # SELECT alterna (nas duas direções), preservando cursor e aba; as janelas do outro modo são recriadas
    troca = _corpo(fonte, "TrocarModo")
    assert "RemoveWindow(" in troca and "AddWindow(" in troca and "t->modo ^= 1" in troca
    # AddWindow pode falhar (0xFF): a tela sai com segurança em vez de desenhar com tileData NULL
    assert "== 0xFF" in troca and "FASE_SAIR" in troca and troca.index("FASE_SAIR") < troca.index("DesenharTudo(t);")
    assert "SELECT_BUTTON" in _corpo(fonte, "Task_ConquistasTela_Input")
    # o diário não anda além das pontas (sem dar a volta) e rola quando o cursor sai da janela
    diario = _corpo(fonte, "Input_Diario")
    assert "t->dCursor + 1 < t->dN" in diario and "t->dCursor > 0" in diario
    assert "t->dTopo" in diario
    # a entrada nova abre no modo certo (0 conquistas, 1 diário): as janelas do 1º desenho já são as dele
    video = _corpo(fonte, "IniciarVideo")
    assert "t->modo" in video and "InitWindows(" in video
    assert "Diario_Montar(t);" in _corpo(fonte, "Task_ConquistasTela_Montar")


def test_hora_formatada_sem_teto():
    """"hh:mm" com horas sem teto ("123:45"; o save guarda até 65535 minutos = 1092:15) e minutos com 2 dígitos."""
    corpo = _corpo(_ler(TELA_C), "FormatarTempo")
    assert "/ 60" in corpo and "% 60" in corpo
    assert "STR_CONV_MODE_LEADING_ZEROS, 2" in corpo, "minutos com 2 dígitos"
    assert "STR_CONV_MODE_LEFT_ALIGN, 4" in corpo, "horas até 4 dígitos (1092)"


def test_estado_do_diario_e_atalho():
    assert callable(hooks.Mailbox.conq_tela_diario)
    h = _ler(REPO_ROOT / "include" / "test_hooks.h")
    assert "arg0 = 1" in h.split("TEST_CMD_CONQ_TELA,")[1].split("\n")[0], "o enum documenta o arg0 do diário"
    assert "Conquistas_TestGetDiario" in _ler(CONQ_H)


def test_pack_da_entrada_do_diario():
    from esteira import conquistas as cq
    e = {"minutos": 1234, "turnos": 7, "resultado": cq.DIARIO_CAPTURADO, "ordem": 3, "mvp": 0xFF, "mvpNocautes": 0,
         "tamanhoTime": 2, "time": [(150, 70), (6, 100)]}
    raw = cq.pack_entrada(e)
    assert len(raw) == cq.DIARIO_ENTRADA_SIZE == 20
    assert cq.parse_entrada(raw) == e
    assert raw[:2] == (1234).to_bytes(2, "little") and raw[4] == 3


def test_cenario_do_diario():
    cenario = _ler(CENARIO)
    for grupo in ("diario_tela/lista_em_ordem", "diario_tela/vazio", "diario_tela/select_alterna",
                  "diario_tela/varias_entradas", "tela/ajuda_anterior"):
        assert f'"{grupo}"' in cenario, grupo
    fotos = ("diario_lista", "diario_detalhe", "diario_vazio", "diario_varias", "diario_rolado",
             "diario_detalhe_mvp", "diario_detalhe_sem_mvp", "diario_time6")
    for foto in fotos:
        assert f'"{foto}"' in cenario, foto
    pontos = refs.CONQUISTAS_TELA_POINTS
    assert pontos[:3] == ("conquistas_historia", "conquistas_batalha", "cartao_dica"), pontos
    assert set(pontos[3:]) == set(fotos), pontos
    # depois deles, só os das revanches (POK-42), os do DexNav (POK-47) e os do seguidor (POK-48)
    fim = (len(refs.SHARED_POINTS) - len(refs.REVANCHES_POINTS) - len(refs.DEXNAV_POINTS)
           - len(refs.SEGUIDOR_POINTS) - len(refs.POKERUS_POINTS))
    assert refs.SHARED_POINTS[fim - len(pontos):fim] == pontos


def test_foto_do_cartao_nao_varia_com_o_relogio():
    """O cartão mostra o tempo de jogo e os dois-pontos piscam: o ponto de referência `cartao_dica` é só a faixa da
    dica (recorte fixo); o cartão inteiro, para os olhos, sai em `cartao_com_dica` (fora das referências)."""
    cenario = _ler(CENARIO)
    corpo = re.search(r"    def _cartao\(self\).*?(?=\n    def )", cenario, re.S).group(0)
    assert "CARTAO_DICA_RECORTE" in corpo and '"cartao_com_dica"' in corpo and '"cartao_dica"' in corpo
    m = re.search(r"CARTAO_DICA_RECORTE\s*=\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", cenario)
    assert m, "recorte (esquerda, topo, direita, base) da faixa da dica"
    esq, topo, dir_, base = map(int, m.groups())
    # abaixo do tempo de jogo (a linha "Tempo" fica acima de y = 112) e dentro da tela
    assert 0 <= esq < dir_ <= LARGURA_TELA and 112 < topo < base <= 160, (esq, topo, dir_, base)


def test_tela_checa_o_estado_ao_abrir():
    """A checagem do campo é a cada 32 quadros: a tela roda a dela antes de montar a lista, senão uma conquista ganha
    há poucos quadros apareceria pendente (o cenário confere no grupo tela/checa_ao_abrir)."""
    corpo = _corpo(_ler(TELA_C), "Conquistas_AbrirTela")
    assert "Conquistas_ChecarEstado();" in corpo
    assert corpo.index("Conquistas_ChecarEstado();") < corpo.index("SetMainCallback2(CB2_ConquistasTela_Montar)")
    assert corpo.index("Conquistas_ChecarEstado();") < corpo.index("CreateTask(Task_ConquistasTela")
    assert '"tela/checa_ao_abrir"' in _ler(REPO_ROOT / "test" / "esteira" / "scenarios" / "full_conquistas.py")
