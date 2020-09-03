# atd-micromobility-api

The Micromobility API provides an interface for retrieving anonymized and aggregated [dockless mobility](https://austintexas.gov/docklessmobility) trip data in the City of Austin. This API supplies data to our interactive [Dockless Mobility Explorer](https://dockless.austintexas.io).

## Table of Contents
* [Installation](#Installation)
* [API Reference](#api-reference)

## Installation

### About the "Database"

The source database for the API is our [Dockless Vehicle Trips](https://data.austintexas.gov/Transportation-and-Mobility/Dockless-Vehicle-Trips/7d8e-dm7r) dataset.

### Option 1: Run w/ Docker (Suggested)

1.  Clone repo and `cd` into it.
    `git clone https://github.com/cityofaustin/atd-micromobility-api.git`

2. Create a virtual environment and install requirements:

```
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

3.  Start the docker server (in the background on port 80)

`python app.py`

4.  Make a request:

```shell
curl http://localhost:5000/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination
```

## API Reference

[See here](reference.md)


## Deployment

Any code in the `master` or any PRs made against it will be deployed to the staging environment in a lambda function. The production branch will be deployed to its own environment, it does not deploy PRs made against production.

