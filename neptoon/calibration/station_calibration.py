from abc import ABC, abstractmethod


class StationCalibration(ABC):
    """
    Base class for calibration of sensors
    """

    def __init__(
        self, crns_data_hub=None, corrected_crns_data=None, sample_data=None
    ):
        self._crns_data_hub = crns_data_hub
        self.corrected_crns_data = corrected_crns_data
        self.sample_data = sample_data

    @abstractmethod
    def calibrate_with_data_hub(self):
        """
        Calibration when data is supplied via CRNSDataHub
        """
        pass

    @abstractmethod
    def manual_calibration(self):
        """
        Manual calibration steps, user provided data.

        if crns_data_hub = None and (**other data availabe**):
            do_magic()
        """
        pass

    def find_n0(self):
        """
        Universal function that uses sample average to find n0
        """
        pass


class Shroen2017Calibration(StationCalibration):
    pass


class Desilet2010Calibration(StationCalibration):
    pass


class Kohli2015Calibration(StationCalibration):
    pass
