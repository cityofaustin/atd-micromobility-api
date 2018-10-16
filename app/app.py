"""
Dockless origin/destination trip data API
"""
import argparse
import json
import os
import pdb

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
from shapely.geometry import Point, shape, asPolygon, mapping
from shapely.ops import cascaded_union

dirname = os.path.dirname(__file__)
source = os.path.join(dirname, "data/grid.json")

with open(source, "r") as fin:

    data = json.loads(fin.read())

    parser = reqparse.RequestParser()

    parser.add_argument(
        "xy",
        required=True,
        type=str,
        help="Coordinate string missing or unable to convert to decimal value. Must be formatted as comma-separated string in format x,y,x,y...",
    )
    
    parser.add_argument(
        "mode",
        type=str,
        choices=["origin", "destination"],
        help="Mode string must be one of (origin, destination)",
    )

    app = Flask(__name__)
    api = Api(app)


def parse_coordinates(xy_string):
    elements = xy_string.split(",")
    elements = [float(elem) for elem in elements]
    return [tuple(elements[x : x + 2]) for x in range(0, len(elements), 2)]


def get_intersect_features(query_geom, grid):
    ids = []
    polys = []

    for feature in grid["features"]:
        poly = shape(feature["geometry"])

        if query_geom.intersects(poly):
            ids.append(feature["properties"]["id"])
            polys.append(poly)

    return ids, polys


def get_trip_features(source_ids, grid, mode="origin"):
    # used to collect trip count values from grid cells that match a source cell
    trip_features_lookup = {}
    total_trips = 0

    if mode == "origin":
        key = "start_grid_ids"
    elif mode == "destination":
        key = "end_grid_ids"
    else:
        raise Exception("Invalid mode requested")

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


class Api(Resource):
    def get(self):
        args = parser.parse_args()

        if args.get("mode"):
            mode = args.mode
        else:
            mode = "origin"

        coords = parse_coordinates(args.xy)

        if len(coords) == 1:
            query_geom = Point(coords)
        else:
            query_geom = asPolygon(coords)

        intersect_ids, intersect_polys = get_intersect_features(query_geom, data)
        trip_features = get_trip_features(intersect_ids, data, mode=mode)
        intersect_poly = cascaded_union(intersect_polys)
        trip_features["intersect_feature"] = mapping(intersect_poly)

        return jsonify(trip_features)


api.add_resource(Api, "/api")

if __name__ == "__main__":
    app.run(debug=False)
