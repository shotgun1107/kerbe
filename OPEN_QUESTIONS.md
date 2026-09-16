# 미확인 사항과 검증 계획

상태: v1 핵심 Build·Validate 완료 · 잔여 조사 및 최초 실사용 확인 항목 관리

상태 정리: 2026-09-16. 기존 결정과 검증 기록을 대조한 갱신이며, 새 실험이나 기능 승인을 뜻하지 않는다.

로그를 확인해야 답을 얻는 `검증 항목`과 사용자가 선택해야 하는 `설계 결정`을 분리한다.

## 우선 검증 항목

### Q-001. fork·resume·compact의 토큰 기준선

- 상태: 현재 CLI 버전에 대해 부분 해결
- 결과: resume는 같은 누적 카운터를 계속 사용하며 프로세스 재시작 후에도 초기화되지 않았다.
- 결과: fork는 부모 이력과 누적 체크포인트를 복사하고, 복사된 작업의 `turn_id`도 유지했다.
- 결과: fork 이후 새 작업만 새로운 `turn_id`를 사용했으며 부모 누적값은 변하지 않았다.
- 결과: compact는 누적값을 유지했지만 세부 항목이 0인 별도 `last_token_usage.total_tokens`를 기록했다.
- 남은 질문: compact의 불투명한 reported last가 실제 모델 사용량·계정 한도에 포함되는가?
- 확정 정책: 불투명한 reported last는 보존하되 일반 프로젝트 총합에서 제외한다(D-021).
- 남은 검증 완료 기준: compact overhead의 실제 의미를 확인한다. 합산 정책 변경은 별도 결정으로 다룬다.

### Q-002. JSONL과 SQLite의 역할

- 상태: 현재 로컬 버전에 대해 부분 해결
- 결과: 631개 thread 모두 `SQLite threads.id = rollout UUID = session_meta.id`로 조인됐다.
- 결과: `session_meta.session_id`는 고유 thread ID가 아니라 계보 root다.
- 결과: JSONL은 상세 이벤트, SQLite는 인덱스·spawn-edge·최신 요약으로 역할이 나뉜다.
- 결과: lifecycle 통제 실험에서도 JSONL 마지막 누적값과 SQLite `tokens_used`가 일치했다.
- 결과: Git 안·밖과 숨김 백그라운드의 `codex exec`가 모두 `source=exec`로 기록되고 SQLite·JSONL이 연결됐다.
- 남은 질문: 현재 표본에 없는 interactive `cli`와 명시적 `appServer` source에서도 같은 규칙이 유지되는가?
- 완료 기준: 통제 실험에서 실행 종류별 조인과 누락 폴백을 확인한다.

### Q-003. 부모·자식 spawn-edge의 완전성

- 상태: 현재 로컬 subagent에 대해 부분 해결
- 결과: `subagent.thread_spawn` 310개가 spawn-edge child 310개와 정확히 일치했다.
- 결과: edge가 없는 `subagent.other` 175개도 `session_meta.session_id`로 존재하는 root에 연결됐다.
- 결과: 현재 edge에는 누락된 부모·자식, 다중 부모, 순환 관계가 없었다.
- 결과: fork는 spawn-edge가 없지만 JSONL 첫 `session_meta.forked_from_id`로 부모를 명시했다.
- 주의: 현재 통제 실험의 fork 자식 `session_id`는 부모 root가 아니라 자식 자신이므로 fork 연결에 사용하지 않는다.
- 결과: 프로젝트 안·밖의 통제 실험에서 `subagent.thread_spawn` 자식이 모두 직접 spawn-edge와 root `session_id`를 가졌다.
- 남은 질문: 재개된 spawn 자식과 `subagent.other`의 직접 관계가 버전별로 어떻게 달라지는가?
- 완료 기준: 통제 실험에서 실행 종류별 edge와 root 연결을 확인한다.

### Q-004. 첫 token_count 이벤트

- 상태: 현재 CLI 버전에 대해 해결
- 신규 thread: 첫 누적값과 첫 turn 사용량이 일치했다.
- resume thread: 새 기준선을 만들지 않고 기존 누적값을 이어갔다.
- fork thread: 첫 체크포인트는 부모의 복사된 기준선이므로 새 사용량이 아니다.
- 처리 규칙: token_count를 현재 `task_started.turn_id`에 연결하고, fork에서 복사된 동일 turn을 중복 제거한다.
- 회귀 조건: 다른 `cli_version`에서 구조가 바뀌면 다시 검증한다.

### Q-005. Git 메타데이터 누락

- 상태: 현재 CLI 버전에 대해 부분 해결
- 질문: repository URL이 없는 작업을 어떤 정보로 프로젝트에 연결할 수 있는가?
- 현재 관찰: Spike 1 시점 631개 thread 중 repository URL이 있는 thread는 376개였다.
- 현재 관찰: 자기·부모·root·단일 자식 저장소를 사용한 제안 규칙으로 386개를 자동 분류하고 245개는 미분류로 남았다.
- 현재 관찰: 부모와 자식 저장소가 다른 spawn-edge가 64개 있어 자기 Git을 우선해야 한다.
- Spike 3: Git 밖 `exec`는 Git 메타데이터가 없고, 그 부모가 만든 자식도 실제 프로젝트에서 작업했지만 기본 cwd와 Git 정보는 부모의 Git 밖 상태를 유지했다.
- Spike 3: 실제 프로젝트를 사용한 도구 호출의 `workdir`는 rollout에 남아 로컬 Git 판별에 사용할 수 있었다.
- Spike 4: `origin`이 없으면 remote 하나가 있어도 Codex URL은 비었지만, 로컬 Git 조회로 unique remote를 복구할 수 있었다.
- Spike 4: worktree는 원본 remote, submodule은 자기 remote, monorepo 하위 폴더는 루트 remote를 기록했다.
- Spike 4: remote 변경 전후 로그는 각각 당시 URL을 보존하므로 alias 연결이 필요하다.
- Build 검증: turn 활동 Git·자기 Git·계보 합의까지 적용해 logical checkpoint 54,004개 중 43,989개(약 81.5%)를 자동 귀속했다.
- Build 검증: 근거가 부족한 10,015개는 잘못 합치지 않고 `unclassified`로 유지했다.
- 결정: remote 없는 저장소는 append-only `local_repo_link` 수동 매핑으로 여러 기기에서 같은 project ID에 연결한다(D-034).
- 구현 확인: `project list`, `project unresolved`, `project link`, `project alias` CLI가 존재한다. thread·turn 수동 연결은 D-048에 따라 mapping 이벤트로 기록한다.
- 검증 기록: 수동 연결의 멱등성·revision과 두 기기의 collect·sync·link·report·clean rebuild 수용 검증을 완료했다.
- 남은 확인: D-034의 `local_repo_link`와 현재 thread·turn 연결 CLI의 적용 범위가 실제 remote-less 다기기 사용 요구를 충족하는지 별도로 대조한다. CLI가 미정이라는 과거 질문은 종료한다.

### Q-006. 캐시 read/write와 토큰 필드의 버전 차이

- 질문: 버전별로 캐시 쓰기와 읽기 필드가 어떻게 기록되는가?
- 검증: 서로 다른 `cli_version`의 token_count 필드 집합을 비교한다.
- 완료 기준: 버전별 파싱 규칙과 누락값 의미를 정의한다.

### Q-007. sessions와 archived_sessions의 중복

- 현재 관찰: 한 시점의 로컬 검사에서는 같은 session ID 중복이 없었다.
- 질문: archive·unarchive 도중 또는 버전별로 중복 파일이 생길 수 있는가?
- 검증: archive·unarchive 전후 파일과 session ID를 비교한다.
- 완료 기준: 파일 위치와 무관한 dedup 규칙을 정의한다.

### Q-008. 기존 도구 재사용

- 상태: v1 자체 파서 구현 완료 · 재사용 비교 조사는 후속 후보
- 질문: ccusage 또는 다른 오픈소스 파서를 재사용할 수 있는가?
- 확인 내용: 라이선스, 지원 필드, 버전 호환, 증분 읽기, fork 처리.
- 완료 기준: 재사용·부분 차용·자체 구현 중 하나를 근거와 함께 선택한다.

### Q-009. 한 turn에서 여러 저장소를 사용한 경우

- 상태: 귀속 정책 확정 · 추가 실측 여부는 미확인
- 질문: 한 turn이 둘 이상의 Git 저장소를 건드렸을 때 토큰을 어느 프로젝트에 귀속할 것인가?
- 현재 한계: token_count는 모델 응답 구간의 사용량이지 저장소별 사용량이 아니므로 정확한 분할 근거가 없다.
- 확정 정책: 자동 분할하지 않고 `ambiguous_multi_repo`로 저장한 뒤 수동 지정한다(D-035).
- 추가 조사 후보: 실제 다중 저장소 turn의 활동 workdir 집합과 토큰 이벤트 순서를 비교한다. 이번 상태 정리에서는 실험하지 않았다.

### Q-010. Windows Credential Manager 실사용 acceptance

- 상태: 해결
- 결과: adapter가 Windows API까지 도달했지만 현재 Codex 테스트 호스트에는 interactive logon session이 없어 `WinError 1312`가 발생했다.
- 2026-09-01 재검증: wheel 설치 후에도 자동 실행 계정에서는 동일하게 skip됐다. computer-use 안전 규칙상 터미널 UI 우회 실행은 하지 않는다.
- 2026-09-01 사용자 PowerShell 검증: 임시 credential 생성·읽기·삭제 왕복 테스트가 skip 없이 통과했다.
- 안전 처리: 이 환경에서는 secret file로 자동 fallback하지 않고 초기화를 중단한다.
- 남은 검증: 실제 첫·두 번째 기기 설정 시 복구 키 import의 같은 key ID를 최종 확인한다.
- 완료 기준: Credential Manager adapter acceptance는 충족했으며, 복구 키 다기기 import는 최초 실사용 설정 체크리스트로 이동한다.

### Q-011. 비공개 GitHub 실제 원격 smoke

- 상태: 해결
- 2026-09-01 결과: `gh`의 기존 `shotgun1107` 토큰이 만료됐고, 재인증 device-code 요청은 현재 샌드박스의 외부 네트워크 차단으로 시작되지 않았다.
- 안전 처리: 공개 소스 저장소에 장부를 올리거나 실제 회사 로그로 대체 검증하지 않는다.
- 2026-09-01 사용자 PowerShell 검증: 기존 비공개 `shotgun1107/kerbe-ledger`의 임시 브랜치에서 합성 123 토큰을 push하고 clean clone의 DB·보고서를 재생성했다.
- 결과: `doctor`의 원격·read-model·classification 검사가 통과했고 임시 원격 브랜치도 삭제됐다.
- 완료 기준: 충족.

## 해결된 설계 결정

다음 항목은 2026-08-26 사용자 승인으로 확정됐다.

- 회사 정책이 허용할 때 정제 통계만 비공개 장부에 저장
- 공유 비밀키 HMAC 비식별화
- v1 수동 `collect → sync → report`
- CLI 표와 Markdown 보고서
- `turn_id + token ordinal` 멱등 키
- append-only revision과 supersede 정정
- turn 활동 Git이 부모 상속보다 우선
- 다중 저장소 turn은 ambiguous 처리
- monorepo는 기본 저장소 하나
- v1 장부 이벤트 삭제·롤업 없음

결정 상태는 [DECISIONS.md](DECISIONS.md)에서 관리한다.

## 기존 Spike 완료 기록

1. ~~JSONL·SQLite source map과 조인 키 확인~~ — 기존 로그 기준 완료
2. ~~fork·resume·compact 토큰 기준선 실험~~ — 당시 CLI 버전 기준 완료, compact overhead 의미는 미확인·총합 제외 정책은 D-021로 확정
3. ~~CLI·백그라운드·오케스트레이션 귀속 통제 실험~~ — 완료, turn 활동 위치가 필요한 사례 확인
4. ~~Git 메타데이터 누락과 미분류 폴백 실험~~ — 완료, local-only 수동 연결 정책은 D-034로 확정

## Shape & Spike 종료 점검

- JSONL·SQLite 역할과 조인 키: 확인
- lifecycle 토큰 중복 규칙: 확인, compact overhead 의미만 보류
- CLI·백그라운드·오케스트레이션 귀속: 확인
- Git 누락·worktree·submodule·monorepo 폴백: 확인
- 결정 확정: 완료
- PRD·스키마 명세: 완료
- C4·ADR 설계: 승인 완료
- 현재 단계: v1 핵심 Build·Validate 완료(2026-09-01 기록 기준)

## 후속 범위와 실사용 확인

- 1차 실사용에서 확인한 미분류·연구 목적 귀속 문제는 [PHASE1_REVIEW_TODO.md](PHASE1_REVIEW_TODO.md)에 정리했다. 별도 폴더에서 수행한 연구를 어느 프로젝트에 귀속할지는 후속 정책 검토이며, 미분류 전체가 특정 연구라는 결론은 내리지 않았다.

- 정식 출시: `CHANGELOG.md`는 0.1.0 release candidate 상태다. 핵심 검증 완료와 정식 출시 완료를 구분한다.
- 최초 실사용: 두 기기 복구 키 import 후 같은 key ID 확인은 `RELEASE.md` 체크리스트에 남아 있다.
- quota·reset: 2026-09-16 사용자 요청으로 수동 현재값 조회를 구현했다(D-051·D-052). 영속 저장·다기기 계정 식별·공유 장부 개인정보·회사 정책은 미확정이다.
- UI: 사용자 재요청 전까지 제안·구현하지 않는다. 현재 제품은 CLI 중심으로 진행한다.
- 2026-09-16 quota·UI 인계 보고서는 조사·제안 자료다. 보고서의 API 실험 결과는 이번 정리에서 재검증하지 않았고, 트레이·플러그인·스키마 변경 제안을 확정 결정으로 편입하지 않는다.
