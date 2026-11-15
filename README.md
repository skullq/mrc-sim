# MRC-SIM: UEC / Multipath Reliable Connection Verification & Topology Studio

**8대 서버 × 8 GPU (64 GPU, 2-Tier Leaf-Spine Rail-Optimized 패브릭)** 환경에서 링크·스위치(Plane) 장애나 스위치 버퍼 폭주가 발생했을 때, UEC/MRC 프로토콜(`REPS`, `Freezing`, `SLEEK`, `NSCC`, `Packet Trimming`, `ECN`)이 패킷 유실로 멈추지 않고 **건강한 EV 및 우회 경로로 트래픽을 얼마나 빠르고 균등하게 재분배·복구하는지** 검증하는 시뮬레이션 및 시각화 스튜디오입니다.

> 프로토콜 아키텍처·패킷 레이아웃·`TC-01 ~ TC-10` 전체 명세는 [SPEC.md](file:///root/mrc-sim/SPEC.md)를 참고하세요.

---

## 1. 서비스 실행 및 관리

### 웹 대시보드 실행 ([server.sh](file:///root/mrc-sim/scripts/server.sh) · [web_dashboard.py](file:///root/mrc-sim/scripts/web_dashboard.py))
- **관리 스크립트 사용 (권장)**:
  ```bash
  ./scripts/server.sh start      # 백그라운드 실행 (기본 포트 8787, 포트 지정: start 8787)
  ./scripts/server.sh status     # 실행 상태, PID, HTTP 응답 및 접속 URL 확인
  ./scripts/server.sh stop       # 서버 중지
  ./scripts/server.sh restart    # 서버 재시작
  ./scripts/server.sh logs       # 최근 서버 로그 확인 (/tmp/mrc_dashboard.log)
  ```
- **포그라운드 직접 실행**:
  ```bash
  python3 /root/mrc-sim/scripts/web_dashboard.py --port 8787
  ```
- **브라우저 접속**: `http://127.0.0.1:8787` 또는 `http://localhost:8787` (원격 서버 시 `http://<서버IP>:8787`)

### CLI 자동 검증 스위트 (`TC-01 ~ TC-10`) 단독 실행
```bash
python3 /root/mrc-sim/scripts/run_all_tests.py
```

---

## 2. 웹 대시보드 구성 및 사용법

### Tab 1: `Test Suite (TC-01 ~ TC-10)` — 규격 회귀 검증
- `Run All Tests` / `Stop` 버튼으로 `TC-01 ~ TC-10` 전체 시나리오를 실행하고 실시간 진행률, Heartbeat(`sim_us`, `new`, `rtx`, `acks`, `sleek`, `trace`), 디스크 잔여량 및 `Wire View`를 확인합니다.

### Tab 2: `Topology Builder & Fault Injection` — 8×8 장애 주입 실험실
- **고정 토폴로지**: `8 Nodes × 8 GPUs (64 GPUs)` · `2-Tier Leaf-Spine (K=4, ToR=4, Spine=2/plane)` · `Rail-Optimized (-planes 8)`
- **장애 주입**: 다이어그램 상단 Plane(`P0 ~ P7`) 또는 GPU→Plane 링크(`N{s}-P{r}`)를 클릭하여 단일/다중 장애를 선택하고 `Fail At (us)` 시점을 지정합니다.
- **링크 색상 범례**:
  - **하늘색 (`#38bdf8`)**: 정상 트래픽 흐름
  - **연두색 (`#4ade80`)**: 장애 또는 `TX_RTX` EV 전환으로 인한 재분배 부하 증가 (`+Δ%`)
  - **노란색 (`#facc15`)**: ECN 혼잡 마킹 (`SW_ECN`)
  - **보라/마젠타 (`#e879f9`)**: 패킷 페이로드 64B 절단 (`SW_TRIM`)
  - **빨간색 점선 (`#ef4444`)**: 장애 차단 (`FAIL 0%` / `SW_NODE_FAIL` / `SW_LINK_FAIL`)
  - **흐린 회색 (`#475569`)**: 해당 프레임에서 트래픽이 없는(`0%`) 유휴 링크
- **4단계 순차 전이 패널**:
  1. **장애 전 (Baseline)**: 8개 Plane 균등 분산 (`~12.5%`)
  2. **장애 발생 및 감지 (Fault)**: `SW_NODE_FAIL` / `SW_LINK_FAIL` / `SW_ECN` / `SW_TRIM` / `TX_PROBE`
  3. **우회 및 트래픽 재분배 (Reroute)**: `TX_RTX`, `SLEEK`, 전체 `EV` 전환 건수, `P0~P7` 누적 점유율 변화
  4. **최종 마무리 결과 (Final Verdict)**: `PASS (rc=0)` 여부 및 `New` / `ACKs` 완주 통계

- **단일 Flow 집중 트래킹 & Wireshark 패킷/헤더 분석기**:
  - 상단 드롭다운 또는 테이블 행 클릭으로 특정 Flow(예: `Flow 15`)를 선택하면, 토폴로지에 **순방향 데이터(파랑)**·**Trim 전 구간(보라: `Src→Plane→Dst`)**·**NACK 역방향(주황)**·**ACK 역방향(청록)** 화살표가 분리 표시됩니다.
  - 동시에 **Wireshark 패킷 & 헤더 분석기**가 열려 패킷별 `Display Filter`(`DATA`, `TRIM`, `NACK`, `ACK`, `ECN`, `RTX/FAIL`, `PSN=..`), **L2 Rail / IPv4-ECN / UEC Transport 계층별 헤더 트리**, **Hex/ASCII 바이트 덤프**를 확인할 수 있습니다.
- **타임라인 재생 컨트롤**: `◀ 이전`, `▶ Play` / `⏸ Pause` / `↻ Replay`(마지막 프레임 도달 시 처음 `F00`부터 재시작), `다음 ▶`, `Loop ON/OFF`

---

## 3. 테스트 옵션 및 Multipath 알고리즘 상세

### 3.1. 대시보드 & 시뮬레이터 주요 옵션

| 옵션 (UI / CLI 플래그) | 기본값 / 범위 | 설명 |
| :--- | :--- | :--- |
| **xPUs / Ports / Wiring / Tiers** | `8` / `8` / `Rail-Optimized` / `2-Tier` | `8 xPUs × 8 Ports` Rail-Optimized 2-Tier Leaf-Spine 고정 토폴로지 (`-nodes 8 -planes 8 -tiers 2`) |
| **Traffic Pattern** | `All-to-All` / `Incast` | `All-to-All`: 모든 xPU 쌍 간 분산 트래픽(총 56 Flow) / `Incast`: 모든 송신자가 마지막 xPU로 집중 |
| **Multipath Algo** (`-load_balancing_algo`) | `REPS` (`reps`, `freezing`, `oblivious`, `bitmap`, `mixed`) | 패킷 단위 `EV(Entropy Value)` 경로 선택 및 장애/혼잡 회피 알고리즘 |
| **Fail At (us)** (`MRC_FAIL_AT_US`) | `20` (`0 ~ 100,000 us`) | 선택한 노드(`P0~P7`) 또는 링크(`N{s}-P{r}`)에 장애를 주입하는 시각 (`us`) |
| **Recover At (us, 0=perm)** (`MRC_RECOVER_AT_US`) | `0` (`0 ~ 100,000 us`) | 장애 복구 시각 (`0`이면 영구 장애) |
| **Max Test Time (us)** (`-end`) | `10,000` (`100 ~ 100,000 us`) | 시뮬레이션 최대 종료 시간 (`htsim_uec -end`) |
| **Timeline Frames** | `16` (`16 / 32 / 64 / 128`) | 전체 트레이스를 분할해 시각화할 타임라인 프레임 개수 |
| **Link Speed** (`-linkspeed`) | `100G` / `400G` | 링크 대역폭 (`100,000` / `400,000` Mbps). 속도 변경 시 권장 Queue/ECN 연동 가능 |
| **Queue Size (pkts)** (`-q`) | `16` (`4 ~ 512`) | 스위치 출력 큐 크기 (패킷 단위, MTU `4096 B`). 초과 시 `SW_TRIM` 또는 `SW_BTS` 발생 |
| **ECN Low / High (pkts)** (`-ecn`) | `4 / 12` (`1 ~ 512`) | `CompositeQueue` ECN 마킹 임계치 (`low` 미만 `0%`, `low~high` 선형 확률, `high` 이상 `100%` 마킹) |

---

### 3.2. Multipath 알고리즘 비교 및 동작 원리 ([uec_mp.cpp](file:///root/mrc-sim/htsim/htsim/sim/uec_mp.cpp), [main_uec.cpp](file:///root/mrc-sim/htsim/htsim/sim/datacenter/main_uec.cpp))

UEC/MRC는 패킷 헤더의 **EV(Entropy Value)** 를 패킷 단위로 변경하여 다중 Plane/경로로 스프레이(Packet Spraying)합니다.

| 알고리즘 | UI / CLI 값 | 피드백 반영 (`processEv`) | 핵심 동작 및 특징 |
| :--- | :--- | :--- | :--- |
| **REPS** | `reps` (`UecMpRepsLegacy`) | `PATH_GOOD`만 반영 | 초기 윈도우에서 경로를 순차 스프레이한 뒤, **정상 ACK(`PATH_GOOD`)가 돌아온 건강한 `EV`만 큐(`_next_pathid`)에 넣어 재활용**합니다. 재활용 큐가 비면 랜덤 `EV`로 탐색합니다. |
| **REPS + Freezing** | `freezing` (`UecMpReps`) | `PATH_GOOD`, `PATH_TIMEOUT` | `CircularBufferREPS` 기반 개선형 REPS. 타임아웃(`PATH_TIMEOUT`) 등 심각한 장애 감지 시 **Frozen Mode**로 진입해 검증된 경로만 재사용하며, 일정 시간(`exit_freeze_after`) 후 버퍼를 리셋하고 16개 패킷(`explore_counter=16`)을 랜덤 재탐색합니다. *(Trim 활성화 필수)* |
| **Oblivious** | `oblivious` (`UecMpOblivious`) | **없음** (무시) | 네트워크 피드백을 전혀 보지 않고 `_current_ev_index ^ _path_xor` 순열로 모든 `EV`를 순환합니다. 한 사이클 완료 시 `_path_xor`를 랜덤 갱신합니다. |
| **Bitmap** | `bitmap` (`UecMpBitmap`) | `PATH_ECN`, `PATH_NACK`, `PATH_TIMEOUT` | 각 `EV`별 스킵 페널티(`_ev_skip_bitmap`, 최대 `15`)를 관리합니다. **`ECN(+1)`, `NACK(+4)`, `TIMEOUT(+15)`** 발생 시 해당 경로를 건너뛰고, 건너뛸 때마다 페널티를 `1`씩 감소시켜 점진적으로 복구합니다. |
| **Mixed** | `mixed` (`UecMpMixed`) | `Bitmap` + `REPS` 동시 반영 | **`REPS`의 건강한 `EV` 재활용 큐를 최우선**으로 사용하고, 재활용할 `EV`가 없을 때만 **`Bitmap` 페널티 회피 로직**으로 폴백하는 하이브리드 방식입니다. |
| **ECMP** *(CLI 전용)* | `ecmp` (`UecMpEcmp`) | 없음 | Flow당 단일 고정 경로만 사용하는 비교 기준선 모드입니다. |

---

## 4. 100G vs 400G 기준값 (BDP · Queue · ECN 임계치)

### BDP (Bandwidth-Delay Product, 대역폭-지연 곱)란?
- **정의**: $\text{BDP} = \text{링크 대역폭(Bandwidth)} \times \text{왕복 지연시간(RTT)}$
- **의미**: 링크를 쉬지 않고 100% 활용하기 위해 **네트워크 파이프라인(송신→스위치→수신→ACK) 안에 동시에 떠 있어야 하는(in-flight) 데이터 양**입니다.
- **이 시뮬레이터에서의 중요성**:
  1. **전송 윈도우(`-cwnd`) 기준**: 100G(`BDP ≈ 28.5 pkts`)에서는 초기 `cwnd=30`으로 첫 RTT부터 링크를 100% 채울 수 있습니다.
  2. **스위치 큐(`Queue Size`) 및 ECN 임계치 기준**: 스위치 큐가 BDP에 비해 너무 작으면(예: 400G `BDP ≈ 114 pkts` 환경에서 `Queue=16` 사용) 정상적인 트래픽 버스트도 흡수하지 못해 불필요한 `SW_TRIM`·재전송이 급증합니다. 반대로 BDP 수준에 맞춘 `Queue`와 `ECN Low/High`를 설정해야 높은 처리량과 낮은 지연(Tail Latency)을 동시에 확보할 수 있습니다.

2-Tier 무부하 RTT ≈ `9.33 us`, MTU `4096 B` 기준:

| 링크 속도 | BDP (패킷 환산) | 민감 테스트 기본값 | 권장 여유 기준값 (`권장 기준값 적용`) |
| :---: | :---: | :---: | :---: |
| **100G** (`-linkspeed 100000`) | `~116.6 KB` (`~28.5 pkts`) | `Queue=16`, `ECN=4 / 12` | **`Queue=64` (256 KB), `ECN=16 / 48`** |
| **400G** (`-linkspeed 400000`) | `~466.6 KB` (`~114 pkts`) | `Queue=16` 사용 시 버퍼 1/4 부족 | **`Queue=160` (640 KB), `ECN=48 / 112`** |

- 대시보드에서 `Queue Size` 하한은 시뮬레이터 안정성을 위해 **최소 `4` 패킷**으로 제한됩니다.

---

## 5. 핵심 기술 동작 및 구현 상세

### 5.1. 스위치 `CompositeQueue`의 Trim vs ECN 마킹 동작 ([compositequeue.cpp](file:///root/mrc-sim/htsim/htsim/sim/compositequeue.cpp#L96-L144))
작은 스위치 큐(예: `-q 4`)에서 **Packet Trimming(`SW_TRIM`)이 발생하더라도 해당 Trim 패킷에 `SW_ECN`이 함께 찍히지 않는 이유**는 다음과 같습니다.
1. **Trim 패킷의 `QUEUE_HIGH` 우회**: 저우선순위 데이터 큐(`_enqueued_low`)가 포화되어 페이로드가 절단된 패킷(`BOOTED_TRIM`)은 고우선순위 헤더 큐(`_enqueued_high`, `QUEUE_HIGH`)로 이동합니다. `CompositeQueue::completeService()`에서 `decide_ECN()` 기반 `ECN_CE` 마킹은 **`QUEUE_LOW` Dequeue 시점에만 수행**되며, `QUEUE_HIGH` Dequeue 경로의 헤더 ECN 마킹은 비활성화되어 있습니다.
2. **작은 큐의 Enqueue Trim 선행**: `QUEUE_LOW`는 Dequeue 시 패킷 크기를 먼저 차감(`_queuesize_low -= pkt->size()`)한 뒤 `decide_ECN()`을 평가합니다. 따라서 큐 크기가 매우 작을 때는 Enqueue 단계에서 Trim으로 먼저 빠져나가 Dequeue 시점 잔여 큐 길이가 ECN 임계치 미만일 수 있습니다.
3. **프로토콜 설계 의미**: **Trim**은 ECN보다 강한 최상위 혼잡 신호로, 수신자가 즉시 `NACK`을 회신해 송신자의 재전송(`TX_RTX`), EV 경로 전환, 윈도우 축소를 직접 유발합니다. 반면 `QUEUE_LOW`를 정상 통과하는 일반 DATA 패킷에는 `-ecn <low> <high>` 임계치에 따라 `ECN_CE`가 마킹됩니다.

### 5.2. Trim → NACK → 송신 측 복구 사이클 ([uec.cpp](file:///root/mrc-sim/htsim/htsim/sim/uec.cpp#L1628-L1721))
1. **스위치 (`CompositeQueue`)**: 큐 포화 시 페이로드를 잘라낸 64B **Trim 패킷**을 생성해 순방향(`QUEUE_HIGH` → 수신자)으로 전달합니다. (`QUEUE_HIGH`까지 포화되면 `SW_BTS`로 스위치에서 직접 송신자 쪽으로 반사 가능)
2. **수신자 (`UecSink`)**: Trim 수신(`RX_TRIM`) 즉시 반대 방향(송신자 쪽)으로 **`NACK`(`TX_NACK`)** 을 회신합니다.
3. **송신자 (`UecSrc::processNack`)**:
   - `updateCwndOnNack(...)`으로 **`_cwnd` 축소** 및 지연 갱신
   - `_tx_bitmap` 해제 후 `queueForRtx()`로 **재전송 큐(`_rtx_queue`) 최우선 등록**
   - 네트워크 중간 스위치 Trim(`!pkt.last_hop()`) 시 **`_mp->processEv(ev, PATH_NACK)`** 로 불량 `EV` 회피
   - `sendIfPermitted()`로 다른 건강한 `EV`를 선택해 즉시 우회 재전송(`TX_RTX`)

### 5.3. 2-Tier Rail-Optimized vs Shared ToR 수용 용량 ([fat_tree_topology.cpp](file:///root/mrc-sim/htsim/htsim/sim/datacenter/fat_tree_topology.cpp#L476-L493))
2-Tier Leaf-Spine에서 스위치 포트 수(Radix)가 $K$일 때 Plane당 엔드포인트 수는 $\text{NSRV} = K^2 / 2$ 입니다.
- **Rail-Optimized (`-planes 8`)**: 최대 8-xPU 서버 수 = $K^2 / 2$ (예: $K=32 \rightarrow 512$대 / 4,096 xPU, $K=64 \rightarrow 2,048$대)
- **Shared ToR (`-planes 1`)**: 최대 8-xPU 서버 수 = $K^2 / 16$ (예: $K=32 \rightarrow 64$대 / 512 xPU, $K=64 \rightarrow 256$대)

### 5.4. 시뮬레이터 및 트레이서 주요 수정 사항
- **[ecnqueue.cpp](file:///root/mrc-sim/htsim/htsim/sim/ecnqueue.cpp#L106-L117)**: `if (_queuesize > _K)` 중괄호 누락으로 모든 통과 패킷에 `SW_ECN`이 거짓 기록되던 버그 수정.
- **[main_uec.cpp](file:///root/mrc-sim/htsim/htsim/sim/datacenter/main_uec.cpp#L798-L800)**: `-planes 8` 다중 Plane 실행을 막던 `assert(false)` 제거.
- **[uec.cpp](file:///root/mrc-sim/htsim/htsim/sim/uec.cpp#L2245-L2248)**: 다중 Plane 장애 재전송 시 `_rtx_queue`가 비었을 때 `assert` 대신 `return 0;`으로 안전 처리.
