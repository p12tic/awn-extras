#!/bin/sh

# Mimics the behaviour of main.py, without the overhead of having to launch a
# Python process just to write to a named pipe.

# The location of the command pipe
COMMAND_PIPE="$HOME/.config/awn/applets/comics/commands"

# The name of the main script
COMMAND_EXECUTOR="`dirname $0`/main.py"

# The special command sent to this script to remove the command pipe and restart
CLEAN_COMMAND="clean"

# The number of seconds we wait for a write operation to go ghrough before
# cleaning and restarting
CLEAN_DELAY=3

# The command sent to terminate the application; we treat this as a special
# command, so that we do not spawn a new process when all we want to do is
# terminate the current (non-existing) process
EXIT_COMMAND="exit"

if [ "x$1" = "x$CLEAN_COMMAND" ]; then
	# The clean command is a special command to this script only
	rm "$COMMAND_PIPE"
	exit
fi

if [ -p "$COMMAND_PIPE" ]; then
	# If the command pipe exists, we write to it, but not using the builtin
	# echo, since we want to be able to kill it
	/bin/echo $@ >>"$COMMAND_PIPE" &
	pid=$!
	
	# Give echo five seconds to write to the pipe; if it does not complete,
	# we assume nobody is listening and we clean up and restart
	sleep $CLEAN_DELAY
	if kill -9 $pid; then
		rm "$COMMAND_PIPE"
		$0 "$*"
	fi
elif [ ! "x$1" = "x$EXIT_COMMAND" ]; then
	# Otherwise we start the application in the background
	python "$COMMAND_EXECUTOR" "$*" &
fi

