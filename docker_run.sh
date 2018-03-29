#!/bin/bash

ENV_DIR=$(pwd)

#eval `ssh-agent -s`
#ssh-add

docker run --privileged -it --rm \
    -v "$(dirname $SSH_AUTH_SOCK):/home/ubnt/.ssh-agent:rw" \
    -v "$ENV_DIR:/build:rw" \
    -e "SSH_AUTH_SOCK=/home/ubnt/.ssh-agent/$(basename $SSH_AUTH_SOCK)" \
    ubnt/esxbuild:fcd \
    /bin/bash

#ssh-agent -k

