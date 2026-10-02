# Kerbe

프로젝트명과 기본 명령어는 **Kerbe / `kerbe`**입니다. 독일어로 새긴 홈·눈금을 뜻하며, 사용 기록을 하나의 장부에 새긴다는 의미를 담습니다.

이전 `codex-usage` 명령은 호환용 별칭으로 유지합니다. 기존 기록을 이어 쓰도록 로컬 설정 디렉터리 `codex-usage-tracker`, Credential Manager 대상 `CodexUsageTracker/...`, Python 내부 모듈 `codex_usage`와 장부 스키마는 유지합니다. 이름 변경을 위해 다시 초기화할 필요는 없습니다.

여러 기기와 멀티에이전트 작업에 흩어진 Codex 토큰 소비를 파악·비교하는 CLI입니다. 다양한 사용자에게 공유할 도구를 목표로 합니다. 현재 구현은 Git 저장소 기반이며, [확정한 다음 제품 철학](CLI_PHILOSOPHY.md)의 목적 기반 프로젝트·자동 수집 조회·한도 관측/추정·제목 암호화는 아직 적용되지 않았습니다.

현재 구현된 핵심 기능은 다음과 같습니다.

- HMAC 기반 project·thread·turn 식별자
- Git remote URL 정규화
- origin·unique remote·ambiguous remote 선택 규칙
- Codex rollout JSONL metadata·token parser
- 신규·resume·fork·compact delta와 fork 복사 중복 제거
- Codex SQLite thread·spawn-edge read-only adapter
- turn 도구 실행 경로의 로컬 Git 판별
- 부모·자식·fork 계보 복원과 turn별 프로젝트 귀속
- crash-safe source cursor·SQLite outbox
- revision·void·manual mapping·alias를 적용하는 결정적 ledger replay
- 실패 시 직전 세대를 보존하는 SQLite read model 재생성
- 기기별 append-only JSONL writer와 partial-line 내성 reader
- 체크인된 JSON Schema 검증과 경로·remote·raw ID 개인정보 guard
- Windows Credential Manager 기반 공유 HMAC 키 보관
- 변경 rollout 감지와 `init·collect·sync·report·doctor` CLI
- 기기별 변경 경계·append-only 검증을 적용한 fail-closed Git 동기화
- 프로젝트 목록·미분류 조회와 append-only 수동 연결·별칭 CLI
- JSONL/SQLite join·버전·분류·이력·원격 권한을 확인하는 확장 doctor
- 표준 라이브러리 기반 단위 테스트

Codex 대화·코드·명령·로컬 경로·raw remote는 중앙 장부에 저장하지 않는 것을 원칙으로 합니다. 공개 소스 저장소와 사용자별 비공개 데이터 장부는 분리합니다.

## 현재 CLI 사용법

아래는 **현재 구현의 사용법**입니다. 후속 설계에서는 init을 로컬 시작, sync를 일회성 장부 합류 설정으로 바꾸고 collect를 사용자 명령에서 제외하기로 했지만 아직 구현하지 않았습니다. 현재는 아래 수동 수집·동기화 절차와 공유 HMAC 키가 필요합니다. [확정 명령 설계](CLI_COMMAND_DESIGN.md)를 현재 사용법으로 실행하지 마세요.

현재 후속 작업은 [확정 진행 방향](ROADMAP.md)을 따릅니다. [1단계 정적 대조 결과](STATE_AUDIT_2026-09-18.md)에 현재 구현·문서 불일치·검증 공백을 정리했습니다. 2026-09-30 CLI 철학 1~7은 확정했고 다음은 명령 체계·출력 설계입니다. 유지보수 조사는 미착수이며, 승인된 목표를 현재 기능으로 안내하지 않습니다. [미결정 목록](OPEN_QUESTIONS.md)과 [논의 기록](CLI_DESIGN_REVIEW.md)을 함께 관리합니다.

명령별 입력·출력·실패 동작은 [CLI 동작 참조](CLI_REFERENCE.md), 개발 참여와 검증 방법은 [CONTRIBUTING](CONTRIBUTING.md)에서 확인할 수 있습니다.

### Windows 명령어 등록

프로젝트 폴더의 PowerShell에서 한 번 실행합니다.

```powershell
.\scripts\install_cli.ps1
```

프로젝트 전용 `.venv`에 설치하고 사용자 PATH에 `kerbe` 실행 파일만 등록합니다. 새 CMD·PowerShell 창에서는 현재 폴더와 관계없이 아래처럼 실행할 수 있습니다. 기존 터미널 앱이 이전 PATH를 유지하면 앱을 완전히 종료한 뒤 다시 엽니다.

```text
kerbe status
kerbe init
kerbe collect
kerbe report
```

`init`의 기본 장부는 로컬 설정 폴더 아래 `ledger`입니다. GitHub 연결 없이 로컬 수집·조회부터 시작할 수 있습니다. 다른 기기에서 이미 만든 공유키가 있다면 `init --import-key`를 사용합니다. Git 동기화에는 별도의 비공개 장부 저장소 설정이 필요합니다.

명령어는 프로젝트의 `.venv`를 사용하므로 프로젝트 폴더를 유지해야 합니다. 코드 갱신·폴더 이동 후에는 설치 스크립트를 다시 실행합니다.

### 남은 구독 한도 조회

```powershell
kerbe status
kerbe status --timezone Asia/Seoul --timeout 15
```

기존 Codex CLI의 ChatGPT 로그인을 통해 계정별 한도 버킷의 남은 비율과 초기화 시각을 조회합니다. `init`이나 프로젝트 장부 설정은 필요하지 않습니다. 기간은 서버 응답대로 표시하므로 항상 5시간·주간 두 창이 모두 나오지는 않습니다. 프로젝트별 토큰 집계는 기존 `report`를 사용합니다.

PATH에 Codex가 없으면 Windows의 `%LOCALAPPDATA%\Programs\Codex*` 설치 폴더에서 번들 엔진을 찾습니다. 여러 엔진이 있으면 파일 수정 시각이 가장 최근인 것을 선택합니다. 직접 선택하려면 `--codex-path 'C:\path\to\codex.exe'`로 지정합니다. Windows의 `.cmd`·`.bat`·`.ps1` 래퍼는 지원하지 않습니다. 기본 제한시간은 15초이며 오류 시 로그인·연결 상태를 확인한 뒤 재조회합니다. 자동 로그인이나 reset credit 사용은 수행하지 않습니다.

조회값은 장부·DB에 저장하지 않습니다. 누락값은 `미제공`으로 표시하고, 지난 초기화 시각은 재조회가 필요하다고 표시합니다. 남은 비율을 토큰·메시지 개수로 환산하지 않습니다.

### 설치와 프로젝트 토큰 수집

일반 설치:

```powershell
python -m pip install .
```

개발용 editable 설치:

```powershell
python -m pip install -e .
```

로컬 수집·조회는 Git 저장소 없이 `kerbe init`으로 시작할 수 있습니다. 장부 경로를 직접 정하려면 다음 예시를 사용합니다. 기기 간 `sync`에는 별도로 준비한 비공개 Git 장부 저장소와 origin 설정이 필요합니다.

```powershell
kerbe init --ledger C:\path\to\private-ledger
```

첫 초기화에서 표시되는 복구 키는 다른 기기 연결에 필요합니다. Git이나 일반 텍스트 파일에 저장하지 말고 비밀번호 관리자 등에 보관합니다. 두 번째 기기는 다음 명령을 실행하고 복구 키를 화면에 표시되지 않는 입력창에 붙여 넣습니다.

```powershell
kerbe init --ledger C:\path\to\private-ledger --import-key
```

수집, 장부 동기화, 진단:

```powershell
kerbe collect
kerbe sync
kerbe doctor
```

`collect`는 변경되지 않은 rollout을 건너뛰고, 변경된 rollout만 누적 기준선부터 다시 계산한 뒤 이미 저장된 `source_event_id`를 제외합니다. 손상됐거나 계속 쓰이는 파일은 cursor를 전진시키지 않고 다음 실행에서 재시도합니다.

`sync`는 자기 기기의 `devices/<device-id>/` 아래에 추가된 JSONL만 커밋합니다. 전체 장부의 schema·privacy·HMAC key를 검사한 뒤 `fetch → rebase → replay → push`하며, 충돌·과거 줄 수정·다른 경로 변경은 자동 해결하지 않고 중단합니다. 전송 실패 시 로컬 커밋은 다음 재시도를 위해 보존됩니다.

프로젝트·날짜별 사용량을 조회하거나 Markdown으로 남깁니다.

```powershell
kerbe report
kerbe report --period week --group-by project,date,model
kerbe report --from 2026-08-01 --to 2026-08-31 --project <ID-or-name>
kerbe report --markdown reports\usage.md
```

지원 필터는 project·model·device·source이며, 그룹은 project·date·thread·model·effort·device·source를 조합할 수 있습니다. 날짜는 기본 `Asia/Seoul` 기준입니다. `delta=null` 이벤트는 합계에서 제외하고 건수를 별도로 표시합니다.

자동 분류되지 않은 작업을 확인하고 기존 프로젝트에 연결합니다.

`collect`는 확인한 Git 저장소 이름을 로컬 DB에 보관합니다. `report`와 `project list`는 익명 ID 대신 `소유자/저장소명`을 표시하며, 이름을 확인하지 못한 경우만 ID를 표시합니다. 이름 대응표는 공유 장부에 전송하지 않습니다. 원래 ID가 필요하면 `kerbe project list --ids`를 사용합니다. 저장소 이름 변경 전 기록에는 당시 이름이 표시될 수 있습니다.

```powershell
kerbe project list
kerbe project unresolved
kerbe project link --thread <raw-thread-id-or-thr_h1-id> --project <prj_h1-id>
kerbe project alias --from <old-prj_h1-id> --to <current-prj_h1-id>
kerbe sync
```

`project unresolved`는 이 기기의 Codex SQLite에서 원본 thread ID를 찾을 수 있을 때만 로컬 화면에 표시합니다. `project link`는 입력받은 원본 ID를 즉시 HMAC 식별자로 바꾸며 Git 장부에는 원본 ID를 기록하지 않습니다. 같은 연결은 멱등 처리하고, 연결 변경은 이전 mapping을 가리키는 새 revision으로 보존합니다.

`doctor`는 Codex JSONL·SQLite 조인, 관측 CLI 버전, 파서 경고, 마지막 수집·동기화 상태, pending outbox, 미분류 작업, 장부와 조회 DB 일치 여부, Git 원격 읽기 권한을 검사합니다. 진단 메시지에는 경로·remote·원본 thread ID를 표시하지 않습니다.

## 테스트

```powershell
python -m unittest discover -s tests -t . -v
```

2026-09-16 Windows에서 구형 fork 수집 오류 수정과 로컬 프로젝트 이름 표시를 포함한 전체 182개 테스트가 모두 통과했습니다. 실제 codex-cli 0.154.0 연결에서도 한도 조회를 확인했습니다. Kerbe 이름 변경 후 CMD·PowerShell 명령 실행과 설치된 스키마 로딩을 확인했습니다. 로컬 장부의 프로젝트 9개에 저장소 이름을 대응시켜 목록·보고서의 합계 변화 없이 표시되는 것을 확인했습니다.

기존 v1 검증에서는 로컬 bare remote 기반 두 기기의 수집·동기화·수동 연결·보고와 새 clone의 DB 재생성을 확인했습니다. 실제 비공개 GitHub에서는 합성 이벤트의 push·clean clone 재생성·doctor 검사와 임시 브랜치 삭제가 통과했습니다. wheel을 소스 checkout 밖의 새 가상환경에 설치해 version·schema·CLI entrypoint를 검증했습니다. 실제 로컬 익명 검증에서는 사용량 이벤트 56,208개를 70개 프로젝트·날짜 행으로 집계하고 터미널·Markdown 보고서를 0.628초에 생성했습니다.

## 문서

- [개발·Git·검증 규약](CONTRIBUTING.md)
- [확정 CLI 철학](CLI_PHILOSOPHY.md)
- [명령 설계와 현재 구현의 차이](CLI_COMMAND_DESIGN.md)
- [진행 방향](ROADMAP.md) · [미해결 사항](OPEN_QUESTIONS.md)
- [초기 실사용 검토 기록](PHASE1_REVIEW_TODO.md)

- [프로젝트 브리프](PROJECT.md)
- [v1 PRD](PRD.md)
- [중앙 장부 스키마](SCHEMA.md)
- [v1 아키텍처](ARCHITECTURE.md)
- [결정 기록](DECISIONS.md)
- [자료조사](RESEARCH.md)
- [변경 기록](CHANGELOG.md)
- [v1 release smoke checklist](RELEASE.md)
