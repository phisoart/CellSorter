"""
CellSorter Design System Components

Based on the design specifications in docs/design/DESIGN_SYSTEM.md
Provides reusable UI components with consistent styling.
"""

from typing import Optional, Dict, Any, Literal
from PySide6.QtWidgets import (
    QPushButton, QLineEdit, QFrame, QDialog, QLabel, 
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from services.theme_manager import ThemeManager


# Design Tokens
class DesignTokens:
    """Design tokens based on the design system specifications."""
    
    # Typography
    FONT_FAMILY_SANS = ['Inter', 'system-ui', 'Segoe UI', 'sans-serif']
    FONT_FAMILY_MONO = ['JetBrains Mono', 'Consolas', 'monospace']
    
    # Font Sizes (px)
    TEXT_XS = 12
    TEXT_SM = 14
    TEXT_BASE = 16
    TEXT_LG = 18
    TEXT_XL = 20
    TEXT_2XL = 24
    TEXT_3XL = 30
    TEXT_4XL = 36
    
    # Line Heights
    LEADING_NONE = 1.0
    LEADING_TIGHT = 1.25
    LEADING_NORMAL = 1.5
    LEADING_RELAXED = 1.625
    
    # Font Weights
    FONT_NORMAL = 400
    FONT_MEDIUM = 500
    FONT_SEMIBOLD = 600
    FONT_BOLD = 700
    
    # Spacing (px)
    SPACING_0 = 0
    SPACING_1 = 4
    SPACING_2 = 8
    SPACING_3 = 12
    SPACING_4 = 16
    SPACING_5 = 20
    SPACING_6 = 24
    SPACING_8 = 32
    SPACING_10 = 40
    SPACING_12 = 48
    SPACING_16 = 64
    SPACING_20 = 80
    SPACING_24 = 96
    
    # Border Radius (px)
    RADIUS_NONE = 0
    RADIUS_SM = 2
    RADIUS_DEFAULT = 4
    RADIUS_MD = 6
    RADIUS_LG = 8
    RADIUS_XL = 12
    RADIUS_2XL = 16
    RADIUS_FULL = 9999
    
    # Transitions
    TRANSITION_DEFAULT = 150  # ms
    TRANSITION_FAST = 100
    TRANSITION_SLOW = 300


class Button(QPushButton):
    """
    Modern button component with shadcn/ui styling.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    def __init__(
        self, 
        text: str = "",
        variant: Literal["default", "secondary", "outline", "ghost", "destructive"] = "default",
        size: Literal["sm", "default", "lg", "icon"] = "default",
        parent: Optional[QWidget] = None
    ):
        super().__init__(text, parent)
        self.variant = variant
        self.size = size
        self._setup_style()
        
    def _setup_style(self):
        """Apply styling based on variant and size."""
        # Base styles
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(self._get_font())
        
        # Size-specific styles
        size_styles = {
            "sm": {
                "height": 36,
                "padding": (DesignTokens.SPACING_1, DesignTokens.SPACING_3),
                "font_size": DesignTokens.TEXT_SM
            },
            "default": {
                "height": 40,
                "padding": (DesignTokens.SPACING_2, DesignTokens.SPACING_4),
                "font_size": DesignTokens.TEXT_SM
            },
            "lg": {
                "height": 44,
                "padding": (DesignTokens.SPACING_3, DesignTokens.SPACING_8),
                "font_size": DesignTokens.TEXT_BASE
            },
            "icon": {
                "height": 40,
                "width": 40,
                "padding": (0, 0),
                "font_size": DesignTokens.TEXT_BASE
            }
        }
        
        style = size_styles[self.size]
        self.setMinimumHeight(style["height"])
        if self.size == "icon":
            self.setMinimumWidth(style["width"])
            self.setMaximumWidth(style["width"])
        
        # Apply stylesheet
        self._update_stylesheet()
        
    def _get_font(self) -> QFont:
        """Get font for the button."""
        font = QFont()
        font.setFamily(", ".join(DesignTokens.FONT_FAMILY_SANS))
        font.setWeight(DesignTokens.FONT_MEDIUM)
        return font
        
    def _update_stylesheet(self):
        """Update the stylesheet based on variant."""
        # This will be properly styled by the theme manager
        self.setProperty("variant", self.variant)
        self.setProperty("size", self.size)
        
    def setVariant(self, variant: str):
        """Change button variant."""
        self.variant = variant
        self._update_stylesheet()
        
    def setSize(self, size: str):
        """Change button size."""
        self.size = size
        self._setup_style()


class Input(QLineEdit):
    """
    Modern input field with validation states.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    def __init__(
        self,
        placeholder: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()
        self._state = "default"
        
    def _setup_style(self):
        """Apply base styling."""
        self.setMinimumHeight(40)
        font = QFont()
        font.setFamily(", ".join(DesignTokens.FONT_FAMILY_SANS))
        font.setPixelSize(DesignTokens.TEXT_SM)
        self.setFont(font)
        
        # Content margins
        self.setContentsMargins(
            DesignTokens.SPACING_3, 
            DesignTokens.SPACING_2,
            DesignTokens.SPACING_3,
            DesignTokens.SPACING_2
        )
        
    def setState(self, state: Literal["default", "focused", "error", "disabled"]):
        """Set the input state."""
        self._state = state
        self.setProperty("state", state)
        self.setEnabled(state != "disabled")
        self.style().unpolish(self)
        self.style().polish(self)
        
    def setError(self, error: bool):
        """Set error state."""
        self.setState("error" if error else "default")


class Card(QFrame):
    """
    Container component for grouped content.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_style()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
    def _setup_style(self):
        """Apply card styling."""
        self.setProperty("role", "card")
        self.setFrameStyle(QFrame.StyledPanel)
        
    def addHeader(self, widget: QWidget):
        """Add a header widget to the card."""
        widget.setProperty("role", "card-header")
        self._layout.insertWidget(0, widget)
        
    def addContent(self, widget: QWidget):
        """Add content widget to the card."""
        widget.setProperty("role", "card-content")
        self._layout.addWidget(widget)
        
    def addFooter(self, widget: QWidget):
        """Add footer widget to the card."""
        widget.setProperty("role", "card-footer")
        self._layout.addWidget(widget)
        

class CardHeader(QWidget):
    """Card header component."""
    
    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("role", "card-header")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6
        )
        
        self.title_label = QLabel(title)
        font = QFont()
        font.setFamily(", ".join(DesignTokens.FONT_FAMILY_SANS))
        font.setWeight(DesignTokens.FONT_SEMIBOLD)
        font.setPixelSize(DesignTokens.TEXT_LG)
        self.title_label.setFont(font)
        
        layout.addWidget(self.title_label)
        layout.addStretch()
        
    def setTitle(self, title: str):
        """Set the header title."""
        self.title_label.setText(title)


class CardContent(QWidget):
    """Card content area component."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("role", "card-content")
        self.setContentsMargins(
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6
        )


class CardFooter(QWidget):
    """Card footer area component."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("role", "card-footer")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6,
            DesignTokens.SPACING_6
        )
        layout.setAlignment(Qt.AlignRight)


class Dialog(QDialog):
    """
    Modal dialog component with overlay.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    def __init__(
        self,
        title: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._setup_style()
        self._setup_layout()
        
    def _setup_style(self):
        """Apply dialog styling."""
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def _setup_layout(self):
        """Set up the dialog layout."""
        # Main container
        self.container = QFrame(self)
        self.container.setProperty("role", "dialog")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)
        
        # Container layout
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setSpacing(DesignTokens.SPACING_6)
        
        # Title
        if self.windowTitle():
            title_label = QLabel(self.windowTitle())
            title_label.setProperty("role", "title")
            font = QFont()
            font.setFamily(", ".join(DesignTokens.FONT_FAMILY_SANS))
            font.setWeight(DesignTokens.FONT_SEMIBOLD)
            font.setPixelSize(DesignTokens.TEXT_LG)
            title_label.setFont(font)
            self.content_layout.addWidget(title_label)
            
    def addContent(self, widget: QWidget):
        """Add content to the dialog."""
        self.content_layout.addWidget(widget)
        
    def addButtons(self, buttons: list):
        """Add action buttons to the dialog."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(DesignTokens.SPACING_3)
        button_layout.addStretch()
        
        for button in buttons:
            button_layout.addWidget(button)
            
        self.content_layout.addLayout(button_layout)


class Label(QLabel):
    """
    Styled label component.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    def __init__(
        self,
        text: str = "",
        variant: Literal["default", "muted", "title", "description"] = "default",
        parent: Optional[QWidget] = None
    ):
        super().__init__(text, parent)
        self.variant = variant
        self._setup_style()
        
    def _setup_style(self):
        """Apply label styling based on variant."""
        font = QFont()
        font.setFamily(", ".join(DesignTokens.FONT_FAMILY_SANS))
        
        if self.variant == "title":
            font.setWeight(DesignTokens.FONT_SEMIBOLD)
            font.setPixelSize(DesignTokens.TEXT_LG)
            self.setProperty("role", "title")
        elif self.variant == "description":
            font.setWeight(DesignTokens.FONT_NORMAL)
            font.setPixelSize(DesignTokens.TEXT_SM)
            self.setProperty("role", "description")
        elif self.variant == "muted":
            font.setWeight(DesignTokens.FONT_NORMAL)
            font.setPixelSize(DesignTokens.TEXT_SM)
            self.setProperty("role", "muted")
        else:
            font.setWeight(DesignTokens.FONT_NORMAL)
            font.setPixelSize(DesignTokens.TEXT_BASE)
            
        self.setFont(font)