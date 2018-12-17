#!/usr/bin/env bash
set -o errexit

echo "Logging in to AWS Docker Repository"
$(aws ecr get-login --no-include-email --region $AWS_DEFAULT_REGION)

function build_dockless {
	DOCKLESS_IMAGE=$1
	DOCKLESS_MODE=":latest"
	DOCKLESS_FILE="Dockerfile"

	# First, determine if we are building the base image.
	if [ "${DOCKLESS_IMAGE}" = "base" ]; then
		DOCKLESS_MODE=":base"
		DOCKLESS_FILE="${DOCKLESS_FILE}.base"
	fi;

	# Then, generate the tag string to use in the AWS private registry
	DOCKLESS_TAG="cityofaustin/dockless-api${DOCKLESS_MODE}"
	echo "Final Image Name (tag): ${DOCKLESS_TAG}"

	# Build
  echo "Building ${DOCKLESS_FILE} with tag ${DOCKLESS_TAG}"
	docker build -f $DOCKLESS_FILE -t $DOCKLESS_TAG \
				--build-arg DATABASE_URL=$DOCKLESS_DATABASE_URL \
				.

	# Tag
  echo "Tagging ${DOCKLESS_TAG} with tag ${DOCKLESS_TAG}"
	docker tag $DOCKLESS_TAG $DOCKLESS_REPO/$DOCKLESS_TAG

	# Push
  echo "Pushing: $DOCKLESS_REPO/$DOCKLESS_TAG"
  docker push $DOCKLESS_REPO/$DOCKLESS_TAG

  echo "Done"
}

#
# Restarts all tasks (containers) in ECS, this will cause them to relaunch
# with the latest version of the code and/or latest version of the database.
#
function restart_all_tasks {
  echo "Updating ECS Cluster"
  aws ecs update-service --force-new-deployment --cluster $DOCKLESS_CLUSTER --service $DOCKLESS_SERVICE

  echo "Stopping any old remaining containers (autoscaling should spawn new tasks)"
  for DOCKLESS_TASK_ID in $(aws ecs list-tasks --cluster $DOCKLESS_CLUSTER | jq -r ".taskArns[] | split(\"/\") | .[1]");
  do
	  aws ecs stop-task --cluster $DOCKLESS_CLUSTER --task $DOCKLESS_TASK_ID
  done
}
