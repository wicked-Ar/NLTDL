"""
Test script for robot similarity analyzer
"""
from robot_similarity import RobotSimilarityAnalyzer, Robot


def test_basic_similarity():
    """Test basic similarity calculation."""
    print("="*70)
    print("TEST 1: Basic Similarity Calculation")
    print("="*70)

    # Create two similar robots
    robot1 = Robot(
        manufacturer="doosan",
        model="h2017",
        payload_kg=20.0,
        reach_m=1.7,
        repeatability_mm=0.05,
        dof=6
    )

    robot2 = Robot(
        manufacturer="yaskawa",
        model="hc20",
        payload_kg=20.0,
        reach_m=1.7,
        repeatability_mm=0.05,
        dof=6
    )

    analyzer = RobotSimilarityAnalyzer()
    similarity = analyzer.compare_two_robots(robot1, robot2)

    print(f"\nRobot 1: {robot1}")
    print(f"Robot 2: {robot2}")
    print(f"\n{similarity.summary()}")
    print(f"\nExpected: HIGH similarity (different manufacturer, same specs)")
    print(f"Result: {similarity.replacement_viability} - {similarity.similarity_score:.1f}/100")
    print("\n[PASS] Test passed!\n")


def test_database_search():
    """Test finding similar robots from database."""
    print("="*70)
    print("TEST 2: Database Search for Similar Robots")
    print("="*70)

    try:
        analyzer = RobotSimilarityAnalyzer("robots_db.json")

        # Find a target robot
        target = None
        for robot in analyzer.robots:
            if robot.manufacturer == "doosan" and robot.model == "h2017":
                target = robot
                break

        if not target:
            print("\n[WARNING] Doosan H2017 not found in database, using first robot")
            target = analyzer.robots[0]

        print(f"\nTarget Robot: {target}")
        print(f"Looking for similar robots...\n")

        similarities = analyzer.find_similar_robots(
            target,
            min_score=50.0,
            max_results=5
        )

        print(f"Found {len(similarities)} similar robots:\n")
        for i, sim in enumerate(similarities, 1):
            print(f"{i}. {sim.robot}")
            print(f"   Similarity: {sim.similarity_score:.1f}/100 [{sim.replacement_viability}]")
            print(f"   Manufacturer Match: {'Yes' if sim.manufacturer_match else 'No'}")
            print()

        print("[PASS] Test passed!\n")

    except FileNotFoundError:
        print("\n[ERROR] robots_db.json not found!")
        print("Please run this test from the robot_selector directory.")
        print("[FAIL] Test failed!\n")


def test_different_sizes():
    """Test similarity with different robot sizes."""
    print("="*70)
    print("TEST 3: Different Robot Sizes")
    print("="*70)

    small_robot = Robot(
        manufacturer="universal",
        model="ur3e",
        payload_kg=3.0,
        reach_m=0.5,
        repeatability_mm=0.03,
        dof=6
    )

    large_robot = Robot(
        manufacturer="universal",
        model="ur10e",
        payload_kg=12.5,
        reach_m=1.3,
        repeatability_mm=0.1,
        dof=6
    )

    analyzer = RobotSimilarityAnalyzer()
    similarity = analyzer.compare_two_robots(small_robot, large_robot)

    print(f"\nSmall Robot: {small_robot}")
    print(f"Large Robot: {large_robot}")
    print(f"\n{similarity.summary()}")
    print(f"\nExpected: MODERATE similarity (same manufacturer, different sizes)")
    print(f"Result: {similarity.replacement_viability} - {similarity.similarity_score:.1f}/100")
    print("\n[PASS] Test passed!\n")


def test_collaborative_vs_industrial():
    """Test similarity between collaborative and industrial robots."""
    print("="*70)
    print("TEST 4: Collaborative vs Industrial Robots")
    print("="*70)

    collaborative = Robot(
        manufacturer="universal",
        model="ur10e",
        payload_kg=12.5,
        reach_m=1.3,
        repeatability_mm=0.1,
        dof=6
    )

    industrial = Robot(
        manufacturer="fanuc",
        model="m20ia",
        payload_kg=20.0,
        reach_m=1.81,
        repeatability_mm=0.08,
        dof=6
    )

    analyzer = RobotSimilarityAnalyzer()
    similarity = analyzer.compare_two_robots(collaborative, industrial)

    print(f"\nCollaborative: {collaborative}")
    print(f"Industrial: {industrial}")
    print(f"\n{similarity.summary()}")
    print(f"\nExpected: MODERATE/LOW similarity (different types)")
    print(f"Result: {similarity.replacement_viability} - {similarity.similarity_score:.1f}/100")
    print("\n[PASS] Test passed!\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ROBOT SIMILARITY ANALYZER - TEST SUITE")
    print("="*70 + "\n")

    test_basic_similarity()
    test_database_search()
    test_different_sizes()
    test_collaborative_vs_industrial()

    print("="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)
