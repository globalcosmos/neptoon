# import pandas as pd
from abc import ABC, abstractmethod

"""
This module holds time series preperation classes and methods. The
class/methods in this module are designed to take time series data of
CRNS and format and validate them before use in cosmosbase processes.
This way standards can be ensured and the internal processing will be
robust.

Features:

    - Classes are available to convert standard data formats from the
      most common sensors into the internal format required for use in
      cosmosbase
    - A class that will convert the format described in the
      documentation into the internal cosmosbase format. This is
      available in case a data format is not currently supported by the
      classes within the module (NOTE: if you build a class for
      conversion of your own data and feel it will be useful for the
      community make an issue and we can add it in future updates!)
    - Change the naming convention to a standard format. Fill in the
      YAML file in sensor config files to allow the code to do this.
"""


class DataFormatFactory:
    """
    Class for figuring out what type of data loader to use to format
    data.

    Returns
    -------
    DataIngestRules(variant)
        One of the loader types from DataIngestRules

    Raises
    ------
    ValueError
        If incorrect format given, or if the autodetection fails
    """

    @staticmethod
    def get_loader(format_identifier=None, data=None):
        if format_identifier == "Standard":
            return StandardToDataFrame
        elif format_identifier == "HydroInnova":
            return HydroInnovaToDataFrame
        elif format_identifier == "FTP":
            return FTPToDataFrame
        elif data is not None:
            return DataFormatFactory.auto_detect_format(data)
        else:
            raise ValueError("Unsupported format or data for Autodetection")

    @staticmethod
    def auto_detect_format(data):
        """
        Include some logic here that checks whether data is in a
        particular format.

        E.g., Easiest to begin is to validate if it's in the standard
        format
        """
        pass


class DataFormatRules(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def load_data(self):
        """
        Implement or define a method that subclasses should override
        """
        pass

    pass


class StandardToDataFrame(DataFormatRules):
    """
    This class will format a DataFrame using the standard data format
    described in the cosmosbase documentation

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation steps
    """

    pass


class HydroInnovaToDataFrame(DataFormatRules):
    """
    This Class will convert the standard HydroInnova data outputs for
    use in cosmosbase

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation methods
    """

    pass


class FTPToDataFrame(DataFormatRules):
    """_summary_

    Parameters
    ----------
    DataIngestRules : _type_
        _description_
    """

    pass


class FinappToDataFrame(DataFormatRules):
    """
    This Class will convert the standard FinApp data outputs for
    use in cosmosbase

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation methods
    """

    pass


class StyxNToDataFrame(DataFormatRules):
    """
    This Class will convert the standard StyxNeutronica data outputs for
    use in cosmosbase

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation methods
    """

    pass
