import numpy as np


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

    @staticmethod
    def calc_absolute_humidity(vapour_pressure, temperature):
        """
        calculates out absolute humidity using temperature (C) and
        vapour pressure unit (Pascals)

        Parameters
        ----------
        vapour_pressure : float
            Vapour Presure (Pascals)
        temperature : float
            air temperature (C)

        Returns
        -------
        float
            absolute humidity (ouput as kg/m^3)
        """
        return vapour_pressure / (461.5 * (temperature + 273.15))

    @staticmethod
    def calc_vapour_pressure_from_dewpoint_temp(dewpoint_temp):
        """
        Calculates vapour pressure from dewpoint temperature. Useful if
        using ERA5-Land data (which gives dewpoint temperature values)
        to correct for humidity such as when sensors are missing.

        Parameters
        ----------
        dewpoint_temp : float
            Dewpoint temperature (Celcius)

        Returns
        -------
        vapour_pressure: float
            Vapour pressure (kPA)
        """
        vapour_pressure = np.exp(
            (0.0707 * dewpoint_temp - 0.49299) / (1 + 0.00421 * dewpoint_temp)
        )
        return vapour_pressure


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
