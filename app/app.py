"""
Dockless origin/destination trip data API
# try me
http://localhost:8000/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination&mode=all

#TODO:
- build geosjon
- fetch records by grid cell (council district is placeholder)
- query params for dow, hour day, date
- drop start/end minute/second?
"""
import argparse
import json
import os
import urllib.request

import requests
from rtree import index
from sanic import Sanic
from sanic import response
from sanic import exceptions
from sanic_cors import CORS, cross_origin
from shapely.geometry import Point, shape, asPolygon, mapping, polygon
from shapely.ops import cascaded_union


def spatial_index(features):
    # create spatial index of grid cell features
    # features: geojson feature array
    idx = index.Index()
    for pos, feature in enumerate(features):
        idx.insert(pos, shape(feature["geometry"]).bounds)

    return idx


def parse_flow(args):
    if not args.get("flow") or args.get("flow") == "origin":
        return "origin"
    elif args.get("flow") == "destination":
        return "destination"
    else:
        raise exceptions.ServerError("Unsupported flow specified. Must be either origin (default) or destination.", status_code=500)


def parse_mode(args):
    if not args.get("mode") or args.get("mode") == "all":
        return "total"
    elif args.get("mode") == "scooter":
        return "scooter"
    elif args.get("mode") == "bicycle":
        return "bicycle"
    else:
        raise exceptions.ServerError("Unsupported mode specified. Must be either scooter, bicycle, or all (default).", status_code=500)


def parse_coordinates(args):
    if not args.get("xy"):
        raise exceptions.ServerError("XY parameter is requried.", status_code=500)

    elements = args.get("xy").split(",")

    try:
        elements = [float(elem) for elem in elements]
    except ValueError:
        raise exceptions.ServerError("Unable to handle xy. Verify that xy is a comma-separated string of numbers.", status_code=500)

    return [tuple(elements[x : x + 2]) for x in range(0, len(elements), 2)]


def get_query_geom(coords):
    if len(coords) == 1:
        return Point(coords)
    elif len(coords) > 2:
        return asPolygon(coords)
    else:
        raise exceptions.ServerError("Insufficient xy coordinates provided. A LinearRing must have at least 3 coordinate tuples.", status_code=500)


def get_intersect_features(query_geom, grid, idx, id_property="id"):
    # get the grid cells that intersect with the request geometry
    # see: https://stackoverflow.com/questions/14697442/faster-way-of-polygon-intersection-with-shapely
    ids = []
    polys = []

    if isinstance(query_geom, polygon.PolygonAdapter):
        coords = query_geom.exterior.coords
    else:
        coords = query_geom.coords

    # reduce intersection feature set with rtree (this tests polygon bbox intersection)
    for intersect_pos in idx.intersection(query_geom.bounds):

        grid_id = list(grid["FeatureIndex"].keys())[intersect_pos]
        poly = shape(grid["FeatureIndex"][grid_id]["geometry"])

        # check if poly actually interesects with request geom
        if query_geom.intersects(poly):
            # simulate id lookup
            from random import randint
            val = str(randint(1, 10))
            ids.append(val)

            # actual id lookup
            # ids.append(grid["FeatureIndex"][grid_id]["properties"][id_property])
            polys.append(poly)

    return ids, polys


def get_trip_data(intersect_ids, flow, mode):
    '''
    Given a list of cell ids, extract trip count properties from the source grid data.
    '''

    # aggregate trip count values from grid cells that match a source cell
    trip_features_lookup = {}

    total_trips = 0

    # flow == `destination` or not recognized 
    flow_key_init = "council_district_end"
    flow_key_end = "council_district_start"

    if flow == "origin":
        flow_key_init = "council_district_start"
        flow_key_end = "council_district_end"

    url =  "https://data.austintexas.gov/resource/pqaf-uftu.json"

    # generate a string of single-quoted ids (as if for a SQL `IN ()` statement)
    intersect_id_string = ', '.join([f"'{id_}'" for id_ in intersect_ids])

    query = f"select count(*) as trip_count, {flow_key_end} where {flow_key_init} in ({intersect_id_string}) group by {flow_key_end}"

    print(query)
    params = { "$query" : query }

    res = requests.get(url, params)

    res.raise_for_status()

    return res.json()


dirname = os.path.dirname(__file__)
source = os.path.join(dirname, "data/grid.json")

with open(source, "r") as fin:
    data = json.loads(fin.read())
    idx = spatial_index(data["FeatureIndex"][feature_id] for feature_id in data["FeatureIndex"].keys())
    app = Sanic(__name__)
    CORS(app)


@app.get("/trips", version=1)
async def trip_handler(request):
    print(request)
    flow = parse_flow(request.args)

    mode = parse_mode(request.args)

    coords = parse_coordinates(request.args)

    query_geom = get_query_geom(coords)

    intersect_ids, intersect_polys = get_intersect_features(query_geom, data, idx)

    trip_data = {}
    trip_data['features'] = get_trip_data(intersect_ids, flow, mode)

    intersect_poly = cascaded_union(intersect_polys)

    trip_data["intersect_feature"] = mapping(intersect_poly)

    return response.json(trip_data)

@app.route('/reload', version=1)
async def index(request):
    urllib.request.urlretrieve(os.getenv("DATABASE_URL"), "/app/data/council_districts_simplified.json")
    return response.text("Reloaded")

@app.route('/', version=1)
async def index(request):
    return response.text("Hello World")

@app.exception(exceptions.NotFound)
async def ignore_404s(request, exception):
    return response.text("Page not found: {}".format(request.url))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)