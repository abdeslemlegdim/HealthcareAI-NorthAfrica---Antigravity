"""
Simple integration test to verify activity tracking is properly integrated.

This test verifies that:
1. ActivityService is imported correctly in all endpoint files
2. The activity recording calls are present in the code
3. The integration compiles without errors
"""

import pytest
import ast
import inspect


def test_medical_imaging_api_has_activity_service_import():
    """Verify medical imaging API imports ActivityService."""
    from src.medical_imaging import api
    
    # Check that ActivityService is available in the module
    assert hasattr(api, 'ActivityService'), "ActivityService should be imported in medical_imaging.api"


def test_vital_signs_api_has_activity_service_import():
    """Verify vital signs API imports ActivityService."""
    from src.vital_signs import api
    
    # Check that ActivityService is available in the module
    assert hasattr(api, 'ActivityService'), "ActivityService should be imported in vital_signs.api"


def test_rag_api_has_activity_service_import():
    """Verify RAG API imports ActivityService."""
    from src.rag_system import api
    
    # Check that ActivityService is available in the module
    assert hasattr(api, 'ActivityService'), "ActivityService should be imported in rag_system.api"


def test_medical_imaging_classify_has_activity_tracking():
    """Verify classify endpoint has activity tracking code."""
    from src.medical_imaging.api import classify_image
    
    # Get source code
    source = inspect.getsource(classify_image)
    
    # Check for activity tracking calls
    assert 'ActivityService' in source, "classify_image should use ActivityService"
    assert 'record_activity' in source, "classify_image should call record_activity"
    assert "activity_type='imaging'" in source, "classify_image should record 'imaging' activity"


def test_medical_imaging_explain_has_activity_tracking():
    """Verify explain endpoint has activity tracking code."""
    from src.medical_imaging.api import explain_image
    
    source = inspect.getsource(explain_image)
    
    assert 'ActivityService' in source, "explain_image should use ActivityService"
    assert 'record_activity' in source, "explain_image should call record_activity"
    assert "activity_type='imaging'" in source, "explain_image should record 'imaging' activity"


def test_vital_signs_measure_has_activity_tracking():
    """Verify measure_vitals endpoint has activity tracking code."""
    from src.vital_signs.api import measure_vitals
    
    source = inspect.getsource(measure_vitals)
    
    assert 'ActivityService' in source, "measure_vitals should use ActivityService"
    assert 'record_activity' in source, "measure_vitals should call record_activity"
    assert "activity_type='vitals'" in source, "measure_vitals should record 'vitals' activity"


def test_vital_signs_heart_rate_has_activity_tracking():
    """Verify measure_heart_rate endpoint has activity tracking code."""
    from src.vital_signs.api import measure_heart_rate
    
    source = inspect.getsource(measure_heart_rate)
    
    assert 'ActivityService' in source, "measure_heart_rate should use ActivityService"
    assert 'record_activity' in source, "measure_heart_rate should call record_activity"
    assert "activity_type='vitals'" in source, "measure_heart_rate should record 'vitals' activity"


def test_rag_query_has_activity_tracking():
    """Verify query_knowledge_base endpoint has activity tracking code."""
    from src.rag_system.api import query_knowledge_base
    
    source = inspect.getsource(query_knowledge_base)
    
    assert 'ActivityService' in source, "query_knowledge_base should use ActivityService"
    assert 'record_activity' in source, "query_knowledge_base should call record_activity"
    assert "activity_type='chat'" in source, "query_knowledge_base should record 'chat' activity"


def test_activity_tracking_uses_current_user():
    """Verify activity tracking uses current_user.id."""
    from src.medical_imaging.api import classify_image
    from src.vital_signs.api import measure_vitals
    from src.rag_system.api import query_knowledge_base
    
    # Check all endpoints use current_user.id
    for func in [classify_image, measure_vitals, query_knowledge_base]:
        source = inspect.getsource(func)
        assert 'current_user' in source, f"{func.__name__} should have current_user parameter"
        assert 'user_id=current_user.id' in source, f"{func.__name__} should use current_user.id for activity tracking"


def test_activity_tracking_includes_metadata():
    """Verify activity tracking includes metadata."""
    from src.medical_imaging.api import classify_image
    from src.vital_signs.api import measure_vitals
    from src.rag_system.api import query_knowledge_base
    
    # Check all endpoints include metadata
    for func in [classify_image, measure_vitals, query_knowledge_base]:
        source = inspect.getsource(func)
        assert 'metadata=' in source, f"{func.__name__} should include metadata in activity tracking"


def test_activity_service_record_activity_signature():
    """Verify ActivityService.record_activity has correct signature."""
    from src.auth.services.activity_service import ActivityService
    
    # Check method exists
    assert hasattr(ActivityService, 'record_activity'), "ActivityService should have record_activity method"
    
    # Get method signature
    method = getattr(ActivityService, 'record_activity')
    sig = inspect.signature(method)
    
    # Verify parameters
    params = list(sig.parameters.keys())
    assert 'user_id' in params, "record_activity should have user_id parameter"
    assert 'activity_type' in params, "record_activity should have activity_type parameter"
    assert 'metadata' in params, "record_activity should have metadata parameter"


def test_activity_types_are_correct():
    """Verify correct activity types are used."""
    from src.medical_imaging.api import classify_image
    from src.vital_signs.api import measure_vitals
    from src.rag_system.api import query_knowledge_base
    
    # Medical imaging should use 'imaging'
    imaging_source = inspect.getsource(classify_image)
    assert "'imaging'" in imaging_source or '"imaging"' in imaging_source
    
    # Vital signs should use 'vitals'
    vitals_source = inspect.getsource(measure_vitals)
    assert "'vitals'" in vitals_source or '"vitals"' in vitals_source
    
    # RAG should use 'chat'
    rag_source = inspect.getsource(query_knowledge_base)
    assert "'chat'" in rag_source or '"chat"' in rag_source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
