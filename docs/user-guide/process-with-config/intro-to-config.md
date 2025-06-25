# Working with configuration files

It is possible to use configuration files when working in neptoon. These can be imported, either through your python editor or with the GUI, and will automatically fill out important values required for processing. This allows users to fill out the information specific to their site, store it in the YAML, and use this for quick, simple, and *replicable* data processing.

The configuration files are in the YAML format (**Y**et **A**nother **M**arkup **L**anguage). This type of format a nice balance between being human readable and computer readable. Checkout examples [here](https://codebase.helmholtz.cloud/cosmos/neptoon_examples/-/tree/main/configuration_files?ref_type=heads). When making changes be sure to maintain the indentation you see, and read on below for more specifics on how to fill this out correctly.

!!! warning "A warning on config files before v1.0 release"
      Until we release v1.0, there are occasions when updates might cause your current configuration files to show errors. For example, if we add a setting that is now considered essential, or receive feedback that a better naming convention is more intuative to new users. We will try to minimise this, however cannot guarentee it. Once v1.0 has been released we promise that no updates (until a v2.0) will cause configuration files to stop working.


## What are the configuration files?

The config files are divided into two distinct types. 

1. **Processing Configuration**
   
   This configuration file stores information about the steps to be taken during data processing. It essentially outlines the workflow. This file is not unique to each site, and the same configuration file can (and should) be used across many sites. Differences in this file will lead to different processing methodologies.
   
2. **Sensor Information**
   
   This configuration file stores key information specific to the sensor being processed. This will be unique to each site as it stores information such as the latitude and longitude, or average meteorological conditions. One of these should be created for each individual sensor you wish to process. 

