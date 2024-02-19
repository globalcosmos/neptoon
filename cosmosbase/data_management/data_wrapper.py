"""
This
"""

import pandas as pd


class DataFrameWrapper:
    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe

    def __repr__(self) -> str:
        return repr(self.dataframe)

    def save_data(self, folder_path: str, file_name: str):
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
        file_name_and_save_location = folder_path + file_name + ".csv"
        self.dataframe.to_csv(file_name_and_save_location)
