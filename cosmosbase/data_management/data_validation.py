import pandas as pd
import logging

"""
    - Validate which columns are inlcuded in the data. There are
      essential columns, without which we are unable to process CRNS.
      There are warning columns, without which certain validation steps
      will be unavailable (although processing could still occur). And
      there are extra columns to support data not necessary for CRNS
      processing.
    - 
"""


class ValidateDataInclusion:

    def validate_essential_columns(
        self, dataframe: pd.DataFrame
    ) -> pd.DataFrame:
        for column in self.data_configuration.essential_columns:
            if column not in dataframe.columns:
                logging.error(f"Error: Missing essential column: {column}")
                raise ValueError(f"Missing essential column: {column}")

        return dataframe

    def validate_warning_columns(
        self, dataframe: pd.DataFrame
    ) -> pd.DataFrame:
        for column in self.data_configuration.warning_columns:
            if column not in dataframe.columns:
                logging.warning(
                    f"Warning: Missing recommended column: {column}"
                )

        return dataframe

    def validate_all_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = self.validate_essential_columns(dataframe)
        dataframe = self.validate_warning_columns(dataframe)

        return dataframe
