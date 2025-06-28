"""
Simple Performance Benchmarking Test
"""

import unittest
import time
import tempfile
import os
import numpy as np
import pandas as pd
from pathlib import Path


class TestSimplePerformance(unittest.TestCase):
    """Simple performance tests."""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(str(self.temp_dir), ignore_errors=True)
    
    def test_csv_performance(self):
        """Test CSV processing performance."""
        print("\n📊 Testing CSV Performance...")
        
        # Create test data
        n_cells = 1000
        data = {
            'ImageNumber': [1] * n_cells,
            'ObjectNumber': list(range(1, n_cells + 1)),
            'Intensity_MedianIntensity_DAPI': np.random.normal(300, 50, n_cells),
            'Intensity_MedianIntensity_CK7': np.random.normal(150, 30, n_cells),
        }
        
        df = pd.DataFrame(data)
        csv_path = self.temp_dir / "test_data.csv"
        df.to_csv(csv_path, index=False)
        
        # Benchmark CSV loading
        start_time = time.time()
        loaded_df = pd.read_csv(csv_path)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"  CSV loading time: {execution_time:.4f}s")
        print(f"  Rows loaded: {len(loaded_df)}")
        
        self.assertEqual(len(loaded_df), n_cells)
        self.assertLess(execution_time, 5.0, "CSV loading should be fast")
        
        print("✅ CSV performance test completed")
    
    def test_coordinate_transformation_performance(self):
        """Test coordinate transformation performance."""
        print("\n📐 Testing Coordinate Transformation Performance...")
        
        # Simple coordinate transformation simulation
        n_points = 1000
        
        start_time = time.time()
        
        # Simulate coordinate transformations
        results = []
        for i in range(n_points):
            x = i * 1.5 + 100  # Simple transformation
            y = i * 1.2 + 200
            results.append((x, y))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        transforms_per_second = n_points / execution_time if execution_time > 0 else 0
        
        print(f"  Transformation time: {execution_time:.4f}s")
        print(f"  Points transformed: {len(results)}")
        print(f"  Transforms per second: {transforms_per_second:.1f}")
        
        self.assertEqual(len(results), n_points)
        self.assertGreater(transforms_per_second, 1000, "Should handle many transforms per second")
        
        print("✅ Coordinate transformation performance test completed")
    
    def test_memory_usage(self):
        """Test memory usage tracking."""
        print("\n💾 Testing Memory Usage...")
        
        try:
            import psutil
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"  Initial memory: {initial_memory:.2f} MB")
            
            # Create some data
            large_data = np.random.randint(0, 255, (1000, 1000), dtype=np.uint8)
            
            after_data_memory = process.memory_info().rss / 1024 / 1024
            memory_delta = after_data_memory - initial_memory
            
            print(f"  After data creation: {after_data_memory:.2f} MB (+{memory_delta:.2f} MB)")
            
            # Clean up
            del large_data
            import gc
            gc.collect()
            
            after_cleanup_memory = process.memory_info().rss / 1024 / 1024
            cleanup_delta = after_cleanup_memory - after_data_memory
            
            print(f"  After cleanup: {after_cleanup_memory:.2f} MB ({cleanup_delta:+.2f} MB)")
            
            self.assertLess(memory_delta, 100, "Memory usage should be reasonable")
            
        except ImportError:
            print("  psutil not available, skipping memory test")
        
        print("✅ Memory usage test completed")


if __name__ == '__main__':
    unittest.main() 