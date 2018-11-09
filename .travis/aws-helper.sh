#!/usr/bin/env bash
set -o errexit

# Set these up in Travis next time around
DOCKLESS_REPO="445025639710.dkr.ecr.us-east-1.amazonaws.com"
DOCKLESS_CLUSTER="dockless-austintexas-io"
DOCKLESS_SERVICE="dockless-api-service"

# Also set these dependencies in Travis (Settings > Environment Variables) be sure they are private
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="powwow_id_here"
export AWS_SECRET_ACCESS_KEY="papapaw_secret_here"


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
	docker tag $DOCKLESS_TAG $DOCKLESS_REPO/$DOCKLESS_TAG

  echo "Pushing: $DOCKLESS_REPO/$DOCKLESS_TAG"
  docker push $DOCKLESS_REPO/$DOCKLESS_TAG

  echo "Done"
}

function restart_all_tasks {
  echo "Rebooting all tasks in ECS"
  aws ecs update-service --force-new-deployment --cluster $DOCKLESS_CLUSTER --service $DOCKLESS_SERVICE
}
