"""
Run wormhole configuration optimizer.

Searches for Morris-Thorne configurations with minimal ANEC violations.
"""

import json
from pathlib import Path
from src.optimization.config_optimizer import optimize_wormhole_config


def main():
    """Main optimizer runner."""
    # Run optimization
    results = optimize_wormhole_config(l0=1.0, verbose=True)
    
    # Save results
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "wormhole_optimization.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("=" * 70)
    print(f"Optimization results saved to: {output_file}")
    print("=" * 70)
    
    # Summary
    best = results["best_configs"][0]
    print("\nBEST CONFIGURATION:")
    print(f"  Shape: {best['shape']}{best['shape_params']}")
    print(f"  ANEC: {best['anec_crossing']:.3e} J")
    print(f"  Violation: {'YES' if best['anec_violated'] else 'NO'}")
    print(f"  ρ(l₀): {best['rho_throat']:.3e} J/m³")
    
    if not best['anec_violated']:
        print("\n🎯 BREAKTHROUGH: Found ANEC-satisfying wormhole configuration!")
    else:
        print("\n⚠️  All configurations still violate ANEC (searching for minimum violation)")


if __name__ == "__main__":
    main()
