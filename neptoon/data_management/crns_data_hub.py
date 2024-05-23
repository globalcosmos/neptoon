import pandas as pd
import logging
import numpy as np
from neptoon.configuration.configuration_input import ConfigurationManager
from neptoon.data_management.data_validation_tables import (
    FormatCheck,
)
from saqc import SaQC
from neptoon.logging import get_logger

core_logger = get_logger()


class CRNSDataHub:
    """
    The CRNSDataHub is used to manage the time series data throughout
    the processing steps. Some key features:

    - It stores a DataFrame for a site
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
        configuration_manager: ConfigurationManager = None,
        quality_assessor: SaQC = None,
        validation: bool = True,
        journalist: bool = True,
    ):
        """
        Inputs to the CRNSDataHub.

        Parameters
        ----------
        crns_data_frame : pd.DataFrame
            CRNS data in a dataframe format. It will be validated to
            ensure it has been formatted correctly.
        configuration_manager : ConfigurationManager, optional
            A ConfigurationManager instance storing configuration YAML
            information, by default None
        quality_assessor : SaQC
            SaQC object which is used for quality assessment. Used for
            the creation of flags to define poor data.
        validation : bool
            Toggle for whether to have continued validation of data
            tables during processing (see
            data_management>data_validation_tables.py for examples of
            tables being validated). These checks ensure data is
            correctly formatted for internal processing.
        journalist : bool
            Whether the journalist class will be used to collect info on
            key data throughout processing. Default is True.
        """
        self._crns_data_frame = crns_data_frame
        if configuration_manager is not None:
            self._configuration_manager = configuration_manager
        self._validation = validation
        self._quality_assessor = quality_assessor

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df):
        self._crns_data_frame = df

    @property
    def validation(self):
        return self._validation

    @property
    def quality_assessor(self):
        return self._quality_assessor

    @quality_assessor.setter
    def quality_assessor(self, assessor):
        self._quality_assessor = assessor

    def validate_dataframe(self, schema: str):
        """
        Validates the dataframe against a pandera schema See
        data_validation_table.py for schemas.

        Parameters
        ----------
        schema : str
            The name of the schema to use for the check.
        """

        if schema == "initial_check":
            tmpdf = self.crns_data_frame
            FormatCheck.validate(tmpdf, lazy=True)
        elif schema == "before_corrections_check":
            pass
        elif schema == "after_corrections_check":
            pass
        elif schema == "final_check":
            pass
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
        pass

    def save_data(self, folder_path, file_name, step):  #
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

    def add_column_to_crns_data_frame(
        self, source, column_name: str = None, new_column_name: str = None
    ):
        if isinstance(source, pd.DataFrame):
            if column_name is None:
                raise ValueError(
                    "Must specify a column name "
                    "when the source is DataFrame"
                )
            if new_column_name is None:
                new_column_name = column_name
            if not isinstance(source.index, pd.DatetimeIndex):
                raise ValueError("DataFrame source must have a DatetimeIndex.")
            mapped_data = source[column_name].reindex(
                self.crns_data_frame.index, method="nearest"
            )
        elif isinstance(source, dict):
            if new_column_name is None:
                raise ValueError(
                    "New column name must be specified when source is a dictionary"
                )
            mapped_data = pd.Series(source).reindex(
                self.crns_data_frame.index, method="nearest"
            )
        else:
            raise TypeError(
                "Source must be either a DataFrame or a dictionary"
            )
        self.crns_data_frame[new_column_name] = mapped_data
