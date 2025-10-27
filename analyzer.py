"""
LLM-based Natural Language Requirement Analyzer
Uses Gemini API to understand and extract structured information from user requirements.
"""
from dataclasses import dataclass, field
from typing import List
from llm_client import GeminiClient


@dataclass
class RequirementAnalysis:
    """Structured analysis result from LLM."""
    actions: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    coordinates: dict = field(default_factory=dict)  # NEW: Store location coordinates
    task_description: str = ""
    raw_input: str = ""

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "actions": self.actions,
            "objects": self.objects,
            "locations": self.locations,
            "constraints": self.constraints,
            "coordinates": self.coordinates,
            "task_description": self.task_description,
            "raw_input": self.raw_input
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"[INFO] Task: {self.task_description}",
            f"[TARGET] Actions: {', '.join(self.actions) if self.actions else 'None'}",
            f"[OBJECTS] Objects: {', '.join(self.objects) if self.objects else 'None'}",
            f"[LOCATIONS] Locations: {', '.join(self.locations) if self.locations else 'None'}",
        ]

        # Add coordinates if available
        if self.coordinates:
            coord_strs = [f"{loc}: {coords}" for loc, coords in self.coordinates.items()]
            lines.append(f"[COORDS] Coordinates: {', '.join(coord_strs)}")

        lines.append(f"[CONSTRAINTS]  Constraints: {', '.join(self.constraints) if self.constraints else 'None'}")
        return "\n".join(lines)


class LLMRequirementAnalyzer:
    """Analyzes natural language requirements using LLM."""

    def __init__(self, api_key: str = None):
        """
        Initialize analyzer with LLM client.

        Args:
            api_key: Gemini API key. If None, reads from environment.
        """
        self.llm_client = GeminiClient(api_key)

    def analyze(self, user_input: str) -> RequirementAnalysis:
        """
        Analyze user requirement using LLM.

        Args:
            user_input: Natural language requirement (Korean or English)

        Returns:
            RequirementAnalysis object with extracted information

        Raises:
            Exception: If LLM analysis fails
        """
        print("\n[LLM] LLM analyzing requirement...")

        try:
            # Call LLM to analyze requirement
            result = self.llm_client.analyze_requirement(user_input)

            # Create RequirementAnalysis object
            analysis = RequirementAnalysis(
                actions=result.get("actions", []),
                objects=result.get("objects", []),
                locations=result.get("locations", []),
                constraints=result.get("constraints", []),
                coordinates=result.get("coordinates", {}),  # NEW: Extract coordinates
                task_description=result.get("task_description", ""),
                raw_input=user_input
            )

            print("[OK] LLM analysis completed")
            return analysis

        except Exception as e:
            raise Exception(f"LLM requirement analysis failed: {e}")

    def validate_analysis(self, analysis: RequirementAnalysis) -> bool:
        """
        Validate that the analysis has sufficient information.

        Args:
            analysis: Analysis result to validate

        Returns:
            True if valid, False otherwise
        """
        # At least one action should be present
        if not analysis.actions:
            return False

        # If transfer/pick/place actions, should have at least one location
        action_needs_location = {"transfer", "pick", "place", "move"}
        if any(action in analysis.actions for action in action_needs_location):
            if not analysis.locations:
                return False

        return True

    def interactive_correction(self, analysis: RequirementAnalysis) -> RequirementAnalysis:
        """
        Allow user to interactively correct the analysis.

        Args:
            analysis: Initial analysis result

        Returns:
            Corrected analysis
        """
        print("\n" + "="*60)
        print("Analysis Result - Please verify:")
        print("="*60)
        print(analysis.summary())
        print("="*60)

        while True:
            user_input = input("\nIs this correct? (yes/no/edit): ").strip().lower()

            if user_input in ["yes", "y"]:
                return analysis
            elif user_input in ["no", "n"]:
                print("\nPlease provide the corrected information:")

                actions_input = input(f"Actions (current: {', '.join(analysis.actions)}): ").strip()
                if actions_input:
                    analysis.actions = [a.strip() for a in actions_input.split(",")]

                objects_input = input(f"Objects (current: {', '.join(analysis.objects)}): ").strip()
                if objects_input:
                    analysis.objects = [o.strip() for o in objects_input.split(",")]

                locations_input = input(f"Locations (current: {', '.join(analysis.locations)}): ").strip()
                if locations_input:
                    analysis.locations = [l.strip() for l in locations_input.split(",")]

                constraints_input = input(f"Constraints (current: {', '.join(analysis.constraints)}): ").strip()
                if constraints_input:
                    analysis.constraints = [c.strip() for c in constraints_input.split(",")]

                print("\n[OK] Analysis updated")
                print(analysis.summary())
            elif user_input == "edit":
                print("\nWhich field to edit?")
                print("1. Actions")
                print("2. Objects")
                print("3. Locations")
                print("4. Constraints")
                print("5. Task Description")
                choice = input("Enter number: ").strip()

                if choice == "1":
                    actions_input = input(f"Actions (comma-separated): ").strip()
                    if actions_input:
                        analysis.actions = [a.strip() for a in actions_input.split(",")]
                elif choice == "2":
                    objects_input = input(f"Objects (comma-separated): ").strip()
                    if objects_input:
                        analysis.objects = [o.strip() for o in objects_input.split(",")]
                elif choice == "3":
                    locations_input = input(f"Locations (comma-separated): ").strip()
                    if locations_input:
                        analysis.locations = [l.strip() for l in locations_input.split(",")]
                elif choice == "4":
                    constraints_input = input(f"Constraints (comma-separated): ").strip()
                    if constraints_input:
                        analysis.constraints = [c.strip() for c in constraints_input.split(",")]
                elif choice == "5":
                    desc_input = input(f"Task Description: ").strip()
                    if desc_input:
                        analysis.task_description = desc_input

                print("\n[OK] Field updated")
                print(analysis.summary())
            else:
                print("Invalid input. Please enter 'yes', 'no', or 'edit'.")
