"""
Coordinate mappings for Morris-Thorne wormholes.

We work with the areal radius r and define the proper radial coordinate l via:
    dl/dr = ± 1/sqrt(1 - b(r)/r),   l(r0) = 0
where r0 is the throat radius satisfying b(r0) = r0.

This module provides numeric helpers:
- l_of_r(r, b_func, r0)
- r_of_l(l, b_func, r0)

We assume r >= r0 on each side; crossing the throat is modeled by l in (-L, +L)
with r(l) = r(|l|), symmetric about the throat.
"""

from typing import Callable, Tuple
import numpy as np


def _integrand_dl_dr(r: np.ndarray, b_func: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    """dl/dr integrand for mapping to proper radial coordinate.

    dl/dr = 1 / sqrt(1 - b(r)/r)
    """
    r = np.asarray(r)
    eps = 1e-12
    denom = np.clip(1.0 - b_func(r) / np.clip(r, eps, None), eps, None)
    return 1.0 / np.sqrt(denom)


def l_of_r(r_vals: np.ndarray, b_func: Callable[[np.ndarray], np.ndarray], r0: float,
           n_steps: int = 2000) -> np.ndarray:
    """
    Compute proper radial coordinate l(r) with l(r0) = 0 via numeric integration.

    Args:
        r_vals: Array of r >= r0
        b_func: Shape function b(r)
        r0: Throat radius where b(r0)=r0
        n_steps: Integration resolution for each r value

    Returns:
        l_vals: Proper radial coordinate values with l(r0)=0; monotonically increasing.
    """
    r_vals = np.atleast_1d(r_vals)
    l_vals = np.zeros_like(r_vals, dtype=float)

    for i, r in enumerate(r_vals):
        if r <= r0:
            l_vals[i] = 0.0
            continue
        # integrate from r0 to r
        rs = np.linspace(r0, r, n_steps)
        integrand = _integrand_dl_dr(rs, b_func)
        l_vals[i] = np.trapz(integrand, rs)
    return l_vals


def r_of_l(l_vals: np.ndarray, b_func: Callable[[np.ndarray], np.ndarray], r0: float,
           r_max: float, n_steps: int = 4000) -> np.ndarray:
    """
    Compute r(l) by inverting the mapping numerically.

    Strategy:
      - Precompute a monotonic mapping table r ∈ [r0, r_max] -> l(r)
      - Invert by interpolation for |l|; use symmetry: r(l) = r(|l|)

    Args:
        l_vals: Array of proper radial coordinates (can be negative)
        b_func: Shape function b(r)
        r0: Throat radius
        r_max: Maximum areal radius to cover
        n_steps: Resolution of the table

    Returns:
        r_vals: Areal radius corresponding to each l
    """
    l_vals = np.atleast_1d(l_vals)
    # Build table
    r_grid = np.linspace(r0, r_max, n_steps)
    l_grid = l_of_r(r_grid, b_func, r0, n_steps//2)
    # Ensure strict monotonicity for interpolation
    # Add a tiny epsilon if needed
    for j in range(1, len(l_grid)):
        if l_grid[j] <= l_grid[j-1]:
            l_grid[j] = l_grid[j-1] + 1e-12

    # Interpolate r as function of l for positive l
    from numpy import interp
    abs_l = np.abs(l_vals)
    abs_l = np.clip(abs_l, l_grid[0], l_grid[-1])
    r_pos = interp(abs_l, l_grid, r_grid)
    return r_pos


def build_r_of_l_mapper(b_func: Callable[[np.ndarray], np.ndarray], r0: float, r_max: float,
                        n_steps: int = 4000) -> Callable[[np.ndarray], np.ndarray]:
    """
    Return a callable r(l) mapper for reuse.
    """
    r_grid = np.linspace(r0, r_max, n_steps)
    l_grid = l_of_r(r_grid, b_func, r0, n_steps//2)
    for j in range(1, len(l_grid)):
        if l_grid[j] <= l_grid[j-1]:
            l_grid[j] = l_grid[j-1] + 1e-12
    from numpy import interp
    def r_of_l_func(l_vals: np.ndarray) -> np.ndarray:
        abs_l = np.abs(np.atleast_1d(l_vals))
        abs_l = np.clip(abs_l, l_grid[0], l_grid[-1])
        return interp(abs_l, l_grid, r_grid)
    return r_of_l_func
