"""
CellSorter CSV Parser

This module handles parsing and validation of CellProfiler CSV exports
with support for large datasets and robust error handling.
"""

import time
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
from PySide6.QtCore import QObject, Signal, QThread

from config.settings import (
    REQUIRED_CSV_COLUMNS, MAX_CELL_COUNT, PERFORMANCE_TARGET_SECONDS
)
from utils.exceptions import CSVParseError, DataValidationError, PerformanceError
from utils.error_handler import error_handler
from utils.logging_config import LoggerMixin


class CSVParseWorker(QObject, LoggerMixin):
    """
    Worker thread for parsing large CSV files without blocking the UI.
    """
    
    # Signals
    progress_updated = Signal(int)  # percentage
    parsing_finished = Signal(pd.DataFrame, dict)  # dataframe, metadata
    parsing_failed = Signal(str)  # error_message
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.is_cancelled = False
    
    def cancel(self) -> None:
        """Cancel the parsing operation."""
        self.is_cancelled = True
    
    @error_handler("Parsing CSV file")
    def parse_csv(self) -> None:
        """Parse CSV file in worker thread."""
        try:
            start_time = time.time()
            file_path = Path(self.file_path)
            
            # Validate file
            if not file_path.exists():
                raise CSVParseError(f"File not found: {file_path}")
            
            if file_path.suffix.lower() != '.csv':
                raise CSVParseError(f"Not a CSV file: {file_path.suffix}")
            
            self.progress_updated.emit(10)
            
            # Get file size for progress estimation
            file_size = file_path.stat().st_size
            chunk_size = max(1000, min(10000, file_size // 100))  # Adaptive chunk size
            
            self.log_info(f"Starting CSV parsing: {file_path.name} ({file_size} bytes)")
            
            # Read CSV in chunks for large files
            chunks = []
            row_count = 0
            
            try:
                for chunk_idx, chunk in enumerate(pd.read_csv(
                    file_path, 
                    chunksize=chunk_size,
                    low_memory=False,
                    encoding='utf-8'
                )):
                    if self.is_cancelled:
                        return
                    
                    chunks.append(chunk)
                    row_count += len(chunk)
                    
                    # Update progress (up to 70%)
                    progress = min(70, 10 + (chunk_idx * 60 // 10))
                    self.progress_updated.emit(progress)
                    
                    # Check for excessive size
                    if row_count > MAX_CELL_COUNT:
                        raise DataValidationError(
                            f"Too many rows: {row_count} > {MAX_CELL_COUNT}"
                        )
                
                # Combine chunks
                self.progress_updated.emit(75)
                df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
                
            except UnicodeDecodeError:
                # Try alternative encodings
                self.log_info("UTF-8 failed, trying latin-1 encoding")
                df = pd.read_csv(file_path, encoding='latin-1', low_memory=False)
                row_count = len(df)
            
            self.progress_updated.emit(80)
            
            if self.is_cancelled:
                return
            
            # Validate CSV structure
            validation_result = self._validate_csv(df)
            
            self.progress_updated.emit(90)
            
            # Calculate performance metrics
            parse_time = time.time() - start_time
            target_time = PERFORMANCE_TARGET_SECONDS * (row_count / 50000)  # 3s for 50k records
            
            # Create metadata
            metadata = {
                'file_path': str(file_path),
                'row_count': row_count,
                'column_count': len(df.columns),
                'parse_time_seconds': parse_time,
                'performance_target_met': parse_time <= target_time,
                'file_size_bytes': file_size,
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'validation_errors': validation_result['errors'],
                'validation_warnings': validation_result['warnings'],
                'has_required_columns': validation_result['has_required_columns'],
                'numeric_columns': validation_result['numeric_columns'],
                'bounding_box_columns': validation_result['bounding_box_columns']
            }
            
            self.progress_updated.emit(100)
            
            # Log results
            if validation_result['errors']:
                raise DataValidationError(f"CSV validation failed: {validation_result['errors']}")
            
            self.log_info(f"CSV parsed successfully: {row_count:,} rows, {len(df.columns)} columns, {parse_time:.2f}s")
            
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    self.log_warning(warning)
            
            if not metadata['performance_target_met']:
                self.log_warning(f"CSV parsing exceeded target time: {parse_time:.2f}s > {target_time:.2f}s")
            
            self.parsing_finished.emit(df, metadata)
            
        except Exception as e:
            self.log_error(f"Failed to parse CSV {self.file_path}: {e}")
            self.parsing_failed.emit(str(e))
    
    def _validate_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate CSV structure and content.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append("CSV file is empty")
            return {
                'errors': errors,
                'warnings': warnings,
                'has_required_columns': False,
                'numeric_columns': [],
                'bounding_box_columns': []
            }
        
        # Check for required columns
        missing_columns = [col for col in REQUIRED_CSV_COLUMNS if col not in df.columns]
        has_required_columns = len(missing_columns) == 0
        
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Find numeric columns (for plotting)
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_columns) < 2:
            warnings.append("Less than 2 numeric columns found - plotting may be limited")
        
        # Validate bounding box columns if present
        bounding_box_columns = [col for col in REQUIRED_CSV_COLUMNS if col in df.columns]
        
        if has_required_columns:
            # Check for valid bounding box values
            for col in bounding_box_columns:
                if df[col].isna().any():
                    warnings.append(f"Column {col} contains missing values")
                
                if (df[col] < 0).any():
                    warnings.append(f"Column {col} contains negative values")
                
                # Check for reasonable coordinate ranges
                max_val = df[col].max()
                if max_val > 50000:  # Arbitrary large image size threshold
                    warnings.append(f"Column {col} has very large values (max: {max_val})")
        
        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate rows")
        
        # Check data types
        object_columns = df.select_dtypes(include=['object']).columns
        if len(object_columns) > len(df.columns) * 0.8:
            warnings.append("Most columns are text - this may not be CellProfiler output")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'has_required_columns': has_required_columns,
            'numeric_columns': numeric_columns,
            'bounding_box_columns': bounding_box_columns
        }


class CSVParser(QObject, LoggerMixin):
    """
    CSV Parser for CellProfiler data files.
    
    Features:
    - Robust CSV parsing with encoding detection
    - Large file support (up to 100,000 records)
    - Performance monitoring and optimization
    - Data validation and error reporting
    - Asynchronous parsing to prevent UI blocking
    """
    
    # Signals
    csv_loaded = Signal(str)  # file_path
    csv_load_failed = Signal(str)  # error_message
    data_validated = Signal(bool)  # validation_success
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # State
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.current_file_path: Optional[str] = None
        
        # Worker thread
        self.parse_worker: Optional[CSVParseWorker] = None
        self.parse_thread: Optional[QThread] = None
        
        # Performance tracking
        self.parse_start_time: Optional[float] = None
    
    @error_handler("Loading CSV file")
    def load_csv(self, file_path: str) -> None:
        """
        Load a CSV file asynchronously.
        
        Args:
            file_path: Path to the CSV file
        """
        if self.parse_thread and self.parse_thread.isRunning():
            self.cancel_parsing()
        
        self.current_file_path = file_path
        self.parse_start_time = time.time()
        
        # Create worker and thread
        self.parse_worker = CSVParseWorker(file_path)
        self.parse_thread = QThread()
        
        # Connect signals
        self.parse_worker.moveToThread(self.parse_thread)
        self.parse_thread.started.connect(self.parse_worker.parse_csv)
        self.parse_worker.parsing_finished.connect(self._on_csv_loaded)
        self.parse_worker.parsing_failed.connect(self._on_csv_load_failed)
        self.parse_worker.parsing_finished.connect(self.parse_thread.quit)
        self.parse_worker.parsing_failed.connect(self.parse_thread.quit)
        
        # Start parsing
        self.parse_thread.start()
        
        self.log_info(f"Started parsing CSV: {Path(file_path).name}")
    
    def cancel_parsing(self) -> None:
        """Cancel current CSV parsing operation."""
        if self.parse_worker:
            self.parse_worker.cancel()
        
        if self.parse_thread and self.parse_thread.isRunning():
            self.parse_thread.quit()
            self.parse_thread.wait(1000)  # Wait up to 1 second
        
        self.log_info("CSV parsing cancelled")
    
    def _on_csv_loaded(self, dataframe: pd.DataFrame, metadata: Dict[str, Any]) -> None:
        """
        Handle successful CSV loading.
        
        Args:
            dataframe: Parsed DataFrame
            metadata: Parsing metadata
        """
        self.data = dataframe
        self.metadata = metadata
        
        # Emit signals
        self.csv_loaded.emit(self.current_file_path)
        self.data_validated.emit(metadata['has_required_columns'])
        
        # Log performance
        if self.parse_start_time:
            total_time = time.time() - self.parse_start_time
            self.log_info(f"CSV loading completed in {total_time:.2f}s")
            
            if not metadata.get('performance_target_met', True):
                self.log_warning("CSV parsing exceeded performance target")
    
    def _on_csv_load_failed(self, error_message: str) -> None:
        """
        Handle failed CSV loading.
        
        Args:
            error_message: Error description
        """
        self.data = None
        self.metadata = {}
        
        # Emit signal
        self.csv_load_failed.emit(error_message)
        
        self.log_error(f"CSV loading failed: {error_message}")
    
    def get_numeric_columns(self) -> List[str]:
        """
        Get list of numeric columns suitable for plotting.
        
        Returns:
            List of numeric column names
        """
        if self.data is None:
            return []
        
        return self.data.select_dtypes(include=[np.number]).columns.tolist()
    
    def get_bounding_box_data(self) -> Optional[pd.DataFrame]:
        """
        Extract bounding box data for cells.
        
        Returns:
            DataFrame with bounding box columns or None
        """
        if self.data is None or not self.metadata.get('has_required_columns', False):
            return None
        
        bbox_columns = self.metadata.get('bounding_box_columns', [])
        if not bbox_columns:
            return None
        
        return self.data[bbox_columns].copy()
    
    def get_column_statistics(self, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific column.
        
        Args:
            column_name: Name of the column
        
        Returns:
            Dictionary with column statistics or None
        """
        if self.data is None or column_name not in self.data.columns:
            return None
        
        column = self.data[column_name]
        
        stats = {
            'name': column_name,
            'dtype': str(column.dtype),
            'count': len(column),
            'null_count': column.isna().sum(),
            'unique_count': column.nunique()
        }
        
        if pd.api.types.is_numeric_dtype(column):
            stats.update({
                'mean': float(column.mean()),
                'std': float(column.std()),
                'min': float(column.min()),
                'max': float(column.max()),
                'median': float(column.median()),
                'q25': float(column.quantile(0.25)),
                'q75': float(column.quantile(0.75))
            })
        
        return stats
    
    def filter_data(self, conditions: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Filter data based on conditions.
        
        Args:
            conditions: Dictionary of filter conditions
        
        Returns:
            Filtered DataFrame or None
        """
        if self.data is None:
            return None
        
        filtered_data = self.data.copy()
        
        for column, condition in conditions.items():
            if column not in filtered_data.columns:
                continue
            
            if isinstance(condition, dict):
                if 'min' in condition:
                    filtered_data = filtered_data[filtered_data[column] >= condition['min']]
                if 'max' in condition:
                    filtered_data = filtered_data[filtered_data[column] <= condition['max']]
                if 'values' in condition:
                    filtered_data = filtered_data[filtered_data[column].isin(condition['values'])]
        
        return filtered_data
    
    def get_data_sample(self, n_rows: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get a sample of the data for preview.
        
        Args:
            n_rows: Number of rows to sample
        
        Returns:
            Sample DataFrame or None
        """
        if self.data is None:
            return None
        
        if len(self.data) <= n_rows:
            return self.data.copy()
        
        return self.data.sample(n=n_rows).copy()
    
    def get_data_by_index(self, index: int) -> Optional[pd.Series]:
        """
        Get data for a specific row index.
        
        Args:
            index: Row index to retrieve
        
        Returns:
            Series with row data or None if not found
        """
        if self.data is None or self.data.empty:
            return None
        
        if index < 0 or index >= len(self.data):
            self.log_warning(f"Index {index} out of range [0, {len(self.data)})")
            return None
        
        return self.data.iloc[index].copy()
    
    def get_xy_columns(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the X and Y coordinate column names.
        
        Returns:
            Tuple of (x_column, y_column) names or (None, None)
        """
        if self.data is None:
            return None, None
        
        # Look for standard CellProfiler coordinate columns
        x_candidates = [col for col in self.data.columns if 'Center_X' in col or 'Location_Center_X' in col]
        y_candidates = [col for col in self.data.columns if 'Center_Y' in col or 'Location_Center_Y' in col]
        
        x_col = x_candidates[0] if x_candidates else None
        y_col = y_candidates[0] if y_candidates else None
        
        return x_col, y_col
    
    def export_filtered_data(self, filtered_data: pd.DataFrame, 
                           output_path: str, include_metadata: bool = True) -> bool:
        """
        Export filtered data to CSV file.
        
        Args:
            filtered_data: DataFrame to export
            output_path: Output file path
            include_metadata: Whether to include metadata header
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if include_metadata and self.metadata:
                # Write metadata as comments
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# CellSorter Filtered Export\n")
                    f.write(f"# Original file: {self.metadata.get('file_path', 'Unknown')}\n")
                    f.write(f"# Original rows: {self.metadata.get('row_count', 0)}\n")
                    f.write(f"# Filtered rows: {len(filtered_data)}\n")
                    f.write(f"# Export time: {pd.Timestamp.now().isoformat()}\n")
                    f.write("#\n")
                
                # Append data
                filtered_data.to_csv(output_path, mode='a', index=False)
            else:
                filtered_data.to_csv(output_path, index=False)
            
            self.log_info(f"Exported {len(filtered_data)} rows to {output_path}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to export data: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the current dataset.
        
        Returns:
            Dictionary with dataset information
        """
        if self.data is None:
            return {}
        
        info = {
            'file_path': self.current_file_path,
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'numeric_columns': self.get_numeric_columns(),
            'memory_usage_mb': self.data.memory_usage(deep=True).sum() / (1024 * 1024),
            'has_bounding_boxes': self.metadata.get('has_required_columns', False)
        }
        
        info.update(self.metadata)
        return info
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.cancel_parsing()
        self.data = None
        self.metadata = {}
        self.current_file_path = None