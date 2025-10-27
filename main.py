"""
LLM-based NL2TDL Converter - Main Application
Uses Google Gemini API to understand natural language and generate TDL documents.

Research Focus: LLM-based understanding of user requirements for industrial robotics
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from llm_client import GeminiClient, test_connection
from analyzer import LLMRequirementAnalyzer
from tdl_generator import LLMTDLGenerator


def print_banner():
    """Print application banner."""
    banner = """
===============================================================
                LLM-based NL2TDL Converter
        Natural Language to Task Description Language
              Powered by Google Gemini API
===============================================================
"""
    print(banner)


def setup_api_key(args) -> str:
    """
    Setup and validate API key.

    Args:
        args: Command line arguments

    Returns:
        Valid API key

    Raises:
        SystemExit: If API key is invalid or missing
    """
    # Try to get API key from arguments, environment, or config file
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")

    # Try to read from config file if not found
    if not api_key:
        config_file = Path(__file__).parent / "config.txt"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == "GEMINI_API_KEY":
                                    api_key = value.strip()
                                    break
                            else:
                                api_key = line
                                break
            except Exception as e:
                print(f"[WARNING]  Warning: Failed to read config file: {e}")

    if not api_key:
        print("\n[ERROR] Gemini API key is required!")
        print("\nPlease provide your API key in one of these ways:")
        print("  1. Command line: --api-key YOUR_KEY")
        print("  2. Environment variable: set GEMINI_API_KEY=YOUR_KEY")
        print("  3. Config file: Create config.txt with 'GEMINI_API_KEY=YOUR_KEY'")
        print("\nGet your API key from: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    # Test connection
    print("\n[INFO] Testing API connection...")
    if not test_connection(api_key):
        print("[ERROR] API connection test failed!")
        print("Please check your API key and internet connection.")
        sys.exit(1)

    print("[OK] API connection successful")
    return api_key


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="LLM-based Natural Language to TDL Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -r "박스를 A에서 B로 옮겨줘"
  python main.py -r "Pick box from A to B" -o output.tdl
  python main.py -r "용접 작업 수행" --api-key YOUR_API_KEY
  python main.py -r "조립하기" --interactive
  python main.py -r "이동" --explain

Get your Gemini API key from: https://aistudio.google.com/app/apikey
        """
    )

    parser.add_argument(
        "-r", "--requirement",
        type=str,
        required=True,
        help="Natural language requirement (Korean or English)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google Gemini API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output TDL file path (default: auto-generated with timestamp)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for TDL files (default: output)"
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print TDL to console without saving"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode to verify and correct LLM analysis"
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Generate human-readable explanation of the TDL document"
    )
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip TDL validation checks"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Setup API key
    api_key = setup_api_key(args)

    print("\n" + "="*60)
    print("STEP 1: Analyzing Natural Language Requirement")
    print("="*60)
    print(f"Input: {args.requirement}")

    # Step 1: Analyze requirement using LLM
    try:
        analyzer = LLMRequirementAnalyzer(api_key)
        analysis = analyzer.analyze(args.requirement)

        print("\n" + analysis.summary())

        # Interactive verification
        if args.interactive:
            analysis = analyzer.interactive_correction(analysis)

        # Validate analysis
        if not analyzer.validate_analysis(analysis):
            print("\n[WARNING]  Warning: Analysis may be incomplete!")
            if not args.interactive:
                print("Consider using --interactive mode to verify results.")

    except Exception as e:
        print(f"\n[ERROR] Error during requirement analysis: {e}")
        sys.exit(1)

    print("\n" + "="*60)
    print("STEP 2: Generating TDL Document with LLM")
    print("="*60)

    # Step 2: Generate TDL using LLM
    try:
        generator = LLMTDLGenerator(api_key)

        if args.no_validation:
            tdl_content = generator.generate(analysis)
            tdl_content = generator.post_process_tdl(tdl_content)
        else:
            tdl_content = generator.generate_with_validation(analysis)

        print(f"\n[OK] TDL document generated ({len(tdl_content)} characters)")

    except Exception as e:
        print(f"\n[ERROR] Error during TDL generation: {e}")
        sys.exit(1)

    # Step 3: Output
    print("\n" + "="*60)
    print("STEP 3: Output")
    print("="*60)

    if args.print_only:
        print("\n[DOCUMENT] Generated TDL Document:")
        print("-" * 60)
        print(tdl_content)
        print("-" * 60)
    else:
        # Determine output path
        if args.output:
            output_path = Path(args.output_dir) / args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            task_name = "_".join(analysis.actions[:2]) if analysis.actions else "task"
            filename = f"tdl_{task_name}_{timestamp}.tdl"
            output_path = Path(args.output_dir) / filename

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save TDL file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tdl_content)

            print(f"\n[OK] TDL file saved successfully!")
            print(f"[FILE] Output file: {output_path.absolute()}")
            print(f"[SIZE] File size: {output_path.stat().st_size} bytes")

            # Also save analysis metadata
            metadata_path = output_path.with_suffix('.json')
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(analysis.to_dict(), f, ensure_ascii=False, indent=2)

            print(f"[INFO] Metadata saved: {metadata_path.absolute()}")

        except Exception as e:
            print(f"\n[ERROR] Error saving file: {e}")
            sys.exit(1)

    # Optional: Generate explanation
    if args.explain:
        print("\n" + "="*60)
        print("TDL Document Explanation")
        print("="*60)

        try:
            explanation = generator.explain_tdl(tdl_content)
            print(f"\n{explanation}")

            # Save explanation if saving to file
            if not args.print_only:
                explain_path = output_path.with_suffix('.txt')
                with open(explain_path, 'w', encoding='utf-8') as f:
                    f.write(f"TDL Document Explanation\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Original Request: {args.requirement}\n")
                    f.write("="*60 + "\n\n")
                    f.write(explanation)

                print(f"\n[EXPLAIN] Explanation saved: {explain_path.absolute()}")

        except Exception as e:
            print(f"\n[WARNING]  Warning: Could not generate explanation: {e}")

    print("\n" + "="*60)
    print("[DONE] Conversion Completed Successfully!")
    print("="*60)
    print("\n[RESEARCH] Research Note: This system uses LLM to understand user requirements")
    print("   and generate industrial robot task descriptions automatically.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING]  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
