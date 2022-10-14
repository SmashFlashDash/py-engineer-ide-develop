#!/bin/sh
SCRIPT_LOCATION="$0"
PYTHON=$(command -v python3)
DIRNAME=$(command -v dirname)
DIRNAME=$($DIRNAME $SCRIPT_LOCATION)
LAUNCHER="${DIRNAME}/launcher.py"
cd $DIRNAME
$PYTHON $LAUNCHER
