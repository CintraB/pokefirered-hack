"""Os valores copiados à mão em esteira/hooks.py batem com include/test_hooks.h."""

import re

from esteira import hooks
from esteira.scenarios import REPO_ROOT

HEADER = (REPO_ROOT / "include" / "test_hooks.h").read_text(encoding="utf-8")
FIELD_SIZES = {"u32": 4}


def _commands() -> dict[str, int]:
    """TEST_CMD_* de todos os enums (valor = anterior + 1; `= N` explícito recomeça em N)."""
    cmds: dict[str, int] = {}
    for body in re.findall(r"enum\s*\{(.*?)\};", HEADER, re.S):
        body = re.sub(r"//[^\n]*", "", body)
        value = 0
        for entry in (e.strip() for e in body.split(",") if e.strip()):
            m = re.fullmatch(r"(TEST_CMD_\w+)(?:\s*=\s*(0x[0-9A-Fa-f]+|\d+))?", entry)
            assert m, entry
            if m.group(2):
                value = int(m.group(2), 0)
            assert m.group(1) not in cmds and value not in cmds.values(), entry
            cmds[m.group(1)] = value
            value += 1
    return cmds


def _offsets() -> dict[str, int]:
    body = re.search(r"struct TestMailbox\s*\{(.*?)\};", HEADER, re.S).group(1)
    offsets, pos = {}, 0
    for kind, name in re.findall(r"(\w+)\s+(\w+);", body):
        offsets[name] = pos
        pos += FIELD_SIZES[kind]
    return offsets


def test_comandos_batem_com_o_enum():
    cmds = _commands()
    assert cmds["TEST_CMD_NONE"] == 0
    python = {f"TEST_{name}": value for name, value in vars(hooks).items()
              if name.startswith("CMD_")}
    assert python == {k: v for k, v in cmds.items() if k != "TEST_CMD_NONE"}


def test_deslocamentos_da_caixa_batem_com_a_struct():
    offsets = _offsets()
    assert list(offsets) == ["cmd", "arg0", "arg1", "result", "done"]
    assert offsets["cmd"] == 0               # Mailbox.call escreve cmd em addr + 0
    assert (hooks._ARG0, hooks._RESULT, hooks._DONE) == (
        offsets["arg0"], offsets["result"], offsets["done"])
    assert offsets["arg1"] == hooks._ARG0 + 4   # arg0, arg1, result, done num pack "<IIII"


def test_simbolo_da_caixa():
    assert re.search(rf"struct TestMailbox\s+{hooks.MAILBOX_SYMBOL}\s*;", HEADER)
