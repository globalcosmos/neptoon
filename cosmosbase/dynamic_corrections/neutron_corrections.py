"""
These should be hanging functions so they can be reused


"""

import numpy as np


def press_corr(press, B, p0):
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


def clay_to_lw(clay, method="Greasen_etal_1985"):
    if method == "Franz_etal_2012":
        from grains.Greasen1985x import clay_to_lw

        lw = clay_to_lw(clay)
    else:
        print("! Unknown method to convert Clay to lattice water.")
        lw = np.nan
    return lw
