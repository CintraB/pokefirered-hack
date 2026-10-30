`gen6.json`: categoria e tipo de cada golpe (1–360), tipos das 18 espécies que viram Fada e learnsets X/Y dos 6 golpes Fada, tirados dos CSVs da PokéAPI (`data/v2/csv`, version group X/Y).
Regenerar (WSL): `python3 -I tools/gen6/gerar.py` (baixa os CSVs para uma pasta temporária, fora do repo, e regrava o JSON).
`python3 -I tools/gen6/gerar.py --aplicar` acrescenta `.category` em `src/data/battle_moves.h` (só numa tabela ainda sem `.category`).
