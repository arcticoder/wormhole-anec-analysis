"""Throat geometry calculations for Morris-Thorne wormholes."""

import numpy as np
from typing import Tuple
from ..metrics.morris_thorne import MorrisThorne


class ThroatGeometry:
    """
    Throat geometry analyzer for Morris-Thorne wormholes.
    
    Computes geometric properties at and near the wormhole throat:
    - Embedding diagram parameters
    - Proper circumference
    - Tidal accelerations
    - Curvature scalars
    """
    
    def __init__(self, wormhole: MorrisThorne):
        """
        Initialize throat geometry analyzer.
        
        Args:
            wormhole: MorrisThorne instance
        """
        self.wh = wormhole
        self.l0 = wormhole.params.l0
        
    def proper_circumference(self, l: np.ndarray) -> np.ndarray:
        """
        Compute proper circumference at radial coordinate l.
        
        For Morris-Thorne metric: C(l) = 2π l
        
        Args:
            l: Radial coordinate
            
        Returns:
            Circumference in meters
        """
        return 2 * np.pi * l
    
    def embedding_radius(self, l: np.ndarray) -> np.ndarray:
        """
        Compute embedding diagram radius r(l).
        
        In 3D Euclidean space, wormhole throat can be visualized as
        surface of revolution. For MT metric:
        
        r(l) = l  (proper circumference radius)
        
        Args:
            l: Radial coordinate
            
        Returns:
            Embedding radius
        """
        return l
    
    def embedding_height(self, l: np.ndarray) -> np.ndarray:
        """
        Compute embedding diagram height z(l).
        
        From embedded surface: dz/dl = ±√(b(l)/(l - b(l)))
        
        Args:
            l: Radial coordinate (l > l₀)
            
        Returns:
            Height z(l) relative to throat plane
        """
        l = np.atleast_1d(l)
        b_l = self.wh.b(l)
        
        # Integrand: sqrt(b/(l-b))
        integrand = np.sqrt(b_l / (l - b_l + 1e-12))  # Small epsilon for stability
        
        # Numerical integration from throat
        z = np.zeros_like(l)
        for i in range(1, len(l)):
            dl = l[i] - l[i-1]
            z[i] = z[i-1] + integrand[i] * dl
            
        return z
    
    def flare_out_parameter(self) -> float:
        """
        Compute flare-out parameter at throat: b'(l₀).
        
        Must be < 1 for traversability.
        Determines exotic matter density.
        
        Returns:
            b'(l₀): Shape function derivative at throat
        """
        return self.wh.throat_flare_out_parameter()
    
    def tidal_acceleration_radial(self, l: np.ndarray) -> np.ndarray:
        """
        Compute radial tidal acceleration.
        
        For geodesic deviation (approximate):
        a_tidal ~ Φ''(l) + (corrections from b(l))
        
        Args:
            l: Radial coordinate
            
        Returns:
            Tidal acceleration (m/s²)
        """
        # Numerical second derivative of Φ
        dl = 1e-6 * self.l0
        l_vals = np.atleast_1d(l)
        
        Phi_plus = self.wh.Phi(l_vals + dl)
        Phi_minus = self.wh.Phi(l_vals - dl)
        Phi_l = self.wh.Phi(l_vals)
        
        Phi_double_prime = (Phi_plus - 2*Phi_l + Phi_minus) / dl**2
        
        # Convert to acceleration (multiply by c²)
        return Phi_double_prime * self.wh.params.c**2
    
    def ricci_scalar(self, l: np.ndarray) -> np.ndarray:
        """
        Compute Ricci scalar R at given radial coordinate.
        
        For Morris-Thorne metric (spherically symmetric):
        R = 2[Φ'' + 2Φ'/l - b'/(l²) + 2b/(l³) + ...]
        
        This is a simplified approximation. Full calculation requires
        all Christoffel symbols.
        
        Args:
            l: Radial coordinate
            
        Returns:
            Ricci scalar (m⁻²)
        """
        l_vals = np.atleast_1d(l)
        dl = 1e-6 * self.l0
        
        # Numerical derivatives
        b_l = self.wh.b(l_vals)
        b_plus = self.wh.b(l_vals + dl)
        b_minus = self.wh.b(l_vals - dl)
        b_prime = (b_plus - b_minus) / (2 * dl)
        
        Phi_l = self.wh.Phi(l_vals)
        Phi_plus = self.wh.Phi(l_vals + dl)
        Phi_minus = self.wh.Phi(l_vals - dl)
        Phi_prime = (Phi_plus - Phi_minus) / (2 * dl)
        Phi_double_prime = (Phi_plus - 2*Phi_l + Phi_minus) / dl**2
        
        # Approximate Ricci scalar (simplified)
        R = 2 * (Phi_double_prime + 2*Phi_prime/l_vals - 
                 b_prime/(l_vals**2) + 2*b_l/(l_vals**3))
        
        return R
    
    def throat_properties(self) -> dict:
        """
        Compute comprehensive throat properties.
        
        Returns:
            Dictionary with throat geometry data:
            - l0: Throat radius
            - circumference: Proper circumference
            - b_prime: Flare-out parameter
            - exotic_matter_required: Whether ρ < 0 needed
            - traversable: Traversability status
        """
        l0_arr = np.array([self.l0])
        
        traversable, msg = self.wh.is_traversable()
        b_prime = self.flare_out_parameter()
        
        return {
            "l0_m": self.l0,
            "circumference_m": self.proper_circumference(l0_arr)[0],
            "b_prime": b_prime,
            "exotic_matter_required": b_prime < 1.0,
            "traversable": traversable,
            "traversability_message": msg,
            "ricci_scalar_throat": self.ricci_scalar(l0_arr)[0],
            "tidal_accel_throat": self.tidal_acceleration_radial(l0_arr)[0]
        }


def compute_throat_cross_section(wormhole: MorrisThorne, n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute throat cross-section for visualization.
    
    Args:
        wormhole: MorrisThorne instance
        n_points: Number of points for profile
        
    Returns:
        (l_vals, r_vals): Radial coordinates and embedding radii
    """
    l0 = wormhole.params.l0
    l_vals = np.linspace(l0, 5*l0, n_points)
    
    geom = ThroatGeometry(wormhole)
    r_vals = geom.embedding_radius(l_vals)
    
    return l_vals, r_vals
