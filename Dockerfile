


FROM python:3.6

#  Set the working directory
WORKDIR /app

#  Copy package requirements
COPY requirements.txt /app

RUN apt-get update
RUN apt-get install dialog apt-utils -y

# Install libspatialindex
# See: https://github.com/libspatialindex/libspatialindex/wiki/1.-Getting-Started
RUN apt-get install -y curl \
  g++ \
  make
RUN curl -L http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.gz | tar xz
RUN cd spatialindex-src-1.8.5 && ./configure \
&& make \
&& make install \
&& ldconfig

#  Update python3-pip
RUN python -m pip install pip --upgrade
RUN python -m pip install wheel

#  Install python packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

CMD [ "python", "app.py" ]
