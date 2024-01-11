import numpy as np


class NeutronCorrections:
    """Class contains the neutron corrections"""

    @staticmethod
    def pressfact_B(press, B, p0):
        """pressfact_B corrects neutrons for pressure changes

        Parameters
        ----------
        press : float
            pressure (mb)
        B : float
            beta coefficient e.g. 0.007
        p0 : int
            reference pressure (mb)

        Returns
        -------
        float
            number to multiply neutron counts by to correct
        """
        return np.exp(B * (press - p0))
