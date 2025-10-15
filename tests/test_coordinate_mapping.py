"""Tests for coordinate mapping r <-> l in Morris-Thorne."""

import numpy as np
from src.metrics.morris_thorne import create_morris_thorne_wormhole
from src.metrics.coordinate_mapping import l_of_r, r_of_l


def test_l_of_r_monotonic():
    wh = create_morris_thorne_wormhole(l0=1.0, shape="power_law", shape_params={"n": 0.5})
    b = lambda r: wh.b(r)
    r0 = wh.params.l0
    r_vals = np.linspace(r0, 5.0, 200)
    l_vals = l_of_r(r_vals, b, r0)
    assert np.all(np.diff(l_vals) >= -1e-9)
    assert l_vals[0] == 0.0
    assert l_vals[-1] > 0.0


def test_r_of_l_inversion():
    wh = create_morris_thorne_wormhole(l0=1.0, shape="power_law", shape_params={"n": 0.5})
    b = lambda r: wh.b(r)
    r0 = wh.params.l0
    r_vals = np.linspace(r0, 3.0, 150)
    l_vals = l_of_r(r_vals, b, r0)
    r_back = r_of_l(l_vals, b, r0, r_max=3.0)
    # Inversion accuracy
    rel_err = np.max(np.abs(r_back - r_vals) / np.maximum(1.0, r_vals))
    assert rel_err < 1e-3
