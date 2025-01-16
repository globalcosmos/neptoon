"""
Here are basic figures for creating plots.
"""

import pandas as pd
import numpy as np
from typing import List
from figurex import Figure
from neptoon.columns import ColumnInfo
import matplotlib.pyplot as plt
import seaborn as sns
import math


def validate_columns_present(
    data_frame: pd.DataFrame,
    required_cols: List[str],
):
    """
    Utility function to validate column existence in data frame
    Raises ValueError if columns are missing
    """
    missing = [col for col in required_cols if col not in data_frame.columns]
    if missing:
        raise ValueError(f"Required columns missing from dataframe: {missing}")


def some_other_figure():
    pass


def make_nmdb_data_figure(
    data_frame: pd.DataFrame,
    station_name: str,
    reference_value: int,
    incoming_neutron_col_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
    resolution: int = 60,
    show: bool = False,
    save_location: str = None,
):
    """
    Makes the figure

    Parameters
    ----------
    data_frame : pd.DataFrame
        DataFrame containing data
    station_name : str
        Station name
    reference_value : int
        reference value
    resolution : int, optional
        resolution in minutes, by default 60
    show : bool, optional
        show interactively, by default False
    save : str
        The save path

    Returns
    -------
    BytesIO
        Figure object to be used for later display
    """

    validate_columns_present(
        data_frame=data_frame, required_cols=[incoming_neutron_col_name]
    )

    with Figure(
        title="Incoming cosmic radiation",
        size=(12, 3),
        transparent=False,
        x_range=(data_frame.index.min(), data_frame.index.max()),
        show=show,
        save=(save_location if save_location else None),
    ) as ax:

        ax.plot(
            data_frame.index,
            data_frame[incoming_neutron_col_name],
            label="Station {:}, resolution: {:} minutes".format(
                station_name,
                resolution,
            ),
        )
        ax.axhline(
            reference_value,
            ls=":",
            lw=1,
            label="Reference value",
        )
        ax.set_ylabel("Neutron count rate (counts)")
        ax.legend()


def soil_moisture_coloured_figure(
    data_frame: pd.DataFrame,
    station_name: str,
    sm_column_name: str = str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
    lower_bound: float = 0,
    save_location: str = None,
):
    validate_columns_present(
        data_frame=data_frame, required_cols=[sm_column_name]
    )

    # produce colour pallete
    nsteps = 50
    colrange = sns.diverging_palette(
        29, 255, 85, 47, n=nsteps, sep=1, center="light"
    )
    prcnt35 = math.ceil(
        len(colrange) * 0.30
    )  # Apply to allow changes to n bins
    prcnt65 = math.ceil(len(colrange) * 0.55)
    colrange2 = colrange[0:prcnt35] + colrange[prcnt65:nsteps]
    ymax = data_frame[sm_column_name].max()
    steps = ymax / nsteps
    gradrange = list(np.arange(0, ymax, steps))

    # produce figure
    fig, ax = plt.subplots(figsize=(15, 3.75))
    ax.plot(
        data_frame[sm_column_name],
        lw=0.1,
        label="Soil Moisture Volumetric (cm$^3$/cm$^3$)",
        color="black",
    )
    ax.set_ylabel("Soil Moisture - Volumetric (cm$^3$/cm$^3$)")
    ax.set_xlabel("Date")
    ax.set_title("Soil Moisture over time at " + str(station_name))
    ax.plot(
        data_frame.index,
        data_frame[sm_column_name],
        lw=0.1,
        label="Soil Moisture Volumetric (cm$^3$/cm$^3$)",
        color="black",
    )

    ymaxplus = ymax * 1.05
    ax.set_ylim(lower_bound, ymaxplus)
    for i in range(len(colrange2)):
        ax.fill_between(
            data_frame.index,
            lower_bound,
            data_frame[sm_column_name],
            where=data_frame[sm_column_name] > gradrange[i],
            facecolor=colrange2[i],
            alpha=0.2,
        )
    if save_location:
        fig.savefig(save_location)
