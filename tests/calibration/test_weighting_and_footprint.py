# %%
import pandas as pd
import numpy as np
from neptoon.corrections import Schroen2017


# %%
def test_horizontal_weighting(r=1, sm=0.1, h=5):
    w = Schroen2017.horizontal_weighting(
        distance=r, soil_moisture=sm, air_humidity=h
    )
    assert int(w) == 203702

    w = Schroen2017.horizontal_weighting(
        distance=pd.Series([1, 10, 100]), soil_moisture=sm, air_humidity=h
    )
    assert len(w) == 3
    # return w


# %%
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


# %%
def test_calculate_measurement_depth(
    distance=1, bulk_density=1.6, soil_moisture=0.1
):
    w = Schroen2017.calculate_measurement_depth(
        distance, bulk_density, soil_moisture
    )
    assert int(w) == 29
    # return w


# %%
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


# %%
def test_rescale_distance(distance=1, pressure=1013):
    w = Schroen2017.rescale_distance(distance, pressure=800)
    assert int(10 * w) == 12
    w = Schroen2017.rescale_distance(distance=np.array([5, 10, 50]))
    assert len(w) == 3
    # return w


# %%
def test_calculate_footprint_radius(soil_moisture=0.1, air_humidity=5.0):
    w = Schroen2017.calculate_footprint_radius(soil_moisture, air_humidity)
    assert int(w) == 209
    # return w


# %%
# a = np.array([203702.76807141,  11638.09428262,   5124.294245  ])
# b = np.array([16.62640866,  0.96275104,  0.36787944])
# print(a/a.sum(), b/b.sum())
# %%
# Examples
# test_horizontal_weighting(pd.Series([1,10,100]))

# data = pd.DataFrame()
# data["r"] = np.arange(300)
# data["w1"] = test_horizontal_weighting(data["r"],0.1,5.0)
# data["w2"] = test_horizontal_weighting(data["r"],0.3,5.0)
# data["w3"] = test_horizontal_weighting(data["r"],0.1,15.0)
# data["w1"].plot(logy=True)
# data["w2"].plot()
# data["w3"].plot()
