# Robot Selector - 적합 로봇 탐색 프로그램

TDL 파일을 분석하여 작업에 적합한 로봇을 자동으로 추천하는 프로그램입니다.

## 🎯 주요 기능

### 1. TDL 문서 분석
- **Payload 요구사항**: 물체 무게를 기반으로 필요한 payload 계산
- **Reach 요구사항**: 작업 좌표를 분석하여 필요한 reach 계산
- **속도/가속도 범위**: TDL 내 모든 이동 명령의 속도/가속도 범위 추출
- **기능 요구사항**: Gripper, 용접, 힘 제어 등 필요한 기능 파악
- **작업 복잡도**: 0-10점 척도로 작업 복잡도 계산

### 2. 로봇 매칭 알고리즘
- **적합도 점수**: 100점 만점으로 각 로봇 평가
  - Payload 적합성: 40점
  - Reach 적합성: 40점
  - Repeatability: 10점
  - 에너지 효율: 10점
- **안전 마진**: Payload 및 Reach의 안전 여유 계산
- **상세 추천 이유**: 각 로봇이 적합한 이유 설명

### 3. 다양한 실행 모드
- 단일 TDL 파일 분석
- 전체 폴더 스캔
- 보고서 저장 (TXT, JSON)

## 📁 파일 구조

```
robot_selector/
├── main.py              # 메인 프로그램
├── tdl_analyzer.py      # TDL 분석기
├── robot_matcher.py     # 로봇 매칭 알고리즘
├── robots_db.json       # 로봇 데이터베이스
└── README.md            # 이 문서
```

## 🚀 사용 방법

### 기본 사용법

```bash
cd robot_selector

# 단일 TDL 파일 분석
python main.py ../output/transfer_test.tdl

# 전체 output 폴더 스캔
python main.py --scan-all

# 보고서 저장
python main.py ../output/task.tdl --save-report
```

### 고급 옵션

```bash
# 최소 적합도 점수 지정 (60점 이상만 표시)
python main.py ../output/task.tdl --min-score 60

# 커스텀 출력 디렉토리 지정
python main.py --scan-all --output-dir ../my_tasks

# 커스텀 로봇 데이터베이스 사용
python main.py ../output/task.tdl --robots-db custom_robots.json

# 도움말
python main.py --help
```

## 📊 출력 예시

### 상세 분석 모드

```
======================================================================
STEP 1: Analyzing TDL Document
======================================================================
============================================================
Robot Requirements Analysis
============================================================
Required Payload: 6.00 kg
Required Reach: 430 mm (0.43 m)
Velocity Range: 50 - 100 mm/s
Acceleration Range: 50 - 50 mm/s²

Capabilities:
  - Gripper Required: Yes
  - Welding Required: No
  - Force Control Required: No

Complexity:
  - Total Commands: 15
  - Complexity Score: 5.40/10
============================================================

======================================================================
STEP 2: Finding Suitable Robots
======================================================================

ROBOT RECOMMENDATIONS (Ranked by Suitability):
======================================================================

1. UNIVERSAL UR10E (Payload: 12.5kg, Reach: 1.3m)
   Suitability Score: 100.0/100
   Status: SUITABLE
   Payload: 12.5 kg (Margin: +108.3%)
   Reach: 1.30 m (Margin: +202.6%)
   Repeatability: 0.100 mm
   Energy Class: A
   Notes:
     - Excellent payload capacity
     - Excellent reach
     - Energy efficient (Class A)

RECOMMENDED ROBOT:
======================================================================
  UNIVERSAL UR10E (Payload: 12.5kg, Reach: 1.3m)
  Suitability Score: 100.0/100
```

### 스캔 모드

```
[INFO] Found 5 TDL file(s)

======================================================================
File: transfer_task.tdl
======================================================================
Required Payload: 6.00 kg
Required Reach: 0.43 m
Task Complexity: 5.4/10

[BEST] UNIVERSAL UR10E (Payload: 12.5kg, Reach: 1.3m) (Score: 100.0/100)

======================================================================
File: welding_task.tdl
======================================================================
Required Payload: 3.00 kg
Required Reach: 0.85 m
Task Complexity: 7.2/10

[BEST] YASKAWA HC20 (Payload: 20.0kg, Reach: 1.7m) (Score: 97.0/100)
```

## 🔧 로봇 데이터베이스

`robots_db.json` 파일 형식:

```json
[
  {
    "manufacturer": "doosan",
    "model": "h2017",
    "payload_kg": 20.0,
    "reach_m": 1.7,
    "repeatability_mm": 0.05,
    "energy_class": "B"
  },
  {
    "manufacturer": "universal",
    "model": "ur10e",
    "payload_kg": 12.5,
    "reach_m": 1.3,
    "repeatability_mm": 0.1,
    "energy_class": "A"
  }
]
```

### 새 로봇 추가

데이터베이스에 로봇을 추가하려면 JSON 파일에 새 항목을 추가하세요:

```json
{
  "manufacturer": "제조사명",
  "model": "모델명",
  "payload_kg": 페이로드(kg),
  "reach_m": 도달거리(m),
  "repeatability_mm": 반복정밀도(mm),
  "energy_class": "A|B|C|D"
}
```

## 📈 분석 알고리즘 상세

### Payload 계산

물체 타입별 기본 무게:
- `box`: 5.0 kg
- `small_box`: 2.0 kg
- `large_box`: 10.0 kg
- `part`: 1.0 kg
- `component`: 1.5 kg
- `product`: 3.0 kg
- `tool`: 2.0 kg
- `workpiece`: 5.0 kg
- `default`: 5.0 kg (알 수 없는 경우)

**안전 마진**: 계산된 무게의 120% (20% 추가)

### Reach 계산

1. TDL 내 모든 `PosX(x, y, z, ...)` 좌표 추출
2. 각 좌표에서 원점까지의 거리 계산: `√(x² + y² + z²)`
3. 최대 거리 선택
4. 안전 마진 10% 추가

### 복잡도 점수 (0-10점)

- **명령어 수** (0-3점): 명령어 개수에 비례
- **기능 수** (0-3점): 필요한 기능 개수
- **특수 작업** (0-2점): 용접(1점), 힘 제어(1점)
- **Reach 요구사항** (0-2점): 1000mm 이상(1점), 1500mm 이상(2점)

### 적합도 점수 (0-100점)

**Payload 평가 (40점):**
- Margin ≥ 50%: 40점 (Excellent)
- Margin ≥ 20%: 35점 (Good)
- Margin ≥ 0%: 25점 (Adequate)
- Margin < 0%: 0점 (Insufficient)

**Reach 평가 (40점):**
- Margin ≥ 30%: 40점 (Excellent)
- Margin ≥ 10%: 35점 (Good)
- Margin ≥ 0%: 25점 (Adequate)
- Margin < 0%: 0점 (Insufficient)

**Repeatability 평가 (10점):**
- 복잡도 ≥ 7: ≤0.05mm (10점), ≤0.1mm (7점), 그 외 (4점)
- 복잡도 < 7: ≤0.1mm (10점), 그 외 (7점)

**에너지 효율 (10점):**
- Class A: 10점
- Class B: 7점
- Class C: 4점
- Class D: 2점

## 💾 보고서 저장

`--save-report` 옵션 사용 시 두 가지 형식으로 저장:

### 1. 텍스트 보고서 (`*.robot_report.txt`)
사람이 읽기 쉬운 형식

### 2. JSON 보고서 (`*.robot_report.json`)
프로그램으로 처리 가능한 형식:

```json
{
  "tdl_file": "path/to/task.tdl",
  "requirements": {
    "payload_kg": 6.0,
    "reach_mm": 430,
    "velocity_range": [50, 100],
    "acceleration_range": [50, 50],
    "capabilities": ["gripper", "pick_and_place"],
    "complexity_score": 5.4
  },
  "matches": [
    {
      "robot": {
        "manufacturer": "universal",
        "model": "ur10e",
        "payload_kg": 12.5,
        "reach_m": 1.3
      },
      "suitability_score": 100.0,
      "meets_payload": true,
      "meets_reach": true,
      "payload_margin_percent": 108.3,
      "reach_margin_percent": 202.6,
      "reasons": ["Excellent payload capacity", "Excellent reach"]
    }
  ]
}
```

## 🎓 연구 활용

### 1. 자동 로봇 선택 시스템
TDL 작업 명세 → 최적 로봇 자동 추천

### 2. 작업 복잡도 분석
다양한 작업의 복잡도 정량화 및 비교

### 3. 로봇 벤치마킹
여러 로봇의 다양한 작업에 대한 적합도 비교

### 4. 데이터 수집
- 작업 유형별 요구사항 통계
- 로봇 선택 패턴 분석
- Payload/Reach 요구사항 분포

## 🔄 워크플로우 예시

### NL2TDL → Robot Selector 파이프라인

```bash
# 1. 자연어 → TDL 생성
cd ..
python main.py -r "박스를 A에서 B로 옮겨줘" -o my_task.tdl

# 2. TDL → 로봇 추천
cd robot_selector
python main.py ../output/my_task.tdl --save-report

# 3. 결과 확인
# - output/my_task.tdl (TDL 문서)
# - output/my_task.json (메타데이터)
# - output/my_task.robot_report.txt (추천 보고서)
# - output/my_task.robot_report.json (추천 데이터)
```

## 📝 커스터마이징

### 물체 무게 변경

`tdl_analyzer.py`의 `OBJECT_WEIGHTS` 수정:

```python
OBJECT_WEIGHTS = {
    "box": 5.0,
    "heavy_box": 15.0,  # 추가
    "light_part": 0.5,  # 추가
    # ...
}
```

### 안전 마진 조정

```python
PAYLOAD_SAFETY_MARGIN = 1.3  # 30%로 변경 (기본 1.2 = 20%)
```

### 복잡도 계산 수정

`tdl_analyzer.py`의 `_calculate_complexity()` 메서드 수정

## ⚠️ 주의사항

1. **좌표계**: TDL의 PosX는 mm 단위, 로봇 DB의 reach는 m 단위
2. **안전 마진**: 계산된 요구사항에는 이미 안전 마진이 포함됨
3. **물체 무게**: 실제 물체 무게가 다를 수 있으므로 검증 필요
4. **메타데이터**: JSON 메타데이터 파일이 있으면 더 정확한 분석 가능

## 🐛 문제 해결

### "Robots database not found" 에러

```bash
# 명시적으로 DB 경로 지정
python main.py ../output/task.tdl --robots-db ./robots_db.json
```

### "No suitable robots found" 경고

- 요구사항이 너무 높은 경우
- `--min-score 0`으로 모든 로봇 확인
- 로봇 DB에 더 다양한 로봇 추가 필요

### Import 에러

```bash
# robot_selector 폴더 내에서 실행해야 함
cd robot_selector
python main.py ../output/task.tdl
```

## 📚 관련 문서

- 상위 폴더의 `README.md`: LLM-based NL2TDL 변환기
- `../rag_documents/TDLset.md`: TDL 명세 문서

---

**개발**: LLM-based NL2TDL 프로젝트의 일부
**목적**: 연구 및 교육용
