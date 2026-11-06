"""POK-51 (Task 1): estado da Família Sombra. Leitura estática do C, das constantes e dos specials."""

import re

from esteira.scenarios import REPO_ROOT

CONST_H = REPO_ROOT / "include" / "constants" / "familia_sombra.h"
FLAGS_H = (REPO_ROOT / "include" / "constants" / "flags.h").read_text(encoding="utf-8")
VARS_H = (REPO_ROOT / "include" / "constants" / "vars.h").read_text(encoding="utf-8")
SPECIALS = (REPO_ROOT / "data" / "specials.inc").read_text(encoding="utf-8")
FAMILIA_C = (REPO_ROOT / "src" / "familia_sombra.c").read_text(encoding="utf-8")

NOVAS_FLAGS = (
    [f"FLAG_FAMILIA_ITEM_{a}_{n}" for a in range(1, 6) for n in range(1, 4)]
    + ["FLAG_FAMILIA_PEDAGIO_PAGO", "FLAG_FAMILIA_GEMEOS_VENCIDOS"]
    + [f"FLAG_FAMILIA_ROSA_{r}" for r in range(1, 5)]
)
NOVAS_VARS = ["VAR_FAMILIA_OCUPACAO", "VAR_FAMILIA_ESTADO", "VAR_FAMILIA_QUEDA"]


def _defines(text: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"^#define\s+(\w+)\s+(0x[0-9A-Fa-f]+)\b", text, re.M)}


def test_constantes_do_spec():
    text = CONST_H.read_text(encoding="utf-8")
    esperado = {
        "FAMILIA_OCUPACOES_TOTAL": 4, "FAMILIA_OCUPACOES_ATIVAS": 2, "FAMILIA_MEIOS_DIAS_RETORNO": 7,
        "FAMILIA_PEDAGIO": 1000, "FAMILIA_ESTADO_FECHADO": 0, "FAMILIA_ESTADO_ATIVA": 1,
        "FAMILIA_ESTADO_SEM_CHEFE": 2, "FAMILIA_ESTADO_ENCERRADA": 3,
    }
    for nome, valor in esperado.items():
        m = re.search(rf"^#define\s+{nome}\s+(\d+)\b", text, re.M)
        assert m and int(m.group(1)) == valor, nome


def test_ids_novos_livres():
    flags = _defines(FLAGS_H)
    vars_ = _defines(VARS_H)
    for nomes, defs, texto in ((NOVAS_FLAGS, flags, FLAGS_H), (NOVAS_VARS, vars_, VARS_H)):
        ids = []
        for nome in nomes:
            assert nome in defs, nome
            assert re.search(rf"^#define\s+{nome}\s.*// POK-51", texto, re.M), nome
            ids.append(int(defs[nome], 16))
        assert len(set(ids)) == len(ids)
        outros = [int(v, 16) for k, v in defs.items() if k not in nomes]
        assert not set(ids) & set(outros), "colide com um id existente"
    # o bloco de itens é contíguo
    primeira = int(flags["FLAG_FAMILIA_ITEM_1_1"], 16)
    assert [int(flags[f"FLAG_FAMILIA_ITEM_{a}_{n}"], 16) for a in range(1, 6) for n in range(1, 4)] \
        == list(range(primeira, primeira + 15))
    assert re.search(r"^#define\s+FLAG_FAMILIA_ITENS_PRIMEIRA\s+FLAG_FAMILIA_ITEM_1_1\b", FLAGS_H, re.M)
    assert re.search(r"^#define\s+FLAG_FAMILIA_ITENS_ULTIMA\s+FLAG_FAMILIA_ITEM_5_3\b", FLAGS_H, re.M)


def test_ids_novos_nao_sao_usados_por_ninguem_mais():
    """Os ids viraram nomes novos: nenhum nome FLAG_0x4xx/VAR_0x40xx antigo ficou sobrando no código."""
    for nome in ("VAR_0x40ED", "VAR_0x40EE", "VAR_0x40EF"):
        assert nome not in VARS_H


def test_especiais_registrados():
    for nome in ("FamiliaSombra_Atualizar", "FamiliaSombra_ChefeCaiu",
                 "FamiliaSombra_GetEstado", "FamiliaSombra_GetOcupacao"):
        assert re.search(rf"^\s*def_special\s+{nome}\b", SPECIALS, re.M), nome
        assert re.search(rf"\b{nome}\s*\(", FAMILIA_C), nome


def test_meio_dia_usa_relogio():
    m = re.search(r"u16 FamiliaSombra_MeiosDiasAgora\(void\)\s*\{(.*?)\n\}", FAMILIA_C, re.S)
    assert m
    assert "DayNight_GetTotalMinutes()" in m.group(1) and "720" in m.group(1)


def test_regras_do_ciclo():
    atualizar = re.search(r"void FamiliaSombra_Atualizar\(void\)\s*\{(.*?)\n\}", FAMILIA_C, re.S).group(1)
    assert "FLAG_BADGE08_GET" in atualizar
    assert "FAMILIA_MEIOS_DIAS_RETORNO" in atualizar and "FAMILIA_OCUPACOES_ATIVAS" in atualizar
    caiu = re.search(r"void FamiliaSombra_ChefeCaiu\(void\)\s*\{(.*?)\n\}", FAMILIA_C, re.S).group(1)
    assert "VAR_FAMILIA_QUEDA" in caiu and "FAMILIA_ESTADO_SEM_CHEFE" in caiu and "sRosas[ocupacao - 1]" in caiu
    assert "FLAG_FAMILIA_ROSA_1" in FAMILIA_C
    repovoar = re.search(r"void FamiliaSombra_Repovoar\(void\)\s*\{(.*?)\n\}", FAMILIA_C, re.S).group(1)
    assert "FLAG_FAMILIA_GEMEOS_VENCIDOS" in repovoar and "FLAG_FAMILIA_ITENS_PRIMEIRA" in repovoar
    assert "FLAG_FAMILIA_ROSA" not in repovoar and "FLAG_FAMILIA_PEDAGIO_PAGO" not in repovoar
