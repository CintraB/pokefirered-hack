#ifndef GUARD_MESTRE_GOLPES_H
#define GUARD_MESTRE_GOLPES_H

#include "global.h"

// Mestre dos Golpes da Rota 6 (POK-51, spec 2026-11-06-casas-familia-sombra-design.md §3).
// Lista os 15 golpes de tutor do FRLG numa ListMenu com rolagem; devolve em VAR_RESULT o id do tutor
// (TUTOR_MOVE_*, 0-14) ou MESTRE_GOLPES_CANCELOU. O ensino em si é o special original ChooseMonForMoveTutor.

#define MESTRE_GOLPES_CANCELOU 0xFF
#define MESTRE_GOLPES_PRECO    3000

void MestreGolpes_EscolherGolpe(void);

#endif // GUARD_MESTRE_GOLPES_H
