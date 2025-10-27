"""
TDL Parser
Parses TDL (Task Description Language) files into structured representation.
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TDLCommand:
    """Represents a single TDL command."""
    command_type: str
    args: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""

    def __str__(self) -> str:
        return f"{self.command_type}({self.args})"


@dataclass
class TDLGoal:
    """Represents a GOAL block in TDL."""
    name: str
    commands: List[TDLCommand] = field(default_factory=list)

    def __str__(self) -> str:
        return f"GOAL {self.name} ({len(self.commands)} commands)"


@dataclass
class TDLProgram:
    """Represents entire TDL program."""
    goals: List[TDLGoal] = field(default_factory=list)
    definitions: Dict[str, str] = field(default_factory=dict)  # DEFINE statements

    def get_goal(self, name: str) -> Optional[TDLGoal]:
        """Get goal by name."""
        for goal in self.goals:
            if goal.name == name:
                return goal
        return None

    def resolve_definition(self, name: str) -> str:
        """Resolve DEFINE reference to its value."""
        return self.definitions.get(name, name)


class TDLParser:
    """Parser for TDL files."""

    def parse_file(self, file_path: str) -> TDLProgram:
        """Parse TDL file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content)

    def parse(self, tdl_content: str) -> TDLProgram:
        """Parse TDL content."""
        program = TDLProgram()
        lines = tdl_content.split('\n')

        current_goal = None
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('//') or line.startswith('#'):
                i += 1
                continue

            # Parse DEFINE statements
            if line.startswith('DEFINE'):
                self._parse_define(line, program)
                i += 1
                continue

            # Parse GOAL declaration
            if line.startswith('GOAL'):
                match = re.match(r'GOAL\s+(\w+)\s*\(\s*\)', line)
                if match:
                    goal_name = match.group(1)
                    current_goal = TDLGoal(name=goal_name)
                    program.goals.append(current_goal)
                i += 1
                continue

            # Skip opening/closing braces
            if line == '{' or line == '}':
                i += 1
                continue

            # Parse SPAWN commands
            if line.startswith('SPAWN') and current_goal:
                command = self._parse_spawn_command(line)
                if command:
                    current_goal.commands.append(command)

            i += 1

        return program

    def _parse_define(self, line: str, program: TDLProgram):
        """Parse DEFINE statement."""
        # Format: DEFINE Name = Value;
        match = re.match(r'DEFINE\s+(\w+)\s*=\s*(.+?);', line)
        if match:
            name = match.group(1)
            value = match.group(2).strip()
            program.definitions[name] = value

    def _parse_spawn_command(self, line: str) -> Optional[TDLCommand]:
        """Parse SPAWN command line."""
        # Remove SPAWN and WITH WAIT
        line = line.replace('SPAWN', '').replace('WITH WAIT', '').replace(';', '').strip()

        # Extract command name
        match = re.match(r'(\w+)\s*\((.*)\)', line, re.DOTALL)
        if not match:
            return None

        command_type = match.group(1)
        args_str = match.group(2)

        # Parse arguments
        args = self._parse_arguments(args_str)

        return TDLCommand(
            command_type=command_type,
            args=args,
            raw_line=line
        )

    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse command arguments."""
        args = {}

        if not args_str.strip():
            return args

        # Handle named arguments (key=value)
        # Updated regex to handle nested parentheses properly
        # Pattern: key = value (where value can contain commas if inside parentheses)
        pattern = r'(\w+)\s*=\s*((?:Pos[XJ]\([^)]+\)|[^,]+))'
        matches = re.findall(pattern, args_str)

        for key, value in matches:
            value = value.strip()

            # Parse value type
            if value.startswith('PosX(') or value.startswith('PosJ('):
                # Keep as string for now
                args[key] = value
            elif value.startswith('(') and value.endswith(')'):
                # Tuple
                args[key] = value
            elif value.isdigit():
                args[key] = int(value)
            elif self._is_float(value):
                args[key] = float(value)
            elif value.lower() in ['true', 'false']:
                args[key] = value.lower() == 'true'
            else:
                # String (remove quotes if present)
                args[key] = value.strip('"\'')

        return args

    def _is_float(self, value: str) -> bool:
        """Check if string is a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False
