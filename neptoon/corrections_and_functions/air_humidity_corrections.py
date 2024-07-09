"""
Functions related neutron corrections for changes to air humidity

Functions in this module:

    humidity_correction_rosolem2013
    saturation_vapour_pressure
    calc_absolute_humidity
    calc_vapour_pressure_from_dewpoint_temp
    calc_relative_humidity_from_temperature

"""

import numpy as np
from neptoon.logging import get_logger

core_logger = get_logger()


def humidity_correction_rosolem2013(
    absolute_humidity: float, reference_absolute_humidity: float = 0
):
    """
    Calculate the correction factor for neutron counts based on the
    difference in absolute humidity between current and reference
    conditions.

    Parameters
    ----------
    absolute_humidity : float
        Current absolute humidity in grams per cubic meter (g/m^3).
    reference_absolute_humidity : float
        Reference absolute humidity in grams per cubic meter (g/m^3).

    Returns
    -------
    c_humidity: float
        Correction factor to be multiplied with neutron counts.
    """
    c_humidity = 1 + 0.0054 * (absolute_humidity - reference_absolute_humidity)
    return c_humidity


def calc_absolute_humidity(vapour_pressure: float, temperature: float):
    """
    Calculate absolute humidity using air temperature and vapour
    pressure.

    Parameters
    ----------
    vapour_pressure : float
        Vapour pressure in pascals (hPa)
    temperature : float
        Air temperature in Celsius (C)

    Returns
    -------
    absolute_humidity: float
        Absolute humidity in grams per cubic meter (g/m^3)
    """
    absolute_humidity = (
        (vapour_pressure * 100) / (461.5 * (temperature + 273.15))
    ) * 1000
    return absolute_humidity


def calc_saturation_vapour_pressure(temperature: float):
    """
    Calculate saturation vapour pressure (hPA) using average temperature
    Can be used to calculate actual vapour pressure (hPA) if using dew
    point temperature

    Parameters
    ----------
    temperature : float
        temperature (C)

    Returns
    -------
    float
        saturation vapour pressure (hPA)
    """
    return 6.112 * np.exp((17.67 * temperature) / (243.5 + temperature))


def calc_vapour_pressure_from_dewpoint_temp(dewpoint_temp: float):
    """
    Calculate vapour pressure from the dewpoint temperature,
    particularly useful when using ERA5-Land data.

    Parameters
    ----------
    dewpoint_temp : float
        Dewpoint temperature in degrees Celsius (C)

    Returns
    -------
    vapour_pressure: float
        Vapour pressure in hectopascals (hPa).

    Example
    -------
    >>> calc_vapour_pressure_from_dewpoint_temp(12)
    1.40
    """
    vapour_pressure = (
        np.exp(
            (0.0707 * dewpoint_temp - 0.49299) / (1 + 0.00421 * dewpoint_temp)
        )
    ) / 10
    return vapour_pressure


def calc_relative_humidity_from_dewpoint_temperature(
    temperature: float, dewpoint_temperature: float
):
    """
    Calculate relative humidity from temperature and dewpoint temperature

    Parameters
    ----------
    temperature : float
        Temperature in Celsius (C)
    dewpoint_temperature : float
        Dewpoint temperature in Celsius (C)

    Returns
    -------
    relative_humidity: float
        Relative humidity (%)
    """
    relative_humidity = 100 * np.exp(
        (17.625 * 243.04 * (dewpoint_temperature - temperature))
        / ((243.04 + temperature) * (243.04 + dewpoint_temperature))
    )
    return relative_humidity


def calc_actual_vapour_pressure(
    saturation_vapour_pressure: float, relative_humidity: float
):
    """
    Calculates actual vapour pressure

    Parameters
    ----------
    saturation_vapour_pressure : float
        Saturation Vapour Pressure (hPa)
    relative_humidity : float
        Relative Humdity (%)

    Returns
    -------
    actual vapour pressure: float
        The actual vapour pressure (hPa)
    """
    return saturation_vapour_pressure * (relative_humidity / 100)
