import pytest

import _setpath
from app.app import *


def test_get_request_valid():
    params = {"xy": "-97.7509434127,30.27618598841"}
    request, response = app.test_client.get("/v1/trips", params=params)
    assert response.status == 200


def test_get_query_geom_point():
    assert isinstance(get_query_geom([(125.6, 10.1)]), Point)


def test_get_query_geom_polygon():
    assert isinstance(
        get_query_geom([(125.6, 10.1), (125.6, 10.1), (125.6, 10.1), (125.6, 10.1)]),
        polygon.PolygonAdapter,
    )


def test_parse_flow():
    assert parse_flow({"flow": "origin"}) == "origin"
    assert parse_flow({"flow": None}) == "origin"
    assert parse_flow({"flow": "destination"}) == "destination"

    with pytest.raises(exceptions.ServerError):
        parse_flow({"flow": "pizza"})


def test_parse_mode():
    assert parse_mode({"mode": "scooter"}) == "scooter"
    assert parse_mode({"mode": "all"}) == "total"
    assert parse_mode({"mode": None}) == "total"
    assert parse_mode({"mode": "bicycle"}) == "bicycle"

    with pytest.raises(exceptions.ServerError):
        parse_mode({"mode": "pizza"})
