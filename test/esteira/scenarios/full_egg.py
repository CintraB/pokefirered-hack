"""Modo completo: um ovo de verdade na creche de Four Island (Hack 6), na build de teste.

Ponto de partida: o .sav do fim do modo rápido, numa sessão própria da ROM de teste. Os
atalhos (esteira/hooks.py) só fazem o que o jogo levaria horas para fazer: montam os dois pais
na creche com um ovo pendente (como depois de andar com eles lá), pulam a cena do rival na
chegada a Four Island (VAR_MAP_SCENE_FOUR_ISLAND) e levam o jogador até a frente do velho da
creche. Daí em diante é o jogo:

1. fala com o velho da creche: "Quer o ovo?" SIM, o ovo entra no time (GiveEggFromDaycare do
   script do mapa, com as regras novas);
2. o ovo confere com a creche: espécie, marca de ovo, posição da habilidade = bit da
   personalidade, natureza = personalidade % 25, golpes só da espécie/pais;
3. o atalho zera os ciclos que faltam no ovo (e deixa a creche a 10 passos do próximo ciclo);
   o jogador ANDA até o ovo chocar, a cena inteira roda e o apelido é recusado (NÃO);
4. o filhote é o ovo: mesma personalidade, IVs, golpes, natureza, habilidade, gênero e shiny;
   nível 5, não é mais ovo, apelido = nome da espécie.

Telas: telas/ovo_recebido.png, ovo_chocando.png e ovo_chocado.png (sem referência).
Numa janela, em tempo real: `make test-watch CENARIO=ovo`.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only ovo
"""

import sys

from ..breeding import CONFIGS, NATURES, Record, egg_moves, header_defines, unpack_records
from ..emu import KEY_B, KEY_UP
from ..game import POKEMON_SIZE, decode_mon
from ..hooks import CMD_EGGS_READY, CMD_PACK_PARTY_MON, CMD_SET_VAR, CMD_WARP
from . import REPO_ROOT, ScenarioContext
from .base import TEXT_PERIOD, Abort
from .full_breeding import BreedingScenario

CONFIG = CONFIGS[0]                 # Rattata x Rattata com golpes de ovo (esteira/breeding.py)
DAYCARE_MAN_FRONT = (16, 15)        # o velho fica em (16, 14) com um ovo pendente
STEPS_BEFORE_CYCLE = 245            # a creche conta até 255: 10 passos até o ovo chocar
WALK_LIMIT = 40
HATCH_TIMEOUT = 6000
EGG_HATCH_CALLBACKS = ("CB2_EggHatch_0", "CB2_EggHatch_1")


class EggScenario(BreedingScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.slot = 0
        self.egg: Record | None = None
        self.egg_mon = None
        self.continue_shot = "ovo_continue"

    def _record(self, slot: int) -> Record:
        assert self.box.call(CMD_PACK_PARTY_MON, slot) == 1, f"slot {slot} vazio"
        return unpack_records(self.emu.read(self.results_addr, 8), 1)[0]

    def _party_mon(self, slot: int):
        base = self.game.syms.addr("gPlayerParty") + slot * POKEMON_SIZE
        return decode_mon(self.emu.read(base, POKEMON_SIZE), self.game.charmap)

    # --- passos --------------------------------------------------------------------------
    def _arrive(self) -> str:
        compat = self.setup(CONFIG, pending=True)
        assert self.game.flag(self.consts.flag("FLAG_PENDING_DAYCARE_EGG")), "ovo não ficou pendente"
        var = header_defines(REPO_ROOT, "vars.h")["VAR_MAP_SCENE_FOUR_ISLAND"]
        assert self.box.call(CMD_SET_VAR, var, 1) == 1
        group, num = self.consts.map("MAP_FOUR_ISLAND")
        x, y = DAYCARE_MAN_FRONT
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para Four Island")
        self.ctl.wait_overworld_idle(600)
        self._expect_map("MAP_FOUR_ISLAND")
        assert self.game.player_xy() == DAYCARE_MAN_FRONT, f"jogador em {self.game.player_xy()}"
        return (f"{CONFIG.what} na creche (compatibilidade {compat}), ovo pendente; jogador em "
                f"Four Island {self.game.player_xy()}, de frente para o velho da creche")

    def _take_egg(self) -> str:
        before = len(self.game.party())
        self._talk(KEY_UP, "velho da creche entrega o ovo")       # "Quer o ovo?" -> A = SIM
        party = self.game.party()
        assert len(party) == before + 1, f"time {before} -> {len(party)}: o ovo não veio"
        self.slot = len(party) - 1
        self.egg = self._record(self.slot)
        self.egg_mon = self._party_mon(self.slot)
        assert not self.game.flag(self.consts.flag("FLAG_PENDING_DAYCARE_EGG")), \
            "FLAG_PENDING_DAYCARE_EGG continua ligada"
        self.measures["ovo_recebido"] = self._shot("ovo_recebido")
        e = self.egg
        return (f"ovo no slot {self.slot}: {self._sp(e.species)}, IVs {list(e.ivs)}, natureza "
                f"{NATURES[e.nature]}, habilidade {e.ability}, gênero {e.gender}, "
                f"shiny {e.shiny}, golpes {self.egg_mon.moves}")

    def _sp(self, species: int) -> str:
        return self.consts.species_name(species).removeprefix("SPECIES_")

    def _check_egg(self) -> str:
        e, mon = self.egg, self.egg_mon
        assert e.is_egg, "o Pokémon recebido não é ovo"
        assert e.species == self.consts.species(CONFIG.child), f"espécie {self._sp(e.species)}"
        assert e.nature == mon.personality % 25, "natureza != personalidade % 25"
        assert e.ability == mon.personality & 1, "posição da habilidade != bit da personalidade"
        assert mon.ot_id == self._party_mon(0).ot_id, "OT do ovo não é o jogador"
        allowed = set(header_defines(REPO_ROOT, "moves.h")[m] for m in
                      egg_moves(REPO_ROOT, CONFIG.child))
        # golpes de nível 5 da espécie (o Rattata nasce com Tackle e Tail Whip) e os de ovo
        moves = header_defines(REPO_ROOT, "moves.h")
        allowed |= {moves["MOVE_TACKLE"], moves["MOVE_TAIL_WHIP"], 0}
        extra = [m for m in mon.moves if m not in allowed]
        assert not extra, f"golpes fora do esperado: {extra}"
        return (f"personalidade {mon.personality:08x}: natureza {NATURES[e.nature]}, habilidade "
                f"{e.ability}, golpes {mon.moves} (de nível ou de ovo da espécie)")

    def _hatch(self) -> str:
        eggs = self.box.call(CMD_EGGS_READY, STEPS_BEFORE_CYCLE)
        assert eggs == 1, f"{eggs} ovos no time"
        steps, direction, started = 0, "left", False
        while not started:
            assert steps < WALK_LIMIT, f"{steps} passos e o ovo não chocou"
            self.nav.step(direction, 1)
            started = self.nav.interrupted == "script"
            steps += 1
            direction = "right" if direction == "left" else "left"
        spent, shot = 0, False
        while True:
            hatching = self.game.callback2() in EGG_HATCH_CALLBACKS
            if hatching and not shot and spent > 400:
                self.measures["ovo_chocando"] = self._shot("ovo_chocando")
                shot = True
            if not hatching and spent > 60 and self._settled_idle():
                break
            assert spent < HATCH_TIMEOUT, "a cena do ovo chocando não terminou"
            # B avança as falas e responde NÃO ao "Dar um apelido?"
            self._press(KEY_B)
            spent += TEXT_PERIOD
        self.measures["ovo_chocado"] = self._shot("ovo_chocado")
        return f"chocou depois de {steps} passos andando; cena e apelido (NÃO) em {spent} quadros"

    def _check_hatched(self) -> str:
        e, egg_mon = self.egg, self.egg_mon
        after = self._record(self.slot)
        mon = self._party_mon(self.slot)
        assert not after.is_egg, "continua ovo"
        same = {"espécie": (after.species, e.species), "IVs": (after.ivs, e.ivs),
                "natureza": (after.nature, e.nature), "habilidade": (after.ability, e.ability),
                "gênero": (after.gender, e.gender), "shiny": (after.shiny, e.shiny),
                "personalidade": (mon.personality, egg_mon.personality),
                "golpes": (mon.moves, egg_mon.moves)}
        diff = [f"{k}: ovo {b} -> filhote {a}" for k, (a, b) in same.items() if a != b]
        assert not diff, "; ".join(diff)
        name = self._sp(after.species)
        assert mon.level == 5, f"nível {mon.level}"
        assert mon.nickname == name, f"apelido {mon.nickname!r}"
        return (f"{name} nível 5 sem apelido, idêntico ao ovo: IVs {list(after.ivs)}, natureza "
                f"{NATURES[after.nature]}, habilidade {after.ability}, gênero {after.gender}, "
                f"golpes {mon.moves}")

    def run(self) -> None:
        try:
            self._flow("ovo: CONTINUAR com o save do modo rápido na build de teste", self._start)
            self._flow("ovo: pais na creche (atalho) e chegada a Four Island", self._arrive)
            res = self.suite.run("ovo: o velho da creche de Four Island entrega o ovo",
                                 self._take_egg)
            if "ovo_recebido" in self.measures:
                res.images.append(self.measures["ovo_recebido"])
            if res.status == "falha":
                raise Abort("ovo")
            self.suite.run("ovo: dados do ovo batem com as regras da creche", self._check_egg)
            res = self.suite.run("ovo: anda até o ovo chocar (cena inteira, sem apelido)",
                                 self._hatch)
            res.images += [self.measures[k] for k in ("ovo_chocando", "ovo_chocado")
                           if k in self.measures]
            if res.status == "falha":
                raise Abort("chocar")
            self.suite.run("ovo: o filhote é o ovo (personalidade, IVs, golpes...)",
                           self._check_hatched)
        except Abort:
            pass


def run_full_egg(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    EggScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only ovo ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "ovo", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
