"""Resultados de cenário e a Suite que os coleta."""

from dataclasses import dataclass, field
from typing import Callable, Literal


class StepTimeout(Exception):
    """Um passo de controle estourou o tempo-limite; carrega as evidências salvas."""

    def __init__(self, what: str, screenshot_path: str, state_path: str):
        super().__init__(f"tempo esgotado esperando: {what} "
                         f"(screenshot={screenshot_path}, state={state_path})")
        self.what = what
        self.screenshot_path = screenshot_path
        self.state_path = state_path


@dataclass
class Result:
    name: str
    status: Literal["ok", "falha", "aviso"]
    detail: str
    images: list[str] = field(default_factory=list)
    state: str | None = None   # savestate de depuração (StepTimeout), quando houver
    # medição parcial de um cenário dividido em partes (esteira/paralelo.py); o CLI junta as
    # partes e o relatório nunca a mostra
    data: dict | None = None


class Suite:
    def __init__(self) -> None:
        self.results: list[Result] = []

    def add(self, result: Result) -> None:
        self.results.append(result)

    def run(self, name: str, fn: Callable[[], object]) -> Result:
        """Roda `fn`; StepTimeout/AssertionError viram `falha` (com evidências), o resto propaga.

        Se `fn` devolver um str, ele vira o detalhe do resultado `ok`.
        """
        try:
            ret = fn()
        except StepTimeout as exc:
            result = Result(name, "falha", str(exc),
                            [exc.screenshot_path], state=exc.state_path)
        except AssertionError as exc:
            result = Result(name, "falha", f"asserção falhou: {exc}")
        else:
            result = Result(name, "ok", ret if isinstance(ret, str) else "")
        self.add(result)
        return result

    def failed(self) -> bool:
        return any(r.status == "falha" for r in self.results)
