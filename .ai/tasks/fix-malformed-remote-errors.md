# malformed remote 오류 정규화 작업 상태

갱신: 2026-10-10 · 이 파일이 이 작업의 유일한 handoff 정본이다. PR 본문에는 별도 최신 handoff를 두지 않는다.

## 목표와 Acceptance

- 목표: `src/codex_usage/domain/git_remote.py`의 `_parse_url_remote`에서 `urlsplit(remote)`가 내는 `ValueError`를 기존 `RemoteNormalizationError` 계약으로 정규화한다. malformed metadata/inventory remote가 기존 project attribution fallback과 collect 이름 후보 처리를 중단시키지 않게 하는 독립 결함 수정 하나다.
- Acceptance:
  1. `normalize_remote("ssh://[2001:db8::1/repo.git")`, `normalize_remote("https://[not-an-ip]/repo.git")`가 `RemoteNormalizationError`를 낸다.
  2. 세션 metadata remote가 malformed여도 `ProjectAttributionEngine`이 주입된 fake `git_probe`의 cwd remote로 fallback한다(`UNIQUE_REMOTE`, `github.com/example/project`).
  3. 선택 module 두 개와 CI 절차(전체 unittest, wheel)가 통과한다. URL 형태·API·출력 계약은 확장하지 않는다.

## 범위

- 포함: `_parse_url_remote`의 `urlsplit` 예외 변환(Codex 단계), 회귀시험 `tests/unit/test_git_remote.py::NormalizeRemoteTests::test_malformed_ipv6_url_remotes_are_rejected`, `tests/unit/test_project_attribution_engine.py::ProjectAttributionEngineTests::test_malformed_session_remote_falls_back_to_cwd_git_probe`.
- 제외(기록만): `src/codex_usage/sources/git.py:103`의 `resolve_remote`가 `RemoteNormalizationError`를 내면 `project_attribution.py:319`는 `(GitProbeError, OSError)`만 잡으므로 cwd 저장소의 malformed remote가 attribution을 중단시킬 수 있다(git_probe 예외 adapter 문제). 이번 범위 밖이며 고치지 않는다.
- 실제 Git 원격·계정·DB·원본 Codex 자료, `scripts/private_github_smoke.py`, 실제 `kerbe init/collect/sync`·계정 명령은 사용하지 않는다. fixture는 합성 문자열과 fake probe 주입만 쓴다.

## Base·Writer·단계

- Branch `fix/malformed-remote-errors`, base `efd539a6ab5cd05a2c7f33cf3b8db13c021458be`(= 작업 시작 시 `origin/main`).
- 순차 Writer 교대: Phase1 Claude(Opus 5.5) → Phase2 Codex. 한 시점에 writer는 하나다.
- 현재 유일한 source writer는 Codex다. Supervisor의 Claude idle·종료 확인과 복원 gate 승인을 받아 기존 worktree를 인수했다. Claude는 다시 쓰지 않는다. 추가 agent/worktree는 만들지 않았다.
- Phase1(Claude): 격리 runtime, baseline, RED 회귀시험과 handoff를 완료했다. checkpoint `ce96e381385bfc09829819309c1381c8ddf0a529`는 local/remote/PR #5 HEAD 일치·clean으로 확인했다. PR은 OPEN·Draft이며 checkpoint의 Windows/Ubuntu CI는 모두 FAILURE다(실패 상세는 조회하지 않음).
- 이 handoff를 담은 checkpoint commit은 자기 SHA를 파일에 담을 수 없다. `git log --oneline efd539a..origin/fix/malformed-remote-errors`로 확인한다.

## 결정

- 수정 위치는 `_parse_url_remote` 한 곳. 기존 port 처리(`parsed.port`의 `ValueError` → `RemoteNormalizationError`)와 같은 형태로 `urlsplit` 호출을 감싼다. 호출부(collect, project_attribution)는 이미 `RemoteNormalizationError`를 잡으므로 변경하지 않는다.
- RED의 세 오류는 모두 `urlsplit`에서 발생했다. Phase2에서 로컬 Python 3.14의 hostname accessor는 문자열 분리/소문자화이고 path는 결과 필드임을 읽기 확인했다. 추가 예외 변환은 필요하지 않아 `urlsplit`만 감쌌다. Python 3.12의 실제 실행 판정은 CI에 맡긴다.

## Runtime

- runtime_owner: worktree `wks_6ff707e7c396efdb`. 서비스·포트·DB·컨테이너 없음. Claude는 background 명령·하위 agent·heartbeat를 시작하지 않았다(작성 시점 기준. 종료 확인은 Supervisor가 한다).
- venv: 이 worktree의 `.venv`(작업 전 없음 확인). `uv 0.12.23`으로 `uv venv --seed --no-cache --no-python-downloads --python /usr/bin/python3 .venv` 생성. `.venv/.gitignore`(`*`)가 자체 무시한다. 설치는 `.venv/bin/python -m pip install --no-cache-dir -e .`만 수행했다. uv cache 미사용, 글로벌 Python·PYTHONPATH·sudo 미사용.
- 버전: Python 3.14.4(`/usr/bin/python3`), pip 26.2.1, tzdata 2026.5, kerbe 0.1.0(editable). CI는 Python 3.12이며 3.12 로컬 실행은 하지 않았다.
- import 확인(assert 통과): `sys.prefix` = `<worktree>/.venv`, `codex_usage.__file__` = `<worktree>/src/codex_usage/__init__.py`.
- task 소유 폴더: `.venv/k12-m-runtime/{tmp,logs,wheels}`. `wheels`는 비어 있다.
- TMPDIR 설계 수정: 처음에는 `.venv/k12-m-runtime/tmp`를 TMPDIR로 썼다. 이 경로는 worktree 안이라 plain directory fixture가 상위 Kerbe Git 저장소로 인식되어 baseline 2개가 실패했다. 이후에는 `mktemp -d /tmp/kerbe-m-6f07d351-XXXXXX`로 만든 `/tmp/kerbe-m-6f07d351-CYllHj`(0700, shotgun1107 소유, `git rev-parse --show-toplevel` 실패 = 저장소 아님)를 쓴다. 경로는 `.venv/k12-m-runtime/tmp-root.txt`에 기록했다.
- 보존 자료(삭제·변경 금지): `.venv/k12-m-runtime/tmp/tmp5hh6g14i`(중단된 첫 baseline의 잔여 fixture), `logs/baseline.log`(중단 기록), `logs/baseline-retry.log`, `logs/pip-install.log`, `logs/env-recheck.log`, `logs/red.log`.
- 실행 형식: `env -u PYTHONPATH TMPDIR=/tmp/kerbe-m-6f07d351-CYllHj .venv/bin/python -m unittest ...`

## 실제 test 결과(revision: base `efd539a` + 미커밋 회귀시험, source 무수정)

1. baseline 첫 시도: `unittest discover -s tests -t . -v`(TMPDIR=worktree 내부)를 실행했으나 Supervisor 개입으로 첫 acceptance test 도중 중단됐다. 결과 없음(`baseline.log`).
2. baseline 재실행(TMPDIR=worktree 내부, 1회, `baseline-retry.log`): Ran 182, **FAILED(failures=2, skipped=2)**. 회귀시험 추가 전이다.
   - FAIL `tests.integration.test_cli.CliIntegrationTests.test_init_collect_and_doctor_user_flow`: `doctor_code` 2 != 0.
   - FAIL `tests.unit.test_git_probe.GitProbeTests.test_missing_path_and_plain_directory_are_not_repositories`: `REPOSITORY` != `NOT_REPOSITORY`.
   - skip 2개는 Windows 전용 시험이다(`test_quota_status` Windows desktop discovery, `test_windows_credentials` Credential Manager integration). Linux skip이며 실제 외부 smoke가 아니다. 합성 private GitHub smoke unittest는 통과 집계에 포함됐고 외부 smoke는 실행하지 않았다.
3. 환경 재검증(새 TMPDIR, 위 FAIL 2개만, `env-recheck.log`): Ran 2, **OK**. 두 실패는 TMPDIR 위치로 인한 환경 오류로 판단한다. 새 TMPDIR로 전체 suite는 재실행하지 않았다.
4. RED(새 TMPDIR, `-v tests.unit.test_git_remote tests.unit.test_project_attribution_engine`, `red.log`): Ran 21(test method 수), **FAILED(errors=3)**. errors 3은 subTest 단위이며, 영향을 받은 test method는 2개다(정규화 subcase 2개 + attribution 1개). 계획된 미완성 checkpoint이며 통과가 아니다.
   - `test_malformed_ipv6_url_remotes_are_rejected` subTest `ssh://[2001:db8::1/repo.git`: `ValueError: Invalid IPv6 URL`(기대: `RemoteNormalizationError`).
   - 같은 test subTest `https://[not-an-ip]/repo.git`: `ValueError: 'not-an-ip' does not appear to be an IPv4 or IPv6 address`(Python 3.14 `urlsplit`의 `_check_bracketed_host`).
   - `test_malformed_session_remote_falls_back_to_cwd_git_probe`: `_self_remote` → `resolve_remote` → `normalize_remote`에서 `ValueError: Invalid IPv6 URL`. fallback에 도달하지 못했다(기대: `UNIQUE_REMOTE`, `github.com/example/project`).
   - 나머지 19개 test method는 통과했다.
- 미실행: 새 TMPDIR 전체 suite, wheel build, Python 3.12 로컬 실행, GREEN.

## Phase2(Codex) 실제 결과 — 2026-10-10

- 실제 모드: Codex 0.160.1 / gpt-6.1-sol / medium / on-request / workspace-write(network=false). Full Access·설정 변경·persistent allow·wrapper 우회 없음. native merge 차단 증거는 Supervisor가 대조했으며 새 위험 probe는 하지 않았다.
- source 수정 전 gate: clean/checkpoint 확인 → task branch no-op 일반 push `Everything up-to-date` → PR #5 provenance comment 게시 및 GET 동일 확인(https://github.com/shotgun1107/kerbe/pull/5#issuecomment-6086175610) → task branch fetch 후 local/origin HEAD 동일·clean 확인.
- 구현: `_parse_url_remote`의 `urlsplit(remote)`만 `try/except ValueError`로 감싸 `RemoteNormalizationError("remote contains an invalid URL") from error`로 변환. API·URL 형태·출력 계약 및 호출부 변경 없음.
- 아래 실행은 모두 기존 `.venv`, `env -u PYTHONPATH TMPDIR=/tmp/kerbe-m-6f07d351-CYllHj`를 사용했다. 기존 로그/fixture를 덮어쓰거나 삭제하지 않았다.
  1. RED 재현 1회: `-m unittest -v tests.unit.test_git_remote tests.unit.test_project_attribution_engine` → Ran 21, FAILED(errors=3), exit 1. Phase1과 같은 두 정규화 subcase와 attribution 한 건(`logs/codex-red.log`).
  2. 최소 수정 후 같은 선택 module GREEN: Ran 21, OK, exit 0(`logs/codex-green.log`).
  3. `-m unittest discover -s tests -t .` 1회: Ran 184, OK(skipped=2), exit 0(`logs/codex-full.log`). Windows 전용 desktop discovery·Credential Manager 두 검사는 Linux skip이며 통과로 세지 않는다. 합성 private smoke unittest는 포함되지만 외부 smoke/실제 credential store는 실행하지 않았다.
  4. `-m pip wheel --no-cache-dir --no-deps . --wheel-dir .venv/k12-m-runtime/wheels`: sandbox에서는 격리 build dependency의 PyPI DNS 실패로 exit 1(`logs/codex-wheel.log`). 동일 명령을 정상 개별 승인 후 실행해 exit 0(`logs/codex-wheel-network.log`). cache는 사용하지 않았으며 임시 build 자료는 task TMPDIR 안에서 처리됐다.
- wheel: `kerbe-0.1.0-py3-none-any.whl`, SHA-256 `55fcf55fbb3c5a5590ec1b670eb065c566877d94c98055aa336cfe468f088bbb`. 압축 내부 source에 수정 포함을 확인했다.
- `git diff --check` 통과. 새 TMPDIR·venv 재생성·서비스/운영 데이터 접근 없음. 전체 suite는 성공 뒤 반복하지 않았다.
- 권한 기록(이 기록 시점): Phase2 명령별 escalation 요청 6회(no-op push, provenance POST, provenance GET, fetch, wheel, 기존 PR GET), 모두 허용·성공. sandbox 실패 3건(push DNS, comment API 연결, wheel PyPI DNS). 복원 턴의 escalation 2회는 별도다. 이후 전달 명령의 승인/실패와 최종 SHA는 PR handoff에 기록한다.

## Next(Codex 전달)

1. 이 source/task diff 전체를 검토하고 명시 stage 후 한국어 Conventional commit + `Agent: codex`로 commit한다. task branch만 일반 push하고 실제 remote/PR HEAD를 확인한다.
2. 목표/Acceptance/실제 검사/Next/runtime/보존자료/미확인을 기존 Draft PR #5 본문으로 승격한다. `gh api` REST PATCH + GET으로 저장을 확인한 후 이 작업에서 추가한 task 파일 하나만 삭제해 별도 commit/push한다. 삭제 commit은 source 변경 없는 최종 후보 H이며 전체 suite를 근거 없이 재실행하지 않는다.
3. 최종 H의 local/remote/PR HEAD·clean·Draft·CI 상태를 확인하고 PR에 H를 기록한다. H의 CI가 2분 내 완료하지 않으면 대기 중으로 전달한다. 독립 리뷰는 Supervisor가 실행 종료 후 수행하며 현재 미실행이다.
4. 승격 후 현재 handoff 정본은 PR #5 하나로 유지한다. AI Ready/merge/main push/force/Archive/권한 변경은 하지 않는다.

## 주의점

- main push·force push·merge·Ready 전환은 금지. `fix/malformed-remote-errors`만 일반 push한다.
- git_probe 예외 adapter 문제는 범위 밖이다(위 제외 항목).
- 로컬 `main` ref는 `026a8a0`으로 낡았다. 기준은 `origin/main`(`efd539a`)이다.
- 다른 agent의 보호 설정을 열람·수정하지 않는다. 실제 계정·DB·Codex 원본은 사용하지 않는다.
