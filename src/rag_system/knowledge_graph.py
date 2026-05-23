"""
Knowledge Graph for Disease Relationships
==========================================

This module builds a simple graph of medical diseases using NetworkX,
with nodes representing diseases and edges representing relationships
based on shared symptoms, categories, or causes.

The graph enables finding related diseases for better RAG context.
"""

import logging
from typing import List, Set, Dict
import networkx as nx

logger = logging.getLogger(__name__)

# Disease categories for organizing relationships
DISEASE_CATEGORIES = {
    "respiratory_infections": [
        "Pneumonia", "COVID-19", "Tuberculosis", "Bronchitis",
        "Acute Bronchiolitis", "Influenza"
    ],
    "lung_diseases": [
        "Asthma", "COPD", "Pneumothorax", "Atelectasis",
        "Pleural Effusion", "Pulmonary Edema", "Pneumoconiosis"
    ],
    "cardiac": [
        "Cardiomegaly", "Hypertension", "Heart Failure",
        "Myocardial Infarction", "Ischemic Heart Disease"
    ],
    "infectious_diseases": [
        "Malaria", "Typhoid", "Dengue", "Hepatitis B", "UTI"
    ],
    "gastrointestinal": [
        "Appendicitis", "Gastroenteritis", "Peptic Ulcer", "Cirrhosis"
    ],
    "kidney_diseases": [
        "Glomerulonephritis", "UTI", "Nephrolithiasis"
    ],
    "metabolic": [
        "Diabetes", "Obesity"
    ]
}

# Common symptom relationships
SYMPTOM_RELATIONSHIPS = {
    "fever": [
        "Pneumonia", "COVID-19", "Tuberculosis", "Bronchitis",
        "Influenza", "Malaria", "Typhoid", "Dengue", "Hepatitis B",
        "UTI", "Appendicitis", "Gastroenteritis"
    ],
    "cough": [
        "Pneumonia", "COVID-19", "Tuberculosis", "Asthma",
        "COPD", "Bronchitis", "Acute Bronchiolitis", "Influenza"
    ],
    "chest_pain": [
        "Myocardial Infarction", "Pneumothorax", "Pulmonary Edema",
        "Heart Failure", "Ischemic Heart Disease", "Cardiomegaly"
    ],
    "dyspnea": [
        "Pneumonia", "Asthma", "COPD", "Pulmonary Edema",
        "Heart Failure", "Pneumothorax", "Pleural Effusion",
        "Myocardial Infarction"
    ],
    "abdominal_pain": [
        "Appendicitis", "Gastroenteritis", "Peptic Ulcer",
        "Nephrolithiasis", "Cirrhosis", "Hepatitis B"
    ],
    "jaundice": [
        "Hepatitis B", "Cirrhosis", "Malaria"
    ]
}

# Organ system relationships
ORGAN_RELATIONSHIPS = {
    "lungs": [
        "Pneumonia", "COVID-19", "Tuberculosis", "Asthma", "COPD",
        "Pneumothorax", "Atelectasis", "Pleural Effusion",
        "Pulmonary Edema", "Pneumoconiosis", "Acute Bronchiolitis",
        "Bronchitis", "Influenza"
    ],
    "heart": [
        "Cardiomegaly", "Hypertension", "Heart Failure",
        "Myocardial Infarction", "Ischemic Heart Disease"
    ],
    "kidney": [
        "Glomerulonephritis", "UTI", "Nephrolithiasis"
    ],
    "gi_tract": [
        "Appendicitis", "Gastroenteritis", "Peptic Ulcer", "Cirrhosis"
    ],
    "blood": [
        "Malaria", "Dengue", "Hepatitis B"
    ]
}

# Complications and related conditions
COMPLICATION_RELATIONSHIPS = {
    "Pneumonia": ["Acute Bronchiolitis", "Pulmonary Edema"],
    "COVID-19": ["Myocardial Infarction", "Pneumonia"],
    "Tuberculosis": ["Pneumothorax", "Asthma"],
    "Asthma": ["Bronchitis", "COPD"],
    "COPD": ["Pneumonia", "Heart Failure"],
    "Hypertension": ["Myocardial Infarction", "Heart Failure"],
    "Diabetes": ["Heart Failure", "Glomerulonephritis"],
    "Obesity": ["Hypertension", "Diabetes"],
    "Hepatitis B": ["Cirrhosis"],
}


class MedicalKnowledgeGraph:
    """
    A knowledge graph representing relationships between medical diseases.
    
    Nodes represent diseases, and edges represent relationships based on:
    - Shared symptom presentation
    - Shared disease category/organ system
    - Complication relationships
    - Common causes or risk factors
    """

    def __init__(self):
        """Initialize the knowledge graph with diseases and relationships."""
        self.graph = nx.Graph()
        self._build_graph()
        logger.info(f"Knowledge graph initialized with {self.graph.number_of_nodes()} diseases")

    def _build_graph(self) -> None:
        """Build the knowledge graph by adding nodes and edges."""
        # Collect all diseases
        all_diseases = set()
        all_diseases.add("Normal")  # Add Normal as baseline
        
        for diseases in DISEASE_CATEGORIES.values():
            all_diseases.update(diseases)
        
        # Add nodes
        for disease in all_diseases:
            self.graph.add_node(disease)
        
        # Add edges based on category relationships
        for category, diseases in DISEASE_CATEGORIES.items():
            for i, disease1 in enumerate(diseases):
                for disease2 in diseases[i + 1:]:
                    self.graph.add_edge(disease1, disease2, weight=1.0, relation="same_category")
        
        # Add edges based on symptom relationships
        for symptom, diseases in SYMPTOM_RELATIONSHIPS.items():
            for i, disease1 in enumerate(diseases):
                for disease2 in diseases[i + 1:]:
                    if self.graph.has_edge(disease1, disease2):
                        # Increase weight if already connected
                        self.graph[disease1][disease2]["weight"] += 0.5
                    else:
                        self.graph.add_edge(disease1, disease2, weight=0.5, relation="shared_symptom")
        
        # Add edges based on organ system relationships
        for organ, diseases in ORGAN_RELATIONSHIPS.items():
            for i, disease1 in enumerate(diseases):
                for disease2 in diseases[i + 1:]:
                    if self.graph.has_edge(disease1, disease2):
                        self.graph[disease1][disease2]["weight"] += 0.3
                    else:
                        self.graph.add_edge(disease1, disease2, weight=0.3, relation="same_organ")
        
        # Add edges for complications
        for disease, complications in COMPLICATION_RELATIONSHIPS.items():
            for complication in complications:
                if complication in self.graph:
                    weight = 0.7  # High weight for direct causal relationships
                    if self.graph.has_edge(disease, complication):
                        self.graph[disease][complication]["weight"] += weight
                    else:
                        self.graph.add_edge(disease, complication, weight=weight, relation="complication")
        
        logger.debug(f"Graph built with {self.graph.number_of_edges()} edges")

    def get_related_diseases(self, disease_name: str, max_distance: int = 2, limit: int = 10) -> List[str]:
        """
        Get diseases related to the specified disease.
        
        Args:
            disease_name: Name of the disease to find relationships for
            max_distance: Maximum graph distance for related diseases (1-2)
            limit: Maximum number of related diseases to return
        
        Returns:
            List of related disease names, sorted by relevance (connection weight)
        
        Examples:
            >>> kg = MedicalKnowledgeGraph()
            >>> related = kg.get_related_diseases("Pneumonia")
            >>> print(related)  # ['COVID-19', 'Tuberculosis', 'Bronchitis', ...]
        """
        # Validate disease exists
        if disease_name not in self.graph:
            logger.warning(f"Disease '{disease_name}' not found in knowledge graph")
            return []
        
        related_diseases = set()
        
        # Get direct neighbors (distance 1)
        neighbors = list(self.graph.neighbors(disease_name))
        related_diseases.update(neighbors)
        
        # Get second-degree neighbors if max_distance > 1
        if max_distance > 1:
            for neighbor in neighbors:
                second_neighbors = list(self.graph.neighbors(neighbor))
                related_diseases.update(second_neighbors)
        
        # Remove the query disease itself
        related_diseases.discard(disease_name)
        
        # Score by edge weight (higher weight = more relevant)
        scored_diseases = []
        for related in related_diseases:
            if self.graph.has_edge(disease_name, related):
                # Direct connection: use edge weight
                weight = self.graph[disease_name][related].get("weight", 1.0)
                distance = 1
            else:
                # Indirect connection: use inverse distance and neighbor weight
                try:
                    path_length = nx.shortest_path_length(self.graph, disease_name, related)
                    weight = 1.0 / path_length  # Penalize indirect connections
                    distance = path_length
                except nx.NetworkXNoPath:
                    continue
            
            scored_diseases.append((related, weight, distance))
        
        # Sort by weight (descending), then by distance (ascending)
        scored_diseases.sort(key=lambda x: (-x[1], x[2]))
        
        # Return top results
        result = [disease for disease, weight, distance in scored_diseases[:limit]]
        logger.debug(f"Found {len(result)} related diseases for '{disease_name}'")
        return result

    def get_graph_info(self) -> Dict[str, int]:
        """
        Get basic statistics about the knowledge graph.
        
        Returns:
            Dictionary with graph statistics
        """
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "num_components": nx.number_connected_components(self.graph)
        }

    def get_diseases_by_category(self, category: str) -> List[str]:
        """
        Get all diseases in a specific category.
        
        Args:
            category: Disease category name
        
        Returns:
            List of diseases in the category
        """
        return DISEASE_CATEGORIES.get(category, [])

    def get_all_categories(self) -> List[str]:
        """Get list of all disease categories."""
        return list(DISEASE_CATEGORIES.keys())


# Module-level instance for easy access
_kg_instance = None


def get_knowledge_graph() -> MedicalKnowledgeGraph:
    """
    Get or create the singleton knowledge graph instance.
    
    Returns:
        MedicalKnowledgeGraph instance
    """
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = MedicalKnowledgeGraph()
    return _kg_instance


def get_related_diseases(disease_name: str, max_distance: int = 2, limit: int = 10) -> List[str]:
    """
    Convenience function to get related diseases.
    
    Args:
        disease_name: Name of the disease
        max_distance: Maximum graph distance (1-2)
        limit: Maximum number of results
    
    Returns:
        List of related disease names
    
    Example:
        >>> related = get_related_diseases("Pneumonia", limit=5)
        >>> print(related)
    """
    kg = get_knowledge_graph()
    return kg.get_related_diseases(disease_name, max_distance=max_distance, limit=limit)


if __name__ == "__main__":
    # Example usage
    kg = get_knowledge_graph()
    
    print("Knowledge Graph Statistics:")
    stats = kg.get_graph_info()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n\nCategory List:")
    for category in kg.get_all_categories():
        diseases = kg.get_diseases_by_category(category)
        print(f"  {category}: {len(diseases)} diseases")
    
    print("\n\nRelated Disease Examples:")
    test_diseases = ["Pneumonia", "COVID-19", "Myocardial Infarction", "Diabetes"]
    for disease in test_diseases:
        related = kg.get_related_diseases(disease, limit=5)
        print(f"  {disease}: {related}")
