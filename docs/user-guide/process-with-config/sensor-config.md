
<style>
/*number of ".md-nav__list" determines the max level of TOC to be displayed in TOC*/
/*e.g. if ".md-nav__list" is repeated 2 times - the headers ###, ####, #####,  ... will not be displayed in TOC*/
.md-sidebar--secondary .md-nav__list .md-nav__list .md-nav__list .md-nav__list {display: none}
</style>

## Overview
The sensor configuration file tells neptoon about the sensor being processed. The sections in this file are: config, sensor_info, raw_data_parse_options, time_series_data, input_data_qa, soil_moisture_qa, calibration, data_storage and figures. Below is an example file which you can use a starting point for your own sensor, a quick start guide and a more detailed reference to each possiblility.

## File Structure

```yaml
--8<-- "./examples/A101_station.yaml"
```

# Configuration Quick Reference Guide

## Sensor Information

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| name | Yes | string | `Cunnesdorf_test_site` | Site identifier used for file naming and metadata |
| country | No | string | `Germany` | Country where sensor is located |
| identifier | No | string | `A102` | Unique sensor identifier code |
| install_date | Yes | string | `2016-10-21` | Date sensor was installed (YYYY-MM-DD) |
| latitude | Yes | float | `51.369597` | Site latitude in decimal degrees |
| longitude | Yes | float | `12.557120` | Site longitude in decimal degrees |
| elevation | Yes | float | `113` | Site elevation in meters |
| time_zone | Yes | string | `+1` | Time zone offset from UTC |
| site_cutoff_rigidity | Yes | float | `2.94` | Geomagnetic cutoff rigidity in GV |
| avg_lattice_water | No | float | `0.0043` | Average lattice water content as decimal (e.g., 0.0043 = 0.43%) |
| avg_soil_organic_carbon | No | float | `0.0184` | Soil organic carbon content as decimal (e.g., 0.0184 = 1.84%) |
| avg_dry_soil_bulk_density | No | float | `1.6` | Dry soil bulk density in g/cm³ |
| N0 | No | float | `1100` | Calibration parameter for neutron-to-soil moisture conversion |
| beta_coefficient | No | float | - | Site-specific coefficient for pressure correction |
| mean_pressure | No | float | - | Reference atmospheric pressure for corrections |


## Raw Data Parse Options

!!! tip "Requirements"
    For this section the `Required` column will change if you select `True` for `parse_raw_data`.

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| parse_raw_data | Yes | boolean | `True` | Toggle for raw data parsing functionality. When False, this entire section is ignored |
| data_location | No | Path | `"data/CRNS-station_data.zip"` | Path to raw data files/directory. Supports folders, zip, or tar archives |
| column_names | No | List[str] | `["date", "time", "counts"]` | Expected column names in order. If not provided, will attempt auto-detection |
| prefix | No | string | `"CRNS_"` | Filter raw files by filename prefix |
| suffix | No | string | `".dat"` or `.txt` | Filter raw files by filename suffix |
| encoding | No | string | `"cp850"` | File encoding format. Common alternatives: utf-8, ascii |
| skip_lines | No | integer | `2` | Number of header/metadata lines to skip before data |
| separator | No | string | `","` | Column delimiter character (e.g., comma, tab, semicolon) |
| decimal | No | string | `"."` | Decimal point character. |
| skip_initial_space | No | boolean | `True` | Remove leading whitespace in data fields |
| parser_kw | No | object | - | Advanced parser configuration |
| ├─ strip_left | No | boolean | `True` | Remove leading whitespace in fields |
| ├─ digit_first | No | boolean | `True` | Expect numeric data at start of line |
| starts_with | No | string | `"#"` | Required prefix for header lines |
| multi_header | No | boolean | `False` | Support for multi-line header formats |
| strip_names | No | boolean | `True` | Remove whitespace from column names |
| remove_prefix | No | string | `"//"` | Remove lines that start with this |

!!! note "Additional Information"
    - Paths in `data_location` can be absolute or relative to the configuration file
    - When `column_names` is not provided, the parser attempts to detect headers from the first file
    - For compressed data, both .zip and .tar formats are automatically detected and extracted

## Time Series Data

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| path_to_data | No | string | - | Path to pre-processed data (leave blank if parsing raw data) |
| input_resolution | Yes | string | `15mins` | Time step of input data |
| output_resolution | Yes | string | `1hour` or `None` | Desired time step of output data |
| align_timestamps | Yes | boolean | `true` | Whether to align timestamps |
| alignment_method | Yes | string | `time` | Method for timestamp alignment |
| aggregate_method | Yes | string | `bagg` | Method for data aggregation |
| aggregate_func | Yes | string | `mean` | Function used for aggregation |
| aggregate_maxna_fraction | Yes | float | `0.3` | Maximum allowed fraction of NA values |

### Key Column Information (Time Series Data)


| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| epithermal_neutron_columns | Yes | list | `[N2Cts]` | Columns containing epithermal neutron counts |
| thermal_neutron_columns | No | list | `[N1Cts]` | Columns containing thermal neutron counts |
| neutron_count_units | Yes | string | `absolute_count` or `counts_per_hour` or `counts_per_second` | Units for neutron measurements |
| pressure_columns | Yes | list | `[P4_mb, P3_mb, P1_mb]` | Pressure columns in priority order |
| pressure_units | Yes | string | `hectopascals` | Units for pressure measurements |
| pressure_merge_method | Yes | string | `priority` | How to handle multiple pressure columns |
| temperature_columns | Yes | list | `[T1_C, T2_C]` | Temperature measurement columns |
| temperature_units | Yes | string | `celcius` | Units for temperature measurements |
| temperature_merge_method | Yes | string | `priority` | How to handle multiple temperature columns |
| relative_humidity_columns | Yes | list | `[RH1]` | Relative humidity measurement columns |
| relative_humidity_units | Yes | string | `percent` | Units for humidity measurements |
| date_time_columns | Yes | list | `[Date Time(UTC)]` | Columns containing date/time data |
| date_time_format | Yes | string | `"%Y/%m/%d %H:%M:%S"` | Format string for parsing dates |

!!! note "Time Formats"
    DateTime format strings must be enclosed in quotes (e.g., `"%Y/%m/%d %H:%M:%S"`) to comply with YAML syntax.


## Quality Assessment Settings

See below for more details - this section can be as large or as small as desired

## Calibration

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| calibrate | Yes | boolean | `True` | Toggle for whether calibration will be done |
| data_format | No | string | `custom` | (WIP) automatic formatting for set styles |
| location | No | string | `home_dir/example_data/FSCD001_calibration.csv` | Location of the calibration data |
| date_time_format | No | string | `"%d.%m.%Y %H:%M"` | DateTime format of the calibration data|

### Key Column Names (Calibration)

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| date_time | No | string | `"DateTime_utc"` | Name of the column with DateTime |
| profile_id | No | string | `"Profile_ID"` |Name of the column with profile ID |
| sample_depth | No | string | `"Profile_Depth_cm"` | Name of the column with sample depth values |
| radial_distance_from_sensor | No | string | `"Distance_to_CRNS_m"`|Name of the column with distance of the sample from the sensor (m)|
| bulk_density_of_sample | No | string | `"DryBulkDensity_g_cm3"` | Name of the column with bulk density of the samples|
| gravimetric_soil_moisture | No | string | `"SoilMoisture_g_g"`| Name of the column with gravimetric soil moisture values |
| soil_organic_carbon | No | string | `"SoilOrganicCarbon_g_g"` | Name of the column with soil organic carbon values |
| lattice_water | No | string | `"LatticeWater_g_g"` | Name of the column with lattice water values |


## Data Storage

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| save_folder | No | string | - | Directory for saving outputs |
| append_yaml_hash_to_folder_name | No | boolean | `False` |(WIP) Add configuration hash to folder names |

## Figures

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| create_figures | Yes | boolean | `True` | Generate visualization figures |
| make_all_figures | Yes | boolean | `True` | Generate all available figure types in figure registry |
| custom_list | No | list | `[nmdb_incoming_radiation]` | List of specific figures to generate |


# Detailed Configuration Reference

## Sensor Information (`sensor_info`)

This section contains essential metadata about your Cosmic-Ray Neutron Sensor (CRNS) station and site characteristics. This information is crucial for accurate soil moisture estimation and data organization.


---
#### `name`
**Description**  
A unique identifier for the monitoring station that will be used in file naming and outputs.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Example**: `"Cunnesdorf_test_site"`

**Technical Details**

  - Should be URL-safe (avoid special characters)
  - Used as default folder name for outputs
  - Case-sensitive
  - No spaces recommended (use underscores)


---
#### `identifier`
**Description**  
The unique hardware identifier for the CRNS unit, typically provided by the manufacturer.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"A102"`


---
#### `install_date`
**Description**  
The date when the CRNS was installed at the monitoring site.

**Specification**

  - **Type**: Date string
  - **Format**: YYYY-MM-DD
  - **Required**: Yes
  - **Example**: `"2016-10-21"`

**Technical Details**

  - Used as cutoff for data processing
  - Single-digit months/days require leading zeros


---
#### `latitude` and `longitude`
**Description**  
Geographic coordinates of the CRNS installation location.

**Specification**

  - **Type**: float
  - **Required**: Yes
  - **Range**: -90 to 90 (latitude), -180 to 180 (longitude)
  - **Example**: `51.369597, 12.557120`

**Technical Details**

  - Decimal degrees format  

---
#### `elevation`
**Description**  

Height above sea level of the CRNS installation site.

**Specification**

  - **Type**: float
  - **Required**: Yes
  - **Units**: meters above sea level
  - **Example**: `113`

**Technical Details**

  - Used in atmospheric corrections
  - Affects pressure corrections
  - Important for neutron flux calculations

---
#### `site_cutoff_rigidity`
**Description**  
The geomagnetic cutoff rigidity at the installation site, which affects cosmic ray flux.

**Specification**

  - **Type**: float
  - **Required**: Yes
  - **Units**: GV (gigavolts)
  - **Example**: `2.94`

**Technical Details**

  - Affects incoming neutron corrections
  - Location-dependent parameter
  - www.crnslab.org provides methods to calculate this with latitude and longitude values


---
#### `avg_lattice_water`
**Description**  
The average lattice water content in soil minerals at the monitoring site. 

**Specification**

  - **Type**: float
  - **Required**: No
  - **Units**: g/g (decimal percentage)
  - **Example**: `0.0043`

**Technical Details**

  - Represented as decimal (0.0043 = 0.43%)
  - Site-specific constant
  - Used in soil moisture conversion
  - If not supplied defaults to 0
  - Can be automatically calculated if calibration sample data is provided with this in it (a site average is used)
---
#### `avg_soil_organic_carbon`
**Description**  
The average soil organic carbon content at the monitoring site.

**Specification**

  - **Type**: float
  - **Required**: No
  - **Units**: g/g (decimal percentage)
  - **Example**: `0.0184`

**Technical Details**

  - Represented as decimal (0.0184 = 1.84%)
  - If not supplied defaults to 0
  - Can be automatically calculated if calibration sample data is provided with this in it (a site average is used)
  - Used in soil moisture conversion equations


---
#### `avg_dry_soil_bulk_density`
**Description**  
The average dry soil bulk density across the CRNS footprint. This parameter is essential for converting gravimetric to volumetric soil moisture content.

**Specification**

  - **Type**: float
  - **Required**: No
  - **Units**: g/cm³
  - **Example**: `1.6`

**Technical Details**

  - Affects neutron-to-moisture conversion
  - Influences effective measurement depth
  - Can be automatically calculated if calibration sample data is provided with this in it (a site average is used)


---
#### `N0`
**Description**  
Site-specific calibration parameter that converts corrected neutron counts to soil moisture. This parameter is crucial for the accuracy of soil moisture measurements.

**Specification**

  - **Type**: float
  - **Required**: No
  - **Example**: `1100`

**Technical Details**

  - Determined through field calibration
  - Used in standard calibration function
  - Can be calibrated with soil sampling data if this option turned on

---
#### `beta_coefficient`
**Description**  
Site-specific coefficient used in the atmospheric pressure correction of neutron count rates. 

**Specification**

  - **Type**: float
  - **Required**: No
  - **Units**: hPa⁻¹
  - **Example**: `0.0076`

**Technical Details**

  - Used in pressure correction equations
  - Location and elevation dependent
  - Affects neutron count normalization
  - Will be automatically calculated in neptoon if not provided using elevation and lat/lon data

---
#### `mean_pressure`
**Description**  
The long-term average atmospheric pressure at the monitoring site. Used as a reference pressure for neutron count corrections.

**Specification**

  - **Type**: float
  - **Required**: No
  - **Units**: hPa (hectopascals)
  - **Example**: `1013.25`

**Technical Details**

  - Used for pressure corrections
  - Elevation dependent
  - Will be automatically calculated in neptoon if not provided using elevation and lat/lon data


---
#### `time_zone`
**Description**  
The time zone offset from UTC for the monitoring site. Essential for proper temporal alignment of data.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Format**: ±H
  - **Example**: `"+1"` 


## Raw Data Parse Options (`raw_data_parse_options`)

This section configures how neptoon reads and interprets raw data files from CRNS sensors. These settings are crucial for correctly importing data from various sensor manufacturers and file formats.


---
#### `parse_raw_data`
**Description**  
Primary toggle that determines whether neptoon should process raw data files or expect pre-processed data.

**Specification**

  - **Type**: boolean
  - **Required**: Yes
  - **Example**: `True`

**Technical Details**

  - Controls entire raw data processing pipeline
  - Determines workflow path

---
#### `data_location`
**Description**  
Path to the raw data files or archive. Supports individual files, directories, or compressed archives.

**Specification**

  - **Type**: string (path)
  - **Required**: Yes (if parse_raw_data is True)
  - **Example**: `"data/CRNS-station_data.zip"` or `"../raw_data/"`

**Technical Details**

  - Supports absolute or relative paths
  - Handles zip and tar archives automatically
  - Recursive directory scanning
  - Path resolution relative to config file
  - Supported archive formats: .zip, .tar

---
#### `column_names`
**Description**  
Explicit list of column names in the order they appear in the raw data files. Provides direct control over column identification and naming.

**Specification**

  - **Type**: list[string]
  - **Required**: No
  - **Example**:
  ```yaml
  column_names:
    - date_time
    - neutron_counts
    - pressure_hpa
    - temperature_c
    - humidity_percent
  ```

**Technical Details**

  - Overrides automatic header detection
  - Case-sensitive matching
  - Maintains column order

---
#### `prefix`

**Description**

String pattern used to filter raw data files by their filename prefix.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: "CRNS_"

**Technical Details**

  - Case-sensitive matching
  - Used in file selection phase

---
**`suffix`**

**Description**
String pattern used to filter raw data files by their filename suffix.
**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: ".dat" or ".txt"

Technical Details

  - Case-sensitive matching
  - Include the dot for file extensions
  - Applied after prefix filtering

---

#### `skip_lines`
**Description**  
Number of lines to skip at the beginning of each data file.

**Specification**

  - **Type**: integer
  - **Required**: No
  - **Default**: `0`
  - **Example**: `3`

**Technical Details**

  - Affects all files in batch


---
#### `encoding`
**Description**  
Specifies the character encoding used in the raw data files. Critical for correct text interpretation, especially with international characters.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Default**: `"utf-8"`
  - **Example**: `"cp850"`

**Technical Details**

  - Common options:
    - `"utf-8"`: Universal encoding 
    - `"cp850"`: Windows Western European
    - `"ascii"`: 7-bit ASCII
    - `"latin1"`: ISO-8859-1


---
#### `separator`
**Description**  
Character used to separate columns in the raw data files. Must be explicitly defined to ensure correct data parsing.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Example**: `","`

**Technical Details**
  - Common separators:
    - `","`: CSV files
    - `"\t"`: Tab-separated
    - `";"`: European CSV
    - `"|"`: Pipe-separated
  - Must be in quotes
------

#### `decimal`
**Description**  
Character used as decimal separator in numeric values. 

**Specification**

  - **Type**: string
  - **Required**: No
  - **Default**: `"."`
  - **Example**: `","`

**Technical Details**

  - Must be in quotes

---
#### `skip_initial_space`
**Description**  
Controls whether leading whitespace in data fields should be removed during parsing.

**Specification**

  - **Type**: boolean
  - **Required**: No
  - **Default**: `True`
  - **Example**: `True`


---
#### `parser_kw`
**Description**  
AAdditional parser key words

**Specification**

  - **Type**: object
  - **Required**: No
  - **Properties**:
    - `strip_left`: boolean - Remove leading whitespace
    - `digit_first`: boolean - Expect numeric data at start

**Technical Details**

  - Specialized parsing behavior
  - Applied during data import

---
#### `starts_with`
**Description**  
String pattern that identifies header lines in the data files.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Default**: `""`
  - **Example**: `"#"`

**Technical Details**

  - Used in header detection
  - Case-sensitive matching


---
#### `multi_header`
**Description**  
  Indicates whether data files contain multiple header lines that need special processing.

**Specification**

  - **Type**: boolean
  - **Required**: No
  - **Default**: `False`
  - **Example**: `False`



---
#### `strip_names`
**Description**  
Controls whether whitespace should be removed from column names during parsing.

**Specification**

  - **Type**: boolean
  - **Required**: No
  - **Default**: `True`
  - **Example**: `True`

**Technical Details**

  - Applied to column headers
  - Affects column name matching


---
#### `remove_prefix`
**Description**  
String pattern to be removed from the beginning of column names.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"//"`

**Technical Details**

  - Must be in quotes
  - Used for cleanup of raw headers
---



---

## Time Series Data (`time_series_data`)

This section defines how data is formatted ready for use in neptoon. It presumes that the format has already been compiled into a `.csv` format.

---
#### `path_to_data`
**Description**  
The path to the .csv containing time series data

**Specification**

  - **Type**: string
  - **Required**: Yes (if no parsing done)
  - **Example**: `/path/to/data.csv`

## Temporal Configuration (`time_series_data.temporal`)

---
#### `input_resolution`
**Description**  
Specifies the time step of the input data, critical for proper temporal processing and aggregation.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Format**: `<number><unit>`
  - **Example**: `"15mins"` or `"1hour"`

**Technical Details**

  - Valid units:
    - Minutes: "min", "minute", "minutes"
    - Hours: "hour", "hours", "hr", "hrs"
    - Days: "day", "days"
  - Number must be positive integer

---
#### `output_resolution`
**Description**  
Desired time step for processed data output. Determines the temporal resolution of final results.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Format**: `<number><unit>` or `"None"`
  - **Example**: `"1hour"`

**Technical Details**

  - Must be greater than or equal to input_resolution
  - Use "None" to maintain input resolution
  - When different from input aggregation will occur

---
#### `align_timestamps`
**Description**  
Controls whether timestamps should be aligned to regular intervals.

**Specification**

  - **Type**: boolean
  - **Required**: Yes
  - **Example**: `true`

**Technical Details**

  - Ensures consistent temporal spacing
  - Affects data aggregation methods
  - If aggregation occurs this is ignored (already aligned)

---
#### `alignment_method`
**Description**  
Specifies how timestamps should be aligned when processing data.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Example**: `"time"`, `"nshift"`

**Technical Details**

  - "time": Aligns to clock intervals
  - "index": Maintains equal spacing
  - See [here](https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.align) for more details

### Key Column Configuration

---
#### `epithermal_neutron_columns`
**Description**  
Specifies which columns contain epithermal neutron count data, the primary measurement for soil moisture estimation.

**Specification**

  - **Type**: list[string]
  - **Required**: Yes
  - **Example**:
  ```yaml
  epithermal_neutron_columns:
    - N2Cts
    - ModNeutrons
  ```

**Technical Details**

  - Must match column names exactly

---
#### `thermal_neutron_columns`
**Description**  

Identifies columns containing thermal neutron count data, used for advanced corrections and quality control.

**Specification**

  - **Type**: list[string]
  - **Required**: No
  - **Example**:
  ```yaml
  thermal_neutron_columns:
    - N1Cts
  ```

**Technical Details**

  - Optional, recommended if available


---
#### `neutron_count_units`
**Description**  
Specifies the units of the neutron count measurements.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Options**: 
    - `"absolute_count"`
    - `"counts_per_hour"`
    - `"counts_per_second"`
  - **Example**: `"absolute_count"`

**Technical Details**

  - Affects count rate calculations
  - Critical for cross-site comparisons
  - Must match sensor configuration
  - Internally counts are converted into absolute counts (raw) and counts_per_hour (corrected)

---
#### `pressure_columns`
**Description**  
List of columns containing atmospheric pressure measurements, in order of priority.

**Specification**

  - **Type**: list[string]
  - **Required**: Yes
  - **Example**:
  ```yaml
  pressure_columns:
    - P4_mb  # Primary sensor
    - P3_mb  # Backup sensor
    - P1_mb  # Tertiary sensor
  ```

**Technical Details**

  - Order determines priority in 'priority' merge method
  - All must use same units

---
#### `pressure_units`
**Description**  
Units of the pressure measurements in the specified columns.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Options**: `"hectopascals"`, `"millibars"`
  - **Example**: `"hectopascals"`

**Technical Details**

  - Must be consistent across all pressure columns
  - Standard is hectopascals

---
#### `pressure_merge_method`
**Description**  
Method used to combine multiple pressure measurements when available.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Options**: `"priority"`, `"mean"`
  - **Example**: `"priority"`

**Technical Details**

  - "priority": Uses highest priority available
  - "mean": Averages all available values
  - Handles missing data automatically

---
#### `temperature_columns`
**Description**  
List of columns containing air temperature measurements, in order of priority.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Example**:
  ```yaml
  temperature_columns:
    - T1_C
    - T2_C
  ```

**Technical Details**

  - Order determines priority
  - All must use same units
  - Used in humidity corrections

---
#### `temperature_units`
**Description**  
Units of the temperature measurements.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Options**: `"celcius"`, `"kelvin"`, `"fahrenheit"`
  - **Example**: `"celcius"`

**Technical Details**

  - Must be consistent across all temperature columns


---
#### `temperature_merge_method`
**Description**  
Method used to combine multiple temperature measurements when available.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Options**: `"priority"`, `"mean"`
  - **Example**: `"priority"`

**Technical Details**

  - Follows same logic as pressure_merge_method


---
#### `date_time_columns`
**Description**  
Columns containing temporal information for measurements.

**Specification**

  - **Type**: list[string]
  - **Required**: Yes
  - **Example**: `["Date Time(UTC)"]`

**Technical Details**

  - Must contain valid datetime information
  - Used for all temporal alignment
  - Critical for data processing
  - Multiple columns can be merged e.g., `['Date', 'Time']`

---
#### `date_time_format`
**Description**  
Format string specifying how datetime information is encoded.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Format**: Python datetime format string
  - **Example**: `"%Y/%m/%d %H:%M:%S"`

**Technical Details**

  - Must be in quotes
  - Follows Python strftime format

---

#### `initial_time_zone`
**Description**  
Timezone of data. Most CRNS data is given in UTC, but if it's not we can handle that here.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Example**: `utc` or `Europe/Berlin`



---
#### `convert_time_zone_to`
**Description**  
Timezone to convert data to **STRONG** recommendation to leave this as utc.

**Specification**

  - **Type**: string
  - **Required**: Yes
  - **Example**: `utc`

**Technical Details**


---

---
## Quality Assessment Configuration

The Quality Assessment (QA) system in neptoon allows you to validate meteorological data used in soil moisture estimation. The system currently supports QA checks on three key meteorological variables and provides two different assessment methods.

### Supported Variables
Quality assessment can be performed on the following meteorological variables:

  - `air_relative_humidity`  
  - `air_pressure`  
  - `air_temperature`  

For QA on soil moisture data the style is like:

```yaml
soil_moisture_qa:
  soil_moisture:
    flag_range:
      min: 0
      max: 1

```

### Assessment Methods

#### 1. Range Check (`flag_range`)
The range check method flags values that fall outside specified minimum and maximum thresholds.

##### Required Parameters
  - `min`: Minimum acceptable value (in data units)
  - `max`: Maximum acceptable value (in data units)

##### Example Configuration
```yaml
input_data_qa:
  air_pressure:
    flag_range:
      min: 850  # hPa
      max: 1050 # hPa
  
  air_relative_humidity:
    flag_range:
      min: 0    # %
      max: 100  # %
  
  air_temperature:
    flag_range:
      min: -30  # °C
      max: 50   # °C
```

#### 2. Univariate Local Outlier Factor (`spike_uni_lof`)
This method uses the Local Outlier Factor algorithm to detect anomalies in univariate time series data. More information on this [here](https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.flagUniLOF)

##### Optional Parameters
- `periods_in_calculation`: Number of time steps included in LOF calculation
    - Default: 20
    - Units: time steps
  
- `threshold`: Threshold for flagging outliers
    - Default: 1.5
    - Units: decimal
  
- `algorithm`: Algorithm for calculating nearest neighbors
    - Default: "ball_tree"
    - Options: ["ball_tree", "kd_tree", "brute", "auto"]

##### Example Configuration
```yaml
input_data_qa:
  air_temperature:
    spike_uni_lof:
      periods_in_calculation: 24  # Use 24 time steps
      threshold: 2.0             # More permissive threshold
      algorithm: "ball_tree"     # Default algorithm
```

#### Complete Example
Here's a complete example showing how to combine both methods:

```yaml
input_data_qa:
  air_pressure:
    flag_range:
      min: 850
      max: 1050
    spike_uni_lof:
      periods_in_calculation: 12
      threshold: 1.8
  
  air_relative_humidity:
    flag_range:
      min: 0
      max: 100
    spike_uni_lof:
      periods_in_calculation: 6
      threshold: 1.3
  
  air_temperature:
    flag_range:
      min: -30
      max: 50
```

##### Best Practices

1. **Range Selection**
    - Choose ranges based on physically possible values for your location
    - Consider seasonal variations when setting thresholds

2. **LOF Parameters**
    - `periods_in_calculation`: Choose based on your data's temporal resolution
    - Hourly data: 24 periods = 1 day window
    - 15-min data: 96 periods = 1 day window
    - `threshold`: Start conservative (1.5) and adjust based on results
    - `algorithm`: Use default unless you have specific performance requirements

##### Notes
  - QA configuration is optional but recommended
  - Methods can be applied individually or in combination
  - Configuration is applied during data processing via the CRNSDataHub
  - Flagged data will be excluded from subsequent processing steps

---

---


## Calibration (`calibration`)


#### `calibrate`
**Description**  
Toggle for whether calibration will be done.

**Specification**

  - **Type**: boolean
  - **Required**: Yes
  - **Example**: `True`

---
#### `data_format`
**Description**  
(WIP) automatic formatting for set styles.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `custom`
---
#### `location`
**Description**  
Location of the calibration data.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `home_dir/example_data/FSCD001_calibration.csv`
---
#### `date_time_format`
**Description**  
DateTime format of the calibration data.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"%d.%m.%Y %H:%M"`
---
## Key Column Names (`calibration.key_column_names`)

#### `date_time`
**Description**  
Name of the column with DateTime.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"DateTime_utc"`

---
#### `profile_id`
**Description**  
Name of the column with profile ID.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"Profile_ID"`

---
#### `sample_depth`
**Description**  
Name of the column with sample depth values.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"Profile_Depth_cm"`

---
#### `radial_distance_from_sensor`
**Description**  
Name of the column with distance of the sample from the sensor (m).

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"Distance_to_CRNS_m"`

---
#### `bulk_density_of_sample`
**Description**  
Name of the column with bulk density of the samples.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"DryBulkDensity_g_cm3"`

---
#### `gravimetric_soil_moisture`
**Description**  
Name of the column with gravimetric soil moisture values.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"SoilMoisture_g_g"`

---
#### `soil_organic_carbon`
**Description**  
Name of the column with soil organic carbon values.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"SoilOrganicCarbon_g_g"`

---
#### `lattice_water`
**Description**  
Name of the column with lattice water values.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: `"LatticeWater_g_g"`

---

---

## Data Storage Options (`data_storage`)

---
#### `save_folder`
**Description**  
Directory for saving outputs.

**Specification**

  - **Type**: string
  - **Required**: No
  - **Example**: -

**Technical Details**

  - If left blank it saves in the working directory from where the script is run

---
#### `append_yaml_hash_to_folder_name`
**Description**  
(WIP) Add configuration hash to folder names.

**Specification**

  - **Type**: boolean
  - **Required**: No
  - **Example**: `False`

**Technical Details**

  - Work In Progress - check back soon

---
#### `create_report`
**Description**  
Whether to create the pdf report during the processing run. When selected the Magazine system is turned on and information and figures are prepared in a report and saved with the data.

**Specification**

  - **Type**: boolean
  - **Required**: Yes
  - **Example**: `True`


---
---

## Figures Options (`figures`)

---
#### `create_figures`
**Description**  
Generate visualization figures and automatically store them when saved.

**Specification**

  - **Type**: boolean
  - **Required**: Yes
  - **Example**: `True`

**Technical Details**
  
  - Figures are saved in the folder when saved

---
#### `make_all_figures`
**Description**  
Generate all available figure types in figure registry.

**Specification**

  - **Type**: boolean
  - **Required**: Yes
  - **Example**: `True`

---
#### `custom_list`
**Description**  
List of specific figures to generate if not doing all

**Specification**

  - **Type**: list
  - **Required**: No
  - **Example**: `[nmdb_incoming_radiation]`

**Technical Details**

  - If `make_all_figures` is true this is ignored.