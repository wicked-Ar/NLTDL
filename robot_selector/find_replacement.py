"""
Robot Replacement Finder - Find Similar Robots for Replacement Scenarios

This tool helps identify suitable replacement robots when:
- Upgrading existing production lines
- Dealing with robot failures/end-of-life
- Expanding production with similar setups
- Standardizing robot fleets

Usage:
    python find_replacement.py --manufacturer doosan --model h2017
    python find_replacement.py --manufacturer universal --model ur10e --min-score 70
    python find_replacement.py --manufacturer doosan --model h2017 --max-results 5
"""
import argparse
import sys
from pathlib import Path

from robot_similarity import RobotSimilarityAnalyzer, Robot


def print_banner():
    """Print application banner."""
    banner = """
===============================================================
        Robot Replacement Finder - Similarity Analysis
           Find Similar Robots for Replacement Scenarios
===============================================================
"""
    print(banner)


def find_robots_db() -> Path:
    """Find robots database file."""
    # Try multiple locations
    locations = [
        Path("robots_db.json"),
        Path("../robots_db.json"),
        Path("../../robots_db.json"),
        Path(__file__).parent / "robots_db.json",
        Path(__file__).parent.parent / "robots_db.json",
    ]

    for loc in locations:
        if loc.exists():
            return loc.resolve()

    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Robot Replacement Finder - Find similar robots for replacement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find replacements for Doosan H2017
  python find_replacement.py --manufacturer doosan --model h2017

  # Find replacements with high similarity (70+ score)
  python find_replacement.py --manufacturer universal --model ur10e --min-score 70

  # Limit results to top 5
  python find_replacement.py --manufacturer doosan --model h2017 --max-results 5

  # Use custom robots database
  python find_replacement.py --manufacturer abb --model irb1600 --robots-db custom.json

  # Compare two specific robots
  python find_replacement.py --compare --robot1-mfr doosan --robot1-model h2017 \\
                             --robot2-mfr yaskawa --robot2-model hc20
        """
    )

    parser.add_argument(
        "--manufacturer",
        type=str,
        help="Manufacturer of robot to replace"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model of robot to replace"
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
        help="Minimum similarity score (0-100, default: 0)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save similarity report to file"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare two specific robots"
    )
    parser.add_argument(
        "--robot1-mfr",
        type=str,
        help="Manufacturer of first robot (for --compare mode)"
    )
    parser.add_argument(
        "--robot1-model",
        type=str,
        help="Model of first robot (for --compare mode)"
    )
    parser.add_argument(
        "--robot2-mfr",
        type=str,
        help="Manufacturer of second robot (for --compare mode)"
    )
    parser.add_argument(
        "--robot2-model",
        type=str,
        help="Model of second robot (for --compare mode)"
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
        print("Example: python find_replacement.py --manufacturer doosan --model h2017 --robots-db robots_db.json")
        sys.exit(1)

    print(f"[INFO] Using robots database: {robots_db_path}")
    print()

    # Initialize similarity analyzer
    analyzer = RobotSimilarityAnalyzer(str(robots_db_path))

    # Compare mode
    if args.compare:
        if not all([args.robot1_mfr, args.robot1_model, args.robot2_mfr, args.robot2_model]):
            print("[ERROR] Compare mode requires all four robot parameters!")
            print("Usage: --compare --robot1-mfr <mfr> --robot1-model <model> \\")
            print("                --robot2-mfr <mfr> --robot2-model <model>")
            sys.exit(1)

        # Find the two robots in database
        robot1 = None
        robot2 = None

        for robot in analyzer.robots:
            if (robot.manufacturer.lower() == args.robot1_mfr.lower() and
                robot.model.lower() == args.robot1_model.lower()):
                robot1 = robot
            if (robot.manufacturer.lower() == args.robot2_mfr.lower() and
                robot.model.lower() == args.robot2_model.lower()):
                robot2 = robot

        if not robot1:
            print(f"[ERROR] Robot not found: {args.robot1_mfr} {args.robot1_model}")
            sys.exit(1)
        if not robot2:
            print(f"[ERROR] Robot not found: {args.robot2_mfr} {args.robot2_model}")
            sys.exit(1)

        print("="*70)
        print("COMPARING TWO ROBOTS")
        print("="*70)
        print(f"\nRobot 1: {robot1}")
        print(f"Robot 2: {robot2}")
        print()

        similarity = analyzer.compare_two_robots(robot1, robot2)

        print(similarity.summary())
        print()
        print(f"Replacement Viability: {similarity.replacement_viability}")
        print()

        sys.exit(0)

    # Normal mode - find replacements
    if not args.manufacturer or not args.model:
        print("[ERROR] Manufacturer and model are required!")
        print("\nUsage:")
        print("  python find_replacement.py --manufacturer <manufacturer> --model <model>")
        print("\nRun with --help for more options")
        sys.exit(1)

    # Find target robot in database
    target_robot = None
    for robot in analyzer.robots:
        if (robot.manufacturer.lower() == args.manufacturer.lower() and
            robot.model.lower() == args.model.lower()):
            target_robot = robot
            break

    if not target_robot:
        print(f"[ERROR] Robot not found in database: {args.manufacturer} {args.model}")
        print("\nAvailable robots:")
        for robot in sorted(analyzer.robots, key=lambda r: (r.manufacturer, r.model)):
            print(f"  - {robot.manufacturer} {robot.model}")
        sys.exit(1)

    print("="*70)
    print("STEP 1: Target Robot Information")
    print("="*70)
    print(f"\n{target_robot}")
    print(f"Payload: {target_robot.payload_kg:.1f} kg")
    print(f"Reach: {target_robot.reach_m:.2f} m")
    print(f"Repeatability: {target_robot.repeatability_mm:.3f} mm")
    print(f"DoF: {target_robot.dof}")
    print()

    # Find similar robots
    print("="*70)
    print("STEP 2: Finding Similar Robots")
    print("="*70)
    print()

    try:
        similarities = analyzer.find_similar_robots(
            target_robot,
            min_score=args.min_score,
            max_results=args.max_results
        )

        print(f"[INFO] Found {len(similarities)} similar robot(s)")
        print(f"       (Minimum score: {args.min_score:.0f}/100, Max results: {args.max_results})\n")

        # Generate report
        report = analyzer.generate_similarity_report(target_robot, similarities)
        print(report)

        # Save report if requested
        if args.save_report:
            report_filename = f"{args.manufacturer}_{args.model}_replacement_report.txt"
            report_path = Path(report_filename)

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"\n[INFO] Report saved to: {report_path}")

    except Exception as e:
        print(f"[ERROR] Failed to find similar robots: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

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
