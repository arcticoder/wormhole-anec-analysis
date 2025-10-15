"""
Comprehensive wormhole analysis: Compare Morris-Thorne vs Thin-Shell models.

Runs complete analysis and generates comparison report.
"""

import json
import numpy as np
from pathlib import Path

from src.metrics.morris_thorne import create_morris_thorne_wormhole
from src.metrics.thin_shell import create_thin_shell_wormhole
from src.anec.wormhole_integrator import WormholeANECIntegrator


def analyze_morris_thorne_config(shape: str, shape_params: dict, 
                                  redshift: str = "zero", 
                                  redshift_params: dict = None) -> dict:
    """Analyze a single Morris-Thorne configuration."""
    print(f"  Analyzing MT {shape}{shape_params}...")
    
    wh = create_morris_thorne_wormhole(
        shape=shape,
        shape_params=shape_params,
        redshift=redshift,
        redshift_params=redshift_params or {}
    )
    
    integrator = WormholeANECIntegrator(wh)
    
    # Crossing ANEC (full throat crossing)
    crossing = integrator.compute_anec_crossing(r_max_factor=3.0, n_points=2001)
    
    # Get throat properties
    l0 = wh.params.l0
    
    # Use Einstein solver to get stress-energy
    from src.stress_energy.einstein_solver import EinsteinSolver
    solver = EinsteinSolver(wh)
    
    rho_throat = solver.energy_density(np.array([l0]))[0]
    p_r_throat = solver.radial_pressure(np.array([l0]))[0]
    
    return {
        "model": "Morris-Thorne",
        "shape": shape,
        "shape_params": shape_params,
        "redshift": redshift,
        "redshift_params": redshift_params or {},
        "throat_radius_m": float(l0),
        "anec_crossing_J": float(crossing["anec_crossing"]),
        "anec_violated": bool(crossing["anec_violated"]),
        "rho_throat_J_m3": float(rho_throat),
        "pr_throat_Pa": float(p_r_throat),
        "exotic_matter_at_throat": bool(rho_throat < 0),
        "L_integration_extent_m": float(crossing.get("L", 0)),
        "n_integration_points": int(crossing.get("n_points", 0))
    }


def analyze_thin_shell_config(a: float, M: float) -> dict:
    """Analyze a thin-shell wormhole configuration."""
    print(f"  Analyzing thin-shell a={a:.2f}, M={M:.2f}...")
    
    wh = create_thin_shell_wormhole(a=a, M=M)
    summary = wh.summary()
    
    return {
        "model": "Thin-Shell",
        "shell_radius_m": a,
        "mass_parameter_kg": M,
        "schwarzschild_radius_m": summary["schwarzschild_radius_m"],
        "anec_shell_J": summary["anec_shell_J"],
        "anec_violated": summary["anec_violated"],
        "surface_energy_density_J_m2": summary["surface_energy_density_J_m2"],
        "surface_tension_Pa": summary["surface_tension_Pa"],
        "exotic_matter_required": summary["exotic_matter_required"],
        "NEC_violated": summary["NEC_violated"],
        "traversable": summary["traversable"]
    }


def run_comprehensive_comparison():
    """Run comprehensive comparison of wormhole models."""
    print("=" * 70)
    print("COMPREHENSIVE WORMHOLE COMPARISON")
    print("=" * 70)
    
    results = {
        "morris_thorne": [],
        "thin_shell": [],
        "summary": {}
    }
    
    # ===== Morris-Thorne Configurations =====
    print("\n1. MORRIS-THORNE WORMHOLES")
    print("-" * 70)
    
    mt_configs = [
        # Best from optimizer
        ("tanh", {"sigma": 0.1}),
        ("tanh", {"sigma": 0.15}),
        ("tanh", {"sigma": 0.2}),
        
        # Other promising
        ("exponential", {"lambda_scale": 0.5}),
        ("exponential", {"lambda_scale": 1.0}),
        
        # For comparison (violations expected)
        ("power_law", {"n": 0.5}),
        ("power_law", {"n": 0.8}),
    ]
    
    for shape, params in mt_configs:
        try:
            res = analyze_morris_thorne_config(shape, params)
            results["morris_thorne"].append(res)
        except Exception as e:
            print(f"    ERROR: {e}")
    
    # ===== Thin-Shell Configurations =====
    print("\n2. THIN-SHELL WORMHOLES")
    print("-" * 70)
    
    thin_shell_configs = [
        (2.0, 0.3),   # Shell radius 2m, low mass
        (2.0, 0.4),
        (3.0, 0.5),
        (5.0, 1.0),   # Larger wormhole
        (10.0, 2.0),  # Even larger
    ]
    
    for a, M in thin_shell_configs:
        try:
            res = analyze_thin_shell_config(a, M)
            results["thin_shell"].append(res)
        except Exception as e:
            print(f"    ERROR: {e}")
    
    # ===== Summary Statistics =====
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Morris-Thorne stats
    mt_satisfied = [r for r in results["morris_thorne"] if not r["anec_violated"]]
    mt_violated = [r for r in results["morris_thorne"] if r["anec_violated"]]
    
    print(f"\nMorris-Thorne:")
    print(f"  Total tested: {len(results['morris_thorne'])}")
    print(f"  ANEC satisfied: {len(mt_satisfied)} ({100*len(mt_satisfied)/len(results['morris_thorne']):.1f}%)")
    print(f"  ANEC violated: {len(mt_violated)} ({100*len(mt_violated)/len(results['morris_thorne']):.1f}%)")
    
    if mt_satisfied:
        best_mt = max(mt_satisfied, key=lambda x: x["anec_crossing_J"])
        print(f"\n  Best ANEC: {best_mt['shape']}{best_mt['shape_params']}")
        print(f"    ANEC = {best_mt['anec_crossing_J']:.3e} J")
        print(f"    ρ(throat) = {best_mt['rho_throat_J_m3']:.3e} J/m³")
    
    # Thin-shell stats
    ts_satisfied = [r for r in results["thin_shell"] if not r["anec_violated"]]
    ts_violated = [r for r in results["thin_shell"] if r["anec_violated"]]
    
    print(f"\nThin-Shell:")
    print(f"  Total tested: {len(results['thin_shell'])}")
    print(f"  ANEC satisfied: {len(ts_satisfied)} ({100*len(ts_satisfied)/len(results['thin_shell']):.1f}%)")
    print(f"  ANEC violated: {len(ts_violated)} ({100*len(ts_violated)/len(results['thin_shell']):.1f}%)")
    
    if ts_satisfied:
        best_ts = max(ts_satisfied, key=lambda x: x["anec_shell_J"])
        print(f"\n  Best ANEC: a={best_ts['shell_radius_m']:.2f}m, M={best_ts['mass_parameter_kg']:.2f}kg")
        print(f"    ANEC = {best_ts['anec_shell_J']:.3e} J")
        print(f"    σ = {best_ts['surface_energy_density_J_m2']:.3e} J/m²")
    
    # Key finding
    print("\n" + "=" * 70)
    total_satisfied = len(mt_satisfied) + len(ts_satisfied)
    total_tested = len(results["morris_thorne"]) + len(results["thin_shell"])
    
    if total_satisfied > 0:
        print("🎯 KEY FINDING: ANEC-satisfying wormhole configurations EXIST!")
        print(f"   {total_satisfied}/{total_tested} configurations satisfy ANEC globally")
        print("   (Exotic matter still required locally at throat)")
    else:
        print("⚠️  No ANEC-satisfying configurations found in tested parameter space")
    
    print("=" * 70)
    
    # Save results
    results["summary"] = {
        "total_tested": total_tested,
        "total_anec_satisfied": total_satisfied,
        "morris_thorne_satisfaction_rate": len(mt_satisfied) / len(results["morris_thorne"]) if results["morris_thorne"] else 0,
        "thin_shell_satisfaction_rate": len(ts_satisfied) / len(results["thin_shell"]) if results["thin_shell"] else 0
    }
    
    output_path = Path("results/comprehensive_wormhole_comparison.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    run_comprehensive_comparison()
