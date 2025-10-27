"""
Robot Similarity Analyzer
Evaluates similarity between robots for replacement scenarios.

This module helps identify similar robots that can replace existing ones
with minimal process disruption.
"""
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
from robot_matcher import Robot


@dataclass
class RobotSimilarity:
    """Robot similarity result."""
    robot: Robot
    target_robot: Robot
    similarity_score: float  # 0-100
    spec_similarity: float  # Payload, reach, repeatability similarity
    form_factor_similarity: float  # Size and form similarity
    manufacturer_match: bool
    reasons: List[str]
    replacement_viability: str  # "EXCELLENT", "GOOD", "MODERATE", "POOR"

    def summary(self) -> str:
        """Generate summary string."""
        lines = [
            f"[{self.replacement_viability}] {self.robot}",
            f"    Overall Similarity: {self.similarity_score:.1f}/100",
            f"    Spec Similarity: {self.spec_similarity:.1f}/100",
            f"    Form Factor Similarity: {self.form_factor_similarity:.1f}/100",
            f"    Manufacturer Match: {'Yes' if self.manufacturer_match else 'No'}",
        ]
        if self.reasons:
            lines.append(f"    Notes:")
            for reason in self.reasons:
                lines.append(f"      - {reason}")
        return "\n".join(lines)


class RobotSimilarityAnalyzer:
    """Analyzes similarity between robots for replacement scenarios."""

    # Manufacturer-specific characteristics (form factor, design philosophy)
    MANUFACTURER_CHARACTERISTICS = {
        "universal": {
            "type": "collaborative",
            "design": "compact_cylindrical",
            "mounting": ["table", "wall", "ceiling"],
            "ease_of_use": "high",
            "form_factor_weight": 1.2  # Unique design, higher weight
        },
        "doosan": {
            "type": "industrial_collaborative",
            "design": "hybrid",
            "mounting": ["floor", "table", "ceiling"],
            "ease_of_use": "high",
            "form_factor_weight": 1.0
        },
        "yaskawa": {
            "type": "industrial",
            "design": "industrial_standard",
            "mounting": ["floor", "ceiling"],
            "ease_of_use": "medium",
            "form_factor_weight": 0.9
        },
        "fanuc": {
            "type": "industrial",
            "design": "industrial_standard",
            "mounting": ["floor", "ceiling", "wall"],
            "ease_of_use": "medium",
            "form_factor_weight": 0.9
        },
        "abb": {
            "type": "industrial",
            "design": "industrial_standard",
            "mounting": ["floor", "ceiling", "wall"],
            "ease_of_use": "medium",
            "form_factor_weight": 0.9
        },
        "kuka": {
            "type": "industrial",
            "design": "industrial_standard",
            "mounting": ["floor", "ceiling"],
            "ease_of_use": "medium",
            "form_factor_weight": 0.9
        },
        "techman": {
            "type": "collaborative",
            "design": "compact_cylindrical",
            "mounting": ["table", "wall"],
            "ease_of_use": "high",
            "form_factor_weight": 1.1
        },
        "staubli": {
            "type": "industrial",
            "design": "compact",
            "mounting": ["floor", "ceiling", "table"],
            "ease_of_use": "medium",
            "form_factor_weight": 1.0
        },
        "aubo": {
            "type": "collaborative",
            "design": "compact_cylindrical",
            "mounting": ["table", "wall"],
            "ease_of_use": "high",
            "form_factor_weight": 1.1
        },
        "hansrobot": {
            "type": "collaborative",
            "design": "compact",
            "mounting": ["table", "wall"],
            "ease_of_use": "high",
            "form_factor_weight": 1.0
        },
        "kawasaki": {
            "type": "industrial",
            "design": "industrial_standard",
            "mounting": ["floor", "ceiling"],
            "ease_of_use": "medium",
            "form_factor_weight": 0.9
        },
        "mitsubishi": {
            "type": "industrial",
            "design": "compact",
            "mounting": ["floor", "table", "ceiling"],
            "ease_of_use": "medium",
            "form_factor_weight": 1.0
        },
        "standardbots": {
            "type": "collaborative",
            "design": "modern_cylindrical",
            "mounting": ["table", "wall", "ceiling"],
            "ease_of_use": "high",
            "form_factor_weight": 1.1
        }
    }

    def __init__(self, robots_db_path: str = None):
        """
        Initialize similarity analyzer.

        Args:
            robots_db_path: Path to robots database JSON file
        """
        if robots_db_path:
            self.robots = self._load_robots(robots_db_path)
        else:
            self.robots = []

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
                dof=item.get("dof", 6)
            )
            robots.append(robot)

        return robots

    def find_similar_robots(
        self,
        target_robot: Robot,
        candidates: List[Robot] = None,
        min_score: float = 0.0,
        max_results: int = 10
    ) -> List[RobotSimilarity]:
        """
        Find robots similar to the target robot.

        Args:
            target_robot: Robot to find replacements for
            candidates: List of candidate robots (uses self.robots if None)
            min_score: Minimum similarity score (0-100)
            max_results: Maximum number of results to return

        Returns:
            List of RobotSimilarity objects, sorted by similarity score
        """
        if candidates is None:
            candidates = self.robots

        similarities = []

        for robot in candidates:
            # Skip the target robot itself
            if (robot.manufacturer == target_robot.manufacturer and
                robot.model == target_robot.model):
                continue

            similarity = self._evaluate_similarity(robot, target_robot)
            if similarity.similarity_score >= min_score:
                similarities.append(similarity)

        # Sort by similarity score (highest first)
        similarities.sort(key=lambda s: s.similarity_score, reverse=True)

        return similarities[:max_results]

    def _evaluate_similarity(
        self,
        robot: Robot,
        target: Robot
    ) -> RobotSimilarity:
        """
        Evaluate similarity between two robots.

        Args:
            robot: Candidate robot
            target: Target robot to compare against

        Returns:
            RobotSimilarity object with detailed comparison
        """
        reasons = []

        # 1. Specification Similarity (50 points)
        spec_score = self._calculate_spec_similarity(robot, target, reasons)

        # 2. Form Factor Similarity (30 points)
        form_score = self._calculate_form_factor_similarity(robot, target, reasons)

        # 3. Manufacturer Match (20 points)
        manufacturer_match = robot.manufacturer.lower() == target.manufacturer.lower()
        manufacturer_score = 20.0 if manufacturer_match else 0.0

        if manufacturer_match:
            reasons.append("Same manufacturer - minimal reprogramming needed")
        else:
            reasons.append(f"Different manufacturer - may require significant reprogramming")

        # Total similarity score
        similarity_score = spec_score + form_score + manufacturer_score

        # Determine replacement viability
        if similarity_score >= 85:
            viability = "EXCELLENT"
        elif similarity_score >= 70:
            viability = "GOOD"
        elif similarity_score >= 50:
            viability = "MODERATE"
        else:
            viability = "POOR"

        return RobotSimilarity(
            robot=robot,
            target_robot=target,
            similarity_score=similarity_score,
            spec_similarity=spec_score,
            form_factor_similarity=form_score,
            manufacturer_match=manufacturer_match,
            reasons=reasons,
            replacement_viability=viability
        )

    def _calculate_spec_similarity(
        self,
        robot: Robot,
        target: Robot,
        reasons: List[str]
    ) -> float:
        """
        Calculate specification similarity (50 points max).

        Compares payload, reach, repeatability, and DoF.
        """
        score = 0.0

        # Payload similarity (20 points)
        payload_diff_percent = abs(robot.payload_kg - target.payload_kg) / target.payload_kg * 100
        if payload_diff_percent <= 10:
            score += 20
            reasons.append(f"Very similar payload capacity (±{payload_diff_percent:.1f}%)")
        elif payload_diff_percent <= 20:
            score += 15
            reasons.append(f"Similar payload capacity (±{payload_diff_percent:.1f}%)")
        elif payload_diff_percent <= 30:
            score += 10
        elif payload_diff_percent <= 50:
            score += 5
        else:
            reasons.append(f"Significantly different payload ({payload_diff_percent:.1f}% difference)")

        # Reach similarity (20 points)
        reach_diff_percent = abs(robot.reach_m - target.reach_m) / target.reach_m * 100
        if reach_diff_percent <= 10:
            score += 20
            reasons.append(f"Very similar reach (±{reach_diff_percent:.1f}%)")
        elif reach_diff_percent <= 20:
            score += 15
            reasons.append(f"Similar reach (±{reach_diff_percent:.1f}%)")
        elif reach_diff_percent <= 30:
            score += 10
        elif reach_diff_percent <= 50:
            score += 5
        else:
            reasons.append(f"Significantly different reach ({reach_diff_percent:.1f}% difference)")

        # Repeatability similarity (5 points)
        repeatability_diff_percent = abs(robot.repeatability_mm - target.repeatability_mm) / target.repeatability_mm * 100
        if repeatability_diff_percent <= 20:
            score += 5
        elif repeatability_diff_percent <= 50:
            score += 3
        else:
            score += 1

        # DoF match (5 points)
        if robot.dof == target.dof:
            score += 5
        else:
            reasons.append(f"Different DoF ({robot.dof} vs {target.dof})")

        return score

    def _calculate_form_factor_similarity(
        self,
        robot: Robot,
        target: Robot,
        reasons: List[str]
    ) -> float:
        """
        Calculate form factor similarity (30 points max).

        Considers robot type, design, size category, and physical characteristics.
        """
        score = 0.0

        robot_mfr = robot.manufacturer.lower()
        target_mfr = target.manufacturer.lower()

        # Get manufacturer characteristics
        robot_char = self.MANUFACTURER_CHARACTERISTICS.get(
            robot_mfr,
            {"type": "industrial", "design": "standard", "form_factor_weight": 1.0}
        )
        target_char = self.MANUFACTURER_CHARACTERISTICS.get(
            target_mfr,
            {"type": "industrial", "design": "standard", "form_factor_weight": 1.0}
        )

        # Robot type similarity (10 points)
        if robot_char["type"] == target_char["type"]:
            score += 10
            if robot_char["type"] == "collaborative":
                reasons.append("Both are collaborative robots - similar safety features")
            elif robot_char["type"] == "industrial":
                reasons.append("Both are industrial robots - similar robustness")
        else:
            score += 3
            reasons.append(f"Different robot types ({robot_char['type']} vs {target_char['type']})")

        # Design similarity (10 points)
        if robot_char["design"] == target_char["design"]:
            score += 10
            reasons.append(f"Similar design philosophy ({robot_char['design']})")
        elif "cylindrical" in robot_char["design"] and "cylindrical" in target_char["design"]:
            score += 7
            reasons.append("Similar cylindrical form factor")
        elif "compact" in robot_char["design"] and "compact" in target_char["design"]:
            score += 7
            reasons.append("Similar compact form factor")
        else:
            score += 3

        # Size category similarity (10 points)
        robot_size_cat = self._get_size_category(robot)
        target_size_cat = self._get_size_category(target)

        if robot_size_cat == target_size_cat:
            score += 10
            reasons.append(f"Same size category ({robot_size_cat})")
        elif abs(self._size_category_to_int(robot_size_cat) -
                 self._size_category_to_int(target_size_cat)) == 1:
            score += 6
            reasons.append(f"Adjacent size categories ({robot_size_cat} vs {target_size_cat})")
        else:
            score += 2
            reasons.append(f"Different size categories ({robot_size_cat} vs {target_size_cat})")

        return score

    def _get_size_category(self, robot: Robot) -> str:
        """
        Categorize robot by size based on payload and reach.

        Categories: micro, small, medium, large, heavy
        """
        # Combined metric: payload + normalized reach
        combined_metric = robot.payload_kg + (robot.reach_m * 10)

        if combined_metric < 8:
            return "micro"  # Small collaborative robots
        elif combined_metric < 15:
            return "small"  # Light duty robots
        elif combined_metric < 30:
            return "medium"  # General purpose robots
        elif combined_metric < 50:
            return "large"  # Heavy duty robots
        else:
            return "heavy"  # Very heavy duty robots

    def _size_category_to_int(self, category: str) -> int:
        """Convert size category to integer for comparison."""
        categories = {"micro": 0, "small": 1, "medium": 2, "large": 3, "heavy": 4}
        return categories.get(category, 2)

    def generate_similarity_report(
        self,
        target_robot: Robot,
        similarities: List[RobotSimilarity]
    ) -> str:
        """
        Generate detailed similarity comparison report.

        Args:
            target_robot: Original robot to be replaced
            similarities: List of similar robots

        Returns:
            Formatted report string
        """
        lines = [
            "",
            "="*70,
            "ROBOT REPLACEMENT SIMILARITY REPORT",
            "="*70,
            "",
            "TARGET ROBOT (to be replaced):",
            "-"*70,
            f"  {target_robot}",
            f"  Payload: {target_robot.payload_kg:.1f} kg",
            f"  Reach: {target_robot.reach_m:.2f} m ({target_robot.reach_mm:.0f} mm)",
            f"  Repeatability: {target_robot.repeatability_mm:.3f} mm",
            f"  DoF: {target_robot.dof}",
            "",
        ]

        if not similarities:
            lines.extend([
                "="*70,
                "NO SIMILAR ROBOTS FOUND",
                "="*70,
                "",
                "Recommendations:",
                "  1. Expand search criteria (lower min_score)",
                "  2. Consider robots from different manufacturers",
                "  3. Review process requirements for flexibility",
                "",
            ])
        else:
            lines.extend([
                "SIMILAR ROBOTS (Ranked by Similarity):",
                "="*70,
                "",
            ])

            for i, sim in enumerate(similarities, 1):
                lines.append(f"{i}. {sim.robot}")
                lines.append(f"   Overall Similarity: {sim.similarity_score:.1f}/100 [{sim.replacement_viability}]")
                lines.append(f"   - Spec Similarity: {sim.spec_similarity:.1f}/50")
                lines.append(f"   - Form Factor Similarity: {sim.form_factor_similarity:.1f}/30")
                lines.append(f"   - Manufacturer Match: {'Yes (20/20)' if sim.manufacturer_match else 'No (0/20)'}")
                lines.append(f"   ")
                lines.append(f"   Specifications:")
                lines.append(f"   - Payload: {sim.robot.payload_kg:.1f} kg (Target: {target_robot.payload_kg:.1f} kg)")
                lines.append(f"   - Reach: {sim.robot.reach_m:.2f} m (Target: {target_robot.reach_m:.2f} m)")
                lines.append(f"   - Repeatability: {sim.robot.repeatability_mm:.3f} mm (Target: {target_robot.repeatability_mm:.3f} mm)")
                lines.append(f"   - DoF: {sim.robot.dof} (Target: {target_robot.dof})")

                if sim.reasons:
                    lines.append(f"   ")
                    lines.append(f"   Analysis:")
                    for reason in sim.reasons:
                        lines.append(f"     - {reason}")

                lines.append("")

            # Best replacement recommendation
            best_match = similarities[0]
            lines.extend([
                "="*70,
                "RECOMMENDED REPLACEMENT:",
                "="*70,
                f"  {best_match.robot}",
                f"  Similarity Score: {best_match.similarity_score:.1f}/100",
                f"  Replacement Viability: {best_match.replacement_viability}",
                "",
            ])

            if best_match.similarity_score < 70:
                lines.extend([
                    "  [WARNING] Similarity score is below 70!",
                    "  Significant process adjustments may be required.",
                    "  Consider:",
                    "    - Thorough testing before deployment",
                    "    - Process parameter adjustments",
                    "    - Safety system reconfiguration",
                    "    - Operator retraining",
                    "",
                ])
            elif best_match.similarity_score < 85:
                lines.extend([
                    "  [INFO] Moderate similarity - some adjustments needed.",
                    "  Consider:",
                    "    - Testing with sample workpieces",
                    "    - Minor process parameter tuning",
                    "    - Operator familiarization",
                    "",
                ])
            else:
                lines.extend([
                    "  [SUCCESS] Excellent similarity!",
                    "  This robot should be a drop-in replacement with minimal changes.",
                    "",
                ])

        lines.append("="*70)

        return "\n".join(lines)

    def compare_two_robots(self, robot1: Robot, robot2: Robot) -> RobotSimilarity:
        """
        Compare two specific robots.

        Args:
            robot1: First robot
            robot2: Second robot (treated as target)

        Returns:
            RobotSimilarity object
        """
        return self._evaluate_similarity(robot1, robot2)
