# CellSorter Product Requirements Document

## Executive Summary

CellSorter is a specialized GUI-based software application designed to interface with the CosmoSort research instrument for precision cell sorting and tissue extraction from pathology slides. The software analyzes microscopy images and CellProfiler-generated data to enable researchers to select specific cell populations and generate extraction protocols for automated tissue harvesting.

## Product Vision

To provide researchers with an intuitive, powerful tool that bridges the gap between cellular image analysis and physical tissue extraction, enabling precise, reproducible cell sorting workflows for pathology research and diagnostics.

## Target Market

- **Primary**: Pathology research laboratories
- **Secondary**: Clinical diagnostics facilities
- **Tertiary**: Academic institutions with cell biology programs

## Functional Requirements

### FR1: Data Input and Loading

#### FR1.1: Image Loading
- **Requirement**: Load and display microscopy images in multiple formats
- **Acceptance Criteria**:
  - Support for TIFF, JPG, JPEG, and PNG image formats
  - Support for multi-channel TIFF files up to 2GB
  - Display images with pan and zoom functionality
  - Maintain image quality during zoom operations (1x to 100x magnification)
  - Load time < 5 seconds for images up to 500MB
- **Priority**: High

#### FR1.2: CSV Data Import
- **Requirement**: Parse and validate CellProfiler CSV exports
- **Acceptance Criteria**:
  - Automatically detect and validate required columns:
    - `AreaShape_BoundingBoxMaximum_X/Y`
    - `AreaShape_BoundingBoxMinimum_X/Y`
  - Support CSV files with up to 100,000 cell records
  - Display data validation errors with specific column references
  - Parse time < 3 seconds for 50,000 cell records
- **Priority**: High

#### FR1.3: File Format Validation
- **Requirement**: Validate input file formats and data integrity
- **Acceptance Criteria**:
  - Support TIFF, JPG, JPEG, and PNG image formats with appropriate validation
  - Validate CSV structure and required columns
  - Check for data completeness and consistency
  - Provide specific error descriptions for invalid data
- **Priority**: Medium

### FR2: Data Visualization and Analysis

#### FR2.1: Scatter Plot Generation
- **Requirement**: Create interactive scatter plots from CSV signal data
- **Acceptance Criteria**:
  - User selects any two numeric columns for X and Y axes
  - Plot renders within 2 seconds for 50,000 data points
  - Supports standard plot interactions (pan, zoom, reset)
  - Automatic axis scaling and labeling
  - Export plot as PNG/SVG format
- **Priority**: High

#### FR2.2: Cell Selection Interface
- **Requirement**: Enable rectangular region selection on scatter plots
- **Acceptance Criteria**:
  - Shift+drag creates rectangular selection tool
  - Visual feedback during selection process
  - Display count of selected cells in real-time
  - Support multiple independent selections
  - Ability to modify or delete existing selections
- **Priority**: High

#### FR2.3: Selection Management
- **Requirement**: Manage multiple cell selections with metadata
- **Acceptance Criteria**:
  - Assign unique colors to each selection (16 predefined colors minimum)
  - Add custom labels to selections
  - Display selection table with columns: checkbox, label, color, well, cell count
  - Edit selection properties after creation
  - Delete individual selections
- **Priority**: High

### FR3: Image Integration and Visualization

#### FR3.1: Cell Highlighting on Image
- **Requirement**: Display selected cells on the microscopy image
- **Acceptance Criteria**:
  - Overlay colored markers on image corresponding to selected cells
  - Real-time updates when selections change
  - Toggle overlay visibility
  - Maintain performance with up to 10,000 highlighted cells
  - Color consistency between scatter plot and image overlay
- **Priority**: High

#### FR3.2: Image Navigation
- **Requirement**: Provide intuitive image navigation tools
- **Acceptance Criteria**:
  - Pan and zoom functionality
  - Zoom levels from 10% to 1000%
  - Minimap for large image navigation
  - Coordinate display (pixel coordinates)
  - Fit-to-window and 1:1 zoom options
- **Priority**: Medium

### FR4: Coordinate Calibration System

#### FR4.1: Two-Point Calibration
- **Requirement**: Implement pixel-to-stage coordinate transformation
- **Acceptance Criteria**:
  - User clicks two reference points on the image
  - Manual entry of corresponding real-world XY stage coordinates
  - Automatic calculation of affine transformation matrix
  - Visual indicators for calibration points
  - Validation of calibration quality (minimum distance requirements)
- **Priority**: High

#### FR4.2: Coordinate Transformation
- **Requirement**: Convert pixel coordinates to stage coordinates
- **Acceptance Criteria**:
  - Transform all cell bounding boxes to stage coordinates
  - Maintain precision to 0.1 micrometer accuracy
  - Real-time coordinate display during image interaction
  - Reverse transformation capability for validation
- **Priority**: High

### FR5: Well Plate Management

#### FR5.1: 96-Well Plate Assignment
- **Requirement**: Assign selections to 96-well plate positions
- **Acceptance Criteria**:
  - Automatic assignment following standard layout (A01-H12)
  - Manual well assignment override capability
  - Visual well plate map display
  - Prevent duplicate well assignments
  - Well assignment validation and conflict resolution
- **Priority**: Medium

#### FR5.2: Well Plate Visualization
- **Requirement**: Display well plate layout and assignments
- **Acceptance Criteria**:
  - Standard 96-well plate visual representation
  - Color-coded wells matching selection colors
  - Click-to-select well functionality
  - Export well plate map as image
- **Priority**: Low

### FR6: Data Export and Protocol Generation

#### FR6.1: Protocol File Export
- **Requirement**: Generate .cxprotocol files for CosmoSort hardware
- **Acceptance Criteria**:
  - INI-style format with IMAGE and IMAGING_LAYOUT sections
  - Include all selection data, coordinates, and calibration information
  - File size optimization for large datasets
  - Export validation and integrity checking
  - Automatic backup generation
- **Priority**: High

#### FR6.2: Crop Region Calculation
- **Requirement**: Calculate square crop regions from cell bounding boxes
- **Acceptance Criteria**:
  - Select shorter dimension for square size
  - Center square on bounding box centroid
  - Ensure crops don't exceed image boundaries
  - Minimum crop size validation (10x10 pixels)
  - Export crop coordinates in both pixel and stage coordinate systems
- **Priority**: High

#### FR6.3: Data Export Options
- **Requirement**: Provide multiple export formats for analysis results
- **Acceptance Criteria**:
  - CSV export of selection data and coordinates
  - Image export with overlays
  - Configuration file export for session recovery
  - Batch export capabilities
- **Priority**: Medium

## Non-Functional Requirements

### NFR1: Performance Requirements

#### NFR1.1: Response Time
- Image loading: < 5 seconds for files up to 500MB
- CSV parsing: < 3 seconds for 50,000 records
- Scatter plot rendering: < 2 seconds for 50,000 points
- Selection highlighting: < 1 second for 1,000 cells
- Protocol export: < 10 seconds for complete workflow

#### NFR1.2: Memory Usage
- Maximum RAM usage: 4GB for typical workflows
- Efficient memory management for large images
- Garbage collection optimization
- Memory leak prevention

#### NFR1.3: File Size Limits
- Maximum image size: 2GB for all supported formats (TIFF/JPG/JPEG/PNG)
- Maximum CSV records: 100,000 cells
- Protocol file size: < 100MB for largest datasets

### NFR2: Platform Compatibility

#### NFR2.1: Operating System Support
- **Primary**: Windows 10 and Windows 11 (64-bit)
- **Secondary**: Future macOS support consideration
- No Linux support required for initial release

#### NFR2.2: Hardware Requirements
- **Minimum**: 8GB RAM, Intel i5 or equivalent, 1GB available storage
- **Recommended**: 16GB RAM, Intel i7 or equivalent, 5GB available storage
- Graphics card: DirectX 11 compatible
- Display: 1920x1080 minimum resolution

### NFR3: Reliability and Availability

#### NFR3.1: System Stability
- Zero data loss during normal operations
- Graceful handling of invalid input data
- Auto-save functionality for work in progress
- Session recovery after unexpected shutdowns

#### NFR3.2: Error Handling
- Comprehensive error logging
- User-friendly error messages
- Fallback options for recoverable errors
- Diagnostic information for support

### NFR4: Usability

#### NFR4.1: User Interface
- Intuitive GUI following Windows design guidelines
- Consistent visual design and interaction patterns
- Keyboard shortcuts for common operations
- Contextual help and tooltips

#### NFR4.2: Learning Curve
- New users productive within 30 minutes
- Comprehensive user documentation
- Built-in tutorial system
- Example datasets and workflows

### NFR5: Security and Data Protection

#### NFR5.1: Data Security
- All processing performed locally (no network transmission)
- Secure file handling and temporary file cleanup
- No collection of user data or analytics
- Compliance with research data protection requirements

#### NFR5.2: Access Control
- File system permission respect
- No administrative privileges required
- Secure handling of sensitive pathology data

### NFR6: Maintainability

#### NFR6.1: Code Quality
- Comprehensive unit test coverage (>80%)
- Modular architecture for easy updates
- Clear documentation for all components
- Version control and release management

#### NFR6.2: Updates and Support
- Automatic update notification system
- Backward compatibility for data files
- Clear versioning scheme
- Bug tracking and resolution process

## User Personas

### Primary Persona: Research Pathologist

**Background:**
- Dr. Sarah Chen, 35 years old
- 10+ years experience in pathology research
- Works with tissue samples for cancer research
- Collaborates with interdisciplinary research teams

**Goals:**
- Identify specific cell populations in tissue samples
- Extract precise tissue regions for further analysis
- Maintain reproducible research protocols
- Publish high-quality research with reliable data

**Pain Points:**
- Manual cell selection is time-consuming and inconsistent
- Existing tools lack integration with extraction hardware
- Difficulty in maintaining consistent selection criteria across samples
- Need for precise coordinate mapping for downstream applications

**Technology Proficiency:** Intermediate
**Usage Pattern:** Daily use, 2-4 hours per session

### Secondary Persona: Laboratory Technician

**Background:**
- Michael Rodriguez, 28 years old
- 5 years experience in research laboratory
- Operates various laboratory instruments
- Follows established protocols with high precision

**Goals:**
- Execute researcher-defined protocols accurately
- Process multiple samples efficiently
- Maintain quality control standards
- Document all procedures properly

**Pain Points:**
- Complex software interfaces slow down workflow
- Need for consistent results across different operators
- Requirement for detailed documentation and traceability
- Integration challenges between different laboratory systems

**Technology Proficiency:** Intermediate
**Usage Pattern:** Daily use, 4-6 hours per session

### Tertiary Persona: Graduate Student

**Background:**
- Lisa Park, 24 years old
- PhD student in Cell Biology
- Limited experience with specialized software
- Learning research methodologies

**Goals:**
- Learn proper cell analysis techniques
- Generate data for thesis research
- Understand relationship between image analysis and physical extraction
- Develop expertise in quantitative cell biology

**Pain Points:**
- Steep learning curve for specialized software
- Need for guidance and validation of analysis decisions
- Time pressure to complete research projects
- Limited access to expert consultation

**Technology Proficiency:** Beginner to Intermediate
**Usage Pattern:** 2-3 times per week, 1-3 hours per session

## Use Case Scenarios

### Scenario 1: Cancer Cell Population Analysis

**Context:** Dr. Chen is analyzing a colon cancer tissue sample to identify and extract specific cell populations based on protein markers.

**Workflow:**
1. Load H&E stained tissue slide image (2048x2048 pixels, 200MB TIFF)
2. Import CellProfiler CSV containing signal intensities for CK7, CK20, and CDX2 markers
3. Create scatter plot with CK7 on X-axis and CK20 on Y-axis
4. Identify distinct cell populations through visual clustering
5. Select rectangular regions containing cells of interest using shift+drag
6. Assign descriptive labels ("Adenocarcinoma_CK7pos", "Normal_Epithelium") and colors
7. Calibrate coordinate system using two fiducial markers
8. Review cell selections on original image to verify accuracy
9. Export .cxprotocol file for automated extraction using CosmoSort

**Expected Outcome:** Precise extraction coordinates for 150-300 cells per population, enabling downstream single-cell analysis.

**Success Metrics:**
- Selection time: < 10 minutes for complete workflow
- Coordinate accuracy: ±2 micrometers
- Extraction success rate: >95% for selected regions

### Scenario 2: Rare Cell Detection and Extraction

**Context:** Graduate student Lisa is studying circulating tumor cells (CTCs) in blood samples for her thesis research.

**Workflow:**
1. Load brightfield microscopy image of blood smear (4096x4096 pixels)
2. Import CellProfiler CSV with morphological features (area, eccentricity, intensity)
3. Plot cell area vs. nuclear intensity to identify outliers
4. Select small regions containing suspected CTCs (5-10 cells per selection)
5. Assign colors and sequential labels ("CTC_candidate_01", "CTC_candidate_02")
6. Use image overlay to confirm morphological characteristics
7. Perform two-point calibration using known reference objects
8. Generate extraction protocol with high-precision coordinates
9. Document selection criteria and export analysis summary

**Expected Outcome:** Identification and extraction of 10-20 rare cells from 10,000+ total cells analyzed.

**Success Metrics:**
- Detection sensitivity: Identify >90% of manually verified CTCs
- False positive rate: <5%
- Protocol generation time: < 15 minutes

### Scenario 3: Multi-Sample Comparative Study

**Context:** Laboratory technician Michael is processing a batch of 20 samples for a comparative drug efficacy study.

**Workflow:**
1. Load standardized tissue array image (2x2 cm, 500MB TIFF)
2. Import batch-processed CellProfiler CSV (50,000+ cells)
3. Apply consistent selection criteria across all samples:
   - Control cells: Low marker A, Low marker B
   - Drug-treated cells: High marker A, Variable marker B
   - Resistant cells: Low marker A, High marker B
4. Use pre-defined color scheme and labeling convention
5. Apply saved calibration parameters from reference sample
6. Generate 96-well plate assignments for systematic extraction
7. Export protocol files with standardized naming convention
8. Validate all selections meet quality control criteria

**Expected Outcome:** Consistent cell population extraction across all samples with standardized protocols for downstream analysis.

**Success Metrics:**
- Processing time: < 30 minutes per sample
- Inter-sample consistency: <10% variation in selection criteria
- Protocol validation: 100% success rate in coordinate transformation

### Scenario 4: Quality Control and Method Validation

**Context:** Dr. Chen is validating the accuracy and reproducibility of the CellSorter workflow for a new research protocol.

**Workflow:**
1. Load reference tissue sample with known cell populations
2. Perform independent selections by three different operators
3. Compare selection consistency across operators:
   - Overlap analysis of selected cell populations
   - Coordinate accuracy assessment
   - Protocol file validation
4. Test calibration accuracy using known distance measurements
5. Verify extraction success rate using post-extraction imaging
6. Document any systematic biases or operator-dependent variations
7. Refine selection criteria and update standard operating procedures

**Expected Outcome:** Validated workflow with documented accuracy metrics and operator training materials.

**Success Metrics:**
- Inter-operator agreement: >85% overlap in cell selections
- Calibration accuracy: <1% error in distance measurements
- Extraction success: >98% successful cell recovery

## Sample Data References

### Input Data Specifications

#### Microscopy Images (`docs/examples/sample_images/`)
- **Format**: TIFF (uncompressed or LZW compression)
- **Bit Depth**: 8-bit or 16-bit per channel
- **Channels**: 1-4 channels (brightfield, fluorescence, or combinations)
- **Resolution**: 0.1-10 micrometers per pixel
- **Size Range**: 512x512 to 8192x8192 pixels

**Example Files:**
- `colon_cancer_he.tiff` - H&E stained colon cancer tissue (2048x2048, 8-bit RGB)
- `breast_tissue_ihc.tiff` - IHC stained breast tissue (4096x4096, 8-bit grayscale)
- `blood_smear_bf.tiff` - Brightfield blood smear (3072x3072, 8-bit grayscale)

#### CellProfiler CSV Data (`docs/examples/sample_data/`)
- **Required Columns**: Bounding box coordinates (4 columns)
- **Optional Columns**: Any numeric feature measurements
- **Typical Features**: Area, perimeter, intensity measurements, shape descriptors
- **Record Count**: 100-100,000 cells per file

**Example Files:**
- `colon_cancer_cellprofiler_output.csv` - 15,000 cells with CK7/CK20/CDX2 measurements
- `breast_tissue_analysis.csv` - 25,000 cells with ER/PR/HER2 measurements  
- `blood_cells_morphology.csv` - 50,000 cells with size and shape features

#### Protocol Files (`docs/examples/protocols/`)
- **Format**: INI-style format (.cxprotocol extension)
- **Content**: Complete workflow metadata and extraction coordinates
- **Validation**: Format-validated structure for hardware compatibility

**Example Files:**
- `cancer_cell_extraction.cxprotocol` - 200 selected cancer cells with metadata
- `rare_cell_protocol.cxprotocol` - 15 rare cells with high-precision coordinates
- `batch_analysis_results.cxprotocol` - Multi-sample extraction protocol

### Data Quality Standards

#### Image Quality Requirements
- **Signal-to-noise ratio**: Minimum 10:1 for feature detection
- **Focus quality**: Sharp cellular boundaries required
- **Illumination**: Even illumination across field of view
- **Artifacts**: Minimal dust, debris, or imaging artifacts

#### CSV Data Quality
- **Completeness**: <5% missing values in required columns
- **Accuracy**: Bounding box coordinates within image bounds
- **Consistency**: Consistent measurement units across features
- **Validation**: Automated quality checks during import

#### Protocol Validation
- **Coordinate bounds**: All coordinates within valid stage range
- **File integrity**: INI format structure validation
- **Hardware compatibility**: .cxprotocol format verification for CosmoSort
- **Metadata completeness**: All required fields populated

## Acceptance Criteria Summary

### Critical Success Factors
1. **Data Integration**: Seamless loading and processing of multiple image formats (TIFF/JPG/JPEG/PNG) and CellProfiler CSV data
2. **User Interaction**: Intuitive scatter plot selection and image visualization
3. **Coordinate Accuracy**: Precise pixel-to-stage transformation with <1% error
4. **Protocol Generation**: Valid .cxprotocol files compatible with CosmoSort hardware
5. **Performance**: Responsive interface handling up to 50,000 cells in <2 seconds

### Quality Metrics
- **Reliability**: 99.9% uptime during normal operations
- **Accuracy**: <1 micrometer coordinate transformation error
- **Usability**: 90% of new users productive within 30 minutes
- **Performance**: All operations complete within specified time limits
- **Compatibility**: 100% success rate with CosmoSort hardware integration

### Validation Requirements
- Comprehensive testing with representative datasets
- User acceptance testing with target personas
- Hardware integration testing with CosmoSort
- Performance testing under maximum load conditions
- Security audit for data handling procedures

This product requirements document provides the foundation for developing CellSorter as a robust, user-friendly tool that meets the specific needs of pathology researchers while maintaining the precision required for automated cell sorting applications. 

## Development & Documentation Notes
- 개발/테스트 의존성은 requirements-dev.txt, 빌드/배포 의존성은 requirements-build.txt에 분리 관리합니다.
- 본 프로젝트는 별도의 CONTRIBUTING.md, RELEASE_PLAN.md 파일을 생성하지 않으며, 관련 규칙은 README.md 및 기타 문서에 통합되어 관리됩니다. 