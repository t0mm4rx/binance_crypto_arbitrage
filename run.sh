#!/bin/sh

# Kill previous instances.
killall python3

if [[ "$*" == *--kill* ]]
then
	echo "Killed."
else
	# Create a background job for every exchange.
	python3 run.py binance &
	python3 run.py bittrex &
	echo "Launched."
fi
