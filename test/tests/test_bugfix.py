"""POK-52: as correções de bugs do jogo original (BUGFIX/UBFIX da pret) ficam sempre ligadas."""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def _makefile():
    return (RAIZ / "Makefile").read_text(encoding="utf-8")


def test_makefile_liga_bugfix_e_ubfix_no_c_e_no_montador():
    mk = _makefile()
    # C e #ifdef em .s/.inc (passam pelo cpp) leem o -D; `.ifdef BUGFIX` dos scripts de evento lê o --defsym
    assert re.search(r"^CPPFLAGS \+= -DBUGFIX -DUBFIX$", mk, re.M)
    assert re.search(r"^ASFLAGS \+= --defsym BUGFIX=1 --defsym UBFIX=1$", mk, re.M)


def test_flags_valem_para_todas_as_builds_nao_so_uma_condicional():
    # as linhas ficam no nível de cima do Makefile (sem recuo), logo depois da definição de CPPFLAGS
    mk = _makefile()
    i_cpp = mk.index("CPPFLAGS := ")
    i_fix = mk.index("CPPFLAGS += -DBUGFIX -DUBFIX")
    entre = mk[i_cpp:i_fix]
    assert "ifeq" not in entre and "ifneq" not in entre


def test_script_do_cassino_usa_o_ifdef_do_montador():
    # o único ponto com `.ifdef` (montador): sem o --defsym a carinha do caça-níquel continua quebrada
    txt = (RAIZ / "data/maps/CeladonCity_GameCorner/scripts.inc").read_text(encoding="utf-8")
    assert ".ifdef BUGFIX" in txt


def test_ultimo_build_da_switch_saiu_com_as_flags():
    log = RAIZ / "build/firered_switch.log"
    if not log.exists():
        pytest.skip("sem build/firered_switch.log (rode make firered_switch)")
    texto = log.read_text(encoding="utf-8", errors="replace")
    if "--defsym" not in texto:
        pytest.skip("log sem as linhas de comando do montador (build parcial)")
    assert "--defsym BUGFIX=1 --defsym UBFIX=1" in texto
