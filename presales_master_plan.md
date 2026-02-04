# Applied AI (Pre-Sales Architect, KR) — Master Plan (Codex Handoff)

> 이 문서는 **내 최종목적 + 프리세일즈 직군 타겟 + 현재 내 상황 + 프로젝트 1 완료 + 프로젝트 2~5로 확장**하는 계획을 한 번에 정리한 “단일 핸드오프” 문서다.  
> 목적은 Codex에게 그대로 넘겨 **2~5를 순차적으로 구현**하고, 최종적으로 Applied AI(Pre-Sales Architect) 지원에 필요한 포트폴리오/데모/산출물을 완성하는 것이다.

---

## 0) 내 최종목적 (North Star)
- **목표:** LLM를 대기업(특히 한국 엔터프라이즈) 환경에 안전하고 성공적으로 도입시키는 **Pre-Sales Architect/Applied AI**로 합격한다.
- **증명 방식:** “말”이 아니라 **재현 가능한 PoC/워크숍/통합/평가/보안/ROI 산출물**로 “현업 즉시 투입” 가능함을 증명한다.

---

## 1) 타겟 직무 정의 (Applied AI = Pre-Sales Architect)
이 직무는 **프리세일즈(Pre-Sales)** 성격이 핵심이며, 동시에 **초기 도입/배포(Deployment)까지 가이드**하는 성격이 섞여 있다.

### 반드시 보여줘야 하는 역량(포트폴리오 평가 항목)
- **Discovery → 요구사항을 기술 설계로 번역**
- **Evals/PoC 설계 및 성공 기준 설정**
- **Security/Governance**: RBAC, audit logs, redaction, prompt-injection defense, tool allowlist
- **Enterprise Integration**: SSO(OIDC/SAML), 업무툴(Slack), 티켓(Jira/ServiceNow)
- **Exec/Eng 커뮤니케이션 산출물**: 3분 임원용, 10분 엔지니어용 데모 스크립트
- **운영/관측성(LLMOps)**: metrics, cost/latency, 회귀 방지(eval gate)

---

## 2) 현재 내 상황 요약
- 이미 **Project 1 (Pre-Sales PoC Kit)** 를 완료했고, README/검증 흐름까지 “제출 가능한 수준”으로 정리되어 있음.
- 다음 단계는 이 PoC를 **엔터프라이즈 통합/현장 워크숍/안전성 레드팀/프로덕션 전환**으로 확장하여 “프리세일즈 실전감”을 극대화하는 것.

---

## 3) 프로젝트 로드맵 (1 → 5)
### Project 1 — Pre-Sales PoC Kit (완료 ✅)
**핵심:** Discovery → Secure Architecture → Evals → LLMOps/Deployment 준비  
**증거:** Proof 섹션( audit/eval/demo/metrics ), `make demo`, `pytest -q`, quick verify, acceptance tests 등  
**상태:** READY TO SUBMIT: YES (완료)

---

### Project 2 — Enterprise Integration Pack (SSO + Slack + Jira/ServiceNow) (진행 예정)
**목표:** “기존 기술 스택에 LLM를 실제로 붙일 줄 안다”를 증명  
**구성:**
- SSO: OIDC(mock) 기반 login + role claim → RBAC 매핑
- Slack: 이벤트/웹훅 입력 → UC1/UC2 실행 → 응답 템플릿 반환 + audit 기록
- Jira/ServiceNow: 티켓 텍스트 입력 → 요약/원인/다음 액션 생성 + audit 기록
**완성 기준:**
- 데모 스크립트에서 “SSO 로그인 → Slack 요청 → Jira 티켓 생성/요약”이 한 흐름으로 재현됨
- 통합 흐름에서도 audit/metrics가 남고, PII/redaction 정책이 유지됨

---

### Project 3 — Workshop-in-a-Box (고객 현장 워크숍 패키지) (진행 예정)
**목표:** “고객 현장 워크숍/딥다이브를 내가 설계하고 진행할 수 있다”를 증명  
**구성:**
- 3시간 워크숍 커리큘럼(문서) + 실습 3개(Discovery, BYO eval, Security review)
- 워크숍 산출물 자동 생성(brief, eval plan, ROI, PoC success criteria)
**완성 기준:**
- 처음 보는 사람이 문서만 보고 3시간 따라하면 `docs/samples/workshop_output/`에 산출물이 생성됨

---

### Project 4 — Red Team & Safety Eval Pack (안전성 평가/회귀 차단) (진행 예정)
**목표:** “safe & steerable” 철학에 정면으로 맞추기  
**구성:**
- redteam dataset(50+) + 평가 루브릭(refusal correctness, safe completion, tool misuse 방지)
- CI/게이트: safety/groundedness 기준 미달 시 fail
- 리포트: 실패 케이스 2~3개 + 개선(정책/프롬프트/필터) 루프
**완성 기준:**
- 안전성 점수/회귀 차단이 숫자로 증명되고, 데모에서 “공격 → 방어 → 로그 증거”가 재현됨

---

### Project 5 — PoC → Production Playbook (전환 플레이북) 또는 Exec Value Dashboard (진행 예정)
**목표:** “PoC에서 끝이 아니라 프로덕션 전환까지 가이드” 능력 증명

**Option A: PoC → Production Playbook**
- 데이터 거버넌스(PII/retention), 네트워크/프라이빗 연결(개념도), rate limit/retry/fallback
- 장애 대응(LLM failure modes) + 운영 체크리스트 + 결정 트리

**Option B: Executive Value Dashboard (1페이지)**
- ROI(월 절감/BE point), 품질(accuracy/groundedness/safety), 운영(latency/cost/volume)을 1페이지로
- PoC 산출물에서 자동으로 업데이트되는 형태

**완성 기준:**
- “임원 설득(1분) + 엔지니어 설득(10분)”을 같은 데이터로 끌고 갈 수 있음

---

## 4) 실행 원칙 (Codex에게 주는 공통 룰)
- **기존 작동 유지**: docker-compose, eval runner, metrics, demo scripts 깨지면 안 됨
- **증분 개발**: 큰 리팩터 금지, 최소 변경으로 기능 추가
- **각 프로젝트마다 Proof 남기기**: 문서 + 테스트 + 데모 재현(스크립트/출력/스크린샷 체크리스트)
- **보안/프라이버시 우선**: secrets 금지, 로그는 redacted/hashes 모드 제공

---

## 5) Project 2부터 시작 — Codex 실행 프롬프트(붙여넣기)
> 아래 프롬프트를 Codex에 그대로 넣고 Project 2를 구현한다.

```md
You are Codex. Start Project 2: Enterprise Integration Pack (SSO + Slack + Jira/ServiceNow).
Repo already works; DO NOT refactor or break existing commands.

## Hard rules
- Keep docker-compose, evals, metrics, and make demo working.
- Incremental changes only. Add docs + at least 1 test per integration.
- No secrets. Provide mock modes if real tokens are not available.

# Deliverables
1) SSO/OIDC mock integration
- Implement OIDC mock login flow (or a simple JWT issuer) producing role claims.
- Map role claims to existing RBAC model used in UC1 retrieval filter.
- Add docs: docs/integrations/sso_oidc.md
- Add test: tests/test_sso_rbac_mapping.py

2) Slack integration (mock webhook)
- Create an endpoint that receives Slack-style events/webhook payloads.
- Route messages to UC1/UC2 based on a command prefix (e.g., /uc1, /uc2).
- Return a Slack message payload template response (blocks or simple text).
- Ensure audit logs + metrics record the interaction.
- Docs: docs/integrations/slack.md
- Test: tests/test_slack_webhook.py

3) Jira or ServiceNow integration (choose one; default Jira)
- Create an endpoint that accepts a ticket payload (title, description, priority).
- Run UC2 log analysis or summarization and produce:
  - summary, suspected root cause, next steps, runbook links
- Write a “ticket comment” payload example.
- Ensure audit logs + metrics record the interaction.
- Docs: docs/integrations/jira.md (or servicenow.md)
- Test: tests/test_ticket_integration.py

4) Demo upgrades
- Update docs/sales/demo_script_eng.md to include a 10-min “integration demo” path:
  SSO login → Slack event → Jira ticket → show audit log → show metrics
- Add a “Proof” subsection in README linking to integration docs and sample payloads.

5) Sample payloads
- Add sample JSON payloads under app/backend/data/samples/:
  slack_event_sample.json, jira_ticket_sample.json, oidc_claims_sample.json
- No secrets; realistic values only.

## Final validation
- pytest -q must pass
- make demo must still run
- curl /metrics must still work
- Provide a short diff summary
Start now.
```

---

## 6) 끝
- Project 1은 완료.  
- 이제 Project 2부터 5까지 순차적으로 확장하여, Applied AI(Pre-Sales Architect) 지원 포트폴리오를 “현업형”으로 완성한다.
