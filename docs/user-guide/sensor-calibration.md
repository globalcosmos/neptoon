## Introduction

Calibration of a CRNS generally involves finding the so-called "N0" number. This number is the theorised maximum number of neutrons that will be counted by a sensor, over a defined time period, if conditions were **completely dry.** In neptoon we standardise all our counting rates to counts per hour (cph) and so our N0 number will always be the number of neutrons expected to be counted by a sensor, at a particular site, over a 1 hour integration window, in totally dry conditions. 

To convert neutrons to soil moisture we now take the ratio between the actual count rate vs the theorised dry count rate. This ratio places us on the calibration curve which can be seen in Figure 1 below (Franz et al., 2012). 


<img src="/assets/N0-calib-curve.png" alt="N0 calibration curve" width="60%" style="display: block; margin: 0 auto;">
<p style="text-align: center; font-style: italic;">Figure 1: N0 calibration curve showing the relationship between neutron counts and soil moisture.</p>

!!! important "Neutron Correction"
	Neutron count rates are expected to be corrected by the time we get to calibration. The correction removes external influences on the neutron counts (e.g., changes in atmospheric pressure). So the N0 is a corrected term. More on corrections [here](choosing-corrections.md). This means that if you change your corrections steps you **must** recalibrate and get a new N0 number. If not your N0 and N numbers are being corrected differently!

## Before you calibrate...

Before we begin lets describe whats expected at this stage. 

- You have a CRNSDataHub instance
- You have imported your CRNS data into the hub (more on that [here](importing-data.md))
- You have a SensorInformation in the hub (more on that [here](key-site-information.md))
- You have collected any external data you need (more on that [here](external-data.md))
- You have ideally performed some quality assessment on your data (more on that [here](data-quality-checks.md))
- You have corrected your neutron counts so that you have a corrected neutrons column (more on that [here](choosing-corrections.md))

## Your sample data 

TBD

# Calibrate without CRNSDataHub

It's possible to calibrate your site more directly, without a data hub. For this you will need; 1. A dataframe with pre-corrected CRNS timeseries data and 2. your sample data. For example, you could save your dataframe in your datahub just before calibration and use this to test different variations of your sample data.

Checkout the [examples](neptoon-examples.md). The example demonstrating this is found under `jupyter_notebooks>calibration>example_calibration.ipynb`


## References

Franz, T. E., Zreda, M., Rosolem, R., and Ferre, T. P. A.: A universal calibration function for determination of soil moisture with cosmic-ray neutrons, Hydrol. Earth Syst. Sci., 17, 453–460, https://doi.org/10.5194/hess-17-453-2013, 2013. 