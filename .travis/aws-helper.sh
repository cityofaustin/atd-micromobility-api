#!/usr/bin/env bash

echo "Logging in to AWS Docker Repository"
$(aws ecr get-login --no-include-email --region us-east-1)

function build_dockless {
	DOCKLESS_IMAGE=$1

	DOCKLESS_MODE=":latest"
	DOCKLESS_FILE="Dockerfile"

	if [ "${DOCKLESS_IMAGE}" = "base" ]; then
		DOCKLESS_MODE=":base"
		DOCKLESS_FILE="${DOCKLESS_FILE}.base"
	fi;

	DOCKLESS_TAG="cityofaustin/dockless-api${DOCKLESS_MODE}"

  echo "Building ${DOCKLESS_FILE} with tag ${DOCKLESS_TAG}"
	docker build -f $DOCKLESS_FILE -t $DOCKLESS_TAG .

  echo "Tagging ${DOCKLESS_TAG} with tag ${DOCKLESS_TAG}"
	docker tag $DOCKLESS_TAG 445025639710.dkr.ecr.us-east-1.amazonaws.com/$DOCKLESS_TAG

  echo "Pushing: 445025639710.dkr.ecr.us-east-1.amazonaws.com/$DOCKLESS_TAG"
  docker push 445025639710.dkr.ecr.us-east-1.amazonaws.com/$DOCKLESS_TAG

  echo "Done"
}

function restart_all_tasks {
  echo "Rebooting all tasks in ECS"
  aws ecs update-service --force-new-deployment --cluster $DOCKLESS_CLUSTER --service $DOCKLESS_SERVICE
}
