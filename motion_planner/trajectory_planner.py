"""
Trajectory Planner with Collision Detection
Plans smooth, collision-free trajectories between waypoints.
"""
import pybullet as p
import numpy as np
from typing import List, Tuple, Optional, Dict
import math


class TrajectoryPlanner:
    """Plans collision-free trajectories using interpolation and collision checking."""

    def __init__(self, robot_id: int, check_collisions: bool = True):
        """
        Initialize trajectory planner.

        Args:
            robot_id: PyBullet robot body ID
            check_collisions: Enable collision checking
        """
        self.robot_id = robot_id
        self.check_collisions = check_collisions
        self.num_joints = p.getNumJoints(robot_id)

        # Get joint indices
        self.joint_indices = []
        self.joint_limits = []

        for i in range(self.num_joints):
            joint_info = p.getJointInfo(robot_id, i)
            if joint_info[2] != p.JOINT_FIXED:
                self.joint_indices.append(i)
                # Store joint limits
                lower_limit = joint_info[8]
                upper_limit = joint_info[9]
                self.joint_limits.append((lower_limit, upper_limit))

        print(f"[Trajectory] Initialized with {len(self.joint_indices)} joints")
        print(f"[Trajectory] Collision checking: {check_collisions}")

    def plan_joint_trajectory(
        self,
        start_joints: List[float],
        goal_joints: List[float],
        velocity: float = 100.0,
        acceleration: float = 50.0,
        num_waypoints: int = 50
    ) -> Optional[Dict]:
        """
        Plan a joint-space trajectory from start to goal.

        Args:
            start_joints: Starting joint configuration (radians)
            goal_joints: Goal joint configuration (radians)
            velocity: Desired velocity (mm/s or deg/s - used for timing)
            acceleration: Desired acceleration (mm/s² or deg/s² - used for timing)
            num_waypoints: Number of waypoints in trajectory

        Returns:
            Dictionary with trajectory info or None if planning fails
        """
        # Validate joint limits
        if not self._check_joint_limits(goal_joints):
            print("[ERROR] Goal joints exceed joint limits")
            return None

        # Generate interpolated waypoints
        waypoints = self._interpolate_joint_path(start_joints, goal_joints, num_waypoints)

        # Check collisions if enabled
        if self.check_collisions:
            for i, waypoint in enumerate(waypoints):
                if self._is_in_collision(waypoint):
                    print(f"[ERROR] Collision detected at waypoint {i}/{len(waypoints)}")
                    return None

        # Calculate trajectory timing
        max_joint_diff = max(abs(g - s) for g, s in zip(goal_joints, start_joints))
        duration = self._calculate_duration(max_joint_diff, velocity, acceleration)

        return {
            'waypoints': waypoints,
            'duration': duration,
            'num_waypoints': len(waypoints),
            'type': 'joint'
        }

    def plan_linear_trajectory(
        self,
        start_joints: List[float],
        goal_pos: Tuple[float, float, float],
        goal_orn: Tuple[float, float, float],
        ik_solver,
        velocity: float = 100.0,
        acceleration: float = 50.0,
        num_waypoints: int = 50
    ) -> Optional[Dict]:
        """
        Plan a Cartesian linear trajectory.

        Args:
            start_joints: Starting joint configuration
            goal_pos: Goal position (x, y, z) in meters
            goal_orn: Goal orientation (rx, ry, rz) in radians
            ik_solver: IK solver instance
            velocity: Linear velocity (mm/s)
            acceleration: Linear acceleration (mm/s²)
            num_waypoints: Number of waypoints

        Returns:
            Dictionary with trajectory info or None if planning fails
        """
        # Get start Cartesian position
        start_pos, start_euler = ik_solver.forward_kinematics(start_joints)

        # Interpolate Cartesian path
        cartesian_waypoints = self._interpolate_cartesian_path(
            start_pos, goal_pos, num_waypoints
        )

        # Interpolate orientations
        orientation_waypoints = self._interpolate_cartesian_path(
            start_euler, goal_orn, num_waypoints
        )

        # Convert each Cartesian waypoint to joint configuration
        joint_waypoints = []
        current_joints = start_joints

        for cart_pos, cart_orn in zip(cartesian_waypoints, orientation_waypoints):
            # Solve IK
            joint_solution = ik_solver.solve_ik_from_euler(
                tuple(cart_pos),
                tuple(cart_orn),
                current_joints
            )

            if joint_solution is None:
                print(f"[ERROR] IK failed for waypoint at {cart_pos}")
                return None

            # Check joint limits
            if not self._check_joint_limits(joint_solution):
                print(f"[ERROR] Joint limits exceeded at {cart_pos}")
                return None

            # Check collision
            if self.check_collisions and self._is_in_collision(joint_solution):
                print(f"[ERROR] Collision at {cart_pos}")
                return None

            joint_waypoints.append(joint_solution)
            current_joints = joint_solution

        # Calculate duration based on Cartesian distance
        distance = np.linalg.norm(np.array(goal_pos) - np.array(start_pos))
        duration = self._calculate_duration(distance * 1000, velocity, acceleration)  # Convert to mm

        return {
            'waypoints': joint_waypoints,
            'duration': duration,
            'num_waypoints': len(joint_waypoints),
            'type': 'linear',
            'cartesian_path': cartesian_waypoints
        }

    def _interpolate_joint_path(
        self,
        start: List[float],
        goal: List[float],
        num_points: int
    ) -> List[List[float]]:
        """Linear interpolation in joint space."""
        waypoints = []
        for i in range(num_points):
            alpha = i / (num_points - 1) if num_points > 1 else 1.0
            waypoint = [
                s + alpha * (g - s)
                for s, g in zip(start, goal)
            ]
            waypoints.append(waypoint)
        return waypoints

    def _interpolate_cartesian_path(
        self,
        start: List[float],
        goal: List[float],
        num_points: int
    ) -> List[List[float]]:
        """Linear interpolation in Cartesian space."""
        waypoints = []
        for i in range(num_points):
            alpha = i / (num_points - 1) if num_points > 1 else 1.0
            waypoint = [
                s + alpha * (g - s)
                for s, g in zip(start, goal)
            ]
            waypoints.append(waypoint)
        return waypoints

    def _check_joint_limits(self, joints: List[float]) -> bool:
        """Check if joint configuration is within limits."""
        for i, (joint_val, (lower, upper)) in enumerate(zip(joints, self.joint_limits)):
            if joint_val < lower or joint_val > upper:
                print(f"[WARNING] Joint {i} value {joint_val:.3f} outside limits [{lower:.3f}, {upper:.3f}]")
                return False
        return True

    def _is_in_collision(self, joints: List[float]) -> bool:
        """
        Check if a joint configuration results in collision.

        Args:
            joints: Joint configuration to check

        Returns:
            True if in collision, False otherwise
        """
        # Set robot to test configuration
        for i, joint_idx in enumerate(self.joint_indices):
            if i < len(joints):
                p.resetJointState(self.robot_id, joint_idx, joints[i])

        # Perform collision detection
        p.performCollisionDetection()

        # Check for contacts
        contact_points = p.getContactPoints(bodyA=self.robot_id)

        # Filter self-collisions (adjacent links are OK)
        for contact in contact_points:
            link_a = contact[3]
            link_b = contact[4]

            # Skip contacts with ground plane or self
            if link_a == -1 or link_b == -1:
                continue

            # Skip adjacent links (they naturally touch)
            if abs(link_a - link_b) <= 1:
                continue

            # Collision detected
            return True

        return False

    def _calculate_duration(
        self,
        distance: float,
        velocity: float,
        acceleration: float
    ) -> float:
        """
        Calculate trajectory duration using trapezoidal velocity profile.

        Args:
            distance: Total distance (mm or radians)
            velocity: Max velocity (mm/s or rad/s)
            acceleration: Acceleration (mm/s² or rad/s²)

        Returns:
            Duration in seconds
        """
        # Time to accelerate to max velocity
        t_accel = velocity / acceleration

        # Distance covered during acceleration
        d_accel = 0.5 * acceleration * t_accel**2

        # Check if we reach max velocity
        if 2 * d_accel < distance:
            # Trapezoidal profile (accel, cruise, decel)
            d_cruise = distance - 2 * d_accel
            t_cruise = d_cruise / velocity
            total_time = 2 * t_accel + t_cruise
        else:
            # Triangular profile (accel, decel only)
            t_accel = math.sqrt(distance / acceleration)
            total_time = 2 * t_accel

        return total_time

    def smooth_trajectory(
        self,
        waypoints: List[List[float]],
        smoothing_factor: float = 0.5
    ) -> List[List[float]]:
        """
        Apply smoothing to trajectory waypoints.

        Args:
            waypoints: Original waypoints
            smoothing_factor: Smoothing strength (0-1)

        Returns:
            Smoothed waypoints
        """
        if len(waypoints) < 3:
            return waypoints

        smoothed = [waypoints[0]]  # Keep first waypoint

        for i in range(1, len(waypoints) - 1):
            prev = np.array(waypoints[i - 1])
            curr = np.array(waypoints[i])
            next_wp = np.array(waypoints[i + 1])

            # Average with neighbors
            smoothed_point = (
                (1 - smoothing_factor) * curr +
                smoothing_factor * 0.5 * (prev + next_wp)
            )

            smoothed.append(smoothed_point.tolist())

        smoothed.append(waypoints[-1])  # Keep last waypoint

        return smoothed
