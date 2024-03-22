import pandas as pd
from configuration.configuration_input import ConfigurationManager
from cosmosbase.data_management.data_audit import DataAuditLog

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
    """

    def __init__(
        self,
        raw_data_frame: pd.DataFrame,
        column_names: dict = None,
        data_audit_log: DataAuditLog = None,
    ):
        """_summary_

        Parameters
        ----------
        raw_data_frame : pd.DataFrame
            _description_
        column_names : dict, optional
            _description_, by default None
        """

        self._raw_data_frame = raw_data_frame
        self._dataframe_flags = pd.DataFrame(
            0, index=raw_data_frame.index, columns=raw_data_frame.columns
        )
        self._dataframe_uncertanties = pd.DataFrame(index=raw_data_frame.index)
        self._processing_meta_data = None

    def expand_dataframe_flags(self):
        """
        Code which expands the dataframe_flags when new data is in the
        dataframe. This could be a comparison of columns, and then add
        columns missing from flags.
        """
        pass

    def attach_flags(self, flag_series):
        """
        This code will replace a column with flags.
        """
        pass

    def validate_dataframe(self, scheme: str):
        """
        Validates the dataframe against a validation scheme from within
        the data_validation_table.py module

        scheme will be a str to know what stage is being validated.
        """
        pass

    def save_data(self, folder_path, file_name):
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
        file_name_and_save_location = folder_path + file_name + ".csv"
        self.dataframe.to_csv(file_name_and_save_location)

    def archive_data(self, folder_path, file_name):
        """
        Archive the data into a zip file. All the data tables in the
        instance will be collected and saved together.

        Parameters
        ----------
        folder_path : _type_
            _description_
        file_name : _type_
            _description_
        """
