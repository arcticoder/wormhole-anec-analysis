"""
ANEC integrator for Morris-Thorne wormholes.

Computes Averaged Null Energy Condition (ANEC) integral:

ANEC = ∫ T_μν k^μ k^ν dλ

where k^μ is a null geodesic tangent vector and λ is an affine parameter.

For radial null geodesics in Morris-Thorne metric, we integrate stress-energy
along throat-crossing paths.
"""

import numpy as np
from typing import Tuple, List, Dict
from ..metrics.morris_thorne import MorrisThorne
from ..stress_energy.einstein_solver import EinsteinSolver
from ..metrics.coordinate_mapping import build_r_of_l_mapper


class WormholeANECIntegrator:
    """
    ANEC integrator for wormhole throat-crossing geodesics.
    
    Simplification: For radial null geodesics in spherically symmetric spacetime,
    the geodesic equations reduce to simple expressions.
    """
    
    def __init__(self, wormhole: MorrisThorne):
        """
        Initialize ANEC integrator.
        
        Args:
            wormhole: MorrisThorne instance
        """
        self.wh = wormhole
        self.solver = EinsteinSolver(wormhole)
        
    def radial_null_geodesic(self, l_start: float, l_end: float, 
                            n_points: int = 1000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute radial null geodesic crossing wormhole throat.
        
        For radial null geodesic (θ, φ constant):
        ds² = 0 = -e^{2Φ} dt² + dl²/(1-b/l)
        
        → dt/dl = ±e^{-Φ} √(1-b/l)
        
        Args:
            l_start: Starting radial coordinate
            l_end: Ending radial coordinate
            n_points: Number of integration points
            
        Returns:
            (l_vals, t_vals, lambda_vals): Coordinates and affine parameter
        """
        l_vals = np.linspace(l_start, l_end, n_points)
        
        # Proper time along geodesic
        t_vals = np.zeros(n_points)
        Phi_vals = self.wh.Phi(l_vals)
        b_vals = self.wh.b(l_vals)
        
        for i in range(1, n_points):
            dl = l_vals[i] - l_vals[i-1]
            
            # dt/dl = exp(-Phi) * sqrt(1 - b/l)
            factor = np.exp(-Phi_vals[i]) * np.sqrt(max(1e-12, 1.0 - b_vals[i]/l_vals[i]))
            t_vals[i] = t_vals[i-1] + factor * dl
        
        # Affine parameter (use l as proxy for simplicity)
        lambda_vals = l_vals
        
        return l_vals, t_vals, lambda_vals
    
    def null_tangent_vector(self, l: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute null geodesic tangent vector k^μ.
        
        For radial null geodesic:
        k^t = E (energy)
        k^l = ±√[(1-b/l) E² e^{-2Φ}]
        k^θ = 0
        k^φ = 0
        
        Normalized so k^μ k_μ = 0 (null condition).
        
        Args:
            l: Radial coordinate
            
        Returns:
            Dictionary with k^μ components
        """
        l = np.atleast_1d(l)
        E = 1.0  # Normalize energy to 1
        
        Phi_vals = self.wh.Phi(l)
        b_vals = self.wh.b(l)
        
        k_t = E * np.ones_like(l)
        k_l = np.sqrt(np.maximum(1e-12, (1.0 - b_vals/l))) * E * np.exp(-Phi_vals)
        k_theta = np.zeros_like(l)
        k_phi = np.zeros_like(l)
        
        return {
            "k_t": k_t,
            "k_l": k_l,
            "k_theta": k_theta,
            "k_phi": k_phi
        }
    
    def stress_energy_projection(self, l: np.ndarray) -> np.ndarray:
        """
        Compute T_μν k^μ k^ν along geodesic.
        
        For diagonal stress-energy:
        T_μν k^μ k^ν = T_tt (k^t)² + T_ll (k^l)² + ...
        
        In geometric units: T_tt = ρ, T_ll = p_r
        
        Args:
            l: Radial coordinate along geodesic
            
        Returns:
            T_μν k^μ k^ν values
        """
        l = np.atleast_1d(l)
        
        # Get stress-energy components
        T = self.solver.stress_energy_tensor(l)
        rho = T["rho"]
        p_r = T["p_r"]
        
        # Get null tangent vector (covariant components)
        k_dict = self.null_tangent_vector(l)
        
        # Covariant components: k_μ = g_μν k^ν
        g_tt = -np.exp(2 * self.wh.Phi(l))
        g_ll = 1.0 / (1.0 - self.wh.b(l)/l)
        
        k_t_cov = g_tt * k_dict["k_t"]
        k_l_cov = g_ll * k_dict["k_l"]
        
        # T_μν k^μ k^ν = T_tt k^t k_t + T_ll k^l k_l
        # Note: Convert to same units (J/m³ for both)
        T_kk = rho * k_dict["k_t"] * k_t_cov + p_r * k_dict["k_l"] * k_l_cov
        
        return T_kk
    
    def compute_anec_integral(self, l_start: float, l_end: float, 
                             n_points: int = 1000) -> Dict:
        """
        Compute ANEC integral for throat-crossing geodesic.
        
        ANEC = ∫ T_μν k^μ k^ν dλ
        
        For traversable wormhole, if ANEC < 0, violates ANEC.
        
        Args:
            l_start: Starting radial coordinate (e.g., 5*l₀)
            l_end: Ending radial coordinate (minimum approach, not through throat)
            n_points: Number of integration points
            
        Returns:
            Dictionary with ANEC result and diagnostics
        """
        # Avoid throat singularity: only integrate to slightly above l₀
        l0 = self.wh.params.l0
        l_end_safe = max(l_end, l0 * 1.01)  # Stay 1% above throat
        
        # Geodesic path
        l_vals, t_vals, lambda_vals = self.radial_null_geodesic(l_start, l_end_safe, n_points)
        
        # T_μν k^μ k^ν along path
        T_kk = self.stress_energy_projection(l_vals)
        
        # Filter out infinities and NaNs
        valid_mask = np.isfinite(T_kk)
        if np.sum(valid_mask) < 2:
            return {
                "anec_integral_J": float("nan"),
                "anec_violated": False,
                "median_T_kk": float("nan"),
                "min_T_kk": float("nan"),
                "max_T_kk": float("nan"),
                "negative_fraction": 0.0,
                "l_start": float(l_start),
                "l_end": float(l_end_safe),
                "n_points": int(n_points)
            }
        
        T_kk_valid = T_kk[valid_mask]
        lambda_valid = lambda_vals[valid_mask]
        
        # Integrate using trapezoidal rule
        anec_integral = np.trapz(T_kk_valid, lambda_valid)
        
        # Diagnostics
        median_T_kk = np.median(T_kk_valid)
        min_T_kk = np.min(T_kk_valid)
        max_T_kk = np.max(T_kk_valid)
        negative_fraction = np.sum(T_kk_valid < 0) / len(T_kk_valid)
        
        return {
            "anec_integral_J": float(anec_integral),
            "anec_violated": bool(anec_integral < 0),
            "median_T_kk": float(median_T_kk),
            "min_T_kk": float(min_T_kk),
            "max_T_kk": float(max_T_kk),
            "negative_fraction": float(negative_fraction),
            "l_start": float(l_start),
            "l_end": float(l_end_safe),
            "n_points": int(n_points)
        }
    
    def anec_throat_sweep(self, l_range_factor: float = 5.0, 
                         n_geodesics: int = 9) -> List[Dict]:
        """
        Sweep ANEC over multiple approaching geodesics.
        
        Note: These geodesics approach the throat but don't cross it
        to avoid coordinate singularities.
        
        Args:
            l_range_factor: How far from throat to start (multiples of l₀)
            n_geodesics: Number of geodesics to test
            
        Returns:
            List of ANEC results for each geodesic
        """
        l0 = self.wh.params.l0
        results = []
        
        # Different approach paths (vary starting points slightly)
        for i in range(n_geodesics):
            # Vary starting point from l_range_factor to 2*l_range_factor
            factor = l_range_factor + (i / max(1, n_geodesics-1)) * l_range_factor
            l_start = factor * l0
            l_end = l0 * 1.05  # Approach to 5% above throat
            
            result = self.compute_anec_integral(l_start, l_end)
            result["geodesic_id"] = i
            results.append(result)
        
        return results
    
    def summarize_anec_results(self, results: List[Dict]) -> Dict:
        """
        Summarize ANEC sweep results.
        
        Args:
            results: List of ANEC results from anec_throat_sweep
            
        Returns:
            Summary statistics
        """
        anec_integrals = [r["anec_integral_J"] for r in results]
        violations = [r["anec_violated"] for r in results]
        
        return {
            "n_geodesics": len(results),
            "n_violations": sum(violations),
            "violation_fraction": sum(violations) / len(violations),
            "median_anec": np.median(anec_integrals),
            "mean_anec": np.mean(anec_integrals),
            "min_anec": np.min(anec_integrals),
            "max_anec": np.max(anec_integrals),
            "all_violated": all(violations),
            "any_violated": any(violations)
        }

    # New: Proper-throat-crossing ANEC in l-coordinate
    def compute_anec_crossing(self, r_max_factor: float = 5.0, n_points: int = 4001) -> Dict:
        """
        Compute ANEC integral across the throat using proper radial coordinate l.

        Strategy:
        - Build r(l) mapper from r0 to r_max
        - Integrate along l in [-L, +L] where L = l(r_max)
        - Use integrand (up to affine scaling): e^{-Phi(r(l))} [p_r(r(l)) - rho(r(l))]
        - Integrate over dl; sign indicates (violation vs not)

        Args:
            r_max_factor: Maximum areal radius as multiple of r0
            n_points: Number of l-grid points (odd number recommended)

        Returns:
            Dictionary with ANEC value and diagnostics
        """
        r0 = self.wh.params.l0
        r_max = r_max_factor * r0

        # Build r(l) mapper
        r_of_l = build_r_of_l_mapper(lambda r: self.wh.b(np.atleast_1d(r)), r0, r_max)

        # Determine L = l(r_max)
        # Sample positive l at r_max by calling mapper inverse-like: approximate by stepping to large l
        # We'll estimate L by evaluating l_of_r via mapping table indirectly: sample a few l until r close to r_max
        # Simpler: build a small grid and pick l so that r(l) ~ r_max
        l_pos = np.linspace(0.0, 10.0 * r_max, 5000)
        r_probe = r_of_l(l_pos)
        # Find index where r is closest to r_max
        idx = int(np.argmax(r_probe))
        L = l_pos[idx]

        # Construct symmetric l-grid
        l_grid = np.linspace(-L, L, n_points)
        r_grid = r_of_l(l_grid)

        # Evaluate fields at r(l)
        Phi = self.wh.Phi(r_grid)
        T = self.solver.stress_energy_tensor(r_grid)
        rho = T["rho"]
        p_r = T["p_r"]

        # Integrand proportional to e^{-Phi} (p_r - rho)
        integrand = np.exp(-Phi) * (p_r - rho)

        # Finite-mask to avoid any numerical pathologies
        mask = np.isfinite(integrand)
        if np.count_nonzero(mask) < 3:
            return {
                "anec_crossing": float("nan"),
                "anec_violated": False,
                "negative_fraction": 0.0,
                "L": 0.0,
                "r_max": float(r_max),
                "n_points": int(n_points)
            }

        anec_val = np.trapz(integrand[mask], l_grid[mask])
        neg_frac = float(np.mean(integrand[mask] < 0))

        return {
            "anec_crossing": float(anec_val),
            "anec_violated": bool(anec_val < 0),
            "negative_fraction": neg_frac,
            "L": float(L),
            "r_max": float(r_max),
            "n_points": int(n_points)
        }

    def crossing_sweep(self, configs: List[Dict] | None = None) -> Dict:
        """
        Optional helper to compute crossing ANEC for current wormhole only.
        Provided for API symmetry.
        """
        return self.compute_anec_crossing()
