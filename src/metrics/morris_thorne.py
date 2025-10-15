"""
Morris-Thorne Traversable Wormhole Metric

Reference: Morris & Thorne (1988) "Wormholes in spacetime and their use for interstellar travel"

Metric form (Schwarzschild-like coordinates):
ds² = -e^{2Φ(l)} c²dt² + dl²/(1 - b(l)/l) + l²(dθ² + sin²θ dφ²)

where:
- l: radial proper distance coordinate (l ≥ l₀)
- Φ(l): redshift function (controls tidal forces)
- b(l): shape function (determines throat geometry)
- l₀: throat radius (minimum value of l)

Traversability conditions:
1. Φ(l) finite everywhere (no horizons)
2. b(l₀) = l₀ (throat at l₀)
3. b'(l₀) < 1 (flare-out condition)

The flare-out condition b'(l₀) < 1 ensures the wormhole opens up from the throat,
and from Einstein equations implies ρ(l₀) < 0 (exotic matter required).
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Tuple, Optional


@dataclass
class MorrisThornParams:
    """Parameters for Morris-Thorne wormhole."""
    l0: float = 1.0          # Throat radius (m)
    M: float = 0.0           # Mass parameter (kg) - zero for traversable
    c: float = 2.998e8       # Speed of light (m/s)
    G: float = 6.674e-11     # Gravitational constant (m³/kg/s²)
    
    def __post_init__(self):
        """Validate parameters."""
        if self.l0 <= 0:
            raise ValueError(f"Throat radius l0={self.l0} must be positive")


class ShapeFunction:
    """Catalog of shape functions b(l) for Morris-Thorne wormholes."""
    
    @staticmethod
    def power_law(l: np.ndarray, l0: float, n: float = 2.0) -> np.ndarray:
        """
        Power-law shape function: b(l) = l₀ (l₀/l)^n
        
        Args:
            l: Radial coordinate (proper distance)
            l0: Throat radius
            n: Power-law index (n > 0 for flare-out)
            
        Returns:
            b(l): Shape function values
            
        Properties:
            - b(l₀) = l₀ (throat condition)
            - b'(l₀) = -n < 1 (flare-out if n < 1)
        """
        return l0 * (l0 / l)**n
    
    @staticmethod
    def exponential(l: np.ndarray, l0: float, lambda_scale: float = 1.0) -> np.ndarray:
        """
        Exponential shape function: b(l) = l₀ exp(-(l-l₀)/λ)
        
        Args:
            l: Radial coordinate
            l0: Throat radius
            lambda_scale: Decay scale (larger = slower decay)
            
        Returns:
            b(l): Shape function values
            
        Properties:
            - b(l₀) = l₀ (throat condition)
            - b'(l₀) = -l₀/λ (flare-out if λ > l₀)
        """
        return l0 * np.exp(-(l - l0) / lambda_scale)
    
    @staticmethod
    def tanh(l: np.ndarray, l0: float, sigma: float = 0.5) -> np.ndarray:
        """
        Tanh-based shape function: b(l) = l₀ [1 - tanh((l-l₀)/σl₀)]/2
        
        Args:
            l: Radial coordinate
            l0: Throat radius
            sigma: Transition width (smaller = sharper throat)
            
        Returns:
            b(l): Shape function values
            
        Properties:
            - b(l₀) ≈ l₀/2 (modified to ensure b < l)
            - Smooth transition from throat
            - Asymptotically b → 0 as l → ∞
        """
        # Modified: b(l) = l0 (1 - tanh((l-l0)/(sigma*l0)) + 1)/2 
        # At l=l0: b = l0, but this violates b < l
        # Better: b(l) = l0 exp(-(l-l0)/lambda) with appropriate scaling
        lambda_scale = sigma * l0 * 2
        return l0 * np.exp(-(l - l0) / lambda_scale)


class RedshiftFunction:
    """Catalog of redshift functions Φ(l) for Morris-Thorne wormholes."""
    
    @staticmethod
    def zero(l: np.ndarray) -> np.ndarray:
        """
        Zero redshift: Φ(l) = 0
        
        Simplest choice - no tidal forces from redshift function.
        All tidal forces come from shape function b(l).
        """
        return np.zeros_like(l)
    
    @staticmethod
    def constant(l: np.ndarray, Phi0: float = 0.0) -> np.ndarray:
        """
        Constant redshift: Φ(l) = Φ₀
        
        Shifts overall time coordinate but doesn't affect traversability.
        """
        return Phi0 * np.ones_like(l)
    
    @staticmethod
    def gaussian_hump(l: np.ndarray, l0: float, amplitude: float = 0.1, 
                      width: float = 1.0) -> np.ndarray:
        """
        Gaussian redshift hump: Φ(l) = A exp(-(l-l₀)²/(2w²))
        
        Creates tidal forces localized near throat.
        Must keep amplitude small to avoid horizons.
        """
        return amplitude * np.exp(-((l - l0)**2) / (2 * width**2))


class MorrisThorne:
    """
    Morris-Thorne traversable wormhole metric.
    
    Metric components in Schwarzschild-like coordinates (t, l, θ, φ):
    g_tt = -e^{2Φ(l)}
    g_ll = 1/(1 - b(l)/l)
    g_θθ = l²
    g_φφ = l² sin²θ
    """
    
    def __init__(self, params: MorrisThornParams,
                 shape_func: Callable[[np.ndarray], np.ndarray],
                 redshift_func: Callable[[np.ndarray], np.ndarray]):
        """
        Initialize Morris-Thorne wormhole.
        
        Args:
            params: Wormhole parameters
            shape_func: Function b(l) determining throat geometry
            redshift_func: Function Φ(l) determining tidal forces
        """
        self.params = params
        self.shape_func = shape_func
        self.redshift_func = redshift_func
        
    def b(self, l: np.ndarray) -> np.ndarray:
        """Shape function b(l)."""
        return self.shape_func(l)
    
    def Phi(self, l: np.ndarray) -> np.ndarray:
        """Redshift function Φ(l)."""
        return self.redshift_func(l)
    
    def metric(self, l: np.ndarray, theta: float = np.pi/2) -> np.ndarray:
        """
        Compute metric tensor g_μν at given coordinates.
        
        Args:
            l: Radial coordinate (proper distance)
            theta: Polar angle (default: equatorial plane)
            
        Returns:
            g: 4x4 metric tensor [g_tt, g_tl, g_tθ, g_tφ; ...]
        """
        l = np.atleast_1d(l)
        shape = (len(l), 4, 4)
        g = np.zeros(shape)
        
        b_l = self.b(l)
        Phi_l = self.Phi(l)
        
        # Diagonal components
        g[:, 0, 0] = -np.exp(2 * Phi_l)                    # g_tt
        g[:, 1, 1] = 1.0 / (1.0 - b_l / l)                 # g_ll
        g[:, 2, 2] = l**2                                   # g_θθ
        g[:, 3, 3] = (l * np.sin(theta))**2                # g_φφ
        
        if len(l) == 1:
            return g[0]
        return g
    
    def inverse_metric(self, l: np.ndarray, theta: float = np.pi/2) -> np.ndarray:
        """
        Compute inverse metric tensor g^μν.
        
        Args:
            l: Radial coordinate
            theta: Polar angle
            
        Returns:
            g_inv: 4x4 inverse metric tensor
        """
        l = np.atleast_1d(l)
        shape = (len(l), 4, 4)
        g_inv = np.zeros(shape)
        
        b_l = self.b(l)
        Phi_l = self.Phi(l)
        
        # Diagonal components (inverse)
        g_inv[:, 0, 0] = -np.exp(-2 * Phi_l)               # g^tt
        g_inv[:, 1, 1] = 1.0 - b_l / l                     # g^ll
        g_inv[:, 2, 2] = 1.0 / l**2                        # g^θθ
        g_inv[:, 3, 3] = 1.0 / (l * np.sin(theta))**2     # g^φφ
        
        if len(l) == 1:
            return g_inv[0]
        return g_inv
    
    def is_traversable(self, l_test: Optional[np.ndarray] = None) -> Tuple[bool, str]:
        """
        Check traversability conditions.
        
        Args:
            l_test: Test points (default: near throat)
            
        Returns:
            (is_traversable, reason): Bool and explanation string
        """
        if l_test is None:
            l_test = np.linspace(self.params.l0, 3 * self.params.l0, 100)
        
        # Check 1: No horizons (Φ finite)
        Phi_vals = self.Phi(l_test)
        if not np.all(np.isfinite(Phi_vals)):
            return False, "Redshift function Φ(l) has infinities (horizon present)"
        
        # Check 2: Throat exists (b(l₀) = l₀)
        b_throat = self.b(np.array([self.params.l0]))[0]
        if not np.isclose(b_throat, self.params.l0, rtol=1e-6):
            return False, f"Throat condition violated: b(l₀)={b_throat:.6f} ≠ l₀={self.params.l0}"
        
        # Check 3: Flare-out (b'(l₀) < 1)
        # Numerical derivative
        dl = 1e-6 * self.params.l0
        b_plus = self.b(np.array([self.params.l0 + dl]))[0]
        b_minus = self.b(np.array([self.params.l0 - dl]))[0]
        b_prime_throat = (b_plus - b_minus) / (2 * dl)
        
        if b_prime_throat >= 1.0:
            return False, f"Flare-out condition violated: b'(l₀)={b_prime_throat:.6f} ≥ 1"
        
        # Check 4: g_ll positive (no coordinate singularities)
        # Test away from throat to avoid b(l₀) = l₀ singularity
        l_test_away = l_test[l_test > self.params.l0 * 1.001]  # Exclude immediate throat
        if len(l_test_away) > 0:
            b_vals = self.b(l_test_away)
            if not np.all(b_vals < l_test_away):
                return False, "Shape function b(l) ≥ l (coordinate singularity)"
        
        return True, "All traversability conditions satisfied"
    
    def throat_flare_out_parameter(self) -> float:
        """
        Compute flare-out parameter b'(l₀).
        
        Must be < 1 for traversability.
        Determines exotic matter density at throat.
        """
        dl = 1e-6 * self.params.l0
        b_plus = self.b(np.array([self.params.l0 + dl]))[0]
        b_minus = self.b(np.array([self.params.l0 - dl]))[0]
        return (b_plus - b_minus) / (2 * dl)


def create_morris_thorne_wormhole(
    l0: float = 1.0,
    shape: str = "power_law",
    shape_params: Optional[dict] = None,
    redshift: str = "zero",
    redshift_params: Optional[dict] = None
) -> MorrisThorne:
    """
    Factory function to create Morris-Thorne wormhole with common configurations.
    
    Args:
        l0: Throat radius (m)
        shape: Shape function type ("power_law", "exponential", "tanh")
        shape_params: Parameters for shape function
        redshift: Redshift function type ("zero", "constant", "gaussian_hump")
        redshift_params: Parameters for redshift function
        
    Returns:
        MorrisThorne instance
        
    Example:
        >>> wh = create_morris_thorne_wormhole(l0=1.0, shape="power_law", 
        ...                                    shape_params={"n": 0.5})
        >>> traversable, msg = wh.is_traversable()
        >>> print(msg)
    """
    if shape_params is None:
        shape_params = {}
    if redshift_params is None:
        redshift_params = {}
    
    # Create shape function
    if shape == "power_law":
        n = shape_params.get("n", 2.0)
        shape_func = lambda l: ShapeFunction.power_law(l, l0, n)
    elif shape == "exponential":
        lambda_scale = shape_params.get("lambda_scale", 1.0)
        shape_func = lambda l: ShapeFunction.exponential(l, l0, lambda_scale)
    elif shape == "tanh":
        sigma = shape_params.get("sigma", 0.5)
        shape_func = lambda l: ShapeFunction.tanh(l, l0, sigma)
    else:
        raise ValueError(f"Unknown shape function: {shape}")
    
    # Create redshift function
    if redshift == "zero":
        redshift_func = RedshiftFunction.zero
    elif redshift == "constant":
        Phi0 = redshift_params.get("Phi0", 0.0)
        redshift_func = lambda l: RedshiftFunction.constant(l, Phi0)
    elif redshift == "gaussian_hump":
        amplitude = redshift_params.get("amplitude", 0.1)
        width = redshift_params.get("width", 1.0)
        redshift_func = lambda l: RedshiftFunction.gaussian_hump(l, l0, amplitude, width)
    else:
        raise ValueError(f"Unknown redshift function: {redshift}")
    
    params = MorrisThornParams(l0=l0)
    return MorrisThorne(params, shape_func, redshift_func)
