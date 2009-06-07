#!/bin/sh

# Mimics the behaviour of main.py, without the overhead of having to launch a
# Python process just to write to a named pipe.

COMMAND_PIPE="$HOME/.config/awn/applets/comics/commands"
CLEAN_COMMAND="clean"
EXIT_COMMAND="exit"

if [ "x$1" = "x$CLEAN_COMMAND" ]; then
	# The clean command is a special command to this script only
	rm "$COMMAND_PIPE"
	exit
fi

if [ -p "$COMMAND_PIPE" ]; then
	# If the command pipe exists, we write to it
	echo $@ >>"$COMMAND_PIPE"
elif [ ! "x$1" = "x$EXIT_COMMAND" ]; then
	# Otherwise we start the application in the background
	python main.py $@ &
fi

