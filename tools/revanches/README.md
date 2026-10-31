`gerar.py`: times das revanches do Vs. Seeker por degrau (POK-42), a partir de `sRematches`, dos times atuais e de `regras.json` (níveis, IVs, itens, ramos de evolução) e `temas.json` (espécies de cada classe).
Regenerar (WSL): `python3 -I tools/revanches/gerar.py` grava `src/data/rematch_tiers.h`; `--conferir` sai com 1 se o header commitado divergir.
Amostra para revisão: `python3 -I tools/revanches/gerar.py --amostra > amostra.md` (times de 6 linhas nos degraus 1, 3 e 5, temas por classe e itens por degrau).
