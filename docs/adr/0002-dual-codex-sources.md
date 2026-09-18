# ADR-002: JSONL과 SQLite 이중 원천

상태: 승인됨

날짜: 2026-08-26

## 상황

JSONL은 token checkpoint·모델·turn·Git 이력을 제공하지만 직접 spawn-edge가 없다. SQLite는 thread 인덱스·spawn-edge·최신 합계를 제공하지만 상세 token 이력이 없다.

## 결정

- JSONL을 token·turn·모델·Git의 상세 원천으로 사용한다.
- SQLite를 thread inventory·rollout 위치·spawn-edge·최신 합계 검증에 사용한다.
- `threads.id = rollout UUID = 첫 session_meta.id`로 조인한다.
- 두 원천은 항상 read-only로 연다.
- Codex 내부 스키마는 versioned adapter 뒤에 격리한다.

구현 대조(2026-09-18): 이 항목은 설계 의도다. 현재 JSONL parser는 버전별 dispatch가 아닌 구조 기반 단일 parser이며, doctor도 지원 버전 목록을 판정하지 않는다. 요구 변경 여부를 확정하지 않고 [1단계 대조 A-02](../../STATE_AUDIT_2026-09-18.md)에 차이로 기록했다.
- SQLite 사용 불가 시 JSONL-only로 수집하되 lineage 불완전 경고를 남긴다.

## 대안

- JSONL만 사용: 직접 부모 관계와 빠른 inventory가 약하다.
- SQLite만 사용: token 세부값과 과거 checkpoint를 복구할 수 없다.
- SQLite 파일 공유: 바이너리 충돌과 개인정보 위험이 생긴다.

## 결과

- 더 정확한 집계가 가능하지만 두 원천의 일관성 검사가 필요하다.
- Codex 버전 변화가 adapter별 테스트 부담으로 남는다.
