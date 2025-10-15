"""
Stress-energy tensor from Einstein equations for Morris-Thorne wormholes.

From Einstein field equations: G_μν = 8πG T_μν
where G_μν = R_μν - (1/2)g_μν R is the Einstein tensor.

For Morris-Thorne metric, we compute stress-energy components:
- ρ(l): Energy density
- p_r(l): Radial pressure
- p_t(l): Tangential pressure

Key result: Flare-out condition b'(l₀) < 1 implies ρ(l₀) < 0 (exotic matter).
"""

import numpy as np
from typing import Dict
from ..metrics.morris_thorne import MorrisThorne


class EinsteinSolver:
    """
    Solve Einstein equations for Morris-Thorne wormhole stress-energy.
    
    Computes T_μν from metric via Einstein equations.
    Uses numerical derivatives for generality.
    """
    
    def __init__(self, wormhole: MorrisThorne):
        """
        Initialize Einstein equation solver.
        
        Args:
            wormhole: MorrisThorne instance
        """
        self.wh = wormhole
        self.G = wormhole.params.G
        self.c = wormhole.params.c
        
    def energy_density(self, l: np.ndarray) -> np.ndarray:
        """
        Compute energy density ρ(l) from Einstein equations.
        
        From G_θθ = 8πG T_θθ with T_θθ = -p_t:
        
        ρ(l) = (1/(8πG l²)) × [b'(l) - (1 - b/l)(2Φ' l)]
        
        For Φ = 0: ρ(l) = b'(l)/(8πG l²)
        
        Flare-out b'(l₀) < 1 → ρ(l₀) < 0 (exotic matter)
        
        Args:
            l: Radial coordinate
            
        Returns:
            Energy density (kg/m³ in geometric units, or J/m³)
        """
        l = np.atleast_1d(l)
        dl = 1e-6 * self.wh.params.l0
        
        # Numerical derivatives
        b_plus = self.wh.b(l + dl)
        b_minus = self.wh.b(l - dl)
        b_prime = (b_plus - b_minus) / (2 * dl)
        
        Phi_plus = self.wh.Phi(l + dl)
        Phi_minus = self.wh.Phi(l - dl)
        Phi_prime = (Phi_plus - Phi_minus) / (2 * dl)
        
        b_l = self.wh.b(l)
        
        # Energy density (simplified for Φ = 0 case)
        # Full formula: rho = [b' - (1-b/l)(2*Phi'*l)] / (8*pi*G*l^2)
        # For Φ = 0: rho = b' / (8*pi*G*l^2)
        
        term1 = b_prime
        term2 = -(1.0 - b_l/l) * (2 * Phi_prime * l)
        
        rho = (term1 + term2) / (8 * np.pi * self.G * l**2)
        
        # Convert to energy density (J/m³) by multiplying by c²
        return rho * self.c**2
    
    def radial_pressure(self, l: np.ndarray) -> np.ndarray:
        """
        Compute radial pressure p_r(l) from Einstein equations.
        
        From G_tt = 8πG T_tt:
        
        p_r(l) = -(1/(8πG l²)) × [b/l³ - 2(1-b/l)Φ'/l]
        
        For Φ = 0: p_r(l) = -b/(8πG l³)
        
        Args:
            l: Radial coordinate
            
        Returns:
            Radial pressure (Pa or J/m³)
        """
        l = np.atleast_1d(l)
        dl = 1e-6 * self.wh.params.l0
        
        b_l = self.wh.b(l)
        
        Phi_plus = self.wh.Phi(l + dl)
        Phi_minus = self.wh.Phi(l - dl)
        Phi_prime = (Phi_plus - Phi_minus) / (2 * dl)
        
        # Radial pressure
        # Full: p_r = -[b/l^3 - 2(1-b/l)Phi'/l] / (8*pi*G)
        # For Φ = 0: p_r = -b / (8*pi*G*l^3)
        
        term1 = b_l / l**3
        term2 = -2 * (1.0 - b_l/l) * Phi_prime / l
        
        p_r = -(term1 + term2) / (8 * np.pi * self.G)
        
        # Convert to pressure (Pa = J/m³)
        return p_r * self.c**2
    
    def tangential_pressure(self, l: np.ndarray) -> np.ndarray:
        """
        Compute tangential pressure p_t(l) from Einstein equations.
        
        From G_rr = 8πG T_rr:
        
        p_t(l) = (1/(8πG l)) × [(1-b/l)(Φ'' + Φ'²) + 
                                  Φ'/l × (b' - b/l) - 
                                  b''/(2l) + b'b/(2l²)]
        
        For Φ = 0: Simplified expression
        
        Args:
            l: Radial coordinate
            
        Returns:
            Tangential pressure (Pa or J/m³)
        """
        l = np.atleast_1d(l)
        dl = 1e-6 * self.wh.params.l0
        
        # Numerical derivatives
        b_l = self.wh.b(l)
        b_plus = self.wh.b(l + dl)
        b_minus = self.wh.b(l - dl)
        b_prime = (b_plus - b_minus) / (2 * dl)
        b_double_prime = (b_plus - 2*b_l + b_minus) / dl**2
        
        Phi_l = self.wh.Phi(l)
        Phi_plus = self.wh.Phi(l + dl)
        Phi_minus = self.wh.Phi(l - dl)
        Phi_prime = (Phi_plus - Phi_minus) / (2 * dl)
        Phi_double_prime = (Phi_plus - 2*Phi_l + Phi_minus) / dl**2
        
        # Tangential pressure (complex expression)
        factor = 1.0 - b_l / l
        
        term1 = factor * (Phi_double_prime + Phi_prime**2)
        term2 = (Phi_prime / l) * (b_prime - b_l/l)
        term3 = -b_double_prime / (2*l)
        term4 = b_prime * b_l / (2 * l**2)
        
        p_t = (term1 + term2 + term3 + term4) / (8 * np.pi * self.G * l)
        
        # Convert to pressure
        return p_t * self.c**2
    
    def stress_energy_tensor(self, l: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute all stress-energy components.
        
        Args:
            l: Radial coordinate
            
        Returns:
            Dictionary with components:
            - rho: Energy density (J/m³)
            - p_r: Radial pressure (Pa)
            - p_t: Tangential pressure (Pa)
            - T_tt: T_00 component
            - T_rr: T_11 component
            - T_theta_theta: T_22 component
        """
        l = np.atleast_1d(l)
        
        rho = self.energy_density(l)
        p_r = self.radial_pressure(l)
        p_t = self.tangential_pressure(l)
        
        return {
            "rho": rho,
            "p_r": p_r,
            "p_t": p_t,
            "T_tt": rho,           # T_00 = ρ
            "T_rr": p_r,           # T_11 = p_r
            "T_theta_theta": p_t,  # T_22 = p_t
            "T_phi_phi": p_t       # T_33 = p_t (spherical symmetry)
        }
    
    def throat_stress_energy(self) -> Dict[str, float]:
        """
        Compute stress-energy at wormhole throat.
        
        Critical for exotic matter requirement.
        
        Returns:
            Dictionary with throat stress-energy:
            - rho_throat: Energy density at l₀
            - p_r_throat: Radial pressure at l₀
            - p_t_throat: Tangential pressure at l₀
            - exotic_matter: Whether ρ < 0
        """
        l0 = np.array([self.wh.params.l0])
        
        T = self.stress_energy_tensor(l0)
        
        return {
            "rho_throat_J_m3": T["rho"][0],
            "p_r_throat_Pa": T["p_r"][0],
            "p_t_throat_Pa": T["p_t"][0],
            "exotic_matter": T["rho"][0] < 0,
            "l0_m": self.wh.params.l0
        }
    
    def energy_condition_violations(self, l: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Check energy condition violations.
        
        Energy conditions:
        - NEC (Null): ρ + p_i ≥ 0 for all i
        - WEC (Weak): ρ ≥ 0 and ρ + p_i ≥ 0
        - SEC (Strong): ρ + Σp_i ≥ 0 and ρ + p_i ≥ 0
        - DEC (Dominant): ρ ≥ |p_i|
        
        Args:
            l: Radial coordinate
            
        Returns:
            Dictionary with violation booleans
        """
        l = np.atleast_1d(l)
        
        T = self.stress_energy_tensor(l)
        rho = T["rho"]
        p_r = T["p_r"]
        p_t = T["p_t"]
        
        # Null energy condition: ρ + p ≥ 0
        NEC_radial = rho + p_r >= 0
        NEC_tangential = rho + p_t >= 0
        NEC_satisfied = np.logical_and(NEC_radial, NEC_tangential)
        
        # Weak energy condition: ρ ≥ 0 and NEC
        WEC_satisfied = np.logical_and(rho >= 0, NEC_satisfied)
        
        # Strong energy condition: ρ + p_r + 2p_t ≥ 0 and ρ + p_i ≥ 0
        SEC_sum = rho + p_r + 2*p_t >= 0
        SEC_satisfied = np.logical_and(SEC_sum, NEC_satisfied)
        
        # Dominant energy condition: ρ ≥ |p_i|
        DEC_radial = rho >= np.abs(p_r)
        DEC_tangential = rho >= np.abs(p_t)
        DEC_satisfied = np.logical_and(DEC_radial, DEC_tangential)
        
        return {
            "NEC_violated": ~NEC_satisfied,
            "WEC_violated": ~WEC_satisfied,
            "SEC_violated": ~SEC_satisfied,
            "DEC_violated": ~DEC_satisfied,
            "NEC_radial": NEC_radial,
            "NEC_tangential": NEC_tangential
        }
