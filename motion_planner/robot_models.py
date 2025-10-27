"""
Robot Models and URDF Management
Provides simplified robot models for motion planning when URDF files are not available.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional


class RobotModel:
    """Base class for robot kinematic models."""

    def __init__(self, name: str, manufacturer: str):
        self.name = name
        self.manufacturer = manufacturer
        self.dof = 6  # Default 6-DOF
        self.joint_limits = []  # [(min, max), ...]
        self.home_position = []

    def get_joint_limits(self) -> List[Tuple[float, float]]:
        """Get joint limits in radians."""
        return self.joint_limits

    def get_home_position(self) -> List[float]:
        """Get home position joint angles."""
        return self.home_position


class DoosanH2017Model(RobotModel):
    """Doosan H2017 robot model (20kg payload, 1.7m reach)."""

    def __init__(self):
        super().__init__("H2017", "Doosan")
        self.dof = 6

        # Joint limits in radians (approximate)
        self.joint_limits = [
            (-np.pi, np.pi),      # Joint 1
            (-np.pi, np.pi),      # Joint 2
            (-np.pi, np.pi),      # Joint 3
            (-np.pi, np.pi),      # Joint 4
            (-np.pi, np.pi),      # Joint 5
            (-np.pi, np.pi),      # Joint 6
        ]

        # Home position (all zeros)
        self.home_position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # DH parameters (approximate for H2017)
        # [a, alpha, d, theta_offset]
        self.dh_params = [
            [0, np.pi/2, 0.151, 0],
            [0.409, 0, 0, 0],
            [0.367, 0, 0, 0],
            [0, np.pi/2, 0.124, 0],
            [0, -np.pi/2, 0.124, 0],
            [0, 0, 0.126, 0]
        ]

        self.max_reach = 1.7  # meters


class UniversalUR10eModel(RobotModel):
    """Universal Robots UR10e model (12.5kg payload, 1.3m reach)."""

    def __init__(self):
        super().__init__("UR10e", "Universal Robots")
        self.dof = 6

        # Joint limits in radians (UR10e specs)
        self.joint_limits = [
            (-2*np.pi, 2*np.pi),  # Joint 1: ±360°
            (-2*np.pi, 2*np.pi),  # Joint 2: ±360°
            (-2*np.pi, 2*np.pi),  # Joint 3: ±360°
            (-2*np.pi, 2*np.pi),  # Joint 4: ±360°
            (-2*np.pi, 2*np.pi),  # Joint 5: ±360°
            (-2*np.pi, 2*np.pi),  # Joint 6: ±360°
        ]

        self.home_position = [0.0, -np.pi/2, 0.0, -np.pi/2, 0.0, 0.0]

        # DH parameters for UR10e
        self.dh_params = [
            [0, np.pi/2, 0.1807, 0],
            [-0.6127, 0, 0, 0],
            [-0.57155, 0, 0, 0],
            [0, np.pi/2, 0.17415, 0],
            [0, -np.pi/2, 0.11985, 0],
            [0, 0, 0.11655, 0]
        ]

        self.max_reach = 1.3  # meters


class GenericRobotModel(RobotModel):
    """Generic 6-DOF robot model for simulation."""

    def __init__(self, reach_m: float = 1.0, payload_kg: float = 10.0):
        super().__init__("Generic6DOF", "Generic")
        self.dof = 6
        self.max_reach = reach_m
        self.payload = payload_kg

        # Generic joint limits
        self.joint_limits = [
            (-np.pi, np.pi),
            (-np.pi, np.pi),
            (-np.pi, np.pi),
            (-np.pi, np.pi),
            (-np.pi, np.pi),
            (-np.pi, np.pi),
        ]

        self.home_position = [0.0, 0.0, np.pi/2, 0.0, np.pi/2, 0.0]

        # Simplified DH parameters based on reach
        link_length = reach_m / 3.0
        self.dh_params = [
            [0, np.pi/2, link_length * 0.3, 0],
            [link_length, 0, 0, 0],
            [link_length, 0, 0, 0],
            [0, np.pi/2, link_length * 0.3, 0],
            [0, -np.pi/2, link_length * 0.2, 0],
            [0, 0, link_length * 0.2, 0]
        ]


def get_robot_model(manufacturer: str, model: str) -> RobotModel:
    """
    Get robot model by manufacturer and model name.

    Args:
        manufacturer: Robot manufacturer (doosan, universal, etc.)
        model: Robot model name

    Returns:
        RobotModel instance
    """
    manufacturer = manufacturer.lower()
    model = model.lower()

    if manufacturer == "doosan":
        if "h2017" in model or "h-2017" in model:
            return DoosanH2017Model()
    elif manufacturer == "universal":
        if "ur10e" in model:
            return UniversalUR10eModel()

    # Default to generic model
    print(f"[WARNING] No specific model for {manufacturer} {model}, using generic model")
    return GenericRobotModel()


def create_simple_urdf(robot_model: RobotModel, output_path: str):
    """
    Create a simplified URDF file for PyBullet simulation.

    Args:
        robot_model: Robot model
        output_path: Path to save URDF file
    """
    urdf_content = f"""<?xml version="1.0"?>
<robot name="{robot_model.name}">

  <!-- Base Link -->
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder radius="0.1" length="0.1"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.1" length="0.1"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="5"/>
      <inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/>
    </inertial>
  </link>

"""

    # Generate links and joints based on DH parameters
    for i in range(robot_model.dof):
        link_name = f"link_{i+1}"
        joint_name = f"joint_{i+1}"
        prev_link = "base_link" if i == 0 else f"link_{i}"

        # Simplified link (cylinder)
        link_length = 0.3 if i < robot_model.dof - 1 else 0.15

        urdf_content += f"""  <!-- Link {i+1} -->
  <link name="{link_name}">
    <visual>
      <origin xyz="0 0 {link_length/2}" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="0.05" length="{link_length}"/>
      </geometry>
      <material name="blue">
        <color rgba="0.2 0.4 0.8 1"/>
      </material>
    </visual>
    <collision>
      <origin xyz="0 0 {link_length/2}" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="0.05" length="{link_length}"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="1"/>
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/>
    </inertial>
  </link>

  <!-- Joint {i+1} -->
  <joint name="{joint_name}" type="revolute">
    <parent link="{prev_link}"/>
    <child link="{link_name}"/>
    <origin xyz="0 0 {link_length}" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="{robot_model.joint_limits[i][0]}" upper="{robot_model.joint_limits[i][1]}" effort="100" velocity="2.0"/>
  </joint>

"""

    # End effector
    urdf_content += f"""  <!-- End Effector -->
  <link name="ee_link">
    <visual>
      <geometry>
        <box size="0.08 0.08 0.04"/>
      </geometry>
      <material name="red">
        <color rgba="0.8 0.2 0.2 1"/>
      </material>
    </visual>
  </link>

  <joint name="ee_joint" type="fixed">
    <parent link="link_{robot_model.dof}"/>
    <child link="ee_link"/>
    <origin xyz="0 0 0.15" rpy="0 0 0"/>
  </joint>

</robot>
"""

    with open(output_path, 'w') as f:
        f.write(urdf_content)

    print(f"[INFO] Generated URDF: {output_path}")
