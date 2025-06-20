"""
This module contains functions related to calibration steps

"""

import numpy as np
import pandas as pd
from typing import Literal
from pathlib import Path
from neptoon.logging import get_logger


core_logger = get_logger()


# TODO: should this go into the Schroen2017 class? How?
def _load_footprint_lookup():
    """
    Load the Footprint lookup table into cache
    """

    this_path = Path(__file__).absolute().parent.parent

    _footprint_lookup = np.loadtxt(
        this_path / "assets" / "footprint_radius.csv"
    )

    return _footprint_lookup


class Schroen2017:

    _footprint_lookup = _load_footprint_lookup()

    @staticmethod
    def horizontal_weighting(
        distance=1,
        volumetric_soil_moisture: float = 0.1,
        abs_air_humidity: float = 5.0,
        normalize: bool = False,
    ):
        """
        W_r is the radial weighting function
        for point measurements taken in the footprint of the sensor.

        Parameters
        ----------
        distance : float or array or pandas.Series
            Rescaled distance from sensor in meters (m).
            Referred to as r in Schroen et al., (2017).
            See: Schroen2017.radius_rescale()
        volumetric_soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in m^3/m^3.
            Referred to as y in Schroen et al., (2017)
        abs_air_humidity : float
            Absolute air humidity from 0.1 to 0.50 in g/m^3.
            Referred to as x in Schroen et al., (2017)
        normalze : bool
            Normalize the weights relative to the sum of weights

        Returns
        -------
        weight: float
            The weighting to apply to the sample.

        """

        # Simplify notation
        r = distance
        x = abs_air_humidity
        y = volumetric_soil_moisture

        # Parameters
        a00 = 8735
        a01 = 22.689
        a02 = 11720
        a03 = 0.00978
        a04 = 9306
        a05 = 0.003632
        a10 = 2.7925e-002
        a11 = 6.6577
        a12 = 0.028544
        a13 = 0.002455
        a14 = 6.851e-005
        a15 = 12.2755
        a20 = 247970
        a21 = 23.289
        a22 = 374655
        a23 = 0.00191
        a24 = 258552
        a30 = 5.4818e-002
        a31 = 21.032
        a32 = 0.6373
        a33 = 0.0791
        a34 = 5.425e-004
        b00 = 39006
        b01 = 15002337
        b02 = 2009.24
        b03 = 0.01181
        b04 = 3.146
        b05 = 16.7417
        b06 = 3727
        b10 = 6.031e-005
        b11 = 98.5
        b12 = 0.0013826
        b20 = 11747
        b21 = 55.033
        b22 = 4521
        b23 = 0.01998
        b24 = 0.00604
        b25 = 3347.4
        b26 = 0.00475
        b30 = 1.543e-002
        b31 = 13.29
        b32 = 1.807e-002
        b33 = 0.0011
        b34 = 8.81e-005
        b35 = 0.0405
        b36 = 26.74

        # Parameter functions
        A0 = (
            a00 * (1 + a03 * x) * np.exp(-a01 * y)
            + a02 * (1 + a05 * x)
            - a04 * y
        )
        A1 = ((-a10 + a14 * x) * np.exp(-a11 * y / (1 + a15 * y)) + a12) * (
            1 + x * a13
        )
        A2 = a20 * (1 + a23 * x) * np.exp(-a21 * y) + a22 - a24 * y
        A3 = a30 * np.exp(-a31 * y) + a32 - a33 * y + a34 * x
        B0 = (
            (b00 - b01 / (b02 * y + x - 0.13)) * (b03 - y) * np.exp(-b04 * y)
            - b05 * x * y
            + b06
        )
        B1 = b10 * (x + b11) + b12 * y
        B2 = (
            b20 * (1 - b26 * x) * np.exp(-b21 * y * (1 - x * b24))
            + b22
            - b25 * y
        ) * (2 + x * b23)
        B3 = (
            (-b30 + b34 * x) * np.exp(-b31 * y / (1 + b35 * x + b36 * y)) + b32
        ) * (2 + x * b33)

        # Scalar or vector calculation
        if np.isscalar(r):
            # Using scalars
            if r <= 1:
                w = (A0 * (np.exp(-A1 * r)) + A2 * np.exp(-A3 * r)) * (
                    1 - np.exp(-3.7 * r)
                )
            elif (r > 1) & (r < 50):
                w = A0 * (np.exp(-A1 * r)) + A2 * np.exp(-A3 * r)
            elif r >= 50:
                w = B0 * (np.exp(-B1 * r)) + B2 * np.exp(-B3 * r)
            return w
        else:
            # Using vectors
            W = pd.DataFrame(dtype=float)
            W["r"] = r
            W["w"] = 0.0
            W.loc[W.r <= 1, "w"] = (
                A0 * (np.exp(-A1 * W.loc[W.r <= 1, "r"]))
                + A2 * np.exp(-A3 * W.loc[W.r <= 1, "r"])
            ) * (1 - np.exp(-3.7 * W.loc[W.r <= 1, "r"]))
            W.loc[W.r > 1, "w"] = A0 * (
                np.exp(-A1 * W.loc[W.r > 1, "r"])
            ) + A2 * np.exp(-A3 * W.loc[W.r > 1, "r"])
            W.loc[W.r >= 50, "w"] = B0 * (
                np.exp(-B1 * W.loc[W.r >= 50, "r"])
            ) + B2 * np.exp(-B3 * W.loc[W.r >= 50, "r"])

            if normalize:
                # Normalize weights by the sum of weights
                W.w /= W.w.sum()

            return W.w.values

    W_r = horizontal_weighting

    @staticmethod
    def horizontal_weighting_approx(distance=1, normalize: bool = False):
        """
        W_r_approx is an approximation of the radial weighting function
        for point measurements taken in the footprint of the sensor.

        Parameters
        ----------
        distance : float or array or pandas.Series
            Rescaled distance from sensor in meters (m).
            Referred to as r in Schroen et al., (2017).
            See: Schroen2017.radius_rescale()
        normalize : bool
            Normalize the weights relative to the sum of weights

        Returns
        -------
        weight: float
            The weighting to apply to the sample.

        """

        # Simplify notation
        r = distance

        # Parameters
        p0 = 30.0
        p1 = 0.625
        p2 = 0.01
        p3 = 1.0
        p4 = 3.7

        w = (p0 * np.exp(-p1 * r) + np.exp(-p2 * r)) * (p3 - np.exp(-p4 * r))

        # Scalar or vector calculation
        if np.isscalar(r):
            # Using scalars
            return w
        else:
            # Using vectors
            W = pd.DataFrame()
            W["r"] = r
            W["w"] = w

            if normalize:
                # Normalize weights by the sum of weights
                W.w /= W.w.sum()

            return W.w.values

    W_r_approx = horizontal_weighting_approx

    @staticmethod
    def calculate_measurement_depth(
        distance, bulk_density, volumetric_soil_moisture
    ):
        """
        Calculates the depth of sensor measurement (taken as the
        depth from which 86% of neutrons originate)

        Parameters
        ----------
        distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        bulk_density : float
            Dry soil bulk density of the soil (g/cm^3)
        volumetric_soil_moisture : float
            Volumetric soil moisture from 0.02 to 0.50 in cubic centimeter per
            cubic centimeter (m^3/m^3)

        Returns
        -------
        D86: float
            The depth of the sensor measurement in centimeters (cm)
        """

        D86 = (
            1
            / bulk_density
            * (
                8.321
                + 0.14249
                * (0.96655 + np.exp(-0.01 * distance))
                * (20 + volumetric_soil_moisture)
                / (0.0429 + volumetric_soil_moisture)
            )
        )
        return D86

    # D86 = calculate_measurement_depth

    @staticmethod
    def vertical_weighting(
        depth,
        distance: float = 1.0,
        bulk_density: float = 1.6,
        volumetric_soil_moisture: float = 0.1,
    ):
        """
        Wd Weighting function to be applied on samples to calculate
        weighted impact of soil samples based on depth.

        Parameters
        ----------
        depth : float
            Depth of sample in centimeters (cm)
        distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        bulk_density : float
            Dry soil bulk density in grams per cubic centimeter (g/cm^3)
        volumetric_soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in cubic centimeter per
            cubic centimeter (cm^3/cm^3)

        Returns
        -------
        weight: float
            The weight to give the sample.
        """
        D86 = Schroen2017.calculate_measurement_depth(
            distance=distance,
            bulk_density=bulk_density,
            volumetric_soil_moisture=volumetric_soil_moisture,
        )

        w = np.exp(-2 * depth / D86)
        return w

    W_d = vertical_weighting

    @staticmethod
    def rescale_distance(
        distance_from_sensor,
        atmospheric_pressure=1013.25,
        height_veg=0,
        volumetric_soil_moisture=0.1,
    ):
        """
        Rescales the distance to account for influences from atmospheric
        pressure, vegetation and antecedant soil moisture.

        Parameters
        ----------
        distance_from_sensor : float
            Distance from the sensor in meters (m)
        pressure : float
            Pressure at the site in hectopascals (hPa)
        height_veg : float
            Height of vegetation during calibration period in meters (m)
        volumetric_soil_moisture : float
            Volumetric soil moisture from 0.02 to 0.50 in cubic
            centimeters per cubic centimeters (cm^3/cm^3)

        Returns
        -------
        rescaled_radius: float
            The adjusted radius to use in future calculations.
        """
        F_p = 0.4922 / (0.86 - np.exp(-atmospheric_pressure / 1013.25))
        F_veg = 1 - 0.17 * (1 - np.exp(-0.41 * height_veg)) * (
            1 + np.exp(-9.25 * volumetric_soil_moisture)
        )
        rescaled_distance = distance_from_sensor * F_p * F_veg
        return rescaled_distance

    @staticmethod
    def calculate_footprint_radius(
        volumetric_soil_moisture: float = 0.1,
        abs_air_humidity: float = 5.0,
        atmospheric_pressure: float | None = None,
    ):
        """
        Parameters
        ----------
        volumetric_soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in m^3/m^3.
            Referred to as y in Schroen et al., (2017)
        abs_air_humidity : float
            Absolute air humidity from 0.1 to 0.50 in g/m^3.
            Referred to as x in Schroen et al., (2017)
        atmospheric_pressure : float
            Atmospheric pressure in hectopascals

        Returns
        -------
        R86: float
            Footprint radius in meters
        """
        # Filter input and extend over limits
        if np.isnan(volumetric_soil_moisture) or np.isnan(abs_air_humidity):
            return np.nan
        if volumetric_soil_moisture < 0.01:
            volumetric_soil_moisture = 0.01
        if volumetric_soil_moisture > 0.49:
            volumetric_soil_moisture = 0.49
        if abs_air_humidity > 29:
            abs_air_humidity = 29

        lookup_table = Schroen2017._footprint_lookup
        R86 = lookup_table[int(round(100 * volumetric_soil_moisture))][
            int(round(abs_air_humidity))
        ]

        if atmospheric_pressure is not None:
            R86 = Schroen2017.rescale_distance(
                distance_from_sensor=R86,
                volumetric_soil_moisture=volumetric_soil_moisture,
                atmospheric_pressure=atmospheric_pressure,
            )

        return R86

    def calculate_footprint_volume(
        D86_1m, soil_moisture, bulk_density, footprint_radius
    ):
        """
        Footprint volume in m³

        Parameters
        ----------
        D86_1m : float or array-like
            Measurement depth at 1 m distance
        soil_moisture : float or array-like
            Soil moisture in m³/m³
        bulk_density : float or array-like
            Bulk density
        footprint_radius : float or array-like
            Footprint radius in meters

        Returns
        -------
        V86
            Footprint volume in m³
        """

        D86_at_R86 = Schroen2017.D86(
            soil_moisture, bulk_density, footprint_radius
        )

        average_depth = (D86_1m + D86_at_R86) * 0.01 * 0.47
        # 0.44 (dry) ..0.5 (wet) is roughly the average D over radii
        footprint_area = 3.141 * footprint_radius**2

        return average_depth * footprint_area / 1000
