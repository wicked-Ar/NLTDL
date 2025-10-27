# Validation & Verification System Design Proposal

## 🎯 목표

NL → TDL 변환의 정확성과 안전성을 검증하는 AI 기반 V&V 시스템 개발

**핵심 Contribution Point:**
- 자연어 기반 로봇 프로그래밍의 신뢰성 보장
- 생산 환경 적용 전 자동 검증
- LLM 출력의 품질 보증

---

## 📊 검증해야 할 사항들

### 1. **Syntactic Validation (구문 검증)**
- ✅ TDL 문법 준수 여부
- ✅ 명령어 형식 정확성
- ✅ 파라미터 타입 및 범위

### 2. **Semantic Validation (의미 검증)**
- 🔍 자연어 의도와 TDL 동작의 일치성
- 🔍 좌표계 및 단위 정확성
- 🔍 물체/위치 참조의 일관성

### 3. **Safety Validation (안전성 검증)**
- ⚠️ 충돌 위험 검출
- ⚠️ 작업 공간 범위 초과
- ⚠️ 비정상적인 속도/가속도
- ⚠️ Singularity 위험

### 4. **Logical Validation (논리 검증)**
- 🧠 작업 순서의 합리성
- 🧠 전제 조건 만족 여부
- 🧠 목표 상태 달성 가능성

---

## 🏗️ 제안하는 V&V 아키텍처 (3가지 옵션)

## **옵션 A: 규칙 기반 + LLM Validator 하이브리드** ⭐ 추천

### 구조
```
Natural Language → LLM → TDL → [V&V System] → Validated TDL
                                     ↓
                        ┌────────────┴────────────┐
                        ↓                         ↓
                  Rule-based Checker        LLM Validator
                  (빠르고 확실)              (유연하고 지능적)
```

### 장점
- ✅ **논문 novelty 확보**: AI 기반 의미 검증 + 규칙 기반 안전성 검증
- ✅ **실용성**: 규칙 기반으로 명확한 오류 빠르게 잡고, LLM으로 애매한 케이스 판단
- ✅ **설명 가능성**: 왜 검증 실패했는지 명확한 이유 제공
- ✅ **점진적 개선**: 규칙 추가 + LLM 파인튜닝 가능

### 구성 요소

#### 1. **Rule-based Checker** (Python 구현)
```python
class SyntaxValidator:
    - TDL 문법 검증
    - 파라미터 범위 체크
    - 필수 필드 존재 확인

class SafetyValidator:
    - 좌표 범위 검증 (로봇 reach 내)
    - 속도/가속도 한계 검증
    - 충돌 검사 (간단한 bounding box)

class ConsistencyValidator:
    - 물체 참조 일관성
    - 좌표계 일관성
```

#### 2. **LLM-based Semantic Validator**
```python
class SemanticValidator:
    - 자연어 의도 vs TDL 동작 일치성 검증
    - Few-shot prompting 사용
    - "이 자연어 명령과 TDL 코드가 같은 의미인가?" 판단
```

**프롬프트 예시:**
```
Given:
- Natural Language: "Move the box from table A to table B"
- Generated TDL: [TDL code]

Question: Does the TDL correctly implement the natural language instruction?
Verify:
1. Are the source and destination correct?
2. Is the object reference correct?
3. Is the motion sequence logical?

Answer: YES/NO with reasoning.
```

#### 3. **Verification Score Aggregator**
```python
def calculate_verification_score(
    syntax_score: float,
    safety_score: float,
    semantic_score: float,
    weights: dict
) -> VerificationResult:
    total_score = (
        syntax_score * weights['syntax'] +
        safety_score * weights['safety'] +
        semantic_score * weights['semantic']
    )
    return VerificationResult(score=total_score, details=...)
```

### Contribution Points
1. **Novel hybrid approach**: 규칙 기반의 확실성 + LLM의 유연성
2. **Multi-level validation**: Syntax → Safety → Semantics 계층적 검증
3. **Explainable results**: 각 검증 레벨별 상세 피드백

---

## **옵션 B: Fine-tuned Classification Model**

### 구조
```
(NL, TDL) pair → BERT/RoBERTa Fine-tuned Model → Binary Classification
                                                    (Valid / Invalid)
```

### 데이터셋 구축
```python
Training Data:
- Positive examples: (올바른 NL, 올바른 TDL) pairs
- Negative examples:
  - Type 1: (NL, 문법 오류 TDL)
  - Type 2: (NL, 의미 불일치 TDL)
  - Type 3: (NL, 안전하지 않은 TDL)
```

### 장점
- ✅ End-to-end 학습
- ✅ 명확한 평가 메트릭 (Accuracy, Precision, Recall)
- ✅ 빠른 추론 속도

### 단점
- ❌ 대량의 labeled data 필요 (최소 1000+ pairs)
- ❌ 설명 가능성 낮음
- ❌ 새로운 TDL 명령어 추가 시 재학습 필요

---

## **옵션 C: Self-Consistency Verification (LLM-only)**

### 구조
```
NL → LLM → TDL_1
   ↓
   → LLM → TDL_2  → Consistency Check → Score
   ↓
   → LLM → TDL_3
```

### 방법
1. 같은 자연어로 TDL을 여러 번 생성 (Temperature > 0)
2. 생성된 TDL들의 일관성 측정
3. 일관성 높으면 → 신뢰도 높음
4. 차이 있으면 → 가장 안전한 것 선택 or 재생성

### 장점
- ✅ 추가 모델 학습 불필요
- ✅ 자기 검증 (self-verification) 가능
- ✅ Novelty 있음 (로봇 프로그래밍에 적용한 사례 적음)

### 단점
- ❌ LLM 호출 비용 증가 (3배)
- ❌ 일관성 != 정확성 (모두 틀릴 수도)

---

## 🎯 추천: **옵션 A (하이브리드)** + 일부 옵션 C 활용

### 이유

1. **실용성과 Novelty 균형**
   - 규칙 기반: 산업 환경에서 필수적 (안전 검증)
   - LLM 기반: 연구 novelty 확보 (의미 검증)

2. **명확한 Contribution**
   - "Multi-level hybrid V&V framework for LLM-generated robot programs"
   - Rule-based (fast & reliable) + LLM-based (intelligent & flexible)

3. **논문 구성에 유리**
   - Related Work: 기존 규칙 기반 검증 vs 본 연구의 하이브리드
   - Ablation Study: 규칙만 vs LLM만 vs 하이브리드 성능 비교
   - Case Study: 복잡한 케이스에서 LLM의 우수성 입증

4. **점진적 개선 가능**
   - Phase 1: 규칙 기반 구현 (빠르게 동작하는 baseline)
   - Phase 2: LLM validator 추가 (의미 검증)
   - Phase 3: Self-consistency 추가 (optional, 고신뢰도 필요 시)

---

## 📐 구체적 구현 계획 (옵션 A 기준)

### Phase 1: Rule-based Validators (1-2주)

```python
# validator/syntax_validator.py
class SyntaxValidator:
    def validate_tdl(self, tdl_content: str) -> ValidationResult:
        # 1. TDL 파싱 가능 여부
        # 2. 필수 섹션 존재 (Header, Objects, Positions, Tasks)
        # 3. 명령어 문법 정확성
        pass

# validator/safety_validator.py
class SafetyValidator:
    def validate_safety(
        self,
        tdl_content: str,
        robot_spec: RobotSpec
    ) -> ValidationResult:
        # 1. 좌표가 로봇 reach 내에 있는지
        # 2. 속도/가속도가 로봇 한계 내
        # 3. Gripper force가 물체 파손 범위 내
        pass

# validator/consistency_validator.py
class ConsistencyValidator:
    def validate_consistency(self, tdl_content: str) -> ValidationResult:
        # 1. 참조하는 물체가 정의되어 있는지
        # 2. 참조하는 위치가 정의되어 있는지
        # 3. Task 순서가 논리적인지 (Move 전에 Grip 등)
        pass
```

### Phase 2: LLM-based Semantic Validator (1주)

```python
# validator/semantic_validator.py
class SemanticValidator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.few_shot_examples = self._load_examples()

    def validate_semantics(
        self,
        natural_language: str,
        tdl_content: str
    ) -> ValidationResult:
        prompt = self._build_validation_prompt(
            natural_language,
            tdl_content
        )

        response = self.llm.generate(prompt)

        return self._parse_validation_response(response)

    def _build_validation_prompt(self, nl: str, tdl: str) -> str:
        return f"""
        You are a robot programming expert. Validate if the TDL code
        correctly implements the natural language instruction.

        {self.few_shot_examples}

        Natural Language: {nl}
        Generated TDL:
        {tdl}

        Validate the following:
        1. Object correctness: Are the objects correctly identified?
        2. Action correctness: Are the actions (Move, Pick, Place) correct?
        3. Sequence correctness: Is the order of operations logical?
        4. Parameter correctness: Are speeds, forces reasonable?

        Provide:
        - VERDICT: PASS or FAIL
        - CONFIDENCE: 0-100
        - REASONING: Detailed explanation
        - ISSUES: List of problems found (if any)

        Format your response as JSON.
        """
```

### Phase 3: Orchestrator (통합) (3-5일)

```python
# validator/vv_orchestrator.py
class VVOrchestrator:
    def __init__(self):
        self.syntax_validator = SyntaxValidator()
        self.safety_validator = SafetyValidator()
        self.consistency_validator = ConsistencyValidator()
        self.semantic_validator = SemanticValidator(llm_client)

    def validate(
        self,
        natural_language: str,
        tdl_content: str,
        robot_spec: RobotSpec,
        validation_level: str = "FULL"  # BASIC, STANDARD, FULL
    ) -> VVReport:
        results = {}

        # Level 1: Syntax (필수)
        results['syntax'] = self.syntax_validator.validate_tdl(tdl_content)
        if not results['syntax'].passed:
            return VVReport(passed=False, level="SYNTAX", results=results)

        # Level 2: Safety (필수)
        results['safety'] = self.safety_validator.validate_safety(
            tdl_content, robot_spec
        )
        if not results['safety'].passed:
            return VVReport(passed=False, level="SAFETY", results=results)

        # Level 3: Consistency (Standard 이상)
        if validation_level in ["STANDARD", "FULL"]:
            results['consistency'] = self.consistency_validator.validate_consistency(
                tdl_content
            )

        # Level 4: Semantics (Full만)
        if validation_level == "FULL":
            results['semantic'] = self.semantic_validator.validate_semantics(
                natural_language, tdl_content
            )

        # Aggregate results
        overall_score = self._calculate_overall_score(results)

        return VVReport(
            passed=overall_score > 0.85,
            score=overall_score,
            results=results,
            recommendations=self._generate_recommendations(results)
        )
```

---

## 📊 평가 메트릭 (논문용)

### 1. **Detection Metrics**
```python
# 오류 검출 성능
Precision = TP / (TP + FP)  # 검출한 오류 중 실제 오류 비율
Recall = TP / (TP + FN)     # 실제 오류 중 검출한 비율
F1-Score = 2 * (Precision * Recall) / (Precision + Recall)
```

### 2. **Validation Accuracy**
```python
# 검증 정확도
Accuracy = (올바르게 PASS + 올바르게 FAIL) / 전체 케이스
```

### 3. **Safety Guarantee**
```python
# 안전성 보장 (가장 중요!)
Safety_Recall = 위험한 TDL을 잡아낸 비율
# 목표: 99% 이상 (위험한 것을 절대 놓치면 안됨)
```

### 4. **Ablation Study**
```
성능 비교:
- Baseline (규칙만)
- LLM만
- 하이브리드 (제안 방법)

각각에 대해:
- Detection rate
- False positive rate
- Validation time
```

---

## 🧪 Test Dataset 구축 전략

### 자동 생성 + 수동 큐레이션

```python
# 1. Positive Examples (정상 케이스)
positive_samples = [
    (nl, tdl) for nl, tdl in existing_successful_conversions
]

# 2. Negative Examples - Synthetic Error Injection
def inject_errors(correct_tdl: str, error_type: str) -> str:
    if error_type == "syntax":
        # 문법 오류 주입
        return introduce_syntax_error(correct_tdl)
    elif error_type == "semantic":
        # 의미 오류 (물체 바꾸기 등)
        return swap_object_references(correct_tdl)
    elif error_type == "safety":
        # 안전 오류 (좌표 범위 초과 등)
        return make_unsafe_coordinates(correct_tdl)

# 3. Real-world Errors
# LLM이 실제로 생성한 오류 케이스 수집
```

### 최소 데이터셋 크기 제안
- **Positive**: 200개
- **Negative (Syntax)**: 100개
- **Negative (Semantic)**: 100개
- **Negative (Safety)**: 100개
- **Total**: 500개

(논문에서는 "500 validated test cases" 라고 쓸 수 있음)

---

## 💡 추가 Contribution 아이디어

### 1. **Confidence-based Filtering**
```python
if vv_score < 0.7:
    # 재생성 요청
    regenerate_tdl(with_feedback=vv_report.issues)
elif vv_score < 0.85:
    # 사용자 확인 요청
    request_human_verification()
else:
    # 자동 승인
    approve_tdl()
```

### 2. **Feedback Loop for LLM Improvement**
```python
# V&V 결과를 LLM에게 피드백
if not vv_result.passed:
    improved_tdl = llm.regenerate(
        nl=original_nl,
        previous_tdl=failed_tdl,
        feedback=vv_result.issues
    )
```

### 3. **Safety Certification Report**
```python
# 산업 환경을 위한 검증 리포트 자동 생성
generate_certification_report(
    tdl_file="task.tdl",
    vv_results=vv_results,
    standard="ISO 10218-1"  # 로봇 안전 표준
)
```

---

## 📝 논문 Structure 제안

### Title
"Multi-level Validation Framework for LLM-generated Robot Task Programs"

### Abstract
- Problem: LLM으로 생성한 로봇 프로그램의 신뢰성 문제
- Solution: 규칙 기반 + AI 기반 하이브리드 V&V
- Results: 95%+ 오류 검출률, 실시간 검증

### Contributions
1. **Novel hybrid V&V architecture** combining rule-based and LLM-based validation
2. **Multi-level validation** (Syntax → Safety → Semantics)
3. **Semantic validation using LLM** with few-shot prompting
4. **Comprehensive evaluation** on 500+ test cases

### Related Work
- Traditional robot program verification (formal methods)
- LLM code generation validation
- Safety verification in robotics

### Methodology
- Section 4.1: Rule-based Validators
- Section 4.2: LLM-based Semantic Validator
- Section 4.3: Hybrid Orchestration
- Section 4.4: Feedback Mechanism

### Experiments
- Dataset construction
- Baseline comparisons
- Ablation study
- Case studies

---

## 🚀 다음 단계

어떤 방향으로 진행하시겠습니까?

**Option 1**: 옵션 A (하이브리드) 구현 시작
- Phase 1 규칙 기반 validator 먼저 구현
- 빠르게 동작하는 baseline 확보

**Option 2**: 더 구체적인 설계 논의
- 특정 validation rule 정의
- LLM 프롬프트 설계
- 평가 데이터셋 구축 계획

**Option 3**: 다른 접근 방법 탐색
- Fine-tuned model (옵션 B) 고려
- Self-consistency (옵션 C) 실험

제 추천은 **Option 1 (하이브리드 구현)**입니다.
- 실용성과 novelty 모두 확보
- 논문 contribution이 명확
- 단계별 개선 가능

어떻게 진행하시겠습니까?
