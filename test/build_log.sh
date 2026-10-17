#!/bin/sh
# Prepara o log de build que a esteira le (--log). Usado por test/pipeline.sh e pelos alvos
# make test-quick/test-full:
#     sh test/build_log.sh <log do make> <memory.txt> <destino>
#
# - Copia o log do make ate a marca de fim de build: o que vem depois e saida da propria esteira
#   daquela vez ("*** ROM NAO TESTADA ***", arquivos citados no resumo...), nao do build.
# - Se o log nao traz o uso de EWRAM/IWRAM (o make so refez a ROM com o objcopy, sem o ld:
#   reteste depois de um vermelho, SKIP_TESTS, Ctrl-C), acrescenta o <memory.txt> que o link
#   grava junto dos objetos (build/<nome>/memory.txt).
# - Sem o log do make: o destino fica so com o <memory.txt>, avisando no terminal.
# Sai 0 se escreveu o destino; 1 se nao ha log nem memory.txt (o destino nao e criado).

log="$1"
memory="$2"
dest="$3"
marker="[esteira] build finished"     # impressa pelo Makefile logo antes de chamar a esteira

if [ -n "$log" ] && [ -f "$log" ]; then
    awk -v m="$marker" '{ print } index($0, m) { exit }' "$log" > "$dest" || exit 1
else
    echo "[esteira] sem log de build: checagens de compilação puladas; use make firered_switch"
    [ -f "$memory" ] || exit 1
    : > "$dest"
fi
if ! grep -qE '^[[:space:]]*EWRAM:' "$dest" && [ -f "$memory" ]; then
    cat "$memory" >> "$dest"
fi
exit 0
