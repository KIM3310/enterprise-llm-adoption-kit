# 영상 시연 런북 (LLM + 시스템 아키텍처)

## 0) 보안 원칙 (중요)
- 실제 API 키를 문서/코드/Git에 직접 저장하지 않습니다.
- 키는 런타임에만 입력합니다.
- 시연 후 키를 회전(폐기 후 재발급)하는 것을 권장합니다.

## 1) 시연 전 준비
1. 백엔드 실행
```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app
```

2. 프론트엔드 실행
```bash
cd app/frontend
npm install
npm run dev
```

3. 브라우저 접속
- `http://localhost:5173`

## 2) OpenAI 키 연결 방법

### 방법 A: UI에서 런타임 입력 (시연에 가장 쉬움)
1. UI에서 `Role=Admin`으로 로그인
2. `Admin Runtime LLM Settings` 카드로 이동
3. 아래 값 입력 후 저장
   - `Provider`: `openai`
   - `Model`: `gpt-4o-mini` (또는 원하는 모델)
   - `OpenAI API Key`: `sk-...` (실제 키)
4. `Save Runtime Settings` 클릭
5. `API key configured: yes` 확인

### 방법 B: 터미널 환경변수
```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o-mini
export LLM_OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
```
- 백엔드를 재시작하면 반영됩니다.

## 3) 시스템 아키텍처 샘플 넣는 방법

샘플 파일:
- `app/backend/data/samples/architecture_import_sample.jsonl`

UI에서 입력:
1. `Architecture Dataset Manager` 카드 이동
2. `Choose JSONL File` 클릭 후 위 파일 선택
3. `Import + Reindex` 클릭
4. 완료 후 아래 메타 정보 확인
   - `Docs`, `Indexed chunks`, `Systems`, `Envs`, `Access groups`

## 4) 시연 흐름 (권장 5~7분)

1. 로그인 및 목적 설명 (30초)
- "엔터프라이즈 LLM 도입 전, 아키텍처 진단/보안/운영 가능성을 검증하는 데모"라고 설명

2. LLM 연결 시연 (1분)
- `Admin Runtime LLM Settings`에서 `openai` + 모델 + API 키 저장
- `API key configured: yes` 확인

3. 아키텍처 데이터 주입 시연 (1분)
- `architecture_import_sample.jsonl` 업로드
- `Import + Reindex` 후 카탈로그 수치 확인

4. 아키텍처 진단 실행 (2분)
- 탭에서 Architecture 진단 실행
- 예시 질의:
  - `payments prod architecture에서 가장 위험한 운영 리스크 3가지를 우선순위로 정리해줘`
- `system=payments`, `env=prod` 지정해서 실행
- 답변 + citations 확인

5. 통제 포인트 시연 (1~2분)
- `Citation only` 켜고 다시 실행 (민감 환경에서 근거 중심 응답)
- Role을 `Employee`로 바꿔 같은 질문 실행 (RBAC 필터 차이 설명)
- 필요시 `Runtime Debug Snapshot`으로 최근 이벤트/상태 확인

## 5) 시연 멘트 예시
- "이 데모는 단순 챗봇이 아니라, 아키텍처 데이터 주입 후 role/system/env 기준으로 검색 범위를 통제합니다."
- "LLM 호출 전후에 redaction/injection 가드가 있고, 결과는 audit/metrics로 관측됩니다."
- "운영 관점에서 모델/파라미터/API 연결을 런타임에서 안전하게 교체할 수 있습니다."

## 6) 시연 후 정리
1. 키 제거
```bash
unset LLM_OPENAI_API_KEY
```
2. 사용한 OpenAI API 키 회전(재발급) 권장

