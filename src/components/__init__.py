"""
Components Module

Modern UI components following shadcn/ui design patterns.
"""

from .base.base_button import BaseButton, ButtonVariant, ButtonSize
from .base.base_card import BaseCard
from .base.base_input import BaseInput, InputState
from .base.base_select import BaseSelect, SelectState
from .base.base_textarea import BaseTextarea, TextareaState

# Import Button alias from design_system for convenience
from .design_system import Button

from .tooltip_wrapper import (
    TruncatedTextLabel, 
    TooltipWrapper, 
    TooltipPosition,
    create_truncated_label,
    wrap_with_tooltip
)

from .skeleton_loader import (
    BaseSkeleton,
    SkeletonAnimation,
    SkeletonShape,
    create_skeleton_text,
    create_skeleton_card,
    create_skeleton_table,
    create_skeleton_list
)

from .scientific_widgets import (
    ScatterPlotWidget,
    ImageViewerWidget,
    WellPlateWidget
)

# Widget imports temporarily removed - will be added when widgets are implemented

from .design_system import DesignTokens

__all__ = [
    # Base components
    'BaseButton',
    'Button',  # Alias for BaseButton
    'ButtonVariant', 
    'ButtonSize',
    'BaseCard',
    'BaseInput',
    'InputState',
    'BaseSelect',
    'SelectState',
    'BaseTextarea',
    'TextareaState',
    
    # Tooltip components
    'TruncatedTextLabel',
    'TooltipWrapper',
    'TooltipPosition',
    'create_truncated_label',
    'wrap_with_tooltip',
    
    # Skeleton components
    'BaseSkeleton',
    'SkeletonAnimation',
    'SkeletonShape',
    'create_skeleton_text',
    'create_skeleton_card',
    'create_skeleton_table',
    'create_skeleton_list',
    
    # Scientific widgets
    'ScatterPlotWidget',
    'ImageViewerWidget',
    'WellPlateWidget',
    
    # Widget aliases (will be added when implemented)
    # 'WellPlate',
    # 'ScatterPlot',
    # 'SelectionPanel',
    # 'MiniMapWidget',
    # 'ExpressionFilterWidget',
    
    # Design system
    'DesignTokens',
]