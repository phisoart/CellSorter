"""
CellSorter Selection Manager

Multi-selection management system with color coding, labeling,
and 96-well plate coordinate mapping.
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
from PySide6.QtCore import QObject, Signal

from utils.error_handler import error_handler
from utils.logging_config import LoggerMixin


class SelectionStatus(Enum):
    """Selection status enumeration."""
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPORTED = "exported"


@dataclass
class CellSelection:
    """Cell selection data structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    color: str = "#FF0000"  # Default red
    well_position: str = ""
    cell_indices: List[int] = field(default_factory=list)
    status: SelectionStatus = SelectionStatus.ACTIVE
    created_timestamp: float = field(default_factory=lambda: __import__('time').time())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.label:
            self.label = f"Selection_{self.id[:8]}"
    
    @property
    def cell_count(self) -> int:
        """Get number of cells in selection."""
        return len(self.cell_indices)
    
    def contains_cell(self, cell_index: int) -> bool:
        """Check if selection contains a specific cell."""
        return cell_index in self.cell_indices
    
    def add_cells(self, indices: List[int]) -> None:
        """Add cell indices to selection."""
        new_indices = set(self.cell_indices) | set(indices)
        self.cell_indices = list(new_indices)
    
    def remove_cells(self, indices: List[int]) -> None:
        """Remove cell indices from selection."""
        remaining_indices = set(self.cell_indices) - set(indices)
        self.cell_indices = list(remaining_indices)


class SelectionManager(QObject, LoggerMixin):
    """
    Multi-selection management system for cell populations.
    
    Features:
    - Color-coded cell selections
    - Automatic well plate assignment
    - Selection labeling and metadata
    - Conflict detection and resolution
    - Export preparation
    """
    
    # Color palette for selections (16 distinct colors)
    COLOR_PALETTE = [
        "#FF0000",  # Red
        "#00FF00",  # Green
        "#0000FF",  # Blue
        "#FFFF00",  # Yellow
        "#FF00FF",  # Magenta
        "#00FFFF",  # Cyan
        "#C0C0C0",  # LightGray
        "#800000",  # DarkRed
        "#008000",  # DarkGreen
        "#000080",  # DarkBlue
        "#808000",  # DarkYellow
        "#800080",  # DarkMagenta
        "#008080",  # DarkCyan
        "#808080",  # DarkGray
        "#FFFFFF",  # White
        "#000000",  # Black
    ]
    
    # 96-well plate layout (standard 8x12 format)
    WELL_LAYOUT = [
        f"{row}{col:02d}" 
        for col in range(1, 13)  # Columns 1-12
        for row in "ABCDEFGH"      # Rows A-H
    ]
    
    # Signals
    selection_added = Signal(str)  # selection_id
    selection_removed = Signal(str)  # selection_id
    selection_updated = Signal(str)  # selection_id
    selections_cleared = Signal()
    well_assignment_changed = Signal(str, str)  # selection_id, well_position
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # Data storage
        self.selections: Dict[str, CellSelection] = {}
        self.used_colors: Set[str] = set()
        self.used_wells: Set[str] = set()
        self.color_index = 0
        self.well_index = 0
        
        # Configuration
        self.max_selections = 96  # Maximum selections (one per well)
        self.auto_assign_wells = True
        self.auto_generate_labels = True
        
        self.log_info("Selection manager initialized")
    
    @error_handler("Adding cell selection")
    def add_selection(self, cell_indices: List[int], label: str = "", 
                     color: str = "", well_position: str = "") -> Optional[str]:
        """
        Add a new cell selection.
        
        Args:
            cell_indices: List of cell indices to select
            label: Optional custom label
            color: Optional custom color (hex format)
            well_position: Optional custom well position
        
        Returns:
            Selection ID if successful, None otherwise
        """
        if not cell_indices:
            self.log_warning("Cannot create selection with no cells")
            return None
        
        if len(self.selections) >= self.max_selections:
            self.log_warning(f"Maximum selections reached: {self.max_selections}")
            return None
        
        # Check for cell conflicts
        conflicts = self._check_cell_conflicts(cell_indices)
        if conflicts:
            self.log_warning(f"Cell indices conflict with existing selections: {conflicts}")
            # Could implement conflict resolution here
        
        # Create selection
        selection = CellSelection(
            cell_indices=list(set(cell_indices)),  # Remove duplicates
            label=label,
            color=color,
            well_position=well_position
        )
        
        # Auto-assign color if not provided
        if not selection.color or selection.color in self.used_colors:
            selection.color = self._get_next_color()
        
        # Auto-assign well if enabled and not provided
        if self.auto_assign_wells and not selection.well_position:
            selection.well_position = self._get_next_well()
        
        # Auto-generate label if not provided
        if self.auto_generate_labels and not selection.label:
            selection.label = f"Selection_{len(self.selections) + 1}"
        
        # Validate well assignment
        if selection.well_position and selection.well_position in self.used_wells:
            self.log_warning(f"Well {selection.well_position} already used, auto-assigning new well")
            selection.well_position = self._get_next_well()
        
        # Store selection
        self.selections[selection.id] = selection
        self.used_colors.add(selection.color)
        if selection.well_position:
            self.used_wells.add(selection.well_position)
        
        # Emit signal
        self.selection_added.emit(selection.id)
        
        self.log_info(f"Added selection '{selection.label}' with {selection.cell_count} cells "
                     f"(color: {selection.color}, well: {selection.well_position})")
        
        return selection.id
    
    def _check_cell_conflicts(self, cell_indices: List[int]) -> List[str]:
        """
        Check for cell index conflicts with existing selections.
        
        Args:
            cell_indices: Cell indices to check
        
        Returns:
            List of conflicting selection IDs
        """
        conflicts = []
        cell_set = set(cell_indices)
        
        for selection_id, selection in self.selections.items():
            if selection.status != SelectionStatus.ACTIVE:
                continue
            
            existing_set = set(selection.cell_indices)
            if cell_set & existing_set:  # Intersection check
                conflicts.append(selection_id)
        
        return conflicts
    
    def _get_next_color(self) -> str:
        """Get the next available color from the palette."""
        # Find unused color
        for color in self.COLOR_PALETTE:
            if color not in self.used_colors:
                return color
        
        # If all colors used, cycle through palette
        color = self.COLOR_PALETTE[self.color_index % len(self.COLOR_PALETTE)]
        self.color_index += 1
        return color
    
    def _get_next_well(self) -> str:
        """Get the next available well position."""
        # Find unused well
        for well in self.WELL_LAYOUT:
            if well not in self.used_wells:
                return well
        
        # If all wells used, return empty (should not happen with max_selections=96)
        self.log_warning("All wells are used")
        return ""
    
    def remove_selection(self, selection_id: str) -> bool:
        """
        Remove a selection.
        
        Args:
            selection_id: ID of selection to remove
        
        Returns:
            True if removed successfully, False otherwise
        """
        if selection_id not in self.selections:
            self.log_warning(f"Selection not found: {selection_id}")
            return False
        
        selection = self.selections[selection_id]
        
        # Free up resources
        self.used_colors.discard(selection.color)
        self.used_wells.discard(selection.well_position)
        
        # Remove selection
        del self.selections[selection_id]
        
        # Emit signal
        self.selection_removed.emit(selection_id)
        
        self.log_info(f"Removed selection '{selection.label}'")
        return True
    
    def update_selection(self, selection_id: str, **kwargs) -> bool:
        """
        Update selection properties.
        
        Args:
            selection_id: ID of selection to update
            **kwargs: Properties to update
        
        Returns:
            True if updated successfully, False otherwise
        """
        if selection_id not in self.selections:
            self.log_warning(f"Selection not found: {selection_id}")
            return False
        
        selection = self.selections[selection_id]
        old_color = selection.color
        old_well = selection.well_position
        
        # Update properties
        for key, value in kwargs.items():
            if hasattr(selection, key):
                setattr(selection, key, value)
        
        # Handle color change
        if 'color' in kwargs and kwargs['color'] != old_color:
            self.used_colors.discard(old_color)
            if kwargs['color'] not in self.used_colors:
                self.used_colors.add(kwargs['color'])
            else:
                # Color conflict, assign new color
                selection.color = self._get_next_color()
                self.used_colors.add(selection.color)
        
        # Handle well change
        if 'well_position' in kwargs and kwargs['well_position'] != old_well:
            self.used_wells.discard(old_well)
            if kwargs['well_position'] and kwargs['well_position'] not in self.used_wells:
                self.used_wells.add(kwargs['well_position'])
                self.well_assignment_changed.emit(selection_id, kwargs['well_position'])
            elif kwargs['well_position'] in self.used_wells:
                # Well conflict, assign new well
                selection.well_position = self._get_next_well()
                self.used_wells.add(selection.well_position)
                self.well_assignment_changed.emit(selection_id, selection.well_position)
        
        # Emit signal
        self.selection_updated.emit(selection_id)
        
        self.log_info(f"Updated selection '{selection.label}'")
        return True
    
    def update_selection_indices(self, selection_id: str, new_indices: List[int]) -> bool:
        """
        Update the cell indices for a specific selection.
        
        Args:
            selection_id: ID of selection to update
            new_indices: New list of cell indices
        
        Returns:
            True if updated successfully, False otherwise
        """
        if selection_id not in self.selections:
            self.log_warning(f"Selection not found: {selection_id}")
            return False
        
        selection = self.selections[selection_id]
        old_count = selection.cell_count
        
        # Update the cell indices
        selection.cell_indices = list(set(new_indices))  # Remove duplicates
        
        # Emit signal
        self.selection_updated.emit(selection_id)
        
        self.log_info(f"Updated selection '{selection.label}' indices: {old_count} -> {selection.cell_count} cells")
        return True
    
    def get_selection(self, selection_id: str) -> Optional[CellSelection]:
        """
        Get a selection by ID.
        
        Args:
            selection_id: Selection ID
        
        Returns:
            CellSelection object or None if not found
        """
        return self.selections.get(selection_id)
    
    def get_all_selections(self, status_filter: Optional[SelectionStatus] = None) -> List[CellSelection]:
        """
        Get all selections, optionally filtered by status.
        
        Args:
            status_filter: Optional status filter
        
        Returns:
            List of CellSelection objects
        """
        selections = list(self.selections.values())
        
        if status_filter:
            selections = [s for s in selections if s.status == status_filter]
        
        return selections
    
    def get_selection_table_data(self) -> List[Dict[str, Any]]:
        """
        Get selection data formatted for table display.
        
        Returns:
            List of dictionaries with selection data
        """
        table_data = []
        
        for selection in self.selections.values():
            row = {
                'id': selection.id,
                'enabled': selection.status == SelectionStatus.ACTIVE,
                'label': selection.label,
                'color': selection.color,
                'well': selection.well_position,
                'cell_count': selection.cell_count,
                'status': selection.status.value
            }
            table_data.append(row)
        
        # Sort by creation order (or by well position)
        table_data.sort(key=lambda x: x['well'] if x['well'] else 'ZZZ')
        
        return table_data
    
    def get_cells_by_color(self) -> Dict[str, List[int]]:
        """
        Get cell indices grouped by color.
        
        Returns:
            Dictionary mapping colors to cell index lists
        """
        color_map = {}
        
        for selection in self.selections.values():
            if selection.status == SelectionStatus.ACTIVE:
                if selection.color not in color_map:
                    color_map[selection.color] = []
                color_map[selection.color].extend(selection.cell_indices)
        
        return color_map
    
    def find_cell_selections(self, cell_index: int) -> List[str]:
        """
        Find all selections containing a specific cell.
        
        Args:
            cell_index: Cell index to search for
        
        Returns:
            List of selection IDs
        """
        containing_selections = []
        
        for selection_id, selection in self.selections.items():
            if selection.contains_cell(cell_index):
                containing_selections.append(selection_id)
        
        return containing_selections
    
    def merge_selections(self, selection_ids: List[str], 
                        new_label: str = "", new_color: str = "") -> Optional[str]:
        """
        Merge multiple selections into one.
        
        Args:
            selection_ids: List of selection IDs to merge
            new_label: Label for merged selection
            new_color: Color for merged selection
        
        Returns:
            New selection ID if successful, None otherwise
        """
        if len(selection_ids) < 2:
            self.log_warning("Need at least 2 selections to merge")
            return None
        
        # Collect all cell indices
        all_indices = []
        merged_metadata = {}
        
        for selection_id in selection_ids:
            if selection_id in self.selections:
                selection = self.selections[selection_id]
                all_indices.extend(selection.cell_indices)
                merged_metadata.update(selection.metadata)
        
        if not all_indices:
            self.log_warning("No cells found in selections to merge")
            return None
        
        # Create merged selection
        merged_id = self.add_selection(
            cell_indices=list(set(all_indices)),  # Remove duplicates
            label=new_label or f"Merged_{len(selection_ids)}_selections",
            color=new_color
        )
        
        if merged_id:
            # Update metadata
            self.selections[merged_id].metadata = merged_metadata
            
            # Remove original selections
            for selection_id in selection_ids:
                self.remove_selection(selection_id)
            
            self.log_info(f"Merged {len(selection_ids)} selections into '{self.selections[merged_id].label}'")
        
        return merged_id
    
    def clear_all_selections(self) -> None:
        """Clear all selections."""
        self.selections.clear()
        self.used_colors.clear()
        self.used_wells.clear()
        self.color_index = 0
        self.well_index = 0
        
        self.selections_cleared.emit()
        
        self.log_info("All selections cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get selection statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.selections:
            return {
                'total_selections': 0,
                'total_cells': 0,
                'active_selections': 0,
                'used_wells': 0,
                'used_colors': 0
            }
        
        active_selections = [s for s in self.selections.values() if s.status == SelectionStatus.ACTIVE]
        total_cells = sum(len(s.cell_indices) for s in active_selections)
        
        return {
            'total_selections': len(self.selections),
            'active_selections': len(active_selections),
            'total_cells': total_cells,
            'used_wells': len(self.used_wells),
            'used_colors': len(self.used_colors),
            'average_cells_per_selection': total_cells / len(active_selections) if active_selections else 0,
            'well_utilization': len(self.used_wells) / len(self.WELL_LAYOUT) * 100,
            'color_utilization': len(self.used_colors) / len(self.COLOR_PALETTE) * 100
        }
    
    def export_selections_data(self) -> List[Dict[str, Any]]:
        """
        Export selection data for protocol generation.
        
        Returns:
            List of selection data dictionaries
        """
        export_data = []
        
        for selection in self.selections.values():
            if selection.status == SelectionStatus.ACTIVE and selection.cell_indices:
                data = {
                    'id': selection.id,
                    'label': selection.label,
                    'color': selection.color,
                    'well_position': selection.well_position,
                    'cell_indices': selection.cell_indices.copy(),
                    'cell_count': selection.cell_count,
                    'metadata': selection.metadata.copy(),
                    'created_timestamp': selection.created_timestamp
                }
                export_data.append(data)
        
        # Sort by well position for consistent output
        export_data.sort(key=lambda x: x['well_position'] if x['well_position'] else 'ZZZ')
        
        return export_data
    
    def import_selections_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Import selection data.
        
        Args:
            data: List of selection data dictionaries
        
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            # Clear existing selections
            self.clear_all_selections()
            
            # Import each selection
            for selection_data in data:
                selection = CellSelection(
                    id=selection_data.get('id', str(uuid.uuid4())),
                    label=selection_data.get('label', ''),
                    color=selection_data.get('color', self._get_next_color()),
                    well_position=selection_data.get('well_position', ''),
                    cell_indices=selection_data.get('cell_indices', []),
                    metadata=selection_data.get('metadata', {}),
                    created_timestamp=selection_data.get('created_timestamp', __import__('time').time())
                )
                
                # Store selection
                self.selections[selection.id] = selection
                self.used_colors.add(selection.color)
                if selection.well_position:
                    self.used_wells.add(selection.well_position)
            
            self.log_info(f"Imported {len(data)} selections")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to import selections: {e}")
            self.clear_all_selections()
            return False