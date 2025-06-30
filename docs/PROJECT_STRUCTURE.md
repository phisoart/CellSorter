# CellSorter Project Structure

## DEPRECATED/REMOVED COMPONENTS

The following components and files have been removed from the project structure:

### 1. Help System Components
**REMOVED**:
- Help menu handler components
- About dialog files
- Documentation viewer components
- Support/tutorial related files

### 2. Theme Management Files
**REMOVED**:
- Dark theme stylesheet files
- Theme toggle component files  
- Theme preference configuration files
- Dynamic theme switching logic

### 3. Expression Filter Components
**REMOVED**:
- Expression filter widget files (`expression_filter.py` functionality)
- Expression parser modules
- Filter validation components
- Advanced filtering UI elements

### 4. View Toggle Components
**REMOVED**:
- Panel visibility toggle components
- Layout state management files
- View configuration persistence files

### 5. Session Management Files *(NEW)*
**REMOVED**:
- `src/headless/session_manager.py` - Headless session management
- `src/models/session_manager.py` - GUI session management (if exists)
- Session serialization/deserialization modules
- Session file format handlers (.cellsession)
- Auto-save mechanism files
- Session backup and recovery systems
- Recent sessions cache management

**REMOVED TEST FILES**:
- `tests/dev_mode/test_session_save_load.py`
- `tests/dual_mode/test_session_save_load_consistency.py`
- `tests/gui_mode/test_session_save_load_production.py`
- `tests/test_headless/test_session_manager.py`
- `tests/test_auto_session.py`

**CONFIGURATION REMOVALS**:
- Session storage directories
- Session metadata schemas
- Session migration scripts

**Note**: The above components may still exist in the file system but should be considered deprecated and not used in new development.

## File Organization

```
├── PRODUCT_REQUIREMENTS.md          # 제품 요구사항 명세서 ('무엇'과 '왜')
├── README.md                        # 프로젝트 개요, 실행 방법, 설치 등
├── ARCHITECTURE.md                 # 전체 기술 아키텍처 및 기술 스택 설명
├── CODING_STYLE_GUIDE.md           # 네이밍 규칙, 디렉토리 구조, 문서화 규칙 등
├── TESTING_STRATEGY.md             # 단위/통합 테스트 계획, 도구, 커버리지 기준
├── .cursorignore                   # Cursor AI를 위한 명확한 행동 지침 정의
├── .gitignore                      # Git 버전 관리 무시 파일 설정
│
├── requirements.txt                # Python 라이브러리 명세
├── requirements-dev.txt            # 개발 및 테스트 의존성 명세  
├── requirements-build.txt          # 빌드/배포 의존성 명세
├── run.py                          # 간단한 애플리케이션 실행 스크립트
│
├── /docs/
│   ├── /design/
│   │   ├── DESIGN_SPEC.md          # 전체 UI 흐름, 페이지별 인터랙션 정의
│   │   ├── DESIGN_SYSTEM.md        # 버튼, 입력창 등 UI 컴포넌트 정의 및 속성
│   │   ├── assets/                 # 디자인에 쓰이는 이미지, 예시 mockup
│   │   └── style.css               # 주요 스타일 정의 파일 (디자인 시스템 기반)
│   │
│   ├── /examples/                  # 샘플 데이터 및 예제 파일
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
│   │   ├── /dialogs/               # 커스텀 다이얼로그
│   │   └── /widgets/               # 커스텀 위젯
│   ├── /pages/                     # 메인 애플리케이션 페이지/화면
│   ├── /models/                    # 데이터 모델 및 비즈니스 로직
│   ├── /utils/                     # 유틸리티 함수 및 헬퍼
│   ├── /config/                    # 설정 파일
│   ├── /assets/                    # 아이콘, 이미지 등 정적 파일
│   ├── /logic/                     # 추가 비즈니스 로직 (예비)
│   ├── /ui/                        # UI 관련 추가 파일 (예비)
│   └── main.py                     # 애플리케이션 진입점
│
├── /tests/                         # 단위 및 통합 테스트 코드
│   ├── conftest.py                 # pytest 설정 및 공통 fixtures
│   ├── test_*.py                   # 개별 테스트 파일들
│   └── .gitkeep                    # 빈 디렉토리 유지용
│
└── /.cursor/                       # Cursor IDE 설정
    └── /rules/                     # 프로젝트별 AI 규칙 정의
        ├── base-rules.mdc          # 기본 개발 규칙
        └── update-rules.mdc        # 프로젝트 업데이트 규칙
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
- **requirements-dev.txt**: 개발 및 테스트 의존성 명세
- **requirements-build.txt**: 빌드/배포 의존성 명세
- **run.py**: 간단한 애플리케이션 실행 스크립트

### Documentation (/docs/)
- **design/**: UI/UX 설계 관련 문서
- **examples/**: 샘플 데이터 및 예제 파일들
- **USER_PERSONAS.md**: 타겟 사용자 정의
- **USER_SCENARIOS.md**: 사용자 시나리오 및 워크플로우
- **PROJECT_STRUCTURE.md**: 이 파일 - 프로젝트 구조 설명

### Source Code (/src/)
- **components/**: 재사용 가능한 UI 컴포넌트
  - **dialogs/**: 모달 다이얼로그 컴포넌트들
  - **widgets/**: 커스텀 위젯 컴포넌트들
- **pages/**: 메인 애플리케이션 화면
- **models/**: 데이터 모델 및 비즈니스 로직
- **utils/**: 공통 유틸리티 함수
- **config/**: 애플리케이션 설정
- **assets/**: 정적 리소스 파일
- **logic/**: 추가 비즈니스 로직 (예비 디렉토리)
- **ui/**: UI 관련 추가 파일 (예비 디렉토리)
- **main.py**: 애플리케이션 진입점

### Tests (/tests/)
- 소스 코드 구조를 미러링하는 테스트 파일들
- **conftest.py**: pytest 설정 및 공통 fixtures
- **test_*.py**: 개별 테스트 파일들

### IDE Configuration (/.cursor/)
- **rules/**: Cursor AI를 위한 프로젝트별 규칙 정의
  - **base-rules.mdc**: 기본 개발 규칙 (TDD, 크로스 플랫폼, 코드 스타일 등)
  - **update-rules.mdc**: 프로젝트 업데이트 및 문서 동기화 규칙

### Note on CONTRIBUTING.md, RELEASE_PLAN.md
- 본 프로젝트는 별도의 CONTRIBUTING.md, RELEASE_PLAN.md 파일을 생성하지 않습니다. 관련 규칙 및 워크플로우는 README.md 및 기타 문서에 통합되어 관리됩니다.

### Note on IDE Configuration
현재 프로젝트는 Cursor IDE의 기본 설정을 사용하며, 별도의 `.cursor/` 디렉토리 구성 없이 `.cursorignore` 파일을 통해 필요한 설정을 관리합니다. 향후 프로젝트 복잡도가 증가하면 별도의 Cursor 설정 디렉토리 구성을 고려할 수 있습니다. 