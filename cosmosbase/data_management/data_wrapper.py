import pandas as pd
from configuration.configuration_input import ConfigurationManager

"""
This
"""


class CRNSDataHub:
    """
    The CRNSDataHub is used to manage the time series data throughout
    the processing steps. Some key features:

    - It stores a DataFrame for a site
    - It creates a shadow DataFrame which stores flag values
    - It creates another shadow DataFrame which stores uncertainty
      values (to keep things clean)
    - As we progress through the steps, data can be added to the
      DataFrame and the shadow DataFrame's updated.
    - It adds the configuration manager to ensure metadata and CRNS data
      are together

    Features to add:

    - Add a function for returning a dataframe with flags applied (i.e.
      Data Removed)
    - Think how to support multiple sensors e.g., Pressure sensors, we
      don't want to remove secondary data but ultimately we want to work
      with a single value. This could be an average of the sensors? We
      then want to keep the pressure data but work with one value.
    """

    def __init__(
        self, dataframe: pd.DataFrame, config_manager: ConfigurationManager
    ):
        self.dataframe = dataframe
        self.dataframe_flags = pd.DataFrame(
            0, index=dataframe.index, columns=dataframe.columns
        )
        self.dataframe_uncertanties = pd.DataFrame(index=dataframe.index)
        self.config = config_manager

    def psuedo_qa_1(self):
        """
        Take the dataframe, collect information about the type of QA
        required and create a table which uses.
        """
        if self.config.processing.qa1 == "standard":
            pass

    def expand_dataframe_flags(self):
        """
        Code which expands the dataframe_flags when new data is in the
        dataframe. This could be a comparison of columns, and then add
        columns missing from flags.
        """
        pass

    def save_data(self, folder_path, file_name):
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
