#!/bin/bash

docker rmi -f ubnt/esxbuild:fcd
set -e
docker build -f Dockerfile -t ubnt/esxbuild:fcd .

