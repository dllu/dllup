#!/bin/bash
for file in *.svg
do
    pdf="`basename ${file} .svg`.pdf"
    if [ ! -f "$pdf" ]
    then
        inkscape -z -f "${file}" -e "$pdf"
    fi
done
