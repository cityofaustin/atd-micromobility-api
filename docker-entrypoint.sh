#!/usr/bin/env bash
echo "-- Entrypoint Executed (docker-entrypoint.sh)"
echo "--    DEPLOYMENT_MODE:   ${DEPLOYMENT_MODE}"
echo "--    DATABASE_URL:      ${DATABASE_URL}"
echo ""
echo "Downloading latest database"
curl -o /app/data/grid.json https://s3.amazonaws.com/dockless/data/grid.json
echo "Done"
exec "$@"
