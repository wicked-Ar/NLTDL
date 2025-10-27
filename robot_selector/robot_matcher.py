"""
Robot Matcher
Matches robot requirements with available robots and provides recommendations.
"""
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
from tdl_analyzer import RobotRequirements


@dataclass
class Robot:
    """Robot specification."""
    manufacturer: str
    model: str
    payload_kg: float
    reach_m: float
    repeatability_mm: float
    dof: int

    @property
    def reach_mm(self) -> float:
        """Get reach in mm."""
        return self.reach_m * 1000

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "payload_kg": self.payload_kg,
            "reach_m": self.reach_m,
            "reach_mm": self.reach_mm,
            "repeatability_mm": self.repeatability_mm,
            "dof": self.dof,
        }

    def __str__(self) -> str:
        return f"{self.manufacturer.upper()} {self.model.upper()} ({self.dof}-DoF, Payload: {self.payload_kg}kg, Reach: {self.reach_m}m)"


@dataclass
class RobotMatch:
    """Robot match result with suitability score."""
    robot: Robot
    suitability_score: float  # 0-100
    meets_payload: bool
    meets_reach: bool
    payload_margin_percent: float
    reach_margin_percent: float
    reasons: List[str]

    def summary(self) -> str:
        """Generate summary string."""
        status = "[OK]" if self.meets_payload and self.meets_reach else "[WARNING]"
        lines = [
            f"{status} {self.robot}",
            f"    Suitability Score: {self.suitability_score:.1f}/100",
            f"    Payload Margin: {self.payload_margin_percent:+.1f}%",
            f"    Reach Margin: {self.reach_margin_percent:+.1f}%",
        ]
        if self.reasons:
            lines.append(f"    Notes: {'; '.join(self.reasons)}")
        return "\n".join(lines)


class RobotMatcher:
    """Matches robot requirements with available robots."""

    def __init__(self, robots_db_path: str):
        """
        Initialize robot matcher.

        Args:
            robots_db_path: Path to robots database JSON file
        """
        self.robots = self._load_robots(robots_db_path)

    def _load_robots(self, db_path: str) -> List[Robot]:
        """Load robots from database."""
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        robots = []
        for item in data:
            robot = Robot(
                manufacturer=item["manufacturer"],
                model=item["model"],
                payload_kg=item["payload_kg"],
                reach_m=item["reach_m"],
                repeatability_mm=item["repeatability_mm"],
                dof=item.get("dof", 6)  # Default to 6-DoF if not specified
            )
            robots.append(robot)

        return robots

    def find_suitable_robots(
        self,
        requirements: RobotRequirements,
        min_score: float = 0.0
    ) -> List[RobotMatch]:
        """
        Find suitable robots for given requirements.

        Args:
            requirements: Robot requirements from TDL analysis
            min_score: Minimum suitability score (0-100)

        Returns:
            List of RobotMatch objects, sorted by suitability score (descending)
        """
        matches = []

        for robot in self.robots:
            match = self._evaluate_robot(robot, requirements)
            if match.suitability_score >= min_score:
                matches.append(match)

        # Sort by suitability score (highest first)
        matches.sort(key=lambda m: m.suitability_score, reverse=True)

        return matches

    def _evaluate_robot(self, robot: Robot, requirements: RobotRequirements) -> RobotMatch:
        """
        Evaluate how well a robot matches requirements.

        Args:
            robot: Robot to evaluate
            requirements: Required specifications

        Returns:
            RobotMatch object with evaluation results
        """
        reasons = []
        score = 0.0

        # 1. Payload evaluation (40 points max)
        payload_margin = ((robot.payload_kg - requirements.required_payload_kg) /
                          requirements.required_payload_kg * 100) if requirements.required_payload_kg > 0 else 100
        meets_payload = robot.payload_kg >= requirements.required_payload_kg

        if meets_payload:
            if payload_margin >= 50:
                score += 40  # Excellent margin
                reasons.append("Excellent payload capacity")
            elif payload_margin >= 20:
                score += 35  # Good margin
                reasons.append("Good payload capacity")
            elif payload_margin >= 0:
                score += 25  # Minimal margin
                reasons.append("Adequate payload capacity")
        else:
            score += 0
            reasons.append("INSUFFICIENT PAYLOAD CAPACITY")

        # 2. Reach evaluation (40 points max)
        reach_margin = ((robot.reach_mm - requirements.required_reach_mm) /
                        requirements.required_reach_mm * 100) if requirements.required_reach_mm > 0 else 100
        meets_reach = robot.reach_mm >= requirements.required_reach_mm

        if meets_reach:
            if reach_margin >= 30:
                score += 40  # Excellent reach
                reasons.append("Excellent reach")
            elif reach_margin >= 10:
                score += 35  # Good reach
                reasons.append("Good reach")
            elif reach_margin >= 0:
                score += 25  # Minimal reach
                reasons.append("Adequate reach")
        else:
            score += 0
            reasons.append("INSUFFICIENT REACH")

        # 3. Repeatability evaluation (15 points max)
        if requirements.complexity_score >= 7:
            # High complexity requires high precision
            if robot.repeatability_mm <= 0.03:
                score += 15
                reasons.append("Excellent precision for complex task")
            elif robot.repeatability_mm <= 0.05:
                score += 12
                reasons.append("High precision for complex task")
            elif robot.repeatability_mm <= 0.1:
                score += 8
            else:
                score += 4
        else:
            # Lower complexity is more forgiving
            if robot.repeatability_mm <= 0.05:
                score += 15
                reasons.append("Excellent precision")
            elif robot.repeatability_mm <= 0.1:
                score += 12
            else:
                score += 8

        # 4. DoF (Degree of Freedom) evaluation (5 points max)
        required_dof = requirements.required_dof if hasattr(requirements, 'required_dof') else 6
        if robot.dof >= required_dof:
            if robot.dof == required_dof:
                score += 5
                reasons.append(f"Perfect DoF match ({robot.dof}-DoF)")
            else:
                score += 3
                reasons.append(f"Higher DoF available ({robot.dof}-DoF)")
        else:
            score += 0
            reasons.append(f"INSUFFICIENT DoF (requires {required_dof}, has {robot.dof})")

        # Create match result
        match = RobotMatch(
            robot=robot,
            suitability_score=score,
            meets_payload=meets_payload,
            meets_reach=meets_reach,
            payload_margin_percent=payload_margin,
            reach_margin_percent=reach_margin,
            reasons=reasons
        )

        return match

    def generate_recommendation_report(
        self,
        requirements: RobotRequirements,
        matches: List[RobotMatch]
    ) -> str:
        """
        Generate detailed recommendation report.

        Args:
            requirements: Robot requirements
            matches: List of robot matches

        Returns:
            Formatted report string
        """
        lines = [
            "",
            "="*70,
            "ROBOT RECOMMENDATION REPORT",
            "="*70,
            "",
            "TASK REQUIREMENTS:",
            "-"*70,
            f"  Payload Required: {requirements.required_payload_kg:.2f} kg",
            f"  Reach Required: {requirements.required_reach_mm:.0f} mm ({requirements.required_reach_mm/1000:.2f} m)",
            f"  Velocity Range: {requirements.velocity_range[0]:.0f} - {requirements.velocity_range[1]:.0f} mm/s",
            f"  Task Complexity: {requirements.complexity_score:.1f}/10",
            f"  Capabilities Needed: {', '.join(requirements.required_capabilities) if requirements.required_capabilities else 'None'}",
            "",
        ]

        if not matches:
            lines.extend([
                "="*70,
                "NO SUITABLE ROBOTS FOUND",
                "="*70,
                "",
                "Recommendations:",
                "  1. Consider robots with higher payload capacity",
                "  2. Consider robots with longer reach",
                "  3. Review task requirements and optimize if possible",
                "",
            ])
        else:
            lines.extend([
                "ROBOT RECOMMENDATIONS (Ranked by Suitability):",
                "="*70,
                "",
            ])

            for i, match in enumerate(matches, 1):
                lines.append(f"{i}. {match.robot}")
                lines.append(f"   Suitability Score: {match.suitability_score:.1f}/100")
                lines.append(f"   Status: {'SUITABLE' if match.meets_payload and match.meets_reach else 'NOT SUITABLE'}")
                lines.append(f"   DoF: {match.robot.dof}")
                lines.append(f"   Payload: {match.robot.payload_kg:.1f} kg (Margin: {match.payload_margin_percent:+.1f}%)")
                lines.append(f"   Reach: {match.robot.reach_m:.2f} m (Margin: {match.reach_margin_percent:+.1f}%)")
                lines.append(f"   Repeatability: {match.robot.repeatability_mm:.3f} mm")

                if match.reasons:
                    lines.append(f"   Notes:")
                    for reason in match.reasons:
                        lines.append(f"     - {reason}")

                lines.append("")

            # Best recommendation
            best_match = matches[0]
            lines.extend([
                "="*70,
                "RECOMMENDED ROBOT:",
                "="*70,
                f"  {best_match.robot}",
                f"  Suitability Score: {best_match.suitability_score:.1f}/100",
                "",
            ])

            if not (best_match.meets_payload and best_match.meets_reach):
                lines.extend([
                    "  [WARNING] This robot does not fully meet requirements!",
                    "  Please review carefully or consider alternative robots.",
                    "",
                ])

        lines.append("="*70)

        return "\n".join(lines)
