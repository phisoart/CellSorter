# CellSorter Project Structure

## File Organization

```
├── PRODUCT_REQUIREMENTS.md          # 제품 요구사항 명세서 ('무엇'과 '왜')
├── README.md                        # 프로젝트 개요, 실행 방법, 설치 등
├── ARCHITECTURE.md                 # 전체 기술 아키텍처 및 기술 스택 설명
├── CODING_STYLE_GUIDE.md           # 네이밍 규칙, 디렉토리 구조, 문서화 규칙 등
├── TESTING_STRATEGY.md             # 단위/통합 테스트 계획, 도구, 커버리지 기준
├── CONTRIBUTING.md                 # 개발 참여자를 위한 워크플로우와 협업 가이드
├── .cursor-rules                   # Cursor AI를 위한 명확한 행동 지침 정의
│
├── package.json                    # (선택) 의존성 관리용 (Python이면 requirements.txt)
├── requirements.txt                # Python 라이브러리 명세
│
├── /docs/
│   ├── /design/
│   │   ├── DESIGN_SPEC.md          # 전체 UI 흐름, 페이지별 인터랙션 정의
│   │   ├── DESIGN_SYSTEM.md        # 버튼, 입력창 등 UI 컴포넌트 정의 및 속성
│   │   ├── assets/                 # 디자인에 쓰이는 이미지, 예시 mockup
│   │   └── style.css               # 주요 스타일 정의 파일 (디자인 시스템 기반)
│   │
│   ├── USER_PERSONAS.md            # 주요 사용자 유형 정의 (페르소나)
│   ├── USER_SCENARIOS.md           # 페르소나 기반 시나리오 (예: "이미지를 자르고 저장")
│   └── RELEASE_PLAN.md             # 기능 릴리즈 일정 및 배포 방법 정리
│
├── /src/                           # PySide6 애플리케이션 코드
│   ├── /components/                # 재사용 가능한 UI 컴포넌트
│   │   ├── __init__.py
│   │   ├── /base/                  # 기본 컴포넌트 클래스
│   │   ├── /dialogs/               # 커스텀 다이얼로그
│   │   └── /widgets/               # 커스텀 위젯
│   ├── /pages/                     # 메인 애플리케이션 페이지/화면
│   ├── /models/                    # 데이터 모델 및 비즈니스 로직
│   ├── /utils/                     # 유틸리티 함수 및 헬퍼
│   ├── /config/                    # 설정 파일
│   ├── /assets/                    # 아이콘, 이미지 등 정적 파일
│   └── main.py                     # 애플리케이션 진입점
│
└── /tests/                         # 단위 및 통합 테스트 코드
    ├── /components/                # 컴포넌트 테스트
    ├── /pages/                     # 페이지 테스트
    ├── /models/                    # 모델 테스트
    └── /utils/                     # 유틸리티 테스트
```

## Directory Descriptions

### Root Level Files
- **PRODUCT_REQUIREMENTS.md**: 제품의 기능 요구사항과 비즈니스 목표
- **README.md**: 프로젝트 설치, 실행, 사용법 가이드
- **ARCHITECTURE.md**: 기술 스택, 시스템 아키텍처, 설계 결정사항
- **CODING_STYLE_GUIDE.md**: 코딩 컨벤션, 네이밍 규칙, 문서화 규칙
- **TESTING_STRATEGY.md**: 테스트 전략, 도구, 커버리지 기준
- **CONTRIBUTING.md**: 기여자를 위한 개발 워크플로우

### Configuration Files
- **requirements.txt**: Python 의존성 라이브러리 명세
- **package.json**: Node.js 의존성 (선택사항)

### Documentation (/docs/)
- **design/**: UI/UX 설계 관련 문서
- **USER_PERSONAS.md**: 타겟 사용자 정의
- **USER_SCENARIOS.md**: 사용자 시나리오 및 워크플로우
- **RELEASE_PLAN.md**: 릴리즈 계획 및 배포 전략

### Source Code (/src/)
- **components/**: 재사용 가능한 UI 컴포넌트
- **pages/**: 메인 애플리케이션 화면
- **models/**: 데이터 모델 및 비즈니스 로직
- **utils/**: 공통 유틸리티 함수
- **config/**: 애플리케이션 설정
- **assets/**: 정적 리소스 파일

### Tests (/tests/)
- 소스 코드 구조를 미러링하는 테스트 파일들 