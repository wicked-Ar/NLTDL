
# Motion Planner - PyBullet Path/Motion Planning

TDL 태스크를 위한 충돌 없는 궤적을 계획하는 PyBullet 기반 모션 플래너입니다.

## 🎯 주요 기능

### 핵심 기능

- ✅ **Inverse Kinematics (IK)**: PosX (Cartesian) → PosJ (Joint angles) 변환
- ✅ **Forward Kinematics (FK)**: Joint angles → End effector pose 계산
- ✅ **Trajectory Planning**: 부드러운 궤적 생성 (선형 보간)
- ✅ **Collision Detection**: 자체 충돌 및 환경 충돌 감지
- ✅ **TDL 통합**: TDL 파일 직접 읽어서 모션 계획
- ✅ **Robot Selector 연동**: 자동 로봇 감지
- ✅ **3D Visualization**: PyBullet GUI로 시각화 (선택 사항)

### 지원 기능

- MoveLinear: Cartesian 공간 직선 이동
- MoveJoint: Joint 공간 이동
- 속도/가속도 기반 시간 계산 (Trapezoidal profile)
- Joint limit 검증
- 모션 계획 결과 JSON 저장

## 📁 파일 구조

```
motion_planner/
├── main.py                    # 메인 프로그램
├── robot_models.py            # 로봇 모델 정의 (DH parameters, URDF 생성)
├── ik_solver.py               # IK/FK 솔버 (PyBullet IK 엔진)
├── trajectory_planner.py      # 궤적 계획 및 충돌 감지
├── tdl_motion_planner.py      # TDL 통합 레이어
└── README.md                  # 이 문서
```

## 🚀 사용 방법

### 기본 사용

```bash
cd motion_planner

# Doosan 로봇으로 모션 계획
python main.py ../output/task.tdl --robot doosan

# Universal Robots로 모션 계획
python main.py ../output/task.tdl --robot universal

# 자동 로봇 감지 (robot_selector 결과 활용)
python main.py ../output/task.tdl --auto

# 3D 시각화 활성화
python main.py ../output/task.tdl --robot doosan --visualize

# 모션 계획 결과 저장
python main.py ../output/task.tdl --robot doosan --save-plan
```

### 고급 옵션

```bash
# 충돌 감지 비활성화 (더 빠른 계획)
python main.py ../output/task.tdl --robot doosan --no-collision-check

# 특정 로봇 모델 지정
python main.py ../output/task.tdl --robot doosan --model h2017
```

## 📊 모션 계획 예시

### 입력 (TDL)

```
GOAL Execute_Process()
{
    SPAWN MoveJoint(target_pose=PosJ(0, 0, 90, 0, 90, 0), velocity=50, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
    SPAWN MoveLinear(target_pose=PosX(300, 200, 50, 0, 0, 0), velocity=100, acceleration=50, tool=0, blending_radius=0) WITH WAIT;
}
```

### 출력 (Console)

```
===============================================================
          Motion Planner - PyBullet Path Planning
               Collision-Free Trajectory Generation
===============================================================

[INFO] Using robot: Doosan H2017
[INFO] DOF: 6
[INFO] Max Reach: 1.7m

[Simulation] Loaded robot: H2017
[Simulation] Number of joints: 7
[Simulation] End effector link: 6

[IK] Initialized with 6 controllable joints
[Trajectory] Initialized with 6 joints
[Trajectory] Collision checking: True

[INFO] Parsed TDL: 1 GOALs
[INFO] Planning motion...

============================================================
MOTION PLANNING SUMMARY
============================================================
Status: SUCCESS
Total Duration: 4.32 seconds
Total Waypoints: 100
Number of GOALs: 1

  GOAL: Execute_Process
    Commands: 2
    Duration: 4.32s
============================================================

[INFO] Motion plan saved to: ../output/task.motion_plan.json

[DONE] Motion planning completed successfully!
[INFO] Total execution time: 4.32 seconds
[INFO] Total waypoints: 100
```

### 출력 (JSON 파일)

```json
{
  "goals": [
    {
      "name": "Execute_Process",
      "trajectories": [
        {
          "command": "MoveJoint",
          "waypoints": [[0, 0, 0, 0, 0, 0], ..., [0, 0, 1.57, 0, 1.57, 0]],
          "duration": 2.16,
          "num_waypoints": 50,
          "type": "joint"
        },
        {
          "command": "MoveLinear",
          "waypoints": [...],
          "duration": 2.16,
          "num_waypoints": 50,
          "type": "linear",
          "cartesian_path": [[0.0, 0.0, 0.0], ..., [0.3, 0.2, 0.05]]
        }
      ],
      "duration": 4.32,
      "num_commands": 2
    }
  ],
  "total_duration": 4.32,
  "total_waypoints": 100,
  "success": true,
  "errors": []
}
```

## 🔄 전체 워크플로우 통합

### NL → TDL → Robot Selection → Motion Planning → Control Code

```bash
# 1단계: 자연어 → TDL
cd ..
python main.py -r "박스를 A에서 B로 옮겨줘" -o transfer.tdl

# 2단계: TDL → 최적 로봇 추천
cd robot_selector
python main.py ../output/transfer.tdl --save-report

# 3단계: Motion Planning (자동 로봇 감지)
cd ../motion_planner
python main.py ../output/transfer.tdl --auto --save-plan --visualize

# 4단계: TDL → 로봇 제어 코드
cd ../job_converter
python main.py ../output/transfer.tdl --auto

# 결과 파일:
# - transfer.tdl                      (TDL 문서)
# - transfer.robot_report.json        (로봇 추천)
# - transfer.motion_plan.json         (모션 계획)
# - transfer.drl                      (Doosan 제어 코드)
```

## 🤖 지원 로봇

### Doosan Robotics

- **H2017**: 20kg payload, 1.7m reach, 6-DOF
- Simplified DH parameters 사용
- 기본 홈 포지션: [0, 0, 0, 0, 0, 0]

### Universal Robots

- **UR10e**: 12.5kg payload, 1.3m reach, 6-DOF
- UR 표준 DH parameters
- 기본 홈 포지션: [0, -90°, 0, -90°, 0, 0]

### Generic Robot

- 제조사별 모델이 없을 경우 자동 생성
- Payload/Reach 기반 스케일링
- 6-DOF 기본

## 🔧 기술 세부사항

### IK Solver (ik_solver.py)

- **엔진**: PyBullet의 `calculateInverseKinematics()`
- **알고리즘**: Damped Least Squares (DLS) 기반
- **입력**: Target position (x, y, z), orientation (quaternion or Euler)
- **출력**: Joint angles (radians)
- **특징**:
  - Current joint configuration을 시드로 사용 (가까운 해 선호)
  - 100 iterations, 1e-4 residual threshold

### Trajectory Planner (trajectory_planner.py)

- **보간 방식**: Linear interpolation (joint space / Cartesian space)
- **충돌 감지**: PyBullet의 `getContactPoints()`
- **시간 계산**: Trapezoidal velocity profile
  - 가속 구간 → 등속 구간 → 감속 구간
  - 짧은 이동은 삼각형 프로파일 (가속-감속만)
- **Smoothing**: 옵션으로 trajectory 부드럽게 처리 가능

### 좌표 변환

- **TDL 단위**: mm (위치), degrees (회전)
- **PyBullet 단위**: meters (위치), radians (회전)
- **자동 변환**: `convert_tdl_to_meters()` 함수

## ⚠️ 주의사항

### 1. URDF 모델

- 현재 **간소화된 URDF** 사용 (실제 로봇 형상과 다를 수 있음)
- 실제 로봇 URDF를 사용하려면:
  - 제조사에서 URDF 파일 다운로드
  - `robot_models.py`에서 `create_simple_urdf()` 대신 실제 파일 로드

### 2. DH Parameters

- Doosan H2017, UR10e: 근사값 사용
- 정밀한 계획이 필요하면 제조사 공식 문서 참조하여 수정

### 3. 충돌 감지

- 자체 충돌만 감지 (로봇 링크 간)
- 환경 장애물은 직접 추가 필요:
  ```python
  # main.py에서
  obstacle_id = p.loadURDF("cube.urdf", [0.5, 0, 0.5])
  ```

### 4. 성능

- GUI 모드 (`--visualize`): 느림 (시각화 오버헤드)
- DIRECT 모드: 빠름 (기본)
- 충돌 감지 OFF (`--no-collision-check`): 더 빠름

### 5. MoveCircular 미지원

- 현재 원호 이동은 미구현
- 추후 Bezier curve 또는 circular interpolation 추가 예정

## 🐛 문제 해결

### "IK failed for waypoint" 에러

**원인**: Target pose가 로봇 도달 범위 밖이거나, 특이점(singularity) 근처

**해결**:
- TDL의 좌표값 확인 (mm 단위, 로봇 reach 내인지)
- 목표 자세(orientation) 수정
- Joint space 이동(MoveJoint) 사용

### "Collision detected" 에러

**원인**: 계획된 경로에 충돌 발생

**해결**:
- 시각화로 확인: `--visualize`
- 충돌 감지 임시 비활성화: `--no-collision-check`
- Waypoint 조정 (안전한 경유 지점 추가)

### PyBullet GUI가 열리지 않음

**원인**: 환경에 따라 GUI 미지원 (서버, Docker 등)

**해결**:
- DIRECT 모드 사용 (기본값, GUI 없음)
- X11 forwarding 설정 (Linux)
- VNC/원격 데스크톱 사용

## 🔮 향후 개선 계획

- [ ] MoveCircular 구현 (원호 보간)
- [ ] 실제 로봇 URDF 사용 (제조사 공식 모델)
- [ ] RRT/RRT* 등 고급 경로 계획 알고리즘
- [ ] 동적 장애물 회피
- [ ] Trajectory optimization (시간 최소화, 에너지 최소화)
- [ ] ROS 연동 (MoveIt과 비교)
- [ ] 실시간 제어 시뮬레이션

## 📚 관련 문서

- `../README.md`: LLM-based NL2TDL 변환기
- `../robot_selector/README.md`: 로봇 선택기
- `../job_converter/README.md`: Job 파일 변환기
- [PyBullet 공식 문서](https://pybullet.org/)

---

**개발**: LLM-based NL2TDL 프로젝트의 일부
**목적**: 연구 및 교육용
**기술**: PyBullet, NumPy, Python 3.10+
