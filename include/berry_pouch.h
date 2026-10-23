#ifndef GUARD_BERRY_POUCH_H
#define GUARD_BERRY_POUCH_H

#include "task.h"

// Bytes per berry list entry (sListMenuStrbuf in berry_pouch.c): {FONT_SMALL}{NO}{CLEAR 0x01}, 2 digits,
// space, {FONT_NORMAL}, name and EOS take 15 bytes plus the name. 28 fits a 13-letter berry name (the
// original 27 only fit 12); the entry is copied whole to gStringVar1[32] (CopySelectedListMenuItemName).
#define BERRY_POUCH_LIST_STRBUF_SIZE 28

enum BerryPouchType
{
    BERRYPOUCH_FROMFIELD,
    BERRYPOUCH_FROMPARTYGIVE,
    BERRYPOUCH_FROMMARTSELL,
    BERRYPOUCH_FROMPOKEMONSTORAGEPC,
    BERRYPOUCH_FROMBATTLE,
    BERRYPOUCH_FROMBERRYCRUSH,
    BERRYPOUCH_NA
};

void BerryPouch_StartFadeToExitCallback(u8 taskId);
void BerryPouch_SetExitCallback(void (*exitCallback)(void));
void InitBerryPouch(u8 type, void (*savedCallback)(void), u8 allowSelect);
void DisplayItemMessageInBerryPouch(u8 taskId, u8 fontId, const u8 * str, TaskFunc followUpFunc);
void Task_BerryPouch_DestroyDialogueWindowAndRefreshListMenu(u8 taskId);
void BerryPouch_CursorResetToTop(void);

#endif //GUARD_BERRY_POUCH_H
