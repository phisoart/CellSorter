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