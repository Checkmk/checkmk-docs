#!/bin/bash

# imagemagick is needed for testing images and icons
if ! command -v convert >/dev/null 2>&1 || ! command -v identify >/dev/null 2>&1; then
    echo "Commands \"convert\" or \"identify\" not found. Seems, that imagemagick is not installed"
    exit 2
fi

# These are the defaults used in this script
SIZE=20
CONVERT=false


usage() {
    cat <<EOF
icon_size.sh -i FILE [-c]

Checks an icon for the correct height. Currently we do use $SIZE px as
a default for all icons to be consistent with the text. Optionally it is
possible to directly convert the icon into the correct height.

Options:

    -i FILE  Check the given input file. The path may be provided as
             absolute or relative path
    -c       Do convert the file into the correct height in case its too big
    -h       Show this help
EOF
}


while getopts hci: opt; do
    case "$opt" in
        c)
            CONVERT=true
            ;;
        i)
            FILE=$OPTARG
            ;;
        h)
            usage
            ;;
        *)
            echo "There is no such option. You should read the help!"
            exit 1
            ;;
    esac
done

if ! [ -e "$FILE" ]; then
    echo "Dude - this only works if you give me a valid image to check!"
    echo "Cannot find $FILE"
    exit 2
fi

ICON_SIZE=$(identify -verbose -format "%h" "$FILE")

if [ "$ICON_SIZE" -gt "$SIZE" ]; then
    echo "This icon is too big! height: $ICON_SIZE px"
    if [ "$CONVERT" = true ]; then
        echo "Will change the size to $SIZE"
        convert "$FILE" -resize x"$SIZE" "$FILE"
        exit 0
    fi
    exit 1
elif [ "$ICON_SIZE" -lt "$SIZE" ]; then
    echo "This icon is to small! height $ICON_SIZE px"
    echo "You should update to a better resolution!"
    exit 1
else
    echo "this icon has the perfect height: $ICON_SIZE px"
    echo "Nothing to do here..."
fi
