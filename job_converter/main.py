"""
Job Converter - TDL to Robot-Specific Code Converter
Converts TDL files to manufacturer-specific robot control code.

Usage:
    python main.py input.tdl --robot doosan
    python main.py input.tdl --robot universal -o output.script
    python main.py input.tdl --auto  # Auto-detect from robot_selector
"""
import argparse
import sys
import json
from pathlib import Path

from tdl_parser import TDLParser
from doosan_converter import DoosanJobGenerator
from universal_converter import UniversalJobGenerator


def print_banner():
    """Print application banner."""
    banner = """
===============================================================
              Job Converter - TDL to Robot Code
          Convert TDL to Manufacturer-Specific Code
===============================================================
"""
    print(banner)


def detect_robot_from_report(tdl_file_path: Path) -> str:
    """
    Detect recommended robot from robot_selector report.

    Args:
        tdl_file_path: Path to TDL file

    Returns:
        Robot manufacturer name or None
    """
    # Look for robot_report.json
    report_file = tdl_file_path.with_suffix('.robot_report.json')

    if not report_file.exists():
        return None

    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # Get best match
        matches = report.get('matches', [])
        if matches:
            best_robot = matches[0]['robot']
            manufacturer = best_robot.get('manufacturer', '').lower()
            return manufacturer
    except Exception as e:
        print(f"[WARNING] Failed to read robot report: {e}")
        return None


def convert_tdl(
    tdl_file: Path,
    robot: str,
    output_file: Path = None
) -> str:
    """
    Convert TDL file to robot-specific code.

    Args:
        tdl_file: Input TDL file path
        robot: Robot manufacturer ('doosan', 'universal', etc.)
        output_file: Output file path (optional)

    Returns:
        Generated code as string
    """
    # Parse TDL
    print(f"\n[1/3] Parsing TDL file: {tdl_file.name}")
    parser = TDLParser()

    try:
        program = parser.parse_file(str(tdl_file))
        print(f"[OK] Parsed {len(program.goals)} GOALs")
    except Exception as e:
        print(f"[ERROR] Failed to parse TDL: {e}")
        raise

    # Convert to robot-specific code
    print(f"\n[2/3] Converting to {robot.upper()} code...")

    try:
        if robot == 'doosan':
            generator = DoosanJobGenerator()
            code = generator.generate(program)
            default_ext = '.drl'
        elif robot == 'universal':
            generator = UniversalJobGenerator()
            code = generator.generate(program)
            default_ext = '.script'
        else:
            raise ValueError(f"Unsupported robot: {robot}")

        print(f"[OK] Conversion completed ({len(code)} characters)")
    except Exception as e:
        print(f"[ERROR] Failed to convert: {e}")
        raise

    # Save output
    print(f"\n[3/3] Saving output...")

    if output_file is None:
        # Auto-generate output filename
        output_file = tdl_file.with_suffix(default_ext)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)

        print(f"[OK] Saved to: {output_file}")
        print(f"[INFO] File size: {output_file.stat().st_size} bytes")
    except Exception as e:
        print(f"[ERROR] Failed to save: {e}")
        raise

    return code


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Job Converter - Convert TDL to robot-specific code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert to Doosan DRL
  python main.py task.tdl --robot doosan

  # Convert to Universal Robots UR Script
  python main.py task.tdl --robot universal

  # Auto-detect robot from robot_selector report
  python main.py task.tdl --auto

  # Specify output file
  python main.py task.tdl --robot doosan -o my_program.drl

  # Convert all TDL files in directory
  python main.py --batch ../output --robot universal

Supported Robots:
  - doosan    : Doosan Robotics (DRL - Python-based)
  - universal : Universal Robots (UR Script)
        """
    )

    parser.add_argument(
        "tdl_file",
        nargs="?",
        type=str,
        help="Path to TDL file to convert"
    )
    parser.add_argument(
        "--robot",
        type=str,
        choices=["doosan", "universal"],
        help="Target robot manufacturer"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (default: auto-generated)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect robot from robot_selector report"
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Batch convert all TDL files in directory"
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print code to console instead of saving"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Batch mode
    if args.batch:
        batch_dir = Path(args.batch)
        if not batch_dir.exists():
            print(f"[ERROR] Directory not found: {batch_dir}")
            sys.exit(1)

        if not args.robot:
            print("[ERROR] --robot is required for batch mode")
            sys.exit(1)

        tdl_files = list(batch_dir.glob("*.tdl"))
        if not tdl_files:
            print(f"[WARNING] No TDL files found in {batch_dir}")
            sys.exit(0)

        print(f"[INFO] Found {len(tdl_files)} TDL file(s)")
        print()

        for tdl_file in tdl_files:
            print("="*60)
            print(f"Converting: {tdl_file.name}")
            print("="*60)

            try:
                convert_tdl(tdl_file, args.robot)
                print()
            except Exception as e:
                print(f"[ERROR] Failed: {e}")
                print()
                continue

        print("[DONE] Batch conversion completed")
        sys.exit(0)

    # Single file mode
    if not args.tdl_file:
        print("[ERROR] TDL file path required!")
        print("\nUsage:")
        print("  python main.py <tdl_file> --robot <robot>")
        print("  python main.py --help")
        sys.exit(1)

    tdl_file = Path(args.tdl_file)
    if not tdl_file.exists():
        print(f"[ERROR] TDL file not found: {tdl_file}")
        sys.exit(1)

    # Determine robot
    robot = args.robot

    if args.auto:
        print("[INFO] Auto-detecting robot from report...")
        detected_robot = detect_robot_from_report(tdl_file)

        if detected_robot:
            robot = detected_robot
            print(f"[OK] Detected robot: {robot.upper()}")
        else:
            print("[WARNING] Could not auto-detect robot")
            if not robot:
                print("[ERROR] Please specify --robot manually")
                sys.exit(1)

    if not robot:
        print("[ERROR] Robot not specified!")
        print("Use --robot <manufacturer> or --auto")
        sys.exit(1)

    # Determine output file
    output_file = Path(args.output) if args.output else None

    # Convert
    try:
        code = convert_tdl(tdl_file, robot, output_file)

        if args.print_only:
            print("\n" + "="*60)
            print("Generated Code:")
            print("="*60)
            print(code)
            print("="*60)

        print("\n[DONE] Conversion completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


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
