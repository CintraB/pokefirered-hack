#ifndef GUARD_FOLLOWER_H
#define GUARD_FOLLOWER_H

#include "global.h"
#include "sprite.h"

// Pokémon seguidor (POK-48). Esta parte só tem os dados por espécie; o objeto em campo vem depois.
//
// Um único graphicsId (OBJ_EVENT_GFX_FOLLOWER) serve a todas as espécies: as imagens e a paleta são
// escolhidas em tempo de execução por gFollowerSpecies (src/data/object_events/follower_species.h, gerado por
// tools/seguidores/converter.py a partir do pacote HGSS do Veekun).
//
// Folha de cada espécie: 8 quadros 32x32 (sul, norte, oeste, leste; 2 por direção; o leste tem desenho próprio).
// A paleta shiny usa os mesmos índices da normal.
struct FollowerSpecies
{
    u16 species;
    const struct SpriteFrameImage *images;
    const u16 *palette;
    const u16 *shinyPalette;
};

#define FOLLOWER_SPECIES_COUNT 12

extern const struct FollowerSpecies gFollowerSpecies[FOLLOWER_SPECIES_COUNT];

// NULL se a espécie não segue o jogador (não está em gFollowerSpecies).
const struct FollowerSpecies *Follower_GetSpeciesInfo(u16 species);

#endif // GUARD_FOLLOWER_H
