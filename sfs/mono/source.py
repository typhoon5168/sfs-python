"""Compute the sound field generated by a sound source"""

import numpy as np
from scipy import special
from .. import util


def point(omega, x0, x, y, z=0, c=None):
    """Point source"""
    #              1  e^(-j k |x-x0|)
    # G(x-xs,w) = --- ---------------
    #             4pi      |x-x0|
    k = util.wavenumber(omega, c)
    xx, yy, zz = np.meshgrid(x - x0[0], y - x0[1], z - x0[2], sparse=True)
    r = np.sqrt((xx) ** 2 + (yy) ** 2 + (zz) ** 2)
    return np.squeeze(np.exp(-1j * k * r) / r)


def line(omega, x0, x, y, z=0, c=None):
    """Line source parallel to the z-axis"""
    #                 (2)
    # G(x-xs,w) =  j H0  ( k |x-x0| )
    k = util.wavenumber(omega, c)
    xx, yy, zz = np.meshgrid(x - x0[0], y - x0[1], z, sparse=True)
    r = np.sqrt((xx) ** 2 + (yy) ** 2)
    return np.squeeze(special.hankel2(0, k * r))


def plane(omega, n0, x, y, z=0, c=None):
    """Plane wave"""
    # G(x,w) = e^(-i w/c n x)
    k = util.wavenumber(omega, c)
    xx, yy, zz = np.meshgrid(x, y, z, sparse=True)
    n0 = np.asarray(n0)
    return np.squeeze(
        np.exp(-1j * k * np.inner(np.array([xx, yy, zz], dtype=object), n0)))
