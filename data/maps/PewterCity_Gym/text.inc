PewterCity_Gym_Text_BrockIntro::
    .string "Então você chegou. Sou o Brock,\n"
    .string "Líder do Ginásio de Pewter.\p"
    .string "Minha vontade é dura como pedra,\n"
    .string "e isso aparece nos meus Pokémon.\p"
    .string "Meus Pokémon são duros como rocha\n"
    .string "e têm muita garra.\p"
    .string "Isso mesmo: todos os meus Pokémon\n"
    .string "são do tipo Pedra!\p"
    .string "Fuhaha! Vai me desafiar mesmo\n"
    .string "sabendo que vai perder?\p"
    .string "É a honra de Treinador que leva\n"
    .string "você a me desafiar.\p"
    .string "Pois bem!\n"
    .string "Mostre o seu melhor!{PLAY_BGM}{MUS_ENCOUNTER_GYM_LEADER}$"

@ NOTE: This defeat text actually causes a buffer overflow. It's too long for the gDisplayedStringBattle
@ buffer that it's put into, and it stomps all over the gBattleTextBuffs after, as well as the otherwise
@ unused array after that, sFlickerArray. Perhaps that's the reason why said array exists.
PewterCity_Gym_Text_BrockDefeat::
    .string "Eu subestimei você e,\n"
    .string "por isso, perdi.\p"
    .string "Como prova da sua vitória, eu lhe\n"
    .string "concedo… a Insígnia Rocha oficial\l"
    .string "da Liga Pokémon.\p"
    .string "{FONT_NORMAL}{PLAYER} recebeu a Insígnia Rocha\n"
    .string "do Brock!{PAUSE_MUSIC}{PLAY_BGM}{MUS_OBTAIN_BADGE}{PAUSE 0xFE}{PAUSE 0x56}{RESUME_MUSIC}\p"
    .string "{FONT_MALE}Só de ter a Insígnia Rocha, seus\n"
    .string "Pokémon ficam mais fortes.\p"
    .string "Ela também permite usar o golpe\n"
    .string "Clarão fora das batalhas.\p"
    .string "Claro, o Pokémon precisa saber\n"
    .string "o golpe Clarão para usá-lo.$"

PewterCity_Gym_Text_TakeThisWithYou::
    .string "Espere!\n"
    .string "Leve isto com você.$"

PewterCity_Gym_Text_ReceivedTM39FromBrock::
    .string "{PLAYER} recebeu a MT39\n"
    .string "do Brock.$"

PewterCity_Gym_Text_ExplainTM39::
    .string "Uma MT, Máquina Técnica, contém\n"
    .string "uma técnica para Pokémon.\p"
    .string "Usar uma MT ensina o golpe que ela\n"
    .string "contém a um Pokémon.\p"
    .string "Uma MT só pode ser usada uma vez.\p"
    .string "Por isso, na hora de usar, escolha\n"
    .string "o Pokémon com cuidado.\p"
    .string "Enfim…\n"
    .string "a MT39 contém Tumba de Rochas.\p"
    .string "Ela arremessa pedregulhos no\n"
    .string "inimigo e reduz a sua Velocidade.$"

PewterCity_Gym_Text_BrockPostBattle::
    .string "Há todo tipo de Treinador neste\n"
    .string "nosso mundo enorme.\p"
    .string "Você parece ter muito talento\n"
    .string "para treinar Pokémon.\p"
    .string "Então deixe-me dar uma sugestão.\p"
    .string "Vá ao Ginásio de Cerulean e teste\n"
    .string "as suas habilidades.$"

PewterCity_Gym_Text_DontHaveRoomForThis::
    .string "Você não tem espaço para isto.$"

PewterCity_Gym_Text_LiamIntro::
    .string "Pare aí, criança!\p"
    .string "Você está a dez mil anos-luz de\n"
    .string "enfrentar o Brock!$"

PewterCity_Gym_Text_LiamDefeat::
    .string "Droga!\p"
    .string "Anos-luz não medem tempo…\n"
    .string "Medem distância!$"

PewterCity_Gym_Text_LiamPostBattle::
    .string "Você é demais.\n"
    .string "…Mas não tanto quanto o Brock!$"

PewterCity_Gym_Text_LetMeTakeYouToTheTop::
    .string "Oi!\n"
    .string "Quer sonhar alto?\p"
    .string "Você tem coragem de sonhar com o\n"
    .string "título de campeão Pokémon?\p"
    .string "Eu não sou Treinador, mas posso\n"
    .string "ensinar como vencer.\p"
    .string "Deixe-me levar você ao topo!$"

PewterCity_Gym_Text_LetsGetHappening::
    .string "Beleza!\n"
    .string "Vamos nessa!$"

PewterCity_Gym_Text_TryDifferentPartyOrders::
    .string "O primeiro Pokémon a entrar na\n"
    .string "luta é o da esquerda da lista.\p"
    .string "Mudando a ordem dos Pokémon, você\n"
    .string "pode levar vantagem.\p"
    .string "Teste ordens diferentes de acordo\n"
    .string "com o grupo do seu oponente.$"

PewterCity_Gym_Text_ItsFreeLetsGetHappening::
    .string "É um serviço gratuito!\n"
    .string "Vamos nessa!$"

PewterCity_Gym_Text_YoureChampMaterial::
    .string "Eu sabia!\n"
    .string "Você tem tudo para conquistar o\n"
    .string "título de campeão Pokémon!$"

PewterCity_Gym_Text_GymStatue::
    .string "Ginásio Pokémon de Pewter\n"
    .string "Líder: Brock\p"
    .string "Quem já venceu o Ginásio:\n"
    .string "{RIVAL}$"

PewterCity_Gym_Text_GymStatuePlayerWon::
    .string "Ginásio Pokémon de Pewter\n"
    .string "Líder: Brock\p"
    .string "Quem já venceu o Ginásio:\n"
    .string "{RIVAL}, {PLAYER}$"

