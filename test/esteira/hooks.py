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
CMD_EVOLUTION_TEXT = 8      # arg0 = espécie, arg1 = 0 (GetEvolutionPageText) | 1 (o texto que a página
                            # EVOLUTION aberta imprimiu) -> tamanho; o texto fica em gTestText
CMD_SUMMARY_STATE = 9       # -> página | modo << 8 | ovo << 16 do resumo aberto (0xFFFFFFFF = nenhum)
CMD_SET_PARTY_EGG = 10      # arg0 = espécie, arg1 = slot -> nº no time (ovo de CreateEgg)
CMD_IVEV_TEXT = 11          # arg0 = IVs (5 bits cada: HP, Atk, Def, Spe, SpA, SpD), EVs em gTestText[0-5],
                            # arg1 = slot + 1 (0 = um Pokémon novo) -> tamanho do texto da página IVs/EVs

# modos de GetEvolutionTargetSpecies (EVO_MODE_* de include/constants/pokemon.h)
EVO_MODE_NORMAL, EVO_MODE_TRADE, EVO_MODE_ITEM_USE = 0, 1, 2

MAILBOX_SYMBOL = "gTestMailbox"
TEXT_SYMBOL = "gTestText"   # u8[TEST_TEXT_SIZE], texto no charmap do jogo terminado em 0xFF
_ARG0, _RESULT, _DONE = 0x04, 0x0C, 0x10
NO_RESULT = 0xFFFFFFFF

# PSS_PAGE_* e PSS_MODE_* (include/pokemon_summary_screen.h)
PSS_PAGE_INFO, PSS_PAGE_SKILLS, PSS_PAGE_MOVES, PSS_PAGE_MOVES_INFO = 0, 1, 2, 3
PSS_PAGE_EVOLUTION, PSS_PAGE_IVS = 6, 7
PSS_MODE_NORMAL, PSS_MODE_SELECT_MOVE = 0, 2


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

    # --- página EVOLUTION do resumo (Hack 4) ---------------------------------------------
    def evolution_text(self, species: int = 0, from_open_summary: bool = False) -> bytes:
        """Bytes (charmap do jogo, sem o 0xFF) do texto da página EVOLUTION: o que
        GetEvolutionPageText monta para `species`, ou o que a página aberta imprimiu."""
        length = self.call(CMD_EVOLUTION_TEXT, species, int(from_open_summary))
        assert length != NO_RESULT, ("EVOLUTION_TEXT recusado: " + (
            "nenhum resumo aberto" if from_open_summary else f"espécie {species}"))
        data = self.emu.read(self.ctl.game.syms.addr(TEXT_SYMBOL), length + 1)
        assert data[length] == 0xFF, f"texto de {length} bytes sem terminador: {data.hex()}"
        return data[:length]

    def summary_state(self) -> tuple[int, int, bool] | None:
        """(página, modo, ovo) do resumo aberto (PSS_PAGE_*, PSS_MODE_*), ou None."""
        state = self.call(CMD_SUMMARY_STATE)
        if state == NO_RESULT:
            return None
        return state & 0xFF, (state >> 8) & 0xFF, bool((state >> 16) & 0xFF)

    def ivev_text(self, ivs: tuple[int, ...], evs: tuple[int, ...], slot: int | None = None) -> bytes:
        """Texto (bytes, sem o 0xFF) de GetIvEvPageText para um Pokémon com esses IVs e EVs (na
        ordem da página: HP, ATK, DEF, SP. ATK, SP. DEF, SPEED). Com `slot`, eles vão para
        gPlayerParty[slot] (e os atributos são recalculados)."""
        # a caixa usa a ordem dos MON_DATA_*: HP, Atk, Def, Spe, SpA, SpD
        order = (0, 1, 2, 5, 3, 4)
        packed = sum(ivs[j] << (5 * i) for i, j in enumerate(order))
        addr = self.ctl.game.syms.addr(TEXT_SYMBOL)
        self.emu.write(addr, bytes(evs[j] for j in order))
        length = self.call(CMD_IVEV_TEXT, packed, 0 if slot is None else slot + 1)
        assert length != NO_RESULT, f"IVEV_TEXT recusado: slot {slot}"
        return self.emu.read(addr, length)

    def set_party_egg(self, slot: int, species: int) -> int:
        """Põe um ovo de `species` (CreateEgg) em gPlayerParty[slot]; devolve o nº no time."""
        count = self.call(CMD_SET_PARTY_EGG, species, slot)
        assert count > slot, f"SET_PARTY_EGG recusado: espécie {species}, slot {slot} (time = {count})"
        return count
