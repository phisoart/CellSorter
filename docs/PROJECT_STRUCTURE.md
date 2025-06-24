# CellSorter Project Structure

## File Organization

```
├── PRODUCT_REQUIREMENTS.md          # 제품 요구사항 명세서 ('무엇'과 '왜')
├── README.md                        # 프로젝트 개요, 실행 방법, 설치 등
├── ARCHITECTURE.md                 # 전체 기술 아키텍처 및 기술 스택 설명
├── CODING_STYLE_GUIDE.md           # 네이밍 규칙, 디렉토리 구조, 문서화 규칙 등
├── TESTING_STRATEGY.md             # 단위/통합 테스트 계획, 도구, 커버리지 기준
├── .cursorignore                   # Cursor IDE용 무시 파일 설정
├── .gitignore                      # Git 버전 관리 무시 파일 설정
│
├── requirements.txt                # Python 라이브러리 명세
│
├── /docs/
│   ├── /design/
│   │   ├── DESIGN_SPEC.md          # 전체 UI 흐름, 페이지별 인터랙션 정의
│   │   ├── DESIGN_SYSTEM.md        # 버튼, 입력창 등 UI 컴포넌트 정의 및 속성
│   │   ├── assets/                 # 디자인에 쓰이는 이미지, 예시 mockup
│   │   └── style.css               # 주요 스타일 정의 파일 (디자인 시스템 기반)
│   │
│   ├── /examples/                  # 예제 데이터 파일들
│   │   ├── data_FilterObjects_dapi_CK7n_CK20_CDX2.csv  # CellProfiler CSV 예제
│   │   └── example.cxprotocol      # CosmoSort 프로토콜 예제
│   │
│   ├── USER_PERSONAS.md            # 주요 사용자 유형 정의 (페르소나)
│   ├── USER_SCENARIOS.md           # 페르소나 기반 시나리오 (예: "이미지를 자르고 저장")
│   └── PROJECT_STRUCTURE.md        # 프로젝트 구조 설명 문서
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

### Configuration Files
- **requirements.txt**: Python 의존성 라이브러리 명세
- **.cursorignore**: Cursor IDE가 무시할 파일/디렉토리 패턴
- **.gitignore**: Git 버전 관리에서 제외할 파일/디렉토리 패턴

### Documentation (/docs/)
- **design/**: UI/UX 설계 관련 문서
  - **DESIGN_SPEC.md**: 전체 UI 플로우 및 인터랙션 정의
  - **DESIGN_SYSTEM.md**: 컴포넌트 라이브러리 및 디자인 시스템
  - **style.css**: shadcn/ui + qt-material 스타일 정의
  - **assets/**: 디자인 관련 이미지 및 mockup 파일
- **examples/**: 샘플 데이터 및 예제 파일
- **USER_PERSONAS.md**: 타겟 사용자 정의
- **USER_SCENARIOS.md**: 사용자 시나리오 및 워크플로우
- **PROJECT_STRUCTURE.md**: 이 파일 - 프로젝트 구조 설명

### Source Code (/src/)
- **components/**: 재사용 가능한 UI 컴포넌트
  - **base/**: 기본 추상 컴포넌트 클래스들
  - **dialogs/**: 모달 다이얼로그 컴포넌트들
  - **widgets/**: 커스텀 위젯 컴포넌트들
- **pages/**: 메인 애플리케이션 화면 및 뷰
- **models/**: 데이터 모델 및 비즈니스 로직
- **utils/**: 공통 유틸리티 함수 및 헬퍼
- **config/**: 애플리케이션 설정 및 상수
- **assets/**: 정적 리소스 파일 (아이콘, 이미지 등)
- **main.py**: 애플리케이션 메인 진입점

### Tests (/tests/)
- 소스 코드 구조를 미러링하는 테스트 파일들
- **components/**: UI 컴포넌트 테스트
- **pages/**: 페이지/뷰 테스트
- **models/**: 비즈니스 로직 테스트
- **utils/**: 유틸리티 함수 테스트

### Development Configuration
- **.cursorignore**: Cursor IDE가 분석에서 제외할 파일/폴더 패턴 정의
- **.gitignore**: Git 버전 관리에서 제외할 파일/폴더 패턴 정의

### Note on IDE Configuration
현재 프로젝트는 Cursor IDE의 기본 설정을 사용하며, 별도의 `.cursor/` 디렉토리 구성 없이 `.cursorignore` 파일을 통해 필요한 설정을 관리합니다. 향후 프로젝트 복잡도가 증가하면 별도의 Cursor 설정 디렉토리 구성을 고려할 수 있습니다. 