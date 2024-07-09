from dataclasses import dataclass
from typing import Optional


@dataclass
class SiteInformation:
    """
    A data class which stores information about the site which is needed
    in data processing

    TODO: alternatively do we use pydantic and validate?
    """

    latitude: float
    longitude: float
    elevation: float
    reference_incoming_neutron_value: float
    bulk_density: float
    lattice_water: float
    soil_organic_carbon: float
    cutoff_rigidity: float
    mean_pressure: Optional[float] = None
    site_biomass: Optional[float] = None

    def add_custom_value(self, name: str, value):
        """
        Adds a value to SiteInformation that has not been previously
        designed.

        Parameters
        ----------
        name : str
            name of the new attribute
        value
            The value of the new attribute
        """
        setattr(self, name, value)
