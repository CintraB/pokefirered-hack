#!/bin/sh
# Gate de testes de uma ROM recem-gerada. Chamado pela regra $(ROM) do Makefile:
#     sh test/pipeline.sh <rom>
#
#   COMPARE=1                      -> nada (build de comparacao com o original)
#   nome termina em _test.gba      -> nada (build de teste, TESTBUILD=1)
#   ROM que nao e a pokefirered_switch.gba -> so versiona (version_rom.sh)
#   SKIP_TESTS=1                   -> relatorio "NAO TESTADA" (esteira nao-testada) e versiona
#                                     a ROM com NAO_TESTADA.txt
#   senao roda a esteira rapida em test/out/<data-hora>/:
#       passou (0)                   -> versiona a ROM com o relatorio (roms/<N>.0/)
#       reprovou (1, com relatorio)  -> copia tudo para roms/ultima-falha/, APAGA a ROM, sai 1
#       qualquer outra coisa (127 sem python, 130 Ctrl-C, crash sem relatorio, log de build
#       incompleto) -> "falha de infraestrutura": nao versiona, nao mexe em ultima-falha,
#       APAGA a ROM (o proximo make retesta) e sai 1
# A ROM e apagada em todo caminho que nao versiona: sem isso o make diria "Nothing to be done" e
# uma ROM sem teste pareceria pronta. O ELF fica (o uso de memoria do ld esta em memory.txt).
#
# Variaveis opcionais (usadas pelos testes e pelo Makefile):
#   BUILD_LOG         log do build (o tee do Makefile); a esteira so le depois da marca de fim
#   ESTEIRA_CMD       comando da esteira (padrao: python3 -m esteira, executado em test/)
#   ESTEIRA_ROMS_DIR  pasta das versoes (padrao: roms)
#   ESTEIRA_OUT_BASE  pasta das execucoes (padrao: test/out)
#   ESTEIRA_OBJ_DIR   objetos do build e memory.txt (padrao: build/<nome do build>)
#   ESTEIRA_LOG_WAIT  segundos esperando a marca de fim no BUILD_LOG (padrao: 15)

rom="$1"
if [ -z "$rom" ]; then
    echo "uso: sh test/pipeline.sh <rom>" >&2
    exit 2
fi

root=$(cd "$(dirname "$0")/.." && pwd)
roms_dir=${ESTEIRA_ROMS_DIR:-roms}
base=$(basename "$rom")
marker="[esteira] build finished"     # impressa pelo Makefile logo antes de chamar este script

[ "${COMPARE:-0}" = 1 ] && exit 0
case "$base" in
    *_test.gba) exit 0 ;;
esac

if [ "$base" != "pokefirered_switch.gba" ]; then
    sh "$root/version_rom.sh" "$rom"
    exit $?
fi

name=${base#poke}
name=${name%.gba}
obj_dir=${ESTEIRA_OBJ_DIR:-build/$name}
memory_file="$obj_dir/memory.txt"
esteira=${ESTEIRA_CMD:-python3 -m esteira}

out_base=${ESTEIRA_OUT_BASE:-$root/test/out}
mkdir -p "$out_base"
out="$(cd "$out_base" && pwd)/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out"

# Roda a esteira a partir de test/ (os caminhos que ela recebe sao absolutos).
run_esteira() {
    # shellcheck disable=SC2086  # ESTEIRA_CMD e uma lista de palavras de proposito
    ( cd "$root/test" && $esteira "$@" )
}

# Nao versiona: tira a ROM do caminho para o proximo make refazer e retestar.
infra_failure() {
    rm -f "$rom"
    echo "[esteira] falha de infraestrutura: $1" >&2
    echo "[esteira] a ROM foi removida (o proximo make retesta); execucao em $out" >&2
    exit 1
}

if [ "${SKIP_TESTS:-0}" = 1 ]; then
    echo "[esteira] SKIP_TESTS=1: ROM versionada SEM testes (NAO_TESTADA.txt)"
    run_esteira nao-testada --out "$out" \
        || echo "[esteira] aviso: nao consegui escrever o relatorio NAO TESTADA" >&2
    sh "$root/version_rom.sh" "$rom" "$out" --untested
    exit $?
fi

rom_abs=$(cd "$(dirname "$rom")" && pwd)/$base
elf_abs=${rom_abs%.gba}.elf

# Log para a esteira: o do build (cortado na marca de fim, o resto e saida da propria esteira),
# mais o uso de memoria do ld guardado em memory.txt se o log desta execucao nao o traz (make
# interrompido: so o objcopy rodou de novo).
log_args=""
log_file="$out/build.log"
if [ -n "${BUILD_LOG:-}" ]; then
    waited=0
    limit=$(( ${ESTEIRA_LOG_WAIT:-15} * 10 ))
    while [ $waited -lt $limit ] && ! grep -qF "$marker" "$BUILD_LOG" 2>/dev/null; do
        sleep 0.1
        waited=$(( waited + 1 ))
    done
    if ! grep -qF "$marker" "$BUILD_LOG" 2>/dev/null; then
        infra_failure "o log do build ($BUILD_LOG) nao chegou ao fim em ${ESTEIRA_LOG_WAIT:-15} s; log possivelmente incompleto"
    fi
    awk -v m="$marker" '{ print } index($0, m) { exit }' "$BUILD_LOG" > "$log_file"
    if ! grep -qE '^[[:space:]]*EWRAM:' "$log_file" && [ -f "$memory_file" ]; then
        cat "$memory_file" >> "$log_file"
    fi
    log_args="--log $log_file"
else
    echo "[esteira] sem log de build: checagens de compilação puladas; use make firered_switch"
    if [ -f "$memory_file" ]; then
        cp "$memory_file" "$log_file"
        log_args="--log $log_file"
    fi
fi

echo "[esteira] testando $base (esteira rapida, ~35 s)..."
# shellcheck disable=SC2086  # log_args e uma lista de palavras de proposito
run_esteira rapido --rom "$rom_abs" --elf "$elf_abs" $log_args --out "$out"
status=$?

if [ $status -eq 0 ]; then
    sh "$root/version_rom.sh" "$rom" "$out"
    exit $?
fi

if [ $status -ne 1 ] || [ ! -f "$out/relatorio.html" ]; then
    infra_failure "a esteira terminou com código $status sem concluir o relatório"
fi

# Reprovada de verdade: guarda a execucao e tira a ROM do caminho. Os objetos dos arquivos
# citados no log saem junto (senao os avisos de compilacao nao reaparecem no reteste: o make
# so relinkaria e o log novo sairia limpo).
rm -rf "$roms_dir/ultima-falha"
mkdir -p "$roms_dir"
cp -r "$out" "$roms_dir/ultima-falha"
rm -f "$rom"
if [ -n "${BUILD_LOG:-}" ]; then
    grep -oE '(^|[^A-Za-z0-9_./-])src/[A-Za-z0-9_./-]+\.c:' "$log_file" | grep -oE 'src/[A-Za-z0-9_./-]+\.c' \
        | sort -u | while read -r src; do
        rm -f "$obj_dir/${src%.c}.o"
    done
fi
echo "[esteira] REPROVADA: ROM removida; relatorio em $roms_dir/ultima-falha/relatorio.html" >&2
exit 1
