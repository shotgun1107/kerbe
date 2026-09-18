# Kerbe CLI 동작 계약 — AI 조회용 현재 구현 참조

확인일: 2026-09-17
코드 기준: `15a23540d9e1c91e2c3c97bb39e749f96002062f`
검증 방식: 저장소 코드 및 기존 테스트 내용 대조. 이번 문서 작성 중 제품 명령·테스트·계정 조회는 실행하지 않았다. 설치된 실행 파일과 이 소스의 일치 여부는 별도다.

이 문서는 현재 구현의 동작 설명이다. 희망 기능이나 승인 전 설계는 포함하지 않는다. UX 의견은 [별도 검토 기록](CLI_UX_REVIEW_2026-09-17.md), 제품 결정은 [DECISIONS](DECISIONS.md)를 읽는다. 코드가 바뀌면 관련 항목과 기준 커밋을 함께 갱신한다. 아래 근거 표의 함수·테스트로 재확인할 수 있다.

## 문서 사용 규칙

후속 실행 순서는 [ROADMAP.md](ROADMAP.md), D-059를 따른다. 이 문서는 1단계의 입력 자료이며, 완료 근거와 미해결 사항은 [상태 대조 결과](STATE_AUDIT_2026-09-18.md)를 읽는다. 2026-09-18 정적 대조로 위 코드 기준이나 CLI 동작이 변경된 것은 아니다.

- 답변 순서: 아래 질문 색인 → 해당 명령의 **동작 계약** → 필요한 경우 상세 규칙과 근거만 읽는다.
- `[C]`는 구현 코드로 확인한 동작이다. `[T]`는 이름을 명시한 기존 테스트에 해당 assertion이 있다는 뜻이다. 이번 세션에서 테스트를 실행했다는 뜻은 아니다.
- 테스트 이름이 옆에 없는 `[C]`를 테스트 검증 완료로 확대하지 않는다. 시나리오의 가상 수치는 실제 사용자 데이터가 아니다.
- 기준 커밋 이후 관련 코드가 바뀌었다면 아래 구현 함수와 테스트를 먼저 재확인한다. 설치본 동작, 개인 DB 내용, 서버의 실제 현재값은 이 문서로 확인할 수 없다.
- 실행 예시는 명령 실행 승인이 아니다. 사용자가 설명만 요청했다면 데이터 변경·계정 조회·sync를 실행하지 않는다.
- 명령에 없는 기능을 내부 스키마의 지원 여부만으로 사용 가능하다고 답하지 않는다. 특히 mapping 해제 데이터 구조와 해제 CLI는 별개다.
- 근거가 없는 질문은 미확인으로 답한다. UX 검토 문서의 요구를 현재 기능으로 혼합하지 않는다.

### 질문 → 조회 위치

| 질문 주제 | 읽을 계약 |
|---|---|
| 설정 경로·도움말·종료 코드·공유 키 필요 여부 | GLOBAL 및 해당 명령 |
| 초기화 위치·복구 키·재초기화 | INIT |
| 최신 기록·중복·수집 결과 숫자 | COLLECT |
| 기간·정렬·필터·열·Markdown | REPORT |
| 남은 구독 한도·reset·로그인 필요 여부 | STATUS |
| 목록의 합계·미분류 누락·alias 이후 행 | PROJECT-LIST, PROJECT-ALIAS |
| 미분류 이유·긴 ID·원본 ID 누락 | PROJECT-UNRESOLVED |
| 세션 귀속·자식 포함·재지정 | PROJECT-LINK |
| 프로젝트 통합·이전 기록·되돌리기 | PROJECT-ALIAS |
| 다른 기기·Git 전송·실패 후 남는 변경 | SYNC |
| 진단 기준·오류와 경고·네트워크 | DOCTOR |

각 계약의 `입력` 행 아래에 옵션 상세가 이어진다. 함수는 저장소 상대경로 링크로 찾고, 테스트는 파일 안에서 정확한 함수명을 검색한다.

## 빠른 답변

| 질문 | 현재 동작 |
|---|---|
| 지금 폴더의 프로젝트만 조회하나? | 아니다. 설정된 로컬 DB가 대상이며 report 기본은 전체 프로젝트·전체 기간이다. |
| report가 새 기록도 수집하나? | 아니다. 먼저 collect로 수집해야 한다. |
| status와 report는 같은 사용량인가? | 아니다. 계정 구독 한도 현재값과 수집된 실제 토큰 집계다. |
| project list에 미분류가 나오나? | 아니다. effective project ID가 있는 사용 기록만 집계한다. |
| 프로젝트 이름을 입력할 수 있나? | report 필터는 정확한 표시 이름 또는 ID를 받는다. link·alias는 전체 project ID만 받는다. |
| alias 후 이전 프로젝트는 목록에 남나? | 원본 기록은 남지만 별도 집계 행은 없어지고 최종 대상의 행으로 합산된다. |
| alias로 새 프로젝트를 만들 수 있나? | 아니다. source와 target 모두 이미 알려진 프로젝트여야 한다. |
| link가 자식 세션까지 연결하나? | 아니다. 지정 thread 자체에 적용하며, 해당 turn의 별도 수동 연결은 thread 연결보다 우선한다. |
| 연결을 취소하는 명령이 있나? | unlink·unalias 명령은 없다. 다른 대상 재지정과 연결 해제는 다르다. |
| doctor는 오프라인인가? | 보장하지 않는다. 유효한 장부 Git 저장소에 대해 origin 읽기 접근도 검사한다. |

## 1. 공통 규칙

### GLOBAL — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 명령 선택, 설정 파일 지정, 도움말·버전 조회 |
| 입력 | 전역 -h/--help, --version, --config PATH. project는 하위 명령 필요 |
| 사전 조건 | 도움말·버전 출력에는 초기화·계정 조회 불필요 |
| 상태 변화 | 옵션 파싱·도움말 자체는 제품 데이터 변경 없음 |
| 보존 | 도움말 요청으로 실제 하위 작업을 실행하지 않음 |
| 출력·종료 | 도움말/버전 0, 잘못된 문법 2. 나머지는 하위 계약 참조 |
| 반복·정정 | 동일 도움말 조회는 설정 변경을 만들지 않음 |
| 실패·제한 | --config는 하위 명령 앞에 지정. 공통 language/units/verbose/json 옵션 없음 |

**근거:** `[C]` [main.py](src/codex_usage/cli/main.py) `_build_parser`, `main`; [config.py](src/codex_usage/config.py) `default_config_path`; [lock.py](src/codex_usage/application/lock.py) `ApplicationLock`.

**상황:** 설정 없음 → `kerbe --help` → 명령 목록 조회 가능. 설정 없음 → `kerbe report` → 설정 없음 오류. `[T]` 설정 누락 오류의 코드 2·traceback 비출력은 [test_cli.py](tests/integration/test_cli.py) `test_expected_failure_is_reported_without_traceback`에서 collect 대상으로 확인한다. 도움말 예시 자체는 `[C]`다.

### 상세 규칙

```powershell
kerbe --help
kerbe --version
kerbe --config "C:\path\config.json" report
```

- 전역 옵션: `-h/--help`, `--version`, `--config PATH`. `--config`는 하위 명령 앞에 둔다.
- 기본 설정: Windows의 `%LOCALAPPDATA%\codex-usage-tracker\config.json`. LOCALAPPDATA가 없으면 홈의 `.local/share/codex-usage-tracker/config.json`.
- `status`는 설정을 읽지 않는다. `report`는 설정을 읽지만 공유 키를 가져오지 않는다. collect·sync·doctor·모든 project 명령은 설정과 공유 키가 필요하다.
- 성공은 종료 코드 0, 처리하는 실행 오류는 2. 잘못된 문법도 argparse가 2로 종료한다. doctor는 경고만 있을 때 0이고 오류가 있으면 2다.
- 도움말·열 이름은 영어이며 결과·고정 오류 접두사 등에 한국어가 섞여 있다. 언어 선택 기능은 없다.
- collect·sync·link·alias는 같은 state DB의 OS 잠금을 사용한다. 동시 변경은 대기 대신 실패한다. 잠금 파일 자체는 종료 후 남을 수 있다.
- 아래 `<...>`는 사용자가 바꿔 넣어야 하는 자리표시자다. 그대로 실행하는 명령이 아니다.

| 명령 | 주요 읽기 대상 | 변경/외부 접근 |
|---|---|---|
| init | 옵션·가져온 복구 키 | 설정·로컬 DB·장부 폴더·비밀 저장소 생성/설정 |
| collect | Codex 로컬 기록, 로컬 Git 근거, 기존 장부 | 로컬 DB·장부·수집 이력·이름 대응표 변경. push 없음 |
| report | 로컬 조회 DB | 기본 읽기만. --markdown이면 파일 저장 |
| status | Codex App Server 계정 한도 응답 | 계정 조회. Kerbe DB·장부 저장 없음 |
| doctor | 원본 메타데이터·DB·장부·Git | 진단만. 조건에 따라 origin 읽기 접근 |
| sync | 장부 및 origin | 장부 저장소 commit/fetch/rebase/push, 조회 DB·이력 변경 |
| project list/unresolved | 조회 DB, unresolved는 Codex SQLite도 조회 | 읽기만 |
| project link/alias | 장부·pending outbox | mapping 추가, outbox 저장 완료, 조회 DB 재생성. push 없음 |

## 2. init — 이 기기 설정

### INIT — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 이 기기의 설정·공유 키·저장 경로 준비 |
| 입력 | --ledger, --codex-home, --state-db, --import-key, --force. 아래 기본값 표 참조 |
| 사전 조건 | 기존 설정이 없어야 함. 교체하려면 --force 필요. 비밀 저장소 접근 필요 |
| 상태 변화 | 새 UUID, 설정 저장, 키 저장, 장부 폴더·로컬 DB 준비 |
| 보존 | 기존 장부 데이터를 자동 삭제·통합하지 않음. Git remote 생성 없음 |
| 출력·종료 | 초기화 완료·기기 ID. 신규 키만 복구 키 출력. 정상 0 |
| 반복·정정 | 기본 재실행은 거절. --force는 새 UUID로 설정 교체이며 원상복구 명령 아님 |
| 실패·제한 | 기존 설정, 잘못된 키, 저장 실패 등 오류 2. 실행 폴더를 프로젝트로 등록하지 않음 |

**근거:** `[C]` [main.py](src/codex_usage/cli/main.py) `_run_init`; [config.py](src/codex_usage/config.py) `save_config`.

**상황:** 별도 설정 경로 지정 → ledger 옵션 없이 init → 그 설정 폴더 아래 ledger 생성. `[T]` [test_cli.py](tests/integration/test_cli.py) `test_init_without_ledger_uses_config_directory`. 기존 복구 키 import → 키를 저장하되 출력하지 않음. `[T]` 같은 파일 `test_init_can_import_existing_recovery_key_without_printing_it`.

### 상세 규칙

```powershell
kerbe init
kerbe init --ledger "C:\path\private-ledger" --import-key
```

| 옵션 | 기본값·동작 |
|---|---|
| --ledger PATH | 설정 파일 폴더 아래 ledger |
| --codex-home PATH | 사용자 홈 아래 .codex |
| --state-db PATH | 설정 파일 폴더 아래 state.sqlite |
| --import-key | 기존 복구 키를 숨김 입력. 생략하면 새 공유 키 생성 |
| --force | 기존 설정 교체 허용 |

새 기기 UUID를 만들고 경로를 절대경로로 저장한다. 장부 폴더와 로컬 DB를 준비하고 공유 키를 비밀 저장소에 저장한다. Windows에서는 Credential Manager를 사용한다. 현재 작업 폴더를 추적 프로젝트로 등록하지 않는다. Git 저장소·origin·원격 저장소를 자동 생성하지 않는다.

출력: 초기화 완료, 기기 ID. 새 키를 만든 경우에만 복구 키를 출력하며 import 시 출력하지 않는다.

반복 실행: 설정이 이미 있으면 기본적으로 오류. `--force`는 단순 점검이 아니라 새 기기 ID와 선택한 키로 설정을 다시 만든다. 기존 장부·DB를 초기화하거나 기존 데이터와 새 키를 자동 통합하지 않는다. 잘못된 복구 키·설정 저장 실패 등은 오류다.

## 3. collect — 사용 기록 수집

### COLLECT — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 로컬 사용 기록을 수집하고 보고서용 DB 갱신 |
| 입력 | 전용 옵션 없음. 설정의 codex_home/state_db/ledger_root 사용 |
| 사전 조건 | 설정·올바른 공유 키·로컬 파일 접근·변경 잠금 획득 |
| 상태 변화 | 이력·cursor·outbox·정제 장부·조회 DB·이름 대응표 갱신 |
| 보존 | Codex 원본은 읽기. 이미 알려진 source event를 신규 기록으로 재추가하지 않음 |
| 출력·종료 | 이번 처리 건수와 경고. 수집 결과에 일부 경고가 있어도 정상 반환은 0 |
| 반복·정정 | 변경 없는 파일 건너뜀. 기존 기록을 임의 초기화하는 복구 동작 없음 |
| 실패·제한 | 충돌·키 불일치 등 2. 자동 수집·push 없음. 실패 시 전체 무변경 보장 아님 |

**근거:** `[C]` [collect.py](src/codex_usage/application/collect.py) `CollectService.collect`, `_collect`; [main.py](src/codex_usage/cli/main.py) `_run_collect`.

**상황:** fixture 첫 수집 → 신규 4건 → 변경 없이 반복 → 신규 0건 → 원본에 turn 추가 → 기존 4건·신규 1건. `[T]` [test_collect_service.py](tests/integration/test_collect_service.py) `test_first_repeat_and_appended_turn_collection`. 파싱 손상 파일 → cursor 미전진은 같은 파일 `test_invalid_complete_rollout_is_quarantined_without_advancing_cursor`.

### 상세 규칙

```powershell
kerbe collect
```

전용 옵션은 없다. 변경된 Codex rollout을 읽어 누적 체크포인트의 증가량을 계산하고, SQLite 계보·Git 근거로 분류한 뒤 정제 이벤트를 로컬 장부에 저장한다. 조회 DB와 로컬 프로젝트 이름도 갱신한다.

- 변경되지 않은 파일은 건너뛴다. 변경된 파일은 처음부터 계산하되 이미 알려진 source event는 다시 추가하지 않는다.
- Codex SQLite가 없거나 읽을 수 없으면 JSONL fallback을 사용하고 경고한다.
- 읽는 중 변경되는 파일·파싱 손상 파일은 다음 실행에서 재시도할 수 있게 cursor를 전진시키지 않는다. 손상 파일을 별도 폴더로 이동하는 기능은 아니다.
- 상속 기준값·증가량 미확인 기록은 보존하되 total delta가 null이면 합계에서 제외한다.
- 실제 체크포인트 충돌, HMAC 키 불일치, 중복 위험이 있는 구형 저장 키 등은 중단 오류다.
- 자동 상시 수집·Git 전송은 하지 않는다. 실패 전 로컬 이력·outbox 등이 기록됐을 수 있으므로 전체 작업이 무조건 원상복구된다고 해석하지 않는다.
- parser_version이 바뀌어도 알려진 source event의 수정 revision을 자동 생성하지 않는다. 장부가 usage 정정 이벤트를 표현할 수 있는 것과 collect의 자동 정정은 다르다(A-04).

출력: 변경 파일/발견 파일, 신규·기존 이벤트, 장부 이벤트, 미분류, 조회 DB generation과 조건별 경고.

여기서 **기존 이벤트는 이번에 다시 계산하다 중복으로 건너뛴 건수**다. 전체 누적 건수가 아니다. 출력의 **미분류는 이번 신규 인코딩 기록 중 project ID가 없는 건수**이며 전체 미분류 잔량이 아니다. generation은 조회 DB를 재생성한 세대 번호다.

## 4. report — 수집된 사용량 조회·Markdown 저장

### REPORT — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 수집된 토큰을 조건별 집계하고 선택적으로 Markdown 저장 |
| 입력 | 기본 전체 기간·전체 프로젝트, group-by project,date, Asia/Seoul. 아래 옵션 표 참조 |
| 사전 조건 | 설정 및 조회 가능한 DB. 공유 키·계정 조회 불필요 |
| 상태 변화 | 기본 조회는 읽기. --markdown만 지정 파일·부모 폴더 생성/교체 |
| 보존 | 장부·사용량 귀속·조회 DB를 바꾸지 않음 |
| 출력·종료 | 요약·표·부분 제공 주석, 저장 시 경로. 빈 결과도 0 |
| 반복·정정 | 동일 DB·조건이면 동일 집계. 상대기간은 실행 날짜에 따라 변함. export는 동일 파일 덮어씀 |
| 실패·제한 | 날짜·그룹·DB·저장 오류 2. 최신 기록 수집·소유자/effort 필터·임의 정렬·열 선택 없음 |

**근거:** `[C]` [main.py](src/codex_usage/cli/main.py) `_run_report`, `_report_dates`; [query.py](src/codex_usage/reports/query.py) `build_usage_report`, `_matches`, `_sort_key`; [render.py](src/codex_usage/reports/render.py) `write_markdown_report`.

**상황:** 동일 프로젝트가 KST 날짜별 30·30토큰 → 날짜별 cumulative 30·60, 제외 1건은 합계에서 제외. `[T]` [test_reports.py](tests/unit/test_reports.py) `test_kst_grouping_cumulative_partial_and_excluded_counts`. Markdown 부모 폴더 생성·저장 내용 일치는 `test_renderers_and_atomic_markdown_write`. 이름 충돌·이전 alias ID 필터 동작은 `_matches`의 `[C]` 근거이며 해당 두 테스트가 검증한다고 주장하지 않는다.

### 상세 규칙

```powershell
kerbe report
kerbe report --period week --group-by project,model,effort
kerbe report --from 2026-09-01 --to 2026-09-17
kerbe report --project "shotgun1107/kerbe"
kerbe report --project unclassified
kerbe report --period week --markdown "C:\reports\usage-week.md"
```

| 옵션 | 현재 의미 |
|---|---|
| --period all/today/week | 기본 all. week는 지정 시간대의 이번 월요일부터 오늘까지. 최근 7일이 아님 |
| --from / --to | 시작·종료 날짜 포함. 한쪽만 지정 가능. today/week와 병용 불가 |
| --timezone | 기본 Asia/Seoul. UTC 원본을 이 시간대의 날짜로 변환 |
| --project | 최종 project ID 또는 현재 표시 이름과 정확히 일치. 미분류는 unclassified 또는 미분류 |
| --model | 모델 문자열 정확히 일치 |
| --device | 기기 ID 또는 표시 이름 정확히 일치 |
| --source | source 문자열 정확히 일치 |
| --group-by | 쉼표 조합. 기본 project,date. 허용: project,date,thread,model,effort,device,source |
| --markdown PATH | 화면에 출력한 집계와 같은 내용을 Markdown 파일로 저장 |

필터는 함께 적용한다. 이름 부분 검색·소유자 필터가 아니다. 표시 이름이 같은 ID가 여러 개면 이름 필터는 그 기록들을 모두 통과시키며 선택 질문을 하지 않는다. 집계 키는 여전히 ID라서 이름이 같아도 자동 병합하지 않는다.

현재 정렬: group-by 순서의 **내부 값**을 문자열 오름차순으로 비교한다. project는 표시 이름이 아닌 ID이고 미분류는 빈 값이다. 날짜는 ISO 날짜 순, effort도 문자열 순이다. 토큰 크기 정렬 옵션은 없다.

### 열과 계산

| 열 | 의미·단위 |
|---|---|
| project/date/thread/model/effort/device/source | 선택한 집계 기준. effort는 추론 강도, source는 기록의 실행 출처 |
| input | 입력 토큰 |
| cache | 캐시에서 읽은 입력 토큰 |
| cache_write | 캐시 쓰기 입력 토큰 |
| output | 출력 토큰 |
| reasoning | 추론 출력 토큰 |
| total | 저장된 증가량의 총 토큰. 캐시·추론 열을 다시 더하지 않음 |
| cumulative | 이번 조회 범위에서 date 외의 그룹 조합별 total 누적값 |
| events | total delta가 있는 사용 기록 수. 메시지 수나 세션 수가 아님 |
| excluded | total delta가 null이어서 합계에서 제외한 기록 수 |

date가 그룹에 없으면 각 행의 cumulative는 해당 행 total과 같다(포함 토큰이 없는 행의 cumulative는 0). 기간 이전의 토큰을 누적 시작값으로 가져오지 않는다. 제외 이벤트는 세부 토큰 합계에서도 제외한다. 필드가 전부 미제공이면 `—`, 일부만 제공됐다면 제공분 합계 뒤 `*`를 붙인다. 미제공을 0으로 표시하지 않는다.

출력: 기간·시간대, 총합·포함/제외 건수, 표, 필요한 경우 부분 제공 주석. 빈 결과는 “조회 조건에 맞는 사용량이 없습니다.”로 표시하며 오류가 아니다.

Markdown: 상대경로는 실행한 현재 폴더 기준이다. 부모 폴더를 만들며 동일 파일은 확인 질문 없이 임시 파일을 통한 교체 방식으로 덮어쓴다. 파일 확장자로 형식을 추론하지 않는다. 저장 후 절대경로를 출력한다.

오류: 없는 DB, 잘못된 날짜·시간대, 역전된 기간, 빈/중복/미지원 group-by. 일치하지 않는 필터는 보통 빈 결과다. export 실패 전 터미널 표가 이미 출력될 수 있다.

## 5. status — 계정 한도 현재값

### STATUS — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 계정의 남은 구독 한도와 초기화 시각 수동 조회 |
| 입력 | --codex-path codex, --timeout 15, --timezone Asia/Seoul |
| 사전 조건 | 실행 가능한 Codex 엔진과 조회 가능한 기존 로그인 상태. Kerbe init 불필요 |
| 상태 변화 | App Server 프로세스 실행·계정 조회·종료. Kerbe 장부/DB에 저장하지 않음 |
| 보존 | 프로젝트 토큰 집계와 매핑을 변경하지 않음 |
| 출력·종료 | 제공된 버킷/기간/%/reset. 정상 응답에 정보가 없어도 안내 후 0 |
| 반복·정정 | 매 실행 현재값 재조회. 과거 snapshot 조회·정정 없음 |
| 실패·제한 | 엔진·시간 초과·응답·시간대 오류 2. 프로젝트별 quota·잔여 토큰 환산 없음 |

**근거:** `[C]` [sources/quota.py](src/codex_usage/sources/quota.py) `find_codex`, `read_rate_limits`, `_query`; [reports/quota.py](src/codex_usage/reports/quota.py) `render_quota`.

**상황:** Kerbe 설정 없음 → status → 설정/키 없이 한도 조회 경로 진입. `[T]` [test_quota_status.py](tests/integration/test_quota_status.py) `test_status_without_config_or_secret_store`(조회 mock). 다중 버킷이 빈 객체이면 legacy가 있어도 정보 없음: `test_empty_map_does_not_reuse_legacy_bucket`. 실제 계정의 현재 잔량은 이 테스트로 확인하지 않는다.

### 상세 규칙

```powershell
kerbe status
kerbe status --timezone Asia/Seoul --timeout 15
kerbe status --codex-path "C:\path\codex.exe"
```

- `--codex-path`: 기본 codex. 실행 파일 탐색 및 Windows 설치 엔진 fallback. 네이티브 실행 파일을 사용한다.
- `--timeout`: 기본 15초. 유한한 값이며 0초 초과 120초 이하여야 한다.
- `--timezone`: 기본 Asia/Seoul.

Codex App Server를 실행해 초기화 후 `account/rateLimits/read`를 한 번 요청하고 종료한다. 기존 Codex 로그인에 의존하며 init·공유 키·Kerbe 설정이 필요 없다. Kerbe 장부·DB에 한도 이력을 남기지 않는다.

다중 버킷 응답을 우선하며 그것이 null/누락일 때만 legacy 응답을 사용한다. 빈 다중 버킷을 legacy로 덮어쓰지 않는다. primary/secondary가 실제 응답에 있을 때만 표시한다.

출력: 조회 시각, 버킷 이름·구분, 기간, 남음/사용 %, 정확한 초기화 날짜·시각·시간대와 남은 시간. 남음은 100-used를 0~100으로 제한한다. 없는 값은 미제공, 지난 reset은 재조회 필요로 표시한다. 현재 출력에는 설명문도 포함된다.

토큰·메시지 잔여량이나 프로젝트별 quota 소모를 계산하지 않는다. 실행 파일 없음·로그인/프로토콜 오류·시간 초과·잘못된 시간대는 오류. 정보 없는 정상 응답은 오류로 단정하지 않고 정보 없음으로 출력한다.

## 6. project list — 집계된 프로젝트 목록

### PROJECT-LIST — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 최종 귀속 프로젝트별 전체 사용량 목록 조회 |
| 입력 | --ids만 선택 가능 |
| 사전 조건 | 설정·일치하는 공유 키·조회 DB |
| 상태 변화 | 없음. 조회만 수행 |
| 보존 | 원본 귀속·mapping·장부 보존 |
| 출력·종료 | project/tokens/threads/events/excluded, 선택 시 ID. 빈 목록도 0 |
| 반복·정정 | 동일 DB이면 동일 집계. 이름 변경·매핑 정정 기능 아님 |
| 실패·제한 | 키/DB 오류 2. 미분류 행·기간 필터·페이지 없음 |

**근거:** `[C]` [project_management.py](src/codex_usage/application/project_management.py) `list_projects`; [query.py](src/codex_usage/reports/query.py) `_load_names`.

**상황:** 프로젝트 P=12, Q=30, 미분류=20 → 목록에는 Q=30, P=12만 표시. `[T]` [test_project_management.py](tests/integration/test_project_management.py) `test_lists_projects_and_resolves_local_raw_thread_id`. P→Q alias 후 Q=42 한 행은 `test_alias_combines_usage_and_rejects_cycle`.

### 상세 규칙

```powershell
kerbe project list
kerbe project list --ids
```

조회 DB의 effective project ID가 null이 아닌 기록을 전체 기간 집계한다. 목록은 프로젝트 등록부가 아니라 **사용 기록의 최종 귀속 프로젝트별 집계**다. 사용 기록이 없는 이름만으로 행을 만들지 않는다.

열: project, tokens, threads, events, excluded. `--ids`는 전체 project_id 열을 추가한다. tokens는 알려진 total 합계, threads는 고유 thread 수(제외 기록의 thread도 포함), events/excluded는 포함/제외 기록 수다. 하나의 thread가 여러 프로젝트에 걸치면 각 프로젝트의 threads에 들어갈 수 있다.

정렬: tokens 내림차순 → 같은 값이면 project ID 순. 이름이 없으면 전체 ID 표시. 미분류 행·기간 필터·소유자 필터·페이지 기능은 없다.

alias가 적용되면 원래 ID의 독립 행은 나오지 않는다. 이름은 최종 대상의 로컬 이름을 우선할 수 있지만 대상 이름이 없으면 연결 전 이름이 이어질 수도 있다. 수동 표시명 mapping이 있으면 자동 이름보다 우선한다. CLI에서 수동 이름을 만드는 명령은 없다.

로컬 Git 이름 대응표는 공유 장부에 저장되지 않는다. 다른 기기에서 장부만 재생성하면 사용량은 복원해도 이 이름 표시는 동일하게 복원된다고 보장하지 않는다.

## 7. project unresolved — 미배정 기록

### PROJECT-UNRESOLVED — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 최종 프로젝트가 없는 사용 기록을 thread별 조회 |
| 입력 | 전용 옵션 없음 |
| 사전 조건 | 설정·일치하는 키·조회 DB. 원본 ID 대응에는 로컬 Codex SQLite 필요 |
| 상태 변화 | 없음. 로컬 원본 ID 대응도 읽기 |
| 보존 | 미분류를 자동 귀속시키지 않음 |
| 출력·종료 | thread 키/로컬 ID/사유/토큰/포함·제외 건수. 빈 목록도 0 |
| 반복·정정 | 같은 데이터면 같은 결과. 수정은 별도 link 명령 |
| 실패·제한 | 조회 DB 오류 2. SQLite 대응 불가면 원본 ID는 -. 제목·후보 저장소·페이지 없음 |

**근거:** `[C]` [project_management.py](src/codex_usage/application/project_management.py) `list_unresolved`, `_local_thread_ids`; [main.py](src/codex_usage/cli/main.py) `_run_project`.

**상황:** 미분류 thread가 로컬 SQLite에 존재하고 20토큰 기록 → 원본 ID, unclassified, 20 표시. `[T]` [test_project_management.py](tests/integration/test_project_management.py) `test_lists_projects_and_resolves_local_raw_thread_id`. 같은 thread의 일부 기록만 미분류면 그 일부만 합산하는 것은 SQL 조건의 `[C]` 근거다.

### 상세 규칙

```powershell
kerbe project unresolved
```

전용 옵션 없음. effective project ID가 null인 사용 기록만 thread별로 모은다. 이미 귀속된 같은 thread의 기록은 이 합계에 넣지 않는다. thread key 순으로 전체 목록을 출력한다.

열: thread_key, local_thread_id, reason, tokens, events, excluded. 로컬 Codex SQLite에서 대응하는 thread를 찾을 때만 원본 ID를 보이고, 못 찾으면 `-`다. 조회 DB 기록은 있어도 SQLite에 없으면 원본 ID를 못 보일 수 있다.

reason은 기록된 project_resolution의 고유 값을 정렬해 쉼표로 나열한다. unclassified는 귀속 미결정, ambiguous_multi_repo는 복수 저장소 때문에 결정되지 않은 상태다. 상세 원인·후보 저장소·제목·작업 경로는 출력하지 않는다.

빈 결과는 “미분류 또는 모호한 작업이 없습니다.”. 조회만 하며 자동 연결하지 않는다.

## 8. project link — 수동 귀속

### PROJECT-LINK — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 지정 thread 또는 turn의 사용량 귀속 프로젝트 지정 |
| 입력 | --thread 또는 --turn 중 하나, --project 전체 ID 필수 |
| 사전 조건 | 설정·키·잠금·알려진 target과 subject. raw thread의 SQLite 존재 예외는 아래 참조 |
| 상태 변화 | 수동 mapping 추가/개정, pending outbox flush, 조회 DB 재생성 |
| 보존 | 원본 사용 이벤트와 과거 mapping 보존. Codex 앱의 세션 위치 보존 |
| 출력·종료 | 기록 완료/변경 없음, revision·generation, 변경 시 sync 안내. 정상 0 |
| 반복·정정 | 동일 최종 target이면 mapping 추가 없음. 다른 target이면 revision 증가. 해제 CLI 없음 |
| 실패·제한 | 잘못된/없는 ID·장부 문제 등 2. turn 수동 지정이 우선. 자식 재귀 적용·이름 선택 없음 |

**근거:** `[C]` [project_management.py](src/codex_usage/application/project_management.py) `link`, `_subject_exists`, `_write_mapping`; [replay.py](src/codex_usage/ledger/replay.py) `replay_ledger_events`.

**상황:** thread를 P에 연결 → revision 1 → 같은 연결 반복 → 새 mapping 없음 → Q로 변경 → revision 2, 이전 이벤트 참조. `[T]` [test_project_management.py](tests/integration/test_project_management.py) `test_manual_link_is_private_idempotent_and_revisioned`. turn 지정 우선은 [test_ledger_replay.py](tests/unit/test_ledger_replay.py) `test_turn_manual_beats_thread_manual_and_alias_is_resolved`. 자식 재귀 미적용은 replay 조회 로직의 `[C]` 근거다.

### 상세 규칙

```text
kerbe project link --thread <원본-thread-ID-또는-thr_h1-ID> --project <전체-prj_h1-ID>
kerbe project link --turn <원본-turn-ID-또는-turn_h1-ID> --project <전체-prj_h1-ID>
```

thread와 turn 중 정확히 하나를 지정한다. target은 `prj_h1_` 뒤 43자리의 유효한 ID여야 하고 알려진 프로젝트여야 한다. 이름·목록 번호로 지정하거나 새 프로젝트를 생성하지 않는다. target이 alias source라면 최종 대상으로 해석한다.

원본 subject ID는 로컬에서 HMAC으로 바꾼다. 장부에 이미 알려진 subject여야 한다. 예외로 raw thread ID는 로컬 Codex SQLite에 존재하면 아직 사용 기록이 없어도 연결할 수 있다. raw turn ID는 해당 변환값이 실제 기록의 turn key와 맞아야 하며 임의로 추측한 값은 연결되지 않는다.

처리: 기존 장부와 pending outbox를 읽고 mapping을 추가 → outbox를 장부에 반영 → 조회 DB 재생성. 같은 상태 저장소의 다른 pending 기록도 함께 반영될 수 있다. 네트워크 전송은 하지 않는다.

- 해당 thread/turn에 있는 과거 사용 기록에 즉시 적용한다. 이후 동일 키의 기록도 replay할 때 mapping을 적용한다.
- 수동 turn 연결 > 수동 thread 연결 > 원래 자동 귀속 순이다. 마지막으로 project alias를 적용한다.
- thread 연결은 자식·후손 thread에 재귀 적용되지 않는다. 날짜 범위를 지정하는 옵션도 없다.
- 같은 대상을 반복 지정하면 mapping을 추가하지 않고 “변경 없음”. 그래도 flush·DB 재생성은 수행한다.
- 다른 대상으로 재지정하면 revision을 올리고 이전 mapping을 supersedes로 참조한다. 원본 사용 기록을 고쳐 쓰지 않는다.
- 수동 지정을 제거하고 자동 귀속으로 되돌리는 CLI는 없다.

출력: “프로젝트 연결 기록 완료/변경 없음”, revision, generation. 새 기록이면 sync 안내. 알 수 없는 subject/target, 잘못된 ID, 장부 불완전 줄·기존 alias cycle 등은 오류다.

## 9. project alias — 프로젝트 집계 통합

### PROJECT-ALIAS — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 기존 project ID를 다른 기존 프로젝트의 집계 대상으로 연결 |
| 입력 | --from 전체 source ID, --to 전체 target ID |
| 사전 조건 | 설정·키·잠금, 두 프로젝트 존재, 순환 없는 관계 |
| 상태 변화 | alias mapping 추가/개정, pending outbox flush, 조회 DB 재생성 |
| 보존 | 원본 사용 이벤트·원래 ID·mapping 이력. 이전 ID의 독립 집계 행은 보존하지 않음 |
| 출력·종료 | 기록 완료/변경 없음, revision·generation, 변경 시 sync 안내. 정상 0 |
| 반복·정정 | 동일 최종 대상으로 반복하면 새 mapping 없음. 다른 대상으로 재지정 가능. 해제 CLI 없음 |
| 실패·제한 | 없는 ID·형식 오류·자기 연결·순환 등 2. 새 프로젝트 생성·상위 그룹 생성 아님 |

**근거:** `[C]` [project_management.py](src/codex_usage/application/project_management.py) `alias`, `_known_project_ids`, `_write_mapping`, `list_projects`; [query.py](src/codex_usage/reports/query.py) `_matches`; [replay.py](src/codex_usage/ledger/replay.py) `_build_aliases`.

**상황:** P=12, Q=30 → P→Q 연결 → 목록 Q=42만 남음 → 같은 연결 반복은 변경 없음 → Q→P는 순환 오류. `[T]` [test_project_management.py](tests/integration/test_project_management.py) `test_alias_combines_usage_and_rejects_cycle`. 아래 3개 프로젝트 사례와 이전 ID report 필터는 코드에서 도출한 `[C]` 사례이며 이 테스트가 직접 검증하는 범위와 구별한다.

### 상세 규칙

```text
kerbe project alias --from <기존-prj_h1-ID> --to <대상-prj_h1-ID>
```

source와 target 모두 유효한 전체 ID이고 장부에서 알려진 프로젝트여야 한다. **이 명령은 target을 새로 만들지 않는다.** `new3` 같은 임의 이름이나 번호를 넣으면 ID 오류다.

이미 별칭인 target은 최종 대상으로 해석한다. source가 자기 자신으로 돌아오거나 순환을 만들면 거절한다. 원본 사용 이벤트를 삭제·복사하지 않고 project alias mapping을 추가한 뒤 조회 DB를 재생성한다.

### 여러 프로젝트를 같은 대상으로 연결한 예

아래 1·2·3은 설명용 기호이며 실제 CLI 입력값이 아니다. 모두 기존 프로젝트이며, 별도 수동 귀속이나 제외 기록이 없다고 가정한다.

| 상태 | project list의 집계 행 |
|---|---|
| 연결 전 | 1: 100 토큰, 2: 200 토큰, 3: 50 토큰 |
| 1 → 3 적용 | 2: 200 토큰, 3: 150 토큰 |
| 2 → 3도 적용 | 3: 350 토큰 |

- 1·2의 원본 이벤트와 원래 project ID는 장부에 남는다.
- project list와 project 기준 report는 최종 ID 3으로 집계한다. 1·2는 별도 집계 행으로 남지 않는다.
- report의 `--project`는 입력된 이전 ID를 alias로 변환하지 않고 **최종 ID/표시 이름**과 비교한다. 이전 ID 1로 필터하면 alias 이전 기록만 따로 조회되는 것이 아니다. 최종 ID 3을 사용해야 한다.
- 서로 다른 프로젝트를 유지하면서 상위 그룹을 만드는 기능이 아니다. 합산에 필요한 계층 관계도 만들지 않는다.
- 명시적 turn/thread 연결이 있으면 먼저 그 귀속을 결정하고 alias를 적용하므로, 원본 ID만 보고 모든 기록이 이동한다고 단정하지 않는다.

반복: 같은 source를 같은 최종 target에 연결하면 “변경 없음”, 그래도 DB는 재생성한다. 같은 source를 다른 유효 target에 재지정하면 새 revision으로 보존한다. alias 해제 명령은 없으며 역방향 alias를 취소 용도로 사용할 수 없다(순환 오류).

alias는 연결을 영속 mapping으로 남기므로 나중에 수집한 기록에도 최종 해석 시 적용된다. target 자체를 나중에 다른 프로젝트로 연결하면 chain을 따라 최종 대상으로 집계한다. 입력 당시 target은 최종 ID로 해석돼 저장되므로, 중간 별칭의 미래 변경을 무조건 따라간다고 가정하지 않는다.

출력: “프로젝트 별칭 기록 완료/변경 없음”, revision, generation, 변경 시 sync 안내. 다른 기기에는 sync해야 전달된다. source/target 없음, ID 형식 오류, 순환, 장부 불완전 줄 등은 오류다.

## 10. sync — 비공개 장부 Git 동기화

### SYNC — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 기기별 정제 장부 파일을 origin과 통합 |
| 입력 | 전용 옵션 없음. 설정된 ledger_root와 origin/current branch 사용 |
| 사전 조건 | 설정·키·잠금, 올바른 장부 Git 루트·허용 변경·원격 접근 |
| 상태 변화 | 실행 이력, 로컬 commit/fetch/rebase, 조회 DB 재생성, 필요 시 push |
| 보존 | 기존 장부 줄의 수정·삭제는 거절. 실패 전 생성한 로컬 커밋은 보존될 수 있음 |
| 출력·종료 | branch/변경 파일/커밋·push 여부/장부 건수/generation. 정상 0 |
| 반복·정정 | 보낼 커밋 없으면 push 불필요. 충돌 자동 해결·실패 전체 rollback 없음 |
| 실패·제한 | 네트워크·충돌·정책 위반 등 2. collect 또는 pending outbox flush를 대신하지 않음 |

**근거:** `[C]` [application/sync.py](src/codex_usage/application/sync.py) `SyncService._sync`; [sync/git.py](src/codex_usage/sync/git.py) `validate`, `validate_own_changes`, `rebase`, `push`.

**상황:** 장부 변경 → sync → 커밋·전송·조회 DB 갱신. `[T]` [test_git_sync.py](tests/integration/test_git_sync.py) `test_sync_commits_pushes_and_rebuilds_read_model`. 로컬 커밋 생성 후 fetch 실패 → 새 로컬 커밋 유지: `test_fetch_failure_preserves_the_new_local_commit`. 실제 개인 원격 설정이 정상이라는 검증은 아니다.

### 상세 규칙

```powershell
kerbe sync
```

전용 옵션 없음. 설정된 ledger_root 자체가 Git 작업 트리 루트여야 하며 origin과 현재 branch가 필요하다. detached HEAD 및 진행 중인 merge/rebase/cherry-pick은 거절한다. init만으로 이 준비가 완료되는 것은 아니다.

처리 순서:

1. 장부 저장소와 변경 경계·장부 내용 검증.
2. 자기 `devices/<device-id>/` 아래 허용되는 JSONL 변경만 stage·commit.
3. origin fetch. 원격 현재 branch가 있으면 로컬 커밋 검증 후 rebase.
4. 깨끗한 작업 트리·보낼 변경 검증, 통합 장부 replay, 조회 DB 재생성.
5. 원격보다 앞선 커밋이 있으면 push.

원격 branch가 없고 로컬 HEAD가 있으면 `remote_branch_missing`으로 중단한다. 최초 원격 branch 게시를 대신하는 명령으로 안내하지 않는다. 자기 기기 외 경로 변경·삭제·이름 변경·과거 줄 수정·비 JSONL 변경은 거절한다.

출력: branch, 변경 파일 수, 커밋 생성 여부, push 완료/불필요, 통합 장부 이벤트·generation. 재실행 시 변경이나 앞선 커밋이 없으면 새 커밋/push 없이 조회 DB를 재생성할 수 있다.

collect를 대신하지 않으며 pending outbox를 직접 flush하지 않는다. 이미 장부 파일에 반영된 기록을 동기화한다. 충돌·네트워크 실패를 자동 해결하지 않는다. 전송 실패 전 만든 로컬 커밋과 일부 로컬 변경은 보존될 수 있고, push 전에 DB 재생성이 끝날 수도 있다. 실행 이력은 성공/실패로 기록한다.

## 11. doctor — 현재 상태 검사

### DOCTOR — 동작 계약

| 필드 | 현재 계약 |
|---|---|
| 목적 | 수집 원천·로컬 저장소·장부·Git 준비 상태 진단 |
| 입력 | 전용 옵션 없음 |
| 사전 조건 | 설정 및 공유 키를 가져올 수 있어야 함. 이후 개별 검사 실패는 아래 표대로 판정 |
| 상태 변화 | 진단만. 유효 Git 저장소라면 origin 읽기 접근 발생 가능 |
| 보존 | 자동 복구·collect·조회 DB 재생성·fetch·push 없음 |
| 출력·종료 | 검사별 OK/경고/오류. 오류가 있으면 2, 경고만이면 0 |
| 반복·정정 | 현재 상태를 다시 검사. 경고를 무시/해제하는 저장 기능 없음 |
| 실패·제한 | 키 자체가 없으면 진단 목록 이전에 오류. 부분 비교를 전체 검증으로 해석하지 않음 |

**근거:** `[C]` [doctor.py](src/codex_usage/application/doctor.py) `run_doctor`, `_run_history_check`, `_check_read_model`, `_check_git_repository`; [main.py](src/codex_usage/cli/main.py) `_run_doctor`.

**상황:** 원격 읽기 접근 실패 → ledger-remote 오류, URL 원문 노출 없음. `[T]` [test_doctor.py](tests/integration/test_doctor.py) `test_remote_access_failure_is_an_error_without_leaking_url`. 초기 로컬 장부가 Git 저장소 아님 → 경고지만 CLI 0: [test_cli.py](tests/integration/test_cli.py) `test_init_collect_and_doctor_user_flow`. read-model의 세 값 비교 범위는 `[C]`이며 토큰 전수 검증 테스트로 해석하지 않는다.

### 상세 규칙

```powershell
kerbe doctor
```

전용 옵션 없음. 아래는 실제 판정 기준이며 개선 제안이 아니다. 정상 `[OK]`, 경고 `[경고]`, 오류 `[오류]`로 표시한다. 오류가 하나라도 있으면 종료 코드 2, 경고만 있으면 0이다. 공유 키 자체가 없으면 CLI에서 오류로 끝나 검사 목록까지 도달하지 않는다.

| 항목 | 현재 검사·판정 |
|---|---|
| shared-key | 가져온 키의 key_id와 설정 비교. 불일치 오류 |
| codex-rollouts | Codex home 없음/발견 실패 오류, 발견 0개 경고, 그 외 OK. 파일 수 표시 |
| codex-state | SQLite 없음 경고, 읽기 실패 오류, 읽으면 thread·spawn edge 수와 OK |
| codex-lineage | inventory 호환성 issue가 있으면 경고, 없으면 OK. state 읽기 성공 시만 출력 |
| codex-versions | 초반 session_meta의 관측 버전. 누락/파싱 불가가 있거나 버전이 없으면 경고. 모든 버전의 전체 기능 호환 인증이 아님 |
| codex-join | JSONL-only ID 또는 rollout_path가 있는 SQLite-only ID가 하나라도 있으면 경고. 양쪽 수를 구분 |
| local-state | DB 없음 경고, 읽기/무결성 실패 오류. 지원보다 새 스키마 오류, 옛 스키마 경고 |
| collection-history / sync-history | 이력 없음/테이블 없음/최신 실행이 성공 아님이면 경고. 최신 성공이면 시각과 OK. 오래됨 임계값 없음 |
| outbox | 미반영 건수 > 0이면 경고 |
| parser-issues | 저장된 parser issue가 있으면 경고와 코드별 건수 |
| classification | 최종 project ID 없는 이벤트가 있으면 경고와 사유별 건수·thread 수 |
| ledger | 장부 읽기·스키마·privacy·key·replay 검증. 검증 실패 오류, 불완전 줄 경고 |
| ledger-git | Git 미설치/잘못된 준비 상태/허용 밖 변경 오류. Git 저장소가 아직 아니면 경고. 허용 변경이 대기 중이면 경고 |
| ledger-remote | 저장소 validate 성공 후 origin의 ls-remote 읽기 검사. 실패 오류 |
| read-model | 저장된 key_id·입력 이벤트 수·유효 usage 수를 replay 결과와 비교. 없거나 불일치면 경고 |

read-model은 모든 행·토큰 필드를 전수 비교하는 검사가 아니다. 선행 데이터가 없거나 읽기 실패면 일부 후속 항목은 출력되지 않는다. “건너뜀” 상태를 별도로 표시하지 않는다. ledger는 단순 JSON 형식 검사만 하는 것이 아니다.

기본 실행에서도 원격 검사가 가능하며, --online/--offline/--verbose/--json 옵션은 없다. Git 원격 검사는 읽기이며 fetch·commit·push하지 않는다. 진단 자체가 문제를 복구하거나 조회 DB를 재생성하지 않는다.

## 12. 코드·테스트 근거와 유지보수

아래 테스트는 **내용을 읽어 대조한 기존 테스트**다. 이번 문서 작성에서 실행해 통과시켰다는 뜻이 아니다. 테스트가 모든 세부 동작을 다룬다고 주장하지 않는다.

| 범위 | 구현 근거 | 기존 테스트 근거 |
|---|---|---|
| 옵션·dispatch·종료·init | [cli/main.py](src/codex_usage/cli/main.py): _build_parser, main, _run_init; [config.py](src/codex_usage/config.py) | [test_cli.py](tests/integration/test_cli.py), [test_config_and_secrets.py](tests/unit/test_config_and_secrets.py) |
| collect | [collect.py](src/codex_usage/application/collect.py): CollectService; [lock.py](src/codex_usage/application/lock.py) | [test_collect_service.py](tests/integration/test_collect_service.py), [test_legacy_fork_counters.py](tests/unit/test_legacy_fork_counters.py) |
| report | [query.py](src/codex_usage/reports/query.py): _matches, _sort_key, build_usage_report; [render.py](src/codex_usage/reports/render.py) | [test_reports.py](tests/unit/test_reports.py) |
| 이름 표시 | [query.py](src/codex_usage/reports/query.py): _load_names; [project_names.py](src/codex_usage/storage/project_names.py) | [test_local_project_names.py](tests/unit/test_local_project_names.py) |
| project 전체 | [project_management.py](src/codex_usage/application/project_management.py): list_projects, list_unresolved, link, alias, _write_mapping | [test_project_management.py](tests/integration/test_project_management.py) |
| alias 후 목록 | 같은 파일: list_projects의 effective_project_id 집계 | test_alias_combines_usage_and_rejects_cycle: 12+30이 42인 한 행으로 나오는지 검증 |
| mapping 우선순위 | [replay.py](src/codex_usage/ledger/replay.py): replay_ledger_events | [test_ledger_replay.py](tests/unit/test_ledger_replay.py) |
| status | [sources/quota.py](src/codex_usage/sources/quota.py), [reports/quota.py](src/codex_usage/reports/quota.py) | [test_quota_status.py](tests/integration/test_quota_status.py) |
| sync | [application/sync.py](src/codex_usage/application/sync.py), [sync/git.py](src/codex_usage/sync/git.py) | [test_git_sync.py](tests/integration/test_git_sync.py) |
| doctor | [doctor.py](src/codex_usage/application/doctor.py): run_doctor, _check_read_model 등 | [test_doctor.py](tests/integration/test_doctor.py) |

명령 동작을 변경할 때는 옵션/기본값, 저장·네트워크 부작용, 반복·정정 동작, 출력·종료 코드, 위 근거를 함께 갱신한다. 실제 구현과 문서가 다르면 먼저 해당 함수와 테스트를 확인하고 문서의 근거 날짜를 갱신한다.
