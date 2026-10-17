# Esteira de testes

A esteira joga a ROM de verdade num emulador (mGBA, sem janela) apertando botões e lendo a
memória, confere o log do build e os textos do jogo, e só entrega a ROM versionada
(`roms/<N>.0/`) se tudo passou. O relatório de cada execução é uma página HTML com telas, o
vídeo acelerado da execução e o tempo de cada etapa.

Tudo roda dentro do WSL (Ubuntu). A ROM testada é sempre a `pokefirered_switch.gba` da raiz do
repo.

| Quero... | Comando (dentro do WSL, na raiz do repo) | Tempo |
|---|---|---|
| Compilar, testar e versionar a ROM | `make firered_switch -j$(nproc)` | build + ~35 s de teste |
| Compilar e versionar **sem** testar | `SKIP_TESTS=1 make firered_switch -j$(nproc)` | só o build |
| Testar de novo a ROM já compilada, sem versionar | `make test-quick` | ~35 s |
| Teste completo (cenários longos, ROM de teste) | `make test-full` | ~12-17 min (o shiny ~4-9 min, a creche ~4 min) |
| Ver o roteiro rápido numa janela | `make test-watch` | ~ tempo real |
| Ver as evoluções sem troca (Hack 3) numa janela | `make test-watch CENARIO=evolucoes` | ~9 min (tempo real) |
| Ver um ovo da creche chocar (Hack 6) numa janela | `make test-watch CENARIO=ovo` | ~1,5 min (tempo real) |
| Aprovar as telas de referência | `make test-approve` | instantâneo |
| Testes unitários da própria esteira | `python3 -m pytest test -q` | ~5-6 min (~80 s sem os lentos) |

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
PowerShell não mexer no `$(nproc)` nem em variáveis:

```powershell
wsl -d Ubuntu --cd /mnt/c/Users/crist/Documents/GitHub/pokefirered -- bash -c 'make firered_switch -j$(nproc)'
wsl -d Ubuntu --cd /mnt/c/Users/crist/Documents/GitHub/pokefirered -- bash -c 'SKIP_TESTS=1 make firered_switch -j$(nproc)'
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
     para a caixa, sintaxe;
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
| `creche` | **ROM de teste** | Hack 6, breeding genético: ~21 000 ovos pelo caminho real da creche comparados com a distribuição exata das regras (IVs, natureza, habilidade, golpes de ovo, gênero, itens), taxa de shiny dos ovos com/sem charm e os Power items em batalha (veja abaixo) |
| `ovo` | **ROM de teste** | Hack 6: um ovo de verdade na creche de Four Island, entregue pelo velho, chocado andando e conferido na memória |

Depende da ROM jogável da raiz (se não existir, vira falha `emulador/rom-playable`). Não grava
em `roms/`: o resultado fica em `test/out/<data-hora>/`. Rode com o terminal aberto por ~12-17
min; o shiny leva ~4-9 min disso e a `creche` ~4 min.

O `shiny` e o `evolucoes` partem do mesmo save do jogo (o `.sav` do fim do `captura`), cada um
numa **sessão própria** da ROM de teste: um não herda o que o outro fez (o shiny liga a Dex
Nacional e ganha o Shiny Charm), e `--only evolucoes` roda só ele (~30 s).

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
pedras no menu de Pokémon) e os 6 itens à venda na Celadon Dept. Store 4F por 2100.

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

### `make test-approve`

Promove as telas de uma execução a **screenshots de referência**:

```bash
make test-approve                          # a execução mais recente em test/out/
make test-approve DIR=test/out/20261017-030544   # uma execução específica (também vale roms/ultima-falha)
```

Copia `telas/*.png` dos pontos-chave para `test/referencias/<INICIAL>/<ponto>.png` (o inicial vem
do `meta.json` da execução). Pontos: `nome`, `inicial`, `batalha_rival`, `captura`,
`save_continue` (modo rápido) e `bolsa`, `resumo`, `pokedex`, `opcoes`, `cartao`, `pc`, `loja`,
`mapa` (tour do modo completo). Cada inicial tem o seu conjunto: para aprovar os três, rode a
esteira uma vez com cada um (`--starter`). As telas da cena de evolução (`evo_*_antes`,
`evo_*_depois`, do cenário `evolucoes`) não dependem do inicial e vão para
`test/referencias/COMUM/`, que vale para os três.

"Mais recente" é a pasta `test/out/<data-hora>` modificada por último, de qualquer comando;
confira o `DIR` quando tiver rodado outras coisas. O comando **não confere se a execução
passou**: quem decide se a tela está certa é você.

Diferença de tela **nunca reprova** a ROM: vira *aviso* no relatório, com três imagens (a atual,
a referência e o diff com os pixels diferentes em vermelho). Sem referência também é só aviso.
Telas com dados que mudam de execução para execução (dinheiro, HP, tempo de jogo, vistos na
Pokédex) podem continuar avisando mesmo depois de aprovadas.

**Revisar e commitar:** `test/referencias/` hoje **não está no Git** (aparece como `??` no
`git status`). Abra as imagens (`test/referencias/<INICIAL>/*.png`, no Explorer) e, se estiverem
certas, versione-as:

```powershell
git add test/referencias
git commit -m "test(esteira): referências de tela"
```

Referências aprovadas depois entram como alterações normais; o `git diff --stat test/referencias`
mostra quais PNG mudaram.

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

**Cenário do modo completo numa janela** (`CENARIO=`: `evolucoes` ou `ovo`):

```bash
make test-watch CENARIO=evolucoes                    # Hack 3: as evoluções, em tempo real
make test-watch CENARIO=evolucoes STARTER=SQUIRTLE   # usa o save de uma execução com esse inicial
make test-watch CENARIO=ovo                          # Hack 6: o ovo entregue e chocando (~1,5 min)
```

- Recompila antes a **ROM de teste** (`make firered_switch TESTBUILD=1`, como o `test-full`) e
  roda o cenário nela, na janela, com o mesmo roteiro do modo completo (inclusive as
  conferências: no fim aparece o resumo de ok/falhas).
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
| `assistir` | Roteiro rápido (ou, com `--cenario evolucoes`, esse cenário na ROM de teste) numa janela (é o que o `make test-watch` chama) |
| `nao-testada --out DIR` | Só o relatório "NÃO TESTADA" (usado por `SKIP_TESTS=1`) |

Opções de `rapido` e `completo` (`--rom`, `--elf` e `--out` são obrigatórios):

| Opção | Significado |
|---|---|
| `--rom`, `--elf` | ROM jogável e seu ELF (o ELF dá os endereços dos símbolos) |
| `--rom-test`, `--elf-test` | ROM de teste e ELF, só para cenários que usam a build de teste (padrão: `pokefirered_switch_test.*` na raiz) |
| `--log` | Log do build; sem ele só a checagem de texto roda (a do build vira aviso) |
| `--out` | Pasta da execução (relatório, telas, estados, vídeo) |
| `--only NOME` | Só um item: `build`, `texto`, `abertura`, `rota1`, `captura`; no `completo` também `pc`, `telas`, `floresta_brock`, `master`, `shiny`, `evolucoes`, `creche`, `ovo` |
| `--starter X` | Força `BULBASAUR`, `CHARMANDER` ou `SQUIRTLE` (não mexe no rodízio) |
| `--sem-video` | Não grava `video.webp` |

`assistir`: `--starter`, `--from {encomenda,rival}` ou `--cenario {evolucoes,ovo}` (com `--rom-test`/`--elf-test`, padrão os da raiz), `--rom`, `--elf`. Códigos de saída de
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
- `--only shiny`, `--only evolucoes`, `--only creche` e `--only ovo` precisam do `<OUT>/captura.sav` que o `rapido`/`completo` anterior (mesma
  pasta) deixou; sem ele o resultado é uma falha dizendo o que rodar antes;
- `--only build` e `--only texto` não usam emulador e não têm esse problema.

O vídeo (`video.webp`) grava a execução inteira acelerada, tipicamente 4x (um quadro a cada 8
emulados, 30 fps; execuções longas descartam quadros para caber no teto de 25 MB), e é embutido
no relatório. Problema para gravar é só aviso. Com
`--only` de item sem emulador não há vídeo.

## Testes unitários da esteira

```bash
python3 -m pytest test -q                       # tudo: ~5-6 min
ESTEIRA_SKIP_SLOW=1 python3 -m pytest test -q   # sem os lentos: ~80 s
```

Na raiz do repo, dentro do WSL. Os testes marcados `slow` compilam de verdade (um deles quebra um
`.c` numa cópia do repo e confere que o `make firered_switch` falha; não toca em `roms/`);
`ESTEIRA_SKIP_SLOW=1` pula os lentos. Os testes que precisam do emulador usam a
`pokefirered_switch.gba` da raiz e são pulados se ela não existir. Rode isto depois de mexer em
qualquer arquivo de `test/esteira/`.

## Requisitos (uma vez só)

No Ubuntu do WSL, como root:

```bash
sudo apt install libmgba-dev mgba-sdl libpng-dev python3-pytest python3-pil
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
  `rule` (`charmap`, `terminador`, `largura`...), `fingerprint` (sha1 abreviado do texto cru do
  rótulo) e, na regra `largura`, `valor` (largura em px da linha mais larga).

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

**Largura do texto** (regra `largura`): cada fonte de texto tem a sua largura útil em px, tirada
dos templates de janela do código. As principais: diálogos de mapa (`data/maps/*/text.inc`) e a
maioria de `data/text/*.inc`, 208 px (26 tiles); descrições de itens (`src/data/items.json`),
200 px; Quest Log (`src/data/text/quest_log.h`) e barra de ajuda do menu Start (os
`gStartMenuDesc_*` de `src/strings.c`), 238 px. Textos que não são diálogo (menus, o resto de
`strings.c`, nomes, `help_system`, `new_game_intro`, `fame_checker`, `pokedude`, `pc_transfer`,
`save`, `pokedex_rating`, braille, o resto de `src/data/text/*.h`) **não têm checagem de largura**: a janela
varia ou não foi determinada. A tabela completa, com o motivo de cada uma, está em `WIDTH_RULES`
em `test/esteira/check_text.py`. Os caracteres ({PLAYER}/{RIVAL} medem 7 letras) e o espaçamento
entre letras seguem o jogo.

## Limitações conhecidas

- **Teste estatístico do shiny**: sorteia 200 000 Pokémon e exige a taxa dentro de ±3 desvios
  padrão do esperado. Isso dá **~0,6% de falso vermelho por execução completa** (duas medições,
  com e sem charm). Um vermelho só no `shiny`, com a taxa perto do limite da faixa, vale rodar de novo
  (`--only shiny`, veja o cuidado com `--only`) antes de investigar.
- **Testes estatísticos do breeding** (`creche`): ~60 checagens de proporção a ±4σ, ~20 qui-quadrados
  (p ≥ 1e-5) e as duas taxas de shiny dos ovos a ±3σ dão **~1% de falso vermelho** por execução.
  Um vermelho isolado num item do `creche`, perto do limite, vale rodar de novo (`--only creche`)
  antes de investigar.
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
