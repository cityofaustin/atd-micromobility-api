# dockless-api

The Dockless API provides an interface for retrieving anonymized and aggregated [dockless mobility](https://austintexas.gov/docklessmobility) trip data in the City of Austin. This API supplies data to our interactive [Dockless Mobility Explorer](https://dockless.austintexas.io).

## Table of Contents
* [Installation](#Installation)
* [API Reference](#api-reference)

## Installation

### About the "Database"

The source database for the API is a modified geojson file. TODO: add sample data and link to processing tools to generate source data.

### Option 1: Run w/ Docker (Suggested)

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

### Option 2: Run w/ Python 3

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

## API Reference

### Base URL + Versioning

Dockless API calls described below can be made via the following semantically versioned endpoint:

`https://dockless-api.austintexas.io/v1[/request]`

### Trips
----

Given an input geometry, the trips endpoint returns GeoJSON `FeatureCollection` which contains aggregated dockless trip counts. 

* **URL**

  /trips

* **Method:**

  `GET`
  
*  **URL Params**

    **Required:**

    `xy=[lng1],[lat1],[lng2],[lat2]...` a comma-separated string of latitude and longitude coordinates expressed as decimal degrees. The endpoint expects either one coordinate (a *point*: `[lng1],[lng2]`) or three or more coordinates (a *polygon*: `[lng1],[lat1],[lng2],[lat2],[lng3],[lat3]...`).
    *Note: Line references are not currently supported*

    **Optional:**

    `mode=all` filter identifying the mode transport. Either `bicycle`, `scooter`, or `all` (default).

    `flow=origin` indicate if the returned data reflects trips which originated in the requested geometry (`origin`) or terminated in the requested geometry (`destination`).

* **Success Response:**

    * **Code:** 200

    * **Content:** `{...}`

    - `features`:
        A GeoJSON (`type: FeatureCollection`), in which each feature is a hexagon grid cell with a single `trips` property whose value is the aggregated number of dockless trips which originated or terminated in the cell, given the requested `mode` and `flow`.

        TODO: define feature properties

    - `intersect_feature`
        A GeoJSON (`type: Polygon`) representing the union of the hexagon grid cells which intersect with the requested input geometry.

  - `total_trips`:
        The total number of trips associated with the returned features.
        


