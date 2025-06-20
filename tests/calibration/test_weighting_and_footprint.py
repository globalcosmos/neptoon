import pandas as pd
import numpy as np
from neptoon.corrections import Schroen2017


def test_horizontal_weighting(r=1, sm=0.1, h=5):
    w = Schroen2017.horizontal_weighting(
        distance=r,
        volumetric_soil_moisture=sm,
        abs_air_humidity=h,
    )
    assert int(w) == 203702

    w = Schroen2017.horizontal_weighting(
        distance=pd.Series([1, 10, 100]),
        volumetric_soil_moisture=sm,
        abs_air_humidity=h,
    )
    assert len(w) == 3


def test_horizontal_weighting_approx(r=1):
    w = Schroen2017.horizontal_weighting_approx(
        distance=r,
    )
    assert int(w) == 16
    w = Schroen2017.horizontal_weighting_approx(
        distance=pd.Series([1, 10, 100]),
    )
    assert len(w) == 3
    # return w


def test_calculate_measurement_depth(
    distance=1, bulk_density=1.6, soil_moisture=0.1
):
    w = Schroen2017.calculate_measurement_depth(
        distance, bulk_density, soil_moisture
    )
    assert int(w) == 29
    # return w


def test_vertical_weighting(
    depth=10, distance=1, bulk_density=1.6, soil_moisture=0.1
):
    w = Schroen2017.vertical_weighting(
        depth, distance, bulk_density, soil_moisture
    )
    assert int(10 * w) == 5
    w = Schroen2017.vertical_weighting(depth=np.array([5, 10, 50]))
    assert len(w) == 3
    # return w


def test_rescale_distance():
    w = Schroen2017.rescale_distance(
        distance_from_sensor=1, atmospheric_pressure=800
    )
    assert int(10 * w) == 12
    w = Schroen2017.rescale_distance(
        distance_from_sensor=np.array([5, 10, 50])
    )
    assert len(w) == 3


def test_calculate_footprint_radius(soil_moisture=0.1, air_humidity=5.0):
    w = Schroen2017.calculate_footprint_radius(soil_moisture, air_humidity)
    assert int(w) == 209
    # return w
