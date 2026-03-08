# Enterprise LLM Adoption Kit Service-Grade SPECKIT

Last updated: 2026-03-08

## S - Scope
- 대상 repo: `enterprise-llm-adoption-kit`
- 이번 iteration 목표:
  - 분산된 discovery/security/evals/ops 증거를 하나의 서비스 브리프로 압축
  - 운영자/구매자 관점에서 바로 이해되는 `readiness board`를 홈과 validation 화면에 노출
  - 백엔드 계약형 surface 추가: `GET /ops/service-brief`, `GET /ops/service-brief/schema`
  - executive 시점의 proof bundle을 `GET /ops/review-pack`으로 분리

## P - Product Thesis
- 이 repo의 강점은 기능 수가 아니라 `enterprise rollout 전체 흐름`을 한 저장소 안에서 보여준다는 점이다.
- 따라서 이번 단계의 핵심은 기능을 더 붙이는 것이 아니라, 이미 있는 증거를 `서비스 수준의 문맥`으로 재조립하는 것이다.
- 리뷰어가 2분 안에 봐야 할 것:
  - 어떤 단계(Discovery -> Security -> Evals -> Deployment -> Operations)를 다루는가
  - 어떤 증거가 실제로 존재하는가
  - 지금 런타임 posture가 무엇인가
  - 어떤 플랫폼 대화(AWS/Snowflake/Palantir)까지 이어질 수 있는가

## E - Execution
- 백엔드
  - `service_brief.py` 추가
  - typed response model 추가
  - `/health` links/capabilities 확장
  - `GET /ops/service-brief`
  - `GET /ops/service-brief/schema`
  - `GET /ops/review-pack`
- 프론트엔드
  - `ServiceBriefBoard` 컴포넌트 추가
  - `ExecutiveReviewPack` 컴포넌트 추가
  - Home/Readiness 상단에 readiness board 삽입
  - Home/Readiness에 buyer thesis와 rollout track을 보여주는 review pack 삽입
  - 백엔드 미연결 상황에서도 static fallback으로 서비스 브리프 유지
- 문서
  - README / README.ko에 service-grade surface 설명 추가
  - 본 문서로 이번 iteration의 spec 기록

## C - Criteria
- PASS 조건
  - 백엔드 응답 계약이 테스트로 고정된다
  - 홈 화면에서 광고보다 먼저 서비스 증거가 보인다
  - validation 화면에서 추상적 체크리스트 대신 실제 artifact/stage 기반 readiness가 보인다
  - reviewer가 buyer promise, rollout track, platform dialogue를 UI에서 바로 읽는다
  - 정적 배포 환경에서도 fallback 데이터로 UX가 무너지지 않는다
  - `pytest -q` 및 `npm run build`가 통과한다

## K - Keep
- synthetic/demo라는 한계는 숨기지 않는다
- README의 honest framing 유지
- runtime diagnostics, audit, evals 같은 "운영 증거"는 계속 제품 표면에 노출한다

## I - Improve
- 다음 iteration 후보
  - buyer persona별 demo mode (`exec`, `security`, `platform`) preset
  - `/ops/service-brief`를 markdown export 가능한 brief로 확장
  - Scenario Runner 결과와 service brief를 연결한 evidence pack 생성
  - Control Tower와 Snowflake/Palantir ontology narrative를 더 정교하게 매핑

## T - Trace
- 관련 surface
  - `app/backend/app/service_brief.py`
  - `app/backend/app/main.py`
  - `app/frontend/src/components/ServiceBriefBoard.jsx`
  - `app/frontend/src/components/ExecutiveReviewPack.jsx`
  - `app/frontend/src/App.jsx`
  - `app/frontend/src/style.css`
  - `tests/test_service_brief.py`
  - `tests/test_ui_service_brief.py`
