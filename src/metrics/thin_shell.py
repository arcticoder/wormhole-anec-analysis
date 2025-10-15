"""
Thin-shell wormholes via Visser cut-and-paste construction.

Reference: Visser (1989) "Traversable wormholes: Some simple examples"

Construction:
1. Take two copies of Schwarzschild spacetime (or other solution)
2. Cut at radius a > 2M (outside horizon)
3. Identify the boundaries → create a throat at r=a
4. Surface stress-energy from Israel junction conditions

Israel junction: [K_ij] = 8πG (S_ij - (1/2)h_ij S)
where K_ij is extrinsic curvature discontinuity, S_ij is surface stress

For thin shell at r=a, we get:
- Surface energy density σ
- Surface tension τ

ANEC along null generators on the shell.
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class ThinShellParams:
    """Parameters for thin-shell wormhole."""
    a: float = 2.0           # Shell radius (m), must be > 2M for Schwarzschild
    M: float = 0.5           # Mass parameter (M < a/2 for no horizon)
    G: float = 6.674e-11     # Gravitational constant
    c: float = 2.998e8       # Speed of light
    
    def __post_init__(self):
        """Validate parameters."""
        r_s = 2 * self.G * self.M / (self.c**2)
        if self.a <= r_s:
            raise ValueError(f"Shell radius a={self.a} must be > 2GM/c²={r_s}")


class ThinShellWormhole:
    """
    Thin-shell wormhole from Schwarzschild cut-and-paste.
    
    Metric (outside shell r > a):
    ds² = -(1 - 2M/r) dt² + dr²/(1 - 2M/r) + r²dΩ²
    
    At shell r=a, discontinuity in extrinsic curvature → surface stress
    """
    
    def __init__(self, params: ThinShellParams):
        """Initialize thin-shell wormhole."""
        self.params = params
        self.a = params.a
        self.M = params.M
        self.G = params.G
        self.c = params.c
        
    def schwarzschild_radius(self) -> float:
        """Schwarzschild radius r_s = 2GM/c²."""
        return 2 * self.G * self.M / (self.c**2)
    
    def metric_coefficient_gtt(self, r: np.ndarray) -> np.ndarray:
        """g_tt = -(1 - 2M/r) for r > a."""
        r = np.atleast_1d(r)
        return -(1.0 - 2 * self.M / r)
    
    def metric_coefficient_grr(self, r: np.ndarray) -> np.ndarray:
        """g_rr = 1/(1 - 2M/r) for r > a."""
        r = np.atleast_1d(r)
        return 1.0 / (1.0 - 2 * self.M / r)
    
    def extrinsic_curvature_jump(self) -> Tuple[float, float]:
        """
        Compute jump in extrinsic curvature at shell r=a.
        
        For Schwarzschild throat:
        [K_θθ] = discontinuity in K_θθ across shell
        [K_φφ] = discontinuity in K_φφ
        
        Returns:
            (K_theta_jump, K_phi_jump)
        """
        # Extrinsic curvature of spherical shell in Schwarzschild
        # K_θθ = r√(1-2M/r) (induced geometry term)
        # Jump: [K] = 2 * K(a) since we glue two copies
        
        factor = self.a * np.sqrt(1.0 - 2 * self.M / self.a)
        K_theta_jump = 2.0 / factor  # Simplified: [K_θθ] ∝ 1/√(a(a-2M))
        
        return K_theta_jump, K_theta_jump  # Spherical symmetry
    
    def surface_energy_density(self) -> float:
        """
        Surface energy density σ from Israel junction conditions.
        
        Israel: σ = -[K]/(8πG)
        where [K] is the trace of extrinsic curvature jump
        
        Returns:
            σ in kg/m² (or J/m² in c=1 units)
        """
        K_jump, _ = self.extrinsic_curvature_jump()
        
        # Trace [K] = [K_θθ + K_φφ]/a² (normalized)
        # Simplified: σ ~ -√(a-2M)/a / (8πG)
        
        sigma = -(1.0 / self.a) * np.sqrt((self.a - self.schwarzschild_radius()) / self.a) / (8 * np.pi * self.G)
        
        # Convert to energy density (multiply by c²)
        return sigma * self.c**2
    
    def surface_tension(self) -> float:
        """
        Surface tension τ from Israel junction conditions.
        
        For static thin shell, relates to radial pressure balance.
        
        Returns:
            τ in Pa (or J/m² in c=1 units)
        """
        # Simplified model: τ ≈ σ/2 for equilibrium
        sigma = self.surface_energy_density()
        return sigma / 2.0
    
    def is_exotic(self) -> bool:
        """Check if surface stress-energy violates energy conditions."""
        sigma = self.surface_energy_density()
        tau = self.surface_tension()
        
        # Null energy condition on shell: σ + τ ≥ 0
        NEC = sigma + tau >= 0
        
        # Weak energy condition: σ ≥ 0 and σ ± τ ≥ 0
        WEC = (sigma >= 0) and (sigma + tau >= 0) and (sigma - tau >= 0)
        
        return not (NEC and WEC)
    
    def anec_on_shell(self, n_points: int = 1000) -> Dict:
        """
        Compute ANEC integral along null generator on the shell.
        
        For null ray grazing the shell at r=a, we integrate surface stress
        projected onto null direction.
        
        Returns:
            Dictionary with ANEC result
        """
        # Null generator: tangent k^μ = (E, 0, k^θ, 0) on shell
        # Surface stress: S_μν projected
        
        sigma = self.surface_energy_density()
        tau = self.surface_tension()
        
        # ANEC integrand (simplified): T_kk ~ (σ + τ) on the shell
        # For grazing null ray: integrate over shell circumference
        
        circumference = 2 * np.pi * self.a
        
        # T_μν k^μ k^ν ~ (σ + τ) for null k on 2-sphere
        T_kk_shell = sigma + tau
        
        # ANEC = ∫ T_kk dλ ~ T_kk * (path length)
        # Path length ~ circumference for equatorial null orbit
        anec_shell = T_kk_shell * circumference
        
        return {
            "anec_shell": float(anec_shell),
            "anec_violated": bool(anec_shell < 0),
            "sigma": float(sigma),
            "tau": float(tau),
            "NEC_violated": bool(sigma + tau < 0),
            "exotic_matter": self.is_exotic(),
            "shell_radius": float(self.a),
            "circumference": float(circumference)
        }
    
    def summary(self) -> Dict:
        """Complete summary of thin-shell wormhole properties."""
        anec_res = self.anec_on_shell()
        
        return {
            "shell_radius_m": float(self.a),
            "mass_parameter_kg": float(self.M),
            "schwarzschild_radius_m": float(self.schwarzschild_radius()),
            "surface_energy_density_J_m2": anec_res["sigma"],
            "surface_tension_Pa": anec_res["tau"],
            "exotic_matter_required": anec_res["exotic_matter"],
            "NEC_violated": anec_res["NEC_violated"],
            "anec_shell_J": anec_res["anec_shell"],
            "anec_violated": anec_res["anec_violated"],
            "traversable": self.a > self.schwarzschild_radius()
        }


def create_thin_shell_wormhole(a: float = 2.0, M: float = 0.4) -> ThinShellWormhole:
    """
    Factory to create thin-shell wormhole.
    
    Args:
        a: Shell radius (m)
        M: Mass parameter (kg), must satisfy a > 2GM/c²
        
    Returns:
        ThinShellWormhole instance
    """
    params = ThinShellParams(a=a, M=M)
    return ThinShellWormhole(params)
