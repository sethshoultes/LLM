#!/usr/bin/env python3
"""
Unit tests for RAG API bridge.

Tests the compatibility layer between the original RAG API handler
and the new controller-based implementation.
"""

import unittest
from unittest.mock import patch, MagicMock

from web.api.bridges.rag_api_bridge import RagApiBridge


class TestRagApiBridge(unittest.TestCase):
    """Test RAG API bridge functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create bridge
        self.bridge = RagApiBridge()
        
        # Mock controller
        self.mock_controller = MagicMock()
        
        # Create patch for controller
        self.controller_patch = patch('web.api.bridges.rag_api_bridge.rag_controller', self.mock_controller)
        self.controller_patch.start()
        
        # Set up test data
        self.test_path = "/api/projects/test_project_id"
        self.test_method = "GET"
        self.test_query_params = {"param": "value"}
        self.test_body = {"key": "value"}
        
        # Mock controller response
        self.mock_controller.handle_request.return_value = (200, {"status": "success", "data": "test_data"})
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop patches
        self.controller_patch.stop()
    
    def test_handle_request(self):
        """Test request handling."""
        # Call method
        status, response = self.bridge.handle_request(
            path=self.test_path,
            method=self.test_method,
            query_params=self.test_query_params,
            body=self.test_body
        )
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], "test_data")
        
        # Verify mock calls
        self.mock_controller.handle_request.assert_called_once_with(
            path=self.test_path,
            method=self.test_method,
            query_params=self.test_query_params,
            body=self.test_body
        )
    
    def test_handle_request_error(self):
        """Test error handling."""
        # Set up mock controller to raise exception
        self.mock_controller.handle_request.side_effect = Exception("Test error")
        self.mock_controller.format_error_response.return_value = (500, {"status": "error", "error": "Internal server error"})
        
        # Call method
        status, response = self.bridge.handle_request(
            path=self.test_path,
            method=self.test_method
        )
        
        # Verify response
        self.assertEqual(status, 500)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Internal server error")
        
        # Verify mock calls
        self.mock_controller.handle_request.assert_called_once()
        self.mock_controller.format_error_response.assert_called_once_with(
            "Internal server error",
            "Test error",
            "internal_error",
            status_code=500
        )


if __name__ == "__main__":
    unittest.main()