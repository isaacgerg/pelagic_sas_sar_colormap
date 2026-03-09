"""
schlick_drc.py
==============
Schlick's rational tone mapping operator for dynamic range compression.

Implements the rational tone mapping operator from:

    Schlick, C. (1998). "Quantization Techniques for Visualization of
    High Dynamic Range Pictures." In: Photorealistic Rendering Techniques.
    Springer. DOI: 10.1007/978-3-642-87825-1_2

The rational tone mapping operator maps normalised intensity L in [0, 1]
to output via:

    L_out = (b * L) / ((b - 1) * L + 1)

where b is a brightness parameter derived from the image statistics
(median or RMS) and a user-specified target brightness level.

Usage
-----
    from schlick_drc import schlick

    # magnitude is a real-valued 2D array (e.g. abs of complex SAS image)
    compressed = schlick(magnitude, brightness=0.3)

    # With a mask (e.g. to ignore zero-padded regions):
    compressed = schlick(magnitude, brightness=0.25, mask=valid_pixels)

Dependencies
------------
    numpy
"""

import numpy as np

_EPS = 1e-7


def normalize(arr, vmin=None, vmax=None):
    """Min-max normalize array to [0, 1].

    Parameters
    ----------
    arr : ndarray
        Input array.
    vmin, vmax : float, optional
        Explicit range. If None, uses arr.min() and arr.max().

    Returns
    -------
    ndarray
        Normalized copy of arr in [0, 1].
    """
    out = arr.copy()
    if vmin is None and vmax is None:
        out -= out.min()
        out /= (out.max() + _EPS)
    else:
        out -= vmin
        out /= ((vmax - vmin) + _EPS)
    return out


def schlick(L, brightness=0.3, median_flag=True, mask=None):
    """Schlick's rational tone mapping operator.

    Compresses the dynamic range of a high-dynamic-range image so that
    detail is visible across the full intensity range, using the rational
    tone mapping operator from Schlick (1998).

    Parameters
    ----------
    L : ndarray
        Input intensity image (real, non-negative). Must NOT be complex —
        pass np.abs(complex_image) before calling.
    brightness : float, optional
        Target brightness level for the median (or RMS) of the image,
        in [0, 1]. Lower values produce darker output with more headroom
        for bright targets; higher values lift the background.
        Default: 0.3.
    median_flag : bool, optional
        If True (default), compute the image midpoint as the median of
        the masked region. If False, use the RMS (root mean square).
    mask : ndarray of bool, optional
        Boolean mask of the same shape as L. Only pixels where mask is
        True are normalized and compressed; masked-out pixels are set
        to 0. If None, all pixels are processed.

    Returns
    -------
    ndarray
        Tone-mapped image in [0, 1], same shape as L.

    References
    ----------
    Schlick, C. (1998). "Quantization Techniques for Visualization of
    High Dynamic Range Pictures." In: Photorealistic Rendering Techniques,
    Springer. DOI: 10.1007/978-3-642-87825-1_2

    The rational tone mapping operator:  L_out = (b * L) / ((b - 1) * L + 1)
    where b controls the compression curve shape.
    """
    assert not np.any(np.iscomplex(L)), \
        "Input must be real-valued. Apply np.abs() to complex data first."

    L = np.squeeze(L).astype(np.float64)

    if mask is None:
        mask = np.ones_like(L, dtype=bool)

    # Normalize masked region to [0, 1]
    L[mask] = normalize(L[mask])

    # Compute midpoint statistic
    if median_flag:
        m = np.median(L[mask])
    else:
        m = np.sqrt(np.sum(L**2) / (2 * np.prod(L.shape)))

    if np.isnan(m):
        return np.zeros_like(L)

    # Derive brightness parameter b from target and midpoint
    b = (brightness - brightness * m) / (m - brightness * m + _EPS)
    b = np.clip(b, 0, 99999999)

    # Apply rational tone mapping operator
    L = (b * L) / ((b - 1) * L + 1 + _EPS)

    L[~mask] = 0

    return L
