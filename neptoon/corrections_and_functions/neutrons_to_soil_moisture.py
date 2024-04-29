"""

"""


def convert_neutrons_to_soil_moisture(
    a0: float,
    a1: float,
    a2: float,
    bulk_density: float,
    neutron_count: float,
    n0: float,
    lattice_water: float,
    water_equiv_soil_organic_carbon: float,
):
    """
    Converts corrected neutrons counts into volumetric soil moisture

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
        - water_equiv_soil_organic_carbon
    ) * bulk_density


def convert_neutrons_to_soil_moisture_kohli(
    a0: float,
    a1: float,
    a2: float,
    bulk_density: float,
    neutron_count: float,
    n0: float,
    lattice_water: float,
    water_equiv_soil_organic_carbon: float,
):
    """
    Converts corrected neutrons counts into volumetric soil moisture
    following the method outline in Köhli paper

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
