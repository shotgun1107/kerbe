# Changelog

## Unreleased

- 프로젝트·배포 패키지·기본 CLI를 Kerbe / `kerbe`로 변경; `codex-usage` 호환 별칭과 기존 데이터 경로 유지

- Windows 설치 스크립트로 CMD·PowerShell 어디서든 `kerbe` 실행
- `init`의 장부 경로를 생략하면 로컬 설정 폴더 아래 장부 생성

- `kerbe status`: Codex App Server의 계정 한도 버킷별 남은 비율·초기화 시각·조회 시각 표시
- 장부 초기화 없이 수동 조회, 시간 초과·오류 처리, 누락값과 지난 reset 시각 구분
- quota 영속 저장·자동 갱신·reset 소비·그래픽 UI는 포함하지 않음

## 0.1.0 — release candidate

- Codex JSONL 누적 체크포인트를 실제 delta로 변환
- SQLite spawn-edge와 rollout 계보를 이용한 멀티에이전트 귀속
- Git remote 기반 프로젝트 통합과 미분류 수동 연결·alias
- HMAC 비식별화, append-only JSONL 장부, Windows Credential Manager
- 다기기 Git sync와 재생성 가능한 SQLite read model
- 프로젝트·날짜·thread·모델·기기별 terminal·Markdown 보고서
- 확장 doctor와 로컬 bare remote 기반 다기기 acceptance
- Windows에서도 KST 보고서가 동작하도록 IANA 시간대 데이터 포함

구독 한도·reset 수집과 Codex 채팅 여백 UI는 0.1.0 핵심 범위에 포함하지 않는다.
