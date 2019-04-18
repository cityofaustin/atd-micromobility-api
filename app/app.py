"""
Dockless origin/destination trip data API
# try me
http://localhost:8000/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination&mode=all
"""
import argparse
from datetime import datetime
import json
import os
import urllib.request

import pytz
import requests
from rtree import index
from sanic import Sanic
from sanic import response
from sanic import exceptions
from sanic_cors import CORS, cross_origin
from shapely.geometry import Point, shape, asPolygon, mapping, polygon
from shapely.ops import cascaded_union


def spatial_index(features):
    # create spatial index of census tract features
    # features: geojson feature array
    idx = index.Index()
    for pos, feature in enumerate(features):
        idx.insert(pos, shape(feature["geometry"]).bounds)

    return idx


def parse_flow(args):
    if not args.get("flow"):
        return "origin"

    elif args.get("flow").lower() == "origin":
        return "origin"

    elif args.get("flow").lower() == "destination":
        return "destination"

    else:
        raise exceptions.ServerError(
            "Unsupported flow specified. Must be either `origin` (default) or `destination`.",
            status_code=500,
        )


def parse_mode(args):
    if not args.get("mode"):
        return "all"
    elif args.get("mode").lower() == "all":
        return "all"
    elif args.get("mode").lower() == "scooter":
        return "scooter"
    elif args.get("mode").lower() == "bicycle":
        return "bicycle"
    else:
        raise exceptions.ServerError(
            "Unsupported mode specified. Must be either `scooter`, `bicycle`, or `all` (default).",
            status_code=500,
        )


def to_local_string(timestamp):

    if not timestamp:
        return None

    try:
        timestamp = int(float(timestamp)) / 1000

    except ValueError:
        raise exceptions.ServerError(
            f"{date_param} must be a number representing Unix time in milliseconds.",
            status_code=500,
        )

    # for god knows why utcfromtimestamp returns a naive timestamp.
    # so we have to append `.replace(tzinfo=pytz.utc)` to make it tz aware
    dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)

    # and now we can represent the time in local time
    local = dt.astimezone(tz)

    # we lop off the tz info from the timestamp because we're going
    # to pass socrata a "local" naive timestamp (YYYY-MM-DDTHH:MM:SS)
    return local.isoformat()[0:19]


def parse_coordinates(args):
    if not args.get("xy"):
        raise exceptions.ServerError("XY parameter is requried.", status_code=500)

    elements = args.get("xy").split(",")

    try:
        elements = [float(elem) for elem in elements]
    except ValueError:
        raise exceptions.ServerError(
            "Unable to handle xy. Verify that xy is a comma-separated string of numbers.",
            status_code=500,
        )

    return [tuple(elements[x : x + 2]) for x in range(0, len(elements), 2)]


def get_query_geom(coords):
    if len(coords) == 1:
        return Point(coords)
    elif len(coords) > 2:
        return asPolygon(coords)
    else:
        raise exceptions.ServerError(
            "Insufficient xy coordinates provided. A LinearRing must have at least 3 coordinate tuples.",
            status_code=500,
        )


def get_intersect_features(query_geom, polygons, idx, id_property="GEOID10"):
    # get the census tracts that intersect with the request geometry
    # see: https://stackoverflow.com/questions/14697442/faster-way-of-polygon-intersection-with-shapely
    ids = []
    polys = []

    if isinstance(query_geom, polygon.PolygonAdapter):
        coords = query_geom.exterior.coords
    else:
        coords = query_geom.coords

    # reduce intersection feature set with rtree (this tests polygon bbox intersection)
    for intersect_pos in idx.intersection(query_geom.bounds):

        poly_id = list(polygons.keys())[intersect_pos]
        poly = shape(polygons[poly_id]["geometry"])

        # check if poly actually interesects with request geom
        if query_geom.intersects(poly):
            ids.append(polygons[poly_id]["properties"][id_property])
            polys.append(poly)

    return ids, polys


def get_flow_keys(flow):
    """
    Bit of harcoding to map the flow to the corresponding dataset property
    """
    if flow == "origin":
        flow_key_init = "census_geoid_start"
        flow_key_end = "cenus_geoid_end"
    elif flow == "destination":
        flow_key_init = "cenus_geoid_end"
        flow_key_end = "census_geoid_start"
    else:
        # this should never happen because we validate the flow param when parsing
        # the request
        raise exceptions.ServerError(
            "Unsupported flow specified. Must be either `origin` (default) or `destination`.",
            status_code=500,
        )

    return [flow_key_init, flow_key_end]


def get_where_clause(flow_key_init, flow_key_end, intersect_id_string, **params):
    """
    Compose a WHERE statement for Socrata SoQL query
    """

    # select matching tract ids by flow
    id_filter = f"{flow_key_init} IN ({intersect_id_string}) AND {flow_key_init} NOT IN ('OUT_OF_BOUNDS') AND {flow_key_end} NOT IN ('OUT_OF_BOUNDS')"

    # exclude trips that don't meet our minimum criteria to be considered valid
    trip_filter = " AND trip_distance * 0.000621371 >= 0.1 AND trip_distance * 0.000621371 < 500 AND trip_duration < 86400"

    where_clause = id_filter + trip_filter

    mode = params.get("mode")

    if mode == "bicycle" or mode == "scooter":
        # if the request does not explicity define a mode it is left out of the query
        # resulting in all records being selected regardless of mode
        where_clause += f" AND vehicle_type='{mode}'"

    if params.get("start_time"):
        where_clause += " AND start_time >= '{}'".format(params.get("start_time"))

    if params.get("end_time"):
        where_clause += " AND end_time <= '{}'".format(params.get("end_time"))

    return where_clause


def get_trips(intersect_ids, flow_keys, **params):
    """
    Given a list of census tract ids, extract trip count properties from the source polygon data.
    """

    # this flow O/D stuff can get confusing, so let's name these list elements
    flow_key_init = flow_keys[0]
    flow_key_end = flow_keys[1]

    # generate a string of single-quoted ids (as if for a SQL `IN ()` statement)
    intersect_id_string = ", ".join([f"'{id_}'" for id_ in intersect_ids])

    where_clause = get_where_clause(
        flow_key_init, flow_key_end, intersect_id_string, **params
    )

    query = f"SELECT count(*) AS trip_count, {flow_key_end} WHERE {where_clause} GROUP BY {flow_key_end} LIMIT 10000000"

    params = {"$query": query}

    res = requests.get(TRIPS_URL, params, timeout=90)

    res.raise_for_status()

    return res.json()


def build_geojson(polygons, trips, flow_key_start):
    """
    Combine trip counts with their corresponding geojson feature, returning a geojson
    object with counts assigned to `trips` property
    """
    geojson = {"type": "FeatureCollection", "features": []}

    for tract in trips:
        tract_id = tract.get(flow_key_start)
        feature = polygons.get(tract_id)

        count = int(tract.get("trip_count"))

        count_as_height = (
            count / 5
        )  # each 5 trips will equate to 1 meter of height on the map

        feature["properties"]["trips"] = count
        feature["properties"]["count_as_height"] = count_as_height
        feature["properties"]["tract_id"] = int(tract_id)
        feature["properties"]["trips"] = count
        geojson["features"].append(feature)

    return geojson


def get_total_trips(trips):
    return sum([int(trip["trip_count"]) for trip in trips])


dirname = os.path.dirname(__file__)
source = os.path.join(dirname, "data/census_tracts_2010_simplified_20pct_indexed.json")
tz = pytz.timezone("US/Central")

with open(source, "r") as fin:

    TRIPS_URL = "https://data.austintexas.gov/resource/7d8e-dm7r.json"

    census_tracts = json.loads(fin.read())
    idx = spatial_index(census_tracts[feature_id] for feature_id in census_tracts.keys())
    app = Sanic(__name__)
    CORS(app)


@app.get("/trips", version=1)
async def trip_handler(request):
    flow = parse_flow(request.args)

    flow_keys = get_flow_keys(flow)

    mode = parse_mode(request.args)

    params = {
        "start_time": to_local_string(request.args.get("start_time")),
        "end_time": to_local_string(request.args.get("end_time")),
        "mode": mode,
    }

    coords = parse_coordinates(request.args)

    query_geom = get_query_geom(coords)

    intersect_ids, intersect_polys = get_intersect_features(query_geom, census_tracts, idx)

    trips = get_trips(intersect_ids, flow_keys, **params)

    response_data = {}

    response_data["features"] = build_geojson(census_tracts, trips, flow_keys[1])

    response_data["total_trips"] = get_total_trips(trips)

    intersect_poly = cascaded_union(intersect_polys)

    response_data["intersect_feature"] = mapping(intersect_poly)

    return response.json(response_data)


@app.route("/reload", version=1)
async def index(request):
    urllib.request.urlretrieve(
        os.getenv("DATABASE_URL"), "/app/data/hex500_indexed.json"
    )
    return response.text("Reloaded")


@app.route("/", version=1)
async def index(request):
    return response.text("Hello World")


@app.exception(exceptions.NotFound)
async def ignore_404s(request, exception):
    return response.text("Page not found: {}".format(request.url))


#
# TODO: does this break the app deployment? Handy for local deve but seem to remember
# TODO: a good reason for removing it
#
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
