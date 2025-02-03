"""
Functions related to neutron corrections for changes to atmospheric
pressure.

Functions in this module:

    pressure_correction_l_coeff
    pressure_correction_beta_coeff
    calc_mean_pressure
    calc_beta_coefficient
"""

import numpy as np
from neptoon.logging import get_logger

core_logger = get_logger()


def calc_pressure_correction_beta_coeff(
    current_pressure: float, reference_pressure: float, beta_coeff: float
):
    """
    Calculate a pressure correction factor accounting for changes in
    atmospheric pressure on neutron counting rates, using the beta
    coefficient method.

    Parameters
    ----------
    current_pressure : float
        Current atmospheric pressure at the site in pascals (Pa).
    reference_pressure : float
        Reference atmospheric pressure, typically a long-term average at
        the site, in pascals (Pa) to keep correction factors around 1
    beta_coeff : float
        Beta coefficient, akin to (1/l_coeff), and used as per Hawdon et
        al., 2014, typically around 0.007

    Returns
    -------
    c_factor
        Correction factor to multiply raw neutron count rates by, e.g.,
        1.04.
    """
    if beta_coeff >= 1:
        message = (
            "The beta_coeff is > 1 which suggests "
            "the incorrect function is being used. "
            "Use pressure_correction_l_coeff() instead"
        )

        core_logger.warning(message)
        raise ValueError(message)
    c_factor = np.exp(beta_coeff * (current_pressure - reference_pressure))
    return c_factor


def calc_mean_pressure(elevation: float):
    """
    Calculate mean atmospheric pressure based on elevation.

    Parameters
    ----------
    elevation : float
        Elevation above sea level in meters (m).

    Returns
    -------
    mean_pressure: float
        Mean atmospheric pressure at the given elevation in millibars (mb).
    """
    mean_pressure = (
        101325 * (1 - 2.25577 * (10**-5) * elevation) ** 5.25588
    ) / 100  # output in mb
    return mean_pressure


def calc_beta_coefficient(mean_pressure, latitude, elevation, cutoff_rigidity):
    """
    Calculate the beta coefficient necessary for the
    pressure_correction_beta_coeff() function. This coefficient
    represents the inverse of the mass attenuation length.

    Parameters
    ----------
    mean_pressure : float
        Mean atmospheric pressure in millibars (hPa).
    latitude : float
        Geographic latitude of the site in degrees.
    elevation : float
        Elevation of the site in meters (m).
    cutoff_rigidity : float
        Cutoff rigidity at the site in MeV.

    Returns
    -------
    beta_coeff: float
        Beta coefficient at site (usually ~0.007)
    """
    rho_rck = 2670
    mean_pressure = calc_mean_pressure(elevation)
    # variables
    z = (
        -0.00000448211 * mean_pressure**3
        + 0.0160234 * mean_pressure**2
        - 27.0977 * mean_pressure
        + 15666.1
    )

    # latitudeitude correction
    g_lat = 978032.7 * (
        1
        + 0.0053024 * (np.sin(np.radians(latitude)) ** 2)
        - 0.0000058 * (np.sin(np.radians(2 * latitude))) ** 2
    )

    # free air correction
    del_free_air = -0.3087691 * z

    # Bouguer correction
    del_boug = rho_rck * z * 0.00004193

    g_corr = (g_lat + del_free_air + del_boug) / 100000

    # final gravity and depth
    g = g_corr / 10
    x = mean_pressure / g

    # --- elevation scaling ---

    # parameters
    n_1 = 0.01231386
    alpha_1 = 0.0554611
    k_1 = 0.6012159
    b0 = 4.74235e-06
    b1 = -9.66624e-07
    b2 = 1.42783e-09
    b3 = -3.70478e-09
    b4 = 1.27739e-09
    b5 = 3.58814e-11
    b6 = -3.146e-15
    b7 = -3.5528e-13
    b8 = -4.29191e-14

    # calculations
    term1 = (
        n_1
        * (1 + np.exp(-alpha_1 * cutoff_rigidity**k_1)) ** -1
        * (x - mean_pressure)
    )
    term2 = (
        0.5
        * (b0 + b1 * cutoff_rigidity + b2 * cutoff_rigidity**2)
        * (x**2 - mean_pressure**2)
    )
    term3 = (
        0.3333
        * (b3 + b4 * cutoff_rigidity + b5 * cutoff_rigidity**2)
        * (x**3 - mean_pressure**3)
    )
    term4 = (
        0.25
        * (b6 + b7 * cutoff_rigidity + b8 * cutoff_rigidity**2)
        * (x**4 - mean_pressure**4)
    )

    beta_ceoff = abs((term1 + term2 + term3 + term4) / (mean_pressure - x))

    return beta_ceoff


def dunai_2020(
    current_pressure: float,
    reference_pressure: float,
    beta_coeff: float,
    inclination: float,
):
    """
    TODO
    !!!Speak with Martin about this method from corny!!!
    """
    pass
