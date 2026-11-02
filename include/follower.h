#ifndef GUARD_FOLLOWER_H
#define GUARD_FOLLOWER_H

#include "global.h"
#include "sprite.h"
#include "constants/event_object_movement.h"
#include "constants/event_objects.h"

// Pokémon seguidor (POK-48): o 1º da equipe anda atrás do jogador no campo (src/follower.c).
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

// localId do objeto do seguidor: fora dos templates dos mapas (localId = índice + 1, no máximo
// OBJECT_EVENT_TEMPLATES_COUNT = 64) e abaixo de LOCALID_PLAYER (0xFF)
#define OBJ_EVENT_ID_FOLLOWER 0xFE

// Animação parada: os 2 quadros da direção alternam a cada FOLLOWER_IDLE_FRAMES quadros (o "respirar" do HGSS)
#define FOLLOWER_IDLE_FRAMES 20

// Animações paradas em sAnimTable_Follower, depois das 20 padrão (sul, norte, oeste, leste)
#define FOLLOWER_ANIM_IDLE_SOUTH (ANIM_STD_COUNT + 0)
#define FOLLOWER_ANIM_IDLE_NORTH (ANIM_STD_COUNT + 1)
#define FOLLOWER_ANIM_IDLE_WEST  (ANIM_STD_COUNT + 2)
#define FOLLOWER_ANIM_IDLE_EAST  (ANIM_STD_COUNT + 3)

extern const struct FollowerSpecies gFollowerSpecies[FOLLOWER_SPECIES_COUNT];

struct ObjectEvent;

// NULL se a espécie não segue o jogador (não está em gFollowerSpecies, ou SPECIES_NONE).
const struct FollowerSpecies *Follower_GetSpeciesInfo(u16 species);

// Opção "Seguidor: Sim/Não" do menu de Opções (SaveBlock2.optionsFollowerOff, 0 = Sim)
bool8 Follower_IsEnabled(void);

// Opção Sim, 1º da equipe não-ovo com PS > 0 e espécie na tabela, a pé (sem bicicleta/surf), fora do replay do
// Quest Log e de link, mapa sem objeto que use o slot de paleta do seguidor e com objeto livre para ele.
bool8 Follower_ShouldExist(void);

// Cria (ou recria) o seguidor atrás do jogador se Follower_ShouldExist(); tile de trás ocupado ou bloqueado = no
// tile do jogador, escondido até o 1º passo.
void Follower_Spawn(void);
void Follower_Remove(void);
// Compara espécie/shiny/estado com o objeto atual: cria, apaga ou recria (no mesmo tile) se mudou.
void Follower_Refresh(void);

// Índice em gObjectEvents (OBJECT_EVENTS_COUNT se não existe)
u8 Follower_GetObjectEventId(void);
bool8 Follower_IsFollowerObject(const struct ObjectEvent *objectEvent);

// Ganchos do motor de objetos (event_object_movement.c): o sprite do seguidor acabou de ser criado (spawn ou volta ao
// campo) e precisa das imagens, da paleta e do callback da espécie; e a paleta recarregada do ROM (tom dia/noite).
void Follower_OnSpriteCreated(struct ObjectEvent *objectEvent, struct Sprite *sprite);
void Follower_ReloadPalette(void);

// Atalho TEST_CMD_FOLLOWER_STATE (include/test_hooks.h): 0 = existe | espécie << 8 | shiny << 24 | escondido << 25;
// 1 = x | y << 16 (s16, sem o MAP_OFFSET; 0xFFFFFFFE = não existe); 2 = direção | quadro parado << 8 | objetos com
// o localId do seguidor << 16; 0xFFFFFFFF fora do campo
u32 Follower_TestGetState(u8 what);

#endif // GUARD_FOLLOWER_H
