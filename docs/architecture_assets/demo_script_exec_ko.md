# 데모 스크립트 (임원용, 3분)

## 목적
엔터프라이즈 안전성과 운영 준비도를 3분 내로 보여준다.

## 흐름
1) 포지셔닝 (20초)
   - "본 키트는 한국 시장용 Applied AI 기술 검토를 위한 엔터프라이즈 LLM 도입 레퍼런스입니다."
   - "두 가지 핵심 시나리오: Handover Copilot, DevOps Log Intelligence"

2) 보안/거버넌스 (45초)
   - Ops로 로그인 -> RBAC 강조
   - 감사 로그 필드와 PII 마스킹 표시
   - 프롬프트 인젝션 방어 + 도구 allowlist 언급

3) UC1: Handover Copilot (45초)
   - "payments prod handover 리스크 요약" 요청
   - citations (doc_id + field_path) 확인
   - citation-only 모드 전환 강조

4) UC2: Log Intelligence (45초)
   - 에러 로그 붙여넣기
   - 요약/가설/런북 단계 확인
   - tool calls가 allowlist만 사용함을 확인

5) 마무리 (25초)
   - "LLM API는 어댑터로 쉽게 교체 가능"
   - "Evals/LLMOps 포함으로 안전한 확장 가능"

