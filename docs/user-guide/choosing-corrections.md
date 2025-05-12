# Corrections Module

## Introduction

Neutron corrections are critical in getting CRNS soil moisture estimates. It is here that we are removing the impact of additional influence on the neutron signal, besides soil moisture. Doing this means that changes in the neutron count rate can be considered as coming from changes in soil moisture only.

## Why are corrections important?

For the CRNS to work, we want changes in neutron count rates to reflect changes in soil moisture dynamics as closely as possible. However, CRNS measurements are affected by several environmental factors beyond soil moisture:

- **Atmospheric pressure** - Higher pressure reduces neutron counts by increasing atmospheric shielding
- **Incoming neutron intensity** - Variations in cosmic ray intensity affect the baseline neutron flux
- **Atmospheric humidity** - Water vapor in the air moderates neutrons before they reach the ground
- **Above-ground biomass** - Plant matter can moderate neutrons similarly to soil water

## Using Corrections with CRNSDataHub

You can apply corrections through the `CRNSDataHub` interface:

```python
from neptoon.hub import CRNSDataHub
from neptoon.corrections.factory.build_corrections import CorrectionType, CorrectionTheory

# Create data hub (with data already loaded)
data_hub = CRNSDataHub(crns_data_frame=your_data, sensor_info=your_sensor_info)

# apply previous processing steps....

# Select corrections to apply - using all default theories
data_hub.select_correction(correction_type=CorrectionType.PRESSURE)
data_hub.select_correction(correction_type=CorrectionType.INCOMING_INTENSITY)
data_hub.select_correction(correction_type=CorrectionType.HUMIDITY)

# Apply all selected corrections
data_hub.correct_neutrons()
```

Alternatively it's possible to be selective on the specific theory to apply:

```python
from neptoon.hub import CRNSDataHub
from neptoon.corrections.factory.build_corrections import CorrectionType, CorrectionTheory

# Create data hub (with data already loaded)
data_hub = CRNSDataHub(crns_data_frame=your_data, sensor_info=your_sensor_info)

# apply previous processing steps....

# Select corrections to apply - using all default theories
data_hub.select_correction(correction_type=CorrectionType.PRESSURE)
data_hub.select_correction(correction_type=CorrectionType.HUMIDITY)

# Select specific theory
data_hub.select_correction(
	correction_type=CorrectionType.INCOMING_INTENSITY,
	correction_theory=CorrectionTheory.HAWDON_2014
	)

# Apply all selected corrections
data_hub.correct_neutrons()

```

## The Corrections

### Pressure Correction

The pressure correction accounts for the influence of atmospheric pressure on neutron count rates. Higher pressure means more air mass above the sensor, which attenuates more cosmic rays.

!!! important "Reference Pressure"
    The reference pressure should ideally be the long-term average atmospheric pressure at your site. Changing this value will affect your calibration parameters, so document what reference value you use.

### Incoming Intensity Correction

This correction accounts for temporal variations in the cosmic ray flux, which can change due to solar activity and other space weather phenomena.

Available theoretical implementations:

| Theory | Description | 
|--------|-------------|
| `ZREDA_2012` | Original implementation without cutoff rigidity adjustment |
| `HAWDON_2014` | Includes cutoff rigidity adjustment |
| `MCJANNET_DESILETS_2023` | Advanced implementation with atmospheric depth considerations |

### Humidity Correction

The humidity correction accounts for the moderating effect of atmospheric water vapor on neutrons. This can be calculated when relative humidity and temperature sensors are present.

### Above-ground Biomass Correction

This correction accounts for neutron moderation by vegetation biomass.

Available theoretical implementations:

| Theory | Description | 
|--------|-------------|
| `BAATZ_2015` | Based on biomass in kg/m² | 
| `MORRIS_2024` | Based on biomass water equivalent in mm | 

## Scientific References

The corrections implemented in this module are based on peer-reviewed scientific literature:

- **Pressure Correction**: Based on exponential attenuation of cosmic rays in the atmosphere, from [Zreda et al., 2012](https://doi.org/10.5194/hess-16-4079-2012)
- **Incoming Intensity**: Methods from [Zreda et al., 2012](https://doi.org/10.5194/hess-16-4079-2012), [Hawdon et al., 2014](https://doi.org/10.1002/2013WR015138) and [McJannet & Desilets, 2023](https://doi.org/10.1029/2022WR033889)
- **Humidity Correction**: From [Rosolem et al., 2013](https://doi.org/10.1175/JHM-D-12-0120.1)
- **Biomass Correction**: Methods from [Baatz et al., 2015](https://doi.org/10.5194/hess-19-3203-2015) and [Morris et al., 2024](https://doi.org/10.3390/s24134094)
