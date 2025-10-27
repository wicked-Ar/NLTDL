"""
Doosan DRL (Doosan Robotics Language) Converter
Converts TDL to Doosan DRL (Python-based) code.
"""
from typing import List, Dict
from tdl_parser import TDLProgram, TDLGoal, TDLCommand


class DoosanConverter:
    """Converts TDL to Doosan DRL."""

    def __init__(self):
        """Initialize converter."""
        self.indent_level = 0

    def convert(self, program: TDLProgram) -> str:
        """Convert TDL program to Doosan DRL."""
        lines = []

        # Header
        lines.append("# Doosan DRL Script")
        lines.append("# Generated from TDL")
        lines.append("")

        # Convert each goal
        for goal in program.goals:
            goal_code = self._convert_goal(goal)
            lines.extend(goal_code)
            lines.append("")

        return "\n".join(lines)

    def _convert_goal(self, goal: TDLGoal) -> List[str]:
        """Convert TDL goal to DRL function."""
        lines = []

        # Function definition
        lines.append(f"def {goal.name}():")

        if not goal.commands:
            lines.append("    pass")
            return lines

        # Convert commands
        for command in goal.commands:
            cmd_line = self._convert_command(command)
            if cmd_line:
                lines.append(f"    {cmd_line}")

        return lines

    def _convert_command(self, command: TDLCommand) -> str:
        """Convert single TDL command to DRL."""
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
            return f"set_digital_output({port}, {value})"

        elif cmd_type == "GetDigitalInput":
            port = args.get("port", 0)
            return f"get_digital_input({port})"

        # Time commands
        elif cmd_type == "Delay":
            duration = args.get("duration_sec", args.get("duration", 0))
            return f"wait({duration})"

        # Welding commands
        elif cmd_type == "ArcOn":
            return "# Arc welding ON - implement with vendor-specific command"

        elif cmd_type == "ArcOff":
            return "# Arc welding OFF - implement with vendor-specific command"

        # Control flow
        elif cmd_type == "End":
            return "return"

        # Unknown command
        else:
            return f"# TODO: {cmd_type}({args})"

    def _convert_move_linear(self, args: Dict) -> str:
        """Convert MoveLinear to DRL movel."""
        pose = self._extract_pose(args.get("target_pose", ""))
        velocity = args.get("velocity", 100)
        acceleration = args.get("acceleration", 50)
        radius = args.get("blending_radius", 0)

        return f"movel({pose}, v={velocity}, a={acceleration}, radius={radius})"

    def _convert_move_joint(self, args: Dict) -> str:
        """Convert MoveJoint to DRL movej."""
        pose = self._extract_pose(args.get("target_pose", ""))
        velocity = args.get("velocity", 100)
        acceleration = args.get("acceleration", 50)
        radius = args.get("blending_radius", 0)

        return f"movej({pose}, v={velocity}, a={acceleration}, radius={radius})"

    def _convert_move_circular(self, args: Dict) -> str:
        """Convert MoveCircular to DRL movec."""
        via_pose = self._extract_pose(args.get("via_pose", ""))
        target_pose = self._extract_pose(args.get("target_pose", ""))
        velocity = args.get("velocity", 100)
        acceleration = args.get("acceleration", 50)

        return f"movec({via_pose}, {target_pose}, v={velocity}, a={acceleration})"

    def _extract_pose(self, pose_str: str) -> str:
        """Extract pose from TDL format."""
        if not pose_str:
            return "posx(0, 0, 0, 0, 0, 0)"

        # If already in correct format, return as-is
        if pose_str.startswith('posx(') or pose_str.startswith('posj('):
            return pose_str.lower()

        # If tuple format, convert
        if pose_str.startswith('(') and pose_str.endswith(')'):
            # Extract numbers
            coords = pose_str.strip('()').split(',')
            coords = [c.strip() for c in coords]
            return f"posx({', '.join(coords)})"

        return pose_str


class DoosanJobGenerator:
    """Generates complete Doosan job file."""

    def generate(self, program: TDLProgram) -> str:
        """Generate complete DRL job file."""
        converter = DoosanConverter()

        lines = []

        # File header
        lines.append("#!/usr/bin/env python")
        lines.append("# -*- coding: utf-8 -*-")
        lines.append("")
        lines.append("# Doosan Robot Job File")
        lines.append("# Auto-generated from TDL")
        lines.append("")

        # Convert program
        drl_code = converter.convert(program)
        lines.append(drl_code)
        lines.append("")

        # Main execution
        lines.append("# Main execution")
        lines.append("if __name__ == '__main__':")

        for goal in program.goals:
            lines.append(f"    {goal.name}()")

        return "\n".join(lines)
