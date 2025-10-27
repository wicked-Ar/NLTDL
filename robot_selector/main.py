"""
Robot Selector - Suitable Robot Finder for TDL Tasks
Analyzes TDL files and recommends suitable robots based on task requirements.

Usage:
    python robot_selector.py output/task.tdl
    python robot_selector.py output/task.tdl --robots-db ../robots_db.json
    python robot_selector.py output/task.tdl --min-score 50
    python robot_selector.py --scan-all
"""
import argparse
import sys
import json
from pathlib import Path

from tdl_analyzer import TDLAnalyzer, RobotRequirements
from robot_matcher import RobotMatcher, RobotMatch
from robot_similarity import RobotSimilarityAnalyzer


def print_banner():
    """Print application banner."""
    banner = """
===============================================================
            Robot Selector - Suitable Robot Finder
               Analyze TDL and Find Perfect Robot
===============================================================
"""
    print(banner)


def find_robots_db() -> Path:
    """Find robots database file."""
    # Try multiple locations
    locations = [
        Path("robots_db.json"),  # Current directory
        Path("../robots_db.json"),  # Parent directory
        Path("../../robots_db.json"),  # Grandparent
        Path(__file__).parent / "robots_db.json",  # Same as script
        Path(__file__).parent.parent / "robots_db.json",  # Script parent
    ]

    for loc in locations:
        if loc.exists():
            return loc.resolve()

    return None


def scan_output_directory(output_dir: Path, robots_db_path: Path, min_score: float = 0.0):
    """
    Scan all TDL files in output directory and analyze.

    Args:
        output_dir: Output directory path
        robots_db_path: Path to robots database
        min_score: Minimum suitability score
    """
    print(f"\n[INFO] Scanning directory: {output_dir}")

    tdl_files = list(output_dir.glob("*.tdl"))

    if not tdl_files:
        print(f"[WARNING] No TDL files found in {output_dir}")
        return

    print(f"[INFO] Found {len(tdl_files)} TDL file(s)\n")

    analyzer = TDLAnalyzer()
    matcher = RobotMatcher(str(robots_db_path))

    for tdl_file in tdl_files:
        print("="*70)
        print(f"File: {tdl_file.name}")
        print("="*70)

        # Find metadata file
        metadata_file = tdl_file.with_suffix('.json')

        # Analyze TDL
        try:
            requirements = analyzer.analyze_file(
                str(tdl_file),
                str(metadata_file) if metadata_file.exists() else None
            )

            # Find suitable robots
            matches = matcher.find_suitable_robots(requirements, min_score)

            # Show brief summary
            print(f"\nRequired Payload: {requirements.required_payload_kg:.2f} kg")
            print(f"Required Reach: {requirements.required_reach_mm/1000:.2f} m")
            print(f"Task Complexity: {requirements.complexity_score:.1f}/10")

            if matches:
                best = matches[0]
                print(f"\n[BEST] {best.robot} (Score: {best.suitability_score:.1f}/100)")
            else:
                print("\n[WARNING] No suitable robots found!")

            print()

        except Exception as e:
            print(f"[ERROR] Failed to analyze {tdl_file.name}: {e}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Robot Selector - Find suitable robots for TDL tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single TDL file
  python robot_selector.py output/transfer_task.tdl

  # Specify custom robots database
  python robot_selector.py output/welding.tdl --robots-db ../robots_db.json

  # Set minimum suitability score
  python robot_selector.py output/assembly.tdl --min-score 60

  # Scan all TDL files in output directory
  python robot_selector.py --scan-all

  # Scan with custom output directory
  python robot_selector.py --scan-all --output-dir my_tasks
        """
    )

    parser.add_argument(
        "tdl_file",
        nargs="?",
        type=str,
        help="Path to TDL file to analyze"
    )
    parser.add_argument(
        "--robots-db",
        type=str,
        default=None,
        help="Path to robots database JSON file (auto-detect if not specified)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum suitability score (0-100, default: 0)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for TDL files (default: output)"
    )
    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan all TDL files in output directory"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save recommendation report to file"
    )
    parser.add_argument(
        "--find-similar",
        action="store_true",
        help="Find similar robots to the recommended robot (for replacement scenarios)"
    )
    parser.add_argument(
        "--similarity-count",
        type=int,
        default=5,
        help="Number of similar robots to show (default: 5)"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Find robots database
    if args.robots_db:
        robots_db_path = Path(args.robots_db)
    else:
        robots_db_path = find_robots_db()

    if not robots_db_path or not robots_db_path.exists():
        print("[ERROR] Robots database not found!")
        print("\nPlease specify the path using --robots-db option")
        print("Example: python robot_selector.py task.tdl --robots-db ../robots_db.json")
        sys.exit(1)

    print(f"[INFO] Using robots database: {robots_db_path}")

    # Scan all mode
    if args.scan_all:
        output_dir = Path(args.output_dir)
        if not output_dir.exists():
            print(f"[ERROR] Output directory not found: {output_dir}")
            sys.exit(1)

        scan_output_directory(output_dir, robots_db_path, args.min_score)
        sys.exit(0)

    # Single file mode
    if not args.tdl_file:
        print("[ERROR] TDL file path required!")
        print("\nUsage:")
        print("  python robot_selector.py <tdl_file>")
        print("  python robot_selector.py --scan-all")
        print("\nRun with --help for more options")
        sys.exit(1)

    tdl_file_path = Path(args.tdl_file)
    if not tdl_file_path.exists():
        print(f"[ERROR] TDL file not found: {tdl_file_path}")
        sys.exit(1)

    print(f"[INFO] Analyzing TDL file: {tdl_file_path.name}\n")

    # Find metadata file
    metadata_file_path = tdl_file_path.with_suffix('.json')

    # Step 1: Analyze TDL
    print("="*70)
    print("STEP 1: Analyzing TDL Document")
    print("="*70)

    analyzer = TDLAnalyzer()

    try:
        requirements = analyzer.analyze_file(
            str(tdl_file_path),
            str(metadata_file_path) if metadata_file_path.exists() else None
        )

        print(requirements.summary())

    except Exception as e:
        print(f"[ERROR] Failed to analyze TDL file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 2: Find suitable robots
    print("\n" + "="*70)
    print("STEP 2: Finding Suitable Robots")
    print("="*70)

    try:
        matcher = RobotMatcher(str(robots_db_path))
        matches = matcher.find_suitable_robots(requirements, args.min_score)

        print(f"\n[INFO] Found {len(matches)} suitable robot(s)")
        print(f"       (Minimum score: {args.min_score:.0f}/100)\n")

        # Generate report
        report = matcher.generate_recommendation_report(requirements, matches)
        print(report)

        # Save report if requested
        if args.save_report:
            report_path = tdl_file_path.with_suffix('.robot_report.txt')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n[INFO] Report saved to: {report_path}")

            # Also save as JSON
            json_report_path = tdl_file_path.with_suffix('.robot_report.json')
            json_data = {
                "tdl_file": str(tdl_file_path),
                "requirements": {
                    "payload_kg": requirements.required_payload_kg,
                    "reach_mm": requirements.required_reach_mm,
                    "velocity_range": requirements.velocity_range,
                    "acceleration_range": requirements.acceleration_range,
                    "capabilities": requirements.required_capabilities,
                    "complexity_score": requirements.complexity_score,
                },
                "matches": [
                    {
                        "robot": match.robot.to_dict(),
                        "suitability_score": match.suitability_score,
                        "meets_payload": match.meets_payload,
                        "meets_reach": match.meets_reach,
                        "payload_margin_percent": match.payload_margin_percent,
                        "reach_margin_percent": match.reach_margin_percent,
                        "reasons": match.reasons,
                    }
                    for match in matches
                ]
            }

            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            print(f"[INFO] JSON report saved to: {json_report_path}")

    except Exception as e:
        print(f"[ERROR] Failed to find suitable robots: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 3: Find similar robots (if requested)
    if args.find_similar and matches:
        print("\n" + "="*70)
        print("STEP 3: Finding Similar Robots (Replacement Analysis)")
        print("="*70)

        try:
            best_robot = matches[0].robot
            print(f"\n[INFO] Finding robots similar to: {best_robot}")
            print(f"       (For replacement/upgrade scenarios)\n")

            similarity_analyzer = RobotSimilarityAnalyzer(str(robots_db_path))
            similarities = similarity_analyzer.find_similar_robots(
                best_robot,
                min_score=50.0,  # Only show reasonably similar robots
                max_results=args.similarity_count
            )

            if similarities:
                print(f"[INFO] Found {len(similarities)} similar robot(s)\n")

                # Show brief summary
                print("SIMILAR ROBOTS (Ranked by Similarity):")
                print("-"*70)
                for i, sim in enumerate(similarities, 1):
                    print(f"\n{i}. {sim.robot}")
                    print(f"   Similarity Score: {sim.similarity_score:.1f}/100 [{sim.replacement_viability}]")
                    print(f"   Payload: {sim.robot.payload_kg:.1f} kg (vs {best_robot.payload_kg:.1f} kg)")
                    print(f"   Reach: {sim.robot.reach_m:.2f} m (vs {best_robot.reach_m:.2f} m)")
                    if sim.manufacturer_match:
                        print(f"   ✓ Same manufacturer")
                    else:
                        print(f"   ✗ Different manufacturer")

                # Save similarity report if requested
                if args.save_report:
                    similarity_report_path = tdl_file_path.with_suffix('.similarity_report.txt')
                    similarity_report = similarity_analyzer.generate_similarity_report(
                        best_robot,
                        similarities
                    )
                    with open(similarity_report_path, 'w', encoding='utf-8') as f:
                        f.write(similarity_report)
                    print(f"\n[INFO] Similarity report saved to: {similarity_report_path}")
            else:
                print("[WARNING] No similar robots found!")

        except Exception as e:
            print(f"[ERROR] Failed to find similar robots: {e}")
            import traceback
            traceback.print_exc()

    print("\n[DONE] Analysis completed successfully!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
