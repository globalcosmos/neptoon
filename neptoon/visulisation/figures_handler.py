import pandas as pd
from dataclasses import dataclass
from neptoon.config.configuration_input import SensorInfo
from neptoon.visulisation.figures import (
    make_nmdb_data_figure,
    soil_moisture_coloured_figure,
    soil_moisture_figure_uncertainty,
    uncorr_and_corr_neutrons_figure,
    atmospheric_conditions_figure,
    correction_factors_figure,
)
from neptoon.columns import ColumnInfo
from typing import List, Optional
from enum import Enum
from magazine import Magazine
from pathlib import Path
import tempfile
import atexit
import shutil


class FigureTopic(Enum):
    NMDB = "nmdb"
    NEUTRONS = "neutrons"
    SOIL_MOISTURE = "soil_moisture"
    ATMOSPHERIC = "atmospheric"


@dataclass
class FigureMetadata:
    """
    Key information on each figure created.

    topic : FigureTopic
        The topic the figure is related to
    description : str
        A brief description about the figure
    required_columns: List[str]
        The columns required for this particular figure.
    method : callable
        The method (found in FigureHandler) which will be called to
        produce this figure.
    """

    topic: FigureTopic
    description: str
    required_columns: List[str]
    method: callable


@dataclass
class TempFigure:
    """
    Tracks a temporary figure file

    name : str
        Name of the figure

    """

    name: str
    path: Path
    topic: str


class TempFigureHandler:
    """
    Handles the creation and storage of figures made with the
    FigureHandler by creating a temp directory, recording paths for each
    figure, and removing temp files upon program exit.
    """

    def __init__(
        self,
    ):
        self._temp_dir = Path(tempfile.mkdtemp(prefix="neptoon_figures_"))
        self.figures: List[TempFigure] = []
        atexit.register(self.cleanup)

    def store_figure(self, name: str, topic: FigureTopic):
        """
        Stores metadata of temporary figure storage

        Parameters
        ----------
        name : str
            name of the figure being stored
        topic : FigureTopic
            Topic the figure is part of (e.g., NMDB, or Soil)

        Returns
        -------
        Path
            Path of the temp figure
        """
        temp_path = self._temp_dir / f"{name}.png"
        self.figures.append(
            TempFigure(
                name=name,
                path=temp_path,
                topic=topic,
            )
        )
        return temp_path

    def cleanup(self):
        """Remove temporary directory and files"""
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)

    def get_figures(self, topic: Optional[FigureTopic] = None):
        """
        Collect the figures that are saved

        Parameters
        ----------
        topic : FigureTopic
            Topic the figure is part of (e.g., NMDB, or Soil)

        Returns
        -------
        List[TempFigure]
            A list of TempFigure objects with location of save files.
        """
        if topic is None:
            return self.figures
        return [fig for fig in self.figures if fig.topic == topic]


class FigureHandler:
    """
    Class to manage creating figures when data has been processed using the CRNSDataHub.
    """

    _figure_registry = {
        "nmdb_incoming_radiation": FigureMetadata(
            topic=FigureTopic.NMDB,
            description="NMDB incoming cosmic radiation plot",
            method="_nmdb_incoming_radiation",
            required_columns=[
                str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
                str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE),
            ],
        ),
        "correction_factors_figure": FigureMetadata(
            topic=FigureTopic.NEUTRONS,
            description="Correction factors applied to raw neutron counts",
            method="_neutron_correction_factors",
            required_columns=[],  # empty for flexibility
        ),
        "neutron_counts_corr_uncorr": FigureMetadata(
            topic=FigureTopic.NEUTRONS,
            description="Corrected and uncorrected count rates at the sensor",
            method="_uncorr_and_corr_neutrons_figure",
            required_columns=[
                str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
                str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL),
            ],
        ),
        "soil_moisture_uncertainty": FigureMetadata(
            topic=FigureTopic.SOIL_MOISTURE,
            description="Soil moisture time series with uncertainty bounds",
            method="_soil_moisture_uncertainty",
            required_columns=[
                str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL),
                str(ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_LOWER),
                str(ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_UPPER),
            ],
        ),
        # "soil_moisture_coloured": FigureMetadata(
        #     topic=FigureTopic.SOIL_MOISTURE,
        #     description="Soil moisture time series with colour filling",
        #     method="_soil_moisture_colour",
        #     required_columns=[str(ColumnInfo.Name.SOIL_MOISTURE_FINAL)],
        # ),
        "atmospheric_variables": FigureMetadata(
            topic=FigureTopic.ATMOSPHERIC,
            description="Atmospheric variables.",
            method="_atmospheric_variables",
            required_columns=[
                str(ColumnInfo.Name.AIR_PRESSURE),
                str(ColumnInfo.Name.AIR_TEMPERATURE),
                str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY),
                str(ColumnInfo.Name.ABSOLUTE_HUMIDITY),
            ],
        ),
    }

    def __init__(
        self,
        data_frame: pd.DataFrame,
        sensor_info: SensorInfo,
        create_all: bool = False,
        ignore_sections: List = None,
        selected_figures: List[str] = None,
        show_figures: bool = False,
        backend: str = "Agg",
    ):

        self.data_frame = data_frame
        self.sensor_info = sensor_info
        self.temp_handler = TempFigureHandler()
        self.create_all = create_all
        self.ignore_sections = (
            ignore_sections if ignore_sections is not None else []
        )
        self.selected_figures = (
            selected_figures if selected_figures is not None else []
        )
        self.show_figures = show_figures
        self.backend = backend

    def _validate_required_columns(self, metadata: FigureMetadata):
        """
        Validates that the required columns are present in the data
        frame

        Parameters
        ----------
        metadata : FigureMetadata
            An instance of FigureMetadata

        Raises
        ------
        ValueError
            When missing columns necessary for processing
        """

        missing_cols = [
            col
            for col in metadata.required_columns
            if col not in self.data_frame.columns
        ]
        if missing_cols:
            raise ValueError(
                f"DataFrame is missing required columns: {missing_cols}"
            )

    def _resolve_method(self, metadata: FigureMetadata):
        """
        Resolves the method string to an actual callable method.

        """
        method_name = metadata.method
        if not hasattr(self, method_name):
            raise AttributeError(
                f"Method {method_name} not found in {self.__class__.__name__}"
            )
        return getattr(self, method_name)

    @Magazine.reporting_figure(topic="NMDB")
    def _nmdb_incoming_radiation(self):
        """
        Implements nmdb figure 1
        """
        temp_path = self.temp_handler.store_figure(
            name="nmdb_incoming_radiation",
            topic=FigureTopic.NMDB,
        )
        reference_value = self.data_frame[
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE)
        ].iloc[0]

        make_nmdb_data_figure(
            data_frame=self.data_frame,
            # nmdb_station_name=self.sensor_info.name,
            reference_value=reference_value,
            incoming_neutron_col_name=str(
                ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY
            ),
            show=self.show_figures,
            backend=self.backend,
            save_location=temp_path,
        )

    @Magazine.reporting_figure(topic="Neutron Correction")
    def _uncorr_and_corr_neutrons_figure(self):
        """
        Implements uncorrected and corrected neutrons figures
        """
        temp_path = self.temp_handler.store_figure(
            name="neutron_counts_corr_uncorr",
            topic=FigureTopic.NEUTRONS,
        )
        uncorr_and_corr_neutrons_figure(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            raw_neutron_col_name=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
            corr_neutron_col_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
            ),
            show=self.show_figures,
            backend=self.backend,
            save_location=temp_path,
        )

    @Magazine.reporting_figure(topic="Soil Moisture")
    def _soil_moisture_uncertainty(self):
        """
        Implements soil moisture with uncertainty figure.
        """
        temp_path = self.temp_handler.store_figure(
            name="soil_moisture_uncertainty",
            topic=FigureTopic.SOIL_MOISTURE,
        )

        sm_max = (
            self.data_frame[str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL)].max()
        ) * 1.1
        sm_min = 0
        sm_range = (sm_min, sm_max)

        soil_moisture_figure_uncertainty(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            soil_moisture_col=str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL),
            upper_uncertainty_col=str(
                ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_UPPER
            ),
            lower_uncertainty_col=str(
                ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_LOWER
            ),
            sm_range=sm_range,
            show=self.show_figures,
            backend=self.backend,
            save_location=temp_path,
        )

    @Magazine.reporting_figure(topic="Soil Moisture")
    def _soil_moisture_colour(self):
        """
        Implements colour soil moisture figure.
        """
        temp_path = self.temp_handler.store_figure(
            name="soil_moisture_colour_fig",
            topic=FigureTopic.SOIL_MOISTURE_VOL,
        )

        soil_moisture_coloured_figure(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            sm_column_name=str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL),
            save_location=temp_path,
        )

    @Magazine.reporting_figure(topic="Atmospheric Conditions")
    def _atmospheric_variables(self):
        """
        Implements 3 panel figure with atmopsheric variables
        """
        temp_path = self.temp_handler.store_figure(
            name="atmospheric_variables",
            topic=FigureTopic.ATMOSPHERIC,
        )
        temperature_min = (
            self.data_frame[str(ColumnInfo.Name.AIR_TEMPERATURE)].min() - 2
        )
        temperature_max = (
            self.data_frame[str(ColumnInfo.Name.AIR_TEMPERATURE)].max() + 2
        )

        atmospheric_conditions_figure(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            pressure_col=str(ColumnInfo.Name.AIR_PRESSURE),
            temperature_col=str(ColumnInfo.Name.AIR_TEMPERATURE),
            rel_humidity_col=str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY),
            temperature_range=(temperature_min, temperature_max),
            show=self.show_figures,
            backend=self.backend,
            save_location=temp_path,
        )

    @Magazine.reporting_figure(topic="Neutron Correction")
    def _neutron_correction_factors(self):
        """
        Implements the correction factor figure
        """
        temp_path = self.temp_handler.store_figure(
            name="correction_factors_figure",
            topic=FigureTopic.NEUTRONS,
        )
        correction_factors_figure(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            pressure_corr_col=str(ColumnInfo.Name.PRESSURE_CORRECTION),
            humidity_corr_col=str(ColumnInfo.Name.HUMIDITY_CORRECTION),
            intensity_corr_col=str(ColumnInfo.Name.INTENSITY_CORRECTION),
            biomass_corr_col=str(
                ColumnInfo.Name.ABOVEGROUND_BIOMASS_CORRECTION
            ),
            show=self.show_figures,
            backend=self.backend,
            save_location=temp_path,
        )

    def _create_intended_figures_list(self):
        """
        Create a list of the figures to be created.

        Returns
        -------
        List
            List of figures to be made
        """
        # Get list of figures to create
        if self.selected_figures:
            figures_to_process = [
                name
                for name, metadata in self._figure_registry.items()
                if name in self.selected_figures
                and metadata.topic not in self.ignore_sections
            ]
        elif self.create_all:
            figures_to_process = [
                name
                for name, metadata in self._figure_registry.items()
                if metadata.topic not in self.ignore_sections
            ]
        else:
            figures_to_process = []

        return figures_to_process

    def create_figures(self):
        """
        Creates the figures
        """
        figures_to_process = self._create_intended_figures_list()

        # Create figures
        for figure_name in figures_to_process:
            try:
                metadata = self._figure_registry[figure_name]
                self._validate_required_columns(metadata=metadata)
                method = self._resolve_method(metadata=metadata)
                method()

            except Exception as e:
                print(f"Could not create figure {figure_name}: {str(e)}")
