"""
TDL Document Analyzer
Analyzes TDL files to extract robot requirements (payload, reach, capabilities)
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class RobotRequirements:
    """Robot requirements extracted from TDL analysis."""
    required_payload_kg: float = 0.0
    required_reach_mm: float = 0.0
    required_dof: int = 6  # Default to 6-DoF
    required_capabilities: List[str] = field(default_factory=list)
    velocity_range: Tuple[float, float] = (0, 0)  # (min, max)
    acceleration_range: Tuple[float, float] = (0, 0)  # (min, max)
    has_welding: bool = False
    has_force_control: bool = False
    has_gripper: bool = False
    total_commands: int = 0
    complexity_score: float = 0.0

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "="*60,
            "Robot Requirements Analysis",
            "="*60,
            f"Required DoF: {self.required_dof}",
            f"Required Payload: {self.required_payload_kg:.2f} kg",
            f"Required Reach: {self.required_reach_mm:.0f} mm ({self.required_reach_mm/1000:.2f} m)",
            f"Velocity Range: {self.velocity_range[0]:.0f} - {self.velocity_range[1]:.0f} mm/s",
            f"Acceleration Range: {self.acceleration_range[0]:.0f} - {self.acceleration_range[1]:.0f} mm/s²",
            f"\nCapabilities:",
            f"  - Gripper Required: {'Yes' if self.has_gripper else 'No'}",
            f"  - Welding Required: {'Yes' if self.has_welding else 'No'}",
            f"  - Force Control Required: {'Yes' if self.has_force_control else 'No'}",
            f"\nComplexity:",
            f"  - Total Commands: {self.total_commands}",
            f"  - Complexity Score: {self.complexity_score:.2f}/10",
            "="*60,
        ]
        return "\n".join(lines)


class TDLAnalyzer:
    """Analyzes TDL documents to extract robot requirements."""

    # Typical object weights (kg) - can be customized
    OBJECT_WEIGHTS = {
        "box": 5.0,
        "small_box": 2.0,
        "large_box": 10.0,
        "part": 1.0,
        "component": 1.5,
        "product": 3.0,
        "tool": 2.0,
        "workpiece": 5.0,
        "default": 5.0,  # Default if unknown
    }

    # Safety margin for payload (add 20% for safety)
    PAYLOAD_SAFETY_MARGIN = 1.2

    def __init__(self):
        """Initialize TDL analyzer."""
        pass

    def analyze_file(self, tdl_file_path: str, metadata_file_path: str = None) -> RobotRequirements:
        """
        Analyze TDL file and extract robot requirements.

        Args:
            tdl_file_path: Path to TDL file
            metadata_file_path: Optional path to JSON metadata file

        Returns:
            RobotRequirements object
        """
        # Read TDL content
        with open(tdl_file_path, 'r', encoding='utf-8') as f:
            tdl_content = f.read()

        # Read metadata if available
        metadata = None
        if metadata_file_path:
            import json
            try:
                with open(metadata_file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass

        return self.analyze_content(tdl_content, metadata)

    def analyze_content(self, tdl_content: str, metadata: Dict = None) -> RobotRequirements:
        """
        Analyze TDL content and extract requirements.

        Args:
            tdl_content: TDL document as string
            metadata: Optional metadata dictionary

        Returns:
            RobotRequirements object
        """
        requirements = RobotRequirements()

        # 1. Extract payload - TDL file takes priority
        payload_from_tdl = self._extract_payload_from_tdl(tdl_content)
        if payload_from_tdl is not None:
            # Use payload from TDL file (already includes any safety margin from generation)
            requirements.required_payload_kg = payload_from_tdl
        elif metadata:
            # Fallback to metadata if TDL doesn't have payload
            objects = metadata.get("objects", [])
            requirements.required_payload_kg = self._estimate_payload(objects)
        else:
            # Last resort: use default
            requirements.required_payload_kg = self.OBJECT_WEIGHTS["default"] * self.PAYLOAD_SAFETY_MARGIN

        # 2. Extract reach from position coordinates
        requirements.required_reach_mm = self._extract_max_reach(tdl_content)

        # 3. Extract velocity and acceleration ranges
        requirements.velocity_range = self._extract_velocity_range(tdl_content)
        requirements.acceleration_range = self._extract_acceleration_range(tdl_content)

        # 4. Detect required capabilities
        requirements.has_gripper = self._has_gripper_operations(tdl_content)
        requirements.has_welding = self._has_welding_operations(tdl_content)
        requirements.has_force_control = self._has_force_control(tdl_content)

        # 5. Extract capability keywords
        requirements.required_capabilities = self._extract_capabilities(tdl_content, metadata)

        # 6. Calculate complexity
        requirements.total_commands = self._count_commands(tdl_content)
        requirements.complexity_score = self._calculate_complexity(tdl_content, requirements)

        return requirements

    def _extract_payload_from_tdl(self, tdl_content: str) -> Optional[float]:
        """
        Extract payload from TDL HEADER section.

        Looks for:
        HEADER
          PAYLOAD_KG: 5.0
        END_HEADER

        Returns:
            Payload in kg, or None if not found
        """
        # Pattern to match PAYLOAD_KG in HEADER section
        payload_pattern = r'PAYLOAD_KG:\s*(\d+\.?\d*)'
        match = re.search(payload_pattern, tdl_content, re.IGNORECASE)

        if match:
            payload = float(match.group(1))
            # Apply safety margin if TDL payload doesn't already include it
            # We assume TDL already has appropriate value, so we don't add margin again
            return payload

        return None

    def _estimate_payload(self, objects: List[str]) -> float:
        """Estimate required payload based on objects."""
        if not objects:
            return self.OBJECT_WEIGHTS["default"] * self.PAYLOAD_SAFETY_MARGIN

        total_weight = 0.0
        for obj in objects:
            obj_lower = obj.lower()
            # Try to match object name to known weights
            weight = None
            for key, value in self.OBJECT_WEIGHTS.items():
                if key in obj_lower:
                    weight = value
                    break
            if weight is None:
                weight = self.OBJECT_WEIGHTS["default"]
            total_weight += weight

        # Apply safety margin
        return total_weight * self.PAYLOAD_SAFETY_MARGIN

    def _extract_max_reach(self, tdl_content: str) -> float:
        """Extract maximum reach required from position coordinates."""
        # Find all PosX coordinates
        posx_pattern = r'PosX\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)'
        matches = re.findall(posx_pattern, tdl_content)

        if not matches:
            return 1000.0  # Default 1000mm if no positions found

        max_distance = 0.0
        for match in matches:
            x, y, z = float(match[0]), float(match[1]), float(match[2])
            # Calculate distance from origin (0, 0, 0)
            distance = (x**2 + y**2 + z**2) ** 0.5
            max_distance = max(max_distance, distance)

        # Add 10% safety margin
        return max_distance * 1.1

    def _extract_velocity_range(self, tdl_content: str) -> Tuple[float, float]:
        """Extract velocity range from move commands."""
        velocity_pattern = r'velocity=(\d+\.?\d*)'
        matches = re.findall(velocity_pattern, tdl_content)

        if not matches:
            return (0, 0)

        velocities = [float(v) for v in matches]
        return (min(velocities), max(velocities))

    def _extract_acceleration_range(self, tdl_content: str) -> Tuple[float, float]:
        """Extract acceleration range from move commands."""
        accel_pattern = r'acceleration=(\d+\.?\d*)'
        matches = re.findall(accel_pattern, tdl_content)

        if not matches:
            return (0, 0)

        accelerations = [float(a) for a in matches]
        return (min(accelerations), max(accelerations))

    def _has_gripper_operations(self, tdl_content: str) -> bool:
        """Check if TDL uses gripper operations."""
        gripper_keywords = [
            'SetDigitalOutput',
            'GraspObject',
            'ReleaseObject',
            'gripper',
            'grasp',
            'release'
        ]
        return any(keyword in tdl_content for keyword in gripper_keywords)

    def _has_welding_operations(self, tdl_content: str) -> bool:
        """Check if TDL uses welding operations."""
        welding_keywords = [
            'ArcOn',
            'ArcOff',
            'SetArcCondition',
            'ConfigureArcWeaving',
            'SpotWeld',
            'weld'
        ]
        return any(keyword in tdl_content for keyword in welding_keywords)

    def _has_force_control(self, tdl_content: str) -> bool:
        """Check if TDL uses force control."""
        force_keywords = [
            'StartCompliance',
            'ReleaseCompliance',
            'SetDesiredForce',
            'force',
            'compliance'
        ]
        return any(keyword in tdl_content for keyword in force_keywords)

    def _extract_capabilities(self, tdl_content: str, metadata: Dict = None) -> List[str]:
        """Extract required capabilities."""
        capabilities = []

        if self._has_gripper_operations(tdl_content):
            capabilities.append("gripper")

        if self._has_welding_operations(tdl_content):
            capabilities.append("welding")

        if self._has_force_control(tdl_content):
            capabilities.append("force_control")

        # Check for specific move types
        if "MoveLinear" in tdl_content:
            capabilities.append("linear_motion")

        if "MoveCircular" in tdl_content:
            capabilities.append("circular_motion")

        if "MoveJoint" in tdl_content:
            capabilities.append("joint_motion")

        # Check metadata for actions
        if metadata:
            actions = metadata.get("actions", [])
            if "pick" in actions or "place" in actions or "transfer" in actions:
                capabilities.append("pick_and_place")
            if "assemble" in actions:
                capabilities.append("assembly")

        return list(set(capabilities))  # Remove duplicates

    def _count_commands(self, tdl_content: str) -> int:
        """Count total number of SPAWN commands."""
        return tdl_content.count("SPAWN")

    def _calculate_complexity(self, tdl_content: str, requirements: RobotRequirements) -> float:
        """Calculate task complexity score (0-10)."""
        score = 0.0

        # Command count (0-3 points)
        cmd_count = requirements.total_commands
        score += min(3.0, cmd_count / 10.0 * 3.0)

        # Capability count (0-3 points)
        cap_count = len(requirements.required_capabilities)
        score += min(3.0, cap_count / 5.0 * 3.0)

        # Special operations (0-2 points)
        if requirements.has_welding:
            score += 1.0
        if requirements.has_force_control:
            score += 1.0

        # Reach requirement (0-2 points)
        if requirements.required_reach_mm > 1500:
            score += 2.0
        elif requirements.required_reach_mm > 1000:
            score += 1.0

        return min(10.0, score)
