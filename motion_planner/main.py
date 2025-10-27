"""
Motion Planner - PyBullet-based Path/Motion Planning
Plans collision-free trajectories for TDL tasks using PyBullet physics simulation.

Usage:
    python main.py input.tdl --robot doosan
    python main.py input.tdl --auto  # Auto-detect from robot_selector
    python main.py input.tdl --robot universal --visualize
"""
import argparse
import sys
import os
from pathlib import Path
import json

# PyBullet imports
import pybullet as p
import pybullet_data

# Local imports
from robot_models import get_robot_model, create_simple_urdf
from ik_solver import IKSolver
from trajectory_planner import TrajectoryPlanner
from tdl_motion_planner import load_and_plan_tdl


def print_banner():
    """Print application banner."""
    banner = """
===============================================================
          Motion Planner - PyBullet Path Planning
               Collision-Free Trajectory Generation
===============================================================
"""
    print(banner)


def detect_robot_from_report(tdl_file_path: Path) -> tuple:
    """
    Detect recommended robot from robot_selector report.

    Args:
        tdl_file_path: Path to TDL file

    Returns:
        Tuple of (manufacturer, model) or (None, None)
    """
    report_file = tdl_file_path.with_suffix('.robot_report.json')

    if not report_file.exists():
        return None, None

    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        matches = report.get('matches', [])
        if matches:
            best_robot = matches[0]['robot']
            manufacturer = best_robot.get('manufacturer', '').lower()
            model = best_robot.get('model', '').lower()
            return manufacturer, model

    except Exception as e:
        print(f"[WARNING] Failed to read robot report: {e}")

    return None, None


def setup_pybullet_simulation(robot_model, gui: bool = False):
    """
    Setup PyBullet simulation environment.

    Args:
        robot_model: Robot model instance
        gui: Enable GUI visualization

    Returns:
        Tuple of (physics_client_id, robot_id, end_effector_link_index)
    """
    # Connect to PyBullet
    if gui:
        client_id = p.connect(p.GUI)
        p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)  # Hide GUI panels
    else:
        client_id = p.connect(p.DIRECT)

    # Set additional search path for PyBullet data
    p.setAdditionalSearchPath(pybullet_data.getDataPath())

    # Set gravity
    p.setGravity(0, 0, -9.81)

    # Load ground plane
    plane_id = p.loadURDF("plane.urdf")

    # Create robot URDF
    urdf_path = Path(__file__).parent / f"temp_{robot_model.name}.urdf"
    create_simple_urdf(robot_model, str(urdf_path))

    # Load robot
    robot_start_pos = [0, 0, 0]
    robot_start_orientation = p.getQuaternionFromEuler([0, 0, 0])

    robot_id = p.loadURDF(
        str(urdf_path),
        robot_start_pos,
        robot_start_orientation,
        useFixedBase=True
    )

    # Find end effector link
    num_joints = p.getNumJoints(robot_id)
    ee_link_index = num_joints - 1  # Last link is end effector

    print(f"[Simulation] Loaded robot: {robot_model.name}")
    print(f"[Simulation] Number of joints: {num_joints}")
    print(f"[Simulation] End effector link: {ee_link_index}")

    return client_id, robot_id, ee_link_index


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Motion Planner - PyBullet-based trajectory planning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plan motion for Doosan robot
  python main.py task.tdl --robot doosan

  # Auto-detect robot from robot_selector report
  python main.py task.tdl --auto

  # Enable visualization
  python main.py task.tdl --robot universal --visualize

  # Disable collision checking (faster)
  python main.py task.tdl --robot doosan --no-collision-check

  # Save motion plan to file
  python main.py task.tdl --robot doosan --save-plan

Supported Robots:
  - doosan    : Doosan Robotics (H2017, etc.)
  - universal : Universal Robots (UR10e, etc.)
        """
    )

    parser.add_argument(
        "tdl_file",
        type=str,
        help="Path to TDL file"
    )
    parser.add_argument(
        "--robot",
        type=str,
        choices=["doosan", "universal"],
        help="Target robot manufacturer"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific robot model (default: manufacturer default)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect robot from robot_selector report"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Enable PyBullet GUI visualization"
    )
    parser.add_argument(
        "--no-collision-check",
        action="store_true",
        help="Disable collision checking (faster)"
    )
    parser.add_argument(
        "--save-plan",
        action="store_true",
        help="Save motion plan to JSON file"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Validate TDL file
    tdl_file = Path(args.tdl_file)
    if not tdl_file.exists():
        print(f"[ERROR] TDL file not found: {tdl_file}")
        sys.exit(1)

    # Determine robot
    manufacturer = args.robot
    model = args.model

    if args.auto:
        print("[INFO] Auto-detecting robot from report...")
        detected_manufacturer, detected_model = detect_robot_from_report(tdl_file)

        if detected_manufacturer:
            manufacturer = detected_manufacturer
            model = detected_model or manufacturer  # Use manufacturer as model if not specified
            print(f"[OK] Detected robot: {manufacturer.upper()} {model}")
        else:
            print("[WARNING] Could not auto-detect robot")
            if not manufacturer:
                print("[ERROR] Please specify --robot manually")
                sys.exit(1)

    if not manufacturer:
        print("[ERROR] Robot not specified!")
        print("Use --robot <manufacturer> or --auto")
        sys.exit(1)

    # Get robot model
    model = model or manufacturer
    robot_model = get_robot_model(manufacturer, model)

    print(f"\n[INFO] Using robot: {robot_model.manufacturer} {robot_model.name}")
    print(f"[INFO] DOF: {robot_model.dof}")
    print(f"[INFO] Max Reach: {robot_model.max_reach}m")

    # Setup PyBullet simulation
    print(f"\n[INFO] Setting up simulation...")
    client_id, robot_id, ee_link_index = setup_pybullet_simulation(
        robot_model,
        gui=args.visualize
    )

    try:
        # Initialize IK solver
        print(f"\n[INFO] Initializing IK solver...")
        ik_solver = IKSolver(robot_id, ee_link_index)

        # Initialize trajectory planner
        print(f"[INFO] Initializing trajectory planner...")
        check_collisions = not args.no_collision_check
        trajectory_planner = TrajectoryPlanner(robot_id, check_collisions=check_collisions)

        # Load TDL and plan motion
        print(f"\n[INFO] Loading TDL file: {tdl_file.name}")
        motion_plan = load_and_plan_tdl(
            str(tdl_file),
            ik_solver,
            trajectory_planner,
            save_report=args.save_plan
        )

        # Success message
        if motion_plan['success']:
            print(f"\n[DONE] Motion planning completed successfully!")
            print(f"[INFO] Total execution time: {motion_plan['total_duration']:.2f} seconds")
            print(f"[INFO] Total waypoints: {motion_plan['total_waypoints']}")
        else:
            print(f"\n[ERROR] Motion planning failed!")
            sys.exit(1)

        # Keep GUI open if visualization enabled
        if args.visualize:
            print("\n[INFO] Visualization active. Press Ctrl+C to exit.")
            try:
                while True:
                    p.stepSimulation()
            except KeyboardInterrupt:
                print("\n[INFO] Shutting down...")

    finally:
        # Disconnect PyBullet
        p.disconnect()

        # Clean up temporary URDF
        urdf_path = Path(__file__).parent / f"temp_{robot_model.name}.urdf"
        if urdf_path.exists():
            urdf_path.unlink()


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
