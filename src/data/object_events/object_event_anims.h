static const union AnimCmd sAnim_StayStill[] = {
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpFaceSouth[] = {
    ANIMCMD_FRAME(0, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpFaceNorth[] = {
    ANIMCMD_FRAME(1, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpFaceWest[] = {
    ANIMCMD_FRAME(2, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpFaceEast[] = {
    ANIMCMD_FRAME(2, 16, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoSouth[] = {
    ANIMCMD_FRAME(3, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(3, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoNorth[] = {
    ANIMCMD_FRAME(4, 8),
    ANIMCMD_FRAME(1, 8),
    ANIMCMD_FRAME(4, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoWest[] = {
    ANIMCMD_FRAME(5, 8),
    ANIMCMD_FRAME(2, 8),
    ANIMCMD_FRAME(6, 8),
    ANIMCMD_FRAME(2, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoEast[] = {
    ANIMCMD_FRAME(5, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(6, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 8, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastSouth[] = {
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(3, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastNorth[] = {
    ANIMCMD_FRAME(4, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(4, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastWest[] = {
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(6, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastEast[] = {
    ANIMCMD_FRAME(5, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(6, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFasterSouth[] = {
    ANIMCMD_FRAME(3, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_FRAME(3, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFasterNorth[] = {
    ANIMCMD_FRAME(4, 2),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_FRAME(4, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFasterWest[] = {
    ANIMCMD_FRAME(5, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_FRAME(6, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFasterEast[] = {
    ANIMCMD_FRAME(5, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(6, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastestSouth[] = {
    ANIMCMD_FRAME(3, 1),
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_FRAME(3, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastestNorth[] = {
    ANIMCMD_FRAME(4, 1),
    ANIMCMD_FRAME(1, 1),
    ANIMCMD_FRAME(4, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastestWest[] = {
    ANIMCMD_FRAME(5, 1),
    ANIMCMD_FRAME(2, 1),
    ANIMCMD_FRAME(6, 1),
    ANIMCMD_FRAME(2, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_QuintyPlumpGoFastestEast[] = {
    ANIMCMD_FRAME(5, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(6, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 1, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FaceSouth[] = {
    ANIMCMD_FRAME(0, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FaceNorth[] = {
    ANIMCMD_FRAME(1, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FaceWest[] = {
    ANIMCMD_FRAME(2, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FaceEast[] = {
    ANIMCMD_FRAME(2, 16, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoSouth[] = {
    ANIMCMD_FRAME(3, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(4, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoNorth[] = {
    ANIMCMD_FRAME(5, 8),
    ANIMCMD_FRAME(1, 8),
    ANIMCMD_FRAME(6, 8),
    ANIMCMD_FRAME(1, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoWest[] = {
    ANIMCMD_FRAME(7, 8),
    ANIMCMD_FRAME(2, 8),
    ANIMCMD_FRAME(8, 8),
    ANIMCMD_FRAME(2, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoEast[] = {
    ANIMCMD_FRAME(7, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(8, 8, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 8, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastSouth[] = {
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(4, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastNorth[] = {
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(6, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastWest[] = {
    ANIMCMD_FRAME(7, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(8, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastEast[] = {
    ANIMCMD_FRAME(7, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(8, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFasterSouth[] = {
    ANIMCMD_FRAME(3, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_FRAME(4, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFasterNorth[] = {
    ANIMCMD_FRAME(5, 2),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_FRAME(6, 2),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFasterWest[] = {
    ANIMCMD_FRAME(7, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_FRAME(8, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFasterEast[] = {
    ANIMCMD_FRAME(7, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(8, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastestSouth[] = {
    ANIMCMD_FRAME(3, 1),
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_FRAME(4, 1),
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastestNorth[] = {
    ANIMCMD_FRAME(5, 1),
    ANIMCMD_FRAME(1, 1),
    ANIMCMD_FRAME(6, 1),
    ANIMCMD_FRAME(1, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastestWest[] = {
    ANIMCMD_FRAME(7, 1),
    ANIMCMD_FRAME(2, 1),
    ANIMCMD_FRAME(8, 1),
    ANIMCMD_FRAME(2, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GoFastestEast[] = {
    ANIMCMD_FRAME(7, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(8, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 1, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

// POK-48: Pokémon seguidor. A folha tem 8 quadros: sul 0-1, norte 2-3, oeste 4-5, leste 6-7 (o leste tem desenho
// próprio, sem espelho). Parado mostra o 1º quadro da direção; andar alterna os dois, no ritmo de cada velocidade.
#define FOLLOWER_WALK_ANIM(name, frame, ticks) static const union AnimCmd name[] = {     ANIMCMD_FRAME(frame, ticks),     ANIMCMD_FRAME((frame) + 1, ticks),     ANIMCMD_JUMP(0), }

static const union AnimCmd sAnim_FollowerFaceSouth[] = {
    ANIMCMD_FRAME(0, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FollowerFaceNorth[] = {
    ANIMCMD_FRAME(2, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FollowerFaceWest[] = {
    ANIMCMD_FRAME(4, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FollowerFaceEast[] = {
    ANIMCMD_FRAME(6, 16),
    ANIMCMD_JUMP(0),
};

FOLLOWER_WALK_ANIM(sAnim_FollowerGoSouth, 0, 8);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoNorth, 2, 8);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoWest, 4, 8);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoEast, 6, 8);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastSouth, 0, 4);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastNorth, 2, 4);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastWest, 4, 4);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastEast, 6, 4);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFasterSouth, 0, 2);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFasterNorth, 2, 2);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFasterWest, 4, 2);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFasterEast, 6, 2);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastestSouth, 0, 1);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastestNorth, 2, 1);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastestWest, 4, 1);
FOLLOWER_WALK_ANIM(sAnim_FollowerGoFastestEast, 6, 1);
// Parado (o "respirar" do HGSS): os 2 quadros da direção, a cada FOLLOWER_IDLE_FRAMES (include/follower.h)
FOLLOWER_WALK_ANIM(sAnim_FollowerIdleSouth, 0, FOLLOWER_IDLE_FRAMES);
FOLLOWER_WALK_ANIM(sAnim_FollowerIdleNorth, 2, FOLLOWER_IDLE_FRAMES);
FOLLOWER_WALK_ANIM(sAnim_FollowerIdleWest, 4, FOLLOWER_IDLE_FRAMES);
FOLLOWER_WALK_ANIM(sAnim_FollowerIdleEast, 6, FOLLOWER_IDLE_FRAMES);

// For indicating a VS Seeker rematch
static const union AnimCmd sAnim_RaiseHand[] = {
    ANIMCMD_FRAME(9, 0),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_HoOhFlapWings[] = {
    ANIMCMD_FRAME(3, 8),
    ANIMCMD_FRAME(4, 8),
    ANIMCMD_FRAME(3, 8),
    ANIMCMD_FRAME(4, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_HoOhStayStill[] = {
    ANIMCMD_FRAME(3, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_SurfFaceSouth[] = {
    ANIMCMD_FRAME(0, 60),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_SurfFaceNorth[] = {
    ANIMCMD_FRAME(1, 60),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_SurfFaceWest[] = {
    ANIMCMD_FRAME(2, 60),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_SurfFaceEast[] = {
    ANIMCMD_FRAME(2, 60, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownFaceSouth[] = {
    ANIMCMD_FRAME(0, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownFaceNorth[] = {
    ANIMCMD_FRAME(1, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownFaceWest[] = {
    ANIMCMD_FRAME(2, 16),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownFaceEast[] = {
    ANIMCMD_FRAME(2, 16, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoSouth[] = {
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(4, 4),
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_FRAME(6, 4),
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoNorth[] = {
    ANIMCMD_FRAME(7, 4),
    ANIMCMD_FRAME(8, 4),
    ANIMCMD_FRAME(7, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(9, 4),
    ANIMCMD_FRAME(10, 4),
    ANIMCMD_FRAME(9, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoWest[] = {
    ANIMCMD_FRAME(11, 4),
    ANIMCMD_FRAME(12, 4),
    ANIMCMD_FRAME(11, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(13, 4),
    ANIMCMD_FRAME(14, 4),
    ANIMCMD_FRAME(13, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoEast[] = {
    ANIMCMD_FRAME(11, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(12, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(11, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(14, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastNorth[] = {
    ANIMCMD_FRAME(3, 2),
    ANIMCMD_FRAME(4, 2),
    ANIMCMD_FRAME(3, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_FRAME(5, 2),
    ANIMCMD_FRAME(6, 2),
    ANIMCMD_FRAME(5, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastSouth[] = {
    ANIMCMD_FRAME(7, 2),
    ANIMCMD_FRAME(8, 2),
    ANIMCMD_FRAME(7, 2),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_FRAME(9, 2),
    ANIMCMD_FRAME(10, 2),
    ANIMCMD_FRAME(9, 2),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastWest[] = {
    ANIMCMD_FRAME(11, 2),
    ANIMCMD_FRAME(12, 2),
    ANIMCMD_FRAME(11, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_FRAME(13, 2),
    ANIMCMD_FRAME(14, 2),
    ANIMCMD_FRAME(13, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastEast[] = {
    ANIMCMD_FRAME(11, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(12, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(11, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(14, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFasterNorth[] = {
    ANIMCMD_FRAME(3, 1),
    ANIMCMD_FRAME(4, 1),
    ANIMCMD_FRAME(3, 1),
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_FRAME(5, 1),
    ANIMCMD_FRAME(6, 1),
    ANIMCMD_FRAME(5, 1),
    ANIMCMD_FRAME(0, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFasterSouth[] = {
    ANIMCMD_FRAME(7, 1),
    ANIMCMD_FRAME(8, 1),
    ANIMCMD_FRAME(7, 1),
    ANIMCMD_FRAME(1, 1),
    ANIMCMD_FRAME(9, 1),
    ANIMCMD_FRAME(10, 1),
    ANIMCMD_FRAME(9, 1),
    ANIMCMD_FRAME(1, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFasterWest[] = {
    ANIMCMD_FRAME(11, 1),
    ANIMCMD_FRAME(12, 1),
    ANIMCMD_FRAME(11, 1),
    ANIMCMD_FRAME(2, 1),
    ANIMCMD_FRAME(13, 1),
    ANIMCMD_FRAME(14, 1),
    ANIMCMD_FRAME(13, 1),
    ANIMCMD_FRAME(2, 1),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFasterEast[] = {
    ANIMCMD_FRAME(11, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(12, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(11, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(14, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 1, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 1, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastestNorth[] = {
    ANIMCMD_FRAME(3, 0),
    ANIMCMD_FRAME(4, 0),
    ANIMCMD_FRAME(3, 0),
    ANIMCMD_FRAME(0, 0),
    ANIMCMD_FRAME(5, 0),
    ANIMCMD_FRAME(6, 0),
    ANIMCMD_FRAME(5, 0),
    ANIMCMD_FRAME(0, 0),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastestSouth[] = {
    ANIMCMD_FRAME(7, 0),
    ANIMCMD_FRAME(8, 0),
    ANIMCMD_FRAME(7, 0),
    ANIMCMD_FRAME(1, 0),
    ANIMCMD_FRAME(9, 0),
    ANIMCMD_FRAME(10, 0),
    ANIMCMD_FRAME(9, 0),
    ANIMCMD_FRAME(1, 0),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastestWest[] = {
    ANIMCMD_FRAME(11, 0),
    ANIMCMD_FRAME(12, 0),
    ANIMCMD_FRAME(11, 0),
    ANIMCMD_FRAME(2, 0),
    ANIMCMD_FRAME(13, 0),
    ANIMCMD_FRAME(14, 0),
    ANIMCMD_FRAME(13, 0),
    ANIMCMD_FRAME(2, 0),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_UnknownGoFastestEast[] = {
    ANIMCMD_FRAME(11, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(12, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(11, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(14, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(13, 0, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 0, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_SpinSouth[] = {
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_LOOP(1),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_SpinNorth[] = {
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_LOOP(1),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_SpinWest[] = {
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE), // Starts by facing East?
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_FRAME(2, 2),
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_LOOP(1),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_SpinEast[] = {
    ANIMCMD_FRAME(2, 2), // Starts by facing West?
    ANIMCMD_FRAME(0, 2),
    ANIMCMD_FRAME(2, 2, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 2),
    ANIMCMD_LOOP(1),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_ShakeHeadOrWalkInPlace[] = {
    ANIMCMD_FRAME(18, 16),
    ANIMCMD_FRAME(0, 16),
    ANIMCMD_FRAME(19, 16),
    ANIMCMD_FRAME(0, 32),
    ANIMCMD_LOOP(1),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_RunSouth[] = {
    ANIMCMD_FRAME(9, 5),
    ANIMCMD_FRAME(10, 3),
    ANIMCMD_FRAME(9, 5),
    ANIMCMD_FRAME(11, 3),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_RunNorth[] = {
    ANIMCMD_FRAME(12, 5),
    ANIMCMD_FRAME(13, 3),
    ANIMCMD_FRAME(12, 5),
    ANIMCMD_FRAME(14, 3),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_RunWest[] = {
    ANIMCMD_FRAME(15, 5),
    ANIMCMD_FRAME(16, 3),
    ANIMCMD_FRAME(15, 5),
    ANIMCMD_FRAME(17, 3),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_RunEast[] = {
    ANIMCMD_FRAME(15, 5, .hFlip = TRUE),
    ANIMCMD_FRAME(16, 3, .hFlip = TRUE),
    ANIMCMD_FRAME(15, 5, .hFlip = TRUE),
    ANIMCMD_FRAME(17, 3, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_FieldMove[] = {
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(4, 8),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_VSSeeker[] = {
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_FRAME(6, 4),
    ANIMCMD_LOOP(0),
    ANIMCMD_FRAME(7, 4),
    ANIMCMD_FRAME(8, 4),
    ANIMCMD_LOOP(6),
    ANIMCMD_FRAME(6, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_VSSeekerBike[] = {
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_LOOP(0),
    ANIMCMD_FRAME(4, 4),
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_LOOP(6),
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_GetOnOffSurfSouth[] = {
    ANIMCMD_FRAME(9, 32),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GetOnOffSurfNorth[] = {
    ANIMCMD_FRAME(10, 32),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GetOnOffSurfWest[] = {
    ANIMCMD_FRAME(11, 32),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_GetOnOffSurfEast[] = {
    ANIMCMD_FRAME(11, 32, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_BunnyHopBackWheelSouth[] = {
    ANIMCMD_FRAME(15, 4),
    ANIMCMD_FRAME(16, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopBackWheelNorth[] = {
    ANIMCMD_FRAME(19, 4),
    ANIMCMD_FRAME(20, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopBackWheelWest[] = {
    ANIMCMD_FRAME(23, 4),
    ANIMCMD_FRAME(24, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopBackWheelEast[] = {
    ANIMCMD_FRAME(23, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(24, 4, .hFlip = TRUE),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopFrontWheelSouth[] = {
    ANIMCMD_FRAME(17, 4),
    ANIMCMD_FRAME(18, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopFrontWheelNorth[] = {
    ANIMCMD_FRAME(21, 4),
    ANIMCMD_FRAME(22, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopFrontWheelWest[] = {
    ANIMCMD_FRAME(25, 4),
    ANIMCMD_FRAME(26, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BunnyHopFrontWheelEast[] = {
    ANIMCMD_FRAME(25, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(26, 4, .hFlip = TRUE),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieBackWheelSouth[] = {
    ANIMCMD_FRAME(15, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieBackWheelNorth[] = {
    ANIMCMD_FRAME(19, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieBackWheelWest[] = {
    ANIMCMD_FRAME(23, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieBackWheelEast[] = {
    ANIMCMD_FRAME(23, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieFrontWheelSouth[] = {
    ANIMCMD_FRAME(17, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieFrontWheelNorth[] = {
    ANIMCMD_FRAME(21, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieFrontWheelWest[] = {
    ANIMCMD_FRAME(25, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_StandingWheelieFrontWheelEast[] = {
    ANIMCMD_FRAME(25, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_MovingWheelieSouth[] = {
    ANIMCMD_FRAME(27, 4),
    ANIMCMD_FRAME(16, 4),
    ANIMCMD_FRAME(28, 4),
    ANIMCMD_FRAME(16, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_MovingWheelieNorth[] = {
    ANIMCMD_FRAME(29, 4),
    ANIMCMD_FRAME(20, 4),
    ANIMCMD_FRAME(30, 4),
    ANIMCMD_FRAME(20, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_MovingWheelieWest[] = {
    ANIMCMD_FRAME(31, 4),
    ANIMCMD_FRAME(24, 4),
    ANIMCMD_FRAME(32, 4),
    ANIMCMD_FRAME(24, 4),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_MovingWheelieEast[] = {
    ANIMCMD_FRAME(31, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(24, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(32, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(24, 4, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_BerryTreeStage0[] = {
    ANIMCMD_FRAME(0, 32),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BerryTreeStage1[] = {
    ANIMCMD_FRAME(1, 32),
    ANIMCMD_FRAME(2, 32),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BerryTreeStage2[] = {
    ANIMCMD_FRAME(3, 48),
    ANIMCMD_FRAME(4, 48),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BerryTreeStage3[] = {
    ANIMCMD_FRAME(5, 32),
    ANIMCMD_FRAME(5, 32),
    ANIMCMD_FRAME(6, 32),
    ANIMCMD_FRAME(6, 32),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_BerryTreeStage4[] = {
    ANIMCMD_FRAME(7, 48),
    ANIMCMD_FRAME(7, 48),
    ANIMCMD_FRAME(8, 48),
    ANIMCMD_FRAME(8, 48),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_NurseBow[] = {
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(9, 32),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_RockBreak[] = {
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(1, 8),
    ANIMCMD_FRAME(2, 8),
    ANIMCMD_FRAME(3, 8),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_TreeCut[] = {
    ANIMCMD_FRAME(0, 6),
    ANIMCMD_FRAME(1, 6),
    ANIMCMD_FRAME(2, 6),
    ANIMCMD_FRAME(3, 6),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_TakeOutRodSouth[] = {
    ANIMCMD_FRAME(8, 4),
    ANIMCMD_FRAME(9, 4),
    ANIMCMD_FRAME(10, 4),
    ANIMCMD_FRAME(11, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_TakeOutRodNorth[] = {
    ANIMCMD_FRAME(4, 4),
    ANIMCMD_FRAME(5, 4),
    ANIMCMD_FRAME(6, 4),
    ANIMCMD_FRAME(7, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_TakeOutRodWest[] = {
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_TakeOutRodEast[] = {
    ANIMCMD_FRAME(0, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(3, 4, .hFlip = TRUE),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_PutAwayRodSouth[] = {
    ANIMCMD_FRAME(11, 4),
    ANIMCMD_FRAME(10, 6),
    ANIMCMD_FRAME(9, 6),
    ANIMCMD_FRAME(8, 6),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_PutAwayRodNorth[] = {
    ANIMCMD_FRAME(7, 4),
    ANIMCMD_FRAME(6, 6),
    ANIMCMD_FRAME(5, 6),
    ANIMCMD_FRAME(4, 6),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_PutAwayRodWest[] = {
    ANIMCMD_FRAME(3, 4),
    ANIMCMD_FRAME(2, 4),
    ANIMCMD_FRAME(1, 4),
    ANIMCMD_FRAME(0, 4),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_PutAwayRodEast[] = {
    ANIMCMD_FRAME(3, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(2, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(1, 4, .hFlip = TRUE),
    ANIMCMD_FRAME(0, 4, .hFlip = TRUE),
    ANIMCMD_END,
};

static const union AnimCmd sAnim_HookedPokemonSouth[] = {
    ANIMCMD_FRAME(10, 6),
    ANIMCMD_FRAME(11, 6),
    ANIMCMD_LOOP(1),
    ANIMCMD_FRAME(11, 30),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_HookedPokemonNorth[] = {
    ANIMCMD_FRAME(6, 6),
    ANIMCMD_FRAME(7, 6),
    ANIMCMD_LOOP(1),
    ANIMCMD_FRAME(7, 30),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_HookedPokemonWest[] = {
    ANIMCMD_FRAME(2, 6),
    ANIMCMD_FRAME(3, 6),
    ANIMCMD_LOOP(1),
    ANIMCMD_FRAME(3, 30),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd sAnim_HookedPokemonEast[] = {
    ANIMCMD_FRAME(2, 6, .hFlip = TRUE),
    ANIMCMD_FRAME(3, 6, .hFlip = TRUE),
    ANIMCMD_LOOP(1),
    ANIMCMD_FRAME(3, 30, .hFlip = TRUE),
    ANIMCMD_JUMP(0),
};

// Unused
static const union AffineAnimCmd sAffineAnim_KyogreGroudon_GoSouthStart[] = {
    AFFINEANIMCMD_FRAME(0, 0, 1, 1),
    AFFINEANIMCMD_FRAME(0, 0, 0, 1),
    AFFINEANIMCMD_FRAME(0, 0, 0, 1),
    AFFINEANIMCMD_FRAME(0, 0, 0, 1),
    AFFINEANIMCMD_LOOP(7),
    AFFINEANIMCMD_JUMP(0),
};

// Unused
static const union AffineAnimCmd sAffineAnim_KyogreGroudon_GoSouth[] = {
    AFFINEANIMCMD_FRAME(0, 0, -1, 1),
    AFFINEANIMCMD_FRAME(0, 0, 0, 1),
    AFFINEANIMCMD_LOOP(15),
    AFFINEANIMCMD_FRAME(0, 0, 1, 1),
    AFFINEANIMCMD_FRAME(0, 0, 0, 1),
    AFFINEANIMCMD_LOOP(15),
    AFFINEANIMCMD_JUMP(0),
};

static const union AnimCmd *const sAnimTable_Inanimate[] = {
    [ANIM_STAY_STILL] = sAnim_StayStill
};

// Hack 8: Jirachi's star glint, a small star that flares up now and then
static const union AnimCmd sAnim_JirachiStar[] = {
    ANIMCMD_FRAME(1, 24),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_FRAME(1, 8),
    ANIMCMD_FRAME(0, 8),
    ANIMCMD_JUMP(0),
};

static const union AnimCmd *const sAnimTable_JirachiStar[] = {
    [ANIM_STAY_STILL] = sAnim_JirachiStar
};

// Leftover from Ruby/Sapphire
static const union AnimCmd *const sAnimTable_QuintyPlump[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_QuintyPlumpFaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_QuintyPlumpFaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_QuintyPlumpFaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_QuintyPlumpFaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_QuintyPlumpGoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_QuintyPlumpGoNorth,
    [ANIM_STD_GO_WEST] = sAnim_QuintyPlumpGoWest,
    [ANIM_STD_GO_EAST] = sAnim_QuintyPlumpGoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_QuintyPlumpGoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_QuintyPlumpGoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_QuintyPlumpGoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_QuintyPlumpGoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_QuintyPlumpGoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_QuintyPlumpGoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_QuintyPlumpGoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_QuintyPlumpGoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_QuintyPlumpGoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_QuintyPlumpGoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_QuintyPlumpGoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_QuintyPlumpGoFastestEast,
};

static const union AnimCmd *const sAnimTable_Standard[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_FaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_FaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_FaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_FaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_GoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_GoNorth,
    [ANIM_STD_GO_WEST] = sAnim_GoWest,
    [ANIM_STD_GO_EAST] = sAnim_GoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_GoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_GoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_GoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_GoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_GoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_GoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_GoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_GoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_GoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_GoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_GoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_GoFastestEast,
    [ANIM_RAISE_HAND] = sAnim_RaiseHand,
};

// Mesma ordem (ANIM_STD_*) da sAnimTable_Standard, com os quadros da folha do seguidor
static const union AnimCmd *const sAnimTable_Follower[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_FollowerFaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_FollowerFaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_FollowerFaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_FollowerFaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_FollowerGoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_FollowerGoNorth,
    [ANIM_STD_GO_WEST] = sAnim_FollowerGoWest,
    [ANIM_STD_GO_EAST] = sAnim_FollowerGoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_FollowerGoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_FollowerGoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_FollowerGoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_FollowerGoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_FollowerGoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_FollowerGoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_FollowerGoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_FollowerGoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_FollowerGoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_FollowerGoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_FollowerGoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_FollowerGoFastestEast,
    [FOLLOWER_ANIM_IDLE_SOUTH] = sAnim_FollowerIdleSouth,
    [FOLLOWER_ANIM_IDLE_NORTH] = sAnim_FollowerIdleNorth,
    [FOLLOWER_ANIM_IDLE_WEST] = sAnim_FollowerIdleWest,
    [FOLLOWER_ANIM_IDLE_EAST] = sAnim_FollowerIdleEast,
};

static const union AnimCmd *const sAnimTable_HoOh[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_FaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_FaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_FaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_FaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_HoOhFlapWings,
    [ANIM_STD_GO_NORTH] = sAnim_HoOhStayStill,
    [ANIM_STD_GO_WEST] = sAnim_GoWest,
    [ANIM_STD_GO_EAST] = sAnim_GoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_GoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_GoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_GoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_GoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_GoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_GoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_GoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_GoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_GoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_GoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_GoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_GoFastestEast,
    [ANIM_RAISE_HAND] = sAnim_RaiseHand,
};

static const union AnimCmd *const sAnimTable_Unknown[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_UnknownFaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_UnknownFaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_UnknownFaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_UnknownFaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_UnknownGoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_UnknownGoNorth,
    [ANIM_STD_GO_WEST] = sAnim_UnknownGoWest,
    [ANIM_STD_GO_EAST] = sAnim_UnknownGoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_UnknownGoFastNorth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_UnknownGoFastSouth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_UnknownGoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_UnknownGoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_UnknownGoFasterNorth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_UnknownGoFasterSouth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_UnknownGoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_UnknownGoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_UnknownGoFastestNorth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_UnknownGoFastestSouth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_UnknownGoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_UnknownGoFastestEast,
    [ANIM_RUN_SOUTH] = sAnim_RunSouth,
    [ANIM_RUN_NORTH] = sAnim_RunNorth,
    [ANIM_RUN_WEST] = sAnim_RunWest,
    [ANIM_RUN_EAST] = sAnim_RunEast,
};

static const union AnimCmd *const sAnimTable_RedGreenNormal[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_FaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_FaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_FaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_FaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_GoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_GoNorth,
    [ANIM_STD_GO_WEST] = sAnim_GoWest,
    [ANIM_STD_GO_EAST] = sAnim_GoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_GoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_GoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_GoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_GoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_GoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_GoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_GoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_GoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_GoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_GoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_GoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_GoFastestEast,
    [ANIM_RUN_SOUTH] = sAnim_RunSouth,
    [ANIM_RUN_NORTH] = sAnim_RunNorth,
    [ANIM_RUN_WEST] = sAnim_RunWest,
    [ANIM_RUN_EAST] = sAnim_RunEast,
    [ANIM_SPIN_SOUTH] = sAnim_SpinSouth,
    [ANIM_SPIN_NORTH] = sAnim_SpinNorth,
    [ANIM_SPIN_WEST] = sAnim_SpinWest,
    [ANIM_SPIN_EAST] = sAnim_SpinEast,
    [ANIM_SHAKE_HEAD_OR_WALK_IN_PLACE] = sAnim_ShakeHeadOrWalkInPlace,
};

// Leftover from Ruby/Sapphire
static const union AnimCmd *const sAnimTable_AcroBike[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_FaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_FaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_FaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_FaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_GoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_GoNorth,
    [ANIM_STD_GO_WEST] = sAnim_GoWest,
    [ANIM_STD_GO_EAST] = sAnim_GoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_GoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_GoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_GoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_GoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_GoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_GoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_GoFasterWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_GoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_GoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_GoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_GoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_GoFastestEast,
    [ANIM_BUNNY_HOP_BACK_WHEEL_SOUTH] = sAnim_BunnyHopBackWheelSouth,
    [ANIM_BUNNY_HOP_BACK_WHEEL_NORTH] = sAnim_BunnyHopBackWheelNorth,
    [ANIM_BUNNY_HOP_BACK_WHEEL_WEST] = sAnim_BunnyHopBackWheelWest,
    [ANIM_BUNNY_HOP_BACK_WHEEL_EAST] = sAnim_BunnyHopBackWheelEast,
    [ANIM_BUNNY_HOP_FRONT_WHEEL_SOUTH] = sAnim_BunnyHopFrontWheelSouth,
    [ANIM_BUNNY_HOP_FRONT_WHEEL_NORTH] = sAnim_BunnyHopFrontWheelNorth,
    [ANIM_BUNNY_HOP_FRONT_WHEEL_WEST] = sAnim_BunnyHopFrontWheelWest,
    [ANIM_BUNNY_HOP_FRONT_WHEEL_EAST] = sAnim_BunnyHopFrontWheelEast,
    [ANIM_STANDING_WHEELIE_BACK_WHEEL_SOUTH] = sAnim_StandingWheelieBackWheelSouth,
    [ANIM_STANDING_WHEELIE_BACK_WHEEL_NORTH] = sAnim_StandingWheelieBackWheelNorth,
    [ANIM_STANDING_WHEELIE_BACK_WHEEL_WEST] = sAnim_StandingWheelieBackWheelWest,
    [ANIM_STANDING_WHEELIE_BACK_WHEEL_EAST] = sAnim_StandingWheelieBackWheelEast,
    [ANIM_STANDING_WHEELIE_FRONT_WHEEL_SOUTH] = sAnim_StandingWheelieFrontWheelSouth,
    [ANIM_STANDING_WHEELIE_FRONT_WHEEL_NORTH] = sAnim_StandingWheelieFrontWheelNorth,
    [ANIM_STANDING_WHEELIE_FRONT_WHEEL_WEST] = sAnim_StandingWheelieFrontWheelWest,
    [ANIM_STANDING_WHEELIE_FRONT_WHEEL_EAST] = sAnim_StandingWheelieFrontWheelEast,
    [ANIM_MOVING_WHEELIE_SOUTH] = sAnim_MovingWheelieSouth,
    [ANIM_MOVING_WHEELIE_NORTH] = sAnim_MovingWheelieNorth,
    [ANIM_MOVING_WHEELIE_WEST] = sAnim_MovingWheelieWest,
    [ANIM_MOVING_WHEELIE_EAST] = sAnim_MovingWheelieEast,
};

static const union AnimCmd *const sAnimTable_RedGreenSurf[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_SurfFaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_SurfFaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_SurfFaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_SurfFaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_SurfFaceSouth,
    [ANIM_STD_GO_NORTH] = sAnim_SurfFaceNorth,
    [ANIM_STD_GO_WEST] = sAnim_SurfFaceWest,
    [ANIM_STD_GO_EAST] = sAnim_SurfFaceEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_SurfFaceSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_SurfFaceNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_SurfFaceWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_SurfFaceEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_SurfFaceSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_SurfFaceNorth,
    [ANIM_STD_GO_FASTER_WEST] = sAnim_SurfFaceWest,
    [ANIM_STD_GO_FASTER_EAST] = sAnim_SurfFaceEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_SurfFaceSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_SurfFaceNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_SurfFaceWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_SurfFaceEast,
    [ANIM_GET_ON_OFF_POKEMON_SOUTH] = sAnim_GetOnOffSurfSouth,
    [ANIM_GET_ON_OFF_POKEMON_NORTH] = sAnim_GetOnOffSurfNorth,
    [ANIM_GET_ON_OFF_POKEMON_WEST] = sAnim_GetOnOffSurfWest,
    [ANIM_GET_ON_OFF_POKEMON_EAST] = sAnim_GetOnOffSurfEast,
};

static const union AnimCmd *const sAnimTable_Nurse[] = {
    [ANIM_STD_FACE_SOUTH] = sAnim_FaceSouth,
    [ANIM_STD_FACE_NORTH] = sAnim_FaceNorth,
    [ANIM_STD_FACE_WEST] = sAnim_FaceWest,
    [ANIM_STD_FACE_EAST] = sAnim_FaceEast,
    [ANIM_STD_GO_SOUTH] = sAnim_GoSouth,
    [ANIM_STD_GO_NORTH] = sAnim_GoNorth,
    [ANIM_STD_GO_WEST] = sAnim_GoWest,
    [ANIM_STD_GO_EAST] = sAnim_GoEast,
    [ANIM_STD_GO_FAST_SOUTH] = sAnim_GoFastSouth,
    [ANIM_STD_GO_FAST_NORTH] = sAnim_GoFastNorth,
    [ANIM_STD_GO_FAST_WEST] = sAnim_GoFastWest,
    [ANIM_STD_GO_FAST_EAST] = sAnim_GoFastEast,
    [ANIM_STD_GO_FASTER_SOUTH] = sAnim_GoFasterSouth,
    [ANIM_STD_GO_FASTER_NORTH] = sAnim_GoFasterNorth,
    [ANIM_STD_GO_FASTER_WEST]  = sAnim_GoFasterWest,
    [ANIM_STD_GO_FASTER_EAST]  = sAnim_GoFasterEast,
    [ANIM_STD_GO_FASTEST_SOUTH] = sAnim_GoFastestSouth,
    [ANIM_STD_GO_FASTEST_NORTH] = sAnim_GoFastestNorth,
    [ANIM_STD_GO_FASTEST_WEST] = sAnim_GoFastestWest,
    [ANIM_STD_GO_FASTEST_EAST] = sAnim_GoFastestEast,
    [ANIM_NURSE_BOW] = sAnim_NurseBow,
};

static const union AnimCmd *const sAnimTable_RedGreenFieldMove[] = {
    [ANIM_FIELD_MOVE] = sAnim_FieldMove,
};

static const union AnimCmd *const sAnimTable_RedGreenVSSeeker[] = {
    [ANIM_VS_SEEKER] = sAnim_VSSeeker,
};

static const union AnimCmd *const sAnimTable_RedGreenVSSeekerBike[] = {
    [ANIM_VS_SEEKER] = sAnim_VSSeekerBike,
};

// Unused
static const union AnimCmd *const sAnimTable_BerryTree[] = {
    sAnim_BerryTreeStage0,
    sAnim_BerryTreeStage1,
    sAnim_BerryTreeStage2,
    sAnim_BerryTreeStage3,
    sAnim_BerryTreeStage4,
};

static const union AnimCmd *const sAnimTable_RockSmashRock[] = {
    [ANIM_STAY_STILL] = sAnim_StayStill,
    [ANIM_REMOVE_OBSTACLE] = sAnim_RockBreak,
};

static const union AnimCmd *const sAnimTable_CutTree[] = {
    [ANIM_STAY_STILL] = sAnim_StayStill,
    [ANIM_REMOVE_OBSTACLE] = sAnim_TreeCut,
};

static const union AnimCmd *const sAnimTable_RedGreenFish[] = {
    [ANIM_TAKE_OUT_ROD_SOUTH] = sAnim_TakeOutRodSouth,
    [ANIM_TAKE_OUT_ROD_NORTH] = sAnim_TakeOutRodNorth,
    [ANIM_TAKE_OUT_ROD_WEST] = sAnim_TakeOutRodWest,
    [ANIM_TAKE_OUT_ROD_EAST] = sAnim_TakeOutRodEast,
    [ANIM_PUT_AWAY_ROD_SOUTH] = sAnim_PutAwayRodSouth,
    [ANIM_PUT_AWAY_ROD_NORTH] = sAnim_PutAwayRodNorth,
    [ANIM_PUT_AWAY_ROD_WEST] = sAnim_PutAwayRodWest,
    [ANIM_PUT_AWAY_ROD_EAST] = sAnim_PutAwayRodEast,
    [ANIM_HOOKED_POKEMON_SOUTH] = sAnim_HookedPokemonSouth,
    [ANIM_HOOKED_POKEMON_NORTH] = sAnim_HookedPokemonNorth,
    [ANIM_HOOKED_POKEMON_WEST] = sAnim_HookedPokemonWest,
    [ANIM_HOOKED_POKEMON_EAST] = sAnim_HookedPokemonEast,
};

static const struct StepAnimTable sStepAnimTables[] = {
    {
        .anims = sAnimTable_QuintyPlump,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_Standard,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_RedGreenNormal,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_AcroBike,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_RedGreenSurf,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_Nurse,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_RedGreenFish,
        .animPos = {1, 3, 0, 2},
    },
    {
        .anims = sAnimTable_Unknown,
        .animPos = {3, 7, 0, 4},
    },
    {}
};
