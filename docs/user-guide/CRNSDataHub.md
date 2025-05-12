# CRNSDataHub Class

The `CRNSDataHub` class serves as a central management system for Cosmic-Ray Neutron Sensor (CRNS) data processing within the neptoon package. It coordinates various processing steps and maintains data integrity throughout the workflow.

## Class Overview

The `CRNSDataHub` class manages:
- CRNS data storage and manipulation
- Quality assessment of data
- Application of corrections to neutron counts
- Conversion of neutron counts to soil moisture estimates
- Data validation at various processing stages

## Key Attributes

- `crns_data_frame`: pandas DataFrame containing the CRNS time series data
- `flags_data_frame`: pandas DataFrame containing quality flags for the data (created)
- `site_information`: SiteInformation object containing metadata about the CRNS site
- `quality_assessor`: DataQualityAssessor object for performing quality checks
- `correction_factory`: CorrectionFactory object for creating correction instances
- `correction_builder`: CorrectionBuilder object for managing multiple corrections

## Main Methods

### __init__

```python
def __init__(self, crns_data_frame: pd.DataFrame, flags_data_frame: pd.DataFrame = None, 
             configuration_manager: ConfigurationManager = None, 
             quality_assessor: DataQualityAssessor = None, validation: bool = True, 
             site_information: SiteInformation = None, process_with_config: bool = False):
```

Initializes the CRNSDataHub with the provided data and configuration.

### validate_dataframe

```python
def validate_dataframe(self, schema: str):
```

Validates the data frame against a specified schema to ensure data integrity.

### update_site_information

```python
def update_site_information(self, new_site_information: SiteInformation):
```

Updates the site information and reinitializes the correction factory.

### attach_nmdb_data

```python
def attach_nmdb_data(self, station="JUNG", new_column_name="incoming_neutron_intensity", 
                     resolution="60", nmdb_table="revori"):
```

Attaches incoming neutron intensity data from NMDB to the CRNS data frame.

### apply_quality_flags

```python
def apply_quality_flags(self, custom_flags: QualityAssessmentFlagBuilder = None, 
                        flags_from_config: bool = False, flags_default: str = None):
```

Applies quality flags to the data based on specified criteria.

### select_correction

```python
def select_correction(self, correction_type: CorrectionType = "empty", 
                      correction_theory: CorrectionTheory = None, 
                      use_all_default_corrections=False):
```

Selects and adds corrections to be applied to the neutron count data.

### correct_neutrons

```python
def correct_neutrons(self, correct_flagged_values_too=False):
```

Applies selected corrections to the neutron count data.

### smooth_data

```python
def smooth_data(self, column_to_smooth: str, smooth_method: Literal["rolling_mean", "savitsky_golay"] = "rolling_mean", 
                window: Optional[Union[int, str]] = 12, poly_order: int = 4, auto_update_final_col: bool = True):
```

Applies smoothing to a specified data column.

### produce_soil_moisture_estimates

```python
def produce_soil_moisture_estimates(self, n0: float = None, dry_soil_bulk_density: float = None, 
                                    lattice_water: float = None, soil_organic_carbon: float = None):
```

Calculates soil moisture estimates based on corrected neutron counts and site parameters.

### save_data

```python
def save_data(self, folder_path, file_name, step):
```

Saves the processed data to a specified location.

## Usage Example

```python
import pandas as pd
from neptoon.data_management import CRNSDataHub, SiteInformation

# Assume we have a pandas DataFrame 'crns_df' with CRNS data
crns_df = pd.read_csv('crns_data.csv')

# Create a SiteInformation object
site_info = SiteInformation(latitude=52.3676, longitude=4.9041, elevation=1, ...)

# Initialize CRNSDataHub
data_hub = CRNSDataHub(crns_data_frame=crns_df, site_information=site_info)

# Perform data processing steps
data_hub.validate_dataframe(schema="initial_check")
data_hub.attach_nmdb_data()
data_hub.apply_quality_flags()
data_hub.select_correction(correction_type="pressure")
data_hub.correct_neutrons()
data_hub.produce_soil_moisture_estimates()

# Save processed data
data_hub.save_data(folder_path='output/', file_name='processed_crns_data', step='final')
```

## Notes

- The CRNSDataHub is designed to be flexible, allowing users to customize various aspects of the data processing workflow.
- It's important to ensure that all required data and metadata are properly initialized before proceeding with data processing steps.
- The class includes various validation checks to maintain data integrity throughout the processing pipeline.