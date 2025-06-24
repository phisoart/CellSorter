# User Scenarios

## Scenario 1: Cell Feature-Based Region Selection and Extraction (Expert User)

**User Profile**: Experienced pathology researcher with extensive CosmoSort device experience

**Goal**: Select regions of interest from pathology slides based on specific single-cell characteristics and generate coordinate files (.cxprotocol) compatible with CosmoSort equipment for physical cell separation.

**Context**:
- User has slide images in TIFF format
- Single-cell signal data extracted from slides available as CSV files from CellProfiler
- Analysis targets cell populations distinguished by combination of CK7n and CDX2 markers

**Workflow**:

1. Launch CellSorter and load image file and CSV file respectively
2. Select 'CK7n' and 'CDX2' from the CSV feature list within the program
3. X-Y scatter plot is displayed in the center of the screen based on selected features
4. User holds Shift key and drags mouse to select regions of interest
5. Cells corresponding to selected points are highlighted with colors on the image and simultaneously added as individual items to the right-side list
6. User clicks two reference points on the image and inputs their actual X, Y coordinates on the CosmoSort device
7. System performs 2-point calibration based on these points to convert image coordinate system to actual device coordinate system
8. After reviewing automatically assigned colors and labels in the list (or modifying if necessary), user clicks Extract button
9. Selected information is saved as .cxprotocol file, and image regions containing each cell are also extracted and saved together

**Expected Result**:
The generated .cxprotocol file is compatible with CosmoSort device loading and execution, enabling physical extraction of cells selected from the image.

## Scenario 2: Quick Protocol Generation Using Existing Template (Novice User)

**User Profile**: Junior research assistant familiar with CellProfiler, limited CosmoSort experience

**Goal**: Perform repetitive protocol generation quickly and accurately according to analysis criteria (template) provided by the team.

**Context**:
- Analysis criteria are predefined
- User receives image and CSV files and must process them consistently according to established criteria

**Workflow**:

1. Launch CellSorter, and feature combinations and reference point settings from previous session are automatically loaded
2. When new image and CSV files are loaded, dot plot is automatically generated based on previous settings
3. User does not manually select regions of interest; template-based regions are automatically applied or saved ROI is loaded
4. System automatically loads previously input coordinates for 2 reference points and uses them unless specifically changed
5. List is auto-generated, and user clicks Extract button immediately without additional review
6. .cxprotocol file is saved to designated folder along with necessary image fragments

**Expected Result**:
CosmoSort device protocols can be generated quickly with consistent criteria without manual work, minimizing error occurrence.

## Scenario 3: Coordinate Mapping Failure Handling (Exception Flow)

**User Profile**: Experienced user who accidentally set incorrect reference points

**Goal**: When coordinate calibration errors occur, receive appropriate feedback and perform correct calibration to continue work.

**Context**:
The two reference points clicked by the user are too close together, significantly reducing coordinate transformation precision.

**Workflow**:

1. User clicks two reference points on the image and inputs hardware coordinates for each
2. System calculates distance between these two points and outputs error message if below threshold
3. Alert popup displays "Calibration points too close. Please choose wider distance."
4. User follows guidance to re-specify two reference points at more distant locations and inputs coordinates
5. When calibration completes successfully, system recalculates region coordinates based on this and updates the list

**Expected Result**:
User clearly understands the failure cause and can quickly correct it, allowing the overall workflow to continue without interruption.

## Scenario 4: 96-Well Plate Organization and Management (Expert User)

**User Profile**: Senior researcher processing multiple cell populations for downstream analysis

**Goal**: Organize multiple cell selections into a 96-well plate layout for systematic sample management and automated liquid handling integration.

**Context**:
- User has identified 5-10 distinct cell populations from a complex tissue sample
- Each population requires assignment to specific well positions for downstream processing
- Integration with laboratory automation systems requires standardized well plate organization

**Workflow**:

1. Complete basic cell selection workflow (Scenario 1) resulting in multiple colored selections
2. Navigate to the 96-Well Plate Management panel in the Selection section
3. Review automatically assigned well positions (A01, B01, C01, etc.) for each selection
4. Manually reassign specific selections to preferred well positions by:
   - Clicking on a selection in the list
   - Clicking on desired target well in the 96-well plate visualization
   - Confirming the assignment change
5. Add custom labels and metadata for each well assignment:
   - Cell type classification
   - Expected cell count
   - Processing priority
6. Validate well plate layout through visual inspection:
   - Check for proper spatial distribution
   - Ensure no well conflicts or duplications
   - Verify all selections have assigned positions
7. Export enhanced .cxprotocol file containing:
   - Standard coordinate information
   - Well plate mapping data
   - Metadata for each assigned well

**Expected Result**:
Generated .cxprotocol file includes comprehensive well plate organization data, enabling seamless integration with laboratory automation systems and standardized sample tracking.

## Scenario 5: Batch Processing with Well Plate Consistency (Advanced User)

**User Profile**: Laboratory technician processing multiple slides with identical analysis requirements

**Goal**: Process a series of tissue samples using consistent cell selection criteria while maintaining organized well plate assignments across multiple protocol files.

**Context**:
- Daily processing of 10-15 similar tissue samples
- Requirement to maintain consistent well assignments for specific cell types
- Need for systematic sample tracking across multiple extraction runs

**Workflow**:

1. Load first sample and complete standard analysis workflow
2. Define well plate template with standardized assignments:
   - Cancer cells → Wells A01-A06
   - Normal epithelium → Wells B01-B06
   - Stroma → Wells C01-C06
   - Immune infiltrate → Wells D01-D06
3. Save analysis template including:
   - Feature selection criteria
   - Selection thresholds
   - Well assignment rules
4. For subsequent samples:
   - Load new image and CSV data
   - Apply saved template settings
   - Review auto-generated selections for quality
   - Adjust well assignments if sample has different cell counts
   - Export .cxprotocol with sample-specific naming
5. Maintain batch tracking log:
   - Sample ID mapping to well positions
   - Processing timestamp and quality metrics
   - Cross-reference with original slide identifiers

**Expected Result**:
Consistent, high-throughput sample processing with standardized well plate organization enables efficient laboratory workflow management and reliable downstream analysis.

## Scenario 6: Well Plate Visualization and Quality Control (Quality Assurance)

**User Profile**: Laboratory supervisor reviewing extraction protocols before CosmoSort execution

**Goal**: Validate well plate assignments and cell distribution before committing to physical sample extraction.

**Context**:
- Multiple researchers generate protocols requiring supervisory review
- CosmoSort extraction is irreversible and expensive
- Need to ensure optimal cell distribution and prevent processing errors

**Workflow**:

1. Open completed .cxprotocol file in CellSorter for review
2. Examine well plate visualization for:
   - Even distribution of samples across available wells
   - Appropriate cell count per well (not too sparse or crowded)
   - Logical grouping of similar cell types
3. Review selection quality indicators:
   - Cell count statistics for each selection
   - Coordinate transformation accuracy metrics
   - Image quality assessments
4. Validate metadata completeness:
   - All wells have proper labels and descriptions
   - Sample tracking information is accurate
   - Processing parameters are documented
5. If issues are identified:
   - Flag specific selections for revision
   - Provide feedback to original analyst
   - Request reprocessing with corrected parameters
6. Approve protocol for CosmoSort execution with digital signature

**Expected Result**:
Quality-assured protocols minimize extraction failures and ensure optimal use of CosmoSort hardware resources while maintaining high scientific standards.