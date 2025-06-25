## Introduction

Calibration of a CRNS generally involves finding the so-called "N0" number. This number is the theorised maximum number of neutrons that will be counted by a sensor, over a defined time period, if conditions were **completely dry.** In neptoon we standardise all our counting rates to counts per hour (cph) and so our N0 number will always be the number of neutrons expected to be counted by a sensor, at a particular site, over a 1 hour integration window, in totally dry conditions. 

To convert neutrons to soil moisture we now take the ratio between the actual count rate vs the theorised dry count rate. This ratio places us on the calibration curve which can be seen in Figure 1 below (Franz et al., 2012). 


![N0 calibration curve showing the relationship between neutron counts and soil moisture.](N0-calib-curve.png){ width="70%" .center }

*Figure 1: N0 calibration curve showing the relationship between neutron counts and soil moisture.*
{ .caption .center }

!!! important "Neutron Correction"
	Neutron count rates are expected to be corrected by the time we get to calibration. The correction removes external influences on the neutron counts (e.g., changes in atmospheric pressure). So the N0 is a corrected term. More on corrections [here](choosing-corrections.md). This means that if you change your corrections steps you **must** recalibrate and get a new N0 number. If not your N0 and N numbers are being corrected differently!

### Weighting samples

The closer a sample is to the sensor, the greater weight it's soil moisture values should be given. The weighting procedure in neptoon is done automatically [(Schrön et al., 2017)](https://doi.org/10.5194/hess-21-5009-2017).

## Before you calibrate...

Before we begin lets describe whats expected at this stage. 

- You have a CRNSDataHub instance
- You have imported your CRNS data into the hub (more on that [here](importing-data.md))
- You have a SensorInformation in the hub (more on that [here](key-site-information.md))
- You have collected any external data you need (more on that [here](external-data.md))
- You have performed some quality assessment on your data (more on that [here](data-quality-checks.md))
- You have corrected your neutron counts so that you have a corrected neutrons column (more on that [here](choosing-corrections.md))

## Your sample data 

To calibrate a sensor, and calculate the N0 term, we need sample data from around the sensor.

The following columns are required in the calibration data:

: 1. **Date Time Column (`calib_data_date_time_column_name`):** The column name containing date and time information when samples were collected, formatted according to `calib_data_date_time_format` (default: '%d.%m.%Y %H:%M')
2. **Profile ID (`profile_id_column`):** Column containing unique identifiers for each soil sampling profile
3. **Distance to Sensor (`distance_column`):** Column with distances from the CRNS sensor to each sampling point in meters
4. **Sample Depth (`sample_depth_column`):** Column with the depth of each soil sample in centimeters
5. **Gravimetric Soil Moisture (`soil_moisture_gravimetric_column`):** Column containing soil moisture measurements in g/g (mass of water per mass of dry soil)
6. **Dry Bulk Density (`bulk_density_of_sample_column`):** Column with soil bulk density values in g/cm³ of each sample
7. **Soil Organic Carbon (`soil_organic_carbon_column`):** Column with soil organic carbon content in g/g of each sample (if missing can be set to 0)
8. **Lattice Water (`lattice_water_column`):** Column with lattice water content in g/g of each sample (if missing can be set to 0)

When multiple days of calibration data are available, these should all be supplied in the same file. Neptoon will automatically split them up using the DateTime column and complete calibration on each day separately, before finding an average N0.

!!! important "Soil Moisture Units"
    To be clear in neptoon we expect _gravimetric_ soil moisture values in the calibration data. In the literature describing the weighting (e.g., Schrön et al., 2017), volumetric units are used. We make this conversion internally.

## Adding this into the pipeline

Bringing this together - we must read in the sample data as a DataFrame, and create a `CalibrationConfiguration` object. This object lets neptoon know what the different columns are called in the sample data.

```python
from neptoon.calibration import CalibrationConfiguration
import pandas as pd

calib_df = pd.read_csv("example/data/path/calibration_data.csv")
data_hub.calibration_samples_data = calib_df

calibration_config = CalibrationConfiguration(
    calib_data_date_time_column_name='DateTime_utc',
    calib_data_date_time_format='%d.%m.%Y %H:%M', # Also include info on datetime format
    profile_id_column='Profile_ID',
    distance_column='Distance_to_CRNS_m',
    sample_depth_column='Profile_Depth_cm',
    soil_moisture_gravimetric_column='SoilMoisture_g_g',
    bulk_density_of_sample_column='DryBulkDensity_g_cm3',
    soil_organic_carbon_column='SoilOrganicCarbon_g_g',
    lattice_water_column='LatticeWater_g_g',
)
data_hub.calibrate_station(config=calibration_config)
```

After running this code neptoon will have undertaken calibration using the sample data supplied. Automatically weighting the samples according to the literature and producing an N0 number which is directly saved into the `SensorInfo` object. 

# Calibrate without CRNSDataHub

It's possible to calibrate your site more directly, without a data hub. For this you will need; 1. A dataframe with pre-corrected CRNS timeseries data and 2. your sample data. For example, you could save your dataframe in your datahub just before calibration and use this to test different variations of your sample data.

Checkout the [examples](neptoon-examples.md). The example demonstrating this is found under `jupyter_notebooks>calibration>example_calibration.ipynb`


## References

Franz, T. E., Zreda, M., Rosolem, R., and Ferre, T. P. A.: A universal calibration function for determination of soil moisture with cosmic-ray neutrons, Hydrol. Earth Syst. Sci., 17, 453–460, https://doi.org/10.5194/hess-17-453-2013, 2013. 

 Schrön, M., Köhli, M., Scheiffele, L., Iwema, J., Bogena, H. R., Lv, L., Martini, E., Baroni, G., Rosolem, R., Weimar, J., Mai, J., Cuntz, M., Rebmann, C., Oswald, S. E., Dietrich, P., Schmidt, U., and Zacharias, S.: Improving calibration and validation of cosmic-ray neutron sensors in the light of spatial sensitivity, Hydrol. Earth Syst. Sci., 21, 5009–5030, https://doi.org/10.5194/hess-21-5009-2017, 2017. 