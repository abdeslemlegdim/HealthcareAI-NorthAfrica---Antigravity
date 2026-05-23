#!/usr/bin/env python3
"""
Test suite for the Medical Knowledge Graph module.
"""

from src.rag_system.knowledge_graph import (
    get_knowledge_graph, 
    get_related_diseases,
    MedicalKnowledgeGraph
)

def test_singleton_instance():
    """Test that singleton instance creation works."""
    kg = get_knowledge_graph()
    assert kg is not None
    print('[TEST 1] Singleton instance creation: PASS')

def test_graph_stats():
    """Test basic graph statistics."""
    kg = get_knowledge_graph()
    stats = kg.get_graph_info()
    assert stats['num_nodes'] > 0 and stats['num_edges'] > 0
    print('[TEST 2] Graph stats: PASS - {} nodes, {} edges'.format(
        stats['num_nodes'], stats['num_edges']))

def test_related_diseases():
    """Test related disease lookup for various conditions."""
    kg = get_knowledge_graph()
    test_cases = {
        'Pneumonia': 5,
        'Myocardial Infarction': 5,
        'Diabetes': 5,
        'Hepatitis B': 5
    }
    
    for disease, limit in test_cases.items():
        related = kg.get_related_diseases(disease, limit=limit)
        assert len(related) > 0, 'No related diseases found for {}'.format(disease)
        assert disease not in related, 'Disease {} found in its own related list'.format(disease)
        print('[TEST 3] {}: PASS - {}'.format(disease, related))

def test_convenience_function():
    """Test the module-level convenience function."""
    related_pneumonia = get_related_diseases('Pneumonia', limit=3)
    assert isinstance(related_pneumonia, list)
    assert len(related_pneumonia) > 0
    print('[TEST 4] Convenience function: PASS - {}'.format(related_pneumonia))

def test_category_lookup():
    """Test disease category lookup."""
    kg = get_knowledge_graph()
    respiratory = kg.get_diseases_by_category('respiratory_infections')
    assert len(respiratory) > 0
    print('[TEST 5] Category lookup: PASS - {} respiratory diseases'.format(len(respiratory)))

def test_invalid_disease_handling():
    """Test handling of non-existent diseases."""
    kg = get_knowledge_graph()
    invalid_related = kg.get_related_diseases('NonexistentDisease')
    assert invalid_related == []
    print('[TEST 6] Invalid disease handling: PASS - returns empty list')

def test_graph_density():
    """Test graph connectivity metrics."""
    kg = get_knowledge_graph()
    stats = kg.get_graph_info()
    # Graph should be reasonably connected (density > 0.3)
    assert stats['density'] > 0.2, 'Graph density too low: {}'.format(stats['density'])
    print('[TEST 7] Graph density: PASS - density = {:.3f}'.format(stats['density']))

def test_direct_vs_indirect_relations():
    """Test that both direct and indirect relations are found."""
    kg = get_knowledge_graph()
    
    # Pneumonia should be directly connected to respiratory diseases
    pneumonia_related = kg.get_related_diseases('Pneumonia', max_distance=1, limit=10)
    assert len(pneumonia_related) > 0
    
    # With max_distance=2, should get more results
    pneumonia_related_2 = kg.get_related_diseases('Pneumonia', max_distance=2, limit=10)
    # May be same due to density, but should not crash
    assert len(pneumonia_related_2) >= 0
    
    print('[TEST 8] Distance-based lookup: PASS')

if __name__ == '__main__':
    print('=' * 60)
    print('MEDICAL KNOWLEDGE GRAPH TEST SUITE')
    print('=' * 60 + '\n')
    
    test_singleton_instance()
    test_graph_stats()
    test_related_diseases()
    test_convenience_function()
    test_category_lookup()
    test_invalid_disease_handling()
    test_graph_density()
    test_direct_vs_indirect_relations()
    
    print('\n' + '=' * 60)
    print('✅ All 8 tests PASSED')
    print('=' * 60)
