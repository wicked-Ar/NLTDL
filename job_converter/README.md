

# Job Converter - TDL을 로봇 제어 코드로 변환

TDL (Task Description Language) 파일을 제조사별 로봇 제어 코드로 변환하는 프로그램입니다.

## 🎯 주요 기능

### 지원하는 로봇 제조사

1. **Doosan Robotics**
   - 출력: DRL (Doosan Robotics Language)
   - 형식: Python 기반
   - 확장자: `.drl`

2. **Universal Robots**
   - 출력: UR Script
   - 형식: UR 전용 스크립트 언어
   - 확장자: `.script`

### 핵심 기능

- ✅ TDL 파일 파싱 및 분석
- ✅ 제조사별 코드 생성
- ✅ Robot Selector 연동 (자동 로봇 감지)
- ✅ 배치 변환 (폴더 내 모든 TDL 파일)
- ✅ 단위 자동 변환 (mm→m, deg→rad 등)

## 📁 파일 구조

```
job_converter/
├── main.py                  # 메인 프로그램
├── tdl_parser.py            # TDL 파서
├── doosan_converter.py      # Doosan DRL 변환기
├── universal_converter.py   # Universal UR Script 변환기
└── README.md                # 이 문서
```

## 🚀 사용 방법

### 기본 사용

```bash
cd job_converter

# Doosan 로봇용 변환
python main.py ../output/task.tdl --robot doosan

# Universal Robots용 변환
python main.py ../output/task.tdl --robot universal

# 출력 파일 지정
python main.py ../output/task.tdl --robot doosan -o my_program.drl
```

### 자동 로봇 감지

Robot Selector의 결과를 자동으로 읽어서 추천된 로봇으로 변환합니다:

```bash
# 1. 먼저 robot_selector로 최적 로봇 찾기
cd ../robot_selector
python main.py ../output/task.tdl --save-report

# 2. 자동 감지로 변환
cd ../job_converter
python main.py ../output/task.tdl --auto
```

### 배치 변환

폴더 내 모든 TDL 파일을 한 번에 변환:

```bash
# output 폴더의 모든 TDL 파일을 Doosan 코드로 변환
python main.py --batch ../output --robot doosan

# Universal Robots 코드로 변환
python main.py --batch ../output --robot universal
```

### 코드 출력만 (파일 저장 안함)

```bash
python main.py ../output/task.tdl --robot doosan --print-only
```

## 📊 변환 예시

### 입력 (TDL)

```
GOAL Initialize_Process()
{
    SPAWN MoveJoint(target_pose=PosJ(0, 0, 90, 0, 90, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT;
}

GOAL Execute_Process()
{
    SPAWN MoveLinear(target_pose=PosX(0, 0, 150, 0, 0, 0), velocity=100, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
    SPAWN SetDigitalOutput(port=1, value=1) WITH WAIT;
    SPAWN Delay(duration_sec=0.5) WITH WAIT;
}

GOAL Finalize_Process()
{
    SPAWN SetDigitalOutput(port=1, value=0) WITH WAIT;
    SPAWN MoveJoint(target_pose=PosJ(0, 0, 90, 0, 90, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
    SPAWN End() WITH WAIT;
}
```

### 출력 1: Doosan DRL (Python 기반)

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Doosan Robot Job File
# Auto-generated from TDL

def Initialize_Process():
    movej(posj(0, 0, 90, 0, 90, 0), v=50, a=50, radius=0)
    set_digital_output(1, 0)

def Execute_Process():
    movel(posx(0, 0, 150, 0, 0, 0), v=100, a=50, radius=0)
    set_digital_output(1, 1)
    wait(0.5)

def Finalize_Process():
    set_digital_output(1, 0)
    movej(posj(0, 0, 90, 0, 90, 0), v=50, a=50, radius=0)
    return

# Main execution
if __name__ == '__main__':
    Initialize_Process()
    Execute_Process()
    Finalize_Process()
```

### 출력 2: Universal Robots UR Script

```
# Universal Robots UR Script
# Auto-generated from TDL

def Initialize_Process():
  movej([0.000000, 0.000000, 1.570796, 0.000000, 1.570796, 0.000000], a=0.500, v=0.500)
  set_digital_out(1, False)
end

def Execute_Process():
  movel(p[0.000000, 0.000000, 0.150000, 0.000000, 0.000000, 0.000000], a=0.050, v=0.100, r=0.000)
  set_digital_out(1, True)
  sleep(0.5)
end

def Finalize_Process():
  set_digital_out(1, False)
  movej([0.000000, 0.000000, 1.570796, 0.000000, 1.570796, 0.000000], a=0.500, v=0.500)
  # End
end

# Main program
Initialize_Process()
Execute_Process()
Finalize_Process()
```

## 🔄 전체 워크플로우

### NL → TDL → 로봇 추천 → 제어 코드

```bash
# 1단계: 자연어 → TDL 생성
cd ..
python main.py -r "박스를 A에서 B로 옮겨줘" -o transfer_task.tdl

# 2단계: TDL 분석 및 최적 로봇 추천
cd robot_selector
python main.py ../output/transfer_task.tdl --save-report

# 3단계: TDL → 로봇 제어 코드 변환
cd ../job_converter
python main.py ../output/transfer_task.tdl --auto

# 결과 파일:
# - transfer_task.tdl          (TDL 문서)
# - transfer_task.json         (메타데이터)
# - transfer_task.robot_report.json  (로봇 추천)
# - transfer_task.drl          (Doosan 제어 코드)
```

## 📝 지원하는 TDL 명령어

### 이동 명령
- `MoveLinear` → `movel` (직선 이동)
- `MoveJoint` → `movej` (관절 보간 이동)
- `MoveCircular` → `movec` (원호 이동)

### I/O 제어
- `SetDigitalOutput` → `set_digital_output` / `set_digital_out`
- `GetDigitalInput` → `get_digital_input` / `get_digital_in`

### 시간 제어
- `Delay` → `wait` / `sleep`

### 제어 흐름
- `End` → `return` / `# End`

### 용접 (주석 처리)
- `ArcOn` → 주석으로 출력 (제조사별 구현 필요)
- `ArcOff` → 주석으로 출력

## 🔧 단위 변환

### Doosan DRL
- 위치: mm (TDL과 동일)
- 회전: degrees (TDL과 동일)
- 속도: mm/s (TDL과 동일)
- 가속도: mm/s² (TDL과 동일)

### Universal Robots UR Script
- 위치: mm → **m** (÷1000)
- 회전: degrees → **radians** (×π/180)
- 속도: mm/s → **m/s** (÷1000)
- 가속도: mm/s² → **m/s²** (÷1000)

## ⚠️ 주의사항

### 1. 좌표계
- TDL의 PosX/PosJ가 로봇별로 다르게 해석될 수 있음
- 실제 로봇에서 테스트 전 좌표 확인 필요

### 2. 안전
- 생성된 코드는 시뮬레이션에서 먼저 테스트
- 실제 로봇 적용 전 전문가 검토 필요

### 3. 용접/특수 기능
- 용접 등 특수 기능은 주석으로 표시
- 제조사별 구현 필요

### 4. 단위 변환
- Universal Robots는 m, rad 단위 사용
- 자동 변환되지만 확인 권장

## 🐛 문제 해결

### "Failed to parse TDL" 에러

TDL 파일 형식 확인:
- GOAL 블록이 올바른지
- SPAWN 명령어 형식이 맞는지
- 중괄호 `{}` 짝이 맞는지

### "--auto 모드에서 로봇 감지 실패"

Robot Selector를 먼저 실행:
```bash
cd ../robot_selector
python main.py ../output/task.tdl --save-report
```

### "Unsupported robot" 에러

지원하는 로봇 목록 확인:
```bash
python main.py --help
```

현재 지원: `doosan`, `universal`

## 🔮 향후 개선 계획

- [ ] ABB, KUKA, Fanuc 등 추가 제조사 지원
- [ ] 용접/특수 기능 매핑 완성
- [ ] 고급 제어 흐름 (If/While/For) 변환
- [ ] 시뮬레이터 연동
- [ ] 단위 테스트 추가

## 📚 관련 문서

- `../README.md`: LLM-based NL2TDL 변환기
- `../robot_selector/README.md`: 로봇 선택기
- `../../rag_documents/TDLset.md`: TDL 명세

---

**개발**: LLM-based NL2TDL 프로젝트의 일부
**목적**: 연구 및 교육용
