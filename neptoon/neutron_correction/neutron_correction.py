import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from neptoon.logging import get_logger
from neptoon.data_management.site_information import SiteInformation

# read in the specific functions here
from neptoon.corrections_and_functions.incoming_intensity_corrections import (
    incoming_intensity_zreda_2012,
)

core_logger = get_logger()


class Correction(ABC):
    """
    Abstract class for the Correction classes. Ensures that all
    corrections have an apply method which takes a DataFrame as an
    argument. The return of the apply function should be a DataFrame
    with the correction factor calculated and added as a column. The
    correction_factor_column_name should be set which is the name of the
    column the correction factor will be recorded into.

    The CorrectionBuilder class will then store the name of columns
    where correction factors are stored. This enables the creation of
    the overall corrected neutron count column.
    """

    def __init__(
        self, correction_type: str, correction_factor_column_name: str
    ):
        self._correction_factor_column_name = correction_factor_column_name
        self.correction_type = correction_type

    @abstractmethod
    def apply(self, data_frame: pd.DataFrame):
        """
        The apply button should always take a dataframe as an input, do
        some logic, and return a dataframe with the additional columns
        calucalted during processing.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The crns_data_frame
        """
        pass

    @property
    def correction_factor_column_name(self) -> str:
        if self._correction_factor_column_name is None:
            raise ValueError("correction_factor_column_name has not been set.")
        return self._correction_factor_column_name

    @correction_factor_column_name.setter
    def correction_factor_column_name(self, value: str):
        self._correction_factor_column_name = value

    def get_correction_factor_column_name(self):
        """
        Declare the name of the correction factor column
        """
        return self.correction_factor_column_name


class IncomingIntensityZreda(Correction):
    """
    Corrects neutrons for incoming neutron intensity according to the
    original Zreda et al. (2012) equation.

    https://doi.org/10.5194/hess-16-4079-2012
    """

    def __init__(
        self,
        reference_incoming_neutron_value: float,
        correction_type: str = "intensity",
        correction_factor_column_name: str = "correction_for_intensity",
        incoming_neutron_column_name: str = "incoming_neutron_intensity",
    ):
        """
        Required attributes for creation.

        Parameters
        ----------
        reference_incoming_neutron_value : float
            reference count of incoming neutron intensity at a point in
            time.
        correction_type : str, optional
            correction type, by default "intensity"
        correction_factor_column_name : str, optional
            name of column corrections will be written to, by default
            "correction_for_intensity"
        incoming_neutron_column_name : str, optional
            name of column where incoming neutron intensity values are
            stored in the dataframe, by default
            "incoming_neutron_intensity"
        """
        self.incoming_neutron_column_name = incoming_neutron_column_name
        self.reference_incoming_neutron_value = (
            reference_incoming_neutron_value
        )
        self.correction_factor_column_name = correction_factor_column_name
        self.correction_type = correction_type

    def apply(self, data_frame):
        """
        Applies the neutron correction

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with appropriate data

        Returns
        -------
        pd.DataFrame
            DataFrame now corrected
        """
        # TODO validation here??
        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_zreda_2012(
                row[self.incoming_neutron_column_name],
                self.reference_incoming_neutron_value,
            ),
            axis=1,
        )

        return data_frame


class CorrectionBuilder:
    """
    Staging place for the corrections as they are built. First a user
    adds a check using the add_check method.

    Parameters
    ----------

    corrections : dict
        dictionary which contains the corrections. The key is the
        correction_type assigned in each correction, the value is the
        correction itself.

    """

    def __init__(self):
        self.corrections = {}

    def add_correction(self, correction: Correction):
        """
        Adds a correction to the CorrectionBuilder

        Parameters
        ----------
        correction : Correction
            A Correction object
        """
        if isinstance(correction, Correction):
            correction_type = correction.correction_type
            self.corrections[correction_type] = correction

    def remove_correction_by_type(self, correction_type: str):
        """
        Removes a correction from the CorrectionBuilder based on its
        type

        Parameters
        ----------
        correction_type : str
            The type of correction to be removed
        """
        if correction_type in self.corrections:
            self.corrections.pop(correction_type)
        else:
            raise ValueError(
                f"Correction type '{correction_type}' not found in the builder."
            )

    def get_corrections(self):
        """
        Returns the corrections stored in the builder
        """
        return self.corrections.values()


class CorrectNeutrons:
    """
    CorrectNeutrons class handles correcting neutrons for additional
    influences beyond soil moisture. It takes in a crns_data_frame which
    is a pd.DataFrame which stores the required data.

    Methods are available for staging a series of corrections which are
    applied to remove additional influences on the neutron signal. A
    user can add corrections individually, or create a CorrectionBuilder
    class seperately that has been pre-compiled and inject that into the
    CorrectNeutrons instance.

    Once the CorrectionBuilder has been appropriately staged with
    desired corrections, the correct_neutrons method will apply each
    correction, record the correction factor and create a corrected
    epithermal neutron count column with the correction factors applied.
    """

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        correction_builder: CorrectionBuilder,
    ):
        """
        Attributes for using the CorrectNeutrons class

        Parameters
        ----------
        crns_data_frame : pd.DataFrame
            A DataFrame which contains the appropriate information to
            apply corrections.
        correction_builder : CorrectionBuilder
            Staging area for corrections. Can be built or supplied
            completed.
        """
        self._crns_data_frame = crns_data_frame
        self._correction_builder = correction_builder
        self._correction_columns = []

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df: pd.DataFrame):
        # TODO add checks that it is df
        self._crns_data_frame = df

    @property
    def correction_builder(self):
        return self._correction_builder

    @correction_builder.setter
    def correction_builder(self, builder: CorrectionBuilder):
        if isinstance(builder, CorrectionBuilder):
            self._correction_builder = builder
        else:
            message = f"It appears {builder} is not a CorrectionBuilder object"
            core_logger.error(message)
            raise AttributeError

    @property
    def correction_columns(self):
        return self._correction_columns

    def add_correction(self, new_correction: Correction):
        """
        Add an invidual correction to the CorrectionBuilder

        Parameters
        ----------
        new_correction : Correction
            The new correction to apply
        """
        self.correction_builder.add_correction(new_correction)

    def add_correction_builder(
        self, new_correction_builder: CorrectionBuilder
    ):
        """
        Add a whole correction builder. Useful if a correction builder
        has been built somewhere in the code and you want to read it in.

        Parameters
        ----------
        new_correction_builder : CorrectionBuilder
            A pre-compiled correction builder.
        """
        self.correction_builder = new_correction_builder

    def create_correction_factors(self, df: pd.DataFrame):
        """
        Cycles through all the corrections in the CorrectionBuilder and
        applies them to the DataFrame. Returns the DataFrame with additional
        columns.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame which is prepared for correction.

        Returns
        -------
        pd.DataFrame
            DataFrame with additional columns applied during correction.
        """
        for correction in self.correction_builder.get_corrections():
            df = correction.apply(df)
            correction_column_name = (
                correction.get_correction_factor_column_name()
            )
            self.correction_columns.append(correction_column_name)

        return df

    def create_corrected_neutron_column(self, df):
        """
        Calculates the corrected neutron count rate after applying all
        the corrections.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with the corrections applied and recorded in the
            columns

        Returns
        -------
        pd.DataFrame
            DataFrame with the corrected epithermal neutron count
            recorded in a column
        """
        df["corrected_epithermal_neutron_count"] = df["epithermal_neutrons"]
        for column_name in self.correction_columns:
            df["corrected_epithermal_neutron_count"] = (
                df["corrected_epithermal_neutron_count"] * df[column_name]
            )
        return df

    def correct_neutrons(self):
        """
        Corrects neutrons using the CorrectionBuilder. Returns the
        DataFrame.

        Returns
        -------
        df: pd.DataFrame
            DataFrame returned with additional columns.
        """
        df = self.create_correction_factors(self.crns_data_frame)
        df = self.create_corrected_neutron_column(df)
        return df


class CorrectionType(Enum):
    """
    The types of correction avaiable to implement.
    """

    INCOMING_INTENSITY = "incoming_intensity"
    ABOVE_GROUND_BIOMASS = "above_ground_biomass"
    PRESSURE = "pressure"
    HUMIDITY = "humidity"


class CorrectionTheory(Enum):
    """
    The corrections theories for correcting influence on neutron signal
    beyond soil moisture
    """

    ZREDA_2012 = "zreda_2012"
    ROSOLEM_2012 = "rosolem_2012"
    # TODO the rest


class CorrectionFactory:
    """ """

    def __init__(self, site_information: SiteInformation):
        self._site_information = site_information
        self.custom_corrections = []

    @property
    def site_information(self):
        return self._site_information

    def create_correction(
        self,
        correction_type: CorrectionType,
        correction_theory: CorrectionTheory = None,
    ):
        """
        Creates a particular Correction object using the
        site_information. CorrectionType and CorrectionTheory enums are
        used for selection. If CorrectionTheory is left empty the
        default correction is selected.

        Parameters
        ----------
        correction_type : CorrectionType
            The correction type to stage can be:
                - CorrectionType.INCOMING_INTENSITY
                - CorrectionType.ABOVE_GROUND_BIOMASS
                - CorrectionType.PRESSURE
                - CorrectionType.HUMIDITY
        correction_theory : CorrectionTheory, optional
            The theory to apply leave blank to use the default format,
            otherwise see CorrectionTheory for options, by default None

        Returns
        -------
        Correction
            Returns a correction object with the site specific values
            read in from the SiteInformation class
        """
        if (correction_type, correction_theory) in self.custom_correction:
            return self.custom_corrections[
                (correction_type, correction_theory)
            ](self.site_information)
        if correction_type == CorrectionType.ABOVE_GROUND_BIOMASS:
            return self.create_biomass_correction(
                correction_theory=correction_theory
            )

        if correction_type == CorrectionType.INCOMING_INTENSITY:
            return self.create_intensity_correction(
                correction_theory=correction_theory
            )
        if correction_type == CorrectionType.PRESSURE:
            return self.create_pressure_correction(
                correction_theory=correction_theory
            )
        if correction_type == CorrectionType.HUMIDITY:
            return self.create_humidity_correction(
                correction_theory=correction_theory
            )

    def create_intensity_correction(self, correction_theory: CorrectionTheory):
        if correction_theory == None:
            # Apply default correction theory
            # TODO decide and add the default correction type
            pass
        elif correction_theory == CorrectionTheory.ZREDA_2012:
            return IncomingIntensityZreda(
                self.site_information.reference_incoming_neutron_value
            )

    def create_biomass_correction(self, correction_theory: CorrectionTheory):
        pass

    def create_pressure_correction(self, correction_theory: CorrectionTheory):
        pass

    def create_humidity_correction(self, correction_theory: CorrectionTheory):
        pass

    def register_custom_correction(
        self, correction_type: CorrectionType, theory: str, correction_class
    ):
        """
        Used to register a custom correction theory. Without
        registration the correction cannot be used.

        The correction_class must be an object which inherits the
        Correction class and follows the same principles as other
        Correction type objects. This means it requires an apply method,
        which takes in a dataframe and returns a dataframe along with
        updates calulcated along the way.

        The key difference of a custom Correction class is that it must
        take a SiteInformation object. The logic under apply() will then
        use this SiteInformation object to collect relevant information
        for processing.

        Parameters
        ----------
        correction_type : CorrectionType
            The type of correction being registered
        theory : str
            A name for the custom correction
        correction_class : Correction
            A custom Correction class. See documentation on how to make
            this.

        Raises
        ------
        ValueError
            If the correction class is not a Correction type object it
            throws an error
        """
        if not issubclass(correction_class, Correction):
            message = "Custom correction must inherit from Correction class"
            core_logger.error(message)
            raise ValueError(message)
        self.custom_corrections[(correction_type, theory)] = correction_class
