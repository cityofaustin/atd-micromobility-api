"""
Dockless origin/destination trip data API

# try me
http://localhost:8000/v1/trips?xy=-97.75094341278084,30.276185988411257&flow=destination

TODO: check origin/destinon logic
TODO: tests
"""
import argparse
import json
import os

from rtree import index
from sanic import Sanic
from sanic import response
from sanic import exceptions
from sanic_cors import CORS, cross_origin
from shapely.geometry import Point, shape, asPolygon, mapping, polygon
from shapely.ops import cascaded_union


def spatial_index(features):
    # create spatial index of grid cell features
    # featues: geojson feature array
    # todo: use shapely STRtree !
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
        

def get_intersect_features(query_geom, grid, idx):
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
            ids.append(grid["FeatureIndex"][grid_id]["properties"]["id"])
            polys.append(poly)

    return ids, polys


def get_trip_features(intersect_ids, grid, flow, mode):
    '''
    Given a list of cell ids, extract trip count properties from the source grid data.
    '''    

    # aggregate trip count values from grid cells that match a source cell
    trip_features_lookup = {}

    total_trips = 0

    if flow == "origin":
        flow_key = "orig_cell_ids"
    elif flow == "destination":
        flow_key = "dest_cell_ids"

    for intersect_cell_id in intersect_ids:

        if flow_key in grid["FeatureIndex"][intersect_cell_id]["properties"]:
            
            for trip_cell_id in grid["FeatureIndex"][intersect_cell_id]["properties"][flow_key].keys():

                count = grid["FeatureIndex"][intersect_cell_id]["properties"][flow_key][trip_cell_id][mode]

                if trip_cell_id not in trip_features_lookup:
                    '''
                    Add a new entry in the trip features lookup, dropping all feature
                    properties except current count
                    '''
                    trip_features_lookup[trip_cell_id] = dict(grid["FeatureIndex"][trip_cell_id])
                    trip_features_lookup[trip_cell_id]["properties"] = { "current_count" : 0 }

                trip_features_lookup[trip_cell_id]["properties"]["current_count"] += count                

                total_trips += count
    
    # assemble matched features into geojson structure
    trip_features = {"type": "FeatureCollection" } 

    trip_features["features"] = [trip_features_lookup[cell_id] for cell_id in trip_features_lookup.keys()]

    return {"features": trip_features, "total_trips": total_trips}


dirname = os.path.dirname(__file__)
source = os.path.join(dirname, "data/grid.json")

with open(source, "r") as fin:
    data = json.loads(fin.read())   
    idx = spatial_index(data["FeatureIndex"][feature_id] for feature_id in data["FeatureIndex"].keys())
    app = Sanic(__name__)
    CORS(app)


@app.get("/v1/trips")
async def trip_handler(request):

    flow = parse_flow(request.args)

    mode = parse_mode(request.args)

    coords = parse_coordinates(request.args)
    
    query_geom = get_query_geom(coords)

    intersect_ids, intersect_polys = get_intersect_features(query_geom, data, idx)

    trip_features = get_trip_features(intersect_ids, data, flow, mode)

    intersect_poly = cascaded_union(intersect_polys)

    trip_features["intersect_feature"] = mapping(intersect_poly)

    return response.json(trip_features)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, workers=8)

