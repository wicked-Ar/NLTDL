# LLM-based NL2TDL Converter

**대형 언어 모델(LLM)을 활용한 자연어를 TDL(Task Description Language)로 변환하는 연구 프로젝트**

## 🎓 연구 개요

이 프로젝트는 **LLM을 바탕으로 사용자의 자연어 요구사항을 이해하고, 산업용 로봇을 위한 작업 명세서(TDL)를 자동 생성**하는 시스템입니다.

### 핵심 연구 질문
- LLM이 산업용 로봇 작업을 위한 자연어 요구사항을 얼마나 정확하게 이해할 수 있는가?
- LLM 기반 접근법이 기존의 규칙 기반 또는 키워드 기반 방법보다 우수한가?
- 한국어와 영어 혼용 환경에서 LLM의 성능은 어떠한가?

### 주요 특징

✅ **LLM 중심 설계**: Google Gemini API를 핵심 엔진으로 사용
✅ **자연어 이해**: 키워드 매칭 없이 순수 LLM 기반 의도 파악
✅ **다국어 지원**: 한국어, 영어 및 혼합 입력 처리
✅ **상호작용 모드**: LLM 분석 결과 검증 및 수정 기능
✅ **설명 생성**: TDL 문서에 대한 자연어 설명 자동 생성
✅ **메타데이터 저장**: 분석 과정 및 결과 추적 가능

## 📋 시스템 아키텍처

```
사용자 자연어 입력
       ↓
┌──────────────────────┐
│  LLM Requirement     │  ← Gemini API
│  Analyzer            │     (요구사항 이해)
└──────────────────────┘
       ↓
  RequirementAnalysis
  (구조화된 정보)
       ↓
┌──────────────────────┐
│  LLM TDL Generator   │  ← Gemini API
│                      │     (TDL 생성)
└──────────────────────┘
       ↓
   TDL Document
   (로봇 작업 명세서)
```

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.7 이상
- Google Gemini API 키 ([여기서 발급](https://aistudio.google.com/app/apikey))
- 인터넷 연결

**외부 라이브러리 불필요** - Python 표준 라이브러리만 사용합니다.

### 2. API 키 설정

세 가지 방법 중 하나를 선택하세요:

#### 방법 1: 설정 파일 (권장)

`config.txt` 파일을 편집:

```bash
# 주석 해제하고 API 키 입력
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

#### 방법 2: 환경 변수

```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

#### 방법 3: 커맨드 라인 인자

```bash
python main.py --api-key your_api_key_here -r "요구사항"
```

### 3. 기본 사용법

```bash
cd llm_nl2tdl

# 기본 실행
python main.py -r "박스를 A에서 B로 옮겨줘"

# 영어 입력
python main.py -r "Pick up the box from location A and place it at B"

# 혼합 입력
python main.py -r "robot이 부품을 천천히 A에서 B로 transfer"
```

## 📖 상세 사용법

### 기본 명령어

```bash
# 간단한 변환
python main.py -r "박스 옮기기"

# 출력 파일 지정
python main.py -r "용접 작업" -o welding_task.tdl

# 출력 디렉토리 지정
python main.py -r "조립하기" --output-dir results

# 콘솔에만 출력 (파일 저장 안함)
python main.py -r "이동" --print-only
```

### 고급 기능

#### 1. 상호작용 모드 (Interactive Mode)

LLM의 분석 결과를 확인하고 수정할 수 있습니다:

```bash
python main.py -r "박스를 옮겨줘" --interactive
```

실행 시 다음과 같은 프롬프트가 표시됩니다:

```
Analysis Result - Please verify:
============================================================
📋 Task: 박스를 A 위치에서 B 위치로 이동
🎯 Actions: transfer
📦 Objects: box
📍 Locations: A, B
⚙️  Constraints: None
============================================================

Is this correct? (yes/no/edit):
```

#### 2. 설명 생성 모드 (Explanation Mode)

생성된 TDL에 대한 자연어 설명을 함께 생성합니다:

```bash
python main.py -r "용접 작업" --explain
```

출력 예시:
```
============================================================
TDL Document Explanation
============================================================

이 TDL 문서는 용접 작업을 수행하는 로봇 프로세스입니다.

1. Initialize_Process: 로봇을 홈 위치로 이동하고 그리퍼를 초기화
2. Execute_Process: 지정된 위치로 이동 후 용접 작업 수행
3. Finalize_Process: 작업 완료 후 안전하게 종료

...
```

#### 3. API 키 직접 지정

```bash
python main.py --api-key AIzaSy... -r "작업 요구사항"
```

### 출력 파일

프로그램은 여러 파일을 생성합니다:

1. **TDL 파일** (`*.tdl`): 로봇 작업 명세서
2. **메타데이터** (`*.json`): 분석 과정 및 결과
3. **설명 파일** (`*.txt`): 자연어 설명 (--explain 사용 시)

예시:
```
output/
├── tdl_transfer_20251021_143000.tdl      # TDL 문서
├── tdl_transfer_20251021_143000.json     # 분석 메타데이터
└── tdl_transfer_20251021_143000.txt      # 자연어 설명
```

## 📊 사용 예시

### 예시 1: 기본 이송 작업 (한국어)

**입력:**
```bash
python main.py -r "박스를 A에서 B로 옮겨줘"
```

**LLM 분석 결과:**
```
📋 Task: 박스를 A 위치에서 B 위치로 이동
🎯 Actions: transfer
📦 Objects: box
📍 Locations: A, B
⚙️  Constraints: None
```

**생성된 TDL:** (예시)
```
HEADER
  TaskName=transfer
  Description=박스를 A 위치에서 B 위치로 이동
END_HEADER

GOAL Initialize_Process
  MoveToHome()
  InitializeGripper()
END_GOAL

GOAL Execute_Process
  MoveToPosition(position=(0, 0, 150, 0, 0, 0), velocity=100, acceleration=50)
  MoveToPosition(position=(0, 0, 60, 0, 0, 0), velocity=50.0, acceleration=50)
  GraspObject(force=50)
  MoveToPosition(position=(0, 0, 150, 0, 0, 0), velocity=50.0, acceleration=50)
  MoveToPosition(position=(300, 200, 150, 0, 0, 0), velocity=100, acceleration=50)
  MoveToPosition(position=(300, 200, 60, 0, 0, 0), velocity=50.0, acceleration=50)
  ReleaseObject()
  MoveToPosition(position=(300, 200, 150, 0, 0, 0), velocity=50.0, acceleration=50)
END_GOAL

GOAL Finalize_Process
  ReleaseObject()
  MoveToHome()
  Shutdown()
END_GOAL
```

### 예시 2: 복잡한 작업 (영어)

**입력:**
```bash
python main.py -r "Carefully pick up the component from the assembly line and weld it at station C" --explain
```

**LLM 분석 결과:**
```
📋 Task: Pick component from assembly line and weld at station C
🎯 Actions: pick, weld
📦 Objects: component
📍 Locations: assembly_line, C
⚙️  Constraints: careful
```

### 예시 3: 제약 조건 포함 (혼합)

**입력:**
```bash
python main.py -r "로봇이 부품을 천천히 조심스럽게 A에서 B로 이동" --interactive
```

**LLM 분석 결과:**
```
📋 Task: 부품을 천천히 조심스럽게 A에서 B로 이동
🎯 Actions: transfer, move
📦 Objects: part
📍 Locations: A, B
⚙️  Constraints: slow, careful
```

## 🔬 연구 활용 가이드

### 실험 데이터 수집

모든 실행은 자동으로 메타데이터를 생성합니다:

```json
{
  "actions": ["transfer"],
  "objects": ["box"],
  "locations": ["A", "B"],
  "constraints": [],
  "task_description": "박스를 A에서 B로 이동",
  "raw_input": "박스를 A에서 B로 옮겨줘"
}
```

### 성능 측정 포인트

1. **LLM 이해 정확도**: 분석된 actions, objects, locations의 정확성
2. **TDL 생성 품질**: 생성된 TDL의 실행 가능성
3. **처리 시간**: API 호출 시간 측정
4. **언어별 성능**: 한국어 vs 영어 vs 혼합

### 배치 실험 스크립트 예시

```python
# batch_experiment.py
import subprocess
import json
from pathlib import Path

test_cases = [
    "박스를 A에서 B로 옮겨줘",
    "Pick box from A to B",
    "부품을 천천히 이동",
    "Weld at position C",
    # ... 더 많은 테스트 케이스
]

results = []
for i, requirement in enumerate(test_cases):
    print(f"Test {i+1}/{len(test_cases)}: {requirement}")

    # Run the converter
    subprocess.run([
        "python", "main.py",
        "-r", requirement,
        "--output-dir", f"experiments/test_{i}",
        "-o", f"result_{i}.tdl"
    ])

    # Load and analyze results
    metadata_file = Path(f"experiments/test_{i}/result_{i}.json")
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            results.append({
                "test_id": i,
                "input": requirement,
                "analysis": metadata
            })

# Save experiment results
with open("experiments/summary.json", 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## 🛠️ 파일 구조

```
llm_nl2tdl/
├── main.py              # 메인 애플리케이션 (NL → TDL 변환)
├── llm_client.py        # Gemini API 클라이언트
├── analyzer.py          # LLM 기반 요구사항 분석기
├── tdl_generator.py     # LLM 기반 TDL 생성기
├── config.txt           # API 키 설정 파일
├── robots_db.json       # 로봇 데이터베이스
├── README.md            # 이 문서
├── output/              # 생성된 TDL 파일들 (자동 생성)
└── robot_selector/      # 🤖 적합 로봇 탐색 프로그램 (별도)
    ├── main.py          # 로봇 선택 메인 프로그램
    ├── tdl_analyzer.py  # TDL 분석기
    ├── robot_matcher.py # 로봇 매칭 알고리즘
    ├── robots_db.json   # 로봇 데이터베이스
    └── README.md        # 로봇 선택기 상세 문서
```

## 🤖 Robot Selector (추가 프로그램)

`robot_selector` 폴더에는 생성된 TDL 파일을 분석하여 적합한 로봇을 추천하는 별도 프로그램이 있습니다.

### 주요 기능
- TDL 파일에서 payload, reach 요구사항 자동 추출
- 로봇 데이터베이스와 비교하여 적합도 점수 계산
- 최적 로봇 추천 및 상세 보고서 생성

### 빠른 사용법
```bash
cd robot_selector

# 단일 TDL 파일 분석
python main.py ../output/transfer_test.tdl

# 모든 TDL 파일 스캔
python main.py --scan-all

# 상세 문서 확인
cat README.md
```

## 🔧 커스터마이징

### LLM 프롬프트 수정

`llm_client.py`의 프롬프트를 수정하여 LLM의 동작을 조정할 수 있습니다:

```python
# llm_client.py의 analyze_requirement() 메서드 내부
prompt = f"""당신은 로봇 작업 분석 전문가입니다...

[여기에 프롬프트를 수정하여 LLM의 이해도를 조정]
"""
```

### TDL 생성 규칙 변경

`llm_client.py`의 `generate_tdl()` 메서드에서 TDL 생성 규칙을 수정:

```python
# 위치 좌표 변경
4. 위치 좌표 (mm 단위):
   - A: (100, 50, 30, 0, 0, 0)  # 여기를 수정
   - B: (400, 300, 50, 0, 0, 0)
```

### 온도(Temperature) 조정

LLM의 창의성/일관성을 조정:

```python
# analyzer.py
response = self.llm_client.generate_content(prompt, temperature=0.3)  # 0.0~1.0

# 낮은 값 (0.0~0.3): 일관적이고 예측 가능한 결과
# 중간 값 (0.4~0.7): 균형잡힌 결과
# 높은 값 (0.8~1.0): 창의적이지만 불안정할 수 있음
```

## ❓ 문제 해결

### API 키 오류

```
❌ Error: Gemini API key is required!
```

**해결 방법:**
1. API 키가 올바른지 확인
2. `config.txt`에서 주석(`#`)이 제거되었는지 확인
3. 환경 변수가 올바르게 설정되었는지 확인

### API 연결 실패

```
❌ API connection test failed!
```

**해결 방법:**
1. 인터넷 연결 확인
2. API 키의 유효성 확인
3. Google AI Studio에서 API 사용이 활성화되었는지 확인

### JSON 파싱 오류

```
Failed to parse LLM response as JSON
```

**해결 방법:**
1. LLM 응답이 불안정할 수 있음 - 재시도
2. `temperature` 값을 낮춰서 더 일관된 응답 유도
3. 프롬프트를 더 구체적으로 수정

### TDL 검증 실패

```
⚠️  Warning: TDL validation failed
```

**해결 방법:**
1. `--no-validation` 플래그로 검증 스킵 (테스트용)
2. LLM 프롬프트를 더 상세하게 수정
3. `--interactive` 모드로 분석 결과 수동 확인

## 📈 연구 결과 분석

### 메타데이터 분석 스크립트

```python
import json
from pathlib import Path
from collections import Counter

# Load all metadata files
metadata_files = Path("output").glob("*.json")

all_actions = []
all_constraints = []

for file in metadata_files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        all_actions.extend(data.get("actions", []))
        all_constraints.extend(data.get("constraints", []))

# Analyze
print("Most common actions:", Counter(all_actions).most_common(5))
print("Most common constraints:", Counter(all_constraints).most_common(5))
```

## 🎯 향후 개선 방향

- [ ] 다른 LLM 모델 지원 (GPT-4, Claude 등)
- [ ] TDL 실행 시뮬레이터 통합
- [ ] 웹 인터페이스 개발
- [ ] 다중 로봇 협업 작업 지원
- [ ] 실시간 피드백 기반 학습

## 📝 라이선스

연구 및 교육 목적으로 자유롭게 사용 가능합니다.

## 🙋 지원

문제가 발생하면 다음을 확인하세요:

1. Google Gemini API 상태: https://ai.google.dev/
2. API 키 설정 확인
3. Python 버전 확인 (3.7+)

---

**🎓 Research Project: LLM-based Natural Language Understanding for Industrial Robotics**

*이 프로젝트는 LLM을 활용한 자연어 이해 기술을 산업용 로봇 분야에 적용하는 연구입니다.*
