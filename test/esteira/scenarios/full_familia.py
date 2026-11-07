"""Modo completo: a Família Sombra (POK-51), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). O aviso das conquistas fica em
silêncio (ele pausa o campo). A ocupação vem do atalho FAMILIA_SET; as lutas começam pelos atalhos
START_TRAINER_BATTLE (capanga, sem fala de abertura) e FAMILIA_GEMEOS (o trainerbattle_double de verdade).

Task 3 (capangas como treinadores):

- `familia/capanga_apresentacao`: ocupação 1 ATIVA, batalha contra TRAINER_FAMILIA_CAPANGA_1: o texto de abertura é
  gText_FamiliaCapangaQuerLutar e o sprite do oponente é o Pokémon (callbacks do selvagem), não um humano; nenhum
  sprite está no SpriteCB_TrainerSlideIn. Tela `familia_capanga_batalha` (só gravada; a comparação entra com o
  registro dos pontos de tela, Ruling R6);
- `familia/bola_capanga`: 5 Poké Bolas a mais na bolsa; uma jogada: o texto do desvio, a bolsa com as mesmas Poké
  Bolas e a batalha segue (de volta ao menu de ação, o capanga em campo);
- `familia/vitoria_sem_premio`: vencendo o capanga 1 (Shadow Ball): "Você derrotou Capanga da Família!", sem o
  prêmio em dinheiro (o dinheiro não muda) e com a flag do treinador ligada;
- `familia/thief`: Mewtwo com Ladrão (sem item) e com Truque (segurando Restos) contra o capanga 1: depois do turno o
  Mewtwo continua sem item / com os Restos (na batalha e no time) e o capanga com o Talismã Fantasma;
- `familia/time_por_ocupacao`: BUILD_TRAINER_PARTY na ocupação 1 e na 2: espécie, nível, item e golpes do capanga 1
  batem com src/data/familia_sombra_times.h; gêmeos (2, dupla) e as 2 lutas do pedágio (plantel, níveis 56/58 + 6);
- `familia/gemeos_dupla`: 2 Pokémon no time, FAMILIA_GEMEOS: 2 Machamp nv 60 em campo (batalhadores 1 e 3), a fala
  gText_FamiliaGemeosQueremLutar, sem sprite de treinador e a música MUS_VS_GYM_LEADER. Tela `familia_gemeos_batalha`.

Task 4 (andares 4-5, efeito de filme e o chefe). Os andares 4-5 só existem na Task 5 (Ruling R4): o encontro começa pelo
atalho FAMILIA_WILD, que monta o mesmo Pokémon do encontro do andar e liga BATTLE_TYPE_FAMILIA.

- `familia/encontro_wild`: espécie do plantel da ocupação 1, nível 54-58, item e golpes do plantel, o texto do
  capanga, sprite do selvagem, a música de treinador e a paleta do oponente = noir() da prévia aplicado à paleta
  normal da espécie (gPlttBufferUnfaded, índice 0 intocado). Tela `familia_filme_batalha`;
- `familia/passos_andar_escuro`: o atalho FAMILIA_PASSOS roda o TryStandardWildEncounter de verdade com o andar escuro
  forçado (o mapa sem tabela própria): com chefe ativo sai um capanga do plantel; sem chefe, 400 passos sem encontro;
- `familia/bola_selvagem`: a bola desviada e não gasta, como no capanga;
- `familia/thief_selvagem`: Ladrão e Truque não tiram o item do encontro;
- `familia/chefe`: o special FamiliaSombra_IniciarChefe: abertura "GENGAR, O DOM, quer acertar as contas!", Gengar
  shiny nv 62 com os golpes e o item da tabela,
  batalha lendária com BATTLE_TYPE_FAMILIA_CHEFE (sem BATTLE_TYPE_FAMILIA), gTrainerBattleOpponent_A = 0,
  MUS_VS_LEGEND e as cores shiny sem filme. Tela `familia_chefe_batalha`;
- `familia/bola_chefe`: a Master Ball é gasta e captura o chefe;
- `familia/chefe_ia`: Golem nv 100 (imune a Raio) só com Endurecer contra o chefe por 3 turnos: a IA usa as 5 flags
  de chefe (aiLogicId 9) e nunca escolhe Raio, nem Comedor de Sonhos com o Golem acordado, nem Hipnose com ele
  dormindo (ao acaso, passar nos 3 turnos tem 1/8 de chance).

Task 5 (o prédio da Rota 23: 6 andares e a sala do Dom). As insígnias vêm do atalho SET_FLAG (Ruling R7); o atalho
WARP só chega a y < 128, então a frente da porta (4, 150) se alcança saindo pelo tapete do 1º andar.

- `familia/porta_trancada`: sem a 8ª insígnia a porta não abre e a placa fala do charuto (tela
  `familia_porta_trancada`); com ela, entrar na Rota 23 liga a ocupação 1 e a porta leva ao 1º andar (tela
  `familia_rota23_predio`);
- `familia/ciclo`: save antigo com a insígnia = ocupação 1; queda + 6 meios-dias = sem chefe; +7 = ocupação 2 com
  itens e treinadores de volta, uma vez só; a 2ª queda + 7 = continua sem chefe e o andar fica vazio;
- `familia/capanga_ve`: o capanga 2 do 1º andar vê o jogador, vem até ele, luta e some depois da derrota;
- `familia/subida`: da porta ao 6º andar pelas escadas (música, escuro e névoa por andar; o Gengar shiny e os 2
  Machamp na sala); telas `familia_andar_1`, `familia_andar_4` e `familia_sala_do_dom`;
- `familia/encontro_andar4` e `familia/sem_encontro_sem_chefe` (Ruling R4): passos de verdade no 4º andar;
- `familia/gemeos_um_pokemon`: com 1 Pokémon a dupla é recusada e nada começa;
- `familia/chefe_fuga`: gêmeos já vencidos, a cena vai direto ao chefe; fugindo, ele fica e não há rosa;
- `familia/rosa`: a cena inteira (gêmeos, Dom) e a Rosa Vermelha na bolsa (tela `familia_rosa`).

Task 6 (o pedágio da Rota 23, nos dois sentidos). O cobrador é um Persian de chapéu no corredor (x 13-15, y 145-148); o
jogador chega do sul pela porta do prédio e do norte por um WARP a (10, 126) mais uma caminhada; o dinheiro vem da
escrita direta no save (como full_egg) e a Rota 23 sem guardas (VAR_MAP_SCENE_ROUTE23 = 0).

- `familia/pedagio_paga`: o Persian está lá; pagando ¥1.000 o dinheiro cai 1000, a flag liga e o jogador passa; entrar
  no prédio e sair não cobra de novo (tela `familia_pedagio`, a pergunta de pagar);
- `familia/pedagio_sem_dinheiro`: com ¥999 vai direto ao menu "Voltar depois / Passar à força" (sem a pergunta de
  pagar) e voltar empurra um passo para o sul; recusando com dinheiro, a pergunta vem antes do mesmo menu;
- `familia/pedagio_forca`: passar à força = TRAINER_FAMILIA_PEDAGIO_1 e depois _2 (2 espécies diferentes do plantel),
  sem prêmio, e a passagem fica paga;
- `familia/pedagio_volta`: pago, sair pela Victory Road 1F limpa a flag; descendo, cobra no lado norte (voltar
  depois empurra um passo para o norte; pagando, passa);
- `familia/pedagio_sem_chefe`: sem chefe não há cobrador e o corredor fica livre.

Task 7 (conquistas e diário). O estado das conquistas vem de conq_reset(True) (jogo novo) e o aviso fica em silêncio:

- `familia/conquista_dom`: com o jogo já zerado (FLAG_SYS_GAME_CLEAR), a cena do 6º andar até vencer o Dom (gêmeos já
  vencidos): "Vencer o Dom" passa de pendente a feita e as outras 4 seguem pendentes; o diário ganha a entrada
  "O Dom" (Gengar, derrotado, o time e os turnos); telas `familia_conquistas_batalha` (aba Batalha rolada até o fim)
  e `familia_diario_dom` (o diário com a entrada);
- `familia/gengar_fora_nao_conta`: um Gengar selvagem comum (nv 62) vencido não grava a entrada do Dom nem a conquista;
- `familia/pedagio_forca` também confere "Pagar ou lutar": pendente antes das 2 lutas, feita depois.

Ajustes do Cintra (depois das telas da v67):

- `familia/rosa_bolsa_cheia`: o bolso de itens-chave cheio (30 itens pelo atalho GIVE_ITEM), o Dom vencido:
  FLAG_FAMILIA_ROSA_1 ligada (a redoma da Sala de Troféus acende por ela), a Rosa Vermelha fora da bolsa e a fala
  "…foi enviada direto à Sala de Troféus da Ilha Sete!";
- `familia/continue_rota23_ativa`, `_sem_chefe`, `_fechado`: salvar parado na Rota 23 (lado sul do pedágio), resetar e
  CONTINUAR (só o ON_LOAD roda): mapa, layout e tile iguais, porta trancada só antes da 8ª insígnia e o Persian
  visível exatamente quando o pedágio está armado (VAR_TEMP_3). Telas `familia_continue_rota23_*` só gravadas.

- `familia/chefe_balcao`: depois de fugir do chefe, da frente da mesa (8, 6) olhando para cima, o A atravessa os 2
  tiles de balcão (MB_COUNTER na coluna do meio da mesa) e a batalha do chefe recomeça sem sair da sala.

O quadro da sala do Dom (retrato do chefe em preto e branco, trocado no ON_LOAD do 6º andar):

- `familia/subida` também confere o retrato do Dom na ocupação 1;
- `familia/quadro_cobrador`: ocupação 2 (atalho FAMILIA_SET), subindo pela escada do 5º andar: o retrato do Cobrador
  (tela `familia_quadro_cobrador`, só gravada); sem chefe fica o do último chefe; ocupação 3 = tela vazia.

POK-54, Task 7 (ocupações 3 e 4: o motor). O chefe cai pelo atalho FAMILIA_CHEFE_CAIU (o special da cena do 6º andar):

- `familia/ciclo_ate_o_fim`: a queda do chefe 2 + 7 meios-dias traz a ocupação 3 (ATIVA, repovoada uma vez só); a queda do
  3 + 7 traz a 4; a queda do 4 deixa ENCERRADA, com a queda dele gravada (Task 10), e +20 meios-dias depois continua
  ENCERRADA;
- `familia/chefe_mercenario`: o special com a ocupação 3: "GARCHOMP, O MERCENÁRIO, ...", Garchomp shiny nv 74 com os
  golpes e a Lum Berry da tabela, MUS_VS_LEGEND e a paleta shiny. Tela `familia_chefe_mercenario`;
- `familia/chefe_pesadelo`: ocupação 4: Darkrai shiny nv 80, Leftovers, MUS_VS_DEOXYS. Contra um Golem nv 100 só com
  Endurecer a IA abre com Vazio Negro e não usa Comedor de Sonhos com o Golem acordado. Tela `familia_chefe_pesadelo`;
- `familia/captura_marca`: Master Ball no Mercenário e a queda: só a flag de captura 3 liga. O Pesadelo vencido sem
  captura deixa a flag 4 desligada e o estado ENCERRADA;
- `familia/conquistas_parte2`: um Garchomp selvagem comum não grava nada; o Mercenário vencido marca a conquista 44 e a
  entrada "O Mercenário" (DERROTOU); o Pesadelo capturado marca a 45 e "O Pesadelo" (CAPTURADO).

POK-54, Task 8 (ocupações 3 e 4: o prédio, as falas e os retratos):

- `familia/sala_mercenario` e `familia/sala_pesadelo`: subindo ao 6º andar na ocupação 3 (4), Garchomp (Darkrai) shiny de
  chapéu, os 2 Gligar (Dusclops) e o retrato dele no quadro. Telas `familia_sala_mercenario` e `familia_sala_pesadelo`;
- `familia/rosa_azul`: a cena inteira da ocupação 3 (gêmeos Gligar, Mercenário vencido): ITEM_ROSA_AZUL na bolsa;
- `familia/rosa_negra_bolsa_cheia`: ocupação 4 com o bolso de itens-chave cheio: a rosa não entra, FLAG_FAMILIA_ROSA_4
  fica ligada e o estado vira ENCERRADA;
- `familia/redomas_completas`: com as 4 rosas a Sala de Troféus acende as 4 redomas. Tela `sala_trofeus_completa`.

POK-54, Task 9 (o dossiê do caso, src/dossie.c, aberto pelo atalho DOSSIE_ABRIR = o special num script de campo):

- `dossie/navegacao`: abre na capa; → avança, ← volta, ← na capa não muda; A até o fim passa por todas as páginas na
  ordem de sDossiePaginas; → na última não sai dela; A na última fecha e o jogo volta ao campo com o script terminado.
  Aberto de novo, B na 3ª página fecha. Telas `dossie_capa` e `dossie_depois`;
- `dossie/carimbos`: as 4 rosas e só FLAG_FAMILIA_CAPTURADO_3: DERROTADO nas fichas 1, 2 e 4, CAPTURADO na 3, nenhum na
  capa e no Depois. Telas `dossie_ficha_dom` (DERROTADO) e `dossie_ficha_mercenario_capturado`.

POK-54, Task 10 (o fechamento: a polícia na porta, a Oficial Jenny e a entrega dos chefes apreendidos). O estado vem de
FAMILIA_SET (ocupação 4, ENCERRADA) e SET_FLAG; o jogador sai do 1º andar pelo tapete e chega na porta lacrada (4, 149):

- `familia/cena_jenny`: nada capturado, 5 no time. A cena começa sozinha: a Jenny vem até o jogador (tela
  `familia_jenny_cena`), entrega o Garchomp (time, que fica com 6) e o Darkrai (PC), ambos shiny, nível 74/80, sem item e
  com os golpes do chefe, vistos e capturados na Dex. A pergunta do dossiê vem e "Não" só agradece. As 3 flags ligam, a
  Jenny volta ao posto e o jogador sai da porta;
- `familia/jenny_de_novo`: falando com a Jenny, a fala, a pergunta e "Sim": o dossiê abre (capa) e B volta ao campo. Sem
  entrega repetida;
- `familia/entrega_capturado`: com FLAG_FAMILIA_CAPTURADO_3 só o Darkrai é entregue (ao time);
- `familia/entrega_time_cheio`: com 6 no time os dois vão ao PC e o texto avisa;
- `familia/entrega_pc_cheio`: time e PC cheios: nada é entregue, as ENTREGUE ficam desligadas, a Jenny pede espaço; abrindo
  2 vagas e falando de novo a entrega acontece;
- `familia/porta_lacrada`: o metatile das faixas (sem warp): a porta não abre, a placa fala da polícia, sem cobrador, sem
  pedágio e sem capangas. Tela `familia_policia_porta`;
- `familia/policia_ambiente`: os 2 policiais, o Growlithe e o Arcanine falam.

Rodada de correção 1 (revisão da Task 10):

- `familia/entrega_pc_cheio` também conversa 3 vezes com tudo cheio e confere que `shiniesObtidos` não muda (a vaga é
  conferida antes de criar o Pokémon) e que os 2 recebidos de verdade contam;
- `familia/entrega_caixa_cheia`: a caixa atual cheia: os dois vão para a caixa 2 e o aviso diz a caixa que estava cheia;
- `familia/cena_jenny_sim`: nada a entregar e a resposta é Sim: o dossiê abre no meio da cena, a Jenny volta ao posto e
  o jogador sai livre da porta;
- `familia/cena_jenny_corda`: Corda de Fuga de verdade (bolsa) de dentro do prédio: o escape warp (4, 150) chega certo
  (y >= 128) e a Jenny para em (4, 151);
- as 3 cenas conferem onde a Jenny está quando a 1ª fala abre (ela já terminou de andar);
- `familia/continue_rota23_*` conferem que a polícia não aparece no CONTINUAR sem a Família encerrada.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only familia
"""

import importlib.util
import json
import re

from ..battle import (ACTION_FIGHT, B_OUTCOME_CAUGHT, MENU_TIMEOUT, MOVE_FUNC_SUFFIX, NICKNAME_COMMAND,
                      BattleDriver)
from ..breeding import header_defines
from ..game import POKEMON_SIZE, SB1_MONEY, mon_checksum_ok
from .. import conquistas as cq
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_LEFT, KEY_R, KEY_RIGHT, KEY_UP
from ..hooks import CMD_GIVE_ITEM, CMD_SET_VAR, CMD_START_WILD_BATTLE, CMD_WARP, Mailbox
from ..nav import Navigator
from . import REPO_ROOT, ScenarioContext
from .base import YESNO_TASK, Abort
from .full_casas import SALA_REDOMAS
from ..field_menu import STARTMENU_BAG
from .quick_catch_save import CatchSaveScenario

ESTADO_FECHADO = 0                   # FAMILIA_ESTADO_FECHADO (include/constants/familia_sombra.h)
ESTADO_ATIVA = 1                     # FAMILIA_ESTADO_ATIVA
ESTADO_SEM_CHEFE = 2                 # FAMILIA_ESTADO_SEM_CHEFE
ESTADO_ENCERRADA = 3                 # FAMILIA_ESTADO_ENCERRADA (POK-54: o 4º chefe caiu)
PASSOS = 400                         # passos do caso familia/passos_andar_escuro
SPRITE_SIZE, SPRITE_CALLBACK, SPRITE_DATA, SPRITE_IN_USE = 0x44, 0x1C, 0x2E, 0x3E   # struct Sprite
MAX_SPRITES = 64
# o Pokémon do oponente que aparece direto (OpponentHandleLoadMonSprite → SpriteCB_EnemyMon e seguintes)
WILD_MON_CALLBACKS = {"SpriteCB_EnemyMon", "SpriteCB_MoveWildMonToRight", "SpriteCB_WildMonShowHealthbox",
                      "SpriteCallbackDummy_2"}
TRAINER_SLIDE = "SpriteCB_TrainerSlideIn"
STRING_BYTES = 300                   # gDisplayedStringBattle[300]
# Telas que o cenário grava em OUT/telas/ e que entram na comparação com as referências (esteira/refs.py)
SCREEN_POINTS = ("familia_capanga_batalha", "familia_filme_batalha", "familia_chefe_batalha", "familia_gemeos_batalha",
                 "familia_chefe_mercenario", "familia_chefe_pesadelo",   # POK-54, Task 7
                 "familia_sala_mercenario", "familia_sala_pesadelo", "sala_trofeus_completa",   # POK-54, Task 8
                 "dossie_capa", "dossie_ficha_dom", "dossie_ficha_mercenario_capturado", "dossie_depois",   # POK-54, Task 9
                 "familia_jenny_cena", "familia_policia_porta",   # POK-54, Task 10
                 "familia_rosa", "familia_porta_trancada", "familia_rota23_predio", "familia_pedagio",
                 "familia_andar_1", "familia_andar_4", "familia_sala_do_dom",
                 "familia_conquistas_batalha")   # `familia_diario_dom` é gravada mas fica fora: traz o TEMPO de jogo (00:08 x 00:09)
SONG_SIZE = 8                        # struct Song (header, ms, me)
BATTLE_MON_SIZE, BATTLE_MON_ITEM = 0x58, 0x2E   # struct BattlePokemon (include/pokemon.h)
PLAYER_LEVEL = 60
INTRO_TIMEOUT = 3000
EXTRA_BALLS = 5
DODGE_TEXT = "desvia a Poké Bola"
TEAM = (("SPECIES_MEWTWO", PLAYER_LEVEL), ("SPECIES_SNORLAX", PLAYER_LEVEL))
TIMES_H = REPO_ROOT / "src" / "data" / "familia_sombra_times.h"
BATTLE_TYPE_TRAINER, BATTLE_TYPE_LEGENDARY = 1 << 3, 1 << 13
BATTLE_TYPE_FAMILIA, BATTLE_TYPE_FAMILIA_CHEFE = 1 << 20, 1 << 21   # include/constants/battle.h
OBJ_PLTT = 256                       # gPlttBufferUnfaded: as paletas de sprite começam na 256; batalhador n = 256 + 16n
PALETTE_ENTRY = 8                    # struct CompressedSpritePalette (data, tag)
BATTLE_MON_STATUS1 = 0x4C            # struct BattlePokemon
STATUS1_SLEEP = 0x7
AI_RESOURCES, AI_LOGIC_ID = 0x14, 0x11   # gBattleResources->ai, AI_ThinkingStruct.aiLogicId
CHEFE_AI_BITS = 9                    # FAMILIA_AI_CHEFE vai até AI_SCRIPT_HP_AWARE (bit 8)
AI_TURNS = 3
# Task 5: o prédio (posições de tools/familia_sombra/predio.json e dos map.json)
PORTA_FRENTE = (4, 150)              # Rota 23: o tile na frente da porta do prédio (porta em (4, 149))
PORTA = (4, 149)
ROTA23_SUL = (10, 126)               # Rota 23: um tile livre ao sul
SAIDA_1F = (7, 11)                   # 1º andar: o tapete da saída
ANTES_DA_ESCADA = (10, 3)            # andares 1-5: o tile à esquerda do warp da escada para cima (11, 3)
SAIDA_ESCADA_6F = (4, 3)             # 6º andar: onde a escada deixa o jogador; um passo para baixo é o gatilho (4, 4)
VAI_E_VEM_4F = ((4, 6), ("down", "up"))   # 4º andar: corredor da esquerda, (4, 6) a (4, 10) e de volta
PASSOS_ANDAR = 400
# 1º andar: do tapete (7, 11) até (10, 6), na linha do capanga 2 (12, 6), que vem até (11, 6)
VISTA_CAPANGA_2 = ((("right", 2), ("up", 2), ("right", 1), ("up", 3)), (11, 6))
OBJECT_EVENT_XY, MAP_OFFSET = 0x10, 7  # ObjectEvent.currentCoords (coordenadas do mapa + 7)
QUEDA_ROSA = 30                      # meio-dia do relógio na vitória do caso familia/rosa
TRAINER_FLAGS_START = 0x500
REPEL_VAR = 0x4020                   # VAR_REPEL_STEP_COUNT
SB1_FLASH_LEVEL = 0x30               # SaveBlock1.flashLevel
SB2_GAME_CLOCK = 0x90                # SaveBlock2.gameClockFrames (src/day_night.c)
GAME_CLOCK_FRAMES_PER_MINUTE, GAME_CLOCK_START_MINUTE, HALF_DAY_MINUTES = 150, 480, 720   # constants/day_night.h
BUTTON_WAIT_STATES = {1, 2, 3}       # RENDER_STATE_WAIT/CLEAR/SCROLL_START: o texto espera um botão
PALETTE_FADE_ACTIVE = 7              # byte de gPaletteFade com o bit `active` (0x80)
OBJECT_EVENTS_COUNT, OBJECT_EVENT_SIZE, OBJECT_EVENT_LOCAL_ID, OBJECT_EVENT_GFX = 16, 0x24, 8, 5
FOG_CALLBACK = "FogHorizontalSpriteCallback"
LOCALID_PLAYER, LOCALID_FOLLOWER = 0xFF, 0xFE
# Task 7: estados das conquistas (include/constants/conquistas.h), o resultado do diário e a tela de conquistas
CONQ_PENDENTE, CONQ_FEITA = 0, 1
DIARIO_CAPTURADO, DIARIO_DERROTOU = 2, 3
CONQ_BATALHA_ABA = 1
TELA_PRONTA_TIMEOUT = 300
TELA_ASSENTA = 20
DESCE_ATE_O_FIM = 14                 # apertos de Baixo: a aba Batalha tem 12 linhas ativas
# Task 6: o pedágio
LOCALID_COBRADOR = 8                 # 8º objeto de Route23 (os 7 guardas vêm antes; o teste estático confere)
VAR_MAP_SCENE_ROUTE23 = 0x405F
MULTICHOICE_TASK = "Task_MultichoiceMenu_HandleInput"
PEDAGIO_SUL = (14, 148)              # um passo antes do gatilho do lado sul (14, 147)
PEDAGIO_NORTE = (14, 144)            # um passo antes do gatilho do lado norte (14, 145)
PEDAGIO = 1000
VR_1F_LIVRE = (11, 19)               # Victory Road 1F: tile livre ao lado do warp de volta à Rota 23
# Ajustes do Cintra: CONTINUAR parado na Rota 23 e a rosa com o bolso de itens-chave cheio
PREDIO_JSON = REPO_ROOT / "tools" / "familia_sombra" / "predio.json"
ITEMS_JSON = REPO_ROOT / "src" / "data" / "items.json"
SB1_VARS, VARS_START = 0x1000, 0x4000  # SaveBlock1.vars (include/global.h)
VAR_TEMP_3 = 0x4003                  # o pedágio armado (Route23_EventScript_ArmarPedagio)
MAP_HEADER_LAYOUT_ID = 0x12          # struct MapHeader.mapLayoutId
BACKUP_LAYOUT_WIDTH, BACKUP_LAYOUT_MAP = 0, 8   # VMap, struct BackupMapLayout (Xsize, map)
OBJECT_EVENT_FLAGS_1, INVISIBLE_BIT = 1, 1 << 5   # ObjectEvent: o bit 13 (invisible) é o bit 5 do 2º byte
KEY_ITEMS_POCKET = 1                 # índice do bolso de itens-chave em SB1_BAG_POCKETS
BAG_KEYITEMS_COUNT = header_defines(REPO_ROOT, "global.h")["BAG_KEYITEMS_COUNT"]   # include/constants/global.h
FRENTE_DA_MESA = (8, 6)              # 6º andar: na frente da coluna do meio da mesa (balcão de 2 tiles até o chefe)
# Task 9: o dossiê (src/dossie.c): ordem das páginas lida de src/data/dossie_textos.h
DOSSIE_TEXTOS_H = REPO_ROOT / "src" / "data" / "dossie_textos.h"
DOSSIE_CAPA, DOSSIE_DEPOIS = 0, 5
CARIMBO_NENHUM, CARIMBO_DERROTADO, CARIMBO_CAPTURADO = 0, 1, 2
DOSSIE_PRONTO_TIMEOUT = 300
DOSSIE_MUSICA = re.search(r"#define DOSSIE_MUSICA (MUS_\w+)",
                          (REPO_ROOT / "src" / "dossie.c").read_text(encoding="utf-8")).group(1)
DOSSIE_MUSICA_ASSENTA = 30            # quadros depois de fechar até conferir a música do campo
DOSSIE_TECLA = dict(hold=6, release=12)   # a troca de página leva mais de 1 quadro (texto da janela de 30x20)
# Task 10: a polícia na porta (data/maps/Route23/map.json; os LOCALID_* são o índice no array + 1, o teste estático confere)
LOCALID_JENNY, LOCALID_POLICIAL_1, LOCALID_POLICIAL_2, LOCALID_GROWLITHE, LOCALID_ARCANINE = 9, 10, 11, 12, 13
JENNY_POSTO = (6, 150)               # onde a Jenny fica (vem até o jogador na cena e volta)
JENNY_DE_FRENTE = (6, 151)           # o tile de onde se fala com ela (olhando para cima)
LOCALIDS_POLICIA = (LOCALID_JENNY, LOCALID_POLICIAL_1, LOCALID_POLICIAL_2, LOCALID_GROWLITHE, LOCALID_ARCANINE)
LOCALIDS_CAPANGAS_1F = {1, 2, 3}     # os 3 capangas do 1º andar (os 3 primeiros objetos de Route23_UnusedHouse)
QUEDA_FIM = 40                       # meio-dia do relógio em que o Pesadelo caiu nos casos do fechamento
TOTAL_BOXES = 14                     # TOTAL_BOXES_COUNT
SB1_ESCAPE_WARP = 0x24               # SaveBlock1.escapeWarp (struct WarpData: grupo, mapa, warp, pad, x s16, y s16)


def dossie_chefes() -> list[int]:
    """O chefe de cada página do dossiê, na ordem de sDossiePaginas (0 capa, 1-4, 5 depois)."""
    corpo = re.search(r"sDossiePaginas\[\] = \{(.*?)\n\};", DOSSIE_TEXTOS_H.read_text(encoding="utf-8"), re.S).group(1)
    nomes = {"DOSSIE_CAPA": DOSSIE_CAPA, "DOSSIE_DEPOIS": DOSSIE_DEPOIS}
    return [nomes[c] if c in nomes else int(c) for c in re.findall(r"\{(\w+), \d+, \d+,", corpo)]


def _noir_tool():
    spec = importlib.util.spec_from_file_location("familia_noir", REPO_ROOT / "tools" / "familia_sombra" / "noir.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def lz77(data: bytes) -> bytes:
    """Descompacta o LZ77 do BIOS do GBA (cabeçalho 0x10 + tamanho de 24 bits)."""
    assert data[0] == 0x10, data[0]
    size = int.from_bytes(data[1:4], "little")
    out, i = bytearray(), 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                length = (data[i] >> 4) + 3
                disp = ((data[i] & 0xF) << 8 | data[i + 1]) + 1
                i += 2
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out[:size])


def chefe_da_tabela(ocupacao: int) -> tuple[str, int, str, list[str]]:
    """(espécie, nível, item, golpes) do chefe da ocupação em sFamiliaChefes."""
    text = TIMES_H.read_text(encoding="utf-8")
    text = text[text.index("sFamiliaChefes["):]
    sp, lv, item, moves = re.findall(r"MEMBRO\((\w+),\s*(\d+),\s*(\w+),\s*([\w ,]+)\)", text)[ocupacao - 1]
    return sp, int(lv), item, [m.strip() for m in moves.split(",")]


def times_table(name: str) -> list[list[tuple[str, int, str, list[str]]]]:
    """[ocupação][membro] = (espécie, nível, item, golpes) da tabela `name` de familia_sombra_times.h."""
    text = TIMES_H.read_text(encoding="utf-8")
    body = text[text.index(f"{name}["):]
    body = body[body.index("{") + 1:]
    out, depth, start = [], 0, 0
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
            if depth == 1:
                start = i
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append([(sp, int(lv), item, [m.strip() for m in moves.split(",")]) for sp, lv, item, moves in
                            re.findall(r"MEMBRO\((\w+),\s*(\d+),\s*(\w+),\s*([\w ,]+)\)", body[start:i])])
            elif depth < 0:
                return out
    raise AssertionError(name)


class FamiliaScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.driver: BattleDriver | None = None
        self.moves = header_defines(REPO_ROOT, "moves.h")
        self.moves_names = {v: k for k, v in self.moves.items() if k.startswith("MOVE_")}
        self.songs = header_defines(REPO_ROOT, "songs.h")
        self.nav = Navigator(self.ctl)
        self.gfx = header_defines(REPO_ROOT, "event_objects.h")

    # --- leitura --------------------------------------------------------------------
    def _sym(self, name: str) -> int:
        return self.game.syms.addr(name)

    def _rom_text(self, symbol: str) -> str:
        return self.game.charmap.decode(self.emu.read(self._sym(symbol), STRING_BYTES).split(b"\xff")[0])

    def _battle_text(self) -> str:
        return self._rom_text("gDisplayedStringBattle")

    def _sprite_callback(self, sprite_id: int) -> str:
        ptr = self.emu.read_u32(self._sym("gSprites") + sprite_id * SPRITE_SIZE + SPRITE_CALLBACK)
        return self.game.syms.name_at(ptr & ~1) or hex(ptr)

    def _battler_sprite(self, battler: int) -> tuple[str, int]:
        """(callback, data[2]) do sprite do batalhador: no Pokémon, data[2] = espécie."""
        sprite_id = self.emu.read_u8(self._sym("gBattlerSpriteIds") + battler)
        data2 = self.emu.read_u16(self._sym("gSprites") + sprite_id * SPRITE_SIZE + SPRITE_DATA + 4)
        return self._sprite_callback(sprite_id), data2

    def _sliding_trainers(self) -> int:
        base = self._sym("gSprites")
        return sum(1 for i in range(MAX_SPRITES)
                   if self.emu.read_u16(base + i * SPRITE_SIZE + SPRITE_IN_USE) & 1
                   and self._sprite_callback(i) == TRAINER_SLIDE)

    def _bgm_header(self) -> int:
        return self.emu.read_u32(self._sym("gMPlayInfo_BGM"))

    def _bgm_is(self, song: str) -> bool:
        header = self.emu.read_u32(self._sym("gMPlayInfo_BGM"))
        number = self.songs[song]
        return header == self.emu.read_u32(self._sym("gSongTable") + number * SONG_SIZE)

    def _sp(self, name: str) -> int:
        return self.consts.species(f"SPECIES_{name}")

    def _trainer(self, name: str) -> int:
        return self.consts._eval(name)

    # --- preparo --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self.driver = BattleDriver(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="familia_continue")
        self.box.conq_silencio(True)
        for slot, (species, level) in enumerate(TEAM):
            self.box.set_party_mon(slot, self.consts.species(species), level)
        self.box.party_size(len(TEAM))
        self.box.familia_set(1, ESTADO_ATIVA)
        self.ctl.checkpoint("familia_base")
        return f"CONTINUAR; time {TEAM}; ocupação 1 ATIVA; savestate familia_base"

    def _restore(self, name: str) -> None:
        self.ctl.restore(name)
        self.emu.frames(12)

    def _wait_intro(self, symbol: str, battlers: tuple[int, ...]) -> list[str]:
        """Espera a fala de abertura `symbol` na caixa e confere, nesse instante, o sprite de cada batalhador."""
        want = self._rom_text(symbol)
        self.driver.wait_battle_start()
        self.ctl.wait_until(lambda: self._battle_text() == want, INTRO_TIMEOUT, f"abertura {symbol}")
        seen = []
        for battler in battlers:
            callback, data2 = self._battler_sprite(battler)
            species = self.driver.battler_species_level(battler)[0]
            assert callback in WILD_MON_CALLBACKS and data2 == species, \
                f"batalhador {battler}: sprite com callback {callback}, data[2] {data2} (espécie {species})"
            seen.append(f"{battler}: {self.consts.species_name(species)} ({callback})")
        assert self._sliding_trainers() == 0, "sprite de treinador entrando na tela"
        return seen

    # --- casos ----------------------------------------------------------------------
    def _capanga(self) -> str:
        self._restore("familia_base")
        self.box.start_trainer_battle(self._trainer("TRAINER_FAMILIA_CAPANGA_1"))
        seen = self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        self.emu.frames(30)
        shot = self._shot("familia_capanga_batalha")
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        self.ctl.checkpoint("familia_capanga")
        return f"abertura = gText_FamiliaCapangaQuerLutar; oponente {seen}; sem treinador; tela {shot}"

    def _ball(self, checkpoint: str = "familia_capanga") -> str:
        self._restore(checkpoint)
        ball = self.consts.item("ITEM_POKE_BALL")
        assert self.box.call(CMD_GIVE_ITEM, ball, EXTRA_BALLS) == 1
        before = self.game.bag_quantity(ball)
        d = self.driver
        d._open_bag_on_item(ball)
        d.bag.use_selected()
        texts = set()
        result = d._advance_until_menu_or_end("bola no capanga", INTRO_TIMEOUT,
                                              on_step=lambda: texts.add(self._battle_text()))
        after = self.game.bag_quantity(ball)
        dodge = [t for t in texts if DODGE_TEXT in t]
        assert dodge, f"sem o texto do desvio; vi {sorted(texts)}"
        assert dodge[0] == self._rom_text("gText_FamiliaDesviaBola"), dodge[0]
        assert result == "menu" and self.game.in_battle(), f"a batalha não seguiu: {result}"
        assert after == before >= EXTRA_BALLS, f"Poké Bolas: {before} antes, {after} depois"
        species = self.consts.species_name(self.driver.battler_species_level(1)[0])
        return f"desvio: {dodge[0]!r}; Poké Bolas {before} → {after}; batalha segue contra {species}"

    def _win(self) -> str:
        """A vitória sem humano: 'Você derrotou Capanga da Família!', a fala de derrota, nenhum prêmio em dinheiro
        e a flag do treinador ligada (o capanga some do mapa até a próxima ocupação)."""
        self._restore("familia_base")
        self.box.set_party_move(0, 0, self.moves["MOVE_SHADOW_BALL"])   # Fantasma 2x no Misdreavus
        money = self.game.money()
        self.box.start_trainer_battle(self._trainer("TRAINER_FAMILIA_CAPANGA_1"))
        texts = set()
        result = self.driver.fight_to_end(on_step=lambda: texts.add(self._battle_text()))
        assert result == "win", f"resultado {result}; textos {sorted(texts)}"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        won = [t for t in texts if t.startswith("Você derrotou")]
        assert won and "Capanga da Família!" in won[0], f"sem a frase da vitória: {sorted(texts)}"
        prize = [t for t in texts if "pela vitória" in t]
        assert not prize and self.game.money() == money, f"prêmio: {prize}, dinheiro {money} → {self.game.money()}"
        flag = 0x500 + self._trainer("TRAINER_FAMILIA_CAPANGA_1")       # TRAINER_FLAGS_START + id
        assert self.game.flag(flag), "flag do capanga 1 desligada depois da vitória"
        return f"{won[0]!r}; dinheiro {money} → {self.game.money()}; flag do treinador {flag:#x} ligada"

    def _item_move(self, move: str, held: str | None, start=None) -> str:
        """Um turno de `move` (no golpe 0) do Mewtwo segurando `held` contra o capanga 1 (Misdreavus com Talismã
        Fantasma) ou contra a batalha que `start` começa: o item não muda de dono, nem na batalha nem no time."""
        self._restore("familia_base")
        held_id = self.consts.item(f"ITEM_{held}") if held else 0
        self.box.set_party_mon(0, self._sp("MEWTWO"), PLAYER_LEVEL, held_id)
        self.box.set_party_move(0, 0, self.moves[f"MOVE_{move}"])
        if start is None:
            self.box.start_trainer_battle(self._trainer("TRAINER_FAMILIA_CAPANGA_1"))
        else:
            start()
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        foe_item = self.game.enemy_party()[0].held_item
        assert start is not None or foe_item == self.consts.item("ITEM_SPELL_TAG"), foe_item
        assert foe_item and self.emu.read_u16(self._sym("gBattleMons") + BATTLE_MON_SIZE + BATTLE_MON_ITEM) == foe_item
        result = self.driver.fight_turn(INTRO_TIMEOUT)
        mine = self.emu.read_u16(self._sym("gBattleMons") + BATTLE_MON_ITEM)
        # o time lido com o checksum certo (a leitura pode pegar o Pokémon no meio de um GetMonData/SetMonData)
        raw = lambda: self.emu.read(self._sym("gPlayerParty"), POKEMON_SIZE)
        self.ctl.wait_until(lambda: mon_checksum_ok(raw()), 10, "time com checksum certo")
        party_item = self.game.party()[0].held_item
        assert (mine, party_item) == (held_id, held_id), \
            f"{move}: item do Mewtwo {mine} (batalha) / {party_item} (time), esperava {held_id}"
        detail = f"{move}: Mewtwo continua com {held or 'nada'}"
        if result == "menu":
            foe = self.emu.read_u16(self._sym("gBattleMons") + BATTLE_MON_SIZE + BATTLE_MON_ITEM)
            assert foe == foe_item, f"{move}: o capanga ficou com {foe}, esperava o item dele ({foe_item})"
            detail += f"; o capanga continua com o item {foe_item}"
        return detail

    def _thief(self) -> str:
        return self._item_move("THIEF", None) + " | " + self._item_move("TRICK", "LEFTOVERS")

    def _party_matches(self, mon, expected: tuple[str, int, str, list[str]], level: int | None = None) -> str:
        sp, lv, item, moves = expected
        got = (mon.species, mon.level, mon.held_item, mon.moves)
        want = (self._sp(sp), lv if level is None else level, self.consts.item(f"ITEM_{item}"),
                [self.moves[f"MOVE_{m}"] for m in moves])
        assert got == want, f"{sp}: {got}, esperava {want}"
        assert not mon.is_shiny, f"{sp} shiny"
        return f"{sp} nv {want[1]}"

    def _teams(self) -> str:
        self._restore("familia_base")
        capangas, gemeos, plantel = (times_table(t) for t in ("sFamiliaCapangas", "sFamiliaGemeos",
                                                               "sFamiliaPlantel"))
        seen = []
        for ocupacao in (1, 2):
            self.box.familia_set(ocupacao, ESTADO_ATIVA)
            extra = (ocupacao - 1) * 6
            size, _tier, double = self.box.build_trainer_party(self._trainer("TRAINER_FAMILIA_CAPANGA_1"), False)
            assert (size, double) == (1, False), (ocupacao, size, double)
            capanga = self._party_matches(self.game.enemy_party()[0], capangas[ocupacao - 1][0])
            size, _tier, double = self.box.build_trainer_party(self._trainer("TRAINER_FAMILIA_GEMEOS"), False)
            mons = self.game.enemy_party()
            assert (size, double, len(mons)) == (2, True, 2), (ocupacao, size, double, len(mons))
            twins = [self._party_matches(m, e) for m, e in zip(mons, gemeos[ocupacao - 1])]
            pedagio = []
            for n, level in (("1", 56 + extra), ("2", 58 + extra)):
                size, _tier, _double = self.box.build_trainer_party(self._trainer(f"TRAINER_FAMILIA_PEDAGIO_{n}"), False)
                mon = self.game.enemy_party()[0]
                match = [e for e in plantel[ocupacao - 1] if self._sp(e[0]) == mon.species]
                assert size == 1 and match, f"pedágio {n}: espécie {mon.species} fora do plantel da ocupação {ocupacao}"
                pedagio.append(self._party_matches(mon, match[0], level))
            assert pedagio[0].split()[0] != pedagio[1].split()[0], f"pedágio com a mesma espécie: {pedagio}"
            seen.append(f"ocupação {ocupacao}: capanga 1 {capanga}; gêmeos {twins}; pedágio {pedagio}")
        self.box.familia_set(1, ESTADO_ATIVA)
        return "; ".join(seen)

    # --- Task 4: andares 4-5 e o chefe ----------------------------------------------------------
    def _species_palette(self, species: int, shiny: bool) -> list[int]:
        """As 16 cores (GBA) da paleta da espécie, descompactadas da ROM (gMonPaletteTable / gMonShinyPaletteTable)."""
        table = self._sym("gMonShinyPaletteTable" if shiny else "gMonPaletteTable")
        ptr = self.emu.read_u32(table + species * PALETTE_ENTRY)
        raw = lz77(self.emu.read(ptr, 64))
        return [int.from_bytes(raw[i:i + 2], "little") for i in range(0, 32, 2)]

    def _battler_palette(self, battler: int) -> list[int]:
        base = self._sym("gPlttBufferUnfaded") + (OBJ_PLTT + 16 * battler) * 2
        return [self.emu.read_u16(base + 2 * i) for i in range(16)]

    def _encontro(self) -> str:
        self._restore("familia_base")
        plantel = times_table("sFamiliaPlantel")[0]
        species, level = self.box.familia_wild()
        member = [m for m in plantel if self._sp(m[0]) == species]
        assert member, f"espécie {species} fora do plantel da ocupação 1"
        assert 54 <= level <= 58, f"nível {level} fora de 54-58"
        seen = self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA and not flags & (BATTLE_TYPE_TRAINER | BATTLE_TYPE_FAMILIA_CHEFE), \
            f"gBattleTypeFlags {flags:#x}"
        detail = self._party_matches(self.game.enemy_party()[0], member[0], level)
        assert self._bgm_is("MUS_VS_TRAINER"), "a música não é a de treinador"
        normal = self._species_palette(species, False)
        want = [normal[0]] + [_noir_tool().noir_gba(c) for c in normal[1:]]
        got = self._battler_palette(1)
        assert got == want, f"paleta do oponente {[hex(c) for c in got]}, esperava o filme {[hex(c) for c in want]}"
        self.emu.frames(30)
        shot = self._shot("familia_filme_batalha")
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        self.ctl.checkpoint("familia_selvagem")
        return f"{detail} com item e golpes do plantel; {seen}; MUS_VS_TRAINER; paleta = noir(normal); tela {shot}"

    def _wild_ball(self) -> str:
        return self._ball("familia_selvagem")

    def _wild_thief(self) -> str:
        start = self.box.familia_wild
        return self._item_move("THIEF", None, start) + " | " + self._item_move("TRICK", "LEFTOVERS", start)

    def _chefe(self) -> str:
        self._restore("familia_base")
        expected = chefe_da_tabela(1)
        gengar = self._sp(expected[0])
        self.box.familia_chefe()
        seen = self._wait_intro("gText_FamiliaChefeDom", (1,))     # "GENGAR, O DOM, quer acertar as contas!"
        assert self.driver.battler_species_level(1)[0] == gengar, seen
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA_CHEFE and flags & BATTLE_TYPE_LEGENDARY, f"gBattleTypeFlags {flags:#x}"
        assert not flags & (BATTLE_TYPE_FAMILIA | BATTLE_TYPE_TRAINER), f"gBattleTypeFlags {flags:#x}"
        assert self.emu.read_u16(self._sym("gTrainerBattleOpponent_A")) == 0, "gTrainerBattleOpponent_A não zerado"
        mon = self.game.enemy_party()[0]
        assert mon.is_shiny, f"chefe não shiny: pid {mon.personality:#x}, OT {mon.ot_id:#x}"
        assert mon.ot_id == self.game.party()[0].ot_id, "o OT do chefe não é o jogador"
        sp, lv, item, moves = expected
        got = (mon.species, mon.level, mon.held_item, mon.moves)
        want = (gengar, lv, self.consts.item(f"ITEM_{item}"), [self.moves[f"MOVE_{m}"] for m in moves])
        assert got == want, f"{sp}: {got}, esperava {want}"
        assert self._bgm_is("MUS_VS_LEGEND"), "a música não é a de lendário"
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        shiny = self._species_palette(gengar, True)
        got = self._battler_palette(1)
        assert got == shiny, f"paleta do chefe {[hex(c) for c in got]}, esperava a shiny {[hex(c) for c in shiny]}"
        shot = self._shot("familia_chefe_batalha")
        self.ctl.checkpoint("familia_chefe")
        return (f"{sp} nv {lv} shiny, {item}, {moves}; abertura {self._rom_text('gText_FamiliaChefeDom')!r}; "
                f"lendária + FAMILIA_CHEFE; MUS_VS_LEGEND; paleta shiny sem filme; tela {shot}")

    def _passos(self) -> str:
        """O caminho de cada passo (TryStandardWildEncounter) com o mapa valendo como andar escuro e SEM entrada em
        wild_encounters.json para ele: com chefe ativo sai um capanga do plantel; sem chefe, nada em 400 passos."""
        self._restore("familia_base")
        plantel = times_table("sFamiliaPlantel")[0]
        steps, started = self.box.familia_passos(PASSOS)
        assert started, f"nenhum encontro em {PASSOS} passos com chefe ativo"
        self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA and not flags & BATTLE_TYPE_TRAINER, f"gBattleTypeFlags {flags:#x}"
        species, level = self.driver.battler_species_level(1)
        assert any(self._sp(m[0]) == species for m in plantel) and 54 <= level <= 58, (species, level)
        ativo = f"chefe ativo: encontro no passo {steps} ({self.consts.species_name(species)} nv {level})"
        self._restore("familia_base")
        self.box.familia_set(1, ESTADO_SEM_CHEFE)
        steps, started = self.box.familia_passos(PASSOS)
        self.emu.frames(30)
        assert not started and steps == PASSOS and not self.game.in_battle(), (steps, started)
        self.box.familia_set(1, ESTADO_ATIVA)
        return f"{ativo}; sem chefe: {PASSOS} passos sem encontro"

    def _chefe_ball(self) -> str:
        self._restore("familia_chefe")
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1
        before = self.game.bag_quantity(master)
        caught = self.driver.throw_ball(master)
        after = self.game.bag_quantity(master)
        assert caught, "a Master Ball não capturou o chefe"
        assert after == before - 1, f"Master Ball: {before} antes, {after} depois (não foi gasta)"
        return f"capturado; Master Ball {before} -> {after}"

    def _chefe_ia(self) -> str:
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("GOLEM"), 100)
        self.box.set_party_move(0, 0, self.moves["MOVE_HARDEN"])
        self.box.familia_chefe()
        thunderbolt = self.moves["MOVE_THUNDERBOLT"]
        dream, hypnosis = self.moves["MOVE_DREAM_EATER"], self.moves["MOVE_HYPNOSIS"]
        chosen = []
        for turn in range(1, AI_TURNS + 1):
            self.driver.wait_action_menu(INTRO_TIMEOUT)
            asleep = bool(self.emu.read_u32(self._sym("gBattleMons") + BATTLE_MON_STATUS1) & STATUS1_SLEEP)
            self.emu.frames(10)
            move, result = self._turn_reading_foe_move()
            name = self.moves_names.get(move, str(move))
            chosen.append(name + (" (Golem dormindo)" if asleep else ""))
            assert move != thunderbolt, f"turno {turn}: Raio contra o Golem (imune)"
            bad = hypnosis if asleep else dream
            assert move != bad, f"turno {turn}: {name} com o Golem {'dormindo' if asleep else 'acordado'}"
            if turn == 1:
                ai = self.emu.read_u32(self.emu.read_u32(self._sym("gBattleResources")) + AI_RESOURCES)
                bits = self.emu.read_u8(ai + AI_LOGIC_ID)
                assert bits == CHEFE_AI_BITS, f"IA do chefe com {bits} bits de flags, esperava {CHEFE_AI_BITS}"
            assert result == "menu", f"turno {turn}: a batalha acabou ({result})"
        return f"IA de chefe (aiLogicId {CHEFE_AI_BITS}); golpes {chosen}"

    def _turn_reading_foe_move(self) -> tuple[int, str]:
        """Um turno de LUTAR (1º golpe com PP), como BattleDriver.fight_turn, lendo gChosenMoveByBattler[1] logo que o
        jogador escolhe (o motor zera a escolha no fim do turno): (golpe do oponente, 'menu' ou 'end')."""
        d = self.driver
        d._choose_action(ACTION_FIGHT)
        in_moves = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        d._choose_first_move_with_pp()
        self.ctl.wait_until(lambda: not in_moves(), 60, "saída do menu de golpes")
        chosen = self._sym("gChosenMoveByBattler") + 2
        self.ctl.wait_until(lambda: self.emu.read_u16(chosen) != 0, MENU_TIMEOUT, "escolha do chefe")
        move = self.emu.read_u16(chosen)
        return move, d._advance_until_menu_or_end("fim do turno", INTRO_TIMEOUT)

    def _twins(self) -> str:
        self._restore("familia_base")
        self.box.familia_gemeos()
        seen = self._wait_intro("gText_FamiliaGemeosQueremLutar", (1, 3))
        flags = self.driver.battle_type_flags()
        assert flags & 1, f"não é dupla: gBattleTypeFlags {flags:#x}"
        for battler in (1, 3):
            species, level = self.driver.battler_species_level(battler)
            assert (species, level) == (self._sp("MACHAMP"), 60), f"batalhador {battler}: {(species, level)}"
        assert self._bgm_is("MUS_VS_GYM_LEADER"), "a música não é a de líder de ginásio"
        self.emu.frames(30)
        shot = self._shot("familia_gemeos_batalha")
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        return f"dupla: {seen}, 2 Machamp nv 60; MUS_VS_GYM_LEADER; tela {shot}"

    # --- Task 5: o prédio ------------------------------------------------------------------------
    def _flag(self, name: str) -> int:
        return self.consts.flag(name)

    def _trainer_flag(self, name: str) -> int:
        return TRAINER_FLAGS_START + self._trainer(name)

    def _message(self) -> str:
        """A última caixa de mensagem do campo (gStringVar4)."""
        return self.game.charmap.decode(self.emu.read(self._sym("gStringVar4"), STRING_BYTES).split(b"\xff")[0])

    def _fade_active(self) -> bool:
        return bool(self.emu.read_u8(self._sym("gPaletteFade") + PALETTE_FADE_ACTIVE) & 0x80)

    def _settle(self, what: str) -> None:
        self.ctl.wait_overworld_idle(900)
        self.ctl.wait_until(lambda: not self._fade_active(), 300, f"fim do fade: {what}")
        self.emu.frames(4)

    def _warp(self, map_name: str, xy: tuple[int, int]) -> None:
        """Atalho WARP (fade e carga do mapa como numa porta: o on_transition do destino roda)."""
        group, num = self.consts.map(map_name)
        self._settle(f"antes do warp para {map_name}")
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_name}")
        self._settle(f"warp para {map_name}")

    def _at(self, map_name: str) -> bool:
        return self.game.location() == self.consts.map(map_name)

    def _half_day(self) -> int:
        """Meio-dia do relógio da hack (FamiliaSombra_MeiosDiasAgora)."""
        frames = self.emu.read_u32(self.emu.read_u32(self._sym("gSaveBlock2Ptr")) + SB2_GAME_CLOCK)
        return (frames // GAME_CLOCK_FRAMES_PER_MINUTE + GAME_CLOCK_START_MINUTE) // HALF_DAY_MINUTES

    def _set_half_day(self, half: int) -> None:
        self.box.set_clock(half // 2, (half % 2) * HALF_DAY_MINUTES)
        assert self._half_day() == half, (self._half_day(), half)

    def _repovoaveis(self) -> dict[str, bool]:
        """O que FamiliaSombra_Repovoar desmarca: 1 item, 1 capanga e os gêmeos (amostra) e a flag dos gêmeos."""
        return {
            "item 1_1": self.game.flag(self._flag("FLAG_FAMILIA_ITEM_1_1")),
            "capanga 1": self.game.flag(self._trainer_flag("TRAINER_FAMILIA_CAPANGA_1")),
            "treinador gêmeos": self.game.flag(self._trainer_flag("TRAINER_FAMILIA_GEMEOS")),
            "gêmeos vencidos": self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")),
        }

    def _mark_repovoaveis(self) -> None:
        for flag in (self._flag("FLAG_FAMILIA_ITEM_1_1"), self._trainer_flag("TRAINER_FAMILIA_CAPANGA_1"),
                     self._trainer_flag("TRAINER_FAMILIA_GEMEOS"), self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")):
            assert self.box.set_flag(flag, True)

    def _active_objects(self) -> list[int]:
        """localId dos objetos ativos do mapa (sem o jogador e o seguidor), em ordem."""
        base = self._sym("gObjectEvents")
        ids = []
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            local = self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID)
            if self.emu.read_u8(addr) & 1 and local not in (LOCALID_PLAYER, LOCALID_FOLLOWER):
                ids.append(local)
        return sorted(ids)

    def _waiting(self) -> bool:
        """Página inteira na tela, esperando botão (ou impressão acabada)."""
        return not self.game.text_printer_active() or self.game.text_printer_state(0) in BUTTON_WAIT_STATES

    def _sprites_with(self, callback: str) -> int:
        base = self._sym("gSprites")
        return sum(1 for i in range(MAX_SPRITES)
                   if self.emu.read_u16(base + i * SPRITE_SIZE + SPRITE_IN_USE) & 1 and self._sprite_callback(i) == callback)

    def _object_gfx(self, local: int) -> int:
        base = self._sym("gObjectEvents")
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            if self.emu.read_u8(addr) & 1 and self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID) == local:
                return self.emu.read_u8(addr + OBJECT_EVENT_GFX)
        raise AssertionError(f"objeto {local} não está no mapa")

    def _scene(self, until, what: str, timeout: int = 4000, shot: tuple[str, str] | None = None) -> list[str]:
        """Aperta A até `until()`; devolve as mensagens do campo vistas (gStringVar4). `shot` = (trecho, tela):
        foto quando o trecho está na caixa, já impresso e esperando o botão."""
        seen, spent, taken = [], 0, False
        while not until():
            if spent > timeout:
                raise self.ctl.timeout_error(f"{what}; mensagens {seen}")
            msg = self._message()
            if self.ctl.script_active() and msg and (not seen or seen[-1] != msg):
                seen.append(msg)
            if shot and not taken and shot[0] in msg and self.ctl.script_active():
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, f"texto {shot[0]!r}")
                self._shot(shot[1])
                taken = True
            if self.ctl.script_active() and not self.game.in_battle():
                self.emu.press(KEY_A, hold=2, release=8)
                spent += 10
            else:
                self.emu.frames(4)
                spent += 4
        return seen

    def _sair_do_predio(self) -> None:
        """Pelo tapete do 1º andar até a frente da porta na Rota 23 (o atalho WARP não chega a y >= 128)."""
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self.nav.go_through_warp("down")
        self._settle("saída do prédio")
        if self.game.player_xy() == PORTA:      # porta trancada: sai sem a animação e fica no tile da porta
            self.nav.step("down")
        assert self._at("MAP_ROUTE23") and self.game.player_xy() == PORTA_FRENTE, \
            (self.game.location(), self.game.player_xy())

    def _porta(self) -> str:
        """Sem a 8ª insígnia a porta do prédio está trancada (o metatile vira o da porta sem comportamento e a placa
        fala do charuto); com ela, a 1ª entrada liga a ocupação 1 e a porta leva ao 1º andar."""
        self._restore("familia_base")
        badge = self._flag("FLAG_BADGE08_GET")
        self.box.set_flag(badge, False)
        self.box.familia_set(0, ESTADO_FECHADO)
        self._sair_do_predio()
        self.emu.keys(KEY_UP)
        self.emu.frames(60)
        self.emu.keys(0)
        self.emu.frames(10)
        assert self._at("MAP_ROUTE23") and self.game.player_xy() == PORTA_FRENTE, \
            f"a porta trancada deixou passar: {self.game.location()} {self.game.player_xy()}"
        self.ctl.press_until(KEY_A, self.ctl.script_active, "placa da porta", tries=5)
        self.ctl.wait_until(self._waiting, 600, "texto da porta")
        msg = self._message()
        assert msg == self._rom_text("Route23_Text_PortaFamiliaTrancada"), msg
        self._shot("familia_porta_trancada")
        self._scene(self.ctl.overworld_idle, "fim da placa")
        assert self.box.familia_estado()[:2] == (0, ESTADO_FECHADO)
        self.box.set_flag(badge, True)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (1, ESTADO_ATIVA), self.box.familia_estado()
        self._sair_do_predio()
        self._shot("familia_rota23_predio")
        self.nav.go_through_warp("up")
        assert self._at("MAP_ROUTE23_UNUSED_HOUSE"), self.game.location()
        return f"trancada: {msg!r}; com a 8ª insígnia: ocupação 1 ATIVA e a porta leva ao 1º andar"

    def _ciclo(self) -> str:
        """O ciclo pelo relógio: save antigo com a 8ª insígnia entra = ocupação 1; queda + 6 meios-dias = ainda sem
        chefe; +7 = ocupação 2 com itens e treinadores de volta (uma vez só). As ocupações 3 e 4 e o fim da Família ficam
        em familia/ciclo_ate_o_fim (POK-54)."""
        self._restore("familia_base")
        log = []
        self.box.set_flag(self._flag("FLAG_BADGE08_GET"), True)
        self.box.familia_set(0, ESTADO_FECHADO)
        self._mark_repovoaveis()
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (1, ESTADO_ATIVA), self.box.familia_estado()
        assert not any(self._repovoaveis().values()), self._repovoaveis()
        log.append("save antigo com a insígnia: ocupação 1 ATIVA, tudo no lugar")
        queda = 20
        self._set_half_day(queda)
        self.box.familia_set(1, ESTADO_SEM_CHEFE, queda)
        self._mark_repovoaveis()
        self._set_half_day(queda + 6)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado() == (1, ESTADO_SEM_CHEFE, queda), self.box.familia_estado()
        log.append("queda + 6 meios-dias: sem chefe")
        self._set_half_day(queda + 7)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (2, ESTADO_ATIVA), self.box.familia_estado()
        assert not any(self._repovoaveis().values()), f"não repovoou: {self._repovoaveis()}"
        log.append("+7: ocupação 2 ATIVA, itens e treinadores de volta")
        self._mark_repovoaveis()           # o jogador vence o capanga e pega o item da ocupação 2
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (2, ESTADO_ATIVA)
        assert all(self._repovoaveis().values()), f"repovoou de novo: {self._repovoaveis()}"
        log.append("entrar de novo não repovoa outra vez")
        return "; ".join(log)

    # --- o pedágio (Task 6) -----------------------------------------------------------
    def _set_money(self, amount: int) -> None:
        """Dinheiro do jogador (u32 XOR encryptionKey): escrita na RAM, só na ROM de teste."""
        self.emu.write(self.game._sb1() + SB1_MONEY, (amount ^ self.game._key()).to_bytes(4, "little"))

    def _pedagio_prep(self) -> None:
        """Uma vez só: monta os dois pontos de partida (norte e sul do corredor) como savestates."""
        if getattr(self, "_pedagio_pronto", False):
            return
        self._restore("familia_base")
        self.box.set_flag(self._flag("FLAG_BADGE08_GET"), True)
        self.box.set_flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"), False)
        self.box.call(CMD_SET_VAR, VAR_MAP_SCENE_ROUTE23, 0)      # sem a cena dos guardas das insígnias
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        self.box.set_party_move(0, 0, self.moves["MOVE_SHADOW_BALL"])
        self.box.familia_set(1, ESTADO_ATIVA)
        self._set_money(5000)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.nav.walk_to(*PEDAGIO_NORTE), f"não chegou ao lado norte: {self.game.player_xy()}"
        self.ctl.checkpoint("pedagio_norte")
        self._sair_do_predio()
        assert self.nav.walk_to(*PEDAGIO_SUL), f"não chegou ao lado sul: {self.game.player_xy()}"
        self.ctl.checkpoint("pedagio_sul")
        self._pedagio_pronto = True

    def _pedagio_cena(self, pagar: bool = False, forca: bool = False, shot: str | None = None) -> dict:
        """Roda a cena do pedágio até o campo ficar livre: A avança as falas; a pergunta sim/não recebe A (pagar) ou B;
        o menu recebe A em "Voltar depois" ou BAIXO + A em "Passar à força"; cada batalha é lutada até o fim."""
        info = {"msgs": [], "yesno": False, "menu": False, "lutas": [], "especies": []}
        spent, handled = 0, False
        while not (self.ctl.overworld_idle() and info["msgs"]):
            if spent > 30000:
                raise self.ctl.timeout_error(f"cena do pedágio; mensagens {info['msgs']}, lutas {info['lutas']}")
            if self.game.in_battle():
                self.driver.wait_battle_start()
                info["lutas"].append(self.emu.read_u16(self._sym("gTrainerBattleOpponent_A")))
                info["especies"].append(self.driver.battler_species_level(1)[0])
                result = self.driver.fight_to_end()
                assert result == "win", f"perdeu para o pedágio: {result}"
                self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
                spent += 100
                continue
            tasks = self._tasks()
            msg = self._message()
            if self.ctl.script_active() and msg and (not info["msgs"] or info["msgs"][-1] != msg):
                info["msgs"].append(msg)
            if YESNO_TASK in tasks:
                info["yesno"] = True
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, "pergunta de pagar")
                if shot and not handled:
                    info["shot"] = self._shot(shot)
                handled = True
                self.emu.press(KEY_A if pagar else KEY_B, hold=2, release=8)
                spent += 10
            elif MULTICHOICE_TASK in tasks:
                info["menu"] = True
                self.emu.frames(10)
                if forca:
                    self.emu.press(KEY_DOWN, hold=2, release=8)
                self.emu.press(KEY_A, hold=2, release=20)
                spent += 40
            elif self.ctl.script_active():
                self.emu.press(KEY_A, hold=2, release=8)
                spent += 10
            else:
                self.emu.frames(4)
                spent += 4
        self.emu.frames(10)
        return info

    def _pedagio_passo(self, direction: str) -> None:
        """Um passo para o gatilho: o script começa um quadro depois do passo (o jogador já pode estar parado)."""
        assert self.nav.step(direction) == 1
        self.ctl.wait_until(self.ctl.script_active, 60, f"o gatilho do pedágio ({direction})")

    def _pedagio_gatilho(self, checkpoint: str = "pedagio_sul") -> None:
        """Do checkpoint, um passo para o gatilho (sul: y 147; norte: y 145); o script do pedágio toma os controles."""
        self._pedagio_prep()
        self._restore(checkpoint)
        self._pedagio_passo("down" if checkpoint == "pedagio_norte" else "up")

    def _pedagio_paga(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        assert self.game.money() == 5000 and not self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert LOCALID_COBRADOR in self._active_objects(), f"sem o cobrador: {self._active_objects()}"
        assert self._object_gfx(LOCALID_COBRADOR) == self.gfx["OBJ_EVENT_GFX_FAMILIA_PERSIAN"]
        assert self._object_xy(LOCALID_COBRADOR) == (14, 146), self._object_xy(LOCALID_COBRADOR)
        self._pedagio_gatilho()
        info = self._pedagio_cena(pagar=True, shot="familia_pedagio")
        assert info["yesno"] and not info["menu"] and not info["lutas"], info
        assert self._rom_text("Route23_Text_PedagioPago") in info["msgs"], info["msgs"]
        assert self.game.money() == 5000 - PEDAGIO, f"dinheiro {self.game.money()}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        # passa pela esquerda do Persian e anda sem ser cobrado
        assert self.game.player_xy() == (14, 147), self.game.player_xy()
        assert self.nav.step("left") == 1 and self.nav.step("up", 3) == 3 and self.nav.interrupted is None
        assert self.game.player_xy() == (13, 144), self.game.player_xy()
        # entra no prédio e sai: continua pago, e não cobra na volta
        assert self.nav.walk_to(*PORTA_FRENTE), f"não voltou à porta: {self.game.player_xy()}"
        self.nav.go_through_warp("up")
        assert self._at("MAP_ROUTE23_UNUSED_HOUSE") and self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        self.nav.go_through_warp("down")
        self._settle("saída do prédio")
        assert self._at("MAP_ROUTE23") and self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO")), \
            "o prédio zerou o pago"
        assert self.nav.walk_to(14, 148)
        self.nav.step("up")                     # o gatilho arma de novo a cada carga do mapa: o pago o deixa passar
        self.ctl.wait_overworld_idle()
        assert self.game.player_xy() == (14, 147) and self.game.money() == 5000 - PEDAGIO
        assert YESNO_TASK not in self._tasks() and self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self.nav.step("left") == 1 and self.nav.step("up", 3) == 3 and self.nav.interrupted is None
        return (f"cobrador no (14, 146); pagou: ¥5.000 → ¥{self.game.money()}, flag ligada; passou, entrou no "
                f"prédio, saiu e subiu sem ser cobrado; tela {info['shot']}")

    def _pedagio_sem_dinheiro(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        self._set_money(PEDAGIO - 1)
        self.ctl.checkpoint("pedagio_pobre")
        self._pedagio_gatilho("pedagio_pobre")
        info = self._pedagio_cena()
        assert not info["yesno"] and info["menu"] and not info["lutas"], info
        assert self._rom_text("Route23_Text_PedagioSemDinheiro") in info["msgs"], info["msgs"]
        assert self._rom_text("Route23_Text_PedagioVoltar") in info["msgs"], info["msgs"]
        assert self.game.money() == PEDAGIO - 1 and not self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self.game.player_xy() == PEDAGIO_SUL, f"não voltou um passo: {self.game.player_xy()}"
        # com dinheiro, recusando: a pergunta vem antes do mesmo menu e nada é cobrado
        self._pedagio_gatilho("pedagio_sul")
        info2 = self._pedagio_cena(pagar=False)
        assert info2["yesno"] and info2["menu"] and not info2["lutas"], info2
        assert self._rom_text("Route23_Text_PedagioRecusou") in info2["msgs"], info2["msgs"]
        assert self.game.money() == 5000 and not self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self.game.player_xy() == PEDAGIO_SUL
        return (f"sem dinheiro (¥{PEDAGIO - 1}): só o menu, voltou um passo, nada cobrado; "
                f"recusando com ¥5.000: pergunta + menu, voltou, ¥5.000 intactos")

    def _pedagio_forca(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        self._set_money(500)
        self.box.conq_reset(True)
        assert self._conq("familia_pedagio") == CONQ_PENDENTE
        self.ctl.checkpoint("pedagio_pobre")
        self._pedagio_gatilho("pedagio_pobre")
        info = self._pedagio_cena(forca=True)
        assert info["menu"] and not info["yesno"], info
        want = [self._trainer("TRAINER_FAMILIA_PEDAGIO_1"), self._trainer("TRAINER_FAMILIA_PEDAGIO_2")]
        assert info["lutas"] == want, f"lutas {info['lutas']}, esperava {want}"
        assert len(set(info["especies"])) == 2, f"as 2 lutas com a mesma espécie: {info['especies']}"
        assert self.game.money() == 500, f"prêmio ou cobrança: ¥{self.game.money()}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self._rom_text("Route23_Text_PedagioLivre") in info["msgs"], info["msgs"]
        assert self.nav.step("left") == 1 and self.nav.step("up", 3) == 3 and self.nav.interrupted is None
        nomes = [self.consts.species_name(sp) for sp in info["especies"]]
        assert self._conq("familia_pedagio") == CONQ_FEITA, "Pagar ou lutar não ficou feita"
        assert self._conq("familia_dom") == CONQ_PENDENTE
        return f"2 lutas seguidas ({nomes}), dinheiro intacto, passagem paga e livre; Pagar ou lutar feita"

    def _pedagio_volta(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_norte")
        pago = self._flag("FLAG_FAMILIA_PEDAGIO_PAGO")
        self.box.set_flag(pago, True)           # pagou na ida
        self._warp("MAP_VICTORY_ROAD_1F", VR_1F_LIVRE)
        assert not self.game.flag(pago), "a Victory Road 1F não zerou o pago"
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert not self.game.flag(pago)
        assert self.nav.walk_to(*PEDAGIO_NORTE), f"descida interrompida em {self.game.player_xy()}"
        # descendo: cobra no lado norte; recusar + voltar depois empurra um passo para o norte
        self._pedagio_passo("down")
        info = self._pedagio_cena(pagar=False)
        assert info["yesno"] and info["menu"], info
        assert self._rom_text("Route23_Text_PedagioCobra") in info["msgs"], info["msgs"]
        assert self.game.player_xy() == PEDAGIO_NORTE and self.game.money() == 5000 \
            and not self.game.flag(pago), (self.game.player_xy(), self.game.money())
        # de novo e pagando: passa pela direita e desce até o sul sem ser cobrado
        self._pedagio_passo("down")
        info = self._pedagio_cena(pagar=True)
        assert info["yesno"] and not info["menu"], info
        assert self.game.money() == 5000 - PEDAGIO and self.game.flag(pago)
        assert self.nav.step("right") == 1 and self.nav.step("down", 3) == 3 and self.nav.interrupted is None
        assert self.game.player_xy() == (15, 148), self.game.player_xy()
        return "pago na ida, a Victory Road 1F zera; descendo cobra no norte: voltar empurra ao norte, pagar libera"

    def _pedagio_sem_chefe(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        queda = 20
        self._set_half_day(queda)
        self.box.familia_set(1, ESTADO_SEM_CHEFE, queda)
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self.nav.go_through_warp("down")
        self._settle("saída do prédio")
        assert self._at("MAP_ROUTE23") and self.box.familia_estado() == (1, ESTADO_SEM_CHEFE, queda)
        assert LOCALID_COBRADOR not in self._active_objects(), f"cobrador sem chefe: {self._active_objects()}"
        assert self.nav.walk_to(*PEDAGIO_SUL)
        assert self.nav.step("up", 5) == 5 and self.nav.interrupted is None, "o pedágio disparou sem chefe"
        assert self.game.player_xy() == (14, 143) and not self.ctl.script_active()
        return "sem chefe: sem Persian, sem gatilho, o corredor livre (inclusive o tile do cobrador)"

    def _subida(self) -> str:
        """Da porta ao 6º andar pelas escadas de verdade (capangas já vencidos, Repelente com o Mewtwo nv 100 na
        frente): música, clima e escuro de cada andar; telas do 1º, do 4º (escuro e névoa) e da sala do Dom."""
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        self._sair_do_predio()
        self.nav.go_through_warp("up")
        self._settle("1º andar")
        shots = [self._shot("familia_andar_1")]
        for slot in range(1, 10):
            self.box.set_flag(self._trainer_flag(f"TRAINER_FAMILIA_CAPANGA_{slot}"), True)
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        seen = []
        for andar in range(1, 6):
            name = "MAP_ROUTE23_UNUSED_HOUSE" if andar == 1 else f"MAP_ROUTE23_FAMILIA_SOMBRA_{andar}F"
            assert self._at(name), (andar, self.game.location())
            song = "MUS_ROCKET_HIDEOUT" if andar <= 3 else "MUS_POKE_TOWER"
            assert self._bgm_is(song), f"{andar}º andar sem {song}"
            flash = self.emu.read_u8(self.emu.read_u32(self._sym("gSaveBlock1Ptr")) + SB1_FLASH_LEVEL)
            assert (flash > 0) == (andar in (4, 5)), f"{andar}º andar: flashLevel {flash}"
            fog = self._sprites_with(FOG_CALLBACK)
            assert (fog > 0) == (andar in (4, 5)), f"{andar}º andar: {fog} sprites de névoa"
            if andar == 4:
                shots.append(self._shot("familia_andar_4"))
            seen.append(f"{andar}º ({song}, escuro {flash}, névoa {fog})")
            assert self.nav.walk_to(*ANTES_DA_ESCADA), f"{andar}º andar: não chegou à escada"
            self.nav.go_through_warp("right")
            self._settle(f"{andar + 1}º andar")
        assert self._at("MAP_ROUTE23_FAMILIA_SOMBRA_6F"), self.game.location()
        self.emu.frames(30)
        shots.append(self._shot("familia_sala_do_dom"))
        objs = sorted(self._active_objects())
        assert objs == [1, 2, 3], f"sala do Dom: objetos {objs} (chefe e os 2 gêmeos)"
        gfx = [self._object_gfx(local) for local in objs]
        want = [self.gfx[f"OBJ_EVENT_GFX_FAMILIA_{n}"] for n in ("GENGAR_SHINY", "MACHAMP", "MACHAMP")]
        assert gfx == want, f"gráficos da sala {gfx}, esperava {want}"
        assert self._quadro() == "dom", f"quadro da ocupação 1: {self._quadro()}"
        self._sala_igual_ao_layout()
        return f"andares {seen}; 6º com o Gengar shiny, os 2 Machamp e o retrato do Dom; telas {shots}"

    def _capanga_ve(self) -> str:
        """O capanga 2 do 1º andar (visão 4, olhando para a esquerda) vê o jogador a 2 tiles, vem até ele e luta;
        vencido, some do mapa na hora (a flag do treinador é a flag do objeto)."""
        self._restore("familia_base")
        self.box.set_party_move(0, 0, self.moves["MOVE_THUNDERBOLT"])
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        assert 2 in self._active_objects(), self._active_objects()
        start = self._object_xy(2)
        for direction, n in VISTA_CAPANGA_2[0]:     # pela direita, longe da vista do capanga 1
            assert self.nav.step(direction, n) == n, (direction, n, self.game.player_xy())
        self.ctl.wait_until(self.ctl.script_active, 60, "o capanga vê o jogador")
        self._scene(self.game.in_battle, "o capanga vem lutar")
        moved = self._object_xy(2)
        trainer = self.emu.read_u16(self._sym("gTrainerBattleOpponent_A"))
        assert trainer == self._trainer("TRAINER_FAMILIA_CAPANGA_2"), trainer
        assert moved == VISTA_CAPANGA_2[1], f"o capanga não veio até o jogador: {start} -> {moved}"
        assert self.driver.fight_to_end() == "win", "perdeu para o capanga 2"
        self._scene(self.ctl.overworld_idle, "volta da batalha")
        assert 2 not in self._active_objects(), f"o capanga vencido continua no mapa: {self._active_objects()}"
        assert self.game.flag(self._trainer_flag("TRAINER_FAMILIA_CAPANGA_2"))
        return f"o capanga 2 andou de {start} para {moved}, lutou e sumiu depois da derrota"

    def _object_xy(self, local: int) -> tuple[int, int]:
        base = self._sym("gObjectEvents")
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            if self.emu.read_u8(addr) & 1 and self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID) == local:
                return (self.emu.read_u16(addr + OBJECT_EVENT_XY) - MAP_OFFSET,
                        self.emu.read_u16(addr + OBJECT_EVENT_XY + 2) - MAP_OFFSET)
        raise AssertionError(f"objeto {local} não está no mapa")

    def _to_scene(self, party: tuple[tuple[str, int], ...], gemeos_vencidos: bool, ocupacao: int = 1) -> None:
        """Na sala do chefe da `ocupacao`, um passo antes do gatilho (o tile da saída da escada), com o time `party`."""
        self._restore("familia_base")
        if ocupacao != 1:
            self.box.familia_set(ocupacao, ESTADO_ATIVA)
        for slot, (species, level) in enumerate(party):
            self.box.set_party_mon(slot, self._sp(species), level)
        self.box.party_size(len(party))
        self.box.set_flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS"), gemeos_vencidos)
        self.box.set_flag(self._trainer_flag("TRAINER_FAMILIA_GEMEOS"), gemeos_vencidos)
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_6F", SAIDA_ESCADA_6F)

    def _gatilho(self) -> None:
        """Um passo para baixo, da saída da escada para o gatilho da cena (4, 4), e a cena começa."""
        self.nav.step("down")
        self.ctl.wait_until(self.ctl.script_active, 60, "cena do 6º andar")

    def _gemeos_um(self) -> str:
        """Com 1 Pokémon só: o chefe fala, os gêmeos recusam a dupla ("Os gêmeos só lutam em dupla.") e nada começa;
        o jogador anda de novo e tudo fica como estava."""
        self._to_scene((("MEWTWO", 100),), False)
        self._gatilho()
        msgs = self._scene(self.ctl.overworld_idle, "recusa dos gêmeos")
        assert not self.game.in_battle(), "começou uma batalha com 1 Pokémon"
        want = self._rom_text("Route23_FamiliaSombra_6F_Text_SoEmDupla")
        assert want in msgs, f"sem a recusa; mensagens {msgs}"
        dom = self._rom_text("Route23_FamiliaSombra_6F_Text_Dom").split("\n")[0]
        assert any(m.startswith(dom) for m in msgs), f"sem a fala do Dom: {msgs}"
        assert not self.game.flag(self._trainer_flag("TRAINER_FAMILIA_GEMEOS"))
        assert not self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS"))
        assert self.box.familia_estado()[:2] == (1, ESTADO_ATIVA)
        assert self.nav.step("up") == 1, "o jogador ficou preso depois da recusa"
        return f"recusa {want!r}; sem batalha; gêmeos e chefe no lugar; o jogador anda"

    def _chefe_fuga(self) -> str:
        """Gêmeos já vencidos: a cena vai direto ao chefe. Fugindo, o chefe fica (objeto, estado ATIVA, sem queda nem
        rosa) e os gêmeos não voltam."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True)
        objs = sorted(self._active_objects())
        assert objs == [1], f"gêmeos vencidos voltaram: {objs}"
        self._gatilho()
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA_CHEFE and not flags & 1, f"gBattleTypeFlags {flags:#x}"
        assert self.driver.run_away(), "não fugiu do chefe"
        msgs = self._scene(self.ctl.overworld_idle, "volta da fuga")
        assert any(self._rom_text("Route23_FamiliaSombra_6F_Text_FugaDom") in m for m in msgs), msgs
        assert self.box.familia_estado() == (1, ESTADO_ATIVA, 0), self.box.familia_estado()
        assert sorted(self._active_objects()) == [1], self._active_objects()
        assert not self.game.flag(self._flag("FLAG_FAMILIA_ROSA_1"))
        assert self.game.bag_quantity(self.consts.item("ITEM_ROSA_VERMELHA")) == 0
        return "direto ao chefe (gêmeos vencidos); fugiu: chefe no lugar, ATIVA, sem rosa"

    def _rosa(self) -> str:
        """A cena inteira: o Dom fala, a dupla dos gêmeos (vencida), o Dom fala de novo, a luta (vencida): a queda
        conta, a Rosa Vermelha vai para a bolsa com FLAG_FAMILIA_ROSA_1 e a sala esvazia."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), False)
        self._set_half_day(QUEDA_ROSA)
        for slot in (0, 1):
            for i in range(4):
                self.box.set_party_move(slot, i, self.moves["MOVE_PSYCHIC"])
        self._gatilho()
        self._scene(self.game.in_battle, "começo da dupla")
        assert self.driver.battle_type_flags() & 1, "os gêmeos não lutaram em dupla"
        assert self.driver.fight_to_end() == "win", "perdeu para os gêmeos"
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        assert self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")), "gêmeos vencidos sem a flag"
        assert self.driver.fight_to_end() == "win", "perdeu para o Dom"
        half = self._half_day()
        assert half == QUEDA_ROSA, half
        msgs = self._scene(self.ctl.overworld_idle, "a rosa", shot=("Rosa Vermelha", "familia_rosa"))
        rosa = self.consts.item("ITEM_ROSA_VERMELHA")
        assert self.game.bag_quantity(rosa) == 1, f"Rosa Vermelha na bolsa: {self.game.bag_quantity(rosa)}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_1"))
        assert self.box.familia_estado() == (1, ESTADO_SEM_CHEFE, half), self.box.familia_estado()
        assert self._active_objects() == [], self._active_objects()
        drop = self._rom_text("Route23_FamiliaSombra_6F_Text_RosaDom")
        assert drop in msgs, msgs
        return f"gêmeos e Dom vencidos; {drop!r}; Rosa Vermelha na bolsa; SEM_CHEFE na queda {half}"

    # --- Task 7: conquistas e diário -------------------------------------------------------------------
    def _conq(self, cid: str) -> int:
        return self.box.conq_estado(cq.num(cid))[0]

    def _tela_pronta(self, what: str) -> tuple[int, int, int, bool]:
        self.ctl.wait_until(lambda: (s := self.box.conq_tela()) is not None and s[3], TELA_PRONTA_TIMEOUT, what)
        self.emu.frames(TELA_ASSENTA)
        return self.box.conq_tela()

    def _fechar_tela(self) -> None:
        self.ctl.press_until(KEY_B, lambda: self.box.conq_tela() is None, "B fecha a tela de conquistas",
                             tries=3, wait=60)
        self.ctl.wait_overworld_idle(600)

    def _conquista_dom(self) -> str:
        """O jogo já zerado e o Dom vencido pela cena de verdade: a conquista e a entrada do diário (com o título)."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True)
        self.box.conq_reset(True)
        self.box.set_flag(self._flag("FLAG_SYS_GAME_CLEAR"), True)   # a sala é do pós-jogo: o diário não depende do Hall
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_PSYCHIC"])
        assert [self._conq(c) for c in ("familia_dom", "familia_cobrador", "familia_pedagio")] == [CONQ_PENDENTE] * 3
        assert self.box.diario_entrada(cq.evento("familia_dom")) is None
        self._gatilho()
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        assert self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self._conq("familia_dom") == CONQ_PENDENTE, "feita antes de vencer"
        assert self.driver.fight_to_end() == "win", "perdeu para o Dom"
        self._scene(self.ctl.overworld_idle, "a rosa")
        assert self._conq("familia_dom") == CONQ_FEITA, "Vencer o Dom não ficou feita"
        outras = [self._conq(c) for c in ("familia_cobrador", "familia_pedagio", "familia_mercenario", "familia_toda")]
        assert outras == [CONQ_PENDENTE] * 4, outras
        e = self.box.diario_entrada(cq.evento("familia_dom"))
        assert e is not None, "o Dom vencido e o diário vazio"
        assert e["resultado"] == DIARIO_DERROTOU and e["turnos"] >= 1, e
        assert e["time"] == [(self._sp("MEWTWO"), 100), (self._sp("SNORLAX"), 100)], e
        assert self.box.diario_entrada(cq.evento("familia_cobrador")) is None
        titulo = cq.dados()["diario"][cq.evento("familia_dom")]
        assert titulo["nome"] == "O Dom" and titulo["especie"] == "SPECIES_GENGAR", titulo
        # a tela de conquistas, na aba Batalha rolada até o fim, e o diário com a entrada
        self.box.open_conquistas()
        self._tela_pronta("tela de conquistas")
        self.ctl.press_until(KEY_R, lambda: self.box.conq_tela()[1] == CONQ_BATALHA_ABA, "R: aba Batalha",
                             tries=3, wait=10)
        for _ in range(DESCE_ATE_O_FIM):
            self.emu.press(KEY_DOWN, hold=2, release=6)
        self.emu.frames(TELA_ASSENTA)
        shot_conq = self._shot("familia_conquistas_batalha")
        self._fechar_tela()
        self.box.open_conquistas(True)
        self._tela_pronta("tela do diário")
        shot_diario = self._shot("familia_diario_dom")
        self._fechar_tela()
        return (f"Dom vencido com o jogo zerado: Vencer o Dom feita, as outras 4 pendentes; diário: {titulo['nome']!r} "
                f"derrotado em {e['turnos']} turnos, time {len(e['time'])}; telas {shot_conq} e {shot_diario}")

    def _gengar_fora(self) -> str:
        """Um Gengar selvagem comum (fora da sala do Dom, sem BATTLE_TYPE_FAMILIA_CHEFE) não grava nada."""
        self._restore("familia_base")
        self.box.conq_reset(True)
        self.box.set_flag(self._flag("FLAG_SYS_GAME_CLEAR"), True)
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_PSYCHIC"])
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp("GENGAR"), 62) == 1, "START_WILD_BATTLE"
        self.driver.wait_battle_start()
        assert not self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.driver.fight_to_end() == "win", "perdeu para o Gengar selvagem"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        self.ctl.wait_overworld_idle(900)
        assert self.box.diario_entrada(cq.evento("familia_dom")) is None, "o Gengar selvagem entrou como o Dom"
        assert self._conq("familia_dom") == CONQ_PENDENTE
        return "Gengar selvagem nv 62 vencido: sem entrada do Dom no diário e a conquista pendente"

    def _encontro_andar4(self) -> str:
        """Passos de verdade no 4º andar com chefe ativo: sai um capanga do plantel (BATTLE_TYPE_FAMILIA)."""
        self._restore("familia_base")
        group, num = self.consts.map("MAP_ROUTE23_FAMILIA_SOMBRA_4F")
        self.box.call(CMD_WARP, group | num << 8, VAI_E_VEM_4F[0][0] | VAI_E_VEM_4F[0][1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para o 4º andar")
        self.ctl.wait_until(lambda: self.ctl.overworld_idle() or self.game.in_battle(), 900, "4º andar")
        steps = self._walk_until_battle(PASSOS_ANDAR)
        assert self.game.in_battle(), f"nenhum encontro em {PASSOS_ANDAR} passos no 4º andar"
        self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA and not flags & BATTLE_TYPE_TRAINER, f"gBattleTypeFlags {flags:#x}"
        plantel = times_table("sFamiliaPlantel")[0]
        species, level = self.driver.battler_species_level(1)
        assert any(self._sp(m[0]) == species for m in plantel) and 54 <= level <= 58, (species, level)
        return f"encontro no passo {steps}: {self.consts.species_name(species)} nv {level}"

    def _sem_encontro(self) -> str:
        """Sem chefe, o 4º andar fica vazio: nenhum item e nenhum encontro em PASSOS_ANDAR passos."""
        self._restore("familia_base")
        self.box.familia_set(1, ESTADO_SEM_CHEFE, self._half_day())
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_4F", VAI_E_VEM_4F[0])
        assert self._active_objects() == [], f"objetos no 4º andar sem chefe: {self._active_objects()}"
        steps = self._walk_until_battle(PASSOS_ANDAR)
        assert not self.game.in_battle() and steps == PASSOS_ANDAR, steps
        return f"{steps} passos sem encontro e sem itens"

    def _walk_until_battle(self, limit: int) -> int:
        steps, k = 0, 0
        while steps < limit and not self.game.in_battle():
            # o encontro começa no fim de um passo e a batalha demora uns quadros para aparecer
            self.ctl.wait_until(lambda: self.ctl.overworld_idle() or self.game.in_battle(), 600, "4º andar livre")
            if self.game.in_battle():
                break
            direction = VAI_E_VEM_4F[1][k % 2]
            moved = self.nav.step(direction, 4)
            steps += moved
            k += 1
            if self.nav.interrupted == "battle" or self.game.in_battle():
                break
        return steps

    # --- Ajustes do Cintra: a rosa com o bolso de itens-chave cheio ----------------------------------
    def _encher_itens_chave(self) -> int:
        """Enche o bolso de itens-chave (BAG_KEYITEMS_COUNT slots) com itens-chave que não são rosas."""
        itens = [i["itemId"] for i in json.loads(ITEMS_JSON.read_text(encoding="utf-8"))["items"]
                 if i.get("pocket") == "POCKET_KEY_ITEMS" and not i["itemId"].startswith("ITEM_ROSA_")]
        for nome in itens:
            if len(self.game.bag_pocket(KEY_ITEMS_POCKET)) >= BAG_KEYITEMS_COUNT:
                break
            self.box.call(CMD_GIVE_ITEM, self.consts.item(nome), 1)
        cheio = len(self.game.bag_pocket(KEY_ITEMS_POCKET))
        assert cheio == BAG_KEYITEMS_COUNT, f"bolso de itens-chave com {cheio} slots"
        return cheio

    def _chefe_balcao(self) -> str:
        """Fugir do chefe e falar com ele de novo sem sair da sala: na frente da mesa, olhando para cima, o A atravessa
        os 2 tiles de balcão da mesa e a batalha do chefe recomeça."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True)
        self._gatilho()
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        assert self.driver.run_away(), "não fugiu do chefe"
        self._scene(self.ctl.overworld_idle, "volta da fuga")
        assert sorted(self._active_objects()) == [1], self._active_objects()
        assert self.nav.walk_to(*FRENTE_DA_MESA), f"não chegou à frente da mesa: {self.game.player_xy()}"
        self.emu.press(KEY_UP, hold=4, release=12)      # vira para a mesa (o tile de cima tem colisão)
        self.ctl.wait_overworld_idle(120)
        assert self.game.player_xy() == FRENTE_DA_MESA, self.game.player_xy()
        self.emu.press(KEY_A, hold=2, release=8)
        self.ctl.wait_until(self.ctl.script_active, 60, "A na mesa abre a fala do chefe")
        msgs = self._scene(self.game.in_battle, "a revanche pelo balcão")
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA_CHEFE, f"gBattleTypeFlags {flags:#x}"
        fala = self._rom_text("Route23_FamiliaSombra_6F_Text_DomSemGemeos").split("\n")[0]
        assert any(m.startswith(fala) for m in msgs), f"sem a fala do Dom; mensagens {msgs}"
        return f"fugiu; de {FRENTE_DA_MESA} olhando para cima, o A no balcão recomeçou a batalha do chefe"

    def _rosa_bolsa_cheia(self) -> str:
        """Bolso de itens-chave cheio: o Dom vencido liga FLAG_FAMILIA_ROSA_1 (a redoma da Sala de Troféus acende por
        ela), a rosa NÃO entra na bolsa e a fala diz que ela foi direto para a Sala de Troféus da Ilha Sete."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True)
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_PSYCHIC"])
        slots = self._encher_itens_chave()
        self._gatilho()
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        assert self.driver.fight_to_end() == "win", "perdeu para o Dom"
        msgs = self._scene(self.ctl.overworld_idle, "a rosa com a bolsa cheia")
        rosa = self.consts.item("ITEM_ROSA_VERMELHA")
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_1")), "a flag da rosa não ligou"
        assert self.game.bag_quantity(rosa) == 0, f"Rosa Vermelha na bolsa: {self.game.bag_quantity(rosa)}"
        assert len(self.game.bag_pocket(KEY_ITEMS_POCKET)) == BAG_KEYITEMS_COUNT
        want = self._rom_text("Route23_FamiliaSombra_6F_Text_BolsaCheiaRosaVermelha")
        assert want in msgs, f"sem a fala da Sala de Troféus; mensagens {msgs}"
        assert self.box.familia_estado()[:2] == (1, ESTADO_SEM_CHEFE), self.box.familia_estado()
        return f"bolso com {slots} itens-chave: FLAG_FAMILIA_ROSA_1 ligada, rosa fora da bolsa, fala {want[:40]!r}…"

    # --- Ajustes do Cintra: CONTINUAR parado na Rota 23 --------------------------------------------------
    def _var(self, var: int) -> int:
        return self.emu.read_u16(self.emu.read_u32(self._sym("gSaveBlock1Ptr")) + SB1_VARS + (var - VARS_START) * 2)

    def _metatile(self, x: int, y: int) -> int:
        base = self._sym("VMap")                     # struct BackupMapLayout (src/fieldmap.c)
        width = self.emu.read_u32(base + BACKUP_LAYOUT_WIDTH)
        grid = self.emu.read_u32(base + BACKUP_LAYOUT_MAP)
        return self.emu.read_u16(grid + 2 * ((y + MAP_OFFSET) * width + x + MAP_OFFSET)) & 0x3FF

    def _object_visible(self, local: int) -> bool:
        base = self._sym("gObjectEvents")
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            if self.emu.read_u8(addr) & 1 and self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID) == local:
                return not self.emu.read_u8(addr + OBJECT_EVENT_FLAGS_1) & INVISIBLE_BIT
        return False

    def _rota23_agora(self) -> dict:
        predio = json.loads(PREDIO_JSON.read_text(encoding="utf-8"))["indigo_plateau"]
        porta = self._metatile(*PORTA)
        assert porta in (predio["porta_trancada"], predio["porta_aberta"]), f"metatile da porta {porta:#x}"
        layouts = header_defines(REPO_ROOT, "layouts.h")
        return {
            "mapa": self.game.location(), "xy": self.game.player_xy(),
            "layout": self.emu.read_u16(self._sym("gMapHeader") + MAP_HEADER_LAYOUT_ID) == layouts["LAYOUT_ROUTE23"],
            "porta_trancada": porta == predio["porta_trancada"],
            "persian": self._object_visible(LOCALID_COBRADOR),
            "policia": any(self._object_visible(l) for l in LOCALIDS_POLICIA),
            "pedagio_armado": self._var(VAR_TEMP_3) == 1,
            "estado": self.box.familia_estado()[:2],
        }

    def _continue_rota23(self, ocupacao: int, estado: int, insignia: bool) -> str:
        """O estado (`ocupacao`, `estado`, 8ª insígnia), a saída do prédio até o lado sul do pedágio, salvar parado na
        Rota 23, resetar e CONTINUAR (só o ON_LOAD roda): o mesmo mapa e layout, o jogador no mesmo tile, a porta
        trancada só antes da insígnia e o Persian visível exatamente quando o pedágio está armado."""
        self._restore("familia_base")
        self.box.set_flag(self._flag("FLAG_BADGE08_GET"), insignia)
        self.box.set_flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"), False)
        self.box.call(CMD_SET_VAR, VAR_MAP_SCENE_ROUTE23, 0)      # sem a cena dos guardas das insígnias
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self.box.familia_set(ocupacao, estado, self._half_day())
        self._sair_do_predio()
        assert self.nav.walk_to(*PEDAGIO_SUL), f"não chegou perto do pedágio: {self.game.player_xy()}"
        self.ctl.wait_overworld_idle(300)
        antes = self._rota23_agora()
        assert self.menu.save_game() == 1, "save"
        self.emu.flush_save()
        self.emu.reset()
        nome = {ESTADO_FECHADO: "fechado", ESTADO_ATIVA: "ativa", ESTADO_SEM_CHEFE: "sem_chefe"}[estado]
        self._title_to_continue("tela de título depois do reset", shot=f"familia_continue_rota23_{nome}")
        self.box.conq_silencio(True)
        self.emu.frames(30)
        depois = self._rota23_agora()
        assert depois == antes, f"antes do save {antes}, depois do CONTINUAR {depois}"
        assert depois["mapa"] == self.consts.map("MAP_ROUTE23") and depois["layout"], depois
        assert depois["xy"] == PEDAGIO_SUL, depois
        assert depois["porta_trancada"] == (estado == ESTADO_FECHADO), depois
        assert depois["persian"] == depois["pedagio_armado"] == (estado == ESTADO_ATIVA), depois
        assert not depois["policia"], f"a polícia apareceu no CONTINUAR sem a Família encerrada: {depois}"
        return (f"CONTINUAR em {depois['xy']}: layout LAYOUT_ROUTE23, porta "
                f"{'trancada' if depois['porta_trancada'] else 'aberta'}, Persian "
                f"{'visível e pedágio armado' if depois['persian'] else 'ausente e pedágio desarmado'}")

    def _continue_ativa(self) -> str:
        return self._continue_rota23(1, ESTADO_ATIVA, True)

    def _continue_sem_chefe(self) -> str:
        return self._continue_rota23(1, ESTADO_SEM_CHEFE, True)

    def _continue_fechado(self) -> str:
        return self._continue_rota23(0, ESTADO_FECHADO, False)

    # --- O quadro da sala do Dom: o retrato do chefe da ocupação ------------------------------------------
    def _quadro(self) -> str:
        """Qual quadro está na parede da sala (os 6 metatiles de (7..9, 1..2) em VMap): "dom", "cobrador", "mercenario"
        ou "pesadelo"."""
        q = json.loads(PREDIO_JSON.read_text(encoding="utf-8"))["quadro"]
        agora = [[self._metatile(q["x"] + dx, q["y"] + dy) for dx in range(3)] for dy in range(2)]
        achados = [nome for nome, ids in q["metatiles"].items() if ids == agora]
        assert len(achados) == 1, f"quadro desconhecido: {agora}"
        return achados[0]

    def _sala_igual_ao_layout(self) -> None:
        """A sala carregada (VMap) é a do map.bin do repositório, fora o quadro (que o ON_LOAD troca): pega ROM
        compilada com layout velho e tileset novo (metatiles trocados)."""
        raw = (REPO_ROOT / "data/layouts/Route23_FamiliaSombra_6F/map.bin").read_bytes()
        q = json.loads(PREDIO_JSON.read_text(encoding="utf-8"))["quadro"]
        largura = 13
        diferentes = []
        for i in range(len(raw) // 2):
            x, y = i % largura, i // largura
            if q["x"] <= x < q["x"] + 3 and q["y"] <= y < q["y"] + 2:
                continue
            esperado = int.from_bytes(raw[i * 2:i * 2 + 2], "little") & 0x3FF
            if self._metatile(x, y) != esperado:
                diferentes.append((x, y))
        assert not diferentes, f"sala diferente do map.bin em {diferentes[:8]}"

    def _quadro_cobrador(self) -> str:
        """Ocupação 2 pelo atalho FAMILIA_SET: subindo pela escada do 5º andar, o retrato é o do Cobrador (tela
        `familia_quadro_cobrador`, só gravada); sem chefe fica o do último chefe; as ocupações 3 e 4 trazem o
        retrato do Mercenário e o do Pesadelo."""
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self.box.familia_set(2, ESTADO_ATIVA)
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_5F", ANTES_DA_ESCADA)
        self.nav.go_through_warp("right")
        self._settle("6º andar")
        assert self._at("MAP_ROUTE23_FAMILIA_SOMBRA_6F"), self.game.location()
        self.emu.frames(30)
        shot = self._shot("familia_quadro_cobrador")
        visto = {"ocupação 2": self._quadro()}
        assert self._object_gfx(1) == self.gfx["OBJ_EVENT_GFX_FAMILIA_TYRANITAR_SHINY"], "o chefe não é o Cobrador"
        self.box.familia_set(2, ESTADO_SEM_CHEFE, self._half_day())
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_6F", SAIDA_ESCADA_6F)
        visto["sem chefe (depois da 2)"] = self._quadro()
        self.box.familia_set(3, ESTADO_ATIVA)
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_6F", SAIDA_ESCADA_6F)
        visto["ocupação 3"] = self._quadro()
        self.box.familia_set(4, ESTADO_ATIVA)
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_6F", SAIDA_ESCADA_6F)
        visto["ocupação 4"] = self._quadro()
        self.box.familia_set(1, ESTADO_SEM_CHEFE, self._half_day())
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_6F", SAIDA_ESCADA_6F)
        visto["sem chefe (depois da 1)"] = self._quadro()
        assert visto == {"ocupação 2": "cobrador", "sem chefe (depois da 2)": "cobrador", "ocupação 3": "mercenario",
                         "ocupação 4": "pesadelo", "sem chefe (depois da 1)": "dom"}, visto
        return f"quadros {visto}; tela {shot}"

    # --- POK-54, Task 7: ocupações 3 e 4 (o Mercenário e o Pesadelo), a captura registrada e o fim da Família --------
    def _queda(self, ocupacao: int, estado_seguinte: int, half: int, queda_antes: int = 0) -> tuple[int, int, tuple]:
        """O chefe da `ocupacao` (ATIVA, com `queda_antes` na var da queda) cai pelo special de verdade (atalho
        FAMILIA_CHEFE_CAIU), no meio-dia `half`."""
        self._set_half_day(half)
        self.box.familia_set(ocupacao, ESTADO_ATIVA, queda_antes)
        got = self.box.familia_chefe_caiu()
        assert got[:2] == (ocupacao, estado_seguinte), got
        return got

    def _virar_de_ocupacao(self, half: int, ocupacao: int) -> None:
        """Espera o retorno da máfia (`half` já é o meio-dia da queda + 7) entrando na Rota 23 (o on_transition roda
        FamiliaSombra_Atualizar) e confere a ocupação que chegou, ATIVA, com tudo de volta; depois entra e sai de novo
        para provar que o repovoamento é uma vez só."""
        self._set_half_day(half)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (ocupacao, ESTADO_ATIVA), self.box.familia_estado()
        assert not any(self._repovoaveis().values()), f"não repovoou: {self._repovoaveis()}"
        self._mark_repovoaveis()            # o jogador vence o capanga e pega o item
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (ocupacao, ESTADO_ATIVA), self.box.familia_estado()
        assert all(self._repovoaveis().values()), f"repovoou de novo: {self._repovoaveis()}"

    def _ciclo_ate_o_fim(self) -> str:
        """O ciclo inteiro pelo relógio, de verdade: a queda do chefe 2 + 7 meios-dias traz o Mercenário, uma vez só;
        a queda do 3 + 7 traz o Pesadelo; a queda do 4 fecha a Família (ENCERRADA, com a queda dele gravada) e nem 20
        meios-dias depois a máfia volta."""
        self._restore("familia_base")
        log = []
        queda2 = 20
        self._queda(2, ESTADO_SEM_CHEFE, queda2)
        assert self.box.familia_estado() == (2, ESTADO_SEM_CHEFE, queda2), self.box.familia_estado()
        self._set_half_day(queda2 + 6)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (2, ESTADO_SEM_CHEFE), "voltou antes dos 7 meios-dias"
        self._virar_de_ocupacao(queda2 + 7, 3)
        log.append("queda 2 + 7: ocupação 3 ATIVA, uma vez só")
        queda3 = queda2 + 9
        self._queda(3, ESTADO_SEM_CHEFE, queda3, queda2)
        assert self.box.familia_estado() == (3, ESTADO_SEM_CHEFE, queda3), self.box.familia_estado()
        self._virar_de_ocupacao(queda3 + 7, 4)
        log.append("queda 3 + 7: ocupação 4 ATIVA, uma vez só")
        queda4 = queda3 + 9
        self._queda(4, ESTADO_ENCERRADA, queda4, queda3)
        # ENCERRADA também grava a queda (Task 10): a var não fica com a do chefe 3
        assert self.box.familia_estado() == (4, ESTADO_ENCERRADA, queda4), self.box.familia_estado()
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_4")), "a rosa negra não ligou"
        self._set_half_day(queda4 + 20)
        for _ in range(2):
            self._warp("MAP_ROUTE23", ROTA23_SUL)
            self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        assert self.box.familia_estado() == (4, ESTADO_ENCERRADA, queda4), self.box.familia_estado()
        assert self.box.familia_chefe_caiu()[:2] == (4, ESTADO_ENCERRADA), "chamada repetida mudou o estado"
        assert self.box.familia_estado()[2] == queda4, "a chamada repetida regravou a queda"
        log.append("queda 4: ENCERRADA com a queda dele gravada; +20 meios-dias e continua ENCERRADA")
        return "; ".join(log)

    def _chefe_de(self, ocupacao: int, abertura: str, musica: str, tela: str, checkpoint: str) -> str:
        """O chefe da `ocupacao` pelo special de verdade: abertura com o título, espécie shiny, nível, golpes e item da
        tabela, batalha lendária de chefe, a música certa e a paleta shiny."""
        self._restore("familia_base")
        expected = chefe_da_tabela(ocupacao)
        species = self._sp(expected[0])
        self.box.familia_set(ocupacao, ESTADO_ATIVA)
        self.box.familia_chefe()
        seen = self._wait_intro(abertura, (1,))
        assert self.driver.battler_species_level(1)[0] == species, seen
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA_CHEFE and flags & BATTLE_TYPE_LEGENDARY, f"gBattleTypeFlags {flags:#x}"
        assert not flags & (BATTLE_TYPE_FAMILIA | BATTLE_TYPE_TRAINER), f"gBattleTypeFlags {flags:#x}"
        mon = self.game.enemy_party()[0]
        assert mon.is_shiny, f"chefe não shiny: pid {mon.personality:#x}, OT {mon.ot_id:#x}"
        sp, lv, item, moves = expected
        got = (mon.species, mon.level, mon.held_item, mon.moves)
        want = (species, lv, self.consts.item(f"ITEM_{item}"), [self.moves[f"MOVE_{m}"] for m in moves])
        assert got == want, f"{sp}: {got}, esperava {want}"
        assert self._bgm_is(musica), f"a música não é {musica}"
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        shiny = self._species_palette(species, True)
        got_pal = self._battler_palette(1)
        assert got_pal == shiny, f"paleta do chefe {[hex(c) for c in got_pal]}, esperava a shiny"
        shot = self._shot(tela)
        self.ctl.checkpoint(checkpoint)
        return (f"{sp} nv {lv} shiny, {item}, {moves}; abertura {self._rom_text(abertura)!r}; {musica}; "
                f"paleta shiny; tela {shot}")

    def _chefe_mercenario(self) -> str:
        return self._chefe_de(3, "gText_FamiliaChefeMercenario", "MUS_VS_LEGEND", "familia_chefe_mercenario",
                              "familia_mercenario")

    def _chefe_pesadelo(self) -> str:
        """O Darkrai de verdade, com a música do Deoxys; depois a IA: contra um Golem nv 100 só com Endurecer ela abre
        com Vazio Negro (o Golem dorme) e nunca usa Comedor de Sonhos com o Golem acordado."""
        texto = self._chefe_de(4, "gText_FamiliaChefePesadelo", "MUS_VS_DEOXYS", "familia_chefe_pesadelo",
                               "familia_pesadelo")
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("GOLEM"), 100)
        self.box.set_party_move(0, 0, self.moves["MOVE_HARDEN"])
        self.box.familia_set(4, ESTADO_ATIVA)
        self.box.familia_chefe()
        dark_void, dream = self.moves["MOVE_DARK_VOID"], self.moves["MOVE_DREAM_EATER"]
        chosen = []
        for turn in range(1, AI_TURNS + 1):
            self.driver.wait_action_menu(INTRO_TIMEOUT)
            asleep = bool(self.emu.read_u32(self._sym("gBattleMons") + BATTLE_MON_STATUS1) & STATUS1_SLEEP)
            self.emu.frames(10)
            move, result = self._turn_reading_foe_move()
            name = self.moves_names.get(move, str(move))
            chosen.append(name + (" (Golem dormindo)" if asleep else ""))
            if turn == 1:
                assert move == dark_void, f"turno 1: {name}, esperava MOVE_DARK_VOID"
                ai = self.emu.read_u32(self.emu.read_u32(self._sym("gBattleResources")) + AI_RESOURCES)
                bits = self.emu.read_u8(ai + AI_LOGIC_ID)
                assert bits == CHEFE_AI_BITS, f"IA do chefe com {bits} bits de flags, esperava {CHEFE_AI_BITS}"
            assert not (move == dream and not asleep), f"turno {turn}: Comedor de Sonhos com o Golem acordado"
            if result != "menu":      # o Golem pode cair no último turno (Comedor de Sonhos com ele dormindo)
                assert turn > 1, f"turno {turn}: a batalha acabou ({result})"
                break
        return f"{texto} | IA do Darkrai contra o Golem: {chosen}"

    def _capturar(self, ball: int, quem: str) -> None:
        """Lança a bola `ball` no chefe em campo e leva a captura até o campo: sem apelido (B), o resto com A."""
        d = self.driver
        assert d.throw_ball(ball), f"a Master Ball não capturou {quem}"
        for _ in range(4000):
            if d._battle_over():
                break
            d._press(KEY_B if d._script_command() == NICKNAME_COMMAND else KEY_A)
        assert d.outcome() == B_OUTCOME_CAUGHT, f"gBattleOutcome = {d.outcome()}"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        self.ctl.wait_overworld_idle(900)

    def _captura_marca(self) -> str:
        """Master Ball no Mercenário: o chefe cai capturado e só o bit 3 liga. O Pesadelo vencido sem captura: bit 4
        desligado, ENCERRADA e a queda não gravada."""
        self._restore("familia_mercenario")
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1
        self._capturar(master, "o Mercenário")
        got = self.box.familia_chefe_caiu()
        assert got == (3, ESTADO_SEM_CHEFE, (False, False, True, False)), got
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_3"))
        capturado = f"Mercenário capturado: {got}"
        # o Pesadelo vencido sem captura: Superpoder (Lutador, 2x no tipo Sombrio) do Mewtwo mais rápido derruba num golpe
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_SUPERPOWER"])
        self.box.familia_set(4, ESTADO_ATIVA)
        self.box.familia_chefe()
        self.driver.wait_battle_start()
        assert self.driver.fight_to_end() == "win", "perdeu para o Pesadelo"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        self.ctl.wait_overworld_idle(900)
        got = self.box.familia_chefe_caiu()
        assert got == (4, ESTADO_ENCERRADA, (False, False, False, False)), got
        assert self.box.familia_estado()[2] == 0, "ENCERRADA gravou a queda"
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_4"))
        return f"{capturado}; Pesadelo vencido sem captura: {got}"

    def _conquistas_parte2(self) -> str:
        """As conquistas 44 e 45 e o diário pelas lutas de verdade: um Garchomp selvagem comum não grava nada; o
        Mercenário vencido marca "Vencer o Mercenário" e a entrada de "O Mercenário"; o Pesadelo capturado marca
        "Derrubar a Família Sombra" e a entrada de "O Pesadelo"."""
        self._restore("familia_base")
        self.box.conq_reset(True)
        self.box.set_flag(self._flag("FLAG_SYS_GAME_CLEAR"), True)
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_PSYCHIC"])
        mercenario, pesadelo = cq.evento("familia_mercenario"), cq.evento("familia_pesadelo")
        assert [self._conq(c) for c in ("familia_mercenario", "familia_toda")] == [CONQ_PENDENTE] * 2
        # 1) o Garchomp comum (nv 74, sem o chefe) não grava nada
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp("GARCHOMP"), 74) == 1, "START_WILD_BATTLE"
        self.driver.wait_battle_start()
        assert not self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.driver.fight_to_end() == "win", "perdeu para o Garchomp selvagem"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        self.ctl.wait_overworld_idle(900)
        assert self.box.diario_entrada(mercenario) is None, "o Garchomp selvagem entrou como o Mercenário"
        assert self._conq("familia_mercenario") == CONQ_PENDENTE
        # 2) o Mercenário de verdade, vencido
        self.box.familia_set(3, ESTADO_ATIVA)
        self.box.familia_chefe()
        self.driver.wait_battle_start()
        assert self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.driver.fight_to_end() == "win", "perdeu para o Mercenário"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        self.ctl.wait_overworld_idle(900)
        assert self._conq("familia_mercenario") == CONQ_PENDENTE, "feita antes da queda"
        assert self.box.familia_chefe_caiu()[:2] == (3, ESTADO_SEM_CHEFE)
        assert self._conq("familia_mercenario") == CONQ_FEITA, "Vencer o Mercenário não ficou feita"
        assert self._conq("familia_toda") == CONQ_PENDENTE
        e = self.box.diario_entrada(mercenario)
        assert e is not None and e["resultado"] == DIARIO_DERROTOU and e["turnos"] >= 1, e
        assert e["time"] == [(self._sp("MEWTWO"), 100), (self._sp("SNORLAX"), PLAYER_LEVEL)], e
        titulo = cq.dados()["diario"][mercenario]
        assert titulo["nome"] == "O Mercenário" and titulo["especie"] == "SPECIES_GARCHOMP", titulo
        assert titulo["local"] == "Garchomp, Rota 23", titulo
        # 3) o Pesadelo de verdade, capturado
        self.box.familia_set(4, ESTADO_ATIVA)
        self.box.familia_chefe()
        self.driver.wait_battle_start()
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1
        self._capturar(master, "o Pesadelo")
        assert self._conq("familia_toda") == CONQ_PENDENTE, "feita antes da queda"
        assert self.box.familia_chefe_caiu() == (4, ESTADO_ENCERRADA, (False, False, False, True))
        assert self._conq("familia_toda") == CONQ_FEITA, "Derrubar a Família Sombra não ficou feita"
        assert self._conq("familia_mercenario") == CONQ_FEITA
        e = self.box.diario_entrada(pesadelo)
        assert e is not None and e["resultado"] == DIARIO_CAPTURADO, e
        titulo = cq.dados()["diario"][pesadelo]
        assert titulo["nome"] == "O Pesadelo" and titulo["especie"] == "SPECIES_DARKRAI", titulo
        assert titulo["local"] == "Darkrai, Rota 23", titulo
        return ("Garchomp selvagem sem registro; Mercenário vencido: conquista 44 feita e diário DERROTOU; Pesadelo "
                "capturado: conquista 45 feita, diário CAPTURADO e ENCERRADA")

    # --- POK-54, Task 8: a sala do Mercenário e do Pesadelo, as rosas azul e negra, as 4 redomas --------------------
    def _sala_do_chefe(self, ocupacao: int, chefe: str, gemeos: str, quadro: str, tela: str) -> str:
        """Ocupação `ocupacao` pelo atalho FAMILIA_SET, subindo pela escada do 5º andar: o chefe shiny de chapéu na
        poltrona, os dois gêmeos de chapéu um de cada lado, o retrato dele no quadro e o resto da sala igual ao layout."""
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self.box.familia_set(ocupacao, ESTADO_ATIVA)
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_5F", ANTES_DA_ESCADA)
        self.nav.go_through_warp("right")
        self._settle("6º andar")
        assert self._at("MAP_ROUTE23_FAMILIA_SOMBRA_6F"), self.game.location()
        self.emu.frames(30)
        shot = self._shot(tela)
        assert self._quadro() == quadro, f"o quadro é {self._quadro()}, esperava {quadro}"
        chefe_gfx = [self._object_gfx(local) for local in (1, 2, 3)]
        want = [self.gfx[f"OBJ_EVENT_GFX_{n}"] for n in (chefe, gemeos, gemeos)]
        assert chefe_gfx == want, f"chefe e gêmeos {chefe_gfx}, esperava {want} ({chefe}, 2x {gemeos})"
        self._sala_igual_ao_layout()
        return f"{chefe} de chapéu, 2x {gemeos}, retrato {quadro} no quadro; tela {shot}"

    def _sala_mercenario(self) -> str:
        return self._sala_do_chefe(3, "FAMILIA_GARCHOMP_SHINY", "FAMILIA_GLIGAR", "mercenario", "familia_sala_mercenario")

    def _sala_pesadelo(self) -> str:
        return self._sala_do_chefe(4, "FAMILIA_DARKRAI_SHINY", "FAMILIA_DUSCLOPS", "pesadelo", "familia_sala_pesadelo")

    def _fala_vista(self, msgs: list[str], simbolo: str) -> None:
        """A fala `simbolo` do texto da sala passou pelo campo (a 1ª linha dela abre alguma mensagem vista)."""
        primeira = self._rom_text(f"Route23_FamiliaSombra_6F_Text_{simbolo}").split("\n")[0]
        assert any(m.startswith(primeira) for m in msgs), f"sem a fala {simbolo} ({primeira!r}); mensagens {msgs}"

    def _rosa_azul(self) -> str:
        """A cena inteira da ocupação 3: o Mercenário fala, os gêmeos Gligar (dupla vencida), ele fala de novo e é
        vencido: a Rosa Azul vai para a bolsa com FLAG_FAMILIA_ROSA_3, a queda conta e a sala esvazia."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), False, 3)
        self._set_half_day(QUEDA_ROSA)
        for slot in (0, 1):
            for i in range(4):
                self.box.set_party_move(slot, i, self.moves["MOVE_PSYCHIC"])
        self._gatilho()
        msgs = self._scene(self.game.in_battle, "começo da dupla")
        assert self.driver.battle_type_flags() & 1, "os gêmeos Gligar não lutaram em dupla"
        self._fala_vista(msgs, "Mercenario")
        assert self.driver.fight_to_end() == "win", "perdeu para os gêmeos Gligar"
        msgs += self._scene(self.game.in_battle, "começo da batalha do Mercenário")
        assert self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")), "gêmeos vencidos sem a flag"
        self._fala_vista(msgs, "DesafioMercenario")
        assert self.driver.fight_to_end() == "win", "perdeu para o Mercenário"
        half = self._half_day()
        assert half == QUEDA_ROSA, half
        msgs = self._scene(self.ctl.overworld_idle, "a rosa azul", shot=("Rosa Azul", "familia_rosa_azul"))
        rosa = self.consts.item("ITEM_ROSA_AZUL")
        assert self.game.bag_quantity(rosa) == 1, f"Rosa Azul na bolsa: {self.game.bag_quantity(rosa)}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_3"))
        assert not self.game.flag(self._flag("FLAG_FAMILIA_ROSA_4"))
        assert self.box.familia_estado() == (3, ESTADO_SEM_CHEFE, half), self.box.familia_estado()
        assert self._active_objects() == [], self._active_objects()
        drop = self._rom_text("Route23_FamiliaSombra_6F_Text_RosaMercenario")
        assert drop in msgs, msgs
        assert "GARCHOMP, O MERCENÁRIO" in drop
        return f"gêmeos Gligar e Mercenário vencidos; {drop!r}; Rosa Azul na bolsa; SEM_CHEFE na queda {half}"

    def _rosa_negra_bolsa_cheia(self) -> str:
        """Ocupação 4 com o bolso de itens-chave cheio: o Pesadelo vencido liga FLAG_FAMILIA_ROSA_4 (a redoma acende por
        ela), a rosa NÃO entra na bolsa, a fala manda a rosa para a Sala de Troféus e a Família fica ENCERRADA."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True, 4)
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_SUPERPOWER"])
        slots = self._encher_itens_chave()
        self._gatilho()
        msgs = self._scene(self.game.in_battle, "começo da batalha do Pesadelo")
        self._fala_vista(msgs, "PesadeloSemGemeos")
        assert self.driver.fight_to_end() == "win", "perdeu para o Pesadelo"
        msgs = self._scene(self.ctl.overworld_idle, "a rosa negra com a bolsa cheia")
        rosa = self.consts.item("ITEM_ROSA_NEGRA")
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_4")), "a flag da rosa negra não ligou"
        assert self.game.bag_quantity(rosa) == 0, f"Rosa Negra na bolsa: {self.game.bag_quantity(rosa)}"
        assert len(self.game.bag_pocket(KEY_ITEMS_POCKET)) == BAG_KEYITEMS_COUNT
        want = self._rom_text("Route23_FamiliaSombra_6F_Text_BolsaCheiaRosaNegra")
        assert want in msgs, f"sem a fala da Sala de Troféus; mensagens {msgs}"
        assert self._rom_text("Route23_FamiliaSombra_6F_Text_RosaPesadelo") in msgs, msgs
        assert self.box.familia_estado()[:2] == (4, ESTADO_ENCERRADA), self.box.familia_estado()
        return (f"bolso com {slots} itens-chave: FLAG_FAMILIA_ROSA_4 ligada, rosa fora da bolsa, fala {want[:40]!r}…; "
                "ENCERRADA")

    def _redomas_completas(self) -> str:
        """Com as 4 flags de rosa, a Sala de Troféus acende as 4 redomas (vermelha, dourada, azul e negra), cada uma no
        seu lugar. A tela `sala_trofeus_completa` fica gravada."""
        self._restore("familia_base")
        for n in range(1, 5):
            self.box.set_flag(self._flag(f"FLAG_FAMILIA_ROSA_{n}"), True)
        self._warp("MAP_SEVEN_ISLAND_UNUSED_HOUSE", (3, 6))
        self.emu.frames(30)
        base = self._sym("gObjectEvents")
        objs = {}
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            if self.emu.read_u8(addr) & 1 and not self.emu.read_u8(addr + 2) & 1:       # active, não é o jogador
                xy = (self.emu.read_u16(addr + OBJECT_EVENT_XY) - MAP_OFFSET,
                      self.emu.read_u16(addr + OBJECT_EVENT_XY + 2) - MAP_OFFSET)
                objs[xy] = self.emu.read_u8(addr + OBJECT_EVENT_GFX)
        cores = ("VERMELHA", "DOURADA", "AZUL", "NEGRA")
        achadas = [objs.get(xy) for xy in SALA_REDOMAS]
        want = [self.gfx[f"OBJ_EVENT_GFX_REDOMA_{c}"] for c in cores]
        assert achadas == want, f"redomas {achadas}, esperava {want} ({cores})"
        shot = self._shot("sala_trofeus_completa")
        return f"as 4 redomas acesas {list(cores)} em {SALA_REDOMAS}; tela {shot}"

    # --- POK-54, Task 9: o dossiê do caso -------------------------------------------------------------------------
    def _dossie_abrir(self, what: str) -> dict:
        """Abre o dossiê pelo special de verdade (script de campo) e espera a tela pronta para o input."""
        self._settle(f"antes do dossiê: {what}")
        self.box.dossie_abrir()
        self.ctl.wait_until(lambda: (e := self.box.dossie_estado()) is not None and e["pronta"],
                            DOSSIE_PRONTO_TIMEOUT, f"dossiê pronto: {what}")
        self.emu.frames(4)
        return self.box.dossie_estado()

    def _dossie_tecla(self, key: int) -> dict | None:
        self.emu.press(key, **DOSSIE_TECLA)
        return self.box.dossie_estado()

    def _dossie_fechou(self, what: str) -> None:
        self.ctl.wait_until(lambda: self.box.dossie_estado() is None, DOSSIE_PRONTO_TIMEOUT, f"dossiê fechado: {what}")
        self.ctl.wait_overworld_idle(600)
        self.ctl.wait_until(lambda: not self._fade_active(), 300, f"campo de volta: {what}")

    def _dossie_navegacao(self) -> str:
        """→ avança, ← volta, ← na capa não muda, A até o fim e A na última página fecha (o jogo volta ao campo e o
        script continua); de novo, B na 3ª página fecha."""
        chefes = dossie_chefes()
        self._restore("familia_base")
        self._settle("antes do dossiê")
        musica_do_mapa = self._bgm_header()
        assert not self._bgm_is(DOSSIE_MUSICA), "o mapa de teste já toca a música do dossiê"
        e = self._dossie_abrir("navegação")
        assert (e["pagina"], e["total"], e["chefe"]) == (0, len(chefes), DOSSIE_CAPA), e
        assert self._bgm_is(DOSSIE_MUSICA), "o dossiê não tocou a música dele"
        shots = [self._shot("dossie_capa")]
        assert self._dossie_tecla(KEY_RIGHT)["pagina"] == 1
        assert self._dossie_tecla(KEY_LEFT)["pagina"] == 0
        assert self._dossie_tecla(KEY_LEFT)["pagina"] == 0, "← na capa mudou a página"
        vistos = [DOSSIE_CAPA]
        for pagina in range(1, len(chefes)):
            e = self._dossie_tecla(KEY_A)
            assert e is not None and e["pagina"] == pagina, (pagina, e)
            vistos.append(e["chefe"])
        assert vistos == chefes, (vistos, chefes)
        self.emu.frames(4)
        shots.append(self._shot("dossie_depois"))
        assert self._dossie_tecla(KEY_RIGHT)["pagina"] == len(chefes) - 1, "→ na última página saiu dela"
        self.emu.press(KEY_A, **DOSSIE_TECLA)
        self._dossie_fechou("A na última página")
        assert not self.ctl.script_active(), "o script do dossiê não terminou"
        self.emu.frames(DOSSIE_MUSICA_ASSENTA)
        assert self._bgm_header() == musica_do_mapa and not self._bgm_is(DOSSIE_MUSICA), (
            "a música do dossiê continuou no campo depois de fechar")
        e = self._dossie_abrir("de novo")
        assert e["pagina"] == 0, e
        self._dossie_tecla(KEY_RIGHT)
        assert self._dossie_tecla(KEY_RIGHT)["pagina"] == 2
        self.emu.press(KEY_B, **DOSSIE_TECLA)
        self._dossie_fechou("B na 3ª página")
        return (f"{len(chefes)} páginas, chefes {vistos}; {DOSSIE_MUSICA} no dossiê e a do mapa de volta no campo; "
                f"A na última e B na 3ª fecham; telas {shots}")

    def _dossie_carimbos(self) -> str:
        """Rosas 1-4 ligadas e só FLAG_FAMILIA_CAPTURADO_3: DERROTADO nas fichas 1, 2 e 4, CAPTURADO na 3, nada na
        capa e no Depois."""
        chefes = dossie_chefes()
        self._restore("familia_base")
        for n in range(1, 5):
            self.box.set_flag(self._flag(f"FLAG_FAMILIA_ROSA_{n}"), True)
            self.box.set_flag(self._flag(f"FLAG_FAMILIA_CAPTURADO_{n}"), n == 3)
        want = {DOSSIE_CAPA: CARIMBO_NENHUM, 1: CARIMBO_DERROTADO, 2: CARIMBO_DERROTADO, 3: CARIMBO_CAPTURADO,
                4: CARIMBO_DERROTADO, DOSSIE_DEPOIS: CARIMBO_NENHUM}
        e = self._dossie_abrir("carimbos")
        vistos, shots = [], []
        for pagina, chefe in enumerate(chefes):
            if pagina:
                e = self._dossie_tecla(KEY_RIGHT)
            assert (e["pagina"], e["chefe"]) == (pagina, chefe), (pagina, e)
            assert e["carimbo"] == want[chefe], f"página {pagina} (chefe {chefe}): carimbo {e['carimbo']}"
            vistos.append(e["carimbo"])
            primeira = chefe not in chefes[:pagina]
            if primeira and chefe in (1, 3):
                self.emu.frames(4)
                shots.append(self._shot("dossie_ficha_dom" if chefe == 1 else "dossie_ficha_mercenario_capturado"))
        self.emu.press(KEY_B, **DOSSIE_TECLA)
        self._dossie_fechou("carimbos")
        return f"carimbos por página {vistos}; telas {shots}"

    # --- POK-54, Task 10: a polícia na porta, a Oficial Jenny e a entrega dos chefes apreendidos --------------------
    def _flags_do_fim(self, capturados: tuple[int, ...] = (), cena: bool = False) -> None:
        """As 4 rosas (os 4 chefes caíram), a captura só dos chefes de `capturados` e as flags da Jenny zeradas
        (a da cena fica ligada com `cena`)."""
        for n in range(1, 5):
            self.box.set_flag(self._flag(f"FLAG_FAMILIA_ROSA_{n}"), True)
            self.box.set_flag(self._flag(f"FLAG_FAMILIA_CAPTURADO_{n}"), n in capturados)
        self.box.set_flag(self._flag("FLAG_FAMILIA_POLICIA_CENA"), cena)
        for n in (3, 4):
            self.box.set_flag(self._flag(f"FLAG_FAMILIA_ENTREGUE_{n}"), False)

    def _time_com(self, n: int) -> None:
        """Completa o time (Mewtwo e Snorlax da base) com Pidgey nv 5 até `n` Pokémon."""
        for slot in range(len(self.game.party()), n):
            self.box.set_party_mon(slot, self._sp("PIDGEY"), 5)
        assert len(self.game.party()) == n, len(self.game.party())

    def _prep_fim(self, capturados: tuple[int, ...] = (), time: int = 5, pc_cheio: bool = False,
                  cena: bool = False) -> None:
        """ENCERRADA (ocupação 4, o Pesadelo caiu), o time com `time` Pokémon e o PC cheio ou não."""
        self._restore("familia_base")
        self.box.familia_set(4, ESTADO_ENCERRADA, QUEDA_FIM)
        self._flags_do_fim(capturados, cena)
        self._time_com(time)
        if pc_cheio:
            assert self.box.fill_pc() > 0

    def _sair_encerrada(self) -> None:
        """Pelo tapete do 1º andar até a Rota 23 (a porta lacrada não tem animação: o jogador chega em cima dela e a
        cena da Jenny, se for a hora, já começa)."""
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        group, num = self.consts.map("MAP_ROUTE23")
        self.emu.keys(KEY_DOWN)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "saída do prédio")
        self.emu.keys(0)

    def _mon_apreendido(self, mon, ocupacao: int, nivel: bool = True) -> str:
        """O Pokémon entregue é o chefe da tabela: shiny, sem item, os golpes dele (e o nível, se está no time)."""
        especie, lv, _item, golpes = chefe_da_tabela(ocupacao)
        assert mon.species == self._sp(especie), (mon.species, especie)
        assert mon.is_shiny, f"{especie} entregue sem ser shiny: pid {mon.personality:#x}, OT {mon.ot_id:#x}"
        assert mon.held_item == 0, f"{especie} entregue com o item {mon.held_item}"
        assert mon.moves == [self.moves[f"MOVE_{m}"] for m in golpes], (mon.moves, golpes)
        if nivel:
            assert mon.level == lv, f"{especie} nv {mon.level}, esperava {lv}"
        return f"{especie} shiny{f' nv {lv}' if nivel else ''}, sem item, golpes {golpes}"

    def _no_pc(self, especie: str) -> list:
        return [m for box in range(TOTAL_BOXES) for m in self.game.box_mons(box) if m and m.species == self._sp(especie)]

    def _entregues(self) -> tuple[bool, bool]:
        return (self.game.flag(self._flag("FLAG_FAMILIA_ENTREGUE_3")),
                self.game.flag(self._flag("FLAG_FAMILIA_ENTREGUE_4")))

    def _jenny_cena(self, quer_ouvir: bool = False, shot: tuple[str, str] | None = None) -> dict:
        """Roda a cena da Jenny (ou a conversa com ela) até soltar o jogador. A avança as falas; a pergunta do dossiê
        recebe A (sim, e o dossiê abre: B o fecha) ou B (não). `shot` = (trecho, tela): foto quando o trecho está na
        caixa, já impresso e esperando o botão."""
        info = {"msgs": [], "perguntas": 0, "dossie": None}
        gastos, taken, na_pergunta = 0, False, False
        while not (self.ctl.overworld_idle() and info["msgs"]):
            if gastos > 8000:
                raise self.ctl.timeout_error(f"cena da Jenny; mensagens {info['msgs']}")
            estado = self.box.dossie_estado() if info["perguntas"] and quer_ouvir else None
            msg = self._message()
            if self.ctl.script_active() and msg and (not info["msgs"] or info["msgs"][-1] != msg):
                info["msgs"].append(msg)
                if "jenny_xy" not in info and msg == self._rom_text("Route23_Text_JennyCaso"):
                    info["jenny_xy"] = self._object_xy(LOCALID_JENNY)      # onde ela está quando a 1ª fala abre
            if shot and not taken and shot[0] in msg and self.ctl.script_active():
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, f"texto {shot[0]!r}")
                info["shot"] = self._shot(shot[1])
                taken = True
            if estado is not None:
                if estado["pronta"]:
                    info["dossie"] = estado
                    self.emu.press(KEY_B, **DOSSIE_TECLA)
                    self._dossie_fechou("dossiê da Jenny")
                else:
                    self.emu.frames(4)
                gastos += 10
            elif YESNO_TASK in self._tasks():
                if not na_pergunta:                       # a tarefa leva uns quadros para sumir depois do botão
                    info["perguntas"] += 1
                    na_pergunta = True
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, "pergunta do dossiê")
                self.emu.press(KEY_A if quer_ouvir else KEY_B, hold=2, release=8)
                gastos += 10
            elif self.ctl.script_active():
                na_pergunta = False
                self.emu.press(KEY_A, hold=2, release=8)
                gastos += 10
            else:
                self.emu.frames(4)
                gastos += 4
        self.emu.frames(10)
        return info

    def _falar_com(self, local_xy: tuple[int, int], direcao: str) -> None:
        """Anda até `local_xy` e olha para `direcao` (o tile vizinho tem NPC: o botão só vira o jogador); A abre a fala."""
        assert self.nav.walk_to(*local_xy), f"não chegou a {local_xy}: {self.game.player_xy()}"
        tecla = {"left": KEY_LEFT, "right": KEY_RIGHT, "up": KEY_UP, "down": KEY_DOWN}[direcao]
        for _ in range(2):          # o 1º toque vira o jogador; o 2º esbarra no NPC (nunca anda: o tile está ocupado)
            self.emu.press(tecla, hold=2, release=10)
        assert self.game.player_xy() == local_xy, f"andou em vez de virar: {self.game.player_xy()}"
        self.ctl.press_until(KEY_A, self.ctl.script_active, f"fala de {direcao} de {local_xy}", tries=6)

    def _esperar_cena(self) -> None:
        """Depois de sair do prédio: a polícia no mapa e o script da cena já rodando."""
        self.ctl.wait_until(lambda: LOCALID_JENNY in self._active_objects() and self.ctl.script_active(), 600,
                            "a cena da Jenny ao sair do prédio")

    def _posto_da_policia(self, jenny_no_posto: bool = True) -> dict:
        """Onde está cada um da polícia: todos no mapa, nos tiles do map.json (a Jenny, só se `jenny_no_posto`)."""
        ativos = self._active_objects()
        esperado = {LOCALID_JENNY: JENNY_POSTO, LOCALID_POLICIAL_1: (3, 150), LOCALID_POLICIAL_2: (5, 150),
                    LOCALID_GROWLITHE: (3, 151), LOCALID_ARCANINE: (7, 150)}
        for local, xy in esperado.items():
            assert local in ativos and self._object_visible(local), f"objeto {local} fora do mapa: {ativos}"
            if local != LOCALID_JENNY or jenny_no_posto:
                assert self._object_xy(local) == xy, (local, self._object_xy(local), xy)
        assert self._object_gfx(LOCALID_JENNY) == self.gfx["OBJ_EVENT_GFX_OFICIAL_JENNY"]
        assert self._object_gfx(LOCALID_GROWLITHE) == self.gfx["OBJ_EVENT_GFX_POLICIA_GROWLITHE"]
        assert self._object_gfx(LOCALID_ARCANINE) == self.gfx["OBJ_EVENT_GFX_POLICIA_ARCANINE"]
        assert self._object_gfx(LOCALID_POLICIAL_1) == self._object_gfx(LOCALID_POLICIAL_2) == self.gfx["OBJ_EVENT_GFX_POLICEMAN"]
        return esperado

    def _cena_jenny(self) -> str:
        """Nada capturado, 5 no time. Saindo do prédio a cena começa: a Jenny vem até o jogador, entrega o Garchomp (vai
        para o time, que fica com 6) e o Darkrai (time cheio: vai para o PC), ambos shiny, no nível da luta, sem item e
        com os golpes do chefe. A pergunta do dossiê vem e "Não" só agradece. As 3 flags ficam ligadas."""
        self._prep_fim(time=5)
        assert not self.game.flag(self._flag("FLAG_FAMILIA_POLICIA_CENA"))
        self._sair_encerrada()
        self._esperar_cena()
        self._posto_da_policia(jenny_no_posto=False)       # a cena já pode ter começado: ela anda
        assert self.game.player_xy() == PORTA, self.game.player_xy()
        info = self._jenny_cena(quer_ouvir=False, shot=("Oficial Jenny: Um momento!", "familia_jenny_cena"))
        msgs = info["msgs"]
        junto = " ".join(" ".join(msgs).split())
        nome = self.game.player_name()
        for rotulo in ("Route23_Text_JennyCaso", "Route23_Text_JennyApreendido3", "Route23_Text_JennyApreendido4",
                       "Route23_Text_JennyQuerOuvir", "Route23_Text_JennyObrigada"):
            assert self._rom_text(rotulo) in msgs, (rotulo, msgs)
        assert f"{nome} recebeu GARCHOMP!" in junto and "DARKRAI foi transferido para o PC" in junto, junto
        assert "Caixa “" in junto, junto         # o aviso do PC diz a caixa, no padrão do jogo
        assert info["jenny_xy"] == (4, 150), f"a fala abriu com a Jenny em {info['jenny_xy']} (ela ainda andava)"
        assert msgs.index(self._rom_text("Route23_Text_JennyApreendido3")) < msgs.index(
            self._rom_text("Route23_Text_JennyApreendido4")) < msgs.index(self._rom_text("Route23_Text_JennyQuerOuvir"))
        assert info["perguntas"] == 1 and info["dossie"] is None
        party = self.game.party()
        assert len(party) == 6 and party[5].species == self._sp("GARCHOMP"), [m.species for m in party]
        feito = [self._mon_apreendido(party[5], 3)]
        no_pc = self._no_pc("DARKRAI")
        assert len(no_pc) == 1 and not self._no_pc("GARCHOMP"), (len(no_pc), len(self._no_pc("GARCHOMP")))
        feito.append(self._mon_apreendido(no_pc[0], 4, nivel=False) + " no PC")
        assert [m.species for m in party[:5]] == [self._sp("MEWTWO"), self._sp("SNORLAX")] + [self._sp("PIDGEY")] * 3
        assert self.game.flag(self._flag("FLAG_FAMILIA_POLICIA_CENA")) and self._entregues() == (True, True), \
            self._entregues()
        for especie in ("GARCHOMP", "DARKRAI"):       # visto e capturado na Dex (as 2 últimas posições do atalho)
            dex = self.box.dex_info(self._sp(especie))[0]
            assert self.box.dex_completa(dex)[2:] == (True, True), especie
        # a Jenny volta ao posto e libera a porta: o jogador não fica preso
        assert self._object_xy(LOCALID_JENNY) == JENNY_POSTO, self._object_xy(LOCALID_JENNY)
        self.ctl.checkpoint("jenny_fim")
        assert self.nav.step("down", 2) == 2 and self.game.player_xy() == (4, 151), self.game.player_xy()
        assert self.nav.walk_to(8, 151) and self.nav.walk_to(*PORTA_FRENTE), "o jogador ficou preso na porta"
        return f"{'; '.join(feito)}; flags ligadas; tela {info['shot']}"

    def _livre_da_porta(self) -> None:
        """O jogador que acabou a cena sai de verdade: desce pela saída entre os policiais e volta."""
        xy = self.game.player_xy()
        assert xy in (PORTA, PORTA_FRENTE), xy
        assert self.nav.step("down", 151 - xy[1]) == 151 - xy[1] and self.game.player_xy() == (4, 151), \
            self.game.player_xy()
        assert self.nav.walk_to(8, 151) and self.nav.walk_to(*PORTA_FRENTE), "o jogador ficou preso na porta"

    def _cena_jenny_sim(self) -> str:
        """Nada a entregar (os 2 capturados) e a resposta é Sim: o dossiê abre no meio da cena (capa, B fecha), a Jenny
        volta ao posto e o jogador sai livre da porta."""
        self._prep_fim(capturados=(3, 4), time=3)
        self._sair_encerrada()
        self._esperar_cena()
        info = self._jenny_cena(quer_ouvir=True)
        msgs = info["msgs"]
        assert msgs[-2:] == [self._rom_text("Route23_Text_JennyCaso"), self._rom_text("Route23_Text_JennyQuerOuvir")], msgs
        assert not any("Apreendido" in m or "recebeu" in m for m in msgs), msgs
        assert info["jenny_xy"] == (4, 150), info["jenny_xy"]
        assert info["dossie"] is not None and info["dossie"]["chefe"] == DOSSIE_CAPA, info["dossie"]
        assert not self.ctl.script_active() and self.box.dossie_estado() is None
        assert self.game.flag(self._flag("FLAG_FAMILIA_POLICIA_CENA")) and self._entregues() == (False, False)
        assert self._object_xy(LOCALID_JENNY) == JENNY_POSTO, self._object_xy(LOCALID_JENNY)
        assert len(self.game.party()) == 3
        self._livre_da_porta()
        return "Sim: dossiê aberto no meio da cena (capa) e fechado com B; a Jenny volta ao posto; o jogador sai da porta"

    def _usar_corda_de_fuga(self) -> None:
        """START > BOLSA > Corda de Fuga > USAR, de verdade, e conduz a mensagem e o warp até a Rota 23."""
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_BAG)
        self.menu.bag.wait_ready()
        self.menu.bag.select(self.consts.item("ITEM_ESCAPE_ROPE"))
        self.menu.bag.use_selected()
        group, num = self.consts.map("MAP_ROUTE23")
        gastos = 0
        while self.game.location() != (group, num):
            if gastos > 3000:
                raise self.ctl.timeout_error("Corda de Fuga até a Rota 23")
            self.emu.press(KEY_A, hold=2, release=18)
            gastos += 20

    def _cena_jenny_corda(self) -> str:
        """Corda de Fuga de verdade, de dentro do prédio (1º andar), com a Família já encerrada: o escape warp gravado ao
        entrar pela porta ((4, 149), y >= 128) leva o jogador para (4, 150), à frente dela; a Jenny para em (4, 151) e
        fala olhando para cima, nunca em cima dele; no fim volta ao posto e o jogador sai livre. (Antes os parâmetros de
        SetEscapeWarp eram s8: y = 150 virava -106 e a Corda deixava o jogador no meio da Rota 23.)"""
        self._restore("familia_base")
        self.box.set_flag(self._flag("FLAG_BADGE08_GET"), True)
        self.box.familia_set(1, ESTADO_ATIVA)
        self._sair_do_predio()                          # a porta real (ainda aberta): (4, 150), de frente para ela
        self.nav.go_through_warp("up")                  # entrar grava o escape warp (UpdateEscapeWarp)
        assert self._at("MAP_ROUTE23_UNUSED_HOUSE"), self.game.location()
        escape = self.emu.read(self.emu.read_u32(self._sym("gSaveBlock1Ptr")) + SB1_ESCAPE_WARP, 8)
        assert (escape[0], escape[1]) == self.consts.map("MAP_ROUTE23"), escape.hex()
        x, y = int.from_bytes(escape[4:6], "little", signed=True), int.from_bytes(escape[6:8], "little", signed=True)
        assert (x, y) == PORTA_FRENTE, f"escape warp gravado em {(x, y)}: as coordenadas ainda truncam em 8 bits"
        # a Família termina por dentro: o prédio fecha e a Jenny chega
        self.box.familia_set(4, ESTADO_ENCERRADA, QUEDA_FIM)
        self._flags_do_fim(capturados=(3, 4))
        self._time_com(3)
        assert self.box.call(CMD_GIVE_ITEM, self.consts.item("ITEM_ESCAPE_ROPE"), 1) == 1
        self._usar_corda_de_fuga()
        self._esperar_cena()
        assert self.game.player_xy() == PORTA_FRENTE, f"a Corda deixou o jogador em {self.game.player_xy()}"
        assert self.game.bag_quantity(self.consts.item("ITEM_ESCAPE_ROPE")) == 0, "a corda não foi gasta"
        info = self._jenny_cena(quer_ouvir=False)
        assert info["jenny_xy"] == (4, 151), f"a Jenny abriu a fala em {info['jenny_xy']}"
        assert info["msgs"][-1] == self._rom_text("Route23_Text_JennyObrigada"), info["msgs"]
        assert self.game.flag(self._flag("FLAG_FAMILIA_POLICIA_CENA"))
        assert self._object_xy(LOCALID_JENNY) == JENNY_POSTO, self._object_xy(LOCALID_JENNY)
        self._livre_da_porta()
        return ("Corda de Fuga pela bolsa: escape warp (4, 150) gravado, o jogador chega em (4, 150); a Jenny parou em "
                "(4, 151), voltou ao posto e ele saiu livre")

    def _jenny_de_novo(self) -> str:
        """Falando com a Jenny depois da cena: a fala dela, nenhuma entrega repetida e a pergunta; "Sim" abre o
        dossiê (o estado vira != 0xFFFFFFFF, capa) e B volta ao campo. De novo, "Não" só agradece."""
        self._restore("jenny_fim")
        antes = [(m.species, m.personality) for m in self.game.party()]
        self._falar_com(JENNY_DE_FRENTE, "up")
        info = self._jenny_cena(quer_ouvir=True)
        msgs = info["msgs"]
        assert msgs[0] == self._rom_text("Route23_Text_JennyDeNovo") and msgs[-1] == self._rom_text(
            "Route23_Text_JennyQuerOuvir"), msgs
        assert len(msgs) == 2, f"entrega repetida: {msgs}"
        assert info["dossie"] is not None and info["dossie"]["chefe"] == DOSSIE_CAPA and info["dossie"]["pagina"] == 0, info
        assert not self.ctl.script_active() and self.box.dossie_estado() is None
        assert [(m.species, m.personality) for m in self.game.party()] == antes and not self._no_pc("GARCHOMP")
        assert self._entregues() == (True, True)
        self._falar_com(JENNY_DE_FRENTE, "up")
        info = self._jenny_cena(quer_ouvir=False)
        assert info["msgs"][-1] == self._rom_text("Route23_Text_JennyObrigada") and info["dossie"] is None, info["msgs"]
        # o carimbo do Garchomp entregue continua DERROTADO (a entrega não é captura)
        e = self._dossie_abrir("carimbo do chefe entregue")
        while e["chefe"] != 3:
            e = self._dossie_tecla(KEY_RIGHT)
        assert e["carimbo"] == CARIMBO_DERROTADO, e
        self.emu.press(KEY_B, **DOSSIE_TECLA)
        self._dossie_fechou("carimbo do entregue")
        return ("fala, pergunta, sim: dossiê na capa e B volta ao campo; de novo, não: agradece; nada entregue duas "
                "vezes; o carimbo do Garchomp entregue segue DERROTADO")

    def _entrega_capturado(self) -> str:
        """Com o Garchomp capturado (FLAG_FAMILIA_CAPTURADO_3), só o Darkrai é entregue: vai para o time."""
        self._prep_fim(capturados=(3,), time=3)
        self._sair_encerrada()
        self._esperar_cena()
        info = self._jenny_cena()
        junto = " ".join(" ".join(info["msgs"]).split())
        assert self._rom_text("Route23_Text_JennyApreendido4") in info["msgs"], info["msgs"]
        assert self._rom_text("Route23_Text_JennyApreendido3") not in info["msgs"], info["msgs"]
        assert f"{self.game.player_name()} recebeu DARKRAI!" in junto and "GARCHOMP" not in junto.replace(
            "DARKRAI", ""), junto
        party = self.game.party()
        assert [m.species for m in party] == [self._sp("MEWTWO"), self._sp("SNORLAX"), self._sp("PIDGEY"),
                                              self._sp("DARKRAI")], [m.species for m in party]
        feito = self._mon_apreendido(party[3], 4)
        assert not self._no_pc("GARCHOMP") and not self._no_pc("DARKRAI")
        assert self._entregues() == (False, True) and self.game.flag(self._flag("FLAG_FAMILIA_CAPTURADO_3"))
        return f"{feito}; o Garchomp capturado não é entregue; ENTREGUE (3, 4) = {self._entregues()}"

    def _entrega_time_cheio(self) -> str:
        """Com 6 no time os dois vão ao PC e a Jenny avisa; o time fica como estava."""
        self._prep_fim(time=6)
        antes = [(m.species, m.personality) for m in self.game.party()]
        self._sair_encerrada()
        self._esperar_cena()
        info = self._jenny_cena()
        junto = " ".join(" ".join(info["msgs"]).split())
        assert junto.count("foi transferido para o PC") == 2 and "GARCHOMP foi transferido para o PC" in junto and \
            "DARKRAI foi transferido para o PC" in junto and "recebeu" not in junto, junto
        assert junto.count("Caixa “") == 2 and "estava cheia" not in junto, junto
        assert [(m.species, m.personality) for m in self.game.party()] == antes
        garchomp, darkrai = self._no_pc("GARCHOMP"), self._no_pc("DARKRAI")
        assert len(garchomp) == 1 and len(darkrai) == 1
        feito = [self._mon_apreendido(garchomp[0], 3, nivel=False), self._mon_apreendido(darkrai[0], 4, nivel=False)]
        assert self._entregues() == (True, True)
        return f"time cheio: {feito} no PC, com o aviso; time intacto"

    def _entrega_pc_cheio(self) -> str:
        """Time e PC cheios: nada é entregue, as flags ENTREGUE ficam desligadas e a Jenny pede espaço (a cena acaba
        e a flag dela liga). Com 2 vagas no time e conversando de novo, a entrega acontece."""
        self._prep_fim(time=6, pc_cheio=True)
        self.box.conq_reset(True)                   # liga as conquistas (o contador de shinies só conta com o marcador)
        shinies = self.box.conq_contador(1)
        self._sair_encerrada()
        self._esperar_cena()
        info = self._jenny_cena()
        assert self._rom_text("Route23_Text_JennySemEspaco") in info["msgs"], info["msgs"]
        assert not any("recebeu" in m or "transferido" in m for m in info["msgs"]), info["msgs"]
        assert info["msgs"].count(self._rom_text("Route23_Text_JennySemEspaco")) == 1, "o laço não parou"
        assert not self._no_pc("GARCHOMP") and not self._no_pc("DARKRAI") and len(self.game.party()) == 6
        assert not any(m.species in (self._sp("GARCHOMP"), self._sp("DARKRAI")) for m in self.game.party())
        assert self._entregues() == (False, False), "a flag ligou sem entregar"
        assert self.game.flag(self._flag("FLAG_FAMILIA_POLICIA_CENA")), "a cena acabou"
        assert self._rom_text("Route23_Text_JennyObrigada") in info["msgs"]
        # tudo cheio e conversando várias vezes: nada é dado, e o Garchomp shiny que não saiu não conta como recebido
        for _ in range(3):
            self._falar_com(JENNY_DE_FRENTE, "up")
            outra = self._jenny_cena()
            assert self._rom_text("Route23_Text_JennySemEspaco") in outra["msgs"], outra["msgs"]
        assert self.box.conq_contador(1) == shinies, f"shiniesObtidos {shinies} -> {self.box.conq_contador(1)}"
        assert self._entregues() == (False, False) and len(self.game.party()) == 6
        # abre 2 vagas no time e fala de novo: a entrega acontece
        assert self.box.party_size(4) == 4
        self._falar_com(JENNY_DE_FRENTE, "up")
        info = self._jenny_cena()
        junto = " ".join(" ".join(info["msgs"]).split())
        assert f"{self.game.player_name()} recebeu GARCHOMP!" in junto and f"{self.game.player_name()} recebeu DARKRAI!" in junto, junto
        assert info["msgs"][0] == self._rom_text("Route23_Text_JennyDeNovo")
        assert [m.species for m in self.game.party()[4:]] == [self._sp("GARCHOMP"), self._sp("DARKRAI")]
        assert self._entregues() == (True, True)
        assert self.box.conq_contador(1) == shinies + 2, "os 2 recebidos de verdade contam"
        return ("PC e time cheios: nada entregue, flags desligadas, a Jenny pede espaço; 4 conversas com tudo cheio não "
                "somam shinies; com 2 vagas, falando de novo, os 2 chegam ao time (e contam)")

    def _entrega_caixa_cheia(self) -> str:
        """Time cheio e a caixa atual (a 1) também: o Garchomp e o Darkrai vão para a caixa 2 e o aviso diz a caixa que
        estava cheia, no padrão do jogo."""
        self._prep_fim(time=6)
        for pos in range(30):
            self.box.conq_pc_mon(0, pos, self._sp("PIDGEY"))
        self._sair_encerrada()
        self._esperar_cena()
        info = self._jenny_cena()
        junto = " ".join(" ".join(info["msgs"]).split())
        assert junto.count("estava cheia") == 1 and junto.count("foi transferido para") == 2, junto
        assert self._no_pc("GARCHOMP") and self._no_pc("DARKRAI")
        boxes = [i for i in range(TOTAL_BOXES) for m in self.game.box_mons(i) if m and m.species in (
            self._sp("GARCHOMP"), self._sp("DARKRAI"))]
        assert boxes == [1, 1], boxes
        assert self._entregues() == (True, True)
        return f"caixa 1 cheia: os dois na caixa 2; aviso com a caixa cheia: {junto[junto.index('A Caixa'):][:60]!r}"

    def _porta_lacrada(self) -> str:
        """Com a Família encerrada o metatile da porta é o das faixas amarelas: a porta não abre (nem andando para
        cima), a placa fala da polícia, não há cobrador nem pedágio armado e o 1º andar não tem capangas."""
        self._restore("jenny_fim")
        lacrada = json.loads(PREDIO_JSON.read_text(encoding="utf-8"))["indigo_plateau"]["porta_lacrada"]
        assert self._metatile(*PORTA) == lacrada & 0x3FF, f"metatile da porta {self._metatile(*PORTA):#x}"
        assert not self._object_visible(LOCALID_COBRADOR) and self._var(VAR_TEMP_3) == 0
        self._posto_da_policia()
        self.box.set_follower_option(False)             # o Mewtwo de seguidor taparia as faixas na foto
        self.emu.frames(10)
        assert self.nav.step("down", 2) == 2 and self.game.player_xy() == (4, 151)
        self._settle("dois passos da porta lacrada")   # o passo termina na tela depois de a posição mudar
        shot = self._shot("familia_policia_porta")     # um tile mais longe: o jogador não tapa as faixas
        assert self.nav.step("up") == 1 and self.game.player_xy() == PORTA_FRENTE
        self.emu.keys(KEY_UP)
        self.emu.frames(60)
        self.emu.keys(0)
        self.emu.frames(10)
        assert self._at("MAP_ROUTE23") and self.game.player_xy() == PORTA_FRENTE, \
            f"a porta lacrada deixou passar: {self.game.location()} {self.game.player_xy()}"
        self.ctl.press_until(KEY_A, self.ctl.script_active, "placa da porta", tries=5)
        self.ctl.wait_until(self._waiting, 600, "texto da porta")
        msg = self._message()
        assert msg == self._rom_text("Route23_Text_PortaFamiliaLacrada"), msg
        self._scene(self.ctl.overworld_idle, "fim da placa")
        # o 1º andar não tem capangas nem itens de volta: o prédio está vazio
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        assert not set(self._active_objects()) & LOCALIDS_CAPANGAS_1F, self._active_objects()
        return f"porta lacrada (metatile {lacrada:#x}) não abre; placa {msg!r}; sem cobrador e sem capangas; tela {shot}"

    def _policia_ambiente(self) -> str:
        """Os policiais e o Growlithe falam, o Arcanine late (a fala e o grito)."""
        self._restore("jenny_fim")
        self._posto_da_policia()
        fala = {}
        for nome, xy, direcao, rotulo in (("policial 1", (4, 150), "left", "Route23_Text_Policial1"),
                                          ("policial 2", (4, 150), "right", "Route23_Text_Policial2"),
                                          ("growlithe", (4, 151), "left", "Route23_Text_Growlithe"),
                                          ("arcanine", (7, 151), "up", "Route23_Text_Arcanine")):
            self._falar_com(xy, direcao)
            self.ctl.wait_until(self._waiting, 600, f"fala do {nome}")
            msg = self._message()
            assert msg == self._rom_text(rotulo), (nome, msg)
            fala[nome] = msg
            self._scene(self.ctl.overworld_idle, f"fim da fala do {nome}")
        assert fala["arcanine"] == "Arcanine: Au! Au!"
        return f"falas: {fala}"

    def run(self) -> None:
        try:
            self._flow("familia: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("familia/capanga_apresentacao", self._capanga)
            self.suite.run("familia/bola_capanga", self._ball)
            self.suite.run("familia/vitoria_sem_premio", self._win)
            self.suite.run("familia/thief", self._thief)
            self.suite.run("familia/time_por_ocupacao", self._teams)
            self.suite.run("familia/gemeos_dupla", self._twins)
            self.suite.run("familia/encontro_wild", self._encontro)
            self.suite.run("familia/passos_andar_escuro", self._passos)
            self.suite.run("familia/bola_selvagem", self._wild_ball)
            self.suite.run("familia/thief_selvagem", self._wild_thief)
            self.suite.run("familia/chefe", self._chefe)
            self.suite.run("familia/bola_chefe", self._chefe_ball)
            self.suite.run("familia/chefe_ia", self._chefe_ia)
            self.suite.run("familia/porta_trancada", self._porta)
            self.suite.run("familia/ciclo", self._ciclo)
            self.suite.run("familia/capanga_ve", self._capanga_ve)
            self.suite.run("familia/subida", self._subida)
            self.suite.run("familia/encontro_andar4", self._encontro_andar4)
            self.suite.run("familia/sem_encontro_sem_chefe", self._sem_encontro)
            self.suite.run("familia/gemeos_um_pokemon", self._gemeos_um)
            self.suite.run("familia/chefe_fuga", self._chefe_fuga)
            self.suite.run("familia/rosa", self._rosa)
            self.suite.run("familia/conquista_dom", self._conquista_dom)
            self.suite.run("familia/gengar_fora_nao_conta", self._gengar_fora)
            self.suite.run("familia/pedagio_paga", self._pedagio_paga)
            self.suite.run("familia/pedagio_sem_dinheiro", self._pedagio_sem_dinheiro)
            self.suite.run("familia/pedagio_forca", self._pedagio_forca)
            self.suite.run("familia/pedagio_volta", self._pedagio_volta)
            self.suite.run("familia/pedagio_sem_chefe", self._pedagio_sem_chefe)
            self.suite.run("familia/chefe_balcao", self._chefe_balcao)
            self.suite.run("familia/rosa_bolsa_cheia", self._rosa_bolsa_cheia)
            self.suite.run("familia/continue_rota23_ativa", self._continue_ativa)
            self.suite.run("familia/continue_rota23_sem_chefe", self._continue_sem_chefe)
            self.suite.run("familia/continue_rota23_fechado", self._continue_fechado)
            self.suite.run("familia/quadro_cobrador", self._quadro_cobrador)
            self.suite.run("familia/ciclo_ate_o_fim", self._ciclo_ate_o_fim)
            self.suite.run("familia/chefe_mercenario", self._chefe_mercenario)
            self.suite.run("familia/chefe_pesadelo", self._chefe_pesadelo)
            self.suite.run("familia/captura_marca", self._captura_marca)
            self.suite.run("familia/conquistas_parte2", self._conquistas_parte2)
            self.suite.run("familia/sala_mercenario", self._sala_mercenario)
            self.suite.run("familia/sala_pesadelo", self._sala_pesadelo)
            self.suite.run("familia/rosa_azul", self._rosa_azul)
            self.suite.run("familia/rosa_negra_bolsa_cheia", self._rosa_negra_bolsa_cheia)
            self.suite.run("familia/redomas_completas", self._redomas_completas)
            self.suite.run("dossie/navegacao", self._dossie_navegacao)
            self.suite.run("dossie/carimbos", self._dossie_carimbos)
            self.suite.run("familia/cena_jenny", self._cena_jenny)
            self.suite.run("familia/jenny_de_novo", self._jenny_de_novo)
            self.suite.run("familia/entrega_capturado", self._entrega_capturado)
            self.suite.run("familia/entrega_time_cheio", self._entrega_time_cheio)
            self.suite.run("familia/entrega_pc_cheio", self._entrega_pc_cheio)
            self.suite.run("familia/entrega_caixa_cheia", self._entrega_caixa_cheia)
            self.suite.run("familia/cena_jenny_sim", self._cena_jenny_sim)
            self.suite.run("familia/cena_jenny_corda", self._cena_jenny_corda)
            self.suite.run("familia/porta_lacrada", self._porta_lacrada)
            self.suite.run("familia/policia_ambiente", self._policia_ambiente)
        except Abort:
            pass


def run_full_familia(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    FamiliaScenario(ctx_test).run()
