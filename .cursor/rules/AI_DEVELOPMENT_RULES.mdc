---
description: # AI Development Rules for CellSorter
globs: 
alwaysApply: false
---
# AI 개발 규칙

## 3모드 테스트 패턴

### DEV 모드 (헤드리스 시뮬레이션)
```python
def test_dev_mode_interactions():
    dev_tester = DevModeHeadlessTester()
    
    # 모든 인터랙션 시뮬레이션
    dev_tester.simulate_all_button_clicks()
    dev_tester.simulate_all_drag_operations()
    dev_tester.simulate_keyboard_navigation()
    
    # UX 검증
    dev_tester.validate_color_scheme()
    dev_tester.validate_responsive_layout()
    dev_tester.test_complete_user_journeys()
    
    assert dev_tester.all_interactions_successful()
    assert dev_tester.design_meets_ux_standards()
```

### DUAL 모드 (GUI 일치성 검증)
```python
def test_dual_mode_validation():
    # DEV 모드 기준선
    dev_results = DevModeHeadlessTester().run_all_tests()
    
    # GUI 모드 비교
    gui_tester = GUIModeValidator()
    gui_results = gui_tester.run_same_tests()
    
    # 일치성 검증
    assert dev_results.interactions == gui_results.interactions
    gui_tester.validate_visual_rendering()
    gui_tester.validate_real_mouse_interactions()
    
    # 동기화 검증
    sync_tester = HeadlessGUISyncTester()
    sync_tester.test_real_time_sync()
    
    assert gui_tester.gui_matches_dev_expectations()
    assert sync_tester.sync_working_properly()
```

### GUI 모드 (프로덕션)
```python
def test_gui_mode_production():
    gui_tester = GUIModeProductionTester()
    
    # 실제 하드웨어 인터랙션
    gui_tester.test_real_mouse_clicks()
    gui_tester.test_real_keyboard_input()
    
    # 프로덕션 성능
    gui_tester.validate_startup_time()
    gui_tester.validate_memory_usage()
    gui_tester.test_long_running_operations()
    
    assert gui_tester.production_ready()
```

## 필수 개발 순서
1. **DEV → DUAL → GUI** (예외 없음)
2. 모든 모드 통과해야 통합 가능

## UI 정의 구조
```yaml
version: "1.0"
metadata:
  created_by: "AI Agent"
  description: "UI 목적"

widgets:
  - type: QPushButton
    name: submitButton  # camelCase + 타입 접미사
    properties:
      text: "Submit"
    events:
      - signal: clicked
        handler: on_submitButton_clicked  # 표준 패턴
```

## 모드별 코드 생성
```python
def create_ui():
    mode = get_current_mode()
    
    if mode == "dev":
        return create_headless_ui()
    elif mode == "dual":  
        return create_dual_mode_ui()
    elif mode == "gui":
        return create_qt_widgets()
```

## 테스트 명령어
```bash
# DEV 모드
python run.py --dev-mode --test-all-interactions
pytest tests/test_dev_mode_complete.py -v

# DUAL 모드  
python run.py --dual-mode --validate-gui
pytest tests/test_dual_mode_validation.py -v

# GUI 모드
python run.py --gui-mode --production-test
pytest tests/test_gui_mode_production.py -v
```
