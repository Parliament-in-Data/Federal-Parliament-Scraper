#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <original path> <session>"
    exit 1
fi

for f in $(find "$1/build/sessions/$2" -type f -name '*.json' -printf '%P\n'); do
    # https://stackoverflow.com/questions/31930041/using-jq-or-alternative-command-line-tools-to-compare-json-files
    comparison=$(jq --argfile a "$1/build/sessions/$2/$f" --argfile b "build/sessions/$2/$f" -n 'def post_recurse(f): def r: (f | select(. != null) | r), .; r; def post_recurse: post_recurse(.[]?); ($a | (post_recurse | arrays) |= sort) as $a | ($b | (post_recurse | arrays) |= sort) as $b | $a == $b')
    if [ "$comparison" = "false" ]; then
        cat "$1/build/sessions/$2/$f" | grep '"title": null' > /dev/null
        if test $? -eq 1; then
            cat build/sessions/$2/$f | grep '"title": null' > /dev/null
            if test $? -eq 0; then
                echo $f has a mismatch
            fi
        fi
    fi
done
