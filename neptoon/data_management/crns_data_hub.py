import pandas as pd
import numpy as np
from neptoon.configuration.configuration_input import ConfigurationManager
from neptoon.ancillary_data_collection.nmdb_data_collection import (
    NMDBDataAttacher,
)
from neptoon.neutron_correction.neutron_correction import (
    CorrectionBuilder,
    CorrectionFactory,
    CorrectionType,
    CorrectionTheory,
    CorrectNeutrons,
)
from neptoon.data_management.data_validation_tables import (
    FormatCheck,
)
from neptoon.data_management.site_information import SiteInformation
from neptoon.quality_assesment.quality_assesment import (
    QualityAssessmentFlagBuilder,
    DataQualityAssessor,
)

from neptoon.logging import get_logger

core_logger = get_logger()


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
        site_information: SiteInformation = None,
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
        site_information : SiteInformation
            Object which contains information about a site necessary for
            processing crns data. e.g., bulk density data
        """

        self._crns_data_frame = crns_data_frame
        self._flags_data_frame = flags_data_frame
        if configuration_manager is not None:
            self._configuration_manager = configuration_manager
        self._validation = validation
        self._quality_assessor = quality_assessor
        self._process_with_config = process_with_config
        self._site_information = site_information
        self._correction_factory = CorrectionFactory(self._site_information)
        self._correction_builder = CorrectionBuilder()

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df: pd.DataFrame):
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
        if isinstance(assessor, DataQualityAssessor):
            self._quality_assessor = assessor
        else:
            message = (
                f"{assessor} is not a DataQualityAssessor class. "
                "Cannot assign to self.quality_assessor"
            )
            core_logger.error(message)
            raise TypeError(message)

    @property
    def process_with_config(self):
        return self._process_with_config

    @property
    def site_information(self):
        return self._site_information

    @property
    def correction_factory(self):
        return self._correction_factory

    @property
    def correction_builder(self):
        return self._correction_builder

    @correction_builder.setter
    def correction_builder(self, builder: CorrectionBuilder):
        self._correction_builder = builder

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

    def update_site_information(self, new_site_information: SiteInformation):
        """
        When a user wants to update the hub with a SiteInformation
        object it must be done with this method.

        Parameters
        ----------
        site_information : SiteInformation
            SiteInformation object
        """
        self._site_information = new_site_information
        self._correction_factory = CorrectionFactory(self._site_information)
        core_logger.info("Site information updated sucessfully")

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

    def select_correction(
        self,
        use_all_default_corrections=False,
        correction_type: CorrectionType = "empty",
        correction_theory: CorrectionTheory = None,
    ):
        """
        Method to select corrections to be applied to data. If
        use_all_default_corrections is True then it will apply the
        default correction methods. These will periodically be updated
        to the most current and agreed best methods.

        Individual corrections can be applied using a CorrectionType and
        CorrectionTheory. If a user assignes a CorrectionType without a
        CorrectionTheory, then the default correction for that
        CorrectionType is applied.

        Parameters
        ----------
        use_all_default_corrections : bool, optional
            decision to use defaults, by default False
        correction_type : CorrectionType, optional
            A CorrectionType, by default "empty"
        correction_theory : CorrectionTheory, optional
            A CorrectionTheory, by default None
        """

        if use_all_default_corrections:
            pass  # TODO build default corrections
        else:
            correction = self.correction_factory.create_correction(
                correction_type=correction_type,
                correction_theory=correction_theory,
            )
            self.correction_builder.add_correction(correction=correction)

    def correct_neutrons(
        self,
        correct_flagged_values_too=False,
    ):
        """
        Create correction factors as well as the corrected epithermal
        neutrons column. By default it will collect apply corrections
        only on data that has been left unflagged during QA. Opionally
        this can be turned off.

        Parameters
        ----------
        correct_flagged_values_too : bool, optional
            Whether to turn off the masking of data defined as poor in
            QA, by default False
        """
        if correct_flagged_values_too:
            corrector = CorrectNeutrons(
                crns_data_frame=self.crns_data_frame,
                correction_builder=self.correction_builder,
            )
            self.crns_data_frame = corrector.correct_neutrons()
        else:
            corrector = CorrectNeutrons(
                crns_data_frame=self.mask_flagged_data(),
                correction_builder=self.correction_builder,
            )
            self.crns_data_frame = corrector.correct_neutrons()

    def produce_soil_moisture_estimates(self):
        pass

    def mask_flagged_data(self):
        """
        Returns a pd.DataFrame() where flagged data has been replaced
        with NaN values
        """
        mask = self.flags_data_frame == "UNFLAGGED"
        masked_df = self.crns_data_frame.copy()
        masked_df[~mask] = np.nan
        return masked_df

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
