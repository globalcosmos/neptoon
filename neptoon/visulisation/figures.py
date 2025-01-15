"""
Here are basic figures for creating plots.
"""

import pandas as pd
from typing import List
from figurex import Figure
from neptoon.columns import ColumnInfo


def return_obj():
    pass


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
    return_as_obj=False,
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
    save : None


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
        x_range=(data_frame.index.min(), data_frame.index.max()),
        show=show,
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

    if return_as_obj:
        return_obj()
