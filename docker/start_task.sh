#!/bin/bash

container_type=$1

set -m
# echo $HOME
echo $container_type

# $HOME/AirSim/build_release/output/bin/RtspStream

# echo "Sleeping 10 seconds..."
# sleep 10

# cat nohup.out

# echo "-- Motion client"
# python3 $HOME/AirSim/PythonClient/multirotor/sweep_motion.py 34 7 3 50 15 &

if [ $container_type == "stream" ]; then
	echo "<<< Streamer Container >>>"
	$HOME/AirSim/build_release/output/bin/RtspStream
elif [ $container_type == "action" ]; then
	echo "<<< Action Container >>>"
	python3 $HOME/AirSim/PythonClient/multirotor/sweep_motion.py 34 7 3 50 15
else
	echo "<<< Unknown Type! Exiting... >>>"
fi
