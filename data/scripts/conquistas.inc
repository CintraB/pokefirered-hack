@ POK-44: o aviso de conquista. Conquistas_TentarAviso (src/conquistas_aviso.c) põe este script no campo quando há
@ prêmio a entregar; o special entrega o prêmio, mostra a janela e reativa o script ao fechar (waitstate).
@ O waitfanfare (como no Std_ObtainItem) segura o campo até a fanfarra acabar: sem ele, um menu ou uma porta logo
@ depois do aviso roda o ResetTasks, mata o Task_Fanfare e a música do mapa não volta mais.
EventScript_AvisoConquista::
	goto_if_questlog EventScript_ReleaseEnd
	lockall
	specialvar VAR_RESULT, Conquistas_MostrarAviso
	goto_if_eq VAR_RESULT, FALSE, EventScript_AvisoConquistaSemTask
	waitstate
	waitfanfare
	releaseall
	end

@ sem task livre para o aviso: nada foi entregue (nem fanfarra), e o aviso volta num quadro livre seguinte
EventScript_AvisoConquistaSemTask::
	releaseall
	end

