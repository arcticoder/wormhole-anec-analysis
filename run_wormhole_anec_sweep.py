"""
Main runner for wormhole ANEC analysis.

Computes ANEC integrals for Morris-Thorne wormholes and generates
JSON report comparing to Phase A/B results.
"""

import json
import numpy as np
from pathlib import Path

from src.metrics.morris_thorne import create_morris_thorne_wormhole
from src.geometry.throat import ThroatGeometry
from src.stress_energy.einstein_solver import EinsteinSolver
from src.anec.wormhole_integrator import WormholeANECIntegrator


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return super().default(obj)


def run_wormhole_anec_analysis():
    """
    Main analysis: Compute ANEC for Morris-Thorne wormholes.
    
    Tests multiple shape functions and compares to warp drive results.
    """
    print("=" * 70)
    print("WORMHOLE ANEC ANALYSIS (Phase C)")
    print("=" * 70)
    print()
    
    # Test configurations
    configs = [
        {"name": "power_law_n0.5", "shape": "power_law", "params": {"n": 0.5}},
        {"name": "power_law_n0.8", "shape": "power_law", "params": {"n": 0.8}},
        {"name": "exponential", "shape": "exponential", "params": {"lambda_scale": 2.0}},
        {"name": "tanh", "shape": "tanh", "params": {"sigma": 0.3}}
    ]
    
    results = {
        "phase": "C",
        "analysis": "wormhole_anec",
        "date": "2025-10-15",
        "wormholes": []
    }
    
    for config in configs:
        print(f"\n{'─'*70}")
        print(f"Configuration: {config['name']}")
        print(f"{'─'*70}")
        
        # Create wormhole
        wh = create_morris_thorne_wormhole(
            l0=1.0,
            shape=config["shape"],
            shape_params=config["params"]
        )
        
        # Check traversability
        traversable, msg = wh.is_traversable()
        print(f"Traversable: {traversable}")
        print(f"Message: {msg}")
        
        if not traversable:
            print("⚠️  Non-traversable wormhole, skipping ANEC computation")
            continue
        
        # Throat geometry
        geom = ThroatGeometry(wh)
        throat_props = geom.throat_properties()
        
        print(f"\nThroat Properties:")
        print(f"  l₀ = {throat_props['l0_m']:.3f} m")
        print(f"  Circumference = {throat_props['circumference_m']:.3f} m")
        print(f"  b'(l₀) = {throat_props['b_prime']:.6f}")
        print(f"  Exotic matter required: {throat_props['exotic_matter_required']}")
        
        # Stress-energy at throat
        solver = EinsteinSolver(wh)
        throat_stress = solver.throat_stress_energy()
        
        print(f"\nThroat Stress-Energy:")
        print(f"  ρ(l₀) = {throat_stress['rho_throat_J_m3']:.3e} J/m³")
        print(f"  p_r(l₀) = {throat_stress['p_r_throat_Pa']:.3e} Pa")
        print(f"  p_t(l₀) = {throat_stress['p_t_throat_Pa']:.3e} Pa")
        print(f"  Exotic: {throat_stress['exotic_matter']}")
        
        # Energy condition violations
        l_test = np.linspace(wh.params.l0, 5*wh.params.l0, 100)
        violations = solver.energy_condition_violations(l_test)
        
        nec_violation_fraction = np.sum(violations["NEC_violated"]) / len(l_test)
        wec_violation_fraction = np.sum(violations["WEC_violated"]) / len(l_test)
        
        print(f"\nEnergy Condition Violations:")
        print(f"  NEC violated: {nec_violation_fraction*100:.1f}% of points")
        print(f"  WEC violated: {wec_violation_fraction*100:.1f}% of points")
        
        # ANEC computation
        print(f"\nComputing ANEC integrals...")
        integrator = WormholeANECIntegrator(wh)
        
        anec_results = integrator.anec_throat_sweep(l_range_factor=5.0, n_geodesics=9)
        summary = integrator.summarize_anec_results(anec_results)
        
        print(f"\nANEC Results:")
        print(f"  Geodesics tested: {summary['n_geodesics']}")
        print(f"  ANEC violations: {summary['n_violations']}/{summary['n_geodesics']} "
              f"({summary['violation_fraction']*100:.1f}%)")
        print(f"  Median ANEC: {summary['median_anec']:.3e} J")
        print(f"  Min ANEC: {summary['min_anec']:.3e} J")
        print(f"  Max ANEC: {summary['max_anec']:.3e} J")
        
        if summary['all_violated']:
            print("  ✗ ALL geodesics violate ANEC")
        elif summary['any_violated']:
            print("  ⚠️  SOME geodesics violate ANEC")
        else:
            print("  ✓ NO ANEC violations")
        
        # Store results
        wormhole_result = {
            "config_name": config["name"],
            "shape_function": config["shape"],
            "shape_params": config["params"],
            "traversable": traversable,
            "throat_properties": {k: (float(v) if isinstance(v, (np.integer, np.floating)) else bool(v) if isinstance(v, np.bool_) else v) 
                                 for k, v in throat_props.items()},
            "throat_stress_energy": {
                "rho_J_m3": float(throat_stress['rho_throat_J_m3']),
                "p_r_Pa": float(throat_stress['p_r_throat_Pa']),
                "p_t_Pa": float(throat_stress['p_t_throat_Pa']),
                "exotic_matter": bool(throat_stress['exotic_matter'])
            },
            "energy_conditions": {
                "NEC_violation_fraction": float(nec_violation_fraction),
                "WEC_violation_fraction": float(wec_violation_fraction)
            },
            "anec_summary": {
                "n_geodesics": summary['n_geodesics'],
                "violation_fraction": float(summary['violation_fraction']),
                "median_anec_J": float(summary['median_anec']),
                "min_anec_J": float(summary['min_anec']),
                "max_anec_J": float(summary['max_anec']),
                "all_violated": summary['all_violated'],
                "any_violated": summary['any_violated']
            },
            "anec_geodesics": [
                {
                    "id": r["geodesic_id"],
                    "anec_J": float(r["anec_integral_J"]),
                    "violated": r["anec_violated"],
                    "negative_fraction": float(r["negative_fraction"])
                }
                for r in anec_results
            ]
        }
        
        results["wormholes"].append(wormhole_result)
    
    # Phase comparison
    print(f"\n{'='*70}")
    print("PHASE COMPARISON")
    print(f"{'='*70}")
    
    # Compute aggregate statistics
    all_violations = [w["anec_summary"]["violation_fraction"] 
                     for w in results["wormholes"]]
    
    if all_violations:
        avg_violation_frac = np.mean(all_violations)
        print(f"\nWormholes (Phase C):")
        print(f"  Average ANEC violation fraction: {avg_violation_frac*100:.1f}%")
    
    print(f"\nPhase A (Warp Drives):")
    print(f"  Natário: 76.9% ANEC violations (median -6.32×10³⁸ J)")
    print(f"  Alcubierre: 0% ANEC violations (positive everywhere)")
    print(f"  QI violations: 10²³× margin")
    
    print(f"\nPhase B (Scalar-Tensor):")
    print(f"  Brans-Dicke: δφ/φ₀ ~ -10²³ (field collapse)")
    print(f"  Horndeski: R_V/R ~ 0.009 (screening 100× too small)")
    
    # Save results
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "wormhole_anec_sweep.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")
    
    return results


if __name__ == "__main__":
    run_wormhole_anec_analysis()
