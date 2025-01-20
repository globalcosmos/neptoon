"""
Functions related neutron corrections for changes to above ground
biomass.

Functions in this module:

    above_ground_biomass_correction_baatz2015
"""

from neptoon.logging import get_logger

core_logger = get_logger()


def above_ground_biomass_correction_baatz2015(above_ground_biomass):
    """
    Provides the correction value to account for changes in above ground
    biomass.

    Parameters
    ----------
    above_ground_biomass : float
        above ground biomass in kilograms per meter squared (kg/m^2)

    Returns
    -------
    c_factor: float
        Correction factor to be multiplied with neutron counts.
    """
    c_factor = 1 / (1 - (0.009 * above_ground_biomass))
    return c_factor


def above_ground_biomass_correction_morris2024(biomass_water_equivalent):
    """
    Provides the correction value to account for changes in above ground
    biomass.

    Parameters
    ----------
    biomass_water_equivalent : float
        biomass_water_equivalent in mm (kg/m^2). To convert above ground
        biomass to biomass water equivalent you can multiply by the
        water equivelant of cellulose (0.494)

    Returns
    -------
    c_factor: float
        Correction factor to be multiplied with neutron counts.
    """
    c_factor = 1 / (1 - (0.01 * biomass_water_equivalent))
    return c_factor
