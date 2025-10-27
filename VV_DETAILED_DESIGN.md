# Validation & Verification System - Detailed Design Specification

## 📋 목차

1. [Rule-based Validation Rules](#rule-based-validation-rules)
2. [LLM-based Semantic Validation](#llm-based-semantic-validation)
3. [Test Dataset Construction](#test-dataset-construction)
4. [Architecture Design](#architecture-design)
5. [Evaluation Metrics](#evaluation-metrics)
6. [Implementation Timeline](#implementation-timeline)

---

## 1. Rule-based Validation Rules

### 1.1 Syntax Validator

#### **검증 항목**

##### R-SYN-001: TDL Document Structure
```python
RULE: TDL 문서는 반드시 다음 요소를 포함해야 함
- DEFINE 섹션 (위치 정의)
- GOAL 섹션 (최소 1개 이상)

CHECK:
✓ DEFINE 키워드가 최소 1개 이상 존재
✓ GOAL 키워드가 최소 1개 이상 존재
✓ 각 GOAL은 중괄호 {}로 감싸져 있음

SEVERITY: CRITICAL
ERROR_MESSAGE: "TDL document missing required DEFINE or GOAL sections"
```

##### R-SYN-002: Position Definition Format
```python
RULE: DEFINE 문은 올바른 형식이어야 함
PATTERN: DEFINE <name> = Pos[J|X|Y](<params>);

CHECK:
✓ DEFINE 다음에 식별자 존재
✓ = 기호 존재
✓ PosJ, PosX, PosY 중 하나 사용
✓ 괄호와 세미콜론 올바르게 사용

EXAMPLES:
✓ DEFINE Home_Pose = PosJ(0, 0, 90, 0, 90, 0);
✓ DEFINE A_Safe_Pose = PosX(0, 0, 150, 0, 0, 0);
✗ DEFINE Bad_Pose = PosX(0, 0, 150)  // Missing semicolon
✗ DEFINE Bad_Pose = (0, 0, 150);     // Missing Pos type

SEVERITY: CRITICAL
ERROR_MESSAGE: "Invalid position definition at line {line_number}"
```

##### R-SYN-003: PosJ Parameter Count
```python
RULE: PosJ는 6개의 joint angle 파라미터를 가져야 함

CHECK:
✓ PosJ(...) 내부 파라미터 개수 = 6
✓ 각 파라미터는 숫자 (정수 또는 실수)

EXAMPLES:
✓ PosJ(0, 0, 90, 0, 90, 0)
✓ PosJ(0.0, -45.5, 90.0, 0.0, 90.0, 0.0)
✗ PosJ(0, 0, 90, 0, 90)       // Only 5 parameters
✗ PosJ(0, 0, 90, 0, 90, 0, 0) // 7 parameters

SEVERITY: CRITICAL
ERROR_MESSAGE: "PosJ requires exactly 6 parameters, found {count}"
```

##### R-SYN-004: PosX Parameter Count
```python
RULE: PosX는 6개의 Cartesian 파라미터를 가져야 함

CHECK:
✓ PosX(...) 내부 파라미터 개수 = 6
✓ x, y, z, rx, ry, rz 순서
✓ 각 파라미터는 숫자

EXAMPLES:
✓ PosX(300, 200, 50, 0, 0, 0)
✓ PosX(0.0, 0.0, 150.0, 0.0, 0.0, 0.0)
✗ PosX(300, 200, 50)          // Only 3 parameters

SEVERITY: CRITICAL
ERROR_MESSAGE: "PosX requires exactly 6 parameters (x,y,z,rx,ry,rz)"
```

##### R-SYN-005: SPAWN Command Format
```python
RULE: SPAWN 명령어는 올바른 형식이어야 함
PATTERN: SPAWN <Command>(<params>) WITH <option>;

CHECK:
✓ SPAWN 키워드 존재
✓ 명령어 이름 (MoveJoint, MoveLinear, SetDigitalOutput 등)
✓ WITH 키워드 존재
✓ WAIT 또는 NOWAIT 옵션
✓ 세미콜론으로 종료

EXAMPLES:
✓ SPAWN MoveLinear(target_pose=A_Safe_Pose, velocity=100, ...) WITH WAIT;
✓ SPAWN Delay(duration_sec=0.5) WITH WAIT;
✗ SPAWN MoveLinear(...) WAIT;        // Missing WITH
✗ SPAWN MoveLinear(...) WITH WAIT    // Missing semicolon

SEVERITY: CRITICAL
ERROR_MESSAGE: "Invalid SPAWN command format at line {line_number}"
```

##### R-SYN-006: Required Parameters Check
```python
RULE: 각 명령어는 필수 파라미터를 가져야 함

MoveJoint:
  REQUIRED: target_pose, velocity, acceleration, tool, blending_radius

MoveLinear:
  REQUIRED: target_pose, velocity, acceleration, tool, blending_radius

SetDigitalOutput:
  REQUIRED: port, value

Delay:
  REQUIRED: duration_sec

CHECK:
✓ 명령어별 필수 파라미터 모두 존재
✓ 파라미터 이름 정확

EXAMPLES:
✓ MoveLinear(target_pose=A, velocity=100, acceleration=50, tool=0, blending_radius=0)
✗ MoveLinear(target_pose=A, velocity=100)  // Missing parameters

SEVERITY: CRITICAL
ERROR_MESSAGE: "Missing required parameter '{param}' for command '{command}'"
```

---

### 1.2 Safety Validator

#### **검증 항목**

##### R-SAF-001: Position Reachability
```python
RULE: 모든 좌표는 로봇의 reach 범위 내에 있어야 함

INPUT:
- TDL positions (PosX)
- Robot spec (reach_m)

CHECK:
for each PosX(x, y, z, rx, ry, rz):
    distance = sqrt(x² + y² + z²)
    ✓ distance <= robot.reach_m * 1000  // Convert to mm

SEVERITY: CRITICAL
ERROR_MESSAGE: "Position {pose_name} at ({x},{y},{z}) exceeds robot reach of {reach}mm"

EXAMPLE:
Robot: UR10E (reach = 1300mm)
✓ PosX(300, 200, 50, 0, 0, 0)     // distance = 361mm
✓ PosX(1000, 500, 200, 0, 0, 0)   // distance = 1128mm
✗ PosX(2000, 1000, 500, 0, 0, 0)  // distance = 2345mm > 1300mm
```

##### R-SAF-002: Velocity Limits
```python
RULE: 속도는 안전 범위 내에 있어야 함

LIMITS:
- MIN_VELOCITY: 10 mm/s (너무 느리면 비효율)
- MAX_VELOCITY: 1000 mm/s (안전 한계)
- RECOMMENDED: 50-500 mm/s

CHECK:
for each Move command:
    ✓ 10 <= velocity <= 1000
    ⚠ velocity < 50 or velocity > 500 → WARNING

SEVERITY:
- velocity < 10 or > 1000: CRITICAL
- velocity < 50 or > 500: WARNING

ERROR_MESSAGE: "Velocity {velocity} mm/s is outside safe range [10-1000]"
WARNING_MESSAGE: "Velocity {velocity} mm/s is outside recommended range [50-500]"

EXAMPLE:
✓ velocity=100
✓ velocity=500
⚠ velocity=800  // Warning: too fast
✗ velocity=1500 // Error: exceeds limit
✗ velocity=5    // Error: too slow
```

##### R-SAF-003: Acceleration Limits
```python
RULE: 가속도는 안전 범위 내에 있어야 함

LIMITS:
- MIN_ACCELERATION: 10 mm/s²
- MAX_ACCELERATION: 500 mm/s²
- RECOMMENDED: 20-200 mm/s²

CHECK:
for each Move command:
    ✓ 10 <= acceleration <= 500
    ⚠ acceleration < 20 or acceleration > 200 → WARNING

SEVERITY:
- acceleration < 10 or > 500: CRITICAL
- acceleration < 20 or > 200: WARNING

ERROR_MESSAGE: "Acceleration {accel} mm/s² is outside safe range [10-500]"
```

##### R-SAF-004: Z-axis Safety (Collision Prevention)
```python
RULE: Z 좌표는 항상 바닥(0) 이상이어야 함

CHECK:
for each PosX(x, y, z, rx, ry, rz):
    ✓ z >= 0  // 바닥 충돌 방지
    ⚠ z < 10 → WARNING (너무 낮음)

SEVERITY:
- z < 0: CRITICAL
- z < 10: WARNING

ERROR_MESSAGE: "Z-coordinate {z}mm is below ground level (z=0)"
WARNING_MESSAGE: "Z-coordinate {z}mm is dangerously close to ground"

EXAMPLE:
✓ PosX(300, 200, 50, 0, 0, 0)
⚠ PosX(300, 200, 5, 0, 0, 0)   // Warning: too low
✗ PosX(300, 200, -10, 0, 0, 0) // Error: underground
```

##### R-SAF-005: Gripper State Validation
```python
RULE: Gripper 상태 변화가 논리적이어야 함

CHECK:
- 물체를 잡기 전에는 gripper가 열려있어야 함
- 물체를 놓을 때는 gripper가 닫혀있어야 함
- 연속된 같은 명령 감지 (불필요한 반복)

PATTERN:
✓ SetDigitalOutput(port=1, value=0) → ... → SetDigitalOutput(port=1, value=1)  // Open → Close
✗ SetDigitalOutput(port=1, value=1) → SetDigitalOutput(port=1, value=1)        // Close → Close (redundant)

SEVERITY: WARNING
WARNING_MESSAGE: "Redundant gripper command detected at line {line}"
```

##### R-SAF-006: Motion Sequence Safety
```python
RULE: Pick & Place 동작 시 안전한 순서를 따라야 함

SAFE_PATTERN:
1. Approach (안전 높이에서 접근)
2. Descend (천천히 하강)
3. Grasp (그립)
4. Lift (안전 높이로 상승)
5. Move (이동)
6. Descend (목표 위치로 하강)
7. Release (놓기)
8. Retreat (안전 높이로 후퇴)

CHECK:
✓ Grasp 전에 Descend 존재
✓ Grasp 후에 Lift 존재
✓ Release 전에 Descend 존재
✓ Release 후에 Retreat 존재

SEVERITY: WARNING
WARNING_MESSAGE: "Potentially unsafe motion sequence detected"
```

---

### 1.3 Consistency Validator

#### **검증 항목**

##### R-CON-001: Reference Validation
```python
RULE: 참조하는 모든 변수/위치는 사전에 정의되어 있어야 함

CHECK:
1. SPAWN 명령어의 target_pose 파라미터 추출
2. 해당 이름이 DEFINE 섹션에 정의되어 있는지 확인

EXAMPLE:
DEFINE A_Safe_Pose = PosX(0, 0, 150, 0, 0, 0);
...
✓ SPAWN MoveLinear(target_pose=A_Safe_Pose, ...)  // OK: defined
✗ SPAWN MoveLinear(target_pose=B_Safe_Pose, ...)  // Error: not defined

SEVERITY: CRITICAL
ERROR_MESSAGE: "Undefined position reference '{pose_name}' at line {line}"
```

##### R-CON-002: Duplicate Definition Check
```python
RULE: 같은 이름으로 중복 정의하면 안됨

CHECK:
for each DEFINE statement:
    ✓ 이름이 unique해야 함

EXAMPLE:
✗ DEFINE Home_Pose = PosJ(0, 0, 90, 0, 90, 0);
  DEFINE Home_Pose = PosJ(0, 0, 0, 0, 0, 0);  // Duplicate!

SEVERITY: WARNING
WARNING_MESSAGE: "Duplicate definition of '{name}' at line {line}"
```

##### R-CON-003: GOAL Naming Convention
```python
RULE: GOAL 이름은 명명 규칙을 따라야 함

CONVENTION:
- Initialize_Process, Execute_Process, Finalize_Process 권장
- CamelCase 또는 Snake_Case
- 의미있는 이름

CHECK:
✓ GOAL 이름이 영문자로 시작
✓ 특수문자 사용 안함 (언더스코어 제외)
⚠ 일반적인 패턴 (Initialize, Execute, Finalize) 권장

SEVERITY: INFO
INFO_MESSAGE: "Consider using conventional GOAL names (Initialize_Process, Execute_Process, Finalize_Process)"
```

##### R-CON-004: Parameter Consistency
```python
RULE: 같은 종류의 동작은 비슷한 파라미터를 사용해야 함

CHECK:
- 같은 높이에서의 이동은 같은 velocity 사용 권장
- 하강/상승 동작은 더 느린 velocity 사용 권장

HEURISTIC:
- Safe approach: velocity = 100-200 mm/s
- Precision move (grasp/place): velocity = 50-100 mm/s
- Lift/Lower: velocity = 50-100 mm/s

SEVERITY: INFO
INFO_MESSAGE: "Consider using consistent velocities for similar motions"
```

##### R-CON-005: Logical Sequence Validation
```python
RULE: Task 순서가 논리적이어야 함

CHECK:
1. Initialize_Process가 가장 먼저 실행되어야 함
2. Execute_Process가 중간에 실행
3. Finalize_Process가 마지막에 실행

PATTERN:
✓ Initialize → Execute → Finalize
✗ Execute → Initialize → Finalize

SEVERITY: WARNING
WARNING_MESSAGE: "Unusual GOAL execution order detected"
```

##### R-CON-006: End Command Presence
```python
RULE: 프로그램은 반드시 End() 명령으로 종료되어야 함

CHECK:
✓ Finalize_Process (또는 마지막 GOAL) 내에 End() 존재

SEVERITY: WARNING
WARNING_MESSAGE: "Program should end with End() command"
```

---

### 1.4 Domain-Specific Validator

#### **검증 항목**

##### R-DOM-001: Pick-and-Place Pattern Recognition
```python
RULE: Pick & Place 작업은 표준 패턴을 따라야 함

STANDARD_PATTERN:
1. Home 위치로 이동
2. Gripper 열기
3. Source 위치로 접근 (safe height)
4. 하강 (grasp height)
5. Gripper 닫기 + Delay
6. 상승 (safe height)
7. Destination 위치로 이동 (safe height)
8. 하강 (place height)
9. Gripper 열기 + Delay
10. 후퇴 (safe height)
11. Home 위치로 복귀

CHECK:
✓ 위 패턴의 80% 이상 일치
⚠ 패턴과 크게 다르면 WARNING

SEVERITY: INFO
INFO_MESSAGE: "Non-standard pick-and-place pattern detected"
```

##### R-DOM-002: Safe Height Convention
```python
RULE: Safe height는 base height + 100mm 이상이어야 함

CONVENTION:
- Base/Grasp/Place height: z = 50-100mm
- Safe height: z = base_z + 100mm 이상

CHECK:
for positions with "Safe" in name:
    ✓ z >= 100mm

SEVERITY: WARNING
WARNING_MESSAGE: "Safe height {z}mm may be too low (recommend >= 100mm)"
```

##### R-DOM-003: Delay After Gripper Action
```python
RULE: Gripper 동작 후에는 Delay가 있어야 함

PATTERN:
SetDigitalOutput(port=1, value=X) → Delay(duration_sec=0.5~2.0)

CHECK:
✓ Gripper 명령 후에 Delay 존재
✓ Delay 시간이 0.3~2.0초 범위

SEVERITY: WARNING
WARNING_MESSAGE: "Missing delay after gripper action at line {line}"
```

---

## 2. LLM-based Semantic Validation

### 2.1 Validation Strategy

#### **Two-Stage Validation**

```
Stage 1: Quick Check (Fast)
- Binary classification: PASS / FAIL
- Confidence score: 0-100
- Using lightweight prompt

Stage 2: Detailed Analysis (Thorough)
- Only for low-confidence cases (< 80)
- Detailed reasoning
- Specific error identification
```

### 2.2 Prompt Design

#### **Stage 1: Quick Validation Prompt**

```python
PROMPT_TEMPLATE = """
You are an expert in robot programming validation. Your task is to quickly verify if a TDL program correctly implements a natural language instruction.

# Natural Language Instruction:
{natural_language}

# Generated TDL Code:
{tdl_code}

# Quick Validation Checklist:
1. Object Match: Does the TDL reference the correct objects mentioned in the instruction?
2. Action Match: Does the TDL perform the correct actions (pick, place, move, etc.)?
3. Location Match: Are source and destination locations correct?
4. Sequence Match: Is the order of operations logical?

# Response Format (JSON):
{{
  "verdict": "PASS" or "FAIL",
  "confidence": 0-100,
  "brief_reason": "one sentence explanation"
}}

# Examples:

## Example 1:
NL: "Move the box from A to B"
TDL: [code with A as source, B as destination]
Response: {{"verdict": "PASS", "confidence": 95, "brief_reason": "Correct source A and destination B"}}

## Example 2:
NL: "Pick up the red cube"
TDL: [code referencing "blue_cube"]
Response: {{"verdict": "FAIL", "confidence": 90, "brief_reason": "Object mismatch: red vs blue"}}

## Example 3:
NL: "Place the part gently"
TDL: [code with velocity=1000]
Response: {{"verdict": "FAIL", "confidence": 85, "brief_reason": "High velocity contradicts 'gently' requirement"}}

# Now validate:
Response (JSON only):
"""
```

#### **Stage 2: Detailed Analysis Prompt**

```python
DETAILED_PROMPT_TEMPLATE = """
You are an expert robot programming validator conducting a thorough analysis.

# Task Description (Natural Language):
{natural_language}

# Generated TDL Program:
{tdl_code}

# Detailed Validation Requirements:

## 1. Object Validation
- Extract all objects mentioned in NL
- Verify each object is correctly defined in TDL
- Check if object properties match (color, size, type)

## 2. Action Validation
- Extract all actions mentioned in NL (pick, place, move, transfer, etc.)
- Verify corresponding TDL commands exist
- Check action parameters (gripper state, motion type)

## 3. Spatial Validation
- Verify source location matches NL description
- Verify destination location matches NL description
- Check if intermediate waypoints are reasonable

## 4. Temporal Validation
- Verify sequence of operations is logical
- Check if timing constraints are met (delays, synchronization)

## 5. Safety & Quality Validation
- Check if motion is safe (no sudden movements)
- Verify velocities match task requirements (gentle, fast, precise, etc.)
- Validate gripper forces if mentioned

# Analysis Output Format (JSON):
{{
  "overall_verdict": "PASS" or "FAIL",
  "confidence": 0-100,
  "detailed_analysis": {{
    "object_validation": {{
      "status": "PASS/FAIL",
      "details": "explanation"
    }},
    "action_validation": {{
      "status": "PASS/FAIL",
      "details": "explanation"
    }},
    "spatial_validation": {{
      "status": "PASS/FAIL",
      "details": "explanation"
    }},
    "temporal_validation": {{
      "status": "PASS/FAIL",
      "details": "explanation"
    }},
    "safety_validation": {{
      "status": "PASS/FAIL",
      "details": "explanation"
    }}
  }},
  "issues_found": ["list", "of", "specific", "issues"],
  "suggestions": ["list", "of", "improvement", "suggestions"]
}}

Provide detailed analysis (JSON only):
"""
```

### 2.3 Few-shot Examples Database

```python
FEW_SHOT_EXAMPLES = [
    {
        "nl": "Transfer the box from table A to table B",
        "tdl": """
DEFINE A_Grasp_Pose = PosX(0, 0, 60, 0, 0, 0);
DEFINE B_Place_Pose = PosX(300, 200, 60, 0, 0, 0);
GOAL Execute_Process() {
    SPAWN MoveLinear(target_pose=A_Grasp_Pose, ...) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=1) WITH WAIT; // Close gripper
    SPAWN MoveLinear(target_pose=B_Place_Pose, ...) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT; // Open gripper
}
        """,
        "verdict": "PASS",
        "confidence": 95,
        "reason": "Correctly moves from A to B with proper grasp and release"
    },
    {
        "nl": "Pick the red block from position A",
        "tdl": """
DEFINE Blue_Block_Pose = PosX(0, 0, 60, 0, 0, 0);
GOAL Execute_Process() {
    SPAWN MoveLinear(target_pose=Blue_Block_Pose, ...) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=1) WITH WAIT;
}
        """,
        "verdict": "FAIL",
        "confidence": 90,
        "reason": "Object mismatch: instruction mentions 'red block' but TDL uses 'Blue_Block_Pose'"
    },
    {
        "nl": "Slowly place the fragile glass at position B",
        "tdl": """
DEFINE B_Place_Pose = PosX(300, 200, 60, 0, 0, 0);
GOAL Execute_Process() {
    SPAWN MoveLinear(target_pose=B_Place_Pose, velocity=500, ...) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT;
}
        """,
        "verdict": "FAIL",
        "confidence": 85,
        "reason": "Velocity too high (500mm/s) for 'slowly' and 'fragile' requirements"
    },
    {
        "nl": "Move to position A then position B then return home",
        "tdl": """
DEFINE Home_Pose = PosJ(0, 0, 90, 0, 90, 0);
DEFINE A_Pose = PosX(100, 0, 150, 0, 0, 0);
DEFINE B_Pose = PosX(300, 200, 150, 0, 0, 0);
GOAL Execute_Process() {
    SPAWN MoveLinear(target_pose=B_Pose, ...) WITH WAIT;  // ERROR: B first
    SPAWN MoveLinear(target_pose=A_Pose, ...) WITH WAIT;  // Then A
    SPAWN MoveJoint(target_pose=Home_Pose, ...) WITH WAIT;
}
        """,
        "verdict": "FAIL",
        "confidence": 95,
        "reason": "Sequence error: goes to B before A, contradicting 'A then B' instruction"
    },
    {
        "nl": "Grip the part tightly",
        "tdl": """
GOAL Execute_Process() {
    SPAWN SetDigitalOutput(port=1, value=1) WITH WAIT;
    // No delay specified
}
        """,
        "verdict": "FAIL",
        "confidence": 75,
        "reason": "Missing delay after gripper action to ensure secure grip"
    }
]
```

### 2.4 Semantic Validation Categories

| Category | Description | Example Error |
|----------|-------------|---------------|
| **Object Mismatch** | TDL references wrong object | NL: "red cube" → TDL: "blue_cube" |
| **Action Mismatch** | Wrong action type | NL: "place gently" → TDL: velocity=1000 |
| **Location Error** | Source/destination swapped | NL: "A to B" → TDL: B to A |
| **Sequence Error** | Wrong operation order | NL: "then" → TDL: reversed order |
| **Missing Step** | Required action omitted | NL: "pick and place" → TDL: only pick |
| **Parameter Error** | Velocity/force mismatch | NL: "slowly" → TDL: fast velocity |
| **Safety Concern** | Unsafe motion pattern | Sudden movement without approach |

---

## 3. Test Dataset Construction

### 3.1 Dataset Structure

```python
TEST_DATASET = {
    "positive_examples": [
        {
            "id": "POS-001",
            "natural_language": "Transfer box from A to B",
            "tdl_code": "[correct TDL]",
            "expected_verdict": "PASS",
            "metadata": {
                "complexity": "simple",
                "task_type": "pick_and_place",
                "objects": ["box"],
                "locations": ["A", "B"]
            }
        },
        # ... 200 examples
    ],
    "negative_examples": {
        "syntax_errors": [
            {
                "id": "NEG-SYN-001",
                "natural_language": "Move to position A",
                "tdl_code": "[TDL with missing semicolon]",
                "expected_verdict": "FAIL",
                "error_type": "syntax",
                "error_location": "line 15",
                "error_description": "Missing semicolon"
            },
            # ... 100 examples
        ],
        "semantic_errors": [
            {
                "id": "NEG-SEM-001",
                "natural_language": "Pick the red cube from A",
                "tdl_code": "[TDL referencing blue_cube]",
                "expected_verdict": "FAIL",
                "error_type": "semantic",
                "error_subtype": "object_mismatch",
                "error_description": "Color mismatch: red vs blue"
            },
            # ... 100 examples
        ],
        "safety_errors": [
            {
                "id": "NEG-SAF-001",
                "natural_language": "Move to position B",
                "tdl_code": "[TDL with z < 0]",
                "expected_verdict": "FAIL",
                "error_type": "safety",
                "error_subtype": "collision_risk",
                "error_description": "Z-coordinate below ground"
            },
            # ... 100 examples
        ],
        "consistency_errors": [
            {
                "id": "NEG-CON-001",
                "natural_language": "Move to safe position",
                "tdl_code": "[TDL referencing undefined pose]",
                "expected_verdict": "FAIL",
                "error_type": "consistency",
                "error_subtype": "undefined_reference",
                "error_description": "Reference to undefined position"
            },
            # ... 100 examples
        ]
    }
}
```

### 3.2 Error Injection Strategy

#### **자동 오류 주입 (Synthetic)**

```python
class ErrorInjector:
    """자동으로 오류를 주입하여 negative examples 생성"""

    def inject_syntax_error(self, correct_tdl: str) -> str:
        """문법 오류 주입"""
        errors = [
            self._remove_semicolon,
            self._remove_bracket,
            self._wrong_keyword,
            self._missing_parameter,
        ]
        return random.choice(errors)(correct_tdl)

    def inject_semantic_error(self, correct_tdl: str, nl: str) -> str:
        """의미 오류 주입"""
        errors = [
            self._swap_objects,       # 물체 바꾸기
            self._swap_locations,     # 위치 바꾸기
            self._reverse_sequence,   # 순서 뒤집기
            self._change_velocity,    # 속도 변경
        ]
        return random.choice(errors)(correct_tdl, nl)

    def inject_safety_error(self, correct_tdl: str) -> str:
        """안전 오류 주입"""
        errors = [
            self._exceed_reach,       # 좌표 범위 초과
            self._negative_z,         # Z 음수 만들기
            self._excessive_velocity, # 속도 한계 초과
            self._excessive_accel,    # 가속도 한계 초과
        ]
        return random.choice(errors)(correct_tdl)

    def _remove_semicolon(self, tdl: str) -> str:
        """무작위 줄의 세미콜론 제거"""
        lines = tdl.split('\n')
        target_lines = [i for i, line in enumerate(lines) if ';' in line]
        if target_lines:
            idx = random.choice(target_lines)
            lines[idx] = lines[idx].replace(';', '', 1)
        return '\n'.join(lines)

    def _swap_objects(self, tdl: str, nl: str) -> str:
        """물체 이름 바꾸기"""
        # NL에서 "red cube" → TDL에서 "red" → "blue"로 변경
        # 간단한 예: "box" → "cube"
        return tdl.replace("box", "cube")

    def _exceed_reach(self, tdl: str) -> str:
        """좌표를 도달 불가능한 범위로 변경"""
        # PosX(300, 200, 50, ...) → PosX(3000, 2000, 500, ...)
        import re
        pattern = r'PosX\((\d+),\s*(\d+),\s*(\d+),'

        def multiply_coords(match):
            x, y, z = match.groups()
            return f'PosX({int(x)*10}, {int(y)*10}, {int(z)*10},'

        return re.sub(pattern, multiply_coords, tdl)
```

### 3.3 Dataset Size Target

| Category | Target Size | Rationale |
|----------|-------------|-----------|
| Positive (Correct) | 200 | Baseline for correct patterns |
| Syntax Errors | 100 | Critical for catching basic errors |
| Semantic Errors | 150 | Core validation challenge |
| Safety Errors | 100 | Critical for safety guarantee |
| Consistency Errors | 50 | Less common but important |
| **Total** | **600** | Sufficient for validation |

### 3.4 Complexity Distribution

```python
COMPLEXITY_DISTRIBUTION = {
    "simple": 40%,      # Single action (move, pick, place)
    "moderate": 40%,    # Pick-and-place sequence
    "complex": 15%,     # Multiple objects, conditional logic
    "edge_case": 5%,    # Unusual scenarios
}
```

---

## 4. Architecture Design

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   V&V Orchestrator                          │
│  (Coordinates validation pipeline)                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► Level 1: Syntax Validator (Rule-based)
             │   └─► PASS/FAIL + Error details
             │
             ├─► Level 2: Safety Validator (Rule-based)
             │   └─► PASS/FAIL + Safety warnings
             │
             ├─► Level 3: Consistency Validator (Rule-based)
             │   └─► PASS/FAIL + Consistency issues
             │
             └─► Level 4: Semantic Validator (LLM-based)
                 ├─► Stage 1: Quick Check
                 │   └─► High confidence → Done
                 └─► Stage 2: Detailed Analysis (if low confidence)
                     └─► PASS/FAIL + Detailed reasoning

                 ↓
        ┌────────────────────┐
        │  Aggregator        │
        │  - Combine results │
        │  - Calculate score │
        │  - Generate report │
        └────────────────────┘
                 ↓
        ┌────────────────────┐
        │  V&V Report        │
        │  - Overall verdict │
        │  - Confidence      │
        │  - Issues list     │
        │  - Recommendations │
        └────────────────────┘
```

### 4.2 Validation Flow

```python
def validate(nl: str, tdl: str, robot_spec: RobotSpec, level: str = "FULL"):
    """
    Multi-level validation pipeline

    Args:
        nl: Natural language instruction
        tdl: Generated TDL code
        robot_spec: Robot specifications for safety checks
        level: "BASIC", "STANDARD", or "FULL"

    Returns:
        VVReport with overall verdict and detailed results
    """

    results = {}

    # ===== LEVEL 1: SYNTAX (Always) =====
    print("[V&V] Level 1: Syntax Validation...")
    results['syntax'] = syntax_validator.validate(tdl)

    if not results['syntax'].passed:
        # Syntax error → FAIL immediately
        return VVReport(
            verdict="FAIL",
            level_failed="SYNTAX",
            confidence=100,  # 확실한 오류
            results=results,
            message="Syntax errors detected - cannot proceed"
        )

    # ===== LEVEL 2: SAFETY (Always) =====
    print("[V&V] Level 2: Safety Validation...")
    results['safety'] = safety_validator.validate(tdl, robot_spec)

    if not results['safety'].passed:
        # Safety error → FAIL immediately
        return VVReport(
            verdict="FAIL",
            level_failed="SAFETY",
            confidence=100,  # 확실한 위험
            results=results,
            message="Safety violations detected"
        )

    # ===== LEVEL 3: CONSISTENCY (STANDARD+) =====
    if level in ["STANDARD", "FULL"]:
        print("[V&V] Level 3: Consistency Validation...")
        results['consistency'] = consistency_validator.validate(tdl)

        # Consistency issues → WARNING (not critical)
        if not results['consistency'].passed:
            results['warnings'] = results['consistency'].issues

    # ===== LEVEL 4: SEMANTICS (FULL only) =====
    if level == "FULL":
        print("[V&V] Level 4: Semantic Validation...")

        # Stage 1: Quick check
        quick_result = semantic_validator.quick_check(nl, tdl)

        if quick_result.confidence >= 80:
            # High confidence → Trust result
            results['semantic'] = quick_result
        else:
            # Low confidence → Detailed analysis
            print("[V&V] Low confidence, performing detailed analysis...")
            detailed_result = semantic_validator.detailed_analysis(nl, tdl)
            results['semantic'] = detailed_result

        if not results['semantic'].passed:
            return VVReport(
                verdict="FAIL",
                level_failed="SEMANTIC",
                confidence=results['semantic'].confidence,
                results=results,
                message="Semantic mismatch detected"
            )

    # ===== AGGREGATE RESULTS =====
    overall_score = calculate_overall_score(results)
    overall_verdict = "PASS" if overall_score >= 0.85 else "FAIL"

    return VVReport(
        verdict=overall_verdict,
        score=overall_score,
        confidence=calculate_confidence(results),
        results=results,
        recommendations=generate_recommendations(results)
    )
```

### 4.3 Class Hierarchy

```python
# validator/base.py
class BaseValidator(ABC):
    @abstractmethod
    def validate(self, tdl: str, **kwargs) -> ValidationResult:
        pass

# validator/syntax_validator.py
class SyntaxValidator(BaseValidator):
    def validate(self, tdl: str) -> ValidationResult:
        issues = []
        issues.extend(self._check_structure(tdl))
        issues.extend(self._check_definitions(tdl))
        issues.extend(self._check_commands(tdl))
        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            category="syntax"
        )

# validator/safety_validator.py
class SafetyValidator(BaseValidator):
    def validate(self, tdl: str, robot_spec: RobotSpec) -> ValidationResult:
        issues = []
        issues.extend(self._check_reachability(tdl, robot_spec))
        issues.extend(self._check_velocity_limits(tdl))
        issues.extend(self._check_collision_risk(tdl))
        return ValidationResult(
            passed=len([i for i in issues if i.severity == "CRITICAL"]) == 0,
            issues=issues,
            category="safety"
        )

# validator/semantic_validator.py
class SemanticValidator(BaseValidator):
    def __init__(self, llm_client):
        self.llm = llm_client

    def quick_check(self, nl: str, tdl: str) -> ValidationResult:
        prompt = self._build_quick_prompt(nl, tdl)
        response = self.llm.generate(prompt)
        result = self._parse_quick_response(response)
        return result

    def detailed_analysis(self, nl: str, tdl: str) -> ValidationResult:
        prompt = self._build_detailed_prompt(nl, tdl)
        response = self.llm.generate(prompt)
        result = self._parse_detailed_response(response)
        return result
```

---

## 5. Evaluation Metrics

### 5.1 Primary Metrics

#### **Detection Performance**

```python
# Confusion Matrix
#                 Predicted
#              PASS    FAIL
# Actual PASS   TP      FP
#        FAIL   FN      TN

Precision = TP / (TP + FP)  # 검출한 오류 중 실제 오류 비율
Recall = TP / (TP + FN)     # 실제 오류 중 검출한 비율
F1-Score = 2 * P * R / (P + R)
Accuracy = (TP + TN) / Total
```

**목표:**
- Overall F1-Score: **≥ 0.90**
- Safety Recall: **≥ 0.99** (위험한 것을 놓치면 안됨!)
- Syntax Precision: **≥ 0.95** (오탐 최소화)

#### **Validation Quality**

```python
# 각 validation level별 성능
syntax_f1 = f1_score(y_true_syntax, y_pred_syntax)
safety_f1 = f1_score(y_true_safety, y_pred_safety)
semantic_f1 = f1_score(y_true_semantic, y_pred_semantic)

# Weighted average
overall_f1 = (
    syntax_f1 * 0.3 +    # 30% weight
    safety_f1 * 0.4 +    # 40% weight (most important)
    semantic_f1 * 0.3    # 30% weight
)
```

### 5.2 Secondary Metrics

#### **Efficiency**

```python
avg_validation_time = total_time / num_samples
time_by_level = {
    "syntax": avg_syntax_time,
    "safety": avg_safety_time,
    "semantic": avg_semantic_time
}
```

**목표:**
- Syntax validation: **< 0.1s** per sample
- Safety validation: **< 0.2s** per sample
- Semantic validation (quick): **< 2s** per sample
- Semantic validation (detailed): **< 5s** per sample

#### **Confidence Calibration**

```python
# LLM confidence vs actual accuracy 상관관계
confidence_bins = [0-20, 20-40, 40-60, 60-80, 80-100]
for bin in confidence_bins:
    samples_in_bin = get_samples_with_confidence(bin)
    actual_accuracy = calculate_accuracy(samples_in_bin)
    print(f"Confidence {bin}: Actual accuracy {actual_accuracy}")

# 목표: High correlation (confidence 높을 때 accuracy도 높아야 함)
```

### 5.3 Ablation Study Design

```python
ABLATION_EXPERIMENTS = {
    "baseline": {
        "name": "Rule-based Only",
        "components": ["syntax", "safety", "consistency"],
        "expected_performance": "High precision, lower recall on semantic"
    },
    "llm_only": {
        "name": "LLM-based Only",
        "components": ["semantic_validator"],
        "expected_performance": "Good semantic, may miss syntax errors"
    },
    "hybrid_no_semantic": {
        "name": "Hybrid without Semantic",
        "components": ["syntax", "safety", "consistency"],
        "expected_performance": "Similar to baseline"
    },
    "hybrid_full": {
        "name": "Hybrid Full (Proposed)",
        "components": ["syntax", "safety", "consistency", "semantic"],
        "expected_performance": "Best overall performance"
    }
}
```

**비교 지표:**
- Detection rate (Recall)
- False positive rate
- Validation time
- F1-score

**예상 결과:**
```
Method                  | Syntax F1 | Safety F1 | Semantic F1 | Overall F1
------------------------|-----------|-----------|-------------|------------
Rule-based Only         |   0.95    |   0.97    |    0.70     |   0.87
LLM-based Only          |   0.75    |   0.80    |    0.92     |   0.82
Hybrid Full (Proposed)  |   0.95    |   0.97    |    0.90     |   0.94
```

### 5.4 Case Study Categories

논문에 포함할 대표적인 케이스:

1. **Complex Semantic Error** (LLM의 우수성 입증)
   - NL: "Place the fragile glass gently"
   - TDL: velocity=1000 (너무 빠름)
   - Rule-based: PASS (문법/안전 OK)
   - LLM: FAIL (semantic mismatch: "gently" vs high velocity)

2. **Subtle Safety Issue** (Rule-based의 확실성 입증)
   - TDL: PosX(1500, 1000, 500, ...) for UR10E (reach=1300mm)
   - Rule-based: FAIL (exceeds reach)
   - LLM: May PASS (doesn't know robot spec)

3. **Ambiguous Case** (Hybrid의 장점 입증)
   - NL: "Move to A then B"
   - TDL: goes to B then A (순서 반대)
   - Rule-based: PASS (문법/안전 OK)
   - LLM: FAIL (sequence mismatch)
   - Hybrid: FAIL (LLM catches it)

---

## 6. Implementation Timeline

### Week 1-2: Rule-based Validators
- **Day 1-3**: Syntax Validator
  - TDL parsing
  - Structure validation
  - Command validation

- **Day 4-7**: Safety Validator
  - Reachability check
  - Velocity/acceleration limits
  - Collision prevention

- **Day 8-10**: Consistency Validator
  - Reference validation
  - Sequence checking
  - Naming conventions

- **Day 11-14**: Testing & Refinement
  - Unit tests for each validator
  - Error message refinement
  - Performance optimization

### Week 3: LLM-based Semantic Validator
- **Day 1-2**: Prompt Design
  - Quick check prompt
  - Detailed analysis prompt
  - Few-shot examples

- **Day 3-5**: LLM Integration
  - API wrapper
  - Response parsing
  - Error handling

- **Day 6-7**: Confidence Calibration
  - Test on labeled data
  - Adjust confidence thresholds
  - Optimize prompts

### Week 4: Integration & Evaluation
- **Day 1-3**: Orchestrator Implementation
  - Pipeline integration
  - Score aggregation
  - Report generation

- **Day 4-5**: Test Dataset Construction
  - Error injection
  - Manual curation
  - Labeling

- **Day 6-7**: Evaluation Experiments
  - Run ablation studies
  - Collect metrics
  - Generate visualizations

---

## 다음 단계

이제 상세 설계가 완료되었습니다. 다음 중 선택해주세요:

### Option 1: 바로 구현 시작 ⭐
- Week 1 Day 1-3부터 시작 (Syntax Validator)
- 코드 스켈레톤 생성
- 첫 번째 규칙 구현

### Option 2: Test Dataset 먼저 구축
- 정상 TDL 예제 수집
- 오류 주입 스크립트 작성
- Labeling 시작

### Option 3: Prompt Engineering 먼저
- Few-shot examples 작성
- LLM 프롬프트 테스트
- Confidence calibration

어떤 것부터 시작하시겠습니까?

제 추천은 **Option 1 (구현 시작)**입니다:
- 규칙 기반 validator는 빠르게 구현 가능
- 테스트하면서 필요한 규칙 발견 가능
- Dataset과 Prompt는 병렬로 진행 가능

구현을 시작할까요?
