"""Modo completo: conquistas e diário de batalhas (POK-44), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). Os atalhos do bloco
0xB0 (include/test_hooks.h) leem e montam o estado no save; as áreas são lidas também direto da RAM
(`gSaveBlock1Ptr->conquistas` em +0x348C, `gSaveBlock2Ptr->diario` em +0xB20):

- `save/jogo_novo`: o diário com lixo e `conq_reset(True)` (Conquistas_IniciarJogoNovo, o que o
  NewGameInitData chama logo depois do ClearSav1) → marcador "CQD1", versão 1, origem jogo novo,
  `adiadoNoMapa` 0xFFFF, todos os estados pendentes, nada entregue, contadores e diário zerados;
- `save/antigo_sem_marcador`: `conq_reset(False)` (as duas áreas zeradas, como em todo save de antes
  das conquistas) → magic 0, e a checagem (`conq_checar`) não quebra;
- `save/num_invalido`: um `num` fora da tabela devolve 0xFFFFFFFF.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only conquistas
Numa janela, em tempo real: `make test-watch CENARIO=conquistas`.
"""

import sys

from .. import conquistas as cq
from ..hooks import CMD_CONQ_ESTADO, NO_RESULT, Mailbox
from . import ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

SB1_CONQUISTAS, SB2_DIARIO = 0x348C, 0xB20
CONQ_SAVE_SIZE, DIARIO_SAVE_SIZE = 400, 0x400
ADIADO_NO_MAPA = 0x2C   # offset de adiadoNoMapa em struct ConquistasSave


class ConquistasScenario(CatchSaveScenario):
    def _sb(self, n: int) -> int:
        return self.emu.read_u32(self.game.syms.addr(f"gSaveBlock{n}Ptr"))

    def _conq_raw(self) -> bytes:
        return self.emu.read(self._sb(1) + SB1_CONQUISTAS, CONQ_SAVE_SIZE)

    def _diario_raw(self) -> bytes:
        return self.emu.read(self._sb(2) + SB2_DIARIO, DIARIO_SAVE_SIZE)

    # --- passos ------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="conquistas_continue")
        magic = self.box.conq_contador(3)
        return f"CONTINUAR com o save do modo rápido; magic do save = {magic:#010x}"

    def _jogo_novo(self) -> str:
        # lixo nas duas áreas: o jogo novo zera tudo (o de um jogo anterior não sobrevive)
        self.emu.write(self._sb(2) + SB2_DIARIO, bytes([0x5A]) * 64)
        self.emu.write(self._sb(1) + SB1_CONQUISTAS + 8, bytes([0xA5]) * 36)
        magic = self.box.conq_reset(True)
        assert magic == cq.CONQ_MAGIC == self.box.conq_contador(3), f"magic = {magic:#x}"
        assert self.box.conq_contador(2) == cq.CONQ_ORIGEM_JOGO_NOVO, "origem | resumoPendente"
        assert self.box.conq_contador(0) == 0 and self.box.conq_contador(1) == 0, "contadores"
        raw = self._conq_raw()
        assert raw[4] == 1 and not any(raw[5:8]), f"versão/origem/resumo/livre0 = {raw[4:8].hex()}"
        assert int.from_bytes(raw[ADIADO_NO_MAPA:ADIADO_NO_MAPA + 2], "little") == 0xFFFF, "adiadoNoMapa"
        assert not any(raw[8:ADIADO_NO_MAPA]) and not any(raw[ADIADO_NO_MAPA + 2:]), "área com lixo"
        estados = {n: self.box.conq_estado(n) for n in range(len(cq.dados()["conquistas"]))}
        assert all(e == (0, 0, 0, 0) for e in estados.values()), {n: e for n, e in estados.items() if any(e)}
        diario = self._diario_raw()
        assert diario[1] == 1 and not any(diario[:1]) and not any(diario[2:]), "diário não zerado"
        return f"magic CQD1, {len(estados)} conquistas pendentes, diário zerado"

    def _antigo(self) -> str:
        magic = self.box.conq_reset(False)
        assert magic == 0 == self.box.conq_contador(3), f"magic = {magic:#x}"
        assert not any(self._conq_raw()) and not any(self._diario_raw()), "áreas não zeradas"
        avisos = self.box.conq_checar()
        assert avisos == 0, f"avisos = {avisos}"
        return "save sem marcador: magic 0"

    def _invalido(self) -> str:
        assert self.box.call(CMD_CONQ_ESTADO, 63) == NO_RESULT
        assert self.box.call(CMD_CONQ_ESTADO, 0x100) == NO_RESULT
        return "num 63 e 0x100 → 0xFFFFFFFF"

    def run(self) -> None:
        try:
            self._flow("conquistas: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("save/jogo_novo", self._jogo_novo)
            self.suite.run("save/antigo_sem_marcador", self._antigo)
            self.suite.run("save/num_invalido", self._invalido)
        except Abort:
            pass


def run_full_conquistas(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    ConquistasScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only conquistas ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "conquistas", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
