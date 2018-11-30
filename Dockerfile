#
# Dockless-API Container
#

FROM cityofaustin/dockless-api:base

ARG DEPLOYMENT_MODE
ENV DEPLOYMENT_MODE ${DEPLOYMENT_MODE:-"PRODUCTION"}

ARG DATABASE_URL
ENV DATABASE_URL ${DATABASE_URL:-""}

ARG DATABASE_PATH
ENV DATABASE_PATH ${DATABASE_PATH:-"/app/data/grid.json"}

ARG PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED ${PYTHONUNBUFFERED:-1}

ARG WEB_CONCURRENCY
ENV WEB_CONCURRENCY ${WEB_CONCURRENCY:-4}

ARG HOST
ENV HOST ${HOST:-"0.0.0.0"}

ARG PORT
ENV PORT ${PORT:-80}
EXPOSE $PORT

# We copy the source code one more time, since we are relaunching.
COPY "$PWD/app" /app
COPY "$PWD/docker-entrypoint.sh" /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD [ "gunicorn", "app:app", "--worker-class", "sanic.worker.GunicornWorker",  "--pythonpath", "/app/" ]
