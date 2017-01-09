"""Compute time based driving functions for various systems.

.. include:: math-definitions.rst

"""
from __future__ import division
import numpy as np
from numpy.core.umath_tests import inner1d  # element-wise inner product
import scipy.signal as sig
from .. import defs
from .. import util


def wfs_25d_plane(x0, n0, n=[0, 1, 0], xref=[0, 0, 0], c=None):
    r"""Plane wave model by 2.5-dimensional WFS.

    Parameters
    ----------
    x0 : (N, 3) array_like
        Sequence of secondary source positions.
    n0 : (N, 3) array_like
        Sequence of secondary source orientations.
    n : (3,) array_like, optional
        Normal vector (propagation direction) of synthesized plane wave.
    xref : (3,) array_like, optional
        Reference position
    c : float, optional
        Speed of sound

    Returns
    -------
    delays : (N,) numpy.ndarray
        Delays of secondary sources in seconds.
    weights: (N,) numpy.ndarray
        Weights of secondary sources.

    Notes
    -----
    2.5D correction factor

    .. math::

        g_0 = \sqrt{2 \pi |x_\mathrm{ref} - x_0|}

    d using a plane wave as source model

    .. math::

        d_{2.5D}(x_0,t) = h(t)
        2 g_0 \scalarprod{n}{n_0}
        \dirac{t - \frac{1}{c} \scalarprod{n}{x_0}}

    with wfs(2.5D) prefilter h(t), which is not implemented yet.

    References
    ----------
    See http://sfstoolbox.org/en/latest/#equation-d.wfs.pw.2.5D

    """
    if c is None:
        c = defs.c
    x0 = util.asarray_of_rows(x0)
    n0 = util.asarray_of_rows(n0)
    n = util.asarray_1d(n)
    xref = util.asarray_1d(xref)
    g0 = np.sqrt(2 * np.pi * np.linalg.norm(xref - x0, axis=1))
    delays = inner1d(n, x0) / c
    weights = 2 * g0 * inner1d(n, n0)
    return delays, weights


def wfs_25d_point(x0, n0, xs, xref=[0, 0, 0], c=None):
    r"""Point source by 2.5-dimensional WFS.

    Parameters
    ----------
    x0 : (N, 3) array_like
        Sequence of secondary source positions.
    n0 : (N, 3) array_like
        Sequence of secondary source orientations.
    xs : (3,) array_like
        Virtual source position.
    xref : (3,) array_like, optional
        Reference position
    c : float, optional
        Speed of sound

    Returns
    -------
    delays : (N,) numpy.ndarray
        Delays of secondary sources in seconds.
    weights: (N,) numpy.ndarray
        Weights of secondary sources.

    Notes
    -----
    2.5D correction factor

    .. math::

         g_0 = \sqrt{2 \pi |x_\mathrm{ref} - x_0|}


    d using a point source as source model

    .. math::

         d_{2.5D}(x_0,t) = h(t)
         \frac{g_0  \scalarprod{(x_0 - x_s)}{n_0}}
         {2\pi |x_0 - x_s|^{3/2}}
         \dirac{t - \frac{|x_0 - x_s|}{c}}

    with wfs(2.5D) prefilter h(t), which is not implemented yet.

    References
    ----------
    See http://sfstoolbox.org/en/latest/#equation-d.wfs.ps.2.5D

    """
    if c is None:
        c = defs.c
    x0 = util.asarray_of_rows(x0)
    n0 = util.asarray_of_rows(n0)
    xs = util.asarray_1d(xs)
    xref = util.asarray_1d(xref)
    g0 = np.sqrt(2 * np.pi * np.linalg.norm(xref - x0, axis=1))
    ds = x0 - xs
    r = np.linalg.norm(ds, axis=1)
    delays = r/c
    weights = g0 * inner1d(ds, n0) / (2 * np.pi * r**(3/2))
    return delays, weights


def driving_signals(delays, weights, signal, fs=None):
    """Get driving signals per secondary source.

    Returned signals are the delayed and weighted mono input signal
    (with N samples) per channel (C).

    Parameters
    ----------
    delays : (C,) array_like
        Delay in seconds for each channel, negative values allowed.
    weights : (C,) array_like
        Amplitude weighting factor for each channel.
    signal : (N,) array_like
        Excitation signal (mono) which gets weighted and delayed.
    fs: int, optional
        Sampling frequency in Hertz.

    Returns
    -------
    driving_signals : (N, C) numpy.ndarray
        Driving signal per channel (column represents channel).
    t_offset : float
        Simulation point in time offset (seconds).

    """
    delays = util.asarray_1d(delays)
    weights = util.asarray_1d(weights)
    d, t_offset = apply_delays(signal, delays, fs)
    return d * weights, t_offset


def apply_delays(signal, delays, fs=None):
    """Apply delays for every channel.

    A mono input signal gets delayed for each channel individually. The
    simultation point in time is shifted by the smallest delay provided,
    which allows negative delays as well.

    Parameters
    ----------
    signal : (N,) array_like
        Mono excitation signal (with N samples) which gets delayed.
    delays : (C,) array_like
        Delay in seconds for each channel (C), negative values allowed.
    fs: int, optional
        Sampling frequency in Hertz.

    Returns
    -------
    out : (N, C) numpy.ndarray
        Output signals (column represents channel).
    t_offset : float
        Simulation point in time offset (seconds).

    """
    if fs is None:
        fs = defs.fs
    signal = util.asarray_1d(signal)
    delays = util.asarray_1d(delays)

    delays_samples = np.rint(fs * delays).astype(int)
    offset_samples = delays_samples.min()
    delays_samples -= offset_samples
    out = np.zeros((delays_samples.max() + len(signal), len(delays_samples)))
    for channel, cdelay in enumerate(delays_samples):
        out[cdelay:cdelay + len(signal), channel] = signal
    return out, offset_samples / fs

    
def nfchoa_25d_plane(x0, r0, npw, max_order=None, c=None, fs=None):
    """Vritual plane wave by 2.5-dimensional NFC-HOA.

    Parameters
    ----------
    x0 : (N, 3) array_like
        Sequence of secondary source positions.
    r0 : float
        Radius of the circular secondary source distribution
    npw : (3,) array_like
        Unit vector (propagation direction) of plane wave.
    max_order : int
        Ambisonics order
    c : float, optional
        Speed of sound

    Returns
    -------
    delay : float
        Overall delay (common to all secondary source)
    weight : float
        Overall weight (common to all secondary sources)
    sos : dictionary
        Second-order section filters 
    phase : float
        Phase shift

    """    
    if max_order is None:
        max_order =_max_order_circular_harmonics(len(x0), max_order)
    if c is None:
        c = defs.c
    if fs is None:
        fs = defs.fs

    x0 = util.asarray_of_rows(x0)
    npw = util.asarray_1d(npw)
    phipw, _, _ = util.cart2sph(*npw)
    r0 = util.cart2sph(*x0[0])[2]
    M = _max_order_circular_harmonics(len(x0), max_order)
    T = 1/fs
    
    delay = 0/c
    weight = 2*r0
    sos = {}
#    sos[0] = [1., 0., 0., 1., 0., 0.]
    for m in range(0,M+1):
        _, p, k = sig.besselap(m, norm='delay')
        z0 = [np.exp(0*T) for s0 in p]
#        z0 = np.ones((m,1))
        zinf = [np.exp(c/r0*sinf*T) for sinf in p]
        sos[m] = sig.zpk2sos(z0,zinf,1,pairing='nearest')
    phase = phipw - np.pi
    return delay, weight, sos, phase

    
def nfchoa_25d_point(x0, r0, xs, max_order=None, c=None, fs=None):
    """Point source by 2.5-dimensional NFC-HOA.

    Parameters
    ----------
    x0 : (N, 3) array_like
        Sequence of secondary source positions.
    r0 : float
        Radius of the circular secondary source distribution
    xs : (3,) array_like
        Virtual source position.
    max_order : int
        Ambisonics order
    c : float, optional
        Speed of sound

    Returns
    -------
    delay : float
        Overall delay (common to all secondary source)
    weight : float
        Overall weight (common to all secondary sources)
    sos : dictionary
        Second-order section filters 
    phase : float
        Phase shift

    """    
    if max_order is None:
        max_order =_max_order_circular_harmonics(len(x0), max_order)
    if c is None:
        c = defs.c
    if fs is None:
        fs = defs.fs
    x0 = util.asarray_of_rows(x0)
    xs = util.asarray_1d(xs)
    phi, _, r = util.cart2sph(*xs)
    r0 = util.cart2sph(*x0[0])[2]
    M = _max_order_circular_harmonics(len(x0), max_order)
    T = 1/fs
    
    delay = (r-r0)/c
    weight = 1/2/np.pi/r
    sos = {}
    for m in range(0,M+1):
        _, p, k = sig.besselap(m, norm='delay')
        z0 = [np.exp(c/r*s0*T) for s0 in p]
        zinf = [np.exp(c/r0*sinf*T) for sinf in p]
        sos[m] = sig.zpk2sos(z0,zinf,1,pairing='nearest')
    phase = phi
    return delay, weight, sos, phase


def _max_order_circular_harmonics(N, max_order):
    """Compute order of 2D HOA."""
    return N // 2 if max_order is None else max_order


    
