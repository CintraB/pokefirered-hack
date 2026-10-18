"""Modo completo: relógio do jogo (Hack 7), na build de teste.

O relógio conta os quadros jogados em gSaveBlock2Ptr->gameClockFrames (150 quadros = 1 minuto
do jogo; 0 = 08:00 do dia 0), avançado a cada quadro em que o contador de tempo de jogo não
está parado, inclusive depois de travar em 999:59 (esteira/dia_noite.py tem as regras). Sessão própria da ROM de teste a partir do .sav do
`captura` (`save_from="captura"`):

1. `relogio/anda`: 1500 quadros parado no campo avançam 10 minutos;
2. `relogio/salva`: relógio acertado no dia 3, 18:30 (atalho SET_CLOCK), salvo pelo menu
   (START > SALVAR), reset e CONTINUAR → o relógio volta como foi salvo (entardecer, dia 3);
3. `relogio/save_antigo`: gameClockFrames = 0 (como num save de antes do relógio), salvo, reset
   e CONTINUAR → 08:00, manhã.

O relógio não para durante o diálogo de salvar nem depois do CONTINUAR, então o valor salvo
fica entre o acertado e o lido logo depois do save, e o lido depois do CONTINUAR passa do salvo
no máximo pelos quadros jogados desde o reset: as checagens usam esses limites exatos, e o
minuto esperado ganha a folga desses quadros (o detalhe mostra quanto foi).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only relogio
"""

import sys

from .. import dia_noite as dn
from ..emu import KEY_B
from ..hooks import Mailbox
from . import ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

GAME_CLOCK_OFFSET = 0x090   # gameClockFrames em struct SaveBlock2 (include/global.h)
WALK_MINUTES = 10
SAVE_DAY, SAVE_MINUTE = 3, 18 * 60 + 30


class ClockScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None

    # --- utilidades ----------------------------------------------------------------
    def _clock_addr(self) -> int:
        return self.emu.read_u32(self.game.syms.addr("gSaveBlock2Ptr")) + GAME_CLOCK_OFFSET

    def _clock_frames(self) -> int:
        return self.emu.read_u32(self._clock_addr())

    @staticmethod
    def _minutes(frames: int) -> int:
        """Minutos desde o começo do dia 0 para um valor de gameClockFrames."""
        return frames // dn.FRAMES_PER_MINUTE + dn.START_MINUTE

    @staticmethod
    def _hhmm(minute: int) -> str:
        return f"{minute // 60:02d}:{minute % 60:02d}"

    def _save_reset_continue(self, set_clock, shot: str) -> dict:
        """`set_clock()` acerta o relógio; salva pelo menu, reseta e dá CONTINUAR. Devolve os
        gameClockFrames acertado, lido logo depois do save e lido depois do CONTINUAR, e os
        quadros jogados desde o reset (o relógio só pode ter andado isso depois do load)."""
        set_clock()
        frames_set = self._clock_frames()
        self._save()
        frames_saved_max = self._clock_frames()
        self.emu.reset()
        self._title_to_continue("tela de título depois do reset", shot=shot)
        # o reset do core zera o contador de quadros: o valor agora é o jogado desde o reset
        # (se um dia não zerar, só fica maior, e o limite afrouxa em vez de dar falso vermelho)
        elapsed = self.emu.frames(1)

        frames_after = self._clock_frames()
        assert frames_set <= frames_after <= frames_saved_max + elapsed, (
            f"gameClockFrames depois do CONTINUAR = {frames_after}, fora de [{frames_set}, "
            f"{frames_saved_max} + {elapsed} quadros desde o reset]: o relógio não veio do save")
        return {"set": frames_set, "saved_max": frames_saved_max, "after": frames_after,
                "elapsed": elapsed}

    def _check_minute(self, got: int, want: int, slack_frames: int) -> int:
        """Minuto do dia lido x esperado, com ±1 e mais a folga dos quadros em que o relógio
        pode ter corrido entre acertar e ler; devolve a diferença."""
        slack = 1 + -(-slack_frames // dn.FRAMES_PER_MINUTE)
        diff = (got - want) % dn.MINUTES_PER_DAY
        assert diff <= slack or diff >= dn.MINUTES_PER_DAY - 1, (
            f"minuto {self._hhmm(got)}, esperava {self._hhmm(want)} (folga de {slack} min)")
        return diff

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="relogio_continue")
        minute, period = self.box.clock_info()
        return (f"CONTINUAR com o save do modo rápido: relógio em {self._hhmm(minute)} "
                f"({dn.PERIOD_NAMES[period]})")

    def _walk(self) -> str:
        before, _ = self.box.clock_info()
        self.emu.frames(dn.FRAMES_PER_MINUTE * WALK_MINUTES)
        after, period = self.box.clock_info()
        advanced = (after - before) % dn.MINUTES_PER_DAY
        assert abs(advanced - WALK_MINUTES) <= 1, (
            f"{dn.FRAMES_PER_MINUTE * WALK_MINUTES} quadros avançaram {advanced} min "
            f"({self._hhmm(before)} → {self._hhmm(after)}), esperava {WALK_MINUTES}")
        assert period == dn.period_at(after), (period, after)
        return (f"{self._hhmm(before)} → {self._hhmm(after)} ({advanced} min em "
                f"{dn.FRAMES_PER_MINUTE * WALK_MINUTES} quadros), {dn.PERIOD_NAMES[period]}")

    def _saved_clock(self) -> str:
        def set_clock() -> None:
            got = self.box.set_clock(SAVE_DAY, SAVE_MINUTE)
            assert got == SAVE_MINUTE, f"SET_CLOCK devolveu {got}, esperava {SAVE_MINUTE}"

        f = self._save_reset_continue(set_clock, "relogio_salva_continue")
        minute, period = self.box.clock_info()
        diff = self._check_minute(minute, SAVE_MINUTE, f["saved_max"] - f["set"] + f["elapsed"])
        assert period == dn.EVENING, f"período {dn.PERIOD_NAMES[period]}, esperava entardecer"
        day = self._minutes(self._clock_frames()) // dn.MINUTES_PER_DAY
        assert day == SAVE_DAY, f"dia {day}, esperava {SAVE_DAY}"
        return (f"acertado dia {SAVE_DAY} {self._hhmm(SAVE_MINUTE)}; depois do CONTINUAR dia "
                f"{day} {self._hhmm(minute)} (+{diff} min: save e CONTINUAR levaram "
                f"{f['saved_max'] - f['set']} + {f['elapsed']} quadros), "
                f"{dn.PERIOD_NAMES[period]}")

    def _old_save(self) -> str:
        def zero_clock() -> None:
            self.emu.write(self._clock_addr(), bytes(4))   # só a ROM de teste pode escrever

        f = self._save_reset_continue(zero_clock, "relogio_save_antigo_continue")
        minute, period = self.box.clock_info()
        diff = self._check_minute(minute, dn.START_MINUTE, f["saved_max"] + f["elapsed"])
        assert period == dn.MORNING, f"período {dn.PERIOD_NAMES[period]}, esperava manhã"
        return (f"gameClockFrames = 0 salvo; depois do CONTINUAR {self._hhmm(minute)} "
                f"(+{diff} min: save e CONTINUAR levaram {f['saved_max']} + {f['elapsed']} "
                f"quadros), {dn.PERIOD_NAMES[period]}")

    # --- Hack 7 frente A: hora no menu Start e aviso de troca de período ------------------
    def _idle(self, frames: int) -> None:
        self.emu.frames(frames)

    def _popup_period(self) -> int:
        return self.emu.read_u8(self.game.syms.addr("gDayNightPopupPeriod"))

    def _clock_text(self) -> str:
        raw = self.emu.read(self.game.syms.addr("gDayNightClockText"), 20)
        return self.game.charmap.decode(bytes(raw))

    def _menu_text(self, minute: int, shot: str | None) -> str:
        """Acerta o relógio, abre o menu Start e lê o que a janela da hora imprimiu (pode ter
        andado 1 minuto entre acertar e desenhar)."""
        self.box.set_clock(1, minute)
        self.menu.open_start_menu()
        try:
            if shot:
                self._shot(shot)
            want = {f"{m // 60:02d}:{m % 60:02d} " + dn.PERIOD_NAMES[dn.period_at(m)].capitalize()
                    for m in (minute, minute + 1)}
            got = self._clock_text()
            assert got in want, f"janela da hora imprimiu {got!r}, esperava um de {sorted(want)}"
        finally:
            self.menu.close_start_menu()
        return got

    def _clock_menu(self) -> str:
        a = self._menu_text(18 * 60 + 30, "relogio_menu")
        b = self._menu_text(7 * 60, None)
        return f"{a!r} e {b!r}"

    def _notice_night(self) -> str:
        self.box.set_clock(1, 19 * 60 + 30)
        self._idle(400)   # o aviso do entardecer passa e o período fica registrado
        self.box.set_clock(1, 19 * 60 + 59)
        spent = 0
        while self._popup_period() != dn.NIGHT:
            assert spent < 700, f"sem aviso da noite: gDayNightPopupPeriod = {self._popup_period():#x}"
            self._idle(10)
            spent += 10
        self._idle(90)
        self._shot("relogio_aviso_noite")
        return f"aviso da noite {spent} quadros depois de 19:59"

    def _notice_in_menu(self) -> str:
        self.box.set_clock(1, 9 * 60)
        self._idle(400)
        assert self._popup_period() == dn.MORNING, f"período {self._popup_period():#x}"
        self.menu.open_start_menu()
        self.box.set_clock(1, 9 * 60 + 59)
        self._idle(dn.FRAMES_PER_MINUTE + 100)
        assert self._popup_period() == dn.MORNING, "aviso com o menu Start aberto"
        self.menu.close_start_menu()
        spent = 0
        while self._popup_period() != dn.AFTERNOON:
            assert spent < 300, "sem aviso da tarde depois de fechar o menu"
            self._idle(10)
            spent += 10
        return f"nenhum aviso no menu; tarde avisada {spent} quadros depois de fechar"

    def _save_cancel(self) -> str:
        """START > SALVAR > cancelar (B) várias vezes: a janela da hora é recriada a cada volta
        sem vazar janelas (o id fica estável e a janela está aberta com o menu)."""
        syms = self.game.syms
        ids = []
        self.menu.open_start_menu()
        for i in range(4):
            self.menu.choose(4)   # STARTMENU_SAVE
            self._idle(90)
            self.ctl.press_until(KEY_B, lambda: self.menu.accepting_input() and self.menu.start_menu_open(),
                                 f"menu START depois de cancelar o save ({i})", tries=10, wait=60)
            assert self.emu.read_u8(syms.addr("sClockWindowOpen")) == 1, "janela da hora fechada"
            ids.append(self.emu.read_u8(syms.addr("sClockWindowId")))
        assert len(set(ids)) == 1, f"id da janela da hora mudou entre os cancelamentos: {ids}"
        self.menu.close_start_menu()
        assert self.emu.read_u8(syms.addr("sClockWindowOpen")) == 0, "janela da hora vazou"
        return f"4 cancelamentos do save, janela da hora sempre no id {ids[0]}"

    def _no_notice_on_enter(self) -> str:
        def set_clock() -> None:
            self.box.set_clock(1, 20 * 60 + 30)

        self._save_reset_continue(set_clock, "relogio_sem_aviso_continue")
        self._idle(300)
        got = self._popup_period()
        assert got == 0xFF, f"aviso ao entrar no campo: gDayNightPopupPeriod = {got:#x}"
        return "300 quadros no campo depois do CONTINUAR às 20:30, sem aviso"

    def run(self) -> None:
        try:
            self._flow("relogio: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("relogio/anda: 1500 quadros no campo = 10 minutos", self._walk)
            self._flow("relogio/salva: dia 3 18:30 sobrevive a salvar, reset e CONTINUAR",
                       self._saved_clock)
            self._flow("relogio/save_antigo: gameClockFrames = 0 começa às 08:00 (manhã)",
                       self._old_save)
            self._flow("relogio/menu: hora no menu Start", self._clock_menu)
            self._flow("relogio/aviso: aviso da noite com o jogador livre", self._notice_night)
            self._flow("relogio/aviso_no_menu: sem aviso com o menu aberto", self._notice_in_menu)
            self._flow("relogio/save_cancelado: janela da hora sem vazar", self._save_cancel)
            self._flow("relogio/sem_aviso_ao_entrar: CONTINUAR às 20:30 não avisa",
                       self._no_notice_on_enter)
        except Abort:
            pass


def run_full_clock(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    ClockScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only relogio ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "relogio", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
