"""
TDL Motion Planner Integration
Connects TDL parser with motion planning system.
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add parent directory to path for TDL parser import
sys.path.append(str(Path(__file__).parent.parent / "job_converter"))

from tdl_parser import TDLParser, TDLProgram, TDLGoal, TDLCommand
from ik_solver import parse_tdl_pose, convert_tdl_to_meters


class TDLMotionPlanner:
    """Plans motion for TDL commands."""

    def __init__(self, ik_solver, trajectory_planner, tdl_program=None):
        """
        Initialize TDL motion planner.

        Args:
            ik_solver: IK solver instance
            trajectory_planner: Trajectory planner instance
            tdl_program: TDL program (for resolving DEFINE statements)
        """
        self.ik_solver = ik_solver
        self.trajectory_planner = trajectory_planner
        self.current_joints = None
        self.tdl_program = tdl_program

    def plan_tdl_program(self, tdl_program: TDLProgram) -> Dict:
        """
        Plan motion for entire TDL program.

        Args:
            tdl_program: Parsed TDL program

        Returns:
            Dictionary with motion plan for each GOAL
        """
        # Store program for definition resolution
        self.tdl_program = tdl_program

        motion_plan = {
            'goals': [],
            'total_duration': 0.0,
            'total_waypoints': 0,
            'success': True,
            'errors': []
        }

        # Set initial position (home)
        self.current_joints = [0.0] * 6  # Assume 6-DOF

        for goal in tdl_program.goals:
            goal_plan = self._plan_goal(goal)

            if goal_plan is None:
                motion_plan['success'] = False
                motion_plan['errors'].append(f"Failed to plan GOAL: {goal.name}")
                continue

            motion_plan['goals'].append({
                'name': goal.name,
                'trajectories': goal_plan,
                'duration': sum(t.get('duration', 0) for t in goal_plan if t),
                'num_commands': len(goal.commands)
            })

            # Update total statistics
            motion_plan['total_duration'] += sum(t.get('duration', 0) for t in goal_plan if t)
            motion_plan['total_waypoints'] += sum(t.get('num_waypoints', 0) for t in goal_plan if t)

        return motion_plan

    def _plan_goal(self, goal: TDLGoal) -> Optional[List[Dict]]:
        """
        Plan motion for a single GOAL.

        Args:
            goal: TDL goal

        Returns:
            List of trajectory dictionaries, or None if planning fails
        """
        trajectories = []

        for command in goal.commands:
            trajectory = self._plan_command(command)

            if trajectory is None and self._is_motion_command(command):
                print(f"[ERROR] Failed to plan command: {command.command_type}")
                return None

            trajectories.append(trajectory)

            # Update current position if motion command succeeded
            if trajectory and 'waypoints' in trajectory:
                self.current_joints = trajectory['waypoints'][-1]

        return trajectories

    def _plan_command(self, command: TDLCommand) -> Optional[Dict]:
        """
        Plan motion for a single TDL command.

        Args:
            command: TDL command

        Returns:
            Trajectory dictionary or None
        """
        cmd_type = command.command_type
        args = command.args

        # Motion commands
        if cmd_type == "MoveLinear":
            return self._plan_move_linear(args)

        elif cmd_type == "MoveJoint":
            return self._plan_move_joint(args)

        elif cmd_type == "MoveCircular":
            print(f"[WARNING] MoveCircular not yet implemented")
            return None

        # Non-motion commands (I/O, delay, etc.)
        else:
            return {
                'type': 'non_motion',
                'command': cmd_type,
                'args': args,
                'duration': self._estimate_command_duration(command)
            }

    def _resolve_pose(self, pose_str: str) -> str:
        """Resolve pose from DEFINE if needed."""
        if self.tdl_program and pose_str in self.tdl_program.definitions:
            return self.tdl_program.definitions[pose_str]
        return pose_str

    def _plan_move_linear(self, args: Dict) -> Optional[Dict]:
        """Plan MoveLinear command."""
        target_pose_str = args.get('target_pose', '')
        velocity = args.get('velocity', 100)  # mm/s
        acceleration = args.get('acceleration', 50)  # mm/s²

        # Resolve DEFINE reference
        target_pose_str = self._resolve_pose(target_pose_str)

        # Parse target pose
        pose_dict = parse_tdl_pose(target_pose_str)
        if not pose_dict:
            print(f"[ERROR] Failed to parse pose: {target_pose_str}")
            return None

        # Convert to meters and radians
        pose_converted = convert_tdl_to_meters(pose_dict)

        if pose_converted['type'] == 'cartesian':
            # Plan linear trajectory in Cartesian space
            trajectory = self.trajectory_planner.plan_linear_trajectory(
                start_joints=self.current_joints,
                goal_pos=tuple(pose_converted['position']),
                goal_orn=tuple(pose_converted['orientation']),
                ik_solver=self.ik_solver,
                velocity=velocity,
                acceleration=acceleration,
                num_waypoints=50
            )

            if trajectory:
                trajectory['command'] = 'MoveLinear'
                trajectory['target_pose'] = target_pose_str

            return trajectory

        elif pose_converted['type'] == 'joint':
            # If joint pose given for linear move, treat as joint move
            print(f"[WARNING] PosJ given for MoveLinear, using MoveJoint instead")
            return self._plan_move_joint(args)

        return None

    def _plan_move_joint(self, args: Dict) -> Optional[Dict]:
        """Plan MoveJoint command."""
        target_pose_str = args.get('target_pose', '')
        velocity = args.get('velocity', 100)  # deg/s or mm/s
        acceleration = args.get('acceleration', 50)

        # Resolve DEFINE reference
        target_pose_str = self._resolve_pose(target_pose_str)

        # Parse target pose
        pose_dict = parse_tdl_pose(target_pose_str)
        if not pose_dict:
            print(f"[ERROR] Failed to parse pose: {target_pose_str}")
            return None

        # Convert to meters and radians
        pose_converted = convert_tdl_to_meters(pose_dict)

        # Determine goal joints
        if pose_converted['type'] == 'joint':
            goal_joints = pose_converted['joints']

        elif pose_converted['type'] == 'cartesian':
            # Solve IK to get joint configuration
            goal_joints = self.ik_solver.solve_ik_from_euler(
                tuple(pose_converted['position']),
                tuple(pose_converted['orientation']),
                self.current_joints
            )

            if goal_joints is None:
                print(f"[ERROR] IK failed for {target_pose_str}")
                return None
        else:
            return None

        # Plan joint trajectory
        trajectory = self.trajectory_planner.plan_joint_trajectory(
            start_joints=self.current_joints,
            goal_joints=goal_joints,
            velocity=velocity,
            acceleration=acceleration,
            num_waypoints=50
        )

        if trajectory:
            trajectory['command'] = 'MoveJoint'
            trajectory['target_pose'] = target_pose_str

        return trajectory

    def _is_motion_command(self, command: TDLCommand) -> bool:
        """Check if command is a motion command."""
        motion_commands = ['MoveLinear', 'MoveJoint', 'MoveCircular']
        return command.command_type in motion_commands

    def _estimate_command_duration(self, command: TDLCommand) -> float:
        """Estimate duration for non-motion commands."""
        cmd_type = command.command_type
        args = command.args

        if cmd_type == "Delay":
            return args.get('duration_sec', args.get('duration', 0))

        elif cmd_type in ["SetDigitalOutput", "GetDigitalInput"]:
            return 0.01  # 10ms for I/O

        elif cmd_type in ["GraspObject", "ReleaseObject"]:
            return 0.5  # 500ms for gripper

        elif cmd_type in ["ArcOn", "ArcOff"]:
            return 0.1  # 100ms for welding control

        else:
            return 0.0


def load_and_plan_tdl(
    tdl_file_path: str,
    ik_solver,
    trajectory_planner,
    save_report: bool = False
) -> Dict:
    """
    Load TDL file and create motion plan.

    Args:
        tdl_file_path: Path to TDL file
        ik_solver: IK solver instance
        trajectory_planner: Trajectory planner instance
        save_report: Save motion plan report to file

    Returns:
        Motion plan dictionary
    """
    # Parse TDL file
    parser = TDLParser()
    program = parser.parse_file(tdl_file_path)

    print(f"[INFO] Parsed TDL: {len(program.goals)} GOALs")

    # Create motion planner
    motion_planner = TDLMotionPlanner(ik_solver, trajectory_planner)

    # Plan motion
    print("[INFO] Planning motion...")
    motion_plan = motion_planner.plan_tdl_program(program)

    # Print summary
    print("\n" + "="*60)
    print("MOTION PLANNING SUMMARY")
    print("="*60)
    print(f"Status: {'SUCCESS' if motion_plan['success'] else 'FAILED'}")
    print(f"Total Duration: {motion_plan['total_duration']:.2f} seconds")
    print(f"Total Waypoints: {motion_plan['total_waypoints']}")
    print(f"Number of GOALs: {len(motion_plan['goals'])}")

    for goal_plan in motion_plan['goals']:
        print(f"\n  GOAL: {goal_plan['name']}")
        print(f"    Commands: {goal_plan['num_commands']}")
        print(f"    Duration: {goal_plan['duration']:.2f}s")

    if motion_plan['errors']:
        print("\nERRORS:")
        for error in motion_plan['errors']:
            print(f"  - {error}")

    print("="*60)

    # Save report if requested
    if save_report:
        tdl_path = Path(tdl_file_path)
        report_path = tdl_path.with_suffix('.motion_plan.json')

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(motion_plan, f, indent=2)

        print(f"\n[INFO] Motion plan saved to: {report_path}")

    return motion_plan
