#ifndef GUARD_DAYCARE_CONSTANTS_H
#define GUARD_DAYCARE_CONSTANTS_H

// Parent compatibility scores
#define PARENTS_INCOMPATIBLE       0
#define PARENTS_LOW_COMPATIBILITY  20
#define PARENTS_MED_COMPATIBILITY  50
#define PARENTS_MAX_COMPATIBILITY  70

// Daycare state
#define DAYCARE_NO_MONS     0
#define DAYCARE_EGG_WAITING 1
#define DAYCARE_ONE_MON     2
#define DAYCARE_TWO_MONS    3

#define INHERITED_IV_COUNT 3
#define EGG_HATCH_LEVEL 5
#define EGG_GENDER_MALE 0x8000  // used to create a male egg from a female-only parent species (e.g. Nidoran)

// Genetic breeding (Hack 6, docs/superpowers/specs/2026-10-17-breeding-genetico-design.md).
// Every probability of the egg rules lives here (percentages); the test pipeline checks these
// values against the design (test/esteira/breeding.py).
// IVs, per stat:
#define BREED_IV_POWER_ITEM_CHANCE     90 // parent holding the stat's Power item: copy its IV exactly
#define BREED_IV_MUTATION_CHANCE        5 // otherwise: random 0-31
#define BREED_IV_ONE_PARENT_CHANCE     25 // otherwise: one parent's IV (50/50; Destiny Knot: the higher one)...
#define BREED_IV_ONE_PARENT_SPREAD      2 // ...+-2
#define BREED_IV_AVERAGE_SPREAD         3 // otherwise: parents' average (rounded up) +-3
#define BREED_IV_AVERAGE_SPREAD_KNOT    1 // ...+-1 when a parent holds the Destiny Knot
// Nature (nature = raised stat * 5 + lowered stat):
#define BREED_NATURE_EVERSTONE_CHANCE  70 // parent holding an Everstone passes its nature
#define BREED_NATURE_MUTATION_CHANCE   10 // otherwise: random nature; else raised/lowered stat each from a random parent
// Ability slot (species with two abilities):
#define BREED_ABILITY_MUTATION_CHANCE  10 // random slot
#define BREED_ABILITY_FATHER_CHANCE    60 // otherwise the father's slot, else the mother's
// Egg moves (each one a parent knows, independently):
#define BREED_EGG_MOVE_FATHER_CHANCE   60
#define BREED_EGG_MOVE_MOTHER_CHANCE   40
// Power items in battle: extra EVs in the item's stat per defeated mon (Speed is halved)
#define POWER_ITEM_EV_BONUS             8

#define DAYCARE_LEVEL_MENU_EXIT 5
#define DAYCARE_EXITED_LEVEL_MENU 2 // would be redundant with above if GF had used the same value

// Array buffers
#define EGG_MOVES_ARRAY_COUNT           10
#define EGG_LVL_UP_MOVES_ARRAY_COUNT    50

#endif //GUARD_DAYCARE_CONSTANTS_H
