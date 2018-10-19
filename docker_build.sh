#!/bin/bash

docker rmi -f ubnt/live-cd:fcd
set -e
docker build -f Dockerfile -t ubnt/live-cd:fcd .

