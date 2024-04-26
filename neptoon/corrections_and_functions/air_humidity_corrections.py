"""
Functions related neutron corrections for changes to air humidity 

Inside:

    humidity_correction_rosolem2013
    calc_absolute_humidity
    calc_vapour_pressure_from_dewpoint_temp
"""

import numpy as np
from neptoon.data_management.logging import get_logger

core_logger = get_logger()


def humidity_correction_rosolem2013(
    absolute_humidity, reference_absolute_humidity
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


def calc_absolute_humidity(vapour_pressure, temperature):
    """
    Calculate absolute humidity using air temperature and vapour
    pressure.

    Parameters
    ----------
    vapour_pressure : float
        Vapour presure in pascals (Pa)
    temperature : float
        Air temperature in Celsius (C)

    Returns
    -------
    absolute_humidity: float
        Absolute humidity in grams per cubic meter (g/m^3)
    """
    absolute_humidity = vapour_pressure / (461.5 * (temperature + 273.15))
    return absolute_humidity


def calc_vapour_pressure_from_dewpoint_temp(dewpoint_temp):
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
        Vapour pressure in kilopascals (kPa).

    Example
    -------
    >>> calc_vapour_pressure_from_dewpoint_temp(12)
    1.40
    """
    vapour_pressure = np.exp(
        (0.0707 * dewpoint_temp - 0.49299) / (1 + 0.00421 * dewpoint_temp)
    )
    return vapour_pressure
