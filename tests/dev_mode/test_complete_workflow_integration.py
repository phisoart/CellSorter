"""
Complete Integration Test Suite - DEV Mode
이미지 로드부터 프로토콜 내보내기까지 전체 워크플로우를 headless 모드에서 실행하고 검증
"""

import unittest
import tempfile
import os
import numpy as np
import pandas as pd
import json
from pathlib import Path
from PIL import Image
from unittest.mock import Mock, patch
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Import test framework
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.headless.testing.framework import UITestCase

from src.headless.mode_manager import ModeManager, AppMode
from src.models.csv_parser import CSVParser
from src.models.coordinate_transformer import CoordinateTransformer
from src.models.selection_manager import SelectionManager
from src.models.extractor import Extractor
from src.models.template_manager import TemplateManager
from src.models.session_manager import SessionManager


class TestCompleteWorkflowIntegration(UITestCase):
    """Complete workflow integration tests in DEV mode."""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Ensure we're in dev mode
        mode_manager = ModeManager()
        mode_manager.set_mode(AppMode.DEV)
        self.assertTrue(mode_manager.is_dev_mode())
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample files
        self.sample_image_file = self._create_sample_image()
        self.sample_csv_file = self._create_sample_csv()
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(str(self.temp_dir), ignore_errors=True)
        super().tearDown()
    
    def _create_sample_image(self):
        """Create a sample TIFF image file."""
        # Create a realistic test image (1024x1024 RGB)
        np.random.seed(42)
        image_array = np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8)
        image = Image.fromarray(image_array)
        
        image_path = self.temp_dir / "test_image.tiff"
        image.save(image_path, format='TIFF')
        return image_path
    
    def _create_sample_csv(self):
        """Create a sample CSV file with realistic CellProfiler data."""
        np.random.seed(42)
        
        # Generate realistic CellProfiler output data
        n_cells = 100
        data = {
            'ImageNumber': [1] * n_cells,
            'ObjectNumber': list(range(1, n_cells + 1)),
            'Intensity_MedianIntensity_DAPI': np.random.normal(300, 50, n_cells),
            'Intensity_MedianIntensity_CK7': np.random.normal(150, 30, n_cells),
            'Intensity_MedianIntensity_CK20': np.random.normal(200, 40, n_cells),
            'Intensity_MedianIntensity_CDX2': np.random.normal(180, 35, n_cells),
            'AreaShape_BoundingBoxMinimum_X': np.random.uniform(50, 900, n_cells),
            'AreaShape_BoundingBoxMinimum_Y': np.random.uniform(50, 900, n_cells),
            'AreaShape_BoundingBoxMaximum_X': np.random.uniform(60, 910, n_cells),
            'AreaShape_BoundingBoxMaximum_Y': np.random.uniform(60, 910, n_cells),
            'AreaShape_Center_X': np.random.uniform(55, 905, n_cells),
            'AreaShape_Center_Y': np.random.uniform(55, 905, n_cells),
        }
        
        # Ensure bounding box max > min
        for i in range(n_cells):
            data['AreaShape_BoundingBoxMaximum_X'][i] = max(
                data['AreaShape_BoundingBoxMaximum_X'][i],
                data['AreaShape_BoundingBoxMinimum_X'][i] + 10
            )
            data['AreaShape_BoundingBoxMaximum_Y'][i] = max(
                data['AreaShape_BoundingBoxMaximum_Y'][i],
                data['AreaShape_BoundingBoxMinimum_Y'][i] + 10
            )
        
        df = pd.DataFrame(data)
        csv_path = self.temp_dir / "test_data.csv"
        df.to_csv(csv_path, index=False)
        return csv_path
    
    @pytest.fixture
    def main_window_adapter(self):
        """Create MainWindow adapter for headless operations."""
        adapter = MainWindowAdapter()
        yield adapter
        adapter.cleanup()
    
    def test_01_image_loading_workflow(self, sample_image_file, main_window_adapter):
        """Test complete image loading workflow."""
        # Step 1: Initialize image handler
        image_handler = ImageHandler()
        
        # Step 2: Load image in headless mode
        success = image_handler.load_image(str(sample_image_file))
        assert success, "Image loading should succeed"
        
        # Step 3: Verify image properties
        assert image_handler.current_image is not None
        assert image_handler.image_path == str(sample_image_file)
        assert image_handler.get_image_size() == (1024, 1024)
        
        # Step 4: Test image processing capabilities
        scaled_image = image_handler.get_scaled_image(0.5)
        assert scaled_image is not None
        
        # Step 5: Verify memory management
        initial_memory = image_handler.get_memory_usage()
        assert initial_memory > 0
        
        print(f"✓ Image loading workflow completed successfully")
        print(f"  - Image size: {image_handler.get_image_size()}")
        print(f"  - Memory usage: {initial_memory:.2f} MB")
    
    def test_02_csv_processing_workflow(self, sample_csv_file, main_window_adapter):
        """Test complete CSV processing workflow."""
        # Step 1: Initialize CSV parser
        csv_parser = CSVParser()
        
        # Step 2: Load and parse CSV
        success = csv_parser.load_csv(str(sample_csv_file))
        assert success, "CSV loading should succeed"
        
        # Step 3: Verify data structure
        assert csv_parser.dataframe is not None
        assert len(csv_parser.dataframe) == 100
        assert 'Intensity_MedianIntensity_DAPI' in csv_parser.dataframe.columns
        
        # Step 4: Test data validation
        numeric_cols = csv_parser.get_numeric_columns()
        assert len(numeric_cols) >= 4  # At least 4 intensity columns
        
        # Step 5: Test data filtering capabilities
        filtered_data = csv_parser.filter_data({'Intensity_MedianIntensity_DAPI': (250, 350)})
        assert len(filtered_data) > 0
        assert len(filtered_data) < len(csv_parser.dataframe)
        
        print(f"✓ CSV processing workflow completed successfully")
        print(f"  - Total cells: {len(csv_parser.dataframe)}")
        print(f"  - Numeric columns: {len(numeric_cols)}")
        print(f"  - Filtered cells: {len(filtered_data)}")
    
    def test_03_coordinate_calibration_workflow(self, main_window_adapter):
        """Test complete coordinate calibration workflow."""
        # Step 1: Initialize coordinate transformer
        transformer = CoordinateTransformer()
        
        # Step 2: Add calibration points (simulating user clicks)
        success1 = transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "Top Left")
        success2 = transformer.add_calibration_point(900, 800, 9000.0, 8000.0, "Bottom Right")
        
        assert success1 and success2, "Calibration points should be added successfully"
        
        # Step 3: Verify calibration
        assert transformer.is_calibrated
        assert len(transformer.calibration_points) == 2
        
        # Step 4: Test coordinate transformation
        result = transformer.pixel_to_stage(500, 400)
        assert result is not None
        assert result.confidence > 0.8  # High confidence expected
        
        # Step 5: Test inverse transformation accuracy
        pixel_coords = transformer.stage_to_pixel(result.stage_x, result.stage_y)
        assert pixel_coords is not None
        
        # Should be close to original coordinates
        tolerance = 5.0
        assert abs(pixel_coords[0] - 500) < tolerance
        assert abs(pixel_coords[1] - 400) < tolerance
        
        # Step 6: Test calibration export/import
        calibration_data = transformer.export_calibration()
        assert calibration_data is not None
        
        new_transformer = CoordinateTransformer()
        import_success = new_transformer.import_calibration(calibration_data)
        assert import_success
        assert new_transformer.is_calibrated
        
        print(f"✓ Coordinate calibration workflow completed successfully")
        print(f"  - Calibration points: {len(transformer.calibration_points)}")
        print(f"  - Transform confidence: {result.confidence:.3f}")
        print(f"  - Transform accuracy: {abs(pixel_coords[0] - 500):.1f}, {abs(pixel_coords[1] - 400):.1f} pixels")
    
    def test_04_selection_management_workflow(self, sample_csv_file, main_window_adapter):
        """Test complete selection management workflow."""
        # Step 1: Load data
        csv_parser = CSVParser()
        csv_parser.load_csv(str(sample_csv_file))
        
        # Step 2: Initialize selection manager
        selection_manager = SelectionManager()
        
        # Step 3: Create selections based on intensity criteria
        high_dapi_indices = csv_parser.dataframe[
            csv_parser.dataframe['Intensity_MedianIntensity_DAPI'] > 320
        ].index.tolist()
        
        high_ck7_indices = csv_parser.dataframe[
            csv_parser.dataframe['Intensity_MedianIntensity_CK7'] > 160
        ].index.tolist()
        
        # Step 4: Add selections
        selection1_id = selection_manager.add_selection(high_dapi_indices[:20], "High DAPI")
        selection2_id = selection_manager.add_selection(high_ck7_indices[:15], "High CK7")
        
        assert selection1_id is not None
        assert selection2_id is not None
        
        # Step 5: Verify selection properties
        assert len(selection_manager.selections) == 2
        table_data = selection_manager.get_selection_table_data()
        assert len(table_data) == 2
        
        # Step 6: Test selection statistics
        stats = selection_manager.get_statistics()
        assert stats['total_selections'] == 2
        assert stats['active_selections'] == 2
        assert stats['total_cells'] == 35  # 20 + 15
        
        # Step 7: Test export functionality
        export_data = selection_manager.export_selections_data()
        assert len(export_data) == 2
        assert all('cell_indices' in item for item in export_data)
        
        print(f"✓ Selection management workflow completed successfully")
        print(f"  - Total selections: {stats['total_selections']}")
        print(f"  - Total selected cells: {stats['total_cells']}")
        print(f"  - Well assignments: {[item['well'] for item in export_data]}")
    
    def test_05_protocol_export_workflow(self, sample_csv_file, sample_image_file, temp_dir, main_window_adapter):
        """Test complete protocol export workflow."""
        # Step 1: Set up complete analysis pipeline
        csv_parser = CSVParser()
        csv_parser.load_csv(str(sample_csv_file))
        
        transformer = CoordinateTransformer()
        transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "Top Left")
        transformer.add_calibration_point(900, 800, 9000.0, 8000.0, "Bottom Right")
        
        selection_manager = SelectionManager()
        
        # Step 2: Create realistic selections
        high_intensity_indices = csv_parser.dataframe[
            (csv_parser.dataframe['Intensity_MedianIntensity_DAPI'] > 300) &
            (csv_parser.dataframe['Intensity_MedianIntensity_CK7'] > 150)
        ].index.tolist()[:10]
        
        selection_manager.add_selection(high_intensity_indices, "Target Cells")
        
        # Step 3: Initialize extractor
        extractor = Extractor()
        
        # Step 4: Create bounding boxes from CSV data
        bounding_boxes = []
        for _, row in csv_parser.dataframe.iterrows():
            from src.models.extractor import BoundingBox
            bbox = BoundingBox(
                row['AreaShape_BoundingBoxMinimum_X'],
                row['AreaShape_BoundingBoxMinimum_Y'],
                row['AreaShape_BoundingBoxMaximum_X'],
                row['AreaShape_BoundingBoxMaximum_Y']
            )
            bounding_boxes.append(bbox)
        
        # Step 5: Generate extraction points
        selections_data = selection_manager.export_selections_data()
        extraction_points = extractor.create_extraction_points(
            selections_data, bounding_boxes, transformer, (1024, 1024)
        )
        
        assert len(extraction_points) == 10  # Should match selection size
        
        # Step 6: Export protocol file
        protocol_path = temp_dir / "test_protocol.cxprotocol"
        success = extractor.export_protocol(extraction_points, str(protocol_path))
        assert success, "Protocol export should succeed"
        
        # Step 7: Verify protocol file
        assert protocol_path.exists()
        assert protocol_path.stat().st_size > 0
        
        # Step 8: Validate protocol content
        with open(protocol_path, 'r') as f:
            content = f.read()
            assert '[EXTRACTION_POINTS]' in content
            assert 'Target Cells' in content
            assert str(len(extraction_points)) in content or len(content.split('\n')) > 10
        
        print(f"✓ Protocol export workflow completed successfully")
        print(f"  - Extraction points: {len(extraction_points)}")
        print(f"  - Protocol file size: {protocol_path.stat().st_size} bytes")
        print(f"  - Output path: {protocol_path}")
    
    def test_06_template_system_workflow(self, temp_dir, main_window_adapter):
        """Test complete template system workflow."""
        # Step 1: Initialize template manager
        template_manager = TemplateManager()
        
        # Step 2: Create custom template
        template_data = {
            'name': 'Test Analysis Template',
            'description': 'Automated test template',
            'markers': ['DAPI', 'CK7', 'CK20', 'CDX2'],
            'settings': {
                'intensity_threshold': 200,
                'size_filter_min': 50,
                'size_filter_max': 1000
            }
        }
        
        # Step 3: Save template
        template_path = temp_dir / "test_template.json"
        success = template_manager.save_template(template_data, str(template_path))
        assert success, "Template saving should succeed"
        
        # Step 4: Load template
        loaded_template = template_manager.load_template(str(template_path))
        assert loaded_template is not None
        assert loaded_template['name'] == template_data['name']
        assert len(loaded_template['markers']) == 4
        
        # Step 5: Apply template (simulate)
        applied_settings = template_manager.apply_template(loaded_template)
        assert applied_settings is not None
        assert 'intensity_threshold' in applied_settings
        
        # Step 6: Test template validation
        is_valid = template_manager.validate_template(loaded_template)
        assert is_valid, "Template should be valid"
        
        print(f"✓ Template system workflow completed successfully")
        print(f"  - Template: {loaded_template['name']}")
        print(f"  - Markers: {len(loaded_template['markers'])}")
        print(f"  - Settings: {len(loaded_template['settings'])} parameters")
    
    def test_07_session_save_load_workflow(self, sample_csv_file, sample_image_file, temp_dir, main_window_adapter):
        """Test complete session save/load workflow."""
        # Step 1: Create complete session state
        session_manager = SessionManager()
        
        # Load all components
        csv_parser = CSVParser()
        csv_parser.load_csv(str(sample_csv_file))
        
        image_handler = ImageHandler()
        image_handler.load_image(str(sample_image_file))
        
        transformer = CoordinateTransformer()
        transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "P1")
        transformer.add_calibration_point(900, 800, 9000.0, 8000.0, "P2")
        
        selection_manager = SelectionManager()
        test_indices = list(range(10))
        selection_manager.add_selection(test_indices, "Test Selection")
        
        # Step 2: Save session
        session_data = {
            'image_path': str(sample_image_file),
            'csv_path': str(sample_csv_file),
            'calibration': transformer.export_calibration(),
            'selections': selection_manager.export_selections_data(),
            'metadata': {
                'created': '2024-12-28',
                'version': '1.0'
            }
        }
        
        session_path = temp_dir / "test_session.json"
        success = session_manager.save_session(session_data, str(session_path))
        assert success, "Session saving should succeed"
        
        # Step 3: Load session
        loaded_session = session_manager.load_session(str(session_path))
        assert loaded_session is not None
        assert loaded_session['image_path'] == str(sample_image_file)
        assert loaded_session['csv_path'] == str(sample_csv_file)
        assert 'calibration' in loaded_session
        assert 'selections' in loaded_session
        
        # Step 4: Restore session state
        # Restore calibration
        new_transformer = CoordinateTransformer()
        restore_success = new_transformer.import_calibration(loaded_session['calibration'])
        assert restore_success
        assert new_transformer.is_calibrated
        
        # Restore selections
        new_selection_manager = SelectionManager()
        for sel_data in loaded_session['selections']:
            new_selection_manager.add_selection(
                sel_data['cell_indices'], 
                sel_data['name']
            )
        assert len(new_selection_manager.selections) == 1
        
        print(f"✓ Session save/load workflow completed successfully")
        print(f"  - Session file size: {session_path.stat().st_size} bytes")
        print(f"  - Restored calibration: {new_transformer.is_calibrated}")
        print(f"  - Restored selections: {len(new_selection_manager.selections)}")
    
    def test_08_error_handling_workflow(self, temp_dir, main_window_adapter):
        """Test error handling across the complete workflow."""
        # Test 1: Invalid image file
        image_handler = ImageHandler()
        invalid_image_path = temp_dir / "nonexistent.tiff"
        success = image_handler.load_image(str(invalid_image_path))
        assert not success, "Loading nonexistent image should fail gracefully"
        
        # Test 2: Invalid CSV file
        csv_parser = CSVParser()
        invalid_csv_path = temp_dir / "nonexistent.csv"
        success = csv_parser.load_csv(str(invalid_csv_path))
        assert not success, "Loading nonexistent CSV should fail gracefully"
        
        # Test 3: Invalid calibration
        transformer = CoordinateTransformer()
        result = transformer.pixel_to_stage(100, 100)
        assert result is None, "Transformation without calibration should return None"
        
        # Test 4: Empty selections
        selection_manager = SelectionManager()
        stats = selection_manager.get_statistics()
        assert stats['total_selections'] == 0
        assert stats['total_cells'] == 0
        
        # Test 5: Protocol export without data
        extractor = Extractor()
        protocol_path = temp_dir / "empty_protocol.cxprotocol"
        success = extractor.export_protocol([], str(protocol_path))
        # Should handle empty data gracefully
        
        print(f"✓ Error handling workflow completed successfully")
        print(f"  - All error cases handled gracefully")
    
    def test_complete_end_to_end_workflow(self):
        """Test complete end-to-end workflow integration."""
        print("\n🚀 Starting complete end-to-end workflow test...")
        
        # Step 1: Initialize all components (mock image handler)
        print("  1. Initializing components...")
        with patch('src.models.image_handler.ImageHandler') as mock_image_handler:
            # Mock the image handler to avoid GUI initialization
            mock_handler = Mock()
            mock_handler.load_image.return_value = True
            mock_handler.get_image_size.return_value = (1024, 1024)
            mock_handler.current_image = Mock()
            mock_handler.image_path = str(self.sample_image_file)
            mock_image_handler.return_value = mock_handler
            
            csv_parser = CSVParser()
            transformer = CoordinateTransformer()
            selection_manager = SelectionManager()
            extractor = Extractor()
            session_manager = SessionManager()
            
            # Step 2: Load data
            print("  2. Loading data...")
            image_handler = mock_image_handler()
            image_success = image_handler.load_image(str(self.sample_image_file))
            csv_success = csv_parser.load_csv(str(self.sample_csv_file))
            self.assertTrue(image_success and csv_success, "Data loading should succeed")
            
            # Step 3: Calibrate coordinates
            print("  3. Calibrating coordinates...")
            cal_success1 = transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "Reference 1")
            cal_success2 = transformer.add_calibration_point(900, 800, 9000.0, 8000.0, "Reference 2")
            self.assertTrue(cal_success1 and cal_success2, "Calibration should succeed")
            self.assertTrue(transformer.is_calibrated)
            
            # Step 4: Create selections
            print("  4. Creating cell selections...")
            high_dapi = csv_parser.dataframe[
                csv_parser.dataframe['Intensity_MedianIntensity_DAPI'] > 320
            ].index.tolist()[:8]
            
            sel1_id = selection_manager.add_selection(high_dapi, "High DAPI Expression")
            self.assertTrue(sel1_id, "Selection should be created successfully")
            
            # Step 5: Generate extraction points
            print("  5. Generating extraction points...")
            bounding_boxes = []
            for _, row in csv_parser.dataframe.iterrows():
                from src.models.extractor import BoundingBox
                bbox = BoundingBox(
                    row['AreaShape_BoundingBoxMinimum_X'],
                    row['AreaShape_BoundingBoxMinimum_Y'],
                    row['AreaShape_BoundingBoxMaximum_X'],
                    row['AreaShape_BoundingBoxMaximum_Y']
                )
                bounding_boxes.append(bbox)
            
            selections_data = selection_manager.export_selections_data()
            extraction_points = extractor.create_extraction_points(
                selections_data, bounding_boxes, transformer, (1024, 1024)
            )
            
            self.assertEqual(len(extraction_points), 8, f"Expected 8 extraction points, got {len(extraction_points)}")
            
            # Step 6: Export protocol
            print("  6. Exporting protocol...")
            protocol_path = self.temp_dir / "complete_workflow_protocol.cxprotocol"
            export_success = extractor.export_protocol(extraction_points, str(protocol_path))
            self.assertTrue(export_success, "Protocol export should succeed")
            self.assertTrue(protocol_path.exists() and protocol_path.stat().st_size > 0)
            
            print("✅ Complete end-to-end workflow test PASSED!")
            print(f"   - Extraction points: {len(extraction_points)}")
            print(f"   - Protocol file size: {protocol_path.stat().st_size} bytes")
    
    def test_10_stress_test_workflow(self, temp_dir, main_window_adapter):
        """Stress test the complete workflow with larger datasets."""
        print("\n🔥 Starting stress test workflow...")
        
        # Create larger test dataset
        np.random.seed(42)
        n_cells = 1000  # Larger dataset
        
        large_data = {
            'ImageNumber': [1] * n_cells,
            'ObjectNumber': list(range(1, n_cells + 1)),
            'Intensity_MedianIntensity_DAPI': np.random.normal(300, 50, n_cells),
            'Intensity_MedianIntensity_CK7': np.random.normal(150, 30, n_cells),
            'Intensity_MedianIntensity_CK20': np.random.normal(200, 40, n_cells),
            'Intensity_MedianIntensity_CDX2': np.random.normal(180, 35, n_cells),
            'AreaShape_BoundingBoxMinimum_X': np.random.uniform(0, 1900, n_cells),
            'AreaShape_BoundingBoxMinimum_Y': np.random.uniform(0, 1900, n_cells),
            'AreaShape_BoundingBoxMaximum_X': np.random.uniform(10, 1910, n_cells),
            'AreaShape_BoundingBoxMaximum_Y': np.random.uniform(10, 1910, n_cells),
        }
        
        # Ensure proper bounding boxes
        for i in range(n_cells):
            large_data['AreaShape_BoundingBoxMaximum_X'][i] = max(
                large_data['AreaShape_BoundingBoxMaximum_X'][i],
                large_data['AreaShape_BoundingBoxMinimum_X'][i] + 10
            )
            large_data['AreaShape_BoundingBoxMaximum_Y'][i] = max(
                large_data['AreaShape_BoundingBoxMaximum_Y'][i],
                large_data['AreaShape_BoundingBoxMinimum_Y'][i] + 10
            )
        
        large_df = pd.DataFrame(large_data)
        large_csv_path = temp_dir / "stress_test_data.csv"
        large_df.to_csv(large_csv_path, index=False)
        
        # Create larger image
        large_image_array = np.random.randint(0, 256, (2048, 2048, 3), dtype=np.uint8)
        large_image = Image.fromarray(large_image_array)
        large_image_path = temp_dir / "stress_test_image.tiff"
        large_image.save(large_image_path, format='TIFF')
        
        # Run workflow with larger data
        print("  Loading large dataset...")
        csv_parser = CSVParser()
        image_handler = ImageHandler()
        
        csv_success = csv_parser.load_csv(str(large_csv_path))
        image_success = image_handler.load_image(str(large_image_path))
        
        assert csv_success and image_success, "Large data loading should succeed"
        
        # Test selection performance with larger dataset
        print("  Testing selection performance...")
        selection_manager = SelectionManager()
        
        # Create multiple large selections
        high_dapi = large_df[large_df['Intensity_MedianIntensity_DAPI'] > 350].index.tolist()
        high_ck7 = large_df[large_df['Intensity_MedianIntensity_CK7'] > 170].index.tolist()
        high_ck20 = large_df[large_df['Intensity_MedianIntensity_CK20'] > 220].index.tolist()
        
        sel1 = selection_manager.add_selection(high_dapi[:50], "High DAPI (Stress)")
        sel2 = selection_manager.add_selection(high_ck7[:40], "High CK7 (Stress)")
        sel3 = selection_manager.add_selection(high_ck20[:30], "High CK20 (Stress)")
        
        assert all([sel1, sel2, sel3]), "Large selections should be created"
        
        # Test extraction with large dataset
        print("  Testing extraction performance...")
        transformer = CoordinateTransformer()
        transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "Stress P1")
        transformer.add_calibration_point(1900, 1800, 19000.0, 18000.0, "Stress P2")
        
        extractor = Extractor()
        bounding_boxes = []
        for _, row in large_df.iterrows():
            from src.models.extractor import BoundingBox
            bbox = BoundingBox(
                row['AreaShape_BoundingBoxMinimum_X'],
                row['AreaShape_BoundingBoxMinimum_Y'],
                row['AreaShape_BoundingBoxMaximum_X'],
                row['AreaShape_BoundingBoxMaximum_Y']
            )
            bounding_boxes.append(bbox)
        
        selections_data = selection_manager.export_selections_data()
        extraction_points = extractor.create_extraction_points(
            selections_data, bounding_boxes, transformer, (2048, 2048)
        )
        
        assert len(extraction_points) == 120, f"Expected 120 extraction points, got {len(extraction_points)}"
        
        # Export large protocol
        print("  Testing large protocol export...")
        stress_protocol_path = temp_dir / "stress_test_protocol.cxprotocol"
        export_success = extractor.export_protocol(extraction_points, str(stress_protocol_path))
        assert export_success, "Large protocol export should succeed"
        
        # Verify performance metrics
        image_memory = image_handler.get_memory_usage()
        protocol_size = stress_protocol_path.stat().st_size
        
        print("✅ Stress test workflow PASSED!")
        print(f"   📊 Stress Test Summary:")
        print(f"   - Processed cells: {len(large_df)}")
        print(f"   - Image size: 2048x2048")
        print(f"   - Memory usage: {image_memory:.2f} MB")
        print(f"   - Extraction points: {len(extraction_points)}")
        print(f"   - Protocol size: {protocol_size / 1024:.1f} KB")
        
        # Memory should be reasonable even with large data
        assert image_memory < 100, "Memory usage should remain reasonable"
        assert protocol_size > 1000, "Large protocol should have substantial content" 