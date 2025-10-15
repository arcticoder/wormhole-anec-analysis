"""Tests for thin-shell wormholes."""

import pytest
import numpy as np
from src.metrics.thin_shell import create_thin_shell_wormhole, ThinShellParams


def test_thin_shell_params():
    """Test ThinShellParams validation."""
    # Valid parameters
    params = ThinShellParams(a=2.0, M=0.4)
    assert params.a == 2.0
    assert params.M == 0.4
    
    # Invalid: a <= 2GM/c² (inside horizon)
    # For M=1.0 kg: r_s = 2GM/c² ≈ 1.5e-27 m (tiny!)
    # So a=1.0 m is actually fine. Use larger M instead.
    with pytest.raises(ValueError):
        ThinShellParams(a=1.0, M=1e27)  # Huge mass → r_s > a


def test_thin_shell_creation():
    """Test thin-shell wormhole creation."""
    wh = create_thin_shell_wormhole(a=2.0, M=0.4)
    assert wh.a == 2.0
    assert wh.M == 0.4
    
    r_s = wh.schwarzschild_radius()
    assert r_s < wh.a  # Shell outside horizon


def test_metric_coefficients():
    """Test Schwarzschild metric coefficients."""
    wh = create_thin_shell_wormhole(a=3.0, M=0.5)
    
    r = np.array([4.0, 5.0, 10.0])
    g_tt = wh.metric_coefficient_gtt(r)
    g_rr = wh.metric_coefficient_grr(r)
    
    # Check signature
    assert np.all(g_tt < 0)  # Timelike
    assert np.all(g_rr > 0)  # Spacelike
    
    # Check Schwarzschild form
    assert np.allclose(g_tt * g_rr, -1.0)


def test_surface_stress_energy():
    """Test surface stress-energy calculation."""
    wh = create_thin_shell_wormhole(a=2.0, M=0.4)
    
    sigma = wh.surface_energy_density()
    tau = wh.surface_tension()
    
    # Should be finite
    assert np.isfinite(sigma)
    assert np.isfinite(tau)
    
    # Typically negative for wormhole
    # (exotic matter required)
    exotic = wh.is_exotic()
    assert exotic  # Expect exotic matter


def test_anec_on_shell():
    """Test ANEC calculation on shell."""
    wh = create_thin_shell_wormhole(a=2.0, M=0.4)
    
    anec_res = wh.anec_on_shell()
    
    assert "anec_shell" in anec_res
    assert "anec_violated" in anec_res
    assert "sigma" in anec_res
    assert "tau" in anec_res
    
    # Check consistency
    assert np.isfinite(anec_res["anec_shell"])


def test_summary():
    """Test complete summary generation."""
    wh = create_thin_shell_wormhole(a=3.0, M=0.5)
    
    summary = wh.summary()
    
    assert "shell_radius_m" in summary
    assert "anec_violated" in summary
    assert "exotic_matter_required" in summary
    assert "traversable" in summary
    
    # Shell should be traversable (a > r_s)
    assert summary["traversable"]
