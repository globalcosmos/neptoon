
<style>
/*number of ".md-nav__list" determines the max level of TOC to be displayed in TOC*/
/*e.g. if ".md-nav__list" is repeated 2 times - the headers ###, ####, #####,  ... will not be displayed in TOC*/
.md-sidebar--secondary .md-nav__list .md-nav__list .md-nav__list .md-nav__list {display: none}
</style>

## Overview
The process configuration file tells neptoon about the sensor being processed. The sections in this file are: config, neutron_quality_assessment, correction_steps, and data_smoothing. Below is an example file which you can use a starting point for your own sensor.

```yaml
--8<-- "./examples/v1_processing_method.yaml"
```

# Configuration Quick Reference Guide

## Neutron Quality Assessment

### Raw Neutron Quality Control Parameters

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| spike_uni_lof.periods_in_calculation | Yes | integer | `12` | Number of time periods used in Local Outlier Factor calculation |
| spike_uni_lof.threshold | Yes | float | `2.0` | Threshold value for spike detection using LOF algorithm |

### Corrected Neutron Quality Control Parameters

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| greater_than_N0.percent_maximum | Yes | float | `1.075` | Maximum allowed neutron count as percentage of N0 (Köhli 2021) |
| below_N0_factor.percent_minimum | Yes | float | `0.3` | Minimum allowed neutron count as percentage of N0 |

## Correction Steps

### Air Humidity Correction

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"rosolem_2013"` | Method used for humidity correction |
| omega | Yes | float | `0.0054` | Correction coefficient for humidity |
| humidity_ref | Yes | float | `0` | Reference humidity value for correction |

### Air Pressure Correction

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"zreda_2012"` | Method used for pressure correction |
| dunai_inclination | No | float | - | Inclination parameter for dunai method |

### Incoming Intensity Correction

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"hawdon_2014"` or<br> `"zreda_2012"` or `"mcjannet_desilets_2023"` | Method used for incoming intensity correction |
| reference_neutron_monitor.station | Yes | string | `"JUNG"` or<br> `"SOPO"` or<br> `"OULU"` or<br> `"PSNM"` or<br> `"MXCO"` or<br> `"AATA"` or<br> `"INVK"` or<br> `"KIEL"` | Reference neutron monitor station |
| reference_neutron_monitor.resolution | Yes | integer | `60` | Time resolution in minutes |
| reference_neutron_monitor.nmdb_table | Yes | string | `"revori"` or `"ori"`| NMDB table name (revori recommended) |

### Above Ground Biomass Correction

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | No | string | `"baatz_2015"` or `"morris_2024"` | Method used for biomass correction |
| biomass_units | No | string | - | Units for biomass measurements |

### Soil Moisture Estimation

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"desilets_etal_2010"` or `"koehli_etal_2021"` | Method for converting neutrons to soil mositure|
|koehli_method_form|No|string|`"Jan23_uranos"` or `"Jan23_mcnpfull"` or `"Mar12_atmprof"` or `"Mar21_mcnp_drf"` or `"Mar21_mcnp_ewin"` or `"Mar21_uranos_drf"` or `"Mar21_uranos_ewin"` or `"Mar22_mcnp_drf_Jan"` or `"Mar22_mcnp_ewin_gd"` or `"Mar22_uranos_drf_gd"` or `"Mar22_uranos_ewin_chi2"` or `"Mar22_uranos_drf_h200m"` or `"Aug08_mcnp_drf"` or `"Aug08_mcnp_ewin"` or `"Aug12_uranos_drf"` or `"Aug12_uranos_ewin"` or `"Aug13_uranos_atmprof"` or `"Aug13_uranos_atmprof2"`| Thats a lot of options... just stick with `"Mar21_uranos_drf"` if you want simple. This sets the parameters when using the koehlie et al., 2021 method|


## Data Smoothing

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| smooth_corrected_neutrons | Yes | boolean | `true` | Enable smoothing for corrected neutron counts |
| smooth_soil_moisture | Yes | boolean | `false` | Enable smoothing for soil moisture data |
| settings.algorithm | Yes | string | `"rolling_mean"` | Smoothing algorithm selection |
| settings.window | Yes | string | `12h` or `12hours` or `1day` or `1d` or `30min` or `30m` | Window size for smoothing operation, provided as a string which neptoon will automatically parse into a timedelta window |
| settings.poly_order | Yes | integer | `4` | Polynomial order for Savitzky-Golay filter (Currently not used)|

!!! note "Additional Information"
    - The smoothing algorithm supports only `rolling_mean` until a future update. 
