# SensorInfo Documentation

## Overview

The `SensorInfo` class stores essential metadata about you CRNS site. These are generally values that are not expecting to change with time. For example, the latitude and longitude of the sensor (if you move your sensor, treat it as a "new" sensor!). 

## SensorInfo Class

The `SensorInfo` class stores site-specific information. Here is an example of how you could create one in your pipeline:

```python
from neptoon.config.configuration_input import SensorInfo

sensor_info = SensorInfo(
    name="MyStation",
    latitude=52.3676,
    longitude=4.9041,
    elevation=100,
    reference_incoming_neutron_value=150,
    dry_soil_bulk_density=1.5,
    lattice_water=0.02,
    soil_organic_carbon=0.01,
    site_cutoff_rigidity=3.5,
)

```

## Key Attributes

| Attribute | Type | Description | Impact on Processing |
|-----------|------|-------------|---------------------|
| `name` | str | Name identifier for the station | Used in output file naming and reports |
| `latitude` | float | Latitude in decimal degrees | Used in spatial corrections and footprint calculations |
| `longitude` | float | Longitude in decimal degrees | Used in spatial corrections and site-specific retrievals |
| `elevation` | float | Elevation in meters | Affects pressure-based corrections |
| `reference_incoming_neutron_value` | float | Reference value for incoming neutron intensity | Required for intensity correction normalization |
| `dry_soil_bulk_density` | float | Dry soil bulk density (g/cm³) | Critical for converting neutron counts to soil moisture |
| `lattice_water` | float | Lattice water content (g/g) | Affects neutron moderation and soil moisture calculations |
| `soil_organic_carbon` | float | Soil organic carbon content (g/g) | Influences neutron moderation similar to water |
| `site_cutoff_rigidity` | float | Geomagnetic cutoff rigidity (GV) | Used for cosmic ray intensity corrections |
| `mean_pressure` | Optional[float] | Mean atmospheric pressure (hPa) | Used for pressure correction reference |
| `site_biomass` | Optional[float] | Above-ground biomass (kg/m²) | Used for biomass correction if enabled |
| `N0` | Optional[float] | Calibration parameter | Key parameter linking neutron counts to soil moisture |
| `beta_coefficient` | Optional[float] | Beta coefficient | Parameter for some soil moisture conversion equations |

## Using SensorInfo with CRNSDataHub

The `SensorInfo` object should be attached to a `CRNSDataHub` instance for data processing:

```python
from neptoon.hub import CRNSDataHub
import pandas as pd

# Assume we have pre-formatted CRNS data
crns_data = pd.DataFrame(...)  

# Create the data hub with sensor information
data_hub = CRNSDataHub(
    crns_data_frame=crns_data,
    sensor_info=sensor_info
)

# The sensor_info can also be added or updated later
data_hub.sensor_info = sensor_info

```

## Adding SensorInfo to your time series

Once you have your `SensorInfo` attached to your data_hub there is an important step you **must** take:

```python
# Prepare static values in the data frame from sensor_info
data_hub.prepare_static_values()
```

This method will take each of the values in the `SensorInfo` class and attach them to your time series data as columns of data (1 value repeated).

!!! note "Why this step?"
    The reason behind this is that whilst for stationary sensor some of these values will be static (e.g., elevation), for roving these values will change. By attaching static values as a time series - we ensure that methods to correct neutrons are applied the same way - whether it's roving data or stationary data. 

## Best Practices

1. **Data Completeness**: Provide as much information as possible, even optional attributes, to ensure accurate processing.

2. **Metadata Sources**: Information like soil properties should ideally come from direct field measurements, but literature values can be used when site-specific data is unavailable.

3. **Calibration**: The N0 value should be determined through field calibration rather than assumed. More on this later.

5. **Configuration Files**: For reproducibility, consider storing SensorInfo in YAML configuration files that can be version-controlled.

## Impact on Processing

The `SensorInfo` values directly influence key processing steps:

- **Correction Factors**: Values like elevation and cutoff rigidity affect atmospheric and cosmic ray corrections
- **Soil Moisture Conversion**: N0, dry_soil_bulk_density, and other soil properties determine the relationship between neutron counts and volumetric soil moisture

## Configuration-Based Approach

For production workflows, creating SensorInfo through configuration files is recommended:

```python
from neptoon.io.read import DataHubFromConfig

# Load from a YAML configuration file
hub_creator = DataHubFromConfig(path_to_sensor_config='sensors/my_station.yaml')
data_hub = hub_creator.create_data_hub()

# The sensor_info is automatically created and attached
```

This approach ensures consistent processing across multiple runs and simplifies reproducibility.