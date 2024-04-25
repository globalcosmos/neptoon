import numpy as np


class PressureCorrections:
    """
    This class stores correction methods associated with pressure
    corrections as static methods.
    """

    @staticmethod
    def zreda_2012_l(
        current_pressure: float, reference_pressure: float, l_coeff: float
    ):
        """
        Pressure correction factor which accounts for the influence
        changes in atmopsheric pressure has on neutron counting rates.

        Parameters
        ----------
        current_pressure : float
            pressure at the specific site
        reference_pressure : float
            reference pressure - recommended to use long term average to
            keep correction factors around 1
        l_coeff : float
            mass attenuation length for high-energy neutrons in g/cm^-2.
            varies progressively between 128 g/cm^-2 (high latitude) and
            142 g/cm^-2 (equator).

        Returns
        -------
        c_factor
            correction factor to account for change in pressure, raw
            count rate is mutiplied by this number e.g., 1.04
        """
        c_factor = np.exp((current_pressure - reference_pressure) / l_coeff)
        return c_factor

    @staticmethod
    def zreda_2012_beta(
        current_pressure: float, reference_pressure: float, beta_coeff: float
    ):
        """_summary_

        Parameters
        ----------
        current_pressure : float
            pressure at the specific site
        reference_pressure : float
            reference pressure - recommended to use long term average to
            keep correction factors around 1
        beta_coeff : float
            _description_

        Returns
        -------
        _type_
            _description_
        """
        c_factor = np.exp(beta_coeff * (current_pressure - reference_pressure))
        return c_factor

    @staticmethod
    def dunai_2020(
        current_pressure: float,
        reference_pressure: float,
        beta_coeff: float,
        inclination: float,
    ):
        """
        !!!Speak with Martin about this method from corny!!!
        """
        pass


class AtmosphericHumidityCorrections:

    @staticmethod
    def rosolem_2014(absolute_humidity, reference_absolute_humidity):
        """
        This gives the factorial to multiply Neutron counts by

        Parameters
        ----------
        absolute_humidity : float
            absolute humidity in g/cm^3
        reference_absolute_humidity : float
            reference absolute humidity

        Returns
        -------
        float
            factor to multiply neutrons by
        """
        return 1 + 0.0054 * (absolute_humidity - reference_absolute_humidity)


class IncomingIntensityCorrections:

    @staticmethod
    def zreda_2012(incoming_intensity, incoming_ref):
        """_summary_

        Parameters
        ----------
        incoming_intensity : _type_
            _description_
        incoming_ref : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """
        c_factor = incoming_ref / incoming_intensity
        return c_factor


# class CorrectionMethod:

#     required_modules = []

#     @classmethod
#     def _prepare_imports_(cls):
#         for requirement in cls.required_modules:
#             if requirement not in globals():
#                 print("Loading Module", requirement)
#                 globals()[requirement] = import_module(
#                     requirement
#                 )  # See note (1)

#     @classmethod
#     def _do_correction_(
#         **kwargs,
#     ):  # May want to add the abc.abstractmethod decorator
#         """Run the actual correction.

#         Inheriting classes should override this.
#         They may specify the actually accepted arguments and should return the corrected values.
#         """
#         pass  # Override this

#     @classmethod
#     def do_correction(cls, **kwargs):
#         """Sets up and runs the correction.

#         Users of the correction method call this.
#         It will deal with all required setup, import, validation,… internally
#         and then call the actual correction method.
#         """
#         cls._prepare_imports_()
#         return cls._do_correction_(**kwargs)


# # === User-defined corrections ===
# # from cosmos_methods import CorrectionMethod


# class FredoMethod(CorrectionMethod):

#     magic_number = 2

#     @classmethod
#     def _do_correction_(cls, initial_value):
#         return initial_value * cls.magic_number


# class MartinMethod(CorrectionMethod):

#     magic_number = 3

#     required_modules = ["math"]

#     @classmethod
#     def _do_correction_(cls, initial_value, temperature):
#         return math.sin(initial_value) + cls.magic_number * temperature


# # === Use case ===

# fredo_correction = FredoMethod.do_correction(initial_value=8)
# martin_correction = MartinMethod.do_correction(initial_value=8, temperature=12)

# print("Fredo:", fredo_correction)
# print("Martin:", martin_correction)
