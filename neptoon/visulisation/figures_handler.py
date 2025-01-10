import pandas as pd
from dataclasses import dataclass, asdict
from neptoon.config.configuration_input import SensorInfo
from neptoon.visulisation.figures import (
    make_nmdb_data_figure,
    some_other_figure,
)
from neptoon.columns import ColumnInfo
from typing import List
from enum import Enum
from magazine import Magazine


@dataclass
class FigureMetadata:
    """Description of the Figures and what they are for"""

    topic: str
    description: str
    required_columns: List[str]
    method: callable


class FigureTopics(Enum):
    NMDB = "nmdb"
    NEUTRONS = "neutrons"
    SOIL_MOISTURE = "soil_moisture"


class CreateFigures:
    """
    Class to manage creating figures when data has been processed using the CRNSDataHub.
    """

    _figure_registry = {
        "nmdb_figure_1": FigureMetadata(
            topic=FigureTopics.NMDB,
            description="NMDB incoming cosmic radiation plot",
            method="_nmdb_figure_1",
            required_columns=[
                str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
                str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE),
            ],
        ),
        "soil_moisture_figure_1": FigureMetadata(
            topic=FigureTopics.SOIL_MOISTURE,
            description="Soil moisture time series with uncertainty bounds",
            method="_some_other_figure",
            required_columns=[str(ColumnInfo.Name.SOIL_MOISTURE_FINAL)],
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
    ):

        self.data_frame = data_frame
        self.sensor_info = sensor_info
        self.create_all = create_all
        self.ignore_sections = (
            ignore_sections if ignore_sections is not None else []
        )
        self.selected_figures = (
            selected_figures if selected_figures is not None else []
        )
        self.show_figures = show_figures

    def _validate_required_columns(self, metadata: FigureMetadata):

        missing_cols = [
            col
            for col in metadata.required_columns
            if col not in self.data_frame.columns
        ]
        if missing_cols:
            raise ValueError(
                f"DataFrame is missing required columns: {missing_cols}"
            )

    def _resolve_method(self, metadata: FigureMetadata) -> callable:
        """
        Resolves the method string to an actual callable method.

        """
        method_name = metadata.method
        if not hasattr(self, method_name):
            raise AttributeError(
                f"Method {method_name} not found in {self.__class__.__name__}"
            )
        return getattr(self, method_name)

    @Magazine.reporting(topic="NMDB")
    def _nmdb_figure_1(self):
        """
        Implements nmdb figure 1
        """

        reference_value = self.data_frame[
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE)
        ].iloc[0]

        make_nmdb_data_figure(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            reference_value=reference_value,
            incoming_neutron_col_name=str(
                ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY
            ),
            show=self.show_figures,
        )

    def create_figures(self):
        """
        Creates the figures
        """
        created_figures = []

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

        for figure_name in figures_to_process:
            metadata = self._figure_registry[figure_name]
            self._validate_required_columns(metadata=metadata)
            method = self._resolve_method(metadata=metadata)

            try:
                method()
                created_figures.append(figure_name)
            except Exception as e:
                print(f"Error creating {figure_name}: {str(e)}")

        return created_figures
