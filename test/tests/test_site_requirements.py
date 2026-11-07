"""tools/site/requirements.txt cobre todo módulo de terceiros importado pelo gerador (POK-22)."""
import ast
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SITE = RAIZ / "tools" / "site"
# nome do import -> nome do pacote no PyPI
PACOTES = {"PIL": "pillow", "numpy": "numpy"}


def _importados():
    nomes = {}
    for arq in SITE.glob("*.py"):
        for no in ast.walk(ast.parse(arq.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Import):
                mods = [a.name for a in no.names]
            elif isinstance(no, ast.ImportFrom) and no.level == 0 and no.module:
                mods = [no.module]
            else:
                continue
            for m in mods:
                nomes.setdefault(m.split(".")[0], arq.name)
    return nomes


def _requirements():
    linhas = (SITE / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return {re.split(r"[<>=!~ ;\[]", l.strip(), maxsplit=1)[0].lower() for l in linhas if l.strip() and not l.startswith("#")}


def test_todo_modulo_de_terceiros_esta_no_requirements():
    locais = {p.stem for p in SITE.glob("*.py")}
    terceiros = {m: a for m, a in _importados().items()
                 if m not in sys.stdlib_module_names and m not in locais and m != "__future__"}
    assert terceiros, "esperava ao menos PIL e numpy"
    pedidos = _requirements()
    for modulo, arquivo in terceiros.items():
        assert modulo in PACOTES, f"{arquivo} importa {modulo}: mapeie o pacote em PACOTES"
        assert PACOTES[modulo] in pedidos, f"{modulo} ({arquivo}) falta em tools/site/requirements.txt"
