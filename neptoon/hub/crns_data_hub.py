import pandas as pd
import numpy as np
from typing import Literal, Union, Optional
from pathlib import Path
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
    NeutronUncertaintyCalculator,
)
from neptoon.config.configuration_input import SensorInfo
from neptoon.products.estimate_sm import NeutronsToSM
from neptoon.quality_control.data_validation_tables import (
    FormatCheck,
)
from neptoon.quality_control import (
    QualityAssessmentFlagBuilder,
    DataQualityAssessor,
)
from neptoon.visulisation.figures_handler import FigureHandler
from neptoon.io.save import SaveAndArchiveOutputs
from neptoon.data_prep.smoothing import SmoothData
from neptoon.data_prep.conversions import AbsoluteHumidityCreator
from neptoon.columns import ColumnInfo
from neptoon.logging import get_logger
from magazine import Magazine

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
        flags_data_frame: pd.DataFrame | None = None,
        sensor_info: SensorInfo | None = None,
        quality_assessor: DataQualityAssessor | None = None,
        validation: bool = True,
        calibration_samples_data: pd.DataFrame | None = None,
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
        calibration_samples_data : pd.DataFrame
            The sample data taken during the calibration campaign.
        """

        self._raw_data = crns_data_frame.copy()
        self._crns_data_frame = crns_data_frame
        self._flags_data_frame = flags_data_frame
        self._sensor_info = sensor_info
        self._validation = validation
        self._quality_assessor = quality_assessor
        self._calibration_samples_data = calibration_samples_data
        self._correction_factory = CorrectionFactory()
        self._correction_builder = CorrectionBuilder()
        self.calibrator = None
        self.figure_creator = None
        self.magazine_active = [Magazine.active if Magazine.active else False]

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
    def sensor_info(self):
        return self._sensor_info

    @sensor_info.setter
    def sensor_info(self, new_config: SensorInfo):
        self._sensor_info = new_config

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

    @Magazine.reporting(topic="NMDB")
    def attach_nmdb_data(
        self,
        station="JUNG",
        new_column_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
        resolution="60",
        nmdb_table="revori",
        reference_value: int | None = None,
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
        reference_value : int, optional
            The reference value of the neutron monitor, if left as None
            it will use the value from the first data point in the time
            series.
        Report
        ------
        Neutron monitoring data was attached from NMDB.eu. The station
        used was {station} at a resolution of {resolution} minutes. The
        data table used was {nmdb_table}.
        """
        attacher = NMDBDataAttacher(
            data_frame=self.crns_data_frame, new_column_name=new_column_name
        )
        attacher.configure(
            station=station,
            reference_value=reference_value,
            resolution=resolution,
            nmdb_table=nmdb_table,
        )
        attacher.fetch_data()
        attacher.attach_data()
        self.crns_data_frame = attacher.return_data_frame()

    def add_quality_flags(
        self,
        custom_flags: QualityAssessmentFlagBuilder | None = None,
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
        self.crns_data_frame = self.mask_flagged_data(
            data_frame=self.crns_data_frame
        )
        message = "Flagging of data complete using Custom Flags"
        core_logger.info(message)

    def select_correction(
        self,
        correction_type: CorrectionType | str = "empty",
        correction_theory: CorrectionTheory | None = None,
    ):
        """
        Method to select corrections to be applied to data.

        Individual corrections can be applied using a CorrectionType and
        CorrectionTheory. If a user assigns a CorrectionType without a
        CorrectionTheory, then the default correction for that
        CorrectionType is applied.

        Parameters
        ----------
        correction_type : CorrectionType, optional
            A CorrectionType, by default "empty"
        correction_theory : CorrectionTheory, optional
            A CorrectionTheory, by default None
        """

        correction = self.correction_factory.create_correction(
            correction_type=correction_type,
            correction_theory=correction_theory,
        )
        self.correction_builder.add_correction(correction=correction)

    def correct_neutrons(
        self,
    ):
        """
        Create correction factors as well as the corrected epithermal
        neutrons column.
        """
        corrector = CorrectNeutrons(
            crns_data_frame=self.crns_data_frame,
            correction_builder=self.correction_builder,
        )
        self.crns_data_frame = corrector.correct_neutrons()

    def create_neutron_uncertainty_bounds(self):
        """
        Create uncertainty bounds for statistical uncertainty of neutron
        count rates.
        """

        uncertainty = NeutronUncertaintyCalculator(
            data_frame=self.crns_data_frame
        )
        self.crns_data_frame = uncertainty.add_neutron_uncertainty_columns()

    @Magazine.reporting(topic="Data Preparation")
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

        Report
        ------
        Data smoothing was done on {column_to_smooth}. This was done
        using {smooth_method} with a window of {window}.
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

    @Magazine.reporting(topic="Calibration")
    def calibrate_station(
        self,
        config: CalibrationConfiguration = None,
    ):
        """
        Calibrate the sensor

        Parameters
        ----------
        config : CalibrationConfiguration, optional
            Config file which contains all the required info for
            calibration, by default None

        Raises
        ------
        ValueError
            When no calibration data provided

        Report
        ------
        Calibration was undertaken. The N0 number was calculated as
        {n0}, using the {config.neutron_conversion_method} method. From the samples, the average dry soil bulk density is
        {avg_dry_soil_bulk_density}, the average soil organic carbon is
        {avg_soil_organic_carbon}, and the average lattice water content
        is {avg_lattice_water}.
        """
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
        n0 = int(self.calibrator.find_n0_value())
        avg_dry_soil_bulk_density = round(
            self.calibrator.calibrator.calib_data_object.list_of_profiles[
                0
            ].site_avg_bulk_density,
            4,
        )
        avg_soil_organic_carbon = round(
            self.calibrator.calibrator.calib_data_object.list_of_profiles[
                0
            ].site_avg_organic_carbon,
            4,
        )
        avg_lattice_water = round(
            self.calibrator.calibrator.calib_data_object.list_of_profiles[
                0
            ].site_avg_lattice_water,
        )
        self.sensor_info.N0 = n0
        self.sensor_info.avg_dry_soil_bulk_density = avg_dry_soil_bulk_density
        self.sensor_info.avg_lattice_water = avg_lattice_water
        self.sensor_info.avg_soil_organic_carbon = avg_soil_organic_carbon
        print(f"N0 number was calculated as {n0}")

    @Magazine.reporting(topic="Soil Moisture")
    def produce_soil_moisture_estimates(
        self,
        n0: float | None = None,
        conversion_theory: Literal[
            "desilets_etal_2010", "koehli_eta_2021"
        ] = "desilets_etal_2010",
        dry_soil_bulk_density: float | None = None,
        lattice_water: float | None = None,
        soil_organic_carbon: float | None = None,
        koehli_method_form: Literal[
            "Jan23_uranos",
            "Jan23_mcnpfull",
            "Mar12_atmprof",
            "Mar21_mcnp_drf",
            "Mar21_mcnp_ewin",
            "Mar21_uranos_drf",
            "Mar21_uranos_ewin",
            "Mar22_mcnp_drf_Jan",
            "Mar22_mcnp_ewin_gd",
            "Mar22_uranos_drf_gd",
            "Mar22_uranos_ewin_chi2",
            "Mar22_uranos_drf_h200m",
            "Aug08_mcnp_drf",
            "Aug08_mcnp_ewin",
            "Aug12_uranos_drf",
            "Aug12_uranos_ewin",
            "Aug13_uranos_atmprof",
            "Aug13_uranos_atmprof2",
        ] = "Mar21_uranos_drf",
    ):
        """
        Produces SM estimates with the NeutronsToSM class. If values for
        n0, dry_soil_bulk_density, lattice_water, or soil_organic_carbon
        are not supplied, the values are taken from the internal
        sensor_info class.

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

        Report
        ------
        Soil moisture was estimated using an n0 of {default_params[n0]},
        a bulk density of {default_params[dry_soil_bulk_density]}, a
        lattice water content of {default_params[lattice_water]}, and a
        soil organic carbon content of
        {default_params[soil_organic_carbon]}
        """
        print("Producing soil moisture estimates.")
        # Create attributes for NeutronsToSM
        default_params = {
            "n0": self.sensor_info.N0,
            "dry_soil_bulk_density": self.sensor_info.avg_dry_soil_bulk_density,
            "lattice_water": self.sensor_info.avg_lattice_water,
            "soil_organic_carbon": self.sensor_info.avg_soil_organic_carbon,
        }
        provided_params = {
            "n0": n0,
            "dry_soil_bulk_density": dry_soil_bulk_density,
            "lattice_water": lattice_water,
            "soil_organic_carbon": soil_organic_carbon,
            "conversion_theory": conversion_theory,
            "koehli_method_form": koehli_method_form,
        }
        params = {k: v for k, v in provided_params.items() if v is not None}
        default_params.update(params)

        soil_moisture_calculator = NeutronsToSM(
            crns_data_frame=self.crns_data_frame, **default_params
        )
        soil_moisture_calculator.calculate_all_soil_moisture_data()
        self.crns_data_frame = soil_moisture_calculator.return_data_frame()

    def mask_flagged_data(self, data_frame: pd.DataFrame):
        """
        Returns a pd.DataFrame() where flagged data has been replaced
        with np.nan values
        """
        mask = self.flags_data_frame == "UNFLAGGED"
        data_frame[~mask] = np.nan
        return data_frame

    def prepare_static_values(self):
        """
        Attaches the static values from the SensorInfo Pydantic model as
        columns of values in the crns_data_frame.

        This method:
        1. Converts the Pydantic model to a dictionary
        2. Checks if each key already exists in the DataFrame
        3. Skips None values
        4. Adds the remaining values as new columns

        The method preserves existing column values if they are already
        present in the DataFrame to avoid accidental overwrites.
        """

        sensor_info_dict = self.sensor_info.model_dump()
        for key, value in sensor_info_dict.items():
            if key in self.crns_data_frame.columns:
                message = (
                    f"{key} already found in columns of crns_data_frame"
                    " when trying to add static values from sensor_info."
                    "This value from SensorInfo was not written to the"
                    " crns_data_frame."
                )
                core_logger.info(message)
                continue
            elif value is None:
                # TODO add skip here
                continue
            else:
                self.crns_data_frame[key] = value

    def prepare_additional_columns(self):
        """
        Prepares and adds additional columns required for processing.

        Such as:
           - absolute humidity
        """
        abs_hum_creator = AbsoluteHumidityCreator(
            data_frame=self.crns_data_frame
        )
        self.crns_data_frame = (
            abs_hum_creator.check_and_return_abs_hum_column()
        )

    def create_figures(
        self,
        create_all=True,
        ignore_sections=[],
        selected_figures=[],
        show_figures: bool = False,
    ):
        """
        Handles creating the figures using the FigureHandler.

        Parameters
        ----------
        create_all : bool, optional
            Default to create all figures in the
            FigureHandler._register, by default True
        ignore_sections : list, optional
            Ignore a whole topic section of figure names, by default []
        selected_figures : list, optional
            A list of the figures to be created if not using create_all.
            See FigureHandler._figure_registry for the names of possible
            figures, by default []
        show_figures : bool, optional
            Turn to False to not show Figures in the kernel, by default
            True
        """
        self.figure_creator = FigureHandler(
            data_frame=self.crns_data_frame,
            sensor_info=self.sensor_info,
            create_all=create_all,
            ignore_sections=ignore_sections,
            selected_figures=selected_figures,
            show_figures=show_figures,
        )
        self.figure_creator.create_figures()

    def save_data(
        self,
        folder_name: Union[str, None] = None,
        save_folder_location: Union[str, Path, None] = None,
        append_audit_log_hash_to_folder_name: bool = False,
        use_custom_column_names: bool = False,
        custom_column_names_dict: Union[dict, None] = None,
        append_timestamp: bool = True,
    ):
        """
        Saves the file to a specified location. It must contain the
        correct folder_path and file_name.

        Parameters
        ----------
        folder_path : str
            Path to the save folder
        file_name : str
            Name of the file
        """
        if folder_name is None:
            folder_name = self.sensor_info.name
        if save_folder_location is None:
            save_folder_location = Path.cwd()
        if self.calibrator:
            calib_df = self.calibrator.return_calibration_results_data_frame()
        else:
            calib_df = None

        self.saver = SaveAndArchiveOutputs(
            folder_name=folder_name,
            processed_data_frame=self.crns_data_frame,
            flag_data_frame=self.flags_data_frame,
            sensor_info=self.sensor_info,
            save_folder_location=save_folder_location,
            append_audit_log_hash_to_folder_name=append_audit_log_hash_to_folder_name,
            use_custom_column_names=use_custom_column_names,
            custom_column_names_dict=custom_column_names_dict,
            append_timestamp=append_timestamp,
            figure_handler=self.figure_creator,
            calib_df=calib_df,
            magazine_active=self.magazine_active,
        )
        self.saver.save_outputs()
