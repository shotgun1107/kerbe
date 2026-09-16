# v1 release smoke checklist

## Kerbe 이름 변경 검증 (2026-09-16)

- 전체 회귀 테스트 175개 통과.
- 기존 가상환경의 이전 배포 패키지를 제거하고 `kerbe` wheel 설치 성공.
- 사용자 PATH의 `kerbe` 실행 파일로 CMD·PowerShell에서 도움말 실행 성공; 설치된 JSON Schema 로딩 성공.
- 기존 `codex-usage` 호환 명령 유지. 로컬 설정·공유키 대상·장부 경로는 변경하지 않음.
- GitHub 저장소명과 로컬 origin을 `shotgun1107/kerbe`로 변경.

## 현재 상태

- v1 핵심 Build·Validate: 2026-09-01 완료 기록이 있다.
- 0.1.0 정식 출시: 확인되지 않았다. `CHANGELOG.md`의 release candidate 표기를 유지한다. 2026-09-16 로컬 Git 조회에서는 태그가 없었으며 원격 출시 여부는 조회하지 않았다.
- 최초 실사용 설정: 실제 두 기기의 복구 키 import와 같은 `key_id` 확인은 별도 체크리스트 항목이다.
- quota·reset: 2026-09-16 수동 `status` 조회 추가(D-051·D-052). 영속 수집과 UI는 후속 검토 범위다.

아래 명령과 체크리스트는 검증 절차다. 앞선 문서 상태 정리에서는 테스트·설치·원격 smoke를 재실행하지 않았다. 이후 status 구현 검증은 아래 별도 기록으로 구분한다.

## 자동 검증

```powershell
python -m unittest discover -s tests -t .
python -m pip wheel --no-deps . --wheel-dir dist
```

새 가상환경에 wheel을 설치한 뒤 다음 항목을 확인한다.

```powershell
kerbe --version
kerbe --help
```

- 설치된 패키지에서 `LedgerSchemaValidator.default()`가 schema를 찾는다.
- `init`, `collect`, `sync`, `doctor`, `project`, `report` 명령이 help에 나타난다.
- 소스 checkout 밖에서 실행해도 동일하게 동작한다.

## 실제 Windows 사용자 세션

일반 PowerShell에서 다음 테스트를 실행한다. 테스트는 임시 Credential Manager 항목을 생성하고 `finally`에서 삭제한다.

```powershell
python -m unittest tests.integration.test_windows_credentials -v
```

- `skipped`가 아니라 `OK`인지 확인한다.
- 첫 기기 `init`에서 만든 복구 키를 별도 비밀번호 관리자에 보관한다.
- 두 번째 기기의 `init --import-key`가 같은 `key_id`를 사용하는지 확인한다.
- 복구 키와 Git 인증정보를 저장소 파일에 기록하지 않는다.

## 비공개 GitHub 장부

- 빈 비공개 저장소를 장부 전용으로 만든다.
- 실제 회사 로그를 사용하기 전 회사 정책을 확인한다.
- smoke test에서는 합성 rollout만 사용한다.
- 두 clone에서 `collect → sync` 후 합계가 같아야 한다.
- `project link → sync`가 다른 clone에 반영돼야 한다.
- 세 번째 clean clone에서 `sync`만으로 조회 DB를 재생성해야 한다.
- `doctor`의 `ledger-remote`, `read-model`, `classification`이 `OK`여야 한다.

이미 초기 commit이 있는 비공개 저장소에서 다음 합성 smoke를 실행할 수 있다. 스크립트는 저장소 공개 여부를 먼저 검사하고, 임시 브랜치만 생성·검증한 뒤 삭제한다.

```powershell
python scripts\private_github_smoke.py --remote https://github.com/<owner>/<private-repo>.git
```

공개 저장소와 이 프로젝트의 소스 저장소는 입력으로 거부한다. 실패 후 임시 브랜치 정리 오류가 표시되면 출력된 정확한 브랜치만 수동으로 삭제한다.

## 정리와 출시

- 로컬 smoke가 만든 `.tmp-release-smoke`는 검증 후 `Remove-Item -LiteralPath .\.tmp-release-smoke -Recurse -Force`로 정리한다.
- `git status`가 깨끗한지 확인한다.
- `README.md`의 테스트 개수와 실제 결과가 같은지 확인한다.
- `OPEN_QUESTIONS.md`의 실사용 검증 결과를 갱신한다.
- version과 changelog를 확정한 뒤 tag를 만든다.
- 한도·reset 수집은 핵심 v1 출시 이후 별도 단위로 진행한다.

## 0.1.0 검증 결과

아래는 2026-09-01 핵심 v1 검증 기록이다.

- Windows 사용자 세션 Credential Manager 테스트: 통과
- 비공개 GitHub 합성 장부 smoke: 통과, 합계 123, 임시 브랜치 삭제 확인
- 로컬 전체 테스트: 159개 중 158개 통과, 자동 환경 Credential 테스트 1개 skip
- GitHub Actions: Windows·Ubuntu 전체 테스트와 wheel 생성 통과

## 후속 status 검증 (2026-09-16)

- Windows Python 3.12.10: 전체 테스트 174개 모두 통과, skip 없음.
- 신규 status 테스트 15개: 합성 App Server stdio·오류·시간 초과·종료 정리·다중 버킷·누락값·CLI 초기화 불필요 확인.
- 실제 codex-cli 0.154.0: 계정 한도 읽기 성공, 일반·별도 모델 버킷과 KST 초기화 시각 표시 확인.
- wheel 빌드·프로젝트 전용 `.venv` 설치 완료. 소스 checkout 밖에서 설치된 `kerbe status`와 JSON Schema 로딩 성공.
- 이번 후속 변경의 원격 CI·정식 출시는 아직 수행하지 않았다.
