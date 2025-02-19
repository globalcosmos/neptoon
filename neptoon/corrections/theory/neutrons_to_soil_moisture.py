"""

"""

import numpy as np


def neutrons_to_grav_sm_desilets(
    neutrons,
    N0=1000,
    a0=0.0808,
    a1=0.372,
    a2=0.115,
):
    return a0 / (neutrons / N0 - a1) - a2


def convert_neutrons_to_soil_moisture(
    dry_soil_bulk_density: float,
    neutron_count: float,
    n0: float,
    lattice_water: float,
    water_equiv_soil_organic_matter: float,
    a0: float = 0.0808,
    a1: float = 0.372,
    a2: float = 0.115,
):
    """
    Converts corrected neutrons counts into volumetric soil moisture

    doi: TODO

    Parameters
    ----------
    a0 : float
        constant
    a1 : float
        constant
    a2 : float
        constant
    bulk_density : float
        dry soil bulk density of the soil in grams per cubic centimer
        e.g. 1.4 (g/cm^3)
    neutron_count : int
        Neutron count in counts per hour (cph)
    n0 : int
        N0 number
    lattice_water : float
        lattice water - decimal percent e.g. 0.002
    water_equiv_soil_organic_carbon : float
        water equivelant soil organic carbon - decimal percent e.g, 0.02


    """
    return (
        ((a0) / ((neutron_count / n0) - a1))
        - (a2)
        - lattice_water
        - water_equiv_soil_organic_matter
    ) * dry_soil_bulk_density


def convert_neutrons_to_soil_moisture_kohli(
    bulk_density: float,
    neutron_count: float,
    n0: float,
    lattice_water: float,
    water_equiv_soil_organic_carbon: float,
    a0: float = 0.0808,
    a1: float = 0.372,
    a2: float = 0.115,
):
    """
    Converts corrected neutrons counts into volumetric soil moisture
    following the method outlined in Köhli et al. 2021

    https://doi.org/10.3389/frwa.2020.544847

    Parameters
    ----------
    a0 : float
        Constant
    a1 : float
        Constant
    a2 : float
        Constant
    bulk_density : float
        Dry soil bulk density of the soil in grams per cubic centimer
        e.g. 1.4 (g/cm^3)
    neutron_count : int
        Neutron count in counts per hour (cph)
    n0 : int
        N0 number given as maximum number of neutrons possible over a 1
        hour integration.
    lattice_water : float
        Lattice water - decimal percent e.g. 0.002
    water_equiv_soil_organic_carbon : float
        Water equivelant soil organic carbon - decimal percent e.g, 0.02
    """
    nmax = n0 * ((a0 + (a1 * a2)) / (a2))
    ah0 = -a2
    ah1 = (a1 * a2) / (a0 + (a1 * a2))
    sm = (
        (ah0 * ((1 - (neutron_count / nmax)) / (ah1 - (neutron_count / nmax))))
        - lattice_water
        - water_equiv_soil_organic_carbon
    ) * bulk_density
    return sm


def convert_neutrons_to_soil_moisture_uts(
    neutron_count: float,
    n0: float,
    air_humidity: float,
    bulk_density: float = 1.0,
    lattice_water: float = 0.0,
    water_equiv_soil_organic_carbon: float = 0.0,
    method: str = "Mar21_uranos_drf",
):
    """
    Converts corrected neutrons counts into volumetric soil moisture
    following the method outlined in Köhli et al. 2021

    https://doi.org/10.3389/frwa.2020.544847

    Example
    -------
    convert_neutrons_to_soil_moisture_uts(
        neutron_count=2000, n0=3000, air_humidity=5
    )


    """
    if np.isnan(neutron_count):
        return np.nan

    # neutron_count = neutron_count/n0

    t0 = 0.0
    t1 = 4.0
    n_i0 = convert_soil_moisture_to_neutrons_uts(
        0.0,
        n0=n0,
        h=air_humidity,
        method=method,
        off=lattice_water + water_equiv_soil_organic_carbon,
        bd=bulk_density,
    )
    n_i1 = convert_soil_moisture_to_neutrons_uts(
        1.0,
        h=air_humidity,
        n0=n0,
        method=method,
        off=lattice_water + water_equiv_soil_organic_carbon,
        bd=bulk_density,
    )
    while t1 - t0 > 0.0001:
        t2 = 0.5 * (t0 + t1)
        n2 = convert_soil_moisture_to_neutrons_uts(
            t2,
            h=air_humidity,
            n0=n0,
            method=method,
            off=lattice_water + water_equiv_soil_organic_carbon,
            bd=bulk_density,
        )
        if neutron_count < n2:
            t0 = t2
            n_i0 = n2
        else:
            t1 = t2
            n_i1 = n2
    t2 = 0.5 * (t0 + t1)

    # if t2 <= 0.0001: t2 = np.nan

    return t2


def convert_soil_moisture_to_neutrons_uts(sm, h, n0, off=0.0, bd=1, method="Mar21_uranos_drf", bio=0):
    """
    Example
    -------
    convert_soil_moisture_to_neutrons_uts(sm=0.0316, n0=3000, h=5)

    """

    # total sm
    smt = sm + off
    smt *= 1.43 / bd
    if smt == 0.0:
        smt = 0.001
    p = []

    if method == "Jan23_uranos":
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
    elif method == "Jan23_mcnpfull":
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
    elif method == "Mar12_atmprof":
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

    elif method == "Mar21_mcnp_drf":
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
    elif method == "Mar21_mcnp_ewin":
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
    elif method == "Mar21_uranos_drf":
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
    elif method == "Mar21_uranos_ewin":
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

    elif method == "Mar22_mcnp_drf_Jan":
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
    elif method == "Mar22_mcnp_ewin_gd":
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
    elif method == "Mar22_uranos_drf_gd":
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
    elif method == "Mar22_uranos_ewin_chi2":
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
    elif method == "Mar22_uranos_drf_h200m":
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

    elif method == "Aug08_mcnp_drf":
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
    elif method == "Aug08_mcnp_ewin":
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
    elif method == "Aug12_uranos_drf":
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
    elif method == "Aug12_uranos_ewin":
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
    elif method == "Aug13_uranos_atmprof":
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
    elif method == "Aug13_uranos_atmprof2":
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

    N = (p[1] + p[2] * smt) / (smt + p[1]) * (
        p[0] + p[6] * h + p[7] * h**2 + p[8] * h**3 / smt
    ) + np.exp(-p[3] * smt) * (p[4] + p[5] * (h + bio / 5 * 1000))

    return N * n0


"""
Examples
--------
import pandas

data = pandas.DataFrame()
data["N"] = [2000, 1900, 1800, 2100]
data["h"] = [1, 2, 3, 4]

data["sm"] = [
    convert_neutrons_to_soil_moisture_uts(
        neutron_count=N,
        n0=3000,
        air_humidity=h,
        bulk_density=1.23,
        lattice_water=0.01,
        water_equiv_soil_organic_carbon=0.01,
        method="Mar21_mcnp_drf",
    )
    for (N, h) in data[["N", "h"]]
]

data["sm"] = data.apply(
    lambda row: convert_neutrons_to_soil_moisture_uts(
        neutron_count=row["N"],
        n0=3000,
        air_humidity=row["h"],
        bulk_density=1.23,
        lattice_water=0.01,
        water_equiv_soil_organic_carbon=0.01,
        method="Mar21_mcnp_drf",
    ),
    axis=1,
)

data

soil_moisture_m3m3 = convert_neutrons_to_soil_moisture_uts(
    neutron_count=2000,
    n0=3000,
    air_humidity=5.0,
    bulk_density=1.23,
    lattice_water=0.0027,
    water_equiv_soil_organic_carbon=0.1,
    method="Mar21_mcnp_drf",
)
"""


def compute_n0_uts(sm, h, n, lattice_water=0.0, water_equiv_soil_organic_carbon=0.0, bd=1, method="Mar21_uranos_drf", bio=0):
    """
    Computes the n0 for the UTS-function
    following the method outlined in Köhli et al. 2021
    (as needed by convert_neutrons_to_soil_moisture_uts() and convert_soil_moisture_to_neutrons_uts())

    https://doi.org/10.3389/frwa.2020.544847

    Parameters
    ----------
    sm : float
        volumetric water content (cm3/cm3)
    h : float
        air_humidity (%?)
    bd : float
        Dry soil bulk density of the soil in grams per cubic centimeter
        e.g. 1.4 (g/cm^3)
    n : float
        Neutron count in counts per hour (cph)
    lattice_water : float
        Lattice water - decimal percent e.g. 0.002
    water_equiv_soil_organic_carbon : float
        Water equivalent soil organic carbon - decimal percent e.g, 0.02
    method: str
        one of "Mar21_uranos_drf", "Aug13_uranos_atmprof", ...

    Example
    -------
    sm=0.3 #soil moisture [-]
    h=3 #air humidity (%?)
    bd = 1.2 #bulk density
    bio = 0 #(kg/m²]?
    n_obs = 3000 #observed neutron counts (counts / hour)

    n0  = compute_n0_uts(sm=sm, h=h, n=n_obs, lattice_water=0.0, water_equiv_soil_organic_carbon=0.0, bd=bd, method="Mar21_uranos_drf", bio=0)
    #check the determined n0, which should be close to n:
    convert_soil_moisture_to_neutrons_uts(
            sm=theta, h=h, n0=n0, off=0.0, bd=bd, method="Mar21_uranos_drf", bio=bio)

    """
    from scipy.optimize import minimize_scalar

    off = lattice_water + water_equiv_soil_organic_carbon

    def obj_n0(n0_try):   #objective function to optimize for best n0
        n_est = convert_soil_moisture_to_neutrons_uts(
            sm=sm, h=h, n0=n0_try, off=off, bd=bd, method=method, bio=bio)
        error = np.abs(n - n_est)
        return np.mean(error)
    
    singleopt = minimize_scalar(obj_n0)   #optimize to find best n0
    n0 = singleopt.x  #

    return(n0) 
