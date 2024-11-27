"""
Functions related neutron corrections for changes to incoming neutron
intensity.

TODO: finish off the McJannetDesilets2023 method

Functions in this module:

    incoming_intensity_zreda_2012
    cutoff_rigidity_adjustment_to_jung
    incoming_intensity_adjustment_rc_corrected
    McjannetDesilets2023.local_gravity
    McjannetDesilets2023.local_air_pressure
    McjannetDesilets2023.tau
"""

import numpy as np
from neptoon.logging import get_logger

core_logger = get_logger()


def incoming_intensity_correction(
    incoming_intensity,
    ref_incoming_intensity,
    rc_scaling,
):
    """
    Calculate the correction factor for neutron counts based on the
    difference in incoming neutron intensity between current conditions
    and a reference.

    This function is based on the methodology introduced in Zreda
    (2012).

    Parameters
    ----------
    incoming_intensity : float
        Current incoming neutron intensity, in counts per time unit.
    ref_incoming_intensity : float
        Reference incoming neutron intensity, in counts per time unit.
    rc_scaling : float
        A scaling factor to account for difference in cut off rigidity
        between sensor and reference monitor

    Returns
    -------
    c_factor: float
        Correction factor to be multiplied with neutron counts.
    """
    intensity_ratio = ref_incoming_intensity / incoming_intensity
    c_factor = rc_scaling * (intensity_ratio - 1) + 1
    return c_factor


def rc_correction_hawdon(
    site_cutoff_rigidity,
    ref_monitor_cutoff_rigidity,
):
    """
    Creates adjustment parameter required to adjust for cutoff
    rigidities between a location and jungfraujoch. As described in
    Hawdon et al., 2014.

    Parameters
    ----------
    site_cutoff_rigidity : float
        Cutoff rigidity of CRNS site given in Gigavolts (Gv)
    reference_monitor_cutoff_rigidity : float, optional
        Cutoff rigidity of reference monitor given in Gigavolts (Gv)

    Returns
    -------
    rc_correction: float
        adjustment for differences in cutoff rigidity
    """

    rc_correction = (
        -0.075 * (site_cutoff_rigidity - ref_monitor_cutoff_rigidity) + 1
    )
    return rc_correction


class McjannetDesilets2023:
    """
    Provides methods for correcting incoming neutron intensity based on
    the research of McJannet and Desilets (2023).

    Reference:
        McJannet, D. L., & Desilets, D. (2023). Incoming Neutron Flux
        Corrections for Cosmic-Ray Soil and Snow Sensors Using the
        Global Neutron Monitor Network. Water Resources Research, 59,
        e2022WR033889. https://doi.org/10.1029/2022WR033889
    """

    @staticmethod
    def local_gravity(latitude, elevation):
        """
        Calculate the local gravitational acceleration based on latitude
        and elevation.

        Parameters
        ----------
        latitude : float
            Latitude in degrees
        elevation : float
            Elevation in meters (m)

        Returns
        -------
        gravity
            Local gravitational acceleration in meters per second
            squared (m/s^2).
        """
        rock_density = 2670
        g1 = 9.780327 * (
            1
            + 0.0053024 * np.sin(latitude / 180 * 3.141) ** 2
            - 0.0000058 * np.sin(2 * latitude / 180 * 3.141) ** 2
        )
        g2 = -3.086 * 10**-6 * elevation
        g3 = 4.194 * 10**-10 * rock_density * elevation
        gravity = g1 + g2 + g3

        return gravity

    @staticmethod
    def local_air_pressure(latitude, elevation):
        """
        Estimate the local atmospheric pressure based on latitude and elevation.

        Parameters
        ----------
        latitude : float
            Latitude in degrees
        elevation : float
            Elevation in meters (m)

        Returns
        -------
        p_ref: float
            Local atmospheric pressure in hectopascals (hPa).
        """
        g = McjannetDesilets2023.local_gravity(latitude, elevation)
        p_ref = 1013.25 * (1 + (-0.0065 / 288.15) * elevation) ** (
            (-g * 0.0289644) / (8.31432 * -0.0065)
        )
        p_ref = p_ref / 100

        return p_ref

    @staticmethod
    def tau(latitude, elevation, cut_off_rigidity):
        """
        Calculate the correction factor tau for neutron correction based
        on latitude, altitude, and cutoff rigidity.

        latitude : float
            Latitude in degrees
        elevation : float
            Elevation in meters (m)
        cut_off_rigidity: float
            Cutoff rigidity at the site in Gigavolts (Gv)

        Returns
        -------
        tau: float
            Tau correction factor to adjust difference between site and
            reference monitor cut off rigidity
        """
        c0 = -0.0009
        c1 = 1.7699
        c2 = 0.0064
        c3 = 1.8855
        c4 = 0.000013
        c5 = -1.2237
        eps = 1

        Rc_JUNG = 4.49
        atmospheric_depth_JUNG = 665.18
        tau_JUNG = (
            eps
            * 1
            * (c0 * atmospheric_depth_JUNG + c1)
            * (
                1
                - np.exp(
                    -(c2 * atmospheric_depth_JUNG + c3)
                    * Rc_JUNG ** (c4 * atmospheric_depth_JUNG + c5)
                )
            )
        )
        K_JUNG = 1 / tau_JUNG

        gravity = McjannetDesilets2023.local_gravity(latitude, elevation)
        pressure_ref = McjannetDesilets2023.local_air_pressure(
            latitude, elevation
        )
        pressure_ref = pressure_ref * 100  # convert to pascal
        amtmospheric_depth = 10 * pressure_ref / gravity
        tau = (
            eps
            * K_JUNG
            * (c0 * amtmospheric_depth + c1)
            * (
                1
                - np.exp(
                    -(c2 * amtmospheric_depth + c3)
                    * cut_off_rigidity ** (c4 * amtmospheric_depth + c5)
                )
            )
        )
        return tau
