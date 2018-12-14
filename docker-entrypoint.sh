#!/usr/bin/env bash
echo "-- Entrypoint Executed (docker-entrypoint.sh)"
echo "--    DEPLOYMENT_MODE:   ${DEPLOYMENT_MODE}"
echo "--    DATABASE_URL:      ${DATABASE_URL}"
echo "--    DATABASE_PATH:     ${DATABASE_PATH}"
echo "--    PYTHONUNBUFFERED:  ${PYTHONUNBUFFERED}"
echo "--    WEB_CONCURRENCY:   ${WEB_CONCURRENCY}"
echo "--    HOST:              ${HOST}"
echo "--    PORT:              ${PORT}"

echo ""

echo "Using the existing database: ${DATABASE_PATH}"

exec "$@"
