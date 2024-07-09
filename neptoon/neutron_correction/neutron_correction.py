import pandas as pd
from neptoon.logging import get_logger
from neptoon.data_management.site_information import SiteInformation
from neptoon.data_management.column_names import ColumnInfo
from neptoon.neutron_correction.correction_classes import (
    Correction,
    CorrectionType,
    CorrectionTheory,
    IncomingIntensityCorrectionZreda2012,
    IncomingIntensityCorrectionHawdon2014,
    HumidityCorrectionRosolem2013,
    PressureCorrectionZreda2012,
)


core_logger = get_logger()


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
        else:
            print(f"{correction}No")  # TODO this properly...

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
        df[str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)] = df[
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT)
        ]
        for column_name in self.correction_columns:
            df[str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)] = (
                df[str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)]
                * df[column_name]
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


class CorrectionFactory:
    """
    Used inside the CRNSDataHub when selecting which corrections to
    apply. Creating a correction involves providing a CorrectionType and
    (optionally) a CorrectionTheory. The factory will then use
    information from the SiteInformation object to create a Correction
    with the appropriate information provided. Additionally a user can
    register a custom correction for use in processing.
    """

    def __init__(self, site_information: SiteInformation):
        self._site_information = site_information
        self.custom_corrections = {}

    @property
    def site_information(self):
        return self._site_information

    def create_correction(
        self,
        correction_type: CorrectionType,
        correction_theory: CorrectionTheory = None,
    ):
        """
        Creates a particular Correction object using site_information.
        CorrectionType and CorrectionTheory enums are used for
        selection. If CorrectionTheory is left empty the default
        correction is selected.

        Parameters
        ----------
        correction_type : CorrectionType
            The correction type to stage can be:
                - CorrectionType.INCOMING_INTENSITY
                - CorrectionType.ABOVE_GROUND_BIOMASS
                - CorrectionType.PRESSURE
                - CorrectionType.HUMIDITY
                - CorrectionType.CUSTOM
        correction_theory : CorrectionTheory, optional
            The theory to apply leave blank to use the default format,
            otherwise see CorrectionTheory for options, by default None

        Returns
        -------
        Correction
            Returns a correction object with the site specific values
            read in from the SiteInformation class
        """
        if (correction_type, correction_theory) in self.custom_corrections:
            return self.custom_corrections[
                (correction_type, correction_theory)
            ](
                site_information=self.site_information,
                correction_type=correction_type,
            )
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
        """
        Internal method for selecting the incoming neutron intensity
        correction to use. If no CorrectionTheory supplied it will use
        the default.

        Parameters
        ----------
        correction_theory : CorrectionTheory
            The CorrectionTheory to use

        Returns
        -------
        Correction
            Intensity correction with values filled in.
        """
        if correction_theory is None:
            return IncomingIntensityCorrectionHawdon2014(
                incoming_neutron_intensity=(
                    self.site_information.reference_incoming_neutron_value
                ),
                cutoff_rigidity=self.site_information.cutoff_rigidity,
            )
        elif correction_theory == CorrectionTheory.ZREDA_2012:
            return IncomingIntensityCorrectionZreda2012(
                reference_incoming_neutron_value=(
                    self.site_information.reference_incoming_neutron_value
                )
            )
        elif correction_theory == CorrectionTheory.HAWDON_2014:
            return IncomingIntensityCorrectionHawdon2014(
                incoming_neutron_intensity=(
                    self.site_information.reference_incoming_neutron_value
                ),
                cutoff_rigidity=self.site_information.cutoff_rigidity,
            )

    def create_biomass_correction(self, correction_theory: CorrectionTheory):
        pass

    def create_pressure_correction(self, correction_theory: CorrectionTheory):
        """
        Internal method for selecting the correct pressure correction to
        use

        Parameters
        ----------
        correction_theory : CorrectionTheory
            The CorrectionTheory to apply

        Returns
        -------
        Correction
            Returns a pressure Correction with values inserted.
        """
        correction_theory = (
            correction_theory  # TODO remove this or leave it for consistency?
        )
        return PressureCorrectionZreda2012(
            site_elevation=self.site_information.elevation,
            reference_pressure_value=self.site_information.mean_pressure,
            latitude=self.site_information.latitude,
            cutoff_rigidity=self.site_information.cutoff_rigidity,
        )

    def create_humidity_correction(self, correction_theory: CorrectionTheory):
        """
        Internal method for selecting the correct humidity correction to
        use

        Parameters
        ----------
        correction_theory : CorrectionTheory
            The CorrectionTheory to apply

        Returns
        -------
        Correction
            Returns the Correction
        """
        if correction_theory is None:
            return HumidityCorrectionRosolem2013()
        elif correction_theory == CorrectionTheory.ROSOLEM_2013:
            return HumidityCorrectionRosolem2013()

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
