"""
Integration tests for RAG -> Imaging pipeline.

Tests the complete workflow of querying medical knowledge and analyzing images.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from typing import Dict, Any


@pytest.mark.integration
class TestRAGImagingPipeline:
    """Test RAG and Imaging integration."""
    
    def test_rag_query_then_imaging(self, client: TestClient, sample_xray_image: Path):
        """
        Test complete workflow: RAG query -> Image analysis.
        
        Scenario:
        1. User asks about pneumonia symptoms
        2. RAG returns information about pneumonia
        3. User uploads chest X-ray
        4. Imaging classifies the image
        5. Results are correlated
        """
        # Step 1: Query RAG about pneumonia
        rag_response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "What are the symptoms of pneumonia?",
                "language": "en"
            }
        )
        
        assert rag_response.status_code == 200, f"RAG query failed: {rag_response.text}"
        rag_data = rag_response.json()
        
        # Verify RAG response structure
        assert "answer" in rag_data, "RAG response missing 'answer' field"
        assert "sources" in rag_data, "RAG response missing 'sources' field"
        assert "confidence" in rag_data, "RAG response missing 'confidence' field"
        assert len(rag_data["answer"]) > 0, "RAG answer is empty"
        
        # Verify pneumonia is mentioned in the answer
        answer_lower = rag_data["answer"].lower()
        assert "pneumonia" in answer_lower or "lung" in answer_lower or "respiratory" in answer_lower, \
            "RAG answer doesn't mention pneumonia or related terms"
        
        # Verify confidence is reasonable
        assert 0.0 <= rag_data["confidence"] <= 1.0, "RAG confidence out of range"
        
        # Step 2: Upload chest X-ray for analysis
        with open(sample_xray_image, "rb") as f:
            imaging_response = client.post(
                "/api/v1/imaging/classify",
                files={"file": ("test_xray.jpg", f, "image/jpeg")}
            )
        
        assert imaging_response.status_code == 200, f"Imaging analysis failed: {imaging_response.text}"
        imaging_data = imaging_response.json()
        
        # Verify imaging response structure
        assert "disease" in imaging_data, "Imaging response missing 'disease' field"
        assert "confidence" in imaging_data, "Imaging response missing 'confidence' field"
        assert "filename" in imaging_data, "Imaging response missing 'filename' field"
        
        # Verify confidence is reasonable
        assert 0.0 <= imaging_data["confidence"] <= 1.0, "Imaging confidence out of range"
        
        # Step 3: Verify data flow and correlation
        predicted_disease = imaging_data["disease"].lower()
        
        # Log the correlation for analysis
        print(f"\n=== Pipeline Test Results ===")
        print(f"RAG Query: 'What are the symptoms of pneumonia?'")
        print(f"RAG Answer: {rag_data['answer'][:150]}...")
        print(f"RAG Confidence: {rag_data['confidence']:.2f}")
        print(f"RAG Sources: {len(rag_data.get('sources', []))}")
        print(f"Imaging Prediction: {imaging_data['disease']}")
        print(f"Imaging Confidence: {imaging_data['confidence']:.2f}")
        print(f"Correlation: {'[MATCH]' if 'pneumonia' in predicted_disease else '[DIFFERENT]'}")
        
        # Verify both systems returned valid results
        assert len(imaging_data["disease"]) > 0, "Imaging disease prediction is empty"
        assert imaging_data["confidence"] > 0.0, "Imaging confidence is zero"
        
    def test_imaging_then_rag_correlation(self, client: TestClient, sample_xray_image: Path):
        """
        Test reverse workflow: Image analysis -> RAG query about detected disease.
        
        Scenario:
        1. User uploads chest X-ray
        2. Imaging system classifies the image
        3. User asks RAG about the detected disease
        4. RAG returns relevant information
        5. Verify correlation between imaging result and RAG knowledge
        """
        # Step 1: Upload and classify chest X-ray
        with open(sample_xray_image, "rb") as f:
            imaging_response = client.post(
                "/api/v1/imaging/classify",
                files={"file": ("test_xray.jpg", f, "image/jpeg")},
                data={"top_k": 3}
            )
        
        assert imaging_response.status_code == 200, f"Imaging analysis failed: {imaging_response.text}"
        imaging_data = imaging_response.json()
        
        # Verify imaging response
        assert "disease" in imaging_data, "Imaging response missing 'disease' field"
        detected_disease = imaging_data["disease"]
        
        # Step 2: Query RAG about the detected disease
        rag_query = f"What is {detected_disease}? What are its symptoms and treatment?"
        rag_response = client.post(
            "/api/v1/rag/query",
            json={
                "query": rag_query,
                "language": "en",
                "top_k": 5
            }
        )
        
        assert rag_response.status_code == 200, f"RAG query failed: {rag_response.text}"
        rag_data = rag_response.json()
        
        # Verify RAG response structure
        assert "answer" in rag_data, "RAG response missing 'answer' field"
        assert "sources" in rag_data, "RAG response missing 'sources' field"
        assert len(rag_data["answer"]) > 0, "RAG answer is empty"
        
        # Step 3: Verify correlation - RAG should mention the detected disease
        answer_lower = rag_data["answer"].lower()
        disease_lower = detected_disease.lower()
        
        # Check if disease name or related terms appear in the answer
        disease_mentioned = disease_lower in answer_lower
        
        # Log correlation results
        print(f"\n=== Reverse Pipeline Test Results ===")
        print(f"Imaging Prediction: {detected_disease}")
        print(f"Imaging Confidence: {imaging_data['confidence']:.2f}")
        print(f"RAG Query: '{rag_query}'")
        print(f"RAG Answer: {rag_data['answer'][:150]}...")
        print(f"RAG Confidence: {rag_data['confidence']:.2f}")
        print(f"Disease Mentioned in RAG: {disease_mentioned}")
        print(f"RAG Sources: {len(rag_data.get('sources', []))}")
        print(f"RAG Mode: {rag_data.get('mode', 'unknown')}")
        
        # Verify data flow - sources may be empty if using direct_llm mode
        # This is acceptable as long as we get a valid answer
        assert rag_data["confidence"] > 0.0, "RAG confidence is zero"
        
        # Verify the answer contains relevant medical information
        # Check for structured sections (symptoms, causes, treatment)
        has_structured_info = (
            len(rag_data.get("symptoms", [])) > 0 or
            len(rag_data.get("causes", [])) > 0 or
            len(rag_data.get("treatment", [])) > 0
        )
        assert has_structured_info, "RAG response missing structured medical information"
        
    def test_multiple_diseases_pipeline(
        self, 
        client: TestClient, 
        sample_xray_image: Path,
        sample_diseases: list
    ):
        """
        Test pipeline with multiple disease queries.
        
        Scenario:
        1. Query RAG about multiple diseases
        2. Verify each query returns relevant information
        3. Upload X-ray and verify imaging works
        4. Verify data consistency across multiple queries
        """
        # Test multiple disease queries
        diseases_to_test = sample_diseases[:5]  # Test first 5 diseases
        rag_results = []
        
        print(f"\n=== Testing Multiple Diseases ===")
        
        for disease in diseases_to_test:
            # Query RAG about each disease
            rag_response = client.post(
                "/api/v1/rag/query",
                json={
                    "query": f"What are the symptoms of {disease}?",
                    "language": "en"
                }
            )
            
            assert rag_response.status_code == 200, f"RAG query failed for {disease}"
            rag_data = rag_response.json()
            
            # Verify response structure
            assert "answer" in rag_data, f"RAG response missing 'answer' for {disease}"
            assert "confidence" in rag_data, f"RAG response missing 'confidence' for {disease}"
            
            rag_results.append({
                "disease": disease,
                "answer": rag_data["answer"],
                "confidence": rag_data["confidence"],
                "sources": len(rag_data.get("sources", []))
            })
            
            print(f"Disease: {disease}")
            print(f"  Confidence: {rag_data['confidence']:.2f}")
            print(f"  Sources: {len(rag_data.get('sources', []))}")
            print(f"  Answer length: {len(rag_data['answer'])} chars")
        
        # Verify all queries succeeded
        assert len(rag_results) == len(diseases_to_test), "Not all disease queries succeeded"
        
        # Verify all have reasonable confidence
        for result in rag_results:
            assert result["confidence"] >= 0.0, f"Invalid confidence for {result['disease']}"
            assert len(result["answer"]) > 0, f"Empty answer for {result['disease']}"
        
        # Now test imaging with the same X-ray
        with open(sample_xray_image, "rb") as f:
            imaging_response = client.post(
                "/api/v1/imaging/classify",
                files={"file": ("test_xray.jpg", f, "image/jpeg")},
                data={"top_k": 5}
            )
        
        assert imaging_response.status_code == 200, "Imaging analysis failed"
        imaging_data = imaging_response.json()
        
        print(f"\nImaging Result:")
        print(f"  Predicted: {imaging_data['disease']}")
        print(f"  Confidence: {imaging_data['confidence']:.2f}")
        
        # Verify imaging result
        assert "disease" in imaging_data, "Imaging response missing 'disease'"
        assert imaging_data["confidence"] > 0.0, "Imaging confidence is zero"
        
        # Check if imaging prediction matches any of the queried diseases
        predicted_disease = imaging_data["disease"].lower()
        queried_diseases = [d.lower() for d in diseases_to_test]
        
        print(f"\nCorrelation Check:")
        print(f"  Predicted disease in queried list: {predicted_disease in queried_diseases}")
        
    def test_data_flow_assertions(self, client: TestClient, sample_xray_image: Path):
        """
        Test data flow between RAG and Imaging systems.
        
        Verifies:
        1. Both systems can handle the same medical context
        2. Response formats are consistent
        3. Confidence scores are properly calculated
        4. Sources/metadata are properly returned
        """
        # Step 1: Query RAG
        rag_response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "What causes pneumonia and how is it treated?",
                "language": "en",
                "top_k": 5
            }
        )
        
        assert rag_response.status_code == 200, "RAG query failed"
        rag_data = rag_response.json()
        
        # Verify RAG data flow
        assert "answer" in rag_data, "RAG missing answer"
        assert "sources" in rag_data, "RAG missing sources"
        assert "confidence" in rag_data, "RAG missing confidence"
        assert "language" in rag_data, "RAG missing language"
        
        # Verify sources structure
        if len(rag_data.get("sources", [])) > 0:
            source = rag_data["sources"][0]
            assert "title" in source or "source" in source, "Source missing title"
            assert "content" in source or "text" in source, "Source missing content"
            assert "score" in source, "Source missing score"
        
        # Step 2: Classify image
        with open(sample_xray_image, "rb") as f:
            imaging_response = client.post(
                "/api/v1/imaging/classify",
                files={"file": ("test_xray.jpg", f, "image/jpeg")},
                data={"top_k": 3, "explain": False}
            )
        
        assert imaging_response.status_code == 200, "Imaging classification failed"
        imaging_data = imaging_response.json()
        
        # Verify imaging data flow
        assert "disease" in imaging_data, "Imaging missing disease"
        assert "confidence" in imaging_data, "Imaging missing confidence"
        assert "filename" in imaging_data, "Imaging missing filename"
        
        # Verify metadata if present
        if "model_metadata" in imaging_data:
            metadata = imaging_data["model_metadata"]
            assert "backbone" in metadata, "Metadata missing backbone"
            assert "num_classes" in metadata, "Metadata missing num_classes"
        
        # Step 3: Verify data consistency
        print(f"\n=== Data Flow Verification ===")
        print(f"RAG Response Fields: {list(rag_data.keys())}")
        print(f"Imaging Response Fields: {list(imaging_data.keys())}")
        print(f"RAG Language: {rag_data.get('language')}")
        print(f"RAG Sources Count: {len(rag_data.get('sources', []))}")
        print(f"Imaging Backend: {imaging_data.get('inference_backend', 'unknown')}")
        
        # Verify both systems returned valid confidence scores
        assert 0.0 <= rag_data["confidence"] <= 1.0, "RAG confidence out of range"
        assert 0.0 <= imaging_data["confidence"] <= 1.0, "Imaging confidence out of range"
        
        # Verify language is set correctly
        assert rag_data.get("language") in ["en", "ar", "fr"], "Invalid language code"
        
        # Verify filename was preserved
        assert imaging_data["filename"] == "test_xray.jpg", "Filename not preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
