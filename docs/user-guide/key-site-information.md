# SensorInfo Class

The `SiteInformation` class is used to store essential information about a CRNS site that is needed for data processing. When processing data with YAML configuration files this information is automatically extracted from the supplied YAML. 

## Class Definition

```python
@dataclass
class SensorInfo:
    latitude: float
    longitude: float
    elevation: float
    reference_incoming_neutron_value: float
    dry_soil_bulk_density: float
    lattice_water: float
    soil_organic_carbon: float
    cutoff_rigidity: float
    mean_pressure: Optional[float] = None
    site_biomass: Optional[float] = None
    n0: Optional[float] = None
    beta_coefficient: Optional[float] = None
    l_coefficient: Optional[float] = None
```

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| latitude | float | The latitude of the CRNS site in degrees |
| longitude | float | The longitude of the CRNS site in degrees |
| elevation | float | The elevation of the CRNS site (in meters) |
| reference_incoming_neutron_value | float | Reference value for incoming neutron intensity |
| dry_soil_bulk_density | float | Dry soil bulk density (in g/cm³) |
| lattice_water | float | Lattice water content (in g/g) |
| soil_organic_carbon | float | Soil organic carbon content (in g/g) |
| cutoff_rigidity | float | Geomagnetic cutoff rigidity (in GV) |
| mean_pressure | Optional[float] | Mean atmospheric pressure at the site (in hPa) |
| site_biomass | Optional[float] | Above-ground biomass at the site (in kg/m²) |
| n0 | Optional[float] | Calibration parameter for neutron counting |
| beta_coefficient | Optional[float] | Beta coefficient for soil moisture calculation |
| l_coefficient | Optional[float] | L coefficient for soil moisture calculation |

## Methods

### add_custom_value

This method allows you to add a custom attribute to the SiteInformation instance.

```python
def add_custom_value(self, name: str, value):
    """
    Adds a value to SiteInformation that has not been previously designed.

    Parameters:
    -----------
    name : str
        Name of the new attribute
    value : Any
        The value of the new attribute
    """
```

This can be important when testing new ideas such as trying out a new theory with [your own correction](~/advanced-users/write-your-own-corrections.md) !!!TODO fix this link!!!

## Usage Example

```python
from neptoon.data_management import SiteInformation

# Create a SiteInformation instance
site_info = SiteInformation(
    latitude=52.3676,
    longitude=4.9041,
    elevation=100,
    reference_incoming_neutron_value=150,
    dry_soil_bulk_density=1.5,
    lattice_water=0.02,
    soil_organic_carbon=0.01,
    cutoff_rigidity=3.5
)

# Add a custom value
site_info.add_custom_value("vegetation_type", "grassland")

# Access attributes
print(f"Site latitude: {site_info.latitude}")
print(f"Site vegetation type: {site_info.vegetation_type}")
```

and then if we want to now add this to our data hub:

```python

from neptoon.data_management import CRNSDataHub, SiteInformation
# presume dataframe pre-formatted
site_info = SiteInformation(
    latitude=52.3676,
    longitude=4.9041,
    elevation=100,
    reference_incoming_neutron_value=150,
    dry_soil_bulk_density=1.5,
    lattice_water=0.02,
    soil_organic_carbon=0.01,
    cutoff_rigidity=3.5
)

data_hub = CRNSDataHub(
			   crns_data_frame = df
			   site_information = site_info
				   )
```


!!! note "How much information?"
	Optional attributes can be set to `None` if the information is not available. However, providing as much information as possible will ensure outputs (e.g., PDF reports) are complete
