#ifndef GUARD_CONQUISTAS_H
#define GUARD_CONQUISTAS_H

#include "global.h"
#include "constants/conquistas.h"

// Conquistas e diário de batalhas (POK-44), desenho em docs/superpowers/specs/2026-10-31-conquistas-e-diario-design.md.
//
// A tabela mora em src/data/conquistas/conquistas.json; o make gera, com tools/conquistas/gen_conquistas.py,
// src/data/conquistas_ids.h (CONQ_<ID>, CONQ_ABA_<ID>, DIARIO_EVT_<ID> e as contagens) e
// src/data/conquistas_tabela.h (as tabelas abaixo; só `const`, sem EWRAM). Os tipos e as larguras de texto
// ficam aqui: a checagem de texto da esteira (test/esteira/check_text.py) lê as constantes *_LARGURA.

// Larguras úteis (px, FONT_NORMAL, 1 linha). O nome de conquista com degraus traz {STR_VAR_1} no lugar do
// {N} do JSON; a medida usa "300" (o maior degrau).
#define CONQ_NOME_LARGURA    152
#define DIARIO_NOME_LARGURA  80
#define DIARIO_LOCAL_LARGURA 136

struct ConquistaPremio
{
    u16 item;
    u8 qtd;
};

// param / param2 / lista / degraus, por tipo:
//   FLAG          param = flag
//   FLAGS_TODAS   param = primeira flag, param2 = quantas (flags consecutivas)
//   DEX_TODOS     lista = espécies (SPECIES_*, termina em 0xFFFF), todas capturadas
//   DEX_KANTO     param = quantas de Kanto (151) capturadas
//   DEX_NACIONAL  param = quantas capturadas (as obtíveis no jogo)
//   NIVEL         param = nível mínimo de algum Pokémon (equipe ou PC)
//   AMIZADE_MAX   param = amizade (255) de algum Pokémon
//   GAME_STAT     param = GAME_STAT_*, param2 = valor mínimo
//   DINHEIRO      param = ₽ mínimos
//   HORAS         degraus = horas de jogo
//   VITORIAS      degraus = treinadores derrotados
//   SHINIES       degraus = shinies capturados/chocados
//   EVENTO        param = CONQ_EVT_*
// Com degraus, `numDegraus` > 0 e `slotDegrau` (0 a CONQ_MAX_DEGRAUS - 1) é o slot de progresso no save
// (campo `slot` do JSON, explícito e fixo: `degrauEntregue[slot]` em struct ConquistasSave);
// sem degraus `slotDegrau` é 0xFF. `premios` tem max(1, numDegraus) entradas (um prêmio por degrau).
struct Conquista
{
    const u8 *nome;
    u8 aba;
    u8 tipo;
    u8 numDegraus;
    u8 slotDegrau;
    bool8 perdivel;   // pode ser perdida num save que já passou da chance
    bool8 ativa;      // false = existe na tabela mas não aparece, não conta e não dispara (POK-42)
    u16 param2;
    u32 param;
    const u16 *lista;
    const u16 *degraus;
    const struct ConquistaPremio *premios;
};

// `treinadores` (TRAINER_*, termina em 0xFFFF) para o tipo TREINADOR; `especie` para o tipo LENDARIO.
struct DiarioEvento
{
    const u8 *nome;
    const u8 *local;
    u8 tipo;
    bool8 lider;
    bool8 rival;
    u16 especie;
    const u16 *treinadores;
};

extern const struct Conquista gConquistas[];
extern const struct DiarioEvento gDiarioEventos[];
extern const u8 *const gConquistasAbaNomes[];

// Estado no save (src/conquistas.c; struct ConquistasSave em gSaveBlock1Ptr->conquistas, struct DiarioSave em
// gSaveBlock2Ptr->diario). `num` é CONQ_<ID>; fora da tabela, as leituras dão 0 e as escritas não fazem nada.
bool8 Conquistas_NumValido(u8 num);              // num de uma conquista da tabela
void Conquistas_IniciarJogoNovo(void);           // zera as duas áreas e grava o marcador (origem: jogo novo)
u8 Conquistas_GetEstado(u8 num);                 // CONQ_PENDENTE / CONQ_FEITA / CONQ_PERDIDA
void Conquistas_Marcar(u8 num);                  // só PENDENTE -> FEITA (perdida nunca vira feita)
void Conquistas_Perder(u8 num);                  // só PENDENTE -> PERDIDA
bool8 Conquistas_Entregue(u8 num);               // prêmio já entregue
void Conquistas_SetEntregue(u8 num);
u8 Conquistas_DegrauEntregue(u8 num);            // degraus já entregues (0 sem degraus)
void Conquistas_SetDegrauEntregue(u8 num, u8 degrau);

// Regras de estado (src/conquistas.c; nada de regra fora de lá). Só as conquistas ativas contam.
void Conquistas_ChecarEstado(void);              // sem marcador, varre o save antigo antes; depois avalia os tipos de
                                                 // estado (NIVEL/AMIZADE_MAX só no time) e, com as 8 insígnias,
                                                 // perde `lider_um_pokemon` pendente
void Conquistas_VarrerSaveAntigo(void);          // uma vez por save sem marcador: grava o marcador (origem save antigo,
                                                 // resumo pendente) e reconhece o que o save prova, inclusive no PC
u8 Conquistas_DegrauAtual(u8 num);               // degraus alcançados (0 sem degraus); FEITA quando = numDegraus
bool8 Conquistas_Progresso(u8 num, u32 *atual, u32 *meta); // FALSE nas de sim/não; com degraus, meta = próximo degrau
u8 Conquistas_AvisosPendentes(void);             // feitas não entregues + degraus não entregues (1 com o resumo pendente)
void Conquistas_ContarAba(u8 aba, u8 *feitas, u8 *validas); // válidas = ativas e não perdidas

struct Pokemon;

// Gatilhos de evento (Task 4). Os arquivos do motor só chamam estes ganchos de uma linha; a regra fica em
// src/conquistas.c. Num save ainda sem marcador (antes da primeira checagem) eles não fazem nada: a varredura do
// save antigo reconhece depois o que o save prova (shinies, ovos, Elite 4).
// Ignoram link, Pokédude, tutorial do velho, Trainer Tower, e-Reader e Battle Tower (o FRLG não tem "recorded").
void Conquistas_Evento(u8 evento);               // marca as conquistas ativas de tipo EVENTO com param = evento
void Conquistas_PerderEvento(u8 evento);         // perde as mesmas (só as pendentes)
void Conquistas_OnNocaute(u8 battlerAtacante);   // Cmd_tryfaintmon, oponente desmaiou: soma ao Pokémon do jogador
                                                 // (gBattleStruct->conq*, pela personalidade)
void Conquistas_OnEficacia(u8 battlerAtacante, u16 multX10); // Cmd_typecalc: 40 (x4) com dano -> CONQ_EVT_GOLPE_X4
void Conquistas_OnFimDeBatalha(void);            // HandleEndTurn_FinishBattle, antes do script do campo (insígnia)
void Conquistas_OnCaptura(struct Pokemon *mon, u16 bola); // Cmd_givecaughtmon, antes do GiveMonToPlayer
void Conquistas_OnPokemonRecebido(struct Pokemon *mon);   // GiveMonToPlayer: não-ovo shiny soma shiniesObtidos
void Conquistas_OnOvoChocado(struct Pokemon *mon);        // AddHatchedMonToParty: shiny, 6 IVs 31

// Diário (src/diario.c). Só a primeira vitória/captura de cada evento entra; revanche nunca. Um lendário capturado
// depois de um DERROTOU troca a entrada, com ordem nova.
void Diario_OnFimDeBatalha(void);                   // chamado por Conquistas_OnFimDeBatalha (já sem as batalhas ignoradas)
const struct DiarioEntrada *Diario_GetEntrada(u8 evt); // NULL com o slot vazio (ordem 0) ou evt fora da tabela
u8 Diario_ListarEmOrdem(u8 *evts);                  // DIARIO_EVT_* preenchidos, em ordem crescente de `ordem`; devolve quantos

#endif // GUARD_CONQUISTAS_H
