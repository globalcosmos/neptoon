import pandas as pd
from neptoon.configuration.configuration_input import ConfigurationManager
from neptoon.ancillary_data_collection.nmdb_data_collection import (
    NMDBDataAttacher,
)
from neptoon.data_management.data_validation_tables import (
    FormatCheck,
)
from neptoon.quality_assesment.quality_assesment import (
    QualityAssessmentFlagBuilder,
    DataQualityAssessor,
)

from neptoon.logging import get_logger

core_logger = get_logger()


class SiteInformation:
    """
    This class should store key info needed for site processing. For
    example, bulk density, lat/lon, lattice water, reference values. A
    user can then define this and add it to the hub. We can also
    automate building of it using config information.
    """

    pass


class CRNSDataHub:
    """
    The CRNSDataHub is used to manage the time series data throughout
    the processing steps. Some key features:

    - It stores a DataFrame for a site
    - As we progress through the steps, data can be added to the
      DataFrame and the shadow DataFrame's updated.

    Raw data is checked against the RawDataSchema which is a first line
    of defense against incorrectly formatted tables. Should a fail
    happen here data must be either reformatted using one of the
    provided routines or manually formatted to match the standard.
    """

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        flags_data_frame: pd.DataFrame = None,
        configuration_manager: ConfigurationManager = None,
        quality_assessor: DataQualityAssessor = None,
        validation: bool = True,
        process_with_config: bool = False,
    ):
        """
        Inputs to the CRNSDataHub.

        Parameters
        ----------
        crns_data_frame : pd.DataFrame
            CRNS data in a dataframe format. It will be validated to
            ensure it has been formatted correctly.
        configuration_manager : ConfigurationManager, optional
            A ConfigurationManager instance storing configuration YAML
            information, by default None
        quality_assessor : SaQC
            SaQC object which is used for quality assessment. Used for
            the creation of flags to define poor data.
        validation : bool
            Toggle for whether to have continued validation of data
            tables during processing (see
            data_management>data_validation_tables.py for examples of
            tables being validated). These checks ensure data is
            correctly formatted for internal processing.
        """
        self._crns_data_frame = crns_data_frame
        self._flags_data_frame = flags_data_frame
        if configuration_manager is not None:
            self._configuration_manager = configuration_manager
        self._validation = validation
        self._quality_assessor = quality_assessor
        self._process_with_config = process_with_config

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df: pd.DataFrame):
        # TODO checks on df
        self._crns_data_frame = df

    @property
    def flags_data_frame(self):
        return self._flags_data_frame

    @flags_data_frame.setter
    def flags_data_frame(self, df: pd.DataFrame):
        # TODO checks on df
        self._flags_data_frame = df

    @property
    def validation(self):
        return self._validation

    @property
    def quality_assessor(self):
        return self._quality_assessor

    @quality_assessor.setter
    def quality_assessor(self, assessor: DataQualityAssessor):
        self._quality_assessor = assessor

    @property
    def process_with_config(self):
        return self._process_with_config

    def _create_quality_assessor(self):
        pass

    def validate_dataframe(self, schema: str):
        """
        Validates the dataframe against a pandera schema See
        data_validation_table.py for schemas.

        Parameters
        ----------
        schema : str
            The name of the schema to use for the check.
        """

        if schema == "initial_check":
            tmpdf = self.crns_data_frame
            FormatCheck.validate(tmpdf, lazy=True)
        elif schema == "before_corrections_check":
            pass
        elif schema == "after_corrections_check":
            pass
        elif schema == "final_check":
            pass
        else:
            validation_error_message = (
                "Incorrect schema or table name given "
                "when validating the crns_data_frame"
            )
            core_logger.error(validation_error_message)
            print(validation_error_message)

    def attach_nmdb_data(
        self,
        station="JUNG",
        new_column_name="incoming_neutron_intensity",
        resolution="60",
        nmdb_table="revori",
    ):
        """
        Utilises the NMDBDataAttacher class to attach NMDB incoming
        intensity data to the crns_data_frame. Collects data using
        www.NMDB.eu

        See NMDBDataAttacher documentation for more information.

        Parameters
        ----------
        station : str, optional
            The station to collect data from, by default "JUNG"
        new_column_name : str, optional
            The name of the column were data will be written to, by
            default "incoming_neutron_intensity"
        resolution : str, optional
            The resolution in minutes, by default "60"
        nmdb_table : str, optional
            The table to pull data from, by default "revori"
        """
        attacher = NMDBDataAttacher(
            data_frame=self.crns_data_frame, new_column_name=new_column_name
        )
        attacher.configure(
            station=station, resolution=resolution, nmdb_table=nmdb_table
        )
        attacher.fetch_data()
        attacher.attach_data()

    def apply_quality_flags(
        self,
        custom_flags: QualityAssessmentFlagBuilder = None,
        flags_from_config: bool = False,
        flags_default: str = None,
    ):
        """
        Flags data based on quality assessment. A user can supply a
        QualityAssessmentFlagBuilder object that has been custom built,
        they can flag using the config file (if supplied), or they can
        choose a standard flagging routine.

        Everything is off by default so a user must choose.

        Parameters
        ----------
        custom_flags : QualityAssessmentFlagBuilder, optional
            A custom built set of Flags , by default None
        flags_from_config : bool, optional
            State if to conduct QA using config supplied configuration,
            by default False
        flags_default : str, optional
            A string representing a default version of flagging, by
            default None
        """
        if self.quality_assessor is None:
            self.quality_assessor = DataQualityAssessor(
                data_frame=self.crns_data_frame
            )

        if flags_from_config:
            # validate config flags section is complete
            # compile flag_builder using config object
            # apply flags
            pass

        if custom_flags:
            self.quality_assessor.add_custom_flag_builder(custom_flags)
            self.quality_assessor.apply_quality_assessment()
            self.flags_data_frame = (
                self.quality_assessor.return_flags_data_frame()
            )
            message = "Flagging of data complete using Custom Flags"
            core_logger.info(message)

        if flags_default:
            # Do we include a default system here? Is this possible?
            pass

    def correct_neutrons(self):
        pass

    def produce_soil_moisture_estimates(self):
        pass

    def mask_flagged_data(self):
        """
        Returns a pd.DataFrame() where flagged data has been replaced
        with NaN values
        """
        pass

    def save_data(self, folder_path, file_name, step):
        """
        Saves the file to a specified location. It must contain the
        correct folder_path and file_name.

        Provide options on what is saved:

        - everything (uncertaities, flags, etc)
        - seperate
        - key variables only


        Parameters
        ----------
        folder_path : str
            Path to the save folder
        file_name : str
            Name of the file
        """

        file_name_and_save_location = folder_path + file_name + ".csv"
        self.dataframe.to_csv(file_name_and_save_location)

    def archive_data(self, folder_path, file_name):
        """
        Archive the data into a zip file. All the data tables in the
        instance will be collected and saved together.

        Parameters
        ----------
        folder_path : _type_
            _description_
        file_name : _type_
            _description_
        """
        pass

    def add_column_to_crns_data_frame(
        self,
        source,
        source_column_name: str = None,
        new_column_name: str = None,
    ):
        if isinstance(source, pd.DataFrame):
            if source_column_name is None:
                raise ValueError(
                    "Must specify a column name "
                    "when the source is DataFrame"
                )
            if new_column_name is None:
                new_column_name = source_column_name
            if not isinstance(source.index, pd.DatetimeIndex):
                raise ValueError("DataFrame source must have a DatetimeIndex.")
            mapped_data = source[source_column_name].reindex(
                self.crns_data_frame.index, method="nearest"
            )
        elif isinstance(source, dict):
            if new_column_name is None:
                raise ValueError(
                    "New column name must be specified when source is a dictionary"
                )
            mapped_data = pd.Series(source).reindex(
                self.crns_data_frame.index, method="nearest"
            )
        else:
            raise TypeError(
                "Source must be either a DataFrame or a dictionary"
            )
        self.crns_data_frame[new_column_name] = mapped_data
