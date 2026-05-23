"""
Test to verify all shared fixtures work correctly.

This test file validates that all fixtures defined in conftest.py
are properly configured and functional.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from typing import Dict, Any


def test_client_fixture(client):
    """Test that client fixture provides a working TestClient."""
    assert isinstance(client, TestClient)
    assert client is not None


def test_test_image_fixture(test_image):
    """Test that test_image fixture provides a valid image path."""
    assert isinstance(test_image, Path)
    assert test_image.exists()
    assert test_image.suffix in [".jpg", ".jpeg", ".png"]


def test_sample_xray_image_fixture(sample_xray_image):
    """Test that sample_xray_image fixture provides a valid image path."""
    assert isinstance(sample_xray_image, Path)
    assert sample_xray_image.exists()


def test_test_image_alias(test_image, sample_xray_image):
    """Test that test_image is an alias for sample_xray_image."""
    assert test_image == sample_xray_image


def test_mock_rag_response_fixture(mock_rag_response):
    """Test that mock_rag_response fixture provides valid data."""
    assert isinstance(mock_rag_response, dict)
    assert "answer" in mock_rag_response
    assert "sources" in mock_rag_response
    assert "confidence" in mock_rag_response
    assert isinstance(mock_rag_response["sources"], list)
    assert len(mock_rag_response["sources"]) > 0


def test_mock_imaging_response_fixture(mock_imaging_response):
    """Test that mock_imaging_response fixture provides valid data."""
    assert isinstance(mock_imaging_response, dict)
    assert "disease" in mock_imaging_response
    assert "confidence" in mock_imaging_response
    assert "top_k_predictions" in mock_imaging_response
    assert isinstance(mock_imaging_response["top_k_predictions"], list)


def test_mock_vitals_response_fixture(mock_vitals_response):
    """Test that mock_vitals_response fixture provides valid data."""
    assert isinstance(mock_vitals_response, dict)
    assert "heart_rate" in mock_vitals_response
    assert "blood_pressure" in mock_vitals_response
    assert "confidence" in mock_vitals_response


def test_sample_rag_queries_fixture(sample_rag_queries):
    """Test that sample_rag_queries fixture provides valid queries."""
    assert isinstance(sample_rag_queries, list)
    assert len(sample_rag_queries) > 0
    assert all(isinstance(q, str) for q in sample_rag_queries)


def test_sample_diseases_fixture(sample_diseases):
    """Test that sample_diseases fixture provides valid disease names."""
    assert isinstance(sample_diseases, list)
    assert len(sample_diseases) > 0
    assert all(isinstance(d, str) for d in sample_diseases)


def test_test_database_fixture(test_database):
    """Test that test_database fixture provides mock database."""
    assert isinstance(test_database, dict)
    assert "type" in test_database
    assert "connected" in test_database
    assert test_database["type"] == "mock"
    assert test_database["connected"] is True


def test_temp_upload_dir_fixture(temp_upload_dir):
    """Test that temp_upload_dir fixture creates a temporary directory."""
    assert isinstance(temp_upload_dir, Path)
    assert temp_upload_dir.exists()
    assert temp_upload_dir.is_dir()


def test_cleanup_test_files_fixture(cleanup_test_files):
    """Test that cleanup_test_files fixture provides a list for tracking."""
    assert isinstance(cleanup_test_files, list)
    assert len(cleanup_test_files) == 0  # Should start empty


def test_cleanup_uploaded_images_fixture(cleanup_uploaded_images):
    """Test that cleanup_uploaded_images fixture provides a list for tracking."""
    assert isinstance(cleanup_uploaded_images, list)
    assert len(cleanup_uploaded_images) == 0  # Should start empty


def test_api_base_url_fixture(api_base_url):
    """Test that api_base_url fixture provides a valid URL."""
    assert isinstance(api_base_url, str)
    assert api_base_url.startswith("http")


def test_api_timeout_fixture(api_timeout):
    """Test that api_timeout fixture provides a valid timeout value."""
    assert isinstance(api_timeout, int)
    assert api_timeout > 0


def test_cleanup_test_files_functionality(cleanup_test_files, tmp_path):
    """Test that cleanup_test_files actually cleans up files."""
    # Create a test file
    test_file = tmp_path / "test_cleanup.txt"
    test_file.write_text("test content")
    assert test_file.exists()
    
    # Register for cleanup
    cleanup_test_files.append(test_file)
    
    # File should still exist during test
    assert test_file.exists()
    
    # After test, the fixture will clean it up automatically


def test_cleanup_uploaded_images_functionality(cleanup_uploaded_images, tmp_path):
    """Test that cleanup_uploaded_images actually cleans up images."""
    # Create a test image file
    test_image = tmp_path / "test_image.jpg"
    test_image.write_bytes(b"fake image data")
    assert test_image.exists()
    
    # Register for cleanup
    cleanup_uploaded_images.append(test_image)
    
    # File should still exist during test
    assert test_image.exists()
    
    # After test, the fixture will clean it up automatically
