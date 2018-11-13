#!/usr/bin/env bash

echo "starting..."

set -o errexit

TAG='dockless-api:local'
echo "building docker image..."
docker build --tag "$TAG" .
echo "running docker image..."

docker run \
   -d \
   -it \
   --rm \
   -p 80:8000 \
   -v `pwd`:/app \
   atddocker/dockless-api \
   python app/app.py
