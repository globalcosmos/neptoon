# import pandas as pd
from abc import ABC, abstractmethod
from cosmosbase.data_management.data_wrapper import DataFrameWrapper

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


class DataIngestRules(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def load_data(self):
        """
        Implement or define a method that subclasses should override
        """
        pass

    pass


class StandardToDataFrame(DataIngestRules):
    """
    This class will format a DataFrame using the standard data format
    described in the cosmosbase documentation

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation steps
    """

    pass


class HydroInnovaToDataFrame(DataIngestRules):
    """
    This Class will convert the standard HydroInnova data outputs for
    use in cosmosbase

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation methods
    """

    pass


class FinappToDataFrame(DataIngestRules):
    """
    This Class will convert the standard FinApp data outputs for
    use in cosmosbase

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation methods
    """

    pass


class StyxNToDataFrame(DataIngestRules):
    """
    This Class will convert the standard StyxNeutronica data outputs for
    use in cosmosbase

    Parameters
    ----------
    DataToDataFrame : Class
        Base Class with validation methods
    """

    pass


class read_data:
    def __init__(self):
        pass


"""
import cosmosbase

globalconfig = cosmosbase.readglobalconfigfunction('path') #1
siteconfig = cosmosbase.readsiteconfigfunction('path) #2

crns_data = cosmosbase.read_data(globalconfig, siteconfig)

"""
