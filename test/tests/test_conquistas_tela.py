"""Conquistas e diário de batalhas (POK-44), Task 7: a tela de conquistas e o botão no Cartão de Treinador.

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
    assert "if (!sTrainerCardDataPtr->isLink)" in dica, "a dica só no cartão do próprio jogador"
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
    assert "gHelpSystemEnabled = FALSE;" in entrada
    saida = _corpo(fonte, "Task_ConquistasTela_Sair")
    assert saida.index("HelpSystem_Enable();") < saida.index("SetMainCallback2(voltar);")
    assert "Free(t);" in saida and "FreeAllWindowBuffers();" in saida


def test_memoria_no_heap():
    fonte = _sem_comentarios(_ler(TELA_C))
    assert "EWRAM_DATA" not in fonte and "IWRAM_DATA" not in fonte
    # nenhuma variável global de arquivo (o ponteiro do bloco fica na task)
    globais = re.findall(r"^static (?!const\b)[^(=;]*[;=]", fonte, re.M)
    assert globais == [], globais
    assert "AllocZeroed(sizeof(*t))" in fonte
    assert "SetWordTaskArg(" in fonte and "GetWordTaskArg(" in fonte


def test_controles():
    corpo = _corpo(_ler(TELA_C), "Task_ConquistasTela_Input")
    for trecho in ("JOY_NEW(B_BUTTON)", "JOY_NEW(L_BUTTON)", "JOY_NEW(R_BUTTON)", "JOY_NEW(SELECT_BUTTON)",
                   "JOY_REPT(DPAD_UP)", "JOY_REPT(DPAD_DOWN)"):
        assert trecho in corpo, trecho
    fonte = _ler(TELA_C)
    trocar = _corpo(fonte, "TrocarAba")
    assert "CONQ_ABAS_COUNT" in trocar, "L/R dão a volta"


def test_estado_da_tela():
    corpo = _corpo(_ler(TELA_C), "Conquistas_TestGetState")
    assert "0xFFFFFFFF" in corpo
    assert re.search(r"modo\s*\|\s*.*aba\s*<<\s*8\s*\|\s*.*topo\s*<<\s*16\s*\|\s*.*inputReady\s*<<\s*24", corpo,
                     re.S), corpo


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
    assert specials[-2:] == ["Conquistas_MostrarAviso", "Conquistas_AbrirTelaDoScript"], specials[-2:]
    assert hooks.CMD_OPEN_CONQUISTAS == 0xBE and hooks.CMD_CONQ_TELA == 0xBF
    assert callable(hooks.Mailbox.open_conquistas) and callable(hooks.Mailbox.conq_tela)
    corpo = _ler(SRC / "test_hooks.c")
    assert "case TEST_CMD_OPEN_CONQUISTAS:" in corpo and "case TEST_CMD_CONQ_TELA:" in corpo


def test_cenario_e_telas():
    cenario = _ler(CENARIO)
    for grupo in ("tela/abre_e_abas", "tela/lr_sem_ajuda", "tela/rodape", "tela/cartao"):
        assert f'"{grupo}"' in cenario, grupo
    pontos = ("conquistas_historia", "conquistas_batalha", "cartao_dica")
    assert refs.SHARED_POINTS[-len(pontos):] == pontos, refs.SHARED_POINTS[-5:]
