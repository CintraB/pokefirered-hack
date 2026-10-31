@ POK-44: o aviso de conquista. Conquistas_TentarAviso (src/conquistas_aviso.c) põe este script no campo quando há
@ prêmio a entregar; o special entrega o prêmio, mostra a janela e reativa o script ao fechar (waitstate).
EventScript_AvisoConquista::
	goto_if_questlog EventScript_ReleaseEnd
	lockall
	specialvar VAR_RESULT, Conquistas_MostrarAviso
	goto_if_eq VAR_RESULT, FALSE, EventScript_AvisoConquistaSemTask
	waitstate
	releaseall
	end

@ sem task livre para o aviso: nada foi entregue, e o aviso volta num quadro livre seguinte
EventScript_AvisoConquistaSemTask::
	releaseall
	end

