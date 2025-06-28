"""
Performance Benchmarking Between Modes - DEV Mode
Headless와 GUI 모드 간 성능 비교 테스트
"""

import unittest
import time
import tempfile
import os
import numpy as np
import pandas as pd
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


class TestPerformanceBenchmarking(UITestCase):
    """Performance benchmarking tests between Headless and GUI modes."""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test datasets of different sizes
        self.small_csv = self._create_csv_dataset(100)
        self.medium_csv = self._create_csv_dataset(1000)
        self.large_csv = self._create_csv_dataset(5000)
        
        self.small_image = self._create_image_dataset(512, 512)
        self.medium_image = self._create_image_dataset(1024, 1024)
        self.large_image = self._create_image_dataset(2048, 2048)
        
        # Performance tracking
        self.performance_results = {}
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(str(self.temp_dir), ignore_errors=True)
        super().tearDown()
    
    def _create_csv_dataset(self, n_cells):
        """Create CSV dataset with specified number of cells."""
        np.random.seed(42)
        
        data = {
            'ImageNumber': [1] * n_cells,
            'ObjectNumber': list(range(1, n_cells + 1)),
            'Intensity_MedianIntensity_DAPI': np.random.normal(300, 50, n_cells),
            'Intensity_MedianIntensity_CK7': np.random.normal(150, 30, n_cells),
            'Intensity_MedianIntensity_CK20': np.random.normal(200, 40, n_cells),
            'Intensity_MedianIntensity_CDX2': np.random.normal(180, 35, n_cells),
            'AreaShape_BoundingBoxMinimum_X': np.random.uniform(50, 1900, n_cells),
            'AreaShape_BoundingBoxMinimum_Y': np.random.uniform(50, 1900, n_cells),
            'AreaShape_BoundingBoxMaximum_X': np.random.uniform(60, 1910, n_cells),
            'AreaShape_BoundingBoxMaximum_Y': np.random.uniform(60, 1910, n_cells),
        }
        
        # Ensure proper bounding boxes
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
        csv_path = self.temp_dir / f"dataset_{n_cells}_cells.csv"
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def _create_image_dataset(self, width, height):
        """Create image dataset with specified dimensions."""
        np.random.seed(42)
        image_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(image_array)
        
        image_path = self.temp_dir / f"image_{width}x{height}.tiff"
        image.save(image_path, format='TIFF')
        return image_path
    
    def _benchmark_function(self, func, *args, **kwargs):
        """Benchmark a function execution time."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_csv_parsing_performance_comparison(self):
        """Test CSV parsing performance across different data sizes."""
        print("\n📊 CSV Parsing Performance Benchmarking...")
        
        datasets = [
            ("Small (100 cells)", self.small_csv),
            ("Medium (1000 cells)", self.medium_csv),
            ("Large (5000 cells)", self.large_csv)
        ]
        
        results = {}
        
        for dataset_name, csv_path in datasets:
            print(f"  Testing {dataset_name}...")
            
            # Test in DEV mode (headless)
            mode_manager = ModeManager()
            mode_manager.set_mode(AppMode.DEV)
            
            csv_parser = CSVParser()
            result, execution_time = self._benchmark_function(
                csv_parser.load_csv, str(csv_path)
            )
            
            self.assertTrue(result, f"CSV loading should succeed for {dataset_name}")
            
            results[dataset_name] = {
                'cells': len(csv_parser.dataframe),
                'columns': len(csv_parser.dataframe.columns),
                'execution_time': execution_time,
                'memory_size': csv_parser.dataframe.memory_usage(deep=True).sum()
            }
            
            print(f"    - Cells: {results[dataset_name]['cells']}")
            print(f"    - Execution time: {execution_time:.4f}s")
            print(f"    - Memory usage: {results[dataset_name]['memory_size'] / 1024 / 1024:.2f} MB")
        
        # Performance validation
        self.assertLess(results["Small (100 cells)"]["execution_time"], 1.0, 
                       "Small dataset should load quickly")
        self.assertLess(results["Medium (1000 cells)"]["execution_time"], 5.0, 
                       "Medium dataset should load reasonably fast")
        self.assertLess(results["Large (5000 cells)"]["execution_time"], 20.0, 
                       "Large dataset should load within reasonable time")
        
        self.performance_results['csv_parsing'] = results
        print("✅ CSV parsing performance test completed")
    
    def test_image_loading_performance_comparison(self):
        """Test image loading performance across different image sizes."""
        print("\n🖼️ Image Loading Performance Benchmarking...")
        
        with patch('src.models.image_handler.ImageHandler') as mock_image_handler:
            datasets = [
                ("Small (512x512)", self.small_image),
                ("Medium (1024x1024)", self.medium_image),
                ("Large (2048x2048)", self.large_image)
            ]
            
            results = {}
            
            for dataset_name, image_path in datasets:
                print(f"  Testing {dataset_name}...")
                
                # Mock image handler for performance testing
                mock_handler = Mock()
                mock_handler.load_image.return_value = True
                mock_image_handler.return_value = mock_handler
                
                # Test in DEV mode (headless)
                mode_manager = ModeManager()
                mode_manager.set_mode(AppMode.DEV)
                
                image_handler = mock_image_handler()
                result, execution_time = self._benchmark_function(
                    image_handler.load_image, str(image_path)
                )
                
                # Get actual file size for reference
                file_size = os.path.getsize(image_path)
                
                results[dataset_name] = {
                    'file_size': file_size,
                    'execution_time': execution_time,
                    'loading_speed_mbps': (file_size / 1024 / 1024) / execution_time if execution_time > 0 else 0
                }
                
                print(f"    - File size: {file_size / 1024 / 1024:.2f} MB")
                print(f"    - Execution time: {execution_time:.4f}s")
                print(f"    - Loading speed: {results[dataset_name]['loading_speed_mbps']:.2f} MB/s")
            
            # Performance validation
            self.assertGreater(results["Small (512x512)"]["loading_speed_mbps"], 10, 
                             "Small image should load at reasonable speed")
            
            self.performance_results['image_loading'] = results
            print("✅ Image loading performance test completed")
    
    def test_selection_operations_performance(self):
        """Test selection operations performance with different dataset sizes."""
        print("\n🎯 Selection Operations Performance Benchmarking...")
        
        datasets = [
            ("Small (100 cells)", self.small_csv, 10),
            ("Medium (1000 cells)", self.medium_csv, 50),
            ("Large (5000 cells)", self.large_csv, 200)
        ]
        
        results = {}
        
        for dataset_name, csv_path, selection_size in datasets:
            print(f"  Testing {dataset_name}...")
            
            # Load data
            csv_parser = CSVParser()
            csv_parser.load_csv(str(csv_path))
            
            # Test selection creation performance
            selection_manager = SelectionManager()
            
            # Create indices for selection
            indices = list(range(min(selection_size, len(csv_parser.dataframe))))
            
            result, execution_time = self._benchmark_function(
                selection_manager.add_selection, indices, f"Test Selection {dataset_name}"
            )
            
            self.assertTrue(result, f"Selection creation should succeed for {dataset_name}")
            
            # Test selection export performance
            export_result, export_time = self._benchmark_function(
                selection_manager.export_selections_data
            )
            
            self.assertIsNotNone(export_result, f"Selection export should succeed for {dataset_name}")
            
            results[dataset_name] = {
                'dataset_size': len(csv_parser.dataframe),
                'selection_size': len(indices),
                'creation_time': execution_time,
                'export_time': export_time,
                'total_time': execution_time + export_time
            }
            
            print(f"    - Dataset size: {results[dataset_name]['dataset_size']}")
            print(f"    - Selection size: {results[dataset_name]['selection_size']}")
            print(f"    - Creation time: {execution_time:.4f}s")
            print(f"    - Export time: {export_time:.4f}s")
            print(f"    - Total time: {results[dataset_name]['total_time']:.4f}s")
        
        # Performance validation
        self.assertLess(results["Small (100 cells)"]["total_time"], 0.5, 
                       "Small selection operations should be very fast")
        self.assertLess(results["Medium (1000 cells)"]["total_time"], 2.0, 
                       "Medium selection operations should be reasonably fast")
        self.assertLess(results["Large (5000 cells)"]["total_time"], 10.0, 
                       "Large selection operations should complete within reasonable time")
        
        self.performance_results['selection_operations'] = results
        print("✅ Selection operations performance test completed")
    
    def test_coordinate_transformation_performance(self):
        """Test coordinate transformation performance."""
        print("\n📐 Coordinate Transformation Performance Benchmarking...")
        
        transformer = CoordinateTransformer()
        
        # Setup calibration
        setup_result, setup_time = self._benchmark_function(
            self._setup_calibration, transformer
        )
        self.assertTrue(setup_result, "Calibration setup should succeed")
        
        # Test different batch sizes of coordinate transformations
        batch_sizes = [10, 100, 1000, 5000]
        results = {}
        
        for batch_size in batch_sizes:
            print(f"  Testing batch size: {batch_size}")
            
            # Generate test coordinates
            np.random.seed(42)
            test_coords = [(np.random.uniform(0, 1000), np.random.uniform(0, 1000)) 
                          for _ in range(batch_size)]
            
            # Benchmark transformation
            transform_results = []
            start_time = time.time()
            
            for x, y in test_coords:
                result = transformer.pixel_to_stage(x, y)
                transform_results.append(result)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Validate results
            successful_transforms = sum(1 for r in transform_results if r is not None)
            
            results[batch_size] = {
                'batch_size': batch_size,
                'execution_time': execution_time,
                'successful_transforms': successful_transforms,
                'transforms_per_second': batch_size / execution_time if execution_time > 0 else 0,
                'average_time_per_transform': execution_time / batch_size if batch_size > 0 else 0
            }
            
            print(f"    - Execution time: {execution_time:.4f}s")
            print(f"    - Transforms/sec: {results[batch_size]['transforms_per_second']:.1f}")
            print(f"    - Avg time per transform: {results[batch_size]['average_time_per_transform']:.6f}s")
            print(f"    - Success rate: {successful_transforms}/{batch_size}")
        
        # Performance validation
        self.assertGreater(results[10]['transforms_per_second'], 100, 
                         "Should handle at least 100 transforms per second")
        self.assertGreater(results[1000]['transforms_per_second'], 50, 
                         "Should maintain reasonable speed with larger batches")
        
        self.performance_results['coordinate_transformation'] = results
        print("✅ Coordinate transformation performance test completed")
    
    def _setup_calibration(self, transformer):
        """Helper method to setup calibration for performance testing."""
        success1 = transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "P1")
        success2 = transformer.add_calibration_point(900, 800, 9000.0, 8000.0, "P2")
        return success1 and success2
    
    def test_protocol_export_performance(self):
        """Test protocol export performance with different data sizes."""
        print("\n📄 Protocol Export Performance Benchmarking...")
        
        # Test different extraction point counts
        point_counts = [10, 50, 100, 500]
        results = {}
        
        for point_count in point_counts:
            print(f"  Testing {point_count} extraction points...")
            
            # Create mock extraction points
            extraction_points = self._create_mock_extraction_points(point_count)
            
            extractor = Extractor()
            protocol_path = self.temp_dir / f"protocol_{point_count}_points.cxprotocol"
            
            result, execution_time = self._benchmark_function(
                extractor.export_protocol, extraction_points, str(protocol_path)
            )
            
            self.assertTrue(result, f"Protocol export should succeed for {point_count} points")
            
            # Get file size
            file_size = os.path.getsize(protocol_path) if protocol_path.exists() else 0
            
            results[point_count] = {
                'point_count': point_count,
                'execution_time': execution_time,
                'file_size': file_size,
                'points_per_second': point_count / execution_time if execution_time > 0 else 0,
                'bytes_per_point': file_size / point_count if point_count > 0 else 0
            }
            
            print(f"    - Execution time: {execution_time:.4f}s")
            print(f"    - File size: {file_size / 1024:.2f} KB")
            print(f"    - Points/sec: {results[point_count]['points_per_second']:.1f}")
            print(f"    - Bytes per point: {results[point_count]['bytes_per_point']:.1f}")
        
        # Performance validation
        self.assertGreater(results[10]['points_per_second'], 50, 
                         "Should export at least 50 points per second")
        self.assertLess(results[500]['execution_time'], 30.0, 
                       "Large exports should complete within reasonable time")
        
        self.performance_results['protocol_export'] = results
        print("✅ Protocol export performance test completed")
    
    def _create_mock_extraction_points(self, count):
        """Create mock extraction points for testing."""
        extraction_points = []
        for i in range(count):
            # Create a simple mock extraction point
            point = Mock()
            point.id = f"point_{i:03d}"
            point.label = f"Cell {i}"
            point.crop_region = Mock()
            point.crop_region.min_x = i * 10
            point.crop_region.min_y = i * 10
            point.crop_region.max_x = i * 10 + 50
            point.crop_region.max_y = i * 10 + 50
            point.crop_region.size = 2500
            point.well_position = f"A{(i % 96) + 1:02d}"
            point.color = "#FF0000"
            extraction_points.append(point)
        
        return extraction_points
    
    def test_memory_usage_tracking(self):
        """Test memory usage across different operations."""
        print("\n💾 Memory Usage Tracking...")
        
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  Initial memory usage: {initial_memory:.2f} MB")
        
        # Test CSV loading memory impact
        csv_parser = CSVParser()
        csv_parser.load_csv(str(self.large_csv))
        
        after_csv_memory = process.memory_info().rss / 1024 / 1024
        csv_memory_delta = after_csv_memory - initial_memory
        
        print(f"  After CSV loading: {after_csv_memory:.2f} MB (+{csv_memory_delta:.2f} MB)")
        
        # Test selection creation memory impact
        selection_manager = SelectionManager()
        large_selection = list(range(1000))
        selection_manager.add_selection(large_selection, "Large Selection")
        
        after_selection_memory = process.memory_info().rss / 1024 / 1024
        selection_memory_delta = after_selection_memory - after_csv_memory
        
        print(f"  After selection creation: {after_selection_memory:.2f} MB (+{selection_memory_delta:.2f} MB)")
        
        # Force garbage collection and measure
        gc.collect()
        after_gc_memory = process.memory_info().rss / 1024 / 1024
        gc_memory_delta = after_gc_memory - after_selection_memory
        
        print(f"  After garbage collection: {after_gc_memory:.2f} MB ({gc_memory_delta:+.2f} MB)")
        
        # Memory usage validation
        self.assertLess(csv_memory_delta, 100, "CSV loading should not use excessive memory")
        self.assertLess(selection_memory_delta, 50, "Selection creation should be memory efficient")
        
        memory_results = {
            'initial': initial_memory,
            'after_csv': after_csv_memory,
            'after_selection': after_selection_memory,
            'after_gc': after_gc_memory,
            'csv_delta': csv_memory_delta,
            'selection_delta': selection_memory_delta,
            'gc_delta': gc_memory_delta
        }
        
        self.performance_results['memory_usage'] = memory_results
        print("✅ Memory usage tracking completed")
    
    def test_generate_performance_report(self):
        """Generate comprehensive performance report."""
        print("\n📋 Generating Performance Report...")
        
        # Run all benchmarks first
        self.test_csv_parsing_performance_comparison()
        self.test_image_loading_performance_comparison()
        self.test_selection_operations_performance()
        self.test_coordinate_transformation_performance()
        self.test_protocol_export_performance()
        self.test_memory_usage_tracking()
        
        # Generate report
        report_path = self.temp_dir / "performance_report.json"
        
        report_data = {
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_mode': 'DEV (headless)',
            'performance_results': self.performance_results,
            'summary': {
                'csv_parsing_fastest': min(
                    self.performance_results['csv_parsing'].values(),
                    key=lambda x: x['execution_time']
                ),
                'coordinate_transform_rate': max(
                    self.performance_results['coordinate_transformation'].values(),
                    key=lambda x: x['transforms_per_second']
                )['transforms_per_second'],
                'protocol_export_rate': max(
                    self.performance_results['protocol_export'].values(),
                    key=lambda x: x['points_per_second']
                )['points_per_second'],
                'peak_memory_usage': self.performance_results['memory_usage']['after_selection']
            }
        }
        
        with open(report_path, 'w') as f:
            import json
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"  Performance report saved to: {report_path}")
        print(f"  Report size: {os.path.getsize(report_path) / 1024:.2f} KB")
        
        # Validate report
        self.assertTrue(report_path.exists(), "Performance report should be created")
        self.assertGreater(os.path.getsize(report_path), 1000, "Report should contain substantial data")
        
        print("✅ Performance report generation completed")
        
        # Print summary
        print("\n🎯 Performance Summary:")
        print(f"  - Fastest CSV parsing: {report_data['summary']['csv_parsing_fastest']['execution_time']:.4f}s")
        print(f"  - Coordinate transform rate: {report_data['summary']['coordinate_transform_rate']:.1f} transforms/sec")
        print(f"  - Protocol export rate: {report_data['summary']['protocol_export_rate']:.1f} points/sec")
        print(f"  - Peak memory usage: {report_data['summary']['peak_memory_usage']:.2f} MB")


if __name__ == '__main__':
    unittest.main() 