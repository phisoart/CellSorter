"""
UI Compatibility Layer

Provides compatibility classes for the UI renderer.
These classes bridge the gap between the complete ui_model and simplified renderer expectations.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .ui_model import Widget as BaseWidget, WidgetType, EventBinding, LayoutItem, Size, Geometry, SizePolicy


@dataclass
class Widget:
    """Widget definition compatible with renderer."""
    name: str
    type: WidgetType
    parent: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    visible: Optional[bool] = None
    enabled: Optional[bool] = None
    tooltip: Optional[str] = None
    style_sheet: Optional[str] = None
    geometry: Optional[Geometry] = None
    minimum_size: Optional[Size] = None
    maximum_size: Optional[Size] = None
    size_policy: Optional[SizePolicy] = None
    events: List[EventBinding] = field(default_factory=list)
    
    def to_base_widget(self) -> 'BaseWidget':
        """Convert to base widget from ui_model."""
        from .ui_model import Widget as BaseWidget
        
        base_widget = BaseWidget(
            name=self.name,
            type=self.type,
            properties=self.properties.copy() if self.properties else {},
            parent_name=self.parent
        )
        
        if self.geometry:
            base_widget.geometry = self.geometry
        
        if self.visible is not None:
            base_widget.visible = self.visible
        
        if self.enabled is not None:
            base_widget.enabled = self.enabled
        
        if self.tooltip:
            base_widget.tooltip = self.tooltip
        
        if self.style_sheet:
            base_widget.style_sheet = self.style_sheet
        
        return base_widget
    
    @classmethod
    def from_base_widget(cls, base_widget: 'BaseWidget') -> 'Widget':
        """Create from base widget."""
        widget = cls(
            name=base_widget.name,
            type=base_widget.type,
            parent=base_widget.parent_name,
            properties=base_widget.properties.copy()
        )
        
        if base_widget.geometry:
            widget.geometry = base_widget.geometry
        
        widget.visible = base_widget.visible
        widget.enabled = base_widget.enabled
        widget.tooltip = base_widget.tooltip
        widget.style_sheet = base_widget.style_sheet
        
        return widget


@dataclass 
class UI:
    """Simple UI definition for renderer compatibility."""
    widgets: List[Widget] = field(default_factory=list)
    layouts: List[LayoutItem] = field(default_factory=list)
    events: List[EventBinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'widgets': [w.__dict__ for w in self.widgets],
            'layouts': [l.to_dict() for l in self.layouts],
            'events': [e.to_dict() for e in self.events],
            'metadata': self.metadata.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UI':
        """Create from dictionary."""
        widgets = []
        for w_data in data.get('widgets', []):
            widget = Widget(**w_data)
            if 'geometry' in w_data and w_data['geometry']:
                widget.geometry = Geometry.from_dict(w_data['geometry'])
            if 'minimum_size' in w_data and w_data['minimum_size']:
                widget.minimum_size = Size.from_dict(w_data['minimum_size'])
            if 'maximum_size' in w_data and w_data['maximum_size']:
                widget.maximum_size = Size.from_dict(w_data['maximum_size'])
            if 'size_policy' in w_data and w_data['size_policy']:
                widget.size_policy = SizePolicy.from_dict(w_data['size_policy'])
            widgets.append(widget)
        
        return cls(
            widgets=widgets,
            layouts=[LayoutItem.from_dict(l) for l in data.get('layouts', [])],
            events=[EventBinding.from_dict(e) for e in data.get('events', [])],
            metadata=data.get('metadata', {})
        ) 