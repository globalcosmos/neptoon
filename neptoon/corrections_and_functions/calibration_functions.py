"""
This module contains functions related to calibration steps

"""

import numpy as np
from neptoon.logging import get_logger

core_logger = get_logger()


class Schroen2017CalibrationFunctions:

    @staticmethod
    def WrX(
        rescaled_distance: float,
        absolute_humidity: float,
        soil_moisture: float,
    ):
        """
        WrX Radial Weighting function for point measurements taken
        within 5m of sensor.

        Parameters
        ----------
        rescaled_distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        absolute_humidity : float
            Air Humidity from 0.1 to 0.50 in grams per cubic meter
            (g/m^3). Referred to as x in Schroen et al., (2017)
        soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in cubic centimeters per
            cubic centimeters (cm^3/cm^3). Referred to as y in Schroen
            et al., (2017)

        Returns
        -------
        weight: float
            The weighting to apply to the sample.
        """
        x00 = 3.7
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

        x0 = x00
        A0 = (
            a00 * (1 + a03 * absolute_humidity) * np.exp(-a01 * soil_moisture)
            + a02 * (1 + a05 * absolute_humidity)
            - a04 * soil_moisture
        )
        A1 = (
            (-a10 + a14 * absolute_humidity)
            * np.exp(-a11 * soil_moisture / (1 + a15 * soil_moisture))
            + a12
        ) * (1 + absolute_humidity * a13)
        A2 = (
            a20 * (1 + a23 * absolute_humidity) * np.exp(-a21 * soil_moisture)
            + a22
            - a24 * soil_moisture
        )
        A3 = (
            a30 * np.exp(-a31 * soil_moisture)
            + a32
            - a33 * soil_moisture
            + a34 * absolute_humidity
        )

        weight = (
            A0 * (np.exp(-A1 * rescaled_distance))
            + A2 * np.exp(-A3 * rescaled_distance)
        ) * (1 - np.exp(-x0 * rescaled_distance))
        return weight

    @staticmethod
    def WrA(
        rescaled_distance: float,
        absolute_humidity: float,
        soil_moisture: float,
    ):
        """
        WrA Radial Weighting function for point measurements taken
        within 50m of sensor.

        Parameters
        ----------
        rescaled_distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        absolute_humidity : float
            Air Humidity from 0.1 to 0.50 in grams per cubic meter
            (g/m^3). Referred to as x in Schroen et al., (2017)
        soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in cubic centimeters per
            cubic centimeters (cm^3/cm^3). Referred to as y in Schroen
            et al., (2017)

        Returns
        -------
        weight: float
            The weighting to apply to the sample.

        """

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

        A0 = (
            a00 * (1 + a03 * absolute_humidity) * np.exp(-a01 * soil_moisture)
            + a02 * (1 + a05 * absolute_humidity)
            - a04 * soil_moisture
        )
        A1 = (
            (-a10 + a14 * absolute_humidity)
            * np.exp(-a11 * soil_moisture / (1 + a15 * soil_moisture))
            + a12
        ) * (1 + absolute_humidity * a13)
        A2 = (
            a20 * (1 + a23 * absolute_humidity) * np.exp(-a21 * soil_moisture)
            + a22
            - a24 * soil_moisture
        )
        A3 = (
            a30 * np.exp(-a31 * soil_moisture)
            + a32
            - a33 * soil_moisture
            + a34 * absolute_humidity
        )

        weight = A0 * (np.exp(-A1 * rescaled_distance)) + A2 * np.exp(
            -A3 * rescaled_distance
        )
        return weight

    @staticmethod
    def WrB(
        rescaled_distance: float,
        absolute_humidity: float,
        soil_moisture: float,
    ):
        """
        WrB Radial Weighting function for point measurements taken over 50m of sensor

        Parameters
        ----------
        rescaled_distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        absolute_humidity : float
            Air Humidity from 0.1 to 0.50 in grams per cubic meter
            (g/m^3). Referred to as x in Schroen et al., (2017)
        soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in cubic centimeters per
            cubic centimeters (cm^3/cm^3). Referred to as y in Schroen
            et al., (2017)

        Returns
        -------
        weight: float
            The weighting to apply to the sample.

        """
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

        B0 = (
            (b00 - b01 / (b02 * soil_moisture + absolute_humidity - 0.13))
            * (b03 - soil_moisture)
            * np.exp(-b04 * soil_moisture)
            - b05 * absolute_humidity * soil_moisture
            + b06
        )
        B1 = b10 * (absolute_humidity + b11) + b12 * soil_moisture
        B2 = (
            b20
            * (1 - b26 * absolute_humidity)
            * np.exp(-b21 * soil_moisture * (1 - absolute_humidity * b24))
            + b22
            - b25 * soil_moisture
        ) * (2 + absolute_humidity * b23)
        B3 = (
            (-b30 + b34 * absolute_humidity)
            * np.exp(
                -b31
                * soil_moisture
                / (1 + b35 * absolute_humidity + b36 * soil_moisture)
            )
            + b32
        ) * (2 + absolute_humidity * b33)

        weight = B0 * (np.exp(-B1 * rescaled_distance)) + B2 * np.exp(
            -B3 * rescaled_distance
        )
        return weight

    @staticmethod
    def calculate_measurement_depth(
        rescaled_distance, bulk_density, soil_moisture
    ):
        """
        Calculates the depth of sensor measurement (taken as the
        depth from which 86% of neutrons originate)

        Parameters
        ----------
        rescaled_distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        bulk_density : float
            Dry soil bulk density of the soil (g/cm^3)
        soil_moisture : float
            Soil moisture from 0.02 to 0.50 in cubic centimeter per
            cubic centimeter (cm^3/cm^3)

        Returns
        -------
        d86: float
            The depth of the sensor measurement in centimeters (cm)
        """

        d86 = (
            1
            / bulk_density
            * (
                8.321
                + 0.14249
                * (0.96655 + np.exp(-0.01 * rescaled_distance))
                * (20 + soil_moisture)
                / (0.0429 + soil_moisture)
            )
        )
        return d86

    @staticmethod
    def vertical_weighting(
        depth, rescaled_distance, bulk_density, soil_moisture
    ):
        """
        Wd Weighting function to be applied on samples to calculate
        weighted impact of soil samples based on depth.

        Parameters
        ----------
        depth : float
            Depth of sample in centimeters (cm)
        rescaled_distance : float
            Rescaled distance from sensor in meters (m). Referred to as
            r in Schroen et al., (2017). See
            Schroen2017funcs.radius_rescale()
        bulk_density : float
            Dry soil bulk density in grams per cubic centimeter (g/cm^3)
        soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in cubic centimeter per
            cubic centimeter (cm^3/cm^3)

        Returns
        -------
        weight: float
            The weight to give the sample.
        """

        weight = np.exp(
            -2
            * depth
            / Schroen2017CalibrationFunctions.calculate_d86(
                rescaled_distance, bulk_density, soil_moisture
            )
        )
        return weight

    @staticmethod
    def radius_rescale(radius, pressure, height_veg, soil_moisture):
        """
        Rescales the radius to account for influences from atmospheric
        pressure, vegetation and antecedant soil moisture.

        Parameters
        ----------
        radius : float
            Radius from the sensor in meters (m)
        pressure : float
            Pressure at the site in hectopascals (hPa)
        height_veg : float
            Height of vegetation during calibration period in meters (m)
        soil_moisture : float
            Soil Moisture from 0.02 to 0.50 in cubic centimeters per
            cubic centimeters (cm^3/cm^3)

        Returns
        -------
        rescaled_radius: float
            The adjusted radius to use in future calculations.
        """
        Fp = 0.4922 / (0.86 - np.exp(-pressure / 1013.25))
        Fveg = 1 - 0.17 * (1 - np.exp(-0.41 * height_veg)) * (
            1 + np.exp(-9.25 * soil_moisture)
        )
        rescaled_radius = radius / Fp / Fveg
        return rescaled_radius
