# 1단계 현재 상태·문서 불일치·검증 공백

작성일: 2026-09-18
범위: D-059 / ROADMAP 1단계
기준: main, `15a23540d9e1c91e2c3c97bb39e749f96002062f`의 제품 코드
결과: **정적 대조 완료. 제품 정상 동작의 재인증이나 설치본 검증 완료가 아니다.**

## 1. 조사 방식과 한계

PROJECT·PROCESS·DECISIONS·PRD·ARCHITECTURE·SCHEMA·README·RELEASE·CHANGELOG·RESEARCH·OPEN_QUESTIONS, ADR 관련 문구, ROADMAP, CLI_REFERENCE, UX/TODO를 대조했다. CLI 진입점과 명령 서비스, parser·파일 snapshot·encoder·replay·조회/출력·Git 동기화·진단·설정, 배포 설정과 기존 테스트의 관련 assertion을 읽었다.

- 코드와 테스트를 수정하지 않았다. 실제 장부·Codex 원본·인증정보를 읽지 않았다. 계정 API·공식 분석 기능의 보류 조사를 재개하지 않았다.
- 테스트를 실행하지 않았다. 기존 테스트의 존재·검증 내용을 확인한 것과 이번 실행 결과를 구별한다.
- 설치·네트워크 smoke·Git 원격 조회·커밋·푸시는 하지 않았다.
- 작업 시작 시 문서 변경과 새 문서가 이미 미커밋 상태였다. 제품 코드·테스트·pyproject.toml의 tracked diff는 없었다.
- tests의 `def test` 선언은 182개다. 이는 테스트 통과 수가 아니며 skip·실제 실행 여부도 증명하지 않는다.
- 과거 182개 통과와 Windows/Ubuntu·실제 GitHub 검증은 RELEASE의 해당 날짜 기록으로 유지한다. 현재 원격 CI·현재 설치본·현재 실사용 데이터 정확성은 미확인이다.

## 2. 현재 구현 범위와 근거

| 범위 | 코드에서 확인한 구현 | 기존 검증 근거 | 이번 판단 |
|---|---|---|---|
| init/공통 CLI | 7개 최상위 명령, project 4개 하위 명령, 설정·키 저장 | test_cli, test_config_and_secrets | 현재 동작은 CLI_REFERENCE. 초기화 요구 일부는 A-01 미충족 |
| collect | 변경 파일 재계산·source event 중복 제외·outbox·장부·조회 DB | test_collect_service, test_legacy_fork_counters | 반복 수집·구형 fork 처리 근거 존재. 자동 정정은 A-04 별개 |
| 귀속 | turn 활동 Git·자기 Git·계보·수동 mapping, alias | test_project_attribution_engine, test_attribution, test_ledger_replay | 연구 목적 귀속이나 자식 일괄 수동 연결까지 완료된 것은 아님 |
| report/목록 | effective project 기준 필터·집계·로컬 이름·Markdown | test_reports, test_local_project_names, test_project_management | UX 신규 후보 미구현. 이름 조회와 이름으로 변경 명령 입력은 다름 |
| link/alias | append-only mapping revision·반복 멱등·순환 거절 | test_project_management, test_ledger_replay | 해제 CLI 없음. 변경 없음이어도 flush·DB 재생성 가능 |
| status | App Server 한도 조회, 다중 버킷·reset·오류 처리 | test_quota_status의 mock 및 모의 프로세스 | 실제 계정 최신 응답 검증은 아님 |
| sync | 자기 기기 장부 commit→fetch→rebase→검증/rebuild→push | test_git_sync, test_two_device_workflow | 로컬 bare remote 합성 검증과 실사용 다기기 배치는 별개 |
| doctor | 원천 메타데이터·운영 이력·장부 replay·Git 원격 읽기 | test_doctor, test_cli | 지원 버전 인증·전체 DB 수치 대조가 아님 |
| 저장·privacy | 스키마 guard·HMAC·중복/revision replay·재생성 rollback | test_usage_encoder, test_ledger_validation, test_ledger_jsonl, test_read_model | 원본 장부/조회 DB와 비밀 저장소는 역할 분리 |
| 배포 | kerbe와 codex-usage entrypoint, Python>=3.12, Windows 설치 스크립트 | test_package_metadata 및 과거 RELEASE | 현재 설치본과 소스 일치는 이번에 확인하지 않음 |

## 3. 발견한 불일치와 처리

종류는 `문서 오류`, `요구-구현 차이`, `범위 혼동`으로 구분한다. 요구-구현 차이는 미구현 기능을 요구사항에서 삭제해 숨기지 않고 현황을 주석으로 남겼다. 아래 번호는 추적 ID이며 구현 우선순위가 아니다.

### A-01 — init 요구와 실제 초기화 범위

- 종류: 요구-구현 차이 / 미해결.
- 문서: PRD FR-001의 기본 시간대 설정, 장부의 기존 key ID 일치 확인.
- 코드: `cli/main.py::_run_init`과 `config.py::AppConfig`에는 시간대 필드·옵션이 없다. report/status에 각각 Asia/Seoul 기본값이 있다. init은 기존 장부를 읽어 키를 비교하지 않는다. collect/sync 등에서 이후 검사한다.
- 영향: init 성공만으로 기존 장부와 키가 맞는다고 판단하면 안 된다. --force는 새 UUID를 만들며 안전한 재설정 검증을 대신하지 않는다.
- 처리: PRD에 구현 차이 명시. 요구 유지/변경 또는 구현 여부는 후속 결정. init을 수정하지 않음.
- 근거: test_init_without_ledger_uses_config_directory, test_init_can_import_existing_recovery_key_without_printing_it는 생성/import를 검증하며 기존 장부 키 검증까지 증명하지 않는다.

### A-02 — 버전별 parser와 지원 버전 진단

- 종류: 요구-구현 차이 / 미해결.
- 문서: PRD FR-002의 cli_version별 adapter, FR-012의 지원·미지원 버전 확인. ADR-0002도 versioned adapter를 설계 방향으로 기록한다.
- 코드: `sources/codex_jsonl.py::parse_rollout`은 구조 기반 단일 parser다. cli_version은 metadata로 읽는다. `doctor.py::_check_cli_versions`는 관측·파싱 가능한 버전을 표시하며 호환성 allowlist를 판정하지 않는다.
- 처리: PRD·ADR에 구현 범위 주석. 모든 관측 버전을 지원한다고 표현하지 않는다.

### A-03 — 파일 cursor 정체성과 재작성 경고

- 종류: 요구-구현 차이 / 미해결.
- 문서: PRD FR-003은 파일 이동에도 thread 식별자로 같은 원천을 인식하고, 잘림·재작성 시 경고한다고 기술한다.
- 코드: `sources/rollout_files.py::rollout_source_id`는 절대경로 해시다. 이동 시 새 cursor가 된다. 변경 snapshot은 완전한 줄을 처음부터 반환하며 usage 중복은 별도의 source event ID에서 제거한다. 전용 잘림·재작성 경고 코드는 없다.
- 영향: 파일 cursor의 동일성과 토큰 이벤트 중복 제거를 혼동하면 안 된다. 재작성된 기존 source event의 정정은 A-04와 연결된다.
- 근거: test_source_id_is_stable_and_path_specific, test_truncation_and_replacement_are_returned_as_changed는 경로별 ID·변경 감지를 확인한다. 이동 후 end-to-end 무중복 검증과 동일하지 않다.
- 처리: PRD에 차이 명시. ARCHITECTURE의 “새 줄만 읽기” 표현은 변경 파일의 전체 완전 줄 재계산으로 정정.

### A-04 — revision 스키마 지원과 자동 parser 정정은 다름

- 종류: 범위 혼동 / 자동 정정 미구현.
- 코드: `privacy/encoder.py::encode`는 usage revision=1, supersedes=None을 만든다. `CollectService._collect`는 알려진 source event를 건너뛴다. parser_version 변경만으로 기존 usage의 수정 revision을 생성하는 경로는 없다.
- 구현된 것: replay의 revision·voided 처리 및 manual mapping 재지정 revision.
- 영향: parser 업데이트 후 collect만 재실행하면 과거 사용량도 자동 수정된다고 안내할 수 없다.
- 근거: test_latest_revision_wins_and_voided_event_is_removed는 만들어진 정정 이벤트를 replay하는 테스트다. collect가 정정 이벤트를 만드는 테스트가 아니다.
- 처리: PRD·ARCHITECTURE·SCHEMA에 구분 명시. 자동 정정 방식/CLI는 별도 기능 결정 대상.

### A-05 — report 데이터 흐름과 mapping 순서

- 종류: 문서 오류 / 정정 완료.
- 이전 ARCHITECTURE: report 흐름에 매번 장부 replay가 포함된 것처럼 보이며 alias→manual 순서로 기술.
- 코드: `main.py::_run_report`는 조회 DB를 읽는다. `ledger/replay.py::replay_ledger_events`는 turn manual→thread manual→원본 project를 선택하고 alias를 마지막에 적용한다.
- 처리: 장부→DB 생성과 report 조회를 분리하고 순서를 정정.
- 근거: test_turn_manual_beats_thread_manual_and_alias_is_resolved.

### A-06 — sync 처리 순서

- 종류: 문서 오류 / 정정 완료.
- PRD FR-009의 설명은 fetch·통합 후 자기 파일을 commit하는 것처럼 적혀 있었다.
- 실제: `SyncService._sync`는 로컬 장부 검증·자기 변경 commit 후 fetch/rebase, 통합 검증·DB 재생성, push 순이다. D-046 및 기존 아키텍처 sync 도식과 일치한다.
- 처리: PRD 순서 정정. push 실패가 전체 rollback을 뜻하지 않음을 유지.
- 근거: test_fetch_failure_preserves_the_new_local_commit.

### A-07 — 먼저 Git 장부를 준비해야 한다는 README 안내

- 종류: 문서 오류 / 정정 완료.
- README 일부는 먼저 비공개 Git 장부를 준비해야 한다고 안내하지만 D-055와 init 구현은 Git 없이 로컬 사용 시작을 지원한다.
- 처리: Git 연결은 다기기 sync에 필요하다고 문구 수정. 기본 init과 명시적 장부 경로 예시를 구분.

### A-08 — partial line 읽기와 복구 주체

- 종류: 문서 설명 불완전 / 정정 완료.
- ARCHITECTURE는 partial line을 다음 실행까지 기다린다고만 기술했다.
- 실제: Codex 원본의 미완성 줄은 읽기 대상에서 제외한다. Kerbe 장부 reader도 불완전 끝줄을 무시하지만, writer는 자기 대상 파일의 partial tail을 잘라내고 pending 이벤트를 저장할 수 있다. sync/link/alias는 읽은 장부에 partial issue가 있으면 중단한다.
- 처리: 원본과 장부, 읽기와 writer 복구를 구분. 원본 수정으로 오해하지 않게 함.
- 근거: test_reader_ignores_and_writer_recovers_partial_final_line.

### A-09 — schema/DB 기능과 사용자 CLI 기능의 혼동

- 종류: 범위 혼동 / 구분 명시 완료.
- quota_snapshot, project_name/device_name, voided·mapping 해제 표현은 schema/replay에서 다룰 수 있어도 이를 모두 만드는 CLI가 있는 것은 아니다.
- 현재 status는 quota를 저장하지 않는다. 수동 이름 설정·unlink·unalias·독립 rebuild CLI도 없다. collect/sync/link/alias 내부에서 DB를 재생성한다.
- 장부만으로 사용량 조회 데이터를 재생성하는 것과, 로컬에서만 저장한 Git 표시명을 복원하는 것은 다르다.
- 처리: SCHEMA에 범위 주석, CLI_REFERENCE에 관련 제한 보강. 기존 이름 대응표의 rebuild 보존은 test_local_names_survive_rebuild_without_entering_ledger로 확인되며 새 기기에 이름을 전송한다는 의미가 아니다.

### A-10 — 구형 turn ID 예외가 PRD에 빠짐

- 종류: 문서 누락 / 정정 완료.
- PRD FR-004는 fork 복사 turn의 전역 ID 처리만 설명하고 D-056의 구형 rollout-N 예외를 명시하지 않았다.
- 처리: thread 범위 ID와 미확인 fork baseline 제외를 D-056/057에 연결. 기존 정책 변경 없음.
- 근거: test_local_recovery_ids_are_separate_in_memory_and_ledger, test_missing_fork_prefix_never_counts_inherited_total.

### A-11 — 진단 성공 범위와 새 UX 후보

- 종류: 오해 위험 / 현재 제한 확인.
- doctor read-model OK는 key_id·입력 이벤트 수·유효 usage 수 일치다. 모든 토큰 필드 일치 확인이 아니다. 이력 오래됨 임계값, JSON, offline/online 분리, 건너뜀 표시, 새 device-id 검사는 없다.
- CLI_REFERENCE에는 실제 판정을 이미 명시했다. UX 문서의 Claude 제안은 현재 코드 평가로 자동 채택하지 않는다.
- 언어·단위 설정, 정렬·열 선택, 소유자 필터, 이름으로 link/alias는 아직 후보이며 현재 parser에는 없다.
- 처리: 추가 기능 구현 없음. 2단계 규칙 정의의 입력으로 유지.

### A-12 — “검증 완료”의 시점과 대상

- 종류: 범위 혼동 / 구분 명시 완료.
- 테스트 정의 182개, 과거 통과 기록, 실제 개인 다기기 장부 배치, 현재 설치본의 결과는 서로 다르다.
- `.github/workflows/ci.yml`에 Windows/Ubuntu 테스트·wheel 설정은 있지만 이번에 원격 run 상태를 조회하지 않았다.
- `test_windows_credentials`는 임시 Credential Manager 항목을 실제 생성/삭제한다. Windows CI에서는 skip한다. 파일만 확인했다고 실행한 것으로 기록하지 않는다.
- `test_private_github_smoke`는 URL 파서·합성 이벤트 검증이며 실제 GitHub push 테스트 자체가 아니다. 별도 script 실행 기록과 구분한다.

## 4. 검증 공백 — 테스트 신설·실행은 하지 않음

아래는 관련 기존 테스트 파일에서 직접 확인한 범위와 부족한 범위다. “직접 테스트 미확인”은 곧 버그 확정이라는 뜻이 아니다.

| ID | 확인할 시나리오 | 현재 근거와 공백 | 다음 담당 단계 |
|---|---|---|---|
| V-01 | init --force, 다른 키의 기존 장부와 결합 | 기본/import 테스트는 있음. 기존 데이터 안전성·실패 순서 직접 검증 미확인; A-01 요구 차이 | 2에서 정책, 4/5에서 구현·검증 범위 결정 |
| V-02 | 파일 archive 이동 후 재수집 및 동일 source 내용 재작성 | snapshot/path 단위 테스트 있음. 이동→collect 전체 흐름과 자동 정정은 별개 | 3 조사 또는 후속 기능 범위 |
| V-03 | alias A→C/B→C, 재지정, 이전 ID report 필터 | 두 프로젝트 합산·반복·cycle 테스트 있음. 다중 source·연쇄 재지정·report 이전 ID 조합의 직접 테스트 미확인 | 2 정책 검토 후 4/5 |
| V-04 | CLI --turn, thread/turn 수동 지정 충돌, 자식 범위 | replay 우선순위 테스트 있음. CLI 테스트는 주로 --thread. 자식/미래 자식 범위의 CLI 직접 테스트 미확인 | 2 정의 후 4/5 |
| V-05 | 날짜별 필터와 오늘/주간 경계 | KST 날짜·누적·필터 테스트 있음. CLI today/week의 월요일·자정 경계를 고정 시계로 검증한 테스트 미확인 | 4 관련 변경 검증 |
| V-06 | 같은 이름의 프로젝트 필터·alias 이름 fallback | 로컬 이름/수동 이름 우선 테스트 있음. 동명 필터 및 복수 alias 이름 선택 직접 테스트 미확인 | 2 이름 규칙 후 4 |
| V-07 | doctor 수치 손상 탐지 | 정상·경고·원격 실패 테스트 있음. count는 같고 token 값만 다른 DB는 현재 검사 범위 밖 | 2 진단 의미 정의 후 4/5 |
| V-08 | sync 실패의 단계별 상태 | fetch 실패 커밋 보존·로컬 다기기 합성 테스트 있음. 실제 개인 다기기 배치·현재 원격 상태 미확인 | 별도 운영 검증 승인 시 |
| V-09 | 도움말/목록/보고서 성능 | 0.16/6.13/1.68초 단발 관찰뿐. 구간 계측·cold/warm 반복 미실시 | 3 유지보수 조사 |
| V-10 | 현재 소스와 사용자 설치본 일치 | 배포 스크립트는 non-editable pip install. 문서/소스 수정만으로 설치본이 갱신되지 않음 | 4 적용 후 설치·smoke 범위 결정 |

## 5. 이번 단계에서 수정한 것과 남긴 것

수정한 것은 문서뿐이다. README의 Git 준비 안내, ARCHITECTURE의 읽기·mapping·partial line 설명, PRD의 오래된 순서/예외 및 구현 차이 주석, SCHEMA의 표현 가능 범위와 CLI 생성 범위, ADR-0002의 현재 구현 주석을 정리했다. 요구-구현 차이 A-01~04는 기능을 구현하거나 승인 요구를 폐기하지 않고 미해결로 남겼다.

문서 역할도 유지한다: ROADMAP은 순서, DECISIONS는 승인 이력, PRD는 요구, CLI_REFERENCE는 코드 기준 현재 동작, 이 문서는 차이와 검증 공백이다. 코드에 맞춰 요구사항을 조용히 낮추지 않는다.

**1단계 완료 조건:** 현재 구현·문서 차이·기존 테스트 범위와 남은 검증을 추적 가능하게 남겼다. 이번 정적 검토는 완료다. 코드 정상성·실사용 데이터 완전성·성능 개선 완료를 선언하지 않는다. 다음 선택 가능한 범위는 2단계 CLI 규칙 정의와 3단계 코드 변경 없는 유지보수 조사이며, 이 보고서 작성으로 자동 착수하지 않는다.
