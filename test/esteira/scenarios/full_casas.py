"""Modo completo: as casas do Cintra (POK-51, partes 2 e 3 do plano das casas), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). O aviso das conquistas fica em
silêncio (ele pausa o campo). As Tasks 9 e 10 acrescentam casos a este cenário.

Task 8 (Rota 6, Mestre dos Golpes). A casa fica no gramado à esquerda do lago (x 6-9, y 27-30, porta em (7, 30)); o
time é um Snorlax nv 50 com um golpe só (os outros três vazios: o tutor aprende direto, sem a pergunta de esquecer) e o
dinheiro vem da escrita direta no save (como full_egg).

- `casas/mestre_ensina`: entra pela porta (tela `casa_rota6_exterior`), fala com o Mestre, a lista dos 15 golpes abre
  (tela `mestre_lista`), ensina Pancada Corporal (¥3.000) e, na mesma conversa, Faca 2 Gumes (mais ¥3.000); as flags de
  "já ensinou" dos tutores originais seguem desligadas;
- `casas/mestre_sem_dinheiro`: com ¥2.999 ele recusa e nada é ensinado nem cobrado;
- `casas/mestre_cancelar_nao_cobra`: cancelar na lista, e escolher o golpe mas cancelar na tela da equipe, não cobram.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only casas
"""

from ..breeding import header_defines
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_UP
from ..game import SB1_MONEY
from ..hooks import CMD_WARP, Mailbox
from ..nav import Navigator
from . import REPO_ROOT, ScenarioContext
from .base import YESNO_TASK, Abort
from .quick_catch_save import CatchSaveScenario

STRING_BYTES = 300                   # gStringVar4
PALETTE_FADE_ACTIVE = 7              # byte de gPaletteFade com o bit `active` (0x80)
BUTTON_WAIT_STATES = {1, 2, 3}       # RENDER_STATE_WAIT/CLEAR/SCROLL_START: o texto espera um botão
LISTA_TASK = "Task_MestreGolpes_Entrada_Input"
PRECO = 3000
DINHEIRO = 10000
NIVEL = 5                            # um Snorlax tão novo ainda tem golpes vagos
TUTOR_BODY_SLAM, TUTOR_DOUBLE_EDGE = 3, 4   # TUTOR_MOVE_* (constants/party_menu.h)
ROTA6_FRENTE_DA_PORTA = (7, 31)      # Route6: o tile abaixo da porta (7, 30)
ROTA6_LONGE = (8, 32)                # Route6: de onde se vê a casa inteira (tela casa_rota6_exterior)
MESTRE_FRENTE = (4, 4)               # Route6_UnusedHouse: o Mestre está em (4, 3)
SCENE_TIMEOUT = 20000


class CasasScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.nav = Navigator(self.ctl)
        self.moves = header_defines(REPO_ROOT, "moves.h")

    # --- leitura --------------------------------------------------------------------
    def _sym(self, name: str) -> int:
        return self.game.syms.addr(name)

    def _rom_text(self, symbol: str) -> str:
        return self.game.charmap.decode(self.emu.read(self._sym(symbol), STRING_BYTES).split(b"\xff")[0])

    def _message(self) -> str:
        """A última caixa de mensagem do campo (gStringVar4)."""
        return self.game.charmap.decode(self.emu.read(self._sym("gStringVar4"), STRING_BYTES).split(b"\xff")[0])

    def _fade_active(self) -> bool:
        return bool(self.emu.read_u8(self._sym("gPaletteFade") + PALETTE_FADE_ACTIVE) & 0x80)

    def _waiting(self) -> bool:
        return not self.game.text_printer_active() or self.game.text_printer_state(0) in BUTTON_WAIT_STATES

    def _move(self, name: str) -> int:
        return self.moves[name]

    def _lead_moves(self) -> list[int]:
        return [m for m in self.game.party()[0].moves if m]

    def _set_money(self, amount: int) -> None:
        """Dinheiro do jogador (u32 XOR encryptionKey): escrita na RAM, só na ROM de teste."""
        self.emu.write(self.game._sb1() + SB1_MONEY, (amount ^ self.game._key()).to_bytes(4, "little"))

    def _settle(self, what: str) -> None:
        self.ctl.wait_overworld_idle(900)
        self.ctl.wait_until(lambda: not self._fade_active(), 300, f"fim do fade: {what}")
        self.emu.frames(4)

    def _warp(self, map_name: str, xy: tuple[int, int]) -> None:
        group, num = self.consts.map(map_name)
        self._settle(f"antes do warp para {map_name}")
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_name}")
        self._settle(f"warp para {map_name}")

    def _at(self, map_name: str) -> bool:
        return self.game.location() == self.consts.map(map_name)

    # --- preparo --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="casas_continue")
        self.box.conq_silencio(True)
        self.box.set_party_mon(0, self.consts.species("SPECIES_SNORLAX"), NIVEL)
        self.box.party_size(1)
        assert len(self._lead_moves()) <= 2, f"o Snorlax nv {NIVEL} já tem {self._lead_moves()}"
        self._set_money(DINHEIRO)
        self.ctl.checkpoint("casas_base")
        return f"CONTINUAR; Snorlax nv {NIVEL} com {len(self._lead_moves())} golpe(s), ¥{DINHEIRO}; savestate casas_base"

    def _restore(self, name: str) -> None:
        self.ctl.restore(name)
        self.emu.frames(12)

    # --- o Mestre -------------------------------------------------------------------
    def _entrar_na_casa(self, shot: str | None = None) -> None:
        """Da Rota 6, pela porta de verdade, até a frente do Mestre."""
        self._warp("MAP_ROUTE6", ROTA6_LONGE)
        if shot:
            self.emu.frames(180)                # o nome da rota some da tela
            self.measures["exterior"] = self._shot(shot)
        assert self.nav.walk_to(*ROTA6_FRENTE_DA_PORTA), f"não chegou à porta: {self.game.player_xy()}"
        self.nav.go_through_warp("up")
        assert self._at("MAP_ROUTE6_UNUSED_HOUSE"), self.game.location()
        assert self.nav.walk_to(*MESTRE_FRENTE), f"não chegou ao Mestre: {self.game.player_xy()}"

    def _falar(self) -> None:
        self.emu.hold(KEY_UP, 4)                # o Mestre bloqueia: só vira para ele
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do Mestre")
        self.ctl.wait_overworld_idle()
        self.emu.press(KEY_A, hold=2, release=8)
        self.ctl.wait_until(self.ctl.script_active, 120, "a fala do Mestre")

    def _cena(self, plano: list[tuple[int | None, int]], shot_lista: str | None = None) -> dict:
        """Roda a conversa até o campo ficar livre. `plano` = uma entrada por abertura da lista: (índice do golpe ou
        None para cancelar com B, tecla na tela da equipe: A escolhe o Pokémon, B desiste). A pergunta "outra técnica?"
        recebe SIM enquanto houver plano e NÃO depois."""
        plano = list(plano)
        info = {"msgs": [], "listas": 0, "equipe": 0}
        spent = 0
        party_key = KEY_A
        while not (self.ctl.overworld_idle() and info["msgs"]):
            if spent > SCENE_TIMEOUT:
                raise self.ctl.timeout_error(f"conversa com o Mestre; mensagens {info['msgs']}")
            tasks = self._tasks()
            msg = self._message()
            if self.ctl.script_active() and msg and (not info["msgs"] or info["msgs"][-1] != msg):
                info["msgs"].append(msg)
            if LISTA_TASK in tasks:
                info["listas"] += 1
                indice, party_key = plano.pop(0)
                self.emu.frames(20)
                if shot_lista and "lista" not in info:
                    info["lista"] = self._shot(shot_lista)
                if indice is None:
                    self.emu.press(KEY_B, hold=2, release=20)
                else:
                    for _ in range(indice):
                        self.emu.press(KEY_DOWN, hold=2, release=8)
                    self.emu.frames(10)
                    self.emu.press(KEY_A, hold=2, release=20)
                spent += 60
            elif YESNO_TASK in tasks:
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, "pergunta")
                self.emu.press(KEY_A if plano else KEY_B, hold=2, release=8)
                spent += 10
            elif self.game.callback2() != "CB2_Overworld" and not self._fade_active():
                info["equipe"] += 1
                self.emu.press(party_key, hold=2, release=30)
                spent += 32
            elif self.ctl.script_active():
                self.emu.press(KEY_A, hold=2, release=8)
                spent += 10
            else:
                self.emu.frames(4)
                spent += 4
        self.emu.frames(10)
        return info

    # --- casos ----------------------------------------------------------------------
    def _ensina(self) -> str:
        self._restore("casas_base")
        self._entrar_na_casa("casa_rota6_exterior")
        self.ctl.checkpoint("casas_mestre")
        self._falar()
        base = self._lead_moves()
        body, edge = self._move("MOVE_BODY_SLAM"), self._move("MOVE_DOUBLE_EDGE")
        info = self._cena([(TUTOR_BODY_SLAM, KEY_A), (TUTOR_DOUBLE_EDGE, KEY_A)], shot_lista="mestre_lista")
        assert info["listas"] == 2 and info["equipe"] >= 2, info
        assert self._rom_text("Route6_UnusedHouse_Text_Ensinado") in info["msgs"], info["msgs"]
        golpes = self._lead_moves()
        assert golpes == base + [body, edge], f"golpes {golpes}, esperava {base + [body, edge]}"
        assert self.game.money() == DINHEIRO - 2 * PRECO, f"dinheiro {self.game.money()}"
        for flag in ("FLAG_TUTOR_BODY_SLAM", "FLAG_TUTOR_DOUBLE_EDGE"):
            assert not self.game.flag(self.consts.flag(flag)), f"{flag} ligada pelo Mestre"
        return (f"lista com a tela {info['lista']}; Pancada Corporal e Faca 2 Gumes ensinadas: ¥{DINHEIRO} → "
                f"¥{self.game.money()}; flags dos tutores originais desligadas; exterior {self.measures['exterior']}")

    def _sem_dinheiro(self) -> str:
        self._restore("casas_mestre")
        self._set_money(PRECO - 1)
        self._falar()
        base = self._lead_moves()
        info = self._cena([(TUTOR_BODY_SLAM, KEY_A)])
        assert info["listas"] == 1 and info["equipe"] == 0, info
        assert self._rom_text("Route6_UnusedHouse_Text_SemDinheiro") in info["msgs"], info["msgs"]
        assert self.game.money() == PRECO - 1 and self._lead_moves() == base
        return f"¥{PRECO - 1}: ele recusou (sem tela da equipe), dinheiro e golpes intactos"

    def _cancelar(self) -> str:
        self._restore("casas_mestre")
        base = self._lead_moves()
        self._falar()
        info = self._cena([(None, KEY_A)])
        assert info["listas"] == 1 and info["equipe"] == 0, info
        assert self._rom_text("Route6_UnusedHouse_Text_Cancelou") in info["msgs"], info["msgs"]
        assert self.game.money() == DINHEIRO and self._lead_moves() == base
        # escolhe o golpe e desiste na tela da equipe (B): nada é ensinado e nada é cobrado
        self._falar()
        info = self._cena([(TUTOR_BODY_SLAM, KEY_B)])
        assert info["listas"] == 1 and info["equipe"] >= 1, info
        assert self._rom_text("Route6_UnusedHouse_Text_Desistiu") in info["msgs"], info["msgs"]
        assert self.game.money() == DINHEIRO and self._lead_moves() == base
        return "B na lista e B na tela da equipe: ¥10.000 e golpes intactos"

    def run(self) -> None:
        try:
            self._flow("casas: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("casas/mestre_ensina", self._ensina)
            self.suite.run("casas/mestre_sem_dinheiro", self._sem_dinheiro)
            self.suite.run("casas/mestre_cancelar_nao_cobra", self._cancelar)
        except Abort:
            pass


def run_full_casas(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    CasasScenario(ctx_test).run()
