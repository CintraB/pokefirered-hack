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

    # --- relógio do jogo (Hack 7) ----------------------------------------------------------
    def set_clock(self, day: int, minute: int) -> int:
        """Acerta o relógio do jogo (antes de 08:00 do dia 0 vira 08:00 do dia 0); devolve o
        minuto do dia que o jogo passou a ver."""
        return self.call(CMD_SET_CLOCK, day, minute)

    def clock_info(self) -> tuple[int, int]:
        """(minuto do dia 0–1439, período TIME_*) do relógio do jogo."""
        info = self.call(CMD_CLOCK_INFO)
        return info & 0xFFFF, info >> 16

    # --- Hack 7 — frente C: cena pós-Liga (ovo raro) ---------------------------------------
    def rare_egg_roll(self) -> int:
        """Espécie sorteada por GetRandomRareEggSpecies()."""
        return self.call(CMD_RARE_EGG_ROLL)

    def set_kanto_owned(self, n: int) -> int:
        """Marca vistos e capturados os n primeiros de Kanto (sem ligar a Dex Nacional);
        devolve quantos de Kanto o jogo conta como capturados."""
        return self.call(CMD_SET_KANTO_OWNED, n)

    def fill_pc(self) -> int:
        """Enche todas as caixas do PC com um Pokémon simples; devolve quantos slots."""
        return self.call(CMD_FILL_PC)

    def set_flag(self, flag: int, on: bool = True) -> bool:
        """Liga/desliga uma flag; devolve o valor que o jogo passou a ver."""
        result = self.call(CMD_SET_FLAG, flag, int(on))
        assert result != NO_RESULT, f"SET_FLAG recusado: flag {flag:#x}"
        return bool(result)

    # --- Hack 7 - frente D: linha de amizade da página EVOLUTION -----------------------------
    def friendship_text(self, friendship: int = 0, from_open_summary: bool = False) -> bytes:
        """Bytes (sem o 0xFF) da linha de amizade: GetFriendshipLineText(`friendship`) ou a linha
        que a página EVOLUTION aberta imprimiu."""
        length = self.call(CMD_FRIENDSHIP_TEXT, friendship, 1 if from_open_summary else 0)
        assert length != NO_RESULT, ("FRIENDSHIP_TEXT recusado: " + (
            "nenhum resumo aberto" if from_open_summary else f"amizade {friendship}"))
        data = self.emu.read(self.ctl.game.syms.addr(TEXT_SYMBOL), length + 1)
        assert data[length] == 0xFF, f"texto de {length} bytes sem terminador: {data.hex()}"
        return data[:length]

    def zero_friendship(self, slot: int) -> None:
        """Zera a amizade do Pokémon do slot (SET_PARTY_MON usa 0 para "amizade base")."""
        got = self.call(CMD_FRIENDSHIP_TEXT, slot, 2)
        assert got == 0, f"FRIENDSHIP_TEXT zerou o slot {slot} mas a amizade ficou {got}"

    # --- Hack 7 frente A: tom de cor por período ------------------------------------------
    def tint_at(self, minute: int) -> tuple[int, int, int]:
        """(r, g, b) em 1/256 que DayNight_GetTintAt dá para o minuto do dia."""
        packed = self.call(CMD_TINT_AT, minute)
        assert packed != NO_RESULT, "TINT_AT não implementado nesta ROM"
        return packed & 0x3FF, (packed >> 10) & 0x3FF, (packed >> 20) & 0x3FF

    def roll_weather(self, region: int, day: int, period: int) -> int:
        """Clima (WEATHER_*) que DayNight_RollWeather sorteia para a região no dia e período."""
        assert 0 <= day < 1 << 24, day
        weather = self.call(CMD_ROLL_WEATHER, region, day | period << 24)
        assert weather != NO_RESULT, "ROLL_WEATHER não implementado nesta ROM"
        return weather

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

# --- Hack 7: dia/noite, clima e encontros por horário (enum à parte em include/test_hooks.h, ---
# a partir de 0x70; números fixos do plano, os ainda não implementados devolvem 0xFFFFFFFF)
CMD_SET_CLOCK = 0x70        # arg0 = dia, arg1 = minuto do dia -> DayNight_GetMinuteOfDay()
CMD_CLOCK_INFO = 0x71       # -> minuto do dia | período << 16
CMD_TINT_AT = 0x72          # arg0 = minuto do dia -> r | g << 10 | b << 20 (tom em 1/256)
CMD_ROLL_WEATHER = 0x73     # arg0 = região, arg1 = dia | período << 24 -> clima (DayNight_RollWeather)
CMD_LAND_SPECIES = 0x74
CMD_FRIENDSHIP_TEXT = 0x75
CMD_RARE_EGG_ROLL = 0x76
CMD_SET_KANTO_OWNED = 0x77
CMD_START_WILD_BATTLE = 0x78  # arg0 = espécie, arg1 = nível -> 1 (batalha selvagem por script de campo)
CMD_FILL_PC = 0x79
CMD_SET_FLAG = 0x7A
CMD_SPECIES_ON_MAP = 0x7B

# --- Hack 8: exclusivos do LeafGreen na natureza (enum à parte, a partir de 0x80) ---
CMD_ROLL_WILD = 0x80        # arg0 = área (0 grama, 1 água, 2 pedra, 3 pesca) | vara << 8, arg1 = 1: também
                            # começa a batalha -> espécie | nível << 16 (0xFFFFFFFF = sem essa tabela aqui)

# --- Tela de novidades do Prof. Carvalho (enum à parte, a partir de 0x90) ---
CMD_OPEN_NOVIDADES = 0x90   # script de campo com `special OpenNovidadesScreen` -> número do special
                            # (0xFFFFFFFF = fora de gSpecials); o script usa gTestText como buffer
CMD_NOVIDADES_STATE = 0x91  # -> cursor | pronta para input << 8 | ícones vivos << 16
                            # | (cartão aberto + 1, 0 = grade) << 24 (0xFFFFFFFF = fechada)
CMD_NOVIDADES_CARD = 0x92   # -> tópico | cartão << 8 | imagem (0 ícone do tópico, 1 item, 2 uma espécie,
                            # 3 duas) << 16 | sprites vivos da imagem << 24 (0xFFFFFFFF = fora do cartão)
