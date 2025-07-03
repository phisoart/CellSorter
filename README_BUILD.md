# CellSorter 실행파일 빌드 가이드

PyInstaller를 사용하여 CellSorter를 단일 실행파일로 빌드하는 방법입니다.

## 시스템 요구사항

- **Python 3.12+** (Anaconda/Miniconda 권장)
- **cellsorter conda 환경** 설정 완료
- **최소 4GB RAM** (빌드 과정에서 메모리 사용량이 높음)
- **최소 2GB 여유 디스크 공간**

## 빌드 방법

### Windows

```bash
# 1. 저장소 클론 및 이동
git clone https://github.com/phisoart/CellSorter.git
cd CellSorter

# 2. 실행파일 빌드
build.bat

# 3. 실행
dist\CellSorter.exe
```

### macOS/Linux

```bash
# 1. 저장소 클론 및 이동
git clone https://github.com/phisoart/CellSorter.git
cd CellSorter

# 2. 실행파일 빌드
./build.sh

# 3. 실행
./dist/CellSorter
```

## 수동 빌드 (고급 사용자용)

```bash
# 1. 환경 활성화
conda activate cellsorter

# 2. 빌드 의존성 설치
pip install -r build_requirements.txt

# 3. 빌드 실행
pyinstaller build_exe.spec --clean --noconfirm
```

## 빌드 결과물

- **Windows**: `dist\CellSorter.exe` (약 200-300MB)
- **macOS**: `dist/CellSorter` (약 200-300MB)
- **Linux**: `dist/CellSorter` (약 200-300MB)

## 특징

✅ **Single File**: 하나의 실행파일로 모든 의존성 포함  
✅ **No Console**: GUI 전용, 터미널 창 없음  
✅ **Portable**: 별도 설치 없이 바로 실행 가능  
✅ **All Modes**: GUI, DEV, DUAL 모드 모두 지원  

## 주의사항

- 첫 실행 시 압축 해제로 인해 시작이 다소 느릴 수 있습니다
- Windows Defender 등 백신에서 오탐지될 수 있습니다
- 실행파일 크기가 큽니다 (모든 의존성 포함 때문)

## 문제해결

### 빌드 실패 시
```bash
# 환경 재생성
conda env remove -n cellsorter
conda create -n cellsorter python=3.12
conda activate cellsorter
pip install -r requirements.txt
pip install -r build_requirements.txt
```

### 실행 실패 시
- 백신 프로그램에서 실행파일을 예외 처리하세요
- Windows에서는 관리자 권한으로 실행해보세요
- 임시 폴더 용량을 확인하세요 (압축 해제 공간 필요)

---

빌드 관련 문의는 GitHub Issues에서 해주세요. 