"""
Dockless origin/destination trip data API

# try me
http://localhost:8000/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination

"""
import argparse
import json
import os

from sanic import Sanic
from sanic import response
from sanic import exceptions
from sanic_cors import CORS, cross_origin
from shapely.geometry import Point, shape, asPolygon, mapping
from shapely.ops import cascaded_union

dirname = os.path.dirname(__file__)
source = os.path.join(dirname, "data/grid.json")

with open(source, "r") as fin:
    data = json.loads(fin.read())
    app = Sanic(__name__)
    CORS(app)



def parse_flow(args):
    if not args.get("flow") or args.get("flow") == "origin":
        return "origin"
    elif args.get("flow") == "destination":
        return "destination"
    else:
        raise exceptions.ServerError("Unsupported flow specified", status_code=500)


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
        

def get_intersect_features(query_geom, grid):
    ids = []
    polys = []

    for feature in grid["features"]:
        poly = shape(feature["geometry"])

        if query_geom.intersects(poly):
            ids.append(feature["properties"]["id"])
            polys.append(poly)

    return ids, polys


def get_trip_features(source_ids, grid, flow):
    # used to collect trip count values from grid cells that match a source cell
    trip_features_lookup = {}
    total_trips = 0

    if flow == "origin":
        key = "start_grid_ids"
    elif flow == "destination":
        key = "end_grid_ids"

    # check all grid cells to see if they have trips connected to any of the source ID cells
    for feature in grid["features"]:
        if key in feature["properties"]:
            for trip_grid_id in feature["properties"][key].keys():
                for grid_id in source_ids:

                    if trip_grid_id == grid_id:
                        feature_id = feature["properties"]["id"]
                        if feature_id not in trip_features_lookup:
                            # add feature to collection of matching features
                            feature["properties"]["current_count"] = 0
                            trip_features_lookup[feature_id] = feature

                        feature["properties"]["current_count"] += feature["properties"][
                            key
                        ][trip_grid_id]["count"]
                        # copy trip count to "total_trips"
                        total_trips += feature["properties"][key][trip_grid_id]["count"]

    # assemble matched features back into geojson structure
    trip_features = {"type": "FeatureCollection", "features": []}

    for grid_id in trip_features_lookup.keys():
        trip_features["features"].append(trip_features_lookup[grid_id])

    return {"features": trip_features, "total_trips": total_trips}


@app.get("/v1/trips")
async def trip_handler(request):

    flow = parse_flow(request.args)
    print("******************* {} **************".format(flow))

    coords = parse_coordinates(request.args)
    
    query_geom = get_query_geom(coords)

    intersect_ids, intersect_polys = get_intersect_features(query_geom, data)

    trip_features = get_trip_features(intersect_ids, data, flow)

    intersect_poly = cascaded_union(intersect_polys)

    trip_features["intersect_feature"] = mapping(intersect_poly)

    return response.json(trip_features)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

