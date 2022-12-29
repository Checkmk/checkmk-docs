#!/bin/bash
# I (SK) just wanted to quickly compare the size in bytes of our articles across the german and english version.
# This might(!) be an indicator, that the content is not in sync.
# Of course, this can also be an indicator, that one version still contains a ton of comments...
# This script can certainly be improved.
FILES="../de/*.asciidoc"
for f in $FILES;
do
	FILE=$(basename -- $f)
	SIZE1=$(stat -c%s ../de/$FILE)
	if [ -f ../en/$FILE ]; then
		SIZE2=$(stat -c%s ../en/$FILE)
		PERC=$(bc <<< "scale=4; ($SIZE1 - $SIZE2)/$SIZE1 * 100")
		if (( $(echo "$PERC > 15" | bc -l) ))
		then
			printf "$FILE: $PERC %%\n"
		fi
	else
		printf "\n$FILE only exists in german\n\n"
	fi

done
