# Changelog

## Unreleased

- 문서(2026-09-30): 사용자·Claude·GPT 논의를 종합해 CLI_PHILOSOPHY에 철학 1~7과 충돌 보충·최종 2건을 보존. D-060~066으로 기존 v1 정책의 변경 범위 기록. 프로젝트/PRD·진행·미결정·UX/조사 문서 갱신, 현 CLI·스키마/아키텍처와 목표 분리. 코드·테스트·설정·장부 변경 및 제품 검증 실행 없음.

- 문서(2026-09-18, 1단계): 구현·문서·기존 테스트의 정적 대조 보고 추가. 초기화/버전별 parser/파일 cursor/자동 정정의 요구 차이와 검증 공백 기록. report/replay·sync 순서, partial line 처리, Git 없이 로컬 시작 가능한 범위 정정. 제품 코드 및 테스트 변경·재실행 없음.

- 문서(2026-09-18): D-059로 후속 순서 확정 — 문서·검증 관리 → CLI 규칙 정의 → 유지보수 조사 → CLI 규칙 적용 → 기능 개발. 1단계 이후 2·3단계 병행 가능. ROADMAP을 진행 정본으로 두고 기존 문서의 재개 안내를 연결. 제품 코드·스키마 변경이나 신규 테스트 실행은 없음.
- 문서: 전체 CLI의 현재 동작 계약·상황별 사례·코드/기존 테스트 근거와 사용자 UX 검토 기록 추가. 제안과 구현을 구분.

- 프로젝트 목록·보고서에서 로컬 Git 근거로 확인한 저장소 이름 표시, 전체 ID는 `project list --ids`로 조회

- 구형 `rollout-N` turn ID를 파일의 thread 범위로 구분해 수집 충돌 방지
- 압축된 fork의 상속 카운터와 기준값이 없는 첫 이벤트를 새 사용량으로 합산하지 않음
- 동일 체크포인트의 온전한 카운터 이력이 있을 때만 미확인 delta 보완; 실제 수치 충돌은 계속 중단

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
