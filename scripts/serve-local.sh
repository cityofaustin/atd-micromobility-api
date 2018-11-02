#!/usr/bin/env bash

set -o errexit

if [ "$REBUILD" == "on" ]; then
    echo "Re-building Dockerless API Docker Image"
    docker build --no-cache -f Dockerfile.base -t cityofaustin/dockerless-api .
    echo "Re-building service"
    docker-compose -f docker-compose.local.yml up --build
else
    echo "Building Dockerless API Docker Image"
    docker build -f Dockerfile.base -t cityofaustin/dockerless-api .
    echo "Building Service"
    docker-compose -f docker-compose.local.yml up
fi
