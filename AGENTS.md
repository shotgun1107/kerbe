# AI 작업 진입점

파일럿은 사람 직접 merge·수동 정리로 시작한다. 자동 archive는 비활성이다.
아래 고정 merge 명령은 사람 실행용 참고다. 사람이 상태·설정을 명시적으로 전환하기 전에는 실행하지 않는다.

작업 전에 [CONTRIBUTING.md](CONTRIBUTING.md)를 **전체 읽는다**. 공통 개발·Git·검증·권한 규약의 정본은 그 문서이며 여기에는 복제하지 않는다.
이 파일은 K12 Paseo 운영 정본 v2.4를 Kerbe에 적용한 agent 실행 지침이다. 운영 정본 원문과 P0 실측·복구 기록은 repo 밖 사람 운영 자료에 있으며 여기에 복제하지 않는다.

시작 순서:
1. CONTRIBUTING의 작업 전 상태 확인 절차를 수행한다.
2. [ROADMAP](ROADMAP.md)과 해당 `.ai/tasks/` 기록에서 현재 범위를 확인한다.
3. 제품 판단은 [CLI_PHILOSOPHY](CLI_PHILOSOPHY.md)·[DECISIONS](DECISIONS.md), 현재 동작은 [CLI_REFERENCE](CLI_REFERENCE.md)의 질문 색인→명령 계약→코드/테스트 순으로 찾는다.
4. 관련 명세·코드·테스트를 대조하고 CONTRIBUTING의 검증·전달 절차를 따른다.

진행 중 CLI 설계 기록: [.ai/tasks/docs-cli-design.md](.ai/tasks/docs-cli-design.md).
기기 간 전달 기록: [SYNC](SYNC.md). 나머지 문서 지도는 CONTRIBUTING을 따른다.

## 적용 범위

- 독립적으로 합칠 결과 하나 = task worktree 하나 = branch 하나 = PR 하나.
- 구현·테스트·문서는 같은 결과에 묶는다. L 작업은 독립적인 M 크기 slice로 나눈다.
- 원본 checkout(`~/workspace/kerbe/`)에서는 소스 편집·commit·설치·테스트·생성물 출력을 하지 않는다.
- git이 아닌 scratch는 예외다. 파일럿에서 trunk-direct는 사용하지 않는다.
- 최초 main 생성과 원본·공통 Git 설정 관리는 사람이 수행한다.
- 사람이 Paseo에서 준비한 task worktree를 사용한다. 추가 worktree는 사람의 생성 요청이 있을 때만 만든다.
- detached review·경쟁 구현도 추가 생성 요청과 목적이 있어야 한다.
- 한 worktree에는 활성 workspace 하나만 둔다. provider 교대를 archive로 처리하지 않는다.
- 요청 범위 밖의 새 결과를 임의로 시작하지 않는다. 배정된 작업의 commit·branch push·PR 생성은 수행한다.

## 불변 원칙

1. 변경은 해당 task worktree에서만 한다.
2. worktree당 writer는 하나다. 사람의 편집도 포함한다.
3. 리뷰는 고정 full head SHA에 대해 수행하고 결과에 SHA를 남긴다.
4. 중단·교대 전에 상태를 기록하고 의도한 변경을 commit·push한다.
5. main에는 사람이 명시적으로 승인한 대상만 반영한다.

교대 전에 이전 writer의 명령·하위 agent·heartbeat 종료를 확인한다.
source 변경은 commit한다. 비밀값·ignored runtime을 commit하지 않는다.
workflow patch 예외는 아래 보존 규칙을 따른다.
push 실패와 local-only commit을 기록하며 백업 완료로 표시하지 않는다.
검증 결과는 통과 / 실패 / 미실행으로 구분한다.

## 재개

1. 위 시작 순서를 따르고 진행 중 task(`.ai/tasks/`) 또는 PR의 handoff를 읽는다. Kerbe에는 STATE.md가 없다.
2. cwd·branch·기준 commit·현재 HEAD·commit log·diff를 확인한다.
3. 기록과 실제 Git·runtime 상태를 대조한다.
4. 이전 실행 종료와 setup 상태를 확인하고 필요한 검증만 수행한다.
5. 기록된 Next부터 진행한다.

compaction 후에도 위 상태를 재확인한다. 정상적이면 같은 세션을 이어간다.
역할·provider 변경, 문맥 혼선, 제약 망각, 반복 실패는 세션 교체 신호다.
추가 agent는 사람이 요청한 범위에서만 생성한다. shell·CLI도 동일하다.

## Handoff

- task 기록 경로는 CONTRIBUTING 2절의 `.ai/tasks/<type>-<task-name>.md`다.
- M·L slice·R은 시작 시 추적되는 task를 기본으로 만든다. 유효한 PR handoff가 있으면 중복 생성하지 않는다.
- S는 미완료로 교대할 때 task를 만든다.
- 목표·Acceptance·기준 SHA·writer·주요 결정·완료 commit·검증·Next·함정을 적는다.
- runtime 식별자와 필요한 데이터 보존 상태를 남긴다. 비밀값은 쓰지 않는다.
- task는 대체로 한 화면으로 유지하고 원격 복원이 가능하게 push한다.
- task의 지속할 정보를 PR·정본으로 옮겨 저장을 확인한 뒤 task를 삭제한다.
- 삭제 직후부터 Draft 여부와 관계없이 진행 기록은 PR에 남긴다.
- 세션 종료 때문에 삭제한 task를 다시 만들지 않는다. task와 PR에 별개 최신 handoff를 유지하지 않는다.
- 사람이 응답하지 않으면 승인된 목표·범위의 독립적인 일만 진행한다.
- 필요한 질문을 묶고 checkpoint와 차단 사유를 task·PR에 남긴 뒤 막힌 경로를 멈춘다.
- 범위·권한 확대나 불명확한 부작용·merge를 추정 승인하지 않는다. 새 작업·agent·반복 재시도로 대기를 피하지 않는다.

## Git과 merge

- 작업 기준은 최신 origin/main이다. 의존 branch에서 분기하면 기준과 이유를 기록한다.
- base 갱신은 깨끗한 작업 트리·index에서 시작한다. merge 전 HEAD·대상 base full SHA를 확인하고 merge → 관련 check → push 순서로 한다.
- main 직접 push·force push·기존 commit amend·공유 history 재작성을 하지 않는다.
- 의도한 변경만 stage하고 실제 provider의 Agent 트레일러(`Agent: claude` 또는 `Agent: codex`)를 붙인다.
- 채택 요청에 변경 결과·Acceptance 근거·diff/검증 링크·후보 full SHA·리뷰 방식/SHA·남은 위험과 base 상태를 제시한다.
- 기본은 사람 직접 merge다. 검토 동안 writer를 멈추고 직전 head·검사·리뷰를 다시 대조한다.
- AI merge 상태 줄이 없거나 불명확하면 AI merge는 비활성으로 취급하며 agent는 merge를 실행하지 않는다.
- 아래 AI merge 절차는 사람이 상태를 활성으로 바꾼 뒤에만 적용한다. 그때도 해당 명령의 매회 사람 승인만 인정한다.
- 채팅의 “ㅇㅋ”를 merge 승인으로 쓰거나 agent가 활성 상태를 추정하지 않는다.
- main 반영 승인을 별도 migration·비용 발생·데이터 삭제 승인으로 확대하지 않는다.
- 승인한 SHA는 미리 조회해 고정하며 실행 시점의 HEAD로 대체하지 않는다.
- 실행이 허용된 경우에만 아래를 실제 값으로 채운 단일 명령을 사용한다. 미확정 값이 있으면 실행하지 않는다.

```bash
gh pr merge <PR_NUMBER> --repo shotgun1107/kerbe --squash --match-head-commit <APPROVED_FULL_HEAD_SHA>
```

- 변수·명령 치환·리다이렉트·명령 연결·다른 호출 형태로 승인 규칙을 우회하지 않는다.
- --admin·--auto·--delete-branch·merge queue를 사용하지 않는다.
- head가 바뀌면 필요한 검사·리뷰 기록을 갱신하고 다시 승인받는다.
- head 일치는 base 최신 검증을 대신하지 않는다.
- 사용자·project·local의 권한 설정과 rules 파일, AGENTS의 AI merge 상태 줄을 수정하지 않는다. 단, base 갱신으로 main의 AI merge 상태 줄을 그대로 받는 것은 허용한다. 필요한 변경은 사람에게 제안한다.
- 권한 규칙을 스스로 완화하거나 다른 호출 경로로 우회하지 않는다. 변경은 트리거 6번 리뷰 대상이다.
- 사람이 명시적으로 요청한 차단 시험만 지정한 무해한 대상·호출로 한 번 시도한다. 거부되면 다른 방법을 시도하지 않고 결과만 보고한다. 업무 PR에는 적용하지 않는다.
- 권한 막힘을 Full Access·Bypass·sudo·rootful Docker로 해결하지 않는다.

## 검증과 리뷰

- 실제 repo check와 변경에 필요한 검증을 수행한다. skipped·neutral·미실행을 실제 통과로 적지 않는다.
- 새 동작에는 의미 있는 테스트를 추가한다. 형식적인 테스트를 강제하지 않는다.
- 크기와 무관하게 다음 중 하나면 독립 리뷰한다. 마지막 writer의 반대 provider를 우선한다.
  - 인증·권한·비밀정보, DB 스키마·migration·데이터 삭제/변환.
  - 공개 API·CLI·설정 계약, 동시성·비동기·캐시.
  - 새 의존성·major 갱신, CI·Docker·setup·agent 권한/지침.
  - 실패 해결 대신 테스트 기대값·검사 범위를 바꾸거나 반복 실패 후 방향을 바꿈.
  - PRD·ARCHITECTURE·ADR의 의미 있는 변경 또는 큰 변경.
- 반대 provider가 불가하면 사람이 위험·근거를 보고 대체 리뷰를 선택한다. agent가 임의로 바꾸지 않는다.
- 실제 검토 방식·SHA·한계를 기록한다. 필요한 독립 검토가 미실행이거나 고위험의 충분한 근거가 없으면 Ready·merge를 보류한다.
- 리뷰어는 source·설정·task를 수정하지 않는다. 지적 반영은 writer가 한다.
- 읽기 전용 리뷰의 쓰기·sandbox 밖 실행 승격은 승인하지 않는다.
- 리뷰 결과의 최종 위치는 아래 지도의 PR 코멘트다. 기존 권한으로 쓸 수 없거나 미확인이면 응답에 결과·검토 full SHA·PR 미기록 사실을 남겨 사람에게 전달을 요청한다.
- 사람이 writer 세션에 전달하면 writer가 원문·검토 SHA를 바꾸지 않고 PR 코멘트로 옮긴다. reviewer와 대리 게시 사실을 표시하고 게시를 확인한다.
- 리뷰 입력은 Acceptance·고정 SHA diff·관련 코드·검증 결과다.
- 결과에 심각도·위치·실패 조건·근거·SHA·미확인 항목을 적는다.
- 같은 worktree 검증은 writer와 충돌하는 실행이 끝난 뒤 한다.
- 원본 Local에서는 고정 SHA의 Git 객체만 정적으로 읽는다.
- 독립 실행은 요청받아 준비한 detached SHA·별도 config·DB 환경에서만 한다.
- task 승격·삭제 후 만든 최종 후보 SHA에 필수 검사·리뷰의 PR 기록을 연결하고 Ready로 전환한다. 필요한 리뷰의 PR 기록이 없으면 Ready로 전환하지 않는다.

## Setup과 runtime

- Kerbe에는 paseo.json·Makefile·scripts/dev-setup·lockfile·.env.example이 없다. 존재한다고 가정하지 않는다.
- setup은 아래 지도의 pip 명령을 사용한다. 의존성은 pyproject.toml 범위 지정만 있고 고정 lockfile이 없다.
- setup 변경(paseo.json·setup script 추가 포함)은 먼저 merge해 새 worktree가 읽도록 한다.
- setup에서 전체 테스트/빌드를 하지 않는다.
- 기존 .env는 유지한다. Kerbe는 현재 .env를 요구하지 않는다.
- 완료 표시가 없거나 관련 조건이 바뀌면 원인을 확인하고 setup을 검증한다.
- 버전 임의 변경·권한 전면 완화·DB 강제 초기화로 우회하지 않는다.
- runtime은 repo와 worktree 전체 경로 기반으로 식별하고 소유 관계·충돌을 확인한다.
- branch 이름으로 포트를 계산하지 않는다. Kerbe는 현재 웹 서비스가 없다. 도입하면 PASEO_PORT를 사용한다.
- 수동 worktree에서는 Git으로 경로를 확인한다. 식별 실패 시 공용 기본 DB로 진행하지 않는다.
- `kerbe`의 기본 `--config`는 사용자 공용 경로(`%LOCALAPPDATA%` 또는 `~/.local/share`의 `codex-usage-tracker/config.json`)이며 실제 개인 장부·SQLite와 연결될 수 있다. 수동 실행은 worktree별 임시 `--config`을 명시하고, 개인 장부 접근 경계는 CONTRIBUTING의 Kerbe 적용 정보를 따른다.

## Workflow 권한 예외

- agent가 새로 작성·수정·삭제한 `.github/workflows/` 변경은 일반 작업 branch에 commit하지 않는다. 토큰 권한으로 예외를 추정하지 않는다.
- 기준 full SHA와 patch를 준비하고 사람이 별도 branch·PR로 반영하도록 넘긴다.
- 작은 비밀값 없는 텍스트 patch는 관련 Draft PR 코멘트에 원문이 보존됐는지 확인한다.
- 원격 보존 또는 사람 수신 확인 전에는 patch를 버리거나 백업 완료로 표시하지 않는다.
- 이미 main에 반영된 workflow를 그대로 받는 base 갱신은 신규 작성과 구분해 아래 절차를 따른다.
- base merge 중 workflow 충돌이 나면 해결·commit·push를 멈춘다. merge 전 HEAD·대상 base full SHA와 충돌 경로를 응답 또는 PR에 먼저 기록한 뒤 `git merge --abort`한다.
- abort 후 HEAD가 merge 전 SHA인지, 작업 트리·index가 깨끗한지 확인한다. 실패·거부·복원 미확인 시 강제 reset하지 않고 남은 상태·오류를 사람에게 보고한다.
- 실측에서 base push가 허용되면 일반 merge·check·push를 유지한다.
- 권한 거부가 확인됐으면 writer를 멈추고 local/remote head 일치·깨끗한 상태를 먼저 확인한다.
- 사람이 Update with merge commit 또는 권한 있는 환경에서 갱신한 뒤 fetch·fast-forward only로 받는다.
- 이미 local merge 후 push가 거부됐으면 그 commit을 보존하고 사람에게 그대로 전달하는 복구를 우선한다.
- local/remote가 갈라졌으면 멈추고 대조한다. force push·강제 reset으로 맞추지 않는다.
- head 변경 후 관련 check·리뷰·승인 기록을 갱신한다. token 권한을 임의로 확대하지 않는다.

## Docker와 보존

Kerbe는 현재 Docker·Compose를 사용하지 않는다. 첫 네 항목은 도입할 때 적용하며 도입 자체가 트리거 6번 대상이다.

- rootless를 유지하고 개발 포트는 127.0.0.1의 고포트만 게시한다.
- DB·volume·Compose project를 worktree별로 분리한다. 공유 DB·고정 container_name을 쓰지 않는다.
- source 쓰기가 필요하고 이미지가 지원할 때만 container UID 0을 우선 검토한다.
- DB·cache는 named volume을 우선한다. 필요한 영속 데이터는 teardown 삭제 범위 밖에 둔다.
- 일시중단은 worktree 유지다. 7일 경과나 push 완료만으로 archive하지 않는다.
- archive 전 종료 결정·미보존 source/commit 없음·필요한 runtime 보존·관련 실행 종료를 확인한다.
- 자동 archive 또는 Acceptance·검증 근거에 필요한 데이터는 Ready 전에 보존한다. external volume은 백업이 아니다.
- 자동 삭제가 꺼진 나머지 보존·정리 대기는 PR에 남긴 채 merge할 수 있다. 삭제 전 보존 조건은 그대로 적용한다.
- teardown은 정확히 이 worktree 소유 자원만 정리하고 오류·잔여 자원을 밖에 기록한다.
- 보관 표시와 실제 정리 완료를 구분한다. archive 재시도가 같은 teardown을 안전하게 반복한다고 가정하지 않는다.
- 전역 volume prune·다른 작업 자원 삭제를 하지 않는다.
- 기존 서버 서비스와 데이터는 개발 자원 정리 대상이 아니다.
- 부작용 명령 중단 후 실제 결과부터 확인한다. 결과를 판별할 수 없으면 해당 쓰기를 멈추고 요청 식별자를 보존한다.
- Git lock은 실행 중인 Git 프로세스를 확인한 뒤 판정한다.
- 파괴적 복구 전 source와 필요한 untracked·ignored 데이터까지 실제로 보존한다.

## 명령과 문서 지도

확인하지 않은 명령을 존재한다고 가정하거나 성공 결과를 만들지 않는다. 검증 절차의 정의는 [.github/workflows/ci.yml](.github/workflows/ci.yml)과 CONTRIBUTING의 Kerbe 적용 정보다.

| 항목 | Kerbe 실제 값 |
|---|---|
| setup | `python -m pip install .`, 개발용 `python -m pip install -e .` |
| test | `python -m unittest discover -s tests -t .` |
| package/build check | `python -m pip wheel --no-deps . --wheel-dir dist` |
| lint / typecheck | 없음. CI에도 정의되지 않음 |
| dev / db-up / migration | 별도 명령 없음. DB는 로컬 SQLite이며 `src/codex_usage/storage/schema.py`의 `DATABASE_VERSION` 기준으로 `src/codex_usage/storage/sqlite.py` 연결 시 자동 적용된다. 실제 사용자 DB의 migration은 승인 범위를 확인한다 |
| task / STATE | `.ai/tasks/`. STATE.md 없음. 감사 기록은 [STATE_AUDIT_2026-09-18](STATE_AUDIT_2026-09-18.md) |
| PRD / ARCHITECTURE / ROADMAP / DECISIONS / RESEARCH | repo root의 [PRD](PRD.md), [ARCHITECTURE](ARCHITECTURE.md), [ROADMAP](ROADMAP.md), [DECISIONS](DECISIONS.md), [RESEARCH](RESEARCH.md) |
| ADR | `docs/adr/0001`~`0007`. 기존 번호 체계를 유지한다 |
| 핫 파일 | `src/codex_usage/cli/main.py`의 명령 등록 영역, `src/codex_usage/storage/schema.py`, `schemas/ledger-event-v1.schema.json`, `pyproject.toml`, `src/codex_usage/__init__.py`의 `__version__`. lockfile 없음 |
| 사람 운영 문서 | home-dev-ops의 설정·복구 문서. repo 안 링크는 미기재 |
| AI merge 설정·검증 | 상태는 상단 상태 줄을 따른다. 차단·활성화 검증 기록은 home-dev-ops에 있으며 repo 안 링크는 미기재 |
| 리뷰 기록 위치 | 해당 PR의 리뷰 코멘트. 작성 불가·미확인 시 사람 전달·writer 대리 게시 절차는 ‘검증과 리뷰’를 따른다 |
| workflow 실측 결과 | 실제 token의 base 반영 결과 미기재. 기록 전까지 ‘Workflow 권한 예외’의 보수적 경로를 따른다 |

CLAUDE.md는 이 파일을 import한다. 공통 규칙을 복제하지 않는다.
코드와 문서가 다르면 버그·사양 변경·낡은 문서 중 무엇인지 판단한다.
같은 사실의 정본은 한 곳으로 정하고 나머지는 링크한다.
