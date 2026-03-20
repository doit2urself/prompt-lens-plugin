# PromptLens - 설계 문서 v2.1

## 개요
Claude Code 플러그인. 사용자의 프롬프트를 **Claude 자체에 위임**하여 PE 원칙 기반으로 평가·보정한다.
사용자는 플러그인의 존재를 인식하지 못하며, Claude가 원래 똑똑한 것처럼 느낀다.

## 아키텍처 결정 기록 (ADR)

### ADR-1: Rule-based → Claude-delegated
- **결정**: 프롬프트 품질 판단을 Python 규칙 엔진이 아닌 Claude에게 위임
- **근거**: Rule-based는 대화 맥락을 이해하지 못하여 오탐 다수 발생. "fix the bug"는 PE 규칙상 나쁘지만 대화 흐름에서는 적절.
- **참고**: severity1/claude-code-prompt-improver 프로젝트도 동일 접근 채택

### ADR-2: pe-principles.json 삭제
- **결정**: 별도 규칙 파일 없이 평가 지침을 스크립트에 내장
- **근거**: Claude-delegated 모델에서는 세부 규칙이 아닌 평가 관점 힌트만 필요. 14개 PE 원칙 중 6개를 선별하여 ~150토큰 지침으로 압축. Claude의 내재 지식이 나머지를 커버.

### ADR-3: additionalContext 경로 선택
- **결정**: SessionStart 1회 주입이 아닌 UserPromptSubmit 매 프롬프트 주입
- **근거**: SessionStart의 additionalContext는 compaction 시 소실 (Issue #14258 확인). startup matcher도 불안정 (Issue #10373). UserPromptSubmit은 compaction과 무관하게 안정적.

### ADR-4: 열린 루프(open-loop) 한계
- **결정**: 피드백 루프 없이 고정 텍스트를 매 프롬프트 주입하는 구조를 수용
- **근거**: Claude Code hooks API는 Claude 응답을 관찰하거나 후처리하는 메커니즘을 제공하지 않음. 주입 후 Claude가 실제로 되물었는지, 사용자가 만족했는지 추적 불가. 이것은 API 제약이며 설계 결함이 아님.
- **영향**: EVALUATION_INSTRUCTION의 효과를 런타임에서 자동 조정할 수 없음. 효과 개선은 수동 A/B 테스트를 통한 지침 문구 수정으로만 가능.

### ADR-5: YAGNI — 확장 가능성은 가치 검증 후 논의
- **결정**: 프롬프트 유형별 차등 지침, 세션 상태 인식, 사용자 프로필 기반 개인화 등의 확장은 구현하지 않음
- **근거**: 현재 플러그인의 기본 가치(모호 프롬프트에서 되묻기 유도)가 검증되지 않은 상태에서 확장을 설계하는 것은 시기상조. Binary gate(주입 or 스킵)의 단순성은 디버깅과 예측 가능성에서 장점. 160줄 스크립트의 리팩토링 비용은 미미하므로, 가치 검증 후 확장해도 늦지 않음.

## 성공 기준

### 플러그인 성공 조건
1. **투명성**: 사용자가 플러그인 존재를 인식하지 못한 채 자연스럽게 사용
2. **개선 효과**: 모호한 프롬프트에 대해 Claude가 실행 전 핵심 사항을 확인하는 빈도 증가
3. **무해성**: 명확한 프롬프트에 대해 불필요한 질문이나 지연이 발생하지 않음
4. **안정성**: 스킵 대상(확인응답, 코드 등)이 정상 통과하며 UX 방해 없음

### 검증 방법
- 동일 프롬프트에 대해 플러그인 ON/OFF 응답 비교 (A/B 테스트)
- 실사용 세션에서 불필요한 질문 발생 여부 관찰
- 스킵 조건 오탐/미탐 비율 모니터링 (`PROMPTLENS_DEBUG=1`)

## 행동 명세 (Given/When/Then)

### 모호한 프롬프트 → 확인 질문
```
Given: 사용자가 "버그 고쳐" 라고 입력
When: PromptLens가 additionalContext 주입
Then: Claude가 "어떤 파일의 어떤 버그인지 알려주시겠어요?" 등 핵심 질문 후 실행
```

### 명확한 프롬프트 → 즉시 실행
```
Given: 사용자가 "src/auth.py의 login 함수에서 토큰 만료 체크 로직 추가해줘" 라고 입력
When: PromptLens가 additionalContext 주입
Then: Claude가 질문 없이 바로 구현 진행
```

### 확인 응답 → 스킵
```
Given: 사용자가 "y" 라고 입력
When: PromptLens 스킵 판정
Then: additionalContext 미주입, 원본 그대로 전달
```

### 자연어 + 에러 혼합 → 주입 (스킵 안 됨)
```
Given: 사용자가 "이 에러 해결해줘:\n\nTraceback..." 라고 입력
When: PromptLens 코드 비율 검사 (자연어 포함 → <70%)
Then: additionalContext 주입, Claude가 에러 맥락을 파악하여 해결
```

### 순수 코드 붙여넣기 → 스킵
```
Given: 사용자가 코드만 붙여넣기 (import문 + 함수 정의, 코드 비율 ≥70%)
When: PromptLens 코드 비율 검사
Then: additionalContext 미주입, 원본 그대로 전달
```

### 바이패스 → 스킵
```
Given: 사용자가 "* 그냥 해줘" 라고 입력
When: PromptLens가 `*` 접두사 감지
Then: additionalContext 미주입, 원본 그대로 전달
```

## 확정된 결정 사항
- 보정 엔진: **Claude-delegated** (훅은 경량 래퍼, Claude가 판단)
- 사용자 경험: **완전 투명** (SessionStart 알림만 표시, 이후 무음)
- 바이패스: `*` 접두사로 스킵 가능
- 토큰 오버헤드: 프롬프트당 ~150토큰 (평가 지침)
- 디버그: `PROMPTLENS_DEBUG=1` 환경변수로 stderr 로깅 활성화

## 핵심 기술 제약
- `UserPromptSubmit` 훅은 프롬프트 직접 수정 **불가**
- `updatedPrompt` 필드는 미구현 (GitHub Issue #20833 → NOT_PLANNED)
- 가능한 것: `additionalContext` 주입 (사용자에게 안 보임, Claude 내부 컨텍스트에만 추가)
- `${CLAUDE_PLUGIN_ROOT}` 환경 변수로 플러그인 경로 참조

## 디렉토리 구조
```
prompt-lens-plugin/
├── .claude-plugin/
│   └── plugin.json              # 플러그인 매니페스트
├── hooks/
│   └── hooks.json               # SessionStart + UserPromptSubmit
├── scripts/
│   ├── session-init.sh          # 시작 알림 출력
│   └── prompt-refiner.py        # 경량 래퍼 (~160줄)
├── tests/
│   └── test_refiner.py          # 통합 테스트 (21개 케이스)
└── ref-docs/
    └── Prompt Engineering.pdf   # 원본 참고 문서
```

## 작동 흐름

### 1. SessionStart
- session-init.sh 실행
- matcher: `startup|resume` (새 세션 시작 및 세션 복원 시)
- "[PromptLens] 활성화됨 — 프롬프트 품질 평가가 백그라운드에서 작동합니다." 알림 표시

### 2. UserPromptSubmit (매 프롬프트, 무음)
1. stdin으로 JSON 수신 (prompt, session_id, transcript_path 등)
2. 바이패스 접두사(`*`) 체크
3. **스킵 체크** (9개 조건)
4. 스킵 아닌 경우: 평가 지침을 additionalContext로 주입
5. stdout에 JSON 출력

### 3. Claude 처리
- 원본 프롬프트 + additionalContext를 함께 수신
- 대화 맥락 속에서 프롬프트의 명확성을 자체 판단
- 명확하면: 즉시 실행 (오버헤드 제로)
- 모호하면: 자연스럽게 1-2개 핵심 질문 후 실행

## prompt-refiner.py 설계

### 스킵 조건 (9개)
| # | 조건 | 판정 방식 |
|---|------|----------|
| 1 | 빈 프롬프트 | strip 후 빈 문자열 |
| 2 | 슬래시 명령 | `/` 시작 |
| 3 | 해시 메모 | `#` 시작 |
| 4 | 짧은 확인 응답 | 정규식: y, n, ok, yes, no, ㅇ, ㄴ, 네, 아니 등 |
| 5 | 선택 응답 | 정규식: 숫자만, "첫 번째", "두 번째" 등 |
| 6 | 파일 경로 | 전체 문자열이 경로 형태 (공백 포함 프롬프트는 통과) |
| 7 | 코드/에러 붙여넣기 | 3줄 이상 + 전체의 70% 이상이 코드 패턴 |
| 8 | 매우 긴 프롬프트 | 2000자 초과 |
| 9 | 바이패스 접두사 | `*` 시작 (main에서 선처리) |

> **설계 근거**: 2000자/3줄/70% 등 임계값은 실사용 후 조정 예정. 현재는 보수적(오탐 최소화) 기준.

### 코드 감지 로직
- `CODE_LINE` pre-compiled regex로 키워드 시작, 괄호/세미콜론 종료, 키워드+콜론 조합 탐지
- **절대 비율**: 3줄 이상 + **상대 비율**: 전체 줄의 70% 이상이 코드여야 스킵
- 자연어 요청 + 코드 첨부("이 에러 해결해줘:\nTraceback...") → 코드 비율 < 70% → 통과

### 평가 지침 (additionalContext에 주입, ~150토큰)
```
Before responding, briefly assess this prompt's clarity in the current conversation context:
- Is the intent clear enough to produce the right result?
- Are there high-impact ambiguities that could lead to wasted effort?

If clear: proceed immediately, no overhead.
If genuinely ambiguous with high-impact unknowns: ask 1-2 focused questions before proceeding.
Do not ask about low-impact details you can reasonably infer.

PE considerations: output format specified, scope clearly bounded, sufficient context provided,
complex tasks broken into steps, examples included where patterns matter,
instructions framed positively (do X) rather than negatively (don't do Y).
```

> **PE 원칙 선별 근거**: PDF 14개 베스트 프랙티스 중 6개 선별. Claude의 내재 PE 지식이 나머지를 커버하므로, 핵심 관점 힌트만 제공하여 토큰 효율 최적화.

### 출력 형식
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "평가 지침..."
  }
}
```

- additionalContext는 API 레벨에서 비가시적 (사용자 transcript에 미표시)
- 스킵 시: 빈 JSON `{}` 출력 (exit 0)

### 에러 처리
- 전체 try/except 래핑
- 에러 시: exit 0 + 빈 JSON (fail-open, 프롬프트 정상 진행)
- **절대 exit 2 사용 금지** (사용자 프롬프트 차단됨)
- 디버그: `PROMPTLENS_DEBUG=1` 시 stderr로 skip/inject/error 상태 출력

### 보안
- 사용자 프롬프트 원문을 additionalContext에 **삽입하지 않음**
- 평가 지침은 고정 텍스트 (프롬프트 인젝션 불가)
- stdin 최대 64KB 읽기 제한

## 검증 계획

### 1단계: 무해성 검증 (최우선)
- **방법**: 플러그인 ON 상태로 실제 개발 작업 30분 수행
- **판정 기준**: 불편한 순간(불필요한 질문, 이상 동작) 0건
- **실패 시**: EVALUATION_INSTRUCTION 문구 조정 또는 스킵 조건 추가

### 2단계: A/B 효과 비교
- **방법**: 10개 프롬프트를 새 세션에서 ON/OFF 각각 실행, 응답 비교
- **테스트 프롬프트** (카테고리별 2개):
  - 모호한 코딩: "버그 고쳐", "이거 리팩토링해줘"
  - 명확한 코딩: "src/auth.py의 login 함수에 rate limit 추가", "이 테스트에 edge case 3개 추가"
  - 설명 요청: "이 코드 뭐하는거야", "이 아키텍처 설명해줘"
  - 복잡한 요청: "이 프로젝트를 TypeScript로 마이그레이션해줘", "전체 테스트 커버리지 80%로 올려줘"
  - 짧은 지시: "해줘", "고고"
- **판정 기준**: 모호 프롬프트에서 명확한 행동 차이 관찰 (정성적)
- **실패 시**: 차이 미관찰 → EVALUATION_INSTRUCTION 강화 또는 프로젝트 가치 재검토

### 3단계: additionalContext 누적 확인
- **방법**: 10턴 세션 실행 후 transcript.jsonl 분석
- **판정 기준**: 이전 턴의 additionalContext가 다음 턴 transcript에 미누적
- **실패 시**: 누적 확인 → 토큰 영향도 평가 후 대응

### 보류 항목
- [ ] 다중 플러그인 UserPromptSubmit 충돌 여부 → 실제 충돌 발생 시 대응
- [ ] 임계값 조정 (2000자, 3줄/70%) → 오탐/미탐 발견 시 조정

## 참고 자료
- Claude Code Hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code Plugins: https://docs.anthropic.com/en/docs/claude-code/plugins
- GitHub Issue #20833 (updatedPrompt 미구현)
- claude-code-prompt-improver: https://github.com/severity1/claude-code-prompt-improver
- Plugin hooks 미실행 버그 (Issue #10225): 수동 설치 fallback 필요 가능성
- SessionStart additionalContext compaction 시 소실 (Issue #14258)
- SessionStart startup matcher 불안정 (Issue #10373)
