"""
Base Card Component

Container component for grouped content following the design system.
"""

from typing import Optional, Dict

from PySide6.QtWidgets import QFrame, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Signal

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt
from utils.card_colors import get_default_card_colors
from utils.accessibility import set_accessibility_properties, AccessibilityRole, set_focus_properties


class CardHeader(QWidget):
    """Card header component."""
    
    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui(title)
    
    def _setup_ui(self, title: str) -> None:
        """Set up the header UI."""
        tokens = DesignTokens()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6']
        )
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardHeaderTitle")
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Style
        color_vars = get_default_card_colors()
        raw_style = f"""
        CardHeader {{
            border-bottom: 1px solid var(--border);
        }}
        
        QLabel#cardHeaderTitle {{
            font-family: {tokens.get_font_string()};
            font-size: {tokens.TYPOGRAPHY['text_lg']}px;
            font-weight: {tokens.TYPOGRAPHY['font_semibold']};
            color: var(--foreground);
        }}
        """
        qt_style = convert_css_to_qt(raw_style, color_vars)
        self.setStyleSheet(qt_style)
    
    def set_title(self, title: str) -> None:
        """Update the header title."""
        self.title_label.setText(title)


class CardContent(QWidget):
    """Card content area."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the content UI."""
        tokens = DesignTokens()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6']
        )


class CardFooter(QWidget):
    """Card footer area."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the footer UI."""
        tokens = DesignTokens()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6'],
            tokens.SPACING['spacing_6']
        )
        
        # Style
        color_vars = get_default_card_colors()
        raw_style = """
        CardFooter {
            border-top: 1px solid var(--border);
            background-color: var(--muted);
        }
        """
        qt_style = convert_css_to_qt(raw_style, color_vars)
        self.setStyleSheet(qt_style)


class BaseCard(QFrame):
    """
    Container component for grouped content.
    
    Implements the design system's card specifications with support
    for header, content, and footer areas.
    """
    
    # Signals
    clicked = Signal()
    
    def __init__(
        self,
        title: str = "",
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the card.
        
        Args:
            title: Optional card title for header
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._theme_manager: Optional[ThemeManager] = None
        self._clickable = False
        
        self._setup_ui(title)
        self._apply_style()
    
    def _setup_ui(self, title: str) -> None:
        """Set up the card UI."""
        tokens = DesignTokens()
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sections
        self.header: Optional[CardHeader] = None
        self.content = CardContent()
        self.footer: Optional[CardFooter] = None
        
        # Add header if title provided
        if title:
            self.set_header(title)
        
        # Add content
        self.main_layout.addWidget(self.content)
        
        # Set frame properties
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setProperty("role", "card")
        
        # Enhanced accessibility
        self._update_accessibility_properties(title)
    
    def _update_accessibility_properties(self, title: str = "") -> None:
        """Update accessibility properties based on current state."""
        # Set accessible name based on title or default
        if title:
            accessible_name = f"Card: {title}"
        elif self.header and hasattr(self.header, 'title_label'):
            accessible_name = f"Card: {self.header.title_label.text()}"
        else:
            accessible_name = "Content card"
        
        # Set description based on whether card is clickable
        if self._clickable:
            description = "Clickable content container, press Enter or Space to activate"
            role = AccessibilityRole.BUTTON
        else:
            description = "Content container"
            role = None
        
        set_accessibility_properties(
            self,
            name=accessible_name,
            description=description,
            role=role
        )
        
        # Set focus properties for clickable cards
        if self._clickable:
            set_focus_properties(self, focusable=True)
        else:
            set_focus_properties(self, focusable=False)
    
    def _apply_style(self) -> None:
        """Apply card styling."""
        tokens = DesignTokens()
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        raw_style = f"""
        QFrame[role="card"] {{
            background-color: var(--card);
            color: var(--card-foreground);
            border: 1px solid var(--border);
            border-radius: {tokens.BORDER_RADIUS['radius_lg']}px;
        }}
        
        QFrame[role="card"][clickable="true"]:hover {{
            border-color: var(--accent);
        }}
        """
        
        # Convert CSS variables to Qt values
        qt_style = convert_css_to_qt(raw_style, color_vars)
        self.setStyleSheet(qt_style)
    
    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """
        Set the theme manager for dynamic theme updates.
        
        Args:
            theme_manager: ThemeManager instance
        """
        self._theme_manager = theme_manager
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change."""
        self._apply_style()
    
    def _get_theme_colors(self) -> Dict[str, str]:
        """
        Get theme color variables for style conversion.
        
        Returns:
            Dictionary mapping color variable names to their values
        """
        if self._theme_manager:
            # Get colors from theme manager
            return {
                'card': self._theme_manager.get_color('card'),
                'card_foreground': self._theme_manager.get_color('card_foreground'),
                'border': self._theme_manager.get_color('border'),
                'accent': self._theme_manager.get_color('accent'),
                'foreground': self._theme_manager.get_color('foreground'),
                'muted': self._theme_manager.get_color('muted'),
            }
        else:
            return get_default_card_colors()
    
    # Header management
    def set_header(self, title: str) -> CardHeader:
        """
        Set or update the card header.
        
        Args:
            title: Header title text
            
        Returns:
            The header widget
        """
        if not self.header:
            self.header = CardHeader(title)
            self.main_layout.insertWidget(0, self.header)
        else:
            self.header.set_title(title)
        
        # Update accessibility properties when header changes
        self._update_accessibility_properties()
        
        return self.header
    
    def remove_header(self) -> None:
        """Remove the card header."""
        if self.header:
            self.main_layout.removeWidget(self.header)
            self.header.deleteLater()
            self.header = None
    
    # Footer management
    def set_footer(self) -> CardFooter:
        """
        Add a footer to the card.
        
        Returns:
            The footer widget
        """
        if not self.footer:
            self.footer = CardFooter()
            self.main_layout.addWidget(self.footer)
        
        return self.footer
    
    def remove_footer(self) -> None:
        """Remove the card footer."""
        if self.footer:
            self.main_layout.removeWidget(self.footer)
            self.footer.deleteLater()
            self.footer = None
    
    # Content access
    def get_content_layout(self) -> QVBoxLayout:
        """
        Get the content area layout for adding widgets.
        
        Returns:
            The content area layout
        """
        return self.content.layout()
    
    # Interaction
    def set_clickable(self, clickable: bool) -> None:
        """
        Make the card clickable.
        
        Args:
            clickable: Whether the card should be clickable
        """
        self._clickable = clickable
        self.setProperty("clickable", str(clickable).lower())
        self.setCursor(Qt.CursorShape.PointingHandCursor if clickable else Qt.CursorShape.ArrowCursor)
        
        # Update accessibility properties when clickable state changes
        self._update_accessibility_properties()
        
        self._apply_style()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard events for accessibility."""
        if self._clickable and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    # Convenience factory methods
    @staticmethod
    def create_simple(
        title: str,
        content_widget: QWidget,
        parent: Optional[QWidget] = None
    ) -> 'BaseCard':
        """Create a simple card with title and content."""
        card = BaseCard(title, parent)
        card.get_content_layout().addWidget(content_widget)
        return card
    
    @staticmethod
    def create_clickable(
        title: str,
        content_widget: QWidget,
        parent: Optional[QWidget] = None
    ) -> 'BaseCard':
        """Create a clickable card."""
        card = BaseCard.create_simple(title, content_widget, parent)
        card.set_clickable(True)
        return card 