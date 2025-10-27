"""
Motion Plan Visualizer
Visualize joint trajectories from motion plan JSON file.
"""
import json
import sys
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_motion_plan(json_path):
    """Load motion plan from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def visualize_motion_plan(motion_plan, save_path=None):
    """
    Visualize motion plan as joint angle trajectories.

    Args:
        motion_plan: Motion plan dictionary
        save_path: Optional path to save the figure
    """
    if not motion_plan['success']:
        print("[ERROR] Motion plan failed, cannot visualize")
        return

    num_goals = len(motion_plan['goals'])

    # Create figure with subplots for each GOAL
    fig, axes = plt.subplots(num_goals, 1, figsize=(12, 4 * num_goals))
    if num_goals == 1:
        axes = [axes]

    fig.suptitle('Joint Angle Trajectories', fontsize=16, fontweight='bold')

    for goal_idx, goal_data in enumerate(motion_plan['goals']):
        ax = axes[goal_idx]

        goal_name = goal_data['name']
        trajectories = goal_data['trajectories']

        # Collect all waypoints for this goal
        all_waypoints = []
        time_stamps = []
        current_time = 0.0

        for traj in trajectories:
            if traj and 'waypoints' in traj:
                waypoints = traj['waypoints']
                duration = traj.get('duration', 0)

                # Generate time stamps
                num_waypoints = len(waypoints)
                if num_waypoints > 1:
                    traj_time = np.linspace(current_time, current_time + duration, num_waypoints)
                    time_stamps.extend(traj_time)
                    all_waypoints.extend(waypoints)
                    current_time += duration

        if not all_waypoints:
            ax.text(0.5, 0.5, 'No motion data', ha='center', va='center', fontsize=12)
            ax.set_title(f'GOAL: {goal_name}')
            continue

        # Convert to numpy array
        waypoints_array = np.array(all_waypoints)
        time_array = np.array(time_stamps)

        num_joints = waypoints_array.shape[1]

        # Plot each joint
        colors = plt.cm.tab10(np.linspace(0, 1, num_joints))
        for joint_idx in range(num_joints):
            joint_angles = waypoints_array[:, joint_idx]
            ax.plot(time_array, np.degrees(joint_angles),
                   label=f'Joint {joint_idx + 1}',
                   color=colors[joint_idx],
                   linewidth=2)

        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('Joint Angle (degrees)', fontsize=11)
        ax.set_title(f'GOAL: {goal_name} (Duration: {goal_data["duration"]:.2f}s)', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', ncol=3, fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[INFO] Figure saved to: {save_path}")
    else:
        plt.show()


def print_motion_summary(motion_plan):
    """Print motion plan summary."""
    print("\n" + "="*60)
    print("MOTION PLAN SUMMARY")
    print("="*60)
    print(f"Status: {'SUCCESS' if motion_plan['success'] else 'FAILED'}")
    print(f"Total Duration: {motion_plan['total_duration']:.2f} seconds")
    print(f"Total Waypoints: {motion_plan['total_waypoints']}")
    print(f"Number of GOALs: {len(motion_plan['goals'])}")

    for goal_data in motion_plan['goals']:
        print(f"\n  GOAL: {goal_data['name']}")
        print(f"    Commands: {goal_data['num_commands']}")
        print(f"    Duration: {goal_data['duration']:.2f}s")
        print(f"    Trajectories: {len(goal_data['trajectories'])}")

    if motion_plan['errors']:
        print("\nERRORS:")
        for error in motion_plan['errors']:
            print(f"  - {error}")

    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize_plan.py <motion_plan.json> [--save]")
        print("\nExamples:")
        print("  python visualize_plan.py ../output/task.motion_plan.json")
        print("  python visualize_plan.py ../output/task.motion_plan.json --save")
        sys.exit(1)

    json_path = sys.argv[1]
    save_fig = '--save' in sys.argv

    # Load motion plan
    print(f"[INFO] Loading motion plan from: {json_path}")
    motion_plan = load_motion_plan(json_path)

    # Print summary
    print_motion_summary(motion_plan)

    # Visualize
    save_path = None
    if save_fig:
        save_path = Path(json_path).with_suffix('.trajectory.png')

    print("\n[INFO] Generating visualization...")
    visualize_motion_plan(motion_plan, save_path)

    if not save_fig:
        print("[INFO] Close the plot window to exit")
