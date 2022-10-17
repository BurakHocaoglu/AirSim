#!/bin/bash
DOCKER_IMAGE_NAME=$1

# get the base directory name of the unreal binary's shell script
# we'll mount this volume while running docker container
UNREAL_BINARY_PATH=$(dirname $(readlink -f $2))
UNREAL_BINARY_SHELL_ABSPATH=$(readlink -f $2)

# This is to determine Docker version for the command
version_less_than_equal_to() { test "$(printf '%s\n' "$@" | sort -V | head -n 1)" = "$1"; }

REQ_DOCKER_VERSION=19.03
docker_version=$(docker -v | cut -d ' ' -f3 | sed 's/,$//')

if version_less_than_equal_to $REQ_DOCKER_VERSION $docker_version; then
    # Use the normal docker command
    DOCKER_CMD="docker run --gpus all"
else
    # Use nvidia-docker
    DOCKER_CMD="nvidia-docker run --runtime=nvidia"
fi

# this block is for running X apps in docker
XAUTH=/tmp/.docker.xauth
if [ ! -f $XAUTH ]
then
    xauth_list=$(xauth nlist :0 | sed -e 's/^..../ffff/')
    if [ ! -z "$xauth_list" ]
    then
        echo $xauth_list | xauth -f $XAUTH nmerge -
    else
        touch $XAUTH
    fi
    chmod a+r $XAUTH
fi

# this are the first (maximum) four arguments which the user specifies:
# ex: ./run_airsim_image.sh /PATH/TO/UnrealBinary/UnrealBinary.sh -windowed -ResX=1080 -ResY=720
# we save them in a variable right now:
UNREAL_BINARY_COMMAND="$UNREAL_BINARY_SHELL_ABSPATH $3 $4 $5"

# now let's check if user specified  an "-- headless" parameter in the end
# we'll set SDL_VIDEODRIVER_VALUE to '' if it wasn't specified, 'offscreen' if it was
SDL_VIDEODRIVER_VALUE='';
while [ -n "$1" ]; do
    case "$1" in
    --)
        shift 
        break
        ;; 
    esac
    shift
done
 
for param in $@; do
    case "$param" in
    headless) SDL_VIDEODRIVER_VALUE='offscreen' ;;
    esac
done


# AirSim game container
$DOCKER_CMD --name airsim-game -dit \
    -v $(pwd)/settings.json:/home/ue4/Documents/AirSim/settings.json \
    -v $UNREAL_BINARY_PATH:$UNREAL_BINARY_PATH \
    --net=host \
    --rm \
    $DOCKER_IMAGE_NAME \
    /bin/bash -c "$UNREAL_BINARY_SHELL_ABSPATH -RenderOffscreen"


# RTSP streaming container
$DOCKER_CMD --name airsim-rtsp-stream -dit \
    -v $(pwd)/settings.json:/home/ue4/Documents/AirSim/settings.json \
    -v $(pwd)/rtsp_opts_2.json:/home/ue4/Documents/AirSim/rtsp_opts.json \
    -e SDL_VIDEODRIVER='' \
    -e SDL_HINT_CUDA_DEVICE='0' \
    --net=host \
    --env="DISPLAY=$DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    -env="XAUTHORITY=$XAUTH" \
    --volume="$XAUTH:$XAUTH" \
    --rm \
    $DOCKER_IMAGE_NAME \
    /bin/bash -c './start_task.sh stream'


sleep 10


# AirSim client action container
$DOCKER_CMD --name airsim-client -dit \
    -v $(pwd)/settings.json:/home/airsim_user/Documents/AirSim/settings.json \
    -v $(pwd)/rtsp_opts_2.json:/home/ue4/Documents/AirSim/rtsp_opts.json \
    -v $(pwd)/sweep_motion_g.py:/home/ue4/AirSim/PythonClient/multirotor/sweep_motion.py \
    -e SDL_VIDEODRIVER='' \
    -e SDL_HINT_CUDA_DEVICE='0' \
    --net=host \
    --env="DISPLAY=$DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    -env="XAUTHORITY=$XAUTH" \
    --volume="$XAUTH:$XAUTH" \
    --rm \
    $DOCKER_IMAGE_NAME \
    /bin/bash -c './start_task.sh action'

echo "Ready!"