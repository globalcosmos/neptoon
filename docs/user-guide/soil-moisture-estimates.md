# Soil Moisture Estimates

Finally we get to what (for most of you) this is all about, getting soil moisture estimates!

Prior to this point we've organised and parsed the data, attached required external data, quality assessed, corrected, smoothed, and calibrated our data. We are now ready to start processing. 

The following is enough to do this with the datahub (as long as the previously described steps have been complete):

```python

conversion_theory="desilets_etal_2010"

data_hub.produce_soil_moisture_estimates(
    conversion_theory=conversion_theory
    ) 

```

Pretty simple!

Behind the scenes neptoon will collect the N0 number from the SensorConfig attached to the hub (with the N0 suppleid at the beggning or perhaps calibrated in the currenty pipeline). It will also collect other site info such as dry soil bulk density, lattice water, and soil organic carbon. 

We have also selected the theory for conversion. An alternative to the classic Desilets et al., (2010) approach is the new UTS function (Koehli et al., 2021). If you wished to run this you would run:

```python

conversion_theory="koehli_etal_2021"

data_hub.produce_soil_moisture_estimates(
    conversion_theory=conversion_theory
    ) 

```

In this case there are additional behind the scenes checks. The UTS function corrected for humidity in the conversion to soil moisture itself. So neptoon will check to see if you have already corrected for humidity using Rosolem et al., (2013) and remove this correction if required. This ensures we don't double correct for humidity!

### Testing and playing

But lets suppose you want to do some testing of different values. You can do this with this:

```python

conversion_theory="koehli_etal_2021"

data_hub.produce_soil_moisture_estimates(
    conversion_theory=conversion_theory,
    n0 = 2000,
    dry_soil_bulk_density = 1.1,
    lattice_water = 0.01,
    soil_organic_carbon = 0.02,
    koehli_parameters = "Mar21_mcnp_ewin"
    ) 
```

Be sure to check the docstrings for more options here!