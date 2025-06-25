"""
Test CSV Parser

Tests for models.csv_parser module to ensure compliance with
PRODUCT_REQUIREMENTS.md specifications for CellProfiler data handling.
"""

import pytest
import time
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from pathlib import Path

from PySide6.QtCore import QThread

from models.csv_parser import CSVParser, CSVParseWorker
from utils.exceptions import CSVParseError, DataValidationError
from config.settings import REQUIRED_CSV_COLUMNS, MAX_CELL_COUNT


@pytest.mark.unit
class TestCSVParseWorker:
    """Test CSVParseWorker for asynchronous CSV parsing."""
    
    def test_worker_creation(self, sample_csv_file):
        """Test CSVParseWorker instantiation."""
        worker = CSVParseWorker(str(sample_csv_file))
        assert worker.file_path == str(sample_csv_file)
        assert worker.is_cancelled is False
    
    def test_worker_cancellation(self, sample_csv_file):
        """Test worker cancellation functionality."""
        worker = CSVParseWorker(str(sample_csv_file))
        worker.cancel()
        assert worker.is_cancelled is True
    
    def test_parse_valid_csv(self, sample_csv_file, sample_csv_data):
        """Test parsing valid CellProfiler CSV file."""
        worker = CSVParseWorker(str(sample_csv_file))
        
        # Capture results
        results = {'dataframe': None, 'metadata': None, 'error': None}
        
        def capture_success(df, metadata):
            results['dataframe'] = df
            results['metadata'] = metadata
        
        def capture_error(error):
            results['error'] = error
        
        worker.parsing_finished.connect(capture_success)
        worker.parsing_failed.connect(capture_error)
        
        # Parse CSV
        worker.parse_csv()
        
        # Verify successful parsing
        assert results['error'] is None, f"Parsing failed: {results['error']}"
        assert results['dataframe'] is not None
        assert results['metadata'] is not None
        
        # Verify dataframe content
        df = results['dataframe']
        assert len(df) == len(sample_csv_data)
        assert list(df.columns) == list(sample_csv_data.columns)
        
        # Verify metadata
        metadata = results['metadata']
        assert metadata['row_count'] == len(sample_csv_data)
        assert metadata['column_count'] == len(sample_csv_data.columns)
        assert metadata['has_required_columns'] is True
        assert 'parse_time_seconds' in metadata
        assert 'file_size_bytes' in metadata
    
    def test_parse_invalid_csv(self, invalid_csv_file):
        """Test parsing CSV with missing required columns."""
        worker = CSVParseWorker(str(invalid_csv_file))
        
        error_message = None
        
        def capture_error(error):
            nonlocal error_message
            error_message = error
        
        worker.parsing_failed.connect(capture_error)
        worker.parse_csv()
        
        assert error_message is not None
        assert "validation failed" in error_message.lower()
    
    def test_parse_nonexistent_file(self, temp_dir):
        """Test error handling for nonexistent files."""
        nonexistent_file = temp_dir / "nonexistent.csv"
        worker = CSVParseWorker(str(nonexistent_file))
        
        error_message = None
        
        def capture_error(error):
            nonlocal error_message
            error_message = error
        
        worker.parsing_failed.connect(capture_error)
        worker.parse_csv()
        
        assert error_message is not None
        assert "File not found" in error_message
    
    def test_validate_csv_structure(self, sample_csv_data):
        """Test CSV validation logic."""
        worker = CSVParseWorker("dummy_path")
        
        # Test valid CSV
        result = worker._validate_csv(sample_csv_data)
        assert len(result['errors']) == 0
        assert result['has_required_columns'] is True
        assert len(result['numeric_columns']) > 0
        assert len(result['bounding_box_columns']) == 4
        
        # Test CSV with missing columns
        invalid_df = sample_csv_data.drop(columns=[REQUIRED_CSV_COLUMNS[0]])
        result = worker._validate_csv(invalid_df)
        assert len(result['errors']) > 0
        assert result['has_required_columns'] is False
        
        # Test empty CSV
        empty_df = pd.DataFrame()
        result = worker._validate_csv(empty_df)
        assert len(result['errors']) > 0
        assert "empty" in result['errors'][0].lower()
    
    def test_csv_with_missing_values(self, temp_dir, sample_csv_data):
        """Test handling of CSV with missing values."""
        # Introduce some missing values
        modified_data = sample_csv_data.copy()
        modified_data.loc[0, REQUIRED_CSV_COLUMNS[0]] = np.nan
        
        csv_file = temp_dir / "csv_with_missing.csv"
        modified_data.to_csv(csv_file, index=False)
        
        worker = CSVParseWorker(str(csv_file))
        
        results = {'metadata': None}
        
        def capture_success(df, metadata):
            results['metadata'] = metadata
        
        worker.parsing_finished.connect(capture_success)
        worker.parse_csv()
        
        # Should complete but with warnings
        assert results['metadata'] is not None
        assert len(results['metadata']['validation_warnings']) > 0
    
    @pytest.mark.slow
    def test_large_csv_parsing(self, large_csv_file, performance_thresholds):
        """Test parsing large CSV files within performance requirements."""
        worker = CSVParseWorker(str(large_csv_file))
        
        start_time = time.time()
        results = {'completed': False, 'metadata': None}
        
        def capture_success(df, metadata):
            results['completed'] = True
            results['metadata'] = metadata
        
        worker.parsing_finished.connect(capture_success)
        worker.parse_csv()
        
        # Wait for completion with timeout
        while not results['completed'] and (time.time() - start_time) < 30:
            time.sleep(0.1)
        
        assert results['completed'], "Large CSV parsing timed out"
        
        # Verify performance requirement
        metadata = results['metadata']
        parse_time = metadata['parse_time_seconds']
        row_count = metadata['row_count']
        
        # Target: 3 seconds for 50K records
        target_time = performance_thresholds['csv_parse_time_50k'] * (row_count / 50000)
        tolerance_factor = 2.0  # Allow some tolerance for test environment
        
        assert parse_time <= target_time * tolerance_factor, \
            f"CSV parsing too slow: {parse_time:.2f}s > {target_time * tolerance_factor:.2f}s for {row_count:,} rows"


@pytest.mark.gui
class TestCSVParser:
    """Test CSVParser GUI component."""
    
    def test_csv_parser_creation(self, qapp):
        """Test CSVParser instantiation."""
        parser = CSVParser()
        
        assert parser.data is None
        assert parser.current_file_path is None
        assert len(parser.metadata) == 0
    
    @pytest.mark.slow
    def test_load_csv_async(self, qapp, sample_csv_file):
        """Test asynchronous CSV loading."""
        parser = CSVParser()
        
        # Track signals
        signals_received = {'loaded': False, 'failed': False, 'validated': None}
        
        def on_loaded(file_path):
            signals_received['loaded'] = True
        
        def on_failed(error):
            signals_received['failed'] = True
        
        def on_validated(success):
            signals_received['validated'] = success
        
        parser.csv_loaded.connect(on_loaded)
        parser.csv_load_failed.connect(on_failed)
        parser.data_validated.connect(on_validated)
        
        # Start loading
        parser.load_csv(str(sample_csv_file))
        
        # Wait for loading to complete
        timeout = 10  # 10 seconds
        start_time = time.time()
        
        while not (signals_received['loaded'] or signals_received['failed']):
            qapp.processEvents()
            if (time.time() - start_time) > timeout:
                break
            time.sleep(0.01)
        
        # Verify successful loading
        assert signals_received['loaded'] is True
        assert signals_received['failed'] is False
        assert signals_received['validated'] is True
        assert parser.data is not None
        assert parser.current_file_path == str(sample_csv_file)
    
    def test_get_numeric_columns(self, qapp, sample_csv_data):
        """Test numeric column identification."""
        parser = CSVParser()
        
        # Test empty state
        numeric_cols = parser.get_numeric_columns()
        assert numeric_cols == []
        
        # Test with data
        parser.data = sample_csv_data
        numeric_cols = parser.get_numeric_columns()
        
        # Should include all numeric columns from sample data
        expected_numeric = sample_csv_data.select_dtypes(include=[np.number]).columns.tolist()
        assert set(numeric_cols) == set(expected_numeric)
    
    def test_get_bounding_box_data(self, qapp, sample_csv_data):
        """Test bounding box data extraction."""
        parser = CSVParser()
        
        # Test empty state
        bbox_data = parser.get_bounding_box_data()
        assert bbox_data is None
        
        # Test with valid data
        parser.data = sample_csv_data
        parser.metadata = {'has_required_columns': True, 'bounding_box_columns': REQUIRED_CSV_COLUMNS}
        
        bbox_data = parser.get_bounding_box_data()
        assert bbox_data is not None
        assert list(bbox_data.columns) == REQUIRED_CSV_COLUMNS
        assert len(bbox_data) == len(sample_csv_data)
    
    def test_get_column_statistics(self, qapp, sample_csv_data):
        """Test column statistics calculation."""
        parser = CSVParser()
        parser.data = sample_csv_data
        
        # Test numeric column
        numeric_col = 'AreaShape_Area'
        stats = parser.get_column_statistics(numeric_col)
        
        assert stats is not None
        assert stats['name'] == numeric_col
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'median' in stats
        
        # Verify statistical values are reasonable
        column_data = sample_csv_data[numeric_col]
        assert abs(stats['mean'] - column_data.mean()) < 1e-10
        assert abs(stats['min'] - column_data.min()) < 1e-10
        assert abs(stats['max'] - column_data.max()) < 1e-10
        
        # Test non-existent column
        stats = parser.get_column_statistics('NonExistentColumn')
        assert stats is None
    
    def test_filter_data(self, qapp, sample_csv_data):
        """Test data filtering functionality."""
        parser = CSVParser()
        parser.data = sample_csv_data
        
        # Test range filtering
        area_column = 'AreaShape_Area'
        original_mean = sample_csv_data[area_column].mean()
        
        conditions = {
            area_column: {
                'min': original_mean,
                'max': sample_csv_data[area_column].max()
            }
        }
        
        filtered_data = parser.filter_data(conditions)
        assert filtered_data is not None
        assert len(filtered_data) <= len(sample_csv_data)
        assert (filtered_data[area_column] >= original_mean).all()
        
        # Test value filtering
        object_numbers = [1, 2, 3, 4, 5]
        conditions = {
            'ObjectNumber': {
                'values': object_numbers
            }
        }
        
        filtered_data = parser.filter_data(conditions)
        assert len(filtered_data) == len(object_numbers)
        assert filtered_data['ObjectNumber'].isin(object_numbers).all()
    
    def test_get_data_sample(self, qapp, sample_csv_data):
        """Test data sampling functionality."""
        parser = CSVParser()
        
        # Test empty state
        sample = parser.get_data_sample()
        assert sample is None
        
        # Test with data smaller than sample size
        parser.data = sample_csv_data
        sample = parser.get_data_sample(2000)  # Larger than sample data
        
        assert sample is not None
        assert len(sample) == len(sample_csv_data)
        
        # Test with data larger than sample size
        sample = parser.get_data_sample(100)  # Smaller than sample data
        assert len(sample) == 100
        assert list(sample.columns) == list(sample_csv_data.columns)
    
    def test_export_filtered_data(self, qapp, temp_dir, sample_csv_data):
        """Test filtered data export functionality."""
        parser = CSVParser()
        parser.data = sample_csv_data
        parser.metadata = {'file_path': 'original.csv', 'row_count': len(sample_csv_data)}
        
        # Create filtered subset
        filtered_data = sample_csv_data.head(100)
        output_file = temp_dir / "exported_data.csv"
        
        # Test export with metadata
        success = parser.export_filtered_data(filtered_data, str(output_file), include_metadata=True)
        assert success is True
        assert output_file.exists()
        
        # Verify exported content
        exported_data = pd.read_csv(output_file, comment='#')
        assert len(exported_data) == 100
        assert list(exported_data.columns) == list(sample_csv_data.columns)
        
        # Verify metadata in file
        with open(output_file, 'r') as f:
            content = f.read()
            assert "# CellSorter Filtered Export" in content
            assert "# Original rows:" in content
            assert "# Filtered rows:" in content
    
    def test_get_info(self, qapp, sample_csv_data):
        """Test dataset information retrieval."""
        parser = CSVParser()
        
        # Test empty state
        info = parser.get_info()
        assert info == {}
        
        # Test with loaded data
        parser.data = sample_csv_data
        parser.current_file_path = "/test/path.csv"
        parser.metadata = {
            'has_required_columns': True,
            'row_count': len(sample_csv_data),
            'parse_time_seconds': 1.5
        }
        
        info = parser.get_info()
        assert info['file_path'] == "/test/path.csv"
        assert info['shape'] == sample_csv_data.shape
        assert 'columns' in info
        assert 'numeric_columns' in info
        assert 'memory_usage_mb' in info
        assert info['has_bounding_boxes'] is True
        assert info['row_count'] == len(sample_csv_data)
    
    def test_cleanup(self, qapp):
        """Test resource cleanup."""
        parser = CSVParser()
        
        # Set up some state
        parser.data = pd.DataFrame({'A': [1, 2, 3]})
        parser.metadata = {'test': 'value'}
        parser.current_file_path = "/test/path.csv"
        
        # Cleanup
        parser.cleanup()
        
        assert parser.data is None
        assert len(parser.metadata) == 0
        assert parser.current_file_path is None


@pytest.mark.performance
class TestCSVParserPerformance:
    """Test CSV parser performance requirements."""
    
    @pytest.mark.slow
    def test_large_csv_performance(self, qapp, large_csv_file, performance_thresholds):
        """Test parsing performance for large CSV files."""
        parser = CSVParser()
        
        # Track loading time
        start_time = time.time()
        loading_completed = {'done': False, 'error': None}
        
        def on_loaded(file_path):
            loading_completed['done'] = True
            loading_completed['load_time'] = time.time() - start_time
        
        def on_failed(error):
            loading_completed['done'] = True
            loading_completed['error'] = error
        
        parser.csv_loaded.connect(on_loaded)
        parser.csv_load_failed.connect(on_failed)
        
        # Start loading
        parser.load_csv(str(large_csv_file))
        
        # Wait for completion with generous timeout
        timeout = 60  # 60 seconds
        start_wait = time.time()
        
        while not loading_completed['done']:
            qapp.processEvents()
            if (time.time() - start_wait) > timeout:
                pytest.fail("CSV parsing timed out")
            time.sleep(0.01)
        
        # Verify performance requirement
        if loading_completed.get('error'):
            pytest.fail(f"CSV parsing failed: {loading_completed['error']}")
        
        load_time = loading_completed.get('load_time', float('inf'))
        row_count = len(parser.data)
        
        # Target: 3 seconds for 50K records
        target_time = performance_thresholds['csv_parse_time_50k'] * (row_count / 50000)
        tolerance_factor = 3.0  # Allow extra tolerance for test environment
        
        assert load_time <= target_time * tolerance_factor, \
            f"CSV parsing too slow: {load_time:.2f}s > {target_time * tolerance_factor:.2f}s for {row_count:,} rows"
    
    def test_memory_usage_large_csv(self, qapp, large_csv_data):
        """Test memory usage with large CSV datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        parser = CSVParser()
        parser.data = large_csv_data
        
        current_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable
        data_size_mb = large_csv_data.memory_usage(deep=True).sum() / (1024 * 1024)
        max_acceptable_increase = data_size_mb * 3  # Allow 3x for processing overhead
        
        assert memory_increase < max_acceptable_increase, \
            f"Memory usage too high: {memory_increase:.1f}MB > {max_acceptable_increase:.1f}MB"
        
        # Cleanup
        parser.cleanup()
    
    def test_filtering_performance(self, qapp, large_csv_data):
        """Test data filtering performance."""
        parser = CSVParser()
        parser.data = large_csv_data
        
        # Test multiple filtering operations
        start_time = time.time()
        
        for i in range(10):
            conditions = {
                'AreaShape_Area': {
                    'min': 50 + i * 5,
                    'max': 200 - i * 5
                }
            }
            filtered_data = parser.filter_data(conditions)
            assert filtered_data is not None
        
        elapsed_time = time.time() - start_time
        
        # Should complete 10 filtering operations quickly
        assert elapsed_time < 5.0, f"Filtering operations too slow: {elapsed_time:.2f}s"
    
    def test_statistics_calculation_performance(self, qapp, large_csv_data):
        """Test column statistics calculation performance."""
        parser = CSVParser()
        parser.data = large_csv_data
        
        numeric_columns = parser.get_numeric_columns()
        
        start_time = time.time()
        
        # Calculate statistics for all numeric columns
        for column in numeric_columns:
            stats = parser.get_column_statistics(column)
            assert stats is not None
        
        elapsed_time = time.time() - start_time
        
        # Should calculate stats for all columns quickly
        max_time = len(numeric_columns) * 0.1  # 100ms per column
        assert elapsed_time < max_time, \
            f"Statistics calculation too slow: {elapsed_time:.2f}s for {len(numeric_columns)} columns"


@pytest.mark.integration
class TestCSVParserIntegration:
    """Test CSV parser integration with other components."""
    
    def test_error_handler_integration(self, qapp, temp_dir):
        """Test integration with error handling system."""
        parser = CSVParser()
        
        # Try to load nonexistent file
        nonexistent_file = temp_dir / "nonexistent.csv"
        
        error_occurred = {'error': None}
        
        def capture_error(error_msg):
            error_occurred['error'] = error_msg
        
        parser.csv_load_failed.connect(capture_error)
        parser.load_csv(str(nonexistent_file))
        
        # Wait for error
        start_time = time.time()
        while error_occurred['error'] is None and (time.time() - start_time) < 5:
            qapp.processEvents()
            time.sleep(0.01)
        
        assert error_occurred['error'] is not None
        assert "File not found" in error_occurred['error']
    
    def test_thread_safety(self, qapp, sample_csv_file):
        """Test thread safety of CSV parsing."""
        parser = CSVParser()
        
        # Start multiple parse operations (second should cancel first)
        parser.load_csv(str(sample_csv_file))
        
        # Immediately start another parse
        parser.load_csv(str(sample_csv_file))
        
        # Should not crash or cause issues
        results = {'loaded': 0, 'failed': 0}
        
        def on_loaded(path):
            results['loaded'] += 1
        
        def on_failed(error):
            results['failed'] += 1
        
        parser.csv_loaded.connect(on_loaded)
        parser.csv_load_failed.connect(on_failed)
        
        # Wait for completion
        start_time = time.time()
        while (results['loaded'] + results['failed']) == 0 and (time.time() - start_time) < 10:
            qapp.processEvents()
            time.sleep(0.01)
        
        # Should have at least one result
        assert (results['loaded'] + results['failed']) > 0
    
    def test_data_consistency_with_requirements(self, qapp, sample_csv_data):
        """Test that parsed data meets product requirements."""
        parser = CSVParser()
        parser.data = sample_csv_data
        parser.metadata = {'has_required_columns': True, 'bounding_box_columns': REQUIRED_CSV_COLUMNS}
        
        # FR1.2: Required bounding box columns must be present
        bbox_data = parser.get_bounding_box_data()
        assert bbox_data is not None
        
        for col in REQUIRED_CSV_COLUMNS:
            assert col in bbox_data.columns
        
        # Verify bounding box data validity
        min_x = bbox_data['AreaShape_BoundingBoxMinimum_X']
        max_x = bbox_data['AreaShape_BoundingBoxMaximum_X']
        min_y = bbox_data['AreaShape_BoundingBoxMinimum_Y']
        max_y = bbox_data['AreaShape_BoundingBoxMaximum_Y']
        
        # Min should be less than max
        assert (min_x < max_x).all(), "Invalid bounding box: min_x >= max_x"
        assert (min_y < max_y).all(), "Invalid bounding box: min_y >= max_y"
        
        # Coordinates should be non-negative
        assert (min_x >= 0).all(), "Negative X coordinates found"
        assert (min_y >= 0).all(), "Negative Y coordinates found"