#!/usr/bin/env bash


## reference
# https://gist.github.com/luaraneda/c12d5d111d6ccac00319d1948b2fc955

set -e
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 [cpp flags] [dts file]"
    exit -1
fi

DTS_CPP_FLAGS="-nostdinc -Iinclude -undef -D__DTS__ -x assembler-with-cpp"

while [[ $# > 1 ]]; do
    DTS_CPP_FLAGS="$DTS_CPP_FLAGS $1"
    shift
done
shift $((OPTIND - 1))

DTS_FILE=$1
DTS_RAW_NAME=${DTS_FILE/%.dts}

echo "DTS_CPP_FLAGS = $DTS_CPP_FLAGS"
echo "DTS_FILE= $DTS_FILE"
echo "DTS_RAW_NAME = $DTS_RAW_NAME"

CLANG_BIN=$(which clang)

if [[ $? != 0 ]]; then
    cpp -Wp,-MD,${DTS_RAW_NAME}.dts.dep.tmp ${DTS_CPP_FLAGS} -o ${DTS_RAW_NAME}.dts.tmp ${DTS_FILE}
else
    clang -E -Wp,-MMD,{DTS_RAW_NAME}.dts.dep.tmp ${DTS_CPP_FLAGS} -o ${DTS_RAW_NAME}.dts.tmp ${DTS_FILE}
fi

dtc -O dtb -o ${DTS_RAW_NAME}.dtb -b 0 -d ${DTS_RAW_NAME}.dts.dep.tmp ${DTS_RAW_NAME}.dts.tmp

rm ${DTS_RAW_NAME}.dts.dep.tmp
rm ${DTS_RAW_NAME}.dts.tmp

echo "Get dtb at: ${DTS_RAW_NAME}.dtb"
# fdtdump ${DTS_RAW_NAME}.dtb
