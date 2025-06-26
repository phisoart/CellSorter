# CellSorter Architecture Documentation

## System Overview

CellSorter is a sophisticated GUI-based software application designed to work in conjunction with the CosmoSort hardware instrument for advanced cell sorting and tissue extraction from pathology slides. The software serves as the analytical frontend that processes microscopy images and CellProfiler-generated CSV data to enable precise cell selection and coordinate transformation for automated tissue extraction.

### Technology Stack

- **Framework**: PySide6 (Qt for Python)
- **Image Processing**: OpenCV, Pillow, NumPy
- **Data Analysis**: Pandas, NumPy
- **Visualization**: Matplotlib (embedded in Qt)
- **File I/O**: Python standard libraries
- **Coordinate Mathematics**: NumPy for affine transformations
- **Development/Testing**: pytest, black, flake8, mypy 등은 requirements-dev.txt에 분리 관리
- **Build/Deployment**: pyinstaller 등은 requirements-build.txt에 분리 관리

### Integration Context

CellSorter operates as a bridge between:
- **CellProfiler**: Provides cellular analysis and feature extraction
- **CosmoSort Hardware**: Receives coordinate instructions for physical tissue extraction
- **96-Well Plate System**: Standard laboratory automation integration

## Data Flow Architecture

```
[Microscopy Image (TIFF/JPG/PNG)] ──┐
                                    ├──► [CellSorter GUI] ──► [.cxprotocol Export] ──► [CosmoSort Hardware]
[CellProfiler CSV Data] ────────────┘
```

### Detailed Data Flow

1. **Input Stage**
   - Load microscopy image (TIFF/JPG/JPEG/PNG) → Image Handler
   - Parse CellProfiler CSV → CSV Parser
   - Extract cellular features and coordinates

2. **Analysis Stage**
   - Generate scatter plot from selected CSV columns → Scatter Plot View
   - Enable user interaction for cell selection → Selection Manager
   - Apply color coding and labeling → UI Controller

3. **Calibration Stage**
   - Capture user-defined reference points → Coordinate Transformer
   - Calculate affine transformation parameters
   - Map pixel coordinates to stage coordinates

4. **Export Stage**
   - Generate cropped regions from bounding boxes → Extractor
   - Create .cxprotocol file with coordinates and metadata
   - Prepare data for CosmoSort hardware consumption

## Core Components Architecture

### Implementation Status: ✅ **85% Complete - Production Ready**

All core scientific functionality is implemented and operational. The application successfully provides end-to-end workflow from image loading to protocol export.

### 1. GUI Controller (`src/pages/main_window.py`) ✅ COMPLETE

**Responsibilities:**
- Main application window management
- Menu system and toolbar actions
- Status bar updates and user feedback
- Component orchestration

**Key Methods:**
```python
class MainWindow(QMainWindow):
    def __init__(self)
    def load_image(self, file_path: str) -> bool
    def load_csv(self, file_path: str) -> bool
    def update_status(self, message: str) -> None
    def export_protocol(self, file_path: str) -> bool
```

### 2. Image Handler (`src/models/image_handler.py`) ✅ COMPLETE

**Responsibilities:**
- Multi-format image loading and validation (TIFF/JPG/JPEG/PNG)
- Image display and zoom functionality
- Overlay management for cell highlighting
- Coordinate tracking for user interactions

**Key Features:**
- Multi-channel image support
- Memory-efficient image handling
- Real-time overlay rendering
- Pixel-to-stage coordinate mapping

```python
class ImageHandler:
    def load_image(self, file_path: str) -> np.ndarray
    def apply_overlay(self, selections: List[CellSelection]) -> None
    def pixel_to_stage(self, pixel_coords: Tuple[int, int]) -> Tuple[float, float]
    def get_crop_region(self, bounding_box: BoundingBox) -> np.ndarray
```

### 3. CSV Parser (`src/models/csv_parser.py`) ✅ COMPLETE

**Responsibilities:**
- CellProfiler CSV data validation and parsing ✅
- Feature extraction and data cleaning ✅
- Column mapping and data type conversion ✅
- Coordinate extraction for bounding boxes ✅

**Data Schema Handling:**
```python
class CSVParser:
    REQUIRED_COLUMNS = [
        'AreaShape_BoundingBoxMaximum_X',
        'AreaShape_BoundingBoxMinimum_X', 
        'AreaShape_BoundingBoxMaximum_Y',
        'AreaShape_BoundingBoxMinimum_Y'
    ]
    
    def parse_csv(self, file_path: str) -> pd.DataFrame
    def validate_columns(self, df: pd.DataFrame) -> bool
    def extract_bounding_boxes(self) -> List[BoundingBox]
    def get_signal_columns(self) -> List[str]
```

### 4. Scatter Plot View (`src/components/widgets/scatter_plot.py`) ✅ COMPLETE

**Responsibilities:**
- Interactive matplotlib scatter plot generation ✅
- Rectangle selection tool (shift+drag) ✅
- Real-time cell highlighting ✅
- Axis configuration and labeling ✅

**Interaction Model:**
```python
class ScatterPlotWidget(QWidget):
    selection_changed = Signal(list)  # Emitted when cells are selected
    
    def __init__(self, parent=None)
    def plot_data(self, x_data: np.ndarray, y_data: np.ndarray) -> None
    def enable_rectangle_selection(self) -> None
    def highlight_selected_cells(self, indices: List[int]) -> None
    def get_selected_indices(self) -> List[int]
```

### 5. Selection Manager (`src/models/selection_manager.py`) ✅ COMPLETE

**Responsibilities:**
- Cell selection state management ✅
- Color assignment and tracking ✅
- Label management system ✅
- 96-well plate coordinate mapping ✅

**Well Plate Mapping Logic:**
```python
class SelectionManager:
    WELL_LAYOUT = [
        "A01", "B01", "C01", "D01", "E01", "F01", "G01", "H01",
        "A02", "B02", "C02", "D02", "E02", "F02", "G02", "H02",
        # ... continues to H12
    ]
    
    COLOR_PALETTE = {
        "Red": "#FF0000", "Green": "#00FF00", "Blue": "#0000FF",
        "Yellow": "#FFFF00", "Magenta": "#FF00FF", "Cyan": "#00FFFF",
        # ... complete color dictionary
    }
    
    def add_selection(self, cell_indices: List[int], color: str, label: str) -> str
    def assign_well_coordinates(self, selection_id: str) -> str
    def get_selection_table_data(self) -> List[Dict]
    def update_selection_color(self, selection_id: str, color: str) -> None
```

### 6. Coordinate Transformer (`src/models/coordinate_transformer.py`) ✅ COMPLETE

**Responsibilities:**
- Two-point calibration system ✅
- Affine transformation calculation ✅
- Pixel-to-stage coordinate conversion ✅
- Transformation matrix management ✅

**Mathematical Implementation:**
```python
class CoordinateTransformer:
    def __init__(self):
        self.calibration_points: List[CalibrationPoint] = []
        self.transform_matrix: np.ndarray = None
    
    def add_calibration_point(self, pixel_coord: Tuple[int, int], 
                            stage_coord: Tuple[float, float]) -> None
    
    def calculate_affine_transform(self) -> bool:
        """
        Calculate affine transformation matrix using two calibration points.
        
        Mathematical approach:
        1. Create coefficient matrix from pixel coordinates
        2. Solve linear system for transformation parameters
        3. Construct 3x3 affine transformation matrix
        """
        if len(self.calibration_points) < 2:
            return False
            
        # Extract pixel and stage coordinates
        pixel_coords = np.array([[p.pixel_x, p.pixel_y, 1] for p in self.calibration_points])
        stage_coords = np.array([[p.stage_x, p.stage_y] for p in self.calibration_points])
        
        # Solve for transformation parameters
        self.transform_matrix = np.linalg.lstsq(pixel_coords, stage_coords, rcond=None)[0]
        return True
    
    def transform_coordinates(self, pixel_coords: List[Tuple[int, int]]) -> List[Tuple[float, float]]
```

### 7. Extractor (`src/models/extractor.py`) ✅ COMPLETE

**Responsibilities:**
- Square crop region calculation ✅
- .cxprotocol file generation ✅
- Metadata compilation ✅
- Export validation ✅

**Crop Algorithm:**
```python
class Extractor:
    def calculate_square_crop(self, bounding_box: BoundingBox) -> CropRegion:
        """
        Generate square crop from bounding box by selecting shorter side
        and centering the square region.
        """
        width = bounding_box.max_x - bounding_box.min_x
        height = bounding_box.max_y - bounding_box.min_y
        
        # Use shorter side for square dimension
        crop_size = min(width, height)
        
        # Calculate centered position
        center_x = (bounding_box.max_x + bounding_box.min_x) / 2
        center_y = (bounding_box.max_y + bounding_box.min_y) / 2
        
        return CropRegion(
            x=center_x - crop_size/2,
            y=center_y - crop_size/2,
            size=crop_size
        )
    
    def generate_protocol_file(self, selections: List[CellSelection], 
                             output_path: str) -> bool
```

### 8. Well Plate Widget (`src/components/widgets/well_plate.py`) ✅ COMPLETE

**Responsibilities:**
- 96-well plate visual representation ✅
- Color-coded wells matching selection colors ✅
- Click-to-select well functionality ✅
- Export well plate map as image ✅

**Key Features:**
```python
class WellPlateWidget(QWidget):
    well_selected = Signal(str)  # Well position clicked
    
    def assign_well(self, well_position: str, selection_id: str, 
                   color: str, label: str) -> bool
    def clear_all_wells(self) -> None
    def export_as_image(self, file_path: str) -> bool
    def get_well_assignments(self) -> Dict[str, Dict[str, Any]]
```

### 9. Selection Panel (`src/components/widgets/selection_panel.py`) ✅ COMPLETE

**Responsibilities:**
- Complete selection management UI ✅
- Selection table with editable properties ✅
- Export controls and buttons ✅
- Real-time selection updates ✅

**Interface Features:**
```python
class SelectionPanel(QWidget):
    selection_deleted = Signal(str)  # Selection ID
    export_requested = Signal()
    
    def add_selection(self, selection_data: Dict[str, Any]) -> None
    def update_selection(self, selection_id: str, data: Dict[str, Any]) -> None
    def remove_selection(self, selection_id: str) -> None
    def load_selections(self, selections: List[Dict[str, Any]]) -> None
```

## Calibration System Design

### Two-Point Calibration Logic

The coordinate transformation system employs a robust two-point calibration approach:

1. **Reference Point Capture**
   - User clicks on identifiable features in the microscopy image
   - Corresponding real-world XY stage coordinates are manually entered
   - System stores pixel → stage coordinate pairs

2. **Affine Transformation Calculation**
   ```
   [stage_x]   [a  b  c] [pixel_x]
   [stage_y] = [d  e  f] [pixel_y]
   [   1   ]   [0  0  1] [   1   ]
   ```

3. **Transformation Application**
   - All cell bounding box coordinates are transformed
   - Real-time validation ensures accuracy
   - Error checking prevents invalid transformations

### Calibration Quality Assurance

- **Minimum Point Requirement**: Two calibration points mandatory
- **Distance Validation**: Points must be sufficiently separated
- **Transformation Testing**: Reverse transformation validation
- **User Feedback**: Visual indicators for calibration quality

## Export Protocol (.cxprotocol)

### File Format Specification

The .cxprotocol file follows an INI-style format with sections for image metadata and imaging layout:

```ini
[IMAGE]
FILE = "sample_tissue"
WIDTH = 2048
HEIGHT = 2048
FORMAT = "TIF"

[IMAGING_LAYOUT]
PositionOnly = 1
AfterBefore = "01"
Points = 4
P_1 = "24.5693; 11.0685; 24.6437; 11.1429;red;A01;"
P_2 = "24.6994; 11.1114; 24.7781; 11.1901;blue;B01;"
P_3 = "24.6722; 11.1880; 24.7142; 11.2300;green;C01;"
P_4 = "24.6104; 11.2206; 24.6404; 11.2506;yellow;D01;"
```

Each point entry (P_1, P_2, etc.) contains semicolon-separated values:
- **min_x**: Minimum X coordinate of crop region
- **min_y**: Minimum Y coordinate of crop region  
- **max_x**: Maximum X coordinate of crop region
- **max_y**: Maximum Y coordinate of crop region
- **color**: Selection color (red, blue, green, etc.)
- **well**: 96-well plate position (A01-H12)

### Export Validation

- **Coordinate Bounds Checking**: Ensure all coordinates are within valid ranges
- **File Integrity**: INI format structure validation
- **Hardware Compatibility**: .cxprotocol format verification for CosmoSort
- **Backup Generation**: Automatic backup file creation

## Design Principles

### 1. Modularity

- **Component Separation**: Clear boundaries between GUI, data processing, and export logic
- **Interface Contracts**: Well-defined APIs between components
- **Plugin Architecture**: Extensible design for future enhancements

### 2. Testability

- **Unit Testing**: Individual component validation
- **Integration Testing**: End-to-end workflow verification
- **Mock Data**: Synthetic datasets for testing edge cases
- **Performance Testing**: Large dataset handling validation

### 3. Real-time Feedback

- **Progressive Loading**: Incremental data loading with progress indicators
- **Responsive UI**: Non-blocking operations with worker threads
- **Visual Feedback**: Immediate response to user interactions
- **Error Handling**: Graceful degradation with informative messages

### 4. Performance Optimization

- **Memory Management**: Efficient handling of large images (TIFF/JPG/JPEG/PNG)
- **Lazy Loading**: On-demand data processing
- **Caching Strategy**: Intelligent caching of processed data
- **Vectorized Operations**: NumPy optimization for coordinate transformations

### 5. Extensibility

- **Configuration System**: User-customizable settings
- **Format Support**: Extensible file format handlers
- **Color Schemes**: Customizable color palettes
- **Export Formats**: Multiple output format support

## Error Handling and Validation

### Input Validation
- **File Format Verification**: Strict image format (TIFF/JPG/JPEG/PNG) and CSV format checking
- **Data Integrity**: Missing value detection and handling
- **Coordinate Validation**: Bounds checking for all coordinate operations

### User Error Prevention
- **Input Sanitization**: Automatic data cleaning and formatting
- **Confirmation Dialogs**: Critical operation confirmations
- **Undo/Redo**: State management for user corrections
- **Auto-save**: Periodic backup of work in progress

### System Recovery
- **Graceful Degradation**: Partial functionality during errors
- **Error Logging**: Comprehensive error tracking and reporting
- **Recovery Options**: Multiple recovery strategies for different failure modes

## Security Considerations

### Data Protection
- **Local Processing**: No network transmission of sensitive data
- **File Permissions**: Appropriate access controls
- **Temporary Files**: Secure cleanup of intermediate data

### Input Sanitization
- **CSV Injection Prevention**: Safe parsing of user-provided CSV data
- **Path Traversal Protection**: Secure file path handling
- **Resource Limits**: Memory and CPU usage constraints

## Development & Collaboration Notes
- 본 프로젝트는 별도의 CONTRIBUTING.md, RELEASE_PLAN.md 파일을 생성하지 않으며, 관련 규칙은 README.md 및 기타 문서에 통합되어 관리됩니다.

This architecture provides a robust, scalable foundation for the CellSorter application while maintaining the flexibility needed for research applications and future enhancements. 