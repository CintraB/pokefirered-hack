"""Modo completo: cena pós-Liga nova do Oak (Hack 7), na build de teste.

A cena do Prof. Carvalho (Pallet Town > laboratório) deixou de "melhorar a Pokédex": ele dá um
Ovo raro (Larvitar, Bagon ou Beldum), ¥45.000 e anuncia o objetivo do Amuleto Brilhante. A
condição continua a de antes (Liga vencida, FLAG_WORLD_MAP_ONE_ISLAND, 60 capturados de Kanto) e
a Dex Nacional (flag + var + magic) liga no fim da cena. Sessão própria da ROM de teste a partir
do .sav do `captura` (`save_from="captura"`); a preparação (atalhos SET_KANTO_OWNED, SET_FLAG,
SET_VAR) é refeita a cada caso a partir do CONTINUAR (savestate `pos_liga_base`):

1. `pos_liga/equipe`: a cena roda até o fim apertando A: ovo na equipe (espécie sorteada ∈
   {LARVITAR, BAGON, BELDUM}), +¥45.000, Dex Nacional ligada, FLAG_GOT_RARE_EGG; telas
   `pos_liga_ovo`, `pos_liga_dinheiro` e `pos_liga_objetivo`. Desde o POK-28 a cena também dá o
   1º ovo do Prof. Elm logo depois do raro (o A escolhe a 1ª opção do menu, CHIKORITA): 2 ovos;
2. `pos_liga/pc`: equipe cheia: os dois ovos vão para o PC e as flags ligam;
3. `pos_liga/oak_guarda`: equipe cheia e PC cheio: a cena termina sem ovo e sem flag (o dinheiro
   e a Dex Nacional vêm igual) e nem oferece o do Elm; com uma vaga aberta, falar com o Oak
   entrega o ovo raro, e o do Elm fica para depois (sem vaga de novo);
4. `pos_liga/sorteio`: 3000 sorteios (RARE_EGG_ROLL): cada espécie a ±4σ de 1/3;
5. `pos_liga/sem_60`: com 59 capturados de Kanto a cena não começa (Oak só elogia e vai embora).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only pos_liga
"""

import math
import sys

from ..breeding import header_defines
from ..emu import KEY_A, KEY_UP
from ..game import BOX_MON_FLAGS, BOX_MON_SIZE, IN_BOX_COUNT, POKEMON_SIZE, STORAGE_BOXES
from ..hooks import CMD_SET_VAR, CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

SB1_VARS = 0x1000                  # u16 vars[] em struct SaveBlock1 (include/global.h)
SB1_MONEY = 0x0290                 # u32 money (XOR encryptionKey), como em game.py
SB2_NATIONAL_MAGIC = 0x1B          # SaveBlock2.pokedex.nationalMagic (0x18 + 3)
VAR_BASE = 0x4000
NATIONAL_DEX_MAGIC_VAR, NATIONAL_DEX_MAGIC_BYTE = 0x6258, 0xB9
EGG_BIT = 0x04                     # BoxPokemon: isBadEgg:1, hasSpecies:1, isEgg:1
RARE_EGGS = ("SPECIES_LARVITAR", "SPECIES_BAGON", "SPECIES_BELDUM")
ELM_EGGS = ("SPECIES_CHIKORITA", "SPECIES_CYNDAQUIL", "SPECIES_TOTODILE")   # POK-28: ovos do Prof. Elm
MONEY_GIFT = 45000
PALLET_PLAYER = (6, 8)             # diante da porta da casa: onde o Oak vem falar com o jogador
LAB, PALLET = "MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB", "MAP_PALLET_TOWN"
OAK_FRONT = (6, 4)                 # abaixo do Oak, que fica em (6, 3) depois da cena
SCENE_FRAMES = 14000
SETTLE_FRAMES = 12
ROLLS = 3000
OWNED_NEEDED = 60
TEXT_OVO, TEXT_DINHEIRO, TEXT_OBJETIVO = "recebeu o Ovo!", "recebeu ¥45.000!", "Amuleto Brilhante"
TEXT_SEM_ESPACO = "você não tem espaço"
# trecho da mensagem -> (tela, espera da caixa em que ela é tirada: cada \p e cada \l antes do trecho
# conta uma; o "Amuleto Brilhante" só aparece depois da rolagem do \l da 2ª página)
SHOTS = {TEXT_OVO: ("pos_liga_ovo", 0), TEXT_DINHEIRO: ("pos_liga_dinheiro", 0),
         TEXT_OBJETIVO: ("pos_liga_objetivo", 2)}
BUTTON_WAIT_STATES = {1, 2, 3}     # RENDER_STATE_WAIT/CLEAR/SCROLL_START: o texto espera um botão
STRING_VAR4_SIZE = 0x100


class PostLeagueScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.vars = header_defines(REPO_ROOT, "vars.h")

    # --- leitura do estado ---------------------------------------------------------
    def _sp(self, name: str) -> int:
        return self.consts.species(name)

    def _flag(self, name: str) -> bool:
        return self.game.flag(self.consts.flag(name))

    def _var(self, name: str) -> int:
        sb1 = self.game._sb1()
        return self.emu.read_u16(sb1 + SB1_VARS + (self.vars[name] - VAR_BASE) * 2)

    def _nat_dex(self) -> tuple[bool, int, int]:
        return (self._flag("FLAG_SYS_NATIONAL_DEX"), self._var("VAR_NATIONAL_DEX"),
                self.emu.read_u8(self.game._sb2() + SB2_NATIONAL_MAGIC))

    def _nat_dex_on(self) -> bool:
        return self._nat_dex() == (True, NATIONAL_DEX_MAGIC_VAR, NATIONAL_DEX_MAGIC_BYTE)

    def _party_eggs(self) -> list[int]:
        base = self.game.syms.addr("gPlayerParty")
        count = self.emu.read_u8(self.game.syms.addr("gPlayerPartyCount"))
        eggs = []
        for i in range(count):
            raw = self.emu.read(base + i * POKEMON_SIZE, POKEMON_SIZE)
            if raw[BOX_MON_FLAGS] & EGG_BIT:
                eggs.append(self.game.party()[i].species)
        return eggs

    def _box_addr(self, box: int, slot: int) -> int:
        storage = self.emu.read_u32(self.game.syms.addr("gPokemonStoragePtr"))
        return storage + STORAGE_BOXES + (box * IN_BOX_COUNT + slot) * BOX_MON_SIZE

    def _pc_eggs(self) -> list[tuple[int, int, int]]:
        """(caixa, slot, espécie) dos ovos no PC."""
        eggs = []
        for box in range(14):
            for slot, mon in enumerate(self.game.box_mons(box)):
                if mon is not None and self.emu.read(self._box_addr(box, slot), BOX_MON_SIZE)[
                        BOX_MON_FLAGS] & EGG_BIT:
                    eggs.append((box, slot, mon.species))
        return eggs

    def _message(self) -> str:
        """Texto da última caixa de mensagem do campo (gStringVar4, já com {PLAYER} trocado)."""
        return self.game.charmap.decode(
            self.emu.read(self.game.syms.addr("gStringVar4"), STRING_VAR4_SIZE))

    # --- montagem ------------------------------------------------------------------
    def _set_party(self, size: int) -> None:
        for slot in range(size):
            self.box.set_party_mon(slot, self._sp("SPECIES_RATTATA"), 5)

    def _clear_egg_flags(self) -> None:
        """Estado de antes do 1º ovo (Hack 8: uma flag por espécie dada e a do ovo pendente)."""
        for name in ("FLAG_GOT_RARE_EGG", "FLAG_GOT_EGG_LARVITAR", "FLAG_GOT_EGG_BAGON",
                     "FLAG_GOT_EGG_BELDUM", "FLAG_RARE_EGG_PENDING", "FLAG_GOT_ELM_EGG",
                     "FLAG_GOT_EGG_CHIKORITA", "FLAG_GOT_EGG_CYNDAQUIL", "FLAG_GOT_EGG_TOTODILE",
                     "FLAG_ELM_EGG_PENDING"):
            assert not self.box.set_flag(self.consts.flag(name), False), name

    def _prepare(self, owned: int) -> None:
        """Liga (pelos atalhos) tudo que a cena exige, menos o warp para Pallet Town."""
        got = self.box.set_kanto_owned(owned)
        assert got == owned, f"{got} capturados de Kanto, esperava {owned}"
        for name in ("FLAG_SYS_GAME_CLEAR", "FLAG_WORLD_MAP_ONE_ISLAND"):
            assert self.box.set_flag(self.consts.flag(name), True), name
        self._clear_egg_flags()
        self.box.call(CMD_SET_VAR, self.vars["VAR_MAP_SCENE_PALLET_TOWN_OAK"], 2)

    def _warp(self, map_name: str, xy: tuple[int, int]) -> None:
        group, num = self.consts.map(map_name)
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600,
                            f"warp para {map_name}")

    def _run_scene(self, until, what: str, shots: dict[str, tuple[str, int]] | None = None) -> list[str]:
        """Aperta A até `until()` com o jogo livre; cada trecho de SHOTS que aparecer na caixa
        de mensagem (texto todo impresso) gera uma tela. Devolve as telas tiradas."""
        taken: list[str] = []
        spent = 0
        while not (until() and self._settled_idle()):
            if spent >= SCENE_FRAMES:
                raise self.ctl.timeout_error(what)
            text = self._message()
            for needle, (name, page) in (shots or {}).items():
                if needle in text and name not in taken and self.ctl.script_active():
                    self._shot_page(needle, name, page)
                    taken.append(name)
            self._press(KEY_A)
            spent += 10
        return taken

    def _waiting(self) -> bool:
        """Página inteira na tela: esperando botão, ou (message sem msgbox) impressão acabada."""
        return (not self.game.text_printer_active()
                or self.game.text_printer_state(0) in BUTTON_WAIT_STATES)

    def _a_released(self) -> bool:
        """O último ReadKeys() do jogo viu o A solto: o próximo aperto vira JOY_NEW."""
        return not self.game.held_keys() & KEY_A

    def _shot_page(self, needle: str, name: str, page: int) -> None:
        """Avança as esperas da caixa atual (\\p e \\l) até a `page` esperar um botão e tira a tela."""
        for current in range(page + 1):
            self.ctl.wait_until(self._waiting, 300, f"texto '{needle}' (página {current + 1})")
            if current == page:
                break
            # o impressor instantâneo desenha a página num giro só do laço principal, que pode
            # durar mais de um quadro: o estado de espera aparece no meio do giro, antes de o jogo
            # ler o A do aperto anterior solto, e um A novo agora seria lido como "segurado"
            self.ctl.wait_until(self._a_released, 60, f"A solto antes da página {current + 2}")
            self.emu.press(KEY_A, hold=2, release=0)
            for _ in range(120):   # quadro a quadro: a página nova pode imprimir em poucos
                if not self._waiting():
                    break
                self.emu.frames(1)
            else:
                raise self.ctl.timeout_error("próxima página")
        self.emu.frames(SETTLE_FRAMES)
        self.measures.setdefault("shots_by_name", {})[name] = self._shot(name)

    def _scene_done(self) -> bool:
        return self._var("VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB") == 8

    def _play_scene(self, shots: dict[str, tuple[str, int]] | None = None) -> list[str]:
        """Do warp para Pallet Town até a cena do laboratório terminar (var do lab = 8)."""
        self._warp(PALLET, PALLET_PLAYER)
        self.ctl.wait_until(self.ctl.script_active, 600, "início da cena do Oak")
        taken = self._run_scene(self._scene_done, "cena pós-Liga", shots)
        assert self.game.location() == self.consts.map(LAB), self.game.location()
        return taken

    def _egg_checks(self, party_eggs: int, pc_eggs: int, elm: int = 0) -> str:
        """Ovos na equipe e no PC; `elm` deles são do Prof. Elm (POK-28) e o resto, raros."""
        assert len(self._party_eggs()) == party_eggs, f"ovos na equipe: {self._party_eggs()}"
        pc = self._pc_eggs()
        assert len(pc) == pc_eggs, f"ovos no PC: {pc}"
        rare, elms = {self._sp(n) for n in RARE_EGGS}, {self._sp(n) for n in ELM_EGGS}
        species = self._party_eggs() + [s for _, _, s in pc]
        assert all(s in rare | elms for s in species), (
            f"espécies {[self.consts.species_name(s) for s in species]}")
        assert sum(s in elms for s in species) == elm, (
            f"ovos do Elm: {[self.consts.species_name(s) for s in species]}, esperava {elm}")
        return ", ".join(self.consts.species_name(s).removeprefix("SPECIES_") for s in species)

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="pos_liga_continue")
        self.ctl.checkpoint("pos_liga_base")
        return "CONTINUAR com o save do modo rápido; savestate pos_liga_base"

    def _restore(self) -> None:
        self.ctl.restore("pos_liga_base")
        self.emu.frames(SETTLE_FRAMES)

    def _team(self) -> str:
        self._restore()
        self._prepare(OWNED_NEEDED)
        money, party = self.game.money(), len(self.game.party())
        assert not self._nat_dex_on(), "Dex Nacional já ligada antes da cena"
        shots = self._play_scene(SHOTS)
        assert sorted(shots) == sorted(n for n, _ in SHOTS.values()), f"telas tiradas: {shots}"
        kind = self._egg_checks(2, 0, elm=1)
        assert len(self.game.party()) == party + 2, "os ovos não entraram na equipe"
        assert self.game.money() == money + MONEY_GIFT, (money, self.game.money())
        assert self._nat_dex_on(), f"Dex Nacional {self._nat_dex()}"
        assert self._flag("FLAG_GOT_RARE_EGG"), "FLAG_GOT_RARE_EGG desligada"
        assert self._flag("FLAG_GOT_ELM_EGG"), "FLAG_GOT_ELM_EGG desligada"
        return (f"ovos de {kind} na equipe, dinheiro {money} -> {self.game.money()}, "
                f"Dex Nacional ligada; telas {shots}")

    def _pc(self) -> str:
        self._restore()
        self._prepare(OWNED_NEEDED)
        self._set_party(6)
        money = self.game.money()
        self._play_scene()
        kind = self._egg_checks(0, 2, elm=1)
        assert len(self.game.party()) == 6
        assert self._flag("FLAG_GOT_RARE_EGG"), "FLAG_GOT_RARE_EGG desligada"
        assert self._flag("FLAG_GOT_ELM_EGG"), "FLAG_GOT_ELM_EGG desligada"
        assert self.game.money() == money + MONEY_GIFT
        assert self._nat_dex_on(), f"Dex Nacional {self._nat_dex()}"
        return f"equipe cheia: ovos de {kind} na caixa {self._pc_eggs()[0][0] + 1}, flags ligadas"

    def _oak_keeps(self) -> str:
        self._restore()
        self._prepare(OWNED_NEEDED)
        self._set_party(6)
        assert self.box.fill_pc() == 14 * IN_BOX_COUNT
        money = self.game.money()
        shots = self._play_scene({TEXT_SEM_ESPACO: ("pos_liga_sem_espaco", 0)})
        assert shots == ["pos_liga_sem_espaco"], f"fala do Oak sem espaço não apareceu: {shots}"
        self._egg_checks(0, 0)
        assert not self._flag("FLAG_GOT_RARE_EGG"), "a flag ligou sem entregar o ovo"
        assert not self._flag("FLAG_GOT_ELM_EGG"), "a flag do Elm ligou sem entregar o ovo"
        assert self.game.money() == money + MONEY_GIFT, "dinheiro não foi dado"
        assert self._nat_dex_on(), f"Dex Nacional {self._nat_dex()}"
        # abre uma vaga no PC e fala com o Oak
        self.emu.write(self._box_addr(0, 0), bytes(BOX_MON_SIZE))
        self._warp(LAB, OAK_FRONT)
        self.ctl.wait_overworld_idle(600)
        self._talk(KEY_UP, "falar com o Oak")
        kind = self._egg_checks(0, 1)
        assert self._flag("FLAG_GOT_RARE_EGG"), "o Oak não ligou FLAG_GOT_RARE_EGG"
        assert self.game.money() == money + MONEY_GIFT, "o Oak deu dinheiro de novo"
        # a vaga foi para o raro: o do Elm (oferecido em seguida) ficou sem espaço, e nada mudou
        assert not self._flag("FLAG_GOT_ELM_EGG"), "a flag do Elm ligou sem vaga para o ovo"
        self._talk(KEY_UP, "falar com o Oak de novo")
        self._egg_checks(0, 1)
        assert not self._flag("FLAG_GOT_ELM_EGG"), "a flag do Elm ligou sem vaga para o ovo"
        return (f"sem espaço: cena termina sem ovo nem flag; com vaga no PC o Oak entrega o ovo "
                f"de {kind} (uma vez só); o do Elm espera vaga")

    def _roll(self) -> str:
        self._clear_egg_flags()      # o sorteio ignora as espécies já dadas (Hack 8)
        counts = {n: 0 for n in RARE_EGGS}
        ids = {self._sp(n): n for n in RARE_EGGS}
        for _ in range(ROLLS):
            sp = self.box.rare_egg_roll()
            assert sp in ids, f"sorteou {self.consts.species_name(sp)}"
            counts[ids[sp]] += 1
        sigma = math.sqrt(ROLLS / 3 * 2 / 3)
        bad = {n: c for n, c in counts.items() if abs(c - ROLLS / 3) > 4 * sigma}
        assert not bad, f"fora de ±4σ ({4 * sigma:.0f}): {bad}"
        return (f"{ROLLS} sorteios: " + ", ".join(
            f"{n.removeprefix('SPECIES_')} {c}" for n, c in counts.items())
            + f" (esperado {ROLLS // 3} ± {4 * sigma:.0f})")

    def _sem_60(self) -> str:
        self._restore()
        self._prepare(OWNED_NEEDED - 1)
        money = self.game.money()
        self._warp(PALLET, PALLET_PLAYER)
        self.ctl.wait_until(self.ctl.script_active, 600, "início da cena do Oak")
        self._run_scene(lambda: self._var("VAR_MAP_SCENE_PALLET_TOWN_OAK") == 3,
                        "Oak sem Pokémon suficientes")
        assert self.game.location() == self.consts.map(PALLET), (
            f"foi para {self.game.location()}: a cena do laboratório começou")
        assert self._var("VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB") != 8
        self._egg_checks(0, 0)
        assert not self._flag("FLAG_GOT_RARE_EGG")
        assert self.game.money() == money
        assert not self._nat_dex_on() and not self._flag("FLAG_SYS_NATIONAL_DEX")
        return "59 capturados: a cena do laboratório não começa; sem ovo, dinheiro nem Dex Nacional"

    def run(self) -> None:
        try:
            self._flow("pos_liga: CONTINUAR com o save do modo rápido", self._start)
            res = self.suite.run("pos_liga/equipe: ovo, ¥45.000 e objetivo, Dex Nacional ligada",
                                 self._team)
            for name, _ in SHOTS.values():
                if name in self.measures.get("shots_by_name", {}):
                    res.images.append(self.measures["shots_by_name"][name])
            self.suite.run("pos_liga/pc: equipe cheia, o ovo vai para o PC", self._pc)
            self.suite.run("pos_liga/oak_guarda: sem espaço o Oak guarda o ovo", self._oak_keeps)
            self.suite.run("pos_liga/sorteio: Larvitar, Bagon e Beldum equiprováveis",
                           self._roll)
            self.suite.run("pos_liga/sem_60: com 59 capturados a cena não começa", self._sem_60)
        except Abort:
            pass


def run_full_post_league(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    PostLeagueScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only pos_liga ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "pos_liga", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
