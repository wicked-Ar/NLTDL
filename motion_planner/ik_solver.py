"""
Inverse Kinematics Solver using PyBullet
Converts Cartesian poses (PosX) to joint angles (PosJ).
"""
import pybullet as p
import numpy as np
from typing import List, Tuple, Optional
import math


class IKSolver:
    """Inverse Kinematics solver using PyBullet's IK engine."""

    def __init__(self, robot_id: int, end_effector_link_index: int):
        """
        Initialize IK solver.

        Args:
            robot_id: PyBullet robot body ID
            end_effector_link_index: Index of end effector link
        """
        self.robot_id = robot_id
        self.ee_link_index = end_effector_link_index
        self.num_joints = p.getNumJoints(robot_id)

        # Get controllable joints
        self.joint_indices = []
        for i in range(self.num_joints):
            joint_info = p.getJointInfo(robot_id, i)
            if joint_info[2] != p.JOINT_FIXED:  # Not a fixed joint
                self.joint_indices.append(i)

        print(f"[IK] Initialized with {len(self.joint_indices)} controllable joints")

    def solve_ik(
        self,
        target_pos: Tuple[float, float, float],
        target_orn: Optional[Tuple[float, float, float, float]] = None,
        current_joints: Optional[List[float]] = None
    ) -> Optional[List[float]]:
        """
        Solve inverse kinematics for target pose.

        Args:
            target_pos: Target position (x, y, z) in meters
            target_orn: Target orientation as quaternion (x, y, z, w)
            current_joints: Current joint configuration (for closer solution)

        Returns:
            Joint angles in radians, or None if IK fails
        """
        # Default orientation (pointing down)
        if target_orn is None:
            target_orn = p.getQuaternionFromEuler([0, np.pi/2, 0])

        # Set current joint positions if provided
        if current_joints:
            for i, joint_idx in enumerate(self.joint_indices):
                if i < len(current_joints):
                    p.resetJointState(self.robot_id, joint_idx, current_joints[i])

        # Solve IK
        joint_positions = p.calculateInverseKinematics(
            bodyUniqueId=self.robot_id,
            endEffectorLinkIndex=self.ee_link_index,
            targetPosition=target_pos,
            targetOrientation=target_orn,
            maxNumIterations=100,
            residualThreshold=1e-4
        )

        # Extract only controllable joint positions
        result = [joint_positions[i] for i in range(len(self.joint_indices))]

        return result

    def solve_ik_from_euler(
        self,
        target_pos: Tuple[float, float, float],
        target_euler: Tuple[float, float, float],
        current_joints: Optional[List[float]] = None
    ) -> Optional[List[float]]:
        """
        Solve IK with Euler angle orientation (roll, pitch, yaw).

        Args:
            target_pos: Target position (x, y, z) in meters
            target_euler: Target orientation as Euler angles (rx, ry, rz) in radians
            current_joints: Current joint configuration

        Returns:
            Joint angles in radians
        """
        # Convert Euler to quaternion
        target_orn = p.getQuaternionFromEuler(target_euler)
        return self.solve_ik(target_pos, target_orn, current_joints)

    def forward_kinematics(self, joint_angles: List[float]) -> Tuple[List[float], List[float]]:
        """
        Compute forward kinematics.

        Args:
            joint_angles: Joint angles in radians

        Returns:
            Tuple of (position, orientation_euler) in meters and radians
        """
        # Set joint positions
        for i, joint_idx in enumerate(self.joint_indices):
            if i < len(joint_angles):
                p.resetJointState(self.robot_id, joint_idx, joint_angles[i])

        # Get end effector state
        link_state = p.getLinkState(self.robot_id, self.ee_link_index)
        position = list(link_state[0])
        orientation_quat = list(link_state[1])
        orientation_euler = list(p.getEulerFromQuaternion(orientation_quat))

        return position, orientation_euler


def parse_tdl_pose(pose_str: str) -> dict:
    """
    Parse TDL pose string (PosX or PosJ) into structured data.

    Args:
        pose_str: TDL pose string like "PosX(300, 200, 50, 0, 0, 0)"

    Returns:
        Dictionary with pose information
    """
    import re

    # PosX: Cartesian position (x, y, z, rx, ry, rz)
    if pose_str.startswith('PosX('):
        match = re.search(r'PosX\((.*?)\)', pose_str)
        if match:
            coords_str = match.group(1)
            coords = [float(c.strip()) for c in coords_str.split(',')]
            return {
                'type': 'cartesian',
                'position': coords[:3],  # x, y, z in mm
                'orientation': coords[3:6] if len(coords) >= 6 else [0, 0, 0]  # rx, ry, rz in degrees
            }

    # PosJ: Joint angles (j1, j2, j3, j4, j5, j6)
    elif pose_str.startswith('PosJ('):
        match = re.search(r'PosJ\((.*?)\)', pose_str)
        if match:
            coords_str = match.group(1)
            coords = [float(c.strip()) for c in coords_str.split(',')]
            return {
                'type': 'joint',
                'joints': coords  # Joint angles in degrees
            }

    return None


def convert_tdl_to_meters(pose_dict: dict) -> dict:
    """
    Convert TDL pose (mm, degrees) to PyBullet units (meters, radians).

    Args:
        pose_dict: Parsed TDL pose dictionary

    Returns:
        Converted pose dictionary
    """
    if pose_dict['type'] == 'cartesian':
        # Convert mm to meters
        position_m = [p / 1000.0 for p in pose_dict['position']]
        # Convert degrees to radians
        orientation_rad = [math.radians(o) for o in pose_dict['orientation']]

        return {
            'type': 'cartesian',
            'position': position_m,
            'orientation': orientation_rad
        }

    elif pose_dict['type'] == 'joint':
        # Convert degrees to radians
        joints_rad = [math.radians(j) for j in pose_dict['joints']]

        return {
            'type': 'joint',
            'joints': joints_rad
        }

    return pose_dict
