#
# Production Dockless Container
#

FROM cityofaustin/dockless-api:base

ENV DEPLOYMENT_MODE "PRODUCTION"

ENTRYPOINT ["/app/docker-entrypoint.sh"]

ENV PYTHONUNBUFFERED=1
ENV WEB_CONCURRENCY=4
ENV PORT ${PORT:-80}
EXPOSE $PORT

CMD [ "gunicorn", "app:app", "-b 0.0.0.0:80", "--worker-class", "sanic.worker.GunicornWorker",  "--pythonpath", "/app/" ]
