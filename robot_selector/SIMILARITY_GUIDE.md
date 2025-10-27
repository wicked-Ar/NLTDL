# Robot Similarity Analyzer - 로봇 유사도 분석 및 교체 가이드

로봇 교체 시나리오를 위한 유사도 기반 로봇 추천 시스템입니다.

## 🎯 개요

생산 라인에서 로봇을 교체해야 할 때 (고장, 업그레이드, 표준화 등), 기존 로봇과 유사한 특성을 가진 로봇을 찾아 최소한의 공정 변경으로 교체할 수 있도록 돕습니다.

### 주요 사용 사례

1. **로봇 고장/단종**: 기존 로봇의 대체품 선정
2. **생산 라인 확장**: 기존 로봇과 유사한 로봇으로 추가 설치
3. **플릿 표준화**: 여러 제조사의 로봇을 통일된 플랫폼으로 전환
4. **업그레이드**: 성능은 향상되면서도 기존 설정을 재사용할 수 있는 로봇 선정

## 📁 새로 추가된 파일

```
robot_selector/
├── robot_similarity.py          # 유사도 계산 핵심 로직
├── find_replacement.py          # 독립 실행 스크립트 (유사도 검색)
├── test_similarity.py           # 테스트 스크립트
├── robots_db_extended.json      # 확장된 로봇 데이터베이스 (form factor 정보 포함)
└── SIMILARITY_GUIDE.md          # 이 문서
```

**기존 파일은 모두 유지됩니다!**
- `main.py`: 유사도 검색 옵션이 추가되었지만 기존 기능은 그대로 작동
- `robot_matcher.py`: 변경 없음
- `tdl_analyzer.py`: 변경 없음
- `robots_db.json`: 변경 없음 (새로운 `robots_db_extended.json` 추가)

## 🔍 유사도 평가 기준 (100점 만점)

### 1. Specification Similarity (50점)

물리적 사양의 유사성을 평가합니다.

#### Payload Similarity (20점)
- ±10% 이내: 20점 (매우 유사)
- ±20% 이내: 15점 (유사)
- ±30% 이내: 10점
- ±50% 이내: 5점
- 그 이상: 0점

#### Reach Similarity (20점)
- ±10% 이내: 20점 (매우 유사)
- ±20% 이내: 15점 (유사)
- ±30% 이내: 10점
- ±50% 이내: 5점
- 그 이상: 0점

#### Repeatability Similarity (5점)
- ±20% 이내: 5점
- ±50% 이내: 3점
- 그 이상: 1점

#### DoF Match (5점)
- 동일: 5점
- 다름: 0점

### 2. Form Factor Similarity (30점)

생김새와 형태적 특성의 유사성을 평가합니다.

#### Robot Type (10점)
- 동일 타입 (collaborative/industrial): 10점
- 다른 타입: 3점

**로봇 타입 분류:**
- `collaborative`: 협동 로봇 (UR, Doosan A/M 시리즈, TechMan 등)
- `industrial`: 산업용 로봇 (Fanuc, ABB, Yaskawa 등)
- `industrial_collaborative`: 하이브리드 (Doosan H 시리즈)

#### Design Philosophy (10점)
- 동일 디자인: 10점
- 유사 디자인 (둘 다 cylindrical 또는 둘 다 compact): 7점
- 다른 디자인: 3점

**디자인 분류:**
- `compact_cylindrical`: 원통형 협동 로봇 (UR, Doosan A/M)
- `industrial_standard`: 전통적 산업용 (Fanuc, ABB, Yaskawa)
- `compact`: 소형 산업용 (Staubli, Mitsubishi)
- `hybrid`: 하이브리드 형태 (Doosan H 시리즈)

#### Size Category (10점)
- 동일 크기 카테고리: 10점
- 인접 카테고리: 6점
- 2단계 차이: 2점

**크기 분류 (payload + reach 기반):**
- `micro`: 초소형 (< 8 combined metric)
- `small`: 소형 (8-15)
- `medium`: 중형 (15-30)
- `large`: 대형 (30-50)
- `heavy`: 초대형 (≥ 50)

### 3. Manufacturer Match (20점)

- 동일 제조사: 20점 ✅ **프로그래밍 언어/환경이 동일하여 재프로그래밍 최소화**
- 다른 제조사: 0점 ⚠️ **상당한 재프로그래밍 필요**

### 종합 평가 등급

- **EXCELLENT** (85-100점): 거의 직접 교체 가능
- **GOOD** (70-84점): 약간의 조정 필요
- **MODERATE** (50-69점): 중간 정도의 공정 조정 필요
- **POOR** (< 50점): 상당한 변경 필요, 신중히 검토 필요

## 🚀 사용 방법

### 방법 1: 독립 실행 스크립트 사용

```bash
cd robot_selector

# 기본 사용법
python find_replacement.py --manufacturer doosan --model h2017

# 최소 점수 설정 (70점 이상만 표시)
python find_replacement.py --manufacturer universal --model ur10e --min-score 70

# 결과 개수 제한
python find_replacement.py --manufacturer doosan --model h2017 --max-results 5

# 보고서 저장
python find_replacement.py --manufacturer abb --model irb1600 --save-report

# 두 로봇 직접 비교
python find_replacement.py --compare \
    --robot1-mfr doosan --robot1-model h2017 \
    --robot2-mfr yaskawa --robot2-model hc20
```

### 방법 2: TDL 분석과 함께 사용 (main.py)

기존 TDL 분석에 유사도 검색을 추가합니다.

```bash
# TDL 분석 + 추천 로봇과 유사한 로봇 검색
python main.py ../output/task.tdl --find-similar

# 유사 로봇 개수 조정 (기본 5개)
python main.py ../output/task.tdl --find-similar --similarity-count 10

# 보고서 저장 (TDL 분석 + 유사도 분석)
python main.py ../output/task.tdl --find-similar --save-report
```

**출력 파일:**
- `task.robot_report.txt`: TDL 기반 로봇 추천 보고서
- `task.similarity_report.txt`: 유사도 분석 보고서
- `task.robot_report.json`: 추천 데이터 (JSON)

## 📊 출력 예시

### 유사도 분석 결과

```
======================================================================
ROBOT REPLACEMENT SIMILARITY REPORT
======================================================================

TARGET ROBOT (to be replaced):
----------------------------------------------------------------------
  DOOSAN H2017 (6-DoF, Payload: 20.0kg, Reach: 1.7m)
  Payload: 20.0 kg
  Reach: 1.70 m (1700 mm)
  Repeatability: 0.050 mm
  DoF: 6

SIMILAR ROBOTS (Ranked by Similarity):
======================================================================

1. DOOSAN H2515 (6-DoF, Payload: 25.0kg, Reach: 1.5m)
   Overall Similarity: 81.0/100 [GOOD]
   - Spec Similarity: 31.0/50
   - Form Factor Similarity: 30.0/30
   - Manufacturer Match: Yes (20/20)

   Specifications:
   - Payload: 25.0 kg (Target: 20.0 kg)
   - Reach: 1.50 m (Target: 1.70 m)
   - Repeatability: 0.100 mm (Target: 0.050 mm)
   - DoF: 6 (Target: 6)

   Analysis:
     - Similar reach (±11.8%)
     - Similar design philosophy (hybrid)
     - Same size category (large)
     - Same manufacturer - minimal reprogramming needed

2. YASKAWA HC20 (6-DoF, Payload: 20.0kg, Reach: 1.7m)
   Overall Similarity: 66.0/100 [MODERATE]
   - Spec Similarity: 50.0/50
   - Form Factor Similarity: 16.0/30
   - Manufacturer Match: No (0/20)

   Specifications:
   - Payload: 20.0 kg (Target: 20.0 kg)
   - Reach: 1.70 m (Target: 1.70 m)
   - Repeatability: 0.050 mm (Target: 0.050 mm)
   - DoF: 6 (Target: 6)

   Analysis:
     - Very similar payload capacity (±0.0%)
     - Very similar reach (±0.0%)
     - Different robot types (industrial_collaborative vs industrial)
     - Same size category (large)
     - Different manufacturer - may require significant reprogramming

======================================================================
RECOMMENDED REPLACEMENT:
======================================================================
  DOOSAN H2515 (6-DoF, Payload: 25.0kg, Reach: 1.5m)
  Similarity Score: 81.0/100
  Replacement Viability: GOOD

  [INFO] Moderate similarity - some adjustments needed.
  Consider:
    - Testing with sample workpieces
    - Minor process parameter tuning
    - Operator familiarization

======================================================================
```

## 🧪 테스트

테스트 스크립트를 실행하여 유사도 계산이 올바르게 작동하는지 확인할 수 있습니다.

```bash
cd robot_selector
python test_similarity.py
```

**테스트 항목:**
1. 기본 유사도 계산 (동일 사양, 다른 제조사)
2. 데이터베이스 검색
3. 크기 차이가 있는 로봇 (동일 제조사)
4. 협동 로봇 vs 산업용 로봇

## 💡 실전 활용 예시

### 예시 1: 고장난 로봇 교체

**상황:** Doosan H2017이 고장나서 긴급히 교체 필요

```bash
python find_replacement.py --manufacturer doosan --model h2017 --min-score 70
```

**결과 해석:**
- **DOOSAN H2515** (81점, GOOD): 같은 제조사, 유사한 사양 → **최우선 추천**
- **YASKAWA HC20** (66점, MODERATE): 사양은 동일하지만 다른 제조사 → 재프로그래밍 필요

**권장 조치:**
1. 1순위: Doosan H2515 선택 (최소한의 변경)
2. 2순위: Yaskawa HC20 선택 시 프로그래밍 재작업 예산 확보

### 예시 2: 생산 라인 확장

**상황:** 기존에 Universal UR10E를 사용 중이며, 추가 라인 구축

```bash
python find_replacement.py --manufacturer universal --model ur10e --max-results 10
```

**결과 해석:**
- 같은 Universal 시리즈 (UR5E, UR16E 등)가 높은 점수로 추천됨
- 프로그래밍 재사용, 교육 최소화 가능

### 예시 3: TDL 작업 분석과 함께 사용

**상황:** 새로운 작업을 TDL로 정의하고, 적합한 로봇 + 대체 가능한 로봇 찾기

```bash
# 1단계: TDL 분석 및 로봇 추천
python main.py ../output/welding_task.tdl

# 2단계: 추천된 로봇과 유사한 로봇 검색
python main.py ../output/welding_task.tdl --find-similar --similarity-count 5 --save-report
```

**결과:**
- `welding_task.robot_report.txt`: "이 작업에 최적인 로봇"
- `welding_task.similarity_report.txt`: "추천 로봇과 유사하여 대체 가능한 로봇들"

### 예시 4: 두 로봇 직접 비교

**상황:** Doosan H2017과 Yaskawa HC20 중 어느 것이 더 호환성이 좋은지 확인

```bash
python find_replacement.py --compare \
    --robot1-mfr doosan --robot1-model h2017 \
    --robot2-mfr yaskawa --robot2-model hc20
```

## 🔧 커스터마이징

### 제조사 특성 추가

새로운 제조사를 추가하려면 `robot_similarity.py`의 `MANUFACTURER_CHARACTERISTICS`에 추가:

```python
MANUFACTURER_CHARACTERISTICS = {
    # ... 기존 항목들 ...
    "새제조사이름": {
        "type": "collaborative",  # or "industrial", "industrial_collaborative"
        "design": "compact_cylindrical",  # 디자인 타입
        "mounting": ["table", "wall", "ceiling"],  # 설치 옵션
        "ease_of_use": "high",  # "high", "medium", "low"
        "form_factor_weight": 1.1  # 형태 가중치 (0.9-1.2)
    }
}
```

### 평가 가중치 조정

`robot_similarity.py`의 `_evaluate_similarity()` 메서드에서 점수 배분 조정 가능:

```python
# 현재 배분 (총 100점)
spec_score = self._calculate_spec_similarity(...)  # 50점
form_score = self._calculate_form_factor_similarity(...)  # 30점
manufacturer_score = 20.0 if manufacturer_match else 0.0  # 20점

# 예: 제조사 일치를 더 중요하게 (30점으로 증가)
# 이 경우 spec_score와 form_score 비중을 줄여야 합니다
```

### 크기 카테고리 조정

`robot_similarity.py`의 `_get_size_category()` 메서드 수정:

```python
def _get_size_category(self, robot: Robot) -> str:
    combined_metric = robot.payload_kg + (robot.reach_m * 10)

    # 기준값 조정 가능
    if combined_metric < 8:
        return "micro"
    elif combined_metric < 15:
        return "small"
    # ... 나머지
```

## 📈 데이터베이스 확장

### 기본 DB vs 확장 DB

- **robots_db.json**: 기본 사양만 포함 (호환성 유지)
- **robots_db_extended.json**: form factor 정보 추가

확장 DB 사용:

```bash
python find_replacement.py \
    --manufacturer doosan --model h2017 \
    --robots-db robots_db_extended.json
```

### 새 로봇 추가 (확장 DB 형식)

```json
{
  "manufacturer": "제조사명",
  "model": "모델명",
  "payload_kg": 20.0,
  "reach_m": 1.7,
  "repeatability_mm": 0.05,
  "dof": 6,
  "robot_type": "collaborative",  # collaborative/industrial/industrial_collaborative
  "form_factor": "compact_cylindrical",  # 디자인 타입
  "weight_kg": 95.0,  # 로봇 자체 무게 (선택)
  "mounting_options": ["floor", "ceiling", "table"]  # 설치 옵션 (선택)
}
```

## ⚠️ 주의사항

### 1. 유사도 ≠ 완벽한 호환성

유사도 점수가 높아도 다음 사항들은 반드시 검증이 필요합니다:
- **End-effector 호환성**: 그리퍼, 툴 등의 인터페이스
- **통신 프로토콜**: 제어 시스템과의 연동
- **안전 규격**: 작업장 안전 요구사항 충족 여부
- **물리적 공간**: 실제 설치 공간 확인

### 2. 제조사가 다를 경우

- 프로그래밍 언어가 다를 수 있음 (UR Script, Inform, RAPID 등)
- 티칭 방법이 다를 수 있음
- 유지보수 부품 및 서비스 네트워크가 다름

### 3. 크기 카테고리는 참고용

실제 설치 공간, 케이블 배선, 안전 펜스 등은 개별 확인 필요

## 🎓 연구 활용

### 1. 로봇 선택 패턴 분석
- 어떤 작업에 어떤 타입의 로봇이 선호되는지 통계 분석
- 제조사별 선호도 및 교체 패턴

### 2. 플릿 최적화
- 여러 로봇을 보유한 경우, 표준화 가능한 로봇 조합 찾기
- 재고 부품 최소화 전략

### 3. TCO (Total Cost of Ownership) 분석
- 유사도 점수와 교체 비용의 상관관계 연구
- 재프로그래밍 비용, 교육 비용 등 정량화

## 📚 API 사용 예시 (Python 코드에서)

```python
from robot_similarity import RobotSimilarityAnalyzer, Robot

# Analyzer 초기화
analyzer = RobotSimilarityAnalyzer("robots_db.json")

# 특정 로봇 찾기
target_robot = None
for robot in analyzer.robots:
    if robot.manufacturer == "doosan" and robot.model == "h2017":
        target_robot = robot
        break

# 유사 로봇 검색
similarities = analyzer.find_similar_robots(
    target_robot,
    min_score=60.0,
    max_results=5
)

# 결과 출력
for sim in similarities:
    print(f"{sim.robot}: {sim.similarity_score:.1f}/100")
    print(f"Viability: {sim.replacement_viability}")
    print(f"Reasons: {', '.join(sim.reasons)}")
    print()

# 두 로봇 직접 비교
robot1 = analyzer.robots[0]
robot2 = analyzer.robots[1]
similarity = analyzer.compare_two_robots(robot1, robot2)
print(f"Similarity: {similarity.similarity_score:.1f}/100")
```

## 🔗 관련 문서

- **README.md**: Robot Selector 전체 가이드
- **../README.md**: NL2TDL 프로젝트 전체 개요
- **../rag_documents/TDLset.md**: TDL 명세

## 📝 버전 정보

- **Version**: 1.0.0
- **Date**: 2025
- **Author**: NL2TDL Project Team
- **Purpose**: 로봇 교체 시나리오를 위한 유사도 기반 추천 시스템

---

**문의사항이나 개선 제안은 프로젝트 관리자에게 연락 바랍니다.**
