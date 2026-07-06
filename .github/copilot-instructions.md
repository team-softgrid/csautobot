# GitHub Copilot Instructions — csautobot
# .github/copilot-instructions.md
# 원본: team-softgrid/ai-harness

## 프로젝트 컨텍스트
- 레포: team-softgrid/csautobot
- 스택: {{STACK}}
- 전체 행동 규칙: AGENTS.md 참조

## 코드 생성 규칙
- 기존 파일의 코드 스타일과 네이밍을 따른다
- TypeScript 사용 시 any 타입 금지
- 비동기 함수는 항상 try-catch 또는 에러 핸들링 포함
- 환경변수는 process.env.XXX 형식으로만 참조

## 테스트 규칙
- 새 함수 작성 시 대응하는 테스트 파일도 함께 제안
- 테스트 파일 위치: `__tests__/` 또는 `*.test.ts`
- 커버리지 목표: 80% 이상

## 보안 규칙
- API 키, 비밀번호 하드코딩 제안 금지
- SQL 쿼리는 파라미터 바인딩 방식으로만 제안
- 사용자 입력은 반드시 검증 로직 포함
