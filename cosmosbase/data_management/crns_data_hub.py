import pandas as pd
import logging
import numpy as np
from cosmosbase.configuration.configuration_input import ConfigurationManager
from cosmosbase.data_management.data_audit import DataAuditLog
from cosmosbase.data_management.data_validation_tables import (
    FormatCheck,
)


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

    Raw data is checked against the RawDataSchema which is a first line
    of defense against incorrectly formatted tables. Should a fail
    happen here data must be either reformatted using one of the
    provided routines or manually formatted to match the standard.
    """

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        data_audit_log: DataAuditLog = None,
        configuration_manager: ConfigurationManager = None,
        validation: bool = True,
    ):
        """
        Possible inputs to the CRNSDataHub.

        Parameters
        ----------
        crns_data_frame : pd.DataFrame
            CRNS data in a dataframe format. It will be validated to
            ensure it has been formatted correctly.
        data_audit_log : DataAuditLog, optional
            A DataAuditLog instance which, when present, will keep a log
            of all data transformation and processing steps to provide
            line of site to users with how data has been processed, by
            default None
        configuration_manager : ConfigurationManager, optional
            A ConfigurationManager instance storing configuration YAML
            information, by default None
        validation : bool
            Toggle for enforcement of continuous validation of data
            tables during processing (see
            data_management>data_validation_tables.py for examples of
            tables being validated). This is recommended to stay on but
            can be turned off for debugging or testing.
        """

        self._crns_data_frame = crns_data_frame
        self._validation = validation
        if self._crns_data_frame is not self._crns_data_frame.empty:
            self.flags_data_frame = pd.DataFrame(
                0, index=crns_data_frame.index, columns=crns_data_frame.columns
            )
        if self._crns_data_frame is not self._crns_data_frame.empty:
            self._uncertainty_data_frame = pd.DataFrame(
                index=crns_data_frame.index
            )
        if data_audit_log is not None:
            self._data_audit_log = data_audit_log
        if configuration_manager is not None:
            self._configuration_manager = configuration_manager

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df):
        self._crns_data_frame = df

    @property
    def validation(self):
        return self._validation

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

    def validate_dataframe(self, schema: str, table: str = None):
        """
        Validates the dataframe against a validation schema from within
        the data_validation_table.py module

        schema will be a str to know what stage is being validated.
        """

        if schema == "initial_check":
            tmpdf = self.crns_data_frame
            FormatCheck.validate(tmpdf)
        else:
            validation_error_message = (
                "Incorrect schema or table name given "
                "when validating the crns_data_frame"
            )
            logging.error(validation_error_message)
            print(validation_error_message)

    def replace_dataframe(self, dataframe):
        """
        Function to replace the dataframe when manual adjustments have
        been made. Not recommended for general processing, but can be
        used when testing new features or theories.

        TODO: How does this impact uncertainty/flags??
        CHANGES MUST BE CHECKED

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame that has been changed and you wish to replace
        """
        pass

    def return_cleaned_dataframe(self):
        mask = self.flags_data_frame != 0
        clean_df = self.crns_data_frame.where(~mask, np.nan)
        return clean_df

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

    def save_data_audit_log(self, folder_path, file_name):
        """
        Output the DataAuditLog into a YAML format for human reading

        Parameters
        ----------
        folder_path : str
            Path to folder where it should be saved
        file_name : str
            Desired name of the file
        """
        pass
