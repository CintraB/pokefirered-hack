#include "global.h"
#include "link_rfu.h"
#include "mystery_gift_server.h"
#include "mystery_gift_client.h"
#include "constants/union_room.h"

ALIGNED(4) const u8 gText_UR_EmptyString[] = _("");
ALIGNED(4) const u8 gText_UR_Colon[] = _(":");
ALIGNED(4) const u8 gText_UR_ID[] = _("{ID}");
ALIGNED(4) const u8 gText_UR_PleaseStartOver[] = _("Comece de novo desde o início.");
ALIGNED(4) const u8 gText_UR_WirelessSearchCanceled[] = _("A busca do Sistema de\nComunicação Sem Fio foi cancelada.");
ALIGNED(4) static const u8 sText_AwaitingCommunucation2[] = _("ともだちからの れんらくを\nまっています");
ALIGNED(4) const u8 gText_UR_AwaitingCommunication[] = _("{STR_VAR_1}! Aguardando a\ncomunicação de outro jogador.");
ALIGNED(4) const u8 gText_UR_AwaitingLinkPressStart[] = _("{STR_VAR_1}! Aguardando conexão!\nCom todos prontos, aperte START.");

ALIGNED(4) static const u8 sText_SingleBattle[] = _("シングルバトルを かいさいする");
ALIGNED(4) static const u8 sText_DoubleBattle[] = _("ダブルバトルを かいさいする");
ALIGNED(4) static const u8 sText_MultiBattle[] = _("マルチバトルを かいさいする");
ALIGNED(4) static const u8 sText_TradePokemon[] = _("ポケモンこうかんを かいさいする");
ALIGNED(4) static const u8 sText_Chat[] = _("チャットを かいさいする");
ALIGNED(4) static const u8 sText_DistWonderCard[] = _("ふしぎなカードをくばる");
ALIGNED(4) static const u8 sText_DistWonderNews[] = _("ふしぎなニュースをくばる");
ALIGNED(4) static const u8 sText_DistMysteryEvent[] = _("ふしぎなできごとを かいさいする");
ALIGNED(4) static const u8 sText_HoldPokemonJump[] = _("なわとびを かいさいする");
ALIGNED(4) static const u8 sText_HoldBerryCrush[] = _("きのみマッシャーを かいさいする");
ALIGNED(4) static const u8 sText_HoldBerryPicking[] = _("きのみどりを かいさいする");
ALIGNED(4) static const u8 sText_HoldSpinTrade[] = _("ぐるぐるこうかんを かいさいする");
ALIGNED(4) static const u8 sText_HoldSpinShop[] = _("ぐるぐるショップを かいさいする");

// Unused
static const u8 *const sLinkGroupActionTexts[] = {
    sText_SingleBattle,
    sText_DoubleBattle,
    sText_MultiBattle,
    sText_TradePokemon,
    sText_Chat,
    sText_DistWonderCard,
    sText_DistWonderNews,
    sText_DistWonderCard,
    sText_HoldPokemonJump,
    sText_HoldBerryCrush,
    sText_HoldBerryPicking,
    sText_HoldBerryPicking,
    sText_HoldSpinTrade,
    sText_HoldSpinShop
};

static const u8 sText_1PlayerNeeded[] = _("Falta 1\njogador");
static const u8 sText_2PlayersNeeded[] = _("Faltam 2\njogadores");
static const u8 sText_3PlayersNeeded[] = _("Faltam 3\njogadores");
static const u8 sText_4PlayersNeeded[] = _("あと4にん\nひつよう");
static const u8 sText_2PlayerMode[] = _("Modo 2\njogadores");
static const u8 sText_3PlayerMode[] = _("Modo 3\njogadores");
static const u8 sText_4PlayerMode[] = _("Modo 4\njogadores");
static const u8 sText_5PlayerMode[] = _("Modo 5\njogadores");

const u8 *const gTexts_UR_PlayersNeededOrMode[][5] = {
    { // 2 players required
        sText_1PlayerNeeded,
        sText_2PlayerMode
    },
    { // 4 players required
        sText_3PlayersNeeded,
        sText_2PlayersNeeded,
        sText_1PlayerNeeded,
        sText_4PlayerMode
    },
    { // 2-5 players required
        sText_1PlayerNeeded,
        sText_2PlayerMode,
        sText_3PlayerMode,
        sText_4PlayerMode,
        sText_5PlayerMode
    },
    { // 3-5 players required
        sText_2PlayersNeeded,
        sText_1PlayerNeeded,
        sText_3PlayerMode,
        sText_4PlayerMode,
        sText_5PlayerMode
    }
};

ALIGNED(4) const u8 gText_UR_BButtonCancel[] = _("{B_BUTTON}Cancelar");
ALIGNED(4) static const u8 sText_SearchingForParticipants[] = _("ため\nさんかしゃ ぼしゅうちゅう です！");
ALIGNED(4) const u8 gText_UR_PlayerContactedYouForXAccept[] = _("{STR_VAR_2} chamou você para\n{STR_VAR_1}. Aceita?");
ALIGNED(4) const u8 gText_UR_PlayerContactedYouShareX[] = _("{STR_VAR_2} chamou você.\nVai compartilhar {STR_VAR_1}?");
ALIGNED(4) const u8 gText_UR_PlayerContactedYouAddToMembers[] = _("{STR_VAR_2} chamou você.\nIncluir entre os membros?");
ALIGNED(4) const u8 gText_UR_AreTheseMembersOK[] = _("{STR_VAR_1}!\nEstes membros estão certos?");
ALIGNED(4) const u8 gText_UR_CancelModeWithTheseMembers[] = _("Cancelar o modo {STR_VAR_1}\ncom estes membros?");
ALIGNED(4) const u8 gText_UR_AnOKWasSentToPlayer[] = _("Um “OK” foi enviado\npara {STR_VAR_1}.");

ALIGNED(4) static const u8 sText_OtherTrainerUnavailableNow[] = _("Parece que o outro Treinador não\nestá disponível agora…\p");
ALIGNED(4) static const u8 sText_CantTransmitTrainerTooFar[] = _("Não dá para transmitir para um\nTreinador que está longe demais.\p");
ALIGNED(4) static const u8 sText_TrainersNotReadyYet[] = _("Ainda há Treinadores que não\nestão prontos.\p");

const u8 *const gTexts_UR_CantTransmitToTrainer[] = {
    sText_CantTransmitTrainerTooFar,
    sText_TrainersNotReadyYet
};

ALIGNED(4) const u8 gText_UR_ModeWithTheseMembersWillBeCanceled[] = _("O modo {STR_VAR_1} com estes\nmembros será cancelado.{PAUSE 90}");
ALIGNED(4) static const u8 sText_MemberNoLongerAvailable[] = _("Um dos membros não pode mais\ncontinuar disponível.\p");

const u8 *const gTexts_UR_PlayerUnavailable[] = {
    sText_OtherTrainerUnavailableNow,
    sText_MemberNoLongerAvailable
};

ALIGNED(4) static const u8 sText_TrainerAppearsUnavailable[] = _("O outro Treinador parece não\nestar disponível…\p");
ALIGNED(4) const u8 gText_UR_PlayerSentBackOK[] = _("{STR_VAR_1} respondeu com um “OK”!");
ALIGNED(4) const u8 gText_UR_PlayerOKdRegistration[] = _("{STR_VAR_1} aceitou o seu registro\ncomo membro.");
ALIGNED(4) static const u8 sText_PlayerRepliedNo[] = _("{STR_VAR_1} respondeu: “Não…”\p");
ALIGNED(4) const u8 gText_UR_AwaitingOtherMembers[] = _("{STR_VAR_1}!\nAguardando os outros membros!");
ALIGNED(4) const u8 gText_UR_QuitBeingMember[] = _("Deixar de ser membro?");
ALIGNED(4) static const u8 sText_StoppedBeingMember[] = _("Você deixou de ser membro.\p");

const u8 *const gTexts_UR_PlayerDisconnected[] = {
    [RFU_STATUS_OK]                  = NULL,
    [RFU_STATUS_FATAL_ERROR]         = sText_MemberNoLongerAvailable,
    [RFU_STATUS_CONNECTION_ERROR]    = sText_TrainerAppearsUnavailable,
    [RFU_STATUS_CHILD_SEND_COMPLETE] = NULL,
    [RFU_STATUS_NEW_CHILD_DETECTED]  = NULL,
    [RFU_STATUS_JOIN_GROUP_OK]       = NULL,
    [RFU_STATUS_JOIN_GROUP_NO]       = sText_PlayerRepliedNo,
    [RFU_STATUS_WAIT_ACK_JOIN_GROUP] = NULL,
    [RFU_STATUS_LEAVE_GROUP_NOTICE]  = NULL,
    [RFU_STATUS_LEAVE_GROUP]         = sText_StoppedBeingMember
};

ALIGNED(4) const u8 gText_UR_WirelessLinkEstablished[] = _("A conexão do Sistema de\nComunicação Sem Fio foi feita.");
ALIGNED(4) const u8 gText_UR_WirelessLinkDropped[] = _("A conexão do Sistema de\nComunicação Sem Fio caiu…");
ALIGNED(4) const u8 gText_UR_LinkWithFriendDropped[] = _("A conexão com quem estava\njogando com você caiu…");
ALIGNED(4) static const u8 sText_PlayerRepliedNo2[] = _("{STR_VAR_1} respondeu: “Não…”");

const u8 *const gTexts_UR_LinkDropped[] = {
    [RFU_STATUS_OK]                  = NULL,
    [RFU_STATUS_FATAL_ERROR]         = gText_UR_LinkWithFriendDropped,
    [RFU_STATUS_CONNECTION_ERROR]    = gText_UR_LinkWithFriendDropped,
    [RFU_STATUS_CHILD_SEND_COMPLETE] = NULL,
    [RFU_STATUS_NEW_CHILD_DETECTED]  = NULL,
    [RFU_STATUS_JOIN_GROUP_OK]       = NULL,
    [RFU_STATUS_JOIN_GROUP_NO]       = sText_PlayerRepliedNo2,
    [RFU_STATUS_WAIT_ACK_JOIN_GROUP] = NULL,
    [RFU_STATUS_LEAVE_GROUP_NOTICE]  = NULL,
    [RFU_STATUS_LEAVE_GROUP]         = NULL
};

ALIGNED(4) static const u8 sText_DoYouWantXMode[] = _("Quer o modo\n{STR_VAR_2}?");
ALIGNED(4) static const u8 sText_DoYouWantXMode2[] = _("Quer o modo\n{STR_VAR_2}?");

// Unused
static const u8 *const sDoYouWantModeTexts[] = {
    sText_DoYouWantXMode,
    sText_DoYouWantXMode2
};

ALIGNED(4) static const u8 sText_CommunicatingPleaseWait[] = _("はなしかけています…\nしょうしょう おまちください"); // Unused
ALIGNED(4) const u8 gText_UR_AwaitingPlayersResponseAboutTrade[] = _("Aguardando a resposta de\n{STR_VAR_1} sobre a troca…");

ALIGNED(4) static const u8 sText_Communicating[] = _("Comunicando{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.\n{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.");
ALIGNED(4) static const u8 sText_CommunicatingWithPlayer[] = _("Comunicando com {STR_VAR_1}{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.\n{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.");
ALIGNED(4) static const u8 sText_PleaseWaitAWhile[] = _("Aguarde um pouco{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.\n{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.{PAUSE 15}.");

const u8 *const gTexts_UR_CommunicatingWait[] = {
    sText_Communicating,
    sText_CommunicatingWithPlayer,
    sText_PleaseWaitAWhile
};

ALIGNED(4) static const u8 sText_HiDoSomethingMale[] = _("Opa! Tem alguma coisa que você\nqueira fazer?");
ALIGNED(4) static const u8 sText_HiDoSomethingFemale[] = _("Olá!\nQuer fazer alguma coisa?");
ALIGNED(4) static const u8 sText_HiDoSomethingAgainMale[] = _("{STR_VAR_1}: Opa, de novo por aqui!\nO que vai ser desta vez?");
ALIGNED(4) static const u8 sText_HiDoSomethingAgainFemale[] = _("{STR_VAR_1}: Ah! Olá, {PLAYER}!\nQuer fazer alguma coisa?");

const u8 *const gTexts_UR_HiDoSomething[][GENDER_COUNT] = {
    {
        sText_HiDoSomethingMale,
        sText_HiDoSomethingFemale
    }, {
        sText_HiDoSomethingAgainMale,
        sText_HiDoSomethingAgainFemale
    }
};

ALIGNED(4) static const u8 sText_DoSomethingMale[] = _("Quer fazer alguma coisa?");
ALIGNED(4) static const u8 sText_DoSomethingFemale[] = _("Gostaria de fazer alguma coisa?");
ALIGNED(4) static const u8 sText_DoSomethingAgainMale[] = _("{STR_VAR_1}: O que você gostaria\nde fazer agora?");
ALIGNED(4) static const u8 sText_DoSomethingAgainFemale[] = _("{STR_VAR_1}‘また なにかする？");

// Unused
static const u8 *const sDoSomethingTexts[][GENDER_COUNT] = {
    {
        sText_DoSomethingMale,
        sText_DoSomethingFemale
    }, {
        sText_DoSomethingAgainMale,
        sText_DoSomethingAgainMale // was probably supposed to be sText_DoSomethingAgainFemale
    }
};

ALIGNED(4) static const u8 sText_SomebodyHasContactedYou[] = _("Alguém chamou você.{PAUSE 60}");
ALIGNED(4) static const u8 sText_PlayerHasContactedYou[] = _("{STR_VAR_1} chamou você.{PAUSE 60}");

const u8 *const gTexts_UR_PlayerContactedYou[] = {
    sText_SomebodyHasContactedYou,
    sText_PlayerHasContactedYou
};

ALIGNED(4) static const u8 sText_AwaitingResponseFromTrainer[] = _("Aguardando a resposta do\noutro Treinador…");
ALIGNED(4) static const u8 sText_AwaitingResponseFromPlayer[] = _("Aguardando a resposta de\n{STR_VAR_1}…");

const u8 *const gTexts_UR_AwaitingResponse[] = {
    sText_AwaitingResponseFromTrainer,
    sText_AwaitingResponseFromPlayer
};

ALIGNED(4) static const u8 sText_AwaitingResponseCancelBButton[] = _("あいての ていあんを まっています\nビーボタンで キャンセル");

ALIGNED(4) const u8 gText_UR_ShowTrainerCard[] = _("O outro Treinador mostrou o\nCartão de Treinador para você.\pQuer mostrar o seu\nCartão de Treinador?");
ALIGNED(4) const u8 gText_UR_BattleChallenge[] = _("O outro Treinador desafia você\npara uma batalha.\pVai aceitar o desafio?");
ALIGNED(4) const u8 gText_UR_ChatInvitation[] = _("O outro Treinador chama você\npara um chat.\pVai aceitar o convite?");
ALIGNED(4) const u8 gText_UR_OfferToTradeMon[] = _("Há uma oferta de troca pelo seu\n{DYNAMIC 1} Nv. {DYNAMIC 0} registrado\pem troca de um\n{DYNAMIC 3} Nv. {DYNAMIC 2}.\pVai aceitar esta oferta\nde troca?");
ALIGNED(4) const u8 gText_UR_OfferToTradeEgg[] = _("Há uma oferta de troca pelo seu\nOvo registrado.\lVai aceitar esta oferta de troca?");
ALIGNED(4) const u8 gText_UR_ChatDropped[] = _("O chat caiu.\p");
ALIGNED(4) const u8 gText_UR_OfferDeclined1[] = _("Você recusou a oferta.\p");
ALIGNED(4) const u8 gText_UR_OfferDeclined2[] = _("Você recusou a oferta.\p");
ALIGNED(4) const u8 gText_UR_ChatEnded[] = _("O chat terminou.\p");

// Unused
static const u8 *const sInvitationTexts[] = {
    gText_UR_ShowTrainerCard,
    gText_UR_BattleChallenge,
    gText_UR_ChatInvitation,
    gText_UR_OfferToTradeMon
};

ALIGNED(4) static const u8 sText_JoinChatMale[] = _("Ah, oi! A gente está num chat agora.\nQuer entrar também?");
ALIGNED(4) static const u8 sText_PlayerJoinChatMale[] = _("{STR_VAR_1}: Oi, {PLAYER}!\nA gente está num chat agora.\lQuer entrar também?");
ALIGNED(4) static const u8 sText_JoinChatFemale[] = _("Ah, olá! Estamos num chat agora.\nGostaria de participar?");
ALIGNED(4) static const u8 sText_PlayerJoinChatFemale[] = _("{STR_VAR_1}: Ah, olá, {PLAYER}!\nEstamos num chat agora.\lGostaria de participar?");

const u8 *const gTexts_UR_JoinChat[][GENDER_COUNT] = {
    {
        sText_JoinChatMale,
        sText_JoinChatFemale
    }, {
        sText_PlayerJoinChatMale,
        sText_PlayerJoinChatFemale
    }
};

ALIGNED(4) const u8 gText_UR_TrainerAppearsBusy[] = _("……\nO Treinador parece estar ocupado…\p");
ALIGNED(4) static const u8 sText_WaitForBattleMale[] = _("Uma batalha, é?\nCerto, só me dá um tempinho.");
ALIGNED(4) static const u8 sText_WaitForChatMale[] = _("Quer bater papo, é?\nClaro, só espera um pouco.");
ALIGNED(4) static const u8 sText_ShowTrainerCardMale[] = _("Claro! Como “Saudação”, aqui\nestá o meu Cartão de Treinador.");
ALIGNED(4) static const u8 sText_WaitForBattleFemale[] = _("Uma batalha? Claro, mas preciso\nde um tempo para me preparar.");
ALIGNED(4) static const u8 sText_WaitForChatFemale[] = _("Quer conversar?\nTudo bem, mas espere um momento.");
ALIGNED(4) static const u8 sText_ShowTrainerCardFemale[] = _("Para me apresentar, vou mostrar\no meu Cartão de Treinador.");

const u8 *const gTexts_UR_WaitOrShowCard[GENDER_COUNT][4] = {
    {
        sText_WaitForBattleMale,
        sText_WaitForChatMale,
        NULL,
        sText_ShowTrainerCardMale
    }, {
        sText_WaitForBattleFemale,
        sText_WaitForChatFemale,
        NULL,
        sText_ShowTrainerCardFemale
    }
};

ALIGNED(4) static const u8 sText_WaitForChatMale2[] = _("チャットだね！\nわかった ちょっと まってて！");
ALIGNED(4) static const u8 sText_DoneWaitingBattleMale[] = _("Valeu por esperar!\nVamos começar a batalha!{PAUSE 60}");
ALIGNED(4) static const u8 sText_DoneWaitingChatMale[] = _("Beleza!\nVamos conversar!{PAUSE 60}");
ALIGNED(4) static const u8 sText_DoneWaitingBattleFemale[] = _("Desculpe a demora!\nVamos começar!{PAUSE 60}");
ALIGNED(4) static const u8 sText_DoneWaitingChatFemale[] = _("Desculpe a demora!\nVamos conversar.{PAUSE 60}");
ALIGNED(4) static const u8 sText_TradeWillBeStarted[] = _("A troca vai começar.{PAUSE 60}");
ALIGNED(4) static const u8 sText_BattleWillBeStarted[] = _("A batalha vai começar.{PAUSE 60}");
ALIGNED(4) static const u8 sText_EnteringChat[] = _("Entrando no chat…{PAUSE 60}");

const u8 *const gTexts_UR_StartActivity[][GENDER_COUNT][3] = {
    {
        {
            sText_BattleWillBeStarted,
            sText_EnteringChat,
            sText_TradeWillBeStarted
        }, {
            sText_BattleWillBeStarted,
            sText_EnteringChat,
            sText_TradeWillBeStarted
        }
    }, {
        {
            sText_DoneWaitingBattleMale,
            sText_DoneWaitingChatMale,
            sText_TradeWillBeStarted
        }, {
            sText_DoneWaitingBattleFemale,
            sText_DoneWaitingChatFemale,
            sText_TradeWillBeStarted
        }
    }
};

ALIGNED(4) static const u8 sText_BattleDeclinedMale[] = _("Foi mal! Os meus Pokémon não estão\nse sentindo muito bem agora.\lVamos batalhar outra hora.\p");
ALIGNED(4) static const u8 sText_BattleDeclinedFemale[] = _("Sinto muito, mas os meus Pokémon\nnão estão se sentindo bem…\pVamos batalhar outra hora.\p");

const u8 *const gTexts_UR_BattleDeclined[GENDER_COUNT] = {
    sText_BattleDeclinedMale,
    sText_BattleDeclinedFemale
};

ALIGNED(4) static const u8 sText_ShowTrainerCardDeclinedMale[] = _("Hã? O meu Cartão de Treinador…\nCadê ele?\lFoi mal! Mostro outra hora!\p");
ALIGNED(4) static const u8 sText_ShowTrainerCardDeclinedFemale[] = _("Ué? Onde foi que eu deixei o meu\nCartão de Treinador?…\lDesculpe! Mostro mais tarde!\p");

const u8 *const gTexts_UR_ShowTrainerCardDeclined[GENDER_COUNT] = {
    sText_ShowTrainerCardDeclinedMale,
    sText_ShowTrainerCardDeclinedFemale
};

ALIGNED(4) static const u8 sText_IfYouWantToDoSomethingMale[] = _("Se quiser fazer alguma coisa\ncomigo, é só me chamar!\p");
ALIGNED(4) static const u8 sText_IfYouWantToDoSomethingFemale[] = _("Se quiser fazer alguma coisa\ncomigo, não precisa ter vergonha.\p");

const u8 *const gTexts_UR_IfYouWantToDoSomething[GENDER_COUNT] = {
    sText_IfYouWantToDoSomethingMale,
    sText_IfYouWantToDoSomethingFemale
};

ALIGNED(4) const u8 gText_UR_TrainerBattleBusy[] = _("Opa! Desculpe, mas preciso fazer\noutra coisa.\lFica para outra vez, tá?\p");
ALIGNED(4) const u8 gText_UR_NeedTwoMonsOfLevel30OrLower1[] = _("Para batalhar, você precisa de\ndois Pokémon abaixo do\lNv. 30.\p");
ALIGNED(4) const u8 gText_UR_NeedTwoMonsOfLevel30OrLower2[] = _("Para uma batalha, você precisa de\ndois Pokémon abaixo do Nv. 30.\p");

ALIGNED(4) static const u8 sText_DeclineChatMale[] = _("Ah, tudo bem.\nVenha me ver quando quiser, tá?\p");
ALIGNED(4) static const u8 stext_DeclineChatFemale[] = _("Ah…\nApareça quando quiser.\p");

// Response from partner when player declines chat
const u8 *const gTexts_UR_DeclineChat[GENDER_COUNT] = {
    sText_DeclineChatMale,
    stext_DeclineChatFemale
};

ALIGNED(4) static const u8 sText_ChatDeclinedMale[] = _("Ah, foi mal!\nAgora não dá mesmo.\lVamos bater papo outra hora.\p");
ALIGNED(4) static const u8 sText_ChatDeclinedFemale[] = _("Ah, sinto muito.\nTenho muita coisa para fazer agora.\lVamos conversar outra hora.\p");

// Response from partner when they decline chat
const u8 *const gTexts_UR_ChatDeclined[GENDER_COUNT] = {
    sText_ChatDeclinedMale,
    sText_ChatDeclinedFemale
};

ALIGNED(4) static const u8 sText_YoureToughMale[] = _("Uau!\nDá para ver que você é forte!\p");
ALIGNED(4) static const u8 sText_UsedGoodMoveMale[] = _("Você usou esse golpe?\nBoa estratégia!\p");
ALIGNED(4) static const u8 sText_BattleSurpriseMale[] = _("Mandou bem!\nEssa me abriu os olhos!\p");
ALIGNED(4) static const u8 sText_SwitchedMonsMale[] = _("Ah! Como você pensou em usar esse\nPokémon numa hora dessas?\p");
ALIGNED(4) static const u8 sText_YoureToughFemale[] = _("Esse Pokémon…\nFoi muito bem treinado!\p");
ALIGNED(4) static const u8 sText_UsedGoodMoveFemale[] = _("É isso aí!\nEsse é o golpe certo agora!\p");
ALIGNED(4) static const u8 sText_BattleSurpriseFemale[] = _("Que incrível!\nDá para batalhar desse jeito?\p");
ALIGNED(4) static const u8 sText_SwitchedMonsFemale[] = _("Você tem um ótimo senso de tempo\npara trocar de Pokémon!\p");

const u8 *const gTexts_UR_BattleReaction[GENDER_COUNT][4] = {
    {
        sText_YoureToughMale,
        sText_UsedGoodMoveMale,
        sText_BattleSurpriseMale,
        sText_SwitchedMonsMale
    }, {
        sText_YoureToughFemale,
        sText_UsedGoodMoveFemale,
        sText_BattleSurpriseFemale,
        sText_SwitchedMonsFemale
    }
};

ALIGNED(4) static const u8 sText_LearnedSomethingMale[] = _("Ah, entendi!\nIsso é bem educativo!\p");
ALIGNED(4) static const u8 sText_ThatsFunnyMale[] = _("Para de falar coisa engraçada!\nJá estou com dor de tanto rir!\p");
ALIGNED(4) static const u8 sText_RandomChatMale1[] = _("É?\nAconteceu uma coisa dessas.\p");
ALIGNED(4) static const u8 sText_RandomChatMale2[] = _("Hum… Quê?\nEntão é isso que você quer dizer?\p");
ALIGNED(4) static const u8 sText_LearnedSomethingFemale[] = _("É mesmo?\nEu não sabia disso.\p");
ALIGNED(4) static const u8 sText_ThatsFunnyFemale[] = _("Hahaha!\nComo assim?\p");
ALIGNED(4) static const u8 sText_RandomChatFemale1[] = _("Sim, é exatamente isso!\nFoi o que eu quis dizer.\p");
ALIGNED(4) static const u8 sText_RandomChatFemale2[] = _("Em outras palavras…\nSim! É isso mesmo!\p");

const u8 *const gTexts_UR_ChatReaction[GENDER_COUNT][4] = {
    {
        sText_LearnedSomethingMale,
        sText_ThatsFunnyMale,
        sText_RandomChatMale1,
        sText_RandomChatMale2
    }, {
        sText_LearnedSomethingFemale,
        sText_ThatsFunnyFemale,
        sText_RandomChatFemale1,
        sText_RandomChatFemale2
    }
};

ALIGNED(4) static const u8 sText_ShowedTrainerCardMale1[] = _("Mostro o meu Cartão de Treinador\ncomo forma de cumprimento.\p");
ALIGNED(4) static const u8 sText_ShowedTrainerCardMale2[] = _("Espero conhecer você melhor!\p");
ALIGNED(4) static const u8 sText_ShowedTrainerCardFemale1[] = _("Mostramos os Cartões de Treinador\num ao outro para nos conhecermos.\p");
ALIGNED(4) static const u8 sText_ShowedTrainerCardFemale2[] = _("Prazer em conhecer você.\nApareça sempre!\p");

const u8 *const gTexts_UR_TrainerCardReaction[GENDER_COUNT][2] = {
    {
        sText_ShowedTrainerCardMale1,
        sText_ShowedTrainerCardMale2
    }, {
        sText_ShowedTrainerCardFemale1,
        sText_ShowedTrainerCardFemale2
    }
};

ALIGNED(4) static const u8 sText_MaleTraded1[] = _("Eba!\nEu queria muito este Pokémon!\p");
ALIGNED(4) static const u8 sText_MaleTraded2[] = _("Finalmente uma troca me deu o\nPokémon que eu queria há tempos.\p");
ALIGNED(4) static const u8 sText_FemaleTraded1[] = _("Estou trocando Pokémon agora.\p");
ALIGNED(4) static const u8 sText_FemaleTraded2[] = _("Finalmente consegui numa troca o\nPokémon que eu queria!\p");

const u8 *const gTexts_UR_TradeReaction[GENDER_COUNT][4] = {
    {
        sText_MaleTraded1,
        sText_MaleTraded2
    }, {
        sText_FemaleTraded1,
        sText_FemaleTraded2
    }
};

const u8 gText_UR_XCheckedTradingBoard[] = _("{STR_VAR_1} consultou o\nMural de Trocas.\p");
ALIGNED(4) const u8 gText_UR_RegisterMonAtTradingBoard[] = _("Boas-vindas ao Mural de Trocas.\pAqui você registra o seu Pokémon\ne o oferece para uma troca.\pQuer registrar um dos seus\nPokémon?");
ALIGNED(4) const u8 gText_UR_TradingBoardInfo[] = _("O Mural de Trocas serve para\n"
                                                    "oferecer um Pokémon para troca.\p"
                                                    "Basta registrar um Pokémon\n"
                                                    "para a troca.\p"
                                                    "Outro Treinador pode oferecer um\n"
                                                    "Pokémon da equipe em troca.\p"
                                                    "Esperamos que você registre\n"
                                                    "Pokémon e troque com muitos,\l"
                                                    "muitos outros Treinadores.\p"
                                                    "Quer registrar um dos seus\n"
                                                    "Pokémon?");
ALIGNED(4) static const u8 sText_ThankYouForRegistering[] = _("こうかんけいじばん の とうろくが\nかんりょう しました\pごりよう ありがとう\nございました！\p");
ALIGNED(4) static const u8 sText_NobodyHasRegistered[] = _("けいじばんに だれも ポケモンを\nとうろく していません\p\n");
ALIGNED(4) const u8 gText_UR_ChooseRequestedMonType[] = _("Escolha o tipo de Pokémon\nque você quer na troca.\n");
ALIGNED(4) const u8 gText_UR_WhichMonWillYouOffer[] = _("Qual Pokémon da sua equipe\nvocê vai oferecer na troca?\p");
ALIGNED(4) const u8 gText_UR_RegistrationCanceled[] = _("O registro foi cancelado.\p");
ALIGNED(4) const u8 gText_UR_RegistraionCompleted[] = _("O registro foi concluído.\p");
ALIGNED(4) const u8 gText_UR_TradeCanceled[] = _("A troca foi cancelada.\p");
ALIGNED(4) const u8 gText_UR_CancelRegistrationOfMon[] = _("Cancelar o registro do seu\n{STR_VAR_1} Nv. {STR_VAR_2}?");
ALIGNED(4) const u8 gText_UR_CancelRegistrationOfEgg[] = _("Cancelar o registro do seu\nOvo?");
ALIGNED(4) const u8 gText_UR_RegistrationCanceled2[] = _("O registro foi cancelado.\p");
ALIGNED(4) static const u8 sText_TradeTrainersWillBeListed[] = _("こうかんを きぼうしているひとを\nひょうじします");
ALIGNED(4) static const u8 sText_ChooseTrainerToTradeWith2[] = _("こうかん したい トレーナーを\nえらんで ください");
ALIGNED(4) const u8 gText_UR_AskTrainerToMakeTrade[] = _("Quer pedir a {STR_VAR_1}\npara fazer uma troca?");
ALIGNED(4) static const u8 sText_AwaitingResponseFromTrainer2[] = _("……\nあいての へんじを まっています");
ALIGNED(4) static const u8 sText_NotRegisteredAMonForTrade[] = _("あなたが こうかんにだす\nポケモンが とうろくされていません\p");
ALIGNED(4) const u8 gText_UR_DontHaveTypeTrainerWants[] = _("Você não tem um Pokémon do tipo\n{STR_VAR_2} que {STR_VAR_1} quer.\p");
ALIGNED(4) const u8 gText_UR_DontHaveEggTrainerWants[] = _("Você não tem um Ovo que\n{STR_VAR_1} quer.\p");

ALIGNED(4) static const u8 sText_PlayerCantTradeForYourMon[] = _("{STR_VAR_1} não pode trocar pelo\nseu Pokémon agora.\p");
ALIGNED(4) static const u8 sText_CantTradeForPartnersMon[] = _("Você não pode trocar pelo\nPokémon de {STR_VAR_1} agora.\p");

// Unused
static const u8 *const sCantTradeMonTexts[] = {
    sText_PlayerCantTradeForYourMon,
    sText_CantTradeForPartnersMon
};

ALIGNED(4) const u8 gText_UR_TradeOfferRejected[] = _("A sua oferta de troca foi recusada.\p");
ALIGNED(4) const u8 gText_UR_EggTrade[] = _("Troca de Ovo");
ALIGNED(4) const u8 gText_UR_ChooseJoinCancel[] = _("{DPAD_UPDOWN}Escolher  {A_BUTTON}Entrar  {B_BUTTON}Cancelar");
ALIGNED(4) const u8 gText_UR_ChooseTrainer[] = _("Escolha um Treinador.");
ALIGNED(4) static const u8 sText_ChooseTrainerSingleBattle[] = _("Escolha um Treinador para\numa batalha simples.");
ALIGNED(4) static const u8 sText_ChooseTrainerDoubleBattle[] = _("Escolha um Treinador para\numa batalha dupla.");
ALIGNED(4) static const u8 sText_ChooseLeaderMultiBattle[] = _("Escolha o líder para\numa batalha múltipla.");
ALIGNED(4) static const u8 sText_ChooseTrainerToTradeWith[] = _("Escolha o Treinador com quem\nvai trocar.");
ALIGNED(4) static const u8 sText_ChooseTrainerToShareWonderCards[] = _("Escolha o Treinador que está\ncompartilhando Cartões Maravilha.");
ALIGNED(4) static const u8 sText_ChooseTrainerToShareWonderNews[] = _("Escolha o Treinador que está\ncompartilhando Notícias Maravilha.");
ALIGNED(4) static const u8 sText_ChooseLeaderPokemonJump[] = _("Pule com Pokémon pequenos!\nEscolha o líder.");
ALIGNED(4) static const u8 sText_ChooseLeaderBerryCrush[] = _("Esmaga Frutas!\nEscolha o líder.");
ALIGNED(4) static const u8 sText_ChooseLeaderBerryPicking[] = _("Colheita do Dodrio!\nEscolha o líder.");

const u8 *const gTexts_UR_ChooseTrainer[] = {
    [LINK_GROUP_SINGLE_BATTLE] = sText_ChooseTrainerSingleBattle,
    [LINK_GROUP_DOUBLE_BATTLE] = sText_ChooseTrainerDoubleBattle,
    [LINK_GROUP_MULTI_BATTLE]  = sText_ChooseLeaderMultiBattle,
    [LINK_GROUP_TRADE]         = sText_ChooseTrainerToTradeWith,
    [LINK_GROUP_POKEMON_JUMP]  = sText_ChooseLeaderPokemonJump,
    [LINK_GROUP_BERRY_CRUSH]   = sText_ChooseLeaderBerryCrush,
    [LINK_GROUP_BERRY_PICKING] = sText_ChooseLeaderBerryPicking,
    [LINK_GROUP_WONDER_CARD]   = sText_ChooseTrainerToShareWonderCards,
    [LINK_GROUP_WONDER_NEWS]   = sText_ChooseTrainerToShareWonderNews
};

ALIGNED(4) const u8 gText_UR_SearchingForWirelessSystemWait[] = _("Procurando um Sistema de\nComunicação Sem Fio. Aguarde...");
ALIGNED(4) static const u8 sText_MustHaveTwoMonsForDoubleBattle[] = _("ダブルバトルでは 2ひき いじょうの\nポケモンが ひつようです\p");
ALIGNED(4) const u8 gText_UR_AwaitingPlayersResponse[] = _("Aguardando resposta de {STR_VAR_1}…");
ALIGNED(4) const u8 gText_UR_PlayerHasBeenAskedToRegisterYouPleaseWait[] = _("{STR_VAR_1} recebeu o pedido para\nregistrar você como membro. Aguarde.");
ALIGNED(4) const u8 gText_UR_AwaitingResponseFromWirelessSystem[] = _("Aguardando resposta do Sistema\nde Comunicação Sem Fio.");
ALIGNED(4) static const u8 sText_PleaseWaitForOtherTrainersToGather[] = _("ほかの さんかしゃが そろうまで\nしょうしょう おまちください");

ALIGNED(4) static const u8 sText_NoCardsSharedRightNow[] = _("Parece que nenhum Cartão está \nsendo compartilhado agora.");
ALIGNED(4) static const u8 sText_NoNewsSharedRightNow[] = _("Parece que nenhuma Notícia está\nsendo compartilhada agora.");

const u8 *const gTexts_UR_NoWonderShared[] = {
    sText_NoCardsSharedRightNow,
    sText_NoNewsSharedRightNow
};

ALIGNED(4) const u8 gText_UR_Battle[] = _("Batalha");
ALIGNED(4) const u8 gText_UR_Chat2[] = _("Chat");
ALIGNED(4) const u8 gText_UR_Greetings[] = _("Saudação");
ALIGNED(4) const u8 gText_UR_Exit[] = _("Sair");

ALIGNED(4) const u8 gText_UR_Exit2[] = _("Sair");
ALIGNED(4) const u8 gText_UR_Info[] = _("Info");
ALIGNED(4) const u8 gText_UR_NameWantedOfferLv[] = _("Nome{CLEAR_TO 0x3C}Procura{CLEAR_TO 0x6E}Oferece{CLEAR_TO 0xC6}Nv.");

ALIGNED(4) const u8 gText_UR_SingleBattle[] = _("Batalha simples");
ALIGNED(4) const u8 gText_UR_DoubleBattle[] = _("Batalha dupla");
ALIGNED(4) const u8 gText_UR_MultiBattle[] = _("Batalha múltipla");
ALIGNED(4) const u8 gText_UR_PokemonTrades[] = _("Trocas de Pokémon");
ALIGNED(4) const u8 gText_UR_Chat[] = _("Chat");
ALIGNED(4) const u8 gText_UR_Cards[] = _("Cartões");
ALIGNED(4) const u8 gText_UR_WonderCards[] = _("Cartões Maravilha");
ALIGNED(4) const u8 gText_UR_WonderNews[] = _("Notícias Maravilha");
ALIGNED(4) const u8 gText_UR_PokemonJump[] = _("Pulo Pokémon");
ALIGNED(4) const u8 gText_UR_BerryCrush[] = _("Esmaga Frutas");
ALIGNED(4) const u8 gText_UR_BerryPicking[] = _("Colheita do Dodrio");
ALIGNED(4) const u8 gText_UR_Search[] = _("Busca");
ALIGNED(4) const u8 gText_UR_SpinTrade[] = _("ぐるぐるこうかん");
ALIGNED(4) const u8 gText_UR_ItemTrade[] = _("アイテムトレード");

ALIGNED(4) static const u8 sText_ItsNormalCard[] = _("É um Cartão Normal.");
ALIGNED(4) static const u8 sText_ItsBronzeCard[] = _("É um Cartão Bronze!");
ALIGNED(4) static const u8 sText_ItsCopperCard[] = _("É um Cartão Cobre!");
ALIGNED(4) static const u8 sText_ItsSilverCard[] = _("É um Cartão Prata!");
ALIGNED(4) static const u8 sText_ItsGoldCard[] = _("É um Cartão Ouro!");

const u8 *const gTexts_UR_CardColor[] = {
    sText_ItsNormalCard,
    sText_ItsBronzeCard,
    sText_ItsCopperCard,
    sText_ItsSilverCard,
    sText_ItsGoldCard
};

ALIGNED(4) const u8 gText_UR_TrainerCardInfoPage1[] = _("Este é o Cartão de Treinador\nde {DYNAMIC 0} {DYNAMIC 1}…\l{DYNAMIC 2}\pPokédex: {DYNAMIC 3}\nTempo:   {DYNAMIC 4}:{DYNAMIC 5}\p");
ALIGNED(4) const u8 gText_UR_TrainerCardInfoPage2[] = _("Batalhas: {DYNAMIC 0} V.  {DYNAMIC 2} D.\nTrocas:  {DYNAMIC 3} vezes\p“{DYNAMIC 4} {DYNAMIC 5}\n{DYNAMIC 6} {DYNAMIC 7}”\p");
ALIGNED(4) static const u8 sText_GladToMeetYouMale[] = _("{DYNAMIC 1}: Foi um prazer!{PAUSE 60}");
ALIGNED(4) static const u8 sText_GladToMeetYouFemale[] = _("{DYNAMIC 1}: Muito prazer!{PAUSE 60}");

const u8 *const gTexts_UR_GladToMeetYou[GENDER_COUNT] = {
    sText_GladToMeetYouMale,
    sText_GladToMeetYouFemale
};

ALIGNED(4) const u8 gText_UR_FinishedCheckingPlayersTrainerCard[] = _("Viu todo o Cartão de Treinador\nde {DYNAMIC 1}.{PAUSE 60}");
ALIGNED(4) static const u8 sText_CanceledReadingCard[] = _("A leitura do Cartão foi cancelada.");

static const struct MysteryGiftClientCmd sClientScript_DynamicError[] = {
    {CLI_RECV, MG_LINKID_DYNAMIC_MSG},
    {CLI_COPY_MSG},
    {CLI_SEND_READY_END},
    {CLI_RETURN, CLI_MSG_BUFFER_FAILURE}
};

const struct MysteryGiftServerCmd gServerScript_ClientCanceledCard[] = {
    {SVR_LOAD_CLIENT_SCRIPT, PTR_ARG(sClientScript_DynamicError)},
    {SVR_SEND},
    {SVR_LOAD_MSG, PTR_ARG(sText_CanceledReadingCard)},
    {SVR_SEND},
    {SVR_RECV, MG_LINKID_READY_END},
    {SVR_RETURN, SVR_MSG_CLIENT_CANCELED}
};
