import pandas as pd
import numpy as np
from typing import Literal, Union, Optional
import dataclasses
from pathlib import Path
from neptoon.config.site_information import SiteInformation
from neptoon.config.configuration_input import ConfigurationManager
from neptoon.external.nmdb_data_collection import (
    NMDBDataAttacher,
)
from neptoon.calibration import (
    CalibrationConfiguration,
    CalibrationStation,
)
from neptoon.corrections.factory.build_corrections import (
    CorrectionBuilder,
    CorrectionFactory,
    CorrectionType,
    CorrectionTheory,
    CorrectNeutrons,
)
from neptoon.products.estimate_sm import NeutronsToSM
from neptoon.quality_control.data_validation_tables import (
    FormatCheck,
)

from neptoon.quality_control import (
    QualityAssessmentFlagBuilder,
    DataQualityAssessor,
)
from neptoon.io.save import SaveAndArchiveOutputs
from neptoon.data_prep.smoothing import SmoothData

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
        calibration_samples_data: pd.DataFrame = None,
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
        calibration_samples_data : pd.DataFrame
            The sample data taken during the calibration campaign.
        """

        self._crns_data_frame = crns_data_frame
        self._flags_data_frame = flags_data_frame
        if configuration_manager is not None:
            self._configuration_manager = configuration_manager
        self._validation = validation
        self._quality_assessor = quality_assessor
        self._process_with_config = process_with_config
        self._site_information = site_information
        self._calibration_samples_data = calibration_samples_data
        self._correction_factory = CorrectionFactory(self._site_information)
        self._correction_builder = CorrectionBuilder()
        self.calibrator = None

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
    def calibration_samples_data(self):
        return self._calibration_samples_data

    @calibration_samples_data.setter
    def calibration_samples_data(self, data: pd.DataFrame):
        # TODO add verification
        self._calibration_samples_data = data

    @property
    def correction_builder(self):
        return self._correction_builder

    @correction_builder.setter
    def correction_builder(self, builder: CorrectionBuilder):
        self._correction_builder = builder

    def validate_dataframe(
        self,
        schema: str,
    ):
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

    def update_site_information(
        self,
        new_site_information: SiteInformation,
    ):
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

    def add_quality_flags(
        self,
        custom_flags: QualityAssessmentFlagBuilder = None,
        add_check=None,
    ):
        """
        Add QualityChecks to undertake on the dataframe

        Parameters
        ----------
        custom_flags : QualityAssessmentFlagBuilder, optional
            user can build a QualityAssessmentFlagBuilder with checks
            and attach this as a whole, by default None
        add_check : Check, optional
            user can add individual Checks, or a list of Checks. These
            will be then added to the QualityAssessmentFlagBuilder, by
            default None
        """
        # if self.quality_assessor is None:
        #     self.quality_assessor = DataQualityAssessor(
        #         data_frame=self.crns_data_frame
        #     )
        # else:
        #     self.quality_assessor.data_frame = self.crns_data_frame
        self.quality_assessor = DataQualityAssessor(
            data_frame=self.crns_data_frame
        )
        if custom_flags:
            self.quality_assessor.add_custom_flag_builder(custom_flags)

        if add_check:
            if isinstance(add_check, list):
                for check in add_check:
                    self.quality_assessor.add_quality_check(check)
            else:
                self.quality_assessor.add_quality_check(add_check)

    def apply_quality_flags(
        self,
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

        self.quality_assessor.apply_quality_assessment()

        self.flags_data_frame = self.quality_assessor.return_flags_data_frame(
            current_flag_data_frame=self.flags_data_frame,
        )
        message = "Flagging of data complete using Custom Flags"
        core_logger.info(message)

    def select_correction(
        self,
        correction_type: CorrectionType = "empty",
        correction_theory: CorrectionTheory = None,
        use_all_default_corrections=False,
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

    def smooth_data(
        self,
        column_to_smooth: str,
        smooth_method: Literal[
            "rolling_mean", "savitsky_golay"
        ] = "rolling_mean",
        window: Optional[Union[int, str]] = 12,
        poly_order: int = 4,
        auto_update_final_col: bool = True,
    ):
        """
        Applies a smoothing method to a series of data in the
        crns_data_frame using the SmoothData class.

        A `column_to_smooth` attribute must be supplied, and should be
        written using the "str(ColumnInfo.Name.COLUMN)" format. The two
        most likely to be used are:

           - str(ColumnInfo.Name.SOIL_MOISTURE)
           - str(ColumnInfo.Name.EPI_NEUTRONS)

        If parameters are left as None, it uses defaults from SmoothData
        (i.e., rolling_mean, window size == 12).

        Parameters
        ----------
        column_to_smooth : str(ColumnInfo.Name.VALUE)
            The column in the crns_data_frame that needs to be smoothed.
            Automatically
        """
        series_to_smooth = pd.Series(self.crns_data_frame[column_to_smooth])
        smoother = SmoothData(
            data=series_to_smooth,
            column_to_smooth=column_to_smooth,
            smooth_method=smooth_method,
            window=window,
            poly_order=poly_order,
            auto_update_final_col=auto_update_final_col,
        )
        col_name = smoother.create_new_column_name()
        self.crns_data_frame[col_name] = smoother.apply_smoothing()

    def calibrate_station(
        self,
        config: CalibrationConfiguration = None,
    ):
        if self.calibration_samples_data is None:
            message = "No calibration_samples_data found. Cannot calibrate."
            core_logger.error(message)
            raise ValueError(message)
        if config is None:
            message = "No CalibrationConfiguration provided - using defaults"
            core_logger.info(message)
            config = CalibrationConfiguration()

        self.calibrator = CalibrationStation(
            calibration_data=self.calibration_samples_data,
            time_series_data=self.crns_data_frame,
            config=config,
        )
        n0 = self.calibrator.find_n0_value()
        self.site_information.n0 = n0
        print(f"N0 number is {n0}")

    def produce_soil_moisture_estimates(
        self,
        n0: float = None,
        dry_soil_bulk_density: float = None,
        lattice_water: float = None,
        soil_organic_carbon: float = None,
    ):
        """
        Produces SM estimates with the NeutronsToSM class. If values for
        n0, dry_soil_bulk_density, lattice_water, or soil_organic_carbon
        are not supplied, the values are taken from the internal
        site_information class.

        Parameters
        ----------
        n0 : float, optional
            n0 calibration term, by default None
        dry_soil_bulk_density : float, optional
            given in g/cm3, by default None
        lattice_water : float, optional
            given as decimal percent e.g., 0.01, by default None
        soil_organic_carbon : float, optional
            Given as decimal percent, e.g., 0.001, by default None
        """
        # Create attributes for NeutronsToSM
        default_params = {
            "n0": self.site_information.n0,
            "dry_soil_bulk_density": self.site_information.dry_soil_bulk_density,
            "lattice_water": self.site_information.lattice_water,
            "soil_organic_carbon": self.site_information.soil_organic_carbon,
        }
        provided_params = {
            "n0": n0,
            "dry_soil_bulk_density": dry_soil_bulk_density,
            "lattice_water": lattice_water,
            "soil_organic_carbon": soil_organic_carbon,
        }
        params = {k: v for k, v in provided_params.items() if v is not None}
        default_params.update(params)

        soil_moisture_calculator = NeutronsToSM(
            crns_data_frame=self.crns_data_frame, **default_params
        )
        soil_moisture_calculator.calculate_all_soil_moisture_data()
        self.crns_data_frame = soil_moisture_calculator.return_data_frame()

    def mask_flagged_data(self):
        """
        Returns a pd.DataFrame() where flagged data has been replaced
        with np.nan values
        """
        mask = self.flags_data_frame == "UNFLAGGED"
        masked_df = self.crns_data_frame.copy()
        masked_df[~mask] = np.nan
        return masked_df

    def prepare_static_values(self):
        """
        Attaches the static values from the SiteInformation object as
        columns of values in the crns_data_frame.

        TODO
         - Add a way to use str(ColumnInfo.Name.VARIABLE) for assigning
           names.
         - This must consider if people already have the variables and
           don't want them changed.
         - Must be a way to compare the SiteInformation key and the
           appropriate ColumnInfo.Name
        """

        site_information_dict = dataclasses.asdict(self.site_information)
        for key in site_information_dict:
            if key in self.crns_data_frame.columns:
                message = (
                    f"{key} already found in columns of crns_data_frame"
                    " when trying to add static values from site_information."
                    "Values from SiteInformation were not writtent to the"
                    " crns_data_frame."
                )
                core_logger.info(message)
                continue
            elif site_information_dict[key] is None:
                # TODO add skip here
                pass
            else:
                self.crns_data_frame[key] = site_information_dict[key]

    def save_data(
        self,
        folder_name: Union[str, None] = None,
        save_folder_location: Union[str, Path, None] = None,
        append_yaml_hash_to_folder_name: bool = False,
        use_custom_column_names: bool = False,
        custom_column_names_dict: Union[dict, None] = None,
    ):
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
        if folder_name is None:
            folder_name = self.site_information.site_name
        if save_folder_location is None:
            save_folder_location = Path.cwd()

        saver = SaveAndArchiveOutputs(
            folder_name=folder_name,
            processed_data_frame=self.crns_data_frame,
            flag_data_frame=self.flags_data_frame,
            site_information=self.site_information,
            save_folder_location=save_folder_location,
            append_yaml_hash_to_folder_name=append_yaml_hash_to_folder_name,
            use_custom_column_names=use_custom_column_names,
            custom_column_names_dict=custom_column_names_dict,
        )
        saver.save_outputs()
