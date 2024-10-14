#!/bin/bash
# I (SK) just wanted to quickly compare the size in bytes of our articles across the german and english version.
# This might(!) be an indicator, that the content is not in sync.
# Of course, this can also be an indicator, that one version still contains a ton of comments...
# This script can certainly be improved.
GERMAN_FILES="../src/*/de/*.asciidoc"
for de in $GERMAN_FILES;
do
	en="${de/\/de\//\/en\/}"
	SIZE1=$(stat -c%s $de)
	if [ -f $en ]; then
                SIZE2=$(stat -c%s $en)
                PERC=$(bc <<< "scale=4; ($SIZE1 - $SIZE2)/$SIZE1 * 100")
                if (( $(echo "$PERC > 15" | bc -l) ))
                then
                        printf "$de: $PERC %%\n"
                fi
        else
                printf "\n$de only exists in german\n\n"
        fi



done

