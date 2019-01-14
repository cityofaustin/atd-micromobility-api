## API Reference

### Base URL + Versioning

Dockless API calls described below can be made via the following semantically versioned endpoint:

`https://dockless-api.austintexas.io/v1[/request]`

### Trips
----

Given an input geometry, the trips endpoint returns a GeoJSON `FeatureCollection` which contains dockless trip counts aggregated to hexagon cells.

* **URL**

  /trips

* **Method:**

  `GET`
  
*  **URL Params**

    **Required:**

    `xy=[lng1],[lat1],[lng2],[lat2]...` a comma-separated string of latitude and longitude coordinates expressed as decimal degrees. The endpoint expects either one coordinate (a *point*: `[lng1],[lng2]`) or three or more coordinates (a *polygon*: `[lng1],[lat1],[lng2],[lat2],[lng3],[lat3]...`).
    *Note: Line references and multipart polygons are not currently supported*

    **Optional Trip Filters:**

    `mode=all` The mode of transport. Either `bicycle`, `scooter`, or `all` (default).

    `flow=origin` Indicates if trips originated in the input geometry (`origin`) or terminated in the input geometry (`destination`).

    `start_time` A unix timestamp in millseconds which will select for trips that began at or after the given timestamp.

    `end_time` A unix timestamp in millseconds which will select for trips that ended before the given timestamp.

* **Success Response:**

    * **Code:** 200

    * **Content:** `{...}`

    - `features`:
        A GeoJSON (`type: FeatureCollection`), in which each feature is a hexagon grid cell with a single `trips` property whose value is the aggregated number of dockless trips which originated or terminated in the cell, given the requested `mode` and `flow`.

    - `intersect_feature`
        A GeoJSON (`type: Polygon`) representing the union of the hexagon grid cells which intersect with the requested input geometry.

  - `total_trips`:
        The total number of trips associated with the returned features.
        
## License

This work belong to the City of Austin, and so it belongs to the people. The contents of this repository are in the public domain within the United States. Additionally, we waive copyright and related rights in the work worldwide through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
