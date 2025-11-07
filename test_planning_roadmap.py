#!/usr/bin/env python3
"""
Unit tests for Planning Roadmap Creator
Tests core functionality without requiring API credentials.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys

# Import the module - will work if run from project directory
try:
    from planning_roadmap import PlanningRoadmapCreator
except ImportError:
    # Fallback for running tests from different locations
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from planning_roadmap import PlanningRoadmapCreator


class TestPlanningRoadmapCreator(unittest.TestCase):
    """Test cases for PlanningRoadmapCreator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'starting_location': 'Nanterre, France',
            'google_maps_api_key': 'test_api_key',
            'rest_time_minutes': 30,
            'work_day_start_hour': 8,
            'work_day_end_hour': 18
        }
        
    @patch('planning_roadmap.googlemaps.Client')
    def test_initialization(self, mock_gmaps):
        """Test proper initialization of PlanningRoadmapCreator."""
        with patch.object(PlanningRoadmapCreator, 'load_config', return_value=self.test_config):
            creator = PlanningRoadmapCreator()
            self.assertEqual(creator.starting_location, 'Nanterre, France')
            self.assertEqual(creator.rest_time_minutes, 30)
    
    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        creator = PlanningRoadmapCreator.__new__(PlanningRoadmapCreator)
        config = creator.load_config('nonexistent.json')
        
        # Should return default config
        self.assertIn('starting_location', config)
        self.assertEqual(config['starting_location'], 'Nanterre, France')
        self.assertEqual(config['rest_time_minutes'], 30)
    
    def test_initialization_missing_api_key(self):
        """Test initialization fails when API key is missing."""
        config_without_key = {
            'starting_location': 'Nanterre, France',
            'rest_time_minutes': 30
        }
        with patch.object(PlanningRoadmapCreator, 'load_config', return_value=config_without_key):
            with self.assertRaises(ValueError) as context:
                creator = PlanningRoadmapCreator()
            self.assertIn('API key', str(context.exception))
    
    @patch('planning_roadmap.googlemaps.Client')
    def test_nearest_neighbor_tsp(self, mock_gmaps):
        """Test TSP nearest neighbor algorithm."""
        with patch.object(PlanningRoadmapCreator, 'load_config', return_value=self.test_config):
            creator = PlanningRoadmapCreator()
            
            # Simple distance matrix
            durations = [
                [0, 10, 15, 20],
                [10, 0, 35, 25],
                [15, 35, 0, 30],
                [20, 25, 30, 0]
            ]
            
            route = creator.nearest_neighbor_tsp(durations)
            
            # Should start at 0
            self.assertEqual(route[0], 0)
            
            # Should visit all nodes
            self.assertEqual(len(route), 4)
            self.assertEqual(set(route), {0, 1, 2, 3})
    
    @patch('planning_roadmap.googlemaps.Client')
    def test_generate_route_summary(self, mock_gmaps):
        """Test route summary generation."""
        with patch.object(PlanningRoadmapCreator, 'load_config', return_value=self.test_config):
            creator = PlanningRoadmapCreator()
            
            route_info = {
                'ordered_addresses': [
                    'Nanterre, France',
                    '15 Rue de la Paix, Paris',
                    'Arc de Triomphe, Paris',
                    'Nanterre, France'
                ],
                'total_distance_km': 45.5,
                'total_time_hours': 2.5,
                'rest_time_minutes': 30
            }
            
            summary = creator.generate_route_summary(route_info)
            
            # Check summary contains key information
            self.assertIn('OPTIMIZED ROUTE PLAN', summary)
            self.assertIn('Nanterre, France', summary)
            self.assertIn('45.5', summary)
            self.assertIn('2.5', summary)
            self.assertIn('30', summary)
    
    @patch('planning_roadmap.googlemaps.Client')
    def test_calculate_optimal_route_empty_addresses(self, mock_gmaps):
        """Test route calculation with empty address list."""
        with patch.object(PlanningRoadmapCreator, 'load_config', return_value=self.test_config):
            creator = PlanningRoadmapCreator()
            
            ordered, route_info = creator.calculate_optimal_route([])
            
            # Should return empty list
            self.assertEqual(ordered, [])
            self.assertEqual(route_info, {})
    
    @patch('planning_roadmap.googlemaps.Client')
    def test_calculate_optimal_route_with_addresses(self, mock_gmaps):
        """Test route calculation with mock Google Maps API."""
        with patch.object(PlanningRoadmapCreator, 'load_config', return_value=self.test_config):
            creator = PlanningRoadmapCreator()
            
            # Mock the distance_matrix response
            mock_matrix = {
                'rows': [
                    {
                        'elements': [
                            {'status': 'OK', 'distance': {'value': 0}, 'duration': {'value': 0}},
                            {'status': 'OK', 'distance': {'value': 10000}, 'duration': {'value': 600}},
                            {'status': 'OK', 'distance': {'value': 15000}, 'duration': {'value': 900}}
                        ]
                    },
                    {
                        'elements': [
                            {'status': 'OK', 'distance': {'value': 10000}, 'duration': {'value': 600}},
                            {'status': 'OK', 'distance': {'value': 0}, 'duration': {'value': 0}},
                            {'status': 'OK', 'distance': {'value': 5000}, 'duration': {'value': 300}}
                        ]
                    },
                    {
                        'elements': [
                            {'status': 'OK', 'distance': {'value': 15000}, 'duration': {'value': 900}},
                            {'status': 'OK', 'distance': {'value': 5000}, 'duration': {'value': 300}},
                            {'status': 'OK', 'distance': {'value': 0}, 'duration': {'value': 0}}
                        ]
                    }
                ]
            }
            
            creator.gmaps.distance_matrix = Mock(return_value=mock_matrix)
            
            addresses = ['Address 1, Paris', 'Address 2, Paris']
            ordered, route_info = creator.calculate_optimal_route(addresses)
            
            # Should include starting location
            self.assertIn('Nanterre, France', ordered[0])
            
            # Should have route info
            self.assertIn('total_distance_km', route_info)
            self.assertIn('total_time_hours', route_info)
            self.assertIn('rest_time_minutes', route_info)


class TestConfigManagement(unittest.TestCase):
    """Test configuration file management."""
    
    def test_example_config_exists(self):
        """Test that example config file exists."""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config.example.json'
        )
        self.assertTrue(os.path.exists(config_path))
        
        # Validate it's valid JSON
        with open(config_path, 'r') as f:
            config = json.load(f)
            self.assertIn('starting_location', config)
            self.assertIn('google_maps_api_key', config)
            self.assertIn('rest_time_minutes', config)


def run_tests():
    """Run all tests."""
    print("Running Planning Roadmap Creator Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPlanningRoadmapCreator))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManagement))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
