"""
Universal Robots UR Script Converter
Converts TDL to Universal Robots UR Script.
"""
from typing import List, Dict
from tdl_parser import TDLProgram, TDLGoal, TDLCommand


class UniversalConverter:
    """Converts TDL to UR Script."""

    def convert(self, program: TDLProgram) -> str:
        """Convert TDL program to UR Script."""
        lines = []

        # Header
        lines.append("# Universal Robots UR Script")
        lines.append("# Generated from TDL")
        lines.append("")

        # Convert each goal to a thread/function
        for goal in program.goals:
            goal_code = self._convert_goal(goal)
            lines.extend(goal_code)
            lines.append("")

        # Main program
        lines.append("# Main program")
        for goal in program.goals:
            lines.append(f"{goal.name}()")

        return "\n".join(lines)

    def _convert_goal(self, goal: TDLGoal) -> List[str]:
        """Convert TDL goal to UR Script function."""
        lines = []

        # Function definition
        lines.append(f"def {goal.name}():")

        if not goal.commands:
            lines.append("  # No commands")
            return lines

        # Convert commands
        for command in goal.commands:
            cmd_line = self._convert_command(command)
            if cmd_line:
                lines.append(f"  {cmd_line}")

        lines.append("end")

        return lines

    def _convert_command(self, command: TDLCommand) -> str:
        """Convert single TDL command to UR Script."""
        cmd_type = command.command_type
        args = command.args

        # Move commands
        if cmd_type == "MoveLinear":
            return self._convert_move_linear(args)
        elif cmd_type == "MoveJoint":
            return self._convert_move_joint(args)
        elif cmd_type == "MoveCircular":
            return self._convert_move_circular(args)

        # I/O commands
        elif cmd_type == "SetDigitalOutput":
            port = args.get("port", 0)
            value = args.get("value", 0)
            # UR uses True/False for digital outputs
            value_str = "True" if value else "False"
            return f"set_digital_out({port}, {value_str})"

        elif cmd_type == "GetDigitalInput":
            port = args.get("port", 0)
            return f"get_digital_in({port})"

        # Time commands
        elif cmd_type == "Delay":
            duration = args.get("duration_sec", args.get("duration", 0))
            return f"sleep({duration})"

        # Welding commands
        elif cmd_type == "ArcOn":
            return "# Arc welding ON - implement with vendor-specific command"

        elif cmd_type == "ArcOff":
            return "# Arc welding OFF - implement with vendor-specific command"

        # Control flow
        elif cmd_type == "End":
            return "# End"

        # Unknown command
        else:
            return f"# TODO: {cmd_type}({args})"

    def _convert_move_linear(self, args: Dict) -> str:
        """Convert MoveLinear to UR Script movel."""
        pose = self._extract_pose(args.get("target_pose", ""))
        velocity = args.get("velocity", 100) / 1000.0  # Convert mm/s to m/s
        acceleration = args.get("acceleration", 50) / 1000.0  # Convert mm/s² to m/s²
        radius = args.get("blending_radius", 0) / 1000.0  # Convert mm to m

        return f"movel({pose}, a={acceleration:.3f}, v={velocity:.3f}, r={radius:.3f})"

    def _convert_move_joint(self, args: Dict) -> str:
        """Convert MoveJoint to UR Script movej."""
        pose = self._extract_pose(args.get("target_pose", ""))
        velocity = args.get("velocity", 100)
        acceleration = args.get("acceleration", 50)

        # UR uses rad/s for joint velocity, m/s for linear
        # Simplified conversion
        velocity_rad = velocity / 100.0  # Simple scaling
        acceleration_rad = acceleration / 100.0

        return f"movej({pose}, a={acceleration_rad:.3f}, v={velocity_rad:.3f})"

    def _convert_move_circular(self, args: Dict) -> str:
        """Convert MoveCircular to UR Script movec."""
        via_pose = self._extract_pose(args.get("via_pose", ""))
        target_pose = self._extract_pose(args.get("target_pose", ""))
        velocity = args.get("velocity", 100) / 1000.0
        acceleration = args.get("acceleration", 50) / 1000.0

        return f"movec({via_pose}, {target_pose}, a={acceleration:.3f}, v={velocity:.3f})"

    def _extract_pose(self, pose_str: str) -> str:
        """Extract and convert pose to UR Script format."""
        if not pose_str:
            return "p[0, 0, 0, 0, 0, 0]"

        # PosX -> p[x, y, z, rx, ry, rz] (meters and radians)
        if pose_str.startswith('PosX('):
            # Extract coordinates
            import re
            match = re.search(r'PosX\((.*?)\)', pose_str)
            if match:
                coords_str = match.group(1)
                coords = [float(c.strip()) for c in coords_str.split(',')]
                # Convert mm to m for position
                coords[0] /= 1000.0
                coords[1] /= 1000.0
                coords[2] /= 1000.0
                # Convert degrees to radians for rotation
                import math
                coords[3] = math.radians(coords[3])
                coords[4] = math.radians(coords[4])
                coords[5] = math.radians(coords[5])
                return f"p[{', '.join(f'{c:.6f}' for c in coords)}]"

        # PosJ -> joint positions (radians)
        elif pose_str.startswith('PosJ('):
            import re
            match = re.search(r'PosJ\((.*?)\)', pose_str)
            if match:
                coords_str = match.group(1)
                coords = [float(c.strip()) for c in coords_str.split(',')]
                # Convert degrees to radians
                import math
                coords = [math.radians(c) for c in coords]
                return f"[{', '.join(f'{c:.6f}' for c in coords)}]"

        # Already in correct format
        if pose_str.startswith('p[') or pose_str.startswith('['):
            return pose_str

        return pose_str


class UniversalJobGenerator:
    """Generates complete Universal Robots job file."""

    def generate(self, program: TDLProgram) -> str:
        """Generate complete UR Script job file."""
        converter = UniversalConverter()

        lines = []

        # File header
        lines.append("# Universal Robots UR Script")
        lines.append("# Auto-generated from TDL")
        lines.append("")

        # Convert program
        ur_script = converter.convert(program)
        lines.append(ur_script)

        return "\n".join(lines)
