# Quality Assessment in neptoon

## Overview

The quality assessment (QA) system in neptoon provides tools to identify and flag questionable data points in CRNS time series. Built on top of [SaQC](https://rdm-software.pages.ufz.de/saqc/) framework, neptoon's QA system allows users to apply standardized quality checks to their data, helping to ensure that downstream analyses are based on reliable measurements.

## Key Components

The quality assessment system in neptoon is built from several interconnected parts, each serving a specific function in the data quality workflow:

- **QualityCheck**: This is the fundamental building block that defines what you want to check (like neutron counts), how you want to check it (like range validation), and the specific thresholds or criteria to use.
- **QualityAssessmentFlagBuilder**: Collects multiple quality checks into a cohesive set
- **DataQualityAssessor**: Applies quality checks to data and manages the SaQC integration
- **QAMethod**: This is a set of pre-defined checking methods you can choose from, such as range checks (is the value between X and Y?), spike detection, or constant value detection.
- **QATarget**: This defines which data columns in your CRNS dataset you want to check, such as raw neutron counts, air pressure, or humidity measurements.

## Getting Started

### Creating Quality Checks

Quality checks are created using the `QualityCheck` class, which requires three key pieces of information:

1. **Target**: What data column to check (using `QATarget` enum)
2. **Method**: What type of check to perform (using `QAMethod` enum)
3. **Parameters**: Configuration parameters specific to the method (provided as a dictionary)

```python
from neptoon.quality_control import QualityCheck, QAMethod, QATarget

# Create a range check for neutron counts
neutron_range_check = QualityCheck(
    target=QATarget.RAW_EPI_NEUTRONS,
    method=QAMethod.RANGE_CHECK,
    parameters={
        "min": 500,  # Minimum acceptable value
        "max": 2000  # Maximum acceptable value
    }
)

# Create a spike detection check for air pressure
pressure_spike_check = QualityCheck(
    target=QATarget.AIR_PRESSURE,
    method=QAMethod.SPIKE_UNILOF,  # Univariate Local Outlier Factor method
    parameters={
        "periods_in_calculation": 24,  # Look at 24 time periods
        "threshold": 2.0             # Sensitivity threshold
    }
)
```

### Building a Set of Quality Checks

Multiple quality checks can be combined using the `QualityAssessmentFlagBuilder`:

```python
from neptoon.quality_control import QualityAssessmentFlagBuilder

# Create a flag builder
flag_builder = QualityAssessmentFlagBuilder()

# Add multiple checks
flag_builder.add_check(neutron_range_check)
flag_builder.add_check(pressure_spike_check)

# Alternatively, add multiple checks at once
flag_builder.add_check(neutron_range_check, pressure_spike_check)
```

### Applying Quality Checks to Data

Once you have defined your quality checks, you can apply them to your data using the `DataQualityAssessor`:

```python
from neptoon.quality_control import DataQualityAssessor
from neptoon.hub import CRNSDataHub

# Assuming you have a CRNSDataHub with data
data_hub = CRNSDataHub(crns_data_frame=your_data_frame)

# Add quality checks
data_hub.add_quality_flags(custom_flags=flag_builder)

# Apply the quality checks
data_hub.apply_quality_flags()

# The flagged data is now masked in the data_hub.crns_data_frame
# The flags themselves are in data_hub.flags_data_frame
```

## Quality Check Methods

neptoon provides several quality check methods through the `QAMethod` enum:

| Method | Description | Common Parameters |
|--------|-------------|-------------------|
| `RANGE_CHECK` | Flags values outside a specified range | `min`, `max` |
| `SPIKE_UNILOF` | Detects spikes using the univariate Local Outlier Factor algorithm | `periods_in_calculation`, `threshold` |
| `CONSTANT` | Flags periods where values remain constant | - |
| `ABOVE_N0` | Flags neutron counts above a factor of the N0 calibration value | `N0`, `percent_maximum` |
| `BELOW_N0_FACTOR` | Flags neutron counts below a factor of the N0 calibration value | `N0`, `percent_minimum` |

## Finding Required Parameters

To discover what parameters are required for a specific quality check method, use the `WhatParamsDoINeed` utility:

```python
from neptoon.quality_control import WhatParamsDoINeed, QAMethod

# Display parameter information for a method
WhatParamsDoINeed(QAMethod.RANGE_CHECK)
```

This will print detailed information about required and optional parameters for the specified method.

## Quality Check Targets

The following data columns can be targeted for quality checks via the `QATarget` enum:

| Target | Description |
|--------|-------------|
| `RAW_EPI_NEUTRONS` | Raw epithermal neutron counts |
| `CORRECTED_EPI_NEUTRONS` | Corrected epithermal neutron counts |
| `RELATIVE_HUMIDITY` | Air relative humidity |
| `AIR_PRESSURE` | Atmospheric pressure |
| `TEMPERATURE` | Air temperature |
| `SOIL_MOISTURE` | Calculated soil moisture |
| `CUSTOM` | User-defined column (requires specifying `column_name` in parameters) |

## Advanced Usage

### Custom Quality Check Targets

To quality-check a column not covered by the standard `QATarget` enum:

```python
from neptoon.quality_control import QualityCheck, QAMethod, QATarget

custom_check = QualityCheck(
    target=QATarget.CUSTOM,
    method=QAMethod.RANGE_CHECK,
    parameters={
        "column_name": "your_custom_column_name",  # Specify the column name
        "min": 0,
        "max": 100
    }
)
```

### Changing the SaQC Flagging Scheme

neptoon uses SaQC's "simple" flagging scheme by default, but you can change this:

```python
quality_assessor = DataQualityAssessor(data_frame=your_data_frame)
quality_assessor.change_saqc_scheme("dmp")  # Other options: "float", "positional", "annotated-float"
```

### Direct Access to Flags

You can access the generated flags directly:

```python
# Get the flags dataframe
flags_df = data_hub.flags_data_frame

# Values are "UNFLAGGED" or specific flags (depends on the SaQC scheme)
print(flags_df.head())
```

## Recommendations for CRNS Data

For CRNS data, we recommend the following quality checks as a starting point:

1. **Neutron count range check**:
   ```python
   QualityCheck(
       target=QATarget.RAW_EPI_NEUTRONS,
       method=QAMethod.RANGE_CHECK,
       parameters={"min": 500, "max": 3000}
   )
   ```

2. **Pressure anomaly check**:
   ```python
   QualityCheck(
       target=QATarget.AIR_PRESSURE,
       method=QAMethod.RANGE_CHECK,
       parameters={"min": 800, "max": 1100}
   )
   ```

3. **Humidity range check**:
   ```python
   QualityCheck(
       target=QATarget.RELATIVE_HUMIDITY,
       method=QAMethod.RANGE_CHECK,
       parameters={"min": 0, "max": 100}
   )
   ```

4. **Neutron spike detection**:
   ```python
   QualityCheck(
       target=QATarget.CORRECTED_EPI_NEUTRONS,
       method=QAMethod.SPIKE_UNILOF,
       parameters={"periods_in_calculation": 12}
   )
   ```

These values should be adjusted based on your specific site characteristics and sensor properties.

## Integration with Data Processing Pipeline

Quality assessment is typically performed after corrections have been applied but before soil moisture conversion:

```python
# Abbreviated workflow
data_hub.correct_neutrons()  # Apply corrections first
data_hub.add_quality_flags(custom_flags=flag_builder)
data_hub.apply_quality_flags()  # Apply QA
data_hub.produce_soil_moisture_estimates()  # Then calculate soil moisture
```

This ensures that quality checks can be applied to both raw and corrected data, but soil moisture is only calculated from quality-controlled data.
