#ifndef GUARD_DOSSIE_H
#define GUARD_DOSSIE_H

#include "global.h"

// O dossiê da Família Sombra (POK-54, spec 2026-11-07-familia-sombra-parte2 §5): tela cheia aberta pela Oficial
// Jenny (`special Dossie_Abrir` + `waitstate`). Uma página por vez: A ou → avança, ← volta, B fecha, e A na última
// página fecha. Os textos ficam em src/data/dossie_textos.h; os gráficos saem de tools/familia_sombra/dossie.py.
//
// Esta é a única definição das medidas do texto: a tela imprime nelas e a checagem de texto da esteira
// (test/esteira/check_text.py) mede cada texto de src/data/dossie_textos.h com as mesmas constantes.
// Todo o texto é FONT_NORMAL, em linhas de DOSSIE_LINHA_PX px (só `\n`).
//
// Ficha (página de chefe): a foto à esquerda; à direita o título em destaque, os gêmeos, a rosa e a 1ª linha da lore
// (mais estreita: DOSSIE_LORE_TOPO_PX); embaixo da foto, as outras linhas da lore na largura toda (DOSSIE_LORE_PX).
#define DOSSIE_LINHA_PX          13
#define DOSSIE_LORE_TOPO_PX      140   // 1ª linha da lore, ao lado da foto (x = 89 até a borda da pasta)
#define DOSSIE_LORE_PX           216   // demais linhas da lore e o texto da página "Depois" (x = 12)
#define DOSSIE_LORE_LINHAS       5     // linhas da lore numa página de ficha (1 ao lado da foto + 4 embaixo)
#define DOSSIE_DEPOIS_LINHAS     8     // linhas do texto da página "Depois" (sem foto)
#define DOSSIE_TITULO_PX         134   // título em destaque (o marca-texto passa 3 px de cada lado)
#define DOSSIE_CABECALHO_PX      140   // linha dos gêmeos
#define DOSSIE_ROSA_PX           128   // linha da rosa (o desenho da rosa ocupa os 12 px antes dela)
#define DOSSIE_ABA_PX            96    // texto da aba (esquerda da aba)
#define DOSSIE_FOLHA_PX          56    // "FOLHA 1/3" no fim da aba da ficha
#define DOSSIE_CAPA_ROTA_PX      52    // "ROTA 23" na caixa branca da capa
#define DOSSIE_RODAPE_PX         150   // "Arquivo: ..." no rodapé da capa (o "N/T" fica à direita)

// Chefe de cada página (DossiePagina.chefe)
#define DOSSIE_CAPA     0
#define DOSSIE_DEPOIS   5   // 1-4 = os chefes, na ordem das ocupações

struct DossiePagina
{
    u8 chefe;           // DOSSIE_CAPA, 1-4 (Dom, Cobrador, Mercenário, Pesadelo) ou DOSSIE_DEPOIS
    u8 parte;           // 1.. dentro da ficha do chefe
    u8 partes;          // quantas páginas a ficha do chefe tem
    const u8 *titulo;   // título em destaque (NULL na capa: o título dela é desenho)
    const u8 *texto;    // a lore da página (ficha: até DOSSIE_LORE_LINHAS linhas), o "Depois" ou o rodapé da capa
};

void Dossie_Abrir(void);

#if TESTBUILD
u32 Dossie_TestEstado(void);
#endif

#endif // GUARD_DOSSIE_H
