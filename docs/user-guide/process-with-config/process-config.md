
<style>
/*number of ".md-nav__list" determines the max level of TOC to be displayed in TOC*/
/*e.g. if ".md-nav__list" is repeated 2 times - the headers ###, ####, #####,  ... will not be displayed in TOC*/
.md-sidebar--secondary .md-nav__list .md-nav__list .md-nav__list .md-nav__list {display: none}
</style>

## Overview
The process configuration file tells neptoon about the sensor being processed. The sections in this file are: config, neutron_quality_assessment, correction_steps, and data_smoothing. Below is an example file which you can use a starting point for your own sensor.

### Cosmos Standard

There are ongoing discussion in the community to set a standard for CRNS which users can use as a jumping off point. The standard is considered to be using established methods that have been tested in the field and produce good results. There are arguably better technique (and ones we've yet to discover) - we endeavour to keep up to date with the scienfitic knowledge. 

The below processing yaml will be up to date with the current standard. 

```yaml
--8<-- "./examples/v1_processing_method.yaml"
```

# Configuration Quick Reference Guide

## Neutron Quality Assessment

### Raw Neutron Quality Control Parameters

Here we conduct spike detection to account for problems in the raw count rate. There are a few algorithms to choose from, however we currently recommend using `spike_offset` with the defaults set to what you cna see in the above yaml file. This follows the current literature by identifying spikes as anything >20% of previous value.

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| spike_offset.threshold_relative | Yes | list | `[0.2, -0.2]` | Maximum percent (as decimal) that an observation can jump, before being designated a spike. Add two values in list format (with square brackets `[]`), one with a postive sign and one with a negative sign. Advised to stick to uniform.  |
| spike_offset.window | Yes | integer | `12h` | The window to use to identify whether a spike as returned back to base line after a plateau of spikes |

### Corrected Neutron Quality Control Parameters

These are some quality checks we do on corrected neutrons based on the literature. 

It's recommended to not touch this section unless your experimenting.

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| greater_than_N0.percent_maximum | Yes | float | `1.075` | Maximum allowed neutron count as percentage of N0 (Köhli 2021) |
| below_N0_factor.percent_minimum | Yes | float | `0.3` | Minimum allowed neutron count as percentage of N0 |

## Correction Steps

The following section is for applying corrections to the neutron count rate to account for additional influences, besides soil moisture, that influence the count rate. 

If you wish to turn off a particular correction - set the method to `"none"`. 

### Air Humidity Correction

Air humidity corrections can be left as the example values shown below when being applied as these are based on the literature. 

!!! warning "Köhli et al., 2021 method for neutron conversion"
    - If you are using the `koehli_etal_2021` method for neutron to soil moisture conversion - set the method to `"none"`. The humidity correction is integrated to this method already. (If you forget neptoon will disapply this correction during neutron conversion, but it's best to not apply it in the first place)


| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | No | string | `"rosolem_2013"` or `"none"` | Method used for humidity correction |
| omega | No | float | `0.0054` | Correction coefficient for humidity |
| humidity_ref | No | float | `0` | Reference humidity value for correction |

### Air Pressure Correction

Air pressure correction - very important to leave on as CRNS are very sensitive to atmospheric pressure changes. 

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"desilets_zreda_2003"` or `"desilets_2021"` or `"tirado_bueno_2021"` or `"none"` | Method used for pressure correction |
| dunai_inclination | No | float | - | Inclination parameter for dunai method |

### Incoming Intensity Correction


| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"hawdon_2014"` or<br> `"zreda_2012"` or<br> `"mcjannet_desilets_2023"` or<br> `"none"` | Method used for incoming intensity correction |
| reference_neutron_monitor.station | Yes | string | `"AATB"` or<br> `"INVK"` or<br> `"JUNG"` or<br> `"KERG"` or<br> `"KIEL"` or<br>`"MXCO"` or<br>`"NEWK"` or<br>`"OULU"` or<br>`"PSNM"` or<br>`"SOPO"` or<br>`"TERA"` or<br>`"THUL"` | Reference neutron monitor station |
| reference_neutron_monitor.resolution | Yes | integer | `60` | Time resolution in minutes |
| reference_neutron_monitor.nmdb_table | Yes | string | `"revori"` or `"ori"`| NMDB table name (revori recommended) |


### Above Ground Biomass Correction

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | No | string | `"baatz_2015"` or `"morris_2024"` or `"none"` | Method used for biomass correction |
| biomass_units | No | string | - | Units for biomass measurements |

### Soil Moisture Estimation

Here we state how we will convert neutrons to soil mositure. If you choose `koehli_etal_2021` then `koehli_method_form` is required.

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| method | Yes | string | `"desilets_etal_2010"` or `"koehli_etal_2021"` or `"none"` | Method for converting neutrons to soil mositure|
|koehli_etal_2021_parameterset| No | string |`"Jan23_uranos"` or `"Jan23_mcnpfull"` or `"Mar12_atmprof"` or `"Mar21_mcnp_drf"` or `"Mar21_mcnp_ewin"` or `"Mar21_uranos_drf"` or `"Mar21_uranos_ewin"` or `"Mar22_mcnp_drf_Jan"` or `"Mar22_mcnp_ewin_gd"` or `"Mar22_uranos_drf_gd"` or `"Mar22_uranos_ewin_chi2"` or `"Mar22_uranos_drf_h200m"` or `"Aug08_mcnp_drf"` or `"Aug08_mcnp_ewin"` or `"Aug12_uranos_drf"` or `"Aug12_uranos_ewin"` or `"Aug13_uranos_atmprof"` or `"Aug13_uranos_atmprof2"`| Thats a lot of options... just stick with `"Mar21_mcnp_drf"` if you want simple. This sets the parameters when using the koehlie et al., 2021 method|


## Data Smoothing

In this section we state whether to do smoothing on the neutron data, and how to do it. The boolean statement is required. If this is set to `true` then the further options need to be set too, otherwise they can be left blank.


| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| smooth_corrected_neutrons | Yes | boolean | `true` | Enable smoothing for corrected neutron counts |
| smooth_soil_moisture | Yes | boolean | `false` | Enable smoothing for soil moisture data |
| settings.algorithm | No | string | `"rolling_mean"` | Smoothing algorithm selection |
| settings.window | No | string | `12h` or `12hours` or `1day` or `1d` or `30min` or `30m` | Window size for smoothing operation, provided as a string which neptoon will automatically parse into a timedelta window |
| settings.min_proportion_good_data | No | float | `0.7` | The minimum proportion of available data for the smoothing window to succeed. If less than this is available in the window the observation is `nan` |

!!! note "Additional Information"
    - The smoothing algorithm supports only `rolling_mean` until a future update. 

## Temporal Aggregation

In this section we state whether to do smoothing on the neutron data, and how to do it. 

The boolean statements are required. If they are set to `true` then the further options need to be set too, otherwise they can be left blank. 

Alignment is used if you want to have your data output on rounded time points, but don't wish to change the resolution of your data (e.g., data at `15:04` realigned to be at `15:00`). 

Aggregation does what it says, converts your data to a new resolution via aggregation. The output_resolution should be larger than original timestep resolution of your data (no downscaling). 

More info on this found [here](https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.resample)

| Parameter | Required | Type | Example | Description |
|-----------|----------|------|---------|-------------|
| aggregate_data | Yes | boolean |  `true` or `false` | Whether to aggregate data |
| output_resolution | No | string | `1h` or `None` | Desired time step of output data. Should be pandas style FreqStr (e.g., `1h`, `1m`) |
| aggregate_method | No | string | `bagg` | Method for data aggregation |
| aggregate_func | No | string | `mean` | Function used for aggregation |
| aggregate_maxna_fraction | No | float | `0.3` | Maximum allowed fraction of NA values in the aggregation period |
| align_timestamps | Yes | boolean | `true` or `false` | Whether to align timestamps |
| alignment_method | No | string | `time` | Method for timestamp alignment |