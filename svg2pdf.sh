#!/bin/bash
if compgen -G "*.svg"
then
    for file in *.svg
    do
        pdf="`basename ${file} .svg`.pdf"
        inkscape -z -f "${file}" -e "$pdf"
    done
fi
