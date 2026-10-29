#ifndef GUARD_FIELD_MOVE_RULES_H
#define GUARD_FIELD_MOVE_RULES_H

// POK-38: quem usa um golpe de HM no campo (PARTY_SIZE = ninguém).
u8 FindPartyMonForFieldMove(u16 move);
// Insígnia do golpe + alguém que use (FindPartyMonForFieldMove).
bool8 CanUseFieldMove(u16 move);

#endif // GUARD_FIELD_MOVE_RULES_H
