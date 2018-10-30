


FROM python:3.6

#  Set the working directory
WORKDIR /app

#  Copy package requirements
COPY requirements.txt /app

RUN apt-get update
RUN apt-get install dialog apt-utils -y

#  Update python3-pip
RUN python -m pip install pip --upgrade
RUN python -m pip install wheel

#  Install python packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

CMD [ "gunicorn", "app:app", "-b 0.0.0.0:5000", "--worker-class", "sanic.worker.GunicornWorker" ]

