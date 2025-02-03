"""
Here are basic figures for creating plots.
"""

import pandas as pd
import numpy as np
from typing import List
from figurex import Figure, Panel
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


def make_nmdb_data_figure(
    data_frame: pd.DataFrame,
    station_name: str,
    reference_value: int,
    incoming_neutron_col_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
    resolution: int = 60,
    show: bool = False,
    backend: str = "agg",
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
    backend : str, optional
        the backend to use in matplotlib, by default "agg
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
    show = True  # REMOVE

    with Figure(
        title="Incoming cosmic radiation",
        size=(12, 3),
        transparent=False,
        x_range=(data_frame.index.min(), data_frame.index.max()),
        show=show,
        save=(save_location if save_location else None),
        backend=backend,
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


def uncorr_and_corr_neutrons_figure(
    data_frame: pd.DataFrame,
    station_name: str,
    raw_neutron_col_name: str = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
    corr_neutron_col_name: str = str(
        ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
    ),
    show=False,
    backend: str = "agg",
    save_location: str = None,
):
    with Figure(
        title=f"Neutron counts at {station_name}",
        size=(12, 3),
        transparent=False,
        x_range=(data_frame.index.min(), data_frame.index.max()),
        show=show,
        save=(save_location if save_location else None),
        backend=backend,
    ) as ax:
        ax.plot(
            data_frame.index,
            data_frame[raw_neutron_col_name],
            label="Uncorrected epitherma neutrons",
        ),

        ax.plot(
            data_frame.index,
            data_frame[corr_neutron_col_name],
            label="Corrected epithermal neturons",
        )

        ax.set_ylabel("Neutron count rate (cph)")
        ax.legend()


def soil_moisture_figure_uncertainty(
    data_frame: pd.DataFrame,
    station_name: str,
    soil_moisture_col: str = str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
    upper_uncertainty_col: str = str(
        ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_UPPER
    ),
    lower_uncertainty_col: str = str(
        ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_LOWER
    ),
    sm_range: tuple = (
        0,
        0.5,
    ),
    show: bool = False,
    backend: str = "agg",
    save_location: str = None,
):
    """
    Creates a two-panel figure showing soil moisture content and
    associated uncertainties.

    The top panel displays the soil moisture time series. The bottom
    panel shows the uncertainty bounds as separate lines with filled
    regions to emphasize the error margins.

    Parameters
    ----------
    data_frame : pd.DataFrame
        DataFrame containing the soil moisture and uncertainty data
    station_name : str
        Name of the CRNS station for the title
    soil_moisture_col : str, optional
        Column name for soil moisture data, defaults to
        SOIL_MOISTURE_FINAL
    upper_uncertainty_col : str, optional
        Column name for upper uncertainty bound
    lower_uncertainty_col : str, optional
        Column name for lower uncertainty bound
    sm_range : tuple, optional
        Y-axis range for soil moisture plots as (min, max), defaults to
        (0, 0.5)
    show : bool, optional
        Whether to display the figure, defaults to False
    backend : str, optional
        Matplotlib backend to use, defaults to "agg"
    save_location : str, optional
        Path to save the figure, if None the figure is not saved

    Returns
    -------
    None
        The figure is either displayed, saved, or both based on
        parameters
    """
    with Figure(
        title=f"Soil Moisture Content at {station_name}",
        size=(12, 8),
        transparent=False,
        x_range=(data_frame.index.min(), data_frame.index.max()),
        layout=(2, 1),
        show=show,
        save=(save_location if save_location else None),
        backend=backend,
    ) as (ax1, ax2):
        # Top panel: Soil moisture content
        ax1.plot(
            data_frame.index,
            data_frame[soil_moisture_col],
            color="C0",
            drawstyle="steps-post",
            lw=1,
            label="Water content",
        )
        ax1.set_ylim(sm_range[0], sm_range[1])
        ax1.set_ylabel("Water content (m³/m³)")
        ax1.grid(alpha=0.2)
        ax1.legend()

        # Bottom panel: Uncertainty bounds
        ax2.plot(
            data_frame.index,
            data_frame[lower_uncertainty_col],
            color="C3",
            drawstyle="steps-post",
            lw=0.6,
            label="Lower uncertainty",
        )
        ax2.plot(
            data_frame.index,
            data_frame[upper_uncertainty_col],
            color="C2",
            drawstyle="steps-post",
            lw=0.6,
            label="Upper uncertainty",
        )

        # Fill uncertainty regions
        ax2.fill_between(
            data_frame.index,
            data_frame[upper_uncertainty_col],
            data_frame[lower_uncertainty_col],
            color="C3",
            alpha=0.2,
            step="post",
        )

        max_uncertainty = max(
            data_frame[upper_uncertainty_col].max(),
            abs(data_frame[lower_uncertainty_col].min()),
        )
        y_limit = max_uncertainty * 1.1  # Add 10% padding

        ax2.set_ylim(0, y_limit)
        ax2.set_ylabel("Water content (m³/m³)")
        ax2.grid(alpha=0.2)
        ax2.legend()


def soil_moisture_coloured_figure(
    data_frame: pd.DataFrame,
    station_name: str,
    sm_column_name: str = str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
    lower_bound: float = 0,
    save_location: str = None,
):
    """
    Soil moisture plot which fills below the line colours between blue
    and brown to represent wet vs dry periods.

    Parameters
    ----------
    data_frame : pd.DataFrame
        time series data
    station_name : str
        name of the station
    sm_column_name : str, optional
        column name containing soil moisture data, by default
        str(ColumnInfo.Name.SOIL_MOISTURE_FINAL)
    lower_bound : float, optional
        lower bound of y-axis, by default 0
    save_location : str, optional
        location to save data if desired, by default None
    """
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
