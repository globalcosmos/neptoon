from dataclasses import dataclass
from typing import Optional


@dataclass
class SiteInformation:
    """
    A data class which stores information about the site which is needed
    in data processing

    IMPORTANT: If updating this with new values in the code base, ensure
    you also update ColumnInfo in
    ..data_management.column_information.py to include a mapping to a
    column name. This ensures when running the
    CRNSDataHub.prepare_static_values() method that the name for the
    column is consistent throughout processing.


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
    n0: Optional[float] = None

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
