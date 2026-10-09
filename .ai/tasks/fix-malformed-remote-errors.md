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
- 이 파일 작성 시점의 writer는 Claude이며 교대 대기 상태다. 이 checkpoint의 commit/push/Draft PR과 Claude 실행 종료를 Supervisor가 확인한 뒤 Codex가 writer를 인수한다. Claude는 이후 새 요청 없이는 다시 쓰지 않는다.
- Phase1(Claude): 격리 runtime 준비, baseline, RED 회귀시험 추가, 이 handoff 작성은 완료했다. 프로덕션 source는 수정하지 않았다. checkpoint commit/push/Draft PR 전달과 실행 종료는 이 파일 작성 이후 단계이므로 Git·PR 상태로 실제 확인한다.
- 이 handoff를 담은 checkpoint commit은 자기 SHA를 파일에 담을 수 없다. `git log --oneline efd539a..origin/fix/malformed-remote-errors`로 확인한다.

## 결정

- 수정 위치는 `_parse_url_remote` 한 곳. 기존 port 처리(`parsed.port`의 `ValueError` → `RemoteNormalizationError`)와 같은 형태로 `urlsplit` 호출을 감싼다. 호출부(collect, project_attribution)는 이미 `RemoteNormalizationError`를 잡으므로 변경하지 않는다.
- RED의 세 오류는 모두 `git_remote.py:134`의 `urlsplit`에서 발생했다. `parsed.hostname`·`parsed.path` 쪽 추가 예외 여부는 Phase2에서 확인한다.

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

## Next(Codex Phase2)

1. 시작 전 native/remote 쓰기 gate를 확인한다. Codex 기본 on-request/workspace-write에서 진행하고 Full Access는 사용할 수 없다. `git fetch` 뒤 local/remote HEAD가 이 branch의 최신 checkpoint와 같고 clean인지 확인한다.
2. 기존 `.venv`를 재사용한다(삭제·clear 금지). `PYTHONPATH`를 해제하고 TMPDIR을 `tmp-root.txt`의 경로로 고정한다. 그 경로가 없으면 같은 규칙(`mktemp -d /tmp/kerbe-m-6f07d351-XXXXXX`, 저장소 아님·0700 확인)으로 새로 만들고 이 파일을 갱신한다.
3. `_parse_url_remote`에서 `urlsplit`을 `try/except ValueError`로 감싸 `RemoteNormalizationError`로 변환한다(`from error`). 다른 계약은 바꾸지 않는다.
4. 선택 module 2개 GREEN → 전체 `unittest discover -s tests -t .` → `pip wheel --no-deps . --wheel-dir <runtime>/wheels`를 실행하고 결과를 이 파일에 기록한다.
5. commit/push 뒤 Draft PR CI(Windows·Ubuntu, 3.12)를 확인한다. 이 task를 최종 PR handoff로 승격하거나 삭제하는 일은 Codex 마무리 단계에서 한다.

## 주의점

- main push·force push·merge·Ready 전환은 금지. `fix/malformed-remote-errors`만 일반 push한다.
- git_probe 예외 adapter 문제는 범위 밖이다(위 제외 항목).
- 로컬 `main` ref는 `026a8a0`으로 낡았다. 기준은 `origin/main`(`efd539a`)이다.
- 다른 agent의 보호 설정을 열람·수정하지 않는다. 실제 계정·DB·Codex 원본은 사용하지 않는다.
