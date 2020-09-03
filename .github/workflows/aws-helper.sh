#!/usr/bin/env bash

#
# By default we are going to assume the current branch will be deployed to the dev server
#
export ATD_AWS_LAMBDA_ENV="staging";

#
# If this is production or staging, assign the variable accordingly.
#
if [[ "${BRANCH_NAME}" == "production" ]]; then
    export ATD_AWS_LAMBDA_ENV="production";
else
    export ATD_AWS_LAMBDA_ENV="staging";
fi;

function deploy_aws_lambda {
    echo "Updating AWS Lambda Environment: ${ATD_AWS_LAMBDA_ENV}";
    zappa update $ATD_AWS_LAMBDA_ENV;
}