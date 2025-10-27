"""
Motion Plan Summary Tool
Show detailed summary of motion plan without GUI.
"""
import json
import sys
from pathlib import Path


def load_motion_plan(json_path):
    """Load motion plan from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def print_motion_summary(motion_plan):
    """Print detailed motion plan summary."""
    print("\n" + "="*70)
    print(" "*20 + "MOTION PLAN ANALYSIS")
    print("="*70)

    print(f"\nStatus: {'SUCCESS' if motion_plan['success'] else 'FAILED'}")
    print(f"Total Duration: {motion_plan['total_duration']:.2f} seconds")
    print(f"Total Waypoints: {motion_plan['total_waypoints']}")
    print(f"Number of GOALs: {len(motion_plan['goals'])}")

    print("\n" + "-"*70)
    print("GOAL-BY-GOAL BREAKDOWN")
    print("-"*70)

    for goal_idx, goal_data in enumerate(motion_plan['goals'], 1):
        print(f"\n[{goal_idx}] GOAL: {goal_data['name']}")
        print(f"    Duration: {goal_data['duration']:.2f}s")
        print(f"    Commands: {goal_data['num_commands']}")
        print(f"    Trajectories: {len(goal_data['trajectories'])}")

        # Show trajectory details
        for traj_idx, traj in enumerate(goal_data['trajectories'], 1):
            if not traj:
                continue

            if 'command' in traj:
                print(f"\n    [{traj_idx}] {traj['command']}")
                if 'target_pose' in traj:
                    print(f"        Target: {traj['target_pose']}")
                if 'duration' in traj:
                    print(f"        Duration: {traj['duration']:.3f}s")
                if 'num_waypoints' in traj:
                    print(f"        Waypoints: {traj['num_waypoints']}")
                if 'type' in traj:
                    print(f"        Type: {traj['type']}")
            elif traj.get('type') == 'non_motion':
                print(f"    [{traj_idx}] {traj.get('command', 'Unknown')}")
                print(f"        Duration: {traj.get('duration', 0):.3f}s")
                if 'args' in traj:
                    print(f"        Args: {traj['args']}")

    if motion_plan['errors']:
        print("\n" + "-"*70)
        print("ERRORS:")
        print("-"*70)
        for error in motion_plan['errors']:
            print(f"  [X] {error}")

    print("\n" + "="*70)
    print("TRAJECTORY STATISTICS")
    print("="*70)

    # Calculate statistics
    total_motion_time = 0
    total_non_motion_time = 0
    motion_commands = 0
    non_motion_commands = 0

    for goal_data in motion_plan['goals']:
        for traj in goal_data['trajectories']:
            if not traj:
                continue
            duration = traj.get('duration', 0)
            if traj.get('type') == 'non_motion':
                total_non_motion_time += duration
                non_motion_commands += 1
            elif 'waypoints' in traj:
                total_motion_time += duration
                motion_commands += 1

    print(f"\nMotion Commands: {motion_commands}")
    print(f"  Total time: {total_motion_time:.2f}s ({total_motion_time/motion_plan['total_duration']*100:.1f}%)")

    print(f"\nNon-Motion Commands: {non_motion_commands}")
    print(f"  Total time: {total_non_motion_time:.2f}s ({total_non_motion_time/motion_plan['total_duration']*100:.1f}%)")

    avg_waypoints = motion_plan['total_waypoints'] / motion_commands if motion_commands > 0 else 0
    print(f"\nAverage waypoints per motion: {avg_waypoints:.1f}")

    print("="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_plan.py <motion_plan.json>")
        print("\nExample:")
        print("  python show_plan.py ../output/task.motion_plan.json")
        sys.exit(1)

    json_path = sys.argv[1]

    # Load motion plan
    print(f"\n[INFO] Loading motion plan from: {json_path}")
    motion_plan = load_motion_plan(json_path)

    # Print summary
    print_motion_summary(motion_plan)
