"""Modo completo: PC do Bill (sistema de armazenamento) no Centro de Viridian.

Só aperta botões e lê memória. Começa do checkpoint `save` (modo rápido: no Centro de
Viridian, time com o inicial e o capturado com apelido) e termina no mesmo Centro, com o
checkpoint `pc`.

1. PC > "PC de alguém" (do BILL depois de conhecê-lo) > DEPOSITAR: o capturado (party()[1])
   vai para a CAIXA 1 — time −1, caixa 1 +1, o mesmo Pokémon (personalidade/OT/apelido);
2. salvar, reset, CONTINUAR: time e caixa 1 iguais aos de antes do reset;
3. PC > RETIRAR: o Pokémon volta ao time e a caixa 1 fica como no início.

Telas (src/pokemon_storage_system_*.c): o menu do PC de armazenamento é a task
Task_PCMainMenu (data[1] = opção, data[0] = estado; 2 = esperando botão); a tela das caixas
troca a função da sua task (Task_PokeStorageMain, Task_OnSelectedMon, Task_DepositMenu,
Task_WithdrawMon, Task_OnBPressed...) e guarda o estado em gStorage->state (1º byte). O cursor
fica em sCursorArea/sCursorPosition.
"""

from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_UP
from . import ScenarioContext
from .base import Abort
from .pc_menu import MULTICHOICE_TASK, PC_MENU_STORAGE, PC_TIMEOUT, PcMenuMixin
from .quick_catch_save import CatchSaveScenario

# Task_PCMainMenu (src/pokemon_storage_system_menu.c): opções e estado
PC_MAIN_TASK = "Task_PCMainMenu"
OPTION_WITHDRAW, OPTION_DEPOSIT = 0, 1
PC_MAIN_STATE, PC_MAIN_OPTION = 0, 1          # data[0] tState, data[1] tSelectedOption
PC_MAIN_READY = 2                             # STATE_HANDLE_INPUT

# tela das caixas (pokemon_storage_system_tasks.c / _data.c)
STORAGE_MAIN = "Task_PokeStorageMain"
STORAGE_SELECTED = "Task_OnSelectedMon"
STORAGE_DEPOSIT = "Task_DepositMenu"
STORAGE_B = "Task_OnBPressed"
SELECTED_MENU_READY = 2                       # Task_OnSelectedMon: HandleMenuInput
DEPOSIT_CHOOSE_BOX = 1                        # Task_DepositMenu: escolhendo a caixa
B_YESNO = 2                                   # Task_OnBPressed: "Continuar mexendo nas caixas?"
CURSOR_AREA_IN_BOX, CURSOR_AREA_IN_PARTY = 0, 1

BOX = 0                                       # CAIXA 1 (sDepositBoxId começa em 0)
STORAGE_TIMEOUT = 1500


class PcScenario(PcMenuMixin, CatchSaveScenario):
    # --- leitura -------------------------------------------------------------------
    def _storage_state(self) -> int:
        return self.emu.read_u8(self.emu.read_u32(self.game.syms.addr("gStorage")))

    def _storage_at(self, task: str, state: int) -> bool:
        return task in self._tasks() and self._storage_state() == state

    def _cursor(self) -> tuple[int, int]:
        syms = self.game.syms
        return (self.emu.read_u8(syms.addr("sCursorArea")),
                self.emu.read_u8(syms.addr("sCursorPosition")))

    def _box(self) -> list:
        return self.game.box_mons(BOX)

    @staticmethod
    def _ident(mon) -> tuple:
        return (mon.personality, mon.ot_id, mon.species, mon.nickname)

    # --- telas ---------------------------------------------------------------------
    def _open_storage(self, option: int) -> None:
        """Liga o PC, entra no PC de armazenamento e abre a tela das caixas em `option`."""
        self._open_pc_menu()
        self._choose_menu_item(PC_MENU_STORAGE)
        main = lambda: (self.game.task_data(PC_MAIN_TASK) or [None])[PC_MAIN_STATE] == PC_MAIN_READY
        self.ctl.advance_text(main, PC_TIMEOUT, "menu do PC de armazenamento")
        option_now = lambda: self.game.task_data(PC_MAIN_TASK)[PC_MAIN_OPTION]
        for _ in range(4):
            cur = option_now()
            if cur == option:
                break
            self.ctl.press_until(KEY_DOWN if option > cur else KEY_UP,
                                 lambda: option_now() != cur, "opção do PC de armazenamento")
        assert option_now() == option, f"opção {option_now()}, esperava {option}"
        self._press(KEY_A)
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_MAIN, 0), STORAGE_TIMEOUT,
                            "tela das caixas")

    def _move_cursor(self, area: int, position: int) -> None:
        for _ in range(8):
            cur = self._cursor()
            if cur == (area, position):
                return
            assert cur[0] == area, f"cursor na área {cur[0]}, esperava {area}"
            self.ctl.press_until(KEY_DOWN if position > cur[1] else KEY_UP,
                                 lambda: self._cursor() != cur, "cursor da tela das caixas")
            self.ctl.wait_until(lambda: self._storage_at(STORAGE_MAIN, 0), 120,
                                "cursor parado na tela das caixas")
        raise self.ctl.timeout_error(f"cursor em {self._cursor()}, esperava {(area, position)}")

    def _select_first_option(self) -> None:
        """A no Pokémon sob o cursor e A na 1ª opção do menu (DEPOSITAR/RETIRAR)."""
        self.ctl.press_until(KEY_A, lambda: self._storage_at(STORAGE_SELECTED, SELECTED_MENU_READY),
                             "menu do Pokémon escolhido", tries=5, wait=60)
        self._press(KEY_A)

    def _close_storage(self) -> None:
        """B, NÃO em "Continuar?", B no menu de armazenamento e B no menu do PC."""
        self.ctl.press_until(KEY_B, lambda: self._storage_at(STORAGE_B, B_YESNO),
                             "pergunta Continuar mexendo nas caixas?", tries=5, wait=60)
        main = lambda: (self.game.task_data(PC_MAIN_TASK) or [None])[PC_MAIN_STATE] == PC_MAIN_READY
        self.ctl.press_until(KEY_B, main, "volta ao menu do PC de armazenamento",
                             tries=3, wait=STORAGE_TIMEOUT // 3)
        self.ctl.press_until(KEY_B, lambda: MULTICHOICE_TASK in self._tasks(),
                             "volta ao menu do PC", tries=5, wait=120)
        self.ctl.press_until(KEY_B, lambda: MULTICHOICE_TASK not in self._tasks(), "PC desligado")
        self.ctl.wait_overworld_idle(PC_TIMEOUT)

    # --- passos --------------------------------------------------------------------
    def _deposit(self) -> str:
        party, box = self.game.party(), self._box()
        assert len(party) == 2, f"time com {len(party)} Pokémon, esperava 2"
        mon = party[1]
        self.measures.update(party0=party, box0=box, deposited=mon)
        self._open_storage(OPTION_DEPOSIT)
        self._move_cursor(CURSOR_AREA_IN_PARTY, 1)
        self._select_first_option()
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_DEPOSIT, DEPOSIT_CHOOSE_BOX),
                            STORAGE_TIMEOUT, "pergunta Depositar em qual caixa?")
        self.measures["pc_shot"] = self._shot("pc_caixa")
        self._press(KEY_A)                         # CAIXA 1 (a 1ª vez o seletor começa nela)
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_MAIN, 0), STORAGE_TIMEOUT,
                            "fim do depósito")
        self._close_storage()
        party_after, box_after = self.game.party(), self._box()
        filled = [m for m in box_after if m is not None]
        before = [m for m in box if m is not None]
        assert len(party_after) == len(party) - 1, (
            f"time {len(party)} -> {len(party_after)}, esperava -1")
        assert len(filled) == len(before) + 1, f"caixa 1 {len(before)} -> {len(filled)}, esperava +1"
        new = [m for m in filled if self._ident(m) not in {self._ident(b) for b in before}]
        assert [self._ident(m) for m in new] == [self._ident(mon)], (
            f"na caixa entrou {[self._ident(m) for m in new]}, esperava {self._ident(mon)}")
        self.measures["after_deposit"] = (self._ident_party(), self._ident_box())
        return (f"{mon.nickname} ({self._species(mon.species)}) depositado: time "
                f"{len(party)} -> {len(party_after)}, caixa 1 {len(before)} -> {len(filled)}")

    def _ident_party(self) -> list:
        return [(self._ident(m), m.level, m.hp, m.max_hp) for m in self.game.party()]

    def _ident_box(self) -> list:
        return [None if m is None else self._ident(m) for m in self._box()]

    def _save_and_continue(self) -> str:
        detail = self._save()
        detail += "; " + self._continue_after_reset(shot="pc_continue")
        party, box = self.measures["after_deposit"]
        assert self._ident_party() == party, (
            f"time depois do reset {self._ident_party()}, antes {party}")
        assert self._ident_box() == box, "caixa 1 diferente depois de reset + CONTINUAR"
        return detail + "; caixa 1 igual"

    def _withdraw(self) -> str:
        mon = self.measures["deposited"]
        box = self._box()
        slot = next(i for i, m in enumerate(box) if m is not None and self._ident(m) == self._ident(mon))
        self._open_storage(OPTION_WITHDRAW)
        self._move_cursor(CURSOR_AREA_IN_BOX, slot)
        self._select_first_option()
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_MAIN, 0), STORAGE_TIMEOUT,
                            "fim da retirada")
        self._close_storage()
        party = self.game.party()
        party0, box0 = self.measures["party0"], self.measures["box0"]
        assert [self._ident(m) for m in party] == [self._ident(m) for m in party0], (
            f"time depois de retirar {[self._ident(m) for m in party]}, "
            f"esperava {[self._ident(m) for m in party0]}")
        assert self._ident_box() == [None if m is None else self._ident(m) for m in box0], (
            "caixa 1 não voltou ao estado do início")
        return f"{mon.nickname} de volta em party()[{len(party) - 1}]; caixa 1 como no início"

    def run(self) -> None:
        try:
            res = self.suite.run("pc: depositar o capturado — time −1, caixa 1 +1", self._deposit)
            if "pc_shot" in self.measures:
                res.images.append(self.measures["pc_shot"])
            if res.status == "falha":
                raise Abort("depositar")
            self._flow("pc: salvar, reset e CONTINUAR mantêm time e caixa 1",
                       self._save_and_continue)
            self._flow("pc: retirar devolve o Pokémon ao time", self._withdraw)
            self.ctl.checkpoint("pc")
        except Abort:
            pass


def run_full_pc(ctx: ScenarioContext) -> None:
    """Roda a partir do checkpoint `save` (Centro de Viridian) já carregado no emulador."""
    PcScenario(ctx).run()
