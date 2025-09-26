import numpy as np
import pandas as pd
from typing import Literal, Union, List, Sequence

ArrayLike = Union[
    float,
    int,  # scalars
    List[Union[float, int]],  # lists
    Sequence[Union[float, int]],  # any sequence (tuple, etc.)
    np.ndarray,  # numpy arrays
    pd.Series,  # pandas series
]


def grav_soil_moisture_to_neutrons_desilets_etal_2010(
    gravimetric_sm: float,
    n0: float,
    additional_gravimetric_water: float = 0.0,
    a0: float = 0.0808,
    a1: float = 0.372,
    a2: float = 0.115,
):
    """
    Convert gravimetric soil moisture to neutron counts
    based on Eq. (A1) in Desilets et al. (2010).
    $$ N = N_0 \\,\\Big(\\frac{a_0}{\\theta_\\mathrm{grv} + \\theta_\\mathrm{add} + a_2} + a_1\\Big) $$

    References
    ----------
    * Desilets et al. (2010), Water Resources Research, doi:[10.1029/2009wr008726](https://doi.org/10.1029/2009wr008726)

    Parameters
    ----------
    gravimetric_sm : float
        Gravimetric soil moisture, $\\theta_\\mathrm{grv}$ (g/g)
    n0 : float
        Neutron scaling parameter, $N_0$ (cph)
    additional_gravimetric_water : float
        Gravimetric water equivalent of additional hydrogen pools, $\\theta_\\mathrm{add}$ (g/g),
        from lattice water or soil organic carbon, for instance.
    a0 : float
        Numerical constant
    a1 : float
        Numerical constant
    a2 : float
        Numerical constant

    Returns
    -------
    neutron_count : float
        Neutron count, $N$ (cph)
    """
    neutron_count = n0 * (
        a0 / (gravimetric_sm + additional_gravimetric_water + a2) + a1
    )
    return neutron_count


def neutrons_to_grav_soil_moisture_desilets_etal_2010(
    neutron_count: float,
    n0: float,
    additional_gravimetric_water: float = 0.0,
    a0: float = 0.0808,
    a1: float = 0.372,
    a2: float = 0.115,
):
    """
    Convert corrected neutron counts to gravimetric soil moisture
    based on Eq. (A1) in Desilets et al. (2010).
    $$ \\theta_\\mathrm{grv}(N) = \\frac{a_0}{N/N_0 - a_1} - a_2 - \\theta_\\mathrm{add} $$

    References
    ----------
    * Desilets et al. (2010), Water Resources Research, doi:[10.1029/2009wr008726](https://doi.org/10.1029/2009wr008726)

    Parameters
    ----------
    neutron_count : float
        Neutron count $N$ (cph)
    n0 : float
        Neutron scaling parameter, $N_0$ (cph)
    additional_gravimetric_water : float
        Gravimetric water equivalent of additional hydrogen pools, $\\theta_\\mathrm{add}$ (g/g),
        from lattice water or soil organic carbon, for instance.
    a0 : float
        Numerical constant
    a1 : float
        Numerical constant
    a2 : float
        Numerical constant

    Returns
    -------
    gravimetric_sm : float
        Gravimetric soil moisture, $\\theta_\\mathrm{grv}$ (g/g)
    """
    return (
        ((a0) / ((neutron_count / n0) - a1))
        - (a2)
        - additional_gravimetric_water
    )


def neutrons_to_grav_soil_moisture_desilets_etal_2010_reformulated(
    neutron_count: float,
    n0: float = None,
    n_max: float = None,
    additional_gravimetric_water: float = 0.0,
    a0: float = 0.0808,
    a1: float = 0.372,
    a2: float = 0.115,
):
    """
    Convert corrected neutron counts to gravimetric soil moisture
    based on Eq. (A1) in Desilets et al. (2010) and the reformulation
    suggested by Eq. (12) in Köhli et al. (2021).
    $$ \\theta_\\mathrm{grv}(N) = p_0\\,\\frac{1 - N/N_\\mathrm{max}}{p_1 - N/N_\\mathrm{max}} - \\theta_\\mathrm{add} $$

    References
    ----------
    * Desilets et al. (2010), Water Resources Research, doi:[10.1029/2009wr008726](https://doi.org/10.1029/2009wr008726)
    * Köhli et al. (2021), Frontiers in Water, doi:[10.3389/frwa.2020.544847](https://doi.org/10.3389/frwa.2020.544847)

    Parameters
    ----------
    neutron_count : float
        Neutron count $N$ (cph)
    n0 : float
        Neutron scaling parameter, $N_0$ (in cph), if $N_\\mathrm{max}$ is not defined.
    n_max : float
        Neutron scaling parameter, $N_\\mathrm{max}$ (in cph), if $N_0$ is not defined.
    additional_gravimetric_water : float
        Gravimetric water equivalent of additional hydrogen pools, $\\theta_\\mathrm{add}$ (g/g),
        from lattice water or soil organic carbon, for instance.
    a0 : float
        Numerical constant
    a1 : float
        Numerical constant
    a2 : float
        Numerical constant

    Returns
    -------
    gravimetric_sm : float
        Gravimetric soil moisture, $\\theta_\\mathrm{grv}$ (g/g)
    """
    if n_max is None:
        if n0 is None:
            print(
                "Error: Specify either N_0 or N_max for neutron to soil moisture conversion!"
            )
        else:
            n_max = n0 * ((a0 + (a1 * a2)) / (a2))
    p0 = -a2
    p1 = (a1 * a2) / (a0 + (a1 * a2))
    volumetric_sm = (
        p0 * ((1 - (neutron_count / n_max)) / (p1 - (neutron_count / n_max)))
    ) - additional_gravimetric_water
    return volumetric_sm


def neutrons_to_grav_soil_moisture_koehli_etal_2021(
    neutron_count: float,
    n0: float,
    abs_air_humidity: float,
    additional_gravimetric_water: float = 0.0,
    koehli_parameters: Literal[
        "Jan23_uranos",
        "Jan23_mcnpfull",
        "Mar12_atmprof",
        "Mar21_mcnp_drf",
        "Mar21_mcnp_ewin",
        "Mar21_uranos_drf",
        "Mar21_uranos_ewin",
        "Mar22_mcnp_drf_Jan",
        "Mar22_mcnp_ewin_gd",
        "Mar22_uranos_drf_gd",
        "Mar22_uranos_ewin_chi2",
        "Mar22_uranos_drf_h200m",
        "Aug08_mcnp_drf",
        "Aug08_mcnp_ewin",
        "Aug12_uranos_drf",
        "Aug12_uranos_ewin",
        "Aug13_uranos_atmprof",
        "Aug13_uranos_atmprof2",
    ] = "Mar21_mcnp_drf",
):
    """
    Convert corrected neutron counts and air humidity to gravimetric
    soil moisture based on the UTS function, Eq. (15) in Köhli et al. (2021).
    Note that this is a numerical inversion of the UTS function,
    developed by Prof. Ulrich Schmidt (University of Heidelberg).
    $$ \\theta_\\mathrm{grv} = f(N, h) - \\theta_\\mathrm{add},\\quad\\mathrm{where}\\quad f=\\mathrm{UTS}^{-1} $$

    References
    ----------
    * Köhli et al. (2021), Frontiers in Water, doi:[10.3389/frwa.2020.544847](https://doi.org/10.3389/frwa.2020.544847)

    Parameters
    ----------
    neutron_count : float
        Neutron count $N$ (cph)
    n0 : float
        Neutron scaling parameter ($N_0$ or $N_\\mathrm{D}$)
    abs_air_humidity : float
        Absolute air humidity, $h$ (g/cm³)
    additional_gravimetric_water : float
        Gravimetric water equivalent of additional hydrogen pools, $\\theta_\\mathrm{add}$ (g/g),
        from lattice water or soil organic carbon, for instance.
    koehli_parameters : str
        Parameter set to use.

    Returns
    -------
    gravimetric_sm : float
        Gravimetric soil moisture, $\\theta_\\mathrm{grv}$ (g/g)

    Examples
    --------
    With scalars:

    >>> soil_moisture_grv = neutrons_to_grav_soil_moisture_koehli_etal_2021(
    ...     neutron_count=1000,
    ...     n0=3000,
    ...     abs_air_humidity=5.0,
    ...     additional_gravimetric_water = 0.05,
    ... )
    0.292

    With Pandas:

    >>> data = pandas.DataFrame()
    >>> data["N"] = [1600, 1400, 1200, 1000]
    >>> data["h"] = [2, 3, 4, 5]
    >>> data["sm_grv"] = [
    ...     neutrons_to_grav_soil_moisture_koehli_etal_2021(
    ...         neutron_count=N,
    ...         n0=3000,
    ...         abs_air_humidity=h,
    ...         additional_gravimetric_water = 0.05,
    ...     )
    ...     for N, h in zip(data["N"].values, data["h"].values)
    ... ]
    """
    if pd.isna(neutron_count) or pd.isna(abs_air_humidity):
        return np.nan

    gravimetric_soil_moisture_0 = 0.0
    gravimetric_soil_moisture_1 = 2.0
    while gravimetric_soil_moisture_1 - gravimetric_soil_moisture_0 > 0.0001:
        gravimetric_soil_moisture_2 = (0.5 * gravimetric_soil_moisture_0) + (
            0.5 * gravimetric_soil_moisture_1
        )
        n2 = grav_soil_moisture_to_neutrons_koehli_etal_2021(
            gravimetric_sm=gravimetric_soil_moisture_2,
            abs_air_humidity=abs_air_humidity,
            n0=n0,
            koehli_parameters=koehli_parameters,
            additional_gravimetric_water=additional_gravimetric_water,
        )
        if neutron_count < n2:
            gravimetric_soil_moisture_0 = gravimetric_soil_moisture_2
        else:
            gravimetric_soil_moisture_1 = gravimetric_soil_moisture_2
    return gravimetric_soil_moisture_2


def grav_soil_moisture_to_neutrons_koehli_etal_2021(
    gravimetric_sm: float,
    abs_air_humidity: float,
    n0: float,
    additional_gravimetric_water: float = 0.0,
    koehli_parameters: Literal[
        "Jan23_uranos",
        "Jan23_mcnpfull",
        "Mar12_atmprof",
        "Mar21_mcnp_drf",
        "Mar21_mcnp_ewin",
        "Mar21_uranos_drf",
        "Mar21_uranos_ewin",
        "Mar22_mcnp_drf_Jan",
        "Mar22_mcnp_ewin_gd",
        "Mar22_uranos_drf_gd",
        "Mar22_uranos_ewin_chi2",
        "Mar22_uranos_drf_h200m",
        "Aug08_mcnp_drf",
        "Aug08_mcnp_ewin",
        "Aug12_uranos_drf",
        "Aug12_uranos_ewin",
        "Aug13_uranos_atmprof",
        "Aug13_uranos_atmprof2",
    ] = "Mar21_mcnp_drf",
):
    """
    Convert gravimetric soil moisture and air humidity to neutrons
    based on the UTS function, Eq. (15) in Köhli et al. (2021). Note that the UTS
    implementation here includes bulk density scaling,
    $\\theta_\\mathrm{vol}\\cdot1.43/\\varrho_\\mathrm{s}=\\theta_\\mathrm{grv}\\cdot1.43$
    (see Appendix).
    $$ N = \\mathrm{UTS}(\\theta_\\mathrm{grv} + \\theta_\\mathrm{add}, h) $$

    References
    ----------
    * Köhli et al. (2021), Frontiers in Water, doi:[10.3389/frwa.2020.544847](https://doi.org/10.3389/frwa.2020.544847)

    Parameters
    ----------
    gravimetric_sm : float
        Gravimetric soil moisture, $\\theta_\\mathrm{grv}$ (g/g)
    abs_air_humidity : float
        Aabsolute air humidity at the site, $h$ (g/cm³)
    n0 : float
        Neutron scaling parameter ($N_0$ or $N_\\mathrm{D}$)
    additional_gravimetric_water : float
        Gravimetric water equivalent of additional hydrogen pools, $\\theta_\\mathrm{add}$ (g/g),
        from lattice water or soil organic carbon, for instance.
    koehli_parameters : str
        Parameter set to use

    Returns
    -------
    neutron_count : float
        Neutron count $N$ (cph)

    Examples
    --------
    >>> N_cph = grav_soil_moisture_to_neutrons_koehli_etal_2021(
    ...     gravimetric_sm=0.292,
    ...     n0=3000,
    ...     abs_air_humidity=5.0,
    ...     additional_gravimetric_water=0.05,
    ... )
    1000
    """

    # Add offset water to consider total water content
    soil_moisture_total = gravimetric_sm + additional_gravimetric_water

    # Rescale to simulated bulk density according to Köhli et al. (2021), Appendix
    soil_moisture_total *= 1.43

    # Numerical check to keep soil moisture above zero
    if soil_moisture_total == 0.0:
        soil_moisture_total = 0.001
    p = []

    if koehli_parameters == "Jan23_uranos":
        p = [
            4.2580,
            0.0212,
            0.206,
            1.776,
            0.241,
            -0.00058,
            -0.02800,
            0.0003200,
            -0.0000000180,
        ]
    elif koehli_parameters == "Jan23_mcnpfull":
        p = [
            7.0000,
            0.0250,
            0.233,
            4.325,
            0.156,
            -0.00066,
            -0.01200,
            0.0004100,
            -0.0000000410,
        ]
    elif koehli_parameters == "Mar12_atmprof":
        p = [
            4.4775,
            0.0230,
            0.217,
            1.540,
            0.213,
            -0.00022,
            -0.03800,
            0.0003100,
            -0.0000000003,
        ]
    elif koehli_parameters == "Mar21_mcnp_drf":
        p = [
            1.0940,
            0.0280,
            0.254,
            3.537,
            0.139,
            -0.00140,
            -0.00880,
            0.0001150,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar21_mcnp_ewin":
        p = [
            1.2650,
            0.0259,
            0.135,
            1.237,
            0.063,
            -0.00021,
            -0.01170,
            0.0001200,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar21_uranos_drf":
        p = [
            1.0240,
            0.0226,
            0.207,
            1.625,
            0.235,
            -0.00290,
            -0.00930,
            0.0000740,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar21_uranos_ewin":
        p = [
            1.2230,
            0.0185,
            0.142,
            2.568,
            0.155,
            -0.00047,
            -0.01190,
            0.0000920,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar22_mcnp_drf_Jan":
        p = [
            1.0820,
            0.0250,
            0.235,
            4.360,
            0.156,
            -0.00071,
            -0.00610,
            0.0000500,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar22_mcnp_ewin_gd":
        p = [
            1.1630,
            0.0244,
            0.182,
            4.358,
            0.118,
            -0.00046,
            -0.00747,
            0.0000580,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar22_uranos_drf_gd":
        p = [
            1.1180,
            0.0221,
            0.173,
            2.300,
            0.184,
            -0.00064,
            -0.01000,
            0.0000810,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar22_uranos_ewin_chi2":
        p = [
            1.0220,
            0.0218,
            0.199,
            1.647,
            0.243,
            -0.00029,
            -0.00960,
            0.0000780,
            0.0000000000,
        ]
    elif koehli_parameters == "Mar22_uranos_drf_h200m":
        p = [
            1.0210,
            0.0222,
            0.203,
            1.600,
            0.244,
            -0.00061,
            -0.00930,
            0.0000740,
            0.0000000000,
        ]
    elif koehli_parameters == "Aug08_mcnp_drf":
        p = [
            1.110773444917129,
            0.034319446894963,
            0.180046592985848,
            1.211393214064259,
            0.093433803170610,
            -1.877788035e-005,
            -0.00698637546803,
            5.0316941885e-005,
            0.0000000000,
        ]
    elif koehli_parameters == "Aug08_mcnp_ewin":
        p = [
            1.271225645585415,
            0.024790265564895,
            0.107603498535911,
            1.243101823658557,
            0.057146624195463,
            -1.93729201894976,
            -0.00866217333051,
            6.198559205414182,
            0.0000000000,
        ]
    elif koehli_parameters == "Aug12_uranos_drf":
        p = [
            1.042588152355816,
            0.024362250648228,
            0.222359434641456,
            1.791314246517330,
            0.197766380530824,
            -0.00053814104957,
            -0.00820189794785,
            6.6412111902e-005,
            0.0000000000,
        ]
    elif koehli_parameters == "Aug12_uranos_ewin":
        p = [
            1.209060105287452,
            0.021546879683024,
            0.129925023764294,
            1.872444149093526,
            0.128883139550384,
            -0.00047134595878,
            -0.01080226893400,
            8.8939419535e-005,
            0.0000000000,
        ]
    elif koehli_parameters == "Aug13_uranos_atmprof":
        p = [
            1.044276170094123,
            0.024099232055379,
            0.227317847739138,
            1.782905159416135,
            0.198949609723093,
            -0.00059182327737,
            -0.00897372356601,
            7.3282344356e-005,
            0.0000000000,
        ]
    elif koehli_parameters == "Aug13_uranos_atmprof2":
        p = [
            4.31237,
            0.020765,
            0.21020,
            1.87120,
            0.16341,
            -0.00052,
            -0.00225,
            0.000308,
            -1.9639e-8,
        ]

    N = (p[1] + p[2] * soil_moisture_total) / (soil_moisture_total + p[1]) * (
        p[0]
        + p[6] * abs_air_humidity
        + p[7] * abs_air_humidity**2
        + p[8] * abs_air_humidity**3 / soil_moisture_total
    ) + np.exp(-p[3] * soil_moisture_total) * (p[4] + p[5] * abs_air_humidity)

    return N * n0


def find_n0(
    gravimetric_sm: ArrayLike,
    neutron_count: ArrayLike,
    abs_air_humidity: ArrayLike = 0.0,
    additional_gravimetric_water: ArrayLike = 0.0,
    conversion_theory: Literal[
        "desilets_etal_2010", "koehli_etal_2021"
    ] = "desilets_etal_2010",
    desilets_parameters: ArrayLike = [0.0808, 0.372, 0.115],
    koehli_parameters: Literal[
        "Jan23_uranos",
        "Jan23_mcnpfull",
        "Mar12_atmprof",
        "Mar21_mcnp_drf",
        "Mar21_mcnp_ewin",
        "Mar21_uranos_drf",
        "Mar21_uranos_ewin",
        "Mar22_mcnp_drf_Jan",
        "Mar22_mcnp_ewin_gd",
        "Mar22_uranos_drf_gd",
        "Mar22_uranos_ewin_chi2",
        "Mar22_uranos_drf_h200m",
        "Aug08_mcnp_drf",
        "Aug08_mcnp_ewin",
        "Aug12_uranos_drf",
        "Aug12_uranos_ewin",
        "Aug13_uranos_atmprof",
        "Aug13_uranos_atmprof2",
    ] = "Mar21_mcnp_drf",
    metric: Literal[
        "rmse",
        "mae",
        "mse",
        "mape",
        "rmspe",
        "log_mse",
        "log_mse",
        "relative_rmse",
    ] = "rmse",
    return_error: bool = False,
):
    """
    Finds the neutron scaling parameter, $N_0$ for Desilets et al. (2010)
    or $N_\\mathrm{D}$ for Köhli et al. (2021). The function works with scalar
    input (single calibration day) or vectorized input (multiple days).

    References
    ----------
    * Desilets et al. (2010), Water Resources Research, doi:[10.1029/2009wr008726](https://doi.org/10.1029/2009wr008726)
    * Köhli et al. (2021), Frontiers in Water, doi:[10.3389/frwa.2020.544847](https://doi.org/10.3389/frwa.2020.544847)

    Parameters
    ----------
    gravimetric_sm : float
        gravimetric water content (g/cm3)
    neutron_count : float
        Neutron count in counts per hour (cph)
    abs_air_humidity : float
        absolute air humidity (g/cm³)
    additional_gravimetric_water : float
        Gravimetric water equivalent of additional hydrogen pools (g/g),
        from lattice water or soil organic carbon, for instance.
    desilets_parameters: ArrayLike
        Parameter set for the Desilets Eq., [a0, a1, a2],
    koehli_parameters: str
        Parameter set for the Köhli Eq.
    metric:
        Error metric to optimize, one of: 'rmse',  'mae',  'mse',  'mape',  'rmspe',  'log_mse',  'log_mse', 'relative_rmse'
    return_error: bool
        If true, return a second value representing the RMSE

    Examples
    --------
    >>> N0, rmse = find_n0(
    ...    gravimetric_sm=[0.292, 0.032],
    ...    abs_air_humidity=[5,4],
    ...    neutron_count=[1000,1650],
    ...    additional_gravimetric_water=[0.05,0.05],
    ...    conversion_theory='koehli_etal_2021',
    ...    return_error = True
    ... )
    >>> print(f"N0 = {N0:.0f} ± {rmse:.0f}")
    3165 ± 46
    """
    from scipy.optimize import minimize_scalar

    # Broadcast ArrayLike input to same-lengths arrays
    n_array, sm_array, h_array, a_array = np.broadcast_arrays(
        np.atleast_1d(neutron_count),
        np.atleast_1d(gravimetric_sm),
        np.atleast_1d(abs_air_humidity),
        np.atleast_1d(additional_gravimetric_water),
    )

    def _obj_n0(n0_try):
        if conversion_theory == "koehli_etal_2021":
            neutron_estimates = np.array(
                [
                    grav_soil_moisture_to_neutrons_koehli_etal_2021(
                        gravimetric_sm=sm_i,
                        abs_air_humidity=h_i,
                        n0=n0_try,
                        additional_gravimetric_water=a_i,
                        koehli_parameters=koehli_parameters,
                    )
                    for sm_i, h_i, a_i in zip(sm_array, h_array, a_array)
                ]
            )
        elif conversion_theory == "desilets_etal_2010":
            neutron_estimates = np.array(
                [
                    grav_soil_moisture_to_neutrons_desilets_etal_2010(
                        gravimetric_sm=sm_i,
                        n0=n0_try,
                        additional_gravimetric_water=a_i,
                        a0=desilets_parameters[0],
                        a1=desilets_parameters[1],
                        a2=desilets_parameters[2],
                    )
                    for sm_i, a_i in zip(sm_array, a_array)
                ]
            )

        errors = n_array - neutron_estimates
        if metric == "rmse":
            return np.sqrt(np.mean(errors**2))
        elif metric == "mae":
            return np.mean(np.abs(errors))
        elif metric == "mse":
            return np.mean(errors**2)
        elif metric == "mape":
            # Mean Absolute Percentage Error - good for non-linear functions
            return np.mean(np.abs(errors / n_array)) * 100
        elif metric == "rmspe":
            # Root Mean Square Percentage Error
            return np.sqrt(np.mean((errors / n_array) ** 2)) * 100
        elif metric == "log_mse":
            # Log-scale MSE - reduces impact of large values
            log_n = np.log(np.maximum(n_array, 1e-10))  # Avoid log(0)
            log_estimates = np.log(np.maximum(neutron_estimates, 1e-10))
            return np.mean((log_n - log_estimates) ** 2)
        elif metric == "log_mse":
            # Relative RMSE - normalized by target values
            relative_errors = errors / np.maximum(np.abs(n_array), 1e-10)
            return np.sqrt(np.mean(relative_errors**2))
        elif metric == "relative_rmse":
            # Relative RMSE - normalized by target values
            relative_errors = errors / np.maximum(np.abs(n_array), 1e-10)
            return np.sqrt(np.mean(relative_errors**2))
        else:
            raise ValueError(f"Error: Invalid metric selected: {metric}")

    n0 = minimize_scalar(_obj_n0).x

    if return_error:
        return n0, _obj_n0(n0)
    else:
        return n0
