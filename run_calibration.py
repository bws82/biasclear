#!/usr/bin/env python3
"""
run_calibration.py — Run the full calibration pipeline.

Usage:
    python run_calibration.py                      # Full run
    python run_calibration.py --corpus-dir path/    # Custom corpus location
    python run_calibration.py --domain legal        # Filter by domain
    python run_calibration.py --optimize            # Include weight recommendations
    python run_calibration.py --json                # Output JSON only (for CI)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from calibration.corpus_parser import parse_all_corpora
from calibration.benchmark import run_benchmark, format_report, save_report
from calibration.optimizer import optimize_weights, format_optimization_report


def main():
    parser = argparse.ArgumentParser(description="BiasClear Calibration Runner")
    parser.add_argument(
        "--corpus-dir",
        default="calibration/corpus",
        help="Path to corpus directory (default: calibration/corpus)",
    )
    parser.add_argument(
        "--domain",
        default="legal",
        help="Domain to evaluate (default: legal)",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Include weight optimization recommendations",
    )
    parser.add_argument(
        "--output-dir",
        default="calibration/reports",
        help="Directory for output reports (default: calibration/reports)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (for CI/automation)",
    )
    args = parser.parse_args()

    # Step 1: Check corpus
    corpus_dir = Path(args.corpus_dir)
    if not corpus_dir.exists():
        print(f"Error: Corpus directory not found: {corpus_dir}")
        sys.exit(1)

    samples = parse_all_corpora(corpus_dir)
    if not samples:
        print(f"Error: No samples found in {corpus_dir}")
        print("Add tagged samples to calibration/corpus/legal_corpus.txt")
        sys.exit(1)

    print(f"Loaded {len(samples)} samples from {corpus_dir}")

    # Step 2: Run benchmark
    result = run_benchmark(corpus_dir=corpus_dir, domain=args.domain)

    # Step 3: Output
    if args.json:
        import json
        _, json_path = save_report(result, args.output_dir)
        print(json_path.read_text())
    else:
        report = format_report(result)
        print(report)

        # Save to files
        report_path, json_path = save_report(result, args.output_dir)
        print(f"\nReport saved to: {report_path}")
        print(f"JSON saved to:   {json_path}")

    # Step 4: Optimization (if requested)
    if args.optimize:
        opt_report = optimize_weights(result)
        opt_text = format_optimization_report(opt_report)

        if args.json:
            import json
            print(json.dumps({
                "summary": opt_report.summary,
                "separation": opt_report.current_separation,
                "recommendations": [
                    {
                        "parameter": r.parameter,
                        "current": r.current_value,
                        "recommended": r.recommended_value,
                        "reason": r.reason,
                    }
                    for r in opt_report.recommendations
                ],
            }, indent=2))
        else:
            print()
            print(opt_text)

    # Step 5: Exit code for CI
    if result.overall_f1 < 0.5 and result.biased_samples > 5:
        print("\n⚠️  F1 below 0.5 — calibration failing")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
