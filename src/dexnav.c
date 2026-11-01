#include "global.h"
#include "gflib.h"
#include "data.h"
#include "day_night.h"
#include "dexnav.h"
#include "help_system.h"
#include "menu.h"
#include "menu_helpers.h"
#include "new_menu_helpers.h"
#include "overworld.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_icon.h"
#include "quest_log.h"
#include "scanline_effect.h"
#include "script.h"
#include "strings.h"
#include "task.h"
#include "constants/songs.h"

// DexNav (POK-47), a tela: três modos no mesmo arquivo, cada um com o seu Montar*/Desenhar*/Input*, sobre a mesma
// lista rolável (linhas de tipos diferentes, seções com título fixo ao rolar, ícones de Pokémon nas linhas de 24 px).
// Desenho em docs/superpowers/specs/2026-10-31-dexnav-design.md.
//
// MODO MAPA (layout A aprovado pelo Cintra): topo com o nome do mapa, o período do dia (o nome do relógio: Manhã,
// Tarde, Entardecer, Noite) e "capturados/total" do mapa (todas as espécies, em qualquer horário), que vira "100%" com
// a coroa no mapa completo. Abas por jeito de encontrar (GRAMA, SURFAR, VARAS, PEDRA; só as que o mapa tem; L/R dão a
// volta), com a coroa na aba completa. Lista da aba: os Pokémon do período de agora, por chance (maior primeiro), cada
// linha com o ícone (silhueta se nunca visto), a marca (capturado, visto, nunca visto), o nome ("??????" se nunca
// visto), a chance e a faixa de nível, em colunas fixas (COL_*). VARAS tem uma seção por vara. No fim da aba, "+N à
// noite" (ou de dia, de manhã...) quando outro período tem espécies que não aparecem agora.
//
// MODO LISTA (SELECT): todos os mapas com encontro da região (abas KANTO e SEVII, L/R), cada linha com o nome, a barra
// de progresso, "capturados/total" (ou a coroa e "100%") em colunas fixas (LST_*); o topo diz quantos mapas da região
// estão completos. Mapa ainda não visitado: "?/?", barra vazia, e A não abre (sem estragar surpresa). A abre o modo
// mapa do mapa escolhido. Abre no mapa da tela de onde se veio (ou no mapa atual / no último com encontro visitado).
//
// MODO BUSCA (START): passo 1, a lista das espécies vistas na Pokédex que aparecem em algum mapa (ordem da Pokédex
// Nacional; ícone, marca, número, nome e em quantos mapas aparece; L/R pulam uma página). Passo 2, os mapas onde a
// espécie aparece, em seções por jeito de encontrar (Grama, Surfar, as varas, Esmaga Pedra), cada linha com o mapa, a
// chance e o horário (RES_*); mapa não visitado vira "??????" e A não abre. A abre o modo mapa daquele mapa, na aba do
// jeito e na linha da espécie.
//
// Navegação: SELECT e START trocam de modo (se a tela pedida já está na pilha, volta até ela); A empilha a tela de
// agora e abre a outra; B volta uma tela (sai do DexNav na primeira). Nunca passa de PILHA_MAX telas empilhadas.
//
// A tarde-noite (TIME_EVENING) vale como tarde e noite ao mesmo tempo (DexNav_CurrentPeriodBit devolve os 2 bits): a
// lista mostra as espécies das duas tabelas e a chance é a média (DexNav_RateForPeriods), como o encontro real.
//
// Memória: o estado num bloco AllocZeroed (sDexNav é o único EWRAM novo: EWRAM ~99,6%), liberado na saída. A ajuda do
// jogo (que também escuta L/R) fica desligada enquanto a tela está aberta. A lista e a busca precisam passar pelos 124
// mapas (DexNav_GetMapEntries): a varredura é feita em partes de VARRER_POR_QUADRO mapas por quadro e o resultado fica
// no bloco (contagens por mapa e por espécie uma vez por abertura; os mapas da espécie a cada busca).

// Janelas, todas no BG0 (bloco de caracteres 0, tilemap no bloco 31), uma faixa de tiles depois da outra:
//   linhas 0-1    WIN_TOPO    nome do mapa (ou título), período e contador (ou "100%") com a coroa
//   linhas 2-3    WIN_ABAS    as abas do mapa, as regiões (lista) ou os títulos das colunas (busca)
//   linhas 4-17   WIN_LISTA   LISTA_ALTURA px de linhas
//   linhas 18-19  WIN_RODAPE  os botões
#define TELA_TILES_X        (DISPLAY_WIDTH / 8)
#define TOPO_TILES          2
#define ABAS_TILES          2
#define RODAPE_TILES        2
#define LISTA_TOPO_TILES    (TOPO_TILES + ABAS_TILES)
#define LISTA_ALTURA        112
#define RODAPE_TOPO_TILES   (LISTA_TOPO_TILES + LISTA_ALTURA / 8)
STATIC_ASSERT(RODAPE_TOPO_TILES + RODAPE_TILES == DISPLAY_HEIGHT / 8, DexNavOcupaATela);

// Linhas da lista: Pokémon e espécie da busca (com o ícone de 32x32, centrado na linha), título de seção, a linha
// extra ("+N") e as linhas curtas (mapa da lista, mapa do resultado da busca).
// A lista rola quando passa de ICONES_MAX linhas com ícone: cada linha visível tem o seu sprite.
#define LINHA_MON_ALTURA    24
#define LINHA_SECAO_ALTURA  16
#define LINHA_EXTRA_ALTURA  16
#define LINHA_CURTA_ALTURA  16
#define ICONES_MAX          4
STATIC_ASSERT(ICONES_MAX * LINHA_MON_ALTURA <= LISTA_ALTURA && (ICONES_MAX + 1) * LINHA_MON_ALTURA > LISTA_ALTURA,
              DexNavIconesVisiveis);

// Colunas da linha de Pokémon, em px na janela da lista (240 px), as mesmas em todas as linhas (pedido do Cintra):
//   ícone (sprite 32x32 de COL_ICONE_X a +32), marca (8x8), nome (até COL_NOME_LARGURA: a espécie mais larga mede 60),
//   chance alinhada à direita até COL_CHANCE_FIM (até COL_CHANCE_LARGURA: "99,5%" mede 31), "Nv." em COL_NIVEL_X, o
//   nível mínimo alinhado à direita até COL_NIVEL_MIN_FIM, o traço em COL_NIVEL_TRACO_X e o máximo alinhado à esquerda
//   em COL_NIVEL_MAX_X: "3 - 4" e "25 - 35" com o traço na mesma coluna e o mesmo respiro dos dois lados (nível único:
//   só o mínimo, na coluna dele). As setas de rolagem ficam em COL_SETA_X.
// test/tests/test_dexnav_tela.py::test_colunas_fixas confere que nenhuma coluna encosta na outra no pior caso.
#define COL_ICONE_X         0
#define COL_MARCA_X         32
#define COL_NOME_X          44
#define COL_NOME_LARGURA    64
#define COL_CHANCE_FIM      150
#define COL_CHANCE_LARGURA  32
#define COL_NIVEL_X         160
#define COL_NIVEL_MIN_FIM   196
#define COL_NIVEL_TRACO_X   199
#define COL_NIVEL_MAX_X     208
#define COL_NIVEL_MAX_LARGURA 18  // "100"
#define COL_SETA_X          228
STATIC_ASSERT(COL_NOME_X + COL_NOME_LARGURA + 4 <= COL_CHANCE_FIM - COL_CHANCE_LARGURA, DexNavNomeAntesDaChance);
STATIC_ASSERT(COL_NIVEL_MAX_X + COL_NIVEL_MAX_LARGURA <= COL_SETA_X, DexNavNivelAntesDasSetas);

// Colunas da linha de mapa (lista, 16 px): nome (até DEXNAV_NAME_WIDTH), a barra de progresso (trilho de
// LST_BARRA_LARGURA px, cheia na proporção capturados/total), a coroa do mapa completo e o contador ("8/10", "100%" ou
// "?/?") alinhado à direita até LST_CONTADOR_FIM (até LST_CONTADOR_LARGURA: "99/99" mede 30).
// test_colunas_lista_fixas mede o pior caso de cada coluna.
#define LST_NOME_X          4
#define LST_BARRA_X         128
#define LST_BARRA_LARGURA   48
#define LST_BARRA_ALTURA    6
#define LST_BARRA_DY        5
#define LST_COROA_X         180
#define LST_COROA_DY        4
#define LST_CONTADOR_FIM    222
#define LST_CONTADOR_LARGURA 32
STATIC_ASSERT(LST_NOME_X + DEXNAV_NAME_WIDTH + 4 <= LST_BARRA_X, DexNavListaNomeAntesDaBarra);
STATIC_ASSERT(LST_BARRA_X + LST_BARRA_LARGURA + 4 <= LST_COROA_X, DexNavListaBarraAntesDaCoroa);
STATIC_ASSERT(LST_COROA_X + 8 + 2 <= LST_CONTADOR_FIM - LST_CONTADOR_LARGURA, DexNavListaCoroaAntesDoContador);
STATIC_ASSERT(LST_CONTADOR_FIM + 2 <= COL_SETA_X, DexNavListaContadorAntesDasSetas);
STATIC_ASSERT(LST_BARRA_DY + LST_BARRA_ALTURA <= LINHA_CURTA_ALTURA, DexNavListaBarraNaLinha);

// Colunas da escolha da busca (24 px, com ícone): ícone e marca nas colunas do modo mapa, o número da Pokédex
// Nacional alinhado à direita até ESC_NUM_FIM ("386" mede 18), o nome em ESC_NOME_X (até COL_NOME_LARGURA) e em
// quantos mapas a espécie aparece, alinhado à direita até ESC_MAPAS_FIM (até ESC_MAPAS_LARGURA: "Mapas" mede 29).
#define ESC_NUM_FIM         62
#define ESC_NUM_LARGURA     18
#define ESC_NOME_X          68
#define ESC_MAPAS_FIM       172
#define ESC_MAPAS_LARGURA   30
STATIC_ASSERT(COL_MARCA_X + 8 + 4 <= ESC_NUM_FIM - ESC_NUM_LARGURA, DexNavEscolhaMarcaAntesDoNumero);
STATIC_ASSERT(ESC_NUM_FIM + 4 <= ESC_NOME_X, DexNavEscolhaNumeroAntesDoNome);
STATIC_ASSERT(ESC_NOME_X + COL_NOME_LARGURA + 4 <= ESC_MAPAS_FIM - ESC_MAPAS_LARGURA, DexNavEscolhaNomeAntesDosMapas);
STATIC_ASSERT(ESC_MAPAS_FIM + 2 <= COL_SETA_X, DexNavEscolhaMapasAntesDasSetas);

// Colunas do resultado da busca (16 px): o mapa (até DEXNAV_NAME_WIDTH), a chance alinhada à direita até
// RES_CHANCE_FIM (até COL_CHANCE_LARGURA) e o horário em RES_HORARIO_X (até RES_HORARIO_LARGURA: "manhã/noite" mede
// 61). Os títulos das colunas (WIN_ABAS) usam as mesmas constantes.
#define RES_NOME_X          4
#define RES_CHANCE_FIM      158
#define RES_HORARIO_X       164
#define RES_HORARIO_LARGURA 62
STATIC_ASSERT(RES_NOME_X + DEXNAV_NAME_WIDTH + 2 <= RES_CHANCE_FIM - COL_CHANCE_LARGURA, DexNavBuscaNomeAntesDaChance);
STATIC_ASSERT(RES_CHANCE_FIM + 6 <= RES_HORARIO_X, DexNavBuscaChanceAntesDoHorario);
STATIC_ASSERT(RES_HORARIO_X + RES_HORARIO_LARGURA <= COL_SETA_X, DexNavBuscaHorarioAntesDasSetas);

// Posições verticais dentro de cada linha (o texto FONT_NORMAL ocupa ~14 px)
#define LINHA_TEXTO_DY      5   // texto da linha de Pokémon (24 px)
#define LINHA_MARCA_DY      8   // marca 8x8 no meio da linha de Pokémon
#define LINHA_ICONE_DY      10  // centro do ícone (o desenho do Pokémon fica na parte de baixo dos 32x32)
#define LINHA_CURTA_TEXTO_DY 1  // texto das linhas de 16 px (seção, extra, mapa, resultado)
#define SECAO_X             4   // título da seção (VARAS, jeitos da busca), com um fio até SELECAO_FIM
#define SELECAO_X           0   // fundo amarelo da linha selecionada
#define SELECAO_FIM         228

// Topo (barra azul): nome do mapa em TOPO_NOME_X (até DEXNAV_NAME_WIDTH), período em TOPO_PERIODO_X (até
// TOPO_PERIODO_LARGURA: "Entardecer" mede 56), contador alinhado à direita até TOPO_CONTADOR_FIM e a coroa em TOPO_COROA_X.
// Lista e busca: o título (até TOPO_TITULO_LARGURA) em TOPO_NOME_X; à direita, "completos/total" da região (até
// TOPO_CONTADOR_LARGURA) ou "capturado"/"visto" da espécie (até TOPO_STATUS_LARGURA), com a coroa ou a marca.
#define TOPO_TEXTO_Y            1
#define TOPO_NOME_X             4
#define TOPO_PERIODO_X          130
#define TOPO_PERIODO_LARGURA    56
#define TOPO_CONTADOR_FIM       222
#define TOPO_CONTADOR_LARGURA   32
#define TOPO_TITULO_LARGURA     180
#define TOPO_STATUS_LARGURA     56
#define TOPO_COROA_X            226
#define TOPO_COROA_Y            4
STATIC_ASSERT(TOPO_NOME_X + DEXNAV_NAME_WIDTH + 4 <= TOPO_PERIODO_X, DexNavNomeDoMapaAntesDoPeriodo);
STATIC_ASSERT(TOPO_NOME_X + TOPO_TITULO_LARGURA + 4 <= TOPO_CONTADOR_FIM - TOPO_CONTADOR_LARGURA, DexNavTituloAntesDoContador);
STATIC_ASSERT(TOPO_NOME_X + COL_NOME_LARGURA + 4 <= TOPO_CONTADOR_FIM - TOPO_STATUS_LARGURA, DexNavEspecieAntesDoStatus);

// Abas: vagas fixas de ABA_LARGURA px a cada ABA_PASSO, a partir de ABA_X0 (as que o mapa tem, na ordem GRAMA, SURFAR,
// VARAS, PEDRA; na lista, KANTO e SEVII); o rótulo em +ABA_TEXTO_DX e a coroa da aba completa em +ABA_COROA_DX.
#define ABA_X0              4
#define ABA_PASSO           58
#define ABA_LARGURA         54
#define ABA_TEXTO_DX        4
#define ABA_COROA_DX        44
#define ABA_TEXTO_Y         1
#define ABA_COROA_Y         4
STATIC_ASSERT(ABA_X0 + (DEXNAV_TAB_COUNT - 1) * ABA_PASSO + ABA_LARGURA <= DISPLAY_WIDTH, DexNavAbasCabem);

// Rodapé: as partes do modo ("L/R aba", "SELECT mapas"...) em FONT_SMALL, separadas por sText_SeparadorRodape
#define RODAPE_X            4
#define RODAPE_Y            2

enum {
    WIN_TOPO,
    WIN_ABAS,
    WIN_LISTA,
    WIN_RODAPE,
    WIN_COUNT
};

#define WIN_TOPO_BASE    1
#define WIN_ABAS_BASE    (WIN_TOPO_BASE + TELA_TILES_X * TOPO_TILES)
#define WIN_LISTA_BASE   (WIN_ABAS_BASE + TELA_TILES_X * ABAS_TILES)
#define WIN_RODAPE_BASE  (WIN_LISTA_BASE + TELA_TILES_X * LISTA_ALTURA / 8)
#define WINS_FIM         (WIN_RODAPE_BASE + TELA_TILES_X * RODAPE_TILES)
STATIC_ASSERT(WINS_FIM * TILE_SIZE_4BPP <= 31 * BG_SCREEN_SIZE, DexNavJanelasAntesDoTilemap);

// Ícones de graphics/dexnav/icones.png (8x8 cada, lado a lado); a paleta é a da tela inteira (icones.pal).
enum {
    ICONE_CAPTURADO,
    ICONE_VISTO,
    ICONE_NUNCA_VISTO,
    ICONE_COROA,
    ICONE_COUNT
};

// Cores de graphics/dexnav/icones.pal
#define COR_FUNDO        0
#define COR_BRANCO       1
#define COR_TEXTO        2
#define COR_SOMBRA       3
#define COR_OURO         5   // a coroa (barra do mapa completo)
#define COR_BARRA        7
#define COR_SOMBRA_BARRA 8
#define COR_SELECAO      9
#define COR_FAIXA_ABAS   10
#define COR_ABA          11
#define COR_DIVISOR      12
#define COR_CINZA        13
#define COR_SECAO        14
#define COR_SOMBRA_ABA   15

// Ícone de Pokémon nunca visto: a paleta toda escura (a cor 0 continua transparente)
#define TAG_SILHUETA     0x4E44
#define COR_SILHUETA     RGB(5, 5, 7)
#define ICONE_NENHUM     SPRITE_NONE

enum {
    LINHA_MON,       // idx = índice em entries (modo mapa)
    LINHA_SECAO,     // idx = DEXNAV_METHOD_* (uma vara no modo mapa; um jeito no resultado da busca)
    LINHA_EXTRA,     // "+N à noite"
    LINHA_VAZIA,     // "Nenhum agora": a aba não tem Pokémon no período de agora (vem antes da linha extra)
    LINHA_MAPA,      // idx = índice em gDexNavMaps (lista)
    LINHA_ESPECIE,   // idx = espécie (escolha da busca)
    LINHA_RESULTADO, // idx = índice em resultados (resultado da busca)
};

// A escolha tem no máximo uma linha por espécie da Pokédex Nacional; as outras listas cabem nisso (os STATIC_ASSERT)
#define LINHAS_MAX          NATIONAL_DEX_COUNT
#define LINHA_NENHUMA       0xFFFF
// Pares (mapa, jeito) de uma espécie: o pior caso de hoje é o Magikarp, com 101 (test_resultados_cabem)
#define RESULTADOS_MAX      128
STATIC_ASSERT(DEXNAV_MAX_ENTRIES + 3 + 2 <= LINHAS_MAX, DexNavLinhasDoMapaCabem);
STATIC_ASSERT(DEXNAV_MAP_COUNT <= LINHAS_MAX, DexNavLinhasDaListaCabem);
STATIC_ASSERT(RESULTADOS_MAX + DEXNAV_METHOD_COUNT <= LINHAS_MAX, DexNavLinhasDoResultadoCabem);

// Telas empilhadas (B volta a elas): no pior caso mapa, lista, mapa, escolha, resultado (a lista e as duas telas da
// busca aparecem uma vez cada; SELECT/START voltam a elas em vez de empilhar de novo)
#define PILHA_MAX           6

// Mapas lidos por quadro na varredura (DexNav_GetMapEntries de 124 mapas não cabe num quadro só)
#define VARRER_POR_QUADRO   8

enum {
    VARRER_NADA,
    VARRER_CONTAGEM,    // capturados/total de cada mapa e em quantos mapas cada espécie aparece
    VARRER_RESULTADO,   // os mapas da espécie da busca
};

enum {
    FASE_ESPERA,    // criada no DexNav_Open, até o CB2 montar a tela
    FASE_MONTAR,
    FASE_INPUT,
    FASE_TROCAR,    // troca de modo: a varredura (se precisar) e o desenho do modo novo
    FASE_SAIR,
};

struct DexNavLinha
{
    u8 tipo;        // LINHA_*
    u16 idx;
};

// Um mapa onde a espécie da busca aparece, num jeito de encontrar
struct DexNavResultado
{
    u8 mapIndex;
    u8 method;      // DEXNAV_METHOD_*
    u8 periods;     // DEXNAV_PERIOD_* em que aparece
    u16 rateX10;    // a chance agora se aparece agora; senão, a média dos períodos em que aparece
};

// Uma tela guardada na pilha (o que precisa para remontá-la como estava)
struct DexNavQuadro
{
    u8 modo;
    u8 mapIndex;
    u8 regiao;
    u8 abaPos;
    u8 buscaPasso;
    u16 species;
    u16 cursor;
    u16 topo;
};

struct DexNavTela
{
    MainCallback voltar;
    u8 modo;            // DEXNAV_MODE_*
    u8 fase;
    u8 passo;           // passo da montagem
    u8 inputReady;
    u8 ajudaAntes;      // gHelpSystemEnabled de antes da tela (volta a ele na saída)
    u8 mapIndex;        // em gDexNavMaps: o mapa da tela (modo mapa) ou o da linha selecionada (lista)
    u8 periods;         // DexNav_CurrentPeriodBit() ao abrir (a tarde-noite tem 2 bits)
    u8 period;          // DayNight_GetPeriod() ao abrir (o nome no topo)
    u8 nEntries;
    u8 abasMask;        // bit por DEXNAV_TAB_* que o mapa tem
    u8 nAbas;
    u8 abas[DEXNAV_TAB_COUNT];  // as abas do mapa, em ordem
    u8 abaPos;          // a aba atual (posição em abas)
    u8 nMons;           // linhas de Pokémon da aba
    u8 extraN;          // espécies da aba que não aparecem agora (a linha "+N")
    u8 extraPeriods;    // períodos em que elas aparecem
    u8 capturadosMapa;
    u8 totalMapa;
    u8 capturadosAba;
    u8 totalAba;
    u8 regiao;          // lista: DEXNAV_REGION_*
    u8 buscaPasso;      // busca: DEXNAV_SEARCH_*
    u8 alvoMetodo;      // modo mapa aberto pela busca: a aba deste jeito e a linha de alvoEspecie (0xFF = nenhum)
    u8 restaurar;       // a tela veio da pilha: cursor e topo voltam como estavam
    u8 nPilha;
    u8 contado;         // mapCapturados, mapTotal e especieMapas prontos
    u8 varrerTipo;      // VARRER_* em andamento
    u8 varrerPos;       // próximo mapa da varredura
    u16 species;        // busca: a espécie escolhida
    u16 resultadoDe;    // espécie de que resultados é (0 = nenhuma)
    u16 alvoEspecie;    // a linha em que a tela abre (modo mapa, escolha)
    u16 nResultados;
    u16 nLinhas;
    u16 cursor;         // linha (em linhas) selecionada
    u16 topo;           // primeira linha visível
    u16 restaurarCursor;
    u16 restaurarTopo;
    u8 icones[ICONES_MAX];  // sprites dos ícones visíveis (ICONE_NENHUM = vago)
    u8 mapCapturados[DEXNAV_MAP_COUNT];
    u8 mapTotal[DEXNAV_MAP_COUNT];
    u8 especieMapas[NATIONAL_DEX_COUNT + 1];  // pelo número da Pokédex Nacional: em quantos mapas aparece
    struct DexNavQuadro pilha[PILHA_MAX];
    struct DexNavLinha linhas[LINHAS_MAX];
    struct DexNavEntry entries[DEXNAV_MAX_ENTRIES];
    struct DexNavResultado resultados[RESULTADOS_MAX];
};

static EWRAM_DATA struct DexNavTela *sDexNav = NULL;

static void AbrirTela(MainCallback voltar, u8 modo, u8 mapIndex);
static void CB2_DexNav_Montar(void);
static void VBlankCB_DexNav(void);
static void Task_DexNav(u8 taskId);
static void Task_DexNav_Montar(u8 taskId);
static void Task_DexNav_Input(u8 taskId);
static void Task_DexNav_Trocar(u8 taskId);
static void Task_DexNav_Sair(u8 taskId);
static void IniciarVideo(void);
static bool8 Varrer(struct DexNavTela *t);
static void MontarModo(struct DexNavTela *t);
static void MontarMapa(struct DexNavTela *t);
static void MontarAba(struct DexNavTela *t);
static void MontarLista(struct DexNavTela *t);
static void MontarEscolha(struct DexNavTela *t);
static void MontarResultado(struct DexNavTela *t);
static void ContarEspecies(struct DexNavTela *t, u8 aba, u8 *capturados, u8 *total);
static void InputMapa(struct DexNavTela *t);
static void InputLista(struct DexNavTela *t);
static void InputBusca(struct DexNavTela *t);
static void TrocarAba(struct DexNavTela *t, s8 passo);
static void TrocarRegiao(struct DexNavTela *t);
static void MoverCursor(struct DexNavTela *t, s8 passo);
static void PularPagina(struct DexNavTela *t, s8 passo);
static void AjustarTopo(struct DexNavTela *t);
static void Empilhar(struct DexNavTela *t);
static void Desempilhar(struct DexNavTela *t);
static void IrPara(struct DexNavTela *t, u8 modo);
static void Voltar(struct DexNavTela *t);
static void DesenharTudo(struct DexNavTela *t);
static void DesenharTopo(struct DexNavTela *t);
static void DesenharTopoLista(struct DexNavTela *t);
static void DesenharTopoBusca(struct DexNavTela *t);
static void DesenharAbas(struct DexNavTela *t);
static void DesenharAbasLista(struct DexNavTela *t);
static void DesenharCabecalhoBusca(struct DexNavTela *t);
static void DesenharLista(struct DexNavTela *t);
static void DesenharRodape(struct DexNavTela *t);
static void DestruirIcones(struct DexNavTela *t);

static const u8 sIcones_Gfx[] = INCBIN_U8("graphics/dexnav/icones.4bpp");
static const u16 sIcones_Pal[] = INCBIN_U16("graphics/dexnav/icones.gbapal");

static const u16 sSilhueta_Pal[16] = {
    0, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA,
    COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA, COR_SILHUETA,
};

static const struct SpritePalette sSilhueta_SpritePal = {sSilhueta_Pal, TAG_SILHUETA};

// {fundo, letra, sombra}
static const u8 sCor_Barra[3] = {COR_BARRA, COR_BRANCO, COR_SOMBRA_BARRA};
static const u8 sCor_BarraClara[3] = {COR_BARRA, COR_FAIXA_ABAS, COR_SOMBRA_BARRA};
static const u8 sCor_Aba[3] = {COR_ABA, COR_TEXTO, COR_SOMBRA_ABA};
static const u8 sCor_AbaAtual[3] = {COR_BARRA, COR_BRANCO, COR_SOMBRA_BARRA};
static const u8 sCor_Cabecalho[3] = {COR_FAIXA_ABAS, COR_SECAO, COR_SOMBRA_ABA};
static const u8 sCor_Secao[3] = {COR_FUNDO, COR_SECAO, COR_SOMBRA};
static const u8 sCor_Extra[3] = {COR_FUNDO, COR_CINZA, COR_SOMBRA};
static const u8 sCor_Seta[3] = {COR_FUNDO, COR_DIVISOR, COR_SOMBRA};
static const u8 sCor_Rodape[3] = {COR_SOMBRA_BARRA, COR_BRANCO, COR_BARRA};

static const u8 sText_SetaCima[] = _("{UP_ARROW}");
static const u8 sText_SetaBaixo[] = _("{DOWN_ARROW}");
static const u8 sText_Traco[] = {CHAR_HYPHEN, EOS};
static const u8 sText_SeparadorRodape[] = _("  ");

// A aba de cada jeito de encontrar
static const u8 sAbaDoMetodo[DEXNAV_METHOD_COUNT] = {
    [DEXNAV_METHOD_LAND]      = DEXNAV_TAB_LAND,
    [DEXNAV_METHOD_WATER]     = DEXNAV_TAB_WATER,
    [DEXNAV_METHOD_OLD_ROD]   = DEXNAV_TAB_RODS,
    [DEXNAV_METHOD_GOOD_ROD]  = DEXNAV_TAB_RODS,
    [DEXNAV_METHOD_SUPER_ROD] = DEXNAV_TAB_RODS,
    [DEXNAV_METHOD_ROCK]      = DEXNAV_TAB_ROCK,
};

static const u8 *const sNomeDaAba[DEXNAV_TAB_COUNT] = {
    [DEXNAV_TAB_LAND]  = gText_DexNav_AbaGrama,
    [DEXNAV_TAB_WATER] = gText_DexNav_AbaSurf,
    [DEXNAV_TAB_RODS]  = gText_DexNav_AbaVaras,
    [DEXNAV_TAB_ROCK]  = gText_DexNav_AbaPedra,
};

// Título da seção de cada jeito de encontrar (as varas no modo mapa; todos no resultado da busca)
static const u8 *const sNomeDoMetodo[DEXNAV_METHOD_COUNT] = {
    [DEXNAV_METHOD_LAND]      = gText_DexNav_MetodoGrama,
    [DEXNAV_METHOD_WATER]     = gText_DexNav_MetodoSurfar,
    [DEXNAV_METHOD_OLD_ROD]   = gText_DexNav_VaraVelha,
    [DEXNAV_METHOD_GOOD_ROD]  = gText_DexNav_VaraBoa,
    [DEXNAV_METHOD_SUPER_ROD] = gText_DexNav_Supervara,
    [DEXNAV_METHOD_ROCK]      = gText_DexNav_MetodoPedra,
};

// Horário do resultado da busca, pelos bits DEXNAV_PERIOD_*: "dia" é manhã e tarde, como na linha "+N de dia" do
// modo mapa; os três períodos são "dia/noite"
static const u8 *const sNomeDoHorario[DEXNAV_PERIOD_ALL + 1] = {
    [0]                                            = gText_DexNav_HorarioSempre,
    [DEXNAV_PERIOD_MORNING]                        = gText_DexNav_HorarioManha,
    [DEXNAV_PERIOD_DAY]                            = gText_DexNav_HorarioTarde,
    [DEXNAV_PERIOD_NIGHT]                          = gText_DexNav_HorarioNoite,
    [DEXNAV_PERIOD_MORNING | DEXNAV_PERIOD_DAY]    = gText_DexNav_HorarioDia,
    [DEXNAV_PERIOD_DAY | DEXNAV_PERIOD_NIGHT]      = gText_DexNav_HorarioTardeNoite,
    [DEXNAV_PERIOD_MORNING | DEXNAV_PERIOD_NIGHT]  = gText_DexNav_HorarioManhaNoite,
    [DEXNAV_PERIOD_ALL]                            = gText_DexNav_HorarioSempre,
};

static const u8 *const sNomeDaRegiao[] = {
    [DEXNAV_REGION_KANTO] = gText_DexNav_RegiaoKanto,
    [DEXNAV_REGION_SEVII] = gText_DexNav_RegiaoSevii,
};

static const u8 *const sTituloDaRegiao[] = {
    [DEXNAV_REGION_KANTO] = gText_DexNav_MapasKanto,
    [DEXNAV_REGION_SEVII] = gText_DexNav_MapasSevii,
};

static const struct BgTemplate sBgTemplates[] = {
    {
        .bg = 0,
        .charBaseIndex = 0,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0,
    },
};

static const struct WindowTemplate sWindowTemplates[WIN_COUNT + 1] = {
    [WIN_TOPO] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = TELA_TILES_X,
        .height = TOPO_TILES,
        .paletteNum = 0,
        .baseBlock = WIN_TOPO_BASE,
    },
    [WIN_ABAS] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = TOPO_TILES,
        .width = TELA_TILES_X,
        .height = ABAS_TILES,
        .paletteNum = 0,
        .baseBlock = WIN_ABAS_BASE,
    },
    [WIN_LISTA] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = LISTA_TOPO_TILES,
        .width = TELA_TILES_X,
        .height = LISTA_ALTURA / 8,
        .paletteNum = 0,
        .baseBlock = WIN_LISTA_BASE,
    },
    [WIN_RODAPE] = {
        .bg = 0,
        .tilemapLeft = 0,
        .tilemapTop = RODAPE_TOPO_TILES,
        .width = TELA_TILES_X,
        .height = RODAPE_TILES,
        .paletteNum = 0,
        .baseBlock = WIN_RODAPE_BASE,
    },
    [WIN_COUNT] = DUMMY_WIN_TEMPLATE
};

// --- entrada e saída ------------------------------------------------------------------------------------------------

// Mapa sem encontro: a lista abre no último mapa com encontro visitado (gravado ao entrar nele); sem ele (jogo novo,
// save de antes do DexNav), no primeiro mapa visitado; sem nenhum, na primeira linha.
static u8 MapaInicialDaLista(void)
{
    u8 i, ultimo = gSaveBlock1Ptr->dexNav.lastMapIndex;

    if (ultimo < DEXNAV_MAP_COUNT && DexNav_IsVisited(ultimo))
        return ultimo;
    for (i = 0; i < DEXNAV_MAP_COUNT; i++)
    {
        if (DexNav_IsVisited(i))
            return i;
    }
    return 0;
}

void DexNav_Open(MainCallback returnTo)
{
    s16 mapIndex = DexNav_MapIndexOf(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum);

    // mapa sem encontro (cidade, interior): a lista de mapas
    if (mapIndex < 0)
        AbrirTela(returnTo, DEXNAV_MODE_LIST, MapaInicialDaLista());
    else
        AbrirTela(returnTo, DEXNAV_MODE_MAP, mapIndex);
}

// Script de campo (`callnative`, depois de `fadescreen`; a volta continua o script, que espera com `waitstate`)
void DexNav_OpenFromScript(void)
{
    QuestLog_CutRecording();
    DexNav_Open(CB2_ReturnToFieldContinueScriptPlayMapMusic);
    LockPlayerFieldControls();
}

// Aloca o bloco, guarda o retorno e troca o CB2: a tela monta no próximo CB2, fora de quem chamou. Sem memória, volta.
static void AbrirTela(MainCallback voltar, u8 modo, u8 mapIndex)
{
    struct DexNavTela *t;
    u8 i;

    sDexNav = AllocZeroed(sizeof(*sDexNav));
    if (sDexNav == NULL)
    {
        SetMainCallback2(voltar);
        return;
    }
    t = sDexNav;
    t->voltar = voltar;
    t->modo = modo;
    t->mapIndex = mapIndex;
    t->regiao = gDexNavMaps[mapIndex].region;
    t->alvoMetodo = 0xFF;
    t->fase = FASE_ESPERA;
    for (i = 0; i < ICONES_MAX; i++)
        t->icones[i] = ICONE_NENHUM;
    t->ajudaAntes = gHelpSystemEnabled;
    gHelpSystemEnabled = FALSE;
    SetMainCallback2(CB2_DexNav_Montar);
}

static void CB2_DexNav_Montar(void)
{
    SetVBlankHBlankCallbacksToNull();
    ClearScheduledBgCopiesToVram();
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();
    ResetTasks();
    ScanlineEffect_Stop();
    CreateTask(Task_DexNav, 0);   // com as tasks zeradas, sempre há uma livre
    sDexNav->fase = FASE_MONTAR;
    SetMainCallback2(CB2_DexNav);
}

void CB2_DexNav(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void VBlankCB_DexNav(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void Task_DexNav(u8 taskId)
{
    switch (sDexNav->fase)
    {
    case FASE_MONTAR:
        Task_DexNav_Montar(taskId);
        break;
    case FASE_INPUT:
        Task_DexNav_Input(taskId);
        break;
    case FASE_TROCAR:
        Task_DexNav_Trocar(taskId);
        break;
    case FASE_SAIR:
        Task_DexNav_Sair(taskId);
        break;
    }
}

static void Task_DexNav_Montar(u8 taskId)
{
    struct DexNavTela *t = sDexNav;

    switch (t->passo)
    {
    case 0:
        SetVBlankCallback(NULL);
        IniciarVideo();
        break;
    case 1:
        LoadPalette(sIcones_Pal, BG_PLTT_ID(0), PLTT_SIZE_4BPP);
        LoadMonIconPalettes();
        LoadSpritePalette(&sSilhueta_SpritePal);
        // o período vale a abertura toda (todas as telas mostram o mesmo "agora")
        t->periods = DexNav_CurrentPeriodBit();
        t->period = DayNight_GetPeriod();
        break;
    case 2:
        // a lista e a busca varrem os mapas antes (alguns quadros, com a tela ainda escura)
        if (!Varrer(t))
            return;
        MontarModo(t);
        DesenharTudo(t);
        break;
    case 3:
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        SetVBlankCallback(VBlankCB_DexNav);
        break;
    default:
        if (gPaletteFade.active)
            return;
        t->inputReady = TRUE;
        t->fase = FASE_INPUT;
        return;
    }
    t->passo++;
}

// Comum a todos os modos: B volta, SELECT/START trocam de modo, ▲▼ movem a seleção; A e L/R são de cada modo
static void Task_DexNav_Input(u8 taskId)
{
    struct DexNavTela *t = sDexNav;

    if (JOY_NEW(B_BUTTON))
    {
        Voltar(t);
    }
    else if (JOY_NEW(SELECT_BUTTON))
    {
        IrPara(t, DEXNAV_MODE_LIST);
    }
    else if (JOY_NEW(START_BUTTON))
    {
        IrPara(t, DEXNAV_MODE_SEARCH);
    }
    else if (JOY_REPT(DPAD_UP))
    {
        MoverCursor(t, -1);
    }
    else if (JOY_REPT(DPAD_DOWN))
    {
        MoverCursor(t, 1);
    }
    else
    {
        switch (t->modo)
        {
        case DEXNAV_MODE_MAP:
            InputMapa(t);
            break;
        case DEXNAV_MODE_LIST:
            InputLista(t);
            break;
        default:
            InputBusca(t);
            break;
        }
    }
}

// Troca de modo: termina a varredura (se o modo precisa dela) e desenha a tela nova
static void Task_DexNav_Trocar(u8 taskId)
{
    struct DexNavTela *t = sDexNav;

    if (!Varrer(t))
        return;
    MontarModo(t);
    DesenharTudo(t);
    t->inputReady = TRUE;
    t->fase = FASE_INPUT;
}

static void Task_DexNav_Sair(u8 taskId)
{
    MainCallback voltar = sDexNav->voltar;
    u8 ajudaAntes = sDexNav->ajudaAntes;

    if (gPaletteFade.active)
        return;
    DestruirIcones(sDexNav);
    FreeAllWindowBuffers();
    DestroyTask(taskId);
    Free(sDexNav);
    sDexNav = NULL;
    if (ajudaAntes)
        HelpSystem_Enable();
    SetMainCallback2(voltar);
}

static void IniciarVideo(void)
{
    DmaClearLarge16(3, (void *)VRAM, VRAM_SIZE, 0x1000);
    DmaClear32(3, (void *)OAM, OAM_SIZE);
    DmaClear16(3, (void *)PLTT, PLTT_SIZE);
    SetGpuReg(REG_OFFSET_DISPCNT, 0);
    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sBgTemplates, ARRAY_COUNT(sBgTemplates));
    ChangeBgX(0, 0, BG_COORD_SET);
    ChangeBgY(0, 0, BG_COORD_SET);
    InitWindows(sWindowTemplates);
    DeactivateAllTextPrinters();
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_1D_MAP | DISPCNT_OBJ_ON);
    // quem abre pode chegar com escurecimento (BLDCNT/BLDY) e janelas ligados: a tela começa limpa
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    SetGpuReg(REG_OFFSET_BLDY, 0);
    SetGpuReg(REG_OFFSET_WININ, 0);
    SetGpuReg(REG_OFFSET_WINOUT, 0);
    ShowBg(0);
}

// --- navegação entre os modos ---------------------------------------------------------------------------------------

static void Trocar(struct DexNavTela *t)
{
    t->inputReady = FALSE;
    t->fase = FASE_TROCAR;
}

// Guarda a tela de agora na pilha (B volta a ela). A pilha nunca enche (PILHA_MAX); se enchesse, a tela não é guardada.
static void Empilhar(struct DexNavTela *t)
{
    struct DexNavQuadro *q;

    if (t->nPilha >= PILHA_MAX)
        return;
    q = &t->pilha[t->nPilha++];
    q->modo = t->modo;
    q->mapIndex = t->mapIndex;
    q->regiao = t->regiao;
    q->abaPos = t->abaPos;
    q->buscaPasso = t->buscaPasso;
    q->species = t->species;
    q->cursor = t->cursor;
    q->topo = t->topo;
}

// Volta à tela do alto da pilha, com a seleção e a rolagem de quando saiu dela
static void Desempilhar(struct DexNavTela *t)
{
    struct DexNavQuadro *q = &t->pilha[--t->nPilha];

    t->modo = q->modo;
    t->mapIndex = q->mapIndex;
    t->regiao = q->regiao;
    t->abaPos = q->abaPos;
    t->buscaPasso = q->buscaPasso;
    t->species = q->species;
    t->restaurar = TRUE;
    t->restaurarCursor = q->cursor;
    t->restaurarTopo = q->topo;
    t->alvoEspecie = SPECIES_NONE;
    t->alvoMetodo = 0xFF;
    Trocar(t);
}

// SELECT (lista) e START (busca): se a tela pedida já está na pilha, volta até ela; senão, empilha a de agora e abre
// a pedida. A lista abre no mapa da tela de agora; a busca, na espécie selecionada no modo mapa.
static void IrPara(struct DexNavTela *t, u8 modo)
{
    s8 i;
    u16 especie = SPECIES_NONE;

    if (t->modo == modo)
        return;
    PlaySE(SE_SELECT);
    for (i = t->nPilha - 1; i >= 0; i--)
    {
        if (t->pilha[i].modo == modo)
        {
            t->nPilha = i + 1;
            Desempilhar(t);
            return;
        }
    }
    if (t->modo == DEXNAV_MODE_MAP && t->cursor < t->nLinhas && t->linhas[t->cursor].tipo == LINHA_MON)
        especie = t->entries[t->linhas[t->cursor].idx].species;
    Empilhar(t);
    t->modo = modo;
    t->restaurar = FALSE;
    t->alvoMetodo = 0xFF;
    if (modo == DEXNAV_MODE_LIST)
    {
        t->regiao = gDexNavMaps[t->mapIndex].region;
        t->alvoEspecie = SPECIES_NONE;
    }
    else
    {
        t->buscaPasso = DEXNAV_SEARCH_CHOOSE;
        t->alvoEspecie = especie;
    }
    Trocar(t);
}

// B: a tela anterior; na primeira, sai do DexNav
static void Voltar(struct DexNavTela *t)
{
    PlaySE(SE_SELECT);
    if (t->nPilha == 0)
    {
        t->inputReady = FALSE;
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        t->fase = FASE_SAIR;
        return;
    }
    Desempilhar(t);
}

// Abre o modo mapa de `mapIndex` por cima da tela de agora (A na lista ou no resultado da busca)
static void AbrirMapa(struct DexNavTela *t, u8 mapIndex, u16 especie, u8 metodo)
{
    PlaySE(SE_SELECT);
    Empilhar(t);
    t->modo = DEXNAV_MODE_MAP;
    t->mapIndex = mapIndex;
    t->abaPos = 0;
    t->restaurar = FALSE;
    t->alvoEspecie = especie;
    t->alvoMetodo = metodo;
    Trocar(t);
}

// --- dados ----------------------------------------------------------------------------------------------------------

// Espécies distintas das entradas, contando as capturadas (o mapa todo na varredura)
static void ContarMapa(struct DexNavTela *t, u8 mapIndex)
{
    u8 i, j;
    u16 dex;

    ContarEspecies(t, DEXNAV_TAB_COUNT, &t->mapCapturados[mapIndex], &t->mapTotal[mapIndex]);
    for (i = 0; i < t->nEntries; i++)
    {
        for (j = 0; j < i; j++)
        {
            if (t->entries[j].species == t->entries[i].species)
                break;
        }
        dex = SpeciesToNationalPokedexNum(t->entries[i].species);
        if (j == i && dex <= NATIONAL_DEX_COUNT)
            t->especieMapas[dex]++;
    }
}

// As entradas do mapa com a espécie da busca. A chance é a de agora quando a espécie aparece agora; senão, a dos
// períodos em que ela aparece (a média deles, como a tarde-noite).
static void ColherResultados(struct DexNavTela *t, u8 mapIndex)
{
    const struct DexNavEntry *e;
    struct DexNavResultado *r;
    u8 i;

    for (i = 0; i < t->nEntries; i++)
    {
        e = &t->entries[i];
        if (t->entries[i].species != t->species || t->nResultados >= RESULTADOS_MAX)
            continue;
        r = &t->resultados[t->nResultados++];
        r->mapIndex = mapIndex;
        r->method = e->method;
        r->periods = e->periods;
        r->rateX10 = DexNav_RateForPeriods(e, (e->periods & t->periods) ? t->periods : e->periods);
    }
}

// Uma parte da varredura dos mapas que o modo precisa (VARRER_POR_QUADRO mapas); TRUE quando os dados estão prontos.
// As entradas de cada mapa passam por `entries` (o modo mapa remonta as dele ao voltar).
static bool8 Varrer(struct DexNavTela *t)
{
    u8 tipo, fim;

    if (t->modo == DEXNAV_MODE_MAP)
        return TRUE;
    if (!t->contado)
        tipo = VARRER_CONTAGEM;
    else if (t->modo == DEXNAV_MODE_SEARCH && t->buscaPasso == DEXNAV_SEARCH_RESULT && t->resultadoDe != t->species)
        tipo = VARRER_RESULTADO;
    else
        return TRUE;
    if (t->varrerTipo != tipo)
    {
        t->varrerTipo = tipo;
        t->varrerPos = 0;
        t->nResultados = 0;
    }
    fim = t->varrerPos + VARRER_POR_QUADRO;
    if (fim > DEXNAV_MAP_COUNT)
        fim = DEXNAV_MAP_COUNT;
    for (; t->varrerPos < fim; t->varrerPos++)
    {
        t->nEntries = DexNav_GetMapEntries(t->varrerPos, t->entries, DEXNAV_MAX_ENTRIES);
        if (tipo == VARRER_CONTAGEM)
            ContarMapa(t, t->varrerPos);
        else
            ColherResultados(t, t->varrerPos);
    }
    if (t->varrerPos < DEXNAV_MAP_COUNT)
        return FALSE;
    if (tipo == VARRER_CONTAGEM)
        t->contado = TRUE;
    else
        t->resultadoDe = t->species;
    t->varrerTipo = VARRER_NADA;
    return FALSE;   // no próximo quadro: a outra varredura, se faltar, ou pronto
}

static bool8 Selecionavel(u8 tipo)
{
    return tipo == LINHA_MON || tipo == LINHA_MAPA || tipo == LINHA_ESPECIE || tipo == LINHA_RESULTADO;
}

static void AdicionarLinha(struct DexNavTela *t, u8 tipo, u16 idx)
{
    if (t->nLinhas >= LINHAS_MAX)
        return;
    t->linhas[t->nLinhas].tipo = tipo;
    t->linhas[t->nLinhas].idx = idx;
    t->nLinhas++;
}

static void LimparLinhas(struct DexNavTela *t)
{
    t->nLinhas = 0;
    t->nMons = 0;
    t->topo = 0;
    t->cursor = 0;
}

// A primeira linha que se escolhe (0 se nenhuma)
static u16 PrimeiraSelecionavel(struct DexNavTela *t)
{
    u16 i;

    for (i = 0; i < t->nLinhas; i++)
    {
        if (Selecionavel(t->linhas[i].tipo))
            return i;
    }
    return 0;
}

// Monta as linhas do modo de agora; a tela que veio da pilha volta com a seleção e a rolagem de antes (se a linha
// ainda existe: o período não muda dentro do DexNav, mas por garantia)
static void MontarModo(struct DexNavTela *t)
{
    DestruirIcones(t);
    switch (t->modo)
    {
    case DEXNAV_MODE_MAP:
        MontarMapa(t);
        break;
    case DEXNAV_MODE_LIST:
        MontarLista(t);
        break;
    default:
        if (t->buscaPasso == DEXNAV_SEARCH_CHOOSE)
            MontarEscolha(t);
        else
            MontarResultado(t);
        break;
    }
    if (t->restaurar)
    {
        t->restaurar = FALSE;
        if (t->restaurarCursor < t->nLinhas && Selecionavel(t->linhas[t->restaurarCursor].tipo))
        {
            t->cursor = t->restaurarCursor;
            t->topo = t->restaurarTopo <= t->cursor ? t->restaurarTopo : t->cursor;
        }
    }
    if (t->modo == DEXNAV_MODE_LIST && t->cursor < t->nLinhas)
        t->mapIndex = t->linhas[t->cursor].idx;
    AjustarTopo(t);
}

// --- modo mapa: dados -----------------------------------------------------------------------------------------------

// As entradas do mapa (todas, de todos os períodos), as abas que ele tem e o contador do mapa. Abre na aba guardada
// (pilha) ou na primeira; aberto pela busca, na aba do jeito (alvoMetodo) e na linha da espécie (alvoEspecie).
static void MontarMapa(struct DexNavTela *t)
{
    u16 i;

    t->nEntries = DexNav_GetMapEntries(t->mapIndex, t->entries, DEXNAV_MAX_ENTRIES);
    t->abasMask = 0;
    for (i = 0; i < t->nEntries; i++)
        t->abasMask |= 1 << sAbaDoMetodo[t->entries[i].method];
    t->nAbas = 0;
    for (i = 0; i < DEXNAV_TAB_COUNT; i++)
    {
        if (t->abasMask & (1 << i))
            t->abas[t->nAbas++] = i;
    }
    if (t->alvoMetodo < DEXNAV_METHOD_COUNT)
    {
        for (i = 0; i < t->nAbas; i++)
        {
            if (t->abas[i] == sAbaDoMetodo[t->alvoMetodo])
                t->abaPos = i;
        }
    }
    if (t->abaPos >= t->nAbas)
        t->abaPos = 0;
    ContarEspecies(t, DEXNAV_TAB_COUNT, &t->capturadosMapa, &t->totalMapa);
    MontarAba(t);
    if (t->alvoMetodo < DEXNAV_METHOD_COUNT)
    {
        for (i = 0; i < t->nLinhas; i++)
        {
            if (t->linhas[i].tipo == LINHA_MON && t->entries[t->linhas[i].idx].species == t->alvoEspecie
             && t->entries[t->linhas[i].idx].method == t->alvoMetodo)
            {
                t->cursor = i;
                break;
            }
        }
    }
    t->alvoMetodo = 0xFF;
    t->alvoEspecie = SPECIES_NONE;
}

static bool8 NaAba(const struct DexNavEntry *e, u8 aba)
{
    return aba == DEXNAV_TAB_COUNT || sAbaDoMetodo[e->method] == aba;
}

// Espécies distintas da aba (DEXNAV_TAB_COUNT = o mapa todo), em qualquer horário (o progresso não muda com o
// relógio), e quantas delas estão capturadas na Pokédex.
static void ContarEspecies(struct DexNavTela *t, u8 aba, u8 *capturados, u8 *total)
{
    u8 i, j;

    *capturados = 0;
    *total = 0;
    for (i = 0; i < t->nEntries; i++)
    {
        if (!NaAba(&t->entries[i], aba))
            continue;
        for (j = 0; j < i; j++)
        {
            if (t->entries[j].species == t->entries[i].species && NaAba(&t->entries[j], aba))
                break;
        }
        if (j < i)
            continue;
        (*total)++;
        if (GetSetPokedexFlag(SpeciesToNationalPokedexNum(t->entries[i].species), FLAG_GET_CAUGHT))
            (*capturados)++;
    }
}

// A espécie aparece agora em alguma entrada da aba?
static bool8 AparecemAgora(struct DexNavTela *t, u8 aba, u16 species)
{
    u8 i;

    for (i = 0; i < t->nEntries; i++)
    {
        if (t->entries[i].species == species && NaAba(&t->entries[i], aba) && (t->entries[i].periods & t->periods))
            return TRUE;
    }
    return FALSE;
}

// As linhas da aba atual: por jeito de encontrar (VARAS: uma seção por vara, com título, só se tiver Pokémon agora),
// os Pokémon do período de agora por chance (maior primeiro; empate: a ordem de DexNav_GetMapEntries) e, no fim, a
// linha extra com as espécies da aba que só aparecem em outro período. A seleção vai para o primeiro Pokémon.
static void MontarAba(struct DexNavTela *t)
{
    u8 aba, m, i;
    u16 j, secao, primeira;
    u16 rate;
    const struct DexNavEntry *e;

    LimparLinhas(t);
    t->extraN = 0;
    t->extraPeriods = 0;
    t->capturadosAba = 0;
    t->totalAba = 0;
    if (t->nAbas == 0)
        return;
    aba = t->abas[t->abaPos];
    ContarEspecies(t, aba, &t->capturadosAba, &t->totalAba);
    for (m = 0; m < DEXNAV_METHOD_COUNT; m++)
    {
        if (sAbaDoMetodo[m] != aba)
            continue;
        secao = t->nLinhas;
        if (aba == DEXNAV_TAB_RODS)
            AdicionarLinha(t, LINHA_SECAO, m);
        primeira = t->nLinhas;
        for (i = 0; i < t->nEntries; i++)
        {
            e = &t->entries[i];
            if (e->method != m || !(e->periods & t->periods) || t->nLinhas >= LINHAS_MAX)
                continue;
            rate = DexNav_RateForPeriods(e, t->periods);
            for (j = t->nLinhas; j > primeira && DexNav_RateForPeriods(&t->entries[t->linhas[j - 1].idx], t->periods) < rate; j--)
                t->linhas[j] = t->linhas[j - 1];
            t->linhas[j].tipo = LINHA_MON;
            t->linhas[j].idx = i;
            t->nLinhas++;
            t->nMons++;
        }
        if (t->nLinhas == primeira)
            t->nLinhas = secao;   // a vara não tem nada agora: sem título
    }

    // espécies da aba que não aparecem agora (cada uma uma vez) e os períodos delas
    for (i = 0; i < t->nEntries; i++)
    {
        e = &t->entries[i];
        if (!NaAba(e, aba) || AparecemAgora(t, aba, e->species))
            continue;
        t->extraPeriods |= e->periods;
        for (j = 0; j < i; j++)
        {
            if (t->entries[j].species == e->species && NaAba(&t->entries[j], aba))
                break;
        }
        if (j == i)
            t->extraN++;
    }
    // sem Pokémon agora (a aba existe, então todas as espécies dela são de outro período): a tela se explica
    if (t->nMons == 0)
        AdicionarLinha(t, LINHA_VAZIA, 0);
    if (t->extraN != 0)
        AdicionarLinha(t, LINHA_EXTRA, 0);
    t->cursor = PrimeiraSelecionavel(t);
}

// --- modo lista: dados ----------------------------------------------------------------------------------------------

// Conhecido: visitado e com encontro agora (a câmara de Tanoby trancada, visitada, ainda não tem nada: "?/?" e A não
// abre, como o não visitado)
static bool8 MapaConhecido(struct DexNavTela *t, u8 i)
{
    return DexNav_IsVisited(i) && t->mapTotal[i] != 0;
}

// Completo: visitado (o que não foi visitado não se sabe) e com todas as espécies capturadas
static bool8 MapaCompleto(struct DexNavTela *t, u8 i)
{
    return DexNav_IsVisited(i) && t->mapTotal[i] != 0 && t->mapCapturados[i] == t->mapTotal[i];
}

// Mapas completos e mapas da região (o topo da lista e a coroa da aba da região)
static void ContarRegiao(struct DexNavTela *t, u8 regiao, u8 *completos, u8 *total)
{
    u8 i;

    *completos = 0;
    *total = 0;
    for (i = 0; i < DEXNAV_MAP_COUNT; i++)
    {
        if (gDexNavMaps[i].region != regiao)
            continue;
        (*total)++;
        if (MapaCompleto(t, i))
            (*completos)++;
    }
}

// O mapa do jogador: o atual (se tem encontro) ou o último com encontro visitado
static u8 MapaDoJogador(void)
{
    s16 i = DexNav_MapIndexOf(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum);

    return i >= 0 ? i : gSaveBlock1Ptr->dexNav.lastMapIndex;
}

// Os mapas da região, na ordem da tabela (a da Pokédex AREA). A seleção vai para o mapa da tela de onde se veio (ou
// guardado), senão para o mapa do jogador, senão para o primeiro visitado, senão para a primeira linha.
static void MontarLista(struct DexNavTela *t)
{
    u8 i, jogador = MapaDoJogador();
    u16 noMapa = LINHA_NENHUMA, noJogador = LINHA_NENHUMA, visitado = LINHA_NENHUMA;

    LimparLinhas(t);
    for (i = 0; i < DEXNAV_MAP_COUNT; i++)
    {
        if (gDexNavMaps[i].region == t->regiao)
        {
            if (i == t->mapIndex)
                noMapa = t->nLinhas;
            if (i == jogador)
                noJogador = t->nLinhas;
            if (visitado == LINHA_NENHUMA && DexNav_IsVisited(i))
                visitado = t->nLinhas;
            AdicionarLinha(t, LINHA_MAPA, i);
        }
    }
    if (noMapa != LINHA_NENHUMA)
        t->cursor = noMapa;
    else if (noJogador != LINHA_NENHUMA)
        t->cursor = noJogador;
    else if (visitado != LINHA_NENHUMA)
        t->cursor = visitado;
}

// --- modo busca: dados ----------------------------------------------------------------------------------------------

// Passo 1: as espécies vistas na Pokédex que aparecem em algum mapa, na ordem da Pokédex Nacional. A seleção vai para
// a espécie selecionada no modo mapa de onde se veio, se ela está na lista.
static void MontarEscolha(struct DexNavTela *t)
{
    u16 dex, species;

    LimparLinhas(t);
    for (dex = 1; dex <= NATIONAL_DEX_COUNT; dex++)
    {
        if (t->especieMapas[dex] == 0 || !GetSetPokedexFlag(dex, FLAG_GET_SEEN))
            continue;
        species = NationalPokedexNumToSpecies(dex);
        if (species == t->alvoEspecie)
            t->cursor = t->nLinhas;
        AdicionarLinha(t, LINHA_ESPECIE, species);
    }
    t->alvoEspecie = SPECIES_NONE;
}

// A espécie aparece agora (no período de agora) neste resultado?
static bool8 ResultadoAgora(struct DexNavTela *t, const struct DexNavResultado *r)
{
    return (r->periods & t->periods) != 0;
}

// Ordem do resultado: primeiro os que aparecem agora, depois por chance (maior primeiro)
static bool8 ResultadoAntes(struct DexNavTela *t, u16 a, u16 b)
{
    bool8 agoraA = ResultadoAgora(t, &t->resultados[a]), agoraB = ResultadoAgora(t, &t->resultados[b]);

    if (agoraA != agoraB)
        return agoraA;
    return t->resultados[a].rateX10 > t->resultados[b].rateX10;
}

// Passo 2: os mapas da espécie, uma seção por jeito de encontrar (na ordem DEXNAV_METHOD_*); em cada uma, primeiro os
// mapas onde ela aparece agora, depois os de outro horário, cada grupo por chance (maior primeiro; empate: a ordem
// dos mapas)
static void MontarResultado(struct DexNavTela *t)
{
    u8 m;
    u16 r, j, secao, primeira;

    LimparLinhas(t);
    for (m = 0; m < DEXNAV_METHOD_COUNT; m++)
    {
        secao = t->nLinhas;
        AdicionarLinha(t, LINHA_SECAO, m);
        primeira = t->nLinhas;
        for (r = 0; r < t->nResultados; r++)
        {
            if (t->resultados[r].method != m || t->nLinhas >= LINHAS_MAX)
                continue;
            for (j = t->nLinhas; j > primeira && ResultadoAntes(t, r, t->linhas[j - 1].idx); j--)
                t->linhas[j] = t->linhas[j - 1];
            t->linhas[j].tipo = LINHA_RESULTADO;
            t->linhas[j].idx = r;
            t->nLinhas++;
        }
        if (t->nLinhas == primeira)
            t->nLinhas = secao;
    }
    t->cursor = PrimeiraSelecionavel(t);
}

// --- controles ------------------------------------------------------------------------------------------------------

// Modo mapa: L/R trocam de aba
static void InputMapa(struct DexNavTela *t)
{
    if (JOY_NEW(L_BUTTON))
        TrocarAba(t, -1);
    else if (JOY_NEW(R_BUTTON))
        TrocarAba(t, 1);
}

// Lista: A abre o modo mapa do mapa selecionado (só se visitado: sem estragar surpresa); L/R trocam de região
static void InputLista(struct DexNavTela *t)
{
    u8 mapIndex;

    if (JOY_NEW(A_BUTTON))
    {
        if (t->cursor >= t->nLinhas || t->linhas[t->cursor].tipo != LINHA_MAPA)
            return;
        mapIndex = t->linhas[t->cursor].idx;
        if (!DexNav_IsVisited(mapIndex))
            return;
        if (!MapaConhecido(t, mapIndex))
            return;   // visitado, mas sem encontro agora (câmara de Tanoby trancada)
        AbrirMapa(t, mapIndex, SPECIES_NONE, 0xFF);
    }
    else if (JOY_NEW(L_BUTTON) || JOY_NEW(R_BUTTON))
    {
        TrocarRegiao(t);
    }
}

// Busca: A na escolha mostra os mapas da espécie; A no resultado abre o modo mapa (só mapa visitado); L/R, página
static void InputBusca(struct DexNavTela *t)
{
    const struct DexNavResultado *r;

    if (JOY_NEW(A_BUTTON))
    {
        if (t->cursor >= t->nLinhas)
            return;
        if (t->buscaPasso == DEXNAV_SEARCH_CHOOSE)
        {
            if (t->linhas[t->cursor].tipo != LINHA_ESPECIE)
                return;
            PlaySE(SE_SELECT);
            Empilhar(t);
            t->species = t->linhas[t->cursor].idx;
            t->buscaPasso = DEXNAV_SEARCH_RESULT;
            t->restaurar = FALSE;
            Trocar(t);
            return;
        }
        if (t->linhas[t->cursor].tipo != LINHA_RESULTADO)
            return;
        r = &t->resultados[t->linhas[t->cursor].idx];
        if (!DexNav_IsVisited(r->mapIndex))
            return;
        AbrirMapa(t, r->mapIndex, t->species, r->method);   // DEXNAV_MODE_MAP na aba do jeito
    }
    else if (JOY_NEW(L_BUTTON))
    {
        PularPagina(t, -1);
    }
    else if (JOY_NEW(R_BUTTON))
    {
        PularPagina(t, 1);
    }
}

// L/R: aba anterior/seguinte entre as que o mapa tem, dando a volta; a lista volta ao topo.
static void TrocarAba(struct DexNavTela *t, s8 passo)
{
    if (t->nAbas <= 1)
        return;
    PlaySE(SE_SELECT);
    t->abaPos = (t->abaPos + t->nAbas + passo) % t->nAbas;
    MontarAba(t);
    DesenharAbas(t);
    DesenharLista(t);
}

// L/R na lista: Kanto ↔ Ilhas Sevii (só duas: L e R fazem o mesmo)
static void TrocarRegiao(struct DexNavTela *t)
{
    PlaySE(SE_SELECT);
    t->regiao = t->regiao == DEXNAV_REGION_KANTO ? DEXNAV_REGION_SEVII : DEXNAV_REGION_KANTO;
    MontarModo(t);
    DesenharTudo(t);
}

static u8 AlturaDaLinha(u8 tipo)
{
    switch (tipo)
    {
    case LINHA_MON:
    case LINHA_ESPECIE:
        return LINHA_MON_ALTURA;
    case LINHA_SECAO:
        return LINHA_SECAO_ALTURA;
    case LINHA_EXTRA:
    case LINHA_VAZIA:
        return LINHA_EXTRA_ALTURA;
    default:
        return LINHA_CURTA_ALTURA;
    }
}

// Altura das linhas de `de` a `ate` (inclusive)
static u16 AlturaDasLinhas(struct DexNavTela *t, u16 de, u16 ate)
{
    u16 altura = 0;

    for (; de <= ate && de < t->nLinhas; de++)
        altura += AlturaDaLinha(t->linhas[de].tipo);
    return altura;
}

// O título da seção a que a linha pertence: a última LINHA_SECAO antes dela (LINHA_NENHUMA = sem seção)
static u16 SecaoDaLinha(struct DexNavTela *t, u16 linha)
{
    while (linha > 0)
    {
        linha--;
        if (t->linhas[linha].tipo == LINHA_SECAO)
            return linha;
    }
    return LINHA_NENHUMA;
}

// Título fixo no alto da lista: quando a primeira linha visível é de uma seção cujo título já rolou para cima, o título
// fica preso no alto (LINHA_SECAO_ALTURA px), e as linhas começam embaixo dele. Assim a seção da linha de cima nunca
// some ao rolar (o título só "volta para o lugar" quando a lista sobe até ele).
static u16 SecaoFixa(struct DexNavTela *t)
{
    if (t->topo >= t->nLinhas || t->linhas[t->topo].tipo == LINHA_SECAO)
        return LINHA_NENHUMA;
    return SecaoDaLinha(t, t->topo);
}

// Altura usada a partir de `topo` até `ate`, contando o título fixo
static u16 AlturaVisivel(struct DexNavTela *t, u16 ate)
{
    return AlturaDasLinhas(t, t->topo, ate) + (SecaoFixa(t) != LINHA_NENHUMA ? LINHA_SECAO_ALTURA : 0);
}

// Rola para mostrar a linha selecionada e, na última que se escolhe, o que vier depois dela (a linha extra). Subindo,
// o topo vai até o título da seção da linha selecionada (se ela tiver); descendo, o título que sair de vista fica fixo
// no alto (SecaoFixa): a seção da linha selecionada está sempre à vista.
static void AjustarTopo(struct DexNavTela *t)
{
    u16 primeira = t->cursor, ultima = t->cursor, secao, i;

    if (t->nLinhas == 0)
    {
        t->topo = 0;
        return;
    }
    secao = SecaoDaLinha(t, t->cursor);
    if (secao != LINHA_NENHUMA)
        primeira = secao;
    for (i = t->cursor + 1; i < t->nLinhas && !Selecionavel(t->linhas[i].tipo); i++)
        ;
    if (i >= t->nLinhas)
        ultima = t->nLinhas - 1;
    if (t->topo > t->cursor)
        t->topo = primeira;
    while (t->topo < t->cursor && AlturaVisivel(t, ultima) > LISTA_ALTURA)
        t->topo++;
}

// A linha anterior/seguinte que se escolhe (sem dar a volta; os títulos e a linha extra são pulados); FALSE no fim
static bool8 AvancarCursor(struct DexNavTela *t, s8 passo)
{
    s32 i = t->cursor;

    do
    {
        i += passo;
    } while (i >= 0 && i < t->nLinhas && !Selecionavel(t->linhas[i].tipo));
    if (i < 0 || i >= t->nLinhas)
        return FALSE;
    t->cursor = i;
    return TRUE;
}

static void CursorMudou(struct DexNavTela *t)
{
    PlaySE(SE_SELECT);
    if (t->modo == DEXNAV_MODE_LIST)
        t->mapIndex = t->linhas[t->cursor].idx;
    AjustarTopo(t);
    DesenharLista(t);
}

// ▲▼: a linha anterior/seguinte
static void MoverCursor(struct DexNavTela *t, s8 passo)
{
    if (AvancarCursor(t, passo))
        CursorMudou(t);
}

// L/R na busca: uma página (as linhas que cabem na lista) para cima/baixo, parando no começo/fim
static void PularPagina(struct DexNavTela *t, s8 passo)
{
    u8 n, linhas;

    if (t->cursor >= t->nLinhas)
        return;
    linhas = LISTA_ALTURA / AlturaDaLinha(t->linhas[t->cursor].tipo);
    for (n = 0; n < linhas && AvancarCursor(t, passo); n++)
        ;
    if (n != 0)
        CursorMudou(t);
}

// --- desenho --------------------------------------------------------------------------------------------------------

static void BlitIcone(u8 windowId, u8 icone, u16 x, u16 y)
{
    BlitBitmapRectToWindow(windowId, sIcones_Gfx, icone * 8, 0, ICONE_COUNT * 8, 8, x, y, 8, 8);
}

static void DesenharTudo(struct DexNavTela *t)
{
    switch (t->modo)
    {
    case DEXNAV_MODE_MAP:
        DesenharTopo(t);
        DesenharAbas(t);
        break;
    case DEXNAV_MODE_LIST:
        DesenharTopoLista(t);
        DesenharAbasLista(t);
        break;
    default:
        DesenharTopoBusca(t);
        DesenharCabecalhoBusca(t);
        break;
    }
    DesenharLista(t);
    DesenharRodape(t);
}

// "capturados/total" (até 2 algarismos cada)
static void FormatarContador(u8 *dest, u8 capturados, u8 total)
{
    dest = ConvertIntToDecimalStringN(dest, capturados, STR_CONV_MODE_LEFT_ALIGN, 3);
    *dest++ = CHAR_SLASH;
    ConvertIntToDecimalStringN(dest, total, STR_CONV_MODE_LEFT_ALIGN, 3);
}

// Nome do mapa, período e "capturados/total" do mapa (ou "100%" e a coroa, com tudo capturado)
static void DesenharTopo(struct DexNavTela *t)
{
    u8 contador[12];
    bool8 completo = t->totalMapa != 0 && t->capturadosMapa == t->totalMapa;

    FillWindowPixelBuffer(WIN_TOPO, PIXEL_FILL(COR_BARRA));
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_NOME_X, TOPO_TEXTO_Y, 0, 0, sCor_Barra, TEXT_SKIP_DRAW,
                                 gDexNavMaps[t->mapIndex].name);
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_PERIODO_X, TOPO_TEXTO_Y, 0, 0, sCor_BarraClara,
                                 TEXT_SKIP_DRAW, gText_DayNight_PeriodName[t->period]);
    if (completo)
    {
        StringCopy(contador, gText_DexNav_Completo);
        BlitIcone(WIN_TOPO, ICONE_COROA, TOPO_COROA_X, TOPO_COROA_Y);
    }
    else
    {
        FormatarContador(contador, t->capturadosMapa, t->totalMapa);
    }
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_CONTADOR_FIM - GetStringWidth(FONT_NORMAL, contador, 0),
                                 TOPO_TEXTO_Y, 0, 0, sCor_Barra, TEXT_SKIP_DRAW, contador);
    PutWindowTilemap(WIN_TOPO);
    CopyWindowToVram(WIN_TOPO, COPYWIN_FULL);
}

// Lista: "Mapas de Kanto" (ou das Ilhas Sevii) e "completos/total" da região, com a coroa
static void DesenharTopoLista(struct DexNavTela *t)
{
    u8 contador[12], completos, total;

    ContarRegiao(t, t->regiao, &completos, &total);
    FillWindowPixelBuffer(WIN_TOPO, PIXEL_FILL(COR_BARRA));
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_NOME_X, TOPO_TEXTO_Y, 0, 0, sCor_Barra, TEXT_SKIP_DRAW,
                                 sTituloDaRegiao[t->regiao]);
    FormatarContador(contador, completos, total);
    AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_CONTADOR_FIM - GetStringWidth(FONT_NORMAL, contador, 0),
                                 TOPO_TEXTO_Y, 0, 0, sCor_Barra, TEXT_SKIP_DRAW, contador);
    BlitIcone(WIN_TOPO, ICONE_COROA, TOPO_COROA_X, TOPO_COROA_Y);
    PutWindowTilemap(WIN_TOPO);
    CopyWindowToVram(WIN_TOPO, COPYWIN_FULL);
}

// Busca: "Buscar Pokémon" na escolha; no resultado, o nome da espécie e "capturado"/"visto" com a marca
static void DesenharTopoBusca(struct DexNavTela *t)
{
    bool8 capturado;
    const u8 *status;

    FillWindowPixelBuffer(WIN_TOPO, PIXEL_FILL(COR_BARRA));
    if (t->buscaPasso == DEXNAV_SEARCH_CHOOSE)
    {
        AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_NOME_X, TOPO_TEXTO_Y, 0, 0, sCor_Barra,
                                     TEXT_SKIP_DRAW, gText_DexNav_BuscaTitulo);
    }
    else
    {
        capturado = GetSetPokedexFlag(SpeciesToNationalPokedexNum(t->species), FLAG_GET_CAUGHT);
        status = capturado ? gText_DexNav_Capturado : gText_DexNav_Visto;
        AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_NOME_X, TOPO_TEXTO_Y, 0, 0, sCor_Barra,
                                     TEXT_SKIP_DRAW, gSpeciesNames[t->species]);
        AddTextPrinterParameterized4(WIN_TOPO, FONT_NORMAL, TOPO_CONTADOR_FIM - GetStringWidth(FONT_NORMAL, status, 0),
                                     TOPO_TEXTO_Y, 0, 0, sCor_BarraClara, TEXT_SKIP_DRAW, status);
        BlitIcone(WIN_TOPO, capturado ? ICONE_CAPTURADO : ICONE_VISTO, TOPO_COROA_X, TOPO_COROA_Y);
    }
    PutWindowTilemap(WIN_TOPO);
    CopyWindowToVram(WIN_TOPO, COPYWIN_FULL);
}

// Uma aba na vaga fixa `p`: a atual em azul; coroa quando completa
static void DesenharAba(u8 p, bool8 atual, const u8 *nome, bool8 coroa)
{
    u16 x = ABA_X0 + p * ABA_PASSO;

    FillWindowPixelRect(WIN_ABAS, PIXEL_FILL(atual ? COR_BARRA : COR_ABA), x, 1, ABA_LARGURA, 14);
    AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL, x + ABA_TEXTO_DX, ABA_TEXTO_Y, 0, 0,
                                 atual ? sCor_AbaAtual : sCor_Aba, TEXT_SKIP_DRAW, nome);
    if (coroa)
        BlitIcone(WIN_ABAS, ICONE_COROA, x + ABA_COROA_DX, ABA_COROA_Y);
}

static void TerminarFaixa(void)
{
    PutWindowTilemap(WIN_ABAS);
    CopyWindowToVram(WIN_ABAS, COPYWIN_FULL);
}

// As abas do mapa, cada uma na sua vaga fixa; coroa na aba com tudo capturado
static void DesenharAbas(struct DexNavTela *t)
{
    u8 p, capturados, total;

    FillWindowPixelBuffer(WIN_ABAS, PIXEL_FILL(COR_FAIXA_ABAS));
    for (p = 0; p < t->nAbas; p++)
    {
        ContarEspecies(t, t->abas[p], &capturados, &total);
        DesenharAba(p, p == t->abaPos, sNomeDaAba[t->abas[p]], total != 0 && capturados == total);
    }
    TerminarFaixa();
}

// Lista: as abas KANTO e SEVII (coroa na região com todos os mapas completos)
static void DesenharAbasLista(struct DexNavTela *t)
{
    u8 r, completos, total;

    FillWindowPixelBuffer(WIN_ABAS, PIXEL_FILL(COR_FAIXA_ABAS));
    for (r = DEXNAV_REGION_KANTO; r <= DEXNAV_REGION_SEVII; r++)
    {
        ContarRegiao(t, r, &completos, &total);
        DesenharAba(r, r == t->regiao, sNomeDaRegiao[r], total != 0 && completos == total);
    }
    TerminarFaixa();
}

// Busca: os títulos das colunas, nas mesmas constantes das linhas
static void DesenharCabecalhoBusca(struct DexNavTela *t)
{
    FillWindowPixelBuffer(WIN_ABAS, PIXEL_FILL(COR_FAIXA_ABAS));
    if (t->buscaPasso == DEXNAV_SEARCH_CHOOSE)
    {
        AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL, ESC_NOME_X, ABA_TEXTO_Y, 0, 0, sCor_Cabecalho,
                                     TEXT_SKIP_DRAW, gText_DexNav_ColPokemon);
        AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL,
                                     ESC_MAPAS_FIM - GetStringWidth(FONT_NORMAL, gText_DexNav_ColMapas, 0),
                                     ABA_TEXTO_Y, 0, 0, sCor_Cabecalho, TEXT_SKIP_DRAW, gText_DexNav_ColMapas);
    }
    else
    {
        AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL, RES_NOME_X, ABA_TEXTO_Y, 0, 0, sCor_Cabecalho,
                                     TEXT_SKIP_DRAW, gText_DexNav_ColMapa);
        AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL,
                                     RES_CHANCE_FIM - GetStringWidth(FONT_NORMAL, gText_DexNav_ColChance, 0),
                                     ABA_TEXTO_Y, 0, 0, sCor_Cabecalho, TEXT_SKIP_DRAW, gText_DexNav_ColChance);
        AddTextPrinterParameterized4(WIN_ABAS, FONT_NORMAL, RES_HORARIO_X, ABA_TEXTO_Y, 0, 0, sCor_Cabecalho,
                                     TEXT_SKIP_DRAW, gText_DexNav_ColHorario);
    }
    TerminarFaixa();
}

// Chance x 10 em "%": "50%", "2,5%"
static void FormatarChance(u8 *dest, u16 rateX10)
{
    dest = ConvertIntToDecimalStringN(dest, rateX10 / 10, STR_CONV_MODE_LEFT_ALIGN, 3);
    if (rateX10 % 10 != 0)
    {
        *dest++ = CHAR_COMMA;
        dest = ConvertIntToDecimalStringN(dest, rateX10 % 10, STR_CONV_MODE_LEFT_ALIGN, 1);
    }
    *dest++ = CHAR_PERCENT;
    *dest = EOS;
}

static bool8 FoiVisto(u16 species)
{
    u16 dex = SpeciesToNationalPokedexNum(species);

    return GetSetPokedexFlag(dex, FLAG_GET_CAUGHT) || GetSetPokedexFlag(dex, FLAG_GET_SEEN);
}

// As cores do texto da linha: fundo amarelo na selecionada (e o retângulo amarelo pintado), letra normal ou cinza
static void CoresDaLinha(u8 *cor, bool8 selecionada, bool8 cinza, u16 y, u8 altura)
{
    cor[0] = selecionada ? COR_SELECAO : COR_FUNDO;
    cor[1] = cinza ? COR_CINZA : COR_TEXTO;
    cor[2] = COR_SOMBRA;
    if (selecionada)
        FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(COR_SELECAO), SELECAO_X, y, SELECAO_FIM - SELECAO_X, altura);
}

// O ícone do Pokémon da linha (em silhueta se nunca visto; o selecionado se mexe), na frente do fundo da linha
static void CriarIcone(struct DexNavTela *t, u8 slot, u16 species, bool8 selecionada, u16 y)
{
    u8 spriteId;

    spriteId = CreateMonIcon(species, selecionada ? SpriteCB_MonIcon : SpriteCallbackDummy,
                             COL_ICONE_X + 16, LISTA_TOPO_TILES * 8 + y + LINHA_ICONE_DY, 0, 0, FALSE);
    if (spriteId >= MAX_SPRITES)
        return;
    gSprites[spriteId].oam.priority = 0;
    if (!FoiVisto(species))
        gSprites[spriteId].oam.paletteNum = IndexOfSpritePaletteTag(TAG_SILHUETA);
    t->icones[slot] = spriteId;
}

static void DestruirIcones(struct DexNavTela *t)
{
    u8 i;

    for (i = 0; i < ICONES_MAX; i++)
    {
        if (t->icones[i] != ICONE_NENHUM)
            DestroyMonIcon(&gSprites[t->icones[i]]);
        t->icones[i] = ICONE_NENHUM;
    }
}

// Uma linha de Pokémon, coluna por coluna (COL_*): marca, nome, chance (à direita), "Nv." e os níveis (à direita)
static void DesenharLinhaMon(struct DexNavTela *t, u16 linha, u16 y)
{
    const struct DexNavEntry *e = &t->entries[t->linhas[linha].idx];
    u16 dex = SpeciesToNationalPokedexNum(e->species);
    bool8 capturado = GetSetPokedexFlag(dex, FLAG_GET_CAUGHT);
    bool8 visto = capturado || GetSetPokedexFlag(dex, FLAG_GET_SEEN);
    bool8 selecionada = linha == t->cursor;
    u8 cor[3], corNome[3], texto[12];

    CoresDaLinha(cor, selecionada, FALSE, y, LINHA_MON_ALTURA);
    corNome[0] = cor[0];
    corNome[1] = visto ? COR_TEXTO : COR_CINZA;
    corNome[2] = COR_SOMBRA;

    BlitIcone(WIN_LISTA, capturado ? ICONE_CAPTURADO : (visto ? ICONE_VISTO : ICONE_NUNCA_VISTO), COL_MARCA_X,
              y + LINHA_MARCA_DY);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NOME_X, y + LINHA_TEXTO_DY, 0, 0, corNome, TEXT_SKIP_DRAW,
                                 visto ? gSpeciesNames[e->species] : gText_DexNav_Desconhecido);

    FormatarChance(texto, DexNav_RateForPeriods(e, t->periods));
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_CHANCE_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);

    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_X, y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW,
                                 gText_DexNav_Nivel);
    ConvertIntToDecimalStringN(texto, e->minLevel, STR_CONV_MODE_LEFT_ALIGN, 3);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_MIN_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);
    if (e->maxLevel != e->minLevel)
    {
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_TRACO_X, y + LINHA_TEXTO_DY, 0, 0, cor,
                                     TEXT_SKIP_DRAW, sText_Traco);
        ConvertIntToDecimalStringN(texto, e->maxLevel, STR_CONV_MODE_LEFT_ALIGN, 3);
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NIVEL_MAX_X, y + LINHA_TEXTO_DY, 0, 0, cor,
                                     TEXT_SKIP_DRAW, texto);
    }
}

// Uma linha da lista de mapas, coluna por coluna (LST_*): nome, barra (trilho fixo, cheia na proporção capturados/total;
// dourada no mapa completo), coroa e contador à direita. Não visitado: nome cinza, barra vazia e "?/?". Visitado mas
// sem nenhum encontro agora (câmara de Tanoby trancada): o nome normal, barra vazia e "?/?" em cinza.
static void DesenharLinhaMapa(struct DexNavTela *t, u16 linha, u16 y)
{
    u8 texto[12];
    u8 cor[3];
    u8 i = t->linhas[linha].idx;
    bool8 visitado = DexNav_IsVisited(i);
    bool8 completo = MapaCompleto(t, i);

    CoresDaLinha(cor, linha == t->cursor, !visitado, y, LINHA_CURTA_ALTURA);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, LST_NOME_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, cor,
                                 TEXT_SKIP_DRAW, gDexNavMaps[i].name);
    FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(COR_ABA), LST_BARRA_X, y + LST_BARRA_DY, LST_BARRA_LARGURA, LST_BARRA_ALTURA);
    if (visitado && t->mapTotal[i] != 0 && t->mapCapturados[i] != 0)
    {
        FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(completo ? COR_OURO : COR_BARRA), LST_BARRA_X, y + LST_BARRA_DY,
                            LST_BARRA_LARGURA * t->mapCapturados[i] / t->mapTotal[i], LST_BARRA_ALTURA);
    }
    if (completo)
    {
        BlitIcone(WIN_LISTA, ICONE_COROA, LST_COROA_X, y + LST_COROA_DY);
        StringCopy(texto, gText_DexNav_Completo);
    }
    else if (MapaConhecido(t, i))
    {
        FormatarContador(texto, t->mapCapturados[i], t->mapTotal[i]);
    }
    else
    {
        StringCopy(texto, gText_DexNav_Interrogacao);
    }
    cor[1] = MapaConhecido(t, i) ? COR_TEXTO : COR_CINZA;
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, LST_CONTADOR_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_CURTA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);
}

// Uma espécie da escolha da busca (ESC_*): marca, número da Pokédex Nacional e nome; à direita, em quantos mapas aparece
static void DesenharLinhaEspecie(struct DexNavTela *t, u16 linha, u16 y)
{
    u16 species = t->linhas[linha].idx;
    u16 dex = SpeciesToNationalPokedexNum(species);
    u8 cor[3], texto[8];
    u8 marca = GetSetPokedexFlag(dex, FLAG_GET_CAUGHT) ? ICONE_CAPTURADO : ICONE_VISTO;

    CoresDaLinha(cor, linha == t->cursor, FALSE, y, LINHA_MON_ALTURA);
    BlitIcone(WIN_LISTA, marca, COL_MARCA_X, y + LINHA_MARCA_DY);
    ConvertIntToDecimalStringN(texto, dex, STR_CONV_MODE_LEADING_ZEROS, 3);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, ESC_NUM_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, ESC_NOME_X, y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW,
                                 gSpeciesNames[species]);
    ConvertIntToDecimalStringN(texto, t->especieMapas[dex], STR_CONV_MODE_LEFT_ALIGN, 3);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, ESC_MAPAS_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);
}

// Um mapa do resultado da busca (RES_*): nome ("??????" em cinza se não visitado), chance à direita e horário; a
// chance e o horário em cinza (como a linha "+N à noite") quando a espécie não aparece agora nesse mapa
static void DesenharLinhaResultado(struct DexNavTela *t, u16 linha, u16 y)
{
    const struct DexNavResultado *r = &t->resultados[t->linhas[linha].idx];
    bool8 visitado = DexNav_IsVisited(r->mapIndex);
    u8 cor[3], texto[12];

    CoresDaLinha(cor, linha == t->cursor, !visitado, y, LINHA_CURTA_ALTURA);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, RES_NOME_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, cor,
                                 TEXT_SKIP_DRAW, visitado ? gDexNavMaps[r->mapIndex].name : gText_DexNav_Desconhecido);
    cor[1] = ResultadoAgora(t, r) ? COR_TEXTO : sCor_Extra[1];
    FormatarChance(texto, r->rateX10);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, RES_CHANCE_FIM - GetStringWidth(FONT_NORMAL, texto, 0),
                                 y + LINHA_CURTA_TEXTO_DY, 0, 0, cor, TEXT_SKIP_DRAW, texto);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, RES_HORARIO_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, cor,
                                 TEXT_SKIP_DRAW, sNomeDoHorario[r->periods & DEXNAV_PERIOD_ALL]);
}

// Título da seção de um jeito de encontrar (as varas no modo mapa; todos na busca), com um fio até o fim da linha
static void DesenharLinhaSecao(struct DexNavTela *t, u16 linha, u16 y)
{
    const u8 *nome = sNomeDoMetodo[t->linhas[linha].idx];
    u16 fimTexto = SECAO_X + GetStringWidth(FONT_NORMAL, nome, 0) + 4;

    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, SECAO_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, sCor_Secao,
                                 TEXT_SKIP_DRAW, nome);
    if (fimTexto < SELECAO_FIM)
        FillWindowPixelRect(WIN_LISTA, PIXEL_FILL(COR_DIVISOR), fimTexto, y + LINHA_SECAO_ALTURA / 2, SELECAO_FIM - fimTexto, 1);
}

// "+N à noite" (de dia, de manhã, à tarde ou em outros horários), na coluna do nome
static void DesenharLinhaExtra(struct DexNavTela *t, u16 y)
{
    const u8 *texto;

    switch (t->extraPeriods)
    {
    case DEXNAV_PERIOD_NIGHT:
        texto = gText_DexNav_MaisNoite;
        break;
    case DEXNAV_PERIOD_MORNING | DEXNAV_PERIOD_DAY:
        texto = gText_DexNav_MaisDia;
        break;
    case DEXNAV_PERIOD_MORNING:
        texto = gText_DexNav_MaisManha;
        break;
    case DEXNAV_PERIOD_DAY:
        texto = gText_DexNav_MaisTarde;
        break;
    default:
        texto = gText_DexNav_MaisOutros;
        break;
    }
    ConvertIntToDecimalStringN(gStringVar1, t->extraN, STR_CONV_MODE_LEFT_ALIGN, 2);
    StringExpandPlaceholders(gStringVar4, texto);
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NOME_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, sCor_Extra,
                                 TEXT_SKIP_DRAW, gStringVar4);
}

// "Nenhum agora": a aba só tem espécies de outro período (a linha extra, logo abaixo, diz quantas e quando)
static void DesenharLinhaVazia(u16 y)
{
    AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_NOME_X, y + LINHA_CURTA_TEXTO_DY, 0, 0, sCor_Extra,
                                 TEXT_SKIP_DRAW, gText_DexNav_NenhumAgora);
}

// A mensagem da lista vazia de cada modo
static const u8 *TextoDaListaVazia(struct DexNavTela *t)
{
    if (t->modo != DEXNAV_MODE_SEARCH)
        return gText_DexNav_Nenhum;
    return t->buscaPasso == DEXNAV_SEARCH_CHOOSE ? gText_DexNav_BuscaVazia : gText_DexNav_NenhumMapa;
}

// As linhas visíveis a partir de `topo` (até LISTA_ALTURA), os ícones delas e as setas de rolagem; o título da seção
// que rolou para cima fica fixo no alto (SecaoFixa)
static void DesenharLista(struct DexNavTela *t)
{
    u8 slot = 0;
    u16 i, y = 0, altura, fixa = SecaoFixa(t);
    const u8 *vazia;

    DestruirIcones(t);
    FillWindowPixelBuffer(WIN_LISTA, PIXEL_FILL(COR_FUNDO));
    if (t->nLinhas == 0)
    {
        vazia = TextoDaListaVazia(t);
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL,
                                     (DISPLAY_WIDTH - GetStringWidth(FONT_NORMAL, vazia, 0)) / 2,
                                     (LISTA_ALTURA - 16) / 2, 0, 0, sCor_Extra, TEXT_SKIP_DRAW, vazia);
    }
    if (fixa != LINHA_NENHUMA)
    {
        DesenharLinhaSecao(t, fixa, 0);
        y = LINHA_SECAO_ALTURA;
    }
    for (i = t->topo; i < t->nLinhas; i++)
    {
        altura = AlturaDaLinha(t->linhas[i].tipo);
        if (y + altura > LISTA_ALTURA)
            break;
        switch (t->linhas[i].tipo)
        {
        case LINHA_MON:
            DesenharLinhaMon(t, i, y);
            if (slot < ICONES_MAX)
                CriarIcone(t, slot++, t->entries[t->linhas[i].idx].species, i == t->cursor, y);
            break;
        case LINHA_ESPECIE:
            DesenharLinhaEspecie(t, i, y);
            if (slot < ICONES_MAX)
                CriarIcone(t, slot++, t->linhas[i].idx, i == t->cursor, y);
            break;
        case LINHA_MAPA:
            DesenharLinhaMapa(t, i, y);
            break;
        case LINHA_RESULTADO:
            DesenharLinhaResultado(t, i, y);
            break;
        case LINHA_SECAO:
            DesenharLinhaSecao(t, i, y);
            break;
        case LINHA_VAZIA:
            DesenharLinhaVazia(y);
            break;
        default:
            DesenharLinhaExtra(t, y);
            break;
        }
        y += altura;
    }
    if (t->topo > 0)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_SETA_X, 0, 0, 0, sCor_Seta, TEXT_SKIP_DRAW,
                                     sText_SetaCima);
    if (i < t->nLinhas)
        AddTextPrinterParameterized4(WIN_LISTA, FONT_NORMAL, COL_SETA_X, LISTA_ALTURA - 16, 0, 0, sCor_Seta,
                                     TEXT_SKIP_DRAW, sText_SetaBaixo);
    PutWindowTilemap(WIN_LISTA);
    CopyWindowToVram(WIN_LISTA, COPYWIN_FULL);
}

// Uma parte do rodapé, depois do separador (se já tem alguma antes)
static u8 *JuntarRodape(u8 *inicio, u8 *fim, const u8 *parte)
{
    if (fim != inicio)
        fim = StringCopy(fim, sText_SeparadorRodape);
    return StringCopy(fim, parte);
}

// Os botões do modo (FONT_SMALL): "L/R aba" só quando o mapa tem mais de uma aba; B sai na primeira tela e volta
// nas outras
static void DesenharRodape(struct DexNavTela *t)
{
    u8 *s = gStringVar4;

    *s = EOS;
    switch (t->modo)
    {
    case DEXNAV_MODE_MAP:
        if (t->nAbas >= 2)
            s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeAba);
        s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeMapas);
        s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeBusca);
        break;
    case DEXNAV_MODE_LIST:
        s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeAbrir);
        s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeRegiao);
        s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeBusca);
        break;
    default:
        // lista vazia (nada visto ainda): só o que funciona
        if (t->nLinhas != 0)
        {
            s = JuntarRodape(gStringVar4, s, t->buscaPasso == DEXNAV_SEARCH_CHOOSE ? gText_DexNav_RodapeBuscar
                                                                                   : gText_DexNav_RodapeAbrir);
            s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapePagina);
        }
        s = JuntarRodape(gStringVar4, s, gText_DexNav_RodapeMapas);
        break;
    }
    JuntarRodape(gStringVar4, s, t->nPilha != 0 ? gText_DexNav_RodapeVoltar : gText_DexNav_RodapeSair);
    FillWindowPixelBuffer(WIN_RODAPE, PIXEL_FILL(COR_SOMBRA_BARRA));
    AddTextPrinterParameterized4(WIN_RODAPE, FONT_SMALL, RODAPE_X, RODAPE_Y, 0, 0, sCor_Rodape, TEXT_SKIP_DRAW,
                                 gStringVar4);
    PutWindowTilemap(WIN_RODAPE);
    CopyWindowToVram(WIN_RODAPE, COPYWIN_FULL);
}

// --- esteira --------------------------------------------------------------------------------------------------------

// TEST_CMD_DEXNAV_STATE (o formato de cada `what` está em include/dexnav.h)
u32 DexNav_TestGetState(u8 what)
{
    struct DexNavTela *t = sDexNav;
    const struct DexNavResultado *r;
    u8 aba, cursor8, completos = 0, total = 0;
    u16 cursor = 0, selecionaveis = 0, i, idx;

    if (t == NULL)
        return 0xFFFFFFFF;
    switch (t->modo)
    {
    case DEXNAV_MODE_MAP:
        aba = t->nAbas != 0 ? t->abas[t->abaPos] : 0xFF;
        break;
    case DEXNAV_MODE_LIST:
        aba = t->regiao;
        ContarRegiao(t, t->regiao, &completos, &total);
        break;
    default:
        aba = t->buscaPasso;
        break;
    }
    for (i = 0; i < t->nLinhas; i++)
    {
        if (!Selecionavel(t->linhas[i].tipo))
            continue;
        if (i < t->cursor)
            cursor++;
        selecionaveis++;
    }
    idx = t->cursor < t->nLinhas ? t->linhas[t->cursor].idx : 0;
    cursor8 = cursor > 0xFF ? 0xFF : cursor;
    switch (what)
    {
    case 0:
        return t->modo | aba << 8 | cursor8 << 16 | t->mapIndex << 24;
    case 1:
        return t->inputReady | t->abasMask << 8 | t->nMons << 16 | (t->topo & 0xFF) << 24;
    case 2:
        return t->capturadosMapa | t->totalMapa << 8 | t->capturadosAba << 16 | t->totalAba << 24;
    case 3:
        return t->extraN | t->extraPeriods << 8 | t->periods << 16;
    case 4:
        return cursor | (u32)selecionaveis << 16;
    case 5:
        return t->nPilha | completos << 8 | total << 16;
    case 6:
        return t->species | (u32)t->nResultados << 16;
    case 7:
        if (t->cursor >= t->nLinhas)
            return 0xFFFFFFFF;
        switch (t->linhas[t->cursor].tipo)
        {
        case LINHA_MAPA:
            return idx | DexNav_IsVisited(idx) << 8 | t->mapCapturados[idx] << 16 | (u32)t->mapTotal[idx] << 24;
        case LINHA_ESPECIE:
            return idx | (u32)t->especieMapas[SpeciesToNationalPokedexNum(idx)] << 16;
        case LINHA_RESULTADO:
            r = &t->resultados[idx];
            return r->mapIndex | r->method << 8 | r->periods << 16 | (u32)DexNav_IsVisited(r->mapIndex) << 24;
        }
        return 0xFFFFFFFF;
    }
    return 0xFFFFFFFF;
}
