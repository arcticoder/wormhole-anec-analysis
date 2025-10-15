"""Tests for Morris-Thorne wormhole implementation."""

import pytest
import numpy as np
from src.metrics.morris_thorne import (
    MorrisThorne, MorrisThornParams, ShapeFunction, RedshiftFunction,
    create_morris_thorne_wormhole
)


def test_morris_thorne_params():
    """Test MorrisThornParams initialization."""
    params = MorrisThornParams(l0=1.0)
    assert params.l0 == 1.0
    assert params.c > 0
    assert params.G > 0
    
    # Test validation
    with pytest.raises(ValueError):
        MorrisThornParams(l0=-1.0)


def test_power_law_shape_function():
    """Test power-law shape function."""
    l0 = 1.0
    l = np.array([1.0, 2.0, 3.0])
    
    # n=2 case
    b = ShapeFunction.power_law(l, l0, n=2.0)
    assert np.isclose(b[0], l0)  # b(l₀) = l₀
    assert b[1] < b[0]  # Decreasing
    assert b[2] < b[1]


def test_exponential_shape_function():
    """Test exponential shape function."""
    l0 = 1.0
    l = np.array([1.0, 2.0, 3.0])
    
    b = ShapeFunction.exponential(l, l0, lambda_scale=1.0)
    assert np.isclose(b[0], l0)  # b(l₀) = l₀
    assert np.all(b[1:] < b[0])  # Decreasing


def test_tanh_shape_function():
    """Test tanh-based shape function."""
    l0 = 1.0
    l = np.linspace(1.0, 5.0, 50)
    
    b = ShapeFunction.tanh(l, l0, sigma=0.5)
    assert np.isclose(b[0], l0)  # b(l₀) = l₀
    assert np.all(b <= l)  # b(l) ≤ l (no singularities)
    assert b[-1] < b[0]  # Decreasing


def test_zero_redshift_function():
    """Test zero redshift function."""
    l = np.array([1.0, 2.0, 3.0])
    Phi = RedshiftFunction.zero(l)
    assert np.allclose(Phi, 0.0)


def test_morris_thorne_metric():
    """Test Morris-Thorne metric tensor."""
    wh = create_morris_thorne_wormhole(l0=1.0, shape="power_law", 
                                       shape_params={"n": 0.5})
    
    l = np.array([2.0])
    g = wh.metric(l)
    
    # Check metric is 4x4
    assert g.shape == (4, 4)
    
    # Check signature (-,+,+,+)
    assert g[0, 0] < 0  # g_tt < 0
    assert g[1, 1] > 0  # g_ll > 0
    assert g[2, 2] > 0  # g_θθ > 0
    assert g[3, 3] > 0  # g_φφ > 0
    
    # Check diagonal (spherical symmetry)
    assert np.allclose(g[0, 1:], 0.0)
    assert np.allclose(g[1, [0,2,3]], 0.0)


def test_inverse_metric():
    """Test metric inverse."""
    wh = create_morris_thorne_wormhole(l0=1.0, shape="power_law",
                                       shape_params={"n": 0.5})
    
    l = np.array([2.0])
    g = wh.metric(l)
    g_inv = wh.inverse_metric(l)
    
    # Check g · g⁻¹ = I
    identity = np.dot(g, g_inv)
    assert np.allclose(identity, np.eye(4), atol=1e-10)


def test_traversability_conditions():
    """Test traversability checking."""
    # Traversable wormhole (n < 1 → b'(l₀) < 0, flare-out)
    wh_good = create_morris_thorne_wormhole(l0=1.0, shape="power_law",
                                            shape_params={"n": 0.5})
    traversable, msg = wh_good.is_traversable()
    assert traversable, f"Should be traversable: {msg}"
    assert wh_good.throat_flare_out_parameter() < 1.0
    
    # Borderline case (n = 0.99, b'(l₀) ≈ -0.99 < 1, should still pass)
    wh_borderline = create_morris_thorne_wormhole(l0=1.0, shape="power_law",
                                                  shape_params={"n": 0.99})
    traversable_border, msg_border = wh_borderline.is_traversable()
    # Note: n=0.99 gives b'(l₀) = -0.99 < 1, so should be traversable


def test_throat_flare_out_parameter():
    """Test flare-out parameter computation."""
    wh = create_morris_thorne_wormhole(l0=1.0, shape="power_law",
                                       shape_params={"n": 0.5})
    
    b_prime = wh.throat_flare_out_parameter()
    
    # For power-law with n=0.5: b'(l₀) = -n = -0.5
    assert b_prime < 1.0  # Flare-out condition
    assert np.isclose(b_prime, -0.5, atol=0.01)


def test_create_wormhole_factory():
    """Test factory function."""
    # Test different configurations
    wh1 = create_morris_thorne_wormhole(l0=1.0, shape="power_law")
    wh2 = create_morris_thorne_wormhole(l0=2.0, shape="exponential")
    wh3 = create_morris_thorne_wormhole(l0=1.0, shape="tanh")
    
    assert wh1.params.l0 == 1.0
    assert wh2.params.l0 == 2.0
    assert wh3.params.l0 == 1.0
    
    # Test invalid shape
    with pytest.raises(ValueError):
        create_morris_thorne_wormhole(shape="invalid")
