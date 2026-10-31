#ifndef GUARD_MAP_NAME_POPUP_H
#define GUARD_MAP_NAME_POPUP_H

#include "global.h"

void ShowMapNamePopup(bool32 palIntoFadedBuffer);
void DismissMapNamePopup(void);
bool32 IsMapNamePopupTaskActive(void);
void ShowFieldMessagePopup(const u8 *text);

#endif //GUARD_MAP_NAME_POPUP_H
