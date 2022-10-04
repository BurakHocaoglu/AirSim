#!/bin/sh

set -m

echo $HOME
echo $(pwd)
echo $(ls $HOME/AirSim/build_release/output/bin)

nohup sh -c $HOME/AirSim/build_release/output/bin/RtspStream &

echo "Sleeping 10 seconds..."
sleep 10

# echo "-- Motion client"
# python3 $HOME/AirSim/PythonClient/multirotor/sweep_motion.py 34 7 3 50 15 &