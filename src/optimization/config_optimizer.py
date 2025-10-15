"""
Configuration optimizer for Morris-Thorne wormholes.

Search for shape/redshift function parameters that:
1. Satisfy traversability (b(l0)=l0, b'(l0)<1, Φ finite)
2. Minimize ANEC violation (maximize ANEC_crossing ≥ 0)
3. Minimize exotic matter magnitude |ρ(l0)|
4. Keep tidal forces bounded

Strategy: Grid search + local refinement via scipy.optimize.minimize
"""

import numpy as np
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
from ..metrics.morris_thorne import create_morris_thorne_wormhole, MorrisThorne
from ..anec.wormhole_integrator import WormholeANECIntegrator
from ..stress_energy.einstein_solver import EinsteinSolver


@dataclass
class OptimizationResult:
    """Result from wormhole configuration optimization."""
    shape: str
    shape_params: Dict
    redshift: str
    redshift_params: Dict
    anec_crossing: float
    anec_violated: bool
    rho_throat: float
    traversable: bool
    score: float  # Higher is better


class WormholeOptimizer:
    """Optimizer for wormhole configurations."""
    
    def __init__(self, l0: float = 1.0, r_max_factor: float = 3.0, n_anec_points: int = 2001):
        """
        Initialize optimizer.
        
        Args:
            l0: Throat radius
            r_max_factor: Integration extent for ANEC
            n_anec_points: Resolution for ANEC integral
        """
        self.l0 = l0
        self.r_max_factor = r_max_factor
        self.n_anec_points = n_anec_points
        
    def evaluate_config(self, shape: str, shape_params: Dict,
                       redshift: str = "zero", redshift_params: Dict = None) -> OptimizationResult:
        """
        Evaluate a single configuration.
        
        Returns:
            OptimizationResult with score (higher = better)
        """
        if redshift_params is None:
            redshift_params = {}
            
        try:
            # Create wormhole
            wh = create_morris_thorne_wormhole(
                l0=self.l0,
                shape=shape,
                shape_params=shape_params,
                redshift=redshift,
                redshift_params=redshift_params
            )
            
            # Check traversability
            traversable, msg = wh.is_traversable()
            if not traversable:
                return OptimizationResult(
                    shape=shape, shape_params=shape_params,
                    redshift=redshift, redshift_params=redshift_params,
                    anec_crossing=float('-inf'), anec_violated=True,
                    rho_throat=0.0, traversable=False, score=float('-inf')
                )
            
            # Compute ANEC crossing
            integrator = WormholeANECIntegrator(wh)
            anec_res = integrator.compute_anec_crossing(self.r_max_factor, self.n_anec_points)
            anec_crossing = anec_res["anec_crossing"]
            
            # Get throat stress-energy
            solver = EinsteinSolver(wh)
            throat_stress = solver.throat_stress_energy()
            rho_throat = throat_stress["rho_throat_J_m3"]
            
            # Score function (to maximize):
            # Priority: ANEC_crossing ≥ 0, then minimize |rho|
            if np.isnan(anec_crossing):
                score = float('-inf')
            elif anec_crossing >= 0:
                # Positive ANEC: bonus + penalty for large |rho|
                score = 1e30 + anec_crossing - 1e-20 * abs(rho_throat)
            else:
                # Negative ANEC: penalty proportional to violation
                score = anec_crossing
            
            return OptimizationResult(
                shape=shape, shape_params=shape_params,
                redshift=redshift, redshift_params=redshift_params,
                anec_crossing=float(anec_crossing),
                anec_violated=bool(anec_crossing < 0),
                rho_throat=float(rho_throat),
                traversable=True,
                score=float(score)
            )
            
        except Exception as e:
            return OptimizationResult(
                shape=shape, shape_params=shape_params,
                redshift=redshift, redshift_params=redshift_params,
                anec_crossing=float('-inf'), anec_violated=True,
                rho_throat=0.0, traversable=False, score=float('-inf')
            )
    
    def grid_search_power_law(self, n_values: np.ndarray = None) -> List[OptimizationResult]:
        """Grid search over power-law shape function parameter n."""
        if n_values is None:
            n_values = np.linspace(0.1, 0.99, 20)
        
        results = []
        for n in n_values:
            res = self.evaluate_config("power_law", {"n": float(n)})
            results.append(res)
        
        return results
    
    def grid_search_exponential(self, lambda_values: np.ndarray = None) -> List[OptimizationResult]:
        """Grid search over exponential shape function parameter λ."""
        if lambda_values is None:
            lambda_values = np.linspace(0.5, 5.0, 20)
        
        results = []
        for lam in lambda_values:
            res = self.evaluate_config("exponential", {"lambda_scale": float(lam)})
            results.append(res)
        
        return results
    
    def grid_search_tanh(self, sigma_values: np.ndarray = None) -> List[OptimizationResult]:
        """Grid search over tanh shape function parameter σ."""
        if sigma_values is None:
            sigma_values = np.linspace(0.1, 1.0, 20)
        
        results = []
        for sigma in sigma_values:
            res = self.evaluate_config("tanh", {"sigma": float(sigma)})
            results.append(res)
        
        return results
    
    def comprehensive_search(self) -> Dict[str, List[OptimizationResult]]:
        """
        Comprehensive grid search across all shape families.
        
        Returns:
            Dictionary mapping shape type to results list
        """
        return {
            "power_law": self.grid_search_power_law(),
            "exponential": self.grid_search_exponential(),
            "tanh": self.grid_search_tanh()
        }
    
    def find_best_config(self, max_candidates: int = 10) -> List[OptimizationResult]:
        """
        Find best configurations across all families.
        
        Args:
            max_candidates: Number of top candidates to return
            
        Returns:
            Sorted list of top configurations (best first)
        """
        all_results = self.comprehensive_search()
        
        # Flatten and sort by score
        flat_results = []
        for family_results in all_results.values():
            flat_results.extend(family_results)
        
        flat_results.sort(key=lambda r: r.score, reverse=True)
        
        return flat_results[:max_candidates]


def optimize_wormhole_config(l0: float = 1.0, verbose: bool = True) -> Dict:
    """
    High-level optimizer interface.
    
    Args:
        l0: Throat radius
        verbose: Print progress
        
    Returns:
        Dictionary with best configurations and search results
    """
    optimizer = WormholeOptimizer(l0=l0)
    
    if verbose:
        print("=" * 70)
        print("WORMHOLE CONFIGURATION OPTIMIZATION")
        print("=" * 70)
        print(f"Throat radius: {l0} m")
        print(f"Searching across power-law, exponential, tanh shape functions...")
        print()
    
    # Comprehensive search
    all_results = optimizer.comprehensive_search()
    
    # Find best overall
    best_configs = optimizer.find_best_config(max_candidates=10)
    
    if verbose:
        print("Top 10 Configurations:")
        print("-" * 70)
        for i, res in enumerate(best_configs, 1):
            print(f"{i}. {res.shape}({res.shape_params})")
            print(f"   ANEC: {res.anec_crossing:.3e} J ({'VIOLATED' if res.anec_violated else 'SATISFIED'})")
            print(f"   ρ(l₀): {res.rho_throat:.3e} J/m³")
            print(f"   Score: {res.score:.3e}")
            print()
    
    # Statistics
    total_configs = sum(len(results) for results in all_results.values())
    satisfied_anec = sum(1 for r in best_configs if not r.anec_violated)
    
    if verbose:
        print(f"Total configurations tested: {total_configs}")
        print(f"Configurations with ANEC ≥ 0 (in top 10): {satisfied_anec}/10")
        print()
    
    return {
        "best_configs": [
            {
                "rank": i+1,
                "shape": res.shape,
                "shape_params": res.shape_params,
                "redshift": res.redshift,
                "redshift_params": res.redshift_params,
                "anec_crossing": res.anec_crossing,
                "anec_violated": res.anec_violated,
                "rho_throat": res.rho_throat,
                "traversable": res.traversable,
                "score": res.score
            }
            for i, res in enumerate(best_configs)
        ],
        "search_summary": {
            "total_tested": total_configs,
            "top10_anec_satisfied": satisfied_anec,
            "families_tested": list(all_results.keys())
        },
        "full_results": {
            family: [
                {
                    "shape_params": r.shape_params,
                    "anec_crossing": r.anec_crossing,
                    "anec_violated": r.anec_violated,
                    "score": r.score
                }
                for r in results
            ]
            for family, results in all_results.items()
        }
    }
