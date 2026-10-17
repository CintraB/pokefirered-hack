#!/bin/sh
# Gate de testes de uma ROM recem-gerada. Chamado pela regra $(ROM) do Makefile:
#     sh test/pipeline.sh <rom>
#
#   COMPARE=1                      -> nada (build de comparacao com o original)
#   nome termina em _test.gba      -> nada (build de teste, TESTBUILD=1)
#   ROM que nao e a pokefirered_switch.gba -> so versiona (version_rom.sh)
#   SKIP_TESTS=1                   -> versiona marcada como NAO TESTADA
#   senao roda a esteira rapida em test/out/<data-hora>/:
#       passou -> versiona a ROM com o relatorio (roms/<N>.0/)
#       falhou -> copia tudo para roms/ultima-falha/, APAGA a ROM (e o ELF) e sai 1
#
# Variaveis opcionais (usadas pelos testes e pelo Makefile):
#   BUILD_LOG         log do build (o tee do Makefile); a esteira so le depois da marca de fim
#   ESTEIRA_CMD       comando da esteira (padrao: python3 -m esteira, executado em test/)
#   ESTEIRA_ROMS_DIR  pasta das versoes (padrao: roms)
#   ESTEIRA_OUT_BASE  pasta das execucoes (padrao: test/out)
#   ESTEIRA_OBJ_DIR   objetos do build (padrao: build/<nome do build>)
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

if [ "${SKIP_TESTS:-0}" = 1 ]; then
    echo "[esteira] SKIP_TESTS=1: ROM versionada SEM testes (NAO_TESTADA.txt)"
    sh "$root/version_rom.sh" "$rom" --untested
    exit $?
fi

rom_abs=$(cd "$(dirname "$rom")" && pwd)/$base
elf_abs=${rom_abs%.gba}.elf

# O log chega pelo tee, que pode atrasar um pouco: espera a marca de fim de build.
log_args=""
if [ -n "${BUILD_LOG:-}" ]; then
    waited=0
    limit=$(( ${ESTEIRA_LOG_WAIT:-15} * 10 ))
    while [ $waited -lt $limit ] && ! grep -qF "$marker" "$BUILD_LOG" 2>/dev/null; do
        sleep 0.1
        waited=$(( waited + 1 ))
    done
    # a esteira roda em test/: os caminhos precisam ser absolutos
    log_args="--log $(cd "$(dirname "$BUILD_LOG")" && pwd)/$(basename "$BUILD_LOG")"
fi

out_base=${ESTEIRA_OUT_BASE:-$root/test/out}
mkdir -p "$out_base"
out="$(cd "$out_base" && pwd)/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out"

echo "[esteira] testando $base (esteira rapida, ~35 s)..."
# shellcheck disable=SC2086  # ESTEIRA_CMD e log_args sao listas de palavras de proposito
( cd "$root/test" && ${ESTEIRA_CMD:-python3 -m esteira} rapido --rom "$rom_abs" --elf "$elf_abs" \
    $log_args --out "$out" )
status=$?

if [ $status -eq 0 ]; then
    sh "$root/version_rom.sh" "$rom" "$out"
    exit $?
fi

# Reprovada: guarda a execucao e tira a ROM do caminho para o proximo make retestar em vez de
# dizer "Nothing to be done". O ELF sai junto (o ld precisa rodar de novo: o uso de memoria vem
# do log dele) e os objetos dos arquivos citados no log tambem (senao os avisos de compilacao
# nao reaparecem no reteste).
rm -rf "$roms_dir/ultima-falha"
mkdir -p "$roms_dir"
cp -r "$out" "$roms_dir/ultima-falha"
rm -f "$rom" "$elf_abs"
if [ -n "${BUILD_LOG:-}" ] && [ -f "$BUILD_LOG" ]; then
    name=${base#poke}
    name=${name%.gba}
    obj_dir=${ESTEIRA_OBJ_DIR:-build/$name}
    grep -oE '(^|[^A-Za-z0-9_./-])src/[A-Za-z0-9_./-]+\.c:' "$BUILD_LOG" | grep -oE 'src/[A-Za-z0-9_./-]+\.c' \
        | sort -u | while read -r src; do
        rm -f "$obj_dir/${src%.c}.o"
    done
fi
echo "[esteira] REPROVADA: ROM removida; relatorio em $roms_dir/ultima-falha/relatorio.html" >&2
exit 1
