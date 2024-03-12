#!/bin/bash

RED='\033[0;31m'
NC='\033[0m'

function main {
    parse_parameters $*

    encode_files
}

function usage {
    echo "$0 {ARGUMENTS} path"
    echo "Usage: "
    echo "    -h | --help        : show this prompt"
    echo "    -e | --encoder     : specify an encoder (amd, nvidia, software). Defaults to software if not provided *not required*"
    echo "    -c | --codec       : codec to encode to (x264 or x265)"
    echo "    --file-extension   : extension of file to encode. Defaults to every file if not provided *not required*"
}

function parse_parameters {
    # while [[ $# -gt 0 ]]; do
    #     case $1 in
    #         -h|--help)
    #             usage
    #             exit 0
    #             ;;
    #         -e|--encoder)
    #             ENCODER=${2,,}
    #             shift
    #             shift
    #             ;;
    #         -c|--codec)
    #             CODEC=${2,,}
    #             shift
    #             shift
    #             ;;
    #         --file-extension)
    #             FILE_EXTENSION=$2
    #             shift
    #             shift
    #             ;;
    #         *)
    #             FILES_PATH="$1"
    #             shift
    #             shift
    #             ;;
    #     esac
    # done


    ARGS=$(getopt -o abg:d: --long alpha,beta,gamma:,delta: -- "$@")
    if [[ $? -ne 0 ]]; then
        exit 1;
    fi

    eval set -- "$ARGS"
    while [ : ]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -e|--encoder)
                ENCODER=${2,,}
                shift
                shift
                ;;
            -c|--codec)
                CODEC=${2,,}
                shift
                shift
                ;;
            --file-extension)
                FILE_EXTENSION=$2
                shift
                shift
                ;;
            *)
                FILES_PATH="$1"
                shift
                shift
                ;;
        esac
    done

    if [ -z $CODEC ]; then
        echo -e "${RED} ERROR - Please provide a codec${NC}"
        exit 1
    fi

    if [ -z "$FILES_PATH" ]; then
        echo -e "${RED} ERROR - Please provide a path${NC}"
        exit 1
    fi

    if [[ $CODEC != "x264" && $CODEC != "x265" ]]; then
        echo -e "${RED} ERROR - $CODEC is not supported. Please provide x264 or x265 as a codec${NC}"
        exit 1
    fi

    if [ -z $ENCODER ]; then
        ENCODER="software"
    fi

    if [[ $ENCODER != "amd" && $ENCODER != "nvidia" && $ENCODER != "software" ]]; then
        echo -e "${RED} ERROR - $ENCODER is not supported. Please provide nvidia, amd or software as an encoder${NC}"
        exit 1
    fi

    # TODO check prerequisites for encoder
}

function encode_files {
    mkdir ./tmp

    for file in $(find "$FILES_PATH" -name "*$FILE_EXTENSION"); do
        echo "Encoding $file in $CODEC"
        if [ $ENCODER = "software" ]; then
            ffmpeg -i "$file" -c:v lib$CODEC "./tmp/$(basename "$file")"
        elif [[ $ENCODER = "nvidia" && $CODEC = "x265" ]]; then
            ffmpeg -hwaccel auto -i "$file" -c:v hevc_nvenc -x265-params crf=25 -c:a copy "./tmp/$(basename "$file")"
        elif [[ $ENCODER = "nvidia" && $CODEC = "x264" ]]; then
            ffmpeg -hwaccel auto -i "$file" -c:v h264_nvenc -c:a copy "./tmp/$(basename "$file")"
        elif [[ $ENCODER = "amd" && $CODEC = "x265" ]]; then
            ffmpeg -hwaccel auto -i "$file" -c:v hevc_vaapi -x265-params crf=25 -c:a copy "./tmp/$(basename $file)"
        elif [[ $ENCODER = "amd" && $CODEC = "x264" ]]; then
            ffmpeg -hwaccel auto -i "$file" -c:v h264_vaapi -c:a copy "./tmp/$(basename "$file")"
        fi
        [ ! $? -eq 0 ] && rm "./tmp/$(basename "$file")" && break

        echo "Replacing $file"
        mv "./tmp/$(basename "$file")" "$file"
    done

    rm -rf ./tmp
}

main $*
