"""
LLM Client for Google Gemini API
Handles all communication with the Gemini API for natural language understanding.
"""
import json
import os
from typing import Dict, Any, Optional
import urllib.request
import urllib.error


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google AI Studio API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.5-flash"

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))

            # Debug: Print response structure for troubleshooting
            # print(f"DEBUG: Response keys: {response_data.keys()}")

            # Extract text from response
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]

                # Check finish reason
                finish_reason = candidate.get("finishReason", "")
                if finish_reason == "MAX_TOKENS":
                    # Response was cut off, but we can still try to get partial content
                    pass

                if "content" in candidate:
                    content = candidate["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        parts = content["parts"]
                        if "text" in parts[0]:
                            return parts[0]["text"]

                    # Handle case where content exists but parts is empty or missing
                    # This can happen with MAX_TOKENS on very short responses
                    if finish_reason == "MAX_TOKENS" and "parts" not in content:
                        # Return empty string for test connection
                        return ""

            # If normal path fails, check for error messages in response
            if "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown error")
                raise Exception(f"API returned error: {error_msg}")

            # Last resort: return full response for debugging
            raise Exception(f"Unexpected response format. Response: {json.dumps(response_data, indent=2)}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_body)
                if "error" in error_json:
                    error_msg = error_json["error"].get("message", error_body)
                    raise Exception(f"HTTP {e.code}: {error_msg}")
            except json.JSONDecodeError:
                pass
            raise Exception(f"Gemini API HTTP error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"Gemini API connection error: {e.reason}")
        except Exception as e:
            if "Gemini API" in str(e) or "HTTP" in str(e) or "API returned error" in str(e):
                raise
            raise Exception(f"Gemini API error: {str(e)}")

    def analyze_requirement(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user requirement and extract structured information.

        Args:
            user_input: Natural language requirement

        Returns:
            Dictionary with actions, objects, locations, constraints
        """
        prompt = f"""당신은 로봇 작업 분석 전문가입니다. 사용자의 자연어 요구사항을 분석하여 구조화된 정보를 추출해주세요.

사용자 입력: "{user_input}"

다음 정보를 JSON 형식으로 추출해주세요:

1. actions: 수행할 동작 리스트 (예: pick, place, move, transfer, wait, weld, assemble 등)
2. objects: 대상 물체 리스트 (예: box, part, component 등)
3. locations: 위치 정보 리스트 (예: A, B, home, start 등)
4. coordinates: 위치별 좌표 딕셔너리 (예: {{"A": [0, 0, 0, 0, 0, 0], "B": [100, 200, 50, 0, 0, 0]}})
5. constraints: 제약 조건 리스트 (예: slow, fast, careful, precise 등)
6. task_description: 작업에 대한 간단한 설명 (1-2 문장)

주의사항:
- "옮기다", "전달하다", "이송하다"는 transfer로 변환
- "집다", "잡다", "픽업"은 pick으로 변환
- "놓다", "배치하다", "내려놓다"는 place로 변환
- transfer 동작은 자동으로 pick + move + place를 포함합니다
- 영어와 한국어 모두 지원
- 사용자가 좌표를 명시한 경우 (예: A(0,0,0,0,0,0)), 반드시 정확히 추출하세요
- 좌표 형식: [x, y, z, rx, ry, rz] (단위: mm, degrees)
- 좌표가 명시되지 않은 경우 coordinates는 빈 딕셔너리로 설정

응답은 반드시 유효한 JSON 형식으로만 제공하세요. 다른 설명은 포함하지 마세요.

JSON 형식:
{{
  "actions": ["action1", "action2"],
  "objects": ["object1"],
  "locations": ["location1", "location2"],
  "coordinates": {{"location1": [x, y, z, rx, ry, rz], "location2": [x, y, z, rx, ry, rz]}},
  "constraints": ["constraint1"],
  "task_description": "작업 설명"
}}"""

        response = self.generate_content(prompt, temperature=0.3)

        # Extract JSON from response
        try:
            # Try to find JSON in response
            response = response.strip()
            if "```json" in response:
                # Extract from code block
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                # Extract from code block without language
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response

            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")

    def generate_tdl(
        self,
        task_description: str,
        actions: list,
        objects: list,
        locations: list,
        constraints: list,
        coordinates: dict = None
    ) -> str:
        """
        Generate TDL document using LLM.

        Args:
            task_description: Task description
            actions: List of actions
            objects: List of objects
            locations: List of locations
            constraints: List of constraints
            coordinates: Dictionary mapping locations to coordinates (optional)

        Returns:
            Complete TDL document as string
        """
        # Format coordinates if provided
        coordinates_str = ""
        if coordinates and isinstance(coordinates, dict) and len(coordinates) > 0:
            coordinates_str = "\n사용자 지정 좌표:\n"
            for loc, coords in coordinates.items():
                if isinstance(coords, list) and len(coords) == 6:
                    coordinates_str += f"   - {loc}: PosX({coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}, {coords[4]}, {coords[5]})\n"

        # Format objects with weights
        objects_str = ', '.join(objects) if objects else '없음'

        prompt = f"""당신은 TDL(Task Description Language) 문서 생성 전문가입니다.

다음 정보를 바탕으로 완전한 TDL 문서를 생성해주세요:

작업 설명: {task_description}
동작: {', '.join(actions) if actions else '없음'}
대상 물체: {objects_str}
위치: {', '.join(locations) if locations else '없음'}
제약 조건: {', '.join(constraints) if constraints else '없음'}{coordinates_str}

TDL 문서 작성 규칙:

1. HEADER 섹션 (필수):
```
HEADER
  TASK_NAME: "작업 이름"
  DESCRIPTION: "작업 설명"
  OBJECT: "대상 물체 이름"
  PAYLOAD_KG: 예상_무게
END_HEADER
```
**중요**:
- OBJECT: 대상 물체 이름 (예: box, part, component 등)
- PAYLOAD_KG: 물체의 예상 무게 (kg 단위)
  - box → 5.0
  - small_box → 2.0
  - large_box → 10.0
  - part → 1.0
  - component → 1.5
  - product → 3.0
  - tool → 2.0
  - workpiece → 5.0
  - 알 수 없으면 → 5.0
- 여러 물체가 있으면 총 무게를 합산

2. 기본 구조 (GOAL 형식):
```
GOAL Initialize_Process()
{{
    SPAWN command1() WITH WAIT;
    SPAWN command2() WITH WAIT;
}}

GOAL Execute_Process()
{{
    SPAWN command3() WITH WAIT;
}}

GOAL Finalize_Process()
{{
    SPAWN command4() WITH WAIT;
}}
```

3. 핵심 명령어 (표준 TDL 명세):

**위치 정의:**
- PosX(x, y, z, rx, ry, rz): 데카르트 좌표 (mm, degrees)
- PosJ(j1, j2, j3, j4, j5, j6): 관절 좌표 (degrees)
- Trans(x, y, z, rx, ry, rz): 상대 오프셋

**이동 명령:**
- MoveJoint(target_pose, velocity, acceleration, tool=0, blending_radius=0): 관절 보간 이동
- MoveLinear(target_pose, velocity, acceleration, tool=0, blending_radius=0): 직선 이동
- MoveCircular(via_pose, target_pose, velocity, acceleration, tool=0, blending_radius=0): 원호 이동

**시간 제어:**
- Delay(duration_sec): 대기

**I/O 제어:**
- SetDigitalOutput(port, value): 디지털 출력
- GetDigitalInput(port): 디지털 입력 읽기
- WaitForDigitalInput(port, value, timeout_sec): 디지털 입력 대기

**용접 (Arc Welding):**
- SetArcCondition(condition_id, current, voltage, wire_feed_speed, gas_pre_flow_time, gas_post_flow_time)
- ConfigureArcWeaving(pattern, amplitude, frequency, dwell_time): pattern = "zigzag", "sinusoidal", "trapezoidal", "circular"
- ArcOn(): 아크 시작
- ArcOff(): 아크 종료

**힘 제어:**
- StartCompliance(stiffness, ref_coord): 컴플라이언스 시작
- ReleaseCompliance(): 컴플라이언스 해제
- SetDesiredForce(force, axis, ref_coord): 목표 힘 설정

**흐름 제어:**
- Label(name): 레이블 정의
- GoTo(label): 레이블로 이동
- If(condition): 조건 시작
- Else(): else 블록
- EndIf(): 조건 종료

4. 위치 좌표 (mm 단위):
   **중요: 위에 "사용자 지정 좌표"가 제공된 경우, 반드시 해당 좌표를 정확히 사용하세요!**
   **사용자 지정 좌표가 없는 경우에만 아래 기본 좌표를 사용하세요:**
   - A: PosX(0, 0, 50, 0, 0, 0)
   - B: PosX(300, 200, 50, 0, 0, 0)
   - C: PosX(600, 0, 50, 0, 0, 0)
   - Home: PosX(0, 0, 200, 0, 0, 0)

5. Transfer 동작 시퀀스 (pick-and-place):
```
GOAL Execute_Process()
{{
    // 1. Approach source (safe height: +100mm)
    SPAWN MoveLinear(target_pose=PosX(0, 0, 150, 0, 0, 0), velocity=100, acceleration=50, tool=0, blending_radius=0) WITH WAIT;

    // 2. Descend to grasp height (+10mm)
    SPAWN MoveLinear(target_pose=PosX(0, 0, 60, 0, 0, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;

    // 3. Grasp (close gripper - use digital output)
    SPAWN SetDigitalOutput(port=1, value=1) WITH WAIT;
    SPAWN Delay(duration_sec=0.5) WITH WAIT;

    // 4. Lift from source
    SPAWN MoveLinear(target_pose=PosX(0, 0, 150, 0, 0, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;

    // 5. Move to target (above)
    SPAWN MoveLinear(target_pose=PosX(300, 200, 150, 0, 0, 0), velocity=100, acceleration=50, tool=0, blending_radius=0) WITH WAIT;

    // 6. Lower to place height
    SPAWN MoveLinear(target_pose=PosX(300, 200, 60, 0, 0, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;

    // 7. Release (open gripper)
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT;
    SPAWN Delay(duration_sec=0.5) WITH WAIT;

    // 8. Retract to safe height
    SPAWN MoveLinear(target_pose=PosX(300, 200, 150, 0, 0, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
}}
```

6. 속도/가속도 설정:
   - 기본 속도: 100 (mm/s or %)
   - 기본 가속도: 50 (mm/s² or %)
   - slow 제약 시: velocity=50
   - fast 제약 시: velocity=150
   - 정밀 접근 시: velocity를 50% 감소

7. Initialize_Process 예시:
```
GOAL Initialize_Process()
{{
    SPAWN MoveJoint(target_pose=PosJ(0, 0, 90, 0, 90, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT;  // Open gripper
}}
```

8. Finalize_Process 예시:
```
GOAL Finalize_Process()
{{
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT;  // Ensure gripper open
    SPAWN MoveJoint(target_pose=PosJ(0, 0, 90, 0, 90, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
    SPAWN End() WITH WAIT;
}}
```

9. 중요 규칙:
   - 모든 명령은 SPAWN ... WITH WAIT; 또는 SPAWN ...; 형식
   - WITH WAIT는 완료를 기다림, 없으면 비동기
   - 각 GOAL은 {{}} 중괄호로 감쌈
   - 주석은 //로 시작
   - 위치는 반드시 PosX() 또는 PosJ() 함수 사용

완전하고 실행 가능한 TDL 문서를 생성하세요. 표준 TDL 명세를 정확히 따르세요. 다른 설명 없이 TDL 문서만 출력하세요."""

        response = self.generate_content(prompt, temperature=0.5, max_tokens=8000)

        # Clean response
        response = response.strip()
        if "```" in response:
            # Extract from code block
            start = response.find("```")
            # Skip the first ``` line
            start = response.find("\n", start) + 1
            end = response.find("```", start)
            response = response[start:end].strip()

        return response


def test_connection(api_key: str) -> bool:
    """
    Test Gemini API connection.

    Args:
        api_key: API key to test

    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = GeminiClient(api_key)
        response = client.generate_content("Hello", temperature=0.1, max_tokens=50)
        # Even empty response means API is working
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
