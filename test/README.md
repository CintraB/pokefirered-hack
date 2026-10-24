# Esteira de testes

A esteira joga a ROM de verdade num emulador (mGBA, sem janela) apertando botões e lendo a
memória, confere o log do build e os textos do jogo, e só entrega a ROM versionada
(`roms/<N>.0/`) se tudo passou. O relatório de cada execução é uma página HTML com telas, o
vídeo acelerado da execução e o tempo de cada etapa.

Tudo roda dentro do WSL (Ubuntu). A ROM testada é sempre a `pokefirered_switch.gba` da raiz do
repo.

| Quero... | Comando (dentro do WSL, na raiz do repo) | Tempo |
|---|---|---|
| Compilar, testar e versionar a ROM | `make firered_switch` | build + ~35 s de teste |
| Compilar e versionar **sem** testar | `SKIP_TESTS=1 make firered_switch` | só o build |
| Testar de novo a ROM já compilada, sem versionar | `make test-quick` | ~35 s |
| Teste completo (cenários longos, ROM de teste) | `make test-full` | ~4 min (em paralelo; ~16 min com `ESTEIRA_JOBS=1`) |
| Ver o roteiro rápido numa janela | `make test-watch` | ~ tempo real |
| Ver as evoluções sem troca (Hack 3) numa janela | `make test-watch CENARIO=evolucoes` | ~9 min (tempo real) |
| Ver a página EVOLUTION do resumo (Hack 4) numa janela | `make test-watch CENARIO=resumo_evolucao` | ~2 min (tempo real) |
| Ver a página IVs/EVs do resumo (Hack 5) numa janela | `make test-watch CENARIO=resumo_ivs` | ~2 min (tempo real) |
| Ver um ovo da creche chocar (Hack 6) numa janela | `make test-watch CENARIO=ovo` | ~1,5 min (tempo real) |
| Ver o relógio, a hora no menu, o aviso e o tom de cor (Hack 7) numa janela | `make test-watch CENARIO=relogio` | tempo real |
| Ver o clima por região e o granizo na batalha (Hack 7) numa janela | `make test-watch CENARIO=clima` | tempo real |
| Ver outro cenário do Hack 7 numa janela | `make test-watch CENARIO=encontros` (ou `dex_nacional`, `pos_liga`, `evo_dia_noite`, `resumo_amizade`) | tempo real |
| Aprovar as telas de referência | `make test-approve` | instantâneo |
| Testes unitários da própria esteira | `python3 -m pytest test -q` | ~40 s (~1,5 min na 1ª vez depois de ligar o WSL) |

> **Atenção: nunca rode `python3` ou `python` no PowerShell nem no Git Bash do Windows.**
> Nesta máquina isso é um alias do Windows que abre a Microsoft Store (App Execution Alias).
> Python só dentro do WSL.

## Como chamar os comandos

**De dentro do WSL** (recomendado: abra uma vez e use à vontade):

```powershell
wsl -d Ubuntu --cd /mnt/c/Users/crist/Documents/GitHub/pokefirered
```

Depois, no prompt do Ubuntu, os comandos da tabela acima valem como estão.

**Direto do PowerShell**, uma linha por comando. Use aspas simples em volta do comando para o
PowerShell não mexer em variáveis:

```powershell
wsl -d Ubuntu --cd /mnt/c/Users/crist/Documents/GitHub/pokefirered -- bash -c 'make firered_switch'
wsl -d Ubuntu --cd /mnt/c/Users/crist/Documents/GitHub/pokefirered -- bash -c 'SKIP_TESTS=1 make firered_switch'
wsl -d Ubuntu --cd /mnt/c/Users/crist/Documents/GitHub/pokefirered -- make test-quick
```

Os relatórios são arquivos normais do Windows: abra o `relatorio.html` com duplo clique
(por exemplo `C:\Users\crist\Documents\GitHub\pokefirered\roms\5.0\relatorio.html`).

## O que acontece em `make firered_switch`

1. Compila a ROM. O log do build é guardado em `build/firered_switch.log`.
2. Roda a **esteira rápida** (~35 s) em `test/out/<data-hora>/`:
   - **log do build**: erro de compilação, aviso novo do compilador, do assembler ou do linker, ou
     EWRAM/IWRAM em 100% ou mais reprovam;
   - **textos do jogo**: caractere fora do charmap, falta de terminador, linha larga demais
     para a caixa, linhas demais, nome longo demais para o buffer, sintaxe; e, para a tradução,
     códigos de controle diferentes do original, termo fora do glossário, texto copiado para um
     buffer fixo menor que ele (regra `buffer`) e texto com palavra inglesa (regra `ingles`);
   - **3 roteiros no emulador**: `abertura` (nome, inicial, batalha do rival), `rota1`
     (passos, Rota 1, encomenda do Oak) e `captura` (loja, captura com apelido, Poção, Centro,
     salvar, reiniciar e continuar).
3. Conforme o resultado:

| Resultado | O que faz | Como reconhecer |
|---|---|---|
| **Verde** (exit 0) | Copia a ROM e o relatório para `roms/<N>.0/` (próximo número livre). | `Versioned ... -> roms/N.0/` |
| **Vermelho** (teste reprovou) | Copia a execução inteira para `roms/ultima-falha/` (substitui a anterior), **apaga a ROM** e sai com erro. O próximo `make firered_switch` refaz a ROM (recompilando o que deu aviso de build) e **testa de novo**. | `[esteira] REPROVADA: ROM removida; relatorio em roms/ultima-falha/relatorio.html` |
| **Falha de infraestrutura** (a esteira nem chegou a concluir: sem Python, Ctrl-C, crash sem relatório, log de build incompleto, runner do emulador sem compilar) | **Não versiona** e **não mexe** em `ultima-falha`. Apaga a ROM (o próximo make retesta) e sai com erro. | `[esteira] falha de infraestrutura: <motivo>` |

Diferença prática: "vermelho" quer dizer que o jogo tem um problema, e o relatório mostra qual.
"Infraestrutura" quer dizer que o teste não rodou direito; leia a mensagem, corrija o ambiente e
rode o make de novo. A ROM é apagada nos dois casos de propósito: se ela ficasse lá, o make diria
"Nothing to be done" e uma ROM sem teste pareceria pronta.

Só a `pokefirered_switch.gba` passa pela esteira. As outras ROMs (`firered`, `leafgreen`...) só
são versionadas, e builds de comparação (`COMPARE=1`) e de teste (`*_test.gba`) não são tocados.
Erro de compilação derruba o `make` antes da esteira; o log fica em `build/firered_switch.log`.

### `SKIP_TESTS=1`

`SKIP_TESTS=1 make firered_switch` pula o emulador e **versiona a ROM mesmo assim**, marcada:
a pasta `roms/<N>.0/` ganha o arquivo `NAO_TESTADA.txt` e o `relatorio.html` abre com uma faixa
vermelha **ROM NÃO TESTADA**. Serve para quando você precisa da ROM agora; teste depois com
`make test-quick`.

### Onde ficam as coisas

| O quê | Onde |
|---|---|
| ROM, relatório, telas, vídeo e `meta.json` da versão | `roms/<N>.0/` (`pokefirered_switch.gba`, `relatorio.html`, `img/`, `video.webp`, `meta.json`) |
| Última execução reprovada | `roms/ultima-falha/` (relatório, telas, `estados/`, savestates de depuração) |
| Toda execução (verde ou vermelha, inclusive `make test-quick`) | `test/out/<data-hora>/` |
| Log do último build | `build/firered_switch.log` (`..._test.log` para a build de teste) |
| Estado do rodízio de iniciais | `roms/estado-esteira.json` |
| Saves reais | `roms/saves/` (a esteira **nunca** escreve aí) |

Mantenha o `relatorio.html` junto das pastas/arquivos `img/` e `video.webp`: a página os
referencia por caminho relativo. `meta.json` tem inicial usado, data, commit, modo, tempos e se a
ROM foi testada. `roms/` e `test/out/` não vão para o Git. **`test/out/` guarda só as 15
execuções mais novas**: no fim de cada `make firered_switch` as pastas `<data-hora>` mais antigas
são apagadas (inclusive as dos `make test-*`). O resto de `test/out/` (por exemplo `fixtures/`,
o cache de um teste unitário) nunca é tocado. Para guardar uma execução, copie-a para fora.

### Rodízio de iniciais

As execuções usam os iniciais em ordem: Bulbasaur, Charmander, Squirtle, Bulbasaur... O
`roms/estado-esteira.json` guarda o último inicial de uma execução **verde**
(`{"inicial": "SQUIRTLE"}`); a execução seguinte usa o próximo da lista. Arquivo ausente ou
ilegível recomeça em Bulbasaur.

- **O rodízio só avança quando a execução termina verde.** Uma reprovação (ou falha de
  infraestrutura) **repete o mesmo inicial** na próxima: um bug que só aparece com um inicial
  não some no reteste só porque o inicial trocou. Corrija e rode de novo; o inicial muda quando
  passar. Se precisar da ROM antes, `SKIP_TESTS=1` (que não mexe no rodízio).
- `--starter X` e o `make test-watch` não mexem no rodízio. Para forçar um:
  `python3 -m esteira rapido ... --starter CHARMANDER` (veja abaixo).

## Comandos manuais

Rodam sobre a ROM que já está na raiz (`pokefirered_switch.gba`) e **não versionam nada**. Os que
usam o emulador (todos menos o `test-approve`) recompilam antes o runner do emulador
(`test/harness`) se ele estiver desatualizado.

### `make test-quick`

Os mesmos testes do `make firered_switch` (checagem do log, dos textos e os 3 roteiros),
~35 s, resultado em `test/out/<data-hora>/`. Usa o `build/firered_switch.log` do último build
tratado como no pipeline (`test/build_log.sh`): cortado na marca de fim de build e completado
com o uso de memória do link (`build/firered_switch/memory.txt`) quando o último make só refez a
ROM. Sem o log, só o uso de memória é conferido (o terminal avisa). Deixa os savestates em
`estados/`, que o `make test-watch --from` aproveita.

### `make test-full`

1. Recompila a **ROM de teste** (`pokefirered_switch_test.gba`/`.elf`, `make firered_switch
   TESTBUILD=1`, objetos em `build/firered_switch_test`). A ROM jogável **não** é recompilada
   nem alterada. A primeira vez compila tudo do zero; a ROM de teste nunca é versionada.
2. Roda o modo `completo` (rápido + cenários completos):

| Cenário | Roda em | O que confere |
|---|---|---|
| `pc` | ROM jogável | PC do Bill: depositar, salvar/reiniciar, retirar |
| `telas` | ROM jogável | Tour de telas (bolsa, resumo, Pokédex, opções, cartão, PC, loja, mapa): só screenshots comparados com as referências |
| `floresta_brock` | ROM jogável | Floresta de Viridian, prêmios dos treinadores, Brock (adaptativo), tênis de corrida e ritmo de corrida |
| `master` | sem emulador | O branch `master` (pret original) ainda compila idêntico ao original (SHA1), numa worktree temporária em `/tmp` |
| `shiny` | **ROM de teste** | Shiny Charm e taxa de shiny com/sem o charm (usa atalhos da build de teste) |
| `evolucoes` | **ROM de teste** | Hack 3, fim das evoluções por troca e da trava da Dex Nacional: Rare Candy/pedra pela bolsa e a cena de evolução de verdade para os 11 Pokémon (nível 37, com/sem item segurado), Bellossom e Crobat, item errado, "passou do 37 sem item" e a troca que não evolui mais, tudo sem a Dex Nacional (veja abaixo) |
| `resumo_evolucao` | **ROM de teste** | Hack 4, página EVOLUTION do resumo: o texto de todas as 386 espécies, a página pelo menu de verdade (→/←, troca de Pokémon com ↓), ovo e modo de aprender golpe sem a página (veja abaixo) |
| `resumo_ivs` | **ROM de teste** | Hack 5, página IVs/EVs do resumo: o texto da página para as bordas do design, todos os tipos de Hidden Power e 150 combinações sorteadas, a página pelo menu de verdade (→/←, ↓ entre 5 Pokémon com IVs/EVs escolhidos) e o ovo sem a página (veja abaixo) |
| `creche` | **ROM de teste** | Hack 6, breeding genético: ~21 000 ovos pelo caminho real da creche comparados com a distribuição exata das regras (IVs, natureza, habilidade, golpes de ovo, gênero, itens), taxa de shiny dos ovos com/sem charm e os Power items em batalha (veja abaixo) |
| `ovo` | **ROM de teste** | Hack 6: um ovo de verdade na creche de Four Island, entregue pelo velho, chocado andando e conferido na memória, e a loja de Four Island |
| `relogio` | **ROM de teste** | Hack 7: relógio do jogo (anda, salva, save antigo), hora no menu Start, aviso de troca de período e tom de cor por período (veja abaixo) |
| `clima_visual` | **ROM de teste** | Hack 7: neve, cinzas, areia e neblina visíveis no campo (flocos caindo, blend e paleta do Emerald, neblina externa mais fraca) |
| `encontros` | **ROM de teste** | Hack 7: encontros de grama/caverna por horário (manhã/tarde/noite; entardecer meio a meio) e a área da Pokédex |
| `dex_nacional` | **ROM de teste** | Hack 7: Pokédex Nacional na tela desde o início, sem ligar a flag do pós-Liga |
| `pos_liga` | **ROM de teste** | Hack 7: cena pós-Liga do Prof. Carvalho (Ovo raro na equipe, no PC ou guardado pelo Oak, ₽45.000, objetivo do Amuleto Brilhante) |
| `evo_dia_noite` | **ROM de teste** | Hack 7: Espeon de dia, Umbreon de noite/entardecer, Milotic pela Escama Prisma e a Escama Prisma na loja de Four Island |
| `resumo_amizade` | **ROM de teste** | Hack 7: linha de amizade com corações na página EVOLUTION do resumo |
| `clima` | **ROM de teste** | Hack 7: clima dinâmico por região e período, interiores/cavernas/climas fixos, troca de período e volta da bolsa, e o clima do mapa na batalha (neve → granizo, areia, chuva) |

Depende da ROM jogável da raiz (se não existir, vira falha `emulador/rom-playable`). Não grava
em `roms/`: o resultado fica em `test/out/<data-hora>/`. Leva **~4 min** (os cenários rodam em
paralelo, veja **Paralelismo**; ~45 s disso é o `make` da ROM de teste conferindo que está em
dia). O caminho mais longo é a corrente jogável (rápido → `pc` → `telas` → `floresta_brock`,
~3 min); o `shiny` (~8 min sozinho) e a `creche` (~4 min sozinha) vão em pedaços ao lado dela.
Com `ESTEIRA_JOBS=1` volta a ser sequencial: ~16 min.

O `shiny`, o `evolucoes`, o `resumo_evolucao` e o `resumo_ivs` partem do mesmo save do jogo (o `.sav` do fim do
`captura`), cada um numa **sessão própria** da ROM de teste: um não herda o que o outro fez (o
shiny liga a Dex Nacional e ganha o Shiny Charm), e `--only evolucoes` roda só ele (~30 s;
`--only resumo_evolucao` e `--only resumo_ivs`, ~5 s cada).

**O cenário `evolucoes`** (`test/esteira/scenarios/full_evolutions.py`; as regras ficam numa
tabela só, `test/esteira/evolutions.py`). Os atalhos da build de teste só montam o Pokémon no
time (espécie, nível, item segurado, amizade) e dão Rare Candies, Metal Coat e Sun Stone; a
subida de nível é a de verdade (START > BOLSA > RARE CANDY > USAR; a pedra também, pela bolsa)
e a cena de evolução roda inteira. Se o jogo perguntar sobre golpe novo, o cenário recusa (NÃO
para esquecer um golpe, SIM para desistir) e confere que nenhum golpe foi esquecido. Tudo
**sem a Dex Nacional** (como no save): o hack tirou a trava original do FireRed que cancelava
evoluções para espécies de fora de Kanto (Crobat, Steelix...) antes dela. Ordem:

1. os 12 casos das regras evoluem: Kadabra, Haunter, Machoke e Graveler 36 → 37; Slowking,
   Politoed, Steelix, Scizor, Kingdra, Porygon2, Huntail e Gorebyss, com o item continuando
   segurado; e Slowpoke 36 sem item vira Slowbro;
2. de fora de Kanto por outros caminhos: Gloom + Sun Stone (pela bolsa) → Bellossom; Golbat com
   amizade 250 + Rare Candy → Crobat;
3. Onix 36 com King's Rock (item errado) e Clamperl 36 sem item não evoluem;
4. Onix 39 sem item sobe para 40 e continua Onix; recebe o Metal Coat pela bolsa (DAR); sobe
   para 41 e vira Steelix, ainda segurando o Metal Coat;
5. `GetEvolutionTargetSpecies` no modo troca devolve 0 para os 11, com e sem o item antigo;
6. no fim a Dex Nacional continua desligada.

Telas antes/depois de cada cena: `telas/evo_<alvo>_antes.png` e `_depois.png`, comparadas com
`test/referencias/COMUM/` (não dependem do inicial). O teste estático
`test/tests/test_evolucoes_estatico.py` (pytest, sem emulador) confere a tabela de evoluções, o
método novo no C, que a trava da Dex Nacional não voltou (cena de evolução normal e de troca,
pedras no menu de Pokémon, modo troca de `GetEvolutionTargetSpecies`) e os 6 itens à venda na
Celadon Dept. Store 4F por 2100.

**O cenário `resumo_evolucao`** (Hack 4; `test/esteira/scenarios/full_summary_evolution.py`).
O resumo do Pokémon ganhou a 4ª página, **EVOLUTION** (depois de INFO / SKILLS / KNOWN MOVES),
que lista como a espécie evolui, uma linha por entrada da tabela de evoluções. Quem monta o
texto é `GetEvolutionPageText` (`src/pokemon_summary_screen.c`); os formatos e o texto
esperado de cada espécie, gerado em Python dos fontes (`evolution.h`, `species_names.h`,
`items.json`), ficam em `test/esteira/evolution_page.py`. Os atalhos da build de teste montam o
time (Eevee, Onix, Slowpoke, Bulbasaur e Tauros nos slots 0-4 e um ovo de Togepi no 5), dão uma
Rare Candy e leem o estado do resumo (página, modo, ovo) e o texto que a página imprimiu. Ordem:

1. `GetEvolutionPageText` de **todas** as espécies (1..CHIMECHO, sem as OLD_UNOWN) é igual,
   byte a byte, ao texto esperado;
2. START > POKéMON > Eevee > RESUMO, → três vezes até a página EVOLUTION (conferida pela
   página ativa na memória e pelo texto impresso); ← volta para KNOWN MOVES e → de novo;
3. ↓ na página EVOLUTION troca para Onix, Slowpoke, Bulbasaur e Tauros sem sair da página
   (texto de cada um); ↓ no Tauros não vai para o ovo;
4. o resumo do ovo não sai da página INFO com →;
5. Tauros 18 + Rare Candy quer aprender PURSUIT: SIM abre o resumo de escolher o golpe a
   esquecer (modo `PSS_MODE_SELECT_MOVE`), onde → não leva à página EVOLUTION; B cancela, SIM
   desiste de aprender e nenhum golpe muda.

Telas da página: `telas/resumo_evo_<espécie>.png` e, do Eevee, `telas/resumo_pag_skills.png`,
`resumo_pag_moves.png` e `resumo_pag_detalhe.png` (os pontos de página do cabeçalho), comparadas
com `test/referencias/COMUM/` (e `telas/resumo_evo_escolher_golpe.png`, só registro). O teste `test/tests/test_resumo_evolucao.py`
(pytest) confere sem emulador os casos fixos (Bulbasaur, Eevee, Onix, Slowpoke, Feebas, Tauros,
Wurmple, Nincada, Tyrogue), a largura e o tamanho do texto de toda espécie, a ligação com
`src/strings.c` e o C da página; e, se a ROM de teste estiver em dia, o texto do jogo de todas
as espécies. A largura das linhas montadas também entra na checagem de **textos do jogo** da
esteira rápida (veja **Largura do texto**).

**O cenário `resumo_ivs`** (Hack 5; `test/esteira/scenarios/full_summary_ivs.py`; design em
`docs/superpowers/specs/2026-10-17-pagina-ivs-evs-design.md`). A 5ª página do resumo,
**IVs/EVs** (depois de EVOLUTION, com as mesmas regras: sem ovo, sem os modos de golpe), mostra
o IV de cada atributo com o nível (31 Perfect, 26-30 Excellent, 16-25 Very good, 1-15 Good, 0
Poor), o EV de cada um, o total de IVs com % (arredondado) e avaliação geral (186 Perfect,
151-185 Outstanding, 121-150 Above average, 91-120 Average, 0-90 Below average), o total de
EVs (/510) e o Hidden Power (tipo e poder, pela mesma função `CalcHiddenPower` que o golpe usa
em batalha). Quem monta o texto é `GetIvEvPageText`; as contas e o texto esperado, em Python,
ficam em `test/esteira/ivev_page.py`. O atalho `IVEV_TEXT` da build de teste dá IVs/EVs a um
Pokémon (novo ou do time) e devolve o texto da página. Ordem:

1. o texto do jogo é igual, byte a byte, ao calculado em Python nas bordas (tudo 31, tudo 0,
   25/26, 15/16, EVs 510, todos os tipos de Hidden Power) e em 150 combinações sorteadas;
2. time: Mewtwo (tudo 31, 510 EVs), Magikarp (tudo 0), Eevee (limites), Charizard (Hidden Power
   70) e Tauros (120, Average) + um ovo; START > POKéMON > SUMMARY, → quatro vezes até IVs/EVs
   (página ativa na memória e texto impresso); ← volta para EVOLUTION e → de novo;
3. ↓ na página troca de Pokémon (os 5) sem sair dela; ↓ no último não vai para o ovo;
4. o resumo do ovo não sai da página INFO com →.

Telas: `telas/resumo_ivs_<espécie>.png`, comparadas com `test/referencias/COMUM/`. O pytest
`test/tests/test_resumo_ivs.py` confere as contas nos limites do design, a ligação com
`src/strings.c` e com o C (colunas, janela, `Cmd_hiddenpowercalc` usando `CalcHiddenPower`), a
largura e, com a ROM de teste em dia, o texto do jogo.

**Hack 6, breeding genético: `creche` e `ovo`** (`test/esteira/scenarios/full_breeding.py` e
`full_egg.py`; as regras e o modelo exato ficam numa tabela só, `test/esteira/breeding.py`,
e as probabilidades do C em `include/constants/daycare.h`). Cada um numa sessão própria da ROM
de teste, a partir do `captura.sav`:

- `creche` (~3,7 min): para 9 pares de pais (sem item, Everstone + Destiny Knot, Power items
  diferentes e iguais, dois Everstones, Ditto como mãe e como pai, pai de uma habilidade só,
  sem gênero + Ditto) o atalho põe os dois na creche de verdade e gera ~21 000 ovos pelo
  caminho real (ovo pendente + `GiveEggFromDaycare`, o mesmo do velho da creche). Confere contra
  a distribuição **exata** das regras: IVs (qui-quadrado dos 32 valores e média de cada
  atributo), natureza (qui-quadrado das 25 e a frequência da natureza de cada pai), habilidade
  60/40 com 10% de mutação e o pai "sem informação" (Ditto/uma habilidade só), golpes de ovo
  60%/40%/76% e gênero sem viés. Depois: o ovo entregue tem exatamente a personalidade que a
  rotina de sorteio dá a partir do mesmo RNG, a taxa de shiny dessa rotina com e sem o Shiny
  Charm (400 000 cada, ±3σ, ~1/4096 e ~1/2048) e os Power items em batalha (`MonGainEVs` com +8
  no atributo e os limites 255/510; `GetWhoStrikesFirst` com a Velocidade pela metade).
  Proporções usam ±4σ e as distribuições qui-quadrado com p ≥ 1e-5 (muitas checagens: o falso
  vermelho total fica perto de 1%, metade dele no shiny a ±3σ, como no `shiny`).
- `ovo` (~5 s): atalhos montam os pais com um ovo pendente, pulam a cena do rival e levam o
  jogador até o velho da creche em Four Island; daí é o jogo: SIM para o ovo, o ovo é
  conferido, o atalho zera os ciclos que faltam e o jogador **anda** até ele chocar (cena
  inteira, apelido recusado); o filhote tem de ser o ovo (personalidade, IVs, golpes, natureza,
  habilidade, gênero). Por fim entra na loja de Four Island (dinheiro posto pelo atalho) e confere
  os 8 itens de empurrão e os preços. Telas `ovo_recebido`, `ovo_chocando` e `ovo_chocado` (sem
  referência) e `loja_four_island`/`loja_four_island_quantidade` (preço de 5 dígitos do Destiny
  Knot), comparadas com `test/referencias/COMUM/`.
  Numa janela: `make test-watch CENARIO=ovo` (~1,5 min em tempo real).

O teste estático `test/tests/test_breeding_estatico.py` confere as probabilidades do C contra o
design, os 7 itens novos (slots 53-59, preço, efeito, ícone 24×24 4bpp e paleta JASC CRLF), a
Everstone a ₽7000, a loja de Four Island e o próprio modelo (contra uma simulação independente
das regras, com poder para reprovar uma regra errada).

**Hack 7, dia/noite e clima** (design em `docs/superpowers/specs/2026-10-17-dia-noite-clima-design.md`).
O jogo ganhou um relógio próprio (`gSaveBlock2Ptr->gameClockFrames`: 150 quadros = 1 minuto do
jogo, 1 dia = 1 h real; jogo novo e save antigo começam às 08:00 do dia 0) com quatro períodos:
manhã 04–10, tarde 10–17, entardecer 17–20 e noite 20–04. As regras ficam em Python em
`test/esteira/dia_noite.py` (tom de cor, sorteio do clima) e os atalhos da build de teste são os
`0x70`–`0x7B` de `include/test_hooks.h` (`SET_CLOCK`, `CLOCK_INFO`, `TINT_AT`, `ROLL_WEATHER`,
`LAND_SPECIES`, `FRIENDSHIP_TEXT`, `RARE_EGG_ROLL`, `SET_KANTO_OWNED`, `START_WILD_BATTLE`,
`FILL_PC`, `SET_FLAG`, `SPECIES_ON_MAP`). Cada cenário numa sessão própria da ROM de teste, a
partir do `captura.sav` (`--only <nome>`):

- `relogio` (`full_clock.py`): `relogio/anda` (1500 quadros = 10 minutos), `relogio/salva` (dia 3
  18:30 sobrevive a salvar, reset e CONTINUAR), `relogio/save_antigo` (relógio 0 = 08:00),
  `relogio/menu` (hora e período no menu Start, tela `relogio_menu`), `relogio/aviso` (aviso da
  noite com o jogador livre, tela `relogio_aviso_noite`), `relogio/aviso_no_menu`,
  `relogio/save_cancelado` (a janela da hora não vaza), `relogio/sem_aviso_ao_entrar`; e o tom de
  cor: `tom/hook` (os 1440 minutos iguais ao espelho Python), `tom/periodos` (Rota 1 às 06, 12, 18
  e 22 h = cor do ROM × tom, telas `tom_*`), `tom/interior` (sem tom), `tom/sem_acumular` (menu,
  casa e batalha não aplicam o tom duas vezes) e `tom/transicao` (a cor muda em degraus de 16:00
  até o entardecer).
- `clima` (`full_weather.py`): o clima de um mapa externo com header NONE/SUNNY/SUNNY_CLOUDS sai
  de um sorteio por região, dia do clima e período; o **dia do clima vira às 04:00** e o **dia 0
  é sempre céu limpo**. `clima/hook` (2000 sorteios iguais ao espelho), `clima/neve` (Four Island,
  tela `clima_neve`), `clima/interior`, `clima/troca_de_periodo` (tela `clima_troca_de_periodo`),
  `clima/volta_da_bolsa`, `clima/fixo` (Viridian Forest, Pokémon Tower), `clima/caverna`, e na
  batalha: `clima/batalha_granizo` (neve do mapa → granizo permanente, tela `batalha_granizo`),
  `batalha_areia`, `batalha_chuva` e `batalha_cinzas` (sem clima de batalha).
- `clima_visual` (`full_weather_gfx.py`): cada clima injetado na Rota 1 ao meio-dia por 1500
  quadros: `neve` (flocos caindo), `cinzas` e `areia` (blend e paleta do Emerald), `areia_troca`
  (a neve volta à paleta padrão) e `neblina` (mais fraca fora, original na Pokémon Tower). Telas
  `clima_*` só para registro.
- `encontros` (`full_encounters.py`; tabela em `src/data/wild_encounters_time.json`):
  `encontros/hook` (35 mapas × 3 períodos × 12 slots), `encontros/entardecer` (tarde ou noite meio
  a meio, ±4σ), `encontros/rota1_noite` (selvagem de verdade na grama às 22:00 e às 07:00),
  `encontros/sem_tabela` (Rota 12 segue o FRLG) e `encontros/area_pokedex`.
- `dex_nacional` (`full_national_dex.py`): a flag continua desligada, a Pokédex abre na lista
  nacional (tela `pokedex_nacional`), o resumo do Larvitar mostra 246 e o porteiro da Liga segue no
  lugar.
- `pos_liga` (`full_post_league.py`): a cena do Prof. Carvalho depois da Liga (60 capturados de
  Kanto + One Island) dá um Ovo raro (Larvitar, Bagon ou Beldum: na equipe, senão no PC, senão o
  Oak guarda e entrega depois), ₽45.000 e o objetivo do Amuleto Brilhante, e liga a Dex Nacional;
  `pos_liga/sorteio` (3000 sorteios, ±4σ) e `pos_liga/sem_60`. Telas `pos_liga_ovo`,
  `pos_liga_dinheiro` e `pos_liga_objetivo`.
- `evo_dia_noite` (`full_day_night_evo.py`): Eevee com amizade 220 + Rare Candy vira Espeon de
  manhã/tarde e Umbreon de noite e no entardecer; amizade baixa não evolui; Feebas segurando a
  Escama Prisma vira Milotic; a Escama Prisma a ₽7000 na loja de Four Island, antes dos 8 itens do
  breeding.
- `resumo_amizade` (`full_summary_friendship.py`): a 6ª linha da página EVOLUTION ("<corações>
  n/255 <frase>", " (220+)" a partir de 220) para 0..255 e na página de verdade (tela
  `resumo_amizade_eevee`).

Os testes estáticos ficam em `test/tests/test_dia_noite.py` (relógio, hora no menu, tom, clima,
granizo), `test_clima_visual.py`, `test_encontros_estatico.py`, `test_dex_nacional_estatico.py`,
`test_pos_liga_estatico.py`, `test_evolucoes_estatico.py` e `test_resumo_evolucao.py` (Espeon,
Umbreon, Milotic e a linha de amizade) e `test_glifos.py` (ã õ Ã Õ nas fontes).

### `make test-approve`

Promove as telas de uma execução a **screenshots de referência**:

```bash
make test-approve                          # a execução mais recente em test/out/
make test-approve DIR=test/out/20261017-030544   # uma execução específica (também vale roms/ultima-falha)
```

Copia `telas/*.png` dos pontos-chave para `test/referencias/<INICIAL>/<ponto>.png` (o inicial vem
do `meta.json` da execução). Pontos: `nome`, `inicial`, `batalha_rival`, `captura`,
`save_continue` (modo rápido) e `bolsa`, `resumo`, `pokedex`, `opcoes`, `cartao`, `pc`, `loja`,
`mapa` (tour do modo completo) e, do Hack 7, `relogio_menu`, `relogio_aviso_noite`,
`pokedex_nacional`, `pos_liga_ovo`, `pos_liga_dinheiro` e `pos_liga_objetivo` (mudam com o inicial
ou com a execução: NPC andando no Centro Pokémon, contagem da Pokédex, Poké Balls na mesa do Oak;
`refs.STARTER_DEPENDENT_POINTS`). Cada inicial tem o seu conjunto: para aprovar os três, rode a
esteira uma vez com cada um (`--starter`). As telas da cena de evolução (`evo_*_antes`,
`evo_*_depois`, do cenário `evolucoes`) e das páginas novas do resumo (`resumo_evo_*`, `resumo_pag_*`, do
`resumo_evolucao`; `resumo_ivs_*`, do `resumo_ivs`), da loja de Four Island (`loja_four_island*`,
do `ovo`) e do Hack 7 (`resumo_amizade_eevee`) não dependem do inicial e vão para
`test/referencias/COMUM/`, que vale para os três.

"Mais recente" é a pasta `test/out/<data-hora>` modificada por último, de qualquer comando;
confira o `DIR` quando tiver rodado outras coisas. O comando **não confere se a execução
passou**: quem decide se a tela está certa é você.

Diferença de tela **nunca reprova** a ROM: vira *aviso* no relatório, com três imagens (a atual,
a referência e o diff com os pixels diferentes em vermelho). Sem referência também é só aviso.
Telas com dados que mudam de execução para execução (dinheiro, HP, tempo de jogo, vistos na
Pokédex) podem continuar avisando mesmo depois de aprovadas.

**Revisar e commitar:** `test/referencias/` **está no Git**. Depois de aprovar, o
`git status`/`git diff --stat test/referencias` mostra quais PNG mudaram ou chegaram; abra as
imagens (`test/referencias/<INICIAL>/*.png` e `COMUM/*.png`, no Explorer) e, se estiverem
certas, commite-as:

```powershell
git add test/referencias
git commit -m "test(esteira): referências de tela"
```

### `make test-watch`

Assiste ao roteiro rápido (abertura, Rota 1, captura) numa **janela do Windows (WSLg)**, em
tempo real e com som. Fora da esteira: save temporário, não versiona, não escreve em `roms/` e
não gasta o rodízio (usa o inicial da vez só para ler).

```bash
make test-watch                                  # do começo, inicial da vez
make test-watch STARTER=SQUIRTLE                 # inicial à escolha
make test-watch FROM=rival                       # começa na Rota 1
make test-watch FROM=encomenda STARTER=SQUIRTLE  # começa na captura
```

- `FROM=` (`rival` ou `encomenda`) carrega o savestate mais recente que um `make test-quick`
  deixou em `test/out/*/estados/` **posterior ao último build da ROM** (e do inicial pedido).
  Sem um, o comando avisa para rodar `make test-quick` antes (exit 2) ou para assistir sem `FROM=`.
- Para encerrar: **feche a janela** ou aperte **Esc**; ou **Ctrl-C** no terminal. Terminar sem
  falha apaga o save temporário; com falha, as evidências ficam numa pasta temporária informada
  na saída.
- Precisa do WSLg (Windows 11) e da `libsdl2-dev` (veja Requisitos). Sem janela disponível o
  comando diz para rodar `wsl --update` e `wsl --shutdown` no PowerShell e abrir o WSL de novo.

**Cenário do modo completo numa janela** (`CENARIO=`: `evolucoes`, `resumo_evolucao`,
`resumo_ivs`, `ovo`, `relogio`, `encontros`, `dex_nacional`, `pos_liga`, `evo_dia_noite`,
`resumo_amizade` ou `clima`; o `clima_visual` não, ele injeta o clima direto na memória):

```bash
make test-watch CENARIO=evolucoes                    # Hack 3: as evoluções, em tempo real
make test-watch CENARIO=evolucoes STARTER=SQUIRTLE   # usa o save de uma execução com esse inicial
make test-watch CENARIO=resumo_evolucao              # Hack 4: a página EVOLUTION do resumo
make test-watch CENARIO=resumo_ivs                   # Hack 5: a página IVs/EVs de 5 Pokémon
make test-watch CENARIO=ovo                          # Hack 6: o ovo entregue e chocando (~1,5 min)
make test-watch CENARIO=relogio                      # Hack 7: relógio, hora no menu, aviso e tom de cor
make test-watch CENARIO=clima                        # Hack 7: clima por região/período e granizo na batalha
make test-watch CENARIO=encontros                    # Hack 7: selvagens da Rota 1 de noite e de manhã
make test-watch CENARIO=dex_nacional                 # Hack 7: Pokédex Nacional desde o início
make test-watch CENARIO=pos_liga                     # Hack 7: cena pós-Liga do Oak (Ovo raro, ₽45.000)
make test-watch CENARIO=evo_dia_noite                # Hack 7: Espeon/Umbreon por horário e Milotic
make test-watch CENARIO=resumo_amizade               # Hack 7: corações de amizade no resumo
```

- Recompila antes a **ROM de teste** (`make firered_switch TESTBUILD=1`, como o `test-full`) e
  roda o cenário nela, na janela, com o mesmo roteiro do modo completo (inclusive as
  conferências: no fim aparece o resumo de ok/falhas). No `resumo_evolucao`, a janela fica
  parada ~2,5 s em cada página EVOLUTION (e no resumo de escolher golpe) para dar tempo de ler;
  antes, uns 7 s no campo enquanto confere o texto das 386 espécies. No `resumo_ivs`, o mesmo
  em cada página IVs/EVs, depois de ~4 s conferindo as combinações de IVs/EVs.
- Parte de uma **cópia** do save do jogo (`captura.sav`) mais recente em `test/out/*/` — todo
  `make firered_switch` e `make test-quick` deixa um; o inicial é o desse save. Sem nenhum, o
  comando pede para rodar `make test-quick` antes (exit 2). Não grava em `roms/` e não mexe no
  rodízio.
- `CENARIO=` e `FROM=` não combinam. O `shiny` e o `creche` não estão disponíveis aqui: 400 000 Pokémon em
  tempo real levariam horas.

## Usando a esteira direto (`python3 -m esteira`)

Os `make test-*` são atalhos para isto. Dentro do WSL, a partir de `test/`:

```bash
cd test
python3 -m esteira rapido --rom ../pokefirered_switch.gba --elf ../pokefirered_switch.elf \
    --log ../build/firered_switch.log --out out/minha-execucao
```

| Subcomando | Para quê |
|---|---|
| `rapido` | Checagens estáticas + 3 roteiros rápidos |
| `completo` | O rápido + os cenários de `FULL_SCENARIOS` |
| `aprovar DIR` | Promove as telas da execução `DIR` a referência |
| `assistir` | Roteiro rápido (ou, com `--cenario <nome>` de `WATCH_FULL_SCENARIOS`, esse cenário na ROM de teste) numa janela (é o que o `make test-watch` chama) |
| `nao-testada --out DIR` | Só o relatório "NÃO TESTADA" (usado por `SKIP_TESTS=1`) |

Opções de `rapido` e `completo` (`--rom`, `--elf` e `--out` são obrigatórios):

| Opção | Significado |
|---|---|
| `--rom`, `--elf` | ROM jogável e seu ELF (o ELF dá os endereços dos símbolos) |
| `--rom-test`, `--elf-test` | ROM de teste e ELF, só para cenários que usam a build de teste (padrão: `pokefirered_switch_test.*` na raiz) |
| `--log` | Log do build; sem ele só a checagem de texto roda (a do build vira aviso) |
| `--out` | Pasta da execução (relatório, telas, estados, vídeo) |
| `--only NOME` | Só um item: `build`, `texto`, `abertura`, `rota1`, `captura`; no `completo` também `pc`, `telas`, `floresta_brock`, `master`, `shiny`, `evolucoes`, `resumo_evolucao`, `resumo_ivs`, `creche`, `ovo`, `relogio`, `clima_visual`, `encontros`, `dex_nacional`, `pos_liga`, `evo_dia_noite`, `resumo_amizade`, `clima` |
| `--starter X` | Força `BULBASAUR`, `CHARMANDER` ou `SQUIRTLE` (não mexe no rodízio) |
| `--sem-video` | Não grava `video.webp` |

`assistir`: `--starter`, `--from {encomenda,rival}` ou `--cenario {evolucoes,resumo_evolucao,resumo_ivs,ovo,relogio,encontros,dex_nacional,pos_liga,evo_dia_noite,resumo_amizade,clima}` (com `--rom-test`/`--elf-test`, padrão os da raiz), `--rom`, `--elf`. Códigos de saída de
`rapido`/`completo`: 0 sem falha (aviso não reprova), 1 com falha.

Exemplos:

```bash
python3 -m esteira rapido --rom ../pokefirered_switch.gba --elf ../pokefirered_switch.elf --out out/so-texto --only texto
python3 -m esteira rapido --rom ../pokefirered_switch.gba --elf ../pokefirered_switch.elf --out out/a --starter CHARMANDER --sem-video
python3 -m esteira completo --rom ../pokefirered_switch.gba --elf ../pokefirered_switch.elf --out out/a --only shiny --starter CHARMANDER
```

**Cuidado com `--only` num cenário de emulador.** Ele reaproveita os savestates que uma execução
anterior deixou em `<OUT>/estados/` **na mesma pasta `--out`** (por exemplo `--only rota1` parte
de `estados/rival.ss`) e **não confere que vieram do mesmo build**. Se você recompilou a ROM
desde então, o estado é de outro código e o teste pode falhar de jeitos estranhos ou, pior,
passar sem valer. Regras práticas:

- só reuse a pasta `--out` se a ROM não mudou desde aquela execução;
- passe o mesmo `--starter` da execução original (está no `meta.json`): sem ele a esteira usa o
  inicial da vez no rodízio e, se não for o do checkpoint, descarta o checkpoint e roda a
  cadeia toda;
- `--only` de qualquer cenário da ROM de teste (`shiny`, `evolucoes`, `resumo_evolucao`,
  `resumo_ivs`, `creche`, `ovo` e os do Hack 7) precisa do `<OUT>/captura.sav` que o
  `rapido`/`completo` anterior (mesma pasta) deixou; sem ele o resultado é uma falha dizendo o que rodar antes;
- `--only build` e `--only texto` não usam emulador e não têm esse problema.

O vídeo (`video.webp`) grava a execução inteira acelerada, tipicamente 4x (um quadro a cada 8
emulados, 30 fps; execuções longas descartam quadros para caber no teto de 25 MB), e é embutido
no relatório. Problema para gravar é só aviso. Com
`--only` de item sem emulador não há vídeo.

## Testes unitários da esteira

```bash
python3 -m pytest test -q                       # tudo: ~40 s (10 processos; veja Paralelismo)
ESTEIRA_SKIP_SLOW=1 python3 -m pytest test -q   # sem os lentos: ~30 s
```

Na raiz do repo, dentro do WSL. Os testes marcados `slow` compilam de verdade (um deles quebra um
`.c` numa cópia do repo e confere que o `make firered_switch` falha; não toca em `roms/`);
`ESTEIRA_SKIP_SLOW=1` pula os lentos. Os testes que precisam do emulador usam a
`pokefirered_switch.gba` da raiz e são pulados se ela não existir. Rode isto depois de mexer em
qualquer arquivo de `test/esteira/`.

Rodam em paralelo com o `pytest-xdist` (`test/pytest.ini`: `-n auto --dist loadfile`, e o
`-n auto` vira `ESTEIRA_JOBS` workers, padrão 10). Cada arquivo de teste fica num worker só, e
cada teste usa a sua pasta temporária, o seu emulador e o seu save. Para rodar num processo só:
`python3 -m pytest test -q -n 0`; com menos processos: `ESTEIRA_JOBS=4 python3 -m pytest test -q`.

A cópia do repo do teste lento é um **espelho fixo em `/tmp/esteira-espelho-repo-<uid>/`** (ext4
do WSL), atualizado com `rsync` a cada execução: ~20 s, ou ~75 s na primeira vez depois de ligar
o WSL (o `/tmp` começa vazio). No `/mnt/c` a cópia levava ~4,5 min. São ~250 MB; pode apagar a
pasta quando quiser (o teste a refaz).

## Paralelismo (`ESTEIRA_JOBS`)

A máquina tem 16 threads; a esteira usa **no máximo 10 processos de trabalho ao mesmo tempo**
(sobram 6 para usar o PC). O teto vale para tudo o que roda junto: cada sessão de emulador (o
Python que a dirige e o runner do mGBA se revezam: conta 1), a checagem de textos, os workers do
pytest e os `make -jN` (contam N). Para mudar:

```bash
ESTEIRA_JOBS=4 make test-full              # mais leve (mais lento)
make firered_switch ESTEIRA_JOBS=6         # também vale como variável do make
ESTEIRA_JOBS=1 make test-full              # o modo sequencial de antes (~16 min)
```

- **Compilação**: `make firered_switch` (e o `make firered_switch TESTBUILD=1` do `test-full` e do
  `test-watch`) usa `-j$ESTEIRA_JOBS` (10) quando a linha de comando não tem `-j`. Um `-jN`
  explícito continua valendo. Não use mais `-j$(nproc)` (16).
- **Esteira rápida** (`make firered_switch`, `make test-quick`): o roteiro jogado é uma corrente
  (abertura → Rota 1 → captura) e não se divide; a checagem de textos roda num processo ao lado
  do emulador (~2 s a menos). Resultado e versionamento iguais.
- **Modo completo** (`make test-full`): cada sessão roda num processo próprio, com o seu emulador
  e a sua pasta (`<OUT>/sessoes/<cenário>/`, apagada no fim; telas e estados voltam para
  `<OUT>/telas` e `<OUT>/estados`). Saem logo de cara a checagem de textos, o grupo jogável
  (rápido → `pc` → `telas` → `floresta_brock`, que é uma corrente: cada um parte do checkpoint do
  anterior) e o `master` (com as vagas que sobram no `make -j`). As sessões da ROM de teste
  esperam a ponte `captura.sav`, que o grupo jogável grava logo depois do `captura`, e então
  rodam todas juntas. Relatório, vídeo, tempos e resumo do terminal são juntados **na ordem do
  modo sequencial** (mesmos cenários, mesmos nomes, mesmas asserções); o tempo de um cenário é
  o da sessão dele (do pedaço mais longo, nos divididos).
- **`shiny` e `creche` divididos em partes**: o `shiny` roda em 6 sessões e a `creche` em 3. Cada
  parte conta a sua fatia do N (200 000 Pokémon por taxa; os ovos de cada par de pais; 400 000
  ovos por taxa) e o processo principal soma as fatias e aplica **as mesmas faixas** (±3σ, ±4σ,
  qui-quadrado) ao total. A parte 1 faz o roteiro inteiro (Dex completa, PC, Oak, charm,
  personalidade, EVs, Velocidade); as outras só CONTINUAR e as contagens. Para as fatias não
  repetirem a mesma sequência, cada parte grava no `gRngValue` do jogo uma semente
  (`esteira/paralelo.py`, `part_seed`) separada das outras por 2^27 passos do gerador, então as
  sequências nunca se cruzam. As sementes partem de um **sal sorteado a cada execução**: cada
  `make test-full` usa outras sequências (um falso vermelho estatístico não se repete). O sal
  aparece no detalhe de cada resultado juntado (`ESTEIRA_SEED=0x...`), no fim do resumo do
  terminal e no `meta.json` (`"semente"`). Os números diferem dos do modo sequencial, não as
  faixas nem os nomes; o detalhe diz "em 6 processos".
- **Reproduzir um vermelho do shiny/creche**: rode de novo com o sal daquela execução, com a
  mesma ROM; as contagens saem iguais (o número de partes não depende do teto, então vale com
  qualquer `ESTEIRA_JOBS` > 1):

  ```bash
  ESTEIRA_SEED=0x1234abcd make test-full
  ```
- `--only` e `ESTEIRA_JOBS=1` rodam como antes, tudo num processo só, sem dividir nada.
- `ESTEIRA_JOBS` que não seja inteiro positivo vale 10, e o teto máximo é 64 (no Makefile e na
  esteira). Um `-jN` explícito na linha do make vale como está (não é cortado pelo teto).
- Ctrl-C ou erro de infraestrutura no meio: cada sessão roda num grupo de processos próprio e é
  encerrada com SIGTERM (os `finally` rodam: o `master` apaga a worktree em `/tmp` e o `make`
  dele morre junto); só se não sair em 30 s leva SIGKILL.

**Pular o desenho dos quadros (medido, não adotado):** o runner pode deixar de desenhar os quadros
que não viram tela nem vídeo (o `frameskip` do mGBA; a emulação não muda: memória, quadro e tela
final idênticos). O ganho medido foi de ~3% (20 000 quadros em pedidos de 2: 12,9 s → 12,6 s;
60 000 em pedidos de 60: 32,7 s → 31,6 s), abaixo dos 15% que justificariam mais uma chave; o
desenho do mGBA é barato perto da emulação. Fica como está.

## Requisitos (uma vez só)

No Ubuntu do WSL, como root:

```bash
sudo apt install libmgba-dev mgba-sdl libpng-dev python3-pytest python3-pytest-xdist python3-pil rsync
sudo apt install libsdl2-dev     # OPCIONAL: só para o make test-watch (janela)
```

- O runner do emulador (`test/harness/mgba_runner`, em C) é compilado sozinho pelos comandos que
  precisam dele (`make -C test/harness`). Sem `libsdl2-dev` ele compila sem janela e o
  `test-watch` não funciona; o resto sim. **Se instalar a libsdl2-dev depois**, recompile o runner:
  `make -C test/harness clean && make -C test/harness`.
- O compilador `agbcc` precisa estar em `tools/agbcc` (fora do Git). O cenário `master` também o
  copia para a worktree temporária.
- O Windows 11 com WSLg (padrão) é necessário só para o `test-watch`.

## Como adicionar um teste novo

**Regras**

- **Modo rápido** (roda a cada `make firered_switch`): só **aperta botões e lê memória**. Nunca
  escreve na RAM do jogo. Precisa ser rápido (hoje ~35 s no total): não pendure nada pesado nele.
- **Modo completo**: também só aperta botões e lê memória na ROM jogável. Quando precisar de
  atalho (dar item, marcar a Dex completa...), use a **build de teste**
  (`make firered_switch TESTBUILD=1`), que tem a caixa de comandos `gTestMailbox` (C em
  `src/test_hooks.c` e `include/test_hooks.h`, lado Python em `test/esteira/hooks.py`). A ROM
  jogável não tem nada disso.
- Escrita na RAM do emulador só vale em teste unitário do pytest ou na ROM de teste.

**Passo a passo (cenário novo no modo completo)**

1. Crie `test/esteira/scenarios/full_<nome>.py` com uma função `run_full_<nome>(ctx)`. O `ctx`
   (`ScenarioContext`) traz `emu`, `game` (estado lido da memória), `controller`, `nav`, `suite`,
   `consts` e `starter`. Cada checagem vira um resultado com `ctx.suite.run("nome", funcao)`
   (`AssertionError` e tempo esgotado viram *falha* com evidência) ou
   `ctx.suite.add(Result(nome, "ok"|"aviso"|"falha", detalhe))`. Use como modelo:
   `full_pc.py` (ROM jogável, continua a sessão), `full_shiny.py` (ROM de teste),
   `full_master.py` (sem emulador). Utilidades comuns em `scenarios/base.py`
   (`Scenario`, `_press`, `_finish_script`, `_shot`).
2. Para guardar um ponto de retomada, chame `ctx.controller.checkpoint("nome")` no fim (grava
   `estados/nome.ss`).
3. Registre em `test/esteira/__main__.py`: o `import` e **uma linha** na lista `FULL_SCENARIOS`:

   ```python
   ScenarioSpec("meu_cenario", run_full_meu, needs="telas"),   # ROM jogável, recomeça do checkpoint `telas`
   ScenarioSpec("outro", run_full_outro, rom=TEST),            # ROM de teste, parte do boot
   ScenarioSpec("host", run_full_host, rom=HOST),              # sem emulador
   ```

   `needs` é o checkpoint de onde o cenário pode recomeçar com `--only`. Cenários da mesma ROM
   rodam em sequência numa sessão só, **na ordem da lista**, cada um continuando do estado que o
   anterior deixou. Se o cenário usa o `.sav` do jogo, veja `save_from` na docstring de
   `ScenarioSpec` (um cenário com `save_from` abre uma sessão nova da ROM de teste, como o
   `shiny` e o `evolucoes`; para assistir numa janela, acrescente-o em `WATCH_FULL_SCENARIOS`).
4. Atualize o teste `test_registro_dos_cenarios_completos` em `test/tests/test_cli.py` (ele
   confere a ordem e as dependências) e escreva um teste em `test/tests/test_<nome>.py`.
5. Se o cenário tira screenshots que devem ser comparados, grave em `<OUT>/telas/<ponto>.png` e
   acrescente o ponto em `TOUR_POINTS`/`KEY_POINTS` de `test/esteira/refs.py`; depois rode
   `make test-approve`.
6. Cenário no **modo rápido** é `QUICK_SCENARIOS` no mesmo arquivo. Mexa nele com cuidado: a
   esteira rápida é o portão de toda ROM versionada.

## `test/excecoes.json`

Lista de achados **antigos** que a esteira deve ignorar para não reprovar por problema que já
existia. Tem duas listas:

- `build_warnings`: pedaços de texto; um aviso do compilador que contém algum deles é aceito.
- `text`: achados de texto congelados. Cada item tem `file` (arquivo), `label` (rótulo do texto),
  `rule` (`charmap`, `terminador`, `largura`, `linhas`, `letras`, `controle`, `glossario`,
  `ingles`), `fingerprint` (sha1 abreviado do texto cru do rótulo) e, nas regras que medem
  (`largura`, `linhas`, `letras`), `valor` (a medida: px da linha mais larga, linhas ou letras).

Hoje as duas listas estão **vazias**: não há problema conhecido, e qualquer achado novo reprova.

Como funciona:

- A exceção só vale **enquanto o texto for o mesmo** (o fingerprint bate). Mudou o texto, ele volta
  a ser checado normalmente: não dá para "esconder" um texto editando-o.
- Exceção cujo rótulo sumiu, cujo texto mudou ou cujo problema desapareceu vira o aviso
  **"exceção obsoleta"** no relatório. Apague essa entrada do JSON. **A lista só deve encolher**:
  exceção nova não se escreve à mão; o certo é corrigir o texto.
- Se mesmo assim precisar congelar o estado atual (por exemplo, ao adotar uma regra nova), a lista
  se gera pelo código; em `test/`, dentro do WSL:

  ```bash
  python3 -c "import json; from esteira.check_text import compute_baseline; print(json.dumps(compute_baseline('..'), ensure_ascii=False, indent=1))"
  ```

  e cole o resultado em `"text"`.

**Fontes de texto**: `.string`/`.braille` de `data/text/*.inc`, `data/maps/*/text.inc`,
`data/scripts/*.inc`, `data/event_scripts.s` e `data/mystery_event_msg.s`; todo `_("...")` de
`src/**/*.c|h` (menos o `pokedex_text_lg.h`, que a build FireRed não compila); `english` (rótulo
`ITEM_X.name`) e `description_english` (rótulo `ITEM_X`) do `items.json`; `name` do
`region_map_sections.json` (rótulo `MAPSEC_X`). Em C o rótulo é o índice (`MOVE_X`), o campo com
o dono (`TRAINER_X.trainerName`, `NATIONAL_DEX_X.categoryName`) ou a variável (`gText_X`; item
posicional repetido vira `gDecorations#2`).

**Janela de cada texto** (regras `largura`, `linhas`, `letras`): cada fonte de texto tem a sua
janela, tirada dos templates do código, com arquivo:linha de cada uma em `WIDTH_RULES`
(`test/esteira/check_text.py`): largura útil em px, fonte (normal ou small), largura do espaço
(a ajuda usa 4 px), máximo de linhas e, nos campos de nome, máximo de bytes do buffer. As
principais: diálogo 208 px (mapas, scripts, quase todo `data/text`, Union Room, TV Educativa,
Pokédude, fala do Carvalho); mensagem de batalha 222 px (28 tiles, x = 2); tutorial do
Carvalho na batalha 208; ajuda 208 px com espaço de 4 px e 7 linhas, e os itens das listas da
ajuda (tópicos, perguntas, "Usando...", termos, assuntos, tipos e "Cancelar", lidos das tabelas
`sHelpSystem*Ptrs` de `src/help_system.c`) **1 linha de 200 px**: saem em x = 8 na lista e viram o
título da resposta, que começa 24 px abaixo; Fame Checker 208 (caixa),
56 (nomes) e 84 em FONT_SMALL (quadro do ícone); descrição de golpe 113 px e 4 linhas; entrada da
Pokédex 240 px e 3 linhas; descrição de item 198 px e 3 linhas (a mochila tem 200, mas o item no PC
de Pokémon sai em x = 2), de fruta 198 px e **2** linhas (bolsa de frutas), e a de MT/MO no
`items.json` sem medida (o jogo mostra a descrição do golpe, `src/data/items.json.txt:17-18`); nome de item 13 letras e 101 px;
golpe 12 letras e 64 px em FONT_SMALL; habilidade 12; tipo 6; fruta 6; classe 12; espécie 10;
categoria da Pokédex 11; nome de lugar 108 px e 18 letras (`mapName[19]` do mapa da região);
nome sugerido 7.

**Janela pelo uso** (`test/esteira/janelas_uso.py`): os textos do `src/strings.c`, as palavras do
Easy Chat e os textos soltos de outros `.c` não têm janela fixa: a checagem indexa onde cada
rótulo é usado em `src/**` (a função que o recebe, `call:DisplayPartyMenuMessage`; a tabela que o
contém, `table:sCursorOptions`; outro código, `code`) e mede contra a janela de cada uso
(`USAGE_RULES`, com arquivo:linha). O texto tem de caber em todas; o achado diz qual janela
estourou. Texto sem uso nenhum é "texto morto" e fica sem medida. Fonte sem janela determinável
tem regra explícita com o motivo (braille, naturezas, descrições de enfeite, teclados); um teste
garante que nenhum texto cai fora das regras. Texto de tabela, de chamada de menu/lista
(`MENU_CALL`) ou de menu montado à mão (`AddTextPrinterParameterized*` numa função que abre cursor
de menu, como o menu do PC e o do Seagallop) não pode cair na regra-pega-tudo do arquivo (contexto
e rótulo `"*"`): tem regra própria, ou a regra é marcada `unica=True` (tela de janela única:
créditos, cursor da lista). Nas telas revistas (Pokédex, Union Room, Fame Checker, Easy Chat,
multiescolha) um teste confere que a janela citada tem a largura dita e que o trecho citado mostra
o texto indo para ela. Modelos do Easy Chat que o FRLG não abre (batalha, bardo, entrevista, frase
da moda) são texto morto; a palavra do Easy Chat mede no máximo 79 px (duas por linha, com
`{CLEAR 17}`, na moldura de 24 tiles). Textos que dividem a mesma linha (`SHARED_ROWS`: "Grito" e
os controles da Pokédex, categoria e "PÁG. xx/xx") são medidos juntos: o da esquerda não pode
encostar no que vem alinhado à direita.
Cobertura: `python3 -m esteira.check_text --regras`.
Os caracteres
({PLAYER}/{RIVAL} medem 7 letras; nomes de batalha `{B_*}` o maior nome do campo, e os
`_WITH_PREFIX` somam o prefixo mais largo; `{STR_VAR_n}`, `{B_BUFF*}`, `{B_COPY_VAR_n}` e os outros
placeholders de conteúdo variável medem 0 no texto igual à base e o pior caso no texto traduzido,
veja "Tradução") e o espaçamento entre letras seguem o jogo;
`{CLEAR_TO n}`/`{SKIP n}` levam a caneta a n px e `{CLEAR n}` avança n.

**Tradução** (`TRANSLATION_BASE` em `check_text.py`: o SHA completo de `3a8d861f5`, o commit da
`hack-switch` antes dela). `controle` e `glossario` comparam com **esta** base: uma mudança em
inglês que entrar depois na `hack-switch` e for trazida para a tradução aparece como texto
"mudado" (falso positivo) até a base ser atualizada.
- `controle`: todo texto mudado tem os mesmos códigos de controle e placeholders (`{PLAYER}`,
  `{STR_VAR_n}`, `{B_*}`, `{COLOR ...}`, `$`...) da versão inglesa (`git cat-file` da base),
  em qualquer ordem; só `\n`, `\l` e `\p` podem mudar, e macros que só imprimem glifo
  (`{LV_2}`, `{PKMN}`, `{ID}`, `{NO}`) podem virar texto ("Nv."). Pasta sem `.git` (fixtures,
  espelho do teste lento): as regras não rodam; com `.git` mas git falhando ou sem o commit base:
  aviso `texto/controle`, `texto/glossario` e `texto/largura` (pior caso) com o motivo. Objeto ausente da base: os rótulos do
  arquivo contam como novos.
- `glossario`: texto mudado (ou novo) com variante proibida ("Pokébola", "Professor Oak", "HP",
  "Team Rocket"...) ou termo inglês do glossário que sobrou ("POKé BALL", "PALLET TOWN" ou
  "Pallet Town"). O glossário de máquina é `test/esteira/glossario.json`, gerado do glossário
  aprovado (`python3 -m esteira.glossario gerar <md>`); termo novo de uma frente entra lá com
  fonte "criado". `python3 -m esteira.glossario checar "texto"` mostra os achados de um texto.
- `ingles`: **bloqueante** (`ENGLISH_MODE`, desde a Task 11 da tradução): cada texto com
  palavra inglesa reprova, com as palavras achadas. Texto que fica em inglês de propósito
  (as mensagens de depuração `sDmaOverErrorMsg` e `sText_TaskOver`) é exceção congelada em
  `excecoes.json` (regra `ingles`, com fingerprint e `obs`); se o texto mudar, volta a
  reprovar e a exceção vira "obsoleta". O modo `progresso` (um aviso só, com o total; usado
  pelas frentes da tradução) continua disponível em `check_text(..., english=...)`. Lista de permissões: nomes de espécie e de Treinador, créditos (`gCreditsString_*`),
  japonês (`gJPText_*`), teclados (`src/keyboard_text.c`). Por arquivo:
  `python3 -m esteira.check_text --ingles [arquivo...]` (em `test/`).
- `largura` no **pior caso** dos placeholders de conteúdo variável (`VAR_SIZES` em
  `check_text.py`): no texto mudado (ou novo), `{STR_VAR_n}`, `{B_BUFF1..3}`, `{B_COPY_VAR_n}`,
  `{B_26}`, `{UNKNOWN_STR}`, `{DYNAMIC n}` (Quest Log, Union Room, minijogos) medem **10 letras** na letra mais larga da fonte (o tamanho de um nome
  de Pokémon, que cobre nome de jogador/rival e "LT. SURGE"); `{KUN}` (vazio no FRLG) e as falas
  `{B_TRAINER*_LOSE/WIN_TEXT}` medem 0. O inglês confia em nomes curtos e muitas vezes estoura
  nessa medida, por isso o critério é **"sem piorar a base"**: o texto traduzido reprova se a
  linha mais larga dele, no pior caso, passa da janela **e** passa da mesma medida do rótulo na
  base inglesa (rótulo novo, sem inglês: não pode passar da janela). Texto igual à base não é
  medido assim. O achado diz o pior caso usado ("{STR_VAR_1} = 10 letras") e quanto a base ia.
  Sem base (fixtures, espelho): não roda; base indisponível: aviso `texto/largura`.
  **Exceção por contexto** (`VAR_CONTENTS` em `test/esteira/janelas_uso.py`): quando o código que
  enche o buffer prova o conteúdo, declare `VarContent(arquivo, rótulo, "STR_VAR_1", N,
  "fonte arquivo:linha", digits=True)` (número de até N algarismos) ou com `digits=False` (N
  letras, ex.: nome de item = 13). Arquivo e rótulo aceitam fnmatch; o placeholder é o nome
  **literal** de `VAR_SIZES` (`"STR_VAR_1"`, `"DYNAMIC"` cobre todo `{DYNAMIC n}`); a citação
  arquivo:linha é obrigatória (teste) e a entrada tem de casar com um texto real que tenha o
  placeholder. Duas entradas para o mesmo texto e placeholder são erro, então a ordem não decide
  nada; mantenha a lista em ordem alfabética de arquivo e rótulo (só para o merge das frentes).
- Quebra de linha: `python3 -m esteira.reflow` refaz `\n`/`\l` medindo como a checagem
  (`--texto "..." --largura 208`, ou um `.inc` com `--rotulo X --escrever`; sem `--largura` usa a
  janela da regra do arquivo). Só mexe na caixa que tem linha estourada, e nela só na linha que
  estoura (o excesso desce para a seguinte): placas, listas (`{CIRCLE_n}`, `{CIRCLE_DOT}`,
  `{TRIANGLE}`, `{BIG_MULT_X}`) e recuos ficam; item que termina em ":" abre sublista, e as
  linhas recuadas dele ficam uma por linha; `--forcar` refaz tudo do zero. Os placeholders
  variáveis medem o pior caso (10 letras, ou o `VAR_CONTENTS` do rótulo no modo `.inc`), então a
  quebra deixa espaço para o nome; `--var STR_VAR_1=5d` (5 algarismos) ou `--var STR_VAR_1=13`
  (13 letras) muda um deles (pode repetir). O `--var` é só **prévia**: a checagem não o vê e
  usa só o `VAR_CONTENTS`; quebrou contando com um número, declare o contexto, ou o check
  reprova. Num `.inc` sem `--rotulo`, o `--var` vale para todos os rótulos do arquivo, e rótulo
  ainda em inglês que estoure no pior caso também é refeito.

Página EVOLUTION do resumo (Hack 4): os textos `gText_PokeSum_Evo*` de `src/strings.c` têm o
limite da janela da página, 222 px (28 tiles com o texto em x = 2, `sWindowTemplates_Evolution`
e `EVOLUTION_PAGE_TEXT_X` em `src/pokemon_summary_screen.c`). Como eles têm `{STR_VAR_*}` (nível,
item, espécie), que no rótulo sozinho medem 0 (ou o pior caso genérico, no texto traduzido), a checagem também monta a página de **toda** espécie com os
nomes de verdade e mede cada linha (`test/esteira/evolution_page.py`): um item ou espécie
renomeado que estoure a janela reprova como `texto/largura`. Hoje a linha mais larga é a do
Umbreon, 220 px.

Página IVs/EVs (Hack 5): mesma janela (222 px, `sWindowTemplates_Ivs`, texto em x = 2) para os
`gText_PokeSum_Iv*`, `Stat*`, `Ev` e `HiddenPower`; as linhas inteiras, com as colunas
`{SKIP x}`, são montadas para os textos e números mais largos (todos os níveis, avaliações e
tipos de Hidden Power) e medidas, e uma coluna que encavale na anterior também reprova
(`check_page_widths` em `test/esteira/ivev_page.py`).

### Linhas por caixa no diálogo padrão (regra `linhas`)

A caixa de mensagem padrão tem 4 tiles de altura = **2 linhas** (`sStandardTextBox_WindowTemplates`,
`src/new_menu_helpers.c:36-44`): `\n` desce uma linha, `\l` rola a caixa e o texto seguinte fica na
mesma linha (a de cima sobe; `src/text.c:872-879`), `\p` limpa. Uma 3ª linha numa caixa (dois `\n`
antes do próximo `\p`, ou `\n` depois de `\l` já na 2ª linha) sai da janela e é cortada **sem aviso**. As regras do diálogo (`data/maps/*/text.inc`, `data/scripts/*.inc`,
`data/event_scripts.s`, os `data/text/*.inc` de msgbox, a fala do Carvalho e os textos de `.c` cuja
janela de uso é o diálogo padrão) têm `box_lines=2`: no texto mudado em relação à base, uma caixa com
mais de 2 linhas reprova (`texto/linhas`), a menos que o mesmo rótulo em inglês já tivesse tantas
quanto (rótulo novo: estrito). `box_lines()` em `check_text.py` mede um texto.

**Achados conhecidos** (`KNOWN_FINDINGS` em `check_text.py`): achado de regra nova que já estava
na `hack-switch` e tem frente dona vira `aviso` "(conhecido: ...)" enquanto o texto (fingerprint) e a
medida forem os mesmos; corrigido, vira aviso "não ocorre mais" (tire a entrada); mudado e ainda
errado, volta a reprovar.

### Buffers de string (regra `buffer`, `test/esteira/buffers.py`)

Texto copiado em tempo de execução para um array de tamanho fixo **trava o jogo** se passar do
tamanho: `StringCopy` copia até o EOS, sem conferir nada. Casos da rodada 1: "Bolso de itens-chave"
(20 letras + EOS) no `gStringVar3[20]` pelo `bufferstdstring` da mensagem de item obtido (travava a
encomenda do Viridian Mart) e "Loja de Celadon Cobertura" (25 + EOS) no `mapName[25]` do aviso de
mapa. A regra mede **bytes + EOS** (letra acentuada = 1 byte; placeholder = os bytes do charmap)
contra o tamanho **lido do C** (`u8 gStringVar3[20]`, `u8 mapName[25]`, `#define` resolvidos), em
cada caminho de cópia, com o arquivo:linha de onde a cópia acontece:

- **scripts**: `bufferstdstring` (a entrada de `gStdStringPtrs`, e a tabela inteira contra o menor
  `gStringVarN`), `bufferstring`/`vbufferstring`, `bufferitemname`, `bufferitemnameplural` (nome +
  o sufixo de plural mais comprido) e `buffermovename`, em `data/maps/*/scripts.inc`,
  `data/scripts/*.inc` e `data/event_scripts.s`; o `STR_VAR_n` dá o buffer (`gStringVar1` 32,
  `gStringVar2`/`3` 20, `src/string_util.c`);
- **C automático**: `StringCopy`/`StringCopyN`/`StringCopyPadded`/`StringExpandPlaceholders`/
  `DynamicPlaceholderTextUtil_ExpandPlaceholders`/`CopyItemName`/`GetMapName*`/`CopyEasyChatWord`
  com destino num array de tamanho conhecido (global, local da função, campo de struct) e origem
  traduzível (rótulo de texto, tabela de textos como `gMoveNames[i]`, nome de item ou de lugar);
- **C declarado** (`DECLARED`): concatenação (texto + texto ou número: nível, HP, ID, "Nº",
  separadores), destino ponteiro (o código prova qual buffer é) e os caminhos isentos, cada um com
  o motivo e arquivo:linha. Um teste reprova cópia de texto traduzível que não esteja nem medida
  nem declarada, e declaração que não case com nenhuma chamada;
- **aviso de mapa**: um caminho por `map.json` com andar: nome do lugar (o especial da Loja de
  Celadon) + " " + andar ("B1F") ou `gText_Rooftop2`, em `mapName[25]`;
- **texto de batalha** em `gDisplayedStringBattle[300]` (`BattleStringExpandPlaceholders*`, com os
  `{B_*}` expandidos: nome de 10 letras, prefixo "Wild "/"Foe " + 10, `{B_BUFF*}` 10): toda mensagem
  de `src/battle_message.c` (`BufferStringBattle`), as falas do Pokédude (`data/text/pokedude.inc`,
  via `GetPokedudeText`) e do tutorial do Carvalho, e as mensagens da cena de evolução. O inglês do
  Pokédude já passa de 300 (`Pokedude_Text_ButterfreeDoubleResistsGrass`, 308): a tradução pode ir
  até o pior caso inglês, não além.

Quando a função expande os placeholders, cada um mede o pior caso da largura: `{PLAYER}`/`{RIVAL}`
7 letras, `{STR_VAR_n}`/`{DYNAMIC n}` 10 (ou o `VAR_CONTENTS` do rótulo). Concatenação soma a
maior alternativa de cada parte. **Critério**: igual ao da largura no pior caso, "sem piorar a
base": a alternativa (um rótulo) reprova se o total passa do buffer **e** da base inglesa: num
caminho de um texto só, o mesmo rótulo em inglês; num caminho composto (texto + texto, 3 palavras
do Easy Chat), o pior caso do caminho em inglês. Rótulo novo não pode passar. Só roda com a base (sem `.git`, não roda;
base indisponível: aviso `texto/buffer`). O inglês que já estoura fica documentado no relatório
da T4 e a tradução pode ir até ele. Estouro já mergeado com dono vai para `KNOWN_OVERFLOWS`
(aviso, não reprova, enquanto o texto do rótulo (fingerprint) e o total forem os mesmos; mudou e
continua estourando, reprova; corrigido, vira aviso de obsoleto).

Limites conhecidos: origem guardada antes numa variável local (`const u8 *t = gText_X;
StringCopy(buf, t)`, ex. `src/party_menu.c:1662`) não é vista pelo guarda do inventário; índice
aninhado (`gStatNamesTable[sStatsToRaise[i]]`) é. Sem `.git` (checkout sem histórico, espelho do teste
lento) a regra não roda, e os testes de buffer da E1 (`test_traducao_e.py`) pulam. O contexto da regra
(o C lido) fica em cache por processo (`buffers.cached_context`): as várias chamadas de `check_text` do
pytest sobre o repo real leem o C uma vez só.

**Só esta checagem**, nos textos de uma frente (em `test/`, no WSL):

```bash
python3 -m esteira.buffers ../data/maps/X/text.inc ../src/strings.c   # caminhos relativos ao repo também valem: src/strings.c
python3 -m esteira.buffers --todos src/data/items.json                 # todo caminho medido, com bytes/tamanho
```

Sai com código 1 se houver estouro novo. Para testar um texto antes de gravar, use
`buffers.with_texts(buffers.repo_context(repo), {(arquivo, rótulo): "texto"})` com
`buffers.check_buffers(repo, ctx=...)` (modelo em `test/tests/test_buffers.py`).

## Limitações conhecidas

- **Teste estatístico do shiny**: sorteia 200 000 Pokémon e exige a taxa dentro de ±3 desvios
  padrão do esperado. Isso dá **~0,6% de falso vermelho por execução completa** (duas medições,
  com e sem charm). Um vermelho só no `shiny`, com a taxa perto do limite da faixa, vale rodar de novo
  (`--only shiny`, veja o cuidado com `--only`) antes de investigar.
- **Testes estatísticos do breeding** (`creche`): ~60 checagens de proporção a ±4σ, ~20 qui-quadrados
  (p ≥ 1e-5) e as duas taxas de shiny dos ovos a ±3σ dão **~1% de falso vermelho** por execução.
  Um vermelho isolado num item do `creche`, perto do limite, vale rodar de novo (`--only creche`)
  antes de investigar.
- **No modo paralelo** um vermelho do `shiny`/`creche` traz no detalhe o sal da execução
  (`ESTEIRA_SEED=0x...`): `make test-full` de novo usa outro sal (outras sequências do RNG), e
  `ESTEIRA_SEED=<o do detalhe> make test-full` reproduz exatamente as mesmas contagens.
- **Brock no modo completo** é adaptativo, mas **probabilístico**: treina até um nível e tenta
  algumas vezes; com azar nos golpes/RNG pode perder todas as tentativas e reprovar sem que o jogo
  tenha problema.
- **O modo completo depende da ROM jogável compilada na raiz**: ela é a base do rápido, do
  `pc`/`telas`/`floresta_brock` e do `.sav` que o `shiny` usa. A ROM de teste é recompilada pelo
  `make test-full`, a jogável não.
- **Vermelho raro no modo rápido**: a `rota1` confere a barra de HP num golpe recebido e luta até
  8 batalhas selvagens esperando levar um. Sem nenhum golpe nas 8 ela reprova (a barra não foi
  conferida). Com 4 batalhas isso dava ~0,08% das execuções; com 8 é bem mais raro. Se acontecer
  (o detalhe diz "nenhum golpe recebido"), rode de novo.
- **O inicial só muda quando a execução passa** (rodízio): um vermelho repete o mesmo inicial até
  ser corrigido. Um vermelho que só aparece com um inicial pode ser um bug específico dele;
  reproduza com `--starter`.
- **`make -O`/`--output-sync` não é suportado** no `make firered_switch`: a esteira espera a marca
  de fim de build chegar ao log (pelo `tee`) antes de testar, e com a saída agrupada ela só é
  escrita depois que a regra termina; o resultado é "falha de infraestrutura: o log do build ...
  não chegou ao fim". Use `-j` normal.
- O `make test-watch` não faz parte da esteira e não testa nada além de assistir; o relatório e a
  versão só existem para `make firered_switch`.
