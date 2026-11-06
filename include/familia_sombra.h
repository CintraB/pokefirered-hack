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

// Batalhas (Task 3)
struct Pokemon;
bool8 FamiliaSombra_EhBatalhaDaFamilia(void);
bool8 FamiliaSombra_ItemProtegido(void);
u8 FamiliaSombra_CriarTime(struct Pokemon *party, u16 trainerId);

// Andares 4-5, efeito de filme e o chefe (Task 4)
bool8 FamiliaSombra_EhChefe(void);
bool8 FamiliaSombra_EhAndarEscuro(void);
u8 FamiliaSombra_NivelSelvagem(void);
void FamiliaSombra_CriarSelvagem(u8 level);
void FamiliaSombra_PaletaNoir(u16 *pal, u16 count);

// Specials (VAR_RESULT)
void FamiliaSombra_GetEstado(void);
void FamiliaSombra_GetOcupacao(void);
void FamiliaSombra_SortearPedagio(void);
void FamiliaSombra_IniciarChefe(void);

#endif // GUARD_FAMILIA_SOMBRA_H
