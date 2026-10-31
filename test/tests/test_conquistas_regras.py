"""Conquistas e diário de batalhas (POK-44), Task 3: as regras de estado e a varredura do save antigo.

A regra de cada tipo mora em `src/conquistas.c` (uma função de avaliação por tipo, despachada por um `switch`
que `Conquistas_ChecarEstado` usa). A varredura de um save sem marcador roda uma vez e é a única que lê o PC.
O comportamento no emulador fica no cenário `conquistas` (grupos `estado/*` e `retro/*`).
"""

import re

from esteira import hooks
from esteira.scenarios import REPO_ROOT

CONQ_C = REPO_ROOT / "src" / "conquistas.c"
CONQ_H = REPO_ROOT / "include" / "conquistas.h"
CONSTS_H = REPO_ROOT / "include" / "constants" / "conquistas.h"
HOOKS_C = REPO_ROOT / "src" / "test_hooks.c"
CENARIO = REPO_ROOT / "test" / "esteira" / "scenarios" / "full_conquistas.py"


def _fonte() -> str:
    return CONQ_C.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w ]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _tipos() -> list[str]:
    return re.findall(r"#define (CONQ_TIPO_\w+)\s", CONSTS_H.read_text(encoding="utf-8"))


def test_interface():
    h = CONQ_H.read_text(encoding="utf-8")
    for proto in ("void Conquistas_ChecarEstado(void);", "void Conquistas_VarrerSaveAntigo(void);",
                  "u8 Conquistas_DegrauAtual(u8 num);",
                  "bool8 Conquistas_Progresso(u8 num, u32 *atual, u32 *meta);",
                  "u8 Conquistas_AvisosPendentes(void);",
                  "void Conquistas_ContarAba(u8 aba, u8 *feitas, u8 *validas);"):
        assert proto in h, proto


def test_cada_tipo_tem_regra():
    """Cada CONQ_TIPO_* menos EVENTO tem `case` no despacho que Conquistas_ChecarEstado usa."""
    fonte = _fonte()
    checar = _corpo(fonte, "Conquistas_ChecarEstado")
    assert "CumpreEstado(" in checar
    despacho = _corpo(fonte, "CumpreEstado")
    tipos = _tipos()
    assert len(tipos) == 13
    for tipo in tipos:
        if tipo == "CONQ_TIPO_EVENTO":
            continue
        assert re.search(rf"case {tipo}:", despacho), tipo


def test_checar_varre_so_sem_marcador():
    checar = _corpo(_fonte(), "Conquistas_ChecarEstado")
    m = re.search(r"if \(sConq->magic != CONQ_MAGIC\)\s*\n\s*Conquistas_VarrerSaveAntigo\(\);", checar)
    assert m, "a varredura entra só sem o marcador"
    assert checar.index("Conquistas_VarrerSaveAntigo") < checar.index("CumpreEstado(")


def test_pc_so_na_varredura():
    """Ler o PC custa caro: só a varredura (uma vez por save) passa por ele, nunca a checagem cadenciada."""
    fonte = _fonte()
    for token in ("GetBoxMonDataAt", "GetBoxedMonPtr", "gPokemonStoragePtr"):
        usos = [nome for nome in re.findall(r"^[\w ]+\b(\w+)\([^;{]*\)\n\{", fonte, re.M)
                if token in _corpo(fonte, nome)]
        assert set(usos) <= {"VarrerTimeEPC"}, (token, usos)
    chamadas = [nome for nome in re.findall(r"^[\w ]+\b(\w+)\([^;{]*\)\n\{", fonte, re.M)
                if "VarrerTimeEPC(" in _corpo(fonte, nome)]
    assert chamadas == ["Conquistas_VarrerSaveAntigo"], chamadas


def test_varredura_grava_marcador_e_resumo():
    varrer = _corpo(_fonte(), "Conquistas_VarrerSaveAntigo")
    for trecho in ("CONQ_MAGIC", "CONQ_ORIGEM_SAVE_ANTIGO", "resumoPendente = TRUE", "adiadoNoMapa = 0xFFFF",
                   "diario.versao = CONQ_VERSAO", "FLAG_SYS_GAME_CLEAR", "TRAINER_FLAGS_START",
                   "CONQ_EVT_RIVAL_TODAS", "CONQ_EVT_ELITE4", "CONQ_EVT_OVO_SHINY", "CONQ_EVT_OVO_6IVS"):
        assert trecho in varrer, trecho


def test_ativas_e_perdidas_fora_da_conta():
    fonte = _fonte()
    assert "gConquistas[num].ativa" in _corpo(fonte, "Ativa")
    contar = _corpo(fonte, "Conquistas_ContarAba")
    assert "Ativa(num)" in contar and "CONQ_PERDIDA" in contar
    for nome in ("Conquistas_ChecarEstado", "Conquistas_VarrerSaveAntigo", "Conquistas_AvisosPendentes",
                 "AplicarEvento"):
        assert "Ativa(num)" in _corpo(fonte, nome), nome


def test_atalhos_ligados():
    corpo = re.search(r"case TEST_CMD_CONQ_CHECAR:(.*?)break;", HOOKS_C.read_text(encoding="utf-8"), re.S).group(1)
    assert "Conquistas_ChecarEstado()" in corpo and "Conquistas_AvisosPendentes()" in corpo
    hooks_c = HOOKS_C.read_text(encoding="utf-8")
    assert "Conquistas_DegrauAtual(num) << 24" in hooks_c
    assert "Conquistas_ContarAba(" in _corpo(hooks_c, "ConqContador")
    assert hooks.CMD_CONQ_APLICAR == 0xB4
    assert callable(hooks.Mailbox.conq_aplicar)


def test_grupos_do_cenario():
    texto = CENARIO.read_text(encoding="utf-8")
    for grupo in ("estado/insignia", "estado/dinheiro", "estado/nivel", "estado/degraus_horas",
                  "estado/conta_aba", "estado/marcar_perder", "retro/save_antigo", "retro/roda_uma_vez"):
        assert f'"{grupo}"' in texto, grupo
