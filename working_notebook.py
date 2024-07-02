from pathlib import Path
import math
import pandas as pd
from neptoon.quality_assesment.quality_assesment import (
    QualityAssessmentFlagBuilder,
    FlagRangeCheck,
    FlagNeutronGreaterThanN0,
    FlagBelowMinimumPercentN0,
    DataQualityAssessor,
    FlagSpikeDetectionUniLOF,
)

from neptoon.data_management.crns_data_hub import CRNSDataHub

from neptoon.data_management.site_information import SiteInformation

from neptoon.neutron_correction.neutron_correction import (
    CorrectionType,
    CorrectionTheory,
    Correction,
)

from neptoon.data_management.data_audit import (
    DataAuditLog,
)


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

"""Step 2: Create the initial CRNSDataHub and validate

The next step is adding the correctly formatted dataframe to the
CRNSDataHub. The DataHub provides validation checks and flagging
capabilities. That is it creates a flag system to ensure we flag data
which fails any checks without the need to remove data itself. 

NOTE: It will be possible to work without the DataHub. We could perhaps
even show this in a notebook? This would just be using the functions in
a workbook.
"""

site_information = SiteInformation(
    latitude=90,
    longitude=90,
    elevation=0,
    reference_incoming_neutron_value=150,
    bulk_density=1.4,
    lattice_water=0.01,
    soil_organic_carbon=0,
)

site_information.add_custom_value("n0", 2000)
site_information.add_custom_value("biomass", 1)

data_hub = CRNSDataHub(
    crns_data_frame=crns_df, site_information=site_information
)
data_hub.validate_dataframe(schema="initial_check")

"""Step 3: Attach the NMDB data

Important step in preperation of data. Collect the NMDB data for
intensity corrections.
"""

data_hub.attach_nmdb_data()

"""Step 4: Perform first QA steps

Here we would perform QA. This requires creating QA routines and
applying them. The flags would be updated. Validation with another
schema to ensure the QA was succesfully implemented.
"""

qa_flags = QualityAssessmentFlagBuilder()
qa_flags.add_check(
    FlagRangeCheck("air_relative_humidity", min_val=0, max_val=100),
    FlagRangeCheck("precipitation", min_val=0, max_val=20),
    FlagSpikeDetectionUniLOF("epithermal_neutrons"),
    # ...
)

data_hub.apply_quality_flags(custom_flags=qa_flags)


"""Step 5: Correct Neutrons

# steps = CorrectionBuilder()
# steps.add_correction(IncomingIntensityZreda(150))
# corrector = CorrectNeutrons(data_hub.crns_data_frame, steps)
# df = corrector.correct_neutrons()
"""


class NewIdeaForBiomass(Correction):
    """
    My new idea to correct for biomass with humidity
    """

    def __init__(self, site_information):
        self.site_information = site_information
        self.correction_type = CorrectionType.ABOVE_GROUND_BIOMASS
        self.correction_factor_column_name = "biomass_correction_dp"
        self.humidity_column_name = "air_relative_humidity"

    @staticmethod
    def new_func(biomass, humidity):
        return (biomass / humidity) / 100

    def apply(self, data_frame: pd.DataFrame):

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: self.new_func(
                row[self.humidity_column_name],
                self.site_information.biomass,
            ),
            axis=1,
        )
        return data_frame


data_hub.correction_factory.register_custom_correction(
    correction_type=CorrectionType.ABOVE_GROUND_BIOMASS,
    theory="my_new_idea",
    correction_class=NewIdeaForBiomass,
)

data_hub.select_correction(
    correction_type=CorrectionType.INCOMING_INTENSITY,
    correction_theory=CorrectionTheory.ZREDA_2012,
)

data_hub.select_correction(
    correction_type=CorrectionType.ABOVE_GROUND_BIOMASS,
    correction_theory="my_new_idea",
)

data_hub.correction_builder.get_corrections()
data_hub.correct_neutrons(correct_flagged_values_too=False)


data_hub.crns_data_frame
data_hub.flags_data_frame


"""Step 6: Calibration [Optional]
"""


"""Step 7: Convert to theta
"""

data_hub.produce_soil_moisture_estimates()

# soil_moisture_calculator = NeutronsToSM(
#     crns_data_frame=data_hub.crns_data_frame, n0=700
# )
# soil_moisture_calculator.process_data()
# soil_moisture_calculator.return_data_frame()

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

DataAuditLog.archive_and_delete_log(site_name="TestQA")
# Cant access file, file is in use (self._accessor.unlink(self))
