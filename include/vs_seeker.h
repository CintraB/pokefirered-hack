#ifndef GUARD_VS_SEEKER_H
#define GUARD_VS_SEEKER_H

#include "global.h"

// Linhas de sRematches (vs_seeker.c). A tabela gerada do POK-42 (REMATCH_TIER_ROWS) tem de bater: os dois lados
// conferem na compilação (STATIC_ASSERT em vs_seeker.c e em rematch_tier.c).
#define VS_SEEKER_REMATCH_ROWS 221

void Task_VsSeeker_0(u8 taskId);
void ClearRematchStateByTrainerId(void);
void ClearRematchStateOfLastTalked(void);
int GetRematchTrainerId(u16 trainerId);
s32 GetVsSeekerRematchRow(u16 trainerId);
bool8 UpdateVsSeekerStepCounter(void);
void MapResetTrainerRematches(u16 mapGroup, u16 mapNum);

#endif //GUARD_VS_SEEKER_H
