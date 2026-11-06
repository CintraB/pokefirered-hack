#ifndef GUARD_FAMILIA_SOMBRA_H
#define GUARD_FAMILIA_SOMBRA_H

#include "constants/familia_sombra.h"

u16 FamiliaSombra_MeiosDiasAgora(void);
u8 FamiliaSombra_Ocupacao(void);
u8 FamiliaSombra_Estado(void);
bool8 FamiliaSombra_ChefeAtivo(void);
void FamiliaSombra_Atualizar(void);
void FamiliaSombra_Repovoar(void);
void FamiliaSombra_ChefeCaiu(void);
bool8 FamiliaSombra_NoPredio(void);

// Specials (VAR_RESULT)
void FamiliaSombra_GetEstado(void);
void FamiliaSombra_GetOcupacao(void);

#endif // GUARD_FAMILIA_SOMBRA_H
