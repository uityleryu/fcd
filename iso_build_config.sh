#!/bin/bash

set -x
set -e

#if [ -d esx-all ]; then
#	cd esx-all; git fetch --all; git clean -fdx; git checkout master;  git reset --hard origin/master; cd -
#else
#	git clone -b ${BRANCH} --reference-if-able /var/cache/git/github.com/ubiquiti/esx-all.git git@github.com:ubiquiti/esx-all.git
#fi


ENV_DIR=$(pwd)

eval `ssh-agent -s`
ssh-add

run_docker() {
docker run --privileged -it --rm \
    -v "$(dirname $SSH_AUTH_SOCK):/home/ubnt/.ssh-agent:rw" \
    -v "$ENV_DIR:/build:rw" \
    -e "SSH_AUTH_SOCK=/home/ubnt/.ssh-agent/$(basename $SSH_AUTH_SOCK)" \
    ubnt/live_deb10:fcd_d10 \
    "$@"
    echo $?
}

run_docker bash -c "
  cd /build; \
  lb clean --purge; \
  lb config noauto \
    --mode debian \
    --architectures i386 \
    --distribution buster \
    --debian-installer false \
    --archive-areas 'main contrib non-free' \
    --apt-indices false \
    --memtest none \
    '${@}'; \
  lb build
"

ssh-agent -k

