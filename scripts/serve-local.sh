#!/usr/bin/env bash

BASE_CONTAINER_TAG="cityofaustin/dockless-api:base"

if [ "$CLEANUP" == "on" ]; then
  echo "Stopping all containers"
  docker kill $(docker ps -q)
  echo "Removing all dockless containers"
  docker rm $(docker ps -a -q)
  echo "Removing all dockless images"
  docker rmi $(docker image ls | awk '{print $1}' | grep dockless)
fi

if [ "$REBUILD" == "on" ]; then
    echo "Re-building Dockless API Docker Image"
    docker build --no-cache -f Dockerfile.base -t $BASE_CONTAINER_TAG .
    echo "Re-building service"
    docker-compose -f docker-compose.local.yml up --build
else
    echo "Building Dockless API Docker Image"
    docker build -f Dockerfile.base -t $BASE_CONTAINER_TAG .
    echo "Building Service"
    docker-compose -f docker-compose.local.yml up
fi
