#ifndef GUARD_SALA_TROFEUS_H
#define GUARD_SALA_TROFEUS_H

#include "global.h"
#include "constants/sala_trofeus.h"

// Sala de troféus da Ilha Sete (POK-51, spec 2026-11-06-casas-familia-sombra-design.md §5).
// Taça de cada aba das conquistas pela % de feitas/válidas (válidas = ativas e não perdidas).
#define TACA_BRONZE_PCT 34
#define TACA_PRATA_PCT  67

u8 SalaTrofeus_NivelDaTaca(u8 feitas, u8 validas);

#endif // GUARD_SALA_TROFEUS_H
