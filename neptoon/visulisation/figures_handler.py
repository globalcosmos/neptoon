import pandas as pd
from neptoon.config.configuration_input import SensorInfo
from neptoon.visulisation.figures import make_nmdb_data_figure
from neptoon.columns import ColumnInfo
from typing import List
from magazine import Magazine


class HandleFigures:

    def __init__(
        self,
        data_frame: pd.DataFrame,
        sensor_info: SensorInfo,
        create_all: bool = False,
        figures_to_make: List[str] = None,
    ):
        self.data_frame = data_frame
        self.sensor_info = sensor_info
        self.create_all = create_all
        self.figures_to_make = figures_to_make

    @Magazine.reporting(topic="NMDB")
    def nmdb_figure_1(self):

        reference_value = self.data_frame[
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE)
        ].iloc[0]

        make_nmdb_data_figure(
            data_frame=self.data_frame,
            station_name=self.sensor_info.name,
            reference_value=reference_value,
        )

    def create_figures(self):
        if self.create_all:
            # Loop through all figs
            pass
        else:
            # Go through
            pass
