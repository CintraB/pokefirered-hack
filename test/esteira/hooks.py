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

    def calc_damage(self, move: int) -> int:
        """CalculateBaseDamage com o slot 0 do time atacando o slot 1 (sem crítico, clima, tela,
        insígnia nem efeito de campo; antes de STAB, eficácia e fator aleatório)."""
        damage = self.call(CMD_CALC_DAMAGE, move, 0)
        assert damage != NO_RESULT, f"golpe inválido: {move}"
        return damage

    def type_effectiveness(self, move_type: int, type1: int, type2: int) -> int:
        """Multiplicador x 100 de gTypeEffectiveness para um golpe do tipo `move_type` contra um
        defensor `type1`/`type2`, como o Cmd_typecalc aplica, sem Foresight (400 = x4, 25 = x0,25)."""
        return self.call(CMD_TYPE_EFFECTIVENESS, move_type, type1 | type2 << 8)

    # --- POK-44: conquistas e diário ----------------------------------------------------
    def conq_estado(self, num: int) -> tuple[int, int, int, int]:
        """(estado, entregue, degrau entregue, degrau atual) da conquista `num` (CONQ_*): estado
        0 pendente, 1 feita, 2 perdida; o degrau atual é 0 até as regras de estado (Task 3)."""
        packed = self.call(CMD_CONQ_ESTADO, num)
        assert packed != NO_RESULT, f"conquista inválida: {num}"
        return packed & 0xFF, packed >> 8 & 0xFF, packed >> 16 & 0xFF, packed >> 24 & 0xFF

    def conq_contador(self, k: int) -> int:
        """0 vitórias, 1 shinies, 2 origem | resumoPendente << 8, 3 magic, 4 + aba: feitas |
        válidas << 8 daquela aba (0 até a Task 3)."""
        value = self.call(CMD_CONQ_CONTADOR, k)
        assert value != NO_RESULT, f"contador inválido: {k}"
        return value

    def conq_reset(self, jogo_novo: bool) -> int:
        """jogo_novo: Conquistas_IniciarJogoNovo(); senão zera as duas áreas (save antigo, sem
        marcador). Devolve o magic."""
        return self.call(CMD_CONQ_RESET, int(jogo_novo))

    def conq_checar(self) -> int:
        """Conquistas_ChecarEstado() agora (num save sem marcador, a varredura antes); devolve
        Conquistas_AvisosPendentes()."""
        return self.call(CMD_CONQ_CHECAR)

    def conq_aplicar(self, num: int, op: int, degrau: int = 0) -> tuple[int, int, int, int]:
        """Acessor do núcleo na conquista `num`: op 0 Conquistas_Marcar, 1 Conquistas_Perder,
        2 Conquistas_SetEntregue, 3 Conquistas_SetDegrauEntregue(num, degrau). Devolve o
        conq_estado(num) depois."""
        packed = self.call(CMD_CONQ_APLICAR, num, op | degrau << 8)
        assert packed != NO_RESULT, f"conq_aplicar recusado: num {num}, op {op}"
        return packed & 0xFF, packed >> 8 & 0xFF, packed >> 16 & 0xFF, packed >> 24 & 0xFF

    def conq_pc_mon(self, box: int, pos: int, species: int, level: int = 5, shiny: bool = False,
                    chocado: bool = False) -> int:
        """Grava um Pokémon do jogador (OT) na caixa `box`, posição `pos` do PC; `chocado` = MET_LEVEL 0
        e 6 IVs 31. Espécie 0 esvazia a vaga. Devolve a espécie lida de volta."""
        opcoes = int(shiny) | int(chocado) << 1
        lida = self.call(CMD_CONQ_PC_MON, box | pos << 8 | opcoes << 16, species | level << 16)
        assert lida == species, f"conq_pc_mon recusado/errado: caixa {box}, pos {pos}, lida {lida:#x}"
        return lida

    def start_trainer_battle(self, trainer: int) -> int:
        """Começa uma batalha contra `trainer` (sem a fala de abertura; a de derrota é "…")."""
        result = self.call(CMD_START_TRAINER_BATTLE, trainer)
        assert result == 1, f"START_TRAINER_BATTLE recusado: treinador {trainer}"
        return result

    def set_party_move(self, slot: int, index: int, move: int) -> int:
        """Põe `move` (com o PP cheio) no golpe `index` (0-3) de gPlayerParty[slot]; devolve o golpe lido."""
        lido = self.call(CMD_SET_PARTY_MOVE, slot | index << 8, move)
        assert lido == move, f"SET_PARTY_MOVE recusado: slot {slot}, golpe {index}, {move} (lido {lido:#x})"
        return lido

    def party_size(self, n: int) -> int:
        """Fica só com os `n` primeiros Pokémon do time; devolve gPlayerPartyCount."""
        count = self.call(CMD_PARTY_SIZE, n)
        assert count != NO_RESULT, f"PARTY_SIZE recusado: {n}"
        return count

    def conq_captura(self, species: int, ball: int) -> int:
        """Conquistas_OnCaptura de um `species` nv 30 (em gEnemyParty[0]) capturado com `ball`."""
        result = self.call(CMD_CONQ_CAPTURA, species, ball)
        assert result == 1, f"CONQ_CAPTURA recusado: espécie {species}, bola {ball}"
        return result

    def conq_chocar(self, slot: int, species: int, shiny: bool = False, ivs31: bool = False) -> None:
        """Choca, pelo special de verdade, um ovo do jogador de `species` posto em gPlayerParty[slot]."""
        lido = self.call(CMD_CONQ_CHOCAR, slot | (int(shiny) | int(ivs31) << 1) << 8, species)
        assert lido == species, f"CONQ_CHOCAR recusado/errado: slot {slot}, espécie {species} (lido {lido:#x})"

    def diario_entrada(self, evt: int) -> dict | None:
        """A entrada do diário do evento `evt` (DIARIO_EVT_*), decodificada por conquistas.parse_entrada;
        None se o slot está vazio (ordem 0)."""
        from .conquistas import DIARIO_ENTRADA_SIZE, parse_entrada
        ordem = self.call(CMD_DIARIO_ENTRADA, evt)
        assert ordem != NO_RESULT, f"DIARIO_ENTRADA recusado: evento {evt}"
        if ordem == 0:
            return None
        entrada = parse_entrada(self.emu.read(self.ctl.game.syms.addr(TEXT_SYMBOL), DIARIO_ENTRADA_SIZE))
        assert entrada["ordem"] == ordem, (entrada, ordem)
        return entrada

    def conq_silencio(self, on: bool) -> int:
        """Liga (True) ou desliga o silêncio do aviso das conquistas: em silêncio, o campo nem checa o estado."""
        result = self.call(CMD_CONQ_SILENCIO, int(on))
        assert result == int(on), f"CONQ_SILENCIO recusado: {result:#x}"
        return result

    def encher_bolso(self, item: int, pc: bool = False) -> int:
        """Enche o bolso de `item` (o próprio item e outros do mesmo bolso, 999 cada); com `pc`, também os 30
        espaços do PC de itens. Devolve os espaços ocupados (bolso + PC)."""
        result = self.call(CMD_ENCHER_BOLSO, item, int(pc))
        assert result != NO_RESULT, f"ENCHER_BOLSO recusado: item {item}"
        return result

    def open_conquistas(self, diario: bool = False) -> int:
        """Abre a tela de conquistas (ou o diário) pelo special, de um script de campo; devolve o número do
        special. A tela monta nos quadros seguintes: espere `conq_tela()` com a entrada pronta."""
        result = self.call(CMD_OPEN_CONQUISTAS, int(diario))
        assert result != NO_RESULT, "Conquistas_AbrirTelaDoScript fora de gSpecials"
        return result

    def conq_tela(self) -> tuple[int, int, int, bool] | None:
        """(modo, aba, topo da lista, entrada pronta) da tela de conquistas; None com a tela fechada."""
        raw = self.call(CMD_CONQ_TELA)
        if raw == NO_RESULT:
            return None
        return raw & 0xFF, raw >> 8 & 0xFF, raw >> 16 & 0xFF, bool(raw >> 24 & 0xFF)

    def conq_tela_diario(self) -> tuple[int, int, int] | None:
        """(quantas entradas, DIARIO_EVT_* da linha selecionada, primeira linha visível) do modo diário; None com a
        tela fechada ou no modo conquistas. A linha selecionada é o `cursor` de `conq_tela()[2]`."""
        raw = self.call(CMD_CONQ_TELA, 1)
        if raw == NO_RESULT:
            return None
        return raw & 0xFF, raw >> 8 & 0xFF, raw >> 16 & 0xFF

    # --- atalhos das revanches por degrau (POK-42) -------------------------------------
    def build_trainer_party(self, trainer: int, rematch: bool) -> tuple[int, int, bool]:
        """Monta em gEnemyParty o time que CreateNPCTrainerParty faria para `trainer` (como revanche do Vs. Seeker
        ou não), sem começar a batalha; devolve (tamanho do time, degrau aplicado, dupla). O time sai em
        `Game.enemy_party()`."""
        raw = self.call(CMD_BUILD_TRAINER_PARTY, trainer, int(rematch))
        assert raw != NO_RESULT, f"BUILD_TRAINER_PARTY recusado: treinador {trainer}"
        return raw & 0xFF, raw >> 8 & 0xFF, bool(raw >> 16 & 1)

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

# --- POK-43: físico/especial por golpe (enum à parte, a partir de 0xA0) ---
CMD_CALC_DAMAGE = 0xA0      # arg0 = golpe, arg1 = 0 -> CalculateBaseDamage: gPlayerParty[0] ataca gPlayerParty[1]
                            # (BattlePokemon montados na hora; sem crítico, clima, tela, insígnia nem efeito de campo)
CMD_TYPE_EFFECTIVENESS = 0xA1  # arg0 = tipo do golpe, arg1 = tipo1 | tipo2 << 8 do defensor -> multiplicador x 100
                              # (gTypeEffectiveness como no Cmd_typecalc, sem Foresight; POK-45)

# --- POK-44: conquistas e diário de batalhas (enum à parte, a partir de 0xB0) ---
CMD_CONQ_ESTADO = 0xB0      # arg0 = num -> estado | entregue << 8 | degrau entregue << 16 | degrau atual << 24
                            # (0xFFFFFFFF = num inválido)
CMD_CONQ_CONTADOR = 0xB1    # arg0 = 0 vitórias, 1 shinies, 2 origem | resumoPendente << 8, 3 magic,
                            # 4 + aba -> feitas | válidas << 8 (Conquistas_ContarAba)
CMD_CONQ_RESET = 0xB2       # arg0 = 0 zera as duas áreas (save antigo), 1 Conquistas_IniciarJogoNovo -> magic
CMD_CONQ_CHECAR = 0xB3      # Conquistas_ChecarEstado() -> Conquistas_AvisosPendentes()
CMD_CONQ_APLICAR = 0xB4     # arg0 = num, arg1 = op | degrau << 8 (0 Marcar, 1 Perder, 2 SetEntregue,
                            # 3 SetDegrauEntregue) -> o mesmo de CMD_CONQ_ESTADO depois
CMD_CONQ_PC_MON = 0xB5      # arg0 = caixa | posição << 8 | opções << 16 (1 shiny, 2 chocado pelo jogador: MET_LEVEL 0
                            # e 6 IVs 31), arg1 = espécie | nível << 16 (espécie 0 esvazia) -> espécie lida na caixa
CMD_START_TRAINER_BATTLE = 0xB6  # arg0 = treinador (TRAINER_*) -> 1: batalha sem fala de abertura por script de campo
                                 # em RAM (trainerbattle_no_intro); derrota volta ao Centro como de costume
CMD_SET_PARTY_MOVE = 0xB7   # arg0 = slot | golpe (0-3) << 8, arg1 = golpe (PP cheio) -> golpe lido
CMD_PARTY_SIZE = 0xB8       # arg0 = n -> fica só com os n primeiros do time -> gPlayerPartyCount
CMD_CONQ_CAPTURA = 0xB9     # arg0 = espécie, arg1 = bola -> gEnemyParty[0] nv 30 e Conquistas_OnCaptura -> 1
CMD_CONQ_CHOCAR = 0xBA      # arg0 = slot | opções << 8 (1 shiny, 2 seis IVs 31), arg1 = espécie -> ovo do jogador no slot,
                            # chocado pelo ScriptHatchMon (AddHatchedMonToParty) -> espécie | ovo << 16 lidos
CMD_DIARIO_ENTRADA = 0xBB   # arg0 = evento (DIARIO_EVT_*) -> ordem (0 = vazia; 0xFFFFFFFF = evento inválido);
                            # os 20 bytes da struct DiarioEntrada em gTestText
CMD_CONQ_SILENCIO = 0xBC    # arg0 = 1 silencia o aviso das conquistas (nem checa), 0 volta -> arg0 (só na ROM de teste)
CMD_ENCHER_BOLSO = 0xBD     # arg0 = item: os espaços livres do bolso dele com itens distintos do mesmo bolso, 999 cada,
                            # a começar pelo próprio item; arg1 = 1 enche também os 30 do PC de itens -> espaços ocupados
                            # (bolso + PC)
CMD_OPEN_CONQUISTAS = 0xBE  # arg0 = modo (0 conquistas, 1 diário): script de campo com setvar VAR_0x8004 e `special
                            # Conquistas_AbrirTelaDoScript` -> número do special (0xFFFFFFFF = fora de gSpecials)
CMD_CONQ_TELA = 0xBF        # -> modo | aba << 8 | topo da lista (conquistas) ou cursor (diário) << 16 | entrada pronta << 24
                            # (0xFFFFFFFF = fechada); arg0 = 1: no diário, n | evento selecionado << 8 | topo << 16

# --- POK-42: revanches por degrau (enum à parte, a partir de 0xC0) ---
CMD_BUILD_TRAINER_PARTY = 0xC0  # arg0 = treinador (TRAINER_*), arg1 = 1 revanche do Vs. Seeker / 0 combate normal ->
                                # tamanho do time | degrau aplicado << 8 | dupla << 16 (time em gEnemyParty;
                                # 0xFFFFFFFF = treinador inválido)
