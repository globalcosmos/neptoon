# Quality Assessment in neptoon

## Overview

The quality assessment (QA) system in neptoon provides tools to identify and flag bad data in CRNS time series. Built on top of [SaQC](https://rdm-software.pages.ufz.de/saqc/) framework, neptoon's QA system allows users to apply standardized quality checks to their data, helping to ensure that soil moisture estimates are based on reliable measurements.

## Key Components

The quality assessment system in neptoon is built from several interconnected parts:

- **QualityCheck**: This is the fundamental building block that defines what you want to check (like neutron counts), how you want to check it (like range validation), and the specific thresholds or criteria to use.
- **QualityAssessmentFlagBuilder**: Collects multiple quality checks into a set
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

For CRNS data processing, we recommend implementing the following quality checks as a starting point in your workflow:

### 1. Spike Detection on Raw Neutron Counts

Identify anomalous spikes in your raw neutron count data:

```python
QualityCheck(
    target=QATarget.RAW_EPI_NEUTRONS,
    method=QAMethod.SPIKE_UNILOF, 
    parameters={
        "periods_in_calculation": 24,  
        "threshold": 2.0              
    }
)
```

### 2. Meteorological Variable Validation

Ensure meteorological variables are within physically reasonable ranges:

```python
# Air pressure range check 
QualityCheck(
    target=QATarget.AIR_PRESSURE,
    method=QAMethod.RANGE_CHECK,
    parameters={"min": 800, "max": 1100} 
)

# Relative humidity range check
QualityCheck(
    target=QATarget.RELATIVE_HUMIDITY,
    method=QAMethod.RANGE_CHECK,
    parameters={"min": 0, "max": 100}  # Percentage (0-100%)
)

# Temperature checks....
```

!!! note "further processing here"
	At this point you would correct your neutrons and calibrate your sensor to get an N0 value

### 3. Calibration-Based Checks (Apply After Calibration)

After performing calibration and determining your N0 value, add these checks based on the N0:

```python
qa_flags_2 = QualityAssessmentFlagBuilder()
qa_flags_2.add_check(
    
    QualityCheck(
        target=QATarget.CORRECTED_EPI_NEUTRONS,
        method=QAMethod.ABOVE_N0,
        parameters={
            "percent_maximum":1.075,
            "N0":data_hub.sensor_info.N0
                }),

    QualityCheck(
        target=QATarget.CORRECTED_EPI_NEUTRONS,
        method=QAMethod.BELOW_N0_FACTOR,
        parameters={
            "N0":data_hub.sensor_info.N0,
            "percent_minimum":0.3
                }),
    )
data_hub.add_quality_flags(custom_flags=qa_flags_2)
data_hub.apply_quality_flags()
```

The parameter values presented here are general guidelines. You should adjust these values based on your:
- Site-specific environmental conditions
- Sensor model and characteristics
- Elevation and local atmospheric patterns
- Expected soil moisture range

These quality checks should be applied at appropriate stages in your processing pipeline: spike detection on raw data, meteorological variable validation before corrections, and N0-based checks after calibration has been performed.


