# %%
from pathlib import Path
import math
import pandas as pd

from neptoon.data_management.crns_data_hub import CRNSDataHub
from neptoon.ancillary_data_collection.nmdb_data_collection import (
    NMDBDataAttacher,
)
from neptoon.data_management.data_audit import (
    DataAuditLog,
)
from neptoon.data_management.data_audit import log_key_step

# %%

""" Test later
# from neptoon.configuration.configuration_input import (
#     ConfigurationManager,
# )

"""
DataAuditLog.create()

"""IDEA ON SIMPLE ONE LINE RUN
# Import Config files to ConfigManager
station_config_path = "/Users/power/Documents/code/cosmosbase/configuration_files/A101_station.yaml"
process_config_path = "/Users/power/Documents/code/cosmosbase/configuration_files/v1_processing_method.yaml"

config_manager = ConfigurationManager()
config_manager.load_and_validate_configuration("station", station_config_path)
config_manager.load_and_validate_configuration(
    "processing", process_config_path
)

# Run process with one line!
ProcessCRNSWithConfig(config_manager)

"""


class PseudoDataProcessor:
    def __init__(self):
        pass

    @log_key_step("style", "a1")
    def theta_calc(self, style="first", N0=2000, a1=2.5):
        pass

    @log_key_step("method", "window")
    def smooth_neutrons(self, method="SG", window=12):
        # logic
        pass


processor = PseudoDataProcessor()
processor.theta_calc(style="second")
processor.smooth_neutrons(method="SG", window=12)

# %%
"""Step 0: Collect data from source
"""

"""Step 1: Create correct format of dataframe

This section will eventually be replaced by the full ingest routine. The
ingest routine will handle how we take raw data and convert it to a
format that fits what we decide is the "standard". 

The point is that data should eventually fit some set of standards for
use in the software.

These include:
    - Index as a datetime
    - Key columns labelled correctly
    - math.nan values for missing data
    - A full timeseries (fill in gaps with rows).
    - Columns of the correct type (ensure they are read in as floats and
      not objects!)
"""


def import_crns_dataframe_and_format(filename):
    """
    This is a pseudo function that will eventually be replaced by the
    ingest routines. For now it converts a sample dataset into a format
    (which we can update later).
    """
    cwd = Path.cwd()
    crns_df_path = cwd / "tests" / "sample_crns_data" / filename
    crns_df = pd.read_csv(crns_df_path)
    crns_df["date_time_utc"] = pd.to_datetime(
        crns_df["date_time_utc"], dayfirst=True
    )
    crns_df.set_index(crns_df["date_time_utc"], inplace=True)
    crns_df.drop(["date_time_utc"], axis=1, inplace=True)
    crns_df = crns_df.replace("noData", math.nan)
    crns_df["epithermal_neutrons"] = pd.to_numeric(
        crns_df["epithermal_neutrons"]
    )
    crns_df["thermal_neutrons"] = pd.to_numeric(crns_df["thermal_neutrons"])
    crns_df["air_temperature"] = pd.to_numeric(crns_df["air_temperature"])
    crns_df["air_relative_humidity"] = pd.to_numeric(
        crns_df["air_relative_humidity"]
    )
    crns_df["precipitation"] = pd.to_numeric(crns_df["precipitation"])
    crns_df["air_pressure"] = pd.to_numeric(crns_df["air_pressure"])

    return crns_df


crns_df = import_crns_dataframe_and_format("CUC001.csv")
crns_df

# %%
# ### TEMP

from saqc import SaQC

qc = SaQC(crns_df, scheme="simple")
qc = qc.flagRange("epithermal_neutrons", min=400, max=900)
qc = qc.flagRaise()
# OutliersMixin.flagRaise() missing 1 required positional argument: 'field'
qc.flags.to_pandas()
qc.data.to_pandas()
qc.plot("epithermal_neutrons")


# %%
def fancy_new_function():
    pass


# qc.flagGeneric(
#     field="epithermal_neutrons", func=fancy_new_function, flag="BAD"
# )


#### END TEMP
# %%
"""Step 2: Create the initial CRNSDataHub and validate

The next step is adding the correctly formatted dataframe to the
CRNSDataHub. The DataHub provides validation checks and flagging
capabilities. That is it creates a flag system to ensure we flag data
which fails any checks without the need to remove data itself. 

NOTE: It will be possible to work without the DataHub. We could perhaps
even show this in a notebook? This would just be using the functions in
a workbook.
"""

data_hub = CRNSDataHub(crns_data_frame=crns_df)
# Validate the dataframe to check for initial errors
data_hub.validate_dataframe(schema="initial_check")
# The dataframe can be accessed here.
data_hub.crns_data_frame


# %%
"""Step 3: Perform first QA steps

Here we would perform QA. This requires creating QA routines and
applying them. The flags would be updated. Validation with another
schema to ensure the QA was succesfully implemented.
"""

# %%
"""Step 4: Attach the NMDB data

Important step in preperation of data. Collect the NMDB data for
intensity corrections.

"""

attacher = NMDBDataAttacher(data_hub)
attacher.configure(station="JUNG")
attacher.fetch_data()
attacher.attach_data()

# %%
"""Step 5: Correct Neutrons
"""


class NeutronCorrector:
    """
    This class takes as input a CRNSDataHub and applies neutron
    corrections to the data attached to it.
    """

    def __init__(
        self,
        data_hub: CRNSDataHub = None,
    ):
        self.data_hub = data_hub

    def select_steps(
        self,
        pressure_correction,
        water_vapour_correction,
        above_ground_biomass_correction,
        incoming_neutron_intensity_correction,
    ):
        """
        TODO: Pandera check here depending on steps

        Parameters
        ----------
        steps_to_implement : _type_
            _description_
        """
        pass

    def validate_data_is_suitable():
        pass

    def correct_neutrons():
        pass


corrector = NeutronCorrector(data_hub)
corrector.select_steps("steps")

# %%
"""Step 6: Calibration [Optional]
"""


class SiteCalibrator:
    def __init__(
        self,
        data_hub: CRNSDataHub,
    ):
        pass


def assess_data(crns_data_hub):
    qc = SaQC(crns_data_hub.crns_df, scheme="simple")
    qc = qc.flagRange("epithermal_neutrons", min=400, max=900)
    qc = qc.flagRaise()
    crns_data_hub.flags_table = qc.flags.to_pandas()
    crns_data_hub.crns_df = qc.data.to_pandas()
    qc.plot("epithermal_neutrons")


# %%
"""Step 7: Convert to theta
"""

"""Step 8: Final QA
"""

"""Step 9: PDF/Figure outputs

Here we could do some analysis based on data from processing. Some of
this will be like the Journalist class in corny. So maybe things like
data removed, number of days with good data or other hydrological
information. Make some figures maybe using the data.


"""

"""Step 10: Create AuditLog/Update YAML and close

At the very end we would want to organise the audit log by saving and
archiving it. I also imagine some steps here to update the YAML file
(particularly the site yaml file) with new information collated in the
previous step. So we could have a section of average values or
something?

"""

DataAuditLog.archive_and_delete_log(site_name="Site From Somewhere")
# Cant access file, file is in use (self._accessor.unlink(self))

# %%
# Here testing the TimeStampAligner
import pandas as pd
import numpy as np
from neptoon.data_ingest_and_formatting.timestamp_alignment import (
    TimeStampAligner,
)

data = {"value": [1, 2, 3, 4]}
index = pd.to_datetime(
    [
        "2021-01-01 00:04:00",
        "2021-01-01 01:10:00",
        "2021-01-01 02:05:00",
        "2021-01-01 02:58:00",
    ]
)
df = pd.DataFrame(data, index=index)
df
# %%
# Initialize the TimeStampAligner
tsa = TimeStampAligner(df)
# Align timestamps
tsa.align_timestamps(method="nshift", freq="1h")
# Get the aligned dataframe
aligned_df = tsa.return_dataframe()
aligned_df
# %%
