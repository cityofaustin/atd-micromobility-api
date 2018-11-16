#
# Development Dockless Container
#

FROM cityofaustin/dockless-api:base

ENV DEPLOYMENT_MODE "PRODUCTION"

ENV PYTHONUNBUFFERED=1
ENV WEB_CONCURRENCY=4

ARG HOST
ENV HOST ${HOST:-"0.0.0.0"}

ARG PORT
ENV PORT ${PORT:-80}
EXPOSE $PORT

COPY "$PWD/docker-entrypoint.sh" /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD [ "gunicorn", "app:app", "--worker-class", "sanic.worker.GunicornWorker",  "--pythonpath", "/app/" ]
