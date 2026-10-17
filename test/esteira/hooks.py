"""Caixa de comandos da build de teste (`make firered_switch TESTBUILD=1`).

`gTestMailbox` (include/test_hooks.h) é `struct TestMailbox {u32 cmd, arg0, arg1, result,
done}`: o runner escreve arg0/arg1 e zera result/done, depois escreve cmd; o jogo executa o
comando em `TestHooks_Run` (uma vez por quadro, src/main.c), grava result, zera cmd e põe
done = 1. Só existe na build de teste: a ROM jogável não tem o símbolo.
"""

import struct

from .control import Controller

CMD_COUNT_SHINIES = 1       # arg0 = quantos, arg1 = com Shiny Charm (0/1) -> nº de shinies
CMD_SET_DEX_COMPLETE = 2    # -> HasAllMons()
CMD_GIVE_ITEM = 3           # arg0 = item, arg1 = quantidade -> AddBagItem()
CMD_CHECK_SHINY = 4         # arg0 = personalidade, arg1 = OT ID -> IsMonShiny() (em gEnemyParty[0])
CMD_SET_PARTY_MON = 5       # arg0 = espécie | nível << 16, arg1 = item segurado | slot << 16
                            # | amizade << 24 (0 = a da espécie) -> nº no time
CMD_ENABLE_NATIONAL_DEX = 6 # -> IsNationalPokedexEnabled()
CMD_EVOLUTION_TARGET = 7    # arg0 = espécie | item << 16, arg1 = modo | nível << 8 | item de evolução << 16
                            # -> GetEvolutionTargetSpecies() (Pokémon em gEnemyParty[0])

# modos de GetEvolutionTargetSpecies (EVO_MODE_* de include/constants/pokemon.h)
EVO_MODE_NORMAL, EVO_MODE_TRADE, EVO_MODE_ITEM_USE = 0, 1, 2

MAILBOX_SYMBOL = "gTestMailbox"
_ARG0, _RESULT, _DONE = 0x04, 0x0C, 0x10


class NotATestBuild(AssertionError):
    """A ROM carregada não tem gTestMailbox: não é a build de teste."""


class Mailbox:
    def __init__(self, controller: Controller):
        self.ctl = controller
        self.emu = controller.emu
        try:
            self.addr = controller.game.syms.addr(MAILBOX_SYMBOL)
        except KeyError:
            raise NotATestBuild(f"{MAILBOX_SYMBOL} não existe no ELF: rode a build de teste "
                                "(make firered_switch TESTBUILD=1)") from None

    def call(self, cmd: int, arg0: int = 0, arg1: int = 0, timeout: int = 60,
             poll: int = 1) -> int:
        """Executa `cmd` no jogo e devolve result; StepTimeout se done não vier em `timeout`
        quadros (lido a cada `poll` quadros)."""
        self.emu.write(self.addr + _ARG0, struct.pack("<IIII", arg0, arg1, 0, 0))
        self.emu.write(self.addr, struct.pack("<I", cmd))
        spent = 0
        while self.emu.read_u32(self.addr + _DONE) != 1:
            if spent >= timeout:
                raise self.ctl.timeout_error(f"comando {cmd} da caixa de testes")
            self.emu.frames(poll)
            spent += poll
        return self.emu.read_u32(self.addr + _RESULT)

    # --- atalhos dos testes de evolução (Hack 3) ---------------------------------------
    def set_party_mon(self, slot: int, species: int, level: int, held_item: int = 0,
                      friendship: int = 0) -> int:
        """Põe o Pokémon em gPlayerParty[slot] (o jogador como OT, personalidade fixa nunca
        shiny); devolve o nº de Pokémon no time. AssertionError se o jogo recusar."""
        assert 0 <= friendship <= 255, friendship
        count = self.call(CMD_SET_PARTY_MON, species | level << 16,
                          held_item | slot << 16 | friendship << 24)
        assert count > slot, (f"SET_PARTY_MON recusado: espécie {species}, nível {level}, "
                              f"item {held_item}, slot {slot} (time = {count})")
        return count

    def enable_national_dex(self) -> bool:
        return bool(self.call(CMD_ENABLE_NATIONAL_DEX))

    def evolution_target(self, species: int, mode: int, level: int = 36, held_item: int = 0,
                         evolution_item: int = 0) -> int:
        """GetEvolutionTargetSpecies() de um Pokémon montado em gEnemyParty[0] (0 = não evolui)."""
        result = self.call(CMD_EVOLUTION_TARGET, species | held_item << 16,
                           mode | level << 8 | evolution_item << 16)
        assert result != 0xFFFFFFFF, f"EVOLUTION_TARGET recusado: espécie {species}, nível {level}"
        return result


# --- Hack 6: breeding genético (enum à parte em include/test_hooks.h, a partir de 0x60; ------
# o uso fica em esteira/breeding.py e scenarios/full_breeding.py / full_egg.py)
CMD_BREED_SETUP = 0x60      # gTestBreedSetup -> creche (arg0 = 1: ovo pendente) -> compatibilidade (0xFFFFFFFF = pai inválido)
CMD_BREED_EGGS = 0x61       # arg0 = quantos (<= 64) ovos entregues; registros em gEnemyParty -> quantos
CMD_EGG_SHINIES = 0x62      # arg0 = quantos, arg1 = com Shiny Charm -> shinies entre as personalidades
CMD_EGG_PERSONALITY = 0x63  # arg0 = tentativas -> quantos ovos entregues têm a personalidade sorteada
CMD_PACK_PARTY_MON = 0x64   # arg0 = slot -> registro em gEnemyParty (1; 0 = slot vazio)
CMD_EGGS_READY = 0x65       # arg0 = contador de passos da creche -> ovos no time (chocam no próximo ciclo)
CMD_WARP = 0x66             # arg0 = grupo | mapa << 8, arg1 = x | y << 16 -> 1
CMD_SET_VAR = 0x67          # arg0 = var, arg1 = valor -> VarGet()
CMD_GAIN_EVS = 0x68         # arg0 = item | espécie derrotada << 16, arg1 = EV do atributo | outros << 8
                            # | atributo << 16 -> total (os 6 EVs em bytes em gEnemyParty)
CMD_SPEED_ORDER = 0x69      # arg0/arg1 = velocidade | item << 16 -> GetWhoStrikesFirst (0, 1, 2 empate)
