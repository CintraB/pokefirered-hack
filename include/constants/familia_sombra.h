#ifndef GUARD_CONSTANTS_FAMILIA_SOMBRA_H
#define GUARD_CONSTANTS_FAMILIA_SOMBRA_H

// POK-51: Família Sombra, a máfia do prédio da Rota 23.
#define FAMILIA_OCUPACOES_TOTAL     4  // chefes possíveis
#define FAMILIA_OCUPACOES_ATIVAS    4  // ocupações ligadas (a parte 2 ligou a 3 e a 4)
#define FAMILIA_MEIOS_DIAS_RETORNO  7  // meios-dias do relógio da hack = entre 3h00 e 3h30 jogadas (a queda guarda o meio-dia inteiro)
#define FAMILIA_PEDAGIO             1000

#define FAMILIA_ESTADO_FECHADO      0  // antes da 8ª insígnia
#define FAMILIA_ESTADO_ATIVA        1  // chefe ativo, prédio cheio
#define FAMILIA_ESTADO_SEM_CHEFE    2  // chefe vencido, esperando reforços
#define FAMILIA_ESTADO_ENCERRADA    3  // o 4º chefe caiu: a polícia fechou o prédio para sempre (final; a queda dele fica gravada, mas nada a lê mais)

// A IA dos chefes (POK-32/46), a mesma dos 12 treinadores-slot: o chefe a usa mesmo sendo encontro capturável.
#define FAMILIA_AI_CHEFE (AI_SCRIPT_CHECK_BAD_MOVE | AI_SCRIPT_TRY_TO_FAINT | AI_SCRIPT_CHECK_VIABILITY \
                        | AI_SCRIPT_SETUP_FIRST_TURN | AI_SCRIPT_HP_AWARE)

#endif // GUARD_CONSTANTS_FAMILIA_SOMBRA_H
