<div align="center">

# 🔥 Pokémon FireRed — PT-BR (hack Cintra)

**FireRed em português do Brasil, com qualidade de vida dos jogos atuais, dia e noite, clima,<br>
a Pokédex inteira obtível e uma esteira de testes automática no emulador.**

![GBA](https://img.shields.io/badge/plataforma-Game%20Boy%20Advance-6a3fa0?style=flat-square)
![Idioma](https://img.shields.io/badge/idioma-PT--BR-009c3b?style=flat-square)
![Base](https://img.shields.io/badge/base-pret%2Fpokefirered-e3350d?style=flat-square)
![Linguagem](https://img.shields.io/badge/C-agbcc-555555?style=flat-square)
![Testes](https://img.shields.io/badge/pytest-4660%20testes-2ea44f?style=flat-square)
![Esteira](https://img.shields.io/badge/esteira-363%20checagens-2ea44f?style=flat-square)
![Versão](https://img.shields.io/badge/ROM-v50-informational?style=flat-square)

<img src="docs/readme/inicial.png" width="240" alt="Escolha do inicial em português">
<img src="docs/readme/chuva.png" width="240" alt="Batalha com chuva contínua">
<img src="docs/readme/novidades.png" width="240" alt="Tela de novidades do Prof. Carvalho">

</div>

---

## Sumário

- [O que é](#o-que-é)
- [Destaques](#destaques)
- [Tudo o que mudou](#tudo-o-que-mudou)
- [Galeria](#galeria)
- [Linha do tempo](#linha-do-tempo)
- [Esteira de testes](#esteira-de-testes)
- [Como compilar](#como-compilar)
- [Onde fica cada coisa](#onde-fica-cada-coisa)
- [Créditos](#créditos)

## O que é

Uma hack pessoal de **Pokémon FireRed**, feita sobre a decompilação da
[pret](https://github.com/pret/pokefirered) (versão do Nintendo Switch Online, `pokefirered_switch.gba`).
O jogo inteiro foi traduzido para o português do Brasil e ganhou recursos dos jogos mais novos, sem
perder o jeito do FireRed.

> [!NOTE]
> Projeto feito para jogar, sem distribuição de ROM. Para compilar, você precisa da sua própria cópia
> do jogo (veja [Como compilar](#como-compilar)).

## Destaques

| | Recurso | Em uma frase |
|:-:|---|---|
| 🇧🇷 | **Tradução completa** | Textos, menus, nomes, Pokédex e ajuda em português do Brasil. |
| ⚡ | **Jogo mais rápido** | Andar e correr mais rápidos, texto instantâneo, batalhas mais ágeis. |
| ✨ | **Shiny mais comum** | 1 em 4096, e o Amuleto Brilhante dobra a chance. |
| 🔁 | **Fim das trocas** | Quem evoluía por troca evolui por nível (com o item, quando precisa). |
| 📋 | **Resumo turbinado** | Páginas EVOLUÇÃO (com amizade em corações) e IVs/EVs. |
| 🥚 | **Creche genética** | IVs, natureza e golpes de ovo passam dos pais, com itens de criação. |
| 🌗 | **Dia e noite** | Um dia dura uma hora; o céu muda de cor e os encontros mudam com a hora. |
| 🌦️ | **Clima** | Chuva, neve, areia, cinzas e sol forte por região, e visíveis na batalha. |
| 🧚 | **Tipos e golpes modernos** | Físico ou especial por golpe e o tipo Fada, como em Pokémon X e Y. |
| 📖 | **Pokédex completa** | Exclusivos do LeafGreen, os dois fósseis, lendários e míticos obtíveis. |
| 🛠️ | **Melhorias modernas** | Exp. Share para todos, PC Portátil, HMs sem ensinar, status com L/R… |
| 🏆 | **Conquistas e diário** | 41 conquistas com prêmio na bolsa e o diário das batalhas marcantes, no Cartão de Treinador. |
| 🔝 | **Revanches por degrau** | Depois do Hall da Fama, a Elite 4 e as revanches do Explorador VS sobem até o nível 100. |
| 🗞️ | **Tela de novidades** | O Prof. Carvalho apresenta cada mudança em cartões ilustrados. |
| 🧪 | **Esteira de testes** | Toda ROM é jogada no emulador e testada antes de existir. |

## Tudo o que mudou

> A mesma lista aparece dentro do jogo, na **tela de novidades** do Prof. Carvalho.

<details open>
<summary><b>🌦️ Clima e batalha</b></summary>

| | |
|---|---|
| **Clima na batalha** | Chuva, granizo, areia e sol aparecem durante a batalha toda e somem enquanto um golpe é animado. Com Cloud Nine ou Air Lock em campo, a cena volta ao normal. |
| **Sol forte** | A Ilha Cinnabar e o Monte Ember têm dias de sol forte, com o efeito do Emerald: a tela clareia e pulsa. Na batalha, começa com sol. |
| **Clima por região** | Sorteado a cada período: chuva no litoral, neve na Ilha Quatro (que vira granizo na batalha), areia nas Rotas 3 e 10, cinzas e sol forte no vulcão. |
| **Status com L/R** | Na escolha da ação, **L** mostra os bônus e as quedas do seu Pokémon e **R** os do adversário (`Atq+2 Vel-1`…). |
| **Chefes mais espertos** | Líderes, Elite 4 e rival preparam o terreno no 1º turno e escolhem o golpe pelo PS de cada lado. |
| **Chefes com clima** | A Misty abre com Dança Chuva e o Blaine com Dia de Sol, com times montados para o clima. |
| **Barra de PS moderna** | Anda rápido mesmo com muito PS e muda de cor aos poucos, do verde ao vermelho. |

<p align="center">
<img src="docs/readme/chuva.png" width="200" alt="Chuva">
<img src="docs/readme/granizo.png" width="200" alt="Granizo">
<img src="docs/readme/areia.png" width="200" alt="Tempestade de areia">
<img src="docs/readme/sol.png" width="200" alt="Sol">
</p>
</details>

<details open>
<summary><b>🧚 Tipos e golpes</b></summary>

| | |
|---|---|
| **Físico ou especial por golpe** | Cada golpe é Físico, Especial ou de Estado, como desde a 4ª geração: Soco de Fogo usa o Ataque, e Thick Fat e queimadura seguem a categoria. No resumo, o detalhe do golpe mostra **FÍSICO**, **ESPEC.** ou **ESTADO** ao lado do PODER. |
| **Tipo Fada** | A tabela de tipos de Pokémon X e Y: Fada vence Dragão, Lutador e Sombrio e é imune a Dragão; Aço não resiste mais a Fantasma e Sombrio. 18 espécies viraram Fada (Clefairy, Jigglypuff, Togepi, Marill, Ralts, Mawile…), e Encantar, Beijo Doce e Luar também. |
| **Seis golpes de Fada** | Expl. Lunar, Jogo Duro, Clarão Desl., Beijo Dren., Vento Fada e Voz Desarm., com os dados de X e Y, nos níveis de X e Y. O Poder Oculto dos seus Pokémon não muda. |

<p align="center">
<img src="docs/readme/resumo_fada.png" width="240" alt="Resumo do Gardevoir, Psíquico e Fada">
<img src="docs/readme/golpe_fada.png" width="240" alt="Expl. Lunar no resumo, Fada e especial">
</p>
</details>

<details open>
<summary><b>🏆 Conquistas e diário</b></summary>

| | |
|---|---|
| **Conquistas** | 41 conquistas em 5 abas (História, Batalha, Captura, Treino e Exploração): as 8 insígnias, Elite 4 e Campeão, treinadores vencidos de 10 em 10, shinies, lendários, Pokédex, nível 100, ovo perfeito, ₽999.999, horas de jogo… Cada linha mostra ✓ ou o progresso (`87/100`), e o rodapé, o total da aba. |
| **Prêmio na hora** | Ao conquistar, o jogo pausa com um aviso animado e a fanfarra, e o prêmio cai na bolsa (bolsa cheia: no PC). Prêmios maiores para as conquistas mais difíceis, até a Master Ball. |
| **Save antigo reconhecido** | Na primeira vez que um save de antes abre nesta versão, o jogo confere o que já foi feito e entrega tudo num aviso só. O que não dá mais para provar (vencer um líder com um Pokémon só, vencer o rival em todas) fica riscado e fora do total. |
| **Diário da jornada** | A primeira vitória contra cada líder, o rival, a Elite 4 e o Campeão, e cada lendário capturado ou derrotado: tempo de jogo, turnos, time usado e o MVP (quem mais nocauteou). |
| **Onde fica** | No Cartão de Treinador (menu START), o **SELECT** abre as conquistas; na tela, **L/R** trocam a aba e o **SELECT** alterna para o diário. |

<p align="center">
<img src="docs/readme/conquistas.png" width="240" alt="Tela de conquistas, aba História">
<img src="docs/readme/diario.png" width="240" alt="Diário da jornada">
<img src="docs/readme/conquista_aviso.png" width="240" alt="Aviso de conquista com o prêmio">
</p>
</details>

<details open>
<summary><b>🔝 Revanches por degrau</b></summary>

| | |
|---|---|
| **A guarda da Liga pergunta** | Depois do Hall da Fama, a guarda na porta da Elite 4 (Platô Índigo) pergunta o nível das batalhas a cada visita: **Normal** (o jogo de sempre) ou **Nível 60, 70, 80, 90 e 100**, em escolha livre. Enquanto a Lorelei está ausente (a Liga fecha até o fim das Ilhas Sevii), a escolha vale só para o Explorador VS. |
| **Para quem vale** | Elite 4, Campeão e todas as revanches do **Explorador VS**. O primeiro combate de cada treinador não muda. |
| **Times mais fortes** | 6 Pokémon em volta do nível escolhido (o ás um pouco acima), espécies evoluídas e mais fortes do tema de cada classe, inclusive de Johto e Hoenn, com item segurado e IVs que sobem com o degrau (até 31). A Elite 4 e o Campeão têm times feitos à mão para cada degrau. |
| **IA dos chefes** | Do Nível 80 para cima, as revanches do Explorador VS usam a IA dos líderes e da Elite 4. |
| **Conquistas** | Vencer uma revanche no Nível 100 e a Liga no Nível 100 são duas das 41 conquistas. |

<p align="center">
<img src="docs/readme/revanche_lista.png" width="240" alt="A guarda da Liga com a lista de níveis">
</p>
</details>

<details>
<summary><b>🛠️ Melhorias modernas</b></summary>

| | |
|---|---|
| **Repelente automático** | Quando o efeito acaba, o jogo pergunta se você quer usar outro. |
| **PE ao capturar** | Capturar dá PE à equipe, como se o Pokémon tivesse sido derrotado. |
| **PE para a equipe toda** | Quem lutou ganha tudo e o resto ganha metade, sem item. O assistente da Rota 15 dá o Ovo da Sorte. |
| **PC Portátil** | Já vem nos Itens-chave e abre o PC de qualquer lugar (menos ginásios e Liga). Dá para registrar no SELECT. |
| **Incubadora** | Dada pelo dono da creche da Ilha Quatro: Ovos chocam 2× mais rápido (4× com Corpo Chama ou Armadura Magma). |
| **HMs sem ensinar** | Com a insígnia e a HM na bolsa, basta um Pokémon que possa aprender o golpe. Cavernas escuras já acendem. |
| **Viagem pelo Mapa** | Com o Voar liberado, o Mapa da Cidade leva direto a uma cidade visitada. |
</details>

<details>
<summary><b>⚡ Ritmo, shiny e evoluções</b></summary>

- **Andar e correr mais rápido**; os eventos da história seguem no ritmo normal.
- **Texto instantâneo** com a velocidade Rápida, que é o novo padrão.
- **Batalhas mais ágeis**: pausas mais curtas e barras de PS e PE mais rápidas.
- **Shiny 1/4096** para selvagens e ovos; o **Amuleto Brilhante** vem do Prof. Carvalho depois dos 151 de Kanto.
- **Fim das trocas**, no nível 37:
  - direto: Kadabra → Alakazam, Machoke → Machamp, Graveler → Golem, Haunter → Gengar;
  - segurando o item (que não é gasto): Onix → Steelix e Scyther → Scizor (Revestimento Metálico), Seadra → Kingdra (Escama de Dragão), Porygon → Porygon2 (Melhora), Clamperl → Huntail/Gorebyss, Slowpoke → Slowking e Poliwhirl → Politoed (Pedra do Rei).
- **Itens de evolução à venda** no 4º andar da Loja de Celadon, inclusive a Pedra Solar.
- **Espeon e Umbreon**: Eevee com amizade 220+ evolui de dia (Espeon) ou no entardecer e à noite (Umbreon).
- **Milotic**: Feebas evolui segurando a Escama Prisma (loja da Ilha Quatro).

<p align="center">
<img src="docs/readme/evo_gengar_antes.png" width="240" alt="Haunter evoluindo">
<img src="docs/readme/evo_gengar_depois.png" width="240" alt="Gengar">
</p>
</details>

<details>
<summary><b>📋 Resumo do Pokémon e creche</b></summary>

- **Página EVOLUÇÃO**: como cada Pokémon evolui (nível, pedra, item, troca ou amizade).
- **Amizade em corações**, com o número (até 255) e a marca 220+.
- **Página IVs/EVs**: nota de cada IV (de Fraco a Perfeito), total em %, EVs e tipo do Poder Oculto.
- **Herança de IVs**: o ovo segue a média dos pais, com variação e mutações raras.
- **Natureza e golpes de ovo** herdados dos pais.
- **Itens de criação** na Ilha Quatro: Pedra Eterna, Nó do Destino e os itens de Poder.

<p align="center">
<img src="docs/readme/resumo_evolucao.png" width="240" alt="Página EVOLUÇÃO">
<img src="docs/readme/resumo_amizade.png" width="240" alt="Amizade em corações">
<img src="docs/readme/resumo_ivs.png" width="240" alt="Página IVs/EVs">
</p>
</details>

<details>
<summary><b>🌗 Dia e noite</b></summary>

- **Um dia do jogo dura uma hora**: manhã (04h–10h), tarde (10h–17h), entardecer (17h–20h) e noite (20h–04h).
- **Hora no menu START**, cor do céu por período e um aviso quando o período vira.
- **Encontros por horário**: à noite aparecem Hoothoot e outros notívagos.

<p align="center">
<img src="docs/readme/relogio.png" width="240" alt="Hora no menu START">
<img src="docs/readme/aviso_noite.png" width="240" alt="Aviso de que a noite chegou">
</p>
</details>

<details>
<summary><b>📖 Pokédex, lendários e pós-Liga</b></summary>

- **Pokédex Nacional desde o início.**
- **Exclusivos do LeafGreen** aparecem nos mesmos lugares do FireRed, dividindo a vez.
- **Iniciais na Zona de Safári**, raros: Bulbasaur no Leste, Charmander no Norte, Squirtle no Oeste (surfando).
- **Caverna Mutante** muda de Pokémon a cada dia.
- **Os dois fósseis** do Monte Lua (Domo e Hélice).
- **Bilhetes do Carvalho**: Bilhete Místico (Lugia e Ho-Oh) e Bilhete Aurora (Deoxys) no primeiro Hall da Fama.
- **Cães em sequência**: Entei, Raikou e Suicune, um depois do outro.
- **Segunda chance**: lendário derrotado volta na próxima entrada no Hall da Fama.
- **Míticos**: Mew, Celebi e Jirachi escondidos pelo mundo, com pistas.
- **Presentes do Carvalho**: um ovo raro por vitória na Liga (Larvitar, Bagon, Beldum) e ¥45.000 na primeira.

<p align="center">
<img src="docs/readme/pokedex_nacional.png" width="240" alt="Pokédex Nacional">
<img src="docs/readme/pos_liga_ovo.png" width="240" alt="Ovo raro do Prof. Carvalho">
</p>
</details>

<details>
<summary><b>🇧🇷 Sobre a hack</b></summary>

- **Tudo em português do Brasil**: textos, menus, nomes, Pokédex e sistema de ajuda, com glossário próprio e medição de largura de cada janela.
- **Save em qualquer emulador de GBA.**
- **Tela de novidades**: o Prof. Carvalho mostra cada mudança num cartão com ícone, antes e depois.
</details>

## Galeria

| | | |
|:-:|:-:|:-:|
| <img src="docs/readme/batalha_rival.png" width="240" alt="Batalha com o rival"><br>Batalha com o rival | <img src="docs/readme/status_lr.png" width="240" alt="Status com L/R"><br>Status com **R** (7 alterações) | <img src="docs/readme/sol_forte.png" width="240" alt="Sol forte em Cinnabar"><br>Sol forte em Cinnabar |
| <img src="docs/readme/neve.png" width="240" alt="Neve na Ilha Quatro"><br>Neve na Ilha Quatro | <img src="docs/readme/novidades_cartao.png" width="240" alt="Cartão de novidade"><br>Cartão de novidade | <img src="docs/readme/loja_quatro.png" width="240" alt="Loja da Ilha Quatro"><br>Itens de criação |
| <img src="docs/readme/pc.png" width="240" alt="PC"><br>PC | <img src="docs/readme/inicial.png" width="240" alt="Escolha do inicial"><br>Escolha do inicial | <img src="docs/readme/sol.png" width="240" alt="Sol na batalha"><br>Sol na batalha |
| <img src="docs/readme/resumo_fada.png" width="240" alt="Gardevoir Psíquico e Fada"><br>Gardevoir agora é **Fada** | <img src="docs/readme/golpe_fisico.png" width="240" alt="M. Esmagador físico"><br>Categoria do golpe: **FÍSICO** | <img src="docs/readme/golpe_fada.png" width="240" alt="Expl. Lunar"><br>Golpe novo: **Expl. Lunar** |

## Linha do tempo

| Etapa | O que trouxe |
|---|---|
| **Hack 1** | Build do Switch jogável num GBA comum (save na flash). |
| **Hack 2** | Shiny 1/4096 + Amuleto Brilhante; jogo mais rápido. |
| **Hack 3** | Fim das evoluções por troca. |
| **Hacks 4 e 5** | Páginas EVOLUÇÃO e IVs/EVs no resumo. |
| **Hack 6** | Creche genética. |
| **Hack 7** | Dia e noite, clima por região, encontros por horário. |
| **Tradução** | O jogo inteiro em PT-BR, em três rodadas. |
| **Hack 8** | Pokédex completa: LeafGreen, fósseis, lendários e míticos. |
| **Novidades** | Tela do Prof. Carvalho com os cartões. |
| **Melhorias modernas** | Repelente, PE, IA, barra de PS, PC Portátil, Incubadora, HMs, viagem, status com L/R, chefes com clima. |
| **Clima na batalha** | Clima sempre visível e o sol forte consertado. |
| **Físico/especial e Fada** (30/10) | Categoria por golpe, tipo Fada com a tabela de X e Y, 18 espécies e 6 golpes novos. |
| **Conquistas e diário** (31/10) | 41 conquistas com prêmio e aviso, save antigo reconhecido e o diário das batalhas marcantes. |
| **Revanches por degrau** (31/10) | A guarda da Liga escolhe o nível (Normal a 100) da Elite 4, do Campeão e das revanches do Explorador VS: times de 6, item, IVs altos e a IA dos chefes. |

## Esteira de testes

Nenhuma ROM existe sem passar pela esteira. O `make firered_switch` compila, joga o começo do jogo
sozinho no emulador e só versiona a ROM em `roms/<N>.0/` se tudo der certo.

```mermaid
flowchart LR
    A[make firered_switch] --> B[compila a ROM]
    B --> C{log do build<br>e textos}
    C -->|ok| D[emulador: abertura,<br>Rota 1 e captura]
    D -->|verde| E[(roms/N.0/)]
    C -->|erro| F[roms/ultima-falha/<br>relatório + savestates]
    D -->|vermelho| F
    E --> G[make test-full:<br>ROM de teste com atalhos]
    G --> H[cenários longos:<br>clima, creche, shiny,<br>evoluções, conquistas…]
    H --> I[telas comparadas<br>com as referências]
```

- **Dois modos**: o rápido (~40 s) roda em todo build; o completo (~4 min) roda dezenas de cenários
  numa ROM de teste com atalhos (dar item, mudar o relógio, abrir batalha, ler a RAM).
- **Rodízio de iniciais**: cada execução joga com Bulbasaur, Charmander ou Squirtle, e as telas são
  comparadas pixel a pixel com as referências aprovadas de cada um.
- **Checagem de texto**: mede a largura de cada frase traduzida na janela onde ela aparece e o
  tamanho dos buffers, para nada estourar.
- **4660 testes em pytest** cobrem a própria esteira e as regras de cada hack.

<details>
<summary>Comandos (WSL)</summary>

```bash
make firered_switch          # ROM testada e versionada
make test-quick              # retesta sem versionar
make test-full               # tudo, com a ROM de teste
make test-watch              # assiste numa janela
python3 -m pytest test -q    # testes da esteira
```

O manual completo está em [`test/README.md`](test/README.md).
</details>

## Como compilar

1. Prepare o ambiente da pret (WSL + `agbcc`) seguindo o [INSTALL.md](INSTALL.md).
2. Na raiz do repositório, no WSL:

   ```bash
   make firered_switch
   ```

3. A ROM testada sai em `roms/<N>.0/pokefirered_switch.gba`. Se a esteira reprovar, o relatório fica
   em `roms/ultima-falha/relatorio.html`.

> [!TIP]
> `SKIP_TESTS=1 make firered_switch` gera a ROM sem a esteira (ela sai marcada como não testada).

## Onde fica cada coisa

| Caminho | O quê |
|---|---|
| `src/battle_weather_visual.c` | Clima sempre visível na batalha |
| `src/field_weather.c` | Clima do campo, inclusive o sol forte restaurado |
| `src/day_night.c`, `src/data/day_night_weather.h` | Relógio, períodos e sorteio de clima por região |
| `src/data/novidades/cartoes.json` | Cartões da tela de novidades |
| `src/field_move_rules.c` | HMs sem ensinar |
| `test/esteira/` | A esteira de testes (Python + mGBA) |
| `test/referencias/` | Telas aprovadas, por inicial |
| `roms/` | ROMs testadas e versionadas |

## Créditos

- **[pret](https://github.com/pret/pokefirered)**: a decompilação do FireRed que é a base de tudo
  ([pret.github.io](https://pret.github.io/)).
- **[pret/pokeemerald](https://github.com/pret/pokeemerald)**: as tabelas de cor do sol forte.
- **Pokémon** é marca da Nintendo, Creatures Inc. e GAME FREAK inc. Este é um projeto de fã, sem fins
  comerciais.

<details>
<summary>ROMs que a decompilação original reproduz byte a byte</summary>

* [**pokefirered.gba**](https://datomatic.no-intro.org/?page=show_record&s=23&n=1616) `sha1: 41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc`
* [**pokeleafgreen.gba**](https://datomatic.no-intro.org/?page=show_record&s=23&n=1617) `sha1: 574fa542ffebb14be69902d1d36f1ec0a4afd71e`
* [**pokefirered_rev1.gba**](https://datomatic.no-intro.org/?page=show_record&s=23&n=1672) `sha1: dd5945db9b930750cb39d00c84da8571feebf417`
* [**pokeleafgreen_rev1.gba**](https://datomatic.no-intro.org/index.php?page=show_record&s=23&n=1668) `sha1: 7862c67bdecbe21d1d69ce082ce34327e1c6ed5e`
* [**pokefirered_switch.gba**](https://datomatic.no-intro.org/index.php?page=show_record&s=23&n=x550) `sha1: baa452d0b24629dd7782cfc07a8984085dde1311`
* [**pokeleafgreen_switch.gba**](https://datomatic.no-intro.org/index.php?page=show_record&s=23&n=x551) `sha1: 62b9fc77549dbc67032eb6cbd0ea6ad3b825690f`
</details>
