# 데모 스크립트 (엔지니어링, 10분)

## 목적
아키텍처, 보안 통제, 평가, 관측성을 기술적으로 설명한다.

## 아젠다
1) 아키텍처 및 Trust Boundary
2) UC1 RAG + citations + RBAC
3) UC2 tool calling + redaction
4) 감사 로그 + metrics + rate limit
5) eval runner + baseline diff

## 진행
1) 아키텍처 (2분)
   - `docs/blueprint/02_architecture.md` 설명
   - Trust boundary와 데이터 흐름 강조

2) 인증/RBAC (1분)
   - Employee vs Admin 비교
   - 문서 접근 범위 차이 확인

3) UC1 RAG (2분)
   - 질의 실행
   - citations 확인 (doc_id + field_path)
   - citation-only 모드 전환

4) UC2 Log Intelligence (2분)
   - PII 포함 로그 입력
   - redaction 적용 및 tool calls 확인

5) 관측성 (1분)
   - `/metrics` 확인
   - audit log 스키마 설명

6) Evals (2분)
   - eval runner 실행
   - report.md + baseline diff 확인

