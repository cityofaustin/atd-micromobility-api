# dockless-api

A dockless mobility data API built with Python/Sanic

## Installation

### About the "Database"

The source database for the API is a modified geojson file. TODO: add sample data and link to processing tools to generate source data.

### Option 1: Run w/ Python 3

1.  Clone repo and `cd` into it.

2.  Install python requirements:

```python
pip install -r requirements.txt
```

3.  Install [libspatialindex](http://libspatialindex.github.io/)

4.  Copy `grid.json` source data to `../dockless-api/app/data`

5.  Start the server:

```python
python app/app.py
```

6.  Make a request:

```shell
curl http://localhost:8000/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination
```

### Option 2: Run w/ Docker

1.  Install [docker](https://www.docker.com/) and start the engine:
    `systemctl start docker`

2.  Clone repo and `cd` into it.
    `git clone https://github.com/cityofaustin/dockless-api.git`

3.  Copy `grid.json` source data to `../dockless-api/app/data`

4.  Start the docker server (in the background on port 80)

`./scripts/serve-local.sh`

5.  Make a request:

```shell
curl http://localhost:80/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination
```
