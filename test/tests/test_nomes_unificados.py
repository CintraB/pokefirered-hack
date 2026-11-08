"""POK-28: o item e o lugar têm um nome só no jogo, no README e na página (Doce Raro, Monte Brasa)."""

from pathlib import Path

from esteira.scenarios import REPO_ROOT

PROIBIDOS = ("Bala Rara", "Monte Ember")
RAIZES = ("src", "data", "include", "site", "README.md")
EXTENSOES = {".inc", ".h", ".c", ".json", ".md", ".s", ".html", ".txt"}


def _arquivos():
    for raiz in RAIZES:
        p = Path(REPO_ROOT) / raiz
        achados = [p] if p.is_file() else sorted(p.rglob("*"))
        for f in achados:
            if f.is_file() and f.suffix in EXTENSOES and "__pycache__" not in f.parts:
                yield f


def test_nomes_unificados():
    achados = []
    for f in _arquivos():
        texto = f.read_text(encoding="utf-8", errors="ignore")
        for n, linha in enumerate(texto.splitlines(), 1):
            achados += [f"{f.relative_to(REPO_ROOT)}:{n}: {nome}" for nome in PROIBIDOS if nome in linha]
    assert not achados, "nome fora do glossário:\n" + "\n".join(achados)
