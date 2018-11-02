#!/usr/bin/env bash
echo "-- Entrypoint Executed (docker-entrypoint.sh)"
echo "--    DEPLOYMENT_MODE:   ${DEPLOYMENT_MODE}"
echo "--    DATABASE_URL:      ${DATABASE_URL}"
echo ""
exec "$@"
