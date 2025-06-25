"""
CellSorter Exception Classes

This module defines custom exception classes for the CellSorter application.
All exceptions inherit from CellSorterError for consistent error handling.
"""

from typing import Optional, Any, Dict


class CellSorterError(Exception):
    """Base exception class for all CellSorter errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class FileError(CellSorterError):
    """Raised when file operations fail."""
    pass


class ImageLoadError(FileError):
    """Raised when image loading fails."""
    pass


class CSVParseError(FileError):
    """Raised when CSV parsing fails."""
    pass


class DataValidationError(CellSorterError):
    """Raised when data validation fails."""
    pass


class CoordinateTransformError(CellSorterError):
    """Raised when coordinate transformation fails."""
    pass


class CalibrationError(CoordinateTransformError):
    """Raised when calibration is invalid or fails."""
    pass


class TransformationError(CoordinateTransformError):
    """Raised when coordinate transformation fails."""
    pass


class SelectionError(CellSorterError):
    """Raised when cell selection operations fail."""
    pass


class ExportError(CellSorterError):
    """Raised when protocol export fails."""
    pass


class ProtocolFormatError(ExportError):
    """Raised when protocol format is invalid."""
    pass


class PerformanceError(CellSorterError):
    """Raised when performance requirements are not met."""
    pass


class MemoryError(PerformanceError):
    """Raised when memory limits are exceeded."""
    pass


class HardwareIntegrationError(CellSorterError):
    """Raised when hardware integration fails."""
    pass


class UIError(CellSorterError):
    """Raised when UI operations fail."""
    pass


class ConfigurationError(CellSorterError):
    """Raised when configuration is invalid."""
    pass


class SessionError(CellSorterError):
    """Raised when session management operations fail."""
    pass


# Error codes for common issues
ERROR_CODES = {
    "FILE_NOT_FOUND": "The specified file could not be found",
    "UNSUPPORTED_FORMAT": "The file format is not supported",
    "FILE_TOO_LARGE": "The file exceeds the maximum size limit",
    "INVALID_CSV_FORMAT": "The CSV file format is invalid",
    "MISSING_REQUIRED_COLUMNS": "Required columns are missing from the CSV",
    "CALIBRATION_POINTS_TOO_CLOSE": "Calibration points are too close together",
    "COORDINATE_OUT_OF_BOUNDS": "Coordinates are outside valid range",
    "INSUFFICIENT_MEMORY": "Insufficient memory to complete operation",
    "PERFORMANCE_TARGET_MISSED": "Operation exceeded performance target",
    "EXPORT_VALIDATION_FAILED": "Export validation failed",
    "HARDWARE_COMMUNICATION_ERROR": "Failed to communicate with hardware"
}