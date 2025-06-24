# CellSorter Design Specification

## Overview

CellSorter follows a modern, accessible design philosophy inspired by Material Design principles and shadcn/ui aesthetics. The interface prioritizes clarity, efficiency, and user-centered workflows for pathology research applications.

## Design Philosophy

### Core Principles

1. **Clarity First**: Every UI element has a clear purpose and intuitive meaning
2. **Accessibility**: WCAG 2.1 AA compliance with high contrast and keyboard navigation
3. **Consistency**: Unified design language across all components and interactions
4. **Efficiency**: Streamlined workflows that minimize cognitive load
5. **Flexibility**: Adaptable interface supporting various screen sizes and use cases

### Visual Hierarchy

- **Primary Actions**: Elevated surfaces with high contrast
- **Secondary Actions**: Subtle styling with clear affordances  
- **Content Areas**: Clean backgrounds with proper spacing
- **Navigation**: Persistent and contextual navigation patterns

## Application Layout

### Main Window Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Title Bar                                    [─] [□] [×]     │
├─────────────────────────────────────────────────────────────┤
│ Menu Bar: File | Edit | View | Tools | Analysis | Help     │
├─────────────────────────────────────────────────────────────┤
│ Toolbar: [📁] [💾] [🔍] [⚙️] [▶️] | Theme Toggle [🌙/☀️]   │
├─────────────────────────────────────────────────────────────┤
│ Main Content Area                                           │
│ ┌─────────────────┬─────────────────┬─────────────────────┐ │
│ │                 │                 │                     │ │
│ │   Image Panel   │  Scatter Plot   │   Selection Panel   │ │
│ │                 │     Panel       │                     │ │
│ │                 │                 │                     │ │
│ └─────────────────┴─────────────────┴─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Status Bar: Ready | 15,234 cells loaded | Zoom: 100%       │
└─────────────────────────────────────────────────────────────┘
```

### Responsive Layout Breakpoints

- **Large Desktop**: ≥1920px - Three-column layout with full panels
- **Desktop**: 1200px-1919px - Three-column layout with collapsible panels
- **Tablet**: 768px-1199px - Two-column layout with tabbed panels
- **Mobile**: <768px - Single-column stack with full-screen modals

## Panel Specifications

### Image Panel (Left - 40% width)

**Purpose**: Display microscopy images with cell overlays and navigation controls

**Layout**:
```
┌─────────────────────────────────────┐
│ ┌─ Image Controls ─────────────────┐ │
│ │ 📁 Load  🔍 Zoom  📏 Measure   │ │
│ │ Zoom: [25%] [50%] [100%] [200%] │ │
│ │ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Image Display ─────────────────┐ │
│ │                                 │ │
│ │     [Microscopy Image]          │ │
│ │                                 │ │
│ │  • Cell overlays               │ │
│ │  • Selection highlights        │ │
│ │  • Calibration points          │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Image Info ────────────────────┐ │
│ │ Dimensions: 2048 × 2048 px      │ │
│ │ Scale: 0.5 μm/pixel            │ │
│ │ Cursor: (1024, 512)            │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Interactions**:
- **Pan**: Click and drag to navigate
- **Zoom**: Mouse wheel or zoom controls
- **Calibration**: Ctrl+Click to set reference points
- **Overlay Toggle**: Toggle cell highlighting visibility

### Scatter Plot Panel (Center - 35% width)

**Purpose**: Interactive data visualization for cell selection

**Layout**:
```
┌─────────────────────────────────────┐
│ ┌─ Plot Controls ─────────────────┐ │
│ │ X-Axis: [CK7_Intensity    ▼]   │ │
│ │ Y-Axis: [CK20_Intensity   ▼]   │ │
│ │ [🎨 Color Mode] [📊 Stats]     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Scatter Plot ──────────────────┐ │
│ │ ↑                               │ │
│ │ │     • • •                     │ │
│ │ │   •  ○  •                     │ │
│ │ │  •   ○○  •                    │ │
│ │ │    •  ○•                      │ │
│ │ │     • •                       │ │
│ │ └─────────────────────────→     │ │
│ │                                 │ │
│ │ Selection: 147 cells            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Selection Tools ───────────────┐ │
│ │ [🔲 Rectangle] [🟡 Lasso]      │ │
│ │ [⭐ Clear] [🎯 Zoom to Fit]     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Interactions**:
- **Rectangle Selection**: Shift+Drag to select cells
- **Lasso Selection**: Alt+Drag for freeform selection
- **Zoom**: Mouse wheel with modifier keys
- **Pan**: Middle-click drag or arrow keys

### Selection Panel (Right - 25% width)

**Purpose**: Manage cell selections and export protocols

**Layout**:
```
┌─────────────────────────────────────┐
│ ┌─ Active Selections ─────────────┐ │
│ │ ☐ Selection 1                   │ │
│ │   🔴 Cancer Cells (145 cells)   │ │
│ │   Well: A01                     │ │
│ │                                 │ │
│ │ ☐ Selection 2                   │ │
│ │   🔵 Normal Tissue (89 cells)   │ │
│ │   Well: B01                     │ │
│ │                                 │ │
│ │ ☐ Selection 3                   │ │
│ │   🟢 Stroma (67 cells)          │ │
│ │   Well: C01                     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Selection Properties ──────────┐ │
│ │ Label: [Cancer Cells        ]   │ │
│ │ Color: [🔴 Red          ▼]     │ │
│ │ Well:  [A01             ▼]     │ │
│ │ [✏️ Edit] [🗑️ Delete]          │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Export Options ────────────────┐ │
│ │ Protocol Name:                  │ │
│ │ [cancer_analysis_001        ]   │ │
│ │                                 │ │
│ │ [📤 Export Protocol]            │ │
│ │ [💾 Save Session]               │ │
│ │ [📋 Copy Coordinates]           │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Workflow States

### 1. Initial State (Empty)

**Visual Characteristics**:
- Clean, minimal interface with prominent "Load Data" actions
- Subtle onboarding hints and shortcuts
- Disabled controls with helpful tooltips

**User Actions**:
- Load microscopy image
- Load CellProfiler CSV data
- Access help documentation

### 2. Data Loaded State

**Visual Characteristics**:
- Image displayed in left panel
- Scatter plot generated automatically
- All controls enabled and interactive

**User Actions**:
- Configure scatter plot axes
- Navigate and zoom image
- Begin cell selection workflow

### 3. Selection Active State

**Visual Characteristics**:
- Active selection rectangle overlay
- Real-time cell count updates
- Preview of selected cells on image

**User Actions**:
- Complete selection by releasing mouse
- Assign labels and colors
- Continue with additional selections

### 4. Calibration Mode

**Visual Characteristics**:
- Special cursor for calibration points
- Overlay indicators for reference points
- Coordinate input dialogs

**User Actions**:
- Click reference points on image
- Enter real-world coordinates
- Validate calibration accuracy

### 5. Export Ready State

**Visual Characteristics**:
- Export controls enabled
- Protocol summary displayed
- Success indicators and confirmations

**User Actions**:
- Generate .cxprotocol file
- Save current session
- Review export summary

## Component Interactions

### Modal Dialogs

**File Loading Dialog**:
```
┌─────────────────────────────────────┐
│ Load Microscopy Image               │
├─────────────────────────────────────┤
│                                     │
│ ┌─ File Browser ─────────────────┐  │
│ │ 📁 Recent Files                │  │
│ │ • sample_tissue.tiff           │  │
│ │ • breast_sample.jpg            │  │
│ │ • colon_biopsy.png             │  │
│ │                                │  │
│ │ [📁 Browse Files...]           │  │
│ └───────────────────────────────┘  │
│                                     │
│ ┌─ Preview ──────────────────────┐  │
│ │ [Image thumbnail]              │  │
│ │ Format: TIFF                   │  │
│ │ Size: 2048 × 2048 px           │  │
│ │ File size: 24.5 MB             │  │
│ └───────────────────────────────┘  │
│                                     │
│          [Cancel] [Load Image]      │
└─────────────────────────────────────┘
```

**Calibration Point Dialog**:
```
┌─────────────────────────────────────┐
│ Set Calibration Point               │
├─────────────────────────────────────┤
│                                     │
│ Pixel Coordinates:                  │
│ X: [1024        ] px                │
│ Y: [512         ] px                │
│                                     │
│ Real-World Coordinates:             │
│ X: [25.6        ] μm                │
│ Y: [12.3        ] μm                │
│                                     │
│ Reference: First calibration point  │
│                                     │
│          [Cancel] [Set Point]       │
└─────────────────────────────────────┘
```

### Context Menus

**Image Right-Click Menu**:
- Set Calibration Point
- Zoom to Selection
- Export View
- ---
- Copy Coordinates
- Measure Distance

**Selection Right-Click Menu**:
- Edit Properties
- Duplicate Selection
- Delete Selection
- ---
- Zoom to Selection
- Export Coordinates

## Theming System

### Theme Structure

**Light Theme (Default)**:
- Background: `hsl(0 0% 100%)`
- Foreground: `hsl(222.2 84% 4.9%)`
- Primary: `hsl(222.2 47.4% 11.2%)`
- Secondary: `hsl(210 40% 96%)`

**Dark Theme**:
- Background: `hsl(222.2 84% 4.9%)`
- Foreground: `hsl(210 40% 98%)`
- Primary: `hsl(217.2 32.6% 17.5%)`
- Secondary: `hsl(217.2 32.6% 17.5%)`

**Material Theme (qt-material integration)**:
- Uses qt-material color schemes
- Supports all qt-material themes
- Seamless theme switching

### Theme Toggle

**Location**: Top-right toolbar
**Behavior**: 
- Single click switches between light/dark
- Dropdown for material theme selection
- Persists user preference

## Accessibility Features

### Keyboard Navigation

**Global Shortcuts**:
- `Ctrl+O`: Open image file
- `Ctrl+Shift+O`: Open CSV file
- `Ctrl+S`: Save session
- `Ctrl+E`: Export protocol
- `Ctrl+Z`: Undo last action
- `Ctrl+Y`: Redo action
- `F11`: Toggle fullscreen
- `Tab`: Navigate between panels

**Panel-Specific**:
- Arrow keys: Navigate image/plot
- `+/-`: Zoom in/out
- `Space`: Pan mode toggle
- `Shift+Click`: Selection mode
- `Escape`: Cancel current action

### Screen Reader Support

- Semantic HTML structure
- ARIA labels for all interactive elements
- Live regions for status updates
- Descriptive alt text for data visualizations

### High Contrast Mode

- Increased border weights
- Enhanced focus indicators
- Alternative color schemes
- Larger click targets

## Responsive Behavior

### Panel Collapsing

**Desktop → Tablet**:
- Selection panel moves to bottom tabs
- Image and plot panels stack vertically
- Toolbar remains horizontal

**Tablet → Mobile**:
- Single panel view with navigation tabs
- Full-screen modal dialogs
- Touch-optimized controls

### Content Scaling

- Text scales with system font size
- Icons use SVG for crisp scaling
- Layout maintains proportions
- Minimum touch target: 44px

## Error States and Feedback

### Loading States

**Image Loading**:
```
┌─────────────────────────────────────┐
│ ┌─ Loading Image ─────────────────┐ │
│ │                                 │ │
│ │    [Loading Spinner]            │ │
│ │                                 │ │
│ │ Loading sample_tissue.tiff...   │ │
│ │ 45% complete                    │ │
│ │                                 │ │
│ │ [████████░░] 24.5 MB / 54.2 MB  │ │
│ │                                 │ │
│ │           [Cancel]              │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Error States

**File Format Error**:
```
┌─────────────────────────────────────┐
│ ⚠️ Unsupported File Format           │
├─────────────────────────────────────┤
│                                     │
│ The selected file cannot be opened: │
│ "data.xlsx"                         │
│                                     │
│ Supported formats:                  │
│ • TIFF (.tiff, .tif)               │
│ • JPEG (.jpg, .jpeg)               │
│ • PNG (.png)                        │
│                                     │
│ Would you like to select a          │
│ different file?                     │
│                                     │
│    [Select Different] [Cancel]      │
└─────────────────────────────────────┘
```

### Success Feedback

**Export Complete**:
```
┌─────────────────────────────────────┐
│ ✅ Protocol Export Successful        │
├─────────────────────────────────────┤
│                                     │
│ Protocol saved successfully:        │
│ "cancer_analysis_001.cxprotocol"   │
│                                     │
│ • 3 selections exported            │
│ • 301 total cells processed        │
│ • Calibration validated             │
│                                     │
│ [📁 Open Folder] [📋 Copy Path] [OK] │
└─────────────────────────────────────┘
```

## Animation and Transitions

### Micro-Interactions

- **Button Hover**: 150ms ease-out scale and color transition
- **Panel Resize**: 300ms ease-in-out width/height animation
- **Selection Feedback**: 100ms pulse animation on selection
- **Theme Switch**: 200ms cross-fade transition

### Loading Animations

- **Skeleton Loading**: Shimmer effect for data tables
- **Progress Indicators**: Smooth progress bar animations
- **Spinner**: Subtle rotation for background tasks

### Focus Management

- **Focus Rings**: 2px solid outline with 2px offset
- **Focus Trap**: Modal dialogs trap focus within
- **Focus Restoration**: Return focus after modal close

This design specification ensures CellSorter provides a modern, accessible, and efficient user experience that scales across different devices and user needs while maintaining the sophisticated functionality required for pathology research workflows. 