#!/bin/bash

docker rmi -f ubnt/live_deb10:fcd_d10
set -e
docker build -f Dockerfile -t ubnt/live_deb10:fcd_d10 .

